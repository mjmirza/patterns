---
name: Data Access Object
slug: data-access-object
family: 01-design-patterns-gof
category: Structural
aliases: [DAO, DAO Pattern]
first_described: "Alur, Crupi, Malks 2001 (Core J2EE Patterns)"
maturity: canonical
related: [facade, factory-method, abstract-factory, dependency-injection, data-transfer-object]
incompatible_with: []
verified: 2026-08-23
---

## 1. Name, aliases, and lineage

The Data Access Object pattern (DAO, sometimes written DAO Pattern) was catalogued by Deepak Alur, John Crupi, and Dan Malks in Core J2EE Patterns, first published by Prentice Hall in 2001 with a second edition in 2003. The catalogue entry describes the DAO as the object that abstracts and encapsulates all access to a data source, so a business object obtains and stores data through a stable interface rather than through vendor-specific calls scattered across the application. The original catalogue page carries a Sun Microsystems copyright dated 2001 to 2002, confirming it as the primary source rather than a later reprint, and it remains mirrored on Oracle's own domain today, a rare case of a two-decade-old catalogue page still hosted by the company that absorbed Sun.

A companion site, corej2eepatterns.com, excerpts the same second-edition text and displays cover endorsements from Martin Fowler, John Vlissides, and Grady Booch, though the exact operator of that site was not independently confirmed during research and should be treated as a companion or excerpt source rather than the authors own official channel.

It is worth recording, plainly, that DAO terminology did not travel uniformly across the industry. Microsoft's own Application Architecture Guide, in its Chapter 8 data layer guidelines, lists a relevant-patterns table naming Active Record, Data Mapper, Query Object, Repository, Row Data Gateway, Table Data Gateway, and Table Module, and cites every one of them to Martin Fowler's Patterns of Enterprise Application Architecture (Addison-Wesley, 2002) rather than to Sun's Core J2EE Patterns. Microsoft's own era-appropriate .NET guidance never adopts the name DAO anywhere in that catalogue; its closest concrete artifact is a library called the Data Access Application Block, not a named pattern. So DAO is best understood as the Java EE communitys own name for a pattern whose underlying idea, hiding the storage mechanism behind a stable interface, was independently and differently named in the .NET world at the same historical moment.

## 2. Problem and context

Most real applications need to read and write persistent data at some point, and that data can live behind very different access mechanisms: a relational database reached through JDBC, an object database, a flat file, a legacy mainframe gateway, or a business-to-business service call. Each of those mechanisms has its own API shape, its own connection lifecycle, and its own error model. When business logic calls those APIs directly, every class that touches persistence becomes coupled to one specific technology and one specific vendor, so migrating to a different database, adding a second storage technology, or even swapping a JDBC driver for a connection-pooling wrapper means editing code spread across the whole application rather than in one place.

The context in which this problem is sharpest is any application whose data source is likely to change, whose deployment targets more than one storage technology, or whose team wants to unit test business logic without a live database on hand. The context in which it is not a problem is the opposite: a small application with one client, one storage technology it will never swap, and few enough business rules that the persistence code is trivial to read wherever it lives.

## 3. Forces

Portability against convenience is the dominant tension. Coupling business code directly to a JDBC ResultSet or a specific driver call is the fastest way to get a feature working, but it is also what makes changing the underlying storage expensive later. The DAO pattern moves that migration cost into a small, isolated set of implementing classes, so the client code that calls the DAO interface never has to change when the storage technology does.

A second force is granularity, and it cuts against the pattern if handled carelessly. A DAO interface can be defined per aggregate, exposing a handful of coarse operations, or per table, exposing narrow CRUD methods that mirror the schema. Wikipedia's own treatment of the pattern names this directly as a source of leaky abstraction, observing that DAO objects can obscure the true cost of a database access because they read like ordinary in-memory method calls, and that this specific problem tends to appear "when you have a separate DAO for each table and the SELECT query is prevented from accessing anything other than the target table." A DAO defined at the wrong granularity trades one coupling problem for a different, subtler one: business code that looks decoupled from storage while actually issuing far more queries than it needs to.

A third force is who owns the transaction boundary, the DAO or the business object that calls it. Spring's own current documentation on declarative transactions does not state an explicit rule for this, but every code example in that documentation places the @Transactional annotation on the service class rather than on the DAO or repository class beneath it, and the documentation itself recommends annotating concrete classes rather than interface methods. The convention embedded in that example code, transaction boundaries live one layer above the DAO, is strong enough to treat as the field's de facto answer even though Spring never states it as a hard rule.

A fourth force is the historical one that produced most of the pattern's modern implementation variants: the mismatch between an object-oriented domain model and a relational schema. Hibernate's own project page states plainly that its adoption "was originally driven by grassroots Java developers looking for a way out of the quagmire of handwritten object/relational mapping code," which is precisely the burden a hand-written JDBC-based DAO carries and an ORM-backed one largely removes.

## 4. Applicability and non-applicability

Reach for a DAO when the application genuinely needs to isolate business logic from a specific persistence technology: when the storage engine might change, when more than one storage technology must be supported side by side, when the service layer needs to be unit tested against a mock or in-memory stand-in rather than a live database, or when the data source is an external system such as a gateway or a business-to-business service rather than a conventional database. Microsoft's own Chapter 8 guidance corroborates the external-service case directly, describing "service agents" as components that "isolate the varying requirements for calling services from your application," the same encapsulating instinct applied to a REST or gateway integration rather than a database.

