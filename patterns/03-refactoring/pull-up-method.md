---
name: Pull Up Method
slug: pull-up-method
family: 03-refactoring
category: Refactoring
aliases: [Pull Up Function, Move Method to Superclass]
first_described: "Fowler 1999"
maturity: canonical
related: [pull-up-field, pull-up-constructor-body, extract-superclass, collapse-hierarchy, push-down-method, move-function]
incompatible_with: []
verified: 2026-08-13
---

# Pull Up Method

## 1. Name, aliases, and lineage

The canonical name is **Pull Up Method**, introduced by Martin Fowler in
*Refactoring. Improving the Design of Existing Code*, 1st edition,
Addison-Wesley, 1999, chapter 11, "Dealing with Generalization." The
refactoring survived into the second edition, Martin Fowler, *Refactoring.
Improving the Design of Existing Code*, 2nd edition, Addison-Wesley, 2018,
chapter 12, "Simplification and Generalization," under the same name.
Fowler groups it with Pull Up Field, Pull Up Constructor Body, and Push
Down Method, because the four refactorings move features within an
inheritance hierarchy.

The underlying idea, that a method shared by multiple subclasses should
be on the superclass, is the method level equivalent of Pull Up Field.
Grady Booch, in *Object-Oriented Analysis and Design with Applications*,
Benjamin Cummings, 1994, describes inheritance as sharing both structure
(fields) and behaviour (methods), and Pull Up Method is the mechanical
path for the behavioural side.

## 2. Problem and context

Two or more subclasses have the same method, with the same body and the
same signature. The method was written on each subclass independently,
and the duplication means a change to the logic must be made in every
subclass. The method should be on the superclass, because the behaviour
is part of the shared concept.

The situation reads like this. `Employee` and `Customer` both extend
`Person`, and both have a `getName` method that returns `self.name`. The
method is identical in both subclasses, and a change to the formatting
must be made in both. The method should be on `Person`, where the `name`
field lives.

The fix is to pull up the method. Move `getName` to `Person`, and remove
it from both subclasses. Both subclasses inherit the method, and a change
is made in one place.

## 3. Forces

**Duplication versus hierarchy.** Duplicated methods are a maintenance
burden. Pulling up removes the duplication but adds the method to the
superclass, which affects every subclass. The force favours pulling up
when the method is shared by all or most subclasses.

**Polymorphism versus static sharing.** A pulled up method is shared
statically: every subclass calls the same code. A method left on
subclasses can be overridden independently, which is polymorphic. The
force favours pulling up when the behaviour is the same for every
subclass and should not be overridden.

**Body similarity versus signature similarity.** Two methods may have the
same signature but different bodies. Pulling them up requires unifying
the bodies, which may require Extract Function or template method. The
force favours pulling up when the bodies are identical, and favours
template method when the bodies share structure but differ in details.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- Two or more subclasses have the same method, with the same body and the
  same signature.
- The method's behaviour is part of the shared concept, not a subclass
  specialisation.
- The method does not need to be overridden by subclasses, or if it does,
  the default on the superclass is the correct default.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The methods have the same signature but different bodies. The methods
  are not the same, they are polymorphic variants. The fix is
  Replace Conditional with Polymorphism, not Pull Up Method.
- The method is only on some subclasses, not all. Pulling it up gives
  every subclass the method, which is wrong for subclasses that do not
  need it.
- The method uses a subclass specific field that is not on the
  superclass. Pulling up the method requires pulling up the field first,
  or passing the field as a parameter.

## 5. Structure

The refactoring has one participant: the method that is moved from the
subclasses to the superclass.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER
  ------                              -----

  class Person:                      class Person:
    name                                name
                                       getName(): return name
  class Employee(Person):
    getName(): return self.name       class Employee(Person):
                                       salary
  class Customer(Person):            class Customer(Person):
    getName(): return self.name        discount
                                     (getName inherited)
  (getName duplicated)               (getName on Person)
```

## 7. Dynamics

```
  t0  identify identical methods on subclasses
       |
       v
  t1  verify the methods are truly identical
       (same body, same signature, same behaviour)
       |
       v
  t2  move the method to the superclass
       |
       v
  t3  remove the method from each subclass
       |
       v
  t4  run test suite
       |
       v
  t5  commit. the method is pulled up.
```

## 8. Implementation variants

**Direct pull up.** The canonical variant. The method is moved verbatim
to the superclass, and the copies are removed from the subclasses.

**Pull up with template method.** The methods share structure but differ
in a detail. The shared structure is pulled up as a template method, and
the differing detail becomes an abstract hook method that each subclass
overrides. This variant combines Pull Up Method with the Template Method
pattern.

**Pull up with parameter.** The methods differ in a constant value. The
method is pulled up with the constant as a parameter, which is
Parameterize Function applied at the superclass level.

```python
# Python: before (getName duplicated)

