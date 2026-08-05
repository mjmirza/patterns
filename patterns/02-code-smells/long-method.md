---
name: Long Method
slug: long-method
family: 02-code-smells
category: Bloaters
aliases: [Long Function, Long Routine, God Function]
first_described: "Fowler, Beck, Brant, Opdyke, Roberts 1999, Refactoring, Improving the Design of Existing Code"
maturity: canonical
related: [large-class, feature-envy, comments, duplicate-code, dead-code, data-clumps]
incompatible_with: []
verified: 2026-08-02
---

# Long Method

## 1. Name, aliases, and lineage

The canonical name is Long Method. It is one of the original smells catalogued
in Martin Fowler, with Kent Beck, John Brant, William Opdyke, and Don Roberts,
*Refactoring, Improving the Design of Existing Code*, Addison-Wesley, 1999,
Chapter 3, "Bad Smells in Code", under the heading "Long Method". The book
pairs the smell with its primary cure, Extract Method, in the same chapter,
and treats the two as a matched diagnosis and treatment rather than as two
independent ideas. The second edition of the book, 2018, keeps the smell name
Long Method but renames the cure Extract Function to match the JavaScript
examples used throughout that edition. Fowler's own refactoring catalog site
lists Extract Method as an alias of Extract Function and states plainly that
Extract Function is the inverse of Inline Function, confirming that the two
names describe one operation across the two editions rather than two
different refactorings, source https://refactoring.com/catalog/extractFunction.html,
verified 2026-08-02.

Long Method sits in the informal family commonly labelled Bloaters in
secondary teaching sources and static analysis documentation, alongside
Large Class, Long Parameter List, Primitive Obsession, and Data Clumps. This
grouping is a widely used way of summarizing the catalogue rather than a
direct quotation from the book, and it is presented here as engineering
categorization, the same qualification the sibling entry for Large Class in
this repository makes about the same family label.

Language communities that favor free functions over methods, most visibly
JavaScript and Go, tend to say Long Function rather than Long Method, and the
tooling built for those languages reflects that wording directly. ESLint
ships a rule literally named `max-lines-per-function`, described in its own
documentation as a way to "enforce a maximum number of lines of code in a
function" because "large functions tend to do a lot of things and can make
it hard following what's going on", source
https://eslint.org/docs/latest/rules/max-lines-per-function, verified
2026-08-02. Steve McConnell, *Code Complete*, second edition, Microsoft
Press, 2004, Chapter 7, "High-Quality Routines", uses the word routine
throughout rather than method or function, because the chapter treats
procedures, functions, and methods as one category of unit for the purposes
of the length question it investigates, and Long Routine is the term that
appears in secondary discussion of that chapter. God Function is a smaller,
informally used alias that mirrors God Class, describing the extreme end of
the smell where one function has absorbed the responsibilities of an entire
subsystem. it is listed here as observed usage without an attributable
coining source, the same honesty standard the sibling Large Class entry
applies to Kitchen Sink Class and Swiss Army Knife Class.

The underlying diagnostic idea, that a unit of code with too many decision
paths is measurably harder to understand and more error prone, predates
Fowler's catalogue by more than two decades and has an independent, verified
lineage of its own. Thomas J. McCabe, "A Complexity Measure", IEEE
Transactions on Software Engineering, volume SE-2, number 4, pages 308 to
320, December 1976, defines cyclomatic complexity as a count of the linearly
independent paths through a routine's control flow graph, and proposes it as
a size and testability metric independent of raw line count. The paper's
existence and IEEE Transactions on Software Engineering venue is confirmed
by the digital object identifier resolving to IEEE Xplore document 1702388,
source https://doi.org/10.1109/TSE.1976.233837, verified 2026-08-02. McCabe's
metric is not Long Method itself. it is the most common quantitative proxy
practitioners reach for when they want to say precisely how tangled a long
method has become, and it is why static analysis tools frequently pair a
raw line count threshold with a cyclomatic complexity threshold rather than
relying on either measure alone.

## 2. Problem and context

A method starts small. It does one clear thing, and its name says what that
thing is. Then a bug fix adds a branch. A new requirement adds a loop around
the existing loop. A related calculation that seemed too small to deserve
its own method gets inlined rather than extracted, because extracting it
felt like more ceremony than the two lines were worth. None of these
individual additions looks unreasonable at the moment it is made. Months
later the method is four hundred lines long, its name still describes what
it did at fifty lines, and nobody can hold the whole thing in their head at
once while reading it top to bottom.

The observable symptom is almost always the same regardless of language or
codebase. a reader opens the method to answer one specific question, for
example whether a particular discount is applied before or after tax, and
has to scroll past unrelated setup code, unrelated error handling, and
unrelated logging before finding the three lines that actually answer the
question. The method has stopped being a unit of meaning and become a
container of steps that happen to execute in sequence. This context is what
distinguishes Long Method from a merely large but well organized method. a
method built from ten clearly named, well factored helper calls that
together read like a short story is not the smell, even if its own body is
thirty lines long, because the reader can understand it at the level of the
helper names without reading the helper bodies. The smell is present when
the length forces the reader down into implementation detail before they can
form any summary understanding of what the method accomplishes.

