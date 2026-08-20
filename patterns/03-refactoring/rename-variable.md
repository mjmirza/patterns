---
name: Rename Variable
slug: rename-variable
family: 03-refactoring
category: Refactoring
aliases: [Rename Local, Rename Temp, Rename Binding]
first_described: "Fowler 2018"
maturity: canonical
related: [rename-field, extract-variable, inline-variable, change-function-declaration, encapsulate-variable]
incompatible_with: []
verified: 2026-08-13
---

# Rename Variable

## 1. Name, aliases, and lineage

The canonical name is **Rename Variable**, introduced by Martin Fowler in
*Refactoring. Improving the Design of Existing Code*, 2nd edition,
Addison-Wesley, 2018, chapter 6, "A First Set of Refactorings." The
refactoring is new to the second edition as a separate entry, though the
broader Rename Method from the first edition (1999) covered the case of
renaming local variables. Fowler split it out because renaming a local
variable has different mechanics: it has no serialisation contract, no
public API, and no accessor methods. It is the simplest rename, but it
is also the most common.

The underlying principle, that a variable name should communicate what
the value represents, is the intention revealing names principle from
Kent Beck, *Smalltalk Best Practice Patterns*, Prentice Hall, 1997. A
variable name like `x` or `temp` communicates nothing, and a name like
`customerId` or `totalPrice` communicates the concept. The rename is
the mechanical path from an opaque name to a communicative one.

The term **rename** is used by all refactoring tools and across all
communities. The alias **Rename Local** is used to distinguish the
operation from renaming fields. The alias **Rename Binding** is used in
the functional programming community, where variables are bindings.

## 2. Problem and context

A local variable has a name that does not communicate what the value
represents. The name was chosen for brevity, or it was accurate when the
variable was created but the meaning changed, or it was a placeholder
that was never replaced. Every reader who encounters the variable must
determine its meaning from the surrounding code, which takes time and
produces misunderstandings.

The situation reads like this. A function has a variable `a` that holds
the result of a complex calculation. The name `a` communicates nothing.
A reader who sees `a = compute(order)` must trace the usage of `a`
through the function to understand what it represents. If the variable
were named `totalCharge`, the reader would understand immediately.

The fix is to rename the variable. Change `a` to `totalCharge`, and
update every reference within the function's scope. The name now
communicates the concept at every use.

## 3. Forces

**Communication versus brevity.** A longer name communicates more, but
takes more space. A shorter name is briefer, but communicates less. The
force favours longer names when the communication benefit exceeds the
space cost, which is almost always for variables that represent domain
concepts.

**Scope versus ceremony.** A variable with a wide scope is used in many
places, and a good name saves time for every reader. A variable with a
narrow scope is used in one or two lines, and a long name adds ceremony
without proportionate benefit. The force favours descriptive names for
wide scope variables and short names for narrow scope variables.

**Convention versus meaning.** A naming convention may require a
specific pattern, for example `i` for loop indices or `_` for unused
variables. The force favours convention when the convention is load
bearing, and favours meaning when the convention obscures the concept.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- A variable name does not communicate what the value represents, and a
  better name exists.
- The variable has a scope wide enough that a reader encounters it more
  than once, and the name would save time on each encounter.
- The name was a placeholder or abbreviation that was never replaced with
  a meaningful name.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The variable has a narrow scope, for example a loop index or a one line
  intermediate, and the name is adequate for the scope. Renaming a loop
  index from `i` to `rowIndex` adds ceremony without proportionate
  benefit.
- The variable name follows a convention that is load bearing for the
  codebase, for example `self` in Python or `this` in Java, and renaming
  would break the convention.
- The variable is a destructuring binding where the name is determined by
  the structure, and renaming would break the destructure.

## 5. Structure

The refactoring has one participant: the variable whose name is changed.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER
  ------                              -----

  a = compute(order)                  totalCharge = compute(order)
  print(a)                            print(totalCharge)
```

## 7. Dynamics

```
  t0  identify variable with opaque name
       |
       v
  t1  choose a name that communicates
       what the value represents
       |
       v
  t2  rename the declaration
       |
       v
  t3  update every reference
       (compiler finds them in static languages)
       |
       v
  t4  run test suite
       |
       v
  t5  commit. variable renamed.
```

## 8. Implementation variants

**Rename in place.** The canonical variant. The variable is renamed, and
every reference within the scope is updated.

**Rename via extract.** The variable is extracted into a new function,
which gives it a fresh name and a fresh scope. This variant is used when
the variable's scope is too wide for a simple rename.

**Rename with type annotation.** In languages with type annotations, the
rename is accompanied by a type annotation that documents the variable's
type, which is additional communication.

```python
# Python: before (opaque name)

def process(order):
    a = order.quantity * order.unit_price
    if a > 1000:
        a *= 0.9  # discount
    return a

# Python: after (renamed)

def process(order):
    total_charge = order.quantity * order.unit_price
    if total_charge > 1000:
        total_charge *= 0.9  # discount
    return total_charge
