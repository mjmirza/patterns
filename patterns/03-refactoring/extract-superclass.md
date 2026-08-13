---
name: Extract Superclass
slug: extract-superclass
family: 03-refactoring
category: Refactoring
aliases: [Extract Base Class, Pull Up Common, Extract Parent]
first_described: "Fowler 1999"
maturity: canonical
related: [extract-class, extract-subclass, collapse-hierarchy, pull-up-field, pull-up-method, replace-inheritance-with-delegation]
incompatible_with: []
verified: 2026-08-13
---

# Extract Superclass

## 1. Name, aliases, and lineage

The canonical name is **Extract Superclass**, introduced by Martin Fowler
in *Refactoring. Improving the Design of Existing Code*, 1st edition,
Addison-Wesley, 1999, chapter 11, "Dealing with Generalization." The
refactoring survived into the second edition, Martin Fowler, *Refactoring.
Improving the Design of Existing Code*, 2nd edition, Addison-Wesley, 2018,
chapter 12, "Simplification and Generalization," under the same name and
with the same mechanics. Fowler groups it with Extract Subclass, Pull Up
Field, Pull Up Method, and Collapse Hierarchy, because the five
refactorings move features within an inheritance hierarchy.

The underlying idea, that shared code should be pulled up into a common
parent rather than duplicated in each subclass, is one of the oldest uses
of inheritance in object oriented design. Grady Booch, in *Object-Oriented
Analysis and Design with Applications*, Benjamin Cummings, 1994, describes
inheritance as a mechanism for reusing structure and behaviour, and the
extraction of a superclass is the mechanical path from duplicated code to
shared inheritance.

The alias **Extract Base Class** is used in the C sharp community, where
the keyword `base` refers to the parent. The alias **Pull Up Common** is
used in the Eclipse community, where the related Pull Up refactoring family
performs the same operation as a set of menu items.

## 2. Problem and context

You have two classes that share fields and methods, either because they
were written independently and converged, or because they were originally
one class that was split and the shared code was duplicated. The
duplication is a maintenance burden: a change to the shared logic must be
made in both classes, and a bug fixed in one is not fixed in the other.
The classes are related, not coincidental: they represent different
specialisations of the same concept, and the shared code is the common
part of that concept.

The situation reads like this. A `Employee` class and a `Customer` class
both have `name`, `address`, and `phoneNumber` fields, and both have
`getName`, `setName`, `getAddress`, and `formatContact` methods. The code
is identical in both classes. A change to the phone formatting logic must
be made in both, and a bug in the address validation of one class is
absent in the other because someone forgot to copy the fix. The two
classes are both "people" in the domain, but the language has no `Person`
class to hold the shared code.

The fix is to extract a superclass. Create a `Person` class with the
shared fields and methods, and make `Employee` and `Customer` subclasses.
The shared code lives in one place, and a change or a fix is made once.

## 3. Forces

**Duplication versus hierarchy depth.** Duplicated code is a maintenance
burden. Extracting a superclass removes the duplication but adds a level
of hierarchy, which is navigation overhead. The force favours extraction
when the duplication cost exceeds the hierarchy cost, which happens when
the shared code is nontrivial and changes at the same rate in both
classes.

**Inheritance versus composition.** A superclass provides code reuse
through inheritance, which is tight coupling. Composition, where the
shared code lives in a separate object that both classes delegate to,
provides looser coupling. The force favours inheritance when the
relationship is genuinely a subtype relationship ("Employee is a Person")
and favours composition when the relationship is a "has a" relationship
("Employee has a contact record").

**Type hierarchy versus implementation reuse.** A superclass defines both
a type hierarchy and a code reuse mechanism. The type hierarchy is visible
to the type system and enables polymorphism. The implementation reuse is
visible to the developer and eliminates duplication. The force favours
extraction when both benefits are wanted, and favours composition when
only implementation reuse is wanted, because composition does not impose
a type hierarchy.

**Subclass control versus superclass rigidity.** A subclass inherits the
superclass's fields and methods, which is convenient but rigid: the
subclass cannot change the inherited behaviour without overriding it. The
force favours extraction when the inherited behaviour is stable and the
subclasses want it, and favours composition when the subclasses need to
control the behaviour independently.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- Two classes share fields and methods that are identical or nearly
  identical, and the shared code represents a common concept that both
  classes are specialisations of.
- The two classes have an is a relationship in the domain: an Employee is
  a Person, a SavingsAccount is an Account. The extraction formalises a
  relationship that already exists in the domain model.
- The shared code changes at the same rate in both classes, meaning a
  change to one should be a change to both, and the duplication is
  preventing that from happening.
- The shared code is nontrivial, meaning it is more than a few field
  definitions, and the duplication cost is real.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The two classes share code by coincidence, not by relationship. They
  happen to have the same fields but represent unrelated concepts.
  Extracting a superclass would communicate a relationship that does not
  exist, which is worse than the duplication.
- The relationship is "has a" not "is a." An Employee has an Address, it is
  not an Address. The fix is composition, not inheritance.
- The shared code is trivial, for example two field definitions. The
  hierarchy adds more structure than the duplication warrants.
