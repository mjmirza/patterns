---
name: Split Loop
slug: split-loop
family: 03-refactoring
category: Refactoring
aliases: [Loop Splitting, Separate Loop Concerns, Two Pass Loop]
first_described: "Fowler 2018"
maturity: canonical
related: [slide-statements, extract-function, split-variable, replace-loop-with-pipeline, separate-query-from-modifier]
incompatible_with: [loop-fusion]
verified: 2026-08-02
---

# Split Loop

## 1. Name, aliases, and lineage

The canonical name is **Split Loop**. Martin Fowler's public catalog records
the refactoring under that name and shows a loop that accumulates salary and
age being replaced by two loops, one for each calculation,
https://refactoring.com/catalog/splitLoop.html, verified 2026-08-02. The book
citation is Martin Fowler, with Kent Beck, *Refactoring. Improving the Design
of Existing Code*, 2nd edition, Addison-Wesley, 2018, chapter 8, "Moving
Features," catalog entry "Split Loop."

The common aliases are **Loop Splitting**, **Separate Loop Concerns**, and
**Two Pass Loop**. They are not perfect synonyms. Loop Splitting is the general
compiler and refactoring phrase. Separate Loop Concerns names the design
reason. Two Pass Loop names the resulting execution shape, which may be used
by code that was never refactored from a combined loop.

The pattern has an inverse. Compilers and performance engineers often use
**loop fusion** to combine adjacent loops over the same range to reduce passes
and improve locality. This entry is about a source-level refactoring whose
primary target is readability, testability, and change isolation. It is not a
claim that two passes are always faster than one. A peer-reviewed analysis by
Dominic Steinhöfel and Reiner Hähnle discusses Split Loop as a transformation,
states preconditions for semantic safety, and says the direct overhead is the
repeated loop guard evaluation rather than a change in asymptotic order,
https://link.springer.com/article/10.1007/s10817-023-09692-0, verified
2026-08-02.

Judgement. In this repository, Split Loop is treated as a refactoring pattern
because it changes code structure while preserving observable behavior. The
name should be reserved for a loop whose body contains independent work. If the
parts cannot be separated without changing what later code can observe, the
edit is not Split Loop.

## 2. Problem and context

A loop walks one collection and performs two or more independent pieces of
work. Each piece may be small, but the combined loop body forces the reader to
understand several goals at once. The code might compute two summaries, build
two indexes, collect errors while building output, derive a display total while
recording audit facts, or update separate accumulators that have no real
relationship except that they read the same elements.

The usual reason the loop exists is economy. One traversal felt cheaper than
two, and the author placed every per-element action in that traversal. That is
often fine while the body has two short lines. It ages poorly when each line
gains branching, temporary values, logging, error handling, or comments. The
loop becomes a small procedure disguised as iteration. A change to one concern
now has to be reviewed against every other concern in the same body.

The smell is not multiple variables by itself. A loop that computes `sum` and
`count` to return a mean has one concern. A loop that computes `totalSalary`
and `oldestEmployeeName` may still have one concern if both belong to the same
report row. Split Loop applies when the loop is doing separable work, not when
it happens to use several locals.

A useful reader test is to cover the loop body with your hand and ask what
each accumulator means. If the answer for one accumulator does not mention the
other accumulator, the two pieces may be independent. Then reverse the test:
read each statement and ask which result would be wrong if that statement were
deleted. If every statement belongs to one result, the loop is a good candidate.
If many statements serve both results, or if the results only make sense
together, the loop is expressing a combined invariant and should stay combined
until that invariant is named.

The context is ordinary imperative code where traversal order is not part of
the domain behavior. The input is usually an array, list, slice, vector, map
entries view, query result already materialized in memory, or another finite
collection. The output may be two local variables, two return fields, two
indexes, or one result plus one side report. The refactoring is local: it does
not require a new class, a public API change, or a new library.

The split can be the final improvement, or it can prepare another refactoring.
Once the two loops exist, each loop can often be named with Extract Function,
converted to a collection pipeline, moved to a better owner, parallelized, or
deleted when one result is no longer used. Fowler's loop-to-pipeline article
shows the wider refactoring habit of turning loop behavior into smaller named
pieces before changing the representation,
https://martinfowler.com/articles/refactoring-pipelines.html, verified
2026-08-02.

The danger is false independence. If one concern reads a value written by the
other concern during the same iteration, if either concern changes the iterator
or loop bound, or if exceptions and early exits are visible, splitting can
change behavior. Steinhöfel and Hähnle explicitly identify independence of
frames and footprints, non-abrupt completion, and side-effect-free guards as
preconditions in their treatment of Split Loop,
https://link.springer.com/article/10.1007/s10817-023-09692-0, verified
2026-08-02.