The problem compounds specifically inside change-heavy code, because a long
method is also a method with a large git blame surface. Every unrelated
change that happens to touch the same method collides in the diff, code
review has to re-examine logic nobody intended to change, and the odds that
two developers edit overlapping lines in the same sprint climb with the
method's size. Long Method is therefore not purely a readability concern. it
is a concurrency-of-editing concern that shows up as merge conflicts and
review friction well before anyone measures comprehension directly.

## 3. Forces

**Cohesion versus procedural convenience.** Keeping every step of a
multi-stage process in one method is procedurally convenient while writing
it the first time, because the author never has to name intermediate results
or decide where a helper belongs. That convenience is paid back, with
interest, by every future reader who did not write the method and has no
mental model of its stages already loaded.

**Local variable scope versus extraction friction.** A long method
accumulates local variables that many of its later steps depend on. Breaking
the method apart means deciding, for each step, whether that variable
becomes a parameter, a field, or the return value threaded through a chain
of calls. In a language with strong support for multiple return values or
records this friction is low. in a language where only one value can be
returned it is real friction, and it is the single most common reason
Extract Method stalls partway through in practice.

**Performance versus decomposition, mostly imagined.** Developers
sometimes resist splitting a long method because they believe the function
call overhead of ten small calls will be slower than one large block. In
almost every managed runtime this fear is unfounded for ordinary business
logic, because modern JIT compilers inline small, hot methods
automatically, and even in ahead of time compiled languages the call
overhead of a well predicted branch is a handful of nanoseconds against
work that is virtually always outweighed by I/O, allocation, or genuine
computation elsewhere. This force is real as a psychological brake on
refactoring even where it is not real as a measured cost, and it is worth
naming honestly as a force that favors staying long, whether or not the
underlying belief holds up under profiling.

**Debuggability versus stack depth.** A single long method gives a
debugger exactly one stack frame to step through in order, with every
variable visible in one scope at once. Splitting it into many small methods
means stepping in and out of frames, and losing the ability to see two
unrelated local variables side by side in the debugger's locals pane unless
they were threaded through as parameters. This is a genuine, not imagined,
cost of decomposition that experienced engineers weigh against the
readability gain, particularly for code that is debugged far more often than
it is read cold.

**Testability versus surface area.** A long method that does five things
can usually only be tested by asserting on its combined output, because
there is no seam to intercept the intermediate results of step three
without either mocking internals or duplicating the earlier steps in the
test. Extracting the five things into five methods multiplies the number of
testable units and shrinks the input space each unit test has to cover, at
the cost of writing and maintaining more test files.

## 4. Applicability and non-applicability

Reach for the Long Method diagnosis, and its cure, when the following hold.

- The method mixes more than one level of abstraction in its body, for
  example raw string parsing sitting directly beside a business rule about
  discount eligibility, so that a reader has to context switch between
  reading like a parser author and reading like a domain expert in the same
  paragraph of code.
- A reader cannot state, in one sentence, what the method does without
  using the word "and" more than once, for example "it validates the
  order, calculates the discount, applies tax, and writes the receipt."
- The method has grown past what its original name still accurately
  describes, so the name is now either misleadingly narrow or has been
  weakened into something vague like `processOrder` or `handleRequest`
  purely to keep pace with everything the body now does.
- Sections of the method are commented with a short label describing what
  the following block does, for example `// calculate shipping`, because
  the block itself is not self-explanatory at a glance. A same-purpose
  comment sitting directly above a block of code is one of Fowler's own
  named indicators for where an Extract Method boundary belongs, discussed
  further in dimension 14.
- Local variables are reused across genuinely distinct phases of the
  method for genuinely distinct purposes, which is itself evidence that the
  method is doing more than one job with one shared, overloaded scope.

Do not reach for it, and do not decompose further, in these cases, because
the cure would make the code worse rather than better.

- A method is long purely because it is a flat, sequential list of
  independent, already well named calls to other methods, each doing one
  clear thing, so that the body reads top to bottom like a table of
  contents. This is sometimes called a Composed Method, and splitting it
  further usually adds indirection without adding clarity, because the
  decomposition work has already happened at the call level.
- The logic genuinely has one job and is long only because that one job is
  irreducibly detailed, for example a state machine transition table or a
  parser for a fixed binary format where every branch corresponds to one
  real-world byte layout case that has no natural subgrouping. Splitting
  such a method along arbitrary line-count boundaries produces helper
  methods with meaningless names like `parsePart2`, which is worse than the
  long method it replaced.
- The method sits on a proven, extremely hot path where a profiler has
  measured that inlining matters, and the team has verified with real
  measurements, not assumption, that the compiler or runtime does not
  already inline the extracted pieces. This is rare in ordinary application
  code and common in specific domains such as codec implementations or
  physics engines, and it should be treated as the exception it is, with a
  comment recording the measurement that justified staying long.
- Splitting the method would require passing an unreasonable number of
  parameters between the pieces because the method's true state genuinely
  belongs together, in which case the correct move covered in dimension 14
  is Extract Class or Introduce Parameter Object first, so the pieces can
  be split apart with the state carried on an object rather than threaded
  through a growing parameter list.

