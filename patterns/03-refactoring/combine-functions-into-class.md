---
name: Combine Functions into Class
slug: combine-functions-into-class
family: 03-refactoring
category: Refactoring
aliases: [Form Class from Functions, Encapsulate Functions, Group Functions into Class]
first_described: "Fowler 1999"
maturity: canonical
related: [combine-functions-into-transform, extract-class, encapsulate-record, replace-function-with-command, introduce-parameter-object]
incompatible_with: []
verified: 2026-08-13
---

# Combine Functions into Class

## 1. Name, aliases, and lineage

The canonical name is **Combine Functions into Class**, introduced by
Martin Fowler in *Refactoring. Improving the Design of Existing Code*, 1st
edition, Addison-Wesley, 1999, chapter 6, "Moving Features Between
Objects." In the second edition, Martin Fowler, *Refactoring. Improving the
Design of Existing Code*, 2nd edition, Addison-Wesley, 2018, chapter 8,
"Encapsulating Data," Fowler renamed and reorganised the refactoring,
placing it in the context of data encapsulation rather than object
movement, because the refactoring is fundamentally about giving data a
home.

The underlying idea, that a group of functions that operate on the same
data should become methods of a class that owns the data, is one of the
oldest ideas in object oriented design. Grady Booch, in *Object-Oriented
Analysis and Design with Applications*, Benjamin Cummings, 1994, describes
the principle of colocation: data and the operations on that data should
live together in the same abstraction. Fowler's refactoring is the
mechanical path from a procedural structure to that object oriented
structure.

The alias **Form Class from Functions** appears in the Python community,
where the operation is common because Python supports both free functions
and methods, and the decision about which to use is a recurring design
question. The alias **Encapsulate Functions** is used in the JavaScript
community, where module patterns were the precursor to class syntax.

## 2. Problem and context

You have a set of functions, typically free functions in a module, that all
operate on the same data structure or the same set of parameters. Each
function takes the data as a parameter, performs some transformation, and
returns a result. The functions are coupled by the data they share, but
the coupling is invisible in the code structure because the functions are
scattered across a module or across several modules. A change to the data
structure requires finding and updating every function that takes it as a
parameter, and there is no single place that owns the data or the
operations on it.

The situation reads like this. A `temperature` module has three functions:
`toCelsius(rawReading)`, `toFahrenheit(rawReading)`, and
`isInRange(rawReading, min, max)`. Each function takes the same
`rawReading` parameter, which is a number representing a sensor reading in
Kelvin. The functions are related by their shared data, but they live as
free functions. A caller has to know which module has the functions, and
the data has no home. If a fourth function is added, it is placed in the
same module by convention, but nothing enforces the grouping. If the data
structure changes, for example if `rawReading` becomes a tuple of value
and unit, every function must be found and updated, and the compiler will
only catch the ones that are called with the old signature.

The fix is to combine the functions into a class. Create a `Temperature`
class that holds the raw reading as a field, and convert each function into
a method that operates on that field. The data now has a home, the
operations are colocated with it, and the class boundary makes the coupling
visible and enforceable.

## 3. Forces

**Colocation versus flexibility.** Free functions are flexible: any caller
can call them with any data. Class methods are colocated: the data and the
operations are bound. The force favours the class when the flexibility of
free functions is producing bugs, because callers pass the wrong data or
pass data in the wrong state, and the class boundary prevents that.

**State versus statelessness.** Free functions are stateless: they take
input and produce output. Class instances hold state: the data lives in the
object between calls. The force favours the class when the state is a
useful cache or context, and favours free functions when the state is a
liability because it creates aliasing and mutation bugs.

**Cohesion versus accidental grouping.** Functions that operate on the same
data are cohesive by definition, and grouping them into a class makes the
cohesion visible. Functions that happen to be in the same module but
operate on different data are accidentally grouped, and putting them in a
class would create a class with low cohesion. The force favours the class
when the functions share data, and favours keeping them as free functions
when they do not.

**Testing versus encapsulation.** Free functions are easy to test: call
them with input, check the output. Class methods require an instance, which
means the test must construct the object with the right state first. The
force favours free functions when testing simplicity matters most, and
favours the class when the encapsulation benefit exceeds the testing cost.

**Immutability versus mutation.** A class can be immutable, holding its
data as a final field, or mutable, allowing in place changes. Free
functions that take input and return output are naturally immutable in their
data model. The force favours the class when immutability is a useful
guarantee that the class can enforce, and is neutral when the functions are
already stateless.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- Two or more functions take the same parameter, or the same set of
  parameters, in every call. The shared parameter is the data the class
  will hold.
