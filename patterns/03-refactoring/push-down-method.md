---
name: Push Down Method
slug: push-down-method
family: 03-refactoring
category: Refactoring
aliases: [Push Down Function, Move Method to Subclass]
first_described: "Fowler 1999"
maturity: canonical
related: [push-down-field, pull-up-method, extract-subclass, collapse-hierarchy, replace-conditional-with-polymorphism, move-function]
incompatible_with: []
verified: 2026-08-13
---

# Push Down Method

## 1. Name, aliases, and lineage

The canonical name is **Push Down Method**, introduced by Martin Fowler
in *Refactoring. Improving the Design of Existing Code*, 1st edition,
Addison-Wesley, 1999, chapter 11, "Dealing with Generalization." The
refactoring survived into the second edition, Martin Fowler, *Refactoring.
Improving the Design of Existing Code*, 2nd edition, Addison-Wesley, 2018,
chapter 12, "Simplification and Generalization," under the same name.
Fowler groups it with Pull Up Method, Pull Up Field, and Push Down Field,
because the four refactorings move features within an inheritance
hierarchy in opposite directions.

The underlying idea, that a method on a superclass that is only relevant
to one subclass should be moved to that subclass, is the inverse of Pull
Up Method. The method was placed on the superclass speculatively or was
once shared, and now only one subclass uses it. The method is dead weight
on the superclass's interface, and it should be pushed down.

## 2. Problem and context

A method on the superclass is only called by one subclass, or its
behaviour only makes sense for one subclass. The other subclasses inherit
the method but never call it, or calling it produces wrong behaviour
because the method assumes state that only one subclass has. The method
pollutes the superclass's interface, and a reader who sees it on the
superclass expects it to be a shared behaviour, not a subclass specific
one.

The situation reads like this. A `Account` superclass has a method
`calculateOverdraftFee` that is only meaningful for `CheckingAccount`.
`SavingsAccount` inherits the method but calling it produces zero or
throws, because savings accounts do not have overdrafts. The method is
on the superclass, but it is subclass specific, and its placement
communicates a shared behaviour that does not exist.

The fix is to push down the method. Move `calculateOverdraftFee` from
`Account` to `CheckingAccount`, and remove it from the superclass.
`SavingsAccount` no longer inherits it, and the superclass's interface
is cleaner.

## 3. Forces

**Interface cleanliness versus access path.** A method on the superclass
that only one subclass uses is dead weight on the interface. Pushing it
down removes the dead weight but requires callers to use the subclass
type. The force favours pushing down when the method is clearly subclass
specific.

**Speculation versus present reality.** The method was placed on the
superclass expecting sharing. Pushing it down accepts that the speculation
was wrong. The force favours pushing down when the speculation is clearly
wrong.

**Polymorphism versus subclass specific behaviour.** A method on the
superclass can be overridden by subclasses, which is polymorphic. A
method on the subclass is not visible through the superclass type, which
prevents polymorphic dispatch. The force favours keeping when
polymorphism is wanted, and favours pushing down when the method is
subclass specific and should not be polymorphic.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- A method on the superclass is only called by one subclass, and the
  other subclasses never call it or calling it produces wrong behaviour.
- The method's behaviour assumes state that only one subclass has, and
  it is not meaningful as a shared behaviour.
- The method is dead weight on the superclass's interface, and its
  presence communicates a shared behaviour that does not exist.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The method is called polymorphically through the superclass type by
  consumers who do not know the subclass. Pushing down breaks the
  polymorphic dispatch.
- The method is part of the superclass's public API and consumers call
  it through the superclass type. Pushing down breaks the contract.
- The method is used by more than one subclass, even if not all. The fix
  is an intermediate superclass, not a push down to one.

## 5. Structure

The refactoring has one participant: the method that is moved from the
superclass to the subclass.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER
  ------                              -----

  class Account:                     class Account:
    balance                             balance
    calculateOverdraftFee()
                                     class CheckingAccount(Account):
  class CheckingAccount(Account):      calculateOverdraftFee()  (pushed down)
    (calls calculateOverdraftFee)
                                     class SavingsAccount(Account):
  class SavingsAccount(Account):       (no longer inherits it)
    (inherits but never calls)
```

## 7. Dynamics

```
  t0  identify method on superclass
       only one subclass uses
       |
       v
  t1  move the method to the subclass
       |
       v
  t2  remove the method from the superclass
       |
       v
  t3  update callers that accessed the
       method through the superclass type
       (requires cast or type check)
       |
       v
  t4  run test suite
       |
       v
  t5  commit. the method is pushed down.
```

## 8. Implementation variants

**Direct push down.** The canonical variant. The method is moved to the
subclass and removed from the superclass.

**Push down with abstract method.** The method is pushed down to the
subclass, and an abstract declaration remains on the superclass for
polymorphic dispatch. This variant is used when the method should be
called through the superclass type but the implementation is subclass
specific.

**Push down with interface.** The method is pushed down, and the
superclass declares an interface that subclasses can implement
optionally. Callers that need the method check `instanceof` or use a
pattern match to access it.

```python
# Python: before (method on superclass, only one subclass uses)

