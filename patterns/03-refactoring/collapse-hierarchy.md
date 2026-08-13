---
name: Collapse Hierarchy
slug: collapse-hierarchy
family: 03-refactoring
category: Refactoring
aliases: [Merge Superclass and Subclass, Flatten Inheritance]
first_described: "Fowler 1999"
maturity: canonical
related: [extract-superclass, extract-subclass, replace-inheritance-with-delegation, replace-delegation-with-inheritance, inline-class]
incompatible_with: []
verified: 2026-08-13
---

# Collapse Hierarchy

## 1. Name, aliases, and lineage

The canonical name is **Collapse Hierarchy**, introduced by Martin Fowler in
*Refactoring. Improving the Design of Existing Code*, 1st edition,
Addison-Wesley, 1999, chapter 11, "Dealing with Generalization." The
refactoring survived into the second edition, Martin Fowler, *Refactoring.
Improving the Design of Existing Code*, 2nd edition, Addison-Wesley, 2018,
chapter 12, "Simplification and Generalization," under the same name and
with the same mechanics. Fowler moved it alongside Extract Superclass and
Extract Subclass in both editions, because the three refactorings form a
family: you add a hierarchy level with Extract, you remove one with
Collapse.

The alias **Merge Superclass and Subclass** appears in the Eclipse
refactoring menu, where the operation is offered as a safe transformation
that the IDE performs with compile time verification of every affected
call site. The alias **Flatten Inheritance** is used in the JavaScript
community, where prototype chains are the inheritance mechanism and
flattening means moving all properties up the chain into the base
constructor.

## 2. Problem and context

A subclass and its superclass have diverged or, more commonly, have
converged to the point where the hierarchy level adds no value. The
subclass was originally created to specialise behaviour, but over time
either the specialisation was removed or the superclass absorbed it, and
now the subclass is a pass through that adds a level of indirection
without adding a distinction. Every method on the subclass either
overrides the superclass method identically or is empty, and every field
on the subclass could live on the superclass without affecting any other
subclass.

The situation reads like this. A `SavingsAccount` subclass of `Account`
was created because savings accounts had different interest calculation
logic. Over several refactors, the interest calculation was moved to a
strategy object, the account type was parameterised, and the subclass
became empty. `SavingsAccount` now has no fields, no methods, and no
constructors beyond the ones it inherits. It exists only as a type label,
and every place that constructs a `SavingsAccount` could construct an
`Account` with the savings strategy and get identical behaviour. The
hierarchy level is pure overhead: it adds a class, a file, and a level of
navigation every reader must traverse, and it gives nothing back.

The fix is to collapse the hierarchy. Merge the subclass into the
superclass (or the superclass into the subclass, whichever direction
reduces the number of classes without losing behaviour), and delete the
empty level. Every reference to the collapsed class is updated to point to
the surviving class.

## 3. Forces

**Distinction versus indirection.** A hierarchy level that distinguishes
behaviour is earning its place. A hierarchy level that adds only indirection
is not. The force favours collapsing when the indirection cost exceeds the
distinction benefit, which happens when the subclass has no behaviour of its
own.

**Type safety versus simplicity.** A subclass provides a distinct type
that the compiler can check at call sites. Collapsing the hierarchy loses
that type, and every call site that referenced the subclass type must use
the superclass type instead, which may weaken compile time guarantees. The
force favours keeping the hierarchy when the type distinction is load
bearing in the type system, and collapsing when it is not.

**Future extension versus present clarity.** A hierarchy level that is
empty today might be needed tomorrow when a new specialisation is added.
The force favours keeping the hierarchy as a speculative investment in
future extension, and collapsing when the future extension is speculative
enough that the present indirection cost is not justified by it.

**Documentation versus structure.** A class name can communicate intent
even when the class has no behaviour. `SavingsAccount` as an empty subclass
tells the reader that the codebase knows about savings accounts, even if
the behaviour is elsewhere. The force favours keeping the hierarchy when
the name is documentation, and collapsing when the name is a lie because
the class does not actually do anything savings specific.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- A subclass has no fields, no methods, and no constructors of its own. It
  is a pure pass through to the superclass, and every instance of the
  subclass behaves identically to an instance of the superclass with the
  same configuration.
