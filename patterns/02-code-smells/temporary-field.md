---
name: Temporary Field
slug: temporary-field
family: 02-code-smells
category: Object-Orientation Abusers
aliases: [Temporary Attribute, Sometimes Field, Optional Field]
first_described: "Fowler, Beck, Brant, Opdyke, Roberts 1999, Refactoring, Improving the Design of Existing Code"
maturity: canonical
related: [data-class, lazy-class, feature-envy, long-method, extract-class]
incompatible_with: []
verified: 2026-08-02
---

# Temporary Field

## 1. Name, aliases, and lineage

The canonical name is Temporary Field. It is one of the twenty two named
code smells catalogued in the 1999 book Refactoring, Improving the Design
of Existing Code by Martin Fowler, with contributions credited to Kent
Beck, John Brant, William Opdyke, and Don Roberts, published by
Addison-Wesley. The book places it inside the chapter that teaches a
reader to recognise problems before teaching the mechanical steps that fix
them, and it groups Temporary Field with the smells that flag object
design abuse rather than raw bloat or raw duplication. Independent
secondary sources that catalogue Fowler's smell list use the same name and
attribute it to the same source. SourceMaking's refactoring catalogue
entry, "Temporary Field", opens with the line "Temporary fields get their
values (and thus are needed by objects) only under certain circumstances.
Outside of these circumstances, they are empty",
https://sourcemaking.com/refactoring/smells/temporary-field, verified
2026-08-02, and attributes the term to the Fowler catalogue. No competing
attribution exists in the literature.

Two aliases circulate informally rather than by independent naming
credit. Temporary Attribute is used interchangeably in code review
discussions, since field and attribute are synonyms in most
object-oriented vocabularies. Sometimes Field describes the same shape
from the reader's point of view, a field that only sometimes holds a
value rather than an empty or default one, and this phrasing is used
deliberately in this entry's own prose below because it names the
observable symptom rather than the mechanism. Neither alias carries a
separate citation of its own; both are recorded here as observed usage,
in the same spirit as the Data Clumps entry in this repository records
Shotgun Parameter List as a team habit rather than a sourced term.

The smell should not be confused with two neighbours it is frequently
mistaken for. It is not the same as a nullable field that is genuinely
optional domain data, for example a `middleName` on a `Person` that some
people simply do not have. A nullable domain field represents a fact about
the entity that is permanently and validly absent for some instances. A
temporary field represents scratch state belonging to one operation, that
happens to have been placed on the object instead of passed as a
parameter or return value, and that carries no value before that
operation runs and a stale one after it finishes. The distinction matters
for every dimension that follows, and dimension 4 gives it a dedicated
test.

## 2. Problem and context

The smell appears when a class has a method that implements a complex,
multi-step algorithm, and that algorithm needs several intermediate values
threaded through more than one private helper method. The author of the
class faces a real and common temptation at this point. Passing five or
six intermediate values as parameters to three or four helper methods
produces long, ugly parameter lists, and the temptation is to shortcut the
problem by storing those intermediate values as instance fields instead.
The helper methods then read and write the fields directly, and the
parameter lists shrink back down to nothing. The code compiles, the
algorithm runs, and the class now looks tidy at each individual method
signature.

The cost of that shortcut is paid somewhere else. The class's field list
now contains two different kinds of state living side by side with no
marker to distinguish them. Some fields hold state that is valid for the
entire lifetime of the object, set in the constructor or by an explicit
setter, and any method can trust them at any time. Other fields hold state
that is valid only during one call to one particular method, carrying no
useful value before that call starts, and stale garbage after it
finishes. A reader looking at the field declarations at the top of the
class cannot tell which is which without reading every method body.
Fowler's own catalogue description gives the compact test that captures
the resulting confusion. outside the circumstances in which the temporary
field is set, it is empty, and a reader has no way to know from the
field's declaration alone what those circumstances are,
https://sourcemaking.com/refactoring/smells/temporary-field, verified
2026-08-02.

A second, related context produces the same smell from a different
direction. A class represents a general concept, but a small subset of the
values that concept can take needs extra fields that only make sense for
that subset. An `Order` class carries an `expeditedCarrier` field and an
`expeditedTrackingUrl` field that are null for the overwhelming majority
of orders and populated only when the order happens to be an expedited
one. Here the fields are not scratch state for one method call, they are
state that is permanently attached to only some instances of the class for
the whole lifetime of those instances, but the smell reads the same way to
a caller. A field on the class that is empty for most instances forces
every piece of code that touches the class to reason about whether this
particular instance is one of the ones where the field is populated. This
entry treats the two contexts as one smell because the observable symptom
and the mechanical fixes overlap heavily, and calls out where they diverge
in dimension 8 and dimension 11.

Both contexts share the same underlying pressure. The class already
exists, it is convenient to add one more field to it, and adding a field
is a smaller, more local edit than introducing a new type. The smell is
therefore, like several of its neighbours in the Fowler catalogue, a
signal about incremental accretion under time pressure as much as it is a
signal about the code's current shape.

## 3. Forces

**Cohesion.** Sacrificed by the smell, favoured by the fix. Cohesion, in
the sense measured informally by asking whether most methods on a class
use most of the class's fields, drops whenever a subset of fields is
touched only by a subset of methods. A class with three long-lived fields
used everywhere and four temporary fields used only inside one algorithm
has effectively become two classes wearing one name, and every method that
does not need the temporary fields still pays the cost of a class that
looks larger and more entangled than it is.

**Parameter-list length.** The smell trades a long parameter list for a
field list, favouring apparent method-signature tidiness at the direct
expense of cohesion. This is the central and most honest trade the smell
makes. A helper method that needs five values genuinely does have a long
signature if those values are passed as parameters, and the field-based
shortcut removes that visible ugliness by hiding the same coupling inside
the class body instead of in the method signature.

**Correctness under reuse and concurrency.** Heavily sacrificed. A
temporary field that is not reset between calls carries state from one
invocation into the next. On a single-threaded object reused across
several calls to the same algorithm, a code path in the second call that
never re-sets the field can silently read the value the first call left
behind. On an object shared across threads, or exposed as a
request-scoped bean that a container may reuse, the same field becomes a
live data race, because two overlapping invocations write to the same
storage location that was never designed to be invocation-scoped.
Dimension 17 returns to this force in more depth.

**Discoverability and readability.** Sacrificed. A field declared at the
top of a class is a public promise, even when the field is private,
because every reader of the class's methods will encounter it and must
build a mental model of when it holds a value. A local variable declared
inside the one method that uses it carries no such promise. its scope is
its own documentation.