## 5. Structure

Long Method does not have participants in the sense that a design pattern
does, because it is a smell describing the shape of a single unit of code
rather than a collaboration between named roles. The structure worth naming
is the internal shape a long method typically takes once it has grown past
readability, because that internal shape is exactly what the refactoring in
dimension 14 targets.

**The setup block.** The opening lines of the method, usually argument
validation, default value resolution, and the fetching or unwrapping of
whatever data the rest of the method will operate on.

**The stage sequence.** A run of two or more logically distinct phases,
often separated by a blank line or a comment, each of which reads and
writes a subset of the method's local variables and does not depend on
variables introduced by a later stage.

**The accumulator or result variable.** One or more local variables,
frequently declared near the top and mutated across several stages, that
carry the running result forward and are finally returned or written out
at the end.

**The exit paths.** Early returns, thrown exceptions, or continue and
break statements scattered through the stages, which is the structural
element most responsible for why a long method resists being cleanly cut
into pieces, because an early return in stage two has to become an early
return out of whatever new method stage two is extracted into, which then
has to be checked and propagated by the caller.

## 6. ASCII structure diagram

```
+-------------------------------------------------+
| processOrder(order)                              |
|                                                    |
|  setup block                                      |
|  +----------------------------------------------+ |
|  | validate order not null                       | |
|  | resolve customer record                        | |
|  +----------------------------------------------+ |
|                                                    |
|  stage 1: pricing                                 |
|  +----------------------------------------------+ |
|  | subtotal = sum(line items)                     | |
|  | discount = lookup discount rules               | |
|  +----------------------------------------------+ |
|              |  shares "subtotal", "discount"      |
|              v                                     |
|  stage 2: tax                                      |
|  +----------------------------------------------+ |
|  | taxRate = lookup by region                      | |
|  | total = (subtotal - discount) * (1 + taxRate)   | |
|  +----------------------------------------------+ |
|              |  shares "total"                     |
|              v                                     |
|  stage 3: persistence and side effects             |
|  +----------------------------------------------+ |
|  | write receipt row                               | |
|  | enqueue confirmation email                       | |
|  | log audit entry                                  | |
|  +----------------------------------------------+ |
|                                                    |
|  return total                                      |
+-------------------------------------------------+
```

## 7. Dynamics

At runtime a long method executes exactly the same instructions whether or
not it has ever been split. the smell has no runtime signature of its own,
which is part of why it is easy to leave unfixed. it costs nothing at
execution time and everything at comprehension time. The dynamics worth
tracing are therefore the reader's dynamics, the order in which a human has
to build a mental model while stepping through the source, and how that
compares once the method has been decomposed.

```
Reading a long method, cold
  read setup ---> hold state in head ---> read stage 1
       ---> extend state in head ---> read stage 2
       ---> extend state in head, forget some of stage 1
       ---> read stage 3 ---> now uncertain whether stage 1's
            discount value is still what stage 3 assumes it is

Reading the extracted version, cold
  read processOrder() body, five calls, each named
       ---> form summary understanding in one pass
       ---> only descend into calculatePricing() if that
            specific question is the one being answered
```

The second path is strictly cheaper in working memory, because each named
call defers the reader's need to hold that stage's internal variables in
mind until the reader chooses to descend into it. This is the same
principle behind progressive disclosure in user interface design, applied
to source code, and it is the direct, mechanical reason Extract Method
improves comprehension speed independent of any change in the underlying
logic.

## 8. Implementation variants

**Extract Method or Extract Function, the direct cure.** Select a
coherent group of statements inside the long method, give it a name that
states its intent rather than its implementation, and replace the
statements with a call to the new method. Fowler's refactoring catalog
site presents Extract Function this way and states it as the inverse of
Inline Function, source https://refactoring.com/catalog/extractFunction.html,
verified 2026-08-02. This is the baseline variant every other variant below
is a special case of.

**Replace Temp with Query.** Where the long method builds a local
variable purely to hold a value computed once and read several times, that
computation is turned into its own method call and the temp variable is
removed. This variant matters specifically because a lingering temp
variable is frequently the thing that makes an otherwise clean block hard
to extract, since extraction would otherwise have to pass the temp back out
as a return value threaded through several stages.

**Introduce Parameter Object, then extract.** Where several stages of the
long method share three or more related pieces of state, for example a
street, a city, and a postal code passed together everywhere, the shared
state is first collected into one object, and only then are the stages
extracted, each now taking the one object as a parameter instead of three
or four loose primitives. This ordering matters. attempting to extract
first, before consolidating the shared state, produces new methods with
long parameter lists, which is itself the sibling smell Long Parameter
List and simply relocates the problem rather than solving it.

**Decompose Conditional.** Where a long method's length comes from a large
if or switch statement rather than a sequence of stages, each branch's body
is extracted into its own method named after the condition it satisfies,
so the outer structure reads as a dispatch table over clearly named
outcomes instead of a wall of inline logic.

