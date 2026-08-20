---
name: Split Variable
slug: split-variable
family: 03-refactoring
category: Refactoring
aliases: [Split Temp, Split Temporary Variable, Remove Assignments to Parameters]
first_described: "Fowler 1999"
maturity: canonical
related: [rename-variable, extract-variable, inline-variable, replace-derived-variable-with-query, split-loop, slide-statements, extract-function]
incompatible_with: []
verified: 2026-08-02
---

# Split Variable

## 1. Name, aliases, and lineage

The canonical name is **Split Variable**. Martin Fowler's online refactoring
catalog lists the refactoring under that name, with **Remove Assignments to
Parameters** and **Split Temp** as aliases
(https://refactoring.com/catalog/splitVariable.html, verified 2026-08-02).
Fowler's article on changes in the second edition says the first edition entry
**Split Temporary Variable** was replaced by **Split Variable**, and that
**Remove Assignments to Parameters** was also replaced by Split Variable
(https://martinfowler.com/articles/refactoring-2nd-changes.html, verified
2026-08-02).

The book lineage is Martin Fowler, *Refactoring. Improving the Design of
Existing Code*, 1st edition, Addison-Wesley, 1999, chapter 6, "Composing
Methods", sections "Split Temporary Variable" and "Remove Assignments to
Parameters"; and Martin Fowler, *Refactoring. Improving the Design of Existing
Code*, 2nd edition, Addison-Wesley, 2018, chapter 9, "Organizing Data", section
"Split Variable". The page location for the second edition section is page 240,
confirmed from the published table of contents shown by Schweitzer Online
(https://www.schweitzer-online.de/ebook/Fowler/Refactoring/9780134757698/A50710241/,
verified 2026-08-02). The wording and examples in this entry are original.

The word **variable** is broader than **temporary variable**. In older catalogs,
the common target was a local temporary whose value was overwritten halfway
through a function. In modern code, the same problem appears in parameters,
fields, captured closure variables, module variables, and test fixture members.
The common defect is not locality. The defect is one storage name carrying more
than one meaning during a reader's pass through the code.

The inverse refactoring is **Merge Variable**, which appears in RefactoringMiner
as a supported API-change refactoring beside Split Variable
(https://github.com/tsantalis/RefactoringMiner, verified 2026-08-02). Merge
Variable can be useful after two variables have converged to the same meaning.
Split Variable is used when the old single variable hides separate meanings.

## 2. Problem and context

A variable is assigned once, used for one idea, then assigned again and used for
a different idea. The program may be correct, but a reader has to ask a question
at every use: which lifetime of this name am I seeing? That question is a tax on
review, debugging, extraction, and tool support.

The simplest example is a `temp` variable used first for perimeter and later for
area. Fowler's catalog page shows that before and after shape
(https://refactoring.com/catalog/splitVariable.html, verified 2026-08-02). The
same shape appears in less toy-like code:

```
let value = request.query.limit;
value = Number(value);
value = Math.min(value, plan.maxRows);
return value;
```

The name `value` moves through three meanings. First it is untrusted text from
the request, then a parsed number, then a policy-bounded row count. When an
incident report says "value was wrong", the code gives no clue about which
meaning failed. Split Variable gives each stage a name:

```
const requestedLimit = request.query.limit;
const parsedLimit = Number(requestedLimit);
const allowedLimit = Math.min(parsedLimit, plan.maxRows);
return allowedLimit;
```

The context that makes the refactoring useful has four parts.

- The variable has at least two non-overlapping lifetimes, or the later uses can
  be separated by meaning.
- Each lifetime has a name that says more than the old variable name.
- The split can be made without changing externally visible behaviour.
- The surrounding code is valuable enough that lowering ambiguity is worth the
  extra names.

The refactoring is small, but it often opens the door to larger changes. Once
separate names mark separate concepts, Slide Statements can gather each concept
near the statements that compute it, and Extract Function can move a paragraph
out with fewer parameters. That relationship is engineering judgement. The cited
Fowler lineage establishes the refactoring name and its aliases, not this
entry's advice about sequencing local edits.

There is a second context worth naming because it appears in mature systems:
code that has been made correct by a sequence of small fixes. A request handler
starts with a query parameter, one patch adds trimming, another adds parsing, a
third adds tenant limits, and a fourth adds telemetry. Each patch reuses the
same local name because that is the least risky edit at the time. Months later,
the variable no longer has a single story. Split Variable is a low-risk way to
make that history visible without redesigning the handler in one pass.

The refactoring also fits code that has drifted across type boundaries. Static
languages may hide this drift behind broad types such as `Object`, `any`, or an
interface that is too wide. Dynamic languages allow it by default. The smell is
not "dynamic typing is bad"; the smell is that one name makes several stages
look like the same value. When the stages are named, the code often reveals a
natural data pipeline: raw bytes, decoded text, parsed structure, validated
command, persisted record. That pipeline may later become explicit modules, but
the variable split is the first cheap statement of the boundary.

## 3. Forces

This dimension is engineering judgement unless a sentence cites a named source.

**Readability versus compactness.** Split Variable favours readability. The code
gets more declarations, but each declaration carries a more exact name. Compact
code is better when the old name has one meaning. Compact code is worse when a
reader has to remember that the name changed identity at line 19.

**Mutation versus immutability.** Split Variable favours immutability. After the
split, each new variable can often be `const`, `final`, `let` without later
assignment, or a language equivalent. Fowler's catalog page illustrates a
mutable `temp` becoming two `const` declarations
(https://refactoring.com/catalog/splitVariable.html, verified 2026-08-02).

**Cognitive load versus name count.** The pattern lowers the mental load of
tracking a name through assignments, but it raises the number of identifiers in
scope. The trade is good when the names are concepts. It is poor when the new
names are mechanical labels such as `value1` and `value2`.

**Extraction cost versus local edit cost.** A reused variable can block Extract
Function because the extracted code needs the variable before and after its
reassignment. Splitting the variable can make the future extraction smaller.
This is a local edit paid now to make the next move cheaper.

**Latency.** Usually neutral. Splitting a local variable does not create a heap
object in mainstream compiled and bytecode languages. It can change timing if
the original reassignment avoided a second expensive call and the split repeats
that call. The refactoring should preserve the old evaluation count unless the
change is intentionally paired with Extract Variable or Replace Temp with Query.

**Consistency.** Favoured. A variable with one responsibility has fewer
opportunities for a later statement to read a value from the wrong phase.

**Operability.** Mildly favoured. Logs, trace attributes, and debugger watches
become clearer when they can name `rawLimit`, `parsedLimit`, and
`boundedLimit` rather than a single changing `limit`.

**Team topology.** Favoured in shared modules. Different teams often touch the
same long method for different reasons. A split variable marks the boundary
between concerns inside the method before larger ownership boundaries exist.

**Cost of change.** Favoured for near-term edits that alter one phase of a
calculation. Sacrificed when the method is so small that more names create more
surface area than the next change needs.

**Review precision.** Favoured. Review comments become tied to one stage of the
calculation. "The bounded limit should use the plan limit" is clearer than "the
second assignment to `limit` is wrong". That precision matters in asynchronous
review because the reviewer cannot point to a live debugger session.

**Diff size versus future diff safety.** Sacrificed in the immediate commit. A
split touches every read of the old variable, so the diff can look larger than
the behaviour change. Favoured in later commits, because a future edit to one
stage should touch fewer lines and has less chance of colliding with unrelated
work in the same method.

**Static analysis.** Favoured. Def-use chains, type narrowing, null analysis,
and unused-variable checks tend to produce better findings when a name is not
rebound to unrelated values. This is judgement about tool behaviour in general;
tool-specific claims require a named tool citation, such as the RefactoringMiner
source in dimensions 8 and 9.

## 4. Applicability and non-applicability

Reach for Split Variable when the following hold.

- A local variable is assigned more than once, and the later assignment is not a
  loop counter, accumulator, builder, or cache refresh.
- A parameter is reassigned to represent a normalized or corrected value, while
  later code still needs the original argument for logging, validation, or error
  reporting.
- A field is used as a staging slot for different phases of a calculation, and
  each phase can be moved toward a smaller scope.
- A method cannot be extracted cleanly because one variable crosses the desired
  boundary with two meanings.
- A debugger watch or log line keeps misleading people because a name has
  changed meaning by the time it is observed.
- A type change is hidden by a permissive language. For example, a Python name
  holds text, then a number, then a validated domain object.
- A code review comment says "rename this variable", but there is no single
  honest name because the variable is serving multiple roles.

Do NOT reach for Split Variable in these cases.

- **The variable is a true accumulator.** A running total, string builder,
  buffer, hash map being filled, or collection being appended to is meant to be
  updated. Splitting it would hide the accumulation.
- **The variable is a loop control variable.** `i`, `index`, iterator state, and
  cursor variables change by design. Split them only when the same name is later
  reused outside the loop for a different concept.
- **The reassignment is a cache refresh.** A field holding the current snapshot
  may be assigned again when the snapshot is invalidated. The right question is
  cache ownership, not variable splitting.
- **The new names would be fake precision.** `resultBefore`, `resultAfter`, and
  `resultFinal` are often worse than one `result`. If the concepts cannot be
  named, the code may need Extract Function or Substitute Algorithm first.
- **The split changes evaluation order.** If computing the new variables moves a
  function call earlier or later, the edit is no longer a pure Split Variable.
  Use tests to pin the old behaviour before making that larger change.
- **The variable carries a resource that must be reassigned.** Handles, locks,
  transaction objects, and stream references often have lifetime rules. Splitting
  them without changing cleanup code can leak or double close.
- **The language idiom already gives a clearer expression.** Pattern matching,
  destructuring, and pipeline operators can make stages explicit without adding
  extra names.
- **The code is generated.** Generated code often optimizes for stable output,
  not human naming. Change the generator if humans maintain the result.
- **The method is being deleted.** Do not polish a variable in code scheduled for
  Remove Dead Code unless the split is needed to verify the deletion.

## 5. Structure

Split Variable has fewer participants than an object design pattern, but the
roles are still distinct.

- **Overloaded variable.** The original name whose assignments carry more than
  one meaning. It is the subject of the refactoring.
- **Meaning segment.** A contiguous span of code where the old variable had one
  responsibility. A segment begins at declaration or assignment and ends before
  the next reassignment that changes meaning.
- **Replacement variable.** A new name for one meaning segment. It should be
  declared as close as practical to its first use and made immutable where the
  language allows it.
- **Boundary assignment.** The statement where the old variable changes meaning.
  It is the edit point. After the refactoring, this statement either becomes a
  declaration for a new variable or disappears because the replacement variable
  receives the expression directly.
- **Remaining readers.** Every read of the old variable. Each read must be
  assigned to exactly one replacement variable before the old variable can be
  removed.

The refactoring preserves data flow. It changes names and scopes, not the value
computed at each program point. A good split makes def-use chains shorter: the
reader of `parsedLimit` can look upward to one declaration, while the reader of
`rawLimit` does not have to cross a later normalization assignment.

The safest mechanical order is first segment to last segment. Rename the
declaration and reads in the first segment. Stop at the next assignment. Turn
that next assignment into a declaration for the next name. Test. Repeat until no
assignment changes the role of a variable. This staging matches the mechanics
summarized in Fowler's second edition section, where the public catalog and
change article identify Split Variable and its aliases
(https://refactoring.com/catalog/splitVariable.html, verified 2026-08-02;
https://martinfowler.com/articles/refactoring-2nd-changes.html, verified
2026-08-02).

## 6. ASCII structure diagram

```
Before

  +------------------- function -------------------+
  |                                                |
  |  x = expression for meaning A                  |
  |  read x as meaning A                           |
  |                                                |
  |  x = expression for meaning B                  |
  |  read x as meaning B                           |
  |                                                |
  |  x = expression for meaning C                  |
  |  read x as meaning C                           |
  |                                                |
  +------------------------------------------------+
            one name, three responsibilities

After

  +------------------- function -------------------+
  |                                                |
  |  a = expression for meaning A                  |
  |  read a as meaning A                           |
  |                                                |
  |  b = expression for meaning B                  |
  |  read b as meaning B                           |
  |                                                |
  |  c = expression for meaning C                  |
  |  read c as meaning C                           |
  |                                                |
  +------------------------------------------------+
            one name per responsibility
```

## 7. Dynamics

Runtime dynamics are simple because the refactoring is internal to one scope.
The observable result should not change. The mental dynamics change a lot:
instead of a name being rebound to a new role, each role receives its own name.

```
Before

  time  statement                         variable table
  ----  --------------------------------  ----------------------------
  t1    value = readQuery("limit")        value = raw text
  t2    log(value)                        value means raw text
  t3    value = parseInt(value)           value = parsed number
  t4    check(value)                      value means parsed number
  t5    value = min(value, plan.maxRows)  value = bounded number
  t6    return value                      value means bounded number

After

  time  statement                         variable table
  ----  --------------------------------  ----------------------------
  t1    rawLimit = readQuery("limit")     rawLimit = raw text
  t2    log(rawLimit)                     rawLimit still raw text
  t3    parsedLimit = parseInt(rawLimit)  parsedLimit = parsed number
  t4    check(parsedLimit)                parsedLimit still parsed
  t5    boundedLimit = min(...)           boundedLimit = bounded number
  t6    return boundedLimit               final meaning is explicit
```

The dynamic check is equivalence at each old read. At every line that used to
read the overloaded variable, the new variable must contain the value the old
variable held at that point. If a read crosses a reassignment, that read belongs
to the later replacement variable, not the earlier one. If a language has
closures, note whether the closure captures by reference or by value. In
JavaScript, a closure over a `let` variable sees later reassignments; a closure
over a new `const` sees the split value. That can be a feature or a behaviour
change, so test it directly.

## 8. Implementation variants

**Local temporary split.** A mutable local is replaced by two or more local
declarations. This is the most common form and the one shown on Fowler's catalog
page (https://refactoring.com/catalog/splitVariable.html, verified
2026-08-02). Prefer immutable declarations for the new names.

**Parameter split.** A reassigned parameter is left untouched, and a local
variable receives the changed value. The original argument keeps its meaning.
This is the shape formerly described as Remove Assignments to Parameters in the
first edition lineage, later folded into Split Variable according to Fowler's
second edition change article
(https://martinfowler.com/articles/refactoring-2nd-changes.html, verified
2026-08-02).

**Type-phase split.** A dynamically typed name is split when its runtime type
changes. `payload` might become `payloadText`, then `payloadJson`, then
`payloadCommand`. The split is valuable even if the language permits the
mutation, because the type transition is part of the reader's model.

**Validation-phase split.** External input becomes parsed input, then validated
domain data. The split makes trust boundaries visible. This variant is common in
request handlers and command-line parsers.

**Scope-narrowing split.** A field or outer-scope variable is copied into a
local variable for a calculation paragraph, then the resulting update is written
back at one point. Emily Bache's Samman Coaching refactoring note describes an
extended form that includes splitting a class or global variable into a smaller
scope (https://sammancoaching.org/refactorings/split_variable.html, verified
2026-08-02). This entry treats that as a useful extension, not as the narrow
Fowler core.

**Declaration-initializer split.** IDEs also use "split variable declaration" to
mean separating `int x = f();` into `int x; x = f();`. Eclipse JDT Language
Server added code actions for "Join/Split variable" in release 1.26.0
(https://github.com/eclipse-jdtls/eclipse.jdt.ls/blob/main/CHANGELOG.md,
verified 2026-08-02). install4j 11 lists "Split variable declaration" and
"Join variable declaration" in its Java script editor refactoring popup
(https://www.ej-technologies.com/install4j/whatsnew10, verified 2026-08-02).
That IDE action is related but narrower. It changes declaration shape, not
necessarily responsibility. Use it as a helper, not as a substitute for naming
each meaning.

**Refactoring-miner detection.** RefactoringMiner treats Split Variable as a
detectable API-change refactoring in its supported list
(https://github.com/tsantalis/RefactoringMiner, verified 2026-08-02). The
RefactoringMiner 2.0 paper describes split-variable detection in terms of a
deleted source variable and newly added target variables, matched through
statement replacements in the old and new scopes
(https://www.researchgate.net/publication/342799123_RefactoringMiner_20,
verified 2026-08-02). That variant matters for history analysis, code review
bots, and migration reports.

**Branch-local split.** A variable is assigned before a conditional, then
rewritten inside one branch to mean "adjusted for that branch". Split the
branch-specific value into a name local to the branch, and keep the outer value
unchanged. This prevents one branch from changing the meaning seen by code after
the conditional. If both branches produce a common final value, give that final
value its own name after the conditional rather than mutating the original input
inside each branch.

**Error-path split.** A name is reused after an exception or error check to hold
fallback data. This is risky because the happy path and fallback path often have
different trust levels. Use separate names for the happy-path value and the
fallback value, then introduce a final selected value at the merge point. The
result reads like a decision rather than a mutation.

**Ownership split.** In Rust, Go, C, and C++, one name can blur the difference
between an owning handle and a borrowed or derived view. The refactoring is not
only cosmetic there. A split can make lifetime and cleanup rules visible: one
name owns the resource, another name is a derived value that must not close it.
This variant should be paired with compiler checks, linters, or resource tests,
because a wrong split can change lifetime behaviour.

## 9. Known production uses

**Info-ZIP Zip, `zip.c` large-file work.** The `ds-zip` mirror of Info-ZIP's
CHANGES file records an October 2004 change for version 3.0c: variable `t` in
`zip.c` was split into `t` with type `off_t` and `tf` with type `ulg`
(https://github.com/dspace-group/ds-zip/blob/master/CHANGES, verified
2026-08-02). This is a named production codebase and a named source file. The
source describes the concrete variable split. It does not claim Fowler's
refactoring name, so treating it as Split Variable is engineering judgement
based on the edit shape.

**Eclipse JDT Language Server.** Eclipse JDT LS 1.26.0, released July 27, 2023,
added code actions for "Join/Split variable" in its changelog
(https://github.com/eclipse-jdtls/eclipse.jdt.ls/blob/main/CHANGELOG.md,
verified 2026-08-02). The project site for the same release repeats that
feature (https://projects.eclipse.org/projects/eclipse.jdt.ls/releases/1.26.0,
verified 2026-08-02). This is production use as an editor service that exposes a
split-variable transformation to Java users.

**install4j Java script editor.** install4j 11 lists "Split variable
declaration" and "Join variable declaration" in the refactoring popup for its
Java editor (https://www.ej-technologies.com/install4j/whatsnew10, verified
2026-08-02). This is production use as a shipped developer tool. It is the
declaration-initializer variant from dimension 8, so it should not be
overstated as responsibility splitting in every invocation.

**RefactoringMiner.** RefactoringMiner is a Java library and API for detecting
refactorings in project history, and its supported API-change list includes
Split Variable (https://github.com/tsantalis/RefactoringMiner, verified
2026-08-02). The RefactoringMiner 2.0 paper describes detection rules for split
variables and says the extended oracle includes commits from 185 open-source
GitHub-hosted projects (https://www.researchgate.net/publication/342799123_RefactoringMiner_20,
verified 2026-08-02). This is production use in analysis tooling rather than an
application refactoring performed by hand.

## 10. Consequences

Positive.

- Each name has one role, so reviews can discuss the concept rather than a
  mutable slot.
- The new variables can often be immutable, which makes accidental later writes
  a compile-time or lint-time failure.
- Extract Function becomes easier because each candidate paragraph depends on
  fewer changing locals.
- Error messages and logs can name the stage that failed, such as raw input,
  parsed input, validated input, or bounded input.
- Static analysis and refactoring tools have cleaner def-use chains to inspect.
- A later Rename Variable has a smaller target because each name covers a
  shorter lifetime.

Negative.

- More names enter the scope. Poor names can make the function longer without
  making it clearer.
- A careless split can change behaviour by moving evaluation, changing closure
  capture, or breaking resource cleanup.
- Readers may infer that each new variable is a business concept even when one
  is only a mechanical intermediate.
- A sequence of split variables can expose that the method is doing too much,
  which is accurate but may require a larger follow-up refactoring.
- In languages with manual memory management, a split involving ownership can
  make lifetime rules more visible but also more demanding.

The net consequence is not "more variables are better". The better rule is one
name per stable meaning, and no name for a value that does not deserve a
concept.

## 11. Failure modes and misuse

This dimension is engineering judgement.

**Symptom.** A log line prints `value`, and the incident team cannot tell
whether it is raw text, parsed data, or validated data. **Cause.** The same
variable name carried all three stages. **Fix.** Split the variable by trust
stage and log the stage-specific name.

**Symptom.** A test starts failing after a split because a function with side
effects is now called earlier. **Cause.** The edit combined Split Variable with
reordering. **Fix.** Restore the old order first. Then make any order change as
a separate refactoring with its own test.

**Symptom.** A closure sees the old final value before the split and an earlier
value after the split. **Cause.** The closure now captures one replacement
variable instead of the reassigned original. **Fix.** Decide which value the
closure should capture, then write the capture explicitly and add a regression
test.

**Symptom.** A resource is closed twice or not closed at all after a variable is
split. **Cause.** The old variable represented ownership transfer, not only a
computed value. **Fix.** Split ownership and borrowed views explicitly, and keep
cleanup attached to the owning name.

**Symptom.** The new names are `result1`, `result2`, and `result3`, and reviews
are no clearer. **Cause.** The refactoring was applied mechanically without
finding the meanings. **Fix.** Pause the split, identify the domain words, or
use Extract Function to give the paragraph a name instead.

**Symptom.** A field split creates two fields that must always be updated
together. **Cause.** The old field was a compound value rather than an
overloaded variable. **Fix.** Replace the field with a small value object, or
use Change Reference to Value if identity is not needed.

**Symptom.** Performance drops because a value that used to be computed once is
computed once per branch. **Cause.** The split duplicated the expression instead
of naming the old value at the same program point. **Fix.** Keep one declaration
for the expensive result, then split only the meanings that differ after it.

**Symptom.** A linter reports shadowing after the split. **Cause.** A new name
was declared in an inner scope with the same name as an outer concept. **Fix.**
Rename one side, or narrow the outer scope so no shadow remains.

## 12. Trade-off matrix

<table>
  <thead>
    <tr>
      <th>Force</th>
      <th>Split Variable</th>
      <th>Rename Variable</th>
      <th>Extract Variable</th>
      <th>Inline Variable</th>
      <th>Replace Derived Variable with Query</th>
      <th>Extract Function</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Readability</td>
      <td>High when meanings differ.</td>
      <td>High when one meaning has a poor name.</td>
      <td>High when an expression lacks a name.</td>
      <td>High when a name adds no value.</td>
      <td>High when stored data duplicates a calculation.</td>
      <td>High when a paragraph deserves a name.</td>
    </tr>
    <tr>
      <td>Mutation control</td>
      <td>Strong. New names can be immutable.</td>
      <td>Neutral. Assignment count stays the same.</td>
      <td>Strong if extracted as immutable.</td>
      <td>Strong only by removing the slot.</td>
      <td>Strong. Updates disappear.</td>
      <td>Mixed. Locals move across a boundary.</td>
    </tr>
    <tr>
      <td>Cognitive load</td>
      <td>Lower def-use tracking, higher name count.</td>
      <td>Lower if the old name was misleading.</td>
      <td>Lower expression parsing, higher name count.</td>
      <td>Lower name count, higher expression parsing.</td>
      <td>Lower state tracking, higher call tracing.</td>
      <td>Lower local detail, higher call graph tracing.</td>
    </tr>
    <tr>
      <td>Latency</td>
      <td>Neutral if evaluation count is preserved.</td>
      <td>Neutral.</td>
      <td>May reduce repeated evaluation.</td>
      <td>May increase repeated evaluation.</td>
      <td>May recompute unless cached elsewhere.</td>
      <td>Usually neutral, with call overhead possible.</td>
    </tr>
    <tr>
      <td>Operability</td>
      <td>Better stage names in logs and watches.</td>
      <td>Better only if the one name improves.</td>
      <td>Better expression names.</td>
      <td>Worse when logs lose a named stage.</td>
      <td>Better source of truth, less stored state.</td>
      <td>Better trace and stack names.</td>
    </tr>
    <tr>
      <td>Best trigger</td>
      <td>One name, multiple meanings.</td>
      <td>One meaning, wrong name.</td>
      <td>Unnamed expression.</td>
      <td>Pointless intermediate name.</td>
      <td>Stored value duplicates other state.</td>
      <td>Paragraph has a purpose.</td>
    </tr>
  </tbody>
</table>

Read the matrix by first diagnosing the smell. If the name is wrong, rename it.
If the expression is dense, extract it. If the value is derived state, replace
it with a query. Split Variable is the answer only when one storage location
has more than one meaning.

## 13. Related and incompatible patterns

**Rename Variable.** Often follows Split Variable. The first split may use
obvious temporary names to keep the edit safe. A second pass sharpens the names
after the data flow is visible.

**Extract Variable.** Often precedes Split Variable when a later assignment is a
large expression. Extract the expression so it has a name, then split the
overloaded variable that used to receive it.

**Inline Variable.** The inverse pressure. If a split produces a name that is
read once and says no more than its expression, Inline Variable removes it.

**Replace Derived Variable with Query.** A follow-up when one of the split names
is derived from other local or object state. Fowler's second edition table of
contents places Split Variable in chapter 9 before Replace Derived Variable
with Query (https://www.schweitzer-online.de/ebook/Fowler/Refactoring/9780134757698/A50710241/,
verified 2026-08-02). The practical sequence is often split first, then remove
the derived slot.

**Split Loop.** Related when an accumulator is doing two jobs inside one loop.
Do not split a true accumulator into fake stages. Split the loop when separate
passes express separate results.

**Slide Statements.** Composes well. After a split, statements that compute one
replacement variable can often be moved together, leaving a cleaner paragraph.

**Extract Function.** A common target after the split. The new names mark the
inputs and output of the paragraph to extract.

**Merge Variable.** Incompatible when applied to the same code for the same
reason. Use Merge Variable only when two variables have converged to the same
meaning and the duplication is noise.

**Introduce Parameter Object.** A substitute when the split reveals that several
new variables always travel together. Do not leave six split locals when they
are really one domain value.

## 14. Refactoring path in and out

Introducing Split Variable.

1. Find a variable with more than one assignment.
2. Classify each assignment. Mark true accumulators, loop counters, cache
   refreshes, and resource ownership changes as special cases before editing.
3. Identify the first meaning segment: declaration or assignment through the
   read before the next role-changing assignment.
4. Rename that declaration and its reads to a concept name.
5. Stop before the next role-changing assignment. Turn that assignment into a
   declaration for the next concept name.
6. Make the new variable immutable where the language allows it.
7. Run the narrow test for the function or module.
8. Repeat segment by segment until the overloaded name is gone.
9. Slide each declaration toward its first use if that keeps the scope smaller.
10. Consider Extract Function only after the split has made data flow clear.

Detailed staging for a high-risk function.

1. Add a characterization test around the current function. If the function is
   hard to call directly, test at the nearest public boundary and capture the
   visible result.
2. Record the assignments to the overloaded variable in a short note or review
   comment. For each assignment, write the meaning in domain words.
3. Change only the first segment. Do not edit formatting, order statements, or
   simplify expressions in the same step.
4. Run the narrow test. If it fails, the defect is inside that one segment.
5. Commit or checkpoint the passing state if the function is large.
6. Continue with the next segment. The goal is a series of small, reversible
   edits rather than one broad rewrite.
7. After all segments pass, remove the old variable. If the old name remains,
   there is still at least one read whose meaning has not been classified.
8. Run the broader test set for the owning module because local variable changes
   can still alter closure capture, evaluation order, or cleanup timing.

The same method works for parameters, with one extra rule. Keep the original
parameter name only if it names the incoming value. For example, a function
receiving `rawLimit` should not reassign that parameter to the parsed value.
If the public API already calls it `limit`, decide whether callers think of it
as raw input or domain input. Then name the first local accordingly.

Refactoring out.

1. Look for replacement variables whose names have become aliases for the same
   concept.
2. Inline single-use names that repeat their expression and do not help logging
   or debugging.
3. Merge variables only when their lifetimes overlap and they carry the same
   meaning.
4. If the replacements always move together, create a value object or parameter
   object and pass that instead of several names.
5. If a query can calculate the value from existing state, use Replace Derived
   Variable with Query and delete the stored variable.

The removal path should be as disciplined as the introduction path. It is
common for a split to be correct during a cleanup branch and then become
unneeded after Extract Function. When that happens, deleting the extra names is
not backsliding. The test is whether the reader still benefits from seeing the
intermediate stage. If the extracted function name already says the same thing,
the local variable may have served its purpose.

The out path matters because Split Variable is a working step as well as an end
state. During a refactoring session, you may split names to make the code
legible, then inline or move half of them after the larger design emerges.

## 15. Testing and verification

This dimension is engineering judgement.

The main test is behavioural equivalence. Every public result, mutation, thrown
error, and emitted event should match the old code. Because Split Variable is
small, the best verification is often a narrow unit test around the function
plus a direct read-through of the diff.

Useful techniques.

- **Golden input-output cases.** Feed representative inputs through the function
  before and after the split. This catches reassignment mistakes.
- **Boundary cases.** Include empty input, zero, null or none, maximum values,
  invalid input, and values that cross a validation boundary.
- **Property tests.** When the function is arithmetic or parsing heavy, compare
  old and new implementations over many generated inputs during the refactoring
  branch, then delete the duplicate old function after trust is established.
- **Mutation or coverage check.** Make sure each branch that reads each new
  variable has test coverage. A split can look correct while one stale read
  still points at the wrong name.
- **Log snapshot check.** If observability changes are part of the refactoring,
  assert that log fields contain the new stage names without leaking sensitive
  raw input.
- **Compiler and linter checks.** In TypeScript, Java, Go, Rust, Swift, and
  similar languages, changing new names to immutable declarations lets the
  compiler catch later accidental writes.

What became easier. The code can be tested around smaller concepts. A failing
assertion points to `validatedLimit` or `rawLimit`, not to a changing `limit`.
Extract Function tests become easier because the extracted function has fewer
mutable locals crossing its boundary.

What became harder. If the language allows shadowing, tests may not catch a
reader accidentally bound to the wrong name unless the values differ in the test
case. Choose test data where each meaning has a visibly different value.

Review checklist.

- Does every new name describe a value at one stage, not an operation that
  happened to produce it?
- Does every old read now point to the replacement variable that has the same
  value at that program point?
- Did any expression move across a conditional, exception handler, loop, or
  resource boundary?
- Did any closure capture a different variable than before?
- Can any new variable be made immutable?
- Are raw or sensitive stages kept out of logs?
- Did the edit leave behind a variable whose name no longer matches its meaning?

For arithmetic code, compare intermediate values directly during the refactoring
branch. For parsing and validation code, use test data where the raw value,
parsed value, normalized value, and final value are visibly different. For
resource code, add a test that counts opens and closes or that uses a fake
resource failing on double close. Those tests are more useful than broad
snapshot tests because they target the risks that Split Variable can introduce.

The code examples below were run locally with `npx tsc` plus `node`,
`python3`, and `go run`. Java was attempted, but this environment reported no
Java runtime, so Java is omitted from the verified examples.

### TypeScript

```typescript
type Plan = { maxRows: number };

function pageSize(rawLimit: string, plan: Plan): number {
  const requestedLimit = rawLimit.trim();
  const parsedLimit = Number.parseInt(requestedLimit, 10);
  const fallbackLimit = Number.isFinite(parsedLimit) ? parsedLimit : 25;
  const boundedLimit = Math.min(Math.max(fallbackLimit, 1), plan.maxRows);
  return boundedLimit;
}

console.log(pageSize(" 120 ", { maxRows: 100 }));
console.log(pageSize("nope", { maxRows: 100 }));
```

### Python

```python
def page_size(raw_limit: str, max_rows: int) -> int:
    requested_limit = raw_limit.strip()
    try:
        parsed_limit = int(requested_limit)
    except ValueError:
        parsed_limit = 25
    bounded_limit = min(max(parsed_limit, 1), max_rows)
    return bounded_limit


if __name__ == "__main__":
    print(page_size(" 120 ", 100))
    print(page_size("nope", 100))
```

### Go

```go
package main

import (
    "fmt"
    "strconv"
    "strings"
)

func pageSize(rawLimit string, maxRows int) int {
    requestedLimit := strings.TrimSpace(rawLimit)
    parsedLimit, err := strconv.Atoi(requestedLimit)
    if err != nil {
        parsedLimit = 25
    }
    boundedLimit := min(max(parsedLimit, 1), maxRows)
    return boundedLimit
}

func main() {
    fmt.Println(pageSize(" 120 ", 100))
    fmt.Println(pageSize("nope", 100))
}
```

## 16. Observability signals

This dimension is engineering judgement.

Split Variable usually has no direct production signal because it is an
internal code-shape refactoring. The signal appears when the new names are used
to label logs, traces, counters, and debugger output.

Record these when the variable crosses a trust or validation boundary.

- A trace attribute for the stage, such as `limit.stage = parsed`, rather than
  one mutable `limit` field changing over time.
- A validation error field naming the failing stage, such as `raw_limit_invalid`
  or `bounded_limit_exceeded`.
- A counter for fallback paths, labelled by reason. For example,
  `page_size_fallback_total{reason="parse_error"}`.
- A debug log that records derived safe values, not raw sensitive input.
- A metric for unexpected coercions, such as strings that parse to `NaN`, empty
  user input, or values clipped by policy.

A healthy instance has stable ratios. Parse failures stay within expected
traffic patterns. Bounds clipping rises when a customer sends larger requests,
and drops after client fixes. Debug logs use the new names consistently.

A failing instance has one of these shapes. Parse failures spike after a client
release. The bounded value is always equal to the maximum, suggesting a bad
default or abuse. A raw value appears in a log field meant for a safe value. Or
two stages report the same label, which means the observability did not follow
the split.

The refactoring can also improve debugger work. In a watch window, three stable
names are easier to inspect than one name whose meaning depends on the current
line. That is operational value even when no metric changes.

## 17. Security and privacy implications

This dimension is engineering judgement.

Split Variable is mostly security-neutral when it only renames locals inside a
pure calculation. It becomes security-relevant when the old variable crossed a
trust boundary. A single name such as `email`, `path`, `amount`, or `token` can
hide the difference between raw external input, parsed data, normalized data,
validated data, and redacted data. Splitting the variable makes that boundary
visible:

```
rawEmail -> parsedEmail -> canonicalEmail -> redactedEmail
```

That visibility lowers three risks.

- Raw sensitive data is less likely to be logged under a safe-looking name.
- Validation checks are less likely to be applied to the wrong stage.
- Authorization decisions are less likely to read data before normalization.

It also adds two risks.

- More variables can mean more chances to log the wrong one. Name raw values
  with a `raw` prefix and review logs in the same change.
- A split can keep a sensitive raw value alive longer than before. Narrow the
  scope of raw values, and do not store them in object fields unless required.

For memory-safe languages, the privacy concern is retention and logging, not
pointer safety. For languages with manual memory management or explicit resource
ownership, splitting a variable that owns a handle must preserve exactly one
owner and exactly one cleanup path. Treat borrowed views and owning handles as
separate names.

## 18. References

1. Martin Fowler. *Refactoring. Improving the Design of Existing Code*. 1st
   edition. Addison-Wesley, 1999. Chapter 6, "Composing Methods", sections
   "Split Temporary Variable" and "Remove Assignments to Parameters". Source
   for first-edition lineage.
2. Martin Fowler. *Refactoring. Improving the Design of Existing Code*. 2nd
   edition. Addison-Wesley, 2018. Chapter 9, "Organizing Data", section "Split
   Variable". Section page 240 confirmed through Schweitzer Online table of
   contents,
   https://www.schweitzer-online.de/ebook/Fowler/Refactoring/9780134757698/A50710241/
   Verified 2026-08-02.
3. Martin Fowler. "Split Variable". Refactoring catalog.
   https://refactoring.com/catalog/splitVariable.html
   Verified 2026-08-02. Source for the canonical catalog name, aliases, and the
   perimeter and area example shape.
4. Martin Fowler. "Changes for the 2nd Edition of Refactoring".
   https://martinfowler.com/articles/refactoring-2nd-changes.html
   Verified 2026-08-02. Source for the replacement of Split Temporary Variable
   and Remove Assignments to Parameters by Split Variable.
5. Emily Bache. "Split Variable". Samman Coaching.
   https://sammancoaching.org/refactorings/split_variable.html
   Verified 2026-08-02. Source for the coaching-site extension to accumulators
   and smaller-scope variants.
6. Eclipse JDT Language Server maintainers. `CHANGELOG.md`, release 1.26.0.
   https://github.com/eclipse-jdtls/eclipse.jdt.ls/blob/main/CHANGELOG.md
   Verified 2026-08-02. Source for code actions for Join/Split variable.
7. Eclipse Foundation. "Eclipse JDT LS 1.26.0".
   https://projects.eclipse.org/projects/eclipse.jdt.ls/releases/1.26.0
   Verified 2026-08-02. Secondary source for the same JDT LS release feature and
   release date.
8. ej-technologies. "What's new in install4j 11".
   https://www.ej-technologies.com/install4j/whatsnew10
   Verified 2026-08-02. Source for the script editor listing Split variable
   declaration and Join variable declaration.
9. Info-ZIP maintainers, mirrored by dspace-group. `ds-zip` `CHANGES`.
   https://github.com/dspace-group/ds-zip/blob/master/CHANGES
   Verified 2026-08-02. Source for the production change splitting variable
   `t` in `zip.c` into `t` and `tf`.
10. Nikolaos Tsantalis and contributors. `RefactoringMiner` README.
    https://github.com/tsantalis/RefactoringMiner
    Verified 2026-08-02. Source for Split Variable in the supported
    API-change refactoring list.
11. Nikolaos Tsantalis, Ameya Ketkar, Danny Dig. "RefactoringMiner 2.0". IEEE
    Transactions on Software Engineering, 2020. ResearchGate mirror:
    https://www.researchgate.net/publication/342799123_RefactoringMiner_20
    Verified 2026-08-02. Source for split-variable detection rules and the
    oracle description covering 185 open-source GitHub-hosted projects.