**Nullability and defensive coding.** Sacrificed. Every method that reads
a temporary field, or a permanently-sometimes-empty field from the second
context in dimension 2, must either trust that the field was set by
something that ran earlier, which is an invisible temporal coupling
enforced by convention rather than the type system, or must add a null
check, which spreads defensive conditionals through the class.

**Short-term edit locality.** Favoured, and this is the only force the
smell genuinely wins on. Adding a field and reading it from three private
methods is a smaller, more contained diff than introducing a new class,
moving the algorithm's helper methods onto it, and updating the call site.
This is the same short-term-velocity force that Data Clumps trades on, and
the same honest acknowledgment applies here. the smell is rarely
malicious, it is usually the cheapest edit available at the moment it was
made.

## 4. Applicability and non-applicability

This dimension describes when to apply the FIX, extracting the temporary
state into its own object or its own type, not when to apply the smell
itself, since no engineer sets out to introduce a smell on purpose.

Apply the fix when the following hold.

- A method's algorithm needs three or more intermediate values threaded
  through two or more private helper methods, and those values are
  currently stored as instance fields on the class that also holds
  long-lived, always-relevant state.
- A field is set by one method and read only by other methods that are
  always called as part of the same operation, never independently, and
  the field's value before that operation starts, or after it finishes, is
  never read by any other code for any real reason.
- A subset of a class's instances need extra fields that a majority of
  instances leave empty, and code elsewhere in the system already has, or
  would benefit from having, conditionals that branch on whether those
  fields are populated.
- The class is reused across multiple invocations of the algorithm, for
  example a request-scoped handler, a batch job runner, or anything a
  container or thread pool might hand out more than once, and a
  temporary field risks leaking state between invocations.
- A debugger session or a bug report has already shown a temporary field
  holding a stale value from a previous call, which is direct evidence
  the shortcut has already cost real debugging time.

Do NOT apply the fix in these cases, and the reason matters more than the
rule.

- **The field is genuinely long-lived domain state, simply nullable.** A
  `Person.middleName` that is null for people without a middle name is not
  a temporary field. It never gets a value later in the object's
  lifetime that it lacked before, it is not set and cleared by a
  particular method call, and it does not represent scratch state for an
  algorithm. Extracting it into a class does not remove any confusion,
  because there was no confusion about when it holds a value, only about
  whether it does for this particular real-world person. The correct
  fix, if any, is a language-level Optional or nullable type annotation,
  not Extract Class.
- **The intermediate values are used by exactly one method with no
  helper-method fan-out.** If only one method reads and writes the
  values, they are ordinary local variables that were, for no good
  reason, promoted to fields. The fix is the much smaller refactoring
  Replace Field with Local Variable or simply deleting the field
  declaration and declaring the variables where they are used, not the
  heavier Extract Class.
- **The class is a short-lived, single-purpose object that already
  exists only to run this one algorithm once.** A `LoanRiskCalculation`
  object constructed fresh per calculation, used once, and discarded is
  not exhibiting the smell even though every field on it is only valid
  during the calculation, because there is no other, unrelated long-lived
  state on the class competing for the reader's attention, and the
  object's entire lifetime coincides with the algorithm's lifetime. This
  is in fact the shape the fix produces, see dimension 8, so recognising
  it prevents refactoring something that is already correct.
- **The field represents genuine object identity or configuration set
  once at construction and read forever after, even if it happens to be
  used by only a few methods.** A `connectionTimeoutMillis` field read
  only inside a `connect()` method is not temporary, it is configuration.
  it holds the same value for the whole object lifetime regardless of how
  many times `connect()` is called, and calling `connect()` does not
  invalidate it. The test in dimension 2's third paragraph, does the
  value survive the operation that set it, distinguishes this case.
- **Threading the values as explicit parameters and a small return
  struct or tuple is available and idiomatic in the language, and the
  helper-method count is small enough that the resulting signatures stay
  readable.** In languages with first-class tuples, records, or multiple
  return values, three helper methods each returning a small value object
  and taking one or two parameters is frequently a lighter, equally clear
  fix than a full Extract Class, see dimension 8's discussion of the
  parameter-object variant.

## 5. Structure

The smell has a before-shape and a fixed-shape, and both are worth naming
explicitly because a code smell entry, unlike a design pattern entry, is
judged on the transformation between the two.

**The smelly structure.** One class, call it the **Host**, carries two
categories of field that a reader cannot distinguish from the
declarations alone.

- **Persistent fields.** Set once, usually at construction, valid for
  the object's whole lifetime, read by most of the class's public
  methods. These are legitimate instance state and are not the problem.
- **Temporary fields.** Set by one entry-point method at the start of a
  single algorithm run, read and written by that method's private
  helpers during the run, and left holding a stale or otherwise useless
  value once the run finishes. These are the smell.

The Host's public surface gives no signal separating the two groups. Every
caller of the Host sees one flat list of fields and one flat list of
methods.

**The fixed structure.** The temporary fields, and the private helper
methods that exclusively read and write them, move onto a new,
narrowly-scoped type, the **Extracted Calculation**. The Host keeps its
persistent fields and its public entry-point method, but the entry-point
method's body becomes a short delegation. construct an Extracted
Calculation instance, passing it whatever the Host's persistent state
supplies as input, call its one public method, and use the result. The
Extracted Calculation's fields, which are exactly the fields that were
temporary on the Host, are now fully legitimate, because the Extracted
Calculation's entire lifetime is scoped to exactly one algorithm run.
there is no longer any period during the Extracted Calculation's life
when those fields are empty or stale, because the object itself does not
outlive the operation.

## 6. ASCII structure diagram

