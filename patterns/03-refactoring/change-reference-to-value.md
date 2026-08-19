---
name: Change Reference to Value
slug: change-reference-to-value
family: 03-refactoring
category: Refactoring
aliases: [Reference to Value, Make Value Object]
first_described: "Fowler 1999"
maturity: canonical
related: [change-value-to-reference, replace-constructor-with-factory-function, replace-data-value-with-object, change-function-declaration]
incompatible_with: []
verified: 2026-08-13
---

# Change Reference to Value

## 1. Name, aliases, and lineage

The canonical name is **Change Reference to Value**, introduced by Martin
Fowler in *Refactoring. Improving the Design of Existing Code*, 1st edition,
Addison-Wesley, 1999, chapter 8, "Organizing Data." The refactoring survived
into the second edition, Martin Fowler, *Refactoring. Improving the Design of
Existing Code*, 2nd edition, Addison-Wesley, 2018, chapter 9, "Moving
Features," under the same name and with the same mechanics. Fowler moved it
from "Organizing Data" to "Moving Features" in the second edition because the
refactoring is fundamentally about where behaviour lives when an object's
identity changes.

The underlying concept, the distinction between reference objects and value
objects, predates the refactoring catalog. The term **value object** comes
from Martin Fowler's own writing in *Analysis Patterns*, Addison-Wesley,
1997, where he defines a value object as an object whose identity is
defined by its field values rather than by an object identifier. Ward
Cunningham and Kent Beck had used the term informally in the Smalltalk
community through the 1990s. The formal treatment in the patterns
literature is often credited to Linda Rising's *The Patterns Handbook*
(1998), which collected several treatments of value semantics.

The alias **Make Value Object** is used in the JavaScript and TypeScript
communities, where the operation is common because those languages lack a
built in value type for user defined classes. The alias **Reference to
Value** is a short form used in refactoring tools that display the operation
as a menu item.

## 2. Problem and context

You have a reference object, an object whose identity matters and which is
shared among multiple callers, but the sharing is producing more problems
than it solves. Each holder of the reference can mutate the object, and every
other holder sees the mutation, which creates coupling between callers that
have no other reason to know about each other. The object was made a
reference originally because someone expected it to be shared and mutated,
but in practice it is either never mutated after construction, or every
mutating call should have been a replacement with a new instance rather than
an in place modification.

The situation reads like this. A `Money` class was modelled as a reference
object because the original author assumed that amounts would be updated in
place, for example adding a fee to an existing Money instance. In practice,
every caller that receives a Money object treats it as read only and never
mutates it. But because the object is a reference, every caller must
defensively copy it before doing anything that might look like a mutation,
and every bug where a caller forgot to copy produces a shared mutation bug
that is among the hardest to diagnose. A fee added to one order's total
silently appears on three other orders because they all held the same Money
reference.

The fix is to make the class a value object. A value object has no identity
beyond its field values. Two Money objects with the same amount and currency
are interchangeable. The object is immutable after construction, so there is
no shared mutation to worry about. Adding a fee produces a new Money
instance rather than mutating the old one.

## 3. Forces

**Sharing versus independence.** A reference object allows multiple holders
to share state, which is efficient in memory and convenient when the shared
state genuinely needs to be visible everywhere. A value object gives each
holder its own copy, which costs more memory but eliminates the coupling
that shared mutation creates. The force favours value semantics when the
coupling cost of sharing exceeds the memory cost of copying.

**Mutation versus replacement.** A reference object is mutated in place,
which is cheap if the mutation is local and expensive if every holder must
be notified. A value object is replaced with a new instance, which is cheap
if the object is small and expensive if the object is large. The force
favours value when the object is small enough that replacement is cheap and
when in place mutation is the source of bugs.

**Equality semantics.** A reference object is compared by identity, so two
objects with identical fields are not equal. A value object is compared by
field values, so two objects with identical fields are equal. The force
favours value when callers naturally expect two identical amounts to be
equal, which is the case for money, coordinates, dates, and quantities.

**Hashing and collection behaviour.** A reference object that is mutated
after being inserted into a hash based collection breaks the collection's
invariant, because the hash code changes. A value object, being immutable,
has a stable hash code. The force favours value when the object is used as a
dictionary key or a set element.

**Serialisation.** A reference object that is shared among multiple holders
produces a serialisation graph with cycles or with duplicated data when the
same object appears in multiple places. A value object serialises naturally
because each instance is independent. The force favours value when the
object needs to be serialised across a boundary.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- The object is immutable in practice, meaning no caller mutates it after
  construction, but the class still allows mutation and the allowance is
  creating bugs.
