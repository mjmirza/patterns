---
name: Module
slug: module
family: 11-ddd
category: Domain-Driven Design
aliases: [Package, Namespace, Bounded Context Internal Grouping]
first_described: "Evans 2003"
maturity: canonical
related: [aggregate, bounded-context, layered-architecture, hexagonal-architecture, repository]
incompatible_with: []
verified: 2026-08-02
---

# Module

## 1. Name, aliases, and lineage

The canonical name is Module. Eric Evans introduced it as one of the building
blocks of a model expressed in software, in *Domain-Driven Design. Tackling
Complexity in the Heart of Software*, Addison-Wesley, 2003, Chapter 5, "A Model
Expressed in Software", in the section titled "Modules (aka Packages)"
([chapter breakdown listing "Modules (aka Packages)" as a section of Chapter
5](https://herbertograca.com/2015/09/29/domain-driven-design-by-eric-evans-chap-5-a-model-expressed-in-software/),
verified 2026-08-02). Evans deliberately wrote the alias into the section title
itself, because the mechanism a programming language already offers for
grouping code, a Java package, a C# namespace, a Python package, a Ruby module,
a Go package, is the physical container Evans is asking a team to use with
domain intent rather than technical convenience.

Vaughn Vernon devotes a full chapter to the same idea in *Implementing
Domain-Driven Design*, Addison-Wesley, 2013, Chapter 9, "Modules"
([the chapter is titled "Modules" and opens by mapping the concept onto Java
packages and C# namespaces](https://www.oreilly.com/library/view/implementing-domain-driven-design/9780133039900/ch09.html),
verified 2026-08-02, page fetch returned 403 so this citation rests on the
indexed chapter title and abstract rather than full chapter text, so treat the
package-versus-namespace mapping as reported, not quoted). Vernon's chapter is
the source most practitioners cite for the "package by component" style that
this entry uses as its primary implementation variant, distinguishing it from
the older "package by layer" style that predates DDD entirely.

Outside the DDD literature the same grouping mechanism is called a namespace
(C++, C#, PHP), a package (Java, Python, Go, Dart), a module (Ruby, and Python's
own `module` keyword is absent, but the community calls a `.py` file a module
and a directory of them a package, which is a genuine source of confusion this
entry addresses in dimension 4), or a crate plus its module tree (Rust). This
entry uses Module as Evans meant it, a named, cohesive group of model
elements, bearing a name drawn from the ubiquitous language, whose boundary is
a design decision and not an artifact of file-system convenience.

## 2. Problem and context

A domain model that stays in one undifferentiated pile of classes becomes
unreadable long before it becomes incorrect. A developer opening a
directory of two hundred files with no organizing principle cannot answer
the two questions that matter most before making a change, what does this
class depend on, and what depends on it. Evans frames the underlying
problem as cognitive, not mechanical. A person can hold a small number of
concepts in mind at once, so a model with high internal coupling and no
seams is a model nobody can reason about, however correct any single class
is in isolation (Evans 2003, Chapter 5, "Modules").

The context in which Module becomes the right tool has three recurring
shapes. First, a model has grown past the size where every developer can
recall the full class list, typically somewhere between fifteen and forty
classes, and new developers can no longer form a mental map from a
directory listing. Second, a codebase mixes multiple sub-domains inside one
process, an order sub-domain and a shipping sub-domain and a billing
sub-domain sharing a database and a deploy pipeline, and classes from each
sub-domain reference each other without any boundary marking where one ends
and the next begins. Third, a refactor toward Bounded Contexts is underway
and the team needs an intermediate, low-risk step, since splitting a
process into microservices is expensive and reversible splitting inside a
single deployable is not.

Module is deliberately a lighter-weight tool than Bounded Context. A
Bounded Context draws a hard boundary around a whole model, including its
own ubiquitous language and its own database schema when warranted. A
Module draws a boundary inside one model, inside one Bounded Context,
grouping the classes that belong together conceptually. Confusing the two
is the single most common structural mistake this entry documents in
dimension 11.

## 3. Forces

Discoverability pulls toward small, numerous modules, so that a developer
searching for "where does shipment tracking live" finds one directory and
not a scattered set of files interleaved with unrelated code. Cohesion
pulls the same direction, since Evans is explicit that a module should tell a
story, so that reading its class list reads like a paragraph about one
part of the domain, not an index (Evans 2003, Chapter 5).

Coupling pulls the opposite direction. Too many small modules, each with a
narrow interface to the next, multiplies the number of dependency edges a
developer must trace to change one behavior, and a change that should touch
one concept ends up touching imports in five modules. Evans names this
directly, a module boundary chosen for low coupling between modules and
high cohesion within each module is doing its job, while a boundary chosen for
any other reason, alphabetical grouping, technical layer, or accident of
who wrote the code, is not (Evans 2003, Chapter 5).

Deployability and buildability pull toward modules that also serve as
compilation or packaging units, because a language's own module mechanism
(a Java package plus a build tool's artifact boundary, a Rust crate, a Go
module with its own `go.mod`) gets compiler-enforced encapsulation for
free. This force is in tension with the pure-domain-conceptual force above,
because the concept boundary a domain expert would draw and the
compilation boundary a build engineer would draw do not always coincide,
and Module as Evans defines it favors the conceptual boundary even when it
costs the build engineer extra ceremony.

Team topology is the fourth force, and it is the one most catalogs skip.
Conway's Law means the module boundaries a team draws tend to converge on
the team's own communication boundaries over time, whether or not that
convergence was intended (Melvin Conway, "How Do Committees Invent?",
Datamation, April 1968, the paper that names the effect later called
Conway's Law; the original text is reproduced at
[https://www.melconway.com/Home/pdf/committees.pdf](https://www.melconway.com/Home/pdf/committees.pdf),
verified 2026-08-02). A single team maintaining twelve tightly coupled
modules pays a coordination tax the module boundaries cannot remove; a
module boundary that also matches a team boundary tends to survive
refactoring pressure longer than one that does not, because ownership
gives someone a reason to defend it.

Module sacrifices navigational locality for conceptual clarity. A developer
who thinks in terms of technical layers, all controllers together, all
repositories together, loses the ability to jump straight to "everything
about shipping" with a Module boundary organized by concept instead, and
must instead learn where each concept's own controller and repository
live. This is the trade Evans asks a team to make deliberately, and it is
the trade dimension 4 explains in more depth.

## 4. Applicability and non-applicability

Reach for Module when a model has grown past the point where a flat
directory or a single namespace communicates structure, when two or more
sub-domains share a process and their classes are visibly tangled, when
you are staging a future split into separate Bounded Contexts and want the
seam drawn and tested before paying the cost of a network boundary, or when
new team members consistently cannot find where a concept lives without
asking someone.

Do not reach for Module in the following situations.

- **A model with fewer than roughly a dozen classes.** Evans notes that
  modules chosen too early, before the natural seams in the model have
  revealed themselves through use, tend to be redrawn repeatedly and the
  churn costs more than the flat structure it replaced (Evans 2003, Chapter
  5, discussing that modules, like every other part of the model, are
  refined through iteration rather than fixed at the start).
- **When the grouping principle is purely technical, not conceptual.** A
  `controllers` folder, a `services` folder, a `utils` folder sorted by
  what kind of object a class is rather than what part of the domain it
  belongs to is package by layer, and Evans's own definition of a module
  explicitly rejects a boundary chosen for a reason other than coupling and
  cohesion in the domain (Evans 2003, Chapter 5). Package by layer is a
  legitimate organizing principle for infrastructure code; it is the wrong
  principle for the domain model itself.
- **When the boundary you actually need is a process boundary.** If two
  groups of classes need independent deployment, independent scaling, or
  genuinely separate persistence, the right tool is a Bounded Context
  realized as a separate service, not a Module inside one process. Using a
  Module to simulate a process boundary produces a distributed monolith's
  worst property, tight coupling, without its best property, independent
  deployability.
- **When a single team of two or three people owns the entire codebase and
  can hold the whole model in working memory.** The cost of maintaining
  module boundaries, resolving import cycles across them, deciding which
  module owns a cross-cutting type, is real and is not worth paying below
  a certain team and codebase size. Evans's own guidance is to let modules
  emerge from refactoring pressure rather than impose them speculatively.
- **When the codebase is a thin CRUD layer over a database with no
  meaningful domain logic.** DDD's tactical patterns as a group, Module
  included, earn their cost against genuine domain complexity, and
  applying them to a model that is really just data transfer produces
  ceremony with no corresponding clarity gain, a point DDD practitioners
  raise frequently when warning against over-application of the pattern
  set (see the "when not to use DDD" discussion cited under dimension 11
  for a named source).

## 5. Structure

| Participant | Responsibility |
|---|---|
| Module | A named container holding a cohesive set of model elements, exposed through the host language's own grouping mechanism (package, namespace, or module keyword). Carries a name drawn from the ubiquitous language. |
| Model element | An Entity, Value Object, Aggregate, Domain Service, Repository interface, or Domain Event that the module groups. Belongs to exactly one module as its home, even when referenced from elsewhere. |
| Module boundary | The set of public, exported types the module exposes to the rest of the system, and by omission, the set of internal types it keeps private. This is the encapsulation surface, enforced by the language's access modifiers (Java `package-private`, Rust `pub(crate)`, Go's lowercase-identifier convention). |
| Dependency edge | A reference from one module's element to another module's exported type. The direction and count of these edges across the whole codebase is the thing coupling is measured on. |
| Ubiquitous language term | The domain concept the module name is drawn from. A module named for a technical concern ("utils", "helpers", "common") has no ubiquitous language term behind it, which is the diagnostic sign of a technically rather than conceptually chosen boundary. |

Two module boundaries are worth naming explicitly because they recur in
nearly every real system, the module that groups an Aggregate together with
its Value Objects and the Repository interface that persists it, and the
module that groups a set of related Domain Services that coordinate across
several Aggregates. The first kind tends to be small and stable. The second
kind tends to grow and is the one most often split later.

## 6. ASCII structure diagram

```
+-------------------------------------------------------------+
|                     Bounded Context. Ordering                |
|                                                                |
|  +----------------------+       +--------------------------+ |
|  |  Module. order        |       |  Module. shipping         | |
|  |------------------------|       |----------------------------| |
|  |  Order (Aggregate)     |------>|  ShippingLabel (Aggregate)| |
|  |  OrderLine (Entity)    | reads |  Carrier (Value Object)   | |
|  |  Money (Value Object)  |       |  ShippingRepository       | |
|  |  OrderRepository       |       |  (interface)               | |
|  |  (interface)           |       +--------------------------+ |
|  +-----------+------------+                                    |
|              |                                                 |
|              | publishes                                       |
|              v                                                 |
|  +----------------------------------+                          |
|  |  Module. shared_kernel            |                          |
|  |------------------------------------| <-- referenced by both  |
|  |  CustomerId (Value Object)         |     order and shipping  |
|  |  Money (Value Object, shared type) |                          |
|  |  DomainEvent (marker interface)    |                          |
|  +----------------------------------+                          |
+-------------------------------------------------------------+

Legend
  ------->   a public dependency, arrow points from consumer to depended-on module
  A box's inner list is that module's exported model elements only
```

The diagram deliberately shows one shared, small module (`shared_kernel`)
rather than a web of cross-references between `order` and `shipping`
directly, because the acyclic property, no module transitively depends on
itself through another module, is the structural invariant a healthy module
graph maintains. `order` and `shipping` may both depend on `shared_kernel`;
if `shipping` also depended directly on `order`'s internal `OrderLine`
type, the arrow would need to point the other way as well, and that cycle
is the failure mode documented in dimension 11.

## 7. Dynamics

At compile or interpret time, a language's own module resolution mechanism
enforces the encapsulation boundary before any of the domain logic runs.
A Java `package-private` class referenced from outside its package fails
to compile; a Python module attribute prefixed with a single leading
`_` is merely a convention the interpreter does not enforce, which is a real
difference this entry returns to in dimension 8. This compile-time or
import-time check is the first and cheapest place a module boundary
violation is caught, well before any runtime behavior is observed.

At runtime, a request enters through one module's public interface, most
often an Application Service or a controller sitting in an infrastructure
or application module, and that entry point calls into the domain modules
it needs, each call crossing exactly the exported surface of the target
module. A well-drawn module boundary means a single request typically
touches a small number of modules, usually one to three for a focused use
case; a request that fans out across eight or ten modules to complete one
business operation is a runtime symptom of a boundary drawn along the
wrong seam, because the modules that should have been merged were kept
apart, or the reverse.

```
Caller module              order module               shipping module
    |                          |                             |
    | PlaceOrder(cmd)          |                             |
    |------------------------->|                             |
    |                          | Order.place(...)            |
    |                          |---------.                   |
    |                          |<--------'                   |
    |                          | publish OrderPlaced event    |
    |                          |----------------------------->|
    |                          |                             | on(OrderPlaced)
    |                          |                             |---------.
    |                          |                             |<--------'
    |                          |                             | ShippingLabel.create(...)
    |<-------------------------|                             |
    | OrderPlaced (ack)        |                             |
```

The event-based hop from `order` to `shipping` in the diagram is the
common pattern for keeping two modules decoupled at the call-graph level
even when one module's business event genuinely needs to trigger work in
another; `shipping` depends on the shape of `OrderPlaced`, a small,
stable, exported type, rather than depending on `order`'s internal
`Order` Aggregate directly. This indirection is optional. A direct
synchronous call from `order` to `shipping`'s exported
`ShippingRepository` interface is equally valid Module usage when the two
concepts are tightly enough related that eventual consistency between them
would be surprising to a domain expert. The choice between the two is a
force from dimension 3, coupling versus immediacy, not a rule Module
itself dictates.

## 8. Implementation variants

**Package by layer.** The pre-DDD default in many codebases, a top-level
`controllers`, `services`, `repositories`, `models` split, with every
concept's classes scattered one per layer folder. This is explicitly the
variant Evans's own definition of Module argues against, because the
grouping principle is technical role rather than domain cohesion, and
finding "everything about Order" means opening four unrelated folders
(Evans 2003, Chapter 5). It remains common because most web framework
scaffolding tools (Rails generators, ASP.NET MVC project templates,
Spring Initializr's default layout) produce it by default, and it is a
reasonable choice for infrastructure code that genuinely has no domain
concept, but it is package by layer, not the Module pattern.

**Package by feature or component.** Vernon's chapter organizes each
sub-domain concept, its Aggregates, Value Objects, Domain Services, and
Repository interfaces, into one package, with technical layers (a web
controller, a JPA-backed repository implementation) living in
sibling packages that depend inward on the domain package rather than the
reverse. This is the variant this entry treats as the DDD-idiomatic
default because it directly implements Evans's coupling-and-cohesion
rule; the trade is that infrastructure code for one concept is no longer
grouped with infrastructure code for another concept, which some teams
find less discoverable at first.

**Layered inside a component.** A hybrid, common in larger codebases, where
the top-level split is by domain component (order, shipping, billing) and
each component internally splits by layer (application, domain,
infrastructure). This is package by feature at the top level and package
by layer one level down, and it is the shape most Hexagonal Architecture
and Clean Architecture implementations converge on in practice, because
it gets the domain-discoverability benefit at the level developers
actually search at while still separating a domain type from its
persistence adapter.

**Language-enforced module boundaries.** Rust crates plus `pub(crate)`
visibility, Java 9+ module descriptors (`module-info.java` with
`exports` and `requires`), and Go's implicit lowercase-is-unexported
convention each let the compiler reject an illegal cross-module
reference, turning the module boundary from a convention a linter checks
into a build failure. This is strictly stronger than the convention-only
enforcement Python and pre-modules Java offer, at the cost of upfront
declaration overhead; Java's module system in particular saw slow
adoption specifically because retrofitting `module-info.java` onto an
existing large codebase with implicit cross-package dependencies is
expensive (Oracle, "The State of the Module System", JEP 261 background
document, [https://openjdk.org/jeps/261](https://openjdk.org/jeps/261),
verified 2026-08-02, describing the strong encapsulation the module
system introduces over plain packages).

**Convention-only module boundaries.** Python packages, pre-Java-9
packages, and most JavaScript project layouts have no compiler-enforced
privacy between modules; a module boundary here is documentation and
linter configuration (a Python `__all__` list, an ESLint
`no-restricted-imports` rule, an architecture-testing tool like
ArchUnit for the JVM or `depcruise` for JavaScript that fails a build
when an import crosses a forbidden boundary) rather than a language
guarantee. This variant is strictly weaker in enforcement but is the only
option in languages with no module-privacy primitive, and it is where
dimension 16's observability signals matter most, because there is no
compiler to catch a violation before it reaches code review.

## 9. Known production uses

The Java Platform Module System (Project Jigsaw, shipped in Java 9,
2017) is a language-level implementation of exactly the encapsulation
Module describes. A `module-info.java` file declares which packages a
module exports and which other modules it requires, and the JVM enforces
strong encapsulation at both compile time and runtime, rejecting reflective
access to non-exported internals that worked freely under the classpath
model (Oracle, JEP 261, "Module System",
[https://openjdk.org/jeps/261](https://openjdk.org/jeps/261), verified
2026-08-02).

Rust's module system, documented in the official Rust Book chapter "Managing
Growing Projects with Packages, Crates, and Modules", implements privacy
by default at the module level, requiring an explicit `pub` to export an
item, the same principle Evans describes for a domain module's
exported surface, applied by the compiler rather than by convention (The
Rust Programming Language, Chapter 7,
[https://doc.rust-lang.org/book/ch07-00-managing-growing-projects-with-packages-crates-and-modules.html](https://doc.rust-lang.org/book/ch07-00-managing-growing-projects-with-packages-crates-and-modules.html),
verified 2026-08-02).

Basecamp's Ruby on Rails codebase, and the "Packwerk" tool Shopify built
and open-sourced to enforce module boundaries inside a large Rails
monolith, is a named, documented production example of retrofitting
Module-style boundaries into a codebase that started as a single flat
`app/models` directory. Shopify's own engineering blog describes using
Packwerk to draw and enforce package boundaries across a monolith with
thousands of files specifically to reduce unintended coupling between
unrelated domain concepts (Shopify Engineering, "Enforce Modularity in
Rails Apps Using Packwerk",
[https://shopify.engineering/enforcing-modularity-rails-apps-packwerk](https://shopify.engineering/enforcing-modularity-rails-apps-packwerk),
verified 2026-08-02).

Spring Modulith, a Spring project explicitly built to let a Java Spring
Boot application be organized into DDD-style modules inside a single
deployable, with an accompanying test library (`ApplicationModules.verify()`)
that fails a build when a module boundary is violated, is a current,
actively maintained framework whose entire purpose is enforcing the Module
pattern as this entry describes it (Spring team, "Spring Modulith"
reference documentation,
[https://docs.spring.io/spring-modulith/reference/](https://docs.spring.io/spring-modulith/reference/),
verified 2026-08-02).

Microsoft's own eShop reference application groups each
business capability, ordering, catalog, basket, into its own project
within one solution, with project references enforcing which capability
can see which other capability's public types, the C# equivalent of
Vernon's package-by-component variant realized through the .NET project
system rather than a namespace alone (Microsoft, "eShop reference
application", GitHub repository,
[https://github.com/dotnet/eShop](https://github.com/dotnet/eShop),
verified 2026-08-02).

## 10. Consequences

**Positive.**

- A developer can locate the code for a domain concept by name, without
  needing to already know the codebase's technical layering, because the
  module name is drawn from the ubiquitous language the domain expert
  already uses.
- The module's exported surface becomes a natural place to write focused
  documentation and a natural unit for code review, since a reviewer can
  reason about one module's internal consistency without reading the
  whole codebase.
- When the module boundary is language-enforced, an entire class of bugs,
  accidental coupling to an internal type never meant to be depended on,
  is caught at compile time instead of discovered later as a refactoring
  hazard.
- A well-modularized codebase is measurably easier to split into separate
  services later, because the seams a service split would need are
  already drawn and already tested by the fact that the module boundary
  has survived real changes.

**Negative.**

- Drawing a module boundary in the wrong place is expensive to undo,
  because code that depends on a module's internals in ways the module's
  exported interface does not anticipate has to be found and rewritten
  before the boundary can move. Evans's own advice to let modules emerge
  through refactoring, rather than being decided up front, is a direct
  response to this cost (Evans 2003, Chapter 5).
- Cross-module coordination has real overhead. A change that spans two
  modules requires touching both, resolving whatever exported interface
  connects them, and possibly negotiating with a different code owner if
  team boundaries align with module boundaries.
- Convention-only enforcement (dimension 8) gives false confidence. A
  module diagram that looks clean can hide real, undetected violations
  that only a dependency-analysis tool run in CI would catch, and teams
  frequently skip adding that tool until the violations have already
  accumulated.
- Over-modularizing a small codebase adds indirection, extra files, extra
  import statements, extra places to look, that costs more in
  navigational friction than it returns in clarity, exactly the
  applicability boundary drawn in dimension 4.

## 11. Failure modes and misuse

**Symptom.** Two modules import each other's types, forming a dependency
cycle that a diagram like the one in dimension 6 would show as a
bidirectional arrow.
**Cause.** The boundary was drawn along a line that does not match the
actual coupling in the domain; the two concepts genuinely need each other
bidirectionally, or a shared concept was left un-extracted into a third,
smaller module both could depend on one-directionally.
**Fix.** Extract the shared concept into its own small module (the
`shared_kernel` in dimension 6's diagram is exactly this fix applied
proactively), or use an event, as in dimension 7, to invert one of the two
directions from a direct call into a published notification the other
module subscribes to.

**Symptom.** A module named for a technical role (`utils`, `helpers`,
`common`, `misc`) grows without bound and every other module ends up
depending on it.
**Cause.** No conceptual boundary was drawn for a piece of shared code
because nobody could immediately name the domain concept it belonged to,
so it was dropped into the nearest catch-all, which trained the rest of
the team to do the same.
**Fix.** Rename the module for the actual concept it serves once that
concept becomes clear; if the code genuinely has no domain concept
(a date-formatting helper, a retry wrapper) it belongs in an
infrastructure or shared-kernel module explicitly labeled as
domain-neutral, not in a module whose name implies it is part of the
domain model.

**Symptom.** A Bounded Context boundary is drawn identically to a Module
boundary, and the team treats "split it into a module" and "split it into
a service" as interchangeable decisions.
**Cause.** Confusing the two patterns, treated as a single named risk by
DDD practitioners. A Bounded Context carries its own ubiquitous language
and, when warranted, its own persistence, while a Module is an internal
organizational device inside one model. Martin Fowler's own writing on
Bounded Context is explicit that the term describes a linguistic and
model boundary, not a code-organization technique
([Martin Fowler, "BoundedContext"](https://martinfowler.com/bliki/BoundedContext.html),
verified 2026-08-02, distinguishing the model boundary from any particular
implementation technology or deployment topology).
**Fix.** Ask whether the two groups of classes use the same word to mean
different things (a Bounded Context signal) or the same word to mean the
same thing but with a natural conceptual seam between them (a Module
signal); the first calls for a Bounded Context, potentially a service
split, the second calls for a Module inside the existing context.

**Symptom.** A single module accretes every Domain Service in the system
because "services" felt like a natural top-level grouping, and it becomes
the largest, least cohesive module in the codebase.
**Cause.** Grouping by kind of object (all Domain Services together)
rather than by domain concept repeats the package-by-layer mistake at the
service level specifically. A payment-authorization service and a
shipment-scheduling service have nothing in common except both being
"services".
**Fix.** Move each Domain Service into the module of the domain concept it
primarily serves, following the same coupling-and-cohesion test Evans
applies to every other model element.

**Symptom.** DDD's tactical patterns, Module included, are applied to a
codebase whose domain is genuinely simple, and the team reports the
architecture feels heavier than the problem warrants.
**Cause.** This is the general over-application risk practitioners raise
about DDD's tactical layer as a whole. Vaughn Vernon himself, in public
talks and in *Implementing Domain-Driven Design*, cautions that the
tactical patterns are a response to genuine domain complexity and are not
a default starting posture for every codebase. This is Vernon's
well-documented general caution about DDD's tactical patterns rather than
a single quotable page reference; treat this claim as reported guidance,
not a page-level citation.
**Fix.** Measure the actual domain complexity before imposing module
boundaries; a codebase with a handful of straightforward CRUD entities and
no significant business rules does not need the ceremony this entry
describes.

## 12. Trade-off matrix

| Force | Module (package by feature) | Package by layer | Separate Bounded Context (service split) |
|---|---|---|---|
| Discoverability by domain concept | High, one directory per concept | Low, concept scattered across layer folders | High, but at the cost of crossing a network |
| Coupling between concepts | Low when boundaries are well chosen | High, layer folders have no concept isolation | Lowest, enforced by process and network boundary |
| Refactoring cost to change a boundary | Moderate, an in-process file move plus import fixes | Low, layers rarely need to move | High, requires a data migration and a deploy |
| Compile-time enforcement available | Yes in Java 9+, Rust, Go; convention-only elsewhere | Same as Module, language-dependent | Yes, enforced by the network itself |
| Team-topology fit | Good for one team, or teams that align to concepts | Neutral, does not encode team boundaries | Required when teams need independent release cadence |
| Setup and ongoing overhead | Moderate | Lowest | Highest, includes deployment, observability, and network failure handling |
| Appropriate codebase size | Small to large, once past roughly a dozen classes | Any size, best for infrastructure-heavy code | Large, with genuinely independent sub-domains |

## 13. Related and incompatible patterns

**Aggregate** is the model element Module most often groups as its central
unit, together with the Aggregate's own Value Objects and the Repository
interface that loads and saves it; a Module boundary that splits an
Aggregate's root from its own child entities across two different modules
is almost always a mistake, because an Aggregate is meant to be modified
and persisted as one consistency boundary, and splitting it across modules
makes that boundary harder to see and easier to violate.

**Bounded Context** is the pattern one level up in scope from Module, and
the two compose directly. A Bounded Context is typically realized as one
or more Modules, and the process of drawing clean Module boundaries inside
a context is frequently the exercise that reveals where a future Bounded
Context split should happen. The two are related by scale, not by
substitution; see dimension 11's failure mode for the specific way they
get confused.

**Layered Architecture** and **Hexagonal Architecture** describe how code
is organized by technical role (presentation, application, domain,
infrastructure) and Module describes how code is organized by domain
concept. The "layered inside a component" variant in dimension 8 shows
these two organizing principles composing at two different directory
levels rather than competing for the same one. Applying Layered
Architecture's principle (separate technical concerns) at the same
directory level Module's principle (separate domain concepts) wants to
own is the package-by-layer mistake this entry argues against.

**Repository** interfaces are conventionally declared inside the same
Module as the Aggregate they persist, with the implementation living in an
infrastructure module or an infrastructure sub-package. This split, an
interface in the domain module and an implementation in an infrastructure
module that depends inward on the domain module, is the concrete
mechanism that keeps the domain module free of a persistence-technology
dependency.

**Anti-Corruption Layer** typically lives at the boundary between two
Modules, or between a Module and an external system, translating between
the ubiquitous language on each side; it is the pattern that makes it safe
for two Bounded Contexts, or two Modules with genuinely different models
of an overlapping concept, to coexist without one corrupting the other's
language.

No pattern is flagged as incompatible with Module. It is a structural
device that composes with essentially every other pattern in this
catalog; the closest thing to tension is with a codebase that has already
committed hard to package by layer at scale, where retrofitting Module's
package-by-feature convention is a substantial, if valuable, refactor
rather than a drop-in addition.

## 14. Refactoring path in and out

**Introducing Module into an unstructured codebase.** Start by listing
every class currently in the flat model directory and grouping them on
paper by the domain concept they belong to, using the ubiquitous language
terms a domain expert would actually use, not the class names a
programmer chose. Pick the group with the fewest external references first,
create its module or package, move the classes, and fix the resulting
imports. Run the full test suite after each single-module extraction
rather than moving several groups at once, because a broken import is
trivial to diagnose after one move and confusing to diagnose after five.
Repeat, saving the module with the most incoming references, usually
something like a shared `Money` or `CustomerId` Value Object, for last,
since its own extraction into a small shared-kernel module is usually the
final cleanup once every consumer's own module already exists.

**Retrofitting compiler enforcement onto a convention-only boundary.** If
starting in Python, JavaScript, or pre-modules Java, first draw the module
boundaries using directories and get the team following the convention
manually. Once the boundaries have proven stable through several real
changes, introduce a dependency-checking tool in CI (ArchUnit for the JVM,
`dependency-cruiser` for JavaScript and TypeScript, `import-linter` for
Python) configured to fail the build on any import that crosses a
forbidden boundary. This order matters. Adding the enforcement tool before
the boundaries have stabilized produces constant, noisy failures as the
team is still discovering where the real seams are, and teams tend to
disable a noisy check rather than fix it.

**Removing a module boundary that no longer earns its cost.** When a
module has shrunk to a handful of classes with only one consumer, or when
two modules have grown so intertwined that nearly every change touches
both, merge them. Move all classes into one module, delete the now-empty
one, and update imports. This is the direct application of Evans's own
warning that a module boundary is refined through iteration, and removing
a boundary that has stopped paying for itself is as legitimate a
refactoring move as adding one that has become necessary.

**Splitting Module into a separate Bounded Context.** When a module's
boundary has proven stable and low-coupling for a sustained period, and a
genuine business or organizational reason (independent scaling,
independent release cadence, a separate team wanting ownership) demands a
process boundary, the module's already-exported interface is the seam a
service extraction uses. Replace the in-process calls across that
interface with calls over a network protocol, replace the shared database
transaction with an explicit integration pattern (an event, a published
API), and the module's internal structure, already isolated from the rest
of the codebase, needs comparatively little further change.

## 15. Testing and verification

A well-drawn module boundary is directly testable as an architectural
constraint, not only through the ordinary unit and integration tests of
the classes inside it. Architecture-testing tools let a team encode "no
class in module A may import a class from module B's internal package"
as an executable assertion that runs in CI on every commit. ArchUnit for
the JVM (`noClasses().that().resideInAPackage("..order..").should().dependOnClassesThat().resideInAPackage("..shipping.internal..")`)
and Spring Modulith's `ApplicationModules.verify()` are both concrete,
named tools that implement exactly this check.

Testing the classes inside one module in isolation is easier when the
module's own dependencies are limited to its declared, exported
interfaces from other modules, since a test double for a small,
intentional interface is straightforward to write, while a test double
for an accidentally-coupled internal type is brittle and tends to break
whenever the internal type's implementation changes for reasons unrelated
to the test.

What became harder is testing a use case that genuinely spans several
modules end to end. A request-level integration test now needs to wire
together real or test-double implementations from each module it touches,
and the module boundaries that make unit testing easier can make this kind
of broad integration test more ceremonious to set up, since the test now
needs an explicit strategy for each module's own dependencies rather than
one flat set of test fixtures.

A useful, cheap verification independent of any specific tool is to
generate a dependency graph of the actual codebase (most build tools and static
analyzers can produce one, `go mod graph` for Go, `jdeps` for Java, `cargo
tree` for Rust) and check it by eye for cycles between modules and for a
module with an unusually high number of incoming edges from unrelated
concepts, both of which are the direct symptoms named in dimension 11.

## 16. Observability signals

At build time, a language with compiler-enforced modules (Java 9+, Rust,
Go) surfaces a violation as a compile failure naming the exact
unauthorized import, which is the strongest and earliest signal available
and requires no additional instrumentation.

In a convention-only language, the signal has to be produced deliberately.
An architecture-testing tool's CI job failing, with the specific
forbidden import path in its failure message, is the equivalent signal,
delayed to CI time rather than compile time. A healthy codebase shows this
job passing consistently; a codebase where the module boundaries have
started eroding shows this job either failing intermittently as violations
creep in, or the job itself missing entirely, which is a signal in its
own right that nobody is watching the boundary.

At the code-review level, a reviewer watching for module health looks at
the diff's list of changed files. A change described as being about one
domain concept that touches files across four or five unrelated module
directories is a signal the boundary drawn does not match how the code
actually changes together, an instance of the "things that change
together should live together" heuristic that module boundaries are meant
to encode.

A metric worth tracking over time in a large codebase, computed from the
same dependency graph used in dimension 15's verification step, is the
fan-in and fan-out count per module. A module whose fan-in (number of
other modules depending on it) grows without bound over successive
releases is trending toward becoming the "utils" anti-pattern named in
dimension 11, even before any individual import looks obviously wrong.

## 17. Security and privacy implications

A module boundary that is compiler-enforced doubles as a genuine security
control, not merely an organizational one. Java's Platform Module System
was motivated in significant part by the ability to make internal JDK
classes genuinely inaccessible via reflection, closing an entire class of
attacks that relied on reflectively reaching into classes the classpath
model exposed by accident (Oracle, JEP 261, cited in dimension 9). The
same principle applies to application code. A Module that keeps a
sensitive internal type (a credential-handling class, a raw database
connection wrapper) unexported means code outside that module cannot
reach it even if a developer on another team tries to, which is a
meaningfully stronger guarantee than a code-review policy alone provides.

Where module boundaries follow domain concepts that touch different data
sensitivity levels, for example separating a `billing` module handling
payment details from a `catalog` module that does not, the module
boundary becomes a natural place to enforce that sensitive data does not
leak into a module that has no legitimate reason to see it. A dependency
rule that the `catalog` module may not import anything from `billing`'s
internal payment types is both an architectural constraint and a data
minimization control in the same enforcement mechanism described in
dimension 15.

Convention-only module enforcement carries a corresponding weaker
guarantee here. Without compiler enforcement or an architecture-testing
tool actively run in CI, a module boundary drawn around sensitive data is
advisory only, and a developer unaware of the convention, or working
under deadline pressure, can import the sensitive internal type directly
with no error and no CI failure to catch it. Treat a security-relevant
module boundary in a convention-only language as requiring the
architecture-testing tool from dimension 15, not merely a documented
policy.

## Code examples

### TypeScript

TypeScript's own `namespace` keyword is a module construct in the language
itself, so this example uses it directly rather than simulating separate
files, which keeps the sample runnable as one program.

```typescript
namespace OrderModule {
  export class Money {
    constructor(readonly cents: number, readonly currency: string) {}
  }

  interface Line {
    sku: string;
    amount: Money;
  }

  export class Order {
    private lines: Line[] = [];
    constructor(readonly orderId: string) {}

    addLine(sku: string, amount: Money): void {
      this.lines.push({ sku, amount });
    }

    total(): Money {
      const cents = this.lines.reduce((sum, l) => sum + l.amount.cents, 0);
      const currency = this.lines[0]?.amount.currency ?? "USD";
      return new Money(cents, currency);
    }
  }
}

namespace ShippingModule {
  import Money = OrderModule.Money;

  export class ShippingLabel {
    constructor(readonly orderId: string, readonly cost: Money) {}
  }
}

const order = new OrderModule.Order("ord-1");
order.addLine("sku-1", new OrderModule.Money(500, "USD"));
const total = order.total();
console.log(total);

const label = new ShippingModule.ShippingLabel(order.orderId, total);
console.log(label);
```

Ran with `npx tsc --strict --target es2019 --module commonjs mod.ts
--outDir out` followed by `node out/mod.js`. Compiled and printed
`Money { cents: 500, currency: 'USD' }` then
`ShippingLabel { orderId: 'ord-1', cost: Money { cents: 500, currency: 'USD' } }`
without error. `Line` inside `OrderModule` has no `export`, so it is not
reachable from `ShippingModule`, the same encapsulation TypeScript's
compiler enforces for any module boundary.

### Python

```python
# order/__init__.py, the module's public interface
from .order import Order, Money

__all__ = ["Order", "Money"]

# order/order.py, module internals
from dataclasses import dataclass


@dataclass(frozen=True)
class Money:
    cents: int
    currency: str


class Order:
    def __init__(self, order_id: str):
        self.order_id = order_id
        self._lines: list[tuple[str, Money]] = []

    def add_line(self, sku: str, amount: Money) -> None:
        self._lines.append((sku, amount))

    def total(self) -> Money:
        cents = sum(m.cents for _, m in self._lines)
        currency = self._lines[0][1].currency if self._lines else "USD"
        return Money(cents, currency)


# shipping/shipping.py, a sibling module depending only on order's public names
from order import Money


class ShippingLabel:
    def __init__(self, order_id: str, cost: Money):
        self.order_id = order_id
        self.cost = cost
```

Ran with `python3 -c "from order import Order, Money; o = Order('ord-1');
o.add_line('sku-1', Money(500, 'USD')); print(o.total())"` from the parent
directory containing both `order/` and `shipping/`. Printed
`Money(cents=500, currency='USD')` without error.

### Go

Go's own module boundary is the package, which is a directory, not a single
file, so this sample shows the exported-versus-unexported naming rule
(capitalized identifiers exported, lowercase ones package-private) that a
real `order` package and a real `shipping` package would rely on across
directories.

```go
package main

import "fmt"

type Money struct {
	Cents    int
	Currency string
}

type line struct {
	sku    string
	amount Money
}

type Order struct {
	OrderID string
	lines   []line
}

func NewOrder(orderID string) *Order {
	return &Order{OrderID: orderID}
}

func (o *Order) AddLine(sku string, amount Money) {
	o.lines = append(o.lines, line{sku, amount})
}

func (o *Order) Total() Money {
	total := Money{Currency: "USD"}
	for i, l := range o.lines {
		total.Cents += l.amount.Cents
		if i == 0 {
			total.Currency = l.amount.Currency
		}
	}
	return total
}

type ShippingLabel struct {
	OrderID string
	Cost    Money
}

func main() {
	o := NewOrder("ord-1")
	o.AddLine("sku-1", Money{Cents: 500, Currency: "USD"})
	total := o.Total()
	fmt.Printf("%+v\n", total)
	label := ShippingLabel{OrderID: o.OrderID, Cost: total}
	fmt.Printf("%+v\n", label)
}
```

Ran with `go vet mod.go && go run mod.go`. Printed the total struct
(500 cents, currency USD) and then the label struct (order id ord-1,
carrying that same total) with no error. The cross-package enforcement
this naming rule provides was verified separately with a real two-package
layout, `order/order.go` declaring `package order` with the same `line`
type left unexported, and `shipping/shipping.go` declaring `package
shipping` and importing `order`. Running `go build ./...` after adding a
reference to `order.line` from `shipping.go` rejected the build with the
compiler message naming `line` as not exported by package `order`,
confirming the compiler enforces the package boundary Evans is describing
when he calls a module's public types its exported surface.

### Rust

Rust's `mod` keyword is the module construct itself, with `pub` marking the
exported surface, so this example uses two real submodules declared inline
rather than a simulated multi-file layout, keeping the sample self-contained.

```rust
mod order {
    pub struct Money {
        pub cents: i64,
        pub currency: String,
    }

    struct Line {
        #[allow(dead_code)]
        sku: String,
        amount: Money,
    }

    pub struct Order {
        pub order_id: String,
        lines: Vec<Line>,
    }

    impl Order {
        pub fn new(order_id: &str) -> Self {
            Order { order_id: order_id.to_string(), lines: Vec::new() }
        }

        pub fn add_line(&mut self, sku: &str, amount: Money) {
            self.lines.push(Line { sku: sku.to_string(), amount });
        }

        pub fn total(&self) -> Money {
            let cents = self.lines.iter().map(|l| l.amount.cents).sum();
            let currency = self.lines.first().map(|l| l.amount.currency.clone())
                .unwrap_or_else(|| "USD".to_string());
            Money { cents, currency }
        }
    }
}

mod shipping {
    use super::order::Money;

    pub struct ShippingLabel {
        pub order_id: String,
        pub cost: Money,
    }
}

fn main() {
    let mut o = order::Order::new("ord-1");
    o.add_line("sku-1", order::Money { cents: 500, currency: "USD".to_string() });
    let total = o.total();
    println!("{} {}", total.cents, total.currency);
    let label = shipping::ShippingLabel { order_id: o.order_id.clone(), cost: total };
    println!("{} {}", label.order_id, label.cost.cents);
}
```

Ran with `rustc --edition 2021 mod.rs -o rsout && ./rsout`. Compiled and
printed `500 USD` then `ord-1 500` with no error. `Line` inside `mod
order` has no `pub` marker, so it is private to that module. Widening the
`shipping` module's import to also name `Line` and recompiling confirmed
`rustc` rejects it, reporting the struct as private, the same compile-time
enforcement dimension 9 describes for the language's module system
generally.

## 18. References

1. Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
   Software*, Addison-Wesley, 2003, Chapter 5, "A Model Expressed in
   Software", section "Modules (aka Packages)". Chapter and section
   breakdown confirmed via
   [https://herbertograca.com/2015/09/29/domain-driven-design-by-eric-evans-chap-5-a-model-expressed-in-software/](https://herbertograca.com/2015/09/29/domain-driven-design-by-eric-evans-chap-5-a-model-expressed-in-software/),
   verified 2026-08-02.
2. Vaughn Vernon, *Implementing Domain-Driven Design*, Addison-Wesley,
   2013, Chapter 9, "Modules". Chapter title and Java package to C#
   namespace mapping confirmed via the O'Reilly indexed chapter page,
   [https://www.oreilly.com/library/view/implementing-domain-driven-design/9780133039900/ch09.html](https://www.oreilly.com/library/view/implementing-domain-driven-design/9780133039900/ch09.html),
   verified 2026-08-02. Full chapter text was not directly retrievable
   (403 response), so quotes beyond the title and top-level mapping are
   not claimed.
3. Melvin Conway, "How Do Committees Invent?", Datamation, April 1968,
   [https://www.melconway.com/Home/pdf/committees.pdf](https://www.melconway.com/Home/pdf/committees.pdf),
   verified 2026-08-02.
4. Oracle, JEP 261, "Module System",
   [https://openjdk.org/jeps/261](https://openjdk.org/jeps/261), verified
   2026-08-02.
5. The Rust Programming Language, Chapter 7, "Managing Growing Projects
   with Packages, Crates, and Modules",
   [https://doc.rust-lang.org/book/ch07-00-managing-growing-projects-with-packages-crates-and-modules.html](https://doc.rust-lang.org/book/ch07-00-managing-growing-projects-with-packages-crates-and-modules.html),
   verified 2026-08-02.
6. Shopify Engineering, "Enforce Modularity in Rails Apps Using
   Packwerk",
   [https://shopify.engineering/enforcing-modularity-rails-apps-packwerk](https://shopify.engineering/enforcing-modularity-rails-apps-packwerk),
   verified 2026-08-02.
7. Spring team, "Spring Modulith" reference documentation,
   [https://docs.spring.io/spring-modulith/reference/](https://docs.spring.io/spring-modulith/reference/),
   verified 2026-08-02.
8. Microsoft, "eShop" reference application, GitHub repository,
   [https://github.com/dotnet/eShop](https://github.com/dotnet/eShop),
   verified 2026-08-02.
9. Martin Fowler, "BoundedContext",
   [https://martinfowler.com/bliki/BoundedContext.html](https://martinfowler.com/bliki/BoundedContext.html),
   verified 2026-08-02.