- The language does not support implementation inheritance, for example
  Go, which has only structural typing and embedding. The extraction is
  done through embedding, which is composition, not inheritance.

## 5. Structure

The refactoring has two participants.

- **The subclasses.** The two or more classes that share code. After the
  refactoring, they inherit from the extracted superclass and the shared
  code is removed from each.
- **The superclass.** The new class that holds the shared fields and
  methods. After the refactoring, the subclasses inherit from it.

The invariant is that every caller of the subclasses continues to produce
the same results. Callers that accessed the shared fields and methods now
access them through inheritance.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER
  ------                              -----

  Employee                            Person  (new superclass)
    name                                name
    address                             address
    phoneNumber                         phoneNumber
    salary                              getName()
    getName()                           setName()
    setName()                         +-------+-------+
    formatContact()                   |               |
  Customer                          Employee        Customer
    name                               salary           discount
    address                            formatContact()  formatContact()
    phoneNumber
    discount
    getName()
    setName()
    formatContact()

  (shared code duplicated)           (shared code in Person)
```

## 7. Dynamics

```
  t0  identify shared fields and methods
       across two or more classes
       |
       v
  t1  create the superclass
       |
       v
  t2  pull up shared fields (Pull Up Field)
       |
       v
  t3  pull up shared methods (Pull Up Method)
       |
       v
  t4  make the original classes
       subclasses of the new superclass
       |
       v
  t5  remove the duplicated code
       from the subclasses
       |
       v
  t6  run test suite
       |
       v
  t7  commit. the superclass is extracted.
```

## 8. Implementation variants

**Single inheritance extraction.** The canonical variant in languages with
single inheritance, such as Java, Python, and C sharp. The shared code is
pulled up into one superclass, and the subclasses inherit from it.

**Interface extraction.** When the shared code is small or when the
language does not support implementation inheritance, only the interface
is extracted. The subclasses implement the interface, and the shared
implementation is provided by a helper or a mixin. This variant is used
when the type hierarchy is wanted but the implementation coupling is not.

**Mixin extraction.** In languages that support mixins, such as Python's
multiple inheritance or Ruby's modules, the shared code is extracted as a
mixin that is included in both classes. This variant provides code reuse
without imposing a single inheritance hierarchy.

**Abstract superclass.** The extracted superclass is abstract, meaning it
cannot be instantiated directly. This variant is used when the superclass
represents a concept that is always specialised, for example Person is
always either an Employee or a Customer, never a bare Person.

```python
# Python: before (duplicated code)

class Employee:
    def __init__(self, name: str, salary: int):
        self.name = name
        self.salary = salary

    def get_name(self) -> str:
        return self.name

class Customer:
    def __init__(self, name: str, discount: float):
        self.name = name
        self.discount = discount

    def get_name(self) -> str:
        return self.name

# Python: after (extracted superclass)

class Person:
    def __init__(self, name: str):
        self.name = name

    def get_name(self) -> str:
        return self.name

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
// TypeScript: after (extracted superclass)

class Person {
    constructor(protected name: string) {}

    getName(): string {
        return this.name;
    }
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
// Java: after (abstract superclass)

public abstract class Person {
    private String name;

    protected Person(String name) {
        this.name = name;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }
}

public class Employee extends Person {
    private int salary;

    public Employee(String name, int salary) {
        super(name);
        this.salary = salary;
    }
}

public class Customer extends Person {
    private double discount;

