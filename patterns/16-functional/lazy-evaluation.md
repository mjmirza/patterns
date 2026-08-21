---
name: Lazy Evaluation
slug: lazy-evaluation
family: 16-functional
category: Functional
aliases: [Laziness, Deferred Evaluation, Deferred Execution, Call by Need, Non-strict Evaluation]
first_described: "Established in non-strict functional language research and call-by-need semantics"
maturity: canonical
related: [memoization, iterator, generator, stream, function-composition, foldable, monad, persistent-data-structures]
incompatible_with: [strict-resource-release, required-immediate-side-effects, stack-trace-dependent-control-flow]
verified: 2026-08-02
---

# Lazy Evaluation

## 1. Name, aliases, and lineage

The canonical name in this entry is Lazy Evaluation. In language semantics it
is often discussed through **non-strict evaluation** and **call by need**. In
library design it appears as **deferred evaluation**, **deferred execution**,
**lazy sequence**, **lazy stream**, **lazy query**, **generator**, **iterator**,
or **thunked value**. The names are close, but they do not name identical
contracts.

Non-strict evaluation says an expression may be passed or bound without being
evaluated at that point. Call by name delays evaluation but may recompute the
expression each time it is demanded. Call by need delays evaluation and shares
the result after the first demand. Zena M. Ariola and Matthias Felleisen list
"The Call-by-Need Lambda Calculus" as a 1997 Journal of Functional Programming
article, and the same publication page lists an earlier POPL 1995 conference
paper with Maraist, Odersky and Wadler
(https://ix.cs.uoregon.edu/~ariola/publications.html, verified 2026-08-02).
That paper lineage gives the semantic account behind the phrase call by need.

Haskell made laziness part of a full programming language identity. The Haskell
98 report introduction describes Haskell as a purely functional language with
non-strict semantics and says it grew out of research on non-strict functional
languages (https://www.haskell.org/onlinereport/intro.html, verified
2026-08-02). The Haskell 2010 report preface records the 1987 FPCA meeting that
formed the committee to design a common language for a family of non-strict
purely functional languages
(https://www.haskell.org/onlinereport/haskell2010/haskellli2.html, verified
2026-08-02).

In object-oriented and data-processing communities the name usually changes to
deferred execution. Microsoft documents LINQ queries as building a recipe first
and reading the data later when code asks for results
(https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/statements/linq,
verified 2026-08-02). Apache Spark documents RDD transformations as lazy:
transformations remember work and actions trigger computation
(https://spark.apache.org/docs/latest/rdd-programming-guide, verified
2026-08-02). Django documentation uses the term laziness for `QuerySet`
evaluation and for lazy translation values
(https://docs.djangoproject.com/en/4.2/topics/performance/, verified
2026-08-02).

Engineering judgement. Use "Lazy Evaluation" for the pattern when a value,
collection, or query records how to compute an answer and runs that computation
only when a forcing operation demands it. Use the narrower term "call by need"
when the implementation also memoizes a demanded expression so later demands
reuse the answer.

## 2. Problem and context

A program has a chain of computations, but early execution would do work that
may never be observed. The chain may read a large file, filter rows, sort
records, translate text, fetch related database rows, compute derived fields, or
walk an infinite conceptual sequence. A strict implementation performs each
step at the point where the step is declared. That is easy to reason about when
the data is small and the effects are cheap. It fails when the program only
needs the first matching element, a final aggregate, a page of results, or a
compiled query plan.

The situation has three common shapes.

First, a value is expensive and may not be used. A configuration object may
contain a fallback value that should be computed only if the primary path fails.
A translated label may be created before the request locale is known. Django
describes lazy translation as useful because translation can wait until the
translated string is required in a rendered template
(https://docs.djangoproject.com/en/4.2/topics/performance/, verified
2026-08-02).

Second, a sequence is too large to materialize. Python's `itertools` module is
documented as iterator building blocks for efficient looping and an "iterator
algebra" inspired by APL, Haskell, and SML
(https://docs.python.org/3.13/library/itertools.html, verified 2026-08-02).
The pattern here is not limited to Python. A sequence can expose the next item
on demand while retaining the recipe for producing later items.

Third, a query can be optimized if it remains a plan. Spark records RDD
transformations until an action requires a result
(https://spark.apache.org/docs/latest/rdd-programming-guide, verified
2026-08-02). Polars documents eager and lazy modes, with lazy queries evaluated
when collected and open to query-planner optimizations
(https://docs.pola.rs/user-guide/concepts/lazy-api/, verified 2026-08-02).
LINQ documents deferred execution for many sequence operators
(https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/statements/linq,
verified 2026-08-02).

The context that makes the pattern useful is a boundary between describing work
and demanding a value. If the codebase has no such boundary, laziness becomes
obscurity. If it has one, the boundary can reduce I/O, memory, CPU, and remote
work by delaying the moment where the program commits to a result.

That boundary should be visible in names. A method named `where`, `select`,
`map`, `filter`, `take`, or `defer` commonly reads as descriptive. A method
named `collect`, `count`, `first`, `toList`, `execute`, `render`, or `value`
commonly reads as demanding. The exact names vary by language and library, but
the distinction should be stable inside one API. When the same style of method
sometimes records work and sometimes performs I/O, readers lose the ability to
predict cost from code shape.

The pattern is also a response to partial demand. A strict pipeline commonly
answers the question "what is the full transformed collection?" before it knows
whether the caller needs the full collection. A lazy pipeline can answer a
smaller question: "what is the next item that satisfies the current demand?"
That is the reason `first`, `any`, `take`, pagination, predicate pushdown, and
projection pushdown are natural partners. They make the size of the demanded
answer smaller than the size of the source. If every caller always consumes the
whole result and no optimizer benefits from the full plan, the pattern has less
room to pay for itself.

There is a second boundary, often missed, between laziness and concurrency.
Lazy Evaluation does not mean work runs on another thread. A lazy value can be
perfectly synchronous. The work waits, then runs on the demanding caller's
thread. If the goal is to overlap work with other work, use a Future, Promise,
task, actor, or scheduler. If the goal is to avoid work until demand is known,
use Lazy Evaluation. Some systems combine both, but combining them should be a
named design decision because it changes error timing, cancellation, and
resource ownership.

## 3. Forces

Engineering judgement. These forces describe the costs seen when a program
stores computations as values instead of running them at declaration time.

- **Latency.** Favoured when skipped work dominates. Sacrificed when the first
  demand must pay for all deferred setup on a user-facing request path.
- **Memory.** Favoured for streaming pipelines that avoid materializing
  intermediate collections. Sacrificed when thunks retain large object graphs
  longer than a strict program would.
- **Coupling.** Favoured at pipeline boundaries because producers expose a
  recipe rather than a concrete collection. Sacrificed when consumers must know
  which operations force evaluation.
- **Consistency.** Mixed. A memoized lazy value gives stable results after the
  first force. A non-memoized lazy iterator may observe later mutations in the
  source collection.
- **Operability.** Sacrificed unless the forcing boundary is measured. The
  source line that declares work may not be the source line that pays for it.
- **Cost.** Favoured when less work runs. Sacrificed through wrapper objects,
  closures, iterator frames, query plans, and cache state.
- **Team topology.** Favoured when platform teams expose query or stream
  builders and product teams compose them. Sacrificed when ownership of the
  force point is unclear.
- **Cognitive load.** Sacrificed. Readers must track whether a value is a
  result, a one-shot iterator, a memoized thunk, or a query plan.
- **Failure timing.** Sacrificed. Errors move from declaration time to demand
  time, sometimes far from the code that created the lazy value.

The pattern trades time certainty for optionality. That trade is worth making
when unused branches, large data, or query planning matter. It is harmful when
readability, prompt errors, and deterministic side-effect timing matter more.

The failure-timing force deserves special weight in public APIs. A strict
constructor can reject bad arguments before it returns. A lazy constructor may
accept the same arguments and fail later inside iteration, rendering, or query
execution. That can be correct when the delayed context is part of the contract,
as with a query plan that needs a database connection later. It can be
surprising when the caller believes object construction already proved the
value is usable. API documentation should state whether construction validates
the recipe, the source, both, or neither.

The memory force also has two directions. Lazy sequences reduce peak memory
when they stream through source items and discard them promptly. Memoized lazy
structures can increase memory by retaining every demanded prefix. A lazy tree
with a saved tail can be excellent for replaying a computed prefix, yet a poor
choice for a single pass over a large log. Engineering judgement. Prefer
non-memoized laziness for one-pass streaming and memoized laziness for shared
pure values where repeat demand is expected.

The operability force is often the one that decides whether laziness survives
in a production codebase. If dashboards attribute all cost to the terminal
operation, teams may blame serializers, template renderers, or response
writers for work that was described earlier. A well-instrumented lazy API
carries declaration-site labels or plan summaries forward to the force point.
That way an operator sees both the place where the recipe was built and the
place where it ran.

## 4. Applicability and non-applicability

Reach for Lazy Evaluation when these conditions hold.

- A computation is expensive and many executions do not need its result.
- A collection may be large, infinite, or remote, and consumers commonly take a
  prefix, filter, or aggregate.
- A query optimizer needs the full plan before running any step.
- A value cannot be known at construction time, but a placeholder can travel
  through the program until the needed context exists.
- Composition is more useful than immediate materialization, as in streams,
  iterators, query builders, parser combinators, or lazy trees.
- The implementation can name and document the forcing operations.
- The team can test both declaration time and demand time.

Explicit non-applicability list.

- **Required immediate side effects.** Do not make an operation lazy when
  calling it is supposed to send mail, write an audit record, publish an event,
  or reserve inventory. Delayed execution changes the business contract.
- **Strict resource lifetime.** Do not return a lazy iterator over a database
  cursor, file handle, transaction, or lock when the resource may close before
  enumeration. Materialize inside the lifetime or return an object that owns the
  lifetime.
- **One-shot input with multiple consumers.** Do not expose a non-memoized lazy
  sequence to callers that will enumerate twice. The second pass may be empty,
  slower, or different.
- **Small deterministic data.** Do not wrap a small local list in lazy layers
  when the whole list is always consumed. Strict code is shorter and failure
  happens where the data is built.
- **Hidden network calls.** Do not let property access force remote I/O without
  naming that cost. A lazy facade that looks like an in-memory value causes
  poor capacity planning.
- **Mutation-sensitive inputs.** Do not defer reading a mutable source if the
  caller expects a snapshot. Either copy at declaration time or document that
  the sequence observes later changes.
- **Security checks that must run before authorization decisions.** Do not
  defer validation past the point where a caller can act on unvalidated data.
- **User-visible deadlines.** Do not push all work to the final render, response
  serialization, or commit hook when the earlier stages had time to amortize it.

## 5. Structure

The pattern has six recurring participants.

- **Deferred value.** The public object that represents work not yet performed.
  It may be a thunk, iterator, generator, query object, lazy list, stream, or
  promise-like wrapper for synchronous computation.
- **Recipe.** The function, expression tree, query plan, closure, or iterator
  state needed to compute the result.
- **Force operation.** The method or language construct that asks for the real
  value. Examples include iteration, `next`, `head`, `collect`, `toList`,
  `count`, `value`, rendering, or pattern matching.
- **Memo slot.** Optional storage for the result after the first force. Call by
  need and Scala `LazyList` use this idea. Scala documents `LazyList` elements
  as memoized, computed at most once
  (https://www.scala-lang.org/api/3.x/scala/collection/immutable/LazyList.html,
  verified 2026-08-02).
- **Source.** The data or dependency the recipe reads. It may be an array, file,
  database table, HTTP page, sensor stream, or earlier deferred value.
- **Consumer.** Code that composes more lazy operations or forces the value.

The relationships matter more than class names. A consumer that adds `filter`
or `map` should receive another deferred value. A consumer that asks for
`count`, `collect`, or `first` should cross the forcing boundary and pay the
cost. When those two roles are mixed under vague method names, the pattern
becomes hard to operate.

A production implementation often adds three secondary participants.

- **Demand policy.** Rules for how much work a force operation may perform.
  Examples include one item, a page, the first match, all rows, a timeout, or a
  max-step budget.
- **Invalidation policy.** Rules for whether a memoized result can become
  stale. Pure values may need no invalidation. Values that depend on time,
  locale, tenant, database state, or configuration need a policy or should not
  be memoized.
- **Diagnostic label.** A small piece of metadata that follows the recipe to
  the force point. This can be a query name, declaration location, pipeline
  name, or caller-supplied operation label.

These secondary participants are not part of the minimal pattern. They become
valuable when the lazy value crosses module boundaries or survives longer than
one local function.

## 6. ASCII structure diagram

```text
  +------------+       builds        +------------------+
  |  Consumer  |-------------------->|  Deferred Value  |
  +------------+                     +------------------+
        |                                     |
        | compose map/filter/take             | stores
        v                                     v
  +----------------+                 +------------------+
  | Deferred Value |---------------->|      Recipe      |
  +----------------+                 +------------------+
        |                                     |
        | force                               | reads
        v                                     v
  +----------------+                 +------------------+
  | Force Operation|---------------->|      Source      |
  +----------------+                 +------------------+
        |
        | optional write after first demand
        v
  +----------------+
  |   Memo Slot    |
  +----------------+

  Lazy composition returns more description.
  Forcing turns description into values, effects, or errors.
```

## 7. Dynamics

A lazy value moves through two phases. In the description phase, operations
capture functions and parameters. In the demand phase, the force operation runs
enough of the recipe to produce the requested result.

```text
Client        LazySeq        Recipe Chain       Source        Memo Slot
  |              |                |               |               |
  |-- map(f) --->|                |               |               |
  |<-- LazySeq --|                |               |               |
  |-- filter(p)->|                |               |               |
  |<-- LazySeq --|                |               |               |
  |              |                |               |               |
  |-- take(2) -->|                |               |               |
  |<-- LazySeq --|                |               |               |
  |              |                |               |               |
  |-- toList() ->|-- force ------>|-- pull ------>|               |
  |              |                |<-- item ------|               |
  |              |<-- pass item --|               |               |
  |              |-- save? ------------------------------------->|
  |              |-- maybe pull more items --------------------->|
  |<-- result ---|                |               |               |
  |              |                |               |               |

  No source items are read during map, filter, or take.
  The force operation reads only as many items as the terminal demand needs.
```

There are two runtime variants in this sequence. A non-memoized iterator
performs work each time it is pulled, and may be consumed only once. A memoized
lazy value writes the answer into the memo slot after the first force and
returns that saved answer on later demands. Mixing those variants without naming
them is a common source of bugs.

## 8. Implementation variants

**Language-level non-strict semantics.** Haskell is the reference family member
for this variant. The source program binds expressions without evaluating them
until demanded by pattern matching, primitive operations, I/O sequencing, or
strictness annotations. The Haskell report identifies non-strict semantics as
part of the language design
(https://www.haskell.org/onlinereport/intro.html, verified 2026-08-02). The
trade-off is that every reader must understand where evaluation is forced.

**Memoized thunk.** A wrapper stores a zero-argument function and a cache cell.
The first `value()` call runs the function, stores either the value or error
policy result, then returns. Later calls return from the cache. This is the
library-level call-by-need shape.

```python
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class Lazy(Generic[T]):
    def __init__(self, compute: Callable[[], T]) -> None:
        self._compute = compute
        self._ready = False
        self._value: T | None = None

    def value(self) -> T:
        if not self._ready:
            self._value = self._compute()
            self._ready = True
        return self._value


calls = 0


def load_total() -> int:
    global calls
    calls += 1
    return sum(range(5))


total = Lazy(load_total)
print("before", calls)
print(total.value(), total.value(), calls)
```

**Lazy iterator or generator.** A sequence exposes items one at a time. The
recipe may hold source state and transformation functions. Python generators,
Rust iterators, Java streams, Go iterator functions, and many collection views
fit this shape. The trade-off is that iteration order, one-shot behavior, and
source mutation rules become part of the contract.

```go
package main

import "fmt"

type Seq func(yield func(int) bool)

func Range(n int) Seq {
	return func(yield func(int) bool) {
		for i := 0; i < n; i++ {
			if !yield(i) {
				return
			}
		}
	}
}

func Map(s Seq, f func(int) int) Seq {
	return func(yield func(int) bool) {
		s(func(v int) bool {
			return yield(f(v))
		})
	}
}

func Take(s Seq, n int) []int {
	out := []int{}
	s(func(v int) bool {
		if len(out) == n {
			return false
		}
		out = append(out, v)
		return len(out) < n
	})
	return out
}

func main() {
	calls := 0
	doubled := Map(Range(10), func(v int) int {
		calls++
		return v * 2
	})
	fmt.Println(calls)
	fmt.Println(Take(doubled, 3))
	fmt.Println(calls)
}
```

**Lazy query plan.** A query object stores filters, projections, joins, sorts,
and aggregations. A terminal operation sends the plan to an optimizer or
interpreter. Spark, LINQ, Django QuerySets, and Polars all use this family of
designs, with different force operations named by each API
(https://spark.apache.org/docs/latest/rdd-programming-guide, verified
2026-08-02; https://docs.pola.rs/user-guide/concepts/lazy-api/, verified
2026-08-02).

**Lazy tree or stream with memoized tail.** A node stores a head value and a
deferred tail. Scala `LazyList` documents both laziness and memoization of
elements (https://www.scala-lang.org/api/3.x/scala/collection/immutable/LazyList.html,
verified 2026-08-02). The upside is repeated traversal of already-demanded
prefixes. The cost is retained memory for that prefix.

```rust
struct Lazy<T> {
    value: Option<T>,
    compute: Option<Box<dyn FnOnce() -> T>>,
}

impl<T> Lazy<T> {
    fn new(f: impl FnOnce() -> T + 'static) -> Self {
        Self {
            value: None,
            compute: Some(Box::new(f)),
        }
    }

    fn get(&mut self) -> &T {
        if self.value.is_none() {
            let f = self.compute.take().expect("lazy value forced twice");
            self.value = Some(f());
        }
        self.value.as_ref().unwrap()
    }
}

fn main() {
    let mut calls = 0;
    let mut total = Lazy::new(move || {
        calls += 1;
        (0..5).sum::<i32>() + calls
    });
    println!("{}", total.get());
    println!("{}", total.get());
}
```

**Strict API with lazy internals.** Some APIs expose strict methods while the
implementation internally builds a plan and forces it before returning. This
keeps callers from depending on laziness but still gives the implementation a
place to optimize. Polars documents that eager operations may call the lazy API
under the hood and collect immediately
(https://docs.pola.rs/user-guide/concepts/lazy-api/, verified 2026-08-02).

**View over mutable source.** A view delays reading a source collection until
iteration. This can be cheap and expressive, but it inherits the source's later
mutations. The API should say whether it is a live view or a snapshot. Live
views are useful in local pipelines where the source owner and consumer are the
same scope. They are risky across module boundaries because the consumer may
observe changes made after the view was created.

**Expression tree.** Some APIs store an inspectable tree instead of closures.
The tree can be optimized, serialized, translated to SQL, or sent to a cluster.
Spark, LINQ providers, and Polars are closer to this shape than to a plain
closure chain. The trade-off is that only operations expressible in the tree can
participate in optimization. A black-box callback may force local execution or
block pushdown.

**Suspended effect.** A lazy value may describe an effect, such as a database
query or file read, without running it. This variant should be treated with more
care than a pure lazy value because dropping the value means dropping the
effect. In command-style APIs, prefer an explicit `execute` method and a type
name that says the value is a pending effect.

## 9. Known production uses

**Apache Spark RDD transformations.** Spark documents transformations as lazy.
They remember transformations on a base dataset and compute them when an action
returns a result to the driver
(https://spark.apache.org/docs/latest/rdd-programming-guide, verified
2026-08-02). This is production use in a distributed data-processing engine.

**Django QuerySets and lazy translation.** Django documentation says QuerySets
can be created, passed around, and combined without database trips until a
forcing operation evaluates them. The same page documents lazy translation and
`keep_lazy()` for values whose context is known later
(https://docs.djangoproject.com/en/4.2/topics/performance/, verified
2026-08-02).

**Microsoft LINQ.** Microsoft documents many LINQ sequence operators as using
deferred execution: `Where`, `Select`, and `OrderBy` build a recipe, while
enumeration or scalar operators run it
(https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/statements/linq,
verified 2026-08-02).

**Polars LazyFrame.** Polars documents lazy and eager modes. In lazy mode, a
query is evaluated when collected, which allows predicate pushdown, projection
pushdown, and plan inspection
(https://docs.pola.rs/user-guide/concepts/lazy-api/, verified 2026-08-02).

**Scala LazyList.** Scala's standard library documents `LazyList` as an
immutable linked list whose elements are computed only when needed and
memoized at most once
(https://www.scala-lang.org/api/3.x/scala/collection/immutable/LazyList.html,
verified 2026-08-02).

## 10. Consequences

Positive consequences.

- Work that is not demanded does not run.
- Large pipelines can avoid intermediate collections.
- Query optimizers can see a larger plan before execution.
- Infinite or open-ended sequences become representable.
- The API can separate description from execution, which often improves
  composition.
- Memoized lazy values can avoid repeated expensive computation.
- Callers can pass values through layers before all context exists.

Negative consequences.

- Failure can occur far from the source line that created the lazy value.
- Side effects may run later than a caller expects, or not run at all.
- A deferred computation can retain source objects and create a space leak.
- First demand can have an unexpectedly large latency spike.
- Debuggers and stack traces may show the force point rather than the
  declaration point.
- One-shot iterators can be consumed accidentally and then appear empty.
- Memoization needs synchronization or confinement when multiple threads can
  force the same value.
- Testing must cover both the lazy wrapper and the terminal operation.

Subtle consequences.

- A lazy query can cross a layer boundary and run under a different transaction,
  locale, or authorization context than the one that created it.
- A lazy iterator can make benchmark results misleading if setup is measured
  but the terminal demand is outside the measured region.
- A lazy value can capture `self` or a request object and prolong its lifetime.
- A memoized lazy value can hide changes in a backing source, which is correct
  for a snapshot and wrong for a live view.
- A lazy expression tree can reject ordinary language operations because the
  optimizer cannot inspect them.
- A lazy API can make cancellation late. If the value is forced in a long
  synchronous loop, cancellation must be checked inside the driver, not only at
  recipe construction.

Engineering judgement. The main benefit is optionality. The main cost is hidden
time. Teams should make forcing operations visually and semantically obvious.

## 11. Failure modes and misuse

Engineering judgement. These are practical failure shapes, stated as observable
Symptom, Cause, Fix triples.

- **Symptom.** A request spends little time building a response object, then
  times out during serialization. **Cause.** Lazy properties or query objects
  are forced by the serializer after the controller has finished its visible
  work. **Fix.** Force and measure the expensive fields inside the request
  handler, or return an explicit asynchronous job.
- **Symptom.** A database transaction closes, then iteration raises a cursor or
  connection error. **Cause.** A lazy sequence escaped the resource lifetime.
  **Fix.** Materialize inside the transaction, or return a resource-owning
  iterator with explicit close semantics.
- **Symptom.** The same report query runs many times and load grows with each
  view render. **Cause.** A non-memoized lazy query is enumerated repeatedly.
  **Fix.** Materialize with `toList`, `collect`, or a local cache at the
  intended sharing point.
- **Symptom.** Heap grows while CPU is low, then garbage collection dominates.
  **Cause.** Unevaluated thunks retain large sources. GHC profiling docs name
  this as a common space-leak pattern and recommend forcing computations where
  needed (https://ghc.gitlab.haskell.org/ghc/doc/users_guide/profiling.html,
  verified 2026-08-02). **Fix.** Force smaller values earlier, add strict
  fields, or split the pipeline so sources can be released.
- **Symptom.** Logs show an audit action was prepared but no audit record
  exists. **Cause.** The audit write was stored in a lazy computation and no
  force operation demanded it. **Fix.** Keep externally visible side effects
  strict, or run them through an explicit command queue.
- **Symptom.** Results differ between two enumerations of the same query.
  **Cause.** The lazy value reads a mutable source at demand time. **Fix.**
  Snapshot the source before building the lazy value, or document live-view
  semantics and test them.
- **Symptom.** Two threads force the same lazy value and run the expensive
  computation twice. **Cause.** The memo slot is not synchronized. **Fix.** Add
  locking, single-flight behavior, or thread confinement.
- **Symptom.** A validation error appears after an authorization decision has
  already been made. **Cause.** Required validation was deferred past the trust
  boundary. **Fix.** Force validation before authorization or make the
  authorization function accept only a strict validated type.

## 12. Trade-off matrix

| Force | Lazy Evaluation | Eager Evaluation | Memoization | Iterator | Future or Promise |
|---|---|---|---|---|---|
| Latency | Moves cost to demand, can skip work | Pays early and predictably | Pays once, then fast | Pays per pull | Often starts before demand |
| Memory | Can stream, can retain thunks | May allocate full result | Retains cached result | Retains current state | Retains task state and result |
| Coupling | Couples callers to force points | Simple value contract | Couples to cache lifetime | Couples to traversal protocol | Couples to scheduler contract |
| Consistency | Depends on memo and source mutation | Snapshot if built from snapshot | Stable after first force | Often live or one-shot | Stable after completion |
| Operability | Needs force metrics | Easy timing attribution | Needs hit and miss metrics | Needs pull metrics | Needs queue and completion metrics |
| Cost | Wrapper and deferred error cost | Upfront CPU and memory cost | Cache invalidation cost | State machine cost | Scheduler and synchronization cost |
| Team topology | Good for shared query builders | Good for local code | Good for shared expensive values | Good for streaming APIs | Good for concurrent workflows |
| Cognitive load | Higher | Lower | Medium | Medium | Higher |

Eager Evaluation is the named alternative when prompt execution and simple
debugging matter. Memoization is an adjacent pattern, not a replacement,
because it may cache a strict computation. Iterator is a narrower sequence
variant. Future or Promise moves time through concurrency rather than through
pure demand.

## 13. Related and incompatible patterns

**Memoization** composes with Lazy Evaluation when a forced value should be
saved. Call by need is lazy plus sharing. A lazy iterator without memoization is
not call by need.

**Iterator** is the sequence form of laziness. It exposes a pull protocol. A
lazy collection may be built on an iterator, but a memoized lazy tree has a
different lifetime and replay contract.

**Generator** is a language-level way to write lazy iteration while preserving
local control flow in the generator body.

**Stream** composes with laziness when values are pulled or pushed in bounded
chunks. A stream with backpressure addresses fairness and resource scheduling
that a basic lazy value does not.

**Function Composition** composes well because each `map`, `filter`, or
projection can add a recipe node.

**Foldable** often forces a lazy structure. A fold over an entire sequence
demands every reachable item unless the fold operation can short-circuit.

**Monad** appears in lazy effect descriptions and parser or query DSLs. The
relationship is powerful but can hide costs if `flatMap` chains allocate large
deferred graphs.

**Command** conflicts when the command represents a required side effect. A
lazy command that may never be forced is usually a broken command.

**Resource Acquisition Is Initialization** and other strict lifetime patterns
can conflict because laziness moves use outside the lexical scope where a
resource was acquired.

## 14. Refactoring path in and out

To introduce Lazy Evaluation:

1. Name the force operation first. Decide whether it is `value`, `next`,
   iteration, `collect`, `toList`, `count`, render, or pattern match.
2. Wrap the smallest expensive computation in a deferred value.
3. Keep externally visible side effects outside the lazy recipe unless the API
   is explicitly a job or command builder.
4. Add tests proving construction does not run the computation.
5. Add tests proving the force operation runs the computation once, many times,
   or per pull according to the intended contract.
6. If memoized, add a test for repeated demand and, where relevant, concurrent
   demand.
7. Move composition operations to return new deferred values.
8. Add logging or metrics at the force boundary before expanding use.
9. Replace local eager call sites one at a time.

During introduction, keep the first version smaller than the final target. A
single lazy value around one expensive calculation teaches the team where the
force point should live. A full lazy DSL changes more contracts at once:
validation timing, error timing, resource timing, and debugging. Engineering
judgement. Expand from a narrow wrapper to a query or stream API only after the
force operation, memo policy, and observability story are stable.

When converting an eager collection pipeline, preserve output order and error
order unless the new API clearly states a change. Strict code that maps every
item before filtering may raise an error from an item that the lazy pipeline
would skip after an earlier `take`. That is often a benefit, but it is still a
behavior change. Tests should pin the desired behavior before the refactor.

Named refactorings from the refactoring family apply. **Extract Function**
isolates the expensive computation. **Replace Temp with Query** can become a
lazy query only when the query has no required side effects. **Introduce
Parameter Object** can carry a query recipe through layers before forcing.
**Inline Function** is often part of the way out when the lazy wrapper stops
earning its cost.

To remove Lazy Evaluation:

1. Identify every force operation and every consumer that depends on delayed
   execution.
2. Insert an eager materialization point at the current force boundary.
3. Move errors earlier and update tests that expected demand-time failure.
4. Replace lazy wrappers with strict values in internal APIs.
5. Delete memo slots and invalidation paths after callers stop observing them.
6. Keep streaming APIs lazy if full materialization would change memory bounds.

The path out is often partial. A query builder may remain lazy at the database
boundary while a small in-memory projection becomes strict.

Removal should also consider API trust. If callers have learned that a method
is descriptive, changing it to perform I/O immediately can break latency and
transaction expectations. Add a new strict method, migrate callers, then retire
the lazy method when the old behavior has no remaining users. For internal
code, the safer path is often the reverse: insert `collect` or `toList` at the
boundary first, then inline the lazy implementation behind that boundary.

## 15. Testing and verification

Engineering judgement. Test laziness by observing when work happens, not by
inspecting private fields.

Useful test techniques:

- Use a counting supplier to prove construction does not call the supplier.
- Force once and assert one call.
- Force twice and assert either one call for memoized laziness or two pulls for
  non-memoized laziness.
- Use a throwing supplier to prove exceptions occur at the force point.
- Use a source that records reads to prove `take(3)` reads no more than the
  needed prefix.
- Use a mutable source test to document live-view or snapshot behavior.
- Use resource-lifetime tests: build inside a closed scope, then force outside
  it, and confirm the API either rejects that shape or owns the resource.
- For lazy query plans, assert generated SQL, logical plans, or explained plans
  where the library exposes them. Polars documents `explain` for lazy query
  plan inspection (https://docs.pola.rs/user-guide/concepts/lazy-api/,
  verified 2026-08-02).
- For concurrent memoization, use a barrier so two threads demand the value at
  the same time, then assert the supplier ran once.

What becomes easier: skipping work, prefix reads, and query composition can be
tested directly. What becomes harder: timing of failures, resource ownership,
and side effects require dedicated tests because the declaration site no longer
does the work.

A useful unit-test shape is a probe source. The probe exposes `read_count`,
`closed`, and `items_requested`. A test builds a lazy pipeline, asserts all
probe counters are zero, forces a prefix, then asserts the exact number of
items requested. A second test closes the probe before forcing and confirms the
documented behavior. For a resource-owning lazy value, that behavior may be
"still works because the lazy value owns the resource." For a borrowed view,
the behavior may be "raises a clear error."

Property tests can help with equivalence to strict code. Generate finite input
lists, run the strict pipeline, run the lazy pipeline followed by full
materialization, and compare results. Then add separate properties for prefix
operations, because prefix demand is the reason the lazy version may perform
less work while returning the same prefix.

Performance tests should place timers around the force operation. A benchmark
that times only lazy construction proves almost nothing. A more useful
benchmark reports construction time, first-item time, full-materialization time,
and peak memory. For memoized values, report first force and second force
separately.

## 16. Observability signals

Engineering judgement. A healthy lazy system makes the demand boundary visible.

Log or measure these signals:

- Number of lazy values or query plans created.
- Number of force operations.
- Time spent building recipes versus forcing recipes.
- Items read from sources and items emitted to consumers.
- Prefix termination rate, such as `take`, `first`, or `any` stopping before
  the full source.
- Memo hit rate and memo miss rate.
- Size of retained memoized prefixes.
- Query plan size, optimized plan size, and terminal operation name.
- Database queries triggered by serialization or template rendering.
- Exceptions thrown during force, grouped by declaration site if that metadata
  is available.
- Heap retained by thunks, closures, iterators, or query objects.

A healthy dashboard shows low force latency for common requests, high skip rate
where laziness was introduced to avoid work, bounded memo growth, and terminal
operations in expected layers. A failing dashboard shows force latency spikes in
rendering, rising heap held by deferred closures, repeated forces of the same
query, or database trips after the request handler appears finished.

Trace spans should separate recipe construction from force. A lazy query might
emit `query.build`, `query.optimize`, and `query.execute` spans. A lazy
sequence might emit `lazy.create`, `lazy.pull`, and `lazy.materialize` spans.
The span attributes should include a bounded operation name, source type,
terminal operation, item count, and memo hit status. Do not attach full SQL with
secrets, full predicates containing user data, or large expression dumps to
ordinary logs.

Alerting should focus on ratios, not only absolutes. A high number of lazy
values created is normal for some pipelines. A rising ratio of forced values to
returned responses, a falling memo hit rate, or repeated force of the same plan
inside one request is more actionable. For data systems, compare rows scanned
with rows returned. A lazy query that returns ten rows after scanning millions
may need predicate pushdown, indexing, or a stricter boundary.

GHC documentation discusses heap profiling for space leaks and retainer
profiling for cases where an unevaluated computation retains a larger structure
(https://ghc.gitlab.haskell.org/ghc/doc/users_guide/profiling.html, verified
2026-08-02). That source is Haskell-specific, but the operational lesson
generalizes: observe retained deferred work, not only completed work.

## 17. Security and privacy implications

Engineering judgement. Lazy Evaluation is not a security pattern, but it changes
where data is read, validated, retained, and released.

Positive implications:

- Lazy pipelines can avoid reading sensitive data that a request never needs.
- Lazy projections can allow a query planner to read fewer columns, which
  reduces accidental exposure in memory.
- Deferred translation or formatting can wait until the correct user context is
  present.

Risks:

- Validation can be delayed past a trust boundary if the lazy value is treated
  as already checked.
- A thunk or query object may retain sensitive source objects longer than a
  strict value would.
- A lazy object captured in a closure may cross threads, queues, or tenants with
  more context than intended.
- A deferred database query may run after authorization context has changed.
- Error messages at force time may include recipe details from a layer that the
  caller should not see.
- Memoized lazy values can cache tenant-specific data in a shared object if the
  cache key omits tenant, locale, role, or policy version.

Practical controls:

- Force validation before authorization decisions.
- Keep tenant and authorization context in the recipe only when the force point
  can verify that the context is still current.
- Do not store lazy values containing request-scoped secrets in global caches.
- Redact recipe details in logs unless they are known to be safe.
- Prefer strict materialization at security boundaries and lazy evaluation
  inside those boundaries.

## 18. References

- Zena M. Ariola publications page. Lists "A Call-by-Need Lambda Calculus" as a
  Journal of Functional Programming 7(3):265-301, 1997 article and a related
  POPL 1995 paper. https://ix.cs.uoregon.edu/~ariola/publications.html,
  verified 2026-08-02.
- Haskell 98 Report, Introduction. Describes Haskell as having non-strict
  semantics and as growing from research on non-strict functional languages.
  https://www.haskell.org/onlinereport/intro.html, verified 2026-08-02.
- Simon Marlow, editor. Haskell 2010 Language Report, Preface. Describes the
  1987 FPCA meeting and the Haskell committee's goal of a common language for
  non-strict purely functional languages.
  https://www.haskell.org/onlinereport/haskell2010/haskellli2.html, verified
  2026-08-02.
- Apache Spark 4.2.0 documentation. RDD Programming Guide, RDD Operations.
  Documents lazy transformations and action-triggered computation.
  https://spark.apache.org/docs/latest/rdd-programming-guide, verified
  2026-08-02.
- Django documentation 4.2. Performance and optimization, Understanding
  laziness. Documents lazy QuerySets, lazy translation, and `keep_lazy()`.
  https://docs.djangoproject.com/en/4.2/topics/performance/, verified
  2026-08-02.
- Microsoft Learn. LINQ queries in C#, Run a query. Documents deferred
  execution for sequence operators and eager evaluation for scalar and
  materializing operators.
  https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/statements/linq,
  verified 2026-08-02.
- Polars user guide. Lazy API. Documents eager and lazy modes, `collect`, and
  query-plan optimizations.
  https://docs.pola.rs/user-guide/concepts/lazy-api/, verified 2026-08-02.
- Python 3.13 documentation. `itertools`, Functions creating iterators for
  efficient looping. Documents iterator building blocks and iterator algebra.
  https://docs.python.org/3.13/library/itertools.html, verified 2026-08-02.
- Scala 3 API documentation. `scala.collection.immutable.LazyList`. Documents
  lazy computation and memoization of elements.
  https://www.scala-lang.org/api/3.x/scala/collection/immutable/LazyList.html,
  verified 2026-08-02.
- Glasgow Haskell Compiler User's Guide 9.15.20260306. Profiling, memory usage
  and retainer profiling. Documents space leaks and unevaluated computations as
  retainers.
  https://ghc.gitlab.haskell.org/ghc/doc/users_guide/profiling.html, verified
  2026-08-02.
