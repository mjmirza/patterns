---
name: Preserve Whole Object
slug: preserve-whole-object
family: 03-refactoring
category: Refactoring
aliases: [Pass Whole Object, Replace Parameters with Object]
first_described: "Fowler 1999"
maturity: canonical
related: [introduce-parameter-object, change-function-declaration, extract-function, encapsulate-record, hide-delegate]
incompatible_with: []
verified: 2026-08-13
---

# Preserve Whole Object

## 1. Name, aliases, and lineage

The canonical name is **Preserve Whole Object**, introduced by Martin
Fowler in *Refactoring. Improving the Design of Existing Code*, 1st
edition, Addison-Wesley, 1999, chapter 10, "Making Method Calls Simpler."
The refactoring survived into the second edition, Martin Fowler,
*Refactoring. Improving the Design of Existing Code*, 2nd edition,
Addison-Wesley, 2018, chapter 11, "Making Calls Simpler," under the same
name and with the same mechanics.

The underlying idea, that a function which takes several values from the
same object should take the whole object instead, is the complement of
Introduce Parameter Object. Where Introduce Parameter Object creates a
new object to bundle unrelated parameters, Preserve Whole Object passes
an existing object that the caller already has. Joshua Kerievsky, in
*Refactoring to Patterns*, Addison-Wesley, 2004, describes the
refactoring as a step toward the Parameter Object pattern when the
object does not yet exist.

## 2. Problem and context

A function takes several parameters that are all fields of the same
object. The caller has the object, extracts the fields, and passes them
individually. The function receives the values as separate parameters,
which means it has no reference to the original object and cannot access
other fields if they are needed later. The parameter list is long, and a
change to the object's fields requires updating the function signature
and every call site.

The situation reads like this. A function `calculateRoomCharge` takes
`nights`, `rate`, and `taxRate`, which are all fields of a `Room` object.
The caller has a `Room` and extracts the three values:
`calculateRoomCharge(room.nights, room.rate, room.taxRate)`. If a new
field is needed, for example `cleaningFee`, the function signature
changes and every caller must extract the new field. The function cannot
access the room's other fields, and it cannot call methods on the room.

The fix is to pass the whole object. Change the function to take a
`Room` parameter, and access the fields inside the function. The caller
passes the room directly: `calculateRoomCharge(room)`. The parameter
list is one parameter instead of three, and the function can access any
field it needs without a signature change.

## 3. Forces

**Parameter count versus coupling.** Passing the whole object reduces
the parameter count, which is readable. It also couples the function to
the object's interface, which means a change to the object affects the
function. The force favours the whole object when the parameter count
reduction exceeds the coupling cost.

**Stability versus flexibility.** Passing individual values is stable:
the function is not affected by changes to the object's interface.
Passing the whole object is flexible: the function can access any field
without a signature change. The force favours the whole object when the
flexibility is needed and the object's interface is stable.

**Encapsulation versus transparency.** Passing the whole object gives
the function access to every field, including fields it does not use.
Passing individual values limits the function to what it receives. The
force favours individual values when the function should not have access
to the whole object, and favours the whole object when the function is
trusted to use only what it needs.

**Testing versus simplicity.** Passing individual values makes the
function easy to test: pass values, check the result. Passing the whole
object requires constructing the object with the right fields, which is
more setup. The force favours individual values when testing simplicity
matters most.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- The function takes two or more parameters that are all fields of the
  same object, and the caller already has the object.
- The function may need more fields from the object in the future, and
  passing the whole object avoids a signature change for each new field.
- The parameter list is long because the caller is extracting many fields
  from the same object.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The function takes values from different objects, not from the same
  one. The whole object does not exist, and the refactoring would require
  Introduce Parameter Object to create it.
- The function is a general utility that should not be coupled to a
  specific object's interface. Passing individual values keeps the
  function generic.
- The object is large and passing it gives the function access to many
  fields it does not need, which is a coupling the function should not
  have.
- The object is mutable and the function could accidentally modify it,
  which is a side effect that passing individual values prevents.

## 5. Structure

The refactoring has one participant: the set of parameters that are
fields of the same object. After the refactoring, the function takes the
whole object as a single parameter.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER
  ------                              -----

  charge(nights, rate, taxRate)       charge(room)
    // uses nights, rate, taxRate      // uses room.nights, room.rate, room.taxRate

  caller:                             caller:
    charge(room.nights,                 charge(room)
           room.rate,
           room.taxRate)
```

## 7. Dynamics

```
  t0  identify function with multiple params
       that are fields of the same object
       |
       v
  t1  add the whole object as a new parameter
       |
       v
  t2  replace field accesses with object.field
       in the function body
       |
       v
  t3  update callers to pass the whole object
       |
       v
  t4  remove the old individual parameters
       |
       v
  t5  run test suite
       |
       v
  t6  commit. the whole object is preserved.
```

## 8. Implementation variants

**Pass whole object.** The canonical variant. The function takes the
whole object and accesses its fields internally.

**Pass interface.** The function takes an interface that the object
implements, which limits the coupling to the interface's members. This
variant combines Preserve Whole Object with the Dependency Inversion
Principle.

**Pass immutable copy.** The function takes an immutable copy of the
object, which prevents the function from modifying the original. This
variant is used when the object is mutable and the function should not
have write access.

```python
# Python: before (extracted fields)