```
BEFORE. the smell.

+-------------------------------------------------+
| Host                                            |
| ----------------------------                    |
| id             (persistent)                     |
| createdAt      (persistent)                     |
| processedCount (persistent)                     |
| ............................                    |
| currentRate    (temporary, scratch)             |
| exemption      (temporary, scratch)             |
| remainder      (temporary, scratch)             |
| ----------------------------                    |
| applyRegionalTax(invoice)  <- sets temp fields, |
|   then three private helpers read/write them    |
| lookupRate(region)                              |
| applyExemption(amount)                          |
| roundToCents(amount)                            |
| recordProcessed()  <- unrelated method, does    |
|   not touch temp fields                         |
+-------------------------------------------------+

A reader of the field list cannot tell, without reading
every method body, which three fields are alive only
during one call.


AFTER. Extract Class applied to the temporary fields.

+---------------------+
| Host                |
| ----------------    |
| id                  |
| createdAt           |
| processedCount      |
| ----------------    |
| applyRegionalTax(i) |
|   .calculate()      |
| recordProcessed()   |
+---------------------+
           | creates, per call
           | new RegionalTaxCalculation(i, r)
           v
+----------------------------+
| RegionalTaxCalculation     |
| ----------------------     |
| invoice        (input)     |
| region         (input)     |
| currentRate    (own state) |
| exemption      (own state) |
| remainder      (own state) |
| ----------------------     |
| calculate(): Money         |
| lookupRate()               |
| applyExemption(amount)     |
| roundToCents(amount)       |
+----------------------------+

Every field on RegionalTaxCalculation is now valid for
the entire lifetime of the object, because the object's
lifetime is exactly one calculation.
```

## 7. Dynamics

The dangerous dynamic is a timeline, not a single snapshot, and it is
worth walking through because the failure it produces is intermittent and
therefore hard to reproduce.

```
Host instance, reused across two calls to applyRegionalTax

  t0  Host constructed. currentRate, exemption, remainder are all
      language-default (0, null, zero) and carry no real value yet.

  t1  applyRegionalTax(invoiceA) called, region = "DE-standard".
      currentRate <- 19%      (set)
      exemption   <- 0        (set, this region has no exemption path,
                                so the exemption-setting branch never runs)
      remainder   <- 0.02     (set)
      returns computed tax for invoiceA. Correct.

  t2  applyRegionalTax(invoiceB) called, region = "DE-reduced",
      which DOES have an exemption path, but only when the invoice
      total exceeds a threshold, and invoiceB is under the threshold,
      so the exemption-setting branch is skipped again.
      currentRate <- 7%       (set, overwritten correctly)
      exemption   <- 0        (SHOULD be set to 0 explicitly by the
                                skipped branch, but the branch that skips
                                simply does not touch the field, so the
                                previous run's value survives)
      remainder   <- 0.00     (set)
      returns computed tax for invoiceB. Value is CORRECT here only by
      coincidence, because the leftover exemption from t1 also
      happened to be 0.

  t3  applyRegionalTax(invoiceC) called, region = "DE-reduced",
      total exceeds the threshold, so its own exemption branch fires
      and sets exemption to 500 partway through an earlier, unrelated
      call that this timeline compresses for clarity, then a later
      call reaches the exemption-skip branch again.
      exemption   <- 500      (STALE, left over from an entirely
                                different earlier invoice, never reset)
      returns a tax figure that silently under-counts invoiceC by the
      leftover exemption. WRONG, and nothing in the code raised an
      error, because a field holding a number is indistinguishable
      from a field holding the RIGHT number.
```

The dynamic generalises past this one example. any code path through the
entry-point method that does not explicitly reset every temporary field
on every branch is a latent bug waiting for the specific sequence of
calls that exposes it, and the number of branches that must each
correctly reset every field grows combinatorially with the number of
temporary fields and the number of code paths through the algorithm. The
fixed shape from dimension 5 removes the dynamic entirely, because a
freshly constructed Extracted Calculation has no previous call to inherit
stale state from.

## 8. Implementation variants

**Extract Class, the canonical fix (Fowler).** Create a new class that
owns exactly the temporary fields and the private helper methods that
touch them, give it one public method that runs the whole algorithm and
returns the result, and have the Host construct one instance per call and
delegate to it. This is the fix demonstrated in dimensions 5 through 7 and
in the code examples below. Fowler's catalogue lists Extract Class as the
primary mechanical refactoring for this smell, alongside a secondary
option covered next, https://sourcemaking.com/refactoring/smells/temporary-field,
verified 2026-08-02.

**Introduce Null Object or Introduce Special Case, for the second context
from dimension 2.** When the smell is a field that is permanently
populated for only a subset of instances rather than scratch state for
one algorithm run, Extract Class alone does not remove the caller-side
`if (field != null)` conditionals. The typical companion fix is to give
the empty case its own explicit representation, a Null Object or a
Special Case subtype, so that callers stop branching on presence and
instead call a uniform method that behaves correctly whether or not the
special data was ever populated. This composes with, and does not
replace, Extract Class, because the special data itself may still be a
data clump worth its own type.

**Parameter object plus pure functions, in languages that favour it.** In
languages where multiple return values, records, or tuples are
first-class and cheap, a lighter alternative to a full Extract Class is
to bundle the temporary fields into an immutable value type returned from
one private helper and threaded as a parameter to the next, with no
class-level state at all. This keeps every intermediate value local to
the call stack of the top-level method, which is the strongest possible
fix for the concurrency force in dimension 3, because there is no shared
mutable storage location to race on in the first place. The trade is a
slightly longer parameter or return-type signature per helper compared to
the single Extracted-Calculation-object variant.

**Move the algorithm to a stateless static or module-level function.**
When the temporary fields' only inputs are already available as
parameters or as data already on the Host, and no genuinely reusable
object identity is needed, the whole algorithm can become a pure
function, static in Java or C#, a module-level function in Python, an
exported function in TypeScript, taking every needed input as a
parameter and returning the result, with no fields at all, temporary or
otherwise. This is Extract Class taken to its logical extreme, where the
extracted class has exactly one method and no reason to be
instantiated more than once conceptually, so it collapses into a
function.

**Thread-local or request-scoped storage, as a narrow escape hatch, not a
default.** In frameworks where the Host object genuinely must be a
long-lived singleton for reasons outside the algorithm's control, for
example a single servlet instance handling many concurrent requests, and
introducing a per-call object is blocked by a framework constraint rather
than a design choice, storing the temporary state in a thread-local or a
framework-provided request scope avoids the cross-invocation leak from
dimension 7 without changing the Host's object graph. This variant is
judgement, not a sourced recommendation, and it should be treated as a
narrow escape hatch rather than a default, because it trades one kind of
hidden coupling, the field, for another, the thread-local, and the second
kind is frequently harder to test, see dimension 15.

## 9. Known production uses

Two categories of real evidence exist for this smell. tooling built
specifically to detect it in production codebases, and a well documented
class of API design, event-driven parser callbacks, where the pattern the
smell warns against is common enough that the official documentation for
the APIs explicitly discusses the state-tracking concern.

