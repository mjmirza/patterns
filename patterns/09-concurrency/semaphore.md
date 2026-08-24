---
name: Semaphore
slug: semaphore
family: 09-concurrency
category: Concurrency
aliases: [Counting Semaphore, Binary Semaphore, P/V Operations, Dijkstra Semaphore]
first_described: "Dijkstra 1962 or 1963, EWD-35"
maturity: canonical
related: [mutex, monitor, producer-consumer, thread-pool, bulkhead, rate-limiter, condition-variable]
incompatible_with: []
verified: 2026-08-02
---

# Semaphore

## 1. Name, aliases, and lineage

The canonical name is Semaphore. Wikipedia's history section states the concept
was invented by the Dutch computer scientist Edsger Dijkstra in 1962 or 1963
while he was working on an operating system for the Electrologica X8, the
system that became known as THE multiprogramming system, and that his earliest
paper on the topic was "Over de sequentialiteit van procesbeschrijvingen"
(EWD-35), dated 1962 or 1963 (Wikipedia contributors, "Semaphore
(programming)", https://en.wikipedia.org/wiki/Semaphore_(programming), verified
2026-08-02). The name borrows the railway semaphore signal, a mechanical arm
that tells a train whether the track ahead is clear, which is the same
intuition the primitive gives a thread deciding whether a resource is free.

The two universal aliases are not decoration, they name the two operations
Dijkstra defined. According to the same Wikipedia history, the canonical
operation names derive from Dutch. **V** is explained as *verhogen*,
"increase," and is the operation that returns a permit. **P** in Dijkstra's
original paper meant *passering*, "passing," and he later described it as
short for *prolaag*, itself short for *probeer te verlagen*, "try to reduce."
P is the operation that takes a permit, blocking when none is available. Every
modern API renames these to `acquire` and `release`, or `wait` and `signal`,
but P and V remain the names used in algorithms textbooks and in academic
papers, and a reader who only knows `acquire`/`release` will be lost the first
time a paper says "the process calls P on the semaphore."

The same source distinguishes two shapes that are named separately because
their failure modes differ. A **counting semaphore** holds an integer permit
count above one and models "N interchangeable resources are available." A
**binary semaphore** is restricted to the values 0 and 1 and is used as a
locking mechanism, functionally close to a mutex but, critically, without a
mutex's ownership rule, see dimension 4 for why that distinction matters and is
not merely academic.

## 2. Problem and context

A fixed, known number of interchangeable resources exist. Database
connections in a pool, worker threads in a pool, licence seats, outbound HTTP
calls to a fragile third party, slots in a rate-limited API tier, GPU memory
buffers, disk write handles. Many independent pieces of code, running
concurrently, need to use one of those resources for a while and then give it
back. Too many pieces of code using the resource at once causes the resource
to fail, degrade, or exceed a contractual limit, so something must count how
many are in use and make everyone else wait once the count reaches the limit.

The context that produces this problem has three recognisable shapes in a real
codebase. First, a shared pool with a construction cost, where creating a new
instance of the resource on demand is either impossible (a third party issues
a fixed number of licence seats) or too expensive to do per request (opening a
fresh TCP connection per query). Second, a downstream dependency with its own
concurrency ceiling, where the calling code has no control over the
dependency's capacity and must self-limit to avoid overwhelming it, which is
the same problem as the first shape seen from the caller's side rather than
the resource owner's side. Third, a local resource that is genuinely finite
inside the running process, most often memory or open file descriptors, where
letting an unbounded number of tasks proceed concurrently would exhaust the
process before any individual task fails.

What separates this from a plain mutual-exclusion problem is the word
"interchangeable" and the number attached to it. A mutex protects exactly one
thing and admits exactly one holder. A semaphore protects N interchangeable
things and admits up to N holders at once, and any holder can give its permit
back regardless of who took it. The moment a design needs the number N to be
anything other than one, or needs release to happen from code that never
acquired, a mutex stops being able to express the requirement and a semaphore
is the honest primitive.

## 3. Forces

- **Throughput versus resource protection.** Sacrificed for the latter,
  deliberately. A semaphore's entire purpose is to cap throughput below what
  the calling code could otherwise sustain, in exchange for keeping the
  protected resource inside a safe operating range. Set the permit count too
  high and the resource degrades. Set it too low and callers queue for
  capacity that is sitting idle.
- **Fairness versus latency for the fast path.** The Java documentation
  fetched for this entry states the constructor's `fair` parameter defaults to
  false, which allows a newly arriving thread to "barge" ahead of threads
  already waiting, and that untimed `tryAcquire()` calls ignore fairness
  entirely and grab any available permit immediately, even under a fair
  semaphore (Oracle, *Java SE 21 API Specification*,
  `java.util.concurrent.Semaphore`, verified 2026-08-02, see dimension 18).
  Barging gives lower average latency and higher throughput under contention,
  because the CPU does not have to context-switch to the head of a FIFO
  queue. FIFO fairness gives a bounded worst-case wait per caller, at the
  cost of average throughput. The two cannot both win at once.
- **Ownership versus flexibility.** A semaphore permit is not owned by the
  thread that acquired it. Oracle's own documentation states plainly that
  "a thread other than the acquirer can release permits," and that a
  semaphore imposes no requirement that the thread releasing a permit
  acquired it (same source). This is a deliberate design choice, not an
  oversight, and it is the exact feature that lets a semaphore coordinate a
  producer and a consumer, see dimension 9. The cost is that nothing stops a
  bug from releasing twice, or releasing without ever acquiring, and the
  primitive has no way to detect either.
- **Bounded resource versus unbounded queueing.** A blocking `acquire` turns
  an unbounded burst of demand into a bounded burst of *concurrent execution*,
  but it does not bound the queue of callers waiting to acquire. Every caller
  that shows up still occupies a thread, a coroutine, or a context object
  while it waits, so a semaphore protects the resource behind it without, by
  itself, protecting the caller's own memory from an unbounded arrival rate.
  A separate bound, or a `tryAcquire` with a timeout, is needed for that.
