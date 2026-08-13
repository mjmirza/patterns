---
name: Remove Middle Man
slug: remove-middle-man
family: 03-refactoring
category: Refactoring
aliases: [Remove Delegating Methods, Expose Delegate]
first_described: "Fowler 1999"
maturity: canonical
related: [hide-delegate, move-function, move-field, inline-class, extract-class]
incompatible_with: []
verified: 2026-08-13
---

# Remove Middle Man

## 1. Name, aliases, and lineage

The canonical name is **Remove Middle Man**, introduced by Martin Fowler
in *Refactoring. Improving the Design of Existing Code*, 1st edition,
Addison-Wesley, 1999, chapter 7, "Moving Features Between Objects." The
refactoring survived into the second edition, Martin Fowler, *Refactoring.
Improving the Design of Existing Code*, 2nd edition, Addison-Wesley, 2018,
chapter 9, "Moving Features," under the same name. Fowler groups it with
Hide Delegate as the inverse pair: one adds a delegating method, the
other removes it.

The underlying smell, the **Middle Man** smell, is one of Fowler's code
smells from the "Bad Smells in Code" chapter in both editions. A class
that delegates all its methods to another class is a middle man, and it
adds a level of indirection without adding value. The refactoring removes
the delegating methods and lets the client access the delegate directly.

## 2. Problem and context

A class has methods that do nothing but forward to another class. Every
method on the class is a one line delegation: `return delegate.method()`.
The class is a middle man, and it adds a class, a file, and a level of
navigation without adding any behaviour. The class was originally created
to hide the delegate, but the hiding has produced a pass through that
is pure overhead.

The situation reads like this. A `Person` class has a `Department`
delegate, and it has methods `getManager`, `getDepartmentName`, and
`getDepartmentCode` that all forward to `Department`. The Person class
is a middle man: every method delegates, and the class adds no behaviour
beyond forwarding. A caller that calls `person.getManager()` is really
calling `person.department.getManager()`, and the Person class is just
a pass through.

The fix is to remove the middle man. Expose the delegate through a getter,
remove the delegating methods, and let callers access the delegate
directly: `person.getDepartment().getManager()`.

## 3. Forces

**Indirection versus directness.** A middle man adds indirection, which
is overhead when the class adds no behaviour. Direct access to the
delegate is simpler. The force favours removal when the class is a pure
forwarder.

**Encapsulation versus simplicity.** A middle man hides the delegate,
which is encapsulation. Removing the middle man exposes the delegate,
which is direct but couples the client. The force favours removal when
the encapsulation is providing no value, because the class is not
enforcing invariants or adding behaviour.

**Coupling versus indirection.** Removing the middle man couples the
client to the delegate's type, which is coupling. The middle man shields
the client from the delegate, which is indirection. The force favours
removal when the coupling cost is lower than the indirection cost.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- A class has methods that do nothing but forward to a delegate, and
  the class is a pure pass through.
- The class is a middle man that adds no behaviour beyond delegation.
- The hiding of the delegate is not providing value, because the class
  does not enforce invariants or add validation.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The class adds behaviour in its delegating methods, for example
  validation, logging, or caching. The class is not a pure middle man.
- The hiding of the delegate is providing value, because the client
  should not know about the delegate's type or interface.
- The delegate is mutable and exposing it directly allows the client to
  modify it without the class's knowledge.

## 5. Structure

The refactoring has one participant: the delegating methods that are
removed, and the delegate that is exposed.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER
  ------                              -----

  class Person:                      class Person:
    department                         department  (exposed)
    getManager()                     getDepartment(): return department
      return department.getManager()  
  caller:                            caller:
    person.getManager()                person.getDepartment().getManager()
  (Person is middle man)             (client accesses delegate directly)
```

## 7. Dynamics

```
  t0  identify class with pure delegating methods
       |
       v
  t1  expose the delegate through a getter
       |
       v
  t2  remove the delegating methods
       |
       v
  t3  update callers to access the delegate directly
       |
       v
  t4  run test suite
       |
       v
  t5  commit. middle man removed.
```

## 8. Implementation variants

**Expose delegate.** The canonical variant. The delegate is exposed
through a getter, and the delegating methods are removed.

**Remove specific delegations.** Only the delegating methods that are
pure forwarding are removed. Delegating methods that add behaviour are
kept. This variant is used when the class is a partial middle man.

**Inline class.** When the middle man is removed and the delegate is
exposed, the class may become empty, in which case Inline Class removes
it entirely.

```python
# Python: before (middle man)

