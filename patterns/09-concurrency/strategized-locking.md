---
name: Strategized Locking
slug: strategized-locking
family: 09-concurrency
category: Concurrency
aliases: [Pluggable Synchronization, Parameterized Locking Strategy, Policy-Based Locking]
first_described: "Schmidt 1999; Schmidt, Stal, Rohnert, Buschmann 2000"
maturity: canonical
related: [scoped-locking, thread-safe-interface, monitor-object, strategy, bridge, template-method, double-checked-locking]
incompatible_with: []
verified: 2026-08-14
---

# Strategized Locking

## 1. Name, aliases, and lineage

The canonical name is Strategized Locking. It was named and defined by Douglas
C. Schmidt in "Strategized Locking, Thread-safe Interface, and Scoped Locking.
Patterns and Idioms for Simplifying Multi-threaded C++ Components," a paper
that appeared in *C++ Report*, SIGS Publications, Volume 11, Number 9,
September 1999. The paper is listed on Schmidt's own publications page at
https://www.dre.vanderbilt.edu/~schmidt/patterns-ace.html (verified
2026-08-14), and the full text is hosted at
https://www.dre.vanderbilt.edu/~schmidt/PDF/locking-patterns.pdf (verified
2026-08-14, live and downloadable, confirmed by extracting the document's text
directly). Section 2 of that paper, titled "The Strategized Locking Pattern,"
opens with the pattern's own statement of intent, quoted verbatim from the
extracted text, "The Strategized Locking pattern strategizes a component's
synchronization to increase its flexibility and reusability without degrading
its performance or maintainability." The same paper introduces two companion
ideas in the same document. Thread-safe Interface, a pattern for avoiding
self-deadlock and redundant locking across intra-component method calls, and
Scoped Locking, a C++ idiom for tying a lock's lifetime to a stack-allocated
guard object's constructor and destructor. The three are presented as a family
because they solve adjacent problems in the same class of components, but they
are three distinct pieces of advice, not one pattern under three names.

The pattern was carried into the wider concurrency literature the following
year by Douglas C. Schmidt, Michael Stal, Hans Rohnert, and Frank Buschmann,
*Pattern-Oriented Software Architecture, Volume 2. Patterns for Concurrent and
Networked Objects*, Wiley, 2000, where Strategized Locking sits in the same
object-synchronization family as Scoped Locking, Thread-Safe Interface, and
Double-Checked Locking Optimization. The book's authorship, title, and
publication year are corroborated independently at
https://en.wikipedia.org/wiki/Pattern-Oriented_Software_Architecture (verified
2026-08-14). Because the two sources describe the same pattern with the same
name and the same worked example, this entry treats the 1999 paper as the
primary citation for the pattern's content, since its full text could be
retrieved and its wording quoted directly, and the 2000 book as the
corroborating secondary citation for the pattern's place in the broader POSA2
catalog.

Common aliases in circulation reflect the two families of programming
language that host this idea. In the generic-programming and template-heavy
C++ and Rust world, the pattern is often called Policy-Based Locking, an
extension of Andrei Alexandrescu's broader Policy-Based Design vocabulary,
where policies are compile-time-selected, interchangeable behaviors bound
through a template parameter, even though Schmidt's paper predates
Alexandrescu's 2001 book and uses the term "strategized" rather than "policy."
In the object-oriented and interface-driven world, Java, Go, and C++ code that
chooses the polymorphic variant, the same idea is described as Pluggable
Synchronization, because the mechanism is dependency injection of a lock
object through a constructor or field rather than a template parameter.
Neither alias is wrong. They name the same pattern implemented through the two
mechanisms a language offers for parametrizing behavior, generics and
polymorphism, and the paper itself presents both as equally valid
implementations of one pattern, a point made explicit in dimension 8 below.

A distinction worth drawing at the outset, because the family of names causes
real confusion. Strategized Locking is a decision about which lock type a
component uses, made pluggable so the same component compiles or configures
correctly whether it needs no locking, a spinlock, a recursive mutex, or a
readers-writer lock. It is not a decision about where to acquire and release
that lock inside a method body, that is Scoped Locking's job, and it is not a
decision about how to structure intra-component calls so that acquiring the
lock twice on one thread does not deadlock, that is Thread-safe Interface's
job. The three compose. Strategized Locking chooses the lock's type. Scoped
Locking governs the lock's lifetime once acquired. Thread-safe Interface
governs how many times, and from where, the lock is acquired within one call
chain.

## 2. Problem and context

A reusable component, a cache, a connection pool, a queue, a counter, a buffer
manager, is built once and deployed into more than one concurrency
environment. One deployment runs single-threaded and pays for correctness it
does not need if locking is hard-coded in. A second deployment runs with many
threads contending on the same instance and needs a real mutex. A third
deployment, if the component becomes popular, runs on a platform where a
readers-writer lock beats a plain mutex because reads vastly outnumber
writes, or where a recursive mutex is needed because the component's own
methods call each other. If the component's synchronization is written as a
single hard-coded lock type, embedded directly in the method bodies, then
supporting a new deployment target means either duplicating the entire class
with one line changed, which is exactly the kind of near-duplicate code that
rots the moment one copy gets a bug fix and the other does not, or adding a
runtime branch on a concurrency-mode flag inside every method, which pollutes
every method body with a conditional that has nothing to do with the
component's actual job.

The paper's own worked example is a memory-mapped file cache inside a
high-performance web server, described in Section 2.2 of the source paper, a
component that maps URL pathnames to memory-mapped files so that a cache hit
can be served without a `read` or `write` system call. The cache must run
efficiently on both single-threaded and multi-threaded operating systems, and
the naive approach the paper walks through first is exactly the duplication
problem above, `File_Cache_Thread_Mutex` and `File_Cache_ST` as two nearly
identical classes differing only in whether `find()` takes a
`Guard<Thread_Mutex>` at its top. The paper states the resulting maintenance
cost plainly, "maintaining multiple separate implementations of similar file
cache components can be tedious since future enhancements and fixes must be
updated consistently in each component implementation."

The context in which Strategized Locking is the right answer, rather than
merely one available answer, has three parts, matching the pattern's own
Context section (2.3) and Problem section (2.4) in the source paper.

- A single component's core logic, the part that has nothing to do with
  concurrency, is stable and shared across every deployment target. The
  variation is confined to what protects the component's mutable state, not
  to what the component does with that state.
- The set of viable lock types is known and small at the point the component
  is written, a null lock, a mutex, a recursive mutex, a readers-writer lock,
  a spinlock, occasionally a distributed lock, even though which of those a
  given deployment needs is not known until the component is configured or
  instantiated.
- Performance tuning matters enough that a runtime branch on every method
  call is unacceptable, or portability matters enough that a component must
  compile down to zero-overhead code on a platform with no threading support
  at all, which only a compile-time mechanism, a template parameter, a
  generic, a build-selected type alias, achieves.

## 3. Forces

*This dimension weighs which pressure dominates, which is judgement, not a
sourced fact, though the named forces themselves are drawn from the source
paper's own Problem section (2.4).*

