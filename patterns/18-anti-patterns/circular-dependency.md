---
name: Circular Dependency
slug: circular-dependency
family: 18-anti-patterns
category: Anti-pattern
aliases: [Cyclic Dependency, Dependency Cycle, Import Cycle, Mutual Dependency]
first_described: "Robert C. Martin, Acyclic Dependencies Principle, Engineering Notebook, C++ Report, 1996"
maturity: canonical
related: [dependency-injection, facade, mediator, dependency-inversion-principle, god-object]
incompatible_with: []
verified: 2026-08-02
---

# Circular Dependency

## 1. Name, aliases, and lineage

The canonical name is Circular Dependency. It is also called Cyclic Dependency,
Dependency Cycle, Import Cycle when the mechanism is a module or package import
statement, and Mutual Dependency when exactly two units depend on each other
directly rather than through a longer chain. All four names describe the same
underlying condition. two or more units, where a unit can be a class, a module,
a package, a service, a build target, or a database table, form a chain of
dependency edges that returns to its starting point.

The pattern is not named in the Gang of Four catalog, because the Gang of Four
catalog describes recurring solutions, and this is a recurring problem. The
earliest widely cited naming of the underlying principle comes from Robert C.
Martin's Engineering Notebook column in the C++ Report, where he formulated the
Acyclic Dependencies Principle as one of a set of package-level design
principles, stating that the dependency graph of packages must have no cycles.
Martin later restated the same principle in his book, Robert C. Martin, *Agile
Software Development, Principles, Patterns, and Practices*, Prentice Hall, 2002,
ISBN 0-13-597444-5, chapter 28, "The Acyclic Dependencies Principle". The book
frames a cycle in the package dependency graph as a design defect that must be
broken, and describes two named techniques for breaking it, Dependency
Inversion and the creation of a new package that both original packages depend
on.

The word "circular" in this entry always refers to a STATIC dependency edge,
meaning one unit's source, build definition, schema, or module declaration
names the other. This is distinct from two units that merely call each other at
runtime without either one's build artifact needing the other's source to
compile or load, which is ordinary bidirectional collaboration and is not a
circular dependency in the sense this entry uses. The distinction matters
because the fixes for a static cycle and for legitimate runtime
back-and-forth are different, and confusing the two produces the
over-correction failure mode described in dimension 11.

## 2. Problem and context

A codebase grows by adding files, packages, or services, and each new unit
imports whatever it needs from its neighbours. Nobody sets out to build a
cycle. It appears gradually, one import at a time, each individually
reasonable, until two units that started independent now each name the other.

The concrete situation that creates it. A module `orders` needs a helper type
defined in `customers`, so it imports `customers`. Weeks later, a different
engineer working in `customers` needs a formatting function that happens to
live in `orders`, so they import `orders`. Neither engineer sees the other's
change, because the two edits land in different pull requests, on different
days, reviewed by different people. The compiler, interpreter, or build tool is
the first thing that sees both edges at once, and by then the cycle already
exists in two places at once in two people's mental models. In languages that
tolerate the cycle at compile time, such as Python, JavaScript, C#, and Java,
nothing stops the build. The cycle surfaces later, as a runtime failure
described in dimension 11, or it surfaces never, and simply sits in the
codebase as permanent coupling.

The context in which the problem arises has three recurring shapes.

- **Convenience imports.** A developer needs one small thing from a
  neighbouring module and imports the whole module rather than extracting the
  small thing, because extraction takes longer than the fix in front of them.
- **Shared vocabulary without a shared home.** Two areas of a system both
  reason about the same concept, an `Order` and a `Customer`, an `Account` and
  a `Ledger`, and each area's type ends up referencing the other's type because
  no third place was ever designated to hold the shared vocabulary.
- **Growth without a layering rule.** The codebase started as one module and
  was split into several as it grew, but the split happened along feature
  lines, not along a dependency direction, so nothing prevents a lower layer
  from importing back into a higher one.

Outside code, the same shape appears in a database schema when table A's
foreign key references table B and table B's foreign key references table A,
in a build system when target A depends on an artifact produced by target B
and target B depends on an artifact produced by target A, and in a container
image build when image A's Dockerfile pulls a layer built from image B and
image B's Dockerfile pulls a layer built from image A. The mechanism differs,
the failure mode is the same, an operation that needs to visit the whole graph
in a fixed order has no order to use.

## 3. Forces

This is a defect, not a design choice with a genuine benefit to weigh against
its cost, so the forces below describe what the cycle takes away rather than a
trade a designer accepts on purpose.

- **Buildability and loadability.** Sacrificed outright in strict environments.
  A language or build tool that refuses cycles, described in dimension 8,
  stops the build entirely, and the force here is not a trade, it is a hard
  wall.
- **Testability.** Sacrificed. A unit inside a cycle cannot be instantiated,
  imported, or compiled alone. Testing it in isolation means dragging in every
  other unit on the cycle, whether the test needs them or not.
  See dimension 15.
- **Deployability.** Sacrificed at the service level. Two services that call
  each other synchronously cannot be released independently without one of
  them tolerating the other's absence during the rollout window, which turns
  an ordinary deployment into a coordinated one.
- **Comprehensibility.** Sacrificed. A reader trying to understand unit A must
  first understand unit B to understand A's behaviour, and B in turn depends
  on A, so there is no starting point from which the story reads forward only.
- **Reuse.** Sacrificed. Extracting one of the units into a separate library
  or a separate repository is impossible without extracting its cycle partner
  along with it, so the unit that looked small turns out to have an
  unexpectedly large blast radius.
- **Initialization order.** Sacrificed in any language with module-level or
  static initialization, described in dimensions 7 and 11. There is no order
  that initializes both units correctly if each one's initialization needs a
  finished value from the other.
- **Nothing is favoured.** Unlike every other entry in this catalog, a
  circular dependency has no force it protects in exchange for the forces it
  gives up. The one apparent benefit, that a developer did not have to stop
  and design a shared abstraction, is a short-term convenience, not a
  structural advantage, which is why this entry is filed under anti-patterns
  rather than under patterns.

## 4. Applicability and non-applicability

