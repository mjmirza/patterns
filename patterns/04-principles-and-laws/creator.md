---
name: Creator
slug: creator
family: 04-principles-and-laws
category: Principle
aliases: [GRASP Creator, Creator Pattern, Object Creation Responsibility]
first_described: "Craig Larman, 1997, Applying UML and Patterns"
maturity: canonical
related: [factory-method, abstract-factory, builder, single-responsibility-principle, information-expert]
incompatible_with: []
verified: 2026-08-02
---

# Creator

## 1. Name, aliases, and lineage

Creator is one of the nine General Responsibility Assignment Software
Patterns, universally shortened to GRASP, a set of naming conventions Craig
Larman assembled to answer a single recurring question in object-oriented
design, which class should be given which responsibility. Larman first
published the collection under the title *Applying UML and Patterns* in 1997,
and the definition used across the field today, including the phrasing
quoted below, is the one carried forward into the third edition, *Applying
UML and Patterns, An Introduction to Object-Oriented Analysis and Design and
Iterative Development*, Prentice Hall, 2004 (Wikipedia contributors,
"GRASP (object-oriented design)," verified 2026-08-02,
https://en.wikipedia.org/wiki/GRASP_(object-oriented_design)). GRASP itself
is not a single pattern but a name for the whole set, Creator, Information
Expert, Controller, Low Coupling, High Cohesion, Polymorphism, Pure
Fabrication, Indirection, and Protected Variations. Creator and Information
Expert are the two GRASP entries most directly concerned with class
responsibility rather than structural relationships between classes, and they
are frequently taught and cited together because Creator's own selection
criteria lean on the same closeness-of-relationship reasoning that
Information Expert uses to assign a behavior.

There is no alternative name in wide independent use. "Creator pattern" and
"GRASP Creator" both refer to the same entry and are used interchangeably in
teaching material and in code review conversation. Some authors, including
Larman himself in later writing, describe Creator less as a pattern in the
Gang of Four sense, a reusable solution shape with participants and
collaborations, and more as a responsibility assignment guideline, because
its output is a decision about which existing class should own a
constructor call, not a new structural shape introduced into the design.
That distinction matters for how the entry below is read. Creator does not
compete with Factory Method, Abstract Factory, or Builder as an alternative
creational pattern, it is the question those patterns answer once Creator's
own criteria run out.

Creator predates none of the object-creation vocabulary it draws on. The
"contains or aggregates" criterion is a direct restatement of UML aggregation
and composition semantics, which were already standard modeling vocabulary
by the mid 1990s, and the "closely uses" criterion draws on the older
structured-design idea of coupling, the same lineage that underlies the
Single Responsibility Principle (see `single-responsibility-principle.md`,
dimension 1, for the DeMarco and Page-Jones citation trail). Creator's
distinct contribution is not a new idea about coupling or aggregation, it is
turning those existing ideas into a small, ordered checklist a designer can
run against a specific "who creates this object" question during class design,
rather than reasoning about coupling in the abstract.

## 2. Problem and context

Every object-oriented system eventually needs a new object of type A to
come into existence somewhere, and the code that calls the constructor has to
live in some class B. The question sounds trivial until a system has grown
past a handful of classes, at which point it stops being trivial in a
specific, observable way. two designers working on the same domain model will
often disagree about which class should hold the construction call for a
given type, and if the codebase has no shared convention, the decision gets
made inconsistently, class by class, by whichever developer happened to write
that constructor call first. The result is a system where object creation is
scattered unpredictably. sometimes a domain object creates its own children,
sometimes a service class creates them, sometimes a factory class exists for
one type of object but not a structurally identical sibling type, and there
is no way to predict, from the shape of the domain, where a given creation
call will be found.

The context in which Creator applies is specifically object-oriented class
design during the transition from a domain model, the "what exists" picture,
usually drawn as a class diagram with associations and no methods, to a
design model, the "who does what" picture, where responsibilities including
constructor calls get assigned to specific classes. Creator is a
question asked once per class of created object, at design time, not a
runtime mechanism. It has nothing to say about frameworks, dependency
injection containers, or build tooling, it answers a narrower question, given
that some class in this design is going to instantiate A, which class
should that be, so that the resulting design keeps low coupling and high
cohesion rather than accumulating it by accident. Larman frames the guiding
question directly, asking who should be responsible for creating a new
instance of some class (Wikipedia contributors, "GRASP (object-oriented
design)," verified 2026-08-02, same URL as above).

The problem gets sharper in domains with natural containment hierarchies, the
kind UML calls composition. an Order naturally has OrderLine instances, a
Board naturally has Piece instances, a Document naturally has Paragraph
instances. In every one of these pairs, the question of who creates the
child has an answer that most designers arrive at by intuition before they
ever hear the word Creator, and the value of naming the pattern is not that
it produces a surprising answer, it is that it gives a team a shared,
teachable vocabulary for a decision they were already making implicitly and
often inconsistently.

## 3. Forces

This dimension is largely engineering judgement about which force weighs
heaviest in a given design, applied to the sourced criteria in dimension 4.

Coupling versus discoverability. Assigning creation to the containing or
aggregating class, an Order creating its own OrderLine instances, keeps the
reference graph small. the class that already holds a collection of the
created type gains one more responsibility over objects it already touches,
rather than introducing a new class that both the container and some other
code must know about. The competing force is discoverability. a reader
hunting for where an OrderLine gets built has to already know that Order is
the creator, which is easy inside a small aggregate and gets harder as more
types of object need creation logic spread across more container classes.

Cohesion versus proliferation of tiny classes. Following Creator strictly
tends to concentrate creation responsibility inside a small number of
existing domain classes, which keeps those classes cohesive around a
recognizable concept, an Order that both holds and produces its lines is a
coherent unit, at the cost of those classes accumulating more methods over
time. The alternative, giving every creatable type its own dedicated factory
class, keeps each class small and single purpose but multiplies the total
class count and adds a layer of indirection a reader has to traverse before
reaching the object that matters.

Initializing data locality versus construction complexity. When class B
already holds the data needed to initialize A, Creator's third and fourth
criteria below, letting B build A avoids threading that data through an
extra parameter list to a separate creator. The competing pressure appears
the moment construction logic gets nontrivial. validation, multi-step
assembly, or a choice between several concrete subtypes of A. At that
point the same locality that made B the close creator can pull construction
complexity into a class whose primary responsibility was something else,
lowering B's own cohesion. This is the exact seam where Creator hands off to
Factory Method, Abstract Factory, or Builder, treated in dimension 8 and
dimension 13.

Consistency versus context sensitivity. A team that mechanically applies the
rule that the container always creates its contents gets a predictable,
learnable convention, which lowers the cognitive load of onboarding a new
developer into an unfamiliar codebase. The competing force is that Creator's
own criteria are explicitly a short list of alternatives to weigh, not a
single rule, so mechanical application without judgement produces the wrong
answer in cases where, for instance, the class with the initializing data is
not the class that aggregates the result, and the two criteria point at
different classes.

Cost and operability are not meaningfully in tension here in most cases,
because Creator operates at design time on in-process object graphs and does
not by itself introduce network calls, external resources, or deployment
units. The forces above are almost entirely about code organization, not
runtime cost, which is one of the reasons Creator sits comfortably beside
architectural and cloud patterns without conflicting with them (see
dimension 13).

## 4. Applicability and non-applicability

### When to apply Creator

Apply Creator, meaning give class B responsibility for creating instances
of class A, when one or more of Larman's four stated conditions hold:

- Instances of B contain or compositely aggregate instances of A in the UML
  sense, B has a has-a relationship to A where A's lifetime is bound to B's,
  the composition case, or B merely holds a collection of A without owning
  its lifetime, the aggregation case (Wikipedia contributors, "GRASP
  (object-oriented design)," verified 2026-08-02, same URL as dimension 1).
- Instances of B record instances of A, meaning B is the object responsible
  for keeping track of A instances even without full ownership, for example
  a registry or a directory class.
- Instances of B closely use instances of A, a coupling relationship where B
  already depends on A heavily enough in its normal operation that adding
  creation does not introduce a new dependency, only a new responsibility on
  an existing one.
- Instances of B have the initializing data that A needs at construction
  time and would otherwise have to pass that data on to whoever does create
  A, so letting B create A directly avoids an unnecessary data hand off
  (same source as above).

Multiple criteria commonly agree on the same class, which is the easy and
common case. an Order both aggregates OrderLine instances and holds the
initializing data, product identifier and quantity, that a new OrderLine
needs, so Order is Creator by two independent criteria at once, which is a
strong signal rather than a coincidence.

Apply Creator specifically during the domain-to-design transition, when a
class diagram already shows a has-a or uses relationship and the design
question is which side of that relationship should own the construction
call.

### When not to apply Creator, and why

Do not apply Creator when the object being created needs runtime-selected
concrete type based on configuration, environment, or input, rather than a
fixed type known at the call site. this is the signal to reach for Factory
Method or Abstract Factory instead, because Creator's criteria are about
which existing class is the closest natural owner, not about how to select
among several implementations of the same interface. Forcing Creator's
criteria onto this problem produces a class that both plays its original
domain role and contains branching construction logic unrelated to that
role, which is exactly the cohesion loss Creator exists to prevent in the
first place.

Do not apply Creator when construction requires a multi-step assembly process
with optional parts or a fluent interface, such as building a complex
configuration object piece by piece. this is Builder's problem, not
Creator's. Creator answers which class calls the constructor, not how
many steps construction takes.

Do not apply Creator when the created object must be shared as a single
instance across the whole application, or its creation must be intercepted
for cross-cutting concerns such as logging, caching, or access control. these
concerns belong to Singleton, for the shared-instance case, itself a
frequently misused pattern, see the singleton entry in this repository, or to
a Pure Fabrication class introduced specifically to hold the cross-cutting
logic, because folding interception logic into whichever domain class happens
to satisfy Creator's aggregation criterion couples an unrelated concern to
that class.

Do not apply Creator when doing so would violate the Dependency Inversion
Principle by forcing a stable, high-level class to depend on a concrete,
volatile, low-level class purely because the low-level class happens to
aggregate the object being created. Larman's own criteria are heuristics for
the common case, not an override of the broader dependency-direction
concerns that a design must also satisfy, and when they conflict, a Pure
Fabrication class, a GRASP pattern for introducing a class that exists purely
for design convenience rather than because it represents a domain concept,
is the usual escape valve.

Do not apply Creator retroactively to force an existing, working object
graph into the pattern's shape. Creator is a design-time decision tool, and
mechanically refactoring already-working construction code to match Creator's
criteria, with no other benefit in view, is churn without payoff (see
dimension 14 for when the refactor genuinely is warranted).

## 5. Structure

Creator has exactly two participant roles, and no fixed cardinality beyond
that. the same class can play Creator for several different created types at
once, and the same created type can, in principle, have more than one
plausible creator until the criteria are weighed against each other.

**Creator** (B in Larman's formulation). The class assigned responsibility
for instantiating the created class. Typically an existing domain class that
already participates in a has-a, uses, or records relationship with the
created class, and typically the class holding the constructor call, whether
that call sits inside a domain method, a dedicated factory method on the same
class, or, once the relationship outgrows a simple constructor call, a
delegated factory object the Creator class owns.

**Created** (A in Larman's formulation). The class being instantiated. Has
no special obligations under Creator itself beyond being the target of the
construction call, and in the common case the created class does not need to
know who its creator is.

Unlike Factory Method or Abstract Factory, Creator introduces no interface,
no abstract method, and no subclass hierarchy of its own. it is a
responsibility assignment, not a structural pattern with its own class
diagram shape. The structure of Creator, in the diagrammatic sense, is simply
the pre-existing domain relationship, aggregation, composition, recording,
close use, or data ownership, between two classes, annotated with the
decision that one of them now also owns the construction call for the other.

## 6. ASCII structure diagram

```
  Domain relationship that already exists
  (aggregation / composition / close use / data ownership)

       +-------------+                +-------------+
       |   Order     |  1        *    |  OrderLine  |
       | (Creator)   |----------------| (Created)   |
       +-------------+  aggregates    +-------------+
       | + addLine() |                | - product   |
       +-------------+                | - quantity  |
              |                       +-------------+
              | Creator decision:
              | Order already aggregates OrderLine
              | AND already holds the data
              | (product, quantity) that OrderLine
              | needs at construction.
              v
       addLine(product, qty) {
           line = new OrderLine(product, qty)   <- the assigned responsibility
           lines.add(line)
       }

  Contrast: no natural relationship exists
  (Creator's criteria do not point anywhere)

       +----------------+           +-------------------+
       | PaymentService |  ?  needs | ConcretePayment    |
       |  (no has-a,    |---------->| Gateway (Stripe /  |
       |   no data)     |    ???    | Adyen / PayPal)    |
       +----------------+           +-------------------+
              |
              v  Creator has no answer here; hand off to
                 Factory Method / Abstract Factory (dim. 8, 13)
```

## 7. Dynamics

Creator is resolved once, at design time, and the runtime dynamics it
produces are the ordinary dynamics of a domain method that happens to
contain a constructor call, not a distinct runtime protocol. The sequence
below shows the common case where a client triggers a domain operation on
the Creator class, and the Creator class both builds and retains the created
object in the same call, using the running Order and OrderLine example.

```
  Client              Order (Creator)          OrderLine (Created)
    |                       |                          |
    |  addLine(product,qty) |                          |
    |---------------------->|                          |
    |                       |   new OrderLine(         |
    |                       |     product, qty)        |
    |                       |------------------------->|
    |                       |                          | (constructed)
    |                       |<-------------------------|
    |                       |                          |
    |                       | lines.add(line)           |
    |                       |--(internal, no message)-->|
    |                       |                          |
    |<----------------------|                          |
    |  (order now owns      |                          |
    |   the new line)       |                          |
```

Two variations on this dynamic recur often enough to name explicitly.
First, the Creator class may delegate the actual construction call to a
private factory method on itself rather than inlining it in the triggering
method, a purely internal refactor that keeps the external dynamics identical
while improving readability once construction logic grows past a single
line. Second, when the created object needs to be returned to the client
rather than retained by the Creator, for example a Board creating a Move
object to hand back to a caller rather than storing it, the sequence is the
same up to the point of construction, but the final arrow goes from Creator
back to Client carrying the new object, rather than the Creator retaining it
internally.

## 8. Implementation variants

**Inline constructor call inside a domain method.** The most common and
simplest variant, the Creator class calls the constructor directly inside
whichever method already needed the created object, as in the addLine
example above. Appropriate when construction is a single expression with no
branching and no validation beyond what the constructor itself enforces.

**Dedicated factory method on the Creator class.** Once construction grows a
second concern, most commonly input validation or a default-value policy, it
is idiomatic to extract a private or package-visible factory method on the
Creator class itself, for example a private createLine helper taking product
and quantity, so the triggering method stays readable and the construction
logic has one place to live and one place to test. This variant is still
Creator, not Factory Method in the Gang of Four sense. no interface or
subclass is introduced, and the method exists purely as an internal refactor
of the same responsibility.

**Language-idiomatic variants where construction itself is cheap.** In
languages with first-class functions, the Creator's factory method often
collapses into a closure passed to a collection helper rather than an
explicit named method, for example a Kotlin map call building OrderLine
instances from a list of items, where the surrounding class is still, in
Larman's sense, the Creator, but the language's collection idioms make a
dedicated method unnecessary for the trivial case. This does not change which
class satisfies Creator's criteria, only how compactly the assignment is
expressed in code.

**Handoff to a delegated factory once Creator's criteria stop being enough.**
When the Creator class's own criteria hold, it aggregates and holds the
data, but construction also needs to select among several concrete subtypes
of the created class, or needs a multi-step build, the idiomatic move is for
the Creator class to keep the responsibility of deciding that creation
happens, while delegating the actual object-building mechanics to a Factory
Method override, an Abstract Factory it is given, or a Builder it drives.
The Creator class remains the class a reader looks to first, even though it
no longer literally executes the construction step itself. See dimension 13
for how this composition is structured.

**Static factory method as a Creator surrogate when no natural owning class
exists.** When none of Larman's four criteria point clearly at an existing
domain class, a common pragmatic variant is to introduce a Pure Fabrication,
a class that exists purely for design convenience, most often as a static
factory method, for example a static createManager method on a dedicated
factory type or a Go package level constructor function, rather than force
the responsibility onto an unrelated class purely to satisfy the letter of
Creator. This is a documented, accepted escape hatch rather than a
violation, because Larman's own writing treats Pure Fabrication as a
companion pattern for exactly this gap (Wikipedia contributors, "GRASP
(object-oriented design)," verified 2026-08-02, same URL as dimension 1,
Pure Fabrication section).

## 9. Known production uses

Creator is a responsibility-assignment heuristic applied during class design
rather than a library or runtime mechanism, so production use for this
entry means documented use as a taught, applied design method inside real
software curricula, standards bodies, and widely deployed modeling tooling,
which is the closest analogue Creator has to the library and framework
citations used for structural patterns elsewhere in this repository.

- **Craig Larman's own reference implementation, the NextGen Point-of-Sale
  case study**, used throughout *Applying UML and Patterns* (3rd edition,
  Prentice Hall, 2004) to derive the GRASP patterns from a running example.
  The Sale class is assigned responsibility for creating SalesLineItem
  instances specifically because Sale aggregates SalesLineItem and
  because the transaction-time data, product and quantity, needed to
  construct a line item is already flowing through Sale when a line is
  added. this worked example is the source most GRASP teaching material,
  including the Wikipedia summary cited throughout this entry, derives its
  own illustrations from (Wikipedia contributors, "GRASP (object-oriented
  design)," verified 2026-08-02,
  https://en.wikipedia.org/wiki/GRASP_(object-oriented_design)).
- **University object-oriented design and analysis curricula built directly
  on GRASP**, which teach Creator, alongside Information Expert, as the
  standard first-pass method for assigning constructor responsibility during
  the transition from a domain model to a design class diagram. GRASP is
  documented as widely adopted specifically because Larman intended it as a
  learning aid rather than a proprietary methodology, distinguishing it from
  Rational Unified Process's own broader design guidance from the same era
  (Wikipedia contributors, "GRASP (object-oriented design)," verified
  2026-08-02, same URL, background and adoption discussion).
- **The Unified Modeling Language's own aggregation and composition
  semantics**, standardized by the Object Management Group, form the
  structural vocabulary Creator's first criterion depends on directly. the
  phrase about instances containing or compositely aggregating instances is
  a direct reference to UML's AggregationKind values. the OMG's UML
  specification defines composite aggregation as implying that a part
  instance can belong to at most one composite at a time and that the
  composite's lifecycle governs the part's, which is the precise semantic
  Creator's first criterion is built on (Object Management Group, "Unified
  Modeling Language Specification," version 2.5.1, formal/2017-12-05,
  section on Classes/Kernel, AggregationKind,
  https://www.omg.org/spec/UML/2.5.1/, verified 2026-08-02).

## 10. Consequences

### Positive

Applying Creator consistently keeps the class responsible for creating an
object closely coupled to that object already, on purpose, so the design
does not accumulate a second, independent coupling relationship, a factory
class that also has to know the created class's constructor signature, on
top of the domain coupling that was already there. This is the direct
mechanism behind Larman's stated goal of supporting low coupling.

Because the Creator class typically already holds the initializing data the
created object needs, following Creator avoids threading that data through
an extra hop to a separate factory class, which keeps parameter lists
shorter and keeps the data flow visible at the point where a reader is
already looking.

Following Creator's criteria tends to keep the Creator class's overall set of
responsibilities conceptually coherent, because the criteria themselves
select for classes that already have a strong relationship to the created
type, which is Larman's stated support for high cohesion. an Order that
creates its own OrderLine instances reads as one coherent responsibility,
managing a set of order lines, not two unrelated ones.

Creator gives a team a small, memorable, teachable vocabulary for a decision
that is otherwise made ad hoc, class by class, which is a meaningful
consequence in itself. new team members can be told that creation follows
the Creator criteria and apply the same four-question checklist a senior
designer would use, rather than having to absorb an unwritten,
project-specific convention by trial and error.

### Negative

Creator's criteria concentrate creation responsibility inside existing
domain classes, which means those classes accumulate methods over the life
of a project. an Order that both manages its own lines, calculates totals,
applies discounts, and now also creates OrderLine instances can drift
toward a large, multi-responsibility class if creation is only one of many
responsibilities being added to it over time without corresponding
refactoring. Creator on its own does not protect against this drift, it only
answers the initial question of who creates.

Mechanically applying Creator's criteria without weighing them against other
design goals, particularly the Dependency Inversion Principle, can pull a
stable, abstract class into a concrete dependency on a volatile
implementation class purely because it happens to aggregate that
implementation. this is not a flaw in the criteria themselves, which Larman
presents explicitly as one input among several, but a documented failure
mode of applying them as a rigid rule (see dimension 11).

Because Creator produces no distinct structural artifact, there is no
compiler-enforced or IDE-navigable marker that a given constructor call was
placed according to Creator's reasoning versus placed arbitrarily by
whoever wrote the code first. a reader cannot search for Creator the way
they can search for an interface implementing Factory Method. the pattern's
presence is only visible through the reasoning in a design document, a code
comment, or a team's shared convention, all of which decay over time if not
actively maintained.

Creator gives no guidance at all for the runtime-type-selection problem,
which is common enough in real systems that a team relying on Creator alone,
without also knowing when to reach for Factory Method or Abstract Factory,
will eventually hit a wall and either force an unnatural answer out of
Creator's criteria or introduce ad hoc branching logic in whatever class
happened to be closest, which is a worse outcome than either pattern applied
correctly.

## 11. Failure modes and misuse

This dimension is drawn from practitioner experience applying the pattern,
not from a single citable source, and the symptom, cause, and fix format
below follows the repository's stated convention for judgement-based
dimensions.

**Symptom.** A domain class that started small and focused has grown a long
list of create methods for several unrelated types of created object, and
code review comments start describing it as a god class or a junk drawer.
**Cause.** Creator's criteria were applied correctly for each individual
created type in isolation, one decision at a time, but nobody stepped back
to notice that the same class was accumulating creation responsibility for
several structurally unrelated object families, each of which happened to
pass one of Larman's four tests independently.
**Fix.** Group the related creation methods and extract a Pure Fabrication
class per family once a class's creation responsibilities stop reading as
one coherent concept, keeping each extracted class small and re-running
Creator's criteria against the new, narrower class if a further split is
needed.

**Symptom.** A high-level, otherwise stable class, a domain aggregate root
or a service interface, has picked up a hard compile-time dependency on a
volatile, low-level implementation class, and every time that low-level
class's constructor signature changes, the stable class has to be
recompiled and often retested even though its own logic did not change.
**Cause.** The stable class satisfied one of Creator's criteria, most often
holding the initializing data, against a concrete, frequently-changing
class, and the criteria were applied without weighing the resulting
dependency direction.
**Fix.** Introduce a Pure Fabrication factory, or delegate to Abstract
Factory, so the stable class depends only on an interface or a factory
abstraction it owns, while the volatile concrete class and its constructor
live behind that boundary, restoring the Dependency Inversion direction
Creator's raw criteria did not account for.

**Symptom.** A constructor call for a given type is found in three or four
different places across the codebase, none of them obviously wrong on their
own, and different developers give different answers when asked where new
instances of this type should be created.
**Cause.** No shared team convention around Creator was ever agreed on, so
each developer independently discovered a plausible creator class for a
given need and used it, and each discovery was locally reasonable while the
aggregate result is scattered and unpredictable.
**Fix.** Run Creator's four criteria once, deliberately, as a team decision,
against the type in question, document the chosen creator, even a one-line
code comment or an architecture decision record entry is enough, and
refactor the other call sites to route through it, distinguishing genuine
alternate valid creators, a repository layer reconstituting an object from
storage is a legitimately different case from a domain method constructing
a fresh one, from accidental duplication.

**Symptom.** A test for a domain method that also happens to construct a
related object is hard to isolate, mocking or stubbing the created type
requires reaching into the Creator class's internals, or the test ends up
exercising both the Creator's own logic and the created object's constructor
logic at once, muddying failure diagnosis.
**Cause.** Construction logic that started as Larman's simple, single
Creator's criteria case grew branching or validation over time, without
ever being extracted into its own testable factory method, so the inline
constructor call is now entangled with unrelated logic in the same method.
**Fix.** Extract the construction step into its own named method on the
Creator class, the dedicated factory method variant from dimension 8, so
it can be unit tested independently of the surrounding domain logic, even
though the responsibility for calling it remains correctly assigned to the
Creator class.

## 12. Trade-off matrix

Creator is compared here against its most commonly confused alternatives,
Factory Method and Abstract Factory, which solve a related but distinct
problem, and against an ad hoc no-explicit-rule baseline, which is the
real-world default Creator is displacing.

| Force | Creator | Factory Method | Abstract Factory | No explicit rule (ad hoc) |
|---|---|---|---|---|
| Decision it answers | Which existing class should call the constructor | How a class defers instantiation to subclasses so callers do not depend on a concrete type | How to produce families of related objects without specifying their concrete classes | none, decided per call site by whoever writes the code |
| Coupling direction | Keeps creation coupled to an already-related class, on purpose | Decouples the calling code from the concrete created type via an interface | Decouples the calling code from an entire family of concrete types | Unpredictable, varies call site to call site |
| Handles runtime type selection | No, assumes the concrete type is already known | Yes, that is its central purpose | Yes, across a whole family of types | No, whatever the developer happened to write |
| Introduces a new class or interface | No, only reassigns responsibility on existing classes | Yes, typically an interface or abstract creator method | Yes, typically an interface for the whole factory | No |
| Cost when construction is trivial | Low, often a single line inside an existing method | Higher, adds an interface and at minimum one concrete class for one type | Highest of the three, adds a factory interface plus a concrete factory per family | Low up front, high later as inconsistency accumulates |
| Cost when construction later grows complex | Requires a handoff to one of the other patterns (dimension 8, 13) | Scales naturally, new concrete creators can be added without touching callers | Scales naturally across a whole product family | Does not scale, complexity accumulates unmanaged in whichever class first needed it |
| Discoverability for a new team member | Requires knowing or being told the criteria and the domain relationships | High, the interface is a discoverable, navigable structural marker | High, same as Factory Method | Lowest, no convention to learn |

## 13. Related and incompatible patterns

**Factory Method.** The natural successor once Creator's criteria stop
producing a clean answer, specifically the runtime-type-selection case
described in dimension 4's non-applicability list. A common composition is
for the class Creator identifies to remain the caller of construction, while
delegating the actual choice of concrete type to a Factory Method it defines
or overrides, so Creator answers who initiates creation and Factory Method
answers which concrete type gets built.

**Abstract Factory.** The same handoff as Factory Method, scaled to a whole
family of related created types that must be produced consistently together,
for example a UI toolkit that must produce a matched set of button, menu,
and dialog implementations for a given platform. Creator's criteria can
still identify which class in the design should hold the reference to the
Abstract Factory and trigger its use, even though the factory itself, not
the Creator-selected class, performs the actual instantiation.

**Builder.** Applies when the created object needs multi-step, optionally
staged construction rather than a single constructor call. Creator's
criteria can still identify which class should own and drive the Builder,
most often the same class that would otherwise have called the constructor
directly, while the Builder itself absorbs the step-by-step assembly logic.

**Single Responsibility Principle.** Directly supports and is supported by
Creator. Creator's criteria are, in effect, a specific application of asking
whether a responsibility belongs here to the narrow question of object
creation, and a class that has correctly earned Creator status for a given
type is, by definition, gaining a responsibility that is closely related to
its existing reason to change, which is precisely SRP's own test (see
`single-responsibility-principle.md` for the general principle this
specializes).

**Information Expert.** The GRASP sibling pattern most frequently invoked
alongside Creator, because both answer which class should do this by
looking for the class already closest to the relevant data or relationship,
Information Expert for behavior generally, Creator specifically for
construction. The two frequently point at the same class for the same
reason, which is part of why they are taught as a pair.

**Pure Fabrication.** The documented escape valve when none of Creator's
four criteria clearly apply, or when applying them would violate a stronger
design goal such as dependency direction (dimension 4, dimension 11). Pure
Fabrication introduces a class that exists purely for design convenience
rather than to represent a domain concept, and a static or dedicated factory
class is the most common concrete shape that escape valve takes.

**Singleton.** Not incompatible, but a distinct and separate concern.
Creator answers who creates an object, Singleton answers whether more than
one instance of a type may exist at all. A class can be correctly assigned
Creator responsibility for a type that also happens to be a Singleton, though
the combination is worth naming explicitly in review because Singleton
carries its own, separately documented set of failure modes (see the
singleton entry in this repository).

There are no patterns in wide use that are directly incompatible with
Creator in the sense of two named patterns actively contradicting each
other's structural requirements. the closest thing to an incompatibility is
the Dependency Inversion Principle conflict already covered in dimension 4
and dimension 11, which is a conflict between Creator's raw criteria and a
separate design principle, not between Creator and another named creational
pattern.

## 14. Refactoring path in and out

### Introducing Creator into code that lacks it

Start from the symptom, not the pattern name. object creation for a given
type is scattered across multiple call sites with no discernible convention,
or a class unrelated to a created type's natural aggregation and data
ownership is the one currently constructing it. Locate every constructor
call site for the type in question, typically via an IDE find-usages search
on the constructor or a text search for the type name preceded by a new
keyword. Evaluate Larman's four criteria against the candidate creator
classes present in the domain, and choose the class that satisfies the most
criteria, or the strongest single criterion, aggregation and data ownership
together are usually the strongest combined signal. Move the construction
logic into a method on the chosen Creator class, initially as a direct
extraction of whatever logic already existed at the strongest call site,
then update the other call sites to go through the new method rather than
calling the constructor directly. Where the type's constructor was
previously public and called from many unrelated places, consider narrowing
its visibility once all call sites have been routed through the Creator
class, so the compiler or the language's own access control begins enforcing
the convention rather than relying on team discipline alone. This last step
is optional and depends on the language's visibility model, it is the
mechanism, when available, that turns a documented convention into one that
cannot silently regress.

### Removing Creator once it stops earning its place

The signal that Creator has stopped earning its place is exactly the failure
mode described first in dimension 11, a Creator class has accumulated
creation responsibility for several unrelated object families and no longer
reads as cohesive. The refactor out is Extract Class, applied specifically
to the creation-related methods. group the related create methods that still
belong together conceptually, move that group into a new Pure Fabrication
class, and update the original Creator class's remaining callers to go
through the new class instead. This is not a reversal of the original
decision to apply Creator, the newly extracted class typically becomes the
Creator for its narrower family, re-satisfying the same criteria at a
smaller, more cohesive scope, rather than abandoning the pattern altogether.
A genuine full removal, going back to no explicit convention, is rarely
warranted and is not treated here as a normal refactoring outcome, because
the ad hoc baseline is precisely the state Creator exists to improve on
(dimension 12).

## 15. Testing and verification

This dimension is practice-derived judgement rather than sourced claim.

Because Creator assigns a responsibility rather than introducing a new
interface, testing a Creator-satisfying class is, in the simple case,
indistinguishable from testing any other method on that class. call the
method that triggers construction, assert on the resulting created object's
state, and assert on any side effect on the Creator class itself, for
example that the created object was correctly added to the Creator's
internal collection. No special test double is required for the common
case where construction is a direct, unbranching constructor call, because
there is nothing to substitute. the created object's own constructor is
cheap and deterministic by assumption.

Testing gets harder, in exactly the way described in dimension 11's fourth
failure mode, once construction logic inside the Creator class grows
branching, validation, or a dependency on an external resource, a database
lookup for a default value, for example. At that point the recommended
verification approach is the extraction described in dimension 8's
dedicated factory method variant, pull the construction logic into its own
named method, and test that method directly with a table of input cases,
independently of the domain logic that triggers it. If the extracted
construction method depends on an external collaborator, that collaborator
becomes the natural seam for a test double, a stub or a fake, while the
Creator class's own responsibility, deciding when construction happens,
remains tested through its normal public interface rather than through the
construction internals.

Where a team has adopted Creator as an explicit convention, a lightweight
architectural test, checking that a given type's constructor is only invoked
from within its designated Creator class or package, using whichever
architecture-testing tool the codebase's language ecosystem provides, for
example ArchUnit-style rules in JVM ecosystems, or a custom lint rule that
searches for disallowed constructor call sites, is a practical way to make
an otherwise undocumented, decaying convention self-enforcing over time,
closing the gap named in dimension 10's negative consequences.

## 16. Observability signals

This dimension is practice-derived judgement, not sourced claim, and it is
worth stating plainly that Creator itself produces no distinct runtime
signal to observe, because it is resolved entirely at design and compile
time. there is no Creator event to trace or log in a running system, and a
reader should not expect one.

What can be observed indirectly is the health of the design decision over
time, through code-level signals rather than runtime telemetry. A rising
method count on a class originally assigned Creator responsibility, tracked
by whatever static-analysis or code-metrics tool a project already uses, is
the practical proxy for the junk drawer failure mode in dimension 11, and a
threshold-based alert on that metric, for example flagging a class once its
method count or its count of distinct create methods crosses a team-chosen
number, is a reasonable, low-cost way to surface the drift before it
becomes a large refactor. Similarly, a growing count of distinct
constructor call sites for a type that was supposed to have a single Creator
is directly observable via the same find-usages search described in
dimension 14, and treating that search as a periodic architectural review
step, rather than only running it during an initial introduction, is the
practical way to keep the convention from silently regressing as new
developers join a project and are not aware of the original decision.

## 17. Security and privacy implications

Creator itself, being purely a design-time decision about which existing
class calls a constructor, is silent on security and privacy in the direct
sense. it introduces no new attack surface, no new data flow, and no new
trust boundary on its own. The only place a security implication genuinely
attaches is a specific composition already named as a failure mode in
dimension 11, when a class is judged Creator by the criterion of holding
the initializing data, and that initializing data includes sensitive
fields, personal data or credentials or anything else that carries a
privacy or security classification, that class is, by Creator's own
reasoning, an appropriate place to construct the object, but it is also, as
a direct consequence, a place where sensitive data is present in memory and
in the call stack at construction time. This is not a flaw introduced by
Creator, it is a restatement of an unavoidable fact, sensitive data has to be
present somewhere at the point an object holding it is constructed, and the
practical implication for a design review is simply to confirm that the
class Creator's criteria select for sensitive-data-bearing types is a class
already within the system's existing trust boundary and audit surface, not a
class chosen purely for aggregation convenience without that check.

## 18. References

1. Wikipedia contributors, "GRASP (object-oriented design)," Wikipedia, The
   Free Encyclopedia, verified 2026-08-02,
   https://en.wikipedia.org/wiki/GRASP_(object-oriented_design)
2. Craig Larman, *Applying UML and Patterns, An Introduction to
   Object-Oriented Analysis and Design and Iterative Development*, 3rd
   edition, Prentice Hall, 2004. Source of the Creator pattern's four
   selection criteria and the NextGen Point-of-Sale worked example, Sale
   creates SalesLineItem, cited via the Wikipedia summary at reference 1,
   verified 2026-08-02.
3. Object Management Group, "Unified Modeling Language Specification,"
   version 2.5.1, formal/2017-12-05, section on Classes/Kernel,
   AggregationKind, https://www.omg.org/spec/UML/2.5.1/, verified
   2026-08-02. Source of the composite aggregation semantics Creator's first
   selection criterion depends on.
4. Wikipedia contributors, "Single-responsibility principle," Wikipedia, The
   Free Encyclopedia, verified 2026-08-02,
   https://en.wikipedia.org/wiki/Single-responsibility_principle. Cited for
   the shared coupling and cohesion lineage discussed in dimension 1 and
   dimension 13, and cross-referenced against this repository's own
   `single-responsibility-principle.md` entry.

## Code examples

The examples below implement the same design decision across four
languages, an Order class satisfies Creator for OrderLine because it
aggregates OrderLine instances and already holds the initializing data,
product name and quantity, each OrderLine needs. Every example was compiled
or run locally, results are stated after each block. Java and C# are
omitted for this entry. Java was not available on the machine used to
verify these examples, no Java runtime was installed, and C# was not
installed either, both are noted here rather than silently implied as
compiled.

### TypeScript

```typescript
class OrderLine {
  constructor(
    public readonly product: string,
    public readonly quantity: number
  ) {}
}

class Order {
  private lines: OrderLine[] = [];

  // Order satisfies Creator, it aggregates OrderLine and already
  // holds the data (product, quantity) a new OrderLine needs.
  addLine(product: string, quantity: number): OrderLine {
    const line = new OrderLine(product, quantity);
    this.lines.push(line);
    return line;
  }

  totalItems(): number {
    return this.lines.reduce((sum, l) => sum + l.quantity, 0);
  }
}

const order = new Order();
order.addLine("widget", 3);
order.addLine("gadget", 2);
console.log(order.totalItems());
```

Compiled with `npx tsc --strict order.ts` (no errors) and run with
`node order.js`, output `5`.

### Python

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class OrderLine:
    product: str
    quantity: int


class Order:
    def __init__(self):
        self._lines: list[OrderLine] = []

    # Order satisfies Creator, it aggregates OrderLine and already
    # holds the data (product, quantity) a new OrderLine needs.
    def add_line(self, product: str, quantity: int) -> OrderLine:
        line = OrderLine(product, quantity)
        self._lines.append(line)
        return line

    def total_items(self) -> int:
        return sum(line.quantity for line in self._lines)


order = Order()
order.add_line("widget", 3)
order.add_line("gadget", 2)
print(order.total_items())
```

Run with `python3 order.py`, output `5`.

### Go

```go
package main

import "fmt"

type OrderLine struct {
	Product  string
	Quantity int
}

type Order struct {
	lines []OrderLine
}

// Order satisfies Creator, it aggregates OrderLine and already
// holds the data (product, quantity) a new OrderLine needs.
func (o *Order) AddLine(product string, quantity int) OrderLine {
	line := OrderLine{Product: product, Quantity: quantity}
	o.lines = append(o.lines, line)
	return line
}

func (o *Order) TotalItems() int {
	total := 0
	for _, l := range o.lines {
		total += l.Quantity
	}
	return total
}

func main() {
	order := &Order{}
	order.AddLine("widget", 3)
	order.AddLine("gadget", 2)
	fmt.Println(order.TotalItems())
}
```

Run with `go run order.go`, output `5`.

### Rust

```rust
struct OrderLine {
    product: String,
    quantity: u32,
}

struct Order {
    lines: Vec<OrderLine>,
}

impl Order {
    fn new() -> Self {
        Order { lines: Vec::new() }
    }

    // Order satisfies Creator, it aggregates OrderLine and already
    // holds the data (product, quantity) a new OrderLine needs.
    fn add_line(&mut self, product: &str, quantity: u32) {
        let line = OrderLine {
            product: product.to_string(),
            quantity,
        };
        self.lines.push(line);
    }

    fn total_items(&self) -> u32 {
        self.lines.iter().map(|l| l.quantity).sum()
    }
}

fn main() {
    let mut order = Order::new();
    order.add_line("widget", 3);
    order.add_line("gadget", 2);
    println!("{}", order.total_items());
}
```

Compiled with `rustc order.rs` and run as `./order`, output `5`.
