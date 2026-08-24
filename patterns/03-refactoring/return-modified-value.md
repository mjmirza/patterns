---
name: Return Modified Value
slug: return-modified-value
family: 03-refactoring
category: Composing Functions
aliases: [Return Updated Value, Return New Value, Accumulator Return]
first_described: "Fowler 2018"
maturity: established
related: [split-variable, extract-function, combine-functions-into-transform, replace-temp-with-query, separate-query-from-modifier]
incompatible_with: [command-query-separation]
verified: 2026-08-02
---

# Return Modified Value

## 1. Name, aliases, and lineage

The canonical name is Return Modified Value. Martin Fowler's online refactoring
catalog lists the refactoring under that name and shows a variable updated by a
nested helper being changed into a helper that calculates and returns the value
(https://refactoring.com/catalog/returnModifiedValue.html, verified
2026-08-02). The lineage is Martin Fowler, *Refactoring. Improving the Design
of Existing Code*, 2nd edition, Addison-Wesley, 2018, chapter 6, "A First Set
of Refactorings." Fowler's public notes on the second edition state that the
edition moved the examples to JavaScript and retained the catalog structure
while adding new refactorings (https://martinfowler.com/articles/refactoring-2nd-ed.html,
verified 2026-08-02).

The common aliases are not formal catalog names. **Return Updated Value** is
often used when the old code updates a record, collection, counter, or state
object. **Return New Value** is common in immutable code, where the function
does not mutate an object in place but returns the replacement. **Accumulator
Return** is common in loops, folds, and reducers, where each step receives the
current accumulator and returns the next one.

Judgement. The name is slightly misleading in languages and teams that reserve
"modified" for in-place mutation. The target state of the refactoring is a
value-producing function. The returned value may be a new object, a copied data
structure, a calculated scalar, or the same object after a deliberate local
mutation. What matters is that the caller gets the changed value through the
function boundary instead of through a hidden write to an outer variable,
argument, field, or global.

This entry treats Return Modified Value as a refactoring pattern, not as a
general command style. It is a local move used while cleaning code. It often
appears before Extract Function, Split Phase, Replace Temp with Query, or
Combine Functions into Transform. It is not a license to make every mutating
operation return `this`, nor is it a rejection of procedures that exist to
perform an effect.

## 2. Problem and context

A function changes a value that lives outside the function boundary. The code
works, but the data flow is hard to see. A reader must inspect the helper body
to learn which outer variable, argument, receiver field, or shared object
changed. When there are several helpers in one routine, the only way to know the
final value is to replay the writes mentally in execution order.

The smell often starts in long functions. A calculation begins with a local
variable such as `total`, `invoice`, `route`, `state`, `query`, or `builder`.
Several nested helpers or small procedures update it. The main routine reads
like a list of commands, but the commands are not independent. Each one secretly
relies on the result of the previous one. When a developer tries to extract one
helper, move it to another module, test it alone, or reorder steps, the hidden
write becomes the obstacle.

Return Modified Value changes the contract. The helper receives the current
value and returns the next value. The caller assigns the result. The mutation is
no longer inferred from the helper name or from a write hidden inside the
helper. It appears in the caller as a visible data-flow edge.

Before:

```text
let total = 0;
for (const line of lines) {
  addLineCharge(line);
}

function addLineCharge(line: Line): void {
  total += line.quantity * line.price;
}
```

After:

```text
let total = 0;
for (const line of lines) {
  total = addLineCharge(total, line);
}

function addLineCharge(current: number, line: Line): number {
  return current + line.quantity * line.price;
}
```

The context that makes this useful has three traits. First, the value being
changed is part of a calculation or transformation, not a resource effect such
as sending an email. Second, the caller needs the changed value after the helper
runs. Third, the helper can be made honest about that value without widening its
contract to include unrelated data. If those traits are absent, the refactoring
may turn clear command code into ceremony.

The pattern is common in state update APIs. Redux documents reducers as
functions from current state and action to new state, written as
`(state, action) => newState`, and its rules tell reducers not to mutate the
existing state (https://redux.js.org/tutorials/fundamentals/part-3-state-actions-reducers,
verified 2026-08-02). Immer documents `produce` as applying changes to a draft
while leaving the base state untouched and returning a next state that reflects
the draft changes (https://immerjs.github.io/immer/produce/, verified
2026-08-02). Those APIs are not Fowler's refactoring, but they show the same
design pressure at a system boundary. Make the changed value explicit.

