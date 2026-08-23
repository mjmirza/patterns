---
name: Mapper
slug: mapper
family: 06-enterprise-application-architecture
category: Base Pattern, Object-Relational Behavioral
aliases: [Mapper Layer, Adapter Layer, Bridging Object]
first_described: "Fowler 2002"
maturity: canonical
related: [data-mapper, gateway, unit-of-work, identity-map, facade, adapter, metadata-mapping]
incompatible_with: []
verified: 2026-08-02
---

## 1. Name, aliases, and lineage

The pattern is named Mapper. Martin Fowler's catalog entry for it defines a
Mapper as "an object that sets up a communication between two independent
objects" (martinfowler.com/eaaCatalog/mapper.html, verified 2026-08-02), and
the full write-up sits in chapter 18 of *Patterns of Enterprise Application
Architecture* (Addison-Wesley, 2002). Fowler frames Mapper as a base pattern,
one level more general than the pattern most readers actually reach for, which
is its best known specialization, Data Mapper. Data Mapper is described on its
own catalog page as "a layer of mappers that moves data between objects and a
database while keeping them independent of each other and the mapper itself"
(martinfowler.com/eaaCatalog/dataMapper.html, verified 2026-08-02).

This entry treats Mapper as the base concept, the general habit of putting an
intermediary object between two subsystems that must not know about each
other, and treats Data Mapper as its most common instance, the persistence
case, alongside object to XML mappers, protocol translators, and the internal
DTO to domain mapping objects that ORMs and API clients build every day. Where
a claim is specific to the persistence specialization it is marked as such.

The word "mapper" is heavily overloaded in practice. AutoMapper for .NET,
MapStruct for Java, and ModelMapper all name themselves after this exact
concept and generate the translation code that a hand written Mapper class
would otherwise contain (automapper.org, verified 2026-08-02; mapstruct.org,
verified 2026-08-02). In the persistence world "mapper" is also used loosely
for the whole object relational mapping layer, which is a category error the
GoF-adjacent literature does not make. This entry keeps the two senses
distinct, the Mapper pattern is the intermediary object, an object relational
mapper is a framework that is usually built from many Mapper instances plus a
Unit of Work and an Identity Map.

Fowler does not claim to have invented the idea. He credits the general shape
to the long standing practice of writing adapter and bridging code between
subsystems that predates the catalog, and positions Mapper as the name he
gives that recurring shape so the rest of the catalog, especially Data
Mapper, Gateway, and the object relational mapping chapter, has a vocabulary
to build on (Fowler, *Patterns of Enterprise Application Architecture*,
Addison-Wesley, 2002, chapter 18 introduction). No competing name for the
general pattern is in wide circulation. Competing names exist only for its
persistence specialization, covered under Data Mapper.

## 2. Problem and context

Two subsystems need to exchange information, but neither one should hold a
compile time or a conceptual dependency on the other's shape. A domain object
should not know the column names of the table it is stored in. A REST client
should not force its domain model to mirror an upstream vendor's JSON schema.
A rules engine should not require the objects it evaluates to implement its
own marker interfaces.

The naive fix is to let one side reach into the other directly, a domain
object that knows how to `SELECT` itself, a value object with a `toVendorJson`
method baked in. This works for a small system and rots as soon as either side
needs to change on its own timeline, because now a schema migration forces a
domain model change, or a vendor API version bump forces a domain model
change, and the two concerns that should evolve at different rates are welded
together.

Mapper's context is any place where two representations of related
information exist, are owned by different parts of the system or by different
teams, and must be kept translatable without becoming coupled. The persistence
case, Data Mapper, is the most common instance because nearly every
application has a domain model and a database schema that pull apart the
moment the domain model gains behavior the schema cannot express directly, for
example a computed property, a polymorphic type, or an aggregate spanning
several tables. The same context recurs for DTO to domain translation at a
service boundary, for protocol adapters between two message formats, and for
view model construction where a UI's presentation shape differs from the
domain shape it is drawn from.

## 3. Forces

Independence versus indirection. Keeping both sides ignorant of each other is
the entire point, and it is bought at the cost of an extra object, an extra
hop, and, for a large mapping, real code volume. A system with dozens of
domain classes each needing a Mapper can end up with as much mapping code as
domain code.

