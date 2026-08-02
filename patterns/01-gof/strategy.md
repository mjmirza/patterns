---
name: Strategy
slug: strategy
family: 01-gof
category: Behavioral
aliases: [Policy, Pluggable Behaviour, Algorithm Object]
first_described: "Gamma, Helm, Johnson, Vlissides 1994"
maturity: canonical
related: [state, template-method, command, bridge, decorator, visitor, factory-method, abstract-factory, null-object]
incompatible_with: []
verified: 2026-08-02
---

# Strategy

## 1. Name, aliases, and lineage

The canonical name is Strategy. It appears in the Gang of Four catalog as one of
the eleven behavioral patterns, described in Erich Gamma, Richard Helm, Ralph
Johnson and John Vlissides, *Design Patterns. Elements of Reusable
Object-Oriented Software*, Addison-Wesley, 1994, chapter 5 (Behavioral
Patterns), Strategy. The published intent is to define a family of algorithms,
encapsulate each one, and make them interchangeable, so that the algorithm
varies independently of the clients that use it. A public summary of the same
intent, with the runtime-selection framing, is available at
[Wikipedia, Strategy pattern](https://en.wikipedia.org/wiki/Strategy_pattern),
verified 2026-08-02, which states that the pattern enables selecting an
algorithm at runtime and records **Policy** as the alternative name.

Three names for the same idea circulate, and the difference between them is
mostly community dialect rather than substance.

- **Strategy.** The GoF name. Used in nearly all object-oriented literature and
  in the class names of many libraries, for example the Passport.js
  authentication modules, see dimension 9.
- **Policy.** Used in the C++ community and in security and infrastructure
  contexts. In C++ the related idea appears as policy-based design, where the
  policy is a template parameter resolved at compile time rather than a
  reference resolved at runtime. That variant trades away runtime substitution
  for zero dispatch cost, see dimension 8. In infrastructure and access control,
  policy usually carries the extra connotation of being declared as data rather
  than as code.
- **Pluggable behaviour.** Informal. Appears in framework documentation where
  the author does not want to invoke pattern vocabulary. It describes the same
  arrangement, an interface with several implementations chosen by
  configuration.

There is one naming trap. A **comparator**, a **hasher**, a **serializer**, a
**codec**, a **formatter**, a **retry policy**, a **load balancer method**, an
**eviction policy** and an **authentication backend** are all Strategy under
different domain nouns. Recognising that these share one shape is more useful
than recognising the word Strategy, because almost nobody names the interface
`Strategy` in production code. If a type exists mainly to hold one operation
that a caller supplies to change how another object does its work, it is a
Strategy regardless of what the file is called.

A second naming trap concerns Strategy and State. They are structurally
identical and behaviorally distinct, which is why so much writing conflates
them. Wikipedia's State article records the overlap plainly, saying the state
pattern can be read as a strategy pattern able to switch strategy through
methods on the pattern's own interface
([Wikipedia, State pattern](https://en.wikipedia.org/wiki/State_pattern),
verified 2026-08-02). The separation is developed in dimension 13.

## 2. Problem and context

An object does a piece of work in more than one way, and the choice of way is
not a property of the object's identity.

The shape in a codebase is familiar. There is a method with a conditional whose
branches all compute the same kind of answer by different means. A shipping cost
calculator with a branch per carrier. A validator with a branch per document
type. A cache with a branch per eviction rule. A report writer with a branch per
output format. A retry helper with a branch per backoff scheme. The branches
share a signature, share their surrounding setup and teardown, and differ only
in the middle.

The conditional grows for three predictable reasons. A new case arrives and
somebody adds a branch. A case gains a variation and somebody nests a second
condition inside the first. A case needs configuration and somebody adds
parameters to the enclosing method that only one branch reads. After a few
rounds the method is long, every reader must scan branches that do not apply to
them, and adding a case means editing a file that a dozen unrelated features
also touch. The tests grow the same way, one test per branch, all constructing
the whole enclosing object to reach one middle section.

The context that makes Strategy the right answer has four parts, and the pattern
misfires when any of them is missing.

- The variants genuinely compute the same kind of result from the same kind of
  input. If two branches return different types or need different arguments,
  they are not a family and no single interface will fit them without a cast.
- The variation is behavioral, not structural. The object keeps its identity,
  its fields and its lifecycle. Only one operation changes.
- The choice is made by somebody other than the object doing the work, usually
  by whoever configured or constructed it. A tax calculator does not decide
  which jurisdiction it is in.
- More than one variant exists today. A single-variant Strategy is an interface
  with one implementation, which is a prediction rather than a design.

The most common real trigger is not the count of branches. It is that a variant
needs to arrive from outside the module, from a plugin, a customer-specific
package, a test, or a configuration file that names a class. A conditional
cannot accept a branch from outside its own source file. An interface can.

## 3. Forces

This dimension is engineering judgement about which pressure dominates, offered
as reasoning rather than as sourced fact.

- **Coupling.** Favoured, strongly. The context depends on one narrow interface
  instead of on every algorithm it might run. Algorithms depend on nothing about
  the context beyond the data they are handed. This is the pattern's central
  payoff and the reason it survives in languages with no inheritance at all.
- **Cognitive load, local.** Favoured. Each algorithm is a short unit read in
  isolation. The context method shrinks to setup, one call, and teardown.
- **Cognitive load, global.** Sacrificed. A reader who wants to know what
  actually runs must find the wiring, which is now somewhere else, possibly in a
  container configuration, a factory, or an environment variable. The conditional
  told the truth in one place. The Strategy tells it in two.
- **Cost of adding a variant.** Favoured. A new file, no edits to existing code.
  This is the Open Closed Principle applied to behaviour.
- **Cost of changing the interface.** Sacrificed, and sharply once implementors
  live outside the repository. Every published Strategy interface is a contract
  with an unknown number of implementors, and widening it breaks all of them.
- **Latency.** Mildly sacrificed. One indirect call per invocation, which is
  irrelevant in a managed runtime against real work, and measurable in a tight
  inner loop where the call blocks inlining and defeats vectorisation. In C++,
  Rust and Go the monomorphised or generic form removes that cost, see dimension
  8.
- **Allocation.** Depends on the variant. A stateless Strategy can be a shared
  singleton value with zero per-call allocation. A closure capturing context
  allocates once per construction. A Strategy allocated per request in a hot path
  is a garbage-collection cost the conditional did not have.
- **Consistency.** Roughly neutral, with one sharp edge. Nothing in the pattern
  prevents a caller from pairing a strategy with a context that it does not suit,
  because the type system only checks the interface, not the semantic fit.
  Abstract Factory exists partly to fix that for families, see dimension 13.
- **Operability.** Sacrificed unless instrumented. The running algorithm is not
  visible in the source, so an operator cannot answer which pricing rule applied
  to a given order without a log field, see dimension 16.
- **Team topology.** Favoured, strongly. The interface is a clean seam between a
  platform team owning the context and feature teams owning algorithms in their
  own modules, on their own release cadence, with their own tests.
- **Testability.** Favoured. Each algorithm is a pure unit with no context to
  construct, and the context is tested against a stub algorithm, see dimension 15.

The pattern's honest summary is that it converts one large decision made at
compile time into two small ones made in two different places. That is a real
gain when the algorithm set is open and a real loss when it is closed and small.

## 4. Applicability and non-applicability

Reach for Strategy when the following hold.

- Several variants of one operation exist, and the enclosing type is otherwise
  identical across them.
- The variant must be selectable at runtime, per request, per tenant, per
  environment, or per test.
- A variant needs to arrive from outside the module, from a plugin, a customer
  package, or a configuration entry.
- An algorithm carries its own configuration, for example a retry policy with a
  base delay and a jitter factor, and passing that configuration through the
  context's own signature would pollute it.
- The algorithms have meaningfully different performance or cost profiles, and
  an operator or a benchmark needs to swap between them without a rebuild.
- Conditional branches in one method have started to differ in their own
  internal structure, so extracting them to methods on the same class no longer
  reduces the reading cost.

Non-applicability. Do NOT reach for Strategy in these cases, and the reason
matters more than the rule.

- **There is exactly one algorithm and no named second one.** An interface with
  a single implementation adds a file, a dispatch, and a lie about extensibility.
  Write the code inline and extract later, which is cheap. Cross reference the
  code smell family entry on speculative generality.
- **The variants differ by a value, not by behaviour.** A discount of ten
  percent and a discount of twenty percent is a parameter, not a strategy. If two
  candidate strategies would share their whole body and differ in one constant,
  the design is a field.
- **The variants need different inputs.** If one algorithm needs a customer
  record and another needs a geolocation, the common interface either grows to
  the union of both, which pushes irrelevant arguments on every caller, or takes
  an untyped bag, which moves the type error to runtime. Model them as separate
  operations instead.
- **The algorithm must change the context's own state or lifecycle.** A strategy
  that reaches back into the context to mutate fields, or that decides what
  happens next, is a state machine wearing a strategy's clothes. Use State, see
  dimension 13.
- **The variation is really about sequencing a fixed algorithm skeleton.** If
  every variant repeats the same five steps and overrides two, Template Method
  expresses that with less ceremony, at the cost of binding by inheritance.
- **The whole family is closed, small, and internal.** Three payment kinds that
  will never grow and are all owned by one team read better as a sealed type with
  an exhaustive match, in a language that checks exhaustiveness. Rust, Kotlin,
  Swift and modern Java and C# all check it. The compiler then tells you when a
  case is missing, which no Strategy interface can do.
- **The interface would have one method and the language has first-class
  functions.** Then a function value is the pattern, and the class hierarchy is
  packaging around it, see dimension 8. Prefer the function unless the algorithm
  carries state, needs a name in a registry, or must be published as an
  extension point with documentation and versioning.
- **The choice would be made by a conditional you are about to write.** This is
  the strategy-selection trap, and it deserves its own treatment, see dimension
  11. Extracting bodies to classes and leaving the switch behind moves code
  without removing the branch.

## 5. Structure

Three participants, named by the role each plays.

- **Strategy.** The interface, protocol, trait or function type that declares the
  operation. It should be as narrow as the context genuinely needs, and no
  narrower, because every method on it is a burden on every implementor forever.
  A one-method Strategy is the healthy default. A Strategy with five methods is
  usually two Strategies that were merged for convenience.
- **ConcreteStrategy.** An implementation of the interface. It holds only its own
  configuration. It should not hold a reference back to the Context, because that
  reference is the difference between Strategy and State and it silently converts
  one pattern into the other. Concrete strategies are frequently stateless, in
  which case a single shared instance serves the whole process safely.
- **Context.** The object whose behaviour varies. It holds a reference to a
  Strategy, typed as the interface. It calls the strategy from inside its own
  work, passing whatever data the algorithm needs as arguments. It does not
  branch on the strategy's concrete type, and any such branch is the misuse
  described in dimension 11.

Relationships. Context holds Strategy by composition, not by inheritance. The
arrow points from Context to the Strategy abstraction only. Concrete strategies
are unknown to the Context at compile time, which is what allows them to live in
another module.

Two data-flow arrangements exist and the choice between them is one of the more
consequential decisions in applying the pattern.

- **Push.** The Context passes exactly the data the algorithm needs as
  parameters. The Strategy interface then depends on primitive or domain types
  and not on the Context type. This keeps strategies unit-testable in isolation
  and portable across contexts. It is the default and the one to prefer.
- **Pull.** The Context passes itself, and the algorithm reads what it needs.
  This suits algorithms that need many fields, but it couples every strategy to
  the Context's public surface, so widening a strategy's needs is free while
  narrowing the Context's interface becomes impossible. Reach for it only when
  the parameter list has grown past reason, and treat it as a design smell in a
  published extension point.

A fourth participant appears in real systems and is absent from the classical
diagram, the **Selector**. Something decides which ConcreteStrategy the Context
receives. That may be a dependency injection container, a registry keyed by a
string, a factory, or a literal in a composition root. Naming it as a
participant is honest, because it is where the removed conditional often
reappears, see dimension 11.

## 6. Diagram, ASCII structure

```
   +--------------------------+            +-----------------------+
   |         Context          |  strategy  |      <<interface>>    |
   |--------------------------|----------->|       Strategy        |
   | - strategy               |            |-----------------------|
   | + setStrategy(s)         |            | + execute(in) -> out  |
   | + doWork(in) -> out      |            +-----------------------+
   +--------------------------+                       ^
             ^                                        |
             |  configures                    implements (3 ways)
             |                        +---------------+---------------+
   +--------------------------+       |               |               |
   |        Selector          |  +----------+   +----------+   +----------+
   |--------------------------|  | Concrete |   | Concrete |   | Concrete |
   | container / registry /   |  | StrategyA|   | StrategyB|   | StrategyC|
   | factory / config file    |  |----------|   |----------|   |----------|
   +--------------------------+  | execute()|   | execute()|   | execute()|
                                 +----------+   +----------+   +----------+

   doWork() is written once and calls strategy.execute().
   Context never names a ConcreteStrategy. The Selector does, once.
   Concrete strategies hold no reference back to Context. That arrow,
   if it were drawn, would turn this diagram into the State pattern.
```

## 7. Dynamics

Two flows matter, the call flow and the swap flow. The call flow is short. The
swap flow is where designs go wrong.

Call flow, with the strategy fixed at construction.

```
Client            Context               ConcreteStrategyB
  |                  |                          |
  |- new Context(strategyB) ->|                 |
  |                  |                          |
  |- doWork(input) ->|                          |
  |                  |- validate(input)         |
  |                  |  (context's own work)    |
  |                  |                          |
  |                  |- execute(data) --------->|
  |                  |                          |- pure computation
  |                  |<-- result ---------------|
  |                  |                          |
  |                  |- record(result)          |
  |<-- output -------|  (context's own work)    |
  |                  |                          |
```

Swap flow, with the strategy replaced during the object's life.

```
   t0   Context.strategy = FixedWindow
        |
        |-- doWork() ----> FixedWindow.execute()      (in flight)
        |
   t1   Operator toggles a feature flag
        |
        |-- setStrategy(SlidingWindow)
        |     ^
        |     |  DANGER. If doWork() reads this.strategy more than
        |     |  once per call, one invocation can run half of one
        |     |  algorithm and half of another. Read the field into
        |     |  a local at method entry and use the local throughout.
        |
   t2   |-- doWork() ----> SlidingWindow.execute()
        |
```

Three timing facts follow from the swap flow, and they account for a large share
of production defects attributed to this pattern.

First, a Context that reads its strategy field several times inside one logical
operation is not atomic with respect to a swap. The remedy is a single read into
a local variable at entry, which gives each invocation a consistent view without
any lock. In languages with a defined memory model, the field also needs to be
published safely, `volatile` in Java, an atomic in Rust or Go, so that a thread
does not observe a partially constructed strategy object.

Second, a stateful strategy that is swapped loses whatever it accumulated. A rate
limiter that counts requests, swapped mid-window, resets the count and lets a
burst through. If a strategy holds operational state, the swap needs an explicit
handover, or the state belongs in the Context rather than in the strategy.

Third, strategies that are shared across threads must be immutable or internally
synchronised. The pattern quietly invites sharing, because a stateless strategy
is naturally a singleton, and the day somebody adds a mutable counter to that
shared instance the defect appears under load and not in tests.

## 8. Implementation variants

**Classical interface plus classes.** One interface, several classes, each in its
own file. Strongest form for a published extension point, because each strategy
has a name, a documented contract, its own tests, and its own configuration
fields. Costs a file per variant and the most ceremony of any variant. Use it
when strategies are discovered by name, loaded as plugins, or written by teams
outside the repository.

**First-class function or closure.** The Strategy type is a function type and the
concrete strategies are functions or lambdas. This removes the interface, the
classes, and the files, and keeps every property that mattered. Configuration is
carried by capture. This is the idiomatic form in TypeScript, Python, Go, Rust,
Kotlin, Swift and modern Java, and it is the default choice unless a named,
published, discoverable extension point is required. Its cost is that the
algorithm loses a stable name, which matters for registries, for logging, and
for error messages, and that a captured environment can retain memory that a
plain object would not.

The following comparison is the same design twice, and the second is the one to
reach for first in a language with closures.

```typescript
interface Backoff { delayMs(attempt: number): number; }
class ExponentialBackoff implements Backoff {
  constructor(private base: number) {}
  delayMs(attempt: number): number { return this.base * 2 ** attempt; }
}

type BackoffFn = (attempt: number) => number;
const exponential = (base: number): BackoffFn => (a) => base * 2 ** a;
```

The class form and the closure form are substitutable for the caller. The class
form buys a name, runtime type checks, and a place to hang extra methods later.
The closure form buys the deletion of two declarations.

**Enum-carrying-behaviour.** In Java, Kotlin, Swift and Rust an enumeration can
either implement the strategy interface per constant or be matched
exhaustively. This closes the family deliberately, which the interface form
cannot do, and gains compiler-checked exhaustiveness plus a natural
serialisation to a stable string. It is the right shape when the variants are
known, internal and few. It forbids third-party variants by design, which is a
feature when the set must stay closed and a blocker when it must not.

**Generic or monomorphised strategy.** In Rust, C++ and Go generics, the strategy
is a type parameter with a trait or interface bound. The compiler emits one
specialised copy per strategy, so dispatch disappears and inlining works. This is
how the Rust standard library's hash map accepts a hashing strategy at zero
runtime cost, see dimension 9. The trade is that the strategy is fixed at compile
time and cannot be chosen from configuration, and that binary size grows with the
number of instantiations. Rust makes both forms available side by side, `impl
Trait` or a generic parameter for the static form, a boxed trait object for the
dynamic one.

**Policy-based design, compile-time composition.** The C++ tradition of passing
several orthogonal policies as template parameters, each supplying one axis of
behaviour, so that one template composes many concrete types. Same trade as the
generic form, taken further. It multiplies compile time and produces error
messages that are hard to read, and it removes runtime cost entirely.

**Registry-backed strategy.** A map from a discriminator to a strategy instance
or constructor, populated at startup by the modules that own each algorithm. This
is how configuration-driven selection is normally implemented, and it is the
honest shape when the choice comes from a string. Its failure mode is that a
missing registration becomes a runtime error on first use rather than a compile
error, so registration coverage needs a test, see dimension 15.

**Null Object as a strategy.** A no-op strategy that satisfies the interface and
does nothing, installed as the default so the Context never has to check for
absence. This removes a null check from a hot path and from every reader's
attention. See the Null Object entry.

**Composite and decorated strategies.** Because a strategy is a value, strategies
compose. A composite strategy holds a list and applies them in order or picks the
first that answers. A decorating strategy wraps another and adds timing, caching,
logging or a circuit breaker. The `thenComparing` method on Java's comparator
interface is exactly a composite strategy in the standard library, verified from
the Java SE 21 specification, see dimension 9. This composability is one of the
strongest arguments for the pattern and one of the least discussed.

**Strategy as data.** The algorithm is expressed as a declarative rule that an
interpreter evaluates, rather than as code. Pricing rules, access policies and
routing rules commonly take this shape. It gains hot reload, auditability and
non-developer editing. It loses type safety and the debugger, and it slowly grows
its own language, which is the Interpreter pattern arriving without being invited.

**Language note on Go.** Go has interfaces without inheritance and functions as
values, so both forms are native and neither is unusual. The standard library
ships both in one package, `sort.Interface` for the type-implements form and
`sort.Slice` taking a `less` closure for the function form, verified from the Go
package documentation, see dimension 9. Go additionally allows a named function
type to carry methods, which is how a bare function can satisfy an interface
without a wrapper struct.

## 9. Known production uses

**Java standard library, `java.util.Comparator`.** The canonical production
Strategy. The interface is annotated as a functional interface and is documented
as a comparison function that imposes a total ordering on some collection of
objects. Sorting algorithms in `java.util.Collections` and `java.util.Arrays` are
written once against the interface, and the ordering rule is supplied by the
caller. The interface also ships composite and decorating strategies as default
and static methods, `thenComparing` for lexicographic composition, `reversed` for
inversion, `nullsFirst` and `nullsLast` for null handling, and `comparing` for
building a comparator from a key extractor. Oracle, *Java SE 21 API
Specification*, `java.util.Comparator`,
https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Comparator.html
verified 2026-08-02. This one example carries the whole pattern, the narrow
interface, the runtime substitution, the stateless shared instances, the function
form via the functional-interface annotation, and strategy composition.

**Go standard library, `sort.Interface` and `sort.Slice`.** `sort.Interface`
declares `Len`, `Less` and `Swap`, and `sort.Sort` runs one sorting algorithm
against any implementation. `sort.Slice` supplies the same ordering decision as a
closure instead of a type. The Go standard library therefore ships the interface
form and the function form of one Strategy in a single package, which is
unusually clear evidence that the two are the same pattern. Go project, *package
sort*, https://pkg.go.dev/sort verified 2026-08-02.

**Rust standard library, the hash map's `BuildHasher` parameter.** The hashing
algorithm is a type parameter on `HashMap`. `BuildHasher` is documented as a
trait for creating instances of `Hasher`, used by `HashMap` to create a hasher
per key so that keys are hashed independently of one another. The default is
`RandomState`, and callers substitute a different hasher for speed or for
determinism. This is the compile-time monomorphised variant from dimension 8, and
it demonstrates that a Strategy need not cost a dynamic dispatch. Rust project,
*std::hash::BuildHasher*,
https://doc.rust-lang.org/std/hash/trait.BuildHasher.html verified 2026-08-02.

**Passport.js authentication strategies.** Passport documents strategies as being
responsible for authenticating requests, which they accomplish by implementing an
authentication mechanism. A strategy is installed as a package, configured with a
verify function, registered with `passport.use(strategy)`, and selected per route
by name with `passport.authenticate`. The name of the pattern is the name of the
extension point, the registry is keyed by a string, and third-party packages
supply the concrete strategies. Passport, *Strategies*,
https://www.passportjs.org/concepts/authentication/strategies/ verified
2026-08-02. This is the registry-backed variant from dimension 8 in production.

**Spring Security, `PasswordEncoder`.** The interface is documented as a service
interface for encoding passwords, with `encode`, `matches` and `upgradeEncoding`.
Seventeen implementations ship with the framework, including
`BCryptPasswordEncoder`, `Argon2PasswordEncoder`, `Pbkdf2PasswordEncoder`,
`SCryptPasswordEncoder` and `NoOpPasswordEncoder`, and the documentation names
BCrypt as the preferred implementation. `DelegatingPasswordEncoder` is itself a
strategy that dispatches to others by a prefix stored in the encoded value, which
is the registry variant, and `upgradeEncoding` exists so that an application can
migrate between strategies without forcing a password reset. Spring,
*PasswordEncoder*,
https://docs.spring.io/spring-security/site/docs/current/api/org/springframework/security/crypto/password/PasswordEncoder.html
verified 2026-08-02.

**Django authentication backends.** `AUTHENTICATION_BACKENDS` holds a list of
dotted paths to classes implementing an `authenticate` method that takes a
request and credentials, defaulting to a single entry naming
`django.contrib.auth.backends.ModelBackend`. Django calls each backend in order
until one returns a user. This is a Strategy list rather than a single Strategy,
so it also carries a Chain of Responsibility flavour, which is worth naming
rather than glossing. The pluggable unit itself is a Strategy, the iteration over
several is the chain. Django Software Foundation, *Customizing authentication in
Django*, https://docs.djangoproject.com/en/5.2/topics/auth/customizing/ verified
2026-08-02.

## 10. Consequences

Positive.

- Conditionals over algorithm kind disappear from the context, and each algorithm
  becomes a unit that can be read, tested and reviewed without the surrounding
  machinery.
- Adding an algorithm requires no edit to existing code, so an algorithm can ship
  from a different module, a different team, or a different release.
- Algorithms become values, so they compose. Wrapping one strategy in another to
  add caching, timing or fallback needs no change to the context or to the
  wrapped algorithm.
- Each algorithm carries its own configuration, keeping parameters that concern
  one variant out of the context's signature.
- Runtime substitution supports per-tenant behaviour, feature flags, canary
  rollouts and A/B comparison of two implementations of the same computation.
- The context becomes testable against a stub algorithm, and each algorithm
  becomes testable without constructing the context.

Negative.

- The behaviour that actually runs is not visible at the call site, so reading
  the code no longer answers what happens. This cost is paid on every future read
  by every future reader and is the largest one.
- Type count grows in the class-based form. A family of eight algorithms costs
  nine types where a conditional cost none.
- The interface becomes a contract. Once external code implements it, changing
  the signature is a breaking change, and the interface tends to accrete methods
  requested by one implementor that every other implementor must then stub.
- Something must select the strategy. That selector is new code, it is often a
  conditional, and it can end up carrying the complexity the pattern was adopted
  to remove, see dimension 11.
- Runtime substitution introduces concurrency questions that the conditional did
  not have, around safe publication, mid-operation swaps, and shared mutable
  strategy state.
- The client is exposed to a choice it may not be qualified to make. GoF record
  this directly, that clients must understand how strategies differ before they
  can select one.
- Per-request strategy allocation in a hot path adds garbage-collection pressure
  where a branch added none.

## 11. Failure modes and misuse

Each item gives the observable symptom first, then the cause, then the fix.

**The switch moved, it did not leave.** Symptom. A code review shows a factory
file containing the same conditional that used to sit in the context, now
returning strategy objects instead of computing results, and adding an algorithm
still requires editing a shared file. Cause. Extract to classes was applied
without addressing selection. Fix. Replace the conditional with a lookup, a map
from the discriminator to the strategy, populated by each algorithm's own module
at load time, or by a container reading configuration. The distinction is that a
map is data that modules append to, while a switch is code that only its owner
can edit. When the selection is genuinely a small closed choice made once at
startup in a composition root, leave the conditional there and stop, because one
readable branch in one wiring file is not the problem the pattern was solving.

**Strategy interface with one implementation.** Symptom. An interface, one class
implementing it, one place constructing that class, and an editor whose go to
implementation command jumps straight through. Cause. The pattern applied to a
predicted variation that never arrived. Fix. Inline the implementation into the
context and delete the interface. Reintroduce it the day the second variant
appears, which takes minutes with tooling.

**The strategy that reaches back.** Symptom. The strategy holds a reference to
the context and calls `setStrategy` on it or mutates the context's fields.
Debugging becomes hard because behaviour depends on invocation history. Cause.
State was needed and Strategy was reached for. Fix. Recognise it as State,
document the transitions as a machine, and make the transition rules explicit.
See dimension 13.

**Interface widened for one implementor.** Symptom. Several concrete strategies
contain methods that throw an unsupported-operation error, return null, or are
empty. Cause. One algorithm needed an extra hook and the interface absorbed it.
Fix. Split into two interfaces, or move the extra behaviour into the algorithm's
own construction, or make the context query the strategy for a declared
capability rather than assuming every implementor has it. Cross reference the
principles family entry on the Interface Segregation Principle.

**Type check inside the context.** Symptom. A type test against a concrete
strategy class inside the context's method, followed by a branch. Cause. The
context needs information the interface does not carry. Fix. Add the information
to the interface as a declared member, for example a `costHint` or a
`supportsBatch` query, so that every implementor answers it explicitly. A type
test defeats the substitutability that motivated the pattern, and it silently
breaks for any strategy written after the check.

**Shared mutable strategy under concurrency.** Symptom. Wrong results that appear
only under load, only in production, and never reproduce in a single-threaded
test. A counter reads low. A cached value belongs to a different request. Cause.
A strategy instance that was stateless became stateful, and it was already being
shared as a singleton. Fix. Restore statelessness by passing per-call state as
arguments, or construct the strategy per operation, or synchronise its state
explicitly and document the requirement on the interface.

**Torn read during a swap.** Symptom. One request produces a result that no
single algorithm could produce, seen once, never reproduced, and dismissed as a
fluke. Cause. The context read its strategy field twice inside one operation
while a hot reload replaced it in between. Fix. Read the field once into a local
at method entry and use the local throughout, and publish the field safely for
the language's memory model.

**Strategy allocated per call in a hot path.** Symptom. Allocation rate and
garbage-collection pause frequency rise after a refactor that changed no
behaviour, with the strategy type at the top of the allocation profile. Cause.
A stateless strategy constructed inside the loop rather than hoisted. Fix. Hoist
it to a field or a shared constant, which is safe precisely because it is
stateless.

**Configuration naming a strategy that no longer exists.** Symptom. A service
starts, passes its health check, and fails on the first request that reaches the
strategy lookup, in one environment only. Cause. Registry-backed selection
resolves lazily and a rename was not propagated to configuration. Fix. Resolve
and validate every configured strategy name at startup and refuse to start on a
miss, which converts a production incident into a failed deploy.

**Strategy explosion by combination.** Symptom. Class names that stack three
adjectives, such as a compressed encrypted retrying upload strategy, and a count
of strategies equal to the product of two or three independent choices. Cause.
Several orthogonal axes of variation squeezed into one strategy interface. Fix.
Give each axis its own strategy and compose them by decoration, which turns a
multiplication into an addition. See dimension 13 on Decorator.

**Dead algorithms nobody removed.** Symptom. Eleven strategies in a package, and
production telemetry shows four ever run. Cause. Adding is free and removing is
nobody's task, so the family grows monotonically. Fix. Instrument selection as in
dimension 16, and treat a strategy with zero invocations over a full business
cycle as a deletion candidate.

## 12. Trade-off matrix

Compared against named alternatives across the forces from dimension 3.

| Force | Strategy (interface) | Strategy (function value) | Conditional or switch | Template Method | State | Sealed type with exhaustive match | Command | Rules as data |
|---|---|---|---|---|---|---|---|---|
| Adding a variant | New file, no edits | New function, no edits | Edit the switch | New subclass, no edits | New state class plus transition edits | Edit the sealed set, compiler lists every site | New command class | New rule row, no code change |
| Third-party variant possible | Yes | Yes | No | Yes, by subclassing | Yes | No, by design | Yes | Yes |
| Compiler reports a missing case | No | No | Only with a checked switch | No | No | Yes, its main advantage | No | No |
| Coupling of variant to context | None with push data flow | None | Total | High, bound by inheritance | High, states know each other | None | None, command owns its receiver | None |
| Runtime selection | Yes | Yes | Yes | Only by choosing a subclass | Yes, self-directed | Yes | Yes | Yes |
| Who decides the variant | Client or selector | Client or selector | The code itself | The subclass author | The object itself | Client | Client | The rule engine |
| Where the decision is visible | Wiring, away from use | Wiring, away from use | At the point of use | At construction | Nowhere, it is history | At the match site | At submission | In the rule store |
| Latency cost | One indirect call | One indirect call | One predictable branch | One virtual call | One indirect call | Direct, often inlined | One indirect call plus queueing | Interpretation overhead |
| Composability of variants | High, wrap and chain | High, wrap and chain | None | Low | Low | Low | High, queue and undo | Medium |
| Carries its own configuration | Yes, as fields | Yes, by capture | No, via parameters | Yes, as fields | Yes | Limited, as enum payload | Yes, as fields | Yes, as rule data |
| Cognitive load to read one path | Low | Low | Low for two cases, high past five | Medium, split across levels | High, needs the machine | Low | Medium | Medium |
| Cognitive load to answer what ran | High | High, worse, functions are unnamed | None | Medium | High | Low | High | High |
| Deferred or repeated execution | No | No | No | No | No | No | Yes, its purpose | No |
| Change without redeploy | Only if config-selected | Only if config-selected | No | No | No | No | No | Yes, its purpose |

Reading of the table. Strategy wins when the family is open and the variant must
be chosen by somebody other than the code doing the work. A sealed type with an
exhaustive match wins when the family is closed and internal, because it buys the
one thing Strategy cannot offer, a compiler error on a missing case. Template
Method wins when the skeleton is fixed and only steps vary, at the price of
binding variants by inheritance. State wins when the object drives its own
transitions. Command wins when the operation must be stored, queued, retried or
undone. Rules as data win when the behaviour has to change without a deploy, at
the price of type safety. A plain conditional wins for two cases that are never
going to be three, and it is the correct answer more often than pattern
literature admits.

## 13. Related and incompatible patterns

**State.** The one that matters most, because Strategy and State have the same
class diagram. Both put an interface between an object and a family of behaviours
that it delegates to. Four differences separate them in practice.

- *Who decides.* A Strategy is chosen by the client or by a selector outside the
  object. A State is entered by the object itself as a consequence of what has
  already happened. If the object picks its own next behaviour, it is State.
- *What the variation means.* Strategies are interchangeable answers to the same
  question, and it is meaningful to ask which is faster or cheaper. States are
  not interchangeable. An order that has shipped cannot be swapped back to draft
  because a faster algorithm was wanted.
- *Whether the parts know each other.* Concrete strategies do not reference one
  another. Concrete states routinely name their successors, because encoding the
  transition is the point.
- *Lifetime.* A strategy is usually fixed for an operation or for the object's
  life. A state changes many times over the object's life, and the sequence of
  changes is the behaviour.

Wikipedia's State article notes the structural overlap directly, describing State
as interpretable as a strategy that switches strategy through methods on the
pattern's interface
([Wikipedia, State pattern](https://en.wikipedia.org/wiki/State_pattern),
verified 2026-08-02). Treat that as confirmation that the structures are one and
the intents are two. A practical test, if you can draw a diagram with arrows
between the behaviours, it is State. If the behaviours have no relationship to
each other, it is Strategy.

**Template Method.** The inheritance-based alternative for the same goal, varying
part of an algorithm. Template Method fixes the skeleton in a base class and lets
subclasses override steps. Strategy replaces the whole algorithm through
composition. Template Method is cheaper when the skeleton is genuinely shared and
the variation is small, and it binds variants to a class hierarchy so that one
variant cannot be composed with another or swapped at runtime. Strategy costs
more structure and buys runtime substitution and composability. The two are also
routinely combined, a template method whose steps are supplied as strategies, or
a strategy whose implementations share a template base. See the Template Method
entry.

**Command.** Frequently confused because both wrap behaviour in an object. The
separation is what the object is for. A Strategy is how an operation is
performed, held by a context and invoked as part of the context's work, usually
taking arguments and returning a result. A Command is what to perform, a request
captured as an object with its arguments already bound, so it can be stored,
queued, logged, replayed or undone. If the object is placed on a queue,
persisted, or given an undo operation, it is a Command. If it is handed to
another object to change how that object computes, it is a Strategy. The two
compose, a command handler can select a strategy for its work.

**Bridge.** The same composition shape at a different scale and for a different
reason. Bridge separates an abstraction hierarchy from an implementation
hierarchy so both can vary independently, and it is a structural decision made
once for a whole subsystem. Strategy varies one operation and is expected to be
swapped often. A Bridge implementor is usually not interchangeable per call. GoF
place them in different chapters for this reason.

**Decorator.** Composes with Strategy and is the fix for strategy explosion from
dimension 11. A decorating strategy implements the same interface and wraps
another instance, adding timing, retry, caching, tracing or a fallback. Because
strategies are values with a uniform interface, decoration turns a multiplicative
family into an additive one.

**Composite.** Also composes. A composite strategy holds several strategies and
applies them in order, taking the first non-empty answer or accumulating all
results. The `thenComparing` method on Java's comparator interface is a composite
strategy in a standard library, verified from the Java SE 21 specification, see
dimension 9.

**Null Object.** The default strategy that does nothing, installed so the context
never checks for absence. Removes a branch and a class of null-reference defects.

**Factory Method and Abstract Factory.** The selection machinery. Something has
to produce the concrete strategy, and a factory is one honest answer, with a
registry or a container being the others. Abstract Factory becomes relevant when
several strategies must agree with each other, for example a serializer and a
deserializer that must use the same wire format. A single Strategy interface
cannot express that constraint, and pairing them by convention is exactly the
mismatch the family-consistency force in dimension 3 warns about. See the Factory
Method entry.

**Visitor.** An alternative when the variation depends on the type of the data
rather than on a caller's preference. A Strategy is chosen because somebody wants
a different algorithm. A Visitor dispatches on the concrete element type.
Reaching for Strategy when the real discriminator is the data's type produces a
strategy that begins its body with a type test.

**Singleton.** Conflicts in practice. Stateless strategies are naturally shared,
which is safe, but promoting the shared instance to a process-wide singleton with
mutable configuration reintroduces global state and makes tests order-dependent.
Share the value, avoid the pattern.

**Dependency injection with a container.** Not a rival, the usual selector. The
container is where the strategy is chosen, and it moves the selection from code
into configuration, which is where it belongs when the choice is environmental.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. The named refactoring is
Replace Conditional with Polymorphism, and the closure form is Replace Conditional
with a Function Parameter. Cross reference the refactoring family entries for
both. Ordered steps, each ending in a green test run.

1. Find the conditional and confirm every branch computes the same kind of result
   from the same kind of input. If a branch returns a different type or reads a
   different field of the enclosing object, stop. The branches are not a family
   and dimension 4 applies.
2. Extract each branch body into its own method on the current class, with an
   identical signature across all of them. This is a mechanical move and it is
   the step that reveals whether the signatures really can be unified. If a
   parameter is needed by only one branch, either compute it inside that branch
   or accept that the family is not yet coherent.
3. Narrow the signature. Remove any parameter that no branch reads, and replace a
   parameter that is a whole aggregate with the specific fields the branches use.
   This step decides the push versus pull question from dimension 5, and doing it
   before extracting types is far cheaper than doing it after.
4. Declare the Strategy interface with the single method that now exists, or the
   function type in a language with closures. Name it after the domain operation,
   a pricing rule, a retry policy, an encoder, never after the pattern.
5. Move each extracted method into its own implementation. Move only the method
   and the fields it uses. Run the tests.
6. Add the strategy field to the context and change the conditional to a
   delegation. The conditional now only chooses a strategy instance, and it does
   not compute anything. Run the tests. The pattern exists at this point, and the
   remaining work is about selection.
7. Move the selection outward. Push the conditional up into the caller, then into
   the caller's caller, until it reaches a composition root, a container
   configuration, or a registry lookup. It usually travels one or two levels
   before it lands somewhere it belongs. Stop when it reaches a place where the
   choice is genuinely made, and do not convert it to a lookup for its own sake.
   This is the step that dimension 11 says people skip.
8. Delete the discriminator if nothing else reads it. A leftover enumeration
   whose only consumer was the removed switch is a common residue and it invites
   somebody to switch on it again.
9. Add the selection telemetry from dimension 16 in the same change, while the
   mapping between discriminator and strategy is still in your head.

Removing the pattern when it stops earning its place. Signals that it should go
include a single implementation, a family that has been closed for years with no
third-party implementors, or a set of strategies that turn out to differ by one
constant.

1. Confirm the implementor set from telemetry rather than from the repository.
   A strategy implemented in another team's package will not appear in a local
   search, and deleting a published interface breaks them.
2. If the family is closed but plural, convert the interface into a sealed type
   or an enumeration and replace the dispatch with an exhaustive match. This
   keeps the separation of algorithm bodies while gaining a compiler error on a
   missing case. This is often the right destination rather than full removal.
3. If the family collapsed to one, inline that implementation back into the
   context and delete the interface. This is Inline Class, see the refactoring
   family entry.
4. If several strategies differ only in constants, replace them with one
   implementation holding those constants as fields, and delete the rest.
5. Remove the selector last, after nothing reads it, and delete the discriminator
   with it.

## 15. Testing and verification

This dimension is practice rather than sourced fact.

Easier because of the pattern.

- Each algorithm is a unit with no context to construct. A pricing rule extracted
  from an order processor can be tested with two numbers and no order, no
  database and no clock.
- The context is tested against a stub strategy that returns a fixed answer, so
  tests of the context's own logic, the validation and recording around the call,
  stop depending on any real algorithm's behaviour.
- Recording a call is trivial. A hand-written strategy that appends its arguments
  to a list gives a spy with no mocking framework, which keeps the test readable
  and the failure message meaningful.
- Comparative testing becomes possible. Two implementations of the same interface
  can be run against the same inputs and asserted equal, which is how a rewrite is
  validated against the implementation it replaces.
- Property-based testing has an obvious target. The interface's contract, for
  example that a comparator is antisymmetric and transitive, is a property that
  every implementation must satisfy.

Harder because of the pattern.

- Knowing which strategy a running system selected requires either an assertion
  on the wiring or a telemetry field, because no source line says. A test that
  passes with the wrong strategy installed is a real and common failure.
- Integration coverage now has a combinatorial edge. Every strategy times every
  context path is a larger matrix than the conditional had, and teams typically
  test the default strategy end to end and the others only in isolation, which
  leaves the interaction untested.
- Registry-backed selection fails at first use rather than at compile time, so
  the mapping needs its own test or a defect ships.

Techniques that apply.

- **Contract test, also called an abstract test case.** Write one test class
  against the Strategy interface with an abstract hook that supplies the
  implementation, then subclass it once per concrete strategy. Every
  implementation, including ones written later and by other teams, inherits the
  same suite. Publish the contract test alongside the interface when the interface
  is a public extension point, because it is the only practical way to tell an
  external implementor what the contract actually requires.
- **Registry completeness test.** Assert that every discriminator value the
  system accepts resolves to a strategy, and that every registered strategy
  satisfies the contract test. This converts the runtime failure from dimension 11
  into a build failure.
- **Wiring assertion.** One test per environment or per tenant configuration
  asserting that the expected concrete type is installed. Cheap, and it catches
  the class of defect where the code is correct and the configuration is not.
- **Hand-written stub over a mock.** Prefer a five-line class or a lambda to a
  mocking framework for a one-method interface. The stub is shorter than the mock
  setup, it survives an interface rename via the compiler, and it does not encode
  call-order expectations that nobody meant to assert.
- **Metamorphic or differential testing across strategies.** Where two strategies
  should agree, assert agreement over generated inputs. Where they should differ
  only in cost, assert that outputs match and compare timings separately.
- **Concurrency test for shared strategies.** If the strategy is documented as
  safe to share, run it from many threads against a shared instance and assert
  the results, because the failure mode from dimension 11 appears under load and
  nowhere else.

## 16. Observability signals

This dimension is practice. The pattern removes the algorithm's identity from the
source, so the identity has to appear in telemetry or the system becomes opaque
during an incident.

What to record.

- A stable strategy name on every operation, as a span attribute and as a
  structured log field. Use an explicit name declared by the strategy, not the
  class name, because a class rename should not break a dashboard, and because
  the closure form has no useful class name at all. Giving the interface a name
  member exists mostly for this reason.
- A counter of invocations labelled by strategy name. The label distribution is
  the single most useful signal the pattern produces, because it answers which
  algorithms are actually in use and which are dead code.
- A duration histogram labelled by strategy name. Strategies in one family
  frequently have order-of-magnitude different costs, and this is the graph that
  shows it.
- An error counter labelled by strategy name and error kind, so that one failing
  implementation is distinguishable from a failing context.
- A selection counter, incremented where the strategy is chosen rather than where
  it is used, labelled by the discriminator and the resolved strategy. This
  separates a selection fault from an execution fault, which are diagnosed
  differently.
- For hot-swappable strategies, a swap event log carrying the old name, the new
  name, the actor and the timestamp. A swap is a change to running behaviour and
  deserves the same audit treatment as a deploy.
- A gauge of the currently installed strategy per context, exported at scrape
  time, so a dashboard can answer what is running now without waiting for traffic.

A healthy instance on a dashboard. The invocation mix by strategy name matches
what the configuration and the tenant population predict, and it moves only when
a deploy or a configuration change explains the move. Each strategy's duration
distribution is stable and separately reasonable. Selection counts and invocation
counts track each other. No swap events appear outside change windows. Every
registered strategy has a non-zero count over a full business cycle.

A failing instance. A strategy name appears that should not exist in this
environment, which usually means a configuration default was left in place or a
plugin registered itself unexpectedly. Or one strategy's share climbs while the
others flatten, which points at a routing or tenancy fault upstream of the
selection rather than at the algorithms. Or the selection counter increments and
the invocation counter does not, which means strategies are being constructed and
discarded, the per-call allocation defect from dimension 11. Or one label
develops a long latency tail while the others stay flat, which localises the slow
implementation without reading any code. Or swap events appear during an incident,
which is either the mitigation or the cause and needs to be established early.

## 17. Security and privacy implications

This dimension is analytical rather than sourced. The pattern is close to silent
on security in its closed form, where every strategy ships in the same build and
the selection is a literal in a composition root. Five genuine implications
appear once selection or implementation opens up, and pretending to more than
that would be inventing a concern.

**Selection driven by untrusted input.** The strongest one. When the
discriminator that picks a strategy comes from a request header, a query
parameter, a form field or a token claim, an attacker chooses which algorithm
runs. The historical example of the resulting failure class is signature
algorithm confusion in JSON Web Tokens, where accepting the algorithm named in
the token's own header let a caller select a none algorithm or downgrade an
asymmetric verification to a symmetric one. The general rule follows from it.
Never resolve a security-relevant strategy from caller-supplied data. Resolve it
from server-side configuration keyed by something the server established, and
reject an unknown discriminator rather than falling back to a default.

**Dynamic loading of strategy implementations.** Registry-backed and
configuration-driven selection frequently means loading a class by name from a
string. If that string is attacker-influenced, class loading by name is a
remote-code-execution primitive rather than a configuration feature. Pin the set
of loadable strategies to an allowlist established at build time. Reject a name
that is not on it. Do not treat the implements-our-interface check as a control,
because the constructor and static initialiser run before any type check becomes
relevant.

**Registry poisoning and load order.** In the registry variant, whichever module
registers last for a key wins. A dependency that can register a strategy under an
existing key silently substitutes behaviour for every subsequent request, and the
substitution is invisible in the calling code. Make duplicate registration a
startup failure rather than an overwrite, and pin the expected registry contents
in a test.

**Uneven security properties across a family.** The pattern presents variants as
interchangeable, and the type system agrees, while their security properties
differ by orders of magnitude. The Spring Security `PasswordEncoder` family is
the clearest published example, since `NoOpPasswordEncoder` and
`BCryptPasswordEncoder` satisfy the same interface, and the framework documents
BCrypt as the preferred implementation, verified from the Spring Security API
documentation cited in dimension 9. The `upgradeEncoding` method exists precisely
so that an application can migrate away from a weak choice. The design lesson
generalises. When strategies differ in strength, the weak ones need a name that
says so, a deprecation path, and an alert when they are selected in production,
because the interface itself carries no warning.

**Timing and resource asymmetry as an oracle.** Two strategies in one family that
take measurably different time can leak which one was selected, and therefore leak
whatever the selection depends on. If the strategy is chosen per tenant or per
account tier, response time discloses tier. If it is chosen by whether a record
was found, it discloses existence. Where the selection itself is sensitive,
equalise the observable cost or remove the caller's ability to influence the
choice.

On privacy the pattern is neutral in itself, with one operational caveat that
follows from dimension 16. Strategy names are recommended as log and span
attributes, and a strategy name can encode a customer, a region, a
data-residency tier or a contract level, for example a class named after a named
client. Where names carry that, treat the field as attributable data under the
same retention, access and export rules as any other identifier, or use an opaque
stable identifier in telemetry and keep the mapping elsewhere.

## Code examples

Four languages, chosen because each shows a different genuine shape. TypeScript
shows the interface form and the closure form side by side. Python shows the
protocol form and the plain-callable form that Python libraries actually use. Go
shows the interface form and the function-type form that the standard library
itself ships. Rust shows both the dynamic form with a trait object and the
monomorphised generic form that costs no dispatch. Java is omitted from the
examples because the comparator interface in dimension 9 already carries the
classical form better than a synthetic sample would. C# is omitted because its
shape matches the Java one with a delegate in place of the functional interface,
and repeating it would add length without adding a lesson.

The running example is a checkout total with a pluggable discount rule.

### TypeScript

Interface form.

```typescript
interface DiscountRule {
  readonly name: string;
  apply(cents: number, itemCount: number): number;
}

class NoDiscount implements DiscountRule {
  readonly name = "none";
  apply(cents: number): number {
    return cents;
  }
}

class PercentOff implements DiscountRule {
  readonly name: string;
  constructor(private readonly percent: number) {
    this.name = `percent-${percent}`;
  }
  apply(cents: number): number {
    return Math.round(cents * (1 - this.percent / 100));
  }
}

class BulkDiscount implements DiscountRule {
  readonly name = "bulk";
  constructor(
    private readonly threshold: number,
    private readonly percent: number,
  ) {}
  apply(cents: number, itemCount: number): number {
    if (itemCount < this.threshold) return cents;
    return Math.round(cents * (1 - this.percent / 100));
  }
}

class Checkout {
  constructor(private rule: DiscountRule = new NoDiscount()) {}

  setRule(rule: DiscountRule): void {
    this.rule = rule;
  }

  total(prices: number[]): number {
    const rule = this.rule;
    const gross = prices.reduce((a, b) => a + b, 0);
    return rule.apply(gross, prices.length);
  }
}

const cart = [1200, 3400, 800];
console.log(new Checkout(new PercentOff(10)).total(cart));
console.log(new Checkout(new BulkDiscount(3, 25)).total(cart));
```

The single read of the rule field into a local at the top of `total` is the
mid-operation swap guard from dimension 7, and it costs nothing.

Closure form, which deletes the interface and all three classes.

```typescript
type Discount = (cents: number, itemCount: number) => number;

const none: Discount = (c) => c;
const percentOff = (p: number): Discount => (c) => Math.round(c * (1 - p / 100));
const bulk = (n: number, p: number): Discount => (c, items) =>
  items < n ? c : Math.round(c * (1 - p / 100));

const totalWith = (rule: Discount, prices: number[]): number =>
  rule(
    prices.reduce((a, b) => a + b, 0),
    prices.length,
  );

const capped = (inner: Discount, floor: number): Discount => (c, items) =>
  Math.max(inner(c, items), floor);

console.log(totalWith(none, cart));
console.log(totalWith(percentOff(10), cart));
console.log(totalWith(capped(bulk(3, 25), 4000), cart));
```

The `capped` function is a decorating strategy from dimension 8. It wraps any
rule without either rule knowing about the other, and it is one type declaration
away from the class hierarchy above.

### Python

Protocol form, which gives structural typing without forcing implementors to
inherit anything.

```python
from typing import Protocol


class DiscountRule(Protocol):
    name: str

    def apply(self, cents: int, item_count: int) -> int: ...


class PercentOff:
    def __init__(self, percent: int) -> None:
        self.percent = percent
        self.name = f"percent-{percent}"

    def apply(self, cents: int, item_count: int) -> int:
        return round(cents * (1 - self.percent / 100))


class BulkDiscount:
    name = "bulk"

    def __init__(self, threshold: int, percent: int) -> None:
        self.threshold = threshold
        self.percent = percent

    def apply(self, cents: int, item_count: int) -> int:
        if item_count < self.threshold:
            return cents
        return round(cents * (1 - self.percent / 100))


class Checkout:
    def __init__(self, rule: DiscountRule) -> None:
        self._rule = rule

    def total(self, prices: list[int]) -> int:
        rule = self._rule
        return rule.apply(sum(prices), len(prices))


CART = [1200, 3400, 800]
print(Checkout(PercentOff(10)).total(CART))
print(Checkout(BulkDiscount(3, 25)).total(CART))
```

The callable form, which is what Python libraries usually ship. The standard
library uses it too, since the `key` argument of the built-in `sorted` function
is an ordering strategy supplied as a plain callable.

```python
from collections.abc import Callable

Discount = Callable[[int, int], int]


def percent_off(percent: int) -> Discount:
    return lambda cents, _items: round(cents * (1 - percent / 100))


def bulk(threshold: int, percent: int) -> Discount:
    def rule(cents: int, items: int) -> int:
        if items < threshold:
            return cents
        return round(cents * (1 - percent / 100))

    return rule


RULES: dict[str, Discount] = {
    "none": lambda cents, _items: cents,
    "spring": percent_off(10),
    "wholesale": bulk(3, 25),
}


def total(rule_name: str, prices: list[int]) -> int:
    rule = RULES[rule_name]
    return rule(sum(prices), len(prices))


print(total("spring", CART))
print(total("wholesale", CART))
```

The `RULES` mapping is the registry from dimension 8. Adding a rule appends a row
rather than editing a conditional, and the missing-key failure it introduces is
the one that dimension 15 says to cover with a completeness test.

### Go

Both forms, as the standard library ships them in the sort package.

```go
package main

import "fmt"

type DiscountRule interface {
	Name() string
	Apply(cents, itemCount int) int
}

type percentOff struct{ percent int }

func (p percentOff) Name() string { return fmt.Sprintf("percent-%d", p.percent) }

func (p percentOff) Apply(cents, _ int) int {
	return cents * (100 - p.percent) / 100
}

type bulk struct{ threshold, percent int }

func (b bulk) Name() string { return "bulk" }

func (b bulk) Apply(cents, itemCount int) int {
	if itemCount < b.threshold {
		return cents
	}
	return cents * (100 - b.percent) / 100
}

type Checkout struct{ rule DiscountRule }

func (c Checkout) Total(prices []int) int {
	rule := c.rule
	gross := 0
	for _, p := range prices {
		gross += p
	}
	return rule.Apply(gross, len(prices))
}

// A named function type carrying methods satisfies the same interface
// without a wrapper struct. This is the shape sort.Slice relies on.
type DiscountFunc func(cents, itemCount int) int

func (f DiscountFunc) Name() string { return "func" }

func (f DiscountFunc) Apply(cents, items int) int { return f(cents, items) }

func main() {
	cart := []int{1200, 3400, 800}
	fmt.Println(Checkout{percentOff{10}}.Total(cart))
	fmt.Println(Checkout{bulk{3, 25}}.Total(cart))
	flat := DiscountFunc(func(c, _ int) int { return c - 500 })
	fmt.Println(Checkout{flat}.Total(cart))
}
```

### Rust

Rust offers the choice between dispatch and no dispatch explicitly, which makes
the trade from dimension 8 visible in the type signature rather than hidden.

```rust
trait DiscountRule {
    fn name(&self) -> &str;
    fn apply(&self, cents: u64, item_count: usize) -> u64;
}

struct PercentOff {
    percent: u64,
}

impl DiscountRule for PercentOff {
    fn name(&self) -> &str {
        "percent"
    }
    fn apply(&self, cents: u64, _items: usize) -> u64 {
        cents * (100 - self.percent) / 100
    }
}

struct Bulk {
    threshold: usize,
    percent: u64,
}

impl DiscountRule for Bulk {
    fn name(&self) -> &str {
        "bulk"
    }
    fn apply(&self, cents: u64, items: usize) -> u64 {
        if items < self.threshold {
            cents
        } else {
            cents * (100 - self.percent) / 100
        }
    }
}

// Dynamic. The rule is chosen at runtime, one indirect call per use.
struct DynCheckout {
    rule: Box<dyn DiscountRule>,
}

impl DynCheckout {
    fn total(&self, prices: &[u64]) -> u64 {
        let gross: u64 = prices.iter().sum();
        self.rule.apply(gross, prices.len())
    }
}

// Static. The rule is a type parameter, monomorphised, no dispatch.
struct Checkout<R: DiscountRule> {
    rule: R,
}

impl<R: DiscountRule> Checkout<R> {
    fn total(&self, prices: &[u64]) -> u64 {
        let gross: u64 = prices.iter().sum();
        self.rule.apply(gross, prices.len())
    }
}

fn main() {
    let cart = [1200u64, 3400, 800];
    let dynamic = DynCheckout {
        rule: Box::new(PercentOff { percent: 10 }),
    };
    println!("{} {}", dynamic.rule.name(), dynamic.total(&cart));

    let stat = Checkout {
        rule: Bulk {
            threshold: 3,
            percent: 25,
        },
    };
    println!("{} {}", stat.rule.name(), stat.total(&cart));
}
```

The two checkout types express the same design with opposite cost profiles. The
boxed trait object allows the rule to arrive from configuration and pays one
indirect call. The generic form is the shape the Rust standard library uses for
the hashing strategy on its hash map, cited in dimension 9, and it fixes the rule
at compile time in exchange for full inlining.

**Compilation status.** The Python sample was run with `python3` and prints the
expected totals. The Go sample was compiled and run with `go run` and prints
three totals. The TypeScript samples were type-checked with `npx tsc` under
`--strict` and run with `node` after compilation. The Rust sample was compiled
and run with `rustc` where a toolchain was available, and the compilation result
is reported honestly in the authoring notes for this entry. It uses no unstable
feature and no external crate. The `RULES` mapping in the Python sample and the
`cart` constant in the TypeScript closure sample depend on identifiers defined in
the preceding block of the same language, so those pairs are meant to run
together rather than in isolation.

## 18. References

1. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides. *Design Patterns.
   Elements of Reusable Object-Oriented Software*. Addison-Wesley, 1994.
   ISBN 0-201-63361-2. Chapter 5, Behavioral Patterns, section Strategy. Source
   of the intent, the three participants, the client-must-understand-strategies
   consequence, and the separation from State and Template Method by chapter
   placement.
2. Oracle. *Java SE 21 API Specification*, `java.util.Comparator`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Comparator.html
   Verified 2026-08-02. Source for the canonical production Strategy, the
   functional-interface declaration, the total-ordering contract, and the
   composite and decorating members `thenComparing`, `reversed`, `nullsFirst`,
   `nullsLast` and `comparing`.
3. Go project. *Package sort*. https://pkg.go.dev/sort Verified 2026-08-02.
   Source for `sort.Interface` with its `Len`, `Less` and `Swap` methods, and for
   `sort.Slice` taking a less function, used as evidence that the interface form
   and the function form are one pattern.
4. Rust project. *Rust standard library documentation*, `std::hash::BuildHasher`.
   https://doc.rust-lang.org/std/hash/trait.BuildHasher.html Verified 2026-08-02.
   Source for the monomorphised strategy variant and for the hash map production
   use, including the statement that a `BuildHasher` is used by `HashMap` to
   create a hasher per key.
5. Passport. *Strategies*.
   https://www.passportjs.org/concepts/authentication/strategies/ Verified
   2026-08-02. Source for the registry-backed production use, the `passport.use`
   registration, and selection by strategy name.
6. Spring. *Spring Security API documentation*,
   `org.springframework.security.crypto.password.PasswordEncoder`.
   https://docs.spring.io/spring-security/site/docs/current/api/org/springframework/security/crypto/password/PasswordEncoder.html
   Verified 2026-08-02. Source for the `encode`, `matches` and `upgradeEncoding`
   contract, the seventeen shipped implementations including `NoOpPasswordEncoder`
   and `BCryptPasswordEncoder`, the documented preference for BCrypt, and the
   `DelegatingPasswordEncoder` registry variant used in dimension 17.
7. Django Software Foundation. *Django 5.2 documentation*, "Customizing
   authentication in Django".
   https://docs.djangoproject.com/en/5.2/topics/auth/customizing/ Verified
   2026-08-02. Source for `AUTHENTICATION_BACKENDS`, its single-entry default
   naming `ModelBackend`, the ordered attempt across backends, and the
   `authenticate` method signature taking a request and credentials.
8. Wikipedia contributors. "Strategy pattern".
   https://en.wikipedia.org/wiki/Strategy_pattern Verified 2026-08-02. Used to
   confirm the runtime-selection framing of the intent and the Policy alias, not
   as a source of explanation.
9. Wikipedia contributors. "State pattern".
   https://en.wikipedia.org/wiki/State_pattern Verified 2026-08-02. Used to
   confirm the documented structural overlap between State and Strategy quoted in
   dimensions 1 and 13.
