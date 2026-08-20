---
name: Replace Exception with Precheck
slug: replace-exception-with-precheck
family: 03-refactoring
category: Refactoring
aliases: [Replace Exception with Test, Check Before Operation]
first_described: "Fowler 2018"
maturity: canonical
related: [replace-error-code-with-exception, introduce-assertion, separate-query-from-modifier, consolidate-conditional-expression]
incompatible_with: [easier-to-ask-for-forgiveness-than-permission]
verified: 2026-08-02
---

# Replace Exception with Precheck

## 1. Name, aliases, and lineage

The canonical name is **Replace Exception with Precheck**. Martin Fowler's
public catalog lists the refactoring under that name and gives **Replace
Exception with Test** as its alias
(https://refactoring.com/catalog/replaceExceptionWithPrecheck.html, verified
2026-08-02). Fowler's book page identifies *Refactoring. Improving the Design
of Existing Code*, second edition, Addison-Wesley, 2018, as the edition backed
by the refreshed public catalog
(https://martinfowler.com/books/refactoring.html, verified 2026-08-02).

The older alias, **Replace Exception with Test**, explains the original intent:
replace a `try` block that catches an exception from an ordinary condition with
an explicit test for that condition. The newer name uses **precheck** because
the test must happen before the operation that would otherwise throw.

This entry uses **precheck** rather than **test** for two reasons. First, "test"
can be confused with unit tests. Second, the refactoring is not asking the
reader to test implementation details. It asks the reader to move an expected
branch into a query that states whether the operation is legal, available, or
worth attempting.

The pattern is the inverse pressure of **Replace Error Code with Exception**.
That refactoring moves abnormal failure out of the return path and into the
exception path. Replace Exception with Precheck moves expected control flow out
of the exception path and back into a visible branch. The difference is not the
mechanism. The difference is whether the condition is an expected answer for
the caller.

One naming caution. Some communities prefer the Python phrase **EAFP**,
"easier to ask forgiveness than permission", where code attempts the operation
and handles the failure. This entry does not claim that EAFP is wrong. It names
the narrower refactoring for cases where the exception is being used as a
branch in ordinary code, where a low-cost, reliable predicate already exists,
and where reading the branch before the operation makes the program clearer.

## 2. Problem and context

A function calls an operation that can throw, catches one expected exception,
and treats that catch block as a normal branch. The code is not recovering from
an abnormal fault. It is asking a yes or no question by paying the cost and
noise of exception handling.

The code usually looks like one of these shapes.

- Try to read the next item, catch "no more items", then end a loop.
- Try to parse a value, catch "not a value", then skip that token.
- Try to retrieve a key from a map, catch "missing key", then use a default.
- Try to construct a URL, catch "invalid URL", then reject user input.
- Try to access an array position, catch "out of bounds", then return a
  fallback.

The reader has to inspect the catch block before they know whether the exception
means a true fault, a control-flow branch, or a compatibility shim around an old
API. That weakens the signal exceptions are meant to carry. A future maintainer
may add broad catch logic around the same call and accidentally hide unrelated
failures.

After the refactoring, the branch is explicit. The code first asks a query such
as `hasNext`, `containsKey`, `canParse`, `isValidIndex`, or `tryGetValue`. Only
when that query says the operation is valid does the code run the operation.
The exception remains available for faults the precheck cannot rule out, such
as concurrent mutation, permission loss, I/O errors, or programmer error.

The context that makes the refactoring attractive has four parts.

- The condition is expected in this workflow.
- A predicate exists, or can be extracted, that answers the condition without
  duplicating the operation.
- The predicate and the operation observe the same state closely enough that the
  check is meaningful.
- The code becomes easier to read because the expected branch moves from a
  catch clause into the main control flow.

The refactoring is not a ban on exceptions. It is a contract repair. The
contract becomes: if a caller can know the operation is not valid, that fact
should be visible before the call. Exceptions remain for cases the caller cannot
know locally or cannot handle locally.

The deepest source of confusion is that the same exception type can describe
two very different events. An out-of-bounds access can mean the caller is
walking a list until it ends, or it can mean a prior length calculation is
wrong. A parse exception can mean user input failed a normal validation branch,
or it can mean a service returned data that violates an internal protocol. A
missing-key exception can mean "there is no preference set for this customer",
or it can mean a required configuration record was not loaded. The syntax looks
the same in all cases. The refactoring asks the author to name which case they
mean.

That naming has design value beyond the single line of code. Once the expected
case has a predicate, the team can discuss it as a domain fact. "This period
number is outside the report range" is different from "this report object is
corrupt." "This token is not an integer" is different from "the scanner is
closed." The former belongs in ordinary product behavior. The latter belongs in
fault handling. A catch block that treats both through the same exception type
makes that distinction harder to defend during maintenance.

## 3. Forces

This dimension is engineering judgement, except where a named API or runtime is
cited.

- **Readability.** Favoured when a catch block is being used as an ordinary
  branch. `if scanner.hasNextInt()` tells the reader the next token may or may
  not be an integer before the program tries to consume it. Oracle's `Scanner`
  documentation shows `hasNextLong()` guarding `nextLong()` in sample code, and
  documents `nextInt` as throwing when the next token cannot be translated into
  an integer (https://docs.oracle.com/en/java/javase/18/docs/api/java.base/java/util/Scanner.html,
  verified 2026-08-02).
- **Exception signal quality.** Favoured. When expected misses stop producing
  exceptions, remaining exceptions become more suspicious and easier to route to
  error reporting.
- **Latency.** Favoured when the exception path is frequent. Creating,
  throwing, catching, and sometimes filling stack data is more work than a
  simple branch in many runtimes. This is judgement, not a cross-runtime law.
- **Coupling.** Mixed. A precheck may couple the caller to a second method on
  the callee. A combined query such as `TryGetValue` can reduce that coupling by
  folding the check and retrieval into one API.
- **Consistency.** Favoured when a module adopts one rule: expected absence is
  expressed by a predicate, optional value, boolean return, or typed result,
  while unexpected failure still throws.
- **Atomicity.** Sacrificed when the state can change between check and use.
  Rust's `Path::exists` documentation warns that existence checks can introduce
  time-of-check to time-of-use bugs and says `try_exists` still cannot prevent
  those bugs (https://doc.rust-lang.org/std/path/struct.Path.html, verified
  2026-08-02).
- **Operability.** Favoured when logs and metrics stop filling with expected
  exceptions. Sacrificed if teams stop recording rejected input counts because
  the code no longer throws.
- **Team topology.** Favoured inside a team-owned module, where the same team
  can add a predicate and update callers together. Sacrificed across a public
  API if callers need the old throwing form.
- **Cognitive load.** Favoured for readers of the caller. Sacrificed if the
  precheck predicate duplicates hidden rules and now has to be audited beside
  the operation.

The refactoring favours explicit, expected branches and quieter failure
channels. It sacrifices the compact "try it and handle it" style and can
sacrifice atomicity when the checked state is shared.

There is a social force as well. This is judgement. Teams often create broad
rules such as "never use exceptions for flow control" or "always prefer the
operation over a precheck." Those rules are easy to remember and too coarse for
design work. The useful rule is narrower: expected conditions should be visible
in the contract that the caller is meant to use. Sometimes that contract is a
predicate. Sometimes it is an option or result value. Sometimes it is a narrow
catch around the only operation that can tell the truth. The refactoring is the
right move only for the first group.

## 4. Applicability and non-applicability

Reach for Replace Exception with Precheck when the following hold.

- The exception is raised often enough that it represents expected control flow,
  not an abnormal incident.
- The catch block handles one specific condition and then continues normally.
- A predicate can answer the condition before the operation without causing the
  same side effects as the operation.
- The checked state is local, immutable for the duration of the check and use,
  or protected by a lock or transaction.
- The caller's branch is clearer than the catch block it replaces.
- The exception type is too broad for the branch. For example, catching
  `IndexError` around a block that touches several lists hides which access was
  expected to miss.
- Telemetry treats the exception as an error even though the product treats it
  as an ordinary miss.
- The runtime, library, or language already supplies a paired precheck API, such
  as `Iterator.hasNext` before `Iterator.next` in Java
  (https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Iterator.html,
  verified 2026-08-02).

Do NOT reach for this refactoring in these non-applicability cases.

- **The operation is the only reliable check.** File systems, remote services,
  process tables, queues, and distributed locks can change after a precheck. In
  those cases, attempt the operation and handle the error returned by that
  operation.
- **The precheck creates a race.** Checking whether a file exists before
  creating it can let another process create the file in the gap. Use an atomic
  create operation or handle the creation failure. Rust's path documentation
  warns directly about time-of-check to time-of-use risk for existence checks
  (https://doc.rust-lang.org/std/path/struct.Path.html, verified 2026-08-02).
- **The exception represents a programmer bug.** `NullPointerException`,
  `AssertionError`, failed bounds checks in code that already promised a valid
  index, and impossible enum branches should not be hidden behind defensive
  prechecks. Fix the caller contract or use Introduce Assertion.
- **The caller cannot make a useful choice.** If every caller would run the same
  catch block, leave a throwing helper or central handler in place.
- **The precheck repeats expensive work.** Parsing an entire document to ask
  whether parsing will work, then parsing it again, doubles the cost. Prefer a
  single parse that returns a typed result.
- **The exception is rare and diagnostic detail matters.** A rare failure with a
  stack trace, cause chain, and input context may be easier to debug than a
  false predicate that discards the reason.
- **The language idiom says to return error values.** Go APIs commonly return
  `value, error`; replacing those with panics is not this refactoring.
- **The code runs in concurrent mutable state with no lock.** A collection may
  be non-empty when checked and empty when consumed. Use an atomic poll, pop, or
  take API if one exists.
- **The precheck makes authorization weaker.** Checking "can access" before the
  privileged operation can race with permission changes and can reveal resource
  existence. Authorize during the operation that uses the resource.
- **The catch block is translating an external protocol.** HTTP status codes,
  database SQLState values, and operating-system errors often arrive as error
  data from outside the program. Convert them at the boundary, but do not invent
  a local precheck that cannot know the remote truth.

## 5. Structure

The refactoring has six participants.

- **Client branch.** The caller that currently contains `try`, the operation,
  the catch clause, and the fallback path. After the refactoring it owns an
  explicit conditional.
- **Risky operation.** The operation that may throw. It still may throw after
  the refactoring, but not for the expected branch the caller can check.
- **Expected condition.** The ordinary case currently represented by the caught
  exception, such as empty iterator, missing key, invalid token, or invalid
  index.
- **Precheck query.** A side-effect-free or low-side-effect query that answers
  whether the risky operation should be attempted. It can be an existing method,
  an extracted predicate, or a combined "try" method.
- **Fallback path.** The behavior formerly in the catch block. It may return a
  default, skip an item, show a validation message, or end a loop.
- **Residual exception path.** The abnormal failures that remain exceptional
  after the expected condition is removed from the catch block.

The relationships are small but strict. The client calls the precheck before
the risky operation. The precheck must test the same condition that the catch
block handled. The fallback path moves from the catch clause into the negative
branch. The risky operation remains in the positive branch. The residual
exception path is either removed from the caller because a higher boundary owns
it, or narrowed to failures the caller can still handle.

## 6. ASCII structure diagram

```text
Before

  +--------------------+
  | Client branch      |
  |--------------------|
  | try risky()        |
  | catch Expected     |
  |   fallback()       |
  +---------+----------+
            |
            v
  +--------------------+       throws Expected for normal miss
  | Risky operation    |------------------------------------+
  +--------------------+                                    |
            |                                               |
            v                                               |
  +--------------------+                                    |
  | Normal result      |<-----------------------------------+
  +--------------------+       catch resumes fallback

After

  +--------------------+
  | Client branch      |
  |--------------------|
  | if precheck()      |
  |   risky()          |
  | else fallback()    |
  +----+----------+----+
       |          |
       | yes      | no
       v          v
  +---------+  +--------------------+
  | risky() |  | Fallback path      |
  +----+----+  +--------------------+
       |
       v
  +--------------------+
  | Normal result      |
  +--------------------+

  Residual exceptions still propagate to the owning boundary.
```

## 7. Dynamics

At runtime, the important change is not that an exception disappears from the
program. The important change is that the expected branch is decided before the
operation consumes, mutates, parses, or indexes.

```text
Before

Client            Risky operation          Exception machinery
  |                     |                           |
  |-- call risky() ---->|                           |
  |                     |-- detects expected miss --|
  |                     |                           |
  |                     |<-- create and throw ------|
  |<-- unwind ----------|                           |
  |-- catch Expected --------------------------------
  |-- run fallback()
  |

After

Client            Precheck query            Risky operation
  |                     |                           |
  |-- precheck() ------>|                           |
  |<-- false -----------|                           |
  |-- run fallback()                                |
  |                                                 |
  |-- precheck() ------>|                           |
  |<-- true ------------|                           |
  |-- call risky() -------------------------------->|
  |<-- normal result -------------------------------|
```

Two runtime details decide whether the refactoring is sound.

First, the precheck and the operation must be close together in time and must
see compatible state. On a local immutable string, `canParse` followed by
construction is stable. On a file path shared by processes, existence followed
by open is not stable.

Second, the precheck must not consume the thing the operation needs. If
`hasNextInt` advanced the scanner, it would be unsafe as a guard for `nextInt`.
Oracle documents `Scanner.hasNextLong` as not advancing past input while
answering whether the next token can be interpreted as a long
(https://docs.oracle.com/en/java/javase/18/docs/api/java.base/java/util/Scanner.html,
verified 2026-08-02). That property is the kind of contract a precheck needs.

## 8. Implementation variants

**Existing paired predicate.** Use a library's paired query and operation, such
as `hasNext` with `next` or `canParse` with construction. This is the lowest
risk form because the library author owns both sides of the contract. It still
needs a reader to know whether the query consumes state.

**Extracted predicate.** Move the condition implied by the catch into a named
query, then branch on it. This fits array bounds, enum membership, string shape,
and local value ranges. The risk is duplicated logic when the risky operation
has hidden rules that the extracted query misses.

**Combined try method.** Replace `containsKey` plus indexer, or `has` plus
`get`, with one method that reports success and yields the value. Microsoft's
`IDictionary<TKey,TValue>.TryGetValue` combines key presence and retrieval, and
the documentation contrasts it with using the indexer for missing keys
(https://learn.microsoft.com/en-us/dotnet/api/system.collections.generic.idictionary-2.trygetvalue,
verified 2026-08-02). This variant avoids the gap between check and lookup
inside one collection object.

**Option or nullable return.** Change the risky operation to return `None`,
`null`, `Optional`, or an option type for expected absence. This is stronger
than adding a precheck when the caller wants the value only if present. It moves
the API away from throwing for absence. The cost is a contract change for every
caller.

**Typed result.** Return a value such as `Result<T, E>` or an object with
`ok`, `value`, and `reason`. This fits parsing and validation because the caller
often wants the reason for rejection. It also avoids parsing twice.

**Atomic operation.** Replace check then use with one operation such as
`poll`, `pop`, `take`, `putIfAbsent`, or exclusive create. This is the right
variant when shared mutable state makes a separate precheck unsafe.

**Boundary translation.** Keep exceptions inside a small adapter, but expose a
prechecked or result-based API to callers. This is common when a third-party
library throws for expected misses and the application wants a clearer local
contract.

**Guard clause.** When the precheck rejects the current function's input, put a
guard clause before the risky operation. This keeps the success path less
indented and makes the invalid case visible at the top of the function.

**Policy object.** Put the fallback decision behind a small object or function
when several callers share the same expected miss but disagree about response.
For example, a reporting screen may return zero for an absent period while an
audit export may record a rejected row. The precheck can remain the same while
the policy changes. The risk is turning a simple branch into a second
abstraction before the code has more than one policy.

**Prechecked iterator wrapper.** Wrap a throwing cursor or stream with an
adapter that exposes `peek`, `hasNext`, or `nextOrNone`. This is common when the
source API comes from older code or a third-party package. The wrapper becomes
the local contract and keeps the rest of the codebase from learning the
exception shape. The wrapper must be small and heavily tested, because every
caller now trusts it to preserve cursor state.

**Validation front door.** For user input, run cheap shape checks before calling
constructors or parsers that throw. This fits URLs, dates, integer strings, and
enum names when the validator and parser share rules. It does not fit grammars
where the parser is the only accurate implementation of the language.

## 9. Known production uses

**Java Collections Framework, `Iterator.hasNext()` before `Iterator.next()`.**
The Java SE 21 API documents `hasNext()` as returning true when iteration has
more elements, and describes that as the case where `next()` would return an
element rather than throw. The same page documents `next()` as throwing
`NoSuchElementException` when there are no more elements. This is a standard
library example of replacing "call `next` and catch exhaustion" with a
precheck before consumption
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Iterator.html,
verified 2026-08-02).

**Java `Scanner`, `hasNextInt()` and sibling methods before `nextInt()`.**
Oracle's Scanner documentation describes a scanner that parses tokens into
typed values. It shows a loop using `hasNextLong()` before `nextLong()`, and
documents numeric `next` methods as throwing when the next token cannot be
translated or when input is exhausted. The production use is the standard
library's paired API: ask whether the next token has the right shape before
consuming it
(https://docs.oracle.com/en/java/javase/18/docs/api/java.base/java/util/Scanner.html,
verified 2026-08-02).

**.NET collections, `IDictionary<TKey,TValue>.TryGetValue()`.** Microsoft
documents `TryGetValue` as returning a boolean and assigning the associated
value when a key exists. The same page says it combines `ContainsKey` and the
indexer, and contrasts it with the indexer throwing for nonexistent keys. This
is a named framework API that turns a missing-key exception branch into a
prechecked retrieval
(https://learn.microsoft.com/en-us/dotnet/api/system.collections.generic.idictionary-2.trygetvalue,
verified 2026-08-02).

**Web platform URL API, `URL.canParse()` before `new URL()`.** MDN documents
`URL.canParse()` as returning whether a URL string and optional base are valid
and parsable. The same page says the `URL` constructor raises an exception when
the URL cannot be parsed, and presents `canParse()` as the precheck option
(https://developer.mozilla.org/en-US/docs/Web/API/URL, verified 2026-08-02).

**Rust standard library, `Path::try_exists()` as a guarded existence query.**
Rust documents `Path::exists` and `Path::try_exists`, and warns that both are
unable to prevent time-of-check to time-of-use bugs. This is production
evidence for both the use and the limit of prechecks around filesystem
operations
(https://doc.rust-lang.org/std/path/struct.Path.html, verified 2026-08-02).

## 10. Consequences

This dimension is engineering judgement.

Positive.

- Expected control flow becomes visible in the caller.
- Logs and error trackers stop receiving exceptions for ordinary misses.
- The exception path regains meaning because remaining exceptions are less
  likely to be planned branches.
- Reviewers can check the branch condition directly instead of reading a catch
  block to infer it.
- The code can choose a cheaper fallback before allocating exception objects or
  stack data.
- A named precheck documents the operation's valid domain.
- The refactoring often reveals a missing API, such as `tryRead`, `canParse`,
  `isValidIndex`, or `peek`.

Negative.

- A separate precheck can race with the operation when state is shared.
- The precheck can drift from the operation's real rules if both are maintained
  by hand.
- The caller may now call two methods where it previously called one.
- Broad defensive prechecks can hide programmer errors that should fail fast.
- A false return can lose diagnostic detail that the original exception carried.
- Public APIs may need two forms during migration, one throwing and one
  prechecked or result-based.
- Overuse can produce cluttered code where `try` with a narrow catch was
  simpler.

## 11. Failure modes and misuse

This dimension is engineering judgement.

**Race between check and use.** Symptom. Logs show "file not found",
"already exists", or "empty queue" after a successful precheck a few
microseconds earlier. Cause. Another process or thread changed the state
between the predicate and the operation. Fix. Use an atomic operation, hold the
right lock, or handle the operation's failure directly.

**Precheck duplicates incomplete rules.** Symptom. The branch says input is
valid, but the operation still rejects values that pass the predicate. Cause.
The predicate reimplemented part of the parser, validator, or lookup logic and
missed a rule. Fix. Extract the predicate from the same rule source, or replace
both with a single typed result.

**Broad catch translated into broad guard.** Symptom. The code stops throwing,
but invalid programmer states now return defaults that corrupt later work.
Cause. A catch for a broad exception was replaced with a broad `if` instead of
identifying the one expected condition. Fix. Narrow the condition and let
programmer errors fail.

**Precheck consumes state.** Symptom. Every other token is skipped, the first
row in a cursor is missing, or a queue appears to drop messages. Cause. The
query advanced the iterator, stream, cursor, or scanner. Fix. Use a documented
peek or has method that does not advance, buffer the item, or keep the original
operation with explicit error handling.

**Hidden performance regression.** Symptom. CPU time doubles on large inputs
after "cleanup", with profiles showing validation and parsing both hot. Cause.
The precheck parses enough to prove the full parse will work, then the program
parses again. Fix. Parse once and return a result object with value or reason.

**Metric disappearance.** Symptom. Error counts drop to zero after deployment,
but user-facing rejections stay flat or increase. Cause. The refactoring moved
expected misses out of exceptions without adding a counter for the fallback
path. Fix. Add metrics for rejected, absent, skipped, or defaulted branches.

**Compatibility break.** Symptom. Downstream clients keep catching an exception
that no longer happens, while new callers forget to check the boolean. Cause. A
published API changed from throwing to prechecked return without a migration
adapter. Fix. Add a new method name for the new contract and keep the old
throwing method until callers migrate.

**Double lookup drift.** Symptom. A map lookup returns no value even though a
prior `contains` call returned true, or a value changes between both calls.
Cause. The collection is mutable or concurrent, and the precheck and retrieval
are separate. Fix. Use a combined retrieval method such as `TryGetValue`, or use
the collection's atomic operation.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Replace Exception with Precheck | Keep Narrow Catch | Replace Exception with Result | Introduce Assertion | Atomic Operation | Notification |
|---|---|---|---|---|---|---|
| Expected branch readability | High. The branch is visible before the call | Medium. The catch explains it later | High. Caller branches on result | Low. Assertion states a bug | Medium. Branch depends on return | High for validation |
| Exception signal quality | High. Expected misses stop throwing | Medium. Catch remains planned | High. Expected result does not throw | High. Failures are bugs | High | High |
| Race resistance | Low when state is shared | High. Operation is the check | High if operation returns result | Not applicable | High | Medium |
| Diagnostic detail | Medium. Predicate may hide reason | High. Exception carries context | High if result carries reason | High for programmer bugs | Medium | High. Many reasons |
| Caller cost | One extra branch | One `try` block | Contract change | No recovery path | New API or primitive | Result collection |
| Fit for local immutable data | High | Medium | High | Medium | Low | Medium |
| Fit for files and distributed state | Low unless advisory | Medium | High | Low | High | Low |
| Fit for validation forms | Medium for one field | Low | High | Low | Low | High |
| Operability | High if fallback metrics exist | Medium. Expected exceptions noisy | High | Medium | High | High |
| Team migration cost | Medium | Low | High | Medium | High if API absent | High |

Reading of the table. Replace Exception with Precheck wins when the condition is
local, expected, and cheap to ask. Keep Narrow Catch wins when the operation is
the only truthful check. Replace Exception with Result wins when the caller
needs the failure reason as data. Introduce Assertion wins when the condition
should be impossible. Atomic Operation wins for shared mutable state.
Notification wins when the caller needs many validation messages at once.

The matrix is meant to prevent a mechanical rewrite. This is judgement. A team
can improve one force while damaging another. Replacing a parse exception with
`canParse` may make a form handler clearer, but replacing a database insert
exception with "check then insert" can create a duplicate-key race. Replacing a
missing-key exception with `TryGetValue` improves both readability and race
resistance inside one dictionary object, but replacing it with `ContainsKey`
plus indexer may still be wrong for a concurrent map. The named alternative
matters because the same visible shape, `if` before call, can represent a good
local branch or a broken distributed protocol.

## 13. Related and incompatible patterns

- **Replace Error Code with Exception.** Pulls in the opposite direction. Use it
  when failure is abnormal for the caller and a missed check would continue a
  broken workflow. Use Replace Exception with Precheck when the branch is an
  expected answer that callers should read in ordinary control flow.
- **Separate Query from Modifier.** Often prepares this refactoring. A precheck
  is normally a query, while the risky operation may consume or modify state.
  The split is sound only when the query can answer without changing the state
  the operation needs.
- **Introduce Assertion.** Replaces this refactoring when the caught exception
  indicates a violated programming contract. An assertion says "this should not
  happen"; a precheck says "this may happen and here is the branch."
- **Consolidate Conditional Expression.** Composes with the extracted predicate
  variant. Several small checks can be combined into a named predicate that
  explains why the operation is safe to call.
- **Introduce Special Case.** Can replace a precheck when absence should behave
  like an object with default behavior. Instead of `if missing then default`,
  return a special object and let polymorphism carry the branch.
- **Notification.** Replaces this refactoring for validation workflows that need
  several errors at once. A precheck can answer one condition; a notification
  can report a set.
- **Easier to Ask Forgiveness than Permission.** Conflicts as a general style.
  It can be the better style in Python code, file operations, and concurrent
  state. The conflict is resolved by context, not by declaring one style
  universal.
- **Guard Clauses.** A common shape after the refactoring. Put the negative
  precheck near the top of a function and return early, then let the rest of the
  function read as the success path.

## 14. Refactoring path in and out

Introducing the refactoring.

1. Find a `try` block where the catch clause returns a normal fallback, skips
   an item, or ends a loop.
2. Confirm the caught exception represents one expected condition. If the same
   exception could come from several statements in the block, narrow the block
   first.
3. Write a characterization test for both paths: one input where the operation
   succeeds and one where the catch block runs.
4. Extract the risky operation into its own statement if needed, so the
   expected exception can be tied to one call.
5. Identify an existing precheck. Prefer a documented paired API such as
   `hasNext`, `canParse`, `try_exists`, or `TryGetValue`.
6. If no predicate exists, extract one from the same rules the operation uses.
   Keep it local at first.
7. Replace the `try` and catch with an explicit branch. Put the old catch body
   into the negative branch.
8. Run the characterization tests. Add an edge case for stale state if the
   checked state can change.
9. Remove now-unused exception imports and broad catch blocks.
10. Add fallback metrics if the old exception was counted by production
   telemetry.

Keep the steps small because this refactoring can change behavior while looking
cosmetic. The riskiest hidden behavior change is catch scope. A catch block may
have covered three calls, while the author believed it covered one. After the
refactoring, only one precheck may guard one call. That can be a repair or a
regression. Before editing, isolate the risky call so the old and new behavior
can be compared.

Another hidden behavior change is fallback timing. In the catch form, any side
effects before the throwing line have already happened when fallback runs. In
the precheck form, fallback may run before those side effects. If the side
effects are logging, counters, cursor movement, or cache warming, the new code
can differ even when return values match. Move side effects outside the guarded
region or record the intended ordering in tests.

Refactoring out when the precheck stops earning its place.

1. Look for duplicated check and use pairs where the operation can still fail
   for the checked condition.
2. If the operation is remote, file-based, or concurrent, replace the pair with
   one atomic operation or with a result-returning API.
3. If callers need failure reasons, replace the predicate plus operation with a
   single parse, lookup, or validation function returning a typed result.
4. If the branch states an impossible case, replace the precheck with an
   assertion or a contract test.
5. If all callers do the same fallback, move that fallback into a helper with a
   name that states the policy.
6. Delete precheck predicates that are now private duplicates of the operation's
   own validation rules.

The refactoring often starts locally and then migrates into the API. That second
step should be deliberate. If four callers all write the same precheck before
the same throwing operation, the operation probably needs a paired predicate or
a result-returning sibling. If only one caller needs the branch, keep the
predicate private to that caller. A public predicate is a promise that future
callers can rely on it, which means its naming, race behavior, and cost need the
same review as any other public method.

## 15. Testing and verification

This dimension is engineering judgement.

Easier because of the refactoring.

- The expected branch can be tested without arranging for an exception to be
  thrown.
- The success path and fallback path become separate branch cases in coverage
  reports.
- The predicate can get small boundary tests, such as empty input, last valid
  index, first invalid index, malformed URL, and missing key.
- Tests no longer need broad exception assertions that can pass for the wrong
  reason.

Harder because of the refactoring.

- The predicate and the operation now need consistency tests.
- Race behavior may need stress tests or API-level tests against concurrent
  collections, queues, or files.
- If the old exception carried a reason, tests must verify that the new fallback
  still exposes the reason where the user needs it.
- Code coverage can look better while diagnostic quality gets worse, because
  the exception path no longer appears.

Techniques that apply.

- **Characterization test.** Capture the old catch behavior before changing the
  shape. This is the main guard against changing fallback policy.
- **Predicate boundary table.** Use a table of values at and around the valid
  range. For indexes, include `-1`, `0`, last valid, length, and length plus
  one.
- **Consistency property.** For local deterministic operations, assert that
  when the predicate returns true, the operation does not throw the expected
  exception.
- **Mutation test.** Mutate the predicate boundary and confirm tests fail. This
  catches off-by-one errors in extracted predicates.
- **Concurrency test.** For shared state, force a change between precheck and
  operation. The test should prove the residual failure is still handled.
- **Telemetry test.** If the old exception was counted, assert that the fallback
  path emits the replacement counter.

Test naming should mirror the contract change. A weak test name says
`does_not_throw_for_bad_index`. A stronger name says
`returns_zero_when_period_is_outside_available_range`. The second name states
the domain behavior, which is the reason the exception was wrong for that path.
It also leaves space for other bad indexes to remain faults if the contract
draws that boundary.

For parser-like code, add one test that proves the precheck and operation agree
on a representative set of invalid inputs. The point is not to recreate a full
parser test suite around the predicate. The point is to catch drift when the
operation accepts a new syntax and the predicate still rejects it, or when the
operation tightens syntax and the predicate still allows it. When drift becomes
hard to test cheaply, move away from a separate precheck and toward a single
result-returning operation.

## 16. Observability signals

This dimension is engineering judgement.

What to record.

- A counter for the negative precheck branch, labelled by reason, caller, and
  product surface.
- A counter for residual exceptions from the risky operation, labelled
  separately from expected rejects.
- A ratio of precheck rejects to successful operations.
- A latency histogram for the precheck when it does more than an in-memory
  branch.
- A drift counter for cases where the precheck passed but the operation still
  failed with the formerly expected condition.
- A sample of rejected input shape, scrubbed of private data.

A healthy instance. The reject counter tracks user behavior or input mix, and
residual exceptions for the same condition are near zero. The precheck latency
is much lower than the risky operation. The ratio of rejects to successes moves
with known product changes, import batches, or traffic sources.

A failing instance. Rejects drop to zero while user-visible failures continue,
which means the metric was lost or the predicate stopped running. Residual
exceptions climb after the refactoring, which means the predicate is incomplete
or state is racing. Precheck latency rises until it matches operation latency,
which means the system is doing the expensive work twice. A single caller
produces most rejects, which points to a caller contract mismatch.

Dashboards should separate expected rejects from fault exceptions. This is
judgement. If both are on the same graph, a successful refactoring can look like
an incident rate drop while product rejects stay unchanged. If rejects are not
graphed anywhere, the team loses the ability to distinguish cleaner exception
handling from a real conversion improvement. The fallback branch is part of
normal behavior, so it deserves a normal product metric.

One privacy note for telemetry. Invalid values often include user input. Record
reason codes and coarse shape, not raw strings, file paths, tokens, email
addresses, or query text unless the product already treats that field as
auditable data.

## 17. Security and privacy implications

This dimension is engineering judgement, except for the Rust documentation
warning cited below.

The pattern can close one security gap and open another.

It closes a gap when it removes broad catch blocks. A broad catch can swallow an
authorization error, malformed input error, or dependency failure and return a
default that looks harmless. A narrow precheck for the expected case lets other
failures propagate to the boundary that can deny, roll back, or alert.

It opens a gap when the precheck answers an authorization or existence question
separately from the operation. A caller that checks "does this file exist" or
"can this user access account X" before use may leak existence through timing or
messages. It may also race with permission changes. Authorize and open, read,
write, or mutate in one protected operation when the resource matters.

Rust's standard library documentation is explicit that path existence checks
can introduce time-of-check to time-of-use bugs, and that `try_exists` does not
remove that class of bug
(https://doc.rust-lang.org/std/path/struct.Path.html, verified 2026-08-02).
That warning applies beyond Rust as a design lesson: a precheck on shared
external state is advisory unless the operation itself enforces the same rule.

Privacy also changes when exceptions disappear. Exceptions often carried stack
traces, messages, and values into logs. Removing expected exceptions may reduce
accidental capture of user input. Replacing them with explicit fallback metrics
can reintroduce the same risk if labels include raw rejected values. Keep labels
bounded and categorical.

Security review questions.

- Does the precheck reveal whether a protected resource exists?
- Can the checked state change before use?
- Does the negative branch return a default that could bypass authorization,
  quota, payment, or validation?
- Does the refactoring remove a log entry that incident response relied on?
- Does the new predicate duplicate validation logic that attackers can search
  for gaps?

## Code examples

Three languages are shown because the pattern appears in different idioms.
TypeScript shows the browser and server JavaScript shape with `URL.canParse`.
Python shows an extracted predicate for local immutable data. Rust shows a
precheck before an indexing operation that would otherwise panic.

### TypeScript

```typescript
function hostOrDefault(raw: string, fallback: string): string {
  if (!URL.canParse(raw)) {
    return fallback;
  }

  return new URL(raw).hostname;
}

console.log(hostOrDefault("https://example.com/docs", "invalid"));
console.log(hostOrDefault("not a url", "invalid"));
```

### Python

```python
def value_for_period(values: list[float], period_number: int) -> float:
    if not is_valid_index(values, period_number):
        return 0.0
    return values[period_number]


def is_valid_index(values: list[float], index: int) -> bool:
    return 0 <= index < len(values)


print(value_for_period([10.0, 20.0, 30.0], 1))
print(value_for_period([10.0, 20.0, 30.0], 9))
```

### Rust

```rust
fn value_for_period(values: &[f64], period_number: usize) -> f64 {
    if period_number >= values.len() {
        return 0.0;
    }
    values[period_number]
}

fn main() {
    let values = [10.0, 20.0, 30.0];
    println!("{}", value_for_period(&values, 1));
    println!("{}", value_for_period(&values, 9));
}
```

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, second
  edition, Addison-Wesley, 2018, catalog refactoring "Replace Exception with
  Precheck." Book page:
  https://martinfowler.com/books/refactoring.html, verified 2026-08-02.
- Martin Fowler, "Replace Exception with Precheck", public refactoring catalog,
  https://refactoring.com/catalog/replaceExceptionWithPrecheck.html, verified
  2026-08-02.
- Oracle, Java SE 21 API, `java.util.Iterator`, method details for `hasNext`
  and `next`,
  https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Iterator.html,
  verified 2026-08-02.
- Oracle, Java SE 18 API, `java.util.Scanner`, class documentation and numeric
  token methods,
  https://docs.oracle.com/en/java/javase/18/docs/api/java.base/java/util/Scanner.html,
  verified 2026-08-02.
- Microsoft Learn, .NET API documentation,
  `System.Collections.Generic.IDictionary<TKey,TValue>.TryGetValue`,
  https://learn.microsoft.com/en-us/dotnet/api/system.collections.generic.idictionary-2.trygetvalue,
  verified 2026-08-02.
- MDN Web Docs, "URL", static method `canParse` and constructor behavior,
  https://developer.mozilla.org/en-US/docs/Web/API/URL, verified 2026-08-02.
- Rust Standard Library, `std::path::Path`, methods `exists` and `try_exists`,
  https://doc.rust-lang.org/std/path/struct.Path.html, verified 2026-08-02.