Testability versus completeness. A Mapper is trivial to unit test in
isolation, feed it an object, assert the translated shape, no database, no
network, no framework needed. But a hand written Mapper is only as complete as
its author remembered to make it, and a forgotten field is a silent bug that
a compiler will not catch across two classes with a similar shape that
evolve independently.

Performance versus abstraction. Every hop through a Mapper is a function call
and, in the persistence case, potentially a query. A naive Mapper invoked once
per row in a loop reproduces the N plus 1 query problem even though the
pattern itself is not the cause, the cause is calling it at the wrong
granularity, see dimension 11.

Hand written versus generated. A Mapper can be written by hand for full
control and easy debugging, or generated by a library like MapStruct or
AutoMapper for speed of authoring and reduced human error. The trade is
compile time transparency against a generator's opinions about naming
conventions and null handling, which is a matter of judgment rather than a
settled fact and depends on how far the two shapes have already pulled apart.

## 4. Applicability and non-applicability

Reach for Mapper when the two sides genuinely must not depend on each other,
because they are owned by different teams, evolve on different release
schedules, or one of them is a domain layer that has to stay persistence
ignorant and framework ignorant to remain unit testable in isolation. Reach
for it when the shapes on the two sides are similar enough that a translation
is mechanical, a renamed field, a flattened nested object, a type coercion,
rather than requiring business rules to bridge them, in which case a
different pattern, often Adapter or a domain service, fits better.

Do not reach for Mapper in these situations, with the reason stated for each.

When the two shapes are identical and there is no independence to protect. A
Mapper that copies field for field with no renaming, no coercion, and no
reason to expect the two shapes to change on separate timelines adds a layer
of indirection that returns nothing, and a shared type or a simple constructor
is enough.

When the coupling it prevents is not actually a real risk. In a small single
team application where the domain model and the database schema are
maintained by the same two people in the same pull requests, the independence
Mapper buys costs more in code volume than the coupling it prevents would ever
cost, and Active Record is a better fit, see the incompatibility this pattern
has with that one in the trade-off matrix below.

When the translation requires real business logic rather than a structural
reshape. If producing the target representation requires applying rules,
computing derived values from multiple sources, or making a decision, that
belongs in a domain service or a dedicated use case object, not a Mapper,
because burying business rules inside translation code hides them from the
place a reader would look for business rules.

When performance is on the hot path and the mapping step is measurably the
bottleneck, in interpreted languages with reflection heavy generated mappers,
in which case a leaner hand rolled translation or a code generation approach
that emits direct field assignment, as MapStruct does at compile time rather
than through runtime reflection, is the better choice
(mapstruct.org/faq/, verified 2026-08-02, notes MapStruct's compile time
generation avoids the runtime reflection cost that reflection based mappers
like ModelMapper incur).

## 5. Structure

The pattern has three participants. A Source, the object or subsystem that
holds the information in its native shape and has no knowledge that a
translation exists. A Target, the object or subsystem that receives the
information in a different shape and likewise has no knowledge of the Source's
internal representation. A Mapper, the intermediary that knows about both
shapes, holds the translation logic, and is the only object in the
relationship coupled to both sides.

In the persistence specialization, Data Mapper, the Source is usually the
in-memory domain object, the Target is the relational representation, rows and
columns reached through a database connection, and the mapping runs in both
directions, an object to row direction on save and a row to object direction
on load. A Data Mapper commonly collaborates with an Identity Map to avoid
constructing duplicate in memory objects for the same row, and with a Unit of
Work to batch its writes, both of which are separate patterns this one
composes with rather than requires.

## 6. ASCII structure diagram

```
+-----------------------------+
| Source                      |
| (e.g. domain object, has no |
| knowledge of Target)        |
+-----------------------------+
           ^
           |
           v
+-----------------------------+
| Mapper                      |
| knows both shapes,          |
| holds the translation logic |
+-----------------------------+
           ^
           |
           v
+------------------------------+
| Target                       |
| (e.g. relational row, has no |
| knowledge of Source)         |
+------------------------------+

Mapper optionally collaborates with:

+---------------------------+  +---------------------------+
| Identity Map              |  | Unit of Work              |
| one in-memory object      |  | batches pending           |
| per row                   |  | inserts, updates, deletes |
+---------------------------+  +---------------------------+
```