**Replace Method with Method Object, the escape valve for entangled
state.** When a method's local variables are so deeply threaded through
every stage that ordinary extraction would require passing five or six
parameters between the new pieces, the entire method is turned into its own
small class. the method's parameters become the class's constructor
arguments, its local variables become fields, and each formerly inline
stage becomes a private method on that class reading and writing shared
fields instead of passed parameters. This variant exists precisely for the
case that dimension 4 flags as a non-applicability trap for plain Extract
Method, and it is the variant Fowler's own book reaches for when a method
resists ordinary decomposition.

**Language-shaped variants.** In languages with first class functions,
part of a long method's body is sometimes extracted not into a named
top-level method but into a local closure, which keeps the extracted
logic's scope tightly bound to the enclosing method while still giving the
reader a named seam to skip past, a shape that reads naturally in
JavaScript, Python, Go, and Swift and less naturally in Java before local
classes and lambdas became idiomatic for this purpose.

## 9. Known production uses

Long Method is unusual among the smells in this catalogue in that its
production use is not one famous codebase telling the story of a
refactor. it is the mainstream static analysis and style-enforcement
tooling that entire language toolchains ship as a default, checked-in
guardrail against the smell recurring at scale.

Checkstyle, the long-standing Java source code style checker, ships a
`MethodLength` check whose own documentation states it "checks for long
methods and constructors" because "if a method becomes very long it is
hard to understand", with a default maximum of 150 lines, configurable via
a `max` property, source
https://checkstyle.sourceforge.io/checks/sizes/methodlength.html, verified
2026-08-02.

PMD, the other widely used Java static analysis tool, ships an `NcssCount`
rule that measures method and class size using the Non-Commenting Source
Statements metric rather than a raw physical line count, and flags methods
past 60 NCSS lines and classes past 1500 by default, in order to "identify
excessively long methods that should be refactored into smaller, more
maintainable components", source
https://docs.pmd-code.org/latest/pmd_rules_java_design.html, verified
2026-08-02. PMD's choice of a statement count rather than a physical line
count is itself an acknowledgment that Long Method is about
density of logic, not about how the source happens to be wrapped onto
lines.

ESLint, the most widely used JavaScript and TypeScript linter, ships a
`max-lines-per-function` rule with the stated purpose to "enforce a
maximum number of lines of code in a function" because "large functions
tend to do a lot of things and can make it hard following what's going
on", with a default limit of 50 lines, source
https://eslint.org/docs/latest/rules/max-lines-per-function, verified
2026-08-02.

The Linux kernel's own coding style document instructs contributors
directly, in prose rather than through an automated tool, that "functions
should be short and sweet, and do one thing", should "fit on one or
two screenfuls of text", and separately caps the practical number of local
variables a function should carry at 5 to 10 "or you're doing something
wrong", explicitly reasoning that "the human brain can generally easily
keep track of about 7 different things, anything more and it gets
confused", source https://www.kernel.org/doc/html/latest/process/coding-style.html,
Chapter 6, "Functions", verified 2026-08-02. This matters as a
production use because the Linux kernel is C, a language with none of the
object-oriented method concept the smell's name implies, which demonstrates
that the underlying problem, and the discipline against it, generalizes
past the object-oriented context Fowler's book was written in.

## 10. Consequences

**Positive, from applying Extract Method to a long method.** Each
extracted piece becomes independently readable, independently testable,
and independently reusable if the same logic is ever needed elsewhere.
Names replace the need to read implementation detail to understand intent,
so a reader can build a correct mental model of the whole method by reading
only the sequence of call names, a benefit dimension 7 traces directly.
Diffs shrink and narrow. a change to the tax calculation stage only
touches the tax calculation method, so code review and git blame both
narrow to the actually relevant lines instead of surfacing an entire
four-hundred-line method as changed. The seams created by extraction are
also the seams unit tests need, so testability increases as a direct side
effect rather than as separate additional work, discussed further in
dimension 15.

**Negative, from applying Extract Method carelessly or in excess.**
Extraction performed purely to satisfy a line-count linter, without regard
for whether the resulting pieces are coherent, produces methods with names
like `doStep2` or `helperA` that carry no more meaning than a comment
would have, while adding an extra level of indirection the reader now has
to jump through. This is a real and common failure mode, not a hypothetical
one, and it is the reason dimension 4's non-applicability list matters as
much as the applicability list. Over-decomposition also increases the
number of files or scroll positions a reader has to visit to answer one
question, trading the original problem, too much to read in one place, for
a milder but still real version of the same problem, too much to move
between spread across many places. In performance sensitive code, discussed
under forces in dimension 3, aggressive extraction without profiling can
introduce real, measurable slowdowns in languages or runtimes where the
compiler does not reliably inline the extracted calls, though this is the
less common failure mode of the two by a wide margin in ordinary
application code.

## 11. Failure modes and misuse

**Symptom.** A code review repeatedly gets stuck on one function because
reviewers keep finding themselves scrolling back up to remember what a
variable near the top was set to.
**Cause.** The function mixes an early setup stage with a much later stage
that depends on a variable from setup, and the distance between the write
and the read exceeds what a reader can hold across a screen or two of
scrolling.
**Fix.** Extract the setup stage into its own method with a name that
states the invariant it establishes, so the later stage's dependency on
that invariant is expressed by the call itself rather than by the reader
remembering a specific line.

