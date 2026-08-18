---
name: Change Value to Reference
slug: change-value-to-reference
family: 03-refactoring
category: Refactoring
aliases: [Value to Reference, Make Reference Object]
first_described: "Fowler 1999"
maturity: canonical
related: [change-reference-to-value, replace-constructor-with-factory-function, replace-data-value-with-object, replace-delegation-with-inheritance]
incompatible_with: []
verified: 2026-08-13
---

# Change Value to Reference

## 1. Name, aliases, and lineage

The canonical name is **Change Value to Reference**, introduced by Martin
Fowler in *Refactoring. Improving the Design of Existing Code*, 1st edition,
Addison-Wesley, 1999, chapter 8, "Organizing Data." The refactoring survived
into the second edition, Martin Fowler, *Refactoring. Improving the Design
of Existing Code*, 2nd edition, Addison-Wesley, 2018, chapter 9, "Moving
Features," under the same name and with the same mechanics.

The distinction this refactoring turns on, whether an object's identity
matters, is one of the oldest ideas in object oriented design. The term
**reference object** appears in the Smalltalk community in the early 1990s.
Kent Beck, in *Smalltalk Best Practice Patterns*, Prentice Hall, 1997,
describes the choice between a value and a reference as a decision about
whether two instances with the same fields are interchangeable or whether
each instance has a separate identity that must be preserved.

The alias **Value to Reference** is used in refactoring tooling. The alias
**Make Reference Object** appears in the Java community, where the conversion
is often described as "promoting a value to an entity."

## 2. Problem and context

You have a value object, an object whose identity is defined by its field
values and which is immutable, but the immutability and the value semantics
are producing more problems than they solve. Multiple copies of the same
logical entity exist independently, each with its own field values, and
changes that should be visible to all holders are invisible because each
holder has its own copy. The object was made a value originally because
someone assumed it would be small and immutable, but in practice it
represents an entity whose state needs to be shared and updated.

The situation reads like this. A `Customer` class was modelled as a value
object because the original author treated it as a data transfer object, a
plain bag of fields that would be serialised and sent over the wire. But
the application now needs to update a customer's credit rating and have
every component that holds a reference to that customer see the update.
Because the customer is a value object, each component holds its own copy.
A credit rating update produces a new Customer instance, and only the caller
that triggered the update sees it. Every other component still holds the old
copy with the old rating, and no amount of defensive copying fixes this,
because the fundamental model is wrong.

The fix is to make the class a reference object. A reference object has
identity beyond its field values. Two Customer objects with the same fields
are still different objects if they have different identities. The object is
mutable, and every holder of a reference to it sees mutations. There is only
one Customer instance for a given customer, and it is shared.

## 3. Forces

**Sharing versus independence.** A value object gives each holder its own
copy, which is safe but means changes are not visible across holders. A
reference object allows multiple holders to share state, which is efficient
and correct when the shared state needs to be visible, but creates coupling
between holders. The force favours reference when the visibility is the
correct behaviour, not a bug.

**Identity versus equality.** A value object is compared by field values,
so two instances with the same fields are interchangeable. A reference
object is compared by identity, so two instances with the same fields are
still distinct. The force favours reference when each instance represents a
distinct entity whose identity must be preserved, even when field values
coincide.

**Mutation model.** A value object is replaced with a new instance on
every change, which is safe but loses the connection between the old and
new instance for any holder that was not updated. A reference object is
mutated in place, and every holder sees the mutation, which is the correct
behaviour when the state is shared.

**Memory and aliasing.** A value object is copied on assignment, which
costs memory proportional to the number of holders. A reference object is
shared, which costs one instance but creates aliasing, where the same object
is reachable from multiple paths, which is a source of coupling and of
concurrency bugs if the language does not provide synchronisation.

**Persistence.** A reference object typically maps to a single row in a
database, and the identity is the primary key. A value object does not have
a primary key and is stored as a column or as an embedded value. The force
favours reference when the object needs its own lifecycle in the
persistence layer.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- Multiple copies of the same logical entity exist, and changes made to one
  copy are not visible to holders of other copies, which is a bug.
- The object represents a real world entity whose identity is independent
  of its field values, for example a customer, an account, or an order.
- The object needs to be mutable, and the mutation must be visible to every
  holder, because the state is shared by design.
- The object maps to a row in a database with its own primary key, and the
  persistence layer requires identity to manage caching and dirty checking.
- The object participates in bidirectional relationships that require
  identity to maintain back references.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The object is genuinely a value, like money, a date, or a coordinate, and
  two instances with the same fields are interchangeable. Making it a
  reference would create false distinctions between identical values.
