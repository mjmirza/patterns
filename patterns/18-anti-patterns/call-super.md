---
name: Call Super
slug: call-super
family: 18-anti-patterns
category: Anti-Pattern
aliases: [Base Class Call Requirement, Forgot to Call Super, Refused Bequest of Behaviour, Overriding Hazard]
first_described: "Framework practitioner folklore, mid-1990s; catalogued as a hook-method antidote in Gamma, Helm, Johnson, Vlissides 1994 (Template Method)"
maturity: canonical
related: [template-method, factory-method, decorator, strategy, liskov-substitution-principle]
incompatible_with: [template-method]
verified: 2026-08-02
---

# Call Super

## 1. Name, aliases, and lineage

The name Call Super is not a term the Gang of Four ever wrote down. It is
practitioner shorthand that grew up around the same time as object frameworks
themselves, in the C++ and Smalltalk worlds of the late 1980s and early 1990s,
for a specific hazard that inheritance-based frameworks kept reproducing. A
subclass overrides a method for one reason, forgets that the base class method
being overridden also does load-bearing work, and that work silently stops
happening. The anti-pattern is the API shape that produces this hazard, not
any one instance of forgetting. A public or protected virtual method whose
contract secretly requires every override to invoke `super.method()`, usually
at a specific point (first, last, or wrapping the override's own body), with
nothing in the type system enforcing it.

Erich Gamma, Richard Helm, Ralph Johnson and John Vlissides never named the
anti-pattern, but their book supplies its documented cure under a different
heading. In *Design Patterns. Elements of Reusable Object-Oriented Software*,
Addison-Wesley, 1994, chapter 5, Behavioral Patterns, Template Method, the
authors describe hook methods as empty-bodied members a subclass may safely
override with no obligation to call anything, because the template method
itself, not the hook, drives the fixed sequencing. The GoF book is therefore
cited here twice over, once as the un-named ancestor of the problem (every
concrete framework method that is neither purely abstract nor a template-method
hook lands in the same trap) and once as the earliest catalogued fix.

Herb Sutter gave the fix its second name, the Non-Virtual Interface idiom, in
guidelines circulated through the mid-2000s and archived on the C++ community
wiki as four guidelines. Prefer non-virtual public interfaces built with the
Template Method pattern. Prefer private virtual functions. Make a virtual
function protected only when a derived class genuinely needs to invoke the
base implementation. Give a base class destructor either a public virtual
form or a protected non-virtual form (Wikibooks contributors, *More C++
Idioms, Non-Virtual Interface*,
https://en.wikibooks.org/wiki/More_C%2B%2B_Idioms/Non-Virtual_Interface
verified 2026-08-02). Joshua Bloch names the same failure from the library
author's chair in *Effective Java*, 3rd edition, Addison-Wesley, 2018, Item 19,
"Design and document for inheritance or else prohibit it", where he states
plainly that a class intended for inheritance must document every place a
method invokes an overridable method of itself, in what order, and with what
effect on later calls, because a self-use pattern of this kind is precisely
where the Call Super hazard lives.

A distinct but related name from refactoring literature is Refused Bequest,
coined by Martin Fowler and Kent Beck in *Refactoring. Improving the Design of
Existing Code*, Addison-Wesley, 1999, chapter 3, as the code smell where a
subclass uses only some of what its parent gives it. Refused Bequest and Call
Super sit on opposite ends of the same axis. Refused Bequest is a subclass
choosing not to want the parent's behaviour, which is a design smell about
hierarchy shape. Call Super is a subclass wanting the parent's behaviour,
believing it is getting it, and silently not getting it, which is a contract
enforcement failure. The two are cross-referenced under Related and
incompatible patterns but are not the same defect.

## 2. Problem and context

A base class method does two things at once. it declares an extension point a
subclass is meant to specialise, and it performs some piece of bookkeeping the
rest of the object, or the rest of the framework, depends on. `Activity.onCreate`
in the Android framework restores saved instance state and wires the theme
before the app's own `onCreate` override runs its layout code. `viewDidLoad` in
Apple's UIKit performs setup after the view hierarchy is loaded into memory,
and the framework's own default implementation is meant to run alongside a
subclass's customisation, not instead of it. `GenericServlet.init(ServletConfig)`
in the Java Servlet API stores the `ServletConfig` object the container handed
it so that `getServletConfig()` later works. In every one of these cases the
override exists to ADD behaviour, not to REPLACE it, but the language gives
the subclass author a single override slot that can do either, and nothing at
the call site distinguishes the two.

This is the context in which the problem arises. An inheritance-based
extension point where the base class method carries load-bearing side effects
(state initialisation, resource registration, invariant setup, framework
bookkeeping) and where overriding is the sanctioned way to specialise
behaviour. The failure appears the moment a subclass author, focused entirely
on the behaviour they are adding, writes the override without also writing
the call back to the parent, or writes it at the wrong point in the method
body. Because the compiler accepts the override with or without the call, the
mistake produces no error, no warning by default, and often no crash. It
produces a state that is subtly incomplete. a servlet whose `getServletConfig()`
returns null, an activity whose theme never applied, a dispose chain that
leaks a handle two levels up the hierarchy because a middle class's
`Dispose(bool)` returned without calling `base.Dispose(disposing)`. The bug
surfaces far from its cause, often in a different subsystem, sometimes only
under a specific lifecycle transition the original author never exercised.

The problem is worse in exactly the situations inheritance-based extension is
meant to help with. plugin architectures, UI framework lifecycle callbacks,
resource-management base classes, and any library published to authors the
original class designer will never meet. A closed hierarchy where every
subclass is visible in one repository can be grepped and reviewed. An open
one, where a third party writes the override in a codebase the framework
author never sees, cannot.

## 3. Forces

- **Extensibility versus enforceability.** Favouring extensibility, the base
  class exposes a method a subclass can override to add or change behaviour.
  Sacrificing enforceability, the compiler in mainstream object-oriented
  languages (Java, C#, Kotlin without an explicit guard, Swift, Objective-C)
  has no mechanism to force that override to also call the parent
  implementation, and no mechanism to force it at a particular point relative
  to the subclass's own logic.
- **Documentation cost versus silent breakage.** The library author can shift
  the burden onto prose ("remember to call super"), which costs nothing to
  write and everything to enforce, or onto tooling (a lint rule, a runtime
  assertion), which costs implementation effort but converts a silent failure
  into a build-time or test-time one.
- **Simplicity of the extension point versus safety of the extension point.**
  A single overridable method with documented call-super semantics is the
  simplest possible extension mechanism to read and write. Splitting it into a
  non-virtual public entry point and a private or protected hook (Template
  Method, Non-Virtual Interface) is safer but doubles the member count and
  requires the subclass author to learn a naming convention (an `_impl` or
  `Do`-prefixed hook name) instead of overriding the method they actually
  call.
- **Backward compatibility versus correctness.** A framework that ships a
  virtual method today and later discovers it needs guaranteed base behaviour
  cannot retroactively make the method non-virtual, because doing so breaks
  every subclass compiled against the old contract. This is why long-lived
  frameworks (the Java Servlet API, UIKit, the .NET dispose pattern) still
  carry the Call Super shape in places a green-field design would avoid, and
  why the fix is usually additive (an annotation, a lint check) rather than
  structural.
- **Team topology.** A single team owning both the base class and every
  subclass can catch a missing super call in code review. A platform team
  publishing a base class to many independent application teams, or to
  external plugin authors, cannot rely on review at all, and the enforcement
  burden shifts entirely onto tooling or onto redesigning the extension point.
- **Cognitive load at the override site.** The override author's attention is
  on the behaviour they are adding, not on the contract of the method they are
  replacing. A requirement that lives only in a doc comment competes for
  attention with the actual task and reliably loses, which is precisely the
  documented root cause practitioners give for this class of bug.

The pattern of forces here does not favour a middle ground. Either the
enforcement is structural, meaning the language or a static checker makes the
missing call impossible to ship, or it is not enforced at all and the defect
recurs at a rate proportional to how many subclass authors the base class has
who are not the base class's own author.

## 4. Applicability and non-applicability

This is an anti-pattern entry. The applicability question is inverted from a
normal design pattern entry. the goal is to recognise the API shape (a
concrete overridable method that quietly depends on being called through
`super`) so it can be avoided, and to know when a base implementation that
looks like Call Super is in fact acceptable.

Recognise Call Super, and treat it as a defect to redesign, in these cases.

- A base class method has a non-trivial body (it sets a field, opens a
  resource, registers a callback, mutates shared state) AND is declared
  `public virtual`, `protected virtual`, `open`, or the language's equivalent,
  meaning a subclass can override it and skip that body entirely.
- The only place the requirement to call `super` is written down is a prose
  comment or external documentation, with no compiler check and no runtime
  assertion.
- The base class's correctness in later methods (a getter, a subsequent
  lifecycle callback, a cleanup method) depends on the overridden method
  having run, but nothing verifies that dependency was satisfied.
- The class is intended to be subclassed by authors outside the team that owns
  it, so code review cannot serve as the enforcement mechanism.

Non-applicability, the cases where this is NOT the anti-pattern and should not
be redesigned away, follows.

- **A pure hook method with an empty base body**, as in the classical Template
  Method pattern. If the base implementation does nothing, forgetting to call
  it changes nothing, and there is no hazard to design against. This is the
  distinguishing test. does the base body do anything observable. If not, the
  method is a hook, not a Call Super trap.
- **An abstract method with no body at all.** The language already enforces
  that every concrete subclass supplies an implementation. There is nothing to
  forget to call because there is nothing there.
- **A protected method that exists specifically so a subclass can invoke it as
  a helper, by choice, not as an override obligation.** Calling it is optional
  functionality, not a silently broken contract if skipped.
- **A single, closed hierarchy under one team's control**, reviewed on every
  change, where the cost of the anti-pattern (a missed super call slipping
  past review) is genuinely low and a heavier structural fix (splitting the
  method into a non-virtual entry point and a private hook) would cost more in
  API surface than it saves. This is a judgement call about team topology, not
  a rule.
- **Idempotent, non-load-bearing base behaviour**, for example a base
  `toString()` override that only affects debug output and whose omission
  causes no functional defect, only a cosmetic one. The anti-pattern label is
  reserved for cases where correctness, not polish, depends on the call.

## 5. Structure

Two participants describe the vulnerable shape, and a third describes the
fix, so the fixed structure is included here for contrast even though the
fix's own dynamics belong to Template Method and Non-Virtual Interface, cited
under Related and incompatible patterns.

- **BaseClass.** Declares a method, call it `hook()`, as `public` or
  `protected` and overridable (`virtual`, `open`, non-`final`). The method
  body performs load-bearing work. it sets internal state, registers a
  resource, or maintains an invariant other members of BaseClass rely on.
- **SubClass.** Overrides `hook()` to add its own behaviour. The override
  either calls `super.hook()` at the documented point, calls it at the wrong
  point, or omits the call entirely. The compiler treats all three as equally
  valid.
- **The vulnerable contract.** The dependency runs from BaseClass's OTHER
  members (a getter, a later lifecycle method, a destructor) back onto the
  assumption that `hook()` ran to completion including the base body. This
  dependency exists in the author's head and in a doc comment, nowhere
  machine-checked.

The structural fix, Non-Virtual Interface applied to this exact shape, removes
the SubClass's ability to skip the base body by removing the override target
entirely. `hook()` becomes non-virtual (`public sealed` or simply non-virtual)
and its body is fixed. it does the load-bearing work and then calls a new,
narrower method, `hookImpl()`, private or protected, which is what the
subclass actually overrides. `hookImpl()` may be an empty hook or an abstract
method. Either way, the subclass cannot bypass the load-bearing work, because
it never had the ability to override the method that contains it.

## 6. ASCII structure diagram

```
   THE VULNERABLE SHAPE (Call Super)

   +----------------------------+
   |         BaseClass          |
   |----------------------------|
   | + hook() [virtual]         |  <-- subclass overrides THIS method
   |   { loadBearingWork(); }   |      and can skip loadBearingWork()
   +----------------------------+
                 ^
                 | extends
                 |
   +----------------------------+
   |         SubClass           |
   |----------------------------|
   | + hook() [override]        |
   |   { super.hook();  <---- OPTIONAL, unchecked, easy to omit
   |     addedBehaviour(); }    |
   +----------------------------+


   THE FIX (Non-Virtual Interface / Template Method)

   +------------------------------------+
   |             BaseClass               |
   |--------------------------------------|
   | + hook() [non-virtual, sealed]      |  <-- subclass CANNOT override
   |   { loadBearingWork();              |      this; loadBearingWork()
   |     hookImpl(); }                   |      always runs
   | # hookImpl() [virtual, empty/abst.] |  <-- subclass overrides THIS
   +------------------------------------+      instead, no super call needed
                 ^
                 | extends
                 |
   +------------------------------------+
   |             SubClass                |
   |--------------------------------------|
   | # hookImpl() [override]             |
   |   { addedBehaviour(); }             |
   +------------------------------------+
```

## 7. Dynamics

The vulnerable dynamics show why the bug is invisible at the call site. The
caller of `hook()` never knows, and cannot know from the call alone, whether
the load-bearing work happened.

```
Framework            SubClass instance         BaseClass (inherited)
   |                        |                          |
   |-- hook() ------------->|                          |
   |                        |  (virtual dispatch       |
   |                        |   reaches SubClass       |
   |                        |   override, not the      |
   |                        |   base implementation)   |
   |                        |                          |
   |                        |-- addedBehaviour() ----->|
   |                        |   (super.hook() call     |
   |                        |    OMITTED here)         |
   |                        |<-------------------------|
   |<-- returns ------------|                          |
   |                        |                          |
   ... time passes, unrelated code runs ...
   |                        |                          |
   |-- getSomeField() ----->|                          |
   |                        |-- reads uninitialised    |
   |                        |   or stale field, because|
   |                        |   loadBearingWork() in   |
   |                        |   BaseClass.hook() never |
   |                        |   ran for this instance  |
   |<-- wrong/null value ---|                          |
```

The two moments are separated in time, often across a thread boundary, a
lifecycle callback boundary, or a request boundary, which is exactly why the
defect is hard to trace back to its cause. The fixed dynamics collapse the gap
because the load-bearing work is no longer optional.

```
Framework            SubClass instance         BaseClass.hook() [fixed body]
   |                        |                          |
   |-- hook() ------------->|                          |
   |                        |  (hook() is non-virtual, |
   |                        |   resolves statically    |
   |                        |   to BaseClass)           |
   |                        |                          |
   |                        |-------------------------->|
   |                        |                          |-- loadBearingWork()
   |                        |                          |   (ALWAYS runs)
   |                        |                          |-- calls hookImpl()
   |                        |<-- virtual dispatch ------|   (virtual, reaches
   |                        |    reaches SubClass       |    SubClass override)
   |                        |-- addedBehaviour()        |
   |                        |-------------------------->|
   |<-- returns ------------|                          |
```

## 8. Implementation variants

The variants below are the documented ways codebases either fall into the
anti-pattern or climb out of it, ordered from weakest to strongest guard.

**Prose-only contract (the anti-pattern itself, undefended).** The base
method's doc comment states the requirement, and nothing else enforces it.
This is the shape `GenericServlet.init(ServletConfig)` still carries. its
Javadoc says plainly, "When overriding this form of the method, call
`super.init(config)`", with no compiler or runtime check behind it.

**Annotation-based lint enforcement.** The base method is marked with an
annotation the toolchain understands, and a static analysis pass fails the
build if an override does not contain a call to the corresponding super
method. Android's `androidx.annotation.CallSuper` is the canonical example.
Its own documentation states its purpose in one line, "Denotes that any
overriding methods should invoke this method as well" (androidx source,
`CallSuper.kt`, `androidx-main` branch,
https://raw.githubusercontent.com/androidx/androidx/androidx-main/annotation/annotation/src/commonMain/kotlin/androidx/annotation/CallSuper.kt
verified 2026-08-02). Android Lint's inspection for the annotation is commonly
referenced by the check id `MissingSuperCall`. This variant keeps the flexible
single-method shape (a subclass still overrides one method and decides where
in its body to place the call) but converts a silent runtime defect into a
build-time or IDE-time diagnostic. It is the cheapest fix to retrofit onto an
existing large hierarchy, because it changes no method signatures.

