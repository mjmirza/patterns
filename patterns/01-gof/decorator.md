---
name: Decorator
slug: decorator
family: 01-gof
category: Structural
aliases: [Wrapper, Filter, Middleware, Smart Proxy]
first_described: "Gamma, Helm, Johnson, Vlissides 1994"
maturity: canonical
related: [proxy, adapter, facade, composite, chain-of-responsibility, strategy]
incompatible_with: []
verified: 2026-08-02
---

# Decorator

## 1. Name, aliases, and lineage

The canonical name is Decorator. It appears in the Gang of Four catalog as one of
the seven structural patterns, in Erich Gamma, Richard Helm, Ralph Johnson and
John Vlissides, *Design Patterns. Elements of Reusable Object-Oriented Software*,
Addison-Wesley, 1994, chapter 4 (Structural Patterns), Decorator. The catalog
records **Wrapper** as the book's own alternative name, and the same book uses
Wrapper as the alternative name for Adapter as well, which is the first source of
confusion a reader hits.

Four aliases are in real use, and each one carries a slightly different
connotation.

- **Wrapper.** The GoF alias. Broad and imprecise, because Adapter, Proxy and
  Decorator are all wrappers. When somebody says wrapper in a design discussion,
  ask which of the three they mean before agreeing to anything.
- **Filter.** The Java I/O name. `java.io.FilterInputStream` is the abstract
  decorator of the input stream hierarchy, and its documentation describes it as
  a class that wraps some other input stream, uses that stream as its source of
  data, possibly transforms the data on the way through, and otherwise passes all
  requests to the wrapped stream (Oracle, *Java SE 21 API Specification*,
  `java.io.FilterInputStream`,
  https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/io/FilterInputStream.html
  verified 2026-08-02). That description is a textbook statement of the pattern,
  written without ever using the word decorator.
