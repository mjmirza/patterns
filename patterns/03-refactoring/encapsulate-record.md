---
name: Encapsulate Record
slug: encapsulate-record
family: 03-refactoring
category: Refactoring
aliases: [Encapsulate Field, Wrap Record, Replace Record with Class]
first_described: "Fowler 1999"
maturity: canonical
related: [encapsulate-collection, encapsulate-variable, extract-class, combine-functions-into-class, replace-data-value-with-object]
incompatible_with: []
verified: 2026-08-13
---

# Encapsulate Record

## 1. Name, aliases, and lineage

The canonical name is **Encapsulate Record**, introduced by Martin Fowler
in *Refactoring. Improving the Design of Existing Code*, 2nd edition,
Addison-Wesley, 2018, chapter 8, "Encapsulating Data." In the first
edition (1999), the equivalent refactoring appeared as **Encapsulate
Field** and **Replace Record with Class**, two separate entries in
chapter 8, "Organizing Data." Fowler consolidated them in the second
edition because the mechanics are the same: take a public data structure
and wrap it in a class with accessor methods.

The distinction the refactoring turns on, between a record that callers
can read and write directly and a class that controls access, is one of
the foundational ideas of object oriented programming. Grady Booch, in
*Object-Oriented Analysis and Design with Applications*, Benjamin
Cummings, 1994, describes encapsulation as the principle that the
internal structure of an abstraction is hidden and that access is
mediated by a well defined interface. Fowler's refactoring is the
mechanical path from the record structure to the encapsulated class.

The alias **Encapsulate Field** is used for the scalar variant, where a
single public field is wrapped in accessor methods. The alias **Replace
Record with Class** is used in the C and Pascal communities, where a
record is a language level data structure and the refactoring converts
it to an object.

## 2. Problem and context

You have a data record, a structure with public fields and no behaviour,
that callers read and write directly. The record was created as a passive
data holder, for example a data transfer object or a configuration
struct, but over time it has acquired implicit invariants that no code
enforces. Callers write values directly to the fields, and some of those
values violate invariants that the original author assumed but never
encoded, because the record has no methods to check them.

The situation reads like this. A `ConnectionConfig` record has public
fields `host`, `port`, `timeout`, and `retryCount`. Callers construct
the record and set the fields directly. The original author assumed that
the port is between 1 and 65535, the timeout is positive, and the retry
count is non negative. None of these invariants are enforced, because the
record is a passive struct with no constructor validation. A caller that
sets `port = 0` or `timeout = -1` produces a config that will fail at
runtime with a confusing connection error, and the root cause is an
invalid field value that no code checked.

The fix is to encapsulate the record. Make the fields private, add a
constructor that validates them, and provide getter methods (and setter
methods if needed) that enforce the invariants. Callers can no longer
write invalid values, because the constructor and setters reject them.

## 3. Forces

**Encapsulation versus convenience.** A public record is convenient for
callers: they construct it and set fields directly with no ceremony. An
encapsulated class requires callers to go through a constructor and
accessors, which is more ceremony but gives the class control. The force
favours encapsulation when the record has invariants that need enforcing
and favours the record when the data is truly passive with no invariants.

**Construction validation versus post construction checking.** A record
allows invalid values to be set, and the invalid values are only detected
when the record is used. An encapsulated class can reject invalid values
at construction, which is fail fast. The force favours encapsulation
when early failure is more valuable than construction flexibility.

**Mutability versus immutability.** A record with public fields is
mutable, and changes are visible to every holder. An encapsulated class
can be immutable, with fields set at construction and never changed,
which eliminates aliasing bugs. The force favours immutable encapsulation
when the data should not change after construction and favours mutable
encapsulation when the data needs to be updated under the class's
control.

**Data transfer versus behaviour.** A record is pure data, designed to be
serialised and transmitted. An encapsulated class has methods, which may
interfere with serialisation. The force favours the record when the data
needs to cross a boundary as pure data and favours the class when the
data needs behaviour and validation.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- The record has fields that should not take every value their type
  allows, and the invariants are not enforced because the record has no
  methods.
