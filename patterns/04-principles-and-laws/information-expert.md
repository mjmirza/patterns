---
name: Information Expert
slug: information-expert
family: 04-principles-and-laws
category: Principle
aliases: [Expert, GRASP Expert]
first_described: "Larman 1997, Applying UML and Patterns, 1st edition"
maturity: canonical
related: [creator, low-coupling, high-cohesion, tell-dont-ask, single-responsibility-principle, anemic-domain-model, feature-envy]
incompatible_with: []
verified: 2026-08-02
---

## 1. Name, aliases, and lineage

The canonical name is Information Expert, shortened almost everywhere in
practice to just Expert. It is one of nine patterns collected under the name
GRASP, General Responsibility Assignment Software Patterns, a name Craig Larman
chose deliberately as a mnemonic device rather than a claim that these are
patterns in the Gang of Four sense. Larman introduced GRASP, and Information
Expert as its first and most used member, in the first edition of his book
Applying UML and Patterns in 1997, and the principle has been carried largely
unchanged through the second and third editions of that book. Verified against
the Wikipedia summary of the GRASP article, which states the principle was
introduced by Craig Larman through the 1997 book and lists Information Expert
among the nine GRASP principles alongside Creator, Controller, Indirection, Low
Coupling, High Cohesion, Polymorphism, Protected Variations, and Pure
Fabrication (https://en.wikipedia.org/wiki/GRASP_(object-oriented_design),
verified 2026-08-02).

Larman himself never presented GRASP as an invention of new ideas. He
described it, and this is a direct paraphrase of a documented position rather
than a quotation, as a naming device that packages design wisdom that was
already implicit in object-oriented practice, expert practitioners applying it
without naming it, so that it could be taught systematically to people new to
object design. The underlying idea that classes should hold the data and the
behavior that acts on that data together predates Larman by decades and traces
back to the very definition of encapsulation in Smalltalk and Simula, but
Information Expert is the specific name Larman gave to the resulting
responsibility assignment heuristic, and that name is the one the industry
uses today when discussing where a piece of logic belongs.

The pattern has no widely used alternate name distinct from Expert itself. It
is sometimes folded informally into discussions of Tell, Don't Ask, a closely
related but separately authored idiom associated with Alec Sharp and later
popularized by Martin Fowler, and into discussions of the Anemic Domain Model
anti-pattern that Fowler named as the failure mode of ignoring it. Those two
are related concepts, covered in dimension 13, not aliases for Information
Expert itself.

## 2. Problem and context

A team building an object model reaches a point, usually within the first
design session, where a piece of business logic needs a home. The question is
concrete and recurring. Given a responsibility, which class should own the
method that fulfills it. Two default answers are common and both are wrong
more often than they are right. The first default is to put the logic wherever
the developer happens to be working, often in a controller, a service class,
or a manager class that already exists and is easy to reach. The second
default is to put the logic in whichever class the developer thinks of first,
frequently the class that triggers the action rather than the class that holds
the data the action needs.

Information Expert names the actual criterion that should decide the
question. The responsibility belongs on the class, or the small set of
collaborating classes, that has the information needed to carry it out. This
is a recognition problem more than an invention problem. A developer with an
object model already drawn, containing an Order with a collection of
OrderLines, each carrying a price and a quantity, faces the concrete question
of where the method that computes the order's total should live. The
information needed is the list of line items and each line's price and
quantity. The Order and its OrderLines have that information. A separate
OrderTotalCalculator does not, and would need the Order to hand it over,
which immediately breaks encapsulation and forces the Order to expose its
internal structure to a class that has no other reason to know it.

The context in which this problem recurs is any object-oriented codebase past
its first few classes, and it recurs most sharply in the presence of what
Fowler later named the Anemic Domain Model, where the temptation to centralize
all logic in a small number of service classes has already taken hold. Once
that pattern establishes itself, every new feature reinforces it, because the
existing service classes are the path of least resistance, and Information
Expert becomes the corrective discipline that has to be reapplied consciously
on every new responsibility rather than assumed by default.

## 3. Forces

Several pressures compete when a responsibility is being assigned, and
Information Expert is the resolution Larman favors, but it is a resolution,
not a proof, so the tension is worth naming honestly, and this dimension is
largely engineering judgement rather than sourced fact.

Coupling versus cohesion is the central tension. Placing a responsibility on
the class that owns the data minimizes the number of getter calls needed to
gather that data elsewhere, which lowers coupling between classes, and it
keeps related data and behavior in one place, which raises cohesion. Against
this, a naive reading of Information Expert can push toward putting every
computation that touches a class's data onto that class, which over time can
bloat a single class with responsibilities that have little to do with each
other beyond sharing a data source, an outcome that actually harms cohesion
even while superficially following the letter of the principle. Larman
himself flags this tension by pairing Information Expert with High Cohesion
and Low Coupling as separate but related GRASP principles that must be
weighed together rather than Information Expert alone deciding every case.

