---
name: Open Closed Principle
slug: open-closed-principle
family: 04-principles-and-laws
category: Principle
aliases: [OCP, Open-Closed Principle, the O in SOLID]
first_described: "Meyer 1988"
maturity: canonical
related: [strategy, template-method, decorator, factory-method, dependency-inversion-principle, liskov-substitution-principle]
incompatible_with: []
verified: 2026-08-02
---

# Open Closed Principle

## 1. Name, aliases, and lineage

The canonical name is the Open Closed Principle, almost always shortened to
OCP, and it is the O in the SOLID acronym. Bertrand Meyer introduced it in his
1988 book, *Object-Oriented Software Construction*, Prentice Hall, first
edition, in the chapter on modularity, and restated it in the 1997 second
edition. Meyer's own phrasing was that a module should be open, meaning
available for extension by adding fields or functions, and closed, meaning
available for use by other modules through a well defined and stable
interface. His mechanism for satisfying both at once was inheritance, a
subclass adding behaviour to a parent class that itself never changes once
compiled and shipped (verified against a Wikipedia summary of the original
text, en.wikipedia.org/wiki/Open-closed_principle, verified 2026-08-02).

Robert C. Martin reformulated the principle in a 1996 C++ Report article
titled "The Open-Closed Principle", moving the mechanism away from Meyer's
implementation inheritance and toward abstract interfaces and polymorphic
substitution. In Martin's version, a client depends on an abstraction, and new
behaviour arrives as a new class implementing that abstraction rather than as
a subclass reaching into a parent's internals. Martin folded this reformulated
principle into the SOLID set later. Michael Feathers is credited with coining
the SOLID acronym itself around 2004, gathering five principles Martin had
already been teaching, with Martin's own foundational paper on the underlying
principles dated to his 2000 paper "Design Principles and Design Patterns"
(verified against a Wikipedia summary of the SOLID article,
en.wikipedia.org/wiki/SOLID, verified 2026-08-02).

The distinction between the two formulations matters enough that this entry
treats them as two named variants rather than one idea with a fuzzy history.

- **Meyer's OCP.** Extension through subclassing of a concrete or abstract
  base class. The base class can carry real, shared implementation. New
  behaviour is added by a subclass that overrides or extends what the parent
  provides. This is the older, weaker form, and it still permits a form of
  modification because a subclass can override a virtual method and change
  observable behaviour in a way the base author did not anticipate.
- **Martin's OCP, the polymorphic form.** Extension through implementing an
  abstraction the client already depends on. The abstraction is a pure
  interface or an abstract class with no shared state to inherit incorrectly.
  Clients are written against the abstraction only, so a new implementation
  can be added without the client, or the abstraction, changing at all. This
  is the form embedded in SOLID and the form this entry treats as the working
  definition, because it is the one that composes cleanly with the Liskov
  Substitution Principle and the Dependency Inversion Principle.

## 2. Problem and context

A piece of software that ships once and never changes does not need this
principle. The principle exists because software that is used gets extended,
and every extension is a chance to break something that already worked.

The concrete shape in a codebase looks like this. A function or a class
contains a conditional, an if chain or a switch statement, that dispatches on
a type code, a string tag, or an enum value, and each branch implements one
variant of a behaviour. A tax calculator branches on jurisdiction. A shipping
cost estimator branches on carrier. A discount engine branches on promotion
type. The first version of this code is honest and readable. The trouble
starts at the second and third requirement to add a new variant, because each
addition means opening the same function, adding a branch, and redeploying
every caller of that function even though their own behaviour did not change.

Two costs compound as the branches grow. The first is regression risk, because
touching a function that many callers depend on to add branch six risks
breaking branches one through five, and the whole function must be retested
even though five of six variants are untouched. The second is coupling, because
the function that owns the conditional must import and know about every
concrete variant, so the module that was supposed to be a stable core keeps
growing a dependency on every new feature added anywhere in the system.

The context in which OCP is the right answer has two conditions. The variation
is genuinely going to keep happening along a known axis, meaning a new tax
jurisdiction or a new carrier is a predictable future event, not a one-off. And
the cost of an added layer of abstraction is smaller than the recurring cost
of editing and retesting the shared branch. When variation is truly closed,
when there will only ever be three tax jurisdictions and that is a business
fact, adding an abstraction for a fourth that will never arrive is a cost with
no matching benefit, and dimension 4 below says so explicitly.

