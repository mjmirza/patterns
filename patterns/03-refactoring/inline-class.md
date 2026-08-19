---
name: Inline Class
slug: inline-class
family: 03-refactoring
category: Refactoring
aliases: [Merge Class, Collapse Class, Absorb Class]
first_described: "Fowler 1999"
maturity: canonical
related: [extract-class, move-function, move-field, hide-delegate, inline-function, replace-delegation-with-inheritance]
incompatible_with: []
verified: 2026-08-13
---

# Inline Class

## 1. Name, aliases, and lineage

The canonical name is **Inline Class**, introduced by Martin Fowler in
*Refactoring. Improving the Design of Existing Code*, 1st edition,
Addison-Wesley, 1999, chapter 7, "Moving Features Between Objects." The
refactoring survived into the second edition, Martin Fowler, *Refactoring.
Improving the Design of Existing Code*, 2nd edition, Addison-Wesley, 2018,
chapter 9, "Moving Features," under the same name and with the same
mechanics. Fowler groups it with Extract Class as the inverse pair: one
adds a class, the other removes one.

The underlying idea, that a class that has been so depleted by other
refactorings that it no longer earns its place should be merged into the
class that uses it, is the other side of the Single Responsibility
Principle. Robert C. Martin, in *Agile Software Development. Principles,
Patterns, and Practices*, Prentice Hall, 2002, chapter 8, notes that a
class can be too small as well as too large, and that a class with no
responsibility of its own should be removed. Fowler's Inline Class is the
mechanical path from a class with no independent reason to exist to a
codebase with one fewer class.

The alias **Merge Class** appears in the Eclipse refactoring menu. The
alias **Absorb Class** is used in the JavaScript and TypeScript
communities, where modules and classes are interchangeable and the merge
is expressed as a module consolidation.

## 2. Problem and context

You have a class that no longer earns its place. Its fields and methods
have been moved elsewhere through previous refactorings, or it was created
speculatively for a responsibility that never materialised, or its
responsibility has been absorbed by another class that now does everything
the inline class did. The class has few fields, few methods, and few
callers, and it adds a class, a file, and a level of navigation to the
codebase without adding any value.

The situation reads like this. A `PhoneNumber` class was created to hold
a phone number's area code, exchange, and subscriber number, with methods
to format and validate. Over time, the validation moved to a validator,
the formatting moved to a formatter, and the fields were replaced by a
single string. The class now has one field (the raw string) and one
method (a getter), and it is called from exactly one place: the `Person`
class that holds a `PhoneNumber` field. The `PhoneNumber` class is a
wrapper around a string that adds a class boundary without adding any
behaviour. Every reader who encounters it must navigate to it, read its
one method, and conclude that it does nothing the string does not already
do.

The fix is to inline the class. Move the `PhoneNumber` class's field and
method into `Person`, delete the `PhoneNumber` class, and replace every
reference to `PhoneNumber` with the direct type (a string, in this case)
or with the field on `Person`.

## 3. Forces

**Simplicity versus modularity.** Fewer classes is simpler: less
navigation, less boilerplate, fewer files. More classes is modular: each
class has a clear boundary, and changes are localised. The force favours
inlining when the class is not earning its modularity, because the
simplicity benefit exceeds the modularity cost.

**Coupling versus indirection.** A class boundary provides a boundary
between the class and its users, which reduces coupling if the class has
real behaviour. If the class is a pass through, the boundary is just
indirection, and the coupling is still there, just hidden behind a
delegating call. The force favours inlining when the class provides no
real boundary, only indirection.

**Reuse versus focus.** A separate class can be reused by multiple callers.
An inlined class's behaviour is embedded in the caller and cannot be
reused without extracting it again. The force favours keeping the class
when it is reused by multiple callers, and favours inlining when it has
one caller.

**Future extension versus present simplicity.** A class that is empty today
might be needed tomorrow. Inlining removes the class, and a future need
requires Extract Class to re create it. The force favours keeping the
class as a speculative investment when the future need is likely, and
favouring inlining when the future need is speculative.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- The class has few fields and few methods, and it does not have a
  responsibility that justifies a separate class boundary.
- The class has one caller, and the caller already does everything the
  class does, so the class is a wrapper that adds indirection without
  adding behaviour.
- The class was created speculatively for a responsibility that never
  materialised, and it has been empty or nearly empty since.
- Previous refactorings have moved the class's behaviour elsewhere, and
  what remains is a shell with no independent reason to exist.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The class has a real responsibility that is different from the caller's
  responsibility. Inlining would merge two responsibilities into one class,
  which violates the Single Responsibility Principle.
