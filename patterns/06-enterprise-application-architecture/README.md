# Family 06. Enterprise Application Architecture

Origin. Fowler, PoEAA

56 entries, 371,725 words, 4 more planned, 60 total when the family is complete. Every entry carries all 18
dimensions from [the entry contract](../../docs/ENTRY-TEMPLATE.md).

## Base Pattern

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Layer Supertype](layer-supertype.md) | canonical | 8,735 | An enterprise application is organized into layers, most often domain logic, data source access, and presentation, and each layer accumulates many sibling types over the life of ... |
| [Money](money.md) | canonical | 8,631 | A system that touches prices, balances, fees, taxes, discounts, refunds, or payroll needs to represent a quantity of currency and do arithmetic on it. |
| [Value Object](value-object.md) | canonical | 8,405 | A domain concept, an amount of money, a date range, a phone number, a geographic coordinate, a color, has more than one primitive field and a rule about how those fields combine ... |

## Base Pattern, Object-Relational Behavioral

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Mapper](mapper.md) | canonical | 5,386 | Two subsystems need to exchange information, but neither one should hold a compile time or a conceptual dependency on the other's shape. |

## Base Patterns

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Client Session State](client-session-state.md) | canonical | 7,810 | HTTP, as originally specified, is a stateless request-response protocol. |
| [Database Session State](database-session-state.md) | canonical | 7,361 | A web application needs to remember something about a user across more than one HTTP request, a shopping cart, an authenticated identity, a wizard's partial answers, a rate-limit ... |
| [Gateway](gateway.md) | canonical | 7,526 | An application needs to talk to something outside its own object model. |
| [Registry](registry.md) | canonical | 7,696 | An object, buried several calls deep inside a request, a batch job, or a background worker, needs something it was not given directly. |
| [Separated Interface](separated-interface.md) | canonical | 7,304 | A component in one part of a system needs to call a component in another part, but the natural, obvious dependency direction is backward from where the architecture wants it to be. |
| [Service Stub](service-stub.md) | canonical | 7,445 | An enterprise system routinely depends on a service it does not own and cannot fully control. |
| [Special Case](special-case.md) | canonical | 7,750 | A piece of client code asks a collaborator for information and then has to decide what to do about a boundary condition before it can use the answer. |

## Concurrency

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Coarse-Grained Lock](coarse-grained-lock.md) | canonical | 7,165 | An object graph in an enterprise application is rarely a single row. |
| [Implicit Lock](implicit-lock.md) | canonical | 6,735 | Optimistic Offline Lock and Pessimistic Offline Lock both solve the problem of detecting or preventing conflicting concurrent business transactions, but both share a second ... |
| [Optimistic Offline Lock](optimistic-offline-lock.md) | canonical | 6,892 | A business transaction in an enterprise application often spans more than one system transaction. |
| [Pessimistic Offline Lock](pessimistic-offline-lock.md) | canonical | 7,612 | A business transaction in an enterprise application routinely spans more than one system-level request. |

## Data Source Architectural

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Query Object](query-object.md) | canonical | 9,035 | An application needs to ask its data source for a set of objects that satisfy some condition, and the condition is not known ahead of time. |
| [Row Data Gateway](row-data-gateway.md) | canonical | 8,173 | A codebase has business logic that needs to read a single row from a relational table, change some of its columns, and write the row back. |
| [Table Data Gateway](table-data-gateway.md) | canonical | 7,315 | An application needs to read and write rows in a table, and the two paths that seem obvious both go wrong at scale. |

## Data Source Architectural Patterns

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Record Set](record-set.md) | established | 7,254 | A team is building a screen, or a report, or a batch step, that needs to work with data shaped exactly like a SQL query result. |

## Distribution

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Remote Facade](remote-facade.md) | canonical | 8,710 | A well-factored domain model in a single process is built from many small, single-purpose objects. |

## Domain Logic

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Domain Model](domain-model.md) | canonical | 7,665 | An enterprise application accumulates business rules over its life, pricing tiers, discount eligibility, order-state transitions, tax jurisdictions, credit limits, cancellation ... |
| [Table Module](table-module.md) | established | 6,460 | A team is building a business application against a relational database using a technology stack whose native data-access layer hands back an in-memory, table-shaped structure ... |
| [Transaction Script](transaction-script.md) | canonical | 8,585 | A team is building a business application, an order system, a billing system, a claims processor, anything where the software's job is to carry out operations that a business ... |

