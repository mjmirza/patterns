---
name: Pull Up Field
slug: pull-up-field
family: 03-refactoring
category: Refactoring
aliases: [Pull Up Attribute, Move Field to Superclass]
first_described: "Fowler 1999"
maturity: canonical
related: [pull-up-method, pull-up-constructor-body, extract-superclass, collapse-hierarchy, move-field, push-down-field]
incompatible_with: []
verified: 2026-08-13
---

# Pull Up Field

## 1. Name, aliases, and lineage

The canonical name is **Pull Up Field**, introduced by Martin Fowler in
*Refactoring. Improving the Design of Existing Code*, 1st edition,
Addison-Wesley, 1999, chapter 11, "Dealing with Generalization." The
refactoring survived into the second edition, Martin Fowler, *Refactoring.
Improving the Design of Existing Code*, 2nd edition, Addison-Wesley, 2018,
chapter 12, "Simplification and Generalization," under the same name.
Fowler groups it with Pull Up Method, Pull Up Constructor Body, and
Push Down Field, because the four refactorings move features within an
inheritance hierarchy.

The underlying idea, that a field shared by multiple subclasses should be
on the superclass, is one of the oldest uses of inheritance. Grady Booch,
in *Object-Oriented Analysis and Design with Applications*, Benjamin
Cummings, 1994, describes inheritance as a mechanism for sharing
structure, and the pull up of a field is the mechanical path from
duplicated structure to shared inheritance.

## 2. Problem and context

Two or more subclasses have the same field, with the same type and the
same meaning. The field was declared on each subclass independently, and
the duplication means a change to the field's type, name, or
initialisation must be made in every subclass. The field should be on the
superclass, because the field is part of the shared concept that the
superclass represents.

The situation reads like this. `Employee` and `Customer` both extend
`Person`, and both have a `name` field. The field was declared on each
subclass because the subclasses were written before the `Person`
superclass was extracted. The field is the same, with the same type and
the same meaning, but it is duplicated, and a change to the name field's
type must be made in both subclasses.

The fix is to pull up the field. Declare `name` on `Person`, and remove
it from `Employee` and `Customer`. Both subclasses inherit the field, and
a change to it is made in one place.

## 3. Forces

**Duplication versus hierarchy.** Duplicated fields on subclasses are a
maintenance burden. Pulling up removes the duplication but adds the
field to the superclass, which affects every subclass, including those
that do not use the field. The force favours pulling up when the field is
shared by all subclasses.

**Type sharing versus subclass specificity.** A field on the superclass
is shared by every subclass, which is correct when every subclass uses
the field. If only some subclasses use the field, pulling it up gives the
other subclasses a field they do not need. The force favours pulling up
when the field is universal.

**Initialisation sharing versus flexibility.** A field on the
superclass can be initialised by the superclass constructor, which shares
the initialisation. A field on the subclass is initialised by the
subclass constructor, which is flexible but duplicates the logic. The
force favours pulling up when the initialisation is shared.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- Two or more subclasses have the same field, with the same type and the
  same meaning.
- The field is part of the shared concept that the superclass represents.
- Every subclass that extends the superclass uses the field, so pulling
  it up does not give any subclass a field it does not need.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The field is only on some subclasses, not all. Pulling it up gives
  every subclass the field, which is wrong for subclasses that do not
  use it. The field should stay on the subclasses, or be on an
  intermediate superclass.
- The fields have the same name and type but different meanings. They are
  not the same field, just coincidentally named the same.
- The field is a final field declared on the subclass, and the language
  requires final fields to be initialised in the declaring constructor,
  which prevents the pull up without also pulling up the constructor.

## 5. Structure

The refactoring has one participant: the field that is moved from the
subclasses to the superclass.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER
  ------                              -----

  class Person:                      class Person:
    (no fields)                        name  (pulled up)

  class Employee(Person):            class Employee(Person):
    name                               salary
    salary                           (name inherited)

  class Customer(Person):            class Customer(Person):
    name                               discount
    discount                         (name inherited)

  (name duplicated)                  (name on Person)
```

## 7. Dynamics

```
  t0  identify field on multiple subclasses
       |
       v
  t1  verify the field is the same
       (same type, same meaning)
       |
       v
  t2  declare the field on the superclass
       |
       v
  t3  remove the field from each subclass
       |
       v
  t4  update accessors if needed
       |
       v
  t5  run test suite
       |
       v
  t6  commit. the field is pulled up.
```

## 8. Implementation variants

**Pull up field with accessor.** The canonical variant. The field is
moved to the superclass, and accessors are provided on the superclass.

**Pull up field with constructor.** The field is pulled up, and the
superclass constructor initialises it, which is Pull Up Constructor Body.

**Pull up field with default.** The field is pulled up with a default
value, and subclasses that do not override the default get it for free.

```python
# Python: before (name duplicated)

class Person:
    pass