- **Simplicity versus expressiveness.** A raw counting semaphore expresses
  "up to N concurrent holders" and nothing more. It says nothing about which
  holder gets which resource, in what order work should complete, or what
  happens on partial failure. That simplicity is favoured deliberately,
  because the alternative, building resource-specific bookkeeping into every
  call site, is worse. The cost is that anything more structured, a
  work-stealing pool, a priority queue, a circuit breaker, has to be built on
  top of the semaphore rather than being expressed by it.

## 4. Applicability and non-applicability

Reach for a semaphore when the following hold.

- The number of interchangeable resource instances is known and fixed, or
  changes rarely enough that the change is an administrative act rather than
  something the code must discover per call.
- More than one holder should be able to use the resource at once, and the
  cap on simultaneous holders is exactly the requirement, not an
  approximation of some other requirement.
- Release may legitimately happen from code, a thread, or a callback other
  than the one that acquired, which is the signature use case for a
  producer-consumer handoff, see dimension 9.
- The resource being protected is scarce in a way that failing fast or
  queueing briefly is preferable to letting every caller proceed and having
  the resource itself fail under load, which is the bulkhead pattern's
  reasoning, see dimension 13.
- A rate limit or concurrency limit is imposed by a party outside the calling
  process, an upstream API's documented concurrent-connection cap, a
  database's max-connections setting, a payment gateway's per-merchant
  concurrency ceiling, and the calling code must self-police to that number
  rather than discover the limit by triggering the upstream's own throttling.

Do NOT reach for a semaphore in these cases, and the reason matters more than
the rule.

- **The resource count is exactly one and only one thread should ever hold
  it, with the thread that acquires being the thread that must release.** A
  binary semaphore used purely for mutual exclusion by a single owner is a
  mutex wearing a costume, and it is a worse mutex, because a mutex's
  ownership discipline lets the runtime and static analysis tools catch a
  double-release, a release without acquire, and, in many implementations, a
  thread that dies while holding the lock. A semaphore offers none of that
  protection. If the shape is "exactly one holder, same thread releases,"
  use a mutex.
- **The requirement is ordering, not counting.** A semaphore says nothing
  about which waiter goes next beyond the fairness setting, and nothing at
  all about sequencing distinct steps of a pipeline. When the actual need is
  "step B must not start until step A finishes," a future, a promise, a
  barrier, or a condition variable expresses that directly. Forcing it
  through a semaphore of size one produces code that reads as concurrency
  control when the real intent is sequencing.
- **The resource limit is really a rate over time, not a count of
  concurrent holders.** A semaphore bounds how many callers are inside the
  critical section simultaneously. It does not bound how many complete per
  second. An API that allows 100 requests per second but only 5 concurrent
  in-flight requests needs both a rate limiter and a semaphore, and reaching
  for only the semaphore under-protects the rate dimension while reaching for
  only a rate limiter under-protects the concurrency dimension.
- **The language or framework already gives a higher-level primitive for the
  exact shape needed.** A bounded channel or bounded queue in Go, Rust, or
  Kotlin coroutines already caps in-flight work and additionally handles
  backpressure and cancellation idiomatically. A connection pool library
  already manages the counting internally along with health checks and
  eviction. Reaching past those for a raw semaphore duplicates bookkeeping
  the library already does correctly, see dimension 8 for language-idiomatic
  alternatives.
- **The critical section is read-mostly with rare writers.** A plain
  semaphore treats every acquire identically. When the actual access pattern
  is many concurrent readers and occasional exclusive writers, a
  reader-writer lock expresses that distinction directly and admits more
  concurrency for the common case than a semaphore sized for the writer path
  ever could.
- **Cross-process coordination is not actually required.** A named or
  file-backed POSIX or System V semaphore is heavier and slower than an
  in-process one, and carries its own cleanup hazards, see dimension 11. If
  every participant lives in the same process, an in-process semaphore is
  simpler and there is no reason to reach for the cross-process form.

## 5. Structure

The classical shape has three participants.

- **Semaphore.** Holds an integer counter, initialised to the number of
  available permits, and a wait set of blocked callers. It exposes exactly
  two operations to its callers, acquire and release, plus, in most modern
  implementations, a non-blocking `tryAcquire` variant and a
  timeout-bounded variant. The counter and wait set together must be
  protected by an internal lock or an atomic mechanism, because acquire and
  release are themselves accessed concurrently, which makes the semaphore's
  own implementation a small concurrent data structure in its own right.
- **Permit.** Not a distinct object in most APIs, but a conceptual unit
  represented by one decrement of the counter. A caller that has
  successfully acquired holds one or more permits until it calls release.
  Permits carry no identity, which is why any thread can release a permit it
  never acquired, see dimension 3.
- **Waiter.** A thread, coroutine, or task blocked inside acquire because the
  counter was zero at the time it called. The semaphore's internal wait set
  holds waiters and wakes one, or several, when release increases the
  counter above zero. Whether the woken waiter is the one that has been
  waiting longest depends on the fairness policy, see dimension 3.

A resource pool built on a semaphore typically pairs it with a fourth,
implicit participant, the resource collection itself, a queue or free-list of
the actual connections, buffers, or handles. The semaphore's counter and the
collection's size must stay in lockstep by construction, and a mismatch
between them, more permits than resources or the reverse, is one of the
failure modes in dimension 11.

## 6. ASCII structure diagram

```
+------------------------------------------------------+
| Semaphore                                            |
| counter: int, permits left                           |
| waitSet: queue of Waiter                             |
| acquire(), tryAcquire(), acquire(timeout), release() |
+------------------------------------------------------+
     ^ blocks and enqueues here when counter is 0
     |
+------------------------+
| Waiter A, blocked task |
+------------------------+
+------------------------+
| Waiter B, blocked task |
+------------------------+

Each blocked Waiter is woken in turn when a holder
calls release() and a permit frees up.

A semaphore initialised with N permits admits up to N
concurrent holders. Holder N+1 blocks in the wait set
until any holder releases.

Holder 1. acquire() -> permit 1 taken -> uses resource
          -> release()
Holder 2. acquire() -> permit 2 taken -> uses resource
          -> release()
Holder 3. acquire() -> counter is 0, BLOCKS -> woken
          only when a permit frees up
```

