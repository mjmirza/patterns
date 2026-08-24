---
name: Single Responsibility Principle
slug: single-responsibility-principle
family: 04-principles-and-laws
category: Principle
aliases: [SRP, One Reason to Change]
first_described: "Robert C. Martin, early 2000s, as part of the Principles of Object Oriented Design"
maturity: canonical
related: [interface-segregation-principle, open-closed-principle, dependency-inversion-principle, separation-of-concerns, cohesion-and-coupling]
incompatible_with: []
verified: 2026-08-02
---

# Single Responsibility Principle

## 1. Name, aliases, and lineage

The canonical name is the Single Responsibility Principle, almost always
abbreviated SRP, the first of the five principles Robert C. Martin grouped
under the acronym SOLID. Martin's own formulation, quoted directly, is "a
class should have only one reason to change" (Wikipedia contributors,
"Single-responsibility principle," verified 2026-08-02,
https://en.wikipedia.org/wiki/Single-responsibility_principle). In later
writing Martin restated the same idea from the module side rather than the
class side. gather together the things that change for the same reasons,
separate the things that change for different reasons (same source). The two
statements describe one principle, applied first to a class and later to any
unit of deployment, a package, a service, or a file.

There is no widely used alternative name. "One Reason to Change" functions as
a shorthand people say aloud in code review rather than a distinct alias
found in a separate publication.

The lineage matters more than the name, because SRP did not appear from
nothing. Martin is explicit that he built the principle on top of an older
idea from structured design, cohesion. The relevant citation trail runs
through Tom DeMarco, *Structured Analysis and System Specification*, Yourdon
Press, 1979, and Meilir Page-Jones, *The Practical Guide to Structured
Systems Design*, Yourdon Press, 1988, both of which describe cohesion as a
property of a module and rank cohesion types from weak (coincidental) to
strong (functional) (Wikipedia contributors, "Single-responsibility
principle," verified 2026-08-02, same URL as above, section attributing the
concept to DeMarco and Page-Jones). SRP is best read as cohesion re-expressed
for object-oriented design and given a memorable one-line test, rather than
as an independently invented idea. Anyone who has taught structured design
before object orientation will recognize SRP immediately, because it is the
same claim wearing a different vocabulary.