class Person:
    def __init__(self, department: "Department"):
        self._department = department

    def get_manager(self) -> "Person":
        return self._department.get_manager()

    def get_department_name(self) -> str:
        return self._department.get_name()

class Department:
    def __init__(self, manager: "Person", name: str):
        self._manager = manager
        self._name = name

    def get_manager(self) -> "Person":
        return self._manager

    def get_name(self) -> str:
        return self._name

# Python: after (middle man removed)

class Person:
    def __init__(self, department: "Department"):
        self._department = department

    def get_department(self) -> "Department":
        return self._department

# caller: person.get_department().get_manager()
```

```typescript
// TypeScript: after (delegate exposed)

class Person {
    constructor(private department: Department) {}

    get department_(): Department { return this.department; }
    // delegating methods removed
}

// caller: person.department_.manager
```

```java
// Java: after (delegate exposed)

public class Person {
    private final Department department;

    public Person(Department department) {
        this.department = department;
    }

    public Department getDepartment() {
        return department;
    }
    // delegating methods removed
}

// caller: person.getDepartment().getManager()
```

## 9. Known production uses

**The "Middle Man" code smell** is documented by SonarSource as a
detectable pattern. SonarQube's code smell detection identifies classes
where most methods are pure delegation, which is the pattern this
refactoring targets
([SonarSource Code Smells](https://rules.sonarsource.com/java/),
verified 2026-08-13).

**Java's `Collections.unmodifiableList`** is an example of a deliberate
middle man that is not removed, because it adds behaviour: it throws
`UnsupportedOperationException` on mutation. This is a middle man that
earns its place, not one that should be removed
([java.util.Collections documentation](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Collections.html#unmodifiableList(java.util.List)),
verified 2026-08-13).

## 10. Consequences

Positive.

- The indirection is removed, and the caller accesses the delegate
  directly.
- The class is simpler, with fewer methods that are pure forwarding.
- The caller has more control, because it can access any method on the
  delegate.

Negative.

- The client is coupled to the delegate's type, which was hidden by the
  middle man.
- The class can no longer intercept the calls, which means it cannot
  add validation, logging, or caching without re adding the delegating
  methods.

## 11. Failure modes and misuse

**Removing delegating methods that add behaviour.** A method appears to
be pure delegation but adds validation or logging. Removing it loses the
added behaviour. The symptom is missing validation or missing log
entries.

**Exposing a mutable delegate.** The delegate is mutable, and exposing it
allows the client to modify it without the class's knowledge. The symptom
is uncontrolled mutation of the delegate's state.

## 12. Trade-off matrix

| Alternative | Indirection | Coupling | When to prefer |
|---|---|---|---|
| Remove Middle Man | Reduced | Increased | Class is pure forwarder |
| Hide Delegate | Added | Reduced | Client should not know delegate |
| Inline Class | Eliminated | Increased | Class is empty after removal |
| Move Function | Changed | Changed | Method is on wrong class |

## 13. Related and incompatible patterns

**Hide Delegate** (same catalog) is the inverse. It adds a delegating
method to hide the delegate.

**Inline Class** (same catalog) is the next step when the middle man is
empty after the delegating methods are removed.

**Move Function** (same catalog) is the alternative when the method
should be on the delegate rather than being removed or forwarded.

## 14. Refactoring path in and out

**Path in.** Expose the delegate, remove delegating methods, update
callers.

**Path out.** Hide Delegate re introduces the delegating methods when
the delegate needs to be hidden again.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test that called a delegating method should call the delegate directly
and should produce the same result.

## 16. Observability signals

The refactoring does not change behaviour, so the observable signal in
production is nothing. The call stack is shorter, which is a minor trace
format change.

## 17. Security and privacy implications

The refactoring exposes the delegate, which may give the client access
to methods it should not call. This is a security consideration that
should be reviewed.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 9, "Remove Middle Man."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 7, "Remove Middle Man."
- SonarSource, "Code Smells,"
  [https://rules.sonarsource.com/java/](https://rules.sonarsource.com/java/),
  verified 2026-08-13.
- Oracle, "Collections.unmodifiableList,"
  [https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Collections.html#unmodifiableList(java.util.List)](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Collections.html#unmodifiableList(java.util.List)),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