## 3. Forces

Judgement. These forces are engineering trade-offs, not historical claims. Their
weight depends on language, performance profile, and team habits.

- **Coupling.** The refactoring lowers coupling to ambient state. A helper that
  returns a value can move to another module with fewer captured variables. It
  can raise coupling at the call site because the caller now names the value and
  the assignment order.
- **Consistency.** It favors consistency of data flow. Every step receives a
  current value and returns the next value. It sacrifices the compactness of
  command-style code where the target object is obvious.
- **Cognitive load.** It lowers load for readers tracing one value through a
  routine. It raises load when a function returns a large object and the reader
  must know whether the object is a copy, a mutated original, or a persistent
  structure sharing memory with the old one.
- **Latency.** It is neutral for scalars and references. It can add allocation
  when the refactoring is paired with immutable copies of large structures. It
  can improve latency in code where the explicit return exposes a fold, stream,
  or vectorized operation that the runtime can optimize.
- **Operability.** It improves local debug output because each returned value
  can be logged, inspected, or traced at the assignment point. It can make logs
  noisy when every small update emits a value.
- **Cost of change.** It favors later extraction, movement, and testing. It
  sacrifices the short-term cost of touching every call in a chain, because each
  helper must now have a return type and each caller must assign it.
- **Team topology.** It favors teams that split transformation logic across
  modules. A value-returning function has a contract that can be reviewed,
  documented, and versioned. It is less valuable in a tiny codebase where the
  helper will never leave its parent routine.
- **Error handling.** It favors typed result channels. A function can return
  the new value or an error-bearing result. It can conflict with languages or
  APIs where callers ignore return values by default.

The central exchange is visibility against brevity. The old form hides the
write and keeps the caller compact. The new form exposes the write and makes the
caller carry the data-flow structure.

## 4. Applicability and non-applicability

Reach for Return Modified Value when the following conditions hold.

- A helper changes a local variable in an enclosing function, and the changed
  value is read later.
- A helper mutates an argument, but the caller treats that argument as the next
  version of a calculation rather than as a shared resource.
- A function is being prepared for Extract Function, Move Function, Split Phase,
  Replace Temp with Query, or Combine Functions into Transform.
- A sequence of update steps needs clear ordering because each step depends on
  the previous value.
- A value is being accumulated through a loop, and the current loop body writes
  to an outer accumulator.
- A state update should become testable as an ordinary function from old state
  to new state.
- A function currently returns nothing, but its only meaningful effect is the
  changed value.

Do NOT reach for it in these cases.

- **The operation's purpose is an external effect.** Sending a message, writing
  a file, deleting a row, publishing an event, and committing a transaction are
  commands. Returning the target value can imply a calculation where the real
  contract is an effect plus failure handling.
- **The returned value would be ignored by most callers.** An ignored return is
  worse than an explicit `void` command. It creates the false impression that
  the caller has accepted a new value.
- **The value is a mutable shared owner.** Returning a modified global cache,
  shared connection pool, or singleton does not make the mutation local. It may
  hide aliasing under a cleaner signature.
- **The object already has a fluent command API by design.** Builders and query
  builders often return the receiver to support chaining. Recasting that as
  Return Modified Value adds no clarity unless each call returns a new logical
  value.
- **The function needs to update several independent outputs.** Multiple return
  values or an explicit result object may be right, but forcing unrelated
  outputs into one "modified value" blurs the contract.
- **The caller cannot safely replace its reference.** Identity-sensitive objects
  registered in maps, UI frameworks, or native handles may require in-place
  mutation. Returning a replacement can break identity contracts.
- **The language or framework treats return values specially.** A callback whose
  return value controls propagation, retry, or cancellation should not use that
  channel for an unrelated modified value.
- **The change is pure renaming, not data-flow repair.** If a helper already
  returns its result and the caller already assigns it, changing names to match
  the catalog buys nothing.

## 5. Structure

The structure has five participants.

- **Current value.** The value before the step runs. It may be a scalar, record,
  collection, domain object, state object, accumulator, or builder.
- **Updater function.** The function that calculates the next value. After the
  refactoring it receives the current value as a parameter or reads it from a
  narrow receiver, and it returns the next value.
