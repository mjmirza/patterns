---
name: Builder
slug: builder
family: 01-gof
category: Creational
aliases: [Fluent Builder, Step Builder, Test Data Builder, Functional Options]
first_described: "Gamma, Helm, Johnson, Vlissides 1994"
maturity: canonical
related: [abstract-factory, factory-method, prototype, composite, interpreter]
incompatible_with: []
verified: 2026-08-02
---

# Builder

## 1. Name, aliases, and lineage

The canonical name is Builder. It appears as one of the five creational patterns
in Gamma, Helm, Johnson and Vlissides, *Design Patterns. Elements of Reusable
Object-Oriented Software*, Addison-Wesley 1994, chapter 3, page 97. The stated
intent there is to separate the construction of a complex object from its
representation so that one construction process can produce different
representations. The motivating example in that chapter is a reader for
Rich Text Format documents that walks a single token stream while a swappable
converter object decides what artifact the walk produces, whether plain ASCII,
a widget tree, or a TeX document.

A second, later, and now far more widely deployed pattern shares the name. In
Joshua Bloch, *Effective Java*, third edition, Addison-Wesley 2018, chapter 2,
Item 2, titled "Consider a builder when faced with many constructor parameters",
Builder is presented as the answer to the telescoping constructor and the
JavaBeans setter anti-pattern. A client obtains a mutable builder, calls
setter-like methods for the optional parameters it cares about, and calls
`build()` to obtain an immutable instance. Bloch names the Nutrition Facts label
as the motivating case, a class with three required fields and more than twenty
optional ones.

These are different patterns wearing one name, and conflating them is the single
most common source of confusion in the literature. The distinction is worth
stating plainly.

- **GoF Builder** varies the *representation*. There are many builders, one
  director, and the point of the abstraction is polymorphism over the product
  family. The director does not know what it is building.
- **Bloch Builder** varies the *parameter set*. There is one builder, no
  director, and the point is readable and safe construction of a single
  immutable type with many optional fields. The caller knows exactly what it is
  building.

The alias Step Builder describes a Bloch-style variant where each stage returns
a different interface type, so the compiler refuses a `build()` call until every
required field has been supplied. The alias Functional Options describes the Go
community's replacement for the same problem, which uses variadic closures
instead of a builder object. Nat Pryce's Test Data Builder is the Bloch shape
applied to test fixtures, proposed as a replacement for Object Mother.

## 2. Problem and context

A type is expensive or awkward to construct because construction has several
independent axes. Recognise the problem in your own code by these symptoms.

You have a constructor with eight positional parameters, four of which are the
same primitive type, and every call site is a puzzle where transposing two
arguments compiles cleanly and fails at runtime. You have written five
overloaded constructors that each delegate to a longer one with defaults filled
in, and adding a sixth optional field means adding another overload. Or you have
given up and shipped a no-argument constructor plus public setters, which means
the object is legally observable in a half-configured state and can never be
made immutable or safely shared across threads.

Alternatively the shape is different. You have one algorithm that walks a source
structure once, and you need it to emit three different artifacts. A parser that
must produce either an abstract syntax tree, a pretty-printed listing, or a
symbol table. A document reader that must render to HTML, to PDF, or to a plain
text index. Duplicating the walk three times duplicates the parsing bugs three
times. Putting three output modes inside the walk with conditionals makes the
walk unreadable and couples it to every output format that will ever exist.

The context matters. Builder earns its place when construction is genuinely
multi-step or multi-variant. A value type with two required fields and no
optional ones does not have this problem, and wrapping it in a builder is
ceremony that costs a class, a test, and a reader's attention for nothing.

## 3. Forces

The pattern balances competing pressures, and it clearly favours some over
others.

- **Cognitive load at the call site.** Favoured heavily. A named chain of
  setter-like calls is readable without consulting the signature. This is the
  primary force Bloch Builder optimises.
- **Coupling.** Favoured in the GoF form. The director depends on an abstract
  builder interface, so a new representation costs one new class and zero
  changes to the walk. Sacrificed in the Bloch form, where the builder is a
  nested class welded to its product and the two must change together.
- **Consistency and invariants.** Favoured. Validation happens once, at
  `build()`, on a complete field set. Cross-field rules that a per-setter check
  cannot express become checkable. Immutability of the product becomes possible.
- **Latency and allocation.** Sacrificed. Every construction allocates a builder
  in addition to the product, and in the fluent form each chained call may
  allocate again if the builder is persistent rather than mutable. On a hot path
  building millions of small objects this is measurable.
- **Cost of change.** Sacrificed. Adding a field means touching the product, the
  builder, and often a test factory. The builder is a duplicated field list that
  can drift from the product it builds.
- **Team topology.** Favoured on wide API surfaces. A builder lets a library
  add optional parameters over releases without breaking callers or exploding
  the overload count, which matters when the caller is a different team on a
  different release schedule.
- **Operability.** Neutral to slightly favoured. A single validated construction
  point is a good place to attach metrics and to reject bad configuration at
  startup rather than at first use.

