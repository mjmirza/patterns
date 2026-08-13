---
name: Extract Variable
slug: extract-variable
family: 03-refactoring
category: Refactoring
aliases: [Introduce Explaining Variable, Split Temporary Variable, Extract Local]
first_described: "Fowler 1999"
maturity: canonical
related: [extract-function, inline-variable, encapsulate-variable, replace-temp-with-query, introduce-parameter-object]
incompatible_with: []
verified: 2026-08-13
---

# Extract Variable

## 1. Name, aliases, and lineage

The canonical name is **Extract Variable**, introduced by Martin Fowler
in *Refactoring. Improving the Design of Existing Code*, 1st edition,
Addison-Wesley, 1999, chapter 6, "Composing Methods," where it appeared
as **Introduce Explaining Variable.** In the second edition, Martin
Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
edition, Addison-Wesley, 2018, chapter 6, "A First Set of Refactorings,"
Fowler renamed it to Extract Variable to follow the naming convention of
his other extract refactorings, Extract Function and Extract Class.

The underlying idea, that a complex expression should be broken into
named subexpressions so each part is readable, goes back to the earliest
structured programming literature. The term **explaining variable** is
used by Kent Beck in *Smalltalk Best Practice Patterns*, Prentice Hall,
1997, where he describes naming a temporary variable for the concept it
represents rather than for the computation it performs. Joshua Kerievsky,
in *Refactoring to Patterns*, Addison-Wesley, 2004, uses the same
technique as a step toward the Compose Method pattern and the Named
Parameter pattern.

The alias **Split Temporary Variable** is a related but distinct
refactoring from Fowler's first edition, where a temporary variable is
assigned multiple times for different purposes and should be split into
separate variables. Fowler merged the concept into Extract Variable in
the second edition, because the mechanics are the same: name each use of
a variable for what it represents.

## 2. Problem and context

You have an expression that is hard to read because it combines several
subexpressions into one statement. The expression is correct, but a
reader must parse it from the inside out to understand what each part
does, and the intent of each part is not visible from the code because the
subexpressions have no names. The expression may also be duplicated,
appearing in multiple places with the same structure, and the
duplication is a maintenance burden.

The situation reads like this. A pricing function calculates a
discounted total:

```
price = (basePrice + basePrice * taxRate) * (1 - discountRate) * quantity;
```

The expression nests three levels of arithmetic, and a reader must parse
the parentheses to understand the order of operations. The subexpression
`basePrice + basePrice * taxRate` is the price with tax, and
`1 - discountRate` is the discount multiplier, but neither concept has a
name. A change to the tax calculation requires finding the subexpression
in the middle of the larger expression, which is error prone.

The fix is to extract each subexpression into a named variable:

```
priceWithTax = basePrice + basePrice * taxRate;
discountMultiplier = 1 - discountRate;
price = priceWithTax * discountMultiplier * quantity;
```

Each concept has a name, and the final calculation reads as a sentence:
price is price with tax times discount multiplier times quantity.

## 3. Forces

**Readability versus brevity.** A named variable communicates the intent
of each subexpression, which is readable. An inline expression is briefer,
which is less ceremony but requires the reader to parse the expression to
understand the intent. The force favours extraction when the expression is
complex enough that names help, and favours inlining when the expression
is simple enough that names add verbosity without clarity.

**Naming versus anonymity.** A named variable can be talked about: a
reviewer can say "the price with tax is wrong" instead of "the first
parenthesised subexpression in line 42 is wrong." An inline expression has
no name beyond its position in the code. The force favours extraction
when the subexpression represents a concept the team needs to talk about.

**Evaluation versus storage.** An extracted variable stores the result of
the subexpression, which means it is evaluated once even if the original
expression evaluated the subexpression multiple times. The force favours
extraction when the subexpression is expensive and is evaluated more than
once, and is neutral when the subexpression is cheap.

**Mutation versus immutability.** A variable can be reassigned, which is
flexible but also a source of bugs when the variable's value changes
between uses. An inline expression is always evaluated fresh, which is
safe but may be expensive. The force favours extraction with an immutable
variable (final, const, val) when both safety and naming are wanted.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- The expression is complex enough that a reader cannot understand it at a
  glance, and the subexpressions represent concepts that names can
  communicate.
- The expression is duplicated, and extracting the subexpression into a
  variable would make the duplication visible and the change localised.
- The expression has side effects or expensive computation that should be
  evaluated once, and the inline form evaluates it multiple times.
- The expression appears in a conditional, and naming the condition's
  parts makes the branching logic readable.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The expression is simple, for example `a + b`, and a name would add
  verbosity without clarity. The variable `sum = a + b` is longer than the
  expression itself and communicates nothing the expression did not.
- The subexpression does not represent a concept that needs a name. It is
  an intermediate result with no domain meaning, and naming it would
  produce a variable whose name is a restatement of the expression, for
  example `basePricePlusTax` which is not a concept, just a description of
  the arithmetic.