Do not reach for a hand-written DAO when a framework will generate the equivalent interface implementation for you at effectively zero maintenance cost, which is now the common case for relational data behind Spring Data JPA or Jakarta Data, or behind Android Room for local device storage. Do not reach for it either in a genuinely small application. Microsoft's own guidance states this trade-off honestly for its own ecosystem: "For smaller applications, the business layer, or even the presentation layer, may access the service agent directly," and separately notes that for "a small application that has a single client and few business rules, dynamic SQL is often the best choice," implying no abstraction layer is warranted at all in that case.

## 5. Structure

**BusinessObject.** The pattern's own name for the client of the DAO. This is a service or business-layer object that needs to obtain or store data but should never need to know how that data is physically accessed. It depends only on the DataAccessObject interface, never on a concrete implementation.

**DataAccessObject.** The abstract interface at the center of the pattern. It exposes the operations the BusinessObject actually needs, expressed in domain terms such as findById or save rather than in storage terms such as executeQuery. The catalogue's own wording is that the DataAccessObject "abstracts the underlying data access implementation for the BusinessObject to enable transparent access to the data source."

**ConcreteDataAccessObject.** The class that implements the DataAccessObject interface against one specific storage technology, for example a JDBC-backed implementation, a JPA-backed implementation, or an implementation backed by a document store. This is the layer where portability is paid for: swapping storage technology means writing or selecting a different ConcreteDataAccessObject, never touching the BusinessObject. This exact class name is a secondary-source convention rather than a phrase found verbatim in the primary catalogue text, which discusses the implementing role structurally through its Strategies section without fixing a single class name.

**DataSource.** The underlying persistent store itself, whether a relational database, a legacy system reached through a gateway, or a business-to-business service.

**TransferObject.** The data carrier the DataAccessObject uses to move data across the boundary in both directions. The catalogue's own related-patterns note states this directly: "A DAO uses Transfer Objects to transport data to and from its clients." Rather than handing back a raw persistence type, such as a JDBC ResultSet or a framework-managed entity, a well-formed DataAccessObject returns and accepts plain data carriers shaped for the client's needs.

## 6. ASCII structure diagram

```
+-------------------+          depends on           +------------------------+
|   BusinessObject   |------------------------------->|   <<interface>>        |
|  (service layer)   |                                |   CustomerDao          |
|                     |<-------------------------------|------------------------|
+-------------------+     TransferObject in, out     |  findById(id)          |
                                                        |  findAll()             |
                                                        |  save(customer)        |
                                                        |  delete(id)            |
                                                        +-----------^------------+
                                                                    |
                                                            implements
                                              +---------------------+---------------------+
                                              |                                             |
                              +---------------v----------------+          +----------------v----------------+
                              |   ConcreteDataAccessObject      |          |   ConcreteDataAccessObject      |
                              |   JdbcCustomerDao                |          |   InMemoryCustomerDao            |
                              |----------------------------------|          |----------------------------------|
                              |  - dataSource                    |          |  - records: Map                 |
                              |  findById(id)                    |          |  findById(id)                    |
                              |  findAll()                       |          |  findAll()                       |
                              |  save(customer)                  |          |  save(customer)                  |
                              |  delete(id)                      |          |  delete(id)                      |
                              +---------------+------------------+          +----------------------------------+
                                              |
                                              v
                                   +-----------------------+
                                   |      DataSource         |
                                   |  (relational database) |
                                   +-----------------------+

                                   +-----------------------+
                                   |     TransferObject      |
                                   |     CustomerRecord      |
                                   |-------------------------|
                                   |  id, name, email        |
                                   +-----------------------+
```

## 7. Dynamics

On a read, the BusinessObject calls a finder method on the DataAccessObject interface, for example findById. The ConcreteDataAccessObject that implements it opens or reuses a connection to the DataSource, issues the underlying query, and maps each row or document it gets back into one or more TransferObject instances. Those TransferObjects, never the raw ResultSet or a framework-managed entity, are what the BusinessObject actually receives.

On a write, the BusinessObject constructs or receives a TransferObject describing the change, passes it to a save or update method on the DataAccessObject interface, and the ConcreteDataAccessObject extracts the fields it needs and issues the corresponding insert or update against the DataSource. The BusinessObject never sees the SQL, the connection, or the driver involved, and swapping the ConcreteDataAccessObject for one backed by a different DataSource changes none of the calling code, because both the interface and the TransferObject shape stay identical across implementations.

## 8. Implementation variants

**Hand-written JDBC.** The original 2001-era shape: a ConcreteDataAccessObject holds a Connection or DataSource, builds a PreparedStatement, executes it, iterates the ResultSet by hand, and maps each row into a TransferObject, closing the Connection, Statement, and ResultSet explicitly in a finally block or a try-with-resources. This variant carries the most boilerplate and the most opportunity for a forgotten close call to leak a connection.