class Employee(Person):
    def __init__(self, name: str, salary: int):
        self.name = name
        self.salary = salary

class Customer(Person):
    def __init__(self, name: str, discount: float):
        self.name = name
        self.discount = discount

# Python: after (name pulled up)

class Person:
    def __init__(self, name: str):
        self.name = name

class Employee(Person):
    def __init__(self, name: str, salary: int):
        super().__init__(name)
        self.salary = salary

class Customer(Person):
    def __init__(self, name: str, discount: float):
        super().__init__(name)
        self.discount = discount
```

```typescript
// TypeScript: after (name pulled up)

class Person {
    constructor(public name: string) {}
}

class Employee extends Person {
    constructor(name: string, public salary: number) {
        super(name);
    }
}

class Customer extends Person {
    constructor(name: string, public discount: number) {
        super(name);
    }
}
```

```java
// Java: after (name pulled up)

public class Person {
    private final String name;

    public Person(String name) {
        this.name = name;
    }

    public String getName() { return name; }
}

public class Employee extends Person {
    private final int salary;

    public Employee(String name, int salary) {
        super(name);
        this.salary = salary;
    }
}

public class Customer extends Person {
    private final double discount;

    public Customer(String name, double discount) {
        super(name);
        this.discount = discount;
    }
}
```

## 9. Known production uses

**Java's `AbstractList` class** holds the `modCount` field that tracks
structural modifications, which was pulled up from `ArrayList` and
`LinkedList` to the abstract base class
([java.util.AbstractList](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/AbstractList.html),
verified 2026-08-13). Every list implementation that extends
`AbstractList` inherits the field and the fail fast iteration semantics
it provides.

**Python's `Exception` base class** holds the `args` field that every
exception subclass inherits, which was pulled up from individual
exception classes to the base class to share the storage of exception
arguments
([Python Exception documentation](https://docs.python.org/3/library/exceptions.html),
verified 2026-08-13).

## 10. Consequences

Positive.

- The field is in one place, which eliminates the duplication.
- Every subclass inherits the field, which means a new subclass gets it
  for free.
- The field can be initialised by the superclass constructor, which
  shares the initialisation.

Negative.

- Every subclass gets the field, including subclasses that do not use
  it, if the field was not truly universal.
- The superclass's interface grows, which may make it harder to
  understand for a reader who expects the superclass to be minimal.

## 11. Failure modes and misuse

**Pulling up a field that is not universal.** The field is only on some
subclasses, and pulling it up gives every subclass the field. The symptom
is a subclass with a field it does not use.

**Pulling up a field with a different meaning.** The fields have the same
name and type but represent different concepts. Pulling them up
communicates a shared concept that does not exist.

**Pulling up a final field without pulling up the constructor.** The
final field is declared on the subclass and initialised in the subclass
constructor. Pulling up the field without pulling up the constructor
produces a final field that cannot be initialised, which is a compile
error.

## 12. Trade-off matrix

| Alternative | Duplication | Hierarchy | When to prefer |
|---|---|---|---|
| Pull Up Field | Eliminated | Field on superclass | Field on all subclasses |
| Push Down Field | Eliminated | Field on subclass | Field on superclass, only one subclass uses it |
| Extract Superclass | Eliminated | New superclass | No superclass exists |
| Keep duplicated | Present | None | Fields have different meanings |

## 13. Related and incompatible patterns

**Pull Up Method** (same catalog) moves a method to the superclass, which
is the method version of the same operation.

**Pull Up Constructor Body** (same catalog) moves the constructor body,
which is required when the pulled up field needs to be initialised by the
superclass constructor.

**Push Down Field** (same catalog) is the inverse. It moves a field from
the superclass to the subclass when the field is only used by one
subclass.

**Move Field** (same catalog) moves a field between unrelated classes,
not within an inheritance hierarchy.

## 14. Refactoring path in and out

**Path in.** Declare the field on the superclass, remove it from the
subclasses, update accessors and constructors.

**Path out.** Push Down Field moves the field back to the subclasses when
the field turns out to not be universal.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test that accessed the field should produce the same result, now through
inheritance.

## 16. Observability signals

The refactoring does not change behaviour, so the observable signal in
production is nothing.

## 17. Security and privacy implications

The refactoring does not change what data is stored, so it does not
change the security surface. The field is now on the superclass, which
may make it visible to subclasses that did not previously have access to
it, which is a minor security consideration.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 12, "Pull Up Field."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 11, "Pull Up Field."
- Grady Booch, *Object-Oriented Analysis and Design with Applications*,
  Benjamin Cummings, 2nd edition, 1994.
- Oracle, "java.util.AbstractList,"
  [https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/AbstractList.html](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/AbstractList.html),
  verified 2026-08-13.
- Python Software Foundation, "Built-in Exceptions,"
  [https://docs.python.org/3/library/exceptions.html](https://docs.python.org/3/library/exceptions.html),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