- The functions are related by the data they share, not by coincidence of
  being in the same module. If the functions were in different modules, you
  would still want them together.
- The data has no natural owner in the current structure, or the owner is
  the module itself, which is an implicit owner that the type system does
  not enforce.
- Callers are passing the wrong data or the wrong state to the functions,
  and the class boundary would prevent that by constructing the object in
  a known state and exposing only methods that operate on that state.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The functions do not share data. They are in the same module by
  coincidence, not by cohesion, and grouping them into a class would
  create a class with low cohesion and no purpose.
- The functions are stateless utilities, like `Math.abs` or
  `String.toUpperCase`, that operate on any value of their parameter type
  and have no shared state to encapsulate. These functions belong as free
  functions or static methods, not as instance methods of a class that
  holds state.
- The functions operate on different representations of the data, and the
  class would have to convert between representations internally, adding
  complexity rather than removing it.
- The functions are part of a functional programming style where data is
  passed through a pipeline of transformations, and the pipeline style is
  intentional, not accidental. In that case, the class is the wrong
  abstraction, and a pipeline of functions is the right one.

## 5. Structure

The refactoring has two participants.

- **The functions.** Two or more free functions that share a parameter.
  After the refactoring, each function becomes a method of the class, and
  the shared parameter becomes a field of the class.
- **The data.** The shared parameter, which was passed to every function
  and is now held by the class instance. After the refactoring, callers
  construct the class with the data and call methods on the instance
  instead of passing the data to free functions.

## 6. ASCII structure diagram

```
  BEFORE                                    AFTER
  ------                                    -----

  module temperature:                       class Temperature:
    toCelsius(rawReading)                     rawReading  (field)
    toFahrenheit(rawReading)                  toCelsius()
    isInRange(rawReading, min, max)          toFahrenheit()
                                              isInRange(min, max)

  caller:                                   caller:
    raw = 300                                  temp = Temperature(300)
    c = toCelsius(raw)                         c = temp.toCelsius()
    f = toFahrenheit(raw)                      f = temp.toFahrenheit()
    ok = isInRange(raw, 200, 400)              ok = temp.isInRange(200, 400)
```

## 7. Dynamics

```
  t0  identify functions that share the same parameter
       |
       v
  t1  create a class with the shared parameter as a field
       (constructor takes the data)
       |
       v
  t2  convert each function to a method
       -- remove the shared parameter from the method signature
       -- the method reads the field instead
       |
       v
  t3  update each call site:
       -- construct the class with the data
       -- call the method on the instance
       |
       v
  t4  run test suite
       -- every call site should produce the same result
       |
       v
  t5  delete the old free functions
       (or keep them as delegating shims for backward compat)
       |
       v
  t6  commit. the functions are now methods of a class.
```

## 8. Implementation variants

**Full class with constructor.** The canonical variant. A class is created
with a constructor that takes the shared data as a parameter, and each
function becomes a method that reads the data from the instance field. This
is the variant Fowler describes in the second edition.

**Immutable class with factory.** A factory function or static factory
method constructs the class with the data, and the class is immutable. This
variant combines Combine Functions into Class with the value object
contract, giving both colocation and immutability.

**Extension methods.** In languages that support extension methods, such as
C sharp and Kotlin, the functions can be converted to extension methods on
the data type without creating a new class. This is a lighter weight
variant that gives the appearance of colocation without the class boundary.
It is appropriate when the data type already exists and you do not want to
wrap it, but it does not provide the encapsulation or the state management
that the class variant provides.

**Module as class.** In Python, a module can serve as the class, with the
data stored as module level state. This is the degenerate variant where the
class boundary is the module boundary, and it is appropriate for small sets
of functions where a full class would be overkill. The risk is that module
level state is global, and the variant loses the per instance isolation
that a class provides.

```python
# Python: before (free functions sharing a parameter)

def to_celsius(raw_reading: float) -> float:
    return raw_reading - 273.15

def to_fahrenheit(raw_reading: float) -> float:
    return (raw_reading - 273.15) * 9 / 5 + 32

def is_in_range(raw_reading: float, lo: float, hi: float) -> bool:
    return lo <= raw_reading <= hi

# Python: after (class with shared field)

class Temperature:
    def __init__(self, raw_reading: float):
        self._raw = raw_reading

    def to_celsius(self) -> float:
        return self._raw - 273.15

    def to_fahrenheit(self) -> float:
        return (self._raw - 273.15) * 9 / 5 + 32

    def is_in_range(self, lo: float, hi: float) -> bool:
        return lo <= self._raw <= hi
```

