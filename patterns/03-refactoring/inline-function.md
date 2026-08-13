---
name: Inline Function
slug: inline-function
family: 03-refactoring
category: Refactoring
aliases: [Inline Method, Merge Function into Caller, Remove Indirection]
first_described: "Fowler 1999"
maturity: canonical
related: [extract-function, inline-class, inline-variable, replace-function-with-command, combine-functions-into-transform]
incompatible_with: []
verified: 2026-08-13
---

# Inline Function

## 1. Name, aliases, and lineage

The canonical name is **Inline Function**, introduced by Martin Fowler in
*Refactoring. Improving the Design of Existing Code*, 1st edition,
Addison-Wesley, 1999, chapter 6, "Composing Methods," where it appeared
as **Inline Method.** In the second edition, Martin Fowler, *Refactoring.
Improving the Design of Existing Code*, 2nd edition, Addison-Wesley, 2018,
chapter 6, "A First Set of Refactorings," Fowler renamed it to Inline
Function to match the rename of Extract Method to Extract Function,
because the operation applies to free functions as well as methods.

The underlying idea, that a function whose name is no more informative
than its body should be replaced by its body, is the inverse of Kent
Beck's Composed Method pattern from *Smalltalk Best Practice Patterns*,
Prentice Hall, 1997. Beck says every method should do one thing and be
named for what it does. Fowler's Inline Function says: if the name does
not communicate anything the body does not, the name is not earning its
indirection, and the body should replace the call.

The alias **Inline Method** is the original name from the first edition
and is the name used in the Eclipse and IntelliJ refactoring menus. The
alias **Merge Function into Caller** is used in the JavaScript community,
where the merge is expressed as replacing a function call with the
function body.

## 2. Problem and context

You have a function whose body is as clear as its name, or clearer. The
function was extracted at some point because the body was duplicated or
because the name was informative, but over time the body has been
simplified to the point where the name adds indirection without adding
clarity, or the function is called from exactly one place and the name
is not more informative than the body. The function adds a level of
indirection that a reader must navigate, and the indirection is not paying
for itself.

The situation reads like this. A function called `getRating` has one
line: `return driver.numberOfLateDeliveries > 5 ? 2 : 1;`. The function
was extracted from a `report` function that called it, and at the time
the body was longer and the name was informative. Since then, the body
has been simplified to a single expression that is as clear as the name,
and the function is called from exactly one place. A reader who
encounters `getRating()` must navigate to the function to understand what
it does, and when they arrive they find one line that they could have
read at the call site.

The fix is to inline the function. Replace the call with the body, and
delete the function. The reader sees the expression directly, and the
indirection is gone.

## 3. Forces

**Naming versus indirection.** A function name communicates intent, which
is valuable when the name is more informative than the body. An inline
expression shows the mechanics directly, which is valuable when the body
is as clear as the name. The force favours inlining when the name is not
earning its indirection, and favours keeping the function when the name
communicates something the body does not.

**Reusability versus simplicity.** A separate function can be called from
multiple places. An inlined function's body is at one call site and
cannot be reused without extracting it again. The force favours keeping
the function when it is called from multiple places, and favours inlining
when it is called from one place.

**Testability versus brevity.** A separate function can be tested in
isolation. An inlined function is tested through the caller, which is
integration testing. The force favours keeping the function when isolated
testing is valuable, and favours inlining when the function is so simple
that the test is trivial.

**Abstraction versus transparency.** A function is an abstraction: it
hides its body behind a name. An inlined expression is transparent: the
mechanics are visible. The force favours the function when the body is
complex enough that the abstraction helps, and favours inlining when the
body is so simple that the abstraction adds indirection without clarity.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- The function's body is as clear as its name, or clearer. A one line
  function whose expression is self explanatory is a candidate.
- The function is called from one place, and the indirection is not
  providing reuse or testing benefit.
- The function's name is not more informative than its body, which means
  the name is not communicating intent but restating mechanics.
- The function was extracted for a reason that no longer applies, for
  example the body was duplicated but the duplication has been removed.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The function is called from multiple places. Inlining into one caller
  would duplicate the body in every caller, which is the duplication the
  function was extracted to prevent.
- The function's name communicates intent that the body does not, for
  example `isEligible` is more communicative than
  `age >= 18 and contributions > 0 and not isRetired`. The name is earning
  its indirection.
