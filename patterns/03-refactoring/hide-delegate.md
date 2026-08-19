---
name: Hide Delegate
slug: hide-delegate
family: 03-refactoring
category: Refactoring
aliases: [Encapsulate Delegate, Law of Demeter Fix, Add Delegating Method]
first_described: "Fowler 1999"
maturity: canonical
related: [remove-middle-man, extract-class, move-function, replace-delegation-with-inheritance, encapsulate-record]
incompatible_with: []
verified: 2026-08-13
---

# Hide Delegate

## 1. Name, aliases, and lineage

The canonical name is **Hide Delegate**, introduced by Martin Fowler in
*Refactoring. Improving the Design of Existing Code*, 1st edition,
Addison-Wesley, 1999, chapter 7, "Moving Features Between Objects." The
refactoring survived into the second edition, Martin Fowler, *Refactoring.
Improving the Design of Existing Code*, 2nd edition, Addison-Wesley, 2018,
chapter 9, "Moving Features," under the same name and with the same
mechanics. Fowler groups it with Remove Middle Man, Move Function, and
Move Field, because the four refactorings move features between objects
and the choice depends on the direction of the move.

The underlying principle, that a client should not reach through an object
to get to another object, is known as the **Law of Demeter**, introduced
by Ian Holland at Northeastern University in 1987 and popularised by Karl
Lieberherr in *Demeter. Object-Oriented AOP*, 1989. The law states that a
method should only call methods on itself, its parameters, objects it
creates, and its direct fields, not on objects returned by those fields.
Fowler's Hide Delegate is the mechanical path from a violation of the law
to compliance.

The alias **Law of Demeter Fix** is used in the aspect oriented programming
community, where the law is enforced by aspects. The alias **Add Delegating
Method** is used in the Eclipse refactoring menu, where the operation is
offered as a quick fix for a chain of accessor calls.

## 2. Problem and context

A client calls a method on an object it reaches through another object,
forming a chain of access. The client calls `person.getDepartment().getManager()`
to get the manager of the department that the person belongs to. The
client knows about the Department class and its getManager method, which
means the client is coupled to Department's interface, not just to
Person's. If Department changes its getManager method, the client breaks,
even though the client only wanted to talk to Person. The chain of access
couples the client to every class in the chain.

The situation reads like this. A reporting module needs to find the
manager of a department for each employee. It calls
`employee.getDepartment().getManager().getName()`, a three link chain.
The reporting module knows about Employee, Department, and Person (the
manager), and it depends on the interfaces of all three. A change to
Department's getManager return type, or to Person's getName method, breaks
the reporting module. The reporting module should only need to talk to
Employee, because Employee is the object it has.

The fix is to hide the delegate. Add a method on Employee that delegates
to Department's getManager, so the client calls
`employee.getManager()` instead of
`employee.getDepartment().getManager()`. The client no longer knows about
Department, and a change to Department's interface does not affect the
client.

## 3. Forces

**Coupling versus delegation burden.** Hiding the delegate reduces the
client's coupling to one class, but adds a delegating method to the
server class, which is now responsible for forwarding the call. The force
favours hiding when the coupling cost exceeds the delegation burden,
which happens when the delegate's interface changes frequently or when the
client should not know about the delegate.

**Encapsulation versus transparency.** Hiding the delegate encapsulates
the delegate behind the server, so the client does not know the delegate
exists. Exposing the delegate lets the client access it directly, which is
transparent but couples the client. The force favours hiding when the
delegate is an implementation detail that should not be visible.

**Law of Demeter versus flexibility.** The Law of Demeter says a client
should not reach through a chain of access. Following the law strictly
produces many delegating methods, which is a maintenance burden. The force
favours hiding when the chain is long or when the delegate's interface is
unstable, and favours reaching when the chain is one link and the delegate
is a stable public interface.

**Middle man versus direct access.** If every method on the delegate is
forwarded, the server becomes a middle man that adds no value, and the
refactoring has produced a class full of delegating methods that are pure
forwarding. The force favours hiding a few key methods, not all of them,
and is reversed by Remove Middle Man when the server has become a pure
forwarder.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- A client calls a method on an object it reaches through another object,
  forming a chain of access that couples the client to every class in the
  chain.
- The delegate is an implementation detail that the client should not know
  about, because the delegate's type or interface may change.
- The chain is two or more links, which is the point at which the Law of
  Demeter is violated and the coupling becomes a real problem.
- The delegating method has a clear name that communicates the intent
  without referencing the delegate, for example `getManager` instead of
  `getDepartmentManager`.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The chain is one link, for example `person.getDepartment()`, and the
  delegate is a stable public interface that the client legitimately
  needs to access directly. The Law of Demeter allows one link, and hiding
  it would add a delegating method without reducing coupling.
- The server is already a middle man, with most of its methods forwarding
  to the delegate. Adding more delegating methods makes the middle man
  worse, and the correct refactoring is Remove Middle Man, not Hide
  Delegate.
- The delegate is a collection, and the client needs to iterate or modify
  it. Hiding the collection behind a delegating method would require
  forwarding every collection operation, which is Encapsulate Collection,
  not Hide Delegate.