## 7. Dynamics

A save flow, in the persistence specialization, runs in this order. The
caller hands the Mapper a Source object that has been changed. The Mapper
reads the Source's public state through its own accessors, never through
reflection into private internals unless the language forces that choice
(dimension 8 covers this trade-off directly). The Mapper translates that state
into the Target's shape, an SQL statement's bound parameters, or a row buffer
for a bulk writer. The Mapper hands the translated Target representation to
the persistence mechanism, a JDBC PreparedStatement, an ADO.NET command, a
Python DB-API cursor, which performs the actual write. Neither Source nor
Target participant is aware this exchange happened.

A load flow reverses the direction. The persistence mechanism returns a
result set or a row. The Mapper checks an Identity Map, when one is present,
for an already constructed Source object representing that row's primary key,
and returns the existing instance if found rather than building a duplicate.
When no cached instance exists, the Mapper constructs a new Source object and
populates it field by field from the Target's shape, again through the
Source's own accessors or constructor, never by exposing the Target's raw
columns to calling code.

```
Caller          Mapper              Target/DB           Identity Map
  |  save(src)     |                    |                    |
  |--------------->|                    |                    |
  |                |  translate(src)    |                    |
  |                |------------------->|                    |
  |                |     write row      |                    |
  |                |<-------------------|                    |
  |    load(id)    |                    |                    |
  |--------------->|   check cache(id)  |                    |
  |                |----------------------------------------->|
  |                |<-----------------------------------------|
  |                |   [hit] return cached instance            |
  |                |   [miss] query row                        |
  |                |------------------->|                    |
  |                |<-------------------|                    |
  |                |  construct + register in Identity Map     |
  |                |----------------------------------------->|
  |<---------------|                    |                    |
```

## 8. Implementation variants

Hand written explicit Mapper. A class with two named methods, one per
direction, each of which reads one shape's fields and writes the other. This
is the most transparent variant, the easiest to debug with a breakpoint, and
the one Fowler's own chapter 18 walk through builds by hand for a small
`Person` and `PersonGateway` pair (Fowler, *Patterns of Enterprise
Application Architecture*, chapter 18). It scales poorly past a modest number
of classes because every new field on either side is a manual edit on both
methods.

Reflection or convention based generic Mapper. A single Mapper implementation
that, given two class shapes, matches fields by name and type at runtime and
copies them without hand written per class code. AutoMapper for .NET is the
best known implementation of this variant, configured with a fluent API that
declares exceptions to the default name matching convention
(automapper.org, verified 2026-08-02). The cost is a runtime performance
penalty from reflection, and a class of bug where a field is silently dropped
because it does not match a naming convention rather than the mapping failing
loudly.

Compile time generated Mapper. A code generator inspects two class shapes at
build time and emits ordinary, direct field assignment code with no runtime
reflection. MapStruct for Java is the reference implementation, generating an
implementation class from an interface the developer declares, and documents
this as its core differentiator against reflection based alternatives
(mapstruct.org/faq/, verified 2026-08-02). This variant keeps the transparency
and performance of hand written code while removing the manual maintenance
burden, at the cost of a build step and a generated file the developer does
not directly author.

Metadata driven Mapper, the ORM case. Rather than hand writing or generating
per class translation code, the mapping is described declaratively, an XML
file, annotations, or a fluent configuration API, and a shared, generic Data
Mapper engine reads that metadata at runtime to perform the translation for
every mapped class. This is the shape most production object relational
mappers take and it is documented separately as its own pattern, see
Metadata Mapping, which this entry cross references rather than duplicates.

Closure or function based Mapper, in languages that make first class
functions convenient. Rather than a class with a method, the mapping is a
plain function or a pair of functions, one per direction, passed around as a
value. This variant is common in functional and functional adjacent
codebases, TypeScript and Go both favor it for simple structural translation
where a full class adds no value, and it keeps the pattern's shape, an
intermediary knowing both sides, while dropping the ceremony a class based
implementation carries in languages that do not need it.

## 9. Known production uses

