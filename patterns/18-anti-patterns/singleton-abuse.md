---
name: Singleton Abuse
slug: singleton-abuse
family: 18-anti-patterns
category: Anti-Pattern
aliases: [Singletonitis, Singleton Overuse, Global State via Singleton, Static Everything]
first_described: "Emergent practitioner critique, mid-2000s; earliest citable disowning by Gamma 2009"
maturity: canonical
related: [singleton, monostate, service-locator, dependency-injection, god-object, global-variable]
incompatible_with: [dependency-injection, single-responsibility-principle]
verified: 2026-08-02
---

# Singleton Abuse

## 1. Name, aliases, and lineage

The name used in this entry is Singleton Abuse, chosen to separate a specific
failure of practice from the Singleton pattern itself, which is catalogued
separately in this repository (see the `singleton` entry) as one of the
five creational patterns in Erich Gamma, Richard Helm, Ralph Johnson, and
John Vlissides, *Design Patterns. Elements of Reusable Object-Oriented
Software*, Addison-Wesley, 1994, chapter 3, Creational Patterns, Singleton.
Singleton Abuse is not a rename of that pattern. It is the anti-pattern that
appears when a team treats "make it a Singleton" as the default answer to
"how do I share this," rather than as a deliberate, narrow choice made after
weighing the pattern's cost. The GoF book itself never recommends this
default. The abuse is a practice that grew up around the pattern, mostly in
the fifteen years after the book shipped, as static-accessor singletons
became the easiest thing to type in Java, C++, and later C# codebases.

The most common informal alias is Singletonitis, used in code review and
conference talk shorthand to describe a codebase where singletons have
spread past the handful of genuinely stateless, environment-wide facilities
that justify one, into loggers, caches, configuration objects, database
connection managers, and application state, each reachable from anywhere by
naming the class. The suffix mirrors medical naming for an inflammatory
condition, and the metaphor is doing real work. it names a symptom that
compounds over time rather than a single bad line of code. Global State via
Singleton and Static Everything are used less consistently, mostly by
authors distinguishing the language-idiomatic instance of the disease. C++
and Java shops that say Singleton Abuse, C-family shops with heavy static
method usage that say Static Everything for the same underlying mistake
without ever writing a class that implements the classic GoF shape.

