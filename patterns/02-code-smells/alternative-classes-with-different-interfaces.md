---
name: Alternative Classes with Different Interfaces
slug: alternative-classes-with-different-interfaces
family: 02-code-smells
category: Code Smell, Object-Oriented Abusers
aliases: [Divergent Interfaces, Incompatible Substitutes]
first_described: "Fowler and Beck 1999, revised Fowler 2018"
maturity: canonical
related: [factory-method, template-method, strategy, adapter, extract-superclass]
incompatible_with: []
verified: 2026-08-03
---

# Alternative Classes with Different Interfaces

## 1. Name, aliases, and lineage

The canonical name is Alternative Classes with Different Interfaces. It is
documented as one of the code smells in Martin Fowler, *Refactoring. Improving
the Design of Existing Code*, 2nd edition, Addison-Wesley, 2018, chapter 3,
"Bad Smells in Code". The chapter on smells is credited in the book's own front
matter to Kent Beck, who supplied the taxonomy and the names, while Fowler
wrote the surrounding refactorings that treat each smell. The smell also
appears in the 1999 first edition of the same book under the same name, so the
description below treats the name and the diagnosis as stable across both
editions and cites the current, 2nd edition, text.

Two independent secondary catalogs that summarise Fowler's book state the
definition consistently. sammancoaching.org's code smell catalog gives the
condition as occurring "when you have two or more classes which in theory
should be substitutable for one another, but in practice they have slightly
different interfaces" and names the fix as "unify the interfaces so the
protocols match" (sammancoaching.org, "Alternative Classes with Different
Interfaces", verified 2026-08-03). codesmells.org attributes the smell to the
same source and book, and illustrates it with two classes that implement the
same behaviour under different method names, for example a `Snowman` class and
a `Zombie` class that both implement a "hug" action but expose it as
`hug_snowman()` and `hug_zombie()` respectively, so neither can stand in for
the other even though the underlying logic is identical
(codesmells.org, "Alternative Classes with Different Interfaces", verified
2026-08-03).

The smell has no alias recorded in Fowler's own text. This entry uses
**Divergent Interfaces** as a working short name because several practitioner
write-ups shorten the smell to that phrase, and **Incompatible Substitutes** as
a second alias because it names the failure mode directly. two things that
were meant to be substitutes for each other are not, because their call
surfaces disagree. Neither alias appears in a citable primary source and both
are offered here as description, not as an attested name in the literature.

A derivative catalog site, refactoring-assistant.github.io, classifies the
smell under a section it labels "Object-Oriented Abusers" and recommends
Rename Method and Extract Superclass as the fixes, illustrated with two worked
examples (refactoring-assistant.github.io,
"object-oriented-abusers/alternative-classes-with-different-interfaces",
verified 2026-08-03). That category label is the site's own organisational
scheme built on top of Fowler's list, not a grouping Fowler's book itself uses
in its table of contents, and this entry repeats it only as the label a
working practitioner is likely to encounter when searching for the smell
online, not as a claim about the book's structure.

## 2. Problem and context

Two classes exist in the same codebase that do, in substance, the same job.
One reads configuration from a file and one reads configuration from an
environment, one persists a record to a local cache and one persists it to a
remote cache, one exports a report as CSV and one exports it as JSON. The two
classes were not designed together. They arrived at different times, written
by different people, or one was inherited from an earlier project and the
other was added later for a new requirement. Nobody sat down and asked whether
the two should share a contract, because at the moment each was written it was
the only implementation of its kind and no contract was needed.

The smell appears the moment a third piece of code needs to treat the two
interchangeably. A caller wants to loop over a list of exporters and call the
same method on each, or a caller wants to swap the cache implementation behind
a feature flag without touching the call site. At that moment the difference
in method names, parameter order, return types, or exception behaviour becomes
visible, and the caller is forced into one of two bad shapes, a chain of
`if`/`instanceof` checks that names both concrete classes explicitly, or a
thin wrapper written on the spot that adapts one interface to the other,
usually without a name and without a test, because it was written to unblock
one call site rather than to become a real abstraction.

The context that produces this smell has three recurring shapes. First,
convergent evolution. Two classes are written independently to solve the same
kind of problem and nobody notices the overlap until both already have
callers, so renaming either one risks breaking its own existing callers.
Second, acquired or vendored code. One implementation ships from a library or
a different team with a fixed public interface, and the local implementation
was written before that vendor code arrived, so the two never had a chance to
agree. Third, incremental migration. A team is replacing an old technology
with a new one, for example moving from a blocking I/O API to a non-blocking
one, and for a transition period both the old and the new implementation of
the same responsibility exist side by side, deliberately, with the old one
slated for deletion once the migration completes.

The problem this smell reports is not that duplication exists in the sense of
Duplicated Code, and it is not that a class does too much, which is Fowler's
Large Class smell. The problem is narrower. it is that two things which are
conceptually the same abstraction cannot be used through one variable, one
loop, or one interface, purely because of a naming and shape mismatch that
carries no real information.

## 3. Forces

The forces below are the author's engineering judgement about which pressures
this smell trades against, informed by the fix described in dimension 2, not a
sourced claim from the literature.

- **Substitutability.** This is what the smell reports as broken. Two classes
  that should be interchangeable in a caller's mental model are not
  interchangeable in the type system, so the caller cannot rely on either
  polymorphism or structural typing to treat them the same way.
- **Naming cost versus caller cost.** Fixing the smell almost always means
  renaming a method on at least one of the two classes. That rename is cheap
  to make and expensive to review when the method already has callers,
  because every call site of the renamed method must change too. The smell
  therefore trades a one-time, visible renaming cost against an ongoing,
  invisible cost paid by every future caller who has to remember which class
  uses which name.