MyBatis, a Java persistence framework, is documented by its own project as "a
first class persistence framework" that can "map primitives, Map interfaces
and Java POJOs to database records" through XML or annotation configured
mapper interfaces (mybatis.org/mybatis-3, verified 2026-08-02). The framework
literally names its central artifact a Mapper interface, and its own
documentation describes eliminating "almost all of the JDBC code" that a hand
rolled translation between a `ResultSet` and a Java object would otherwise
require, which is exactly the intermediary role this pattern defines.

SQLAlchemy's imperative mapping style, which the project's own documentation
calls "classical" mapping and states is "the original mapping API," lets a
developer take a plain Python class with no persistence aware base class and
associate it with a database table through an explicit `mapper()` construct,
producing a class the documentation says ends up with "an associated `Mapper`
object" regardless of whether the classical or the newer declarative style is
used (docs.sqlalchemy.org/en/20/orm/mapping_styles.html, verified 2026-08-02).
The classical style is a direct instance of the base Mapper pattern, an
intermediary object, the `Mapper` construct itself, sitting between an
otherwise persistence ignorant Python class and a `Table` object that
represents the relational shape.

Entity Framework Core's change tracking model demonstrates the same
separation at the object relational boundary from the .NET side. Microsoft's
own documentation shows plain C# classes, `Blog` and `Post`, with ordinary
properties and no persistence code, that a `DbContext` tracks, translates, and
writes to the database on `SaveChanges`, generating the SQL `UPDATE`,
`INSERT`, and `DELETE` statements shown in the documentation's own worked
example (learn.microsoft.com/en-us/ef/core/change-tracking, verified
2026-08-02). The plain classes are the Source, the relational rows are the
Target, and the `DbContext`'s internal change tracker plus its SQL generation
plays the Mapper's role of knowing both shapes so neither the domain class nor
the database schema needs to know about the other.

## 10. Consequences

Positive. Both sides of the relationship stay independently testable, a
domain object can be unit tested with no database, and a database schema can
be migrated without touching domain classes as long as the Mapper absorbs the
change. Both sides can evolve on independent schedules, which matters most
when they are owned by different teams or when one side is a third party
contract the codebase does not control. The translation logic has one home,
which makes it auditable and gives a single place to add validation,
normalization, or logging around the boundary crossing.

Negative. Every mapped pair adds an object and, in hand written variants,
real code volume that must be kept in sync by hand, which is itself a
source of bugs, a field added to one side and forgotten on the other. The
extra hop costs a measurable, if usually small, runtime overhead, and in
naive implementations invoked at the wrong granularity it becomes the root
cause of the N plus 1 query problem described in dimension 11. Debugging a
generated or reflection based Mapper is harder than debugging hand written
code, because the failure often surfaces as a silently dropped or silently
null field rather than a compile error or a thrown exception.

## 11. Failure modes and misuse

Symptom, a mapped list operation is dramatically slower than expected and the
database log shows one query per item instead of one query for the whole
list. Cause, a Mapper's load method issues its own query and is called once
per element inside a loop rather than being given a pre-fetched result set or
a batched query to translate, reproducing the N plus 1 problem even though
the pattern is not the fault by itself, the calling code's granularity is.
Fix, batch the fetch, retrieve the full result set or the full collection in
one query, then let the Mapper translate the already fetched rows in memory,
or restructure the Mapper's interface to accept a collection rather than a
single identifier.

Symptom, two objects representing the same underlying record behave
inconsistently, one has a change the other does not reflect. Cause, the
Mapper constructs a new Source instance on every load rather than checking an
Identity Map first, so multiple in memory objects exist for the same
persistent record and updates to one are invisible to the other. Fix, add or
correctly wire an Identity Map that the load path checks before constructing
a new instance, which is a separate pattern this one composes with rather
than one this pattern is required to implement itself.

Symptom, a field silently stops appearing in the saved or loaded data with no
error anywhere in the logs. Cause, a reflection or convention based generic
Mapper relies on name matching between the two shapes, and a rename on either
side breaks the match without raising any exception, the field is simply
skipped. Fix, add an explicit mapping configuration test that asserts every
declared field on both sides is covered by the mapping configuration, which
compile time generated Mappers like MapStruct catch automatically because an
unmapped target property is a build warning or error rather than a silent
runtime gap (mapstruct.org/documentation/stable/reference/html/, verified
2026-08-02, documents unmapped target property reporting).

