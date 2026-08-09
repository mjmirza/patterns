---
name: Polymorphism
slug: polymorphism
family: 04-principles-and-laws
category: Principles and Laws
aliases: [Subtype Polymorphism, Parametric Polymorphism, Ad Hoc Polymorphism, Dynamic Dispatch, Late Binding]
first_described: "Christopher Strachey 1967, Cardelli and Wegner 1985"
maturity: canonical
related: [liskov-substitution-principle, open-closed-principle, strategy, template-method, visitor, bridge, dependency-inversion-principle, interface-segregation-principle]
incompatible_with: []
verified: 2026-08-09
---

# Polymorphism

## 1. Name, aliases, and lineage

The word polymorphism comes from Greek, poly meaning many and morphe meaning form. In
programming language theory it names the property that lets one piece of code, one name,
one call site, run different concrete behavior depending on the type of value it is
operating on. The three-way taxonomy that the field still uses today, parametric, ad hoc,
and inclusion polymorphism, was named and formalized by Christopher Strachey in his 1967
lecture notes "Fundamental Concepts in Programming Languages," written for the International
Summer School in Computer Programming in Copenhagen and later reprinted in *Higher-Order and
Symbolic Computation*, Volume 13, 2000, pages 11 to 49. Strachey coined parametric
polymorphism for a function that behaves uniformly across a range of types, such as a
generic length function over any list, and ad hoc polymorphism for a function that behaves
differently, sometimes unrelatedly, for each type it is defined on, such as overloaded
arithmetic operators.