- **Local correctness versus system-wide consistency.** Each class, read on
  its own, is fine. The method name it chose made sense in its own file at the
  time it was written. The smell only exists when the two files are read
  together, so it is a property of the codebase's vocabulary, not a property
  of either individual class, and it can persist indefinitely if the two
  classes are never read side by side by the same person.
- **Coupling to the old identity.** Once a class ships with a public method
  name, external code and tests bind to that name. Unifying interfaces
  sacrifices some of that binding stability for the sake of substitutability,
  which is a real cost on a public API and a near-zero cost on an
  internal-only class.
- **Speed of the immediate fix versus depth of the real fix.** The fastest
  local fix, an adapter written at the one call site that needs
  substitutability, resolves the symptom for that call site while leaving the
  underlying vocabulary mismatch untouched for the next caller. The deeper
  fix, unifying the interfaces themselves, costs more up front and removes the
  smell for every future caller at once.

## 4. Applicability and non-applicability

This diagnosis applies when the following hold.

- Two or more classes implement conceptually the same responsibility, and a
  caller either already needs to treat them interchangeably or is very likely
  to need that soon (a second implementation is usually the leading indicator
  that a third is coming).
- The methods that do the equivalent work differ only in surface details, the
  method name, the parameter order, the parameter types where a trivial
  conversion exists, or the return type where a trivial conversion exists.
- No caller currently depends on the difference in name or shape as a
  deliberate signal. If a caller specifically wants to know which concrete
  variant it is talking to and branches on that knowledge for a reason that
  matters, the two are not really substitutes and unifying their interface
  would hide information the caller genuinely needs.
- The two classes are both under your control, or at least one of them is,
  so a rename or an extracted interface is actually possible without
  waiting on an external maintainer.

This diagnosis does **not** apply in the following cases, and treating them as
instances of the smell produces a worse design than leaving the mismatch
alone.

- **The two classes look similar but do genuinely different things.**
  A `Rectangle.area()` and a `Circle.area()` sharing a name is not this smell
  resolved, it is the normal, correct outcome of both classes implementing a
  real `Shape` abstraction; the naming coincidence is because the concept is
  the same, not because of an accidental resemblance. Conversely, forcing a
  shared interface onto two classes because their method bodies happen to
  look alike, when their actual responsibilities differ (one validates input,
  one performs a side effect that validation would silently swallow),
  produces a false abstraction, which is its own, worse code smell.
- **One implementation is a wrapper around a third-party library whose public
  method names you do not control**, and the mismatch is between your code
  and that library's naming convention, not between two implementations you
  wrote. Renaming the library's methods is not possible. The correct response
  here is the Adapter pattern at the boundary, not a rename, and this smell
  entry should not be diagnosed on library code you do not own; diagnose it on
  your own code that wraps the library instead, if that wrapper itself
  diverges from a sibling wrapper you also wrote.
- **The interfaces differ because the underlying semantics differ**, most
  commonly around error handling. A method that returns `null` on a missing
  value and a method that throws an exception on a missing value are not
  interchangeable merely by giving them the same name; unifying the name
  while leaving the error behaviour different creates a caller-visible trap
  that is worse than two honestly different names, because a caller who
  assumes uniform behaviour from the shared name will be wrong for one of the
  two. Fix the semantic mismatch first, or make it explicit in the unified
  contract, before renaming.
- **The two implementations are deliberately transitional**, for example
  during a strangler-fig migration where an old class and a new class
  intentionally coexist with different interfaces while callers are migrated
  one at a time. The mismatch is temporary infrastructure, not a defect, and
  unifying the interface too early can make the migration harder to track,
  because it removes the visible signal of which callers still use the old
  path.
- **A single call site needs a one-off adapter and nothing more.** If exactly
  one place in the codebase needs the two classes to look alike, and no
  second place is expected to need it, a small local adapter at that call
  site is proportionate and a repository-wide interface unification is
  speculative generality applied to a design problem instead of to a class
  hierarchy, but the underlying speculative-generality reasoning is the same
  one that governs Factory Method's non-applicability, see the Factory Method
  entry, dimension 4.

## 5. Structure

Two structures matter here. The smell as it exists before treatment, and the
shape it is refactored into. Neither is a fixed set of named GoF-style roles,
because a code smell is a diagnosis, not a construction pattern, but each has
recognisable participants.

Before treatment.

- **DivergentClassA** and **DivergentClassB.** Two classes that implement the
  same underlying responsibility. Each has its own public method that does
  the work, under its own name, with its own parameter list.
- **Ad hoc caller.** Code that needs both classes and currently either
  branches on the concrete type to call the right method by name, or contains
  a small, usually untested, adapter function written to bridge the two at
  that single call site.

After treatment.

- **SharedContract.** The interface, abstract class, or in a
  structurally-typed language the implicit protocol, that both classes are
  changed to satisfy. It carries the method name and shape the domain
  actually needs, chosen deliberately rather than inherited by accident from
  whichever class happened to be written first.
- **DivergentClassA** and **DivergentClassB**, now conforming to
  SharedContract, either because their own methods were renamed directly, or
  because a thin, named, tested adapter was introduced to make one conform
  without touching its original public method, when that method already has
  external callers that cannot be changed at the same time.
- **Unified caller.** Code that now depends only on SharedContract and no
  longer branches on which concrete class it is holding.

## 6. ASCII structure diagram