There is no applicability list for this entry in the sense the rest of the
catalog uses the term, because nobody should deliberately introduce a static
circular dependency. What belongs here instead is the boundary between what
counts as this anti-pattern and what looks similar but is not, because
mistaking one for the other causes real damage in both directions, described
further in dimension 11.

This IS a circular dependency, and should be fixed.

- Module A's `import` or `require` statement names module B, and module B's
  `import` or `require` statement names module A, whether directly or through
  a chain of other modules.
- Class A's constructor, field type, or method signature names class B, class
  B's constructor, field type, or method signature names class A, and neither
  reference is behind an interface that could be satisfied by something else.
- Package or namespace A contains a source file that imports something from
  package B, and package B contains a source file that imports something from
  package A, even if no single file references itself.
- Build target A declares target B as a build dependency, and target B
  declares target A as a build dependency.
- Database table A has a foreign key into table B, and table B has a foreign
  key into table A, with neither key nullable or deferred, so neither row can
  be inserted first.

This is NOT a circular dependency, and reaching for the fixes in dimension 14
here is the over-correction described in dimension 11.

- **Two objects that hold references to each other at runtime through an
  interface, where each side's compiled unit only names the interface.**
  A parent holding a list of children and each child holding a back-reference
  to its parent, mediated through an interface both sides already depend on
  independently, is the Observer or Composite shape, not a build-time cycle.
- **Two services that call each other's HTTP or message API without either
  one importing the other's source or build artifact.** This is ordinary
  service collaboration. The concern here, if any, is a runtime coupling
  concern such as cascading failure, addressed by circuit breakers and
  timeouts, not by this entry.
- **A callback or event handler passed from A into B, where B stores it and
  calls it later.** B depends only on the function type, which usually lives
  in a shared interface or in the language itself, not on A's concrete type.
  This is the Observer pattern working as intended.
- **Mutual recursion inside a single function or a single small module,
  such as an even/odd predicate pair or a recursive-descent parser's
  mutually recursive grammar rules.** These functions call each other, but
  they are declared in the same compilation unit and do not create a
  cross-module dependency edge. Most languages resolve this on their own,
  through forward declaration or hoisting, with no special design needed.
- **A single self-contained subsystem where two internal collaborators
  legitimately need to see the whole of each other, such as a scanner and a
  parser sharing one grammar file.** When both halves are always deployed,
  tested, and released together and never separately, the coupling is a
  cohesion decision, not a defect, though it should still live inside one
  package rather than spanning two, per dimension 5.

## 5. Structure

Circular dependency is not built from named participants the way a design
pattern is, since it is the absence of a design rather than the presence of
one. What follows names the roles that appear once a cycle exists, so that the
fixes in dimension 14 have something concrete to refer to.

- **Cycle members.** The set of units, of whatever granularity applies,
  whose dependency edges form the cycle. A cycle needs at least two members.
  Most real cycles found in production code have between two and five, and a
  cycle involving dozens of units is usually the symptom of a module boundary
  that was never drawn at all rather than of many small individual mistakes.
- **Cycle edge.** A single directed dependency, A imports B, expressed as
  whatever the language or system calls an import, a reference, a foreign
  key, or a build dependency. A cycle is a sequence of edges that returns to
  its origin, A to B to C to A.
- **Shortest offending edge.** Among the edges in a cycle, the one added most
  recently, which is usually also the one that is cheapest to remove because
  it is the one least entangled with everything else. Tooling described in
  dimension 16 can identify this from version control history even when it
  cannot identify it from the code alone.
- **Extraction target.** A new unit, created to hold whatever both cycle
  members need from each other, so that the two original members can each
  depend on the new unit instead of on each other. This is the shared
  vocabulary home missing from dimension 2, made concrete.
- **Consumer.** Any code outside the cycle that tries to use one of the cycle
  members. The consumer is where the cost of the cycle is actually paid,
  because the consumer's build, test, or deploy now transitively pulls in
  every member of the cycle.

## 6. ASCII structure diagram

```
   BEFORE. the defect

   +-------------+   imports   +-------------+
   |   Orders    | ----------> |  Customers  |
   |             | <---------- |             |
   +-------------+   imports   +-------------+

   Neither module can be loaded, compiled, tested, or extracted alone.
   A consumer of Orders transitively pulls in all of Customers, and
   vice versa, regardless of how much of Customers Orders actually uses.


   AFTER. Dependency Inversion (dimension 14, path A)

   +-------------+             +-----------------------+
   |   Orders    | ----------> |  CustomerSummary       |
   |             |             |  (interface, shared)   |
   +-------------+             +-----------------------+
                                          ^
                                          |
                                +-------------+
                                |  Customers  |
                                +-------------+

   Orders depends only on the interface. Customers implements it.
   The edge from Customers to Orders is gone. Orders can be built,
   tested, and reused without Customers ever being present.


   AFTER. Extract Shared Kernel (dimension 14, path B)

              +-------------------------+
              |     SharedVocabulary    |
              |  (CustomerId, Money)    |
              +-------------------------+
                    ^             ^
                    |             |
        +-------------+     +-------------+
        |   Orders    |     |  Customers  |
        +-------------+     +-------------+

   Both original modules depend downward on a new, smaller module that
   neither of them depends on the other for. No edge runs upward.
```

## 7. Dynamics

A cycle has no interesting runtime dynamics of its own, since it is a static
graph property, but three runtime consequences of that static property are
worth tracing explicitly, because they are where a cycle is actually felt.

**Module-level initialization order (the Node.js and Python case).** When a
language executes top-level code in a module as a side effect of importing
it, and two modules import each other, whichever module is imported first
finishes its own initialization only after handing back an incomplete version
of itself to the second module, which then finishes and hands a complete
version back. The sequence below traces the Node.js `require()` case exactly
as node's own documentation describes it, quoted in full in dimension 18,
reference 3.

```
main.js requires a.js requires b.js requires a.js (again)
  |
  |-- a.js begins executing
  |     exports.done = false
  |     a.js requires b.js  -----------------------> b.js begins executing
  |                                                      exports.done = false
  |                                                      b.js requires a.js (cycle!)
  |                                                        Node does not re-run a.js.
  |                                                        It hands back a.js's exports
  |                                                        object AS IT STANDS RIGHT NOW,
  |                                                        which only has done = false.
  |                                                      b.js sees a.done === false
  |                                                      b.js finishes, exports.done = true
  |     b.js returns to a.js  <-----------------------  b.js done
  |     a.js sees b.done === true   (correct, b finished first)
  |     a.js finishes, exports.done = true
  |-- a.js done
  |
main.js now has correct, fully finished copies of both a.js and b.js,
but any code that ran DURING the cycle, inside either module's top level,
saw a partially initialized version of the other module.
```

