---
name: Move Field
slug: move-field
family: 03-refactoring
category: Refactoring
aliases: [Move Member, Relocate Field, Move Attribute]
first_described: "Fowler 1999"
maturity: canonical
related: [move-function, extract-class, inline-class, hide-delegate, change-reference-to-value]
incompatible_with: []
verified: 2026-08-13
---

# Move Field

## 1. Name, aliases, and lineage

The canonical name is **Move Field**, introduced by Martin Fowler in
*Refactoring. Improving the Design of Existing Code*, 1st edition,
Addison-Wesley, 1999, chapter 7, "Moving Features Between Objects." The
refactoring survived into the second edition, Martin Fowler, *Refactoring.
Improving the Design of Existing Code*, 2nd edition, Addison-Wesley, 2018,
chapter 9, "Moving Features," under the same name and with the same
mechanics. Fowler groups it with Move Function, Extract Class, Inline
Class, and Hide Delegate, because the five refactorings move features
between objects.

The underlying principle, that a field should live on the class that uses
it most, is one of the oldest ideas in object oriented design. Grady
Booch, in *Object-Oriented Analysis and Design with Applications*,
Benjamin Cummings, 1994, describes the principle of responsibility
driven design, where each class's fields and methods are determined by
the responsibilities it holds. A field on the wrong class is a sign that
the responsibilities are misplaced.

The alias **Move Member** is used in the C sharp community, where a field
is a member and the move is expressed as a refactoring in the IDE. The
alias **Relocate Field** is used in the Ruby community.

## 2. Problem and context

A field is on a class that does not use it, or that uses it less than
another class does. The field was placed on the original class because it
seemed related at the time, but over time the field's primary user has
become a different class, and the original class now has to delegate every
access to the other class, or the field is accessed from the other class
through a chain of references. The field is on the wrong side of the
relationship, and the misplacement produces delegation methods, chains of
access, and coupling that would not exist if the field were on the right
class.

The situation reads like this. An `Order` class has a `customerName`
field, because the original author thought the order should know the
customer's name. But the customer's name is set and read by the
`Customer` class, and the `Order` class only forwards every access to
`Customer`. The `customerName` field on `Order` is a pass through that
adds a field and a delegation method for every access, and a change to the
customer's name requires updating both `Customer` and `Order`, which is a
maintenance burden and a source of inconsistency.

The fix is to move the field. Move `customerName` from `Order` to
`Customer`, and remove the field and the delegation methods from `Order`.
`Order` accesses the name through its reference to `Customer`, which is
the natural path.

## 3. Forces

**Colocation versus access path.** A field should be colocated with the
class that uses it most, which reduces the access path. A field on the
wrong class has a long access path, which is coupling. The force favours
moving when the access path from the original class to the field is longer
than the access path from the target class.

**Delegation versus ownership.** A field on the wrong class requires
delegation methods, which are indirection. A field on the right class is
owned and accessed directly, which is simpler. The force favours moving
when the delegation burden exceeds the move cost.

**Coupling versus cohesion.** A field on the wrong class couples the two
classes through the delegation, because both classes must know about the
field. A field on the right class is cohesive with the class's other
fields and methods. The force favours moving when the move improves both
coupling and cohesion.

**Data versus behaviour.** A field that has no behaviour associated with it
is a data field, which can be moved freely. A field that has behaviour,
for example validation or computation, is harder to move because the
behaviour must move too. The force favours moving when the field is data
or when the behaviour moves with it via Move Function.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- The field is used more by another class than by the class that holds it,
  and the access path from the other class is shorter.
- The class that holds the field has delegation methods that forward every
  access to another class, which is a sign that the field is on the wrong
  side.
- The field's placement on the original class was accidental, based on a
  design decision that has since changed, and the field should be on the
  class whose responsibility it serves.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The field is used equally by both classes, and moving it to either would
  create a delegation from the other. The field should stay where it is,
  or both classes should be refactored to share the field through a third
  class.
- The field is part of the class's identity or invariant, and moving it
  would break the class's contract. For example, a `Customer` class's
  `id` field is part of its identity and should not be moved.
- The move would require updating a public API, and the field is
  referenced by consumers that cannot be updated.
- The field is a transient field that exists only for serialisation or
  framework purposes, and its placement is dictated by the framework.

## 5. Structure

The refactoring has two participants.

- **The source class.** The class that currently holds the field. After
  the refactoring, the field is removed.