**Runtime assertion.** The base method sets a flag when its body runs, and a
subsequent lifecycle step asserts the flag was set, throwing or logging loudly
if not. This trades compile-time safety for something weaker but still far
better than silence. a test-time or first-run-time failure rather than a
correctness bug discovered in production weeks later. It is common where an
annotation-based checker is unavailable for the language or where the
violation needs to be caught even when a subclass is compiled separately from
the base class and never passes through the same lint pass, for example a
dynamically loaded plugin.

**Static type check via linter, without a dedicated annotation.** Pylint's
`super-init-not-called` (W0231) check is an example specific to Python
constructors. it reads, "Used when an ancestor class method has an `__init__`
method which is not called by a derived class" (pylint source,
`pylint/checkers/classes/class_checker.py`, `main` branch,
https://raw.githubusercontent.com/pylint-dev/pylint/main/pylint/checkers/classes/class_checker.py
verified 2026-08-02). Python has no `virtual` keyword and no annotation
convention as widespread as Android's, so the check is built into the linter's
general knowledge of `__init__` chains rather than driven by a marker the base
class author applies.

**Non-Virtual Interface / Template Method split.** The base method becomes
non-virtual and delegates to a differently named, narrower protected or
private hook, as shown in dimension 5 and 6. This is the only variant that
removes the hazard structurally rather than detecting it. It costs an extra
member per extension point and a naming convention subclass authors must
learn, and it is the shape recommended by Herb Sutter's guidelines and
demonstrated by the GoF Template Method pattern itself.