A description that claims Builder costs nothing is describing it wrongly. It
costs an extra type, an extra allocation, and a permanent maintenance coupling
between two field lists.

## 4. Applicability and non-applicability

Reach for Builder when any of the following holds.

- The type has more than roughly four constructor parameters, and several are
  optional or share a type, per the guidance in Bloch Item 2.
- The type must be immutable after construction but cannot be built in one
  expression.
- Construction has cross-field validation rules that no single setter can check
  alone, for example "either a body or a content length, never both".
- One traversal or parse must yield several unrelated output representations,
  which is the GoF case.
- You are assembling a recursive structure such as a Composite tree or an
  abstract syntax tree, where the assembly order is driven by the source rather
  than by the caller.
- Test fixtures need many near-identical objects that differ in one field each,
  the Test Data Builder case.

Non-applicability. Do not reach for Builder when any of the following holds.

- The type has two or three required fields and no optional ones. A constructor
  or a record is shorter, faster, and better checked. This is the most common
  misapplication.
- The language already solves the problem. Python, Kotlin, C# and Swift have
  named and default arguments, which cover the Bloch case directly with zero
  extra types. Writing a Java-style builder in Python is importing a workaround
  for a limitation the language does not have. Protocol Buffers demonstrates
  this precisely, generating Builder classes in Java because messages are
  immutable there, and generating plain mutable message objects in Python with
  no builder at all.
- The object is on a hot allocation path where the extra object per construction
  is visible in profiling. Prefer a constructor, an object pool, or a mutable
  struct.
- The construction steps are genuinely order-dependent in a way callers must
  understand. A fluent chain implies order-independence. If `withRetries()` must
  precede `withTimeout()`, a builder actively lies about the contract, and a
  Step Builder or a plain constructor is honest.
- The real problem is that the type has too many responsibilities. Twenty
  optional fields is sometimes a signal to split the type rather than to make
  the construction of the oversized type more pleasant.
- The product is a service with behaviour rather than a configuration value.
  Dependency injection and Abstract Factory both fit that better.

## 5. Structure

The GoF form has four participants.

- **Product.** The complex artifact under construction. In the GoF form there is
  no common Product supertype, because the representations may be unrelated. An
  ASCII string and a widget tree share nothing.
- **Builder.** An abstract interface declaring one step operation per element
  the director can encounter, for example `convertCharacter`, `convertParagraph`,
  `convertFontChange`. It deliberately does not declare a retrieval operation,
  because the return type differs per concrete builder.
- **ConcreteBuilder.** One per representation. Holds the partially assembled
  result, implements each step, and offers a retrieval operation with a concrete
  return type that the director never calls.
- **Director.** Owns the traversal or parse. Holds a reference to the abstract
  Builder and calls step operations in the order the source dictates. The client
  hands the director a builder, runs the director, then asks the builder for the
  result.

The Bloch form collapses this to two participants.

- **Product.** An immutable type whose constructor is private and takes the
  builder itself as its single argument.
- **Builder.** A static nested mutable class holding one field per product
  field, with required fields taken in its own constructor, one fluent
  setter per optional field returning `this`, and a `build()` method that
  validates and constructs the product. There is no director, because the
  client is the director.

## 6. ASCII structure diagram

```
GoF Builder. Varies the REPRESENTATION.

  +-------------+  builder   +--------------------+
  |  Director   |----------->|  <<interface>>     |
  |-------------|            |  Builder           |
  | construct() |            |--------------------|
  +-------------+            | buildPartA()       |
        |                    | buildPartB()       |
        | walks source,      +--------------------+
        | calls buildX()          ^          ^
        v                         |          |
   [ source stream ]     +----------------+  +----------------+
                         | AsciiBuilder   |  | WidgetBuilder  |
                         |----------------|  |----------------|
                         | buildPartA()   |  | buildPartA()   |
                         | buildPartB()   |  | buildPartB()   |
                         | getAscii():Str |  | getTree():Node |
                         +----------------+  +----------------+
                                 |                   |
                                 v                   v
                           [ String ]          [ Widget tree ]
                            (Product A)         (Product B)


Bloch Builder. Varies the PARAMETER SET.

  +-----------------+           +--------------------------+
  |     Client      |           |  Request  (immutable)    |
  |-----------------|  build()  |--------------------------|
  | new Builder(u)  |---------->| - uri, method, timeout   |
  |  .timeout(5s)   |           | - headers (defensive cp) |
  |  .header(k,v)   |           |--------------------------|
  |  .build()       |           | private Request(Builder) |
  +-----------------+           +--------------------------+
          |                                 ^
          | mutates                         | constructs + validates
          v                                 |
  +--------------------------+              |
  | Request.Builder (mutable)|--------------+
  |--------------------------|
  | uri, method, timeout ... |
  | timeout(d) : Builder     |
  | header(k,v): Builder     |
  | build()    : Request     |
  +--------------------------+
```

## 7. Dynamics

