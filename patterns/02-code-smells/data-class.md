---
name: Data Class
slug: data-class
family: 02-code-smells
category: Object-Orientation Abusers
aliases: [Anemic Class, Dumb Data Holder, POJO-only Class]
first_described: "Fowler, Beck, Brant, Opdyke, Roberts 1999"
maturity: canonical
related: [anemic-domain-model, feature-envy, data-transfer-object, value-object, primitive-obsession]
incompatible_with: [rich-domain-model]
verified: 2026-08-02
---

# Data Class

## 1. Name, aliases, and lineage

The canonical name is Data Class. It appears in the code smell catalog inside
Martin Fowler, Kent Beck, John Brant, William Opdyke and Don Roberts,
*Refactoring. Improving the Design of Existing Code*, Addison-Wesley, 1999,
chapter 3, the "Bad Smells in Code" catalog. The catalog entry is short by
design, in keeping with the rest of the smells in that chapter, and describes a
class that "have fields, getting and setting methods for the fields, and
nothing else," concluding that "such classes are dumb data holders" that are
"almost always being manipulated in far too much detail by other classes"
([refactoring.guru's paraphrase of the Fowler definition confirms the same
shape](https://refactoring.guru/smells/data-class), verified 2026-08-02, used
here only to cross-check the definition, not as prose source). The second
edition of the book, 2018, keeps the same smell under the same name in the
"Data Class" section of the smells chapter and pairs it with the refactorings
Encapsulate Field, Encapsulate Collection, and Move Method.

The alias **Anemic Class** is used loosely in the wild for the same shape, but
it should be kept distinct in careful writing from **Anemic Domain Model**,
which is a related but larger-scope anti-pattern named separately by Fowler in
a 2003 blog post. A Data Class is a single offending class. An Anemic Domain
Model is a whole layer of a system built entirely from such classes, with all
the behavior pulled out into a separate set of "service" or "manager" classes
that operate on them. Every anemic domain model is built from Data Classes, but
a single Data Class sitting next to otherwise well-designed classes is not yet
an anemic domain model. This entry treats the class-level smell. See the
`anemic-domain-model` entry in this repository for the system-level anti-pattern.

**Dumb Data Holder** is the phrase Fowler uses in the book itself and is
sometimes used as an informal alternative name in code review comments.
**POJO-only Class** is a colloquialism specific to the Java community, playing
on the fact that a Plain Old Java Object is meant to be a class free of
framework coupling, not a class free of behavior, and pointing out that many
codebases collapse the two ideas.

A test that separates the smell from its legitimate cousins runs through this
entry. If a class exists purely so other code can read and write its fields,
and no operation naturally lives inside it, it is worth asking whether the
class is a smell or whether it is doing exactly the job a data-only class is
supposed to do, which is dimension 4 below.

## 2. Problem and context

A class is created to represent something, usually because a database table, an
external API payload, or a domain noun needs a type. The type accumulates a
field for every piece of data associated with that noun, and a getter and
setter for each field, following the JavaBeans convention or its equivalent in
another language. Over time the class grows fields as requirements grow, and no
behavior is ever added to it, because every operation that touches its data is
written as a static-ish free function or as a method on some other class that
receives the data class as a parameter and reaches into it through the
accessors.

The context in which this becomes a real problem is a codebase with a rich set
of relationships between data. When a Customer object's fields determine
whether the customer qualifies for a discount, and that qualification logic
lives in a DiscountCalculator class that calls five getters on Customer to
compute it, the knowledge of what makes a customer eligible is no longer
attached to the customer. It is attached to whichever class happened to need
the answer first. When a second class later needs the same answer, one of two
things happens, the logic is duplicated, or the second class also reaches
across into Customer and re-derives it, often slightly differently. Either
way, the data and the rules that govern the data have separated, and the class
that should own the rules has ended up being a passive container that the rest
of the system takes apart and reassembles by hand.

This is the specific failure Fowler's catalog is pointing at. Not that fields
and getters are wrong in themselves, but that a class with fields and getters
and literally nothing else is a signal that behavior which belongs with the
data has been extracted and scattered. The Data Class is not the disease. It is
the symptom that behavior went missing from where it should live.

## 3. Forces

**Encapsulation versus convenience of access.** A class with only getters and
setters offers maximum convenience to every caller, at the cost of exposing its
internal representation completely. Any caller can read any combination of
fields in any order and derive any conclusion it wants, which means the class
has no say in how its own state is interpreted.

**Cohesion versus the path of least resistance.** Adding a method to the class
that owns the data requires understanding the class's existing responsibilities
and reasoning about whether the new method belongs there. Adding a free
function, or a method on a service or manager class that already exists,
requires no such reasoning. Under time pressure the second path wins
repeatedly, and each time it wins the Data Class gets a little more anemic and
the service class gets a little larger.

**Serialization and transport versus domain modeling.** Data that crosses a
process boundary, a database boundary, or an API boundary genuinely wants to be
a flat, inert structure at that boundary. A struct-shaped type at a boundary
is doing its job correctly. The force appears when the same type is reused as
the in-process domain representation, so the boundary shape and the domain
shape are conflated, and the domain object inherits the boundary object's lack
of behavior by construction rather than by design (dimension 4 develops this
distinction in full).

**Team topology and ownership.** In a codebase where the data model is owned by
one team, or generated from a schema, and the business logic is owned by
another team that only consumes the model, the Data Class shape is often not an
accident of laziness but a structural consequence of who is allowed to change
what. Data Classes proliferate at organizational seams even when every
individual engineer would prefer to attach behavior to the data.

**Refactoring cost versus refactoring benefit.** Moving a method from a service
class into the data class it operates on is a small, mechanical change in
isolation (dimension 14), but it can ripple through every caller that currently
calls the free function or the service method, so the true cost scales with the
number of call sites, not with the size of the method being moved. This is the
force the pattern's critics point to when they argue the smell is easy to name
and expensive to fix in a large, already-shipped codebase.

## 4. Applicability and non-applicability

**When it is a genuine smell, worth fixing.**

- A class exposes public getters and setters for every field, and there exists,
  somewhere else in the codebase, a method that does nothing but read several
  of those getters, combine the values with some logic, and return a result,
  with no state of its own. That logic is a candidate to move onto the data
  class (Feature Envy, a closely related smell, is often diagnosed at exactly
  this call site).
- The class is mutable, is treated as the authoritative in-memory
  representation of a domain concept, and yet no invariant about its fields is
  enforced anywhere. Any combination of field values is accepted, even
  combinations that make no domain sense, because validation was never given a
  home.
- Multiple classes independently reimplement the same derived calculation from
  the same data class's fields, because the calculation was never centralized
  onto the data class itself.
- The class is at the center of a domain model that is meant to encode business
  rules, and the business rules are instead scattered across a layer of
  service, manager, or helper classes that all take the data class as
  a parameter. This is the anemic domain model pattern described by Fowler in
  2003, and the individual data classes inside it are this smell multiplied.

**When it is NOT a smell, and treating it as one causes harm.**

- **Data Transfer Objects.** A class whose entire job is to carry data across a
  process boundary in order to reduce the number of remote calls is correctly a
  flat, behaviorless structure. Fowler's own Patterns of Enterprise
  Application Architecture describes DTO exactly this way. "An object that
  carries data between processes in order to reduce the number of method
  calls," with the goal of batching data for a costly remote call rather than
  making many cheap in-process calls (Martin Fowler, *Patterns of Enterprise
  Application Architecture*, Addison-Wesley, 2002, and the companion catalog
  page [Data Transfer
  Object](https://martinfowler.com/eaaCatalog/dataTransferObject.html), verified
  2026-08-02). Attaching business logic to a DTO defeats its purpose, which is
  to be an inert, serializable envelope that both sides of a boundary can agree
  on independently of either side's domain model.
- **Value Objects.** A class that represents a value rather than an entity,
  where equality is defined by the values of its fields rather than by
  identity, and which is immutable by design, is not a smell even when its only
  methods are accessors, a constructor, equals, and hashCode. Fowler
  describes value objects as "objects that are equal due to the value of their
  properties" and lists money, a date range, and a coordinate pair as examples,
  and treats immutability as essential to the pattern, precisely so the object
  can be passed around freely without anyone needing to track who else holds a
  reference to it ([Martin Fowler, "ValueObject" bliki
  entry](https://martinfowler.com/bliki/ValueObject.html), verified
  2026-08-02). Domain-Driven Design formalizes the same idea as the Value
  Object building block, distinct from an Entity, precisely because a value
  object's whole reason to exist is to be its data (Eric Evans, *Domain-Driven
  Design. Tackling Complexity in the Heart of Software*, Addison-Wesley, 2003,
  chapter 5, "A Model Expressed in Software"). The distinguishing test between
  a Value Object and a smelly Data Class is not "does it have behavior," it is
  "does its equality and its lifecycle match its values." An immutable class
  whose two instances with the same field values are and should be
  interchangeable is a Value Object doing its job. A mutable class whose
  identity is meant to persist across changes, but which still has no behavior
  of its own, is the smell.
- **Generated code at a serialization boundary.** A class generated from a
  Protocol Buffer .proto file, a JSON Schema, an OpenAPI spec, or a database
  ORM's reflection of a table, is expected to be data-only, because the
  generator's job is to mirror an external schema faithfully, and mixing
  hand-written business logic into generated code creates a maintenance trap
  where regenerating the file silently deletes the logic. The correct pattern
  here is to keep the generated type as a Data Class on purpose and to wrap it,
  or map it, into a separate domain type that does carry behavior, rather than
  editing the generated file.
- **Records and similarly purpose-built immutable data carriers.** A type
  declared specifically to be an immutable aggregate of named components, such
  as a Java record, a Kotlin data class, a C# record, or a Python
  frozen dataclass, is not exhibiting the smell merely because it was
  declared with a keyword that generates accessors, equality, and a string
  representation automatically. The Java Language documentation for records
  states they are "a special kind of class... to model plain data aggregates
  with less ceremony" and that declaring one generates private final fields,
  public accessors, a canonical constructor, equals, hashCode, and
  toString for you (Oracle, ["Records" in the Java SE 17
  documentation](https://docs.oracle.com/en/java/javase/17/language/records.html),
  verified 2026-08-02). A record is the language's own admission that
  data-only aggregates are a legitimate, first-class need, not merely a smell
  tolerated because nobody got around to fixing it. The same reasoning applies
  to Lombok's @Data annotation, which generates "all the boilerplate that is
  normally associated with simple POJOs (Plain Old Java Objects) and beans"
  ([Project Lombok, "@Data"
  feature page](https://projectlombok.org/features/Data), verified 2026-08-02).
  Lombok's @Data is a tool for producing data classes efficiently, and using
  it on a genuine DTO or value object is appropriate. Using it on a type that
  is meant to be the seat of domain behavior, purely to avoid writing the
  behavior, reintroduces the smell mechanically and at scale.

**The distinguishing test, stated once and reused throughout this entry.** Ask
whether the class's job is to represent a value or transport a payload, or
whether its job is to be a domain concept that other code is currently only
allowed to look at from the outside. Representing and transporting are
legitimate uses for a data-only shape. Being a domain concept without owning
any of that concept's rules is the smell.

## 5. Structure

**Participants.**

- **The Data Class.** Holds a set of private or public fields, exposes a getter
  and a setter for most or all of them, and defines no method whose body
  contains meaningful logic beyond returning or assigning a field. It has no
  knowledge of the rules that govern combinations of its own fields.
- **The envious caller(s).** One or more other classes, often named with a
  Service, Manager, Processor, Calculator, or Validator suffix,
  that hold the actual behavior associated with the data class's concept. Each
  envious caller receives a reference to the data class, calls several of its
  getters, and computes something with the retrieved values. This participant
  is where Feature Envy typically manifests as the observable symptom of the
  Data Class smell.
- **The invariant that has no owner.** An implicit rule about which
  combinations of the data class's field values are valid, which exists only
  as scattered if checks inside the envious callers, never as a single
  enforced rule inside the data class's constructor or setters.

## 6. ASCII structure diagram

```text
  Legitimate design (behavior lives with data)
  +------------------+
  |    Customer      |
  |------------------|
  | - loyaltyYears   |
  | - totalSpend     |
  |------------------|
  | isEligibleForVIP()|<--- rule lives here, with the data
  +------------------+
           ^
           | calls
  +------------------+
  |   OrderService    |
  +------------------+


  Data Class smell (behavior scattered around data)
  +------------------+
  |    Customer      |
  |------------------|
  | - loyaltyYears   |
  | - totalSpend     |
  |------------------|
  | getLoyaltyYears()|
  | getTotalSpend()  |<--- only accessors, no rule
  +------------------+
       ^        ^
       |        |
  +---------+ +---------+
  | Order   | | Discount|
  | Service | | Service |
  |---------| |---------|
  | reads   | | reads   |
  | 2 fields| | 3 fields|
  | of Cust.| | of Cust.|
  | to dec- | | to dec- |
  | ide VIP | | ide %   |
  | (dupl.) | | (dupl.) |
  +---------+ +---------+
```

## 7. Dynamics

```text
  Runtime flow when the smell is present

  Client            OrderService          Customer (Data Class)
    |                    |                        |
    | placeOrder(cust)   |                        |
    |------------------->|                        |
    |                    | getLoyaltyYears()       |
    |                    |----------------------->|
    |                    |<---- 4 -----------------|
    |                    | getTotalSpend()          |
    |                    |----------------------->|
    |                    |<---- 1200.00 -----------|
    |                    |                        |
    |                    | if (years >= 3 &&       |
    |                    |     spend >= 1000)      |
    |                    |    -> treat as VIP       |
    |                    |  (rule computed here,   |
    |                    |   not inside Customer)  |
    |                    |                        |
    |<-------------------|                        |


  Runtime flow after Extract Method / Move Method fix

  Client            OrderService          Customer
    |                    |                        |
    | placeOrder(cust)   |                        |
    |------------------->|                        |
    |                    | isEligibleForVIP()      |
    |                    |----------------------->|
    |                    |          (Customer checks its
    |                    |           own loyaltyYears and
    |                    |           totalSpend internally)
    |                    |<---- true --------------|
    |<-------------------|                        |
```

## 8. Implementation variants

**The JavaBeans-shape variant.** A class following the JavaBeans convention
(no-argument constructor, a getX/setX pair per property) is the most common
concrete instance of the smell in Java, C#, and languages that copied the
convention, and it is often produced automatically by ORM code generators,
IDE "generate getters and setters" actions, or annotation processors, which
makes it easy to end up with the shape without ever deciding to build it.

**The struct-in-a-class variant.** Languages with a native lightweight record
type (Kotlin data class, C# record, Python dataclass, Swift struct)
still allow the smell, because the language feature only automates the
boilerplate. It does not prevent a developer from also declaring a mutable,
identity-bearing domain concept using the same feature purely to save typing.
The presence of the keyword is not proof of legitimacy, and dimension 4's
distinguishing test still applies to a record or data class that is being
used as a mutable domain entity rather than as a value.

**The anemic-entity-with-repository variant.** In layered architectures
following an older N-tier convention, the entity layer is deliberately kept
free of behavior so that a separate business logic layer, sometimes literally
called the Business Logic Layer, can own all rules. This is the smell at
architectural scale, and it is the shape Fowler specifically criticized as the
Anemic Domain Model in 2003, arguing that the approach throws away the central
benefit of object orientation, which is co-locating data and the behavior that
acts on it.

**The public-field variant.** In languages without an accessor convention at
all, the smell degrades one step further into a class with entirely public
mutable fields and no accessor methods either. This removes even the
theoretical possibility of validating a write, since any code anywhere can
assign directly to a field. C's struct, when used inside a codebase that also
has classes with real methods elsewhere, exhibits this variant, though in a
pure C codebase it is simply the idiom rather than a smell, because C has no
mechanism for attaching behavior to a struct in the first place.

## 9. Known production uses

The point of naming this smell is that it is genuinely common in shipped
systems, not that it is rare. Three concrete, sourced instances.

- **Early java.awt.Point and java.awt.Dimension in the Java standard
  library** expose fully public, mutable fields (x, y for Point;
  width, height for Dimension) with no invariant enforcement at all, a design Josh
  Bloch, the API designer who later wrote the language's most cited style
  guide, calls out directly. Item 16 of his book argues that "in public
  classes... you should always use accessor methods rather than public
  fields," citing exactly this style of AWT class as the counter-example of
  what not to do, because it "compromises the ability to change the class's
  internal representation" once the field is public API (Joshua Bloch,
  *Effective Java*, 3rd edition, Addison-Wesley, 2018, Item 16, "In public
  classes, use accessor methods, not public fields"). Point and Dimension
  predate that advice and remain in the JDK as a widely cited illustration of
  the smell in a system used by essentially every desktop Java application
  written since 1995.
- **Lombok's @Data and @Value annotations**, used across a very large
  fraction of enterprise Java codebases, exist specifically to mechanize the
  production of exactly this class shape, and the project's own documentation
  describes the generated output as "the boilerplate that is normally
  associated with simple POJOs... and beans" ([Project Lombok, "@Data" feature
  page](https://projectlombok.org/features/Data), verified 2026-08-02). Its
  widespread adoption is itself evidence of how common the shape is in
  production Java, since a tool whose entire purpose is auto-generating a
  pattern only becomes popular once the pattern is ubiquitous enough to be
  worth automating.
- **Protocol Buffer generated message classes**, used by Google internally
  and by a large share of the microservice ecosystem for RPC payloads
  (gRPC and its predecessors), are generated as data-only classes by design.
  The .proto compiler emits a type with fields, getters, and builders and
  deliberately does not offer a mechanism for the developer to inject domain
  behavior into the generated class itself, which is the correct application
  of the shape at a serialization boundary rather than an instance of the
  smell (dimension 4). Teams that then use the generated protobuf type
  directly as their in-process domain model, instead of mapping it into a
  richer type, are the ones who reintroduce the smell by conflating boundary
  and domain concerns. The generated class in isolation is doing its job.

## 10. Consequences

**Positive** (why the shape persists even where it is a smell).

- Trivially easy to serialize, since a flat structure with public accessors
  maps directly onto JSON, a database row, or a wire format with no custom
  logic required.
- Easy for a new team member to understand at a glance. There is no hidden
  behavior to learn, only a list of fields.
- Fast to build under time pressure, since adding a field and its accessor
  pair requires no design decision about where a rule belongs.
- Compatible with reflection-based tooling (ORMs, serializers, mock
  frameworks, IDE code generation) that expects the JavaBeans shape or its
  equivalent.

**Negative.**

- Domain rules end up duplicated across every caller that independently
  derives the same conclusion from the same fields, and the duplicates drift
  out of sync as one caller is updated and the others are not.
- The class cannot protect its own invariants, so it is possible to construct
  or mutate it into a domain-nonsensical state (a negative age, an order with
  a ship date before its order date) and nothing in the type system or the
  class itself will object.
- Feature Envy accumulates around the class as more and more logic is written
  against its getters rather than inside it, which in turn increases coupling.
  Every caller that reaches into the data class's fields must be revisited if
  the data class's internal representation ever changes, even though the
  whole point of accessor methods was supposed to be hiding that
  representation.
- Testing the business rule requires instantiating both the data class and the
  service class that holds the rule, and asserting on the interaction between
  them, rather than testing a single class in isolation, which is a symptom
  covered in more depth in dimension 15.
- At scale, this produces the Anemic Domain Model, which Fowler characterizes
  as discarding the central idea of object orientation, since the objects have
  been reduced to bags of data manipulated by procedural code dressed up in
  classes, and the resulting design is closer in spirit to a procedural
  program with an object-oriented veneer than to an object-oriented one.

## 11. Failure modes and misuse

**Symptom.** The same conditional expression, checking the same two or three
fields of the same class, appears in more than one place in the codebase, with
slightly different results.
**Cause.** The rule those fields encode was never given a home on the class that
owns the fields, so every caller that needs the answer re-derives it, and
without a single source of truth the re-derivations diverge over time as one
call site is patched for an edge case and the others are not.
**Fix.** Apply Move Method or Extract Method to pull the shared logic onto the
data class as a named method (isEligibleForVIP()), then have every caller
delegate to it, per dimension 14.

**Symptom.** A change to one field's meaning, for example switching totalSpend
from lifetime spend to spend in the last 12 months, requires touching many
unrelated classes across the codebase, not just the data class itself.
**Cause.** The field's meaning was interpreted independently by every caller that
read it, instead of being interpreted once, inside the class, and exposed
through a stable, semantically named method.
**Fix.** Introduce an intention-revealing method on the data class
(getRecentSpend()) and route every call site through it, so a future
reinterpretation of the underlying field only requires editing the one method.

**Symptom.** Unit tests for a business rule instantiate two or three classes
together, the data class plus one or more service classes, even though the
rule conceptually concerns only the data.
**Cause.** The rule's logic and the data it depends on live in different classes,
so testing the rule in isolation is not possible without also constructing
whatever holds the logic.
**Fix.** After moving the logic onto the data class, the corresponding test can
construct only the data class and assert on its method directly, which is a
concrete, observable signal that the fix worked (developed further in
dimension 15).

**Symptom.** The class can be put into a state that violates an obvious domain
rule, a DateRange whose end precedes its start, a Percentage set to 250,
and no exception, validation error, or compile-time check catches it.
**Cause.** Setters accept any value of the declared type with no validation, and
no invariant is checked in the constructor either, because the class was never
treated as responsible for its own consistency.
**Fix.** Add validation to the constructor and to any setter that could break an
invariant, and where the value is genuinely fixed after construction, remove
the setter entirely and make the class immutable, moving it toward a proper
Value Object where that is what the domain concept actually is.

**Misuse in the opposite direction.** Over-correcting a legitimate DTO or Value
Object by adding domain logic to it because a linter or a well-meaning
refactor flagged it as a Data Class.
**Symptom.** A class used purely to carry a payload across a serialization
boundary starts to accumulate business rules, and the boundary and the domain
model become entangled, so a change to a business rule now requires
regenerating or hand-editing generated code, or a change to the wire format
now risks breaking business logic that should have been independent of it.
**Cause.** The distinguishing test in dimension 4 was skipped, and the smell
detector, human or automated, treated "has only accessors" as sufficient
evidence of a problem without asking whether the class's job was to represent
a value or transport a payload in the first place.
**Fix.** Keep the boundary type as a data-only class, and if behavior is genuinely
needed, introduce a separate domain type and a mapping function between the
two, rather than adding behavior to the boundary type directly.

## 12. Trade-off matrix

| Force | Data Class (kept as-is) | Rich Domain Model (behavior moved in) | Data Transfer Object (kept data-only, on purpose) |
|---|---|---|---|
| Ease of serialization | High, flat structure maps directly to wire formats | Lower, may need explicit mapping to a boundary shape | High, this is the type's entire purpose |
| Encapsulation of invariants | None, any combination of field values is representable | Strong, the class enforces its own rules | Not applicable, the type has no invariants of its own to enforce |
| Risk of duplicated logic | High, every caller re-derives the same conclusions | Low, one canonical implementation | Not applicable, the type carries no logic |
| Testability of the domain rule | Requires instantiating the class plus whichever service holds the logic | Requires instantiating only the class itself | Not applicable |
| Coupling to internal representation | High, callers reach directly into fields via accessors | Low, callers call named, intention-revealing methods | Acceptable, the shape is meant to be visible at the boundary |
| Fit for a serialization boundary | Coincidentally adequate, but for the wrong reason (no logic to strip) | Poor without an explicit mapping step | Ideal, this is the pattern's designed purpose |
| Fit as the in-process domain representation | Poor, invites an anemic domain model at scale | Ideal | Poor, conflates boundary concerns with domain concerns |

## 13. Related and incompatible patterns

**Feature Envy** is the sibling smell, and in practice the two are usually
diagnosed together. A Feature Envy finding almost always points at a method
that is envious of a Data Class's fields, and fixing the Feature Envy by
moving the envious method onto the class it envies is frequently the same
refactor that eliminates the Data Class smell. They are two names for the same
underlying design defect, viewed from opposite sides of the relationship.

**Anemic Domain Model** is the system-scale version of this smell. A codebase
can contain a single, isolated Data Class without being an anemic domain model
overall, but an anemic domain model is, by definition, built from Data Classes
throughout its entity layer, paired with a service layer that holds all the
behavior those entities lack.

**Primitive Obsession** compounds this smell rather than causing it directly. A
Data Class that stores a String for an email address or an int for a
percentage, instead of a small Value Object type, has two separate problems at
once, and Extract Class or Introduce Parameter Object is often the shared fix
for both.

**Value Object and Data Transfer Object are the patterns this smell is most
often confused with**, as developed at length in dimension 4, and the
relationship there is not composition but distinction. Recognizing that a
given class is legitimately one of these two patterns is how a reviewer avoids
misapplying this smell's fix.

**Rich Domain Model is the explicit alternative this smell is contrasted
against.** Where a rich domain model puts business rules on the objects that
own the relevant data, this smell's fix (Move Method, Encapsulate
Field) is the mechanical steps that get a codebase from one state toward the
other. A codebase committed to a rich domain model treats new Data Classes,
outside the boundary contexts described in dimension 4, as a design review
finding.

## 14. Refactoring path in and out

**Introducing the shape** is rarely deliberate, but happens. A Data Class is
usually introduced by accident, through an IDE's "generate getters and
setters" action, an ORM's reverse-engineered entity, or copy-pasting a similar
class and stripping its methods, rather than through a deliberate design
decision. The one deliberate introduction path is dimension 4's legitimate
uses. Choosing to build a DTO or a Value Object on purpose, in which case the
introduction is simply declaring the class with only the fields and
accessors it needs, and stopping there.

**Removing the smell, step by step, following Fowler's catalog.**

1. **Encapsulate Field.** If any field is still public, wrap it behind a
   getter and setter first, so every subsequent step has a stable point to
   intercept reads and writes. In languages with a native property syntax this
   step may already be satisfied.
2. **Find the callers that are envious.** Search the codebase for methods that
   call multiple getters on the same instance of the data class in order to
   compute something, especially methods whose names describe a decision or
   calculation about the data class's concept (isEligible, calculateTotal,
   formatFor). These are the candidates for the next step.
3. **Move Method.** For each envious method identified in step 2, move its body
   onto the data class, changing its parameter list so it operates on the
   class's own fields instead of on a passed-in instance, and update every
   call site to call the new method on the instance instead of calling the
   free function or service method. Where the method only partially concerns
   the data class, Extract Method first to isolate the part that does, then
   move only that part.
4. **Encapsulate Collection.** If the class exposes a raw collection field
   through a getter that returns the mutable collection directly, replace the
   accessor with methods that add or remove one element at a time, or that
   return an unmodifiable view, so external code cannot corrupt the collection
   invisibly.
5. **Remove Setter, where mutability was never actually required.** Once
   behavior has moved onto the class, revisit each setter and ask whether
   external code still legitimately needs to change that field after
   construction. Where the answer is no, remove the setter and, where every
   setter is gone, consider making the class immutable and moving it toward a
   Value Object.
6. **Re-run the distinguishing test from dimension 4** on what remains. If,
   after moving behavior in, the class turns out to genuinely have no rules of
   its own, that is a signal the class was a legitimate DTO or Value Object
   all along, not a smell, and steps 2 through 5 should stop rather than force
   behavior onto a class that has none to hold.

**Removing the pattern once it is no longer earning its place.** A class that
was deliberately built as a rich domain object can regress back toward a Data
Class if new requirements keep adding fields but the corresponding logic keeps
landing in a nearby service class out of habit. The refactor back out is the
same Move Method step run in reverse discipline. At each code review, ask
whether the new logic belongs on the object whose data it touches, before it
accumulates into an envious method elsewhere.

## 15. Testing and verification

**What becomes harder to test while the smell is present.** A business rule
that depends on a data class's fields, but lives inside a separate service
class, cannot be unit tested by constructing the data class alone. The test
must also construct the service class, wire any dependencies the service class
requires, and then call the service method, passing the data class instance
in. This inflates the test's setup code and couples the test to the service
class's constructor signature, so a change to the service class's unrelated
dependencies can break tests that are conceptually only about the data
class's rule.

**What becomes easier to test after the fix.** Once the rule is moved onto the
data class itself (dimension 14, step 3), the corresponding test constructs
only the data class, sets its fields to the values under test, calls the
method, and asserts on the return value. No additional class needs to be
constructed or mocked. This is a concrete, mechanical signal that a Move
Method refactor genuinely succeeded. If the test for the moved behavior still
requires constructing anything beyond the data class, the move was incomplete
or the logic still depends on state the data class does not itself own.

**Test doubles that apply.** Because a correctly-fixed data class holds its
own logic and has no external collaborators, it typically needs no test double
at all, only direct instantiation with representative field values, including
boundary values for any invariant the class now enforces (dimension 11's
validation fix). Where the smell is still present, testing the envious service
class typically requires either a real instance of the data class (cheap,
since it has no behavior to fake) or, if the service also has other
dependencies, mocks or stubs for those, which is a good practical tell that
the test's true subject is entangled with concerns beyond the rule itself.

**A characterization-test strategy for large-scale remediation.** In a
codebase with an entrenched anemic domain model, attempting the full
refactoring path across every data class at once is rarely realistic. A
practical sequencing is to write characterization tests, tests that pin down
current observed behavior even where that behavior has not been formally
specified, against the existing service-layer methods before moving them, so
that the Move Method refactor in dimension 14 can be verified against a
pre-existing behavioral baseline rather than trusted on inspection alone.

## 16. Observability signals

**A pattern in code review comment history, if the repository's review
tooling can be queried, is a leading indicator.** Repeated review comments of
the shape "this logic should live on X" or "why does Y need to reach into
three fields of X" clustered around the same class over time indicate the
class has settled into the Data Class role and its callers are compensating.

**A static-analysis signal, where the tooling exists, follows directly.** A low
ratio of non-accessor public methods to fields on a class, tracked as a
code-quality metric, is a direct, computable proxy for this smell. Several
commercial and open-source static analyzers, for example tools implementing the
"Lack of Cohesion of Methods" family of object-oriented metrics, flag exactly
this shape, though the metric alone cannot distinguish a smelly Data Class from
a legitimate DTO or Value Object, so any automated flag needs dimension 4's
distinguishing test applied by a human before it is acted on.

**A runtime signal is unusual for this smell**, because the smell is a design
defect rather than a behavioral defect and by itself produces no incorrect
output, no exception, and no measurable latency difference. A Data Class that
is read and written correctly by its callers behaves identically, from the
outside, to a rich domain object that enforces the same rules internally. The
absence of a runtime signal is itself worth stating plainly, because it is
part of why this smell can persist for years in a working system with no
production incident ever pointing at it directly, and why its cost shows up
instead in the maintenance metrics, the time-to-fix for a bug in the duplicated
logic, and the size of the diff required to make a change that conceptually
touches only one class's meaning.

## 17. Security and privacy implications

**Unvalidated construction as an input-validation gap.** A Data Class with no
constructor or setter validation will happily hold a value received from an
external source, a deserialized API request body, a form submission, a
database row from an untrusted migration, without checking that the value is
within any sensible range or format, because validation was never given a
home on the class. This does not make the smell itself a vulnerability, but it
removes one of the natural places validation would otherwise live, which
shifts the burden onto every caller to validate independently and increases
the chance that at least one caller forgets to.

**Field-level exposure through unrestricted accessors.** A Data Class exposing
a setter for every field, including fields that represent sensitive state, an
account balance, a permission flag, an authentication token, offers no
protection against a caller mutating that field outside the intended workflow,
because the class has delegated all such decisions to whichever code happens
to call the setter. A rich domain object can restrict a sensitive field to
being set only through a specific method that also enforces the relevant
authorization check or business rule. A pure Data Class structurally cannot,
since every field is equally, uniformly writable.

**Serialization of internal-only fields.** Where a Data Class doubles as both
the in-process domain object and the object handed directly to a serializer,
a conflation flagged in dimension 4 and dimension 10, any field added to the
class for internal bookkeeping is, by default, also exposed in whatever the
serializer produces, unless the developer remembers to annotate or exclude it
explicitly on every occasion. Keeping a genuine DTO separate from the domain
object, as dimension 4 recommends, gives the serialization boundary an
explicit, reviewable list of exactly what crosses it, rather than an implicit
list that is whatever the domain object happens to contain at the time.

## 18. References

1. Martin Fowler, Kent Beck, John Brant, William Opdyke, Don Roberts,
   *Refactoring. Improving the Design of Existing Code*, Addison-Wesley, 1999,
   chapter 3, "Bad Smells in Code," the "Data Class" entry.
2. Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
   edition, Addison-Wesley, 2018, the "Data Class" smell in the smells
   catalog, cross-referenced with the Encapsulate Field, Encapsulate
   Collection, and Move Method refactorings.
3. Martin Fowler, ["AnemicDomainModel"](https://martinfowler.com/bliki/AnemicDomainModel.html),
   martinfowler.com bliki entry, 2003, verified 2026-08-02.
4. Martin Fowler, ["Data Transfer
   Object"](https://martinfowler.com/eaaCatalog/dataTransferObject.html),
   Patterns of Enterprise Application Architecture catalog page,
   martinfowler.com, verified 2026-08-02.
5. Martin Fowler, ["ValueObject"](https://martinfowler.com/bliki/ValueObject.html),
   martinfowler.com bliki entry, verified 2026-08-02.
6. Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
   Software*, Addison-Wesley, 2003, chapter 5, "A Model Expressed in
   Software," the Value Object building block.
7. Joshua Bloch, *Effective Java*, 3rd edition, Addison-Wesley, 2018, Item 16,
   "In public classes, use accessor methods, not public fields."
8. Oracle, ["Records," Java SE 17
   documentation](https://docs.oracle.com/en/java/javase/17/language/records.html),
   verified 2026-08-02.
9. Project Lombok, ["@Data" feature
   page](https://projectlombok.org/features/Data), verified 2026-08-02.
10. [refactoring.guru, "Data Class"](https://refactoring.guru/smells/data-class),
    used only to cross-verify the shape of Fowler's definition against a
    secondary paraphrase, not as prose source for this entry, verified
    2026-08-02.

## Code examples

### TypeScript

The smell, then the fix, showing behavior moving onto the class.

```typescript
// Smell. Customer is a pure data holder.
class CustomerSmelly {
  constructor(
    public loyaltyYears: number,
    public totalSpend: number,
  ) {}
}

function isEligibleForVip(c: CustomerSmelly): boolean {
  return c.loyaltyYears >= 3 && c.totalSpend >= 1000;
}

// Fix. The rule lives with the data.
class Customer {
  constructor(
    private readonly loyaltyYears: number,
    private readonly totalSpend: number,
  ) {
    if (loyaltyYears < 0 || totalSpend < 0) {
      throw new Error("negative values are not valid for a customer");
    }
  }

  isEligibleForVip(): boolean {
    return this.loyaltyYears >= 3 && this.totalSpend >= 1000;
  }
}

const smellyCustomer = new CustomerSmelly(4, 1200);
console.log("smelly result", isEligibleForVip(smellyCustomer));

const customer = new Customer(4, 1200);
console.log("fixed result", customer.isEligibleForVip());
```

### Python

```python
from dataclasses import dataclass


# Smell. Only fields, the rule lives elsewhere.
@dataclass
class CustomerSmelly:
    loyalty_years: int
    total_spend: float


def is_eligible_for_vip(customer: CustomerSmelly) -> bool:
    return customer.loyalty_years >= 3 and customer.total_spend >= 1000


# Fix. The rule moves onto the class that owns the data.
class Customer:
    def __init__(self, loyalty_years: int, total_spend: float) -> None:
        if loyalty_years < 0 or total_spend < 0:
            raise ValueError("negative values are not valid for a customer")
        self._loyalty_years = loyalty_years
        self._total_spend = total_spend

    def is_eligible_for_vip(self) -> bool:
        return self._loyalty_years >= 3 and self._total_spend >= 1000


if __name__ == "__main__":
    smelly = CustomerSmelly(loyalty_years=4, total_spend=1200.0)
    print("smelly result", is_eligible_for_vip(smelly))

    customer = Customer(loyalty_years=4, total_spend=1200.0)
    print("fixed result", customer.is_eligible_for_vip())
```

### Go

Go has no classes, so the smell here is a struct with only exported fields and
free functions in place of methods, contrasted with the same struct given
methods of its own.

```go
package main

import "fmt"

// Smell. CustomerSmelly is a pure data holder, logic lives in a free function.
type CustomerSmelly struct {
	LoyaltyYears int
	TotalSpend   float64
}

func isEligibleForVIP(c CustomerSmelly) bool {
	return c.LoyaltyYears >= 3 && c.TotalSpend >= 1000
}

// Fix. Customer owns its own rule as a method.
type Customer struct {
	loyaltyYears int
	totalSpend   float64
}

func NewCustomer(loyaltyYears int, totalSpend float64) (*Customer, error) {
	if loyaltyYears < 0 || totalSpend < 0 {
		return nil, fmt.Errorf("negative values are not valid for a customer")
	}
	return &Customer{loyaltyYears: loyaltyYears, totalSpend: totalSpend}, nil
}

func (c *Customer) IsEligibleForVIP() bool {
	return c.loyaltyYears >= 3 && c.totalSpend >= 1000
}

func main() {
	smelly := CustomerSmelly{LoyaltyYears: 4, TotalSpend: 1200}
	fmt.Println("smelly result", isEligibleForVIP(smelly))

	customer, err := NewCustomer(4, 1200)
	if err != nil {
		panic(err)
	}
	fmt.Println("fixed result", customer.IsEligibleForVIP())
}
```

Java, Rust, and Swift are omitted from the runnable set for this entry, in
keeping with dimension 8's point that a language's native lightweight record
feature (Java record, Rust plain struct with no impl block, Swift
struct) is exactly where the smell's legitimate and illegitimate line is drawn
most sharply, and the three languages above (TypeScript, Python, Go) already
demonstrate the smell and its fix across a class-based OO language, a
dynamically-typed OO language, and a language with no classes at all.

## Verification of code examples

- TypeScript, compiled and run with npx tsc and node. Confirmed it prints
  "smelly result true" and "fixed result true".
- Python, run with python3. Confirmed it prints
  "smelly result True" and "fixed result True".
- Go, run with go run. Confirmed it prints
  "smelly result true" and "fixed result true".