## 7. Dynamics

The interaction has two distinct shapes worth drawing separately, because
they are the two dominant real-world uses, resource pooling and
producer-consumer signalling.

Resource pooling, where the same task both acquires and releases.

```
Task A               Semaphore(N=2)              Task B               Task C
  |                        |                         |                    |
  |-- acquire() ---------->|                          |                    |
  |   counter: 2 -> 1      |                          |                    |
  |<-- returns immediately-|                          |                    |
  |                        |<-- acquire() ------------|                    |
  |                        |    counter: 1 -> 0       |                    |
  |                        |--- returns immediately -->|                    |
  |                        |                          |                    |
  |                        |<-- acquire() -------------------------------- |
  |                        |    counter=0, C BLOCKS in wait set             |
  |                        |                          |                    |
  |-- release() ---------->|                          |                    |
  |   counter: 0 -> 1      |                          |                    |
  |   wakes C from wait set|                          |                    |
  |                        |---------------------------------------------> |
  |                        |    C's acquire() returns, counter: 1 -> 0     |
```

Producer-consumer signalling, where the releasing task is never the acquiring
task, which is the shape a mutex cannot express.

```
Producer                    Semaphore(N=0, "items available")     Consumer
   |                                  |                               |
   |  produces item, enqueues it      |                               |
   |-- release() ------------------->|                                |
   |   counter: 0 -> 1                |                               |
   |                                  |<-- acquire() ------------------|
   |                                  |    counter: 1 -> 0             |
   |                                  |--- returns, consumer dequeues->|
   |                                  |                                |
   |  (consumer had been blocked      |                                |
   |   in acquire() before this       |                                |
   |   release() happened, if the     |                                |
   |   producer was slower)           |                                |
```

Two timing notes that apply to both shapes. First, the internal counter update
and wait-set manipulation inside acquire and release must be atomic with
respect to each other, or two racing acquires can both observe a stale
positive counter and both proceed when only one permit exists, which is why
every production semaphore implementation guards its own state with a lock or
a compare-and-swap loop rather than a bare integer. Second, a release call
that wakes a waiter does not, in most implementations, hand the permit
directly to that waiter atomically. The woken waiter re-checks the counter
itself, which means a third party can, in an unfair semaphore, barge in and
take the permit between the wake-up signal and the waiter actually resuming,
the barging behaviour the Java documentation describes explicitly in
dimension 3.

## 8. Implementation variants

**Counting semaphore, unfair.** The default in most standard libraries. Any
caller can barge ahead of an already-waiting caller. Higher throughput,
lower average latency, no fairness guarantee. This is Java's default per the
documentation fetched for this entry, and is the shape used when raw
throughput under contention matters more than per-caller latency bounds.

**Counting semaphore, fair.** FIFO ordering among blocked waiters. Oracle's
documentation for `java.util.concurrent.Semaphore` states this explicitly as
a constructor option and recommends it for semaphores that control resource
access, specifically to avoid starving out a thread from a busy resource
(same source, see dimension 18). The cost is reduced throughput under heavy
contention, because the runtime must wake the head-of-queue waiter rather
than letting whichever thread happens to be running proceed.

**Binary semaphore.** Counter restricted to 0 and 1. Functionally close to a
mutex, but retains the no-ownership property, so it remains useful
specifically where release-from-a-different-context is required even though
only one holder is ever admitted, for example a single-slot handoff signal
between an interrupt handler and a worker thread in embedded and real-time
code, where the interrupt handler can never itself hold a mutex it did not
acquire in mutex-respecting code paths.

**Weighted semaphore.** Permits are acquired and released in variable
amounts rather than always one at a time, so a caller can request "8 units
of capacity" in one call rather than acquiring a fixed-size unit eight
times. The `golang.org/x/sync/semaphore` package documentation fetched for
this entry describes its `Weighted` type exactly this way, exposing
`Acquire(ctx, n)`, `TryAcquire(n)`, and `Release(n)` where `n` is the weight
requested (golang.org, `golang.org/x/sync/semaphore`, verified 2026-08-02,
see dimension 18). This variant suits resources with heterogeneous cost,
memory budgets where different tasks consume different byte counts against a
shared ceiling, being the clearest example.

**Context-aware or cancellable acquire.** Go's `Weighted.Acquire` takes a
`context.Context` and returns the context's error rather than blocking
forever if the context is cancelled or its deadline passes, per the same
documentation. This variant matters anywhere requests can be cancelled or
time-bound, because a semaphore acquire with no cancellation path becomes an
unkillable blocking call the moment the caller that would have released the
permit dies or hangs, see dimension 11.

**Async or coroutine-native semaphore.** Python's `asyncio.Semaphore`, per
the documentation fetched for this entry, manages an internal counter and
exposes `acquire`, `release`, and a `locked()` predicate, with a strong
warning that it is not thread-safe and is scoped to a single event loop
(Python Software Foundation, *Python 3 documentation*,
`asyncio.Semaphore`, verified 2026-08-02, see dimension 18). This variant
blocks the coroutine, not the OS thread, so a single OS thread can host
thousands of waiters cheaply, at the cost that mixing an async semaphore
with a thread-based caller is a silent correctness bug rather than a
compile error.

**POSIX or System V named semaphore.** Cross-process rather than
cross-thread. `sem_wait`, `sem_trywait`, `sem_post` operate on a semaphore
object identified by a name or a key rather than an in-memory reference, per
the Linux man page fetched for this entry (Linux man-pages project,
`sem_wait(3)`, verified 2026-08-02, see dimension 18). This variant is the
only one of the set that survives the acquiring process crashing while
holding a permit as a durable artefact, in the specific sense that the
kernel-held semaphore object continues to exist, but the permit is not
automatically returned, see the leaked-permit failure mode in dimension 11.