- Callers are copying the object defensively before using it, which is a
  signal that the reference semantics are the wrong model and the copy is
  working around the wrongness.
- Two objects with the same field values should be considered equal, but
  equality comparison is done by identity, so identical values are reported
  as not equal.
- The object is small enough that copying it on every assignment is not a
  performance concern.
- The object is used as a hash key or a set element and is currently
  mutable, which is a latent bug because a mutation after insertion breaks
  the collection.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The object genuinely needs shared identity. Multiple holders need to see
  mutations from other holders, and that visibility is the correct
  behaviour, not a bug. A bank account is the canonical example: two
  transactions on the same account must see each other's effects.
- The object is large and copying it on every assignment would be
  prohibitively expensive in memory or time. A large document or a complex
  graph is a reference object for performance reasons, not for design
  reasons.
- The object participates in a bidirectional relationship that requires
  identity to maintain the back reference. Making it a value would break the
  invariant that each side of the relationship can update the other.
- The object's identity is load bearing in the persistence layer. A JPA or
  Hibernate entity that uses identity for dirty checking and caching cannot
  be a value object without reworking the persistence strategy.

## 5. Structure

The refactoring has one participant and one invariant.

- **The class.** The object being converted from reference to value. Before
  the refactoring, it has a mutable interface, identity based equality, and
  is shared by reference. After the refactoring, it has an immutable
  interface, value based equality, and is copied on assignment or passed by
  value.

The invariant is that every existing caller continues to produce the same
results. Callers that compared by identity must now compare by value and get
the same answer for the same field values. Callers that mutated the object
in place must now receive a new instance from the mutation and use it as a
replacement.

## 6. ASCII structure diagram

```
  REFERENCE OBJECT                        VALUE OBJECT
  ---------------                         ------------

  holder A --\                           holder A: copy 1 (amount=10)
              \---> [ Money ]                |
              /     amount=10                 v
  holder B --/      mutable!              equality( copy1, copy2 ) == true
                                              ^
                                              |
                                          holder B: copy 2 (amount=10)

  mutation:                              mutation:
  money.add(5)                           money2 = money1.add(5)
  // ALL holders see the change          // only holder A sees the new value
  // holder B is surprised               // holder B keeps the old copy
```

## 7. Dynamics

```
  t0  class is a reference object, mutable, shared
       |
       v
  t1  make all fields final / readonly / immutable
       (this is the mechanical step)
       |
       v
  t2  remove all setters and mutating methods
       (or convert them to return a new instance)
       |
       v
  t3  implement value equality:
       -- equals() / __eq__ compares field values
       -- hashCode() / __hash__ derived from field values
       |
       v
  t4  update callers that relied on in place mutation
       -- they now use the return value of the method
       -- money = money.add(5)  instead of  money.add(5)
       |
       v
  t5  run test suite
       -- every test that compared by identity now compares by value
       -- every test that mutated in place now checks the return value
       |
       v
  t6  commit. the class is now a value object.
```

## 8. Implementation variants

**Full immutability with value equality.** The canonical variant. Every
field is final or readonly, every method that would have mutated returns a
new instance, and equality is based on field values. This is the variant
Fowler describes in the second edition.

**Immutable wrapper.** The original mutable class is kept for internal use
or for a transition period, and an immutable wrapper is placed around it.
The wrapper delegates reads to the wrapped object and throws on writes.
This is the gradual migration variant, useful when the class is too widely
used to convert in one pass.

**Record or data class syntax.** Languages that have built in value record
syntax, such as Java records, C sharp records, or Kotlin data classes,
provide a shorthand for the full immutability variant. The compiler
generates value equality, hashing, and a canonical constructor. This is the
preferred variant in languages that support it, because the compiler
guarantees the invariants the refactoring would otherwise enforce by hand.

**Frozen at construction.** In Python, the `@dataclass(frozen=True)`
decorator produces an immutable value object with value based equality and
hashing. This is the Python idiom for the full immutability variant, and it
is the approach the standard library itself uses for `NamedTuple` and for
`fractions.Fraction`.

```python
# Python: reference object (before)

class Money:
    def __init__(self, amount, currency):
        self.amount = amount
        self.currency = currency

    def add(self, amount):
        self.amount += amount  # mutates in place!

# Python: value object (after, using frozen dataclass)

from dataclasses import dataclass

@dataclass(frozen=True)
class Money:
    amount: int
    currency: str

    def add(self, value: int) -> "Money":
        return Money(self.amount + value, self.currency)
```