- The delegate is a different module or service that the client should be
  aware of, for example a data access object or a repository. Hiding it
  would obscure the architecture's layering, which is the wrong kind of
  encapsulation.

## 5. Structure

The refactoring has two participants.

- **The server.** The object the client has. After the refactoring, it
  has a delegating method that forwards to the delegate.
- **The delegate.** The object the client reaches through the server.
  After the refactoring, the client no longer accesses it directly.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER
  ------                              -----

  client --getDepartment()--> Person   client --getManager()--> Person
           getManager()------> Dept              |
                                                  v
                                              Dept.getManager()
                                              (Person delegates)

  (client coupled to Person AND Dept)   (client coupled to Person only)
```

## 7. Dynamics

```
  t0  identify a chain of access in client code
       (e.g. a.getDept().getManager())
       |
       v
  t1  add a delegating method on the server
       (e.g. Person.getManager())
       |
       v
  t2  the delegating method calls the delegate
       and returns the result
       |
       v
  t3  update the client to call the
       delegating method instead of the chain
       |
       v
  t4  run test suite
       |
       v
  t5  commit. the delegate is hidden.
```

## 8. Implementation variants

**Delegating method.** The canonical variant. The server adds a method
that delegates to the delegate and returns the result. The client calls
the server's method instead of reaching through.

**Delegating property.** In languages with property syntax, the delegation
is through a computed property rather than a method, which gives the client
field access syntax for a delegated call.

**Interface hiding.** The delegate is hidden behind an interface that the
server exposes, so the client depends on the interface, not on the
delegate's concrete type. This variant combines Hide Delegate with the
Dependency Inversion Principle, and it is used when the delegate's
concrete type should not be visible.

```python
# Python: before (client reaches through Person to Department)

class Person:
    def __init__(self, department: "Department"):
        self._department = department

    def get_department(self) -> "Department":
        return self._department

class Department:
    def __init__(self, manager: "Person"):
        self._manager = manager

    def get_manager(self) -> "Person":
        return self._manager

# client: person.get_department().get_manager()  (chain of access)

# Python: after (Person delegates get_manager)

class Person:
    def __init__(self, department: "Department"):
        self._department = department

    def get_manager(self) -> "Person":
        return self._department.get_manager()

# client: person.get_manager()  (no chain)
```

```typescript
// TypeScript: before (chain of access)

class PersonBefore {
    constructor(private _department: DepartmentBefore) {}

    get department(): DepartmentBefore { return this._department; }
}

class DepartmentBefore {
    constructor(private _manager: PersonBefore) {}

    get manager(): PersonBefore { return this._manager; }
}

// client: person.department.manager  (chain)

// TypeScript: after (delegating property)

class Department {
    manager!: Person;
}

class Person {
    constructor(private _department: Department) {}

    get manager(): Person {
        return this._department.manager;
    }
}

// client: person.manager  (no chain)
```

```java
// Java: after (delegating method)

public class Person {
    private final Department department;

    public Person(Department department) {
        this.department = department;
    }

    public Person getManager() {
        return department.getManager();
    }
}

class Department {
    private final Person manager;

    public Department(Person manager) {
        this.manager = manager;
    }

    public Person getManager() {
        return manager;
    }
}