That danger is why Split Loop is best performed as a small refactoring rather
than as a rewrite. The goal is to preserve the old algorithm, not to make the
new passes clever. If a reviewer sees new predicates, new sorting, new caching,
or a new data structure in the same diff, the behavioral proof becomes harder.
First split the concerns with the same operations. Then make later changes one
at a time.

A second reader test is ownership. Ask who would approve a change to each
statement in the loop. If the same person or team owns every statement, Split
Loop may still help, but the review pressure is lower. If one group owns price
math, another owns risk flags, and a third owns export formatting, a combined
loop makes every change look cross-functional even when the work is not. A
split can turn one broad review into two narrow reviews plus a small
orchestration review.

## 3. Forces

Judgement. The forces below are engineering trade-offs. They are not quoted
claims from one source.

- **Clarity.** Split Loop favors clarity when each pass has one reason to
  exist. A reader can name the pass, review it, and test it without mentally
  separating unrelated statements.
- **Latency.** Split Loop sacrifices single-pass latency on hot paths. The
  collection is read more than once. For small in-memory collections this is
  often invisible. For large, remote, streaming, or cache-sensitive data it can
  dominate the cost.
- **Coupling.** Split Loop reduces coupling between concerns inside the loop
  body. Each pass owns its own accumulator and temporary values. It can increase
  coupling to the input shape, because the input must now support repeated
  traversal or be materialized first.
- **Consistency.** Split Loop favors correctness by making each invariant local
  to one pass. It can harm temporal consistency when the original loop updated
  two outputs together so observers never saw one without the other.
- **Operability.** Split Loop improves debug and trace clarity when each pass
  can carry a name, count, duration, and failure label. It can make incident
  order harder when logs move from interleaved per-item order to pass order.
- **Cost.** The main cost is repeated traversal and sometimes materialization.
  The benefit is lower change cost when each concern evolves at a different
  pace.
- **Team topology.** Split Loop helps when different owners care about the two
  results. A billing team can review the billing pass without reading the
  analytics pass. It hurts when performance ownership requires every traversal
  to be visible and budgeted.
- **Cognitive load.** Split Loop lowers load for code review and later
  extraction. It raises load when the same input is far away from its second
  use, so good naming and adjacency matter.

The pattern favors separation of concerns over traversal minimality. That is
the whole bargain. When traversal minimality is the stronger force, keep one
loop and extract small helpers inside it.

The force that most often decides the question is not raw CPU time. It is the
cost of future mistakes. A combined loop invites edits that appear local but
are not: a developer changes the predicate for one accumulator and forgets that
the same `if` also protected another result. A split loop makes that mistake
more visible because the predicate is either copied, extracted, or removed from
one pass. That visibility is a design benefit, but it is paid for with another
read of the input.

There is also a force around deletion. When two outcomes share one loop, dead
code analysis is harder because a result can disappear while the loop still
looks active. After a split, deleting an output often deletes an entire pass.
That makes cleanup cheaper and lowers the chance that old metrics, stale
exports, or retired compatibility behavior remain attached to code that still
has one active concern.

## 4. Applicability and non-applicability

Reach for Split Loop when the following hold.

- A loop updates two or more accumulators that do not depend on each other.
- Each piece of work can be named as a separate sentence.
- The input can be traversed more than once without changing what it yields.
- The loop guard and iterator update do not have effects that a second pass
  would repeat incorrectly.
- Early exit is absent, or it applies to only one concern and can be moved with
  that concern.
- Exceptions from one concern should not prevent the other concern from being
  specified in the same loop body.
- A later Extract Function, Replace Loop with Pipeline, or parallel pass is
  blocked because unrelated statements are interleaved.
- Tests can compare the before and after result for representative inputs.

Do NOT reach for Split Loop in these non-applicability cases.

- **The input is single-use.** An iterator, generator, stream cursor, socket
  reader, database cursor, or message consumer may be exhausted by the first
  pass. Reason. A second pass will see no data unless the input is buffered,
  and buffering may change memory, latency, and failure behavior.
- **The loop is on a hot path over large data.** Reason. A second memory pass
  can harm cache locality and wall time. Measure before splitting, or keep one
  loop with extracted helpers.
- **The concerns interact per element.** Reason. If concern B reads concern
  A's per-iteration mutation, the order is part of the behavior.
- **The loop stops early.** Reason. A split can make one concern process
  elements the original loop never reached. Use the same stop condition in each
  pass only when that preserves the old behavior.
- **The loop owns a transaction, lock, or resource lifetime.** Reason. A split
  can lengthen the lifetime or perform work outside the protected region.
- **The loop body sends effects in item order.** Reason. Two passes change
  observable order from `A1, B1, A2, B2` to `A1, A2, B1, B2`.
- **The accumulators are one invariant.** Reason. `sum` and `count` for an
  average, numerator and denominator for a ratio, or min and max for a range
  may be clearer as one pass.