- The object is small and frequently copied, and the aliasing that reference
  semantics introduces would create more bugs than it solves.
- The object is used as a hash key or a set element. A mutable reference
  object used as a hash key breaks the collection's invariant when mutated.
- The application is concurrent and the shared mutable state would require
  synchronisation that the value semantics currently make unnecessary.
- The object does not need its own persistence lifecycle and is stored as
  an embedded value or a column.

## 5. Structure

The refactoring has one participant and one invariant.

- **The class.** The object being converted from value to reference. Before
  the refactoring, it is immutable, has value based equality, and is copied
  on assignment. After the refactoring, it is mutable, has identity based
  equality, and is shared by reference.

The invariant is that every existing caller continues to produce the same
results for the same operations. Callers that compared by value must now
compare by identity, which changes the semantics. The refactoring therefore
requires that every caller that relied on value equality is updated to rely
on identity equality, and that the update is correct, meaning the caller
genuinely needed identity, not value.

## 6. ASCII structure diagram

```
  VALUE OBJECT                           REFERENCE OBJECT
  ------------                           ----------------

  holder A: copy 1 (rating=A)           holder A --\
                                              \
  holder B: copy 2 (rating=A)               [ Customer ]  <-- single instance
                                              /     rating=A (mutable)
  holder C: copy 3 (rating=A)           holder B --/
                                              \
                                       holder C --/

  update:                               update:
  c1 = c1.withRating("B")              customer.setRating("B")
  // only holder A sees "B"            // ALL holders see "B"
  // holder B still sees "A"           // correct: shared state
  // holder C still sees "A"
```

## 7. Dynamics

```
  t0  class is a value object, immutable, copied on assignment
       |
       v
  t1  decide the class needs shared identity
       (typically: a mutation needs to be visible to all holders)
       |
       v
  t2  introduce a factory or registry that returns the same
       instance for the same logical entity
       (this is the mechanical step: canonicalise instances)
       |
       v
  t3  make fields mutable again
       (setters or mutating methods are re introduced)
       |
       v
  t4  switch equality from value based to identity based
       (equals becomes identity check, or identity based key)
       |
       v
  t5  update callers that relied on value equality
       (they now compare by identity, or by a business key)
       |
       v
  t6  run test suite
       -- tests that expected new instances now get the same instance
       -- tests that compared by value now compare by identity
       |
       v
  t7  commit. the class is now a reference object.
```

## 8. Implementation variants

**Factory with instance cache.** The canonical variant. A factory method
or a registry maintains a cache of instances keyed by a business identifier.
When a caller requests an instance, the factory returns the cached one if
it exists, or creates and caches a new one. This is the approach Fowler
describes in the second edition, and it is the standard pattern in
object relational mappers.

**Singleton per identity.** A specialisation of the factory variant where
each business identity maps to exactly one instance, and the instance is
created on first access and never destroyed. This is appropriate for
immutable reference objects, but is rarely the right choice for mutable
ones, because the singleton prevents the object from being garbage
collected even when no holder is alive.

**Identity map.** A pattern from Fowler's *Patterns of Enterprise
Application Architecture* (2003). An identity map is a map that guarantees
that each object loaded from a database is loaded only once per unit of
work, so that two queries for the same row return the same instance. This
is the mechanism Hibernate and other ORMs use internally, and it is the
production ready variant of the factory with instance cache.

**Database backed identity.** The reference identity is backed by the
database primary key. Two instances with the same primary key are the same
object, and the ORM or data access layer handles the canonicalisation. This
is the variant most production applications use, and it is the one where
the refactoring is least visible in the application code, because the
persistence framework does the work.

```python
# Python: value object (before)

from dataclasses import dataclass

@dataclass(frozen=True)
class Customer:
    name: str
    rating: str

# Python: reference object (after, via registry)

class Customer:
    _registry: dict[str, "Customer"] = {}

    def __init__(self, name: str, rating: str):
        self.name = name
        self.rating = rating

    @classmethod
    def get(cls, name: str) -> "Customer":
        if name not in cls._registry:
            cls._registry[name] = cls(name, "A")
        return cls._registry[name]

    def set_rating(self, rating: str) -> None:
        self.rating = rating
```

```typescript
// TypeScript: reference object via factory + cache

class Customer {
    private static registry = new Map<string, Customer>();

    private constructor(
        public name: string,
        public rating: string
    ) {}

    static get(name: string): Customer {
        let existing = Customer.registry.get(name);
        if (!existing) {
            existing = new Customer(name, "A");
            Customer.registry.set(name, existing);
        }
        return existing;
    }

    setRating(rating: string): void {
        this.rating = rating;
    }
}
```