Symptom, business rules are scattered and hard to find, a bug report about an
incorrect discount calculation leads a reader through three files before
finding the actual computation buried inside a Mapper's translation method.
Cause, the Mapper was used as a dumping ground for logic that belongs in a
domain service, because it was the one place both the input and the output
shape were visible at the same time. Fix, extract the logic into a named
domain method or service that the Mapper calls, so the Mapper's own code stays
purely structural, a discipline this pattern shares with the general single
responsibility principle rather than one that is unique to it.

## 12. Trade-off matrix

| Force | Mapper | Active Record | Direct method on the class |
|---|---|---|---|
| Keeps Source and Target ignorant of each other | Yes, by design | No, the object knows its own persistence | Partial, one side still holds the method |
| Testable without infrastructure | Yes, pure translation logic | Harder, persistence is baked into the object | Yes, but couples the class to the target shape |
| Code volume for a simple 1 to 1 field mapping | Higher, an extra class or function | Lower, no separate layer | Lower, one method |
| Handles differing shapes and independent evolution | Yes, its core strength | Poorly, schema and domain model stay coupled | Poorly, the class must change with the target |
| Where domain logic tends to end up | Kept out, if disciplined | Mixed into the domain object itself | Mixed into the domain object itself |

Active Record is the named alternative Fowler places in direct contrast, and
this entry's frontmatter marks the two as related through the family
structure rather than incompatible with each other in the strict sense, since
a codebase can use Active Record for simple, single team owned entities and
Data Mapper for the complex aggregates where independence earns its place. The
Data Mapper specialization is genuinely incompatible with Active Record within
the scope of a single class, because one class cannot at once be ignorant of
its persistence, the Mapper case, and aware of its own persistence, the
Active Record case.

## 13. Related and incompatible patterns

Data Mapper is this pattern's most common and most thoroughly documented
specialization, the persistence case, and the two are related by
specialization rather than by composition, every Data Mapper is a Mapper but
most discussions of Mapper in production code are really discussions of Data
Mapper specifically.

Gateway composes with Mapper in the persistence case, a Gateway wraps the raw
external API, a JDBC connection or an HTTP client, and a Mapper sits above it
translating between the domain shape and the Gateway's native shape, so the
two patterns split the concern of talking to the outside world from the
concern of translating its shape.

Unit of Work and Identity Map compose with Data Mapper specifically, a Unit
of Work batches the writes a Mapper produces so they commit together, and an
Identity Map is consulted by a Mapper's load path to avoid constructing
duplicate in memory objects for one persistent record, as shown in dimension
7's dynamics.

Facade is a near neighbor worth distinguishing. A Facade simplifies a complex
subsystem's interface without necessarily translating its data shape, while a
Mapper's entire purpose is the translation of shape, a system can need one
without the other, and a system with both often layers a Facade in front of a
subsystem and a Mapper behind it translating that subsystem's native
representation into the caller's domain shape.

Adapter, from the Gang of Four catalog, is the closest general purpose
relative outside the enterprise catalog. Both patterns place an intermediary
between two incompatible interfaces. The distinction Fowler draws is that
Mapper specifically emphasizes keeping both sides wholly unaware of the
translation's existence, including unaware of each other's existence at all,
where a classic Adapter is more often deliberately wrapped around one known,
named interface to make it conform to another known, named interface the
client already expects (Fowler, *Patterns of Enterprise Application
Architecture*, chapter 18, distinguishes Mapper from Adapter along this line).

## 14. Refactoring path in and out

Introducing a Mapper into code that currently has none starts from the
symptom, a domain class with method names like `save`, `load`, or `toRow`
sitting directly on it, or persistence framework attributes decorating a
domain class. The first step is to identify every place that currently calls
those methods or relies on that coupling. The second step is to create the
new Mapper class or function and move the translation logic into it as is,
without changing behavior, which mirrors the general Extract Class refactoring
described in Fowler's refactoring catalog applied specifically to a
persistence or serialization concern. The third step is to update every
caller identified in the first step to go through the new Mapper instead of
calling the domain object's own persistence methods, and the fourth step is
to remove the persistence methods and any framework decoration from the
domain class once no caller depends on them directly.