**`BoundedSemaphore`.** A variant, present in Python's asyncio and threading
modules among others, that raises an error if `release()` would push the
counter above its initial maximum. This catches the specific bug of an
extra, unmatched release call at the moment it happens rather than letting
the counter silently drift upward and under-protect the resource later.

**Semaphore built from a channel.** In Go and in Rust's async ecosystems, a
buffered channel of capacity N, where acquiring means sending a token into
the channel and releasing means receiving one back out, gives semaphore
semantics using the language's native concurrency primitive rather than an
explicit `Semaphore` type. This is idiomatic where the surrounding code is
already channel-based, and it composes naturally with `select` for
cancellation, at the cost of being less immediately recognisable as "a
semaphore" to a reader unfamiliar with the idiom.

## 9. Known production uses

**Java concurrent collections and thread pools, `java.util.concurrent.Semaphore`.**
Part of the JDK's `java.util.concurrent` package since Java 5. Oracle's Java
SE 21 API documentation for the class states its purpose as restricting the
number of threads that can access a resource, and gives a worked pool example
where a fixed-size array of items is guarded by a semaphore sized to the
array length, with `acquire()` called before taking an item and `release()`
called after returning it. Oracle, *Java SE 21 API Specification*,
`java.util.concurrent.Semaphore`,
https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/Semaphore.html
verified 2026-08-02.

**Go's official extended concurrency library, `golang.org/x/sync/semaphore`.**
Maintained under the `golang.org/x` umbrella alongside the Go standard
library proper, and documented as providing a weighted semaphore
implementation useful for bounding concurrent access to a resource, with a
worked example limiting the number of goroutines running work in parallel.
The Go team, package documentation,
https://pkg.go.dev/golang.org/x/sync/semaphore verified 2026-08-02.

**Python's asyncio standard library, `asyncio.Semaphore` and
`asyncio.BoundedSemaphore`.** Part of CPython's standard library
`asyncio.sync` module, documented as a synchronization primitive that
manages an internal counter decremented by `acquire()` and incremented by
`release()`, intended for bounding concurrent coroutine access to a shared
resource such as a limited pool of outbound connections. Python Software
Foundation, *Python 3 documentation*, "Synchronization Primitives",
`asyncio.Semaphore`,
https://docs.python.org/3/library/asyncio-sync.html#asyncio.Semaphore
verified 2026-08-02.

**POSIX threads, `sem_wait`, `sem_trywait`, `sem_timedwait`, `sem_post`.**
Standardised inter-process and inter-thread semaphore functions specified by
POSIX and implemented across Linux, the BSDs, and other POSIX-conformant
systems, forming the low-level primitive that many higher-level language
runtimes build their own semaphore types on top of on Unix-like platforms.
The Linux man page states `sem_wait` decrements, that is, locks, the
semaphore, blocking if the value is currently zero, and describes the
non-blocking `sem_trywait` and timeout-bound `sem_timedwait` variants
alongside it. Linux man-pages project, `sem_wait(3)`,
https://man7.org/linux/man-pages/man3/sem_wait.3.html verified 2026-08-02.

## 10. Consequences

Positive.

- Expresses "up to N concurrent holders of an interchangeable resource"
  directly, with the number N as a single, visible, tunable constant, rather
  than approximating the constraint through ad hoc counters scattered across
  call sites.
- Correctly supports the producer-consumer handoff shape, release from a
  context other than the one that acquired, which a mutex or a lock with
  ownership tracking cannot express without a workaround.
- Decouples the resource's true capacity from the number of callers.
  Callers block, or fail fast with `tryAcquire`, without any of them needing
  to know how many other callers currently hold a permit.
- Composes cleanly as a building block for higher-level patterns, the
  bulkhead pattern, worker pools with a bounded queue depth, and rate
  limiting are all commonly implemented on top of a semaphore rather than as
  entirely separate primitives, see dimension 13.
- The weighted and context-aware variants, see dimension 8, extend the same
  simple counting idea to heterogeneous resource costs and to cancellation
  without changing the caller's mental model.

Negative.

- No ownership tracking means the runtime cannot catch a double-release, a
  release with no matching acquire, or a permit leaked because the holding
  task died without releasing. Every one of these bugs manifests as silent
  drift in the effective concurrency limit rather than as an immediate
  crash, see dimension 11.
- A blocking acquire with no timeout turns a downstream failure into an
  unbounded pile-up of blocked callers, each holding whatever thread stack
  or coroutine state it had before calling acquire, which can itself exhaust
  a different resource, threads or memory, than the one the semaphore was
  protecting.
- Choosing the right permit count N is a judgement call informed by load
  testing and the protected resource's real capacity, not a value that can
  be derived analytically in most systems, and a wrong N either
  under-protects the resource or under-utilises it.
- The primitive itself says nothing about priority, fairness across
  different callers with different importance, or graceful degradation when
  the resource is exhausted, all of which have to be layered on top if the
  system needs them.
- A semaphore used as a substitute for a mutex, see dimension 4, discards
  the ownership guarantees a mutex would have given for free, which is a
  strict downgrade when the actual requirement was single-holder exclusion.

## 11. Failure modes and misuse

**Permit leak on an exception path.** Symptom. Available concurrency slowly
drops over the life of a long-running process, until every caller blocks
forever even though the protected resource is healthy and idle. Cause. A
task acquires a permit, throws or returns early on an exception path, and
the matching release call sits after the code that threw rather than in a
`finally`, `defer`, or equivalent guaranteed-cleanup block. Fix. Pair every
acquire with a release in a construct the language guarantees will run,
Java's `try/finally`, Go's `defer`, Python's `async with`, and prefer the
language's context-manager or defer-based idiom over manual paired calls
whenever one exists, exactly as the Python documentation fetched for this
entry recommends by presenting `async with sem:` as the preferred usage.

