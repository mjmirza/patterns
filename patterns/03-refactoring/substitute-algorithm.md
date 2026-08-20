---
name: Substitute Algorithm
slug: substitute-algorithm
family: 03-refactoring
category: Refactoring
aliases: [Replace Algorithm, Algorithm Substitution]
first_described: "Fowler 1999"
maturity: established
related: [extract-function, replace-loop-with-pipeline, split-phase, separate-query-from-modifier, replace-conditional-with-polymorphism]
incompatible_with: [speculative-rewrite, untested-behavior-change]
verified: 2026-08-02
---

# Substitute Algorithm

## 1. Name, aliases, and lineage

The canonical name is **Substitute Algorithm**. Martin Fowler catalogs it under
that name in *Refactoring. Improving the Design of Existing Code*, first
edition, Addison-Wesley, 1999, chapter 6, "Composing Methods", catalog entry
"Substitute Algorithm." The second edition keeps the same name in Martin
Fowler, with Kent Beck, *Refactoring. Improving the Design of Existing Code*,
second edition, Addison-Wesley, 2018, chapter 6, "A First Set of Refactorings."
Fowler's public catalog page also records the named refactoring and shows the
change from a manual search with repeated conditionals to a shorter search
over a candidate set (https://refactoring.com/catalog/substituteAlgorithm.html,
verified 2026-08-02). Fowler's article on second edition changes lists
Substitute Algorithm as kept from the first edition at page 139
(https://martinfowler.com/articles/refactoring-2nd-changes.html, verified
2026-08-02).

The common aliases are **Replace Algorithm** and **Algorithm Substitution**.
They are accurate enough in conversation, but this entry uses Fowler's name
because the refactoring is not the same thing as inventing a new algorithm in a
greenfield module. The old code already exists. It already has observable
behavior. The refactoring changes the internal method for reaching the same
answer, or a deliberately revised answer recorded by tests and review.

The word "algorithm" is broader here than a named textbook sort or graph
method. It may mean a route selection rule, a pricing calculation, a parser
decision, a scheduler, a merge plan, a cache eviction rule, or a hand-written
loop that can be replaced by a clearer library operation. Donald Knuth's *The
Art of Computer Programming*, volume 3, second edition, Addison-Wesley, 1998,
chapter 5, "Sorting", and Thomas H. Cormen, Charles E. Leiserson, Ronald L.
Rivest and Clifford Stein, *Introduction to Algorithms*, third edition, MIT
Press, 2009, chapters 2, 6, 7, 8, and 15, are useful background for algorithm
properties, but this catalog entry is a refactoring entry. Its first concern is
changing working software without losing the behavior clients rely on.

Judgement. The name is easy to misuse. Many failed rewrites are advertised as
algorithm substitution, but they change the product contract, delete edge-case
handling, or replace a known slow path with a clever path that nobody can
operate. A master-level use of the refactoring starts with an executable
behavior record, not with enthusiasm for the new method.

## 2. Problem and context

A function uses an algorithm that has become the wrong way to express its
behavior. The old code may be slow, too long, too branchy, too hard to prove,
too hard to test, or built around an assumption that no longer holds. The
result may still be correct for common cases, which is why this refactoring
often appears late. The code is not broken enough to force a feature project,
but it is expensive every time somebody needs to read it or tune it.

The problem shows up in ordinary code shapes. A loop scans a list with a dozen
special cases where a set lookup would say the same thing. A nested conditional
implements a precedence rule that belongs in a table. A quadratic deduplication
pass handles ten records well but now receives ten million. A parser walks
characters with flags where a small state machine would make the states plain.
A matching rule compares every candidate against every request even though the
data can be indexed once. A stable result order was once irrelevant, then a
caller began relying on it. A routine tuned for random data is now fed mostly
sorted data. Each case calls for a different replacement, but the refactoring
move is the same: isolate the old algorithm, pin down its contract, build the
new one beside it, then replace the body when the evidence is good enough.

The context that makes Substitute Algorithm a refactoring rather than a
feature rewrite has four parts.

- The algorithm is behind a stable function, method, command, or endpoint.
- The caller-visible contract can be described independently from the current
  implementation.
- Tests, examples, traces, or captured production cases can compare old and new
  behavior.
- The new algorithm has a clear reason to exist, such as simpler expression,
  lower asymptotic cost, better worst-case behavior, stable ordering, lower
  memory use, or a stronger correctness argument.