```typescript
// TypeScript: before (free functions)

function toCelsius(rawReading: number): number {
    return rawReading - 273.15;
}

function toFahrenheit(rawReading: number): number {
    return (rawReading - 273.15) * 9 / 5 + 32;
}

// TypeScript: after (class with shared field)

class Temperature {
    constructor(private readonly raw: number) {}

    toCelsius(): number {
        return this.raw - 273.15;
    }

    toFahrenheit(): number {
        return (this.raw - 273.15) * 9 / 5 + 32;
    }

    isInRange(lo: number, hi: number): boolean {
        return this.raw >= lo && this.raw <= hi;
    }
}
```

```java
// Java: after (immutable class with factory)

public final class Temperature {
    private final double raw;

    private Temperature(double raw) { this.raw = raw; }

    public static Temperature of(double rawReading) {
        return new Temperature(rawReading);
    }

    public double toCelsius() {
        return raw - 273.15;
    }

    public double toFahrenheit() {
        return (raw - 273.15) * 9 / 5 + 32;
    }

    public boolean isInRange(double lo, double hi) {
        return raw >= lo && raw <= hi;
    }
}
```

## 9. Known production uses

**Java's `String` class is the canonical example of this refactoring
applied at the language level.** The `String` class combines a character
sequence (the data) with the operations that work on it (`length`,
`charAt`, `substring`, `toUpperCase`). In C, the equivalent operations are
free functions that take a `char*` parameter, which is the procedural
structure the refactoring transforms away from. The Java `String` class is
immutable, combining the colocation of Combine Functions into Class with
the value object contract of Change Reference to Value
([java.lang.String documentation](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/String.html),
verified 2026-08-13).