**PMD's SingularField rule, shipped in the PMD static analysis tool used
across a very large number of real Java codebases.** The rule reports
"fields which may be converted to a local variable" because "in every
method where the field is used, it is assigned before it is first read",
which is the mechanical, automatable half of the Temporary Field
diagnosis, the case where a field never carries genuine state between
the calls that use it and should never have been a field at all. PMD,
Java Design Rules, SingularField,
https://docs.pmd-code.org/latest/pmd_rules_java_design.html, verified
2026-08-02. PMD is distributed as a general-purpose static analysis tool
integrated into build pipelines across a very large number of real Java
codebases, and a rule dedicated to exactly this smell existing in a
maintained, widely deployed tool is direct evidence the pattern recurs
often enough to be worth automated detection.

**SAX-style event-driven XML parser handlers, in both the Java and Python
standard libraries.** The SAX callback model, `startElement`,
`characters`, `endElement`, called by the parser as it streams through a
document, is a context where implementors are explicitly expected to
accumulate state, such as buffered character data, across a sequence of
calls belonging to one parse. Java's `org.xml.sax.helpers.DefaultHandler`
javadoc documents that "Application writers may override this method in a
subclass to take specific actions at the start of each element such as
allocating a new tree node or writing output to a file", which is
precisely the pattern of state accumulated in instance fields across a
callback sequence, https://docs.oracle.com/javase/8/docs/api/org/xml/sax/helpers/DefaultHandler.html,
verified 2026-08-02. Python's `xml.sax.handler` documentation carries the
matching caution that "the object passed as attrs may be re-used by the
parser; holding on to a reference to it is not a reliable way to keep a
copy of the attributes", explicitly warning implementors away from one
common mistake in exactly this state-accumulation pattern,
https://docs.python.org/3/library/xml.sax.handler.html, verified
2026-08-02. This is a legitimate, non-smelly use of instance fields for
accumulated parse state when the handler object's lifetime is scoped to
one parse, per the non-applicability test in dimension 4, and it becomes
the smell precisely when a handler instance is reused across multiple
parses without every accumulator field being reset at the start of each
parse, which is the exact failure walked through in dimension 7.

**Discussion of accumulating state inside a shared object structure, in
the Visitor pattern's own implementation notes.** The Gang of Four's
Design Patterns devotes part of the Visitor pattern's Implementation
section to the problem of a traversal that needs to accumulate state as
it visits each element, and observes that storing that accumulation as
instance variables directly on the visited objects, rather than on a
dedicated Visitor, spreads state-maintenance responsibility across every
class in the visited structure. Gamma, Helm, Johnson, Vlissides, Design
Patterns, Elements of Reusable Object-Oriented Software, Addison-Wesley,
1994, ISBN 0-201-63361-2, Chapter 5, Behavioral Patterns, Visitor,
Implementation. This is a canonical text, not a live URL, and is cited
here for the specific implementation discussion of accumulator state
placement, which is the design decision this entry's dimension 8 also
covers under Extract Class. Read as engineering judgement rather than a
direct quotation, since this entry paraphrases the design concern rather
than citing exact page text that has not been independently re-verified
against a specific printing.

## 10. Consequences

Positive, of the FIX, not of the smell.

- The Host's field list, after extraction, contains only genuinely
  long-lived state, so any reader can trust that every declared field
  carries a valid value whenever any method on the object runs.
- The Extracted Calculation's fields are fully valid for its entire
  lifetime, eliminating the stale-value class of bug walked through in
  dimension 7 by construction, not by discipline.
- The algorithm becomes independently testable, constructible, and
  reasoned about without needing to also construct and configure the
  unrelated persistent state that used to live on the same class, see
  dimension 15.
- Reuse of the Host across many calls, including concurrent calls, stops
  being a correctness hazard for the extracted state, because a fresh
  Extracted Calculation instance per call has no shared storage to race
  on.

Negative, of the FIX.

- One more type exists in the codebase, with its own file, its own name
  to choose well, and its own place in the class diagram, which is a real
  ongoing cost even when small.
- Construction overhead, one object allocated per algorithm run instead
  of zero, which is negligible in most managed runtimes and worth naming
  explicitly rather than dismissing without measurement in an allocation
  hot path, see dimension 12.
- The relationship between the Host and the Extracted Calculation must be
  named and understood, an association that did not exist before, and a
  reader now needs to know two classes instead of one to fully understand
  the algorithm, even though each of the two is individually simpler.
- If applied over-eagerly to the case ruled out in dimension 4, a single
  method's local variables with no fan-out, it introduces a whole new
  type to solve a problem that Replace Field with Local Variable would
  have solved with a one-line edit.

## 11. Failure modes and misuse

**Stale value read across reused invocations.** Symptom. An intermittent
bug where the same input, run twice in a row through the same long-lived
Host instance, produces a different result the second time, or a result
that is correct the first time and wrong on a later call with a different
input that happens to skip the branch that would have reset a field.
Cause. A temporary field is set on some code paths through the algorithm
and left untouched on others, so a previous call's value survives into
the next call whenever the current call's path does not overwrite it.
Fix. Extract Class per dimension 8's primary variant, which removes the
possibility entirely rather than requiring every branch to remember to
reset every field, or, as a smaller interim step, reset every temporary
field explicitly at the very start of the entry-point method before any
branching begins.

**Concurrent overwrite between two threads sharing one Host.** Symptom. A
production incident where two requests processed close together in time
each receive a result that looks like it belongs to the OTHER request,
or a value that is a corrupted mix of both, and the bug does not
reproduce locally under a debugger because the timing window is narrow.
Cause. Two threads call the same entry-point method on the same shared
Host instance at close to the same time, both write to the same
temporary field, and the second write can land between the first
thread's write and its later read. Fix. Extract Class, constructing one
Extracted Calculation per call so each thread's state lives on its own
object, or, where the Host truly cannot be made per-call, thread-local
storage as the narrow escape hatch from dimension 8, with an explicit
comment recording why the escape hatch was needed.

**Widening null checks spreading through the class.** Symptom. A code
review flags a growing number of `if (field != null)` guards scattered
across several methods on the same class, each one protecting against
the case where the temporary or sometimes-populated field has not been
set for this particular call path or this particular instance. Cause. The
class never draws a boundary between the always-valid state and the
sometimes-valid state, so every method that might run before or without
the field being set has to defend itself independently, and each new
caller repeats the same defensive check because nothing enforces it
centrally. Fix. Extract Class for the algorithm-scratch case, or
Introduce Null Object or Introduce Special Case for the
sometimes-populated-instance case from dimension 2, so the presence
check happens exactly once, at construction, rather than at every read
site.