**Split public and protected method pair with a mandatory call already baked
into the public method, the .NET dispose pattern.** A middle ground between
the prose-only shape and full Non-Virtual Interface. the public entry point
(`Dispose()`) is non-virtual and its body is fixed, but the method a derived
class actually overrides (`protected virtual void Dispose(bool disposing)`)
still requires a super call, now written as `base.Dispose(disposing)`, and
that requirement is still enforced only by documentation, not by the
compiler. This variant is documented at length in dimension 9. it is included
here because it shows that even a redesigned entry point can still contain a
smaller, second instance of the same anti-pattern one level down, if the
protected hook itself is not further split.

**Compile-time enforcement via sealed dispatch.** Languages that default
members to non-overridable, requiring an explicit keyword to opt in
(`open` in Kotlin, `open`/`final` conventions in some C++ style guides), push
every new method toward the safe default. This does not remove the
anti-pattern for methods deliberately marked `open`, but it prevents it from
appearing BY ACCIDENT on methods nobody meant to expose as extension points,
which is a meaningful share of real-world instances. Kotlin's own
documentation is explicit that marking a member `open` still requires an
explicit `super.member()` call to invoke the base implementation, stating,
"Code in a derived class can call its superclass functions and property
accessor implementations using the `super` keyword" (Kotlin documentation,
Inheritance, https://kotlinlang.org/docs/inheritance.html verified
2026-08-02). Marking something `open` narrows WHICH methods can carry the
hazard. it does not remove the hazard from those methods.

