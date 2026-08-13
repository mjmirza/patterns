---
name: Change Function Declaration
slug: change-function-declaration
family: 03-refactoring
category: Refactoring
aliases: [Rename Method, Rename Function, Change Signature, Change Parameter List]
first_described: "Fowler 1999"
maturity: canonical
related: [extract-function, inline-function, parameterize-function, rename-variable, introduce-parameter-object]
incompatible_with: []
verified: 2026-08-13
---

# Change Function Declaration

## 1. Name, aliases, and lineage

The canonical name is **Change Function Declaration**, introduced by Martin
Fowler in *Refactoring. Improving the Design of Existing Code*, 2nd edition,
Addison-Wesley, 2018, chapter 6, "A First Set of Refactorings." In the first
edition of the same book (1999), the same operation appeared under two
separate names, **Rename Method** and **Add Parameter** / **Remove
Parameter**, each with its own catalog entry. Fowler consolidated them into a
single refactoring in the second edition because the mechanical steps are
identical regardless of whether you are changing the name, the parameter
list, or both at once.

The broader idea that names are load bearing and that bad names actively
harm comprehension predates Fowler. Kent Beck, in *Smalltalk Best Practice
Patterns*, Prentice Hall, 1997, treats intention revealing names as a
first-class pattern and writes that a method name should communicate what the
caller gets back, not how the method computes it. Fowler credits Beck's
influence on the "Intention Revealing Names" pattern in the same chapter
that introduces this refactoring.

The alternative name **Change Signature** comes from the IntelliJ IDEA
refactoring menu and has entered common usage through that tool, but the
operation is the same. The name **Rename Function** is the JavaScript and
Python community's preferred label because those languages do not attach
methods to classes the way Java and C sharp do, so "method" is less
natural than "function." This entry uses Fowler's canonical name throughout.

## 2. Problem and context

A function's declaration, its name and its parameter list, is the single
contract every caller depends on. When the name does not communicate what the
function does, or when the parameter list does not match what the function
actually needs to do its job, every caller is paying a comprehension cost on
every read and every modification is harder than it should be because the
signature lies about the function's intent.

The situation reads like this in a real codebase. A function called
`processData` was written to extract a specific field from a JSON payload and
return it as a string. The name was accurate when the function was first
written, because at that point "process" was an honest description of the
one transformation happening. Over six months the function gained
validation, normalisation, truncation, and a side effect of writing an audit
log. The name still says "process data," which now communicates nothing
about any of those responsibilities. A new reader calling the function
expects it to do what its name says and is surprised by the audit log. A
maintainer editing the function has to read every call site to understand
which callers depend on the side effects and which ones only care about the
return value.

The same problem applies to parameters. A function takes a `userId` as an
integer because that was the type used in the original database schema. The
schema migrated to UUIDs. The function now receives a UUID, converts it to
the old integer form internally via a lookup, and proceeds. The parameter
type communicates the old world, not the current one. Every caller has to
convert before calling, and every conversion is a place a bug can enter.

## 3. Forces

**Communication cost versus verification cost.** A comment is the cheapest
possible way to communicate intent, cheaper than a test, cheaper than a
rename, cheaper than an architecture decision record. That cheapness is
precisely the force that produces the smell, because cheap communication is
also unverified communication, and the two properties cannot be separated in
a function declaration as a medium. A rename favours communication accuracy
and sacrifices stability.

**What versus why.** A function name describing what code does is redundant
the instant a reader can read the code itself, and it is a maintenance
liability forever after, because every future edit to the code must also
edit the name or the two diverge. A function name describing why a decision
was made, why an obvious looking alternative was rejected, why a workaround
exists for an external constraint, cannot be recovered by reading the code no
matter how well the code is written, because code expresses mechanism, not
motive. This is the single force that most determines whether a specific
name belongs to this smell or is legitimate documentation, and it recurs
through every other dimension of this entry.