- **Next value.** The value the caller should use after the updater finishes.
  It may be a new object, a copied value, or a deliberately mutated object
  returned to show ownership.
- **Caller assignment.** The statement that replaces the old binding with the
  returned value. This is the visible proof that the caller accepts the update.
- **Downstream reader.** Later code that consumes the next value. This
  participant is why the refactoring matters. If nobody reads the value, the
  update is either dead code or an effect.

The relationships are simple. The caller owns the binding. The updater owns the
calculation. The caller passes the current value into the updater and assigns
the returned next value. Downstream code reads the binding after the assignment.

There are two common ownership variants. In the immutable variant, the updater
returns a distinct value and the old value remains valid. In the mutable-return
variant, the updater mutates the object it received and returns the same object
so the call chain or assignment makes the modified target explicit. Judgement.
Prefer the immutable variant when the value is small enough, shared enough, or
important enough to audit. Prefer the mutable-return variant only when identity,
memory pressure, or an existing API makes copying a poor fit.

## 6. ASCII structure diagram

```text
Before

  +-----------------------+
  | Caller                |
  |-----------------------|
  | current = initial     |
  | updateStep()          |
  | read current          |
  +-----------+-----------+
              |
              | hidden write through closure, field, or argument
              v
  +-----------------------+
  | Updater function      |
  |-----------------------|
  | current = changed     |
  | return void           |
  +-----------------------+

After

  +-----------------------+        +-----------------------+
  | Caller                |        | Updater function      |
  |-----------------------|        |-----------------------|
  | current = initial     | -----> | next = f(current)     |
  | current = update(...) | <----- | return next           |
  | read current          |        +-----------------------+
  +-----------------------+

  The write moves from the updater body to the caller assignment.
  The updater owns calculation. The caller owns the binding.
```

## 7. Dynamics

At runtime the old code changes state through a side channel. The new code
passes the value through the call boundary and makes each transition visible.

```text
Caller                 Updater                    Downstream reader
  |                       |                              |
  | current = initial     |                              |
  |                       |                              |
  | update(current) ----> |                              |
  |                       | compute next                 |
  |                       | return next                  |
  | <-------------------- |                              |
  | current = next        |                              |
  |                       |                              |
  | read current --------------------------------------> |
  |                       |                              |

Loop form

  current0
     |
     v
  step(current0, item1) -> current1
     |
     v
  step(current1, item2) -> current2
     |
     v
  step(current2, item3) -> current3
```

The dynamics matter most during extraction. Once a helper returns the modified
value, the helper can be moved without carrying a reference to the caller's
local variable. The caller becomes the only place where sequencing is expressed.
That makes reordering reviewable. It also makes a missing assignment easy to
spot in languages and linters that warn on ignored return values.

There is a concurrency effect. Hidden mutation can cross thread, task, actor,
or coroutine boundaries without being visible at the call site. Returning the
next value does not solve concurrency by itself, but it narrows the surface. The
caller can decide when to publish the new value, whether to hold a lock, and
whether to compare-and-swap before replacing shared state.

## 8. Implementation variants

**Scalar accumulator return.** A number, boolean, enum, or string is threaded
through a loop. This is the smallest form. It is cheap, highly readable, and
maps well to `reduce` or `fold`. Java's `Stream.reduce` documentation presents
the operation as repeatedly assigning `result = accumulator.apply(result,
element)` and returning the result (https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Stream.html,
verified 2026-08-02). MDN describes JavaScript `Array.prototype.reduce` as
passing the previous callback return value into the next callback and returning
the final value (https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/reduce,
verified 2026-08-02).

**Immutable record copy.** The updater returns a new record with selected fields
changed. Python's `dataclasses.replace` creates a new object of the same type
with specified fields replaced (https://docs.python.org/3/library/dataclasses.html#dataclasses.replace,
verified 2026-08-02). This variant is clear and audit-friendly, but it can add
allocation and may require care for nested mutable fields.

**Mutable object returned for ownership clarity.** The updater changes the
object it receives and returns it. This is common when the object is a builder,
buffer, parser state, or large collection where copying would dominate the
work. The risk is aliasing. A returned mutated object is still mutated for every
other alias.