## 9. Known production uses

**Java Servlet API, `GenericServlet.init(ServletConfig)`.** The default
implementation stores the container-supplied `ServletConfig` for later
retrieval via `getServletConfig()`. Its own Javadoc states the requirement in
one sentence, "This implementation stores the `ServletConfig` object it
receives from the servlet container for later use. When overriding this form
of the method, call `super.init(config)`" (Oracle Java EE 7 API
documentation, `javax.servlet.GenericServlet`,
https://docs.oracle.com/javaee/7/api/javax/servlet/GenericServlet.html
verified 2026-08-02). A servlet that overrides `init(ServletConfig)` and
omits the call finds `getServletConfig()` returns null later in its life
cycle, a defect that has been common enough in Java web development to be a
recurring topic in servlet tutorials for two decades.

**Apple UIKit, `UIViewController.viewDidLoad()`.** Called once the view
controller's view hierarchy is loaded into memory, and the documented pattern
for overriding it is to call `super.viewDidLoad()` first and then perform
additional setup. Apple's own reference confirms the method's purpose,
"Called after the controller's view is loaded into memory", and every code
example Apple ships for the method opens with the super call (Apple Developer
Documentation, `UIViewController.viewDidLoad()`,
https://developer.apple.com/documentation/uikit/uiviewcontroller/viewdidload()
verified 2026-08-02). UIKit does not enforce the call mechanically. Swift and
Objective-C provide no compiler check for it, so the requirement is carried
entirely by documentation and by convention repeated in every tutorial and
project template Apple distributes.

**Android framework, lifecycle callbacks guarded by `@CallSuper`.** Android's
`Activity`, `Fragment`, and `View` classes expose lifecycle methods
(`onCreate`, `onStart`, `onDestroy`, and others) whose base implementations
perform framework bookkeeping a subclass override must not skip. The
`androidx.annotation.CallSuper` annotation exists specifically to let the
framework authors mark these methods so Android Lint can flag a missing super
call at build time rather than leaving the requirement to documentation alone
(androidx source, `CallSuper.kt`,
https://raw.githubusercontent.com/androidx/androidx/androidx-main/annotation/annotation/src/commonMain/kotlin/androidx/annotation/CallSuper.kt
verified 2026-08-02). The existence of a dedicated, framework-maintained
annotation for exactly this hazard, applied across the platform's most
heavily subclassed API surface, is itself evidence of how often the
undocumented, unenforced form of Call Super produced real defects in Android
applications.

**.NET, the `IDisposable` dispose pattern's `Dispose(bool disposing)`
override.** Microsoft's own guidance states the requirement without
ambiguity, "A `protected override void Dispose(bool)` method that overrides
the base class method and performs the actual cleanup of the derived class.
This method must also call the `base.Dispose(bool)` (`MyBase.Dispose(bool)`
in Visual Basic) method passing it the disposing status" (Microsoft Learn,
"Implement a Dispose method",
https://learn.microsoft.com/en-us/dotnet/standard/garbage-collection/implementing-dispose
verified 2026-08-02). Every derived-class code sample Microsoft publishes for
this pattern ends its `Dispose(bool disposing)` override with an explicit
`base.Dispose(disposing)` call, and omitting it is documented in the same
guidance as a resource leak in any class two or more levels deep in a
disposable hierarchy, because each level's own cleanup depends on the level
above it also running.

## 10. Consequences

Positive, in the limited sense that the anti-pattern's underlying extension
mechanism (a virtual method a subclass overrides to add behaviour) is
genuinely useful and cheap to build.

- The base class author writes one method and gets a working extension point
  immediately, with no additional member, no naming convention for a second
  hook method, and no change to the public API shape a caller sees.
- Framework code that has shipped this way for a long time (the Servlet API,
  UIKit) has enormous accumulated documentation, tutorials, and developer
  familiarity, which lowers the practical cost of the missing enforcement for
  experienced teams even though the structural hazard remains.
- The pattern requires no extra abstraction (no separate hook interface, no
  wrapper type) and is trivially discoverable by reading the base class's
  method list, unlike some structural fixes that hide the real extension point
  behind a differently named protected member.

Negative, which is why this entry classifies the shape as an anti-pattern
rather than a neutral design choice.

- The defect it produces is silent by construction. no compile error, no
  runtime exception at the point of omission, and often no immediately visible
  symptom, only a state that is subtly wrong somewhere else in the object's
  life cycle.
- The cost of the defect is paid far from its cause, frequently by a different
  engineer than the one who wrote the override, and frequently long after the
  code review that should have caught it.
- The burden of correctness is placed entirely on every future subclass
  author, an unbounded and often external population, rather than on the base
  class author who could fix it once.
- It scales badly with hierarchy depth. A three-level hierarchy where each
  level's `hook()` override must call `super.hook()` has three independent
  chances for the chain to break, and the failure at any one level silently
  breaks every level above it.
- Retrofitting a structural fix (Non-Virtual Interface) onto a widely
  subclassed, already-published base class is a breaking API change, which is
  why long-lived platforms accumulate lint-based and annotation-based
  mitigations instead of redesigning the method shape outright.

## 11. Failure modes and misuse

**Missing super call in a lifecycle method.** Symptom. an object works
correctly the very first time it is exercised but exhibits a stale or
default value for state the base class was supposed to initialise, most
visible when the base class's initialisation is itself conditional (only
setting a field the second time a method runs, for example) so the very first
call happens to look correct by accident. Cause. the override never calls
`super.hook()` at all. Fix. add the call, and where the language and tooling
allow it, add a static or lint check (`@CallSuper`, a custom analyzer, a
pylint plugin) so a future subclass cannot regress the same way.

**Super call at the wrong point in the override.** Symptom. behaviour that
depends on ORDER is wrong even though the super call is present. a field the
base class sets is overwritten by the subclass's own logic because the
subclass called `super.hook()` LAST when the contract required FIRST, or vice
versa. Cause. the documentation states an ordering requirement (call super
first, then add behaviour) but nothing enforces the order, only the presence
of the call. Fix. state the ordering requirement in the strongest available
form (a code example in the doc comment showing the exact placement) and,
where a redesign is affordable, remove the ordering ambiguity entirely by
moving to Non-Virtual Interface, where the base class controls sequencing and
the subclass's hook has no ordering decision to get wrong.