- **The second pass needs an expensive rematerialization.** Reason. Requerying
  a service or database to repeat traversal can change data and cost.
- **The loop guard has effects.** Reason. Repeating the guard can repeat those
  effects. Steinhöfel and Hähnle name side-effect-free guards as a precondition
  for Split Loop,
  https://link.springer.com/article/10.1007/s10817-023-09692-0, verified
  2026-08-02.
- **The split is meant to hide complexity rather than remove it.** Reason.
  Two loops with the same tangled condition are not a design improvement. Use
  Extract Function or Decompose Conditional first.

## 5. Structure

The participants are roles in the old loop and the new passes.

- **Source collection.** The finite input traversed by the original loop. It
  must be repeatable, or the refactoring must first materialize it into a
  repeatable collection.
- **Original combined loop.** The loop that interleaves independent concerns in
  one body.
- **Concern A.** One separable piece of work. It has its own accumulator,
  temporary values, predicates, and result.
- **Concern B.** A second separable piece of work. More concerns are allowed,
  but two is enough to prove the refactoring.
- **Accumulator A and Accumulator B.** The state owned by each concern. After
  the split, no pass writes the other pass's accumulator.
- **Pass A and Pass B.** The resulting loops. Each pass traverses the same
  source and performs one concern.
- **Result composer.** The statement or function that returns or publishes the
  results after the passes finish. It should not recreate the old tangle by
  mixing concern logic back together.
- **Equivalence tests.** Tests or characterization checks that prove the before
  and after code return the same result for normal, empty, boundary, and error
  inputs.

Relationships. The source collection feeds both passes. Each pass owns its
own accumulator. The result composer reads completed accumulators only after
both passes have run. No pass mutates the source in a way that changes the
other pass.

The structure is deliberately plain. A Split Loop does not require a strategy
object, visitor, command, collector framework, or event bus. Those may appear
later if the passes grow into separate responsibilities, but introducing them
in the same edit hides the value of the refactoring. The first structure should
be boring enough that a reviewer can compare the old loop body with the two
new bodies line by line.

Keep the result composer small. If the composer starts choosing which pass to
run, applying special cases, or merging partial results with business rules,
the design has moved beyond Split Loop. That may be the right next design, but
it should be named as a new change. In a clean Split Loop, the composer mostly
returns a record, passes both results to the caller, or assigns the completed
values to fields that were already assigned before the refactoring.

## 6. ASCII structure diagram

```
  BEFORE

  +----------------------+
  | Source collection    |
  +----------+-----------+
             |
             v
  +-------------------------------+
  | Combined loop                 |
  |-------------------------------|
  | for item in source:           |
  |   update accumulator A        |
  |   update accumulator B        |
  +----------+-----------+--------+
             |           |
             v           v
       +----------+ +----------+
       | Result A | | Result B |
       +----------+ +----------+

  AFTER

  +----------------------+
  | Source collection    |
  +-----+------------+---+
        |            |
        v            v
  +------------+  +------------+
  | Pass A     |  | Pass B     |
  |------------|  |------------|
  | updates A  |  | updates B  |
  +-----+------+  +------+-----+
        |                |
        v                v
  +------------+  +------------+
  | Result A   |  | Result B   |
  +-----+------+  +------+-----+
        |                |
        +--------+-------+
                 v
          +--------------+
          | Composer     |
          +--------------+
```

## 7. Dynamics

The runtime change is from interleaved per-element work to grouped per-concern
work. In the original loop, item order and concern order are interwoven. After
the split, concern order is visible at pass level.

```
  Combined loop over three items

  t0  read item 1
  t1  run A(item 1)
  t2  run B(item 1)
  t3  read item 2
  t4  run A(item 2)
  t5  run B(item 2)
  t6  read item 3
  t7  run A(item 3)
  t8  run B(item 3)
  t9  compose result

  Split loop over the same three items

  t0  read item 1       pass A
  t1  run A(item 1)
  t2  read item 2
  t3  run A(item 2)
  t4  read item 3
  t5  run A(item 3)
  t6  read item 1       pass B
  t7  run B(item 1)
  t8  read item 2
  t9  run B(item 2)
  t10 read item 3
  t11 run B(item 3)
  t12 compose result
```

The equivalence question is concrete. Can anything observe the difference
between `A1, B1, A2, B2` and `A1, A2, B1, B2`? If the answer is yes, the split
is not semantics-preserving. If the answer is no, the design question remains:
does the second shape make the code easier to change?

## 8. Implementation variants

**Straight split into adjacent loops.** The smallest edit duplicates the loop
header and moves statements into the matching loop. Keep the loops adjacent
until the tests pass. This makes review simple because the source collection,
guard, and update are visible twice.