Encapsulation versus convenience is the second force. Following Information
Expert usually means writing fewer public getters, because the class that
knows the data also does the work on it internally, which is the same
direction Tell, Don't Ask pushes. Against this, some designs genuinely need
query access to raw data, for serialization, for reporting, for a UI layer
that has to display the data in a form the owning class should not need to
know about, and an overzealous application of Information Expert can produce
classes that hide data a legitimate external consumer actually needs.

Team topology and ownership boundaries are a third force that classic GRASP
literature does not emphasize but that matters in real organizations. The
class that holds the information is not always the class a given team is
empowered to modify, particularly across service or module boundaries in a
distributed system, and Information Expert as stated assumes a single
in-process object model where any class can be extended freely. Crossing a
network or a bounded context boundary changes the calculus, covered in
dimension 4.

Testability is a fourth, favorable force. Concentrating a computation on the
object that owns its inputs generally makes that computation trivially unit
testable in isolation, because the test constructs the object with known data
and asserts on the result, with no need to mock a service, a repository, or a
collaborator that would otherwise have to supply the data externally.

## 4. Applicability and non-applicability

Reach for Information Expert when a new piece of business logic, a
calculation, a validation, a decision, or a transformation, needs a home and
the object model already contains a class or a small cluster of collaborating
classes that hold all the data the logic needs. It applies at its strongest
inside a rich domain model, the kind Fowler describes as the opposite of the
Anemic Domain Model, where entities and value objects are expected to carry
behavior. It applies particularly well to invariant enforcement, where an
object should never be allowed into an invalid state, because only the object
itself can guarantee that guard runs on every mutation.

Apply it when deciding between two or more candidate classes for a
responsibility and one of them clearly owns most of the needed data while the
others would need to query for it. Apply it when refactoring a service class
that has grown large by accreting logic that actually belongs on the domain
objects it operates against, which is the Move Method refactoring in reverse
direction from how the anti-pattern arose.

Do not apply Information Expert when the class that would become the expert
crosses a process, network, or persistence boundary from the data it would
need, because gathering that data would require a remote call, a query, or a
join that is expensive or fragile to perform inside what should be a cheap
in-memory computation. A price calculation that needs current exchange rates
from an external service does not belong inside the Order entity simply
because the Order has the amounts, because that would make Order responsible
for network I/O, violating separation of concerns and making the entity hard
to construct and test in isolation.

Do not apply it when the responsibility genuinely spans multiple objects with
no single clear owner and forcing it onto one of them would create an
arbitrary and coupling-increasing dependency on the others, the situation
Larman himself resolves by introducing a Pure Fabrication, a class invented
purely for cohesion and low coupling reasons that does not correspond to a
concept in the problem domain, rather than stretching Information Expert past
its useful range.

Do not apply it inside a strict layered architecture, particularly Domain
Driven Design's separation of Application Services from the Domain layer,
when the responsibility requires coordinating across aggregates or invoking
infrastructure, because giving one aggregate root direct behavioral
responsibility for another aggregate's data breaks aggregate boundaries and
transactional consistency guarantees. The coordination responsibility belongs
on an Application Service even though no single domain object is the
information expert for the whole use case.

Do not apply it to responsibilities that are fundamentally about
presentation, formatting for a specific UI, or serialization for a specific
wire format, because coupling a domain entity to those concerns, even though
the entity holds the raw data, pulls in dependencies the entity should not
carry and violates the Single Responsibility Principle at a different axis
than Information Expert addresses.

Do not apply it in immutable, purely functional codebases where the whole
notion of a class owning a mutating operation on its own state does not exist
in the same shape. The underlying idea, keep computation near its data,
survives in functional style as module-level functions colocated with the
type they operate on, but the object-oriented framing of a class assigning
itself a responsibility does not translate directly and forcing it produces
awkward stateful wrappers around what should be pure functions.

## 5. Structure

Information Expert does not prescribe a fixed cast of participant classes the
way a Gang of Four structural pattern does, because it is a responsibility
assignment heuristic applied during design rather than a reusable object
arrangement. The structure below names the roles the heuristic reasons about
each time it is applied.

The Responsibility is the specific piece of behavior under assignment, framed
as a question, who should know how to do this. It is usually phrased as an
operation signature before it has a home, for example computeTotal, or
validateAddress.

The Candidate Classes are every class in the current object model that could
plausibly host the Responsibility. In a well factored model there are usually
two or three real candidates, not dozens, because the model's own structure
narrows the field.

The Information Holder, or the Expert itself once chosen, is the candidate
class that possesses the largest share of the data the Responsibility needs
without querying outside its own state or its directly held collaborators.
This is the class the pattern assigns the Responsibility to.

