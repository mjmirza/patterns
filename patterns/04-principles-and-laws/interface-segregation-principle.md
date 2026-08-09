---
name: Interface Segregation Principle
slug: interface-segregation-principle
family: 04-principles-and-laws
category: Principle
aliases: [ISP, Role Interfaces, Fat Interface Anti-Pattern (the thing it opposes)]
first_described: "Robert C. Martin, 1996, C++ Report article, restated in Agile Software Development: Principles, Patterns, and Practices, 2002"
maturity: canonical
related: [single-responsibility-principle, dependency-inversion-principle, open-closed-principle, adapter, facade, strategy]
incompatible_with: []
verified: 2026-08-02
---

# Interface Segregation Principle

## 1. Name, aliases, and lineage

The canonical name is the Interface Segregation Principle, almost always
abbreviated ISP, the fourth of the five principles Robert C. Martin grouped
under the acronym SOLID. Martin's own statement of it, quoted directly, is "no
client should be forced to depend on methods it does not use" (Wikipedia
contributors, "Interface segregation principle," verified 2026-08-02,
https://en.wikipedia.org/wiki/Interface_segregation_principle). Martin first
formulated ISP while consulting for Xerox on the software controlling a new
line of printers, and published the idea in a 1996 C++ Report article, then
restated it as one chapter of his 2002 book *Agile Software Development,
Principles, Patterns, and Practices* (same source). The name has no widely
used alternative. Some writers refer to the interfaces the principle produces
as "role interfaces," a term this entry uses interchangeably to describe the
output of applying ISP, an interface shaped around what one kind of client
needs rather than around everything a class happens to do.

The Xerox origin story is worth stating because it is the clearest possible
illustration of what ISP is reacting against, and every later explanation of
the principle traces back to it. Xerox was building software for a new
generation of printers that could also staple, fax, and collate. The team's
first design put every operation on one `Job` class, so a class that only
needed to submit a print job depended on a class that also exposed staple
methods, fax methods, and collate methods, and any client of `Job` recompiled
whenever any one of those unrelated capabilities changed. Martin's fix was to
split the fat `Job` interface into narrower ones, a `PrintJobInterface` for
clients that only print, a `StapleJobInterface` for clients that only staple,
so that a class implementing only printing depends on only the printing
interface (Wikipedia contributors, "Interface segregation principle,"
verified 2026-08-02, same URL as above, section describing the Xerox example).
The story matters because it shows ISP was discovered as a fix for a real
coupling bug in a real codebase, not derived from first principles at a
whiteboard.