**Symptom.** A bug fix to one part of a long method causes an unrelated
part of the same method to silently produce wrong output, discovered only
by a later regression test.
**Cause.** Two unrelated stages share a mutable local variable, often
because the variable was reused for a second purpose to avoid declaring a
new one, and the fix mutated it in a way the other stage did not expect.
**Fix.** Give each stage its own clearly scoped variable rather than reusing
one, then extract each stage so the compiler or interpreter enforces the
separation through method scope instead of relying on discipline alone.

**Symptom.** After a refactoring pass, the method is technically shorter
but the codebase now has ten new private methods, each called from exactly
one place, each with a name like `helper1` through `helper10`, and the
original method now reads as a sequence of calls to those names in order.
**Cause.** Extraction was performed mechanically to satisfy a line-count
threshold in a linter without asking whether each extracted piece had a
coherent, nameable responsibility of its own.
**Fix.** Reconsider extraction boundaries around what the code does rather
than around a fixed number of lines, per the guidance in dimension 14, and
rename each helper for its intent, or inline it back if no honest intent
name exists.

**Symptom.** A method that used to be one stack frame in the debugger is
now eight, and diagnosing a production incident under time pressure takes
noticeably longer because the engineer has to step in and out of six
one-line pass-through methods before reaching the line that actually
matters.
**Cause.** Extraction was applied uniformly without regard for the
debuggability force named in dimension 3, splitting even trivial,
non-repeated, single-caller code purely for the sake of shortening the
outer method.
**Fix.** Reserve extraction for stages that genuinely earn a name of their
own, and accept that a short, linear sequence of truly trivial steps with
no independent meaning can stay inline, per the Composed Method exception
in dimension 4.

**Symptom.** Two extracted methods both take the same four parameters in a
slightly different order, and a caller passes them in the wrong order,
producing a bug that compiles cleanly in a weakly or loosely typed
language.
**Cause.** The shared state that used to live in one method's local scope
was extracted as loose, individually passed parameters instead of being
consolidated first, exactly the ordering trap named in dimension 8 under
Introduce Parameter Object.
**Fix.** Consolidate the shared state into one object or record before
extracting further, so the parameter becomes one clearly typed value
instead of several same-typed values whose order can be silently swapped.

## 12. Trade-off matrix

| Approach | Readability at a glance | Debuggability | Testability | Risk of over-decomposition | Setup cost |
|---|---|---|---|---|---|
| Leave the method long | Low, reader must read the whole body to summarize it | High, one stack frame holds all state | Low, only the combined output is assertable | None, there is nothing to over-decompose | None |
| Extract Method into named helpers | High, body reads as a sequence of intents | Medium, state now spans several frames | High, each helper is independently testable | Medium, mechanical extraction can produce meaningless helper names | Low to medium, mostly deciding what to name each piece |
| Replace Method with Method Object | High, and resolves entangled shared state cleanly | Medium, fields replace scattered locals in one debugger watch pane | High, fields and methods on the object are directly assertable | Low, the class boundary forces a coherent grouping decision up front | Higher, a new class and its construction have to be introduced |
| Decompose Conditional | High for branch-heavy methods specifically | Medium, each branch body is its own frame | High, each branch becomes independently testable | Low if branches already correspond to real named outcomes | Low, branches usually already have a natural name |

Large Class is the closest named alternative worth comparing directly,
because a long method that keeps growing and starts accumulating its own
private helper methods and its own private state is frequently the start of
a future Large Class. the two smells sit on the same growth trajectory at
different scales, method versus class, and the same underlying force,
accumulated, unextracted responsibility, drives both.

## 13. Related and incompatible patterns

**Large Class**, covered elsewhere in this family, is Long Method's sibling
at the class scale. a class that repeatedly grows new long methods, and
whose long methods repeatedly grow new private fields to hold their working
state, is a Large Class in the making. fixing Long Method early, before its
private state migrates up into class fields purely to shorten the method
signature, is one of the more reliable ways to prevent Large Class from
forming in the first place.

**Feature Envy**, another entry in this family, often appears inside a
long method as one of its stages, specifically a block that reaches deeply
into another object's data to perform a calculation that arguably belongs
on that other object rather than here. Extracting that block as a first
step frequently reveals it should not merely become a local private
method, but should move entirely onto the object it envies, which is a
distinct refactoring, Move Method, layered on top of the initial Extract
Method step.

**Duplicate Code**, also in this family, is commonly discovered as a side
effect of decomposing a long method, because two long methods that were
never compared side by side while they were long turn out, once broken
into named stages, to share an identically shaped stage that had simply
never been noticed as duplication before extraction gave it a name to
match against.

**Comments**, the smell covering comments used to compensate for unclear
code, is directly related, because a same-purpose comment sitting above a
block inside a long method is one of the strongest available signals for
exactly where an extraction boundary belongs, discussed in dimension 14.

**Single Responsibility Principle**, from Robert C. Martin's writing on
object-oriented design principles, is the class-level design principle
Long Method violates at the method level. a method that has more than one
reason to change, because it mixes concerns that evolve independently of
each other, is a Long Method candidate whether or not it has crossed any
particular line count.

