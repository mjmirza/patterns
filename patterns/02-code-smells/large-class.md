---
name: Large Class
slug: large-class
family: 02-code-smells
category: Bloaters
aliases: [God Class, God Object, The Blob, Kitchen Sink Class, Swiss Army Knife Class]
first_described: "Fowler, Beck, Brant, Opdyke, Roberts 1999, Refactoring, Improving the Design of Existing Code"
maturity: canonical
related: [divergent-change, feature-envy, data-clumps, extract-class, move-method, facade, single-responsibility-principle, strategy, observer]
incompatible_with: []
verified: 2026-08-02
---

# Large Class

## 1. Name, aliases, and lineage

The canonical name is Large Class. It appears as one of the original code
smells in Martin Fowler, with Kent Beck, John Brant, William Opdyke, and Don
Roberts, *Refactoring, Improving the Design of Existing Code*, Addison-Wesley,
1999, Chapter 3, "Bad Smells in Code", in the section titled "Large Class".
The second edition of the book, published in 2018 with Kent Beck as co-author
for the JavaScript examples, keeps the same name and reorganizes the smell
catalogue into informal families. Large Class sits in the family commonly
labelled Bloaters, alongside Long Method, Long Parameter List, Primitive
Obsession, and Data Clumps. This family grouping is a widely used way of
summarizing the book's catalogue in secondary teaching resources and static
analysis documentation rather than a claim about the exact wording printed on
a page of the book itself, and it is presented here as engineering
categorization rather than an exact quotation.

The most common alias, by a wide margin, is God Class, sometimes written God
Object. The earliest formal use of this term traceable in this research is
Arthur J. Riel, *Object-Oriented Design Heuristics*, Addison-Wesley, 1996,
where Riel warns designers to be suspicious of an abstraction whose name
contains Driver, Manager, System, or Subsystem, because those names are a
symptom of a class that has absorbed responsibility that belongs to several
collaborators. Riel's heuristic and Fowler's Large Class describe the same
observable shape from two different angles. Riel's heuristic is a naming
smell that predicts the structural smell Fowler catalogues directly. A class
literally named `SystemManager` or `ApplicationDriver` is a strong leading
indicator that a Large Class diagnosis will follow once the file is opened.

A second alias with independent literature behind it is The Blob, from
William J. Brown, Raphael C. Malveau, Hays W. McCormick III, and Thomas J.
Mowbray, *AntiPatterns, Refactoring Software, Architectures, and Projects in
Crisis*, Wiley, 1998. The Blob is presented in that book as an
architecture-level antipattern rather than a code-level smell. it describes
the organizational and procedural forces that let one class accumulate
disproportionate responsibility over the lifetime of a project, alongside the
refactored solution and the process changes needed to prevent recurrence. The
Blob and Large Class describe the identical code shape. the difference
between the two sources is that Fowler's book stays at the level of a single
class and a mechanical refactoring recipe, while Brown and coauthors widen
the lens to the team habits, deadline pressure, and code review gaps that let
a Blob form and keep growing.

Kitchen Sink Class and Swiss Army Knife Class are informal terms encountered
in code review comments and conference talks. They are listed here as
observed usage, describing the same shape as a class whose public interface
reads as an unrelated grab bag of operations, and are not attributed to a
specific publication because none was found with an independently
verifiable, checkable claim of coining the term.

## 2. Problem and context

A class keeps absorbing new fields and new methods until it is doing the job
of what should have been five or six separate collaborators. The class
compiles. It runs. Every individual method inside it, read in isolation, is
often perfectly reasonable code. The problem is not any single method. the
problem is that the class as a whole answers to no single, coherent
description. Ask a team member what the class is for and they answer with a
list rather than a sentence. "It handles the user's session, formats the
receipt, talks to the payment gateway, writes the audit log, and also has the
retry logic for the email queue." A class whose purpose requires a list to
state is a class that has stopped having one purpose.

This happens for an ordinary and repeatable reason. Early in a project a
class such as `Order`, `User`, or `Report` is created to represent a real
concept in the domain. It starts with a handful of fields and a handful of
methods, and it is genuinely well designed at that size. Over the following
months, every new requirement finds this class as the path of least
resistance. The class already exists, it already has the object reference
passed around the codebase, and adding one more method to an existing class
is a smaller, lower-risk-looking diff than introducing a new type, wiring it
into the constructor of every caller, and updating the tests for all of
them. Each individual addition looks locally reasonable to the person making
it. None of them, on their own, looks like the moment the class crossed a
line. The line is crossed by accumulation, not by any single decision, which
is exactly what makes Large Class hard to catch in ordinary code review. A
diff that adds forty lines to an eight-hundred-line class reads as routine.
The same forty lines, if they had to justify creating a brand new
eight-hundred-and-forty-line class, would draw far more scrutiny.

The context in which this smell is dangerous, and in which the refactoring
that treats it is worth the cost, is a codebase under continued active
development, with more than one contributor, where the class in question sits
on a path that changes often. A twelve-hundred-line class that was written
once, is covered by tests, and never changes again is unpleasant to read but
is not actively costing the team money every sprint. A four-hundred-line
class that receives a commit from three different engineers most weeks, each
one touching an unrelated slice of its behaviour, is the situation Large
Class specifically diagnoses, because that is exactly the situation in which
merge conflicts, review friction, and accidental coupling between unrelated
features compound fastest.

## 3. Forces

Cohesion pulls one way, and the path of least resistance for the next
feature pulls the other. A class with one responsibility is easy to name,
easy to test in isolation, and easy to reason about because its fields all
serve the same purpose and its methods all read and write those same fields.
The moment a second, unrelated responsibility is added, cohesion drops, but
the change that added it was locally cheap, and the codebase does not stop
compiling to warn anyone.

Encapsulation and information hiding pull toward growth, not against it.
Adding a new private method or a new private field to an existing class is
invisible to every caller. it changes nothing about the public interface, so
it passes code review with far less scrutiny than a change that touches a
public contract. This is precisely backwards from where the risk lives.
Encapsulation successfully hides the fact that the class's internal
complexity has doubled, right up until the day someone has to read the whole
file to make a change.

Coupling and change frequency are the sharpest forces in play. A class that
does five unrelated things is touched for five unrelated reasons, so its
git-blame history mixes commits from every feature area that happens to
brush against it. This is the same underlying pressure that produces the
sibling smell Divergent Change, and the two are frequently the same class
observed from two different vantage points, as discussed under Related and
Incompatible Patterns below. High change frequency on one file means more
merge conflicts, more incidental review load on people who only care about
one of the five responsibilities, and a higher chance that a change intended
for responsibility A accidentally breaks responsibility B because the two
happen to share a field.