class Person:
    def __init__(self, name: str):
        self.name = name

class Employee(Person):
    def get_name(self) -> str:
        return self.name.upper()

class Customer(Person):
    def get_name(self) -> str:
        return self.name.upper()

# Python: after (pulled up)

class Person:
    def __init__(self, name: str):
        self.name = name

    def get_name(self) -> str:
        return self.name.upper()

class Employee(Person):
    pass  # get_name inherited

class Customer(Person):
    pass  # get_name inherited
```

```typescript
// TypeScript: after (pulled up)

class Person {
    constructor(protected name: string) {}

    getName(): string {
        return this.name.toUpperCase();
    }
}

class Employee extends Person {}
class Customer extends Person {}
```

```java
// Java: after (pulled up)

public class Person {
    private final String name;

    public Person(String name) { this.name = name; }

    public String getName() {
        return name.toUpperCase();
    }
}

class Employee extends Person {
    public Employee(String name, int salary) {
        super(name);
    }
}

class Customer extends Person {
    public Customer(String name, double discount) {
        super(name);
    }
}
```

## 9. Known production uses

**Java's `AbstractList` class** provides the `indexOf`, `contains`, and
`clear` methods that were pulled up from `ArrayList` and `LinkedList`.
The Java documentation states that `AbstractList` provides a skeletal
implementation of the `List` interface, which includes shared methods
that every list implementation inherits
([java.util.AbstractList](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/AbstractList.html),
verified 2026-08-13).

**Python's `collections.abc.Iterable`** provides the `__iter__` based
methods that were pulled up from concrete collection classes to the
abstract base class. The Python documentation states that the ABCs
provide mixin methods that work in terms of the abstract methods
([collections.abc documentation](https://docs.python.org/3/library/collections.abc.html),
verified 2026-08-13).

## 10. Consequences

Positive.

- The method is in one place, which eliminates the duplication.
- Every subclass inherits the method, which means a new subclass gets it
  for free.
- A change to the method is made in one place, which is the maintenance
  benefit.

Negative.

- Every subclass gets the method, including subclasses that do not need
  it, if the method was not truly universal.
- The method cannot be overridden without overriding, which is a
  constraint on subclasses that need different behaviour.
- The superclass's interface grows, which may make it harder to
  understand.

## 11. Failure modes and misuse

**Pulling up a method that is not identical.** The methods have the same
signature but different bodies, and pulling up unifies them incorrectly.
The symptom is a subclass whose behaviour changed because it inherited
the wrong method.

**Pulling up a method that uses subclass specific fields.** The method
on the subclass uses a field that is only on that subclass, and pulling
up the method requires pulling up the field, which may give other
subclasses a field they do not need.

**Pulling up a method that should be polymorphic.** The method should be
overridden by each subclass, and pulling up provides a default that
subclasses accidentally inherit instead of overriding. The symptom is a
subclass that inherits the default when it should have its own
implementation.

## 12. Trade-off matrix

| Alternative | Duplication | Polymorphism | When to prefer |
|---|---|---|---|
| Pull Up Method | Eliminated | Inherited default | Same method on all subclasses |
| Push Down Method | Eliminated | Per subclass | Method on superclass, only one subclass uses it |
| Template Method | Partial | Hook for variation | Shared structure, varying detail |
| Replace Conditional with Polymorphism | Eliminated | Full | Conditional dispatches on type |

## 13. Related and incompatible patterns

**Pull Up Field** (same catalog) is the field version. The two are
frequently applied together: pull up the field, then pull up the methods
that use it.

**Pull Up Constructor Body** (same catalog) is the constructor specific
version, which has additional mechanics for super calls and final fields.

**Push Down Method** (same catalog) is the inverse. It moves a method
from the superclass to a subclass when the method is only used by one
subclass.

**Extract Superclass** (same catalog) creates the superclass, which is
the prerequisite if it does not exist.

## 14. Refactoring path in and out

**Path in.** Move the method to the superclass, remove it from the
subclasses, run tests.

**Path out.** Push Down Method moves the method back to the subclasses
when the method turns out to not be universal.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test that called the method should produce the same result, now through
inheritance.

## 16. Observability signals

The refactoring does not change behaviour, so the observable signal in
production is nothing.

## 17. Security and privacy implications

The refactoring does not change what data is processed, so it does not
change the security surface.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 12, "Pull Up Method."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 11, "Pull Up Method."
- Grady Booch, *Object-Oriented Analysis and Design with Applications*,
  Benjamin Cummings, 2nd edition, 1994.
- Oracle, "java.util.AbstractList,"
  [https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/AbstractList.html](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/AbstractList.html),
  verified 2026-08-13.
- Python Software Foundation, "collections.abc,"
  [https://docs.python.org/3/library/collections.abc.html](https://docs.python.org/3/library/collections.abc.html),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