Long Method is not incompatible with any named pattern in the sense of
actively conflicting with one, because it is a smell rather than a
structural choice. the closest thing to an incompatibility is with
genuinely irreducible, single-purpose long routines discussed in
dimension 4, where applying Extract Method aggressively would itself
introduce the Comments smell in reverse, meaningless helper names standing
in for what a comment would have said more honestly.

## 14. Refactoring path in and out

**Refactoring out, the common direction.** Fowler's own primary heuristic
for finding extraction boundaries inside a long method is to look for
comments, because a comment explaining what a block of code does is a sign
that the block itself is not communicating that intent on its own, and the
extracted method's name can frequently be built directly from the comment's
wording, after which the comment itself becomes unnecessary and is deleted.
The mechanical steps are consistent across languages. identify a
self-contained sequence of statements, note which local variables it reads
that were set before it and which local variables it writes that are used
after it, declare a new method taking the former as parameters and
returning the latter, replace the original statements with a call to the
new method, then compile or run the test suite before moving on to the
next candidate block. Where the block writes to more than one variable
used later, either the new method returns a small tuple or record, or, if
this pattern recurs across several extractions from the same original
method, the shared state is consolidated first via Introduce Parameter
Object, then the pieces are pulled out taking and returning that one
consolidated value, per the ordering guidance in dimension 8. Where local
variables are so numerous and so entangled across stages that this ordering
still produces unwieldy parameter lists, the escape valve is Replace Method
with Method Object, also covered in dimension 8, converting the entire
original method into a small class whose fields replace the tangled locals.

**Refactoring in, the rarer direction.** A method should be recombined,
via Inline Function or Inline Method, when a previous extraction produced a
piece that is called from exactly one place, adds no independent
understanding beyond what its own name already conveys at the call site,
and whose body a reader would have to open anyway to answer any real
question about the calling method's behavior. This is the direct mirror of
the over-decomposition failure mode named in dimension 11, and it is worth
performing deliberately rather than leaving as accumulated debris, because
a codebase with many single-caller, thin helper methods slows down finding
things for every future reader in a way that is easy to accumulate
gradually and easy to miss without a deliberate pass looking for it.

## 15. Testing and verification

A long method is hard to unit test in the strict sense,
because there is no seam between its internal stages for a test to target,
so tests can only assert on the method's final combined output, which
means the number of test cases needed to cover every combination of
internal branches grows multiplicatively with the number of
stages rather than additively. Once a method is decomposed, each extracted
piece can be tested in isolation with a small, focused input space, and the
outer method's own test suite shrinks to verifying that the pieces are
called in the correct order with the correct data, which is usually a
handful of integration-style cases rather than an exhaustive combinatorial
set.

The practical verification technique for confirming that an extraction was
behavior-preserving, rather than accidentally behavior-changing, is
characterization testing. before touching the long method, write a small
set of tests that capture its current output for a representative set of
inputs, including edge cases the method handles, run those tests to
confirm they pass against the unmodified method, then perform the
extraction and re-run the identical tests without modification. A passing
run after the extraction is direct evidence the refactoring changed the
method's internal structure without changing its externally observable
behavior, which is the entire point of a refactoring as distinct from a
rewrite. Where the long method under test currently has no tests at all,
writing this characterization suite first, before any extraction, is not
optional preparatory work, it is the actual safety net the refactoring
depends on, and skipping it converts what should be a low-risk mechanical
transformation into a high-risk rewrite performed under the reassuring
disguise of a refactoring.

Where a language and toolchain support it, an automated Extract Method
refactoring tool, such as the ones built into modern IDEs for Java,
TypeScript, C#, and several other languages, performs the parameter and
return value analysis mechanically and is generally more reliable at
catching a variable dependency the human eye missed than a manual
extraction, and using the automated tool where one exists is worth
preferring over hand extraction specifically because it removes one entire
class of the failure mode named in dimension 11 involving accidentally
shared mutable state.

## 16. Observability signals

Long Method itself produces no runtime telemetry, because it describes a
property of the source code rather than a property of a running system,
so the observability signals worth tracking are static analysis metrics
gathered at build or review time rather than production metrics gathered
at runtime.

A healthy signal looks like a stable or slowly declining distribution of
method line counts and cyclomatic complexity scores across a codebase over
time, gathered by running the same static analysis tool, such as the
Checkstyle or PMD rules named in dimension 9, on every build and tracking
the trend rather than only the pass or fail state of a fixed threshold.
Tracking the trend catches slow drift, a codebase where the average method
length creeps upward release over release even though no single method
ever crosses the configured line threshold in one commit, which a
pass or fail gate alone will never surface.

A failing signal looks like a small number of methods that repeatedly
reappear at the top of a churn-weighted complexity report, meaning they are
both long or complex and frequently modified, because that combination is
the strongest available predictor that a method is both hard to change
correctly and being changed often, which is exactly the situation dimension
2 describes as the core cost of the smell. Some teams build this
churn-weighted view directly by joining static complexity output against
version control history, surfacing the file and method combinations where
both numbers are simultaneously high, and treating that intersection, not
either metric alone, as the prioritized refactoring backlog.

## 17. Security and privacy implications