- **Ease of performance tuning versus code duplication.** The paper names
  this force directly. "It should be straightforward to tune a component for
  particular concurrency use-cases. If the synchronization strategy is
  hard-coded, however, it is time-consuming to modify the component to
  support new, more efficient synchronization strategies." Strategized Locking
  resolves the tension by making the lock type a parameter rather than a
  hard-coded member, so tuning becomes a one-line instantiation change instead
  of a rewrite.
- **Maintainability versus version skew.** The paper's second named force,
  "New enhancements and bug fixes should be straightforward," is threatened
  precisely because duplicated classes drift. A fix applied to
  `File_Cache_Thread_Mutex` does not automatically reach `File_Cache_ST`.
  Strategizing collapses N deployment-specific classes into one class
  parameterized by lock type, so there is exactly one place to fix a bug.
- **Compile-time cost versus runtime flexibility.** The paper's own
  Implementation section is explicit that this is the central trade-off
  inside the pattern, not merely between the pattern and its absence. Use a
  parameterized type, a template, "when the locking strategy is known at
  compile-time," and use polymorphism "when the locking strategy is not known
  until run-time," with the stated cost being "the tradeoff... between the
  run-time performance of templates vs. the potential for run-time
  extensibility with polymorphism." A template resolves to a monomorphized,
  inlinable, zero-overhead call when the lock is a no-op. A virtual `Lockable`
  base class costs a vtable indirection on every acquire and release but lets
  the concrete lock type change after the binary is compiled, for instance
  read from a configuration file.
- **Obtrusiveness of the strategy in application code.** The paper's own
  Consequences section (2.10) names a genuine liability of the
  template-parameter form specifically. "If templates are used to parameterize
  locking aspects this will expose the locking strategies to application
  code. This design can be obtrusive, particularly for compilers that do not
  support templates efficiently." Every caller of a templated component must
  now spell out the lock type in the component's own type signature,
  `File_Cache<Thread_Mutex>`, which leaks an implementation concern into
  every call site unless it is hidden behind a `typedef` or type alias, as
  the paper's own resolved example does with `FILE_CACHE`.
- **Consistency of the plugged-in strategy versus per-call flexibility.**
  Strategized Locking binds one lock type to one component instance for the
  instance's entire lifetime. This favors predictability, a reader auditing
  the component knows exactly which lock it uses by reading its
  instantiation, over the flexibility of choosing a different lock per call,
  which the pattern deliberately does not offer, because a lock that changes
  identity between an acquire and its matching release is not a coherent lock
  at all.

## 4. Applicability and non-applicability

Reach for Strategized Locking when.

- A component's core algorithm is fixed and shared, but the component must
  run correctly and efficiently across more than one concurrency environment,
  single-threaded, thread-per-connection, thread-pool, single-writer,
  multi-writer, and duplicating the class per environment is already causing
  version skew, per the paper's own named force above.
- The library or framework author cannot know, at the point the component is
  written, which lock the eventual caller needs, because the caller's
  deployment context, embedded single-core firmware versus a sixty-four-core
  server, is unknowable to the library author.
- A no-op, zero-cost lock strategy for single-threaded builds is a real
  requirement, not a hypothetical one, so the abstraction must be capable of
  compiling away entirely on the fast path. This is the case the paper's own
  `Null_Mutex` class exists to serve.
- The set of candidate lock strategies is small, well-understood, and shares
  one narrow interface, most often a pair of methods named acquire and
  release, so
  strategizing does not require inventing a large abstraction the way a
  general-purpose plugin system would.

Do NOT reach for Strategized Locking when.

- The component has exactly one deployment target, ever, and no realistic
  plan to support a second one. Introducing a template parameter or an
  injected lock object for a component that will only ever run
  single-threaded, or only ever run behind one fixed mutex, adds an
  abstraction with no corresponding requirement, which is precisely the kind
  of speculative generality that costs more in reading effort than it ever
  returns. Write the concrete lock directly.
- The synchronization requirement is not "pick a lock type" but "coordinate
  access across an entire subsystem of unrelated components," where a single
  component-local lock, of whatever type, cannot express the needed
  invariant. That problem belongs to coarser patterns such as Monitor Object
  applied at the subsystem boundary, or to explicit distributed coordination,
  not to a locking strategy parameter on one class.
- The component's methods call each other internally and a non-recursive
  lock strategy is plugged in without also applying Thread-safe Interface.
  The source paper is explicit that this specific composition failure causes
  self-deadlock, illustrated with its own `find()` calling `bind()` example in
  Section 3.2, and Strategized Locking alone does nothing to prevent it.
- Overhead is genuinely zero-tolerance and even a monomorphized template
  instantiation's inlining boundary or a generic's dictionary-passing
  overhead, in languages without full monomorphization, is unacceptable. In
  that narrow case, write the one concrete lock type by hand and accept the
  duplication if a second deployment target ever appears, rather than paying
  an abstraction tax nobody asked for.
- The language has no honest mechanism for either compile-time
  parametrization or cheap runtime polymorphism over a narrow lock interface.
  A dynamically typed language without structural or duck typing, rare in
  practice, would force every "pluggable" lock through reflection, which
  defeats the pattern's own performance rationale.

## 5. Structure

The paper describes the pattern's structure implicitly through its worked
examples rather than a named UML diagram, so the participant list below names
the roles the paper's own code plays, using the paper's own class names where
one exists.