- A hierarchy level was created speculatively, for a specialisation that
  was never implemented or that was implemented and then removed, and the
  level has been empty since.
- Two classes in a hierarchy have converged over time to the point where
  one is a copy of the other, and the duplication is a maintenance burden
  because every change must be made in both places.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The subclass has behaviour that the superclass does not, even if the
  behaviour is small. The hierarchy level is distinguishing, and collapsing
  it would merge two classes that are genuinely different.
- The subclass provides a type that is used in the type system. Callers
  declare parameters or variables of the subclass type and rely on the
  compiler to reject instances of the superclass. Collapsing would weaken
  the type guarantee and is a breaking change if the class is part of a
  public API.
- The hierarchy is part of a framework that expects a specific depth or
  structure, for example a UI component framework that instantiates
  subclasses by name. Collapsing would break the framework's instantiation
  contract.
- The subclass is a public API entry point that consumers construct by
  name. Collapsing it would break every consumer that references the class
  name, which is the same breaking change as renaming a public class.

## 5. Structure

The refactoring has two participants.

- **The subclass.** The class being merged into its parent. After the
  refactoring, this class no longer exists.
- **The superclass.** The class that receives the subclass's fields and
  methods (if any) and that survives the refactoring.

If the subclass has fields or methods that the superclass does not, those
are moved up before the collapse, using Pull Up Field and Pull Up Method
refactorings from the same catalog. The collapse itself is the deletion of
the subclass after everything has been moved.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER

  Account                             Account
  +-- balance                          +-- balance
  +-- deposit()                        +-- deposit()
  +-- withdraw()                       +-- withdraw()
                                       +-- (interest strategy field,
  SavingsAccount                           moved from subclass)
  +-- interestStrategy
  +-- (no methods of its own)

  callers:                            callers:
    new SavingsAccount()                new Account(savingsStrategy)
```

## 7. Dynamics

```
  t0  subclass identified as empty or redundant
       |
       v
  t1  if subclass has fields, pull them up to superclass
       (Pull Up Field)
       |
       v
  t2  if subclass has methods, pull them up to superclass
       (Pull Up Method)
       |
       v
  t3  update every call site that constructs the subclass
       to construct the superclass instead
       |
       v
  t4  run test suite
       -- if green, the behaviour is identical
       -- if red, a call site was missed or a method
          was not pulled up correctly
       |
       v
  t5  delete the subclass
       |
       v
  t6  commit. the hierarchy is one level shallower.
```

## 8. Implementation variants

**Collapse subclass into superclass.** The standard variant. The subclass
is empty or its contents are moved up, and the subclass is deleted. Every
call site that referenced the subclass is updated to reference the
superclass. This is the variant Fowler describes in both editions.

**Collapse superclass into subclass.** The reverse direction, used when
the superclass is the one that is empty and the subclass is the one with
real behaviour. The superclass is deleted, and the subclass inherits from
the superclass's parent instead. This variant is less common but is the
right choice when a hierarchy level was added above an existing class and
never filled in.

**Collapse via interface extraction.** When the subclass provides a type
that callers depend on but has no behaviour, the type can be preserved as
an interface or a marker type while the class is collapsed. The interface
has no methods and exists only as a type label, and the superclass
implements it. This variant preserves the type guarantee while removing
the empty class.

```python
# Python: before (empty subclass)

class Account:
    def __init__(self, balance: int):
        self.balance = balance

    def deposit(self, amount: int) -> None:
        self.balance += amount

class SavingsAccount(Account):
    pass  # empty subclass, adds nothing

# Python: after (collapsed)

class Account:
    def __init__(self, balance: int):
        self.balance = balance

    def deposit(self, amount: int) -> None:
        self.balance += amount
```

```typescript
// TypeScript: before (empty subclass)

class Account {
    constructor(public balance: number) {}

    deposit(amount: number): void {
        this.balance += amount;
    }
}

class SavingsAccount extends Account {
    // no fields, no methods
}

// TypeScript: after (collapsed, interface preserves type)

interface SavingsAccountType {}

class Account {
    constructor(public balance: number) {}

    deposit(amount: number): void {
        this.balance += amount;
    }
}

// callers that need the type label use the interface:
function createSavings(): Account & SavingsAccountType {
    return new Account(0) as Account & SavingsAccountType;
}
```

```java
// Java: collapse with interface preservation

