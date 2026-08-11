# Family 06. Enterprise Application Architecture

Origin. Fowler, PoEAA

20 entries, 146,668 words. Every entry carries all 18
dimensions from [the entry contract](../../docs/ENTRY-TEMPLATE.md).

## Data Source Architectural

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Row Data Gateway](row-data-gateway.md) | canonical | 8,173 | A codebase has business logic that needs to read a single row from a relational table, change some of its columns, and write the row back. |
| [Table Data Gateway](table-data-gateway.md) | canonical | 7,315 | An application needs to read and write rows in a table, and the two paths that seem obvious both go wrong at scale. |

## Domain Logic

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Domain Model](domain-model.md) | canonical | 7,665 | An enterprise application accumulates business rules over its life, pricing tiers, discount eligibility, order-state transitions, tax jurisdictions, credit limits, cancellation ... |
| [Table Module](table-module.md) | established | 6,460 | A team is building a business application against a relational database using a technology stack whose native data-access layer hands back an in-memory, table-shaped structure ... |
| [Transaction Script](transaction-script.md) | canonical | 8,585 | A team is building a business application, an order system, a billing system, a claims processor, anything where the software's job is to carry out operations that a business ... |

## Object-Relational Behavioral

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Data Mapper](data-mapper.md) | canonical | 5,831 | An application has a domain model made of objects with behavior, and a relational database made of tables, rows, and columns with no behavior. |
| [Identity Map](identity-map.md) | canonical | 6,353 | An object-relational mapping layer loads rows from a database and turns them into in-memory objects. |
| [Lazy Load](lazy-load.md) | canonical | 7,284 | An object graph persisted in a relational database is, by its nature, larger than any single query needs. |
| [Unit of Work](unit-of-work.md) | canonical | 8,827 | An operation touches several objects that came from, or are destined for, a database. |

## Object-Relational Metadata Mapping Pattern

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Active Record](active-record.md) | canonical | 7,255 | An application needs to load rows from a relational table, let a caller read and mutate the fields as ordinary object properties, validate the values, and persist changes back ... |

## Object-Relational Metadata Mapping Patterns

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Association Table Mapping](association-table-mapping.md) | canonical | 5,922 | An application built with an object model needs to persist a relationship where either side can be associated with more than one instance of the other. |

## Object-Relational Structural

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Class Table Inheritance](class-table-inheritance.md) | canonical | 6,805 | A domain model built with proper object-oriented inheritance, a Player base class with Pitcher and Fielder subclasses each carrying fields the other does not need, sits naturally ... |
| [Dependent Mapping](dependent-mapping.md) | canonical | 8,415 | Data Mapper separates the in-memory domain model from the database schema by giving each persistent class a mapper responsible for moving its state to and from rows. |
| [Foreign Key Mapping](foreign-key-mapping.md) | canonical | 6,300 | An object model represents an association between two entities as a direct object reference. |
| [Serialized LOB](serialized-lob.md) | established | 6,028 | Object models are good at representing composite structures. |

## Object-Relational Structural Pattern

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Embedded Value](embedded-value.md) | canonical | 7,871 | An application's domain model routinely needs small objects that group a handful of related fields into one meaningful unit. |
| [Identity Field](identity-field.md) | canonical | 6,033 | An in-memory object system and a relational database use two different, and incompatible, notions of identity. |

## Object-Relational Structural Patterns

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Concrete Table Inheritance](concrete-table-inheritance.md) | canonical | 8,078 | An application's domain model contains a base type with several concrete subtypes, each subtype adding its own fields, and the persistence layer must map that hierarchy onto ... |
| [Inheritance Mappers](inheritance-mappers.md) | canonical | 8,397 | A domain model with an inheritance hierarchy, a base Employee class with SalariedEmployee, CommissionedEmployee, and HourlyEmployee subclasses, needs a persistence layer that can ... |
| [Single Table Inheritance](single-table-inheritance.md) | canonical | 9,071 | An object model has a natural inheritance hierarchy. |

## Reading order

Entries are independent. Each one names the patterns it composes with and
the patterns it conflicts with in dimension 13, so following those links
gives a better path than reading top to bottom.

Generated by `tools/gen-indexes.py`. Do not edit by hand.
