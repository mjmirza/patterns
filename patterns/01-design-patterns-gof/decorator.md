---
name: Decorator
slug: decorator
family: 01-design-patterns-gof
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

**Delegation keyword.** The Kotlin `by` clause removes the forwarding tax
outright, so the decorator declares only what it changes. The language
documentation states that the clause causes the delegate to be stored internally
in objects of the deriving type and the compiler to generate all the methods of
the interface forwarding to it, and that an override in the deriving type is used
in preference to the delegate's implementation (JetBrains, *Kotlin
documentation*, "Delegation", https://kotlinlang.org/docs/delegation.html
verified 2026-08-02). This is the largest quality-of-life difference between
languages for this pattern. C# has no equivalent clause and pays the tax by hand.
Go struct embedding reaches a similar place by promoting the embedded type's
methods onto the outer type.

Both delegation forms carry the same limitation, and it is the one that bites.
Neither dispatches back into the outer type. The Kotlin documentation says
plainly that members overridden in the deriving type are not called from the
members of the delegate object, which can only access its own implementations of
the interface members (same source). Effective Go makes the matching statement
for embedding, that when an embedded type's method is invoked the receiver is the
inner type and not the outer one, and it names this as the important way in which
embedding differs from subclassing (Go project, *Effective Go*, "Embedding",
https://go.dev/doc/effective_go verified 2026-08-02). The consequence is worth
stating concretely. A self-call inside the wrapped object bypasses the
decorator's override, so a decorator that overrides a method the component also
calls internally will never see those internal calls. That is the
delegation-skipping symptom from dimension 11 arriving from the opposite
direction, with no line of the decorator's own code at fault, and no compiler
warning in either language.

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
forwarding behaviour at runtime rather than requiring it in source. The .NET type
is documented as providing a mechanism for instantiating proxy objects and
handling their method dispatch, with its `Invoke` method invoked to dispatch
control whenever any method on the generated proxy type is called (Microsoft,
*.NET API documentation*, `System.Reflection.DispatchProxy`,
https://learn.microsoft.com/en-us/dotnet/api/system.reflection.dispatchproxy
verified 2026-08-02). This
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

## 15. Testing and verification

Most of this dimension is practice rather than sourced fact, and it is written as
reasoning. The two citations in it are for library behaviour, not for advice.

Easier because of the pattern.

- Each behaviour is testable alone. A caching decorator can be tested against a
  hand-written recording component with no network, no clock and no framework. The
  test asserts that two calls with the same key produce one call to the inner
  component, which is the entire contract of that class in one line.
- The base implementation stays testable without any of the concerns. Because the
  concrete component never learned about retries or metrics, its test suite never
  has to disable them.
- Test doubles are ordinary components. A decorator accepts any Component, so a
  stub, a spy or a fake slots in with no mocking framework and no bytecode
  rewriting. The spy is the most useful of the three here, because the question a
  decorator test asks is usually about call counts and call order rather than
  about return values.
- Fault injection is a decorator. A test-only layer that throws on the third call,
  delays by two hundred milliseconds, or returns a truncated body composes into
  the same stack the production code uses. This gives chaos testing at the object
  level with no infrastructure, and it is the cheapest way to exercise the retry
  and circuit-breaker paths that otherwise only run during an incident.
- Ordering is testable as data. Because a stack is built at a composition root, a
  test can build the same stack the application builds and assert properties of
  it, which is impossible when the behaviour is buried in conditionals.

Harder because of the pattern.

- Nothing in a unit test proves the production stack. Every decorator can pass its
  own test while the wiring assembles them in the wrong order, or omits one, or
  adds one twice. The unit tests are green and the system is wrong, which is the
  worst failure shape a test suite can have.
- Assertions about the innermost component require reaching through the chain.
  Either the test builds the stack itself and keeps a reference to the base, which
  is what the code examples below do, or the decorator exposes an unwrapping
  accessor, which .NET does with `BaseStream` on `GZipStream`
  (https://learn.microsoft.com/en-us/dotnet/api/system.io.compression.gzipstream
  verified 2026-08-02).
- Coverage tools flatter a decorator suite. Forwarding methods are executed by
  every test that touches the stack, so line coverage on a decorator class runs
  high while the branch that skips delegation stays untested.
- A decorator that forgets to delegate produces a green outer test. If the test
  asserts only on the outer return value, and the decorator fabricates a
  plausible one, nothing fails.
- Stack traces in failing tests are long and repetitive, so the assertion message
  has to carry the diagnosis because the trace will not.

Techniques that apply, in the order they earn their keep.

- **Transparency test on the abstract Decorator base.** Wrap a component in the
  bare base with no overrides and assert that every operation produces the same
  result as calling the component directly. This one test catches a forwarding
  method that was never written, which is otherwise a silent hole that every
  ConcreteDecorator inherits.
- **Chain-integrity test with a sentinel innermost component.** Build the real
  production stack over a recording component, call every public operation, and
  assert the recorder saw each one. Repeat for the error paths, because the
  delegation-skipping bug from dimension 11 lives on the error path far more often
  than on the happy path. This is the single highest-value test for this pattern
  and almost nobody writes it.
- **Composition-root test.** Assert on the assembled stack, not on the classes.
  Ask the composition function for the object it would give the application, then
  assert the layer order by unwrapping, by a debug description each layer
  contributes, or by driving a probe call through it and checking the observed
  sequence. Without this test the wiring is the only untested code in the system.
- **Call-count test through a retrying layer.** Compose retry over a component
  that fails a fixed number of times and assert both the returned value and the
  number of inner calls. The second assertion is the one that catches a retry
  budget that multiplies with a second retry layer.
- **Order-invariant test rather than an order test.** Where an order is a safety
  property, for example that no authorisation decision is served from a cache,
  assert the property rather than the arrangement. An arrangement test breaks on
  every legitimate refactor. A property test breaks only when the safety
  property does.
- **Contract test reused across the stack.** Write one suite against the Component
  interface and run it against the bare component and against every decorated
  configuration. A decorator that narrows the contract, as `GZipStream` does with
  `Seek` and `Position`, fails this suite immediately rather than in production,
  and the failure is the honest signal that the interface needs splitting.
- **Property-based test on composability.** For a decorator that claims to be
  transparent for some subset of operations, assert over generated inputs that
  the decorated result equals the undecorated result. Caching, metrics and logging
  layers should all satisfy this. A layer that fails it is doing more than it
  claims.
- **Test that names survive wrapping, in dynamic languages.** In Python, assert
  that a decorated function keeps its `__name__` and `__doc__`, which is what
  `functools.wraps` copies through `WRAPPER_ASSIGNMENTS`, and that `__wrapped__`
  points at the original function so introspection can still reach it (Python
  Software Foundation, *Python 3 documentation*, `functools`,
  https://docs.python.org/3/library/functools.html verified 2026-08-02). Without
  this test every traceback and every generated document names the wrapper.
- **Depth assertion.** Where composition is driven by configuration, assert a
  maximum stack depth in a test so the unbounded-composition failure from
  dimension 11 is caught at build time rather than by a stack overflow.

## 16. Observability signals

This dimension is engineering practice. Treat it as reasoning, with two sourced
claims about how tracing and layer ordering behave.

The observability problem this pattern creates is precise. The composition is
built at runtime and is invisible in the source, so at three in the morning
nobody can answer which layers were installed in the failing deployment. The
observability opportunity it creates is equally precise. Every call passes
through every layer, so a decorator is the cheapest instrumentation point in the
system. Both halves have to be worked, and teams almost always do the second and
skip the first.

Record the composition itself, once, at startup.

- Emit one structured log line per composition root at startup listing the layer
  names in call order, plus the configuration each layer was given, with secrets
  redacted. Without it, an incident review has to reconstruct the stack from a
  deployment artefact.
- Expose the same list on a diagnostic endpoint or in a health payload, so the
  question can be answered about a live process rather than about the artefact
  that was supposedly deployed.
- Include a hash of the ordered layer list in the log line. Comparing that hash
  across replicas answers, in one query, whether the fleet is running the same
  stack, which is a question that otherwise takes an hour.

Record what each layer does, per call.

- One span per layer, not one span for the whole stack. The OpenTelemetry model
  makes nested spans the natural representation of this. Child spans represent
  sub-operations and are linked to a parent by a parent span identifier, and spans
  sharing a trace identifier with a parent hierarchy form the trace
  (OpenTelemetry, "Traces", https://opentelemetry.io/docs/concepts/signals/traces/
  verified 2026-08-02). A decorator stack maps onto that model without any
  distortion, and the resulting waterfall shows exactly where the time went and
  which layer returned early.
- Where a span per layer is too expensive, put a span attribute on the outer span
  naming the layers that acted. Attributes are documented as key-value metadata
  annotating a span with information about the operation it tracks (same source).
  A boolean per layer, or a compact string of layer initials, costs almost nothing
  and answers the cache-hit question without a second span.
- A counter per layer, labelled by layer name and outcome. For a cache layer,
  hit and miss. For a retry layer, attempts and final outcome. For an
  authorisation layer, allow and deny.
- A latency histogram at the outermost layer and at the innermost, both. The
  difference between the two is the cost the middle of the stack adds, and it is
  the only honest measure of the pattern's overhead in that system.

The measurement trap that this pattern creates, stated plainly because it
produces wrong dashboards rather than missing ones. A counter placed outside a
retrying layer counts client calls. A counter placed inside it counts backend
calls. They differ by the retry factor, and under partial outage they differ by a
lot. A counter placed outside a caching layer counts requests. A counter placed
inside it counts misses. Neither pair is wrong, and a dashboard that mixes one of
each without saying so under-reports backend load exactly when the backend is in
trouble. Label every counter with the layer that emitted it and state in the
dashboard which side of the cache and the retry it sits on. The dynamics diagrams
in dimension 7 are the picture of this trap.

Layer order changes what the numbers mean, and the layer library authors say so.
The `tower` builder documentation states that the order in which layers are added
affects how requests are handled and that layers added first are called with the
request first, and it gives the concrete case that a buffer of one hundred
followed by a concurrency limit of ten permits one hundred and ten in-flight
requests while the reverse order permits ten
(https://docs.rs/tower/latest/tower/builder/struct.ServiceBuilder.html verified
2026-08-02). Two stacks with identical layers and identical configuration produce
different concurrency, and therefore different queueing, different latency
distributions and different saturation points. A capacity model built without
knowing the order is a guess.

A healthy instance on a dashboard. The startup composition hash is identical
across every replica and changes only on deploy. The per-layer span waterfall has
the same shape for the same route, with the outer layers contributing a flat and
small share of total latency. Cache hit ratio is stable. Retry attempts sit near
one per call. The difference between outermost and innermost latency histograms
is flat and small.

A failing instance, with the diagnosis each shape points to. Backend call volume
exceeds client call volume by a growing factor, which is retry amplification, and
if the factor is a perfect square then two retry layers are stacked. Cache hit
ratio drops to zero after a deploy while the code did not change, which is a
composition-order change that moved the cache inside a layer that varies the key.
One replica shows a different composition hash, which is a partial rollout
running two stacks. The gap between outer and inner latency histograms widens
under load, which is a layer doing work proportional to load, typically a lock, a
buffer copy or a synchronous log write. A span waterfall that is missing a layer
present in the startup log is the delegation-skipping failure from dimension 11,
observed rather than deduced.

## 17. Security and privacy implications

This dimension is analytical. Where the pattern is silent, this section says so
rather than inventing a concern.

The pattern is neutral on most of the classical attack surface. It does not
parse input, cross a trust boundary, or manage credentials by virtue of being a
decorator. What it changes is who can insert code into a call path and how easily
a reader can tell that they did. Five implications follow from that, and two of
them are genuinely favourable.

**A decorator is the correct place to put a security control, and this is the
pattern's main security benefit.** Authorisation, input validation, rate
limiting, audit logging and encryption at rest all have the shape the pattern
serves. They are orthogonal to the domain operation, they apply uniformly across
implementations, and they must be impossible to forget. Placing them in a layer
rather than in every method means one reviewed implementation covers every call
site. The Jakarta Servlet specification ships this shape as public API and states
it directly. The `ServletRequestWrapper` class documentation describes it as a
convenient implementation of `ServletRequest` that developers subclass to adapt
the request, and says in the class description that the class implements the
Wrapper or Decorator pattern
(https://jakarta.ee/specifications/servlet/6.0/apidocs/jakarta.servlet/jakarta/servlet/servletrequestwrapper
verified 2026-08-02). Request sanitising wrappers in that ecosystem are decorators
by the specification's own naming.

**The same property means a decorator is a control that can be silently omitted.**
A security layer that lives in the composition root is one line away from not
existing, and its absence produces no compile error, no failing unit test and no
runtime exception. It produces a system that works, faster. This is the pattern's
sharpest security risk and it is a direct consequence of its main benefit. The
defences are mechanical. Assert the presence of the security layer in a test that
runs against the real composition root, not against a fixture. Make the composed
type impossible to construct without the layer, for example by having the builder
return a type that only the authorisation layer can produce. Alert on the startup
composition log from dimension 16 when an expected layer name is absent.

**Ordering is a security property, not a preference.** Caching outside
authorisation serves a decision made for one principal to another principal. This
is a real vulnerability class produced entirely by composition order, with every
individual layer correct. The same applies to a rate limiter placed after an
expensive layer rather than before it, which permits the cost to be incurred
before the limit is checked, and to a decryption layer placed outside a logging
layer, which logs plaintext. None of these is detectable by reading one class.
The mitigations are the invariant tests from dimension 15 and a builder that
rejects known-bad adjacencies.

**Logging decorators are the most common source of sensitive-data leakage in this
pattern.** A layer that logs arguments and return values for diagnosis is trivial
to write and is usually the first decorator a team ships. It will log credentials
on the login path, tokens on the refresh path, and personal data on every
customer path, because it was written against the interface without knowing what
flows through it. The weakness is catalogued as CWE-532, "Insertion of Sensitive
Information into Log File", described as the product writing sensitive
information to a log file (MITRE, *Common Weakness Enumeration*, CWE-532,
https://cwe.mitre.org/data/definitions/532.html verified 2026-08-02). The
decorator makes it worse than a scattered log statement would be, because one
generic layer covers every operation including the ones nobody considered.
Mitigate by allowlisting fields rather than logging whole payloads, by making the
domain types carry their own redacted representation so the layer cannot see the
raw value, and by treating any generic argument logger as a review-blocking
change.

**Dynamic proxy generation widens the trust boundary.** The runtime-generated
forwarding variant from dimension 8 dispatches every method through a handler.
Java's `Proxy` documentation states that a method invocation on a proxy instance
is dispatched to the invocation handler's `invoke` method, passing the proxy, a
`Method` object identifying the method invoked, and an array of arguments, and
that whatever the handler returns is returned as the result
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/reflect/Proxy.html
verified 2026-08-02). That handler is a single point that sees every argument and
can substitute every return value. If the handler class is supplied by a plugin,
by a dependency-injection container reading a configuration file, or by any code
outside the review boundary of the component, then an attacker who controls the
handler controls the results the application acts on, without touching the
component's source. Treat handler registration as privileged configuration, pin
the set at build time where the plugin set is known, and prefer compile-time
generation, which puts the forwarding code in the repository where it can be
reviewed.

Two places where the pattern is genuinely silent, stated so the reader does not
look for a concern that is not there. It has no bearing on memory safety beyond
whatever the host language already provides, and wrapping does not introduce a
lifetime hazard that the language did not already have. It has no bearing on
cryptographic correctness. An encryption decorator is exactly as sound as the
primitive it calls, and placing that primitive in a wrapper neither helps nor
hurts the cryptography.

On privacy, one operational point. The composition log recommended in dimension
16 lists layer names and their configuration. Layer configuration frequently
contains connection strings, tenant identifiers and region names. Redact the
configuration values and keep the layer names, which are the part that answers
the incident question.

## 18. References

Books.

1. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides. *Design Patterns.
   Elements of Reusable Object-Oriented Software*. Addison-Wesley, 1994. Chapter
   4, Structural Patterns, the Decorator entry. Source for the canonical name, the
   Wrapper alias, the four participants, the combinatorial-subclassing motivation,
   and the Related Patterns note connecting Decorator to Composite, Adapter,
   Proxy and Strategy.
2. Joshua Bloch. *Effective Java*, 3rd edition. Addison-Wesley, 2018. Item 18,
   "Favor composition over inheritance". Source for the forwarding-class variant,
   the `ForwardingSet` and `InstrumentedSet` example, and the argument that a
   wrapper works over any implementation of the interface where a subclass works
   over only one.

Language and library specifications, all URLs verified 2026-08-02.

3. Oracle. *Java SE 21 API Specification*, `java.io.FilterInputStream`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/io/FilterInputStream.html
   Source for the abstract-decorator participant in the Java stream hierarchy and
   for the protected `in` field holding the filtered stream.
4. Oracle. *dev.java*, "Decorating I/O Streams".
   https://dev.java/learn/java-io/reading-writing/decorating/
   Source for the statement that the Java I/O API uses the Decorator pattern, and
   for the compression example.
5. Oracle. *Java SE 21 API Specification*, `java.lang.reflect.Proxy`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/reflect/Proxy.html
   Source for the runtime-generated forwarding variant and for the dispatch
   contract used in the security analysis.
6. Jakarta EE. *Jakarta Servlet 6.0 API documentation*,
   `jakarta.servlet.ServletRequestWrapper`.
   https://jakarta.ee/specifications/servlet/6.0/apidocs/jakarta.servlet/jakarta/servlet/servletrequestwrapper
   Source for a specification naming the pattern in its own class description and
   for the `getRequest` accessor returning the wrapped request.
7. Jakarta EE. *Jakarta Servlet Specification, version 6.0*, chapter 6,
   Filtering. https://jakarta.ee/specifications/servlet/6.0/jakarta-servlet-spec-6.0
   Source for the treatment of filter chaining and request wrapping as separate
   concepts, used in the Chain of Responsibility comparison.
8. Python Software Foundation. *Python 3 documentation*, `io`.
   https://docs.python.org/3/library/io.html
   Source for the `TextIOWrapper` over `BufferedReader` over raw stream layering.
9. Python Software Foundation. *Python 3 documentation*, `functools`.
   https://docs.python.org/3/library/functools.html
   Source for `wraps`, the `WRAPPER_ASSIGNMENTS` attribute list, and the
   `__wrapped__` attribute pointing at the wrapped function.
10. Python Software Foundation. *PEP 318, Decorators for Functions and Methods*,
    status Final. https://peps.python.org/pep-0318/
    Source for the language-level decorator syntax and its desugaring, used to
    separate the syntax from the structural pattern.
11. TC39. *Decorators proposal*, Stage 2.7 as of the verification date.
    https://github.com/tc39/proposal-decorators
    Source for the JavaScript decorator semantics and the constraint that a
    decorator replaces a value only with one of matching semantics.
12. Microsoft. *.NET API documentation*, `System.IO.Compression.GZipStream`.
    https://learn.microsoft.com/en-us/dotnet/api/system.io.compression.gzipstream
    Source for the `BaseStream` accessor, the `leaveOpen` constructor overloads,
    and the documented `NotSupportedException` on `Length`, `Position`, `Seek`
    and `SetLength`.
13. `tower` crate. `tower::Layer` trait documentation.
    https://docs.rs/tower/latest/tower/trait.Layer.html
    Source for the equivalence of middleware and decoration, and for the
    `layer` method signature taking an inner service and returning the wrapper.
14. `tower` crate. `tower::builder::ServiceBuilder` documentation.
    https://docs.rs/tower/latest/tower/builder/struct.ServiceBuilder.html
    Source for the statement that layers added first are called with the request
    first, and for the buffer and concurrency-limit ordering example used in
    dimension 16.
15. Go project. `net/http`, `StripPrefix`.
    https://pkg.go.dev/net/http#StripPrefix
    Source for the function-valued decorator in the Go standard library.
16. JetBrains. *Kotlin documentation*, "Delegation".
    https://kotlinlang.org/docs/delegation.html
    Source for the `by` clause generating the forwarding methods, for overrides
    taking precedence over the delegate, and for the statement that overridden
    members are not called from the members of the delegate object.
17. Go project. *Effective Go*, "Embedding".
    https://go.dev/doc/effective_go
    Source for method promotion from an embedded type, and for the statement
    that the receiver of a promoted method is the inner type and not the outer
    one, which is the important way embedding differs from subclassing.
18. Microsoft. *.NET API documentation*, `System.Reflection.DispatchProxy`.
    https://learn.microsoft.com/en-us/dotnet/api/system.reflection.dispatchproxy
    Source for the runtime proxy-generation variant on .NET and for the `Invoke`
    dispatch contract.

Standards and research, URLs verified 2026-08-02.

19. MITRE. *Common Weakness Enumeration*, CWE-532, "Insertion of Sensitive
    Information into Log File". https://cwe.mitre.org/data/definitions/532.html
    Source for the logging-decorator leakage class in dimension 17.
20. OpenTelemetry. "Traces", concepts documentation.
    https://opentelemetry.io/docs/concepts/signals/traces/
    Source for the parent and child span model and the definition of span
    attributes, used for the per-layer instrumentation recommendation.
21. Virginia Niculescu, Adrian Sterca, Darius Bufnea. "Should Decorators Preserve
    the Component Interface?", arXiv preprint arXiv:2009.06414, 2020.
    https://arxiv.org/abs/2009.06414
    Source for the academic treatment of the interface-preservation constraint
    and the proposed relaxations, cited in the interface-bloat failure mode.

Claims deliberately not made, recorded so a later contributor does not add them
without evidence. No source was found that states the per-call cost of a
decorator layer in any specific runtime, so no number is given for it, and
dimension 3 says only that the cost is one dispatch per layer. No source was
found attributing the phrase "smart proxy" to a specific publication, so that
alias is recorded as being in informal use rather than as having a named origin.

## Code examples

Four languages, each showing a different genuine shape of the pattern rather than
the same code four times. All four were compiled and run on 2026-08-02, and the
output quoted under each is the real output.

Java and Kotlin are omitted for a stated reason. Java is the canonical language
for the classical form, and dimension 9 covers `java.io` in detail, but no Java
toolchain was available on the authoring machine and the repository policy is not
to imply a compilation that did not happen. Kotlin is the language where the
pattern is cheapest, because the `by` clause generates the forwarding, and its
absence here is a toolchain gap rather than a judgement about the language.

### TypeScript, the classical abstract decorator

The GoF shape with an abstract forwarding base. `CountingRepo` sits under the
cache so its counter measures backend calls rather than client calls, which is
the measurement point dimension 16 makes.

```typescript
interface Repo {
  get(key: string): Promise<string>;
}

class HttpRepo implements Repo {
  async get(key: string): Promise<string> {
    return `value-of-${key}`;
  }
}

// The forwarding base exists so concrete decorators override only what changes.
abstract class RepoDecorator implements Repo {
  constructor(protected readonly inner: Repo) {}
  get(key: string): Promise<string> {
    return this.inner.get(key);
  }
}

class CachingRepo extends RepoDecorator {
  private readonly store = new Map<string, string>();
  override async get(key: string): Promise<string> {
    const hit = this.store.get(key);
    if (hit !== undefined) return hit;
    const value = await super.get(key);
    this.store.set(key, value);
    return value;
  }
}

class CountingRepo extends RepoDecorator {
  public calls = 0;
  override get(key: string): Promise<string> {
    this.calls += 1;
    return super.get(key);
  }
}

async function main(): Promise<void> {
  const inner = new CountingRepo(new HttpRepo());
  const repo: Repo = new CachingRepo(inner);
  console.log(await repo.get("a"), await repo.get("a"), inner.calls);
}

void main();
```

Compiled with TypeScript 5.9.3 under `--strict --target es2022 --module
commonjs` with no errors, then run on Node 23.11.0. Output.

```text
value-of-a value-of-a 1
```

Two client calls, one backend call. The assertion that matters is the `1`, and it
is the chain-integrity test from dimension 15 written as a program.

### Python, both forms in one file

Python offers the object form and the function form, and the two are different
enough that showing both is worth the space. `cached` is the object form. The
`retrying` factory is the parameterised function form from dimension 8, using
`functools.wraps` so the wrapped function keeps its identity.

```python
import functools
from typing import Protocol


class Repo(Protocol):
    def get(self, key: str) -> str: ...


class HttpRepo:
    def get(self, key: str) -> str:
        return f"value-of-{key}"


def cached(repo):
    store = {}

    class Cached:
        def get(self, key):
            if key not in store:
                store[key] = repo.get(key)
            return store[key]

    return Cached()


def retrying(times):
    def wrap(fn):
        @functools.wraps(fn)
        def inner(*a, **kw):
            last = None
            for _ in range(times):
                try:
                    return fn(*a, **kw)
                except Exception as e:
                    last = e
            raise last

        return inner

    return wrap


class Flaky:
    def __init__(self):
        self.n = 0

    @retrying(times=3)
    def get(self, key):
        self.n += 1
        if self.n < 3:
            raise IOError("boom")
        return f"value-of-{key} after {self.n}"


r = cached(HttpRepo())
print(r.get("a"), r.get("a"))
print(Flaky().get("b"))
print(Flaky.get.__name__)
```

Run on Python 3.14.6. Output.

```text
value-of-a value-of-a
value-of-b after 3
get
```

The third line is the point of `functools.wraps`. Without it the last line prints
`inner`, and every traceback through that method names the wrapper rather than the
method, which is the diagnostic loss dimension 15 asks a test to prevent.

### Go, the function form in the standard library shape

Go has no inheritance, and the standard library's `http.Handler` is a
single-method interface, so the function form is the idiomatic one. `Chain` exists
to invert the construction order, which is the job `tower::ServiceBuilder` does in
Rust and the reason dimension 7 flags construction order as inverted.

```go
package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"time"
)

func Logging(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		fmt.Println("in ", r.URL.Path)
		next.ServeHTTP(w, r)
		fmt.Println("out", r.URL.Path)
	})
}

func Timing(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next.ServeHTTP(w, r)
		fmt.Printf("elapsed measured: %v\n", time.Since(start) > 0)
	})
}

// Chain applies layers so the first argument is the outermost layer.
func Chain(h http.Handler, layers ...func(http.Handler) http.Handler) http.Handler {
	for i := len(layers) - 1; i >= 0; i-- {
		h = layers[i](h)
	}
	return h
}

func main() {
	base := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprint(w, "ok:"+r.URL.Path)
	})
	h := Chain(base, Logging, Timing)
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest("GET", "/health", nil))
	fmt.Println("body:", rec.Body.String())
}
```

Built and run with the Go toolchain in a module set to `go 1.21`. Output.

```text
in  /health
elapsed measured: true
out /health
body: ok:/health
```

The interleaving is the pattern's runtime signature. Logging opens, Timing runs
entirely inside it, and Logging closes. Reading the output top to bottom gives the
call order, which reading the construction never does.

### Rust, the generic wrapper with static dispatch

Rust has no inheritance, so the decorator is a generic struct owning its inner
value and implementing the same trait. The whole stack is one concrete type, so
there is no per-layer dynamic dispatch. This is the shape `tower::Layer`
formalises.

```rust
use std::collections::HashMap;

trait Repo {
    fn get(&mut self, key: &str) -> String;
}

struct HttpRepo {
    calls: u32,
}

impl Repo for HttpRepo {
    fn get(&mut self, key: &str) -> String {
        self.calls += 1;
        format!("value-of-{key}")
    }
}

struct Caching<R: Repo> {
    inner: R,
    store: HashMap<String, String>,
}

impl<R: Repo> Caching<R> {
    fn layer(inner: R) -> Self {
        Caching { inner, store: HashMap::new() }
    }
}

impl<R: Repo> Repo for Caching<R> {
    fn get(&mut self, key: &str) -> String {
        if let Some(v) = self.store.get(key) {
            return v.clone();
        }
        let v = self.inner.get(key);
        self.store.insert(key.to_string(), v.clone());
        v
    }
}

struct Upper<R: Repo> {
    inner: R,
}

impl<R: Repo> Repo for Upper<R> {
    fn get(&mut self, key: &str) -> String {
        self.inner.get(key).to_uppercase()
    }
}

fn main() {
    let mut repo = Upper { inner: Caching::layer(HttpRepo { calls: 0 }) };
    println!("{} {}", repo.get("a"), repo.get("a"));
    println!("backend calls: {}", repo.inner.inner.calls);
}
```

Compiled with rustc 1.97.1 at optimisation level one and run. Output.

```text
VALUE-OF-A VALUE-OF-A
backend calls: 1
```

Note `repo.inner.inner.calls`. The full stack type is `Upper<Caching<HttpRepo>>`,
so the composition is visible in the type system and the innermost component is
reachable by name. That is the introspection property the other three languages
lose, and it is bought by giving up the ability to hold a heterogeneous stack
behind one type without boxing.
