---
name: Encapsulate Collection
slug: encapsulate-collection
family: 03-refactoring
category: Refactoring
aliases: [Wrap Collection, Encapsulate List, Return Read-Only Collection]
first_described: "Fowler 2002"
maturity: canonical
related: [encapsulate-record, encapsulate-variable, extract-class, change-reference-to-value, replace-record-with-data-class]
incompatible_with: []
verified: 2026-08-13
---

# Encapsulate Collection

## 1. Name, aliases, and lineage

The canonical name is **Encapsulate Collection**, introduced by Martin
Fowler in *Refactoring. Improving the Design of Existing Code*, 1st
edition, Addison-Wesley, 1999, chapter 8, "Organizing Data." The
refactoring underwent a significant revision between editions. In the
first edition, Fowler recommended returning a copy of the collection to
callers and modifying through accessor methods. In the second edition,
Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
edition, Addison-Wesley, 2018, chapter 8, "Encapsulating Data," Fowler
changed the recommendation to return an unmodifiable view and to provide
add and remove methods on the enclosing class, because the copy on read
approach produced unnecessary allocation and the view approach
communicated the immutability intent at the type level.

The underlying problem, that a collection exposed as a public field or
returned directly from a getter allows any caller to mutate the
collection's structure, is one of the oldest encapsulation issues in
object oriented design. Joshua Bloch addresses it in *Effective Java*,
1st edition, Addison-Wesley, 2001, item 15, "Minimize mutability," and
item 24, "Favour static member classes over nonstatic." Bloch's advice
in the second edition, *Effective Java*, 3rd edition, 2018, item 16, is
to return an unmodifiable view of the collection rather than a copy.

The alias **Wrap Collection** appears in the JavaScript and TypeScript
communities, where the collection is typically an array and the wrapper
provides methods that control mutation. The alias **Encapsulate List**
is the C sharp and Java community's preferred label when the collection
is specifically a list rather than a map or set.

## 2. Problem and context

A class has a collection field, typically a list or a map, that is exposed
to callers. The exposure may be a public field, or it may be a getter
that returns the collection directly. Either way, any caller can add,
remove, or replace elements in the collection without going through the
owning class, which means the owning class cannot enforce invariants on
the collection's contents, cannot log changes, and cannot prevent the
collection from being emptied or filled with invalid entries.

The situation reads like this. A `Course` class has a `List<Student>
attendees` field with a public getter that returns the list directly.
The course has an invariant that the number of attendees cannot exceed
the room capacity, and the enrol method checks this invariant before
adding a student. But because the getter returns the raw list, a caller
can do `course.getAttendees().add(student)` and bypass the capacity
check entirely. The invariant exists in the enrol method, but the
collection exposure makes it unenforceable. A caller that empties the
list via `course.getAttendees().clear()` removes every attendee without
the course knowing, which may break billing, reporting, or room
assignment logic that depends on the attendee count.

The fix is to encapsulate the collection. The field becomes private, the
getter returns an unmodifiable view, and the class provides add and
remove methods that enforce the invariants. Callers can read the
collection but cannot mutate it without going through the owning class's
methods.

## 3. Forces

**Encapsulation versus convenience.** A raw collection is convenient for
callers: they can call any list method directly. An encapsulated
collection requires callers to use the owning class's add and remove
methods, which is more ceremony but gives the class control. The force
favours encapsulation when the class needs to enforce invariants, and
favours raw access when the collection is truly a passive data holder
with no invariants to enforce.

**Allocation versus safety.** The copy on read approach returns a new
list every time, which is safe but allocates. The view approach returns a
wrapper that prevents modification without allocating a copy. The force
favours the view for read heavy access patterns and the copy for cases
where the caller needs to iterate without concurrent modification risk.

**Immutability versus flexibility.** An unmodifiable view prevents all
mutation, which is safe but may be too restrictive for callers that
legitimately need to modify the collection. The add and remove methods on
the owning class provide controlled mutation, which is the right balance
for most cases. The force favours full immutability when the collection
should never change after construction, and controlled mutation when the
collection changes but under the class's authority.

**Type safety versus encapsulation.** A raw collection exposes its type,
for example `List<Student>`, to the caller, which gives compile time type
safety but also gives access to every method on the type. An encapsulated
collection can hide the concrete type and expose only the operations the
class wants to allow, which is stronger encapsulation but weaker type
information for the caller.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- The collection is exposed to callers, either as a public field or
  through a getter that returns the raw collection, and callers can mutate
  it directly.
