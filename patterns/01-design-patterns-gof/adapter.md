---
name: Adapter
slug: adapter
family: 01-design-patterns-gof
category: Structural
aliases: [Wrapper, Translator, Shim, Ports and Adapters (architectural use)]
first_described: "Gamma, Helm, Johnson, Vlissides 1994"
maturity: canonical
related: [facade, bridge, decorator, proxy, strategy, anti-corruption-layer]
incompatible_with: []
verified: 2026-08-02
---

# Adapter

## 1. Name, aliases, and lineage

The canonical name is Adapter. It sits in the Gang of Four catalog among the
seven structural patterns, in Erich Gamma, Richard Helm, Ralph Johnson and John
Vlissides, *Design Patterns. Elements of Reusable Object-Oriented Software*,
Addison-Wesley, 1994, chapter 4 (Structural Patterns), section Adapter, which
begins on page 139. The book states the intent as converting the interface of a
class into another interface that clients expect, so that classes which could
not otherwise work together because of incompatible interfaces are able to
collaborate. Alistair Cockburn quotes that intent word for word in his own
writing,
["Hexagonal Architecture"](https://alistair.cockburn.us/hexagonal-architecture/),
verified 2026-08-02, which gives an independently checkable copy of the sentence.

The book records **Wrapper** as the Also Known As name. That alias is a genuine
source of confusion, because Decorator carries the same alias in the same
chapter, and both patterns wrap. The
[Wikipedia article on the Adapter pattern](https://en.wikipedia.org/wiki/Adapter_pattern),
verified 2026-08-02, states the alias plainly and notes the collision, calling
it "an alternative naming shared with the decorator pattern". Dimension 13 does
the work of separating them, and a reader who takes only one thing from this
entry should take that table.

Two further names appear in real use and neither is a GoF term.

- **Translator.** Used in integration and messaging work for the same idea
  applied to data rather than to call signatures. A component that converts a
  payload from one schema to another is doing Adapter's job at the message
  level rather than at the method level.
- **Shim.** Used in platform and browser work for a thin layer that presents a
  newer or expected interface on top of an older or divergent implementation.
  The word carries an implication of temporariness that Adapter does not.

There is a separate, larger use of the word that deserves its own paragraph
because so many readers meet it first. **Ports and Adapters**, also called
Hexagonal Architecture, is an application architecture written by Alistair
Cockburn in 2005, HaT Technical Report 2005.02, and republished at
https://alistair.cockburn.us/hexagonal-architecture/, verified 2026-08-02. Its
stated intent is to allow an application to be driven equally by users,
programs, automated tests or batch scripts, and to be developed and tested in
isolation from its eventual runtime devices and databases. Cockburn is explicit
about the relationship to the GoF pattern. Under Related Patterns he writes that
"The ports-and-adapters pattern is a particular use of the Adapter pattern."
That single sentence is the whole answer to a question people argue about at
length. The architecture is not a different pattern with a coincidental name. It
is the object-level pattern applied as an organising principle for a whole
application boundary, where each port is an interface owned by the application
and each adapter is an object that translates between that port and one concrete
piece of outside technology. Dimension 13 returns to what changes when the
pattern is scaled up in this way.

The lineage worth stating is that Adapter is older than its catalog entry in the
way that most structural patterns are. Software has translated between
incompatible calling conventions since the first library was reused outside the
program it was written for. The 1994 book did not invent the technique. It named
it, separated it from the four other wrapping patterns it is confused with, and
distinguished the two structural forms described in dimension 8.

## 2. Problem and context

Two pieces of code need to work together and neither can be changed to match the
other. That is the whole problem, and every variation of it reduces to that
sentence.

The situation reads a particular way in a real codebase. There is a body of code
written against an interface that the team owns, or against an interface
supplied by a framework the team has committed to. There is a second body of
code, usually a library, a vendor SDK, a legacy module or a service client, that
does exactly the work needed. It has the right behaviour and the wrong shape.
Its method names differ. Its argument order differs. It returns an error code
where the caller expects an exception, or a callback where the caller expects a
future, or a mutable array where the caller expects an iterable sequence. The
capability is present. The signature is wrong.

Three constraints turn that annoyance into a design problem.

- **The adaptee cannot be edited.** It ships as a compiled artifact, it belongs
  to another team with its own release train, it is generated from a schema, or
  it is under a license that makes forking it a liability. Changing it to match
  is off the table, and pretending otherwise produces a fork nobody maintains.
- **The client cannot be edited either, or not cheaply.** The calling code is
  large, or it is a framework whose extension points are fixed, or there are
  many callers and only one adaptee, so changing the callers multiplies the
  work. In the framework case the client is code you never see, which makes the
  constraint absolute rather than economic.
- **The mismatch is at the interface, not in the behaviour.** This is the test
  that decides whether Adapter is the right pattern at all. If the second piece
  of code does the wrong thing, no amount of translation helps. Adapter is a
  translation of shape, not a repair of semantics, and reaching for it when the
  semantics differ produces the failure described in dimension 11 under leaky
  semantics.

The context in which Adapter is the right answer therefore has a specific
outline. The team owns, or has committed to, one interface. A useful
implementation exists behind a different interface. The behaviours line up
closely enough that a mechanical translation between the two is honest. Nobody
in the picture is willing or able to move.

Outside that outline the pattern is a liability rather than a solution, and
dimension 4 says where the boundary sits.

A concrete instance makes the shape stick. A reporting service is written
against an interface with one method that takes a list of rows and returns a
string. A vendor library that produces the exact output required exposes a class
whose entry point takes a two dimensional array of objects, writes to an output
stream supplied by the caller, and reports failure by returning a non zero
integer. Both do the same work. Neither can call the other. An adapter is a
small class that implements the reporting interface, holds the vendor object,
converts the list to the array, supplies a byte array stream, converts a non
zero return into the exception the service expects, and hands back the resulting
string. Ten lines of translation put an unmovable library behind a movable
interface, and every caller stays unaware that a vendor exists.

## 3. Forces

Adapter balances the following pressures, and it does sacrifice some of them.

- **Coupling.** Strongly favoured, and this is the reason to adopt the pattern.
  Client code depends on the target interface only. The adaptee's type name
  appears in exactly one file. Replacing the vendor becomes a change with a
  known blast radius rather than a change whose blast radius has to be measured
  by search.
- **Cognitive load.** Sacrificed, mildly but genuinely. A reader following a
  call now stops at a class whose only job is forwarding. The real work is one
  more hop away, and stack traces grow a frame that carries no meaning. On a
  codebase with many adapters the effect compounds into the wrapper fatigue
  described in dimension 11.
- **Latency.** Sacrificed in proportion to what the translation does. A pure
  forwarding call is free in any managed runtime after inlining. An adapter that
  copies a collection, allocates a buffer or serialises a payload on every call
  costs real time, and the cost is invisible at the call site because the call
  site sees the target interface only. This is the most commonly mispriced force
  in the pattern.
- **Memory and allocation.** Sacrificed when the translation copies. Object
  adapters that wrap without copying are close to free. Adapters that build a
  new collection per call turn an O(1) accessor into an O(n) one, and the
  pattern hides that from the reader.
- **Consistency.** Neutral to slightly sacrificed. The adapter presents a
  contract the adaptee never promised. Where the target contract says a method
  is idempotent and the adaptee makes no such promise, the adapter has silently
  taken on a guarantee it may not be able to keep.
- **Operability.** Favoured on balance. The adapter is a single, named place to
  put retries, timeouts, metrics, logging and circuit breaking around a
  dependency the team does not control. Teams that have no adapter end up
  scattering that machinery across every call site, or omitting it.
- **Cost.** Favoured over the alternatives that Adapter competes with. The
  pattern is cheap to write, cheap to delete, and needs no build system change,
  no code generation and no new dependency. Compared with forking the adaptee or
  rewriting the client it is close to free.
- **Team topology.** Strongly favoured. The adapter is a contract boundary
  between an application team and a platform, vendor or upstream team. It gives
  the application team a place to absorb an upstream change without a change
  landing in application logic, which turns a coordinated release into an
  uncoordinated one.
- **Testability.** Favoured. The target interface is a seam, so the client can
  be tested against a fake with no mocking framework at all. Dimension 15
  qualifies this, because the adapter itself is the one part of the arrangement
  that a fake cannot test.

The pattern gives up indirection and, when the translation is not free, runtime
cost. Anything described as costless has been described wrongly.

## 4. Applicability and non-applicability

Reach for Adapter when the following hold.

- An existing class does the work required and its interface does not match what
  the calling code expects.
- A reusable class must cooperate with classes that are unrelated or unforeseen,
  which is the second case the GoF applicability list names in the excerpt
  published at
  https://www.informit.com/articles/article.aspx?p=1398600&seqNum=2,
  verified 2026-08-02.
- Several existing subclasses need adapting and subclassing each one is not
  practical. The same excerpt names this as an object adapter only case, because
  the class adapter form commits to one adaptee class at compile time.
- A third party dependency needs a boundary so it can be swapped, mocked or
  version pinned without the change reaching business logic.
- A legacy module has to be consumed by new code written against a modern
  interface, and the legacy module is going to be retired later. The adapter
  becomes the seam at which the retirement happens.
- Test code needs to present a production interface over an in-memory
  implementation, which is the same pattern applied to a fake rather than to a
  vendor.

Do NOT reach for Adapter in these cases. This non-applicability list matters
more than the list above, because Adapter is easy to reach for and its overuse
is one of the most common structural smells in a large codebase.

- **The interfaces are already compatible.** A class that forwards every call
  unchanged, with identical names and identical types, is a pass through with a
  file of its own. It adds a stack frame, a test file and a reason for future
  readers to wonder what it does. Call the adaptee directly.
- **The semantics differ, not only the shape.** If the adaptee's method means
  something different from the target's method, translation produces a class
  that lies. An adaptee whose delete is a soft delete cannot honestly be adapted
  to a target whose delete promises removal. The correct move is to change the
  target interface so it can express the difference, or to refuse the adaptee.
- **You own both sides.** If both the client and the adaptee are yours and both
  are cheap to change, then changing one to match the other removes a class
  rather than adding one. The pattern exists for the case where changing is
  blocked, and adopting it when nothing is blocked is ceremony.
- **You want to simplify a large subsystem rather than translate one
  interface.** That is Facade. Adapter converts an interface into a specific
  other interface that a client already demands. Facade invents a smaller
  interface where none was demanded. Reaching for Adapter to describe a
  simplification produces a class with an invented target interface that has
  exactly one implementation, which is the tell.
- **You want to vary implementation and abstraction independently over time.**
  That is Bridge. Adapter is applied after the fact to interfaces that were
  designed without each other in mind. Bridge is designed up front so that two
  hierarchies can vary separately. The GoF Implementation section for Adapter
  makes the distinction on intent rather than on structure, since an object
  adapter and a Bridge look nearly identical in a class diagram.
- **You want to add behaviour while keeping the same interface.** That is
  Decorator. An adapter that implements the same interface as the thing it wraps
  and adds logging is a Decorator that has been named wrongly, and naming it
  wrongly costs the next reader real time.
- **You want to control access to an object without changing its interface.**
  That is Proxy. Lazy loading, remoting, access control and caching in front of
  an unchanged interface are Proxy responsibilities.
- **The adaptation is per call rather than per object, and the language has
  first-class functions.** In Go, TypeScript, Python, Rust and Kotlin a single
  function conversion is a function, not a class. Dimension 8 covers the
  function-valued form, and Go's own standard library uses it, see
  `http.HandlerFunc` in dimension 9.
- **The translation is expensive and happens on a hot path.** An adapter that
  copies a large collection on every call is a performance defect hidden behind
  a clean interface. Either make the adapter lazy, see the view-based variant in
  dimension 8, or accept the adaptee's interface on that path and translate at
  the edges only.
- **The mismatch is between whole bounded contexts rather than between two
  types.** A single adapter class is the wrong size. Eric Evans' Anti-Corruption
  Layer is the same instinct at a larger scale, with translation, a facade and a
  model of its own. See the domain-driven design family entry.

## 5. Structure

Four participants, named by role rather than by class name.

- **Target.** The interface the client is written against. In the object adapter
  form this is an interface or abstract type. It is owned by the client side of
  the boundary, which is the property that makes the whole arrangement work. If
  the target is owned by the adaptee's author, there is nothing to adapt.
- **Client.** Code written against Target. It never names Adaptee and never
  names Adapter. The client's ignorance of the adapter is the measurable outcome
  of the pattern, and a client that has to know which adapter it received has
  lost the benefit.
- **Adaptee.** The existing type with the useful behaviour and the wrong
  interface. It is normally third party, legacy or generated. It knows nothing
  about Target and must not be modified.
- **Adapter.** Implements Target and translates each Target operation into one
  or more Adaptee operations. It holds the Adaptee by composition in the object
  form, or inherits from it in the class form. It is the only type in the system
  that names both Target and Adaptee, and that fact is what bounds the blast
  radius of an upstream change.

Relationships. Client depends on Target. Adapter implements Target and depends
on Adaptee. Adaptee depends on nothing in this picture, which is what makes the
arrangement safe to apply to code you do not own. The dependency from the stable
side to the volatile side is inverted, which is the Dependency Inversion
Principle at work, see the principles family entry.

Two structural forms exist and the difference is not cosmetic.

The **object adapter** holds a reference to the adaptee and forwards to it. It
composes. One adapter class can accept any adaptee that satisfies the adaptee
type, including subclasses the adapter's author never saw. It can hold more than
one adaptee, adapt an adaptee supplied at runtime, or wrap a missing adaptee to
implement a null object.

The **class adapter** inherits from both the target and the adaptee. The GoF
text states that a class adapter uses multiple inheritance to adapt one
interface to another, while an object adapter relies on object composition, per
the excerpt at
https://www.informit.com/articles/article.aspx?p=1398600&seqNum=2, verified
2026-08-02. The form binds to one concrete adaptee class at compile time, gets
direct access to the adaptee's protected members, and needs no forwarding field.

The class adapter form is unavailable in several major languages, and this is a
language fact rather than a matter of style.

- **Java.** The Java Language Specification, Java SE 21, section 8.1.4, states
  that each class except `Object` is an extension of, that is a subclass of, a
  single existing class,
  https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html, verified
  2026-08-02. A Java adapter can extend the adaptee or extend the target when
  the target is a class, never both.
- **C#.** The Microsoft C# documentation states that a derived class can have
  only one direct base class, and that a class can implement multiple interfaces
  even though it can derive from only a single direct base class,
  https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/object-oriented/inheritance,
  verified 2026-08-02. Same constraint, same consequence.
- **Go.** Go has no type inheritance at all. The Go FAQ states that rather than
  requiring the programmer to declare ahead of time that two types are related,
  a type automatically satisfies any interface that specifies a subset of its
  methods, and that there are ways to embed types in other types to provide
  something analogous but not identical to subclassing,
  https://go.dev/doc/faq, verified 2026-08-02. Embedding forwards methods and
  looks superficially like the class form, but it is composition with automatic
  delegation, so the object adapter is the only real form in Go.

In all three the object adapter is the only available shape when the target is a
class rather than an interface, and it is the preferred shape even when both are
interfaces, because composition survives an adaptee that turns out to be final,
sealed or generated.

## 6. ASCII structure diagram

Object adapter, the composition form. This is the form available in every
language in the set.

```
  +----------------+           +-------------------------+
  |     Client     |  uses     |         Target          |
  |----------------|  ------>  |-------------------------|
  | + doWork()     |           | + request()             |
  +----------------+           +-------------------------+
                                            ^
                                            | implements
                                            |
                               +-------------------------+
                               |        Adapter          |
                               |-------------------------|
                               | - adaptee: Adaptee      |
                               | + request()             |
                               +-------------------------+
                                            |
                                            | holds a reference
                                            v
                               +-------------------------+
                               |        Adaptee          |
                               |-------------------------|
                               | + specificRequest()     |
                               +-------------------------+

  Adapter.request() calls adaptee.specificRequest() and converts.
  Adapter is the only box that names both Target and Adaptee.
```

Class adapter, the multiple inheritance form. Available in C++, Python, Eiffel
and other languages with multiple inheritance. Unavailable in Java, C# and Go
for the reasons cited in dimension 5.

```
  +----------------+           +-------------------------+
  |     Client     |  uses     |         Target          |
  |----------------|  ------>  |-------------------------|
  | + doWork()     |           | + request()             |
  +----------------+           +-------------------------+
                                            ^
                                            | inherits
                                            |
  +-------------------------+               |
  |        Adaptee          |               |
  |-------------------------|               |
  | + specificRequest()     |               |
  | # internalState         |               |
  +-------------------------+               |
              ^                             |
              | inherits                    |
              |                             |
              +--------+   +----------------+
                       |   |
               +-------------------------+
               |        Adapter          |
               |-------------------------|
               | + request()             |
               +-------------------------+

  Adapter.request() calls its own inherited specificRequest().
  No forwarding field. Direct access to protected internalState.
  Bound to exactly one concrete Adaptee at compile time.
```

Two-way adapter, which implements both interfaces so the same object is usable
on either side of the boundary.

```
        +--------------------+         +--------------------+
        |     Interface A    |         |     Interface B    |
        |--------------------|         |--------------------|
        | + aOperation()     |         | + bOperation()     |
        +--------------------+         +--------------------+
                   ^                              ^
                   |  implements                  |  implements
                   +--------------+---------------+
                                  |
                    +-----------------------------+
                    |     TwoWayAdapter           |
                    |-----------------------------|
                    | + aOperation()              |
                    | + bOperation()              |
                    +-----------------------------+
                        ^                     ^
                        |                     |
                 Client written         Client written
                 against A sees          against B sees
                 an A                    a B
```

## 7. Dynamics

The runtime flow is short, and its one interesting property is that the client
never learns that an adapter took part. Every diagnostic consequence in
dimension 16 follows from that.

```
Client              Adapter                 Adaptee
  |                    |                       |
  |-- request(x) ----->|                       |
  |                    |                       |
  |                    | convert x to y        |
  |                    | (map names, reorder,  |
  |                    |  copy, widen types)   |
  |                    |                       |
  |                    |-- specificRequest(y) ->|
  |                    |                       |
  |                    |        does the work  |
  |                    |<-- result r ----------|
  |                    |                       |
  |                    | convert r to s        |
  |                    | (error code to        |
  |                    |  exception, array to  |
  |                    |  list, empty to none) |
  |                    |                       |
  |<-- s --------------|                       |
  |                    |                       |
```

Three timing notes that matter in production.

**Error translation is a second flow, not a footnote.** When the adaptee reports
failure by a return code and the target reports failure by an exception, the
adapter carries the whole conversion. Where the adaptee's failure taxonomy is
coarser than the target's, information is lost at this step and cannot be
recovered downstream. Where it is finer, the adapter has to choose, and the
choice should be written down rather than implied by the code.

```
Client              Adapter                 Adaptee
  |                    |                       |
  |-- request(x) ----->|                       |
  |                    |-- specificRequest(y) ->|
  |                    |<-- code = -7 ----------|
  |                    |                       |
  |                    | look up -7            |
  |                    | -> NotFound           |
  |                    |                       |
  |<-- throws NotFound-|                       |
  |                    |                       |
```

**Lifecycle ownership is decided at construction and is easy to get wrong.**
When the adaptee holds a resource, the adapter has to state whether it owns that
resource. An adapter that closes an adaptee it did not create breaks a caller
that is still using it. An adapter that fails to close an adaptee it did create
leaks. The rule that survives review is that whoever constructs the adaptee
closes it, and an adapter that constructs its own adaptee implements the
language's disposal interface and closes it.

**Statefulness changes the picture entirely.** A stateless adapter is safe to
share across threads if the adaptee is. An adapter that buffers, batches or
caches has state of its own, and the target interface says nothing about that,
so the client cannot know. Every concurrency defect described in dimension 11
originates here.

## 8. Implementation variants

**Object adapter, single adaptee.** The default and the one to reach for first.
The adapter holds the adaptee in a field supplied by its constructor. Works in
every language in the set. Handles adaptee subclasses for free, since the field
is typed against the adaptee's own abstraction where one exists.

**Class adapter, multiple inheritance.** The adapter inherits both target and
adaptee. Fewer objects, no forwarding, and access to the adaptee's protected
members, which is occasionally the only way to reach behaviour the adaptee did
not make public. The costs are heavy. It binds to one concrete adaptee, it
cannot adapt an adaptee chosen at runtime, it inherits the whole adaptee
interface including members the target does not want, and it is impossible in
Java, C# and Go, per dimension 5. Use it in C++ or Python only when the
protected-member access is what makes the adaptation possible at all.

**Two-way adapter.** The adapter implements both interfaces, so the same object
can be handed to a client expecting either. The GoF Implementation section names
this under the heading of transparency and states that two-way adapters can
provide such transparency when two different clients need to view an object
differently, per the excerpt at
https://www.informit.com/articles/article.aspx?p=1398600&seqNum=2, verified
2026-08-02. The problem it solves is real. A one-way adapter is not transparent,
because the adapted object no longer conforms to the adaptee's interface and so
cannot be passed where an adaptee is expected. The GoF example is the
integration of Unidraw, a graphical editor framework, with QOCA, a constraint
solving toolkit, where each system has its own variable type and each has to be
usable as the other. The cost is that the adapter now has two contracts to
honour and two sets of invariants to keep in step, and that in a single
inheritance language it can implement both only when both are interfaces. Treat
it as the exception. Most boundaries flow in one direction, and a two-way
adapter adopted speculatively doubles the exposed area for no gain.

**Pluggable adapter.** The GoF Implementation section describes making a class
more reusable by minimising the assumptions other classes must make to use it,
and names three techniques for building an adapter whose adaptation is supplied
rather than hardcoded. Using abstract operations, where the adapter declares the
narrow operations it needs and a subclass binds them to a specific adaptee.
Using delegate objects, where the adapter forwards to a delegate that the client
sets, which moves the choice from compile time to runtime. Parameterised
adapters, where the adaptation is supplied as functions or blocks rather than as
a type. The third technique is what a modern language expresses as a lambda, and
it is the most widely used of the three today.

**Function-valued adapter.** In a language with first-class functions the
adaptation for a single-method interface is a function, and no class is needed.
Go's standard library uses this form explicitly. The `net/http` documentation
states that `HandlerFunc` is an adapter to allow ordinary functions to be used
as HTTP handlers, and that if `f` is a function with the appropriate signature,
`HandlerFunc(f)` is a `Handler` that calls `f`,
https://pkg.go.dev/net/http#HandlerFunc, verified 2026-08-02. Prefer this shape
whenever the target has one method. It removes a file, a test and a stack frame.

**Lazy or view-based adapter.** Rather than copying the adaptee's data into the
target's shape, the adapter presents a view over the adaptee and translates on
access. `java.util.Arrays.asList` is the canonical example, see dimension 9. The
gain is that an O(n) copy becomes O(1) construction. The cost is aliasing.
Changes on either side are visible on the other, which is correct behaviour for
a view and a defect for anybody who read it as a copy. Document which one it is
in the adapter's name where the language allows, `asList` versus `toList` being
the convention that Java settled on.

**Streaming adapter.** When the adaptee produces or consumes a stream, the
adapter wraps rather than buffers, and preserves back pressure. Go's `io`
package is built from these. `io.LimitReader` returns a reader that reads from
an underlying reader and stops with EOF after n bytes. `io.MultiReader` returns
a reader that is the logical concatenation of its inputs, read sequentially.
`io.TeeReader` returns a reader that writes to a writer what it reads from a
reader, with no internal buffering, so the write completes before the read does.
`io.NopCloser` returns a `ReadCloser` with a no-op `Close` method wrapping the
provided reader, which is an adapter that adds one method the adaptee lacks. All
four from https://pkg.go.dev/io, verified 2026-08-02.

**Interface segregation before adaptation.** Where the adaptee is large and the
client needs three of its forty methods, define the target as those three
methods rather than as a mirror of the adaptee. This is the single change that
most improves an adapter, because it turns a forty-method translation problem
into a three-method one and makes the test double trivial. See the principles
family entry on the Interface Segregation Principle.

**Generated adapter.** Where the adaptee is defined by a schema, an IDL or an
OpenAPI document, the adapter can be generated. The gain is that an upstream
schema change produces a compile error rather than a runtime one. The cost is a
build step, and the habit of regenerating rather than reading, which hides the
semantic mismatches that generation cannot detect.

**Language note on Rust.** Rust has no inheritance, so only the composition form
exists. The idiomatic shape is a newtype struct holding the adaptee and an
`impl` of the target trait for that struct. The orphan rule makes this more than
a stylistic choice. When both the target trait and the adaptee type come from
other crates, a newtype wrapper is the only legal way to implement one for the
other, so Rust turns the object adapter from a preference into a requirement.

**Language note on Python.** Python has multiple inheritance, so the class
adapter form is genuinely available. It is still normally the wrong choice,
because the method resolution order makes name collisions between target and
adaptee resolve silently rather than loudly. Duck typing also removes the need
for a declared target much of the time, which reduces the pattern to a plain
wrapper class with the methods the caller happens to invoke.

## 9. Known production uses

**Java, `java.util.Arrays.asList`.** The method signature is
`static <T> List<T> asList(T... a)` and the specification describes it as
returning a fixed-size list backed by the specified array. It adapts an array,
which is a language primitive with its own access syntax, to the `List`
interface that the Collections Framework is written against, and it does so as a
view rather than a copy, which is why the returned list is fixed-size and why
writes through it reach the array. Oracle, Java SE 21 API Specification,
`java.util.Arrays`,
https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Arrays.html,
verified 2026-08-02.

**Java, `java.io.InputStreamReader`.** The class documentation states that an
`InputStreamReader` is a bridge from byte streams to character streams, that it
reads bytes and turns them into characters using a specified charset. It is an
object adapter in the strict sense. The adaptee is an `InputStream` supplied to
the constructor, the target is `Reader`, and the translation is character set
conversion. The documentation's own use of the word bridge is a naming accident
rather than a claim about the Bridge pattern, which dimension 13 separates.
Oracle, Java SE 21 API Specification, `java.io.InputStreamReader`,
https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/io/InputStreamReader.html,
verified 2026-08-02.

**Go, `net/http.HandlerFunc`.** The documentation calls it an adapter in its own
words, saying that `HandlerFunc` is an adapter to allow ordinary functions to be
used as HTTP handlers, and that `ServeHTTP` calls `f(w, r)`. The adaptee is a
function value, the target is the `Handler` interface, and the adapter is a
named function type with one method. This is the function-valued variant of
dimension 8 shipping in a standard library, and it is worth studying because it
costs one type declaration and one method. Go project, `net/http` package
documentation, https://pkg.go.dev/net/http#HandlerFunc, verified 2026-08-02.

**Go, the `io` package adapter set.** `io.NopCloser` wraps a `Reader` and
returns a `ReadCloser` with a no-op `Close`, and the documentation adds that if
the wrapped reader implements `WriterTo` then the returned value implements
`WriterTo` by forwarding to it, which is an adapter preserving an optional
capability of its adaptee. `io.LimitReader`, `io.MultiReader` and `io.TeeReader`
are further adapters over the same interface. Go project, `io` package
documentation, https://pkg.go.dev/io, verified 2026-08-02.

**.NET, `System.Data.Common.DbDataAdapter` and the ADO.NET provider adapters.**
The type is documented as helping a class implement a `DataAdapter` designed for
use with a relational database, and its concrete subclasses are named in the
documentation as `SqlDataAdapter`, `OleDbDataAdapter`, `OdbcDataAdapter` and
`OracleDataAdapter`. The adaptee is a provider specific command and connection
pair. The target is the in-memory `DataSet` and `DataTable` model. The
translation is performed by `Fill`, documented as adding or refreshing rows in
the `DataSet` to match those in the data source, and by `Update`, documented as
updating values in the database by executing the respective INSERT, UPDATE or
DELETE statements for each inserted, updated or deleted row. Microsoft, .NET API
documentation, `System.Data.Common.DbDataAdapter`,
https://learn.microsoft.com/en-us/dotnet/api/system.data.common.dbdataadapter,
verified 2026-08-02.

**Android, `RecyclerView.Adapter`.** The Android documentation states that the
`RecyclerView` requests views and binds the views to their data by calling
methods in the adapter, and that the adapter is defined by extending
`RecyclerView.Adapter`. The adaptee is an application's own data collection,
whose shape the framework cannot know. The target is the three-method contract
the framework calls, `onCreateViewHolder`, documented as being called whenever
the `RecyclerView` needs to create a new `ViewHolder`, `onBindViewHolder`,
documented as associating a `ViewHolder` with data, and `getItemCount`,
documented as returning the size of the dataset. This is the framework case from
dimension 2 in its purest form, since the client here is code the application
author never sees. Google, Android developer documentation, "Create dynamic
lists with RecyclerView",
https://developer.android.com/develop/ui/views/layout/recyclerview,
verified 2026-08-02.

## 10. Consequences

Positive.

- The client and the adaptee are decoupled without either being modified, which
  is the only outcome available when both are outside the team's control.
- The adaptee's type name appears in one file, so replacing a vendor, upgrading
  a major version or switching a transport becomes a bounded change.
- The target interface becomes a test seam, so the client is testable against an
  in-memory fake with no mocking framework and no network.
- Cross cutting concerns around an untrusted dependency have one obvious home.
  Retries, timeouts, rate limits, metrics and redaction go in the adapter rather
  than being sprinkled across call sites.
- One adapter can serve many adaptee subclasses in the object form, so the class
  count does not grow with the adaptee hierarchy.
- The adapter is a written record of a semantic mismatch. The conversion code is
  documentation that stays true, because it runs.
- Deletion is cheap. When the adaptee is retired, one file goes and the compiler
  finds the construction sites.

Negative.

- One more type, one more file, one more test, one more stack frame per
  boundary. On a codebase with hundreds of dependencies this is the larger cost,
  not the runtime one.
- The translation can be expensive and the cost is invisible from the target
  interface, so an O(n) copy hides behind a method that reads as an accessor.
- The adapter can only present what the adaptee offers. Where the target
  interface promises more, the adapter has to fake it, and faking a guarantee is
  the source of the worst failures in dimension 11.
- Debugging crosses an extra boundary. A stack trace shows the adapter frame
  rather than the reason, and an exception thrown by the adaptee may arrive
  wrapped and stripped of its cause when the translation is careless.
- Two-way and pluggable variants add real complexity, and both are frequently
  adopted before they are needed.
- Adapters accumulate. The pattern is easy to add and nobody is ever assigned
  the work of removing one, so a codebase drifts toward chains of wrappers where
  each layer was individually reasonable.

## 11. Failure modes and misuse

**The pass-through adapter.** Symptom. A class whose every method forwards a
call of the same name with the same arguments to a field, and a test file that
asserts exactly that. Cause. An adapter added for a swap that never came, or
added by convention because the team adapts everything. Fix. Delete it and call
the adaptee. If the swap is genuinely coming, keep it and write down when the
decision will be revisited.

**Leaky semantics.** Symptom. Behaviour that is correct in staging against the
fake and wrong in production against the real adaptee. The classic instance is a
target interface promising that a write is durable when it returns, adapted onto
a client that acknowledges on buffer rather than on commit. Cause. The adapter
translated the shape and assumed the meaning. Fix. Write the target contract
down as executable tests, run those tests against the adapter with the real
adaptee, and change the target interface where the adaptee cannot honour it.

**The copying adapter on a hot path.** Symptom. A profiler shows most time in
array copying inside a method that reads like a getter, or heap allocation
climbs in proportion to request rate. Cause. The adapter materialises a
collection per call because that was the simplest translation to write. Fix.
Return a lazy view in the style of `Arrays.asList`, or hoist the conversion out
of the loop, or accept the adaptee's type on that path and adapt at the edges.

**Swallowed causes in error translation.** Symptom. A production alert with a
generic message and no way to tell which of six upstream conditions produced it,
and a stack trace whose deepest frame is the adapter. Cause. The adapter caught
the adaptee's exception and threw a new one without setting the cause, or mapped
several distinct codes onto one. Fix. Always chain the cause. Map codes onto a
target taxonomy rich enough to distinguish the ones that lead to different
operator actions, and put the raw code in the message.

**Ownership confusion over a resource.** Symptom. Either a closed connection
being used by another caller, or a file descriptor leak that grows with request
count. Cause. Ambiguity about whether the adapter owns the adaptee. Fix. State
the rule in the constructor. An adapter given an adaptee does not close it. An
adapter that constructs its own adaptee closes it and implements the language's
disposal interface.

**Hidden state in a shared adapter.** Symptom. Intermittent wrong results under
load that never reproduce in a single-threaded test, or a cache serving one
tenant's data to another. Cause. An adapter that added buffering, batching or
memoisation, and was then registered as a singleton because the target interface
gave no hint that it had state. Fix. Make the adapter stateless, or make its
lifecycle explicit and document the thread-safety of every method it presents.

**Wrapper fatigue.** Symptom. A call passes through four objects, each named for
what it wraps, before reaching code that does anything, and new joiners cannot
find where work happens. Cause. Each layer was added by a different person for a
locally sound reason. Fix. Collapse the chain. Two adapters in sequence, one
converting A to B and one converting B to C, are one adapter converting A to C
whenever B has no other client.

**Adapter used where the target has one implementation.** Symptom. An interface
with a single implementing class, both written on the same day, and the
interface never mentioned in a test. Cause. Adapter applied as a habit rather
than to solve a mismatch. Fix. Inline the interface. See the refactoring family
entry on Collapse Hierarchy.

**Class adapter attempted in a single-inheritance language.** Symptom. A
compiler error on a second `extends` clause, followed by a redesign that makes
the adaptee an interface it was never meant to be. Cause. A design copied from a
C++ example. Fix. Use the object form, per the language citations in
dimension 5.

**Adapting a broken abstraction upward.** Symptom. The target interface grows
methods that exist only because one adaptee needs them, such as a `flush` that
is a no-op for three of four implementations. Cause. The target was derived from
the adaptee instead of from the client's needs. Fix. Re-derive the target from
what the client calls, and let the adapter absorb the difference. This is
Interface Segregation applied as a repair.

## 12. Trade-off matrix

Compared against named alternatives across the forces from dimension 3. The
alternatives are the moves a team actually considers at this decision point.

| Force | Adapter (object form) | Adapter (class form) | Fork and modify the adaptee | Rewrite the client to the adaptee's interface | Facade | Anti-Corruption Layer (Evans) |
|---|---|---|---|---|---|---|
| Coupling to the foreign type | Low. One file names it | Low, but the adapter is that type | High. The fork is now yours forever | Highest. Every call site names it | Low, but the target was invented not demanded | Lowest. A whole model separates the contexts |
| Cost to adopt | Low. One class, one test | Low where the language allows it | High. Build, patch and merge cost per upstream release | High and proportional to the number of call sites | Low | High. A subsystem, not a class |
| Cost of an upstream breaking change | One file changes | One file changes, and the inheritance may break | Merge conflicts on every upstream release | Every call site changes | One file changes | Contained in the translation layer |
| Latency added | One call, plus the translation | One call, no forwarding hop | None | None | One call | Several calls, often a process boundary |
| Allocation added | Zero when it wraps, O(n) when it copies | Zero. No wrapper object | None | None | Usually zero | Frequently a full object graph |
| Runtime adaptee selection | Supported | Not supported. Bound at compile time | Not applicable | Not applicable | Supported | Supported |
| Works in Java, C#, Go | Yes | No. Single inheritance or none | Yes | Yes | Yes | Yes |
| Access to adaptee protected members | No | Yes | Yes | No | No | No |
| Testability of the client | High. Target is a seam | High | Low. The fork must be run | Low. No seam exists | High | High |
| Team topology fit | Good. A boundary a team owns | Good, with a compile time coupling | Poor. Creates a maintenance obligation | Poor. Spreads the dependency | Good | Good for two teams with different models |
| Fit when semantics also differ | Poor. Translation cannot repair meaning | Poor, same reason | Fair. You can change behaviour | Fair. The client adopts the real semantics | Poor | Strong. That is its purpose |

Reading of the table. The object adapter wins whenever the mismatch is confined
to interface shape and both sides are stable. The class adapter wins only in a
multiple inheritance language when protected access is what makes the
adaptation possible. Forking wins when the adaptee is actually wrong and the
upstream will not fix it, and it should be entered with the maintenance cost
stated out loud. Rewriting the client wins when there are few call sites and the
adaptee's interface is honestly better. Facade wins when the goal is
simplification rather than conformance. An Anti-Corruption Layer wins when the
mismatch is between models rather than between methods, and a single class would
be the wrong size for the problem.

## 13. Related and incompatible patterns

Five patterns wrap another object. They are confused constantly, and the
confusion is understandable because their class diagrams are nearly identical.
The difference is intent, and intent is visible in two questions. Does the
wrapper present the same interface as the thing it wraps? Was the wrapper
designed before the two sides existed, or applied afterwards?

| Pattern | Interface presented | Same interface as the wrapped object? | Primary intent | Designed up front or applied later? | Typical give-away in code |
|---|---|---|---|---|---|
| Adapter | Target, demanded by an existing client | No. Deliberately different | Make incompatible interfaces work together | Applied later, to code you do not own | One class names both a foreign type and a local interface |
| Facade | A new, smaller interface nobody demanded | No. It is invented | Simplify access to a subsystem | Applied later, over code you often do own | One class calls many collaborators, and its interface has one implementation |
| Bridge | An abstraction with its own hierarchy | No. Two hierarchies vary separately | Let abstraction and implementation vary independently | Designed up front, both sides together | Two parallel hierarchies, and a field of the implementor type in the abstraction base |
| Decorator | Same as the wrapped object | Yes | Add responsibilities dynamically without subclassing | Designed up front, for stacking | Wrapper implements the same interface it holds, and instances nest |
| Proxy | Same as the wrapped object | Yes | Control access to the object | Designed up front, for one subject | Same interface, and the wrapper decides whether or when to forward |

The pairwise distinctions, stated as decisions rather than definitions.

- **Adapter versus Facade.** Both sit in front of something awkward. The
  question that separates them is where the interface came from. Adapter's
  target already existed and had clients before the adapter was written. Facade
  invents its interface, and the invented interface has exactly one
  implementation because there is nothing to be compatible with. A Facade that
  grows a second implementation is turning into an Adapter over a target.
- **Adapter versus Bridge.** An object adapter and a Bridge draw the same
  picture, a class holding a reference to something it forwards to. The
  difference is time and ownership. Adapter is remedial, applied to two
  interfaces that were designed in ignorance of each other, and the target is
  fixed by the client. Bridge is anticipatory, designed so that an abstraction
  hierarchy and an implementation hierarchy can each grow without touching the
  other, and both hierarchies are yours. If you can change both sides and you
  are planning for future variation, it is Bridge. If you cannot change either
  side and you are solving today's mismatch, it is Adapter.
- **Adapter versus Decorator.** Both are called Wrapper in the GoF text, which
  is where the confusion starts, per
  https://en.wikipedia.org/wiki/Adapter_pattern, verified 2026-08-02. Decorator
  implements the interface of the object it wraps and adds behaviour, which is
  why decorators stack. Adapter implements a different interface and adds no
  behaviour of its own, which is why adapters do not stack in any useful way.
  The mechanical test is a single line. If the wrapper's interface equals the
  wrapped object's interface, it is not an Adapter.
- **Adapter versus Proxy.** Proxy also keeps the interface identical. What Proxy
  varies is access, not shape. Lazy instantiation, remote invocation,
  permission checks and caching are Proxy responsibilities and none of them
  change the signature. A remote proxy that also converts to a different
  interface has become an Adapter over a Proxy, and it is clearer to write it as
  two objects than one.

Patterns that compose with Adapter rather than compete with it.

- **Strategy.** An adapter is frequently the object that a Strategy field holds.
  The client's target interface is the strategy type, and each adapter is one
  strategy over one vendor. The two patterns are orthogonal and the combination
  is common enough to be unremarkable.
- **Factory Method or a dependency injection container.** Something has to
  construct the adapter and give it to the client. The construction site is the
  one place in the system that names the adaptee, which is the property that
  makes the pattern pay, and the choice of factory or container is about wiring
  rather than about the pattern.
- **Decorator.** Composes cleanly on top. Retry, timing and logging decorators
  wrap the adapter and present the same target interface. Keeping them as
  separate decorators rather than folding them into the adapter is what stops
  the adapter growing into an untestable knot of concerns.
- **Facade.** Composes below. A Facade that simplifies a subsystem can be the
  adaptee that an Adapter then converts to a target the client demands.
- **Anti-Corruption Layer.** The larger relative. Eric Evans' pattern from
  *Domain-Driven Design* is the same instinct applied between bounded contexts,
  built from a facade, a translator and adapters rather than from one class.
  Reach for it when two models disagree, not when two method signatures do. See
  the domain-driven design family entry.
- **Ports and Adapters.** The architectural use of the same word, and the case
  that most readers meet first. Cockburn states directly that the
  ports-and-adapters pattern is a particular use of the Adapter pattern,
  https://alistair.cockburn.us/hexagonal-architecture/, verified 2026-08-02.
  Four things change when the pattern is scaled from an object to an
  architecture. First, the target is always owned by the application and is
  called a port, which makes the ownership rule from dimension 5 into an
  architectural law rather than a preference. Second, adapters come in two
  flavours, because Cockburn separates a primary actor, which drives the
  application, from a secondary actor, which the application drives, and the
  adapters on each side have different shapes. Third, the substitution is
  expected to be exercised in normal work rather than in a hypothetical vendor
  swap, since the same port that carries a database in production carries a mock
  in a test, and the same port that carries a web request carries a test script.
  Fourth, the count is deliberately small. Cockburn writes that his selection
  tends to favour a small number, two, three or four ports, and that there is no
  particular damage in choosing the wrong number. The GoF pattern is silent on
  all four points, which is why the two are worth naming separately even though
  one is a use of the other.

Patterns that conflict with Adapter.

- **Service Locator.** An adapter that reaches into a global registry to find
  its adaptee has thrown away the property that made it useful. The adaptee is
  no longer visible at the construction site, so the blast radius argument from
  dimension 10 stops holding and the client's test seam becomes global mutable
  state. See the anti-patterns family entry.
- **Singleton.** An adapter registered as a process-wide singleton makes
  substitution a global act. Where the adapter has state, per dimension 11, it
  also makes tests order-dependent. Scope adapters to the component that owns
  the dependency instead.

## 14. Refactoring path in and out

Introducing the pattern into code that calls a foreign type directly. The named
refactorings are Extract Interface and Move Method, see the refactoring family
entries for both.

1. Find every call site of the foreign type inside the code you own. This is the
   measurement that decides everything else. Five call sites is an afternoon.
   Five hundred means the mismatch should be handled at a coarser boundary, per
   the Anti-Corruption Layer note in dimension 13.
2. List the operations the client actually calls, not the operations the adaptee
   offers. The difference between those two lists is the difference between a
   three-method target and a forty-method one.
3. Extract an interface containing exactly that list, and phrase its methods in
   the client's vocabulary rather than in the adaptee's. A method named after
   the vendor is a sign that step 2 was skipped.
4. Write the adapter as the only implementation. It holds the adaptee, and its
   body is the code that used to sit at the call sites, moved rather than
   rewritten. Run the tests. Nothing has changed behaviourally yet, which is
   what makes this step safe.
5. Change one call site to depend on the interface and receive the adapter by
   constructor parameter. Run the tests. Repeat per call site rather than in one
   sweep, because a partial migration compiles at every step.
6. Move the construction of the adapter to a single composition point, a factory
   or a container registration. Confirm by search that the adaptee's type name
   appears in two files only, the adapter and the composition point.
7. Write the error translation deliberately at this point rather than leaving it
   implicit. Map each adaptee failure to a target failure, chain causes, and add
   the contract test from dimension 15.
8. Only now consider a second implementation. Do not build the interface for a
   second adaptee that has not been chosen. The interface earns its keep from
   the test seam even with one implementation, which is a sufficient reason on
   its own.

Removing the pattern when it stops earning its place. The signals are a target
interface with one implementation that is never faked in a test, an adapter
whose methods forward unchanged, or a vendor that has been standardised on for
years and will not be replaced.

1. Confirm the adapter performs no translation. Read every method. Any error
   mapping, defaulting or type conversion is real work and must be moved rather
   than deleted.
2. Confirm the target interface is not used as a test seam. If tests fake it,
   the interface is paying for itself and only the adapter class is in question.
3. Inline the adapter's method bodies into the call sites, one at a time,
   running tests after each. This is Inline Method.
4. Change the call sites to depend on the adaptee's type. This is the step that
   reverses the dependency direction, so do it deliberately and with the search
   from step 6 above as the record of what is affected.
5. Delete the interface if nothing else implements it. This is Collapse
   Hierarchy.
6. Where two adapters were chained, prefer collapsing the chain into one adapter
   over deleting both. A single translation from A to C is usually correct and
   is a smaller change than removing the boundary.

## 15. Testing and verification

Easier because of the pattern.

- The client becomes testable without the dependency. A hand-written fake
  implementing the target interface removes the network, the database, the file
  system or the vendor licence from the client's test run. This is the largest
  practical payoff of Adapter and it arrives even when there is only one real
  implementation.
- Failure paths in the client become reachable. A fake that throws on the third
  call tests a retry policy in milliseconds, where reproducing the same failure
  against the real adaptee would need fault injection at the transport.
- The translation is a pure function in most adapters, so it can be tested with
  table-driven cases and, where the mapping is total, with property-based tests
  asserting a round trip.

Harder because of the pattern.

- The adapter itself is the one component a fake cannot verify. Every test that
  uses the fake is silent about whether the adapter's translation is right. This
  is the standard way a well-tested system fails in production, and the answer
  is an integration test that runs the adapter against the real adaptee, in
  contract-test form.
- The target interface is now a published contract with implementations that may
  be written by other people or other teams, so the contract needs its own
  suite rather than living in comments.
- Behaviour that the target promises and the adaptee does not, per dimension 11,
  is invisible to unit tests on either side. Only a test that exercises the
  promise against the real adaptee finds it.

Techniques that apply.

- **Contract test, sometimes called an abstract test case.** Write one test
  class against the target interface with an abstract hook that supplies an
  implementation, then subclass it once per adapter and once for the fake.
  Running the same suite against the fake and against the real adapter is what
  keeps the fake honest, and a fake that drifts from the real adapter is worse
  than no fake at all.
- **Prefer a hand-written fake to a mocking framework for the target.** A mock
  asserts that a call was made. A fake behaves. Since the target interface was
  derived from what the client needs, per dimension 14 step 2, the fake is
  usually under fifty lines, and it catches sequencing errors that a mock's
  verification cannot.
- **Verification tests against the real dependency, run on a schedule.** For a
  vendor SDK or an HTTP client, run the adapter against a sandbox or a recorded
  session, on a schedule rather than on every commit, so that an upstream change
  is discovered by the build rather than by an incident. Cross reference the
  testing family entry on consumer-driven contract testing.
- **Property test on the translation.** Where the adapter converts data in both
  directions, assert that converting out and back is the identity for every
  generated input. This finds the boundary cases in date handling, numeric
  widening, empty collections and absent-value representation that hand-written
  examples miss.
- **Test the error mapping explicitly, one case per adaptee failure.** Assert
  both the target exception type and that the cause is chained. This is the
  cheapest test in the suite and it prevents the swallowed-cause failure from
  dimension 11.
- **Assert that the fake and the adapter agree on laziness.** Where the adapter
  returns a view rather than a copy, the fake must too, otherwise aliasing bugs
  appear only in production. A shared test that mutates the source and reads
  through the result covers it.

## 16. Observability signals

The pattern hides the dependency from the client by design, so the dependency
has to appear in telemetry or nobody can diagnose it. Every measurement below
exists because the source code no longer says which vendor is in play.

What to record.

- A span around the adaptee call, not around the adapter method. The span is the
  boundary between code the team owns and code it does not, which makes it the
  most useful span in the system. Attributes should carry the adaptee's
  identity, its version, the target operation name and the outcome.
- A counter of calls, labelled by target operation and by outcome, where outcome
  distinguishes success, a mapped failure by category, and a translation
  failure. Separating translation failures from adaptee failures is what makes
  the counter worth having, because the two have completely different fixes.
- A latency histogram split into two measurements where the translation is not
  free. Time inside the adaptee, and time spent translating. A single combined
  number cannot tell an operator whether the vendor got slower or the payload
  got larger, and those lead to different actions.
- The adaptee's own error code or status as an attribute, preserved unchanged
  alongside the mapped target error. Mapping loses information by construction,
  and the raw code is what a vendor support ticket needs.
- A version attribute for the adaptee, emitted at startup and on the span. When
  behaviour changes after a dependency upgrade this is the only field that
  connects the two events.
- For a view-based or lazy adapter, a counter of conversions and a size
  histogram of what was converted, so that an O(n) translation on a hot path
  becomes visible before it becomes an incident.
- A startup log line naming which adapter implementation was bound to each
  target interface. In a system with more than one adapter per port this is the
  single field that answers what is actually running.

A healthy instance on a dashboard. Call volume tracks request volume with a
stable ratio. Translation time is a small and flat fraction of adaptee time.
Mapped failures sit in one or two expected categories, such as not found, and
translation failures are zero. The adaptee version attribute has one value
across the fleet. Converted sizes are bounded and their distribution does not
drift.

A failing instance. Translation failures appear at all, which means the adaptee
is returning something the adapter was not written for, and this is nearly
always the first visible sign of an upstream change. Or the ratio of adaptee
calls to inbound requests climbs, which means the client is calling the target
in a loop that the target interface made look cheap. Or translation time grows
while adaptee time is flat, which is the copying adapter from dimension 11
meeting larger payloads. Or two adaptee version values appear at once during a
deploy and the error rate differs between them, which localises a regression to
the upgrade without reading any code. Or mapped failures collapse onto a single
generic category, which means the error mapping lost its distinctions and the
fix belongs in the adapter rather than in the alert.

## 17. Security and privacy implications

The pattern is close to silent on security when both sides are trusted code in
the same build. Claiming otherwise would be inventing a concern. Four genuine
implications appear at the boundary the adapter creates, and all four exist
because the adapter is the point where data crosses between two systems with
different assumptions.

**The adapter is a trust boundary and should behave like one.** The adaptee is
frequently third party. Whatever it returns arrives inside the application's own
model and is then treated as trusted by every layer above, because the target
interface says nothing about provenance. Validate on the way in. Bound lengths,
reject unexpected enum values rather than defaulting them, and refuse structures
larger than the client can process. An adapter that maps an unknown status to a
default is making a security decision without saying so.

**Deserialisation and expansion attacks land in the adapter.** Where the
translation parses XML, JSON or a binary format from the adaptee, the parser
configuration is the adapter's responsibility. External entity resolution,
unbounded recursion and archive expansion are the standard exposures, and they
sit in the one file where nobody thinks to look because the file is described as
plumbing. Configure the parser explicitly rather than accepting library
defaults, and cap input size before parsing rather than after.

**Credentials and secrets concentrate here.** The adapter is normally the object
holding the API key, the connection string or the signing key for the
dependency. That concentration is an improvement over spreading them across call
sites, and it creates one file that must never log its own fields. Two habits
follow. Never implement a string conversion on an adapter that dumps its
configuration, since a debug log statement then prints the key. Redact the
credential in every error path, because the failure case is where secrets escape
most often, usually inside an exception message that includes the request.

**Error mapping can become an information leak.** An adapter that maps an
upstream failure faithfully may pass the adaptee's message to a caller that
returns it to an end user. Vendor messages contain internal hostnames, query
fragments, account identifiers and stack traces. Split the mapping in two. A
rich internal representation that carries the raw detail into logs and traces,
and a coarse external representation that carries only a category and a
correlation identifier. The correlation identifier is what lets support recover
the detail without the detail crossing the boundary.

On privacy the pattern is neutral in itself, with two practical caveats. The
adapter is the natural place to apply data minimisation, because it is the point
where a wide upstream record becomes a narrow internal one, and dropping fields
there is cheaper than governing them everywhere downstream. It is also the place
where a cross border transfer becomes real, since the adaptee may be a service
in another jurisdiction, and the adapter is the one file where that fact is
visible. The observability advice in dimension 16 recommends recording the
adaptee's raw response codes and identifiers. Where those carry personal data,
treat the telemetry field with the same retention and access controls as the
data itself rather than as ordinary operational output.

## 18. References

1. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides. *Design Patterns.
   Elements of Reusable Object-Oriented Software*. Addison-Wesley, 1994.
   ISBN 0-201-63361-2. Chapter 4, Structural Patterns, section Adapter,
   beginning page 139. Source of the intent, the Wrapper alias, the four
   participants, the class versus object adapter distinction, the applicability
   list, and the Implementation section covering pluggable adapters and two-way
   adapters.
2. InformIT (Pearson). Authorised excerpt of the Adapter chapter of *Design
   Patterns*, covering Applicability and Implementation.
   https://www.informit.com/articles/article.aspx?p=1398600&seqNum=2
   Verified 2026-08-02. Used to confirm the wording of the applicability list,
   the class versus object adapter sentences, the pluggable adapter techniques,
   and the two-way adapter transparency note.
3. Alistair Cockburn. "Hexagonal Architecture", originally HaT Technical Report
   2005.02, dated 4 September 2005.
   https://alistair.cockburn.us/hexagonal-architecture/
   Verified 2026-08-02. Source of the Ports and Adapters intent statement, the
   primary versus secondary actor distinction, the guidance on port count, and
   the Related Patterns sentence stating that ports-and-adapters is a particular
   use of the Adapter pattern.
4. Oracle. *Java SE 21 API Specification*, `java.util.Arrays`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Arrays.html
   Verified 2026-08-02. Source for the `asList` production use and the
   fixed-size backed-by-array wording.
5. Oracle. *Java SE 21 API Specification*, `java.io.InputStreamReader`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/io/InputStreamReader.html
   Verified 2026-08-02. Source for the byte-stream to character-stream
   production use.
6. Oracle. *The Java Language Specification, Java SE 21 Edition*, chapter 8,
   section 8.1.4, Superclasses and Subclasses.
   https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html
   Verified 2026-08-02. Source for the single direct superclass rule that makes
   the class adapter form unavailable in Java.
7. Microsoft. *C# documentation*, "Object-oriented programming, inheritance".
   https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/object-oriented/inheritance
   Verified 2026-08-02. Source for the single direct base class rule and the
   multiple interface implementation rule in C#.
8. Microsoft. *.NET API documentation*, `System.Data.Common.DbDataAdapter`.
   https://learn.microsoft.com/en-us/dotnet/api/system.data.common.dbdataadapter
   Verified 2026-08-02. Source for the ADO.NET data adapter production use, its
   provider specific subclasses, and the documented behaviour of `Fill` and
   `Update`.
9. The Go project. *Go FAQ*, "Why is there no type inheritance?".
   https://go.dev/doc/faq
   Verified 2026-08-02. Source for the absence of type inheritance, implicit
   interface satisfaction, and embedding as an analogue rather than an identity.
10. The Go project. *`net/http` package documentation*, `HandlerFunc`.
    https://pkg.go.dev/net/http#HandlerFunc
    Verified 2026-08-02. Source for the standard library calling `HandlerFunc`
    an adapter, and for the `ServeHTTP` behaviour.
11. The Go project. *`io` package documentation*.
    https://pkg.go.dev/io
    Verified 2026-08-02. Source for `NopCloser`, `LimitReader`, `MultiReader`
    and `TeeReader` as stream adapters, including the `WriterTo` forwarding note.
12. Google. *Android developer documentation*, "Create dynamic lists with
    RecyclerView".
    https://developer.android.com/develop/ui/views/layout/recyclerview
    Verified 2026-08-02. Source for the `RecyclerView.Adapter` production use and
    the documented roles of `onCreateViewHolder`, `onBindViewHolder` and
    `getItemCount`.
13. Wikipedia contributors. "Adapter pattern".
    https://en.wikipedia.org/wiki/Adapter_pattern
    Verified 2026-08-02. Used only to confirm the shared Wrapper alias with
    Decorator, the class versus object adapter phrasing, and the GoF page
    attribution, not as a source of explanation.
14. Eric Evans. *Domain-Driven Design. Tackling Complexity in the Heart of
    Software*. Addison-Wesley, 2003. ISBN 0-321-12521-5. Chapter 14, Maintaining
    Model Integrity, section Anti-Corruption Layer. Cited in dimensions 4, 12
    and 13 as the larger-scale relative of Adapter.

## Code examples

Four languages, chosen because each shows a different structural fact. Java
shows the object adapter with error translation, which is the everyday form, in
a language where the class adapter is unavailable per dimension 5. TypeScript
shows the object form beside the function-valued form that usually replaces it
when the target has one method. Python shows the class adapter using multiple
inheritance, which is the form Java, C# and Go cannot express. Go shows the
function-typed adapter that its own standard library uses.

C# is omitted because its object adapter has the same shape as the Java one and
would add no information. Rust is discussed in dimension 8 rather than shown,
because its newtype form is a language constraint story rather than a pattern
story.

### Java, object adapter with error translation

Runnable as a single file. The adaptee reports failure by a return code, the
target by an exception, and the adapter owns the conversion.

```java
import java.util.List;

interface RowRenderer {
    String render(List<String> rows) throws RenderFailed;
}

class RenderFailed extends Exception {
    RenderFailed(String message) { super(message); }
}

// The adaptee. Wrong shape, right behaviour, cannot be edited.
final class LegacyWriter {
    private String output = "";
    int write(String[] cells, char separator) {
        if (cells == null) return -1;
        if (cells.length == 0) return -7;
        output = String.join(String.valueOf(separator), cells);
        return 0;
    }
    String lastOutput() { return output; }
}

final class LegacyWriterAdapter implements RowRenderer {
    private final LegacyWriter adaptee;
    private final char separator;

    LegacyWriterAdapter(LegacyWriter adaptee, char separator) {
        this.adaptee = adaptee;
        this.separator = separator;
    }

    public String render(List<String> rows) throws RenderFailed {
        int code = adaptee.write(rows.toArray(new String[0]), separator);
        if (code == -7) throw new RenderFailed("no rows supplied");
        if (code != 0) throw new RenderFailed("writer failed, code " + code);
        return adaptee.lastOutput();
    }
}

public final class AdapterDemo {
    public static void main(String[] args) throws Exception {
        RowRenderer renderer = new LegacyWriterAdapter(new LegacyWriter(), ',');
        System.out.println(renderer.render(List.of("a", "b", "c")));
        try {
            renderer.render(List.of());
        } catch (RenderFailed e) {
            System.out.println("mapped: " + e.getMessage());
        }
    }
}
```

### TypeScript, object form and function form

The object form first, then the function-valued form that removes the class
entirely. A function value satisfies a single-method target, which is the shape
dimension 8 recommends in every language with first-class functions.

```typescript
interface RowRenderer {
  render(rows: string[]): string;
}

class LegacyWriter {
  write(cells: string[], separator: string): string {
    if (cells.length === 0) throw new Error("code -7");
    return cells.join(separator);
  }
}

class LegacyWriterAdapter implements RowRenderer {
  constructor(
    private readonly adaptee: LegacyWriter,
    private readonly separator: string,
  ) {}

  render(rows: string[]): string {
    return this.adaptee.write(rows, this.separator);
  }
}

const renderer: RowRenderer = new LegacyWriterAdapter(new LegacyWriter(), ",");
console.log(renderer.render(["a", "b", "c"]));

type RenderFn = (rows: string[]) => string;

const legacy = new LegacyWriter();
const renderPipe: RenderFn = (rows) => legacy.write(rows, "|");

function report(rows: string[], render: RenderFn): string {
  return rows.length === 0 ? "" : render(rows);
}

console.log(report(["a", "b"], renderPipe));
```

### Python, class adapter by multiple inheritance

The form Java, C# and Go cannot express. The adapter inherits from both sides
and calls its own inherited method rather than forwarding to a field. The object
form sits beneath it for contrast.

```python
from abc import ABC, abstractmethod


class RowRenderer(ABC):
    @abstractmethod
    def render(self, rows: list[str]) -> str: ...


class LegacyWriter:
    def write(self, cells: list[str], separator: str) -> str:
        if not cells:
            raise ValueError("code -7")
        return separator.join(cells)


class LegacyWriterClassAdapter(LegacyWriter, RowRenderer):
    separator = ","

    def render(self, rows: list[str]) -> str:
        return self.write(rows, self.separator)


class LegacyWriterObjectAdapter(RowRenderer):
    def __init__(self, adaptee: LegacyWriter, separator: str = ",") -> None:
        self._adaptee = adaptee
        self._separator = separator

    def render(self, rows: list[str]) -> str:
        return self._adaptee.write(rows, self._separator)


if __name__ == "__main__":
    print(LegacyWriterClassAdapter().render(["a", "b", "c"]))
    print(LegacyWriterObjectAdapter(LegacyWriter(), "|").render(["a", "b"]))
```

### Go, function-typed adapter

The shape the standard library uses for `http.HandlerFunc`. A named function
type carries the target's method, so a plain function satisfies an interface it
was never written for.

```go
package main

import (
	"fmt"
	"strings"
)

type RowRenderer interface {
	Render(rows []string) (string, error)
}

// RendererFunc adapts an ordinary function to RowRenderer.
type RendererFunc func(rows []string) (string, error)

func (f RendererFunc) Render(rows []string) (string, error) {
	return f(rows)
}

type legacyWriter struct{ separator string }

func (w legacyWriter) Write(cells []string) (string, int) {
	if len(cells) == 0 {
		return "", -7
	}
	return strings.Join(cells, w.separator), 0
}

// Object adapter over the legacy type, with code to error translation.
type legacyAdapter struct{ adaptee legacyWriter }

func (a legacyAdapter) Render(rows []string) (string, error) {
	out, code := a.adaptee.Write(rows)
	if code != 0 {
		return "", fmt.Errorf("writer failed, code %d", code)
	}
	return out, nil
}

func main() {
	var r RowRenderer = legacyAdapter{adaptee: legacyWriter{separator: ","}}
	out, err := r.Render([]string{"a", "b", "c"})
	fmt.Println(out, err)

	var f RowRenderer = RendererFunc(func(rows []string) (string, error) {
		return strings.Join(rows, "|"), nil
	})
	out, err = f.Render([]string{"a", "b"})
	fmt.Println(out, err)
}
```