**Tuple or result object return.** The updater returns the modified value plus
metadata such as warnings, counts, or a cursor. This is useful when the extra
output is part of the update contract. It becomes misuse when unrelated values
are bundled because the function needed a second output.

**Error-bearing return.** Languages with `Result`, `Either`, checked
exceptions, or ordinary exception flow can pair the next value with failure. In
Rust the idiom is often `fn step(value, input) -> Result<Value, Error>`, so the
caller cannot read the next value until it handles failure.

**Reducer callback.** A framework calls the updater repeatedly. The callback
does not modify an outer binding. It returns the next accumulator or state for
the framework to pass onward. Redux reducers and JavaScript array reduction are
well-known examples of this shape.

**Persistent data structure return.** The updater returns a new logical value
that shares unchanged internal structure with the old value. This variant gives
immutable semantics while reducing copy cost. It requires a library or language
runtime that supports structural sharing.

**Fluent receiver return.** A method mutates `self` or `this` and returns the
receiver. Judgement. Treat this as a neighboring idiom, not the preferred form
of the refactoring. It is sound for builders where every method participates in
one construction flow. It is poor for domain commands because callers may chain
effects without checking intermediate validity.

## 9. Known production uses

**Redux reducer contract.** Redux documents reducers as functions that take
current `state` and an `action`, then return a new state result. The same page
says reducers are not allowed to modify the existing state and should make
immutable updates by copying and changing copies
(https://redux.js.org/tutorials/fundamentals/part-3-state-actions-reducers,
verified 2026-08-02). This is Return Modified Value at the application state
boundary. The changed state is not hidden in a captured variable. It is the
return value.

**Immer `produce`.** Immer documents `produce` as taking a base state and a
recipe that mutates a draft, while the base state remains untouched and the next
state reflects the draft changes (https://immerjs.github.io/immer/produce/,
verified 2026-08-02). This is a production library form of the pattern with a
proxy-backed implementation. The programmer writes local mutation syntax, but
the API returns the modified value as the next state.

**Python `dataclasses.replace`.** The Python standard library documents
`dataclasses.replace` as creating a new object of the same type with specified
fields replaced, and it creates that object through the dataclass initializer
(https://docs.python.org/3/library/dataclasses.html#dataclasses.replace,
verified 2026-08-02). This is the record-copy variant. Callers do not pass an
object to be patched in place. They receive the updated object.

**Java Stream `reduce`.** The Java SE 21 API documents `Stream.reduce(identity,
accumulator)` as a reduction that returns the reduced value, and its equivalent
sequential form assigns each accumulator result back to `result` before
returning it (https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Stream.html,
verified 2026-08-02). This is the accumulator-return variant formalized as a
standard library operation.

**JavaScript `Array.prototype.reduce`.** MDN documents `reduce` as passing the
callback's previous return value into the next callback and returning the final
accumulated value (https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/reduce,
verified 2026-08-02). It is the everyday JavaScript form of Return Modified
Value for loop accumulators.

## 10. Consequences

Positive.

- Data flow becomes explicit at the call site. The caller shows where the value
  changes and what later code reads.
- Helpers become easier to extract, move, and test because they no longer need
  access to a caller's local variable.
- State updates become easier to compare in tests. A test can call the updater,
  inspect the returned value, and leave the input unchanged when the immutable
  variant is used.
- The refactoring often exposes a loop as a fold or reducer, which can make the
  structure of an accumulation clearer.
- Error handling can become cleaner because the update result can be wrapped in
  a typed result rather than partly applied before failure.
- Debugging improves when each intermediate value has a name at the assignment
  point.

Negative.

- Call sites become more verbose. A chain of steps now has repeated assignment
  statements.
- The return type becomes part of the public contract. Changing what is returned
  can ripple through callers.
- Immutable copies can add allocation, especially for large nested data.
- Mutable-return variants can create false confidence. Returning the object does
  not remove aliases or shared mutation.
- Callers can ignore the returned value in languages without warnings, causing
  the update to vanish.
- Multiple changed outputs can push the design toward broad result objects that
  hide unrelated concerns under one return.

Judgement. The strongest benefit is not purity by itself. It is local reasoning.
When a reader sees `state = applyDiscount(state, rule)`, the old and new states
are connected in one line. When the helper returns `void`, the reader must open
the helper to learn whether `state` changed.

## 11. Failure modes and misuse

