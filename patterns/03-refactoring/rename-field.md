---
name: Rename Field
slug: rename-field
family: 03-refactoring
category: Refactoring
aliases: [Rename Attribute, Rename Member, Rename Property]
first_described: "Fowler 2018"
maturity: canonical
related: [change-function-declaration, rename-variable, encapsulate-variable, move-field, extract-variable]
incompatible_with: []
verified: 2026-08-13
---

# Rename Field

## 1. Name, aliases, and lineage

The canonical name is **Rename Field**, introduced by Martin Fowler in
*Refactoring. Improving the Design of Existing Code*, 2nd edition,
Addison-Wesley, 2018, chapter 6, "A First Set of Refactorings." The
refactoring is new to the second edition as a separate entry, though the
broader Change Function Declaration (Rename Method in the first edition)
covered the case of renaming fields. Fowler split it out because the
mechanics differ: a field rename involves accessors, serialisation
contracts, and database column names that a method rename does not.

The underlying principle, that a field name should communicate what the
field represents, is the intention revealing names principle from Kent
Beck, *Smalltalk Best Practice Patterns*, Prentice Hall, 1997. A field
name that communicates the concept is better than one that restates the
type or the storage mechanism. The rename is the mechanical path from a
misleading name to a communicative one.

## 2. Problem and context

A field has a name that does not communicate what the field represents.
The name was accurate when the field was created, but over time the
field's meaning changed, or the name was never accurate and was chosen
for expediency. Every reader who encounters the field must determine its
real meaning, which takes time and produces misunderstandings.

The situation reads like this. A class has a field called `data` that
holds a customer's billing address. The name `data` communicates nothing
about what kind of data it is. A reader who sees `order.data` must open
the class and read the field's usage to understand that it is a billing
address. A caller that passes the field to a function must know its type
and its meaning, neither of which the name communicates.

The fix is to rename the field. Change `data` to `billingAddress`, and
update every reference. The name now communicates the concept at every
use site.

## 3. Forces

**Communication versus churn.** A better name communicates intent, but
renaming requires updating every reference. The force favours renaming
when the communication benefit exceeds the churn cost.

**Contract stability versus accuracy.** A field name that is part of a
serialisation contract or a database schema cannot be freely renamed
without breaking the contract. The force favours keeping when the field
is serialised by name, and favours renaming when the field is internal.

**Convention versus meaning.** A naming convention may require a
specific pattern, for example Hungarian notation or a prefix convention.
The force favours meaning when the convention obscures the concept, and
favours convention when the convention is load bearing for tooling.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- The field name does not communicate what the field represents, and a
  better name exists.
- The field is internal, not serialised by name, and renaming does not
  break a serialisation contract or a database schema.
- The field name was accurate but the meaning changed, and the name is
  now misleading.

**Do NOT reach for this refactoring, and treat the situation as a
non-applicability case, when the following hold.**

- The field is serialised by name, and renaming breaks the serialisation
  contract. The fix is a serialisation alias, not a rename.
- The field maps to a database column, and the column name cannot change
  without a migration. The fix is an ORM alias, not a rename.
- The field is part of a public API and consumers reference it by name.

## 5. Structure

The refactoring has one participant: the field whose name is changed.

## 6. ASCII structure diagram

```
  BEFORE                              AFTER
  ------                              -----

  class Order:                       class Order:
    data  (billing address)            billingAddress

  caller:                             caller:
    order.data                        order.billingAddress
```

## 7. Dynamics

```
  t0  identify field with misleading name
       |
       v
  t1  choose a name that communicates
       what the field represents
       |
       v
  t2  rename the field declaration
       |
       v
  t3  update every reference
       (compiler finds them in static languages)
       |
       v
  t4  update serialisation aliases
       if the field is serialised
       |
       v
  t5  run test suite
       |
       v
  t6  commit. field renamed.
```

## 8. Implementation variants

**Rename in place.** The canonical variant. The field is renamed, and
every reference is updated. A compiler finds every reference in a
statically typed language.

**Rename via accessor.** The field is private, and the rename is done
through the accessor methods. The accessor name changes, and the field
name changes internally. Callers that use the accessor are updated.

**Rename with serialisation alias.** The field is serialised by name, and
the rename is done with a serialisation alias that maps the new name to
the old serialisation name. This variant preserves the serialisation
contract.