Use this variant for most code reviews. It makes the diff longer, but the
review question is narrow: did each statement move to the pass that owns its
accumulator, and did no statement change? After that question is answered, the
loops can be renamed, extracted, or converted in smaller follow-up edits.

**Split, then Extract Function.** After the split, extract each pass into a
function named for the concern. This is often the final form when each result
has business meaning.

Use this variant when the caller reads better with names such as
`calculatePaidTotal(orders)` and `collectUnpaidCustomers(orders)`. The extracted
functions should receive the source and return a value. Avoid extracted
functions that mutate outer locals, because that recreates the hidden coupling
that the split was meant to remove.

**Split, then Replace Loop with Pipeline.** Each pass may become a pipeline
once it has one concern. Fowler's catalog records Replace Loop with Pipeline
as a separate refactoring, https://refactoring.com/catalog/replaceLoopWithPipeline.html,
verified 2026-08-02. Split Loop often makes that later move smaller.

**Materialize, then split.** If the input is an iterator but the data volume is
bounded, materialize it into a list first and document the cost. Do this only
when repeated traversal is worth the memory.

This variant changes the resource profile and therefore needs a clearer
contract than the straight split. Name the snapshot, keep its scope small, and
avoid materializing live data that can contain more records than the caller
expects. When the collection may be large, place the materialization behind a
limit or leave the loop combined.

**Split with a read model.** In domain code, it can be cleaner to build a small
read model first, such as a list of normalized order facts, and then run passes
over that read model. This is not free: it adds a type and a memory step. It is
worth considering when both passes currently repeat parsing, null handling, or
permission checks that should have one name.

**Split for parallelization.** Independent passes can sometimes run
concurrently after the split. The Springer article notes that Split Loop can
prepare code for parallelization,
https://link.springer.com/article/10.1007/s10817-023-09692-0, verified
2026-08-02. Treat that as a later optimization, not as a free benefit.

**Split by source partition rather than by concern.** This is a different
move. Partitioning divides the collection into chunks and runs the same work
on each chunk. Split Loop divides the work into concerns and runs each concern
over the collection. Mixing the two in one diff makes review harder.

**Split with a shared precomputed value.** Sometimes both concerns need an
expensive pure value derived from each item. Compute that value in a preparatory
mapping pass only when it has a domain name and is reused by both later passes.
Otherwise, a shared prepass can become a third concern that exists only because
the split was forced.

**TypeScript example.** TypeScript is useful here because arrays are repeatable
and the split remains visible.

```typescript
type Order = {
  customerId: string;
  amount: number;
  paid: boolean;
};

type Summary = {
  paidTotal: number;
  unpaidCustomers: string[];
};

export function summarizeOrders(orders: Order[]): Summary {
  let paidTotal = 0;
  for (const order of orders) {
    if (order.paid) {
      paidTotal += order.amount;
    }
  }

  const unpaidCustomers: string[] = [];
  for (const order of orders) {
    if (!order.paid) {
      unpaidCustomers.push(order.customerId);
    }
  }

  return { paidTotal, unpaidCustomers };
}

const result = summarizeOrders([
  { customerId: "a", amount: 30, paid: true },
  { customerId: "b", amount: 12, paid: false },
  { customerId: "c", amount: 8, paid: true },
]);

if (result.paidTotal !== 38 || result.unpaidCustomers.join(",") !== "b") {
  throw new Error("unexpected summary");
}
```

**Python example.** Python makes the single-use input problem easy to see. The
function accepts a `Sequence`, not an `Iterable`, because it needs repeatable
traversal.

```python
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class Reading:
    sensor: str
    value: float
    failed: bool


def summarize(readings: Sequence[Reading]) -> tuple[float, list[str]]:
    total = 0.0
    for reading in readings:
        if not reading.failed:
            total += reading.value

    failed_sensors: list[str] = []
    for reading in readings:
        if reading.failed:
            failed_sensors.append(reading.sensor)

    return total, failed_sensors


if __name__ == "__main__":
    data = [
        Reading("north", 3.5, False),
        Reading("east", 0.0, True),
        Reading("south", 2.0, False),
    ]
    assert summarize(data) == (5.5, ["east"])
```

**Go example.** Go slices are repeatable, and small helper functions often make
each pass cheap to test.

```go
package main

import "fmt"

type Ticket struct {
	Owner    string
	Minutes  int
	Billable bool
}

type Report struct {
	BillableMinutes int
	Nonbillable     []string
}

func BuildReport(tickets []Ticket) Report {
	billableMinutes := 0
	for _, ticket := range tickets {
		if ticket.Billable {
			billableMinutes += ticket.Minutes
		}
	}

	var nonbillable []string
	for _, ticket := range tickets {
		if !ticket.Billable {
			nonbillable = append(nonbillable, ticket.Owner)
		}
	}

	return Report{BillableMinutes: billableMinutes, Nonbillable: nonbillable}
}

func main() {
	report := BuildReport([]Ticket{
		{Owner: "Ada", Minutes: 30, Billable: true},
		{Owner: "Lin", Minutes: 15, Billable: false},
		{Owner: "Raj", Minutes: 20, Billable: true},
	})
	if report.BillableMinutes != 50 || fmt.Sprint(report.Nonbillable) != "[Lin]" {
		panic("unexpected report")
	}
}
```