- The owning class has invariants on the collection's contents, for
  example a capacity limit, a type restriction, or a consistency check
  with another field, and the direct exposure makes the invariants
  unenforceable.
- The collection is modified by callers in ways the owning class does not
  know about, and the class's state becomes inconsistent because it is not
  notified of changes.
- The owning class needs to log, audit, or react to changes in the
  collection, and the direct exposure prevents it from intercepting the
  changes.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The collection is a passive data holder with no invariants to enforce.
  A data transfer object that carries a list from one layer to another
  has no reason to encapsulate, because no class depends on the
  collection's contents being in a specific state.
- The collection is immutable after construction and the class already
  returns an immutable type, for example a tuple in Python or an
  immutable array in Rust. The encapsulation is already enforced by the
  type system, and the refactoring adds ceremony without benefit.
- The collection is used only internally by the owning class and is never
  exposed to callers. There is no exposure to encapsulate.
- The performance cost of the view or the copy is unacceptable for the
  access pattern, and the class is in a hot path where the allocation or
  the wrapper overhead dominates.

## 5. Structure

The refactoring has one participant.

- **The collection.** The list, map, set, or array that is being
  encapsulated. Before the refactoring, it is exposed directly. After
  the refactoring, it is private, the getter returns an unmodifiable
  view, and the class provides add and remove methods.

The invariant is that every caller that previously mutated the
collection directly now goes through the owning class's methods, and the
class enforces its invariants in those methods.

## 6. ASCII structure diagram

```
  BEFORE                                  AFTER
  ------                                  -----

  class Course:                          class Course:
    attendees: List<Student>               _attendees: List<Student>  (private)
                                           MAX = 30
    getAttendees(): List<Student>
      return attendees                    getAttendees(): List<Student>
                                             return unmodifiable(_attendees)
  caller:
    course.getAttendees().add(s)          enroll(student):
      // bypasses capacity check             if len(_attendees) >= MAX:
                                                 raise FullError
                                             _attendees.add(student)

                                         cancel(student):
                                             _attendees.remove(student)

                                         caller:
                                             course.enroll(s)  // checked
```

## 7. Dynamics

```
  t0  identify exposed collection field
       |
       v
  t1  make the field private
       (rename if needed to signal the change)
       |
       v
  t2  change the getter to return
       an unmodifiable view
       |
       v
  t3  add add/remove methods on the owning class
       that enforce invariants
       |
       v
  t4  update every caller that mutated
       the collection directly to use
       the new methods
       |
       v
  t5  run test suite
       -- callers that used add() now use enroll()
       -- callers that used clear() now use cancelAll()
       |
       v
  t6  commit. the collection is encapsulated.
```

## 8. Implementation variants

**Unmodifiable view.** The canonical variant in the second edition. The
getter returns an unmodifiable view of the backing collection, which
throws `UnsupportedOperationException` on any mutation attempt. This is
the approach `Collections.unmodifiableList` provides in Java and
`MappingProxyType` provides in Python.

**Copy on read.** The first edition's recommendation. The getter returns a
copy of the collection, so callers can mutate the copy without affecting
the original. This is safe but allocates on every read, and it hides the
immutability intent because the copy is mutable.

**Immutable wrapper type.** The class returns a different type that wraps
the collection and provides only read methods. This is the approach
Kotlin's `List` (read only interface) vs `MutableList` takes, and it is
the approach C sharp's `IReadOnlyList` vs `IList` takes.

**Custom collection class.** The owning class returns a custom collection
type that delegates reads to the backing collection and throws or logs on
writes. This is the heaviest variant and is used when the class needs to
intercept every read and write, not just prevent mutation.

```python
# Python: before (exposed list)

class Course:
    def __init__(self, name: str):
        self.name = name
        self.attendees: list[str] = []

# Python: after (encapsulated with view)

from types import MappingProxyType

class Course:
    MAX = 30

    def __init__(self, name: str):
        self.name = name
        self._attendees: list[str] = []

    @property
    def attendees(self) -> tuple[str, ...]:
        return tuple(self._attendees)

    def enroll(self, student: str) -> None:
        if len(self._attendees) >= self.MAX:
            raise ValueError("course is full")
        self._attendees.append(student)

    def cancel(self, student: str) -> None:
        self._attendees.remove(student)
```