## 3. Forces

- **Extensibility versus current simplicity.** An interface plus one
  implementation is more code, more indirection, and more files than a single
  function with one branch. The force pulls toward the interface only when a
  second implementation is a real, near-term event, not a hypothetical one.
- **Regression risk versus development speed.** A closed core that nobody
  edits to add a feature cannot regress from that edit. But building the
  abstraction correctly the first time takes longer than writing the branch,
  and a wrong abstraction is worse than none, because it must be reworked
  under load once the second and third implementations reveal it does not fit.
- **Coupling direction.** OCP in its polymorphic form inverts a dependency, the
  core depends on an interface it owns rather than on the concrete variants.
  This favours the core's stability at the cost of an extra hop for a reader
  tracing from the interface to a concrete implementation, which a language
  without strong navigation tooling makes genuinely harder to follow.
- **Cognitive load for the reader.** A conditional with six branches is legible
  top to bottom in one file. Six classes each implementing an interface are
  individually simple but the reader must hold the interface contract in mind
  while jumping between files. OCP trades local simplicity for global
  stability, and that trade is a net loss on a young, small, rarely extended
  codebase.
- **Team topology.** OCP earns its keep fastest when the people adding a new
  variant are not the people who own the core, a plugin author extending a
  framework they cannot recompile, a vendor writing a driver against a
  published interface. When one team owns both the core and every variant,
  the coordination cost the principle removes barely existed in the first
  place.
- **Cost of premature closure.** Closing an abstraction too early, guessing the
  wrong seam for future variation, produces speculative generality, an
  interface built for extension that never arrives while the extension that
  does arrive does not fit the guessed seam at all.

## 4. Applicability and non-applicability

Apply OCP when all of the following hold.

- New variants of a behaviour are added on a recurring, foreseeable schedule,
  not a one-time event. A payment provider integration, a new file format
  exporter, a new notification channel.
- The variants share a genuinely common contract, so every variant can
  honestly implement the same method signatures with the same pre and post
  conditions, and the abstraction does not leak variant-specific parameters
  through the shared interface.
- The people who will add future variants are not always the people who wrote
  the core, or even when they are the same people, changing the core module
  carries real deployment or review cost, a shared library, a published SDK, a
  module other teams depend on.
- The current conditional has already grown past roughly three or four
  branches and shows a visible pattern of one new branch per release cycle.

Do NOT apply OCP, and prefer the plain conditional or a simple lookup table,
when any of the following hold.

- The set of variants is closed by a fact about the world, not by a lack of
  imagination. Days of the week, the four suits of a card deck, the seven
  HTTP methods a server actually needs to support. Building an interface for
  an eighth day that will never exist is speculative generality, named as an
  anti-pattern by Martin Fowler and Kent Beck's refactoring catalog under that
  exact term (Martin Fowler, *Refactoring, Improving the Design of Existing
  Code*, 2nd edition, Addison-Wesley, 2018, chapter 3, Bad Smells in Code,
  Speculative Generality section, referenced against Fowler's own online
  catalog at refactoring.com/catalog, verified 2026-08-02).
- There is exactly one implementation today and no credible second one in
  sight. YAGNI, the "you aren't gonna need it" heuristic from Extreme
  Programming, applies directly here, add the seam when the second
  implementation actually arrives, not before.
- The variants genuinely need different method signatures or different
  preconditions, because forcing them into one shared interface produces a
  Liskov Substitution Principle violation, an implementation that throws on a
  parameter every other implementation accepts.
- Performance is on the hot path and the added indirection of a virtual call
  or an interface dispatch is measured to matter. A JPEG decoder's innermost
  pixel loop is the wrong place for a Strategy object per pixel.
- The team is small, the codebase is young, and requirements are still
  actively changing shape at the level the abstraction would need to close
  over. Closing an interface before the domain model has stabilised locks in
  a guess.

## 5. Structure

The polymorphic form, the working definition for this entry, has three
participants.