**Partial dispose chain across a multi-level hierarchy.** Symptom. a resource
leak (an open file handle, an undisposed child object) that reproduces only
when a specific concrete subclass three levels deep in the hierarchy is used,
and does not reproduce with a shallower subclass. Cause. one middle class in
the chain overrides `Dispose(bool disposing)` and returns without calling
`base.Dispose(disposing)`, so every level above it in the hierarchy never
runs its own cleanup for that instance. Fix. audit every override of the
dispose hook in the hierarchy for the trailing base call, and add an
automated test that constructs each concrete leaf type, disposes it, and
asserts every level's cleanup ran (via an instrumented counter or a mock),
per dimension 15.

**Super call duplicated across a diamond-shaped mixin or trait hierarchy.**
Symptom. a side effect the base class performs (a counter increment, a log
line, a registration) happens more than once for a single logical call,
producing double-counted metrics or a resource registered twice. Cause. in
languages that support multiple inheritance of implementation (C++ virtual
base classes, Python's method resolution order with multiple parents each
overriding the same method), a naive chain of individual `super()` calls can
walk the same ancestor implementation more than once if the hierarchy is not
using the language's own linearisation correctly (`super()` without explicit
class targeting in Python's cooperative multiple inheritance, virtual
inheritance in C++). Fix. use the language's designed-for-this mechanism
(Python's MRO-aware `super()`, C++ virtual base classes) rather than manually
chained same-name calls up a hand-rolled hierarchy, and add a test asserting
the side effect happens exactly once for the deepest concrete type.

**A test double that mocks the class under test's own base method.** Symptom.
a unit test passes even though the real object, exercised end to end, exhibits
the missing-super-call defect. Cause. a partial mock or a test-only subclass
stubs out the very method whose super-call contract is under test, so the
test never exercises the real base implementation and cannot detect its
absence. Fix. see the contract test recommendation in dimension 15. exercise
the concrete production subclass directly rather than a stand-in that
happens to share its method names.

**Silent regression when the base class adds new load-bearing work.**
Symptom. every EXISTING subclass that previously called super correctly
starts misbehaving the moment the base class version is upgraded, with no
change to any subclass's own code. Cause. the base class author adds a new
field initialisation or a new side effect to the existing `hook()` method,
assuming every override already calls super and will therefore pick up the
new behaviour automatically, but some overrides call super at the wrong
point (the second failure mode above) so the new behaviour lands at the
wrong time relative to the subclass's own logic, or a subclass's super call
was conditional on a flag that is no longer true for the new code path. Fix.
treat any change to a Call Super method's load-bearing work as a breaking
change to the extension contract, and re-verify the contract test suite from
dimension 15 against every known subclass before shipping the base class
change, exactly as a semantic-versioning discipline would require for any
other API contract change.

## 12. Trade-off matrix

Compared against the named structural alternatives, across the forces from
dimension 3.

| Force | Call Super (undocumented, unenforced) | Call Super + lint annotation (`@CallSuper`, Pylint W0231) | Non-Virtual Interface / Template Method | Abstract method (no default body) | Strategy (composition, no inheritance) |
|---|---|---|---|---|---|
| Compiler enforces the contract | No | No, but a static analysis pass does at build time | Yes, structurally. there is nothing to skip | Yes, a missing implementation fails to compile | Yes, there is no super call to omit |
| Extra members needed | None | None, only an annotation on the existing method | One extra hook method per extension point | None | An interface plus one implementing class per strategy |
| Backward-compatible to retrofit onto a shipped API | Trivially, it changes nothing | Yes, adding the annotation is additive | No, changing an existing virtual method to non-virtual breaks existing overriders | Not applicable, only fits a method with no useful default | No, requires callers to be re-wired to accept a strategy object |
| Ordering of base and subclass behaviour controllable by the base | No, the subclass decides ordering entirely | No, the annotation checks presence, not ordering | Yes, the base method's body fixes the ordering | Not applicable | Yes, the composing class controls ordering by construction |
| Works across an open, third-party subclass population | Poorly, no enforcement travels with the API | Well, if the third party's toolchain runs the same lint pass | Well, the guarantee is structural and travels with the compiled type | Well, for the has-a-value-or-not question, but says nothing about ordering | Well, and additionally decouples third parties from the inheritance hierarchy entirely |
| Cost to introduce into a green-field design | Lowest, one method | Low, one method plus one annotation | Medium, two members instead of one, plus a naming convention | Low, one method, but only fits when there is no sensible default | Medium to high, requires designing an interface and injection point up front |

Reading of the table. Undocumented Call Super is the cheapest and least safe
of these options and should not be a deliberate design choice for new code.
The lint-annotation variant is the pragmatic retrofit for a hierarchy that
already exists and cannot be restructured. Non-Virtual Interface and
Strategy are the two structural exits, and the choice between them tracks
whether the extension really is the same operation, customised, which favours
Non-Virtual Interface and staying with inheritance, or a genuinely swappable
algorithm, which favours Strategy and leaving inheritance behind, per the
guidance in the Strategy pattern entry of this catalog.

## 13. Related and incompatible patterns

- **Template Method.** The direct, catalogued fix. Template Method makes the
  overall algorithm's steps fixed and non-virtual in the base class, exposing
  only narrow, ideally empty-bodied hook methods for a subclass to
  specialise. Applying Template Method to an existing Call Super method is
  literally the Non-Virtual Interface refactor described in dimensions 5, 6,
  and 14.
- **Factory Method.** Frequently the specific hook a Call Super method is
  guarding around, in frameworks where object creation is one step of a
  larger fixed algorithm. See the Factory Method entry in this catalog for
  the case where the overridable member is itself a creation decision rather
  than a side-effecting lifecycle step, and note the same GoF chapter
  describes Factory Method as commonly invoked from within a Template Method,
  which is the same structural relationship this entry recommends as the
  fix.
- **Decorator.** An alternative escape from inheritance-based extension
  altogether. Where Call Super tries to let a subclass add behaviour around
  an inherited method, Decorator wraps an object at composition time and adds
  behaviour before or after delegating to the wrapped object's own method,
  with no super-call obligation because there is no inheritance relationship
  to forget. Decorator trades the convenience of a single override for
  explicit, always-executed wrapping.
- **Strategy.** A second alternative escape, favoured when the varying
  behaviour is closer to a whole algorithm than one step of a fixed
  algorithm. Strategy removes the inheritance relationship entirely, which
  removes the Call Super hazard by removing the mechanism (virtual dispatch
  into a partially-overridden method) that creates it.
- **Liskov Substitution Principle.** The principle a Call Super violation
  most directly undermines when the missing base behaviour is an INVARIANT
  the rest of the class relies on. A subclass whose override silently skips
  the base class's invariant-preserving code is no longer safely substitutable
  wherever the base class was expected, even though it satisfies the type
  system.
- **Refused Bequest (code smell family).** A related but distinct smell. a
  subclass that deliberately does not want the parent's behaviour, versus
  Call Super's subclass that wants it and fails to get it by accident. A
  hierarchy exhibiting Refused Bequest is a signal the inheritance
  relationship itself is wrong (composition or a narrower interface would fit
  better), which is a different diagnosis from Call Super's signal that the
  extension mechanism needs stronger enforcement.
- **Incompatible with Template Method by construction, not by conflict.**
  Recorded in this entry's frontmatter as incompatible with Template Method
  in the specific sense that a single method cannot simultaneously be the
  undocumented, overridable, side-effecting Call Super shape and be a
  properly split Template Method hook for the same responsibility. Applying
  the fix removes the anti-pattern from that method. they are mutually
  exclusive implementations of the same extension point, not two patterns
  that compose.

## 14. Refactoring path in and out

Since this is an anti-pattern entry, "in" describes how a codebase typically
arrives at this shape without intending to, and "out" describes the
structural fix, corresponding in spirit to what the refactoring literature
calls Form Template Method, performed here in the safety-first, add-then-remove
direction.

How a codebase arrives here, usually unintentionally, follows this shape.

1. A base class method starts with an empty or near-empty body, a genuine
   hook in the Template Method sense.
2. Over time, requirements accumulate load-bearing work into that same
   method (a metrics counter, a validation step, a resource registration)
   because it is the path of least resistance. the method already exists and
   is already called at the right point in the life cycle.
3. No one revisits whether the method should still be freely overridable now
   that its body carries load-bearing side effects, because each individual
   addition looked small.
4. The method has quietly transitioned from a safe hook to a Call Super trap
   with no single commit that looks like a design regression.

The fix, ordered so each step is safe to ship independently and the tests
stay green throughout, follows.

1. Identify every existing override of the method across the codebase (or,
   for a published library, every known consumer you can find) and confirm
   what each one currently does relative to the base body, particularly
   whether the super call is present and where it sits.
2. Add the cheapest available enforcement first, before attempting the
   structural split, so the hierarchy stops accumulating NEW violations while
   the larger refactor is in progress. In Java or Kotlin on Android, that is
   the `@CallSuper` annotation. In Python, confirm the linter's
   `super-init-not-called` class of check, or an equivalent custom check for
   non-`__init__` methods, is enabled and enforced in CI.
3. Introduce a new, narrower method (`hookImpl()` or a similarly distinct
   name) with the same visibility and override semantics the original method
   had, but with the load-bearing work removed from it, that is, exactly the
   empty or nearly-empty body a genuine hook should have.
4. Change the original method's own body to perform the load-bearing work
   and then call the new narrower method, and mark the original method
   non-virtual, sealed, or final, so it can no longer be overridden.
5. Migrate each existing subclass override, one at a time, so it overrides
   the new narrower method instead of the original one, removing that
   subclass's now-redundant super call in the process since the call is no
   longer needed. Run the full test suite after each migration.
6. Once every subclass has migrated, the original method's signature can be
   locked (in a published library, this is the point at which the
   compatibility break, if any, has already been absorbed by the earlier
   additive steps).
7. Add the contract test from dimension 15 against every concrete subclass so
   a future violation of the (now structurally impossible for the old method,
   but still theoretically possible for the new narrower one if it grows the
   same way) hazard is caught immediately rather than accumulating again.

There is no meaningful refactoring path in the opposite direction, that is,
introducing Call Super where Non-Virtual Interface already exists, because
that direction is the anti-pattern itself, not a design choice a team makes
deliberately. It is included in the general refactoring family only as the
negative example against which Form Template Method is described.

## 15. Testing and verification

Harder because of the anti-pattern.

- A unit test that exercises only the subclass's OWN added behaviour, without
  also asserting the base class's load-bearing work happened, will pass even
  when the super call is missing, because the test was never written to check
  for the base behaviour's side effect in the first place. This is the single
  most common reason the defect ships. the test suite covering the subclass
  was written from the subclass author's mental model, which did not include
  whether the call to super was ever made.
- A partial mock of the class under test, one of the most common ways teams
  accidentally hide this defect from their own test suite, stubs out the
  exact method whose contract is in question, so the mock never runs the real
  base implementation and the test cannot observe its absence.

Techniques that apply follow.

- **Contract test per concrete subclass.** Write one abstract test case
  against the base class's documented contract (analogous to the contract
  test pattern used for interface implementations generally), with an
  abstract factory method supplying the concrete subclass under test, then
  run the same suite once per concrete subclass. Assert the OBSERVABLE effect
  of the base class's load-bearing work (a field is set, a counter
  incremented, a resource registered) after calling the overridden method on
  each concrete instance, not merely that the subclass's own added behaviour
  worked.