The contract can be exact or intentionally revised. Exact substitution means
every allowed input returns the same output and observable effects remain the
same. Intentional revision means the team records a contract change, such as
"sort is now stable" or "ties now break by creation time." That can still use
the mechanics of this refactoring, but it must not be called behavior
preserving. Fowler's public book page describes refactoring as controlled
behavior-preserving transformation
(https://martinfowler.com/books/refactoring.html, verified 2026-08-02). When
the output contract changes, the work has crossed from pure refactoring into a
small design change with a refactoring-style migration.

The hard part is often not writing the replacement. It is learning what the old
algorithm really promised. Mature systems hold implicit contracts in bug
reports, dashboards, serialized files, database rows, client retries, and tests
that assert accidental order. An algorithm that looks excessive may be carrying
one of those contracts. The substitution is ready only when the team can say
which details are preserved, which are intentionally changed, and which are
irrelevant.

## 3. Forces

Judgement. This dimension weighs forces. The cited sources establish names and
real systems, while the balance below depends on local code, runtime, data, and
team skill.

- **Latency.** Favoured when the new algorithm lowers average or tail cost for
  real inputs. Sacrificed when setup cost, allocation, indexing, or generic
  dispatch makes the new path slower for the small inputs that dominate.
- **Coupling.** Favoured when a shorter algorithm removes dependency on hidden
  flags, shared mutation, or scattered helper calls. Sacrificed when the new
  algorithm imports a large library or binds the code to a specialized data
  structure.
- **Consistency.** Favoured when a known algorithm has clearer invariants and a
  simpler tie-breaking rule. Sacrificed when the old behavior was not fully
  specified and callers depended on accidental details.
- **Operability.** Favoured when the new algorithm has named phases, counters,
  and failure states. Sacrificed when it becomes a black box with fewer
  breakpoints and less local logging.
- **Cost.** Favoured when the new method reduces CPU, memory, network calls, or
  maintenance effort. Sacrificed when migration requires duplicate execution,
  shadow comparison, data backfill, or new infrastructure.
- **Team topology.** Favoured when one team can replace an algorithm behind a
  narrow API without changing every caller. Sacrificed when the algorithm's
  quirks are known only by downstream teams and the owning team lacks their
  test cases.
- **Cognitive load.** Favoured when the replacement is a standard library
  operation, a table, a named algorithm, or a small composition of pure
  functions. Sacrificed when the replacement is faster but requires a proof the
  team cannot maintain.
- **Risk.** Sacrificed during the change window. Even a better algorithm can
  produce different order, timing, memory pressure, or exception behavior.

Substitute Algorithm favours clarity and fit to real input. It sacrifices the
comfort of code that has survived production by age alone. That trade is good
when the old algorithm is isolated and well characterized. It is poor when the
old code is entangled with side effects and nobody knows which outcomes matter.

## 4. Applicability and non-applicability

Reach for Substitute Algorithm when these conditions hold.

- A function's result is easier to specify than its current implementation is
  to understand.
- A known algorithm or standard library operation expresses the same contract
  with less code.
- A performance profile points to the algorithm, not to I/O, allocation outside
  the function, logging, database queries, or caller behavior.
- The old implementation has grown defensive branches that can be replaced by
  a data structure with the rule encoded in it.
- A stable API boundary lets the replacement happen inside one function or
  module.
- Golden tests, property tests, differential tests, or captured production
  cases can compare old and new paths.
- The desired change is a local algorithm swap, not a product workflow change.
- The new algorithm's edge cases are better documented than the old path's edge
  cases.

Non-applicability list.

- **The contract is unknown.** Reason. If nobody can state what inputs are
  valid, how ties break, what happens on missing data, and which exceptions are
  allowed, there is no target to preserve. Characterize the behavior first.
- **The function mixes algorithm and effects.** Reason. A routine that sends
  emails, updates rows, mutates globals, and computes a result is not ready for
  a direct swap. Use Separate Query from Modifier and Extract Function first.
- **The issue is the wrong abstraction, not the wrong algorithm.** Reason. A
  faster search inside a poor domain model may hide the smell. Replace
  Primitive with Object, Split Phase, or a domain-level redesign may be the
  better path.
- **The new method changes observable order without a product decision.**
  Reason. Sorting, grouping, hashing, traversal, and parallel execution often
  alter tie order. Treat order as part of the contract unless the API says it
  is unspecified.
- **The data size is small and stable.** Reason. A complex asymptotic win may
  lose to a plain loop at ten elements, while making the code harder to read.
- **The old algorithm encodes domain exceptions.** Reason. Replacing it with a
  textbook routine may delete business rules. Extract and name each exception
  before substitution.
- **The replacement needs a dependency the service cannot operate.** Reason.
  Some algorithms require indexes, model files, native code, or large memory
  buffers. If operations cannot deploy, monitor, or roll back those parts, the
  refactoring is not ready.
- **The team wants a rewrite because the code feels old.** Reason. Age is not a
  defect. Substitute when there is a named force to improve and a way to verify
  the result.

## 5. Structure

Substitute Algorithm has five participants. They are roles in a change, not
classes in a runtime design.

- **Stable Entry Point.** The function, method, endpoint, command, or module API
  callers already use. It owns the externally visible contract and is the place
  where the new algorithm eventually lands.
- **Old Algorithm.** The current implementation. Before the swap, it may need
  extraction into its own function so it can be compared against the new path.
- **Behavior Oracle.** Tests, fixtures, properties, traces, production samples,
  formal invariants, or review rules that say whether the result is acceptable.
  Without this participant the change is a rewrite by hope.
- **Replacement Algorithm.** The new implementation. It may be a library call,
  a table-driven rule, a different data structure, a known named algorithm, or
  simpler code written for the domain.
- **Equivalence Rig.** A temporary structure that runs old and new on the
  same inputs, compares outputs, records differences, and lets the team decide
  whether the differences are defects or contract changes.

The relationship is intentionally temporary. During the refactoring, the stable
entry point may call the old algorithm while tests call both, or a feature flag
may shadow the new algorithm in production while returning the old answer. When
confidence is earned, the old algorithm and rig are deleted. A completed
Substitute Algorithm refactoring should not leave two live algorithms unless
the product now truly supports two modes.

The replacement must be smaller in one important dimension. That dimension may
be code size, proof size, runtime cost, memory footprint, edge-case count,
operational noise, or the number of concepts a reader carries. A replacement
that is larger in every dimension is not a substitution. It is expansion.

## 6. ASCII structure diagram

```text
        before                              during

 +-------------------+              +-------------------+
 | Stable Entry Point|              | Stable Entry Point|
 |-------------------|              |-------------------|
 | calls old logic   |              | calls old logic   |
 +---------+---------+              +---------+---------+
           |                                  |
           v                                  v
 +-------------------+              +-------------------+
 |   Old Algorithm   |              |   Old Algorithm   |
 |-------------------|              +---------+---------+
 | mixed loops,      |                        |
 | branches, state   |                        | same input
 +-------------------+                        v
                                  +-----------+-----------+
                                  | Equivalence Rig   |
                                  |-----------------------|
                                  | compares old and new  |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  | Replacement Algorithm |
                                  +-----------------------+

        after

 +-------------------+              +-----------------------+
 | Stable Entry Point|------------->| Replacement Algorithm |
 |-------------------|              |-----------------------|
 | same public API   |              | clearer rule or cost  |
 +-------------------+              +-----------------------+

 Old Algorithm and Equivalence Rig are removed after the swap.
```

## 7. Dynamics

The runtime dynamics differ by risk level. In a low-risk local function, the
comparison happens only in tests. In a high-risk system, the comparison may run
in production as shadow execution while the old answer is still returned.

```text
Developer          Test Runner        Old Algorithm      New Algorithm
    |                  |                    |                  |
    | write fixture    |                    |                  |
    |----------------->|                    |                  |
    |                  | call old(input)    |                  |
    |                  |------------------->|                  |
    |                  |<-------------------|                  |
    |                  | call new(input)                       |
    |                  |-------------------------------------->|
    |                  |<--------------------------------------|
    |                  | compare output, errors, order, cost   |
    |                  |---------------------------------------|
    |                  | pass, or record a contract question   |
    |<-----------------|                    |                  |
    | replace body     |                    |                  |
    |----------------->|                    |                  |
```

For a production shadow rollout, the caller still receives the old result at
first. The service runs the new algorithm on sampled requests, logs a digest of
both answers, and counts mismatches by reason. After mismatch rate is explained
and the cost budget is acceptable, the service flips the returned answer to the
new path. The old path remains available for rollback only as long as rollback
is a real operation. Then it is removed.

This dynamic has a useful discipline. The new algorithm is not allowed to
rewrite the caller contract while the comparison rig is pretending to test
equivalence. If a difference is accepted, the behavior oracle changes first.
That makes the product decision visible in code review.

## 8. Implementation variants

**Library substitution.** Replace hand-written logic with a standard library
operation. Examples include set membership rather than repeated equality
checks, a stable sort rather than a manual insertion routine, `bisect` rather
than a custom binary search, or a parser combinator in place of manual token
flags. This variant buys readability and reduces code ownership. It costs
dependency on the library's documented contract. Cite that contract in code
review when the behavior matters.

**Data structure substitution.** Keep the operation but change the shape of the
data. A nested loop over users and permissions becomes a map from user id to
permission set. A repeated prefix scan becomes a trie. A last-write-wins merge
uses a hash keyed by entity id. This variant often changes space for time. It
must state build cost, memory cost, and invalidation rules.

**Table-driven substitution.** Replace a branch tree with a table of cases,
predicates, weights, or transitions. This works well when the old logic is a
policy matrix and poor when the old logic has real procedural flow. The table
should be data, not hidden code in strings.

**Known algorithm substitution.** Replace a local routine with a named
algorithm whose properties match the inputs. Examples include moving from
quicksort to a stable adaptive mergesort variant, from naive substring search
to a linear-time search, or from repeated shortest path calculation to a
precomputed graph index. This variant needs benchmark and invariant review.

**Approximation substitution.** Replace exact work with approximate work, such
as sketches, bloom filters, reservoir sampling, or approximate nearest-neighbor
search. This is not a pure refactoring unless the public contract already
allowed approximation. If the product contract changes, label the work as a
behavior change.

**Parallel substitution.** Replace a serial algorithm with a parallel or
vectorized one. This can lower wall-clock time and raise CPU, memory, and
ordering risk. It is most useful when the operation is pure, associative where
needed, and has clear chunk boundaries.

**Incremental substitution.** Replace a batch algorithm with an incremental
one. A full recomputation becomes maintenance of a running index or cache. This
can improve latency while adding invalidation complexity. The tests must cover
create, update, delete, replay, and recovery paths.

**Language-shaped substitution.** In TypeScript and Python, short array or
iterator operations can replace loops when the operation is selection or
projection. In Go, a plain loop may still be clearer, so substitution may mean
using a map or sorting helper rather than forcing a fluent pipeline. In Rust,
iterators and ownership make pure transformations clear, while sort methods
carry documented contracts for stability and allocation
(https://doc.rust-lang.org/std/primitive.slice.html, verified 2026-08-02).

## 9. Known production uses

**CPython list sorting.** CPython's `Objects/listsort.txt` describes the list
sort implementation as an adaptive, stable, natural mergesort called Timsort
and compares it with Python's previous samplesort hybrid. The same document
states that current code uses the powersort merge strategy from Munro and Wild
(https://github.com/python/cpython/blob/main/Objects/listsort.txt, verified
2026-08-02). This is a production-grade example of substituting one sorting
algorithm for another because real input shape, stability, comparison cost, and
merge policy mattered.

**V8 `Array.prototype.sort`.** The V8 team wrote that `Array.prototype.sort`
and `TypedArray.prototype.sort` had relied on a Quicksort implementation with
an insertion-sort fallback, and that V8 later used Timsort for stable
`Array#sort` in V8 7.0 and Chrome 70
(https://v8.dev/blog/array-sort, verified 2026-08-02). The V8 stable sort note
also says the JavaScript specification requires stability while engines remain
free to choose the implementation algorithm, and names V8's Timsort choice
(https://v8.dev/features/stable-sort, verified 2026-08-02). This production
case shows a substitution where a product-level contract, stable sorting,
became part of the reason for the algorithm change.

**Rust standard library slice sorting.** Rust 1.81 release notes state that
the sort implementations were replaced with stable driftsort and unstable
ipnsort for `slice::sort*` and `slice::select_nth*` methods
(https://chromium.googlesource.com/external/github.com/rust-lang/rust/%2Bshow/f21fbac535ab2c3bc50db20547f4d48477357103/RELEASES.md,
verified 2026-08-02). The current Rust slice documentation describes stable
sort as based on driftsort and unstable sort as based on ipnsort
(https://doc.rust-lang.org/std/primitive.slice.html, verified 2026-08-02). This
case is a direct production substitution in a standard library surface where
panic behavior, stability, allocation, and order properties are part of the
contract.

Judgement. These examples are sorting-heavy because sorting algorithms are
publicly documented and easy to verify. The same refactoring appears in pricing
engines, schedulers, matchers, import deduplication, and route planners, but a
master catalog should prefer named public evidence over private anecdotes.

## 10. Consequences

Positive consequences.

- The stable entry point can become shorter and easier to read.
- The new algorithm may have better average cost, tail cost, memory behavior,
  or worst-case bounds for the inputs that matter.
- Edge cases can become explicit because the behavior oracle must name them.
- The team may delete old defensive code that is no longer needed under the new
  method's invariants.
- The replacement may align the system with language or platform contracts,
  such as a stable sort requirement.
- A named algorithm makes review easier when reviewers can check known
  properties instead of reverse-engineering local code.
- Shadow comparison can expose hidden caller expectations before they become
  incidents.

Negative consequences.

- Behavior can drift in small ways: ordering, rounding, tie breaks, exception
  class, log shape, timing, memory use, or duplicate handling.
- A faster algorithm can make the code harder for the team to maintain.
- The new method may move risk into setup cost, precomputed indexes, cache
  invalidation, or dependency updates.
- Benchmarks can lie when they use random inputs while production data has
  structure, skew, duplicates, or adversarial cases.
- Temporary dual execution can double CPU, memory, or downstream calls if the
  algorithm is not pure.
- The old algorithm may have carried business exceptions that were not covered
  by tests.
- A replacement may prevent local debugging if the old hand-written steps are
  folded into an opaque library call.

Judgement. The best consequence is not speed by itself. It is a smaller
explanation. After the refactoring, the owner should be able to explain why the
algorithm fits the contract in a few sentences and point to tests that guard
the important cases.

## 11. Failure modes and misuse

Judgement. These are common production failure shapes. They should be reviewed
as Symptom, Cause, Fix triples because the visible symptom is what an on-call
engineer will see first.

- **Symptom.** Results contain the right items but appear in a different order.
  **Cause.** The replacement used a data structure or unstable algorithm that
  does not preserve tie order. **Fix.** Treat order as part of the oracle. Add
  tie fixtures, choose a stable algorithm, or document and version the order
  change.
- **Symptom.** The benchmark improved but p95 latency worsened. **Cause.** The
  new algorithm has startup cost, allocation, cache misses, or cold generic
  paths that the microbenchmark did not model. **Fix.** Benchmark production
  size distributions and measure allocation, not only CPU.
- **Symptom.** Rare inputs now panic or throw a different error. **Cause.** The
  old algorithm tolerated malformed input, nulls, NaN values, or missing keys.
  **Fix.** Add malformed-input fixtures and either normalize before the new
  algorithm or make the stricter error a product decision.
- **Symptom.** Duplicate records reappear after rollout. **Cause.** A nested
  scan encoded equality with several fields, while the replacement map used
  only one key. **Fix.** Extract a named equivalence function and use it in old
  tests, new code, and observability labels.
- **Symptom.** Memory spikes during traffic peaks. **Cause.** The replacement
  builds an index, temp array, or full materialized pipeline where the old loop
  streamed. **Fix.** Add memory budgets to the oracle and consider a streaming
  or chunked algorithm.
- **Symptom.** A shadow comparison reports too many mismatches to triage.
  **Cause.** The rig compares raw objects containing timestamps, random ids,
  non-deterministic map order, or logging side effects. **Fix.** Compare a
  canonical digest of the contract fields.
- **Symptom.** Operators cannot explain a decision made by the new path.
  **Cause.** A readable branch tree was replaced by a model, table, or library
  call without reason codes. **Fix.** Emit phase names, rule ids, or selected
  candidate ids at debug or trace level.
- **Symptom.** Rollback is impossible after data was rewritten. **Cause.** The
  algorithm substitution also changed stored representation without a reversible
  migration. **Fix.** Split calculation substitution from data migration, and
  keep a backfill plan with checksums.
- **Symptom.** A security review blocks release late. **Cause.** The new
  algorithm introduced a parser, regex, native library, or approximate match
  service with a new attack surface. **Fix.** run threat review before the
  substitute path reaches production.
- **Symptom.** The old algorithm never gets removed. **Cause.** Shadow mode was
  added without an exit rule. **Fix.** Set mismatch thresholds, owner, deletion
  date, and rollback window before shipping dual execution.

## 12. Trade-off matrix

| Force | Substitute Algorithm | Extract Function | Replace Loop with Pipeline | Strategy |
|---|---|---|---|---|
| Primary move | Replace the method for reaching an answer | Name pieces of the same method | Express collection flow as stages | Make algorithms interchangeable at runtime |
| Latency | Can improve or regress, must be measured | Usually neutral | Mixed, lazy or eager API decides | Dispatch overhead is small, selected strategy cost dominates |
| Coupling | Can reduce coupling to local state, or add library coupling | Reduces local coupling inside a function | Couples code to collection API vocabulary | Couples clients to a strategy interface |
| Consistency | Depends on oracle quality | Preserves behavior by smaller moves | Improves standard stage meaning | Improves family consistency when all strategies share tests |
| Operability | Needs counters for old, new, mismatch, phase cost | Easier breakpoints and logs | Needs per-stage names for long chains | Needs strategy name in traces |
| Cost of change | Medium to high during swap | Low | Low to medium | Medium, because interface design matters |
| Team topology | Works well behind owned API | Works inside one team | Works when team shares operator idioms | Works when several teams own variants |
| Cognitive load | Lower if replacement is known, higher if clever | Lower | Lower for dataflow readers | Lower for variation, higher for dispatch tracing |
| Best fit | Wrong algorithm behind a stable contract | Long method with mixed ideas | Loop that is really a data transform | Multiple algorithms must remain live |
| Main risk | Silent behavior drift | Too many tiny functions | Hidden allocation or side effects | Premature variation axis |

## 13. Related and incompatible patterns

**Extract Function** often comes first. It isolates the old algorithm behind a
name so tests and a replacement can target it. If the old code is mixed into a
large workflow, skipping Extract Function makes comparison harder.

**Replace Loop with Pipeline** is a specialized form of algorithm substitution
when the old algorithm is an imperative collection loop and the new algorithm
is a sequence of collection operators. It should be used when the pipeline
stages make the dataflow clearer.

**Split Phase** helps when the old algorithm mixes preparation, calculation,
and formatting. Substitute the calculation only after inputs have a clean
intermediate representation.

**Separate Query from Modifier** is often required before high-confidence
substitution. A pure query can be run twice for comparison. A command with
effects cannot be shadowed safely without extra isolation.

**Replace Conditional with Polymorphism** can replace a branch-heavy algorithm
when each case belongs to a type. Substitute Algorithm can replace the whole
branch tree with a table or known algorithm when types would add ceremony.

**Strategy** is related but different. Strategy keeps several algorithms alive
and chooses among them at runtime. Substitute Algorithm normally deletes the
old one. If both algorithms must remain supported modes, the work may end in
Strategy rather than substitution.

**Template Method** can conflict with this refactoring when the old algorithm
is spread across subclass hooks. A local swap may be impossible until the hook
contract is tightened or replaced.

**Speculative rewrite** is incompatible. That is not a catalog pattern, but it
is a common failure: rewriting an algorithm because a new idea sounds cleaner
without evidence that the old behavior is captured.

## 14. Refactoring path in and out

Refactoring in.

1. Name the stable entry point. Write down the input domain, output contract,
   ordering rule, error behavior, mutation behavior, and cost concern.
2. Capture examples from current tests, bug reports, logs, and production
   traces. Include boring cases, boundary cases, malformed cases, duplicate
   cases, and large cases.
3. Extract the old algorithm if it is mixed into a larger function. Use Extract
   Function and keep the entry point unchanged.
4. Remove side effects from the extracted algorithm where possible. Use
   Separate Query from Modifier if the routine both computes and mutates.
5. Add an oracle. For exact substitution, compare old and new outputs. For
   intentional revision, encode the new contract and record why it differs.
6. Implement the replacement beside the old algorithm. Keep it small enough
   that review can focus on the algorithm, not surrounding motion.
7. Run differential tests. If the input domain is broad, add property tests that
   check invariants such as sortedness, id preservation, conservation of input
   records, idempotence, or monotonicity.
8. Benchmark representative data. Include size distribution, skew, duplicates,
   sorted or reverse-sorted inputs, malformed values, and cold starts.
9. If risk is high, run production shadow comparison with sampled inputs and a
   canonical result digest.
10. Replace the body behind the stable entry point. Keep rollback possible for
   the agreed window.
11. Delete the old algorithm, rig, feature flag, dead metrics, and comments
   once the rollout proves the new path.

Refactoring out.

1. If the replacement no longer earns its place, write down the force that
   changed: smaller data, new product contract, too much memory, poor
   explainability, or a better platform primitive.
2. Add tests that preserve the current desired contract, not the old
   replacement's accidents.
3. Substitute back to a simpler algorithm or to a Strategy if multiple modes
   are now real.
4. Remove stale benchmarks and dashboards that refer to the retired algorithm.

Cross references in this family: Extract Function prepares the boundary,
Replace Loop with Pipeline is a frequent destination, Split Phase separates
preparation from calculation, and Separate Query from Modifier makes safe
shadow comparison possible.

## 15. Testing and verification

Judgement. Testing is the center of this refactoring because the compiler
cannot prove that two algorithms mean the same thing for a business domain.

Use **golden tests** for known inputs and outputs. They should include the
cases that humans care about: empty input, one item, duplicates, equal scores,
missing fields, maximum values, minimum values, invalid values, existing bug
reports, and records copied from production after privacy review.

Use **differential tests** while both algorithms exist. Generate or load an
input, run old and new, compare only the contract fields, and report a small
counterexample when they differ. This is the fastest way to learn which old
behaviors were accidental and which were relied upon.

Use **property tests** for broad invariants. For a sort, check sortedness,
permutation preservation, stability if promised, and behavior with equal keys.
For a matcher, check that every returned candidate meets the predicate and that
stronger filters return subsets. For a merge, check id conservation and
conflict rules. Property tests do not replace examples because they often miss
domain-specific exceptions.

Use **metamorphic tests** when exact expected output is hard to write. For
example, adding an unrelated candidate should not change the selected winner,
duplicating an ignored record should not change a sum, and shuffling input
should not change output unless order is part of the contract.

Use **performance tests** against representative data. Record both the shape of
the data and the machine profile. Random inputs alone are a poor basis for
algorithm choice. The CPython list sort notes compare behavior across several
input shapes, including random, ascending, descending, duplicates, and
structured cases (https://github.com/python/cpython/blob/main/Objects/listsort.txt,
verified 2026-08-02).

Use **panic and exception tests** for language-specific contracts. Rust's slice
documentation describes behavior when comparison functions do not implement the
needed order, including panic and unspecified result order in such cases
(https://doc.rust-lang.org/std/primitive.slice.html, verified 2026-08-02).
JavaScript comparator behavior also depends on comparator well-formedness; MDN
documents that non-well-formed compare functions can produce different results
across engines
(https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/sort,
verified 2026-08-02). Those contracts belong in tests if the substituted code
accepts caller-supplied comparison functions.

Test doubles are useful only at the boundary. A fake clock, fake repository, or
fixture loader can feed inputs. The algorithm itself should usually be tested
as a pure function. Mocking inside the replacement algorithm tends to hide the
invariants that matter.

## 16. Observability signals

Judgement. Observability should prove that the replacement behaves acceptably
on real data and that rollback remains possible during the migration window.

Log or trace the **algorithm name and version** when the path is material to an
incident. Use a small label such as `candidate_ranker=v2` or
`dedupe_algorithm=indexed_v1`. Avoid logging full inputs when they carry user
data.

Measure **input shape**, not only input size. Useful labels include count,
duplicate ratio, sortedness estimate, number of distinct keys, number of
missing fields, maximum group size, and whether the request used a generic or
fast path. Keep labels bounded. High-cardinality raw ids belong in sampled
debug traces, not metric labels.

Measure **phase cost**. For many replacements, the work splits into normalize,
index, search, merge, and format. A single total duration hides the phase that
regressed. Record allocation or memory high-water marks when the new algorithm
builds indexes or temp arrays.

During shadow mode, emit **comparison counters**: old success, new success,
both failed same way, mismatch by reason, skipped comparison, timeout, and
sample rate. Store a privacy-safe digest for mismatches so engineers can group
them without exposing raw records.

Healthy signals look like this: mismatch count is zero or fully explained,
latency stays within budget at p50, p95, and p99, memory does not exceed the
rollout limit, fallback rate trends to zero, and the new algorithm's input
shape matches the benchmark corpus.

Failing signals look like this: mismatches cluster around equal keys, null
values, duplicate ids, large groups, or cold starts; allocation grows faster
than input size; rollback is used but old and new metrics are mixed under the
same label; or the old path remains active long after the decision date.

## 17. Security and privacy implications

Judgement. Substitute Algorithm is not a security pattern, but it can change
security posture when the algorithm parses, ranks, filters, hashes, compares,
or calls external code.

The refactoring can close attack surface when it replaces custom parsing,
escaping, comparison, or cryptographic-looking code with a reviewed platform
primitive. It can open attack surface when it adds a new dependency, native
extension, regex, model, service call, approximate lookup, or cache. A
replacement algorithm that is faster for normal input may still be worse under
adversarial input if it has poor worst-case behavior.

Privacy risk appears in the verification rig. Differential testing and
shadow comparison tempt teams to record full inputs and full outputs. For user
data, compare canonical digests, counts, reason codes, and redacted examples.
If raw production cases are needed, move them through the same approval and
retention process used for any other production data.

Authorization risk appears when the old algorithm accidentally filtered
records that the new algorithm returns. Treat security filters as contract
fields. Do not compare only display fields if hidden authorization fields decide
whether a record may be returned.

Integrity risk appears when substituting ranking, deduplication, fraud, abuse,
or eligibility algorithms. Small tie-break changes can shift money, access,
quota, or moderation outcomes. The rollout should include audit logs that
explain which rule selected the result.

Where the pattern is silent: it does not itself provide encryption,
authentication, authorization, input validation, or secret handling. Those
properties come from the algorithm selected and from the boundary around it.

## Code examples

The examples are intentionally small and original. They model the same move in
three languages: replace a manual priority search with a clearer data-driven
algorithm behind one stable function.

```typescript
type Person = {
  name: string;
  active: boolean;
};

const priority = new Map<string, number>([
  ["Don", 0],
  ["John", 1],
  ["Kent", 2],
]);

export function foundPerson(people: Person[]): string {
  let bestName = "";
  let bestRank = Number.POSITIVE_INFINITY;

  for (const person of people) {
    const rank = priority.get(person.name);
    if (person.active && rank !== undefined && rank < bestRank) {
      bestName = person.name;
      bestRank = rank;
    }
  }

  return bestName;
}

console.log(foundPerson([
  { name: "Ada", active: true },
  { name: "Kent", active: true },
  { name: "Don", active: false },
  { name: "John", active: true },
]));
```

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Person:
    name: str
    active: bool


PRIORITY = {"Don": 0, "John": 1, "Kent": 2}


def found_person(people: list[Person]) -> str:
    eligible = (
        (PRIORITY[p.name], p.name)
        for p in people
        if p.active and p.name in PRIORITY
    )
    return min(eligible, default=(99, ""))[1]


if __name__ == "__main__":
    group = [
        Person("Ada", True),
        Person("Kent", True),
        Person("Don", False),
        Person("John", True),
    ]
    print(found_person(group))
```

```go
package main

import "fmt"

type Person struct {
	Name   string
	Active bool
}

var priority = map[string]int{
	"Don":  0,
	"John": 1,
	"Kent": 2,
}

func foundPerson(people []Person) string {
	bestName := ""
	bestRank := len(priority) + 1

	for _, person := range people {
		rank, ok := priority[person.Name]
		if person.Active && ok && rank < bestRank {
			bestName = person.Name
			bestRank = rank
		}
	}

	return bestName
}

func main() {
	people := []Person{
		{Name: "Ada", Active: true},
		{Name: "Kent", Active: true},
		{Name: "Don", Active: false},
		{Name: "John", Active: true},
	}
	fmt.Println(foundPerson(people))
}
```

The old algorithm in each case would be a sequence of repeated checks in
priority order. The substitute algorithm names priority as data and performs
one pass. The stable contract is "return the highest-priority active candidate,
or the empty string." That contract is easier to test than the original branch
sequence.

## 18. References

- Martin Fowler. *Refactoring. Improving the Design of Existing Code*. First
  edition. Addison-Wesley, 1999. Chapter 6, "Composing Methods", catalog entry
  "Substitute Algorithm."
- Martin Fowler, with Kent Beck. *Refactoring. Improving the Design of
  Existing Code*. Second edition. Addison-Wesley, 2018. Chapter 6, "A First Set
  of Refactorings", catalog entry "Substitute Algorithm."
- Martin Fowler. "Substitute Algorithm." Refactoring catalog.
  https://refactoring.com/catalog/substituteAlgorithm.html, verified
  2026-08-02.
- Martin Fowler. "Refactoring." Book page.
  https://martinfowler.com/books/refactoring.html, verified 2026-08-02.
- Martin Fowler. "Changes for the 2nd Edition of Refactoring."
  https://martinfowler.com/articles/refactoring-2nd-changes.html, verified
  2026-08-02.
- Tim Peters and CPython contributors. "listsort.txt." CPython repository.
  https://github.com/python/cpython/blob/main/Objects/listsort.txt, verified
  2026-08-02.
- Simon Zund. "Getting things sorted in V8." V8 blog.
  https://v8.dev/blog/array-sort, verified 2026-08-02.
- Mathias Bynens. "Stable Array.prototype.sort." V8.
  https://v8.dev/features/stable-sort, verified 2026-08-02.
- MDN Web Docs contributors. "Array.prototype.sort()."
  https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/sort,
  verified 2026-08-02.
- Rust project contributors. "RELEASES.md." Rust 1.81 release notes mirror.
  https://chromium.googlesource.com/external/github.com/rust-lang/rust/%2Bshow/f21fbac535ab2c3bc50db20547f4d48477357103/RELEASES.md,
  verified 2026-08-02.
- Rust project contributors. "Primitive slice documentation."
  https://doc.rust-lang.org/std/primitive.slice.html, verified 2026-08-02.
- Donald E. Knuth. *The Art of Computer Programming, Volume 3. Sorting and
  Searching*. Second edition. Addison-Wesley, 1998. Chapter 5, "Sorting."
- Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, and Clifford Stein.
  *Introduction to Algorithms*. Third edition. MIT Press, 2009. Chapters 2, 6,
  7, 8, and 15.