```typescript
// TypeScript: value object via readonly fields

class Money {
    constructor(
        readonly amount: number,
        readonly currency: string
    ) {}

    add(value: number): Money {
        return new Money(this.amount + value, this.currency);
    }

    equals(other: Money): boolean {
        return this.amount === other.amount
            && this.currency === other.currency;
    }
}
```

```java
// Java: value object via record (Java 16+)

public record Money(int amount, String currency) {
    public Money {
        if (amount < 0) throw new IllegalArgumentException("negative");
    }

    public Money add(int value) {
        return new Money(amount + value, currency);
    }
}
```

## 9. Known production uses

**Java's `java.time` package, introduced in Java 8, uses value objects
exclusively for date and time representations.** The `LocalDate`,
`LocalDateTime`, and `Instant` classes are immutable and use value based
equality. The `LocalDate` documentation states that the class is immutable
and thread safe, and that date arithmetic methods return a new instance
rather than modifying the receiver
([java.time.LocalDate documentation](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/time/LocalDate.html),
verified 2026-08-13). This was a deliberate design choice after the mutable
`java.util.Date` and `java.util.Calendar` classes were the source of
countless concurrency and aliasing bugs in the previous API.

**Python's `fractions.Fraction` class is an immutable value object.** The
standard library documentation states that `Fraction` instances are
immutable and hashable, and that arithmetic operations return new instances
([Python fractions module](https://docs.python.org/3/library/fractions.html),
verified 2026-08-13). The class predates the `dataclass` decorator but
follows the same immutability and value equality contract.

## 10. Consequences

Positive.

- Shared mutation bugs are eliminated by construction, because the object
  cannot be mutated after creation.
- Equality comparison is natural: two objects with the same fields are equal,
  which matches the caller's expectation for quantities, dates, and
  coordinates.
- The object is safe to use as a hash key or set element, because the hash
  code is stable.
- The object is safe to share across threads without synchronisation,
  because immutability means no write can occur.

Negative.

- Every operation that would have mutated in place now allocates a new
  instance, which increases garbage collection pressure proportional to the
  frequency of operations.
- Callers that relied on in place mutation must be updated to use the
  return value, which is a mechanical change but a wide one if the class is
  widely used.
- The object cannot be used where shared identity is needed, for example a
  bank account whose balance must be visible to all holders.
- Large value objects are expensive to copy, so the refactoring is wrong
  for objects that are large and frequently passed around.

## 11. Failure modes and misuse

**Forgetting to update a caller that mutated in place.** A caller that did
`money.add(5)` and expected the mutation to be visible to other holders now
gets a new instance that it discards, and the original money object is
unchanged. The symptom is a silent logic error: the fee was supposed to be
added to the order total, but the total reads the original amount. No
exception is thrown.

**Mutable field inside an immutable class.** The class is marked as
immutable, but one of its fields is a mutable collection, for example a
`List` that is not copied on construction. A caller can reach into the
list and mutate it, bypassing the immutability guarantee. The symptom is
the same shared mutation bug the refactoring was supposed to eliminate,
made worse by the false confidence that the class is immutable.

**Value equality that ignores a field.** The `equals` method compares
amount and currency but forgets a precision field, so `Money(10, "USD",
scale=2)` and `Money(10, "USD", scale=4)` are reported as equal when they
are not. The symptom is incorrect equality that surfaces only when the
ignored field matters, for example in a financial calculation that depends
on precision.

**Performance regression on hot paths.** The refactoring turns a single
in place mutation into an allocation, and on a hot path that allocation
dominates the execution time. The symptom is a measurable slowdown in a
tight loop, which is the one case where the memory cost of copying
outweighs the safety benefit of immutability.

## 12. Trade-off matrix

| Alternative | Mutation model | Equality | Memory cost | Thread safety | When to prefer |
|---|---|---|---|---|---|
| Change Reference to Value | Replace, no in place mutation | By value | Higher, one copy per holder | Free, immutable | Object is small, shared mutation is a bug source |
| Change Value to Reference | In place, shared | By identity | Lower, one object shared | Requires sync | Object is large or needs shared identity |
| Replace Data Value with Object | N/A, creates the object | Depends on later choice | Depends | Depends | A primitive value has grown behaviour and needs a class |
| Replace Constructor with Factory Function | Same as original | Same as original | Same as original | Same as original | Construction needs to be controlled or vary |

## 13. Related and incompatible patterns

**Change Value to Reference** (same catalog) is the inverse refactoring. It
converts a value object to a reference object when shared identity is
needed. The two refactorings are applied in opposite directions and the
choice between them depends on whether the object's identity matters to its
callers.

**Replace Data Value with Object** (same catalog) is the refactoring that
creates the object in the first place, turning a primitive value like a
string into a class. Once the object exists, Change Reference to Value or
its inverse may be applied to set the right semantics.

**Replace Constructor with Factory Function** (same catalog) is frequently
applied alongside Change Reference to Value, because a value object that
is constructed in multiple places benefits from a factory that canonicalises
instances, for example by returning a cached instance for common values.

**Introduce Parameter Object** (same catalog) often produces a value object
as its output, because a parameter object that is passed around is naturally
a value object, and the immutability and value equality contract from this
refactoring applies to it.

## 14. Refactoring path in and out

**Path in.** The refactoring is introduced by making the class immutable
and implementing value equality. The steps are:

1. Make every field of the class final, readonly, or otherwise immutable.
2. Remove every setter and every method that mutates a field. Convert each
   to return a new instance with the updated field values.
3. Implement value based equality: override `equals` (Java), `__eq__`
   (Python), or the language equivalent to compare field values.
4. Implement value based hashing: override `hashCode` (Java), `__hash__`
   (Python), or the language equivalent to derive from field values.
5. Update every caller that relied on in place mutation to use the return
   value of the method instead.
6. Run the test suite. Any failure means either a caller was missed or the
   equality implementation is wrong.

**Path out.** The refactoring is reversed by Change Value to Reference,
which makes the class mutable again and switches equality back to identity.
The reverse is applied when the object genuinely needs shared identity,
not when someone is tired of seeing allocation in a profiler.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test that compared two instances by identity should now compare by value
and should report equal for two instances with the same fields. A test that
does `assert money1 == money2` where both have `amount=10, currency="USD"`
will pass after the refactoring and would have failed before it.

A test that checks immutability should attempt to mutate a field and verify
that the attempt either fails to compile (for final or readonly fields) or
throws at runtime (for frozen dataclasses). This test guards against a
future change that reintroduces mutability.

A test that checks the hash invariant should insert the object into a set,
mutate nothing, and verify the object is still found. This is a trivial
test for an immutable object but guards against a future change that makes
the class mutable and breaks the invariant.

## 16. Observability signals

A value object produces no observable signal in production that differs
from the reference object it replaced, because the behaviour is identical.
The difference is in the absence of shared mutation bugs, which is a
negative signal: bugs that used to happen no longer happen.

The one observable difference is in allocation profiling. The refactoring
increases the allocation rate, because every operation that would have
mutated in place now allocates a new instance. In a profiling tool, this
shows up as more short lived allocations in the garbage collection young
generation. This is expected and is the cost of the safety the refactoring
buys. If the allocation rate is unacceptable, the object is too large or
too frequently mutated for value semantics, and the reverse refactoring
should be considered.

## 17. Security and privacy implications

A value object is safer than the reference object it replaces in two
security relevant ways. First, there is no shared mutation, so one caller
cannot modify a value that another caller is depending on, which eliminates
a class of race conditions that can be exploited when the shared state is
security relevant, for example a permission set. Second, a value object is
safe to share across thread boundaries without synchronisation, which
eliminates the visibility bugs that mutable shared state produces in
concurrent code.

The privacy relevant case is that a value object cannot be used as a
covert channel between callers. Two callers that receive what they believe
is the same object cannot communicate through mutations to that object,
because no mutations are possible. This is a positive privacy signal,
because it closes a side channel that reference objects open.

Where the refactoring is silent is in the case where the value object's
fields contain sensitive data and the object is serialised across a trust
boundary. The refactoring does not change what data is serialised, only
how the object is compared and mutated. The serialisation behaviour is
unchanged and must be reviewed separately.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 9, "Change Reference to Value."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 8, "Change Reference to Value."
- Martin Fowler, *Analysis Patterns*, Addison-Wesley, 1997, "Value Object"
  pattern.
- Oracle, "java.time.LocalDate," Java SE 21 API documentation,
  [https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/time/LocalDate.html](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/time/LocalDate.html),
  verified 2026-08-13.
- Python Software Foundation, "fractions module,"
  [https://docs.python.org/3/library/fractions.html](https://docs.python.org/3/library/fractions.html),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