Cognitive load is the force a metric cannot see directly but that every
engineer who has opened one of these files feels immediately. A class with
forty methods and eighteen fields cannot be held in working memory. A
developer making a two-line change has to read past thirty-eight methods
that are irrelevant to their task to convince themselves they have not
missed a hidden dependency between the field they are about to touch and
some other unrelated feature. This tax is paid on every single change to the
file, for the entire remaining life of the class, by every person who
touches it.

Team topology and ownership pull against splitting the class, in practice
more than any technical force does. A class with unclear boundaries has, by
definition, unclear ownership. no single team or person feels responsible
for keeping it clean, because no single team or person can honestly claim it
represents only their concern. Splitting it into smaller, single-purpose
classes is also splitting it into pieces that different teams can each own
cleanly, but that reorganization itself has an upfront cost, and the team
under the most schedule pressure, which is usually the team least able to
absorb that cost, is also the team most likely to have produced the Large
Class in the first place.

Consistency and testability pull toward splitting, unambiguously. A class
mixing five responsibilities forces every unit test for any one of them to
set up state for all five, whether the test cares about the other four or
not. A test for the tax calculation inside an `Order` class that also owns
persistence and formatting has to either mock a database connection it does
not use, or accept a slower, more brittle integration-style test for logic
that should have been a two-line pure function test. Testability is the
force that most reliably surfaces the smell to a team, because it is the one
that shows up as a concrete, measurable cost, in test run time and in test
flakiness, well before anyone consciously names the design problem.

## 4. Applicability and non-applicability

Reach for the Large Class diagnosis, and the Extract Class family of
refactorings that treat it, in these situations.

- A class has grown past the point where a team member can describe its
  purpose in one sentence without using the word "and" more than once.
- Code review comments repeatedly ask "why does this class also do X" about
  a class whose name suggested it only does Y.
- The class is a frequent source of merge conflicts because unrelated
  features keep landing changes in the same file.
- Unit tests for one piece of the class's behaviour require setting up
  unrelated state that belongs to a different piece of behaviour.
- Static analysis or a metrics tool reports the class in the tail of the
  distribution for method count, field count, or lines of code relative to
  the rest of the codebase, and a human review of the flagged class
  confirms the responsibilities really are unrelated.
- The class name is generic in a way that hints at unbounded scope,
  `Manager`, `Handler`, `Processor`, `Service`, `Util`, `Helper`, with no
  further qualifier naming what specifically it manages, handles, or
  processes.
- Two different teams both need to change the same class for two entirely
  unrelated reasons in the same release cycle.

Do NOT reach for a Large Class refactoring in these situations, and treat
each reason as a real reason, not a excuse to defer needed work.

- The class is large because it is a data-holding record with many fields
  that genuinely belong together, such as a wide configuration object or a
  generated data transfer object mapping a wide external API response. Size
  alone, on a class with low behavioural complexity and high field cohesion,
  is closer to the sibling smell Data Class or is simply a genuinely
  wide but coherent record, not Large Class. Splitting a genuinely cohesive
  wide record into arbitrary pieces to satisfy a line count threshold
  produces worse code, not better code, because it destroys the one
  property, that every field belongs together, that made the class correct
  in the first place.
- The class is a generated artifact, a protocol buffer message class, an ORM
  entity generated from a database schema, or output from an interface
  definition language compiler. Refactoring generated code by hand is
  refactoring the generator's template, not the class, and if the generator
  itself cannot be reasonably changed, the class stays as it is and the
  smell, if there is one, is tolerated as a cost of the generation strategy.
- The class implements a genuinely cohesive algorithm that happens to be
  long, such as a single well-specified parsing state machine or a
  numerical routine translated faithfully from a published specification,
  where every method exists to serve the exact same single responsibility
  and splitting it would scatter one coherent algorithm across several
  files a reader has to reassemble mentally to understand any of it.
- The team is mid-migration, deliberately routing all new code through a
  temporary facade that is intentionally wide while the surrounding
  architecture is transitioned piece by piece, with a stated, tracked plan
  to shrink or retire the facade. Here the size is a known, temporary,
  managed cost, not an unmanaged accumulation, and treating it as an
  unplanned Large Class to fix immediately would fight the migration
  strategy rather than support it.
- The codebase is small, has one maintainer, is not expected to grow past
  its current scope, and the "large" class in question is genuinely the
  entire application. A hundred-line command line script does not need
  Extract Class applied to its one class merely because a linter default
  threshold flags it.
- Performance requirements in a specific, measured hot path genuinely
  benefit from keeping related data and behaviour physically co-located in
  one class to avoid extra indirection, virtual dispatch, or cache misses,
  and this benefit has been measured, not assumed. This is rare, and it
  applies to a narrow hot path, never to a whole application's general
  design, but where it genuinely applies it is a real, measurable reason to
  accept a wider class than the design would otherwise favour.

## 5. Structure

The Large Class smell, as a structural matter, is not a design pattern with named
collaborators the way a Chain of Responsibility or a Visitor has
collaborators. It is the absence of a needed decomposition. The structure
worth naming is what the class contains before treatment, and what the
Extract Class refactoring produces after treatment, because the "structure"
of this smell is best understood as the shape a healthy decomposition would
have had, measured against the shape that is actually present.

Before treatment, one class holds several unrelated clusters of state and
behaviour. Each cluster usually has an internally consistent story of its
own. a set of fields that are read and written together, and a set of
methods that operate on exactly those fields and largely ignore the other
fields in the class. The diagnostic technique of drawing a matrix of methods
against the fields each one touches, sometimes called a cohesion matrix or
informally "circling the clusters", makes this visible on paper even when it
is invisible while scrolling through the file top to bottom. A genuinely
cohesive class produces a matrix where almost every method touches almost
every field. A Large Class produces a matrix with two or more clearly
separated blocks, where the methods in block A never touch the fields that
only block B's methods touch, and vice versa.

After treatment, the participants are as follows. The Original Class is what
remains once the extracted responsibilities are removed, retaining only the
fields and methods for its one, now-nameable core responsibility, and
holding references to the newly extracted collaborators wherever it still
needs their behaviour. An Extracted Class is a new class created for each
coherent cluster identified in the cohesion matrix, owning the fields that
cluster used and exposing the methods that operated on them, under a name
that states its one responsibility plainly. A Delegating Method, where
needed, is a thin method left on the Original Class that forwards a call to
the corresponding Extracted Class, preserving the public interface for
existing callers during a staged migration rather than forcing every caller
to update in the same commit that performs the split.

## 6. ASCII structure diagram

