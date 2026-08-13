---
name: Extract Class
slug: extract-class
family: 03-refactoring
category: Refactoring
aliases: [Split Class, Extract Responsibility, Decompose Class]
first_described: "Fowler 1999"
maturity: canonical
related: [inline-class, extract-function, extract-superclass, move-function, move-field, combine-functions-into-class]
incompatible_with: []
verified: 2026-08-13
---

# Extract Class

## 1. Name, aliases, and lineage

The canonical name is **Extract Class**, introduced by Martin Fowler in
*Refactoring. Improving the Design of Existing Code*, 1st edition,
Addison-Wesley, 1999, chapter 7, "Moving Features Between Objects." The
refactoring survived into the second edition, Martin Fowler, *Refactoring.
Improving the Design of Existing Code*, 2nd edition, Addison-Wesley, 2018,
chapter 9, "Moving Features," under the same name and with the same
mechanics. Fowler groups it with Inline Class, Move Function, and Move
Field in both editions, because the four refactorings move features
between objects in different directions.

The underlying principle, that a class should have one responsibility,
is one of the oldest ideas in object oriented design. Robert C. Martin
formalised it as the Single Responsibility Principle in *Agile Software
Development. Principles, Patterns, and Practices*, Prentice Hall, 2002,
chapter 8, stating that a class should have one and only one reason to
change. Fowler's Extract Class is the mechanical path from a class that
violates the principle to a pair of classes that respect it.

The alias **Split Class** appears in the Eclipse refactoring menu. The
alias **Extract Responsibility** is used in the Ruby and Python
communities, where the focus is on extracting a responsibility rather
than a structural piece.

## 2. Problem and context

You have a class that has grown to the point where it does two things
that should be separate. The class has two groups of fields, each serving
a different responsibility, and the methods that operate on one group
have no relationship to the methods that operate on the other. A change
to one responsibility touches the class, and a change to the other
responsibility also touches the class, which means the class has two
reasons to change, which is the definition of a violation of the Single
Responsibility Principle.

The situation reads like this. A `Person` class has fields for the
person's name, email, and phone number, and it also has fields for the
person's office building, floor, and desk number. The person methods
include `getName`, `updateEmail`, and `formatPhone`, and the office
methods include `getOfficeLocation`, `moveDesk`, and `getFloorLabel`. The
two groups of fields and methods are only related because a person
happens to sit at a desk. A change to the office layout touches the
Person class, and a change to the contact information also touches the
Person class. A team that works on office layout must understand the
contact information code, and a team that works on contact information
must understand the office layout code, because both live in the same
class.

The fix is to extract a class. Move the office fields and methods into a
new `Office` class, and give `Person` a reference to an `Office` instance.
Each class has one responsibility, and a change to one does not require
touching the other.

## 3. Forces

**Cohesion versus splitting.** A class with one responsibility is
cohesive: all its fields and methods serve that one responsibility. A
class with two responsibilities has low cohesion, because the fields and
methods serve different purposes. The force favours extraction when the
cohesion cost of keeping two responsibilities in one class exceeds the
complexity cost of adding a class.

**Team topology versus class boundary.** A class that is modified by two
teams is a coordination point, and the coordination cost grows with the
frequency of changes. Extracting the class so each team owns one class
removes the coordination point. The force favours extraction when the two
responsibilities are owned by different teams, and is neutral when one
team owns both.

**Coupling versus encapsulation.** Extracting a class introduces a
reference from the original class to the extracted class, which is a new
coupling. The coupling is acceptable because it is directed and visible,
where the original class's internal coupling between two responsibilities
is invisible and harder to manage. The force favours extraction when the
directed coupling is better than the internal entanglement.

**Simplicity versus flexibility.** One class is simpler to understand
than two classes and a reference between them. Two classes are more
flexible because each can change independently. The force favours
extraction when the flexibility benefit exceeds the simplicity cost,
which happens when the two responsibilities change at different rates or
for different reasons.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- The class has two or more groups of fields and methods, each serving a
  different responsibility, and the groups are only loosely related.