**Spring JdbcTemplate.** Spring's own reference documentation calls JdbcTemplate "the central class in the JDBC core package," and states directly that "it handles the creation and release of resources, which helps you avoid common errors, such as forgetting to close the connection," that it "performs the basic tasks of the core JDBC workflow," and that it "catches JDBC exceptions and translates them to the generic, more informative, exception hierarchy defined in the org.springframework.dao package." The documentation is explicit about the reduction in developer responsibility: "When you use the JdbcTemplate for your code, you need only to implement callback interfaces, giving them a clearly defined contract." A JdbcTemplate-backed DAO is instantiated with a DataSource reference directly or wired as a Spring bean.

**JPA or Hibernate delegating to an EntityManager or Session.** This is a widely practiced variant, though a source explicitly framing "a DAO that delegates to an EntityManager" as a named pattern was not located during research for this entry, so this claim is offered as engineering judgement rather than a sourced fact. What is independently confirmed is that Hibernate's own release history shows the framework itself moving toward a standardized repository abstraction: Hibernate 6.5 shipped a Jakarta Data tech preview, meaning Hibernate's own maintainers treated the DAO-to-repository transition as significant enough to build first-class support for ahead of the formal standard's release.

**Spring Data JPA's generated repository proxy.** Spring Data's own reference documentation calls the generated implementation a "repository proxy," and documents that it "has two ways to derive a store-specific query from the method name: by deriving the query from the method name directly, by using a manually defined query," describing three lookup strategies, CREATE, USE_DECLARED_QUERY, and the default CREATE_IF_NOT_FOUND. Spring Data's own getting-started guide states the consequence for the developer directly: "You need not write an implementation of the repository interface. Spring Data JPA creates an implementation when you run the application." This is a runtime mechanism: the concrete class is generated by a dynamic proxy when the application starts.

**Android Room's compile-time @Dao processor.** Android's own developer documentation is explicit that Room generates the concrete implementation at build time rather than at runtime: "At compile time, Room automatically generates implementations of the DAOs that you define." The documentation also highlights a benefit specific to compile-time generation that neither the JDBC nor the Spring Data variant offers: "Room validates SQL queries at compile time. This means that if there's a problem with your query, a compilation error occurs instead of a runtime failure." Room additionally documents that a DAO can be declared as either an interface or an abstract class, but must always carry the @Dao annotation.

Across variants (d) and (e), the structural contract described in dimensions 5 through 7 does not change: the BusinessObject depends only on the declared interface. What changes is who writes the ConcreteDataAccessObject and when, moving from the developer writing it by hand, to a framework generating it at application startup, to a compiler plugin generating it before the application ever runs.

## 9. Known production uses

Android's Room persistence library is the clearest current, large-scale, actively maintained production use of the DAO name itself: its @Dao annotation and the compile-time code generation behind it are described directly in Android's own developer documentation, and Room ships as part of Android Jetpack, used across a large share of the Android application ecosystem.

Spring Framework's JdbcDaoSupport class is a second, more nuanced production use: it has shipped in Spring for two decades as a convenience superclass for JDBC-based data access objects, per Spring's own current Javadoc, but that same Javadoc marks the class deprecated as of Spring Framework 7.0, with removal planned, in favor of direct injection of JdbcTemplate or the newer JdbcClient. This is worth recording precisely: the DAO name is being actively retired from Spring's own convenience classes even as the underlying pattern persists everywhere else in the ecosystem under Repository naming.

Jakarta Data, covered in more depth in dimension 18's recent developments, is the most significant current production use in the sense of formal standardization: it is an official Jakarta EE specification, with its 1.0 release ballot concluding on 2026-06-06 as documented on the specification's own page, defining a vendor-neutral repository abstraction that multiple implementations, including Hibernate, now target.

Apache iBATIS, a predecessor to the modern MyBatis project, shipped a component named directly iBATIS DAO as part of its 1.0 release, according to Wikipedia's own account of the project, though that component was later deprecated once the maintainers judged that "better DAO frameworks were available, such as Spring Framework," making it a historically real but no longer current production use.

## 10. Consequences

Positive. Business logic is decoupled from the specific storage technology, so migrating vendors or adding a second storage technology touches only the ConcreteDataAccessObject layer. The service layer becomes independently unit testable, since a mock or stub implementation of the DAO interface can stand in for the real one, as Spring's own testing documentation states directly. Query logic is centralized rather than duplicated across every caller that needs the same data. The interface gives the codebase a single, stable vocabulary for persistence operations, expressed in domain terms rather than in storage-specific ones.

Negative. A DAO defined at too fine a granularity, one per table with narrow CRUD methods, reproduces the leaky-abstraction problem described in dimension 3: it looks like a decoupled in-memory collection while actually issuing far more round trips than a coarser interface would. A hand-written JDBC implementation carries real boilerplate and a real risk of a forgotten resource close leaking a connection. Even a framework-generated implementation does not eliminate the classic object-relational performance pitfalls, most notably the N plus one query problem described in dimension 11. And because the DAO is exactly where query logic and transaction handling meet, an unclear convention for which layer owns the transaction boundary, discussed as a force in dimension 3, can produce bugs that are hard to trace back to the interface itself.

## 11. Failure modes and misuse

