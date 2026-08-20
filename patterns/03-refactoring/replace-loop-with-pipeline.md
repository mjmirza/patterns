---
name: Replace Loop with Pipeline
slug: replace-loop-with-pipeline
family: 03-refactoring
category: Refactoring
aliases: [Loop to Pipeline, Collection Pipeline Refactoring]
first_described: "Fowler 2018"
maturity: established
related: [extract-function, extract-variable, split-loop, combine-functions-into-transform, replace-inline-code-with-function-call]
incompatible_with: []
verified: 2026-08-02
---

# Replace Loop with Pipeline

## 1. Name, aliases, and lineage

The canonical name is Replace Loop with Pipeline. Martin Fowler's online
catalog records the refactoring under that name and shows the core move from a
manual loop with filtering and accumulation to a chain of collection operations
(https://refactoring.com/catalog/replaceLoopWithPipeline.html, verified
2026-08-02). Fowler and Kent Beck also list Loops as a code smell in
*Refactoring. Improving the Design of Existing Code*, second edition,
Addison-Wesley, 2018, chapter 3, "Bad Smells in Code"; the InformIT excerpt for
that chapter points readers to Replace Loop with Pipeline at page 231
(https://www.informit.com/articles/article.aspx?p=2952392&seqNum=13, verified
2026-08-02). The book citation for the catalog entry is Martin Fowler, with
Kent Beck, *Refactoring. Improving the Design of Existing Code*, second
edition, Addison-Wesley, 2018, chapter 6, catalog entry "Replace Loop with
Pipeline."

The broader pattern name is Collection Pipeline. Fowler published a separate
article in 2015 that describes collection pipelines as a style for processing a
collection through operations such as filter, map, and related transforms
(https://martinfowler.com/articles/collection-pipeline/, verified 2026-08-02).
He also published "Refactoring with Loops and Collection Pipelines" in 2015,
where he walks loops into pipeline form through small steps
(https://martinfowler.com/articles/refactoring-pipelines.html, verified
2026-08-02). Those articles predate the second edition catalog entry and give
the refactoring its practical background, but the named catalog refactoring in
this repository is the 2018 Fowler entry.

Several communities use different names for the same target shape. Java calls
the library abstraction a Stream and documents stream operations as supporting
sequential and parallel aggregate operations
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/package-summary.html,
verified 2026-08-02). Python programmers often speak of iterator pipelines
when they combine generator expressions and the `itertools` module, whose
standard library documentation describes iterator building blocks for efficient
looping (https://docs.python.org/3/library/itertools.html, verified
2026-08-02). Data engineers may call the same shape a transformation pipeline,
as Apache Spark describes transformations such as `map`, `filter`, and
`flatMap` on RDDs (https://spark.apache.org/docs/latest/rdd-programming-guide,
verified 2026-08-02).

Engineering judgement. Treat the names as local dialects around one idea. The
refactoring is not anti-loop dogma. It is a disciplined move that replaces a
loop whose body is really a sequence of collection operations with a pipeline
whose stages name those operations.

## 2. Problem and context

The problem begins with a loop that has stopped being a small control-flow
device and has become an unnamed data transformation. It reads a collection,
skips some elements, projects fields, expands nested collections, computes
intermediate values, maybe groups or sorts, then appends selected results into
an output collection. The loop still works, but the intent is buried inside
index management, accumulator mutation, conditional nesting, and temporary
variables.

The reader has to simulate the loop to answer basic questions. Which elements
survive? Which fields are used? Is order preserved? Does the loop emit zero,
one, or many results per input element? Is the accumulator reset for every call?
Can a later statement observe a half-built result? Those are not exotic
questions. They are the normal questions a maintainer asks before changing a
data transformation.

Replace Loop with Pipeline changes the representation. Instead of one block
that interleaves traversal, selection, projection, flattening, grouping, and
collection, the code becomes a chain of named stages. Each stage receives a
sequence and returns another sequence or a final value. A filter names the
selection rule. A map names the projection. A flat map names one-to-many
expansion. A reduce, fold, sum, count, grouping, or collector names the final
aggregation.

The context that makes the refactoring pay is ordinary application code that is
processing in-memory collections or a library abstraction that behaves like a
collection. The source might be a list of orders, parsed records, log entries,
AST nodes, database rows already materialized by a query, or domain events
inside a test fixture. The output is often a list, set, dictionary, scalar
count, grouped index, or stream of transformed records.

This refactoring is strongest when the loop body is mostly declarative data
work. It is weaker when the loop coordinates effects, owns transaction
boundaries, breaks early for latency reasons, mutates several outside variables,
or relies on a specific step-by-step schedule. In those cases the loop may be
the clearest expression of control flow. A pipeline is a better name for a
transformation, not a better name for every repeated action.

