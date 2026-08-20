---
name: Remove Subclass
slug: remove-subclass
family: 03-refactoring
category: Refactoring
aliases: [Remove Subclassing, Eliminate Subclass, Collapse Subclass]
first_described: "Fowler 2018"
maturity: canonical
related: [collapse-hierarchy, extract-subclass, remove-dead-code, replace-inheritance-with-delegation, replace-conditional-with-polymorphism]
incompatible_with: []
verified: 2026-08-13
---

# Remove Subclass

## 1. Name, aliases, and lineage

The canonical name is **Remove Subclass**, introduced by Martin Fowler in
*Refactoring. Improving the Design of Existing Code*, 2nd edition,
Addison-Wesley, 2018, chapter 12, "Simplification and Generalization."
The refactoring is new to the second edition, though the broader
Collapse Hierarchy from the first edition (1999) covered the case of
removing an empty subclass. Fowler split it out because the mechanics
differ when the subclass has fields or methods that need to be moved
before the deletion, and when callers reference the subclass type.

## 2. Problem and context

A subclass exists but adds no value over its superclass. The subclass
was created to specialise behaviour, but over time the specialisation
was removed, or it was absorbed by the superclass, or it was never
implemented. The subclass is now empty or a pass through, and it adds a
class, a file, and a level of hierarchy without adding any distinction.

The situation reads like this. A `SavingsAccount` subclass of `Account`
was created because savings accounts had different interest calculation
logic. The interest calculation was moved to a strategy object, the
account type was parameterised, and the subclass became empty.
`SavingsAccount` now has no fields, no methods, and no constructors
beyond the inherited ones. The subclass exists only as a type label.

The fix is to remove the subclass. Move any remaining fields or methods
to the superclass (or delete them if they are dead), update callers that
reference the subclass type to use the superclass, and delete the
subclass.

## 3. Forces

**Hierarchy depth versus simplicity.** A subclass that adds no value
increases the hierarchy depth without adding distinction. Removing it
simplifies the hierarchy. The force favours removal when the subclass is
empty or a pass through.

**Type distinction versus flatness.** A subclass provides a distinct
type that the compiler can check. Removing it loses the type distinction.
The force favours keeping when the type is load bearing in the type
system, and favours removal when the type is not used.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- A subclass has no fields or methods of its own, or its members are
  dead code or pass throughs.
- The subclass does not provide a type that callers use.
- The subclass was created speculatively and the specialisation was never
  implemented.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The subclass has behaviour that the superclass does not, even if the
  behaviour is small.
- The subclass provides a type used in the type system.
- The subclass is part of a public API.

## 5. Structure

The refactoring has one participant: the subclass that is removed.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER
  ------                              -----

  Account                             Account
  +-- SavingsAccount (empty)          (subclass removed)

  caller:                             caller:
    new SavingsAccount()              new Account(savingsStrategy)
```

## 7. Dynamics

```
  t0  identify empty subclass
       |
       v
  t1  move any remaining members to superclass
       or delete dead code
       |
       v
  t2  update callers to use superclass
       |
       v
  t3  delete the subclass
       |
       v
  t4  run test suite
       |
       v
  t5  commit. subclass removed.
```

## 8. Implementation variants

**Delete subclass.** The canonical variant. The subclass is deleted
after members are moved or deleted.

**Replace with type code.** The subclass is removed, and a type code
field on the superclass distinguishes the cases that the subclass used
to handle. This variant is used when the type distinction is needed but
not as a class hierarchy.

**Replace with interface.** The subclass is removed, and an interface
preserves the type for callers that need it.

```python
# Python: before (empty subclass)

class Account:
    def __init__(self, balance: float):
        self.balance = balance

class SavingsAccount(Account):
    pass  # empty

# Python: after (subclass removed)

class Account:
    def __init__(self, balance: float):
        self.balance = balance

# caller: new Account(100) instead of new SavingsAccount(100)
```

```typescript
// TypeScript: after (subclass removed)

class Account {
    constructor(public balance: number) {}
}