- Callers write invalid values to the fields, and the invalid values
  produce confusing runtime errors far from the point where the invalid
  value was set.
- The record has gained behaviour that does not belong on a passive data
  holder, and the behaviour is scattered across callers that each
  implement it independently.
- The record is shared and mutable, and callers are making defensive
  copies because they do not trust other holders not to mutate it.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The record is a pure data transfer object that carries data across a
  boundary, has no invariants, and gains no behaviour. The encapsulation
  would add methods that the serialisation layer does not expect and that
  the callers do not need.
- The record is a configuration struct that is constructed once and read
  many times, and the construction is already validated by a builder or a
  factory. The encapsulation would duplicate validation that already
  exists.
- The language provides record syntax with built in validation, for
  example Java records with compact constructors, and the built in
  mechanism already enforces the invariants the refactoring would add.
- The record is used in a context that requires the data to be
  transparent, for example a database row mapping or an API response
  model, and encapsulation would break the mapping framework's
  expectations.

## 5. Structure

The refactoring has one participant.

- **The record.** The data structure being encapsulated. Before the
  refactoring, it has public fields and no methods. After the
  refactoring, it has private fields, a validating constructor, and
  accessor methods.

## 6. ASCII structure diagram

```
  BEFORE                                  AFTER
  ------                                  -----

  record ConnectionConfig:                class ConnectionConfig:
    host: str                               _host: str   (private)
    port: int                               _port: int   (private)
    timeout: int                            _timeout: int (private)
    retryCount: int                         _retry: int   (private)

  caller:                                 constructor(host, port, timeout, retry):
    config = ConnectionConfig()                if not (1 <= port <= 65535):
    config.host = "db.example"                     raise ValueError("port")
    config.port = 0                           if timeout < 0:
    config.timeout = -1                           raise ValueError("timeout")
                                              ...

                                          getPort(): int
                                              return _port

                                          setPort(port):
                                              if not (1 <= port <= 65535):
                                                  raise ValueError
                                              _port = port
```

## 7. Dynamics

```
  t0  identify record with unenforced invariants
       |
       v
  t1  make all fields private
       |
       v
  t2  add a constructor that takes all fields
       and validates each one
       |
       v
  t3  add getter methods for each field
       |
       v
  t4  add setter methods if mutation is needed,
       with the same validation as the constructor
       |
       v
  t5  update every construction site to use
       the constructor instead of field assignment
       |
       v
  t6  update every read site to use getters
       instead of direct field access
       |
       v
  t7  run test suite
       -- every valid construction should succeed
       -- every invalid construction should fail
       |
       v
  t8  commit. the record is encapsulated.
```

## 8. Implementation variants

**Full class with constructor and accessors.** The canonical variant. All
fields are private, the constructor validates, and getters and setters
are provided. This is the variant Fowler describes in the second edition.

**Immutable class with factory.** The fields are set only at
construction, there are no setters, and a factory method performs
validation. This variant combines Encapsulate Record with the value
object contract, giving both encapsulation and immutability.

**Language record with validation.** Languages with record syntax, such
as Java records, C sharp records, or Python dataclasses, provide a
shorthand for the full class variant. The record syntax generates the
accessors, and a compact constructor or a custom `__post_init__` provides
validation. This is the preferred variant in languages that support it.

**Builder pattern.** When the record has many fields or complex
validation that depends on combinations of fields, a builder provides
fluent construction with validation at build time. This is the variant
used when the constructor parameter list is too long or when construction
is multi step.

```python
# Python: before (public fields, no validation)

from dataclasses import dataclass

@dataclass
class ConnectionConfig:
    host: str = ""
    port: int = 0
    timeout: int = 0
    retry_count: int = 0

# Python: after (encapsulated with validation)

@dataclass
class ConnectionConfig:
    host: str
    port: int
    timeout: int
    retry_count: int

    def __post_init__(self):
        if not (1 <= self.port <= 65535):
            raise ValueError(f"port must be 1-65535, got {self.port}")
        if self.timeout < 0:
            raise ValueError(f"timeout must be non-negative, got {self.timeout}")
        if self.retry_count < 0:
            raise ValueError(f"retry must be non-negative, got {self.retry_count}")
```