**Local clarity versus global truth maintenance.** A name written at the
point of authorship is, almost by definition, locally clear to the person who
wrote it, because they hold the full context in their head at that moment.
The same name's clarity to a future reader depends entirely on whether the
surrounding code has changed since, a fact the author cannot control and the
name itself cannot signal. This is a design forces trade off, not a
character flaw in any individual engineer, because the same engineer who
writes an accurate name on Monday cannot force their Friday self, let alone
a colleague six months later, to notice that a later edit invalidated it.

**Contract stability versus evolution.** A function that is part of a public
API or a published library contract cannot be freely renamed without
breaking consumers. The force sacrifices evolution speed for contract
stability, which is the right trade for a published library and the wrong
trade for an internal codebase where the compiler or test suite catches every
call site in seconds. Where the function sits on this spectrum determines
how much ceremony the change requires.

**Parameter count versus parameter cohesion.** Adding a parameter to handle
a new case is cheap in the moment but pushes the function toward parameter
lists that are hard to read and easy to get wrong at call sites. The force
that pushes toward more parameters is the same force that pushes toward the
Introduce Parameter Object refactoring, which groups related parameters into a
single value object. The two refactorings are complementary, not
conflicting.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- The function name does not communicate what the function does, or
  communicates it inaccurately, and a reader must open the body to learn the
  intent. A name that requires reading the body to confirm has already failed
  at its job.
- A parameter's type or name is misleading. An integer parameter called
  `count` that actually receives a bit mask is a parameter whose declaration
  is actively harmful.
- The parameter list has grown past the point where a caller can remember
  the order, which in practice means more than three or four parameters of
  the same type, where passing them in the wrong order compiles but produces
  wrong behaviour.
- The function has a side effect its name does not advertise, and the name
  can be changed to advertise it, for example from `getTotal` to
  `getTotalAndLogAudit`. Fowler treats this as a legitimate application in
  the same chapter.
- The function is called from a small number of places, all within the same
  repository, and a compiler or test suite will catch every call site
  immediately.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The function is part of a published public API and consumers you do not
  control depend on the current name. In that case the correct path is a
  deprecation cycle, not a rename, because an immediate rename breaks
  consumers silently if the language does not have a compile time check on
  external callers.
- The function name is bad because the function itself does too many things.
  The fix is Extract Function, not a better name for an oversized body,
  because no honest name can describe a function that does five unrelated
  things.
- The parameter list is long because the function is doing the work of
  several functions. Adding a parameter object to a function that should be
  split is papering over the real problem.
- The rename is cosmetic, for example matching a style preference about verb
  tense, and the current name is not actively misleading. The call site churn
  is real cost with no comprehension benefit, and the refactoring is not
  worth its risk in that case.

## 5. Structure

The refactoring has two participants and one invariant.

- **The declaration.** The function's current name, parameter list, and
  return type. This is the contract every call site depends on.
- **The call sites.** Every location in the codebase that invokes the
  function by its current name and passes arguments matching the current
  parameter list.
- **The invariant.** After the refactoring, every call site must invoke the
  function by its new name and pass arguments matching the new parameter
  list, and the function's behaviour must be identical to what it was before.

The refactoring is mechanical. Find every call site, update each one to use
the new declaration, and delete the old declaration when the last call site
is migrated. The difficulty is not in the mechanics but in finding every
call site, which is trivial when a compiler can do it and hard when it
cannot, for example in dynamically typed languages or when the function is
called via reflection or string based dispatch.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER
  --------                            --------

  function oldName(p1, p2) {          function betterName(p1, p2, p3) {
    // ...                               // ...
  }                                   }

  caller:                             caller:
    oldName(a, b)                       betterName(a, b, c)

  CALL SITES (n)                      CALL SITES (n)
  +-----------+                       +-----------+
  | each must |  -- update -->        | each now  |
  | be found  |                       | calls the |
  | and edited|                       | new name  |
  +-----------+                       +-----------+