**Double release inflates effective capacity.** Symptom. More concurrent
holders are observed inside the protected section than the configured
permit count should allow, and the downstream resource starts failing under
load that should have been within its rated capacity. Cause. A release call
executes on a path that can run twice, a retry wrapper that calls release in
its own cleanup as well as in the caller's cleanup, or a release accidentally
placed inside a loop body instead of after it. Fix. Use a `BoundedSemaphore`
variant where the language offers one, so an over-release raises immediately
rather than silently inflating the counter, and audit every release call
site for the possibility of double execution.

**Deadlock through nested acquisition in inconsistent order.** Symptom. Two
or more tasks each hold one semaphore's permit and block trying to acquire a
different semaphore that the other task holds, and the system stalls with
every thread reporting as blocked in acquire. Cause. Code acquires multiple
semaphores without a fixed global ordering, so task A acquires semaphore 1
then blocks on semaphore 2 while task B has already acquired semaphore 2 and
blocks on semaphore 1. Fix. Establish and document a total order across every
semaphore a codebase uses and always acquire in that order, or restructure
so no code path needs to hold more than one semaphore's permit at a time.

**Unbounded queueing behind a bounded resource.** Symptom. Memory or thread
count grows without limit even though the protected resource itself never
exceeds its permit count, and the process eventually falls over on an
out-of-memory or thread-exhaustion error rather than on the resource the
semaphore was meant to protect. Cause. The semaphore correctly bounds
concurrent holders, but nothing bounds the number of callers piling up in
acquire, and each blocked caller retains a thread stack, a coroutine frame,
or request state while it waits. Fix. Pair the semaphore with an explicit
bound on the number of callers allowed to even attempt acquire, a bounded
queue in front of it, or a `tryAcquire` with a short timeout that fails the
caller fast, converting an unbounded queue into an explicit reject decision.

**Priority inversion under a fair semaphore.** Symptom. A high-priority task
blocks on acquire behind a long queue of lower-priority tasks that arrived
earlier, and the fairness guarantee that was supposed to prevent starvation
now actively harms the task that needed the resource most urgently. Cause.
Plain counting or fair semaphores are priority-blind by design, they order
by arrival, not by importance. Fix. Either use a priority-aware queueing
structure in front of the semaphore, or accept that a fair semaphore
favours no-starvation across equals, not prioritisation, and choose a
different construct when prioritisation is the actual requirement.

**Sized for the average case, not the tail.** Symptom. The system runs fine
under normal load and then falls over during a traffic spike, with every
caller reporting long waits on acquire even though the resource behind the
semaphore is not itself saturated. Cause. The permit count N was chosen from
average concurrency observed in normal operation rather than from the
protected resource's actual rated capacity, so N is set below what the
resource could safely sustain, and legitimate burst traffic queues
unnecessarily. Fix. Load-test the protected resource directly to find its
real safe concurrency ceiling, and set N to that ceiling rather than to an
observed average, revisiting N whenever the underlying resource's capacity
changes.

**Named semaphore left behind after a crash.** Symptom. After a process
crashes and restarts, every acquire call against a cross-process POSIX or
System V named semaphore blocks immediately, even though no live process
should be holding a permit. Cause. The kernel-level semaphore object
persists independently of the process that created it, per the semantics
described in the `sem_wait(3)` man page fetched for this entry, so a process
that dies while holding a permit leaves the counter permanently decremented
until something explicitly resets or removes the semaphore object. Fix. Use
a supervisor or init system that removes or reinitialises named semaphores
on process restart, and prefer an in-process semaphore over a named one
whenever cross-process durability is not an actual requirement.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Semaphore | Mutex or lock | Reader-writer lock | Rate limiter (token bucket) | Bounded queue or channel | Circuit breaker |
|---|---|---|---|---|---|---|
| Concurrent holders admitted | Configurable, N | Exactly one | N readers OR one writer | Not concurrency, requests per interval | Bounded by queue capacity, not by concurrency directly | Zero when open, unbounded when closed |
| Ownership tracking | None. Any thread can release | Strict, acquirer must release | Strict per mode | Not applicable | Not applicable | Not applicable |
| Handles release from a different context | Yes, its defining strength | No, undefined behaviour or an exception in most runtimes | No | Not applicable | Yes, via a separate consumer | Not applicable |
| Bounds requests over time | No, only concurrency | No | No | Yes, that is its purpose | Indirectly, via backpressure | No, it reacts to failure rate |
| Detects and reacts to downstream failure | No, blind to success or failure of the work | No | No | No | No | Yes, that is its purpose |
| Best fit for exact resource count | Excellent | Poor unless count is exactly one | Poor, models a read/write split not a count | Poor, models a rate not a count | Fair, if queue capacity equals resource count | Poor, models failure rate not a count |
| Fairness control | Optional FIFO mode | Implementation dependent | Implementation dependent | Not applicable | FIFO by construction usually | Not applicable |
| Composability with cancellation | Good in modern APIs (context, async) | Good | Good | Good | Excellent, native to channels | Good |

Reading of the table. A semaphore wins whenever the requirement is exactly "N
interchangeable resources, N configurable, release from anywhere." A mutex
wins when N is exactly one and ownership discipline is wanted. A rate
limiter and a semaphore are frequently needed together, because one bounds
requests over time and the other bounds requests in flight at any instant,
and neither substitutes for the other. A circuit breaker answers a different
question entirely, whether to attempt the call at all given recent failure
history, and is commonly layered in front of a semaphore-protected resource
rather than replacing it.

## 13. Related and incompatible patterns

- **Mutex.** The degenerate case. A binary semaphore used for pure mutual
  exclusion by a single owner is functionally close to a mutex, but a mutex
  should be preferred whenever the shape is genuinely single-holder,
  same-thread-releases, because a mutex's ownership discipline lets tooling
  and, in some runtimes, the standard library itself catch misuse that a
  semaphore cannot. See dimension 4.
- **Monitor.** A semaphore is lower-level than a monitor. A monitor bundles
  mutual exclusion with condition variables and a well-defined wait and
  signal protocol tied to a specific predicate, whereas a semaphore's
  counter carries no semantic meaning beyond "how many permits remain." Many
  languages implement monitors, or condition variables used inside a
  monitor, on top of a semaphore or a closely related primitive internally.