```
Before, one class, several unrelated responsibility
clusters:

+---------------------------------------------+
| Order                                       |
| cluster A, pricing: lineItems, customerId,  |
| discountCode, taxRate, currency             |
| cluster B, fulfillment: shippingAddress,    |
| billingAddress, trackingNumber, carrier     |
| cluster C, notification: emailTemplate,     |
| smtpConfig                                  |
| cluster D, audit: auditLog                  |
|                                             |
| cluster A methods: calculateSubtotal(),     |
| applyDiscount(), calculateTax()             |
| cluster B methods: scheduleShipment(),      |
| assignCarrier()                             |
| cluster C methods: sendConfirmationEmail(), |
| sendShippingNotice()                        |
| cluster D methods: recordAuditEntry()       |
+---------------------------------------------+

After, Extract Class applied per cluster, Original
Class delegates:

+--------------------+
| Order (core state) |
+--------------------+
     | uses
     v
+-------------------------------+
| OrderPricer (cluster A logic) |
+-------------------------------+
+-------------------------------------+
| ShipmentScheduler (cluster B logic) |
+-------------------------------------+
+---------------------------------+
| OrderNotifier (cluster C logic) |
+---------------------------------+
+---------------------------------+
| OrderAuditLog (cluster D logic) |
+---------------------------------+

Order uses all four, each handling one cluster's
logic.
```

## 7. Dynamics

Before treatment, a caller obtains one `Order` instance and calls whichever
of its many methods the current use case needs. `checkout()` might call
`calculateSubtotal()`, `applyDiscount()`, `calculateTax()`,
`scheduleShipment()`, `sendConfirmationEmail()`, and `recordAuditEntry()` in
sequence, all against the one object, all sharing the same instance's
internal state, whether or not each step's logic actually needs the fields
another step wrote.

```
caller -> order.calculateSubtotal()
caller -> order.applyDiscount()
caller -> order.calculateTax()
caller -> order.scheduleShipment()
caller -> order.sendConfirmationEmail()
caller -> order.recordAuditEntry()

(all six calls share one object's internal state, whether or not
 each step's logic actually depends on the others' fields)
```

After treatment, the caller, or a coordinating method left on `Order`, calls
each collaborator for exactly the step it is responsible for, passing only
the data that step needs, usually the immutable, already-computed line
items and totals rather than the whole mutable `Order`.

```
caller -> pricer.priceOrder(lineItems, discountCode) -> priced total
caller -> scheduler.scheduleShipment(shippingAddress, priced total)
caller -> notifier.sendConfirmation(customerEmail, priced total)
caller -> auditLog.record(orderId, "checkout completed")

(each collaborator receives only the data it needs, and each call
 can be tested, mocked, and reasoned about independently of the others)
```

The runtime behaviour, the actual sequence of work performed and the final
state of the system, is unchanged by this refactoring when it is done
correctly. What changes is which object owns which piece of state during
that sequence, and therefore how many unrelated concerns a reader, a tester,
or a debugger has to hold in their head to follow any one step of it. This is
the general property of a well executed Extract Class refactoring, and
Fowler states this expectation directly as the governing constraint on every
refactoring in the catalogue, that a refactoring changes the internal
structure of code without changing its observable behaviour, per Fowler,
Beck, Brant, Opdyke, Roberts, *Refactoring*, Addison-Wesley, 1999, Chapter 2,
where the definition of refactoring itself is given.

## 8. Implementation variants

The mechanical core of treating Large Class, identify a coherent subset of
fields and methods and move them into a new class, appears differently
across languages and language styles, and the idiomatic shape a team should
reach for depends heavily on what the host language actually rewards.

In a class-based, single-inheritance object-oriented language such as Java
or C#, the standard variant is Extract Class followed by composition. the
new class is instantiated inside the original class, held as a private
field, and the original class's public methods that logically belong to the
extracted responsibility become thin delegating wrappers, or are removed
entirely once every caller has been migrated to call the new class directly.
Inheritance is deliberately avoided here. subclassing the god class to peel
off a responsibility only produces Refused Bequest and does not reduce
coupling, because the subclass still carries every field of the parent.

In a language with first-class functions and closures, such as JavaScript,
TypeScript, Python, or Go, a genuinely idiomatic alternative to a full class
extraction is to replace an internal cluster of methods with a free function
or a small set of free functions that take the data they need as explicit
parameters and return a result, rather than reading and writing shared
mutable class state. This variant trades the ceremony of a formal class for
a pure function, which is frequently the better trade for a cluster of logic
that has no internal state of its own beyond its inputs, such as
the tax calculation cluster in the running example above. Extract Class and
Extract Function, described in Martin Fowler's catalogue, are sibling
refactorings applied to the same underlying smell, and the choice between
them is a judgement call about whether the extracted responsibility carries
state that needs to persist across calls or is a stateless computation.

In Go specifically, the idiomatic variant departs from the class metaphor
entirely. Go has no classes, and a large struct with many methods attached
via method receivers is treated with the same diagnosis, but the fix
composes smaller structs as named fields inside the original struct, each
with its own small set of methods, and Go's implicit interface satisfaction
lets calling code depend on a narrow interface exposing only the subset of
behaviour it actually needs, rather than on the concrete wide struct. This
is closely related to the Interface Segregation Principle and is frequently
the more idiomatic Go fix even when the underlying diagnosis, too many
unrelated responsibilities on one type, is identical to the Java case.

In a language with mixins or traits, such as Ruby or Rust, a further
variant splits the responsibility into a trait or module that can be
composed into the type rather than requiring a fully separate collaborator
object reached through a field access. This keeps the call site syntax
`order.calculate_tax()` unchanged for callers while still physically
separating the fields and methods that belong to each responsibility into
their own trait or module definition, which is an improvement for
readability and for git history clarity even without changing the runtime
object graph.

Across every variant the underlying test for whether the extraction was done
correctly is unchanged. after the split, can each new piece be understood,
tested, and changed without reading or running the others. If the answer is
still no, the mechanics moved code around the file system without treating
the smell.

## 9. Known production uses

Named, independently checkable examples of Large Class in real, shipped,
widely deployed production systems, each verified directly against the
public source repository rather than against a secondary description.

The Android Open Source Project's `PackageManagerService.java`, in the
`frameworks/base` component of the platform, is the single class responsible
for installing, uninstalling, verifying, and querying every application
package on an Android device, alongside permission resolution and intent
filter matching for the whole system. Fetched directly from the GitHub
mirror of the AOSP source tree at
`https://api.github.com/repos/android/platform_frameworks_base/contents/services/core/java/com/android/server/pm/PackageManagerService.java`,
verified 2026-08-02, the file's reported size is 382,605 bytes, a single
Java source file for a single class, which places it firmly among the
largest individual class files in a widely deployed, actively developed
production codebase. Android's own platform engineering has split large
portions of package management responsibility into separate classes and
services across platform releases since the file's early history, which is
itself consistent with the treatment this entry describes, moving
responsibility out of one class and into focused collaborators over time,
though the file as it stands today remains a large, actively maintained
class by any reasonable measure.