- A change to one responsibility requires modifying the class, and a
  change to the other responsibility also requires modifying the class,
  which means the class has more than one reason to change.
- Two teams work on the same class, each modifying a different
  responsibility, and the coordination cost is real.
- The class is too large to understand as a unit, and the reader must
  hold too much context to navigate it.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The class has one responsibility, even if it is large. A large class
  with one responsibility should be refactored with Extract Function to
  break up its methods, not with Extract Class to split it into two
  classes.
- The two groups are tightly coupled, and extracting one would produce a
  class pair that must communicate extensively, which is worse than one
  class that does both internally.
- The class is a data transfer object with no behaviour, and the fields
  are grouped for serialisation, not for responsibility. Extracting a
  class would break the serialisation contract.
- The class is part of a public API and consumers reference its fields
  and methods directly. Extracting a class would break every consumer
  that references the moved members, which is the same breaking change as
  deleting them.

## 5. Structure

The refactoring has two participants.

- **The original class.** The class being split. After the refactoring,
  it has fewer fields and methods and a reference to the extracted class.
- **The extracted class.** The new class that receives the moved fields
  and methods. After the refactoring, it has one responsibility that was
  previously mixed into the original class.

The invariant is that every caller of the original class continues to
produce the same results. Callers that accessed the moved fields and
methods now go through the reference to the extracted class.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER
  ------                              -----

  class Person:                       class Person:
    name                                 name
    email                                email
    phone                                phone
    building                             office  (ref to Office)
    floor
    desk                              class Office:
    getName()                             building
    updateEmail()                         floor
    formatPhone()                         desk
    getOfficeLocation()                   getOfficeLocation()
    moveDesk()                            moveDesk()
    getFloorLabel()                       getFloorLabel()

  (one class, two responsibilities)   (two classes, one each)
```

## 7. Dynamics

```
  t0  identify class with two responsibilities
       |
       v
  t1  decide which fields and methods to move
       (the ones that serve the responsibility being extracted)
       |
       v
  t2  create the new class with the moved fields
       |
       v
  t3  move the methods to the new class
       (use Move Function and Move Field)
       |
       v
  t4  add a reference from the original class
       to the extracted class
       |
       v
  t5  update every caller that accessed the moved
       members directly to go through the reference
       |
       v
  t6  run test suite
       |
       v
  t7  commit. the class is split.
```

## 8. Implementation variants

**Extract with reference.** The canonical variant. The original class
holds a reference to the extracted class, and callers access the moved
members through the reference. This is the variant Fowler describes in
both editions.

**Extract with delegation.** The original class delegates calls to the
extracted class, so callers do not see the reference. A method like
`getOfficeLocation` on Person delegates to `office.getOfficeLocation`.
This variant hides the extraction from callers, which is useful when the
original class is a public API.

**Extract as value object.** The extracted class is an immutable value
object, and the original class holds an instance. This variant combines
Extract Class with the value object contract, giving both responsibility
separation and immutability. It is appropriate when the extracted
responsibility is a value, like an address or a coordinate.

**Extract as inner class.** The extracted class is a nested class of the
original, which keeps it visible only to the original and avoids polluting
the package namespace. This variant is used when the extracted class is
an implementation detail of the original and is not used by any other
class.

```python
# Python: before (one class, two responsibilities)

class Person:
    def __init__(self, name: str):
        self.name = name
        self.email = ""
        self.phone = ""
        self.building = ""
        self.floor = 0
        self.desk = ""

    def get_office_location(self) -> str:
        return f"{self.building} floor {self.floor} desk {self.desk}"

    def move_desk(self, building: str, floor: int, desk: str) -> None:
        self.building = building
        self.floor = floor
        self.desk = desk

# Python: after (extracted Office class)

class Office:
    def __init__(self, building: str = "", floor: int = 0, desk: str = ""):
        self.building = building
        self.floor = floor
        self.desk = desk

    def get_location(self) -> str:
        return f"{self.building} floor {self.floor} desk {self.desk}"

    def move(self, building: str, floor: int, desk: str) -> None:
        self.building = building
        self.floor = floor
        self.desk = desk