```python
# Python: before (misleading name)

class Order:
    def __init__(self, data: str):
        self.data = data  # actually billing address

# Python: after (renamed)

class Order:
    def __init__(self, billing_address: str):
        self.billing_address = billing_address
```

```typescript
// TypeScript: before (misleading name)

class Order {
    constructor(public data: string) {} // actually billing address
}

// TypeScript: after (renamed)

class Order {
    constructor(public billingAddress: string) {}
}
```

```java
// Java: after (renamed with accessor)

public class Order {
    private String billingAddress;

    public String getBillingAddress() { return billingAddress; }
    public void setBillingAddress(String addr) { this.billingAddress = addr; }
}
```

## 9. Known production uses

**IntelliJ IDEA's "Rename Field" refactoring** automates the rename by
finding every reference and updating it, including accessors,
serialisation annotations, and database mappings
([JetBrains Rename refactoring](https://www.jetbrains.com/help/idea/rename-refactorings.html),
verified 2026-08-13).

**Java's `@JsonProperty` annotation** is the serialisation alias
mechanism. The field is renamed in Java, and the annotation maps the new
name to the old serialisation name, preserving the contract
([Jackson JsonProperty documentation](https://github.com/FasterXML/jackson-annotations),
verified 2026-08-13).

## 10. Consequences

Positive.

- The field name communicates what the field represents, which improves
  readability at every use site.
- The rename makes the concept communicable: a reviewer can say "the
  billing address is wrong" instead of "the data field is wrong."
- The compiler catches every reference in a static language, which makes
  the rename safe.

Negative.

- The rename churns the codebase, which adds lines to the diff and may
  produce merge conflicts with concurrent branches.
- If the field is serialised, the rename requires a serialisation alias,
  which adds an annotation or a configuration.
- The old name may persist in documentation, commit messages, and issue
  trackers, which creates a disconnect between the code and the docs.

## 11. Failure modes and misuse

**Renaming a serialised field without an alias.** The field is
serialised by name, and the rename breaks the contract. The symptom is
a deserialisation failure that occurs when old data is loaded.

**Renaming to a name that is only temporarily better.** The new name is
accurate today but becomes misleading when the field's meaning changes
tomorrow.

**Renaming a public API field.** The field is part of a public API and
consumers reference it by name. The rename breaks every consumer.

## 12. Trade-off matrix

| Alternative | Communication | Churn | Serialisation | When to prefer |
|---|---|---|---|---|
| Rename Field | Improved | Present | Needs alias | Name is misleading |
| Encapsulate Variable | Improved | Present | N/A | Field needs accessors |
| Change Function Declaration | N/A | Present | N/A | Function renamed |
| Keep name | None | None | None | Name is adequate |

## 13. Related and incompatible patterns

**Change Function Declaration** (same catalog) is the function version.
The field version has additional mechanics for serialisation and
database mapping.

**Rename Variable** (same catalog) is the local variable version, which
is simpler because local variables are not serialised.

**Encapsulate Variable** (same catalog) wraps the field in accessors,
which is often applied alongside the rename.

## 14. Refactoring path in and out

**Path in.** Rename the field, update references, add serialisation
aliases if needed.

**Path out.** Rename back to the old name, which is rarely applied.

## 15. Testing and verification

The test suite is the primary verification. After the refactoring, every
test should produce the same result, now through the new name.

A serialisation test should verify that old data can still be
deserialised, if the field is serialised.

## 16. Observability signals

The refactoring does not change behaviour, so the observable signal in
production is nothing. The field name in logs and traces changes, which
is a minor format change.

## 17. Security and privacy implications

The refactoring does not change what data is stored, so it does not
change the security surface. A clearer name may help a reader understand
the security implications of the field, which is a minor positive.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 6, "Rename Field."
- Kent Beck, *Smalltalk Best Practice Patterns*, Prentice Hall, 1997.
- JetBrains, "Rename refactoring,"
  [https://www.jetbrains.com/help/idea/rename-refactorings.html](https://www.jetbrains.com/help/idea/rename-refactorings.html),
  verified 2026-08-13.
- Jackson, "jackson-annotations,"
  [https://github.com/FasterXML/jackson-annotations](https://github.com/FasterXML/jackson-annotations),
  verified 2026-08-13.
- Martin Fowler, "Refactoring Catalog,"
  [https://refactoring.com/catalog/](https://refactoring.com/catalog/),
  verified 2026-08-13.