Hibernate ORM's `SessionImpl.java`, in the `hibernate-core` module, is the
concrete class backing the `Session` interface that every application using
Hibernate interacts with, and it additionally implements several internal
service provider interfaces used by the persistence context, the event
system, and the JDBC coordination layer inside the framework itself.
Fetched directly from
`https://api.github.com/repos/hibernate/hibernate-orm/contents/hibernate-core/src/main/java/org/hibernate/internal/SessionImpl.java`,
verified 2026-08-02, the file's reported size is 92,027 bytes for one class.
This is a well known and frequently discussed case in the Java persistence
community precisely because `Session` is the primary public entry point of
a widely used object-relational mapper, so any responsibility added to
`SessionImpl` is added to the single class through which nearly every
application operation against the database flows.

Mozilla's Gecko browser engine, which powers Firefox, contains
`nsGlobalWindowInner.cpp`, in the `dom/base` component, implementing the
inner `Window` object exposed to web content, covering timers, storage
access, worker and service worker coordination, notification permissions,
and a large share of the DOM APIs a web page can call on `window`.
Fetched directly from
`https://api.github.com/repos/mozilla/gecko-dev/contents/dom/base/nsGlobalWindowInner.cpp`,
verified 2026-08-02, the file's reported size is 258,614 bytes for one C++
class implementation file. This is a C++ example rather than a
class-based-object-oriented-language example in the Java sense, but the
same diagnosis applies at the level of the class definition. one type is
the implementation surface for a very wide slice of what a web page is
permitted to do, and the file size is the direct, measurable consequence of
that breadth living in one class.

Beyond individual named files, the smell's prevalence beyond these three files is
independently evidenced by tooling built specifically to detect it across
arbitrary codebases. PMD, a widely used static analysis tool for Java,
ships a rule named `GodClass`, documented at
`https://docs.pmd-code.org/latest/pmd_rules_java_design.html`, verified
2026-08-02, which flags a class as a God Class when it simultaneously shows
high Weighted Method Count, high Access To Foreign Data, and low Tight
Class Cohesion, the same three metrics formalized by Michele Lanza and Radu
Marinescu in *Object-Oriented Metrics in Practice, Using Software Metrics to
Characterize, Evaluate, and Improve the Design of Object-Oriented Systems*,
Springer, 2006, in their published detection strategy for the God Class
antipattern. PMD ships two further, more mechanical rules in the same
document, `TooManyMethods`, with a default threshold of ten methods,
excluding simple getters and setters,, and `TooManyFields`, with a default threshold of fifteen non-static
non-final fields, both confirmed directly against the same page. That a
mainstream static analysis tool ships three separate, independently
configurable rules dedicated to this one smell, applied by default against
production codebases at organizations using PMD in continuous integration,
is itself evidence that the smell recurs often enough across the industry to
justify dedicated, maintained tooling rather than a one-off lint check.

## 10. Consequences

Positive consequences of the state Large Class describes, stated honestly,
because even a smell has a reason it kept happening. Consolidating related
operations into one class can reduce the number of objects a caller has to
wire together, which lowers the immediate, local friction of adding one more
small feature to code that already exists. It also means a caller only
needs to hold and pass around one reference rather than several, which in a
codebase without a dependency injection framework can genuinely reduce
constructor and parameter list churn in the short term. These are real
short-term wins, and they are exactly why the smell keeps recurring across
every codebase examined for dimension 9, not because engineers are careless
but because the local incentive genuinely points this way at each individual
decision point.

Negative consequences, which compound as the class grows and as the number
of contributors touching it grows, are more numerous and more expensive over
the life of the class. Testability degrades directly. a unit test for one
responsibility inside the class has to construct or mock the state needed by
every other responsibility the class also carries, even when the test under
that specific case does not exercise that other state, which slows down test
suites and increases the odds that an unrelated change breaks a test that
was never really testing the thing it claimed to test. Merge conflict rate
rises, because every contributor working on any of the class's several
responsibilities edits the same file, and version control conflict detection
operates at the level of overlapping lines, not overlapping intent, so two
unrelated changes to unrelated parts of a large file collide far more often
than the same two changes would collide if they lived in separate files.
Code review quality degrades, because a reviewer looking at a diff to one
responsibility inside a large class has to hold the entire class's other
responsibilities in mind to be confident the change has no unintended
interaction with shared state, which is a heavier cognitive task than
reviewers reliably perform under normal review time pressure, so review
quality quietly drops even though nobody made a conscious decision to review
less carefully. Reuse suffers, because a caller that genuinely only needs
one of the class's several responsibilities is forced to depend on, and
therefore couple to, the whole class, including the parts it does not use,
which in a statically compiled language can also mean recompiling and
redeploying code that depends on unrelated parts of the class whenever any
part of it changes. Onboarding cost rises for the same reason cognitive load
rises for existing contributors. a new engineer trying to understand one
feature has to read past every other feature crammed into the same file to
find the part that is actually relevant to their task.

## 11. Failure modes and misuse

**Symptom.** A small, focused two-line bug fix inside one method of the
large class unexpectedly breaks a completely unrelated feature that the
same class also happens to implement.
**Cause.** Two responsibility clusters inside the class share a field that
neither cluster's name or documentation suggests is shared, so a change
that appears, correctly, to affect only cluster A's logic actually also
changes state that cluster B silently depends on.
**Fix.** Draw the cohesion matrix described under Structure, above, to make
the hidden shared field visible on paper, then either genuinely separate
the two fields if they do not need to be the same value, or, if they
legitimately are the same underlying concept, extract that concept into its
own small collaborator that both clusters explicitly depend on rather than
implicitly sharing through class-level mutable state.

**Symptom.** Unit test suite for the class takes noticeably longer to run
than tests of similar size elsewhere in the codebase, and a large share of
individual test cases fail intermittently under parallel test execution.
**Cause.** Tests for unrelated responsibilities inside the same class are
sharing setup and teardown, or are mutating shared class-level or
instance-level state that other tests in the same file also read, producing
order-dependent test flakiness that would not exist if each responsibility
lived in its own class with its own, independent test fixture.
**Fix.** Extract each responsibility cluster into its own class first, then
split the test file to match. one test file per extracted class, each with
its own minimal fixture, generally resolves the flakiness because it
removes the accidental state sharing rather than merely masking it with
retries.

**Symptom.** A refactoring attempt that "fixes" Large Class produces several
smaller classes, but the number of parameters passed between them balloons,
and the code now reads as more confusing, not less, than the original single
class.
**Cause.** The extraction was done along an arbitrary boundary, often simply
splitting the file roughly in half by line count or method count, rather
than along the actual cohesion clusters identified by which fields each
method genuinely touches. This produces Feature Envy in the new classes,
where each extracted class constantly needs data that lives in one of the
sibling classes, and Long Parameter List, where that data has to be passed
explicitly at every call because it no longer lives inside one shared
object.
**Fix.** Revert the split and redo it starting from the cohesion matrix
rather than from a line count target. the boundary that matters is which
fields a method actually reads and writes, not the total size of the
resulting file.