**Serialization or persistence accidentally capturing scratch state.**
Symptom. A serialized snapshot of the Host, taken for caching, logging,
or persistence, includes a field that carries a stale or otherwise wrong
value because the snapshot happened to be taken between algorithm runs,
or in the middle of one, and a later process that deserializes the
object misreads the leftover value as real data. Cause. The temporary
field is declared at the same visibility and the same serialization
scope as the Host's genuine persistent fields, with nothing
distinguishing the two for a generic serializer that walks every field
by reflection. Fix. Extract Class removes the field from the serialized
type entirely, since the Extracted Calculation is constructed, used, and
discarded within a single algorithm run and is never itself persisted,
or, as a narrower patch, mark the field explicitly transient or excluded
from serialization while the larger refactor is scheduled.

**Test setup requiring irrelevant configuration.** Symptom. A unit test
for one narrow calculation has to construct and fully configure the
entire Host object, including persistent fields the calculation under
test never touches, before it can even begin to exercise the temporary
fields' logic, and the test's setup section is longer than its
assertions. Cause. The temporary fields and the persistent fields live on
the same class, so testing the temporary-field logic in isolation is not
possible without also satisfying every constructor and setter dependency
of the unrelated persistent state. Fix. Extract Class, which lets the
extracted algorithm be tested by constructing only the small,
purpose-built Extracted Calculation type with only the inputs that
algorithm actually needs, see dimension 15.

## 12. Trade-off matrix

Compared against named alternatives for handling multi-step algorithm
state, across the forces from dimension 3.

| Force | Temporary field on Host (the smell) | Extract Class (the fix) | Parameter object plus pure functions | Long parameter list, no field | Thread-local storage |
|---|---|---|---|---|---|
| Cohesion of the Host class | Poor. Mixed lifetimes in one field list | Strong. Host keeps only persistent fields | Strong. Host gains no new fields at all | Strong for cohesion, weak for signature length | Poor. State exists but is invisible in the class body |
| Safety across reuse or concurrency | Poor. Stale reads and races, dimension 7 | Strong. Fresh object per call, nothing to race on | Strong. Values live only on the call stack | Strong for the same reason | Strong per thread, but hides the sharing decision |
| Readability of field declarations | Poor. Reader cannot tell which fields are live when | Strong. Every field on each type carries a valid value at all times | Strong. No field-level ambiguity exists | Strong at the field level, weak at the signature level | Poor. Storage location is not visible at the declaration site |
| Method signature length | Short, at the cost of the field list | Short. One entry point, internal helpers keep field access | Longer. Each helper takes and returns explicit values | Longest. Every intermediate value threaded by hand | Short, same as the smell |
| Testability in isolation | Poor. Must configure the whole Host to test one algorithm | Strong. Extracted type constructed with only its own inputs | Strong. Pure functions tested with plain inputs and outputs | Strong, same as pure functions | Poor. A thread-local must be populated before the code under test runs |
| Allocation cost per call | None | One object per call | None, or one small value type per intermediate step | None | None |
| Fit for a genuinely long-lived, container-managed singleton Host | Common, and this is exactly why the smell appears there | Requires the Host to construct a helper, which is usually still possible | Requires the Host to call functions, always possible | Always possible, at the cost of long signatures | The narrow case this variant exists for |

Reading of the table. Extract Class wins on every force except allocation
cost, which is negligible outside a proven hot path, and except the
narrow case where the Host is a framework-imposed singleton that cannot
construct a helper object at all, where thread-local storage is the
accepted, judgement-based escape hatch rather than a preferred default.

## 13. Related and incompatible patterns

- **Data Class.** A frequent neighbour rather than a strict relative. a
  Host exhibiting Temporary Field sometimes also exhibits Data Class
  symptoms once the temporary fields are extracted, if the newly
  Extracted Calculation ends up holding only data with no behaviour
  because the original algorithm's logic was itself thin. Extracting is
  still the correct first step, and the resulting type's own cohesion is
  then judged on its own terms against the Data Class entry in this
  repository.
- **Lazy Class.** A tension, not a conflict. Over-eager application of
  Extract Class to a case ruled out in dimension 4, a single method with
  no helper fan-out, produces exactly the smell that the Lazy Class entry
  in this repository warns against, a class that does not do enough to
  earn its own existence. The applicability test in dimension 4 exists
  specifically to prevent this outcome.
- **Feature Envy.** A common co-occurrence in the second context from
  dimension 2, sometimes-populated instance fields. Once a field like
  `expeditedCarrier` exists on `Order`, other classes' methods
  frequently develop long chains of logic that reach into `Order` to
  read that one field and act on it, which is the Feature Envy shape.
  Introduce Special Case, from dimension 8, usually resolves both
  smells at once by moving the envious behaviour onto the special-case
  type itself.
- **Long Method.** Usually the originating cause, not merely a related
  smell. the multi-step algorithm that first motivated storing
  intermediate values as fields is very often already a Long Method on
  the Host, before it was ever split into private helpers, and the split
  into helpers using shared fields is frequently an intermediate,
  half-finished attempt at applying Extract Method that stopped short of
  also extracting the state.
- **Extract Class.** The primary fix, described fully in dimension 8 and
  dimension 14, not merely related to it. Every code example in this
  entry demonstrates Extract Class applied specifically to this smell.
- **Null Object and Special Case.** The companion fix for the
  sometimes-populated-instance context from dimension 2, described in
  dimension 8. Extract Class alone addresses the algorithm-scratch
  context cleanly but does not, by itself, remove caller-side presence
  checks for the sometimes-populated-instance context, which is why the
  two fixes are frequently applied together rather than as alternatives
  to each other.
- **Singleton.** An active tension when the Host is deliberately a
  process-wide singleton. Every temporary field on a Singleton is a
  concurrency hazard by dimension 7's argument, because a singleton is,
  by definition, shared across every call site in the process, which is
  the worst possible case for the reuse-across-invocations force in
  dimension 3.

## 14. Refactoring path in and out

Applying the fix to smelly code that has it. Fowler's Extract Class,
adapted to the specific case of temporary fields, ordered steps.

1. List every field on the Host and classify each one as persistent,
   valid for the object's whole life, or temporary, valid only during
   one algorithm run. Dimension 4's applicability tests decide the
   ambiguous cases.
2. Confirm the temporary fields are read and written only by the
   entry-point method and its private helpers, never by any other public
   method or by any code outside the class. If an unrelated method also
   reads a candidate field, it may be persistent state, not temporary,
   and the classification from step 1 needs revisiting.
