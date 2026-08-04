---
name: Feature Envy
slug: feature-envy
family: 02-code-smells
category: Coupling
aliases: [Inappropriate Method Placement, Misplaced Responsibility]
first_described: "Fowler and Beck 1999"
maturity: canonical
related: [data-class, move-method, extract-class, message-chains, inappropriate-intimacy]
incompatible_with: []
verified: 2026-08-02
---

# Feature Envy

## 1. Name, aliases, and lineage

The canonical name is Feature Envy. It is one of the original smells catalogued
in Martin Fowler, *Refactoring. Improving the Design of Existing Code*,
Addison-Wesley, 1st edition, 1999, in the chapter "Bad Smells in Code", with
Kent Beck credited as co-author of that chapter's smell catalog. The 2nd
edition (Addison-Wesley, 2018) restructures the book around the refactoring
catalog itself but keeps the smell as a stated motivation for Move Function
(the 2nd edition's renamed Move Method), and the refactoring catalog site lists
Move Function, with Move Method as its recorded alias, under the
"moving features" category (https://refactoring.com/catalog/, verified
2026-08-02).

The term "code smell" itself, the umbrella Feature Envy sits under, was coined
by Kent Beck while he was helping Fowler write the first edition, not by Fowler
alone. Fowler records this directly on his own site. "The term was first
coined by Kent Beck while helping me with my Refactoring book"
(https://martinfowler.com/bliki/CodeSmell.html, verified 2026-08-02). This
detail matters for attribution because many secondary sources credit the whole
smell catalog to Fowler alone, and the primary source contradicts that.

No serious source disputes the name or claims a rival term for the same
observation. Some static analysis tools give the same underlying measurement a
narrower operational name. The Ruby smell detector Reek, for instance, defines
it structurally as "a code fragment [that] references another object more
often than it references itself" (https://github.com/troessner/reek/blob/master/docs/Feature-Envy.md,
verified 2026-08-02), which is the same idea stated as a counting rule rather
than a design judgement. That rewording is a detection heuristic, not a
competing name, and this entry treats it as an implementation of the smell,
covered in dimension 9.

Feature Envy is a code smell, not a design pattern, and that distinction shapes
every dimension below. A pattern is a solution you deliberately choose. A smell
is a diagnostic sign you notice in code that already exists, and the response
to noticing it is a refactoring, not an instantiation. This entry follows the
family 02 convention. dimensions 5 through 7 describe the smell's shape and how
it is recognized rather than participants you would design in from scratch,
and dimension 8 covers the refactorings that resolve it rather than
implementation variants of a construct you would choose to build.

## 2. Problem and context

A method sits on class A. Most of its logic reads or computes from the fields
and accessor methods of class B, an object it was handed as a parameter, an
instance variable, or returned from a call. The method touches its own class's
state rarely, or not at all, beyond invoking the method itself. Reading the
method's body, a person familiar with the codebase would ask why it lives on A
at all, since almost everything it does concerns B.

This arises constantly in three recognizable situations. First, procedural
code migrated into an object-oriented shape without redistributing behavior.
data structures were converted into classes with public fields, and the
functions that used to operate on those structures were converted into
methods on some coordinating class, but the functions themselves never moved
to sit beside the data they process. Second, a class was extended piece by
piece over months or years by different authors, each adding one more method
that happened to need data from a neighboring class because that neighbor was
already reachable, and no one paused to ask whether the method belonged where
it landed. Third, and most common in service oriented and layered
architectures, a coordinating or manager class accumulates business rules
that genuinely concern several different domain objects, and each rule gets
attached to the manager because the manager is where new code goes by
convention, not because the manager's own state is what the rule needs.

The context in which this becomes a real problem, and not merely an aesthetic
preference, is change. When a rule about how a Customer's discount works lives
on an InvoicePrinter instead of on Customer, every future change to discount
logic requires editing InvoicePrinter, reading Customer's public surface to
find the fields the rule depends on, and trusting that the two stay in step by
convention rather than by compiler enforced locality. The moment a second
class, say a SubscriptionRenewal service, needs the same discount rule, the
choice becomes duplicate the logic (now two copies to keep synchronized) or
have SubscriptionRenewal call into InvoicePrinter for a calculation that has
nothing to do with printing invoices, compounding the misplacement. Outside
this context, in genuinely short lived scripts, prototypes discarded within
days, or code with a single reader who will never revisit it, the smell is
present but harmless, because nothing depends on the design surviving change.

## 3. Forces

**Encapsulation versus procedural convenience.** Encapsulation asks that data
and the operations on that data live together, so that the rules governing a
piece of state cannot be violated from outside it. Feature Envy is what
happens when convenience wins that argument locally, one method at a time. It
is almost always easier, in the moment of writing a single method, to reach
through B's public getters from inside A than to stop and move the logic onto
B, especially when A already has the imports, the test scaffolding, and the
surrounding context set up.

**Coupling location versus coupling existence.** Moving the method does not
remove coupling between A's concern and B's data. If A genuinely needs a
computed value derived from B, A stays coupled to that value no matter which
class computes it. What moves is the shape of the coupling, from A depending
on B's internal representation (its fields, its accessor methods, the
invariants between them) to A depending on B's public behavioral contract, one
method with a clear name and a clear return value. The forces trade a wide,
brittle surface for a narrow, stable one, not coupling for no coupling.