**The N plus one query problem.** This is the most commonly observed failure mode in ORM-backed DAO or repository implementations. Baeldung's own current article on the problem states the mechanism directly. "The N+1 problem is the situation when, for a single request, for example, fetching Users, we make additional requests for each User to get their information," and the problem "often is connected to lazy loading" but is not limited to it, usually arising from a many-to-many or one-to-many relationship. The symptom an engineer actually observes is a query log or an APM trace showing one query followed by a burst of near-identical smaller queries, one per row of the first result. The same source is candid that there is no single silver-bullet fix. Switching a relationship's fetch type can reduce request count in simple cases but offers limited control over the query actually generated, so the article's own recommendation is to observe the application's real access patterns and write a dedicated, tailored query for each one, hint Hibernate's fetch mode explicitly rather than relying on the default, and add tests that catch an unintended change in fetch behavior before it reaches production.

**Connection leaks from an unclosed resource.** A hand-written JDBC DAO that fails to close a Connection, Statement, or ResultSet on every code path, including exception paths, will eventually exhaust the connection pool. HikariCP's own documentation describes the concrete, observable symptom: a leak-detection threshold setting that "controls the amount of time that a connection can be out of the pool before a message is logged indicating a possible connection leak," alongside a PendingConnections metric that climbs as threads queue for a connection that never comes back.

**Trusting an in-memory database as a stand-in for the real one.** Baeldung documents a specific, real example of this anti-pattern: a native SQL UPDATE statement using a table alias in its SET clause passes cleanly when tested against an H2 in-memory database, but fails against a real PostgreSQL instance, because "PostgreSQL does not accept aliases in the SET clause." The article's own conclusion is direct: testing on a real database, via a tool such as Testcontainers, is "much more profitable, especially if we use provider-dependent queries," because an in-memory substitute can silently hide a bug that only the production database engine's actual SQL dialect would surface.

**SQL injection through hand-built query strings.** Because a DAO is exactly the layer where raw SQL or a query string is most often constructed, it is also the layer where string concatenation of untrusted input becomes exploitable. This is not a theoretical concern for the frameworks that most commonly implement DAOs: Hibernate's own core has shipped real, CVSS-scored SQL injection vulnerabilities inside its own query-building code, including CVE-2020-25638, a high-severity injection in the JPA Criteria API implementation affecting versions from 5.4.0.Final before 5.4.24.Final, and CVE-2026-0603, a high-severity second-order injection through unsanitized identifier-column handling. MyBatis-Plus, a persistence framework commonly used to implement the pattern, has shipped comparable injection vulnerabilities of its own, including CVE-2022-25517 and CVE-2023-25330. These confirm that even a DAO implementation that correctly avoids hand-written string concatenation in application code can still be exposed by a defect inside the underlying framework's own query construction.

## 12. Trade-off matrix

| Force | Data Access Object | Repository (domain-driven design) | Active Record | Direct EntityManager or Session access |
|---|---|---|---|---|
| Conceptual level | Table or data-source centric, close to storage | Domain centric, models an in-memory collection of aggregates | Domain object carries its own persistence methods | No abstraction, storage API used directly |
| Coupling to storage technology | Isolated behind an interface | Isolated behind an interface | High, the domain object itself is coupled | Highest, callers depend on the ORM API directly |
| Testability of business logic | High, interface is mockable | High, interface is mockable | Lower, persistence and domain logic are fused | Low, tests need a real or embedded persistence context |
| Granularity risk | Can become leaky if defined per table | Lower, naturally scoped to an aggregate | Not applicable, one class per entity | Not applicable, no interface to misdefine |
| Boilerplate for a hand-written implementation | Moderate to high | Moderate to high | Low, methods live on the entity itself | Lowest, no wrapping layer at all |
| Best fit | Multiple or uncertain storage technologies, or an external gateway or service | Complex domains needing a collection-like persistence abstraction | Small applications with simple, table-shaped domain objects | Prototypes or applications that will never need to swap the ORM |

Baeldung's own comparison of DAO and Repository states the distinction this table reflects directly: "DAO is a lower-level concept, closer to the storage systems. However, Repository is a higher-level concept, closer to the Domain objects," and "DAO can't be implemented using a repository. However, a repository can use a DAO for accessing underlying storage."

## 13. Related and incompatible patterns

**Repository.** Related but distinct, and frequently confused with DAO. Baeldung's own comparison draws the line precisely: DAO works "as a data mapping or access layer, hiding ugly queries," while a Repository "is a layer between domains and data access layers," and a Repository may itself be built on top of one or more DAOs, though the reverse composition does not hold. This repository's own separately catalogued Repository entries, in the domain-driven design and mobile architecture families, cover that higher-level pattern in depth.

**Transfer Object (Data Transfer Object).** Directly related by the primary catalogue's own text, quoted in dimension 5: a DAO uses Transfer Objects to move data across its boundary rather than exposing a raw persistence type to the client. A concrete benefit of that discipline, evidenced by Baeldung's own DTO article, is data minimization: "The DTO above provides only the relevant information to the client, hiding the password, for example, for security reasons," a benefit a DAO loses the moment it hands back a raw entity instead.

**Factory Method and Abstract Factory.** The primary Core J2EE Patterns catalogue names both of these Gang of Four patterns directly in its own Related Patterns section, in connection with a documented strategy for constructing the correct ConcreteDataAccessObject for a given deployment without the BusinessObject needing to know which concrete class it received.