The Collaborators are classes the Expert holds direct references to, and
whose own data the Expert is allowed to draw on without breaking
encapsulation, because those references are already part of the Expert's own
composed state, for example an Order holding a list of OrderLine objects.

The Rejected Candidates are classes that were considered and set aside
because fulfilling the Responsibility on them would require reaching outside
their own state into a peer class's private data, which is exactly the
coupling Information Expert exists to avoid.

## 6. ASCII structure diagram

```
  Before assignment, three candidates for computeTotal()

    +----------------+     +----------------+     +----------------+
    | OrderService   |     |     Order      |     |   OrderLine    |
    |----------------|     |----------------|     |----------------|
    | + computeTotal |?    | - lines: []    |?    | - price        |
    |   (order)      |     | + addLine()    |?    | - quantity     |
    +----------------+     +----------------+     +----------------+
       has NO direct           HOLDS the             HOLDS its own
       access to price/         collection of         price and
       quantity data            OrderLine objects     quantity

  Information Expert reasons that computeTotal needs every line's
  price times quantity, summed. Order holds the lines directly.
  Each OrderLine holds its own price and quantity directly.
  So the responsibility is assigned to Order, collaborating
  with OrderLine for each line's own subtotal.

  After assignment

    +-----------------------+        +-------------------+
    |         Order         |1      *|     OrderLine      |
    |------------------------|<>------|-------------------|
    | - lines: List<Line>    |        | - price: Money     |
    | + computeTotal(): Money|        | - quantity: int    |
    |   sum(l.subtotal()     |        | + subtotal(): Money|
    |     for l in lines)    |        +---------------------+
    +-------------------------+

    OrderService now only orchestrates, it never touches price
    or quantity directly.

    +----------------+
    | OrderService   |
    |----------------|
    | + checkout(o)  |----> calls o.computeTotal()
    +----------------+       never reaches into OrderLine
```

## 7. Dynamics

The dynamics of Information Expert are a design-time reasoning process rather
than a runtime interaction, so this dimension is presented as the decision
flow a designer walks through, followed by the resulting runtime call
sequence once the assignment is made.

```
  Design-time decision flow

  1. State the responsibility precisely as an operation with
     required inputs. "compute the order's grand total, in Money,
     given the order's line items."

  2. List every piece of information the operation genuinely
     needs. line items, each line's price, each line's quantity.

  3. For each candidate class, ask whether this class holds the
     needed information directly, or through a collaborator it
     already references. Score each candidate by how much of the
     needed information it holds without an external query.

  4. Pick the candidate with the strongest match. If two
     candidates tie or the information is genuinely split with no
     natural owner, consider a Pure Fabrication instead of forcing
     the assignment onto an arbitrary domain class.

  5. Assign the method to the winning class. Update any caller
     that previously gathered the data externally to instead call
     the new method and hand back only the result.

  Runtime call sequence after assignment

  Client            OrderService         Order            OrderLine
    |                    |                 |                  |
    | checkout()         |                 |                  |
    |------------------->|                 |                  |
    |                    | computeTotal()  |                  |
    |                    |---------------->|                  |
    |                    |                 | subtotal()       |
    |                    |                 |----------------->|
    |                    |                 |    price*qty     |
    |                    |                 |<-----------------|
    |                    |                 | (repeat per line,|
    |                    |                 |  sum results)    |
    |                    |     total       |                  |
    |                    |<----------------|                  |
    |     total          |                 |                  |
    |<-------------------|                 |                  |
    |                    |                 |                  |
```

The observable shift is that OrderService no longer holds a loop that reaches
into each OrderLine's price and quantity. It sends one message, computeTotal,
and receives one result. Every intermediate step happens inside the objects
that own the data, which is the concrete, testable outcome the principle
produces.

## 8. Implementation variants

The direct method variant is the textbook case, a single public method added
to the information-holding class, as shown in dimension 6 and 7. This is the
default and the one most GRASP literature illustrates.

The delegated collaboration variant applies when the information is split
across an object graph, an aggregate root delegating a sub-computation to
each child, then combining results, as the Order and OrderLine example shows.
The root is still the expert for the overall responsibility even though it
delegates parts of the work, because it alone holds the full collection and
the combining logic.

The Pure Fabrication variant is not strictly Information Expert but is the
documented escape hatch Larman himself provides when no single domain class
is a strong expert for a responsibility that spans several classes with no
natural owner, for instance a persistence responsibility. A
PersistenceMapper class is invented that holds no domain meaning but
achieves lower coupling than forcing a save method onto every domain entity
that would otherwise need direct database awareness.

