---
name: Scoped Locking
slug: scoped-locking
family: 09-concurrency
category: Concurrency
aliases: [RAII Lock, Lock Guard, Guard Idiom, Resource Acquisition Is Initialization applied to mutexes]
first_described: "Schmidt 1999; Schmidt, Stal, Rohnert, Buschmann 2000"
maturity: canonical
related: [strategy, thread-safe-interface, double-checked-locking, monitor-object, active-object, reactor]
incompatible_with: []
verified: 2026-08-13
---

# Scoped Locking

## 1. Name, aliases, and lineage

The canonical name is Scoped Locking. It was named and formalized by Douglas
C. Schmidt in "Strategized Locking, Thread-safe Decorator, and Scoped Locking.
Patterns and Idioms for Simplifying Multi-threaded C++ Components," *C++
Report*, SIGS, Volume 11, Number 9, September 1999
(https://www.dre.vanderbilt.edu/~schmidt/patterns-ace.html, verified
2026-08-13, which lists the paper and its abstract, and links to the PDF at
https://www.dre.vanderbilt.edu/~schmidt/PDF/locking-patterns.pdf, verified
2026-08-13, live and served). The pattern was folded into the concurrency
pattern language of the second Pattern-Oriented Software Architecture volume
the following year. Douglas C. Schmidt, Michael Stal, Hans Rohnert, Frank
Buschmann, *Pattern-Oriented Software Architecture, Volume 2. Patterns for
Concurrent and Networked Objects*, Wiley, 2000, where it sits alongside
Strategized Locking, Thread-Safe Interface, and Double-Checked Locking
Optimization as the small family of idioms POSA2 groups under object
synchronization. The book's authorship and year are confirmed independently at
https://en.wikipedia.org/wiki/Pattern-Oriented_Software_Architecture, verified
2026-08-13.

The most common alias in day-to-day C++ conversation is RAII Lock, because
Scoped Locking is the textbook instance of the broader Resource Acquisition Is
Initialization idiom, a phrase coined by Bjarne Stroustrup for binding a
resource's lifetime to a stack-allocated object's constructor and destructor.
Two other names are used interchangeably by different standard libraries for
essentially the same shape with different multiplicities. Lock Guard, after the
C++ Standard Library type `std::lock_guard`, which wraps exactly one mutex, and
Guard Idiom, the term Schmidt's own paper and the ACE framework's source use for
the class itself, `ACE_Guard`. When a language calls the type by a different
noun (`MutexGuard` in Rust, `AutoLock` in Chromium's base library, `MutexLock`
in Google's Abseil), the pattern underneath is the same one described here, not
a different pattern with a coincidentally similar shape.

A distinction worth drawing at the outset. Scoped Locking is a solution to
acquiring and releasing a lock in a disciplined way, not a solution to what to
protect or how coarse a lock should be. Which mutex a piece of state uses is a
design decision the Strategized Locking pattern addresses, by making the lock
type a template or strategy parameter so the same class can run
single-threaded, thread-safe, or reentrant-safe depending on the lock type it
is instantiated with. Scoped Locking composes with that decision. it does not
replace it.

## 2. Problem and context

A piece of code acquires a lock to protect a critical section, and every path
out of that critical section, the normal return, the early return, the thrown
exception, the `break` out of a loop that spans the critical section, must
release the same lock exactly once. A function with three exit points and a
manually paired acquisition and release call needs the release call written,
or at least reached, at each of those three points, and a fourth exit point
added six months later by someone who has never seen the discipline the
function relies on is not required by the compiler to remember it.

The failure this produces is a deadlock, and it is the worst kind of
deadlock to diagnose, because the bug is not in the code that hangs. The
thread that hangs is waiting correctly, exactly as designed, for a lock that
another thread never released. The defect is in a completely different
function, possibly compiled from a completely different translation unit,
possibly written years earlier by someone no longer on the team, on a code
path that is not exercised by the normal test suite because it is the
exception path, the early-return path, or the `throw` path. A reviewer
reading the function that hangs learns nothing. the bug is upstream, in the
function that forgot to release.

The context in which this problem appears is any language whose native
locking primitive is a pair of imperative calls, `lock()` then later
`unlock()`, rather than a lexical block that a compiler enforces. C's
`pthread_mutex_lock` and `pthread_mutex_unlock`, Java's
`java.util.concurrent.locks.Lock.lock()` and `.unlock()`, C++'s raw
`std::mutex::lock()` and `.unlock()`, and the Win32 `EnterCriticalSection`
and `LeaveCriticalSection` API are all in this shape. `java.util.concurrent`'s
own Javadoc states the danger plainly for `ReentrantLock`. "It is recommended
that the following idiom always be used" (lock, then `try`, then `finally`
with the release call inside it), because there is no other mechanism in the
language that guarantees the release runs
(https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/locks/ReentrantLock.html,
verified 2026-08-13). Languages that instead give the programmer an
exception-safe scope, a destructor, a `Drop` implementation, a context
manager, or a `defer` statement, can express the same guarantee mechanically,
and Scoped Locking is the name for using that mechanism specifically to bind a
lock's lifetime to a stack-local object rather than to a manually paired call.

## 3. Forces

**Correctness under all exit paths versus expressiveness of the locking API.**
A bare `lock()` and `unlock()` pair is the most expressive locking API there
is, because it lets the lock be held across arbitrary, non-lexical control
flow, including across function calls that return without releasing on purpose
(hand-off locking) or held while awaiting a condition variable inside a loop
whose bounds are not known until runtime. Scoped Locking trades that
flexibility for a static, lexical guarantee. it can only express "held for
exactly this block," which is the overwhelming majority of real critical
sections and a poor fit for the small minority that need to hand a held lock
across a boundary.

**Exception safety versus explicit control.** Once a codebase permits
exceptions, or panics, or early returns from deep call stacks, a release call
written at the bottom of a function is unreachable by every path that leaves
through the middle. Scoped Locking closes this gap for free, because the
guard's cleanup is tied to stack unwinding, which every one of those paths
triggers identically. The force it gives up in exchange is that the exact
moment of release becomes implicit. a reader has to know the scope's extent
to know when the lock lets go, rather than reading it off an explicit call
site.

**Lock-order deadlock avoidance versus simplicity of a single-mutex guard.**
The original single-mutex Scoped Locking idiom does nothing to prevent two
threads acquiring two mutexes in opposite order and deadlocking against each
other. C++17's `std::scoped_lock`, described further in Dimension 8, extends
the idiom to accept several mutexes in one constructor call and uses a
deadlock-avoidance algorithm, equivalent to `std::lock`, to acquire them
without introducing a fixed global order
(https://learn.microsoft.com/en-us/cpp/standard-library/scoped-lock-class,
verified 2026-08-13). That extension costs a small amount of per-acquisition
overhead (the algorithm may retry) in exchange for closing an entire class of
deadlock that single-mutex Scoped Locking is silent about.