3. Create the new type. Give it a name that describes the algorithm, not
   the Host, for example `RegionalTaxCalculation`, not
   `InvoiceProcessorHelper`, so the name itself signals a bounded,
   self-contained purpose.
4. Move the temporary fields onto the new type as its own fields,
   supplied through its constructor from whatever inputs the algorithm
   actually needs, which usually includes some of the Host's
   persistent state passed in explicitly, not inherited implicitly.
5. Move the private helper methods that read and write those fields onto
   the new type as well, keeping their internal logic unchanged in this
   step, matching the discipline that Extract Class edits should not
   also silently change behaviour.
6. Give the new type one public method that runs the whole algorithm,
   named for what it computes, and have it return the result the
   original entry-point method used to compute inline.
7. Replace the Host's original entry-point method body with construction
   of the new type and a call to its public method, deleting the
   now-unused temporary field declarations from the Host in the same
   change.
8. Run the existing test suite. add the isolation tests from dimension
   15 for the new type if none existed for the algorithm before, since
   the extraction is the natural moment to close that gap cheaply.

Removing the fix when it stops earning its place, the reverse direction,
applies specifically when an Extracted Calculation type has decayed into
something that no longer justifies its own existence, most often the
Lazy Class outcome named in dimension 13.

1. Confirm the Extracted Calculation type is called from exactly one call
   site, has no independent tests that would be lost, and its public
   method does genuinely little work, the condition the Lazy Class entry
   in this repository defines.
2. Inline the type's public method body back into the Host's
   entry-point method, following Inline Class.
3. Convert the type's fields back into local variables scoped to the
   reassembled method, or, if the fan-out to multiple helper methods was
   the original reason for extraction and that fan-out still exists,
   prefer converting to parameters and small return values per
   dimension 8's parameter-object variant rather than reintroducing
   Host-level fields, which would simply reproduce the original smell.
4. Delete the now-empty extracted type and its file.
5. Re-run the test suite, and merge any tests that existed only for the
   extracted type into the Host's test file, adjusting them to call the
   reassembled method directly.

## 15. Testing and verification

Easier because of the fix.

- The extracted algorithm can be unit tested by constructing the
  Extracted Calculation directly with only the inputs it actually needs,
  with no dependency on the Host's unrelated persistent state, its
  constructor, or any setters the Host's other responsibilities require.
- Because the extracted type's fields are always valid for its whole
  lifetime, tests never need to worry about calling methods on it in the
  wrong order relative to some earlier setup call that would have
  populated a temporary field, which removes a whole class of
  order-dependent test bugs.
- A property test that constructs the Extracted Calculation with
  randomised valid inputs and asserts an invariant of the result, for
  example that the computed tax never exceeds the invoice total, becomes
  straightforward to write, because the object under test has no hidden
  state left over from a previous property-test iteration to reset
  between runs.

Harder because of the fix.

- A reader debugging the Host now has to follow one more hop, from the
  Host's entry-point method into the Extracted Calculation's
  constructor and public method, to see the full algorithm, rather than
  reading it all in one class.
- Mocking or stubbing the extracted type, when the Host's own tests want
  to test the Host's delegation logic without exercising the real
  algorithm, requires either a constructor-injectable factory for the
  Extracted Calculation or a language facility for replacing
  construction in tests, which is a small additional design decision the
  smelly version never had to make.

Techniques that apply directly to detecting and verifying the smell
itself, before or without fixing it.

- **Field-usage matrix, read by hand or by tooling.** For each field on
  a suspect class, list every method that reads it and every method that
  writes it. A field written by exactly one method and read only by
  methods that method calls, directly or transitively, in the course of
  one top-level invocation, is a strong candidate for the smell, and is
  exactly the shape PMD's SingularField rule automates for the narrowest
  case, see dimension 9.
- **Reset-coverage test.** For a Host suspected of the smell, call the
  entry-point method twice in a row with two different inputs chosen so
  that the second input takes a code path that would skip setting one of
  the suspect fields, and assert the second call's result does not
  depend on the first call's input. A failure here is a reproducible,
  automatable version of the stale-value failure mode from dimension 11.
- **Concurrent-invocation stress test.** For a Host that is shared, for
  example a singleton or a pooled instance, call the entry-point method
  from several threads concurrently with distinguishable inputs and
  assert each thread's result matches only its own input, never a mix.
  This directly exercises the race described in dimension 7 and
  dimension 11, and should be run with the runtime's data-race or
  thread-sanitizer tooling enabled where the language provides one.

## 16. Observability signals

The smell itself produces no direct runtime signal, because a field
holding a stale value looks, to any generic monitoring system, exactly
like a field holding a correct value, of the same type, within the same
plausible range. The signals below are indirect, drawn from the failure
modes in dimension 11.

What to record, on the smelly version, while it is still in production
and awaiting the fix.

- A counter, or a structured log field, recording the entry-point
  method's input identifier, for example an invoice number, alongside a
  hash or a summary of the temporary fields' values immediately before
  they are used in the final computation, so a later incident
  investigation can correlate a specific output with the exact scratch
  state that produced it.
- An assertion, active in non-production environments and ideally
  sampled in production, that every temporary field is in an expected,
  freshly-set state at the very start of the entry-point method, before
  any branch has had a chance to read a leftover value, catching the
  dimension 11 stale-read failure at the earliest possible point rather
  than at the point where the bad output is finally observed.
- A gauge or a log line at the point where the Host is constructed or
  first put into a shared pool, recording whether the Host is intended
  to be single-call or reused, since this single fact determines whether
  the temporary-field risk from dimension 3 applies at all.

What a healthy instance looks like once the fix is in place. There is no
longer a field-level signal to watch, because the Extracted Calculation's
fields are, by construction, always valid for its whole life, and the
only observability that remains relevant is ordinary logging and tracing
of the algorithm's inputs and outputs, the same as for any other
short-lived, single-purpose object.

What a failing instance looks like before the fix. A log correlation
showing two calls to the same entry-point method, close together in
time or on the same Host instance, where the second call's recorded
scratch-state hash does not match what the second call's own branch
logic should have produced from its own input, which is the direct
observable signature of a stale field carrying over from the first call.

## 17. Security and privacy implications

The smell has a genuine, non-speculative implication once the Host is
shared across requests belonging to different users or tenants, which is
common in exactly the reused, container-managed context described in
dimension 3 and dimension 9.