The value object variant applies Information Expert to small immutable
types. A Money class that owns the amount and the currency is the expert for
its own arithmetic and comparison, so operations like add, multiply, and
isGreaterThan live on Money rather than being performed externally with raw
decimal fields extracted first. This variant is especially strong in
statically typed languages where a value object can enforce its own
invariants in the constructor and every subsequent operation stays type
safe.

The language-idiomatic closure variant appears in languages with
first-class functions. Rather than a full class becoming the expert, a small
function closed over the exact data it needs plays the same structural
role, most visible in JavaScript and Python codebases that favor free
functions taking a narrowly typed argument over classes with methods, while
still following the same underlying rule, do not scatter a computation
across code that has to reach for data it does not directly hold.

The record and companion-function variant appears in languages that
separate data definition from behavior more strongly than classic
object-oriented languages, for example Go, where a struct carries the data
and a set of functions taking a pointer to that struct as the first
argument play the role of methods. Information Expert still applies, the
function that computes a total is defined next to the struct it operates
on and takes that struct as its receiver, rather than living in an
unrelated package that has to import and unpack the struct's fields.

## 9. Known production uses

Domain Driven Design, the discipline Eric Evans formalized in his 2003 book
Domain-Driven Design, Tackling Complexity in the Heart of Software, is built
on the same underlying discipline Information Expert names, that entities and
value objects should carry the behavior that acts on the data they own rather
than exposing that data to external service classes. Evans's Entity and Value
Object patterns are widely implemented in production domain models across the
finance, logistics, and healthcare industries specifically because they push
business rules onto the objects that hold the relevant state, the same
placement criterion Information Expert names. This connection between
Information Expert and rich domain modeling is documented directly by Martin
Fowler, who frames the opposite failure mode explicitly as logic that should
be in a domain object being moved out into a series of methods of external
service classes, calling the resulting design "essentially a procedural
style design" (Martin Fowler, AnemicDomainModel,
https://martinfowler.com/bliki/AnemicDomainModel.html, verified 2026-08-02).

Java's BigDecimal class is a concrete, named standard-library example of the
principle in production. BigDecimal owns its unscaled value and its scale
internally, and every arithmetic operation, add, subtract, multiply,
divide, compareTo, is implemented as a method on BigDecimal itself rather
than as an external utility function that would need to reach into two
BigDecimal instances and manipulate their internal representation. This
design, shipped as part of the Java Class Library since JDK 1.1 and
documented in the current Java SE Platform API specification, is exactly the
value-object variant of Information Expert described in dimension 8, the
class holding the data is the class performing every operation on that data
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/math/BigDecimal.html,
package java.math, verified 2026-08-02).

Ruby on Rails's Active Record pattern, documented in the official Rails
guides, is a widely deployed production example of assigning behavior to the
class that holds the data, in this case a database-backed model class that
carries both its column data as attributes and the validation and business
logic methods that act on that data, following the same underlying
information-locality reasoning that Larman names explicitly as Information
Expert, even though Rails predates any formal citation of GRASP in its own
documentation. Active Record has been the default persistence layer for
Rails applications since Rails's initial 2004 release and remains so in
current Rails releases, making it one of the most widely deployed instances
of data-and-behavior colocation in production web software
(https://guides.rubyonrails.org/active_record_basics.html, verified
2026-08-02).

## 10. Consequences

Positive consequences. Encapsulation improves because the class that
performs an operation on its own data does not need to expose that data
through public getters to an external class, which shrinks the class's
public surface and makes its invariants harder to violate from outside.
Coupling drops because callers send one message and receive one result
rather than pulling multiple raw values out of an object and recombining
them externally, which also means a change to the internal representation
of the data, for instance switching from a raw decimal to a Money value
object, only touches the expert class rather than every external site that
used to read the raw fields. Cohesion rises because the class's public
methods form a coherent story about what the class does with its own data
rather than being an arbitrary bag of getters. Testability improves because
a unit test constructs the expert with known inputs and asserts on its own
output, with no need to mock a separate service that would otherwise
perform the computation externally. Traceability improves for maintainers,
because when a bug report says the total is wrong, there is one class, not
a scattered set of service methods, that owns the total's computation.

Negative consequences. Applied mechanically, Information Expert can bloat a
data-rich class with every operation that happens to touch its fields, even
operations that conceptually belong to a different responsibility,
producing a God Class that violates the Single Responsibility Principle
even while it technically satisfies Information Expert, because the class
remains the information holder for many unrelated concerns. It can also
produce classes that are hard to test in isolation from infrastructure if
the expert reasoning is stretched to include responsibilities that require
I/O, database access, or network calls, because those responsibilities do
belong near the data conceptually but carry dependencies a pure domain
object should not carry, a tension covered in dimension 4's
non-applicability list. It can increase the number of small delegating
methods across an object graph, as seen in the collaboration variant, which
some engineers experience as harder to trace with an IDE's find-usages
tooling compared to a single centralized service method, even though the
total coupling is lower.

