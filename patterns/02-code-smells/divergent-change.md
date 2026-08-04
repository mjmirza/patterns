---
name: Divergent Change
slug: divergent-change
family: 02-code-smells
category: Change Preventers
aliases: [Shotgun Class, God Class Drift, Multiple Reasons to Change]
first_described: "Fowler, Beck, Brant, Opdyke, Roberts 1999, Refactoring, Improving the Design of Existing Code"
maturity: canonical
related: [shotgun-surgery, single-responsibility-principle, extract-class, move-method, facade, strategy, observer]
incompatible_with: []
verified: 2026-08-02
---

# Divergent Change

## 1. Name, aliases, and lineage

The canonical name is Divergent Change. It is one of the twenty two named code
smells catalogued by Martin Fowler, with Kent Beck, John Brant, William
Opdyke, and Don Roberts, in Martin Fowler, *Refactoring, Improving the Design
of Existing Code*, Addison-Wesley, 1999, Chapter 3, "Bad Smells in Code",
section "Divergent Change". The second edition of the book (2018, with Kent
Beck) keeps the same name and the same pairing with its sibling smell,
Shotgun Surgery. Fowler's own living catalogue site restates the smell under
this exact name and groups it under the "Dysfunctional Camaraderie" and
"Change Preventers" family alongside Shotgun Surgery and Parallel Inheritance
Hierarchies, per the second-edition table of contents (refactoring.com
catalog page structure, verified 2026-08-02, though the specific per-smell
page for Divergent Change was not independently resolvable at the time of
this verification).

Fowler chose the word divergent deliberately, and it is worth reading closely
because the two sibling smells are named as mirror images of each other and
are easy to confuse. Divergent Change describes one module that is forced to
change in many different directions for many different, unrelated reasons.
Shotgun Surgery describes the opposite shape, one reason to change forces
edits to scatter across many different modules. Divergent Change is a single
class with too many reasons to change. Shotgun Surgery is a single reason to
change with too many classes affected. The two smells are frequently produced
by the same underlying design mistake viewed from two different vantage
points, poor separation of concerns, and a change that removes one often
worsens the other unless it is done carefully, which is discussed under
Consequences below.

No competing name has taken hold in the wider literature the way it has for
some other Fowler smells. Robert C. Martin's Single Responsibility Principle,
described in Robert C. Martin, *Agile Software Development, Principles,
Patterns, and Practices*, Prentice Hall, 2002, in the chapter introducing the
SRP, is not a synonym but is the design principle whose violation produces
this exact smell. Martin's own formulation of the principle, that a class
should have only one reason to change, is close enough to Fowler's diagnostic
question for Divergent Change that the two are often taught together, and
several later writers, including Martin himself in later talks, use "a class
with more than one reason to change" as a plain-English restatement of
Divergent Change without claiming to have renamed it. The informal terms God
Class Drift and Shotgun Class are observed usages in team retrospectives and
code review comments rather than terms with independent published
attribution, and are listed here only as encountered usage, not as sourced
aliases.

## 2. Problem and context

A single class keeps needing edits, and the edits have nothing to do with
each other. This month it changed because the tax calculation rules changed.
Last month it changed because a new database column was added. The month
before that it changed because the report layout moved a column. None of
those three edits touch the same lines, none of the three people who made
them needed to understand the other two changes, and yet all three had to
open the same file, read past code that was irrelevant to their change, and
risk breaking something unrelated while they were in there.

The situation reads like this in a real codebase. There is a class, often
named after a noun central to the business domain, an `Order`, a `User`, a
`Report`, an `Employee`, an `Invoice`. It started small and grew by
accretion. Each new requirement found the fastest path to be adding a method
or a field to the existing class, because the class already had a database
row, already had a constructor, already appeared in the places the new
behaviour needed to be reached from. Over months or years the class
accumulates persistence logic, validation logic, formatting logic for two or
three different output formats, calculation logic that changes with policy,
and often some cross-cutting concern like audit logging or authorization
sprinkled through the rest. Nobody who works on tax logic wants to also read
the CSV export code sitting sixty lines above it, and nobody exporting a CSV
report wants to trace a tax bug while trying to fix a column header.

The context that produces this smell has three recurring ingredients, each
of them ordinary and each of them individually reasonable in isolation. The
first is a genuinely important domain concept that legitimately needs many
capabilities, an `Order` really does need to be persisted, really does need
validation, and really is the thing a report is about, so pulling all of that
onto one class does not look wrong on day one. The second is incremental
delivery under time pressure, where the cheapest available slot for new
behaviour is always "add a method to the class that already exists" rather
than "design a new collaborator", because the second option costs more time
now for a benefit that only shows up later. The third is the absence of a
design review step that asks, before a method is added, which actor or which
axis of change this new method serves, and whether that axis already has a
home elsewhere in the codebase. Divergent Change is what results when the
second ingredient wins against the third, repeatedly, over a long enough
period that the accumulated cost becomes visible to everyone who has to touch
the class.

## 3. Forces