// before
public class Account {
    private int balance;
    public void deposit(int amount) { balance += amount; }
}

public class SavingsAccount extends Account {
    // empty
}

// after: interface preserves the type, class is deleted
public interface SavingsAccount {}

public class Account implements SavingsAccount {
    private int balance;
    public void deposit(int amount) { balance += amount; }
}
```

## 9. Known production uses

**Eclipse's "Extract Superclass" and "Pull Up" refactoring tools** include
the collapse operation as the inverse of extract. The Eclipse documentation
describes the refactorings as paired operations: Extract Superclass adds a
level, and the corresponding merge operation removes it when the level is
no longer needed
([Eclipse Refactoring documentation](https://help.eclipse.org/latest/topic/org.eclipse.jdt.doc.user/tasks/task-using_refactoring.htm),
verified 2026-08-13). The tool performs a compile time safety check and
reports every call site that references the collapsed class.

**IntelliJ IDEA's "Inline to Superclass" refactoring** automates the
collapse by moving every member of the subclass up to the superclass and
deleting the subclass. JetBrains documents that the tool verifies no
external code depends on the subclass name before allowing the collapse
([JetBrains Inline refactoring](https://www.jetbrains.com/help/idea/inline-refactoring.html),
verified 2026-08-13). This is the production variant used in Java
codebases where the IDE finds every call site.

## 10. Consequences

Positive.

- The codebase has one fewer class to read, maintain, and navigate.
- Every reader who encounters the hierarchy saves the time of discovering
  that the subclass is empty.
- The inheritance tree is one level shallower, which reduces the cognitive
  cost of understanding the type hierarchy.
- Future refactorings that touched the subclass are no longer needed,
  because the subclass is gone.

Negative.

- The type distinction is lost, and callers that referenced the subclass
  type must use the superclass type, which may weaken compile time
  guarantees.
- If a new specialisation is needed later, the hierarchy level must be
  re introduced with Extract Subclass, which is the inverse operation and
  is not free.
- If the collapse was premature, the subclass is re created with a
  different name and different mechanics, which is more disruptive than
  keeping the original empty subclass.

## 11. Failure modes and misuse

**Collapsing a subclass that is not actually empty.** A subclass that
appears empty because its methods are all inherited may still have a
constructor that sets a default strategy or a default field value that
callers depend on. Collapsing without moving the constructor logic means
every caller that constructed the subclass now constructs the superclass
with different defaults. The symptom is a behaviour change that is
invisible in the diff because the constructor body was not moved.

**Collapsing a public API class.** The subclass is part of a published
API, and consumers construct it by name. Collapsing it breaks every
consumer that references the class name, which is the same as deleting a
public type. The symptom is a compile error in consumer code that is only
discovered when the consumer upgrades.

**Collapsing too early.** The subclass is empty today but was created as
part of a planned extension that has not been implemented yet. Collapsing
the subclass means the extension must re create the hierarchy level when it
is implemented, which is more work than keeping the empty subclass. The
misuse is treating a planned extension as dead code.

**Collapsing the wrong direction.** The subclass has the real behaviour
and the superclass is the empty shell, but the refactoring collapses the
subclass into the superclass instead of the other way around. The result
is that the surviving class is the empty shell, and all the behaviour was
in the deleted class. The symptom is a class with no behaviour after the
collapse, which is obviously wrong but is a mistake that happens when the
direction is chosen without checking which class has the methods.

## 12. Trade-off matrix

| Alternative | Hierarchy depth | Type distinction | Indirection cost | When to prefer |
|---|---|---|---|---|
| Collapse Hierarchy | Reduced by one | Lost | Eliminated | Subclass is empty, type is not load bearing |
| Extract Subclass | Increased by one | Added | Introduced | A class needs a specialisation variant |
| Extract Superclass | Increased by one | Added | Introduced | Two classes share a common parent |
| Replace Inheritance with Delegation | Same | Same | Changed to composition | Hierarchy is wrong, composition is better |
| Inline Class | N/A | Lost | Eliminated | Two classes that are not in a hierarchy are merged |

## 13. Related and incompatible patterns

**Extract Subclass** (same catalog) is the inverse. It adds a hierarchy
level to introduce a specialisation. Collapse Hierarchy removes a level
when the specialisation is no longer needed. The two refactorings are
applied in opposite directions, and a codebase that oscillates between
them is not making a mistake, it is responding to changing requirements.

**Extract Superclass** (same catalog) is the other inverse. It adds a
hierarchy level above an existing class to introduce a shared parent.
Collapse Hierarchy can remove that level when the shared parent is no
longer earning its place.

**Inline Class** (same catalog) is the same operation applied to classes
that are not in an inheritance relationship. Inline Class merges a class
into its delegate, while Collapse Hierarchy merges a subclass into its
superclass. The mechanics are similar: move everything, update callers,
delete the source.

**Replace Inheritance with Delegation** (same catalog) is the alternative
when the hierarchy is wrong, not redundant. If the subclass has behaviour
but the inheritance is the wrong model, the fix is to replace inheritance
with delegation, not to collapse the hierarchy.

## 14. Refactoring path in and out

**Path in.** The refactoring is introduced by moving everything from the
subclass to the superclass and then deleting the subclass. The steps are:

1. Identify the empty or redundant subclass.
2. Move every field from the subclass to the superclass (Pull Up Field).
3. Move every method from the subclass to the superclass (Pull Up Method).
4. Move every constructor logic from the subclass to the superclass or to
   a factory method on the superclass.
5. Update every call site that constructs the subclass to construct the
   superclass instead.
6. Run the test suite. Any failure means a method or field was not moved
   or a call site was missed.
7. Delete the subclass.
8. If the type distinction must be preserved, introduce an interface or a
   marker type and have the superclass implement it.

**Path out.** The refactoring is reversed by Extract Subclass, which
re introduces a hierarchy level when a new specialisation is needed. There
is no scenario where the exact deleted subclass is restored, because the
subclass was deleted for being empty, and a restored empty subclass is
the same mistake.

## 15. Testing and verification

The test suite is the primary verification. After the collapse, every test
that constructed the subclass should now construct the superclass and
should pass unchanged, because the behaviour is identical. A test failure
means either a method or field was not moved up, or a call site was missed.

A grep for the subclass name after the collapse should return zero results
in the source. Hits in documentation, commit messages, and issue trackers
are expected and are not failures, but they should be reviewed for
accuracy, because the class no longer exists.

If an interface was introduced to preserve the type, a test should verify
that the superclass implements the interface and that callers that declare
the interface type still compile and pass.

## 16. Observability signals

A collapse does not change behaviour, so the observable signal in
production is nothing. The surviving class produces the same outputs for
the same inputs. If production observability changes after the collapse,
the change was not a collapse but a behaviour change, and the difference
is the signal that the refactoring was misclassified or that a method was
lost in the move.

The one observable difference is in class names that appear in logs,
traces, or serialised data. If the subclass name appeared in log output or
in serialised type information, the superclass name now appears instead.
This is expected and is not a regression, but anyone correlating across
the boundary needs to know both names.

## 17. Security and privacy implications

A collapse does not change the function's behaviour, so it does not open
new attack surfaces or close existing ones. The security relevant case is
when the subclass was used as a type guard, meaning the type system
enforced that only `SavingsAccount` instances were passed to a method
that assumed savings specific behaviour. After the collapse, the type
guard is gone, and the method accepts any `Account`, which may include
instances that were not intended to be savings accounts. This is a
weakening of the type system's enforcement, and it should be reviewed as a
security relevant change if the type guard was load bearing.

The privacy case is that the collapse does not change what data is stored
or transmitted, so it does not change the privacy surface. The refactoring
is silent on data handling.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 12, "Collapse Hierarchy."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 11, "Collapse Hierarchy."
- Eclipse Foundation, "Using Refactoring,"
  [https://help.eclipse.org/latest/topic/org.eclipse.jdt.doc.user/tasks/task-using_refactoring.htm](https://help.eclipse.org/latest/topic/org.eclipse.jdt.doc.user/tasks/task-using_refactoring.htm),
  verified 2026-08-13.
- JetBrains, "Inline refactoring,"
  [https://www.jetbrains.com/help/idea/inline-refactoring.html](https://www.jetbrains.com/help/idea/inline-refactoring.html),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