**Ignored return.** Symptom. A test shows no change after a helper call even
though the helper body calculates the right next value. Cause. The caller calls
`update(value)` but forgets `value = update(value)`. Fix. Assign the return
value, make the language or linter warn on unused results, or keep the old
command form if callers are meant to ignore the result.

**Half-migrated mutation.** Symptom. The caller assigns the returned value, but
another local variable, field, or argument still changes inside the helper.
Cause. The refactoring moved the main value to the return channel while leaving
secondary hidden writes behind. Fix. Repeat the refactoring for each changed
value, introduce a result object for related outputs, or split the effectful
work into a command.

**Copy that is not deep enough.** Symptom. The old and new records compare
different at the top level, yet editing a nested list in the new record changes
the old one. Cause. The immutable-looking updater copied the outer object but
shared mutable children. Fix. Copy the changed nested levels, use persistent
data structures, or document the return as a shallow copy and keep it out of
shared contexts.

**Mutable return mistaken for immutable return.** Symptom. A caller stores the
old value for audit or rollback, then discovers that old and new point to the
same changed object. Cause. The updater mutates the input and returns it, but
the name or type suggests a new value. Fix. Rename to command language such as
`mutateInPlace`, return a distinct copy, or add a test asserting object identity
where it matters.

**Accumulator becomes a dumping ground.** Symptom. A small number accumulator
turns into a large record containing flags, logs, counters, partial results, and
temporary parser details. Cause. Every helper needed one more output, and all
outputs were pushed into the modified value. Fix. Split phases, separate
domain result from diagnostics, or introduce a narrow context object with clear
ownership.

**Performance regression from copying.** Symptom. CPU and allocation profiles
show the updater spending most time cloning arrays, maps, or records. Cause.
The refactoring was paired with whole-object copying on a large nested
structure. Fix. Copy only changed branches, use a persistent collection, keep
an internal mutable builder and return an immutable result at the boundary, or
measure whether in-place mutation is the right local contract.

**Command-query confusion.** Symptom. A method called in an expression also
changes external state, making repeated calls produce different results. Cause.
The design mixed a returned value with unrelated side effects. Fix. Split the
query from the modifier, or make the side effect the named contract and remove
the value return.

**Lost validation step.** Symptom. The returned value is accepted by downstream
code although required invariants no longer hold. Cause. The old mutation
occurred through a setter or method that validated, while the new copy path
reconstructed fields directly. Fix. Route returned values through constructors,
smart constructors, or validation functions that preserve invariants.

## 12. Trade-off matrix

| Force | Return Modified Value | Command Procedure | Mutable Builder | Reducer or Fold | Combine Functions into Transform | Replace Temp with Query |
|---|---|---|---|---|---|---|
| Coupling to ambient state | Low. Changed value crosses return boundary | High when procedure writes outer state | Medium. Builder owns mutable state | Low. Framework threads accumulator | Low. Transform owns data flow | Low for derived value |
| Call-site clarity | High. Assignment shows update | Medium. Name must reveal effect | Medium. Chain can hide steps | High for accumulations | High for phased transforms | High for repeated queries |
| Cognitive load | Medium. Reader tracks returned value | Low for simple effects, high for hidden writes | Medium. Reader tracks builder identity | Medium. Reader must know fold contract | Medium to high | Low when query is cheap |
| Allocation cost | Low for scalars, variable for copies | Low | Low until final output | Low to medium | Medium for copied records | Variable by recomputation |
| Error handling | Good with result types | Good with exceptions or status | Often delayed until build | Good when accumulator type includes errors | Good when transform result carries diagnostics | Poor when errors need context |
| Team topology | Good for shared update helpers | Poor when shared procedure owns many effects | Good inside one construction module | Good for library callbacks | Good for pipelines | Good inside one module |
| Operability | Good. Intermediate values can be logged | Mixed. Effects need custom logging | Mixed. Final state visible, internals hidden | Good for per-step metrics | Good for phase metrics | Neutral |
| Best fit | Local data-flow repair | External effects | Constructing complex objects | Accumulating over collections | Batch transformation | Replacing a derived temp |
| Main risk | Ignored return or copy cost | Hidden coupling | Aliasing and invalid mid-build state | Over-clever callback | Oversized transform object | Repeated expensive work |