Removing a Mapper, when the independence it protects has stopped mattering,
for example the domain model and the schema are now maintained together in
lockstep and separate evolution was never actually exercised, follows the
reverse path. Inline the Mapper's translation logic directly onto the class it
was mapping, verify no other consumer depended on the Mapper as a separate,
substitutable seam, for example a test double that swapped in a fake Mapper,
and then delete the now empty Mapper class. This direction should be taken
with care, because removing the seam removes the independence it bought, and
that decision belongs to whoever owns the schema and domain model boundary,
not to a mechanical refactor alone.

## 15. Testing and verification

A Mapper's core strength for testing is that its correctness can be verified
with a plain object equality assertion, given a Source instance with known
field values, translate it, and assert the Target has the expected shape, no
database connection, no network call, and no test double for the persistence
mechanism is required for this class of test. The reverse direction, Target
to Source, is tested the same way, given a row or a response payload, assert
the constructed Source object has the expected field values.

What becomes harder to test in isolation is the interaction between the
Mapper and its collaborators, an Identity Map's caching behavior or a Unit of
Work's batching, which require either an in memory fake implementation of
those collaborators or an integration test against a real, disposable
database, commonly an in process SQLite instance or a containerized instance
of the production database engine started per test run. A generic reflection
or convention based Mapper additionally needs a completeness test, a test
that iterates the declared fields on both shapes and asserts every one is
covered by the mapping, because the failure mode described in dimension 11,
a silently dropped field, does not surface through a simple assertion on a
single example instance unless that example happens to populate every field.

## 16. Observability signals

For a hand written or compile time generated Mapper, observability is mostly
about what surrounds it rather than the Mapper itself, since a well behaved
Mapper is a pure function with nothing to log beyond its caller's own
tracing. Log or trace the number of translation calls per logical operation,
because a spike from one call to N calls for what should be a single batch
operation is the concrete, observable symptom of the N plus 1 misuse
described in dimension 11.

For a reflection or metadata driven Mapper, a healthy instance shows a stable,
low, and roughly constant per call cost in a latency histogram, because
reflection cost does not usually depend on the specific instance's field
values. A degrading instance, one whose configuration was recently changed,
often shows either a step change in that per call latency, indicating the
mapping strategy changed for example from a cached to an uncached reflection
path, or a rising count of a specific warning log line the mapping framework
emits for unmapped or ambiguous fields, which is the operational counterpart
of the silently dropped field failure mode and should be treated as a signal
worth acting on rather than routine noise.

## 17. Security and privacy implications

A Mapper is a natural, and easy to overlook, place for a sensitive field to
leak across a boundary it should never cross, because the mapping is often
written once, by name matching convention, and never revisited when a new
field is added to either side. A reflection or convention based generic
Mapper is the highest risk variant here specifically because it will
happily map a newly added field, for example a password hash or an internal
audit column added to a domain object, into an outbound API response shape
the moment the field names happen to match, with no explicit developer
decision required for that field to cross the boundary.

The mitigating discipline is to make outbound mapping opt in rather than opt
out wherever the Target crosses a trust boundary, an explicit allowlist of
fields to include, rather than an implicit allowlist of fields to exclude,
so that a newly added sensitive field on the Source defaults to absent from
the Target until a developer deliberately adds it. This is an analytical
implication rather than one drawn from a named incident or a cited advisory,
and it is stated as judgment.

## 18. References

1. Martin Fowler, *Patterns of Enterprise Application Architecture*,
   Addison-Wesley, 2002, chapter 18, "Base Patterns," Mapper section.
2. Martin Fowler, Mapper catalog page.
   https://martinfowler.com/eaaCatalog/mapper.html, verified 2026-08-02.
3. Martin Fowler, Data Mapper catalog page.
   https://martinfowler.com/eaaCatalog/dataMapper.html, verified 2026-08-02.
4. AutoMapper project site, description of convention based object to object
   mapping for .NET. https://automapper.org, verified 2026-08-02.
5. MapStruct project site and FAQ, compile time code generated mapping for
   Java. https://mapstruct.org/faq/, verified 2026-08-02.
6. MapStruct reference documentation, unmapped target property reporting.
   https://mapstruct.org/documentation/stable/reference/html/, verified
   2026-08-02.
7. MyBatis project home page, description of the framework as a persistence
   framework mapping Java objects and Maps to database records through
   Mapper interfaces. https://mybatis.org/mybatis-3, verified 2026-08-02.