The taxonomy was extended and given rigorous type-theoretic treatment by Luca Cardelli and
Peter Wegner in "On Understanding Types, Data Abstraction, and Polymorphism," published in
*ACM Computing Surveys*, Volume 17, Issue 4, December 1985, pages 471 to 523, DOI
10.1145/6041.6042 (verified 2026-08-09 via the ACM Digital Library listing at
https://dl.acm.org/doi/10.1145/6041.6042). Cardelli and Wegner split what Strachey had
called ad hoc polymorphism into two distinct mechanisms, overloading, where one name
denotes several unrelated implementations selected at compile time, and coercion, where a
value of one type is implicitly converted to another. They also introduced inclusion
polymorphism as the formal name for what the object-oriented community calls subtype
polymorphism, the property that a value of a subtype can appear wherever a value of its
supertype is expected, because the subtype's interface includes the supertype's interface.
This is the mechanism that underlies virtual method dispatch in Simula, Smalltalk, C++,
Java, and every mainstream object-oriented language since.

In everyday engineering conversation the word polymorphism, used without qualification,
almost always means subtype or inclusion polymorphism, the ability to call the same method
name on references of a common supertype or interface and have each concrete object respond
with its own implementation. That is the sense of the word this entry treats as primary,
because it is the sense that has design-pattern consequences, that composes with
inheritance and interfaces, and that every downstream pattern in this catalog, Strategy,
Template Method, Visitor, Bridge, Command, and the rest, is built out of. Parametric
polymorphism, known in Java and C# as generics, in C++ as templates, and in Haskell and ML
as the native default, is covered here as a contrasting mechanism in dimension 8, because
the two are frequently confused and the confusion causes real design mistakes, but its full
treatment as a type-system feature belongs to a language-reference source, not a pattern
catalog entry. Ad hoc polymorphism, overloading, is covered the same way, briefly, as a
boundary case.

The alias "dynamic dispatch" names the runtime mechanism, virtual method table lookup or
its equivalent, by which inclusion polymorphism is implemented. "Late binding" is an older
Smalltalk-era term for the same mechanism, contrasted with the early binding that a
statically resolved, non-virtual call uses. Both are mechanism names for the same
principle described from the runtime's point of view rather than the type system's point
of view, and this entry treats them as aliases of the inclusion-polymorphism sense.

## 2. Problem and context

A piece of client code needs to perform an operation, render a shape, calculate a price,
serialize a value, and it needs to do so uniformly over a collection of things that are not
all the same concrete kind. Without polymorphism the client is forced to write a branch,
usually a chain of if statements or a switch on a type tag, that enumerates every
concrete kind it currently knows about and calls the matching operation directly.

That branch is fine the day it is written. It becomes a liability the day a new kind is
added, because now every branch in the codebase that switches on the type tag has to be
found and extended, and the compiler gives no help finding them unless the language has an
exhaustiveness check on the tag itself. Robert C. Martin names this exact failure the
motivation for the Open Closed Principle in *Agile Software Development, Principles,
Patterns, and Practices*, Prentice Hall, 2002, chapter 9, arguing that a module should be
open for extension but closed for modification, and that type-switch code is the textbook
violation because adding a new case requires editing existing, already-tested code rather
than adding new code alongside it.

The context in which polymorphism earns its place is precisely this one, a fixed set of
operations applied across a growing or unknown set of concrete types, where the set of
operations is stable but the set of types is expected to change, or is not knowable at
compile time at all, plugins, drivers, request handlers, renderers. The context in which
polymorphism is the wrong tool is the mirror image, a fixed, small, unlikely to change set
of types with a growing set of operations, and dimension 4 below treats that case
explicitly, because it is the case most catalogs skip and the case where reaching for
polymorphism by habit produces worse code than the branch it replaced.

## 3. Forces

Coupling direction is the dominant force. A type-switch couples the client to every
concrete type by name, in one place, and that coupling is visible and searchable. A
polymorphic call couples the client to one interface, and the knowledge of which concrete
type will actually run moves out of the client and into whichever code constructs the
object, often far away. This is a real trade, not a pure win, because when a bug appears
that is specific to one concrete type, the type-switch version tells you exactly where to
look, while the polymorphic version requires you to trace an object's construction and
follow a vtable-style indirection to find the code that actually ran. Debuggers and IDEs
mitigate this with go-to-implementation tooling, but the cognitive cost is real, especially
for a reader unfamiliar with the codebase.

Extensibility versus enumerability is the second force. Polymorphism buys open extension,
a new subtype can be added without touching existing client code, at the cost of losing a
single place to enumerate every case. A type-switch gives you exhaustiveness, in a language
like Rust, Swift, or Kotlin with sealed or closed type hierarchies and pattern-match
exhaustiveness checking, the compiler will refuse to build if a new case is added and a
switch does not handle it. A pure open hierarchy with dynamic dispatch gives you no such
guarantee, a missing override silently falls back to a default or a base-class
implementation, or compiles fine and does the wrong thing at runtime, which is why sealed
hierarchies plus exhaustive pattern matching have become the preferred alternative to open
inheritance in several modern languages for exactly the case where the set of variants is
in fact closed and known, see dimension 12 below.

Performance is a real but frequently overstated force. Dynamic dispatch through a vtable or
an interface method table costs an extra pointer indirection per call compared to a direct,
statically resolved call, and it defeats inlining, because the compiler cannot see which
concrete method will run at the call site. On a hot inner loop executed billions of times
this genuinely matters and is a documented reason engine and driver code in game
development and low-latency trading systems avoids virtual calls on the hot path. On
ordinary application code calling a handler once per request or once per user action, the
cost is noise next to network, disk, and allocation costs, and choosing a branch over
polymorphism for performance reasons in that context is usually a premature optimization.

Team topology and cognitive load is the fourth force, less discussed but real. A
polymorphic interface with many implementations, spread across files or even across
packages owned by different teams, lets each team add a new implementation without asking
permission from the team that owns the interface, provided the interface's contract is
documented and stable. This is precisely the scenario the plugin architecture and the
strategy pattern exploit, and it is the reason large organizations favor interfaces at team
boundaries even when a closed switch would be simpler for a single team working alone.

## 4. Applicability and non-applicability

Reach for subtype polymorphism when the set of concrete types is open, plugins, drivers,
handlers registered by third parties or by other teams, and new kinds are expected to
appear after the code that calls them has shipped. Reach for it when the operations
performed are stable across the variation, render, execute, serialize, one small,
well-named interface, several implementations. Reach for it when different teams need to
add new behavior without modifying code they do not own, which is the Open Closed Principle
in Martin's own framing, *Agile Software Development, Principles, Patterns, and Practices*,
Prentice Hall, 2002, chapter 9. Reach for it when the alternative is a type-switch that
already appears more than once in the codebase for the same discrimination, because
duplicated switches on the same tag are the concrete, observable symptom that the
discrimination logic belongs behind an interface instead, a point Martin Fowler makes
directly under "Replace Conditional with Polymorphism" in *Refactoring, Improving the
Design of Existing Code*, 2nd edition, Addison-Wesley, 2018, chapter 10, motivating the
refactoring by exactly this duplication symptom.

Do not reach for it when the set of concrete types is closed and known, and unlikely to
grow, a currency code, an HTTP method, a card suit. For a closed set, a sum type or an
enum with an exhaustive pattern match gives you a compiler-enforced guarantee that every
case is handled, a guarantee that an open, polymorphic hierarchy cannot give you, because
new subtypes can always be added silently. This is the well-known expression problem
trade-off, articulated by Philip Wadler in his 1998 note "The Expression Problem"
(https://homepages.inf.ed.ac.uk/wadler/papers/expression/expression.txt, verified
2026-08-09), where Wadler states the problem as wanting to add both new data variants and
new operations without recompiling existing code and without unsafe casts, and shows that
the object-oriented, polymorphic solution makes adding a new variant easy and adding a new
operation hard, exactly the reverse of the functional, closed sum-type solution. Choosing
polymorphism for a closed, rarely-extended set trades away the exhaustiveness check for an
extensibility axis you will not use.

Do not reach for it when there is exactly one implementation and no second implementation
is planned. An interface with one implementer is speculative generality, a cost paid
today, an extra layer of indirection, an extra file, an extra name to look up, for a
benefit that has not materialized and may never materialize. Do not reach for it purely for
testability either, a common but weak justification, because a well-designed concrete class
with clear seams and dependency injection of its own collaborators is usually testable
without an interface, and the interface should be introduced when the second real
implementation appears, not preemptively. Do not reach for it inside a performance-critical
inner loop where the concrete type is in fact known and fixed at that call site, in that
narrow scope monomorphic, statically dispatched code will out-perform a polymorphic call and
the polymorphism is not buying any real extensibility locally.

## 5. Structure

The structure of subtype polymorphism has three participants, independent of which
language implements it.

The Client is the code that performs an operation without knowing, and without needing to
know, which concrete type it is operating on. It holds a reference or a value typed as the
Abstraction, never as a concrete type, and it calls the Abstraction's declared operations.

The Abstraction is the shared contract, an interface, an abstract class, a protocol, or a
trait, that declares the operations the Client depends on and nothing more. Its job is to
be the single stable name the Client couples to. The Interface Segregation Principle, see
the related entry, governs how narrow this contract should be, a fat abstraction with
operations most implementers do not need forces every new implementer to satisfy methods it
cannot meaningfully implement.

The Concrete Implementation, one or more, provides the actual behavior for the
Abstraction's operations for one specific kind of thing. Each Concrete Implementation is
substitutable for the Abstraction wherever the Abstraction is expected, which is precisely
the guarantee the Liskov Substitution Principle, see the related entry, requires the
language and the implementer to uphold, if it is violated the polymorphism is unsafe, a
Client written against the Abstraction's contract will break when handed a particular
Concrete Implementation.

A fourth, often implicit participant is the Binder, whatever mechanism decides at runtime
which Concrete Implementation's code actually executes for a given call, a virtual method
table lookup in C++ and Java, a dynamic method dispatch based on the object's class pointer
in Python and Ruby, an interface method table (itable) lookup in Go, or a vtable pointer
inside a fat pointer for a trait object in Rust. Dimension 6 diagrams this participant
explicitly because it is the mechanism that makes the whole structure work and it is where
the performance force from dimension 3 lives.

## 6. ASCII structure diagram

```
        Client                    Abstraction                Concrete
        (caller)                  (interface / protocol)     Implementations

  +----------------+          +----------------------+     +----------------+
  |  process(shape) |-------->|  interface Shape      |<----|  Circle        |
  |                  |  calls |    area(): number      |     |  area() { ... } |
  |  holds reference |        |    perimeter(): number |     +----------------+
  |  typed Shape     |        +----------------------+     +----------------+
  +------------------+                   ^                  |  Square        |
                                          | implements       |  area() { ... } |
                                          |                   +----------------+
                                          |                  +----------------+
                                          +------------------|  Triangle      |
                                                             |  area() { ... } |
                                                             +----------------+

  Binder (runtime dispatch mechanism, one per language runtime):

  C++ / Java   ->  vtable pointer inside the object header, indexed lookup
  Go           ->  interface value = (type descriptor, data pointer), itable lookup
  Rust dyn     ->  fat pointer = (data pointer, vtable pointer)
  Python/Ruby  ->  method resolution order (MRO) walk on the object's class
```

## 7. Dynamics

```
1. Client holds a reference typed as the Abstraction, e.g. `Shape s`.
2. At construction time, somewhere else in the program, a Concrete
   Implementation is created and assigned to that reference, e.g.
   `s = new Circle(radius)`. The Client's code that calls s.area()
   was compiled or interpreted without knowing this assignment exists.
3. Client calls `s.area()`. The call site names only the Abstraction's
   method signature.
4. The runtime Binder resolves the call:
     a. Static/vtable dispatch (C++, Java, C#): the object carries a
        hidden pointer to its class's vtable, populated at construction.
        The call becomes an indexed load from that table followed by an
        indirect jump. Resolved once per call, cost is one extra memory
        load plus one indirect branch.
     b. Structural/itable dispatch (Go): the interface value itself is a
        two-word pair, a pointer to a per-(concrete-type, interface)
        itable and a pointer to the underlying data. No inheritance
        relationship is declared anywhere; the itable is built the first
        time that (type, interface) pair is used.
     c. MRO dispatch (Python, Ruby, Smalltalk): the runtime walks the
        object's class and its ancestors, in method resolution order,
        looking for the first matching method name. Can be cached but is
        not a fixed-offset table lookup in the general case.
     d. Trait-object dispatch (Rust dyn Trait): the reference is a fat
        pointer of (data pointer, vtable pointer) built at the point the
        concrete value was coerced to `dyn Trait`. The call indexes the
        vtable, same shape as (a).
5. Circle's `area()` executes, computing pi * radius^2, and returns.
6. Client receives the result with no branch, no type check, and no
   knowledge that the concrete type was ever Circle rather than Square.
7. Weeks later, a new Concrete Implementation, Pentagon, is added
   implementing the same Abstraction. Step 4 handles it identically,
   because the Binder resolves by the object's actual runtime type at
   the moment of the call, not by anything the Client's source code
   enumerates. No line in the Client changes.
```

## 8. Implementation variants

Interface-based subtype polymorphism, the primary sense of this entry, is what Java's
`interface` keyword, C#'s `interface`, Go's implicit structural interfaces, Swift's
`protocol`, and Rust's `trait` objects (`dyn Trait`) all implement, each with a different
binding mechanism as shown in dimension 6, but the same Client, Abstraction, Concrete
Implementation shape.

Abstract-class-based inclusion polymorphism is the same shape but the Abstraction is a
partially implemented base class rather than a pure contract, common in C++ and older Java
codebases, and it is the mechanism the Template Method pattern is built on, where the base
class supplies the algorithm's fixed skeleton and delegates specific steps to subclass
overrides.

Structural typing, exemplified by Go's interfaces and by Python's duck typing, drops the
explicit `implements` declaration entirely. A type satisfies an interface by having the
right method signatures, with no coupling at the declaration site between the concrete type
and the interface it happens to satisfy. The Python glossary states this precisely, duck
typing is "a programming style which does not look at an object's type to determine if it
has the right interface; instead, the method or attribute is simply called or used," and
notes that it "avoids tests using type() or isinstance()," commonly using `hasattr()` or
exception-handling (EAFP) instead
(https://docs.python.org/3/glossary.html#term-duck-typing, verified 2026-08-09). This is
the loosest-coupled variant of inclusion polymorphism, the Concrete Implementation need not
even know the Abstraction exists.

Closure-based or first-class-function polymorphism replaces a one-method interface with a
plain function value passed as an argument, common in JavaScript, Go, Rust closures, and
modern Java via functional interfaces and lambdas. This is functionally the same
substitution property for the single-method case, and it is why the Strategy pattern is
frequently implemented as a function parameter rather than an interface hierarchy in
languages with first-class functions, a point made directly in the Strategy pattern's own
"Programming to an Interface, not an Implementation" discussion in Gamma, Helm, Johnson,
Vlissides, *Design Patterns, Elements of Reusable Object-Oriented Software*, Addison-Wesley,
1994, chapter 1.

Parametric polymorphism, generics in Java, C#, and Go, templates in C++, is a distinct
mechanism from inclusion polymorphism and is frequently confused with it. A generic
function like `identity<T>(x: T): T` behaves uniformly for every type T, it does not
dispatch to a different implementation per type, the same code runs regardless of what T
is. C++ templates are the outlier, they are resolved by monomorphization, the compiler
generates a separate, specialized copy of the function per instantiated type, which the
Rust Book describes for Rust's own generics as producing "static dispatch, which is when
the compiler knows what method you're calling at compile time," in explicit contrast to
`dyn Trait` objects which "must use dynamic dispatch" because "the compiler doesn't know
all the types that might be used with the code that's using trait objects"
(https://doc.rust-lang.org/book/ch18-02-trait-objects.html, verified 2026-08-09). Java and
Go generics, by contrast, are compiled once and either erase the type information at
compile time, Java, or use a shared implementation with dictionary-passing for interface
satisfaction, Go since 1.18, so their runtime cost profile differs from C++ and Rust
monomorphization. A codebase that needs the Strategy pattern's runtime substitutability, a
different behavior chosen at runtime based on data, needs inclusion polymorphism. A
codebase that needs the same algorithm to work uniformly over many types with zero runtime
branching needs parametric polymorphism instead. Reaching for the wrong one is a real and
common implementation mistake.

Operator and method overloading, ad hoc polymorphism in Strachey's original taxonomy,
resolves the specific implementation to call at compile time based on the static types of
the arguments, not at runtime based on an object's dynamic type. C++'s operator overloading
and Java's method overloading (as opposed to overriding) are both resolved this way, and
neither one is inclusion polymorphism, no vtable is consulted, the compiler picks the
overload during type checking. This entry treats overloading as a boundary case worth
naming precisely because engineers frequently call it polymorphism without distinguishing
it from the dynamic, subtype sense that carries the extensibility properties described in
dimension 3.

## 9. Known production uses

Go's standard library is built almost entirely on small, interfaces satisfied by shape rather than by name
using inclusion polymorphism without any explicit `implements` keyword. The `io.Writer`
interface, `type Writer interface { Write(p []byte) (n int, err error) }`, is satisfied by
`os.File`, `bytes.Buffer`, `net.Conn`, `gzip.Writer`, and hundreds of other concrete types
across the standard library and the wider set of third-party packages built on it, and
functions like `io.Copy`, `io.MultiWriter`, and `fmt.Fprintf` accept any of them
polymorphically because "any type that implements the `Write(p []byte) (n int, err error)`
method automatically satisfies the `io.Writer` interface, without needing to explicitly
declare it," per the Go standard library documentation
(https://pkg.go.dev/io#Writer, verified 2026-08-09). This is inclusion polymorphism via
structural typing at the scale of an entire standard library.

Rust's `Box<dyn Error>` and `dyn Trait` mechanism is the language's explicit, opt-in
inclusion polymorphism, used pervasively for error handling and plugin-style APIs where the
concrete error type varies by call site but the caller wants to handle any of them
uniformly through the shared `Error` trait. The Rust Book documents this trade-off directly,
`dyn Trait` gives you a heterogeneous collection through dynamic dispatch, at the cost that
"this lookup incurs a runtime cost that doesn't occur with static dispatch," while the
generic, trait-bound alternative is "monomorphized at compile time to use the concrete
types" and restricted to homogeneous collections
(https://doc.rust-lang.org/book/ch18-02-trait-objects.html, verified 2026-08-09).

The Java Virtual Machine implements inclusion polymorphism as a first-class bytecode
instruction, `invokevirtual`, specified in the *Java Virtual Machine Specification*, Java SE
21 edition, Chapter 6, section 6.5, at
https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-6.html#jvms-6.5.invokevirtual
(verified 2026-08-09, the locator resolves and the JVMS documents `invokevirtual` as the
instruction that selects and invokes a method based on the runtime class of the object
reference on the operand stack, the mechanism every Java `interface` and every non-final
method override in the language ultimately compiles to). This is inclusion polymorphism
implemented directly in the execution model of one of the most widely deployed managed
runtimes in production.

Python's iterator protocol is a duck-typed instance of inclusion polymorphism, any object
that defines `__iter__` and `__next__` participates in every `for` loop, list
comprehension, and `itertools` function in the language, with no shared base class
required, exactly matching the Python glossary's own description of duck typing as
emphasizing "interfaces rather than specific types" to allow "polymorphic substitution"
(https://docs.python.org/3/glossary.html#term-duck-typing, verified 2026-08-09).

## 10. Consequences

Positive. New behavior can be added by adding a new Concrete Implementation, with zero
edits to the Client's existing, already-tested code, the Open Closed Principle's central
promise, cited in dimension 3. The Client's code shrinks and stabilizes, because branching
logic that would otherwise grow with every new type instead lives distributed across the
implementations, each implementation only as large as its own case. Teams and third parties
can extend a system through its published interface without needing write access to, or
even knowledge of, the code that calls them, which is the mechanism every plugin
architecture, every dependency-injected service, and every driver-model API depends on.
Testing the Client in isolation becomes straightforward, a test double implementing the
Abstraction stands in for any real Concrete Implementation, with no need to instantiate
real, possibly expensive, dependencies.

Negative. The concrete behavior for a given call is no longer visible at the call site,
which is the coupling-direction trade named in dimension 3, a reader has to trace object
construction, dependency injection wiring, or a factory to know which implementation will
actually run, and this indirection compounds when several layers of polymorphic
substitution are stacked. The set of implementations is, by the nature of inclusion
polymorphism, not enumerable from the Abstraction alone, so exhaustiveness cannot be
checked by the compiler, a new implementation can silently fail to handle a case the
original design assumed every implementation would handle, unless the design also enforces
that contract through tests or an interface method with no default. Dynamic dispatch
carries a small but nonzero per-call cost, an indirect memory load and an indirect branch,
that a monomorphic call does not pay, and it defeats inlining at that call site, both
detailed in dimension 3 and documented for Rust specifically by the Rust Book's own
"runtime cost that doesn't occur with static dispatch" language cited above. An Abstraction
introduced before a second real implementation exists is a cost with no offsetting benefit,
the speculative-generality case named in dimension 4.

## 11. Failure modes and misuse

Symptom, a new implementation of an interface silently does the wrong thing for one method,
and the bug surfaces only for that concrete type, in production, long after the interface
was declared stable. Cause, the interface's contract was never made explicit beyond the
method signatures, no documented preconditions, postconditions, or invariants that a new
implementer is bound by, so the new implementer satisfied the compiler without satisfying
the actual behavioral contract the existing Clients depend on. Fix, document the contract
in terms Liskov and Wing formalized in "A Behavioral Notion of Subtyping," *ACM
Transactions on Programming Languages and Systems*, Volume 16, Issue 6, November 1994,
pages 1811 to 1841, preconditions no stronger than the supertype's, postconditions no
weaker, invariants preserved, and where the language supports it, encode the contract as a
shared test suite every implementation must pass, not merely as prose in a comment.

Symptom, a codebase has a deep inheritance hierarchy, five or six levels, and adding one
small new behavior requires touching three or four classes spread across that hierarchy to
get it right, with the change rippling in a direction nobody predicted. Cause, inclusion
polymorphism was used to model variation along an axis that inheritance cannot cleanly
express, an object varying along two independent dimensions at once, forcing a
combinatorial subclass explosion, shapes that are both filled or outlined and red or blue
producing FilledRedShape, OutlinedBlueShape, and so on. Fix, this is precisely the failure
mode the Bridge pattern exists to solve, see the related entry, decompose the two
independent axes into two separate, composed hierarchies instead of one combined one.

Symptom, every implementation of a wide interface throws `UnsupportedOperationException`,
returns a dummy value, or asserts false for two or three of its ten declared methods, and
new implementers routinely get this wrong because the pattern is so common nobody notices
it anymore. Cause, the Abstraction violates the Interface Segregation Principle, see the
related entry, it bundles operations that not every real implementer actually needs to
support, forcing every implementer to either fake compliance or degrade the interface's
promise. Fix, split the fat interface into several narrow ones, each implementer
implementing only the ones it can genuinely satisfy.

Symptom, a performance profile shows a hot loop spending measurable time in what looks like
trivial getter and setter calls, and the compiler's optimizer report shows the loop was not
inlined. Cause, the loop calls through an interface or a `dyn Trait` reference where the
concrete type is, in that specific call site, actually fixed and known at compile time, but
the code was written generically out of habit rather than necessity, paying the indirect
dispatch cost from dimension 10 for no real extensibility benefit at that site. Fix,
either use a generic, statically dispatched parameter, monomorphized at compile time, at
that hot call site, or, where the language supports it, mark the type `final` or `sealed`
and let the compiler devirtualize the call automatically once it can prove there is exactly
one implementer reachable.

Symptom, a large switch or if/else chain that discriminates on a type tag or a
`instanceof`/`isinstance` check appears in more than one place in the codebase, checking
the exact same set of concrete types every time, and each new concrete type requires
finding and editing every one of those scattered checks. Cause, the discrimination logic
that belongs behind a polymorphic interface was left as data-driven branching instead,
exactly the Open Closed Principle violation named in dimension 2 and the exact symptom
Martin Fowler names as the trigger for "Replace Conditional with Polymorphism" in
*Refactoring, Improving the Design of Existing Code*, 2nd edition, Addison-Wesley, 2018,
chapter 10. Fix, apply that refactoring, see dimension 14 below.

## 12. Trade-off matrix

| Force | Subtype polymorphism (this entry) | Type-switch / if-else chain | Sealed hierarchy plus exhaustive pattern match |
|---|---|---|---|
| Adding a new variant | No edit to existing client code, add one new implementation | Every switch on the tag must be found and edited | New variant added to the sealed set, every match site must be edited but the compiler forces it |
| Adding a new operation over all variants | Every implementation must be edited to add the method | One new function, one switch, done in one place | One new function, one match, done in one place |
| Compile-time exhaustiveness guarantee | None, a missing implementation of a required method is only caught if the interface has no default and the language enforces it at the declaration site | None in most languages, some linters can flag an incomplete switch | Yes, the compiler refuses to build on a missing case |
| Runtime dispatch cost | One indirect load plus one indirect branch per call, small in absolute terms but nonzero, negligible for I/O-bound code, measurable in a hot numeric loop | None, direct call after the branch resolves | None on a match expression that compiles to a jump table, similar in shape to the switch |
| Extension by a third party without editing shared code | Yes, this is its primary strength, cited to the Open Closed Principle in dimension 3 | No, the shared switch must be edited, which requires access to and understanding of code the third party does not own | No, the sealed set is closed by design, that closure is the whole point |
| Best fit | Open, unknown-in-advance set of variants, plugin and driver architectures, cross-team extension points | Small, one-off discrimination that will not recur and is not expected to grow | Closed, fully known set of variants where every operation needs to handle every case correctly, forever |

## 13. Related and incompatible patterns

The Liskov Substitution Principle, see the related entry, is the behavioral contract that
subtype polymorphism must uphold for the substitution in dimension 5's Client to be safe.
Polymorphism is the mechanism, LSP is the correctness condition on that mechanism, a
codebase can have polymorphism without LSP compliance, and when it does the polymorphism is
a latent bug generator rather than a design asset, exactly the first failure mode in
dimension 11.

The Open Closed Principle, see the related entry, is the design goal that subtype
polymorphism is the primary tool for achieving, cited throughout dimensions 2, 3, 4, and
10. Every discussion in this entry of adding a new implementation without editing existing
client code is a restatement, in the specific vocabulary of polymorphism, of what the Open
Closed Principle asks for in general.

The Interface Segregation Principle, see the related entry, governs the width of the
Abstraction from dimension 5, and its violation is the third failure mode in dimension 11.

The Strategy pattern is subtype polymorphism applied specifically to the case where the
varying thing is a single algorithm or policy, encapsulated as a one-method interface, and
substituted into a context object at construction or at call time. Strategy is inclusion
polymorphism scoped narrowly to one behavior; this entry is the general mechanism Strategy
is built from.

The Template Method pattern uses inclusion polymorphism in the opposite direction from
Strategy, the base class holds the shared algorithm skeleton and calls out to subclass
overrides for the variable steps, so the polymorphism runs from the base class downward
into the subclass rather than from a context object outward into an injected strategy.

The Visitor pattern is a case where polymorphism is deliberately doubled, dispatching first
on the concrete type of the element being visited and then on the concrete type of the
visitor, to work around the absence of true multiple dispatch in single-dispatch languages
like Java and C++, and it exists specifically because the single inclusion polymorphism
this entry describes is not, by itself, enough to solve the double-dispatch problem cleanly.

The Bridge pattern is the direct fix for the second failure mode in dimension 11, the
subclass explosion that happens when inclusion polymorphism is asked to model two
independent axes of variation inside one hierarchy; Bridge decomposes the hierarchy into
two, each varying along one axis, connected by composition rather than inheritance.

Parametric polymorphism, generics, is not incompatible with inclusion polymorphism, the two
frequently combine, a generic container `List<T>` where `T` is itself an interface using
inclusion polymorphism internally, but they solve different problems, as detailed in
dimension 8, and reaching for one where the design actually needs the other is a real,
recurring mistake rather than a matter of taste.

## 14. Refactoring path in and out

To introduce polymorphism into code that currently branches on a type tag, Martin Fowler's
"Replace Conditional with Polymorphism," in *Refactoring, Improving the Design of Existing
Code*, 2nd edition, Addison-Wesley, 2018, chapter 10, gives the mechanical steps. First,
for each leg of the conditional, identify or create a class that represents that case.
Second, if these classes do not yet share a common supertype, create one and move the
shared fields and the interface method signature up into it, or extract an interface if
inheritance is not appropriate. Third, one leg at a time, override the method in the
matching subclass with that leg's logic, and delete that leg from the original conditional.
Fourth, once every leg has been moved, the conditional itself is either empty and can be
deleted, or degenerates to a single polymorphic call, `element.operation()`, at the single
remaining call site. Fifth, repeat for every other place in the codebase that switches on
the same tag, each of those switches collapses to the same one polymorphic call, which is
the concrete signal that the refactoring was worth doing, duplicated logic across those
switches disappears rather than merely moving.

To remove polymorphism from a hierarchy that has become over-engineered for a set of
variants that turned out to be closed and stable, the reverse path is Fowler's "Replace
Type Code with Subclasses" run backward, collapse each Concrete Implementation's behavior
into a case inside a single function, using a switch or, in a language that supports it, an
exhaustive pattern match over a sealed enum, and delete the interface and its
implementations once every call site has been converted. This is the right direction when
dimension 4's non-applicability signals are present, the variant set has been stable for a
long time, no new implementer has appeared in years, and the codebase would benefit more
from the compiler's exhaustiveness check than from the extensibility the interface bought
and is not using.

## 15. Testing and verification

Testing the Client is what polymorphism is specifically good for. Write one or more test
doubles, a stub or a hand-written fake, that implement the Abstraction with controlled,
predictable behavior, and inject that double into the Client under test instead of a real
Concrete Implementation. Because the Client only ever calls through the Abstraction, the
test never needs to construct, configure, or clean up whatever expensive or side-effecting
resource a real implementation might depend on, a database connection, a network socket, an
external API. This is the single strongest practical argument for introducing an interface
at a boundary that talks to something slow or nondeterministic, even when the production
code has, and may only ever have, exactly one real implementation.

Testing each Concrete Implementation on its own is a second, separate concern, verify each
implementation's behavior directly, and additionally verify that every implementation
satisfies the same shared contract test suite, one written once against the Abstraction and
run against every Concrete Implementation in turn. This shared-contract-test technique is
the practical, everyday enforcement of Liskov substitutability from dimension 11's first
failure mode, if implementation B fails a test that implementation A passes and both claim
to satisfy the same interface, the interface's contract was ambiguous, underspecified, or B
genuinely violates it, and the shared suite catches this at test time rather than in
production.

A property specific to polymorphism that is easy to under-test is exhaustiveness of
dispatch itself, whether every registered or constructed Concrete Implementation is
actually reachable from every call site that is supposed to handle all of them. Where the
language offers no compiler-enforced exhaustiveness, per the trade-off in dimension 12, a
targeted test that constructs one instance of every known Concrete Implementation and
exercises the Client against all of them in one parametrized test run is the practical
substitute for the check the compiler cannot give you.

## 16. Observability signals

The concrete implementation actually invoked for a given operation is, by design, invisible
at the call site, which means it must be made visible on purpose in production telemetry
or the coupling-direction cost from dimension 10 becomes a debugging cost as well. The
practical fix is to tag every log line, trace span, and metric emitted from inside a
polymorphic call path with the concrete implementation's type name or a registered
identifier for it, for example a `strategy` or `implementation` field on the log entry or
span, so that when behavior differs between instances of the same logical operation, the
difference is queryable by concrete type without needing to attach a debugger.

A healthy polymorphic system shows a roughly stable, expected distribution of which
concrete implementation is invoked per operation over time, and a sudden shift in that
distribution, one implementation's call count dropping to zero, or an unexpected
implementation suddenly appearing, is itself a signal worth alerting on, because it usually
means either a configuration or registration change happened, on purpose or not, or a
factory or dependency-injection wiring bug is routing calls to the wrong implementation.

Per-implementation latency and error-rate metrics, broken out by the same type tag, surface
the case where one Concrete Implementation is systematically slower or less reliable than
its siblings while the aggregate metric for the shared operation looks fine, because the
aggregate is averaging across implementations with genuinely different performance
characteristics, a common mistake in metrics design that only becomes visible once you know
to break the metric out by the polymorphic dispatch target rather than only by the shared
operation name.

## 17. Security and privacy implications

Polymorphism itself carries no inherent data-handling behavior, this dimension is largely
judgement rather than a sourced claim here. Its security relevance is indirect and comes
from what the mechanism enables. An open, pluggable interface accepting third-party or
dynamically loaded Concrete Implementations is, by construction, an extension point, and
every extension point is a place where code outside the original trust boundary can run
with whatever privileges the Client's call site has. A polymorphic plugin API that loads
and instantiates implementations from user-supplied or network-supplied class names, module
paths, or configuration is functionally equivalent to a code-injection surface if that
input is not validated against an allowlist, because deserializing or reflectively
instantiating an attacker-chosen class name is a well-documented technique for arbitrary
object instantiation and, in languages where object construction can have side effects, for
arbitrary code execution.

A second, subtler implication follows from dimension 11's Liskov-violation failure mode
applied to a security-sensitive contract specifically, if an Abstraction's documented
contract includes a security property, an implementation must sanitize input, an
implementation must not log a secret field, and a new Concrete Implementation satisfies the
method signatures but silently fails to uphold that unstated or under-documented property,
the substitution the Client relies on is unsafe in a security sense even though it compiles
and passes ordinary functional tests. Where an interface carries a security-relevant
contract, that contract belongs in the shared test suite described in dimension 15, written
as an explicit, adversarial test case, not left as prose that a new implementer can miss.

## 18. References

- Christopher Strachey, "Fundamental Concepts in Programming Languages," lecture notes,
  International Summer School in Computer Programming, Copenhagen, 1967, reprinted in
  *Higher-Order and Symbolic Computation*, Volume 13, 2000, pages 11 to 49. Origin of the
  parametric, ad hoc, and inclusion polymorphism taxonomy.
- Luca Cardelli and Peter Wegner, "On Understanding Types, Data Abstraction, and
  Polymorphism," *ACM Computing Surveys*, Volume 17, Issue 4, December 1985, pages 471 to
  523, DOI 10.1145/6041.6042, https://dl.acm.org/doi/10.1145/6041.6042 (verified
  2026-08-09). Formalizes inclusion polymorphism and splits ad hoc polymorphism into
  overloading and coercion.
- Barbara Liskov, "Data Abstraction and Hierarchy," keynote address, OOPSLA 1987,
  published in *ACM SIGPLAN Notices*, Volume 23, Issue 5, May 1988, pages 17 to 34, DOI
  10.1145/62138.62141 (verified 2026-08-09). Origin of the substitutability requirement.
- Barbara Liskov and Jeannette M. Wing, "A Behavioral Notion of Subtyping," *ACM
  Transactions on Programming Languages and Systems*, Volume 16, Issue 6, November 1994,
  pages 1811 to 1841. Formal preconditions, postconditions, and invariants requirement for
  safe substitution.
- Robert C. Martin, *Agile Software Development, Principles, Patterns, and Practices*,
  Prentice Hall, 2002, chapter 9. Open Closed Principle, the design goal polymorphism
  serves.
- Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides, *Design Patterns, Elements of
  Reusable Object-Oriented Software*, Addison-Wesley, 1994, chapter 1, "Programming to an
  Interface, not an Implementation." Foundational statement of the design principle
  polymorphism implements mechanically.
- Martin Fowler, *Refactoring, Improving the Design of Existing Code*, 2nd edition,
  Addison-Wesley, 2018, chapter 10, "Replace Conditional with Polymorphism." Mechanical
  refactoring steps and the duplicated-switch symptom.
- Philip Wadler, "The Expression Problem," note, 1998,
  https://homepages.inf.ed.ac.uk/wadler/papers/expression/expression.txt (verified
  2026-08-09). Formal statement of the open-variants-versus-open-operations trade-off
  behind dimension 4's non-applicability guidance.
- Go standard library documentation, `io.Writer`, https://pkg.go.dev/io#Writer (verified
  2026-08-09). Structural, implicit inclusion polymorphism at standard-library scale.
- *The Rust Programming Language*, chapter 18.2, "Using Trait Objects That Allow for
  Values of Different Types," https://doc.rust-lang.org/book/ch18-02-trait-objects.html
  (verified 2026-08-09). Dynamic dispatch versus monomorphized static dispatch, runtime
  cost of trait objects.
- *The Java Virtual Machine Specification*, Java SE 21 edition, Chapter 6, section 6.5,
  `invokevirtual`,
  https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-6.html#jvms-6.5.invokevirtual
  (verified 2026-08-09). The bytecode instruction implementing inclusion polymorphism in
  the JVM.
- Python 3 documentation, Glossary, entry "duck-typing",
  https://docs.python.org/3/glossary.html#term-duck-typing (verified 2026-08-09). Canonical
  definition of shape-typed inclusion polymorphism used in dimensions 8 and 9.

## Code examples

The Client, Abstraction, and Concrete Implementation shape from dimensions 5 through 7,
implemented in three languages that each represent a distinct binding mechanism from
dimension 6, nominal vtable dispatch (TypeScript, compiled to a JavaScript prototype
chain), structural itable dispatch (Go), and duck-typed MRO dispatch (Python).

### TypeScript

```typescript
interface Shape {
  area(): number;
  perimeter(): number;
}

class Circle implements Shape {
  constructor(private radius: number) {}
  area(): number {
    return Math.PI * this.radius * this.radius;
  }
  perimeter(): number {
    return 2 * Math.PI * this.radius;
  }
}

class Square implements Shape {
  constructor(private side: number) {}
  area(): number {
    return this.side * this.side;
  }
  perimeter(): number {
    return 4 * this.side;
  }
}

// Client: knows only the Shape abstraction, never a concrete type.
function totalArea(shapes: Shape[]): number {
  return shapes.reduce((sum, s) => sum + s.area(), 0);
}

const shapes: Shape[] = [new Circle(2), new Square(3)];
console.log(totalArea(shapes).toFixed(4));
console.log(shapes.map((s) => s.perimeter().toFixed(4)));
```

### Go

```go
package main

import (
	"fmt"
	"math"
)

// Shape is satisfied by method shape alone: no "implements" keyword exists in Go.
type Shape interface {
	Area() float64
	Perimeter() float64
}

type Circle struct{ Radius float64 }

func (c Circle) Area() float64      { return math.Pi * c.Radius * c.Radius }
func (c Circle) Perimeter() float64 { return 2 * math.Pi * c.Radius }

type Square struct{ Side float64 }

func (s Square) Area() float64      { return s.Side * s.Side }
func (s Square) Perimeter() float64 { return 4 * s.Side }

// Client: knows only the Shape abstraction.
func totalArea(shapes []Shape) float64 {
	total := 0.0
	for _, s := range shapes {
		total += s.Area()
	}
	return total
}

func main() {
	shapes := []Shape{Circle{Radius: 2}, Square{Side: 3}}
	fmt.Printf("%.4f\n", totalArea(shapes))
	for _, s := range shapes {
		fmt.Printf("%.4f\n", s.Perimeter())
	}
}
```

### Python

```python
from abc import ABC, abstractmethod
import math


class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...

    @abstractmethod
    def perimeter(self) -> float: ...


class Circle(Shape):
    def __init__(self, radius: float) -> None:
        self.radius = radius

    def area(self) -> float:
        return math.pi * self.radius ** 2

    def perimeter(self) -> float:
        return 2 * math.pi * self.radius


class Square(Shape):
    def __init__(self, side: float) -> None:
        self.side = side

    def area(self) -> float:
        return self.side ** 2

    def perimeter(self) -> float:
        return 4 * self.side


def total_area(shapes: list[Shape]) -> float:
    return sum(s.area() for s in shapes)


if __name__ == "__main__":
    shapes: list[Shape] = [Circle(2), Square(3)]
    print(f"{total_area(shapes):.4f}")
    print([f"{s.perimeter():.4f}" for s in shapes])
```