The key smell is not the word `for`. The smell is that the loop body answers a
pipeline question in a control-flow accent. "Take paid orders, read their
customer ids, remove missing ids, and return the unique ids" is a pipeline
question. "Read messages until the socket blocks, commit offsets after each
successful write, and stop at the first poison record" is a control-flow
question. The first wants stages. The second wants a loop or a more explicit
workflow.

## 3. Forces

Engineering judgement. This dimension weighs design pressure. It is not a
sourced claim about one named runtime.

- **Clarity.** Favoured when the loop already performs known collection
  operations. Named stages let a reader scan selection, projection, expansion,
  grouping, and termination without tracing accumulator mutation.
- **Local control.** Sacrificed. A loop exposes every step. A pipeline gives
  control to the collection library, iterator protocol, stream engine, or query
  optimizer.
- **Coupling.** Favoured when clients depend on a stable transformation shape
  rather than on a mutable result list. Harmed when lambdas close over many
  variables and hide dependencies inside anonymous code.
- **Latency.** Mixed. Lazy pipelines can avoid intermediate collections and can
  stop early when a terminal operation permits it. Eager pipelines may allocate
  a new collection at each stage and cost more than the loop they replaced.
- **Consistency.** Favoured when standard operators encode common behavior.
  Filtering, mapping, flattening, and grouping have conventional meanings. A
  hand-written loop can mix those meanings in one branch.
- **Operability.** Sacrificed unless stage names and metrics are added. A loop
  gives one obvious breakpoint. A pipeline may require naming intermediate
  stages, tracing input and output counts, or adding debug hooks.
- **Cost.** Usually neutral for small collections. It can improve cost when a
  runtime fuses stages or pushes work to a query engine, and it can worsen cost
  when each stage materializes.
- **Team topology.** Favoured when teams share a pipeline vocabulary. Harmed
  when half the team thinks in imperative loops and the other half writes dense
  chains with opaque lambdas.
- **Cognitive load.** Favoured for readers who know the operators. Sacrificed
  when the language has many near-duplicate operators, such as `map`, `flatMap`,
  `compactMap`, `filterMap`, `collect`, `reduce`, `fold`, and `scan`.

The refactoring favours naming the dataflow. It sacrifices manual control over
the traversal. The trade is good when the loop is accidental machinery and bad
when the loop is the domain behavior.

## 4. Applicability and non-applicability

Reach for Replace Loop with Pipeline when these conditions hold.

- The loop reads from one primary collection and writes to one result.
- The loop body is a recognizable sequence of selection, projection, expansion,
  grouping, ordering, distinctness, limiting, or aggregation.
- The accumulator is updated in one way, such as append, insert into a set,
  increment, sum, min, max, group, or concatenate.
- The order of operations can be stated as a dataflow sentence.
- Intermediate names would make the transformation easier to test or review.
- A standard library or project utility already provides the needed operators.
- The loop has no meaningful externally visible effect other than its returned
  result.
- A data engine can use the pipeline shape for lazy execution, fusion, pushdown,
  partitioning, or parallel execution.

Do not apply it in these cases.

- **The loop is mainly side effects.** Symptom before refactoring. The body
  writes files, sends messages, updates database rows, emits metrics, or calls
  remote services. Reason. A pipeline can hide execution order and retry
  behavior. Keep explicit control flow or extract effectful steps into named
  commands.
- **The loop relies on early exit for latency.** Reason. Some pipeline APIs have
  short-circuiting operations such as `any`, `find`, `take`, or `limit`, while
  others force full traversal. Use a pipeline only when the chosen API preserves
  the early exit.
- **The loop mutates several accumulators at once.** Reason. A single pipeline
  target may produce a tuple nobody wants to read. Use Split Loop first, or
  introduce a collector type with a named contract.
- **The loop body is a state machine.** Reason. Pipelines are poor at showing
  mode changes, retries, backoff, transaction phases, or protocol transitions.
  Use State, Strategy, or explicit workflow code.
- **The operation depends on element index in non-local ways.** Reason. Some
  languages support indexed operations, but a loop may be clearer for windows,
  lookbehind, lookahead, and adjacency logic. Use a sliding-window helper only
  when it has a local name the team already knows.
- **The collection is tiny and the loop is clearer.** Reason. A three-line loop
  with one append may be lower cost for the reader than a chain with unfamiliar
  operators.
- **The pipeline API is eager and allocates at every stage.** Reason. Replacing
  one loop with five temporary arrays can harm memory and cache behavior. Use a
  lazy iterator, generator, transducer, fused helper, or keep the loop.
- **The team lacks a shared operator vocabulary.** Reason. A refactoring that
  makes one author feel fluent and five maintainers slower has not improved the
  codebase yet. Pair the change with local examples and tests.
- **The loop enforces a security or audit sequence.** Reason. Reviewers may need
  to see validation, authorization, mutation, and logging in a fixed order.
  Extract functions, but do not hide the order in a chain.