The clearest citable moment in the pattern's history where the pattern's own
authors distanced themselves from its casual use is the 2009 InformIT
interview *Design Patterns 15 Years Later. An Interview with Erich Gamma,
Richard Helm, and Ralph Johnson*, in which Gamma, asked which pattern from
the original catalog he would remove, answers "I'm in favor of dropping
Singleton. Its use is almost always a design smell"
([InformIT, verified 2026-08-02](https://www.informit.com/articles/article.aspx?p=1404056)).
That statement is about the pattern's habitual overuse in practice, not about
its structural correctness as a solution to the narrow problem it was
designed for, and this entry treats it as the earliest strong, citable
signal that the pattern's own inventors recognized the abuse as widespread
enough to regret cataloguing it without a stronger warning label.

Two independent practitioner essays predate that interview and are commonly
cited as the moment the abuse pattern got a name outside academic circles.
Steve Yegge published *Singleton Considered Stupid* on September 3, 2004,
arguing that singletons function as "a lifeline for people who didn't
understand" object-oriented design, letting procedural thinking hide inside
an apparently object-oriented shape, and that Singleton-held resources such
as database connections tend to stay open for the life of the process
because "nobody is going to call you and say 'nobody's going to be using you
for a while'"
([Steve Yegge, Singleton Considered Stupid, September 3, 2004, verified 2026-08-02](https://sites.google.com/site/steveyegge2/singleton-considered-stupid)).
Brian Button published *Why Singletons Are Evil* on May 25, 2004, focused on
the same coupling and testability concerns from a Microsoft-community
perspective. Misko Hevery's Google Testing Blog post *Root Cause of
Singletons*, published August 27, 2008, reframes the whole critique around
one root cause. a Singleton is a disguised global variable, and the actual
defect is that its callers acquire a dependency without declaring it in
their own interface, which is what makes the code hard to test and hard to
reason about in isolation
([Misko Hevery, Root Cause of Singletons, Google Testing Blog, August 27, 2008, verified 2026-08-02](https://testing.googleblog.com/2008/08/root-cause-of-singletons.html)).
This entry treats Hevery's framing, the hidden-dependency framing rather
than the one-instance framing, as the most useful lens for diagnosing
Singleton Abuse, because it is the framing that explains why some singletons
are harmless and others are load-bearing technical debt.

## 2. Problem and context

A codebase reaches for Singleton Abuse in a specific, recognizable moment. a
developer needs to share one piece of state, or one expensive resource,
across several parts of the code that were not designed together, or were
not designed with an explicit way to pass that state between them. Threading
it through every constructor and every function signature that might
eventually need it looks like needless ceremony in the moment, especially
early in a project when the call graph is shallow and the team is small.
Wrapping the shared thing in a class with a private constructor and a static
`getInstance` accessor solves the immediate problem in minutes. any code,
anywhere in the program, can now reach the shared thing by naming the class,
with no change to any intervening function signature.

The context in which this becomes an anti-pattern rather than a reasonable
shortcut is growth. the codebase adds features, the call graph deepens, and
the team grows past the point where every engineer holds the full set of
hidden global dependencies in their head. A function's signature stops being
a reliable description of what it needs to run correctly, because some of
its real inputs arrive through a static accessor rather than a parameter. A
second engineer, reading that function in isolation to understand or test
it, cannot tell from the signature that it depends on the current state of
three other singletons. The anti-pattern is not that a shared instance
exists. many programs genuinely have exactly one clock, one hardware device,
one process-wide logger sink. The anti-pattern is reaching for the same
mechanism, a static globally reachable accessor, for things that are shared
by convenience rather than by necessity, and letting that habit compound
until most of a program's real state lives behind static accessors instead
of in an explicit, traceable object graph.

This differs from Global Variable in degree more than in kind. a bare global
variable is at least visible as a variable declaration at file or module
scope, and most static analysis tools flag new ones easily. A singleton
accessor looks, at every call site, like an ordinary method call returning
an ordinary object, which is precisely why it spreads further before anyone
notices the program has accumulated a large, invisible web of shared mutable
state.

## 3. Forces

The dominant force pulling toward Singleton Abuse is convenience under time
pressure. threading a dependency explicitly through every intervening layer
costs real, visible effort right now, while the cost of a hidden dependency
is deferred, diffuse, and paid by whoever later tries to test, parallelize,
or reconfigure the code, often a different engineer on a different day. This
asymmetry, an immediate small cost against a large deferred cost paid by
someone else, is present in almost every anti-pattern in this family and is
unusually strong here because the deferred cost does not show up as a
runtime bug. it shows up as friction in testing and in onboarding, which
rarely gets attributed back to its actual cause.

A second force is a genuine, correct instinct. some things really are
singular in the running process, and passing a reference to the one and
only logger sink, or the one and only hardware clock, through every function
signature that touches it is legitimate ceremony that most teams correctly
avoid. The problem is that this correct instinct does not scale as a
heuristic, because the accessor mechanism looks identical whether the thing
behind it is genuinely singular in the domain, or merely happens to be
implemented as a single instance today for reasons of current convenience.

A third force is testability, and it pulls directly against the first two.
Unit tests need to construct a system under test with a known, controlled
set of inputs, then observe a known, controlled set of outputs. A function
that silently pulls part of its behavior from a process-wide static
accessor cannot be isolated this way without either resetting global state
between tests, which introduces test-order coupling and flaky failures when
tests run in a different order or in parallel, or subclassing and overriding
the accessor, which most languages make awkward for a class that hard-codes
its own construction. Hevery's framing names this directly. the accessor
hides a real dependency from the class's own interface, and a hidden
dependency is, by definition, a dependency a test cannot substitute without
extra machinery
([Hevery, Root Cause of Singletons, verified 2026-08-02](https://testing.googleblog.com/2008/08/root-cause-of-singletons.html)).

A fourth force is concurrency safety, in the opposite direction from what
intuition suggests. a shared mutable singleton looks safer than passing
copies of data around, because there is exactly one copy of the truth. In a
multithreaded or multi-request server process this is precisely backward. a
single mutable instance reachable from every request handler is a shared
resource that every concurrent caller can mutate, and making it safe under
concurrent access requires either synchronization, which serializes access
and becomes a throughput bottleneck as load grows, or careful,
easy-to-get-wrong lock-free design. The historical double-checked locking
bug in Java, where an optimizing compiler or a multiprocessor's memory model
could let a reader thread observe a partially constructed singleton,
required an explicit, widely circulated correction from a group of
concurrency experts including Bill Pugh, Doug Lea, David Bacon, and Joshua
Bloch before the community converged on a version that was actually correct
under the Java Memory Model
([Bacon, Bloch, Click, Lea, Pugh, et al., The "Double-Checked Locking is
Broken" Declaration, University of Maryland, verified 2026-08-02](https://www.cs.umd.edu/~pugh/java/memoryModel/DoubleCheckedLocking.html)).

## 4. Applicability and non-applicability

This is an anti-pattern entry, so the applicability question is really "when
does the fix apply," and the answer is that Singleton Abuse's fix,
replacing hidden static access with explicit passed-in dependencies,
applies whenever a piece of state or a shared resource is currently
reachable through a static accessor, and any of the following hold. the
class using it needs to be unit tested in isolation, the class using it
needs to run with a different configuration in a different test or a
different tenant of the same process, the shared thing is mutable and
touched from more than one thread or one request path, or the codebase has
more than a small handful of these accessors already and a new engineer
cannot enumerate a class's real dependencies from its constructor signature.

The non-applicability list is where this entry earns its keep, because
treating every static accessor as automatically wrong produces the opposite
failure. ceremony without benefit, and a codebase full of dependency
injection wiring for things that were never going to vary. Do not apply the
fix, or do not treat the current design as Singleton Abuse, in these cases.

- **The shared thing is genuinely immutable and process-wide by the domain's
  own rules**, not by current convenience. `java.lang.Runtime`, documented
  as having exactly one instance per running Java application, obtained
  through the static `getRuntime` accessor, because there genuinely is one
  operating system process backing the JVM, and no test double is ever going
  to substitute a second one meaningfully
  ([Oracle, Runtime (Java SE 8), verified 2026-08-02](https://docs.oracle.com/javase/8/docs/api/java/lang/Runtime.html)).
- **The instance is created once at process startup, treated as read-only
  configuration thereafter, and injected explicitly into whatever needs
  it**, rather than pulled through a static accessor at arbitrary call
  sites. This is dependency injection with singleton lifetime, and it does
  not carry the hidden-dependency defect this entry is about, because the
  dependency is still declared in the receiving class's constructor. Spring
  Framework's default singleton bean scope is exactly this shape, one
  instance per bean definition per container, created and owned by the
  container and handed to callers through constructor injection, which the
  Spring reference documentation is explicit about distinguishing from the
  GoF pattern. "Spring's concept of a singleton bean differs from the
  singleton pattern as defined in the Gang of Four (GoF) patterns book...
  The scope of the Spring singleton is best described as being per-container
  and per-bean"
  ([Spring Framework Reference, Bean Scopes, verified 2026-08-02](https://docs.spring.io/spring-framework/reference/core/beans/factory-scopes.html)).
- **The class is a small, leaf utility with no state and no side effects**,
  where a static accessor and an injected instance are behaviorally
  identical because there is nothing to substitute in a test. A pure math
  or string-formatting helper gains nothing from injection and loses
  nothing from a static call.
- **The program is a short-lived script or a single-purpose CLI tool** with
  no meaningful test suite and no plan for concurrent or multi-configuration
  execution, where the deferred cost this entry describes will never
  actually come due before the program is retired.
- **The codebase deliberately favors a small number of well-known, narrowly
  scoped facilities** (one logging sink, one metrics registry) over
  injecting them everywhere, and the team can and does enumerate every such
  facility, keeping the list small enough that it is common knowledge rather
  than a hidden surprise. The failure mode this entry describes is
  proliferation past a small, known set, not the existence of the set
  itself.

## 5. Structure

Singleton Abuse is a shape that appears at the scale of a codebase, not at
the scale of one class, so its structure is best described as a growth
pattern rather than a class diagram.

- **The seed singleton.** One class, implemented with a private constructor
  and a static accessor, created to solve one specific sharing problem, most
  often configuration, logging, or a database or cache connection.
- **The accreting responsibilities.** Over time, unrelated state that
  happens to be convenient to reach from the same places gets added to the
  seed singleton's instance fields, because the accessor is already
  available everywhere and adding a field is cheaper than creating a second
  shared facility. The seed singleton begins to resemble a God Object,
  sharing that anti-pattern's failure mode of accreted, unrelated
  responsibility, but reached through a static accessor rather than through
  an object graph.
- **The dependent chain.** A second singleton is introduced that, in its own
  constructor or initialization, reaches for the first singleton through its
  static accessor rather than receiving it as a parameter. This creates an
  implicit initialization order dependency between two classes that appear,
  from their public interfaces, to be unrelated.
- **The silent caller.** Ordinary business logic classes, scattered
  throughout the codebase, call one or more singleton accessors directly
  inside their methods, rather than receiving the shared thing through their
  own constructor. These are the participants whose signatures lie about
  their real dependencies.
- **The test rig casualty.** Test code, attempting to exercise a silent
  caller in isolation, discovers it cannot construct a clean, controlled
  version of the singleton's state without either a global reset hook added
  specifically for tests, or reflection-based hacks to reach a private
  constructor, both of which are themselves symptoms rather than fixes.

## 6. ASCII structure diagram

```
  Healthy dependency graph              Singleton Abuse growth pattern

  +----------------+                    +------------------------+
  |  OrderService   |                    |   ConfigSingleton      |
  |  ctor(logger,   |                    |   .getInstance()       |<-------+
  |       config,   |                    |   [config, cache,      |        |
  |       cache)    |                    |    db pool, user id,   |        |
  +---+----+----+---+                    |    feature flags ...]  |        |
      |    |    |                        +------------+-----------+        |
      v    v    v                                     ^                    |
  +------+ +----+ +-----+                              |  reads via         |
  |Logger| |Cfg | |Cache|                 +------------+------------+       |
  +------+ +----+ +-----+                 |    CacheSingleton        |      |
                                          |    .getInstance()        |------+
  Every real dependency is                +------------+-------------+
  visible in the constructor.                          ^ reads via
  A test passes fakes for all                           |
  three without touching any             +--------------+---------------+
  global or static state.                |  OrderService                |
                                          |  ctor()  <- no declared deps  |
                                          |  method calls ConfigSingleton |
                                          |  .getInstance() and           |
                                          |  CacheSingleton.getInstance() |
                                          |  from inside method bodies    |
                                          +--------------------------------+

                                          A test of OrderService cannot
                                          isolate it from either singleton
                                          without a global reset, because
                                          its constructor signature does
                                          not name what it actually needs.
```

## 7. Dynamics

The runtime dynamics of Singleton Abuse are most visible during test
execution and during concurrent request handling, which is where the
static-time convenience turns into a runtime defect.

```
  Test suite run, order-dependent failure caused by shared singleton state

  TestRunner        TestA                  ConfigSingleton         TestB
     |                |                          |                   |
     |--- run TestA -->|                          |                   |
     |                |--- getInstance() -------->|                   |
     |                |    (lazily creates,       |                   |
     |                |     default config)       |                   |
     |                |--- setFeatureFlag(X, on)->|                   |
     |                |    (mutates shared        |                   |
     |                |     instance state)        |                   |
     |                |<---- assertions pass -----|                   |
     |<--- TestA OK ---|                          |                   |
     |                |                          |                   |
     |--- run TestB ------------------------------------------------->|
     |                |                          |<--- getInstance() -|
     |                |                          |    (same instance, |
     |                |                          |     flag X still   |
     |                |                          |     on from TestA) |
     |                |                          |----assumes flag----|
     |                |                          |    off, fails ---->|
     |<------------------------- TestB FAIL, order-dependent -------->|

  Running TestB alone passes. Running the suite in a different order,
  or in parallel, changes the outcome, because the singleton's mutable
  state is not reset between tests and no test declares it as a
  dependency it owns and controls.
```

```
  Concurrent request handling, shared mutable singleton as a bottleneck

  RequestA        RequestB        CacheSingleton (single mutable instance)
     |                |                       |
     |-- get(key) --->|                       |
     |----------------+---- get(key) -------->|  (acquires lock)
     |                |---- get(key) --------->|  (blocks on lock)
     |<--------------- value --------------------|  (releases lock)
     |                |<---------- value ---------|  (acquires, returns)
     |                |                       |

  Every concurrent caller serializes on the one shared instance's lock.
  Throughput under load is bounded by how fast one lock can be acquired
  and released, not by how many CPU cores are available, which is the
  opposite of what a stateless, per-request or injected-per-scope design
  would give a multi-core server.
```

## 8. Implementation variants

Singleton Abuse takes a different concrete shape in each language and
platform, though the underlying mistake, a hidden, statically reachable,
mutable dependency, is the same in every variant.

- **Java and C# static accessor variant.** A class with a private
  constructor, a static field holding the one instance, and a public static
  `getInstance` or `Instance` method. This is the canonical shape most
  developers picture, and it is the shape the double-checked locking
  correctness bug historically attached to, when teams tried to make lazy
  initialization thread-safe without paying for a lock on every call
  ([Double-Checked Locking is Broken Declaration, verified 2026-08-02](https://www.cs.umd.edu/~pugh/java/memoryModel/DoubleCheckedLocking.html)).
- **Static class or module-level state variant, common in Python and
  JavaScript.** No class or accessor method at all. module-level mutable
  variables that every importer of the module shares implicitly, because
  the language's module system already guarantees one instance of the
  module's top-level state per process. This is functionally identical to
  the class-based variant but is easy to miss in review because it has no
  `getInstance` call to search for.
- **Android Context or Application-held singleton variant.** A singleton
  that, at construction, is handed a reference to an Android `Activity` or
  its `Context`, and holds that reference past the point where the
  activity's own lifecycle would normally allow it to be garbage collected.
  Android's own performance guidance names this class of bug directly.
  "memory leaks... usually caused by holding onto object references in
  static member variables," and recommends dependency injection frameworks
  such as Hilt to scope objects to the correct lifecycle instead
  ([Android Developers, Manage your app's memory, verified 2026-08-02](https://developer.android.com/topic/performance/memory)).
- **Dependency injection container misused as a service locator variant.**
  A team adopts a DI container correctly for construction, then, instead of
  injecting dependencies through constructors, calls the container's
  resolve or `getBean` method directly from inside business logic at
  arbitrary points. This looks like it solves the hidden-dependency
  criticism because a container is involved, but it recreates the exact
  same defect. the calling class's signature still does not declare what it
  needs, and Martin Fowler's discussion of this exact confusion, framed
  around the Service Locator pattern rather than Singleton by name, notes
  the common objection that such locators "aren't testable because you
  can't substitute implementations for them," a complaint that only
  dissolves when the locator itself is made explicitly injectable and
  swappable rather than reached through a global static
  ([Martin Fowler, Inversion of Control Containers and the Dependency
  Injection pattern, verified 2026-08-02](https://martinfowler.com/articles/injection.html)).
- **Enum singleton variant, present in Java as the recommended
  implementation of the pattern itself when a single instance is truly
  warranted.** This variant is included here because it marks the boundary
  of the anti-pattern rather than an instance of it. an enum-backed
  singleton is serialization-safe and immune to reflection-based
  re-instantiation, which solves the pattern's known correctness pitfalls,
  but it does nothing to address the hidden-dependency criticism, so an enum
  singleton reached by static accessor from deep inside business logic is
  exactly as much an instance of Singleton Abuse as a hand-rolled one.

## 9. Known production uses

Framing this dimension for an anti-pattern means naming real, sourced cases
where the shape appeared and its cost was documented, distinct from
dimension 4's legitimate uses of a genuine single shared instance.

- **Android applications holding `Context` in static fields.** Google's own
  Android performance documentation identifies this as a named, common
  cause of memory leaks in shipped apps, severe enough that the platform's
  official architecture guidance now steers new code toward Hilt-based
  dependency injection specifically to avoid it
  ([Android Developers, Manage your app's memory, verified 2026-08-02](https://developer.android.com/topic/performance/memory)).
- **Early-2000s Java enterprise codebases relying on static singleton
  accessors for database connection management**, the specific case Steve
  Yegge's 2004 essay uses as its running example, where a singleton holding
  a database connection stays open for the process's lifetime because
  nothing in the design forces or even permits an explicit release, since no
  caller owns a reference it can relinquish
  ([Yegge, Singleton Considered Stupid, verified 2026-08-02](https://sites.google.com/site/steveyegge2/singleton-considered-stupid)).
- **Google's internal Java codebases in the mid-2000s**, cited directly by
  Misko Hevery, then a Google engineer building the internal testability
  guidance that later became the public Google Testing Blog and the Guice
  dependency injection framework's design rationale, as the source of the
  Root Cause of Singletons argument. the post is explicitly framed around
  patterns Hevery observed causing real, repeated testing pain across many
  engineers' code at Google, not a hypothetical
  ([Hevery, Root Cause of Singletons, verified 2026-08-02](https://testing.googleblog.com/2008/08/root-cause-of-singletons.html)).

## 10. Consequences

Positive consequences, present in the moment the abuse pattern is chosen,
before its cost accrues.

- Immediate, low-friction sharing of state or a resource across code that
  was not designed with an explicit channel to pass it.
- No change required to any existing function or constructor signature
  along the call path, which makes the change feel local even though its
  effect is global.
- Familiar to nearly every engineer regardless of background, since the
  static-accessor shape is one of the first patterns most developers learn,
  correctly or not, as "how you share one thing in object-oriented code."

Negative consequences, which accrue as the codebase and team grow.

- Class signatures stop accurately describing a class's real dependencies,
  which is the root cause Hevery names directly, and which cascades into
  every other negative consequence below
  ([Hevery, Root Cause of Singletons, verified 2026-08-02](https://testing.googleblog.com/2008/08/root-cause-of-singletons.html)).
- Unit tests either cannot isolate the class under test from global state,
  or require a global reset mechanism added purely for testing, which
  itself becomes a maintenance burden and a source of order-dependent test
  flakiness.
- Concurrent access to mutable singleton state requires synchronization,
  which bounds throughput and, if implemented incorrectly, as
  double-checked locking historically was before the Java Memory Model was
  clarified, introduces subtle correctness bugs that surface only under
  specific hardware or compiler conditions
  ([Double-Checked Locking is Broken Declaration, verified 2026-08-02](https://www.cs.umd.edu/~pugh/java/memoryModel/DoubleCheckedLocking.html)).
- A program cannot run two independent configurations of the same
  supposedly-singular facility in one process, which blocks multi-tenancy,
  blocks running an in-process integration test alongside the real
  application, and blocks any feature that later turns out to genuinely
  need more than one instance.
- Resources acquired by a singleton and never explicitly released tend to
  live for the process's entire lifetime, because no caller holds a
  reference it can use to signal it is done, which is the specific
  complaint Yegge raises about database connections held by singletons
  ([Yegge, Singleton Considered Stupid, verified 2026-08-02](https://sites.google.com/site/steveyegge2/singleton-considered-stupid)).
- On platforms with an explicit component lifecycle, most visibly Android,
  a singleton that holds a reference to a shorter-lived component prevents
  the garbage collector from freeing that component, producing a memory
  leak that grows with every activity or screen transition until the
  process is killed
  ([Android Developers, Manage your app's memory, verified 2026-08-02](https://developer.android.com/topic/performance/memory)).

## 11. Failure modes and misuse

Presented as symptom, cause, fix triples, so the entry is diagnostic and not
only descriptive. Judgement note. the specific symptom wording below is
drawn from engineering practice rather than a single citable source, and is
labeled as such per the judgement-versus-sourced-claim rule this repository
follows.

- **Symptom.** A test suite passes reliably when run one file at a time, but
  fails intermittently, with different tests failing on different runs, when
  the full suite runs together or in parallel.
  **Cause.** One or more singletons carry mutable state that is not reset
  between tests, so an earlier test's mutation leaks into a later test that
  assumes default state.
  **Fix.** Add an explicit reset or fresh-instance hook that the test rig
  calls between tests, then treat that hook's necessity as the signal that
  the underlying dependency should be constructor-injected and owned by the
  test rather than reached through a static accessor.

- **Symptom.** A new engineer, reading a class's constructor to understand
  what it needs to run, is later surprised in code review or in production
  to find the class also depends on the current state of an unrelated
  singleton, discovered only by reading every method body.
  **Cause.** The dependency is real but undeclared, reached through a static
  accessor from inside a method rather than received as a parameter.
  **Fix.** Move the singleton reference into the constructor as an explicit
  parameter, even if, for now, the only caller passes
  `Singleton.getInstance()` at the single real construction site. This
  makes the dependency visible in the type signature without requiring a
  full dependency injection framework in one step.

- **Symptom.** A feature request to run the application with two different
  configurations side by side, for a staging environment inside the same
  process as production traffic, or for a genuinely multi-tenant deployment,
  turns out to require a rewrite rather than a configuration change.
  **Cause.** A configuration or resource that is only conceptually singular
  per tenant or per environment was implemented as singular per process,
  because the static accessor mechanism does not naturally express
  per-scope instances.
  **Fix.** Replace the process-wide static accessor with a scoped instance,
  owned by whatever unit of work or request actually defines the scope, and
  pass it explicitly to the code that needs it, which is the shape Spring's
  singleton bean scope, per-container rather than per-classloader, was
  specifically designed to make possible
  ([Spring Framework Reference, Bean Scopes, verified 2026-08-02](https://docs.spring.io/spring-framework/reference/core/beans/factory-scopes.html)).

- **Symptom.** An Android app's memory usage climbs steadily as a user
  navigates between screens, and a memory profiler shows old `Activity`
  instances retained in memory well after the user has left them.
  **Cause.** A singleton constructed early in the app's life was handed a
  reference to an `Activity` or its `Context`, and holds that reference for
  the singleton's own lifetime, which outlives the activity.
  **Fix.** Pass the application-level `Context`, which genuinely lives as
  long as the process, rather than the activity-level `Context`, or, per
  current Android architecture guidance, replace the manual singleton with
  a Hilt-scoped dependency whose lifetime is tied explicitly to the correct
  Android component
  ([Android Developers, Manage your app's memory, verified 2026-08-02](https://developer.android.com/topic/performance/memory)).

- **Symptom.** Under production load, response latency degrades
  non-linearly as concurrent traffic increases, worse than the increase in
  traffic alone would predict, and a thread dump shows many request-handling
  threads blocked waiting on the same lock.
  **Cause.** A mutable singleton, accessed by every request handler, is
  protected by a single lock, so the program's effective concurrency for
  that resource is one, regardless of how many CPU cores or worker threads
  are available.
  **Fix.** Either make the shared state immutable and safely shareable
  without a lock, or partition it so that concurrent callers contend for
  smaller, independent locks, or, most directly, stop sharing it as process-
  wide mutable state and give each request or worker its own scoped
  instance where the domain allows it.

## 12. Trade-off matrix

Compared against the two most common named alternatives for sharing state or
a resource across a codebase, across the forces named in dimension 3.

| Force | Singleton Abuse (static accessor everywhere) | Dependency Injection (constructor-passed, singleton lifetime) | Service Locator (explicit, injectable locator) |
|---|---|---|---|
| Dependency visibility | Hidden. real dependencies do not appear in a class's constructor signature | Explicit. every dependency is a constructor parameter, visible at a glance | Partially hidden. the locator itself is visible, but what a class pulls from it is not, unless reviewed method by method |
| Unit test isolation | Poor without global reset hooks, which themselves add maintenance burden | Strong. tests construct the class with fakes or mocks for every dependency directly | Moderate. requires the locator to be swappable per test, which Fowler notes is achievable but is an extra design step most teams skip |
| Multiple configurations in one process | Effectively impossible without a rewrite, since the accessor is process-wide by construction | Native. each caller can be constructed with a different configured instance | Possible if the locator instance itself is scoped, uncommon in practice |
| Concurrency safety | Requires explicit synchronization on shared mutable state, bounding throughput | No inherent bottleneck. each caller can hold its own instance, or share an explicitly immutable one | Same profile as Singleton Abuse for whatever the locator hands out, unless the locator itself scopes per caller |
| Onboarding cost for a new engineer | High. undeclared dependencies must be discovered by reading method bodies | Low. constructor signature is a reliable map of what a class needs | Medium. the locator call sites must still be found and understood |
| Setup ceremony for a genuinely process-wide, immutable facility | Minimal. one accessor, no wiring | Higher. requires a DI container or manual wiring even where nothing will ever vary | Minimal, similar to Singleton Abuse, until the locator is asked to support test substitution |

## 13. Related and incompatible patterns

**Singleton (this repository's `singleton` entry).** Singleton Abuse is what
happens when the Singleton pattern is applied by default rather than by
deliberate, narrow choice. Every instance of Singleton Abuse uses the
Singleton pattern's mechanism, but not every use of the Singleton pattern is
an instance of the abuse. the distinction, per dimension 4 of this entry, is
whether the shared instance is genuinely singular in the domain and
explicitly injected, or merely convenient today and reached through a
hidden static accessor.

**Monostate.** A close structural cousin, where instead of one class
guaranteeing one instance, many instances of a class share state through
static fields, so every object looks like a normal instance but all objects
of that class secretly share the same underlying data. Monostate produces
the same hidden-dependency and testing defects as Singleton Abuse, through a
different mechanical route, and the two are often confused in casual
conversation because both present as "there is really only one of these,
somewhere."

**Service Locator.** A registry object that hands out dependencies on
request, looked up by type or by name. Service Locator can either solve or
recreate the Singleton Abuse defect depending entirely on whether the
locator itself is explicitly passed into the classes that use it, making
the dependency on the locator visible, or reached through a static
accessor, in which case it is Singleton Abuse wearing a different name.
Martin Fowler's discussion of this pattern is explicit that its testability
depends on this design choice rather than on the pattern's category
([Fowler, Inversion of Control Containers and the Dependency Injection
pattern, verified 2026-08-02](https://martinfowler.com/articles/injection.html)).

**Dependency Injection.** The primary refactoring target for code exhibiting
Singleton Abuse. converts a hidden static dependency into an explicit
constructor parameter, restoring the property that a class's signature
accurately describes what it needs.

**God Object.** A frequent companion pattern rather than a synonym. the seed
singleton described in dimension 5 tends to accrete unrelated
responsibilities over time in exactly the way a God Object does, the
difference being that a God Object is usually reached through an object
graph while a Singleton Abuse seed is reached through a static accessor from
anywhere in the program, which is a strictly worse discoverability profile
for the same underlying accretion problem.

**Global Variable.** The plainest ancestor of this anti-pattern. Singleton
Abuse is, functionally, a global variable dressed in object-oriented syntax,
and every criticism levied at global variables in structured and procedural
programming applies here, compounded by the fact that a class-based accessor
is harder to spot in review than a bare `global` declaration.

## 14. Refactoring path in and out

Introducing the underlying Singleton pattern deliberately, when dimension 4
genuinely applies, means writing the private constructor and static
accessor directly, as documented in this repository's `singleton` entry,
and stopping there. deliberately not letting a second, unrelated piece of
state join the same class later.

Removing Singleton Abuse from an existing codebase is done incrementally,
because a big-bang rewrite of every call site at once is rarely safe or
approved. the accepted path, following the shape used across most
dependency-injection migration guidance, proceeds in these steps.

1. **Introduce an interface or protocol for the singleton's public surface**,
   if one does not already exist, separate from the concrete class that
   currently implements the accessor. This is the seam a test double will
   later implement.
2. **Add a constructor parameter for the dependency to each class that
   currently calls the static accessor from inside a method**, while
   leaving the accessor itself in place for now. At the single real
   construction site, or sites, pass `Singleton.getInstance()` explicitly as
   the argument. This step alone, with zero behavior change, makes every
   affected class's real dependencies visible in its constructor signature,
   which is the single highest-value step in the whole migration and can be
   done class by class without coordinating a wider change.
3. **Replace method-body calls to the static accessor with references to the
   now-injected field.** Each class stops reaching for the shared instance
   itself and instead uses the one it was handed.
4. **Where dimension 4's non-applicability conditions genuinely do not
   apply**, retire the static accessor and private-constructor guarantee
   entirely, replacing it with construction owned by a composition root,
   a startup routine, or a dependency injection container's registration,
   with singleton lifetime scoped to the container rather than hard-coded
   into the class.
5. **Where the class genuinely needs a fresh instance per test, per
   request, or per tenant**, change its lifetime from singleton to scoped or
   transient in the container's registration, which is a configuration
   change rather than a code change once step 4 is complete, and is exactly
   the flexibility a hard-coded static accessor cannot offer without a
   rewrite.

Step 2 deserves emphasis. teams that stall on this refactoring almost always
stall because they attempt step 4 first, treating the migration as an
all-or-nothing removal of the singleton mechanism, which is a much larger
and riskier change than making dependencies visible while leaving the
underlying instance untouched.

## 15. Testing and verification

Code exhibiting Singleton Abuse is, definitionally, hard to unit test in
isolation, because the class under test's real inputs are not fully
represented by its constructor arguments. Three techniques are used in
practice, in increasing order of how much they actually fix versus merely
work around the underlying defect.

- **Global reset between tests.** The test rig calls a reset method on each
  relevant singleton before or after every test, returning it to a known
  default state. This restores test isolation without touching production
  code, but does not restore an accurate constructor signature, and does
  not help two tests that need to run the same class with genuinely
  different configurations concurrently within the same test process.
- **Reflection or bytecode manipulation to substitute a test double.**
  Frameworks in several languages allow a test to reach into a class's
  private static field and replace the held instance for the duration of a
  test. This is strictly a workaround. it is fragile across refactors,
  slower than direct construction, and signals clearly that the production
  code's design, not the test, is the actual defect.
- **Constructor injection, per the refactoring path in dimension 14.** Once
  a class receives its dependency as a constructor parameter, testing it is
  identical to testing any other class with an injected dependency. the test
  constructs the class under test with a hand-written fake, a mocking
  framework's mock, or a real instance configured for the test, with no
  reset hooks and no reflection required, and can run any number of such
  tests concurrently without interference, because each test's instance is
  independent by construction.

Verifying that a codebase has actually reduced its Singleton Abuse, rather
than merely added workaround tooling, is best done by measuring the second
technique's usage over time. a shrinking number of reflection-based or
global-reset-based test workarounds, alongside a growing proportion of
classes whose full dependency set is visible in their constructor, is a
direct, checkable signal of progress, independent of any subjective code
review judgment.

## 16. Observability signals

A running system suffering from Singleton Abuse tends to show a
recognizable cluster of signals, distinct from the test-time signals in
dimension 15.

- **Memory usage that grows monotonically over the life of a long-running
  process**, most diagnostic on platforms with an explicit component
  lifecycle such as Android, where a heap dump or memory profiler
  attributes retained memory to objects, most often `Activity` or `Context`
  instances, that the garbage collector should have already freed, held
  alive by a static reference
  ([Android Developers, Manage your app's memory, verified 2026-08-02](https://developer.android.com/topic/performance/memory)).
- **Latency under concurrent load that degrades faster than linearly with
  request volume**, visible in a percentile latency dashboard as the tail
  latency, p99 or p999, growing disproportionately compared to median
  latency as concurrency increases, with a thread or goroutine dump at peak
  load showing many workers blocked on the same lock or mutex guarding a
  single shared mutable instance.
- **A process that cannot be safely restarted with a different
  configuration without a full deployment**, observable operationally as a
  configuration change requiring a code deploy or a full process restart
  rather than a runtime reload, because the configuration lives inside a
  singleton initialized once at process startup with no reload path.
- **Log lines or traces that reference a shared resource, most often a
  database connection pool or a cache, by a name or identity that does not
  vary across otherwise-independent requests**, which is expected for a
  legitimately shared, immutable, injected singleton, but is a signal worth
  cross-checking when combined with the latency signal above, since it
  confirms the resource in question really is a single point of contention
  rather than merely a coincidence of naming.

## 17. Security and privacy implications

A mutable, globally reachable singleton widens the blast radius of any bug
or vulnerability that lets an attacker influence its state, because every
part of the program that reads from the singleton, including, in some cases,
code written or reviewed with no awareness that the singleton exists, is
affected by a change to it. Two concrete implications follow from this,
stated here as engineering judgment rather than as claims tied to a specific
sourced incident, per the judgement-versus-sourced-claim rule this
repository follows for dimensions of this kind.

- **A singleton that caches or holds authorization context, a current
  user's identity, permission set, or tenant, is a specific and dangerous
  variant of this anti-pattern in a multithreaded or multi-request server
  process.** If the singleton's state is set at the start of handling one
  request and read later during the same request without being explicitly
  scoped per request, a race condition or an incomplete reset between
  requests can leak one user's authorization context into another user's
  request, which is a privilege escalation or data exposure vulnerability
  rather than merely a correctness bug. The correct fix, per this entry's
  dimension 14, is to scope such state explicitly to the request or the
  unit of work, never to a process-wide singleton, and this is one of the
  strongest concrete arguments for treating request-scoped state as
  categorically different from process-scoped state rather than reaching
  for the same static-accessor mechanism for both.
- **A singleton holding credentials, API keys, or database connection
  strings in memory for the process's entire lifetime** widens the window
  during which a memory dump, a debugging tool attached to the running
  process, or a heap-inspection vulnerability could expose those
  credentials, compared to a design where the credential is scoped narrowly
  to the operation that needs it and discarded afterward. This is not a
  defect unique to Singleton Abuse. any long-lived in-memory secret carries
  this exposure. but the abuse pattern's tendency to accrete unrelated state
  into one long-lived instance, as described in dimension 5, increases the
  odds that a credential ends up held for longer than the operation that
  actually needed it strictly requires.

## 18. References

1. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides. *Design
   Patterns. Elements of Reusable Object-Oriented Software*. Addison-Wesley,
   1994. ISBN 0-201-63361-2. Chapter 3, Creational Patterns, Singleton.
   Source of the pattern this anti-pattern grows out of by overuse.
2. InformIT. *Design Patterns 15 Years Later. An Interview with Erich
   Gamma, Richard Helm, and Ralph Johnson*, 2009. Source of Gamma's direct
   statement recommending Singleton be dropped from the catalog.
   https://www.informit.com/articles/article.aspx?p=1404056 verified
   2026-08-02.
3. Steve Yegge. *Singleton Considered Stupid*, September 3, 2004. Source of
   the resource-lifetime and procedural-thinking-in-disguise criticisms.
   https://sites.google.com/site/steveyegge2/singleton-considered-stupid
   verified 2026-08-02.
4. Misko Hevery. *Root Cause of Singletons*, Google Testing Blog, August 27,
   2008. Source of the hidden-dependency framing used throughout this
   entry, and of the Google-internal production context cited in
   dimension 9.
   https://testing.googleblog.com/2008/08/root-cause-of-singletons.html
   verified 2026-08-02.
5. David F. Bacon, Joshua Bloch, Cliff Click, Doug Lea, Bill Pugh, and
   others. *"Double-Checked Locking is Broken" Declaration*, University of
   Maryland. Source of the memory-model correctness pitfall discussed in
   dimensions 3, 8, and 10.
   https://www.cs.umd.edu/~pugh/java/memoryModel/DoubleCheckedLocking.html
   verified 2026-08-02.
6. Oracle. *Runtime (Java SE 8)*, Java Platform, Standard Edition 8 API
   Specification. Source of the legitimate single-instance-per-process
   example in dimension 4.
   https://docs.oracle.com/javase/8/docs/api/java/lang/Runtime.html
   verified 2026-08-02.
7. Spring Framework Reference Documentation. *Bean Scopes*. Source of the
   Spring singleton bean scope distinction from the GoF pattern, cited in
   dimensions 4, 11, and 12.
   https://docs.spring.io/spring-framework/reference/core/beans/factory-scopes.html
   verified 2026-08-02.
8. Android Developers. *Manage your app's memory*, Android performance
   documentation. Source of the Context-in-singleton memory leak pattern
   cited in dimensions 8, 9, 11, and 16.
   https://developer.android.com/topic/performance/memory verified
   2026-08-02.
9. Martin Fowler. *Inversion of Control Containers and the Dependency
   Injection pattern*. Source of the Service Locator testability discussion
   cited in dimensions 8 and 13.
   https://martinfowler.com/articles/injection.html verified 2026-08-02.
10. This repository, `patterns/01-design-patterns-gof/singleton.md`. Companion entry
    covering the Singleton pattern itself, its structure, dynamics, and
    legitimate implementation variants, referenced throughout this entry
    rather than duplicated.

## Code examples

Three languages, each showing the abuse first, then the constructor-injected
fix from dimension 14, matched to a runnable check.

### TypeScript

```typescript
// The abuse. hidden dependency reached through a static accessor.
class ConfigSingleton {
  private static instance: ConfigSingleton;
  private settings: Record<string, string> = { env: "production" };
  private constructor() {}
  static getInstance(): ConfigSingleton {
    if (!ConfigSingleton.instance) {
      ConfigSingleton.instance = new ConfigSingleton();
    }
    return ConfigSingleton.instance;
  }
  get(key: string): string | undefined {
    return this.settings[key];
  }
  set(key: string, value: string): void {
    this.settings[key] = value;
  }
}

class ReportGenerator {
  // No declared dependency. the real input arrives inside the method.
  generate(): string {
    const env = ConfigSingleton.getInstance().get("env");
    return `report for ${env}`;
  }
}

// The fix. the dependency is explicit, so a test can substitute a fake
// with no reflection and no global reset between tests.
interface ConfigSource {
  get(key: string): string | undefined;
}

class ReportGeneratorFixed {
  constructor(private readonly config: ConfigSource) {}
  generate(): string {
    const env = this.config.get("env");
    return `report for ${env}`;
  }
}

class FakeConfig implements ConfigSource {
  constructor(private readonly values: Record<string, string>) {}
  get(key: string): string | undefined {
    return this.values[key];
  }
}

const before = new ReportGenerator();
console.log(before.generate());

const fixed = new ReportGeneratorFixed(new FakeConfig({ env: "test" }));
console.log(fixed.generate());
if (fixed.generate() !== "report for test") {
  throw new Error("constructor-injected fake was not honored");
}
console.log("TypeScript check passed");
```

Compiled and run with `npx tsc --outDir /tmp/ts-out singleton-abuse.ts &&
node /tmp/ts-out/singleton-abuse.js`. Output confirmed. `report for
production`, `report for test`, `TypeScript check passed`.

### Python

```python
"""Singleton Abuse and its constructor-injected fix, in Python."""

from __future__ import annotations
from typing import Protocol


class ConfigSingleton:
    """The abuse. module-level shared state reached from anywhere."""

    _instance: "ConfigSingleton | None" = None

    def __new__(cls) -> "ConfigSingleton":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._settings = {"env": "production"}
        return cls._instance

    def get(self, key: str) -> str | None:
        return self._settings.get(key)

    def set(self, key: str, value: str) -> None:
        self._settings[key] = value


class ReportGenerator:
    """No declared dependency. reaches the singleton from inside a method."""

    def generate(self) -> str:
        env = ConfigSingleton().get("env")
        return f"report for {env}"


class ConfigSource(Protocol):
    def get(self, key: str) -> str | None: ...


class ReportGeneratorFixed:
    """The fix. dependency is explicit and substitutable per instance."""

    def __init__(self, config: ConfigSource) -> None:
        self._config = config

    def generate(self) -> str:
        env = self._config.get("env")
        return f"report for {env}"


class FakeConfig:
    def __init__(self, values: dict[str, str]) -> None:
        self._values = values

    def get(self, key: str) -> str | None:
        return self._values.get(key)


if __name__ == "__main__":
    before = ReportGenerator()
    print(before.generate())

    fixed = ReportGeneratorFixed(FakeConfig({"env": "test"}))
    print(fixed.generate())
    assert fixed.generate() == "report for test", (
        "constructor-injected fake was not honored"
    )

    # Same class, two independent instances with different configuration,
    # running concurrently in the same process. impossible with the
    # process-wide singleton above without a rewrite.
    fixed_two = ReportGeneratorFixed(FakeConfig({"env": "staging"}))
    assert fixed.generate() == "report for test"
    assert fixed_two.generate() == "report for staging"

    print("Python check passed")
```

Run with `python3 singleton_abuse.py`. Output confirmed. `report for
production`, `report for test`, `Python check passed`.

### Rust

```rust
// Singleton Abuse and its constructor-injected fix, in Rust.
//
// Rust's ownership rules make the classic mutable-static-singleton shape
// require `unsafe` or a `Mutex` wrapped in `OnceLock`, which is itself a
// useful, language-enforced signal of the cost this entry describes. the
// compiler will not let the abuse compile without the programmer writing
// down, explicitly, that shared mutable global state needs synchronization.

use std::collections::HashMap;
use std::sync::{Mutex, OnceLock};

struct ConfigSingleton {
    settings: Mutex<HashMap<String, String>>,
}

fn config_singleton() -> &'static ConfigSingleton {
    static INSTANCE: OnceLock<ConfigSingleton> = OnceLock::new();
    INSTANCE.get_or_init(|| {
        let mut m = HashMap::new();
        m.insert("env".to_string(), "production".to_string());
        ConfigSingleton {
            settings: Mutex::new(m),
        }
    })
}

struct ReportGenerator;

impl ReportGenerator {
    // No declared dependency. reaches process-wide global state directly,
    // and must lock a mutex to do it, exactly the concurrency force
    // described in dimension 3.
    fn generate(&self) -> String {
        let cfg = config_singleton().settings.lock().unwrap();
        let env = cfg.get("env").cloned().unwrap_or_default();
        format!("report for {env}")
    }
}

trait ConfigSource {
    fn get(&self, key: &str) -> Option<String>;
}

struct FakeConfig {
    values: HashMap<String, String>,
}

impl ConfigSource for FakeConfig {
    fn get(&self, key: &str) -> Option<String> {
        self.values.get(key).cloned()
    }
}

struct ReportGeneratorFixed<'a> {
    config: &'a dyn ConfigSource,
}

impl<'a> ReportGeneratorFixed<'a> {
    fn new(config: &'a dyn ConfigSource) -> Self {
        Self { config }
    }

    fn generate(&self) -> String {
        let env = self.config.get("env").unwrap_or_default();
        format!("report for {env}")
    }
}

fn main() {
    let before = ReportGenerator;
    println!("{}", before.generate());

    let mut values = HashMap::new();
    values.insert("env".to_string(), "test".to_string());
    let fake = FakeConfig { values };
    let fixed = ReportGeneratorFixed::new(&fake);
    println!("{}", fixed.generate());
    assert_eq!(fixed.generate(), "report for test");

    println!("Rust check passed");
}
```

Compiled and run with `rustc singleton_abuse.rs -o /tmp/singleton_abuse &&
/tmp/singleton_abuse`. Output confirmed. `report for production`, `report
for test`, `Rust check passed`.

Java is omitted as a fourth language for this entry despite being the
platform most of the cited sources discuss, because no Java runtime was
available in the environment used to write this entry, and this repository
states plainly, per its own toolchain policy, when a sample could not be
compiled rather than silently implying it was. The double-checked locking
mechanics described in dimensions 3, 8, and 10 are Java-specific, and a
reader working in Java should treat the Declaration cited in reference 5 as
the authoritative source for that language's correct singleton
initialization idiom rather than relying on a sample from this entry.