class Person:
    def __init__(self, name: str):
        self.name = name
        self.email = ""
        self.phone = ""
        self.office = Office()
```

```typescript
// TypeScript: after (extracted with delegation)

class Office {
    constructor(
        public building: string = "",
        public floor: number = 0,
        public desk: string = ""
    ) {}

    getLocation(): string {
        return `${this.building} floor ${this.floor} desk ${this.desk}`;
    }

    move(building: string, floor: number, desk: string): void {
        this.building = building;
        this.floor = floor;
        this.desk = desk;
    }
}

class Person {
    public email = "";
    public phone = "";
    private office = new Office();

    constructor(public name: string) {}

    getOfficeLocation(): string {
        return this.office.getLocation();
    }

    moveDesk(building: string, floor: number, desk: string): void {
        this.office.move(building, floor, desk);
    }
}
```

```java
// Java: after (extracted with reference)

public class Office {
    private String building;
    private int floor;
    private String desk;

    public Office() {
        this.building = "";
        this.floor = 0;
        this.desk = "";
    }

    public String getLocation() {
        return building + " floor " + floor + " desk " + desk;
    }

    public void move(String building, int floor, String desk) {
        this.building = building;
        this.floor = floor;
        this.desk = desk;
    }
}

public class Person {
    private String name;
    private String email;
    private String phone;
    private final Office office = new Office();

    public Person(String name) {
        this.name = name;
    }

    public String getOfficeLocation() {
        return office.getLocation();
    }