- **Middleware.** The web-server community's name for a decorator over a request
  handler. The Rust `tower` crate is explicit about the equivalence. Its `Layer`
  trait documentation opens with the sentence that a `Layer` decorates a
  `Service`, transforming either the request or the response (`tower::Layer`,
  https://docs.rs/tower/latest/tower/trait.Layer.html verified 2026-08-02).
- **Smart Proxy.** Occasionally used for a decorator that adds caching, logging
  or reference counting. The name is unfortunate because Proxy is a distinct
  pattern with a distinct intent, see dimension 13.

There is a fifth thing that shares the word and is not this pattern at all. In
Python and in JavaScript, **decorator is a language keyword feature**, not a
structural pattern. Python's is specified in PEP 318, *Decorators for Functions
and Methods*, status Final, which defines `@dec` before a `def` as syntactic
sugar for rebinding the name to the result of calling `dec` on the function, so
that `@dec2` above `@dec1` above `def func` means `func = dec2(dec1(func))`
(https://peps.python.org/pep-0318/ verified 2026-08-02). JavaScript's is the
TC39 decorators proposal, at Stage 2.7 as of the verification date, which defines
decorators as functions called on classes, class elements or other syntax forms
during definition, and which explicitly constrains a decorator to replace a value
only with one of matching semantics rather than wrapping it in an unrelated
container (https://github.com/tc39/proposal-decorators verified 2026-08-02).

The relationship between the two is real but partial. A Python decorator that
returns a wrapping closure over the original function is the GoF pattern applied
to a function rather than an object, and the PEP 318 motivating cases are
`classmethod` and `staticmethod`, which transform rather than wrap. A Python
decorator that mutates the function's attributes and returns the same object, or
registers it in a table and returns it unchanged, is not the pattern at all. The
syntax names a call site, not a structure. Dimension 8 treats the function form
as a genuine variant, and dimension 11 records the mistake of assuming that every
at-sign is a decorator in the design sense.

## 2. Problem and context

An object needs an extra responsibility, only sometimes, only for some
instances, and the set of extra responsibilities keeps growing and keeps
combining.

The shape in a real codebase is recognisable long before anybody names it. There
is a type that does one job well. A data source, a request handler, a payment
gateway client, a text renderer, a repository. Then the requirements arrive one
at a time and each one is orthogonal to the last. Add a cache. Add retries. Add
metrics. Add an audit log. Add rate limiting. Add compression. Add a circuit
breaker. None of them changes what the object is, every one of them changes what
happens when you call it, and any subset of them might be wanted for a given
deployment, a given tenant, or a given test.

The two obvious answers both fail, and they fail in ways that are worth naming
because engineers reach for them by reflex.

The first answer is inheritance. Make `CachingRepository`, `RetryingRepository`,
`AuditedRepository`. It works for one responsibility. It collapses at two,
because now somebody wants caching and retries together and there is no
`CachingRetryingRepository`. With n independent responsibilities the class count
is bounded by 2^n, which is the combinatorial explosion the GoF catalog gives as
the motivation for the pattern. Inheritance also binds the choice at compile
time, so an instance cannot gain or lose a responsibility while the program runs.

The second answer is flags on the base class. Add `enableCache`, `maxRetries`
and `auditEnabled` fields and branch on them inside every method. The class count
stays at one, which feels like a win for about a month. Then the base class holds
every concern in the system, its methods grow a preamble of conditionals, its
test matrix grows multiplicatively, a change to the retry logic risks the audit
logic, and no team can own it because every team has code in it.

The context in which Decorator is the honest answer has four parts, and the
fourth is the one most often missing.

- The responsibilities are **independent of each other** and can be applied in
  more than one combination. If exactly one combination ever ships, a single
  class with the behaviour inlined is cheaper and reads better.
- The responsibilities are **transparent to the caller**. Client code that talks
  to the abstraction should not need to know whether a cache is present. If the
  caller has to know, the extra behaviour belongs in a wider interface, not in a
  decorator.
- The abstraction is **narrow**. This is the constraint that decides whether the
  pattern is pleasant or miserable in practice, and it is the subject of
  dimension 11's interface-bloat failure. A decorator must implement the whole
  component interface. A five-method interface costs a decorator four lines of
  forwarding. A forty-method interface costs it thirty-nine, per decorator, and
  every method added to the interface later breaks every decorator that exists,
  including the ones in other people's repositories.
- The base object's **class is not under your control, or should not be
  modified**. Decorator adds behaviour to an object you did not write and cannot
  subclass safely. This is the argument Joshua Bloch makes in *Effective Java*,
  3rd edition, Addison-Wesley, 2018, Item 18, "Favor composition over
  inheritance", where the `InstrumentedSet` wrapper works over any `Set`
  implementation and any of its constructors, which a subclass of one concrete
  set could never do. Bloch names the pattern by name in that item.

Outside those four conditions the pattern is overhead, and dimension 4 says so
concretely.

## 3. Forces

The pattern balances the following pressures. Each entry states which direction
the pattern pushes, because a pattern that sacrifices nothing has been described
wrongly.

- **Combinatorial class count.** Strongly favoured. This is the reason the
  pattern exists. With n independent behaviours, Decorator costs n classes where
  subclassing costs up to 2^n. The saving is the whole argument.
- **Runtime composability.** Strongly favoured. Behaviour is chosen when the
  object graph is built, not when the code is compiled, so a configuration file,
  a feature flag or a tenant record can decide which decorators wrap the base.
  Neither subclassing nor a compile-time mixin can do that.
- **Open Closed conformance.** Favoured. A new behaviour is a new class. No
  existing class is edited, including the base class, including classes in
  libraries you do not own.
- **Single Responsibility conformance.** Favoured. Each decorator holds one
  concern, so the retry logic and the caching logic never share a file and never
  share a test.
- **Interface width tolerance.** Sacrificed, and this is the largest hidden
  cost. Every decorator pays a forwarding tax proportional to the width of the
  component interface. The tax is paid once per decorator per method, forever,
  and it grows every time the interface grows. In a language without a delegation
  primitive the tax is hand-written code that a reviewer must read past to find
  the four lines that matter.
- **Cognitive load.** Sacrificed. A reader looking at a call site sees the
  component interface and cannot tell how many objects the call passes through,
  in what order, or whether one of them will stop the call early. The stack trace
  tells the truth, but only after the fact. The Java I/O hierarchy is the
  standing example, see dimension 9.
- **Debuggability.** Sacrificed. A stack trace through five decorators has five
  near-identical frames named read, handle or execute, and none of the frames
  says which concern it implements unless the class name does.
- **Latency.** Mildly sacrificed. Each layer costs one virtual or dynamic call
  and, in a managed runtime, one more object to keep alive. Irrelevant at web
  request granularity. Measurable in a per-byte read loop, which is exactly why
  `BufferedInputStream` exists to amortise it, and why a decorator over a hot
  inner loop deserves a benchmark rather than an assumption.
- **Memory.** Mildly sacrificed. One object per layer per instance. Decorating
  a million small objects individually is a real cost, and Flyweight is the
  pattern for that case.
- **Object identity.** Sacrificed, sharply. The decorated object is not the same
  object as the component. Reference equality fails, an `instanceof` test against
  the concrete component fails, and any code that reaches for a downcast fails.
  Systems that key caches or maps on object identity break silently when a
  decorator is introduced.
- **Operability.** Mixed. The decorator is the natural home for metrics,
  tracing and logging, which improves operability enormously. But the layering
  itself is invisible at runtime unless something reports it, so an incident can
  turn on the question of which decorators were installed, and nothing answers
  it. Dimension 16 is about closing that gap.
- **Team topology.** Favoured. A platform team owns the component interface and
  the base implementation. Product teams ship decorators in their own modules on
  their own schedule. The seam is a compile-time interface and a runtime
  composition step, which is about as clean a boundary as a monolith offers.
- **Cost of change.** Favoured for adding a behaviour. Sharply sacrificed for
  changing the component interface, because every decorator everywhere must be
  updated, including decorators in downstream repositories that you cannot see.

## 4. Applicability and non-applicability

Reach for Decorator when the following hold.

- Responsibilities must be added to individual objects, dynamically and
  transparently, without affecting other objects of the same class.
- Responsibilities can be withdrawn as easily as added, for example a debug
  tracing layer that exists only in a development configuration.
- The set of behaviours is open ended, so subclassing would produce an
  impractical number of combinations, or the combinations are chosen by
  configuration rather than by code.
- The class to be extended is final, sealed, generated, or owned by a library,
  so subclassing is impossible or unwise.
- The behaviours are cross-cutting in nature. Caching, retrying, timing, logging,
  authorisation, compression, encryption, rate limiting and buffering are the
  recurring set, and every one of them is orthogonal to the domain operation it
  wraps.
- A pipeline is the natural mental model, meaning the caller thinks of the work
  as passing through stages that each do a little and delegate the rest.

Do NOT reach for Decorator in these cases. This non-applicability list is the
more useful of the two, and the reason attached to each item matters more than
the item.

- **The component interface is wide.** An interface with twenty or more members
  makes every decorator a wall of forwarding methods. The ratio of substance to
  noise in a decorator class drops below the point where a reviewer will read it
  carefully, and the pattern starts hiding bugs rather than isolating concerns.
  Narrow the interface first, or use a language-level delegation primitive, or
  choose a different pattern. See dimension 11 for the observable symptom.
- **Exactly one combination will ever ship.** If the production wiring is always
  cache over retry over base and there is no second configuration, the layering
  is speculative. Write the behaviour into one class and delete two files. Cross
  reference the code smell family entry on speculative generality.
- **Clients need to know which decorators are present.** The moment code calls
  `if (component instanceof CachingRepository)` the transparency assumption is
  gone, and with it the reason to use the pattern. Either widen the interface
  with an honest capability query, or admit that the extra behaviour is part of
  the type and model it as such.
- **The added behaviour changes the contract.** A decorator that makes a
  previously synchronous method asynchronous, that narrows the accepted input
  range, or that starts throwing where the component did not, is a Liskov
  violation wearing a wrapper. Callers written against the component will break.
  The .NET `GZipStream` case in dimension 11 is this failure inside a standard
  library, and it is instructive precisely because the library authors had no
  better option available to them.
- **Ordering between the behaviours is load bearing and unstated.** Retry outside
  cache and cache outside retry are different systems with different failure
  characteristics. If the correct order is not obvious from the names, and
  nothing enforces it, the pattern has handed the team a hazard. Either encode
  the order in a builder that only permits valid stacks, or use a pipeline
  abstraction where the order is data and can be validated.
- **The composition must be inspected or reordered at runtime.** A linked chain
  of wrappers is difficult to introspect. You cannot easily ask a decorated
  object what it is wrapped in, remove the third layer, or reorder two. If those
  operations are requirements, model the stages as a list and run them with an
  interceptor loop, which is the shape gRPC and most RPC frameworks chose.
- **Object identity or equality is load bearing.** If the system keys anything on
  reference identity, or if the component overrides equality in a way callers
  depend on, wrapping breaks it. A decorator that forwards `equals` is not equal
  to the thing it wraps in the reverse direction, so the relation stops being
  symmetric, which quietly corrupts hash-based collections.
- **The concern is genuinely one function, in a language with first-class
  functions.** Wrapping a single-method interface in a class hierarchy when a
  higher-order function would do is ceremony. In Go, TypeScript, Python, Rust,
  Kotlin and modern Java, a function that takes a handler and returns a handler
  is the pattern with none of the classes. See dimension 8.
- **The behaviour applies to every instance, always.** That is not a decorator,
  that is a requirement of the component, and it belongs in the component. A
  decorator that is never absent is an obfuscated part of the base class.
- **You need to control access rather than add behaviour.** Lazy loading, remote
  access, and access control are Proxy, which is a different intent expressed in
  the same structure. Dimension 13 has the discriminating table.

## 5. Structure

Four participants, named by the role each plays rather than by a class name.

- **Component.** The abstraction that both the plain object and every decorator
  implement. It defines the operations a client may call. Its width is the most
  important design decision in the whole pattern, because every decorator pays
  for every member. Keep it as narrow as the client genuinely needs.
- **ConcreteComponent.** The plain implementation that does the real work.
  It has no knowledge that decorators exist, and it must not, because that
  knowledge would reintroduce the coupling the pattern removes. There may be
  several ConcreteComponents, and any decorator works over any of them, which is
  the reuse property Bloch's `InstrumentedSet` argument turns on.
- **Decorator.** An abstract class or a shared base that implements Component and
  holds a reference to a Component. Its default implementation of every operation
  forwards to the held Component and returns the result unchanged. This class
  exists so that ConcreteDecorators do not each rewrite the forwarding. The
  `java.io.FilterInputStream` class is exactly this participant, holding a single
  protected field `in` of type `InputStream`, described in the API specification
  as the input stream to be filtered
  (https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/io/FilterInputStream.html
  verified 2026-08-02). In a language with a delegation keyword this participant
  disappears, see dimension 8.
- **ConcreteDecorator.** Extends Decorator and overrides the small number of
  operations where it has something to add. Its added behaviour goes before the
  forwarding call, after it, around it, or in place of it, and which of those
  four it chooses is the most useful thing its documentation can say.

Relationships. The Decorator has an association to Component, not to
ConcreteComponent, and that single fact is what allows decorators to stack. A
decorator's held Component may itself be another decorator, so the composition is
a linked list terminating in a ConcreteComponent. The recursion is unbounded in
the type system and bounded only by whatever builds the stack.

Two structural properties follow, and both surprise people.

First, the pattern is a degenerate Composite. Both are recursive compositions
over a shared interface. Composite holds many children and combines their
results. Decorator holds exactly one child and adds behaviour around it. The GoF
catalog states the relationship in the Decorator entry's Related Patterns
section, and it is the reason the two entries sit next to each other in chapter
4.

Second, the ConcreteComponent is not required to sit at the bottom of a stack
deeper than one. A single decorator over a bare component is a valid and common
shape, and it is where most real systems start.

## 6. ASCII structure diagram

```
   +--------------------------+
   |        Component         |   <<interface>>
   |--------------------------|
   | + operation()            |
   +--------------------------+
        ^                  ^
        | implements       | implements
        |                  |
+---------------------+   +----------------------------------+
| ConcreteComponent   |   |          Decorator               |
|---------------------|   |----------------------------------|
| + operation()       |   | # wrapped  <>--- points back to  |
| (does the real work)|   |                  Component       |
+---------------------+   | + operation() forwards to wrapped|
                          +----------------------------------+
                                    ^                ^
                                    | extends        | extends
                                    |                |
                    +-------------------------+  +------------------------+
                    |  ConcreteDecoratorA     |  |  ConcreteDecoratorB    |
                    |-------------------------|  |------------------------|
                    | + operation()           |  | + operation()          |
                    |   pre(), then forward   |  |   forward, then post() |
                    +-------------------------+  +------------------------+

   The diamond on Decorator points back at Component, not at
   ConcreteComponent. That single edge is what lets decorators stack.
```

A stack at runtime is a chain, not a tree.

```
   client ---> [ Metrics ] ---> [ Retry ] ---> [ Cache ] ---> [ HttpRepo ]
                  ^                ^              ^               ^
                  |                |              |               |
             decorator        decorator      decorator     concrete component

   Every box satisfies Component. The client holds only the leftmost
   reference and cannot see the rest of the chain.
```

## 7. Dynamics

The runtime property that separates Decorator from every other wrapper is that
each layer gets two chances to act. It runs code on the way in, delegates, and
runs code on the way out. A decorator may also decline to delegate, which stops
the call early, and that is the case most worth drawing because it is the one
that produces surprising production behaviour.

Normal pass-through, three layers.

```
Client        Metrics         Retry          Cache          HttpRepo
  |              |              |              |               |
  |-- get(k) --->|              |              |               |
  |              |-- start timer|              |               |
  |              |-- get(k) --->|              |               |
  |              |              |-- attempt 1  |               |
  |              |              |-- get(k) --->|               |
  |              |              |              |-- miss        |
  |              |              |              |-- get(k) ---->|
  |              |              |              |               |-- I/O
  |              |              |              |<-- value -----|
  |              |              |              |-- store(k,v)  |
  |              |              |<-- value ----|               |
  |              |<-- value ----|              |               |
  |              |-- stop timer, record        |               |
  |<-- value ----|              |              |               |
```

Early return at the cache layer. The two innermost participants are never
touched, which is the entire point, and also the reason a metric recorded at the
outermost layer says nothing about backend load.

```
Client        Metrics         Retry          Cache          HttpRepo
  |              |              |              |               |
  |-- get(k) --->|              |              |               |
  |              |-- get(k) --->|              |               |
  |              |              |-- get(k) --->|               |
  |              |              |              |-- HIT         |
  |              |              |<-- value ----|               |
  |              |<-- value ----|              |    (never called)
  |<-- value ----|              |              |               |
```

Failure travelling outward through a retrying layer. The Retry decorator calls
its inner component more than once for one outer call, so any counter placed
inside it counts differently from one placed outside it.

```
Client        Metrics         Retry          Cache          HttpRepo
  |              |              |              |               |
  |-- get(k) --->|              |              |               |
  |              |-- get(k) --->|              |               |
  |              |              |-- attempt 1 -+-------------->|
  |              |              |<-- timeout --+---------------|
  |              |              |-- backoff    |               |
  |              |              |-- attempt 2 -+-------------->|
  |              |              |<-- value ----+---------------|
  |              |<-- value ----|              |               |
  |<-- value ----|              |              |               |

  One client call, one Metrics observation, two backend calls.
  A dashboard built only on the Metrics layer under-reports load
  by the retry factor, which is dimension 16's warning.
```

Two ordering facts follow from these flows and are worth stating plainly because
teams argue about them without naming them.

Retry outside cache means a cache hit skips the retry logic entirely and a
backend failure is retried against a cold cache. Cache outside retry means a
cache hit skips the retry logic as well, but a successful retry populates the
cache, so the second caller pays nothing. The two stacks have different failure
multiplication and different cache hit ratios under partial outage. Neither is
universally correct, and neither is discoverable from the code without reading
the wiring.

Construction order is the reverse of call order. A nested construction of metrics
over retry over cache over base reads inside-out while the call travels
outside-in. Every builder API for decorator stacks exists to hide that inversion,
and the `tower::ServiceBuilder` type is the well-known example.

## 8. Implementation variants

**Classical abstract decorator base.** An abstract class implements Component,
holds a Component field, and forwards every method. ConcreteDecorators extend it
and override selectively. This is the GoF shape and the `java.io` shape. Its
merit is that the forwarding tax is paid once for the whole hierarchy. Its cost
is that it consumes the single-inheritance slot in languages that have one, and
that a ConcreteDecorator which forgets to call the base method silently drops the
rest of the chain, a failure with no compile-time signal.

**Interface plus explicit forwarding class.** Bloch's shape in *Effective Java*
Item 18. A `ForwardingSet` implements `Set` by holding a `Set` and forwarding
every method, and `InstrumentedSet` extends the forwarding class to add counting.
The same shape as the classical form, but the vocabulary differs because the
forwarding class is presented as a reusable component in its own right rather
than as an abstract member of a pattern. The practical advantage is that one
forwarding class can serve decorators written by unrelated authors.

**Delegation keyword.** The Kotlin `by` clause generates the forwarding methods
at compile time, so the decorator declares only what it changes. This removes the
forwarding tax entirely and is the largest quality-of-life difference between
languages for this pattern. C# has no equivalent and pays the tax by hand. Go
struct embedding achieves a similar effect by promoting the embedded type's
methods, with the difference that Go promotion is not virtual, so an embedded
value cannot call back into the outer type's override.

**Function decorator.** In a language with first-class functions, when Component
is a single-method interface, a decorator is a function from Component to
Component. Go middleware of the form `func(http.Handler) http.Handler` is the
archetype, and the standard library ships instances of it. The
`http.StripPrefix(prefix string, h Handler) Handler` function returns a handler
that removes a prefix from the request path and calls the handler it was given
(`net/http`, https://pkg.go.dev/net/http#StripPrefix verified 2026-08-02). This
variant has the lowest ceremony, the best composability, and the worst
introspectability, because a closure has no name, no type identity and no fields
to inspect. Prefer it for behaviour that will never need to be found again at
runtime.

**Python function decorator syntax.** The PEP 318 sugar applied to a function
that returns a wrapping closure is the function-decorator variant with better
ergonomics at the definition site. The standard idiom pairs it with
`functools.wraps` so the wrapper copies the wrapped function's name, docstring
and module, which matters because otherwise every decorated function in a
traceback is called `wrapper`. Applying the same syntax to return the original
object unchanged, for registration or attribute mutation, is a different
technique that borrows the syntax and not the pattern.

**Parameterised decorator factory.** A function that takes configuration and
returns a decorator. A call such as `retry(times=3)` returns the decorator, which
then wraps the component. Two levels of call, one level of structure. This is how
nearly all real middleware is exposed, because a decorator with no configuration
is rare outside textbooks.

**Ordered builder.** Rather than exposing raw constructors, the library exposes a
builder that accepts layers and applies them in a defined direction. The
`tower::ServiceBuilder` type does this so that the reading order of the code
matches the request order rather than the construction order. The builder can
also reject invalid orderings, which is the only mechanical defence against the
ordering hazard from dimension 4.

**Interceptor list instead of a chain.** Instead of nesting objects, hold an
ordered list of stage objects and run them in a loop, passing an explicit
continuation. This is what gRPC interceptors and most RPC frameworks use. It is
not the GoF structure, and that is the point. The list is data, so it can be
inspected, logged, reordered and validated, which the nested chain cannot. Choose
it when the composition itself needs to be a first-class value. The cost is that
the stages are no longer instances of Component, so they cannot be passed
anywhere a Component is expected.

**Dynamic proxy generation.** The `java.lang.reflect.Proxy` class, the .NET
`DispatchProxy` type, and Python `__getattr__` forwarding all generate the
forwarding behaviour at runtime rather than requiring it in source. This
eliminates the forwarding tax on a wide interface, which is the one case where it
is genuinely worth the cost. The cost is real. Static type checking of the
decorator disappears, method dispatch becomes reflective and slower, stack traces
gain synthetic frames, and ahead-of-time compiled or reflection-restricted
environments may refuse to run it. Use it for cross-cutting concerns over wide
service interfaces, not as a default.

**Compile-time generation.** Source generators, annotation processors and macros
can emit the forwarding class from the interface definition. Rust derive macros
and delegation crates, Java annotation processors, and C# source generators all
sit here. Same benefit as dynamic proxies with none of the runtime cost, at the
price of build complexity and generated code a debugger has to step through.

**Language note on Rust.** Rust has no inheritance, so the classical shape does
not translate directly. The idiomatic form is a generic struct that owns an inner
value bounded by a trait, and implements the same trait by calling through to the
inner value. The `tower::Layer` and `tower::Service` traits are exactly that
shape, and the wrapping operation is the `Layer` trait method
`fn layer(&self, inner: S) -> Self::Service`, which makes the wrapping explicit
in the type system (https://docs.rs/tower/latest/tower/trait.Layer.html verified
2026-08-02). The result is a decorator stack whose full composition is a single
concrete type, resolved and inlinable at compile time, which removes the
per-layer dynamic dispatch cost that every other language pays.

## 9. Known production uses

**Java standard library, the `java.io` stream hierarchy.** `FilterInputStream`
and `FilterOutputStream` are the abstract decorators, and `BufferedInputStream`,
`DataInputStream`, `PushbackInputStream` and the compression streams are the
concrete ones. The API specification for `FilterInputStream` describes it as
wrapping another input stream, using it as the source of data, possibly
transforming that data, and passing all requests through to the wrapped stream
(Oracle, *Java SE 21 API Specification*,
https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/io/FilterInputStream.html
verified 2026-08-02). The Oracle tutorial names the pattern directly, stating
that the Decorator Pattern is one of the twenty-three Gang of Four patterns and
that the Java I/O API uses it to extend or modify the behaviour of some of its
classes, and demonstrating that switching a file to compressed storage is a small
change because `GZIPInputStream` and `GZIPOutputStream` slot into an existing
stack (Oracle, *dev.java*, "Decorating I/O Streams",
https://dev.java/learn/java-io/reading-writing/decorating/ verified 2026-08-02).

Why this is the canonical example, and also the canonical complaint. It is
canonical because the pattern is used as designed, in a library every Java
developer has read, with a genuine combinatorial requirement. Buffering,
character conversion, compression, checksumming, object serialisation and
pushback are mutually orthogonal, and the number of useful combinations is far
larger than the number of classes needed to express them. It is the canonical
complaint for three reasons that show up in every discussion of the API. First,
the reading order is inverted, so a nested construction of a data stream over a
buffered stream over a file stream must be read from the inside out to understand
what happens first, and from the outside in to understand what the client sees.
Second, nothing in the type system says which combinations are sensible, so
wrapping a `BufferedInputStream` around a `BufferedInputStream` compiles and
silently double-buffers, and forgetting to buffer at all compiles and silently
performs one system call per byte. Third, the abstract decorators sit in a class
hierarchy that also carries the `InputStream` concrete default methods, so a
subclass that overrides the three-argument `read` but not the no-argument one
behaves differently from a subclass that does the reverse. The trade is real and
the library made the right call given the alternatives available in 1996, but a
reader who has been bitten by all three is entitled to their complaint.

**Jakarta Servlet, `ServletRequestWrapper` and `ServletResponseWrapper`.** The
specification provides these classes as convenient implementations of the
`ServletRequest` and `ServletResponse` interfaces that developers subclass to
adapt the request or response, with every method defaulting to a call through to
the wrapped object (Jakarta EE, *Jakarta Servlet 6.0 API documentation*,
`jakarta.servlet.ServletRequestWrapper`,
https://jakarta.ee/specifications/servlet/6.0/apidocs/jakarta.servlet/jakarta/servlet/servletrequestwrapper
verified 2026-08-02). Chapter 6 of the Jakarta Servlet 6.0 specification, titled
Filtering, covers wrapping requests and responses as one of its main concepts
(https://jakarta.ee/specifications/servlet/6.0/jakarta-servlet-spec-6.0 verified
2026-08-02). This is a rare case of a specification shipping the abstract
Decorator participant as public API and telling implementors to extend it.

**Python standard library, the `io` module layering.** `BufferedReader` is
documented as a buffered binary stream providing higher-level access to a
readable raw binary stream, keeping a larger amount of data in an internal buffer
than the caller requested, and `TextIOWrapper` is documented as a buffered text
interface to a buffered raw stream (Python Software Foundation, *Python 3
documentation*, `io`, https://docs.python.org/3/library/io.html verified
2026-08-02). The default text-mode `open()` produces a `TextIOWrapper` over a
`BufferedReader` over a `FileIO`, which is a three-layer decorator stack that
most Python programmers use daily without ever constructing.

**The .NET `System.IO.Compression.GZipStream` class.** It is declared as a
subclass of `System.IO.Stream`, its constructors take a `Stream` plus a
compression mode or level, and it exposes a `BaseStream` property documented as
getting a reference to the underlying stream (Microsoft, *.NET API
documentation*,
https://learn.microsoft.com/en-us/dotnet/api/system.io.compression.gzipstream
verified 2026-08-02). Every element of the pattern is present, including the
public accessor for the wrapped component that the GoF structure does not
require and that most decorators omit.

**Rust, the `tower` middleware crate family.** The `tower::Layer` trait documents
itself as decorating a `Service` and transforming either the request or the
response, and its `layer` method takes an inner service and returns the wrapped
one (https://docs.rs/tower/latest/tower/trait.Layer.html verified 2026-08-02).
This is the pattern used as the composition model for an entire HTTP stack rather
than for a single concern, and it is the clearest production evidence that
middleware and Decorator are the same idea under two names.

**Go standard library, `net/http` handler wrapping.** The `http.Handler`
interface requires one method, `ServeHTTP` taking a `ResponseWriter` and a
request pointer, and the `http.StripPrefix` function returns a handler that
modifies the request and then calls the handler it wraps
(https://pkg.go.dev/net/http#StripPrefix verified 2026-08-02). The function form
of the pattern, in the standard library, with a component interface narrow enough
that the forwarding tax is zero.

## 10. Consequences

Positive.

- Behaviour composes at runtime rather than at compile time, so the same binary
  serves configurations that a subclassing design would need separate builds for.
- The class count grows linearly with the number of behaviours rather than
  exponentially with the number of combinations.
- Each behaviour lives in one class with one reason to change and one test file,
  which is the Single Responsibility Principle achieved rather than aspired to.
- Behaviour can be added to types you do not own, including final and sealed
  classes, which subclassing cannot do.
- The base implementation stays ignorant of every concern layered over it, so it
  remains testable in isolation and reusable in contexts where the concerns do
  not apply.
- A decorator is a natural instrumentation point. Every call passes through it,
  so timing, counting and tracing land in one place and apply to every
  implementation of the component.
- Behaviour can be withdrawn as cheaply as it was added, by removing one line of
  wiring, which makes it practical to run a diagnostic layer in one environment
  and not another.

Negative.

- The forwarding tax. Every decorator implements every member of the component
  interface, and the ratio of substance to forwarding falls as the interface
  widens.
- The composition is invisible at the call site. Reading the client tells you
  nothing about what will actually run, and reading one decorator tells you
  nothing about its neighbours.
- Ordering is load bearing and mechanically unenforced. Two stacks containing the
  same decorators in different orders are different systems, and nothing in the
  type system says so.
- Object identity is destroyed. The decorated object is a different object,
  so identity comparisons, identity-keyed maps and downcasts to the concrete
  component all fail.
- Debugging is harder. Stack traces gain a frame per layer, and the frames carry
  the same method name, so the trace is long and low in information.
- Small per-call and per-object overhead, which is negligible at coarse
  granularity and can matter at fine granularity.
- A decorator that forgets to delegate silently truncates the chain, and no
  compiler and no test that exercises only the outer layer will notice.
- Widening the component interface later is expensive in proportion to the number
  of decorators in existence, including ones outside your repository.

## 11. Failure modes and misuse

**Interface bloat makes decorators unreadable and unmaintainable.** Symptom. A
decorator class is four hundred lines long, three hundred and eighty of which are
one-line methods that do nothing but call the same method on the wrapped field.
Code review comments on that file stop appearing. A method added to the component
interface causes a compile failure in eleven decorator classes across four
repositories, and the fix in each is a copy-pasted forwarding line that nobody
reads. Cause. The component interface carries every operation the concrete
component happens to offer rather than the operations clients actually call, so
the pattern's per-decorator cost was multiplied by an interface width that was
never a design decision. Fix, in order of preference. Segregate the interface so
decorators implement only the narrow slice they participate in, per the Interface
Segregation Principle. Use a language delegation primitive such as the Kotlin
`by` clause or Go embedding. Generate the forwarding class from the interface
with a source generator or annotation processor. As a last resort use a dynamic
proxy, accepting the loss of static checking. The academic treatment of this
constraint is Virginia Niculescu, Adrian Sterca and Darius Bufnea, "Should
Decorators Preserve the Component Interface?", 2020, which argues that the
classical requirement to preserve a single implicitly defined component interface
is restrictive and proposes variants that relax it
(https://arxiv.org/abs/2009.06414 verified 2026-08-02).

**A decorator narrows the component contract, breaking substitutability.**
Symptom. Code that worked against the plain component throws
`NotSupportedException` or `UnsupportedOperationException` once a decorator is
introduced, and only on some code paths, so it passes review and fails in
production on the seek-heavy path. Cause. The decorator cannot honestly implement
every member of the interface it inherited. The .NET `GZipStream` class documents
`Length` and `Position` as unsupported properties that always throw
`NotSupportedException`, and `Seek` and `SetLength` likewise, because a
compression stream has no seekable position that would mean anything
(https://learn.microsoft.com/en-us/dotnet/api/system.io.compression.gzipstream
verified 2026-08-02). This is not a bug in .NET. It is the honest consequence of
a component interface that assumed capabilities not every decorator can provide,
which is why the interface-bloat item above is the deeper problem. Fix. Split
capability into separate interfaces so a non-seekable stream is not required to
pretend, or expose a capability query the caller can check, which .NET does with
`CanSeek`. Callers must be written to ask.

**A decorator forgets to delegate and silently truncates the chain.** Symptom.
A metric is missing, a cache never populates, or an audit log has gaps, and the
gap correlates with one particular request type rather than with load. Cause. One
branch inside one decorator returns early without calling the wrapped component,
usually a validation shortcut or an error path added later. Fix. Write a
chain-integrity test that composes a recording sentinel as the innermost
component and asserts it was reached, for every public operation and for the
error paths as well as the happy path. See dimension 15.

**Ordering is wrong and nobody notices for months.** Symptom. Retry counts in the
dashboard are far lower than backend error rates suggest, or a circuit breaker
never opens, or an authorisation decision is cached across tenants. Cause. The
stack was assembled in an order nobody reasoned about, usually by appending the
newest concern to whichever end of the builder was convenient. Cache outside
authorisation is the dangerous instance of this, because it caches a decision
made for one principal and serves it to another. Fix. Encode the order in a
builder that accepts layers in one defined direction and rejects known-bad
adjacencies, and write one test per invariant, for example that no authorisation
decision is reachable from a cache lookup.

**Identity comparison and downcasting break on introduction.** Symptom. A feature
works in unit tests and fails in the wired application with a
`ClassCastException` or with an object that is absent from a map it was placed
in. Cause. Somewhere downstream, code compares the repository against a known
instance by reference, or casts the component to the concrete type to reach a
member the interface does not expose. Fix. Remove the downcast by widening the
interface honestly, or provide an unwrapping accessor on the decorator base as
.NET does with `BaseStream`, and stop keying anything on reference identity.

**Unbounded stack depth from dynamic composition.** Symptom. Stack overflow in
production under a configuration nobody tested, or a stack trace thousands of
frames deep. Cause. Decorators applied in a loop over a configuration list, with
no cap, or a decorator accidentally wrapping itself because the wiring code read
from a mutable registry it was also writing to. Fix. Cap the depth at
composition time and assert the cap in a test, and make the wiring code build
from an immutable description.

**Double wrapping of the same concern.** Symptom. Every log line appears twice,
or throughput drops by half with no code change, or a retry budget of three
produces nine backend calls. Cause. Two composition sites each added the same
decorator, usually a framework auto-configuration plus a manual registration.
Retry outside retry is the multiplicative case and is the one that takes down a
backend. Fix. Make decorators detect and refuse duplicate wrapping where it is
cheap to do so, or centralise composition in one place and forbid ad hoc wrapping
by convention plus a startup assertion.

**The Python at-sign mistaken for the pattern.** Symptom. A design document
claims a module uses the Decorator pattern, and the code contains only
`@dataclass`, `@property` and a routing decorator, none of which wraps anything
in the structural sense. Discussion of the design then proceeds on a false
premise. Cause. The language feature and the pattern share a name and are related
but not identical. PEP 318 defines the syntax as a transformation applied at
definition time, which may or may not return a wrapper
(https://peps.python.org/pep-0318/ verified 2026-08-02). Fix. In design
discussion, name the structure rather than the syntax. Ask whether the returned
object satisfies the same interface and delegates to the original. If it does, it
is the pattern. If it registers, mutates or replaces, it is not.

**Resource lifetime confusion across layers.** Symptom. A file handle leaks, or a
stream is closed twice, or data written through a decorator is lost because the
process exited before a buffer was flushed. Cause. Ownership of the wrapped
component is undefined. Closing the outer decorator may or may not close the
inner one, and different layers in the same stack may disagree. Microsoft made
this explicit by adding constructor overloads with a `leaveOpen` flag precisely
because the default was ambiguous
(https://learn.microsoft.com/en-us/dotnet/api/system.io.compression.gzipstream
verified 2026-08-02). Fix. State the ownership rule in the decorator's
documentation, make it a constructor parameter where the answer is genuinely
per-instance, and test that a buffering layer flushes on close.

**Decorator used where Proxy was meant, and the object is never really there.**
Symptom. An operation that clients believe is local performs a network call, and
latency percentiles are inexplicable from reading the code. Cause. A remote or
lazy-loading wrapper was described and reviewed as a decorator, so nobody
questioned the assumption that the inner component was already constructed and
cheap. Fix. Name it a Proxy, document the access-control or laziness semantics,
and hold it to Proxy's expectations rather than Decorator's. Dimension 13 has the
discriminating criteria.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Decorator | Subclassing per combination | Flags on one class | Strategy | Aspect-oriented advice | Interceptor list |
|---|---|---|---|---|---|---|
| Class count for n behaviours | n classes | Up to 2^n classes | 1 class, n branches | n classes, one slot | n aspects | n stages |
| Arbitrary combinations | Any subset, any order | Only the ones written | Any subset | One at a time per slot | Any, by pointcut | Any subset, order is data |
| Runtime composition | Yes, at wiring time | No, fixed at compile time | Yes, by flag value | Yes, by setter | Usually load time only | Yes, list is mutable |
| Forwarding tax | High, grows with interface | None | None | None | None | None |
| Call-site readability | Poor, chain is invisible | Good, one concrete name | Good, one class to read | Good, one delegate | Very poor, no call-site trace | Fair, list is inspectable |
| Introspecting the composition | Poor, chain is opaque | Trivial, it is the type | Trivial, read the flags | Fair, read the field | Poor, applied implicitly | Strong, the list is a value |
| Ordering safety | Unenforced, silent hazard | Fixed by the class | Fixed by branch order | Not applicable | Precedence rules, obscure | Enforceable by validation |
| Preserves object identity | No, wraps | Yes, one object | Yes, one object | Yes, one object | Usually yes | Yes, subject unwrapped |
| Latency per call | One dispatch per layer | Direct call | One branch per flag | One dispatch | Near zero after compilation | One iteration per stage |
| Testability of one behaviour | Strong, test in isolation | Weak, coupled to base | Weak, flag matrix | Strong | Weak, needs the aspect compiler | Strong |
| Cost of a new behaviour | One class, no edits | Doubles the class count | Edit the shared class | One class if the slot fits | One aspect, no edits | One stage, no edits |
| Team topology | Strong, module boundary | Poor, shared hierarchy | Poor, shared file hotspot | Good | Poor, invisible coupling | Good |
| Tooling and build cost | None | None | None | None | Aspect compiler or agent | None |

Reading of the table. Decorator wins where behaviours are orthogonal, numerous,
and chosen at runtime, and where the component interface is narrow enough that
the forwarding tax stays small. Subclassing wins when there is one combination
and it is permanent. Flags on one class win only for two or three behaviours in a
small class, and stop winning abruptly. Strategy wins when the variation is one
pluggable decision rather than a stack of independent additions. Aspect-oriented
advice wins on ceremony and loses badly on traceability, which is why it has
receded outside a few enterprise Java estates. An interceptor list wins whenever
the composition itself must be inspected, validated or reordered, and it is the
right choice for framework-level middleware for exactly that reason.

## 13. Related and incompatible patterns

The discriminating question for the four wrapping patterns is not what the code
looks like, because all four look alike. It is what the wrapper is for, and
whether the wrapper's interface matches the wrapped object's interface.

| Pattern | Interface of wrapper vs wrapped | Purpose | Stacks | What the client expects |
|---|---|---|---|---|
| Decorator | Same interface | Add behaviour around the same operation | Yes, by design | To behave like the component |
| Proxy | Same interface | Control access to the object, lazily, remotely, protectively | Rarely, one is usual | To behave like the component |
| Adapter | Different interface | Make an incompatible interface usable by a client | No, one conversion | The target interface, not the source |
| Facade | New, narrower interface over many objects | Simplify a subsystem | No, it is a front | A simpler surface than the subsystem |
| Chain of Responsibility | Same handler interface | Find a handler that will process the request | Yes, a chain | One of the chain to handle it |

The differences that matter in practice.

- **Decorator versus Proxy.** Same structure, same interface, different reason.
  A decorator adds behaviour to an object that is already there and always
  delegates to it, because the delegation is the point. A proxy controls access
  to an object that may not exist yet, may live on another machine, or may be
  forbidden to this caller, and it may legitimately never delegate at all. The
  operational tell is that a proxy usually constructs or reaches the subject,
  while a decorator receives it. The design tell is that removing a decorator
  should leave a working system with less behaviour, while removing a proxy
  usually leaves a system that cannot reach its subject. The `tower` layers are
  decorators. A lazy-loading ORM entity reference is a proxy.
- **Decorator versus Adapter.** Adapter changes the interface, Decorator
  preserves it. That is the whole distinction and it is decisive. If the client
  could have called the wrapped object directly and gotten a correct answer with
  less behaviour, it is a decorator. If the client could not have called it at
  all because the signatures do not match, it is an adapter. Adapters do not
  stack, because after one conversion the interface is already the target.
- **Decorator versus Facade.** Facade introduces a new, simpler interface over
  several collaborating objects, and clients call the facade instead of the
  subsystem. Decorator preserves one interface over one object, and clients
  cannot tell the difference. A facade reduces the number of things a client
  talks to. A decorator changes what happens when the client talks to the one
  thing it already had.
- **Decorator versus Chain of Responsibility.** Both are recursive compositions
  where each element may handle the call or pass it on, and in code they can look
  identical. The intents diverge on what passing on means. In Chain of
  Responsibility, each handler asks whether this request is its business, and the
  chain exists so that the sender does not know which handler will answer.
  Handlers are alternatives to each other and the normal case is that exactly one
  of them handles the request. In Decorator, every layer participates in every
  call, and the layers are additive rather than alternative. The practical test.
  If a layer declining to act is the normal path, it is a chain. If a layer
  declining to act is an optimisation or an error, it is a decorator. Servlet
  filters sit uncomfortably between the two, which is why the Jakarta
  specification's Filtering chapter covers both chaining and request wrapping as
  separate concepts
  (https://jakarta.ee/specifications/servlet/6.0/jakarta-servlet-spec-6.0
  verified 2026-08-02).
- **Composite.** The structural sibling. Both compose recursively over a shared
  interface, but Composite holds a collection of children and combines their
  results, while Decorator holds exactly one and adds behaviour around it. A
  decorator can be viewed as a composite with a single child and added
  behaviour. Mixing the two in one hierarchy is workable and produces a tree
  whose nodes are individually decorated, which is how many rendering and UI
  toolkits are built.
- **Strategy.** The usual substitute, and often the better one. Strategy changes
  the inside of an operation by swapping a pluggable part. Decorator wraps the
  operation from outside without changing its inside. Strategy costs no
  forwarding and no identity change, so when the variation is one decision rather
  than a stack of independent additions, Strategy is cheaper. The two compose
  well. A decorator that holds a Strategy for its own added behaviour, for
  example a retry decorator that takes a backoff strategy, is a sound and common
  shape.
- **Template Method.** An alternative for the same goal when the extension points
  are known in advance and fixed. Template Method binds them by inheritance at
  compile time. Decorator leaves them open at runtime. Template Method is
  preferable when the sequence is fixed and the variation is bounded, because it
  has no forwarding tax and no identity change.
- **Flyweight.** Conflicts in practice. Flyweight exists to avoid one object per
  logical item. Decorator adds objects per item. Decorating a large population of
  flyweights individually undoes the memory saving that motivated the flyweight.
  If the decoration is uniform, apply it once at the context level rather than
  per instance.
- **Singleton.** Conflicts in the same way it conflicts with most composition
  patterns. If the component is a process-wide singleton that callers reach
  through a static accessor, no decorator can be inserted between the caller and
  the component, because the caller never asked anyone for the object. Injecting
  the component is a precondition for decorating it.
- **Dependency injection containers.** Compose strongly. Most containers offer
  first-class decoration registration, so the composition is declared once in
  configuration rather than written by hand at every construction site. This is
  the main way the pattern reaches production in application code, and it also
  supplies the single composition point that dimension 11's double-wrapping fix
  asks for.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. The starting position is
almost always a class with a boolean or a conditional guarding an orthogonal
concern, or a small subclass hierarchy that has begun to combine.

1. Find the concern to extract, and confirm it is orthogonal. The test is
   whether the concern's code reads or writes any field the core operation also
   touches. If it does, it is not orthogonal and extracting it will produce two
   classes with a shared secret.
2. Extract the component interface if one does not exist, and make it narrow.
   Include only the members the client calls, not everything the concrete class
   offers. This step decides how expensive every later decorator will be, and it
   is the step teams skip. The named refactoring is Extract Interface.
3. Change the client and every construction site to depend on the interface
   rather than the concrete class. Run the tests. Nothing else has changed yet.
4. Create the abstract Decorator base implementing the interface and forwarding
   every member to a held component. Write a test that asserts the base is
   transparent, meaning a component wrapped in the bare base behaves identically
   to the component alone. This test is worth more than it looks, because it is
   the one that catches a missing forwarding method.
5. Move the concern out of the core class into a ConcreteDecorator extending the
   base. Delete the flag and the conditional from the core class. Run the tests.
   The behaviour should be unchanged because nothing is wired yet.
6. Wire the decorator at the composition root, in the order that reproduces the
   previous behaviour. Run the tests. This is the step where a behaviour change
   would appear, and having done everything else first means the diff under
   suspicion is one line.
7. Repeat from step 5 for the second concern. Stop after the first concern only
   if a second is already scheduled. One decorator and one abstract base to
   replace one boolean is a net loss, and dimension 4 calls it out.
8. Add the chain-integrity test and the composition-order test from dimension 15
   before the third concern arrives, because after the third the order becomes
   difficult to reason about by inspection.

Removing the pattern when it stops earning its place. The signals are a decorator
stack that has been identical in every environment for a year, a decorator that
overrides nothing, or a component interface that has grown so wide that the
forwarding is the bulk of the code.

1. Confirm from the wiring, not from memory, that only one composition exists.
   Search every composition root, every test fixture and every configuration
   file. A second composition in an integration test is enough to keep the
   pattern.
2. Delete any decorator that overrides nothing. It is pure forwarding and can go
   without changing behaviour, which the transparency test from step 4 above
   already proves.
3. For the remaining ones, decide per decorator. A concern that is genuinely
   universal moves into the concrete component. A concern that is one pluggable
   decision becomes a Strategy field on the component. A concern that is only
   ever on in one environment becomes a build-time or configuration-time
   composition of two concrete classes.
4. Inline each decorator's behaviour into the component in the order the chain
   applied it, one at a time, running the tests after each. This is Inline Class
   applied to a wrapper. See the refactoring family entries for Inline Class and
   Replace Subclass with Delegate.
5. Delete the abstract Decorator base once no ConcreteDecorator remains.
6. Reconsider the component interface. It was widened, if it was widened, to
   serve clients rather than decorators. It should not need narrowing now, and
   narrowing it is a separate change with its own blast radius.
