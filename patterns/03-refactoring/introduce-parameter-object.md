---
name: Introduce Parameter Object
slug: introduce-parameter-object
family: 03-refactoring
category: Refactoring
aliases: [Group Parameters, Parameter Object, Bundle Parameters]
first_described: "Fowler 1999"
maturity: canonical
related: [extract-function, combine-functions-into-class, encapsulate-record, change-function-declaration, preserve-whole-object]
incompatible_with: []
verified: 2026-08-13
---

# Introduce Parameter Object

## 1. Name, aliases, and lineage

The canonical name is **Introduce Parameter Object**, introduced by
Martin Fowler in *Refactoring. Improving the Design of Existing Code*, 1st
edition, Addison-Wesley, 1999, chapter 6, "Composing Methods." The
refactoring survived into the second edition, Martin Fowler, *Refactoring.
Improving the Design of Existing Code*, 2nd edition, Addison-Wesley, 2018,
chapter 6, "A First Set of Refactorings," under the same name and with the
same mechanics. Fowler groups it with Extract Function and Extract Variable
in both editions, because the three refactorings are about simplifying
method calls.

The underlying idea, that a group of related parameters should be
bundled into a single object so the relationship is visible and the
parameter list is shorter, has roots in the value object pattern from
Martin Fowler's *Analysis Patterns*, Addison-Wesley, 1997, and in the
Parameter Object pattern from Joshua Kerievsky, *Refactoring to
Patterns*, Addison-Wesley, 2004. Kerievsky treats Parameter Object as a
pattern that emerges from the refactoring, and he notes that the object
can grow behaviour over time, evolving from a data bag into a full domain
object.

The alias **Group Parameters** is used in the Python community, where the
parameter object is often a dataclass. The alias **Bundle Parameters** is
used in the JavaScript community, where the parameter object is often a
plain object passed as a single argument.

## 2. Problem and context

You have a function with a long parameter list where several parameters
are naturally related. The parameters always appear together in the same
order, every caller provides all of them, and the group has a name in the
team's vocabulary that no parameter object carries. The parameter list is
hard to read because a caller must remember the order, and a change to the
group (adding a new parameter) requires updating every function signature
and every call site that passes the group.

The situation reads like this. A function `createOrder` takes `customerId`,
`shippingStreet`, `shippingCity`, `shippingState`, `shippingZip`, and
`billingStreet`, `billingCity`, `billingState`, `billingZip`. The
shipping parameters are always passed together and always in the same
order, and the billing parameters are the same. The function signature has
eight parameters, and a caller must count positions to know which string
is the shipping city and which is the billing city. Adding a `shippingCountry`
parameter requires updating every call site, and a caller that forgets
the country produces an order with no shipping country, silently.

The fix is to introduce a parameter object. Create an `Address` class
with `street`, `city`, `state`, `zip`, and `country` fields. The function
takes `customerId`, `shippingAddress`, and `billingAddress`, three
parameters instead of eight. The relationship between the address fields
is visible in the class, and adding a country field requires updating the
`Address` class, not every call site.

## 3. Forces

**Readability versus ceremony.** A long parameter list is hard to read
because the caller must remember the order and the types. A parameter
object is readable because the fields have names. The force favours the
object when the parameter list is long enough that names help, and favours
the flat list when the list is short enough that names add ceremony.

**Cohesion versus coupling.** A parameter object groups related parameters,
which makes the cohesion visible. The object also introduces a new type,
which is a coupling point. The force favours the object when the cohesion
benefit exceeds the coupling cost, which happens when the parameters are
always passed together.

**Extensibility versus stability.** A parameter object can gain new fields
without changing the function signature, which is extensible. A flat
parameter list requires a signature change for every new parameter, which
is stable but rigid. The force favours the object when the parameter group
is likely to grow.

**Immutability versus mutability.** A parameter object can be immutable,
which is safe because the function cannot modify the caller's data. A flat
parameter list is immutable by construction. The force favours the object
when immutability is wanted and the language supports it.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- The function has three or more parameters that are naturally related,
  for example the fields of an address, a date range, or a coordinate.
- The parameters always appear together in the same order across multiple
  functions, which is a signal that the group is a concept that deserves a
  name.
- The parameter list is long enough that a caller must count positions to
  know which argument is which, which is a readability problem.
- The parameter group is likely to grow, for example adding a country
  field to an address, and the growth should be localised to the object,
  not to every function signature.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The parameters are not related, even though they appear in the same
  function. Grouping unrelated parameters into an object produces a class
  with low cohesion that is worse than the flat list.
- The function has two or three parameters, and the list is readable. The
  object adds a class and a construction step without improving readability.