The GoF form. The client drives a two-phase interaction. Phase one wires the
director to a chosen builder. Phase two runs the traversal, during which the
director issues an unpredictable number of step calls in an order it derives
from the source, not from the client. Only after the traversal does the client
reach past the abstraction to the concrete builder for the typed result.

```
Client            Director          AsciiBuilder        Product
  |                  |                   |                 |
  |-- new(builder) ->|                   |                 |
  |-- construct() -->|                   |                 |
  |                  |-- buildPartA() -->|                 |
  |                  |                   |-- append ------>|
  |                  |-- buildPartB() -->|                 |
  |                  |                   |-- append ------>|
  |                  |-- buildPartA() -->|   (loop, count   |
  |                  |                   |    driven by     |
  |                  |                   |    the source)   |
  |<-- return -------|                   |                 |
  |                                      |                 |
  |-- getResult() ---------------------->|                 |
  |<-- Product --------------------------|                 |
```

The Bloch form is a single-phase accumulation followed by one validating
transition. The builder is a mutable state machine with exactly two states,
accumulating and consumed, and `build()` is the transition.

```
   [ accumulating ]
        |   ^
        |   |  fluent setter, returns this
        |   |  (any number, any order)
        +---+
        |
        | build()
        |   validate required fields
        |   validate cross-field rules
        |   copy mutable collections
        v
   [ product constructed ]
        |
        | build() again ?
        v
   variant A. return a second independent product  (reusable builder)
   variant B. throw IllegalStateException          (single-shot builder)
```

Which of variants A and B applies is a contract the builder must document.
Silence here is a defect, and it is where aliasing bugs are born.

## 8. Implementation variants

**Classic GoF with a director.** Abstract builder, several concrete builders, a
director owning the traversal. Use when the traversal is complex enough to be
worth sharing. The cost is four types for what a reader may see as one
operation. Give the abstract builder empty default implementations of every step
so a concrete builder can ignore the parts it does not care about, which is the
technique the GoF chapter recommends.

**Fluent Bloch builder.** Nested mutable class, chained setters returning
`this`, private product constructor. Use for immutable configuration types with
many optional fields. The cost is the duplicated field list and the runtime,
rather than compile-time, checking of required fields.

**Step Builder.** Each stage returns a distinct interface exposing only the next
legal call, and `build()` exists only on the final interface. Trades a larger
type count for compile-time proof that required fields were supplied and that
order constraints were respected. Worth it on a public API where a runtime
`IllegalStateException` would be a poor first experience.

**Recursive generic builder for inheritance hierarchies.** A self-referential
bound such as `abstract class Builder<T extends Builder<T>>` with an abstract
`self()` returning `T`, so that inherited fluent setters keep the subclass type
and chaining survives subclassing. This is the simulated self-type idiom Bloch
describes in Item 2 for hierarchical builders. It is powerful and hard to read,
so reserve it for genuine hierarchies.

**Closure or lambda replacing the builder object.** Where a language has
first-class functions, the builder can be a function that receives a mutable
config and returns nothing, applied variadically. This is Go's Functional
Options, described by Dave Cheney and credited by him to Rob Pike's earlier
self-referential functions post. It removes the builder type entirely, keeps
defaults sensible, and lets a library add options without breaking callers.

**Language-native replacement.** In Python, Kotlin, C# and Swift, named
parameters with defaults cover the Bloch case with no pattern at all. In Kotlin
a trailing lambda with a receiver gives a type-safe nested DSL that reads like a
builder while being a plain function. In Swift the `@resultBuilder` attribute
introduced by Swift Evolution proposal SE-0289 turns a sequence of statements
into a built-up result value, which is the mechanism behind SwiftUI's `ViewBuilder`
and is a compiler-level generalisation of the GoF director idea.

**Generated builders.** Where the field list is machine-readable, generate the
builder rather than hand-writing it, which removes the drift risk. Protocol
Buffers does this for every Java message type.

## 9. Known production uses

- **Java standard library, `java.net.http.HttpRequest.Builder`.** The Java 11+
  HTTP client builds requests through an interface whose documentation opens
  with "A builder of HTTP requests." It exposes `uri(URI)`, `header(String,
  String)` and `timeout(Duration)`, and a `build()` returning `HttpRequest` that
  throws `IllegalStateException` when no URI was set. Verified 2026-08-02 at
  https://docs.oracle.com/en/java/javase/21/docs/api/java.net.http/java/net/http/HttpRequest.Builder.html
- **Java standard library, `java.util.Locale.Builder`.** The class description
  states that the Builder "checks if a value configured by a setter satisfies the
  syntax requirements defined by the `Locale` class", unlike the constructors and
  the `Locale.of()` factory. This is the validation-at-construction argument made
  concrete in the platform itself. Verified 2026-08-02 at
  https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Locale.Builder.html
- **Protocol Buffers, generated Java code.** The official generated code guide
  states that message objects "are immutable", comparing them to a Java `String`,
  and that "To construct a message object, you need to use a builder." Every
  generated message type ships a nested `Builder` implementing `Message.Builder`.
  The same guide for Python generates plain mutable message classes with no
  builder, which makes protobuf a controlled comparison of the same problem
  solved in two languages. Verified 2026-08-02 at
  https://protobuf.dev/reference/java/java-generated/ and
  https://protobuf.dev/reference/python/python-generated/