A second, distinct lineage runs through Unix. Doug McIlroy's formulation,
"write programs that do one thing and do it well," recorded in Peter H.
Salus, *A Quarter Century of Unix*, Addison-Wesley, 1994, and widely quoted
as part of the Unix philosophy (Wikipedia contributors, "Unix philosophy,"
verified 2026-08-02, https://en.wikipedia.org/wiki/Unix_philosophy), predates
Martin's formulation by roughly two decades and applies the same idea at the
level of a whole program rather than a class. The two lineages, cohesion in
structured design and the Unix one-thing-well ethic, converge on SRP from
different directions, which is one reason the principle reads as obvious once
stated and is nonetheless violated constantly in practice. obviousness in
retrospect is not the same as ease of application in the moment a class is
first written.

## 2. Problem and context

The problem SRP names is a specific, recognizable shape of decay. A class
starts small and does one job well. Over months, unrelated work keeps
landing on it because it is already the place where a related concept lives,
and each addition is individually reasonable. An `Invoice` class that
started by holding invoice data grows a `calculateTotal` method, which is
squarely its job. Then someone needs to print the invoice, and the easiest
place to add that is a `printInvoice` method on the same class, because the
class already has all the fields the printer needs. Then someone needs to
persist the invoice to a database, and again, the class already has the
fields, so `save` lands there too. None of these additions looks wrong on
its own. The class compiles, the tests that exist still pass, and the change
is small.

The consequence shows up later, and it shows up as coupling that nobody
designed. A change to how invoices are printed, a new report format
requested by finance, now requires touching, recompiling, and redeploying
the same class that also owns billing arithmetic and persistence. In a
statically typed language a change to the printing method forces
recompilation of every module that depends on `Invoice`, including modules
that only ever cared about the arithmetic. A test for the total calculation
now has to run against a class whose constructor may also pull in a database
connection, because that dependency lives on the same type. Two developers
working on unrelated concerns, one on tax calculation and one on the PDF
layout, are editing the same file and generate a merge conflict that has
nothing to do with either of their actual changes.

This is a problem of accumulation, not of one bad decision. The context
where it arises is any codebase that grows over time under real deadline
pressure, where the path of least resistance is always to add a method to an
existing, already-imported type rather than to introduce a new one. SRP
exists to name the smell early, at the point where the second unrelated
method is about to land, rather than after the fifth, when the class has
become what practitioners call a god object and the separation is
expensive.

## 3. Forces

- **Cohesion versus convenience.** Favoured toward cohesion. Adding a method
  to an existing class is always the path of least resistance, because the
  fields and helpers are already in scope. SRP asks the author to resist that
  convenience when the new method answers to a different actor or a
  different reason to change than the existing ones.
- **Class count versus change isolation.** Sacrificed on class count.
  Following SRP strictly multiplies the number of small classes. In exchange,
  a change to one axis of behaviour, printing, persistence, arithmetic,
  touches exactly one class, so the blast radius of any single change
  shrinks in proportion to the split.
- **Discoverability versus focus.** A single large class is easy to find,
  because everything about an invoice lives in one file. Splitting it means a
  reader has to know, or discover, that printing lives in
  `InvoiceFormatter` and persistence lives in `InvoiceRepository`. SRP trades
  the convenience of one search location for the benefit that each file, once
  found, is small enough to read completely and reason about in isolation.
- **Compilation and build cost, in compiled languages.** In C++, Java, and
  Rust, a class that groups unrelated responsibilities becomes a
  recompilation hazard, since every consumer of any one responsibility
  depends on the whole type and rebuilds when any part of it changes. SRP
  favours faster incremental builds at the cost of more translation units.
- **Testability versus setup cost.** A class with one responsibility usually
  needs a narrower set of test doubles, because it depends on fewer
  collaborators. A class with several responsibilities needs a database
  connection to test the arithmetic, because the constructor also wires up
  persistence. SRP favours cheap, focused unit tests over one large test
  that exercises everything at once.
- **Team ownership versus a single point of contact.** In an organization
  where Conway's Law is operating, per Melvin Conway's 1968 observation that
  system structure mirrors communication structure, a class that mixes
  billing logic and PDF rendering forces the billing team and the reporting
  team to share ownership of one file. SRP, applied consistently, lets
  responsibility boundaries in code mirror team boundaries, which reduces
  cross-team coordination cost at the price of more cross-class wiring for
  whichever team assembles the pieces.
- **Premature splitting versus late splitting.** SRP is silent on timing, and
  applying it too early, before a second reason to change has actually
  appeared, produces speculative classes nobody asked for. The forces above
  favour splitting once a second real actor is visible, not in anticipation
  of one.

## 4. Applicability and non-applicability

Apply SRP when the following hold.

- A class already has, or is about to gain, a second method that answers to
  a different stakeholder or a different business rule than the methods it
  already has. The `Invoice` example above is the canonical shape. billing
  answers to finance, printing answers to whoever defines report layout, and
  persistence answers to whoever owns the storage schema.
- Two changes that have historically landed on the same class, in the
  version control history, came from unrelated tickets or unrelated teams.
  Git blame and commit history are a legitimate source of evidence for
  whether a class actually has more than one reason to change, not just a
  theoretical worry.
- A class needs to be tested in isolation and currently cannot be, because
  its constructor pulls in a dependency (a database, a network client, a
  filesystem) that belongs to a responsibility the test does not care about.
- A class is a natural seam for a team boundary, and keeping the
  responsibilities together would force two teams to coordinate changes to
  one file.
- A class is growing past the point where a reader can hold its whole
  behaviour in mind at once, and the growth traces to unrelated concerns
  rather than to genuine complexity within one concern.

Do NOT apply SRP in these cases, and the reason is the part most
introductions to SRP skip.

- **The class is small and every method genuinely serves one actor.** A
  `Point` class with `x`, `y`, `distanceTo`, and `translate` is not a
  violation waiting to happen. All four members exist to answer the same
  question, where is this point and how does it relate to another point.
  Splitting `distanceTo` into a separate `PointDistanceCalculator` class adds
  indirection with no corresponding change-isolation benefit, because there
  is only one reason this class would ever change. the definition of a
  point.
- **The responsibilities have never actually diverged and there is no
  organizational reason to expect they will.** A `Money` value type that
  holds an amount and a currency and knows how to add two amounts of the
  same currency is cohesive by construction. Splitting arithmetic from
  storage here produces two anemic classes that must always be used
  together, which is the opposite of the isolation SRP is meant to buy.
- **Anemic domain models produced by over-application.** Splitting every
  class down to a bag of fields plus a separate service class per verb,
  `CreateInvoiceService`, `UpdateInvoiceService`,
  `CalculateInvoiceTotalService`, one class per method, is SRP taken past
  its useful range. Martin Fowler's description of the Anemic Domain Model,
  *PoEAA*, Addison-Wesley, 2002, and his 2003 web article of the same title,
  names this exact failure mode. business logic is pulled out of the domain
  object into service classes until the domain object itself carries no
  behaviour, which trades one problem, coupling, for another, a procedural
  design wearing object syntax (Martin Fowler, "AnemicDomainModel,"
  martinfowler.com, verified 2026-08-02,
  https://martinfowler.com/bliki/AnemicDomainModel.html).
- **The class is a Data Transfer Object or a pure value object with no
  behaviour beyond structural equality.** A DTO's one job is carrying data
  across a boundary. asking whether it has a single responsibility is
  usually a category error, because it has no responsibility beyond being
  data.
- **The "actor" analysis has not been done, and the split is guessed from
  method count alone.** Two methods on a class is not a violation signal by
  itself. The signal is two methods that answer to two different sources of
  change. Splitting on line count or method count without identifying the
  actors produces arbitrary boundaries that do not track real change
  pressure.
- **The system is a short-lived script or a one-off migration.** A script
  that will run once and be deleted gains nothing from responsibility
  isolation, because there is no second future change to isolate against.

## 5. Structure

SRP is not a structural pattern with named participants the way a design
pattern is, since it is a constraint on how responsibility is distributed
across whatever types already exist. It is still useful to name the roles
that appear whenever SRP is applied concretely.

- **The original class.** The type that, before refactoring, holds more than
  one responsibility. In the recurring example this is `Invoice`, which
  starts by holding billing data and arithmetic and then accretes printing
  and persistence.
- **The actor, or source of change.** Not a class in the code, but the
  person, role, or subsystem whose requirements drive one responsibility.
  Martin's later refinement of SRP, in *Clean Architecture. A Craftsman's
  Guide to Software Structure and Design*, Prentice Hall, 2017, chapter 7,
  reframes "reason to change" as "an actor," a single person or tightly
  coupled group who would ask for the change, precisely because "reason to
  change" alone was too vague, and two unrelated reasons can accidentally
  look like one if they are not tied to a concrete requester.
- **The extracted responsibility class.** A new type that owns exactly one
  of the responsibilities the original class used to hold, and is named for
  what it does rather than for the data it touches. In the example this is
  `InvoiceCalculator`, `InvoicePrinter`, and `InvoiceRepository`.
- **The coordinator or composition point.** Some type, often at the
  application's edge, that holds references to the extracted classes and
  wires them together for a use case. This is not itself part of SRP, it is
  the ordinary cost of having split a class. something has to reassemble the
  pieces when a use case needs all of them together.
- **The shared data structure, when one exists.** When the extracted classes
  all need to read the same underlying data, a plain value object, or a
  passed reference to the original entity, plays this role. Its presence is
  what keeps the split from also duplicating state.

## 6. ASCII structure diagram

```
Before

+---------------------------------------+
| Invoice                               |
| fields: lines, tax                    |
| + total(): Money      <- finance team |
| + print(): String     <- layout team  |
| + save(db): void      <- storage team |
+---------------------------------------+

Three unrelated teams each have a reason to change this
one class.


After

+----------------------------------------------+
| Invoice                                      |
| data only, no behaviour beyond its own shape |
+----------------------------------------------+
        ^                ^                ^
        | reads          | reads          | reads
+-------------------+  +----------------+  +-------------------+
| InvoiceCalculator |  | InvoicePrinter |  | InvoiceRepository |
| + total(inv)      |  | + render(inv)  |  | + save(inv)       |
+-------------------+  +----------------+  +-------------------+
      answers to        answers to        answers to
      finance team       layout team       storage team

Each box has exactly one actor who would ask it to change.
A tax law change touches only InvoiceCalculator, a PDF
layout change touches only InvoicePrinter, a storage
schema change touches only InvoiceRepository. No single
edit crosses two boxes.
```

## 7. Dynamics

The interesting dynamics of SRP are not runtime call sequences, since the
principle constrains authorship, not execution order. The dynamics worth
showing are how a change propagates before and after the split, and how a
coordinator assembles the split pieces for a real use case.

```
Before the split, a tax law change:

  Change request: "update VAT calculation"
        |
        v
  Edit Invoice.total()   <-- same file also holds print() and save()
        |
        v
  Full class recompiles (statically typed languages)
        |
        v
  Every module that imports Invoice for ANY reason
  is a candidate for re-verification, including modules
  that only ever call print() or save()
        |
        v
  Test suite for Invoice must stand up a DB connection
  (because save() needs one) just to test total()


After the split, the same tax law change:

  Change request: "update VAT calculation"
        |
        v
  Edit InvoiceCalculator.total()  <-- InvoicePrinter and
        |                             InvoiceRepository untouched
        v
  Only InvoiceCalculator recompiles
        |
        v
  Only modules that call InvoiceCalculator are candidates
  for re-verification
        |
        v
  Unit test for total() constructs InvoiceCalculator alone,
  no database, no printer

  ---

  Use case assembly, at the composition point:

  Client
    |
    |-- new coordinator: IssueInvoiceUseCase(
    |        calculator = InvoiceCalculator(),
    |        printer    = InvoicePrinter(),
    |        repository = InvoiceRepository(db))
    |
    |-- issueInvoiceUseCase.run(invoiceData)
    |        |
    |        |-- calculator.total(invoiceData)  -> Money
    |        |-- printer.render(invoiceData, total) -> String (pdf/text)
    |        |-- repository.save(invoiceData)
    |        v
    |     returns confirmation
    v
  Client receives result
```

## 8. Implementation variants

**Method-per-actor extraction, within one language's class construct.** The
most direct implementation. Each responsibility becomes its own class,
struct, or in Go a type with its own methods, holding only the state that
responsibility needs. This is the shape shown in the diagrams above and in
the code examples.

**Interface plus implementation, so the actor's dependency is on a
contract.** Rather than the coordinator depending on a concrete
`InvoiceRepository`, it depends on an interface such as `InvoiceStore` that
`InvoiceRepository` implements. This variant combines SRP with the
Dependency Inversion Principle, because the class that has a single
responsibility for persistence is now substitutable by a test double that
also has a single responsibility, keeping the data in memory. This is the
variant used in the Go example below, since Go's implicit interface
satisfaction makes it close to free.

**Free function or module-level function, in languages that do not require
a class.** In Python, Go, and JavaScript a "responsibility" can be a module
of free functions rather than a class with methods, and SRP applies the same
way to the module. a module should have one reason to change. `tax.py` that
only computes VAT is following SRP just as much as a `TaxCalculator` class
would.

**Composition over a shared mutable entity.** Extracted classes each take
the entity as a parameter to their one method, rather than holding a
reference to it as a field. `InvoicePrinter.render(invoice)` rather than
`InvoicePrinter(invoice).render()`. This keeps the extracted class stateless
and reusable across many entities, and is the more common shape in practice
because it avoids the extracted class becoming a second home for the
original entity's state.

**Command or handler object per operation, in CQRS-flavoured codebases.**
Command handler frameworks push SRP to its extreme by giving every write
operation its own handler class, `IssueInvoiceHandler`,
`VoidInvoiceHandler`, each with a single `handle` method. This is a genuine
implementation of SRP at the use-case level rather than the class level, and
it composes with the Command pattern, see dimension 13.

**Facade over the split pieces, when callers should not see the split.**
When external callers genuinely need one entry point, a facade wraps the
extracted classes behind a single method, `InvoiceService.issue(data)`,
while the facade itself is thin, delegating rather than doing the work. The
facade's own single responsibility is orchestration, and it must resist
growing real logic of its own, or the god object reappears one layer up.

**Language-specific note.** In C, where there is no class construct at all,
SRP shows up as file- and struct-level discipline. a `.c` file owning one
concern and a `struct` that a second file is not permitted to reach into
directly, enforced by convention and by keeping the struct's definition out
of the shared header (an opaque pointer). The principle survives the
absence of objects because it was never really about objects, it is about
where the boundary between "one reason to change" units is drawn.

## 9. Known production uses

**`java.nio.file.spi.FileSystemProvider`, the JDK's pluggable filesystem
layer.** Each `FileSystemProvider` implementation is responsible for exactly
one URI scheme, `file`, `jar`, or a third party scheme such as an in-memory
or cloud filesystem, and nothing else. The class documentation states the
provider "is identified by a URI scheme" and "creates the FileSystem that
provides access to the file systems accessible" for that scheme (Oracle,
*Java SE 21 API Specification*,
`java.nio.file.spi.FileSystemProvider`, verified 2026-08-02,
https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/file/spi/FileSystemProvider.html).
A single provider never mixes scheme-specific logic for two schemes, which
is exactly the SRP boundary drawn along "which filesystem does this code
know how to talk to."

**Kubernetes, the one-container-per-Pod default and the sidecar pattern as
its named exception.** Kubernetes documentation states plainly that "the
'one-container-per-Pod' model is the most common Kubernetes use case" and
that grouping multiple containers in a Pod "is a relatively advanced use
case" reserved for containers that "are tightly coupled and need to share
resources," explicitly steering ordinary application code away from mixing
unrelated responsibilities inside one running unit (Kubernetes
documentation, "Pods," verified 2026-08-02,
https://kubernetes.io/docs/concepts/workloads/pods/). The sidecar pattern
itself exists as the sanctioned exception precisely because a second
concern, a log shipper or a service-mesh proxy, is a genuinely different
actor from the main application container, and Kubernetes gives it its own
container rather than folding it into the same process, which is SRP
applied at the level of a deployable unit rather than a class.

**The Unix command-line toolset, as the discipline's oldest production
instance.** `grep` matches lines, `sort` orders lines, `wc` counts, and each
does only that one thing, composed through pipes rather than merged into one
program with flags for every combination. Doug McIlroy's rule, "write
programs that do one thing and do it well," as recorded by Peter H. Salus,
*A Quarter Century of Unix*, Addison-Wesley, 1994, and reproduced widely,
including in the Wikipedia summary of the Unix philosophy verified
2026-08-02 at https://en.wikipedia.org/wiki/Unix_philosophy, is SRP applied
to whole executables rather than classes, and it predates Martin's
object-oriented formulation by roughly two decades, which is why the two are
presented together in dimension 1 as convergent lineages rather than one
descending from the other.

**ASP.NET Core middleware pipeline.** Each piece of middleware registered
with `IApplicationBuilder.Use` is documented as handling one concern, such
as authentication, response compression, or routing, and the pipeline
composes many single-purpose middleware components rather than one
monolithic request handler. Microsoft's own guidance for writing custom
middleware frames each middleware component around a narrow, named
responsibility that is added to or removed from the pipeline independently
of the others (Microsoft, ".NET documentation, ASP.NET Core Middleware,"
verified 2026-08-02,
https://learn.microsoft.com/en-us/aspnet/core/fundamentals/middleware/).

## 10. Consequences

Positive.

- A change driven by one actor touches one class, so the set of files a
  reviewer must inspect for a given ticket shrinks to the classes that
  actually answer to that actor.
- Unit tests become cheaper to write and to run, because a class with one
  responsibility needs fewer collaborators wired up to exercise it, per the
  invoice example where testing arithmetic no longer requires a database.
- Merge conflicts between unrelated changes drop, because two teams working
  on two responsibilities are, after the split, editing two different files.
- Classes become independently reusable. `InvoicePrinter` can be reused for
  a quote or a receipt if it does not carry billing arithmetic baked into
  it, whereas the original monolithic `Invoice` cannot be reused for
  anything that is not itself an invoice.
- In compiled languages, incremental build time improves, because a change
  to one responsibility's implementation file does not force recompilation
  of code that only depends on an unrelated responsibility, provided the
  split is reflected in module or package boundaries and not merely in class
  names within one file.

Negative.

- The number of types in the codebase grows, and a reader has to learn where
  each responsibility now lives instead of finding everything in one file.
  For a small codebase this cost can exceed the benefit, see dimension 4.
- Something has to reassemble the split pieces for a real use case, and that
  coordinator is new code that did not exist before the split, carrying its
  own maintenance cost.
- Over-applied, SRP produces the Anemic Domain Model, where all behaviour
  has migrated into service classes and the domain objects are pure data,
  which Fowler identifies as trading one coupling problem for a loss of
  encapsulation (Martin Fowler, "AnemicDomainModel," verified 2026-08-02,
  https://martinfowler.com/bliki/AnemicDomainModel.html).
- Identifying the correct actor boundary is itself a judgement call that can
  be wrong, and a wrong split, along the wrong axis, produces classes that
  must always change together anyway, defeating the purpose while paying
  the indirection cost.
- Cross-class navigation cost rises for a reader trying to understand one
  end-to-end behaviour, since following "what happens when an invoice is
  issued" now requires jumping between the calculator, the printer, and the
  repository rather than reading one method top to bottom.

## 11. Failure modes and misuse

**The god class that never got split.** Symptom. One file with several
thousand lines, imported by nearly every other module in the codebase,
where a small, unrelated bug fix requires the reviewer to read past
hundreds of lines of code that have nothing to do with the fix. Cause. Every
individual addition to the class looked reasonable in isolation and nobody
drew the actor boundary before the class grew large. Fix. Identify the
distinct actors touching the class from its commit history, extract one
responsibility at a time behind a passing test suite, following the
refactoring path in dimension 14.

**Splitting along data rather than along change.** Symptom. Two new classes
that must always be constructed together and always change in lockstep,
because whoever split the class grouped methods by which fields they
touched rather than by who asks for the change. Cause. The split used
"these methods touch the same three fields" as the boundary instead of "who
would ask for this to change." Fix. Re-derive the boundary from actors, not
from field access patterns. two methods can touch the same field and still
answer to different actors, and vice versa.

**The anemic domain model.** Symptom. A `Customer` class with only getters
and setters, and a `CustomerService` class that holds every piece of logic
that used to live on `Customer`, including logic that has no reason to be
separated from customer data at all, such as validating that an email
address is well formed. Cause. SRP applied by method count rather than by
actor, treating every method as a separate responsibility rather than
grouping methods that answer to the same actor. Fix. Recombine behaviour
that belongs to the entity's own invariants back onto the entity, and
reserve extraction for behaviour that genuinely answers to a different
actor, per Fowler's Anemic Domain Model critique cited in dimension 4.

**Premature extraction with only one actor so far.** Symptom. A codebase
with an `InvoiceCalculator`, `InvoicePrinter`, and `InvoiceRepository`, all
three used by exactly one call site, none of which has ever changed
independently of the others in the project's entire history. Cause. SRP
applied speculatively, anticipating future divergence that has not
materialized, following the general anti-pattern of speculative generality.
Fix. Merge responsibilities back together until a second actor genuinely
appears. a class that has always had one caller and one reason to change is
not a violation regardless of how many methods it has.

**The coordinator that quietly regrows the god class.** Symptom. After a
clean split, the coordinator class that wires the extracted pieces together
starts accumulating its own business logic, "just this one conditional,"
until it is itself doing calculation, formatting, and persistence
orchestration that has drifted from pure delegation. Cause. The extraction
solved the immediate problem but nobody enforced that the coordinator stays
thin, so the same accretion pattern that created the original god class
restarts one layer up. Fix. Treat the coordinator's own single
responsibility as "sequence calls to the collaborators, and nothing else,"
and move any conditional logic that decides behaviour into one of the
collaborators or a new one.

**Confusing SRP with "one method per class."** Symptom. A codebase where
`AddInvoiceLineService`, `RemoveInvoiceLineService`, and
`UpdateInvoiceTotalService` each wrap one line of logic and are wired
through a dependency injection container, producing more configuration code
than actual behaviour. Cause. The heuristic "small is better" was applied
without the underlying question, does this class have more than one reason
to change. Fix. Group operations that answer to the same actor back into
one class. the number of public methods is not the measure, the number of
distinct sources of change is.

## 12. Trade-off matrix

Compared against named alternatives across the forces from dimension 3.

| Force | Single Responsibility Principle | Anemic Domain Model (entity plus service classes) | God class (SRP not applied) | Feature Envy tolerated as a pattern | Facade over a monolith (no internal split) |
|---|---|---|---|---|---|
| Change isolation | High. One actor's change touches one class | Medium. Logic is isolated per verb, but entity invariants can drift from the logic that enforces them | Low. Any change risks touching unrelated behaviour | Low. The class whose data is used most still bears the coupling | Low internally, medium externally. Callers are isolated, internals are not |
| Testability | High. Narrow constructor dependencies per class | High for the service, low for the entity, which has no behaviour to test on its own | Low. Testing one behaviour drags in unrelated dependencies | Low. The envying method's tests must set up the envied class too | Medium. The facade is easy to test, but only by proxy for the real logic |
| Encapsulation of invariants | High, when extraction respects actor boundaries | Low. Invariants live outside the entity that should enforce them, per Fowler | Nominally high, since everything is in one place, but unreadable at scale | Low. Behaviour lives far from the data it depends on | High for external callers, unchanged internally |
| Class or file count | Increases, roughly one per actor | Increases sharply, roughly one service per verb plus the anemic entities | Stays low | Stays low | Stays low, hides internal count |
| Cognitive load per file | Low. Each file is small and focused | Low per file, high to trace a full use case across many services | High. One file holds everything | Medium. Logic is near the class it envies, but that class was not designed for it | Low for callers, unchanged for maintainers |
| Risk of premature complexity | Present if applied before a second actor exists | High. This is the typical over-application failure mode | Absent, at the cost of the god class problem instead | Absent | Absent, but defers the problem rather than solving it |
| Merge conflict rate across teams | Low, because teams own different classes | Low, for the same reason, at the cost of encapsulation | High. Everyone edits the same file | Medium. Envying code and envied data are still coupled | High if the facade's internals are not split either |

Reading of the table. SRP is the right default when a second actor is real
and identifiable. The Anemic Domain Model is what SRP degenerates into when
applied without the actor discipline from dimension 5. A god class is what a
codebase looks like when SRP is never applied at all. Feature Envy, covered
in the code smells family, is a narrower symptom that SRP extraction often
cures as a side effect, since moving a method to the class whose data it
uses is frequently the correct SRP-respecting move. A facade over an
unsplit monolith buys external callers isolation without paying the
maintainability cost internally, and is a legitimate stopgap, not a
substitute for eventually applying SRP inside the boundary it hides.

## 13. Related and incompatible patterns

- **Open Closed Principle.** Composes tightly. A class with a single,
  well-bounded responsibility is far easier to extend without modification,
  because the seam for extension, an interface or an abstract method, has a
  narrow, well-understood contract. Classes that mix responsibilities are
  hard to keep closed for modification, because a change driven by any one
  of their several actors forces an edit.
- **Interface Segregation Principle.** A close cousin at the interface
  level rather than the class level. ISP says a client should not be forced
  to depend on methods it does not use. SRP, applied to the interface a
  class exposes, is frequently what makes ISP achievable, since a class with
  one responsibility naturally exposes a narrow interface.
- **Dependency Inversion Principle.** Composes with the interface-based
  implementation variant in dimension 8. Once a responsibility is extracted
  into its own class, depending on an interface for that class rather than
  the concrete type lets the responsibility be substituted, most usefully
  for testing.
- **Separation of Concerns, the broader software-engineering idea.** SRP is
  the class-level, actor-driven operationalization of the older and more
  general Separation of Concerns idea associated with Edsger Dijkstra's 1974
  paper "On the Role of Scientific Thought." Separation of Concerns is the
  goal. SRP is one concrete, testable rule for pursuing it at the class
  level.
- **Cohesion, from structured design.** Not merely related but the direct
  ancestor, as documented in dimension 1. High functional cohesion, in the
  DeMarco and Page-Jones sense, is what a class that follows SRP exhibits.
  Weak, coincidental cohesion is what a god class exhibits.
- **Command pattern.** Frequently the concrete shape SRP takes at the
  use-case level, one command class per operation, each with a single
  `execute` method and a single reason to change, the business rule for
  that one operation.
- **Facade pattern.** Composes as the reassembly point mentioned in
  dimension 5 and dimension 8. A facade's own responsibility is
  orchestration of the split pieces, and it must be held to the same
  single-responsibility discipline or it becomes a new god class one layer
  up, as described in dimension 11.
- **Anemic Domain Model, as an incompatible failure mode rather than a
  companion pattern.** Not a pattern to compose with but a documented
  anti-pattern that results from applying SRP without the actor discipline.
  It is included here because it is the single most common way SRP goes
  wrong in practice, per dimension 4 and dimension 11, and a reader
  studying SRP needs to recognize it as the boundary not to cross.
- **Feature Envy, as a code smell SRP extraction often resolves.** When a
  method on class A mostly calls methods on class B's data, moving that
  method to B is frequently the correct SRP-respecting fix, since the
  method's real responsibility, and its real actor, belongs with B's data.

## 14. Refactoring path in and out

Introducing SRP into a class that currently mixes responsibilities. The
named refactoring most directly involved is Extract Class, see the
refactoring family entry, guided here by the actor analysis SRP requires.

1. List every public method on the class. For each one, write down who
   would ask for it to change, which person, team, or subsystem. Use
   version-control history as evidence where the answer is not obvious, by
   checking which tickets or commits touched which methods.
2. Group the methods by actor. A class with one group has no SRP violation
   to fix, regardless of its method count, per dimension 4. A class with two
   or more distinct groups is a candidate for extraction.
3. Starting with the smallest group, create a new class named for what it
   does, not for the data it touches, `InvoicePrinter` rather than
   `InvoiceHelper2`.
4. Move the methods in that group to the new class. For each moved method,
   pass in the data it needs as a parameter rather than holding a reference
   to the original entity as a field, following the composition-over-shared-entity
   variant from dimension 8, unless the extracted responsibility genuinely
   needs to hold state across calls.
5. Update every call site to call the new class instead of the old method
   on the original class. Run the full test suite after each call site is
   updated, not only at the end, so a broken call site is caught close to
   the edit that broke it.
6. Once a group has been fully moved and all call sites updated, delete the
   now-dead method from the original class. Confirm the original class
   still compiles and its remaining tests pass without the moved behaviour.
7. Repeat for the remaining groups. Stop when every remaining group on the
   original class answers to a single actor. A class does not need to be
   split down to one public method. it needs to be split down to one
   source of change.
8. Introduce a coordinator only if a real caller needs several of the
   extracted pieces together for one use case. Do not introduce it
   speculatively.

Removing SRP-driven extraction when it stops earning its place. This
happens when a supposed second actor never materializes, or the extracted
classes have never in the project's history changed independently of each
other.

1. Confirm, from version control, that the extracted classes have always
   changed together across their full history. A single counterexample, one
   commit that touched `InvoiceCalculator` without touching
   `InvoicePrinter`, is evidence the split is earning its place and should
   not be reverted.
2. If no such counterexample exists, merge the classes back, following
   Inline Class, see the refactoring family entry, moving the methods of
   the smaller class back onto the larger one.
3. Update call sites to call the merged class. Run the full test suite after
   each call site is updated.
4. Delete the now-empty class and its dependency injection wiring, if any.
5. If the coordinator class from step 8 above exists only to wire together
   classes that have just been merged, inline the coordinator too, since its
   only remaining job was assembling pieces that no longer need assembling.

## 15. Testing and verification

Easier because of the principle, when correctly applied.

- Each extracted class can be constructed with only the collaborators its
  one responsibility needs, so a test for `InvoiceCalculator` needs no
  database, no filesystem, and no PDF renderer, only the invoice data and
  the tax rules.
- A test failure localizes to the one responsibility that broke. A failing
  `InvoiceCalculator` test cannot be caused by a change to
  `InvoicePrinter`, because the two classes share no code, which removes an
  entire category of debugging false leads.
- Test doubles are smaller and cheaper to build, since a fake
  `InvoiceRepository` used to test the coordinator needs only to satisfy
  the narrow `InvoiceStore` interface from the interface-based variant in
  dimension 8, not the full surface of a real database client.
- Property-based tests become more tractable per responsibility, since a
  pure `InvoiceCalculator.total()` with no side effects is straightforward
  to generate random inputs for and check algebraic properties on, such as
  totals never going negative for non-negative line items, whereas the same
  property test against the original monolithic `Invoice` would need to
  stub out printing and persistence just to reach the arithmetic.

Harder because of the principle.

- Integration tests that exercise a full use case, issuing an invoice end
  to end, now have to assemble several collaborators correctly, and a
  wiring mistake in the coordinator, the wrong `InvoicePrinter`
  implementation injected, is a failure mode that did not exist when
  everything lived in one class.
- A test suite for the coordinator needs to decide how much of the real
  extracted classes to use versus how much to fake, and getting this
  balance wrong, faking too much, produces tests that pass while the real
  wiring is broken. faking too little turns every coordinator test into a
  slow integration test.

Techniques that apply.

- **Constructor injection of collaborators, verified by test doubles.**
  Each extracted class takes its dependencies through its constructor,
  which is what makes substituting a fake `InvoiceRepository` for a test
  possible without a mocking framework touching private internals.
- **Contract tests against the extracted interface.** When an interface
  such as `InvoiceStore` has more than one implementation, an in-memory
  fake for tests and a real database-backed one for production, one shared
  contract test suite run against both catches divergence between the fake
  and the real implementation before it causes a false-positive unit test.
- **A small number of end-to-end tests, deliberately kept few, covering the
  coordinator's wiring.** Since unit tests per responsibility already cover
  the logic, the coordinator's own tests exist mainly to catch wiring
  mistakes, and a handful of realistic scenarios is enough. there is no
  need to exhaustively re-test the calculator's edge cases at the
  coordinator level.
- **Mutation testing on the extracted classes.** Because each extracted
  class is small and has few dependencies, mutation testing tools run fast
  against it and give a meaningful signal about whether the unit tests
  actually exercise the logic, which is harder to get useful signal from
  against a large, multi-responsibility class where mutation testing time
  balloons.

## 16. Observability signals

SRP is a static design property, so there is no runtime metric labelled
"SRP compliance." What is observable is the downstream consequence of
having, or not having, applied it, and those signals are worth watching
deliberately.

What to record and track.

- **Churn concentration per file, from version control.** A file that
  appears in commits from many unrelated ticket categories, billing fixes,
  layout fixes, and database migration fixes, is a live signal that the
  file has more than one actor and is a genuine SRP-violation candidate,
  not a theoretical one. Tools that compute code churn per file and
  correlate it against issue labels make this visible without manual
  archaeology.
- **File size and cyclomatic complexity trend over time, per class or
  module.** A steadily growing file, with no corresponding growth in test
  coverage, is the accumulation pattern described in dimension 2 happening
  in real time.
- **Test setup cost per test suite.** A rising number of mocks, stubs, or
  fixture objects required to instantiate the class under test is a direct
  observable symptom of a class accumulating dependencies from more than
  one responsibility.
- **Merge conflict frequency on specific files, from the version control
  host.** A file that repeatedly appears in merge conflicts between two
  different teams' branches is exhibiting the team-boundary symptom from
  dimension 3 in a measurable way.
- **Build and recompilation scope, in compiled languages.** How many
  downstream modules recompile when one file changes is directly
  observable from build tooling and is a proxy for how many unrelated
  consumers a class's single, or not-so-single, responsibility touches.

A healthy state on a dashboard looks like this. files with high churn are
also files with a narrow, single ticket category behind that churn, test
setup for the corresponding suites stays flat as the codebase grows, and
recompilation scope for a typical change is proportional to the size of the
change rather than to the size of the whole module. A failing state looks
like the opposite. one file's churn chart is a superset of several unrelated
label categories, its test setup grows every quarter, and small changes to
it trigger large, disproportionate rebuild or re-review scope.

## 17. Security and privacy implications

SRP has a genuine, if often overlooked, security implication rather than
being neutral. The implication runs through the same mechanism that
produces its testability and change-isolation benefits.

**Privilege scoping follows responsibility scoping.** A class that mixes
billing arithmetic and database persistence typically ends up holding, in
its constructor or its fields, both the data needed for arithmetic and a
live database credential or connection needed for persistence, even though
the arithmetic never needs that credential. Anyone who can influence, or
audit, what the arithmetic code path does now has to reason about a class
that also has write access to the database, widening the practical
privilege surface of code that has no legitimate need for it. Splitting the
responsibilities lets the calculator be constructed, and audited, with no
database access at all, which is the principle of least privilege applied
at the class-construction level rather than at the operating-system
permission level.

**Attack surface localization for input validation.** When one responsibility
owns parsing or validating untrusted input, for example turning a
user-submitted invoice line into internal data, and that responsibility is
kept separate from the responsibility that later persists or renders the
data, a security review of the codebase can focus its attention on the one
class that touches untrusted input directly, rather than auditing a
monolithic class where untrusted data and trusted internal logic are
interleaved throughout.

**Audit log clarity.** Because a single-responsibility class has one
narrow set of operations, log lines emitted from within it are unambiguous
about which concern generated them. A log line from `InvoiceRepository`
unambiguously concerns persistence. a log line from a monolithic `Invoice`
class that both prints and persists requires additional context to tell
which concern generated a given entry, which slows down incident response
and can obscure the boundary an auditor needs when investigating a data
exposure.

On privacy specifically, the principle is mostly a lever rather than a
guarantee. Personal data does not become more or less protected merely
because a class has one responsibility. what changes is that a class whose
single responsibility is, say, "compute a customer's loyalty tier," can be
reviewed for what personal data it touches without also reviewing whatever
unrelated concern used to share its file, which makes a data-protection
impact assessment tractable rather than automatically correct.

## Code examples

Three languages chosen for different reasons. TypeScript shows the
interface-based variant with constructor injection, closest to how SRP is
usually taught. Python shows the free-function, module-level variant, since
Python code frequently expresses SRP at the module boundary rather than
strictly at the class boundary. Go shows the interface-satisfaction variant,
since Go's implicit interfaces make substituting a fake repository for
tests nearly free and demonstrate SRP combined with dependency inversion
cleanly. Java, Rust, and Swift are omitted from the working examples for
space, not because SRP does not apply to them. it applies identically, as a
class or struct with one reason to change, in every one of them.

### TypeScript

```typescript
interface InvoiceLine {
  description: string;
  quantity: number;
  unitPriceCents: number;
}

interface Invoice {
  id: string;
  lines: InvoiceLine[];
  taxRatePercent: number;
}

class InvoiceCalculator {
  total(invoice: Invoice): number {
    const subtotal = invoice.lines.reduce(
      (sum, line) => sum + line.quantity * line.unitPriceCents,
      0
    );
    const tax = Math.round((subtotal * invoice.taxRatePercent) / 100);
    return subtotal + tax;
  }
}

class InvoicePrinter {
  render(invoice: Invoice, total: number): string {
    const rows = invoice.lines
      .map((l) => `${l.description}  x${l.quantity}`)
      .join("\n");
    return `Invoice ${invoice.id}\n${rows}\nTotal: ${total} cents`;
  }
}

interface InvoiceStore {
  save(invoice: Invoice): void;
}

class InMemoryInvoiceStore implements InvoiceStore {
  private saved: Invoice[] = [];
  save(invoice: Invoice): void {
    this.saved.push(invoice);
  }
  count(): number {
    return this.saved.length;
  }
}

class IssueInvoiceUseCase {
  constructor(
    private readonly calculator: InvoiceCalculator,
    private readonly printer: InvoicePrinter,
    private readonly store: InvoiceStore
  ) {}

  run(invoice: Invoice): string {
    const total = this.calculator.total(invoice);
    this.store.save(invoice);
    return this.printer.render(invoice, total);
  }
}

const store = new InMemoryInvoiceStore();
const useCase = new IssueInvoiceUseCase(
  new InvoiceCalculator(),
  new InvoicePrinter(),
  store
);
const invoice: Invoice = {
  id: "INV-1",
  taxRatePercent: 19,
  lines: [{ description: "Widget", quantity: 3, unitPriceCents: 500 }],
};
console.log(useCase.run(invoice));
console.log("saved count:", store.count());
```

### Python

```python
from dataclasses import dataclass


@dataclass
class InvoiceLine:
    description: str
    quantity: int
    unit_price_cents: int


@dataclass
class Invoice:
    id: str
    lines: list[InvoiceLine]
    tax_rate_percent: int


def invoice_total(invoice: Invoice) -> int:
    subtotal = sum(l.quantity * l.unit_price_cents for l in invoice.lines)
    tax = round(subtotal * invoice.tax_rate_percent / 100)
    return subtotal + tax


def render_invoice(invoice: Invoice, total: int) -> str:
    rows = "\n".join(f"{l.description}  x{l.quantity}" for l in invoice.lines)
    return f"Invoice {invoice.id}\n{rows}\nTotal: {total} cents"


class InMemoryInvoiceStore:
    def __init__(self) -> None:
        self._saved: list[Invoice] = []

    def save(self, invoice: Invoice) -> None:
        self._saved.append(invoice)

    def count(self) -> int:
        return len(self._saved)


def issue_invoice(invoice: Invoice, store: InMemoryInvoiceStore) -> str:
    total = invoice_total(invoice)
    store.save(invoice)
    return render_invoice(invoice, total)


if __name__ == "__main__":
    store = InMemoryInvoiceStore()
    invoice = Invoice(
        id="INV-1",
        tax_rate_percent=19,
        lines=[InvoiceLine("Widget", 3, 500)],
    )
    print(issue_invoice(invoice, store))
    print("saved count:", store.count())
```

Module-level SRP is visible here at the file boundary rather than the class
boundary. `invoice_total` and `render_invoice` are free functions, each
with exactly one reason to change, tax calculation and print formatting
respectively, and neither one imports or depends on the other, which is the
same isolation the TypeScript classes buy, expressed without a class
construct.

### Go

```go
package main

import "fmt"

type InvoiceLine struct {
	Description    string
	Quantity       int
	UnitPriceCents int
}

type Invoice struct {
	ID            string
	Lines         []InvoiceLine
	TaxRatePercent int
}

type InvoiceCalculator struct{}

func (InvoiceCalculator) Total(inv Invoice) int {
	subtotal := 0
	for _, l := range inv.Lines {
		subtotal += l.Quantity * l.UnitPriceCents
	}
	tax := subtotal * inv.TaxRatePercent / 100
	return subtotal + tax
}

type InvoicePrinter struct{}

func (InvoicePrinter) Render(inv Invoice, total int) string {
	out := fmt.Sprintf("Invoice %s\n", inv.ID)
	for _, l := range inv.Lines {
		out += fmt.Sprintf("%s  x%d\n", l.Description, l.Quantity)
	}
	out += fmt.Sprintf("Total: %d cents", total)
	return out
}

type InvoiceStore interface {
	Save(inv Invoice)
}

type InMemoryInvoiceStore struct {
	saved []Invoice
}

func (s *InMemoryInvoiceStore) Save(inv Invoice) {
	s.saved = append(s.saved, inv)
}

func (s *InMemoryInvoiceStore) Count() int {
	return len(s.saved)
}

type IssueInvoiceUseCase struct {
	Calculator InvoiceCalculator
	Printer    InvoicePrinter
	Store      InvoiceStore
}

func (u IssueInvoiceUseCase) Run(inv Invoice) string {
	total := u.Calculator.Total(inv)
	u.Store.Save(inv)
	return u.Printer.Render(inv, total)
}

func main() {
	store := &InMemoryInvoiceStore{}
	useCase := IssueInvoiceUseCase{
		Calculator: InvoiceCalculator{},
		Printer:    InvoicePrinter{},
		Store:      store,
	}
	inv := Invoice{
		ID:             "INV-1",
		TaxRatePercent: 19,
		Lines: []InvoiceLine{
			{Description: "Widget", Quantity: 3, UnitPriceCents: 500},
		},
	}
	fmt.Println(useCase.Run(inv))
	fmt.Println("saved count:", store.Count())
}
```

`InvoiceStore` is declared as an interface with one method, and
`InMemoryInvoiceStore` satisfies it implicitly, without an `implements`
declaration, which is Go's idiomatic way of expressing the interface-based
variant from dimension 8. the calculator, the printer, and the store each
have one reason to change, and the use case depends on the store only
through the narrow interface, not the concrete in-memory type.

## 18. References

1. Wikipedia contributors. "Single-responsibility principle."
   https://en.wikipedia.org/wiki/Single-responsibility_principle
   Verified 2026-08-02. Source for Martin's "one reason to change" and
   "gather together things that change for the same reasons" formulations,
   and for the attribution of the underlying cohesion concept to Tom DeMarco
   and Meilir Page-Jones.
2. Tom DeMarco. *Structured Analysis and System Specification*. Yourdon
   Press, 1979. Cited via the Wikipedia summary above as the earlier source
   of the cohesion concept SRP builds on. Original chapter and page not
   independently re-verified in this pass, cited at the level the summary
   source supports.
3. Meilir Page-Jones. *The Practical Guide to Structured Systems Design*.
   Yourdon Press, 1988. Cited via the Wikipedia summary above alongside
   DeMarco as the second source of the cohesion concept. Same caveat as
   reference 2.
4. Robert C. Martin. *Clean Architecture. A Craftsman's Guide to Software
   Structure and Design*. Prentice Hall, 2017. ISBN 978-0-13-449416-6.
   Chapter 7, "The Single Responsibility Principle." Source for the
   later "actor" reframing of "reason to change," used in dimension 5.
   Chapter number confirmed against the book's published table of contents
   at the publisher and standard retail listings, page numbers not
   independently re-verified in this pass.
5. Martin Fowler. "AnemicDomainModel." martinfowler.com.
   https://martinfowler.com/bliki/AnemicDomainModel.html
   Verified 2026-08-02. Source for the Anemic Domain Model failure mode
   described in dimensions 4, 10, and 11.
6. Martin Fowler. *Patterns of Enterprise Application Architecture*.
   Addison-Wesley, 2002. ISBN 0-321-12742-0. Cited alongside reference 5 as
   the book-length treatment of domain modelling that the bliki entry
   summarizes, not independently re-verified page by page in this pass.
7. Wikipedia contributors. "Unix philosophy."
   https://en.wikipedia.org/wiki/Unix_philosophy
   Verified 2026-08-02. Source for Doug McIlroy's "write programs that do
   one thing and do it well" and its attribution to Peter H. Salus, *A
   Quarter Century of Unix*, Addison-Wesley, 1994.
8. Oracle. *Java SE 21 API Specification*,
   `java.nio.file.spi.FileSystemProvider`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/file/spi/FileSystemProvider.html
   Verified 2026-08-02. Source for the one-URI-scheme-per-provider
   production use in dimension 9.
9. Kubernetes documentation. "Pods."
   https://kubernetes.io/docs/concepts/workloads/pods/
   Verified 2026-08-02. Source for the one-container-per-Pod default and
   the tightly-coupled exception used in dimension 9.
10. Microsoft. ".NET documentation, ASP.NET Core Middleware."
    https://learn.microsoft.com/en-us/aspnet/core/fundamentals/middleware/
    Verified 2026-08-02. Source for the middleware-pipeline production use
    in dimension 9.