**Cross-request data leakage on a shared Host.** If the Host handles
requests for more than one user, tenant, or session, and a temporary
field holds any piece of that user's data, such as a computed discount,
an authorization decision, or a fragment of personally identifiable
information used mid-algorithm, the stale-read failure mode from
dimension 11 becomes a data leak between users rather than merely an
incorrect number. A second request from a different user, taking a code
path that does not overwrite the field, can read the previous user's
leftover value. This is the same underlying mechanism as the correctness
bug in dimension 7, with a materially worse consequence when the leaked
value is sensitive. The fix is identical to the correctness fix, Extract
Class per dimension 8, and this is a case where the security
implication alone is sufficient justification for the refactor even
absent any observed correctness bug.

**Serialized scratch state escaping its intended boundary.** As noted in
dimension 11's serialization failure mode, a generic serializer that
walks every field by reflection does not distinguish a temporary field
from a persistent one, and can therefore include scratch state, which
was never intended to be persisted or transmitted, in a cache entry, a
log payload, or a network response built from the whole object. Where
that scratch state includes sensitive intermediate values, this is a
genuine, if usually accidental, exposure path. Marking temporary fields
transient, or, preferably, extracting them onto a type that is never
itself passed to the serializer, closes this path.

On authentication and authorization specifically, this entry has no
sourced or judgement-based claim beyond the general data-leakage
mechanism above, and it would be inventing a concern to assert a
narrower one.

## 18. References

1. Martin Fowler, with Kent Beck, John Brant, William Opdyke, Don
   Roberts. Refactoring, Improving the Design of Existing Code.
   Addison-Wesley, 1999. ISBN 0-201-48567-2. Chapter 3, the smell
   Temporary Field, and Chapter 7 for the Extract Class refactoring used
   as the primary fix throughout this entry.
2. SourceMaking. Refactoring Guru's sibling catalogue site,
   "Temporary Field". https://sourcemaking.com/refactoring/smells/temporary-field
   Verified 2026-08-02. Cited only to confirm the smell's definition and
   its attribution to the Fowler catalogue, not used as a source of any
   copied text in this entry.
3. PMD project. Java Design Rules, SingularField.
   https://docs.pmd-code.org/latest/pmd_rules_java_design.html
   Verified 2026-08-02. Source for the automated-detection production
   evidence in dimension 9.
4. Oracle. Java SE 8 API Specification,
   `org.xml.sax.helpers.DefaultHandler`.
   https://docs.oracle.com/javase/8/docs/api/org/xml/sax/helpers/DefaultHandler.html
   Verified 2026-08-02. Source for the SAX callback-accumulation
   production context in dimension 9.
5. Python Software Foundation. Python 3 documentation,
   `xml.sax.handler`, ContentHandler.
   https://docs.python.org/3/library/xml.sax.handler.html
   Verified 2026-08-02. Source for the Python SAX callback-accumulation
   caution cited in dimension 9.
6. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides. Design
   Patterns, Elements of Reusable Object-Oriented Software.
   Addison-Wesley, 1994. ISBN 0-201-63361-2. Chapter 5, Behavioral
   Patterns, Visitor, Implementation section, the discussion of
   accumulating state, cited in dimension 9 and dimension 13.

## Code examples

Three languages, chosen because the smell and its fix are equally
idiomatic in all three and each shows a distinct language facility worth
naming. Java shows the classical Extract Class fix with the smelly
version first for direct comparison. Python shows the same fix using a
dataclass for the Extracted Calculation, which is the idiomatic
lightweight way to express a short-lived, purpose-built value-and-behaviour
object in Python. TypeScript shows the fix alongside the parameter-object
variant from dimension 8, since TypeScript's first-class object literals
make that variant especially natural. Go is omitted because Go has no
classes or instance methods in the sense the smell depends on, its
receiver methods already read as this entry's fixed shape by default, so
demonstrating the smell would require first inventing an unidiomatic Go
shape purely to then remove it, which teaches nothing a Go reader would
recognise from real code. Rust is omitted for the same reason. ownership
rules make a value living only for the duration of one call the default,
not an anti-pattern to guard against, so the smell is unusually hard
to write by accident in Rust.

### Java

The smelly version first, then the fixed version, so the transformation
in dimension 5 is visible directly in code.

```java
// SMELLY. currentRate, exemption, remainder are valid only during
// one call to applyRegionalTax, but they live beside processedCount,
// which is valid for the whole life of an InvoiceProcessor.
final class SmellyInvoiceProcessor {
    private int processedCount = 0;

    private double currentRate;
    private double exemption;
    private double remainder;

    double applyRegionalTax(double invoiceTotal, String region) {
        lookupRate(region);
        applyExemption(invoiceTotal);
        double taxed = invoiceTotal * currentRate - exemption;
        roundToCents(taxed);
        processedCount++;
        return taxed - remainder;
    }

    private void lookupRate(String region) {
        currentRate = region.equals("DE-reduced") ? 0.07 : 0.19;
    }

    private void applyExemption(double invoiceTotal) {
        if (invoiceTotal > 1000.0) {
            exemption = 50.0;
        }
        // BUG. no else branch. exemption keeps whatever the previous
        // call left it at when this call's invoiceTotal is <= 1000.
    }

    private void roundToCents(double amount) {
        remainder = Math.round(amount * 100) / 100.0 - amount;
    }

    int getProcessedCount() {
        return processedCount;
    }
}

// FIXED. Extract Class. RegionalTaxCalculation owns exactly the fields
// that used to be temporary, and every one of them is now valid for
// the whole life of this short-lived object.
final class RegionalTaxCalculation {
    private final double invoiceTotal;
    private final String region;
    private double currentRate;
    private double exemption;
    private double remainder;

    RegionalTaxCalculation(double invoiceTotal, String region) {
        this.invoiceTotal = invoiceTotal;
        this.region = region;
        this.exemption = 0.0;
    }

    double calculate() {
        lookupRate();
        applyExemption();
        double taxed = invoiceTotal * currentRate - exemption;
        roundToCents(taxed);
        return taxed - remainder;
    }

    private void lookupRate() {
        currentRate = region.equals("DE-reduced") ? 0.07 : 0.19;
    }

    private void applyExemption() {
        if (invoiceTotal > 1000.0) {
            exemption = 50.0;
        }
    }

    private void roundToCents(double amount) {
        remainder = Math.round(amount * 100) / 100.0 - amount;
    }
}

final class InvoiceProcessor {
    private int processedCount = 0;

    double applyRegionalTax(double invoiceTotal, String region) {
        double result = new RegionalTaxCalculation(invoiceTotal, region).calculate();
        processedCount++;
        return result;
    }

    int getProcessedCount() {
        return processedCount;
    }
}

public final class TemporaryFieldDemo {
    public static void main(String[] args) {
        InvoiceProcessor fixed = new InvoiceProcessor();
        System.out.println(fixed.applyRegionalTax(1500.0, "DE-standard"));
        System.out.println(fixed.applyRegionalTax(200.0, "DE-reduced"));
        System.out.println("processed: " + fixed.getProcessedCount());
    }
}
```