**Granularity versus contention.** Scoped Locking says nothing about how big
the scope should be, and this is a judgement call the pattern hands entirely
to the author. A scope drawn too wide holds the lock across expensive,
unrelated work (a network call, a log write, a heap allocation) and creates
contention that has nothing to do with the data actually being protected. A
scope drawn too narrow protects each field independently and reintroduces the
torn-update races the lock existed to prevent. The mechanical guarantee Scoped
Locking gives, correct release, is orthogonal to this design decision, and it
is easy to mistake "the lock is released correctly" for "the lock is held for
the right amount of time." They are different properties.

## 4. Applicability and non-applicability

Reach for Scoped Locking when:

- The critical section has a single entry and, from the lock's point of view,
  a single conceptual exit, even if the function has several `return`
  statements, throws, or is written in a language with unchecked exceptions.
- The lock and the protected data have a clear lexical scope, typically a
  function body, a method body, or a block inside one.
- The language gives a mechanical, compiler-or-runtime-enforced way to run
  code on scope exit, a destructor, `Drop`, a context manager `__exit__`, a
  `defer` statement, or `try`/`finally` with an `AutoCloseable`-style wrapper.
- Multiple mutexes must be acquired together and a deadlock-avoidance
  algorithm is available for the multi-mutex constructor form (see Dimension
  8, `std::scoped_lock`).
- Code review or static analysis benefits from making the lock's extent
  visually obvious. a scoped-lock declaration at the top of a block is a
  legible promise that the block is the whole critical section.

Do NOT reach for Scoped Locking when:

- The lock must outlive the function that acquires it, for example a
  hand-off pattern where thread A acquires a lock and thread B releases it
  after consuming a queued item. There is no lexical scope spanning two
  threads for a stack-bound guard to attach to. this needs an explicit,
  independently owned lock handle, and hand-off locking is a documented and
  legitimate use case in the ACE literature precisely because the scoped
  idiom cannot express it (Schmidt 1999, cited above).
- The lock must be released and reacquired repeatedly inside a loop body in a
  pattern that does not map cleanly to nested blocks. a monolithic
  scoped-lock declared once at the top of the loop holds the lock for the
  whole loop body, defeating the purpose of releasing between iterations, and
  writing a fresh scoped lock per iteration inside an artificial inner block
  works but reads awkwardly compared to explicit acquire and release calls
  placed where the algorithm's structure actually wants them.
- The language has no stack-unwind-triggered cleanup mechanism at all and no
  cooperative equivalent (no destructor, no `finally`, no context manager, no
  `defer`). In that situation the underlying guarantee Scoped Locking depends
  on, code on this path always runs when the scope is left, does not exist,
  and a hand-rolled guard object provides no safety over a bare
  `lock()`/`unlock()` pair, only a naming convention.
- The critical section is a single, already-atomic operation better expressed
  with a lock-free primitive (`std::atomic`, `AtomicInteger`,
  `sync/atomic`), where introducing any mutex, scoped or not, is pure overhead
  for a case the hardware already handles.
- A monitor, actor, or thread-confinement design (Monitor Object, Active
  Object) already makes every method on the object implicitly synchronized or
  message-serialized. layering an additional scoped mutex inside such a
  method's body is either redundant or, worse, a second lock that can be
  acquired in the opposite order to the first one elsewhere in the program.
- The scope, once drawn honestly around only the shared-state accesses, would
  span an I/O call, a network round trip, or another unbounded-latency
  operation. Scoped Locking will still release correctly here, but the forces
  in Dimension 3 say this is a granularity mistake the pattern does not fix.
  the fix is to shrink the scope or copy the data out before releasing, not
  to abandon the pattern.

## 5. Structure

- **Guard (the scoped-lock object).** A value, typically stack-allocated, that
  wraps a reference or pointer to one Lock (or, in multi-mutex variants,
  several). Its constructor performs the acquisition, blocking if necessary.
  Its destructor, or language-equivalent cleanup hook, performs the release
  regardless of whatever path caused the object to go out of scope. It is
  non-copyable, because a Guard that could be copied would try to release the
  same lock twice, once per copy, and it is typically non-default-constructible,
  because a Guard with no lock to release has no reason to exist.
- **Lock (the protected resource).** The mutex, reentrant lock, reader-writer
  lock, or spinlock the Guard wraps. The Guard is deliberately ignorant of the
  Lock's internal implementation. it only needs the Lock to expose an acquire
  operation and a release operation, which is what lets the same Guard shape
  be reused across mutex, recursive mutex, and reader-writer lock types via a
  template, generic, or trait parameter (this is exactly the axis Strategized
  Locking varies).
- **Client (the code inside the scope).** The block of statements lexically
  contained within the Guard's lifetime. The client accesses the shared state
  the Lock protects, and is written as though single-threaded, because for the
  duration of the Guard's life, with respect to that Lock, it is.
- **Adopting constructor (optional).** A second constructor form, taking an
  extra tag argument (`std::adopt_lock` in C++, or simply skipping the
  acquire call in a hand-rolled implementation), that constructs a Guard
  around a Lock the caller has already acquired by other means, so that the
  Guard only owns the release, not the acquisition. This is the mechanism
  that lets Scoped Locking interoperate with hand-off locking rather than
  forbid it outright.

## 6. ASCII structure diagram

```
+-------------------------------------------------+
|                     Client                       |
|  {                                                |
|      Guard g(lock);   <-- constructor acquires    |
|      ... protected access to shared state ...     |
|  }   <-- end of scope, destructor releases         |
+-------------------------------------------------+
              |                     ^
              | constructs          | destroys
              v                     |
        +-----------+         +-----------+
        |   Guard   | ------> |    Lock   |
        |-----------|  wraps  |-----------|
        | +Guard()  |         | +acquire()|
        | +~Guard() |         | +release()|
        +-----------+         +-----------+
             ^
             | non-copyable, non-assignable
             | (would double-release on copy)
```

## 7. Dynamics