// caller: new Account(100) instead of new SavingsAccount(100)
```

```java
// Java: after (subclass removed, interface preserves type)

interface SavingsAccount {}

public class Account implements SavingsAccount {
    private double balance;

    public Account(double balance) {
        this.balance = balance;
    }
}
```

## 9. Known production uses

**IntelliJ IDEA's "Safe Delete" refactoring** detects when a class is
unused or only a type label, and offers to remove it after verifying no
caller references it
([JetBrains Safe Delete](https://www.jetbrains.com/help/idea/safe-delete.html),
verified 2026-08-13).

**Java's `removeIf` on collections** is a related concept at the data
level: elements that do not match a predicate are removed from a
collection, which is the data analogue of removing a subclass that does
not add value
([java.util.Collection.removeIf](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Collection.html#removeIf(java.util.function.Predicate)),
verified 2026-08-13).

## 10. Consequences

Positive.

- The hierarchy is one level shallower, which reduces the cognitive cost
  of understanding it. A reader who navigates the class hierarchy has one
  fewer level to traverse, and the superclass's interface is the only one
  to learn.
- The codebase has one fewer class to maintain, which means one fewer
  file, one fewer test fixture, and one fewer name to remember. The
  maintenance burden is proportional to the number of classes, and
  removing one reduces it.
- The reader no longer needs to determine whether the subclass is empty
  or has behaviour, which is a question that every reader must answer
  when they encounter the subclass. Removing the subclass eliminates the
  question.
- The superclass can evolve without worrying about the subclass, which
  means a change to the superclass does not need to be checked against the
  subclass for compatibility.

Negative.

- The type distinction is lost, which may weaken compile time guarantees.
  Callers that declared parameters of the subclass type must now use the
  superclass type, which is wider and may accept instances that the
  subclass type would have rejected.
- If the subclass is needed later, it must be re created with Extract
  Subclass. The cost of re creation is the same as the original extraction,
  which is more work than keeping the empty subclass.
- The subclass's name is lost from the codebase, which may affect
  documentation, commit messages, and issue trackers that reference the
  name. The name was a concept in the team's vocabulary, and its removal
  means the concept must be communicated differently.

## 11. Failure modes and misuse

**Removing a subclass with behaviour.** The subclass has methods that the
superclass does not, and removing it loses the behaviour.

**Removing a subclass used in the type system.** Callers declare
parameters of the subclass type, and removing it breaks the type
declarations.

## 12. Trade-off matrix

| Alternative | Hierarchy | Type distinction | When to prefer |
|---|---|---|---|
| Remove Subclass | -1 | Lost | Subclass is empty |
| Collapse Hierarchy | -1 | Lost | Empty hierarchy level |
| Extract Subclass | +1 | Added | Class needs specialisation |
| Replace Inheritance with Delegation | 0 | Changed | Hierarchy is wrong |

## 13. Related and incompatible patterns

**Collapse Hierarchy** (same catalog) removes an empty hierarchy level,
which is the same operation when the subclass is truly empty.

**Extract Subclass** (same catalog) is the inverse. It adds a subclass
for a specialisation.

**Replace Inheritance with Delegation** (same catalog) is the
alternative when the subclass has behaviour but the inheritance is the
wrong model.

## 14. Refactoring path in and out

**Path in.** Move members, update callers, delete subclass.

**Path out.** Extract Subclass re creates the subclass when a
specialisation is needed.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test that constructed the subclass should construct the superclass and
should produce the same result.

## 16. Observability signals

The refactoring does not change behaviour, so the observable signal in
production is nothing.

## 17. Security and privacy implications

The refactoring does not change what data is stored, so it does not
change the security surface.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 12, "Remove Subclass."
- JetBrains, "Safe Delete,"
  [https://www.jetbrains.com/help/idea/safe-delete.html](https://www.jetbrains.com/help/idea/safe-delete.html),
  verified 2026-08-13.
- Oracle, "Collection.removeIf,"
  [https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Collection.html#removeIf(java.util.function.Predicate)](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Collection.html#removeIf(java.util.function.Predicate)),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