### Python

```python
from dataclasses import dataclass, field


class SmellyInvoiceProcessor:
    """SMELLY. current_rate, exemption, remainder live beside
    processed_count, but only processed_count survives between calls
    on purpose."""

    def __init__(self) -> None:
        self.processed_count = 0
        self.current_rate = 0.0
        self.exemption = 0.0
        self.remainder = 0.0

    def apply_regional_tax(self, invoice_total: float, region: str) -> float:
        self._lookup_rate(region)
        self._apply_exemption(invoice_total)
        taxed = invoice_total * self.current_rate - self.exemption
        self._round_to_cents(taxed)
        self.processed_count += 1
        return taxed - self.remainder

    def _lookup_rate(self, region: str) -> None:
        self.current_rate = 0.07 if region == "DE-reduced" else 0.19

    def _apply_exemption(self, invoice_total: float) -> None:
        if invoice_total > 1000.0:
            self.exemption = 50.0
        # BUG. no else. self.exemption keeps last call's value
        # whenever this call's invoice_total is at or below 1000.

    def _round_to_cents(self, amount: float) -> None:
        self.remainder = round(amount, 2) - amount


@dataclass
class RegionalTaxCalculation:
    """FIXED. Extract Class as a dataclass. Every field here is
    valid for the whole life of this short-lived object."""

    invoice_total: float
    region: str
    current_rate: float = field(default=0.0, init=False)
    exemption: float = field(default=0.0, init=False)
    remainder: float = field(default=0.0, init=False)

    def calculate(self) -> float:
        self._lookup_rate()
        self._apply_exemption()
        taxed = self.invoice_total * self.current_rate - self.exemption
        self._round_to_cents(taxed)
        return taxed - self.remainder

    def _lookup_rate(self) -> None:
        self.current_rate = 0.07 if self.region == "DE-reduced" else 0.19

    def _apply_exemption(self) -> None:
        if self.invoice_total > 1000.0:
            self.exemption = 50.0

    def _round_to_cents(self, amount: float) -> None:
        self.remainder = round(amount, 2) - amount


class InvoiceProcessor:
    def __init__(self) -> None:
        self.processed_count = 0

    def apply_regional_tax(self, invoice_total: float, region: str) -> float:
        result = RegionalTaxCalculation(invoice_total, region).calculate()
        self.processed_count += 1
        return result


if __name__ == "__main__":
    processor = InvoiceProcessor()
    print(processor.apply_regional_tax(1500.0, "DE-standard"))
    print(processor.apply_regional_tax(200.0, "DE-reduced"))
    print("processed:", processor.processed_count)
```

### TypeScript

Shows Extract Class first, then the parameter-object variant from
dimension 8 as a lighter alternative available because TypeScript
functions can return small object literals cheaply.

```typescript
// SMELLY. currentRate, exemption, remainder live beside processedCount
// on the same class, with different, undistinguished lifetimes.
class SmellyInvoiceProcessor {
  processedCount = 0;
  private currentRate = 0;
  private exemption = 0;
  private remainder = 0;

  applyRegionalTax(invoiceTotal: number, region: string): number {
    this.lookupRate(region);
    this.applyExemption(invoiceTotal);
    const taxed = invoiceTotal * this.currentRate - this.exemption;
    this.roundToCents(taxed);
    this.processedCount += 1;
    return taxed - this.remainder;
  }

  private lookupRate(region: string): void {
    this.currentRate = region === "DE-reduced" ? 0.07 : 0.19;
  }

  private applyExemption(invoiceTotal: number): void {
    if (invoiceTotal > 1000) {
      this.exemption = 50;
    }
    // BUG. no else. exemption keeps the previous call's value
    // whenever this call's invoiceTotal is at or below 1000.
  }

  private roundToCents(amount: number): void {
    this.remainder = Math.round(amount * 100) / 100 - amount;
  }
}

// FIXED, variant one. Extract Class.
class RegionalTaxCalculation {
  private currentRate = 0;
  private exemption = 0;
  private remainder = 0;

  constructor(
    private readonly invoiceTotal: number,
    private readonly region: string,
  ) {}

  calculate(): number {
    this.lookupRate();
    this.applyExemption();
    const taxed = this.invoiceTotal * this.currentRate - this.exemption;
    this.roundToCents(taxed);
    return taxed - this.remainder;
  }

  private lookupRate(): void {
    this.currentRate = this.region === "DE-reduced" ? 0.07 : 0.19;
  }

  private applyExemption(): void {
    if (this.invoiceTotal > 1000) {
      this.exemption = 50;
    }
  }

  private roundToCents(amount: number): void {
    this.remainder = Math.round(amount * 100) / 100 - amount;
  }
}

class InvoiceProcessor {
  processedCount = 0;

  applyRegionalTax(invoiceTotal: number, region: string): number {
    const result = new RegionalTaxCalculation(invoiceTotal, region).calculate();
    this.processedCount += 1;
    return result;
  }
}

// FIXED, variant two. parameter object plus pure functions, no
// extracted class at all, from dimension 8.
interface RateResult {
  rate: number;
}
interface ExemptionResult {
  exemption: number;
}

function lookupRate(region: string): RateResult {
  return { rate: region === "DE-reduced" ? 0.07 : 0.19 };
}

function applyExemption(invoiceTotal: number): ExemptionResult {
  return { exemption: invoiceTotal > 1000 ? 50 : 0 };
}

function roundToCents(amount: number): number {
  return Math.round(amount * 100) / 100 - amount;
}

function computeRegionalTax(invoiceTotal: number, region: string): number {
  const { rate } = lookupRate(region);
  const { exemption } = applyExemption(invoiceTotal);
  const taxed = invoiceTotal * rate - exemption;
  const remainder = roundToCents(taxed);
  return taxed - remainder;
}

const fixed = new InvoiceProcessor();
console.log(fixed.applyRegionalTax(1500, "DE-standard"));
console.log(fixed.applyRegionalTax(200, "DE-reduced"));
console.log("processed:", fixed.processedCount);
console.log(computeRegionalTax(1500, "DE-standard"));
```
