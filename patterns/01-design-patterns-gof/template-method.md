---
name: Template Method
slug: template-method
family: 01-design-patterns-gof
category: Behavioral
aliases: [Template Function, Skeleton Algorithm, Hook Method Pattern]
first_described: "Gamma, Helm, Johnson, Vlissides 1994"
maturity: canonical
related: [factory-method, strategy, bridge, decorator, chain-of-responsibility, builder]
incompatible_with: []
verified: 2026-08-02
---

# Template Method

## 1. Name, aliases, and lineage

The canonical name is Template Method. It sits in the Gang of Four catalog among
the behavioral patterns, described in Erich Gamma, Richard Helm, Ralph Johnson
and John Vlissides, *Design Patterns. Elements of Reusable Object-Oriented
Software*, Addison-Wesley, 1994, chapter 5 (Behavioral Patterns), Template
Method. The stated intent is to define the skeleton of an algorithm in an
operation while deferring some steps to subclasses, so that subclasses redefine
individual steps without changing the algorithm's structure. The category
placement and the intent wording are confirmed in the
[Wikipedia summary of the pattern](https://en.wikipedia.org/wiki/Template_method_pattern),
verified 2026-08-02.

The name is stable across communities, which is unusual for a GoF pattern. A few
variations appear in practice.

- **Template Function** is used in C++ writing where the word method carries
  Smalltalk baggage. It has nothing to do with C++ function templates, and the
  collision causes real confusion in code review. When a C++ reader hears
  "template" they think of compile-time generics. The pattern is a runtime
  virtual dispatch mechanism with the opposite binding time.
- **Skeleton Algorithm** or **skeletal implementation** appears in library
  documentation and in Java standard library naming, where classes prefixed with
  `Abstract` supply the skeleton and leave a small number of primitive
  operations to the implementor.
- **Hook Method Pattern** names the pattern by its extension surface rather than
  by its fixed part. This framing appears in framework documentation, where the
  fixed algorithm is invisible to the application programmer and the only thing
  they touch is the hook.

The most important piece of vocabulary attached to this pattern is not a name
for the pattern itself, but a name for its control flow. The GoF book labels the
inverted control structure the **Hollywood Principle**, expressed as "Don't call
us, we'll call you". The subclass never invokes the algorithm step by step. The
base class owns sequencing and calls down into the subclass at the points it
chose. This inversion is described in the pattern's consequences discussion and
is the reason Template Method is the backbone of framework design rather than
of application design. The labelling of the inverted control structure as the
Hollywood principle in the context of this pattern is documented in the
[SourceMaking treatment of Template Method](https://sourcemaking.com/design_patterns/template_method),
verified 2026-08-02, which reproduces the GoF framing that frameworks implement
the invariant parts of an application area and define placeholders for
customisation.

Two further pieces of lineage matter for reading modern code.

Template Method predates the GoF catalog as an informal practice. Class
libraries in Smalltalk-80 and the Model-View-Controller lineage already relied on
overriding a small set of primitive operations inside a fixed framework
algorithm. The GoF contribution is the naming and the analysis of hooks versus
abstract operations, not the invention.

The pattern also gave rise to a widely misapplied idea, **Inversion of Control**.
Inversion of Control as a general term now covers dependency injection,
event-driven callbacks, and framework-owned main loops. Template Method is one
specific mechanism that produces the inversion, implemented through inheritance.
Treating the two as synonyms is a category error, because dependency injection
achieves the same inversion with composition and no subclass.

## 2. Problem and context

Two or more procedures do the same thing in the same order, and differ in a small
number of steps in the middle. The duplication is not textual enough for a naive
extract-method to remove, because the varying steps are interleaved with the
common ones.

This shows up in a codebase in a recognisable shape. A file contains two methods
of eighty lines each. Side by side, lines 1 to 22 are identical, lines 23 to 31
differ, lines 32 to 60 are identical again, lines 61 to 66 differ, and the tail
is identical. Somebody added the second method by copying the first and editing
two regions. A third variant is now requested. The reviewer knows the copy is
wrong and cannot say precisely what to do instead, because the parts that differ
are not at the boundaries where a function could be cleanly extracted.

Concrete instances of that shape.

- A data import pipeline that opens a source, validates a header, parses rows,
  applies business rules, writes to a store, and emits a summary. CSV, JSON and
  a fixed-width mainframe extract differ in how the header is validated and how
  a row is parsed. Everything else is identical, including the transaction
  boundaries and the error accounting.
- A request handler that authenticates, authorises, deserialises a body,
  performs an action, serialises a response and records a metric. The action is
  different per endpoint. The surrounding six steps must not vary, because
  varying them is how a security check gets skipped on one route.
- A test fixture that acquires a database, populates it, runs an assertion body,
  and tears the database down whether or not the assertion body threw. The
  assertion body is the only part any test author writes.
- A build step that resolves dependencies, compiles, runs a linter, packages,
  and uploads an artifact. Language plugins vary compile and lint, and must not
  be able to skip the upload step or reorder it.

The context that makes Template Method correct rather than merely available has
four properties.

- **The order is a real constraint, not a coincidence.** If the steps could be
  reordered without consequence, there is no algorithm to protect, and a list of
  independent functions is the honest shape.
- **The fixed part carries obligation.** Transaction commit, resource release,
  audit logging, metric emission. Something in the skeleton must happen and the
  variant author must not be able to forget it. This is the property that makes
  the pattern earn its cost, and it is the property most missing from tutorial
  examples that use it to print a coffee recipe.
- **The variation is known at type-definition time, not at request time.** A
  subclass is chosen when the object is constructed. If the variant is selected
  per call from a runtime value, the shape is Strategy, see dimension 12.
- **The set of variants is open to code the skeleton author has not seen.** The
  framework ships, applications extend. If everything lives in one repository
  and one team owns all of it, a simpler shape often wins.

Outside that context the pattern hardens a design that wanted to stay soft, see
dimension 4.

## 3. Forces

This dimension is engineering judgement about which pressure wins, stated as
reasoning rather than as sourced fact.

- **Duplication.** Favoured strongly. This is the pattern's primary purchase.
  One copy of the sequencing logic, N copies of only the steps that genuinely
  differ. On a five-step algorithm with two varying steps and four variants, the
  saving is real and compounds every time the fixed part changes.
- **Control over sequencing.** Favoured. The skeleton author decides the order
  and the variant author cannot alter it. For a security or transactional
  envelope this is the whole point, because it converts a convention that
  reviewers must police into a structure the language enforces.
- **Coupling.** Sacrificed heavily, and this is the pattern's defining cost. The
  subclass and the base class are bound by inheritance, which is the tightest
  coupling most languages offer. The subclass depends not on the base class's
  published interface but on its internal call sequence, its protected members
  and its assumptions about when hooks fire. Changing the base class can break
  subclasses that compile against it, which is the fragile base class problem
  analysed in dimension 11.
- **Cognitive load.** Sacrificed. Reading a concrete variant does not tell you
  what the program does. A reader must hold two files open, the skeleton and the
  variant, and mentally interleave them. Debugging is worse, because the call
  stack alternates between the two classes and the reader must reconstruct which
  frame belongs to which file. The GoF book's own advice to minimise the number
  of primitive operations exists because this load grows fast.
- **Consistency.** Favoured. Every variant, including ones written years later
  by people who never read the design document, performs the fixed steps in the
  fixed order. That property is very hard to obtain any other way once the
  variant count passes a handful.
- **Extensibility along one axis.** Favoured. Adding a variant is a new subclass
  and no edit to existing code, which is the Open Closed Principle applied to an
  algorithm. Adding a second, orthogonal axis of variation is where the pattern
  fails, because single inheritance gives you one axis and combinatorial
  subclassing gives you a class per pair.
- **Latency.** Effectively neutral. A virtual call per hook is noise against any
  step that touches memory in bulk, a socket or a disk. It matters in a hot loop
  in C++ or Rust where devirtualisation fails, and it matters when the hook is
  called once per row on a million-row import rather than once per file.
- **Operability.** Mildly sacrificed. A stack trace names the base class method,
  and the concrete variant appears only as the receiver type. An operator
  reading a truncated trace can misattribute a failure to the framework when the
  fault is in an application hook.
- **Cost of change.** Asymmetric, and the asymmetry is the thing to plan around.
  Adding a variant is cheap. Adding a step to the skeleton is cheap when it has
  a default. Changing the meaning, order or signature of an existing hook is
  expensive and ripples into every downstream repository that subclassed you.
  Published skeletons are therefore very hard to evolve, which is why library
  authors version them so conservatively.
- **Team topology.** Favoured for a platform team plus many application teams,
  and this is the topology the pattern was designed for. It is a poor fit for a
  single team that owns everything, because the ceremony buys governance the
  team does not need.

A pattern with no sacrifice is a language feature. Template Method buys
consistency and sequencing control, and pays for them in coupling and in how
hard the base class becomes to change later.

## 4. Applicability and non-applicability

Reach for Template Method when these hold.

- Several procedures share an order of operations and differ in a bounded number
  of interior steps.
- The fixed part contains an obligation that a variant author must not be able
  to skip, reorder or forget. Resource release, commit and rollback, audit
  writes, permission checks.
- You are writing a framework or a library and the variants will be authored by
  people you will never meet, in code you will never read.
- A class hierarchy already exists for other reasons, so the subclass is not a
  new concept invented purely to hold one method.
- You want to control precisely which extension points exist. Template Method is
  a closed extension surface. The subclass can override only what you declared
  overridable, which is a governance property, not merely a design one.
- The refactoring target is existing duplicated code and the varying regions are
  interleaved with fixed ones, so extract-function alone will not remove the
  duplication.

Non-applicability. Do NOT reach for Template Method in these cases. The reason
matters more than the rule, because each of these is a real design that people
force into the pattern's shape.

- **The variant is chosen at runtime from data.** A config value, a request
  header, a database column, a feature flag. Subclass identity is fixed at
  construction. Expressing a runtime choice through subclasses forces a factory
  that maps the value to a class, which is the original conditional plus a
  hierarchy. Strategy holds the varying behaviour in a field and can be swapped
  between calls, which is what the requirement actually asks for.
- **The algorithm has two or more independent axes of variation.** Storage
  backend crossed with serialisation format gives four combinations, then six,
  then nine. Single inheritance cannot express two axes without multiplying the
  classes. Bridge, or two composed Strategy objects, models this correctly.
- **The subclass would override every step.** If nothing is fixed, there is no
  skeleton, and the base class is an interface wearing an abstract class costume.
  Declare an interface and drop the inheritance.
- **There is exactly one variant and no concrete second one requested.** A
  skeleton with one implementation is a single procedure split across two files
  for no benefit. This is speculative generality, and the cost is paid every
  time somebody reads it. Cross reference the code smell family entry on
  speculative generality.
- **The language has no inheritance.** In Go and in Rust the classical shape does
  not exist. Both languages have an idiomatic equivalent, see dimension 8, and
  forcing an embedded-struct imitation of a base class in Go produces something
  that looks like the pattern and does not dispatch like it, because Go has no
  virtual method dispatch on embedded fields.
- **The variants belong to different teams on different release schedules and
  you cannot coordinate a breaking change.** Publishing an inheritance-based
  extension point is a commitment to a very wide compatibility surface, wider
  than an interface, because subclasses depend on your internal call order.
  Prefer publishing an interface the framework calls, so your only commitment is
  a signature.
- **The steps are genuinely independent and could run in any order.** A pipeline
  of independent transformations is a list, and a list is easier to test,
  reorder, and configure than a hierarchy.
- **You need to modify behaviour of an existing object at runtime, per
  instance.** Decorator wraps an instance. Template Method binds at class
  definition and cannot be changed for one object after construction.
- **The only shared part is a try or finally block.** Many languages already have
  a first-class construct for that. Python context managers, C# `using`, Java
  try-with-resources, Go `defer`. Using the language construct is cheaper and
  reads better than a skeleton class.

## 5. Structure

Three participant roles, and the third one is optional but is where most of the
design decisions live.

- **AbstractClass.** Owns the template method, which is a concrete method
  containing the fixed algorithm. It declares the primitive operations the
  template method calls. It is the only participant that knows the order. It is
  normally abstract so that it cannot be instantiated, and the template method
  itself is normally marked non-overridable, `final` in Java, `sealed` in C#
  when overriding a virtual, so a subclass cannot replace the sequencing it
  exists to protect.
- **PrimitiveOperation, also called an abstract step.** A declared operation with
  no body that a subclass must supply. The compiler rejects a subclass that
  omits it. Use this when no single correct default exists and every variant
  must make a choice.
- **HookOperation, also called a hook.** A declared operation with a body, often
  empty or returning a neutral value, that a subclass may override. The base
  class calls it at a defined point in the algorithm. Use this for optional
  behaviour and for extension points added after the base class shipped.
- **ConcreteClass.** Implements every primitive operation and overrides whichever
  hooks it cares about. It never calls the primitive operations directly and it
  never reimplements the sequencing. Its public surface is often only the
  inherited template method.

The distinction between the two kinds of step is the design decision that
separates a well-shaped skeleton from a badly-shaped one, and it deserves stating
plainly.

An **abstract step** is a demand. It says the algorithm cannot proceed without a
decision only the variant can make, and the compiler enforces that the decision
is made. It is a compile-time guarantee, and its cost is that adding one to a
published base class breaks every existing subclass. You cannot add an abstract
step to a shipped library without a major version.

A **hook** is an offer. It says the algorithm has a sensible default and the
variant may intervene. It is source-compatible to add, because existing
subclasses inherit the default and keep working. Its cost is silence. A variant
that meant to override and misspelled the name, or that overrode a hook the base
class stopped calling, fails quietly and produces wrong behaviour rather than a
build error. Languages with an explicit `override` keyword that is checked,
C#, Kotlin, Swift, and Java's `@Override` annotation, remove the misspelling half
of that risk and not the stopped-calling half.

The default-implementation decision therefore reduces to a single question. Is
there a correct behaviour for a variant that does not care about this step? If
yes, the step is a hook with that behaviour as its body. If no, it is abstract.
A hook whose default body throws an exception is neither, it is an abstract step
that traded a compile error for a runtime one, and it should be declared
abstract unless the base class is a published type that cannot break its
existing subclasses.

Relationships. ConcreteClass inherits from AbstractClass. The call direction is
from AbstractClass down into ConcreteClass, which is the inversion. No
association arrow points from ConcreteClass to AbstractClass at the call level,
because the subclass never initiates. The client holds an AbstractClass
reference and calls the template method.

## 6. ASCII structure diagram

```
   +---------------------------------------+
   |            AbstractClass              |
   |---------------------------------------|
   | + templateMethod()      <final>       |
   |     stepOne()                         |
   |     primitiveA()        <abstract>    |
   |     stepTwo()                         |
   |     hookB()             <default body>|
   |     stepThree()                       |
   |---------------------------------------|
   | - stepOne()  - stepTwo()  - stepThree()   fixed, private
   | # primitiveA()          abstract, must override
   | # hookB()               concrete default, may override
   +---------------------------------------+
                    ^                  ^
           extends  |                  |  extends
                    |                  |
   +--------------------------+   +--------------------------+
   |     ConcreteClassA       |   |     ConcreteClassB       |
   |--------------------------|   |--------------------------|
   | # primitiveA()  supplied |   | # primitiveA()  supplied |
   |   (hookB not overridden) |   | # hookB()       supplied |
   +--------------------------+   +--------------------------+

   Calls travel DOWN the arrows at runtime, from AbstractClass into the
   subclass. The subclass never calls templateMethod's internals.
   That inversion is the Hollywood Principle.
```

## 7. Dynamics

The runtime property worth stating first. The client calls one method. Every
other call in the flow originates inside the base class. The subclass is passive
and is entered only when the skeleton reaches a point where it decided to ask.

```
Client        ConcreteClassA        AbstractClass.templateMethod
  |                  |                        |
  |-- new ConcreteClassA() ----------------->|
  |                  |                        |
  |-- templateMethod() ------------------->  (inherited, runs in base)
  |                  |                        |
  |                  |            stepOne()   |   fixed, base only
  |                  |<---------- primitiveA()|   virtual, reaches subclass
  |                  |-- returns ------------>|
  |                  |            stepTwo()   |   fixed, base only
  |                  |<---------- hookB()     |   virtual
  |                  |   (not overridden:     |
  |                  |    base default runs)  |
  |                  |          stepThree()   |   fixed, always runs
  |<-- result -------|------------------------|
  |                  |                        |
```

The failure-path flow is the half that justifies the pattern and is normally
omitted from diagrams. When a primitive operation throws, the skeleton is still
the frame that owns cleanup.

```
Client        ConcreteClassA        AbstractClass.templateMethod
  |                  |                        |
  |-- templateMethod() ------------------->  begin
  |                  |            acquire()   |   fixed
  |                  |<---------- primitiveA()|
  |                  |-- throws ------------->|
  |                  |                        |  catch / finally in base
  |                  |            rollback()  |   fixed, cannot be skipped
  |                  |            release()   |   fixed, cannot be skipped
  |<-- error --------|------------------------|
  |                  |                        |
```

Three timing notes that cause real defects.

First, the template method must not be called from the base class constructor,
and neither must any primitive operation or hook. Joshua Bloch states the rule
without qualification, that constructors must not invoke overridable methods
directly or indirectly, and that violating it will produce program failure, in
*Effective Java*, 3rd edition, Item 19, "Design and document for inheritance or
else prohibit it". The rule and its reasoning are reproduced in the
[community summary of Effective Java Item 19](https://github.com/david-sauvage/effective-java-summary/blob/master/README.md),
verified 2026-08-02. Bloch extends the same prohibition to `clone` and
`readObject`, because both run before the object is fully constructed in the
same sense.

The mechanism behind that failure differs by language, and the difference decides
whether the hazard exists at all. Pattern write-ups routinely flatten the three
cases into one, so they are worth separating.

- **Java and Kotlin. The classic hazard.** The base constructor body runs before
  the subclass field initialisers, so an override executes against a subclass
  whose fields still hold null or zero. This is the case Item 19 describes.
- **C#. The hazard is real but the ordering is reversed.** The C# compiler emits
  a derived class's inline field initialisers at the top of its own constructor,
  where they run before the base constructor is invoked. Microsoft's engineering
  write-up demonstrates it with a program that prints `200 100` rather than
  `100 200`, and states that the compiler "inserts initialization code at the
  very beginning of the instance constructor and this initialization code gets
  invoked before the base instance constructor",
  [Execution order between base and derived inline instance field initializers](https://learn.microsoft.com/en-us/archive/blogs/marcod/execution-order-between-base-and-derived-inline-instance-field-initializers),
  verified 2026-08-02. An inline-initialised field is therefore already set when
  a base constructor makes a virtual call. Anything assigned in the derived
  constructor body is not, so constructor-injected collaborators are the usual
  casualty. Narrower than Java's version of the defect, and equally real.
- **Swift. The compiler forbids it.** Two-phase initialisation makes the hazard
  unreachable rather than merely discouraged. Safety check 1 requires of a
  designated initializer that "all of the properties introduced by its class are
  initialized before it delegates up to a superclass initializer", and
  safety check 4 states that "An initializer can't call any instance methods,
  read the values of any instance properties, or refer to `self` as a value until
  after the first phase of initialization is complete". *The Swift Programming
  Language*, Initialization, Two-Phase Initialization,
  https://docs.swift.org/swift-book/documentation/the-swift-programming-language/initialization/
  verified 2026-08-02. A Swift base class cannot call a hook from its own
  initialiser before the subclass is whole, because that call does not compile.

Second, hook ordering is a contract even though no signature expresses it. If a
base class calls `beforeSave()` and then `validate()`, and a later release swaps
them, every subclass that relied on validation having run keeps compiling and
starts misbehaving. Hook order belongs in the documented contract and in a test,
because the type system does not carry it.

Third, re-entrancy. A subclass hook that calls the template method again, for
example to process a nested record, re-enters the skeleton. Any state the
skeleton keeps in instance fields rather than in locals is now shared across the
two activations. Skeletons intended for recursive use must keep per-activation
state in parameters or locals.

## 8. Implementation variants

**Abstract steps only.** Every varying step is declared with no body. The
strongest form and the one to prefer inside a single codebase. The compiler
rejects an incomplete variant. The cost is that the base class becomes
unextendable without a breaking change, since a new abstract step invalidates
every existing subclass.

**Hooks only.** Every varying step has a default. The base class can be
instantiated and behaves as the default variant. This is the form to use for a
published library, because new hooks can be added in a minor version. The cost
is silent under-implementation, see dimension 11.

**Mixed, with a documented split.** The common production shape. Two or three
abstract steps carry the decisions no variant can avoid, and a longer tail of
hooks carries the optional interventions. Jakarta Servlet's `HttpServlet` is
this shape, see dimension 9, where every `doXxx` method has a default that
returns a protocol error and the subclass overrides only the verbs it serves.

**Sealed or final template method.** Marking the template method
non-overridable is what turns a convention into a guarantee. Without it a
subclass can override the template method itself and the entire sequencing
protection disappears. Java `final`, C# non-virtual or `sealed override`, Kotlin
methods being final by default, Swift `final`. Python and JavaScript cannot
express it and rely on convention plus review.

**Template method calling a factory method.** The step the subclass supplies is
not behaviour but a product. The skeleton owns sequencing, the subclass owns the
type. This is the pairing the GoF catalog describes and is the most common shape
in framework code. See the Factory Method entry.

**Hook returning a decision rather than performing an action.** Instead of
`void filterRow(Row r)`, the hook is `boolean shouldInclude(Row r)`. The
skeleton keeps all the acting and the subclass supplies only a predicate. This
form is much easier to test and much harder to misuse, because the hook cannot
mutate state the skeleton did not expect. Prefer it whenever the step can be
expressed as a question.

**Higher-order function instead of a subclass.** The skeleton takes the varying
steps as function parameters or constructor arguments. Same sequencing
guarantee, no hierarchy, and the variant is composable and testable in
isolation. This is idiomatic in Python, TypeScript, Kotlin, Swift, Rust and Go,
and it is the default choice in those languages unless a published, documented,
discoverable extension point is genuinely needed. The cost is discoverability.
A named protected method with documentation is easier for an external
implementor to find than a parameter of function type.

**Trait or protocol with default method bodies.** Java default methods on
interfaces, Rust trait provided methods, Swift protocol extensions, Kotlin
interface method bodies, Scala traits. The interface declares the required
operations and provides the skeleton as a default method written in terms of
them. This gives Template Method without occupying the single inheritance slot,
which removes the largest structural limitation of the classical form. Rust's
`Iterator` is the reference example, see dimension 9. The limitation is that
default methods cannot access private state, so the skeleton must be expressible
purely in terms of the declared operations.

**Go's shape.** Go has embedding but no virtual dispatch through it. A method on
an embedded struct calls the embedded struct's own method, not the outer type's
override. The correct Go form is a struct holding function fields, or an
interface parameter passed into a package-level skeleton function. Writing the
classical form in Go produces code that compiles and silently never dispatches
to the subtype, which is a genuinely dangerous near-miss.

**Two-level skeleton.** A framework skeleton calls an intermediate skeleton
which calls the leaf. Common in large frameworks and expensive to reason about,
because a hook can now be intercepted at two levels and the effective call order
is not visible from any single file. Limit to two levels and document the full
order in one place.

## 9. Known production uses

**Jakarta Servlet, `HttpServlet.service()`.** The protected `service` method
receives an HTTP request and dispatches to the `doGet`, `doPost`, `doPut`,
`doDelete`, `doHead`, `doOptions` and `doTrace` methods. The specification
documentation states that a subclass must override at least one of the `doXxx`
methods, and that there is almost no reason to override `service` itself, since
`service` handles standard HTTP requests by dispatching them to the handler for
each request type. That is the pattern's governance property stated in a
specification. The dispatch is the fixed skeleton, verb handling is the variable
step, and each `doXxx` has a default so a servlet implements only the verbs it
supports. Jakarta Servlet 6.0 API documentation,
`jakarta.servlet.http.HttpServlet`,
https://jakarta.ee/specifications/servlet/6.0/apidocs/jakarta.servlet/jakarta/servlet/http/httpservlet
verified 2026-08-02.

**Python `unittest.TestCase`.** `TestCase.run()` owns the fixture lifecycle. The
documentation states that `setUp()` is called immediately before the test
method, and that `tearDown()` is called immediately after the test method has
been called and the result recorded, that it is called even if the test method
raised an exception, and that it is called only if `setUp()` succeeded. Both
default implementations do nothing, which makes them hooks in the precise sense
of dimension 5. The test author writes only the test method and optionally the
two hooks, and cannot rearrange the lifecycle. Python 3 documentation,
`unittest`, https://docs.python.org/3/library/unittest.html verified 2026-08-02.

**Django class-based views, `View.dispatch()`.** The documentation states that
the default implementation inspects the HTTP method and attempts to delegate to
a method matching it, a GET to `get()`, a POST to `post()`, and so on, and that
by default a HEAD request is delegated to `get()` unless `head()` is overridden.
When the verb is not supported, `http_method_not_allowed()` runs, itself an
overridable hook whose default returns an HTTP 405 with the allowed verb list.
Django 5.2 documentation, "Base views",
https://docs.djangoproject.com/en/5.2/ref/class-based-views/base/ verified
2026-08-02.

**Spring Framework, `AbstractApplicationContext.refresh()`.** The class
documentation states plainly that it uses the Template Method design pattern,
requiring concrete subclasses to implement abstract methods. `refresh()` runs a
fixed startup sequence, preparing the context, obtaining a fresh bean factory,
configuring it, running bean factory post processors, registering bean post
processors, initialising the message source and the event multicaster, calling
the `onRefresh()` hook for context-specific work, registering listeners,
finishing singleton initialisation and publishing the refreshed event.
Subclasses supply `refreshBeanFactory()`, `closeBeanFactory()` and
`getBeanFactory()`. This is a long skeleton with a documented order and a
deliberately small set of primitive operations. Spring Framework Javadoc,
`org.springframework.context.support.AbstractApplicationContext`,
https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/context/support/AbstractApplicationContext.html
verified 2026-08-02.

**Java Collections Framework, `java.util.AbstractList`.** The documentation
states that to implement an unmodifiable list the programmer needs only to
extend the class and provide implementations of `get(int)` and `size()`, and
that a modifiable list additionally overrides `set(int, E)`, with `add(int, E)`
and `remove(int)` added for a variable-size list. Every other list operation,
including iteration, `indexOf`, `equals`, `hashCode` and the sublist views, is
implemented in the skeleton in terms of those primitives. This is the skeletal
implementation form of the pattern, and it shows the payoff clearly, since a
custom list gets dozens of correct operations from two methods. Java SE 21 API
documentation, `java.util.AbstractList`,
https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/AbstractList.html
verified 2026-08-02.

**Rust standard library, `Iterator`.** The trait declares one required method,
`next()`, and supplies a large set of provided methods including `map`,
`filter`, `fold`, `collect`, `count`, `nth`, `zip` and `chain`, all written in
terms of `next()`. An implementor writes one method and inherits the whole
combinator surface. This is Template Method expressed through trait default
methods rather than class inheritance, and it shows the variant that avoids the
single-inheritance limitation. Rust standard library documentation,
`std::iter::Iterator`, https://doc.rust-lang.org/std/iter/trait.Iterator.html
verified 2026-08-02.

**.NET, `Microsoft.Extensions.Hosting.BackgroundService`.** The abstract class
implements `IHostedService` and supplies `StartAsync` and `StopAsync`, which own
the lifecycle. The documentation describes `ExecuteAsync(CancellationToken)` as
the method called when the hosted service starts, whose implementation should
return a task representing the lifetime of the long running operation. The
service author writes one method, and start, stop, cancellation-token wiring and
disposal come from the skeleton. Microsoft .NET API documentation,
`Microsoft.Extensions.Hosting.BackgroundService`,
https://learn.microsoft.com/en-us/dotnet/api/microsoft.extensions.hosting.backgroundservice
verified 2026-08-02.

## 10. Consequences

Positive.

- Sequencing logic exists once. A correction to the fixed part reaches every
  variant on the next build, including variants in other repositories, without
  any of them being edited.
- Obligations in the skeleton cannot be skipped by a variant author. Commit,
  rollback, resource release, audit write, permission check. This converts a
  code review convention into a structural property.
- New variants arrive without editing existing code, which keeps the skeleton
  closed for modification while remaining open for extension.
- The set of extension points is explicit and closed. A reader of the base class
  can enumerate exactly what a variant is allowed to change, which is valuable
  for security review and for API governance.
- Variants are small. A well-shaped variant is one method, sometimes two, and
  contains only the decision that distinguishes it. Skeletal implementations
  such as `AbstractList` turn two methods into a full collection.
- The pattern is discoverable. Named protected methods with documentation are
  easier for an external implementor to find than a constructor parameter of
  function type, which matters for a library with many third-party extenders.

Negative.

- Inheritance coupling. The subclass depends on the base class's internal call
  sequence and protected surface, not on a published interface. This is the
  widest compatibility commitment a type can make, and it is the source of the
  fragile base class problem in dimension 11.
- The single inheritance slot is consumed. A variant cannot also extend
  something else, and a second axis of variation cannot be expressed without
  multiplying classes.
- Reading cost. No single file contains the behaviour. A reader interleaves two
  or more files mentally, and a debugger alternates frames between them.
- Skeleton rigidity. Once published, the hook set, their order and their
  signatures are frozen for the life of the major version. Removing a hook, or
  calling it at a different point, breaks downstream code that still compiles.
- The base class becomes a magnet. Because every variant inherits from it, the
  cheapest place to put any new shared behaviour is the base class, and it grows
  until it holds behaviour most variants do not want. The observable end state
  is a base class of a thousand lines with fifteen hooks, most of them used by
  one subclass each.
- Testing a variant in isolation is not possible without instantiating the
  skeleton, so a variant's unit test is always at least partly an integration
  test of the base class.

## 11. Failure modes and misuse

**The fragile base class break.** Symptom. A downstream team's build passes,
their tests pass, and their application behaves incorrectly after a framework
upgrade in which no signature changed. Or the reverse, a base class change that
was correct in isolation causes an infinite recursion in a subclass that
overrode two methods the base class now calls through each other. Cause. The
subclass depends on the base class's internal self-call structure, which is
implementation detail that the type system does not describe and the base author
did not consider part of the contract. Leonid Mikhajlov and Emil Sekerinski
formalised this in "A Study of the Fragile Base Class Problem", Proceedings of
the 12th European Conference on Object-Oriented Programming, ECOOP 1998,
https://link.springer.com/chapter/10.1007/BFb0054099 verified 2026-08-02, where
the problem is characterised as a system developer, unaware of extensions
written by users, producing a seemingly acceptable revision of a base class that
damages those extensions. Fix. Document every self-call the template method
makes and treat that documentation as part of the published contract. Bloch's
Item 19 direction is the same, that a class must document its self-use of
overridable methods. Better still, remove the self-call by extracting the
skeleton to call a collaborator object rather than its own overridable methods,
which is the composition-based form and is the reason the composition over
inheritance advice exists.

**Constructor calling an overridable step.** Symptom. A null reference, or an
unexpectedly empty collection, or a Kotlin `lateinit` property access exception,
inside an overridden hook, occurring for some subclasses and not others, and
never reproducible in the base class's own tests. Cause. The base constructor
invokes the template method or a hook while the subclass is only partly built, so
the override reads state that nothing has assigned yet. The exact ordering
differs by language and is set out in dimension 7. In Java and Kotlin the
subclass field initialisers have not run at all. In C# they have already run, but
the derived constructor body has not, so constructor-injected collaborators are
the ones found null. In Swift the compiler rejects the call outright. This is
Bloch's Item 19 prohibition, that constructors must not invoke overridable
methods directly or indirectly, and that violating it will produce program
failure. Fix. Move the call out of the constructor to a lazily evaluated
accessor or an explicit `start()` or `init()` step the client invokes. Where a
base class genuinely needs a value from the subclass during construction, take
it as a constructor parameter rather than a virtual call.

**The forgotten hook.** Symptom. One tenant, one file format, or one endpoint
behaves as the default while every other variant behaves correctly, discovered
weeks later from a support ticket rather than from a build. Cause. A hook with a
default that a variant was supposed to override and did not, or overrode with a
misspelled name in a language without checked overrides. Fix. Make the step
abstract if every variant must choose. Where it must stay a hook for
compatibility, add a per-variant test asserting the observable effect, and use
the language's checked override marker.

**Override that forgets to call super.** Symptom. Behaviour added to the base
class hook in a recent release does not happen for some subclasses. Metrics
missing for a subset of variants. A resource not released on one code path.
Cause. A hook whose default body does real work, overridden without a `super`
call. This is a convention no compiler checks. Fix. Restructure so the base
class does its work outside the overridable method and calls the hook from
there, which is often expressed as a `final` method that does the base work and
then calls a protected empty hook. Then no `super` call is ever required.

**The template method that got overridden.** Symptom. A security check or a
transaction boundary in the skeleton did not run for one subclass, and the
skeleton's own tests pass because they test the base class. Cause. The template
method was not marked non-overridable, and a subclass replaced it wholesale,
usually because a hook was missing and overriding the whole method was the only
way to get the behaviour needed. Fix. Mark it `final` or its language
equivalent, then add the hook the subclass author actually wanted. The override
is a sign that the extension surface was too narrow.

**Hook explosion.** Symptom. A base class with fifteen or more protected
overridable methods, most overridden by exactly one subclass, and no reader can
state the effective call order without tracing the source. Cause. Each new
variant needed a slightly different intervention point and a hook was added
rather than the design being reconsidered. Fix. Group related hooks into a
collaborator object passed into the skeleton, which converts fifteen inheritance
hooks into one interface with fifteen methods that can be implemented, composed
and tested independently. This is Replace Inheritance with Delegation, see
dimension 14.

**Skeleton with one implementation.** Symptom. An abstract class and exactly one
concrete subclass, in the same package, changed together in every commit for two
years. Cause. The pattern applied in anticipation of a second variant that never
arrived. Fix. Inline the subclass into the base class and delete the hierarchy.

**Silent contract drift on hook ordering.** Symptom. After a framework upgrade a
subclass's validation hook sees data that has already been persisted, though no
method signature changed. Cause. The skeleton reordered two hook calls, which is
invisible to every compatibility check that exists. Fix. Pin the order with a
test in the framework's own suite that records the call sequence from a probe
subclass and asserts it, so a reorder becomes a failing test rather than a
downstream defect.

**Re-entrancy corruption.** Symptom. Nested processing produces interleaved or
lost results, and only under a specific input shape such as a record containing
a child record of the same type. Cause. The skeleton stores per-run state in
instance fields and a hook re-enters the template method. Fix. Move per-run
state to locals or to an explicitly passed context object.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Template Method | Strategy | Bridge | Decorator | Higher-order function parameter | Chain of Responsibility |
|---|---|---|---|---|---|---|
| Binding time of the variation | Class definition, fixed at construction | Runtime, swappable per call | Runtime, per abstraction instance | Runtime, per wrapped instance | Runtime, at wiring or per call | Runtime, chain assembled at wiring |
| Number of objects involved | One. The variant is the object | Two. Context plus strategy | Two hierarchies, abstraction and implementor | N wrappers plus one core | One object plus function values | N handlers plus the request |
| Who controls sequencing | The base class, absolutely | The context, which may delegate freely | The abstraction | Each wrapper controls its own before and after | The skeleton function | Each handler decides whether to continue |
| Independent axes of variation | One. Single inheritance limits it | Several, one strategy field per axis | Two by design. That is its purpose | Several, composed by stacking | Several, one parameter per axis | One, along the chain |
| Coupling strength | Highest. Inheritance plus internal call order | Low. An interface | Low. Two interfaces | Low. One interface | Lowest. A function signature | Low. One handler interface |
| Guarantee that fixed steps run | Strong if the template method is final | Weak. Context may be replaced or bypassed | Medium | Weak. A wrapper may not call inner | Strong. The skeleton function owns the flow | Weak. A handler may stop the chain |
| Adding a variant | New subclass, no edits | New strategy class, no edits | New implementor, no edits | New decorator, no edits | New function, no edits | New handler, plus wiring |
| Cognitive load for a reader | High. Behaviour split across files by inheritance | Medium. Two objects, both readable | High. Two hierarchies to hold | High for deep stacks | Low. The wiring names everything | High. Order is implicit in assembly |
| Testability of the varying part in isolation | Poor. Needs the skeleton instantiated | Good. A strategy is a plain object | Good | Good | Good. A function is directly callable | Good |
| Suitability for a published library extension point | Strong. Named, documented, discoverable | Strong. A published interface | Strong | Medium | Weak. Parameters are less discoverable | Medium |
| Cost of evolving the fixed part | Low for additive hooks, very high for reordering or new abstract steps | Low. The interface is the only commitment | Low | Low | Low | Medium |

Reading of the table. Template Method wins when the sequencing must be
guaranteed and the variation is one axis known at type definition. Strategy wins
the moment the variation must change at runtime or a second axis appears, and it
is the single most common correct replacement. Bridge wins with two axes that
both vary. Decorator wins when behaviour must wrap an existing instance rather
than complete a skeleton. A higher-order function parameter wins in any language
where functions are values and no published, discoverable extension point is
required, which covers most application code written today.

The Template Method versus Strategy comparison is worth stating directly,
because the two are confused constantly and the confusion produces the failure
in dimension 4's first non-applicability entry.

- **Binding time.** Template Method binds the variation at compile time through
  the type of the object. Choosing a different variant means constructing a
  different class. Strategy binds at runtime through a field. Choosing a
  different variant means assigning a different object, and it can be done per
  call, per tenant, per request.
- **Object count.** Template Method uses one object that is both the algorithm
  and the variation, which is why it is cheaper in allocation and in indirection.
  Strategy uses two, the context that holds the fixed algorithm and the strategy
  that holds the varying part, which is why it is more flexible and more
  testable.
- **Hierarchy count.** Template Method occupies one inheritance hierarchy and
  consumes the single inheritance slot. Strategy uses composition and consumes
  nothing, which is why several strategies can coexist in one context and
  several axes of variation are expressible.
- **What the varying code can see.** A Template Method hook is inside the type
  and can read protected state, which is convenient and is exactly what makes it
  fragile. A Strategy is outside and sees only what the context passes it, which
  is inconvenient and is exactly what makes it stable.
- **Direction of the general advice.** The GoF book's own second design
  principle, "Favor object composition over class inheritance", stated in
  chapter 1, section 1.6 "Inheritance versus Composition" at page 20 of the 1994
  Addison-Wesley edition, argues for the Strategy shape as the default. The
  reasoning given there is that inheritance is white-box reuse, because the
  subclass sees the parent's implementation, while composition is black-box
  reuse through well-defined interfaces only. The page location and the
  white-box against black-box framing are corroborated in
  [the Python Patterns Guide treatment of the principle](https://python-patterns.guide/gang-of-four/composition-over-inheritance/),
  verified 2026-08-02. Template Method is therefore the pattern that most
  directly trades against the book's own general advice, and it earns that trade
  only when the sequencing guarantee or the discoverable published extension
  point is worth the coupling.

## 13. Related and incompatible patterns

- **Factory Method.** The most common companion. A primitive operation whose job
  is to produce an object rather than to perform an action is a factory method,
  and the GoF catalog notes that factory methods are usually called from within
  template methods. The pairing lets a framework own sequencing while an
  application owns types. See the Factory Method entry.
- **Strategy.** The principal alternative and the usual replacement. Same
  problem of varying part of an algorithm, opposite mechanism. Move to Strategy
  when the variation must be selected at runtime, when a second axis appears, or
  when the variant needs its own tests. See dimension 12 for the direct
  comparison.
- **Bridge.** The pattern to reach for when the skeleton itself varies as well
  as the steps. Bridge separates an abstraction hierarchy from an implementor
  hierarchy so both vary independently. A Template Method base class that is
  starting to grow subclasses along two unrelated axes is usually asking to
  become a Bridge.
- **Decorator.** Composes rather than competes, and solves the adjacent problem
  of adding behaviour around an existing object at runtime. Where Template
  Method fixes the extension points at class definition, Decorator lets callers
  stack behaviour per instance. A skeleton with a hook that everybody overrides
  to add logging is asking for a decorator instead.
- **Chain of Responsibility.** An alternative when the fixed part is a pipeline
  rather than a sequence with holes. Where Template Method has one variant per
  algorithm, a chain has many independent handlers that each decide whether to
  act and whether to continue. Servlet filters are the chain form of the same
  concern that `HttpServlet.service()` handles with Template Method.
- **Builder.** Orthogonal and composes cleanly. Template Method sequences an
  algorithm, Builder sequences the assembly of one object. A template method
  whose steps are all "add a part" is a builder and should be modelled as one.
- **Composite.** Frequently combined. A composite's traversal is a template
  method whose primitive operation is "handle this node", and leaves and
  branches supply different implementations.
- **Dependency injection.** Largely replaces the pattern in application code.
  Injecting a collaborator that the skeleton calls gives the same inversion of
  control with composition rather than inheritance, and the wiring is visible in
  one configuration site rather than distributed across a hierarchy. Template
  Method keeps its place in library code that must run without a container, and
  in APIs where a discoverable, documented, closed extension surface is a
  deliberate goal.
- **Singleton.** Conflicts in practice. A skeleton that reaches a process-wide
  singleton from inside a hook removes the substitutability the pattern exists
  to provide and makes variant tests order-dependent.
- **Service Locator.** Actively conflicts, for the same reason it conflicts with
  Factory Method. A hook that pulls a dependency from a global registry hides
  what the variant needs, which reverses the explicitness a closed extension
  surface was meant to buy. See the anti-patterns family entry.
- **Null Object.** A neat companion for hooks. A hook whose default does nothing
  is the Null Object idea applied to a method rather than to a type, and where a
  hook returns a collaborator, returning a null object rather than a null
  reference removes a branch from the skeleton.

## 14. Refactoring path in and out

Introducing the pattern into duplicated code. The named refactoring is Form
Template Method, and the steps are ordered so that each one is independently
verifiable. Cross reference the refactoring family entry.

1. Place the duplicated procedures side by side and mark every region that
   differs. If the differing regions are not the same count and not in the same
   relative order, stop. The procedures are not variants of one algorithm and
   this refactoring will produce a false abstraction.
2. In each procedure independently, extract every differing region into a method
   with the same name and the same signature across all copies. Do this one
   region at a time and run the tests after each extraction. At this point
   nothing is shared and the classes are still independent, which is the safest
   possible intermediate state.
3. Confirm that the two procedures are now textually identical. If they are not,
   the remaining difference is either an ordering difference, which invalidates
   the refactoring, or a value difference, which should become a parameter or a
   constant supplied by an extracted method.
4. Pull the now-identical procedure up into a common superclass. This is Pull Up
   Method. Only the extracted step methods remain in the subclasses. Run the
   tests.
5. In the superclass, declare the step methods. Make a step abstract when every
   variant must decide, and give it a body when a correct default exists, per
   the decision rule in dimension 5.
6. Mark the template method non-overridable. This is the step most often skipped
   and it is the one that converts the design into a guarantee.
7. Add the call-order test from dimension 15 so a future reorder of the skeleton
   fails a build rather than a customer.

Removing the pattern when it stops earning its place. The indicators are a
hierarchy whose subclasses override nothing but one hook, a request to choose
the variant from configuration at runtime, or a second axis of variation
arriving.

1. Confirm the subclasses carry no state and no behaviour beyond the overridden
   steps. Where they do, only the step part should move and the rest stays.
2. Define an interface holding the varying steps, with the same signatures the
   protected methods had.
3. Add a constructor parameter to the base class holding that interface, and
   default it to an implementation carrying the current default behaviour.
4. For each subclass, create an implementation of the interface containing the
   body of its overrides. Change every construction site of that subclass to
   construct the base class with the new implementation. Run the tests after
   each site rather than at the end.
5. Change the template method to call through the collaborator field instead of
   through its own overridable methods. The self-call is now gone, which removes
   the fragile base class exposure described in dimension 11.
6. Delete the now-empty subclasses and remove `abstract` from the base class.
   This sequence is Replace Inheritance with Delegation followed by Inline Class,
   see the refactoring family entries for both.
7. If a second axis of variation was the motivation, split the interface in two
   and hold two collaborator fields, which is the move from Template Method to a
   Bridge or to two composed strategies.

A smaller intermediate move worth knowing. When only one hook is problematic,
leave the hierarchy in place and convert that single step to a collaborator
field with a default. This is cheap, reversible, and removes the specific
coupling that hurt without a wholesale rewrite.

## 15. Testing and verification

This dimension is practice rather than sourced fact.

Easier because of the pattern.

- The fixed sequence has one test rather than one per variant. A probe subclass
  that records each step into a list and asserts the recorded order verifies the
  skeleton once for every variant that will ever exist.
- Failure-path guarantees are directly assertable. A probe subclass whose
  primitive operation throws, plus an assertion that the release or rollback
  step still ran, tests the property that most justifies the pattern. This test
  is hard to write when the same envelope is duplicated across variants.
- Each variant's test surface is small, because a well-shaped variant is one or
  two methods.

Harder because of the pattern.

- A variant cannot be exercised without the skeleton. Every variant test is at
  least partly an integration test, and a skeleton that touches a database
  drags that dependency into every variant test unless the skeleton is itself
  parameterised.
- Protected methods are not directly callable from a test in the same way public
  ones are, so tests either live in the same package, use reflection, or go
  through the template method and infer the step's behaviour from an
  observable effect. The third option is the correct one and the least
  convenient.
- Verifying that a hook was called, and called at the right point, needs a probe
  rather than a plain assertion, because the call is internal to the skeleton.

Techniques that apply.

- **Probe subclass over a mocking framework.** Write a small test-only subclass
  that records calls into a list. Prefer it to a partial mock. A partial mock
  that stubs a method on the class under test suppresses the real base class
  behaviour and will hide the constructor-ordering defect from dimension 11,
  because the mock has no real construction sequence.
- **Call-order test.** One test in the skeleton's own suite that instantiates a
  probe subclass, runs the template method, and asserts the exact recorded
  sequence of step names. This is the only mechanism that turns hook ordering,
  which no type system expresses, into a checked contract.
- **Abstract test case, sometimes called a contract test.** Write one test class
  against the skeleton's public behaviour with an abstract creation hook, then
  subclass it once per concrete variant. Every variant runs the same suite.
  This is Template Method applied to the test code, and it is how a framework
  publishes a conformance suite for third-party extenders.
- **Exception-path probe.** A probe subclass whose step throws a sentinel
  exception, asserting both that the exception propagated and that the cleanup
  steps ran. Repeat once per step that can fail, since cleanup coverage often
  differs by failure point.
- **Default-override assertion per variant.** For every hook with a default,
  one test per variant asserting the observable behaviour the variant is
  supposed to have. This is what catches the forgotten hook from dimension 11
  before a customer does.
- **Mutation testing on the skeleton.** The skeleton is high-fan-in code, so a
  mutation run there has unusually good return. A surviving mutant in the fixed
  sequence means the call-order test is missing a step.

## 16. Observability signals

This dimension is practice rather than sourced fact.

The pattern hides which variant ran behind a base class stack frame, so the
variant identity has to reach telemetry or nobody can attribute a failure.

What to record.

- On entry to the template method, a span whose attributes carry the concrete
  variant class name and the correlation identifier of the work in progress. The
  span is created in the skeleton, so it exists for every variant automatically,
  which is one of the pattern's operational payoffs.
- A child span or a timed event per skeleton step, labelled with the step name.
  This turns the fixed sequence into a visible waterfall and makes a slow hook
  immediately attributable to the variant rather than to the framework.
- A counter of template method invocations, labelled by concrete variant. The
  label distribution answers which variants are actually in use, which is the
  input to deciding whether a variant can be retired.
- A counter of hook overrides taken, emitted from the base class default rather
  than from the override. A default hook that increments a "default taken"
  counter makes the forgotten-override failure visible on a dashboard rather
  than in a support ticket.
- A counter of failures labelled by variant and by the step that threw. Deriving
  the step from the exception's stack frame is unreliable. Record it explicitly
  in the skeleton's catch block, where the step is known.
- For skeletons that own a resource, a gauge of currently held resources and a
  counter of acquisitions and releases. The two counters should track.

A healthy instance on a dashboard. The per-variant invocation counter shows the
mix expected for the configuration in play, and it moves only when a deployment
or a configuration change explains it. Step durations are stable and the
skeleton's own steps are a small fraction of the total. The default-taken
counter is zero for hooks that every variant is supposed to override, and steady
for hooks that are genuinely optional. Acquisition and release counters track
each other within one in-flight operation.

A failing instance. The default-taken counter becomes non-zero for a hook that
every variant should override, which is the forgotten override, usually
appearing right after a new variant is deployed. Or the acquisition counter
outruns the release counter, which means a failure path is bypassing cleanup and
the skeleton's finally block does not cover the step that threw. Or one variant's
step duration develops a long tail while the skeleton steps stay flat, which
localises a slow hook without reading any code. Or the failure counter shows
errors attributed to the skeleton's step name rather than a variant's, which
usually means the skeleton is catching a variant's exception too broadly and
relabelling it.

## 17. Security and privacy implications

This dimension is analytical rather than sourced.

The pattern's security profile is unusual because it cuts both ways sharply,
and both directions matter.

**It closes a surface, deliberately.** A template method with a `final` marker
and a small set of declared hooks is a closed extension surface. A variant author
can change only what the skeleton declared changeable. When the skeleton contains
an authentication check, an authorisation check, an audit write or a rate limit,
that check runs for every variant including ones written by a team that never
read the design. This is a genuine security property and it is the strongest
argument for choosing this pattern over a set of independent handlers. The
`HttpServlet.service()` shape gets this property for HTTP verb dispatch, since a
servlet cannot serve a verb without going through the dispatcher.

**It opens a surface when the guarantee is not enforced.** The property above is
worth nothing if the template method is overridable. A subclass that overrides
the template method itself bypasses every check in it, and the bypass is
invisible to a reviewer reading the base class. The security-relevant rule is
therefore mechanical, not advisory. Mark the template method non-overridable,
and in languages that cannot express it, Python and JavaScript, add a test that
asserts no subclass in the codebase defines a method with the template method's
name.

**Untrusted implementors run inside the skeleton's frame.** When variants are
plugins loaded from disk or from a package registry, a hook is arbitrary code
executing inside the framework's call stack with the framework's privileges,
between the framework's resource acquisition and its release. A hostile or
merely defective hook can hold a lock indefinitely, exhaust a connection pool by
never returning, or throw an error type the skeleton's cleanup does not catch.
Wrap hook invocations with a timeout where the runtime permits it, catch the
broadest error type the language offers around each hook so cleanup always runs,
and treat any value a hook returns as untrusted input rather than assuming the
declared return type implies well-formed content.

**Protected state is a wider surface than a parameter list.** A hook can read
and write the skeleton's protected fields. When those fields hold a
credential, a decrypted buffer, a session token or a tenant identifier, every
variant author has access to them for the lifetime of the object, whether or not
their step needs them. The composition alternative narrows this to exactly what
the skeleton chooses to pass. Where the skeleton handles secrets, prefer passing
a minimal context object to the hook over exposing protected fields, so the
variant's access is scoped to what it was given.

**Exception messages crossing the boundary.** A skeleton that catches a variant's
exception and includes its message in a response or a log is republishing text
written by code it does not control. A hook that formats a database error into
its exception message can leak a connection string or a query containing
personal data into a place the skeleton's authors believed was safe. Log the
exception type and a skeleton-owned message at the boundary, and route the
variant's own message to a channel with the same handling rules as any other
untrusted content.

On privacy the pattern is neutral in itself, with the same caveat as any pattern
whose observability advice includes a type name. Dimension 16 recommends
labelling telemetry with the concrete variant class. Variant class names commonly
encode a tenant, a customer, a region or a data-residency tier, because that is
frequently the axis the variants vary along. Where the name carries that, the
telemetry label is attributable data and inherits the retention and access rules
of any other identifier.

## 18. References

1. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides. *Design Patterns.
   Elements of Reusable Object-Oriented Software*. Addison-Wesley, 1994.
   ISBN 0-201-63361-2. Chapter 5, Behavioral Patterns, section Template Method,
   for the intent, the participants, the hook and primitive operation
   distinction, and the Hollywood Principle framing of the inverted control
   structure. Chapter 1, section 1.6 "Inheritance versus Composition", page 20,
   for the "Favor object composition over class inheritance" principle and the
   white-box against black-box reuse distinction used in dimension 12.
2. Joshua Bloch. *Effective Java*, 3rd edition. Addison-Wesley, 2018.
   ISBN 978-0-13-468599-1. Item 19, "Design and document for inheritance or else
   prohibit it". Source of the prohibition on constructors invoking overridable
   methods, of the requirement to document self-use of overridable methods, and
   of the advice to prohibit subclassing where inheritance was not designed for.
3. Leonid Mikhajlov, Emil Sekerinski. "A Study of the Fragile Base Class
   Problem". Proceedings of the 12th European Conference on Object-Oriented
   Programming, ECOOP 1998. Lecture Notes in Computer Science volume 1445,
   pages 355 to 382. DOI 10.1007/BFb0054099.
   https://link.springer.com/chapter/10.1007/BFb0054099
   Verified 2026-08-02. SpringerLink bounces this link through an identity
   provider before serving the record, so the DOI above is the stable
   identifier to resolve if the direct link does not open. Source of the fragile
   base class characterisation in dimension 11.
4. Eclipse Foundation. *Jakarta Servlet 6.0 API documentation*,
   `jakarta.servlet.http.HttpServlet`.
   https://jakarta.ee/specifications/servlet/6.0/apidocs/jakarta.servlet/jakarta/servlet/http/httpservlet
   Verified 2026-08-02. Source for the `service()` dispatch production use and
   for the guidance that subclasses override `doXxx` rather than `service`.
5. Python Software Foundation. *Python 3 documentation*, `unittest`.
   https://docs.python.org/3/library/unittest.html
   Verified 2026-08-02. Source for the `TestCase.run()` fixture lifecycle and
   the documented `setUp` and `tearDown` ordering and failure semantics.
6. Django Software Foundation. *Django 5.2 documentation*, "Base views".
   https://docs.djangoproject.com/en/5.2/ref/class-based-views/base/
   Verified 2026-08-02. Source for `View.dispatch()` verb delegation and the
   `http_method_not_allowed()` hook.
7. VMware Tanzu. *Spring Framework API documentation*,
   `org.springframework.context.support.AbstractApplicationContext`.
   https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/context/support/AbstractApplicationContext.html
   Verified 2026-08-02. Source for the `refresh()` skeleton, the explicit
   Template Method attribution in the class documentation, and the abstract
   methods concrete subclasses supply.
8. Oracle. *Java SE 21 API Specification*, `java.util.AbstractList`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/AbstractList.html
   Verified 2026-08-02. Source for the skeletal implementation production use
   and the exact set of primitive operations a subclass supplies.
9. Rust project. *Rust standard library documentation*, `std::iter::Iterator`.
   https://doc.rust-lang.org/std/iter/trait.Iterator.html
   Verified 2026-08-02. Source for the required-method against provided-method
   split used as the trait-based variant in dimension 8 and the production use
   in dimension 9.
10. Microsoft. *.NET API documentation*,
    `Microsoft.Extensions.Hosting.BackgroundService`.
    https://learn.microsoft.com/en-us/dotnet/api/microsoft.extensions.hosting.backgroundservice
    Verified 2026-08-02. Source for the hosted-service lifecycle production use
    and the description of `ExecuteAsync`.
11. Wikipedia contributors. "Template method pattern".
    https://en.wikipedia.org/wiki/Template_method_pattern
    Verified 2026-08-02. Used to confirm the GoF category placement, the intent
    wording, and the description of hook methods as helper methods with empty
    bodies that give a place to hang variant implementations.
12. SourceMaking. "Template Method Design Pattern".
    https://sourcemaking.com/design_patterns/template_method
    Verified 2026-08-02. Used to confirm the labelling of the inverted control
    structure as the Hollywood Principle in the context of this pattern, and the
    framework framing of invariant parts plus customisation placeholders.
13. Brandon Rhodes. "The Composition Over Inheritance Principle", Python Patterns
    Guide. https://python-patterns.guide/gang-of-four/composition-over-inheritance/
    Verified 2026-08-02. Used to corroborate the page 20 location of the GoF
    composition principle and the white-box against black-box reuse framing.
14. Apple. *The Swift Programming Language*, Initialization, section "Two-Phase
    Initialization".
    https://docs.swift.org/swift-book/documentation/the-swift-programming-language/initialization/
    Verified 2026-08-02 against the book's source at
    https://github.com/swiftlang/swift-book/blob/main/TSPL.docc/LanguageGuide/Initialization.md
    Source of safety checks 1 and 4 quoted in dimension 7, which are the reason
    the constructor hazard cannot occur in Swift.
15. Microsoft. "Execution order between base and derived inline instance field
    initializers", Microsoft Learn archived engineering blog, 2007.
    https://learn.microsoft.com/en-us/archive/blogs/marcod/execution-order-between-base-and-derived-inline-instance-field-initializers
    Verified 2026-08-02. Source for the C# ordering in dimension 7, that a
    derived class's inline field initialisers run before the base constructor,
    which is the reverse of Java. Specified in ECMA-334, the C# language
    specification, in the instance constructors section.
16. David Sauvage. *Effective Java 3rd edition summary*.
    https://github.com/david-sauvage/effective-java-summary/blob/master/README.md
    Verified 2026-08-02. Used in dimension 7 as a publicly readable restatement
    of Item 19's prohibition on calling overridable methods from a constructor.

## Code examples

Four languages, chosen because each shows a different structural answer to the
same problem. Java shows the classical inheritance form with a `final` template
method and the abstract-step against hook split. Python shows the same shape and
the dynamic-language caveat that the guarantee is convention only. TypeScript
shows the higher-order function form that usually replaces the classical one.
Rust shows the trait-with-default-methods form, which is the variant that avoids
consuming an inheritance slot. Go is discussed in dimension 8 and omitted here,
because its embedding does not dispatch virtually and the honest Go form is the
function-field shape already shown in TypeScript.

All four samples implement the same skeleton. Load rows from a source, validate
each one, transform the valid ones, and report a count, with the failure-path
guarantee that the source is always closed.

### Java

```java
import java.util.ArrayList;
import java.util.List;

abstract class ImportJob {
    // Sequencing is fixed here. final stops a subclass replacing it.
    public final int run() {
        open();
        try {
            List<String> kept = new ArrayList<>();
            for (String raw : readRows()) {
                if (!isValid(raw)) {
                    onRejected(raw);
                    continue;
                }
                kept.add(transform(raw));
            }
            return kept.size();
        } finally {
            close();
        }
    }

    protected abstract List<String> readRows();

    protected abstract String transform(String raw);

    // Hooks. Defaults are correct for a variant that does not care.
    protected boolean isValid(String raw) {
        return !raw.isBlank();
    }

    protected void onRejected(String raw) {
    }

    private void open() {
        System.out.println("open " + getClass().getSimpleName());
    }

    private void close() {
        System.out.println("close " + getClass().getSimpleName());
    }
}

final class CsvImportJob extends ImportJob {
    private final String body;

    CsvImportJob(String body) {
        this.body = body;
    }

    @Override
    protected List<String> readRows() {
        return List.of(body.split(","));
    }

    @Override
    protected String transform(String raw) {
        return raw.trim().toUpperCase();
    }
}

final class StrictImportJob extends ImportJob {
    private final List<String> rows;
    private int rejected = 0;

    StrictImportJob(List<String> rows) {
        this.rows = rows;
    }

    @Override
    protected List<String> readRows() {
        return rows;
    }

    @Override
    protected String transform(String raw) {
        return raw.trim();
    }

    @Override
    protected boolean isValid(String raw) {
        return raw.length() > 2;
    }

    @Override
    protected void onRejected(String raw) {
        rejected++;
    }

    int rejectedCount() {
        return rejected;
    }
}

public final class Demo {
    public static void main(String[] args) {
        System.out.println(new CsvImportJob("a, bb , ccc").run());
        StrictImportJob strict = new StrictImportJob(List.of("ab", "abcd", " "));
        System.out.println(strict.run() + " kept, " + strict.rejectedCount() + " rejected");
    }
}
```

A probe subclass, which is the call-order test from dimension 15.

```java
final class ProbeImportJob extends ImportJob {
    final List<String> calls = new ArrayList<>();

    @Override
    protected List<String> readRows() {
        calls.add("readRows");
        return List.of("x");
    }

    @Override
    protected String transform(String raw) {
        calls.add("transform");
        throw new IllegalStateException("boom");
    }
}
```

Running `run()` on the probe must throw and must still print the close line,
which is the failure-path guarantee asserted directly.

### Python

```python
from abc import ABC, abstractmethod


class ImportJob(ABC):
    def run(self) -> int:
        self._open()
        try:
            kept = []
            for raw in self.read_rows():
                if not self.is_valid(raw):
                    self.on_rejected(raw)
                    continue
                kept.append(self.transform(raw))
            return len(kept)
        finally:
            self._close()

    @abstractmethod
    def read_rows(self) -> list[str]: ...

    @abstractmethod
    def transform(self, raw: str) -> str: ...

    def is_valid(self, raw: str) -> bool:
        return bool(raw.strip())

    def on_rejected(self, raw: str) -> None:
        pass

    def _open(self) -> None:
        print(f"open {type(self).__name__}")

    def _close(self) -> None:
        print(f"close {type(self).__name__}")


class CsvImportJob(ImportJob):
    def __init__(self, body: str) -> None:
        self.body = body

    def read_rows(self) -> list[str]:
        return self.body.split(",")

    def transform(self, raw: str) -> str:
        return raw.strip().upper()


class StrictImportJob(ImportJob):
    def __init__(self, rows: list[str]) -> None:
        self.rows = rows
        self.rejected = 0

    def read_rows(self) -> list[str]:
        return self.rows

    def transform(self, raw: str) -> str:
        return raw.strip()

    def is_valid(self, raw: str) -> bool:
        return len(raw) > 2

    def on_rejected(self, raw: str) -> None:
        self.rejected += 1


if __name__ == "__main__":
    print(CsvImportJob("a, bb , ccc").run())
    strict = StrictImportJob(["ab", "abcd", " "])
    print(strict.run(), "kept,", strict.rejected, "rejected")
```

Python cannot mark `run` non-overridable. `abstractmethod` gives the abstract
step guarantee, since instantiating a subclass that omits one raises
`TypeError`, but the sequencing guarantee is convention plus review. Where the
skeleton carries a security obligation, add the test named in dimension 17 that
asserts no subclass defines `run`.

```python
def test_no_subclass_overrides_run() -> None:
    for cls in ImportJob.__subclasses__():
        assert "run" not in vars(cls), f"{cls.__name__} overrode the template method"
```

### TypeScript

The classical form first, for comparison.

```typescript
abstract class ImportJob {
  run(): number {
    this.open();
    try {
      const kept: string[] = [];
      for (const raw of this.readRows()) {
        if (!this.isValid(raw)) {
          this.onRejected(raw);
          continue;
        }
        kept.push(this.transform(raw));
      }
      return kept.length;
    } finally {
      this.close();
    }
  }

  protected abstract readRows(): string[];
  protected abstract transform(raw: string): string;

  protected isValid(raw: string): boolean {
    return raw.trim().length > 0;
  }

  protected onRejected(_raw: string): void {}

  private open(): void {
    console.log(`open ${this.constructor.name}`);
  }

  private close(): void {
    console.log(`close ${this.constructor.name}`);
  }
}

class CsvImportJob extends ImportJob {
  constructor(private readonly body: string) {
    super();
  }

  protected readRows(): string[] {
    return this.body.split(",");
  }

  protected transform(raw: string): string {
    return raw.trim().toUpperCase();
  }
}

console.log(new CsvImportJob("a, bb , ccc").run());
```

The higher-order form, which keeps the sequencing guarantee and deletes the
hierarchy. This is the shape to prefer in TypeScript unless a published,
discoverable extension point is wanted.

```typescript
interface ImportSteps {
  readRows(): string[];
  transform(raw: string): string;
  isValid?(raw: string): boolean;
  onRejected?(raw: string): void;
}

function runImport(name: string, steps: ImportSteps): number {
  console.log(`open ${name}`);
  try {
    const valid = steps.isValid ?? ((r: string) => r.trim().length > 0);
    const kept: string[] = [];
    for (const raw of steps.readRows()) {
      if (!valid(raw)) {
        steps.onRejected?.(raw);
        continue;
      }
      kept.push(steps.transform(raw));
    }
    return kept.length;
  } finally {
    console.log(`close ${name}`);
  }
}

let rejected = 0;
console.log(
  runImport("strict", {
    readRows: () => ["ab", "abcd", " "],
    transform: (r) => r.trim(),
    isValid: (r) => r.length > 2,
    onRejected: () => {
      rejected += 1;
    },
  }),
);
```

The optional members carry the hook semantics, the required members carry the
abstract-step semantics, and `runImport` cannot be overridden because there is
nothing to override.

### Rust

Rust has no inheritance, so the classical shape does not translate. The
equivalent is a trait with required methods and a provided method holding the
skeleton, which is the shape of `Iterator` in the standard library.

```rust
trait ImportJob {
    fn name(&self) -> &str;
    fn read_rows(&self) -> Vec<String>;
    fn transform(&self, raw: &str) -> String;

    fn is_valid(&self, raw: &str) -> bool {
        !raw.trim().is_empty()
    }

    fn on_rejected(&self, _raw: &str) {}

    // The skeleton. Implementors get it for free and do not rewrite it.
    fn run(&self) -> usize {
        println!("open {}", self.name());
        let mut kept = 0usize;
        for raw in self.read_rows() {
            if !self.is_valid(&raw) {
                self.on_rejected(&raw);
                continue;
            }
            let _ = self.transform(&raw);
            kept += 1;
        }
        println!("close {}", self.name());
        kept
    }
}

struct CsvImportJob {
    body: String,
}

impl ImportJob for CsvImportJob {
    fn name(&self) -> &str {
        "csv"
    }

    fn read_rows(&self) -> Vec<String> {
        self.body.split(',').map(|s| s.to_string()).collect()
    }

    fn transform(&self, raw: &str) -> String {
        raw.trim().to_uppercase()
    }
}

fn main() {
    let job = CsvImportJob {
        body: "a, bb , ccc".to_string(),
    };
    println!("{}", job.run());
}
```

Two differences from the classical form matter. A provided method cannot touch
private state, so everything the skeleton needs has to come through a declared
method, which is `name()` here. And a trait does not consume an inheritance
slot, so one type can carry several skeletons from several traits, which removes
the single-axis limitation from dimension 3. The Rust form cannot express the
`final` guarantee, because an implementor may override a provided method.

Compilation status is stated plainly rather than implied. The Python sample was
run with `python3` and prints the expected output. The Rust sample was compiled
with `rustc` and run. Both TypeScript samples type-check clean under
`tsc --strict --target ES2020 --noEmit` on TypeScript 5. The Java sample was NOT
compiled. The authoring machine carries the `javac` shim without an installed
JDK runtime, so the Java code is hand-checked against the language rules only.
The Go sample is deliberately absent for the reason given above. The TypeScript
higher-order sample uses optional chaining and nullish coalescing, so it needs
TypeScript 3.7 or later.
