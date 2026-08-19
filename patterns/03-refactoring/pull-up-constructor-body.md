---
name: Pull Up Constructor Body
slug: pull-up-constructor-body
family: 03-refactoring
category: Refactoring
aliases: [Extract Superclass Constructor, Pull Up Constructor]
first_described: "Fowler 2018"
maturity: canonical
related: [pull-up-field, pull-up-method, extract-superclass, collapse-hierarchy, replace-inheritance-with-delegation]
incompatible_with: []
verified: 2026-08-13
---

# Pull Up Constructor Body

## 1. Name, aliases, and lineage

The canonical name is **Pull Up Constructor Body**, introduced by Martin
Fowler in *Refactoring. Improving the Design of Existing Code*, 2nd
edition, Addison-Wesley, 2018, chapter 12, "Simplification and
Generalization." The refactoring is new to the second edition. It does
not appear as a separate entry in the first edition (1999), where the
broader Pull Up Method covered the case of constructors. Fowler split it
out in the second edition because constructors have specific mechanics:
they call `super()`, they set final fields, and they have ordering
constraints that ordinary methods do not.

The underlying idea, that shared initialisation logic in subclass
constructors should be moved to the superclass constructor, is a specific
application of Pull Up Method to constructors. The mechanics differ
because constructors must chain to the superclass constructor, and
because final fields can only be set in the constructor that declares
them.

## 2. Problem and context

Two or more subclasses have constructors that share the same
initialisation logic. The constructors set the same fields in the same
order, with the same validation, and the only difference is the subclass
specific fields that follow. The shared initialisation is duplicated in
every subclass, and a change to the shared logic must be made in every
constructor.

The situation reads like this. `Employee` and `Customer` both extend
`Person`. Both constructors take a `name` and set `self.name = name`
with the same validation. The `Employee` constructor also takes a
`salary` and the `Customer` constructor takes a `discount`. The `name`
initialisation is duplicated, and a change to the name validation must
be made in both constructors.

The fix is to pull up the constructor body. Create a `Person`
constructor that takes `name` and validates it, and have each subclass
constructor call `super(name)` before setting its own fields.

## 3. Forces

**Duplication versus constructor complexity.** The duplicated
initialisation is a maintenance burden. Pulling it up removes the
duplication but makes the superclass constructor more complex, because
it now handles the shared logic. The force favours pulling up when the
duplication cost exceeds the complexity cost.

**Final fields versus flexibility.** In languages with final fields
(Java, Kotlin, Swift), a field can only be set in the constructor that
declares it. Pulling up the field declaration and the field's
initialisation to the superclass is required to pull up the constructor
body that sets it. The force favours pulling up when the field is
shared, and prevents it when the field is subclass specific.

**Ordering constraints versus simplicity.** Constructors have ordering
constraints: the superclass constructor must be called before the
subclass body, and final fields must be set before they are read. Pulling
up the constructor body must respect these constraints, which can make
the mechanics more complex than pulling up a regular method.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- Two or more subclass constructors share the same initialisation logic,
  setting the same fields with the same validation.
- The shared fields are on the superclass, and the subclass constructors
  are setting them directly because the superclass constructor does not.
- A change to the shared logic must be made in every subclass, which is
  a maintenance burden.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The subclass constructors do not share initialisation logic. Each
  constructor is different, and pulling up would merge unrelated logic.
- The shared fields are not on the superclass, and pulling them up would
  require Extract Superclass first.
- The language does not support constructor chaining, which makes the
  pull up impossible without changing the constructor contract.
- The subclass constructors have different ordering constraints that
  cannot be unified in the superclass constructor.

## 5. Structure

The refactoring has one participant: the shared constructor body that is
moved from the subclass constructors to the superclass constructor.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER
  ------                              -----

  class Person:                      class Person:
    name                               name
                                      def __init__(name):
  class Employee(Person):                validate(name)
    def __init__(name, salary):          self.name = name
      validate(name)
      self.name = name              class Employee(Person):
      self.salary = salary            def __init__(name, salary):
                                        super().__init__(name)
  class Customer(Person):              self.salary = salary
    def __init__(name, discount):
      validate(name)                class Customer(Person):
      self.name = name                def __init__(name, discount):
      self.discount = discount          super().__init__(name)
                                        self.discount = discount
  (validate and name duplicated)
```

## 7. Dynamics

```
  t0  identify shared constructor body
       across subclass constructors
       |
       v
  t1  pull up the shared fields to
       the superclass (Pull Up Field)
       |
       v
  t2  create a superclass constructor
       that takes the shared params
       and performs the shared logic
       |
       v
  t3  make subclass constructors call
       super() with the shared params
       |
       v
  t4  remove the shared logic from
       the subclass constructors
       |
       v
  t5  run test suite
       |
       v
  t6  commit. constructor body is pulled up.
```

## 8. Implementation variants

**Pull up with super call.** The canonical variant. The superclass
constructor takes the shared parameters, and the subclass constructors
call `super()` before setting their own fields.

**Pull up with factory.** Instead of a constructor, a factory method on
the superclass creates the instance and performs the shared
initialisation. This variant is used when the constructor is private or
when construction needs to return different subclasses based on input.

**Pull up with template method.** The superclass constructor calls a
hook method that subclasses override to set their specific fields. This
variant is used when the subclass initialisation needs to be ordered
after the superclass initialisation.

```python
# Python: before (duplicated validation)