```
BEFORE

+-----------------+
| DivergentClassA |
| doThingOldWay() |
+-----------------+

+-----------------+
| DivergentClassB |
| performTheJob() |
+-----------------+

+-------------------------+
| AdHocCaller             |
| if a: a.doThingOldWay() |
| if b: b.performTheJob() |
+-------------------------+

The left side has one branch per concrete class at
every call site.


AFTER

+----------------------------+
| SharedContract (interface) |
| doThing()                  |
+----------------------------+
           ^
           | implements
     +-----+-----+
     |           |
+--------------------+ +--------------------+
| DivergentClassA    | | DivergentClassB    |
| doThing()          | | doThing()          |
+--------------------+ +--------------------+
     ^           ^
     +-----+-----+
           |
+------------------+
| UnifiedCaller    |
| for x in things: |
|   x.doThing()    |
+------------------+

The right side has one shared name, resolved by
dispatch, not by branch.
```

## 7. Dynamics

The runtime story of the smell is a comparison, so the diagram below shows the
before and after call sequences for the same task, holding both a
DivergentClassA instance and a DivergentClassB instance and needing to invoke
the equivalent operation on each.

```
BEFORE (branch on concrete type at the call site)

  Caller                     a: DivergentClassA      b: DivergentClassB
    |                                |                        |
    |-- if isinstanceof(a, A) ------>|                        |
    |-- a.doThingOldWay() ---------->|                        |
    |<-- result ---------------------|                        |
    |                                                          |
    |-- if isinstanceof(b, B) -------------------------------->|
    |-- b.performTheJob() --------------------------------------->|
    |<-- result --------------------------------------------------|
    |
    (adding a third class means adding a third branch here,
     by hand, at every caller that does this)

AFTER (single call through the shared contract)

  Caller                thing: SharedContract
    |                          |
    |-- for thing in [a, b] -->|
    |-- thing.doThing() ------>|
    |     (dispatch resolves to the correct override
    |      of DivergentClassA or DivergentClassB
    |      without the caller naming either one)
    |<-- result ---------------|
    |
    (adding a third class means adding it to the collection;
     no caller code changes)
```

The important timing property is that the "before" sequence pays its cost at
every call site, every time a new alternative class is added, while the
"after" sequence pays that cost exactly once, at the point where the new class
is written to satisfy SharedContract.

## 8. Implementation variants

**Direct rename.** When neither method has external callers outside the code
you control, rename one or both methods so their names and signatures match,
and, if the language supports it, extract a shared interface or abstract base
so the compiler enforces the match going forward. This is the cheapest fix and
should be preferred whenever it is available. sammancoaching.org's summary of
the smell states the fix in exactly these terms. "unify the interfaces so the
protocols match" (sammancoaching.org, verified 2026-08-03).

**Extract Superclass or Extract Interface, then push the shared method down.**
When the two classes have enough behaviour in common beyond the one divergent
method, pulling a shared abstract base upward, with the unified method
declared there, documents the relationship explicitly rather than leaving it
implicit in two independently conforming classes. refactoring-assistant.github.io
names Extract Superclass alongside Rename Method as the two techniques it
recommends for this smell (refactoring-assistant.github.io, verified
2026-08-03).

**Adapter at the boundary.** When one of the two implementations is owned by
a third party, or when renaming a method would break external callers you
cannot update, wrap the divergent class in a small adapter that implements
SharedContract and forwards to the original method under its original name.
This variant keeps the original class untouched and is the correct response
whenever the non-applicability case about vendored code, dimension 4, applies.
The cost is a permanent extra layer of indirection that a direct rename would
not need.

**Parameter-object unification.** When the divergence is not only in the
method name but in the parameter list, for example one class takes three
positional arguments and the other takes a single configuration object,
introducing a shared parameter type (an Introduce Parameter Object
refactoring) alongside the rename resolves both mismatches together rather
than leaving a partially unified interface that still forces callers to
assemble arguments differently per class.

**Structural typing, no interface declaration needed.** In a language with
structural or duck typing, such as TypeScript, Go, or Python when using
`typing.Protocol`, unifying two classes' method names and shapes is
sufficient on its own. no explicit `implements` clause or common ancestor is
required for a caller written against the shared shape to accept both. This
removes one whole step compared with the classical, nominally-typed fix, and
it means the smell can be less visible in these languages at design time,
because the type checker does not force a shared name the way an `implements`
clause would, so nothing stops two classes from silently drifting back out of
alignment later. See the language note in the code examples for how this
changes the fix in TypeScript versus Java.

**Delete one class outright.** When the investigation into the smell reveals
that the two classes are not merely alternative interfaces to the same idea
but are, in substance, full duplicates that arose because one team did not
know the other's class existed, the correct outcome is not to unify their
interfaces but to delete one of them and repoint its callers at the survivor.
refactoring-assistant.github.io's first worked example for this smell is
exactly this outcome (refactoring-assistant.github.io, verified 2026-08-03).
This is the only variant that removes a class rather than adding an
abstraction, and it is worth checking for before reaching for any of the
others, because it is strictly cheaper when it applies.

## 9. Known production uses

Because this is a diagnosis applied to code rather than a construction
pattern deliberately chosen by a library author, "production use" here means a
documented, real instance of the mismatch existing in a widely used API,
rather than a library that advertises the pattern by name. Three verified
instances follow.

**`java.util.Enumeration` versus `java.util.Iterator` in the Java Collections
Framework.** Both interfaces exist to walk through a collection one element at
a time, but `Enumeration` exposes `hasMoreElements()` and `nextElement()`
while `Iterator` exposes `hasNext()` and `next()`, along with an added
`remove()` capability that `Enumeration` never had. The official Java SE 21
API documentation for `Iterator` states this plainly. it says that Iterator
"takes the place of Enumeration in the Java Collections Framework", and that
iterators differ from enumerations in two ways, they allow the caller to
remove elements from the underlying collection during iteration with
well-defined semantics, and their method names have been improved (Oracle,
*Java SE 21 API Specification*, `java.util.Iterator`,
https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Iterator.html
verified 2026-08-03). The documentation is explicit that the two interfaces
were never unified. `Enumeration` remains in the standard library for
backward compatibility, and a class that only implements `Enumeration` cannot
be handed to code written against `Iterator`, or to a `for`-each loop, without
an adapter.