**Cohesion versus a single point of extension.** Concentrating logic in one
manager or service class gives a team exactly one place to look when
adding a new rule, which is genuinely valuable in an unfamiliar or poorly
documented codebase. Distributing that logic across the domain objects it
concerns raises cohesion (each class's methods work with that class's own
data) at the cost of that single point of extension. a new team member now
must know that pricing rules live on Customer, shipping rules on Shipment,
and so on, rather than assuming everything is in the service layer.

**Testability versus test setup cost.** A method that lives with its data can
usually be tested by constructing one object and calling one method on it. A
method that reaches across several objects to gather what it needs typically
requires constructing every collaborator, which raises the setup cost of each
test but also, because that cost is uncomfortable, acts as an early warning
signal that a design has too many moving parts wired into one place. Feature
Envy actively resists this signal, because the envying class often reaches
through an already-simple, already-passed-in parameter, so the pain of setup
does not show up until the method grows large enough that the parameter's own
state has to be varied across several test cases.

**Team topology and ownership.** In a codebase owned by one team, moving a
method across a class boundary costs one pull request. In a codebase where
class A and class B are maintained by different teams (a common shape in
larger organizations, sometimes formalized around Conway's Law), the correct
move requires a cross team change, and Feature Envy frequently persists
precisely because the team that notices it does not own the class the method
should move to. This is an operability and organizational force, and pretending
the only forces at work are technical ones understates why the smell survives
in real systems.

## 4. Applicability and non-applicability

Apply the diagnosis and consider a refactoring when:

- A method's body references another object's fields or accessor methods
  substantially more often than it references its own class's state, and this
  is true independent of parameter count, meaning it is not explained away by
  the method simply taking one argument.
- Several unrelated methods across different classes each reach into the same
  object's public surface to perform the same or a closely related
  computation, which is the signature of Fowler and Beck's "several clients do
  the same series of manipulations" case cited by Reek's own definition.
- The method's name, when read honestly, describes a rule about the other
  object's domain concept, not about the class the method sits on. A method
  named `applyCustomerDiscount` sitting on `InvoicePrinter` is a naming
  admission that it belongs on `Customer`.
- Changing the internal representation of the envied class routinely forces an
  edit to the envying method, which is the concrete, observable cost of the
  misplaced coupling described in dimension 2.

Do NOT apply a Move Method refactoring, and do not treat the reading below as
a smell, when:

- The method genuinely coordinates between two or more objects and its
  purpose is that coordination itself, not a computation that belongs to one
  side. A method that reconciles a Shipment against an Order by comparing
  fields from both is not envious of either. moving it onto Shipment or Order
  alone would only relocate the same cross-object reasoning and lose the
  neutral vantage point that made the coordination readable. This is the
  standard Fowler caveat, restated precisely by the JDeodorant documentation
  as the reason automated Move Method suggestions still require a human
  decision, not a blind application (https://github.com/tsantalis/JDeodorant,
  verified 2026-08-02).
- The reaching-into-B behavior exists specifically to keep a stable, external
  API boundary between two modules, packages, or bounded contexts, and B's
  internals are deliberately not meant to be extended with application logic,
  for example because B is a third-party library, a generated client, or a
  value object shared across a service boundary where adding behavior would
  require a coordinated multi-repository release.
- The strategy or visitor family of patterns is deliberately in play. A
  Visitor's `visit(ConcreteElement)` methods are supposed to reach heavily
  into the visited element's data, because the entire point of Visitor is to
  add a new operation without adding a method to the element hierarchy. Move
  Method would defeat that intent by reintroducing the coupling Visitor exists
  to remove. Family 01's Visitor entry covers this in depth; this entry
  defers to it rather than repeating the analysis.
- The method is a DTO mapper, serializer, or adapter whose entire job is to
  translate one object's shape into another's. Reaching into the source
  object's fields is the job description, not a smell, because there is no
  sensible alternative location for read-then-produce logic other than a
  dedicated mapping function that touches both.
- Moving the method would create a circular dependency between two modules
  that must not depend on each other, for example moving a UI-formatting rule
  onto a domain entity that the domain layer's build target is not allowed to
  know about. In a layered architecture the fix in this case is Extract Class
  (pull the rule into a new class in the correct layer) rather than Move
  Method onto the offending class.

## 5. Structure

Feature Envy is a relationship between exactly two roles, observed in the
existing code rather than designed in advance.

- **The envying method.** The method whose body is under inspection. It is
  declared on some class A, and it is the unit of analysis. the smell is
  diagnosed per method, not per class, because a class can have some methods
  that are well placed and others that envy a different class entirely.
- **The envied object.** The object, usually class B, whose data the envying
  method depends on most heavily. It reaches the envying method through one
  of three channels. a parameter passed into the method, an instance field
  already held by class A, or the return value of a call the method makes
  before doing its real work.
- **The reference count comparison.** The structural signal itself, a count of
  references to the envied object's members against a count of references to
  the envying method's own class's members (fields, other methods on `self`
  or `this`), across the body of the method. Fowler's own description, echoed
  by every tool implementation checked for this entry, is comparative rather
  than absolute. the question is not whether a method touches another object
  but whether it touches that other object more than it touches its own class.
- **The candidate destination.** Once diagnosed, the smell implies a specific
  target, ordinarily the envied object's class, though Extract Class is the
  correct move instead when the logic concerns a third concept that neither
  A nor B currently represents, covered in dimension 14.

## 6. ASCII structure diagram

```
  Before                              After

  +----------------+                  +----------------+
  | InvoicePrinter  |                 | InvoicePrinter  |
  |----------------|                  |----------------|
  | +priceFor(c,amt)|--calls-->       | +priceFor(c,amt)|--calls-->
  +----------------+       |          +----------------+       |
         |                 |                                    |
         | reads mostly    |          +----------------+        |
         v                 |          |    Customer    |<-------+
  +----------------+       |          |----------------|
  |    Customer    |<------+          | -discountRate  |
  |----------------|                  | -loyaltyYears  |
  | -discountRate  |                  | -isWholesale   |
  | -loyaltyYears  |                  | +priceFor(amt) |  <- rule now
  | -isWholesale   |                  +----------------+     lives beside
  +----------------+                                          its own data

  Legend. InvoicePrinter.priceFor reads Customer's fields more    Customer.priceFor
  than its own state, the envy.                                   reads only self.
```

## 7. Dynamics

```
Before, per invoice printed.

  Client -> InvoicePrinter.priceFor(customer, baseAmount)
              |
              |-- read customer.discountRate
              |-- read customer.loyaltyYears
              |-- read customer.isWholesale
              |-- compute rate locally inside InvoicePrinter
              |-- return baseAmount * (1 - rate)

  Every rule change to how a customer's discount works is an edit
  inside InvoicePrinter, requiring InvoicePrinter's author to know
  Customer's field layout and keep it in sync by convention.

After, per invoice printed.

  Client -> InvoicePrinter.priceFor(customer, baseAmount)
              |
              |-- delegate. return customer.priceFor(baseAmount)
                              |
                              |-- read self.discountRate
                              |-- read self.loyaltyYears
                              |-- read self.isWholesale
                              |-- compute rate locally inside Customer
                              |-- return baseAmount * (1 - rate)

  A rule change now happens inside Customer, the class whose data
  the rule concerns, and InvoicePrinter's contract with Customer
  shrinks to one behavioral method call.
```

A second dynamic worth showing is the detection flow used by static analysis
tools, since it is how the smell is found at scale rather than by a reviewer's
eye.

```
  Source file -> parse into AST -> for each method M in class A.
                                      count(references to A's own members in M)
                                      for each other class B referenced in M.
                                        count(references to B's members in M)
                                      if max(counts for any B) > count(A's own).
                                        flag M as Feature Envy on B
```

Reek implements a version of exactly this counting comparison for Ruby method
bodies (https://github.com/troessner/reek/blob/master/docs/Feature-Envy.md,
verified 2026-08-02). JDeodorant performs a related but heavier analysis,
computing a numeric entity-placement metric across a method's statements to
decide whether a Move Method refactoring should be suggested, and it
deliberately treats calls to the method's own class through a chain
(`this.a().b()`) differently from direct field access, because chained
self-calls are not the same signal as direct external-field reads
(https://github.com/tsantalis/JDeodorant, verified 2026-08-02).

## 8. Implementation variants

Feature Envy has no implementation in the sense a construct like Factory
Method does; there is nothing to build, only something to notice and then
refactor away. What varies is the shape of the fix, and picking the wrong
shape is itself a common mistake, so this dimension enumerates the real
variants and where each applies.

- **Move Method (Move Function).** The direct fix when the envying method
  depends almost entirely on one other object and does not need any state
  private to the original class. The method's body relocates to the envied
  class, the original class either keeps a thin delegating method (to avoid
  breaking every caller in one commit) or is updated at every call site in the
  same change, and the method's own class's members it did reference become
  parameters passed in explicitly. This is the variant demonstrated in
  dimension 9's code examples.
- **Extract Method then Move Method.** Applied when only part of a larger
  method envies another object; the enveloping method is first split so the
  envious portion is its own method, which is then moved on its own, leaving
  behind a smaller method on the original class that calls the newly relocated
  one. This staged approach avoids moving well-placed logic along with the
  poorly placed logic only because they happened to share a method body.
- **Extract Class then Move Method.** Applied when the envied data does not
  belong to an existing class but to a concept that has not yet been given
  its own class, commonly a primitive-obsession situation where several
  loose fields (say, `streetLine1`, `streetLine2`, `city`, `postalCode`) are
  passed around together and a method envies all of them collectively. Here
  the fix is to create the missing class first (an Address, in this example),
  move the fields onto it, and then move the envying method onto the new
  class rather than onto whatever class happened to hold the loose fields
  before.
- **Split the envy across two destinations.** Applied when a method
  legitimately needs data from two objects roughly equally, and neither one
  is clearly the better home. The correct outcome is often not to move the
  method wholesale but to split it into two smaller methods, each moved to
  the object it actually concerns, with the original method reduced to a
  short coordinating call. This is the case dimension 4 calls out as a
  coordination method that is not envious of either side; recognizing which
  of the two situations you are in, genuine two-way coordination versus a
  method that is really two separate single-object rules glued together, is
  a judgement call, not a mechanical count.
- **Leave it, and document why, when a boundary force applies.** Where
  dimension 4's non-applicability list holds (Visitor, DTO mapping, a
  deliberate module boundary), the correct action is to record, in a
  comment or an architecture decision record, that the reference count is
  intentional, so a future automated scan or reviewer does not repeatedly
  reopen the same non-issue.

## 9. Known production uses

Feature Envy is unusual among catalogued smells in that its clearest
production uses are not applications of a construct but real, named
implementations of its detection, plus documented real-world instances of the
refactoring being applied. Both count as genuine evidence the smell is treated
as real by working engineers, not only by a textbook.

**Reek**, a static analysis gem for Ruby, ships a dedicated `FeatureEnvy`
detector as one of its built-in smell checks. Its own documentation states the
rule precisely. "Feature Envy occurs when a code fragment references another
object more often than it references itself, or when several clients do the
same series of manipulations on a particular type of object," and gives a
worked example where a `Warehouse#sale_price` method that computes
`(item.price - item.rebate) * @vat` is flagged, because the calculation
belongs on `Item` rather than on `Warehouse`
(https://github.com/troessner/reek/blob/master/docs/Feature-Envy.md, verified
2026-08-02). Reek is widely used as a Ruby linting dependency, and its
`FeatureEnvy` check runs, unmodified, against any Ruby codebase that installs
the gem and enables the default smell set.

**JDeodorant**, an Eclipse plugin for Java originating from academic research
by Nikolaos Tsantalis and Alexander Chatzigeorgiou, identifies Feature Envy
instances in Java source and proposes the corresponding Move Method
refactoring automatically. Its own project description states plainly. "Feature
Envy problems can be resolved by appropriate Move Method refactorings," and
lists Feature Envy alongside Type/State Checking, Long Method, God Class, and
Duplicated Code as one of the design problems it identifies
(https://github.com/tsantalis/JDeodorant, verified 2026-08-02). It is a real,
maintained tool that operationalizes exactly the diagnosis this entry
describes, packaged as an IDE-integrated refactoring suggestion rather than a
report a human has to interpret from scratch.

**Beaver Notes**, an open-source, actively maintained note-taking application,
carries a real commit that names Feature Envy explicitly as the reason for a
refactor. Commit `a05218f9b279475f2d45f0b632c479326c98cd8`, message "refactor.
consolidate note store, remove feature envy in FTS sync," reworks the note
store and full-text-search synchronization code; the accompanying
architectural notes in that change identify the specific instance as
`syncFtsIndex` in `src/store/note/helpers.js` directly accessing note
properties instead of using store getters
(https://github.com/Beaver-Notes/Beaver-Notes/commit/a05218f9b279475f2d45f0b632c479326c98cd8,
verified 2026-08-02). This is a concrete instance of the smell diagnosed and
fixed in a real, shipping codebase, not a textbook illustration, and it
matches the entry's own definition precisely. a function reaching into
another module's data more than its own.

## 10. Consequences

Positive, once the refactoring is applied:

- The rule and the data it depends on live in one place, so a future reader
  who wants to understand how a customer's discount works finds the
  entire answer on `Customer` instead of hunting through every class that
  happened to compute one.
- The envied class's invariants (for example, that a discount rate must stay
  within a valid range) can be enforced inside the class itself, at the one
  point where the data changes, rather than re-checked, or forgotten, at every
  external call site that reaches in.
- Test setup for the moved logic shrinks to constructing one object, because
  the method's inputs are now the class's own fields plus whatever narrow
  parameters remain, rather than a second collaborator object that has to be
  built up only to exercise the calculation.
- The originating class (the one the method moved away from) becomes
  measurably smaller and easier to read, because a method that had little to
  do with that class's actual purpose is gone.

Negative, and honest costs of the diagnosis itself:

- Fixing every instance a mechanical counter flags is not free and is not
  always correct; dimension 4's non-applicability cases are real, and a team
  that treats a Feature Envy warning as an automatic mandate to refactor will
  break Visitor-shaped code, DTO mappers, and deliberate module boundaries.
- Move Method changes every call site's shape. code that used to call
  `InvoicePrinter.priceFor(customer, amount)` now calls
  `customer.priceFor(amount)`, and in a large codebase with many call sites
  this is a real, reviewable diff, not a free rename.
- Over-applying the refactoring in the other direction, moving too much logic
  onto a small number of rich domain classes because every borderline case
  gets moved there, can itself create a new smell. a domain class that has
  absorbed so many unrelated rules that it becomes a God Class by a different
  route, covered by that entry's own diagnosis.
- Automated detection tools measure a proxy (reference counts) for a design
  judgement (does this logic conceptually belong here), and the proxy is
  imperfect. a coordination method that genuinely needs two objects roughly
  equally can still tip the count toward one side by accident of how it is
  written, producing a false positive that a careless team fixes anyway.

## 11. Failure modes and misuse

| Symptom | Cause | Fix |
|---|---|---|
| A manager or service class keeps growing every sprint, and almost every new method in it references one specific domain class's fields. | New logic defaults to landing on the coordinating class because that is where the team is used to adding code, rather than being placed with the domain object it concerns. | Apply Move Method to relocate the rule onto the domain object as soon as it is written, or, for existing code, run a static scan (dimension 9's tools, or a manual reference count per method) and work through the highest-count offenders first. |
| Changing one field's meaning on class B (say, renaming `discountRate` to `discountFraction` and changing its scale) requires editing five unrelated classes across the codebase. | The field is read directly, via public accessors, from five different envying methods scattered across five classes, none of which own the concept. | Consolidate the reads by moving each envying method onto B in turn, so a future change to the field's representation touches one class instead of five. |
| A Move Method refactoring is applied mechanically to a method that genuinely coordinates two objects (for example, reconciling a Payment against an Invoice), and afterward the method reads awkwardly, with the other object now passed in as a parameter that the code immediately tears apart to get back the fields it needs. | The diagnosis was applied without checking dimension 4's coordination exception; the reference count happened to lean toward one side, but the method's actual purpose was genuinely about the relationship between the two, not a rule that belongs to either one alone. | Revert the move, and instead consider Extract Class to give the relationship itself a name and a home, rather than forcing it onto one of the two participants. |
| After fixing Feature Envy across a module, one class has ballooned into hundreds of lines and dozens of unrelated methods, and it now takes longer to find anything in it than before the refactor. | Every borderline case was moved onto the same convenient, already-large class because it was the closest plausible destination, without checking whether the class's own cohesion was being harmed in the process. | Apply the class-level smell check (this entry's sibling entry, God Class) after a batch of Move Method refactorings, not only the method-level check that motivated each individual move. |
| An automated Feature Envy detector fires repeatedly on the same Visitor's `visit` methods, and the team either disables the rule entirely for the whole codebase or spends real time each release cycle re-suppressing the same false positives. | The tool's counting heuristic cannot distinguish logic misplaced by accident from logic deliberately placed in a Visitor to keep the visited hierarchy closed to modification. | Use the tool's per-instance or per-file suppression mechanism (JDeodorant and Reek both support this) scoped to the specific Visitor implementation, rather than disabling the check globally, so genuine instances elsewhere in the codebase are still caught. |