```typescript
// TypeScript: before (public fields)

class ConnectionConfigBefore {
    constructor(
        public host: string = "",
        public port: number = 0,
        public timeout: number = 0,
        public retryCount: number = 0
    ) {}
}

// TypeScript: after (encapsulated with validation)

class ConnectionConfig {
    private _port: number;
    private _timeout: number;
    private _retryCount: number;

    constructor(
        public readonly host: string,
        port: number,
        timeout: number,
        retryCount: number
    ) {
        if (port < 1 || port > 65535) throw new RangeError("port");
        if (timeout < 0) throw new RangeError("timeout");
        if (retryCount < 0) throw new RangeError("retryCount");
        this._port = port;
        this._timeout = timeout;
        this._retryCount = retryCount;
    }

    get port() { return this._port; }
    get timeout() { return this._timeout; }
    get retryCount() { return this._retryCount; }
}
```

```java
// Java: record with validation (Java 16+)

public record ConnectionConfig(
    String host,
    int port,
    int timeout,
    int retryCount
) {
    public ConnectionConfig {
        if (port < 1 || port > 65535)
            throw new IllegalArgumentException("port: " + port);
        if (timeout < 0)
            throw new IllegalArgumentException("timeout: " + timeout);
        if (retryCount < 0)
            throw new IllegalArgumentException("retry: " + retryCount);
    }
}
```

## 9. Known production uses

**Java records, introduced in Java 16, are the language level
implementation of this refactoring.** The Java record specification states
that records are transparent carriers of data and that the compiler
generates accessor methods, a constructor, and equality methods
automatically ([java.lang.Record documentation](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Record.html),
verified 2026-08-13). The compact constructor provides validation, which
is the mechanism the refactoring uses to enforce invariants.