**Symptom.** A team declares a class "refactored" because it now has fewer
public methods, but the class still has the same number of private helper
methods and the same number of fields as before, and the reported testing
and merge-conflict pain does not improve.
**Cause.** Methods were consolidated or made private rather than removed
from the class or genuinely moved to a new collaborator, which reduces the
surface area visible to a linter's method count rule without reducing the
actual number of unrelated responsibilities the class still carries.
Metrics-driven refactoring, done purely to satisfy a static analysis
threshold rather than to genuinely improve cohesion, is a common misuse of
the diagnosis, and it is worth naming directly as a failure mode of the
treatment, not only of the original code.
**Fix.** Measure the thing that actually matters, whether an engineer can
now describe the class's purpose in one sentence, and whether unrelated
features can now be tested and changed without touching this file, rather
than measuring only whether a metric threshold now reads green.

## 12. Trade-off matrix

Comparing a Large Class left untreated against the two named alternative
end states a team could deliberately choose instead, across the forces
named in dimension 3.

| Force | Large Class, untreated | Extract Class into focused collaborators | Extract Class into stateless functions |
|---|---|---|---|
| Cohesion | Low, several unrelated clusters share one namespace | High, each collaborator owns exactly one cluster's state and behaviour | High, but only for clusters with no persistent state of their own |
| Coupling at call sites | Low object count, but every caller couples to the whole class's interface | Callers couple only to the narrow collaborator they actually need | Callers couple only to a function signature, the lightest coupling of the three |
| Testability | Poor, tests for one responsibility require setup for all of them | Good, each collaborator is tested with its own minimal fixture | Best, pure functions need no fixture beyond their input arguments |
| Ceremony and boilerplate | Lowest, one constructor, one set of fields | Higher, each new class needs its own constructor and, in many languages, its own file | Lowest of the two refactored options, a function needs no class scaffolding at all |
| Suitability for stateful clusters | N/A, everything lives in the one class regardless of statefulness | Well suited, an object naturally models a cluster with internal state that persists across calls | Poorly suited, forcing persistent state through repeated function parameters is awkward and error-prone |
| Merge conflict rate | Highest, every unrelated feature edits the same file | Lower, each feature edits its own collaborator's file | Lowest, small pure functions are the least likely unit to be edited by two people at once |
| Onboarding cost | Highest, a reader must read the whole file to find their relevant part | Lower, a reader opens only the collaborator relevant to their task | Lowest, a function's name and signature are usually sufficient to understand its role without reading its neighbours |

## 13. Related and incompatible patterns

Divergent Change is Large Class's closest sibling, and in practice the two
are frequently diagnoses of the identical file, observed at different
moments in its life. Large Class describes the shape once it has already
happened, too much unrelated code in one place. Divergent Change describes
the ongoing symptom of that shape, the class keeps changing for many
different, unrelated reasons. A class that is repeatedly flagged for
Divergent Change in code review is, almost by definition, also a Large
Class, and the treatment for both is the same Extract Class refactoring
applied along the cohesion boundaries the symptom reveals.

Feature Envy frequently appears as a direct consequence of an Extract Class
refactoring performed carelessly, as described under Failure Modes above.
if the extraction boundary is drawn along the wrong line, the newly
extracted class ends up needing data that still lives on the original
class, or on a sibling extracted class, producing exactly the symptom
Feature Envy names, a method that is more interested in another class's
data than in its own.

Data Clumps is the smell most easily confused with Large Class on a
surface read, because both involve a class or a parameter list that
looks unusually wide. The distinction that matters is behavioural cohesion,
not size. A Data Clumps situation is several separate fields or parameters
that always travel together and should be consolidated into one small
value object. A Large Class situation is the opposite direction of
movement, one class holding too many things that should be pulled apart.
Confusing the two leads to exactly the wrong fix in each direction, merging
a Large Class further, or splitting a legitimate Data Clumps value object
into pieces that then have to be passed around separately again.

Extract Class, Move Method, and Move Field, all catalogued by Fowler in the
same 1999 book, are the direct mechanical refactorings that treat Large
Class. Extract Class creates the new collaborator. Move Method and Move
Field relocate the specific members that belong to the newly identified
responsibility, and are usually applied repeatedly, one member at a time,
as the safest way to perform the split incrementally with a passing test
suite at every step rather than as one large, risky rewrite commit.

Facade is a pattern that, applied incorrectly, is sometimes mistaken for a
fix to Large Class when it is not one. A Facade class that simply wraps and
forwards calls to the still-monolithic original class without actually
moving any state or behaviour out of it hides the smell from callers
without treating the smell itself. the original class is still large, still
hard to test in isolation, and still a merge conflict magnet for anyone
who has to change its internals. Facade is the right pattern to apply on
top of a fully completed Extract Class refactoring, to give external
callers one simple entry point across several now-separate collaborators,
but it is not a substitute for performing the extraction.

Strategy and Observer are patterns that frequently emerge naturally once a
Large Class is correctly split, because several of the extracted
responsibility clusters often turn out to be variations on a theme, several
different ways to calculate tax for different jurisdictions, or several
different notification channels that all need to be told when an order
completes, and Strategy or Observer becomes the natural next step for
organizing the now-separate collaborators rather than something that needed
to be designed in from the start.

The Single Responsibility Principle, as formulated by Robert C. Martin,
*Agile Software Development, Principles, Patterns, and Practices*, Prentice
Hall, 2002, in the chapter introducing the principle, is the design
principle whose sustained violation produces Large Class as its observable
symptom. A class following the Single Responsibility Principle from the
start is, definitionally, resistant to becoming a Large Class over time,
because each new requirement that does not belong to the class's one stated
reason to change has nowhere convenient to attach itself.

No pattern in this catalogue is incompatible with Large Class in the sense
of actively conflicting with the diagnosis. it is a smell, not a design
choice competing with other design choices, so there is nothing to list
under incompatible patterns beyond noting, again, the non-applicability
cases already covered under dimension 4, where the apparent size is not
actually the smell being described.

## 14. Refactoring path in and out

Introducing the fix into an existing codebase that does not yet have it
follows a fixed, incremental sequence that keeps the test suite passing at
every step rather than requiring one large, risky rewrite.

First, build the cohesion matrix described under Structure, listing every
method down one axis and every field across the other, marking which
methods touch which fields. This can be done by hand for a class under a
few hundred lines, or with a simple script for larger classes, and it is
the step that turns a vague feeling that "this class does too much" into a
concrete, defensible list of the specific responsibility clusters present.

Second, for the smallest, most clearly separated cluster identified in the
matrix, create a new class named for exactly that one responsibility.
Resist the temptation to name it generically. a name like `OrderHelper` or
`OrderUtil` for the new class reproduces the same underlying problem one
level down, because it does not commit to a single, statable purpose.