## 11. Failure modes and misuse

Feature Envy is the most commonly observed symptom of Information Expert
violated in the opposite direction, where a method on class A spends most of
its logic reaching into class B's data through getters, computing something
that conceptually belongs on B.

Symptom. A method whose body is dominated by calls of the shape
other.getX(), other.getY(), combined locally, rather than a single call to
other.doSomething(). A production symptom engineers report is a service
class that keeps growing every sprint because every new feature's logic
gets added there by default, while the domain entities it operates on
remain thin wrappers around getters and setters.

Cause. The responsibility was assigned to the caller rather than to the
object that owns the data the responsibility needs, usually because the
caller was the easiest place to add one more line of logic at the time.

Fix. Martin Fowler and Kent Beck name Feature Envy directly as a code smell
in Fowler's Refactoring book and prescribe Move Method, moving the logic to
the class that actually owns the data, which is Information Expert applied
after the fact (Martin Fowler, Refactoring, Improving the Design of
Existing Code, 2nd edition, chapter 3, the Feature Envy smell).

The Anemic Domain Model is the named failure mode of systematically
ignoring Information Expert across an entire codebase rather than in one
method.

Symptom. Navigating to a class named Order shows only fields, getters, and
setters, while the actual meaning of an order, what makes it valid, how its
total is computed, what states it can transition through, is scattered
across OrderValidationService, OrderCalculationService, and
OrderStateService. Fowler describes anemic domain objects as having "almost
no behavior" (Martin Fowler, AnemicDomainModel,
https://martinfowler.com/bliki/AnemicDomainModel.html, verified
2026-08-02).

Cause. Every new feature's logic is added to a small set of existing service
classes by default, because they are the path of least resistance, rather
than being placed on the domain entity that owns the relevant data.

Fix. Systematically apply the Move Method refactoring described in
dimension 14, moving each piece of service logic to the entity that owns
the data it operates on, one responsibility at a time, verified by the
existing test suite after each move.

Misapplied Information Expert into a God Class is the opposite failure,
where a designer takes the principle to mean every operation touching a
class's fields belongs on that class, regardless of whether the operations
are conceptually related.

Symptom. A class with dozens of public methods spanning several unrelated
responsibilities, all justified individually by pointing at fields the
class happens to hold.

Cause. Information Expert applied without also weighing High Cohesion, the
sibling GRASP principle that asks whether a class's responsibilities form a
focused, related set.

Fix. Split the class along its actual responsibility boundaries, or
introduce a Pure Fabrication for the responsibilities that share only a
data dependency rather than a conceptual purpose.

Cross-boundary misapplication is the failure mode of applying Information
Expert past a service, process, or aggregate boundary.

Symptom. An entity method that internally performs a database query, a
network call, or reaches into a sibling aggregate's repository to gather
data it does not directly hold, producing a domain object with hidden
infrastructure dependencies that is difficult to construct in a unit test
without a running database or a mock server.

Cause. The responsibility was assigned by looking only at which class
conceptually owns the outcome, without checking whether fulfilling it would
require the class to acquire a dependency, such as a repository or an HTTP
client, that it should not carry.

Fix. Move the cross-boundary orchestration to an Application Service or a
Pure Fabrication, per dimension 4's non-applicability guidance, leaving the
domain entity with only the in-memory computation it can perform using data
it already holds.

## 12. Trade-off matrix

| Force | Information Expert | Service Layer centralization (anemic model) | Pure Fabrication |
|---|---|---|---|
| Coupling to data owner | Low. Caller sends one message, no external field access | High. Service must query every field it needs from each entity | Low. Fabrication holds only what it is explicitly given |
| Cohesion of the resulting class | High, when scoped correctly to related responsibilities | Low. Service accumulates unrelated logic that shares only a data dependency | Depends on fabrication's own scope, can be high if narrowly defined |
| Testability in isolation | High. Construct with known data, assert result, no mocks needed | Lower. Service usually needs a repository or entities as collaborators, often mocked | High, same as Information Expert if fabrication has no infrastructure dependency |
| Fit across process or network boundaries | Poor. Entity should not perform remote I/O | Good. Service is the natural place for orchestration across boundaries | Good. Fabrication is explicitly for cross-cutting concerns like persistence |
| Risk of violating Single Responsibility | Present if applied mechanically to every field-touching operation | Present, and typically worse, service accumulates every feature's logic over time | Lower, fabrication is created with one narrow purpose in mind |
| Discoverability for a new team member | High, once the codebase convention is understood, logic is where the data is | Higher initially, all logic is in one obvious place, but that place grows unmanageably | Moderate, requires knowing the fabrication exists and what it is for |

## 13. Related and incompatible patterns