```typescript
// TypeScript: before (exposed array)

class CourseBefore {
    attendees: string[] = [];
}

// TypeScript: after (encapsulated with ReadonlyArray)

class Course {
    static readonly MAX = 30;
    private _attendees: string[] = [];

    get attendees(): readonly string[] {
        return this._attendees;
    }

    enroll(student: string): void {
        if (this._attendees.length >= Course.MAX) {
            throw new Error("course is full");
        }
        this._attendees.push(student);
    }

    cancel(student: string): void {
        const idx = this._attendees.indexOf(student);
        if (idx >= 0) this._attendees.splice(idx, 1);
    }
}
```

```java
// Java: after (encapsulated with unmodifiable view)

import java.util.*;

public class Course {
    public static final int MAX = 30;
    private final List<String> attendees = new ArrayList<>();

    public List<String> getAttendees() {
        return Collections.unmodifiableList(attendees);
    }

    public void enroll(String student) {
        if (attendees.size() >= MAX) {
            throw new IllegalStateException("course is full");
        }
        attendees.add(student);
    }

    public void cancel(String student) {
        attendees.remove(student);
    }
}
```

## 9. Known production uses

**Java's `Collections.unmodifiableList` and related methods** are the
standard library implementation of the unmodifiable view variant. The
method documentation states that the returned list throws
`UnsupportedOperationException` on any mutation attempt and that changes
to the backing list are reflected in the view
([java.util.Collections documentation](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Collections.html#unmodifiableList(java.util.List)),
verified 2026-08-13). This is the mechanism Fowler recommends in the
second edition and the one used by production Java codebases.

**Kotlin's read only collection interfaces** implement the immutable
wrapper type variant at the language level. Kotlin distinguishes
`List<E>` (read only) from `MutableList<E>` (read write), and the
standard library's `toList()` method returns a read only view. The Kotlin
documentation states that a `List` is read only and that mutation
methods are available only on `MutableList`
([Kotlin Collections documentation](https://kotlinlang.org/docs/collections-overview.html#collection-types),
verified 2026-08-13).

## 10. Consequences

Positive.

- The owning class controls every mutation of the collection, which
  allows it to enforce invariants, log changes, and maintain consistency
  with other fields.
- The collection's internal representation can change without affecting
  callers, because they interact through methods, not through the raw
  collection.
- The type system communicates the immutability intent: a read only
  return type tells the caller at compile time that the collection cannot
  be mutated through this reference.
- Concurrent modification risk is reduced, because the view prevents
  structural modification during iteration.

Negative.

- Callers that previously mutated the collection directly must now use
  the owning class's methods, which is a mechanical change but a wide one
  if the collection is widely used.
- The view or copy adds a layer of indirection, which has a small
  performance cost on every read.
- The unmodifiable view throws at runtime rather than failing at compile
  time, unless the language has read only collection types like Kotlin or
  C sharp.
- A caller that needs to modify the collection must call the owning
  class's methods, which may have more parameters or different semantics
  than the raw collection's add and remove.

## 11. Failure modes and misuse

**View that leaks the backing collection.** The getter returns an
unmodifiable view, but the view delegates to the backing collection, so
changes to the backing collection are visible through the view. A caller
that holds the view and iterates it while another thread modifies the
backing collection gets a `ConcurrentModificationException`. The symptom
is an exception during iteration that is caused by a mutation the caller
did not make, which is confusing.

**Copy that is mutable.** The getter returns a copy of the collection,
but the copy is a mutable list, so the caller can mutate it. The caller
believes the mutation is reflected in the original, but it is not,
because the copy is independent. The symptom is a silent logic error
where the caller's changes are lost.

**Encapsulation without invariant enforcement.** The collection is
encapsulated, and the add and remove methods are provided, but the
methods do not check any invariants. The encapsulation adds ceremony
without benefit, because the class does not use the control it gained.
The symptom is a class with private collection, view getter, and add and
remove methods that are thin wrappers around the collection's own
methods, with no validation or logging.

**Over encapsulation.** The collection is a passive data holder with no
invariants, but the refactoring is applied anyway, adding a view getter
and add and remove methods that the class does not need. The symptom is a
class that is all ceremony and no substance, where every access to the
collection goes through a method that does nothing but delegate.

## 12. Trade-off matrix

| Alternative | Mutation control | Allocation | Type safety | When to prefer |
|---|---|---|---|---|
| Encapsulate Collection (view) | Full, via methods | None on read | Runtime check | Class needs to enforce invariants |
| Encapsulate Collection (copy) | Full, via methods | One copy per read | Runtime check | Caller needs a snapshot for safe iteration |
| Immutable wrapper type | Full, via type | None on read | Compile time | Language has read only collection types |
| Encapsulate Record | Full, via class | Depends | Depends | Data is a record, not just a collection |
| Keep raw collection | None | None | Full at type level | Collection is a passive data holder |

## 13. Related and incompatible patterns

**Encapsulate Record** (same catalog) wraps a data record in a class,
which is the same operation as Encapsulate Collection when the record
contains a collection. The two are complementary: Encapsulate Record
gives the record a class boundary, and Encapsulate Collection gives the
collection inside the record controlled access.

**Encapsulate Variable** (same catalog) wraps a mutable variable in
accessor methods, which is the scalar analogue of Encapsulate
Collection. The collection variant is harder because collections have
internal structure that a scalar does not.

**Change Reference to Value** (same catalog) is related when the
collection contains value objects. Making the elements value objects
prevents aliasing within the collection, and encapsulating the collection
prevents external mutation. The two are frequently applied together.

**Extract Class** (same catalog) is the alternative when the collection
and its invariants are complex enough to deserve their own class. Rather
than encapsulating the collection in the existing class, extract a new
class that owns the collection and its invariants.

## 14. Refactoring path in and out

**Path in.** The refactoring is introduced by making the collection
private, returning a view from the getter, and providing add and remove
methods. The steps are:

1. Make the collection field private. Rename it if the old name was
   public and callers accessed it directly.
2. Change the getter to return an unmodifiable view of the collection.
3. Add add and remove methods on the owning class that enforce the
   invariants.
4. Update every caller that mutated the collection directly to use the
   new methods.
5. Run the test suite. Any failure means a caller was missed or an
   invariant check is wrong.
6. Consider whether the collection should be returned as a copy instead
   of a view, if concurrent modification is a concern.

**Path out.** The refactoring is reversed by making the collection public
again and removing the add and remove methods. The reverse is applied
when the encapsulation is providing no benefit, for example when the
class has no invariants to enforce and the collection is a passive data
holder.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test that exercised the collection should produce the same result, but
through the new methods instead of direct mutation. A test failure means
a caller was missed or an invariant check is too strict.

A new test should verify that the view rejects mutation. Attempt to add
or remove an element through the view and verify that the attempt throws
the expected exception. This test guards against a future change that
returns the raw collection from the getter.

A test should verify the invariants. Enrol a student that exceeds the
capacity and verify that the enrol method rejects it. Cancel a student
that is not enrolled and verify the behaviour, whether it is a no op or
an error.

## 16. Observability signals

The refactoring does not change behaviour, so the observable signal in
production is nothing. If production observability changes, the
refactoring introduced a behaviour change, and the difference is the
signal that an invariant check is too strict or a caller was missed.

The one observable difference is in exception patterns. If callers were
mutating the collection in ways the owning class did not know about, and
the new methods reject those mutations, the caller will see exceptions
it did not see before. These exceptions are the signal that the caller
was relying on uncontrolled mutation, and the fix is to update the
caller to use the methods, not to relax the encapsulation.

## 17. Security and privacy implications

The refactoring improves security in one specific way: the owning class
can now validate every element added to the collection, which prevents a
caller from injecting an invalid or malicious entry. This is a positive
security signal when the collection contents are security relevant, for
example a list of permitted origins or a set of authorised users.

The privacy relevant case is that the encapsulation prevents a caller
from emptying the collection, which may contain data that should not be
deleted, for example an audit trail or a consent record. The add and
remove methods can enforce that only authorised callers can remove
entries, which is a positive privacy signal.

Where the refactoring is silent is in the data itself: the collection
contains the same elements, and the refactoring does not change what data
is stored or how it is accessed. The security and privacy benefit comes
from the control, not from the data.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 8, "Encapsulate Collection."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 8, "Encapsulate Collection."
- Joshua Bloch, *Effective Java*, 3rd edition, Addison-Wesley, 2018,
  item 16, "Favour composition over inheritance."
- Oracle, "Collections.unmodifiableList," Java SE 21 API documentation,
  [https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Collections.html#unmodifiableList(java.util.List)](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Collections.html#unmodifiableList(java.util.List)),
  verified 2026-08-13.
- Kotlin, "Collections overview,"
  [https://kotlinlang.org/docs/collections-overview.html#collection-types](https://kotlinlang.org/docs/collections-overview.html#collection-types),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