- The function is part of a public API and consumers call it by name.
  Inlining removes the function, which breaks every consumer.
- The function is a polymorphic override that subclasses use. Inlining
  removes the function, which breaks the polymorphic dispatch.

## 5. Structure

The refactoring has one participant.

- **The function.** The function being inlined. After the refactoring, the
  function's body replaces the call at the call site, and the function
  definition is deleted.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER
  ------                              -----

  function getRating():               function report():
    return lateDeliveries > 5           rating = lateDeliveries > 5
             ? 2 : 1                            ? 2 : 1
                                      // body is at call site
  function report():                  (getRating function deleted)
    rating = getRating()
```

## 7. Dynamics

```
  t0  identify function whose name is
       not more informative than its body
       |
       v
  t1  verify the function has one caller
       (if multiple callers, do NOT inline)
       |
       v
  t2  copy the function body to the call site
       |
       v
  t3  replace the call with the body
       -- handle return values and parameters
       |
       v
  t4  delete the function definition
       |
       v
  t5  run test suite
       |
       v
  t6  commit. the function is inlined.
```

## 8. Implementation variants

**Inline at a single call site.** The canonical variant. The body replaces
the call at one call site, and the function is deleted. This is the
variant Fowler describes in both editions.

**Inline at every call site.** When the function is called from multiple
places but the body is so simple that inlining everywhere is better than
keeping the function, the body is copied to every call site. This variant
is the reverse of Extract Function's duplication removal, and it is
applied when the indirection cost exceeds the duplication cost, which is
rare.

**Inline via macro expansion.** In languages with macros or preprocessor
directives, the function body is expanded at every call site by the
preprocessor. This variant is the compile time version of inlining, and
it is used in C and C++ for performance critical functions.

```python
# Python: before (trivial function called once)

def get_rating(late_deliveries: int) -> int:
    return 2 if late_deliveries > 5 else 1

def report(late_deliveries: int) -> str:
    rating = get_rating(late_deliveries)
    return f"Rating: {rating}"

# Python: after (inlined)

def report(late_deliveries: int) -> str:
    rating = 2 if late_deliveries > 5 else 1
    return f"Rating: {rating}"
```

```typescript
// TypeScript: before (wrapper adds no clarity)

function isEligible(age: number, contributions: number): boolean {
    return age >= 18 && contributions > 0;
}

function processApplication(app: Application): void {
    if (isEligible(app.age, app.contributions)) {
        approve(app);
    }
}

// TypeScript: after (inlined, condition is clear)

function processApplication(app: Application): void {
    if (app.age >= 18 && app.contributions > 0) {
        approve(app);
    }
}
```

```java
// Java: before (one-line method called once)

public int getRating() {
    return driver.getLateDeliveries() > 5 ? 2 : 1;
}

public String report() {
    int rating = getRating();
    return "Rating: " + rating;
}

// Java: after (inlined)