- The language has a pipeline or composition operator that makes the
  expression readable without names, for example Elixir's pipe operator or
  JavaScript's optional chaining. The pipeline is the language's idiom for
  readable complex expressions, and extracting variables would fight the
  idiom.
- The expression is in a hot loop where the variable allocation is
  unacceptable, though in most languages a local variable does not
  allocate because it lives on the stack.

## 5. Structure

The refactoring has one participant.

- **The expression.** A complex subexpression inside a larger expression
  or statement. After the refactoring, it is assigned to a named variable,
  and the variable is used in place of the subexpression.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER
  ------                              -----

  price = (basePrice                  priceWithTax = basePrice
           + basePrice                                  + basePrice * taxRate
           * taxRate)
          * (1 - discountRate)        discountMultiplier = 1 - discountRate
          * quantity
                                      price = priceWithTax
                                                * discountMultiplier
                                                * quantity

  (nested expression, no names)       (named subexpressions, readable)
```

## 7. Dynamics

```
  t0  identify complex expression
       |
       v
  t1  identify a subexpression
       that represents a concept
       |
       v
  t2  declare a variable named for
       the concept (not the arithmetic)
       |
       v
  t3  assign the subexpression to the variable
       |
       v
  t4  replace the subexpression with the variable
       in the original expression
       |
       v
  t5  repeat for other subexpressions
       |
       v
  t6  run test suite
       |
       v
  t7  commit. the expression is decomposed.
```

## 8. Implementation variants

**Named local variable.** The canonical variant. A local variable is
declared, the subexpression is assigned to it, and the variable is used in
place of the subexpression. The variable should be final or const to
prevent reassignment, which would defeat the naming benefit.

**Destructuring.** In languages with destructuring, such as JavaScript
and Python, multiple subexpressions can be extracted in one statement.
The subexpressions are assigned to named variables through destructuring,
which is the language's idiom for multi extraction.

**Const expression.** In languages with compile time constants, the
subexpression can be extracted as a const, which is evaluated at compile
time. This variant is used when the subexpression is a literal or a
constant expression, not a runtime computation.

**Inline return.** In functional languages or in expression bodied
functions, the subexpression can be extracted into a local function or a
let binding, which is the functional variant of a named variable.

```python
# Python: before (complex expression)

def calculate_price(base: float, tax: float,
                    discount: float, qty: int) -> float:
    return (base + base * tax) * (1 - discount) * qty

# Python: after (extracted variables)

def calculate_price(base: float, tax: float,
                    discount: float, qty: int) -> float:
    price_with_tax: float = base + base * tax
    discount_multiplier: float = 1 - discount
    return price_with_tax * discount_multiplier * qty
```

```typescript
// TypeScript: before (nested ternary)

function getLabel(score: number): string {
    return score > 90 ? "A" : score > 80 ? "B" : score > 70 ? "C" : "F";
}

// TypeScript: after (extracted variables)

function getLabel(score: number): string {
    const isA: boolean = score > 90;
    const isB: boolean = score > 80;
    const isC: boolean = score > 70;
    return isA ? "A" : isB ? "B" : isC ? "C" : "F";
}
```

```java
// Java: before (complex expression in a conditional)

public boolean isEligible(Person person) {
    return person.getAge() >= 18
        && person.getContributions() > 0
        && !person.isRetired()
        && person.getYearsOfService() >= 5;
}

// Java: after (extracted variables)