## 9. Known production uses

The examples below are production code using the resulting separated-pass
shape. They are not cited as proof that the maintainers consciously applied
Fowler's refactoring.

**Apache Airflow, DAG rollup asset lookup.** `DAG.is_rollup_asset` reads
cached partition mapper entries with one pass for name matches and a second
pass for URI matches. The source comment explains that a name hit outranks a
URI hit and that URI-only entries need the second pass. Apache Airflow source,
`airflow-core/src/airflow/models/dag.py`,
https://github.com/apache/airflow/blob/main/airflow-core/src/airflow/models/dag.py,
verified 2026-08-02.

**Hugging Face Accelerate, bitsandbytes parameter conversion.** In
`accelerate/utils/bnb.py`, the loaded-model quantization path first visits
named parameters with `remove_duplicate=False`, then performs a second pass
over named modules so keep-in-fp32 modules remain float32 when tied weights
would otherwise be missed. Hugging Face Accelerate source,
https://github.com/huggingface/accelerate/blob/main/src/accelerate/utils/bnb.py,
verified 2026-08-02.

**llama.cpp, ggml ET CPU comparison.** The comparison code checks every output
element for mismatches in one pass, then logs detailed information for a capped
number of elements in a second pass. The first pass owns correctness over the
whole tensor; the second pass owns diagnostic volume. llama.cpp source,
`ggml/src/ggml-et/ggml-et-cpu-compare.cpp`,
https://github.com/ggml-org/llama.cpp/blob/master/ggml/src/ggml-et/ggml-et-cpu-compare.cpp,
verified 2026-08-02.

Judgement. These uses show three different reasons to keep passes separate:
precedence rules, alias coverage, and diagnostic budget. That variety is the
reason Split Loop belongs in a refactoring catalog rather than only in a
performance discussion.

The common thread is policy separation. Airflow separates priority policy from
fallback lookup. Accelerate separates ordinary dtype conversion from tied-weight
repair. llama.cpp separates full correctness checking from bounded debug
output. None of those cases would become clearer by forcing every decision back
into one pass unless a measurement or API contract demanded it.

These examples also show why "production use" should not be read as a license
to split every loop. Each source has a local reason in comments or code shape.
Airflow has precedence. Accelerate has aliasing. llama.cpp has diagnostic
volume. A split with no comparable reason is weaker than a combined loop with a
clear comment.

## 10. Consequences

Positive.

- Each loop has one concern, which makes review and naming easier.
- Each accumulator has a shorter conceptual lifetime and fewer writers.
- Each pass can be extracted, tested, timed, logged, or replaced alone.
- Changes to one concern no longer require reading unrelated statements inside
  the same loop body.
- A pass that becomes unused can be removed without touching the other pass.
- Independent passes may become candidates for pipelines, queries, or parallel
  execution.
- Error handling can become more honest. One pass can fail with a label tied
  to its concern.

Negative.

- The input is traversed more than once.
- Single-use sources must be buffered or rejected.
- Item-level effect order changes unless the passes are pure.
- A combined invariant may become harder to see if it is split by mistake.
- Logs and traces may change from item order to pass order.
- The code can become longer before later extraction makes it shorter.
- Performance reviewers may have to re-check cache behavior, remote reads, and
  memory allocation.

Judgement. The best outcome is not "more loops." The best outcome is that each
remaining loop has a nameable job and a clear owner. If the split creates two
vague loops, the refactoring stopped too early.

There is also a social consequence. Split Loop makes local ownership visible.
That can improve review because a domain reviewer can focus on one pass. It can
also expose an uncomfortable fact: the original loop bundled work from two
teams because neither team owned the boundary. Treat that as useful design
feedback. Do not hide it by naming both passes after technical details such as
`firstPass` and `secondPass`.

Another consequence is that comments often become either better or unnecessary.
In a combined loop, comments tend to mark regions inside the body. After a
split, the loop or extracted function name can carry that meaning. If the same
comment has to be copied above both passes, the split probably missed a shared
rule that should be extracted.

## 11. Failure modes and misuse

**Single-use source consumed twice.** Symptom. The first result is correct and
the second result is empty, or a generator-based test passes only when the
input is a list. Cause. The original loop accepted a one-shot iterator, and the
split assumes repeatable traversal. Fix. Change the contract to require a
repeatable collection, materialize once with an explicit memory budget, or keep
one loop.

