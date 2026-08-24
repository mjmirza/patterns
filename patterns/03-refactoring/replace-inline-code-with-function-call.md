---
name: Replace Inline Code with Function Call
slug: replace-inline-code-with-function-call
family: 03-refactoring
category: Refactoring
aliases: [Replace Hand-Written Idiom with Function Call, Replace Manual Code with Library Call]
first_described: "Fowler 2018"
maturity: canonical
related: [extract-function, inline-function, substitute-algorithm, replace-loop-with-pipeline, slide-statements]
incompatible_with: []
verified: 2026-08-02
---

# Replace Inline Code with Function Call

## 1. Name, aliases, and lineage

The canonical name is **Replace Inline Code with Function Call**. Martin
Fowler introduced it as a new catalog entry in *Refactoring. Improving the
Design of Existing Code*, 2nd edition, Addison-Wesley, 2018, chapter 8,
"Moving Features," section 8.5. Fowler also published that the second
edition added this refactoring as one of fifteen catalog entries that were
new rather than renamed from the first edition
(https://martinfowler.com/articles/refactoring-2nd-changes.html, verified
2026-08-02).

The name is literal. A code region already performs behavior that has a
named function somewhere else. The refactoring replaces the local mechanics
with a call to the named function. The target function can be in the same
module, a sibling module, a standard library, or an external package.