**Dependency Injection.** Modern DAO usage typically replaces a hand-rolled DAO factory with constructor injection of the interface, wiring the concrete implementation in at composition time rather than through a factory object the DAO pattern itself defines. This repository's own Dependency Injection entry, in this same family, covers that wiring mechanism in depth.

**Facade.** An architecturally plausible comparison, since a DAO does simplify a more complex underlying subsystem, whether JDBC's verbose connection and statement API or an ORM's session lifecycle, behind one focused interface, which is structurally close to what a Facade does. No source explicitly drawing this comparison was located during research for this entry despite several targeted attempts, so it is recorded here as engineering judgement rather than a sourced claim, and should not be presented to a reader as an established, citable relationship.

## 14. Refactoring path in and out

**Introducing a DAO into code that lacks one.** Find the calls to a database driver, an ORM session, or an external gateway scattered through business or service code. Group them by the aggregate or record type they operate on. For each group, define an interface exposing only the operations the business code actually calls, expressed in domain terms rather than storage terms. Move the existing storage-specific code into a new class implementing that interface, unchanged in behavior. Replace every direct call site in the business code with a call through the interface, and inject the concrete implementation rather than constructing it inline. This is, in effect, an Extract Interface followed by a Move Method, applied specifically to persistence code.

**Removing a DAO once it stops earning its place.** Two situations justify removal. First, when a framework's own generated repository, such as Spring Data JPA or Jakarta Data, can replace a hand-written implementation one for one with no behavior change, the hand-written ConcreteDataAccessObject class can simply be deleted and the interface declared as a framework repository instead, keeping the same call sites unchanged. Second, when a DAO has become so fine-grained, one per table, with no meaningful abstraction benefit left, that it is pure ceremony around a single query, it can be collapsed into a coarser Repository scoped to the whole aggregate, folding several narrow DAOs into one interface that better matches how the domain actually uses the data.

## 15. Testing and verification

The service layer that depends on a DAO is unit tested by substituting a mock or stub for the DAO interface. Spring's own testing documentation states this directly: "you can test service layer objects by stubbing or mocking DAO or repository interfaces, without needing to access persistent data while running unit tests." A comparison of mocking libraries by Baeldung adds a useful counterpoint: not every DAO method is worth mocking, since mocking a method whose entire purpose is to talk to a real database "would provide minimal value since you'd still need to test whether actual database calls return the expected data," meaning the mock earns its value at the service layer, not as a replacement for testing the DAO implementation itself.

The DAO implementation itself is verified by an integration test against a real, or realistically equivalent, database instance rather than against the mock used one layer up. Testcontainers' own documentation describes exactly this use: "Use a containerized instance of your database to test your data access layer code for complete compatibility, without requiring a complex setup on developer machines," and a companion guide on testing a Spring Boot REST API states the reasoning directly, that using the same database engine as production rather than mocks or an in-memory substitute means "we are free to do any code refactoring" while staying confident the application keeps working as expected. The specific risk this guards against, an in-memory database silently passing a query that fails against the real production engine's SQL dialect, is discussed with a concrete worked example in dimension 11.

## 16. Observability signals

SQL statement logging is the most direct signal into a DAO layer's actual behavior. Hibernate's current documentation names three settings for this: hibernate.show_sql, described as logging "SQL directly to the console," hibernate.format_sql, which logs it "in a multiline, indented format," and hibernate.highlight_sql, which adds ANSI syntax highlighting, all of which the documentation says "really help when troubleshooting the generated SQL statements."

Slow-query detection is the second signal, catching a DAO method whose query has degraded before it becomes a wider incident. PostgreSQL's own configuration reference documents log_min_duration_statement directly: setting it to a duration such as 250 milliseconds means "all SQL statements that run 250ms or longer will be logged," which the documentation notes "can be helpful in tracking down unoptimized queries in your applications."

Connection pool metrics are the third signal, and they are specific to a DAO layer backed by a relational database through a pooled connection. HikariCP exposes ActiveConnections, IdleConnections, and PendingConnections as named metrics, the last of which the library's own documentation describes as "the number of threads awaiting connections from the pool." A healthy DAO layer shows ActiveConnections comfortably below the pool's configured maximum and PendingConnections at or near zero. A DAO layer in trouble shows PendingConnections climbing, "possible connection leak" messages from HikariCP's own leak-detection threshold, or a rising count of entries in the slow-query log that correlate with a specific DAO method.

## 17. Security and privacy implications

SQL injection is the primary security concern that connects directly to this pattern, because the DAO is exactly the layer where a raw query or query string is most often constructed. OWASP's own SQL Injection Prevention Cheat Sheet states the standard defense plainly: "Prepared statements are simple to write and easier to understand than dynamic queries, and parameterized queries force the developer to define all SQL code first and pass in each parameter to the query later," so that "the database will always distinguish between code and data, regardless of what user input is supplied." The dated CVEs listed in dimension 11, against both Hibernate and MyBatis-Plus, demonstrate that this risk is not confined to hand-written query strings; it has also appeared inside the query-building code of the frameworks that most commonly implement the DAO pattern.

A second, related concern is data minimization. A DAO or repository that hands back a raw persistence entity, rather than a Transfer Object shaped for the client, risks exposing a sensitive column to a layer of the application that should never see it. Baeldung's own DTO article gives a concrete example of the discipline that prevents this: a DTO built specifically to hide a password field before it ever reaches a client-facing layer.

