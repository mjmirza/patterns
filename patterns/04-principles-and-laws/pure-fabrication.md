---
name: Pure Fabrication
slug: pure-fabrication
family: 04-principles-and-laws
category: Principle
aliases: [GRASP Pure Fabrication, Fabricated Class, Service Class]
first_described: "Craig Larman, 1997, Applying UML and Patterns"
maturity: canonical
related: [information-expert, low-coupling, high-cohesion, single-responsibility-principle, dependency-inversion-principle, creator]
incompatible_with: []
verified: 2026-08-02
---

# Pure Fabrication

## 1. Name, aliases, and lineage

Pure Fabrication is one of the nine General Responsibility Assignment
Software Patterns, the collection universally shortened to GRASP that Craig
Larman assembled to answer one recurring design question, which class should
own which responsibility. Larman first published the set under the title
*Applying UML and Patterns* in 1997, and the standard modern definition
traces to the phrasing carried forward into the later edition, *Applying UML
and Patterns, An Introduction to Object-Oriented Analysis and Design and
Iterative Development*, Prentice Hall, 2004 (Wikipedia contributors, "GRASP
(object-oriented design)," verified 2026-08-02,
https://en.wikipedia.org/wiki/GRASP_(object-oriented_design)). The Wikipedia
article states the definition directly. "A pure fabrication is a class that
does not represent a concept in the problem domain, specially made up to
achieve low coupling, high cohesion," and the benefit that follows from
reusing that fabricated class. The same article notes that this kind of
class is what domain-driven design calls a service, a naming overlap that
matters for dimension 13 below (Wikipedia contributors, "GRASP
(object-oriented design)," verified 2026-08-02).

No competing name for the pattern is in wide independent use, but two loose
synonyms circulate in practitioner writing. "Fabricated class" and "service
class" both describe the same shape, a class invented purely to hold
behavior that does not belong to any real-world concept in the domain model.
The word "fabrication" is doing real work in the name. it signals, on
purpose, that the class is manufactured for engineering convenience rather
than discovered by analyzing the problem domain. Larman chose the word to
mark a boundary. a domain class like Order or Customer is discovered by
studying the business, while a class like OrderPersistenceService or
TaxCalculator is invented by the designer because no domain concept fits the
responsibility cleanly.

Pure Fabrication sits downstream of two other GRASP entries in the reasoning
chain that produces it. Information Expert says, as a default, give a
responsibility to whichever class already holds the data that responsibility
needs. Low Coupling and High Cohesion say, as constraints, prefer designs
where classes depend on few others and where each class does one coherent
job. Pure Fabrication exists because those three guidelines sometimes
collide. following Information Expert literally can force a domain class to
absorb a technical responsibility, such as SQL generation or file
serialization, that has nothing to do with the domain concept the class
represents, and doing so damages both cohesion (the class now does two
unrelated jobs) and coupling (the domain class now depends on a database
driver or a file format library it should never have needed to know about).
Pure Fabrication is the escape hatch. when the expert-first answer would
produce a worse design by the other two criteria, invent a class instead of
forcing the responsibility onto an existing domain type.

The pattern predates none of the ideas it draws on. structured design's
notion of coupling (Larry Constantine and Edward Yourdon's 1979 work, cited
in `single-responsibility-principle.md` dimension 1) and the general
practice of separating persistence code from business objects were already
common before 1997. Larman's distinct contribution is naming the specific
decision, deliberately introduce a class with no domain meaning, and giving
it a place in an ordered responsibility-assignment vocabulary alongside
Creator, Information Expert, Low Coupling, and High Cohesion, so that the
decision to fabricate a class is a recognized, defensible design move rather
than something that happens by accident and gets criticized later as
"anemic" or "not object oriented."

## 2. Problem and context

A designer following Information Expert as the default rule will, for a
large share of responsibilities, land on the right class without further
thought. the class that holds the relevant data is usually also the right
place to put the behavior that uses that data. The problem shows up at the
edges of the domain model, where a responsibility genuinely needs data spread
across several domain objects, or where the responsibility is by nature
about a technical concern, such as talking to a database, formatting a PDF,
sending an email, or calling a payment gateway, rather than about the
business concept the domain object represents.

Consider a domain model with an Order class and an OrderLine class. Saving an
order to a relational database needs the order's fields, every line's
fields, and knowledge of SQL syntax, table names, and a database connection.
Applying Information Expert naively suggests giving Order a save method,
because Order holds most of the relevant data. But doing so means every
class that only wants to reason about order totals, discounts, and shipping
now also carries import statements for a JDBC driver, or an ORM, or
whichever persistence technology the application happens to use today. The
Order class becomes low in cohesion (it does business logic and persistence
at once) and highly coupled to a technology choice that has nothing to do
with what an order conceptually is. Worse, if the persistence technology
changes, a change that should be purely technical now forces a change to a
class that the rest of the business logic depends on, so the blast radius of
an unrelated decision multiplies.

The context in which Pure Fabrication applies is any moment in
object-oriented or object-based design where the "natural" home for a
responsibility, judged by who holds the relevant data, is a domain concept,
but assigning the responsibility there would violate Low Coupling or High
Cohesion more than the designer is willing to accept. This is a design-time
decision, made while assigning responsibilities to classes during
object-oriented analysis and design, not a runtime concern, and it applies
equally to systems built around GRASP's own vocabulary, to codebases that
never mention GRASP by name but face the identical persistence-versus-domain
tension, and to any layered architecture (three-tier web applications,
hexagonal architecture, clean architecture) where a service or repository
layer is deliberately kept separate from a domain or entity layer.

## 3. Forces

Pure Fabrication balances a specific, narrow set of competing pressures, and
naming them plainly is what separates the pattern from a vague appeal to
"good design."

Representational fidelity pulls toward keeping every class in the codebase
mapped to something a domain expert would recognize, because a model that
mirrors the domain is easier for a newcomer or a business reader to reason
about, and it is the ideal that Information Expert defaults toward. Pure
Fabrication works against this force directly. it deliberately adds a class
that a domain expert would never mention, and the entry only earns its
place when the alternative is worse along a different axis.

Cohesion pulls toward giving each class one job. a domain object that mixes
business rules with database access, network calls, or file formatting has
two reasons to change, the business rule changing and the technical detail
changing, and those two reasons rarely move in step. Pure Fabrication favors
cohesion strongly, often at the direct expense of representational fidelity.
the fabricated class is, definitionally, cohesive around a technical concern
rather than a domain concern.

Coupling pulls toward minimizing how many other classes, libraries, and
external systems a given class depends on. a domain class that talks
directly to a database driver is coupled to that driver's API, its
exceptions, its connection lifecycle, and often its query language. Pure
Fabrication reduces coupling for the domain classes by concentrating the
technical dependency inside the fabricated class, but it does not remove the
coupling from the system, it relocates it. The fabricated class itself is
now tightly coupled to the technical concern it exists to hold, which is an
accepted trade rather than a free win.

Reuse pulls toward extracting behavior that multiple parts of a system need
into a shared class, because a fabricated persistence class or a fabricated
formatting class is frequently useful to more than one domain object,
whereas domain-object-embedded behavior tends to be reusable only by
inheriting or duplicating the domain object itself.

Cognitive load and the ease of finding code pull against the pattern. every
fabricated class is one more name a new engineer has to learn that maps to
no real-world concept, and an application with dozens of loosely-related
service classes named things like ProcessorHelper or DataUtility can become
harder to work through than one where behavior lives close to the data it
uses, even if the latter is technically less cohesive by a strict textbook
measure. Larman's own guidance, echoed across secondary treatments of GRASP,
is that Pure Fabrication is a deliberate escape hatch to be reached for when
Information Expert's answer is genuinely worse, not a default first move
(search results summarizing Larman's *Applying UML and Patterns*, verified
2026-08-02, consistent across the Wikipedia GRASP article and multiple
academic course materials citing the same source text).

Larman's own criteria explicitly favor cohesion, coupling, and reuse over
representational fidelity whenever those forces genuinely conflict. that
ordering is the pattern's whole reason for existing, but it is a design
trade-off, not a law with no cost, and the cost lands as a harder time
finding code by inspection and an added class the domain model does not
explain on its own.

## 4. Applicability and non-applicability

Reach for Pure Fabrication when all of the following hold together, not any
single one in isolation.

A responsibility genuinely spans data from multiple domain objects, or is at
root a technical concern (persistence, serialization, network transport,
cryptography, logging, formatting) rather than a business rule.

Assigning the responsibility to the domain class that Information Expert
would nominate would visibly damage that class's cohesion, for example by
forcing it to import a technology-specific library, catch technology-specific
exceptions, or hold state (a database connection, a socket) that has no
business meaning.

The responsibility is likely to be reused by more than one part of the
system, or is likely to change for reasons entirely unrelated to why the
nearby domain classes change, so that separating it reduces the number of
unrelated reasons any single class has to change.

The team has a naming and layering convention (a service layer, a repository
layer, a persistence layer) that keeps the fabricated class easy to find
rather than a one-off oddity nobody expects to see.

Do not reach for Pure Fabrication in the following situations.

When the responsibility naturally and cleanly belongs to a single domain
object with no coupling or cohesion cost, because Information Expert already
gives the right answer and adding a fabricated class only adds an
unnecessary layer of indirection a reader has to trace through. Creating a
CustomerNameFormatter class to hold a one-line method that concatenates a
first and last name is over-fabrication, the responsibility belongs on
Customer.

When the "fabricated" class is actually a thin wrapper with no real
cohesive purpose of its own, invented to satisfy a rule of thumb rather than
to solve an actual coupling or cohesion problem. This produces the anemic
service-layer anti-pattern described in dimension 11, where every operation
gets its own single-method "manager" class and the fabrication adds
indirection without adding cohesion.

When the domain is genuinely small and stable enough that keeping technical
and business logic together causes no real maintenance pain, particularly in
scripts, prototypes, or small internal tools where the layering overhead of
a full service and repository split outweighs its benefit for the expected
lifetime of the code.

When the language or framework already provides an idiomatic mechanism that
achieves the same separation without a hand-written fabricated class, for
example a language feature like extension functions, mixins, or free
functions in a module, where introducing a class purely to hold a static
method adds ceremony the language does not need. This is discussed further
in dimension 8.

When fabricating the class would hide a design smell that should instead be
fixed at the domain-model level, such as an anemic domain model where nearly
all behavior has been pulled out into service classes and the domain objects
have degenerated into plain data holders with getters and setters and no
real behavior of their own. Martin Fowler names this failure mode directly
as the Anemic Domain Model anti-pattern, and warns that moving too much
behavior into fabricated service classes is one of its causes (this is
Fowler's own well-known naming of the smell, referenced in dimension 11
below with its citation).

## 5. Structure

Pure Fabrication has three participants, and unlike most Gang of Four
patterns, at least one of them is defined by what it is not.

The Domain Class is an existing class in the model, discovered by analyzing
the problem domain, that would be the "natural" home for a responsibility
under Information Expert's data-holding criterion. It is not required to
appear in the resulting design as a collaborator of the fabricated class,
but it is the reference point that motivates the fabrication. it is the
class the designer decided NOT to overload.

The Fabricated Class is the invented class itself, with no counterpart in
the problem domain, given a single cohesive technical or cross-cutting
responsibility. It typically has a name describing what it does rather than
what it is, ending in a suffix like Service, Repository, Manager, Formatter,
Validator, Mapper, or Adapter, and it usually depends on external
infrastructure (a database client, a file system API, a network library)
that the domain classes are deliberately kept unaware of.

The Client is any code, whether a domain class, an application-layer
orchestrator, or a user-interface handler, that needs the fabricated
responsibility performed and calls the fabricated class rather than
performing the work itself or delegating it to a domain object.

The relationship between them is a dependency, not an inheritance or a
composition in the structural sense. the fabricated class often takes domain
objects as method parameters or return values (an OrderRepository takes an
Order to save and returns an Order when loading), but it does not usually
hold a long-lived reference to a specific domain instance the way a
composed part-of relationship would. The domain class, correspondingly, is
free of any reference to the fabricated class at all in the cleanest form of
the pattern, since keeping the domain class unaware of persistence,
formatting, or transport concerns is the entire point.

## 6. ASCII structure diagram

```
+------------------------+          +---------------------------+
|      Domain Class      |          |      Fabricated Class      |
|  (Order, Customer...)  |          |  (OrderRepository, ...)    |
|------------------------|          |-----------------------------|
| business fields         |          | - external dependency      |
| business behavior       |          |   (DB client, HTTP client) |
|                        |          |-----------------------------|
| NO reference to the    |  uses    | + save(order: Domain)      |
| fabricated class        <---------| + load(id): Domain         |
| (kept unaware of the   | as param | + delete(id)                |
| technical concern)      | / return |                             |
+------------------------+          +--------------+--------------+
                                                     |
                                                     | depends on
                                                     v
                                     +---------------------------+
                                     |  External / infrastructure |
                                     |  concern (SQL driver,      |
                                     |  filesystem, HTTP client)  |
                                     +---------------------------+

              +--------------------------+
              |         Client           |
              |  (application service,   |
              |   controller, use case)  |
              +------------+-------------+
                           |
             calls both    |
        +------------------+------------------+
        v                                      v
+------------------+                +---------------------------+
|   Domain Class    |                |     Fabricated Class      |
|  for business     |                |  for the technical        |
|  operations        |                |  operation                |
+------------------+                +---------------------------+
```

## 7. Dynamics

The runtime flow through a Pure Fabrication typically has three steps, and
the sequence is the same whether the fabricated class handles persistence,
network transport, or formatting.

First, the client (an application-layer use case, a controller, or another
domain object acting through an injected dependency) performs whatever
business logic belongs to the domain classes, using the domain classes'
own methods. At this stage no fabricated class is involved, and the domain
objects remain unaware that anything outside the domain will happen next.

Second, the client hands a domain object, or a value derived from one, to
the fabricated class, invoking the technical operation, save this order,
send this email, render this document. The fabricated class receives the
domain object as a plain input. it does not reach back into the domain class
to pull additional data through a chain of calls, it takes what it needs as
a parameter, keeping the dependency direction one-way, from fabricated class
inward to the domain object's public shape, never from the domain object
outward toward the fabricated class.

Third, the fabricated class performs the technical work using its own
infrastructure dependency, translating between the domain object's shape and
whatever external representation the infrastructure requires (a SQL row, an
HTTP request body, a byte stream), and returns a result or raises a
technical-level error, which the client then decides how to handle at the
application level, for example by translating a low-level database
exception into a domain-meaningful error before it reaches a user interface.

```
Client                Domain Class           Fabricated Class        Infra
  |                        |                        |                  |
  |-- apply business ----->|                        |                  |
  |   rule (e.g. place()   |                        |                  |
  |   discount())          |                        |                  |
  |<-- updated domain -----|                        |                  |
  |    object              |                        |                  |
  |                        |                        |                  |
  |---------------------- save(order) -------------->|                  |
  |                        |                        |-- map domain --->|
  |                        |                        |   object to      |
  |                        |                        |   infra format   |
  |                        |                        |<-- ack/result ---|
  |<------------------- save result -----------------|                  |
  |                        |                        |                  |
```

## 8. Implementation variants

The class-based form described in dimensions 5 through 7 is the shape
Larman originally wrote about, because 1997-era object-oriented design
assumed a class-and-object vocabulary throughout. In practice, the pattern's
underlying idea, isolate a technical or cross-cutting responsibility away
from the domain model, is realized differently depending on language
idiom, and the differences are not cosmetic, they change how strongly the
"fabrication" reads as a deliberate design choice versus a language default.

In class-based object-oriented languages without first-class functions as a
common idiom, such as Java prior to widespread lambda use, or C# in its
early years, Pure Fabrication is realized nearly exactly as Larman
describes it, a named class with one or a small number of public methods,
often instantiated once and shared (frequently via dependency injection)
rather than created per use. The Spring Framework's stereotype annotations
are the clearest widely documented instance of this variant given a
first-class name in a production framework. Spring's own reference
documentation states that `@Repository`, `@Service`, and `@Controller` are
"specializations of `@Component` for more specific use cases (in the
persistence, service, and presentation layers, respectively)" (Spring
Framework Reference Documentation, "Classpath Scanning and Managed
Components," verified 2026-08-02,
https://docs.spring.io/spring-framework/reference/core/beans/classpath-scanning.html).
A class annotated `@Repository` in Spring is, by convention, exactly a
fabricated class, invented to isolate persistence concerns from the domain
model, and Spring further ties a technical benefit to the annotation. the
same documentation notes that `@Repository` "is already supported as a
marker for automatic exception translation in your persistence layer,"
meaning the framework converts low-level, technology-specific persistence
exceptions into a consistent unchecked exception hierarchy specifically
because the class is recognized as a fabricated persistence boundary rather
than a domain class.

In languages with closures and first-class functions as an idiomatic
default, such as JavaScript, Python, or Go, the class form of Pure
Fabrication is frequently replaced by a module of free functions or a small
struct of function fields, because the language does not require a class
wrapper purely to group related behavior. A Go package with exported
functions for saving and loading an order to a database is functionally a
Pure Fabrication in the GRASP sense, a cohesive, domain-ignorant grouping of
a technical responsibility, even though it never introduces a class at all.
This is the same substitution noted for Strategy in this repository's other
GRASP and Gang of Four entries, where a language's native support for
first-class functions removes the ceremony a class-based description
implies without removing the underlying design idea.

In dependency-injection-heavy architectures (Spring, .NET's built-in DI
container, Angular's injector), Pure Fabrication classes are typically
registered as singleton or scoped services and injected into whatever needs
them through an interface, which additionally satisfies the Dependency
Inversion Principle (see `dependency-inversion-principle.md`), the domain or
application layer depends on an interface the fabricated class implements,
not on the fabricated class's concrete type, which lets the concrete
persistence or transport technology be swapped in tests or across
environments.

In domain-driven design specifically, Pure Fabrication maps onto Eric
Evans's Service building block, a first-class named concept in DDD's own
vocabulary for exactly this situation, an operation that does not naturally
belong to any Entity or Value Object because it involves multiple objects
or represents a domain-significant process rather than a thing. This mapping
is directly noted by the Wikipedia GRASP article, which states that a pure
fabrication "is called a service" in domain-driven design (Wikipedia
contributors, "GRASP (object-oriented design)," verified 2026-08-02). The
DDD Repository pattern, described by Martin Fowler as a mechanism that
"mediates between the domain and data mapping layers using a
collection-like interface for accessing domain objects" (Martin Fowler,
"Repository," Patterns of Enterprise Application Architecture catalog,
verified 2026-08-02, https://martinfowler.com/eaaCatalog/repository.html),
is one of the most widely adopted named instances of Pure Fabrication in
production software, and is discussed further as a named production use in
dimension 9.

## 9. Known production uses

The Spring Framework's `@Repository`, `@Service`, and `@Controller`
stereotype annotations are a directly documented, named production
implementation of the pattern. Spring's own reference documentation defines
`@Component` as "a generic stereotype for any Spring-managed component" and
the other three as specializations of it for the persistence, service, and
presentation layers respectively (Spring Framework Reference Documentation,
"Classpath Scanning and Managed Components," verified 2026-08-02,
https://docs.spring.io/spring-framework/reference/core/beans/classpath-scanning.html).
Every class a Spring application annotates `@Service` or `@Repository` is,
by the framework's own architectural intent, a class invented to hold a
technical or cross-cutting responsibility that is deliberately kept separate
from the plain domain entities the application also defines, which is
Pure Fabrication's definition applied at framework scale across a very
large share of production Java web applications.

The Data Access Object pattern, documented by Sun's Core J2EE Pattern
Catalog and widely implemented across Java server applications, is a named,
long-standing instance of the pattern applied specifically to persistence.
Multiple independent secondary sources describing GRASP identify DAO
classes directly as textbook pure fabrications, invented specifically
because not all responsibilities can be assigned to domain classes,
especially responsibilities that deal with implementation technologies such
as persistence storage or network communication (summarized across course
materials and technical writing on GRASP and DAO, verified 2026-08-02). This
entry attempted to fetch Oracle's own DAO pattern page directly
(https://www.oracle.com/java/technologies/data-access-object.html) as the
primary source, but the page returned an access restriction on the
verification date and could not be quoted first-hand. the claim above rests
instead on the consistent secondary description of DAO's classification
across multiple independent sources cross-checked on 2026-08-02, and is
flagged here as a claim not verified against the primary source.

The Repository pattern, catalogued by Martin Fowler in Patterns of
Enterprise Application Architecture and adopted as a first-class building
block in Eric Evans's domain-driven design vocabulary, is a widely used,
named production instance. Fowler's own definition, that a Repository
"mediates between the domain and data mapping layers using a
collection-like interface for accessing domain objects" (Martin Fowler,
"Repository," verified 2026-08-02,
https://martinfowler.com/eaaCatalog/repository.html), describes exactly a
fabricated class, invented with no domain-model counterpart, whose sole job
is to isolate the domain layer from persistence technology. The pattern is
implemented directly as first-class framework support in Spring Data's
`JpaRepository` interface hierarchy and in the repository abstractions
documented for Microsoft's Entity Framework Core, both of which generate or
scaffold fabricated persistence classes on top of a plain domain entity.

Utility and helper classes in the Java standard library, such as
`java.util.Collections` and `java.util.Arrays`, are a simpler, older
production instance of the same underlying idea, a class deliberately
invented to hold a cohesive set of stateless, domain-agnostic operations
(sorting, searching, wrapping a list as unmodifiable) that do not belong to
any single data-holding class, because the operations apply uniformly
across many unrelated collection types rather than being duplicated inside
each concrete collection implementation. This is a narrower,
function-library flavor of Pure Fabrication rather than the service-layer
flavor described above, and it illustrates that the pattern existed as a
practical habit in mainstream standard libraries well before GRASP gave it
a name.

## 10. Consequences

Positive consequences.

Domain classes stay focused on business rules and remain free of
technology-specific dependencies, which keeps them easier to unit test
without a database, a network, or a file system, and easier for a domain
expert or a new team member to read without wading through persistence or
transport code.

Cohesion improves for both sides of the split. the domain class now has one
reason to change, a business rule changing, and the fabricated class has one
reason to change, the technical mechanism changing, rather than either
class bearing two unrelated reasons to change at once.

Technical concerns become independently swappable. because the fabricated
class, not the domain class, is coupled to a specific database, file
format, or transport protocol, replacing that infrastructure (switching
databases, changing a serialization format) touches only the fabricated
class and whatever configures it, not the domain model or the business
logic that depends on it.

Reuse increases for the technical responsibility. a persistence-fabricated
class, once written, is typically reusable across every domain object of a
compatible shape, whereas persistence logic embedded per-domain-class tends
to be copied and adapted rather than genuinely shared.

Negative consequences.

The number of classes in the system grows, and every fabricated class is
one more name and one more file a reader has to learn before a mental model
of the codebase forms, which is a real cost even when each individual class
is simple.

The domain model, taken alone, no longer tells the full story of what the
system does. a reader looking only at the domain classes cannot tell how
orders are persisted, only that they exist and follow certain business
rules, so understanding the full behavior of the system requires
understanding the service and repository layer as well, which is more to
hold in working memory at once.

Over-application produces an anemic domain model, where so much behavior
has been extracted into fabricated service classes that the domain classes
degenerate into plain data structures with almost no behavior of their own,
a failure mode named directly in dimension 11 with its own citation.

Indirection can slow down debugging. a bug that manifests as wrong data in
a domain object may actually originate several fabricated classes away, in
a mapper, a repository, or a service that transformed the data incorrectly
before the domain object ever saw it, which lengthens the trace a developer
has to follow compared to a design where the same logic lived in one place.

## 11. Failure modes and misuse

The Anemic Domain Model is the most widely cited failure mode connected to
over-applying Pure Fabrication. Martin Fowler names and describes this
anti-pattern directly, writing that in an anemic domain model "you look at
the behavior and you realize there is hardly any behavior on these
objects, making them little more than bags of getters and setters," because
essentially all business logic has been extracted into a set of service
classes that sit on top of the domain objects (Martin Fowler,
"AnemicDomainModel," bliki, verified 2026-08-02,
https://martinfowler.com/bliki/AnemicDomainModel.html).

Symptom. the domain classes contain almost exclusively fields, getters, and
setters, and every operation, no matter how tightly it belongs to a single
object's own data, lives instead in a correspondingly named service class,
such as an OrderService whose methods take an Order object and manipulate
its fields externally rather than the Order object manipulating its own
fields internally.

Cause. Pure Fabrication's escape hatch was applied by default, on every
responsibility, rather than reserved for the specific cases in dimension 4
where the alternative genuinely damages cohesion or coupling.

Fix. per Fowler's own recommendation and echoed across GRASP secondary
literature, move behavior that operates purely on a single object's own
data back onto that object, and reserve fabricated service classes for
responsibilities that truly cross multiple domain objects or represent a
genuinely technical concern.

Fabrication sprawl, sometimes called the "manager class" or "helper class"
smell in code review practice, is the misuse of creating a new tiny
fabricated class for nearly every method, rather than grouping related
technical responsibilities cohesively.

Symptom. a package or namespace contains dozens of classes with generic,
low-information names like DataHelper, OrderUtils, or ProcessingManager,
each holding one or two methods with no strong internal cohesion connecting
them beyond having been extracted from somewhere else at some point.

Cause. "this does not fit neatly on a domain object" was treated as
sufficient reason to fabricate a new class, rather than checking whether an
existing fabricated class already covers a cohesive, related concern.

Fix. consolidate related technical responsibilities into fewer, more
clearly named fabricated classes organized by cohesive concern (a single
OrderRepository rather than separate OrderSaver, OrderLoader, and
OrderDeleter classes), and apply High Cohesion's own test to the fabricated
classes themselves, not only to the domain classes they were invented to
protect.

God-object fabrication is the opposite failure, where a single fabricated
class accumulates every technical responsibility in the system regardless
of whether those responsibilities are actually related.

Symptom. a class, often named something like ApplicationService or
SystemManager, that every other part of the codebase imports, and whose own
dependency list spans databases, email, file storage, and third-party APIs
at once, with dozens of unrelated public methods.

Cause. Pure Fabrication was treated as license to create exactly one
catch-all class for "everything that is not a domain object," rather than
fabricating a separate cohesive class per distinct technical concern.

Fix. split the god-fabrication along the same cohesion boundary that
motivated Pure Fabrication in the first place, one fabricated class per
genuinely distinct technical responsibility.

Leaky fabrication is a misuse where the fabricated class fails to fully
isolate the technical concern, so that infrastructure-specific types,
exceptions, or identifiers leak past the fabricated class's boundary into
the domain layer or the application code that calls it, defeating the
coupling benefit the pattern exists to provide.

Symptom. a domain-layer or application-layer method catches a
database-specific exception type, or holds a field typed as a database
library's row or cursor type, rather than a plain domain type.

Cause. the fabricated class's public interface was written in terms of the
infrastructure it wraps rather than in terms the domain layer already
understands.

Fix. consistent with Spring's `@Repository` exception translation behavior
described in dimension 8, the fabricated class translates every
infrastructure-specific type and error into a domain-appropriate type or a
technology-neutral exception at its own boundary, so that nothing
downstream of it ever needs to know which concrete infrastructure it wraps.

## 12. Trade-off matrix

| Force | Pure Fabrication | Information Expert (unmodified) | Anemic Domain Model (over-fabrication) | Active Record pattern |
|---|---|---|---|---|
| Domain class cohesion | High, technical concerns kept out | High if the responsibility genuinely fits the data owner | Low, domain classes become data-only | Low, mixes persistence with domain behavior |
| Coupling of domain classes to infrastructure | Low, isolated inside the fabricated class | Can become high if Expert forces a bad fit | Low for domain classes, but no behavior left to couple | High, domain object is directly coupled to its own storage |
| Reuse of technical logic | High, one fabricated class serves many callers | Low, logic is embedded per domain class | High for the fabricated logic, but domain behavior is not reusable in a meaningful sense | Low, persistence logic is duplicated per Active Record subclass |
| Number of classes, and how easy the codebase is to work through | More classes, more names to learn | Fewest classes, most direct to read | Most classes, and domain classes add little value on their own | Fewest classes, but each does two jobs |
| Testability of business rules without infrastructure | High, domain objects test in isolation | High when Expert's answer is a domain-only responsibility | Business rules live in services that often still need infrastructure to test | Low, testing domain behavior usually requires a database or a heavy mock |
| Representational fidelity to the domain | Reduced, adds classes with no domain meaning | Highest, every class maps to a concept | Misleading, domain classes look complete but hold no behavior | High for the entity itself, but the class conflates concept and mechanism |

Active Record, the pattern where a domain object is directly responsible for
its own persistence (common in Ruby on Rails and many lightweight ORMs), is
included here because it represents the opposite design choice from Pure
Fabrication at the same decision point, whether to let the domain object
own its persistence responsibility or to fabricate a separate class for it,
and comparing the two makes the trade explicit rather than presenting Pure
Fabrication as a free improvement.

## 13. Related and incompatible patterns

Information Expert is the pattern Pure Fabrication exists to override under
specific conditions, and the two are best understood as a matched pair. try
Information Expert first, reach for Pure Fabrication only when Expert's
answer would visibly damage Low Coupling or High Cohesion.

Low Coupling and High Cohesion are the two GRASP entries whose criteria
Pure Fabrication is explicitly optimizing for at the expense of
representational fidelity, and any evaluation of whether a fabrication was
justified should be measured against both of them directly, not against a
vague sense that "this feels cleaner."

The Single Responsibility Principle (see
`single-responsibility-principle.md`) and Pure Fabrication reinforce each
other in practice. a fabricated class that itself accumulates unrelated
responsibilities (the god-object fabrication failure mode in dimension 11)
violates SRP even though it technically satisfies the letter of "this class
does not represent a domain concept."

The Dependency Inversion Principle (see
`dependency-inversion-principle.md`) commonly composes with Pure Fabrication
in production code, the fabricated class is defined behind an interface
that the domain or application layer depends on, and a concrete
implementation of that interface is injected, which lets the fabricated
class's specific technology be swapped without touching any code that
merely depends on the abstraction.

The Repository pattern (Fowler, Patterns of Enterprise Application
Architecture) and the Data Access Object pattern (Sun's Core J2EE Patterns)
are named, specialized instances of Pure Fabrication applied specifically
to persistence, discussed in full in dimensions 8 and 9.

The Facade pattern from the Gang of Four catalog and Pure Fabrication are
often confused because both introduce a class with no domain meaning that
sits in front of a more complex subsystem. the distinction is intent.
Facade exists to simplify a client's interaction with an existing complex
subsystem by narrowing its interface, while Pure Fabrication exists to
relocate a responsibility away from a domain class to protect that domain
class's cohesion. A single class can, in practice, serve both roles at
once, but the two patterns answer different design questions and neither
implies the other.

Pure Fabrication has no formally incompatible pattern in the sense of two
patterns that cannot be applied to the same code at once. its tension is
with over-application of itself and with Information Expert applied too
strictly, both of which are covered above as forces and failure modes
rather than as incompatible patterns.

## 14. Refactoring path in and out

Introducing Pure Fabrication into existing code typically follows a small,
repeatable sequence. First, identify a domain class that carries a
responsibility visibly unrelated to its core business meaning, most often
recognizable because the class imports a technology-specific library (a
database driver, an HTTP client, a file format library) that the rest of
the class's methods never touch. Second, extract that responsibility's
methods into a new class named for the technical concern it represents,
following the naming conventions the codebase already uses for similar
concerns (Repository, Service, Mapper, Formatter). This step is a direct
application of the classic Extract Class refactoring (see this
repository's refactoring family for the general technique), specialized
here by the additional constraint that the extracted class should hold no
domain-model meaning of its own. Third, change the original domain class's
callers to invoke the new fabricated class directly for the extracted
responsibility, rather than continuing to call through the domain object.
Fourth, remove the now-unused technology-specific import and any
associated fields from the domain class, confirming that the domain class
compiles and tests pass without any reference to the extracted technical
concern. Fifth, where the codebase uses dependency injection, introduce an
interface for the fabricated class and have callers depend on the
interface rather than the concrete class, completing the Dependency
Inversion composition described in dimension 13.

Removing an over-applied Pure Fabrication follows the reverse path, and is
the appropriate fix for the anemic domain model failure mode. First,
identify a fabricated service class whose methods each take a single domain
object and manipulate only that object's own fields, with no cross-object
coordination and no genuine technical dependency (no database call, no
network call, nothing that would damage the domain class's cohesion if
moved). Second, for each such method, move the method's body onto the
domain object it operates on, following the Move Method refactoring,
adjusting the method to operate on the domain object's own fields directly
rather than through externally exposed getters and setters. Third, update
every caller of the old service method to call the domain object's own
method instead. Fourth, once every method of the fabricated class has
either been moved back to a domain object or confirmed to remain genuinely
technical (a true cross-object or infrastructure-dependent responsibility),
delete the fabricated class if it is now empty, or leave a smaller, more
honestly cohesive fabricated class behind if a real technical core
remains. The decision at each individual method is the same applicability
test from dimension 4, applied retroactively, does this specific piece of
logic genuinely need to live outside the domain object, or was it moved
there by habit.

## 15. Testing and verification

Pure Fabrication, applied correctly, is one of the clearest cases where a
design pattern directly improves testability, and the improvement is
measurable rather than assumed. Domain classes with technical concerns
removed can be unit tested with plain in-memory objects and no test double
for a database, a file system, or a network call, because the domain
class's own dependency graph no longer includes those concerns. This is the
single largest practical benefit engineers report from applying the
pattern, and it is why persistence-ignorant domain models are common
practice in test-driven development.

The fabricated class itself is tested differently, and typically needs one
of two strategies depending on what it wraps. When the fabricated class
wraps genuine external infrastructure (a real database, a real HTTP
endpoint), it is tested either with an integration test against a real or
containerized instance of that infrastructure, or with a test double, a
fake or stub implementation of the interface the fabricated class exposes,
substituted in place of the real infrastructure so that tests of the
fabricated class's own mapping and translation logic run quickly and
deterministically without network or disk access. When the fabricated class
is a pure computation over domain objects with no external infrastructure
(a formatter, a validator that touches only in-memory data), it can usually
be unit tested exactly like a domain class, with no test double required at
all.

Checking that a Pure Fabrication was correctly applied, rather than
over-applied into an anemic domain model, is best done by inspecting the
domain classes directly. a domain class with only getters, setters, and no
methods that enforce a rule or perform a calculation using its own fields
is the observable signal of over-fabrication, and it is worth treating as a
code review check specifically, not something caught only by a runtime
test. Conversely, a fabricated class whose public interface leaks an
infrastructure-specific type (a database row type, a raw HTTP response
object) into its method signatures is the observable signal of the leaky
fabrication failure mode from dimension 11, and can be checked mechanically
in many languages by scanning a fabricated class's public method signatures
for imports from an infrastructure-specific package.

## 16. Observability signals

A healthy Pure Fabrication shows up in production telemetry as a clean
separation of concern boundaries in traces and logs. a distributed trace or
an application performance monitoring span for a request that saves an
order should show a distinct span for the fabricated repository or service
call, separate from spans for pure business-rule evaluation, which makes it
possible to see at a glance whether latency in a given request is coming
from business logic or from the infrastructure the fabricated class wraps.

Error logs from a correctly bounded fabricated class should carry
technology-specific detail (a SQL error code, a connection timeout, an HTTP
status) at the point the fabricated class catches it, but should surface a
translated, domain-appropriate error to anything upstream of it, consistent
with the exception-translation behavior Spring documents for `@Repository`
in dimension 8. A log stream where domain-layer or application-layer code
logs raw driver-level exception types is the observability equivalent of
the leaky fabrication failure mode, and is a useful automated check, grep
production logs for infrastructure-specific exception class names appearing
outside the fabricated classes that are supposed to own them.

A failing fabricated class typically manifests as a spike in a narrow,
identifiable category of error, connection exhaustion, timeout errors, or a
specific external service's error codes, isolated to the operations that
pass through that specific fabricated class, which is itself a useful
observability property. because the fabricated class concentrates a single
technical dependency, an outage in that dependency produces a correlated,
easy-to-diagnose error pattern rather than scattered failures spread across
many unrelated domain classes that each independently touched the failing
infrastructure.

## 17. Security and privacy implications

Pure Fabrication concentrates a system's points of contact with external
infrastructure, databases, file systems, network services, into a small,
identifiable set of classes, which is a net security benefit for auditing
and access control. Reviewing which classes hold credentials, connection
strings, or API keys, and confirming that only the fabricated classes
responsible for a given infrastructure concern hold those secrets, is far
more tractable when persistence and transport logic is concentrated in
dedicated fabricated classes than when it is scattered across every domain
class that happens to need it.

The pattern also creates a natural, auditable boundary for input validation
and sanitization. because a fabricated persistence class is the single
place where domain data is translated into a query or a stored
representation, it is also the natural place to enforce parameterized
queries and reject unsafe input, rather than relying on every domain class
that might eventually be persisted to independently avoid an injection
vulnerability. This is analytical judgment rather than a sourced claim, the
concentration itself does not automatically prevent injection or other
vulnerabilities, it only creates a single, well-known place where the
defense needs to be correctly implemented, and a single missed case in that
one place is still a real vulnerability.

Privacy-sensitive data handling benefits similarly. when a fabricated
persistence class is the sole path through which personal data reaches
storage, applying encryption at rest, data retention policies, or
redaction rules can be implemented and audited in one location, rather than
verified independently across every domain class that happens to hold
personal data. The pattern is silent on how to implement any of these
protections correctly, it only concentrates where they need to be applied,
which is a real but partial security property, not a guarantee.

## 18. References

- Wikipedia contributors, "GRASP (object-oriented design)," Wikipedia, verified 2026-08-02, https://en.wikipedia.org/wiki/GRASP_(object-oriented_design)
- Craig Larman, *Applying UML and Patterns, An Introduction to Object-Oriented Analysis and Design and Iterative Development*, 3rd edition, Prentice Hall, 2004, chapter on GRASP responsibility assignment patterns (citation trail confirmed via the Wikipedia GRASP article and independently corroborated course and reference materials citing the same source text, verified 2026-08-02).
- Spring Framework Reference Documentation, "Classpath Scanning and Managed Components," Spring Framework, verified 2026-08-02, https://docs.spring.io/spring-framework/reference/core/beans/classpath-scanning.html
- Martin Fowler, "Repository," Patterns of Enterprise Application Architecture catalog, verified 2026-08-02, https://martinfowler.com/eaaCatalog/repository.html
- Martin Fowler, "AnemicDomainModel," bliki, verified 2026-08-02, https://martinfowler.com/bliki/AnemicDomainModel.html
- Oracle, "Data Access Object," Java technology documentation, https://www.oracle.com/java/technologies/data-access-object.html. This URL was identified during research but returned an access restriction on the verification date and could not be directly fetched and quoted. The DAO pattern's classification as a pure fabrication is instead sourced from the Wikipedia GRASP article's general service mapping plus multiple independent secondary technical sources describing the same DAO-as-fabrication relationship, cross-checked for consistency on 2026-08-02, flagged here as not verified against the primary source.
- Single Responsibility Principle entry, `single-responsibility-principle.md`, this repository, for the Constantine and Yourdon coupling lineage referenced in dimension 1.

## Code examples

### TypeScript

```typescript
interface Order {
  id: string;
  total: number;
}

class OrderRepository {
  private store = new Map<string, Order>();

  save(order: Order): void {
    this.store.set(order.id, order);
  }

  load(id: string): Order | undefined {
    return this.store.get(id);
  }
}

const repo = new OrderRepository();
repo.save({ id: "o1", total: 42 });
console.log(repo.load("o1"));
```

### Python

```python
class Order:
    def __init__(self, order_id: str, total: float):
        self.order_id = order_id
        self.total = total


class OrderRepository:
    def __init__(self):
        self._store = {}

    def save(self, order: Order) -> None:
        self._store[order.order_id] = order

    def load(self, order_id: str):
        return self._store.get(order_id)


repo = OrderRepository()
repo.save(Order("o1", 42.0))
loaded = repo.load("o1")
print(loaded.order_id, loaded.total)
```

### Go

```go
package main

import "fmt"

type Order struct {
	ID    string
	Total float64
}

type OrderRepository struct {
	store map[string]Order
}

func NewOrderRepository() *OrderRepository {
	return &OrderRepository{store: make(map[string]Order)}
}

func (r *OrderRepository) Save(o Order) {
	r.store[o.ID] = o
}

func (r *OrderRepository) Load(id string) (Order, bool) {
	o, ok := r.store[id]
	return o, ok
}

func main() {
	repo := NewOrderRepository()
	repo.Save(Order{ID: "o1", Total: 42})
	o, ok := repo.Load("o1")
	fmt.Println(o, ok)
}
```