Third, apply Move Field for each field that belongs to the chosen cluster,
moving it from the original class to the new class, and apply Move Method
for each method that operates primarily on those fields, one member at a
time, running the full test suite after every single move. Fowler's own
guidance in the 1999 book stresses this member-at-a-time discipline
specifically because it keeps every individual step small enough to be
trivially reversible if a test fails, rather than accumulating a large,
hard-to-debug diff before the first test run.

Fourth, where existing callers still call the original class's now-removed
methods, leave a temporary delegating method on the original class that
forwards the call to the new collaborator, so the public interface callers
depend on does not break in the same commit that performs the internal
reorganization. Update callers to call the new collaborator directly over
subsequent, smaller commits, and remove the delegating method only once no
caller depends on it any longer.

Fifth, repeat steps two through four for each remaining cluster identified
in the original matrix, checking after each cluster is extracted whether
the original class's purpose can now be stated in one sentence. Stop once
it can. not every Large Class needs to be split into as many pieces as
there were rows in the original matrix. some clusters legitimately belong
together as the class's genuine, narrowed-down core responsibility.

Removing the pattern, in the rare case a team has over-split a class and
wants to walk part of the decomposition back, generally means applying
Inline Class, the direct inverse of Extract Class from the same Fowler
catalogue, to merge a collaborator back into its caller when it turns out
the collaborator never developed a second caller and never developed
real independent behaviour of its own, so the extra indirection was
paying for a flexibility the codebase never actually used. This is a valid,
occasionally correct move, and treating every extracted class as
permanently untouchable is its own mistake, a smaller instance of the same
over-decomposition risk named under Failure Modes above.

## 15. Testing and verification

Testing code that has been through a correct Extract Class refactoring
becomes easier along a specific, measurable axis. each extracted
collaborator can be given its own unit test file with its own minimal
fixture, exercising only the state and behaviour that collaborator actually
owns, without constructing or mocking the state that belonged to sibling
responsibilities before the split. This is the single most reliable
practical signal that an extraction was drawn along the right boundary. if,
after the split, a test for one extracted class still needs to construct or
mock a large slice of state belonging to a different extracted class, the
boundary was drawn in the wrong place, as described under Failure Modes.

Testing the class before it is split, while the smell is still present,
requires a different, more defensive discipline, since a full rewrite
before any tests exist at all is the highest-risk way to treat a Large
Class. The recommended technique, consistent with the general
characterization-testing approach used before any risky refactoring on
legacy code, is to write broad, black-box tests against the class's
existing public interface first, exercising its observable behaviour end to
end without attempting to test its internals in isolation, and only then
begin the incremental extraction described under dimension 14, re-running
this same characterization suite after every single member move to confirm
observable behaviour genuinely has not changed. Fowler's own definition of
refactoring, cited under Dynamics above, makes this the correct standard to
hold every intermediate step to, not merely the final result.

Test doubles play a different role before and after the split. Before the
split, mocking any one dependency of the Large Class, its database
connection, its email client, its logging sink, tends to require a wide
mock covering every dependency the whole class touches, because a single
test exercising even one responsibility cluster frequently triggers code
paths belonging to another cluster through shared setup. After the split,
each extracted collaborator usually needs at most one or two narrow test
doubles corresponding to its own genuinely external dependencies, which is
both faster to write and far more resistant to becoming stale as the
collaborator's neighbours change independently of it.

Integration tests exercising the full, multi-collaborator flow after a
split remain necessary and should not be discarded merely because the
individual collaborators now have good unit test coverage. the split
introduces new seams, the calls between the original class and its
extracted collaborators, and those seams are exactly the place a correct
unit-level split can still hide a wiring mistake, a collaborator
constructed with the wrong dependency, or a delegating method forwarding to
the wrong new method name. at least one integration test covering the
full checkout flow
covering the overall use case the original class served should survive the
refactoring unchanged, and should pass both before and after every
intermediate step, as the outer safety net around the finer-grained unit
tests being added at each step.

## 16. Observability signals

In a running system, a Large Class rarely produces a distinctive runtime
signal of its own, because the smell is a structural, source-level property
rather than a behaviour that manifests as a distinct log line or metric at
execution time. The observability signals worth watching for this smell
therefore live primarily in the development and delivery pipeline rather
than in production telemetry, though a small number of production-adjacent
signals do correlate with it.

Static analysis metrics computed on every build are the primary,
direct-measurement signal, and are the same class of tool discussed under
Known Production Uses. PMD's `TooManyMethods` and `TooManyFields` rules,
with their default thresholds of ten methods and fifteen fields
respectively, confirmed at
`https://docs.pmd-code.org/latest/pmd_rules_java_design.html`, verified
2026-08-02, give a cheap, continuously computed leading indicator that can
be wired into continuous integration and tracked as a trend over time per
file, per module, or per team, rather than only checked as a pass or fail
gate on individual pull requests. A healthy trend line for these metrics,
tracked across a codebase over months, is flat or slowly declining as
extractions are performed. an unhealthy trend line climbs steadily,
indicating new responsibility is being added to existing large classes
faster than it is being extracted.

Git history metadata is a strong, freely available secondary signal that
does not require running any additional tooling beyond version control
already in use. The number of distinct authors who have committed to a
given file within a rolling window, combined with the file's current size,
correlates well in practice with the presence of Large Class or its sibling
Divergent Change, because a genuinely single-responsibility class is
naturally touched by a narrower, more consistent set of contributors than a
class serving several unrelated features. Several open source tools compute
this "code ownership" or "truck factor" style metric directly from commit
history without needing access to running production systems at all.

Code review latency and merge conflict rate, tracked per file rather than
only in aggregate across a repository, is a delivery-pipeline signal
available from most source control platforms' pull request data. a file
that consistently shows above-average time-to-merge and above-average
conflict rate relative to its size is a strong candidate for the smell,
because both of those costs are direct, named consequences of the smell
under dimension 10.

Test suite execution time and flakiness rate, broken down per test file
rather than only reported as an aggregate suite total, is the signal most
directly tied to the concrete, measurable pain described under
Consequences and under Failure Modes above. A disproportionately slow or
disproportionately flaky test file, relative to the size and nature of the
class it is testing, is worth investigating as a Large Class candidate even
before any static analysis tool flags the underlying class directly,
because test symptoms frequently surface before a human notices the
underlying design problem in code review.

A healthy instance, once treated, looks like several smaller files, each
with a narrower, more stable set of committing authors, each showing test
run times proportional to its own small scope, and each showing merge
conflict rates near the codebase's baseline rather than in its tail. An
untreated or worsening instance looks like one file climbing steadily on
every one of these axes at once, month over month, which is the pattern
worth alerting a team lead to well before the file becomes painful enough
that everyone already knows about it informally.

## 17. Security and privacy implications

