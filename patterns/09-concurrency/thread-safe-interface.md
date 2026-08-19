---
name: Thread-Safe Interface
slug: thread-safe-interface
family: 09-concurrency
category: Concurrency
aliases: [Synchronized Interface, Guarded Interface, Locked Boundary]
first_described: "Schmidt 1999; Schmidt, Stal, Rohnert, Buschmann 2000"
maturity: canonical
related: [monitor-object, scoped-locking, double-checked-locking, active-object, strategized-locking]
incompatible_with: []
verified: 2026-08-02
---

# Thread-Safe Interface

## 1. Name, aliases, and lineage

The canonical name is Thread-Safe Interface. It is documented as one of
seventeen named patterns in Douglas C. Schmidt, Michael Stal, Hans Rohnert,
and Frank Buschmann, *Pattern-Oriented Software Architecture, Volume 2.
Patterns for Concurrent and Networked Objects*, John Wiley and Sons, 2000,
where it sits in the Synchronization Patterns section alongside Scoped
Locking, Strategized Locking, and Double-Checked Locking Optimization
([POSA2 pattern list, Vanderbilt DRE Lab](https://www.dre.vanderbilt.edu/~schmidt/POSA/POSA2/),
verified 2026-08-02).

The pattern predates the book. Douglas C. Schmidt published the idea two
years earlier in a C++ trade journal, packaged together with two closely
related synchronization idioms in "Strategized Locking, Thread-Safe
Interface, and Scoped Locking. Patterns and Idioms for Simplifying
Multi-threaded C++ Components," *C++ Report*, SIGS Publications, Vol. 11,
No. 9, September 1999 ([ACE papers index, Vanderbilt DRE Lab](https://www.dre.vanderbilt.edu/~schmidt/ACE-papers.html),
verified 2026-08-02). That paper title is itself a useful map of the family.
Strategized Locking decides which lock type an object uses, a topic covered
in its own entry in this repository. Thread-Safe Interface decides where the
lock boundary sits inside one object's method set. Scoped Locking decides
how a single acquisition and release is written so it cannot leak, see
[scoped-locking](../09-concurrency/scoped-locking.md). The three were
designed as one coherent toolkit for building thread-safe C++ classes on top
of the ACE (Adaptive Communication Environment) network programming toolkit
that Schmidt's group at Washington University in St. Louis, and later
Vanderbilt University, built and maintained.

No competing name has displaced it in the literature this pattern's own
authors produced, but the concept surfaces under several informal labels in
practitioner writing and in code comments, among them "synchronized wrapper
methods," "the locked and unlocked split," and "public locks, private
assumes locked." None of these are attested in a peer-reviewed or
editorially reviewed source the way POSA2 and the 1999 paper are, so this
entry treats them as informal aliases rather than as a second canonical
name. The pattern is frequently discussed in the same breath as Monitor
Object, and the two are close cousins, but POSA2 treats them as two
separate patterns with two separate problem statements, see dimension 13,
and this entry keeps that separation.

## 2. Problem and context

An object holds mutable state that more than one thread can reach at the
same time, and the object exposes more than one public operation on that
state. Somewhere between no locking at all and a lock inside every method,
including the ones other methods call, a design decision has to be made
about exactly which methods acquire the lock and which methods assume it is
already held.

The naive first attempt is to put the lock acquisition inside every method
on the class, public and private alike, because that reads as maximally
safe. It works until one method needs to call a sibling method on the same
object. Two failure shapes follow from that naive attempt, and both are
visible symptoms a working engineer recognizes on sight, not abstractions.

The first shape is self-deadlock. Most native lock primitives that a
systems language exposes directly to the operating system are non-reentrant
by default. A POSIX `pthread_mutex_t` created with the default attributes is
non-recursive, and David R. Butenhof, *Programming with POSIX Threads*,
Addison-Wesley, 1997, describes the default mutex type and the
`PTHREAD_MUTEX_RECURSIVE` attribute that must be requested explicitly to get
recursive behavior; the default is not recursive. A C++11 `std::mutex` is
likewise non-recursive by the language standard; only `std::recursive_mutex`
recurses, at extra bookkeeping cost per acquisition. If every method locks
the mutex on entry, and method A calls method B on the same object while
still holding the lock A took, the thread blocks on its own mutex forever.
The program hangs, and the hang is data-dependent, so it frequently
survives unit tests that never happen to exercise the cross-call path and
only appears once the two call paths meet in production under real traffic.

The second shape is not a hang but a tax. Some languages do provide a
reentrant lock by default, most visibly Java's intrinsic monitor entered by
the `synchronized` keyword, and Python's `threading.RLock`. Reentrancy
solves the deadlock, but every acquisition and release still costs
something, a memory fence at minimum and often an atomic compare-and-swap
or a syscall under contention. A public method that internally calls three
sibling methods, each separately synchronized, pays the acquisition cost
four times for one logical operation, when one acquisition covering the
whole operation would have sufficed. On a hot path this shows up directly
as measured latency and, under contention, as convoy behavior where threads
queue behind a lock they re-enter repeatedly instead of holding once.

The context in which Thread-Safe Interface is the right answer has three
concrete markers. The class has real, non-trivial internal composition,
meaning its own methods legitimately call each other to share logic rather
than duplicate it. The class is meant to be usable from more than one
thread concurrently without the caller doing any locking of its own; the
class itself is the unit of thread safety, not the code around it. And the
underlying lock primitive the class is built on is either non-reentrant by
default, or reentrant but expensive enough per call that redundant
acquisition is measurable. When all three hold, the fix is not to make the
lock reentrant and accept the tax, and it is not to never call your own
methods and accept the duplication. The fix is to draw one boundary.

## 3. Forces

- **Correctness through mutual exclusion versus locking overhead.** Every
  acquisition of a contended lock costs cycles even in the uncontended fast
  path, and costs a great deal more under contention. A design that
  minimizes acquisition count per logical operation, not merely acquisition
  correctness, wins on throughput without giving up safety.
- **Composability of methods versus a flat, everything-locks API.** A class
  with rich internal reuse between its own methods needs some methods that
  can be called while the lock is already held. A class where every public
  method is independent and self-contained does not need this pattern at
  all, and forcing the split onto it is needless ceremony, see dimension 4.
- **Deadlock avoidance versus cheap, non-recursive locks.** Recursive locks
  buy safety on re-entry at a fixed per-acquisition cost increase, because
  the lock must track an owning thread identity and a hold count rather
  than a bare boolean. Thread-Safe Interface buys the same safety by
  convention and by boundary placement instead, keeping the cheaper
  non-recursive lock, at the cost of programmer discipline that the
  compiler, in most languages, cannot check.
- **API surface honesty versus internal flexibility.** A caller of the
  public interface should never need to know or care whether the object is
  currently locked. The internal methods are allowed to assume a fact about
  the object's state, that the lock is held, that the public methods must
  never assume, and that split has to be visible enough in the code,
  through naming or access modifiers, that a future maintainer does not
  blur it by accident.
- **Static enforcement versus manual discipline.** In most languages this
  pattern lives entirely in naming convention and code review discipline; a
  developer can call an internal method from outside the object, or forget
  to acquire the lock before calling one, and nothing stops them at compile
  time. A minority of languages, notably Rust, can make the violation a
  compile error by construction, see dimension 8, and that changes which
  force matters most in the design conversation.

## 4. Applicability and non-applicability

Reach for Thread-Safe Interface when all of the following hold together.

- The class is a shared, mutable object reachable from more than one
  thread, and the class itself, not its callers, is responsible for its own
  internal consistency.
- The class's own methods call each other to share logic, so a purely flat
  design where every method locks and none call each other would force
  duplicated logic to avoid the self-call.
- The lock primitive available is non-reentrant, or is reentrant but
  expensive enough per acquisition that repeated acquisition on one logical
  call is a measured or reasonably anticipated cost.
- The object's invariants require that a public operation be atomic with
  respect to every other public operation, not merely internally consistent
  within itself.

Do not reach for it, and treat any of the following as a real reason to
pick something else, not a shortcut.

- **The object has no internal composition between its own methods.** If no
  method ever calls a sibling method, there is no self-call to protect
  against and no redundant acquisition to eliminate. A flat design where
  every public method locks is simpler and equally correct. Adding an
  internal unguarded layer here is unjustified indirection.
- **The runtime already avoids shared mutable state.** In an actor model,
  Erlang or Elixir processes, or Akka-style actors, or in a
  channel-and-goroutine design in the style Go's own concurrency guidance
  recommends, commonly summarized as favoring communicating over sharing
  memory, there is no shared object with a lock boundary to draw in the
  first place. Applying this pattern there is solving a problem the
  architecture already avoided.
- **The object is confined to one thread.** UI toolkits that require all
  mutation to happen on a single thread, such as the main thread in a
  desktop GUI framework or the main queue in a mobile UI framework, need no
  lock and no internal-external split at all; thread confinement is a
  cheaper and stronger guarantee than any lock discipline.
- **A cheap, well-tested reentrant lock is genuinely available and the
  call frequency is low.** Java's intrinsic `synchronized` monitors are
  reentrant by language guarantee, and for many classes the overhead of
  reentering a lock the same thread already holds is immaterial next to the
  work the method does. Choosing plain, fully synchronized methods here and
  accepting the reentrant lock's small tax is a legitimate simpler design,
  not a violation of best practice; forcing the split is premature
  optimization when nothing has measured it as a bottleneck.
- **The object needs an operation to be atomic across two or more separate
  top-level calls made by the caller**, for example checking a balance,
  then deciding, then withdrawing, performed as three separate client
  calls. No placement of the internal-external boundary inside the object
  can make a sequence of independent public calls atomic with respect to
  other threads; that is a different problem, usually solved by exposing a
  single compound operation, by an explicit external lock the caller holds
  across the sequence, or by an optimistic retry loop.
- **The datatype is a good fit for a lock-free or wait-free algorithm.**
  Thread-Safe Interface is a locking pattern through and through. Where a
  compare-and-swap loop or a lock-free queue design, Michael and Scott's
  algorithm being the canonical example, meets the correctness and progress
  requirements, it avoids locking overhead entirely rather than merely
  minimizing it, and belongs to a different pattern family.

## 5. Structure

- **Client.** Any thread that calls operations on the shared object through
  its public surface. The client never acquires or releases the object's
  internal lock directly and never calls an internal operation directly.
- **Guarded Operation.** A public, or otherwise externally reachable,
  method. Before doing any real work, its body does exactly one thing
  first. It acquires the object's lock, and releases it again on every
  exit path, including exceptional ones. Once the lock is held, it
  performs its logic by calling one or more Unguarded Operations, never by
  re-entering another Guarded Operation.
- **Unguarded Operation.** A private or otherwise internally reachable
  method that implements the actual behavior. It assumes, as a documented
  precondition, that the object's lock is already held by the calling
  thread. It never itself attempts to acquire the lock. It may call other
  Unguarded Operations freely, because the precondition is transitive
  across the internal call graph.
- **Guard.** The synchronization primitive that the Guarded Operations
  manage. Examples include a mutex, an intrinsic monitor, a Rust `Mutex<T>`
  and its guard type, or any object playing the same role. In its simplest
  form this is the object being managed by Scoped Locking, see dimension 8
  and dimension 13, so that an exception or an early return cannot leave it
  held.
- **Protected State.** The mutable fields the object exists to manage.
  Protected State is touched only from Unguarded Operations, never
  directly from a Guarded Operation's own body beyond the call into the
  unguarded layer, so there is exactly one place in the class where a
  reader needs to reason about the invariant holding.

## 6. ASCII structure diagram

```
+-----------------------------------------------------------------+
|                        Thread-Safe Object                       |
|                                                                   |
|   +-----------------------+       +-----------------------+      |
|   |    Guarded Operation  |       |    Guarded Operation   |      |
|   |         put(x)        |       |         take()         |      |
|   |  1. lock.acquire()    |       |  1. lock.acquire()     |      |
|   |  2. call unguarded    |       |  2. call unguarded     |      |
|   |  3. lock.release()    |       |  3. lock.release()     |      |
|   +-----------+-----------+       +-----------+-----------+      |
|               |                               |                  |
|               v                               v                  |
|   +------------------------------------------------------+       |
|   |               Unguarded Operations                    |      |
|   |  put_(x)      take_()      is_full_()   is_empty_()   |      |
|   |  (assume lock held, never acquire it, may call         |      |
|   |   each other)                                           |      |
|   +---------------------------+----------------------------+       |
|                               |                                  |
|                               v                                  |
|                     +-------------------+                        |
|                     |  Protected State  |                        |
|                     |  (buffer, count)  |                        |
|                     +-------------------+                        |
|                                                                   |
|   +-------------------+                                          |
|   |       Guard       |  <--- acquired/released only by          |
|   |  (mutex, monitor) |       Guarded Operations                 |
|   +-------------------+                                          |
+-----------------------------------------------------------------+
              ^
              |  calls only Guarded Operations, never
              |  the unguarded layer directly
    +-------------------+       +-------------------+
    |     Client A      |       |     Client B      |
    | (thread 1)        |       | (thread 2)        |
    +-------------------+       +-------------------+
```

## 7. Dynamics

The everyday call path shows one client, one call, and no self-call
involved.

```
Client         Guarded.put(x)      Guard          Unguarded.put_(x)
  |                  |               |                     |
  |--- put(x) ------>|               |                     |
  |                  |-- acquire() ->|                     |
  |                  |<-- granted ---|                     |
  |                  |----------------- put_(x) ---------->|
  |                  |                |    (mutates state, |
  |                  |                |     may call        |
  |                  |                |     is_full_())     |
  |                  |<---------------------- returns ------|
  |                  |-- release() ->|                     |
  |<---- returns ----|               |                     |
```

The path this pattern exists to make safe shows a Guarded Operation
composing two pieces of internal logic without re-entering the lock a
second time, which is exactly the self-call that a flat design with every
method locking would deadlock or double-charge on.

```
Client        Guarded.transferAll(items)      Guard      Unguarded layer
  |                     |                        |               |
  |-- transferAll() --->|                        |               |
  |                     |----- acquire() ------->|               |
  |                     |<------ granted ---------|               |
  |                     |                        |               |
  |                     |------- for each item: --|-------------->|
  |                     |          put_(item)      |  (no lock,   |
  |                     |          is_full_()?     |   just data) |
  |                     |<-------------------------|---------------|
  |                     |                        |               |
  |                     |----- release() -------->|               |
  |<----- returns ------|                        |               |
```

The blocked-and-woken path shows an Unguarded Operation cooperating with a
condition variable, releasing the Guard while waiting and reacquiring it
before the invariant check that follows. This is the point of contact with
Monitor Object, see dimension 13. The wait itself is delegated to the
Guard's condition primitive, and only the thread that currently holds the
Guard may call wait on it, so the Guarded Operation must have already
acquired the lock before the Unguarded Operation reaches the wait call.

```
Client(consumer)   Guarded.take()   Guard+CondVar     Unguarded.take_()
      |                  |                 |                   |
      |---- take() ----->|                 |                   |
      |                  |-- acquire() --->|                   |
      |                  |----------------------- take_() ---->|
      |                  |                 |    while empty_():|
      |                  |                 |<-- wait() --------|
      |                  |                 |   (lock released  |
      |                  |                 |    while blocked) |
      |                  |                 |                   |
      |                  |    ... producer calls put(),        |
      |                  |    which signals the condvar ...    |
      |                  |                 |                   |
      |                  |                 |-- wakes, lock  -->|
      |                  |                 |   reacquired      |
      |                  |                 |   automatically   |
      |                  |<---------------------- returns ----|
      |                  |-- release() --->|                   |
      |<---- returns ----|                 |                   |
```

## 8. Implementation variants

- **The classic split with a naming convention.** The canonical C++ and
  Java form uses a trailing `_`, a leading `_`, or a
  language-visibility modifier such as `private` to mark the unguarded
  layer, so the boundary is visible in the method's name and signature
  even though the compiler enforces nothing about lock state. This is the
  form presented in the 1999 *C++ Report* paper and in POSA2 itself.
- **Composed with Scoped Locking for exception safety.** Every Guarded
  Operation's acquire-then-release pair is itself a small, easy place to
  leak a held lock if an exception unwinds through the method before the
  release runs. Pairing this pattern with Scoped Locking, where the
  acquisition is owned by a stack-allocated guard object whose destructor
  releases the lock, `std::lock_guard` in C++, `synchronized` blocks in
  Java, `defer mu.Unlock()` in Go, a `with` statement in Python, RAII drop
  semantics in Rust, removes the leak risk entirely and is close to
  universal practice in production code that uses this pattern. See
  [scoped-locking](../09-concurrency/scoped-locking.md).
- **Structural, compiler-enforced variant, Rust.** Rust's `std::sync::Mutex<T>`
  makes the boundary a type-system fact rather than a naming convention.
  The protected data lives inside the `Mutex`, its fields are private, and
  the standard library states plainly that "the data can only be accessed
  through the RAII guards returned from lock and try_lock, which
  guarantees that the data is only ever accessed when the mutex is locked"
  ([Rust standard library documentation, `std::sync::Mutex`](https://doc.rust-lang.org/std/sync/struct.Mutex.html),
  verified 2026-08-02). There is no separate unguarded method to
  accidentally call from outside the lock, because there is no way to name
  the inner data at all except through a live guard. This is a strictly
  stronger guarantee than the naming-convention variant. The self-deadlock
  half of the original problem is unaffected, the language's `Mutex` is
  still non-reentrant, and re-locking on the same thread deadlocks or
  panics depending on the exact API used, but the failure mode of
  accidentally skipping the lock entirely is eliminated at compile time.
- **Recursive-lock relaxation.** Choosing a recursive or reentrant lock,
  Java's intrinsic monitor, Python's `threading.RLock`, or a POSIX mutex
  created with `PTHREAD_MUTEX_RECURSIVE`, and dropping the internal split
  entirely, accepting the modest extra per-acquisition cost of tracking an
  owner thread and a hold count, in exchange for simpler code with no
  naming convention to maintain. This is judgement, not a citable fact; the
  right trade depends on measured contention and call frequency, and for
  many classes it is the better engineering choice.
- **Reader-writer pairing.** For objects whose public surface has a mix of
  read-only and mutating operations, the Guard can be a reader-writer lock
  instead of a plain mutex, with read-only Guarded Operations taking a
  shared lock and mutating ones taking an exclusive lock, while the same
  internal-external split still governs which methods may call which.
- **Facade over a legacy non-thread-safe type.** When an existing class
  cannot be modified but must be shared across threads, a wrapper class,
  see the Wrapper Facade pattern in POSA2 chapter 3, can play the Guarded
  Operation role entirely, delegating each guarded call straight into the
  legacy type's methods, which then collectively play the Unguarded
  Operation role even though they were never designed with that
  precondition in mind. This variant is common in migration work and is
  more fragile than a purpose-built split, because the legacy type's
  authors never documented or enforced the assume-locked precondition.

## 9. Known production uses

- **The ACE toolkit's message-passing classes.** ACE, the Adaptive
  Communication Environment C++ network programming framework Douglas
  Schmidt's group built and that POSA2 draws its running examples from, is
  the toolkit the pattern was extracted from in the first place; the 1999
  paper that introduced it targets exactly this codebase's multi-threaded
  C++ components ([ACE papers index, Vanderbilt DRE Lab](https://www.dre.vanderbilt.edu/~schmidt/ACE-papers.html),
  verified 2026-08-02).
- **TAO, The ACE ORB.** TAO is a CORBA Object Request Broker built on top
  of ACE, developed by the same Vanderbilt DOC group, and its concurrency
  and connection-management components are documented as built from the
  ACE toolkit's synchronization facilities ([ACE toolkit overview,
  Vanderbilt DRE Lab](https://www.dre.vanderbilt.edu/~schmidt/ACE.html),
  verified 2026-08-02). TAO is a real, deployed ORB used in
  telecommunications and avionics middleware, and it inherits the
  Thread-Safe Interface discipline through the ACE base classes its
  concurrent servants are built on.
- **The Rust standard library's `Mutex<T>` API.** Rust's `std::sync::Mutex`
  is a production standard-library type, shipped with every Rust
  toolchain, whose entire public contract is an implementation of this
  pattern's intent enforced structurally. Protected data is reachable only
  through a guard obtained while the lock is held, so client code cannot
  construct a call path that touches the protected state without first
  crossing the guarded boundary ([Rust standard library documentation,
  `std::sync::Mutex`](https://doc.rust-lang.org/std/sync/struct.Mutex.html),
  verified 2026-08-02). This is a different implementation strategy from
  ACE's naming-convention split, see dimension 8, but it is solving the
  same problem and is presented here as a distinct, independently
  verifiable instance of the pattern rather than as a restatement of the
  first two.

## 10. Consequences

Positive.

- Removes self-deadlock as a possibility for any call path that stays
  entirely inside the object's own method set, because the lock is
  acquired exactly once per client-initiated call, at the outermost
  Guarded Operation, regardless of how deep the internal call chain runs.
- Cuts lock acquisition count to one per logical client operation instead
  of one per internal method invocation, which is a direct, measurable
  reduction in synchronization overhead on any hot path with real internal
  composition.
- Makes the class's own internal reuse unconstrained. Internal methods can
  call each other freely to share logic, which keeps the implementation
  DRY in a way a flat design where every method locks actively
  discourages.
- Gives the class a cheaper lock choice. Because self-calls no longer need
  to re-enter the lock, the object can use a non-reentrant mutex, which on
  most platforms is measurably cheaper per acquisition than a recursive
  one, without giving up internal composability.
- Documents intent by placement. A reader who sees a method in the
  unguarded layer knows, from that placement alone, that the method
  assumes the lock is held; the precondition does not need to be restated
  in a comment on every method, only in the class's own documentation of
  the convention.

Negative.

- In every language except the small set with structural enforcement, the
  boundary is a convention, not a guarantee. Nothing stops a future
  contributor, in the same class or in a derived class with looser access
  modifiers than intended, from calling an unguarded method directly, and
  when that happens the bug is a silent data race, not a crash, and can
  sit undetected for a long time.
- Adds an extra method per piece of internal logic in most
  implementations, a thin Guarded wrapper plus the real Unguarded body.
  For a small class this doubles the method count for no behavioral gain
  when the class never actually needed internal composition, which is
  exactly the situation dimension 4's non-applicability list warns
  against.
- The precondition that the caller already holds the lock is invisible to
  a type checker in most mainstream languages, so it lives in a comment, a
  naming convention, or a runtime assertion, none of which catch every
  violation, and none of which are checked by the compiler.
- Because the split makes composition cheap and easy, it can invite
  Unguarded Operations to grow into a large, tangled internal call graph
  that is hard to audit for the one property that matters most. Nothing
  in that graph should ever, on any path, try to acquire the Guard a
  second time, which would reintroduce the self-deadlock this pattern
  exists to prevent, one layer deeper than before.
- Does not, by itself, make a sequence of separate public calls atomic,
  see dimension 4. Teams sometimes reach for this pattern expecting it to
  solve check-then-act races across multiple client calls and are
  surprised when it does not, because the lock is released between calls
  by design.

## 11. Failure modes and misuse

- **Symptom.** The application hangs under load, on a code path that
  passed every unit test. **Cause.** An Unguarded Operation was
  accidentally written to call back into a Guarded Operation on the same
  object, for example an internal helper calling the public `take()`
  method instead of the internal `take_()` method, and the current thread
  deadlocks trying to reacquire a non-reentrant lock it already holds.
  **Fix.** Grep the unguarded layer for calls to any public method name on
  `self` or `this`, not only to other unguarded methods; add an assertion
  in debug builds at the top of every Guarded Operation that the lock is
  not already held by the current thread before acquiring it, where the
  lock API supports querying ownership.
- **Symptom.** A data race is caught by a race detector, Go's `-race`,
  Rust's Miri, or ThreadSanitizer under C++, or, worse, observed as
  corrupted state in production with no detector run. **Cause.** An
  Unguarded Operation was called directly from client code or from an
  unrelated part of the codebase, bypassing the Guarded layer entirely,
  most often after the unguarded method's visibility was accidentally
  widened during a refactor, moved from `private` to package visibility to
  make one caller work, or because the language has no visibility
  enforcement at all and relies on a naming convention a new contributor
  did not know about. **Fix.** Keep the unguarded layer at the strictest
  visibility the language offers; in languages with only
  convention-based privacy, add a lightweight runtime check at the top of
  every unguarded method in debug or test builds that asserts the lock is
  owned by the current thread, and treat any failure of that assertion as
  a build-blocking test failure, not a warning.
- **Symptom.** Throughput regresses after a safety pass through the code
  added more locking. **Cause.** A well-meaning contributor, unfamiliar
  with the pattern's convention, added an acquire and release pair inside
  an Unguarded Operation to be extra safe, which on a non-reentrant lock
  either deadlocks the very next time that method is reached from a
  Guarded Operation, or, on a reentrant lock, silently doubles the
  acquisition count on every call through that path and shows up only as
  a latency regression under load, not as a correctness bug. **Fix.**
  Document the precondition explicitly at the top of every Unguarded
  Operation, stating that the caller must hold the lock, and treat any new
  lock acquisition anywhere below the outermost Guarded Operation as
  something that requires an explicit design conversation, not a silent
  local fix.
- **Symptom.** A deadlock between two different objects, not one, appears
  intermittently under load. **Cause.** This is not actually a
  Thread-Safe Interface bug; it is lock ordering across two separate
  objects, each of which correctly implements this pattern internally, but
  whose Guarded Operations acquire each other's locks in inconsistent
  order from different call sites, for example object A's guarded method
  calling into object B while holding A's lock, while elsewhere object B's
  guarded method calls into A while holding B's lock. It is included here
  because teams that have recently adopted this pattern for single-object
  safety sometimes mistake this cross-object deadlock for a bug in the
  pattern itself. **Fix.** This is a lock-ordering problem, solved by
  imposing and documenting a total order over which objects may be locked
  while holding another object's lock, or by avoiding cross-object calls
  while holding any lock at all; it is outside this pattern's scope, and
  no amount of restructuring the internal-external split inside either
  object fixes it.

## 12. Trade-off matrix

| Force | Thread-Safe Interface | Fully synchronized, every method locks | Monitor Object, POSA2 | Lock-free or CAS-based structure |
|---|---|---|---|---|
| Self-deadlock on internal self-call | Eliminated by construction, if the convention is followed | Present, unless a reentrant lock is used | Eliminated, Monitor Object couples the object's activation with a single synchronized entry and internal scheduling, per POSA2 | Not applicable, no lock to re-enter |
| Lock acquisitions per logical call | One | One per method invoked, including internal ones | One, plus condition-variable coordination for blocking operations | Zero locks; instead a possibly-retried CAS loop |
| Compiler-checked correctness | No, except in Rust's structural variant, dimension 8 | No | No | Often no, though some languages offer atomics with type-level guarantees |
| Fits objects with rich internal composition | Yes, this is the primary case it targets | Poorly, forces duplication or reentrant locks | Yes, and additionally structures blocking and scheduling of waiting threads | Rarely, CAS loops compose badly across multiple fields |
| Handles blocking or waiting operations, producer-consumer style | Only in combination with a condition variable, not by itself | Only in combination with a condition variable, not by itself | Yes, this is Monitor Object's specific additional concern | Requires a specialized lock-free blocking design, uncommon |
| Implementation cost | One extra method layer plus a naming or visibility discipline | Lowest, nothing extra to write | Higher than Thread-Safe Interface alone, needs explicit scheduling policy design | Highest, correctness proofs for CAS loops are genuinely hard |
| Best fit | Shared object with internal composition, non-reentrant or costly-to-reenter lock | Small classes with no internal method-to-method calls | Shared object that must also manage blocking or waiting clients | Simple, single-field or single-pointer structures under high contention |

## 13. Related and incompatible patterns

- **Monitor Object.** The two are frequently confused because both concern
  synchronizing access to one object's state, and POSA2 places them
  adjacent to each other for exactly that reason. Monitor Object's stated
  concern, per its own entry in this repository, additionally covers
  scheduling which of several blocked threads runs next when a condition
  becomes true; Thread-Safe Interface's concern is narrower and purely
  about where the lock boundary sits relative to a class's own method
  calls. A Monitor Object is very often implemented using a Thread-Safe
  Interface as its outer shell, with the monitor's condition-variable
  waiting logic living in the unguarded layer, exactly as shown in
  dimension 7's third diagram. See
  [monitor-object](../09-concurrency/monitor-object.md).
- **Scoped Locking.** Composes directly. Every Guarded Operation's
  acquire-then-release is the exact unit Scoped Locking exists to make
  leak-proof; production code almost never implements the acquire and
  release as raw, manually paired calls once Scoped Locking's RAII-style
  guard object is available in the language. See
  [scoped-locking](../09-concurrency/scoped-locking.md).
- **Strategized Locking.** Complementary rather than overlapping.
  Strategized Locking decides which concrete lock type an object is
  parameterized over, a null lock for single-threaded builds, a mutex for
  multi-threaded ones, a reader-writer lock for read-heavy access
  patterns; Thread-Safe Interface decides where the acquire and release
  calls for whichever lock type was chosen actually sit inside the class.
  A class commonly uses both at once, Strategized over lock type, with
  each Guarded Operation acquiring whichever concrete lock the strategy
  currently supplies.
- **Double-Checked Locking Optimization.** A narrower, more specialized
  sibling from the same POSA2 chapter, aimed specifically at avoiding
  acquisition entirely on the fast path of a lazy-initialization check
  rather than at structuring a whole class's internal composition; the two
  are not typically combined on the same code path, because
  Double-Checked Locking's entire point is that most calls never touch
  the lock at all, whereas Thread-Safe Interface assumes every Guarded
  call does.
- **Active Object.** An architecturally different answer to a similar
  surface problem. Active Object moves each method call into a queued
  request executed later on a dedicated thread, decoupling method
  invocation from execution entirely, rather than synchronizing direct,
  in-thread calls; per POSA2's own cross-reference and this repository's
  Monitor Object entry, Active Object and Monitor Object are typically
  described as alternatives for the same problem rather than as
  compatible layers, and the same tension applies here. A class built as
  an Active Object generally has no need for a Thread-Safe Interface,
  because its methods never execute concurrently with each other in the
  first place; they execute serially on the activation thread regardless
  of how many client threads enqueue requests.
- **No incompatible patterns are recorded for this entry.** Thread-Safe
  Interface is a narrow, structural convention about method placement
  rather than a competing architecture, so it composes with essentially
  every other synchronization or concurrency-structuring pattern in this
  family rather than conflicting with any of them; where a genuine
  tension exists, Active Object above, it is a generally does not apply
  together relationship rather than a strict incompatibility, so it is
  recorded in the relationship text rather than in the frontmatter list.

## 14. Refactoring path in and out

Introducing the pattern into a class that currently locks every method
flatly, done in small, individually testable steps.

1. Identify every place one method on the class currently calls another
   method on the same instance, `self` or `this`, directly. This is the
   complete list of candidate boundary crossings; if the list is empty,
   stop here, this pattern is not needed, see dimension 4.
2. For each public method on the list, extract its body, everything after
   the current lock acquisition, into a new private method with a
   consistent naming or visibility marker, a trailing `_`, an
   `Unlocked` or `_locked` suffix, or simply `private`, whichever the
   codebase's conventions favor. The public method's new body becomes
   three steps in order. Acquire the lock, call the extracted private
   method, then release the lock.
3. Update every self-call identified in step 1 to call the private version
   of the target method, not the public one, since the caller is now
   guaranteed to already hold the lock by the time it reaches that call
   site.
4. Add a debug-only assertion at the top of each private method, where the
   lock API supports querying ownership, that the lock is currently held
   by the calling thread; run the full test suite with this assertion
   enabled to catch any missed self-call from step 3 before merging.
5. If the class currently uses a reentrant lock chosen specifically to
   tolerate the old flat design's self-calls, consider, as a separate,
   deliberately measured follow-up change, switching to the cheaper
   non-reentrant primitive, now that no self-call re-enters it; measure
   before and after, since this step is where the pattern's performance
   benefit is actually realized, and it is optional.

Removing the pattern, when the class no longer needs it, for example after
a redesign moved the class onto an actor or message-passing model where
external synchronization no longer applies.

1. Confirm, by re-running the audit from step 1 above, that removing the
   split is safe. Check whether every remaining caller of the private
   layer is itself a Guarded Operation of the same object, and never a
   caller from outside the class, since an outside caller of a
   nominally-private method is a bug this refactor must not paper over by
   simply making the method public.
2. Fold each private method's body back into its single remaining public
   caller if it now has exactly one caller, or merge the two layers back
   into flat, fully-locked methods if the class no longer benefits from
   the internal composition the split enabled.
3. If step 5 of the introduction path switched the lock to a
   non-reentrant primitive, and the removal reintroduces any self-call
   across what were formerly Guarded and Unguarded layers, switch back to
   a reentrant lock first, or the removal reintroduces the exact
   self-deadlock this pattern was built to prevent.

## 15. Testing and verification

What this pattern makes easier to test. Because the unguarded layer never
touches the lock itself, its logic, the actual state transitions, is fully
testable in a single-threaded unit test with no lock, no thread, and no
timing dependency at all; a test can construct the object, call the
private methods directly, in languages where the test is in the same
module or has reflection access, or by exposing a test-only internal seam,
and assert on state transitions with completely deterministic, race-free
assertions. This isolates whether the state machine is correct from
whether the concurrency is correct as two separate, separately debuggable
test concerns, which is one of the pattern's underappreciated practical
benefits.

What became harder. Testing the concurrency-specific guarantee, that no
two threads ever execute conflicting Unguarded Operations concurrently,
cannot be done by ordinary sequential unit tests at all, because
sequential tests never create the race in the first place. Three
approaches are used in practice, each with a distinct trade-off.

- **Stress testing.** Spin up many threads, each performing a large number
  of operations against one shared instance, and assert on an invariant
  that a race would violate, for example a running total that must never
  be observed inconsistent, or a counter of successful operations that
  must exactly equal the number attempted. This finds real bugs but is
  probabilistic; a passing run is not proof of absence, only evidence.
- **Race detectors.** Go's built-in `-race` flag, Rust's Miri interpreter,
  and Clang and GCC's ThreadSanitizer instrument every shared-memory
  access and flag genuine data races even on a run that happened not to
  produce visibly corrupted output. Running the stress test above under
  one of these tools converts probably fine into definitely no
  unsynchronized access was observed on this run, which is a much
  stronger and much cheaper signal than corruption-watching alone.
- **Assertion-based enforcement in debug builds.** As described in
  dimension 14, an assertion at the top of every Unguarded Operation that
  the lock is currently held by the calling thread turns a silent
  precondition violation into an immediate, loud test failure the moment
  any test path exercises the bug, rather than requiring the race to
  actually manifest as corrupted data on that particular run.

## 16. Observability signals

- **Lock hold time.** The wall-clock duration between a Guarded
  Operation's acquisition and its release, recorded as a histogram per
  operation name. A healthy instance shows a tight, low distribution; a
  sudden shift in the tail toward longer hold times usually indicates
  that an Unguarded Operation is doing more work than intended under the
  lock, for example a network call or a disk write that leaked into the
  guarded section.
- **Acquisition wait time.** The duration a thread spends blocked trying
  to acquire the Guard before it succeeds. A healthy instance keeps this
  near zero for most calls; a rising wait-time percentile under
  increasing load is the leading indicator of lock contention becoming
  the throughput bottleneck, well before it shows up as an end-to-end
  latency complaint.
- **Acquisition count per logical operation.** If the codebase can
  instrument the lock itself, many mutex implementations expose an
  acquire and release counter, or one can be added for observability, a healthy
  instance shows exactly one acquisition per public call, per the
  pattern's own guarantee; a count greater than one per public call is a
  direct, mechanical signal that dimension 11's extra-locking failure
  mode has occurred somewhere in the internal call graph.
- **Deadlock and timeout counters.** If the platform's lock API supports a
  bounded, timed acquisition attempt rather than an unbounded block, using
  it in production and counting timeouts converts a silent, permanent
  hang into a visible, alertable metric; an instance that reports zero
  timeouts under sustained load is healthy, and any non-zero count
  deserves immediate investigation as a probable self-deadlock or
  cross-object lock-ordering bug, see dimension 11.
- **Thread-dump or stack-trace sampling under suspected contention.** Most
  runtimes offer a way to dump every thread's current stack, Java's
  thread dump, Go's runtime stack trace with all goroutines, gdb or lldb
  attached to a native process. A healthy instance under load shows most
  threads either running or briefly blocked on acquisition; an unhealthy
  one shows many threads simultaneously blocked at the same acquisition
  call site with no thread anywhere in the process actually holding and
  progressing past that same lock, which is the direct symptom of the
  self-deadlock failure mode described in dimension 11.

## 17. Security and privacy implications

The pattern itself manages memory-visible concurrent access within a
single process; it makes no claim about network authentication,
encryption, or storage, so most of the standard security concern
categories are silent here, and this entry says so plainly rather than
inventing a concern where none exists. Two implications are real and worth
naming.

The first is a denial-of-service surface rather than a confidentiality or
integrity one. Because the pattern centralizes every public operation
behind a single lock per object, an attacker or a misbehaving caller who
can trigger an Unguarded Operation that runs unexpectedly long, for
example one that was accidentally given an unbounded loop over
attacker-controlled input, blocks every other thread's access to that
same object for the duration, which can be amplified into a broader
service degradation if many requests contend for the same shared object.
This is the same amplification risk any centralized lock carries, and the
mitigation is the ordinary one, bounding the work any Unguarded Operation
can be made to do by attacker-influenced input, not a change to the
pattern itself.

The second is timing side-channel exposure in the narrow case where the
protected state is security-sensitive, for example a shared cache of
authentication attempts or session tokens. Because acquisition and
release are observable externally through timing, an attacker measuring
response latency across many requests can sometimes infer whether a given
request contended with concurrent traffic on the same lock, a design that
shares one lock across genuinely unrelated security-sensitive and
non-sensitive operations can leak more timing information than one that
partitions the lock more finely. This is a general concurrency-and-timing
concern that applies to shared locks broadly, not a defect specific to
this pattern, and it is analytical judgement rather than a sourced claim.
No citation in this entry's reference list makes this specific point about
Thread-Safe Interface; it follows from the general, well-established
literature on timing side channels applied to this pattern's structure.

## 18. References

1. Douglas C. Schmidt, Michael Stal, Hans Rohnert, Frank Buschmann,
   *Pattern-Oriented Software Architecture, Volume 2. Patterns for
   Concurrent and Networked Objects*, John Wiley and Sons, 2000. Pattern
   list and section placement confirmed via the book's official companion
   page, [POSA2 pattern list, Vanderbilt DRE Lab](https://www.dre.vanderbilt.edu/~schmidt/POSA/POSA2/),
   verified 2026-08-02.
2. Douglas C. Schmidt, "Strategized Locking, Thread-Safe Interface, and
   Scoped Locking. Patterns and Idioms for Simplifying Multi-threaded C++
   Components," *C++ Report*, SIGS Publications, Vol. 11, No. 9,
   September 1999. Title, venue, volume, issue, and date confirmed via the
   paper's listing at [ACE papers index, Vanderbilt DRE Lab](https://www.dre.vanderbilt.edu/~schmidt/ACE-papers.html),
   verified 2026-08-02.
3. ACE, Adaptive Communication Environment, and TAO, The ACE ORB, toolkit
   overview, [Vanderbilt DRE Lab](https://www.dre.vanderbilt.edu/~schmidt/ACE.html),
   verified 2026-08-02. Source for the ACE and TAO production-use claims in
   dimension 9.
4. David R. Butenhof, *Programming with POSIX Threads*, Addison-Wesley,
   1997. Source for the default non-recursive behavior of `pthread_mutex_t`
   and the `PTHREAD_MUTEX_RECURSIVE` attribute discussed in dimension 2.
5. Rust standard library documentation, `std::sync::Mutex`,
   [doc.rust-lang.org](https://doc.rust-lang.org/std/sync/struct.Mutex.html),
   verified 2026-08-02. Source for the structural-enforcement implementation
   variant in dimension 8 and the production-use claim in dimension 9.
6. Go community guidance on preferring channel-based communication over
   shared-memory locking, cited in dimension 4's non-applicability
   discussion of actor and channel architectures, commonly summarized as
   "Do not communicate by sharing memory; instead, share memory by
   communicating." This is treated here as a widely attested community
   paraphrase of Go's design philosophy rather than a page-verified direct
   quotation, and is labeled as such.

## Implementation. Go

The bounded queue example below is the domain used throughout this entry's
diagrams. `Put` and `Get` are the Guarded Operations; `full`, `empty`, and
`enqueue` and `dequeue` are Unguarded Operations that assume `mu` is held
and never lock it themselves.

```go
package main

import (
	"fmt"
	"sync"
)

// BoundedQueue is a fixed-capacity, thread-safe FIFO queue.
type BoundedQueue struct {
	mu       sync.Mutex
	notFull  *sync.Cond
	notEmpty *sync.Cond
	items    []int
	capacity int
}

func NewBoundedQueue(capacity int) *BoundedQueue {
	q := &BoundedQueue{items: make([]int, 0, capacity), capacity: capacity}
	q.notFull = sync.NewCond(&q.mu)
	q.notEmpty = sync.NewCond(&q.mu)
	return q
}

// full is an Unguarded Operation. It assumes q.mu is already held.
func (q *BoundedQueue) full() bool {
	return len(q.items) == q.capacity
}

// empty is an Unguarded Operation. It assumes q.mu is already held.
func (q *BoundedQueue) empty() bool {
	return len(q.items) == 0
}

// enqueue is an Unguarded Operation. It assumes q.mu is already held.
func (q *BoundedQueue) enqueue(v int) {
	q.items = append(q.items, v)
}

// dequeue is an Unguarded Operation. It assumes q.mu is already held.
func (q *BoundedQueue) dequeue() int {
	v := q.items[0]
	q.items = q.items[1:]
	return v
}

// Put is a Guarded Operation. It owns the lock, and it is the only
// method here that ever calls Lock, Unlock, or Wait directly.
func (q *BoundedQueue) Put(v int) {
	q.mu.Lock()
	defer q.mu.Unlock()
	for q.full() {
		q.notFull.Wait()
	}
	q.enqueue(v)
	q.notEmpty.Signal()
}

// Get is a Guarded Operation, mirroring Put.
func (q *BoundedQueue) Get() int {
	q.mu.Lock()
	defer q.mu.Unlock()
	for q.empty() {
		q.notEmpty.Wait()
	}
	v := q.dequeue()
	q.notFull.Signal()
	return v
}

// PutAll is a Guarded Operation that composes several internal
// enqueues under one acquisition, the exact case this pattern targets.
func (q *BoundedQueue) PutAll(vs []int) {
	q.mu.Lock()
	defer q.mu.Unlock()
	for _, v := range vs {
		for q.full() {
			q.notFull.Wait()
		}
		q.enqueue(v)
	}
	q.notEmpty.Broadcast()
}

func main() {
	q := NewBoundedQueue(4)
	var wg sync.WaitGroup

	wg.Add(1)
	go func() {
		defer wg.Done()
		q.PutAll([]int{1, 2, 3})
		q.Put(4)
	}()

	wg.Add(1)
	go func() {
		defer wg.Done()
		total := 0
		for i := 0; i < 4; i++ {
			total += q.Get()
		}
		fmt.Println("total:", total)
	}()

	wg.Wait()
}
```

## Implementation. Rust

Rust's `Mutex<T>` makes the Unguarded layer's precondition a compile-time
fact rather than a convention. The plain methods on `Inner` below cannot be
called at all except through the `MutexGuard` that `lock()` returns, so
there is no separate assume-locked comment to trust; the type system
enforces it.

```rust
use std::collections::VecDeque;
use std::sync::{Condvar, Mutex};
use std::thread;

struct Inner {
    items: VecDeque<i32>,
    capacity: usize,
}

impl Inner {
    // Unguarded by convention here too, but reachable only via the
    // MutexGuard produced by locking the outer BoundedQueue, so an
    // outside caller has no path to these methods without holding it.
    fn full(&self) -> bool {
        self.items.len() == self.capacity
    }

    fn empty(&self) -> bool {
        self.items.is_empty()
    }

    fn enqueue(&mut self, v: i32) {
        self.items.push_back(v);
    }

    fn dequeue(&mut self) -> i32 {
        self.items.pop_front().expect("checked empty() before calling")
    }
}

pub struct BoundedQueue {
    inner: Mutex<Inner>,
    not_full: Condvar,
    not_empty: Condvar,
}

impl BoundedQueue {
    pub fn new(capacity: usize) -> Self {
        BoundedQueue {
            inner: Mutex::new(Inner { items: VecDeque::new(), capacity }),
            not_full: Condvar::new(),
            not_empty: Condvar::new(),
        }
    }

    // Guarded Operation. The only place that calls lock() or wait().
    pub fn put(&self, v: i32) {
        let mut guard = self.inner.lock().expect("mutex poisoned");
        while guard.full() {
            guard = self.not_full.wait(guard).expect("mutex poisoned");
        }
        guard.enqueue(v);
        self.not_empty.notify_one();
    }

    // Guarded Operation, mirroring put.
    pub fn get(&self) -> i32 {
        let mut guard = self.inner.lock().expect("mutex poisoned");
        while guard.empty() {
            guard = self.not_empty.wait(guard).expect("mutex poisoned");
        }
        let v = guard.dequeue();
        self.not_full.notify_one();
        v
    }
}

fn main() {
    let q = std::sync::Arc::new(BoundedQueue::new(4));

    let producer = {
        let q = q.clone();
        thread::spawn(move || {
            for v in [1, 2, 3, 4] {
                q.put(v);
            }
        })
    };

    let consumer = {
        let q = q.clone();
        thread::spawn(move || {
            let mut total = 0;
            for _ in 0..4 {
                total += q.get();
            }
            println!("total: {}", total);
        })
    };

    producer.join().unwrap();
    consumer.join().unwrap();
}
```

## Implementation. Python

Python's `threading.Lock` is non-reentrant by default, which makes it a
faithful vehicle for the pattern's original motivation. `_full`, `_empty`,
`_enqueue`, and `_dequeue` are Unguarded Operations, marked by the leading
`_` naming convention, and must never acquire `self._lock` themselves.

```python
import threading
from collections import deque


class BoundedQueue:
    def __init__(self, capacity: int) -> None:
        self._lock = threading.Lock()
        self._not_full = threading.Condition(self._lock)
        self._not_empty = threading.Condition(self._lock)
        self._items: deque[int] = deque()
        self._capacity = capacity

    # Unguarded Operation. Assumes self._lock is already held.
    def _full(self) -> bool:
        return len(self._items) == self._capacity

    # Unguarded Operation. Assumes self._lock is already held.
    def _empty(self) -> bool:
        return len(self._items) == 0

    # Unguarded Operation. Assumes self._lock is already held.
    def _enqueue(self, value: int) -> None:
        self._items.append(value)

    # Unguarded Operation. Assumes self._lock is already held.
    def _dequeue(self) -> int:
        return self._items.popleft()

    # Guarded Operation. Owns the only acquire and wait calls in this class.
    def put(self, value: int) -> None:
        with self._not_full:
            while self._full():
                self._not_full.wait()
            self._enqueue(value)
            self._not_empty.notify()

    # Guarded Operation, mirroring put.
    def get(self) -> int:
        with self._not_empty:
            while self._empty():
                self._not_empty.wait()
            value = self._dequeue()
            self._not_full.notify()
            return value

    # Guarded Operation that composes several internal enqueues
    # under one acquisition, the case this pattern targets directly.
    def put_all(self, values: list[int]) -> None:
        with self._not_full:
            for value in values:
                while self._full():
                    self._not_full.wait()
                self._enqueue(value)
            self._not_empty.notify_all()


def main() -> None:
    queue = BoundedQueue(capacity=4)
    total = {"value": 0}

    def producer() -> None:
        queue.put_all([1, 2, 3])
        queue.put(4)

    def consumer() -> None:
        for _ in range(4):
            total["value"] += queue.get()

    threads = [threading.Thread(target=producer), threading.Thread(target=consumer)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print("total:", total["value"])


if __name__ == "__main__":
    main()
```

A note on language coverage. Java is the most idiomatic host language for
this pattern's original naming-convention form, since intrinsic
`synchronized` methods and manually written `private` helpers are exactly
the shape the 1999 paper and POSA2 describe in C++ terms, but this
session's toolchain has no working Java runtime available, `javac
-version` reports no Java Runtime located, so no Java sample is included
here rather than presenting an uncompiled one as verified. TypeScript and
Swift are omitted for a structural reason rather than a tooling one.
Node.js's single-threaded event loop has no preemptive shared-memory
concurrency for a plain TypeScript class to protect, and the pattern's
motivating problem does not arise there without worker threads and shared
array buffers, which would make the example about that machinery rather
than about the pattern, and Swift's current concurrency idiom for this
exact problem is the actor model, which removes the need for an explicit
internal-external lock split entirely rather than illustrating it.
