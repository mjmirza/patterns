---
name: Remove Setting Method
slug: remove-setting-method
family: 03-refactoring
category: Refactoring
aliases: [Remove Setter, Make Immutable, Remove Mutator]
first_described: "Fowler 2018"
maturity: canonical
related: [encapsulate-variable, change-reference-to-value, remove-dead-code, extract-class, replace-constructor-with-factory-function]
incompatible_with: []
verified: 2026-08-13
---

# Remove Setting Method

## 1. Name, aliases, and lineage

The canonical name is **Remove Setting Method**, introduced by Martin
Fowler in *Refactoring. Improving the Design of Existing Code*, 2nd
edition, Addison-Wesley, 2018, chapter 11, "Making Calls Simpler." The
refactoring is new to the second edition, though the broader Encapsulate
Field from the first edition covered the case of removing a setter to
make a field immutable. Fowler split it out because the mechanics differ:
removing a setter is about making the object immutable, not about
controlling access.

The underlying principle, that a field that should not change after
construction should not have a setter, is one of the oldest ideas in
immutable design. Joshua Bloch, in *Effective Java*, 1st edition,
Addison-Wesley, 2001, item 13, advises minimising mutability, and the
removal of a setter is the mechanical path. Robert C. Martin, in *Clean
Code*, Prentice Hall, 2008, chapter 6, writes that setters blur the
distinction between construction and mutation.

## 2. Problem and context

A class has a setter for a field that should not change after
construction. The setter was provided because the class was originally
mutable, or because a framework required it, or because the author
followed the JavaBeans convention of providing a setter for every field.
The setter allows callers to change the field after construction, which
produces aliasing bugs, concurrency bugs, and a general lack of
confidence in the object's state.

The situation reads like this. An `Order` class has a setter
`setCustomerId` that allows the customer to be changed after the order
is created. But changing the customer after creation is not a legitimate
operation: the order's line items, pricing, and discounts are all tied
to the customer, and changing the customer without re validating the
order produces an inconsistent order. The setter should not exist, but
it does, because the author followed the JavaBeans convention.

The fix is to remove the setting method. Remove `setCustomerId`, make
the field final, and set it only in the constructor. The order is now
immutable with respect to the customer, and the inconsistency is
impossible.

## 3. Forces

**Immutability versus flexibility.** Removing the setter makes the field
immutable, which is safe. Keeping the setter allows mutation, which is
flexible but produces aliasing and concurrency bugs. The force favours
removal when the field should not change after construction.

**Convention versus correctness.** The JavaBeans convention requires a
setter for every field, which is a convention for frameworks that use
reflection to populate objects. Removing a setter breaks the convention,
which may break the framework. The force favours removal when correctness
exceeds the convention's benefit.

**Construction versus mutation.** A field set at construction is
constructed. A field set by a setter is mutated. The force favours
construction when the field's value is known at construction time and
does not change.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- A field should not change after construction, and a setter exists
  that allows the change.
- The setter produces bugs by allowing inconsistent state, for example
  changing the customer on an order without re validating.
- The class does not need to be mutable for a framework that populates
  it via setters.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The field legitimately changes after construction, and the setter is
  the correct mechanism for the change.
- The class is populated by a framework that requires setters, and
  removing the setter breaks the framework.
- The class is a data transfer object that is populated field by field,
  and the setter is the population mechanism.

## 5. Structure

The refactoring has one participant: the setter that is removed, and the
field that becomes immutable.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER
  ------                              -----

  class Order:                       class Order:
    customerId                          customerId  (final)
    setCustomerId(id)                  (no setter)
    getCustomerId()                    getCustomerId()

  caller:                             caller:
    order.setCustomerId(2)             (cannot call setter)
```

## 7. Dynamics

```
  t0  identify setter for a field
       that should be immutable
       |
       v
  t1  make the field final / readonly
       |
       v
  t2  set the field only in the constructor
       |
       v
  t3  remove the setter
       |
       v
  t4  update callers that called the setter
       to pass the value to the constructor
       |
       v
  t5  run test suite
       |
       v
  t6  commit. setter removed.
```

## 8. Implementation variants

**Remove setter, make final.** The canonical variant. The setter is
removed, the field is made final, and the value is set in the
constructor.

**Remove setter, use factory.** The setter is removed, and a factory
method or builder constructs the object with the value.

**Remove setter, use init method.** In frameworks that require a no
arg constructor, the setter is replaced by an init method that is called
once after construction, which is a compromise between immutability and
framework requirements.

```python
# Python: before (mutable with setter)