```

## 7. Dynamics

```
  t0  function declaration identified as needing change
       |
       v
  t1  decide new name / new parameter list
       (this is a design decision, not a mechanical one)
       |
       v
  t2  option A: "rename in place"
       -- create new declaration alongside old
       -- old delegates to new (or new delegates to old)
       -- update call sites one at a time
       -- delete old when zero callers remain
       |
       v
  t2' option B: "big bang rename"
       -- update every call site in one pass
       -- delete old declaration
       -- relies on compiler catching every call site
       |
       v
  t3  run test suite
       -- if green, done
       -- if red, a call site was missed or the new
          signature is wrong
       |
       v
  t4  commit with a message naming the old and new declarations
       so that git log can answer "what was this called before"
```

Option A, the gradual rename, is Fowler's recommended approach when the call
site count is high or the codebase is too large to find every caller with
certainty. The old function keeps working during the migration, so the
codebase is never broken between commits. Option B, the big bang rename, is
safe when the compiler finds every call site, for example in a single
repository with no reflective calls.

## 8. Implementation variants

**Rename via delegation.** Keep the old function, make it delegate to the new
one, and migrate call sites gradually. Each call site change is a separate,
safe commit. The old function is deleted when no caller remains. This is
Fowler's default approach in the second edition, chapter 6.

**Rename via compiler.** Change the declaration, let the compiler produce
every error, and fix each error. This works in statically typed languages
where the compiler finds every call site, and it is the approach the IntelliJ
IDEA and Eclipse refactoring tools automate. The variant fails when the
function is called via reflection or string based dispatch, because the
compiler does not see those call sites.

**Parameter addition with default value.** Add the new parameter with a
default value so existing call sites continue to work without modification.
This is the standard approach in Python, JavaScript, and TypeScript, and it
is the only approach that does not require touching every call site
immediately. The risk is that the default value may mask a real semantic
difference, where a caller should be passing the new parameter but silently
gets the default instead.

**Parameter removal via overloading.** In languages that support function
overloading, such as Java and C sharp, you can add an overload with the new
signature and keep the old signature delegating to it. Call sites migrate to
the new overload one at a time. This is the Java idiom for backward
compatible signature changes.

**Rename via deprecation.** In a published API, mark the old function as
deprecated in the documentation and in the source, add the new function
alongside it, and let consumers migrate at their own pace. The old function
is removed only after a version or two has passed, giving consumers time to
migrate. This is not a code refactoring but an API evolution strategy, and
Fowler treats it separately from the mechanical rename.

```python
# Python: rename via delegation (gradual)

def old_process_payment(amount, currency):
    """Deprecated. Use process_payment."""
    return process_payment(amount, currency)

def process_payment(amount, currency):
    # new name, same behaviour
    if currency == "USD":
        return amount * 1.0
    return amount * 0.85
```

```typescript
// TypeScript: parameter addition with default value

function formatDate(date: Date, format?: string): string {
  const fmt = format ?? "ISO";
  if (fmt === "ISO") return date.toISOString();
  if (fmt === "short") return date.toLocaleDateString();
  return date.toISOString();
}

// existing callers still work:
formatDate(new Date());
// new callers can pass the format:
formatDate(new Date(), "short");
```

```java
// Java: rename via overload (backward compatible)

public class PaymentService {
    @Deprecated
    public Receipt doPayment(int amount, String currency) {
        return processPayment(amount, currency);
    }