    public Customer(String name, double discount) {
        super(name);
        this.discount = discount;
    }
}
```

## 9. Known production uses

**Java's `AbstractList` class** is an example of an extracted superclass
in the standard library. `AbstractList` provides default implementations
of list operations that work in terms of `get` and `size`, which
subclasses must implement. The Java documentation states that
`AbstractList` is a skeletal implementation that minimises the effort
to implement the `List` interface
([java.util.AbstractList documentation](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/AbstractList.html),
verified 2026-08-13). `ArrayList` and `LinkedList` inherit from it and
share the common list behaviour.

**Python's `collections.abc.Sequence`** is the Python equivalent. It is
an abstract base class that provides default method implementations for
sequences, so that subclasses only need to implement `__getitem__` and
`__len__`. The Python documentation states that the ABC provides mixin
methods for the full sequence interface
([collections.abc documentation](https://docs.python.org/3/library/collections.abc.html),
verified 2026-08-13).

## 10. Consequences

Positive.

- Duplicated code is eliminated, which reduces the maintenance burden and
  the risk of a bug being fixed in one class but not the other.
- The type hierarchy enables polymorphism: a caller can treat an
  Employee and a Customer as Persons, which is useful when the caller
  only needs the shared behaviour.
- The shared code lives in one place, where it can be understood, tested,
  and modified independently of the subclasses.
- New subclasses can be added that inherit the shared code, which is
  faster than implementing it from scratch.

Negative.

- The inheritance hierarchy is one level deeper, which adds navigation
  overhead for a reader.
- The subclasses are coupled to the superclass: a change to the
  superclass affects every subclass, which may be a large blast radius.
- The inheritance imposes a type hierarchy that may be too rigid: a
  subclass cannot change the inherited behaviour without overriding it,
  and the override may conflict with future superclass changes.
- The refactoring can be over applied, extracting a superclass for code
  that is only coincidentally shared, which communicates a false type
  relationship.

## 11. Failure modes and misuse

**Extracting a superclass for unrelated classes.** Two classes happen to
have the same fields, but they represent unrelated concepts. The
extraction communicates an is a relationship that does not exist, and a
future reader who sees Employee extends Person and Customer extends Person
may reason incorrectly about the domain model. The fix is composition,
not inheritance.

**Gorilla banana problem.** The superclass provides a large set of methods,
and a subclass that only needs one of them inherits all of them. The
subclass has methods it does not want and cannot remove, which is the
"you wanted a banana but you got a gorilla holding the banana" problem.
The fix is composition with a smaller interface.

**Deep hierarchy.** The extraction adds a level, and subsequent
extractions add more levels, producing a hierarchy five levels deep that
a reader must traverse to understand a single class. The symptom is a
class whose definition is `class X extends Y` and whose real
implementation is spread across five files.

**Fragile base class.** A change to the superclass breaks a subclass in a
way the superclass author did not anticipate, because the subclass relied
on an implementation detail of the superclass that changed. The symptom is
a test failure in a subclass after a change to the superclass, which is
the classic fragile base class problem.

## 12. Trade-off matrix

| Alternative | Duplication | Coupling | Hierarchy depth | When to prefer |
|---|---|---|---|---|
| Extract Superclass | Eliminated | Inheritance (tight) | +1 | Is a relationship, shared code |
| Extract Class (composition) | Eliminated | Delegation (loose) | 0 | Has a relationship, code reuse |
| Mixin | Eliminated | Include (medium) | 0 | Language supports mixins |
| Collapse Hierarchy | Eliminated | None | -1 | A hierarchy level is empty |
| Keep duplicated | None | None | 0 | Code is trivial, classes are unrelated |

## 13. Related and incompatible patterns

**Extract Subclass** (same catalog) is the opposite direction. It adds a
subclass to specialise an existing class, where Extract Superclass adds a
superclass to generalise existing classes. The two are the two directions
of hierarchy manipulation.

**Collapse Hierarchy** (same catalog) removes an empty hierarchy level.
It is the inverse of Extract Superclass when the extracted superclass
turns out to be unnecessary.

**Pull Up Field** and **Pull Up Method** (same catalog) are the
mechanical steps Extract Superclass uses to move shared members from the
subclasses to the superclass.

**Replace Inheritance with Delegation** (same catalog) is the refactoring
that reverses Extract Superclass when the inheritance turns out to be the
wrong model and composition is better.

## 14. Refactoring path in and out

**Path in.** The refactoring is introduced by creating a superclass and
moving shared members into it. The steps are:

1. Identify the shared fields and methods across two or more classes.
2. Create a new class (the superclass).
3. Move the shared fields to the superclass (Pull Up Field).
4. Move the shared methods to the superclass (Pull Up Method).
5. Make the original classes subclasses of the new superclass.
6. Remove the duplicated code from the subclasses.
7. Run the test suite. Any failure means a member was not moved correctly
   or a subclass no longer compiles.

**Path out.** The refactoring is reversed by Collapse Hierarchy (if the
superclass is empty) or by Replace Inheritance with Delegation (if the
inheritance is the wrong model). The reverse is applied when the
superclass is not earning its place or when the is a relationship was
wrong.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test that exercised the subclasses should produce the same result, now
through the inherited members. A test failure means a member was not
moved correctly or a subclass lost a field.

New tests should test the superclass in isolation, verifying its fields
and methods produce the expected results without the subclasses. These
tests verify the shared behaviour independently.

A polymorphism test should verify that a caller that treats the
subclasses as instances of the superclass gets the correct behaviour,
which verifies the type hierarchy.

## 16. Observability signals

The refactoring does not change behaviour, so the observable signal in
production is nothing. The one observable difference is in the class
names that appear in traces: the superclass name may appear in stack
traces where the subclass name used to appear, because the method now
lives on the superclass. This is expected and is not a regression.

## 17. Security and privacy implications

The refactoring does not change what data is stored or how it is
accessed, so it does not change the security surface. The security
relevant case is when the superclass provides a method that should be
restricted in one subclass but not the other, for example a method that
returns sensitive data. The subclass can override the method to restrict
access, but the superclass method is still visible and could be called
through the superclass type, which is a security consideration that did
not exist before the extraction.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 12, "Extract Superclass."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 11, "Extract Superclass."
- Grady Booch, *Object-Oriented Analysis and Design with Applications*,
  Benjamin Cummings, 2nd edition, 1994.
- Oracle, "java.util.AbstractList," Java SE 21 API documentation,
  [https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/AbstractList.html](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/AbstractList.html),
  verified 2026-08-13.
- Python Software Foundation, "collections.abc,"
  [https://docs.python.org/3/library/collections.abc.html](https://docs.python.org/3/library/collections.abc.html),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