- **Rust standard library, `std::process::Command`.** The documentation states
  that "Builder methods are provided to change these defaults and otherwise
  configure the process" and that "The builder methods change the command without
  needing to immediately spawn the process." Configuration accumulates through
  `arg` and `env`, and the terminal operation is one of `spawn`, `output` or
  `status` rather than a `build`. Verified 2026-08-02 at
  https://doc.rust-lang.org/std/process/struct.Command.html
- **OkHttp, `Request.Builder`.** The project README's GET example constructs a
  request through `new Request.Builder().url(url).build()`. OkHttp 5.4.0 at time
  of verification. Verified 2026-08-02 at
  https://raw.githubusercontent.com/square/okhttp/master/README.md
- **Swift and SwiftUI result builders.** Swift Evolution proposal SE-0289,
  status Implemented in Swift 5.4, describes result builders as a feature
  "which allows certain functions (specially-annotated, often via context) to
  implicitly build up a result value from a sequence of components." This is the
  language-level mechanism behind SwiftUI view hierarchies. Verified 2026-08-02 at
  https://github.com/swiftlang/swift-evolution/blob/main/proposals/0289-result-builders.md

## 10. Consequences

Positive.

- The product can be immutable and therefore freely shared across threads
  without synchronisation.
- Validation is centralised at one point with the full field set visible, so
  cross-field invariants become expressible.
- Call sites are self-documenting, which removes the transposed-argument class
  of bug entirely for same-typed parameters.
- A library can add optional parameters across releases without breaking source
  or binary compatibility for existing callers.
- In the GoF form, the construction algorithm and the representation vary
  independently, so a new output format costs one class.
- The internal representation of the product is hidden from the client, which
  keeps the door open to changing it later.

Negative.

- Two field lists now exist for one concept, and they drift. Adding a field and
  forgetting the builder produces a silently defaulted value, which is worse
  than a compile error.
- An extra allocation per construction, plus copying of the field set at
  `build()`.
- Required-field enforcement moves from compile time to runtime unless a Step
  Builder is used. The compiler no longer helps.
- Verbosity. A builder for a five-field type is roughly forty lines of
  mechanical code that a record or a data class would give for free.
- The fluent chain implies that call order does not matter. When it does, the
  API misleads.
- In the GoF form the client must downcast or reach past the abstract builder to
  retrieve a typed result, which is a deliberate hole in the abstraction.

## 11. Failure modes and misuse

**Silent default from a drifted builder.** A field is added to the product and
its setter is added to the builder, but `build()` is not updated to pass it.
Symptom observed in production is a value that is always zero, null, or the type
default for one field, with no error anywhere, often appearing weeks later as a
timeout of 0 meaning infinity.

**Aliased mutable state after a second build.** A reusable builder holds a
`List` and passes the same reference into every product it builds. Symptom is
two supposedly independent immutable objects that change together, and a bug
report reading "editing order B changed order A". The fix is a defensive copy
inside `build()`, and it is required for every mutable field, not only the
obvious ones.

**Concurrent use of one builder.** A builder cached in a field and shared across
request threads. Symptom is field values from one request appearing in another
request's product, intermittently, under load only, and never reproducible
locally. Builders are mutable and are almost never thread-safe.

**Required field missed until runtime.** The Java `HttpRequest.Builder` throws
`IllegalStateException` at `build()` when the URI was never set. Symptom is a
crash at first use in an environment where a code path was not exercised in
tests. Step Builders exist specifically to move this to compile time.

**Builder used where a record belongs.** Symptom is a code review comment
reading "why is there a builder for a two-field type", and a class file that is
five times the size of the value it constructs. This is the most frequent misuse
and it is a taste failure rather than a correctness failure.

**Builder as an escape hatch for a god object.** A builder with thirty-five
setters is not a construction problem, it is a design problem being made
comfortable. Symptom is that no call site ever uses more than six of the
thirty-five.

**Validation split across setters and build.** Half the rules checked eagerly in
setters, half at `build()`. Symptom is inconsistent error timing, where some
mistakes fail on the chained line and others fail three lines later, which makes
error handling at the call site incoherent.

## 12. Trade-off matrix

| Force | Builder (Bloch) | Telescoping constructor | JavaBeans setters | Abstract Factory | Named and default parameters | Functional Options (Go) |
|---|---|---|---|---|---|---|
| Call-site readability | High, named steps | Low, positional | Medium | Medium | High, named at call site | High, named closures |
| Compile-time required-field check | No, unless Step Builder | Yes | No | Yes | Yes | No |
| Product immutability | Yes | Yes | No | Yes | Yes | Yes |
| Cross-field validation point | Single, at build | Single, in ctor | None, no safe point | Single, in factory | Single, in ctor | Single, after apply |
| Allocation cost | Builder plus product | Product only | Product only | Product only | Product only | One closure per option |
| Cost of adding an optional field | One setter, one line in build | New overload, combinatorial | One setter | Change every factory | One parameter | One function |
| Varies representation | No | No | No | Yes, that is its purpose | No | No |
| Extra types introduced | One per product | None | None | One interface plus one per family | None | One option type |
| Binary compatibility for a library | Good | Poor, overloads pin arity | Good | Good | Language dependent | Good |
| Cognitive load on the reader | Medium | High at 6+ params | Low, but unsafe | High | Low | Medium |