public String report() {
    int rating = driver.getLateDeliveries() > 5 ? 2 : 1;
    return "Rating: " + rating;
}
```

## 9. Known production uses

**IntelliJ IDEA's "Inline Method" refactoring** automates the inlining by
replacing every call to the selected method with the method body and
deleting the method. JetBrains documents that the tool handles parameters,
return values, and multiple call sites, and that it verifies no
polymorphic dispatch is broken before allowing the inline
([JetBrains Inline refactoring](https://www.jetbrains.com/help/idea/inline-refactoring.html),
verified 2026-08-13).

**The C++ `inline` keyword** is the language level mechanism for compile
time function inlining. The C++ standard states that an inline function
may be expanded at the call site rather than called, though the compiler
makes the final decision based on cost heuristics
([cppreference inline specifier](https://en.cppreference.com/w/cpp/language/inline),
verified 2026-08-13). This is the compile time variant of the refactoring,
applied by the compiler rather than the developer.

## 10. Consequences

Positive.

- The indirection is removed, and the reader sees the body directly at
  the call site.
- The function is deleted, which reduces the number of functions in the
  codebase.
- The call site is self contained, which means a reader does not need to
  navigate to another function to understand the logic.

Negative.

- If the function was called from multiple places, inlining duplicates
  the body at every call site, which is a maintenance burden.
- If the function was tested in isolation, the test must be removed or
  adapted, because the function no longer exists.
- The call site is longer, which may make the enclosing function harder
  to read if the body is complex.
- If the function's name was communicating intent, the inline loses the
  intent and leaves only the mechanics.

## 11. Failure modes and misuse

**Inlining a function with a communicative name.** The function's name
communicates intent that the body does not, and inlining loses the name.
The symptom is a call site with an expression whose intent is not obvious,
where the function name used to communicate it.

**Inlining a function called from multiple places.** The function is
called from multiple call sites, and inlining duplicates the body at
every site. The symptom is duplicated code that Extract Function would
remove.

**Inlining a polymorphic method.** The method is overridden by a
subclass, and inlining the base class method at the call site breaks the
polymorphic dispatch. The symptom is a call site that no longer dispatches
to the subclass override, which is a silent behaviour change.

**Over inlining.** Every trivial function is inlined, producing long
functions with no named steps. The symptom is a function that is a wall
of expressions with no structure, which is the opposite problem Extract
Function was supposed to solve.

## 12. Trade-off matrix

| Alternative | Indirection | Reusability | Naming | When to prefer |
|---|---|---|---|---|
| Inline Function | Removed | None, body at call site | None | Name adds no value, one caller |
| Extract Function | Added | High, callable elsewhere | High | Block has a clear purpose |
| Replace Function with Command | Changed | High, command object | Medium | Function needs undo, queue, audit |
| Keep function | Present | Depends on callers | Present | Name is communicative, multiple callers |

## 13. Related and incompatible patterns

**Extract Function** (same catalog) is the inverse. It creates a function
from a block, where Inline Function removes a function and puts the block
back at the call site. The two are the opposite directions of function
boundary manipulation.

**Inline Class** (same catalog) is the larger scale version. It merges a
whole class into another, where Inline Function merges a function into
its caller.

**Inline Variable** (same catalog) is the smaller scale version. It
replaces a variable reference with the variable's initialiser, where
Inline Function replaces a call with the function body.

**Replace Function with Command** (same catalog) is the alternative when
the function needs capabilities a plain function does not have, such as
undo, queuing, or audit. The command keeps the indirection but adds the
capabilities.

## 14. Refactoring path in and out

**Path in.** The refactoring is introduced by replacing the call with the
body. The steps are:

1. Identify a function whose name is not more informative than its body.
2. Verify the function has one caller (or that inlining at every caller
   is acceptable).
3. Copy the function body to the call site.
4. Replace parameters with the arguments passed at the call site.
5. If the function returns a value, use the body as an expression or
   assign it to a variable.
6. Delete the function definition.
7. Run the test suite. Any failure means the inlining changed the
   semantics, for example a parameter was not replaced correctly.

**Path out.** The refactoring is reversed by Extract Function, which
extracts the body back into a named function. The reverse is applied
when the body turns out to be complex enough to warrant a name, or when
the body is needed at multiple call sites.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test that exercised the caller should produce the same result. A test
failure means the inlining changed the semantics.

If the function had its own tests, those tests should be removed or
adapted, because the function no longer exists. The function's behaviour
is now tested through the caller's tests, which should cover the same
inputs and outputs.

## 16. Observability signals

The refactoring does not change behaviour, so the observable signal in
production is nothing. The one observable difference is in profiling: the
function disappears from the profiler, and its cost is attributed to the
caller. This is actually an observability loss if the function was a
significant cost centre, because the profiler no longer shows it as a
separate entry.

## 17. Security and privacy implications

The refactoring does not change what data is processed or how it is
processed, so it does not change the security surface. The security
relevant case is when the function's name communicated a security
boundary, for example `validateInput`, and inlining loses the name. A
reader who sees the validation logic inline may not recognise it as a
security boundary, where the function name made it visible. This is a
minor security readability loss.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 6, "Inline Function."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 6, "Inline Method."
- Kent Beck, *Smalltalk Best Practice Patterns*, Prentice Hall, 1997,
  "Composed Method" pattern.
- JetBrains, "Inline refactoring,"
  [https://www.jetbrains.com/help/idea/inline-refactoring.html](https://www.jetbrains.com/help/idea/inline-refactoring.html),
  verified 2026-08-13.
- cppreference, "inline specifier,"
  [https://en.cppreference.com/w/cpp/language/inline](https://en.cppreference.com/w/cpp/language/inline),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
