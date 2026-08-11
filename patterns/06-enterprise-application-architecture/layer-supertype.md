---
name: Layer Supertype
slug: layer-supertype
family: 06-enterprise-application-architecture
category: Base Pattern
aliases: [Base Class Pattern, Common Base, Abstract Layer Root]
first_described: "Fowler 2002"
maturity: canonical
related: [template-method, mapper, unit-of-work, identity-field, repository, active-record]
incompatible_with: []
verified: 2026-08-02
---

# Layer Supertype

## 1. Name, aliases, and lineage

The canonical name is Layer Supertype. It is catalogued as one of the eleven
Base Patterns in Martin Fowler, *Patterns of Enterprise Application
Architecture*, Addison-Wesley, 2002, chapter 18, "Base Patterns". The book's
one-line intent statement is "a type that acts as the supertype for all types
in its layer" ([Fowler, Layer Supertype, martinfowler.com](https://martinfowler.com/eaaCatalog/layerSupertype.html),
verified 2026-08-02). The chapter groups Layer Supertype with the other Base
Patterns, Gateway, Service Stub, Record Set, Mapper, Separated Interface,
Registry, Value Object, Money, Special Case, and Plugin
([Fowler, full catalog, martinfowler.com](https://martinfowler.com/eaaCatalog/),
verified 2026-08-02). Base Patterns are the small, reused building blocks that
the book's larger domain logic, data source, and web presentation patterns are
built from, rather than end to end architectures on their own.

The pattern has no single formal name outside Fowler's book. Practitioners
commonly call the same idea a Base Class Pattern, a Common Base, or, when it is
implemented as an interface rather than a class, an Abstract Layer Root. None
of these alternate names appears in a citable catalog the way Layer Supertype
does, so they are recorded here as the vocabulary a reader is likely to search
for, not as competing formal names.

Layer Supertype predates its 2002 name by decades as a plain engineering habit.
Object-oriented languages that ship a universal root class, Smalltalk's
`Object`, Objective-C's `NSObject`, and Java's `java.lang.Object` before
generics, already gave every object in the entire program one shared ancestor.
Fowler's contribution was narrower and more useful for architecture, naming
the deliberate practice of introducing a second, application-owned supertype
one level below the language's universal root, scoped to a single
architectural layer, carrying only the behavior that layer's members actually
share. That narrower scope is what turns a language feature into an
architectural pattern with its own forces and failure modes, which is why
this entry treats "the language gives you `Object` for free" and "you
deliberately wrote `DomainObject` for your domain layer" as two different
things, only the second of which is Layer Supertype in Fowler's sense.

## 2. Problem and context

An enterprise application is organized into layers, most often domain logic,
data source access, and presentation, and each layer accumulates many sibling
types over the life of the project. A domain layer ends up with dozens of
entity classes, `Order`, `Customer`, `Invoice`, `Shipment`. A data source layer
ends up with one mapper or repository class per entity. A presentation layer
ends up with one controller per resource or one page handler per screen.

Left unattended, these sibling types drift into duplicating the same small set
of behaviors independently. Every domain entity reinvents identity comparison
based on a primary key. Every mapper reinvents the connect, execute, translate
error, and log sequence around a database call. Every controller reinvents how
to turn a service exception into an HTTP status code and a JSON error body.
Each individual duplication looks small, five or ten lines, so no single
instance of it looks worth refactoring. The cost shows up later, when a team
needs to change that shared behavior everywhere at once, add a new audit field
to every entity, tighten the error format returned by every controller, add a
retry policy to every mapper, and discovers the same five or ten lines copied
across thirty files with small accidental variations that have crept in over
time because nothing forced them to stay identical.

The context in which this problem is worth solving has a specific shape. There
must genuinely be many sibling types occupying the same architectural layer,
not two or three. Those siblings must share real, identical behavior, not
behavior that merely looks similar today but is actually independent. And the
project must expect to keep adding layer wide behavior over its life, an
audit trail, a soft delete flag, a standard error envelope, because a
supertype that will never be touched again after it is written earns back very
little of its own cost.

## 3. Forces

Layer Supertype sits at the intersection of five competing pressures, and it
resolves them in one direction consistently, which is exactly why it is not
always the right choice.

**Duplication versus coupling.** Every duplicated line of identical behavior
across N sibling types is a place a future edit can be applied inconsistently.
Collapsing that duplication into one shared supertype removes the
inconsistency risk but creates a single point every sibling now depends on.
The pattern trades a distributed risk, many small independent copies that can
each go stale on their own, for a concentrated risk, one shared class whose
mistakes propagate to everyone at once.

**Discoverability versus flexibility.** A developer who needs to find how
identity comparison works for a domain object has exactly one place to look
when a Layer Supertype exists. That same developer loses the ability to give
one particular sibling type a genuinely different identity comparison without
either overriding the supertype's method, which reintroduces the duplication
the pattern was meant to remove, or leaving that one sibling out of the
hierarchy entirely, which fragments the layer.

**DRY versus the fragile base class problem.** Removing duplication is the
entire justification for the pattern, but a shared base class that many
unrelated subclasses depend on is the textbook setup for the fragile base
class problem. A change made to satisfy one subclass's need can silently
break a sibling subclass that depends on the same inherited behavior in a way
the person making the change did not anticipate, because the two subclasses
are not developed by the same person or team.

**Single inheritance versus is a layer member.** In languages with single class
inheritance, Java, C#, Swift classes, PHP classes, spending the one available
inheritance slot on belonging to this architectural layer means that slot is
not available for a genuine is a relationship the type also needs, extending a
framework exception class, extending a platform view class. This is the force
that most often decides whether the implementation variant is a class or an
interface, see dimension 8.

**Testability versus test double cost.** A concrete type's own unit test
benefits from the supertype's shared behavior being tested once, in the
supertype's own test suite, rather than re-verified in every sibling. The
counter pressure is on the caller's tests. Any code that consumes a value of
the supertype's type now has a wider contract to satisfy when it builds a test
double for that value, even when the test only cares about one narrow slice of
that contract.

The pattern is worth adopting exactly when the first pressure in each pair,
duplication, discoverability, DRY, and the shared identity of belonging to one
layer, outweighs the second. It is worth rejecting when the second pressure in
a pair, flexibility, an is a relationship elsewhere, or test double cost,
turns out to matter more for a specific layer than the project's authors
assumed going in.

## 4. Applicability and non-applicability

Reach for Layer Supertype when all of the following hold.

- A layer already has, or is clearly going to grow, many sibling types, not
  two or three, that occupy the same conceptual role, every domain entity,
  every data mapper, every controller.
- Those siblings share real behavior today, not behavior that coincidentally
  looks alike, identity by primary key, a validation error collection, a
  common query template, a standard response envelope.
- The project expects to keep adding layer wide behavior over its lifetime, an
  audit column, a soft delete flag, a standard logging line, a cross cutting
  authorization check, so that a single place to add it repeatedly pays for
  itself.
- The implementation language offers either single inheritance the layer is
  not already using for something more specific, or an interface and default
  method mechanism, described fully in dimension 8, that avoids spending that
  slot at all.
- A framework the layer already depends on, an ORM, a web framework, has not
  already claimed the single inheritance slot with its own required base
  class, or, if it has, the project is comfortable extending the framework's
  base class with one further application specific supertype in between.

Do not reach for Layer Supertype when any of the following hold. This list is
deliberately the longer and more specific half of this dimension, because it
is the half most catalogs skip and the half that actually prevents the
pattern's known failure modes.

- The layer's members do not actually share behavior beyond an empty marker.
  A supertype with no real shared method or field, introduced purely so every
  type has a common ancestor, buys coupling and gives back nothing. Prefer no
  supertype at all, or a marker interface if the language needs one for
  generic constraints.
- The shared concerns are orthogonal rather than universal. Every entity
  needing an id is universal across a domain layer. Some entities needing
  auditing, some needing soft delete, some needing versioning, with the sets
  overlapping differently for different entities, is orthogonal, and cramming
  all three into one supertype produces exactly the kind of accreted, mostly
  unused surface described in dimension 11 as the God Base Class failure
  mode. Composable traits or mixins, or several small interfaces, fit
  orthogonal concerns better than one shared base.
- A concrete type in the layer already needs to extend something else for a
  genuine is a relationship, a platform framework class, a checked exception
  hierarchy, and the language only allows one parent class. Forcing the Layer
  Supertype relationship here either breaks that other relationship or forces
  the supertype itself to become an interface, which is a legitimate variant,
  see dimension 8, but is a different decision than the one being described
  as not applicable here.
- The layer is genuinely small and will very likely stay small, three or
  fewer sibling types with no plan to add more. The break even point where a
  shared base pays back its own coupling cost is not reached, and a small
  private helper function or two shared free functions do the same job with
  none of the inheritance coupling.
- Tests already show that mocking or stubbing a concrete type in this layer is
  expensive because callers hold the concrete type through the supertype's
  interface and therefore need to satisfy the whole supertype contract in a
  test double even when they only touch one method. When that cost is already
  visible and painful, prefer the interface with default methods variant, or
  composition, over widening an existing concrete class hierarchy further.
- The framework already provides the required base class for this exact layer,
  an ORM's entity base, a web framework's controller base, and the team is
  tempted to insert an additional in house supertype purely to centralize a
  handful of methods that could equally live as free functions or as an
  injected collaborator. A three level hierarchy, framework base, then house
  supertype, then concrete type, is sometimes the right call, see dimension 8,
  but it should be a deliberate choice made because the house supertype adds
  real behavior, not a reflex.

## 5. Structure

| Participant | Responsibility |
|---|---|
| Layer Supertype | The shared type that every member of one architectural layer extends or implements. Declares and, in the class variant, implements the state and behavior every layer member is expected to have, an identity comparison, a validation error list, a common query template, a standard response helper. |
| Concrete Layer Member | One of the many sibling types in the layer, `Order`, `OrderMapper`, `OrdersController`. Extends the Layer Supertype and adds the state and behavior specific to itself. Usually implements a small number of abstract or protocol required members that let the supertype's shared logic do its work polymorphically. |
| Layer Aware Client | Code outside the layer, or infrastructure code inside the layer, that operates on many concrete members through the shared supertype's interface rather than through each concrete type individually. A Unit of Work registering domain objects for dirty checking, a mapper registry dispatching by concrete class but invoking through the Mapper supertype, a routing table dispatching an HTTP request to whichever controller matches, all treat their targets uniformly through the supertype. |
| Framework Base, optional | A supertype imposed by an external library or framework that the layer's members were already required to extend before the project introduced its own Layer Supertype, `ActiveRecord::Base`, `NSManagedObject`, `Microsoft.AspNetCore.Mvc.Controller`. When present, the project's own Layer Supertype sits between the framework base and the concrete types, adding application specific shared behavior on top of what the framework already supplies. |

The relationship between a Layer Supertype and its concrete members is
structural inheritance or interface conformance, drawn as a solid line with a
hollow triangle in UML. The relationship between a Layer Aware Client and the
supertype is usage through the supertype's public contract, a dashed line with
an open arrowhead in UML, deliberately never a dependency on any one concrete
subtype.

## 6. ASCII structure diagram

```text
                       +---------------------------+
                       |      Framework Base        |
                       |  (optional, e.g. ORM base) |
                       +---------------------------+
                                     ^
                                     |
                       +---------------------------+
                       |       Layer Supertype      |
                       |  (e.g. DomainObject)       |
                       |---------------------------|
                       | # id                       |
                       | # errors: List<Error>      |
                       |---------------------------|
                       | + getId()                  |
                       | + equals(other)            |
                       | + addError(msg)            |
                       | + isValid()                |
                       | + validate()  [abstract]   |
                       +---------------------------+
                          ^              ^              ^
                          |              |              |
              +-----------+   +-----------+   +-----------+
              |   Order    |   |  Customer  |   |  Invoice   |
              |------------|   |------------|   |------------|
              | lineItems  |   | email      |   | dueDate    |
              |------------|   |------------|   |------------|
              | validate() |   | validate() |   | validate() |
              +-----------+   +-----------+   +-----------+
                    ^               ^               ^
                    |               |               |
                    +---------------+---------------+
                                    |
                        +-------------------------+
                        |    Layer Aware Client    |
                        |  (Unit of Work / caller) |
                        |-------------------------|
                        | registerDirty(DomainObj) |
                        | commit()                 |
                        +-------------------------+
```

## 7. Dynamics

The interaction that Layer Supertype exists to support is a client acting on a
heterogeneous set of concrete types through one shared contract, without
knowing or caring which concrete type it holds at each step. A Unit of Work
committing a batch of changed domain objects shows the whole flow end to end.

```text
Client            UnitOfWork          DomainObject          Order        Customer
  |                    |                    |                 |             |
  | register(order) -->|                    |                 |             |
  |                    | store ref (as      |                 |             |
  |                    | DomainObject)      |                 |             |
  |                    |------------------->|                 |             |
  |                    |                    |                 |             |
  | register(customer)>|                    |                 |             |
  |                    | store ref (as      |                 |             |
  |                    | DomainObject)      |                 |             |
  |                    |------------------->|                 |             |
  |                    |                    |                 |             |
  | commit() -------->|                    |                 |             |
  |                    | for each dirty obj |                 |             |
  |                    |   obj.validate() ->|-- dispatches to concrete ----->|
  |                    |                    |    Order.validate()           |
  |                    |                    |<--------------------------------
  |                    |   obj.validate() ->|-- dispatches to concrete ----->|
  |                    |                    |    Customer.validate()
  |                    |                    |<--------------------------------
  |                    |   if obj.isValid()  |                 |             |
  |                    |     mapper.save(obj)                  |             |
  |                    |   else               |                 |             |
  |                    |     collect obj.getErrors()            |             |
  |                    |                    |                 |             |
  |<-- commit result --|                    |                 |             |
  |    (saved N, N     |                    |                 |             |
  |     validation     |                    |                 |             |
  |     failures)      |                    |                 |             |
```

The key observation the diagram makes visible is that `UnitOfWork` never
imports `Order` or `Customer` at all. It only ever holds and calls through
`DomainObject`. `validate()` is declared abstract on the supertype and given a
real body by each concrete type, so the call dispatches polymorphically to
whichever validation logic is correct for the actual runtime type, while
`isValid()`, `getErrors()`, and the identity used to key any already
processed object set all come from the shared supertype code, run exactly
once regardless of how many concrete types exist. Adding a fourth sibling
type, `Invoice`, requires zero changes to `UnitOfWork`.

## 8. Implementation variants

**Abstract class with concrete shared state.** The classic form. The
supertype is an abstract class holding the shared fields directly, `id`, an
`errors` list, and shared concrete methods, `equals`, `getErrors`, alongside
one or more abstract methods each concrete subtype must implement,
`validate()`. This is the shape shown in the TypeScript and Python samples
below. It costs the language's single inheritance slot.

**Abstract class as a Template Method host.** The same abstract class shape,
but the supertype's concrete methods define a fixed algorithm skeleton that
calls out to a handful of small abstract steps, `find`, `save`, and their
private helpers `_select`, `_insert`, `_update` in the Python Mapper sample
below. This is Layer Supertype composed with Template Method, a very common
pairing in data source layers, where every mapper needs the identical connect,
log, translate error sequence around a different concrete SQL statement.

**Interface, protocol, or trait with default implementations.** Rather than a
class, the supertype is declared as an interface, and the shared behavior is
supplied as default method bodies the language attaches to the interface
itself. Java interface default methods, available since Java 8
([Oracle, Default Methods, The Java Tutorials](https://docs.oracle.com/javase/tutorial/java/IandI/defaultmethods.html),
verified 2026-08-02), Kotlin interface method bodies, and Swift protocol
extensions, where an `extension` block on a protocol supplies a default
implementation any conforming type picks up for free unless it overrides it
(Apple, *The Swift Programming Language*, Protocols chapter,
[docs.swift.org](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/protocols/),
verified 2026-08-02), are all the same idea in three languages. This variant
is shown in the Swift sample below. It does not spend the language's single
inheritance slot, so a concrete type can still extend a different class for a
genuine is a relationship while also conforming to the Layer Supertype
protocol.

**Composition or delegation in languages without class inheritance.** Go has
no classical subclassing at all, and instead lets a struct embed another
struct or interface, promoting the embedded type's methods onto the outer
type automatically
([The Go Authors, Effective Go, Embedding section](https://go.dev/doc/effective_go#embedding),
verified 2026-08-02). Every concrete controller struct embeds a
`BaseController` struct by value or pointer, and the base's methods, `OK`,
`NotFound`, `BadRequest`, become directly callable on the outer type with zero
forwarding boilerplate, while the receiver Go actually invokes those methods
with is the embedded inner value, not the outer one, an important distinction
from true polymorphic dispatch that dimension 11 revisits. Rust has an
analogous idiom using a trait with default method bodies plus a blanket
implementation, or explicit composition with a field and manually written
forwarding methods where a trait's defaults are not expressive enough.

**Generic or parameterized supertype.** The supertype is written with a type
parameter for the identifier type, `AbstractEntity<ID>` in Java or C#, or
`abstract class Entity<TId>` in TypeScript, so that an `Order` keyed by a
`UUID` and a `LegacyInvoice` keyed by a legacy integer key can both extend the
same supertype without either one widening or narrowing its actual identifier
type.

**Framework base plus one house layer supertype.** When an ORM or web
framework already imposes its own required base class on every member of a
layer, an application's own Rails models conventionally extend an
intermediate `ApplicationRecord` that itself extends `ActiveRecord::Base`
([Rails Guides, Active Record Basics](https://guides.rubyonrails.org/active_record_basics.html),
verified 2026-08-02). The project inserts its own Layer Supertype between the
framework's base and its concrete types, adding house specific shared
behavior, a standard audit column set, a house wide validation convention,
without touching or reimplementing anything the framework's base class
already provides.

## 9. Known production uses

**Ruby on Rails, `ActiveRecord::Base` and `ApplicationRecord`.** Every model
class in a Rails application is generated to inherit from `ApplicationRecord`,
which itself inherits from `ActiveRecord::Base`. Rails' own guide states
plainly that `ApplicationRecord` inherits from `ActiveRecord::Base` and it is
what turns a regular Ruby class into an Active Record model
([Rails Guides, Active Record Basics](https://guides.rubyonrails.org/active_record_basics.html),
verified 2026-08-02). The inherited surface, validations run automatically on
`save`, association declarations, the query interface, `find`, `where`,
`order`, and lifecycle callbacks such as `after_create`, is precisely the
shared, cross cutting behavior a Layer Supertype exists to centralize for a
domain and data access layer combined, and the two level hierarchy,
`ActiveRecord::Base` supplied by the framework, `ApplicationRecord` supplied
by the application, matches the framework base plus house supertype variant
described in dimension 8.

**Django, `django.db.models.Model`.** Django's own documentation states that
each model is a Python class that subclasses `django.db.models.Model`, and
that this base class is what gives every model an automatically generated
database access API, an automatic primary key unless one is declared
explicitly, and a fixed set of instance methods including `save()`,
`delete()`, and `__str__()`
([Django docs, Models topic guide](https://docs.djangoproject.com/en/5.0/topics/db/models/),
verified 2026-08-02). Every Django model in every Django project, across every
Django codebase in active use, shares this one supertype for its domain and
persistence layer.

**ASP.NET Core MVC, the `Controller` base class.** Microsoft's own
documentation states that, by convention, controller classes inherit from
`Microsoft.AspNetCore.Mvc.Controller`, and that deriving from `Controller`
provides access to three categories of helper methods, methods that produce
an empty response body such as `NotFound()` and `Ok()`, methods that produce a
response body with a fixed content type such as `View()`, and methods that
perform content negotiation such as `Ok(value)` and `BadRequest(modelState)`
([Microsoft Learn, Handle requests with controllers in ASP.NET Core MVC](https://learn.microsoft.com/en-us/aspnet/core/mvc/controllers/actions?view=aspnetcore-8.0),
verified 2026-08-02). This is a presentation layer Layer Supertype, shared
across every controller class in every ASP.NET Core MVC application, and it
is the direct model the Go sample in this entry reproduces using struct
embedding instead of class inheritance.

**Hibernate ORM, `@MappedSuperclass`.** Hibernate's user guide documents
`@MappedSuperclass` as a way to establish a base class containing shared
persistent attributes that multiple entity classes can inherit from, commonly
used to centralize identifier fields, optimistic locking version fields, and
audit timestamp fields across every entity in an application, without the
mapped superclass itself becoming a persisted, queryable entity
([Hibernate ORM 6.4 User Guide, section 3.14.1, Inheritance](https://docs.hibernate.org/orm/6.4/userguide/html_single/Hibernate_User_Guide.html),
verified 2026-08-02). This is the object relational mapping industry's own
name for exactly the Layer Supertype relationship applied to a domain entity
layer, formalized as its own annotation because the pattern recurs across
essentially every JPA based Java application.

## 10. Consequences

**Positive.**

- Cross cutting behavior for an entire layer, identity, validation error
  handling, a common query template, a standard response envelope, is
  implemented and tested in exactly one place, then inherited everywhere
  instead of copied.
- A future change to that shared behavior, adding an audit field, tightening a
  validation rule, changing an error response shape, is made once and takes
  effect across every concrete type in the layer simultaneously, with no risk
  of an individual sibling being missed during a manual sweep.
- Layer Aware Clients, a Unit of Work, a request dispatcher, a mapper
  registry, can be written once against the supertype's contract and continue
  working unmodified as new concrete types are added to the layer.
- New team members have exactly one place to look to learn what every domain
  object, every mapper, or every controller in this codebase provides by
  default, which shortens the time it takes to become productive in an
  unfamiliar layer.

**Negative.**

- Every concrete type in the layer is coupled to the supertype, so a poorly
  reasoned change to the supertype, adding a method that makes sense for one
  subtype but not others, can silently affect or break every sibling at once.
  This is the fragile base class problem in its most concentrated form,
  discussed in depth in dimension 11.
- In a single inheritance language, the Layer Supertype relationship consumes
  the one available parent class slot for every concrete type in the layer,
  foreclosing any genuine is a relationship a specific concrete type might
  otherwise need.
- The supertype tends to accumulate members over a project's life because it
  is the path of least resistance for anything that seems generally useful,
  which, left unchecked, produces a wide, low cohesion base class that most
  individual subtypes only use a fraction of.
- Test doubles for a concrete type must satisfy the full inherited surface of
  the supertype, not only the members the test in question actually exercises,
  which raises the cost of writing a narrow, purpose built fake compared to
  mocking a smaller, more focused type.

## 11. Failure modes and misuse

| Symptom | Cause | Fix |
|---|---|---|
| An unrelated concrete type starts failing its tests immediately after a team adds a new field or method to the shared supertype for its own, different purpose. | The fragile base class problem. The supertype accreted a member intended for one subtype's need, and that member's presence, default value, or side effect interacts badly with an unrelated sibling that never asked for it. | Move the member down to the one or two concrete types that actually need it, per Refactoring's Push Down Method or Push Down Field, or extract it into a small, separately named trait or interface that only the concrete types that need it opt into. |
| Autocomplete on any object in the layer shows dozens of inherited members, and most concrete types visibly use only a handful of them. New team members cannot tell which inherited methods are actually load bearing for the type in front of them. | The God Base Class or Blob inheritance failure mode. Over time, every utility that seemed reusable got bolted onto the one shared class available, because that was the path of least resistance rather than a deliberate decision. | Split the supertype along real cohesion lines into several smaller interfaces or traits, following the interface segregation principle, and keep the class supertype itself down to the small set of members that are genuinely universal across the entire layer. |
| A bug in one concrete type is traced back to a protected, mutable field declared on the supertype that a sibling concrete type also writes to, in an order neither type's author anticipated. | Shared mutable protected state on the supertype invites subclasses to reach into that state directly rather than through an accessor that preserves the supertype's invariants, and two subtypes mutating it in different orders violates an invariant neither author saw the other side of. | Make the supertype's state private, expose it only through methods that enforce the supertype's own invariants, and document those invariants explicitly in the supertype's own documentation, not only in each subtype's comments. |
| A subclass constructor throws a null reference or undefined property error the very first time it runs, and the stack trace shows the failure happening inside a method the supertype's constructor called. | The supertype's constructor calls an overridable method, and that method's overridden implementation in the subclass reads a field the subclass's own constructor has not initialized yet, because the language runs the base class constructor to completion before the derived class's field initializers run. | Never call an overridable or virtual method from the supertype's own constructor. Prefer a separate, explicit initialization or factory step that runs after both the base and derived constructors have completed. |
| A new concrete type is blocked from being added to the layer because it genuinely needs to extend a different existing class, a platform framework class, a checked exception hierarchy, and the language allows only one parent class, which the Layer Supertype already occupies. | Over reliance on class inheritance to express belonging to this layer rather than a genuine is a relationship, in a language where inheritance is a scarce, single use resource. | Convert the Layer Supertype to an interface, protocol, or trait with default method implementations where the language supports it, per the interface variant in dimension 8, so conformance no longer competes with a genuine class inheritance need. |
| Code in an unrelated architectural layer, the presentation layer, imports and depends on a domain layer's Layer Supertype purely because it already has an id and an equals method. | No clearly enforced ownership boundary around the supertype, so it becomes an accidental cross layer utility grab bag simply because it happens to be convenient and already exists. | Keep exactly one Layer Supertype per layer, enforce module or package visibility boundaries so a supertype from one layer cannot be imported from another, and if genuinely shared behavior is needed across layers, extract a smaller, explicitly cross layer utility for that specific behavior instead of reusing a layer scoped supertype. |
| In Go, code that expected calling a shared helper method to see the outer, concrete struct's overridden state instead silently operates on the embedded inner struct's own copy of that state, producing results that look like the override was ignored. | Go's struct embedding promotes methods syntactically, so the outer type can call the embedded type's methods directly, but the receiver of a promoted method is still the embedded inner value, not the outer struct, which is a form of composition, not true dynamic dispatch, and does not behave like a virtual method call in a classically inheriting language. | Do not model Layer Supertype in Go as if embedding gave true polymorphic override behavior. Where an overridable hook is genuinely needed, declare it as a Go interface method the outer type implements explicitly, and have the embedded base call back into that interface, the manual template method via an interface field idiom, rather than relying on embedding alone. |

## 12. Trade-off matrix

The matrix below compares Layer Supertype against three named alternatives
that solve the same underlying problem, shared cross cutting behavior across a
set of related types, by a different mechanism, all drawn from the
established literature. Template Method and Decorator come from Erich Gamma,
Richard Helm, Ralph Johnson, and John Vlissides, *Design Patterns*,
Addison-Wesley, 1994, the GoF catalog, and Strategy, also from the same
catalog, is used here as the delegation based alternative to inheritance.

| Force | Layer Supertype | Template Method alone | Decorator | Strategy (delegation) |
|---|---|---|---|---|
| Removes duplication across many sibling types at once | Yes, the primary strength. State and behavior live in one place for the whole layer. | Partially. Removes duplication of one algorithm's skeleton, but each pattern instance is usually applied to a single class hierarchy rather than an entire layer's identity, error handling, and query surface together. | No. Decorator adds behavior to one wrapped instance at a time, it does not centralize behavior for a whole layer of sibling types. | Partially. Centralizes one behavior, the strategy's algorithm, but each cross cutting concern needs its own separately injected strategy, so N concerns need N strategy fields rather than one shared base. |
| Coupling introduced | High. Every concrete type in the layer is coupled to one shared class or interface for its entire lifetime. | High, but scoped to the one hierarchy the template method lives in, not necessarily the whole layer. | Low. A decorated object is coupled only to the interface it decorates, and decorators can be stacked or omitted per instance. | Low. A type holds a reference to a strategy interface, and different instances of the same type can hold different strategy implementations. |
| Runtime flexibility per instance | Low. Every instance of a concrete type gets the exact same inherited behavior, there is no per instance opt out short of overriding a method. | Low, for the same reason as Layer Supertype. Inheritance is fixed at compile time. | High. Which decorators wrap a given object can be decided per instance, at runtime. | High. Which strategy a given instance uses can be swapped at runtime, even after construction. |
| Single inheritance slot cost (in a single inheritance language) | Spends it, unless implemented as an interface with default methods. | Spends it, same constraint. | Does not spend it. Decorator is composition based by definition. | Does not spend it. Strategy is composition based by definition. |
| Best fit | A whole architectural layer with many siblings sharing genuinely universal behavior over the project's life. | One algorithm skeleton shared by a small, closely related family of types. | Adding or removing optional behavior on individual objects at runtime, independent of any layer wide concern. | A single cross cutting concern that needs to vary per instance or be swapped at runtime, decoupled from the type hierarchy entirely. |

## 13. Related and incompatible patterns

**Template Method (GoF).** Layer Supertype and Template Method compose
naturally and very frequently in practice, shown directly in the Python Mapper
sample in this entry. Template Method supplies the algorithm skeleton, `find`
and `save` calling out to `_select`, `_insert`, `_update`, and Layer Supertype
is simply the architectural placement decision of putting that template
method on the one shared base every data source object in the layer extends,
rather than on a narrower, single purpose hierarchy.

**Mapper (Fowler Base Pattern).** In the data source layer specifically, the
Layer Supertype is very often a shared `Mapper` base class, precisely the
Data Mapper pattern's family of per entity mapper classes, giving every mapper
the same connect, execute, and error translation sequence.

**Unit of Work (Fowler, Data Source Architectural Patterns).** A Unit of Work
implementation is the canonical Layer Aware Client from dimension 5. It needs
to register, track, and commit an arbitrary, growing set of domain objects
without depending on each concrete domain type by name, which is only
possible because every domain object shares one supertype it can hold
references to and dispatch through.

**Identity Field (Fowler, Object Relational Structural Patterns).** The
identifier field and the identity based `equals` and hash implementation most
domain objects need are extremely common candidates for exactly the shared
state and behavior a domain layer's Layer Supertype centralizes, shown in the
TypeScript sample's `id`, `equals`, and identity semantics.

**Repository (Fowler, Object Relational Metadata Mapping Patterns).** Where a
project has one repository interface per aggregate root, a shared generic
base repository interface, `Repository<T, ID>`, parameterized over the entity
type and identifier type, is the interface flavored variant of Layer
Supertype applied to the repository layer specifically.

**Active Record (Fowler, Data Source Architectural Patterns).** Active Record
combines domain logic and persistence in one object, and frameworks that
implement it, Rails' `ActiveRecord::Base`, Django's `models.Model`, expose
their combined domain and persistence behavior through exactly a Layer
Supertype, making Active Record and Layer Supertype closely paired in
practice even though they answer different questions. Active Record is about
where domain logic and persistence logic live relative to each other, Layer
Supertype is about how shared behavior across many sibling types in one layer
is organized.

Layer Supertype has no formally incompatible pattern in the sense of two
patterns that cannot coexist in the same codebase. Its natural tension is with
patterns that deliberately favor per instance composition over shared
inheritance, Decorator and Strategy from dimension 12, which is a design trade
off between the two approaches rather than a technical incompatibility. A
codebase can and often does use Layer Supertype for the concerns that are
genuinely universal across a layer and Decorator or Strategy for the concerns
that need to vary per instance.

## 14. Refactoring path in and out

**Introducing Layer Supertype.** The standard route is Refactoring's Extract
Superclass, applied deliberately along an architectural layer boundary rather
than a narrow, pre-existing inheritance hierarchy
([refactoring.com, catalog](https://refactoring.com/catalog/), verified
2026-08-02; Martin Fowler, *Refactoring, Improving the Design of Existing
Code*, 2nd edition, Addison-Wesley, 2018). Identify several sibling types in
the same layer that carry duplicated members, an identical identifier field,
an identical `equals` implementation, an identical validation error list.
Create an empty abstract base class or interface for the layer. Move one
duplicated member up at a time using Pull Up Field or Pull Up Method, running
the full test suite green after every single move, never batching several
moves before re-running the tests. Watch specifically for a member that looks
textually identical across two types but actually encodes a different
business meaning, two `getId()` methods that happen to return the same type
but are keyed by conceptually different identifiers, which should not be
pulled up even though they look like duplication on the surface. Only once
every genuinely shared member has been moved does each sibling type formally
declare `extends LayerSupertype` or its language equivalent.

**Removing or narrowing Layer Supertype.** When the God Base Class symptom or
the fragile base class symptom from dimension 11 recurs, the refactoring path
runs in reverse and in a specific order. First, use Push Down Method and Push
Down Field to move any member that turns out to be used by only one or two
concrete types back down out of the shared supertype, narrowing it toward
genuinely universal members only. Second, where several members cluster
together and are used by an overlapping but not identical subset of concrete
types, extract each cluster into its own small interface or trait using
Extract Interface, converting one wide supertype into several narrow,
composable ones. Third, when a specific concrete type needs the supertype's
behavior but must also extend a different class for a genuine is a
relationship the language will not allow alongside the supertype, apply
Replace Superclass with Delegate, also known as Replace Inheritance with
Delegation, converting the is a relationship into a has a relationship plus
explicit forwarding methods for exactly the members that type still needs
([refactoring.com, catalog](https://refactoring.com/catalog/), verified
2026-08-02).

## 15. Testing and verification

The supertype itself earns a dedicated, focused unit test suite covering
identity semantics, `equals` and hash consistency across identical and
differing identifiers, error collection behavior, `addError`, `isValid`,
`getErrors`, and, where present, the template method's fixed skeleton
behavior independent of any one concrete step implementation. Writing this
suite once against the supertype directly, rather than re-verifying the same
identity and error handling behavior inside every concrete subtype's own test
file, is a genuine and measurable reduction in total test code for the layer.

Each concrete subtype's own test suite then narrows to the behavior that is
actually specific to it, `Order.validate()` rejecting an order with zero line
items, `Customer.validate()` rejecting a malformed email, without re-asserting
identity or error list mechanics the supertype's suite already covers.

A shared, parameterized contract test, run once per concrete type in the
layer rather than once total, closes the one real gap that dedicated
supertype and per subtype tests leave open on their own. It catches a
concrete type that technically compiles against the supertype's contract but
subtly breaks one of its invariants, most commonly a subclass that overrides
`equals` without also overriding the matching hash function, or a controller
subtype that overrides a response helper in a way that stops producing the
standard error envelope every sibling controller is expected to produce. This
is the mechanism the failure mode table in dimension 11 references when it
says an inherited contract violation is caught by a suite run against every
sibling, not by any single subtype's own tests in isolation.

What genuinely gets harder is building a minimal, hand rolled test double for
a concrete type on the caller side. A caller's test that only needs to stub
one narrow behavior of a concrete layer member must still satisfy the
supertype's full inherited surface to produce a value of the expected type, in
statically typed languages. Two mitigations apply directly. Prefer a real,
lightweight concrete subclass built purely for tests over a hand rolled mock
whenever the language makes that convenient, and, where the interface with
default methods variant from dimension 8 is in use, a test double only needs
to implement the interface's required members, not the class supertype's full
inherited state.

## 16. Observability signals

A Layer Supertype is an unusually good single point at which to instrument an
entire layer's cross cutting operations, because instrumentation added once,
inside the supertype's own shared method, automatically covers every current
and future concrete subtype without any per subtype duplication. A single log
line format emitted from the shared `Mapper.save()` method, "saved
`{table_name}` id=`{id}`", produces a consistent, greppable log line for
every entity type in the application with zero per mapper effort, exactly the
behavior shown in the Python sample's `_log` list. A single timing metric
wrapped around a shared `Controller.dispatch()` or `respond()` method
automatically produces latency data for every controller in the application
without a developer remembering to add timing to each new controller as it is
written.

The healthy pattern on a dashboard built from this instrumentation is a
roughly uniform latency and error rate distribution across every concrete
type that shares the supertype's code path, since they are, by construction,
running through the identical instrumented code. A single concrete type whose
numbers sit far apart from its siblings on that same shared dashboard, much
higher latency, a distinct error rate, is worth investigating specifically,
because that gap itself is a signal that the outlier subtype has overridden
or bypassed part of the shared behavior in a way the rest of the layer has
not.

A spike in an exception or assertion raised from inside the supertype's own
shared code, an identity invariant check inside a shared `equals`, a
precondition check inside a shared `save`, should be treated organizationally
as a layer wide incident from the first occurrence, not triaged as a bug in
whichever single concrete type happened to trigger it first, precisely
because the same code path serves every sibling in the layer simultaneously.

## 17. Security and privacy implications

Centralizing behavior in a Layer Supertype is a genuine security asset when
the centralized behavior is itself security relevant. A shared, base level
authorization or CSRF check run once inside the presentation layer's
Controller supertype, the kind of `before_action` hook Rails' own
`ApplicationController` convention supports, or an `[Authorize]` style filter
applied at the controller base in ASP.NET Core, means there is exactly one
place to review, patch, and verify that check, rather than trusting every
individual controller author to have remembered to add it independently.

The exact same concentration is a proportional liability when the shared
behavior is wrong. A missing check, or a check with a subtle bug, inside the
Layer Supertype is not a single controller's vulnerability, it is every
controller in the entire layer's vulnerability simultaneously, from the
moment the flawed supertype code ships. This is the direct security
counterpart of the fragile base class problem in dimension 11, and it argues
for the supertype's own code receiving proportionally more security review
attention than any one concrete subtype receives on its own, precisely
because a defect there has the widest possible blast radius in the layer.

A second, more subtle risk shows up around any generic serialization,
logging, or `toString` style helper placed on the supertype. A debug log
statement written once against the supertype, logging every field of
whichever domain object is passed to it, will silently serialize every field
of every current and future concrete subtype that extends it, including a
sensitive field added to a specific subtype months later by a developer who
never saw, and had no reason to check, the generic logging helper sitting on
the shared base. The concrete, practical mitigation is to make the
supertype's default serialization or logging behavior exclude fields unless a
field is explicitly opted in, rather than defaulting to including every field
a subtype happens to declare.

## Code examples

The languages below deliberately cover four different implementation
variants from dimension 8, an abstract class carrying concrete shared state
in TypeScript, an abstract class hosting a Template Method in Python, struct
embedding in Go, the language's idiomatic answer where classical inheritance
does not exist, and a protocol with default method implementations in Swift,
the variant that avoids spending the language's single class inheritance slot.
Java is deliberately omitted from the compiled samples because no working JDK
was available in the environment this entry was authored in. Both `javac` and
`java` reported an inability to locate a Java runtime. The reader should treat
the Java default methods citation in dimension 8 as documentation, not as a
claim that Java code in this entry was compiled. Every sample shown below was
compiled or run directly, and its printed output is reported exactly as
produced in the surrounding prose.

### TypeScript

A domain layer Layer Supertype, `DomainObject`, supplying identity comparison
by identifier and a shared validation error list, with `Order` and `Customer`
as concrete subtypes. Compiled with `tsc --strict` and run with `node`.

```typescript
abstract class DomainObject {
  protected readonly id: string;
  private readonly errors: string[] = [];

  protected constructor(id: string) {
    this.id = id;
  }

  getId(): string {
    return this.id;
  }

  equals(other: unknown): boolean {
    if (!(other instanceof DomainObject)) return false;
    if (this.constructor !== other.constructor) return false;
    return this.id === other.id;
  }

  addError(message: string): void {
    this.errors.push(message);
  }

  isValid(): boolean {
    return this.errors.length === 0;
  }

  getErrors(): readonly string[] {
    return this.errors;
  }

  abstract validate(): void;
}

class Order extends DomainObject {
  constructor(id: string, private readonly lineItemCount: number) {
    super(id);
  }

  validate(): void {
    if (this.lineItemCount === 0) {
      this.addError("an order needs at least one line item");
    }
  }
}

class Customer extends DomainObject {
  constructor(id: string, private readonly email: string) {
    super(id);
  }

  validate(): void {
    if (!this.email.includes("@")) {
      this.addError("customer email looks malformed");
    }
  }
}

function validateAll(objects: DomainObject[]): DomainObject[] {
  const invalid: DomainObject[] = [];
  for (const obj of objects) {
    obj.validate();
    if (!obj.isValid()) invalid.push(obj);
  }
  return invalid;
}

const order = new Order("ord-1", 0);
const customer = new Customer("cus-1", "not-an-email");
const goodOrder = new Order("ord-2", 3);

const invalid = validateAll([order, customer, goodOrder]);
console.log(`invalid count: ${invalid.length}`);
for (const obj of invalid) {
  console.log(`${obj.getId()}: ${obj.getErrors().join(", ")}`);
}
console.log(`order.equals(order): ${order.equals(order)}`);
console.log(`order.equals(customer): ${order.equals(customer)}`);
```

Running this program prints the invalid count, each invalid object's errors,
and the two equality checks.

```text
invalid count: 2
ord-1: an order needs at least one line item
cus-1: customer email looks malformed
order.equals(order): true
order.equals(customer): false
```

### Python

A data source layer Layer Supertype, `AbstractMapper`, hosting a Template
Method for `find` and `save`, with two concrete in memory mappers standing in
for `OrderMapper` and `CustomerMapper` against a real database. Run with
`python3`.

```python
from abc import ABC, abstractmethod
from typing import Optional


class AbstractMapper(ABC):
    def __init__(self, connection: dict):
        self._connection = connection
        self._log: list[str] = []

    def find(self, id: str) -> Optional[dict]:
        self._log.append(f"find {self.table_name()} id={id}")
        row = self._select(id)
        if row is None:
            return None
        return self._to_domain(row)

    def save(self, obj: dict) -> None:
        self._log.append(f"save {self.table_name()} id={obj['id']}")
        if self._select(obj["id"]) is None:
            self._insert(obj)
        else:
            self._update(obj)

    def log(self) -> list[str]:
        return list(self._log)

    @abstractmethod
    def table_name(self) -> str: ...

    @abstractmethod
    def _select(self, id: str) -> Optional[dict]: ...

    @abstractmethod
    def _insert(self, obj: dict) -> None: ...

    @abstractmethod
    def _update(self, obj: dict) -> None: ...

    @abstractmethod
    def _to_domain(self, row: dict) -> dict: ...


class InMemoryOrderMapper(AbstractMapper):
    def __init__(self, connection: dict):
        super().__init__(connection)
        self._rows: dict[str, dict] = {}

    def table_name(self) -> str:
        return "orders"

    def _select(self, id: str) -> Optional[dict]:
        return self._rows.get(id)

    def _insert(self, obj: dict) -> None:
        self._rows[obj["id"]] = dict(obj)

    def _update(self, obj: dict) -> None:
        self._rows[obj["id"]] = dict(obj)

    def _to_domain(self, row: dict) -> dict:
        return {"id": row["id"], "total": row["total"]}


class InMemoryCustomerMapper(AbstractMapper):
    def __init__(self, connection: dict):
        super().__init__(connection)
        self._rows: dict[str, dict] = {}

    def table_name(self) -> str:
        return "customers"

    def _select(self, id: str) -> Optional[dict]:
        return self._rows.get(id)

    def _insert(self, obj: dict) -> None:
        self._rows[obj["id"]] = dict(obj)

    def _update(self, obj: dict) -> None:
        self._rows[obj["id"]] = dict(obj)

    def _to_domain(self, row: dict) -> dict:
        return {"id": row["id"], "email": row["email"]}


def main() -> None:
    order_mapper: AbstractMapper = InMemoryOrderMapper({})
    customer_mapper: AbstractMapper = InMemoryCustomerMapper({})
    order_mapper.save({"id": "ord-1", "total": 42})
    customer_mapper.save({"id": "cus-1", "email": "a@b.com"})

    for mapper in (order_mapper, customer_mapper):
        for line in mapper.log():
            print(line)

    print(order_mapper.find("ord-1"))
    print(customer_mapper.find("cus-1"))
    print(order_mapper.find("missing"))


if __name__ == "__main__":
    main()
```

Running this program prints the shared mapper log lines, produced entirely by
the supertype, followed by the two found rows and one miss.

```text
save orders id=ord-1
save customers id=cus-1
{'id': 'ord-1', 'total': 42}
{'id': 'cus-1', 'email': 'a@b.com'}
None
```

### Go

A presentation layer Layer Supertype, `BaseController`, reproducing the
`Ok` and `NotFound` style response helpers ASP.NET Core's `Controller` base
class supplies, built with Go's struct embedding since Go has no classical
class inheritance. Run with `go run`.

```go
package main

import (
	"encoding/json"
	"fmt"
	"net/http"
)

type BaseController struct {
	Name string
}

func (c *BaseController) OK(w http.ResponseWriter, payload any) {
	c.respond(w, http.StatusOK, payload)
}

func (c *BaseController) NotFound(w http.ResponseWriter, message string) {
	c.respond(w, http.StatusNotFound, map[string]string{"error": message})
}

func (c *BaseController) BadRequest(w http.ResponseWriter, message string) {
	c.respond(w, http.StatusBadRequest, map[string]string{"error": message})
}

func (c *BaseController) respond(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	body, _ := json.Marshal(payload)
	fmt.Fprintf(w, "%s [from %s]\n", body, c.Name)
}

type OrdersController struct {
	BaseController
	orders map[string]int
}

func NewOrdersController() *OrdersController {
	return &OrdersController{
		BaseController: BaseController{Name: "OrdersController"},
		orders:         map[string]int{"ord-1": 42},
	}
}

func (c *OrdersController) Show(w http.ResponseWriter, id string) {
	total, found := c.orders[id]
	if !found {
		c.NotFound(w, "order not found")
		return
	}
	c.OK(w, map[string]any{"id": id, "total": total})
}

type recorder struct {
	status int
	header http.Header
}

func newRecorder() *recorder {
	return &recorder{header: http.Header{}}
}

func (r *recorder) Header() http.Header { return r.header }
func (r *recorder) Write(b []byte) (int, error) {
	fmt.Print(string(b))
	return len(b), nil
}
func (r *recorder) WriteHeader(s int) { r.status = s }

func main() {
	controller := NewOrdersController()
	w := newRecorder()
	controller.Show(w, "ord-1")
	fmt.Println("status:", w.status)

	w2 := newRecorder()
	controller.Show(w2, "missing")
	fmt.Println("status:", w2.status)
}
```

Running this program shows the promoted `BaseController` methods producing a
JSON body plus a status line for a found and a missing order.

```text
{"id":"ord-1","total":42} [from OrdersController]
status: 200
{"error":"order not found"} [from OrdersController]
status: 404
```

### Swift

A view model layer Layer Supertype implemented as a protocol with default
method implementations, so a concrete view model still has its single class
inheritance slot free for another purpose if it ever needs one. Compiled with
`swiftc`.

```swift
protocol ValidatableViewModel: AnyObject {
    var errors: [String] { get set }
    func validate()
}

extension ValidatableViewModel {
    var isValid: Bool { errors.isEmpty }

    func addError(_ message: String) {
        errors.append(message)
    }
}

final class LoginViewModel: ValidatableViewModel {
    var errors: [String] = []
    var username: String
    var password: String

    init(username: String, password: String) {
        self.username = username
        self.password = password
    }

    func validate() {
        errors.removeAll()
        if username.isEmpty {
            addError("username is required")
        }
        if password.count < 8 {
            addError("password must be at least 8 characters")
        }
    }
}

final class SignupViewModel: ValidatableViewModel {
    var errors: [String] = []
    var email: String

    init(email: String) {
        self.email = email
    }

    func validate() {
        errors.removeAll()
        if !email.contains("@") {
            addError("email looks malformed")
        }
    }
}

let viewModels: [ValidatableViewModel] = [
    LoginViewModel(username: "", password: "short"),
    SignupViewModel(email: "not-an-email"),
    LoginViewModel(username: "mirza", password: "longenoughpassword"),
]

for vm in viewModels {
    vm.validate()
    print("valid=\(vm.isValid) errors=\(vm.errors)")
}
```

Running this program validates each view model in turn and prints its
validity and its error list.

```text
valid=false errors=["username is required", "password must be at least 8 characters"]
valid=false errors=["email looks malformed"]
valid=true errors=[]
```

## 18. References

1. Martin Fowler, "Layer Supertype", Patterns of Enterprise Application
   Architecture catalog, [martinfowler.com/eaaCatalog/layerSupertype.html](https://martinfowler.com/eaaCatalog/layerSupertype.html),
   verified 2026-08-02.
2. Martin Fowler, *Patterns of Enterprise Application Architecture*,
   Addison-Wesley, 2002, chapter 18, "Base Patterns".
3. Martin Fowler, full pattern catalog, [martinfowler.com/eaaCatalog/](https://martinfowler.com/eaaCatalog/),
   verified 2026-08-02, used to confirm the Base Patterns grouping and the
   full list of related architectural patterns in the book.
4. Rails Guides, "Active Record Basics", [guides.rubyonrails.org/active_record_basics.html](https://guides.rubyonrails.org/active_record_basics.html),
   verified 2026-08-02, source for the `ActiveRecord::Base` and
   `ApplicationRecord` production use in dimension 9.
5. Django Software Foundation, "Models", Django documentation, version 5.0,
   [docs.djangoproject.com/en/5.0/topics/db/models/](https://docs.djangoproject.com/en/5.0/topics/db/models/),
   verified 2026-08-02, source for the `django.db.models.Model` production use
   in dimension 9.
6. Microsoft, "Handle requests with controllers in ASP.NET Core MVC",
   Microsoft Learn, [learn.microsoft.com/en-us/aspnet/core/mvc/controllers/actions](https://learn.microsoft.com/en-us/aspnet/core/mvc/controllers/actions?view=aspnetcore-8.0),
   verified 2026-08-02, source for the ASP.NET Core `Controller` base class
   production use in dimension 9 and the Go sample's structural model.
7. Red Hat, Hibernate ORM 6.4 User Guide, section 3.14.1, "Inheritance",
   [docs.hibernate.org/orm/6.4/userguide/html_single/Hibernate_User_Guide.html](https://docs.hibernate.org/orm/6.4/userguide/html_single/Hibernate_User_Guide.html),
   verified 2026-08-02, source for the `@MappedSuperclass` production use in
   dimension 9.
8. Martin Fowler, *Refactoring, Improving the Design of Existing Code*, 2nd
   edition, Addison-Wesley, 2018, refactorings Extract Superclass, Pull Up
   Method, Pull Up Field, Push Down Method, Push Down Field, and Replace
   Superclass with Delegate.
9. Refactoring.com, refactoring catalog, [refactoring.com/catalog/](https://refactoring.com/catalog/),
   verified 2026-08-02, used to confirm the exact current names of the six
   refactorings cited in dimension 14.
10. Oracle, "Default Methods", The Java Tutorials, [docs.oracle.com/javase/tutorial/java/IandI/defaultmethods.html](https://docs.oracle.com/javase/tutorial/java/IandI/defaultmethods.html),
    verified 2026-08-02, source for the Java interface default method
    implementation variant in dimension 8.
11. Apple, "Protocols", *The Swift Programming Language*, [docs.swift.org/swift-book/documentation/the-swift-programming-language/protocols/](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/protocols/),
    verified 2026-08-02, source for the Swift protocol extension
    implementation variant in dimension 8 and the Swift code sample.
12. The Go Authors, "Effective Go", Embedding section, [go.dev/doc/effective_go#embedding](https://go.dev/doc/effective_go#embedding),
    verified 2026-08-02, source for the Go struct embedding implementation
    variant in dimension 8, dimension 11's promoted method receiver failure
    mode, and the Go code sample.
13. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides, *Design
    Patterns, Elements of Reusable Object-Oriented Software*, Addison-Wesley,
    1994, used for the Template Method, Decorator, and Strategy patterns
    named in dimensions 12 and 13.