Information Expert composes directly with High Cohesion and Low Coupling,
the two GRASP principles Larman presents alongside it as a triad that
should be weighed together rather than applied singly, since Information
Expert alone can be stretched into a violation of High Cohesion if a
designer assigns every data-adjacent responsibility to one class without
checking whether those responsibilities are actually related to each
other.

It composes with Creator, another GRASP principle, which answers a closely
related but distinct question, who should be responsible for instantiating
a new object, using a similar information-availability heuristic, that the
class which aggregates, contains, records, or closely uses instances of
another class is a natural candidate to create them.

It underlies Tell, Don't Ask, a separately named and separately authored
principle. Tell, Don't Ask, as Fowler describes it, is about instructing an
object to act rather than querying its state and acting externally, and it
is "a stepping stone towards co-locating behavior and data" (Martin
Fowler, TellDontAsk, https://martinfowler.com/bliki/TellDontAsk.html,
verified 2026-08-02). Information Expert is the responsibility-assignment
reasoning that decides which object gets told, and Tell, Don't Ask is the
calling convention that follows once that assignment is made.

It is the corrective principle against the Anemic Domain Model, named
directly in dimension 11, and it underlies the Rich Domain Model that
Domain Driven Design favors, where Entities and Value Objects, per Evans's
original formulation, are expected to carry both identity or value
semantics and the behavior that operates on their own state.

It is in tension with, though not strictly incompatible with, the
Transaction Script pattern that Fowler documents as an alternative to a
domain model for simple business logic, where a single procedural method
per use case is considered acceptable when the underlying logic is
genuinely simple and a rich object model would be over-engineering.
Information Expert assumes a domain model worth enriching exists, while
Transaction Script is a deliberate choice not to build one.

It relates to the Single Responsibility Principle, one of the SOLID
principles articulated by Robert C. Martin, in that both push toward
focused, cohesive classes, but they answer different questions. Single
Responsibility Principle asks whether a class has more than one reason to
change, while Information Expert asks which existing class should receive
a new responsibility. A class can satisfy Information Expert for a given
responsibility while still violating Single Responsibility Principle
overall if it has accumulated unrelated responsibilities over time, which
is the God Class failure mode in dimension 11.

## 14. Refactoring path in and out

Introducing Information Expert into code that lacks it starts by
identifying a Feature Envy symptom, a method whose body is dominated by
calls into another object's getters, combined locally into a result that
the calling class then uses. The refactoring path is Move Method,
documented by Fowler in Refactoring, Improving the Design of Existing Code.
Create the new method on the class whose data the old method mostly used,
copy the logic across, replace the field access inside the new method with
direct access to the now-local fields, then replace the body of the old
method with a single delegating call to the new method, verify the test
suite is still green, then remove the old method entirely once every call
site has been updated to call the new location directly rather than
through the old delegating shim. When the responsibility spans several
fields across multiple collaborating objects, the path instead becomes
Extract Method followed by Move Method applied iteratively, moving each
sub-computation to the object that owns its own slice of data, then
combining the results one level up at the true aggregate root, mirroring
the delegated collaboration variant in dimension 8.

Removing Information Expert, that is, deliberately pulling a
responsibility back out of the data-owning class, is the less common
direction but is sometimes correct when the responsibility has grown to
require dependencies the data-owning class should not carry, most often
persistence, network access, or presentation formatting. The path is the
reverse Move Method into a newly introduced Pure Fabrication or an
existing Application Service. Extract the offending logic into a new
method on the target class, have that method accept the data-owning object
as a parameter or a small set of extracted values rather than reaching
into its internals directly, replace the original method's body with a
delegating call to the new location, then once every caller has been
updated to call through the new location, remove the original method. This
is the correct direction when an entity has begun performing
infrastructure work internally, the cross-boundary misapplication symptom
named in dimension 11.

## 15. Testing and verification

Code that correctly follows Information Expert is straightforward to unit
test because the expert class can be constructed with known, literal input
data and its method called directly, with the assertion made against the
returned value, requiring no test double, no mock, and no stub for any
collaborator beyond the directly held ones already part of the object's
own composed state, as shown in the Order and OrderLine example, where a
test constructs an Order with two OrderLine instances of known price and
quantity and asserts the returned total equals the hand-computed expected
value.

What becomes harder to test is the boundary at which Information Expert
was correctly declined per dimension 4, the orchestration logic in a
service or application layer that coordinates several information experts
together with an infrastructure dependency such as a repository or an
external API client. That code genuinely needs mocks or fakes for the
infrastructure dependency, because unlike the domain objects it
coordinates, it cannot be tested purely in memory, and this is an expected
and correct cost, not a sign the boundary was drawn wrongly.

