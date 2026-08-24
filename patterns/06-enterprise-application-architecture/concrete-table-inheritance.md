---
name: Concrete Table Inheritance
slug: concrete-table-inheritance
family: 06-enterprise-application-architecture
category: Object-Relational Structural Patterns
aliases: [CTI, Table Per Concrete Type, TPC, Leaf Table Inheritance]
first_described: "Fowler 2002"
maturity: canonical
related: [single-table-inheritance, class-table-inheritance, active-record, foreign-key-mapping, layer-supertype, identity-field]
incompatible_with: [single-table-inheritance, class-table-inheritance]
verified: 2026-08-02
---

# Concrete Table Inheritance

## 1. Name, aliases, and lineage

The canonical name is Concrete Table Inheritance, one of the three inheritance
mapping patterns catalogued in Martin Fowler's *Patterns of Enterprise
Application Architecture*, Addison-Wesley, 2002, ISBN 0-321-12742-0, in the
Object-Relational Structural Patterns group. Fowler's own online catalog page
states the definition plainly, calling it a pattern that "represents an
inheritance hierarchy of classes with one table per concrete class in the
hierarchy" (Fowler, *Patterns of Enterprise Application Architecture*, online
catalog, https://martinfowler.com/eaaCatalog/concreteTableInheritance.html,
verified 2026-08-02). The same page names its most common alternate name,
**leaf table inheritance**, because in the overwhelming majority of real
hierarchies the tables correspond to the leaf classes of the tree, the
classes that are actually instantiated. The page is careful to note that the
technique also applies to concrete classes that are not leaves, a class that
both has subclasses and is itself directly instantiated, though that shape is
rarer in practice.

**Table Per Concrete Type**, usually abbreviated **TPC**, is the name used in
the .NET Entity Framework Core ecosystem, where it sits alongside Table Per
Hierarchy (TPH, Fowler's Single Table Inheritance) and Table Per Type (TPT,
Fowler's Class Table Inheritance) as one of three selectable inheritance
mapping strategies (Microsoft Learn, "Inheritance", EF Core documentation,
https://learn.microsoft.com/en-us/ef/core/modeling/inheritance, verified
2026-08-02). The Microsoft documentation describes the TPC strategy directly,
stating that "all the types are mapped to individual tables. Each table
contains columns for all properties on the corresponding entity type," and it
adds a consequence worth carrying into this entry's own consequences section
verbatim, "TPC database schemas are denormalized." The same document notes
that no table is created for an abstract type in the hierarchy, only for
concrete types, which is the origin of the acronym's middle letter.

In the SQLAlchemy Python ORM the pattern is exposed through two declarative
mixin classes, `ConcreteBase` and `AbstractConcreteBase`, and the project's
own documentation frames the entire strategy under the heading "concrete table
inheritance," describing it as a mapping where "each type of class is
represented by independent tables" (SQLAlchemy, "Mapping Class Inheritance
Hierarchies", https://docs.sqlalchemy.org/en/20/orm/inheritance.html, verified
2026-08-02). SQLAlchemy's own prose is unusually blunt for vendor
documentation about the pattern's cost, calling it "much more complicated
than joined or single table inheritance, and much more limited in
functionality," a warning this entry returns to under Consequences and
Failure Modes.

Two things deserve separation on first read, because both are sources of
confusion in real code review.

- **Concrete Table Inheritance is not the same idea as simply writing three
  unrelated tables that happen to share a few column names.** The pattern
  exists only when an object-oriented supertype relationship is present in
  the domain model, the shared fields are genuinely inherited fields, and the
  application's persistence layer is deliberately choosing to duplicate those
  shared columns into every concrete table rather than factor them into a
  common table. Three tables that coincidentally both have a `name` column
  because two different teams independently needed a name are not an
  instance of this pattern, they are coincidental schema overlap.
- **Concrete Table Inheritance is the ONLY one of Fowler's three inheritance
  patterns that leaves no trace of the hierarchy in the schema itself.**
  Single Table Inheritance leaves a discriminator column. Class Table
  Inheritance leaves foreign key relationships between the tables that mirror
  the class hierarchy. Concrete Table Inheritance leaves nothing, a database
  administrator looking only at the schema, with no access to the
  application source, cannot recover the fact that `Cats`, `Dogs`, and
  `FarmAnimals` once shared a common `Animal` supertype. This is both the
  pattern's chief attraction, because each table is self-contained and reads
  like ordinary denormalised data, and its chief liability, because the
  hierarchy exists only in code and must be reconstructed by convention.

## 2. Problem and context

An application's domain model contains a base type with several concrete
subtypes, each subtype adding its own fields, and the persistence layer must
map that hierarchy onto tables in a relational database that has no native
representation of inheritance. This is the identical starting problem shared
by all three of Fowler's inheritance mapping patterns, and Concrete Table
Inheritance is one of three competing answers, not a standalone technique
invented in isolation.

The concrete situation looks like this. A payments domain has a
`PaymentMethod` base concept with three subtypes, `CreditCardPayment`,
`BankTransferPayment`, and `PayPalPayment`. Each subtype has entirely
different fields, a credit card has a masked PAN and an expiry month, a bank
transfer has an IBAN and a BIC, a PayPal payment has an email and a payer ID.
There is very little that is genuinely shared beyond an amount, a currency,
and a timestamp. Crucially, in this scenario, the application rarely if ever
queries across all three subtypes at once. A reconciliation job for credit
card payments only ever touches `CreditCardPayment` rows. A settlement report
for bank transfers only ever touches `BankTransferPayment` rows. Polymorphic
queries that ask for every payment regardless of kind, sorted by timestamp,
are rare, exceptional, or entirely absent from the application's actual query
patterns.

This is the context in which Concrete Table Inheritance is the right choice
and its two siblings are not. When most queries are subtype-specific and
polymorphic base-type queries are rare, a table per concrete type that
contains every field that subtype needs, with no join and no discriminator
filter, is the cheapest possible read path for the common case. The
uncommon polymorphic query, when it does occur, pays for itself with a `UNION
ALL` across the concrete tables, and that cost is accepted because it is
paid rarely.

