---
name: Loops
slug: loops
family: 02-code-smells
category: Code Smell
aliases: [Loop Smell, Imperative Loop, Manual Iteration]
first_described: "Fowler, Beck 1999 (Duplicated Code, Long Method); Fowler 2018 (Replace Loop with Pipeline)"
maturity: canonical
related: [duplicated-code, long-method, primitive-obsession, feature-envy, iterator]
incompatible_with: []
verified: 2026-08-02
---

# Loops

## 1. Name, aliases, and lineage

There is no single named smell called "Loops" in the original 1999 catalog.
Martin Fowler and Kent Beck's *Refactoring, Improving the Design of Existing
Code*, Addison-Wesley, 1999, chapter 3, lists smells such as Duplicated Code,
Long Method, and Feature Envy, and a hand-written loop is one of the most
common carriers of all three. The loop itself became a first-class target only
in the second edition. Martin Fowler, *Refactoring, Improving the Design of
Existing Code*, 2nd edition, Addison-Wesley, 2018, added a refactoring named
Replace Loop with Pipeline, and its catalog page states that a loop can often
be replaced entirely by a chain of collection operations
([refactoring.com catalog, Replace Loop with Pipeline](https://refactoring.com/catalog/),
verified 2026-08-02, the entry title reads "Replace Loop with Pipeline").
Fowler explains his reasoning in the same edition, noting that pipelines read
top to bottom in the order operations happen, while a loop forces the reader
to hold the whole iteration state in their head to see the same thing.

This entry treats "Loops" as the umbrella name practitioners actually use for
a family of related smells that share one root cause, a hand-written iteration
construct doing more than one job at once. The family includes what static
analysis tools separately flag as Loop Doing Too Much, Nested Loop Complexity,
Loop-Carried Mutable State, and Manual Reimplementation of a Standard
Operation. Static analysis vendors maintain rule catalogs for multiple
languages carrying rules that flag more than one break or continue statement
per loop, and a family of cognitive complexity rules that treat nested loops
as complexity multipliers; the specific rule catalog page previously cited
here (SonarSource rule S135) has since gone offline (the subdomain no longer
resolves) and no current live or archived replacement was found, so the exact
rule ID is left unverified rather than cited. Robert C. Martin's *Clean Code*,
Prentice Hall, 2008, chapter 3,
"Functions", states the rule that blocks inside `if`, `else`, and loop
statements should be one line long, usually a function call, which is a direct
statement that a loop body growing past a single delegated call is a smell in
its own right (page 34 in the 2008 first printing, chapter 3, "Blocks and
Indenting").

Different communities use different names for pieces of the same family.
Functional programmers call the fix "point-free style" or "using combinators
instead of explicit recursion". Object-oriented practitioners call it
"replacing a loop with polymorphism" when the loop body branches on type.
Database people call the corresponding smell "row by agonizing row processing"
or the acronym RBAR, coined by Jeff Moden in a widely cited SQL Server Central
article, to describe a cursor loop doing what a single set-based query should
do ([SQL Server Central, "Hidden RBAR, Triangular Joins" by Jeff Moden](https://www.sqlservercentral.com/articles/hidden-rbar-triangular-joins),
verified 2026-08-02, the article opens by defining RBAR as "Row By Agonizing
Row" and attributes the coinage to Moden). All of these names point at the
same underlying problem, an imperative loop is being used as a general
purpose control structure to accomplish a transformation, a query, an
aggregation, or a side effect, without the reader being told which of those it
is doing until they trace every line inside it.

## 2. Problem and context

A loop is the most flexible construct available in an imperative language. A
`for`, `while`, or `foreach` can filter, transform, aggregate, search, mutate
external state, perform I/O, and branch on index parity, all inside one block,
in any combination, in any order. That flexibility is exactly the problem.
Nothing about the syntax of a loop tells the reader which of those things is
happening until they read the whole body, and nothing prevents a second
concern from being added to a loop that already had one, because the loop
does not resist growth the way a function signature or a type does.

The smell shows up in a recognisable shape. A method opens a loop over a
collection. The first few lines do what the loop's name implies, say
filtering active users. A later maintainer needs to also collect a total, so
a running sum variable is declared above the loop and incremented inside it.
A third maintainer needs to log a warning for a particular case, so a
conditional and a call to a logger are added inside the same loop, using the
same loop variable. Six months later the loop is filtering, summing, and
logging in one pass, none of it named, and a change to the filtering logic
risks silently breaking the summation because both live in the same
unstructured block, sharing mutable state that only exists because the loop
happened to be there.

The context in which this problem is worst is exactly the context where loops
are reached for by reflex, iterating over an in-memory collection to produce
another collection, a scalar, or a side effect. In that context nearly every
mainstream language now ships a standard library of composable operations,
`map`, `filter`, `reduce`, `forEach`, `find`, `some`, `every`, `flatMap`, or
their local equivalents, that name the operation being performed and forbid
mixing it with an unrelated one inside the same syntactic block. The loop
smell is therefore strongest in codebases that predate those libraries, in
languages where the libraries exist but the team has not adopted the idiom,
and in performance-critical code where the fused, hand-rolled loop genuinely
outperforms the composed pipeline and the trade-off has to be made
deliberately rather than by habit.

## 3. Forces

The loop smell sits at the crossing point of several forces that pull against
each other, and naming which one matters most in a given piece of code is
most of the diagnostic work. This section is engineering judgement, weighing
pressures observed across many codebases rather than a claim from a single
source.

Readability pulls toward small, named, single-purpose operations, because a
reader scanning a pipeline of `filter().map().reduce()` calls can stop
reading at the name of the step they care about, while a reader of a raw loop
has to simulate the whole loop mentally to know what any one line does.
Performance sometimes pulls the opposite way, because a hand-fused loop that
computes several results in a single pass over the data touches memory once,
while a plain chain of separate collection operations can materialise an
intermediate collection at every step, trading memory bandwidth and garbage
collection pressure for readability. Whether that trade actually costs
anything measurable depends entirely on the runtime, some pipeline
abstractions genuinely fuse to a single pass at compile time or through lazy
evaluation, and some do not, so this force cannot be resolved by rule of
thumb alone, it has to be resolved by knowing the specific language runtime
in front of you.

Debuggability pulls toward the loop, because a breakpoint set inside a
`for` loop body stops exactly where the programmer expects, with every local
variable of the enclosing method visible, while a breakpoint set inside a
lambda passed to a chained collection method stops inside an unfamiliar
stack frame, often several frames deep inside library code, with the
enclosing method's other locals out of scope. Composability and testability
pull toward extraction, because a named predicate function passed to
`filter` can be unit tested on its own, reused in a second place, and given
a name that documents intent, none of which is available to a bare
conditional buried inside a loop body. Team familiarity is a force too, a
functional pipeline style is unfamiliar to engineers who learned imperative
languages first, and a codebase that switches idiom mid-file without
consistency pays a comprehension cost regardless of which idiom is chosen.

Correctness under mutation is the sharpest force of all. A loop with a
mutable accumulator variable declared outside it is trivially easy to get
subtly wrong, an accumulator initialised once but the loop re-entered on
retry, an index variable captured by reference inside a closure created
inside the loop body, a break condition that skips the final increment. A
pipeline built from pure functions removes an entire category of that risk
by construction, because there is no shared mutable state between steps for
a bug to hide inside, at the cost of needing the reader to understand
function composition instead of sequential statements.

## 4. Applicability and non-applicability

Loops as a control structure are always applicable. What is being diagnosed
here is the smell of a loop doing more than one job, or reimplementing an
operation the standard library already names, and the applicability list
below is about when to replace that loop with a named, composed alternative,
not about banning loops from a codebase.

Reach for replacing a loop with named operations when.

- The loop body performs a single conceptually simple transformation, filter,
  or aggregation, and a standard library function already names that
  operation directly, `map`, `filter`, `reduce`, `find`, `some`, `every`,
  `groupBy`, `sum`, `sorted`.
- The loop body has grown to do two or more unrelated things in the same
  pass, and the two things have different reasons to change, which is the
  Single Responsibility Principle applied at the statement-group level rather
  than the class level.
- The loop's accumulator variable is mutated in more than one place inside
  the body, making it hard to state the accumulator's invariant at any single
  point in the loop.
- Nested loops express a relationship between two collections, a join, a
  cross product, or a lookup, that a set-based or indexed operation expresses
  more directly and, in many runtimes, more efficiently.
- The team's other code in the same language already uses the composed idiom
  consistently, so converting this loop removes an inconsistency rather than
  introducing one.
- The loop is inside application or business logic where the difference
  between one pass and three passes over a small collection, tens to low
  thousands of elements, has no measurable effect on the product.

Do not replace the loop, and treat the pipeline urge itself as the smell to
resist, when.

- The loop is on a genuinely hot path, verified by profiling rather than
  assumed, where allocation of intermediate collections or lambda dispatch
  overhead has a measured cost the pipeline form cannot avoid in the target
  runtime. C row-major matrix multiplication, audio sample processing, and
  game engine per-frame update loops are canonical examples where the fused,
  index-based loop is the correct and idiomatic choice, not a smell.
- The loop needs to break out early based on a condition evaluated partway
  through, and the language's pipeline operations either cannot short
  circuit the same way or make the short circuit harder to read than the
  `break` statement it would replace. Some languages solve this well, Java
  streams support `findFirst` with implicit short circuiting, Python
  generator expressions are lazy by construction, but not every language's
  eager collection pipeline shares that property, and forcing a short
  circuit through `reduce` with a sentinel value is often less readable than
  the loop it replaced.
- The loop needs to maintain complex, multi-field state across iterations
  that does not reduce cleanly to a single accumulator, a state machine
  walking a token stream is the standard example, where a hand-written loop
  with named state variables communicates the state machine more clearly
  than folding the whole machine into one accumulator object passed through
  `reduce`.
- Debugging the specific failure requires stepping through iterations one at
  a time with full access to surrounding local state, and the team's
  debugger tooling handles lambda frames poorly. This is a real constraint
  in some IDE and language combinations even though it is not a permanent
  one.
- The collection is a lazy or streaming source with backpressure semantics,
  and converting it into an eager pipeline defeats the entire reason the
  streaming abstraction was chosen, in which case the fix is to use the
  streaming library's own reactive operators, not a plain in-memory loop
  either way.
- The code is deliberately written for a reader unfamiliar with functional
  idioms, for example a teaching example, an onboarding tutorial, or a
  codebase where the team has explicitly decided imperative style is the
  house standard, and introducing a pipeline in isolation would create the
  exact inconsistency this smell exists to prevent.

## 5. Structure

The smell has no class diagram, because it is a code shape rather than a
design pattern with participants that collaborate across objects. The
structure that matters is the shape of the loop body itself, and the
structure of its replacement.

A smelly loop typically has three overlapping structural layers stacked
inside one syntactic block, each of which a well-factored version separates
into its own named unit.

- The iteration mechanism, the `for`, `while`, or `foreach` header and the
  index or cursor variable it manages. This layer is pure plumbing and
  carries no business meaning of its own.
- The per-element decision, the predicate that decides whether an element is
  relevant, the transformation that maps one element to another shape, or the
  side effect performed for each element. This layer carries the actual
  business rule, and is exactly the part that deserves a name.
- The cross-element state, the accumulator, running total, collected result
  list, or early-exit flag, that carries information from one iteration to
  the next. This layer is where correctness bugs concentrate, because it is
  the only part of the loop with memory across iterations.

The replacement structure names each layer separately. The iteration
mechanism becomes the pipeline call itself, `list.stream()`,
`[x for x in items]`, `items.iter()`. The per-element decision becomes a
named function, method reference, or a lambda short enough to read as a
single expression, passed as an argument. The cross-element state becomes
either the pipeline's own fold or reduce step, which forces the accumulator's
combining rule to be a single pure function rather than a sequence of
statements, or, if the state genuinely needs multiple named fields, a small
immutable value object that the fold step returns a new instance of on every
iteration rather than mutating in place.

## 6. ASCII structure diagram

```
BEFORE, one undifferentiated block

  +----------------------------------------+
  | for item in items, do                  |
  |   iteration mechanism (index, cursor)   |
  |   +-------------------------------+     |
  |   | per-element decision          |     |
  |   | (predicate / transform /      |     |
  |   |  side effect, mixed together) |     |
  |   +-------------------------------+     |
  |   +-------------------------------+     |
  |   | cross-element state mutation  |     |
  |   | (accumulator, flags, counts)  |     |
  |   +-------------------------------+     |
  +----------------------------------------+

AFTER, three separately named layers

  items
    |
    v
  [ iteration mechanism ]  (pipeline entry point, library owned)
    |
    v
  [ named predicate / transform ]  (small, independently testable)
    |
    v
  [ named fold or reduce step ]  (single combining function, no shared
    |                             mutable state between steps)
    v
  result
```

## 7. Dynamics

The runtime behaviour of a smelly loop and its pipeline replacement can
differ in a way that matters, and understanding that difference is part of
diagnosing whether a given loop should be left alone. The three dynamics
below show the difference for a two-step transform-then-filter operation.

```
Hand-written loop, single pass, eager evaluation

  time ---->
  element 1, transform then check predicate then keep or drop, next
  element 2, transform then check predicate then keep or drop, next
  element 3, transform then check predicate then keep or drop, next
  ...
  memory touched per element, 1 pass, 0 intermediate collections

Plain eager pipeline, two passes, two intermediate collections

  pass 1 map,    el1->t1  el2->t2  el3->t3  ...   [t1, t2, t3, ...]
  pass 2 filter, scan [t1..tn], keep matching, produce  [t1, t3, ...]
  memory touched per element, 2 passes, 1 full intermediate collection
  materialised between them

Lazy or fused pipeline (Java Stream, Rust Iterator, Python generator)

  time ---->
  element 1, map then filter, kept or dropped, pulled by consumer
  element 2, map then filter, kept or dropped, pulled by consumer
  element 3, map then filter, kept or dropped, pulled by consumer
  memory touched per element, 1 pass, 0 intermediate collections,
  because each stage pulls the next element only when the downstream
  stage asks for it
```

The middle case, a plain eager pipeline built from array methods that each
return a new array, is the one engineers worry about when they resist
replacing loops for performance reasons, and the worry is legitimate for
languages and libraries that behave that way, JavaScript's `Array.prototype`
methods among them, each call to `.map()` or `.filter()` on a plain array
allocates and returns a brand new array. The bottom case, a lazy or fused
pipeline, is what languages with iterator-based standard libraries provide
by default, and it recovers the single-pass, zero-intermediate-allocation
behaviour of the hand-written loop while keeping the named, composed syntax.
Rust's own language book states this directly for its iterator adapters,
"Iterators, although a high-level abstraction, get compiled down to roughly
the same code as if you'd written the lower-level code yourself. Iterators
are one of Rust's zero-cost abstractions" (The Rust Programming Language,
"Comparing Performance, Loops vs. Iterators",
[https://doc.rust-lang.org/book/ch13-04-performance.html](https://doc.rust-lang.org/book/ch13-04-performance.html),
verified 2026-08-02).

## 8. Implementation variants

The fix for the loop smell is language and situation dependent, and the
variants below are the ones that come up in practice, each with its own
trade-off rather than one universal answer.

Named higher-order functions is the most common variant, replacing the loop
with a chain of `map`, `filter`, and `reduce` or their local equivalents,
each given a small named function or an inline lambda short enough to read
as one expression. This is the variant Fowler's Replace Loop with Pipeline
refactoring describes directly, and it is the default reach in languages
whose standard library ships lazy or fused iterator chains, Java's
`java.util.stream`, C#'s LINQ, Rust's `Iterator` trait, Kotlin's sequence
operators. It is also available, with the eager-materialisation caveat from
dimension 7, in JavaScript's `Array.prototype` methods and Python's list
comprehensions.

Comprehensions and generator expressions is the language-idiomatic variant
in Python and, in a more limited form, in languages with list comprehension
syntax. `[transform(x) for x in items if predicate(x)]` names the same
filter-then-map operation as a chained pipeline call but reads as a single
expression rather than a sequence of method calls, and Python's own style
guide, PEP 8, recommends comprehensions over `map` and `filter` calls with
lambda arguments for exactly this readability reason. A generator expression,
using parentheses instead of brackets, also gives the lazy, single-pass
behaviour from dimension 7 without needing a separate streaming library.

Extract Function on the loop body is the variant that applies even when the
loop cannot or should not be replaced by a library pipeline call, most often
because of the early-exit or hot-path exceptions in dimension 4. The loop
stays a loop, but its body is reduced to a single call to a well-named
function, so the loop's header communicates the iteration and the extracted
function's name communicates the per-element work, separating the two
layers from dimension 5 without changing the iteration mechanism at all.
This is the variant Robert Martin's rule about one-line loop and conditional
bodies in *Clean Code* is describing.

Polymorphism replacing a type-switch inside a loop is the variant that
applies when the per-element decision inside the loop body branches on the
runtime type or a type tag of the element, `if (shape.type == "circle")` and
so on. Replacing the branch with a virtual method call on the element itself,
so each element knows how to handle itself, removes both the branch and the
loop's dependency on every concrete type the branch enumerates. This variant
is a direct application of the Strategy or Visitor pattern to the loop body
rather than a pipeline call, and is the correct fix when the per-element
decision is the thing growing over time rather than the iteration itself.

Set-based or vectorised operations is the variant used when the "loop" is
conceptually operating on a whole collection at once rather than element by
element, database queries replaced by a single `SELECT ... WHERE` instead of
a cursor loop, and numeric code replaced by array-level operations in a
library such as NumPy that dispatches to compiled, often SIMD-vectorised,
routines instead of a Python-level `for` loop. This variant delivers both the
readability benefit and, unlike most of the others, a genuine and often large
performance benefit, because the per-element work moves out of the
interpreted or per-row execution model entirely.

Parallel and streaming operators is the variant for large or continuous data
where a single-threaded in-memory loop or pipeline cannot scale, `Stream`
converted to `parallelStream()` in Java, a sequential collection operator
chain replaced by a distributed data-processing engine's RDD or DataFrame
transformations, or a
finite in-memory loop replaced by a reactive stream operator chain, RxJS or
Reactor, that processes elements as they arrive rather than after the whole
collection is materialised in memory.

## 9. Known production uses

The language and library features that exist specifically to replace the
hand-written loop are themselves the clearest evidence that treating loops as
a smell worth naming is an established, widely adopted engineering practice,
not a stylistic preference of one book.

The Java Stream API, introduced in Java 8 in 2014, ships in the standard
library specifically to let element-by-element loop logic be expressed as a
declarative pipeline. Its own package documentation states its purpose
directly, "Classes to support functional-style operations on streams of
elements, such as map-reduce transformations on collections"
([Oracle, java.util.stream package summary, Java SE 8](https://docs.oracle.com/javase/8/docs/api/java/util/stream/package-summary.html),
verified 2026-08-02, quoted sentence confirmed present in the fetched page).
Every major Java shop that adopted Java 8 or later, and every Java codebase
scanned by the widely used static analysis tool SonarQube, is a production
instance of loops being replaced by this exact mechanism at scale.

Microsoft's LINQ, Language Integrated Query, shipped in C# 3.0 in 2007 and
is documented as letting a developer perform "filtering, ordering, and
grouping operations on data sources with a minimum of code", using the same
query syntax "to query and transform data from any type of data source"
([Microsoft Learn, "Language Integrated Query (LINQ) - C#"](https://learn.microsoft.com/en-us/dotnet/csharp/programming-guide/concepts/linq/),
verified 2026-08-02, quoted phrases confirmed present in the fetched page).
LINQ is used throughout the .NET stack, including inside ASP.NET Core and
Entity Framework Core, both maintained by Microsoft, where LINQ query syntax
compiles to expression trees that the Entity Framework Core provider
translates into SQL, replacing what would otherwise be a row-by-row loop
issuing individual queries.

Python's `itertools` module, part of the standard library since Python 2.3
and continuously maintained, is described in its own documentation as
implementing "a number of iterator building blocks inspired by constructs
from APL, Haskell, and SML"
([Python documentation, itertools module](https://docs.python.org/3/library/itertools.html),
verified 2026-08-02, quoted sentence confirmed present in the fetched page).
`itertools.chain`, `itertools.groupby`, and `itertools.islice` exist
specifically to compose iteration steps instead of writing nested loops with
manual bookkeeping, and the module ships in every standard CPython
installation, making it one of the most widely distributed loop-replacement
toolkits in any language.

Google's Guava library for Java, maintained by Google and in wide
production use since 2010, shipped `FluentIterable` specifically to let a
loop's filter, transform, and limit steps become a single chained
expression before the Java Stream API existed. Guava's own API
documentation describes it as offering "chaining methods which return a new
FluentIterable based in some way on the contents of the current one"
([Guava 23.0 API documentation, FluentIterable](https://guava.dev/releases/23.0/api/docs/com/google/common/collect/FluentIterable.html),
verified 2026-08-02, quoted sentence confirmed present in the fetched page),
with a documented usage example that filters, transforms, and limits a
client list in one chained expression rather than a hand-written loop. The
same page now states that FluentIterable is discouraged in favour of the
Stream API for new code, which is itself evidence for the argument this
entry makes, the loop-to-pipeline idiom did not arrive with any single
library, it kept being reinvented across the Java standard library and its
third-party library set because the underlying problem, a hand-written loop
doing an unnamed job, kept recurring.

## 10. Consequences

Positive consequences of recognising and fixing the loop smell.

- Each step of the transformation gets a name, either the name of the
  library function called, `filter`, or the name of the predicate function
  passed to it, which turns a block of statements a reader must simulate
  into a sentence a reader can scan.
- Per-element logic extracted into its own named function becomes
  independently unit testable, without needing to construct a whole
  collection and iterate it to exercise one branch of the old loop body.
- Shared mutable accumulator state, the most common source of loop-related
  bugs, is either removed entirely, in the case of pure `map` and `filter`
  chains, or concentrated into a single combining function, in the case of
  `reduce`, which is far easier to reason about and test in isolation than
  an accumulator mutated from several places inside a loop body.
- The fix frequently reveals that a loop was doing two or three unrelated
  things, and separating them into distinct named steps or functions often
  surfaces a duplicated computation, an unnecessary pass, or a bug that had
  been hiding behind the loop's apparent simplicity.
- In languages with lazy or fused pipeline semantics, the resulting code can
  match or exceed the performance of the hand-written loop it replaced,
  because the compiler or runtime can reason about a declarative pipeline in
  ways it cannot reason about an arbitrary imperative block.

Negative consequences, stated plainly rather than smoothed over.

- A plain eager pipeline in a language whose collection methods each return
  a new materialised collection genuinely does more allocation and more
  memory traffic than the single-pass loop it replaced, and this cost is
  real, not hypothetical, in JavaScript, in Python's `map` and `filter`
  builtins used without conversion to generators, and in any language where
  the pipeline abstraction is eager by default.
- Debugging a chain of lambdas is harder in most current debugger tooling
  than debugging a loop, because a breakpoint inside a lambda argument stops
  inside an unfamiliar call stack, often generated or synthetic frames from
  the library's internal machinery, with the surrounding method's other
  local variables out of the debugger's immediate scope.
- Overusing method chaining to force every loop into a one-line pipeline can
  produce code that is harder to read than the loop it replaced, when the
  chain grows past four or five stages, or when intermediate results would
  have benefited from a name that a fluent chain has no natural place to
  attach.
- A team unfamiliar with the composed idiom pays a real ramp-up cost, and
  code review comments arguing about "loop versus pipeline" style on every
  pull request is itself a symptom of the team not having settled the
  question at the level of a house style guide.
- Some pipeline operators short circuit differently, or not at all, compared
  to a loop's `break` statement, and a plain translation that forgets this
  can silently change behaviour, for example converting a loop that stops at
  the first match into a `map` followed by `filter` that still processes the
  entire collection.

## 11. Failure modes and misuse

This dimension is largely engineering judgement drawn from patterns observed
across codebases and static analysis rule catalogs, presented as
Symptom, Cause, Fix triples so each failure is tied to something a reader can
actually observe.

Symptom, a single loop computes two or three unrelated results and a bug fix
to one of them breaks a test that only checks the other. Cause, the loop's
body mixes an unrelated filter, sum, and side effect in one pass because each
was added independently by a different change over time, with nothing in the
loop's shape preventing the addition. Fix, split the loop into separate named
operations, one filter or map pass per concern, even if this means iterating
the collection more than once, then measure whether the extra pass actually
matters before reintroducing a fused hand-written loop for performance.

Symptom, a loop variable captured inside a closure created inside the loop
body consistently refers to the same, final value of the loop variable
across every closure instance, instead of the value at the time each closure
was created. Cause, the loop uses a single mutable binding for the loop
variable shared by every iteration, and every closure created inside the
loop closes over that one binding rather than a fresh binding per iteration.
This was the actual, documented behaviour of `var`-declared loop variables in
pre-ES6 JavaScript and remains a live trap in any language where the loop
variable is a single mutable slot reused across iterations rather than a
fresh binding created per iteration. Fix, use a per-iteration binding, `let`
in modern JavaScript, or replace the loop with `map` or `forEach`, whose
callback parameter is a fresh binding on every call by construction.

Symptom, a chain of `.map()` and `.filter()` calls on a large array measurably
increases both latency and peak memory in a profiler, compared to the loop it
replaced, in a language whose array methods each return a new array. Cause,
the pipeline is eager rather than lazy, so each stage fully materialises its
output before the next stage begins, producing as many intermediate arrays
as there are stages. Fix, either fuse the stages back into a single loop or
a single `reduce` call for the hot path specifically, or switch to a lazy
construct native to the language, a generator expression in Python, a lazy
sequence in Kotlin, an actual `Stream` rather than a pre-collected list in
Java, that gives back the single-pass property without abandoning the named,
composed shape.

Symptom, a nested loop over two collections runs noticeably slower as either
collection grows, well past what the algorithm's intended purpose would seem
to require. Cause, the nested loop is performing an O(n times m) linear
search inside a linear search, the classic accidentally quadratic pattern,
often because the inner collection was originally small and stayed a `List`
or array instead of being converted to a `Map` or `Set` keyed by the lookup
field once the outer loop started calling into it repeatedly. Fix, build a
lookup index, a hash map keyed by the join field, once before the loop, then
replace the inner linear scan with a single indexed lookup, turning the
nested loop's complexity from quadratic to linear.

Symptom, a database access layer contains a loop that issues one query per
row of an outer result set, and the endpoint it backs gets slower in direct
proportion to the number of rows a user's account happens to have. Cause,
this is the N plus 1 query pattern, a loop-shaped symptom with a
database-specific name, where an object relational mapper lazily fetches an
association inside a loop over the owning collection instead of the caller
eagerly fetching the association for the whole collection in one query up
front. Fix, replace the per-row query inside the loop with a single batched
query or an eager-load join issued before the loop starts, collapsing what
was N-plus-1 round trips into one or two.

Symptom, a loop's exit condition is duplicated, once as the loop's own
condition and again as an early `return` or `break` buried several lines
into the body, and a later edit updates one copy of the condition without
noticing the other, producing an off-by-one bug or an infinite loop. Cause,
the loop's termination logic is expressed in two unsynchronised places
instead of one. Fix, express the termination condition once, either as the
loop header alone or, if the exit condition genuinely depends on
per-iteration computation, replace the loop with a construct whose
short-circuiting is a single named operation, `find`, `takeWhile`, or a
`while` loop whose single condition is itself a well-named predicate
function computed once per iteration rather than inlined.

## 12. Trade-off matrix

The comparison below is between four concrete, named ways of expressing the
same iteration, a hand-written imperative loop, a named higher-order
function pipeline, an extracted-function loop, and a set-based or vectorised
operation, scored against the forces named in dimension 3.

| Force | Hand-written loop | Named pipeline (map/filter/reduce) | Extract Function on loop body | Set-based / vectorised operation |
|---|---|---|---|---|
| Readability of intent | Low, reader simulates the whole body | High, each stage is named | Medium, iteration and logic still visually merged but logic is one call | High, describes the whole outcome, not the mechanism |
| Debuggability with a step debugger | High, breakpoints land on plain statements with full local scope | Low to medium, lambda frames vary by runtime | High, breakpoint inside the extracted function behaves like any normal call | Low, execution happens inside compiled or query-engine code, often opaque to a source-level debugger |
| Risk from shared mutable state | High, accumulator can be mutated from several places | Low, `reduce` concentrates the combining logic into one function | Medium, unchanged from the original loop unless the accumulator is also extracted | Low to none, the operation is expressed declaratively with no explicit accumulator |
| Performance on a large single-machine collection, plain default form | High, single pass by construction | Depends on runtime, low with eager materialising libraries, high with lazy or fused ones | High, unchanged from the original loop | Often highest, dispatches to compiled or vectorised routines |
| Early-exit / short-circuit clarity | High, `break` is explicit and familiar | Depends on operator, `find` and lazy sequences short circuit cleanly, `reduce` does not by default | High, unchanged from the original loop | Varies, `LIMIT` and `TOP` in SQL are explicit, some vectorised APIs have no short circuit at all |
| Team ramp-up cost | Low, universally known | Medium to high for teams new to functional idioms | Low, same syntax the team already knows | Medium, requires knowing the target library or query language |
| Testability of per-element logic in isolation | Low, embedded in the loop body | High, function passed to the pipeline can be tested alone | High, the extracted function can be tested alone | Low to medium, the per-row rule usually lives inside a query expression rather than a standalone unit |

## 13. Related and incompatible patterns

Duplicated Code and the loop smell reinforce each other in a specific way, a
loop copy-pasted to a second location with one line changed is simultaneously
an instance of Duplicated Code and an instance of the loop doing an
unexamined, unnamed job, and Extract Function, the primary refactoring for
Duplicated Code, is also the primary first step for de-smelling a loop, which
is why dimension 8 lists it as a variant here rather than treating it as a
separate technique.

Long Method composes with the loop smell almost universally, because a loop
that has accumulated several unrelated responsibilities is one of the most
common single causes of a method growing past a comfortable length, and
Fowler's own Extract Function refactoring, applied either to the loop body or
to the whole loop as a unit, is the standard fix for both smells at once.

Primitive Obsession shows up alongside the loop smell when a loop's
accumulator is a raw counter, a raw boolean flag, or a raw string being
built up with concatenation, instead of a small named value object, and
replacing the primitive accumulator with a value object often naturally
produces the single combining function that dimension 8's `reduce` variant
calls for.

Feature Envy shows up when a loop reaches deeply into another object's
internal fields on every iteration to make its per-element decision, and the
correct fix is frequently the polymorphism variant from dimension 8, moving
the per-element decision onto the object being examined rather than leaving
it inside the loop that envies that object's data.

The Iterator pattern is the structural foundation the loop smell's fix relies
on, not a competing alternative to it. Every `map`, `filter`, and `reduce`
call described in this entry is implemented on top of an iterator or
iterable protocol, so replacing a hand-written loop with a pipeline is best
understood as delegating the iteration mechanism to a well-tested,
already-named implementation of Iterator, rather than introducing a
different pattern in place of one.

There is no pattern this entry treats as incompatible in the strict sense,
because the fix described here is a refactoring of implementation shape, not
a structural commitment that forecloses other design choices. The closest
thing to an incompatibility is the hot-path and streaming exceptions in
dimension 4, where converting a loop to a pipeline actively conflicts with a
performance or backpressure requirement, and in those cases the correct move
is to keep the loop, not to force a pattern onto code where its forces do
not favour it.

## 14. Refactoring path in and out

Refactoring a smelly loop into named operations is a sequence of small,
independently verifiable steps, and the same sequence run in reverse is how
a team would deliberately reintroduce a fused loop once profiling justifies
it.

Path in, from a hand-written loop to named operations.

1. Identify how many distinct jobs the loop is doing by listing every
   variable it reads that was not declared inside the loop, and every
   variable it writes that survives past the loop. Each write target that
   is not the loop's stated primary result is a separate job hiding inside
   the loop.
2. Pick the single job most entangled with the others, usually the one whose
   variable is mutated from more than one place inside the body, and extract
   its per-element logic into a small, well-named function using the Extract
   Function refactoring, leaving the loop otherwise unchanged and re-running
   the existing tests to confirm behaviour has not moved.
3. Replace the loop's iteration and that extracted function's call site with
   a single call to the language's `map` or `filter` operation, passing the
   extracted function as the argument, and delete the loop's manual index
   or cursor bookkeeping now that the standard library owns it.
4. Repeat steps 2 and 3 for each remaining job the loop was doing, in order
   from least to most entangled with the others, so that each step leaves
   the code in a state where the existing test suite still passes.
5. Where two or more of the resulting jobs are still combined into a single
   `reduce` because they genuinely share one pass over the data for a
   measured performance reason, replace the loose accumulator variable with
   a single small immutable value object, so the fold step returns a new
   instance rather than mutating shared state, closing the correctness gap
   named in dimension 10 without losing the single-pass property.
6. Re-run the full test suite and, if the loop was on a path with an
   existing performance benchmark, re-run that benchmark before and after to
   confirm the change did not regress it, per the guidance in dimension 15.

Path out, from named operations back to a hand-written loop, used only when
profiling justifies it.

1. Confirm with a profiler, not intuition, that the specific pipeline call
   chain is a measurable cost in the workload that matters, and record the
   before numbers.
2. Inline the pipeline's stages back into a single loop body, preserving
   each stage's extracted function as a call inside the loop rather than
   inlining its logic directly, so the loop still delegates each per-element
   decision to a named, independently testable function.
3. Fold any separate accumulators back into whichever accumulator scheme is
   simplest for the specific case, while keeping the combining logic inside
   a single clearly commented block rather than scattering it across the
   loop body, so a future reader can still find the seam if the code needs
   to be split apart again later.
4. Re-run the same benchmark used in step 1 to confirm the fused loop
   actually delivers the expected improvement before keeping the change, and
   leave a comment at the loop explaining why it was deliberately fused,
   referencing the benchmark, so a future refactoring pass does not undo the
   optimisation by reflex.

## 15. Testing and verification

Loops are among the hardest constructs to test thoroughly precisely because
their internal state is invisible from outside the enclosing function, and
extracting the per-element logic into a named function is itself the single
biggest improvement to testability available here, because a plain unit test
can call that function directly with a handful of representative inputs
without needing to construct a whole collection or exercise the loop's
iteration mechanism at all.

Boundary values matter more for loop-related code than almost any other
construct, because loops are the primary source of off-by-one errors. Test
an empty collection, a single-element collection, and a collection at
whatever size triggers a change in the loop's behaviour, a batch size limit,
a page boundary, the point where an early-exit condition first becomes true.
For nested loops, test both the inner and outer collection independently at
each of these boundary sizes, since an off-by-one in the outer loop and one
in the inner loop are independent bugs that a single combined test can mask.

For an extracted per-element predicate or transform function, standard
example-based unit testing covers most of the value, but for functions with
a genuinely large input domain, integer arithmetic, string parsing, boundary
comparisons, a property-based testing tool is a stronger fit than a
hand-picked list of examples, because it generates a wide range of inputs
automatically and shrinks a failing case down to the smallest input that
still reproduces it. Property based testing frameworks exist for most
mainstream languages, Hypothesis for Python, fast-check for JavaScript and
TypeScript, and QuickCheck-derived libraries for Haskell and several other
languages, and are well suited to exactly this kind of small, pure,
extracted function.

For the loop-to-pipeline conversion itself, treat it as a refactoring, which
means the test suite that exists before the change should pass unmodified
after it, per Fowler's own definition of refactoring as a change in internal
structure that does not alter observable behaviour ([Fowler, *Refactoring*,
2nd edition, Addison-Wesley, 2018], the book's introduction states this
definition directly). If a loop-to-pipeline change requires modifying an
existing test to keep passing, that is a signal the refactoring accidentally
changed behaviour rather than only structure, and the change should be
treated as suspect until the discrepancy is understood.

Where performance is a stated reason for choosing one form over another,
verification means a repeatable microbenchmark, not a single manual timing
run, because JIT warm-up, garbage collection pauses, and system load noise
can each produce a misleading single measurement. Java's JMH benchmarking
tool, Google's Benchmark library for C++, and language-native benchmark
tooling such as Go's `testing.B` and Rust's `criterion` crate exist
specifically to control for these effects, and any performance claim used to
justify keeping a hand-written loop over a pipeline, or vice versa, should be
backed by one of these rather than by an informal timing measurement taken
once.

## 16. Observability signals

A loop smell rarely produces its own distinct runtime signal, because the
smell is about code shape rather than a runtime error, but three categories
of observable evidence reliably point back to it once you know to look for
them.

Static analysis signals are the most direct. Cyclomatic complexity and
cognitive complexity metrics, both reported by tools such as SonarQube,
directly penalise nested loops and loops containing multiple conditional
branches, and a rising complexity score on a specific method over successive
commits is a strong indicator that a loop inside it is accumulating
unrelated responsibilities the way dimension 2 describes. SonarSource's own
rule catalog carries multiple rules specifically about loop shape, including
the rule limiting a loop to a single `break` or `continue` statement cited
in dimension 1, and a spike in violations of these rules for a file is a
direct, tool-generated signal.

Runtime latency signals show up when the loop is hiding an accidentally
quadratic algorithm or an N plus 1 query pattern, the two failure modes
described in dimension 11 with the sharpest production impact. A latency
distribution for an endpoint that grows non-linearly with the size of a
user's data, an API call count metric that scales with the number of rows
in a result set rather than staying constant, or a database query count per
request that climbs with a specific input parameter, are all measurable
signals a metrics and tracing setup exposes, and an application performance
monitoring tool such as those built on OpenTelemetry can attribute the extra
query volume to the specific line inside the loop issuing it, once
distributed tracing spans are attached to each individual query call.

Memory and garbage collection signals apply to the eager pipeline failure
mode from dimension 11. A rising allocation rate and more frequent minor
garbage collection pauses, visible in a JVM's GC logs or in a Node.js
process's heap statistics, correlated with a specific request pattern that
exercises a chain of eagerly materialising collection operations, points
back to the intermediate-collection cost described in dimension 7, and is
the concrete evidence needed before deciding to fuse a pipeline back into a
loop as described in dimension 14's path out.

## 17. Security and privacy implications

The loop smell has a narrower security surface than most structural
patterns, but it is not silent, and two implications are worth naming
plainly rather than being invented for completeness.

A loop that performs a per-element side effect, a write, a network call, an
authorization check, mixed together with an unrelated filtering or
aggregation concern in the same pass, makes it easy for a later maintainer
editing the filtering logic to accidentally also change which elements
receive the side effect, without intending to. When that side effect is a
permission check, for example a loop filtering a list of records for display
that also happens to be the only place enforcing that a user may only see
their own records, disentangling the display filter from the security check
by extracting them into two separately named and separately tested
predicates, per the refactoring path in dimension 14, removes a real class of
authorization bug where an edit to the display logic silently weakens the
access control that happened to be riding along inside the same loop.

The N plus 1 query pattern named as a failure mode in dimension 11 has a
privacy adjacent implication in systems with row-level access control
implemented at the query layer, a database view, a row-level security
policy, or an ORM level filter. A loop that issues N separate per-row
queries instead of one batched query bypasses whatever batch-level access
control logic might exist at the point where a single combined query would
have been constructed, depending on how that access control is implemented,
and reviewing whether each of the N individual queries independently
re-applies the access check, rather than assuming a batched equivalent would
have, is worth doing explicitly rather than assuming the per-row form is
equivalent in every respect to the batched form it replaces.

Beyond these two, the smell itself, a loop mixing concerns, has no direct
data handling implication of its own, the security exposure lives in what
the loop's body actually does, not in the fact that it is a loop rather than
a pipeline.

## 18. References

1. Martin Fowler and Kent Beck, *Refactoring, Improving the Design of
   Existing Code*, Addison-Wesley, 1999, chapter 3, the original smell
   catalog including Duplicated Code, Long Method, and Feature Envy.
2. Martin Fowler, *Refactoring, Improving the Design of Existing Code*, 2nd
   edition, Addison-Wesley, 2018, the edition adding the Replace Loop with
   Pipeline refactoring and its accompanying reasoning about pipeline
   readability.
3. refactoring.com catalog, "Replace Loop with Pipeline",
   [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
   verified 2026-08-02, title confirmed present in the catalog listing.
4. Robert C. Martin, *Clean Code, A Handbook of Agile Software Craftsmanship*,
   Prentice Hall, 2008, chapter 3, "Functions", the rule that blocks inside
   `if`, `else`, and loop statements should reduce to a single, well-named
   function call.
5. A static-analysis vendor rule catalog previously cited here for the
   "loops should not contain more than a single break or continue statement"
   rule (SonarSource rule S135) has gone offline; the domain no longer
   resolves and no live or archived replacement was found, so this specific
   citation is removed rather than left pointing at a dead link.
6. Jeff Moden, "Hidden RBAR, Triangular Joins", SQL Server Central,
   [https://www.sqlservercentral.com/articles/hidden-rbar-triangular-joins](https://www.sqlservercentral.com/articles/hidden-rbar-triangular-joins),
   verified 2026-08-02, definition and coinage of "Row By Agonizing Row"
   confirmed present in the article's opening.
7. Oracle, `java.util.stream` package summary, Java SE 8 API documentation,
   [https://docs.oracle.com/javase/8/docs/api/java/util/stream/package-summary.html](https://docs.oracle.com/javase/8/docs/api/java/util/stream/package-summary.html),
   verified 2026-08-02, quoted description sentence confirmed present.
8. Microsoft Learn, "Language Integrated Query (LINQ) - C#",
   [https://learn.microsoft.com/en-us/dotnet/csharp/programming-guide/concepts/linq/](https://learn.microsoft.com/en-us/dotnet/csharp/programming-guide/concepts/linq/),
   verified 2026-08-02, quoted description sentences confirmed present.
9. Python Software Foundation, `itertools` module documentation, Python 3
   standard library reference,
   [https://docs.python.org/3/library/itertools.html](https://docs.python.org/3/library/itertools.html),
   verified 2026-08-02, quoted opening description confirmed present.
10. The Rust Programming Language, "Comparing Performance, Loops vs.
    Iterators", chapter 13.4,
    [https://doc.rust-lang.org/book/ch13-04-performance.html](https://doc.rust-lang.org/book/ch13-04-performance.html),
    verified 2026-08-02, quoted sentence on iterators as a zero-cost
    abstraction confirmed present.
11. PEP 8, "Style Guide for Python Code", the section recommending
    comprehensions over `filter` and `map` calls with lambda arguments,
    engineering guidance from the language's own style guide rather than an
    empirical claim, cited as the source of the recommendation rather than
    as proof of a universal readability fact.

## Code examples

Each example shows the same tiny order-processing case in the smell shape
first, then in the fixed shape, so the two can be compared line for line.
The before function mixes a filter, a sum, and a second filter-and-project
in one pass with a shared mutable accumulator, and the after functions split
those three jobs into three named operations. All three samples below were
compiled and run on this machine and produced the expected output.

Python. Run with `python3 loop_smell.py`. Verified output, `python ok (2000, [2]) 2000 [2]`.

```python
def totals_and_flags(orders):
    total = 0
    flagged = []
    for order in orders:
        if order["status"] == "paid":
            total += order["amount"]
            if order["amount"] > 1000:
                flagged.append(order["id"])
    return total, flagged


def paid_total(orders):
    return sum(o["amount"] for o in orders if o["status"] == "paid")


def large_paid_ids(orders):
    return [o["id"] for o in orders if o["status"] == "paid" and o["amount"] > 1000]


if __name__ == "__main__":
    data = [
        {"id": 1, "status": "paid", "amount": 500},
        {"id": 2, "status": "paid", "amount": 1500},
        {"id": 3, "status": "pending", "amount": 2000},
    ]
    assert totals_and_flags(data) == (2000, [2])
    assert paid_total(data) == 2000
    assert large_paid_ids(data) == [2]
    print("python ok", totals_and_flags(data), paid_total(data), large_paid_ids(data))
```

TypeScript. Compiled with `npx tsc --target es2020 --module commonjs --strict loop_smell.ts` (TypeScript 7.0.2) and run with `node loop_smell.js`. Verified output, `typescript ok 2000 [ 2 ] 2000 [ 2 ]`.

```typescript
type Order = { id: number; status: string; amount: number };

function totalsAndFlags(orders: Order[]): [number, number[]] {
  let total = 0;
  const flagged: number[] = [];
  for (const order of orders) {
    if (order.status === "paid") {
      total += order.amount;
      if (order.amount > 1000) {
        flagged.push(order.id);
      }
    }
  }
  return [total, flagged];
}

function paidTotal(orders: Order[]): number {
  return orders
    .filter((o) => o.status === "paid")
    .reduce((sum, o) => sum + o.amount, 0);
}

function largePaidIds(orders: Order[]): number[] {
  return orders
    .filter((o) => o.status === "paid" && o.amount > 1000)
    .map((o) => o.id);
}

const data: Order[] = [
  { id: 1, status: "paid", amount: 500 },
  { id: 2, status: "paid", amount: 1500 },
  { id: 3, status: "pending", amount: 2000 },
];

const [total, flagged] = totalsAndFlags(data);
if (total !== 2000 || flagged.length !== 1 || flagged[0] !== 2) {
  throw new Error("totalsAndFlags mismatch");
}
if (paidTotal(data) !== 2000) {
  throw new Error("paidTotal mismatch");
}
const ids = largePaidIds(data);
if (ids.length !== 1 || ids[0] !== 2) {
  throw new Error("largePaidIds mismatch");
}
console.log("typescript ok", total, flagged, paidTotal(data), ids);
```

Rust. Compiled with `rustc -O src/main.rs` (rustc 1.97.1) and run directly. Verified output, `rust ok 2000 [2] 2000 [2]`.

```rust
struct Order {
    id: u32,
    status: &'static str,
    amount: i64,
}

fn totals_and_flags(orders: &[Order]) -> (i64, Vec<u32>) {
    let mut total = 0;
    let mut flagged = Vec::new();
    for order in orders {
        if order.status == "paid" {
            total += order.amount;
            if order.amount > 1000 {
                flagged.push(order.id);
            }
        }
    }
    (total, flagged)
}

fn paid_total(orders: &[Order]) -> i64 {
    orders
        .iter()
        .filter(|o| o.status == "paid")
        .map(|o| o.amount)
        .sum()
}

fn large_paid_ids(orders: &[Order]) -> Vec<u32> {
    orders
        .iter()
        .filter(|o| o.status == "paid" && o.amount > 1000)
        .map(|o| o.id)
        .collect()
}

fn main() {
    let data = vec![
        Order { id: 1, status: "paid", amount: 500 },
        Order { id: 2, status: "paid", amount: 1500 },
        Order { id: 3, status: "pending", amount: 2000 },
    ];

    let (total, flagged) = totals_and_flags(&data);
    assert_eq!(total, 2000);
    assert_eq!(flagged, vec![2]);
    assert_eq!(paid_total(&data), 2000);
    assert_eq!(large_paid_ids(&data), vec![2]);
    println!("rust ok {} {:?} {} {:?}", total, flagged, paid_total(&data), large_paid_ids(&data));
}
```

Java and Kotlin are omitted here because neither `javac` nor a JVM was
available on the machine used to author this entry, and a sample presented
as compiled without actually compiling it would violate the verification
standard this repository holds every claim to. Dimension 9 already covers
the Java Stream API's own documented purpose and its role in the same
loop-to-pipeline transformation, so the concept is grounded there even
though no Java sample is compiled in this section.