- The parameters are of the same type and the group is genuinely just a
  list, not a concept. A list of strings should be a `List<String>`, not a
  `StringGroup` object.
- The language has named arguments, such as Python's keyword arguments,
  and the caller uses names, which makes the order irrelevant and the
  grouping unnecessary for readability.

## 5. Structure

The refactoring has one participant.

- **The parameter group.** A set of related parameters that always appear
  together. After the refactoring, they are bundled into a single parameter
  object, and the function takes the object instead of the individual
  parameters.

## 6. ASCII structure diagram

```
  BEFORE                                    AFTER
  ------                                    -----

  createOrder(customerId,                   createOrder(customerId,
    shippingStreet, shippingCity,            shippingAddress,
    shippingState, shippingZip,              billingAddress)
    billingStreet, billingCity,
    billingState, billingZip)              class Address:
                                              street, city, state, zip
  (8 params, caller counts positions)      (3 params, names are clear)
```

## 7. Dynamics

```
  t0  identify group of related parameters
       |
       v
  t1  create a class for the group
       with the same fields and types
       |
       v
  t2  add the parameter object as a
       new parameter to the function
       |
       v
  t3  update the function body to read
       from the object's fields instead
       of the individual parameters
       |
       v
  t4  update every call site to construct
       the object and pass it
       |
       v
  t5  remove the old individual parameters
       |
       v
  t6  run test suite
       |
       v
  t7  commit. the parameters are grouped.
```

## 8. Implementation variants

**Value object.** The canonical variant. The parameter object is an
immutable value object with the related fields, and the function takes it
as a single parameter. This is the variant Fowler describes in both
editions.

**Dataclass or record.** Languages with dataclass or record syntax provide
a shorthand for the value object variant. The parameter object is a
dataclass in Python, a record in Java, or a record in C sharp, which
generates the constructor, accessors, and equality automatically.

**Builder.** When the parameter object has many fields or optional fields,
a builder provides fluent construction. This variant is used when the
parameter object is complex enough that construction is a multi step
process.

**Keyword arguments object.** In JavaScript and TypeScript, the parameter
object is a plain object or a destructured parameter, which gives the
caller named argument syntax without a formal class.

```python
# Python: before (long parameter list)

def create_order(
    customer_id: int,
    ship_street: str, ship_city: str,
    ship_state: str, ship_zip: str,
    bill_street: str, bill_city: str,
    bill_state: str, bill_zip: str,
) -> Order:
    ...

# Python: after (parameter object via dataclass)

from dataclasses import dataclass

@dataclass(frozen=True)
class Address:
    street: str
    city: str
    state: str
    zip: str

def create_order(
    customer_id: int,
    shipping: Address,
    billing: Address,
) -> Order:
    ...
```

```typescript
// TypeScript: before (long parameter list)

function createOrder(
    customerId: number,
    shipStreet: string, shipCity: string,
    shipState: string, shipZip: string,
    billStreet: string, billCity: string,
    billState: string, billZip: string,
): Order { ... }

// TypeScript: after (parameter object via class)

class Address {
    constructor(
        readonly street: string,
        readonly city: string,
        readonly state: string,
        readonly zip: string
    ) {}
}

function createOrder(
    customerId: number,
    shipping: Address,
    billing: Address,
): Order { ... }
```

```java
// Java: after (parameter object via record)

public record Address(
    String street, String city,
    String state, String zip
) {}

public Order createOrder(
    int customerId,
    Address shipping,
    Address billing
) { ... }
```

## 9. Known production uses

**Java's `java.time.LocalDate` and related classes** are parameter objects
that bundle year, month, and day into a single object. The `java.time`
API was designed to replace the old `Date` and `Calendar` APIs that
used separate integer parameters for year, month, and day, which
produced ordering bugs. The `LocalDate` documentation states that the
class is immutable and that it represents a date without a time zone
([java.time.LocalDate documentation](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/time/LocalDate.html),
verified 2026-08-13).

