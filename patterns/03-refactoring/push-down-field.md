---
name: Push Down Field
slug: push-down-field
family: 03-refactoring
category: Refactoring
aliases: [Push Down Attribute, Move Field to Subclass]
first_described: "Fowler 1999"
maturity: canonical
related: [pull-up-field, push-down-method, extract-subclass, collapse-hierarchy, replace-inheritance-with-delegation, move-field]
incompatible_with: []
verified: 2026-08-13
---

# Push Down Field

## 1. Name, aliases, and lineage

The canonical name is **Push Down Field**, introduced by Martin Fowler in
*Refactoring. Improving the Design of Existing Code*, 1st edition,
Addison-Wesley, 1999, chapter 11, "Dealing with Generalization." The
refactoring survived into the second edition, Martin Fowler, *Refactoring.
Improving the Design of Existing Code*, 2nd edition, Addison-Wesley, 2018,
chapter 12, "Simplification and Generalization," under the same name.
Fowler groups it with Pull Up Field, Pull Up Method, and Push Down Method,
because the four refactorings move features within an inheritance
hierarchy in opposite directions.

The underlying idea, that a field on a superclass that is only used by one
subclass should be moved to that subclass, is the inverse of Pull Up
Field. The field was placed on the superclass speculatively, expecting
all subclasses to use it, but only one does. The field is now dead weight
on every other subclass, and it should be pushed down to the one
subclass that uses it.

## 2. Problem and context

A field on the superclass is only used by one subclass. The other
subclasses inherit the field but never read or write it. The field was
placed on the superclass because the author expected it to be shared, but
the expectation was wrong, or the field was once shared and the other
subclasses stopped using it. The field is now dead weight on the
superclass, and it gives every subclass a field it does not need.

The situation reads like this. A `Person` superclass has an `interestRate`
field that is only used by `Employee`, because only employees have an
interest rate calculation. `Customer` inherits the field but never uses
it. A reader who sees `interestRate` on `Person` expects it to be a
shared field, and they must discover that it is only for `Employee` by
reading the code. The field pollutes the superclass's interface.

The fix is to push down the field. Move `interestRate` from `Person` to
`Employee`, and remove it from the superclass. `Customer` no longer
inherits it, and the superclass's interface is cleaner.

## 3. Forces

**Interface cleanliness versus subclass burden.** A field on the
superclass that only one subclass uses is dead weight on the others.
Pushing it down removes the dead weight but gives the one subclass a
field it now owns. The force favours pushing down when the field is only
on one subclass.

**Speculation versus present reality.** The field was placed on the
superclass speculatively, expecting sharing. Pushing it down accepts that
the speculation was wrong. The force favours pushing down when the
speculation is clearly wrong, and favours keeping when the field may be
needed by future subclasses.

**Access path versus ownership.** A field on the superclass is accessed
through the superclass type, which is a short path. A field on the
subclass is accessed through the subclass type, which requires a cast or
a type check. The force favours keeping when the access path matters, and
favours pushing down when the subclass specific ownership is correct.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- A field on the superclass is only used by one subclass.
- The field is dead weight on the other subclasses, which inherit it but
  never use it.
- The field was placed on the superclass speculatively and the speculation
  was wrong, or the field was once shared and the other subclasses stopped
  using it.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The field is used by more than one subclass, even if not all. The fix
  is to create an intermediate superclass for the subclasses that share
  the field, not to push it down to one.
- The field is part of the superclass's contract, and consumers access it
  through the superclass type. Pushing it down breaks the contract.
- The field is a final field that is initialised in the superclass
constructor, and pushing it down requires pushing down the constructor
logic as well, which may not be feasible.

## 5. Structure

The refactoring has one participant: the field that is moved from the
superclass to the subclass.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER
  ------                              -----

  class Person:                      class Person:
    name                                name
    interestRate  (only Employee)
                                     class Employee(Person):
  class Employee(Person):              interestRate  (pushed down)
    (uses interestRate)               (uses interestRate)
    salary                             salary

  class Customer(Person):            class Customer(Person):
    (inherits but never uses           discount
     interestRate)
                                     (Customer no longer has interestRate)
```

## 7. Dynamics

```
  t0  identify field on superclass
       used by only one subclass
       |
       v
  t1  declare the field on the subclass
       |
       v
  t2  move initialisation to the subclass
       constructor or accessor
       |
       v
  t3  remove the field from the superclass
       |
       v
  t4  update any code that accessed the
       field through the superclass type
       (requires a cast or a type check)
       |
       v
  t5  run test suite
       |
       v
  t6  commit. the field is pushed down.
```

## 8. Implementation variants

**Push down with accessor.** The canonical variant. The field is moved
to the subclass, and accessors are provided on the subclass.

**Push down with constructor.** The field is moved, and the subclass
constructor initialises it instead of the superclass constructor.

**Push down to intermediate class.** The field is used by two of five
subclasses. An intermediate superclass is created for those two, and the
field is pushed down to the intermediate class, not to a single subclass.

```python
# Python: before (field on superclass, only one subclass uses it)

class Person:
    def __init__(self, name: str, interest_rate: float = 0.0):
        self.name = name
        self.interest_rate = interest_rate