## 18. References

1. Deepak Alur, John Crupi, Dan Malks, Core J2EE Patterns, Best Practices and Design Strategies, 2nd edition, Prentice Hall, 2003.
2. Core J2EE Patterns, Data Access Object, https://www.oracle.com/technetwork/java/dataaccessobject-138824.html, verified 2026-08-23.
3. corej2eepatterns.com, Data Access Object, http://www.corej2eepatterns.com/DataAccessObject.htm, verified 2026-08-23.
4. Wikipedia, Data access object, https://en.wikipedia.org/wiki/Data_access_object, verified 2026-08-23.
5. Baeldung, The DAO Pattern in Java, https://www.baeldung.com/java-dao-pattern, verified 2026-08-23.
6. Microsoft Learn, Chapter 8, Data Layer Guidelines, Application Architecture Guide, https://learn.microsoft.com/en-us/previous-versions/msp-n-p/ee658127(v=pandp.10), verified 2026-08-23.
7. Baeldung, DAO vs. Repository Patterns, https://www.baeldung.com/java-dao-vs-repository, verified 2026-08-23.
8. Spring Framework reference, Using @Transactional, https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html, verified 2026-08-23.
9. Hibernate ORM homepage, https://hibernate.org/orm/, verified 2026-08-23.
10. Spring Data JPA, Accessing Data with JPA, https://spring.io/guides/gs/accessing-data-jpa, verified 2026-08-23.
11. Spring Data JPA reference, Getting Started, https://docs.spring.io/spring-data/jpa/reference/jpa/getting-started.html, verified 2026-08-23.
12. GeeksforGeeks, Data Access Object Pattern, https://www.geeksforgeeks.org/system-design/data-access-object-pattern/, verified 2026-08-23.
13. Spring Framework reference, JDBC core, https://docs.spring.io/spring-framework/reference/data-access/jdbc/core.html, verified 2026-08-23.
14. Spring Data Commons reference, Query methods details, https://docs.spring.io/spring-data/commons/reference/repositories/query-methods-details.html, verified 2026-08-23.
15. Baeldung, Guide to Spring Data Repositories, https://www.baeldung.com/spring-data-repositories, verified 2026-08-23.
16. Android Developers, Accessing data using Room DAOs, https://developer.android.com/training/data-storage/room/accessing-data, verified 2026-08-23.
17. Baeldung, N+1 Problem in Hibernate and Spring Data JPA, https://www.baeldung.com/spring-hibernate-n1-problem, verified 2026-08-23.
18. Spring Framework reference, Unit Testing, https://docs.spring.io/spring-framework/reference/testing/unit.html, verified 2026-08-23.
19. Baeldung, Mockito vs EasyMock vs JMockit, https://www.baeldung.com/mockito-vs-easymock-vs-jmockit, verified 2026-08-23.
20. Testcontainers, homepage, https://testcontainers.com/, verified 2026-08-23.
21. Testcontainers, Testing a Spring Boot REST API, https://testcontainers.com/guides/testing-spring-boot-rest-api-using-testcontainers/, verified 2026-08-23.
22. Baeldung, Testing With Testcontainers Instead of an Embedded Database, https://www.baeldung.com/spring-boot-testcontainers-integration-test, verified 2026-08-23.
23. Hibernate ORM 7.1, Introduction, https://docs.hibernate.org/orm/7.1/introduction/html_single/Hibernate_Introduction.html, verified 2026-08-23.
24. PostgreSQL documentation, Error Reporting and Logging, https://www.postgresql.org/docs/current/runtime-config-logging.html, verified 2026-08-23.
25. HikariCP wiki, Dropwizard Metrics, https://github.com/brettwooldridge/HikariCP/wiki/Dropwizard-Metrics, verified 2026-08-23.
26. HikariCP, README, https://github.com/brettwooldridge/HikariCP, verified 2026-08-23.
27. OWASP Cheat Sheet Series, SQL Injection Prevention Cheat Sheet, https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html, verified 2026-08-23.
28. Baeldung, The Data Transfer Object Pattern, https://www.baeldung.com/java-dto-pattern, verified 2026-08-23.
29. GitHub Security Advisories, GHSA-j8jw-g6fq-mp7h, CVE-2020-25638, Hibernate ORM SQL injection, verified 2026-08-23.
30. GitHub Security Advisories, GHSA-2p5w-cvg5-gc5c, CVE-2026-0603, Hibernate SQL injection, verified 2026-08-23.
31. GitHub Security Advisories, GHSA-jaci-x9v5-wr9p, CVE-2022-25517, MyBatis-Plus SQL injection, verified 2026-08-23.
32. GitHub Security Advisories, MyBatis-Plus SQL injection, CVE-2023-25330, verified 2026-08-23.
33. Wikipedia, Apache iBATIS, https://en.wikipedia.org/wiki/Apache_iBATIS, verified 2026-08-23.
34. Jakarta EE, Jakarta Data specification, https://jakarta.ee/specifications/data/, verified 2026-08-23.
35. Jakarta EE, Jakarta Data 1.0, https://jakarta.ee/specifications/data/1.0/, verified 2026-08-23.
36. Hibernate ORM releases, https://hibernate.org/orm/releases/, verified 2026-08-23.
37. Spring Data JPA releases, https://github.com/spring-projects/spring-data-jpa/releases, verified 2026-08-23.
38. Android Developers, Room releases, https://developer.android.com/jetpack/androidx/releases/room, verified 2026-08-23.
39. Spring Framework Javadoc, JdbcDaoSupport, https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/jdbc/core/support/JdbcDaoSupport.html, verified 2026-08-23.