- **Abstraction.** An interface or an abstract base class, owned by the same
  module as the client, declaring the operations the client needs without any
  concrete implementation detail. This is the seam. It never changes once
  clients depend on it, except by a deliberate, versioned, breaking change.
- **Client.** The code that consumes the abstraction to do its job. It holds a
  reference to the abstraction type, never to a concrete implementation type,
  and it is written once and never edited again to accommodate a new variant.
- **Concrete Implementation.** A class implementing the abstraction, one per
  variant. New behaviour arrives as a new Concrete Implementation, added
  alongside the existing ones, wired in through composition or dependency
  injection, never by editing the Client or the Abstraction.

A fourth, often implicit participant is the **Composition Root**, the place,
usually at application start up or in a dependency injection container's
configuration, that decides which Concrete Implementation the Client receives.
This is the one place in the system that does know about every concrete
variant, and that is intentional, the knowledge is concentrated at the edge of
the system rather than distributed through every consumer.

## 6. ASCII structure diagram

```
+-------------------------------------+
| Client                              |
| (never edited to add a new variant) |
+-------------------------------------+
           | uses
           v
+----------------------------+
| Abstraction  <<interface>> |
| operation()                |
+----------------------------+
           ^
           | implements
     +-----+-----+-----+
     |           |     |
+---------------------+ +---------------------+ +---------------------+
| ConcreteImpl A      | | ConcreteImpl B      | | ConcreteImpl C (new)|
| operation()         | | operation()         | | operation()         |
+---------------------+ +---------------------+ +---------------------+
     ^           ^     ^
     +-----+-----+-----+
           | wired by
           v
+-----------------------+
| Composition Root      |
| (knows every variant, |
| only place that does) |
+-----------------------+
```

## 7. Dynamics

```
Adding variant C to a system already open under OCP:

  1. Author writes a new class ConcreteImpl-C implementing Abstraction.
     -> Abstraction file: UNCHANGED
     -> Client file:       UNCHANGED
     -> ConcreteImpl-A, B: UNCHANGED, no retest needed

  2. Author registers ConcreteImpl-C at the Composition Root.
     -> Composition Root:  ONE new registration line added

  3. At runtime, Client calls operation() through the Abstraction reference.
     Client:           call operation()
        |
        v
     Abstraction:      dispatch to whichever ConcreteImpl was injected
        |
        v
     ConcreteImpl-C:   executes, returns result to Client

  4. Client never knows, at compile time or read time, that C exists.
     Only the Composition Root and the test suite for C know.

Contrast, the closed-core-with-conditional shape this principle replaces:

  1. Author opens the shared function/switch that already has branches A, B.
  2. Author adds branch C inline.
  3. Every caller of the shared function is now running a recompiled,
     re-reviewed, re-tested artifact, even the callers only exercising A or B.
```

## 8. Implementation variants

- **Interface plus classes, the canonical mainstream OOP shape.** A named
  interface, one class per variant, wired by constructor injection. This is
  the shape most closely matching Martin's 1996 reformulation and is the
  default in Java, C#, Go, TypeScript, and Kotlin.
- **Abstract base class with template methods.** Meyer's original mechanism.
  Shared implementation lives in the base class, variant behaviour lives in
  overridden methods. This composes with the Template Method pattern
  (`template-method` in this catalog) and remains genuinely useful when
  variants share real, procedural logic, not only a shared contract.
- **First class functions or closures.** In languages with first class
  functions, JavaScript, TypeScript, Python, Go, Rust, the Strategy shape
  collapses to passing a function value instead of an object implementing a
  one-method interface. This is functionally the same closure over OCP, a new
  variant is a new function passed in, and neither the caller nor the other
  variants are edited.
- **Plugin registry with runtime lookup.** The Composition Root is replaced
  by a registry that discovers implementations at start up, a directory scan,
  a service locator, an entry point mechanism such as Python's
  `importlib.metadata.entry_points` or a Go `init()` side-effect import. This
  is the shape used when the party adding a new variant is a separate
  deployable artifact, a plugin package, rather than code in the same build.