The same context, inverted, is exactly why the pattern is wrong when
polymorphic querying is frequent. If the application regularly needs every
payment for a merchant regardless of kind, that query becomes an N-way union
across every concrete table, every time, and the cost that Concrete Table
Inheritance was designed to avoid on the common path is instead paid on every
request. Fowler's catalog entry and the EF Core team's own guidance both
converge on the same shape of advice here, defaulting to Single Table
Inheritance or Class Table Inheritance and reaching for Concrete Table
Inheritance specifically when the query profile consists mostly of
single-type access (Microsoft Learn, "Inheritance", op. cit., stating "TPC is
also a good mapping strategy to use when your code will mostly query for
entities of a single leaf type").

## 3. Forces

The forces at play are the same six that govern the whole inheritance mapping
family, but Concrete Table Inheritance sits at a distinctive point in the
space.

**Read performance for subtype-scoped queries versus read performance for
polymorphic queries.** This is the deciding force and the one that decides
whether the pattern applies at all. A query scoped to one concrete type is as
fast as a query against any ordinary, non-inherited table, because there is
genuinely no join, no discriminator filter, and no wasted columns. A
polymorphic query across the base type must union every concrete table, and
that union grows linearly with the number of subtypes and does not benefit
from an index that spans tables, because no such index can exist.

**Schema clarity versus schema duplication.** Every column shared by two or
more subtypes is physically repeated in every one of their tables. A schema
change to a shared field, adding a `NOT NULL` constraint to `amount`, for
example, must be applied identically to every concrete table by hand or by a
migration tool that understands the convention, because the database itself
enforces no relationship that says the columns must stay in sync. This is the
direct, unavoidable cost of leaving no trace of the hierarchy in the schema,
as described in dimension 1.

**Storage cost versus normalisation.** The pattern denormalises by design,
and Microsoft's own EF Core documentation says so in one sentence, "TPC
database schemas are denormalized" (Microsoft Learn, op. cit.). Storage is
rarely the binding constraint on modern hardware, but the columns are
genuinely duplicated in the schema definition even when a given row uses only
a fraction of them, which never happens here because every column in a
concrete table is genuinely used by that concrete type, unlike Single Table
Inheritance where most rows carry many `NULL` columns.

**Referential integrity versus flexibility of primary keys.** Because rows
for different concrete subtypes live in different tables, a foreign key that
needs to point at any payment regardless of kind cannot be enforced by an
ordinary database foreign key constraint, because a foreign key constraint
names exactly one target table. EF Core's own TPC documentation states this
directly, noting that for a relationship like a favourite animal that can be
any concrete subtype, "this means an FK constraint cannot be created for this
relationship" (Microsoft Learn, op. cit.). This is a genuine, structural
sacrifice the pattern makes, not an incidental inconvenience.

**Primary key generation across independent tables.** When each subtype has
its own table with its own identity column or its own sequence, so that no
two rows across the whole hierarchy ever collide on a key value, which
matters the moment a polymorphic foreign key or a polymorphic cache needs to
reference a specific payment without knowing in advance which table it lives
in, the design requires either a single shared sequence used by every
concrete table, or application-generated globally unique identifiers. EF
Core solves this by default with one database sequence shared across every
table in the hierarchy on databases that support sequences (Microsoft Learn,
op. cit.). This is a real coordination cost the other two inheritance
patterns do not carry, because in both of them exactly one physical location
produces the canonical row and its key.

**Cognitive load for the next engineer.** Because the hierarchy is invisible
in the schema, a new team member reading the database directly, without
reading the ORM mapping code, has no way to discover that `CreditCardPayment`
and `BankTransferPayment` are siblings under a common concept. This is a real
and lasting cost that the other two patterns do not impose, since a
discriminator column or a foreign key relationship both announce the
hierarchy to anyone looking at the schema.

## 4. Applicability and non-applicability

Reach for Concrete Table Inheritance when the following hold together, not
in isolation.

- The application's actual query load consists mostly of queries scoped to
  a single concrete subtype, and polymorphic base-type queries are rare,
  exceptional, or entirely absent. This is the single decisive factor and
  every other consideration below is secondary to it.
- Each concrete subtype has enough of its own fields that a shared base
  table, as Class Table Inheritance would produce, would force every read of
  a single subtype to pay for a join it does not conceptually need.
- The concrete subtypes are stable and few in number, so the maintenance cost
  of manually keeping shared columns synchronised across every table stays
  bounded. A hierarchy with three or four leaf types is comfortable. A
  hierarchy with twenty is not, regardless of query pattern.
- The team already accepts, or actively wants, denormalised, per-type tables
  that read cleanly as ordinary standalone tables to any tool, report, or
  analyst that queries the database directly, with no ORM in the loop.
- No relational database foreign key constraint is required from another
  table toward the base concept as a whole, only toward specific concrete
  subtypes. Foreign keys that target one named concrete table work
  perfectly under this pattern.

Do NOT reach for Concrete Table Inheritance in these cases, and the reason
matters more than the rule.

- **Polymorphic queries against the base type are common.** The union-based
  read path this pattern requires for a base-type query is its most
  expensive operation, and a design that pays that expensive cost on the
  common path has chosen the wrong one of Fowler's three patterns. Reach for
  Single Table Inheritance or Class Table Inheritance instead.
- **A relational foreign key constraint from another table must be able to
  point at any row in the hierarchy regardless of concrete subtype.** This
  requirement cannot be satisfied by Concrete Table Inheritance at the
  database level at all, because no single target table exists to reference.
  Class Table Inheritance, where every subtype row also has a corresponding
  base table row, is the correct choice when this constraint matters.
- **The hierarchy is deep, with three or more levels, or wide, with many
  concrete leaf types.** The manual duplication of shared columns across
  every leaf table becomes an operational burden that scales with the
  number of leaves, not the depth of the tree.
- **Fields shared across subtypes change schema frequently.** Every such
  change requires a coordinated migration across every concrete table, and
  a database that enforces no structural relationship between those tables
  gives the team no safety net if one table's migration is missed.
- **The team wants the schema itself to communicate the domain's
  inheritance relationships.** Concrete Table Inheritance is, by design,
  invisible at the schema level to anyone inspecting the database directly,
  for example a data analyst writing ad hoc SQL, a reporting tool, or a
  future engineer with no access to the ORM's mapping configuration.
- **Reflection or metaprogramming based dynamic dispatch across the
  hierarchy is expected to be cheap.** Because there is no shared identity
  space at the database level, code that materialises a heterogeneous
  mixed-type collection from a single query must build and maintain a
  `UNION ALL` itself, whether by hand or through an ORM feature built for
  the purpose.

## 5. Structure

- **Abstract or base concept.** The shared conceptual supertype exists only
  in the object model and in application code. It has no corresponding
  database table. Its fields exist logically but are physically duplicated
  wherever a concrete subtype needs them.
- **Concrete class.** Each instantiable subtype in the hierarchy. Each one
  owns exactly one table, and that table contains every column the subtype
  needs, both the columns it declares itself and the columns it inherits
  from the shared base concept.
- **Concrete table.** The physical table backing one concrete class. Its
  primary key is drawn from a key space that must not collide with the
  primary keys of sibling concrete tables, whether by a shared sequence, by
  globally unique identifiers, or by an application-managed key allocator.
- **Union view or query-time union.** The mechanism, whether a database
  `VIEW` built from `UNION ALL`, or an ORM feature that constructs the
  equivalent query dynamically, used the rare times a polymorphic,
  base-type-scoped read is required. SQLAlchemy's `ConcreteBase` builds
  exactly this union automatically once every concrete mapped class is
  defined (SQLAlchemy, op. cit.).
- **Mapper or repository per concrete type.** The persistence-layer
  component responsible for reading and writing rows of exactly one concrete
  table. Because there is no shared table, there is no natural place for a
  single mapper to serve the whole hierarchy the way a Class Table
  Inheritance mapper naturally can, so most implementations of this pattern
  end up with one mapper per concrete class, coordinated by a thin dispatch
  layer above them.

## 6. ASCII structure diagram

```
+-----------------------------------------+
| PaymentMethod, in-memory only, no table |
| + amount                                |
| + currency                              |
| + createdAt                             |
+-----------------------------------------+
     ^ extended by three subclasses
     |
+-------------------+
| CreditCardPayment |
| + maskedPan       |
| + expiryMonth     |
+-------------------+
     |
     v
+------------------------------------------+
| credit_card_payments TABLE               |
| id PK seq, amount, currency, created_at, |
| masked_pan, expiry_month                 |
+------------------------------------------+

+---------------------+
| BankTransferPayment |
| + iban              |
| + bic               |
+---------------------+
     |
     v
+------------------------------------------------+
| bank_transfer_payments TABLE                   |
| id PK seq, amount, currency, created_at, iban, |
| bic                                            |
+------------------------------------------------+

+---------------+
| PayPalPayment |
| + payerEmail  |
| + payerId     |
+---------------+
     |
     v
+------------------------------------------+
| paypal_payments TABLE                    |
| id PK seq, amount, currency, created_at, |
| payer_email, payer_id                    |
+------------------------------------------+

No table exists for PaymentMethod. No foreign key
connects the three concrete tables to one another. The
shared columns amount, currency, and created_at are
physically duplicated in every table.
```

## 7. Dynamics

```
Write path, a single concrete subtype, the common and cheap case.

  Application code
        |
        | new CreditCardPayment(amount, currency, maskedPan, expiryMonth)
        v
  CreditCardPaymentRepository.save(payment)
        |
        | allocate id from the shared hierarchy sequence
        | (or from a partitioned per-table sequence, per the key
        |  generation variants in dimension 8)
        v
  INSERT INTO credit_card_payments
    (id, amount, currency, created_at, masked_pan, expiry_month)
  VALUES (?, ?, ?, ?, ?, ?)
        |
        v
  Single INSERT into a single table. No join. No discriminator write.


Read path, subtype-scoped, the common and cheap case.

  Application code
        |
        | find credit card payments for a merchant
        v
  CreditCardPaymentRepository.findByMerchant(merchantId)
        |
        v
  SELECT id, amount, currency, created_at, masked_pan, expiry_month
    FROM credit_card_payments
   WHERE merchant_id = ?
        |
        v
  Single SELECT against a single table. As fast as any ordinary table read.


Read path, polymorphic, the rare and expensive case.

  Application code
        |
        | find every payment for a merchant, any kind
        v
  PaymentMethodRepository.findAllByMerchant(merchantId)
        |
        v
  SELECT id, amount, currency, created_at, 'card' AS kind
    FROM credit_card_payments  WHERE merchant_id = ?
  UNION ALL
  SELECT id, amount, currency, created_at, 'transfer' AS kind
    FROM bank_transfer_payments  WHERE merchant_id = ?
  UNION ALL
  SELECT id, amount, currency, created_at, 'paypal' AS kind
    FROM paypal_payments  WHERE merchant_id = ?
        |
        v
  Result rows are materialised back into the correct concrete class by
  the kind discriminator column that exists ONLY in the query result,
  never in any stored table.
```

## 8. Implementation variants

**Manual repository-per-subtype, with a hand-written union for the
polymorphic path.** This is the variant most teams that do not use a
full-featured ORM end up with by default, and it is honest about the
pattern's true cost, because the union query is visible in the code and must
be maintained by hand whenever a subtype is added or removed.

**ORM-managed union view, built and maintained by the mapping framework.**
SQLAlchemy's `ConcreteBase` and `AbstractConcreteBase` both build this union
automatically, generating it once at mapper configuration time from every
concrete class registered against the base (SQLAlchemy, op. cit.). This
removes the maintenance burden of hand-writing the union at the cost of
depending on the ORM's own polymorphic-loading machinery, which SQLAlchemy's
own documentation warns is the most limited of its three inheritance
strategies.

**Database-level `UNION ALL` view, materialised as a real view object.**
Rather than letting the ORM or the application build the union query at read
time, the union is defined once as a database view, and any tool, including
ones outside the application entirely, can query the view directly. This
trades a small amount of schema visibility back, since the view itself does
announce that the tables are related, for the operational convenience of a
single, centrally maintained union definition rather than one scattered
across application code.

**Shared sequence for cross-table key uniqueness.** EF Core's default TPC key
generation strategy creates a single database sequence and has every concrete
table's identity column draw its next value from that one sequence, which
guarantees no two rows across the whole hierarchy ever collide on a primary
key value even though the rows live in physically separate tables
(Microsoft Learn, op. cit.). This is the cleanest solution when the target
database supports sequences.

**Globally unique identifiers instead of a shared sequence.** When the
target database does not support sequences, or when key generation must be
possible entirely client-side with no round trip to the database, UUIDs
generated by the application before the insert avoid the coordination
problem altogether, at the cost of a larger, less naturally ordered primary
key.

**Per-subtype identity columns with a manually partitioned offset.**
EF Core's documentation also describes an alternative where each concrete
table's identity column is configured with a distinct seed and increment
chosen so that the ranges of values produced by each table's identity
generator can never overlap, for example a seed of one and an increment of
four for the first table, a seed of two and the same increment for the
second, and so on (Microsoft Learn, op. cit.). The same document flags the
operational cost of this approach directly, noting it "makes it harder to
add derived types later as it requires the total number of types in the
hierarchy to be known beforehand."

## 9. Known production uses

**Entity Framework Core, .NET, Table Per Concrete Type mapping strategy.**
EF Core exposes TPC as a directly selectable, first-class mapping strategy
via `UseTpcMappingStrategy()`, alongside TPH and TPT, and Microsoft's own
documentation states the strategy creates one table per concrete class with
no table at all for any abstract class in the hierarchy, showing the
mapping with a worked `Animal`, `Pet`, `Cat`, `Dog`, `FarmAnimal`, `Human`
example that produces exactly one table per concrete leaf, `Cats`, `Dogs`,
`FarmAnimals`, and `Humans` (Microsoft Learn, "Inheritance", EF Core
documentation, https://learn.microsoft.com/en-us/ef/core/modeling/inheritance,
verified 2026-08-02).

**SQLAlchemy, Python, `ConcreteBase` and `AbstractConcreteBase`.**
SQLAlchemy's declarative ORM ships two mixin base classes purpose-built for
this exact pattern, both under the section heading "concrete table
inheritance" in its own documentation, one that requires an explicit table
for the base class and one, `AbstractConcreteBase`, that permits the base
class to have no table of its own at all, matching Fowler's original
definition precisely (SQLAlchemy, "Mapping Class Inheritance Hierarchies",
https://docs.sqlalchemy.org/en/20/orm/inheritance.html, verified 2026-08-02).

**Django, Python, abstract base model classes.** Django's `Meta.abstract =
True` mechanism produces exactly the schema shape this pattern describes.
Django's own documentation states plainly that an abstract base model "will
then not be used to create any database table," and that when a concrete
model inherits from it, the abstract base's fields "will be added to those
of the child class," so that each concrete Django model ends up with its own
independent table containing both its own fields and the fields it inherited
from the shared, table-less abstract base (Django Software Foundation,
"Models, Abstract base classes",
https://docs.djangoproject.com/en/5.1/topics/db/models/#abstract-base-classes,
verified 2026-08-02). This is the single most widely deployed instance of
Concrete Table Inheritance in the Python ecosystem, since Django's own
`AbstractUser`, and countless third-party reusable app base models, are
built on exactly this convention.

## 10. Consequences

**Positive.**

- Every single-subtype query is as fast as an ordinary, non-inherited table
  query, with no join, no discriminator filter, and no wasted work scanning
  columns that belong to a sibling type.
- The schema for any one concrete table is self-describing and reads
  cleanly to any tool that queries it directly, with no need to understand
  an ORM's inheritance mapping conventions to make sense of the columns.
- Storage per row is exactly proportional to the fields that row's own
  concrete type actually uses, with none of the sparse, mostly-`NULL`
  columns that Single Table Inheritance produces for every subtype-specific
  field.
- Adding a brand new concrete subtype is a purely additive schema change, a
  new table, that touches none of the existing tables and risks no
  regression to any existing subtype's queries.
- A foreign key from another table to one specific, known concrete subtype
  can be enforced by an ordinary database foreign key constraint with no
  special handling.

**Negative.**

- Polymorphic, base-type-scoped queries require a `UNION ALL` across every
  concrete table, a cost that grows with the number of subtypes and cannot
  benefit from a single cross-table index, as SQLAlchemy's own documentation
  states directly, warning the strategy "produces very large queries with
  UNIONS that won't perform as well as simple joins" (SQLAlchemy, op. cit.).
- Shared fields are physically duplicated in every concrete table, and the
  database enforces no relationship that keeps those duplicated definitions
  in sync, so a schema change to a shared field must be applied by hand, or
  by tooling that understands the convention, to every concrete table
  individually. Microsoft's documentation calls the resulting schema
  "denormalized" without qualification (Microsoft Learn, op. cit.).
- A relational foreign key constraint cannot target the hierarchy as a
  whole, only one named concrete table, which forces either giving up
  referential integrity for polymorphic relationships or building an
  application-level integrity check to replace what the database would
  otherwise enforce for free.
- Primary key generation requires explicit coordination, a shared sequence,
  globally unique identifiers, or partitioned identity ranges, none of which
  is needed under Single Table Inheritance or Class Table Inheritance, where
  a single physical location naturally owns key generation for the whole
  hierarchy.
- The inheritance relationship is invisible in the schema itself, so any
  reader who inspects the database directly, without also reading the
  application's mapping code, has no way to discover that the tables were
  ever related.

## 11. Failure modes and misuse

This dimension is largely engineering judgement, drawn from the trade-offs
Fowler and the SQLAlchemy and EF Core documentation each name explicitly, and
from the general shape of bugs that this class of denormalised mapping
predictably produces.

**Symptom.** A shared field's schema constraint, for example a `NOT NULL`
requirement on `currency`, silently differs between two of the concrete
tables, and rows that should be invalid according to the domain model are
found in production data. **Cause.** Because no database mechanism ties the
concrete tables together, a migration that adds or tightens a constraint on a
shared column was applied to some tables and missed on others, and nothing
at the database level flagged the inconsistency. **Fix.** Generate every
migration to a shared field programmatically from a single source of truth,
whether a migration-generation tool, a code-generation step over the shared
base type definition, or a checklist enforced by a repository policy that
requires every migration touching a shared field name to list every concrete
table by name.

**Symptom.** A polymorphic report or dashboard that queries every payment
becomes progressively slower as new payment methods are added over time,
with no single query having grown, and no obvious regression in any one
table. **Cause.** The `UNION ALL` behind the polymorphic query grows by one
more branch for every new concrete subtype, and because the union has no
shared index to lean on, the database must execute, sort, and merge every
branch independently. **Fix.** Recognise that the query pattern has drifted
away from what Concrete Table Inheritance was chosen for, per dimension 4,
and either migrate to Class Table Inheritance for the base concept, or
maintain a dedicated, denormalised reporting table populated by triggers or
an event stream specifically for the polymorphic read path, so the
transactional write path is not forced to carry the union's cost.

**Symptom.** Two rows in different concrete tables share the same primary
key value, and a cache, a log correlation, or an audit trail that assumed
identifiers were unique across the whole hierarchy silently merges or
overwrites unrelated records. **Cause.** Each concrete table was given its
own independent identity column with no coordination, most commonly because
the team adopted Concrete Table Inheritance without reading, or without
applying, the key-generation guidance that every serious treatment of the
pattern gives, and each table's auto-increment column happily started from
one. **Fix.** Adopt a single shared sequence across every concrete table in
the hierarchy, matching EF Core's own default TPC behaviour, or switch to
globally unique identifiers generated before insert, and add a test that
asserts no two rows across any two concrete tables ever share a key.

**Symptom.** A foreign key column that should reference any payment is found,
on data audit, to contain identifier values that do not correspond to any
row in any of the concrete tables. **Cause.** No database foreign key
constraint could be created for this relationship in the first place, since
Concrete Table Inheritance structurally cannot support a foreign key that
targets more than one table, and the application-level check that was
supposed to substitute for the missing database constraint was either never
written or has a bug that allows an invalid reference through, exactly the
risk EF Core's own documentation names when it says the FK column will
contain valid values only "as long as the application does not attempt to
insert invalid data" (Microsoft Learn, op. cit.). **Fix.** Treat the
application-level integrity check as a load-bearing piece of the persistence
layer, cover it with the same seriousness of test coverage a database
constraint would otherwise receive for free, and consider whether the
relationship in question is common enough that Class Table Inheritance,
which does support this foreign key natively, would be the better base
pattern.

**Symptom.** A new engineer, reading the database schema directly with no
access to the ORM mapping layer, cannot explain why `credit_card_payments`,
`bank_transfer_payments`, and `paypal_payments` all carry an identically
named and typed `amount`, `currency`, and `created_at` column, and assumes
the repetition is accidental duplication rather than a deliberate mapping
decision. **Cause.** This is not a bug, it is the pattern's structural cost
described in dimension 1, that Concrete Table Inheritance leaves no trace of
the hierarchy anywhere in the schema. **Fix.** Document the inheritance
relationship explicitly, in a schema-adjacent artefact such as a data
dictionary, a comment on each table, or a generated diagram, rather than
relying on the ORM's mapping code as the only source of truth for a fact
about the schema that a schema-only reader has no way to recover.

## 12. Trade-off matrix

| Force | Concrete Table Inheritance | Single Table Inheritance | Class Table Inheritance |
|---|---|---|---|
| Single-subtype read speed | Fastest, no join, no filter | Fast, requires a discriminator filter on an indexed column | Slower, requires a join to the base table |
| Polymorphic base-type read speed | Slowest, requires a UNION ALL across every subtype table | Fastest, a single SELECT with an optional discriminator filter | Moderate, a single join across base and subtype tables |
| Schema visibility of the hierarchy | None, invisible without reading application code | High, a discriminator column names every subtype | High, foreign keys mirror the class hierarchy |
| Storage per row | Minimal, no unused columns | Wasteful, many NULL subtype-specific columns per row | Minimal, columns live only in their owning table |
| Referential integrity for a base-type foreign key | Not possible with a native FK constraint | Trivial, one target table for the whole hierarchy | Trivial, the base table is a valid FK target |
| Primary key coordination across subtypes | Requires an explicit shared sequence or GUIDs | Trivial, one table, one key space | Trivial, the base table owns the key |
| Cost of adding a new subtype | Additive, a new table, no changes to siblings | Additive, new nullable columns on one wide table | Additive, a new table plus a foreign key to the base |
| Cost of changing a shared field | High, must be repeated by hand across every subtype table | Low, one column change on one table | Low, one column change on the base table |

## 13. Related and incompatible patterns

**Single Table Inheritance** and **Class Table Inheritance** are this
pattern's two direct siblings within Fowler's own inheritance-mapping family,
and all three answer the identical problem from dimension 2. They are
structurally incompatible with one another for the same class hierarchy at
the same time, since a hierarchy is mapped by exactly one of the three
strategies, though a large application with many independent hierarchies is
free to choose a different one of the three for each hierarchy according to
that hierarchy's own query profile, and this is common in practice, EF Core
itself allows different hierarchies within one `DbContext` to each pick a
different one of TPH, TPT, or TPC.

**Active Record** and **Data Mapper** are the two persistence-layer patterns
that most commonly sit above whichever inheritance strategy is chosen, and
Concrete Table Inheritance composes cleanly with either. Under Active Record,
each concrete class owns its own save and load logic directly, matching the
one-table-per-class shape naturally. Under Data Mapper, a mapper per
concrete class is the natural unit, with a thin coordinating layer above
them for the rare polymorphic read, exactly the shape shown in the dynamics
diagram in dimension 7.

**Identity Field** is a prerequisite this pattern depends on directly, and
the primary key coordination cost described throughout dimensions 3, 8, and
11 is specifically the cost of applying Identity Field correctly across
multiple independent tables that must nonetheless share one logical
identifier space.

**Layer Supertype** is a closely related idea at the object-model level
rather than the database level. A base class that supplies common behaviour
to every concrete payment type, without that base class itself needing a
database table, is Layer Supertype applied to the in-memory hierarchy this
pattern maps, and the two frequently appear together, since the base class
that has no table under Concrete Table Inheritance is very often exactly the
kind of shared, behaviour-only supertype that Layer Supertype describes.

**Foreign Key Mapping** is the pattern this entry's Applicability section
points toward whenever a real relational foreign key to the base concept as
a whole is required, since Foreign Key Mapping presupposes a single target
table to reference, which only Class Table Inheritance among the three
sibling patterns naturally provides.

## 14. Refactoring path in and out

**Introducing the pattern into code that does not yet have it.** The typical
starting point is a single wide table that already carries the smell Single
Table Inheritance produces when misapplied, many columns that are `NULL` for
most rows because they belong conceptually to only one of several subtypes
that were never formally separated. The refactoring proceeds in small,
reversible steps. First, identify the true concrete subtypes hiding inside
the wide table by grouping columns that are populated together and null
together. Second, create one new table per identified concrete subtype,
containing both the shared columns and that subtype's own columns, and
backfill each new table from the old wide table with an `INSERT INTO ...
SELECT` filtered by whatever condition currently distinguishes the subtype,
often an existing informal type column. Third, cut the application's read
and write paths over to the new per-subtype tables one subtype at a time,
keeping the old wide table as a read-only fallback until every code path is
migrated, verified, and the old table is finally dropped. This is the same
expand-and-contract discipline used for any live schema migration, applied
specifically to the moment a hierarchy is extracted from a previously
undifferentiated table.

**Removing the pattern once query patterns change.** The clearest signal
that Concrete Table Inheritance has stopped earning its place is exactly the
failure mode described in dimension 11, a polymorphic query that was once
rare becoming common. The refactoring path out is the mirror image of the
path in. Introduce a new base table matching either Single Table Inheritance
or Class Table Inheritance, whichever the new query profile favours, migrate
data from every existing concrete table into the new shape, cut reads over
to the new shape incrementally, verified query by query, and only then
retire the old concrete tables. Because Concrete Table Inheritance leaves no
schema trace of the hierarchy, this migration must be planned entirely from
the application's mapping code, since the schema itself offers no shortcut
or hint about which tables were related.

## 15. Testing and verification

Testing code built on Concrete Table Inheritance is, for the common case,
genuinely simpler than testing either of its two siblings, because a test
against one concrete type's repository is a test against one ordinary,
non-inherited table with no discriminator or join to reason about, and this
is one of the pattern's real, if under-advertised, benefits.

What becomes harder to test is precisely the polymorphic path and the
cross-table invariants the database itself does not enforce. A test suite
covering this pattern responsibly includes, at minimum, one test per
concrete subtype exercising its own save and load path in isolation, exactly
as it would for any plain table-backed class. It also needs an explicit test
that asserts primary key uniqueness holds across every concrete table
simultaneously, since this is the one invariant the database will not check
on this pattern's behalf, by inserting rows into two or more concrete tables
in the same test and asserting no key collision is possible given the
chosen key generation strategy from dimension 8. It needs a test of the
polymorphic union query itself, asserting that a row inserted into any one
concrete table is discoverable through the union path and correctly
materialised back into its concrete class, since this is the logic most
likely to silently drift out of sync as new subtypes are added, exactly the
first failure mode in dimension 11. Finally, whenever a shared field exists
across subtypes, a schema-level test that walks every concrete table and
asserts the shared field's type, nullability, and constraints are identical
across all of them catches the second failure mode in dimension 11 before it
reaches production data, since nothing else in the stack will catch it
automatically.

## 16. Observability signals

A healthy instance of this pattern shows a query plan for every
subtype-scoped read that touches exactly one table, with no join and no
filter cost beyond the query's own natural predicates, and the query
latency for that path should be indistinguishable from an equivalent
non-inherited table's latency, which is the whole point of choosing this
pattern in the first place. Query plan monitoring or slow-query logs that
show a rising count of multi-table `UNION` queries against tables known to
be part of a Concrete Table Inheritance hierarchy is the earliest and
clearest signal that the query profile assumption behind the original choice
has changed, since a rising union frequency is exactly the condition
described in dimension 11's second failure mode.

Row count growth per concrete table, tracked individually rather than as an
aggregate across the hierarchy, is a useful signal specifically because
there is no shared table where an aggregate count would be trivially
available, and a dashboard that has to sum three or four independent row
counts to answer how many payments exist is itself a visible symptom of the
schema-invisibility cost from dimension 10.

Primary key allocation should be monitored per sequence, or per key
generator, whichever key strategy from dimension 8 was chosen, with an alert
on any observed collision or any gap in the expected monotonic ordering
across tables, since a collision here is silent at write time and only
surfaces later as data corruption in whatever consumed the colliding key.

## 17. Security and privacy implications

This dimension is engineering judgement drawn from how the pattern's
structural properties interact with common data-protection requirements,
rather than a sourced claim about any specific vendor.

Because each concrete subtype's data lives in its own physically separate
table, this pattern offers a genuine, structural convenience for data that
carries different sensitivity levels by subtype. If, in the payments example
from dimension 2, `CreditCardPayment` rows carry PCI-scoped data and
`BankTransferPayment` rows do not, table-level access controls, encryption
at rest configured per table, or table-level audit logging can each be
applied to exactly the table that needs them, with no risk of a broader
polymorphic query accidentally surfacing the sensitive subtype's columns to
a caller that only asked for the less sensitive one, since a query against
`bank_transfer_payments` structurally cannot return a `masked_pan` value,
that column does not exist in that table at all.

The inverse of this same property is the risk in a right-to-erasure or
data-subject-access request workflow. Because the hierarchy is invisible in
the schema, per dimension 10, a deletion or export process that walks tables
by name must be kept in sync by hand with every concrete table the
hierarchy currently has, and a newly added concrete subtype that is not
added to that process's table list will silently be excluded from erasure
or export requests, which is a compliance risk this pattern's structural
invisibility makes more likely than under Single Table Inheritance, where
one table and one discriminator-scoped query naturally covers every subtype
by construction. Any team adopting this pattern for data subject to
erasure or export obligations should treat the list of concrete tables
belonging to a hierarchy as a maintained, tested artefact, not an implicit
fact inferred from application code.

## 18. References

- Fowler, Martin. *Patterns of Enterprise Application Architecture*,
  Addison-Wesley, 2002, ISBN 0-321-12742-0. Object-Relational Structural
  Patterns group, "Concrete Table Inheritance" catalog entry.
- Fowler, Martin. "Concrete Table Inheritance", online catalog for
  *Patterns of Enterprise Application Architecture*,
  https://martinfowler.com/eaaCatalog/concreteTableInheritance.html,
  verified 2026-08-02.
- Microsoft Learn. "Inheritance", EF Core documentation,
  https://learn.microsoft.com/en-us/ef/core/modeling/inheritance,
  verified 2026-08-02. Source for the Table Per Concrete Type mapping
  strategy, its default key generation via a shared sequence, the
  denormalised-schema characterisation, and the guidance on when TPC is
  preferable to TPH and TPT.
- SQLAlchemy. "Mapping Class Inheritance Hierarchies",
  https://docs.sqlalchemy.org/en/20/orm/inheritance.html, verified
  2026-08-02. Source for the `ConcreteBase` and `AbstractConcreteBase`
  declarative helpers and the documentation's own characterisation of
  concrete table inheritance as more complex and more limited than its
  sibling strategies.
- Django Software Foundation. "Models, Abstract base classes",
  https://docs.djangoproject.com/en/5.1/topics/db/models/#abstract-base-classes,
  verified 2026-08-02. Source for Django's abstract base model behaviour, no
  table for the abstract base, fields copied into each concrete child's own
  table.

## Code examples

Three languages are shown. TypeScript and Python because both are the
languages most commonly reaching for this pattern by hand outside a
full-featured ORM, and Go because Go's lack of inheritance at the language
level makes the pattern's essential shape, independent repositories per
concrete type unified only by a shared interface, unusually clear to read.
Java is omitted here because a fourth, fully worked example added no new
structural idea beyond what TypeScript, Python, and Go already demonstrate,
and the repository's code budget is better spent on depth in prose than on a
fourth repetition of the same shape.

### TypeScript

```typescript
interface PaymentMethod {
  id: number;
  amount: number;
  currency: string;
  createdAt: Date;
  kind: string;
}

interface CreditCardPayment extends PaymentMethod {
  kind: "card";
  maskedPan: string;
  expiryMonth: number;
}

interface BankTransferPayment extends PaymentMethod {
  kind: "transfer";
  iban: string;
  bic: string;
}

class KeyAllocator {
  private next = 1;
  allocate(): number {
    return this.next++;
  }
}

class CreditCardTable {
  private rows = new Map<number, CreditCardPayment>();
  constructor(private keys: KeyAllocator) {}

  save(input: Omit<CreditCardPayment, "id" | "kind">): CreditCardPayment {
    const row: CreditCardPayment = { id: this.keys.allocate(), kind: "card", ...input };
    this.rows.set(row.id, row);
    return row;
  }

  findById(id: number): CreditCardPayment | undefined {
    return this.rows.get(id);
  }

  all(): CreditCardPayment[] {
    return [...this.rows.values()];
  }
}

class BankTransferTable {
  private rows = new Map<number, BankTransferPayment>();
  constructor(private keys: KeyAllocator) {}

  save(input: Omit<BankTransferPayment, "id" | "kind">): BankTransferPayment {
    const row: BankTransferPayment = { id: this.keys.allocate(), kind: "transfer", ...input };
    this.rows.set(row.id, row);
    return row;
  }

  findById(id: number): BankTransferPayment | undefined {
    return this.rows.get(id);
  }

  all(): BankTransferPayment[] {
    return [...this.rows.values()];
  }
}

function findAllPayments(cards: CreditCardTable, transfers: BankTransferTable): PaymentMethod[] {
  return [...cards.all(), ...transfers.all()].sort((a, b) => a.createdAt.getTime() - b.createdAt.getTime());
}

const sharedKeys = new KeyAllocator();
const cardTable = new CreditCardTable(sharedKeys);
const transferTable = new BankTransferTable(sharedKeys);

const card = cardTable.save({
  amount: 4200,
  currency: "EUR",
  createdAt: new Date("2026-08-01T10:00:00Z"),
  maskedPan: "0000000000004242",
  expiryMonth: 12,
});

const transfer = transferTable.save({
  amount: 9900,
  currency: "EUR",
  createdAt: new Date("2026-08-02T09:30:00Z"),
  iban: "DE89370400440532013000",
  bic: "COBADEFFXXX",
});

const scoped = cardTable.findById(card.id);
if (!scoped || scoped.kind !== "card") {
  throw new Error("subtype scoped read failed");
}

const all = findAllPayments(cardTable, transferTable);
if (all.length !== 2 || all[0].id === all[1].id) {
  throw new Error("polymorphic read invariant failed");
}

console.log(`credit card row ${JSON.stringify(card)}`);
console.log(`bank transfer row ${JSON.stringify(transfer)}`);
console.log(`polymorphic union produced ${all.length} rows with distinct keys`);
```

### Python

```python
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import count
from typing import Iterator


class KeyAllocator:
    def __init__(self) -> None:
        self._counter = count(start=1)

    def allocate(self) -> int:
        return next(self._counter)


@dataclass
class CreditCardPayment:
    id: int
    amount: int
    currency: str
    created_at: datetime
    masked_pan: str
    expiry_month: int
    kind: str = "card"


@dataclass
class BankTransferPayment:
    id: int
    amount: int
    currency: str
    created_at: datetime
    iban: str
    bic: str
    kind: str = "transfer"


class CreditCardTable:
    def __init__(self, keys: KeyAllocator) -> None:
        self._keys = keys
        self._rows: dict[int, CreditCardPayment] = {}

    def save(self, amount: int, currency: str, created_at: datetime,
              masked_pan: str, expiry_month: int) -> CreditCardPayment:
        row = CreditCardPayment(
            id=self._keys.allocate(), amount=amount, currency=currency,
            created_at=created_at, masked_pan=masked_pan, expiry_month=expiry_month,
        )
        self._rows[row.id] = row
        return row

    def find_by_id(self, row_id: int) -> CreditCardPayment | None:
        return self._rows.get(row_id)

    def all(self) -> Iterator[CreditCardPayment]:
        return iter(self._rows.values())


class BankTransferTable:
    def __init__(self, keys: KeyAllocator) -> None:
        self._keys = keys
        self._rows: dict[int, BankTransferPayment] = {}

    def save(self, amount: int, currency: str, created_at: datetime,
              iban: str, bic: str) -> BankTransferPayment:
        row = BankTransferPayment(
            id=self._keys.allocate(), amount=amount, currency=currency,
            created_at=created_at, iban=iban, bic=bic,
        )
        self._rows[row.id] = row
        return row

    def find_by_id(self, row_id: int) -> BankTransferPayment | None:
        return self._rows.get(row_id)

    def all(self) -> Iterator[BankTransferPayment]:
        return iter(self._rows.values())


def find_all_payments(cards: CreditCardTable, transfers: BankTransferTable) -> list:
    combined = list(cards.all()) + list(transfers.all())
    return sorted(combined, key=lambda row: row.created_at)


def main() -> None:
    shared_keys = KeyAllocator()
    card_table = CreditCardTable(shared_keys)
    transfer_table = BankTransferTable(shared_keys)

    card = card_table.save(
        amount=4200, currency="EUR",
        created_at=datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc),
        masked_pan="0000000000004242", expiry_month=12,
    )
    transfer = transfer_table.save(
        amount=9900, currency="EUR",
        created_at=datetime(2026, 8, 2, 9, 30, tzinfo=timezone.utc),
        iban="DE89370400440532013000", bic="COBADEFFXXX",
    )

    scoped = card_table.find_by_id(card.id)
    assert scoped is not None and scoped.kind == "card", "subtype scoped read failed"

    all_payments = find_all_payments(card_table, transfer_table)
    ids = {row.id for row in all_payments}
    assert len(all_payments) == 2 and len(ids) == 2, "polymorphic read invariant failed"

    print(f"credit card row {card}")
    print(f"bank transfer row {transfer}")
    print(f"polymorphic union produced {len(all_payments)} rows with distinct keys {sorted(ids)}")


if __name__ == "__main__":
    main()
```

### Go

```go
package main

import (
	"fmt"
	"sort"
	"sync"
	"time"
)

type PaymentMethod interface {
	Identifier() int
	When() time.Time
	Kind() string
}

type KeyAllocator struct {
	mu   sync.Mutex
	next int
}

func NewKeyAllocator() *KeyAllocator {
	return &KeyAllocator{next: 1}
}

func (k *KeyAllocator) Allocate() int {
	k.mu.Lock()
	defer k.mu.Unlock()
	id := k.next
	k.next++
	return id
}

type CreditCardPayment struct {
	ID          int
	Amount      int
	Currency    string
	CreatedAt   time.Time
	MaskedPan   string
	ExpiryMonth int
}

func (p CreditCardPayment) Identifier() int { return p.ID }
func (p CreditCardPayment) When() time.Time { return p.CreatedAt }
func (p CreditCardPayment) Kind() string    { return "card" }

type BankTransferPayment struct {
	ID        int
	Amount    int
	Currency  string
	CreatedAt time.Time
	IBAN      string
	BIC       string
}

func (p BankTransferPayment) Identifier() int { return p.ID }
func (p BankTransferPayment) When() time.Time { return p.CreatedAt }
func (p BankTransferPayment) Kind() string    { return "transfer" }

type CreditCardTable struct {
	keys *KeyAllocator
	rows map[int]CreditCardPayment
}

func NewCreditCardTable(keys *KeyAllocator) *CreditCardTable {
	return &CreditCardTable{keys: keys, rows: map[int]CreditCardPayment{}}
}

func (t *CreditCardTable) Save(amount int, currency string, createdAt time.Time, maskedPan string, expiryMonth int) CreditCardPayment {
	row := CreditCardPayment{ID: t.keys.Allocate(), Amount: amount, Currency: currency, CreatedAt: createdAt, MaskedPan: maskedPan, ExpiryMonth: expiryMonth}
	t.rows[row.ID] = row
	return row
}

func (t *CreditCardTable) FindByID(id int) (CreditCardPayment, bool) {
	row, ok := t.rows[id]
	return row, ok
}

func (t *CreditCardTable) All() []PaymentMethod {
	out := make([]PaymentMethod, 0, len(t.rows))
	for _, row := range t.rows {
		out = append(out, row)
	}
	return out
}

type BankTransferTable struct {
	keys *KeyAllocator
	rows map[int]BankTransferPayment
}

func NewBankTransferTable(keys *KeyAllocator) *BankTransferTable {
	return &BankTransferTable{keys: keys, rows: map[int]BankTransferPayment{}}
}

func (t *BankTransferTable) Save(amount int, currency string, createdAt time.Time, iban string, bic string) BankTransferPayment {
	row := BankTransferPayment{ID: t.keys.Allocate(), Amount: amount, Currency: currency, CreatedAt: createdAt, IBAN: iban, BIC: bic}
	t.rows[row.ID] = row
	return row
}

func (t *BankTransferTable) All() []PaymentMethod {
	out := make([]PaymentMethod, 0, len(t.rows))
	for _, row := range t.rows {
		out = append(out, row)
	}
	return out
}

func findAllPayments(tables ...[]PaymentMethod) []PaymentMethod {
	var combined []PaymentMethod
	for _, t := range tables {
		combined = append(combined, t...)
	}
	sort.Slice(combined, func(i, j int) bool {
		return combined[i].When().Before(combined[j].When())
	})
	return combined
}

func main() {
	sharedKeys := NewKeyAllocator()
	cardTable := NewCreditCardTable(sharedKeys)
	transferTable := NewBankTransferTable(sharedKeys)

	card := cardTable.Save(4200, "EUR", time.Date(2026, 8, 1, 10, 0, 0, 0, time.UTC), "0000000000004242", 12)
	transfer := transferTable.Save(9900, "EUR", time.Date(2026, 8, 2, 9, 30, 0, 0, time.UTC), "DE89370400440532013000", "COBADEFFXXX")

	scoped, ok := cardTable.FindByID(card.ID)
	if !ok || scoped.Kind() != "card" {
		panic("subtype scoped read failed")
	}

	all := findAllPayments(cardTable.All(), transferTable.All())
	seen := map[int]bool{}
	for _, row := range all {
		if seen[row.Identifier()] {
			panic("polymorphic read invariant failed, duplicate key")
		}
		seen[row.Identifier()] = true
	}
	if len(all) != 2 {
		panic("polymorphic read invariant failed, wrong row count")
	}

	fmt.Printf("credit card row %+v\n", card)
	fmt.Printf("bank transfer row %+v\n", transfer)
	fmt.Printf("polymorphic union produced %d rows with distinct keys\n", len(all))
}
```