**Constructor injection order (the Spring case).** A dependency injection
container that builds objects by calling constructors, where A's constructor
needs a finished B and B's constructor needs a finished A, has no legal order
to call either constructor in, because each one requires the other to already
exist. Spring's container detects this at container startup and raises
`BeanCurrentlyInCreationException` rather than looping or returning a broken
object, described further in dimension 9 and cited in dimension 18, reference
4.

**Static initializer deadlock or wrong-value race (the JVM class-loading
case).** When class A's static initializer reads a static field of class B,
and class B's static initializer reads a static field of class A, the JVM's
per-class initialization lock can either serialize the two threads into a
deadlock if they are loaded concurrently from different threads, or, if
loaded from a single thread, silently hand back the default value, zero or
null, for whichever field has not been assigned yet, because the JVM
specification requires that a class currently being initialized is treated as
already initialized by the thread doing the initializing, to avoid the
deadlock at the cost of correctness. This is engineering judgement drawn from
common JVM class-loading behaviour, not a claim about one specific vendor's
implementation, and is stated here as such rather than dressed as a specific
sourced fact.

## 8. Implementation variants

There is no correct implementation of a circular dependency, since the entry
describes a defect. What varies across languages and toolchains is how
aggressively the compiler or loader detects and reacts to a cycle, which
changes how visible the defect is and how urgently it must be fixed.

**Hard-refused at compile time.** The Go compiler treats an import cycle as a
compile error and refuses to build, reporting the cycle explicitly, per widely
known Go toolchain behaviour. This is stated as engineering judgement rather
than as a sourced claim in this pass, because live verification of the exact
compiler-error wording against a canonical page did not succeed during this
session, and is flagged plainly at the bottom of dimension 18 rather than
presented as confirmed. Assuming the behaviour holds, it is the strictest
stance among mainstream languages, meaning a Go codebase by construction
cannot carry a cycle into production, though a large enough Go codebase can
still suffer the design-quality symptoms of near-cycles, described in
dimension 11, where two packages are prevented from directly cycling but
achieve the same coupling through a third package that both depend on and
that depends on neither.

**Tolerated with a defined resolution rule.** Node's CommonJS module system
and Python's import system both allow a cycle to exist and define exactly what
happens when it is hit, an incomplete object is handed back rather than an
infinite loop or an error, as traced in dimension 7. ECMAScript modules add
live bindings on top of this, so a circular ESM import can, in some cases,
see values update after both modules finish, which is a genuine language
feature rather than a bug, but it does not remove the ordering hazard
described in dimension 11 for values read during the cycle itself.

**Tolerated with a runtime exception on detection.** Java's class loader and
Spring's bean container both allow the class files or bean definitions to
exist with a cycle, and instead raise a specific, named exception at the
moment the cycle is actually exercised, `BeanCurrentlyInCreationException` in
Spring's constructor-injection case, described in dimension 9. This makes the
defect visible at application startup rather than at compile time, later than
Go's stance but earlier than a language that stays silent.

**Silently tolerated at the schema level.** A relational database with
foreign key constraints allows two tables to reference each other. Nothing in
standard SQL DDL rejects this at `CREATE TABLE` time. The constraint only
becomes a practical problem the first time a row must be inserted into either
table, described in dimension 11, and most schema tools that flag it, such as
a migration linter, do so as an opt-in check rather than a language-level
refusal.

**Silently tolerated at the build-target level.** Build systems such as Make
detect and refuse a cycle between explicit targets, but a monorepo's package
manager, if it resolves dependencies lazily rather than up front, can allow
two workspace packages to depend on each other without failing until
something tries to actually build the full closure, at which point the
failure mode matches the compile-time or schema-level cases above depending
on the underlying language.

**Detected only by external tooling, never by the language itself.** Some
languages provide no built-in detection at all and rely entirely on a
separate static analysis tool, run in CI, to catch a cycle before it merges.
This is the weakest stance, since it depends on the tool being installed,
configured correctly, and actually run, and a cycle that slips past it
behaves exactly as if no detection existed. Dimension 16 covers the tooling
that fills this gap.

## 9. Known production uses

Framing note. Because this is an anti-pattern, "known production use" does
not mean a system that deliberately employs the pattern for benefit, the way
it would for a design pattern. It means a real, named system whose
documentation explicitly describes how it detects, prevents, or reacts to a
circular dependency, which is evidence that the problem is real enough for
that system's authors to have built a specific, documented response to it.

**Node.js, CommonJS module resolution.** The official Node.js documentation
carries a dedicated section titled "Cycles" describing exactly what happens
when `a.js` and `b.js` require each other, including a worked three-file
example and its exact console output, quoted and traced in dimension 7.
Node.js documentation, "Modules. CommonJS modules", section "Cycles",
https://nodejs.org/api/modules.html#cycles, verified 2026-08-02.

**Python, the `import` statement and its Frequently Asked Questions entry.**
The official Python Frequently Asked Questions documents circular imports as
a named, recurring problem, distinguishes the case that works, `import
module`, from the case that fails, `from module import name` at top level
when the name is not yet defined, and gives four named remediation
strategies attributed to specific contributors including Guido van Rossum.
Python Software Foundation, "Python FAQ", "Programming FAQ", the entry on
using import inside a module,
https://docs.python.org/3/faq/programming.html, verified 2026-08-02.

**Spring Framework, constructor-based dependency injection.** The Spring
Framework reference documentation describes the circular dependency scenario
between two constructor-injected beans by name, states that the container
detects the circular reference at runtime and throws
`BeanCurrentlyInCreationException`, and recommends setter injection as the
documented workaround. Spring Framework reference documentation, "The IoC
Container", "Dependency Injection", section "Circular dependencies",
https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-collaborators.html,
verified 2026-08-02.