Abstract Factory appears here because it is the alternative most often confused
with Builder. It creates families of related products in one call and returns
them immediately. Builder assembles one product across many calls and returns it
last. Choose Abstract Factory when the axis of variation is the product family,
and Builder when the axis is the assembly.

## 13. Related and incompatible patterns

**Abstract Factory** and Builder both hide concrete types behind an interface,
and both are creational. Abstract Factory answers "which family of objects", is
called once, and emphasises the product. Builder answers "how is this one object
assembled", is called many times, and emphasises the process. A GoF Builder is
frequently implemented by delegating each step to an Abstract Factory, so they
compose cleanly.

**Factory Method** is the smaller sibling. When construction is one step with
one decision, a factory method is the right size and a builder is overbuilt. A
builder's `build()` is itself often a factory method in disguise.

**Composite** is the structure a GoF Builder most often assembles. The director
walks a linear source and the builder produces a tree, which is exactly the
shape needed for widget hierarchies and document object models.

**Interpreter** pairs with Builder in every compiler front end. The parser is
the director, the abstract syntax tree is the product, and swapping the builder
turns a parser into a linter, a formatter, or a code generator without touching
the grammar.

**Prototype** replaces Builder when the variation between instances is small and
a deep copy of an exemplar plus one mutation is cheaper than re-running the
assembly. Prototype and Builder are alternatives on the same axis, not
collaborators.

**Singleton** conflicts with Builder in practice rather than in theory. A builder
held as a shared singleton is the concurrency failure mode described above.
Builders are per-construction objects.

**Fluent Interface**, as described by Martin Fowler, is a style not a pattern,
and it is what makes the Bloch Builder readable. It is orthogonal. A builder need
not be fluent, and a fluent API need not build anything.

Nothing here is strictly incompatible with Builder. The nearest thing to a
conflict is that Builder assumes the product is worth constructing atomically,
which puts it at odds with designs that stream a product to a consumer as it is
produced rather than returning it whole.

## 14. Refactoring path in and out

Introducing Builder into code that has a telescoping constructor, in order.

1. Freeze the widest constructor. Confirm every other overload delegates to it,
   and if any does not, make it do so first. This is Fowler's *Introduce
   Parameter Object* territory and the same safety rules apply.
2. Add a static nested `Builder` class with one field per parameter of that
   widest constructor. Copy the defaults from the shorter overloads into the
   builder field initialisers.
3. Give the builder a constructor taking exactly the required parameters, and
   one fluent setter per optional parameter.
4. Add `build()` calling the existing widest constructor. At this point nothing
   has changed behaviourally and every existing test should still pass.
5. Migrate call sites in small batches, favouring the noisiest ones first.
6. Once no external caller remains, reduce the widest constructor to private and
   change its signature to take the builder. Move validation out of the setters
   and into `build()`.
7. Delete the overloads. This is the step that pays for the work.

Introducing the GoF form is a different exercise and is closer to *Extract
Class* followed by *Replace Conditional with Polymorphism*. Take the traversal
that currently contains output conditionals, extract every output statement into
a method on a new interface, have the traversal call the interface, then move
each branch of the old conditional into its own implementation.

Removing Builder when it stops earning its place. This happens most often when a
language gains records, named parameters, or default arguments, or when the
product shrinks after a responsibility is extracted.

1. Confirm the builder has no validation logic that the product's constructor
   lacks. Move any that exists into the constructor first.
2. Confirm no call site relies on partial construction across statements. A
   builder stored in a variable and configured over several lines has to be
   collapsed into one expression before the builder can go.
3. Make the product's constructor public, or convert the product to a record or
   data class with defaults.
4. Rewrite call sites, then delete the builder.

Do not remove a builder that is part of a published API surface without a
deprecation cycle. The builder is the compatibility boundary and dropping it
breaks every downstream caller.

## 15. Testing and verification

What becomes easier. The product is immutable, so tests can share fixtures
freely without defensive copying and without order-dependent test pollution.
Construction is one expression, so a test that needs a product differing in one
field from the default reads as one line. Validation lives at one point, so the
negative tests are a single focused suite rather than scattered across setters.

What becomes harder. Required-field enforcement is now runtime behaviour, so it
needs its own tests, one per required field, each confirming that omitting it
throws. Those tests do not exist for a constructor, because the compiler is the
test. The builder is also a second surface that can drift, so a reflective test
that asserts every product field is reachable from the builder is worth its
weight on a large type.