- **The pipeline would require broad exception gymnastics.** Reason. Languages
  with checked exceptions or APIs that do not allow throwing lambdas can make an
  honest loop clearer than wrappers around every stage.

## 5. Structure

The participants are roles in the transformation.

- **Source collection.** The iterable, stream, sequence, generator, RDD,
  DataFrame, slice, array, list, set, or cursor-like value that supplies input
  elements. The source may be eager, lazy, finite, or unbounded.
- **Stage.** A single operation in the chain. Common stages include filter,
  map, flat map, distinct, sort, take, drop, group, chunk, window, and scan.
  Each stage should have one reason to exist.
- **Predicate.** A boolean function used by a filter-like stage. It decides
  whether an element continues.
- **Mapper.** A function that projects one input element to one output element.
  A mapper should not mutate outside state.
- **Expander.** A function that projects one input element to zero or more
  output elements, later flattened into the pipeline.
- **Aggregator.** A terminal operation that collapses the stream into a scalar,
  collection, grouping, index, or summary.
- **Result.** The final value returned by the enclosing function. It may be a
  materialized collection or a lazy sequence passed onward.
- **Boundary adapter.** Optional code that turns an external cursor, database
  result, callback API, or event source into a pipeline source and closes it at
  the right time.

The relationship is linear at the source level and nested at the call level.
The output of one stage is the input of the next. In lazy implementations, the
chain is often built first and pulled later by a terminal operation. In eager
implementations, each stage may run immediately and return a full collection.

The old loop usually has these hidden roles in one block: iteration, predicate,
mapper, accumulator, and result. The refactoring exposes them. The important
design choice is where to stop exposing. A five-stage pipeline with clear
operators is often easier than five named functions. A fifteen-stage pipeline
usually needs named sub-pipelines, extracted functions, or a domain-specific
transform object.

## 6. ASCII structure diagram

```
Before

  +----------------------+        mutates        +----------------+
  | Loop over source     | --------------------> | result list    |
  |----------------------|                       +----------------+
  | index or iterator    |
  | if predicate         |
  | temp = projection    |
  | maybe expand         |
  | result.add(temp)     |
  +----------------------+

After

  +----------+    +----------+    +--------+    +-----------+
  | Source   | -> | filter   | -> | map    | -> | aggregate |
  +----------+    +----------+    +--------+    +-----------+
       |               |              |              |
       |               |              |              v
       |               |              |        +-----------+
       |               |              +------> | Result    |
       |               +---------------------> +-----------+
       +-------------------------------------->

  Each box names one transformation role. The result is returned rather than
  grown by scattered mutation inside the loop body.
```

## 7. Dynamics

At runtime, a pipeline has two phases in many libraries. First the chain is
assembled. Then a terminal operation pulls or drives data through it. Java's
Stream package describes streams as supporting sequential and parallel
aggregate operations and distinguishes intermediate operations from terminal
operations
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/package-summary.html,
verified 2026-08-02). Spark documents transformations as lazy and says they
are computed when an action requires a result
(https://spark.apache.org/docs/latest/rdd-programming-guide, verified
2026-08-02). Those are named runtimes, not universal rules. Python list
comprehensions are eager, Python generator expressions are lazy, and many
JavaScript array methods are eager.

```
Caller        Pipeline builder       Lazy stage chain        Terminal result
  |                  |                       |                       |
  |-- call fn() ---->|                       |                       |
  |                  |-- source ------------>|                       |
  |                  |-- add filter -------->|                       |
  |                  |-- add map ----------->|                       |
  |                  |-- add distinct ------>|                       |
  |                  |                       |                       |
  |                  |-- collect() --------->|                       |
  |                  |                       |-- pull item 1 --------|
  |                  |                       |-- predicate true -----|
  |                  |                       |-- map item ---------->|
  |                  |                       |-- add to result ------|
  |                  |                       |-- pull item 2 --------|
  |                  |                       |-- predicate false ----|
  |                  |                       |-- skip -------------->|
  |                  |<----------------------|                       |
  |<-- result -------|                       |                       |
```

Two dynamics matter during the refactoring. The first is evaluation timing. A
loop executes where it appears. A lazy pipeline may execute later, when someone
collects it, iterates it, or calls a terminal action. That can move exceptions,
logging, database cursor use, and resource closure to another source line. The
second is element order. Some pipeline APIs preserve encounter order by
default, some do not, and parallel variants can alter timing even when the
final order is stable. The Java Stream documentation defines streams in terms
of a source and operations and includes sequential and parallel execution modes
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/package-summary.html,
verified 2026-08-02). Treat order and parallelism as part of the API contract
you are using, not as a property of the refactoring name.

Engineering judgement. During review, ask for a sentence that describes the
pipeline flow. If the author cannot say "filter to active orders, map to invoice
ids, remove duplicates, sort by id" without mentioning indexes or mutation, the
loop may not have been understood enough to refactor.