**ArchUnit, automated cycle detection as a CI gate.** ArchUnit, a Java
architecture testing library, ships a dedicated feature, `beFreeOfCycles()`,
for asserting that a set of package slices contains no dependency cycle, and
documents both the assertion syntax and an underlying `CycleDetector` API for
custom checks. This is direct evidence that cyclic dependencies between Java
packages are common enough in practice to warrant a first-class, named
testing feature rather than an incidental one. ArchUnit User Guide, section
"4.7. Cycle Checks" and section "8.2. Slices",
https://www.archunit.org/userguide/html/000_Index.html, verified 2026-08-02.

## 10. Consequences

Positive. There are none that belong to the cycle itself. Any local
convenience gained, avoiding a short pause to design a shared abstraction, is
not a consequence of the cycle existing, it is the absence of the cost that
avoiding the cycle would have paid, and it is paid back with interest at every
later point the cycle is touched. This entry records that plainly rather than
inventing a benefit to keep the dimension symmetrical with the rest of the
catalog.

Negative.

- Neither cycle member can be built, tested, imported, or reused
  independently of the other, described fully in dimensions 3 and 15.
- Initialization order becomes language-defined rather than
  programmer-defined, and the language's resolution rule, described in
  dimension 7, can hand code a value that has not been fully computed yet,
  producing a bug that depends on which module happens to be imported first
  by the entry point, which is itself an accident of the codebase's history
  rather than a designed contract.
- The cycle grows. Once two units may reference each other, there is no
  structural reason for a third unit not to join the cycle, and every
  addition makes the next fix more expensive, since dimension 14's
  extraction techniques get harder as the number of cross-references grows.
- Change amplification. A change to either cycle member risks needing a
  matching change to the other, because each one is partly shaped by what the
  other currently expects of it, and the two are usually not owned by the
  same person or team by the time the cycle is old enough to notice.
- The dependency graph stops being a reliable map of the system. A reader,
  a build tool computing what needs to rebuild, or an automated impact
  analysis that assumes a directed acyclic graph, either produces wrong
  answers or refuses to run, because the mathematical guarantees those tools
  rely on, described in dimension 17's tooling notes, require acyclicity.
- At the service level, a cycle in the call graph, not merely the build
  graph, means neither service can start cleanly from zero if both are down
  and each waits for the other to answer a health check before declaring
  itself ready, a distributed-systems variant of the deadlock described in
  dimension 11.

## 11. Failure modes and misuse

**The undefined-value bug.** Symptom. A value that is `undefined`, `None`, or
a stale default appears at runtime in code that looks, on inspection, like it
assigns that value correctly, and the bug reproduces only when the module
import order changes, for instance after reordering unrelated imports at the
top of the entry file, or after a bundler changes its module concatenation
order. Cause. Code executing during the window described in dimension 7 read
a cycle partner's export before that partner finished initializing. Fix. Move
the cross-cutting reference out of top-level, import-time code and into a
function body that only runs after both modules have finished loading, or
apply one of the dimension 14 extractions so the read no longer needs to
cross the cycle at all.

**`BeanCurrentlyInCreationException` and its equivalents.** Symptom. A
dependency injection container fails to start, with an exception whose
message names two or more of the application's own classes and describes them
as currently being created. Cause. Two or more beans are wired together
through constructor injection in a cycle, as described in dimension 7. Fix.
Switch the cycle to setter or field injection as Spring's own documentation
recommends, which defers one side's assignment until after both objects
exist, or, preferably, apply dependency inversion so the container never has
to construct the two beans out of order at all.

**The unresolvable foreign key insert.** Symptom. An `INSERT` into either of
two mutually referencing tables fails a foreign key constraint no matter which
table is inserted into first, because the referenced row in the other table
does not exist yet. Cause. Both foreign keys are declared `NOT NULL` with no
deferred constraint checking. Fix. Make at least one of the two foreign keys
nullable and insert with that column null, then `UPDATE` it once the other
row exists, or use a deferred constraint that is checked at transaction
commit rather than at statement execution, or, at the schema design level,
recognise that a true two-way required reference usually means a third
table, a join or link table, is the correct model, mirroring the shared
extraction target in dimension 5.

**The build-tool refusal that looks like a language bug.** Symptom. A
developer new to a strict language reports that "the compiler is broken"
because a perfectly reasonable-looking pair of files will not build together.
Cause. The language, correctly, refuses an import cycle, as Go's compiler is
widely understood to do. Fix. This is not a bug to work around, it is the
language doing its job. Apply a dimension 14 extraction. The failure mode
here is the developer's misdiagnosis, not the tool's behaviour, and the fix
is education plus the same refactor that would be needed anyway.

**Over-correction. Splitting apart legitimate mutual collaboration.**
Symptom. A codebase review flags "circular dependency" on two classes that
merely hold references to each other through interfaces, such as a parent and
child in a tree structure, or an Observer's subject and its observers, and the
fix applied removes the back-reference entirely, forcing every caller to pass
extra context manually that the removed reference used to supply for free.
Cause. The reviewer or the tool applied the label to a legitimate
bidirectional runtime association, described as a non-applicable case in
dimension 4, rather than to an actual static build-time cycle. Fix. Confirm
whether the two units' compiled or interpreted units genuinely name each
other's concrete type at the module or package level, versus merely holding a
reference typed to a shared interface or base class. Only the former is this
anti-pattern. Reverse the over-correction and restore the back-reference if it
turns out to be the latter.

**The hidden cycle through a third party.** Symptom. Two packages, A and B,
never directly import each other and a naive check finds no cycle, yet
changing either one still triggers a rebuild or a re-test of the other, and
the coupling feels exactly like a cycle in practice. Cause. Both A and B
import package C, and C imports back into A, so the cycle is A, C, back to A,
with B along for the ride because B also touches C. A pairwise check of A and
B alone misses it. Fix. Run a whole-graph cycle detector, described in
dimension 16, rather than checking suspected pairs by hand, since a real
cycle can route through any number of intermediate units.

**The dependency that a mock hides.** Symptom. Unit tests for module A pass
in isolation using a hand-written test double for module B, giving false
confidence that A can be deployed or extracted without B, when in production
the real B still imports back into A and the cycle is very much present.
Cause. Mocking a cycle partner in a test removes the SYMPTOM, the test
failing to compile or import, without removing the CYCLE, which still exists
in the real dependency graph the mock stands in for. Fix. Use a static
dependency graph tool as in dimension 16 to verify the cycle is actually gone
from the source, not merely absent from the test's mocked view of the world.