- **Instrumented base class in test builds.** For hierarchies too large to
  retrofit contract tests onto every subclass at once, a test-only base class
  variant can increment a counter inside its load-bearing-work body, and a
  reflection-based or fixture-driven sweep can instantiate every known
  concrete subclass, invoke the hook, and assert the counter incremented
  exactly once per instance. This catches both a missing call and, with care
  around fixture setup, a duplicated call from a diamond hierarchy.
- **Static analysis as a test-suite-adjacent gate.** Where `@CallSuper`,
  Pylint's `super-init-not-called`, or an equivalent static check is
  available, run it as a required CI check alongside the test suite rather
  than treating it as optional tooling. it catches the defect in code the
  runtime test suite may never exercise, for example a rarely-instantiated
  subclass with no dedicated tests at all.
- **Golden-path integration test through the real life cycle.** For framework
  lifecycle methods specifically (Android activities, iOS view controllers,
  servlet initialisation), an end-to-end test that drives the real life
  cycle (start the activity, load the view controller, initialise the
  servlet through the real container) and asserts the framework-level
  post-condition holds catches the defect even when no unit test targeted
  the specific method, because it exercises the actual dispatch path the
  production system uses.

## 16. Observability signals

The anti-pattern is dangerous in production specifically because it produces
no error signal by default. observability has to be added deliberately to
turn a silent gap into a visible one.

The following signals are worth recording.