class Employee(Person):
    def calculate_interest(self) -> float:
        return self.interest_rate * 100

class Customer(Person):
    pass  # inherits interest_rate but never uses it

# Python: after (pushed down to Employee)

class Person:
    def __init__(self, name: str):
        self.name = name

class Employee(Person):
    def __init__(self, name: str, interest_rate: float):
        super().__init__(name)
        self.interest_rate = interest_rate

    def calculate_interest(self) -> float:
        return self.interest_rate * 100

class Customer(Person):
    pass  # no longer has interest_rate
```

```typescript
// TypeScript: after (pushed down)

class Person {
    constructor(public name: string) {}
}

class Employee extends Person {
    constructor(name: string, public interestRate: number) {
        super(name);
    }

    calculateInterest(): number {
        return this.interestRate * 100;
    }
}

class Customer extends Person {}
```

```java
// Java: after (pushed down)

public class Person {
    private final String name;

    public Person(String name) {
        this.name = name;
    }

    public String getName() { return name; }
}

public class Employee extends Person {
    private final double interestRate;

    public Employee(String name, double interestRate) {
        super(name);
        this.interestRate = interestRate;
    }

    public double calculateInterest() {
        return interestRate * 100;
    }
}

public class Customer extends Person {
    // no interestRate field
}
```

## 9. Known production uses

**Java's `java.awt.Component` class hierarchy** demonstrates this
refactoring. `Component` holds fields shared by all components, while
`Container` holds fields specific to container components (like layout
management), and `Window` holds fields specific to windows (like window
listeners). Fields that were once on `Component` but turned out to be
container or window specific were pushed down to the appropriate subclass
([java.awt.Component](https://docs.oracle.com/en/java/javase/21/docs/api/java.desktop/java/awt/Component.html),
verified 2026-08-13).

**Python's exception hierarchy** shows push down in practice. The
`Exception` base class holds `args`, while `OSError` holds `errno` and
`strerror`, which were pushed down from the base because only OS errors
have those fields
([Python Exception hierarchy](https://docs.python.org/3/library/exceptions.html),
verified 2026-08-13).

## 10. Consequences

Positive.

- The superclass's interface is cleaner, because it no longer holds a
  field that only one subclass uses.
- The other subclasses no longer inherit dead weight.
- The field is colocated with the subclass that uses it, which is the
  correct ownership.

Negative.

- Code that accessed the field through the superclass type must now
  access it through the subclass type, which requires a cast or a type
  check.
- If the field is needed by a future subclass, it must be pushed up
  again or duplicated, which is the cost of the push down.
- The subclass's constructor may gain a parameter for the field, which
  changes the subclass's construction interface.

## 11. Failure modes and misuse

**Pushing down a field used by multiple subclasses.** The field is used
by two of three subclasses, and pushing it down to one leaves the other
without it. The fix is an intermediate superclass, not a push down to one
subclass.

**Pushing down a field that is part of the contract.** The field is
accessed through the superclass type by consumers, and pushing it down
breaks the contract. The symptom is a compile error or a runtime error
in consumer code.

**Pushing down speculatively.** The field is pushed down because it
seems like only one subclass uses it, but a future subclass will need
it. The symptom is the field being pushed back up or duplicated when the
future subclass arrives.

## 12. Trade-off matrix

| Alternative | Dead weight | Ownership | When to prefer |
|---|---|---|---|
| Push Down Field | Eliminated | On subclass | Field only one subclass uses |
| Pull Up Field | None | On superclass | Field shared by all subclasses |
| Extract Subclass | None | New subclass | Superclass has subclass specific fields |
| Replace Inheritance with Delegation | None | Delegate | Hierarchy is wrong |

## 13. Related and incompatible patterns

**Pull Up Field** (same catalog) is the inverse. It moves a field from
subclasses to the superclass.

**Push Down Method** (same catalog) is the method version. It moves a
method from the superclass to a subclass.

**Extract Subclass** (same catalog) is the refactoring that creates the
subclass, which is the prerequisite if the subclass does not exist.

**Move Field** (same catalog) moves a field between unrelated classes,
not within an inheritance hierarchy.

## 14. Refactoring path in and out

**Path in.** Declare the field on the subclass, move initialisation,
remove from superclass, update callers.

**Path out.** Pull Up Field moves the field back to the superclass when
it turns out to be shared.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test that accessed the field should produce the same result, now through
the subclass.

## 16. Observability signals

The refactoring does not change behaviour, so the observable signal in
production is nothing.

## 17. Security and privacy implications

The refactoring improves privacy when the field contains sensitive data
that should not be on every subclass. Pushing it down limits access to
the subclass that uses it, which is a positive privacy signal.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 12, "Push Down Field."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 11, "Push Down Field."
- Oracle, "java.awt.Component,"
  [https://docs.oracle.com/en/java/javase/21/docs/api/java.desktop/java/awt/Component.html](https://docs.oracle.com/en/java/javase/21/docs/api/java.desktop/java/awt/Component.html),
  verified 2026-08-13.
- Python Software Foundation, "Built-in Exceptions,"
  [https://docs.python.org/3/library/exceptions.html](https://docs.python.org/3/library/exceptions.html),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