Cohesion pulls toward keeping related data and behaviour together in one
place, and the domain object genuinely is the natural home for many
behaviours that operate on its data, so a design that starts cohesive does
not look wrong. Separation of concerns pulls in the opposite direction,
toward splitting behaviour by the axis along which it changes rather than by
the data it touches, because two behaviours that share a data structure but
never share a reason to change are not actually related in the sense that
matters for maintenance.

Team topology is a force that is easy to underweight and expensive to
ignore. When the tax team, the reporting team, and the persistence team all
edit the same file, the file becomes a de facto shared resource with all the
coordination cost that implies, merge conflicts, accidental coupling through
shared private helpers, and a review process where nobody on the reviewing
side has full context on every change landing in the file that week. Splitting
along the axes of change lets each team own a smaller file that changes for
reasons only that team cares about, which reduces coordination cost at the
price of an extra layer of indirection between the pieces.

Discoverability and cognitive load pull toward the single class too, at
least initially, because there is exactly one place to look for anything
related to the domain concept, and a newcomer can find "everything about
Order" by opening one file. Once the file passes a size where nobody can hold
its whole shape in working memory, that advantage inverts, because now the
newcomer has to read past several unrelated concerns to find the one they
came for, and the class stops being a map and starts being a maze.

Testability is affected in both directions depending on what is being
tested. Testing the whole domain object end to end is easy when everything
lives in one place, because there is one object to construct and one API
surface to call. Testing one axis of behaviour in isolation, the tax
calculation without touching the database, becomes hard, because the
behaviours are entangled through shared state and the test has to either
mock a large surface or accept a slow, brittle integration-style test for
what should be a pure calculation.

Fowler's own bias, stated directly in the book, favours splitting. The book
frames Divergent Change as something to fix with Extract Class, treating the
coordination and testability costs as dominant once the smell is recognisable
at all, and treats the loss of a single lookup location as a cost worth
paying (Fowler, *Refactoring*, 1999, Chapter 3). This entry follows that bias
but names dimension 4 below as the honest boundary of where it applies.

## 4. Applicability and non-applicability

Reach for a fix when a class has been edited for demonstrably unrelated
reasons across several recent changes, when different roles or teams edit
the same class for reasons that do not reference each other, when a change
for one concern regularly risks breaking an unrelated concern in the same
class (a bug introduced in the report formatter while fixing a validation
rule), when the class has grown past the point where a single person can
hold its full behaviour in mind while making a small change, or when writing
a focused unit test for one concern requires setting up unrelated state that
belongs to a different concern entirely.

Do not reach for a fix in these cases, with the reason stated plainly.

- **The class is small and the multiple responsibilities are still genuinely
  cohesive.** A `Point` class that supports arithmetic, equality, and string
  formatting is not suffering Divergent Change merely because it has three
  kinds of method. The test is not whether this class does more than one
  thing in a literal sense, it is whether this class changes for reasons
  that do not reference each other in practice. A value type whose
  formatting and arithmetic have never changed independently in the life of
  the project is not exhibiting the smell yet, even if it could in
  principle.
- **The apparent divergence is really Shotgun Surgery in disguise.** If the
  fix for a single business rule change requires touching this class along
  with four others, splitting this one class further will not help and may
  make the shotgun spread worse by adding a fifth touch point. Diagnose
  which smell is actually present before choosing Extract Class over Move
  Method, per the trade-off discussion in dimension 12.
- **The team is deliberately keeping a script or a prototype simple.** A
  short-lived exploratory script, a one-off migration tool, or a prototype
  meant to be thrown away after a demo does not benefit from the extra
  indirection Extract Class introduces. The cost of the smell is paid over
  the lifetime of maintenance, and code with no maintenance lifetime ahead
  of it does not owe that cost.
- **The platform genuinely requires a single entry point for the axis in
  question.** Some frameworks mandate a specific base class shape, for
  example a single Android `Activity` subclass that framework lifecycle
  callbacks must land on, or a single ASP.NET Core `Startup` class that
  hosting infrastructure expects to find. Fighting the framework's required
  shape by over-splitting past what the framework can invoke is not a fix,
  it is friction with no corresponding benefit, and the correct response is
  usually to keep a thin framework-mandated shell that immediately delegates
  to the split collaborators, which is exactly what Extract Class produces
  when applied correctly (see dimension 14).
- **The class is already an explicit aggregate root or facade whose whole
  documented job is to present one surface over several collaborators.** A
  Facade (see the Facade pattern) that forwards to several subsystems is
  expected to change whenever any subsystem it wraps changes its public
  contract. That is the facade doing its job, not Divergent Change, provided
  the facade's own body stays thin and the substantive logic lives in the
  wrapped subsystems rather than in the facade itself.

## 5. Structure

Divergent Change is a smell, not a pattern, so it has no participants that
collaborate to deliver a benefit. It has one participant that is doing too
much, and it is useful to name the roles that are entangled inside it rather
than the class itself, because those roles are what the refactoring later
extracts.

- **The Overloaded Class.** The single class exhibiting the smell. It owns
  data, and it has accumulated methods serving several unrelated axes of
  change.
- **The Axis of Change (one or more).** A grouping of methods and the state
  they touch that all move together whenever one particular kind of
  requirement changes, and that never need to move when a different axis
  changes. Persistence is commonly one axis. Validation is commonly a
  second. A calculation whose rules are set by policy, tax, pricing,
  discounting, is commonly a third. Presentation or formatting for a
  specific output channel is commonly a fourth. Each axis is a candidate
  collaborator once extracted.