Techniques that apply.

- **Test Data Builder.** Nat Pryce's 2007 article proposes builders as the
  replacement for the Object Mother pattern in test fixtures, giving each test a
  default-valued builder it mutates in one dimension. The `make-it-easy` library
  by the same author is the reference implementation.
- **Golden-value round trip.** Build a product, read every accessor, compare
  against the field set handed to the builder. This catches the drifted-field
  failure mode directly.
- **Aliasing test.** Build twice from one builder, mutate a collection passed in,
  then assert both products are unaffected and are not the same instance. This is
  the only reliable guard against the shared-mutable-state failure.
- **Property-based testing.** Generate arbitrary valid field combinations and
  assert that `build()` either succeeds or throws a documented exception type,
  never a `NullPointerException`. See the property-first testing guidance in the
  testing family for generator design.
- **Fake builder as a spy for the GoF form.** Substitute a recording builder for
  the real one and assert on the sequence of step calls the director made. This
  tests the traversal without testing any output format, which is the whole
  point of separating them.

## 16. Observability signals

A builder is a construction-time concern, so most of its production signal is at
startup or at request entry rather than steady state.

What to record.

- A counter of `build()` validation rejections, tagged by which rule failed. In a
  healthy system this is flat at zero after deployment settles. A rising count
  after a config change is the first sign that a caller is sending a field
  combination nobody anticipated.
- The exception type and the failing field name in the rejection message. A
  rejection log line that says only "invalid configuration" costs an engineer an
  hour. Name the field.
- For GoF builders, a counter or trace span per step operation. On a healthy
  document conversion the ratio of step calls to source tokens is stable. A
  sudden change in that ratio means the source shape changed, which is a signal
  the parser will not give you.
- Construction latency, but only when the product does real work at build time
  such as compiling a regex, opening a connection, or reading a file. A pure
  field-copy builder does not deserve a timer.
- Allocation rate of builder instances on a hot path. If builder allocation is
  visible in an allocation profile, that is the signal to move to a constructor.

What healthy looks like on a dashboard. Rejection count flat at zero, build
latency a tight distribution with no tail, step-call ratios stable across
deploys. What failing looks like. A step in rejections immediately after a
release, which points at a drifted builder or a new caller. A latency tail on
`build()`, which almost always means work that belongs in a lazy accessor is
happening eagerly. Builder allocations climbing without a matching climb in
requests, which points at a retry loop rebuilding the same object.

Do not log the builder's field set wholesale. See the next dimension.

## 17. Security and privacy implications

Builder closes one attack surface and opens two.

Closed. Centralised validation is a security win. A single `build()` that
rejects malformed input is a single point an auditor can read in one sitting,
whereas validation spread across a dozen setters and three constructors is
where a bypass hides. The `Locale.Builder` documentation makes this argument in
the platform, contrasting the Builder's syntax checking against the constructors
that do not check. Where a type carries a security-relevant field such as a
permission set, a URL, or a file path, the builder is the correct place to
canonicalise and reject.

Opened. First, a builder holds every field in mutable memory for longer than a
constructor does, including secrets. A builder carrying an API token, a password
or a private key keeps that value reachable from the heap until the builder is
collected, which widens the window for a heap dump or a core file to capture it.
Where this matters, hold secrets as a `char[]` or an equivalent zeroable buffer
and clear it inside `build()`, and never store a secret in a builder that is
cached or long-lived.

Second, an auto-generated `toString()` on a builder is a credential leak waiting
for a log line. Many IDEs and code generators produce a `toString()` covering
every field. A debug log of the builder then writes the token to disk. Override
`toString()` on any builder holding a secret and redact those fields explicitly,
and apply the same rule to the observability signals above. Log which field
failed validation, never the value that failed it.

A third, quieter issue. Defensive copying at `build()` is a security property,
not only a correctness one. When a caller passes a mutable collection into a
builder and the builder stores the reference, the caller retains the ability to
change the product after construction, which defeats any check performed at
build time. A validated allowlist that the caller can append to after validation
is not a validated allowlist. Copy on the way in or on the way out, and say
which in the documentation.

On data residency and personal data the pattern is silent. Builder does not move
data across a boundary and imposes no retention behaviour of its own. Claiming
otherwise would be inventing a concern.

## Code examples

Java, the Bloch form with required fields, validation, and a defensive copy.

```java
import java.time.Duration;
import java.util.List;

public final class HttpCall {
    private final String uri;
    private final Duration timeout;
    private final List<String> headers;

    private HttpCall(Builder b) {
        this.uri = b.uri;
        this.timeout = b.timeout;
        this.headers = List.copyOf(b.headers);
    }

    public static Builder to(String uri) { return new Builder(uri); }

    public static final class Builder {
        private final String uri;
        private Duration timeout = Duration.ofSeconds(30);
        private final List<String> headers = new java.util.ArrayList<>();

        private Builder(String uri) {
            if (uri == null || uri.isBlank()) {
                throw new IllegalArgumentException("uri is required");
            }
            this.uri = uri;
        }

        public Builder timeout(Duration d) { this.timeout = d; return this; }

        public Builder header(String name, String value) {
            headers.add(name + "=" + value);
            return this;
        }

        public HttpCall build() {
            if (timeout.isNegative() || timeout.isZero()) {
                throw new IllegalStateException("timeout must be positive");
            }
            return new HttpCall(this);
        }
    }

    @Override public String toString() {
        return "HttpCall[" + uri + ", " + timeout + ", " + headers.size() + " headers]";
    }
}
```

