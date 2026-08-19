---
name: Encapsulate Variable
slug: encapsulate-variable
family: 03-refactoring
category: Refactoring
aliases: [Encapsulate Field, Self Encapsulate Field, Wrap Variable]
first_described: "Fowler 1999"
maturity: canonical
related: [encapsulate-record, encapsulate-collection, extract-class, change-reference-to-value, introduce-parameter-object]
incompatible_with: []
verified: 2026-08-13
---

# Encapsulate Variable

## 1. Name, aliases, and lineage

The canonical name is **Encapsulate Variable**, introduced by Martin Fowler
in *Refactoring. Improving the Design of Existing Code*, 2nd edition,
Addison-Wesley, 2018, chapter 8, "Encapsulating Data." In the first
edition (1999), the same operation appeared as two separate entries:
**Encapsulate Field** for public fields on classes, and **Self Encapsulate
Field** for fields accessed directly within the class that owns them.
Fowler consolidated them in the second edition because the mechanics
are identical regardless of whether the access is external or internal.

The distinction between direct field access and accessor mediated access
is one of the oldest debates in object oriented design. Joshua Bloch, in
*Effective Java*, 1st edition, Addison-Wesley, 2001, item 10, counsels
against public fields and in favour of accessors, primarily because
public fields prevent future changes to the internal representation. Kent
Beck, in *Implementation Patterns*, Addison-Wesley, 2007, takes the
opposite position for internal access, arguing that direct access within a
class is simpler and that accessors add indirection without benefit when
the class is the only accessor.

The alias **Self Encapsulate Field** is the name for the internal access
variant, where the class wraps its own field in accessors so that
subclasses can override the accessor. The alias **Encapsulate Field** is
the external access variant, where the field is public and the
refactoring makes it private with accessors.

## 2. Problem and context

You have a variable, typically a public field on a class or a module
level variable, that callers read and write directly. The direct access
means you cannot change the variable's representation, add validation on
write, or compute the value on read without finding and updating every
access site. The variable was public originally because the author did not
see a reason to hide it, but now the reason has appeared, and the
public access is preventing the change.

The situation reads like this. A `Person` class has a public `name`
field that callers set directly: `person.name = "Alice"`. The field is a
string, and every caller sets it to a non empty string, which works.
Now a new requirement arrives: the name should be trimmed of leading and
trailing whitespace before storage, and an empty name after trimming
should be rejected. Because the field is public, every caller that sets
`person.name` must be found and updated to trim and validate. There are
thirty callers across three modules. The change is mechanical but wide,
and any caller that is missed will set an untrimmed or empty name
silently.

The fix is to encapsulate the variable. Make the field private, add a
setter that trims and validates, and add a getter that returns the stored
value. Every caller that set the field now calls the setter, and every
caller that read the field now calls the getter. The trimming and
validation happen in one place, and every caller benefits without
knowing.

## 3. Forces

**Flexibility versus simplicity.** Direct field access is simple: one
read or write, no indirection. Accessor mediated access is flexible: the
internal representation can change, validation can be added, and the
accessor can be overridden. The force favours accessors when flexibility
matters, and favours direct access when simplicity matters and the
representation is stable.

**Validation versus trust.** A public field trusts every caller to set
valid values, which is fast but unsafe when callers make mistakes. An
accessor can validate, which is safe but adds a check on every write.
The force favours accessors when the variable has invariants, and favours
direct access when the type system already constrains the values enough
that validation is unnecessary.

**Overridability versus directness.** An accessor can be overridden by a
subclass, which allows polymorphic behaviour on field access. Direct
field access cannot be overridden, which is simpler but prevents
subclasses from customising the behaviour. The force favours accessors
when subclasses need to customise, and favours direct access when the
class is final or when subclass customisation is not desired.

**Performance versus indirection.** Direct field access is one memory
read or write. Accessor mediated access is a method call, which the JIT
usually inlines but which may not be inlined in every runtime. The force
favours direct access in hot paths where the method call overhead is
measured and unacceptable, and favours accessors everywhere else.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- The variable is public and callers write to it directly, and you need
  to add validation, logging, or a side effect on write that every caller
  should go through.