This dimension is substantially engineering judgement rather than sourced
fact, because the security literature discusses attack surface and privacy
boundaries directly, but does not, in the sources checked for this entry,
discuss Large Class as a named code smell with a dedicated security
analysis of its own. The reasoning below follows directly from established,
general security principles applied to the specific structural shape this
entry describes.

A Large Class widens the attack surface reachable through one point of
entry, in a way a narrower class does not. If a class implements
authentication, session management, and unrelated business logic together,
a vulnerability discovered anywhere in that class, including in code paths
that have nothing to do with authentication, is discovered inside the same
trust boundary as the authentication logic. A memory safety bug, an
injection flaw, or a logic error in the unrelated business logic portion of
the class can potentially be exploited to reach or corrupt state that the
authentication portion of the same class depends on, purely because both
live in the same object with shared, mutable internal state and no
enforced boundary between them. Splitting the responsibilities into
separate classes, each with its own narrower internal state, does not make
either piece of code bug free, but it does shrink the blast radius any
single bug in either piece can reach, because the two pieces no longer
share mutable state by default.

Privacy-sensitive data handling is similarly easier to audit and easier to
get right in a narrowly scoped class than in a wide one. A class that
handles, among several other unrelated responsibilities, personally
identifiable information belonging to a user, is harder to review for
correct data handling, correct retention, and correct redaction in logs
and error messages, than a class whose sole responsibility is handling that
specific category of sensitive data. A reviewer or an automated data flow
analysis tool auditing a codebase for where personal data is read, written,
or logged has a much narrower, more tractable surface to examine when that
data's handling is concentrated in a small number of purpose-built classes
rather than scattered across the incidental corners of several unrelated
Large Classes throughout the codebase.

Least privilege, applied at the code structure level rather than only at
the infrastructure level, is directly supported by the treatment this entry
describes. a narrowly scoped collaborator class can be given, in principle,
exactly the dependencies and exactly the data access it needs to perform
its one responsibility, and no more, whereas a Large Class, by virtue of
holding many unrelated responsibilities in one object, tends to accumulate
many unrelated dependencies and many unrelated pieces of data access on one
object, making it harder to reason about, or to enforce
through code review, whether any given piece of that class's code is only
touching the data and services it genuinely needs.

None of this suggests Large Class is itself a vulnerability, and it is
important not to overstate the connection. a well tested, carefully
reviewed Large Class can be entirely secure, and a small, narrowly scoped
class can still contain a serious flaw. The relationship described here is
one of surface area and auditability, not one of direct causation, and it
is presented as reasoning a security-conscious reviewer can apply, not as a
claim independently established in the cited security literature for this
specific named code smell.

## Code examples

### Python

Runnable with `python3`. Demonstrates the smell, one `Order` class handling
pricing, shipment scheduling, notification, and audit logging, followed by
the treated version using four focused collaborators.

```python
# Before: Large Class. One object owns four unrelated responsibilities.
class Order:
    def __init__(self, line_items, discount_code, shipping_address, email):
        self.line_items = line_items
        self.discount_code = discount_code
        self.shipping_address = shipping_address
        self.email = email
        self.audit_entries = []

    def calculate_subtotal(self):
        return sum(price for _, price in self.line_items)

    def apply_discount(self, subtotal):
        return subtotal * 0.9 if self.discount_code == "SAVE10" else subtotal

    def calculate_tax(self, amount):
        return round(amount * 0.08, 2)

    def schedule_shipment(self):
        return f"Shipment scheduled to {self.shipping_address}"

    def send_confirmation_email(self, total):
        return f"Emailed {self.email}: total is {total}"

    def record_audit_entry(self, message):
        self.audit_entries.append(message)


def checkout_before(order):
    subtotal = order.calculate_subtotal()
    discounted = order.apply_discount(subtotal)
    total = discounted + order.calculate_tax(discounted)
    print(order.schedule_shipment())
    print(order.send_confirmation_email(total))
    order.record_audit_entry(f"checkout completed, total={total}")
    return total


# After: Extract Class applied. Each collaborator owns one responsibility.
class OrderPricer:
    def price(self, line_items, discount_code):
        subtotal = sum(price for _, price in line_items)
        discounted = subtotal * 0.9 if discount_code == "SAVE10" else subtotal
        return round(discounted + discounted * 0.08, 2)


class ShipmentScheduler:
    def schedule(self, shipping_address):
        return f"Shipment scheduled to {shipping_address}"


class OrderNotifier:
    def send_confirmation(self, email, total):
        return f"Emailed {email}: total is {total}"


class OrderAuditLog:
    def __init__(self):
        self.entries = []

    def record(self, message):
        self.entries.append(message)


class OrderAfter:
    def __init__(self, line_items, discount_code, shipping_address, email):
        self.line_items = line_items
        self.discount_code = discount_code
        self.shipping_address = shipping_address
        self.email = email


def checkout_after(order, pricer, scheduler, notifier, audit_log):
    total = pricer.price(order.line_items, order.discount_code)
    print(scheduler.schedule(order.shipping_address))
    print(notifier.send_confirmation(order.email, total))
    audit_log.record(f"checkout completed, total={total}")
    return total


if __name__ == "__main__":
    items = [("widget", 10.0), ("gadget", 25.0)]
    before = Order(items, "SAVE10", "1 Main St", "a@example.com")
    print("before total:", checkout_before(before))

    after = OrderAfter(items, "SAVE10", "1 Main St", "a@example.com")
    result = checkout_after(
        after, OrderPricer(), ShipmentScheduler(), OrderNotifier(), OrderAuditLog()
    )
    print("after total:", result)
```

### TypeScript

Compiled with `tsc` and run with `node`. Same before/after shape applied to
a user account class mixing authentication, profile updates, and
notification.

```typescript
// Before: Large Class. Authentication, profile, and notification in one place.
class UserAccountManager {
  passwordHash: string;
  displayName: string;
  email: string;
  loginAttempts: number = 0;

  constructor(passwordHash: string, displayName: string, email: string) {
    this.passwordHash = passwordHash;
    this.displayName = displayName;
    this.email = email;
  }

  checkPassword(hash: string): boolean {
    this.loginAttempts += 1;
    return hash === this.passwordHash;
  }

  updateDisplayName(name: string): void {
    this.displayName = name;
  }

  notifyProfileChanged(): string {
    return `Notice sent to ${this.email}: profile updated`;
  }
}

// After: Extract Class applied. Each collaborator owns one responsibility.
class Authenticator {
  checkPassword(storedHash: string, attemptedHash: string): boolean {
    return storedHash === attemptedHash;
  }
}

class ProfileService {
  updateDisplayName(profile: { displayName: string }, name: string): void {
    profile.displayName = name;
  }
}

class Notifier {
  notifyProfileChanged(email: string): string {
    return `Notice sent to ${email}: profile updated`;
  }
}

interface UserAccount {
  passwordHash: string;
  displayName: string;
  email: string;
}

function updateProfileAfter(
  account: UserAccount,
  newName: string,
  auth: Authenticator,
  profiles: ProfileService,
  notifier: Notifier,
  attemptedHash: string
): boolean {
  if (!auth.checkPassword(account.passwordHash, attemptedHash)) {
    return false;
  }
  profiles.updateDisplayName(account, newName);
  console.log(notifier.notifyProfileChanged(account.email));
  return true;
}

const before = new UserAccountManager("abc123", "Alice", "alice@example.com");
console.log("before check:", before.checkPassword("abc123"));
before.updateDisplayName("Alice B");
console.log(before.notifyProfileChanged());

const after: UserAccount = {
  passwordHash: "abc123",
  displayName: "Alice",
  email: "alice@example.com",
};
const ok = updateProfileAfter(
  after,
  "Alice B",
  new Authenticator(),
  new ProfileService(),
  new Notifier(),
  "abc123"
);
console.log("after updated:", ok, after.displayName);
```