```
Thread T1                          Lock L                    Thread T2
   |                                  |                            |
   | enter block                     |                            |
   | Guard g1(L)                     |                            |
   |----- acquire() -----------------|                            |
   |                                  | granted (free -> held)    |
   |<---- returns, g1 owns lock ------|                            |
   |                                  |                            |
   |  ... critical section work ...  |         Guard g2(L)         |
   |                                  |<-----------acquire()-------|
   |                                  |         (T2 blocks, L held)|
   |                                  |                            |
   | return / throw / break          |                            |
   | g1 destructor runs (stack       |                            |
   |  unwind or normal exit)         |                            |
   |----- release() -----------------|                            |
   |                                  | (held -> free, then        |
   |                                  |  immediately re-granted    |
   |                                  |  to the waiting T2)        |
   |                                  |------ acquire() succeeds ->|
   |                                  |                            |
   | (T1's block has fully exited,   |    ... T2's critical        |
   |  g1 no longer exists)           |        section work ...     |
   |                                  |                            |
   |                                  |<---- g2 destructor runs ---|
   |                                  |------ release() -----------|
```

The dynamics that matter are what happens on the abnormal path, shown here as
"return / throw / break." Whichever of those three actually fires, the same
destructor call executes, at the same point in the control-flow graph from the
runtime's point of view. the point where the stack frame containing `g1`
unwinds. The client code never writes a second call to release the lock for
the exception case, because there is no second call. there is exactly one
release path, driven by the language runtime's own unwinding mechanism, and it
runs whether the block exits through its closing brace, a `throw`, a `return`
buried three `if` statements deep, or a `panic!` in Rust that is caught by an
enclosing `catch_unwind`.

## 8. Implementation variants

**Single-mutex RAII guard, C++.** `std::lock_guard<Mutex>`, standardized in
C++11, is the canonical minimal form. its constructor locks the mutex passed
to it, its destructor releases it regardless of exit path, and the type is
explicitly non-copyable. Microsoft's C++ Standard Library reference documents
the destructor's single responsibility plainly. "Unlocks the mutex that was
passed to the constructor"
(https://learn.microsoft.com/en-us/cpp/standard-library/lock-guard-class,
verified 2026-08-13). `std::unique_lock` is a heavier sibling in the same
standard library that adds deferred locking, timed locking, and the ability
to release early or transfer ownership, at the cost of being movable rather
than a pure fixed-scope guard, and is the type to reach for when a Guard
needs to be handed to a condition variable's `wait()` call, which needs to
release and reacquire the lock internally.

**Multi-mutex deadlock-avoiding guard, C++17.** `std::scoped_lock` accepts a
variadic list of mutexes in one constructor call and, when given more than
one, uses a deadlock-avoidance algorithm equivalent to `std::lock` to acquire
all of them without a fixed acquisition order, "prevent[ing] deadlocks" per
Microsoft's own documentation, and offering an `adopt_lock` constructor form
for taking ownership of mutexes a caller has already locked
(https://learn.microsoft.com/en-us/cpp/standard-library/scoped-lock-class,
verified 2026-08-13). This is the variant that directly answers the
lock-ordering force in Dimension 3, and it is the form to prefer over
`std::lock_guard` any time a function needs to hold two or more mutexes at
once, even if today's callers never actually contend on ordering, because it
removes the class of bug outright rather than relying on every future caller
following a documented acquisition order by hand.