- **The Callers.** Code elsewhere in the system that invokes the Overloaded
  Class. Callers are relevant to the structure because after extraction they
  either keep calling the original class, which now delegates internally, or
  they are updated to call the extracted collaborator directly, and the
  choice between those two options is a real design decision made during the
  fix (see dimension 14).

## 6. ASCII structure diagram

```
BEFORE. one class serving several unrelated axes of change

  +----------------------------------------+
  |                Order                    |
  |  (the Overloaded Class)                 |
  |------------------------------------------|
  |  fields: id, items, customerId,          |
  |          taxRate, status                 |
  |------------------------------------------|
  |  save()               <- persistence     |
  |  load(id)              axis              |
  |  validateAddress()    <- validation       |
  |  validateItems()        axis              |
  |  calculateTax()        <- pricing/policy  |
  |  applyDiscount()         axis             |
  |  toCsvRow()            <- reporting       |
  |  toInvoicePdfLines()     axis             |
  +----------------------------------------+
        ^              ^              ^
        |              |              |
  persistence      validation    reporting
     code             code           code
   calls save/load  calls validate  calls toCsvRow

AFTER. Extract Class along each axis, Order delegates

  +---------------+      uses      +-------------------+
  |     Order     | -------------> |  OrderRepository   |
  | (domain data) |                |  (persistence axis)|
  +---------------+                +-------------------+
        |    ^
        |    | uses
        v    |
  +-------------------+           +-------------------+
  |  OrderValidator    |           |  TaxCalculator     |
  |  (validation axis) |           |  (pricing axis)    |
  +-------------------+           +-------------------+
        |
        v
  +-------------------+
  |  OrderReportFormatter |
  |  (reporting axis)     |
  +-------------------+
```

## 7. Dynamics

Before the fix, every request that touches `Order` runs through the single
class regardless of which axis it belongs to. Saving an order, validating an
order, and formatting an order for a report all begin the same way, resolve
a reference to the same `Order` instance, and invoke a method on it, so from
outside the class the interaction looks identical for three unrelated
concerns. Inside the class there is no separation at all, the persistence
method and the tax method sit next to each other in the same source file,
share the same private helper methods in some cases, and are compiled and
loaded as one unit, so a change to one has zero enforced isolation from the
other beyond whatever discipline the author exercised by hand.

```
Persistence call.  Caller -> Order.save()          -> DB write
Validation call.   Caller -> Order.validateItems()  -> throws or returns bool
Reporting call.    Caller -> Order.toCsvRow()        -> string

All three paths pass through the SAME class body, so a change that only
needs to touch one path still recompiles, re-reviews, and re-deploys
alongside the other two whenever they ship in the same release.
```

After Extract Class, the runtime flow gains one hop per delegated axis. A
persistence call now goes `Caller -> Order -> OrderRepository.save(order)`,
or in a cleaner variant the caller talks to `OrderRepository` directly and
`Order` is not on the call path for persistence at all. The dynamics
diverge from the smell's static structure specifically at this point, the
whole value of the fix is that a validation change can now ship, be
reviewed, and be tested without the reporting code being recompiled,
re-reviewed, or re-run at all, because the two axes no longer share a
compilation and review unit even though they may still share the underlying
data through the `Order` reference each collaborator holds.

```
Persistence call.  Caller -> OrderRepository.save(order) -> DB write
Validation call.   Caller -> OrderValidator.validate(order) -> bool
Reporting call.    Caller -> OrderReportFormatter.toCsvRow(order) -> string

Each path now touches only the collaborator responsible for that axis.
A validation-only change recompiles OrderValidator and its own tests,
and never forces OrderReportFormatter's tests to re-run for reasons
unrelated to reporting.
```

## 8. Implementation variants

**Straight Extract Class per axis.** The most literal fix. Identify each
axis of change, move its fields and methods into a new class, and have the
original class either delegate to the new class or be replaced at call sites
by direct references to the new class. This is the mechanism Fowler's book
names directly for this smell (Fowler, *Refactoring*, 1999, Chapter 3,
"Divergent Change", pointing the reader to Extract Class).

**Extract Class plus a thin facade for backward compatibility.** When many
existing callers already depend on the original class's public methods and
a big-bang migration of every call site is not feasible in one change, the
original class keeps its old method signatures but each method body becomes
a one-line delegation to the newly extracted collaborator. This lets the
split land incrementally, with call sites migrated to the new collaborator
directly over subsequent changes, and the thin delegating methods deleted
once the last caller has moved.

**Strategy-based extraction for the policy-shaped axis.** When one of the
axes is specifically a calculation whose rules vary by configuration or by
customer segment, extracting it as a Strategy object rather than a plain
collaborator class lets the calculation itself be swapped at runtime without
touching the class that holds the data, which is a further refinement past
plain Extract Class and is worth reaching for specifically when the axis in
question is expected to grow new variants (see the Strategy pattern entry
for the full trade-off).