- The class is reused by multiple callers. Inlining into one caller
  would force the other callers to duplicate the behaviour or to
  reference the caller's class, which is worse than keeping the shared
  class.
- The class is part of a public API and consumers reference it by name.
  Inlining it would break every consumer that references the class name,
  which is the same breaking change as deleting a public type.
- The class provides a type that the type system uses, for example a
  value object that distinguishes a `UserId` from a bare `String`. Inlining
  would lose the type distinction, which is a safety loss.

## 5. Structure

The refactoring has two participants.

- **The inline class.** The class being merged into its caller. After the
  refactoring, this class no longer exists.
- **The receiving class.** The class that absorbs the inline class's
  fields and methods. After the refactoring, it has the inline class's
  members.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER
  ------                              -----

  Person:                             Person:
    name                                name
    phone: PhoneNumber                  phone: str  (absorbed)
                                      getPhone(): str  (absorbed)
  PhoneNumber:                      (PhoneNumber class deleted)
    phone: str
    getPhone(): str

  caller:                             caller:
    person.phone.getPhone()            person.getPhone()
```

## 7. Dynamics

```
  t0  identify class with no independent responsibility
       |
       v
  t1  move fields from the inline class
       to the receiving class (Move Field)
       |
       v
  t2  move methods from the inline class
       to the receiving class (Move Function)
       |
       v
  t3  update every caller that referenced
       the inline class to reference the
       receiving class's members directly
       |
       v
  t4  delete the inline class
       |
       v
  t5  run test suite
       |
       v
  t6  commit. the class is inlined.
```

## 8. Implementation variants

**Full inline into the receiving class.** The canonical variant. Every
field and method is moved to the receiving class, the inline class is
deleted, and callers use the receiving class's members.

**Inline into the type system.** When the inline class is a wrapper around
a primitive, the fields and methods are absorbed, and the primitive type
replaces the class at every reference. This variant is the one used for
the PhoneNumber example, where the class is replaced by a string.

**Inline via delegation removal.** When the receiving class delegates to
the inline class, the delegation is removed and the behaviour is
implemented directly on the receiving class. This variant is the inverse
of Hide Delegate.

```python
# Python: before (PhoneNumber class with one field and one method)

class PhoneNumber:
    def __init__(self, raw: str):
        self._raw = raw

    def get_raw(self) -> str:
        return self._raw

class PersonBefore:
    def __init__(self, name: str, phone: PhoneNumber):
        self.name = name
        self.phone = phone

    def get_phone(self) -> str:
        return self.phone.get_raw()

# Python: after (PhoneNumber inlined into Person)

class Person:
    def __init__(self, name: str, phone: str):
        self.name = name
        self._phone = phone

    def get_phone(self) -> str:
        return self._phone
```

```typescript
// TypeScript: before (PhoneNumber class)

class PhoneNumber {
    constructor(private readonly raw: string) {}

    get value(): string { return this.raw; }
}

class PersonBefore {
    constructor(
        public name: string,
        private phone: PhoneNumber
    ) {}

    get phoneNumber(): string {
        return this.phone.value;
    }
}

// TypeScript: after (inlined)

class Person {
    constructor(
        public name: string,
        private _phone: string
    ) {}

    get phoneNumber(): string {
        return this._phone;
    }
}
```

```java
// Java: after (inlined, PhoneNumber deleted)

public class Person {
    private String name;
    private String phone;

    public Person(String name, String phone) {
        this.name = name;
        this.phone = phone;
    }

    public String getPhone() {
        return phone;
    }