ISP sits inside SOLID alongside the Single Responsibility Principle, the
Open-Closed Principle, the Liskov Substitution Principle, and the Dependency
Inversion Principle (Wikipedia contributors, "Interface segregation
principle," verified 2026-08-02, same URL as above, SOLID summary section).
The relationship to SRP is close enough that the two are frequently confused,
and this entry is explicit about the distinction in dimension 13. ISP is also
cited in the microservice design literature as one of the five principles
that map onto service boundaries under the IDEALS framework, where interface
segregation becomes a statement about the shape of a service's exposed API
rather than a language-level interface (same source, "In microservices"
section). That extension is not a separate lineage, it is the same principle
applied at a coarser grain, and this entry treats service-API segregation as
a variant of ISP rather than a distinct pattern.

## 2. Problem and context

The problem ISP names is specific and recognizable once you have seen it. An
interface, abstract class, or protocol grows over time as new capabilities
get added to the type it describes, and every client that depends on that
type is forced to depend on the whole thing, including the parts it never
calls. A concrete example follows. A `Worker` interface starts with
`doWork()`. Time passes, and someone adds `takeBreak()`, `eat()`, and
`sleep()`, because the concrete workers in the system are humans and it
seemed natural to keep everything about a worker in one place. Now a
`RobotWorker` class, which does work but never eats or sleeps, is forced to
implement `eat()` and `sleep()` with a body that throws
`UnsupportedOperationException` or silently does nothing, because the
language requires every method of an implemented interface to have a body.
This is the textbook case Martin himself uses to introduce the idea in
*Agile Software Development*, and it is repeated widely enough in the
secondary literature on SOLID that it functions as the canonical teaching
case, though the original wording is Martin's.

The context in which this problem arises is any place where a language
forces a class to implement every member of an interface it claims to
satisfy, which is to say, any nominally-typed language with interfaces or
abstract base classes. Java, C#, Kotlin, Swift, and any C++ codebase using
pure abstract base classes as interfaces all share this shape. The problem
also arises, in a milder form, in structurally-typed languages like Go and
TypeScript, but there the failure mode shifts. Instead of a forced empty
method body, the failure is a type that is technically usable through a
narrow interface but whose author wrote one giant struct or class exposing
dozens of public methods with no interface in front of it at all, so every
caller sees the entire surface even though a structural interface could have
hidden most of it. Dimension 8 treats this distinction in detail, because it
changes what "applying ISP" looks like in practice from language to
language.

The problem also shows up one level removed from code, in service
boundaries. A single microservice or a single third-party API that exposes
fifty endpoints to every consumer, when most consumers only ever call three
of them, has the same shape as a fat interface. Every consumer is coupled to
changes in the fifty, has to authenticate against the whole surface, and is
exposed to the entire deprecation and versioning history of endpoints it
never uses. This is the service-level reading of ISP referenced in
dimension 1.

## 3. Forces

**Cohesion of the abstraction versus number of types in the system.** A
single `Worker` interface with four methods is one type to remember.
Splitting it into `Workable`, `Eatable`, and `Sleepable` is three types,
each smaller, but now anyone reading the code has to hold three names in
mind instead of one, and has to trace which concrete classes implement which
combination. ISP trades a larger vocabulary of small types for freedom from
forced unused-method implementations. This is a real cost, not a free
lunch, and the trade only pays off when clients genuinely differ in what
subset of behavior they need.

**Compile-time and rebuild cost versus interface count, in statically
compiled languages.** In C++ especially, and to a lesser degree in Java and
Kotlin, a change to an interface a class depends on forces recompilation of
every translation unit that includes that interface, whether or not the
specific change touched the methods that translation unit calls. A fat
interface widens the blast radius of every change to it. This force is why
ISP is often discussed as an interface-level analogue of the compile
firewall idiom in C++, and why it matters more in compiled, statically
linked systems than in dynamically dispatched, interpreted ones, where the
cost of a fat interface is closer to purely cognitive.

**Client-specific views versus a single source of truth for the type's
contract.** When you split an interface into role interfaces, you now have
several places describing what a `Worker` can do instead of one, and it
becomes possible for the role interfaces to drift, for `Workable` to add a
method that logically belongs with `Sleepable`, or for a client to have to
implement two or three role interfaces to get behavior that used to come
from one. ISP does not eliminate this force, it relocates it, moving the
burden of assembling the right combination of roles from the type's
original author onto every client and every implementer.

**Discoverability versus precision.** A fat interface is easy to discover.
Open the file, see every method the type could possibly need. A well
segregated set of role interfaces requires the reader to know which
interfaces exist and which ones apply to their situation before they can
find the method they need, particularly in languages without strong IDE
support for interface composition. ISP favors precision of dependency at
the cost of discoverability, and teams that rely heavily on browsing a class
to see what it can do as their primary code navigation strategy feel this
cost directly.

**Interface versioning and evolution versus surface area.** A narrow
interface is easier to version without breaking existing implementers,
because adding a method to a narrow interface breaks fewer implementers
than adding a method to a fat one. This favors ISP strongly in any system
with external implementers of an interface, plugins, third-party adapters,
contract testing across service boundaries, where the cost of a breaking
change is paid by parties outside the team's control.

ISP consistently favors decoupling and change-isolation over minimizing the
number of named types and over the convenience of a single, discoverable
contract. It sacrifices simplicity of the type system for precision of
dependency, and that sacrifice is worthwhile in direct proportion to how
often, and how differently, distinct kinds of clients actually use the
type.

## 4. Applicability and non-applicability

Apply ISP when the following hold.

1. A single interface or abstract class has grown methods serving genuinely
   different clients, and at least one implementer has to fake, stub, or
   throw on a subset of those methods because it does not logically support
   them. This is the strongest, most concrete signal. An empty method body,
   a `NotImplementedError`, or a comment reading "not applicable for this
   type" is direct evidence the interface should split.
2. Different kinds of consumers of a type genuinely use disjoint or nearly
   disjoint subsets of its methods, and this fact is stable, not a
   transient artifact of how the code happens to be organized today.
3. The type in question is a plugin contract, an SPI (service provider
   interface), or any boundary where third parties will implement it, and
   you want additions to the contract to be possible without breaking every
   existing implementer.
4. You are designing a public library or API and want to expose the
   smallest possible contract that lets a consumer do the one thing they
   came for, so the library's own internal implementation details do not
   leak into the caller's compile-time dependency graph.
5. You are working in a statically compiled language and rebuild time from
   a change to a widely depended-upon interface has become a measurable
   friction, evidenced by a change to one interface method triggering
   rebuilds across an unrelated part of the codebase.

Do NOT apply ISP when the following hold.

1. The interface has one real client and one real implementer, and there is
   no evidence a second, differently-shaped client is coming. Splitting a
   single-purpose interface into three role interfaces for future
   flexibility is speculative generality, not interface segregation, and it
   adds indirection with no client that currently benefits from it.
   Martin's own later writing warns against exactly this over-application,
   and the YAGNI heuristic is the correct counterweight here.
2. The methods on the interface, though numerous, are genuinely part of one
   cohesive concept that every real implementer uses in full. An interface
   like a database `Transaction` with `begin()`, `commit()`, `rollback()`
   is not fat merely because it has three methods. Every real
   implementation of a transaction genuinely needs all three, and splitting
   them would not remove any forced-unused-method problem because there is
   none to remove.
3. The language already gives you structural typing, as Go and TypeScript
   do, and no caller has yet needed anything less than the full type. In a
   structurally typed language, a caller can declare the narrow interface
   it needs at the point of use without the type's author pre-declaring
   every possible narrow view in advance. Pre-splitting the type in this
   situation is solving a problem the language's type system already
   solves on demand. Dimension 8 expands on this point at length.
4. Doing so would violate the Liskov Substitution Principle by producing
   role interfaces so fine-grained that clients cannot reason about what a
   concrete type does as a whole, only about the fragment of it visible
   through whichever role interface happens to be in scope, to the point
   that understanding the actual object's behavior requires reading five
   files instead of one. There is a floor below which further splitting
   trades real understandability for principle purity.
5. The system is small, has one deployment unit, one team, and no external
   implementers, and the fat interface, while imperfect, is not currently
   causing any of the specific pains ISP addresses, forced fake
   implementations, unwanted rebuild coupling, unwanted client-side
   dependency on unused behavior. Applying ISP prophylactically to code
   that is not yet in pain is the single most common way teams overspend on
   this principle.

## 5. Structure

ISP's structure is best expressed as a before-and-after relationship rather
than a fixed set of participants, because it is a splitting operation
applied to an existing design, not a pattern with its own runtime
machinery.

Before, a single, wide interface, call it `FatInterface`, exposes methods
`m1` through `mN`. Multiple concrete classes, `ClientA`, `ClientB`,
`ClientC`, each use a different subset of those methods, but the language
forces each class implementing `FatInterface` to provide a body for every
one of `m1..mN`.

After, `FatInterface` is replaced by a set of role interfaces,
`RoleInterface1`, `RoleInterface2`, and so on, each exposing only the
methods one class of client actually needs. A concrete class implements the
union of whichever role interfaces describe its real capabilities. A client
that only ever calls `m1` and `m2` depends only on `RoleInterface1`, and is
insulated from any change to `RoleInterface2`, even though the two might be
implemented by the same concrete class at runtime.

Participants, named by role rather than by generic class name, are these.

The wide contract is the original interface before segregation, or more
often, the mental model of "everything this kind of object can do" that
existed before anyone wrote it down as separate interfaces. This is what the
principle is reacting against, not a participant that should exist in the
final design.

A role interface is a narrow, single-purpose interface exposing only the
methods relevant to one class of client. There are typically several role
interfaces where there used to be one wide contract. Each role interface is
named for the capability it represents, `Readable`, `Writable`,
`Closeable`, not for the concrete type that happens to implement it.

A capable implementer is a concrete class that implements one or more role
interfaces, in whatever combination matches its real capabilities. A single
concrete class commonly implements several role interfaces at once. ISP
does not require one class per role, it requires that clients depend only
on the roles they use, regardless of how many roles a given class happens
to fulfil.

A role-scoped client is code that depends on exactly the role interface it
needs, and nothing more. This is the payoff participant. A role-scoped
client's dependency graph, its imports or `using` statements, names only
the capability it actually exercises, and its compile-time or type-level
coupling to the rest of the system shrinks accordingly.

A composing interface is optional. In languages that support interface
inheritance or embedding, a wider interface can be reconstituted from
several role interfaces for the convenience of clients that genuinely need
the full set, without forcing every client through the wide contract. Go's
`io.ReadWriter`, discussed in dimension 9, is the textbook example. It is
defined as the composition of `io.Reader` and `io.Writer`, so a function
that needs both still gets one named type to depend on, while a function
that needs only one still depends only on that one.

## 6. ASCII structure diagram

```text
                     BEFORE (fat interface)

              +-----------------------+
              |      FatInterface     |
              |  m1() m2() m3() m4()  |
              +-----------+-----------+
                           ^
              implements   |   implements
        +------------------+------------------+
        |                                      |
+---------------+                    +-------------------+
|    ClientA    |                    |     ClientB        |
| (uses m1,m2)  |                    | (uses m3,m4)       |
| stubs m3, m4  |                    | stubs m1, m2       |
+---------------+                    +-------------------+


                     AFTER (segregated by role)

     +------------------+           +------------------+
     |  RoleInterface1  |           |  RoleInterface2  |
     |    m1()  m2()    |           |    m3()  m4()    |
     +---------+--------+           +---------+--------+
               ^                              ^
   implements  |                              |  implements
     +---------+---------+          +---------+---------+
     |      ClientA      |          |      ClientB      |
     |  depends ONLY on  |          |  depends ONLY on  |
     |   RoleInterface1  |          |   RoleInterface2  |
     +--------------------+          +--------------------+

     A class capable of both roles implements both interfaces
     without forcing either client to know about the other role.

     +------------------------------+
     |          BothCapable         |
     |  implements RoleInterface1   |
     |  implements RoleInterface2   |
     +------------------------------+
```

## 7. Dynamics

ISP has no runtime behavior of its own, it constrains compile-time or
type-level dependency, so "dynamics" here means the sequence of decisions
that plays out when a new capability needs to be added to a system that
already applies the principle, and how that sequence differs from a system
that does not.

```text
Adding a new capability to a segregated design

1. A new requirement arrives. Some clients now need capability X.
2. Author checks whether an existing role interface already
   describes X.
   -> yes: extend that role interface, only its existing
      implementers and clients are affected.
   -> no: define a new role interface RoleInterfaceX.
3. Concrete classes that genuinely support X implement RoleInterfaceX
   in addition to whatever roles they already implement.
4. New clients that need X depend on RoleInterfaceX only.
5. Existing clients of the other role interfaces recompile or retest
   NOTHING, because their dependency graph never referenced X.


Adding a new capability to a fat-interface design (the failure mode)

1. A new requirement arrives. Some clients now need capability X.
2. Author adds method X to the one shared interface, because that is
   where every method already lives.
3. EVERY class implementing the interface must now provide a body for
   X, including classes with no logical relationship to X, which stub
   it out, throw, or silently no-op.
4. EVERY client of the interface is now compiled or type-checked
   against a contract that includes X, whether or not that specific
   client will ever call it.
5. A change to X's signature later forces a review of every
   implementer and every client, most of which have nothing to do
   with X.
```

The second sequence is the concrete mechanism by which "no client should be
forced to depend on methods it does not use" produces real cost. It is not
an abstract inconvenience, it is a specific, repeatable chain of forced
touch points every time the fat interface changes. The first sequence is
what that chain looks like once the interface has been segregated by role,
and the difference between the two is the entire empirical case for the
principle.

## 8. Implementation variants

The concrete shape ISP takes differs substantially by language, and this is
one of the dimensions where getting the variant wrong produces cargo-cult
code that looks like ISP but does not deliver its benefit.

**Nominal-typing languages with interfaces (Java, C#, Kotlin).** Here the
principle is applied literally as Martin described it. Split one interface
with many methods into several interfaces with few methods each, and have
concrete classes implement whichever combination applies. This is the
textbook variant, and it is the one every SOLID tutorial demonstrates.
Java's `java.io.Closeable` and `java.io.Flushable` are a real example of
exactly this shape in a widely used standard library, discussed with a
citation in dimension 9. The cost of this variant is a proliferation of
small interface files and a need for IDE tooling to stay navigable as the
number of role interfaces grows.

**Structurally-typed languages (Go, TypeScript).** Here the principle takes
a different, more powerful shape, because the type system already gives you
segregation for free at the point of use, without the type's original
author needing to have anticipated it. In Go, any function can declare a
tiny local interface, `type sizer interface { Size() int }`, and any
existing type that happens to have a `Size() int` method satisfies it
automatically, no `implements` declaration required, no coordination with
the type's author needed. This means the correct application of ISP in Go
is usually NOT to pre-split a struct's methods into interfaces up front, it
is to define interfaces at the consuming site, small and named for what the
consumer needs, and let the compiler verify structural satisfaction. The Go
proverb that captures this, attributed to Rob Pike, is "the bigger the
interface, the weaker the abstraction" (Rob Pike, "Go Proverbs," talk given
at Gopherfest, November 2015, transcript and slides at
https://go-proverbs.github.io/, verified 2026-08-02). TypeScript, being
structurally typed for objects, admits the identical variant. Define the
narrow shape you need as a local type alias or interface at the call site,
and any object with matching members satisfies it, whether or not its
author ever heard of your interface.

**Duck-typed and dynamically-typed languages (Python, Ruby, JavaScript
without TypeScript).** ISP still applies conceptually, as an informal
protocol, but there is no compiler to enforce that a client only depends on
a subset. The practical implementation of the principle here is convention
plus, where available, an abstract base class or a `Protocol` (Python's
`typing.Protocol`, introduced in PEP 544) used purely as documentation and,
if type-checked with a tool like mypy, as a lightweight structural
contract. A Python `Protocol` gets you the same benefit as Go's interfaces,
a narrow, named shape that any object can satisfy without inheriting from
anything, and this is the closest Python analogue to structural ISP.

**Functional-interface variant, single-method interfaces as first-class
values.** In languages with first-class functions or lambdas, Java's
`java.util.function.Function<T,R>`, `Supplier<T>`, `Consumer<T>`, C#'s
`Func<T,TResult>` and `Action<T>`, the extreme end of interface segregation
is a one-method interface that a lambda can satisfy directly. This is ISP
taken to its logical minimum. An interface segregated down to exactly one
capability, with no possibility of a client depending on an unused method
because there is only one method to depend on. Strategy and Command,
treated as related patterns in dimension 13, frequently arrive at this
same shape.

**Role interfaces composed back together for convenience.** Where a real
client genuinely needs several roles at once, the composing-interface
variant from dimension 5 and 8 avoids forcing that client to name five
small interfaces in every function signature. Go's standard library does
this routinely. `io.ReadWriteCloser` is nothing more than the embedding of
`io.Reader`, `io.Writer`, and `io.Closer` (verified against the Go standard
library documentation, see dimension 9). This variant proves that
segregation and convenient composition are not in tension, a wide,
convenient type alias can sit on top of narrow, independently useful
primitives.

## 9. Known production uses

**The Go standard library `io` package.** `io.Reader` is defined as a
single method, `Read(p []byte) (n int, err error)`, and `io.Writer` as a
single method, `Write(p []byte) (n int, err error)`. The package
documentation states its purpose as providing "basic interfaces to I/O
primitives," wrapping concrete implementations in `os` and elsewhere into
small shared abstractions, and the package composes these single-method
interfaces into wider ones, `io.ReadWriter`, `io.ReadCloser`,
`io.ReadWriteCloser`, only where a consumer genuinely needs the combination
(Go standard library documentation, package `io`, verified 2026-08-02,
https://pkg.go.dev/io). This is the single most cited real-world example of
ISP in a language whose type system was designed around exactly this shape
of small, composable interface, and it predates and independently arrives
at the same conclusion Martin reached at Xerox. A client that only needs to
read should depend on something that only offers reading.

**The .NET base class library, `IReadOnlyList<T>` versus `IList<T>`.**
`System.Collections.Generic.IReadOnlyList<T>` is documented as representing
"a read-only collection of elements that can be accessed by index,"
exposing only a `Count` property and a get-only indexer, both inherited
from the narrower `IReadOnlyCollection<T>` (Microsoft Learn, "IReadOnlyList<T>
Interface," verified 2026-08-02,
https://learn.microsoft.com/en-us/dotnet/api/system.collections.generic.ireadonlylist-1).
This is deliberately kept as a separate, smaller interface from `IList<T>`,
which also exposes `Add`, `Remove`, `Insert`, and a settable
indexer. A method that only needs to read a caller's list, and should never
be able to mutate it, declares its parameter as `IReadOnlyList<T>` rather
than `IList<T>`, and by doing so is structurally prevented, at the type
level, from depending on the mutation methods it does not use. This is ISP
applied to mutability specifically, and it is one of the most common,
everyday instances of the principle any C# developer touches, whether or
not they connect it to Martin's original writing.

**The Java standard library, `java.io.Closeable` and `java.io.Flushable`
kept as distinct interfaces.** `Closeable` exposes a single method,
`close() throws IOException`, described in the Java 21 API documentation as
representing "a source or destination of data that can be closed" (Oracle,
"Interface Closeable," Java SE 21 API documentation, verified 2026-08-02,
https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/io/Closeable.html).
`Flushable`, similarly, exposes only a `flush()` method. The two are kept
as separate interfaces rather than merged into one "stream lifecycle"
interface precisely because they represent independent, separable
concerns. Resource cleanup on one hand, forcing buffered output to its
destination on the other, and a class can implement one, the other, both,
or neither according to its actual needs, rather than being forced to
provide a body for a capability that does not apply to it (same source,
description and class-hierarchy sections). `Closeable` also
narrows the checked exception on `close()` from the more general
`Exception` declared by its supertype `AutoCloseable` down to
`IOException`, which is itself a form of interface segregation applied to
the exception contract rather than to the method set. I/O-specific callers
get a narrower, more precise checked exception to handle.

**The origin case itself, Xerox's printer controller software.** Robert C.
Martin's consulting work at Xerox on software for a new line of
multi-function printers, which could print, staple, fax, and collate, is
the documented source of the principle. The original design put every
operation on a single `Job` class. Classes that needed only to submit a
print job were forced to depend on a class that also exposed staple and
fax operations. Martin's fix, splitting the class's clients onto narrower
interfaces such as `PrintJobInterface` and `StapleJobInterface`, is
recorded as the concrete case from which the principle was generalized
(Wikipedia contributors, "Interface segregation principle," verified
2026-08-02, https://en.wikipedia.org/wiki/Interface_segregation_principle,
"Origin" section). This is included as a named production use, distinct
from the three library examples above, because it is the historically
first documented instance of the principle being applied to solve a real
coupling problem, not a retrospectively-labelled example.

## 10. Consequences

Positive consequences follow.

1. A client's compile-time or type-level dependency set shrinks to exactly
   what it uses, which shrinks the blast radius of any change to the parts
   it does not use. A change to a method the client never calls no longer
   forces the client to recompile, retest, or even be aware the change
   happened.
2. Forced fake implementations disappear. A class no longer needs to
   provide a stub, a no-op, or a thrown `NotImplementedException` for a
   method it has no meaningful behavior for, because it is never asked to
   implement an interface wider than what it genuinely supports.
3. Interfaces become easier to version without breaking existing
   implementers, because adding a member to a narrow interface only
   affects the smaller set of classes that implement that specific narrow
   interface, not every implementer of a wide one.
4. The set of role interfaces documents, in the type system itself, the
   distinct ways the system's clients actually use a given concept. A
   reader who sees `Readable` and `Writable` as separate types learns
   something true about the system's real usage patterns that a single
   `Stream` interface would have hidden.
5. Testing becomes easier for role-scoped clients, discussed further in
   dimension 15, because a test double for a narrow interface only has to
   satisfy a few methods, not the entire surface of a fat one.

Negative consequences follow.

1. The number of named types in the system increases, sometimes
   substantially, and every additional type is a name a future reader has
   to learn, remember, and correctly select among. This is a real
   cognitive cost, not a rhetorical one, and it scales with how
   aggressively the principle is applied.
2. Assembling the full picture of what a concrete class does now requires
   reading several interface declarations instead of one, which can make
   answering "what can this object do" a multi-file lookup instead of a
   single-file one, particularly painful without strong IDE
   cross-referencing.
3. Over-application produces an interface per method, which is a real,
   observed failure mode, see dimension 11, and produces more indirection
   than any client actually benefits from. The principle gives no
   mechanical stopping rule for how narrow is narrow enough. That
   judgement is left entirely to the engineer.
4. In compiled, nominally-typed languages, adding a role interface still
   requires every concrete class that should support the new role to be
   edited to declare it implements that interface, even in cases where
   duck typing would have made the addition free. This cost is
   language-specific and does not apply in Go or TypeScript, where the
   equivalent addition is often a zero-edit operation on the implementer's
   side, discussed in dimension 8.

## 11. Failure modes and misuse

Symptom. An interface with exactly one implementer, split into three role
interfaces for future flexibility, and none of the three has ever gained a
second implementer.
Cause. The principle was applied speculatively, in anticipation of
variation that has not materialized, rather than in response to an
observed forced-unused-method problem. This is the single most common
misuse and is functionally indistinguishable from the speculative-generality
anti-pattern wearing ISP's name.
Fix. Merge the role interfaces back into one, or better, remove the
interface entirely and depend on the concrete type directly, until a
second, genuinely different implementer actually exists. Reintroduce the
split at that point, guided by the real difference between the two
implementers rather than by a guess made before either existed.

Symptom. A concrete class implements six or seven tiny, single-method
interfaces, and understanding what the class actually does requires
opening six or seven files.
Cause. ISP applied without a corresponding composing interface, dimension
5 and 8, for the common case where most clients genuinely need several of
the roles together. The role interfaces are individually correct but the
design never gives a convenient name to their common combination.
Fix. Introduce a composing interface, an embedding or inheriting type that
unions the frequently-co-required roles, for clients that need the
combination, while still leaving the narrow role interfaces available for
clients that need only one. Go's `io.ReadWriteCloser`, dimension 8 and 9,
is the canonical shape of this fix.

Symptom. A role interface is defined, but every concrete implementer of it
happens to also implement every other role interface in the same group,
and no client has ever depended on fewer than the full set.
Cause. The methods were genuinely cohesive to begin with. They were split
because ISP is supposed to be applied, not because a real
forced-unused-method problem existed. This is the non-applicability case
from dimension 4, item 2, arrived at empirically after the fact rather
than predicted before the split.
Fix. Recombine the roles into one interface. A cohesive set of methods
that every real implementer supports in full and every real client calls
in full is not a violation of ISP to begin with. Forcing it apart does not
reduce coupling, it only adds files.

Symptom. Adding a single new method to a system now requires touching a
long chain of role interfaces because the roles were split along the
wrong axis, for example by data type rather than by client usage pattern.
Cause. The segregation boundary was drawn incorrectly. ISP does not say
"split interfaces," it says split them along the axis that separates
distinct client usage patterns. Splitting along any other axis,
alphabetical, by data type, by which sprint the method was added in,
produces the same file count as a correct split without the actual
decoupling benefit.
Fix. Re-derive the boundaries from the actual clients. List every real
consumer of the type and the exact subset of methods each one calls. The
correct role interfaces are the distinct subsets that emerge from that
list, not an a priori taxonomy imposed on the methods.

Symptom. A class implements a role interface but its implementation throws
or returns a sentinel error for that role's method, the same forced-fake-
implementation smell ISP is supposed to eliminate, one level removed.
Cause. The role interface itself is still too wide for at least one of its
implementers, or the class in question should not implement that role
interface at all and callers should check capability at runtime instead,
a form of the interface-based feature detection idiom, sometimes
implemented via optional interfaces or type assertions.
Fix. Either split the role interface further along the boundary the
throwing implementer reveals, or remove that implementer's claim to
satisfy the role and have callers detect the capability explicitly, rather
than assuming every implementer of the role interface can honor every one
of its methods.

## 12. Trade-off matrix

| Force | Interface Segregation Principle | Single Responsibility Principle | Facade | Adapter |
|---|---|---|---|---|
| What it constrains | The consumer-facing contract, an interface, narrowed per client | The reason a unit of code changes, narrowed per concern | The set of subsystem calls a client must sequence, hidden behind one entry point | The shape of an existing type, translated to match a caller's expected shape |
| Primary force favored | Minimal client dependency on unused methods | Minimal reasons for a module to change | Simplicity of a complex subsystem's call surface for typical callers | Compatibility between an existing implementation and a required contract |
| Direction of the fix | Splits one interface into several narrow ones | Splits one class or module into several cohesive ones | Adds one new, simpler interface in front of many existing ones | Adds one new interface that wraps a single existing, mismatched one |
| Number of resulting types | Increases, several narrow interfaces replace one wide one | Increases, several small classes replace one large one | Increases by exactly one, the facade. Existing subsystem types are untouched | Increases by exactly one per mismatched type, the adapter |
| Typical trigger | A forced empty or throwing method implementation | A class changes for more than one unrelated business reason | Callers must learn and correctly sequence many subsystem calls to do one thing | An existing class's method names or signatures do not match what a caller's code expects |
| What stays coupled | Concrete implementers may still be coupled to several roles at once. Only clients are decoupled from unused roles | Only the responsibility is isolated. Classes can still share the same interface | Callers of the facade remain coupled to the facade, which is coupled to the whole subsystem | Callers remain coupled to the target interface. The adaptee's original interface is unchanged and still exists |
| Where it operates | At the interface or contract level, between client and implementer | At the class or module level, independent of interfaces | At the subsystem boundary, one level above the classes it wraps | At a single class's boundary, translating one interface to another |

## 13. Related and incompatible patterns

**Single Responsibility Principle.** These two are the pair most often
confused, and the distinction is worth stating precisely because getting it
wrong leads to misapplying one when the other is the actual fix. SRP is
about the reasons a unit of code changes. It says a class should have one
reason to change. ISP is about the shape of a contract as seen by its
clients. It says a client should not be forced to depend on methods it
does not use. A class can violate SRP while satisfying ISP perfectly.
Imagine a class with one narrow, well-focused public interface that
internally mixes two unrelated responsibilities in its private
implementation. Every client of it is fine, but the class itself has two
reasons to change. Conversely, an interface can violate ISP while every
implementer individually satisfies SRP perfectly. A class can have exactly
one responsibility and still be forced to implement a fat interface with
methods belonging to that one responsibility plus several others it does
not own. Applying ISP is a narrowing operation on the contract seen from
outside. Applying SRP is a splitting operation on the reasons a unit
changes from inside. They often travel together in practice because a
class with too many responsibilities tends to accumulate a fat interface
as a side effect, but they are answers to different questions.

**Dependency Inversion Principle.** DIP says high-level modules should
depend on abstractions, not on concrete low-level modules. ISP is the
principle that tells you how narrow those abstractions should be. A design
that follows DIP by depending on an abstraction, but where that
abstraction is a fat interface, has only half-solved the coupling problem.
The high-level module is decoupled from the concrete implementation, but is
still coupled to every method the abstraction exposes, whether it uses
them or not. ISP and DIP compose directly. DIP says depend on an
interface, ISP says make that interface as narrow as the actual dependency
requires.

**Open-Closed Principle.** OCP says a module should be open for extension
but closed for modification. A well segregated set of role interfaces
makes OCP easier to honor, because adding a new capability can mean adding
a new role interface and a new implementer of it, without modifying the
existing role interfaces or their existing implementers at all. A fat
interface makes OCP harder to honor for exactly the reason described in
dimension 7. Adding a capability to a fat interface means modifying the
shared interface, which forces every existing implementer to be touched.

**Facade.** Facade and ISP pull in opposite directions and are frequently
used together to serve different audiences of the same subsystem. Facade
widens the effective interface presented to a typical caller by hiding
several subsystem calls behind one simplified entry point. ISP narrows the
interface presented to a specific caller by excluding methods that caller
does not need. A well designed subsystem often has both, a facade for
callers who want the common, simple path, and several narrow role
interfaces underneath for callers with more specific needs who want to
bypass the facade and depend on exactly one capability. The two are not in
tension because they serve different callers. Using both is common, not
contradictory.

**Adapter.** Adapter translates one existing interface into another that a
caller expects. It is a compatibility fix for a shape mismatch that already
exists. ISP is a design decision made about a contract's own shape,
independent of any specific mismatch. They interact when the newly
segregated role interfaces do not match the shape of a legacy type that
needs to satisfy them, in which case an Adapter is the tool used to make
the legacy type satisfy the new, narrower interface without modifying the
legacy type itself.

**Strategy and Command.** Both patterns frequently converge on exactly the
single-method-interface end state that ISP, taken to its natural
conclusion, arrives at, per dimension 8. A `Strategy` interface with one
method and a `Command` interface with one `execute()` method are both, in
effect, maximally segregated interfaces. A client depending on a
`Strategy` depends on exactly the one algorithm-shaped capability it needs
and nothing else. This is not a coincidence. ISP explains why Strategy and
Command interfaces are conventionally kept to a single method rather than
accumulating related but distinct operations onto the same interface.

No incompatible patterns exist for ISP. It constrains the shape of a
contract and does not conflict structurally with any other pattern in this
catalog. Its only real tension is with the practice of applying it
prematurely, dimension 4 and 11, which is a misuse of the principle rather
than a conflicting pattern.

## 14. Refactoring path in and out

Introducing ISP into code that does not have it proceeds in these steps.

1. Identify the fat interface. Look for an interface or abstract class
   where at least one concrete implementer provides a stub, a no-op, or a
   thrown exception for one or more of its methods. This is the concrete,
   checkable signal to look for rather than a subjective sense that an
   interface "feels big."
2. For every real client of the fat interface, list the exact subset of
   methods that client actually calls. Do this from real call sites, not
   from imagining what a client might plausibly want. Grep or an IDE's
   find-usages applied per method is the mechanical way to build this list
   accurately.
3. Group clients whose method-subsets coincide, or nearly coincide, into
   candidate role groups. Each distinct group becomes a candidate role
   interface.
4. Extract each candidate role interface, moving only the relevant method
   signatures onto it. This step is the classic Extract Interface
   refactoring, and most IDEs, IntelliJ, Visual Studio, VS Code with the
   appropriate language server, offer it as an automated operation once
   the method subset is decided.
5. Change each concrete implementer to declare it implements the specific
   role interface or interfaces matching its real capabilities, and remove
   any stub, no-op, or throwing method that is no longer required because
   the class no longer claims to implement the wider interface.
6. Change each client's declared dependency type from the original fat
   interface to the narrowest role interface that covers the methods it
   actually calls, found in step 2.
7. Where several clients genuinely need the full combination of roles,
   introduce a composing interface, dimension 5 and 8, rather than forcing
   those clients to name every role individually.
8. Delete the original fat interface once no client and no implementer
   references it, or keep it, temporarily, as a deprecated composing
   interface if backward compatibility for external callers requires a
   transition period.

Removing ISP, or more precisely, recombining role interfaces that no
longer earn their split, proceeds in these steps.

1. Confirm the trigger from dimension 11's first failure mode. Every
   implementer of the role interfaces in question implements all of them,
   and no client has ever depended on fewer than the full set, across the
   interfaces' entire observed history.
2. Merge the role interfaces' method signatures back onto a single
   interface.
3. Update every implementer to declare the single merged interface instead
   of the several narrower ones.
4. Update every client's declared dependency type to the merged interface.
5. Delete the now-unused narrow interfaces.

This reversal is legitimate and should not be treated as an admission of
failure. A role split that never produced a second, differently-shaped
client was a reasonable bet that did not pay off, and un-splitting it
removes indirection that is no longer earning its cost, consistent with
the non-applicability guidance in dimension 4.

## 15. Testing and verification

ISP's effect on testing is almost entirely positive, and understanding why
clarifies the principle's real value better than any abstract argument.

Test doubles get smaller and more honest. A test double, a mock, a stub, a
fake, written against a role interface only has to implement the methods
that interface declares. A test double written against a fat interface has
to implement, or explicitly stub out with a "should never be called in
this test" assertion, every method of the fat interface, whether or not
the test exercises it. In a language that requires every interface member
to have a body, a fat interface directly inflates the size and the
maintenance burden of every test double written against it, and any change
to an unrelated part of the fat interface risks breaking test doubles that
never used that part.

Contract tests are easier to write and to keep correct. A contract test
suite, one that every implementer of an interface must pass to be
considered a valid implementer, is easier to write correctly against a
narrow, single-purpose interface, because the suite only has to assert
properties about the one capability the interface represents. A contract
test suite against a fat interface has to reason about several unrelated
capabilities at once, and it becomes easy to accidentally write assertions
that couple the correctness of one capability to the presence of another.

Interaction-based tests become more precise. When a client's declared
dependency is a narrow role interface, a test that verifies the client
interacts correctly with its dependency, a spy or a call-count assertion,
is automatically scoped to only the methods that interface declares, and
cannot accidentally assert on, or accidentally miss, calls to methods
outside that scope, because those methods are not visible through the
type the test is written against.

Verification of the split itself follows a simple check. When refactoring
toward ISP, dimension 14, the correctness of the split is verified by two
properties that should both hold before and after. Every existing client
still compiles or type-checks against its new, narrower dependency,
proving the split did not remove a method a client actually needed, and
every existing implementer's public method set is unchanged, proving the
split did not silently drop or rename behavior, only regroup its
declaration across interfaces. A test suite that exercises every client
through its concrete dependency, run before and after the refactor with
identical results, is the practical way to gain confidence in this.

## 16. Observability signals

ISP is a compile-time and design-time principle. It has no runtime
behavior of its own to trace or log, and so its observability is best
understood as signals visible in the codebase and in the build system
rather than in a running process.

A healthy signal is that a change to one role interface's method set
touches a proportionally small set of files. If your version control
history shows that commits changing one role interface consistently touch
only that interface's implementers and clients, and never ripple into
unrelated parts of the codebase, the segregation is doing its job. This is
directly measurable by looking at the file set of commits that modify a
given interface file, over time.

A second healthy signal, specific to compiled languages, is that build and
rebuild scope stays proportional to change scope. In a build system with
incremental compilation, most JVM and .NET build tools, and Bazel-style
build graphs generally, a well segregated interface produces a rebuild
graph where changing one role interface only forces rebuilds of its own
implementers and clients. A build-graph visualization or a build-time
profiler that shows a small, localized rebuild set after a role-interface
change is direct, measurable evidence the segregation is real rather than
cosmetic.

An unhealthy signal is the presence of any method body in the codebase
whose entire content is a thrown "not supported" exception, a comment
reading "N/A for this type," or a silent no-op that exists only to satisfy
an interface's compiler requirement. Every instance of this pattern is a
direct, greppable indicator that some interface in the codebase is wider
than at least one of its implementers, and is the single most reliable
static signal to search for when auditing a codebase for ISP violations.
Searching for `NotImplementedException`, `NotSupportedException`, or their
equivalents across a codebase, and then reading the surrounding class to
confirm the method really is structurally inapplicable rather than a
genuine bug, is a concrete, repeatable audit technique.

A second unhealthy signal is a role interface with exactly one implementer
and one caller, unchanged since it was introduced, sitting alongside
several other role interfaces in the same feature area with the same
shape. This is the observable trace of the over-segregation failure mode
from dimension 11. It shows up as a cluster of small interfaces in a
code-search or an architecture-visualization tool, each with a fan-in and
fan-out of exactly one, a pattern that legitimate role interfaces, which
typically accumulate a second implementer or a second caller over the
life of a system, tend not to exhibit.

## 17. Security and privacy implications

ISP's security implications are real but indirect, operating through the
principle of least privilege applied to code-level capability rather than
to data access directly.

Least privilege at the type level is the core mechanism. A client that
depends on a narrow role interface can, structurally, only call the
methods that interface exposes. It cannot accidentally or maliciously call
a method it was never given a reference to, because the type it holds does
not expose that method's signature. This is a real, if modest, capability-
security benefit. Segregating interfaces reduces the attack surface a
given piece of code can reach through its declared dependencies, in the
same spirit as capability-based security models, where possessing a
reference to a narrow object grants exactly the authority that object's
interface exposes, no more.

Reduced blast radius for a compromised or buggy client follows from the
same mechanism. If a client depends on `Readable` rather than on a fat
`Storage` interface that also exposes delete and write operations, a
defect or a compromise in that client's code cannot reach the delete or
write path at all, because the client's own type never names those
methods. This is directly analogous to, though weaker than, capability
confinement in an object-capability system. ISP applied deliberately with
security in mind is a lightweight way to get some of that benefit inside
an ordinary object-oriented codebase without adopting a full
capability-security architecture.

Auditing surface benefits similarly. A narrow interface makes it easier to
answer what a piece of code can do to the system, because the answer is
bounded by a short, named method list rather than by the entire surface of
a fat shared interface. This matters directly for code review and for
security audit, where a reviewer checking a new class that depends on
`ReadOnlyRepository` can conclude, from the type alone, that the class
cannot write or delete, without having to read the class's entire
implementation to confirm it never calls a mutation method it was never
given.

Where ISP is silent matters too. The principle says nothing about data
classification, encryption, authentication, or any runtime access-control
enforcement. A narrow interface restricts what a client's code can
syntactically call, not what data flows through the methods it does call,
or whether the underlying implementation itself enforces any
authorization check. A `Readable` interface with one `read()` method still
requires its own, separate, runtime authorization logic so the
caller is allowed to read the specific data being requested. ISP narrows
the compile-time capability surface, it does not substitute for runtime
access control.

## Code examples

Compiled or checked locally before this entry was written. TypeScript
checked with `tsc --strict --noEmit`, Python compiled with `py_compile`
(a local `mypy` install was not available to additionally strict-check the
`Protocol` usage, noted here rather than silently assumed), Go checked
with `go vet` and `go build`, Rust checked with `rustc --emit metadata`.
Java is omitted because no JDK was available in this environment to
compile against; the Java example in dimension 9, `Closeable` and
`Flushable`, is drawn directly from the cited standard library
documentation rather than from an uncompiled hand-written sample.

### TypeScript

```typescript
// Role interfaces narrowed to what each client actually calls.
interface Readable {
  read(): string;
}

interface Writable {
  write(data: string): void;
}

// A composing interface for clients that genuinely need both roles.
interface ReadWrite extends Readable, Writable {}

class FileHandle implements ReadWrite {
  private buffer = "";
  read(): string {
    return this.buffer;
  }
  write(data: string): void {
    this.buffer += data;
  }
}

// This client only reads. It depends on Readable, nothing else.
function summarize(source: Readable): string {
  return source.read();
}

// This client only writes. It cannot call read() even by accident,
// because the type it holds does not expose that method.
function appendLog(sink: Writable, entry: string): void {
  sink.write(entry + "\n");
}

const handle = new FileHandle();
appendLog(handle, "started");
const contents: string = summarize(handle);
```

### Python

```python
from typing import Protocol


class Readable(Protocol):
    def read(self) -> str: ...


class Writable(Protocol):
    def write(self, data: str) -> None: ...


class FileHandle:
    def __init__(self) -> None:
        self._buffer = ""

    def read(self) -> str:
        return self._buffer

    def write(self, data: str) -> None:
        self._buffer += data


def summarize(source: Readable) -> str:
    return source.read()


def append_log(sink: Writable, entry: str) -> None:
    sink.write(entry + "\n")


handle = FileHandle()
append_log(handle, "started")
contents = summarize(handle)
```

### Go

```go
package main

// A tiny local interface defined at the point of use, not by the
// producer of FileHandle. This is the idiomatic Go shape of ISP.
type Readable interface {
	Read() string
}

type Writable interface {
	Write(data string)
}

type FileHandle struct {
	buffer string
}

func (f *FileHandle) Read() string {
	return f.buffer
}

func (f *FileHandle) Write(data string) {
	f.buffer += data
}

// summarize only needs Readable. FileHandle satisfies it
// structurally, with no "implements" declaration required.
func summarize(source Readable) string {
	return source.Read()
}

func appendLog(sink Writable, entry string) {
	sink.Write(entry + "\n")
}

func main() {
	handle := &FileHandle{}
	appendLog(handle, "started")
	_ = summarize(handle)
}
```

### Rust

```rust
// Two narrow traits instead of one trait with every method.
trait Readable {
    fn read(&self) -> String;
}

trait Writable {
    fn write(&mut self, data: &str);
}

struct FileHandle {
    buffer: String,
}

impl Readable for FileHandle {
    fn read(&self) -> String {
        self.buffer.clone()
    }
}

impl Writable for FileHandle {
    fn write(&mut self, data: &str) {
        self.buffer.push_str(data);
    }
}

// This client only reads. Its bound is Readable, not the concrete type.
fn summarize(source: &impl Readable) -> String {
    source.read()
}

fn append_log(sink: &mut impl Writable, entry: &str) {
    sink.write(entry);
    sink.write("\n");
}

fn main() {
    let mut handle = FileHandle {
        buffer: String::new(),
    };
    append_log(&mut handle, "started");
    let _contents = summarize(&handle);
}
```

## 18. References

1. Wikipedia contributors, "Interface segregation principle," Wikipedia,
   verified 2026-08-02,
   https://en.wikipedia.org/wiki/Interface_segregation_principle. Used for
   the definition, the Xerox origin story, the SOLID summary, and the
   microservice-design extension.
2. Robert C. Martin, *Agile Software Development, Principles, Patterns, and
   Practices*, Prentice Hall, 2002. Original book-form statement of ISP as
   one chapter of the SOLID principles, cited per the Wikipedia summary
   above for publication details. Used for the general characterization of
   ISP's origin and its restatement from the earlier 1996 C++ Report
   article.
3. Go standard library documentation, package `io`, verified 2026-08-02,
   https://pkg.go.dev/io. Used for the exact method signatures of
   `io.Reader` and `io.Writer`, and for the composed interfaces
   `io.ReadWriter`, `io.ReadCloser`, `io.ReadWriteCloser`.
4. Rob Pike, "Go Proverbs," talk at Gopherfest, November 2015, transcript
   and slide list at https://go-proverbs.github.io/, verified 2026-08-02.
   Used for the proverb "the bigger the interface, the weaker the
   abstraction," cited as the Go-idiomatic restatement of ISP's underlying
   motivation.
5. Microsoft Learn, "IReadOnlyList<T> Interface (System.Collections.Generic),"
   verified 2026-08-02,
   https://learn.microsoft.com/en-us/dotnet/api/system.collections.generic.ireadonlylist-1.
   Used for the description and member set of `IReadOnlyList<T>`, and for
   the distinction from the mutable `IList<T>` interface it deliberately
   omits members from.
6. Oracle, "Interface Closeable," Java SE 21 API documentation, verified
   2026-08-02,
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/io/Closeable.html.
   Used for the single-method definition of `Closeable`, its relationship
   to `AutoCloseable`, and the deliberate separation from `Flushable`.

Book page numbers were not independently confirmed for Martin's 2002 book
because a physical or searchable copy was not available during
verification. The chapter-level attribution of ISP and its restatement of
the 1996 C++ Report article are corroborated by the Wikipedia summary
cited in reference 1, which itself cites the book directly. Where this
entry states a specific claim about the book's content beyond that
corroborated summary, it is labelled as drawn from the secondary
literature rather than confirmed against a page.