**Observer-based extraction for the audit or notification axis.** When one
of the entangled concerns is a cross-cutting one, such as emitting an audit
log entry or sending a notification whenever the domain object changes state,
extracting that concern as an Observer that the domain object notifies,
rather than a method the domain object calls directly, decouples the
notification logic from the core object entirely and lets new observers be
added without editing the domain class again (see the Observer pattern
entry).

**Idiomatic variants by language.** In languages with free functions and
modules rather than mandatory classes, TypeScript, Go, and Rust among them,
the equivalent extraction is often a separate module or package rather than
a separate class, and the axis boundary is drawn at the module boundary
instead of at a class boundary, with the original struct or interface kept
minimal and the behaviour living in functions that take the data as a
parameter. The underlying diagnostic and the underlying fix are identical,
only the vocabulary changes.

## 9. Known production uses

**Martin Fowler's own worked example.** The *Refactoring* book's own
running example across several chapters is an early-edition `Employee`-style
domain class whose Extract Class walkthrough is offered specifically because
readers recognise the shape from their own codebases, persistence,
calculation, and reporting concerns sharing one class body (Fowler,
*Refactoring*, 1999, Chapter 3, "Divergent Change" and Chapter 7, "Extract
Class"). This is the canonical, book-sourced instance the smell is named
from, and every later production example in this dimension is a real-world
recurrence of the same shape.

**Objective-C and Swift "Massive View Controller" on iOS.** The `objc.io`
essay "Lighter View Controllers" documents, from direct observation of real
iOS codebases, that `UIViewController` subclasses routinely grow to contain
table view data source methods, table view delegate methods, model-parsing
logic, network request code, and view hierarchy construction, all inside one
class, because the framework hands the developer a single lifecycle-managed
class and the path of least resistance is to keep adding to it (Chris Eidhof
and Florian Kugler, "Lighter View Controllers," objc.io Issue 1, "View
Controllers," https://www.objc.io/issues/1-view-controllers/lighter-view-controllers/,
verified 2026-08-02). Each of those responsibilities changes for its own
reason, a new API field forces a change to the parsing code, a new screen
layout forces a change to the view-construction code, and a new list
behaviour forces a change to the data source code, and none of those three
changes has anything to do with either of the other two, which is Divergent
Change presented against a mobile UI framework rather than a persistence
layer. The article's own prescribed fix, moving the data source and delegate
logic out into dedicated collaborator objects that the view controller holds
a reference to, is a direct instance of Extract Class applied per axis.

**Ruby on Rails "fat model" refactoring, documented by thoughtbot.** The
thoughtbot engineering blog post "Skinny Controllers, Skinny Models"
documents, from direct experience maintaining production Rails applications,
an `ActiveRecord` model that begins by legitimately owning persistence and
validation and then accumulates unrelated responsibility as new features
land, in the article's example, HTML-conversion logic for a `Document`
model. The article states plainly that when a model file grows large enough
to slow down editor loading or when the file gets organised into commented
sections for different concerns, maybe there is a new model waiting to be
born, and prescribes extracting the unrelated concern, in the article's
case an `HtmlFile` class, out of the original model (Joe Ferris, "Skinny
Controllers, Skinny Models," thoughtbot blog,
https://thoughtbot.com/blog/skinny-controllers-skinny-models, verified
2026-08-02). This is Extract Class applied specifically to the reasoning
Fowler's book describes for Divergent Change, an `ActiveRecord` model
carrying persistence, validation, and an unrelated formatting concern on one
class, split by axis of change into a persistence-and-validation model and a
separate collaborator for the unrelated concern.

## 10. Consequences

**Positive.** A change for one reason now touches, is reviewed by, and is
tested against only the code that actually implements that reason, which
shrinks the blast radius of every future change and lowers the chance that
an edit to one concern accidentally breaks an unrelated one. Each extracted
collaborator can be unit tested in isolation with a small, focused set of
inputs, rather than requiring a large domain object to be constructed in
full just to exercise one narrow behaviour. Ownership becomes clearer,
because a team responsible for one axis of change can own the corresponding
collaborator without needing broad familiarity with the axes owned by other
teams. Extracted collaborators are also more reusable, because a
`TaxCalculator` that no longer requires a fully constructed `Order` object
can be applied to a quote, a draft order, or a bulk-pricing preview without
first assembling a real order.

**Negative.** The fix trades a single lookup location for several, so a
developer new to the codebase now has to know which of several classes to
open for a given concern, which costs discoverability even as it saves
cognitive load once the right file is found. The number of files, types, and
call indirections increases, which is a real cost in languages where each
extra hop through an interface has runtime overhead or where each extra type
adds compile time. Poorly judged extraction produces the opposite of the
intended benefit, splitting along the wrong axis, or splitting too finely,
creates collaborators that are themselves incoherent and that still change
together, which is Divergent Change one level deeper rather than a fix for
it. Extract Class also has a well-documented interaction with the sibling
smell Shotgun Surgery, discussed under dimension 12, where over-aggressive
splitting of a Divergent Change class can convert it into a Shotgun Surgery
problem elsewhere in the codebase if the newly extracted collaborators are
not given clear, minimal interfaces.

## 11. Failure modes and misuse

**Symptom.** Two engineers working on unrelated tickets both need to edit
the same file in the same sprint, and one of them introduces a merge
conflict or a subtle bug in the other's area while making an unrelated
change.
**Cause.** The class has never been split along axes of change, so unrelated
work keeps landing in the same file by default, because that file is where
the relevant data already lives.
**Fix.** Extract Class per axis (dimension 14), starting with the axis whose
churn rate is highest in the version-control history, since that is the axis
most frequently causing this exact collision.

**Symptom.** A code review for a small, one-line bug fix in a calculation
method takes far longer than the change warrants, because the reviewer has
to scroll past hundreds of unrelated lines to understand the surrounding
class, or the reviewer approves the change without reading the surrounding
context because doing so properly is too costly.
**Cause.** The reviewable unit, the whole class, is far larger than the
actual unit of change, one method belonging to one axis.
**Fix.** Split the class so the diff for a future change of this kind is
naturally scoped to a small file, which shrinks the reviewable surface to
match the actual change.

**Symptom.** Writing a unit test for one behaviour, for example a discount
calculation, requires constructing a fully valid `Order` with a database
connection or a full set of unrelated fields populated, even though the
discount logic itself needs only two numbers.
**Cause.** The behaviour under test is entangled with unrelated state and
unrelated dependencies that happen to live on the same class.
**Fix.** Extract the calculation into its own collaborator whose
constructor requires only the inputs the calculation actually needs,
after which the test constructs that small collaborator directly.

**Symptom.** After a class is finally split, a single business-rule change
now requires editing five newly extracted collaborators instead of one
original class, and the team perceives the split as having made things
worse rather than better.
**Cause.** Misuse of Extract Class, not the smell itself, the axes chosen
for extraction did not correspond to real, independent reasons to change.
Splitting was done by superficial grouping, for example one class per public
method, rather than by grouping methods that genuinely change together and
separating methods that genuinely change independently. This converts a
Divergent Change problem into a Shotgun Surgery problem, because now the one
real axis of change is scattered across the too-finely-split collaborators.
**Fix.** Re-merge the over-split collaborators that actually share a reason
to change, guided by the version-control co-change history described in
dimension 16, and re-split only where the history shows genuinely
independent change frequency.

**Symptom.** A class that was split months ago has quietly regrown a second
concern inside one of the extracted collaborators, and the same coordination
problems the original split fixed begin to reappear inside the new,
smaller class.
**Cause.** Extract Class is a one-time fix, not a standing guarantee. Without
a periodic check of what is landing in each collaborator, the same
incremental pressure that created the original smell recreates it inside the
new, smaller surface.
**Fix.** Treat the co-change signal (dimension 16) as an ongoing metric, not
a one-time diagnostic, and re-run the axis-of-change review whenever a
collaborator's change frequency or the diversity of ticket types touching it
starts climbing again.

## 12. Trade-off matrix

The named alternative in every row is a real, distinct design response to
an overloaded class, not a strawman version of leaving the code unchanged.

| Dimension | Extract Class (per axis) | Facade over the existing class | Do nothing, accept the smell |
|---|---|---|---|
| Isolation of unrelated changes | High. Each axis becomes its own reviewable, testable unit. | Low. A facade adds a thin public surface but the entangled logic still lives together underneath it, so unrelated changes still collide inside the implementation. | None. Every change continues to risk touching unrelated code in the same file. |
| Discoverability for a newcomer | Lower short-term. More files to learn, though each is smaller and named for its concern. | Higher short-term. One entry point stays visible, and the internal mess is hidden behind it, which can mislead a newcomer into underestimating the internal coupling. | Highest short-term, since there is exactly one file, at the cost of that file being large and hard to fully read. |
| Testability of one narrow behaviour | High. A small collaborator can be constructed and tested with minimal setup. | Low. Testing one behaviour through the facade still exercises the entangled implementation underneath, so setup cost stays close to the unsplit version. | Low, for the same reason, with no facade even to hide the setup cost behind. |
| Migration cost and risk | Moderate to high up front. Requires identifying real axes correctly (dimension 11 failure mode) and updating call sites or adding delegation. | Low up front. A facade can be added without moving any existing logic, which makes it a reasonable interim step before a full split. | Zero up front, but compounding over time as the class continues to grow and coordination cost rises with every additional feature landed on it. |
| Risk of over-correction | Real, if axes are chosen by superficial grouping rather than genuine independent change frequency, producing Shotgun Surgery instead (dimension 11). | Low, since no splitting has actually happened yet, only a new entry point has been added. | None, since nothing has changed, though the underlying coordination cost keeps accruing. |
| Best fit | A class whose entangled axes are confirmed, by co-change history or by team-ownership friction, to be genuinely independent reasons to change. | A class where the entangled logic is confirmed to be genuinely coupled internally and cannot yet be safely separated, but where callers benefit from a smaller, stable public surface in the meantime. | A short-lived script, prototype, or class small enough that the coordination cost has not yet materialised (dimension 4). |

## 13. Related and incompatible patterns

**Shotgun Surgery** is the mirror-image sibling smell. Where Divergent
Change is one class with too many reasons to change, Shotgun Surgery is one
reason to change with too many classes affected. The two smells compose
badly if fixed carelessly in one direction only, splitting a Divergent
Change class without giving the extracted collaborators clean, minimal
interfaces can turn a single reason to change into a change that now has to
touch several of the newly split collaborators at once, converting a
Divergent Change problem directly into a Shotgun Surgery problem. Diagnosing
which smell is actually present, or whether both are present at once along
different axes, should precede choosing a fix.

**Single Responsibility Principle** is the design principle whose violation
produces this smell, and the SRP's phrasing that a class should have only
one reason to change is close enough to Fowler's diagnostic question that
the two are taught together (Martin, *Agile Software Development*, 2002).
SRP is the principle. Divergent Change is the observable symptom of failing
to uphold it. Extract Class is the mechanical fix applied.

**Extract Class** and **Move Method** are the primary refactorings that
resolve Divergent Change once the axes are correctly identified (see
dimension 14 for the sequence). Extract Class creates the new home for an
axis. Move Method relocates the individual behaviours belonging to that axis
into the new home.

**Strategy** and **Observer** are compositional patterns that the extracted
collaborators sometimes take the shape of, specifically when the extracted
axis is a swappable calculation (Strategy) or a cross-cutting reaction to a
state change (Observer), as discussed under dimension 8.

**Facade** composes with Divergent Change as a deliberate interim step
rather than a competing fix, a facade can sit in front of an
about-to-be-split class to give callers a stable, small surface while the
underlying split happens incrementally behind it, and the facade's own
purpose, wrapping several subsystems behind one interface, is explicitly not
Divergent Change when the facade's body stays thin, as noted in dimension 4.

**Parallel Inheritance Hierarchies**, another smell in Fowler's Change
Preventers group alongside Divergent Change and Shotgun Surgery, is not the
same failure but is grouped with it in the second-edition table of contents
because all three share the property that a design flaw amplifies the cost
of otherwise ordinary changes. Parallel Inheritance Hierarchies is not
incompatible with Divergent Change, a class can suffer both at once.

## 14. Refactoring path in and out

**Introducing the smell (how it typically arrives).** Nobody deliberately
introduces Divergent Change in one step. It accrues through a long series of
individually reasonable Add Method or Add Field edits, each one the cheapest
available path for a real requirement, none of them stopping to ask which
axis of change the new method belongs to or whether an existing collaborator
already owns that axis. Recognising the arrival pattern is useful because it
points at the prevention step, before adding a method to an existing class,
ask which axis it serves and check whether that axis already has a
dedicated home elsewhere in the codebase.

**Removing the smell, step by step, following Fowler's Extract Class
mechanic (Fowler, *Refactoring*, 1999, Chapter 3 and Chapter 7).**

1. Identify the axes of change. The most reliable signal is version-control
   co-change history (dimension 16), not a subjective read of the code,
   group methods that have historically changed together in the same
   commits, and separate methods that have never changed in the same commit
   as each other.
2. For one axis at a time, create a new, empty class named for that axis's
   responsibility.
3. Move the fields that only that axis touches into the new class, using
   Move Field. If a field is touched by more than one axis, leave it on the
   original class for now and pass it as a parameter to the extracted
   collaborator's methods, revisiting the field's true owner once the split
   settles.
4. Move the methods belonging to that axis into the new class, using Move
   Method, updating internal references as each method lands.
5. Decide, per call site, whether the original class should keep a
   delegating method that forwards to the new collaborator, for a gradual
   migration, or whether call sites should be updated immediately to call
   the new collaborator directly, for a clean cut. Large codebases with many
   existing callers usually favour the delegating approach first, with call
   sites migrated over subsequent changes and the delegating methods deleted
   once the last caller has moved.
6. Repeat for the next axis, re-checking after each extraction that the
   remaining methods on the original class still belong together, since
   removing one axis sometimes reveals that the remainder is still
   entangled along a further axis that was not visible before.
7. Verify, using the tests described in dimension 15, that behaviour is
   unchanged at each step. Extract Class, done correctly, is a pure
   refactoring, it changes structure without changing observable behaviour,
   so a passing test suite before and after each step is the evidence the
   refactor was done safely.

## 15. Testing and verification

Before extraction, write or confirm characterisation tests around the
existing class's observable behaviour for each axis being separated, so
there is a behavioural baseline to compare against after the split. This
matters specifically for Divergent Change because the entangled class often
predates the project's own test suite, and splitting a class with no
existing coverage risks silently changing behaviour along an axis nobody was
paying attention to during the extraction.

After extraction, testing each collaborator becomes markedly easier for the
same reason the smell was costly in the first place, a `TaxCalculator` that
takes two numbers and returns a third can be tested with a small table of
input and expected-output pairs, with no database, no HTTP mock, and no
unrelated fields to populate. This is the practical payoff most visible to
engineers doing the day-to-day work after a Divergent Change fix, tests get
faster, get more focused, and stop breaking for reasons unrelated to what
they claim to test.

What became harder is testing interactions across the newly separated
collaborators, when such interactions still need to be verified end to end,
for example confirming that a full order-placement flow correctly calls
validation, then tax calculation, then persistence, in the right order. That
kind of test now needs to either construct the full graph of collaborators,
using a test double for the slow ones such as persistence, or run as a
smaller number of deliberately maintained integration tests rather than many
unit tests, since it is testing the orchestration of the axes rather than
any single axis.

## 16. Observability signals

The most reliable production signal for Divergent Change is not runtime
telemetry at all, since a smell in code structure has no direct runtime
symptom by itself, but a version-control signal, co-change frequency. A
class whose commit history shows tickets from several unrelated feature
areas each touching it, with those tickets sharing no common label, owning
team, or linked issue, is exhibiting the smell in its most measurable form.
Several widely used static-analysis and code-health tools compute exactly
this metric, commonly called temporal coupling or co-change coupling,
by mining which files change together in the same commit across a
repository's history, and a class that is frequently touched alongside many
unrelated other files, or whose own history shows commits with unrelated
purposes clustering on it, is a strong candidate for this smell regardless
of its raw line count.

Cyclomatic complexity and raw method or line count are secondary, weaker
signals. A large class is not automatically suffering Divergent Change,
since a large class whose methods are all genuinely part of one cohesive
concern is not exhibiting the smell even at significant size, and a small
class touched by only two unrelated ticket types over its lifetime may
already be worth splitting even though its size looks unremarkable. Size is
a proxy that correlates with the smell often enough to be useful as a
starting filter for where to look, but the co-change signal and the
question of whether one ticket references the other during review are the
more direct evidence.

A healthy state, once the smell has been fixed, looks like each extracted
collaborator's commit history showing changes clustered by a single,
identifiable purpose, tax-rule tickets on `TaxCalculator`, schema-migration
tickets on `OrderRepository`, layout tickets on `OrderReportFormatter`, with
very little overlap between the ticket types touching different
collaborators. A regression back toward the smell looks like that overlap
creeping back in over subsequent months, which is the failure mode described
at the end of dimension 11 and is worth watching for specifically after a
split, not only before one.

## 17. Security and privacy implications

Divergent Change carries no direct, mechanical security vulnerability of its
own, unlike an injection-style smell with a specific attack surface, but it
has a real indirect implication worth stating plainly rather than inventing
a specific exploit that does not exist. A class that mixes several unrelated
axes of behaviour, including for example both business logic and audit
logging, or both business logic and access control checks, makes it harder
for a reviewer to confirm that a security-relevant concern, such as an
authorization check, is applied consistently across every code path,
because the security-relevant lines are interleaved with unrelated logic
rather than concentrated in one clearly bounded, easily audited location. A
class that also carries persistence logic for sensitive data alongside
formatting or reporting logic increases the number of code paths that touch
that sensitive data directly, which widens the surface a security review has
to cover for that data, compared to a design where the persistence axis is
isolated in its own narrowly scoped collaborator. Splitting the class along
its axes, done correctly, tends to make the security-relevant axis, when
there is one, easier to isolate, review, and test in a focused way, which is
a genuine indirect benefit of the fix rather than the fix's primary purpose.

## 18. References

1. Martin Fowler, with Kent Beck, John Brant, William Opdyke, and Don
   Roberts. *Refactoring, Improving the Design of Existing Code*.
   Addison-Wesley, 1999. Chapter 3, "Bad Smells in Code", section
   "Divergent Change". Chapter 7 for the Extract Class mechanic used as the
   primary fix.
2. Robert C. Martin. *Agile Software Development, Principles, Patterns, and
   Practices*. Prentice Hall, 2002. Chapter introducing the Single
   Responsibility Principle.
3. Refactoring.com, "Refactoring Catalog", https://refactoring.com/catalog/,
   verified 2026-08-02, confirms the second-edition catalogue structure and
   the pairing of Divergent Change with Shotgun Surgery in the "Bad Smells"
   chapter. The specific per-smell subpage for Divergent Change could not be
   independently resolved during this verification pass, so the naming and
   grouping claim above is sourced to the book's table of contents rather
   than to a page confirmed live at this exact URL.
4. Chris Eidhof and Florian Kugler, "Lighter View Controllers," objc.io,
   Issue 1, "View Controllers,"
   https://www.objc.io/issues/1-view-controllers/lighter-view-controllers/,
   verified 2026-08-02.
5. Joe Ferris, "Skinny Controllers, Skinny Models," thoughtbot blog,
   https://thoughtbot.com/blog/skinny-controllers-skinny-models, verified
   2026-08-02.

## Code examples

The examples below show the same `Order` class before and after the fix, in
three languages. Each "before" sample crams persistence-shaped logic,
validation, and a calculation together on one type. Each "after" sample
splits those axes into separate collaborators the original type delegates
to. All three were compiled or run successfully during authoring.

### TypeScript

```typescript
// before.ts. one class, three unrelated axes of change.
class Order {
  constructor(public id: string, public items: number[], public taxRate: number) {}

  save(): string {
    return `INSERT INTO orders VALUES (${this.id})`;
  }

  validate(): boolean {
    return this.items.length > 0 && this.taxRate >= 0;
  }

  calculateTotal(): number {
    const subtotal = this.items.reduce((a, b) => a + b, 0);
    return subtotal + subtotal * this.taxRate;
  }
}

// after.ts. each axis is its own collaborator, Order delegates.
interface OrderData {
  id: string;
  items: number[];
  taxRate: number;
}

class OrderRepository {
  save(order: OrderData): string {
    return `INSERT INTO orders VALUES (${order.id})`;
  }
}

class OrderValidator {
  validate(order: OrderData): boolean {
    return order.items.length > 0 && order.taxRate >= 0;
  }
}

class TaxCalculator {
  calculateTotal(order: OrderData): number {
    const subtotal = order.items.reduce((a, b) => a + b, 0);
    return subtotal + subtotal * order.taxRate;
  }
}

class OrderV2 implements OrderData {
  private repository = new OrderRepository();
  private validator = new OrderValidator();
  private calculator = new TaxCalculator();

  constructor(public id: string, public items: number[], public taxRate: number) {}

  save(): string {
    return this.repository.save(this);
  }

  validate(): boolean {
    return this.validator.validate(this);
  }

  calculateTotal(): number {
    return this.calculator.calculateTotal(this);
  }
}

const o = new OrderV2("o-1", [10, 20, 30], 0.1);
console.log(o.save(), o.validate(), o.calculateTotal());
```

Compiled with `npx tsc --noEmit` against the TypeScript compiler installed in
the working environment, zero errors.

### Python

```python
# before.py. one class, three unrelated axes of change.
class Order:
    def __init__(self, order_id, items, tax_rate):
        self.order_id = order_id
        self.items = items
        self.tax_rate = tax_rate

    def save(self):
        return f"INSERT INTO orders VALUES ({self.order_id})"

    def validate(self):
        return len(self.items) > 0 and self.tax_rate >= 0

    def calculate_total(self):
        subtotal = sum(self.items)
        return subtotal + subtotal * self.tax_rate


# after.py. each axis is its own collaborator, Order delegates.
class OrderRepository:
    def save(self, order):
        return f"INSERT INTO orders VALUES ({order.order_id})"


class OrderValidator:
    def validate(self, order):
        return len(order.items) > 0 and order.tax_rate >= 0


class TaxCalculator:
    def calculate_total(self, order):
        subtotal = sum(order.items)
        return subtotal + subtotal * order.tax_rate


class OrderV2:
    def __init__(self, order_id, items, tax_rate):
        self.order_id = order_id
        self.items = items
        self.tax_rate = tax_rate
        self._repository = OrderRepository()
        self._validator = OrderValidator()
        self._calculator = TaxCalculator()

    def save(self):
        return self._repository.save(self)

    def validate(self):
        return self._validator.validate(self)

    def calculate_total(self):
        return self._calculator.calculate_total(self)


if __name__ == "__main__":
    o = OrderV2("o-1", [10, 20, 30], 0.1)
    print(o.save(), o.validate(), o.calculate_total())
```

Run with `python3 after.py`, output is
`INSERT INTO orders VALUES (o-1) True 66.0`.

### Go

```go
package main

import "fmt"

// before, a single Order type carrying three unrelated axes as methods
// would look the same shape as below with all logic inlined on Order.
// after, each axis becomes its own type, Order holds references to them.

type Order struct {
	ID      string
	Items   []int
	TaxRate float64

	repository *OrderRepository
	validator  *OrderValidator
	calculator *TaxCalculator
}

type OrderRepository struct{}

func (r *OrderRepository) Save(o *Order) string {
	return fmt.Sprintf("INSERT INTO orders VALUES (%s)", o.ID)
}

type OrderValidator struct{}

func (v *OrderValidator) Validate(o *Order) bool {
	return len(o.Items) > 0 && o.TaxRate >= 0
}

type TaxCalculator struct{}

func (c *TaxCalculator) CalculateTotal(o *Order) float64 {
	subtotal := 0
	for _, item := range o.Items {
		subtotal += item
	}
	return float64(subtotal) + float64(subtotal)*o.TaxRate
}

func NewOrder(id string, items []int, taxRate float64) *Order {
	return &Order{
		ID:         id,
		Items:      items,
		TaxRate:    taxRate,
		repository: &OrderRepository{},
		validator:  &OrderValidator{},
		calculator: &TaxCalculator{},
	}
}

func (o *Order) Save() string            { return o.repository.Save(o) }
func (o *Order) Validate() bool          { return o.validator.Validate(o) }
func (o *Order) CalculateTotal() float64 { return o.calculator.CalculateTotal(o) }

func main() {
	o := NewOrder("o-1", []int{10, 20, 30}, 0.1)
	fmt.Println(o.Save(), o.Validate(), o.CalculateTotal())
}
```

Run with `go run after.go`, output is
`INSERT INTO orders VALUES (o-1) true 66`.

Java, Rust, and Swift are omitted from the fully inlined listing above only
for length. The pattern translates directly in all three. Java and Swift use
the identical class-with-delegated-collaborators shape shown in TypeScript
and Python, and Rust uses a struct holding the data with separate,
free-standing structs and functions for each axis rather than methods on the
data struct itself, matching the module-boundary variant described in
dimension 8. A minimal Rust translation was compiled during authoring with
`rustc` against a struct-plus-free-function shape mirroring the Go example
above, confirming the pattern holds without inheritance or interfaces, using
only ownership and separate types per axis.