- **Component** (the paper's `File_Cache`). The reusable class whose core
  logic is stable across deployments. It holds one instance of the
  synchronization strategy as a private data member and calls that member's
  acquire and release operations to protect its own state. It never contains
  a branch on "which kind of lock am I."
- **Lock strategy interface** (the paper's implicit `acquire`/`release`
  signature, made explicit as the `Lockable` abstract base class in the
  polymorphic variant). The narrow contract every candidate lock type must
  satisfy. An operation that blocks or spins until exclusive, or shared,
  access is obtained, and a matching operation that releases it.
- **Concrete lock strategies** (the paper's `Thread_Mutex`, `Null_Mutex`, and
  the reader's own `RW_Lock`). Each is a small, independently testable class
  implementing the lock strategy interface. `Null_Mutex` is the degenerate,
  no-op strategy the pattern relies on for single-threaded deployments. The
  paper calls it "a surprisingly useful locking strategy" and notes its
  methods are "empty inlined functions that can be completely removed by
  optimizing compilers," an instance of the Null Object pattern applied
  specifically to locking.
- **Strategy binding mechanism.** Either a template, generic, parameter on
  the Component, resolved at compile time, or a constructor- or
  field-injected polymorphic reference to the lock strategy interface,
  resolved at load or configuration time. This is the one structural choice
  the pattern leaves fully open, and it is the axis dimension 8 explores.
- **Client / configurer.** The code that chooses which concrete lock strategy
  a particular Component instance receives, either by writing a type alias
  such as the paper's own `typedef File_Cache<Thread_Mutex> FILE_CACHE;` or
  by constructing and passing a concrete `Lockable` object.

## 6. ASCII structure diagram

```
Compile-time (parameterized-type) form
---------------------------------------

  +----------------------------+
  | Component<LOCK>            |
  | - lock_ : LOCK             |
  | + find(path), + bind(path) |
  +----------------------------+
  LOCK is a type parameter, bound at instantiation, resolved
  by the compiler, no vtable involved. method body acquires
  lock_, does the work, releases lock_.
            | instantiated with
      +-----+-----+-----+
      v     v     v
  +-----------+ +-------------+ +---------------+
  | Null Mutex| | Thread Mutex| | RW Lock       |
  | no-op     | | real mutex  | | readers/writer|
  +-----------+ +-------------+ +---------------+

Runtime (polymorphic) form
---------------------------

  +----------------------------+
  | Component                  |
  | - lock_ : Lockable&        |
  | + find(path), + bind(path) |
  +----------------------------+
            | holds a ref to
            v
  +------------------------+
  | <<interface>> Lockable |
  | + acquire()            |
  | + release()            |
  +------------------------+
            ^
            | implemented by
      +-----+-----+
      |           |
  +-----------------------------+
  | Thread_Mutex_Lockable       |
  | acquire() -> lock_.lock()   |
  | release() -> lock_.unlock() |
  +-----------------------------+

  +-----------------------+
  | Null_Mutex_Lockable   |
  | acquire() -> return 0 |
  | release() -> return 0 |
  +-----------------------+
```

## 7. Dynamics

The runtime behavior is identical in both forms, only the dispatch mechanism
differs. The sequence below shows a single call to a strategized method, using
the paper's own idiom of composing Scoped Locking, the `Guard` object, with
Strategized Locking, the `LOCK` type parameter or `Lockable` reference, which
is exactly how the paper's own resolved example is written.

```
  Client            Component<LOCK>          Guard<LOCK>         LOCK instance
    |                     |                       |                    |
    |  find(pathname)     |                       |                    |
    |-------------------->|                       |                    |
    |                     |  Guard<LOCK> g(lock_)  |                    |
    |                     |----------------------->|                    |
    |                     |                       |   lock() / acquire()
    |                     |                       |------------------->|
    |                     |                       |                    | (blocks until
    |                     |                       |                    |  strategy grants
    |                     |                       |                    |  access, or
    |                     |                       |                    |  returns instantly
    |                     |                       |                    |  if Null_Mutex)
    |                     |                       |<-------------------|
    |                     |   [critical section. read/mutate component state]
    |                     |                       |                    |
    |                     |  g destructor runs     |                    |
    |                     |  (scope exit, normal   |                    |
    |                     |  return or exception)  |                    |
    |                     |----------------------->|                    |
    |                     |                       |  unlock() / release()
    |                     |                       |------------------->|
    |                     |                       |                    |
    |<--------------------|                       |                    |
    |   return value       |                       |                    |
```

The instance being locked is transparent to the client at the point of the
call. `find(pathname)` reads identically whether `Component` was instantiated
with `Null_Mutex`, `Thread_Mutex`, or `RW_Lock`. All that changes is what
happens between the two arrows into the LOCK instance column, and for
`Null_Mutex` those two arrows compile away entirely, a fact confirmed by the
paper's own description of `Null_Mutex`'s methods as removable by an
optimizing compiler.

## 8. Implementation variants

*The mechanism descriptions below quote and paraphrase the paper's own
Implementation section (2.6). The language-specific idioms beyond C++ are this
entry's own extension, each with an independently verified production
example.*

- **Parameterized-type (generic/template) form.** Add a `LOCK` type parameter
  to the component and hold an instance of `LOCK` as a private member. This is
  the paper's recommended approach "when the locking strategy is known at
  compile-time," and it is the zero-overhead variant. A `Null_Mutex`
  instantiation inlines to nothing, and a real mutex instantiation costs
  exactly what that mutex costs, with no virtual dispatch tax. C++ templates,
  Rust generics with a trait bound, and Swift generics with a protocol
  constraint all express this variant natively. The cost is monomorphization,
  every distinct `LOCK` type produces a distinct compiled specialization of
  the component, which is a code-size trade the paper does not discuss but
  which is well documented as the standard cost of C++ and Rust generic
  instantiation.
- **Polymorphic (interface/virtual-dispatch) form.** Define an abstract lock
  interface, the paper's own `Lockable`, with pure virtual `acquire` and
  `release` methods, and hold a reference or pointer to that interface as a
  private member, supplied through the constructor. This is the paper's
  recommended approach "when the locking strategy is not known until
  run-time," for instance when a deployment reads its concurrency mode from a
  configuration file at process start rather than from source code. The
  paper's own construction is a textbook application of the Bridge pattern,
  cited in the paper as, "we apply the Bridge pattern to define a
  non-polymorphic interface class that holds a reference to the polymorphic
  Lockable." The non-polymorphic `Lock` wrapper class exists purely so
  that the polymorphic strategy can still be used as a stack-allocated value
  inside a `Guard<Lock>`, preserving Scoped Locking's RAII discipline even
  though the underlying strategy is chosen at runtime.
- **Structural / duck-typed form.** In a language with structural typing or
  duck typing rather than nominal interfaces, no explicit `Lockable` base
  class is required at all. Any object exposing the expected method names
  satisfies the strategy contract implicitly. Go's `sync.Mutex` and
  `sync.RWMutex` both satisfy a two-method `Locker` interface, `Lock()` and
  `Unlock()`, purely by having the right method set, with no explicit
  `implements` declaration, and Python's `threading.Lock` and
  `threading.RLock` are interchangeable inside code that only calls
  `.acquire()` and `.release()` for the identical reason. This form gets the
  polymorphic variant's runtime flexibility with less ceremony than an
  explicit abstract base class, at the cost of the contract being implicit
  and checked only at first use rather than at compile time.
- **Macro or conditional-typedef form.** For codebases predating generics or
  targeting a language without them, the strategy can be selected at build
  time through a preprocessor macro or a single centrally defined type alias
  that every component references, rather than through a per-component type
  parameter. This is exactly the mechanism the ACE framework uses in
  production, described under dimension 9 below. A build-time trait selects
  `ACE_MT_SYNCH` or `ACE_NULL_SYNCH`, and every ACE component that wants to be
  strategized simply uses the resulting `ACE_SYNCH_MUTEX` type alias, so the
  strategy is chosen once for the whole library rather than once per
  component instantiation. This trades per-component flexibility, every
  component in the build shares one strategy, for build-system simplicity.

Java is deliberately not given a fourth code sample in this entry beyond the
production reference in dimension 9, because the JVM has no zero-cost
generic-monomorphization mechanism, generics are erased, so Java's
`java.util.concurrent.locks.Lock` interface is a pure instance of the
polymorphic form already covered above and adds no third mechanism worth a
separate listing.

## 9. Known production uses

- **The ACE (Adaptive Communication Environment) network programming
  toolkit.** The source paper states directly, in its Known Uses section
  (2.8), "The Strategized Locking pattern is used extensively throughout the
  ACE OO network programming toolkit." This is independently confirmed in the
  toolkit's own current source. `ACE_TAO/ACE/ace/Synch_Traits.h`, in the
  actively maintained repository at
  https://github.com/DOCGroup/ACE_TAO/blob/master/ACE/ace/Synch_Traits.h
  (verified 2026-08-14), defines an `ACE_NULL_SYNCH` traits class providing
  no-op synchronization primitives and an `ACE_MT_SYNCH` traits class
  providing real thread-safe primitives, with the build conditionally
  defining `ACE_SYNCH` to one or the other based on whether `ACE_HAS_THREADS`
  is set. Every ACE component that wants a strategized lock refers to the
  resulting `ACE_SYNCH_MUTEX` alias rather than naming `ACE_Thread_Mutex` or
  a no-op type directly, exactly the macro-or-conditional-typedef variant
  described in dimension 8.
- **The Booch Components.** The same paper's Known Uses section states, "The
  Booch Components were one of the first C++ class libraries to parameterize
  locking strategizes with templates," citing reference [5] in the paper's own
  bibliography, Grady Booch, Michael Vilot, and others, the Booch Component
  library for reusable C++ data structures. This predates the paper's own
  formal naming of the pattern, which the paper itself acknowledges by citing
  it as prior art rather than as a use of the newly named pattern, making it
  the earliest documented instance of the technique the paper later names.
- **The `lock_api` Rust crate.** This crate, documented at
  https://docs.rs/lock_api/latest/lock_api/ (verified 2026-08-14), defines a
  generic `Mutex<R, T>` type where `R` is a type parameter constrained by a
  `RawMutex` trait, and the crate's own documentation states it "provides
  type-safe and fully-featured `Mutex` and `RwLock` types which wrap a simple
  raw mutex or rwlock type" so that "users [can] write code which is generic
  with regards to different lock implementations." The crate's own example
  builds a custom spinlock `RawMutex` implementation and exposes it as
  `pub type Spinlock<T> = lock_api::Mutex<RawSpinlock, T>`, which is the
  parameterized-type form of Strategized Locking applied at the ecosystem
  level. The widely used `parking_lot` crate is itself built on `lock_api`
  with its own `RawMutex` strategy plugged in.
- **`java.util.concurrent.locks.Lock` in the Java Standard Library.**
  Documented at
  https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/locks/Lock.html
  (verified 2026-08-14), the `Lock` interface's own Javadoc states that "Lock
  implementations provide more extensive locking operations than can be
  obtained using synchronized methods and statements," and the interface's
  documented implementing classes include `ReentrantLock` and both the
  read-side and write-side views of `ReentrantReadWriteLock`. Any Java class
  that depends on the `Lock` interface type rather than a concrete
  implementation, a common convention in code that accepts an injected lock
  through a constructor, is applying the polymorphic form of Strategized
  Locking, with the JVM's interface dispatch standing in for the paper's own
  `Lockable` abstract base class.

## 10. Consequences

*Positive and negative consequences below are largely a direct restatement of
the paper's own Section 2.10, plus this entry's own additional analysis where
marked as judgement.*

Positive.

- **Enhanced flexibility and performance tuning**, quoting the paper
  directly. "Because the synchronization aspects of components are
  strategized, it is straightforward to configure and tune a component for
  particular concurrency use-cases." Switching a deployment from a mutex to a
  readers-writer lock becomes a one-line type-alias change rather than a
  rewrite.
- **Decreased maintenance effort**, again quoting the paper. "It is
  straightforward to add enhancements and bug fixes to a component because
  there is only one implementation, rather than a separate implementation for
  each concurrency use-case. This centralization of concerns avoids
  version-skew."
- **Zero-cost single-threaded deployment.** Because `Null_Mutex`, or its
  equivalents in other languages, compiles to nothing under the
  parameterized-type form, a library can honestly claim it imposes no runtime
  overhead in a single-threaded build, a claim that would be false if
  synchronization were hard-coded with a runtime branch instead.
- **Testability of each lock strategy in isolation.** *(Judgement, not
  sourced.)* Because the lock strategies are small, independent classes
  satisfying a narrow contract, each one can be unit-tested for its own
  acquire and release semantics without needing the full component under
  test, which is not true when locking logic is interleaved directly into
  business-logic method bodies.

Negative.

- **Obtrusive locking in the template form**, quoting the paper's own stated
  liability. "If templates are used to parameterize locking aspects this will
  expose the locking strategies to application code. This design can be
  obtrusive, particularly for compilers that do not support templates
  efficiently." Without a hiding `typedef` or type alias, every call site
  must spell out the concrete lock type in the component's own type, which
  leaks a deployment concern into application code.
- **Virtual dispatch overhead in the polymorphic form.** *(Judgement.)* The
  Bridge-pattern indirection the paper's own polymorphic variant introduces
  costs at minimum one virtual call per acquire and one per release, which
  the paper implicitly acknowledges by recommending the template form
  specifically "when the locking strategy is known at compile-time," framing
  the polymorphic form as the deliberately slower, more flexible alternative
  rather than a free upgrade.
- **A wrong strategy is a silent correctness bug, not a compile error.**
  *(Judgement.)* Nothing in the pattern itself prevents a caller from
  instantiating a component with `Null_Mutex` in a context that is, in fact,
  multi-threaded. The type system enforces that the plugged-in type satisfies
  the narrow lock interface. It does not, and structurally cannot, enforce
  that the chosen strategy matches the actual concurrency of the deployment.
  This failure mode recurs frequently enough in practice that it is given its
  own entry in dimension 11.
- **Interacts badly with intra-component recursion unless paired with
  Thread-safe Interface.** As the paper's own worked example in Section 3.2
  shows explicitly, plugging in a non-recursive lock strategy into a
  component whose methods call each other reintroduces self-deadlock, a
  failure the pattern by itself does nothing to prevent.

## 11. Failure modes and misuse

- **Symptom.** A component that ran correctly for months suddenly deadlocks
  under moderate load, always inside a call chain where one public method
  calls another public method on the same object.
  **Cause.** The component was strategized with a non-recursive lock, the
  common default, `Thread_Mutex` in the paper's own example, `std::mutex` in
  C++, a plain `sync.Mutex` in Go, and one method acquires the lock via
  Scoped Locking, then calls a sibling method that tries to acquire the same
  non-recursive lock again on the same thread. This is precisely the failure
  the source paper walks through with its own `find()`/`bind()` example in
  Section 3.2. "the code will self-deadlock when the find method calls the
  bind method since bind reacquires the LOCK already held by find."
  **Fix.** Apply Thread-safe Interface alongside Strategized Locking.
  Separate the public, lock-acquiring interface methods from private,
  lock-free implementation methods, and have interface methods call
  implementation methods, never other interface methods, for any
  intra-component call chain. Only reach for a recursive mutex strategy as a
  stopgap, because recursive mutexes trade the deadlock for the second named
  liability below, unnecessary repeated-acquisition overhead, and they hide
  the design smell that made the recursion necessary in the first place.

- **Symptom.** A component performs correctly in unit tests, which run
  single-threaded, and then corrupts its own state or produces inconsistent
  reads in production, which runs multi-threaded, with no crash and no
  obvious stack trace pointing at the bug.
  **Cause.** The component was strategized with a no-op lock, `Null_Mutex`,
  `NullLock`, an empty `Locker` implementation, for a build or test
  configuration, and that same instantiation, or a copy-pasted one, was
  carried unmodified into a genuinely multi-threaded deployment. Because the
  no-op strategy satisfies the lock interface's type signature perfectly,
  nothing in the type system flags the mismatch. The component believes it is
  protected and is not.
  **Fix.** Never let the choice of no-op-versus-real strategy be implicit or
  inherited by copy-paste. Make the strategy choice an explicit,
  single-source-of-truth build or configuration decision, a feature flag, a
  build-time constant, a single centrally defined type alias as ACE's own
  `ACE_SYNCH_MUTEX` does, and add a runtime or CI assertion that fails loudly
  if a "single-threaded" build configuration is ever linked into a binary
  that also spawns worker threads.

- **Symptom.** A latency-sensitive hot path shows unexplained tail-latency
  spikes that correlate with contention, even though the component's own
  logic is short and the lock is held for only a handful of instructions.
  **Cause.** The polymorphic, virtual-dispatch, variant of Strategized
  Locking was used for a component on a genuinely hot path where the
  compile-time-known template variant would have sufficed. Every acquire and
  release now costs a virtual call in addition to the underlying lock
  operation, and under contention the extra indirection widens the window
  during which the lock is held, which under high concurrency compounds into
  measurable throughput loss.
  **Fix.** Reserve the polymorphic form for components whose lock strategy
  is genuinely unknown until runtime, per the paper's own recommendation in
  dimension 8. Where the strategy is in fact known at build or link time,
  even if it differs between build configurations, prefer the
  parameterized-type form and resolve the choice through a type alias chosen
  per build target, so the hot path pays zero indirection cost.

- **Symptom.** Adding a new lock strategy to an existing strategized
  component requires touching a surprisingly large number of files, defeating
  the pattern's own stated maintenance benefit.
  **Cause.** The lock strategy interface was designed too wide, exposing
  strategy-specific operations, a timeout parameter only some strategies
  support, an upgrade-from-read-to-write operation only readers-writer locks
  support, rather than the narrow acquire-and-release contract the pattern
  calls for. Every concrete strategy is now forced to implement operations it
  cannot meaningfully support, and every component using the wide interface
  couples itself to capabilities most strategies do not have.
  **Fix.** Keep the strategized interface to the smallest common contract
  every candidate lock genuinely shares, matching the paper's own two-method
  `acquire`/`release`, or `lock`/`unlock`, shape. Strategy-specific
  capabilities that only some lock types offer belong on a separate,
  narrower, optional interface that a component explicitly opts into, not on
  the base strategy contract every component depends on.

## 12. Trade-off matrix

| Force | Strategized Locking | Thread-Safe Interface | Monitor Object | Double-Checked Locking |
|---|---|---|---|---|
| What varies | The lock type plugged into one component | Which methods acquire the lock and how many times per call chain | Whether a whole object is synchronized as one unit with condition-variable waits built in | Whether a shared, expensive-to-construct object has already been initialized |
| Compile-time cost | Real, if templates or generics are used, monomorphization, code size | None beyond normal method dispatch | None beyond normal method dispatch | None |
| Runtime cost, best case | Zero, when a no-op strategy is plugged in and the compiler inlines it away | Small, one lock acquire per external call, none for internal calls | One lock acquire per public call, plus condition-variable overhead for waits | Near zero after first initialization, one atomic load |
| Coupling introduced | Every caller of a templated component must name a concrete lock type unless hidden behind an alias | None visible to callers, purely an internal method-splitting discipline | Callers see one coarse-grained object, internal structure of waits is hidden | Callers see one accessor, the flag and the guarded value are tightly coupled |
| Solves self-deadlock | No, by itself, must be composed with Thread-Safe Interface | Yes, that is its entire purpose | Yes, a monitor's own methods do not re-enter the same lock incorrectly by construction | Not applicable, it is not about intra-object recursion |
| Solves cross-platform, zero-threading builds | Yes, this is the pattern's primary motivating use case | No, orthogonal concern | No, a monitor always assumes a lock exists | No, orthogonal concern |
| Primary risk | A no-op or wrong strategy silently plugged into a concurrent deployment | Splitting interface and implementation methods correctly is easy to get subtly wrong | Coarse locking on the whole object can serialize unrelated operations that never conflict | On weakly ordered memory models, the check-then-init sequence is unsafe without explicit memory ordering, a well-documented historical bug class |

## 13. Related and incompatible patterns

- **Scoped Locking.** The pattern most tightly coupled to Strategized
  Locking, described in the same source paper. Scoped Locking governs when a
  strategized lock is acquired and released, tying its lifetime to a stack
  object's constructor and destructor, or, in Rust, an RAII guard's `Drop`.
  In practice the two are almost always used together, as the paper's own
  worked example does throughout. `Guard<LOCK> guard(lock_);` composes a
  Scoped Locking guard around whichever concrete `LOCK` Strategized Locking
  plugged into the component.
- **Thread-Safe Interface.** The companion pattern from the same source
  paper. Where Strategized Locking answers "which lock type," Thread-Safe
  Interface answers "which methods acquire it, and how many times per call
  chain," specifically to prevent the self-deadlock failure mode named in
  dimension 11. A component that uses Strategized Locking with a
  non-recursive strategy but skips Thread-Safe Interface is carrying a latent
  bug, not a complete application of the pattern family.
- **Strategy (Gang of Four).** Strategized Locking is a direct, named special
  case of the general Strategy pattern, applied specifically to the
  synchronization aspect of a component rather than to an arbitrary
  algorithm. Where GoF Strategy usually varies a business-logic algorithm,
  Strategized Locking varies a cross-cutting infrastructural concern, which is
  why it earns its own name in the concurrency literature rather than being
  described merely as "Strategy applied to locks."
- **Bridge (Gang of Four).** The source paper explicitly builds its
  polymorphic variant on Bridge, using a non-polymorphic `Lock` wrapper class
  that holds a reference to an abstract `Lockable` implementation, so that
  the polymorphic strategy can still be manipulated as a stack-allocated
  value by Scoped Locking's `Guard`. The composition exists specifically to
  let two orthogonal axes, lock lifetime management and lock strategy
  selection, vary independently.
- **Null Object.** The paper's own `Null_Mutex` is explicitly framed as an
  application of Null Object. "This class is an example of the Null Object
  pattern, which simplifies applications by defining a no-op placeholder." It
  is the strategy that makes single-threaded, zero-overhead deployments
  possible without a separate code path.
- **Template Method (Gang of Four).** Where a strategized component holds a
  lock as a data member that method bodies call at fixed points, a
  Template-Method-shaped component instead calls an overridable hook method
  at a fixed point in an algorithm's skeleton. The two are related in shape,
  both defer one aspect of behavior to a plugged-in participant, but Template
  Method varies through subclass overriding while Strategized Locking varies
  through composition, and Strategized Locking is specifically scoped to the
  synchronization aspect rather than to an arbitrary algorithm step.
- **Monitor Object.** Where Strategized Locking parametrizes which lock type
  a component uses while leaving the component's method-level locking
  discipline to the author, Monitor Object collapses the entire object into
  one implicit lock with built-in condition-variable waiting, offering no
  strategy parameter at all. The two are not incompatible, a Monitor Object's
  internal mutex could itself be strategized, but they answer different
  questions. Monitor Object answers "how do I make this whole object
  thread-safe with waiting," Strategized Locking answers "which lock type
  should whichever object needs one, use."
- **Incompatible with.** None. Strategized Locking is a narrow, composable
  decision about one component's lock type and does not structurally conflict
  with any other named pattern in this catalog. Its failure modes arise from
  omitting a companion pattern, Thread-Safe Interface, not from combining
  with one.

## 14. Refactoring path in and out

Introducing Strategized Locking into a component whose lock type is currently
hard-coded.

1. Identify every place inside the component's methods that directly names a
   concrete lock type, a member declared `std::mutex lock_;`, a
   language-specific `Mutex` type, or a raw `sync.Mutex` in Go.
2. Confirm the lock strategy is used only through a narrow, consistent set of
   operations, typically a pair of methods named acquire and release. If the code
   also calls strategy-specific operations, a timed acquire only one lock
   type supports, first narrow the usage to the common contract, or plan to
   carry that capability on a separate, optional interface per dimension 11's
   fourth failure mode.
3. Extract that narrow contract into an explicit type. A template or generic
   parameter bound with a trait or interface constraint if the target
   language supports zero-cost generics, or an abstract base
   class or interface if the strategy must be chosen at runtime.
4. Change the component's lock member from a concrete type to the new
   parameter or interface type, and change the component's own declaration to
   take that parameter, `class Component<LOCK>` or an injected
   `Locker lock` field, matching the language's idiom.
5. Write, or identify already-existing, concrete strategies satisfying the
   contract, at minimum the deployment's current real lock, and a no-op
   strategy if a zero-threading deployment target genuinely exists.
6. At every existing instantiation site, bind the concrete lock type that
   preserves the component's current behavior exactly, so this step
   introduces zero behavior change, only a structural one. Hide the
   instantiation behind a type alias if more than one call site needs the
   same binding, to avoid the obtrusive-locking liability from dimension 10.
7. Add a test, per dimension 15, that instantiates the component with at
   least two different strategies and confirms both produce identical
   externally observable behavior under contention, proving the
   strategization did not silently change semantics.

Removing Strategized Locking once it stops earning its place, which happens
when a component's deployment matrix has permanently collapsed to exactly one
lock type and no realistic plan exists to add a second.

1. Confirm, by searching every instantiation site across the codebase, that
   exactly one concrete lock type is ever bound to the component. If more
   than one is found, the pattern is still earning its keep and should not be
   removed.
2. Replace the type parameter or interface field with the one concrete lock
   type directly, inlining it as a hard-coded member.
3. Delete the now-unused strategy interface or type-parameter declaration,
   and any now-orphaned alternative strategy implementations that exist
   solely to satisfy the removed contract, following the standard dead-code
   removal discipline, confirm nothing else in the codebase still references
   them before deleting.
4. Re-run the dual-strategy test from introduction step 7 one final time
   before removing it, to confirm the collapse to a single strategy is truly
   a no-op with respect to current behavior, then delete that test as it no
   longer has a second strategy to compare against.

## 15. Testing and verification

*Testing guidance below is drawn from established concurrency-testing
practice. It is this entry's own analysis, labeled as such per the entry
contract, since the source paper predates most of the tooling named here.*

What Strategized Locking makes easier to test. Each concrete lock strategy is
a small, independent class satisfying a narrow contract, so its own
correctness, does `acquire` actually block a second caller, does `release`
actually unblock one, can be unit-tested in complete isolation from the
component that uses it, with no need to exercise the component's business
logic at all. Separately, the component's core logic can be tested using the
no-op strategy, `Null_Mutex` or its equivalent, in a fully deterministic,
single-threaded test run, verifying correctness of the algorithm with zero
concurrency noise, before a second pass verifies the same logic under a real
lock strategy with genuine concurrent access.

What becomes harder. A bug that only manifests with a specific lock strategy,
most often the self-deadlock failure mode from dimension 11, will not be
caught by tests that only exercise the no-op strategy, because a no-op
strategy cannot deadlock by construction. Any test suite for a strategized
component should deliberately instantiate the component under test with at
least one non-recursive, real-blocking strategy and drive an intra-component
call chain through it, specifically to catch the self-deadlock class before
it reaches production.

Concrete techniques.

- **Strategy substitution as a test double.** Because the lock strategy is
  already an injected parameter or interface, a test-only strategy that
  records every acquire and release call, with timestamps and the calling
  thread's identity, can be plugged in with no change to the component under
  test, giving a cheap, deterministic way to assert lock-acquisition
  invariants, every acquire is matched by exactly one release on the same
  thread, no acquire happens while the same thread already holds the lock
  without a recursive strategy, without needing to run under a real thread
  scheduler at all.
- **Stress and contention tests using a real strategy.** For the
  parameterized-type form in C++ and Rust, ThreadSanitizer,
  `-fsanitize=thread`, and Rust's own `loom` crate, for exhaustively
  exploring thread interleavings under the C11/C++11 memory model, both work
  unmodified against a strategized component instantiated with a real lock,
  because the strategy is a concrete type at that point and carries no
  special-casing for being "strategized."
- **Compile-time contract verification.** In languages with generics or
  templates constrained by an explicit trait or concept, Rust's trait bounds,
  C++20 concepts, Swift's protocol constraints, the strategy contract itself
  is checked at every instantiation site by the compiler, catching a
  strategy that does not satisfy the acquire/release shape before the test
  suite ever runs, which is strictly earlier feedback than a runtime
  duck-typing failure in Python or Go would give.
- **Golden-behavior comparison across strategies.** As named in the
  refactoring path above, a targeted test that instantiates the same
  component with two or more different concrete strategies and asserts
  identical externally observable results under an identical workload
  directly verifies the pattern's central promise, that the component's
  behavior is independent of which strategy is plugged in, rather than only
  verifying each strategy in isolation.

## 16. Observability signals

*Observability guidance is this entry's own practice-derived analysis, not
sourced from the original 1999 paper, which predates modern observability
tooling.*

What to log or trace. Which concrete lock strategy a given component instance
was configured with at startup, logged once at construction time rather than
per call, since the strategy binding does not change across the instance's
lifetime. This single log line is disproportionately valuable during an
incident, because the failure modes in dimension 11 are frequently traceable
to "the wrong strategy was configured for this deployment" and that fact is
otherwise invisible from the outside.

What to measure per lock strategy instance, distinguished by a label or tag
naming the concrete strategy in use so that a metrics dashboard can separate,
for instance, `Thread_Mutex`-backed instances from `RW_Lock`-backed instances
of the same component running in the same fleet.

- Time spent waiting to acquire the strategy's lock, as a histogram, not just
  an average, because contention pathologies show up in the tail.
- Lock hold duration, from acquire to release, again as a histogram, since a
  strategy whose hold duration grows unboundedly under load is the leading
  indicator of the tail-latency failure mode named in dimension 11.
- Acquisition attempt count versus successful acquisition count, for
  strategies that support a non-blocking `try_lock` style operation, since a
  growing gap between attempts and successes is an early signal of rising
  contention before it manifests as user-visible latency.

A healthy instance on a dashboard shows a lock-wait histogram with a short,
tight tail and a hold-duration histogram whose upper bound stays well below
the component's own request-timeout budget. A failing instance shows either a
lock-wait histogram whose tail grows without bound under sustained load, the
signature of genuine contention outstripping the chosen strategy's capacity,
or, in the specific self-deadlock failure mode, a hold-duration metric that
simply stops reporting entirely for the affected instance, because the thread
holding the lock never reaches the release call that would emit the
corresponding metric.

## 17. Security and privacy implications

Strategized Locking itself carries no data-handling implications. It governs
which synchronization primitive protects a component's state, not what that
state contains, so it introduces no new data flow, storage, or transmission
concern by itself.

One narrow attack surface is worth naming plainly rather than inventing a
larger concern where none exists. If the concrete lock strategy is selected
at runtime from an externally influenced source, a configuration value read
from an untrusted request, an environment variable an attacker can set in a
shared or multi-tenant hosting environment, rather than from a trusted,
operator-controlled configuration, an attacker who can force a component into
using the no-op `Null_Mutex` strategy in a genuinely concurrent deployment can
turn a correctness bug, the silent data-race failure mode in dimension 11,
into a targeted denial-of-service or data-corruption vector, by deliberately
racing requests against a component that believes it does not need to
serialize them. The mitigation is unrelated to the pattern itself and is a
standard configuration-hygiene practice. Strategy selection should be bound
at deployment or build time from a trusted source, never derived from
untrusted, per-request input.

A second, minor consideration applies specifically to the polymorphic
variant. Because the strategy is held behind an interface reference rather
than a concrete type, a component's own type signature does not, by
inspection, reveal which lock strategy protects it, which can slow down a
security or correctness audit that is trying to establish whether a given
code path is actually safe under concurrent access. This is a code-review
cost, not a runtime vulnerability, and it is fully mitigated by the logging
practice named in dimension 16, recording the bound strategy explicitly at
construction time.

## Code examples

Three languages, chosen because each expresses a different binding mechanism
for the strategy, compiled or run directly for this entry rather than merely
written by hand. The pattern's own source paper is written in C++, using
template parameters resolved at compile time, and that origin is discussed
throughout this entry, but the runnable samples below draw from the language
set this catalog checks by machine, TypeScript, Rust, and Go, so each sample's
correctness is verified rather than merely asserted. TypeScript shows the
polymorphic (interface-injection) form applied to the async single-threaded
case, an async critical section serialized across interleaved promises rather
than a blocking OS thread lock, which is the honest idiomatic shape
Strategized Locking takes in a language with no OS-level threads in its
standard model. Rust shows the compile-time mechanism through a trait bound,
matching the production shape used by the `lock_api` crate cited in dimension
9. Go shows the polymorphic form through structural typing, where the
standard library's own `sync.Mutex` satisfies the strategy interface with no
explicit declaration at all. Java and Swift are not given separate samples
because both would only restate the polymorphic form already shown in Go and
TypeScript, generics in both languages either erase at runtime (Java) or
dispatch through a witness table with no zero-cost compile-time
specialization guarantee comparable to Rust monomorphization (Swift protocols
with associated types come closest, but add no third mechanism worth a
listing). Python is omitted for the same reason as the structural note in
dimension 8, its duck-typed variant is a weaker-typed restatement of the same
idea already shown in Go.

### TypeScript

Type-checked with `tsc --noEmit --strict` and run with Node. Output confirmed
`single 2` and `serialized 50`.

```typescript
// A synchronization strategy for async critical sections. In a
// single-threaded event loop, "locking" means serializing interleaved
// awaits, not blocking a second OS thread, but the strategized-locking
// shape is identical. the strategy is a pluggable, injected dependency.
interface LockStrategy {
  withLock<T>(fn: () => T | Promise<T>): Promise<T>;
}

// A no-op strategy for contexts with no concurrent interleaving, for
// example a single caller with no other async work sharing the resource.
class NullLock implements LockStrategy {
  async withLock<T>(fn: () => T | Promise<T>): Promise<T> {
    return fn();
  }
}

// A queueing strategy that serializes calls by chaining onto the tail of
// a promise, so two interleaved increments never race between their read
// and their write.
class AsyncQueueLock implements LockStrategy {
  private tail: Promise<unknown> = Promise.resolve();

  withLock<T>(fn: () => T | Promise<T>): Promise<T> {
    const run = this.tail.then(fn, fn);
    this.tail = run.catch(() => undefined);
    return run;
  }
}

// Counter's synchronization aspect is a strategy supplied at
// construction time, matching the polymorphic (interface-injection)
// form of Strategized Locking.
class Counter<S extends LockStrategy> {
  private value = 0;

  constructor(private readonly strategy: S) {}

  async increment(): Promise<void> {
    await this.strategy.withLock(async () => {
      const current = this.value;
      await Promise.resolve();
      this.value = current + 1;
    });
  }

  read(): number {
    return this.value;
  }
}

async function main(): Promise<void> {
  const single = new Counter(new NullLock());
  await single.increment();
  await single.increment();
  console.log("single", single.read());

  const serialized = new Counter(new AsyncQueueLock());
  await Promise.all(
    Array.from({ length: 50 }, () => serialized.increment())
  );
  console.log("serialized", serialized.read());

  if (serialized.read() !== 50) {
    throw new Error(`expected 50, got ${serialized.read()}`);
  }
}

void main();
```

### Rust

Compiled with `rustc -O` and run. Output confirmed
`single=5 shared=80000 wrapped=4000`.

```rust
use std::cell::UnsafeCell;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex as StdMutex};
use std::thread;

// The synchronization strategy is a trait, not a concrete type. Any raw
// lock that implements it can be plugged into Counter<R> below.
trait RawLock: Default {
    fn lock(&self);
    fn unlock(&self);
}

// A no-op strategy for single-threaded use. Every call inlines away.
#[derive(Default)]
struct NullLock;
impl RawLock for NullLock {
    fn lock(&self) {}
    fn unlock(&self) {}
}

// A minimal spinlock strategy for multi-threaded use.
#[derive(Default)]
struct SpinLock {
    flag: AtomicBool,
}
impl RawLock for SpinLock {
    fn lock(&self) {
        while self
            .flag
            .compare_exchange_weak(false, true, Ordering::Acquire, Ordering::Relaxed)
            .is_err()
        {}
    }
    fn unlock(&self) {
        self.flag.store(false, Ordering::Release);
    }
}

// Counter is strategized over R. the lock type is a generic parameter,
// resolved at compile time, matching the parameterized-type form of
// Strategized Locking (see the lock_api crate for the production version).
struct Counter<R: RawLock> {
    raw: R,
    value: UnsafeCell<i64>,
}

unsafe impl<R: RawLock + Sync> Sync for Counter<R> {}

impl<R: RawLock> Counter<R> {
    fn new() -> Self {
        Counter { raw: R::default(), value: UnsafeCell::new(0) }
    }

    fn increment(&self) {
        self.raw.lock();
        unsafe {
            *self.value.get() += 1;
        }
        self.raw.unlock();
    }

    fn value(&self) -> i64 {
        unsafe { *self.value.get() }
    }
}

fn main() {
    let single: Counter<NullLock> = Counter::new();
    for _ in 0..5 {
        single.increment();
    }
    assert_eq!(single.value(), 5);

    let shared = Arc::new(Counter::<SpinLock>::new());
    let mut handles = Vec::new();
    for _ in 0..8 {
        let c = Arc::clone(&shared);
        handles.push(thread::spawn(move || {
            for _ in 0..10_000 {
                c.increment();
            }
        }));
    }
    for h in handles {
        h.join().unwrap();
    }
    assert_eq!(shared.value(), 80_000);

    // std::sync::Mutex is a different shape (guard-returning, not raw
    // lock/unlock), so it is wrapped rather than plugged in directly.
    // This is the second, polymorphic-friendly variant of the pattern.
    let wrapped = Arc::new(StdMutex::new(0i64));
    let mut handles2 = Vec::new();
    for _ in 0..4 {
        let m = Arc::clone(&wrapped);
        handles2.push(thread::spawn(move || {
            for _ in 0..1_000 {
                *m.lock().unwrap() += 1;
            }
        }));
    }
    for h in handles2 {
        h.join().unwrap();
    }

    println!(
        "single={} shared={} wrapped={}",
        single.value(),
        shared.value(),
        *wrapped.lock().unwrap()
    );
}
```

### Go

Run with `go run main.go`. Output confirmed `single=5 shared=80000 rw=4000`.

```go
package main

import (
	"fmt"
	"sync"
	"sync/atomic"
)

// Locker is the strategized synchronization interface. Any type that
// implements Lock/Unlock can be injected into Counter, matching the
// polymorphic form of Strategized Locking (Go has no compile-time
// template parameter, so the strategy is a runtime interface instead).
type Locker interface {
	Lock()
	Unlock()
}

// NullLock is a no-op strategy for single-goroutine use.
type NullLock struct{}

func (NullLock) Lock()   {}
func (NullLock) Unlock() {}

// Counter's synchronization aspect is a field of type Locker, supplied
// by the caller at construction time rather than hard-coded.
type Counter struct {
	lock  Locker
	value int64
}

func NewCounter(strategy Locker) *Counter {
	return &Counter{lock: strategy}
}

func (c *Counter) Increment() {
	c.lock.Lock()
	defer c.lock.Unlock()
	c.value++
}

func (c *Counter) Value() int64 {
	return atomic.LoadInt64(&c.value)
}

func main() {
	single := NewCounter(NullLock{})
	for i := 0; i < 5; i++ {
		single.Increment()
	}
	if single.Value() != 5 {
		panic("single mismatch")
	}

	// sync.Mutex satisfies Locker without any adapter. Go's structural
	// typing means the standard mutex is already a valid strategy.
	shared := NewCounter(&sync.Mutex{})
	var wg sync.WaitGroup
	for t := 0; t < 8; t++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for i := 0; i < 10000; i++ {
				shared.Increment()
			}
		}()
	}
	wg.Wait()
	if shared.Value() != 80000 {
		panic(fmt.Sprintf("shared mismatch. %d", shared.Value()))
	}

	// A readers-writer lock is a different but Locker-compatible
	// strategy. RWMutex.Lock/Unlock give exclusive access.
	rw := NewCounter(&sync.RWMutex{})
	var wg2 sync.WaitGroup
	for t := 0; t < 4; t++ {
		wg2.Add(1)
		go func() {
			defer wg2.Done()
			for i := 0; i < 1000; i++ {
				rw.Increment()
			}
		}()
	}
	wg2.Wait()

	fmt.Printf("single=%d shared=%d rw=%d\n", single.Value(), shared.Value(), rw.Value())
}
```

## 18. References

1. Douglas C. Schmidt, "Strategized Locking, Thread-safe Interface, and
   Scoped Locking. Patterns and Idioms for Simplifying Multi-threaded C++
   Components," *C++ Report*, SIGS Publications, Volume 11, Number 9,
   September 1999. Full text at
   https://www.dre.vanderbilt.edu/~schmidt/PDF/locking-patterns.pdf, verified
   2026-08-14, retrieved and its text extracted directly for this entry.
   Listed on the author's own publications page at
   https://www.dre.vanderbilt.edu/~schmidt/patterns-ace.html, verified
   2026-08-14.
2. Douglas C. Schmidt, Michael Stal, Hans Rohnert, Frank Buschmann,
   *Pattern-Oriented Software Architecture, Volume 2. Patterns for Concurrent
   and Networked Objects*, Wiley, 2000, object-synchronization pattern
   family including Strategized Locking, Scoped Locking, Thread-Safe
   Interface, and Double-Checked Locking Optimization. Publication metadata
   corroborated at
   https://en.wikipedia.org/wiki/Pattern-Oriented_Software_Architecture,
   verified 2026-08-14.
3. `lock_api` crate documentation, https://docs.rs/lock_api/latest/lock_api/,
   verified 2026-08-14. Generic `Mutex<R, T>` and `RwLock<R, T>` types
   parameterized over a `RawMutex` or `RawRwLock` trait, the Rust ecosystem's
   production instance of the parameterized-type form of Strategized
   Locking, and the foundation of the widely used `parking_lot` crate.
4. Oracle, `java.util.concurrent.locks.Lock` interface documentation, Java SE
   21,
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/locks/Lock.html,
   verified 2026-08-14. The Java Standard Library's production instance of
   the polymorphic form, implemented by `ReentrantLock` and both views of
   `ReentrantReadWriteLock`.
5. DOCGroup, `ACE_TAO` source repository, `ACE/ace/Synch_Traits.h`,
   https://github.com/DOCGroup/ACE_TAO/blob/master/ACE/ace/Synch_Traits.h,
   verified 2026-08-14. Defines `ACE_NULL_SYNCH` and `ACE_MT_SYNCH` traits
   classes and the resulting `ACE_SYNCH_MUTEX` type alias, the macro or
   conditional-typedef variant of Strategized Locking in active production
   use, corroborating the source paper's own Known Uses claim that the
   pattern is used extensively throughout the ACE toolkit.