## 12. Trade-off matrix

Framing note. A trade-off matrix normally compares a pattern against
alternative patterns that solve the same problem with different costs. This
entry has no alternative that keeps the cycle, so what the table compares
instead is the anti-pattern itself against the named remediation techniques
from dimension 14 and against the design discipline that prevents it from
ever appearing, across the forces named in dimension 3.

| Force | Circular Dependency (the defect, left in place) | Dependency Inversion (dimension 14, path A) | Extract Shared Kernel (dimension 14, path B) | Mediator pattern | Layered architecture discipline (upfront prevention) |
|---|---|---|---|---|---|
| Buildability | Broken or fragile, language dependent | Restored. Both sides depend downward only | Restored. Both sides depend downward only | Restored. Collaborators depend on the mediator, not each other | Never broken, by construction |
| Testability of either unit alone | Impossible without the partner | Full. Interface can be faked in a test | Full. Kernel is usually pure data, trivial to construct | Full. Mediator can be faked | Full, by construction |
| Cost to introduce | Zero, which is exactly the trap | Medium. Design an interface, wire it | Medium to high. Identify what is genuinely shared | Medium to high. New coordinating type | Highest, paid continuously as a review discipline |
| Cost to remove later | Grows with codebase age | Not applicable, already the fix | Not applicable, already the fix | Not applicable, already the fix | Not applicable, prevention has no removal cost |
| Where responsibility for the shared concept lives | Nowhere, split across both units | Whichever unit the interface's OWNER already suits, usually the lower layer | The new kernel, explicitly | The mediator, explicitly | Whichever layer the architecture assigns it to |
| Best suited when | Never. Always a defect to fix | One side's dependency is a stand-in for behaviour the other implements | Both sides need the same DATA, not behaviour | Three or more units need active back-and-forth coordination | The team can enforce the discipline before code lands, via CI per dimension 16 |
| Risk of over-application | Not applicable | Turning a truly one-directional relationship into an unneeded interface | Turning a small, genuinely local concept into a shared module nobody owns | Adding a mediator for a two-unit relationship that a plain interface would fix more simply | False positives flagging legitimate collaboration, dimension 11 |

Reading of the table. Dependency Inversion is the right choice when the
mutual need is really "each side needs to CALL the other's behaviour" and one
side's role can be expressed as an interface the other implements. Extracting
a shared kernel is the right choice when the mutual need is really "each side
needs to REFER TO the same concept," a value object, an identifier type, or a
constant, rather than to call behaviour. A Mediator earns its extra type once
three or more units would otherwise all need direct references to each
other, since at that point the number of pairwise edges a mediator removes
grows faster than the one type it costs. Layered architecture discipline is
prevention rather than cure, and is the only entry in the table with zero
cost once a cycle already exists, precisely because it stops one from
forming in the first place.

## 13. Related and incompatible patterns

- **Dependency Inversion Principle.** The primary cure. Named as one of two
  remediation techniques in Robert C. Martin's original formulation of the
  Acyclic Dependencies Principle, cited in dimension 1. Breaking a cycle by
  having the lower-level unit depend on an abstraction that the higher-level
  unit's needs are expressed through, rather than depending on the concrete
  higher-level unit directly, removes one of the two edges in the cycle by
  construction.
- **Facade.** A Facade placed in front of a subsystem can absorb the
  many-to-many references that would otherwise form a cycle between two
  subsystems, by giving the outside world, and any collaborating subsystem,
  one narrow surface to depend on instead of the subsystem's internals. This
  reduces the number of cross-boundary edges that could ever participate in a
  cycle.
- **Mediator.** Where three or more units would otherwise reference each
  other directly, a Mediator collects the coordination logic into one new
  type that every participant depends on, and no participant depends on any
  other participant. This is the direct generalisation of the two-unit
  Extract Shared Kernel fix in dimension 14 to more than two units.
- **Observer.** Frequently mistaken for a circular dependency and is not one,
  as covered in dimension 4 and dimension 11, because the subject depends on
  an Observer interface, not on any concrete observer, and any concrete
  observer that depends on the subject depends on it through the subject's
  own public interface, not through a mutual pair of concrete-to-concrete
  references.
- **Composite.** The parent-to-child and child-to-parent references in a
  Composite tree are exactly the legitimate bidirectional runtime association
  covered in dimension 4's non-applicable list, provided both sides are
  declared inside the same module or package rather than importing each
  other across a module boundary.
- **Layered Architecture.** The standing prevention. An architecture with an
  enforced, one-directional layering rule, where a lower layer's code is
  physically forbidden by convention or by a build rule from importing a
  higher layer, cannot develop a cycle across layers by construction, though
  it remains possible within a single layer unless that layer is itself
  further subdivided.
- **God Object.** Actively related in the opposite direction. A God Object
  is frequently the third-party unit at the centre of the hidden cycle
  described in dimension 11, since a class that everything imports and that
  imports many things back is structurally likely to sit on more cycles than
  a small, focused unit would.
- **Service Locator.** Can hide a circular dependency rather than fix it. If
  unit A avoids importing unit B directly by looking B up through a shared
  locator at runtime, the compile-time cycle disappears, but the runtime
  coupling and the initialization-order hazard from dimension 7 do not,
  since both units still need each other to function. This is a case where a
  fix for one problem, the compile-time cycle, quietly reintroduces the
  problem under a different name, described further under the anti-patterns
  family's own Service Locator entry.

## 14. Refactoring path in and out

There is no "path in," since nobody should deliberately introduce this
defect. What follows is a single ordered path out, with two named
destinations depending on what the cycle members actually need from each
other, matched to the two AFTER diagrams in dimension 6.

1. **Find the cycle, do not guess it.** Run a whole-graph static dependency
   tool against the codebase, described in dimension 16. Hand-tracing imports
   across more than two or three files is unreliable and misses the hidden,
   third-party-routed cycle from dimension 11. Confirm the exact list of
   edges that form the cycle before touching any code.
2. **Classify what actually crosses each edge.** For every edge in the
   cycle, read the code that uses the import and ask whether it calls
   BEHAVIOUR defined on the other side, or whether it only reads or
   constructs a VALUE type defined on the other side. This classification
   decides which of the two destinations below applies, and a real cycle
   frequently needs both, one edge fixed one way and the other edge fixed
   the other way.
