---
name: Inline Variable
slug: inline-variable
family: 03-refactoring
category: Refactoring
aliases: [Inline Temp, Remove Explaining Variable, Inline Temp Variable]
first_described: "Fowler 1999"
maturity: canonical
related: [extract-variable, inline-function, replace-temp-with-query, introduce-explaining-variable]
incompatible_with: []
verified: 2026-08-13
---

# Inline Variable

## 1. Name, aliases, and lineage

The canonical name is **Inline Variable**, introduced by Martin Fowler in
*Refactoring. Improving the Design of Existing Code*, 1st edition,
Addison-Wesley, 1999, chapter 6, "Composing Methods," where it appeared
as **Inline Temp.** In the second edition, Martin Fowler, *Refactoring.
Improving the Design of Existing Code*, 2nd edition, Addison-Wesley, 2018,
chapter 6, "A First Set of Refactorings," Fowler renamed it to Inline
Variable to match the naming convention of Inline Function.

The underlying idea, that a variable whose name is no more informative
than its initialiser should be replaced by the initialiser, is the inverse
of Extract Variable (Introduce Explaining Variable in the first edition).
The two refactorings form a pair: one names a subexpression, the other
removes the name when it is no longer earning its place.

The alias **Inline Temp** is the original name from the first edition
and is used in the Eclipse refactoring menu. The alias **Remove Explaining
Variable** is used in the JavaScript community, where the variable is
typically a `const` and the removal is expressed as replacing the
reference with the constant's value.

## 2. Problem and context

You have a variable whose initialiser is as clear as the variable name,
or clearer. The variable was introduced to name a subexpression, but the
expression is simple enough that the name adds verbosity without adding
clarity, or the variable is used once and the name is not more
communicative than the expression itself. The variable adds a line and
an indirection that a reader must trace, and the indirection is not
paying for itself.

The situation reads like this. A function declares
`const basePrice = order.basePrice;` and then uses `basePrice` once in a
comparison: `if (basePrice > 1000)`. The variable name `basePrice` is
no more informative than `order.basePrice`, and the variable adds a
declaration and an assignment that the reader must trace to understand.
If the variable is removed and the comparison is written as
`if (order.basePrice > 1000)`, the reader sees the expression directly
without the indirection of a variable.

The fix is to inline the variable. Replace every reference to the variable
with its initialiser, and remove the declaration.

## 3. Forces

**Clarity versus brevity.** A named variable communicates the concept the
expression represents, which is clear when the name is better than the
expression. An inlined expression is briefer, which is clear when the
expression is as readable as the name. The force favours inlining when the
name is not adding clarity over the expression.

**Single use versus reuse.** A variable used once is a candidate for
inlining, because the variable is not providing reuse benefit. A variable
used multiple times is harder to inline, because the expression is
duplicated at every use site. The force favours inlining for single use
variables and favours keeping variables used multiple times.

**Evaluation versus storage.** An inlined variable's expression is
evaluated at every use site, which is correct if the expression is cheap
and potentially wrong if the expression has side effects or is expensive.
The force favours inlining when the expression is cheap and pure, and
favours keeping the variable when the expression is expensive or has side
effects.

**Debugging versus brevity.** A variable can be inspected at a breakpoint,
which gives the debugger visibility into the intermediate value. An inlined
expression does not have a name to inspect, which makes debugging harder.
The force favours keeping the variable when debugging visibility is
important, and favours inlining when the brevity benefit exceeds the
debugging cost.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- The variable's name is no more informative than its initialiser, and
  the initialiser is a simple expression that is readable at the use site.
- The variable is used once, so inlining does not duplicate the expression.
- The initialiser is a pure expression with no side effects, so inlining
  does not change the evaluation count.
- The variable was introduced by Extract Variable but the expression has
  since been simplified to the point where the name is no longer earning
  its indirection.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The variable's name communicates a concept that the expression does not,
  for example `isEligible` is more communicative than
  `age >= 18 && contributions > 0`. The name is earning its indirection.
- The variable is used multiple times, and inlining duplicates the
  expression at every use site.
- The initialiser has side effects or is expensive, and inlining would
  evaluate it multiple times or change the evaluation order.
- The variable is used in a debugger workflow where the intermediate
  value is inspected at breakpoints, and inlining removes the inspectable
  name.

## 5. Structure

The refactoring has one participant.

- **The variable.** A local variable whose initialiser is as clear as its
  name. After the refactoring, every reference to the variable is replaced
  with the initialiser, and the declaration is removed.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER
  ------                              -----

  const basePrice = order.basePrice;  if (order.basePrice > 1000)
  if (basePrice > 1000) {                 discount = 0.05;
      discount = 0.05;                (variable removed)
  }
```

## 7. Dynamics

```
  t0  identify variable whose name is not
       more informative than its initialiser
       |
       v
  t1  verify the variable is used once
       and the initialiser is pure
       |
       v
  t2  replace the reference with the initialiser
       |
       v
  t3  remove the declaration
       |
       v
  t4  run test suite
       |
       v
  t5  commit. the variable is inlined.
```

## 8. Implementation variants

**Inline const.** The canonical variant in JavaScript and TypeScript. A
`const` variable is replaced by its value at the use site, and the
declaration is removed. This is the variant Fowler describes in the second
edition.

**Inline final.** In Java, a `final` local variable is replaced by its
initialiser. The variant is the same as the const variant, with the
language's keyword.

**Inline let.** In Swift and Rust, a `let` variable is replaced by its
initialiser. The variant is the same.

```python
# Python: before (variable adds no clarity)

def calculate_discount(order):
    base_price = order.base_price
    if base_price > 1000:
        return 0.05
    return 0.0

# Python: after (inlined)