- **Data driven extension, the middle ground.** Where the variance is purely
  in configuration values, not behaviour, a lookup table or a rules engine
  reading external data achieves the same closed-core property without any
  polymorphism at all, extension is adding a row, not a class. This is
  frequently the right choice and is undervalued relative to the OOP shape,
  because a table is easier to review, test, and reason about than a class
  hierarchy when the actual variation is only in data.

## 9. Known production uses

- **The Java Servlet Filter chain.** The `javax.servlet.Filter` interface (now
  `jakarta.servlet.Filter`) lets a container add cross-cutting request
  processing, authentication, logging, compression, by registering new filter
  classes in `web.xml` or via annotations, without modifying the servlet
  container itself or any existing filter. This is Martin's polymorphic OCP
  applied directly to HTTP middleware (Jakarta Servlet Specification, version
  6.0, section 6, "Filtering", jakarta.ee/specifications/servlet/6.0/,
  verified 2026-08-02).
- **The Strategy pattern in the Java Collections Framework's `Comparator`.**
  `java.util.Collections.sort` and `java.util.Arrays.sort` accept a
  `Comparator<T>` parameter, and both methods have been unchanged since Java 2
  while thousands of independent, unrelated `Comparator` implementations have
  been written against that same closed interface. This is the textbook case
  of a stable core, `sort`, extended without modification by every new
  ordering a caller supplies (Oracle Java SE documentation,
  docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Comparator.html,
  verified 2026-08-02).
- **The Django REST Framework's pluggable permission and authentication
  classes.** Django REST Framework's `APIView` reads a `permission_classes`
  and `authentication_classes` list of classes implementing
  `BasePermission`/`BaseAuthentication`, so a project adds a new
  authentication scheme, an API key header, an OAuth provider, by writing a
  new class and listing it, never by editing DRF's `APIView` dispatch code
  (Django REST Framework documentation, "Permissions" and "Authentication",
  www.django-rest-framework.org/api-guide/permissions/, verified 2026-08-02).

## 10. Consequences

Positive.

- A stable core module, once its abstraction is right, can be extended
  indefinitely by new callers without a new release of the core itself, which
  is the property that lets a library or framework author ship a 1.0 that
  third parties can build on for years.
- Regression risk for an added feature is confined to the new implementation
  and its own tests. The existing, already-shipped implementations are
  provably untouched because their source files did not change.
- The abstraction becomes a contract that different teams, or a vendor and its
  customers, can develop against independently and in parallel, since neither
  side needs write access to the other's code.

Negative.

- Indirection. A reader following a call from the Client to the actual
  behaviour must jump through the Abstraction to a Concrete Implementation
  that is chosen somewhere else entirely, the Composition Root, which is
  strictly harder to trace by eye than a conditional with the logic inline.
- The abstraction, once clients depend on it, is genuinely closed, and getting
  it wrong is expensive. A method signature missing a parameter that a third
  variant needs forces either a breaking interface change, which defeats the
  whole point, or a workaround, an optional parameter nobody else uses, a
  second overload, a cast, that erodes the contract's honesty over time.
- Applied where variation never actually recurs, OCP is pure cost, extra
  files, extra indirection, extra onboarding time, for a flexibility the
  system never exercises. This is the speculative generality failure mode
  named in dimension 4 and again in dimension 11.

## 11. Failure modes and misuse

- **Symptom.** A one-implementation interface sits in the codebase for years,
  `IPaymentProcessor` with exactly one class, `StripePaymentProcessor`,
  implementing it, and every call site takes the interface type as a
  parameter. **Cause.** The abstraction was built speculatively, anticipating
  a second payment provider that never arrived, following a rule of thumb
  rather than an actual near-term requirement. **Fix.** Collapse the interface
  back into the concrete class, per YAGNI, and reintroduce the interface only
  when a real second implementation is being written, at which point
  extracting it is a five-minute refactor with the second implementation as
  proof the seam is drawn in the right place.
- **Symptom.** A new business requirement cannot be satisfied by any existing
  implementation of a shared interface, and the fix is adding an optional
  parameter with a default value to the interface's method signature, which
  every other implementation ignores. **Cause.** The abstraction's contract
  was drawn around the first implementation's needs rather than around the
  genuine common behaviour across variants, so the interface leaks
  implementation-specific concerns. **Fix.** Split the interface along the
  axis that is actually varying, per the Interface Segregation Principle, so a
  variant that needs the extra parameter gets its own, narrower interface
  rather than polluting the shared one.