**Evidence grade.** mixed

**Most solid findings.** The pattern's own primary-source name, lineage, problem statement, solution statement, and participant structure are drawn directly from the still-live Core J2EE Patterns catalogue page, quoted verbatim where quoted at all. The implementation-variant claims for Spring JdbcTemplate, Spring Data JPA, and Android Room are each backed by a direct quote from that framework's own current documentation. The named CVEs against Hibernate and MyBatis-Plus, and the dated Jakarta Data 1.0 standardization, are independently checkable against NVD, GitHub Security Advisories, and the Jakarta EE specification page respectively.

**Unverified or unclear.** Three specific claims could not be sourced despite targeted attempts and are labelled as engineering judgement rather than sourced fact in the body above: that JPA or Hibernate delegating to an EntityManager is explicitly named as a pattern in Hibernate's own documentation, that a DAO can be understood as a specialized Facade, and any quantified line-count comparison of boilerplate reduction across the JDBC, JdbcTemplate, JPA, and Spring Data JPA variants. A fourth claim, that hand-optimized SQL still outperforms an equivalent ORM-generated query for specific well-known patterns, was searched for directly but no credible source with real numbers was found, so it is omitted from the entry rather than asserted without evidence.

## Code

### TypeScript

```typescript
// TransferObject: what crosses the boundary, never the raw storage row.
interface CustomerRecord {
  id: string;
  name: string;
  email: string;
}

// DataAccessObject: the interface the BusinessObject depends on.
interface CustomerDao {
  findById(id: string): CustomerRecord | undefined;
  findAll(): CustomerRecord[];
  save(customer: CustomerRecord): void;
  delete(id: string): void;
}

// ConcreteDataAccessObject #1: an in-memory implementation, useful for tests.
class InMemoryCustomerDao implements CustomerDao {
  private records = new Map<string, CustomerRecord>();

  findById(id: string): CustomerRecord | undefined {
    return this.records.get(id);
  }

  findAll(): CustomerRecord[] {
    return Array.from(this.records.values());
  }

  save(customer: CustomerRecord): void {
    this.records.set(customer.id, customer);
  }

  delete(id: string): void {
    this.records.delete(id);
  }
}

// ConcreteDataAccessObject #2: a stand-in for a JDBC-style implementation,
// simulating a query against a relational table without a real driver.
class SqlLikeCustomerDao implements CustomerDao {
  constructor(private table: CustomerRecord[]) {}

  findById(id: string): CustomerRecord | undefined {
    return this.table.find((row) => row.id === id);
  }

  findAll(): CustomerRecord[] {
    return [...this.table];
  }

  save(customer: CustomerRecord): void {
    const index = this.table.findIndex((row) => row.id === customer.id);
    if (index >= 0) {
      this.table[index] = customer;
    } else {
      this.table.push(customer);
    }
  }

  delete(id: string): void {
    const index = this.table.findIndex((row) => row.id === id);
    if (index >= 0) {
      this.table.splice(index, 1);
    }
  }
}

// BusinessObject: depends only on the CustomerDao interface, never on
// which concrete implementation is behind it.
class CustomerService {
  constructor(private dao: CustomerDao) {}

  registerCustomer(id: string, name: string, email: string): void {
    this.dao.save({ id, name, email });
  }

  lookupCustomer(id: string): CustomerRecord | undefined {
    return this.dao.findById(id);
  }
}

const memoryService = new CustomerService(new InMemoryCustomerDao());
memoryService.registerCustomer("c1", "Ada Lovelace", "ada@example.org");
console.log(memoryService.lookupCustomer("c1"));

const sqlService = new CustomerService(new SqlLikeCustomerDao([]));
sqlService.registerCustomer("c2", "Grace Hopper", "grace@example.org");
console.log(sqlService.lookupCustomer("c2"));
```

### Python

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass


# TransferObject: what crosses the boundary, never the raw storage row.
@dataclass
class CustomerRecord:
    id: str
    name: str
    email: str


# DataAccessObject: the interface the BusinessObject depends on.
class CustomerDao(ABC):
    @abstractmethod
    def find_by_id(self, customer_id: str) -> CustomerRecord | None: ...

    @abstractmethod
    def find_all(self) -> list[CustomerRecord]: ...

    @abstractmethod
    def save(self, customer: CustomerRecord) -> None: ...

    @abstractmethod
    def delete(self, customer_id: str) -> None: ...


# ConcreteDataAccessObject #1: an in-memory implementation, useful for tests.
class InMemoryCustomerDao(CustomerDao):
    def __init__(self) -> None:
        self._records: dict[str, CustomerRecord] = {}

    def find_by_id(self, customer_id: str) -> CustomerRecord | None:
        return self._records.get(customer_id)

    def find_all(self) -> list[CustomerRecord]:
        return list(self._records.values())

    def save(self, customer: CustomerRecord) -> None:
        self._records[customer.id] = customer

    def delete(self, customer_id: str) -> None:
        self._records.pop(customer_id, None)