## Enterprise Application Architecture

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Business Delegate](business-delegate.md) | established | 1,703 | A presentation-tier client, or another remote caller such as a device, a web service, or a rich client, needs to reach a business-tier service, and calling that remote service ... |
| [Collecting Parameter](collecting-parameter.md) | established | 1,922 | A single bulky method accumulates a result into a local variable across a long, linear sequence of steps, which is exactly the shape Industrial Logic's own text names directly ... |
| [Composite Entity](composite-entity.md) | established | 1,572 | A domain model made of many small, related objects, mapped one-to-one to individually remote, individually persistent components, pays a real network and management cost for every ... |
| [Composite View](composite-view.md) | established | 1,561 | A page is commonly built from parts that are shared across many other pages, a header, a footer, a navigation block, and duplicating those shared parts directly inside every page ... |
| [Connection Pooling](connection-pooling.md) | canonical | 1,662 | PostgreSQL's own documentation states the direct constraint this pattern works against. |
| [Context Object](context-object.md) | established | 1,490 | A component or a service somewhere in an application needs access to system information, such as request parameters or configuration values, that originates from a specific ... |
| [Tolerant Reader](tolerant-reader.md) | established | 1,517 | Fowler's own text states the underlying problem directly. |
| [View Helper](view-helper.md) | established | 1,467 | A template-based view, such as a JSP page, is easy to fill with embedded processing logic simply because the logic and the markup live in the same file, and once that happens, the ... |

## Object-Relational Behavioral

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Data Mapper](data-mapper.md) | canonical | 5,828 | An application has a domain model made of objects with behavior, and a relational database made of tables, rows, and columns with no behavior. |
| [Identity Map](identity-map.md) | canonical | 6,357 | An object-relational mapping layer loads rows from a database and turns them into in-memory objects. |
| [Lazy Load](lazy-load.md) | canonical | 7,284 | An object graph persisted in a relational database is, by its nature, larger than any single query needs. |
| [Unit of Work](unit-of-work.md) | canonical | 8,827 | An operation touches several objects that came from, or are destined for, a database. |

## Object-Relational Behavioral Patterns

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Metadata Mapping](metadata-mapping.md) | canonical | 7,663 | An object-relational mapper needs to know, for every persistent class, which table it corresponds to, which column each field maps to, how associations between classes translate ... |

## Object-Relational Metadata Mapping Pattern

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Active Record](active-record.md) | canonical | 7,255 | An application needs to load rows from a relational table, let a caller read and mutate the fields as ordinary object properties, validate the values, and persist changes back ... |

## Object-Relational Metadata Mapping Patterns

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Association Table Mapping](association-table-mapping.md) | canonical | 5,934 | An application built with an object model needs to persist a relationship where either side can be associated with more than one instance of the other. |

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
| [Identity Field](identity-field.md) | canonical | 6,034 | An in-memory object system and a relational database use two different, and incompatible, notions of identity. |

## Object-Relational Structural Patterns

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Concrete Table Inheritance](concrete-table-inheritance.md) | canonical | 7,984 | An application's domain model contains a base type with several concrete subtypes, each subtype adding its own fields, and the persistence layer must map that hierarchy onto ... |
| [Inheritance Mappers](inheritance-mappers.md) | canonical | 8,397 | A domain model with an inheritance hierarchy, a base Employee class with SalariedEmployee, CommissionedEmployee, and HourlyEmployee subclasses, needs a persistence layer that can ... |
| [Single Table Inheritance](single-table-inheritance.md) | canonical | 9,071 | An object model has a natural inheritance hierarchy. |

## Session State

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Server Session State](server-session-state.md) | canonical | 8,719 | HTTP is stateless. Each request arrives at the server with no memory of the request before it, and the connection that carried it may already be closed by the time the response ... |

## Structural

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Data Transfer Object](data-transfer-object.md) | canonical | 7,710 | Two processes, or two tiers within the same process boundary that are treated as independently deployable, need to exchange structured data, and the cost or the coupling of ... |
| [Plugin](plugin.md) | canonical | 7,648 | An application has a piece of behavior that legitimately differs across deployments, and the difference is not a business rule that changes with input, it is a difference in which ... |

## Web Presentation

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Application Controller](application-controller.md) | established | 8,471 | The problem shows up first in an application with more than one screen that share the same underlying process. |
| [Front Controller](front-controller.md) | canonical | 8,011 | A web application grows past a handful of pages. |
| [Page Controller](page-controller.md) | canonical | 5,225 | A web application must translate an incoming HTTP request into a specific piece of server-side behavior and a specific response. |
| [Template View](template-view.md) | canonical | 7,530 | A system has finished computing a result, a customer record, a list of orders, a search result set, and now has to turn that result into an HTML document a browser can render. |
| [Transform View](transform-view.md) | established | 7,578 | An application has assembled everything it needs to render a response. |
| [Two Step View](two-step-view.md) | canonical | 6,236 | A web application with more than a handful of pages needs every page to share a consistent visual identity. |

## Planned

Named, not yet authored. Queued in [docs/AUTHORING-QUEUE.json](../../docs/AUTHORING-QUEUE.json), each one to be built to the same 18-dimension standard as the entries above before it is published.

- Intercepting Filter
- Presentation Model
- Service Layer
- Session Facade

## Reading order

Entries are independent. Each one names the patterns it composes with and
the patterns it conflicts with in dimension 13, so following those links
gives a better path than reading top to bottom.

Generated by `tools/gen-indexes.py`. Do not edit by hand.