Reading of the table. Return Modified Value is strongest when the code already
has a single logical value flowing through steps. Command Procedure wins when
the operation exists for an effect. Mutable Builder wins while assembling a
complex object under one owner. Reducer or Fold wins when the update is
naturally one step per element. Combine Functions into Transform wins when
several derived values belong to one transformation pass. Replace Temp with
Query wins when the modified value is only a cached derivation.

## 13. Related and incompatible patterns

- **Extract Function.** Return Modified Value often prepares for it. A helper
  that writes to an outer variable cannot move cleanly. Once it returns the
  changed value, extraction has a narrow signature.
- **Split Variable.** Composes before it. If one variable is reused for separate
  meanings, returning it from helpers will preserve confusion. Split the
  meanings first, then return the modified value for the one true flow.
- **Replace Temp with Query.** Sometimes replaces it. If the "modified" value is
  a derivation that can be recomputed from stable inputs, a query may remove the
  assignment altogether.
- **Combine Functions into Transform.** Composes above it. Several functions
  that return updated versions of the same record may become one named
  transform when they form a phase.
- **Separate Query from Modifier.** Can conflict. Return Modified Value is safe
  when the returned value is the modification. It conflicts when a function both
  returns a query result and performs an unrelated side effect.
- **Command.** Replaces it when the operation is effectful, undoable, queued, or
  auditable as an action. In that case the command result may be status rather
  than a modified value.
- **Builder.** A neighboring idiom. Builders often return the receiver for
  chaining, but the builder's real contract is staged construction. Use Return
  Modified Value language only when each call returns a new logical value or
  when assignment visibility matters.
- **Pipeline and Pipes and Filters.** Composes at a larger scale. Each stage
  receives the current value and returns the next. Return Modified Value is the
  small refactoring that can reveal that shape.
- **Immutable Value Object.** Supports the immutable variant. Returning a new
  value is clearer when the type itself makes mutation impossible.

## 14. Refactoring path in and out

Introducing the refactoring.

1. Identify the value being changed. Name exactly one binding, argument, field,
   or accumulator that the helper changes and the caller later reads.
2. Add a local variable inside the helper for the next value. Compute into that
   variable instead of writing directly to the outer target.
3. Return the next value from the helper. Keep the old hidden write for one
   small step only if needed to make tests pass during the transition.
4. Change the caller to assign the returned value to the original binding.
5. Remove the hidden write from the helper. The helper should now receive the
   current value and return the next value.
6. Run tests. Add a focused test that calls the helper with a known current
   value and asserts the returned next value.
7. If the helper still reads other outer variables, pass them as parameters or
   decide that they are stable context owned by a receiver.
8. If several helpers now form a chain, consider extracting a transform or
   reducer only after the single refactoring is complete.

Mechanical example.

```text
1. total = 0; addFee(); read total
2. addFee() computes nextTotal
3. addFee() returns nextTotal
4. total = addFee(total)
5. addFee no longer writes outer total
```

Removing the refactoring when it stops earning its place.

1. Find callers that always ignore, discard, or immediately overwrite the
   returned value. That is evidence the return channel is not the real contract.
2. If the function performs an external effect, rename it as a command and
   return status, error, or nothing according to local style.
3. If the function returns the same mutable receiver for chaining, decide
   whether it is a builder. If not, change it to `void` and make mutation
   explicit in the method name.
4. If the returned value is a pure derivation from inputs, replace the stored
   update with a query.
5. If the function returns several loosely related values, split it into
   smaller functions or introduce a named result type for the related group.
6. Delete compatibility overloads after downstream callers move to the clearer
   contract.

Cross references in this family: Extract Function, Split Variable, Replace Temp
with Query, Combine Functions into Transform, Replace Query with Parameter, and
Replace Function with Command. The direction depends on whether the code is a
calculation, a transform, or a command.

## 15. Testing and verification

Judgement. The testing payoff is the main reason to do the refactoring in
business logic. A value-returning helper can be tested without a fixture that
recreates the caller's mutable environment.

What becomes easier.

- **Example tests.** Pass a current value and inputs, assert the returned next
  value. No spy is needed to see a hidden write.
- **Regression tests for sequencing.** Test a chain as `v1 = step1(v0)`, `v2 =
  step2(v1)`, then assert `v2`. The test mirrors the production data flow.