- The variable's representation needs to change, for example from a
  stored string to a computed value derived from other fields, and
  direct access prevents the change because every caller reads the field.
- The variable is accessed internally by the owning class, and a subclass
  needs to override the access to provide polymorphic behaviour.
- The variable is a module level global that callers read and write
  directly, and the global access is producing race conditions or
  consistency bugs that accessor methods with synchronisation would fix.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The variable is a private field accessed only by the owning class, the
  class is final or not subclassed, and the representation is stable.
  Accessors would add indirection without benefit, and direct access is
  simpler.
- The variable is a local variable inside a method, not a field. Local
  variables do not have accessors, and the refactoring does not apply.
- The variable is part of a data transfer object that is serialised
  directly, and accessors would break the serialisation framework's
  expectations of public field access.
- The class is a value object with immutable fields set at construction,
  and the fields are already read only. The immutability is enforced by
  the type system, and accessors add no value.

## 5. Structure

The refactoring has one participant.

- **The variable.** The field or module level variable being
  encapsulated. Before the refactoring, it is public or directly
  accessed. After the refactoring, it is private and accessed through
  getter and setter methods.

## 6. ASCII structure diagram

```
  BEFORE                                  AFTER
  ------                                  -----

  class Person:                          class Person:
    name: str  (public)                      _name: str  (private)

  caller:                                 setter:
    person.name = "  Alice  "                person.setName("  Alice  ")
    // stored as "  Alice  "                 // stored as "Alice" (trimmed)
                                             // rejected if empty after trim

                                          getter:
                                             person.getName()
                                             // returns "Alice"
```

## 7. Dynamics

```
  t0  identify variable that needs encapsulation
       |
       v
  t1  make the field private
       (rename if the old name was public, to catch
        direct access at compile time)
       |
       v
  t2  add a getter method
       -- returns the field value
       -- or computes it if the representation changed
       |
       v
  t3  add a setter method (if mutation is needed)
       -- validates the input
       -- stores the field
       |
       v
  t4  update every external caller
       that reads the field to call the getter
       |
       v
  t5  update every external caller
       that writes the field to call the setter
       |
       v
  t6  update internal access within the class
       to use the accessors too (self-encapsulation),
       if subclass override is needed
       |
       v
  t7  run test suite
       |
       v
  t8  commit. the variable is encapsulated.
```

## 8. Implementation variants

**Getter and setter.** The canonical variant. The field is private, the
getter returns it, and the setter validates and stores it. This is the
variant Fowler describes in both editions.

**Computed getter, no setter.** The field is removed, and the getter
computes the value from other fields. This variant is used when the value
is derived and should not be stored independently. It combines
Encapsulate Variable with Replace Derived Variable with Query, another
refactoring from the catalog.

**Property syntax.** Languages with property syntax, such as Python
`@property`, C sharp properties, and Kotlin `val`/`var`, provide a
shorthand for the getter and setter variant. The caller uses field access
syntax, which the language translates into accessor calls. This is the
preferred variant in languages that support it, because the caller syntax
is unchanged while the access is mediated.

**Lazy initialisation.** The getter computes the value on first access and
caches it. This variant is used when the value is expensive to compute
and may not be needed on every code path. The getter is the only
accessor, and there is no setter, because the value is derived.

```python
# Python: before (public field)

class Person:
    def __init__(self):
        self.name = ""

# Python: after (property with validation)

class Person:
    def __init__(self):
        self._name = ""

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("name cannot be empty")
        self._name = trimmed
```

```typescript
// TypeScript: before (public field)

class PersonBefore {
    constructor(public name: string = "") {}
}

// TypeScript: after (private field with getter/setter)

class Person {
    private _name: string = "";

    get name(): string {
        return this._name;
    }

    set name(value: string) {
        const trimmed = value.trim();
        if (!trimmed) throw new Error("name cannot be empty");
        this._name = trimmed;
    }
}
```

