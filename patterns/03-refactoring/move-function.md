---
name: Move Function
slug: move-function
family: 03-refactoring
category: Refactoring
aliases: [Move Method, Relocate Method, Relocate Function]
first_described: "Fowler 1999"
maturity: canonical
related: [move-field, extract-class, inline-class, hide-delegate, change-function-declaration, extract-function]
incompatible_with: []
verified: 2026-08-13
---

# Move Function

## 1. Name, aliases, and lineage

The canonical name is **Move Function**, introduced by Martin Fowler in
*Refactoring. Improving the Design of Existing Code*, 1st edition,
Addison-Wesley, 1999, chapter 7, "Moving Features Between Objects,"
where it appeared as **Move Method.** In the second edition, Martin
Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
edition, Addison-Wesley, 2018, chapter 9, "Moving Features," Fowler
renamed it to Move Function to match the rename of Extract Method to
Extract Function, because the operation applies to free functions as
well as methods.

The underlying principle, that a function should live on the class or
module that uses it most, is the responsibility driven design principle
from Rebecca Wirfs Brock and Brian Wilkerson, *Object-Oriented Design: A
Responsibility Driven Approach*, 1989. A function that is on the wrong
class is a sign that the responsibilities are misplaced, and the move
puts the function where its responsibility belongs.

The alias **Move Method** is the original name from the first edition and
is the name used in the Eclipse and IntelliJ refactoring menus. The alias
**Relocate Method** is used in the C sharp community.

## 2. Problem and context

A function is on a class or module that does not use it, or that uses it
less than another class does. The function was placed on the original
class because it seemed related at the time, but over time the function's
primary user has become a different class, and the original class now has
to delegate every call to the function, or the function accesses the other
class's fields more than its own. The function is on the wrong side of the
relationship, and the misplacement produces delegation methods, feature
envy, and coupling that would not exist if the function were on the right
class.

The situation reads like this. An `Account` class has a method
`calculateOverdraftCharge` that calculates the overdraft charge for an
account type. The method reads the account type's fields (the interest
rate, the fee structure, the threshold) and barely touches the Account
class's own fields. The method has feature envy: it is more interested in
the `AccountType` class than in the `Account` class. Every call to the
method is `account.calculateOverdraftCharge()`, but the method immediately
accesses `account.type.interestRate` and `account.type.fee`, which means
the method is reaching through the Account to the AccountType, and the
Account is just a pass through.

The fix is to move the function. Move `calculateOverdraftCharge` from
`Account` to `AccountType`, where the fields it uses live. `Account`
delegates to `account.type.calculateOverdraftCharge()`, which is a one
line call instead of a full method body.

## 3. Forces

**Feature envy versus colocation.** A function that accesses another
class's fields more than its own has feature envy, which is a smell.
Moving the function to the envied class collocates it with the data it
uses. The force favours moving when the feature envy is clear and
persistent.

**Delegation versus ownership.** A function on the wrong class requires
delegation, which is indirection. A function on the right class is owned
and accesses its data directly. The force favours moving when the
delegation burden exceeds the move cost.

**Cohesion versus coupling.** A function on the wrong class has low
cohesion with the class's other methods, because it serves a different
responsibility. Moving it to the right class improves cohesion. The force
favours moving when the move improves both cohesion and coupling.

**Polymorphism versus static dispatch.** A function that is a candidate
for polymorphic dispatch should be on the class that is the polymorphic
receiver, not on the caller. The force favours moving when the function
should be overridden by subclasses.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- The function accesses another class's fields more than its own, which
  is the feature envy smell. The function is more interested in the other
  class.
- The function is on the wrong class for polymorphic dispatch: subclasses
  of the other class should override it, but it is on a class that is not
  in the hierarchy.
- The function was placed on the original class for historical reasons
  that no longer apply, and the function's natural home is now the other
  class.
- The function is called from the other class more than from its own
  class, and the call path through the original class is a pass through.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The function uses its own class's fields as much as the other class's,
  and the move would create feature envy in the other direction. The
  function is on the right class.
- The function is part of the class's public API and consumers call it by
  name on the original class. Moving it breaks every consumer.
- The function is a callback or a handler that is registered with the
  original class, and moving it would break the registration contract.
- The move would require passing the original class as a parameter to the
  function, which replaces one form of coupling with another.

## 5. Structure

The refactoring has two participants.

- **The source class.** The class that currently holds the function. After
  the refactoring, the function is removed, and a delegating method may
  remain for backward compatibility.