- **The target class.** The class that will hold the field. After the
  refactoring, the field is on this class.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER
  ------                              -----

  class Order:                        class Order:
    customerName                        customer  (ref)
    customer  (ref)
                                      class Customer:
  class Customer:                       name  (moved here)
    (name is on Order)

  order.customerName                  order.customer.name
  (field on Order, accessed            (field on Customer, accessed
   through Order)                       through Order's ref)

  (field on wrong class)              (field on right class)
```

## 7. Dynamics

```
  t0  identify field on the wrong class
       |
       v
  t1  create the field on the target class
       |
       v
  t2  redirect all writes to the target
       (set the field on the target, not the source)
       |
       v
  t3  redirect all reads to the target
       (get the field from the target)
       |
       v
  t4  remove the field from the source class
       |
       v
  t5  remove delegation methods from source
       |
       v
  t6  run test suite
       |
       v
  t7  commit. the field is moved.
```

## 8. Implementation variants

**Move with self delegation.** The canonical variant. The field is
created on the target, and the source's accessors delegate to the target
during the transition. After all callers are updated, the source's field
and accessors are removed.

**Move with encapsulation.** The field is moved with its accessors and
validation, which preserves the invariant on the target class. This
variant combines Move Field with Encapsulate Variable.

**Move via constructor.** The field is set on the target through its
constructor, and the source's constructor passes the value. This variant
is used when the field is required and the target's constructor is the
right place to set it.

```python
# Python: before (field on wrong class)

class Order:
    def __init__(self, customer_name: str):
        self.customer_name = customer_name
        self.customer: Customer | None = None

class Customer:
    pass  # name is on Order, wrong

# Python: after (field moved to Customer)

class Order:
    def __init__(self, customer: "Customer"):
        self.customer = customer

    @property
    def customer_name(self) -> str:
        return self.customer.name

class Customer:
    def __init__(self, name: str):
        self.name = name
```

```typescript
// TypeScript: after (field on Customer)

class Order {
    constructor(private _customer: Customer) {}

    get customerName(): string {
        return this._customer.name;
    }

    get customer(): Customer { return this._customer; }
}

class Customer {
    constructor(public name: string) {}
}
```

```java
// Java: after (field on Customer, Order delegates)

public class Order {
    private final Customer customer;

    public Order(Customer customer) {
        this.customer = customer;
    }

    public String getCustomerName() {
        return customer.getName();
    }
}

class Customer {
    private String name;

    public Customer(String name) {
        this.name = name;
    }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
}
```

## 9. Known production uses

**IntelliJ IDEA's Move refactoring** automates this move at the tooling
level. JetBrains documents that the Move refactoring moves class members,
including fields, to other classes, the exact mechanic this pattern
performs by hand
([JetBrains Move documentation](https://www.jetbrains.com/help/idea/move-refactorings.html),
verified 2026-08-19).

**Eclipse's "Move" refactoring** provides the same automation for Java
fields and methods
([Eclipse Move refactoring](https://help.eclipse.org/latest/topic/org.eclipse.jdt.doc.user/tasks/task-moving.html),
verified 2026-08-13).

## 10. Consequences

Positive.

- The field is colocated with the class that uses it most, which reduces
  the access path and the delegation.
- The coupling between the two classes is reduced, because the source
  class no longer holds a field that belongs to the target.
- The cohesion of both classes is improved, because each class holds the
  fields it uses.

Negative.

- The move changes the access path, which means every access site must be
  updated, which is a mechanical change but a wide one.
- If the move was wrong, the field may need to be moved back, which is the
  same cost in reverse.
- The move may introduce a new dependency from the source to the target,
  if the source previously did not reference the target.

## 11. Failure modes and misuse

**Moving a field that is used equally.** The field is used equally by
both classes, and the move creates a delegation from the source to the
target that is the same as the delegation that existed from the target to
the source. The symptom is the same number of delegation methods, just in
the other direction.

**Moving a field that breaks an invariant.** The field is part of the
source class's invariant, and moving it to the target breaks the source's
ability to enforce the invariant. The symptom is a source class that can
no longer guarantee its fields are consistent.

**Moving a field and forgetting to update a caller.** A caller that
accessed the field through the source's accessor is not updated to access
through the target. The symptom is a compile error in a statically typed
language or a runtime error in a dynamically typed language.

**Over moving.** Fields are moved frequently based on temporary usage
patterns, and the codebase is in constant flux. The symptom is a codebase
where fields are always in the process of moving, which makes the code
hard to read and understand.

## 12. Trade-off matrix

| Alternative | Access path | Delegation | Cohesion | When to prefer |
|---|---|---|---|---|
| Move Field | Shortened | Reduced | Improved | Field on wrong class |
| Hide Delegate | Shortened for client | Added on server | Same | Client reaches through |
| Extract Class | Changed | None | Improved | Two responsibilities |
| Keep field | Unchanged | Present | Lower | Field on right class |

## 13. Related and incompatible patterns

**Move Function** (same catalog) is the method version. It moves a method
to the class that uses it most, where Move Field moves a field. The two
are frequently applied together: move the field, then move the methods
that operate on it.

**Extract Class** (same catalog) is the larger scale version. It moves a
group of fields and methods to a new class, where Move Field moves one
field.

**Hide Delegate** (same catalog) is related when the move is motivated by
a chain of access. Hiding the delegate shortens the chain, and Move Field
moves the field to the class that needs it.

## 14. Refactoring path in and out

**Path in.** The refactoring is introduced by creating the field on the
target and redirecting accesses. The steps are:

1. Create the field on the target class.
2. Redirect all writes to the target.
3. Redirect all reads to the target.
4. Remove the field from the source class.
5. Remove delegation methods from the source.
6. Run the test suite. Any failure means an access was not redirected.

**Path out.** The refactoring is reversed by moving the field back to the
source. The reverse is applied when the move turned out to be wrong, for
example because the field is used equally by both classes.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test that accessed the field should produce the same result, now through
the target class.

## 16. Observability signals

The refactoring does not change behaviour, so the observable signal in
production is nothing. The access path may change in logs and traces,
which is a minor format change.

## 17. Security and privacy implications

The refactoring does not change what data is stored or how it is accessed,
so it does not change the security surface. The security relevant case is
when the move places the field on a class with stronger access control,
which is a positive security signal.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 9, "Move Field."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 7, "Move Field."
- Grady Booch, *Object-Oriented Analysis and Design with Applications*,
  Benjamin Cummings, 2nd edition, 1994.
- JetBrains, "Move,"
  [https://www.jetbrains.com/help/idea/move-refactorings.html](https://www.jetbrains.com/help/idea/move-refactorings.html),
  verified 2026-08-19.
- Eclipse Foundation, "Moving,"
  [https://help.eclipse.org/latest/topic/org.eclipse.jdt.doc.user/tasks/task-moving.html](https://help.eclipse.org/latest/topic/org.eclipse.jdt.doc.user/tasks/task-moving.html),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
