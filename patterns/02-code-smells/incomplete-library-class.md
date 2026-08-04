---
name: Incomplete Library Class
slug: incomplete-library-class
family: 02-code-smells
category: Coupling
aliases: [Foreign Class Needs Extra Method, Insufficient Library Class]
first_described: "Fowler and Beck 1999"
maturity: canonical
related: [adapter, decorator, feature-envy, data-class, alternative-classes-with-different-interfaces]
incompatible_with: []
verified: 2026-08-02
---

# Incomplete Library Class

## 1. Name, aliases, and lineage

The canonical name is Incomplete Library Class. It appears in Martin Fowler,
*Refactoring. Improving the Design of Existing Code*, Addison-Wesley, 1st
edition, 1999, in the chapter "Bad Smells in Code", the same chapter that
introduced Feature Envy, Data Class, and the rest of the original catalog.
Kent Beck is credited as co-author of that smell catalog, a fact Fowler states
directly on his own site rather than in the book's byline alone. "The term was
first coined by Kent Beck while helping me with my Refactoring book"
(https://martinfowler.com/bliki/CodeSmell.html, verified 2026-08-02). The same
attribution point applies here as it does to every smell in the first
edition's catalog, so this entry repeats it rather than assuming the reader
has seen it elsewhere.

The secondary literature groups Incomplete Library Class with Feature Envy,
Inappropriate Intimacy, Message Chains, and Middle Man under a "Couplers"
category, meaning smells that either create excess coupling between classes
or represent coupling disguised as delegation
(https://sourcemaking.com/refactoring/smells, verified 2026-08-02, and see
https://sourcemaking.com/refactoring/smells/incomplete-library-class for the
smell's own page, verified 2026-08-02). That page states the core observation
plainly. "The only solution to the problem, changing the library, is often
impossible since the library is read-only", and names the cause as "the
author of the library has not provided the features you need or has refused
to implement them" (same source). This entry treats that secondary framing as
a restatement of Fowler's original point, not as an independent source, and
grounds the refactorings themselves in Fowler's own catalog site below.

The pattern's second edition of *Refactoring* (Addison-Wesley, 2018)
reorganizes the book around the refactoring catalog rather than the smell
catalog, and the smell names from the first edition are not reproduced as a
standalone list in that structure. What survives unchanged, and is directly
verifiable, is that both refactorings this smell motivates are still
cataloged on Fowler's own refactoring site under their original names.
Introduce Foreign Method is listed with the definition "a server class you
are using needs an additional method, but you can't modify the class", dated
9 Oct 1999, page 162 (https://refactoring.com/catalog/introduceForeignMethod.html,
verified 2026-08-02). Introduce Local Extension is listed with the parallel
definition for the case of several additional methods, "create a new class
that contains these extra methods. Make this extension class a subclass or a
wrapper of the original", page 164 of the same 1999 dating
(https://refactoring.com/catalog/introduceLocalExtension.html, verified
2026-08-02). Neither catalog page names Incomplete Library Class as its
motivating smell in the text this entry could retrieve, which is worth
recording honestly rather than papering over. the connection between the smell
and these two refactorings is Fowler's own first edition chapter structure,
where each smell in "Bad Smells in Code" names the refactorings that treat it,
and Incomplete Library Class is the entry that names exactly these two.

No serious source disputes the name or proposes a competing term for the same
underlying observation. What varies across languages and communities is not
the name of the smell but the name of the language feature invented
specifically to relieve it, covered in dimension 8.

Incomplete Library Class is a code smell, not a design pattern, so this entry
follows the family 02 convention used elsewhere in this catalog. dimensions 5
through 7 describe the smell's shape as something you recognize in an existing
dependency rather than participants you design from a blank page, and
dimension 8 covers the refactorings and language features that resolve it
rather than construction variants of something you would choose to build.

## 2. Problem and context

A team depends on a class, module, or type that ships from outside the
codebase they control. A standard library type, a third party package, a
generated client, a framework base class, an operating system API wrapper. At
some point the team needs behavior that class does not expose. a convenience
computation derived from data the class already holds, a formatting method, a
predicate, a conversion, something that in an owned class would be a two line
method addition. The class cannot be edited, because it is not owned code, it
may be sealed, final, or marked read only by its packaging, and even where the
raw source is technically reachable on disk, editing a vendored dependency in
place breaks the next upgrade and is excluded by the team's own dependency
management discipline.

Two responses are common and both are worse than treating this as a distinct,
nameable problem. The first is to inline the missing computation at every call
site, so the same derived value or the same predicate gets recomputed, by
hand, in every method that needs it, with no single place that states the
computation once. This is not merely duplication of syntax. it is duplication
of a DECISION about how the foreign class's data should be interpreted, and
when that decision needs to change (a rounding rule, a unit conversion
constant, a definition of what counts as "empty"), every inlined copy has to
be found and updated in step. The second is to reach for inheritance or
wrapping reflexively without settling on where the resulting extension lives
and how many call sites depend on it, producing an ad hoc subclass or wrapper
in whichever file happened to need it first, with a second, slightly
different one appearing later in a different file because nobody knew the
first one existed.

The context in which this becomes a real cost, rather than a one off
annoyance, is repetition and drift. A single call site that needs a foreign
class's missing method once is a minor irritation, best handled inline with a
comment. The smell is worth diagnosing and treating once the same missing
behavior is needed from more than one place, because at that point the
question stops being "how do I get this value here" and becomes "where does
the knowledge of how to compute this value live, and who else needs to know
it." Library upgrades sharpen the same context. a locally patched fork of a
vendored dependency, or a copy paste of the library's source with one method
added, silently diverges from the upstream project and stops receiving
security fixes and bug fixes without the team noticing, because nothing
signals that the copy has drifted. Outside this context, in a genuine one off
script, or a single call site that will never be touched again, the smell is
present in the strict diagnostic sense but not worth a refactoring, because
nothing depends on the missing behavior surviving change.

## 3. Forces

**Ownership versus need.** The team needs behavior the class does not
provide, but does not own the class, so the two forces that would normally
resolve most design questions, "add it where it belongs" and "change the
interface to fit the caller", are both unavailable by construction. Every
option left standing is a workaround for exactly this constraint, and the
whole of dimension 8 is a menu of ways to live with it rather than remove it.

**Upgrade safety versus local convenience.** The most locally convenient
option is often to fork the library, patch its source directly, and vendor
the patched copy. This is judgement, not a sourced claim. it removes the
indirection of a wrapper or a free function and lets call sites read exactly
as if the method had always existed. It also detaches the copy from the
upstream project's own release schedule, so every subsequent security patch,
performance fix, and correctness fix upstream ships has to be manually
diffed in or is simply missed. Teams that choose this path are trading a
one time convenience for an ongoing, invisible maintenance liability that
does not show up until an incident traces back to a known upstream fix that
was never applied locally.

**Encapsulation versus surface area.** A foreign method (a free function
taking the library instance as a parameter) respects the library's public
contract exactly as published, adding nothing to the library's own namespace
or vtable. A local extension (a subclass or wrapper) adds a new type to the
codebase's own namespace, and that new type's public surface has to be
maintained, documented, and kept coherent the same as any other class the
team owns. The forces trade a smaller footprint, one function per missing
method, against a larger but more discoverable footprint, one class that
groups every addition together and reads, at every call site, as if it always
belonged.

**Discoverability versus proliferation.** A single missing method is easy to
find as a lone foreign method, sitting near its one caller or in a small
utilities module. Once several missing methods accumulate across a codebase,
scattered foreign methods become hard to discover, because nothing groups
them, and two different authors independently write the same missing method
twice under two different names. A local extension class solves this by
giving every addition one home, at the cost of every caller now needing to
know the extension type exists and to construct or convert to it rather than
using the library type directly, which is friction the scattered foreign
method version does not have.

**Type identity versus composability.** Subclassing the foreign type (where
the language and the library both permit it, see dimension 4) preserves type
identity, an instance of the extension IS an instance of the library type as
far as the type system is concerned, so it flows unchanged through any
existing code that expects the library type. Wrapping the foreign type
(composition, holding an instance rather than extending it) breaks that
identity, an instance of the wrapper is not interchangeable with the library
type without an explicit unwrap, but it works uniformly whether or not the
library type is final, sealed, or otherwise closed to inheritance, and it
never accidentally exposes a library method the extension did not intend to
support.

## 4. Applicability and non-applicability

Apply the diagnosis and reach for one of the refactorings in dimension 8 when:

- A method the codebase needs from a dependency's type is genuinely absent,
  and the dependency's source is not something the team edits directly as
  part of its normal workflow, whether because it is a published package, a
  standard library type, a generated client, or a vendored copy the team has
  committed to keeping unmodified across upgrades.
- The same missing behavior, or a close variant of it, is needed from more
  than one call site, so a single inline computation would have to be kept in
  step by hand across every place that repeats it.
- The missing behavior is a genuine addition, a new capability, a new
  computed value, a new formatting or conversion rule, rather than a change
  to how an EXISTING method of the class behaves, which is a different
  problem this smell's refactorings do not solve, see the non applicability
  list below.
- The codebase's language or platform offers a first class mechanism for
  attaching new call syntax to a foreign type, such as an extension function,
  an extension method, a category, or a trait implemented for a foreign type,
  and using that mechanism keeps the addition close to normal call syntax
  without vendoring the library.

Do NOT reach for these refactorings, and treat the situation as a different
problem, when:

- The class in question IS owned code, in the same codebase, maintained by
  the same team or an adjacent team the codebase can request a change from.
  Extending code you can change is not Incomplete Library Class, it is simply
  adding a method, and reaching for a foreign method or a local extension
  here hides an addition that should be visible in the owned class itself,
  and creates exactly the discoverability problem this smell exists to name.
- What is actually needed is a change to how an existing library method
  BEHAVES, not an additional method. A foreign method or local extension can
  only add new call surface, it cannot alter what a library method already
  does when called, because it has no access to the library's internals and
  cannot intercept calls the library makes to itself internally. Wanting to
  change existing behavior points toward Decorator (dimension 13), toward
  vendoring and patching with an explicit, tracked fork, or toward filing an
  upstream change and accepting the wait.
- The missing capability is needed from exactly one call site with no
  reasonable expectation of a second, and inlining it once, with a short
  comment explaining why the library does not already provide it, is cheaper
  and clearer than introducing a named abstraction that only one place uses.
- The language or library actively forbids the extension mechanism being
  considered. a final class in Java with no interface to implement against
  cannot be subclassed for a local extension, a sealed class in Kotlin or
  Swift restricts subclassing to the same file or module, and a struct
  passed by value in a language without extension methods (see the C# ref
  extension member caveat in dimension 8) may need the wrapper form even
  where a language generally prefers subclassing. Attempting to force
  subclassing against a language's explicit closure mechanism is not a
  workaround, it is a compile error, and the honest response is to choose
  wrapping or a free function instead.
- The team is tempted to reach for runtime monkey patching (reopening the
  foreign class at runtime and injecting a method directly onto it, available
  in Ruby, Python, and JavaScript among others) as a shortcut past writing an
  extension. This is judgement, not a sourced fact for every case, but the
  risk is well established. a monkey patch changes the behavior of the
  foreign type globally, for every caller in the process, including
  dependencies of dependencies that never asked for the change, and two
  monkey patches from two different libraries loaded into the same process
  can silently overwrite each other with no error raised. Prefer a local
  extension, which is opt in per call site, over a monkey patch, which is
  not, except in the narrow case of a small, well isolated compatibility
  shim with an explicit comment naming exactly why it exists and what
  breaks if it is removed.

## 5. Structure

**Foreign Class.** The type the codebase depends on but does not own, and
cannot edit as part of its normal workflow. Publishes a fixed public surface.
Has no awareness that the codebase wants more from it.

**Client.** The code in the owning codebase that needs a capability the
Foreign Class does not expose. Holds or receives an instance of the Foreign
Class and would, in an ideal world where the codebase owned the Foreign
Class, simply call the missing method directly on it.

**Foreign Method.** A function, owned by the codebase, that takes an instance
of the Foreign Class as its first parameter (or, in languages with dedicated
extension syntax, is declared as extending the Foreign Class) and implements
exactly the one missing capability, using only the Foreign Class's already
published public surface. Lives in a module the codebase owns, conventionally
named for the capability it adds or grouped with sibling foreign methods for
the same Foreign Class.

**Local Extension.** A type, owned by the codebase, that either subclasses the
Foreign Class (where the language and the Foreign Class both permit
subclassing) or wraps an instance of it by composition, and adds several
missing methods at once. Presents a public surface that is the Foreign
Class's original surface plus the codebase's additions, either inherited
automatically (the subclass form) or forwarded explicitly one method at a
time (the wrapper form).

**Factory or Conversion Point.** The place, conventionally a static factory
method or constructor on the Local Extension, where an existing instance of
the Foreign Class, or the Foreign Class's own construction arguments, is
turned into an instance of the Local Extension. Every Client that wants the
extension's added behavior passes through this point once.

## 6. ASCII structure diagram

```
  Foreign Method form
  --------------------
  +-----------+        +------------------------+       +----------------+
  |  Client   |------->|  toFahrenheit(t)       |------>|  Temperature   |
  +-----------+        |  (owned free function) |       |  (foreign,     |
                        +------------------------+       |   unmodified)  |
                                                          +----------------+
                        calls t.celsius() internally,
                        exposes no new type at all


  Local Extension form
  ---------------------
  +-----------+        +---------------------------+
  |  Client   |------->|  RichTemperature          |
  +-----------+        |  (owned, extends or wraps)|
                        |  + toFahrenheit()         |
                        |  + toKelvin()              |
                        |  + describe()               |
                        +---------------------------+
                                  |
                                  | subclasses OR holds an instance of
                                  v
                        +----------------+
                        |  Temperature   |
                        |  (foreign,     |
                        |   unmodified)  |
                        |  + celsius()   |
                        +----------------+
```

## 7. Dynamics

```
  Foreign Method call sequence
  -----------------------------
  Client                 toFahrenheit()          Temperature (foreign)
    |                          |                          |
    |-- toFahrenheit(t) ------>|                          |
    |                          |-- t.celsius() ---------->|
    |                          |<-- 100.0 -----------------|
    |                          | compute 100*9/5+32       |
    |<-- 212.0 ----------------|                          |


  Local Extension conversion and call sequence
  ---------------------------------------------
  Client          RichTemperature.from()   RichTemperature       Temperature (foreign)
    |                     |                       |                       |
    |-- from(t) --------->|                       |                       |
    |                     |-- t.celsius() ------------------------------->|
    |                     |<-- 0.0 ----------------------------------------|
    |                     |-- new RichTemperature(0.0) -->|               |
    |<-- richInstance ----|                       |                       |
    |                                              |                      |
    |-- richInstance.describe() ----------------->|                       |
    |                                              |-- self.celsius() --->|
    |                                              |<-- 0.0 ---------------|
    |                                              | compute derived text |
    |<-- "0.0C (32.0F)" --------------------------|                       |
```

## 8. Implementation variants

**Free function foreign method (any language with functions).** The plainest
form. A function in an owned module takes the Foreign Class instance as its
first argument and returns the missing value. No new type, no subclassing
question, works identically whether the Foreign Class is final, sealed, or a
plain struct. The TypeScript, Python, and Go examples in this entry all use
this shape for the single missing method case.

**Language level extension functions or extension methods.** Kotlin,
Swift, C#, and Dart each provide dedicated syntax that lets a function
declared in owned code be CALLED using the foreign type's method call syntax,
without altering the foreign type at all. Kotlin's own documentation states
the purpose directly. "Kotlin extensions let you extend a class or an
interface with new functionality without using inheritance or design patterns
like Decorator. They are useful when working with third-party libraries you
can't modify directly", and adds the guarantee that "extensions don't modify
the classes or interfaces they extend" (https://kotlinlang.org/docs/extensions.html,
verified 2026-08-02). C#'s own documentation frames the same mechanism the
same way. "Extension members are preferable when the original source isn't
under your control, when a derived object is inappropriate or impossible, or
when the functionality has limited scope"
(https://learn.microsoft.com/en-us/dotnet/csharp/programming-guide/classes-and-structs/extension-methods,
verified 2026-08-02). This is functionally the free function foreign method
with better call site ergonomics, since `t.toFahrenheit()` reads identically
to a real member call. one caveat the C# documentation states directly. when
the receiver type is a value type (`struct`) rather than a reference type,
mutating extension members need an explicit `ref` modifier on the receiver
parameter, or changes are made to a copy and silently lost (same source,
verified 2026-08-02).

**Category or protocol conformance (Objective-C categories, Swift protocol
extensions).** A category attaches new methods directly to an existing class
at the language and runtime level, closer to the Local Extension in effect
than to a free function in ergonomics, because the added method becomes a
real method callable via normal dot syntax on any instance of the original
type, with no wrapper or factory step. Swift's protocol extensions achieve a
related effect by declaring a protocol with a default method implementation
and conforming the foreign type to it, which works even for types the
language would not otherwise allow subclassing.

**Subclass local extension (class based languages that permit
subclassing).** A new class extends the Foreign Class directly, inheriting
its full public surface automatically and adding the missing methods on top.
Preserves type identity, an instance of the extension IS an instance of the
Foreign Class as far as the type system and any code expecting the Foreign
Class are concerned. Unavailable when the Foreign Class is declared final
(Java), sealed with restricted inheritance (Kotlin, Swift, C# `sealed`), or
does not expose a public constructor the subclass can call.

**Wrapper local extension (composition, any language).** A new class holds an
instance of the Foreign Class as a field rather than extending it, and
forwards calls to the original surface explicitly, one method at a time,
while adding the new methods on top. Works regardless of whether the Foreign
Class permits subclassing, and never accidentally exposes a Foreign Class
method the wrapper did not intend to forward. Costs more code up front, one
forwarding line per Foreign Class method the wrapper wants to keep
accessible, and this cost grows with the size of the Foreign Class's own
public surface.

**Struct embedding (Go).** Go has no class inheritance, so the language's own
idiomatic substitute for the subclass local extension is struct embedding. a
new struct embeds the Foreign Class's struct as an unnamed field, which
promotes all of the embedded type's methods onto the new type automatically,
and additional methods are declared directly on the new type. The Go example
in this entry uses this form, and it behaves like the subclass local
extension in ergonomics (no per method forwarding needed) while behaving like
the wrapper form in type identity (the new type is not interchangeable with
the embedded type without an explicit field access), because Go has no
inheritance based `is a` relationship to preserve.

**Monkey patching (Ruby, Python, JavaScript prototype patching).**
Reopening the foreign type at runtime and attaching the missing method
directly to it, so every existing instance of the type, everywhere in the
process, gains the new method with no wrapper, no subclass, and no
conversion step. This is the most invasive variant, discussed further as a
non applicability case in dimension 4 and as a failure mode in dimension 11,
because it changes shared global state rather than adding an opt in local
type.

## 9. Known production uses

**Joda-Time, as a response to `java.util.Date` and `java.util.Calendar`
being incomplete.** Joda-Time's own project page states plainly that "the
standard date and time classes prior to Java SE 8 are poor" and that it
"became the de facto standard date and time library for Java prior to Java SE
8." It names specific gaps directly, that `Calendar` "makes accessing 'normal'
dates difficult, due to the lack of simple methods", solved with
"straightforward field accessors such as `getYear()` or `getDayOfWeek()`", and
that the JDK's approach to alternate calendar systems "is clunky, and in
practice it is very difficult to write another calendar system", solved with
"a pluggable system based on the `Chronology` class"
(https://www.joda.org/joda-time/, verified 2026-08-02). This is Incomplete
Library Class at the scale of an entire replacement library rather than a
single missing method. the standard library's date type was too incomplete
to patch call site by call site, so the response was a full Local Extension
style replacement library, and the same page records that Java SE 8's own
`java.time` package, JSR-310, was designed to close the same gaps at the
platform level, after which Joda-Time itself recommends new projects migrate
away from it (same source, verified 2026-08-02).

**Apache Commons Lang, as a response to `java.lang` classes lacking
manipulation methods.** The project's own page states its purpose directly.
"The standard Java libraries fail to provide enough methods for manipulation
of its core classes", and describes the library as offering "a host of helper
utilities for the java.lang API, notably String manipulation methods, basic
numerical methods, object reflection, concurrency, creation and
serialization and System properties"
(https://commons.apache.org/proper/commons-lang/, verified 2026-08-02). Its
`StringUtils` class in particular is a textbook Foreign Method holder at
production scale. `java.lang.String` is a final class in Java, so it cannot
be subclassed, and `StringUtils` exists as a static utility class whose every
method takes a `String` as its first parameter and returns a derived or
transformed value, the exact shape Fowler's Introduce Foreign Method
describes, applied to the entire missing surface of the JDK's `String` type
rather than to one method.

**C# extension methods, as a language feature built specifically to
generalize this smell's resolution.** Microsoft's own documentation states
the motivating case directly. "Rather than creating new objects when reusable
functionality needs to be created, you can often extend an existing type,
such as a .NET or CLR type", naming `System.String`, `System.IO.Stream`, and
`System.Exception` as concrete examples, and gives the general guideline that
"extension members are preferable when the original source isn't under your
control, when a derived object is inappropriate or impossible, or when the
functionality has limited scope"
(https://learn.microsoft.com/en-us/dotnet/csharp/programming-guide/classes-and-structs/extension-methods,
verified 2026-08-02). LINQ's own standard query operators are themselves
implemented this way. the documentation describes them as extension methods
that "add query functionality to the existing `System.Collections.IEnumerable`
and `System.Collections.Generic.IEnumerable<T>` types" so that "any type that
implements `IEnumerable<T>` appears to have instance methods such as
`GroupBy`, `OrderBy`, `Average`" (same source, verified 2026-08-02), which is
Incomplete Library Class resolved for an entire family of collection
interfaces at once, at the scale of the standard library shipping the
extension itself rather than an application team writing one.

**Kotlin's extension function syntax, as a first class alternative to
subclassing a foreign type.** Kotlin's own documentation frames extension
functions explicitly against this smell's non language specific
alternatives. "Kotlin extensions let you extend a class or an interface with
new functionality without using inheritance or design patterns like
Decorator. They are useful when working with third-party libraries you can't
modify directly" (https://kotlinlang.org/docs/extensions.html, verified
2026-08-02). The same documentation states the safety property that makes
extensions preferable to monkey patching. "Importantly, extensions don't
modify the classes or interfaces they extend. When you define an extension,
you don't add new members. You make new functions callable or new properties
accessible using the same syntax" (same source, verified 2026-08-02), meaning
the addition is scoped to wherever the extension is imported, not injected
globally into every user of the type across the process.

## 10. Consequences

Positive.

- The knowledge of how to compute a derived value from a foreign type's data
  lives in exactly one place, whichever form is chosen, instead of being
  reimplemented at every call site that needs it, closing the drift risk
  described in dimension 2.
- The foreign class stays genuinely untouched. no local patch, no forked
  source tree to keep in sync with upstream, so security fixes and
  correctness fixes from the library's maintainers apply cleanly on the next
  upgrade with no manual reconciliation.
- Call sites read close to how they would read if the missing method had
  always existed, especially with a language level extension mechanism or a
  well named foreign method, so the missing capability does not visually
  stand out as a workaround once the addition is made.
- A local extension groups every addition to a given foreign type in one
  place, giving the team a single file to check before writing a new
  addition, which reduces the chance of two authors independently writing
  the same missing method under two different names.

Negative.

- A foreign method or extension can only ADD capability. it cannot correct or
  override behavior the foreign class already has, so this smell's
  refactorings are the wrong tool the moment the actual need is "make this
  existing method behave differently" rather than "add a method that does
  not exist yet", covered as a non applicability case in dimension 4.
- The wrapper form of local extension costs one forwarding method per
  original public method the wrapper wants to keep accessible, and this cost
  is paid up front and maintained forever as the foreign class's own surface
  grows across versions.
- A local extension that subclasses the foreign type introduces a second
  type into the codebase's vocabulary for every call site to reason about,
  the original foreign type and the extension, and code that receives a bare
  instance of the original type has to be explicitly converted through the
  factory point before the extension's added methods become available.
- Scattered, uncoordinated foreign methods across a codebase, one written per
  call site with no shared location, recreate the exact duplication and
  drift problem this smell exists to prevent, one level removed, this
  is the failure mode covered first in dimension 11.

## 11. Failure modes and misuse

**Symptom.** The same missing computation from a foreign class appears,
independently implemented with slightly different logic, in more than one
part of the codebase, and the two implementations quietly disagree on an
edge case (rounding, a boundary value, a locale specific formatting rule).
**Cause.** Foreign methods were written ad hoc, one at a time, near whichever
call site needed them first, with no shared module or naming convention for
"foreign methods on this foreign type", so a second author writing the same
capability later had no way to discover the first one already existed.
**Fix.** Consolidate every foreign method for a given foreign type into one
owned module (or, once several methods have accumulated, promote them into a
local extension class), and grep for the type's name across the codebase
before adding a new foreign method, to confirm one does not already exist.

**Symptom.** A production incident traces back to a security vulnerability or
a correctness bug in a third party library that was already fixed upstream
months earlier, and the fix never reached the running system.
**Cause.** The team's response to an incomplete library class, at some point
in the codebase's history, was to vendor a copy of the library and patch the
copy directly, rather than adding a foreign method or a local extension on
top of the unmodified, upgradeable dependency. The patched copy silently
diverged from every subsequent upstream release. **Fix.** Replace the vendored
patched copy with the unmodified, normally upgraded dependency plus a
foreign method or local extension that adds back exactly the capability the
patch was for, restoring the team's ability to take upstream fixes on every
future upgrade. Treat any existing vendored fork discovered during a code
audit as a standing liability to remove, not a settled decision to leave
alone.

**Symptom.** A behavior in the codebase changes unexpectedly after adding an
unrelated third party dependency, with no code change in the affected area,
and the change is difficult to trace because nothing in a stack trace points
at the actual cause. **Cause.** Two dependencies, or a dependency and the
codebase's own code, both monkey patched the same foreign type, and the one
loaded second silently overwrote the first's patch, or a monkey patch
intended to be narrow ended up changing behavior for every caller of the
foreign type in the process, including code the patch's author never
considered. **Fix.** Replace the monkey patch with a local extension or a
foreign method, which is opt in per call site rather than global, so
unrelated code paths are unaffected by the addition, and any remaining
monkey patch that genuinely must stay carries an explicit comment naming why
a scoped alternative was not sufficient.

**Symptom.** A pull request diff shows a two line addition to a vendored
third party file, buried among unrelated dependency update noise, and the
reviewer approves it without noticing the vendored source was touched at
all. **Cause.** The team has no standing rule that vendored dependencies are
never edited directly, so the path of least resistance in a moment of
urgency was to add the missing method straight into the library's own file
rather than reaching for a foreign method. **Fix.** Adopt a policy, enforced
by code review or by a lint rule scoped to vendored directories, that
vendored source is never diffed in a normal pull request. any addition to a
foreign type's capability is required to land as a foreign method or a local
extension in owned code, never as an edit inside the vendored tree.

## 12. Trade-off matrix

Judgement. the weighting below reflects typical application code rather than
a formal proof, and the right choice always depends on how many methods are
missing, whether the foreign type permits subclassing, and whether the
codebase's language offers dedicated extension syntax.

| Force | Foreign Method (free function) | Local Extension, subclass | Local Extension, wrapper | Adapter | Decorator | Monkey patch |
|---|---|---|---|---|---|---|
| Preserves upgradeability of the foreign type | Full, no changes to the foreign type at all | Full, subclass wraps an unmodified type | Full, wrapper holds an unmodified type | Full, adapter wraps an unmodified type | Full, decorator wraps an unmodified type | None, patches the type's own runtime behavior |
| Adds capability the foreign type lacks | Yes, this is its purpose | Yes, this is its purpose | Yes, this is its purpose | No, Adapter changes an interface's SHAPE, it does not add new behavior beyond what the adaptee already offers under a different name | No, Decorator changes or wraps EXISTING behavior at call time, usually without adding brand new named methods | Yes, but globally rather than per call site |
| Preserves type identity with the original | Full, no new type introduced | Full, subclass IS the original type | None, wrapper is a distinct type | None, adapter is a distinct type | Depends, many Decorator implementations preserve the original interface type | Full, the original type itself is modified |
| Works when the foreign type is final or sealed | Yes, no inheritance required | No, subclassing is impossible by definition | Yes, composition does not need subclassing rights | Yes, composition does not need subclassing rights | Yes, composition does not need subclassing rights | Depends on language, some final/sealed guarantees also block monkey patching |
| Scope of the change per call site | Local, one function call | Local, opt in via the factory point | Local, opt in via the factory point | Local, opt in via wrapping | Local, opt in via wrapping | Global, affects every caller in the process |
| Best suited to | One or two missing methods | Several missing methods, subclassing permitted, type identity matters | Several missing methods, subclassing forbidden or type identity not needed | Reconciling two INCOMPATIBLE existing interfaces, see dimension 13 | Adding or altering behavior around EXISTING calls, see dimension 13 | Narrow, well documented compatibility shims only |

## 13. Related and incompatible patterns

**Adapter.** Adapter and the Local Extension refactoring both wrap an
existing object, and the two are easy to conflate. the distinction is intent.
Adapter exists to translate one already existing interface into ANOTHER
already existing interface a client expects, so two incompatible but already
complete interfaces can work together, whereas a Local Extension exists to
ADD capability that neither the original type nor any target interface
already has. A Local Extension that happens to also implement some other
interface the codebase needs is doing double duty as an Adapter, and it is
worth naming that duty explicitly rather than letting the extension's
purpose blur.

**Decorator.** Decorator wraps an object of the SAME interface it implements,
so a decorated instance is interchangeable with an undecorated one from a
caller's point of view, and Decorator's purpose is to add or alter behavior
AROUND an existing method call, commonly by calling through to the wrapped
object and doing something before or after. A Local Extension's wrapper form
looks similar in shape (compose over the foreign type) but its purpose is
different, adding brand new named methods the original interface never had,
not decorating calls to methods the original interface already exposes. Kotlin's
own documentation makes this same distinction explicit when it describes
extension functions as an alternative to "design patterns like Decorator"
for adding functionality without inheritance
(https://kotlinlang.org/docs/extensions.html, verified 2026-08-02).

**Feature Envy.** Feature Envy is the sibling smell for the inverse
situation, when a method that lives in OWNED code reaches into a different
owned class's data more than its own. Incomplete Library Class shares its
root cause (a method's natural home does not match where it currently lives
or could live), but the fix directions differ, because Feature Envy's fix is
Move Method into a class the team already owns, while Incomplete Library
Class has no such class to move into, since the ideal home, inside the
foreign class itself, is unreachable.

**Data Class.** A foreign type that exposes only accessors and holds no
behavior of its own is exactly the shape Data Class describes, and a
codebase that repeatedly writes foreign methods against the same data
carrying foreign type is effectively treating that foreign type as a Data
Class from the outside. The two smells frequently co-occur when the
dependency in question is itself a plain data transfer object generated from
a schema, an API client response type, or a serialization format.

**Alternative Classes with Different Interfaces.** When two different
libraries each provide their own version of a similar concept (two different
date libraries, two different HTTP client response types) with different
method names for the same underlying operation, and the codebase writes
separate foreign methods or separate local extensions for each one instead
of unifying them behind one shape, the result is the Alternative Classes with
Different Interfaces smell layered on top of two separate instances of
Incomplete Library Class. Consider unifying the two extensions' interfaces,
or introducing a shared Adapter over both, rather than letting the
duplication compound.

**Incompatible with monkey patching as a design stance.** A codebase that has
adopted monkey patching as its default answer to a missing library method
(as opposed to using it narrowly, as an occasional, explicitly documented
exception) is not practicing this smell's refactorings at all, it has chosen
the alternative described in dimension 4 and 11 instead, and the two stances
do not mix well within one codebase, because a reader cannot tell, without
checking every dependency's source, whether a given foreign type's public
surface has been silently altered somewhere in the process.

## 14. Refactoring path in and out

**Introducing a Foreign Method, step by step.** Confirm the missing behavior
is genuinely absent from the foreign type's public surface, not merely
differently named, checking the library's own documentation first rather
than assuming. Write a function in an owned module, naming it for the
capability it adds, taking the foreign type's instance as its first
parameter, and implement it using only the foreign type's already published
public methods. Replace every inlined, hand duplicated copy of the same
computation across the codebase with a call to the new foreign method,
verifying at each replacement that the existing inline logic and the new
function agree, which is itself often how a latent disagreement between two
copies (the first failure mode in dimension 11) gets discovered. If the
language offers dedicated extension function or extension method syntax,
prefer declaring the function that way from the start, since it costs
nothing over a plain free function and improves call site readability.

**Promoting a Foreign Method into a Local Extension.** Once a second, then a
third foreign method accumulates for the same foreign type, this is the
trigger to promote. Decide subclass versus wrapper first, checking whether
the foreign type is final, sealed, or otherwise closed to inheritance in the
codebase's language, which settles the question before any code is written.
Create the new extension type, either extending the foreign type directly or
holding an instance of it as a field. Move each existing foreign method's
BODY into the extension as a proper method (for the subclass form this is
usually a direct move, for the wrapper form each moved method now calls the
foreign type through the held field rather than through a parameter). Add
one static factory method or constructor that accepts an existing instance
of the foreign type, or the foreign type's own construction arguments, and
produces an instance of the extension, then route existing call sites
through that single conversion point. Delete the standalone foreign method
functions once every call site has moved, unless some remain in use as
convenient one liners for code that does not otherwise need the extension's
full surface, which is a reasonable coexistence rather than a smell.

**Refactoring away from a Local Extension, when it stops earning its
place.** If a library upgrade adds the missing capability as part of its own
published surface, meaning the foreign type itself now provides what the
local extension was compensating for, replace call sites that use the
extension's added method with calls to the newly available published method,
verify the two produce identical results across the extension's existing
test coverage, then delete the now redundant extension method (keep the
extension type itself if it still holds other methods the library still
lacks). If the extension's wrapper form has grown to forward nearly every
method of a large foreign type only to keep the foreign type's original
surface accessible, and only one or two of the extension's own added methods
are actually used anywhere, consider collapsing back down to a small number
of standalone foreign methods instead, which removes the forwarding
maintenance burden entirely, this is the reverse of the promotion step above
and is a legitimate refactoring when the extension's overhead has stopped
paying for itself.

## 15. Testing and verification

Judgement, drawn from how these two variants differ in shape rather than
from a single cited source.

A Foreign Method is the easiest of the two forms to test in isolation,
because it is a pure function of its arguments, construct an instance of the
foreign type using the foreign type's own public constructor or factory
(no test double needed for the foreign type itself, since it is real,
already tested code owned by the library's own maintainers), call the
foreign method, and assert on the result. There is no new type to construct
a fixture for beyond what the foreign library itself already provides.

A subclass Local Extension is tested the same way as any subclass, construct
it directly through its own factory method, and both the inherited behavior
(exercised through the parent type's own already-published contract, which
does not need re-testing here) and the newly added methods should be
covered, with the added method tests being the ones that carry real value,
since the inherited behavior is the library's own responsibility to have
already verified.

A wrapper Local Extension needs a slightly different test shape, because it
holds the foreign type rather than extending it, and every forwarded method
is a candidate for a subtle bug (a forgotten parameter, a mismatched return
transformation) that a pure "does compilation succeed" check will not catch.
Cover at minimum every forwarded method with one assertion confirming the
wrapper's forwarded call and the direct call to the underlying foreign type
produce the same result, which catches accidental forwarding mistakes early,
and cover every newly added method with its own dedicated test the same as
the subclass form.

Where the foreign type is expensive to construct in a test (a network client,
a database connection wrapper), and the extension or foreign method's own
logic does not actually need a live instance to verify, consider testing the
extension or foreign method against a minimal fake that satisfies only the
public methods the extension or foreign method actually calls, rather than
against the full, expensive real foreign type, which keeps the unit test fast
while an integration level test elsewhere still exercises the real
dependency.

## 16. Observability signals

Judgement, this dimension is practice guidance rather than a set of sourced
facts.

At the codebase level rather than at runtime, the signal to watch for is
structural. periodically grep for foreign method modules and local extension
classes across the codebase and count how many exist per foreign type. A
foreign type with three, four, or more independently named foreign methods
scattered across different files, with no shared module, is the signal that
a promotion to a local extension (dimension 14) is due, and this check is
cheap enough to run as part of a routine architecture review rather than
needing dedicated tooling.

If a local extension wraps a foreign type that itself performs I/O (a
network call, a disk read), instrument the extension's added methods the
same way the codebase already instruments any other I/O boundary, latency,
error rate, and retry counts attributed specifically to calls that pass
through the extension, so a regression introduced by the extension's own
added logic (as opposed to a regression in the underlying foreign type
itself) is separable in a trace or a dashboard from the foreign type's own
calls.

Watch dependency update logs and changelogs for the specific foreign type a
local extension or foreign method wraps. the moment an upstream release adds
the capability the extension was compensating for as part of its own
published surface, that is the trigger for the "refactoring away from a
Local Extension" step in dimension 14, and a team that does not watch for
this signal tends to carry redundant, unnecessary extensions long after the
underlying dependency has made them obsolete.

## 17. Security and privacy implications

The Foreign Method and Local Extension forms are, by construction, additive
and use only the foreign type's already published public surface, so they do
not open any new attack surface beyond what already exists in the dependency
itself, and this entry states that plainly rather than inventing a concern
that is not there. The one genuine implication worth naming concerns the
monkey patch variant discussed in dimensions 8, 11, and 13. because a monkey
patch alters the foreign type's behavior for every caller in the process
globally, a monkey patch that changes how a security relevant method behaves
(a validation check, a comparison used for authentication, an encoding or
escaping routine) changes it for every OTHER dependency and every OTHER part
of the codebase that also calls that method, including code the monkey
patch's author never audited and may not even know exists. A vendored,
directly patched copy of a library carries a related but distinct risk,
discussed as a failure mode in dimension 11. the patched copy silently stops
receiving the library maintainers' own security fixes on every future
upgrade, so a codebase that vendors and patches a dependency instead of using
a foreign method or local extension on top of an unmodified, normally
upgraded dependency is accepting an ongoing, compounding security debt in
exchange for a one time convenience.

## 18. References

1. Martin Fowler, *Refactoring. Improving the Design of Existing Code*,
   Addison-Wesley, 1st edition, 1999, chapter "Bad Smells in Code" (source of
   the Incomplete Library Class name and its motivating refactorings).
2. Martin Fowler, "CodeSmell", martinfowler.com bliki, attribution of the
   term "code smell" to Kent Beck.
   https://martinfowler.com/bliki/CodeSmell.html, verified 2026-08-02.
3. Martin Fowler, "Introduce Foreign Method", Refactoring catalog.
   https://refactoring.com/catalog/introduceForeignMethod.html, verified
   2026-08-02. Cites first edition, dated 9 Oct 1999, page 162.
4. Martin Fowler, "Introduce Local Extension", Refactoring catalog.
   https://refactoring.com/catalog/introduceLocalExtension.html, verified
   2026-08-02. Cites page 164.
5. SourceMaking, "Code Smells", overview and category listing placing
   Incomplete Library Class under "Couplers".
   https://sourcemaking.com/refactoring/smells, verified 2026-08-02.
6. SourceMaking, "Incomplete Library Class".
   https://sourcemaking.com/refactoring/smells/incomplete-library-class,
   verified 2026-08-02.
7. Joda-Time project page, motivation for the library's creation relative to
   `java.util.Date` and `java.util.Calendar`. https://www.joda.org/joda-time/,
   verified 2026-08-02.
8. Apache Commons Lang project page, stated purpose relative to `java.lang`.
   https://commons.apache.org/proper/commons-lang/, verified 2026-08-02.
9. Microsoft Learn, "Extension members - C#", motivation, mechanics, and the
   `ref` receiver caveat for value types.
   https://learn.microsoft.com/en-us/dotnet/csharp/programming-guide/classes-and-structs/extension-methods,
   verified 2026-08-02.
10. Kotlin documentation, "Extensions", motivation relative to inheritance
    and Decorator, and the no-mutation guarantee.
    https://kotlinlang.org/docs/extensions.html, verified 2026-08-02.

## Code examples

### TypeScript

```typescript
class Temperature {
  constructor(private readonly celsiusValue: number) {}
  celsius(): number {
    return this.celsiusValue;
  }
}

// Introduce Foreign Method. Temperature ships from a package this codebase
// does not own, so the conversion lives beside it as a free function.
function toFahrenheit(t: Temperature): number {
  return t.celsius() * 9 / 5 + 32;
}

// Introduce Local Extension. Several derived methods accumulated, so they
// are promoted into one owned subclass with a single conversion point.
class RichTemperature extends Temperature {
  static from(t: Temperature): RichTemperature {
    return new RichTemperature(t.celsius());
  }
  toFahrenheit(): number {
    return toFahrenheit(this);
  }
  toKelvin(): number {
    return this.celsius() + 273.15;
  }
  describe(): string {
    return `${this.celsius().toFixed(1)}C (${this.toFahrenheit().toFixed(1)}F)`;
  }
}

const boiling = new Temperature(100);
if (toFahrenheit(boiling) !== 212) {
  throw new Error("foreign method disagreement");
}

const freezing = RichTemperature.from(new Temperature(0));
console.log(freezing.describe());
```

Compiled with `tsc --strict --noEmit` and run under Node 23. output confirmed
`0.0C (32.0F)`.

### Python

```python
class Temperature:
    def __init__(self, celsius: float) -> None:
        self._celsius = celsius

    def celsius(self) -> float:
        return self._celsius


# Introduce Foreign Method. A plain function taking the foreign instance
# as its first argument, using only Temperature's own public surface.
def to_fahrenheit(t: Temperature) -> float:
    return t.celsius() * 9 / 5 + 32


# Introduce Local Extension. Python permits subclassing built in and
# third party types alike, so the subclass form applies directly here.
class RichTemperature(Temperature):
    @classmethod
    def from_temperature(cls, t: Temperature) -> "RichTemperature":
        return cls(t.celsius())

    def to_fahrenheit(self) -> float:
        return to_fahrenheit(self)

    def to_kelvin(self) -> float:
        return self.celsius() + 273.15

    def describe(self) -> str:
        return f"{self.celsius():.1f}C ({self.to_fahrenheit():.1f}F)"


if __name__ == "__main__":
    boiling = Temperature(100)
    assert to_fahrenheit(boiling) == 212.0

    freezing = RichTemperature.from_temperature(Temperature(0))
    assert freezing.describe() == "0.0C (32.0F)"
    print(freezing.describe())
```

Run directly with `python3 example.py` on CPython 3.14. output confirmed
`0.0C (32.0F)`.

### Go

```go
package main

import "fmt"

type Temperature struct {
	celsius float64
}

func NewTemperature(celsius float64) Temperature {
	return Temperature{celsius: celsius}
}

func (t Temperature) Celsius() float64 {
	return t.celsius
}

// Introduce Foreign Method. Go has no inheritance, so a free function is
// the direct equivalent for a single missing capability.
func ToFahrenheit(t Temperature) float64 {
	return t.Celsius()*9/5 + 32
}

// Introduce Local Extension via struct embedding, the language idiomatic
// substitute for subclassing a type Go's own type system has no notion of
// extending. Celsius() is promoted automatically through the embedded field.
type RichTemperature struct {
	Temperature
}

func (r RichTemperature) ToFahrenheit() float64 {
	return ToFahrenheit(r.Temperature)
}

func (r RichTemperature) ToKelvin() float64 {
	return r.Celsius() + 273.15
}

func (r RichTemperature) Describe() string {
	return fmt.Sprintf("%.1fC (%.1fF)", r.Celsius(), r.ToFahrenheit())
}

func main() {
	boiling := NewTemperature(100)
	if got := ToFahrenheit(boiling); got != 212 {
		panic(got)
	}

	freezing := RichTemperature{NewTemperature(0)}
	fmt.Println(freezing.Describe())
}
```

Run with `go run main.go` on Go's current toolchain. output confirmed
`0.0C (32.0F)`.

Java, Rust, and Swift are omitted from the runnable examples in this entry.
the Foreign Method form is identical in shape across all three (a static
method or free function taking the foreign instance as its first parameter),
and the Local Extension form maps onto Java's subclassing exactly as the
TypeScript and Python examples show, onto Rust's trait implementation for a
foreign type where Rust's orphan rule permits it, and onto Swift's protocol
extensions or `extension` declarations, all of which this entry's dimension 8
already describes without repeating the same worked example a fourth and
fifth and sixth time.