    public void moveDesk(String building, int floor, String desk) {
        office.move(building, floor, desk);
    }
}
```

## 9. Known production uses

**IntelliJ IDEA's "Extract Class" refactoring** automates the mechanical
steps by moving selected fields and methods into a new class and updating
every call site. JetBrains documents that the tool analyses the
dependencies between the moved members and the remaining members to
determine the correct interface between the two classes
([JetBrains Extract Delegate](https://www.jetbrains.com/help/idea/extract-delegate.html),
verified 2026-08-13). This is the production variant used in Java
codebases where the IDE finds every reference.

**The Java standard library's `Insets` class** is an example of a class
that was extracted from a larger rendering class. `java.awt.Insets`
holds four integer offsets (top, left, bottom, right) that were
previously part of the `Component` class. The extraction moved the
offset fields and their formatting into a separate class, which is
used by every layout manager in the AWT
([java.awt.Insets documentation](https://docs.oracle.com/en/java/javase/21/docs/api/java.desktop/java/awt/Insets.html),
verified 2026-08-13).

## 10. Consequences

Positive.

- Each class has one responsibility, which makes it easier to
  understand, test, and modify.
- A change to one responsibility does not require touching the other
  class, which reduces the risk of a change in one area breaking another.
- Two teams can work on the two classes independently, which removes the
  coordination point.
- The extracted class can be reused by other classes that need the same
  responsibility, which was not possible when the responsibility was
  embedded in the original class.

Negative.

- The reference between the two classes is a new coupling, and the two
  classes must communicate through it.
- Callers that accessed the moved members directly must now go through
  the reference, which is a mechanical change but a wide one.
- The number of classes in the codebase increases, which adds navigation
  overhead for a reader who must understand both classes.
- The extracted class may need its own tests, which is additional test
  infrastructure.

## 11. Failure modes and misuse

**Extracting a class that is never used by anyone else.** The extracted
class has one caller, the original class, and the extraction has added a
class and a reference without enabling reuse. The symptom is a class
with one field and one method that is only used by the class that
extracted it, which is over decomposition.

**Extracting too finely.** Every pair of fields is extracted into its
own class, producing a constellation of tiny classes that communicate
extensively. The symptom is a reader who must navigate through five
classes to understand one operation, which is worse than one class that
does the operation internally.

**Extracting a class that is just a data bag.** The extracted class has
fields but no methods, and the original class still operates on the
fields directly through the reference. The extraction has moved the data
but not the behaviour, which is the worst of both worlds: the class
boundary exists but the behaviour is still in the original class.

**Breaking callers of a public API.** The class is part of a public API,
and extracting members into a new class breaks every consumer that
references them. The symptom is a compile error in consumer code that is
only discovered when the consumer upgrades.

## 12. Trade-off matrix

| Alternative | Cohesion | Coupling | Class count | When to prefer |
|---|---|---|---|---|
| Extract Class | Higher, one responsibility each | Directed reference | +1 | Two responsibilities change for different reasons |
| Inline Class | Lower, merged | Internal entanglement | -1 | Two classes are always used together |
| Extract Superclass | Higher, shared parent | Inheritance | +1 | Two classes share a common responsibility |
| Combine Functions into Class | Higher, data has a home | None | +1 | Free functions share data |
| Keep one class | Lower | None | 0 | One responsibility, even if large |

## 13. Related and incompatible patterns

**Inline Class** (same catalog) is the inverse. It merges a class into
the class that uses it, which is the right move when the extracted class
is always used by exactly one caller and the extraction has not enabled
reuse or independent change.

**Extract Superclass** (same catalog) is the alternative when two
classes share a common responsibility and the shared code should be
pulled up into a parent. Extract Class splits one class into two peers;
Extract Superclass pulls shared code up into a parent.

**Move Function** and **Move Field** (same catalog) are the mechanical
steps Extract Class uses. The fields and methods are moved from the
original class to the extracted class using these refactorings.

**Combine Functions into Class** (same catalog) is the opposite
direction: it creates a class from free functions, where Extract Class
creates a class from an existing class's members.

## 14. Refactoring path in and out

**Path in.** The refactoring is introduced by creating a new class and
moving members into it. The steps are:

1. Identify the fields and methods that serve the responsibility being
   extracted.
2. Create a new class with those fields.
3. Move the methods to the new class using Move Function.
4. Add a reference from the original class to the extracted class.
5. Update every caller that accessed the moved members directly to go
   through the reference, or use delegation to hide the reference.
6. Run the test suite. Any failure means a caller was missed or a method
   was not moved correctly.
7. Consider whether the extracted class should be immutable, which
   eliminates aliasing between the original and the extracted class.

**Path out.** The refactoring is reversed by Inline Class, which merges
the extracted class back into the original. The reverse is applied when
the extracted class is always used by exactly one caller and the
extraction has not enabled reuse or independent change.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test that exercised the original class should produce the same result,
but through the reference or the delegation. A test failure means a caller
was missed or a method was not moved correctly.

New tests should test the extracted class in isolation, verifying its
fields and methods produce the expected results without the original
class. These tests are more granular than the original tests and produce
better failure messages.

A test that checks the reference between the two classes should verify
that the original class has a valid reference to the extracted class after
construction, which guards against a null reference.

## 16. Observability signals

The refactoring does not change behaviour, so the observable signal in
production is nothing. The one observable difference is in the class
names that appear in logs and traces: the extracted class's methods
appear where the original class's methods used to appear. This is expected
and is actually an observability improvement, because the traces now show
which responsibility is being exercised.

## 17. Security and privacy implications

The refactoring improves security when the two responsibilities have
different access levels, for example when one responsibility handles
sensitive data and the other does not. The extracted class can have
its own access control, so callers that only need the non sensitive
responsibility do not get access to the sensitive class.

The privacy relevant case is that the extracted class can be omitted
from serialisation, so the sensitive fields are not serialised when the
original class is serialised. This is a positive privacy signal when the
extracted class contains personally identifiable information.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 9, "Extract Class."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 7, "Extract Class."
- Robert C. Martin, *Agile Software Development. Principles, Patterns,
  and Practices*, Prentice Hall, 2002, chapter 8, "The Single
  Responsibility Principle."
- JetBrains, "Extract Delegate,"
  [https://www.jetbrains.com/help/idea/extract-delegate.html](https://www.jetbrains.com/help/idea/extract-delegate.html),
  verified 2026-08-13.
- Oracle, "java.awt.Insets," Java SE 21 API documentation,
  [https://docs.oracle.com/en/java/javase/21/docs/api/java.desktop/java/awt/Insets.html](https://docs.oracle.com/en/java/javase/21/docs/api/java.desktop/java/awt/Insets.html),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