A useful verification technique specific to this principle is to write the
test for a candidate method before deciding where it lives, and to observe
how many collaborators the test has to construct or mock to exercise it. A
test that needs to construct and configure several unrelated objects just
to call one method is itself a signal, independent of code review, that
the responsibility may have been assigned to the wrong information expert,
or assigned as though the class were an expert when it is not, and the
test's own setup complexity becomes a proxy measurement for the coupling
the principle is meant to reduce.

Property based testing pairs well with Information Expert applied to value
objects, since a value object like Money or a date range that owns its own
arithmetic and comparison operations typically has algebraic properties,
such as commutativity of addition or transitivity of comparison, that a
property based test can assert hold for arbitrary generated inputs, giving
stronger coverage of the expert's own logic than a small number of
hand-picked example based tests would.

## 16. Observability signals

Information Expert itself is a design-time, static-structure principle, so
it produces no runtime metric or trace span of its own, and this dimension
is analytical judgement rather than a sourced claim about a specific
dashboard or monitoring tool.

The healthy signal in a codebase that is following Information Expert well
is static rather than runtime. A code review or a static coupling analysis
tool shows relatively low fan-out from service or controller classes into
domain entity internals, meaning service methods are short and call one or
two domain methods rather than chaining many getter calls, which several
static analysis tools, including SonarQube's Feature Envy style rules and
IDE inspections in IntelliJ and similar tooling, can surface directly as a
metric, classes with unusually high coupling to other classes' data.

The unhealthy signal, observable the same way, is the opposite pattern
growing over time. A small number of service or manager classes whose
lines of code and cyclomatic complexity climb every release while the
domain entities they operate on stay flat or shrink, a trend that a code
churn and complexity trend report, run periodically against the repository
history, will surface clearly as a widening gap between the growth rate of
a handful of god-like service classes and the rest of the codebase.

At runtime, an indirect signal worth watching in a system that has drifted
toward the Anemic Domain Model anti-pattern is elevated latency or
increased call volume on the handful of centralized service classes that
have become the de facto experts for most of the domain, since every
feature's logic funneling through the same few classes tends to also
funnel through the same few methods, making those methods disproportionate
hot spots in a profiler or an APM trace, a pattern that is a downstream
symptom of the anti-pattern rather than a direct measurement of the design
principle itself.

## 17. Security and privacy implications

Information Expert has a real, if indirect, security implication through
its effect on encapsulation. A class that follows the principle exposes
fewer raw getters for its sensitive fields, because operations on that
data happen internally rather than externally, which reduces the number of
code paths that have direct read access to sensitive values such as a
customer's payment details or personal identifiers, narrowing the attack
surface for accidental logging, accidental serialization, or accidental
inclusion in an error message compared to a design where every field is
exposed through a public getter for external services to consume freely.
This is engineering judgement about a general tendency rather than a
documented security guarantee, and Information Expert alone does not
enforce access control, encryption, or audit logging. It only tends to
concentrate the code paths that touch sensitive data into fewer classes,
which makes it easier to apply those protections consistently once a team
decides to.

The principle carries a smaller countervailing risk worth naming plainly.
Concentrating both data and the operations on that data into one class
also concentrates the blast radius of a defect in that class. A bug in an
information expert's own method can corrupt or leak data it holds more
directly than a bug in an external service that merely reads a getter and
computes something incorrectly outside the object, because the expert's
internal state is what other code trusts as the source of truth. This is a
correctness and defect-containment concern more than a security
vulnerability in the traditional sense, but it is relevant to threat
modeling in systems handling regulated data, where the class that is the
information expert for a sensitive field becomes a natural, single point
to audit and review carefully, which is itself a benefit for a focused
security review compared to auditing scattered getter access across an
entire service layer.

## 18. References

1. Craig Larman, Applying UML and Patterns, An Introduction to
   Object-Oriented Analysis and Design and Iterative Development, 3rd
   edition, Prentice Hall, 2004. The GRASP chapter, covering Information
   Expert as the first and most used GRASP pattern, ISBN 0131489062.
2. Wikipedia, GRASP (object-oriented design), summarizing Larman's 1997
   introduction of GRASP and the nine constituent principles including
   Information Expert.
   https://en.wikipedia.org/wiki/GRASP_(object-oriented_design), verified
   2026-08-02.
3. Martin Fowler, AnemicDomainModel, bliki entry describing the
   anti-pattern of separating domain data from domain behavior and its
   cost, contrasted directly with a rich domain model that follows
   Information Expert.
   https://martinfowler.com/bliki/AnemicDomainModel.html, verified
   2026-08-02.
4. Martin Fowler, TellDontAsk, bliki entry on the Tell, Don't Ask
   principle and its relationship to encapsulation and to co-locating
   data and behavior.
   https://martinfowler.com/bliki/TellDontAsk.html, verified 2026-08-02.