## 8. Implementation variants

**Eager collection pipeline.** JavaScript arrays, many Python list
comprehensions, and ordinary array helpers often build a new collection per
stage. This version is easy to inspect and debug. It is a poor fit for large
inputs unless the runtime fuses operations or the number of stages is small.

**Lazy iterator pipeline.** Python generators, Rust iterators, Java streams, and
Swift lazy sequences can delay work until the consumer asks for the next
element. This reduces intermediate allocation and can support short-circuiting.
The cost is shifted timing. Exceptions and effects occur during consumption,
not during pipeline construction.

**Terminal collector.** Some APIs separate intermediate stages from a final
collector. Java Stream uses terminal operations such as collect, count, any
match, and reduce in its package API
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/package-summary.html,
verified 2026-08-02). The collector boundary is a good place to make the return
type explicit.

**Generator expression or comprehension.** Python and similar languages can
replace a simple filter-map loop with a comprehension. Prefer this when the
pipeline is short and returns a list, set, or dictionary. Prefer named iterator
stages when the chain gets longer or must stay lazy.

**Function pipeline with `pipe`.** pandas documents `Series.pipe()` and
`DataFrame.pipe()` as applying chainable functions that receive the whole data
object, and says `.pipe` helps method chaining for functions that expect
Series, DataFrames, or GroupBy objects
(https://pandas.pydata.org/docs/user_guide/user_defined_functions.html,
verified 2026-08-02). This is a table-shaped version of the same idea: each
stage transforms the whole frame.

**Distributed data pipeline.** Spark RDDs and Datasets expose transformations
such as map, filter, and flatMap, with actions that trigger computation
(https://spark.apache.org/docs/latest/rdd-programming-guide, verified
2026-08-02; https://spark.apache.org/docs/latest/sql-programming-guide,
verified 2026-08-02). The local refactoring shape matters here because the
engine can reason about the graph.

**Transducer or fused transform.** Some ecosystems compose transformations
without creating intermediate collections and without binding them to a
particular source type. This variant is strong for library authors and high
volume data paths. It is harder for teams that have not adopted the abstraction
in ordinary code.

**Named stage functions.** When a lambda grows past one expression or carries
domain language, extract it. `isBillable`, `toInvoiceLine`, and
`hasPublicEmail` give the pipeline names that a reviewer can test. This variant
often matters more than the choice between eager and lazy evaluation.

**Parallel pipeline.** Some APIs can distribute independent element work. Use
only when the operation is stateless, order requirements are clear, combining
cost is measured, and the runtime's parallel contract is understood. A loop
with hidden shared mutation is a bad input to a parallel pipeline.

## 9. Known production uses

**Java Platform, Stream API.** The Java SE 21 API documents `java.util.stream`
as classes supporting functional-style operations on streams of elements, such
as map-reduce transformations over collections
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/package-summary.html,
verified 2026-08-02). This is a production platform use of the target shape:
Java programs can replace loops over collections with stream stages and
terminal operations.

**Apache Spark, RDD and Dataset APIs.** Spark's RDD programming guide documents
transformations such as `map`, `filter`, `flatMap`, and actions such as
`reduce`; it also states that transformations are lazy and are computed when an
action needs a result (https://spark.apache.org/docs/latest/rdd-programming-guide,
verified 2026-08-02). Spark SQL documentation describes Datasets and
DataFrames and says Datasets can be manipulated using functional
transformations including `map`, `flatMap`, and `filter`
(https://spark.apache.org/docs/latest/sql-programming-guide, verified
2026-08-02). This is a production data platform where pipeline shape is the
normal programming interface.

**pandas, DataFrame and Series pipe.** pandas documentation describes
`Series.pipe()` and `DataFrame.pipe()` for chainable functions over Series or
DataFrames, and shows `.pipe` as an alternative to nested function calls
(https://pandas.pydata.org/docs/user_guide/user_defined_functions.html,
verified 2026-08-02). This is a production library use for table-oriented
pipelines rather than element-wise loops.