8. SQLAlchemy 2.0 ORM documentation, mapping styles, classical and imperative
   mapping section. https://docs.sqlalchemy.org/en/20/orm/mapping_styles.html,
   verified 2026-08-02.
9. Microsoft Learn, EF Core change tracking documentation, worked example
   with plain `Blog` and `Post` classes and generated SQL.
   https://learn.microsoft.com/en-us/ef/core/change-tracking/, verified
   2026-08-02.

## Code examples

### TypeScript, a closure based Mapper between a domain object and an API DTO

```typescript
interface Customer {
  id: string;
  fullName: string;
  emailAddress: string;
  loyaltyPoints: number;
}

interface CustomerResponseDto {
  customerId: string;
  name: string;
  email: string;
}

function toCustomerResponseDto(source: Customer): CustomerResponseDto {
  return {
    customerId: source.id,
    name: source.fullName,
    email: source.emailAddress,
  };
}

function fromCustomerRequestDto(
  dto: { customerId: string; name: string; email: string },
  existingLoyaltyPoints: number,
): Customer {
  return {
    id: dto.customerId,
    fullName: dto.name,
    emailAddress: dto.email,
    loyaltyPoints: existingLoyaltyPoints,
  };
}

const domainCustomer: Customer = {
  id: "cus_100",
  fullName: "Grace Hopper",
  emailAddress: "grace@example.com",
  loyaltyPoints: 42,
};

const outbound = toCustomerResponseDto(domainCustomer);
console.log(outbound);
```

### Python, an explicit Mapper class between a domain object and a database row

```python
from dataclasses import dataclass
from typing import Any


@dataclass
class Invoice:
    invoice_id: int
    customer_name: str
    total_cents: int
    is_paid: bool


class InvoiceRowMapper:
    """Translates between an Invoice domain object and a row shape.
    Neither Invoice nor the row dict knows this class exists."""

    def to_row(self, source: Invoice) -> dict[str, Any]:
        return {
            "id": source.invoice_id,
            "customer": source.customer_name,
            "total": source.total_cents,
            "paid": 1 if source.is_paid else 0,
        }

    def from_row(self, row: dict[str, Any]) -> Invoice:
        return Invoice(
            invoice_id=row["id"],
            customer_name=row["customer"],
            total_cents=row["total"],
            is_paid=bool(row["paid"]),
        )


def main() -> None:
    mapper = InvoiceRowMapper()
    invoice = Invoice(1, "Ada Lovelace", 4599, False)
    row = mapper.to_row(invoice)
    round_tripped = mapper.from_row(row)
    assert round_tripped == invoice
    print(row)


if __name__ == "__main__":
    main()
```

### Go, a struct based Mapper between an internal model and a wire format

```go
package main

import "fmt"

type Order struct {
	OrderID     string
	CustomerRef string
	LineTotal   int64
}

type OrderWireFormat struct {
	ID       string `json:"id"`
	Customer string `json:"customer"`
	AmountUS int64  `json:"amount_us_cents"`
}

type OrderMapper struct{}

func (OrderMapper) ToWire(source Order) OrderWireFormat {
	return OrderWireFormat{
		ID:       source.OrderID,
		Customer: source.CustomerRef,
		AmountUS: source.LineTotal,
	}
}

func (OrderMapper) FromWire(source OrderWireFormat) Order {
	return Order{
		OrderID:     source.ID,
		CustomerRef: source.Customer,
		LineTotal:   source.AmountUS,
	}
}

func main() {
	mapper := OrderMapper{}
	order := Order{OrderID: "ord_9", CustomerRef: "cus_100", LineTotal: 1299}
	wire := mapper.ToWire(order)
	roundTripped := mapper.FromWire(wire)
	if roundTripped != order {
		panic("mapper round trip mismatch")
	}
	fmt.Printf("%+v\n", wire)
}
```

Java and Rust are omitted from this entry's runnable samples because the
pattern's shape is fully demonstrated by the three languages above, one
closure based, one class based, one struct and method based, and adding a
fourth or fifth language would repeat the same translation logic without
showing a variant this entry has not already covered. Java's idiomatic
variant, the MapStruct compile time generated interface, is documented in
dimension 8 rather than hand duplicated here, since its generated code is
close in shape to the Go example's methods and would not add a new lesson.