- **Producer-consumer.** The signature use case for a semaphore whose
  acquiring and releasing parties are different, see the second diagram in
  dimension 7. A bounded producer-consumer queue is frequently implemented
  as two semaphores, one counting empty slots and one counting filled slots,
  guarding a shared buffer.
- **Thread pool or worker pool.** Composes directly. A thread pool with a
  bounded number of workers is itself a semaphore-shaped resource, and many
  thread pool implementations use a semaphore or an equivalent counter
  internally to admit only as many concurrently executing tasks as there are
  worker threads.
- **Bulkhead pattern.** A direct application. The bulkhead pattern isolates
  a system into partitions so that failure or saturation in one partition
  cannot exhaust resources needed by another, and a semaphore per partition,
  sized to that partition's fair share of a shared resource pool, is the
  standard way to implement it.
- **Rate limiter, specifically the token bucket and leaky bucket
  algorithms.** Related but answering a different question, requests over
  time versus requests in flight at once, see dimension 12. The two are
  frequently combined, and neither replaces the other.
- **Condition variable.** Sits at a similar level of abstraction but solves
  a different problem. A condition variable lets a thread wait for an
  arbitrary predicate to become true and must always be used alongside a
  mutex protecting that predicate, whereas a semaphore's own counter is the
  entire state being waited on and needs no external mutex around it for its
  own bookkeeping.
- **Barrier.** Incompatible in intent, though built from similar low-level
  primitives. A barrier makes every participant wait until all participants
  have arrived, then releases them together, a rendezvous, whereas a
  semaphore's whole purpose is to let up to N participants proceed
  independently and at different times. Using a semaphore where a barrier is
  needed produces code that looks like it synchronises correctly but does
  not enforce the "all arrive together" property at all.

## 14. Refactoring path in and out

Introducing a semaphore into code that currently has no concurrency limit at
all.

1. Identify the shared, finite resource the unbounded code is contending
   for, a connection pool, an in-memory buffer budget, an external API's
   documented concurrency ceiling, and confirm the true safe concurrent
   capacity of that resource through load testing rather than a guess, per
   the sizing failure mode in dimension 11.
2. Introduce a semaphore initialised to that capacity, scoped as narrowly as
   possible, ideally owned by the same module that owns the resource, not
   shared globally unless the resource is genuinely global.
3. Wrap every call site that uses the resource in an acquire before and a
   release after, using the language's guaranteed-cleanup construct, a
   context manager, `defer`, or `try/finally`, never a manual pair with no
   cleanup guarantee. Do this one call site at a time and run the test suite
   after each, because a missed release at any single site reintroduces the
   permit-leak failure mode.
4. Add a timeout or a cancellation path to the acquire call at every site
   that can itself be cancelled or is bound by a request deadline, so a
   downstream stall does not become an unbounded pile-up, per the unbounded
   queueing failure mode in dimension 11.
5. Instrument the semaphore per dimension 16 before relying on it in
   production, so the permit count chosen in step 1 can be validated and
   retuned against real traffic rather than left as an untested guess.
6. If more than one semaphore is now held by any single code path, establish
   and document the acquisition order across all of them before shipping,
   per the deadlock failure mode in dimension 11.

Removing a semaphore once the constraint it protected no longer applies, the
resource became effectively unlimited, was replaced by a managed pool
library, or the concurrency shape changed to something a semaphore does not
fit.

1. Confirm the resource genuinely no longer has the constraint. Removing a
   semaphore because it "seems to never block" without confirming the
   underlying resource's capacity changed is how the resource gets
   overwhelmed the next time load increases.
2. If the resource is now managed by a dedicated pool library, migrate call
   sites to the pool's own acquire and release methods one at a time, and
   remove the hand-rolled semaphore only after every call site has moved and
   the tests still pass.
3. If the constraint is genuinely gone, delete the acquire and release calls
   at every site, then delete the semaphore's declaration, verifying with a
   reference search that nothing else still constructs or reads it.
4. Re-run whatever load test originally justified the semaphore's
   introduction to confirm the resource still behaves acceptably without it,
   rather than assuming the absence of an exception during normal testing
   proves safety under peak load.

## 15. Testing and verification

Easier because of the pattern.

- The semaphore is a single, narrow seam. A test can construct one with a
  small permit count, for example one or two, and deterministically drive
  contention by spawning exactly that many blocking holders plus one more,
  then assert the extra holder is blocked and becomes unblocked only after a
  release, without needing to simulate the full protected resource.
- Because acquire and release are explicit calls, a test double for the
  protected resource itself can be trivial, a counter that increments on
  entry and decrements on exit, with an assertion that the counter never
  exceeds the configured permit count across the whole test run.

Harder because of the pattern.

- Concurrency bugs around a semaphore, a leaked permit, a double release, a
  deadlock from nested acquisition, are inherently timing-dependent and can
  pass thousands of test runs before manifesting under a specific
  interleaving that only shows up in production. A green test suite is
  necessary but not sufficient evidence of correctness here.
- Testing the fairness property, that waiters are served in arrival order
  under a fair semaphore, requires controlling the exact order in which
  threads reach the blocking point, which most languages do not make easy
  without a purpose-built synchronisation tool or a deterministic scheduler.

Techniques that apply.

- **Max-concurrency assertion test.** Spawn more concurrent callers than the
  configured permit count, have each one increment a shared atomic counter
  on entering the critical section and decrement it on leaving, and assert
  the counter never exceeds the permit count at any point observed during
  the run. This is the single highest-value test for any semaphore-guarded
  code and should exist for every real usage of one.
- **Leaked-permit regression test.** For every call site that has an
  exception or early-return path, write a test that forces that specific
  path to trigger, then asserts a subsequent acquire still succeeds within a
  bounded time, catching the permit-leak failure mode in dimension 11 at the
  exact site it can occur rather than only in an aggregate stress test.