class Order:
    def __init__(self):
        self._customer_id: int = 0

    def set_customer_id(self, customer_id: int) -> None:
        self._customer_id = customer_id

    def get_customer_id(self) -> int:
        return self._customer_id

# Python: after (immutable, no setter)

class Order:
    def __init__(self, customer_id: int):
        self._customer_id = customer_id

    def get_customer_id(self) -> int:
        return self._customer_id
```

```typescript
// TypeScript: before (mutable with setter)

class Order {
    private _customerId: number = 0;

    set customerId(id: number) { this._customerId = id; }
    get customerId(): number { return this._customerId; }
}

// TypeScript: after (immutable, readonly)

class Order {
    constructor(readonly customerId: number) {}
}
```

```java
// Java: after (immutable, final field, no setter)

public final class Order {
    private final int customerId;

    public Order(int customerId) {
        this.customerId = customerId;
    }

    public int getCustomerId() {
        return customerId;
    }
    // no setCustomerId
}
```

## 9. Known production uses

**Java's `String` class** has no setters and is immutable. The Java
documentation states that `String` objects are immutable, and the class
has no methods that modify the character sequence after construction
([java.lang.String](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/String.html),
verified 2026-08-13). This is the canonical example of a class with no
setters, and it is the model for the refactoring.

**Python's `frozen=True` dataclass** removes setters by making the
instance immutable. The Python documentation states that frozen dataclasses
raise `FrozenInstanceError` on any assignment to a field after
construction
([Python dataclasses frozen](https://docs.python.org/3/library/dataclasses.html#frozen-instances),
verified 2026-08-13).

## 10. Consequences

Positive.

- The field is immutable, which eliminates aliasing and concurrency bugs.
- The object's state is fixed at construction, which makes it easier to
  reason about.
- The class can be safely shared without defensive copying.

Negative.

- Callers that used the setter must now pass the value to the
  constructor, which changes the construction interface.
- If the value is not known at construction time, the class cannot be
  constructed without the value, which may require a builder or a
  factory.

## 11. Failure modes and misuse

**Removing a setter that is called.** The setter is called by
production code or by a framework, and removing it produces a compile
error or a runtime error.

**Removing a setter for a field that changes.** The field legitimately
changes after construction, and removing the setter makes the change
impossible without constructing a new object.

## 12. Trade-off matrix

| Alternative | Mutability | Immutability | When to prefer |
|---|---|---|---|
| Remove Setting Method | Mutable removed | Immutable | Field should not change |
| Encapsulate Variable | Controlled | Depends | Field needs validation on write |
| Change Reference to Value | N/A | Value object | Object should be a value |
| Keep setter | Mutable | No | Field legitimately changes |

## 13. Related and incompatible patterns

**Encapsulate Variable** (same catalog) is the broader refactoring that
wraps a field in accessors. Remove Setting Method is the specific case
where the setter is removed for immutability.

**Change Reference to Value** (same catalog) makes the whole object a
value object, which includes removing all setters.

**Replace Constructor with Factory Function** (same catalog) is often
applied alongside, because the factory can enforce invariants that the
constructor cannot.

## 14. Refactoring path in and out

**Path in.** Make the field final, set it in the constructor, remove the
setter, update callers.

**Path out.** Re introduce the setter if the field turns out to need
mutation, which is rarely applied.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test that set the field should now pass the value to the constructor.

## 16. Observability signals

The refactoring does not change behaviour for valid inputs, so the
observable signal is nothing. The one observable difference is that
attempts to call the setter produce a compile error in a static language
or an `AttributeError` in Python, which is the signal that the object is
immutable.

## 17. Security and privacy implications

The refactoring improves security when the field is security sensitive,
because immutability prevents unauthorised modification after
construction. This is a positive security signal.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 11, "Remove Setting Method."
- Joshua Bloch, *Effective Java*, 1st edition, Addison-Wesley, 2001,
  item 13.
- Robert C. Martin, *Clean Code*, Prentice Hall, 2008, chapter 6.
- Oracle, "java.lang.String,"
  [https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/String.html](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/String.html),
  verified 2026-08-13.
- Python Software Foundation, "dataclasses, frozen instances,"
  [https://docs.python.org/3/library/dataclasses.html#frozen-instances](https://docs.python.org/3/library/dataclasses.html#frozen-instances),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