    public Receipt processPayment(int amount, String currency) {
        // new name, same body
        if ("USD".equals(currency)) {
            return new Receipt(amount, "USD");
        }
        return new Receipt(amount * 85, "USD-cent");
    }
}
```

## 9. Known production uses

**IntelliJ IDEA's Rename refactoring** automates the mechanical steps of this
refactoring across an entire project, finding every call site through
static analysis and updating them atomically. JetBrains documents that the
tool performs a compile time safety check before applying the rename, so
that a rename that would break the build is reported before any file is
written ([JetBrains Rename refactoring](https://www.jetbrains.com/help/idea/rename-refactorings.html),
verified 2026-08-13). The tool handles the gradual rename via delegation
variant by default when the function is public or has callers the compiler
cannot see.

**The Rust compiler treats function renames as a compile error**, not a
warning, because every function call in Rust is resolved at compile time.
The Rust reference states that function items have nominal types and that a
rename changes the nominal type, so every call site that used the old name
produces an `unresolved name` error ([The Rust Reference, Functions](https://doc.rust-lang.org/reference/items/functions.html),
verified 2026-08-13). This makes the big bang variant the only practical
approach in Rust, and it is safe because the compiler catches every call
site.

## 10. Consequences

Positive.

- Every future read of the codebase benefits from the improved name or
  signature for the remaining lifetime of the function.
- The function's intent is communicated at the call site without requiring
  the reader to open the body.
- The parameter list matches the function's actual needs, reducing the
  cognitive load of each call.
- The test suite, if thorough, catches any missed call site immediately.

Negative.

- Every call site must be updated, which is a real cost proportional to the
  number of callers.
- In dynamically typed languages, a missed call site produces a runtime error
  instead of a compile error, so the rename is only as safe as the test
  coverage.
- The rename can break consumers of a public API unless handled through a
  deprecation cycle.
- A rename changes the git history's connection to old references in
  documentation, commit messages, and issue trackers, which can make
  archaeological work harder unless the commit message records the old name.

## 11. Failure modes and misuse

**Missed call site in a dynamic language.** A Python or JavaScript rename
that relies on grep instead of a compiler will miss call sites that invoke
the function through `getattr`, through `window[name]`, or through any
indirection that hides the name from a text search. The symptom is a
runtime `AttributeError` or `TypeError` that surfaces only when the missed
code path executes, which may be days or weeks after the rename lands.

**Semantic mismatch in parameter default.** Adding a parameter with a
default value that is silently wrong for some callers. A function
`sendEmail(to, cc)` gains a `bcc` parameter with a default of an empty list,
but one caller should have been sending a BCC and now silently does not
because the caller was never updated. The symptom is missing email, missing
audit trail, or a privacy leak, none of which produce a compiler error.

**Rename to a name that is only temporarily better.** A name that is
accurate today becomes inaccurate when the function gains a new
responsibility tomorrow. The misuse is treating a rename as a one time fix
rather than an ongoing hygiene practice, and the symptom is the same bad
name the rename was supposed to fix, just with different words.

**Renaming a function that should be split.** The name is bad because the
function does too much, and no name can honestly describe five
responsibilities. The misuse is renaming `doEverything` to
`processAndValidateAndLog` instead of extracting three functions, each with
a single responsibility and an honest name.

## 12. Trade-off matrix

| Alternative | Call site churn | Comprehension gain | Risk of missed caller | When to prefer |
|---|---|---|---|---|
| Change Function Declaration | Every caller updated | High, name and signature now honest | Medium in dynamic languages, low in static | The name or signature is misleading and callers are findable |
| Extract Function then rename the extract | Only the extract point | High, the new function starts with a good name | Low, the old function body is unchanged | The old name is bad because the function is too large |
| Introduce Parameter Object | Every caller updated, but the list is simpler | High for long parameter lists | Medium | The parameter list is long and parameters are related |
| Deprecation cycle (public API) | Callers migrate at their pace | Deferred | Low, old name still works | The function is part of a published API |
| Inline Function | Every caller gets the body | Removes the abstraction entirely | Low | The function is so simple that the name adds no value |

## 13. Related and incompatible patterns

**Extract Function** (same catalog) is the natural complement. When a
function's name is bad because the function is too large, extract a piece
with a good name rather than renaming the oversized function. The two
refactorings are frequently applied together: extract to get a clean piece,
then rename the extract to communicate its intent.

**Inline Function** (same catalog) is the inverse. When the function name
adds no value over the body itself, the correct move is to remove the
function entirely, not to rename it. Inlining is the right choice when the
function is a one line wrapper whose name communicates nothing the body does
not.

**Introduce Parameter Object** (same catalog) groups related parameters into a
single value object, which reduces the parameter count and makes the call
site more readable. It is complementary to Change Function Declaration when
the parameter list is long because of related parameters, not because the
function does too many things.

**Parameterize Function** (same catalog) replaces several functions that
differ only in a single value with one function that takes that value as a
parameter. It is the right move when you have `chargeMonthly` and
`chargeAnnual` as separate functions, because the fix is to add a period
parameter, not to rename either function.

## 14. Refactoring path in and out

**Path in.** The refactoring is introduced by choosing a new declaration,
deciding whether to use gradual delegation or big bang rename, and updating
every call site. The steps are:

1. Identify the function whose declaration needs to change.
2. Choose the new name, the new parameter list, or both.
3. If the function is part of a public API, add the new declaration
   alongside the old and mark the old as deprecated. Skip to step 7.
4. If using gradual rename, create the new function alongside the old, make
   the old delegate to the new, and update call sites one at a time. Each
   call site update is a separate commit.
5. If using big bang rename, change the declaration in place, let the
   compiler or test suite find every call site, and fix each error.
6. Run the test suite after every call site update.
7. When the last caller has migrated (gradual) or the build is green (big
   bang), delete the old declaration if it still exists.
8. Commit with a message that records the old and new names so that future
   archaeology can find the connection.

**Path out.** The refactoring is removed when the function is deleted
entirely (Inline Function) or when the function is split into smaller
functions (Extract Function). There is no scenario where the rename is
reverted to the old name, because the old name was the reason the
refactoring was applied.

## 15. Testing and verification

The test suite is the primary safety net. Every existing test for the
function should pass unchanged after the rename, because the behaviour is
identical. If a test fails, either a call site was missed or the new
signature is semantically different from the old one, which means the change
is not a rename but a behaviour change that needs its own tests.

In a dynamically typed language, add a test that calls the function by its
new name from every entry point that matters, because the runtime will
only find a missed call site when that code path executes. A grep for the
old name after the rename should return zero results in the source, though
it may return hits in documentation, commit messages, and issue trackers
that are intentionally not updated.

A rename that adds a parameter should add a test for each new code path the
parameter enables. A rename that removes a parameter should verify that no
caller depended on the removed parameter's value, which in practice means
the test suite should have covered every value the parameter could take.

## 16. Observability signals

A rename does not change behaviour, so the observable signal in production
is nothing. The function produces the same outputs for the same inputs,
logs the same messages, and emits the same metrics. If production
observability changes after a rename, the change is not a rename but a
behaviour change, and the difference between what was expected and what was
observed is the signal that the refactoring was misclassified.

The one observable difference is in logs and traces that include the
function name. Distributed tracing systems that record the function name in
span labels will show the new name where the old name used to appear. This
is expected, not a regression, but anyone correlating traces across the
rename boundary needs to know both names, which is why the commit message
should record the mapping.

## 17. Security and privacy implications

A rename does not change the function's behaviour, so it does not open new
attack surfaces or close existing ones. The security relevant case is when
the rename is done to make a security sensitive function's intent clearer,
for example renaming `process` to `sanitizeInput`, which makes the function's
role in the security boundary visible at the call site. This is a positive
security signal, not a security change, because the function was already
doing the work.

A parameter addition that introduces a new code path, for example a
`skipValidation` parameter with a default of false, does change the security
surface, because a caller that passes `true` bypasses a check the function
previously always performed. This is a behaviour change, not a rename, and
it should be reviewed as a security relevant change even though it was
delivered through the same mechanical steps.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 6, "Change Function Declaration."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 7, "Rename Method," "Add
  Parameter," "Remove Parameter."
- Kent Beck, *Smalltalk Best Practice Patterns*, Prentice Hall, 1997,
  "Intention Revealing Names" pattern.
- JetBrains, "Rename refactoring," IntelliJ IDEA documentation,
  [https://www.jetbrains.com/help/idea/rename-refactorings.html](https://www.jetbrains.com/help/idea/rename-refactorings.html),
  verified 2026-08-13.
- The Rust Reference, "Functions,"
  [https://doc.rust-lang.org/reference/items/functions.html](https://doc.rust-lang.org/reference/items/functions.html),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
