---
name: Replace Control Flag with Break
slug: replace-control-flag-with-break
family: 03-refactoring
category: Refactoring
aliases: [Remove Control Flag, Replace Control Flag]
first_described: "Fowler 1999"
maturity: canonical
related: [replace-nested-conditional-with-guard-clauses, replace-loop-with-pipeline, remove-dead-code, extract-function, substitute-algorithm]
incompatible_with: []
verified: 2026-08-02
---

# Replace Control Flag with Break

## 1. Name, aliases, and lineage

The canonical name in this repository is **Replace Control Flag with Break**.
Martin Fowler's online catalog uses that name and lists **Remove Control Flag**
as an alias. The catalog example shows a loop guarded by a boolean named
`found`, then the same loop using `break` at the point where the match is found
(https://refactoring.com/catalog/replaceControlFlagWithBreak.html, verified
2026-08-02).

The lineage comes from the first edition of Martin Fowler's *Refactoring.
Improving the Design of Existing Code*, Addison-Wesley, 1999. Fowler's
published change note for the second edition lists **Remove Control Flag** on
page 245 of the first edition and says it was replaced by **Replace Control Flag
with Break** in the web edition
(https://martinfowler.com/articles/refactoring-2nd-changes.html, verified
2026-08-02). The second edition change note marks the refactoring as a web
edition entry, which is why this repository treats the web catalog name as the
current canonical name.

The phrase **control flag** means a variable whose main job is to steer loop
control after a condition has already decided that the loop should stop. It is
not the same as a business flag. A variable such as `isArchived`,
`requiresApproval`, or `hasPaidInvoice` may be domain state. A variable such as
`done`, `found`, `keepGoing`, or `shouldStop` inside a loop is suspect when it
only exists so the next loop condition can notice what the current iteration
already knows.

This refactoring belongs to the conditional simplification area of the
refactoring family. It is small, but it changes how a reader proves termination.
Before the refactoring, the reader has to track assignment to a mutable
variable. After it, the exit is stated directly by the loop construct.

## 2. Problem and context

A loop is doing a search, scan, parse, validation pass, import pass, or
accumulation. At some point inside the loop body the code learns that no more
iterations are needed. Instead of leaving the loop immediately, it writes that
decision into a flag and lets the loop condition, or a guard at the top of the
next iteration, stop the work later.

The shape often looks like this.

```text
let found = false;
let selected: string | undefined;

for (const sku of skus) {
  if (!found) {
    if (sku.startsWith("vip-")) {
      selected = sku;
      found = true;
    }
  }
}
```

The code is not wrong because it has a boolean. It is wrong when the boolean is
only a delayed exit signal. The assignment `found = true` says "we are done",
but the program keeps executing control scaffolding until the loop notices. The
reader must inspect every later statement in the loop to know whether more work
happens after the flag changes.