```java
// Java: before (public field)

class PersonBefore {
    public String name = "";
}

// Java: after (private field with accessors)

public class Person {
    private String name = "";

    public String getName() {
        return name;
    }

    public void setName(String value) {
        String trimmed = value.trim();
        if (trimmed.isEmpty()) {
            throw new IllegalArgumentException("name cannot be empty");
        }
        this.name = trimmed;
    }
}
```

## 9. Known production uses

**C sharp's property syntax is the language level implementation of this
refactoring.** The C sharp specification states that a property is a
member that provides a flexible mechanism to read, write, or compute the
value of a private field, and that properties can be used as if they were
public data members
([C sharp Properties documentation](https://learn.microsoft.com/en-us/dotnet/csharp/programming-guide/classes-and-structs/properties),
verified 2026-08-13). The property syntax is the standard C sharp idiom
for field encapsulation, and every C sharp codebase uses it.

**Python's `@property` decorator** provides the same mechanism. The
Python documentation describes `property` as a built in that returns a
property attribute, and the decorator syntax allows a getter, setter,
and deleter to be attached to a single attribute name
([Python property documentation](https://docs.python.org/3/library/functions.html#property),
verified 2026-08-13). The `property` decorator is used throughout the
Python standard library, for example in the `fractions.Fraction`
numerator and denominator properties.

## 10. Consequences

Positive.

- The variable's representation can change without affecting callers,
  because they interact through accessors.
- Validation can be added to the setter, which catches invalid values at
  the point of assignment.
- The accessor can be overridden by a subclass, which enables
  polymorphic behaviour on field access.
- A side effect, such as logging or invalidation, can be added to the
  getter or setter without updating callers.

Negative.

- Every read and write goes through a method call, which adds a layer of
  indirection and a small performance cost that is usually negligible.
- The accessor methods add names to the class, which is a maintenance
  burden when the names are wrong or when the accessors are trivial.
- Self encapsulation, where the class accesses its own fields through
  accessors, adds indirection to internal code that can make the class
  harder to read for a reader who expects direct field access.
- The refactoring can be over applied, adding accessors to every field
  even when the field is private, stable, and does not need validation.

## 11. Failure modes and misuse

**Accessor that adds no value.** The getter returns the field and the
setter stores it, with no validation, no computation, and no side effect.
The accessors add indirection without benefit, and the class is harder
to read because every field access goes through a method. The symptom is
a class full of trivial accessors that a reader must navigate through to
understand the code.

**Setter that does not validate.** The setter is provided but performs
no validation, so callers can set invalid values that the refactoring was
supposed to prevent. The symptom is the same invalid value bug the
refactoring was supposed to fix, now hidden behind an accessor that
gives a false sense of safety.

**Accessor that leaks the mutable internal state.** The getter returns a
reference to a mutable object stored in the field, and a caller can
mutate the object through the reference, bypassing the setter. The
symptom is the same uncontrolled mutation the refactoring was supposed
to prevent, because the getter gave out a reference to the internal state
rather than a copy or an unmodifiable view.

**Over encapsulation of a final immutable field.** The field is final,
set at construction, and never changes. The getter is trivial and there
is no setter. The encapsulation adds a method call where a direct field
read would be simpler, and the flexibility benefit does not exist because
the field cannot change. The symptom is a class with a getter for every
field, where the fields are all final and the getters all return the
field directly.

## 12. Trade-off matrix

| Alternative | Validation | Flexibility | Indirection | When to prefer |
|---|---|---|---|---|
| Encapsulate Variable | On write | Internal rep can change | Method call | Variable needs validation or future rep change |
| Encapsulate Record | On construction | Whole record encapsulated | Constructor + accessors | A record with multiple fields needs encapsulation |
| Keep public field | None | None | None | Field is stable, type constrained, no invariants |
| Replace Derived Variable with Query | Computed on read | Highest, no storage | Method call | Value is derived from other fields |

## 13. Related and incompatible patterns

**Encapsulate Record** (same catalog) is the multi field variant. It
wraps a whole record in a class, where Encapsulate Variable wraps a
single field. The two are frequently applied together: encapsulate the
record, then encapsulate individual fields within it.

**Encapsulate Collection** (same catalog) is the collection specific
variant. It wraps a collection field so callers cannot mutate the
collection's structure, where Encapsulate Variable wraps a scalar field.
The collection variant is harder because collections have internal
structure.

**Replace Derived Variable with Query** (same catalog) is the next step
when the variable's value is derived from other fields. The field is
removed entirely, and the getter computes the value on every call. This
is the variant that eliminates storage rather than encapsulating it.

**Extract Class** (same catalog) is the alternative when the variable
and its accessors are complex enough to deserve their own class. Rather
than encapsulating the variable in the existing class, extract a new
class that owns the variable and its accessors.

## 14. Refactoring path in and out

**Path in.** The refactoring is introduced by making the field private
and adding accessors. The steps are:

1. Make the field private. If it was public, rename it to catch direct
   access at compile time.
2. Add a getter method that returns the field value.
3. Add a setter method that validates and stores the value, if mutation
   is needed.
4. Update every external caller that reads the field to call the getter.
5. Update every external caller that writes the field to call the setter.
6. Consider updating internal access within the class to use the
   accessors too, if subclass override is needed.
7. Run the test suite. Any failure means a caller was missed or a
   validation check is wrong.

**Path out.** The refactoring is reversed by making the field public
again or by removing the accessors and accessing the field directly
within the class. The reverse is applied when the accessors are trivial,
the field is stable, and the encapsulation is providing no benefit.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test that read or wrote the field should now go through the accessors
and should produce the same result.

New tests should verify the validation in the setter. For each invariant,
call the setter with a valid value and with an invalid value, and verify
that the invalid value raises the expected exception. These tests guard
against a future change that removes or weakens the validation.

A test that checks the getter's return value should verify that it
matches the value set by the setter, which is the basic contract of the
encapsulated variable.

## 16. Observability signals

The refactoring does not change behaviour for valid inputs, so the
observable signal in production is nothing. The one observable difference
is in error patterns: if callers were setting invalid values that
produced confusing runtime errors, those values are now rejected by the
setter, and the error appears at the point of assignment with a clear
message. This is a positive observability signal.

If the accessor adds logging or a side effect, the observable signal is
the log entry or the side effect, which provides visibility into field
access that did not exist before. This is the observability benefit of
encapsulation: the class can add instrumentation to the accessors without
updating callers.

## 17. Security and privacy implications

The refactoring improves security when the variable is security
sensitive and the setter can reject values that would compromise the
system, for example a privilege level that must not be set above a
threshold. The setter is the security boundary, and the refactoring puts
the boundary in one place that every caller must go through.

The privacy relevant case is that the getter can be restricted or
omitted for sensitive fields, so callers cannot read data they should not
see. The absence of a getter for a field containing personally
identifiable information prevents callers from reading it, which is a
positive privacy signal.

Where the refactoring is silent is in the data itself: the same value is
stored in the same type, and the refactoring does not change what data
is collected or how it is used. The security and privacy benefit comes
from the control, not from the data.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 8, "Encapsulate Variable."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 8, "Encapsulate Field," "Self
  Encapsulate Field."
- Joshua Bloch, *Effective Java*, 1st edition, Addison-Wesley, 2001,
  item 10.
- Kent Beck, *Implementation Patterns*, Addison-Wesley, 2007.
- Microsoft, "Properties (C sharp Programming Guide),"
  [https://learn.microsoft.com/en-us/dotnet/csharp/programming-guide/classes-and-structs/properties](https://learn.microsoft.com/en-us/dotnet/csharp/programming-guide/classes-and-structs/properties),
  verified 2026-08-13.
- Python Software Foundation, "property built in,"
  [https://docs.python.org/3/library/functions.html#property](https://docs.python.org/3/library/functions.html#property),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