- **Property tests.** State invariants can be checked across many generated
  inputs because the function has an ordinary input-output contract.
- **Golden tests.** For record transforms, store the expected returned record
  and compare it with the actual one.
- **Mutation guards.** In languages with freezing, readonly types, or identity
  assertions, test that the old value was not changed when the immutable
  variant is promised.

What becomes harder.

- **Identity expectations.** Tests must state whether the returned value should
  be the same object or a distinct object. Omitting that assertion leaves room
  for aliasing defects.
- **Performance coverage.** Copying large structures may need allocation tests
  or benchmarks, because functional correctness tests will pass while memory
  use rises.
- **Effect separation.** If the old helper both changed a value and performed an
  effect, tests must cover both after the split.

Useful techniques.

- In TypeScript, enable lint rules that flag unused expressions or ignored
  promises, then treat ignored update returns as review findings.
- In Python, compare both equality and identity where copy semantics matter.
- In Java, use immutable records or value objects in tests so accidental
  mutation fails early.
- In Go, write table tests that pass the current value and compare the returned
  value. For pointer returns, include an aliasing case.
- In Rust, prefer ownership-moving signatures for values that should not be
  reused after update. The compiler then helps prevent reads from stale values.

Verification checklist for the refactoring.

- The helper no longer writes the old outer variable.
- The caller assigns the helper return before reading the value.
- Tests fail if the assignment is removed.
- The function name says whether it returns a new value or mutates and returns
  the same value.
- Copy depth is covered for nested mutable data.

## 16. Observability signals

Judgement. This is a local code refactoring, so production telemetry should be
selective. Do not log every small value update in a hot loop.

Useful signals when the update is business-visible.

- Count calls to the updater by operation name and outcome. A sudden drop means
  a branch stopped using the updater. A sudden rise means a loop or retry path
  may be applying it too often.
- Record a small, non-sensitive summary of the input and returned value, such as
  state version, item count, total cents, rule id, or validation status.
- Trace phase boundaries when several returned values form a pipeline. Each
  span should name the step and carry the old and new version identifiers.
- For immutable copies of large structures, measure allocation size, object
  count, and update duration.
- For mutable-return variants, count identity-preserving updates separately from
  copy-returning updates where the distinction matters.

A healthy dashboard shows stable update counts, small and predictable duration,
and returned value summaries that match the input mix. For example, a pricing
step should show one returned invoice per accepted order, not several returned
invoices per line item unless that is the chosen granularity.

A failing dashboard shows repeated updates for the same correlation id, a
returned version that fails to advance, a high rate of discarded results, or
allocation growth after a release that converted in-place updates to copies. A
trace where `step2` reads version `1` after `step1` returned version `2` points
to a missing assignment or a stale alias.

Logging guidance. Log identifiers and summaries, not full returned objects.
Returned values often contain customer data. Redact or hash fields that would
identify a person, tenant, token, or document. When the returned value is large,
log size and checksum rather than content.

## 17. Security and privacy implications

Judgement. Return Modified Value is mostly silent on security. It does not
authenticate, authorize, encrypt, validate input, or isolate tenants by itself.
Its security effect comes from making state transitions easier to review.

Security gains.

- A value-returning update can be wrapped with validation at the boundary. The
  caller can reject the returned value before publishing it to shared state.
- Pure or immutable updates reduce accidental shared-state corruption. That
  helps in authorization, quota, and billing code where stale or partially
  mutated state can become a defect.
- Explicit returned values are easier to audit in tests. Security rules can be
  expressed as invariants over old value, input, and new value.

Security risks.

- A returned object may bypass setters, constructors, or validation paths that
  the old mutation used. Preserve invariants when moving to copy-returning code.
- A mutable-return helper can hide shared mutation behind a clean signature.
  Attackers do not care whether a corrupted object arrived by return value or
  by side effect.
- An ignored returned value in authorization or quota code can leave stale state
  in force. Use linting, types, or review rules for high-risk update paths.
- Logging returned values can leak personal data, access tokens, document text,
  tenant ids, or inferred business facts. Log summaries and identifiers with the
  same privacy controls used for the underlying data.