The context is local control flow, not system design. This refactoring fits
inside one function, one loop, and one narrow behavior-preserving edit. It is
especially common in code written under older style rules that preferred a
single exit point from a function or a single loop condition. Modern mainstream
languages expose direct loop exits. MDN documents JavaScript `break` as ending
the current loop or `switch` and transferring control to the following
statement (https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/break,
verified 2026-08-02). Python documents `break` as terminating the nearest
enclosing loop and skipping the loop `else` clause when present
(https://docs.python.org/3/reference/simple_stmts.html#the-break-statement,
verified 2026-08-02). Go documents `break` as terminating the innermost `for`,
`switch`, or `select`, with an optional label for an enclosing construct
(https://go.dev/ref/spec#Break_statements, verified 2026-08-02).

The refactoring is behavior-preserving only when the flag is not read after the
loop as part of the result. If code after the loop checks `found` to choose an
outcome, the replacement may be `return`, an extracted function, or a result
variable plus `break`. The control flag can be removed, but the result state
must remain somewhere.

The smell is strongest when the flag name describes control rather than domain
meaning. Names such as `done`, `finished`, `stop`, and `keepGoing` ask the
reader to simulate the loop machinery. Names such as `matchingOrder`,
`parseError`, and `selectedUser` describe values the caller might care about
after the loop. The first group tends to disappear under this refactoring. The
second group usually stays, with the loop exit moved beside the assignment that
sets the value.

The old form also creates a timing gap. The code decides to stop at one line,
but the loop stops at another line later in the function. Any edit inserted
between those points can accidentally run during the "already done" interval.
That gap is where maintenance bugs enter. `break` closes the gap by turning the
decision into the control transfer.

## 3. Forces

Engineering judgement. This dimension weighs local code pressures. The cited
language references in dimension 2 define what `break` does, but the choice to
prefer it in a given function is a design judgement.

- **Cognitive load.** Favoured. The exit condition sits where the decision is
  made. The reader does not trace a mutable flag through the remaining body and
  the next loop test.
- **Consistency.** Favoured when the loop has one exit decision. The code has
  one action for "done": leave the loop. It sacrifices consistency when a team
  uses a strict single-exit style and applies that rule across a legacy module.
- **Latency.** Mildly favoured. Work after the flag assignment stops
  immediately rather than waiting for another guard or loop check. The gain is
  usually tiny unless the skipped tail does input, output, locks, allocation, or
  heavy computation.
- **Coupling.** Neutral at module level, favoured inside the function. The loop
  no longer couples unrelated branches through a shared mutable flag.
- **Operability.** Mixed. A direct `break` is easier to inspect in code, but a
  flag name like `timedOut` sometimes carried a named reason that logging could
  reuse. If the reason matters, keep it as result state or log it before the
  exit.
- **Cost of change.** Favoured for small loops. New stop conditions become
  local `if` statements with local exits. It is worse in a long loop with many
  nested blocks, where several `break` statements can scatter termination.
- **Team topology.** Mostly neutral. The refactoring is local enough that it
  rarely crosses ownership lines. It helps teams doing reviews because the
  before and after diff is compact.
- **Testability.** Favoured. Tests can target "stops at first match" directly by
  counting visited items. A hidden flag often makes tests infer termination by
  final state alone.

The pattern favours explicit local exit and sacrifices the comfort of one
mutable variable that appears in the loop header. In compact loops that is a
good trade. In broad loops, the better move may be Extract Function followed by
`return`.

There is also a review-force trade. A flag makes the loop header look complete,
but pushes evidence into the body. A `break` makes the header less complete,
but puts evidence at the branch. In most product code, reviewers spend more
time reading body branches than proving loop algebra, so the second shape costs
less review effort. In numerical kernels, generated code, or code written to a
formal house style, the opposite may be true. That difference is judgement, not
a catalog fact.

## 4. Applicability and non-applicability

Reach for Replace Control Flag with Break when these conditions hold.

- A boolean or enum inside a loop means "stop scanning", "match found", "error
  reached", or "no more input", and it is assigned at the point where the loop
  should stop.
- The flag is not part of the business result after the loop. If a result is
  needed, it can be represented by a result variable, an optional value, an
  error value, or an extracted function return.
- The loop body has a small number of exit points and each one is easy to see
  from the loop body.
- The remaining loop tail after the flag assignment is accidental control
  plumbing, not work that must still run.
- The language's `break` semantics match the desired exit. For example, Python
  `break` leaves the nearest loop and executes any active `finally` before
  leaving that loop (https://docs.python.org/3/reference/simple_stmts.html#the-break-statement,
  verified 2026-08-02).
- The loop is a search, scanner, parser, validation pass, or "read until
  delimiter" operation where early termination is the normal case.

Do NOT reach for it in these cases.

- **The flag is domain state.** Reason. A variable such as `hasPayment`,
  `isComplete`, or `needsAudit` may be returned, logged, stored, or passed to
  another rule. Replacing it with `break` deletes meaning. Keep the state and
  maybe rename it.
- **The flag carries the reason after the loop.** Reason. Code may need to
  choose between "found", "not found", "malformed", and "timed out". Use an enum
  result, an early `return`, or Extract Function. A bare `break` can hide why the
  loop ended.
- **The loop has mandatory cleanup after the flag assignment.** Reason. Direct
  `break` can skip local work if that work sits below the assignment. Move the
  cleanup before the exit, use `defer` in Go, `finally` in JavaScript or Python,
  or extract the operation.
- **The loop has many nested exits.** Reason. Five `break` statements in a large
  body can be harder to audit than one named state machine. Prefer Extract
  Function with early `return`, or Replace Loop with Pipeline when the
  collection operation is a match.
- **The language target lacks labelled break and the exit must leave multiple
  loops.** Reason. JavaScript and Go have labels for this case, but Python does
  not. In Python, extracting the nested loops into a function and returning is
  often clearer than simulating a label with another flag.
- **The loop condition is the public algorithm.** Reason. Some embedded,
  generated, or safety-audited code bases encode their whole loop policy in the
  header. A local `break` may violate a local standard even if the language
  permits it.
- **The flag prevents repeated side effects.** Reason. A flag can sometimes mean
  "the alert was sent, but keep scanning for metrics." Replacing it with `break`
  would drop later observations. Split the side effect from the scan decision
  before changing control flow.
- **The loop is better expressed as a library search.** Reason. If the only
  work is selecting the first matching item, use `find`, `next`, `First`, or the
  language idiom. That may remove the whole loop, not only the flag.

## 5. Structure

The refactoring has five local participants.

- **Loop body.** The block that repeatedly inspects items, characters, rows,
  messages, or records.
- **Control flag.** A mutable local variable read by the loop condition or by a
  guard inside the loop. Its control value means "do not keep iterating."
- **Exit condition.** The branch inside the loop that discovers the stopping
  condition, such as a match, delimiter, parse error, end marker, or limit.
- **Direct exit.** A `break` statement that leaves the loop immediately. In
  labelled languages, it may be a labelled `break` when the target loop is not
  the nearest one.
- **Result state.** Any value that must survive after the loop, such as the item
  found, count accumulated, parse error, or status enum.

The relationship is a replacement of responsibility. Before the refactoring,
the control flag has two jobs. It records a local exit decision, and it may also
record result state. After the refactoring, `break` owns the exit decision. Any
real result state stays in a separate variable with a name tied to the result,
not to control.

The smallest valid end state still has a loop, a condition, and an exit. It has
no mutable variable whose only reader is loop control.

One boundary deserves care. A loop counter is not a control flag merely because
it appears in the condition. A counter such as `i`, `attempts`, or `bytesRead`
records progress through a range or input. It may also stop the loop, but it has
independent meaning. Replace Control Flag with Break is aimed at state whose
only meaning is "the loop should not continue."

## 6. ASCII structure diagram

```text
Before

  +---------------------+
  | caller              |
  +----------+----------+
             |
             v
  +---------------------+      reads and writes
  | loop body           | <---------------------+
  |                     |                       |
  | if exit condition   |                       |
  |   flag = true       |                       |
  | other guarded work  |                       |
  +----------+----------+                       |
             |                                  |
             v                                  |
  +---------------------+                       |
  | loop condition      | ---- checks flag -----+
  | item remains        |
  | and flag is false   |
  +---------------------+

After

  +---------------------+
  | caller              |
  +----------+----------+
             |
             v
  +---------------------+
  | loop body           |
  |                     |
  | if exit condition   |
  |   break             |
  | other normal work   |
  +----------+----------+
             |
             v
  +---------------------+
  | after loop          |
  | uses result state   |
  | if any              |
  +---------------------+
```

## 7. Dynamics

Engineering judgement. The diagram shows the behavior proof a reviewer performs
before and after the refactoring.

```text
Before

Loop start
  |
  v
Read flag in loop condition or top guard
  |
  +-- flag says stop ---------> After loop
  |
  v
Inspect current item
  |
  +-- stop condition true ----> Assign flag
  |                              |
  |                              v
  |                            Finish guarded tail
  |                              |
  |                              v
  |                            Next loop test
  |
  +-- stop condition false ---> Finish normal work
                                 |
                                 v
                               Next loop test

After

Loop start
  |
  v
Inspect current item
  |
  +-- stop condition true ----> break
  |                              |
  |                              v
  |                            After loop
  |
  +-- stop condition false ---> Finish normal work
                                 |
                                 v
                               Next loop test
```

The behavior check has three parts.

1. The flag assignment that ended the loop must be replaced with `break`.
2. Any statement that used to run after the assignment must be proved dead,
   moved before the `break`, or kept by not applying this refactoring.
3. Any value read after the loop must remain represented by result state.

In nested loops, the target of the exit matters. Go labels can name an
enclosing `for`, `switch`, or `select` target
(https://go.dev/ref/spec#Break_statements, verified 2026-08-02). JavaScript
also supports labelled `break` for a labelled statement
(https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/break,
verified 2026-08-02). Rust labels can direct `break` to an enclosing loop
(https://doc.rust-lang.org/reference/expressions/loop-expr.html#break-expressions,
verified 2026-08-02). Python has no labelled break in its reference grammar, so
the usual substitute is Extract Function plus `return`.

## 8. Implementation variants

**Plain loop `break`.** The direct form replaces `done = true` with `break`.
Use it when the loop has one level and no caller needs a reason code.

**Result variable plus `break`.** Keep a variable that records the found item or
error, but remove the flag that controls iteration. This is the common search
shape. The result variable answers "what was found"; `break` answers "why did
iteration stop now."

**Early `return` from extracted function.** If the loop exists only to compute a
value, extract it into a function and return the value at the decision point.
This removes the loop exit and the post-loop result check. It pairs with Extract
Function and often reads better than `break` in Python when multiple nested
loops are involved.

**Labelled `break`.** Go, JavaScript, Java, Rust, and Swift support some form of
labelled loop exit. Use it sparingly for nested scanning where the outer loop is
the true target. Go's specification gives labelled `break` as part of the break
statement grammar (https://go.dev/ref/spec#Break_statements, verified
2026-08-02). Rust documents labelled loop targets for `break`
(https://doc.rust-lang.org/reference/expressions/loop-expr.html#break-expressions,
verified 2026-08-02).

**Sentinel iterator or library search.** Some loops should move past `break` to
a collection operation. TypeScript `Array.prototype.find`, Python `next` over a
generator expression, Rust `Iterator::find`, and Go helper functions can express
"first matching item" without a flag or explicit loop. This is a larger
refactoring because it changes the loop shape.

**State machine remains explicit.** Parsers sometimes keep an enum such as
`InString`, `Escaped`, and `Done`. That is not a control flag smell when the
state has meaning across characters. You may still use `break` for final exit,
but do not erase the state machine.

**Exception or error return.** When the stop condition is failure, `break` is
not always the right exit. Returning an error or raising an exception can be
clearer if the caller should not continue with partial results.

## 9. Known production uses

**TypeScript compiler scanner.** The TypeScript compiler's `scanner.ts` uses
direct `break` statements while scanning trivia and comments. In the verified
source, `scanConflictMarkerTrivia` loops until it sees the next conflict marker
and then breaks; comment scanning also breaks when a line break or block comment
terminator is found
(https://github.com/microsoft/TypeScript/blob/94b4f8b79e370020cb31995e8fb0b78f9ba94349/src/compiler/scanner.ts,
verified 2026-08-20). This is production compiler code where a character-level
condition ends a local scan.

**CPython tokenizer compatibility path.** CPython's `Lib/tokenize.py` includes
`Untokenizer.untokenize`, where iteration over tokens breaks on compatibility
tokens and on the `ENDMARKER` token
(https://github.com/python/cpython/blob/main/Lib/tokenize.py, verified
2026-08-02). The source is a named production interpreter repository, and the
loop exit is expressed directly at the token that ends the local pass.

**Go standard library CSV reader.** The Go standard library's
`encoding/csv/reader.go` uses a labelled `parseField` loop. The verified source
breaks `parseField` on malformed quotes, end of record, end of input, and parse
errors
(https://github.com/golang/go/blob/master/src/encoding/csv/reader.go, verified
2026-08-02). This is a real labelled-break use in parser code, matching the Go
specification's label form for `break`
(https://go.dev/ref/spec#Break_statements, verified 2026-08-02).

These sources are not cited as historical refactoring examples. They are cited
as production code that uses direct loop exit in the class of scanning and
parsing problems where this refactoring usually lands.

## 10. Consequences

Engineering judgement. The lists below describe trade-offs observed in ordinary
maintenance work. The language references define `break`; they do not rate the
design.

Positive.

- The exit is local to the decision. A reviewer can read the condition and the
  exit on adjacent lines.
- The loop condition loses a mutable variable, so there is less state to keep in
  mind across iterations.
- Code after the exit condition becomes easier to classify as either normal
  work or unreachable work that should be moved or removed.
- Tests for early stop become easier because the loop should not visit later
  elements after the matching element.
- It lowers the risk of forgetting to set the flag in one branch, because the
  exit branch contains the exit action.
- It helps later refactorings such as Extract Function, Replace Loop with
  Pipeline, and Substitute Algorithm by making the loop's stop rule explicit.

Negative.

- Multiple `break` points can scatter termination across a long body.
- A bare `break` carries no reason. If the reason matters, it must be captured
  by a named result variable, error, or log field.
- In nested loops, an unlabelled `break` may leave only the inner loop when the
  intended target was outer work.
- A direct `break` can skip statements that were below the flag assignment. The
  edit is safe only after those statements are examined.
- It can conflict with local standards that require a single exit point, even
  when the language and tests permit direct exit.
- Debuggers and trace logs may no longer show the flag value that once hinted at
  why the loop stopped.

## 11. Failure modes and misuse

Engineering judgement. Each item is written as Symptom, Cause, Fix because those
are the signals a maintainer can observe.

**Skipped tail work.** Symptom. A counter, audit call, buffer append, or cleanup
that used to run after a flag assignment no longer runs for early matches.
Cause. The refactoring replaced the assignment with `break` without classifying
the later statements. Fix. Move mandatory tail work above the `break`, put
cleanup in `finally` or `defer`, or leave the flag until the loop can be split.

**Wrong loop exited.** Symptom. A nested scan stops the inner loop but keeps the
outer loop running, producing duplicate matches or overwriting the chosen
result. Cause. An unlabelled `break` was used where the old flag controlled an
outer loop. Fix. Use a labelled break in languages that support it, or extract
the nested scan into a function and `return` from it.

**Lost reason code.** Symptom. Logs or caller behavior can no longer tell
whether a loop stopped because it found a value, hit malformed input, or reached
a limit. Cause. The flag was carrying a reason as well as loop control. Fix. Add
a status enum, error value, or named result before replacing loop control with
`break`.

**Search still scans everything.** Symptom. A test with a spy input shows that
items after the match are still read. Cause. The flag assignment was removed,
but an outer iterator, callback, or library helper kept driving work. Fix.
Return from the callback if the API supports stop signals, or switch to a search
API that stops on first match.

**Boolean renamed but not removed.** Symptom. The diff changes `done` to
`found`, yet the loop still has `while !found` and assignments in several
branches. Cause. The refactoring stopped at naming. Fix. Replace the assignment
that controls termination with `break` and keep only real result state.

**Many breaks in a broad loop.** Symptom. A reviewer has to search an entire
screen to know every exit point. Cause. The refactoring was applied to a loop
that needed decomposition first. Fix. Extract the body, split phases, or use a
small state machine with one exit from each state handler.

**Incorrect Python loop `else`.** Symptom. Code in a Python loop `else` block no
longer runs, or starts running, after the change. Cause. Python's `else` on a
loop runs only when the loop finishes without `break`; the refactoring changes
that rule for matched cases (https://docs.python.org/3/reference/simple_stmts.html#the-break-statement,
verified 2026-08-02). Fix. Move the no-match behavior into an explicit result
check or use early `return`.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Replace Control Flag with Break | Early Return from Extracted Function | Replace Loop with Pipeline | Explicit State Machine | Keep Control Flag |
|---|---|---|---|---|---|
| Cognitive load | Low in short loops | Low when the function name is clear | Low for simple collection queries | Medium, state names must be tracked | High, flag writes and reads are separate |
| Coupling inside function | Low, exit is local | Low, result exits the function | Low, library owns traversal | Medium, branches share state | High, branches share mutable flag |
| Latency | Stops immediately | Stops immediately | Depends on lazy or eager API | Stops by state rule | May run tail guards before stopping |
| Consistency | Good with one or two exits | Good when one result is returned | Good for filtering and finding | Good for parsers with many states | Good only under single-exit style |
| Operability | Needs reason logging if needed | Return value can encode reason | Harder to place step logs | State is visible in telemetry | Flag value can be logged |
| Cost of change | Small local edit | Medium, adds function boundary | Medium, may change style | High, adds formal states | Low now, higher later |
| Team fit | Good for review diffs | Good when team likes small functions | Good in functional style code | Good in parser owners' code | Good only in legacy style modules |
| Failure risk | Skipping tail work | Return may bypass caller cleanup | Eager API may scan all data | Overbuilt for small scans | Forgotten assignment or stale flag |

Reading of the table. Use `break` when the loop is compact and the stop rule is
local. Use early return when the loop computes a value. Use a pipeline when the
operation is a standard collection search. Use a state machine when state is
real algorithm data. Keep the flag only when it has meaning beyond control or
when a local standard forbids direct exit.

## 13. Related and incompatible patterns

- **Extract Function.** Often composes before or after this refactoring. If the
  loop is broad, extract the scan into a named function and use `return` instead
  of a nested `break`.
- **Replace Nested Conditional with Guard Clauses.** Related by style. Both move
  exceptional or terminal cases to direct exits so the normal path reads in a
  straight line.
- **Replace Loop with Pipeline.** A stronger substitute when the loop is a
  collection query. A `find` or `any` operation can express the same early stop
  without hand-written loop mechanics.
- **Substitute Algorithm.** Composes when the whole loop is awkward. Removing
  the flag may reveal that the algorithm should be replaced rather than cleaned
  one branch at a time.
- **Remove Dead Code.** Often follows. Once the flag guard disappears, branches
  that only checked `!done` may become empty or unreachable.
- **Introduce Assertion.** Can pair with the refactoring when a loop invariant
  used to be implicit in the flag. Assert the invariant before the exit or after
  the loop.
- **Explicit State Machine.** Replaces this refactoring when the flag is not a
  mere exit signal. Parsers and protocol readers may need named states.
- **Single Exit Point rule.** Conflicts in teams or tools that ban early loop
  exit. The rule may be local policy rather than language law. If the code base
  enforces it, do not fight the house style in one function.

## 14. Refactoring path in and out

Introducing the refactoring.

1. Find a loop with a variable named like `done`, `found`, `keepGoing`,
   `shouldStop`, `finished`, or `matched`.
2. List every write to that variable. Separate writes that mean "leave the
   loop" from writes that represent a result after the loop.
3. List every read. If all reads are in the loop condition or loop guards, the
   variable is a control flag. If reads appear after the loop, split result state
   from control state first.
4. Pick one assignment that causes termination. Replace it with `break`.
5. Inspect the statements between the old assignment and the end of the loop.
   Move mandatory work above the `break`. Delete dead guard scaffolding.
6. Repeat for other termination assignments, one at a time.
7. Remove the flag from the loop condition. A `while i < n && !done` often
   becomes `while i < n`; a `for` loop with an inner `if !done` loses the guard.
8. Run the focused tests after each replacement. Add a test that proves items
   after the stop item are not visited.
9. If the result state now has a vague name, rename it. `foundItem` is clearer
   than a leftover `found` boolean plus nullable item.

For a large loop, do the same path in smaller commits. First add tests that
lock the current behavior. Next split result state from control state without
changing the exit. Then replace one exit assignment with `break`. Last, remove
the flag from the loop header after no branch writes it. This order keeps each
diff easy to review and makes rollback cheap if a hidden tail statement turns
out to matter.

When the loop has comments explaining the flag, read them as warnings, not
documentation to preserve. A comment such as "set done so later checks skip the
rest" often points to a missing `break`. A comment such as "keep scanning so all
errors are reported" points away from this refactoring. The comment tells you
which behavior the test should protect before you edit.

Refactoring out when `break` no longer earns its place.

1. If several break points now carry different meanings, introduce a status enum
   such as `Matched`, `Malformed`, or `LimitReached`.
2. If callers need a value, extract the loop into a function and return that
   value directly.
3. If nested labelled breaks make the flow hard to audit, extract the inner scan
   into a named function and replace the labelled exit with `return`.
4. If the loop has become a parser with durable state, introduce a small state
   machine and make exit one state transition, not scattered control flow.
5. If a collection pipeline now reads better, replace the loop with the
   language's search or predicate operation and delete the explicit `break`.

## 15. Testing and verification

Engineering judgement. Tests should prove both the returned value and the work
that did not happen after termination.

Useful tests.

- **First-match test.** Input contains two matches. Assert the first match wins.
- **No-match test.** Input contains no match. Assert the no-match result and the
  absence of accidental state from a prior iteration.
- **Stops-early test.** Use a spy iterable, callback, or fake reader that counts
  reads. Assert elements after the first terminal item are not visited.
- **Tail-work test.** If the old loop had cleanup, counters, or metrics below
  the flag assignment, assert that required work still happens.
- **Nested-loop target test.** In a nested scan, input after the inner match
  should reveal whether the outer loop kept running by mistake.
- **Python loop-else test.** When Python `for` or `while` has `else`, assert the
  match and no-match cases because `break` changes whether `else` runs
  (https://docs.python.org/3/reference/simple_stmts.html#the-break-statement,
  verified 2026-08-02).

What becomes easier. Branch coverage becomes more meaningful because the exit
branch contains an actual exit. Mutation testing also has a good target:
removing the `break` should fail the stops-early test.

What becomes harder. If observability relied on the flag value, tests now need
to assert a result enum, returned error, or log event. A bare `break` is not a
state object.

Test doubles that apply.

- A spy iterator that raises if read after the stop item.
- A fake reader that returns records and counts `read` calls.
- A callback spy that records visited ids.
- A contract test for parser loops: valid input, no delimiter, malformed quote,
  and end-of-input cases.

For performance-sensitive loops, keep one micro-benchmark only when the old flag
skipped expensive work or the new direct exit is on a hot path. Most of the
time, the gain is readability and bug prevention, not speed. A benchmark is
useful when the loop scans large buffers, rows, or tokens and the team wants to
prove early exit still happens after later edits.

Mutation tests are a strong fit. Delete the `break`, change the condition, or
move the `break` below the side effect. A healthy test suite should fail in each
case. If it does not, the code may read better after the refactoring, but the
behavior proof is still weak.

## 16. Observability signals

Engineering judgement. This refactoring is local, so many instances need no
production telemetry. Add signals only when the loop sits on a high-volume
path, parses external input, or controls money, access, delivery, or data loss.

What to record.

- A counter for exit reason when the reason matters. Example labels:
  `matched`, `end_marker`, `malformed_input`, `limit_reached`.
- A histogram of items scanned before exit. Healthy search paths should have a
  stable distribution. A sudden move toward scanning the whole input can mean
  the stop condition stopped matching.
- A counter of no-match outcomes for search loops.
- Parser error counters at the same branch that breaks out of the parse loop.
- Debug logs with correlation id and item index for rare, high-cost exits.

Healthy signals. The count of scanned items matches expected input shape. The
first-match path visits fewer items than the input length. No-match rates are
stable. Parser error labels match known bad input rates.

Failing signals. Scanned item counts climb after a release, suggesting that the
new condition no longer exits early. A parse loop reports many malformed exits
from one client. A labelled break path fires more often than expected, pointing
to data shape drift or a caller sending nested structures outside contract.

Do not log raw records merely to explain a `break`. If the input may contain
personal data, log indexes, counts, token kinds, hashes, or coarse reason codes.

A useful dashboard shape is a pair of charts. The first chart shows scanned
items per operation. The second shows exit reason counts. When both move
together, the cause is often data shape. When scanned items rise while exit
reason counts stay flat, the cause is often a lost early exit or a condition
that became too narrow. That distinction is difficult to recover from logs that
only say the loop finished.

For batch jobs, record the first terminal index and the total input length at
job summary level. That gives operators a cheap answer to "did this job stop
early by design or grind through the whole file?" without exposing row content.

## 17. Security and privacy implications

Engineering judgement. The refactoring is mostly silent on security. It does
not add a network boundary, permission check, parser grammar, or storage path by
itself. The risk appears when loop termination controls validation, scanning, or
cleanup.

Security gains.

- A direct exit can stop processing immediately after a validation failure,
  reducing the chance that later code consumes invalid input.
- A direct exit can make "first deny wins" authorization scans easier to audit.
- Removing a mutable flag can reduce stale-state bugs where one iteration sets
  the flag and another branch accidentally resets it.

Security risks.

- Replacing a flag with `break` can skip later validation if the old loop
  intentionally kept scanning after a match. For example, finding one allowed
  role does not prove no denied role appears later.
- A labelled break in nested validation can jump past cleanup, lock release, or
  audit recording unless those actions live in guaranteed cleanup constructs.
- A parser that breaks on malformed input but returns partial records can expose
  confused-deputy behavior if callers treat partial output as trusted.

Privacy implications.

- The old flag name may have encoded a reason without storing input data. If
  replacing it leads developers to log raw items to regain context, privacy gets
  worse. Prefer reason enums and positions.
- Early exit can reduce data touched. A first-match search over sensitive rows
  reads fewer later rows, which may reduce exposure in traces and memory.
- Early exit can also leave data unredacted if redaction used to run in the
  loop tail. Move redaction before every exit or into a cleanup phase.

## 18. References

1. Martin Fowler. *Refactoring. Improving the Design of Existing Code*.
   Addison-Wesley, 1999. Page 245, "Remove Control Flag." Page number
   confirmed by Fowler's second edition change note.
2. Martin Fowler. "Replace Control Flag with Break." Refactoring catalog.
   https://refactoring.com/catalog/replaceControlFlagWithBreak.html
   Verified 2026-08-02. Source for the current name, alias, and catalog shape.
3. Martin Fowler. "Changes for the 2nd Edition of Refactoring." 05 September
   2018.
   https://martinfowler.com/articles/refactoring-2nd-changes.html
   Verified 2026-08-02. Source for the first edition page number and the
   replacement naming in the web edition.
4. MDN Web Docs. "break." JavaScript reference.
   https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/break
   Verified 2026-08-02. Source for JavaScript `break` semantics and labelled
   `break` behavior.
5. Python Software Foundation. *Python 3.14 Language Reference*, section 7.9,
   "The break statement."
   https://docs.python.org/3/reference/simple_stmts.html#the-break-statement
   Verified 2026-08-02. Source for Python `break`, loop `else`, and `finally`
   behavior.
6. The Go Authors. *The Go Programming Language Specification*, "Break
   statements."
   https://go.dev/ref/spec#Break_statements
   Verified 2026-08-02. Source for Go `break` and labelled `break` behavior.
7. The Rust Project Developers. *The Rust Reference*, "Loop expressions",
   "`break` expressions."
   https://doc.rust-lang.org/reference/expressions/loop-expr.html#break-expressions
   Verified 2026-08-02. Source for Rust `break` and labelled loop behavior.
8. Microsoft. *TypeScript*, `src/compiler/scanner.ts`.
   https://github.com/microsoft/TypeScript/blob/94b4f8b79e370020cb31995e8fb0b78f9ba94349/src/compiler/scanner.ts
   Verified 2026-08-20. Source for the TypeScript compiler production use.
9. Python Software Foundation. *CPython*, `Lib/tokenize.py`.
   https://github.com/python/cpython/blob/main/Lib/tokenize.py
   Verified 2026-08-02. Source for the CPython tokenizer production use.
10. The Go Authors. *Go standard library*, `encoding/csv/reader.go`.
    https://github.com/golang/go/blob/master/src/encoding/csv/reader.go
    Verified 2026-08-02. Source for the CSV reader production use.

## Code examples

The examples are intentionally small. TypeScript shows the common search loop.
Python shows an extracted function because Python lacks labelled break. Go shows
a labelled `break` for a nested scan, matching Go's language spec.

### TypeScript

```typescript
type Order = {
  id: string;
  status: "open" | "paid" | "void";
};

export function firstOpenOrderId(orders: Order[]): string | undefined {
  let selected: string | undefined;

  for (const order of orders) {
    if (order.status === "open") {
      selected = order.id;
      break;
    }
  }

  return selected;
}

const result = firstOpenOrderId([
  { id: "a", status: "paid" },
  { id: "b", status: "open" },
  { id: "c", status: "open" },
]);

if (result !== "b") {
  throw new Error(`expected b, got ${result}`);
}
```

### Python

```python
from __future__ import annotations


def first_blocked_user(rows: list[dict[str, str]]) -> str | None:
    selected: str | None = None

    for row in rows:
        if row["state"] == "blocked":
            selected = row["user"]
            break

    return selected


def first_blocked_user_return(rows: list[dict[str, str]]) -> str | None:
    for row in rows:
        if row["state"] == "blocked":
            return row["user"]
    return None


if __name__ == "__main__":
    rows = [
        {"user": "ana", "state": "active"},
        {"user": "bo", "state": "blocked"},
        {"user": "cy", "state": "blocked"},
    ]
    assert first_blocked_user(rows) == "bo"
    assert first_blocked_user_return(rows) == "bo"
```

### Go

```go
package main

import "fmt"

type Cell struct {
	Row   int
	Col   int
	Value string
}

func firstErrorCell(grid [][]string) (Cell, bool) {
	var found Cell
	ok := false

scan:
	for r, row := range grid {
		for c, value := range row {
			if value == "ERR" {
				found = Cell{Row: r, Col: c, Value: value}
				ok = true
				break scan
			}
		}
	}

	return found, ok
}

func main() {
	cell, ok := firstErrorCell([][]string{
		{"ok", "ok"},
		{"ok", "ERR"},
		{"ERR", "late"},
	})
	if !ok || cell.Row != 1 || cell.Col != 1 {
		panic("wrong cell")
	}
	fmt.Println(cell.Row, cell.Col)
}
```