- **The target class.** The class that will hold the function. After the
  refactoring, the function is on this class.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER
  ------                              -----

  class Account:                     class AccountType:
    type: AccountType                  interestRate
                                       fee
    calculateOverdraft():              threshold
      // uses type.interestRate
      // uses type.fee                 calculateOverdraft():
      // uses type.threshold             // uses interestRate
      // barely uses own fields          // uses fee
                                         // uses threshold
  class AccountType:
    interestRate                    class Account:
    fee                                type: AccountType
    threshold
                                      overdraftCharge():
                                        return type.calculateOverdraft()
  (feature envy on AccountType)      (function on AccountType, Account delegates)
```

## 7. Dynamics

```
  t0  identify function with feature envy
       |
       v
  t1  create the function on the
       target class, copying the body
       |
       v
  t2  adjust the body: replace accesses
       to the source's fields with
       parameters or the target's fields
       |
       v
  t3  replace the source's function body
       with a delegation call to the target
       |
       v
  t4  update callers to call the target
       directly (optional, can be gradual)
       |
       v
  t5  run test suite
       |
       v
  t6  commit. the function is moved.
```

## 8. Implementation variants

**Move with delegation.** The canonical variant. The function is created
on the target, and the source's function body is replaced with a
delegation call. Callers can be updated gradually, or they can continue
to call the source's delegating method.

**Move with parameter.** When the function needs access to the source
class, the source is passed as a parameter to the moved function. This
variant is used when the function uses both classes' fields.

**Move to free function.** In languages with free functions, the function
is moved out of the class entirely and into a module. This variant is the
free function version of the move, and it is the one Fowler's second
edition name reflects.

```python
# Python: before (feature envy)

class Account:
    def __init__(self, account_type: "AccountType"):
        self.type = account_type
        self.days_overdrawn = 0

    def overdraft_charge(self) -> float:
        if self.type.premium:
            base = 10
            if self.days_overdrawn > 7:
                base += (self.days_overdrawn - 7) * 0.85
            return base
        return self.days_overdrawn * 1.75

class AccountType:
    premium: bool = False

# Python: after (moved to AccountType)

class AccountType:
    def __init__(self, premium: bool = False):
        self.premium = premium

    def overdraft_charge(self, days_overdrawn: int) -> float:
        if self.premium:
            base = 10
            if days_overdrawn > 7:
                base += (days_overdrawn - 7) * 0.85
            return base
        return days_overdrawn * 1.75

class Account:
    def __init__(self, account_type: AccountType):
        self.type = account_type
        self.days_overdrawn = 0

    def overdraft_charge(self) -> float:
        return self.type.overdraft_charge(self.days_overdrawn)
```

```typescript
// TypeScript: after (moved with parameter)

class AccountType {
    constructor(public premium: boolean = false) {}

    overdraftCharge(daysOverdrawn: number): number {
        if (this.premium) {
            let base = 10;
            if (daysOverdrawn > 7) {
                base += (daysOverdrawn - 7) * 0.85;
            }
            return base;
        }
        return daysOverdrawn * 1.75;
    }
}

class Account {
    constructor(
        private type: AccountType,
        private daysOverdrawn: number = 0
    ) {}

    overdraftCharge(): number {
        return this.type.overdraftCharge(this.daysOverdrawn);
    }
}
```

```java
// Java: after (moved to AccountType)

public class AccountType {
    private final boolean premium;

    public AccountType(boolean premium) {
        this.premium = premium;
    }

    public double overdraftCharge(int daysOverdrawn) {
        if (premium) {
            double base = 10;
            if (daysOverdrawn > 7) {
                base += (daysOverdrawn - 7) * 0.85;
            }
            return base;
        }
        return daysOverdrawn * 1.75;
    }
}

class Account {
    private final AccountType type;
    private final int daysOverdrawn;

    public Account(AccountType type, int daysOverdrawn) {
        this.type = type;
        this.daysOverdrawn = daysOverdrawn;
    }