5. Martin Fowler, Refactoring, Improving the Design of Existing Code, 2nd
   edition, Addison-Wesley, 2018, chapter 3, the Feature Envy code smell
   and the Move Method refactoring used to correct it.
6. Eric Evans, Domain-Driven Design, Tackling Complexity in the Heart of
   Software, Addison-Wesley, 2003. The Entity and Value Object patterns
   that embody the same data-and-behavior colocation Information Expert
   names.
7. Oracle, Java SE 21 API specification, java.math.BigDecimal,
   documenting BigDecimal's arithmetic methods implemented on the class
   that owns the unscaled value and scale.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/math/BigDecimal.html,
   verified 2026-08-02.
8. Ruby on Rails Guides, Active Record Basics, documenting the Active
   Record pattern's colocation of a model's data attributes and its
   validation and business logic methods.
   https://guides.rubyonrails.org/active_record_basics.html, verified
   2026-08-02.
9. Robert C. Martin, the Single Responsibility Principle, one of the
   SOLID principles, as a related but distinct class-design principle
   discussed in dimension 13.

## Code examples

The example is the order-total scenario used throughout this entry. An
Order that owns a collection of OrderLine value objects computes its own
grand total, following Information Expert, rather than an external
service reaching into each line's price and quantity.

### TypeScript

```typescript
class OrderLine {
  constructor(private readonly price: number, private readonly quantity: number) {}
  subtotal(): number {
    return this.price * this.quantity;
  }
}

class Order {
  private lines: OrderLine[] = [];
  addLine(line: OrderLine): void {
    this.lines.push(line);
  }
  computeTotal(): number {
    return this.lines.reduce((sum, line) => sum + line.subtotal(), 0);
  }
}

const order = new Order();
order.addLine(new OrderLine(19.99, 3));
order.addLine(new OrderLine(4.5, 2));
console.log(order.computeTotal());
```

Compiled with `npx tsc` against a minimal `tsconfig.json` targeting ES2020,
transpiled cleanly with no errors, and the transpiled JavaScript executed
with `node` printing `68.97`.

### Python

```python
class OrderLine:
    def __init__(self, price: float, quantity: int) -> None:
        self.price = price
        self.quantity = quantity

    def subtotal(self) -> float:
        return self.price * self.quantity


class Order:
    def __init__(self) -> None:
        self.lines: list[OrderLine] = []

    def add_line(self, line: OrderLine) -> None:
        self.lines.append(line)

    def compute_total(self) -> float:
        return sum(line.subtotal() for line in self.lines)


if __name__ == "__main__":
    order = Order()
    order.add_line(OrderLine(19.99, 3))
    order.add_line(OrderLine(4.50, 2))
    print(order.compute_total())
```

Run with `python3`, printed `68.97`.

### Go

```go
package main

import "fmt"

type OrderLine struct {
	Price    float64
	Quantity int
}

func (l OrderLine) Subtotal() float64 {
	return l.Price * float64(l.Quantity)
}

type Order struct {
	Lines []OrderLine
}

func (o *Order) AddLine(l OrderLine) {
	o.Lines = append(o.Lines, l)
}

func (o *Order) ComputeTotal() float64 {
	total := 0.0
	for _, l := range o.Lines {
		total += l.Subtotal()
	}
	return total
}

func main() {
	order := &Order{}
	order.AddLine(OrderLine{Price: 19.99, Quantity: 3})
	order.AddLine(OrderLine{Price: 4.50, Quantity: 2})
	fmt.Println(order.ComputeTotal())
}
```

Run with `go run main.go`, printed `68.97`.

### Rust

```rust
struct OrderLine {
    price: f64,
    quantity: u32,
}

impl OrderLine {
    fn subtotal(&self) -> f64 {
        self.price * self.quantity as f64
    }
}

struct Order {
    lines: Vec<OrderLine>,
}

impl Order {
    fn new() -> Self {
        Order { lines: Vec::new() }
    }

    fn add_line(&mut self, line: OrderLine) {
        self.lines.push(line);
    }

    fn compute_total(&self) -> f64 {
        self.lines.iter().map(|l| l.subtotal()).sum()
    }
}

fn main() {
    let mut order = Order::new();
    order.add_line(OrderLine { price: 19.99, quantity: 3 });
    order.add_line(OrderLine { price: 4.50, quantity: 2 });
    println!("{}", order.compute_total());
}
```

Compiled and run with `rustc main.rs && ./main`, printed `68.97`.

Java and Swift were not run for this entry. The four languages above
already demonstrate the class based, struct plus method receiver, and
ownership based variants named in dimension 8 across a statically typed, a
dynamically typed, and a systems language, which covers the pattern's
real idiomatic range, so the two remaining languages were skipped rather
than run to keep the sample count proportionate to what each additional
language would newly illustrate.