class Room:
    def __init__(self, nights: int, rate: float, tax_rate: float):
        self.nights = nights
        self.rate = rate
        self.tax_rate = tax_rate

def charge(nights: int, rate: float, tax_rate: float) -> float:
    return nights * rate * (1 + tax_rate)

# caller:
room = Room(3, 100, 0.08)
total = charge(room.nights, room.rate, room.tax_rate)

# Python: after (whole object)

def charge(room: Room) -> float:
    return room.nights * room.rate * (1 + room.tax_rate)

# caller:
total = charge(room)
```

```typescript
// TypeScript: after (whole object)

class Room {
    constructor(
        public nights: number,
        public rate: number,
        public taxRate: number
    ) {}
}

function charge(room: Room): number {
    return room.nights * room.rate * (1 + room.taxRate);
}

// caller:
const room = new Room(3, 100, 0.08);
const total = charge(room);
```

```java
// Java: after (whole object)

public class Room {
    private final int nights;
    private final double rate;
    private final double taxRate;

    public Room(int nights, double rate, double taxRate) {
        this.nights = nights;
        this.rate = rate;
        this.taxRate = taxRate;
    }

    public int getNights() { return nights; }
    public double getRate() { return rate; }
    public double getTaxRate() { return taxRate; }
}

class BillingService {
    public double charge(Room room) {
        return room.getNights() * room.getRate() * (1 + room.getTaxRate());
    }
}
```

## 9. Known production uses

**The Visitor pattern** from the GoF, described in Erich Gamma, Richard
Helm, Ralph Johnson, John Vlissides, *Design Patterns*, Addison-Wesley,
1995, passes the whole element object to the visitor's visit method,
rather than extracting individual fields. The visitor accesses the
fields it needs through the whole object, which is the canonical
application of Preserve Whole Object in a design pattern
([Design Patterns, Visitor](https://en.wikipedia.org/wiki/Visitor_pattern),
verified 2026-08-13).

**Spring's `ModelAttribute` annotation** binds a whole form object to a
controller method parameter, rather than extracting individual form
fields as separate parameters. The Spring documentation states that
`@ModelAttribute` on a method parameter binds request parameters, URI
path variables, and request headers onto that single object, which is
the whole object being preserved across the request boundary
([Spring ModelAttribute method arguments](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-methods/modelattrib-method-args.html),
verified 2026-08-19).

## 10. Consequences

Positive.

- The parameter list is shorter, which makes the function signature
  readable and the call sites clear.
- The function can access any field without a signature change, which is
  extensible.
- The relationship between the parameters is visible: they are all from
  the same object, which communicates that they are related.

Negative.

- The function is coupled to the object's interface, which means a
  change to the object affects the function.
- The function has access to every field, including fields it does not
  use, which is a coupling the function should not have.
- The function must construct or receive the object, which is more setup
  than passing individual values, especially in tests.
- If the object is mutable, the function could accidentally modify it,
  which is a side effect.

## 11. Failure modes and misuse

**Passing a large object that gives too much access.** The function
receives the whole object and gains access to fields it should not see.
The symptom is a function that reaches into fields that are not related
to its responsibility.

**Passing a mutable object that gets modified.** The function modifies
the object's fields, which is a side effect visible to the caller. The
symptom is an object whose fields change after a function call that
should have been read only.

**Coupling a generic utility to a specific type.** The function is a
generic utility that should work with any values, and passing the whole
object couples it to a specific type. The symptom is a function that
only works with one type when it could work with any type that provides
the same values.

## 12. Trade-off matrix

| Alternative | Param count | Coupling | Extensibility | When to prefer |
|---|---|---|---|---|
| Preserve Whole Object | 1 | To object's interface | High | Multiple params from same object |
| Introduce Parameter Object | 1 | To new object | High | Multiple params, object does not exist |
| Keep individual params | N | None | Low | Generic utility, few params |
| Replace Params with Query | 0 | To query | High | Values are computed, not stored |

## 13. Related and incompatible patterns

**Introduce Parameter Object** (same catalog) is the complement. It
creates a new object when one does not exist, where Preserve Whole Object
passes an existing object.

**Change Function Declaration** (same catalog) is the mechanism that
changes the function signature to take the whole object.

**Hide Delegate** (same catalog) is related when the whole object is a
delegate that the caller should not reach through. Preserve Whole Object
and Hide Delegate are applied in opposite directions.

## 14. Refactoring path in and out

**Path in.** Add the whole object as a parameter, replace field accesses,
update callers, remove old parameters.

**Path out.** Extract the individual values back as parameters, which
reverses the refactoring. Applied when the coupling to the object's
interface is wrong.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test should produce the same result, now through the whole object.

## 16. Observability signals

The refactoring does not change behaviour, so the observable signal in
production is nothing.

## 17. Security and privacy implications

The refactoring may affect security when the whole object contains
sensitive fields that the function should not access. Passing the whole
object gives the function access to every field, which is a coupling
that should be reviewed.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 11, "Preserve Whole Object."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 10, "Preserve Whole Object."
- Joshua Kerievsky, *Refactoring to Patterns*, Addison-Wesley, 2004.
- Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides, *Design
  Patterns*, Addison-Wesley, 1995, "Visitor."
- Spring, "ModelAttribute method arguments,"
  [https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-methods/modelattrib-method-args.html](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-methods/modelattrib-method-args.html),
  verified 2026-08-19.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