    public double overdraftCharge() {
        return type.overdraftCharge(daysOverdrawn);
    }
}
```

## 9. Known production uses

**IntelliJ IDEA's Move refactoring** automates moving an instance method
to a different class. JetBrains documents that the list of move targets
includes the method parameters' classes and fields' classes in the
current class, and that the person picks the destination and a parameter
name for the reference back to the original class
([JetBrains Move documentation](https://www.jetbrains.com/help/idea/move-refactorings.html),
verified 2026-08-19).

**Eclipse's "Move" refactoring** provides the same automation for Java
methods
([Eclipse Move refactoring](https://help.eclipse.org/latest/topic/org.eclipse.jdt.doc.user/tasks/task-moving.html),
verified 2026-08-13).

## 10. Consequences

Positive.

- The function is colocated with the data it uses, which eliminates
  feature envy and reduces the access path.
- The delegation from the source is a one line call, which is simpler
  than the full method body.
- The target class gains a method that is cohesive with its other
  methods, because it serves the same responsibility.
- The function can be overridden by subclasses of the target class, which
  enables polymorphic dispatch.

Negative.

- The source class may need to delegate, which adds a one line method
  that is pure indirection.
- If the function uses both classes' fields, the move requires passing
  the source as a parameter, which is a different form of coupling.
- The function's visibility changes from the source's callers to the
  target's callers, which may be a breaking change if the function is
  public.
- The move changes the call site from `source.function()` to
  `target.function()`, which is a mechanical change but a wide one if
  the function is widely called.

## 11. Failure modes and misuse

**Moving a function that uses both classes equally.** The function uses
its own class's fields as much as the other class's, and the move creates
feature envy in the other direction. The symptom is the same smell in the
opposite direction.

**Moving a function and breaking polymorphism.** The function is called
polymorphically on the source class, and moving it to the target class
breaks the dispatch, because the target class is not in the polymorphic
hierarchy. The symptom is a subclass override that is no longer called.

**Moving a public API function.** The function is part of a public API
and consumers call it on the source class. Moving it breaks every
consumer.

**Over moving.** Functions are moved frequently based on temporary usage
patterns, and the codebase is in constant flux. The symptom is a
codebase where functions are always moving, which makes the code hard to
understand.

## 12. Trade-off matrix

| Alternative | Feature envy | Delegation | Cohesion | When to prefer |
|---|---|---|---|---|
| Move Function | Eliminated | One line on source | Improved | Function envies target class |
| Extract Class | Eliminated | None | Improved | Two responsibilities on one class |
| Hide Delegate | Reduced | Added on server | Same | Client reaches through chain |
| Keep function | Present | Present | Lower | Function on right class |

## 13. Related and incompatible patterns

**Move Field** (same catalog) is the field version. It moves a field to
the class that uses it most, where Move Function moves a method. The two
are frequently applied together: move the fields, then move the methods
that use them.

**Extract Class** (same catalog) is the larger scale version. It moves a
group of fields and methods to a new class, where Move Function moves one
method.

**Extract Function** (same catalog) is the step before the move. The
function is extracted from the source, then moved to the target. The two
are complementary: Extract creates the function, Move relocates it.

**Change Function Declaration** (same catalog) is applied alongside the
move to adjust the function's signature, for example adding a parameter
for the source class when the moved function needs access to it.

## 14. Refactoring path in and out

**Path in.** The refactoring is introduced by creating the function on
the target and delegating from the source. The steps are:

1. Create the function on the target class, copying the body.
2. Adjust the body: replace accesses to the source's fields with
   parameters or the target's fields.
3. Replace the source's function body with a delegation call to the
   target.
4. Update callers to call the target directly (optional, can be
   gradual).
5. Run the test suite. Any failure means the body was not adjusted
   correctly or a caller was missed.

**Path out.** The refactoring is reversed by moving the function back to
the source. The reverse is applied when the move turned out to be wrong,
for example because the function uses both classes equally.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test that called the function should produce the same result, now through
the target class or through the source's delegation.

## 16. Observability signals

The refactoring does not change behaviour, so the observable signal in
production is nothing. The call site may change in traces, which is a
minor format change.

## 17. Security and privacy implications

The refactoring does not change what data is processed or how it is
processed, so it does not change the security surface. The security
relevant case is when the move places the function on a class with
stronger access control, which is a positive security signal.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 9, "Move Function."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 7, "Move Method."
- Rebecca Wirfs Brock and Brian Wilkerson, "Object-Oriented Design: A
  Responsibility Driven Approach," 1989.
- JetBrains, "Move,"
  [https://www.jetbrains.com/help/idea/move-refactorings.html](https://www.jetbrains.com/help/idea/move-refactorings.html),
  verified 2026-08-19.
- Eclipse Foundation, "Moving,"
  [https://help.eclipse.org/latest/topic/org.eclipse.jdt.doc.user/tasks/task-moving.html](https://help.eclipse.org/latest/topic/org.eclipse.jdt.doc.user/tasks/task-moving.html),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