public boolean isEligible(Person person) {
    final boolean isAdult = person.getAge() >= 18;
    final boolean hasContributed = person.getContributions() > 0;
    final boolean isNotRetired = !person.isRetired();
    final boolean hasService = person.getYearsOfService() >= 5;
    return isAdult && hasContributed && isNotRetired && hasService;
}
```

## 9. Known production uses

**The Java standard library's `String.format` method** uses extracted
variables internally to break down the format string parsing. The OpenJDK
source for `String.format` extracts the format specifier, the width, the
precision, and the argument into separate named variables before
constructing the output, rather than parsing the format string in one
expression ([OpenJDK String.java](https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/java/lang/String.java),
verified 2026-08-13). This is the production variant of the refactoring
applied to a complex parsing expression.

**Python's `statistics.median` function** extracts the sorted list and
the midpoint into named variables rather than computing them inline in the
return expression. The CPython source for `statistics.median` declares
`data = sorted(data)` and `n = len(data)` before computing the median
([CPython statistics.py](https://github.com/python/cpython/blob/main/Lib/statistics.py),
verified 2026-08-13). This is the production variant applied to a
statistical calculation.

## 10. Consequences

Positive.

- Each subexpression has a name, which communicates its intent at the
  point of use.
- The expression reads as a sequence of named steps, which is readable at
  a high level without requiring the reader to parse the arithmetic.
- The subexpression is evaluated once, which is safe if it has side
  effects and efficient if it is expensive.
- A debugger can inspect the variable at a breakpoint, which gives
  visibility into the intermediate value that an inline expression does
  not provide.

Negative.

- The number of local variables increases, which adds lines and may make
  the function longer.
- The variable names must be chosen well, and a bad name is worse than no
  name because it misleads the reader about the intent.
- The variable may be reassigned by a later statement, which defeats the
  naming benefit and introduces a mutation that the inline expression did
  not have.
- The extraction can be over applied, naming trivial subexpressions that
  add verbosity without clarity.

## 11. Failure modes and misuse

**Variable that restates the expression.** The variable is named
`basePlusTax` instead of `priceWithTax`, which restates the arithmetic
rather than naming the concept. A reader who sees `basePlusTax` must still
understand the arithmetic to know what the variable represents. The fix
is to name the variable for the concept, not the computation.

**Variable that is reassigned.** The variable is declared as mutable, and
a later statement assigns a different value to it, which means the name
is wrong for the second value. The symptom is a variable whose name
describes the first value but whose value at a later point is something
else, which is a source of confusion. The fix is to declare the variable
as final or const, which prevents reassignment.

**Over extraction.** Every subexpression of every expression is extracted
into a variable, producing a function with twenty variables where the
original expression was three lines. The symptom is a function that is
longer and harder to read than the inline version, because the reader must
trace each variable to understand the expression.

**Meaningless name.** The variable is named `temp` or `result` or `x`,
which communicates nothing. The extraction has added a variable without
adding clarity, because the name is as opaque as the expression it
replaced.

## 12. Trade-off matrix

| Alternative | Naming | Indirection | Evaluation | When to prefer |
|---|---|---|---|---|
| Extract Variable | High, subexpression named | One variable | Once, stored | Expression is complex, subexpressions have meaning |
| Extract Function | High, block named | One function call | Once per call | Block is reusable or complex |
| Inline Variable | None | None | Each use | Variable is trivial, name adds no value |
| Replace Temp with Query | High, query named | One method call | Each call | Subexpression is a query that should be a method |

## 13. Related and incompatible patterns

**Extract Function** (same catalog) is the block level version. It
extracts a block of statements into a named function, where Extract
Variable extracts a subexpression into a named variable. The two are the
two levels of naming: expressions and blocks.

**Inline Variable** (same catalog) is the inverse. It replaces a variable
reference with the variable's initialiser, which removes the variable. The
reverse is applied when the variable adds indirection without clarity.

**Replace Temp with Query** (same catalog) is the next step when the
extracted variable should be a method call rather than a local. The
subexpression is extracted as a method that returns the value, which
enables reuse and removes the local variable.

**Split Temporary Variable** (same catalog, first edition) is the related
refactoring for a variable that is assigned multiple times for different
purposes. The fix is to split it into separate variables, each named for
its purpose, which is a specific application of Extract Variable.

## 14. Refactoring path in and out

**Path in.** The refactoring is introduced by assigning a subexpression
to a named variable. The steps are:

1. Identify a complex expression with a subexpression that represents a
   concept.
2. Declare a variable named for the concept.
3. Assign the subexpression to the variable.
4. Replace the subexpression with the variable in the original expression.
5. Repeat for other subexpressions if needed.
6. Run the test suite. Any failure means the subexpression was extracted
   incorrectly or the variable was named misleadingly.

**Path out.** The refactoring is reversed by Inline Variable, which
replaces the variable reference with the variable's initialiser. The
reverse is applied when the variable is trivial and the name adds no
value over the expression itself.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test that exercised the expression should produce the same result. A test
failure means the subexpression was extracted incorrectly, for example the
operator precedence changed because the extraction introduced implicit
grouping.

A new test is not strictly needed, because the extracted variable is an
implementation detail that does not change the function's interface. If the
variable is extracted as a query method (Replace Temp with Query), the
query method should have its own tests.

## 16. Observability signals

The refactoring does not change behaviour, so the observable signal in
production is nothing. The one observable difference is in debugging: a
debugger can inspect the extracted variable at a breakpoint, which gives
visibility into the intermediate value that the inline expression did not
expose. This is a debugging improvement, not a production observability
change.

## 17. Security and privacy implications

The refactoring does not change what data is processed or how it is
stored, so it does not change the security surface. The security relevant
case is when the subexpression is a security check, for example a
comparison against a threshold, and the extracted variable name makes the
security boundary visible in the code. A reader who sees
`isAuthorised = token.role == ADMIN` understands the check, where an inline
expression in a complex conditional might not make the security boundary
visible.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 6, "Extract Variable."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 6, "Introduce Explaining
  Variable."
- Kent Beck, *Smalltalk Best Practice Patterns*, Prentice Hall, 1997.
- Joshua Kerievsky, *Refactoring to Patterns*, Addison-Wesley, 2004.
- OpenJDK, "String.java,"
  [https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/java/lang/String.java](https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/java/lang/String.java),
  verified 2026-08-13.
- CPython, "statistics.py,"
  [https://github.com/python/cpython/blob/main/Lib/statistics.py](https://github.com/python/cpython/blob/main/Lib/statistics.py),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
