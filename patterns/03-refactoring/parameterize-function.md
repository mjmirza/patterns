---
name: Parameterize Function
slug: parameterize-function
family: 03-refactoring
category: Refactoring
aliases: [Parameterize Method, Replace Functions with Parameterized Function]
first_described: "Fowler 2018"
maturity: canonical
related: [change-function-declaration, extract-function, inline-function, combine-functions-into-transform, replace-conditional-with-polymorphism]
incompatible_with: []
verified: 2026-08-13
---

# Parameterize Function

## 1. Name, aliases, and lineage

The canonical name is **Parameterize Function**, introduced by Martin
Fowler in *Refactoring. Improving the Design of Existing Code*, 2nd
edition, Addison-Wesley, 2018, chapter 6, "A First Set of Refactorings."
In the first edition (1999), the equivalent operation appeared as
**Parameterize Method** in chapter 10, "Making Method Calls Simpler."
Fowler renamed it in the second edition to match the Extract Function /
Extract Class naming convention, and because the operation applies to
free functions as well as methods.

The underlying idea, that two or more functions that differ only in a
single value should be replaced by one function that takes the value as a
parameter, is the DRY principle (Don't Repeat Yourself) applied at the
function level. Andy Hunt and Dave Thomas, in *The Pragmatic Programmer*,
Addison-Wesley, 1999, describe the principle: every piece of knowledge
should have a single, unambiguous, authoritative representation within a
system. Two functions that differ only in a constant are two
representations of the same knowledge, and the parameterized function is
the single representation.

## 2. Problem and context

You have two or more functions that perform the same operation with
different constant values. The functions have the same structure, the
same body, and the same logic, differing only in a literal or a
constant. The duplication is a maintenance burden: a change to the logic
must be made in every copy, and a bug fixed in one copy is not fixed in
the others.

The situation reads like this. A codebase has `double baseCharge5` and
`double baseCharge10`, two functions that calculate a base charge for 5
and 10 units. The functions are identical except for the literal 5 and
10. A change to the calculation must be made in both, and a caller that
needs 7 units has no function to call, because neither 5 nor 10 is the
right value.

The fix is to parameterize the function. Replace both functions with one
`baseCharge(units)` that takes the number of units as a parameter. The
caller passes 5, 10, 7, or any value, and the function computes the charge
for that value.

## 3. Forces

**Duplication versus generality.** Two specific functions are easy to
understand, because each does one thing. One parameterized function is
more general, because it handles any value. The force favours
parameterization when the duplication cost exceeds the generality cost.

**Readability versus flexibility.** A specific function name communicates
what it does: `baseCharge5` says "charge for 5 units." A parameterized
function name is less specific: `baseCharge(units)` requires the caller
to pass the value. The force favours parameterization when the
flexibility of any value exceeds the readability of the specific name.

**Type safety versus generality.** A specific function can have a
specific return type or a specific precondition. A parameterized function
must handle any value the parameter can take, which may weaken the type
safety. The force favours keeping specific functions when the type
safety matters.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- Two or more functions have the same body, differing only in a constant
  value.
- The functions are called with different constant values, and a caller
  that needs a value not covered by an existing function has no function
  to call.
- The logic is duplicated, and a change to the logic must be made in
  every copy.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The functions differ in more than one value, and parameterizing them
  would produce a function with many parameters that is harder to call
  than the specific functions.
- The functions have different logic, not just different constants, and
  the parameterization would require conditionals that select the logic
  based on the parameter, which is Replace Conditional with Polymorphism,
  not Parameterize Function.
- The specific function names are part of a public API and consumers call
  them by name. Parameterizing removes the functions, which breaks
  consumers.

## 5. Structure

The refactoring has one participant: the set of functions that differ
only in a constant. After the refactoring, they are one function that
takes the constant as a parameter.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER
  ------                              -----

  function chargeFor5():              function chargeFor(units):
    return 5 * RATE                     return units * RATE
  function chargeFor10():
    return 10 * RATE                 caller:
                                       chargeFor(5)
  caller:                              chargeFor(10)
    chargeFor5()                       chargeFor(7)  // now possible
    chargeFor10()

  (two functions, one constant diff)  (one function, any value)
```

## 7. Dynamics

```
  t0  identify functions with same body,
       differing only in a constant
       |
       v
  t1  create a new function with the
       constant as a parameter
       |
       v
  t2  replace the body with the parameterized version
       |
       v
  t3  update every caller to pass the constant
       |
       v
  t4  delete the old specific functions
       |
       v
  t5  run test suite
       |
       v
  t6  commit. the function is parameterized.
```

## 8. Implementation variants

**Single parameter.** The canonical variant. The functions differ in one
constant, and the parameterized function takes one parameter.

**Multiple parameters.** The functions differ in two or three constants,
and the parameterized function takes multiple parameters. This variant is
used when the constants are related and the parameter count is manageable.

**Parameter object.** The functions differ in many constants, and the
parameterized function takes a parameter object that holds all the
constants. This variant combines Parameterize Function with Introduce
Parameter Object.

```python
# Python: before (two functions, one constant diff)

def charge_for_5():
    return 5 * RATE

def charge_for_10():
    return 10 * RATE

# Python: after (parameterized)

def charge_for(units: int) -> float:
    return units * RATE

# caller:
charge_for(5)
charge_for(10)
charge_for(7)
```

```typescript
// TypeScript: before

function chargeFor5(): number { return 5 * RATE; }
function chargeFor10(): number { return 10 * RATE; }

// TypeScript: after

function chargeFor(units: number): number {
    return units * RATE;
}
```

```java
// Java: after (parameterized)

public double chargeFor(int units) {
    return units * RATE;
}

// caller:
chargeFor(5);
chargeFor(10);
chargeFor(7);
```

## 9. Known production uses

**Python's `functools.partial`** is the language level mechanism for the
inverse: it takes a parameterized function and produces a specific
function with one parameter fixed. The Python documentation states that
`partial` returns a new partial object which behaves like the original
function with the given arguments fixed
([functools.partial documentation](https://docs.python.org/3/library/functools.html#functools.partial),
verified 2026-08-13). The two approaches are complementary:
Parameterize Function creates the general form, and `partial` creates
specific forms from it.

**Java's `Function<T,R>` and `BiFunction<T,U,R>`** from `java.util.function`
are the standard library's parameterized function types. A caller that
needs a specific function creates a lambda that fixes one parameter, which
is the `partial` equivalent in Java
([java.util.function documentation](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/function/package-summary.html),
verified 2026-08-13).

## 10. Consequences

Positive.

- The duplication is eliminated, which reduces the maintenance burden
  and the risk of a bug being fixed in one copy but not the others.
- Any value can be passed, which means a caller that needs a value not
  covered by the specific functions can call the parameterized function.
- The function is more general, which means it can be reused in more
  contexts.

Negative.

- The caller must pass the constant, which is more ceremony than calling
  a specific function by name.
- The specific function names are lost, which may reduce readability for
  callers that always pass the same constant.
- The parameterized function must handle any value the parameter can
  take, which may require validation that the specific functions did not
  need.

## 11. Failure modes and misuse

**Parameterizing functions with different logic.** The functions differ
in more than a constant, and parameterizing them requires conditionals
that select the logic based on the parameter. The symptom is a
parameterized function with a switch or an if that was not in the
original functions.

**Parameterizing too many constants.** The functions differ in three or
four constants, and the parameterized function has a long parameter list
that is harder to call than the specific functions.

**Parameterizing a public API.** The specific functions are part of a
public API, and parameterizing removes them, which breaks consumers.

## 12. Trade-off matrix

| Alternative | Duplication | Generality | When to prefer |
|---|---|---|---|
| Parameterize Function | Eliminated | Any value | Same body, one constant diff |
| Extract Function | Eliminated | Specific | Block is reusable as a named function |
| Replace Conditional with Polymorphism | Eliminated | Polymorphic | Conditional dispatches on type |
| Keep specific functions | Present | Limited | Different logic, public API |

## 13. Related and incompatible patterns

**Change Function Declaration** (same catalog) is the mechanism that
adds the parameter to the function signature.

**Extract Function** (same catalog) is the step before parameterization:
the common body is extracted, then the differing constant is
parameterized.

**Replace Conditional with Polymorphism** (same catalog) is the
alternative when the functions differ in logic, not just in a constant.

## 14. Refactoring path in and out

**Path in.** Create a new function with the constant as a parameter,
update callers, delete the old functions.

**Path out.** Create specific functions that delegate to the
parameterized function with a fixed constant, which is the `partial`
approach.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test that called a specific function should call the parameterized
function with the same constant and should produce the same result.

## 16. Observability signals

The refactoring does not change behaviour, so the observable signal in
production is nothing.

## 17. Security and privacy implications

The refactoring does not change what data is processed, so it does not
change the security surface. The parameterized function may need
validation that the parameter is in a valid range, which is a security
consideration that the specific functions did not need.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 6, "Parameterize Function."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 10, "Parameterize Method."
- Andy Hunt and Dave Thomas, *The Pragmatic Programmer*, Addison-Wesley,
  1999, "DRY Principle."
- Python Software Foundation, "functools.partial,"
  [https://docs.python.org/3/library/functools.html#functools.partial](https://docs.python.org/3/library/functools.html#functools.partial),
  verified 2026-08-13.
- Oracle, "java.util.function,"
  [https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/function/package-summary.html](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/function/package-summary.html),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