**Python standard library, itertools.** Python's standard library documents
`itertools` as iterator building blocks for efficient looping
(https://docs.python.org/3/library/itertools.html, verified 2026-08-02). It is
not a full pipeline framework, but it supplies production-grade primitives such
as chain, islice, takewhile, dropwhile, groupby, and accumulate that often form
the target of this refactoring in Python code.

## 10. Consequences

Positive.

- The transformation's shape becomes visible. Readers see filters, maps,
  flattening, grouping, sorting, and terminal aggregation as named stages.
- Mutation moves inward. The caller receives a value instead of watching a
  result collection grow through scattered statements.
- Tests can target stage functions separately when predicates and mappers are
  named.
- Lazy APIs can avoid intermediate collections and can short-circuit through
  terminal operations.
- Some runtimes can optimize a pipeline graph in ways a hand-written loop hides,
  such as Spark's lazy transformation plan.
- The refactoring can expose duplicated loops. Once two loops become similar
  pipelines, common predicates and mappers become easier to see.
- Code review gets a better vocabulary. A reviewer can ask whether the filter
  belongs before the map or whether a flat map should preserve empty results.

Negative.

- Dense chains can become their own form of unreadable code. A pipeline with
  many anonymous lambdas is a loop smell in another syntax.
- Debugging may be less direct. Breakpoints inside chained lambdas and lazy
  iterators can be awkward in some tools.
- Evaluation can move later. Lazy pipelines can delay exceptions, metrics, and
  resource access until the result is consumed.
- Eager pipelines can allocate more than the loop, especially when each stage
  returns a collection.
- Side effects hidden inside stages make ordering harder to reason about.
- Changing from loop to pipeline can alter order, duplicate handling, null
  handling, exception timing, and numeric behavior if each detail is not tested.
- Some language APIs use names that do not match the team's mental model.
  `collect`, `select`, `where`, `compactMap`, and `flatMap` vary by ecosystem.

## 11. Failure modes and misuse

Engineering judgement. The failures below are drawn from common review and
operations patterns. Named API claims are cited elsewhere; the symptom, cause,
and fix triads are practical guidance.

**Hidden side effects.** Symptom. Reordering two pipeline stages changes which
emails are sent, which audit rows appear, or how many external calls are made.
Cause. A mapper or predicate mutates state or calls an effectful service. Fix.
Move effects outside the pipeline, or name the stage as a command and keep the
ordering explicit.

**Eager allocation spike.** Symptom. A request that used to allocate one result
list now allocates several large temporary arrays and raises garbage collection
time. Cause. The chosen API materializes at each stage. Fix. Use a lazy iterator
variant, combine adjacent stages, use a fused helper, or keep the loop in the
hot path.

**Delayed exception.** Symptom. A function returns a pipeline successfully, but
the caller sees an exception later while iterating it. Cause. A lazy pipeline
was returned instead of a materialized result. Fix. Return a materialized value,
document lazy behavior in the function name and type, or move validation before
return.

**Lost early exit.** Symptom. A search that used to stop after the first match
now scans the whole input and misses latency targets. Cause. The pipeline ends
with a full collection operation instead of a short-circuiting terminal. Fix.
Use `find`, `any`, `first`, `take`, or the local equivalent, or keep the loop
when the API has no short-circuit operation.

**Accumulator smuggled into a closure.** Symptom. A pipeline has `push`,
`append`, `set`, or `+=` inside a lambda and returns an outside variable.
Cause. The loop syntax changed, but the mutable accumulator stayed. Fix.
Replace the mutation with a terminal collector, fold, group, or extracted
collector object.

**Parallel race.** Symptom. A parallel stream or distributed transform produces
non-deterministic counts, duplicate rows, or corrupted output. Cause. Stage
functions share mutable state or depend on execution order. Fix. Make stages
pure, use associative combiners, or run sequentially.

**Operator pileup.** Symptom. A reviewer cannot explain a twelve-stage chain
without stepping through each lambda. Cause. The pipeline lacks domain names.
Fix. Extract sub-pipelines or stage functions with names that say what business
concept they implement.

**Changed null behavior.** Symptom. A migrated loop throws on a missing value or
drops a record the loop preserved. Cause. The refactoring used an operator such
as map, filter, compact map, or flatten without matching the old null policy.
Fix. Add characterization tests for missing values, then choose an operator
whose behavior matches the test.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Replace Loop with Pipeline | Keep Explicit Loop | Extract Function Around Loop | Split Loop | Query Object | Dataflow Engine |
|---|---|---|---|---|---|---|
| Clarity of data transformation | High when stages are named | Medium for short loops, low for mixed loops | Medium. Name helps, internals remain imperative | High when loop has multiple jobs | High for query-like domains | High when graph tooling exists |
| Local control over order | Medium. Depends on API | High | High | High | Medium | Low to medium |
| Allocation cost | Low with lazy or fused API, high with eager stages | Low and predictable | Low and predictable | May traverse more than once | Depends on execution plan | Depends on engine |
| Early exit | Good only with matching terminal operation | Strong | Strong | Strong per loop | Depends on query form | Depends on engine |
| Coupling to collection library | High | Low | Low | Low | Medium | High |
| Testability of predicates and mappers | High when extracted | Medium | Medium | Medium | High | Medium |
| Debugging with breakpoints | Medium | High | High | High | Medium | Low to medium |
| Parallel or distributed execution | Possible in some APIs | Manual work | Manual work | Manual work | Possible | Strong |
| Team readability | High with shared vocabulary | High for imperative teams | High | Medium | Medium | Medium |
| Best fit | Pure collection transform | Control-heavy traversal | Need name but not new shape | One loop has multiple accumulators | Query rules need an object | Large data processing graph |

Reading of the table. Replace Loop with Pipeline wins when the code is already
describing dataflow but does so through mutation. Keep Explicit Loop wins when
the traversal itself is the behavior. Extract Function is the smaller move when
the loop needs a name, not a new internal shape. Split Loop is often the entry
move when one loop updates several results. Query Object is better when the
transformation is a reusable domain query with configuration. A Dataflow Engine
is a platform choice, not a small refactoring, and earns its cost only when
scale, scheduling, or graph optimization matters.

## 13. Related and incompatible patterns

- **Extract Function.** Often comes first. Fowler's 2015 loop refactoring
  article says he often considers extracting the loop before manipulating it
  (https://martinfowler.com/articles/refactoring-pipelines.html, verified
  2026-08-02). A named function creates a testable boundary before the loop body
  changes.
- **Extract Variable.** A useful stepping stone. Fowler's article shows the
  initial loop collection being extracted before stages are introduced
  (https://martinfowler.com/articles/refactoring-pipelines.html, verified
  2026-08-02). The temporary name gives the first stage a place to attach.
- **Split Loop.** A frequent precursor. If a loop builds two results, split it
  into one loop per result before attempting a pipeline. The extra traversal is
  usually worth the clarity unless measurement says otherwise.
- **Combine Functions into Transform.** Composes with this refactoring when the
  pipeline enriches a record through several derived values. The transform can
  hold named stages rather than scattering derived fields across a loop.
- **Replace Inline Code with Function Call.** A mature pipeline often ends with
  predicates and mappers that call named helpers. That move turns anonymous
  lambdas into domain language.
- **Iterator.** The structural partner. Iterator supplies the uniform traversal
  protocol that makes pipelines possible across sources.
- **Strategy.** Composes when a stage varies by policy. A filter predicate or
  mapper can be a Strategy supplied by the caller.
- **Command.** Usually conflicts when stage lambdas become effectful commands.
  If the operation is mostly effects, model it as commands or workflow steps
  rather than as a collection pipeline.
- **Template Method.** Rarely needed. A pipeline gives composition by stages.
  Template Method gives inheritance-based sequencing. Combining them often
  creates two extension mechanisms for one operation.

## 14. Refactoring path in and out

Introducing the refactoring into existing code.

1. Add characterization tests for the loop. Cover empty input, one element,
   several elements, rejected elements, missing values, duplicate values, order,
   and any early exit behavior.
2. Extract the loop into its own function if it is embedded in a larger method.
   This creates a small behavioral boundary.
3. Identify the source collection and name it. If the loop iterates over an
   expression, extract that expression to a variable.
4. Find the first pure selection condition and move it into a filter stage.
   Leave the loop in place for the moment and run tests.
5. Move a pure projection into a map stage. When the loop emits several results
   per input, use flat map or an equivalent helper.
6. Replace accumulator mutation with a terminal operation. Use collect for a
   list, a set collector for uniqueness, group-by for maps of collections,
   count for cardinality, and reduce or fold for scalar summaries.
7. Remove dead loop scaffolding. Delete now-unused temps, flags, and result
   mutation.
8. Extract predicates, mappers, and collectors whose names carry domain meaning.
9. Run performance tests when the input can be large, the path is hot, or the
   chosen API is eager.
10. Review evaluation timing. If the function used to return a materialized
   value, avoid returning a lazy pipeline by accident.

Removing the refactoring when it stops earning its place.

1. Find the reason for removal. Common reasons are hidden effects, allocation,
   debugging pain, weak team fluency, or a chain that grew past readability.
2. Keep named predicates and mappers. They are often still useful inside a loop.
3. Convert the pipeline back one terminal operation at a time. Preserve tests
   after each step.
4. Recreate early exit explicitly when latency is the reason for removal.
5. Replace grouping or folding with a named collector object if the accumulator
   has domain rules.
6. Delete pipeline helpers that no longer carry a concept.

Engineering judgement. The in path and out path should both be small. If a
loop-to-pipeline change requires redesigning persistence, concurrency, and
error handling in the same commit, the loop was not the unit of change.

## 15. Testing and verification

The safest test posture is characterization first, refactor second. The tests
should pin behavior that pipelines often change by accident.

- **Input shape tests.** Empty input, single input, many inputs, missing fields,
  duplicates, unsorted input, and already sorted input.
- **Selection tests.** Elements that pass, elements that fail, boundary values,
  null or optional values, and mixed valid and invalid records.
- **Projection tests.** Field mapping, derived values, type conversion, and
  preservation of values not meant to change.
- **Order tests.** Assert order when order is part of the contract. Avoid
  asserting it when the result is a set or a deliberately unordered summary.
- **Cardinality tests.** A map emits one result per input, a filter emits zero
  or one, and a flat map emits zero or many. Test the exact count.
- **Aggregation tests.** Sums, counts, minimums, maximums, groups, and
  deduplication need examples that catch identity-value and duplicate mistakes.
- **Laziness tests.** If the return type is lazy, test when exceptions occur and
  whether the source resource stays open long enough.
- **Early exit tests.** Use a source that records how many elements were read.
  Confirm `find`, `any`, `take`, or local equivalents stop when they should.
- **Equivalence tests.** For risky changes, keep the old loop as a private
  oracle during the refactoring and compare loop output to pipeline output over
  generated inputs. Delete the oracle before shipping.

What becomes easier. Pure predicates and mappers can be unit tested without
constructing the whole source. Pipeline stages can be tested with small table
fixtures. Property tests work well for laws such as "filtering paid orders never
returns unpaid orders" or "mapping to ids preserves result count after the
filter."

What becomes harder. Debugging staged lazy evaluation can be awkward. Mocking
inside lambdas is usually a smell, because it means the stage has effects.
Testing parallel pipelines requires attention to ordering and shared state.

The code examples in this entry were compiled or run with `node`, `python3`,
and `go` in this workspace. The examples use TypeScript-flavored JavaScript,
Python, and Go because those languages show three common shapes: eager array
chaining, lazy generator pipelines, and an explicit typed pipeline over slices.

## 16. Observability signals

Engineering judgement. Pipelines are easy to hide in source code and hard to
see in production unless they are named. Treat a meaningful pipeline like a
small data product with counts, timings, and error labels.

Useful signals.

- **Input count.** Number of records entering the pipeline.
- **Per-stage output count.** Count after filters, expansions, grouping, and
  deduplication.
- **Drop reason counts.** Named reasons for filtering records out, such as
  `missing_customer_id`, `not_billable`, or `outside_window`.
- **Expansion ratio.** Output rows per input row for flat map stages.
- **Cardinality of groups.** Number of groups and largest group size.
- **Latency by stage.** Wall time for expensive stages, especially parsing,
  remote lookup, sorting, grouping, and serialization.
- **Allocation or memory pressure.** Temporary collection size, peak memory, or
  spill metrics for large pipelines.
- **Terminal operation label.** Whether the pipeline collected, counted,
  reduced, searched, or returned lazily.
- **Exception stage.** Stage name attached to parsing, validation, and mapping
  failures.

A healthy dashboard shows stable ratios. For example, ten thousand inputs,
eight thousand after eligibility filtering, seven thousand nine hundred after
missing-id filtering, seven thousand unique ids, and a narrow latency range. A
failing dashboard shows a sudden drop to zero after one stage, an expansion
ratio that climbs without a product reason, a large gap between input count and
terminal count, or stage latency that grows with data skew.

Do not log every element by default. That leaks data and can make a hot path
slower than the old loop. Log sample records only through approved redaction
paths, and prefer aggregate counts for routine visibility.

## 17. Security and privacy implications

Engineering judgement. Replace Loop with Pipeline is not a security pattern.
It can make data handling clearer, but it does not create authorization,
validation, redaction, or sandboxing by itself.

The security benefit is traceability of dataflow. A pipeline can make it easier
to see that untrusted input is parsed, validated, filtered, normalized, and
redacted before output. A named `redactEmail` stage is easier to review than a
field mutation hidden near the bottom of a loop. Per-stage counts can also show
that invalid records are being rejected rather than carried forward.

The risk is misplaced trust in stage names. A stage called `sanitize` may not
sanitize enough. A `map` lambda can still log secrets, call a network service,
or mutate shared state. Lazy evaluation can move access to a sensitive resource
outside the intended authorization scope. Parallel evaluation can make unsafe
shared caches visible across requests. DataFrame-style pipelines can keep
columns alive longer than expected if a later projection fails to drop them.

Practical controls.

- Keep validation, authorization, and redaction stages named.
- Test that disallowed fields are absent from the final result.
- Avoid logging raw elements inside pipeline stages.
- Do not close over request-scoped secrets in lambdas that may run later.
- Materialize inside the authorized scope when lazy return would cross a trust
  boundary.
- Treat third-party stage functions as plugin code. Use capability checks,
  sandboxing, or a narrow DSL when the author is not trusted.
- For distributed pipelines, confirm where data is serialized, spilled, cached,
  and logged by the runtime.

Where the pattern is silent. It does not decide whether data may be processed,
which tenant owns a row, whether a field is personal data, how long an
intermediate result may live, or whether a transform is legally permitted. Those
rules belong in policy, schema, access control, and retention mechanisms.

## Code examples

TypeScript-flavored JavaScript, run with `node`.

```javascript
const orders = [
  { id: "o1", status: "paid", total: 40, customerId: "c2" },
  { id: "o2", status: "draft", total: 12, customerId: "c1" },
  { id: "o3", status: "paid", total: 75, customerId: null },
  { id: "o4", status: "paid", total: 10, customerId: "c2" },
  { id: "o5", status: "paid", total: 99, customerId: "c3" },
];

function billableCustomerIds(input) {
  return [...new Set(
    input
      .filter((order) => order.status === "paid")
      .filter((order) => order.customerId !== null)
      .filter((order) => order.total >= 25)
      .map((order) => order.customerId)
  )].sort();
}

console.log(billableCustomerIds(orders).join(","));
```

Python, run with `python3`.

```python
from itertools import chain

orders = [
    {"id": "o1", "status": "paid", "lines": [("book", 2), ("pen", 1)]},
    {"id": "o2", "status": "draft", "lines": [("desk", 1)]},
    {"id": "o3", "status": "paid", "lines": [("book", 1)]},
]


def paid_line_skus(input_orders):
    paid_orders = (order for order in input_orders if order["status"] == "paid")
    line_items = chain.from_iterable(order["lines"] for order in paid_orders)
    return sorted({sku for sku, quantity in line_items if quantity > 0})


print(",".join(paid_line_skus(orders)))
```

Go, compiled and run with `go run`.

```go
package main

import (
	"fmt"
	"sort"
	"strings"
)

type Order struct {
	ID         string
	Status     string
	Total      int
	CustomerID string
}

func filter(in []Order, keep func(Order) bool) []Order {
	out := make([]Order, 0, len(in))
	for _, order := range in {
		if keep(order) {
			out = append(out, order)
		}
	}
	return out
}

func mapIDs(in []Order) []string {
	out := make([]string, 0, len(in))
	for _, order := range in {
		out = append(out, order.CustomerID)
	}
	return out
}

func distinctSorted(in []string) []string {
	seen := map[string]bool{}
	out := []string{}
	for _, id := range in {
		if !seen[id] {
			seen[id] = true
			out = append(out, id)
		}
	}
	sort.Strings(out)
	return out
}

func billableCustomerIDs(orders []Order) []string {
	return distinctSorted(mapIDs(filter(filter(filter(
		orders,
		func(order Order) bool { return order.Status == "paid" }),
		func(order Order) bool { return order.CustomerID != "" }),
		func(order Order) bool { return order.Total >= 25 })))
}

func main() {
	orders := []Order{
		{ID: "o1", Status: "paid", Total: 40, CustomerID: "c2"},
		{ID: "o2", Status: "draft", Total: 12, CustomerID: "c1"},
		{ID: "o3", Status: "paid", Total: 75},
		{ID: "o4", Status: "paid", Total: 10, CustomerID: "c2"},
		{ID: "o5", Status: "paid", Total: 99, CustomerID: "c3"},
	}
	fmt.Println(strings.Join(billableCustomerIDs(orders), ","))
}
```

## 18. References

- Martin Fowler, with Kent Beck, *Refactoring. Improving the Design of Existing
  Code*, second edition, Addison-Wesley, 2018, chapter 3, "Bad Smells in Code,"
  and chapter 6, catalog entry "Replace Loop with Pipeline." The page reference
  to Replace Loop with Pipeline at page 231 is confirmed by the InformIT excerpt
  "Loops": https://www.informit.com/articles/article.aspx?p=2952392&seqNum=13,
  verified 2026-08-02.
- Martin Fowler, "Replace Loop with Pipeline," refactoring catalog:
  https://refactoring.com/catalog/replaceLoopWithPipeline.html, verified
  2026-08-02.
- Martin Fowler, "Refactoring with Loops and Collection Pipelines," 14 July
  2015: https://martinfowler.com/articles/refactoring-pipelines.html, verified
  2026-08-02.
- Martin Fowler, "Collection Pipeline," 25 June 2015:
  https://martinfowler.com/articles/collection-pipeline/, verified 2026-08-02.
- Oracle, Java SE 21 API documentation, package `java.util.stream`:
  https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/package-summary.html,
  verified 2026-08-02.
- Python Software Foundation, Python 3.14 documentation, `itertools`:
  https://docs.python.org/3/library/itertools.html, verified 2026-08-02.
- Apache Software Foundation, "RDD Programming Guide," Spark 4.2.0
  documentation: https://spark.apache.org/docs/latest/rdd-programming-guide,
  verified 2026-08-02.
- Apache Software Foundation, "Spark SQL, DataFrames and Datasets Guide," Spark
  4.2.0 documentation: https://spark.apache.org/docs/latest/sql-programming-guide,
  verified 2026-08-02.
- pandas project, "User-Defined Functions," pandas 3.0.5 documentation, section
  "`Series.pipe()` and `DataFrame.pipe()`":
  https://pandas.pydata.org/docs/user_guide/user_defined_functions.html,
  verified 2026-08-02.