// client: person.getManager()  (no chain, client does not know about Department)
```

## 9. Known production uses

**Spring Data JPA repositories** use Hide Delegate to hide the
EntityManager from the application layer. A Spring Data repository
delegates to the EntityManager for find and save operations, but the
application code calls methods on the repository, not on the
EntityManager. The Spring Data documentation states that the repository
abstraction hides the persistence layer from the domain code
([Spring Data Repositories documentation](https://docs.spring.io/spring-data/jpa/reference/repositories/definition.html),
verified 2026-08-13).

**Python's `pathlib.Path`** hides the `os` module's path functions behind
a Path object that delegates to them. A caller that uses
`path.exists()` does not know that Path delegates to `os.path.exists`
internally, which hides the `os` module from the caller
([pathlib documentation](https://docs.python.org/3/library/pathlib.html),
verified 2026-08-13). This is the refactoring applied to the standard
library, and it is the example Fowler uses in the second edition.

## 10. Consequences

Positive.

- The client is coupled to one class, not to a chain, which reduces the
  impact of changes to the delegate's interface.
- The delegate is encapsulated behind the server, so the delegate's type
  and interface are implementation details that can change without
  affecting the client.
- The server's method has a name that communicates the intent, which is
  more readable than a chain of access that communicates only the
  mechanics.
- The Law of Demeter is satisfied, which reduces the coupling that
  produces ripple effects when a class in the chain changes.

Negative.

- The server has one more method, which is a maintenance burden,
  especially if many delegate methods are added.
- The server risks becoming a middle man, where most of its methods are
  pure forwarding to the delegate, which is the anti pattern that Remove
  Middle Man reverses.
- The delegating method adds a level of indirection, which is a small
  performance cost and a navigation cost for a reader.
- The refactoring can be over applied, hiding delegates that the client
  should know about, which obscures the architecture.

## 11. Failure modes and misuse

**Middle man explosion.** Every method on the delegate is forwarded to
the server, producing a server class that is all delegation and no
behaviour. The symptom is a class whose every method is a one line
forwarding call, which is the middle man smell. The fix is Remove Middle
Man, which lets the client access the delegate directly.

**Hiding the wrong delegate.** The delegate is a different architectural
layer, for example a data access object, and hiding it obscures the
layering. The client should know it is talking to a repository, not to a
domain object that delegates to a repository. The symptom is an
architecture where the layering is invisible, which makes it harder to
understand and to test.

**Delegating method with a bad name.** The method is named
`getDepartmentManager` instead of `getManager`, which leaks the delegate's
existence through the name. The client still knows about Department, even
though the chain is hidden, because the name references it. The fix is to
name the method for what the client wants, not for where the result comes
from.

**Over hiding.** The chain is one link, for example `person.getAddress()`,
and the delegate is a stable value object. Hiding it adds a delegating
method without reducing coupling, because the client already knows about
the address and needs to access it. The symptom is a class with delegating
methods for every field of every delegate, which is the middle man smell
applied to every relationship.

## 12. Trade-off matrix

| Alternative | Client coupling | Server methods | Delegation | When to prefer |
|---|---|---|---|---|
| Hide Delegate | One class | +1 per hidden method | Server forwards | Chain is long, delegate is unstable |
| Remove Middle Man | Chain of classes | -N forwarding methods | None | Server is pure forwarding, client should access directly |
| Extract Class | One class | New class | None | Server has too many responsibilities |
| Move Function | Moved to delegate | -1 from server | None | Method is on wrong class |

## 13. Related and incompatible patterns

**Remove Middle Man** (same catalog) is the inverse. It removes the
delegating method and lets the client access the delegate directly, which
is the right move when the server has become a middle man. The two
refactorings are applied in opposite directions, and a codebase that
oscillates between them is responding to changing requirements about how
much the client should know.

**Move Function** (same catalog) is the alternative when the method
should live on the delegate rather than being forwarded to it. If the
method's natural home is the delegate, moving it is better than
forwarding it, because moving eliminates the indirection.

**Extract Class** (same catalog) is the alternative when the server has
too many delegating methods and should be split. The delegating methods
can be extracted into a separate class that the client holds, which
reduces the server's method count.

**Replace Delegation with Inheritance** (same catalog) is the
alternative when the server delegates everything to the delegate and the
relationship is an is a, not a has a. Inheritance removes the delegation
but imposes a type hierarchy.

## 14. Refactoring path in and out

**Path in.** The refactoring is introduced by adding a delegating method
on the server. The steps are:

1. Identify a chain of access in the client, where the client calls a
   method on an object reached through the server.
2. Add a delegating method on the server that calls the delegate and
   returns the result.
3. Name the method for what the client wants, not for where the result
   comes from.
4. Update the client to call the delegating method instead of the chain.
5. Run the test suite. Any failure means the delegating method does not
   reproduce the chain's behaviour.
6. Consider whether the delegate should be fully hidden (no getter for
   the delegate) or partially hidden (getter remains for legitimate
   access).

**Path out.** The refactoring is reversed by Remove Middle Man, which
removes the delegating method and lets the client access the delegate
directly. The reverse is applied when the server has become a middle man
with too many forwarding methods.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test that exercised the chain of access should now exercise the
delegating method and should produce the same result. A test failure
means the delegating method does not reproduce the chain's behaviour.

A new test should test the delegating method in isolation, calling it
with known inputs and verifying the output. This test verifies the
delegation without requiring the client's integration test.

## 16. Observability signals

The refactoring does not change behaviour, so the observable signal in
production is nothing. The one observable difference is in the stack
trace: the delegating method appears in the trace where the chain of
access did not, because the method is now on the call path. This is
expected and is actually an observability improvement, because the trace
now shows the server's method, which has a name that communicates the
intent.

## 17. Security and privacy implications

The refactoring improves security in one specific way: the delegate is
hidden behind the server, so the client cannot access the delegate's
other methods. If the delegate has methods that the client should not
call, for example administrative methods on a Department that only
authorised callers should invoke, hiding the delegate prevents the
client from calling them. This is a positive security signal.

The privacy relevant case is that the delegate may contain sensitive
data that the client should not see. Hiding the delegate prevents the
client from reading the delegate's fields directly, because the client
does not have a reference to the delegate. The server controls what is
exposed through the delegating methods.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 9, "Hide Delegate."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 7, "Hide Delegate."
- Karl Lieberherr, *Demeter. Object-Oriented AOP*, 1989.
- Spring, "Repositories Definition,"
  [https://docs.spring.io/spring-data/jpa/reference/repositories/definition.html](https://docs.spring.io/spring-data/jpa/reference/repositories/definition.html),
  verified 2026-08-13.
- Python Software Foundation, "pathlib,"
  [https://docs.python.org/3/library/pathlib.html](https://docs.python.org/3/library/pathlib.html),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