- **Deterministic interleaving with a scheduler or a race detector.** Go's
  built-in race detector, run with `go test -race`, and equivalent tools in
  other ecosystems, JVM tools such as Java's `jcstress` for micro-level
  concurrency correctness, catch data races in the semaphore's own state
  even when a plain test run does not happen to trigger the interleaving.
  Prefer running the full test suite under whichever race detector the
  language offers as a standard part of continuous integration, not as an
  occasional manual step.
- **Timeout-bounded blocking in tests.** Never assert on a bare, un-timed
  `acquire()` inside a test. Use the timeout-bearing variant and assert on
  the timeout outcome explicitly, so a genuine deadlock in the code under
  test fails the test suite with a clear timeout rather than hanging the
  test runner indefinitely.

## 16. Observability signals

The semaphore's whole job is invisible unless it is explicitly instrumented,
because a healthy semaphore and a saturated one look identical from outside
until someone measures the counter and the wait time.

What to record.

- A gauge of permits currently in use, ideally computed as configured
  maximum minus the live available count, sampled continuously rather than
  only on acquire or release, so a stuck permit shows up even between
  events.
- A histogram of wait time inside acquire, from the moment a caller calls
  acquire to the moment it returns, labelled by the semaphore's identity
  when more than one exists in a process. This is the single most
  actionable signal, because a rising wait-time distribution is the earliest
  warning of undersizing or of a leaked permit.
- A counter of `tryAcquire` failures, where used, since these represent
  callers that were rejected outright rather than queued, and a rising rate
  here means the fail-fast path is now the common path rather than the
  exceptional one.
- A counter of acquire calls versus release calls, tracked separately. In a
  healthy system these two counters converge to the same value once
  in-flight work drains, and a persistent gap between them, acquires
  outpacing releases by a growing margin, is the leading indicator of a
  permit leak long before the available-permit gauge visibly reaches zero.
- Where the protected resource has its own health signal, correlate the
  wait-time histogram against that signal directly, so an operator can see
  whether long waits are caused by the semaphore being undersized or by the
  protected resource itself running slow.

A healthy instance on a dashboard. The in-use gauge oscillates below the
configured maximum and tracks observed request volume, the wait-time
histogram sits near zero with an occasional short tail during traffic
spikes, and the acquire and release counters stay within a small,
bounded delta of each other at every point in time, converging to equal
whenever traffic is quiet.

A failing instance. The in-use gauge pins at the configured maximum and
stays there even during periods of low traffic, which is the visible symptom
of a leaked permit, since a healthy semaphore's in-use count should track
demand and fall when demand falls. The wait-time histogram develops a
growing tail with no matching change in traffic volume, which points at
either undersizing, per dimension 11, or a slowdown in the protected
resource itself rather than in the semaphore. The gap between the acquire
and release counters grows monotonically rather than oscillating around
zero, confirming a leak rather than mere contention. `tryAcquire` failures
climb sharply during a traffic spike, which is the fail-fast path correctly
protecting the resource, but a sustained high rate of failures outside a
spike indicates the configured permit count no longer matches the
resource's real capacity or the system's real demand.

## 17. Security and privacy implications

The pattern is largely silent on data handling in itself, but it sits
directly on the availability side of the security triad, because it is one
of the primary tools used to prevent one part of a system from starving
another, and getting it wrong opens a real denial-of-service surface.

**Denial of service through permit exhaustion by an attacker-controlled
input.** When the number of concurrent operations a single external request
can trigger is itself attacker-influenced, for example a single API call
that fans out into many downstream calls each requiring a permit, an
attacker who can cause many such fan-outs concurrently can exhaust the
semaphore's permits and starve every legitimate caller, even though each
individual request was individually within its own resource budget. Bound
the number of permits any single external request can consume, separately
from the global cap, so one caller's fan-out cannot exhaust capacity meant
to be shared fairly across many callers.

**Slow-loris style holding of permits.** If the work performed while
holding a permit can be made arbitrarily slow by an adversary who controls
part of the input, for example a permit held for the duration of reading a
request body that an attacker can trickle in byte by byte, an attacker
gains a cheap way to hold permits far longer than the honest-case duration
the sizing in dimension 11 assumed, degrading service for everyone else at
low cost to the attacker. Bound the maximum time any single permit may be
held, using the timeout-bearing acquire variant on the caller side and an
independent timeout on the work performed while holding the permit, and
treat a permit held past that bound as a fault to log and, where safe,
forcibly release.

**Information leakage through timing.** A wait-time signal exposed to an
external caller, directly or indirectly through response latency, can leak
information about current system load and, in narrow cases, about whether a
specific resource, for example a per-tenant connection pool, is currently
saturated by another tenant's activity. Where multi-tenant isolation is a
security requirement, per-tenant semaphores rather than one shared semaphore
across tenants avoid one tenant's activity being observable, even
indirectly, through another tenant's request latency.

**Permit-count configuration as an attack surface in itself.** A permit
count that is dynamically configurable at runtime, through a feature flag or
an admin endpoint, becomes a target if that configuration path is not
itself properly authenticated and authorised, since setting the count too
low is a direct, cheap denial-of-service vector and setting it too high
defeats the protection the semaphore exists to provide. Treat any runtime
knob controlling a semaphore's permit count with the same access-control
rigour as any other production configuration that affects availability.

On data privacy specifically the pattern is neutral. It gates access to a
resource, it does not itself observe or transform the data flowing through
that resource, and no dimension of the pattern's own mechanics involves
reading or storing the content of the work being gated.

## Code examples

Three languages where the semaphore is idiomatic in genuinely different
ways. Java shows the classical blocking, thread-based form with explicit
fairness control. Go shows the weighted, context-cancellable form from the
official extended concurrency library. Python shows the coroutine-native
async form, the shape most application code written against the pattern
looks like today in an async runtime. Rust is omitted here because the
idiomatic Rust equivalent for the resource-pooling use case is most often a
bounded channel used as a token pool, which is the channel-based variant
already named in dimension 8 rather than a distinct semaphore type, and
showing it as a fourth example would repeat the Go example's shape with
different syntax rather than illustrate a genuinely different aspect of the
pattern.