def calculate_discount(order):
    if order.base_price > 1000:
        return 0.05
    return 0.0
```

```typescript
// TypeScript: before (const adds no clarity)

interface Order {
    basePrice: number;
}

function calculateDiscountBefore(order: Order): number {
    const basePrice = order.basePrice;
    if (basePrice > 1000) {
        return 0.05;
    }
    return 0.0;
}

// TypeScript: after (inlined)

function calculateDiscount(order: Order): number {
    if (order.basePrice > 1000) {
        return 0.05;
    }
    return 0.0;
}
```

```java
class Order {
    double getBasePrice() { return 0; }
}

public class DiscountCalculator {

    // Java: before (final variable adds no clarity)

    public double calculateDiscountBefore(Order order) {
        final double basePrice = order.getBasePrice();
        if (basePrice > 1000) {
            return 0.05;
        }
        return 0.0;
    }

    // Java: after (inlined)

    public double calculateDiscount(Order order) {
        if (order.getBasePrice() > 1000) {
            return 0.05;
        }
        return 0.0;
    }
}
```

## 9. Known production uses

**IntelliJ IDEA's Inline Variable refactoring** automates the inlining by
replacing references to the selected variable with its initialiser and
removing the declaration. JetBrains documents that if the variable's
initial value is modified elsewhere in the code, only the occurrences
before that modification are inlined, so a reassigned variable is handled
selectively rather than refused outright
([JetBrains Inline documentation](https://www.jetbrains.com/help/idea/inline.html),
verified 2026-08-19).

**The TypeScript compiler's const inlining** is a compile time
optimisation where the compiler replaces const variable references with
their values during transpilation. The TypeScript documentation does not
explicitly document this optimisation, but the language specification
allows it because `const` variables cannot be reassigned
([TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/variable-declarations.html),
verified 2026-08-13).

## 10. Consequences

Positive.

- The indirection is removed, and the reader sees the expression directly.
- The variable declaration is removed, which reduces the line count.
- The function is shorter, which may make it easier to read if the variable
  was adding verbosity without clarity.

Negative.

- If the variable's name was communicative, the inline loses the name and
  the reader must parse the expression to understand the concept.
- The expression is evaluated at every use site, which is correct for pure
  expressions but wrong for expressions with side effects.
- The debugger loses an inspectable intermediate value, which makes
  debugging harder if the expression's value is important.
- If the variable is used multiple times, inlining duplicates the
  expression, which is a maintenance burden.

## 11. Failure modes and misuse

**Inlining a communicative name.** The variable's name communicates a
concept the expression does not, and inlining loses the concept. The
symptom is an expression whose intent is not obvious, where the variable
name used to communicate it.

**Inlining an expression with side effects.** The variable's initialiser
calls a function with a side effect, and inlining evaluates the function at
every use site. The symptom is a side effect that occurs more times than
expected, which is a behaviour change.

**Inlining a variable used multiple times.** The variable is referenced
several times, and inlining duplicates the expression at every site. The
symptom is duplicated expressions that Extract Variable would remove.

**Over inlining.** Every variable is inlined, producing expressions that
are long and hard to read. The symptom is a function with no named
intermediate values, where the reader must parse every expression from
scratch.

## 12. Trade-off matrix

| Alternative | Indirection | Naming | Evaluation | When to prefer |
|---|---|---|---|---|
| Inline Variable | Removed | None | Each use | Name adds no value, one use |
| Extract Variable | Added | High | Once, stored | Expression is complex, name helps |
| Replace Temp with Query | Changed | High, method | Each call | Variable should be a method |
| Keep variable | Present | Present | Once | Name is communicative |

## 13. Related and incompatible patterns

**Extract Variable** (same catalog) is the inverse. It names a
subexpression by assigning it to a variable, where Inline Variable removes
the name and puts the expression back at the use site.

**Inline Function** (same catalog) is the larger scale version. It replaces
a function call with the function body, where Inline Variable replaces a
variable reference with the variable's initialiser.

**Replace Temp with Query** (same catalog) is the alternative when the
variable should be a method call rather than a local. The expression is
extracted as a method, which enables reuse and removes the local variable.

## 14. Refactoring path in and out

**Path in.** The refactoring is introduced by replacing the reference with
the initialiser. The steps are:

1. Identify a variable whose name is not more informative than its
   initialiser.
2. Verify the variable is used once and the initialiser is pure.
3. Replace the reference with the initialiser.
4. Remove the declaration.
5. Run the test suite. Any failure means the initialiser had a side effect
   or the variable was used more than once.

**Path out.** The refactoring is reversed by Extract Variable, which names
the expression by assigning it to a variable. The reverse is applied when
the expression turns out to be complex enough to warrant a name.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test that exercised the function should produce the same result. A test
failure means the initialiser had a side effect or the evaluation order
changed.

## 16. Observability signals

The refactoring does not change behaviour, so the observable signal in
production is nothing. The one observable difference is in debugging: the
variable is no longer inspectable at a breakpoint, which is a debugging
visibility loss.

## 17. Security and privacy implications

The refactoring does not change what data is processed, so it does not
change the security surface. The security relevant case is when the
variable's name communicated a security boundary, for example
`isAuthorised`, and inlining loses the name. The expression
`token.role == ADMIN` at the use site may not be recognised as a security
boundary by a reader, where the variable name made it visible.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 6, "Inline Variable."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 6, "Inline Temp."
- JetBrains, "Inline,"
  [https://www.jetbrains.com/help/idea/inline.html](https://www.jetbrains.com/help/idea/inline.html),
  verified 2026-08-19.
- TypeScript, "Variable Declarations,"
  [https://www.typescriptlang.org/docs/handbook/variable-declarations.html](https://www.typescriptlang.org/docs/handbook/variable-declarations.html),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
