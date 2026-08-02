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