- **Symptom.** A subclass implementing an interface throws
  `NotImplementedException`, or its equivalent, from one of the interface's
  methods, or silently no-ops it. **Cause.** This is a Liskov Substitution
  Principle violation riding on top of an OCP-shaped design, the
  implementation cannot honestly fulfil the contract, and someone forced it to
  compile anyway rather than admitting the abstraction does not fit this
  variant. **Fix.** Narrow the interface so the offending method is not part
  of the contract this variant must implement, again via interface
  segregation, or accept that this variant does not belong under this
  abstraction at all.
- **Symptom.** Adding a new variant class compiles and passes its own tests,
  but a shared, central switch statement elsewhere in the codebase, a
  serializer, a factory, a UI renderer, was not updated, and the new variant
  silently falls through a default case or renders as a placeholder in
  production. **Cause.** The codebase is only partially closed, one seam is
  polymorphic, but a second, undocumented seam still branches on the same type
  and was never converted, so extension at the first seam creates a gap at the
  second. **Fix.** Audit every place that already switches on the variant's
  discriminator and either convert every seam to the same polymorphic shape,
  or, at minimum, add an exhaustiveness check at each remaining switch, an
  enum-based switch with a compiler warning on missing cases in TypeScript, a
  sealed interface with an exhaustive `when` in Kotlin, or a linter rule, so a
  missed seam fails the build instead of failing silently at runtime.
- **Symptom.** The Composition Root itself grows an enormous, brittle
  conditional deciding which Concrete Implementation to wire up, and that
  conditional gets edited on every release. **Cause.** This is not actually a
  failure of OCP, the Client and the individual implementations remain closed,
  but teams sometimes report it as one because the pain moved rather than
  disappeared. **Fix.** Recognise that concentrating the "which variant"
  decision in one place is the intended trade, and if that one place is itself
  painful to maintain, address it with a data-driven registry or a plugin
  lookup mechanism, not by reopening the Client.

## 12. Trade-off matrix