    public void setPhone(String phone) {
        this.phone = phone;
    }
}
// PhoneNumber class is deleted
```

## 9. Known production uses

**IntelliJ IDEA's Inline refactoring family** automates the manual steps of
this pattern one member at a time. inlining a field, a method, or a
constructor folds that member's usages into its caller and removes the
original declaration, which is the same move-then-delete mechanic applied
across every member of a class being inlined
([JetBrains Inline documentation](https://www.jetbrains.com/help/idea/inline.html),
verified 2026-08-19).

**Python's standard library inlined the `UserString` class's role** when
the `str` type gained the methods that `UserString` previously provided
as a wrapper. In Python 3, `UserString` remains for backward
compatibility, but the documentation notes that most use cases are now
served directly by the `str` type
([collections.UserString documentation](https://docs.python.org/3/library/collections.html#collections.UserString),
verified 2026-08-13). This is the refactoring applied to the standard
library: the wrapper was inlined into the type it wrapped.

## 10. Consequences

Positive.

- The codebase has one fewer class to read, maintain, and navigate.
- The indirection of the wrapper is removed, so a reader can see the
  behaviour directly on the receiving class.
- The boilerplate of constructing and managing the inline class is
  removed from every call site.

Negative.

- The receiving class is larger, which may push it toward violating the
  Single Responsibility Principle.
- If the inlined class is needed again later, Extract Class must re
  create it, which is more work than keeping the class.
- If the inlined class was reused by other callers, those callers must
  now duplicate the behaviour or reference the receiving class, which is
  a coupling increase.

## 11. Failure modes and misuse

**Inlining a class with a real responsibility.** The class has a
responsibility that is different from the receiver's, and inlining
merges two responsibilities into one class. The symptom is a class that
now does two things, which is the violation the refactoring was supposed
to prevent (in the opposite direction).

**Inlining a class that is reused.** The class is called from multiple
places, and inlining into one caller forces the other callers to
duplicate or to reference the receiving class, which is worse. The
symptom is duplicated code in the other callers.

**Inlining a public API class.** The class is part of a published API,
and inlining breaks every consumer that references the class name. The
symptom is a compile error in consumer code.

**Inlining too aggressively.** Every helper class is inlined into its
caller, producing large classes with many responsibilities. The symptom
is a class that is a god class, which is the opposite problem the
refactoring was supposed to solve.

## 12. Trade-off matrix

| Alternative | Class count | Indirection | When to prefer |
|---|---|---|---|
| Inline Class | -1 | Removed | Class has no responsibility, one caller |
| Extract Class | +1 | Added | Class has two responsibilities |
| Hide Delegate | 0 | Added | Client should not know about delegate |
| Move Function | 0 | Changed | Method is on wrong class |

## 13. Related and incompatible patterns

**Extract Class** (same catalog) is the inverse. It splits a class into
two, where Inline Class merges two into one. The two are the opposite
directions of class boundary manipulation.

**Move Function** and **Move Field** (same catalog) are the mechanical
steps Inline Class uses to move members from the inline class to the
receiving class.

**Hide Delegate** (same catalog) adds a delegating method that hides the
delegate, where Inline Class removes the delegate entirely. The two are
related but operate at different levels: Hide Delegate keeps both classes
and adds a method, Inline Class removes one class.

**Replace Delegation with Inheritance** (same catalog) is the alternative
when the receiving class delegates everything to the inline class and the
relationship is an is a. Inheritance removes the delegation but keeps the
class, where inlining removes the class.

## 14. Refactoring path in and out

**Path in.** The refactoring is introduced by moving every member from
the inline class to the receiving class. The steps are:

1. Move every field from the inline class to the receiving class (Move
   Field).
2. Move every method from the inline class to the receiving class (Move
   Function).
3. Update every caller that referenced the inline class to reference the
   receiving class's members.
4. Delete the inline class.
5. Run the test suite. Any failure means a member was not moved or a
   caller was missed.

**Path out.** The refactoring is reversed by Extract Class, which splits
the receiving class to re create the boundary. The reverse is applied
when the receiving class has grown too large or when the inlined
behaviour deserves its own class again.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test that exercised the inline class's members should now exercise them
through the receiving class and should produce the same result.

A grep for the inline class name after the refactoring should return zero
results in the source. Hits in documentation and commit messages are
expected and are not failures, but should be reviewed for accuracy.

## 16. Observability signals

The refactoring does not change behaviour, so the observable signal in
production is nothing. The one observable difference is in class names
that appear in logs and traces: the inline class's name disappears, and
the receiving class's name appears where it used to. This is expected.

## 17. Security and privacy implications

The refactoring does not change what data is stored or how it is
accessed, so it does not change the security surface. The security
relevant case is when the inlined class provided a type guard that
distinguished one kind of string from another, for example a
`SanitizedInput` class vs a raw `String`. Inlining loses the type
distinction, which weakens the type system's enforcement of the security
boundary. This is a security relevant change that should be reviewed.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 9, "Inline Class."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 7, "Inline Class."
- Robert C. Martin, *Agile Software Development. Principles, Patterns,
  and Practices*, Prentice Hall, 2002, chapter 8.
- JetBrains, "Inline,"
  [https://www.jetbrains.com/help/idea/inline.html](https://www.jetbrains.com/help/idea/inline.html),
  verified 2026-08-19.
- Python Software Foundation, "collections.UserString,"
  [https://docs.python.org/3/library/collections.html#collections.UserString](https://docs.python.org/3/library/collections.html#collections.UserString),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