Long Method has a modest but real security implication, distinct from the
readability and maintainability concerns covered elsewhere in this entry.
a long method that mixes authorization checks with business logic and data
access in one undifferentiated block makes it materially easier for a
reviewer, or for the original author under time pressure, to miss that a
particular code path added later in the method's life bypasses an
authorization check performed earlier in the same method, because the
check and the sensitive operation it is meant to guard are separated by
unrelated intervening logic rather than sitting next to each other in a
small, clearly named unit. Extracting the authorization check into its own
named method that is called immediately before the sensitive operation,
rather than once at the top of a long combined method, shortens the visual
distance between the guard and the thing it guards, and makes it easier
for a static analysis tool, or a human reviewer, to verify that every path
to the sensitive operation actually passes through the guard.

There is no direct data privacy implication specific to method length
itself. long methods handling personal data are not on their own more or
less exposed than short ones. the relevant privacy risk in that case
belongs to whatever the method does with the data, not to how many lines
the method happens to occupy, and it would be inaccurate to claim a
stronger connection than that.

## 18. References

1. Martin Fowler, with Kent Beck, John Brant, William Opdyke, Don Roberts,
   *Refactoring, Improving the Design of Existing Code*, Addison-Wesley,
   1999, Chapter 3, "Bad Smells in Code", section "Long Method".
2. Martin Fowler, Kent Beck, *Refactoring, Improving the Design of
   Existing Code*, second edition, Addison-Wesley, 2018, catalogue entries
   "Long Function" and "Extract Function".
3. refactoring.com catalog, "Extract Function", alias Extract Method,
   stated as the inverse of Inline Function.
   https://refactoring.com/catalog/extractFunction.html, verified
   2026-08-02.
4. Thomas J. McCabe, "A Complexity Measure", IEEE Transactions on
   Software Engineering, volume SE-2, number 4, pages 308 to 320,
   December 1976. Existence and venue confirmed via DOI resolution.
   https://doi.org/10.1109/TSE.1976.233837, verified 2026-08-02.
5. Steve McConnell, *Code Complete*, second edition, Microsoft Press,
   2004, Chapter 7, "High-Quality Routines".
6. Checkstyle documentation, "MethodLength" check, default maximum 150
   lines. https://checkstyle.sourceforge.io/checks/sizes/methodlength.html,
   verified 2026-08-02.
7. PMD documentation, "NcssCount" rule, Java design rules, default
   thresholds 60 lines for methods and 1500 for classes.
   https://docs.pmd-code.org/latest/pmd_rules_java_design.html, verified
   2026-08-02.
8. ESLint documentation, "max-lines-per-function" rule, default limit 50
   lines. https://eslint.org/docs/latest/rules/max-lines-per-function,
   verified 2026-08-02.
9. Linux kernel documentation, "Linux kernel coding style", Chapter 6,
   "Functions", guidance on function length and local variable count.
   https://www.kernel.org/doc/html/latest/process/coding-style.html,
   verified 2026-08-02.
10. Arthur J. Riel, *Object-Oriented Design Heuristics*, Addison-Wesley,
    1996, heuristic on naming as a symptom of accumulated responsibility,
    cited here for the parallel structural reasoning it shares with Long
    Method at the class scale, discussed under Large Class in this
    repository's companion entry.

## Code examples

Three languages are shown. TypeScript and Python because a long method in a
loosely typed language most visibly demonstrates the entangled local state
problem named in dimension 3, and Go because its lack of exceptions and
strict multiple-return-value support show the extraction pattern in a
language shaped very differently from the first two. Every sample below was
compiled or run against a real toolchain before being included, and the
exact commands are given after each block.

### TypeScript, before and after

```typescript
// Before: one long method mixing four stages and two accumulators.
interface LineItem { price: number; qty: number; }
interface Order { region: string; items: LineItem[]; discountCode?: string; }

function processOrderLong(order: Order): number {
  if (!order || order.items.length === 0) {
    throw new Error("order must have at least one item");
  }
  let subtotal = 0;
  for (const item of order.items) {
    subtotal += item.price * item.qty;
  }
  let discount = 0;
  if (order.discountCode === "SAVE10") {
    discount = subtotal * 0.10;
  } else if (order.discountCode === "SAVE20") {
    discount = subtotal * 0.20;
  }
  const rateByRegion: Record<string, number> = { US: 0.08, EU: 0.20, UK: 0.20 };
  const taxRate = rateByRegion[order.region] ?? 0.0;
  const taxable = subtotal - discount;
  const total = taxable + taxable * taxRate;
  console.log(`order total for region ${order.region}: ${total}`);
  return total;
}

// After: each stage extracted, the outer method reads as a summary.
function calculateSubtotal(items: LineItem[]): number {
  return items.reduce((sum, item) => sum + item.price * item.qty, 0);
}

function calculateDiscount(subtotal: number, code?: string): number {
  if (code === "SAVE10") return subtotal * 0.10;
  if (code === "SAVE20") return subtotal * 0.20;
  return 0;
}

function taxRateFor(region: string): number {
  const rateByRegion: Record<string, number> = { US: 0.08, EU: 0.20, UK: 0.20 };
  return rateByRegion[region] ?? 0.0;
}

function processOrder(order: Order): number {
  if (!order || order.items.length === 0) {
    throw new Error("order must have at least one item");
  }
  const subtotal = calculateSubtotal(order.items);
  const discount = calculateDiscount(subtotal, order.discountCode);
  const taxable = subtotal - discount;
  const total = taxable * (1 + taxRateFor(order.region));
  return total;
}

const sample: Order = {
  region: "EU",
  items: [{ price: 20, qty: 3 }, { price: 5, qty: 2 }],
  discountCode: "SAVE10",
};
console.log("long:", processOrderLong(sample));
console.log("extracted:", processOrder(sample));
```