3. **Path A. Dependency Inversion, when an edge crosses for behaviour.**
   Define an interface, owned by whichever side is conceptually lower level
   or more stable, that describes only the operations the OTHER side
   actually calls, no more. Have the higher-level or less stable side depend
   on that interface instead of on the concrete type. Have the side that
   used to be depended upon implement the interface. This removes the edge
   that pointed the wrong way, leaving one edge pointing down through the
   interface and none pointing back up. Run the full test suite after this
   step, since it changes a concrete dependency into an abstract one and can
   surface places that relied on members the new interface does not expose.
4. **Path B. Extract Shared Kernel, when an edge crosses for a value type.**
   Create a new, small module that contains only the type both sides need to
   refer to, an identifier, a value object, an enum, a constant. Move that
   type's definition into the new module. Update both original units to
   import the new module instead of importing each other for that type. Keep
   the new module deliberately narrow, since a kernel that accumulates
   unrelated types over time becomes the God Object described in dimension
   13 and a magnet for the next cycle.
5. **Re-run the graph tool.** Confirm the cycle no longer appears in the
   dependency graph, not merely that the specific two files that started the
   investigation no longer import each other, since the hidden-cycle failure
   mode in dimension 11 means a pairwise eyeball check is not sufficient
   proof.
6. **Add the regression guard from dimension 16 before closing the work.**
   A cycle fixed without a standing check against its return is a cycle that
   comes back the next time someone adds a convenience import under time
   pressure, which is exactly how the original one was created, per
   dimension 2.

Removing a fix that overcorrected. If dimension 11's over-correction failure
mode occurred, and a legitimate bidirectional association was mistakenly
broken apart, restore the direct reference and instead add a comment or a
project-level exception in the cycle-detection tool's configuration, named at
the specific pair, so the check does not fire on that pair again while still
catching a genuinely new cycle elsewhere.

## 15. Testing and verification

There is nothing a circular dependency makes easier to test. Everything below
describes what the cycle makes harder, and the standing verification that
keeps it from reappearing.

Harder because of the defect.

- Neither cycle member can be unit tested by importing only that unit. A test
  file for module A transitively pulls in module B, and any expensive
  initialization, database connection, network client, or heavy computation
  that B performs at import time now happens inside A's test run whether the
  test needs it or not.
- A test double for one cycle member, written to make the other member's
  tests run in isolation, hides the cycle rather than removing it, described
  as its own failure mode in dimension 11, so passing unit tests give false
  confidence about extractability.
- Integration tests that depend on startup order become flaky specifically
  because of the initialization-order hazard from dimension 7, a test that
  passes when run alone and fails when run as part of a larger suite is a
  classic symptom, because the entry point that imports things first differs
  between the two runs.

Techniques that apply.

- **Whole-graph cycle assertion as a test.** Treat "the dependency graph has
  no cycles" as a testable property of the codebase, not merely a code
  review nicety. ArchUnit's `beFreeOfCycles()`, cited in dimension 9, is a
  direct example of this technique implemented as a JUnit-runnable
  assertion, so a cycle introduced by any commit fails the build the same
  way a broken unit test would.
- **Isolation build as a test.** For languages with strict compile-time
  detection, such as Go, the build itself is the cycle test, and no
  additional tooling is needed. For languages that tolerate cycles, a CI
  step that attempts to import or instantiate each top-level module alone,
  with its declared dependencies stubbed out entirely rather than mocked,
  will fail loudly if that module secretly needs something back from a
  supposed dependent, which a mock would otherwise hide.
- **Container startup as an integration test.** For dependency-injection
  frameworks such as Spring, a test that boots the full application context
  and asserts it starts without a `BeanCurrentlyInCreationException` or
  equivalent is a direct, cheap regression test for the constructor-injection
  cycle described in dimension 7, and should run on every change to wiring
  configuration.
- **Import-order fuzzing, for languages with the dimension 7 hazard.** Where
  practical, running the same test suite with the entry point's import
  order deliberately varied, for instance by alphabetising versus
  reverse-alphabetising the top-level imports, surfaces order-dependent
  bugs from a lingering cycle that a single fixed run would never exercise.

## 16. Observability signals

A cycle is a structural property of source code, not a runtime event, so most
of what is useful here is measured at build or analysis time rather than read
off a production dashboard, with one exception for the runtime failure modes
in dimension 11.

What to record and check.

- **A cycle count metric from static analysis, tracked over time.** Whatever
  tool is used, madge for JavaScript and TypeScript module graphs, ArchUnit
  or a comparable dependency-checking library for Java package graphs, or a
  language's own compiler for languages that refuse cycles outright, run it
  in CI on every change and fail the build on an increase in cycle count from
  the previous known-good baseline. Tracking the count over time, rather than
  only gating on zero, allows an existing codebase with legacy cycles to
  adopt the check without an immediate, disruptive stop-the-world fix,
  while still preventing new cycles from being added.
- **A dependency graph visualization, regenerated on demand.** A rendered
  graph, even an approximate one, makes a hidden multi-hop cycle, the kind
  described in dimension 11 that a pairwise check misses, visually obvious
  as a loop in the picture in a way a flat list of edges is not.
- **Bean or container startup failures, logged with the full exception
  chain.** For frameworks that raise a named exception on a circular
  constructor dependency, such as Spring's `BeanCurrentlyInCreationException`
  cited in dimension 9, the exception message names the beans involved
  directly, so a startup log that captures the full stack trace and
  message, rather than one swallowed by a generic startup failure handler,
  turns an opaque "the app will not start" into a plain, usable list of
  exactly which beans are in the cycle.
- **Import-time duration, per module, in languages where import runs code.**
  A module whose import-time execution takes unusually long, or that
  performs I/O, is worth flagging on its own merits, and it is also more
  dangerous to have inside a cycle, because the initialization-order hazard
  in dimension 7 is worse the more work happens during the vulnerable
  window.

A healthy state. The tracked cycle count is zero, or is at its established
baseline and has not increased across the most recent set of merged changes.
The dependency graph visualization, when regenerated, shows a graph with no
loops, or shows only the specific, reviewed, and intentionally-excepted
loops noted in dimension 14's over-correction recovery step. Container
startup completes without a circular-dependency exception in the log.