**Python's `pathlib.Path` class combines path manipulation functions into a
class.** The `os.path` module provides free functions like `join`,
`split`, `exists`, and `isdir` that take a path string as a parameter.
The `pathlib.Path` class, introduced in Python 3.4, holds the path as a
field and provides the same operations as methods
([pathlib documentation](https://docs.python.org/3/library/pathlib.html),
verified 2026-08-13). This is the refactoring applied to the standard
library, and it is the example Fowler uses in the second edition.

## 10. Consequences

Positive.

- Data and operations are colocated, which makes the coupling visible and
  reduces the risk of a caller passing the wrong data.
- The class boundary provides encapsulation: the internal representation can
  change without affecting callers, because callers interact through methods.
- The class can enforce invariants at construction, rejecting invalid data
  before any method is called.
- The class can be tested as a unit, with all methods tested against the
  same fixture.

Negative.

- Callers must construct an instance before calling methods, which is more
  ceremony than calling a free function.
- The class holds state, which means the object must be managed: created,
  passed, and potentially cleaned up.
- In languages with value semantics, the class must be immutable to avoid
  aliasing bugs, and immutability means every operation allocates a new
  instance.
- The refactoring can be over applied, turning every set of related
  functions into a class even when the functions are stateless utilities that
  do not benefit from encapsulation.

## 11. Failure modes and misuse

**Class with one method.** The refactoring is applied to a single function
that takes a parameter, producing a class with one field and one method. The
class adds ceremony without benefit, because there are no other functions to
colocate. The symptom is a class that exists only to wrap one function, and
the caller's code is longer than the free function version for no
behavioural gain.

**Mutable class with aliasing.** The class is mutable, and a caller holds a
reference that another caller also holds. A mutation from one caller is
visible to the other, producing the same aliasing bug the refactoring was
supposed to prevent. The symptom is a shared mutation bug in a class that
was created to prevent shared mutation, which is the ironic failure mode of
applying the refactoring without the immutability contract.

**Class that is a namespace.** The functions are grouped into a class, but
the class has no state. Every method takes all its data as parameters, and
the constructor is empty or takes nothing. The class is a namespace, not a
data abstraction, and the refactoring has added a class boundary without
colocating data. The symptom is a class that could be a module or a set of
static methods, and the instance provides no value.

**Over encapsulation.** The class hides its data so thoroughly that callers
cannot access information they need. The refactoring went too far in
encapsulation, and the class now requires a method for every piece of data a
caller might want, which is a class that is all interface and no data. The
symptom is a class with dozens of accessor methods, each returning a piece
of the internal state, and the encapsulation is providing no real
protection.

## 12. Trade-off matrix

| Alternative | Data ownership | State | Encapsulation | When to prefer |
|---|---|---|---|---|
| Combine Functions into Class | Class owns the data | Instance holds state | Enforced by class boundary | Functions share data and need a home |
| Combine Functions into Transform | Pipeline owns nothing | Stateless | None | Functions form a pipeline, not a shared data owner |
| Introduce Parameter Object | Caller owns the data | Parameter object is state | None | Parameter list is long, grouping is enough |
| Encapsulate Record | Class owns the data | Mutable or immutable | Enforced | Data is a record that needs methods |

## 13. Related and incompatible patterns

**Combine Functions into Transform** (same catalog) is the alternative when
the functions form a pipeline rather than sharing data. In a pipeline, each
function takes the output of the previous and produces input for the next,
and the correct structure is a chain of calls, not a class with methods.
This refactoring and that one are the two ways to combine functions, and
the choice depends on whether the functions share data or form a pipeline.

**Introduce Parameter Object** (same catalog) groups related parameters into
a single value object, which reduces the parameter count. It is
complementary: the parameter object can become the data field of the class
created by Combine Functions into Class.

**Extract Class** (same catalog) splits a class into two, which is the
inverse direction. Combine Functions into Class merges free functions into a
class, and Extract Class splits a class into two smaller ones.

**Encapsulate Record** (same catalog) wraps a data structure in a class,
which is the same operation as Combine Functions into Class when the
functions are getters and setters on a record.

## 14. Refactoring path in and out

**Path in.** The refactoring is introduced by creating a class and moving
each function into it. The steps are:

1. Identify the shared parameter that the functions take.
2. Create a class with a constructor that takes the shared parameter and
   stores it as a field.
3. For each function, create a method on the class that reads the field
   instead of taking the parameter.
4. Update each call site to construct the class and call the method on the
   instance.
5. Run the test suite. Any failure means a call site was missed or a
   method reads the field incorrectly.
6. Delete the old free functions, or keep them as delegating shims for
   backward compatibility if they are part of a public API.

**Path out.** The refactoring is reversed by Extract Class or by converting
the methods back to free functions. The reverse is applied when the class
turns out to have low cohesion, meaning the methods do not actually share
data, or when the class is a namespace that should be a module.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test that called a free function should now call the equivalent method on a
constructed instance and should produce the same result. A test failure
means either a method was not converted correctly or a call site was missed.

A new test should verify that the class rejects invalid data at
construction, if the class was given validation logic. This test did not
exist before the refactoring, because the free functions could not reject
invalid data before it was passed.

A test that checks the class's immutability, if the class was made
immutable, should attempt to mutate a field and verify that the attempt
fails to compile or throws at runtime. This test guards against a future
change that reintroduces mutability.

## 16. Observability signals

The refactoring does not change behaviour, so the observable signal in
production is nothing. The class produces the same outputs for the same
inputs. If production observability changes, the refactoring was not a
pure structural change, and the difference is the signal that a behaviour
change was introduced alongside the structural change.

The one observable difference is in allocation profiling, because
constructing a class instance allocates an object where a free function
call did not. In a profiling tool, this shows up as more short lived
allocations in the young generation. This is expected and is the cost of
the colocation benefit. If the allocation rate is unacceptable, the class
is being constructed too frequently, and the solution is to construct fewer
instances by reusing them, not to revert to free functions.

## 17. Security and privacy implications

The refactoring improves security in one specific way: the class boundary
allows validation at construction, so invalid data is rejected before any
method is called. This is a positive security signal when the data is
security relevant, for example a URL that must be validated before use, or
a permission set that must not contain wildcards.

The privacy relevant case is that the class boundary hides the internal
representation from callers, so callers cannot reach into the data
structure and extract fields that were not exposed as methods. This is a
form of data hiding that is the purpose of encapsulation, and it is
stronger than the free function model, where the data structure is visible
to every caller.

Where the refactoring is silent is in the data itself: the class does not
change what data is stored or transmitted, only where the data lives.
Data protection regulations are not affected by the refactoring, because
the data is the same data in a different container.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 8, "Combine Functions into Class."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 6, "Replace Data Value with
  Object."
- Grady Booch, *Object-Oriented Analysis and Design with Applications*,
  Benjamin Cummings, 2nd edition, 1994.
- Oracle, "java.lang.String," Java SE 21 API documentation,
  [https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/String.html](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/String.html),
  verified 2026-08-13.
- Python Software Foundation, "pathlib," Python documentation,
  [https://docs.python.org/3/library/pathlib.html](https://docs.python.org/3/library/pathlib.html),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