### Go

Runnable with `go run`. Go has no classes, so the idiomatic variant, noted
under Implementation Variants, composes smaller structs instead of a class
hierarchy.

```go
package main

import "fmt"

// Before: one wide struct with methods covering unrelated responsibilities.
type OrderGod struct {
	LineItems       []float64
	DiscountCode    string
	ShippingAddress string
	Email           string
}

func (o *OrderGod) Subtotal() float64 {
	total := 0.0
	for _, price := range o.LineItems {
		total += price
	}
	return total
}

func (o *OrderGod) ScheduleShipment() string {
	return fmt.Sprintf("Shipment scheduled to %s", o.ShippingAddress)
}

func (o *OrderGod) NotifyConfirmation(total float64) string {
	return fmt.Sprintf("Emailed %s: total is %.2f", o.Email, total)
}

// After: composition of small, focused, single-responsibility structs.
type Pricer struct{}

func (Pricer) Price(lineItems []float64, discountCode string) float64 {
	subtotal := 0.0
	for _, price := range lineItems {
		subtotal += price
	}
	if discountCode == "SAVE10" {
		subtotal *= 0.9
	}
	return subtotal
}

type Scheduler struct{}

func (Scheduler) Schedule(address string) string {
	return fmt.Sprintf("Shipment scheduled to %s", address)
}

type Notifier struct{}

func (Notifier) Confirm(email string, total float64) string {
	return fmt.Sprintf("Emailed %s: total is %.2f", email, total)
}

type Order struct {
	LineItems       []float64
	DiscountCode    string
	ShippingAddress string
	Email           string
}

func Checkout(o Order, p Pricer, s Scheduler, n Notifier) float64 {
	total := p.Price(o.LineItems, o.DiscountCode)
	fmt.Println(s.Schedule(o.ShippingAddress))
	fmt.Println(n.Confirm(o.Email, total))
	return total
}

func main() {
	before := &OrderGod{
		LineItems:       []float64{10.0, 25.0},
		DiscountCode:    "SAVE10",
		ShippingAddress: "1 Main St",
		Email:           "a@example.com",
	}
	fmt.Println(before.ScheduleShipment())
	fmt.Println(before.NotifyConfirmation(before.Subtotal()))

	after := Order{
		LineItems:       []float64{10.0, 25.0},
		DiscountCode:    "SAVE10",
		ShippingAddress: "1 Main St",
		Email:           "a@example.com",
	}
	total := Checkout(after, Pricer{}, Scheduler{}, Notifier{})
	fmt.Printf("after total: %.2f\n", total)
}
```

All three samples above were compiled or run directly during the authoring
of this entry. Python executed with `python3`, printing before and after
totals. TypeScript compiled cleanly with `npx tsc` and the resulting
JavaScript ran with `node`, printing the same style of before and after
output. Go compiled and ran with `go run`, printing shipment, notification,
and total lines for both the wide struct and the composed version. No
sample required a modification after the first attempt to run.

## 18. References

1. Martin Fowler, with Kent Beck, John Brant, William Opdyke, and Don
   Roberts, *Refactoring, Improving the Design of Existing Code*,
   Addison-Wesley, 1999, Chapter 3, "Bad Smells in Code", section "Large
   Class", and Chapter 2 for the definition of refactoring as
   behaviour-preserving structural change.
2. Martin Fowler, with Kent Beck, *Refactoring, Improving the Design of
   Existing Code*, second edition, Addison-Wesley, 2018, retaining the
   Large Class smell and its treatment under the reorganized catalogue.
3. Arthur J. Riel, *Object-Oriented Design Heuristics*, Addison-Wesley,
   1996, heuristic warning against classes named Driver, Manager, System,
   or Subsystem, the earliest formal source found for the God Class term.
   Referenced via https://en.wikipedia.org/wiki/God_object, verified
   2026-08-02.
4. William J. Brown, Raphael C. Malveau, Hays W. McCormick III, and Thomas
   J. Mowbray, *AntiPatterns, Refactoring Software, Architectures, and
   Projects in Crisis*, Wiley, 1998, the Blob antipattern. Author and year
   confirmed via https://openlibrary.org/search.json?q=AntiPatterns+Refactoring+Software+Architectures+Projects+Crisis, verified 2026-08-02.
5. Robert C. Martin, *Agile Software Development, Principles, Patterns, and
   Practices*, Prentice Hall, 2002, chapter introducing the Single
   Responsibility Principle.
6. Michele Lanza and Radu Marinescu, *Object-Oriented Metrics in Practice,
   Using Software Metrics to Characterize, Evaluate, and Improve the
   Design of Object-Oriented Systems*, Springer, 2006, the God Class
   detection strategy using Weighted Method Count, Access To Foreign Data,
   and Tight Class Cohesion. Title, authors, publisher, and year confirmed
   via search, verified 2026-08-02.
7. PMD documentation, "Java Design rules", `GodClass`, `TooManyMethods`,
   `TooManyFields`. https://docs.pmd-code.org/latest/pmd_rules_java_design.html,
   verified 2026-08-02.
8. Android Open Source Project, `PackageManagerService.java`, GitHub mirror
   of `frameworks/base`.
   https://api.github.com/repos/android/platform_frameworks_base/contents/services/core/java/com/android/server/pm/PackageManagerService.java,
   verified 2026-08-02, reported size 382,605 bytes.
9. Hibernate ORM, `SessionImpl.java`, `hibernate-core` module.
   https://api.github.com/repos/hibernate/hibernate-orm/contents/hibernate-core/src/main/java/org/hibernate/internal/SessionImpl.java,
   verified 2026-08-02, reported size 92,027 bytes.
10. Mozilla Gecko, `nsGlobalWindowInner.cpp`, `dom/base` component.
    https://api.github.com/repos/mozilla/gecko-dev/contents/dom/base/nsGlobalWindowInner.cpp,
    verified 2026-08-02, reported size 258,614 bytes.