TypeScript, a Step Builder where the compiler refuses `build()` before the URI is
supplied.

```typescript
type Call = { readonly uri: string; readonly timeoutMs: number };

interface NeedsUri {
  uri(value: string): Configurable;
}

interface Configurable {
  timeoutMs(value: number): Configurable;
  build(): Call;
}

class CallBuilder implements NeedsUri, Configurable {
  private _uri = "";
  private _timeoutMs = 30_000;

  static start(): NeedsUri { return new CallBuilder(); }

  uri(value: string): Configurable {
    if (!value) throw new Error("uri must be non-empty");
    this._uri = value;
    return this;
  }

  timeoutMs(value: number): Configurable {
    this._timeoutMs = value;
    return this;
  }

  build(): Call {
    if (this._timeoutMs <= 0) throw new Error("timeout must be positive");
    return Object.freeze({ uri: this._uri, timeoutMs: this._timeoutMs });
  }
}

const call = CallBuilder.start().uri("https://example.test").timeoutMs(5_000).build();
console.log(call);
```

Rust, the consuming builder. Each setter takes `self` by value and returns it, so
the type system prevents reuse of a partially built value after `build`.

```rust
#[derive(Debug)]
pub struct Call {
    uri: String,
    timeout_ms: u64,
    headers: Vec<(String, String)>,
}

pub struct CallBuilder {
    uri: String,
    timeout_ms: u64,
    headers: Vec<(String, String)>,
}

impl CallBuilder {
    pub fn new(uri: impl Into<String>) -> Self {
        CallBuilder { uri: uri.into(), timeout_ms: 30_000, headers: Vec::new() }
    }

    pub fn timeout_ms(mut self, ms: u64) -> Self {
        self.timeout_ms = ms;
        self
    }

    pub fn header(mut self, k: impl Into<String>, v: impl Into<String>) -> Self {
        self.headers.push((k.into(), v.into()));
        self
    }

    pub fn build(self) -> Result<Call, String> {
        if self.uri.is_empty() {
            return Err("uri is required".into());
        }
        if self.timeout_ms == 0 {
            return Err("timeout must be positive".into());
        }
        Ok(Call { uri: self.uri, timeout_ms: self.timeout_ms, headers: self.headers })
    }
}

fn main() {
    let call = CallBuilder::new("https://example.test")
        .timeout_ms(5_000)
        .header("accept", "application/json")
        .build();
    println!("{:?}", call);
}
```

Python, the GoF form, which is the variant that still earns its place in a
language with named and default arguments. One walk, two representations.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class DocBuilder(ABC):
    @abstractmethod
    def heading(self, text: str) -> None: ...
    @abstractmethod
    def paragraph(self, text: str) -> None: ...


class HtmlBuilder(DocBuilder):
    def __init__(self) -> None:
        self._parts: list[str] = []

    def heading(self, text: str) -> None:
        self._parts.append(f"<h1>{text}</h1>")

    def paragraph(self, text: str) -> None:
        self._parts.append(f"<p>{text}</p>")

    def result(self) -> str:
        return "\n".join(self._parts)


@dataclass
class Outline:
    headings: list[str] = field(default_factory=list)
    word_count: int = 0


class OutlineBuilder(DocBuilder):
    def __init__(self) -> None:
        self._outline = Outline()

    def heading(self, text: str) -> None:
        self._outline.headings.append(text)

    def paragraph(self, text: str) -> None:
        self._outline.word_count += len(text.split())

    def result(self) -> Outline:
        return self._outline


def render(tokens: list[tuple[str, str]], builder: DocBuilder) -> None:
    for kind, text in tokens:
        if kind == "h":
            builder.heading(text)
        else:
            builder.paragraph(text)


tokens = [("h", "Builder"), ("p", "One walk, many outputs."), ("p", "Two more words.")]

html = HtmlBuilder()
render(tokens, html)
print(html.result())

outline = OutlineBuilder()
render(tokens, outline)
print(outline.result())
```

Go, where the community idiom replaces the builder object with variadic
closures, per Cheney's Functional Options.

```go
package main

import (
	"errors"
	"fmt"
	"time"
)

type Call struct {
	URI     string
	Timeout time.Duration
	Headers map[string]string
}

type Option func(*Call)

func Timeout(d time.Duration) Option {
	return func(c *Call) { c.Timeout = d }
}

func Header(k, v string) Option {
	return func(c *Call) { c.Headers[k] = v }
}