| Force | OCP (polymorphic, interface + classes) | Plain conditional / switch | Template Method (Meyer's OCP) | Data-driven table lookup |
|---|---|---|---|---|
| Cost to add variant | Low, one new file, no edit to existing code | Low upfront, rising cost as branches accumulate | Low, but new variant must fit the parent's assumed algorithm skeleton | Lowest, a new row, no code at all |
| Regression risk on addition | Near zero for existing variants | Rises with branch count, whole function must be retested | Low if the parent's shared steps are stable | Near zero, no code path changes |
| Readability for a small, fixed set | Worse, indirection for no real benefit | Best, everything is in one place | Moderate | Best, if variation truly is only data |
| Fit when variants share real algorithmic steps, and not only a contract | Requires duplicating shared steps in each class, unless composed with Template Method | N/A, logic is inline | Best fit, shared steps live once in the parent | Poor fit, cannot express shared procedural logic |
| Fit when a third party adds variants without touching your source | Best fit, this is the case the principle targets | Impossible without editing your source | Possible but requires subclassing your base class, tighter coupling than an interface | Impossible unless the table itself is externally editable |
| Performance on a hot path | One extra virtual dispatch per call, usually negligible, matters in tight inner loops | Fastest, branch prediction on a small, stable switch is very cheap | Same cost as OCP interface form | Fastest for simple value lookups, slower if the "value" requires arbitrary logic |

## 13. Related and incompatible patterns

- **Strategy (`strategy` in this catalog).** Strategy is the design pattern
  that is the most direct, common realisation of Martin's polymorphic OCP, an
  interchangeable family of algorithms behind one interface, selected by the
  Client's owner rather than hardcoded. Where OCP is the principle, Strategy
  is frequently the pattern that implements it.
- **Template Method (`template-method` in this catalog).** Realises Meyer's
  original, inheritance-based OCP directly, a base class fixes the algorithm's
  skeleton and closes it, subclasses extend by filling in the varying steps.
  Composes with polymorphic OCP when the base class itself is an abstract
  class satisfying an interface other code depends on.
- **Decorator (`decorator` in this catalog).** Extends an object's behaviour
  by wrapping it in another object implementing the same interface, which is
  itself an OCP-respecting way to add behaviour, logging, caching, retry,
  without modifying the wrapped object's class.
- **Factory Method (`factory-method` in this catalog).** Frequently sits at
  the Composition Root's edge, providing the mechanism by which a new
  Concrete Implementation gets constructed and handed to a Client without the
  Client's own code naming the concrete type.
- **Liskov Substitution Principle (`liskov-substitution-principle`, if present
  in this catalog).** OCP and LSP are inseparable in practice. OCP's promise
  that a Client can accept any Concrete Implementation of the Abstraction only
  holds if every implementation actually honours LSP, substitutable for the
  Abstraction with no surprising behaviour. A codebase that violates LSP while
  claiming OCP compliance is open for extension only in shape, not in
  behaviour.
- **Dependency Inversion Principle (`dependency-inversion-principle`, if
  present in this catalog).** DIP is the mechanism that makes OCP achievable
  at the module level, the Client depends on an abstraction it or a shared,
  stable module owns, rather than on the concrete, volatile implementations,
  which is exactly the inversion the Composition Root exploits.
- **Incompatible with a premature, ungrounded abstraction.** OCP is actively
  harmful when applied to speculative generality, as detailed in dimensions 4
  and 11, there is no pattern name for the misuse, only the anti-pattern
  itself.

## 14. Refactoring path in and out

Introducing OCP into code that currently branches on a type code.

1. Identify the recurring conditional, the switch statement, if-chain, or
   dictionary of functions, that already has at least three branches and has
   grown at least once in the project's history.
2. Extract the interface the branches all conform to. Look at what each branch
   actually does, not what it is named, the shared method signature is the
   honest common behaviour, not a guess at future needs.
3. Convert each branch's body into its own class implementing that interface,
   one class per existing branch. This step is mechanical and should not
   change behaviour, it is Martin Fowler's Extract Class refactoring applied
   repeatedly (Martin Fowler, *Refactoring*, 2nd edition, Addison-Wesley,
   2018, catalog entry "Extract Class").
4. Replace the conditional with a lookup from a discriminator value to the
   corresponding implementation, a map, a dependency-injected list, or a
   registry, at the Composition Root.
5. Delete the original conditional once every call site goes through the new
   Abstraction. Run the full regression suite for the module before and after
   this deletion, this is the step where behavioural equivalence is actually
   proven, not merely assumed.
6. Add the new variant that motivated the refactor as one new class, with no
   further edits to the Client or the Abstraction.

Removing OCP when the abstraction has outlived its usefulness, most commonly
because the variant set has shrunk to one and stayed there.

1. Confirm there is exactly one Concrete Implementation left, and no credible
   plan for a second, by checking the actual call sites, not by assumption.
2. Inline the sole implementation's method bodies directly into the Client,
   Fowler's Inline Class, the reverse of step 3 above.
3. Delete the Abstraction and the Composition Root wiring for it.
4. Keep the test suite that exercised the old interface, retargeted at the
   now-concrete Client, since the tests still document the same required
   behaviour.

## 15. Testing and verification

OCP makes unit testing the Client trivially easy and dangerous in a specific
way if done carelessly, both need naming plainly.

The easy part, the Client can be tested with a hand-written test double
implementing the Abstraction, a mock, a stub, or a fake, entirely decoupled
from any real Concrete Implementation's side effects, database calls, network
calls. Since the Client only ever calls through the Abstraction, a test double
is a first-class, legitimate implementation of that same interface, not a
special case requiring a mocking framework's magic.

The dangerous part, contract tests are mandatory and are the piece teams skip.
If each Concrete Implementation is unit tested against its own bespoke
expectations rather than against one shared contract test suite run against
every implementation, it is possible for implementation B to violate a
precondition or postcondition that implementation A happens to honour, and the
Client, which only ever exercised implementation A in its own tests, never
catches the mismatch between the two. The fix is a single, shared contract
test suite, parameterised over every registered Concrete Implementation,
asserting the Abstraction's contract, not any one implementation's internal
behaviour. This directly operationalises the Liskov Substitution Principle as
a test, rather than as a hoped-for property.

Integration testing at the Composition Root should assert that every variant
the system is meant to support is actually reachable through the registry or
the dependency injection configuration, catching the "compiles, passes its own
tests, never actually wired in" failure mode from dimension 11.

## 16. Observability signals

- Log or trace which Concrete Implementation was selected for a given request
  or operation, tagged as a dimension on the trace span, since a bug reported
  against "the payment flow" is frequently a bug in exactly one implementation
  and this tag is what lets an on-call engineer skip straight to it.
- Track a metric of calls per Concrete Implementation over time. A variant
  whose call count silently drops to zero after a supposedly unrelated change
  elsewhere is the signature of the "new variant registered but old routing
  logic still branches around it" failure mode.
- Emit a startup-time log line enumerating every Concrete Implementation the
  Composition Root discovered and wired, especially for a plugin-lookup
  variant of the pattern. A missing entry in that log at deploy time is the
  cheapest possible detection of a variant that failed to register.
- A healthy instance of this pattern in production shows call volume
  distributed across implementations matching the expected traffic mix, and
  error rates that are implementation-scoped, a raised error rate confined to
  one Concrete Implementation's tag, not smeared across all of them, which
  would instead suggest the shared Abstraction or Client has the bug.

## 17. Security and privacy implications

The Composition Root is the security-relevant surface of this pattern, because
it is the one place that decides which code actually runs for a given input,
and that decision is frequently driven by external data, a request header, a
tenant identifier, a configuration value read from a database. If that
discriminator value is attacker-controlled and used to select a Concrete
Implementation from a dynamically loaded registry, a plugin scan from an
untrusted directory, a class loaded by a fully attacker-supplied string name,
the pattern becomes an arbitrary code execution vector, the same shape as
an unsafe deserialization bug. The mitigation is an explicit allowlist at
the Composition Root, the discriminator value is validated against a known,
closed set of registered implementations before dispatch, never used to
construct a class name, a file path, or a module import string directly.

Where different Concrete Implementations of the same Abstraction handle data
with different sensitivity levels, a `LocalFileStorage` implementation and a
`ThirdPartyCloudStorage` implementation behind one `IFileStorage` interface,
OCP's uniformity is itself a hazard, the interface's contract does not, and
cannot, in principle, encode which implementations are approved for a given
data classification. That governance has to live outside the type system, in
the Composition Root's wiring policy or in a separate access-control layer,
and should be documented as a deliberate exception in dimension 17 for any
concrete pattern instance handling regulated or sensitive data, since the
interface itself is silent on it.

## 18. References

1. Bertrand Meyer, *Object-Oriented Software Construction*, Prentice Hall,
   1988, chapter on modularity, the original open-closed formulation.
   Referenced via summary at
   https://en.wikipedia.org/wiki/Open%E2%80%93closed_principle, verified
   2026-08-02.
2. Robert C. Martin, "The Open-Closed Principle", *C++ Report*, 1996, the
   polymorphic reformulation. Referenced via summary at
   https://en.wikipedia.org/wiki/Open%E2%80%93closed_principle, verified
   2026-08-02.
3. Robert C. Martin, "Design Principles and Design Patterns", 2000, the paper
   collecting the principles later named SOLID by Michael Feathers around
   2004. Referenced via
   https://en.wikipedia.org/wiki/SOLID, verified 2026-08-02.
4. Martin Fowler and Kent Beck, *Refactoring, Improving the Design of Existing
   Code*, 2nd edition, Addison-Wesley, 2018, chapter 3, "Bad Smells in Code",
   Speculative Generality, and the Extract Class and Inline Class catalog
   entries. Catalog cross-referenced at https://refactoring.com/catalog/,
   verified 2026-08-02.
5. Joshua Bloch, *Effective Java*, 3rd edition, Addison-Wesley, 2018, Item 1,
   used in this catalog family for the adjacent static-factory distinction
   referenced from the Factory Method entry, cited here for consistency of
   terminology around construction versus extension.
6. Jakarta Servlet Specification, version 6.0, section 6, "Filtering",
   https://jakarta.ee/specifications/servlet/6.0/, verified 2026-08-02, cited
   for the Filter chain production use in dimension 9.
7. Oracle, Java SE 21 API documentation, `java.util.Comparator`,
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Comparator.html,
   verified 2026-08-02, cited for the sort/Comparator production use in
   dimension 9.
8. Django REST Framework documentation, "Permissions" and "Authentication",
   https://www.django-rest-framework.org/api-guide/permissions/, verified
   2026-08-02, cited for the pluggable permission classes production use in
   dimension 9.

## Code examples

### TypeScript

```typescript
interface DiscountStrategy {
  apply(amountCents: number): number;
}

class NoDiscount implements DiscountStrategy {
  apply(amountCents: number): number {
    return amountCents;
  }
}

class PercentOffDiscount implements DiscountStrategy {
  constructor(private readonly percent: number) {}
  apply(amountCents: number): number {
    return Math.round(amountCents * (1 - this.percent / 100));
  }
}

// New variant. Zero edits to Checkout or to the two classes above.
class FixedAmountOffDiscount implements DiscountStrategy {
  constructor(private readonly offCents: number) {}
  apply(amountCents: number): number {
    return Math.max(0, amountCents - this.offCents);
  }
}

class Checkout {
  constructor(private readonly discount: DiscountStrategy) {}
  total(amountCents: number): number {
    return this.discount.apply(amountCents);
  }
}

const a = new Checkout(new NoDiscount()).total(10000);
const b = new Checkout(new PercentOffDiscount(20)).total(10000);
const c = new Checkout(new FixedAmountOffDiscount(1500)).total(10000);
console.log(a, b, c);
```

### Python

```python
from abc import ABC, abstractmethod


class DiscountStrategy(ABC):
    @abstractmethod
    def apply(self, amount_cents: int) -> int:
        raise NotImplementedError


class NoDiscount(DiscountStrategy):
    def apply(self, amount_cents: int) -> int:
        return amount_cents


class PercentOffDiscount(DiscountStrategy):
    def __init__(self, percent: float) -> None:
        self.percent = percent

    def apply(self, amount_cents: int) -> int:
        return round(amount_cents * (1 - self.percent / 100))


# New variant. Zero edits to Checkout or to the two classes above.
class FixedAmountOffDiscount(DiscountStrategy):
    def __init__(self, off_cents: int) -> None:
        self.off_cents = off_cents

    def apply(self, amount_cents: int) -> int:
        return max(0, amount_cents - self.off_cents)


class Checkout:
    def __init__(self, discount: DiscountStrategy) -> None:
        self.discount = discount

    def total(self, amount_cents: int) -> int:
        return self.discount.apply(amount_cents)


if __name__ == "__main__":
    print(Checkout(NoDiscount()).total(10000))
    print(Checkout(PercentOffDiscount(20)).total(10000))
    print(Checkout(FixedAmountOffDiscount(1500)).total(10000))
```

### Go

```go
package main

import "fmt"

type DiscountStrategy interface {
	Apply(amountCents int) int
}

type NoDiscount struct{}

func (NoDiscount) Apply(amountCents int) int {
	return amountCents
}

type PercentOffDiscount struct {
	Percent float64
}

func (d PercentOffDiscount) Apply(amountCents int) int {
	return int(float64(amountCents) * (1 - d.Percent/100))
}

// New variant. Zero edits to Checkout or to the two types above.
type FixedAmountOffDiscount struct {
	OffCents int
}

func (d FixedAmountOffDiscount) Apply(amountCents int) int {
	result := amountCents - d.OffCents
	if result < 0 {
		return 0
	}
	return result
}

type Checkout struct {
	Discount DiscountStrategy
}

func (c Checkout) Total(amountCents int) int {
	return c.Discount.Apply(amountCents)
}

func main() {
	fmt.Println(Checkout{NoDiscount{}}.Total(10000))
	fmt.Println(Checkout{PercentOffDiscount{Percent: 20}}.Total(10000))
	fmt.Println(Checkout{FixedAmountOffDiscount{OffCents: 1500}}.Total(10000))
}
```