class Account:
    def __init__(self, balance: float):
        self.balance = balance

    def calculate_overdraft_fee(self) -> float:
        return max(0, -self.balance) * 0.10

class CheckingAccount(Account):
    pass  # uses inherited method

class SavingsAccount(Account):
    pass  # inherits but overdraft makes no sense

# Python: after (pushed down)

class Account:
    def __init__(self, balance: float):
        self.balance = balance

class CheckingAccount(Account):
    def calculate_overdraft_fee(self) -> float:
        return max(0, -self.balance) * 0.10

class SavingsAccount(Account):
    pass  # no longer has the method
```

```typescript
// TypeScript: after (pushed down)

class Account {
    constructor(public balance: number) {}
}

class CheckingAccount extends Account {
    calculateOverdraftFee(): number {
        return Math.max(0, -this.balance) * 0.10;
    }
}

class SavingsAccount extends Account {
    // no calculateOverdraftFee
}
```

```java
// Java: after (pushed down with abstract method for polymorphism)

public abstract class Account {
    protected double balance;

    // abstract: callers can dispatch polymorphically
    public abstract double calculateOverdraftFee();
}

public class CheckingAccount extends Account {
    @Override
    public double calculateOverdraftFee() {
        return Math.max(0, -balance) * 0.10;
    }
}

public class SavingsAccount extends Account {
    @Override
    public double calculateOverdraftFee() {
        return 0;  // no overdraft for savings
    }
}
```

## 9. Known production uses

**Java's `java.awt.Container` class** has methods like `getComponents`
and `setLayout` that were pushed down from `Component`, because only
containers have child components and layout managers. Non-container
components like `Button` do not have these methods
([java.awt.Container](https://docs.oracle.com/en/java/javase/21/docs/api/java.desktop/java/awt/Container.html),
verified 2026-08-13).

**Python's `list` vs `deque`** show push down in the standard library.
`list` has `sort` which is specific to list semantics, while `deque` has
`rotate` and `maxlen` which are specific to deque semantics. Methods that
are only on one collection type are not on the shared `Sequence` ABC,
which is the push down applied at the ABC level
([collections.abc documentation](https://docs.python.org/3/library/collections.abc.html),
verified 2026-08-13).

## 10. Consequences

Positive.

- The superclass's interface is cleaner, because it no longer holds a
  method that only one subclass uses.
- The method is colocated with the subclass that uses it, which is the
  correct ownership.
- A caller that calls the method on the wrong subclass gets a compile
  error in a static language, which is safer than inheriting a method
  that produces wrong behaviour.

Negative.

- Code that called the method through the superclass type must now cast
  or type check, which adds ceremony.
- If the method is needed by a future subclass, it must be pushed up
  again or duplicated.
- The polymorphic dispatch through the superclass type is lost, unless
  an abstract method remains.

## 11. Failure modes and misuse

**Pushing down a polymorphic method.** The method is called through the
superclass type by consumers who do not know the subclass. Pushing it
down breaks the dispatch. The symptom is a compile error in a static
language or an `AttributeError` in a dynamic language.

**Pushing down a method used by multiple subclasses.** The method is
used by two of three subclasses, and pushing it down to one leaves the
other without it. The fix is an intermediate superclass, not a push down
to one subclass.

## 12. Trade-off matrix

| Alternative | Dead weight | Polymorphism | When to prefer |
|---|---|---|---|
| Push Down Method | Eliminated | Lost (unless abstract) | Method only one subclass uses |
| Pull Up Method | None | Inherited | Method shared by all subclasses |
| Replace Conditional with Polymorphism | N/A | Full | Conditional dispatches on type |
| Keep on superclass | Present | Present | Method is part of contract |

## 13. Related and incompatible patterns

**Push Down Field** (same catalog) is the field version.

**Pull Up Method** (same catalog) is the inverse.

**Extract Subclass** (same catalog) creates the subclass, which is the
prerequisite if it does not exist.

**Replace Conditional with Polymorphism** (same catalog) is the
alternative when the method should be polymorphic but the implementations
differ by subclass.

## 14. Refactoring path in and out

**Path in.** Move the method to the subclass, remove from superclass,
update callers.

**Path out.** Pull Up Method moves the method back to the superclass
when it turns out to be shared.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test that called the method should produce the same result, now through
the subclass.

## 16. Observability signals

The refactoring does not change behaviour, so the observable signal in
production is nothing.

## 17. Security and privacy implications

The refactoring improves security when the method accesses sensitive
data that should not be on every subclass. Pushing it down limits access
to the subclass that needs it.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 12, "Push Down Method."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 11, "Push Down Method."
- Oracle, "java.awt.Container,"
  [https://docs.oracle.com/en/java/javase/21/docs/api/java.desktop/java/awt/Container.html](https://docs.oracle.com/en/java/javase/21/docs/api/java.desktop/java/awt/Container.html),
  verified 2026-08-13.
- Python Software Foundation, "collections.abc,"
  [https://docs.python.org/3/library/collections.abc.html](https://docs.python.org/3/library/collections.abc.html),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