```

```typescript
// TypeScript: before (opaque name)

interface Order {
    quantity: number;
    unitPrice: number;
}

function processOrderBefore(order: Order): number {
    const a = order.quantity * order.unitPrice;
    return a > 1000 ? a * 0.9 : a;
}

// TypeScript: after (renamed)

function processOrder(order: Order): number {
    const totalCharge = order.quantity * order.unitPrice;
    return totalCharge > 1000 ? totalCharge * 0.9 : totalCharge;
}
```

```java
// Java: before (opaque name)

class Order {
    private final double quantity;
    private final double unitPrice;

    public Order(double quantity, double unitPrice) {
        this.quantity = quantity;
        this.unitPrice = unitPrice;
    }

    public double getQuantity() { return quantity; }
    public double getUnitPrice() { return unitPrice; }
}

public class PricingService {
    public double processBefore(Order order) {
        double a = order.getQuantity() * order.getUnitPrice();
        if (a > 1000) {
            a *= 0.9;
        }
        return a;
    }

    // Java: after (renamed)

    public double process(Order order) {
        double totalCharge = order.getQuantity() * order.getUnitPrice();
        if (totalCharge > 1000) {
            totalCharge *= 0.9;
        }
        return totalCharge;
    }
}
```

## 9. Known production uses

**IntelliJ IDEA's "Rename Variable" refactoring** automates the rename by
finding every reference within the variable's scope and updating it
([JetBrains Rename refactoring](https://www.jetbrains.com/help/idea/rename-refactorings.html),
verified 2026-08-20).

**Eclipse's "Rename Local Variable" refactoring** provides the same
automation for Java local variables
([Eclipse Rename refactoring](https://help.eclipse.org/latest/topic/org.eclipse.jdt.doc.user/tasks/task-renaming.html),
verified 2026-08-13).

## 10. Consequences

Positive.

- The variable name communicates what the value represents, which
  improves readability at every use site.
- The concept is communicable: a reviewer can say "the total charge is
  wrong" instead of "the variable a is wrong."
- The compiler catches every reference in a static language, which makes
  the rename safe.

Negative.

- The rename churns the diff, which adds lines and may produce merge
  conflicts with concurrent branches.
- The old name may persist in comments, documentation, and muscle memory,
  which creates a disconnect for readers who learned the old name.

## 11. Failure modes and misuse

**Renaming to a name that is only temporarily better.** The new name is
accurate today but becomes misleading when the variable's meaning changes
tomorrow. This is the same failure mode as Rename Field, and the fix is
the same: choose a name that is stable across meaning changes.

**Renaming a loop index.** The variable `i` in a loop is a convention
that every reader recognises. Renaming it to `index` or `rowIndex` adds
verbosity without proportionate benefit for a narrow scope variable.

**Renaming a shadowed variable.** An inner scope variable shadows an
outer scope variable with the same name. Renaming the inner variable to
match the outer variable's intended name produces confusion, because the
reader cannot tell which scope the variable is in.

## 12. Trade-off matrix

| Alternative | Communication | Churn | When to prefer |
|---|---|---|---|
| Rename Variable | Improved | Present | Name is opaque, scope is wide |
| Extract Variable | Improved (new name) | Present | Expression is complex |
| Rename Field | Improved | Present + serialisation | Field on a class |
| Keep name | None | None | Name is adequate |

## 13. Related and incompatible patterns

**Rename Field** (same catalog) is the class field version, which has
additional mechanics for serialisation and accessors.

**Extract Variable** (same catalog) creates a new variable from a
subexpression, which gives the subexpression a name for the first time.

**Inline Variable** (same catalog) removes a variable by replacing its
references with its initialiser, which is the opposite of naming.

**Change Function Declaration** (same catalog) is the function version,
which has additional mechanics for callers and public APIs.

## 14. Refactoring path in and out

**Path in.** Rename the declaration, update references, run tests.

**Path out.** Rename back to the old name, which is rarely applied.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test should produce the same result, now through the new name.

## 16. Observability signals

The refactoring does not change behaviour, so the observable signal in
production is nothing. The variable name is not visible in production
observability unless it appears in a log message, which is a minor format
change.

## 17. Security and privacy implications

The refactoring does not change what data is processed, so it does not
change the security surface. A clearer name may help a reader understand
the security implications of the variable, which is a minor positive.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 6, "Rename Variable."
- Kent Beck, *Smalltalk Best Practice Patterns*, Prentice Hall, 1997,
  "Intention Revealing Names."
- JetBrains, "Rename refactoring,"
  [https://www.jetbrains.com/help/idea/rename-refactorings.html](https://www.jetbrains.com/help/idea/rename-refactorings.html),
  verified 2026-08-13.
- Eclipse Foundation, "Renaming,"
  [https://help.eclipse.org/latest/topic/org.eclipse.jdt.doc.user/tasks/task-renaming.html](https://help.eclipse.org/latest/topic/org.eclipse.jdt.doc.user/tasks/task-renaming.html),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