**Hidden dependency between concerns.** Symptom. The second pass produces
different values from the old code for items after the first mutation. Cause.
Concern B read state that concern A changed during the same iteration. Fix.
Move the dependent state into one concern, or compute an intermediate snapshot
that both passes read.

**Changed effect order.** Symptom. Audit logs, outbound messages, metrics, or
database writes appear grouped by concern instead of by item. Cause. The loop
was split even though effects were observable. Fix. Keep one loop for effects,
or record data in pure passes and publish effects in the required order.

**Early exit drift.** Symptom. The new code processes elements after the point
where the old loop would break, or it misses work that used to run before a
break. Cause. A `break`, `return`, exception, or control flag belonged to the
combined control flow. Fix. Extract and test the stop condition before the
split, or leave the control-flow loop intact.

**Repeated remote read.** Symptom. A slow endpoint or database query now runs
twice, or results disagree because the remote data changed between passes.
Cause. The "collection" was a live remote cursor or lazy query. Fix. Materialize
once inside a named boundary, or push both computations into one query.

**False readability win.** Symptom. Two loops repeat the same long condition
and reviewers must compare them character by character. Cause. The concern was
not isolated before splitting. Fix. Extract the condition, slide statements
into coherent groups, or use Decompose Conditional first.

**Accumulator reset bug.** Symptom. The second pass starts with state left over
from a prior call or prior test. Cause. Variables moved during the split were
not initialized near their pass. Fix. Declare and initialize each accumulator
immediately before its pass.

**Performance surprise.** Symptom. CPU time or cache misses rise after a clean
review, often in batch jobs. Cause. The input is large enough that repeated
memory traversal matters. Fix. Measure, then decide between loop fusion,
chunked processing, or one loop with extracted helpers.

**Divergent predicates.** Symptom. Two passes begin with predicates that look
almost the same, but one includes a new term and the other does not. Defects
appear only for edge records that satisfy one predicate and fail the other.
Cause. A shared filtering rule was duplicated during the split, then changed in
one pass. Fix. Extract the predicate into a named query when the rule is meant
to be shared, or give the predicates different names when divergence is the
intent.

**Lost adjacency after extraction.** Symptom. A reader finds one pass near the
top of the file and the related pass several screens away, with no obvious
caller showing their order. Cause. The loops were extracted before the
relationship was named at the call site. Fix. Keep the orchestration function
short and explicit, with the pass calls adjacent and named by result.

## 12. Trade-off matrix

| Force | Split Loop | Extract Function inside loop | Replace Loop with Pipeline | Loop Fusion | Single pass with tuple accumulator |
|---|---|---|---|---|---|
| Clarity | High when concerns are independent | Medium. Names help, order stays mixed | High for data transforms | Low when concerns differ | Medium for small summaries |
| Latency | Lower on hot paths due to repeated traversal | Preserves one pass | Depends on laziness and fusion | Best for traversal count | Best for traversal count |
| Coupling | Low between concerns | Medium. Helpers may still share locals | Low if stages are pure | High between fused concerns | Medium. Tuple fields can drift |
| Consistency | Strong per concern, weak for per-item atomicity | Strong per item | Strong by stage | Strong per item | Strong for combined invariant |
| Operability | Strong pass-level labels | Strong if helpers are traced | Needs stage labels | One loop label unless instrumented | One summary label |
| Cost of change | Low per concern | Medium | Low when operators fit | High. One change touches the fused body | Medium |
| Team topology | Good for separate owners | Good for shared loop owners | Good for dataflow teams | Good for performance owners | Good for a single owner |
| Cognitive load | Low after naming, higher traversal count | Low for imperative readers | Low for pipeline-fluent readers | High when body grows | Low until tuple meaning grows |
| Single-use input | Poor unless buffered | Good | Depends on API | Good | Good |
| Parallelization path | Good if passes are pure | Limited | Good in stream engines | Poor by design | Limited |

Reading of the table. Split Loop wins when the two concerns will change
separately. Extract Function inside the loop wins when per-item order matters.
Replace Loop with Pipeline wins when each concern is already a collection
operation. Loop Fusion wins when traversal cost is the dominant force. A tuple
accumulator wins when the values are one invariant and should be updated
together.

## 13. Related and incompatible patterns

- **Slide Statements.** Often comes first. Move statements so each concern is
  contiguous inside the original loop, then split. The Slide Statements entry
  cites Fowler's chapter 8 treatment and the public catalog page for that
  refactoring.
- **Extract Function.** Usually follows. Once a pass has one concern, extract
  it into a function named for the result it computes.
- **Split Variable.** Supports the move when one local variable is reused for
  two meanings inside the original loop. Split the variable before splitting
  the loop.