func NewCall(uri string, opts ...Option) (*Call, error) {
	if uri == "" {
		return nil, errors.New("uri is required")
	}
	c := &Call{URI: uri, Timeout: 30 * time.Second, Headers: map[string]string{}}
	for _, opt := range opts {
		opt(c)
	}
	if c.Timeout <= 0 {
		return nil, errors.New("timeout must be positive")
	}
	return c, nil
}

func main() {
	c, err := NewCall("https://example.test", Timeout(5*time.Second), Header("accept", "application/json"))
	fmt.Println(c, err)
}
```

C# and Kotlin are omitted deliberately. Both have named arguments with defaults,
and in both the idiomatic answer to the Bloch problem is a record or data class
with default parameter values rather than a builder. Writing a builder in either
language reproduces a Java limitation that neither has, and would demonstrate
the misuse described in dimension 11 rather than the pattern.

## 18. References

Books.

- Gamma, Erich, Richard Helm, Ralph Johnson and John Vlissides. *Design
  Patterns. Elements of Reusable Object-Oriented Software*. Addison-Wesley,
  1994. ISBN 0-201-63361-2. Builder, chapter 3 Creational Patterns, page 97.
  Source of the intent statement, the four participants, the director role, and
  the Rich Text Format converter example.
- Bloch, Joshua. *Effective Java*, third edition. Addison-Wesley, 2018. ISBN
  978-0-13-468599-1. Chapter 2, Item 2, "Consider a builder when faced with many
  constructor parameters". Source of the telescoping constructor argument, the
  Nutrition Facts example, the guidance on more than a handful of parameters,
  and the recursive generic hierarchical builder idiom.
- Fowler, Martin. *Refactoring. Improving the Design of Existing Code*, second
  edition. Addison-Wesley, 2019. Named refactorings referenced in dimension 14,
  Introduce Parameter Object, Extract Class, and Replace Conditional with
  Polymorphism.

Specifications and primary documentation, each fetched and read on 2026-08-02.

- Oracle. *Java SE 21 API Specification*, interface `java.net.http.HttpRequest.Builder`.
  https://docs.oracle.com/en/java/javase/21/docs/api/java.net.http/java/net/http/HttpRequest.Builder.html
  Verified 2026-08-02. Quoted description "A builder of HTTP requests", and the
  `IllegalStateException` on a missing URI.
- Oracle. *Java SE 21 API Specification*, class `java.util.Locale.Builder`.
  https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Locale.Builder.html
  Verified 2026-08-02. Quoted description of syntax checking versus the
  constructors and `Locale.of()`.
- Google. *Protocol Buffers, Java Generated Code Guide*, section Builders.
  https://protobuf.dev/reference/java/java-generated/ Verified 2026-08-02.
  Quoted "Message objects ... are immutable" and "To construct a message object,
  you need to use a builder."
- Google. *Protocol Buffers, Python Generated Code Guide*.
  https://protobuf.dev/reference/python/python-generated/ Verified 2026-08-02.
  Confirms Python generates mutable message classes with direct property
  assignment and no builder, the language contrast used in dimension 4.
- Rust project. *Standard library documentation*, `std::process::Command`.
  https://doc.rust-lang.org/std/process/struct.Command.html Verified 2026-08-02.
  Quoted "Builder methods are provided to change these defaults and otherwise
  configure the process."
- Square. *OkHttp README*.
  https://raw.githubusercontent.com/square/okhttp/master/README.md Verified
  2026-08-02. GET example using `new Request.Builder().url(url).build()`,
  version 5.4.0 at time of verification.
- Swift project. *Swift Evolution proposal SE-0289, Result builders*.
  https://github.com/swiftlang/swift-evolution/blob/main/proposals/0289-result-builders.md
  Verified 2026-08-02. Status Implemented in Swift 5.4. Quoted introduction on
  implicitly building a result value from a sequence of components.

Articles.

- Cheney, Dave. "Functional options for friendly APIs", 17 October 2014,
  originally presented at dotGo 2014.
  https://dave.cheney.net/2014/10/17/functional-options-for-friendly-apis
  Verified 2026-08-02. Quoted "customisation of the Server is performed not with
  configuration parameters stored in a structure, but with functions which
  operate on the Server value itself", and the attribution to Rob Pike.
- Pike, Rob. "Self-referential functions and the design of options", January
  2014. http://commandcenter.blogspot.com.au/2014/01/self-referential-functions-and-design.html
  Cited by Cheney as the origin of the functional options idea. Link taken from
  the Cheney article verified 2026-08-02. The blog host was not independently
  fetched, so this reference is recorded as a secondary attribution rather than
  a primary read.
- Pryce, Nat. "Test Data Builders. an alternative to the Object Mother pattern",
  27 August 2007. http://www.natpryce.com/articles/000714.html Title, author and
  date confirmed by search on 2026-08-02. The host serves plain HTTP and refused
  a direct HTTPS fetch, so the article body was not independently retrieved. The
  companion library by the same author is at
  https://github.com/npryce/make-it-easy and is described as "A tiny framework
  that makes it easy to write Test Data Builders in Java".