**Python dataclasses with `__post_init__`** provide the same mechanism.
The `dataclass` decorator generates the constructor, and `__post_init__`
is called after the generated constructor sets the fields, which is where
validation goes. The Python documentation states that `__post_init__` is
called by the generated `__init__` method
([dataclasses documentation](https://docs.python.org/3/library/dataclasses.html#post-init-processing),
verified 2026-08-13).

## 10. Consequences

Positive.

- Invalid values are rejected at construction, which is fail fast and
  produces an error at the point where the invalid value entered the
  system.
- The class can add behaviour that is colocated with the data, which
  reduces the scattering of logic across callers.
- The internal representation can change without affecting callers,
  because they interact through accessors.
- The class can be made immutable, which eliminates aliasing and
  concurrency bugs.

Negative.

- Construction requires the constructor parameters, which is more
  ceremony than constructing a record and setting fields.
- The accessors add a method call where the record had a direct field
  read, which is a small performance cost.
- Serialisation may require additional configuration, because the
  serialisation framework needs to know how to read the private fields or
  use the accessors.
- The refactoring can be over applied, turning every data structure into
  a class even when the data has no invariants and the encapsulation adds
  no value.

## 11. Failure modes and misuse

**Validation that is too strict.** The constructor rejects values that
are technically valid for the use case, because the validation was written
for a narrower case than the record is actually used for. The symptom is
a construction failure that the caller cannot fix without relaxing the
validation, which requires changing the class.

**Validation that is too lenient.** The constructor validates some
fields but not others, and the unvalidated fields accept invalid values
that produce runtime errors later. The symptom is the same confusing
runtime error the refactoring was supposed to prevent, just for a
different field.

**Setter that bypasses validation.** A setter method is provided but
does not perform the same validation as the constructor, so a caller can
set an invalid value through the setter after construction. The symptom
is a field with an invalid value that the constructor would have rejected,
set by the setter that should have rejected it.

**Over encapsulation of a data transfer object.** The record is a DTO
that crosses a serialisation boundary, and the encapsulation adds methods
that the serialisation framework does not expect. The symptom is a
serialisation error or a silent field omission that is caused by the
private fields not being accessible to the framework.

## 12. Trade-off matrix

| Alternative | Validation | Mutability | Serialisation | When to prefer |
|---|---|---|---|---|
| Encapsulate Record | At construction | Controlled | May need config | Record has invariants to enforce |
| Encapsulate Collection | At mutation | Controlled | Same | The record contains a collection |
| Keep public record | None | Uncontrolled | Native | Data is passive, no invariants |
| Replace Record with Data Class | At construction | Immutable | Native | Language has data class syntax |
| Combine Functions into Class | None on data | Instance holds state | N/A | Functions share data, not a record |

## 13. Related and incompatible patterns

**Encapsulate Collection** (same catalog) is the collection specific
variant. Encapsulate Record wraps the whole record, and Encapsulate
Collection wraps a collection field inside the record. The two are
frequently applied together.

**Encapsulate Variable** (same catalog) is the scalar variant. It wraps
a single public variable in accessor methods, where Encapsulate Record
wraps a whole record. The mechanics are the same.

**Combine Functions into Class** (same catalog) is the next step when
the encapsulated record gains behaviour. The record is encapsulated, and
then functions that operate on the record's data are moved into the
class as methods.

**Replace Data Value with Object** (same catalog) creates the class from
a primitive value, where Encapsulate Record creates the class from a
record. The difference is the starting point: a single value vs a
multi field record.

## 14. Refactoring path in and out

**Path in.** The refactoring is introduced by making the fields private
and adding a validating constructor and accessors. The steps are:

1. Make every field of the record private.
2. Add a constructor that takes all fields as parameters.
3. Add validation to the constructor for each field that has an
   invariant.
4. Add a getter method for each field.
5. Add a setter method for each field that needs to be mutable, with the
   same validation as the constructor.
6. Update every construction site to use the constructor instead of
   field assignment.
7. Update every read site to use getters instead of direct field access.
8. Run the test suite. Any failure means a construction site was missed
   or a validation check is wrong.

**Path out.** The refactoring is reversed by making the fields public
again and removing the constructor validation. The reverse is applied
when the record is a pure data holder with no invariants and the
encapsulation is providing no value, which is the case for many DTOs.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
construction that was valid should still succeed, and every read that
worked before should produce the same value through the getter.

New tests should verify the validation. For each field with an invariant,
construct the record with a valid value and with an invalid value, and
verify that the invalid construction raises the expected exception. These
tests guard against a future change that weakens or removes the
validation.

A test that checks immutability, if the class was made immutable, should
attempt to set a field and verify that the attempt fails to compile or
throws at runtime.

## 16. Observability signals

The refactoring does not change behaviour for valid inputs, so the
observable signal in production is nothing. The one observable difference
is in error patterns: if callers were setting invalid values that
produced confusing runtime errors, those values are now rejected at
construction, and the error appears earlier and with a clearer message.
This is a positive observability signal, because the error is closer to
its root cause.

## 17. Security and privacy implications

The refactoring improves security in one specific way: the constructor
can reject values that would produce a security relevant configuration,
for example a port that allows a privileged service or a host that
resolves to an internal address. This is a positive security signal when
the record is a configuration object for a security sensitive component.

The privacy relevant case is that the encapsulation can prevent a caller
from reading a field that should not be exposed, for example a field that
contains personally identifiable information. The getter methods control
what is readable, and the absence of a getter for a sensitive field
prevents callers from reading it. This is a positive privacy signal when
the record contains mixed data with different access levels.

Where the refactoring is silent is in the data itself: the same fields are
stored with the same types, and the refactoring does not change what data
is collected or how it is persisted.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 8, "Encapsulate Record."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 8, "Encapsulate Field," "Replace
  Record with Class."
- Grady Booch, *Object-Oriented Analysis and Design with Applications*,
  Benjamin Cummings, 2nd edition, 1994.
- Oracle, "java.lang.Record," Java SE 21 API documentation,
  [https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Record.html](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Record.html),
  verified 2026-08-13.
- Python Software Foundation, "dataclasses, post-init processing,"
  [https://docs.python.org/3/library/dataclasses.html#post-init-processing](https://docs.python.org/3/library/dataclasses.html#post-init-processing),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