- **Separate Query from Modifier.** Composes when one pass computes a value and
  the other mutates state. Separate the pure query from the modifier before
  deciding whether the modifier still belongs in a loop.
- **Replace Loop with Pipeline.** Often follows Split Loop. A single-concern
  pass is easier to turn into `filter`, `map`, `sum`, `group`, or `collect`.
- **Decompose Conditional.** Helps when both candidate passes repeat a dense
  predicate. Name the predicate first so the split does not duplicate mystery.
- **Loop Fusion.** The direct inverse. It conflicts when performance, cache
  locality, or single-use traversal dominates clarity. Fusion may be the right
  refactoring out of Split Loop.
- **Iterator and Generator patterns.** They can conflict because many iterator
  values are single-use. If the input cannot be rewound, Split Loop must change
  the contract or materialize the values.
- **Map Reduce.** Related at a larger scale. A split can expose separate map or
  reduce jobs, but Map Reduce is a distributed computation pattern, not a local
  refactoring.

## 14. Refactoring path in and out

Introducing Split Loop.

1. Characterize the current behavior with tests. Cover empty input, one item,
   several items, boundary values, and any current early exit or exception.
2. Name the concerns in comments or scratch notes. If you cannot name them,
   apply Extract Function or Decompose Conditional before splitting.
3. Identify each accumulator and the statements that write it. Check whether
   any statement writes both accumulators.
4. Use Slide Statements to group statements for concern A and concern B inside
   the original loop without changing behavior.
5. Duplicate the loop header immediately below the original loop. Do not move
   the loops far apart yet.
6. Move concern B statements into the second loop. Leave concern A statements
   in the first loop. Initialize each accumulator directly before its loop.
7. Re-run tests. If tests fail, the concerns were not independent. Inspect
   reads, writes, early exits, effects, and iterator state.
8. Extract each loop into a named function if the name improves the caller.
9. Consider Replace Loop with Pipeline on each pass, but only where the
   pipeline reads better than the loop.
10. Add observability labels if the code runs in production and the pass cost
   or failure rate matters.

Refactoring out when Split Loop stops earning its place.

1. Confirm why it no longer pays. The usual reasons are hot-path traversal
   cost, a single-use source, or a pair of results that became one invariant.
2. Preserve pass names by extracting the body of each pass into small helpers
   that accept one item and the relevant accumulator.
3. Create one combined loop and call the helpers in the old item order.
4. Keep accumulator initialization near the combined loop.
5. Run characterization tests and performance checks.
6. Inline helpers only if they no longer add useful names.
7. If the target is performance, record the measurement that justified loop
   fusion so future readers do not split it again by habit.

## 15. Testing and verification

Judgement. Testing Split Loop is about proving independence, not about testing
the syntax of two loops.

Characterization tests are the first guard. Run the old behavior and record
the result for ordinary input, empty input, duplicate values, values that
exercise each branch, and boundary values. If the loop had effects, record the
effect order too. The test should fail if pass order changes an observable
sequence.

Property tests are useful when the loop computes summaries. Generate lists and
assert that the split version returns the same result as a simple reference
implementation. For a total plus a list, compare both fields. For maps or sets,
compare as unordered data when order is not part of the contract.

Use single-use input tests to protect the contract. If a function now requires
a repeatable sequence, pass a generator in a test and assert that the function
rejects it or materializes it explicitly. Silent generator exhaustion is one of
the easiest bugs to miss.

Regression tests should include records that affect only concern A, only
concern B, both concerns, and neither concern. That four-case shape catches
predicate drift. For example, if one pass handles paid orders and the other
handles unpaid customers, include refunded, pending, paid, and unpaid records
if those states exist in the domain. The goal is not a large test matrix. It is
to make each concern's membership rule visible.

Use mutation tests or spy objects when effects are present. A spy can record
`A(item)` and `B(item)` calls. If the old observable order matters, the spy
test should force the code to stay combined. If the effects are removed before
the split, the spy should disappear.

Performance tests are not always needed, but they matter for large inputs.
Benchmark the old loop and split loops with realistic input sizes. Count
allocations as well as time. In Go, `go test -bench` with allocation reporting
is the natural tool. In Python, a small benchmark can catch accidental list
materialization. In TypeScript, benchmark with representative arrays rather
than tiny fixtures.

Review checks.

- Each pass initializes and writes only its own accumulator.
- The source collection is repeatable or materialized once.
- The loops are adjacent until a later extraction gives them names.
- The split did not duplicate a long condition that should be extracted.
- Early exits, exceptions, and effects are explicitly tested.

For code samples and documentation, compile or run each language example as a
separate artifact. A refactoring entry that teaches a structural move should
not leave readers guessing whether the examples type-check.