A failing state. The cycle count metric increases on a change that added no
new legitimate architectural boundary, which is the signal to open dimension
14's refactor before the change merges rather than after. A container fails
to start with a circular-dependency exception naming beans that were not
expected to depend on each other, which points directly at a recent wiring
change. A previously reliable integration test begins failing intermittently
with symptoms matching dimension 11's undefined-value bug, which is the
runtime signature of an existing cycle whose partially-initialized window is
now being hit under a new code path or a new import order introduced by an
unrelated change elsewhere in the codebase.

## 17. Security and privacy implications

The pattern itself, being an absence of good structure rather than a feature,
has no data-handling behaviour of its own, so most of what follows is an
analytical implication of the structural defect rather than a claim about
what any specific tool does. Two implications are concrete enough to state
plainly, and a third is a caution against overclaiming.

**Weakened blast-radius reasoning for a security review.** A dependency graph
is one of the standard inputs a security reviewer uses to answer "if this
component is compromised, what else is reachable from it." When two
components are joined by a cycle, that answer collapses, since a compromise of
either component gives an attacker a path that eventually reaches everything
the other component can reach too, and the two components' privilege
boundaries, if any were intended, are undermined by the fact that they were
never actually separable in the first place. This is a genuine implication of
the structural defect and is stated as engineering judgement rather than as a
sourced fact about a specific incident, because the underlying claim, that
security review relies on accurate dependency graphs, is analytical rather
than empirical.

**Supply-chain attack surface increase, for the package-level case.** When the
cycle spans two independently published packages rather than two modules
inside one codebase, both packages must be resolved and installed together,
and a compromise of either package's publishing credentials, described
generally in supply-chain security guidance, now affects both packages'
consumers rather than one, because neither package can be adopted or updated
without the other. This is a direct consequence of the reuse cost named in
dimension 3, applied to the specific case of third-party packages rather than
internal modules.

**No claim of a direct exploit is made here.** A circular dependency by itself
is not a known, named vulnerability class the way an injection flaw or a
buffer overflow is, and this entry does not claim it is. Where a security
concern is real, it is downstream of the structural weakness described above,
reduced auditability and coupled attack surface, rather than a defect an
attacker can trigger directly through the cycle itself. Saying otherwise
would be inventing a concern this entry cannot support with a source.

Privacy is silent here in the same way. The pattern does not itself move,
retain, or expose personal data. Where a cycle happens to join a module that
handles personal data with one that does not, the practical effect is that
the data-handling module's code cannot be reviewed, tested, or deployed
separately from the non-data-handling one, which is a data-minimization and
auditability concern worth naming to a privacy reviewer, but it is, again, a
consequence of the structural coupling from dimension 3 rather than a
property of the cycle acting on the data directly.

## Code examples

Three languages, chosen to show the anti-pattern in three genuinely different
mechanisms. TypeScript shows the module-import cycle and the dependency
inversion fix that removes it. Python shows the same import cycle, since
Python's behaviour differs from Node's in exactly the way described in
dimension 9's citation, and shows the function-local import workaround
documented by the Python Frequently Asked Questions. Java shows the
constructor-injection cycle a dependency-injection container detects, and
the setter-injection fix.

### TypeScript

The broken pair. `orders.ts` and `customers.ts` import each other directly.

```typescript
// The two classes below are written as if they lived in two files,
// orders.ts and customers.ts, that import each other directly, shown
// here in one block only so the example compiles standalone. orders.ts
// would read "import { Customer } from './customers'" and customers.ts
// would read "import { Order } from './orders'", which is the cycle.

class Order {
  constructor(public id: string, public buyer: Customer) {}
  describe(): string {
    return `${this.id} for ${this.buyer.name}`;
  }
}

class Customer {
  orders: Order[] = [];
  constructor(public name: string) {}
  placeOrder(order: Order): void {
    this.orders.push(order);
  }
}
```

The fix, dependency inversion. `orders.ts` depends only on an interface that
describes what it actually needs, `customers.ts` implements it, and the
back-edge disappears.

```typescript
// Again written as three files (buyer.ts, orders.ts, customers.ts) in
// one block so the example compiles standalone. buyer.ts would export
// the Buyer interface, orders.ts would import only Buyer from it, and
// customers.ts would import Buyer from buyer.ts and Order from orders.ts,
// which is the one-directional edge the fix leaves behind, no edge
// running back from orders.ts to customers.ts.

interface Buyer {
  name: string;
}

class Order {
  constructor(public id: string, public buyer: Buyer) {}
  describe(): string {
    return `${this.id} for ${this.buyer.name}`;
  }
}

class Customer implements Buyer {
  orders: Order[] = [];
  constructor(public name: string) {}
  placeOrder(order: Order): void {
    this.orders.push(order);
  }
}

const c = new Customer("Ada");
const o = new Order("O-1", c);
c.placeOrder(o);
console.log(o.describe());
```

### Python

The broken pair, matching the exact failure the Python Frequently Asked
Questions page describes for `from module import name` at top level, cited
in dimension 9.

```python
# The two classes below stand in for two files, orders.py and
# customers.py, that import from each other, shown in one block so the
# example runs standalone. orders.py would read "from customers import
# Customer" and customers.py would read "from orders import Order",
# which is the cycle. If customers.py is imported first, Python raises
# ImportError on "from orders import Order" because orders.py has not
# finished defining Order yet, exactly the failure the Python FAQ
# describes for this shape.


class Order:
    def __init__(self, order_id: str, buyer: "Customer") -> None:
        self.order_id = order_id
        self.buyer = buyer

    def describe(self) -> str:
        return f"{self.order_id} for {self.buyer.name}"


class Customer:
    def __init__(self, name: str) -> None:
        self.name = name
        self.orders: list["Order"] = []

    def place_order(self, order: "Order") -> None:
        self.orders.append(order)
```

The fix. Move the cross-module read into function scope, exactly as one of
the FAQ's remediation techniques describes, cited in dimension 9, so the
import runs after both modules have finished defining their top-level names.