Compiled and run with `npx tsc --noEmit long-method.ts` for type checking,
then `npx tsc long-method.ts --outDir /tmp/lm && node /tmp/lm/long-method.js`.
Both paths print the same total, confirming the extraction preserved
behavior, per the characterization testing approach in dimension 15.

### Python, before and after

```python
# Before: one long function mixing validation, parsing, and two calculations.
def summarize_report_long(raw_lines):
    if not raw_lines:
        raise ValueError("raw_lines must not be empty")
    records = []
    for line in raw_lines:
        parts = line.strip().split(",")
        if len(parts) != 2:
            continue
        name, value_str = parts
        try:
            value = float(value_str)
        except ValueError:
            continue
        records.append((name, value))
    total = 0.0
    for _name, value in records:
        total += value
    average = total / len(records) if records else 0.0
    highest = max(records, key=lambda r: r[1]) if records else None
    return {"total": total, "average": average, "highest": highest}


# After: each stage extracted, the outer function reads as a summary.
def parse_records(raw_lines):
    records = []
    for line in raw_lines:
        parts = line.strip().split(",")
        if len(parts) != 2:
            continue
        name, value_str = parts
        try:
            value = float(value_str)
        except ValueError:
            continue
        records.append((name, value))
    return records


def total_of(records):
    return sum(value for _name, value in records)


def average_of(records, total):
    return total / len(records) if records else 0.0


def highest_of(records):
    return max(records, key=lambda r: r[1]) if records else None


def summarize_report(raw_lines):
    if not raw_lines:
        raise ValueError("raw_lines must not be empty")
    records = parse_records(raw_lines)
    total = total_of(records)
    return {
        "total": total,
        "average": average_of(records, total),
        "highest": highest_of(records),
    }


if __name__ == "__main__":
    sample = ["apples,3.5", "pears,2.0", "garbage,line", "kiwis,4.25"]
    assert summarize_report_long(sample) == summarize_report(sample)
    print("long:", summarize_report_long(sample))
    print("extracted:", summarize_report(sample))
```

Run directly with `python3 long_method.py`. The assertion passes, confirming
the two versions produce identical output.

### Go, before and after

```go
package main

import "fmt"

// Before: one long function mixing lookup, aggregation, and formatting.
func buildInvoiceSummaryLong(prices map[string]float64, quantities map[string]int) (string, error) {
	if len(quantities) == 0 {
		return "", fmt.Errorf("quantities must not be empty")
	}
	var lineTotal float64
	var missing []string
	for name, qty := range quantities {
		price, ok := prices[name]
		if !ok {
			missing = append(missing, name)
			continue
		}
		lineTotal += price * float64(qty)
	}
	status := "complete"
	if len(missing) > 0 {
		status = "incomplete"
	}
	summary := fmt.Sprintf("total=%.2f status=%s missing=%v", lineTotal, status, missing)
	return summary, nil
}

// After: each stage extracted, the outer function reads as a summary.
func aggregate(prices map[string]float64, quantities map[string]int) (float64, []string) {
	var lineTotal float64
	var missing []string
	for name, qty := range quantities {
		price, ok := prices[name]
		if !ok {
			missing = append(missing, name)
			continue
		}
		lineTotal += price * float64(qty)
	}
	return lineTotal, missing
}

func statusFor(missing []string) string {
	if len(missing) > 0 {
		return "incomplete"
	}
	return "complete"
}

func buildInvoiceSummary(prices map[string]float64, quantities map[string]int) (string, error) {
	if len(quantities) == 0 {
		return "", fmt.Errorf("quantities must not be empty")
	}
	lineTotal, missing := aggregate(prices, quantities)
	summary := fmt.Sprintf("total=%.2f status=%s missing=%v", lineTotal, statusFor(missing), missing)
	return summary, nil
}

func main() {
	prices := map[string]float64{"apples": 3.5, "pears": 2.0}
	quantities := map[string]int{"apples": 2, "kiwis": 1}
	long, _ := buildInvoiceSummaryLong(prices, quantities)
	extracted, _ := buildInvoiceSummary(prices, quantities)
	fmt.Println("long:", long)
	fmt.Println("extracted:", extracted)
}
```

Run directly with `go run long_method.go`. Both branches print a total of
7.00 with status incomplete and the missing item kiwis listed, confirming
the extraction preserved behavior. Go's map iteration order is randomized
per run, which affects only the order of names inside the `missing` slice
here, not the total or the status, and a real test for this function would
sort `missing` before comparing rather than relying on iteration order, a
detail worth naming honestly rather than glossing over.