**`java.io.File` versus `java.nio.file.Path` for representing a filesystem
path.** The two APIs represent the same concept, a location on a filesystem,
but expose that concept through entirely different method sets, deleting a
file is `File.delete()` on one side and `Files.delete(Path)` on the other,
renaming is `File.renameTo()` versus `Files.move(Path, Path)`, and listing
directory contents is `File.list()` versus `Path.newDirectoryStream()`. The
official Oracle Java tutorial for migrating legacy I/O code states, "Because
the Java implementation of file I/O has been completely re-architected in the
Java SE 7 release, you cannot swap one method for another method... There is
no one-to-one correspondence between the two APIs, but the following table
gives you a general idea of what functionality in the `java.io.File` API maps
to in the `java.nio.file` API" (Oracle, *Legacy File I/O Code*,
https://docs.oracle.com/javase/tutorial/essential/io/legacy.html verified
2026-08-03). The same tutorial documents the interoperability bridge the
platform itself had to add because of the mismatch, `File.toPath()` and
`Path.toFile()`, which is the Adapter variant from dimension 8 applied at the
scale of an entire standard library, not merely a single call site.

**`pathlib.Path` versus the `os.path` module in the Python standard library.**
Both offer path manipulation, but one is method-based and object-oriented
while the other is function-based and procedural, so `os.path.dirname(p)`
becomes `PurePath(p).parent`, `os.path.basename(p)` becomes `PurePath(p).name`,
and `os.path.exists(p)` becomes `Path(p).exists()`. The official Python 3
documentation for `pathlib` states the distinction directly. "pathlib
implements path operations using `PurePath` and `Path` objects, and so it's
said to be object-oriented. On the other hand, the `os` and `os.path` modules
supply functions that work with low-level `str` and `bytes` objects, which is
a more procedural approach." and provides a full correspondence table mapping
`os.path` functions to their `pathlib` equivalents, while also noting that
"pathlib is not a drop-in replacement" because of behavioural differences
around normalisation and symlinks (Python Software Foundation, *pathlib.
Object-oriented filesystem paths*,
https://docs.python.org/3/library/pathlib.html verified 2026-08-03). This is
a case where the standard library itself both documents the divergence and
declines to fully unify it, because the two APIs differ not only in name but
in the semantic edge cases described in dimension 4's discussion of
error-handling mismatches.

## 10. Consequences

Positive, once the fix from dimension 8 is applied.

- Callers write one loop, one interface, and one set of tests against the
  shared contract instead of one branch per concrete class.
- Adding a third implementation is a closed-world change, a new class
  satisfying the existing contract, rather than an open-world change that also
  edits every caller.
- The renamed methods carry vocabulary the domain actually chose, rather than
  vocabulary inherited from whichever class happened to be written first, and
  a reader learns the domain's real verb once rather than learning two
  synonyms.
- Test doubles and fakes for the shared contract now work against both real
  implementations, because both satisfy the same shape.

Negative.

- The rename itself is a breaking change for any caller outside your control,
  which is why the adapter variant exists and why a public API cannot always
  take the direct-rename path.
- A hastily unified interface that papers over a genuine semantic difference,
  see the error-handling case in dimension 4, produces a false sense of
  substitutability that surfaces later as a subtle production bug rather than
  as a compile error.
- Extracting a shared interface adds one more named type to the codebase, and
  in a language without structural typing it also adds an `implements` clause
  to maintain on every future implementer.
- The fix cannot be verified mechanically by a compiler alone. two methods can
  share a name and a signature and still disagree about idempotency, thread
  safety, or ordering, and only a behavioural test, see dimension 15, catches
  that.

## 11. Failure modes and misuse

**The false-friend rename.** Symptom. Two classes now share a method name and
compile against a shared interface, but a bug appears in production only when
one class is substituted for the other at a call site that assumed a
particular behaviour, such as whether the method blocks. Cause. The rename
matched the syntax without matching the semantics, treating a coincidental
name overlap as sufficient evidence the two were interchangeable. Fix. Write
the contract test from dimension 15 before declaring the unification
finished, so a semantic mismatch fails a test rather than surfacing in
production.

**Interface unification applied to genuinely different concepts.** Symptom.
A shared interface accumulates optional parameters, nullable return types, or
a growing set of methods that only one implementer actually uses meaningfully,
while the other implementer either throws `UnsupportedOperationException` or
silently no-ops. Cause. The smell was diagnosed on two classes that only
looked similar rather than two classes that were the same concept under
different names, which is exactly the non-applicability case in dimension 4.
Fix. Split the interface back into what each implementer genuinely supports,
following the Interface Segregation Principle, rather than forcing a single
bloated contract to cover both.

**Repeated adapter proliferation.** Symptom. Three or four small,
undocumented adapter classes or functions accumulate across the codebase,
each independently reconciling the same two divergent classes for a different
call site, none of them sharing code with the others. Cause. The
non-applicability guidance about a single call site, dimension 4, was applied
correctly the first time, but nobody revisited the decision once a second and
third call site needed the same bridge. Fix. Once a second adapter for the
same pair of classes appears, that is the signal to promote the ad hoc
adapters into the shared-interface fix from dimension 8, because the
"one-off" assumption no longer holds.

**Renaming only one side.** Symptom. `DivergentClassA` is renamed to match
`DivergentClassB`'s method name, the change compiles, and the team declares
the smell fixed, but a caller still branches on concrete type because it also
needs a third, unrenamed method that only `DivergentClassA` exposes under its
own old name. Cause. Only the one obviously duplicated method was unified,
while the rest of each class's surface was left untouched, so callers that
need the full behaviour of either class still cannot treat them
interchangeably. Fix. Audit every method a caller actually needs from both
classes before declaring the unification complete, not only the one method
that prompted the investigation.

**Fixing the smell by widening the wrong side.** Symptom. To make two
classes' return types match, a team changes the narrower return type, for
example a class that reliably returns a non-null `Report`, to match the
wider, more permissive type of the other, for example a class that returns
`Report | null`, instead of the other way around. Every caller of the
originally reliable class now has to handle a null case that could never
actually occur for that class. Cause. Interface unification chose to match
whichever signature happened to compile first rather than choosing the
signature that best represents the domain. Fix. Choose the unified signature
deliberately, generally the stricter, more informative one, and adapt the
looser implementation up to it rather than degrading the stricter one down.

## 12. Trade-off matrix

Compared against named alternative responses to the same underlying
situation, two or more classes doing conceptually the same job.

| Force | Unify interfaces (this fix) | Leave as-is, branch at call sites | Local adapter per call site | Delete one class, keep the other | Extract Interface only, no rename |
|---|---|---|---|---|---|
| Cost to fix now | Medium, one rename plus test | None | Low, one small wrapper | Medium to high, migrate every caller of the deleted class | Low, no method names change |
| Cost paid by future callers | Low, one shared name to learn | High, grows with every new caller and every new class | Medium, grows with every new adapter, see failure mode above | None, only one class remains | Medium, callers still see two names through the interface's differing method signatures per implementer |
| Risk of hiding a real semantic difference | Present if the rename is rushed, see dimension 11 | Absent, the difference stays fully visible | Absent, the adapter's own code is where the difference is handled explicitly | Absent, only genuine duplicates should be deleted | Absent, no behaviour changes |
| Effect on public API stability | Breaking, unless paired with an adapter for old callers | None | None, the original classes are untouched | Breaking for callers of the deleted class | None |
| Scales to a third implementation | Well, new implementer just satisfies the contract | Poorly, every caller needs a new branch | Poorly, needs a new adapter per call site per new class | Not applicable, there is only one class left | Poorly, the interface exists but methods still diverge in name |
| Appropriate when | Genuine, recurring substitutability need across two or more call sites | The two classes will never be used interchangeably | Exactly one call site needs interchangeability and no more are expected | The two classes are full duplicates, not merely similar | Never, on its own; it documents the mismatch without fixing it |

Reading of the table. Unifying the interfaces wins whenever more than one
caller genuinely needs substitutability now or soon. A local adapter wins for
a single, unlikely-to-repeat call site. Deleting one class wins whenever the
underlying investigation shows the two were duplicates rather than
alternatives. Extract Interface without a rename is included only to show
that it does not, by itself, resolve the smell.

## 13. Related and incompatible patterns

- **Adapter.** The mechanism most often used to fix this smell without
  touching either original class, described in dimension 8. Adapter is the
  right tool exactly when one of the two divergent classes cannot be edited,
  which the Factory Method entry's dimension 4 also flags as the boundary
  case for when to introduce an abstraction rather than edit existing code.
- **Strategy.** Once the two classes are unified behind a shared interface,
  the result is frequently consumed as a Strategy. a caller holds a reference
  to the shared interface and is configured with one concrete implementation
  or the other. The smell's fix is therefore often the step that makes a
  Strategy usage possible where before only a hardcoded branch existed.
- **Template Method.** When the two divergent classes share most of their
  algorithm and differ only in the one method that prompted the diagnosis,
  the unified method is frequently the exact hook a Template Method exposes,
  and the fix from dimension 8 and the structure of Template Method converge
  on the same shape. See the Template Method entry for the base-class
  sequencing this composes with.
- **Factory Method.** A related but distinct concern. Factory Method decides
  which concrete product a creator returns, given that all products already
  share one interface. This smell is upstream of that. it is the diagnosis
  that the products do not yet share an interface at all. A codebase that
  wants to introduce Factory Method over two divergent classes must fix this
  smell first, or the factory method's return type has nothing honest to
  declare.
- **Extract Superclass / Extract Interface (refactoring family).** The
  mechanical technique dimension 8 relies on for the direct-rename and
  push-down variants. Cross reference the refactoring family entry for the
  step-by-step mechanics of extracting a shared type safely.
- **Duplicated Code (smell family).** A sibling smell, not identical to this
  one. Duplicated Code is about repeated logic; this smell is about
  equivalent logic hidden behind different names. The two frequently appear
  together, because the code inside two alternative classes' equivalent
  methods is often itself duplicated once the naming mismatch is accounted
  for, and fixing this smell often exposes a Duplicated Code smell
  underneath it that a separate Extract Method or Pull Up Method pass then
  addresses.
- **Speculative Generality (smell family).** The active incompatibility.
  where this smell recommends adding an abstraction because two real,
  present-day classes need it, Speculative Generality is the failure of
  adding that same abstraction for a hypothetical third class that does not
  yet exist. The non-applicability guidance in dimension 4 about a single
  call site is this smell's boundary against drifting into Speculative
  Generality.
- **Interface Segregation Principle.** Governs how wide the unified interface
  from dimension 8 should be. Fixing this smell by writing an interface that
  is broader than what both classes genuinely, meaningfully implement
  recreates the "false-friend" and "wrong widening" failure modes in
  dimension 11, which the Interface Segregation Principle exists to prevent.

## 14. Refactoring path in and out

Introducing the fix into code that currently exhibits the smell.

1. Confirm the two classes are genuinely alternatives for the same
   responsibility, not merely similarly named or superficially similar. Read
   both implementations in full, not only the one method a caller happens to
   need right now, and check the non-applicability cases in dimension 4
   before proceeding.
2. List every method a real or anticipated caller needs from either class,
   not only the one that triggered the investigation. A unification that
   covers one method and misses three others reproduces the failure mode in
   dimension 11.
3. For each divergent pair of methods, decide the semantics first. Do the two
   methods actually behave the same way on the same inputs, including on
   errors, on empty input, and on concurrent access. If they do not, resolve
   that difference, or decide to expose it explicitly in the unified
   contract, for example as a documented exception the caller must handle,
   before renaming anything.
4. Choose the unified method name and signature deliberately. Prefer the
   stricter, more informative of the two existing signatures, per dimension
   11's "wrong widening" failure mode, rather than defaulting to whichever
   signature happens to already compile against both bodies.
5. If both classes are under your control and neither has external callers
   you cannot change in the same commit, rename directly. Run the existing
   test suite for each class after each individual rename, not only once at
   the end, so a broken call site is caught at the smallest possible diff.
6. If either class has external callers you cannot change, introduce an
   adapter implementing the unified contract and forwarding to the original,
   unrenamed method, and update only the callers that need
   substitutability to depend on the adapter.
7. If the two classes share enough structure beyond the one method, extract a
   common abstract base or interface and move the shared contract there, so
   the compiler, or in a structurally typed language the type checker,
   enforces the match for every future implementer.
8. Write the contract test described in dimension 15 before considering the
   refactor complete. it is this test, not the compiler, that catches the
   false-friend rename from dimension 11.
9. Update the caller identified in step 1 to depend on the unified contract
   and delete any branch or ad hoc adapter that previously handled the two
   classes separately.

Removing the fix, on the rare occasion the unification turns out to have been
premature, follows the same guidance as reversing Extract Interface generally.

1. Confirm no second caller has since come to depend on the shared contract;
   if one has, the unification is earning its place and should not be
   reversed.
2. Inline the shared interface's single remaining method back into each
   concrete class under whatever name best fits that class alone.
3. Remove the `implements` or `extends` relationship, or in a structurally
   typed language simply stop treating the two as interchangeable at the one
   remaining call site.
4. Delete the now-unused shared type.

## 15. Testing and verification

Easier because of the fix.

- Once both classes satisfy one contract, a single parameterised test suite,
  run once per concrete implementation, replaces two separate,
  independently-maintained test files that previously tested equivalent
  behaviour under different method names with no shared assertions between
  them.
- A caller that only depends on the shared contract can be tested with a
  lightweight fake or stub implementing that contract, without needing to
  construct either real class, which is the normal testability benefit of
  programming to an interface.

Harder because of the fix, and the reason dimension 11's false-friend failure
mode matters.

- The unified interface says nothing, by itself, about whether the two
  implementations actually agree on edge-case behaviour. a shared method
  signature is necessary but not sufficient evidence of substitutability.
- If the unification was done via an adapter rather than a direct rename, the
  adapter itself is new code with its own bugs to test, most commonly around
  whether it correctly translates the original method's exceptions or edge
  cases into the unified contract's expected behaviour.

Techniques that apply.

- **Contract test, run against every implementation.** Write one abstract
  test case against the shared interface with a hook that supplies the
  concrete instance under test, then run it once per implementation. This is
  the single most direct way to prove the unification was not only
  syntactic. it exercises the same assertions against `DivergentClassA` and
  `DivergentClassB` and fails if either one disagrees with the contract on a
  behaviour the test checks. The same technique is recommended for verifying
  Factory Method's product contract, see the Factory Method entry, dimension
  15, and applies here for the identical reason. a shared type signature does
  not, on its own, prove shared behaviour.
- **Characterisation test before the rename.** Before renaming either
  method, write a test that pins down the current, observed behaviour of
  each class exactly as it stands, including any surprising edge case. Run
  this test again after the rename to prove the rename changed only the name,
  not the behaviour.
- **Differential test between the two implementations.** Where both classes
  can be run against the same set of representative inputs, write a test
  that runs both, through the unified interface, and asserts their outputs
  agree, or asserts and documents the specific inputs where they are allowed
  to differ. This surfaces the semantic mismatches the rename alone cannot
  catch, described in the pathlib versus os.path production example in
  dimension 9, where the documentation itself warns that the two are not a
  drop-in replacement for each other on symlinks and normalisation.
- **Mutation or fault-injection review of the adapter.** When the fix used an
  adapter, review or test what the adapter does when the wrapped method
  throws, returns an unexpected value, or is called with an edge-case input,
  since the adapter is exactly the place a translation bug hides.

## 16. Observability signals

The smell itself is a static, design-time property and does not, in its
unfixed state, produce a distinct runtime signal separate from whatever bugs
its ad hoc call-site branches or hand-written adapters happen to carry. The
signals below are about the fix, once applied, and about detecting the smell
recurring after a fix.

What to record.

- A log line or metric at the point where the unified contract is invoked,
  labelled by the concrete implementation actually used, the same
  per-implementation labelling pattern recommended for Factory Method,
  Factory Method entry dimension 16. On a dashboard, this answers the
  question "are both alternatives still genuinely both in use", which
  matters because a smell that was fixed to support two implementations, but
  where one implementation's usage has since dropped to zero, is a candidate
  for the "delete one class" variant in dimension 8 rather than continued
  maintenance of a now-unnecessary abstraction.
- If the fix used an adapter, a counter of translation failures inside the
  adapter, distinct from failures in the wrapped class itself, so an
  operator can tell whether an incident originated in the adapter's own
  translation logic or in the underlying implementation it wraps.
- A static, build-time signal rather than a runtime one is arguably more
  valuable for this specific smell than any runtime metric. a linter or code
  review checklist item that flags two classes in the same module whose
  method names are near-duplicates of each other, string-distance close but
  not identical, which is the earliest, cheapest point to catch the smell
  recurring, well before it reaches production telemetry.

A healthy state. The per-implementation usage counter shows both
implementations in active, expected use consistent with their known callers,
and no adapter translation-failure counter is climbing. A codebase-wide code
search for the unified method name returns exactly the expected concrete
implementations and no stray, differently-named method that duplicates the
same responsibility outside the shared contract.

An unhealthy state. A new class appears in a code review implementing a
responsibility that a shared contract already covers, but under a new,
unrelated method name, which is the smell recurring rather than a genuinely
new concept; this is the single most common way the fix regresses over time,
because nothing at runtime prevents a third class from being added outside
the contract the way a compiler prevents an interface method from being
misspelled. Alternatively, one implementation's usage counter flatlines to
zero while its code remains, which signals the abstraction has outlived its
second user and is a candidate for the delete-one-class variant.

## 17. Security and privacy implications

This entry is largely judgement rather than a sourced claim, because
security and privacy implications of an interface-naming smell are analytical
rather than documented in the primary sources for this entry.

The smell itself, an accidental naming mismatch between two classes, carries
no direct security implication. The implications that do exist appear at the
fix, not at the smell.

**An adapter is a place a security check can be silently dropped.** When the
fix wraps a divergent class in an adapter rather than renaming it directly,
the adapter is new code sitting between the caller and the original
implementation. If the original method performed input validation,
authorization checks, or output encoding as part of its own body, and the
adapter's translation logic calls a different entry point on the wrapped
class that bypasses that check, for example calling an internal, unchecked
overload because it has a more convenient signature to adapt from, the
unification can silently remove a security control that existed in one of
the two original classes. This is worth an explicit line item in the review
of any adapter written to fix this smell. does the adapter call the exact
same code path the original public method called, or a shortcut around it.

**Unifying error-handling behaviour can leak information across a trust
boundary.** dimension 4 already flags that a `null`-returning method and an
exception-throwing method must not be renamed to share an interface without
resolving the difference first. The security-relevant version of that same
warning is this. if one of the two original methods deliberately returned a
generic error to avoid revealing internal state to an untrusted caller, and
the unification adopts the other method's more detailed exception message as
the new shared contract's error behaviour, the fix can widen what an
untrusted caller learns on failure. Choosing the unified error behaviour,
per dimension 14, step 4, should weigh this alongside strictness.

**No general privacy implication is asserted here beyond what any renamed
method inherits from its own data handling**, which this entry does not have
grounds to generalise about, since the smell is name-and-shape level and says
nothing about what data either method actually touches.

## Code examples

Four languages, chosen to show the fix under three different type
disciplines. Nominal typing with an explicit interface declaration (Java),
structural typing with no declaration required (TypeScript, and a brief Go
note), and a dynamically typed language where a `Protocol` or duck typing
substitutes for a nominal interface (Python). C# and Kotlin are omitted
because their toolchains were not verified as installed in this environment
at the time of writing, per the available-toolchains table, and this entry
states that plainly rather than presenting untested code as compiled. Rust is
omitted for the same reason a Go-style structural example already covers the
trait-based, non-inheritance angle without duplicating it, and because Rust's
own idiomatic answer, an ordinary trait implemented by both types, is
structurally identical to the Go example below with syntax substituted, so it
would not demonstrate anything the Go note does not already show.

### Java (nominal typing, explicit interface required)

Before, the smell as written.

```java
final class LocalReportSaver {
    void saveReport(String data) {
        System.out.println("local:" + data);
    }
}

final class RemoteReportUploader {
    void upload(String payload) {
        System.out.println("remote:" + payload);
    }
}
```

A caller holding both is forced to branch by concrete type, because neither
class shares a method name with the other.

```java
final class BadCaller {
    void saveBoth(LocalReportSaver local, RemoteReportUploader remote, String data) {
        local.saveReport(data);
        remote.upload(data);
    }
}
```

After, the fix. a shared interface is extracted, and `RemoteReportUploader`,
which is assumed here to have an external caller depending on its original
`upload` method name, is adapted rather than renamed directly, per dimension
8's adapter variant.

```java
interface ReportWriter {
    void write(String content);
}

final class LocalReportSaver implements ReportWriter {
    public void write(String content) {
        System.out.println("local:" + content);
    }
}

final class RemoteReportUploader {
    // Kept for existing external callers of upload(); not renamed directly.
    void upload(String payload) {
        System.out.println("remote:" + payload);
    }
}

final class RemoteReportUploaderAdapter implements ReportWriter {
    private final RemoteReportUploader delegate;

    RemoteReportUploaderAdapter(RemoteReportUploader delegate) {
        this.delegate = delegate;
    }

    public void write(String content) {
        delegate.upload(content);
    }
}

public final class Demo {
    public static void main(String[] args) {
        java.util.List<ReportWriter> writers = java.util.List.of(
            new LocalReportSaver(),
            new RemoteReportUploaderAdapter(new RemoteReportUploader())
        );
        for (ReportWriter w : writers) {
            w.write("quarterly numbers");
        }
    }
}
```

The caller no longer names either concrete class and no longer branches.
Adding a third `ReportWriter` requires no edit to `Demo.main`.

### TypeScript (structural typing, no declaration required)

```typescript
// Before: two classes, same job, different shape.
class LocalReportSaverV0 {
  saveReport(data: string): void {
    console.log("local:" + data);
  }
}

class RemoteReportUploaderV0 {
  upload(payload: string): void {
    console.log("remote:" + payload);
  }
}

// After: unify by giving both the same method name and signature.
// No `implements` clause is required. TypeScript's structural typing
// accepts any object with a matching write(content: string): void shape.
interface ReportWriter {
  write(content: string): void;
}

class LocalReportSaver {
  write(content: string): void {
    console.log("local:" + content);
  }
}

class RemoteReportUploader {
  write(content: string): void {
    console.log("remote:" + content);
  }
}

function saveAll(writers: ReportWriter[], content: string): void {
  for (const w of writers) {
    w.write(content);
  }
}

saveAll([new LocalReportSaver(), new RemoteReportUploader()], "quarterly numbers");
```

The language note from dimension 8 applies directly here. nothing in
TypeScript prevents a third class from being added later with a differently
named method that still, coincidentally, type-checks against unrelated call
sites. structural typing removes the ceremony of declaring conformance, but
it does not remove the discipline of choosing one shared name and sticking to
it, which is exactly the recurrence risk described in dimension 16.

### Python (dynamic typing, `Protocol` for an explicit but non-enforced contract)

```python
from typing import Protocol


# Before: two classes, same job, different method name and different
# return type, which is the harder version of the smell described in
# dimension 11's "wrong widening" failure mode.
class LocalReportSaverV0:
    def save_report(self, data: str) -> None:
        print("local:" + data)


class RemoteReportUploaderV0:
    def upload(self, payload: str) -> str:
        print("remote:" + payload)
        return "ack"


# After: unify the name and the return type. Protocol documents the shared
# shape without forcing either class to declare inheritance from it.
class ReportWriter(Protocol):
    def write(self, content: str) -> None: ...


class LocalReportSaver:
    def write(self, content: str) -> None:
        print("local:" + content)


class RemoteReportUploader:
    def write(self, content: str) -> None:
        print("remote:" + content)


def save_all(writers: list[ReportWriter], content: str) -> None:
    for w in writers:
        w.write(content)


if __name__ == "__main__":
    save_all([LocalReportSaver(), RemoteReportUploader()], "quarterly numbers")
```

Note that `RemoteReportUploaderV0.upload` returned an acknowledgement string
while `LocalReportSaverV0.save_report` returned nothing. The unified version
above resolves that mismatch by discarding the acknowledgement return value
entirely, which is a real design decision, not a mechanical rename, exactly
the point dimension 14, step 4, makes. choose the unified signature
deliberately rather than by whichever one happens to compile.

### Go, a brief structural note (not a full example, per the available-toolchains guidance to state omissions plainly)

Go has no classes and no inheritance, so the classical "extract an interface
and declare `implements`" step does not exist at all. Two types with
differently named methods are unified purely by giving both a method with the
identical name and signature; the moment they do, any interface value with
that one-method shape accepts both, with zero additional declaration.

```go
type ReportWriter interface {
	Write(content string)
}

type LocalReportSaver struct{}

func (LocalReportSaver) Write(content string) {
	println("local:" + content)
}

type RemoteReportUploader struct{}

func (RemoteReportUploader) Write(content string) {
	println("remote:" + content)
}

func saveAll(writers []ReportWriter, content string) {
	for _, w := range writers {
		w.Write(content)
	}
}
```

This is included as a short note rather than a full before-and-after example
because it would otherwise duplicate the TypeScript example's structural
point without adding a new idea, per the entry's stated reason for omitting a
full Rust example above.

## 18. References

1. Martin Fowler. *Refactoring. Improving the Design of Existing Code*, 2nd
   edition. Addison-Wesley, 2018. ISBN 978-0134757599. Chapter 3, "Bad Smells
   in Code" (credited in the book's front matter to Kent Beck), section
   "Alternative Classes with Different Interfaces". Primary source for the
   smell's name and origin. Not independently page-verified for this entry;
   the chapter and section are confirmed via the two independent secondary
   summaries listed as items 2 and 3 below, both of which name this exact
   book and edition as their source.
2. sammancoaching.org. "Alternative Classes with Different Interfaces".
   https://sammancoaching.org/code_smells/alternative_classes_different_interfaces.html
   Verified 2026-08-03. Source for the definition quoted in dimensions 1 and
   8, and for confirming the 2nd edition attribution.
3. codesmells.org. "Alternative Classes with Different Interfaces".
   https://www.codesmells.org/smells/alternative-classes-with-different-interfaces
   Verified 2026-08-03. Source for the Snowman and Zombie illustrative
   example referenced in dimension 1, and for the 1999 first-edition
   attribution and ISBN.
4. refactoring-assistant.github.io. "Alternative Classes With Different
   Interfaces".
   https://refactoring-assistant.github.io/object-oriented-abusers/alternative-classes-with-different-interfaces
   Verified 2026-08-03. Source for the "Object-Oriented Abusers" category
   label used by this and other derivative catalogs, and for the named
   Rename Method, Extract Superclass, and delete-the-duplicate fix
   techniques referenced in dimensions 1 and 8.
5. Oracle. *Java SE 21 API Specification*, `java.util.Iterator`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Iterator.html
   Verified 2026-08-03. Source for the Enumeration versus Iterator
   production use in dimension 9.
6. Oracle. *The Java Tutorials*, "Legacy File I/O Code".
   https://docs.oracle.com/javase/tutorial/essential/io/legacy.html
   Verified 2026-08-03. Source for the `java.io.File` versus
   `java.nio.file.Path` production use in dimension 9.
7. Python Software Foundation. *Python 3 documentation*, `pathlib`.
   Object-oriented filesystem paths.
   https://docs.python.org/3/library/pathlib.html
   Verified 2026-08-03. Source for the `pathlib.Path` versus `os.path`
   production use in dimension 9, including the explicit non-drop-in-
   replacement caveat referenced in dimensions 11 and 15.
8. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides. *Design
   Patterns. Elements of Reusable Object-Oriented Software*. Addison-Wesley,
   1994. ISBN 0-201-63361-2. Cited only for the Factory Method
   cross-references in dimensions 4, 13, and 15, not for any claim about this
   entry's own smell.