Common aliases are **Replace Hand-Written Idiom with Function Call** and
**Replace Manual Code with Library Call**. Those aliases appear in review
conversation more often than in catalogs, especially when the target is a
standard library operation such as JavaScript `Array.prototype.includes`,
Python `any`, or Go `slices.Contains`. MDN documents `Array.prototype.includes`
as a method that reports whether an array contains a value
(https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/includes,
verified 2026-08-02). Python documents `any` as returning true when any
item in an iterable is true, and gives its loop equivalent
(https://docs.python.org/3/library/functions.html#any, verified
2026-08-02). Go documents `slices.Contains` as reporting whether a value is
present in a slice
(https://pkg.go.dev/slices#Contains, verified 2026-08-02).

This refactoring is not Extract Function. Extract Function creates the
target function first. Replace Inline Code with Function Call starts after
the target function exists, or after a library function is selected. This
refactoring is also not Inline Function. Inline Function removes a function
call and exposes the body. This refactoring moves in the opposite direction,
from local mechanics toward a named operation.

## 2. Problem and context

You have inline code that duplicates behavior already named elsewhere. The
code may be a small loop, a repeated validation block, a hand-written search,
a string parsing idiom, a date conversion, a retry wrapper, or a multi-step
normalization. The local code is correct today, but the same behavior now has
two homes. One home is the named function. The other is the inline block.

The context is ordinary maintenance work in a growing codebase. A team writes
a helper after seeing duplication in one area. Later a second reader notices
that a nearby caller still performs the same work inline. Or a language
release adds a library call that makes a prior hand-written idiom obsolete.
Or a migration creates a shared function in a platform package, while older
feature code still repeats the old sequence.

The risk is not only line count. The risk is semantic drift. Two blocks can
look similar and behave differently on edge cases. One loop may stop early
while another keeps scanning. One parser may trim whitespace before testing a
value while the other tests first. One membership check may treat `NaN` or
case folding differently. When the behavior is intended to be the same, that
spread is a defect incubator.

The refactoring changes the code from "spell out the mechanics here" to
"call the operation that owns this meaning." After the change, the call site
expresses intent, and future behavior changes live in the called function.

This pattern works best when the replacement name fits the local purpose. If
the name reads naturally at the call site, the call makes the code easier to
read. If the name does not fit, the similarity may be accidental, or the
existing function may have the wrong name. In that case, Rename Function or a
new function may be needed before this refactoring.

## 3. Forces

Engineering judgement. This dimension weighs maintenance forces rather than
quoting a single source.

**Coupling.** The refactoring lowers coupling between a caller and the
mechanics of an operation. The caller depends on the function contract instead
of knowing how the operation is performed. It raises coupling to the called
function, which matters when that function is owned by another team or package.

**Consistency.** The refactoring favors consistency. A policy, predicate, or
normalization now has one executable definition. The cost is that a caller
that meant to differ can be pulled under a shared behavior by mistake.

**Latency.** A function call can add a tiny dispatch cost. For most business
code that cost is invisible next to I/O, allocation, parsing, and network
latency. In a hot inner loop, the cost may matter, although modern compilers
often inline small functions. The correct test is measurement, not instinct.

**Operability.** A named function is easier to instrument. A shared helper can
own counters, logs, and error labels. The trade is that a production stack
trace now points at shared code, so telemetry needs enough caller context to
locate the path that invoked it.

**Cost of change.** The refactoring lowers the cost of changing behavior that
is meant to be shared. One edit updates all callers. It raises the cost of
changing one caller differently, because the caller may need a parameter, a new
function, or a local exception.

**Team topology.** The refactoring favors teams that agree on ownership for
shared behavior. It can hurt teams when a central helper becomes a dumping
ground or a review bottleneck.

**Cognitive load.** The call site gets shorter and more intentional. A reader
who needs mechanics must jump to the called function. This is a good trade
when the name is clear and the function contract is stable. It is a poor trade
when the function name hides surprising side effects.

**Safety.** Reusing a tested function reduces duplicated defect surface. The
danger is false equivalence, where similar inline code is replaced by a call
whose edge cases do not match.

## 4. Applicability and non-applicability

Reach for this refactoring when the following hold.

- The inline code performs the same behavior as an existing function, including
  edge cases that matter to the caller.
- The existing function has a name that makes sense at the call site.
- The inline code appears in more than one place, or it repeats a common
  language idiom that a library function already names.
- A change to the shared behavior should affect this caller.
- The replacement call makes the caller read at the level of policy rather
  than mechanism.
- The target function has tests, documentation, or enough usage history to be
  trusted more than the local copy.
- A mechanical search can find more inline copies after one replacement.

Do NOT reach for this refactoring, and treat the situation as
non-applicability, when the following hold.

- **The similarity is accidental.** If the inline block and the function happen
  to look alike today but should evolve separately, sharing creates a future
  coupling bug.
- **The target name does not describe the caller's purpose.** A poor name
  forces the reader to inspect the function body. Rename the function first,
  or keep the inline code.
- **The edge cases differ.** A loop that tests identity is not the same as a
  library call that uses value equality. A parser that accepts empty fields is
  not the same as one that rejects them.
- **The target function has side effects the inline code lacks.** Calling a
  helper that logs, allocates, caches, writes, locks, or mutates input may alter
  behavior even when the returned value matches.
- **The inline code is local adaptation.** Some repetition is a deliberate
  boundary between policies. Merging it removes that boundary.
- **The call would obscure a rare performance constraint.** A tight allocation
  path, parser loop, or numeric kernel may need explicit mechanics. Measure
  before replacing it.
- **The target function is an unstable internal API.** Moving a stable caller
  onto an internal helper can make the caller depend on code that is not meant
  to be reused.
- **The replacement requires many parameters.** A call with a long argument
  list can be harder to read than the inline block. Extract Parameter Object or
  a smaller function may be a better path.

## 5. Structure

The refactoring has four participants.

- **Inline behavior.** The local statements or expression that currently
  perform the operation. They are removed from the caller after the
  refactoring.
- **Caller.** The function, method, pipeline step, or handler that contains the
  inline behavior. After the refactoring, it delegates that behavior through a
  function call.
- **Target function.** The existing function that owns the behavior. It may be
  local, shared across the codebase, or supplied by a library.
- **Behavior contract.** The observable input, output, side effect, exception,
  mutation, ordering, and performance shape that must match between inline
  code and target function.

The relationship is simple but strict. The caller must not change observable
behavior. The target function must be semantically equivalent for this caller,
not only syntactically similar. The behavior contract is the object of review.
If the contract is unclear, write a characterization test before replacing the
inline code.

## 6. ASCII structure diagram

```
  BEFORE

  +-------------------------------+
  | Caller                        |
  |-------------------------------|
  | step A                        |
  | inline behavior               |
  |   statement 1                 |
  |   statement 2                 |
  |   return or assign result     |
  | step C                        |
  +-------------------------------+

  +-------------------------------+
  | Target function               |
  |-------------------------------|
  | same behavior already named   |
  +-------------------------------+


  AFTER

  +-------------------------------+        +----------------------------+
  | Caller                        | calls  | Target function            |
  |-------------------------------|------->|----------------------------|
  | step A                        |        | owns behavior contract     |
  | result = target(args)         |<-------| returns value or effect    |
  | step C                        |        +----------------------------+
  +-------------------------------+

  The caller keeps sequencing. The target function owns the repeated behavior.
```

## 7. Dynamics

Runtime behavior should be unchanged except for the call boundary. The
important action happens before runtime, during review and test: the developer
proves the target function covers the same contract as the inline behavior.

```
Developer          Test suite          Caller               Target function
    |                  |                  |                         |
    | identify match   |                  |                         |
    |----------------->|                  |                         |
    | characterize old |                  |                         |
    | behavior         |----------------->| run inline version       |
    |                  |<-----------------| observed result          |
    | replace inline   |                  |                         |
    | code with call   |                  |                         |
    | run tests        |----------------->| call target(args)        |
    |                  |                  |------------------------>|
    |                  |                  |<------------------------|
    |                  |<-----------------| same observed result     |
    | commit           |                  |                         |
    |                  |                  |                         |
```

The refactoring is often tiny in source text, but it is not trivial in
meaning. A one-line replacement can change evaluation count, mutation order, or
exception type. For example, the Go extension documentation for the
`slicescontains` analyzer warns that a target expression with side effects may
be evaluated once after replacement rather than once per tested slice element
(https://github.com/golang/vscode-go/wiki/settings, verified 2026-08-02).

## 8. Implementation variants

**Library call replacement.** Replace local mechanics with a standard library
or platform call. Examples include replacing a membership loop with
`Array.prototype.includes`, Python `any`, or Go `slices.Contains`. This variant
has the highest trust when the library contract exactly matches the caller.
The risk is edge-case mismatch, such as equality rules or evaluation count.

**Shared domain helper.** Replace repeated business logic with a domain
function, for example `isChargeableLine(item)` or `normalizeCustomerEmail(s)`.
This variant makes policy ownership explicit. The risk is that the helper grows
options until it becomes a weak abstraction for every caller.

**Private local helper already exists.** Replace a second inline block in the
same file with a private function call. This is often the cleanup pass after
Extract Function. It is cheap and low risk because visibility stays narrow.

**Predicate replacement.** Replace flag-setting loops and conditional chains
with a predicate call. This is common in Python and TypeScript:
`orders.some(isRefundable)` or `any(is_refundable(o) for o in orders)`.
The predicate name must state the business meaning, not the mechanics.

**Pipeline replacement.** Replace a loop fragment with a pipeline operation
when the language and team prefer that style. This overlaps with Replace Loop
with Pipeline. Use the more specific entry when the main change is from a loop
to `filter`, `map`, `reduce`, or iterator adapters.

**Generated or codemod replacement.** A static analysis rule or codemod detects
the inline idiom and rewrites it. This works for library idioms with precise
syntax. It is unsafe for domain semantics unless tests prove equivalence.

**Compiler-assisted replacement.** Some languages expose refactorings in IDEs
or analyzers. The tool can replace patterns such as manual contains loops.
Human review still owns semantic intent.

**Wrapper replacement.** Replace inline use of a third-party API with a local
wrapper call. This is valuable when the wrapper carries retries, error mapping,
or telemetry. It is a different decision from replacing a local algorithm with
a library call, because the wrapper becomes a boundary.

## 9. Known production uses

**Go tooling, `gopls` modernize analyzer surfaced through VS Code Go.** The Go
extension settings document an analyzer named `slicescontains` that replaces
loops checking whether a slice contains an element with calls to
`slices.Contains` or `slices.ContainsFunc`. The same documentation names the
side-effect caveat, which is exactly the contract risk this refactoring must
handle (https://github.com/golang/vscode-go/wiki/settings, verified
2026-08-02).

**Kubernetes, `hack/golangci.yaml`.** Kubernetes configures Go analysis policy
for a large production codebase. Its golangci configuration lists
`slicescontains`, describes it as replacing loops with `slices.Contains` or
`slices.ContainsFunc`, and disables it with the comment that the hint can make
code more obvious or avoid helper functions. This is a named production
codebase making an explicit adoption policy for this refactoring family
(https://github.com/kubernetes/kubernetes/blob/master/hack/golangci.yaml,
verified 2026-08-02).

**Cloud Posse Atmos, release v1.222.0.** The Atmos release notes include a
refactoring entry that replaced hand-written `SliceContainsString`,
`SliceContainsStringHasPrefix`, and `SliceContainsStringStartsWith` helpers
with Go standard library `slices.Contains` and `slices.ContainsFunc` across
about thirty-nine call sites, then removed the helpers. The note also records
the judgement that behavior and Big O stayed the same for that cleanup
(https://newreleases.io/project/github/cloudposse/atmos/release/v1.222.0,
verified 2026-08-02).

**Apache Airflow, release notes for the 2.8 line.** Airflow records an internal
refactoring item, "Replace loop by any when looking for a positive value in
core," linked to issue or pull request 33985. That is the Python form of this
pattern: a manual loop that computes existence is replaced by the named
built-in predicate operation
(https://airflow.apache.org/docs/apache-airflow/2.8.0/release_notes.html,
verified 2026-08-02).

## 10. Consequences

Positive.

- The caller reads at a higher level because a name replaces mechanics.
- Shared behavior has one implementation, so later policy changes happen in
  one place.
- The target function can have its own tests, docs, and telemetry.
- Review effort moves from line-by-line mechanics to contract equivalence.
- The codebase loses small hand-written variants of common library behavior.
- Duplicate bug fixes become less likely because there is no second copy to
  forget.
- Static analyzers and codemods can automate some replacements once an idiom is
  well understood.

Negative.

- A wrong replacement can change behavior while making the code look cleaner.
- The reader may need to jump to another file to inspect mechanics.
- A shared helper can collect unrelated callers and become hard to change.
- The function call can hide mutation, allocation, locking, exceptions, or
  evaluation order.
- The refactoring can create dependency direction problems if low-level code
  starts importing a high-level helper.
- A library call may have edge cases that differ from the local code.
- In a tight path, the call boundary may affect inlining or allocation.

## 11. Failure modes and misuse

Engineering judgement. These are practical failure patterns to check during
review and incident analysis.

**Symptom.** A test that passed for ordinary values fails for `NaN`, empty
input, missing fields, locale-specific case, or null values. **Cause.** The
inline code and the target function use different equality, truthiness, or
empty-input rules. **Fix.** Add characterization tests for those values. Keep
the inline code or write a narrower helper when contracts differ.

**Symptom.** A counter increments fewer times after the replacement, or a mock
records fewer predicate calls. **Cause.** The target function short-circuits or
evaluates an argument once, while the inline code evaluated an expression for
each item. **Fix.** Move side effects out of the tested expression, or keep the
explicit loop when repeated evaluation is part of the behavior.

**Symptom.** A caller starts logging, caching, acquiring a lock, or mutating an
input even though the old inline block did not. **Cause.** The shared function
does more than the visible mechanics that matched the inline code. **Fix.**
Split the pure operation from the effectful wrapper, then call the pure one.

**Symptom.** A later change to the target function breaks one caller that had
special business rules. **Cause.** The similarity was accidental. The caller
was pulled into a shared policy it did not own. **Fix.** Separate the policies
with two named functions, and name the difference.

**Symptom.** The codebase gains a utility module full of vague functions such
as `process`, `handle`, or `check`. **Cause.** The team replaced inline code
with calls before finding domain names. **Fix.** Rename functions around
business concepts or keep the inline code until a clear name appears.

**Symptom.** Build dependencies become cyclic or a low-level package imports a
feature package. **Cause.** The target function lives in the wrong module for
reuse. **Fix.** Move the target function to the lowest package that owns the
abstraction, or duplicate deliberately until a better boundary exists.

**Symptom.** A performance dashboard shows slower request handling after a
cleanup commit that looked mechanical. **Cause.** The replacement allocated an
intermediate collection, captured a closure, or prevented compiler inlining.
**Fix.** Benchmark the path. Use a lower-level function, keep the inline code,
or add an optimized helper with the same visible contract.

**Symptom.** A stack trace now ends in a shared helper and gives no clue which
business path supplied bad data. **Cause.** The call erased local context from
the failure location. **Fix.** Wrap errors with caller context or pass a label
used only for diagnostics.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Replace Inline Code with Function Call | Extract Function | Inline Function | Substitute Algorithm | Replace Loop with Pipeline | Keep Duplication |
|---|---|---|---|---|---|---|
| Coupling | Couples caller to an existing function contract | Creates a new local contract | Removes a contract | Couples caller to a new algorithm | Couples caller to collection API | Keeps callers independent |
| Consistency | Strong when behavior is shared | Strong after all callers move | Weak if body is copied | Strong for one algorithm | Strong for data flow idioms | Weak, copies drift |
| Latency | Usually neutral, measure hot paths | Usually neutral | Can remove call overhead | Depends on algorithm | May allocate or short-circuit | Whatever the inline code did |
| Operability | Central place for telemetry | New place for telemetry | Telemetry stays in caller | Depends on replacement | Pipeline steps may be visible | Each caller needs telemetry |
| Cost of change | Low for shared behavior | Low after extraction | High if copied | Low for algorithm updates | Low for pipeline edits | High across copies |
| Cognitive load | Lower at caller, higher when tracing | Lower if name is good | Lower for tiny code | Lower if algorithm is clearer | Lower for collection readers | Low locally, high globally |
| Team topology | Needs clear owner for target function | Local owner can start small | No shared owner | Needs algorithm owner | Needs style agreement | Avoids shared ownership |
| Safety | High with contract tests | High with extraction tests | Risk of copy errors | Risk of new edge cases | Risk from order and laziness | Risk from drift |

The matrix favors this refactoring when behavior already has the right owner.
Extract Function wins when no target function exists yet. Inline Function wins
when the name adds little. Substitute Algorithm wins when the whole algorithm
changes, not only the location of existing behavior. Replace Loop with Pipeline
wins when the main improvement is expressing data flow through collection
operations.

## 13. Related and incompatible patterns

- **Extract Function.** Often comes first. Extract one clear block, name it,
  test it, then search for similar inline blocks and replace them with calls.
- **Inline Function.** The inverse move. Use it when the call name no longer
  earns the jump, when the function is only a pass-through, or when the target
  function has become misleading.
- **Substitute Algorithm.** Related when the target function is not equivalent
  but intentionally better. Use that entry when behavior changes under test.
- **Replace Loop with Pipeline.** Related when the target function is a
  collection operation or iterator adapter. Use that entry for multi-step
  loop-to-pipeline rewrites.
- **Slide Statements.** A preparation move. Move adjacent statements together
  before deciding whether they match a target function.
- **Move Statements into Function.** Related but different. It moves repeated
  statements from callers into a function they already call. Replace Inline
  Code with Function Call replaces a separate inline block with an existing
  function call.
- **Introduce Parameter Object.** Composes when the replacement function would
  otherwise need a long parameter list.
- **Service Locator.** Conflicts when the "function call" hides a global lookup.
  Replacing clear inline code with a call into hidden global state makes
  dependencies less visible.
- **Speculative Generality.** Conflicts when the helper is created or called
  before the codebase has a real shared behavior.

## 14. Refactoring path in and out

Introducing the refactoring.

1. Identify the inline code and the candidate target function.
2. Write down the behavior contract: inputs, output, mutation, exceptions,
   ordering, empty-input behavior, equality rules, and evaluation count.
3. Add or find tests that cover ordinary input and edge cases. If no tests
   exist, add a characterization test around the caller before editing.
4. Replace the inline code with the function call. Keep argument expressions
   side-effect-free.
5. Run the narrow test that covers the caller.
6. Search for the old inline idiom in nearby code. Replace only the copies with
   the same contract.
7. Delete dead local variables and helper code left behind.
8. Run the broader suite for the module.

When the target function name is wrong, apply Rename Function first. When no
target exists, use Extract Function first. When the inline block is similar but
not equivalent, either keep it or use Substitute Algorithm with tests that
accept the changed behavior.

Backing out when the call stops earning its place.

1. Confirm why the call is harmful: wrong policy sharing, bad dependency
   direction, poor name, performance, or edge-case mismatch.
2. If only one caller differs, create a separate named function for that policy
   and move the caller to it.
3. If the target function is now a pass-through, use Inline Function.
4. If the shared helper mixed several policies, split it into smaller functions
   and move callers one group at a time.
5. If a library call caused an edge-case mismatch, restore the inline code or
   add a local adapter whose name states the local rule.
6. Keep tests that caught the difference. They are now contract tests for the
   chosen behavior.

## 15. Testing and verification

Engineering judgement. Testing should prove equivalence first, then guard the
shared contract.

Before the replacement, write or run characterization tests around the caller.
The strongest tests feed the same inputs through the old inline code and the
new function call and compare observable results. When keeping both versions is
not practical, record expected behavior through caller-level tests.

Test ordinary values, boundary values, empty input, null or missing values where
the language permits them, and values that exercise equality rules. For
JavaScript membership checks, include `NaN` if the old code used an equality
rule that could differ from `includes`. For Python `any` or `all`, include
empty iterables and generators with observable call counts. For Go
`slices.ContainsFunc`, include predicates without side effects unless repeated
evaluation is part of the behavior.

Verification techniques.

- **Golden caller test.** Assert that a caller's output is unchanged after the
  replacement.
- **Property test.** Generate inputs and compare old and new behavior while the
  old helper still exists in test code.
- **Mutation test.** Confirm that input objects are mutated, or not mutated, in
  the same way.
- **Exception test.** Confirm the same error type and message boundary when bad
  input is supplied.
- **Call-count test.** Use a spy predicate when evaluation count matters.
- **Microbenchmark.** Measure only when the code runs in a hot path or when the
  replacement allocates.

The refactoring is easy to review when the diff has one shape: deleted inline
mechanics, one function call, and tests that name the contract. It is hard to
review when the same patch renames functions, moves modules, changes policy,
and replaces inline code. Split those changes.

## 16. Observability signals

Engineering judgement. This refactoring usually changes source structure, not
runtime behavior, so observability focuses on guarding the shared function.

Useful signals.

- A counter on the target function when it performs policy that matters, labeled
  by caller or product area if cardinality is controlled.
- Error counts by target function and caller context.
- Duration histograms for replacements that open files, perform I/O, allocate
  large buffers, or call external services.
- Call result distribution for predicates used in routing, eligibility, fraud,
  billing, or access control.
- Version or config labels when a helper implements policy that can change by
  rollout.

A healthy dashboard shows the same call volume and error rate as before the
replacement. For a membership or predicate helper, true and false ratios should
move only when upstream data or product behavior changes. For a parser or
normalizer, rejection rates should not jump after a cleanup patch.

A failing dashboard shows one of four shapes. First, a spike in errors from the
target function after callers moved to it. Second, a caller label that never
appeared before, which can reveal an accidental coupling. Third, slower
duration for a path that replaced inline code with an allocating helper.
Fourth, a changed result ratio, such as fewer eligible records, after a
predicate replacement.

For low-level library calls such as `includes`, `any`, or `slices.Contains`,
there may be no useful telemetry inside the call. Put observability around the
domain decision that uses the result, not around the library call itself.

## 17. Security and privacy implications

Engineering judgement. The classical refactoring is mostly silent on security:
it should preserve behavior. Security risk appears when the inline code and the
target function have different validation, data handling, or side effects.

**Validation drift.** Replacing a local validation block with a shared helper
can tighten or loosen acceptance rules. Tightening can reject valid users.
Loosening can admit invalid data. Security-sensitive validators need tests for
allowed, denied, empty, malformed, encoded, and boundary inputs.

**Authorization and tenancy.** If inline authorization logic is replaced by a
shared function, the call must pass the same subject, resource, tenant, and
context. A missing tenant argument can turn a local check into a cross-tenant
check. Prefer parameter objects for authorization context because they make
missing fields visible.

**Logging and privacy.** A shared helper may log input values that the inline
code kept local. That can expose personal data or secrets. Before replacing
inline code in authentication, billing, health, or support paths, inspect the
target function's logs and errors.

**Dependency trust.** Replacing inline code with a third-party library call
moves trust to that package. This can be right, especially for well-maintained
standard libraries, but it changes supply-chain exposure. For sensitive code,
prefer standard library calls or a vetted internal wrapper.

**Timing behavior.** Some inline comparisons are constant time by design.
Replacing them with an ordinary equality or membership function can reintroduce
timing leaks. Do not apply this refactoring to cryptographic comparison unless
the target function is documented for that purpose.

**Error disclosure.** A target function may raise a more detailed error than
the inline code. That can reveal field names, internal IDs, file paths, or
policy details. Wrap or map errors at the boundary where external users can see
them.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 8, "Moving Features," section 8.5,
  "Replace Inline Code with Function Call."
- Martin Fowler, "Changes for the 2nd Edition of Refactoring,"
  https://martinfowler.com/articles/refactoring-2nd-changes.html, verified
  2026-08-02.
- MDN Web Docs, "Array.prototype.includes(),"
  https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/includes,
  verified 2026-08-02.
- Python Software Foundation, "Built-in Functions," entries for `any` and
  `all`, https://docs.python.org/3/library/functions.html#any, verified
  2026-08-02.
- Go standard library documentation, package `slices`, entries for `Contains`
  and `ContainsFunc`, https://pkg.go.dev/slices#Contains, verified
  2026-08-02.
- Go extension for Visual Studio Code, settings wiki, `slicescontains`
  analyzer, https://github.com/golang/vscode-go/wiki/settings, verified
  2026-08-02.
- Kubernetes, `hack/golangci.yaml`, modernize analyzer policy,
  https://github.com/kubernetes/kubernetes/blob/master/hack/golangci.yaml,
  verified 2026-08-02.
- Cloud Posse Atmos, release v1.222.0 notes,
  https://newreleases.io/project/github/cloudposse/atmos/release/v1.222.0,
  verified 2026-08-02.
- Apache Airflow, release notes for 2.8.0,
  https://airflow.apache.org/docs/apache-airflow/2.8.0/release_notes.html,
  verified 2026-08-02.

## Code examples

### TypeScript

The TypeScript example replaces a hand-written membership loop with
`includes`. It is valid when the desired rule is "blocked means present in this
array."

```typescript
const blockedStates = ["AK", "HI", "PR"];

function shipsByGroundBefore(state: string): boolean {
  let blocked = false;
  for (const code of blockedStates) {
    if (code === state) {
      blocked = true;
    }
  }
  return !blocked;
}

function shipsByGroundAfter(state: string): boolean {
  return !blockedStates.includes(state);
}

console.log(shipsByGroundBefore("MA"));
console.log(shipsByGroundAfter("HI"));
```

Verification run:

```text
$ npx tsc /tmp/replace-inline.ts --target es2020 --module commonjs --outDir /tmp/replace-inline-ts
$ node /tmp/replace-inline-ts/replace-inline.js
true
false
```

### Python

The Python example replaces a flag-setting loop with `any`. The predicate is
pure, so short-circuit behavior matches the intent.

```python
def has_overdue_before(invoices):
    found = False
    for invoice in invoices:
        if invoice["days_late"] > 0:
            found = True
            break
    return found


def has_overdue_after(invoices):
    return any(invoice["days_late"] > 0 for invoice in invoices)


sample = [{"days_late": 0}, {"days_late": 3}]
print(has_overdue_before(sample))
print(has_overdue_after(sample))
```

Verification run:

```text
$ python3 /tmp/replace_inline.py
True
True
```

### Go

The Go example replaces a manual slice scan with `slices.Contains`.

```go
package main

import (
	"fmt"
	"slices"
)

func canDeployBefore(region string) bool {
	allowed := []string{"iad", "fra", "syd"}
	for _, candidate := range allowed {
		if candidate == region {
			return true
		}
	}
	return false
}

func canDeployAfter(region string) bool {
	allowed := []string{"iad", "fra", "syd"}
	return slices.Contains(allowed, region)
}

func main() {
	fmt.Println(canDeployBefore("fra"))
	fmt.Println(canDeployAfter("gru"))
}
```

Verification run:

```text
$ go run /tmp/replace-inline.go
true
false
```