### Java

Compiled and run with `javac` and `java` against a local JDK.

```java
import java.util.concurrent.Semaphore;
import java.util.concurrent.atomic.AtomicInteger;

public final class ConnectionPoolDemo {
    private final Semaphore permits;
    private final AtomicInteger inUse = new AtomicInteger(0);
    private final int capacity;

    ConnectionPoolDemo(int capacity) {
        this.capacity = capacity;
        this.permits = new Semaphore(capacity, true);
    }

    void useConnection(String taskName) throws InterruptedException {
        permits.acquire();
        try {
            int now = inUse.incrementAndGet();
            if (now > capacity) {
                throw new IllegalStateException("capacity exceeded: " + now);
            }
            System.out.println(taskName + " holding a connection, in use=" + now);
            Thread.sleep(20);
        } finally {
            inUse.decrementAndGet();
            permits.release();
        }
    }

    public static void main(String[] args) throws InterruptedException {
        ConnectionPoolDemo pool = new ConnectionPoolDemo(2);
        Runnable worker = () -> {
            try {
                pool.useConnection(Thread.currentThread().getName());
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        };
        Thread[] threads = new Thread[5];
        for (int i = 0; i < threads.length; i++) {
            threads[i] = new Thread(worker, "worker-" + i);
            threads[i].start();
        }
        for (Thread t : threads) {
            t.join();
        }
        System.out.println("done, final in-use count=" + pool.inUse.get());
    }
}
```

### Go

Compiled and run with `go run` against the standard library only, no
external module. This shows the channel-based semaphore idiom described in
dimension 8, the standard-library equivalent of the `golang.org/x/sync/semaphore`
package's `Weighted` type cited in dimensions 8 and 9, built here from a
buffered channel so the sample has no third-party dependency to fetch.

```go
package main

import (
	"context"
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

type chanSemaphore struct {
	tokens chan struct{}
}

func newChanSemaphore(capacity int) *chanSemaphore {
	return &chanSemaphore{tokens: make(chan struct{}, capacity)}
}

func (s *chanSemaphore) acquire(ctx context.Context) error {
	select {
	case s.tokens <- struct{}{}:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

func (s *chanSemaphore) release() {
	<-s.tokens
}

func main() {
	capacity := 2
	sem := newChanSemaphore(capacity)
	var inUse int64
	var wg sync.WaitGroup

	for i := 0; i < 5; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
			defer cancel()
			if err := sem.acquire(ctx); err != nil {
				fmt.Printf("worker %d could not acquire: %v\n", id, err)
				return
			}
			defer sem.release()

			now := atomic.AddInt64(&inUse, 1)
			if int(now) > capacity {
				panic(fmt.Sprintf("capacity exceeded: %d", now))
			}
			fmt.Printf("worker %d holding a permit, in use=%d\n", id, now)
			time.Sleep(20 * time.Millisecond)
			atomic.AddInt64(&inUse, -1)
		}(i)
	}
	wg.Wait()
	fmt.Println("done, final in-use count", atomic.LoadInt64(&inUse))
}
```

### Python

Run with `python3` against the standard library `asyncio` module.

```python
import asyncio


async def use_connection(sem: asyncio.Semaphore, name: str, in_use: list[int], capacity: int) -> None:
    async with sem:
        in_use[0] += 1
        if in_use[0] > capacity:
            raise RuntimeError(f"capacity exceeded: {in_use[0]}")
        print(f"{name} holding a connection, in use={in_use[0]}")
        await asyncio.sleep(0.02)
        in_use[0] -= 1


async def main() -> None:
    capacity = 2
    sem = asyncio.Semaphore(capacity)
    in_use = [0]
    tasks = [
        use_connection(sem, f"task-{i}", in_use, capacity)
        for i in range(5)
    ]
    await asyncio.gather(*tasks)
    print("done, final in-use count", in_use[0])


if __name__ == "__main__":
    asyncio.run(main())
```

## 18. References

1. Wikipedia contributors. "Semaphore (programming)".
   https://en.wikipedia.org/wiki/Semaphore_(programming)
   Verified 2026-08-02. Source for the 1962 or 1963 invention date, the
   EWD-35 paper attribution, the P and V operation naming and their Dutch
   etymology, and the counting versus binary semaphore distinction in
   dimension 1.
2. Oracle. *Java SE 21 API Specification*,
   `java.util.concurrent.Semaphore`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/Semaphore.html
   Verified 2026-08-02. Source for the acquire and release method set, the
   fairness constructor parameter and its default, the barging behaviour of
   `tryAcquire`, the no-ownership property, and the pool usage example
   referenced in dimensions 3, 8, 9, and the code example.
3. The Go Authors. Package documentation,
   `golang.org/x/sync/semaphore`.
   https://pkg.go.dev/golang.org/x/sync/semaphore
   Verified 2026-08-02. Source for the weighted semaphore's `Weighted` type,
   its `Acquire`, `TryAcquire`, and `Release` methods, the context-cancellable
   acquire behaviour, and the worker-pool example referenced in dimensions 8
   and 9.
4. Python Software Foundation. *Python 3 documentation*, "Synchronization
   Primitives", `asyncio.Semaphore` and `asyncio.BoundedSemaphore`.
   https://docs.python.org/3/library/asyncio-sync.html#asyncio.Semaphore
   Verified 2026-08-02. Source for the async counter semantics, the
   preferred `async with` context-manager usage, the not-thread-safe
   warning, and the bounded-semaphore over-release behaviour referenced in
   dimensions 8, 9, and 11.
5. Linux man-pages project. `sem_wait(3)`.
   https://man7.org/linux/man-pages/man3/sem_wait.3.html
   Verified 2026-08-02. Source for the POSIX `sem_wait`, `sem_trywait`, and
   `sem_timedwait` semantics referenced in dimensions 8 and 11.