A useful review technique is a temporary dual implementation. Keep the old
combined loop in a test helper, implement the split version, and assert equality
across generated inputs. Delete the helper after the refactoring lands unless
it remains valuable as a reference oracle. This keeps the production code clean
while giving reviewers a stronger signal than hand inspection alone.

## 16. Observability signals

Judgement. Split Loop changes where work happens, so production telemetry
should make the new pass boundaries visible when the loop is on a meaningful
path.

Record one span or timer per pass when the input can be large. Use labels such
as `pass=paid_total` and `pass=unpaid_customers`, not `pass=first` and
`pass=second`. Count input items seen by each pass. The counts should normally
match for a repeatable collection. A mismatch is a strong signal that the
source is single-use, filtered in the wrong place, or mutated between passes.

Record result sizes by pass. For example, `unpaid_customers.count` and
`paid_total.amount` make the output shape visible without logging sensitive
records. If a pass produces diagnostics, also record how many records were
suppressed by caps or sampling.

Record failures with the pass name. A combined loop often reports one generic
failure label. After the split, an exception in the billing pass should not be
indistinguishable from an exception in the reporting pass.

A healthy dashboard shows both pass durations scaling with input size, stable
input counts, and expected result ratios. A failing dashboard shows one pass
seeing zero items while the other sees many, one pass duration growing faster
than input size, or a new error label tied to only one pass.

Use logs sparingly. Per-item logs can double after a split if copied into both
passes. Prefer pass summaries and targeted debug logs with sampling.

For privacy-sensitive systems, prefer metrics that describe shape over metrics
that describe contents. A pass can usually report `items_seen`, `items_matched`,
`duration_ms`, and `result_count` without exposing identifiers. When identifiers
are needed for diagnosis, log them only under a debug gate and with the same
redaction policy used by the rest of the service.

## 17. Security and privacy implications

Judgement. Split Loop is not a security pattern. Its security impact comes
from changed ordering, repeated reads, and new telemetry.

Authorization and validation order can change accidentally. If the old loop
validated an item before any other action on that item, a split must not move
processing into a pass that runs before validation. Keep validation in one
combined loop, or create a first pass that builds a validated snapshot and make
later passes consume only that snapshot.

Repeated traversal can repeat reads of sensitive data. When the source is a
cursor over personal data, materializing it for a split creates a new data
retention surface. Name the lifetime of that buffer and delete it as soon as
the passes finish. Do not add debug logs that print the buffered data.

Effect order can be part of an audit contract. If the old code wrote an audit
record next to each mutation, splitting audit and mutation into different
passes may create a window where a mutation exists without its audit record.
That is a behavior change, not a refactoring.

Telemetry can leak pass-specific counts. A count of failed payments, flagged
records, or private categories can be sensitive at low cardinality. Aggregate,
bucket, or suppress labels where the count itself reveals private information.

Single-use security streams should not be replayed. Token streams, signed
event streams, and one-time cursors may reject a second pass or produce
different data. Treat repeatability as part of the security contract, not as a
minor implementation detail.

## 18. References

- Martin Fowler, with Kent Beck, *Refactoring. Improving the Design of
  Existing Code*, 2nd edition, Addison-Wesley, 2018, chapter 8, "Moving
  Features," catalog entry "Split Loop."
- Martin Fowler, "Split Loop," refactoring catalog,
  https://refactoring.com/catalog/splitLoop.html, verified 2026-08-02.
- Martin Fowler, "Replace Loop with Pipeline," refactoring catalog,
  https://refactoring.com/catalog/replaceLoopWithPipeline.html, verified
  2026-08-02.
- Martin Fowler, "Refactoring with Loops and Collection Pipelines," 2015,
  https://martinfowler.com/articles/refactoring-pipelines.html, verified
  2026-08-02.
- Dominic Steinhöfel and Reiner Hähnle, "Schematic Program Proofs with
  Abstract Execution," *Journal of Automated Reasoning*, Springer, 2024,
  section 5.1 discussion of Split Loop,
  https://link.springer.com/article/10.1007/s10817-023-09692-0, verified
  2026-08-02.
- Apache Airflow project, `DAG.is_rollup_asset` in
  `airflow-core/src/airflow/models/dag.py`,
  https://github.com/apache/airflow/blob/main/airflow-core/src/airflow/models/dag.py,
  verified 2026-08-02.
- Hugging Face Accelerate project, bitsandbytes utility in
  `src/accelerate/utils/bnb.py`,
  https://github.com/huggingface/accelerate/blob/main/src/accelerate/utils/bnb.py,
  verified 2026-08-02.
- ggml-org llama.cpp project, ET CPU comparison in
  `ggml/src/ggml-et/ggml-et-cpu-compare.cpp`,
  https://github.com/ggml-org/llama.cpp/blob/master/ggml/src/ggml-et/ggml-et-cpu-compare.cpp,
  verified 2026-08-02.