Privacy implication. The pattern encourages naming intermediate states. That is
good for review, but it can tempt teams to log full before-and-after snapshots.
Before-and-after logs are often more sensitive than a single event because they
reveal changed fields. Keep snapshots in test fixtures, not production logs,
unless there is a retention policy and a clear access boundary.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 6, "A First Set of Refactorings."
- Martin Fowler, "Return Modified Value," refactoring catalog,
  https://refactoring.com/catalog/returnModifiedValue.html, verified
  2026-08-02.
- Martin Fowler, "The Second Edition of Refactoring,"
  https://martinfowler.com/articles/refactoring-2nd-ed.html, verified
  2026-08-02.
- Redux documentation, "Redux Fundamentals, Part 3. State, Actions, and
  Reducers,"
  https://redux.js.org/tutorials/fundamentals/part-3-state-actions-reducers,
  verified 2026-08-02.
- Immer documentation, "Using produce,"
  https://immerjs.github.io/immer/produce/, verified 2026-08-02.
- Python Software Foundation, Python 3.14 documentation, `dataclasses.replace`,
  https://docs.python.org/3/library/dataclasses.html#dataclasses.replace,
  verified 2026-08-02.
- Oracle, Java SE 21 API documentation, `java.util.stream.Stream`,
  https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Stream.html,
  verified 2026-08-02.
- MDN Web Docs, "Array.prototype.reduce,"
  https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/reduce,
  verified 2026-08-02.

## Code examples

The examples use TypeScript, Python, Go, and Rust. They are small on purpose.
Each one shows a helper returning the value it changes so the caller owns the
binding. TypeScript and Python show accumulator and record-copy styles. Go shows
the idiomatic explicit return used in table-tested business logic. Rust shows
an ownership-moving update where stale reads are rejected by the type system.

### TypeScript

```typescript
type Line = { sku: string; quantity: number; cents: number };
type Invoice = { subtotal: number; skus: string[] };

function addLine(invoice: Invoice, line: Line): Invoice {
  return {
    subtotal: invoice.subtotal + line.quantity * line.cents,
    skus: [...invoice.skus, line.sku],
  };
}

function price(lines: Line[]): Invoice {
  let invoice: Invoice = { subtotal: 0, skus: [] };
  for (const line of lines) {
    invoice = addLine(invoice, line);
  }
  return invoice;
}

console.log(price([{ sku: "A", quantity: 2, cents: 150 }]));
```

### Python

```python
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Route:
    distance: int
    stops: tuple[str, ...]


def add_stop(route: Route, stop: str, distance: int) -> Route:
    return replace(
        route,
        distance=route.distance + distance,
        stops=route.stops + (stop,),
    )


route = Route(distance=0, stops=())
route = add_stop(route, "AMS", 12)
route = add_stop(route, "BER", 31)
print(route)
```

### Go

```go
package main

import "fmt"

type Cart struct {
	Items []string
	Cents int
}

func AddItem(cart Cart, sku string, cents int) Cart {
	nextItems := append([]string{}, cart.Items...)
	nextItems = append(nextItems, sku)
	return Cart{Items: nextItems, Cents: cart.Cents + cents}
}

func main() {
	cart := Cart{}
	cart = AddItem(cart, "notebook", 450)
	cart = AddItem(cart, "pen", 125)
	fmt.Println(cart.Cents, cart.Items)
}
```

### Rust

```rust
#[derive(Debug)]
struct Basket {
    cents: i32,
    skus: Vec<String>,
}

fn add_item(mut basket: Basket, sku: &str, cents: i32) -> Basket {
    basket.cents += cents;
    basket.skus.push(sku.to_string());
    basket
}

fn main() {
    let mut basket = Basket {
        cents: 0,
        skus: Vec::new(),
    };
    basket = add_item(basket, "notebook", 450);
    basket = add_item(basket, "pen", 125);
    println!("{} {:?}", basket.cents, basket.skus);
}
```

### Swift

```swift
struct Basket: CustomStringConvertible {
    let cents: Int
    let skus: [String]

    var description: String {
        "\(cents) \(skus)"
    }
}

func addItem(_ basket: Basket, sku: String, cents: Int) -> Basket {
    Basket(cents: basket.cents + cents, skus: basket.skus + [sku])
}

var basket = Basket(cents: 0, skus: [])
basket = addItem(basket, sku: "notebook", cents: 450)
basket = addItem(basket, sku: "pen", cents: 125)
print(basket)
```