```python
# Again standing in for two files. orders.py is unchanged, since it
# only ever needed Customer for a type hint, which a string forward
# reference already avoids at runtime. customers.py drops its
# module-level "from orders import Order" and moves the import inside
# the one function that needs it, so by the time the function runs,
# orders.py has fully finished importing.


class Order:
    def __init__(self, order_id: str, buyer: "Customer") -> None:
        self.order_id = order_id
        self.buyer = buyer

    def describe(self) -> str:
        return f"{self.order_id} for {self.buyer.name}"


class Customer:
    def __init__(self, name: str) -> None:
        self.name = name
        self.orders: list = []

    def place_order(self, order) -> None:
        # in the two-file version this import lives inside the
        # function, not at module top level, so it never races the
        # cycle; here Order is already defined above in the same file
        if not isinstance(order, Order):
            raise TypeError("expected an Order")
        self.orders.append(order)


if __name__ == "__main__":
    c = Customer("Ada")
    o = Order("O-1", c)
    c.place_order(o)
    print(o.describe())
```

### Java

The broken pair, the constructor-injection cycle Spring's own documentation
names, cited in dimension 9.

```java
// OrderService.java (the defect)
class OrderService {
    private final CustomerService customerService;

    OrderService(CustomerService customerService) {
        this.customerService = customerService;
    }

    String describe(String orderId, String customerId) {
        return orderId + " for " + customerService.nameOf(customerId);
    }
}

// CustomerService.java (the defect: constructor-injects OrderService back)
class CustomerService {
    private final OrderService orderService;

    CustomerService(OrderService orderService) {
        this.orderService = orderService;
    }

    String nameOf(String customerId) {
        return "Customer-" + customerId;
    }
}

// Neither can be constructed. new OrderService(new CustomerService(???))
// needs a CustomerService, which needs an OrderService, which needs a
// CustomerService, with no base case. This is the exact scenario Spring's
// container detects and reports as BeanCurrentlyInCreationException.
```

The fix, setter injection, exactly as Spring's documentation recommends,
cited in dimension 9, which allows both objects to be constructed with no
arguments first and wired together afterward.

```java
class OrderService {
    private CustomerService customerService;

    void setCustomerService(CustomerService customerService) {
        this.customerService = customerService;
    }

    String describe(String orderId, String customerId) {
        return orderId + " for " + customerService.nameOf(customerId);
    }
}

class CustomerService {
    private OrderService orderService;

    void setOrderService(OrderService orderService) {
        this.orderService = orderService;
    }

    String nameOf(String customerId) {
        return "Customer-" + customerId;
    }
}

public final class Demo {
    public static void main(String[] args) {
        OrderService orders = new OrderService();
        CustomerService customers = new CustomerService();
        orders.setCustomerService(customers);
        customers.setOrderService(orders);
        System.out.println(orders.describe("O-1", "C-1"));
    }
}
```

The stronger fix, applying dependency inversion so the cycle never needs a
workaround, matching the preferred path in dimension 14.

```java
interface CustomerNameLookup {
    String nameOf(String customerId);
}

final class OrderService {
    private final CustomerNameLookup lookup;

    OrderService(CustomerNameLookup lookup) {
        this.lookup = lookup;
    }

    String describe(String orderId, String customerId) {
        return orderId + " for " + lookup.nameOf(customerId);
    }
}

final class CustomerService implements CustomerNameLookup {
    public String nameOf(String customerId) {
        return "Customer-" + customerId;
    }
}

public final class BetterDemo {
    public static void main(String[] args) {
        CustomerService customers = new CustomerService();
        OrderService orders = new OrderService(customers);
        System.out.println(orders.describe("O-1", "C-1"));
    }
}
```

## 18. References

1. Robert C. Martin. "The Acyclic Dependencies Principle". Engineering
   Notebook column, C++ Report, 1996. Cited via its restatement in reference
   2 below, which is the independently checkable, in-print source for the
   principle's chapter-length treatment.
2. Robert C. Martin. *Agile Software Development, Principles, Patterns, and
   Practices*. Prentice Hall, 2002. ISBN 0-13-597444-5. Chapter 28, "The
   Acyclic Dependencies Principle". Source for the naming of the principle,
   the statement that the package dependency graph must contain no cycles,
   and the two named remediation techniques, Dependency Inversion and
   extracting a shared package, that dimension 14 draws from.
3. Node.js documentation, "Modules. CommonJS modules", section "Cycles".
   https://nodejs.org/api/modules.html#cycles
   Verified 2026-08-02. Source for the exact `a.js`/`b.js`/`main.js` example
   and console output traced in dimensions 7 and 9, and for the statement
   about careful planning being needed for cyclic module dependencies to
   work correctly.
4. Python Software Foundation. "Python FAQ", "Programming FAQ", the entry on
   using import inside a module. https://docs.python.org/3/faq/programming.html
   Verified 2026-08-02. Source for the distinction between `import module`
   and `from module import name` under a cycle, and for the four named
   remediation techniques used in dimensions 9 and the Python code example.
5. Spring Framework reference documentation. "The IoC Container", "Dependency
   Injection", section "Circular dependencies".
   https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-collaborators.html
   Verified 2026-08-02. Source for the `BeanCurrentlyInCreationException`
   name, the constructor-injection cycle scenario, and the setter-injection
   recommendation used in dimensions 7, 9, 11, and the Java code example.
6. ArchUnit User Guide. Section "4.7. Cycle Checks" and section "8.2.
   Slices". https://www.archunit.org/userguide/html/000_Index.html
   Verified 2026-08-02. Source for the `beFreeOfCycles()` assertion and the
   `CycleDetector` API cited in dimensions 9, 12, and 15 as a production
   testing technique for package-level cycles.

Unverifiable or not independently sourced in this pass. The JVM
class-loading deadlock and default-value behaviour described in dimension 7
is stated as engineering judgement drawn from generally known JVM
class-initialization semantics rather than tied to a specific verified page
from this pass, and is labelled as such in the text rather than presented as
a sourced claim. The Go compiler's refusal of import cycles, described in
dimension 8 and dimension 11, was attempted against two live sources, the Go
language specification and the `go` command documentation, and neither
page's fetched content contained the specific import-cycle-refusal wording,
so those sentences are stated as widely known properties of the Go
toolchain rather than pinned to a URL verified in this session, and no page
number or URL is attached to them for that reason.