- A counter or gauge, incremented inside the base class's load-bearing-work
  body, labelled by the concrete subclass's runtime type. A healthy system
  shows this counter's rate tracking the rate of the outer operation (one
  activity creation, one servlet request, one disposed object) one for one.
  A subclass whose count is consistently zero or consistently below the
  outer operation's rate is the direct signal that its override is not
  reaching the base implementation.
- A log line, at debug level in normal operation and raised to warning level
  if an assertion-based guard (dimension 8's runtime-assertion variant)
  detects the load-bearing work did not run before a dependent operation
  needed it, naming the concrete subclass type so the offending override can
  be found immediately rather than inferred from a stack trace several calls
  removed.
- For dispose-pattern hierarchies specifically, a live-instance gauge per
  concrete type (see the Factory Method entry's observability section for the
  same technique applied to creation) that should return to zero, or close to
  it, after disposal. a gauge that plateaus above zero for a specific
  concrete type localises a broken dispose chain to that type without reading
  any code.
- Build-time or CI-time observability. a static analysis check (`@CallSuper`,
  `super-init-not-called`) run as a named, tracked CI job, with its pass and
  fail counts visible over time, so a rising rate of newly introduced
  violations is caught as a trend before it becomes a production incident.

A healthy instance on a dashboard looks like this. the per-subclass
load-bearing-work counter and the outer operation's own counter move
together, at the same rate, for every concrete type the system exercises. A
failing instance looks different. one concrete subclass's load-bearing-work
counter sits flat while the same subclass's outer operation counter climbs,
which is the signature of a specific override having stopped calling super,
isolatable to that one type without needing to reproduce the bug locally
first.

## 17. Security and privacy implications

Judgement. the following analysis draws on the general shape of the anti-pattern
rather than a single sourced incident naming this exact failure as a security
defect, and is presented as reasoning, not as a documented CVE class.

Where the base class's load-bearing work performs a SECURITY-RELEVANT step
(input validation, an authorization check, sanitisation of data before it is
stored or rendered, initialisation of a rate limiter or an audit log), a
missing super call becomes a security control that silently does not run for
a specific subclass. This is a more serious variant of the general defect
because it fails OPEN rather than merely producing wrong data. a subclass
that skips a base class's validation step in an override does not raise an
exception, it simply proceeds as if the input were already validated. A base
class designed as a security boundary (a request handler base class that
sanitises input in an overridable `handle()` method, for example) is exactly
the shape this entry warns against reaching for. Security-critical
load-bearing work belongs in the Non-Virtual Interface's non-overridable
entry point, never in a method a subclass can silently bypass, precisely
because the consequence of a missed call is not merely a bug but an
unenforced control.

Audit logging is a specific, common instance of this risk. an audit trail
base method that logs "action performed" and that a subclass overrides to add
its own action-specific detail is only trustworthy as an audit record if the
base logging call cannot be silently skipped. an attacker or a careless
subclass author who omits the call produces a gap in the audit trail with no
corresponding alert, which is precisely the property an audit log is meant
not to have.

On privacy specifically, the pattern carries a narrower but real implication.
Where a base class's load-bearing work performs data minimisation,
redaction, or consent-check logic before data reaches a subclass's own
processing, a missing super call means a subclass processes data that should
have been redacted or gated first. As with the security point above, the
mitigation is structural rather than procedural. any method whose base body
enforces a privacy control should not be a virtual method a subclass can
override without going through it, and should instead be designed with the
Non-Virtual Interface split from the first line of code, not retrofitted
after an incident.

## Code examples

Four languages, chosen because each shows a different real production
manifestation of the same shape. Java mirrors the Servlet API's documented
contract. Kotlin shows the annotation-based enforcement Android uses in
practice, plus the fix. Swift mirrors the UIKit `viewDidLoad` convention.
Python shows the constructor-chaining form the Pylint check targets. All four
were compiled or run as noted below.

### Java

Compiled with `javac`. The vulnerable shape is followed by the Non-Virtual
Interface fix in the same file, so both are directly comparable.

```java
import java.util.HashMap;
import java.util.Map;

// THE ANTI-PATTERN: load-bearing work lives in an overridable method.
abstract class ConfigLoaderVulnerable {
    protected Map<String, String> config;

    // Subclasses override this to add their own keys. Nothing stops a
    // subclass from skipping the load-bearing work below.
    public void load() {
        config = new HashMap<>();
        config.put("initialized", "true");
    }
}

class YamlConfigLoaderBuggy extends ConfigLoaderVulnerable {
    @Override
    public void load() {
        // Forgot to call super.load(). config stays null.
        System.out.println("loading yaml config");
    }
}

// THE FIX: Non-Virtual Interface. load() is now final; subclasses
// override loadImpl(), which cannot bypass the load-bearing work.
abstract class ConfigLoaderFixed {
    protected Map<String, String> config;

    public final void load() {
        config = new HashMap<>();
        config.put("initialized", "true");
        loadImpl();
    }

    protected abstract void loadImpl();
}

class YamlConfigLoaderCorrect extends ConfigLoaderFixed {
    @Override
    protected void loadImpl() {
        config.put("format", "yaml");
    }
}

public class CallSuperDemo {
    public static void main(String[] args) {
        YamlConfigLoaderBuggy buggy = new YamlConfigLoaderBuggy();
        buggy.load();
        System.out.println("buggy config is null: " + (buggy.config == null));

        YamlConfigLoaderCorrect fixed = new YamlConfigLoaderCorrect();
        fixed.load();
        System.out.println("fixed config: " + fixed.config);
    }
}
```

### Kotlin

Demonstrates the annotation-based mitigation alongside the structural fix.
`kotlinc` was not available in this environment. the file was hand-checked
against the Kotlin language grammar and against the documented behaviour of
`open` and `override` cited in dimension 8, and this is stated plainly rather
than claiming a compiler run that did not happen.

```kotlin
// Mitigation variant: an annotation-style marker (androidx.annotation.CallSuper
// is the real one; this is a same-shape stand-in since the androidx dependency
// is not available in this file) documents the requirement, and a lint pass
// external to this file would flag a missing call.
annotation class RequiresSuperCall

abstract class LifecycleOwnerVulnerable {
    var started: Boolean = false
        protected set

    @RequiresSuperCall
    open fun onStart() {
        started = true
    }
}

class ScreenVulnerable : LifecycleOwnerVulnerable() {
    override fun onStart() {
        // Missing super.onStart(). `started` never becomes true.
        println("screen started")
    }
}

// Structural fix: onStart is no longer open. Subclasses override onStartImpl.
abstract class LifecycleOwnerFixed {
    var started: Boolean = false
        private set

    fun onStart() {
        started = true
        onStartImpl()
    }

    protected open fun onStartImpl() {
        // empty hook, safe to override or ignore
    }
}

class ScreenFixed : LifecycleOwnerFixed() {
    override fun onStartImpl() {
        println("screen started")
    }
}

fun main() {
    val vulnerable = ScreenVulnerable()
    vulnerable.onStart()
    println("vulnerable.started = ${vulnerable.started}")

    val fixed = ScreenFixed()
    fixed.onStart()
    println("fixed.started = ${fixed.started}")
}
```

### Swift

Compiled with `swiftc`. Mirrors the UIKit `viewDidLoad()` convention cited in
dimension 9, using a stand-in base class since `UIViewController` requires
the UIKit framework, which is not linkable in this headless run.

```swift
// THE ANTI-PATTERN: mirrors UIViewController.viewDidLoad(). The base
// class's load-bearing work is easy to skip because it is just a normal
// overridable method with no compiler-enforced call requirement.
class ScreenControllerVulnerable {
    var didLoadTheme = false

    func viewDidLoad() {
        didLoadTheme = true
    }
}

class ProfileScreenBuggy: ScreenControllerVulnerable {
    override func viewDidLoad() {
        // Forgot super.viewDidLoad(). didLoadTheme stays false.
        print("profile screen loaded")
    }
}

// THE FIX: split into a final entry point and an overridable hook.
class ScreenControllerFixed {
    private(set) var didLoadTheme = false

    final func viewDidLoad() {
        didLoadTheme = true
        viewDidLoadImpl()
    }

    func viewDidLoadImpl() {
        // empty hook
    }
}

class ProfileScreenCorrect: ScreenControllerFixed {
    override func viewDidLoadImpl() {
        print("profile screen loaded")
    }
}

let buggy = ProfileScreenBuggy()
buggy.viewDidLoad()
print("buggy.didLoadTheme = \(buggy.didLoadTheme)")

let fixed = ProfileScreenCorrect()
fixed.viewDidLoad()
print("fixed.didLoadTheme = \(fixed.didLoadTheme)")
```

### Python

Run with `python3`. Mirrors the `super-init-not-called` check cited in
dimension 8, and shows Python's cooperative `super()` as the fix for
constructor chaining specifically.

```python
class ResourceOwnerVulnerable:
    def __init__(self):
        self.resources = []
        self.resources.append("base-handle")


class CachingResourceVulnerable(ResourceOwnerVulnerable):
    def __init__(self):
        # Forgot to call super().__init__(). self.resources never exists.
        self.cache = {}


class ResourceOwnerFixed:
    def __init__(self):
        self.resources = []
        self.resources.append("base-handle")


class CachingResourceFixed(ResourceOwnerFixed):
    def __init__(self):
        super().__init__()
        self.cache = {}


if __name__ == "__main__":
    buggy = CachingResourceVulnerable()
    try:
        print("buggy.resources =", buggy.resources)
    except AttributeError as exc:
        print("buggy raised AttributeError,", exc)

    fixed = CachingResourceFixed()
    print("fixed.resources =", fixed.resources)
    print("fixed.cache =", fixed.cache)
```

Running the Python example prints an `AttributeError` naming the missing
`resources` attribute on the buggy instance, followed by the fixed instance's
correctly populated `resources` and `cache` attributes, confirming both the
failure mode and the fix live-executed as described.

## 18. References

1. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides. *Design
   Patterns. Elements of Reusable Object-Oriented Software*. Addison-Wesley,
   1994. ISBN 0-201-63361-2. Chapter 5, Behavioral Patterns, Template Method.
   Source of the hook-method concept that is the documented, catalogued fix
   for the shape described in this entry.
2. Joshua Bloch. *Effective Java*, 3rd edition. Addison-Wesley, 2018.
   ISBN 978-0-13-468599-1. Item 19, "Design and document for inheritance or
   else prohibit it". Source of the requirement that a class designed for
   inheritance document its self-use of overridable methods, the library
   author's-side framing of this anti-pattern.
3. Martin Fowler, with Kent Beck, John Brant, William Opdyke, Don Roberts.
   *Refactoring. Improving the Design of Existing Code*. Addison-Wesley,
   1999. ISBN 0-201-48567-2. Chapter 3, the Refused Bequest smell. Source of
   the related but distinct code smell distinguished in dimension 1 and
   dimension 13.
4. Wikibooks contributors. "More C++ Idioms, Non-Virtual Interface".
   https://en.wikibooks.org/wiki/More_C%2B%2B_Idioms/Non-Virtual_Interface
   Verified 2026-08-02. Source of Herb Sutter's guidelines cited in
   dimension 1, and the structural fix described in dimensions 5, 6, and 14.
5. Oracle. *Java EE 7 API Specification*, `javax.servlet.GenericServlet`.
   https://docs.oracle.com/javaee/7/api/javax/servlet/GenericServlet.html
   Verified 2026-08-02. Source of the `init(ServletConfig)` production use
   and its exact documented call-super requirement, dimension 9.
6. Apple Inc. Apple Developer Documentation, `UIViewController.viewDidLoad()`.
   https://developer.apple.com/documentation/uikit/uiviewcontroller/viewdidload()
   Verified 2026-08-02. Source of the UIKit production use, dimension 9.
7. androidx project. `CallSuper.kt`, `androidx-main` branch.
   https://raw.githubusercontent.com/androidx/androidx/androidx-main/annotation/annotation/src/commonMain/kotlin/androidx/annotation/CallSuper.kt
   Verified 2026-08-02. Source of the `@CallSuper` annotation's documented
   purpose, dimensions 8 and 9.
8. Microsoft. "Implement a Dispose method", .NET documentation.
   https://learn.microsoft.com/en-us/dotnet/standard/garbage-collection/implementing-dispose
   Verified 2026-08-02. Source of the .NET dispose-pattern production use and
   its documented `base.Dispose(disposing)` requirement, dimensions 8 and 9.
9. pylint-dev project. `class_checker.py`, `main` branch, message definition
   for `super-init-not-called` (W0231).
   https://raw.githubusercontent.com/pylint-dev/pylint/main/pylint/checkers/classes/class_checker.py
   Verified 2026-08-02. Source of the Pylint constructor-chain check cited in
   dimensions 8, 14, and the Code examples section.
10. JetBrains. Kotlin documentation, "Inheritance".
    https://kotlinlang.org/docs/inheritance.html
    Verified 2026-08-02. Source of the `open` keyword and explicit `super`
    call requirement cited in dimension 8.