# ConcreteDataAccessObject #2: a stand-in for a SQL-backed implementation,
# simulating a query against a relational table without a real driver.
class SqlLikeCustomerDao(CustomerDao):
    def __init__(self, table: list[CustomerRecord]) -> None:
        self._table = table

    def find_by_id(self, customer_id: str) -> CustomerRecord | None:
        for row in self._table:
            if row.id == customer_id:
                return row
        return None

    def find_all(self) -> list[CustomerRecord]:
        return list(self._table)

    def save(self, customer: CustomerRecord) -> None:
        for index, row in enumerate(self._table):
            if row.id == customer.id:
                self._table[index] = customer
                return
        self._table.append(customer)

    def delete(self, customer_id: str) -> None:
        self._table[:] = [row for row in self._table if row.id != customer_id]


# BusinessObject: depends only on the CustomerDao interface, never on
# which concrete implementation is behind it.
class CustomerService:
    def __init__(self, dao: CustomerDao) -> None:
        self._dao = dao

    def register_customer(self, customer_id: str, name: str, email: str) -> None:
        self._dao.save(CustomerRecord(customer_id, name, email))

    def lookup_customer(self, customer_id: str) -> CustomerRecord | None:
        return self._dao.find_by_id(customer_id)


memory_service = CustomerService(InMemoryCustomerDao())
memory_service.register_customer("c1", "Ada Lovelace", "ada@example.org")
print(memory_service.lookup_customer("c1"))

sql_service = CustomerService(SqlLikeCustomerDao([]))
sql_service.register_customer("c2", "Grace Hopper", "grace@example.org")
print(sql_service.lookup_customer("c2"))
```

### Go

```go
package main

import "fmt"

// CustomerRecord is the TransferObject: what crosses the boundary,
// never the raw storage row.
type CustomerRecord struct {
	ID    string
	Name  string
	Email string
}

// CustomerDao is the DataAccessObject interface the BusinessObject
// depends on.
type CustomerDao interface {
	FindByID(id string) (CustomerRecord, bool)
	FindAll() []CustomerRecord
	Save(customer CustomerRecord)
	Delete(id string)
}

// InMemoryCustomerDao is a ConcreteDataAccessObject useful for tests.
type InMemoryCustomerDao struct {
	records map[string]CustomerRecord
}

func NewInMemoryCustomerDao() *InMemoryCustomerDao {
	return &InMemoryCustomerDao{records: make(map[string]CustomerRecord)}
}

func (d *InMemoryCustomerDao) FindByID(id string) (CustomerRecord, bool) {
	record, found := d.records[id]
	return record, found
}

func (d *InMemoryCustomerDao) FindAll() []CustomerRecord {
	all := make([]CustomerRecord, 0, len(d.records))
	for _, record := range d.records {
		all = append(all, record)
	}
	return all
}

func (d *InMemoryCustomerDao) Save(customer CustomerRecord) {
	d.records[customer.ID] = customer
}

func (d *InMemoryCustomerDao) Delete(id string) {
	delete(d.records, id)
}

// SqlLikeCustomerDao is a second ConcreteDataAccessObject, a stand-in
// for a SQL-backed implementation, simulating a relational table
// without a real driver.
type SqlLikeCustomerDao struct {
	table []CustomerRecord
}

func (d *SqlLikeCustomerDao) FindByID(id string) (CustomerRecord, bool) {
	for _, row := range d.table {
		if row.ID == id {
			return row, true
		}
	}
	return CustomerRecord{}, false
}

func (d *SqlLikeCustomerDao) FindAll() []CustomerRecord {
	return append([]CustomerRecord{}, d.table...)
}

func (d *SqlLikeCustomerDao) Save(customer CustomerRecord) {
	for i, row := range d.table {
		if row.ID == customer.ID {
			d.table[i] = customer
			return
		}
	}
	d.table = append(d.table, customer)
}

func (d *SqlLikeCustomerDao) Delete(id string) {
	remaining := make([]CustomerRecord, 0, len(d.table))
	for _, row := range d.table {
		if row.ID != id {
			remaining = append(remaining, row)
		}
	}
	d.table = remaining
}

// CustomerService is the BusinessObject: it depends only on the
// CustomerDao interface, never on which concrete implementation
// is behind it.
type CustomerService struct {
	dao CustomerDao
}

func (s *CustomerService) RegisterCustomer(id, name, email string) {
	s.dao.Save(CustomerRecord{ID: id, Name: name, Email: email})
}

func (s *CustomerService) LookupCustomer(id string) (CustomerRecord, bool) {
	return s.dao.FindByID(id)
}

func main() {
	memoryService := &CustomerService{dao: NewInMemoryCustomerDao()}
	memoryService.RegisterCustomer("c1", "Ada Lovelace", "ada@example.org")
	fmt.Println(memoryService.LookupCustomer("c1"))

	sqlService := &CustomerService{dao: &SqlLikeCustomerDao{}}
	sqlService.RegisterCustomer("c2", "Grace Hopper", "grace@example.org")
	fmt.Println(sqlService.LookupCustomer("c2"))
}
```