**Ownership-transferring guard, Rust.** `std::sync::Mutex::lock()` returns a
`Result<MutexGuard<T>, PoisonError<T>>`, and `MutexGuard` implements `Deref`
and `DerefMut` so the guard is used as if it were the protected value itself,
and implements `Drop` so the guard's cleanup runs when its scope ends. Rust
adds a property the C++ forms do not have as a language guarantee. the
borrow checker statically forbids code outside the guard's lifetime from
touching the protected `T` at all, so "forgot to acquire the lock before
touching the data" is a compile error, not merely "forgot to release it" being
impossible. Rust additionally poisons the mutex if the thread holding the
guard panics, returning `Err(PoisonError)` from the next `lock()` call rather
than silently handing out a guard over data that may be in an inconsistent,
half-mutated state
(https://doc.rust-lang.org/std/sync/struct.Mutex.html, verified 2026-08-13).

**`defer`-based idiom, Go.** Go has no destructors and no exceptions in the
C++ sense, so the idiomatic form pairs a `sync.Mutex` with a `defer m.Unlock()`
statement placed immediately after `m.Lock()`. this is functionally
Scoped Locking without a distinct Guard type. the "guard" is the scheduled
deferred call itself, and Go's own package documentation names the pattern
directly as the recommended usage, warning that calling the release method on
an already-free mutex is a run-time error
(https://pkg.go.dev/sync, verified 2026-08-13). The `defer` statement runs on
every return path from the enclosing function, including a `panic`, which
gives the same abnormal-path guarantee C++'s destructor gives, scoped to the
whole function rather than an arbitrary inner block, because Go's `defer` is
function-scoped, not block-scoped. Achieving a narrower scope in Go requires
wrapping the critical section in a literal, immediately invoked closure so the
`defer` fires at the closure's return rather than the outer function's.

**Context-manager idiom, Python.** `threading.Lock` (and every other
synchronization primitive in the `threading` module that exposes `acquire`
and `release`) supports Python's context-management protocol directly, so
`with lock:` acquires on entry and releases on exit, including exit by
exception. Python's own documentation states the equivalence directly.
using the lock as a context manager is defined to be the same as calling
`acquire()`, then a `try`, then `release()` inside `finally`
(https://docs.python.org/3/library/threading.html, verified 2026-08-13).
Because Python's `with` statement is a first-class language feature rather
than a library convention layered on top of destructors, the guard object
here is the built-in lock itself. no separate wrapper type is needed, and the
idiom looks identical for every stdlib primitive that exposes the two
methods.

**Emulated guard via `try`/`finally` or `AutoCloseable`, Java.**
`ReentrantLock`'s own Javadoc recommends the `lock()`, `try`, `finally`
release idiom as the safe pattern
(https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/locks/ReentrantLock.html,
verified 2026-08-13), because `java.util.concurrent.locks.Lock` was
deliberately designed without a language-level scoping construct bound to it.
A codebase can recover a closer approximation of Scoped Locking by writing a
small `AutoCloseable` wrapper whose constructor calls `lock()` and whose
`close()` calls the release method, then acquiring it inside a
`try`-with-resources statement, which Java guarantees calls `close()` on
every exit path exactly once, including exceptional exit. This is judgement,
not a documented standard-library idiom. Java's `java.util.concurrent`
package ships no such wrapper itself, and the community is divided on
whether the extra indirection is worth it over the plain `try`/`finally`
form the Javadoc itself recommends, precisely because `try`-with-resources
already gives the same cleanup guarantee on every path without a wrapper
class, at the cost of an unused variable binding at the call site
(`try (var ignored = ...)`).

**Async, single-threaded scoped locking, JavaScript and TypeScript.** In a
cooperatively-scheduled, single-threaded runtime like Node.js, there is no
preemption inside a synchronous stretch of code, so a traditional OS mutex is
unnecessary, but a multi-step operation that `await`s partway through, for
example read-modify-write against a database or an in-memory structure
touched by another concurrent async task, can still be interleaved by another
task between the `await` points and needs the same acquire-then-release
discipline. The idiom here, seen in userland libraries such as
`async-mutex`, wraps a promise-based acquire in a helper method (commonly
named `runExclusive` or `withLock`) that takes a callback, awaits the
callback's completion inside a `try`/`finally`, and releases inside the
`finally` regardless of whether the callback resolved or rejected. This is
the same structural guarantee as `lock_guard`, expressed with a
higher-order function taking a closure instead of a stack-lifetime object,
because the language has closures and promises but no scope-exit hook a plain
lexical block could bind to for an asynchronous critical section.

## 9. Known production uses

- **ACE (the Adaptive Communication Environment).** The C++ networking
  framework that Scoped Locking was designed for and named in. Schmidt's 1999
  paper describing the pattern is hosted alongside the rest of the ACE
  pattern literature at Vanderbilt's DRE lab
  (https://www.dre.vanderbilt.edu/~schmidt/patterns-ace.html, verified
  2026-08-13, live), and ACE's own source, maintained today at
  https://github.com/DOCGroup/ACE_TAO (verified 2026-08-13, live, active
  repository), is the codebase from which the idiom was extracted before
  being generalized into the C++ standard library as `std::lock_guard` and
  `std::unique_lock` more than a decade later.
- **Google's Abseil C++ library.** `absl::MutexLock` is documented as
  existing specifically to apply RAII to `absl::Mutex` acquisition and
  release, with Abseil's own synchronization guide stating that the class
  "uses RAII to acquire the mutex and automatically releases it when the
  class goes out of scope"
  (https://abseil.io/docs/cpp/guides/synchronization, verified 2026-08-13),
  and recommending it over calling `Lock()` and `Unlock()` by hand for
  exactly the exit-path-correctness reason described in Dimension 2.
- **The ISO C++ Standard Library**, via `std::lock_guard` (C++11) and
  `std::scoped_lock` (C++17), shipped in every conforming C++ implementation,
  including libstdc++, libc++, and Microsoft's STL, whose own reference page
  documents `scoped_lock`'s deadlock-avoidance behaviour for the multi-mutex
  case (https://learn.microsoft.com/en-us/cpp/standard-library/scoped-lock-class,
  verified 2026-08-13).
- **The Rust Standard Library.** `std::sync::MutexGuard`, returned from every
  call to `Mutex::lock()`, is the mechanism by which Rust code protects
  shared state across threads at all. there is no lower-level manual
  acquire-and-release API exposed for `std::sync::Mutex` in safe Rust, which
  means Scoped Locking is not an optional idiom layered on top of a more
  primitive API in Rust, it is the only API
  (https://doc.rust-lang.org/std/sync/struct.Mutex.html, verified
  2026-08-13).
- **The Go Standard Library's own documentation**, which names the
  `Lock()`/`defer Unlock()` idiom as the way `sync.Mutex` is meant to be used
  in every code example the `sync` package's godoc includes
  (https://pkg.go.dev/sync, verified 2026-08-13).

## 10. Consequences

Positive.

- Every acquired lock is released exactly once, on every exit path, including
  exceptions, panics, and early returns, without the author writing a
  separate release call for each of those paths, because the release is
  driven by the language runtime's own scope-exit mechanism rather than by
  code the author remembers to write.
- The extent of a critical section becomes visually apparent at the
  declaration site. a reviewer sees `Guard g(lock)` at the top of a block and
  knows, without tracing every path out of the function, that the lock covers
  exactly that block.
- Composability with the language's other resource-management idioms.
  because Scoped Locking is an instance of RAII (or its per-language
  equivalent) rather than a bespoke mechanism, it stacks in a well-defined way
  with other RAII-managed resources acquired in the same scope, and
  destructors, `Drop` implementations, or `finally` blocks run in the
  well-defined reverse order of construction, so nested locks release in the
  correct order without extra bookkeeping.
- It removes an entire category of leak-on-exception bug at compile time in
  languages like Rust, where the guard's lifetime is enforced by the borrow
  checker, and it removes it at the cost of code review discipline in
  languages like C++ and Java, where nothing stops a programmer from calling
  the release method a second time by hand and defeating the guarantee.

Negative.

- A guard tied to a stack scope cannot express hand-off locking, where one
  thread acquires and a different thread releases. Programs that genuinely
  need this must fall back to a manually managed lock handle for that one
  code path, which reintroduces the exact discipline problem Scoped Locking
  exists to remove, scoped narrowly to the hand-off code.
- The implicit release point can obscure exactly when a lock lets go in a
  function with several nested blocks, particularly in languages, like Go,
  where `defer` is function-scoped rather than block-scoped, so a lock
  acquired early in a long function is held until the function returns even
  if the critical section conceptually ended many lines earlier, unless the
  author manually carves out a narrower closure.
- A misused Guard, most commonly one declared but immediately discarded
  (binding it to `_` or an unnamed temporary in a language that allows a
  temporary to be destroyed at the end of the full expression rather than the
  end of the block), releases the lock far earlier than the author intended,
  and the resulting bug looks exactly like an unprotected critical section
  because, for the duration that matters, it is one.
- Nesting several Guards acquired one at a time in a fixed textual order,
  rather than using a multi-mutex constructor form when one is available,
  reintroduces lock-order deadlock risk between threads that acquire the same
  two mutexes in opposite textual order, and Scoped Locking's single-mutex
  form provides no defense against this. only the multi-mutex form
  (`std::scoped_lock`) does.

## 11. Failure modes and misuse

**Symptom.** A lock appears to be released the instant it is acquired, and a
race condition shows up in exactly the code the lock was meant to protect.
**Cause.** The Guard was bound to a temporary rather than a named local, most
commonly written as `Guard(lock);` with no variable name, which in several
languages (notably C++, where an unnamed temporary is destroyed at the end of
the full expression it appears in, not at the end of the enclosing block)
releases the lock before the next statement executes. **Fix.** Always bind
the guard to a named local variable, even one that is never read again
(`Guard guard(lock);` or the language's equivalent of an intentionally-unused
binding), and treat a linter warning about an unused local guard variable as
a false positive that should be silenced explicitly, not removed.

**Symptom.** Two threads deadlock, each holding one of two mutexes and
waiting for the other, and both threads' stack traces show they were inside
what looks like correctly written scoped-lock code. **Cause.** Two different
call sites acquire the same pair of mutexes in opposite order, each using a
correct single-mutex Guard for each mutex individually. single-mutex Scoped
Locking provides zero protection against this, because it was never designed
to. **Fix.** Replace the pair of single-mutex guards with one multi-mutex
guard constructor where the language provides one (`std::scoped_lock` in
C++17), which uses a deadlock-avoidance algorithm across the whole set
regardless of the order the mutexes are passed in. Where no such
multi-mutex form exists, establish and enforce, by convention or by a
runtime lock-order checker, a single global acquisition order for every pair
of mutexes that can ever be held simultaneously.

**Symptom.** A function that was fast in isolation becomes a throughput
bottleneck once called concurrently, even though its logic touches shared
state only briefly. **Cause.** The Guard's scope was drawn around the whole
function body, including an I/O call, an allocation, a logging statement, or
other work that does not touch the protected state, because it was easier to
declare the guard once at the top of the function than to work out exactly
which statements need protection. **Fix.** Narrow the scope to only the
statements that actually read or write the shared state, moving the
expensive, unrelated work either before the guard is constructed or after it
is destroyed (an inner block in C++, Rust, or Java. an immediately invoked
closure in Go). If the expensive work genuinely needs a value computed from
the protected state, copy that value out inside the narrow scope and use the
copy after the guard has gone out of scope.

**Symptom.** A guard's lock is manually released early with an explicit call
inside the block, and later, at the natural end of the block, the program
crashes or throws with a message about releasing a lock that is not held.
**Cause.** The Guard's destructor runs regardless of exit path at scope exit,
so an explicit manual release inside the scope, followed by the normal
scope-exit release, releases the same lock twice. some libraries treat this
as undefined behaviour, some throw, some (Rust's `Mutex`, via explicit
`drop(guard)`) handle it correctly because dropping consumes the guard and
there is nothing left to release a second time, and others (a hand-rolled
C++ Guard with a public early-release method) require the author to remember
to mark the guard as already released so the destructor becomes a no-op.
**Fix.** Prefer language and library forms where an early release consumes
the guard object entirely (Rust's `drop(guard)`, or `std::unique_lock`'s
manual-release method paired with its own internal "am I currently locked"
tracking, which is precisely the extra bookkeeping `std::lock_guard`
deliberately omits for performance). If a hand-rolled Guard must support
early release, give it an explicit "already released" flag checked by the
destructor before it acts on the underlying lock, rather than assuming early
release is rare enough to ignore.

**Symptom.** A recursive function, or a function that calls another function
which happens to acquire the same lock again on the same thread, deadlocks
against itself on the very first call. **Cause.** The Guard wraps a plain,
non-reentrant mutex, and the same thread attempts to acquire it a second time
while already holding it. This is not a bug in Scoped Locking at all, the
Guard behaves exactly as documented, acquiring on construction, but it
surfaces as a Scoped Locking failure because the guard is the last thing the
stack trace shows blocking. **Fix.** Either restructure the code so the lock
is acquired exactly once per logical operation (extracting an
already-locked-assumes internal helper that the public, locking entry point
calls), or, where genuinely necessary, switch the underlying Lock type to a
reentrant variant (`std::recursive_mutex`, Java's `ReentrantLock`, which
tracks a per-thread hold count), understanding that reentrant locks are
themselves a design smell in most codebases and are reached for as a last
resort, not a default.

## 12. Trade-off matrix

| Property | Scoped Locking | Bare `lock()`/`unlock()` pair | Strategized Locking alone | Monitor Object |
|---|---|---|---|---|
| Guarantees release on exception or early return | Yes, by language mechanism | No, requires manual try/finally at every call site | Depends entirely on how the caller manages the chosen lock | Yes, implicitly, but only for the whole method |
| Expresses hand-off locking (acquire on one thread, release on another) | No | Yes | Yes, if the underlying lock supports it | No, the monitor's own call convention owns acquisition and release |
| Protects against lock-order deadlock across two locks | Only the multi-mutex constructor form does. single-mutex form does not | No, entirely the caller's responsibility | No, orthogonal concern | Typically not applicable, a monitor usually holds one intrinsic lock |
| Lets the critical section be narrower than a whole method | Yes, scope can be any nested block | Yes, at the cost of manual discipline at every narrower boundary | Yes, orthogonal, this is about which lock type is used, not how narrowly it is held | No, the whole method body is the critical section by construction |
| Visibility of the critical section's extent to a reader | High, the guard's declaration marks the start and its enclosing braces mark the end | Low, requires reading every exit path to find every release call | Unaffected, this pattern is orthogonal | High, the method boundary is the extent |
| Runtime overhead versus the underlying lock alone | Effectively none in a language with zero-cost destructors (C++, Rust). one extra stack slot | None beyond the underlying lock itself | None, this pattern selects the lock type, it adds no wrapper | None beyond the underlying intrinsic lock |

## 13. Related and incompatible patterns

**Strategized Locking.** The sibling pattern from the same 1999 paper that
Scoped Locking is most often confused with, because both are described
together and both are about locking discipline. Strategized Locking answers a
different question, which concrete lock type (a real mutex, a null no-op
lock for single-threaded builds, a recursive mutex) a class should use, made
a template or generic parameter so the choice is made once at the type level
rather than scattered through the class's methods. Scoped Locking answers how
a lock, whichever type Strategized Locking selected, is acquired and released
correctly around a critical section. The two compose directly. a
Strategized-Locking class typically exposes its chosen Lock type, and every
method inside it uses Scoped Locking to acquire that Lock for the duration of
the method's critical section.

**Thread-Safe Interface.** A pattern, also from POSA2, that separates a
class's externally-callable, locking methods from internal, already-locked
helper methods that assume the lock is already held and must never acquire
it themselves. Thread-Safe Interface is precisely the design discipline that
avoids the recursive self-deadlock failure mode described in Dimension 11. an
externally-callable method uses Scoped Locking to acquire the lock once, then
calls internal helpers that touch the protected state directly, with no
second acquisition anywhere in the call graph.

**Double-Checked Locking Optimization.** A related, narrower pattern for
avoiding the cost of acquiring a lock on every call to a lazily-initialized
accessor by checking the initialization condition once outside the lock and
again inside it. It uses Scoped Locking (or the underlying language's atomic
initialization primitives, which have largely superseded it) for the inner,
guarded initialization step, but the double-check structure itself is a
distinct optimization concerned with avoiding lock acquisition in the common
case, not with lock release correctness.

**Monitor Object.** An architecturally different approach to the same
underlying problem, where synchronization is built into the object's method
dispatch itself rather than expressed explicitly inside method bodies. A
class implemented as a Monitor Object has no visible Guard declarations at
all, because every public method is implicitly synchronized by the language
or framework (Java's `synchronized` keyword on a method, for instance, is a
Monitor Object mechanism, not a Scoped Locking one, even though the JVM
implements it with essentially the same acquire-on-entry,
release-on-exit-including-exception guarantee under the hood). Choosing
Monitor Object instead of hand-written Scoped Locking inside every method is
a legitimate, higher-level alternative when every method on the class needs
the same, whole-method critical section, and Scoped Locking remains the right
tool the moment a class needs a critical section narrower than an entire
method, or needs to hold two different locks across different methods.

**Active Object.** A different concurrency pattern entirely, decoupling
method invocation from method execution by queuing requests and running them
on a separate execution thread. Active Object often uses Scoped Locking
internally, to protect its activation queue against concurrent enqueue calls
from multiple client threads, but the pattern itself solves a different
problem (asynchronous method execution) than Scoped Locking solves (correct
lock release), and the two are frequently found nested, an Active Object's
internal queue guarded by a Scoped Locking guard, without being the same
pattern at different scales.

**Reactor.** Not directly related in structure, but worth naming because
single-threaded Reactor implementations are the clearest illustration of
Dimension 4's non-applicability case for locking generally. inside a
single-threaded event loop that never runs two callbacks concurrently, no
mutex, scoped or otherwise, is needed at all to protect state only that loop
touches, and adding one is pure overhead. the moment a Reactor is paired with
a worker thread pool that touches the same state the event loop thread
touches, Scoped Locking becomes applicable again at exactly the boundary
where the two threads meet.

## 14. Refactoring path in and out

Introducing Scoped Locking into code that currently uses bare `lock()` and
`unlock()` calls proceeds in small, verifiable steps.

1. Identify every call site that currently pairs an explicit acquire call
   with a later, hand-written release call, and for each one, confirm there
   is exactly one logical exit from the protected region, even if there are
   several syntactic exits (multiple `return` statements, a `throw`).
2. For the language in use, introduce the appropriate scope-bound guard type
   at the acquisition point, replacing the explicit acquire call with the
   guard's constructor, and delete the corresponding explicit release call
   entirely, trusting the guard's destructor (or `defer`, or `with`, or
   `try`/`finally`) to perform it.
3. Where the original manual code had extra release calls scattered across
   multiple exit paths, specifically because a single release call at the
   bottom of the function could not be reached from every path, delete
   every one of them. this is the concrete signal the refactoring is
   correctly removing duplicated, error-prone release logic rather than
   merely adding a decoration on top of it.
4. Run the existing test suite under a thread sanitizer or race detector
   (ThreadSanitizer for C++ and Go, Rust's borrow checker plus, if unsafe
   code is involved, Miri, or a stress test that forces the exceptional exit
   path deliberately) before and after the change, to confirm no new
   deadlock or missed-release regression was introduced and, ideally, that a
   previously-possible leaked-lock bug on the exception path is now provably
   impossible.
5. If the function needs to hold more than one lock, check whether the
   language's standard library offers a multi-mutex constructor form
   (`std::scoped_lock` in C++17) before writing two separate single-mutex
   guards back to back, because two separate guards reintroduce the
   lock-ordering deadlock risk the multi-mutex form exists to remove.

Removing Scoped Locking, or more precisely, replacing it with a coarser or
different synchronization design, is a decision to make deliberately rather
than a refactoring most code should ever need to do, but the situations where
it happens follow a recognisable path.

1. If profiling shows contention on a lock that Scoped Locking makes trivial
   to acquire and release correctly, but the contention itself is the
   problem, consider first narrowing the guard's scope (per Dimension 11's
   granularity failure mode) before abandoning locking altogether. this
   alone resolves the majority of contention issues attributed to "the
   lock", which are usually attributable to what the lock protects being too
   coarse, not to the guard mechanism.
2. If the protected state reduces to a single scalar or pointer that fits in
   a machine word, replace the mutex and its guard with a lock-free atomic
   type native to the language (`std::atomic`, Rust's `std::sync::atomic`,
   Go's `sync/atomic`), which removes the guard, the mutex, and the
   possibility of contention-driven blocking entirely for that one value.
3. If the design repeatedly needs the same whole-method critical section on
   every public entry point of a class, consider migrating the class to a
   Monitor Object design and removing the per-method Guard declarations in
   favor of the language's built-in synchronized-method mechanism, if one
   exists and matches the class's needs exactly.
4. If a genuine hand-off requirement emerges, where thread A must acquire a
   lock that thread B releases, do not attempt to force this into a Scoped
   Locking shape by widening a guard's lifetime unnaturally (for example
   storing a guard in a heap-allocated box and passing ownership of the box
   between threads). This works in some languages but produces code whose
   locking discipline is no longer visible at either call site, defeating
   the readability benefit Dimension 10 credits the pattern with. it is
   often clearer to fall back to an explicit lock handle for that one path
   and document why.

## 15. Testing and verification

Scoped Locking makes the release half of a lock's lifecycle mechanically
guaranteed, which removes an entire class of test case, the "does this
function leak the lock when it throws" test, because the answer is now a
property of the language runtime rather than a property of the function
under test, and does not need re-verification per call site once the
underlying guard type itself is trusted. What remains genuinely worth testing
is everything the pattern does not automatically guarantee.

- **Deadlock tests under concurrent contention.** Spawn multiple threads (or
  goroutines, or async tasks) that acquire the same guard-protected resource
  under load, including at least one thread that deliberately triggers the
  exceptional exit path (throwing, panicking, or returning early) while
  holding the guard, and assert that every other waiting thread still
  eventually acquires the lock. A thread that never gets unblocked after the
  exceptional-exit thread's guard was supposed to release is the direct,
  observable symptom of a broken or bypassed guard.
- **Lock-order tests for multi-mutex critical sections.** Where a function
  acquires two or more locks, write a test that has two threads acquire the
  same two locks in opposite order and confirm the program does not
  deadlock, which is a useful test only if a multi-mutex guard or an
  explicit acquisition-order convention is actually in place. this test is
  the direct verification of the fix for the lock-order failure mode in
  Dimension 11.
- **Race detector runs, not assertions.** ThreadSanitizer (for C++, Go, and
  several other compiled languages), Rust's compile-time borrow checker
  (which rejects the majority of data races statically before a test even
  runs) plus Miri for unsafe code, and Java's `jcstress` for JVM-level
  memory-visibility bugs are the tools of record here, because a data race
  is, by definition, a bug that a single deterministic test run can fail to
  observe. relying on assertions inside a manually-run concurrent test to
  catch a race is unreliable in a way that a race detector instrumenting
  every memory access is not.
- **Test the un-guarded internal helper path directly.** Where Thread-Safe
  Interface separates a public, guarded entry point from an internal,
  already-locked helper (Dimension 13), the internal helper's logic can and
  should be unit tested directly, without any locking machinery at all,
  because its correctness with respect to the shared state's invariants is
  entirely orthogonal to whether the lock around it was acquired correctly,
  and testing it directly is both faster and gives a clearer failure
  signal than testing it only through the locked public entry point.
- **Assert the guard's own non-copyability at compile time, not at
  runtime.** In a language where the compiler enforces it (C++'s deleted
  copy constructor, Rust's ownership rules), no runtime test is needed for
  the double-release failure mode, the compiler rejects the offending code
  before it exists. In a language that cannot enforce this statically, a
  targeted unit test that constructs a guard, manually triggers a second
  release path, and asserts the resulting behaviour (an exception, a no-op,
  whichever the guard type documents) is the only way to pin the
  double-release contract down.

## 16. Observability signals

A Scoped Locking guard is, by design, invisible at runtime in the common
case, which is exactly the property that makes it hard to observe when
something is wrong. the signals worth instrumenting are proxies for the
guard's behaviour rather than the guard itself.

- **Lock hold-time histograms.** Instrument the moment a guard is
  constructed and the moment it is destroyed (many languages' mutex types
  expose hooks or wrappers for this, and Abseil's `Mutex` ships built-in
  contention profiling for exactly this reason). A healthy system shows a
  tight, low-variance hold-time distribution matching the size of the
  critical section the guard was drawn around. A distribution with a long
  tail, or a distribution that drifts wider over a deploy, is the direct
  signal of the granularity failure mode in Dimension 11, a scope that grew
  to include unrelated, unbounded-latency work.
- **Wait-time versus hold-time ratio.** The proportion of time threads spend
  blocked waiting to acquire a guard's underlying lock, relative to the time
  the lock is actually held once acquired, is the standard contention
  signal. a healthy system keeps this ratio low. a system where wait time
  dwarfs hold time under load is a system where either the lock is too
  coarse (protecting more state, or more callers, than it needs to) or
  contention has genuinely outgrown a single mutex and needs sharding,
  a reader-writer lock, or a different data structure entirely.
- **Deadlock and stuck-thread detection.** A thread-dump or goroutine-dump
  snapshot showing multiple threads blocked inside a lock's acquire call,
  each waiting on a lock another one of the blocked threads holds, is the
  direct, unambiguous signal of the lock-order deadlock failure mode.
  Production systems that use many mutexes benefit from periodic automated
  thread-dump sampling specifically to catch this pattern before an on-call
  engineer has to diagnose it live from a single incident's stack traces.
- **Reentrant-lock hold-count metrics.** Where a codebase deliberately uses
  a reentrant lock (Java's `ReentrantLock.getHoldCount()`, exposed directly
  for this purpose), an unexpectedly high or steadily climbing hold count on
  a single thread is the signal of the recursive self-locking failure mode
  in Dimension 11 escalating from "works, but is fragile" toward "will
  eventually overflow or mask a real bug in the calling pattern."
- **Poison and panic-under-lock counters, Rust specifically.** Because
  `std::sync::Mutex` in Rust poisons on a panic while the guard is held,
  the rate of `PoisonError` returns from `lock()` calls in production is a
  direct, built-in observability signal for "a thread panicked while
  holding this specific lock," with no additional instrumentation required
  beyond logging the `Err` branch, something the equivalent C++ or Java
  guard types give no comparable signal for at all.

## 17. Security and privacy implications

Scoped Locking's own security surface is narrow, because the pattern is a
lifecycle-correctness mechanism for a resource (a lock) that holds no data of
its own, and this dimension is analytical rather than sourced from a specific
document.

The pattern's main indirect security relevance is that it removes a
denial-of-service vector rather than a confidentiality or integrity one. a
lock leaked on an exception path, the exact bug Scoped Locking exists to
prevent, means every subsequent request that needs that lock hangs forever,
which is a straightforward availability failure an attacker able to trigger
the exception path (for example, by supplying input that causes a validation
throw inside a critical section) could exploit deliberately to take a service
down without needing any other vulnerability. Reliable use of Scoped Locking
closes this specific path, but only for the exit-path-correctness half of the
problem. it does nothing to prevent an attacker from causing legitimate,
heavy contention on a correctly-guarded lock by sending many requests that
each hold it briefly, which remains a capacity-planning and rate-limiting
concern outside the pattern's scope.

A secondary, more subtle concern is information leakage through timing. the
hold-time of a lock protecting security-sensitive branching logic (for
example, a lock guarding a credential comparison or an authorization check)
can, in principle, leak information about which branch executed through
observable contention on that same lock from an unrelated thread. this is a
timing side channel that exists independently of whether the lock is
acquired through Scoped Locking or a bare `lock()`/`unlock()` pair, and
Scoped Locking neither introduces nor mitigates it. code with this specific
threat model needs constant-time comparison primitives and careful attention
to what runs inside any critical section at all, locking discipline aside.

Finally, a guard object that wraps a lock protecting sensitive data (a
cryptographic key, a session token) should not itself be logged, serialized,
or included in a debug dump by a generic tracing or reflection mechanism that
walks arbitrary stack-local objects, because doing so risks exposing the
pointer or reference to the protected resource, or the protected resource
itself if the guard's `Deref` implementation makes the data trivially
reachable from the guard value (as it deliberately does in Rust's
`MutexGuard`, for ergonomic reasons unrelated to security). this is a general
caution about any RAII wrapper's interaction with generic debugging tooling,
not a property specific to locking.

## 18. References

- Douglas C. Schmidt, "Strategized Locking, Thread-safe Decorator, and Scoped
  Locking. Patterns and Idioms for Simplifying Multi-threaded C++
  Components," *C++ Report*, SIGS, Volume 11, Number 9, September 1999.
  Listed with abstract and PDF link at
  https://www.dre.vanderbilt.edu/~schmidt/patterns-ace.html, verified
  2026-08-13. PDF served live at
  https://www.dre.vanderbilt.edu/~schmidt/PDF/locking-patterns.pdf, verified
  2026-08-13.
- Douglas C. Schmidt, Michael Stal, Hans Rohnert, Frank Buschmann,
  *Pattern-Oriented Software Architecture, Volume 2. Patterns for Concurrent
  and Networked Objects*, Wiley, 2000. Authors and publication year confirmed
  at https://en.wikipedia.org/wiki/Pattern-Oriented_Software_Architecture,
  verified 2026-08-13.
- Microsoft Learn, "lock_guard Class,"
  https://learn.microsoft.com/en-us/cpp/standard-library/lock-guard-class,
  verified 2026-08-13.
- Microsoft Learn, "scoped_lock Class,"
  https://learn.microsoft.com/en-us/cpp/standard-library/scoped-lock-class,
  verified 2026-08-13.
- The Rust Programming Language, standard library documentation,
  `std::sync::Mutex`, https://doc.rust-lang.org/std/sync/struct.Mutex.html,
  verified 2026-08-13.
- The Go Project, package documentation, `sync`,
  https://pkg.go.dev/sync, verified 2026-08-13.
- Python Software Foundation, *Python Standard Library* documentation,
  `threading`, https://docs.python.org/3/library/threading.html, verified
  2026-08-13.
- Oracle, Java Platform SE 8 API Specification,
  `java.util.concurrent.locks.ReentrantLock`,
  https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/locks/ReentrantLock.html,
  verified 2026-08-13.
- Google, Abseil C++ Library, "Mutex Guides,"
  https://abseil.io/docs/cpp/guides/synchronization, verified 2026-08-13.
- DOCGroup, ACE_TAO source repository,
  https://github.com/DOCGroup/ACE_TAO, verified 2026-08-13.

## Code examples

### Rust

```rust
use std::sync::{Arc, Mutex};
use std::thread;

struct Account {
    balance: Mutex<i64>,
}

impl Account {
    fn new(balance: i64) -> Self {
        Account { balance: Mutex::new(balance) }
    }

    fn transfer_out(&self, amount: i64) -> Result<(), &'static str> {
        let mut balance = self.balance.lock().unwrap();
        if *balance < amount {
            return Err("insufficient funds");
        }
        *balance -= amount;
        Ok(())
    }

    fn deposit(&self, amount: i64) {
        let mut balance = self.balance.lock().unwrap();
        *balance += amount;
    }

    fn snapshot(&self) -> i64 {
        *self.balance.lock().unwrap()
    }
}

fn main() {
    let account = Arc::new(Account::new(1000));
    let mut handles = vec![];

    for _ in 0..8 {
        let account = Arc::clone(&account);
        handles.push(thread::spawn(move || {
            account.deposit(10);
            let _ = account.transfer_out(5);
        }));
    }

    for h in handles {
        h.join().unwrap();
    }

    println!("final balance: {}", account.snapshot());
}
```

The guard returned by `lock()` is dropped at the end of each method's block,
releasing the mutex there. no explicit release call appears anywhere in this
listing. Compiled and run with `rustc`. output `final balance: 1040`.

### Go

```go
package main

import (
	"fmt"
	"sync"
)

type Account struct {
	mu      sync.Mutex
	balance int64
}

func NewAccount(balance int64) *Account {
	return &Account{balance: balance}
}

func (a *Account) TransferOut(amount int64) error {
	a.mu.Lock()
	defer a.mu.Unlock()

	if a.balance < amount {
		return fmt.Errorf("insufficient funds")
	}
	a.balance -= amount
	return nil
}

func (a *Account) Deposit(amount int64) {
	a.mu.Lock()
	defer a.mu.Unlock()
	a.balance += amount
}

func (a *Account) Snapshot() int64 {
	a.mu.Lock()
	defer a.mu.Unlock()
	return a.balance
}

func main() {
	account := NewAccount(1000)
	var wg sync.WaitGroup

	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			account.Deposit(10)
			_ = account.TransferOut(5)
		}()
	}

	wg.Wait()
	fmt.Println("final balance:", account.Snapshot())
}
```

Each method pairs `Lock()` with an immediately-following `defer ... Unlock()`,
the idiomatic Go form of Scoped Locking described in Dimension 8. Compiled and
run with `go run`. output `final balance: 1040`.

### Python

```python
import threading


class Account:
    def __init__(self, balance):
        self._lock = threading.Lock()
        self._balance = balance

    def transfer_out(self, amount):
        with self._lock:
            if self._balance < amount:
                raise ValueError("insufficient funds")
            self._balance -= amount

    def deposit(self, amount):
        with self._lock:
            self._balance += amount

    def snapshot(self):
        with self._lock:
            return self._balance


def worker(account):
    account.deposit(10)
    try:
        account.transfer_out(5)
    except ValueError:
        pass


def main():
    account = Account(1000)
    threads = [threading.Thread(target=worker, args=(account,)) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("final balance:", account.snapshot())


if __name__ == "__main__":
    main()
```

The `with self._lock:` block is Python's context-manager form of the same
idiom, acquiring on entry and releasing on exit, including the exit forced by
the `raise` inside `transfer_out`. Run with `python3`. output
`final balance: 1040`.

### TypeScript

```typescript
class AsyncMutex {
  private locked = false;
  private waiters: Array<() => void> = [];

  async withLock<T>(fn: () => Promise<T> | T): Promise<T> {
    await this.acquire();
    try {
      return await fn();
    } finally {
      this.release();
    }
  }

  private acquire(): Promise<void> {
    if (!this.locked) {
      this.locked = true;
      return Promise.resolve();
    }
    return new Promise((resolve) => this.waiters.push(resolve));
  }

  private release(): void {
    const next = this.waiters.shift();
    if (next) {
      next();
    } else {
      this.locked = false;
    }
  }
}

class Account {
  private balance: number;
  private readonly mutex = new AsyncMutex();

  constructor(balance: number) {
    this.balance = balance;
  }

  transferOut(amount: number): Promise<void> {
    return this.mutex.withLock(() => {
      if (this.balance < amount) {
        throw new Error("insufficient funds");
      }
      this.balance -= amount;
    });
  }

  deposit(amount: number): Promise<void> {
    return this.mutex.withLock(() => {
      this.balance += amount;
    });
  }

  snapshot(): Promise<number> {
    return this.mutex.withLock(() => this.balance);
  }
}

async function main() {
  const account = new Account(1000);
  const tasks: Array<Promise<void>> = [];
  for (let i = 0; i < 8; i++) {
    tasks.push(
      (async () => {
        await account.deposit(10);
        try {
          await account.transferOut(5);
        } catch {
          // ignore
        }
      })()
    );
  }
  await Promise.all(tasks);
  console.log("final balance:", await account.snapshot());
}

main();
```

`withLock` is the closure-based analogue of `lock_guard` described in
Dimension 8 for a single-threaded, async-interleaved runtime. the `finally`
block is what guarantees the release runs whether the callback resolves or
throws. Compiled with `tsc --strict` and run with `node`. output
`final balance: 1040`.

A Java sample using an `AutoCloseable`-wrapped `ReentrantLock`, the idiom
described in Dimension 8, was written and reviewed for correctness but could
not be compiled on this machine. `javac` and `java` are on `PATH` but report
"Unable to locate a Java Runtime," so no installed JDK was available to
verify it. The Java variant is described in prose in Dimension 8 instead of
being included here as unverified code.