```java
// Java: reference object via identity map

import java.util.HashMap;
import java.util.Map;

public class CustomerRegistry {
    private final Map<String, Customer> identityMap = new HashMap<>();

    public Customer findOrCreate(String name) {
        return identityMap.computeIfAbsent(name, n -> new Customer(n, "A"));
    }
}

class Customer {
    private String name;
    private String rating;

    Customer(String name, String rating) {
        this.name = name;
        this.rating = rating;
    }

    public void setRating(String rating) { this.rating = rating; }
    public String getRating() { return rating; }
}
```

## 9. Known production uses

**Hibernate's identity map pattern** is the production implementation of
this refactoring for database backed objects. Hibernate's documentation
states that the first level cache (the Session) guarantees identity within
a unit of work, so that two queries for the same database row return the
same Java object instance
([Hibernate User Guide, Persistence Context](https://docs.jboss.org/hibernate/orm/current/userguide/html_single/Hibernate_User_Guide.html#pc),
verified 2026-08-13). This is the identity map variant applied at the
framework level, and it is why Hibernate entities are reference objects by
default.

**Java's `Integer` class uses a form of value to reference conversion** for
small integers. The `Integer.valueOf(int)` method returns cached instances
for values between minus 128 and 127, so that `Integer.valueOf(5) ==
Integer.valueOf(5)` is true for small values. The Java Language
Specification documents this as a deliberate optimisation that trades
memory for identity stability
([JLS section 5.1.7, Boxing Conversion](https://docs.oracle.com/javase/specs/jls/se21/html/jls-5.html#jls-5.1.7),
verified 2026-08-13). This is the factory with instance cache variant
applied to a value type.

## 10. Consequences

Positive.

- Changes to the object are visible to every holder, which is the correct
  behaviour when the state is shared by design.
- The object maps naturally to a database row with its own primary key.
- Bidirectional relationships work, because each side can hold a reference
  to the other and update the back reference.
- Memory is saved, because one instance is shared rather than copied per
  holder.

Negative.

- Aliasing is introduced: multiple paths reach the same object, and a
  mutation from one path is visible from every other path. This is a source
  of coupling and of concurrency bugs.
- The object cannot be used as a hash key unless the hash is based on
  identity, because mutable state breaks value based hashing.
- Concurrency requires synchronisation, because multiple threads may reach
  the mutable state from different paths.
- The registry or factory that canonicalises instances is a global
  singleton, which is a testing and configuration burden.

## 11. Failure modes and misuse

**Stale reference after identity map eviction.** A registry or identity map
evicts an entry, for example at the end of a unit of work in an ORM. A
caller that held a reference to the evicted instance now has a stale object
that is disconnected from the persistence layer. The symptom is a call to a
mutating method that succeeds in memory but is never persisted, because
the object is no longer managed.

**Concurrent mutation without synchronisation.** Two threads hold
references to the same mutable object and both mutate it. The symptom is a
data race that produces inconsistent state, which is the classic failure
mode of shared mutable state and the one value semantics was designed to
prevent.

**Registry memory leak.** The registry holds strong references to every
instance it has ever created, and instances are never garbage collected.
The symptom is a slow memory growth that is invisible in the heap dump
because the registry looks like a single object, but it holds references to
every entity the application has ever loaded.

**False identity from caching.** Two logical entities that happen to have
the same business key are returned the same instance, because the factory
caches by key and the key collides. The symptom is a cross contamination
bug where a mutation intended for one entity is visible on another, which
is the most dangerous failure mode of this refactoring.

## 12. Trade-off matrix

| Alternative | Sharing | Mutation model | Equality | Concurrency | When to prefer |
|---|---|---|---|---|---|
| Change Value to Reference | Shared, aliased | In place, visible to all | By identity | Requires sync | Entity needs shared identity and visible mutations |
| Change Reference to Value | Copied, independent | Replace, isolated | By value | Free, immutable | Object is a value, shared mutation is a bug |
| Replace Constructor with Factory | Same as original | Same as original | Same as original | Same as original | Construction needs control, not identity |
| Replace Delegation with Inheritance | Same as original | Same as original | Same as original | Same as original | A delegate is doing all the work and the class should be the delegate |

## 13. Related and incompatible patterns

**Change Reference to Value** (same catalog) is the inverse refactoring. It
converts a reference object to a value object when the sharing is producing
more bugs than it solves. The two refactorings are applied in opposite
directions and the choice depends on whether the object's identity matters.

**Replace Constructor with Factory Function** (same catalog) is the
mechanical step that enables the factory with instance cache variant. The
constructor is made private and a factory method returns the canonical
instance. This refactoring is frequently applied alongside Change Value to
Reference to control which instance a caller receives.

**Replace Data Value with Object** (same catalog) creates the object in
the first place. Once the object exists, Change Value to Reference or its
inverse may be applied to set the right semantics.

**Identity Map** (Fowler, *Patterns of Enterprise Application
Architecture*, 2003) is the pattern that implements the instance
canonicalisation in a persistence context. It is the production ready
form of the factory with instance cache variant.

## 14. Refactoring path in and out

**Path in.** The refactoring is introduced by creating a registry or
factory that canonicalises instances and by switching equality to identity.
The steps are:

1. Introduce a business key that uniquely identifies each logical entity,
   for example a customer number or a database primary key.
2. Create a factory method or a registry that maintains a map from
   business key to instance.
3. Modify every construction site to go through the factory, so that two
   requests for the same key return the same instance.
4. Make the fields mutable again, if the object needs in place mutation.
5. Switch equality from value based to identity based. In Java, this means
   `equals` checks reference identity. In Python, drop `__eq__` and
   `__hash__` overrides so the default identity based equality applies.
6. Update every caller that relied on value equality to compare by identity
   or by business key.
7. Run the test suite. Any failure means a caller expected value equality
   and now gets identity equality, which is either a caller that should not
   have been converted or a test that needs updating.

**Path out.** The refactoring is reversed by Change Reference to Value,
which makes the class immutable and switches equality back to value based.
The reverse is applied when the shared identity is no longer needed or when
the aliasing is producing more bugs than it solves.

## 15. Testing and verification

The test suite is the primary verification, but the test cases change
character. A test that verified two instances with the same fields were
equal must now verify that two instances with the same business key are the
same object. A test that verified a mutation on one instance was not visible
to another must now verify that it is visible, because visibility is the
correct behaviour for a reference object.

A concurrency test should verify that mutations from multiple threads
produce consistent state, which means the test must synchronise access to
the shared object or accept that the object's synchronisation strategy is
correct. This is a new test that did not exist for the value object,
because the value object was immutable and had no concurrency concerns.

A test that checks the registry or factory should verify that two
requests for the same key return the same instance, and that two requests
for different keys return different instances. This is the invariant that
the canonicalisation depends on.

## 16. Observability signals

A reference object's observable signal in production is the visibility of
mutations. When a mutation is applied, every holder should see it. The
observability test is to log a mutation event with the object's identity
and then log the value read by a different holder. If the second holder
sees the old value, there is a stale reference or a concurrency bug.

In a distributed system, the reference object is local to a process, and
visibility across processes requires a different mechanism, for example a
cache invalidation protocol. The observability signal there is the cache
invalidation lag, the time between a mutation on one node and the
visibility of the mutation on another. This is not something the
refactoring addresses, because the refactoring is intra process, but it is
the signal that tells you when the refactoring is not enough and a
distributed cache is needed.

## 17. Security and privacy implications

A reference object is riskier than the value object it replaced in two
security relevant ways. First, shared mutable state is a concurrency
hazard, and a data race on a security relevant field, for example a
permission set, can produce a state where a check passes for one thread and
fails for another. Second, the registry or factory that canonicalises
instances is a global singleton, and a compromise of the registry gives an
attacker a single point of control over every instance of the class.

The privacy relevant case is that a reference object allows one caller to
modify a value that another caller is depending on, which is a form of
side channel. Two callers that receive the same object reference can
communicate through mutations, intentionally or unintentionally. This is
the same property that Change Reference to Value eliminates, and it is the
trade off that the refactoring makes.

Where the refactoring is silent is in the persistence layer. A reference
object that maps to a database row has its security governed by the
database's access control, not by the in memory representation. The
refactoring does not change the database's security model.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 9, "Change Value to Reference."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 8, "Change Value to Reference."
- Kent Beck, *Smalltalk Best Practice Patterns*, Prentice Hall, 1997,
  "Value Object" and "Reference Object" patterns.
- Martin Fowler, *Patterns of Enterprise Application Architecture*,
  Addison-Wesley, 2003, "Identity Map" pattern.
- Hibernate, "Persistence Context," Hibernate ORM User Guide,
  [https://docs.jboss.org/hibernate/orm/current/userguide/html_single/Hibernate_User_Guide.html#pc](https://docs.jboss.org/hibernate/orm/current/userguide/html_single/Hibernate_User_Guide.html#pc),
  verified 2026-08-13.
- Oracle, "Boxing Conversion," Java Language Specification, section 5.1.7,
  [https://docs.oracle.com/javase/specs/jls/se21/html/jls-5.html#jls-5.1.7](https://docs.oracle.com/javase/specs/jls/se21/html/jls-5.html#jls-5.1.7),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