## 12. Trade-off matrix

| Force | Feature Envy left as-is | Move Method (this entry's fix) | Extract Class first | Split across both objects |
|---|---|---|---|---|
| Coupling shape | A depends on B's full internal surface | A depends on one narrow behavioral method on B | Both A and B depend on a new, focused class | Two smaller methods, each coupled to one object |
| Cohesion of A | Lower, A carries logic unrelated to its purpose | Higher, unrelated logic is gone from A | Higher, and neither A nor B absorbs unrelated logic | Higher, each fragment is small and focused |
| Cohesion of B | Unaffected, but B's data is exposed for external use | Higher, B now owns behavior over its own data | Unaffected directly, the new class carries the behavior | Higher, but only for its share of the logic |
| Test setup cost | High, must construct both A and B to exercise the rule | Low, construct B alone | Low, construct the new class alone | Low per fragment, but two test suites instead of one |
| Risk of over-concentration, God Class | None, logic stays scattered | Present if applied repeatedly onto one popular class | Lower, a new class absorbs only the specific concern | Lowest, no single class accumulates logic |
| Change locality when B's representation changes | Poor, every envying class must be found and updated | Good, only B changes | Good, only the new class changes | Moderate, both fragments may need updates |
| Appropriate when the method is genuine coordination | Not applicable, the smell is misdiagnosed in this case | Wrong choice, produces awkward code (dimension 11) | Often correct, gives the relationship a name | Correct when the two concerns are separable |

## 13. Related and incompatible patterns

**Data Class**, this family's sibling entry, is frequently the other half of a
Feature Envy pair. a class with public fields or simple accessors and almost
no behavior of its own is exactly the kind of class that attracts envying
methods, because there is nowhere else for behavior to naturally accumulate.
Fixing Feature Envy by moving methods onto a Data Class is usually a genuine
improvement precisely because it gives that class its first real behavior.

**God Class** is the failure mode described in dimension 11 when Move Method
is applied without limit onto the same convenient destination. The two smells
are connected by cause and effect in the wrong direction. treating Feature
Envy in isolation, one instance at a time, without periodically checking the
destination class's own cohesion, is how a codebase drifts from many small
instances of Feature Envy into one large instance of God Class.

**Message Chains**, another family 02 entry, often co-occurs with Feature
Envy. a method that reaches `customer.getAccount().getBillingAddress().getCity()`
is both chaining through several objects and, by the time it uses `getCity()`,
frequently doing more with that city value than the originating class's own
state, which is the Feature Envy signal layered on top of the chain. The two
smells share a root cause, a boundary that should exist between two concepts
does not exist yet, but call for different mechanical fixes. Message Chains is
resolved primarily with Hide Delegate or Extract Method along the chain,
Feature Envy with Move Method at the end of it.

**Inappropriate Intimacy**, a related class-level smell not yet in this
repository, describes two classes that reach so deeply into each other's
internals, in both directions, that they are effectively one class split into
two files. A single instance of Feature Envy, one method reaching into one
other object, is not by itself Inappropriate Intimacy; it becomes that only
when the reaching happens in both directions across many methods, at which
point the correct response shifts from moving individual methods to merging or
more deeply restructuring the two classes.

**Visitor** (family 01) and **Strategy** (family 01) are the two GoF patterns
this entry's non-applicability list names directly, because both deliberately
create methods that reach heavily into another type's data as their entire
purpose. Neither pattern is incompatible with Feature Envy detection existing
in a codebase; what is incompatible is treating a Visitor's or Strategy's
by-design data access as if it were the accidental kind this entry otherwise
targets.

**Law of Demeter**, a design guideline rather than a pattern, is closely
related in spirit. both are concerned with how far a method reaches outside
its own class. They are not identical. A method can obey the Law of Demeter
strictly, never chaining past one dot, while still being envious of the one
object it does reach, if it uses that object's data far more than its own.

## 14. Refactoring path in and out

Introducing the diagnosis into code that does not yet have it identified
starts from a concrete complaint, not a blanket scan. pick a class that is
painful to change, and for each of its methods, count references to the
class's own fields and methods against references to any single other object
reached through a parameter, a field, or a call. A method whose count leans
toward one other object is a Feature Envy candidate. Where a static tool is
available for the language (Reek for Ruby, JDeodorant for Java, or an
equivalent for the codebase's language), run it on the file under review and
treat its output as a prioritized list of candidates to examine, not as a
list of mandatory changes, per dimension 4's exceptions.

The mechanical steps for the direct fix, Move Method, follow Fowler's Move
Function refactoring shape, adapted to the general case.

1. Confirm the envied object's class exposes, or can be given, the fields
   the method needs, either as instance state already present or as
   parameters the method can be given when moved.
2. Copy the method's body onto the envied class as a new method, adjusting
   `customer.discountRate` style references to `self.discountRate` or
   `this.discountRate`, since the method now sits on the class it used to
   reach into.
3. Any reference in the copied body to the original class's own state (the
   small remainder that did not lean toward the envied object) becomes an
   explicit parameter of the new method, since that state is no longer
   directly reachable.
4. Replace the original method's body with a delegating call to the new
   method, so every existing call site keeps working unchanged through this
   intermediate step. Run the test suite here before proceeding.
5. If the original method's only remaining purpose is that one-line
   delegation, and the codebase's conventions favor calling the new location
   directly, update call sites to call the new method on the envied object
   and remove the now-empty delegating method. If many call sites exist,
   this step can be its own separate, later change, since step 4 already
   leaves the system correct.
6. Re-run the full test suite, and specifically re-verify any test that
   previously had to construct both classes to exercise the moved logic; that
   test's setup should now shrink, which is a useful confirmation the move
   was correct as well as a cleanup opportunity in the test itself.

Removing the pattern, or rather, undoing an over-applied instance of the fix,
matters once dimension 11's God Class failure mode has already happened,
because Move Method was repeatedly aimed at the same popular class. The path
out is Extract Class. identify the subset of the swollen class's methods that
share a cohesive theme distinct from the rest (for example, everything to do
with pricing, versus everything to do with shipment tracking, both of which
landed on `Customer` over time), create a new class for that subset, and move
those methods onto it with the same mechanical steps as above, treating the
swollen class as the envying side and the new class as the destination.

## 15. Testing and verification

Testing code before the refactoring typically requires constructing both the
envying class and the envied object, even though the test's actual intent is
to verify a rule that conceptually belongs to only one of them; this is
itself a diagnostic signal worth watching for while writing tests, not only
while reading production code. a test that needs an unrelated collaborator
object only to exercise whether the discount math works is often reporting
the same smell from a different angle.

After the refactoring, the moved method's tests become simpler to write, since
they construct one object and call one method on it, and this simplification
is a useful acceptance check on the refactoring itself. if moving the method
did not make its test setup shrink, the method was probably not genuinely
envious of the destination class, and dimension 4's coordination exception may
apply after all.

For the delegating step described in dimension 14's step 4, add or reuse a
test at the original call site's level that asserts the delegating method
still returns the same result as before the change, and keep that test in
place at least through the transition, since it is the test that would catch
an accidental behavior change introduced by the move, for example an off-by-
one difference between reading `self.rate` inside the new location versus the
`customer.rate` read that used to happen at the old one.

Where an automated Feature Envy detector is part of the toolchain (Reek,
JDeodorant, or an equivalent for the project's language), running it as part
of CI on changed files, rather than as a one-off manual audit, catches new
instances at the point they are introduced, when the fix is cheapest, rather
than after the envying method has accumulated more logic and more callers.
Configure the tool's suppression mechanism for the genuine exceptions in
dimension 4 at the point they are written, with a comment explaining why, so
the suppression itself is reviewable rather than a silent, undocumented
exclusion that a later contributor cannot understand.

## 16. Observability signals

Feature Envy is a static, structural signal rather than a runtime one; there
is no log line or metric that fires when a request is served by an envious
method, because the smell concerns where code lives, not what it does at
execution time. The relevant observability lives at the codebase level, not
the running system.

- A static analysis report (Reek's, JDeodorant's, or an equivalent) run
  periodically and tracked over time, so a team can see whether the count of
  flagged instances in a module is growing or shrinking release over release,
  the same way a team tracks test coverage or cyclomatic complexity trends.
- Churn correlated with cross-class reach. a version-control history tool
  that reports files most frequently changed together will often surface
  an envying method's file and its envied class's file as a tightly coupled
  pair, since a change to one routinely forces a change to the other; this is
  an indirect but real production signal, visible in the commit history
  itself rather than in application logs.
- Code review comment patterns. if reviewers repeatedly leave a comment
  along the lines of "should this live on Customer instead" across several
  unrelated pull requests touching the same class, that recurring review
  friction is itself an observability signal worth tracking, even informally,
  as a prompt to schedule a deliberate refactoring pass.

This entry deliberately reports no runtime telemetry for the smell, because
none exists. the signals above are the honest, complete list, per this
dimension's judgement labelling in dimension 17.

## 17. Security and privacy implications

This dimension is engineering judgement rather than a sourced claim, since no
cited authority makes security claims about a code-organization smell.

The direct security surface of Feature Envy is narrow. Moving a method from
one class to another does not, by itself, change what data is read, only
which class's method reads it, so the refactoring is not a privacy control by
itself.

Where a genuine implication does exist is at the boundary between an envying
method and an object that holds sensitive data it should not be exposing
broadly. If a class `B` holds personally identifiable information and exposes
public getters for every field specifically so that other classes can compute
things with that data, the resulting spread of Feature Envy instances across
the codebase is also a spread of code paths that can read that sensitive
data, each one a separate place that must be audited if the data's handling
requirements change (for example, a new requirement to redact a field in
logs). Consolidating those envying methods back onto `B` through Move Method
has a real, if secondary, security benefit. it reduces the number of distinct
code locations that directly touch the sensitive fields, which narrows the
audit surface for that data, even though the underlying data flow, something
somewhere still needs to read the field to do useful work, is unchanged.

The one place caution is genuinely warranted is when the envied object is
across a trust boundary, for example a value object deserialized directly
from an external API response. Moving business logic onto that object, rather
than onto an internal domain object that wraps it, can accidentally place
application logic in a class whose shape is dictated by an external
contract the team does not control, which then couples the business rule's
location to a schema that can change without the team's consent. This is a
variant of dimension 4's deliberate-module-boundary exception, restated here
because the consequence of getting it wrong is specifically a security and
maintainability risk, not only a coupling inconvenience.

## 18. References

1. Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
   edition, Addison-Wesley, 1999, chapter 3, "Bad Smells in Code", Feature
   Envy.
2. Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
   edition, Addison-Wesley, 2018, Move Function (recorded alias Move Method).
3. Martin Fowler, "CodeSmell", https://martinfowler.com/bliki/CodeSmell.html,
   verified 2026-08-02. Source for the attribution of the term "code smell"
   to Kent Beck.
4. Refactoring catalog, "Move Function", https://refactoring.com/catalog/,
   verified 2026-08-02. Source for Move Method as the recorded alias of Move
   Function, and for the "moving features" category grouping.
5. Reek project documentation, "Feature Envy",
   https://github.com/troessner/reek/blob/master/docs/Feature-Envy.md,
   verified 2026-08-02. Source for the operational definition used by an
   automated Ruby detector, and its worked `Warehouse#sale_price` example.
6. JDeodorant project repository, https://github.com/tsantalis/JDeodorant,
   verified 2026-08-02. Source for a real, maintained tool that detects
   Feature Envy in Java and proposes Move Method refactorings, originating
   from research by Nikolaos Tsantalis and Alexander Chatzigeorgiou.
7. Beaver Notes repository, commit
   a05218f9b279475f2d45f0b632c479326c98cd8, "refactor. consolidate note
   store, remove feature envy in FTS sync",
   https://github.com/Beaver-Notes/Beaver-Notes/commit/a05218f9b279475f2d45f0b632c479326c98cd8,
   verified 2026-08-02. Source for a real, shipping open-source codebase
   naming and fixing a Feature Envy instance.
8. DesigniteJava project repository,
   https://github.com/tushartushar/DesigniteJava, verified 2026-08-02.
   Consulted while researching dimension 9 to confirm which named smells
   that tool detects; Feature Envy is not among them, and this entry does
   not claim it is.

## Code examples

Three languages are shown, Python, TypeScript, and Go, since Feature Envy
translates identically across any class-based language and these three cover
a dynamically typed scripting language, a structurally typed transpiled
language, and a statically compiled language with no classical inheritance.
Java, Rust, and Swift are omitted here only because three languages already
demonstrate the refactoring is language-independent; the underlying move is
identical in each of them.

### Python

```python
class Customer:
    def __init__(self, name, discount_rate, loyalty_years, is_wholesale):
        self.name = name
        self.discount_rate = discount_rate
        self.loyalty_years = loyalty_years
        self.is_wholesale = is_wholesale


# Before. InvoicePrinter.price_for reaches into Customer's fields
# far more than it uses any state of its own. This is the smell.
class InvoicePrinterBefore:
    def price_for(self, customer, base_amount):
        rate = customer.discount_rate
        if customer.loyalty_years > 5:
            rate += 0.05
        if customer.is_wholesale:
            rate += 0.10
        rate = min(rate, 0.5)
        return round(base_amount * (1 - rate), 2)


# After. the pricing rule moved onto Customer, the class whose
# data it depends on. InvoicePrinter now delegates.
class Customer:
    def __init__(self, name, discount_rate, loyalty_years, is_wholesale):
        self.name = name
        self.discount_rate = discount_rate
        self.loyalty_years = loyalty_years
        self.is_wholesale = is_wholesale

    def price_for(self, base_amount):
        rate = self.discount_rate
        if self.loyalty_years > 5:
            rate += 0.05
        if self.is_wholesale:
            rate += 0.10
        rate = min(rate, 0.5)
        return round(base_amount * (1 - rate), 2)


class InvoicePrinterAfter:
    def price_for(self, customer, base_amount):
        return customer.price_for(base_amount)


if __name__ == "__main__":
    c = Customer("Acme", 0.05, 6, True)
    before = InvoicePrinterBefore().price_for(c, 200.0)
    after = InvoicePrinterAfter().price_for(c, 200.0)
    assert before == after == 160.0
    print(before, after)
```

Run with `python3 feature_envy.py`. Verified to print `160.0 160.0` on
CPython 3, no dependencies required.

### TypeScript

```typescript
class CustomerBefore {
  constructor(
    public name: string,
    public discountRate: number,
    public loyaltyYears: number,
    public isWholesale: boolean
  ) {}
}

// Before. InvoicePrinterBefore reaches into CustomerBefore's fields
// more than it uses any state of its own. This is the smell.
class InvoicePrinterBefore {
  priceFor(customer: CustomerBefore, baseAmount: number): number {
    let rate = customer.discountRate;
    if (customer.loyaltyYears > 5) rate += 0.05;
    if (customer.isWholesale) rate += 0.1;
    rate = Math.min(rate, 0.5);
    return Math.round(baseAmount * (1 - rate) * 100) / 100;
  }
}

// After. the pricing rule moved onto Customer, the class whose
// data it depends on. InvoicePrinter now delegates.
class Customer {
  constructor(
    public name: string,
    public discountRate: number,
    public loyaltyYears: number,
    public isWholesale: boolean
  ) {}

  priceFor(baseAmount: number): number {
    let rate = this.discountRate;
    if (this.loyaltyYears > 5) rate += 0.05;
    if (this.isWholesale) rate += 0.1;
    rate = Math.min(rate, 0.5);
    return Math.round(baseAmount * (1 - rate) * 100) / 100;
  }
}

class InvoicePrinterAfter {
  priceFor(customer: Customer, baseAmount: number): number {
    return customer.priceFor(baseAmount);
  }
}

const before = new InvoicePrinterBefore().priceFor(
  new CustomerBefore("Acme", 0.05, 6, true),
  200
);
const after = new InvoicePrinterAfter().priceFor(
  new Customer("Acme", 0.05, 6, true),
  200
);
if (before !== 160 || after !== 160) {
  throw new Error("mismatch");
}
console.log(before, after);
```

Compiled with `tsc --strict --target es2020` (TypeScript 7.0.2) and run with
`node`. Verified to print `160 160` with zero compiler errors under strict
mode.

### Go

```go
package main

import (
	"fmt"
	"math"
)

type Customer struct {
	Name         string
	DiscountRate float64
	LoyaltyYears int
	IsWholesale  bool
}

// Before. priceForBefore reaches into Customer's fields more than
// it uses any state of its own. This is the smell, expressed as a
// free function in a language with no classical inheritance.
func priceForBefore(c Customer, base float64) float64 {
	rate := c.DiscountRate
	if c.LoyaltyYears > 5 {
		rate += 0.05
	}
	if c.IsWholesale {
		rate += 0.10
	}
	rate = math.Min(rate, 0.5)
	return math.Round(base*(1-rate)*100) / 100
}

// After. the rule becomes a method on Customer, the type whose
// data it depends on. Go has no classes, so Move Method here
// means attaching the function to the type as its receiver.
func (c Customer) PriceFor(base float64) float64 {
	rate := c.DiscountRate
	if c.LoyaltyYears > 5 {
		rate += 0.05
	}
	if c.IsWholesale {
		rate += 0.10
	}
	rate = math.Min(rate, 0.5)
	return math.Round(base*(1-rate)*100) / 100
}

func main() {
	c := Customer{"Acme", 0.05, 6, true}
	before := priceForBefore(c, 200)
	after := c.PriceFor(200)
	if before != 160 || after != 160 {
		panic("mismatch")
	}
	fmt.Println(before, after)
}
```

Run with `go run feature_envy.go`. Verified to print `160 160` on the
installed Go toolchain, no dependencies required.