class Person:
    pass

class Employee(Person):
    def __init__(self, name: str, salary: int):
        if not name.strip():
            raise ValueError("name required")
        self.name = name
        self.salary = salary

class Customer(Person):
    def __init__(self, name: str, discount: float):
        if not name.strip():
            raise ValueError("name required")
        self.name = name
        self.discount = discount

# Python: after (pulled up)

class Person:
    def __init__(self, name: str):
        if not name.strip():
            raise ValueError("name required")
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
// TypeScript: after (pulled up)

class Person {
    constructor(public name: string) {
        if (!name.trim()) throw new Error("name required");
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
// Java: after (pulled up)

public class Person {
    private final String name;

    public Person(String name) {
        if (name == null || name.trim().isEmpty()) {
            throw new IllegalArgumentException("name required");
        }
        this.name = name;
    }

    public String getName() { return name; }
}

class Employee extends Person {
    private final int salary;

    public Employee(String name, int salary) {
        super(name);
        this.salary = salary;
    }
}

class Customer extends Person {
    private final double discount;

    public Customer(String name, double discount) {
        super(name);
        this.discount = discount;
    }
}
```

## 9. Known production uses

**Java's `AbstractList` and `AbstractCollection`** provide constructors
that subclasses call to initialise shared state. The JDK source shows
that `ArrayList` calls `super()` on `AbstractList`, which initialises
the `modCount` field that tracks structural modifications
([java.util.AbstractList](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/AbstractList.html),
verified 2026-08-13). This is the pull up constructor body variant
applied to the standard library.

**Python's `super().__init__()` convention** is the language level
mechanism for constructor chaining. The Python documentation states that
`super()` returns a proxy object that delegates method calls to the
parent class, and it is the standard way to call the superclass
constructor
([Python super documentation](https://docs.python.org/3/library/functions.html#super),
verified 2026-08-13).

## 10. Consequences

Positive.

- The shared initialisation is in one place, which eliminates the
  duplication and the risk of a change being made in one constructor but
  not the others.
- The superclass constructor enforces the shared invariants, which means
  every subclass instance has the shared fields correctly initialised.
- A new subclass inherits the shared initialisation without rewriting it.

Negative.

- The subclass constructors must call `super()`, which is a constraint
  that a subclass author must remember.
- The superclass constructor's parameter list may grow as more shared
  fields are pulled up, which can produce a long parameter list.
- Final fields that are subclass specific cannot be pulled up, which
  limits the refactoring when the shared logic sets a final field that
  is declared on the subclass.

## 11. Failure modes and misuse

**Pulling up subclass specific fields.** The field is only used by one
subclass, and pulling it up to the superclass forces every subclass to
have the field, even those that do not use it.

**Pulling up with wrong super call order.** The subclass constructor
calls `super()` after setting its own fields, which means the shared
fields are not initialised when the subclass fields are set. The symptom
is a null pointer or an uninitialised field error.

**Pulling up too much.** The superclass constructor becomes a god
constructor that takes every parameter every subclass needs, and the
parameter list is unmanageable.

## 12. Trade-off matrix

| Alternative | Duplication | Complexity | When to prefer |
|---|---|---|---|
| Pull Up Constructor Body | Eliminated | Superclass constructor grows | Shared init across subclasses |
| Pull Up Method | Eliminated | Superclass grows | Shared method, not constructor |
| Extract Superclass | Eliminated | New class | No superclass exists yet |
| Keep duplicated | Present | None | Subclasses have different init |

## 13. Related and incompatible patterns

**Pull Up Field** (same catalog) moves a field to the superclass, which
is the prerequisite for pulling up the constructor body that sets it.

**Pull Up Method** (same catalog) is the general version for non
constructor methods. The constructor version has specific mechanics
because of super calls and final fields.

**Extract Superclass** (same catalog) creates the superclass, which is
the prerequisite if it does not yet exist.

## 14. Refactoring path in and out

**Path in.** Pull up the shared fields, create a superclass constructor,
make subclasses call super, remove the shared logic from subclasses.

**Path out.** Move the shared logic back to the subclass constructors,
which is rarely applied.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test that constructs a subclass should produce the same result, with the
shared fields correctly initialised.

A new test should verify that the superclass constructor rejects invalid
shared input, which confirms the validation is pulled up.

## 16. Observability signals

The refactoring does not change behaviour, so the observable signal in
production is nothing.

## 17. Security and privacy implications

The refactoring does not change what data is stored, so it does not
change the security surface. The security relevant case is when the
shared constructor performs a security check, for example validating
that a name does not contain script tags, and pulling it up makes the
check apply to every subclass, which is a positive security signal.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 12, "Pull Up Constructor Body."
- Oracle, "java.util.AbstractList,"
  [https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/AbstractList.html](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/AbstractList.html),
  verified 2026-08-13.
- Python Software Foundation, "super,"
  [https://docs.python.org/3/library/functions.html#super](https://docs.python.org/3/library/functions.html#super),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