**Python's `collections.namedtuple` and `typing.NamedTuple`** are the
standard library's parameter object mechanism. The Python documentation
states that named tuples assign a meaning to each position in a tuple and
give it a name, which is the parameter object pattern applied to the
tuple type
([collections.namedtuple documentation](https://docs.python.org/3/library/collections.html#collections.namedtuple),
verified 2026-08-13).

## 10. Consequences

Positive.

- The parameter list is shorter, which makes the function signature
  readable and the call sites clear.
- The relationship between the parameters is visible in the object, which
  communicates that the fields are a group.
- New fields can be added to the object without changing the function
  signature, which is extensible.
- The object can gain behaviour over time, evolving from a data bag into
  a domain object with validation and methods.

Negative.

- The call site must construct the object, which is more ceremony than
  passing the parameters directly.
- The object is a new type in the codebase, which adds a class and a
  file.
- If the parameters are not genuinely related, the object has low cohesion
  and is worse than the flat list.
- The object may be passed to functions that do not need all its fields,
  which gives those functions access to fields they should not see.

## 11. Failure modes and misuse

**Parameter object for unrelated parameters.** The parameters are grouped
into an object because they appear in the same function, but they are not
related. The object has low cohesion and a caller must construct it with
fields it does not need. The symptom is a parameter object whose fields
are not a concept.

**Parameter object that is a data bag.** The object has fields but no
behaviour, and every function that receives it reaches into its fields
directly. The object is a struct, not a domain object, and it provides no
encapsulation. The symptom is a class with public fields and no methods.

**Parameter object that grows too large.** The object starts with three
fields and grows to twenty, because every new parameter is added to the
object rather than to the function signature. The symptom is a parameter
object that is a god object, carrying every parameter the function could
ever need.

**Over grouping.** Two parameters are grouped into an object, which is not
enough to justify the class. The symptom is a parameter object with two
fields that is used by one function, which is more ceremony than the flat
list.

## 12. Trade-off matrix

| Alternative | Param count | Readability | Extensibility | When to prefer |
|---|---|---|---|---|
| Introduce Parameter Object | Reduced | High, named fields | High, add fields | 3+ related params |
| Preserve Whole Object | Reduced | High | High | Object already exists |
| Change Function Declaration | Same | Same | Same | Rename or reorder params |
| Keep flat list | Original | Low for long lists | Low, change signature | List is short, params unrelated |

## 13. Related and incompatible patterns

**Preserve Whole Object** (same catalog) is the variant where the parameter
object already exists as a field on another object, and the function
receives the whole object instead of extracting its fields. The two are
related: Preserve Whole Object passes an existing object, Introduce
Parameter Object creates a new one.

**Combine Functions into Class** (same catalog) is the next step when the
parameter object gains behaviour. The functions that operate on the
object's fields become methods on the object, which evolves the parameter
object from a data bag into a domain object.

**Encapsulate Record** (same catalog) is related when the parameter object
needs validation or encapsulation. The record is encapsulated with private
fields and accessors, which is the same operation applied to the parameter
object.

**Change Function Declaration** (same catalog) is the alternative when
the parameter list is short enough that renaming or reordering is better
than grouping.

## 14. Refactoring path in and out

**Path in.** The refactoring is introduced by creating a parameter object
and replacing the individual parameters with it. The steps are:

1. Identify the group of related parameters.
2. Create a class with the same fields and types.
3. Add the parameter object as a new parameter to the function.
4. Update the function body to read from the object's fields.
5. Update every call site to construct the object and pass it.
6. Remove the old individual parameters.
7. Run the test suite. Any failure means a field was not mapped correctly
   or a call site was missed.

**Path out.** The refactoring is reversed by inlining the object's fields
back into the function signature, which is rarely applied because the
object is usually an improvement. The reverse is applied when the object
turns out to have low cohesion or when the function only uses one field
of the object.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test that exercised the function should produce the same result, but
through the parameter object instead of the individual parameters.

A new test should verify that the parameter object's fields are set
correctly by the caller and read correctly by the function. This is an
integration test of the construction and the field access.

## 16. Observability signals

The refactoring does not change behaviour, so the observable signal in
production is nothing. The one observable difference is in the function's
stack trace: the parameter object appears in the trace where the
individual parameters used to, which is a minor trace format change.

## 17. Security and privacy implications

The refactoring improves security when the parameter object can validate
its fields at construction, which rejects invalid values before the
function is called. This is a positive security signal when the parameters
are security relevant, for example an address that must be validated.

The privacy relevant case is that the parameter object can restrict access
to its fields through encapsulation, so a function that receives the
object can only read the fields the object exposes. This is a positive
privacy signal when the object contains mixed data with different access
levels.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 6, "Introduce Parameter Object."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 6, "Introduce Parameter Object."
- Martin Fowler, *Analysis Patterns*, Addison-Wesley, 1997, "Value Object."
- Joshua Kerievsky, *Refactoring to Patterns*, Addison-Wesley, 2004,
  "Parameter Object."
- Oracle, "java.time.LocalDate,"
  [https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/time/LocalDate.html](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/time/LocalDate.html),
  verified 2026-08-13.
- Python Software Foundation, "collections.namedtuple,"
  [https://docs.python.org/3/library/collections.html#collections.namedtuple](https://docs.python.org/3/library/collections.html#collections.namedtuple),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
