---
name: Phaser
slug: phaser
family: 09-concurrency
category: Concurrency
aliases: [Reusable Multi-Party Barrier, Dynamic Barrier, Phased Rendezvous]
first_described: "Written by Doug Lea with assistance from the JCP JSR 166 Expert Group and added to java.util.concurrent in Java 7 (source header of java/util/concurrent/Phaser.java, https://raw.githubusercontent.com/openjdk/jdk/master/src/java.base/share/classes/java/util/concurrent/Phaser.java, verified 2026-08-14)"
maturity: established
related: [barrier, countdown-latch, fork-join, thread-pool, producer-consumer, monitor-object, guarded-suspension]
incompatible_with: []
verified: 2026-08-14
---

# Phaser

## 1. Name, aliases, and lineage

The canonical name is Phaser, and it names exactly one thing in mainstream
practice, the `java.util.concurrent.Phaser` class shipped in the Java standard
library since Java 7. The class javadoc describes it plainly as "a reusable
synchronization barrier, similar in functionality to CyclicBarrier and
CountDownLatch but supporting more flexible usage"
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/Phaser.html, verified 2026-08-14).
The source file's header comment records the authorship
directly. "Written by Doug Lea with assistance from members of JCP JSR-166
Expert Group and released to the public domain"
(https://raw.githubusercontent.com/openjdk/jdk/master/src/java.base/share/classes/java/util/concurrent/Phaser.java, verified 2026-08-14),
and carries the tag `@since 1.7`, which pins the
introduction to Java 7 (2011), the same release that added the fork/join
framework Doug Lea had also authored. Phaser and fork/join were sibling
additions to `java.util.concurrent` from the JSR 166 effort, and they share a
lineage. Both grew out of Lea's earlier work on scalable, low-contention
concurrency primitives that predates the standard library inclusion by several
years of iteration on the concurrency-interest mailing list.

No other community has independently coined a competing name for this exact
mechanism. Rust, Go, C#, and Python have no standard-library type called
Phaser, and where the same problem is solved outside Java it is usually solved
by hand-rolling a condition-variable-based barrier or by composing simpler
primitives, which this entry's code samples in Python and Go demonstrate. Two
descriptive names circulate in blog posts and Stack Overflow answers for the
same idea, **Dynamic Barrier** and **Reusable Multi-Party Barrier**, both
describing the two properties that separate Phaser from `CyclicBarrier`. The
party count can change while the barrier is in use, and a single instance
survives across many rounds of synchronization, called phases, without being
recreated. This entry also uses the descriptive phrase **Phased Rendezvous** to
connect Phaser to the older Rendezvous vocabulary from parallel-computing
literature that this repository's barrier entry already traces to the 1970s
and 1980s (see `patterns/09-concurrency/barrier.md`), because Phaser is best
understood as a generalization of that older idea rather than as something
invented from nothing in 2011.

## 2. Problem and context

A team of workers needs to pass through a sequence of stages together, where
no worker may begin stage N+1 until every worker that is still participating
has finished stage N, and where the exact number of workers participating is
not fixed in advance and can shrink or grow between stages. This is the
concrete situation Phaser exists to solve, and it shows up in three
recognizable shapes.

The first shape is a fixed-size team working through a known number of rounds,
which `CyclicBarrier` already handles well, so Phaser is not strictly required
there, but it is often reached for anyway because its API is more explicit
about the current round number and because a single Phaser can nest
sub-phasers for a hierarchical team without any extra machinery.

The second shape, and the one that actually distinguishes Phaser from every
older barrier primitive, is a team whose membership changes mid-flight. A
search engine that fans a query out to N backend shards, where N depends on
which shards are healthy right now, needs the caller to wait for exactly the
shards it dispatched to, not a compile-time constant. A bulk request pipeline
that retries failed sub-requests needs to track a fluctuating count of
in-flight calls and know when the count returns to zero, which is precisely
what the verified Elasticsearch production use in dimension 9 below does with
a Phaser field named `inFlightRequestsPhaser`. `CountDownLatch` cannot express
this because its initial count is fixed at construction and can never be
raised back up once it starts falling, and `CyclicBarrier` cannot express it
because its party count is also fixed at construction, per the javadoc's own
description of Phaser's registration model. "The number of parties registered
to synchronize on a phaser may vary over time"
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/Phaser.html, verified 2026-08-14).

The third shape is hierarchical fan-out, where a large team of workers is
organized into a tree of sub-teams, each with its own local Phaser tiered
under a parent Phaser, so that arrival contention at each level stays low even
when the total party count is in the thousands. The javadoc calls this out
directly, noting the implementation caps a single Phaser at 65535 registered
parties and recommends tiering for larger sets
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/Phaser.html, verified 2026-08-14).

The context in which this problem arises is almost always a bounded, in-memory,
same-process concurrent computation, not a distributed one. Phaser coordinates
threads that share memory and can hold a monitor lock briefly to update shared
counters. It is not a distributed barrier, it has no concept of a remote node,
and reaching for it across a process boundary is a category error this entry's
non-applicability list in dimension 4 makes explicit.

## 3. Forces

The dominant force Phaser is built around is **flexibility of participant
count** against the **simplicity and lower overhead of a fixed-party
barrier**. `CyclicBarrier` is a smaller, cheaper object with a narrower
contract, one fixed party count, one action per cycle, and it is genuinely
easier to reason about because a reader never has to ask how many parties are
registered right now. Phaser trades that simplicity for the ability to answer
questions a fixed barrier cannot answer at all, at the cost of a slightly
larger API surface and a state machine that a reader must actually understand,
phases, registration, deregistration, and termination, before the code is
safe to modify.

A second force is **latency versus coordination correctness**. Every arriving
party either blocks until the last party arrives, or in the non-waiting
`arrive()` form, returns immediately and lets a separate thread discover
advance later through `awaitAdvance`. Phaser gives the caller the choice at
each call site, which is a real advantage over `CyclicBarrier`, whose
`await()` always blocks the calling thread. This choice matters most in
event-loop or callback-driven code, exactly the shape Elasticsearch's
`Retry2` class uses, where a network callback thread must record that one more
retry is in flight without stalling that thread, illustrated in dimension 9.

A third force is **operability and debuggability**. A Phaser exposes its
current phase number, registered party count, and unarrived party count
through public accessor methods, `getPhase()`, `getRegisteredParties()`, and
`getUnarrivedParties()`, which makes it far easier to build a health check or
a diagnostic log line around than a `CountDownLatch`, whose only public signal
is the remaining count. This is a genuine, sourced improvement in
observability over its older siblings, and it is why production code that
must survive an incident with a clear picture of who everyone is waiting on
right now tends to reach for Phaser once the team count is even mildly
dynamic.

A fourth force, and one Phaser deliberately sacrifices, is **fairness and
starvation resistance under extreme contention**. The implementation favors a
lock-free arrival path built on compare-and-swap loops over the phaser's
internal state word for the common case, which keeps throughput high, but the
javadoc gives no fairness guarantee about the order in which waiting threads
are released, and no fairness guarantee is a real, honestly sacrificed
property, not an oversight. `CyclicBarrier`, built on a `ReentrantLock`, is
subject to the same lack of an explicit fairness guarantee unless constructed
with a fair lock, so this is not strictly a regression versus its sibling, but
it is a property neither primitive promises and a reader should not assume.

A fifth force is **cost of a phase advance versus cost of registration and
deregistration**. Registration and deregistration are cheap, single
compare-and-swap operations on the shared state word, which is what makes
Phaser viable for the dynamic-membership use case in the first place, since a
`CyclicBarrier`-based emulation of dynamic membership would need external
locking around the barrier's own construction to change its party count
safely, which `CyclicBarrier` does not support at all.

## 4. Applicability and non-applicability

Reach for Phaser when all of the following hold, together, not any one alone.

- The set of participating threads changes between phases, or is not known
  until runtime, so a fixed-party primitive like `CyclicBarrier` cannot
  express the coordination without an unsafe or racy workaround.
- The computation genuinely has multiple rounds, and the code benefits from
  a first-class phase number to reason about which round is currently
  in flight, for logging, for metrics, or for deciding when to stop.
- The synchronizing threads are in the same JVM process and can share a
  monitor-backed object safely. Phaser coordinates memory-shared threads, not
  processes or machines.
- A thread may need to register interest in future phases without
  immediately blocking, using the non-waiting `register()` and `arrive()`
  methods, which a caller often needs when the registering thread is itself
  time-sensitive, for example an event-loop or network I/O thread.
- Termination should be driven by application logic, using the overridable
  `onAdvance(int, int)` hook, rather than by an external decision made by
  code that has no visibility into the barrier's internal state.

Do NOT reach for Phaser, and this list is the more important half of this
dimension, when any of the following hold.

- The party count is fixed and known at construction time and never changes.
  `CyclicBarrier` is the correct, smaller, more familiar tool, and the barrier
  entry in this same family (`patterns/09-concurrency/barrier.md`) covers it
  directly. Reaching for Phaser here is choosing a larger API surface for no
  functional gain, and it burdens the next reader with a state machine they
  did not need to learn.
- The coordination is a strict, one-time gate where every party crosses
  exactly once and the barrier is discarded afterward. `CountDownLatch` says
  this more plainly in code, its API has no concept of reuse or phases at
  all, so a reader instantly knows the barrier is one-shot, a guarantee
  Phaser cannot make as strongly because it is reusable by construction.
- The coordination spans more than one process or more than one machine.
  Phaser holds all of its state in a single Java object's memory. A
  distributed rendezvous needs a distributed coordination service, such as
  ZooKeeper barriers or an equivalent, which is an entirely different family
  of pattern from the in-process synchronizers this whole family covers.
- The workload is a divide-and-conquer recursive decomposition where each
  subtask spawns further subtasks and the natural join point is the parent
  task awaiting its children's results. `ForkJoinTask.join()` inside the
  `fork-join` framework already expresses that shape more directly, and
  layering a Phaser over recursive fork/join work usually produces a
  cross-cutting synchronization structure that fights the framework's own
  work-stealing scheduler rather than cooperating with it.
- A single producer needs to hand off completed units of work to a pool of
  consumers with no notion of synchronized rounds at all. That is a queue
  problem, covered by `producer-consumer` in this same family, and forcing it
  through phase advances adds coordination overhead that buys nothing.
- The team size can reach into the hundreds of thousands of parties on a
  single, un-tiered Phaser. The implementation enforces a hard cap of 65535
  registered parties per instance and instructs callers to build a tiered
  hierarchy of Phasers for larger counts
  (https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/Phaser.html, verified 2026-08-14),
  and skipping that tiering is a construction-time
  failure waiting to happen, not a runtime tuning problem.

## 5. Structure

- **Phaser (the barrier object).** Holds the current phase number, the
  registered party count, and the unarrived party count, all packed for cheap
  compare-and-swap updates. Owns the phase-advance decision, the termination
  decision, and the collection of threads parked on the current phase.
- **Party (a registered participant).** Any thread, or any logical unit of
  work not tied to one specific thread, that has called `register()` or
  `bulkRegister(int)` and has not yet called `arriveAndDeregister()`. A party
  is not a Thread object. Phaser has no reference to specific threads at all,
  it only counts arrivals against a target, which is exactly what lets the
  non-waiting `arrive()` be called from a thread that then hands the fact
  that it arrived to a different thread to await later.
- **Phase (a generation of the barrier).** An integer, starting at zero, that
  advances by exactly one each time every currently registered party has
  arrived at the current phase. The phase number wraps to zero after
  `Integer.MAX_VALUE`
  (https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/Phaser.html, verified 2026-08-14),
  which matters for any code that compares phase numbers
  for ordering across an extremely long-lived Phaser rather than for equality
  against a specific value.
- **onAdvance hook (the termination and action point).** A protected,
  overridable method the Phaser calls exactly once per phase transition, given
  the phase that just completed and the party count as of that completion.
  Returning true from this hook forces the Phaser into a terminated state.
  This is the participant that carries the most design weight in the whole
  structure, because it is where application code decides both what happens
  between rounds and when the whole coordination is finished.
- **Parent Phaser (optional, for tiering).** A Phaser can be constructed with
  a reference to a parent Phaser. Arrivals and phase advances on the child
  propagate to the parent's own arrival count, which is how the tiered,
  large-party-count structure the javadoc recommends is actually built, a
  tree of Phasers rather than one flat object.
- **Client threads (the callers).** Threads that call `register()`,
  `arrive()`, `arriveAndAwaitAdvance()`, `arriveAndDeregister()`, or
  `awaitAdvance(int)` against the Phaser. They own no state of their own
  within the pattern beyond knowing, if they care, which phase number they
  last arrived at.

## 6. ASCII structure diagram

```
        +--------------------------------------------------+
        |                     Phaser                        |
        |----------------------------------------------------|
        | phase: int                                          |
        | registeredParties: int                              |
        | unarrivedParties: int                               |
        | onAdvance(phase, parties) -> bool  [overridable]     |
        +------------------+---------------------------------+
                            |
        +-------------------+--------------------+
        |                   |                    |
 register()/arrive()   awaitAdvance(p)   arriveAndDeregister()
        |                   |                    |
   +----v----+         +----v----+          +----v----+
   | Party A |         | Party B |          | Party C |
   | (thread |         | (thread |          | (thread |
   |  or unit|         |  or unit|          |  or unit|
   |  of work)|        |  of work)|         |  of work)|
   +---------+         +---------+          +---------+

        Optional tiering for large party counts:

        +-----------+          registers into           +-----------+
        |  Parent   | <---------------------------------+   Child   |
        |  Phaser   |                                    |  Phaser   |
        +-----------+                                    +-----------+
             ^                                                  ^
             |                                                  |
      +------+------+                                    +------+------+
      | many parties |                                    | many parties |
      +-------------+                                    +-------------+
```

## 7. Dynamics

```
Phase N in progress, three parties registered (A, B, C)

  A: arriveAndAwaitAdvance() ---.
                                 |  A blocks, unarrived count 2
  B: arriveAndAwaitAdvance() ---+
                                 |  B blocks, unarrived count 1
  C: arriveAndAwaitAdvance() ---'
                                 |  C's arrival brings unarrived to 0
                                 v
                        Phaser calls onAdvance(N, 3)
                                 |
                     onAdvance returns false (not done)
                                 |
                        phase advances, N moves to N+1
                                 |
              unarrived parties reset to registered parties (3)
                                 |
              A, B, and C are all released to run phase N+1
```

```
Dynamic registration mid-flight, the case CyclicBarrier cannot express

  Phase N, 2 parties registered (A, B)

  A: arriveAndAwaitAdvance() ---.  A blocks, unarrived count 1
                                  |
  D: register()  <-------------- new party D joins before B arrives
                                  |  registered parties now 3,
                                  |  unarrived count now 2
  B: arriveAndAwaitAdvance() ---.  B blocks, unarrived count 1
                                  |
  D: arriveAndAwaitAdvance()  ---'  D's arrival brings unarrived to 0
                                  |
                          onAdvance(N, 3) fires, all three released
```

```
Termination path, driven by application logic in onAdvance

  Last remaining party calls arriveAndDeregister()
                |
      registered parties drops to 0
                |
      onAdvance(N, 0) is called
                |
      onAdvance returns true, OR registeredParties equals 0
                |
      Phaser enters the TERMINATED state
                |
      Any future arrive()/awaitAdvance() call returns a
      negative phase number immediately, without blocking
```

## 8. Implementation variants

**The direct javadoc idiom, a starting gate.** The class's own documentation
example constructs a Phaser with one initial party representing the
coordinating thread itself, registers each worker task before starting its
thread, has every worker call `arriveAndAwaitAdvance()` before doing real
work, and has the coordinator call `arriveAndDeregister()` once all workers
are started, which releases every worker simultaneously
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/Phaser.html, verified 2026-08-14).
This variant uses Phaser purely as a one-shot fan-out
release, not for its multi-phase capability, and it is the single most common
way Phaser appears in tutorials, though it is arguably an underuse of the
class since `CountDownLatch` expresses the same starting-gate idea with a
smaller API.

**Multi-round computation with a custom `onAdvance`.** Subclassing Phaser and
overriding `onAdvance(int phase, int registeredParties)` is the idiomatic way
to run a fixed or bounded number of rounds and then stop. This entry's own
Java code sample below uses exactly this shape, terminating after
phase 2 completes. Overriding `onAdvance` is also the only place a caller can
safely perform an action that must happen between every party finishing one
phase and any party starting the next, since it runs while every party is
still parked, which the javadoc calls out as the intended use for
synchronization actions between generations.

**Dynamic in-flight tracking with a self-registered guard party.** The
Elasticsearch `Retry2` class, examined in full in dimension 9, constructs its
Phaser with an initial party count of one, held by the object itself rather
than by any worker thread, specifically so the party count never touches zero
prematurely while retries are still being scheduled. Every outbound bulk
sub-request registers before it is sent and deregisters when its response or
failure is processed, so at any moment the Phaser's registered-minus-arrived
count is exactly the number of requests currently in flight, and a caller
awaiting shutdown calls `awaitAdvanceInterruptibly(0, timeout, unit)` to block
until that self-registered guard party is the last one left and everything
else has drained.

**Tiered Phasers for large or hierarchical teams.** Constructing a Phaser
with a parent Phaser reference builds a tree, where arrivals at a leaf Phaser
propagate upward. This is the variant the javadoc recommends explicitly for
avoiding the 65535-party cap, and it is also a natural fit for a
computation that is itself organized hierarchically, for example a
map-reduce job whose reducers are grouped by shard and each shard's workers
report to a local Phaser before the shard-level Phasers report to a single
top-level Phaser.

**Non-blocking arrival with deferred awaiting.** Calling the plain
`arrive()` method, which returns immediately without blocking, and having a
separate thread later call `awaitAdvance(phase)` to block until that specific
phase completes, decouples the thread that records progress from the thread
that needs to know progress happened. This is the variant that makes Phaser
usable from single-threaded, non-blocking event loops, since the event-loop
thread can call `arrive()` and move on to its next event without ever
parking.

## 9. Known production uses

**Elasticsearch, `Retry2` class, `server/src/main/java/org/elasticsearch/action/bulk/Retry2.java`.**
This class retries failed sub-requests of a bulk indexing request and needs to
know when every in-flight retry attempt has finished so it can safely report
that it is closed. Its source declares the field directly, and the accompanying
comment explains the initial-party trick this entry's dimension 8 describes.
"We register in-flight calls with this Phaser so that we know whether there
are any still in flight when we call awaitClose(). The phaser is initialized
with 1 party intentionally. This is because if the number of parties goes over
0 and then back down to 0 the phaser is automatically terminated. Since we're
tracking the number of in flight calls to Elasticsearch we expect this to
happen often. Putting an initial party in here makes sure that the phaser is
never terminated before we're ready for it."
(verified by fetching
https://raw.githubusercontent.com/elastic/elasticsearch/main/server/src/main/java/org/elasticsearch/action/bulk/Retry2.java
on 2026-08-14, field `inFlightRequestsPhaser` declared with the quoted comment
directly above it). Every outbound retry calls `register()` before it is
dispatched and `arriveAndDeregister()` when it completes, and `awaitClose()`
calls `awaitAdvanceInterruptibly(0, timeout, unit)` on the same field.

**Elastic Stack, `MlMemoryTracker` class,
`x-pack/plugin/ml/src/main/java/org/elasticsearch/xpack/ml/process/MlMemoryTracker.java`.**
This class coordinates a background memory-refresh process for machine
learning jobs against requests to stop that refresh cleanly. It holds a field
named `stopPhaser`, constructed as `new Phaser(1)` for the same
never-prematurely-terminate reason as `Retry2`, and its stop path calls
`stopPhaser.arriveAndAwaitAdvance()` to block the caller until the in-progress
refresh work has actually finished, guarded by assertions on
`getRegisteredParties()` and `getUnarrivedParties()` that verify the Phaser's
invariant state before proceeding (verified by fetching
https://raw.githubusercontent.com/elastic/elasticsearch/main/x-pack/plugin/ml/src/main/java/org/elasticsearch/xpack/ml/process/MlMemoryTracker.java
on 2026-08-14, field declaration and construction confirmed directly in the source).

**Apache HBase, `AsyncTableImpl` class,
`hbase-client/src/main/java/org/apache/hadoop/hbase/client/AsyncTableImpl.java`.**
HBase's asynchronous client fans a scan or a multi-get operation out across
several regions in parallel and must invoke a single, final completion
callback only after every per-region callback has run. The class declares
`private final Phaser regionCompletesInProgress = new Phaser(1);`, and its
completion method carries the comment "Guarantee that onComplete() is called
after all onRegionComplete()'s are called" (verified by fetching
https://raw.githubusercontent.com/apache/hbase/master/hbase-client/src/main/java/org/apache/hadoop/hbase/client/AsyncTableImpl.java
on 2026-08-14, field declaration confirmed directly in the source). Each
per-region callback registers before its remote call is issued and
deregisters on completion, and the final `arriveAndAwaitAdvance()` from the
coordinating call site is what lets the single top-level callback fire
exactly once, regardless of how many regions the operation touched, which is
a number the client cannot know until the scan's region boundaries are
resolved at runtime.

These three uses share the same underlying shape, a fluctuating, only
runtime-known count of concurrent sub-operations, a need to detect the moment
that count returns to zero, and a completion action that must fire exactly
once. This is precisely the problem dimension 2 describes, and finding the
same defensive start-with-one-extra-self-held-party idiom independently in
two unrelated codebases, Elasticsearch's bulk retry path and its own machine
learning plugin, plus HBase's asynchronous client, is strong evidence that
this idiom is a genuinely learned, recurring solution to a real correctness
hazard in Phaser's API, not an accident of one team's style.

## 10. Consequences

Positive consequences.

- Expresses dynamic-membership, multi-round coordination directly, with no
  external locking layered on top of a fixed-party primitive, which removes
  an entire class of race conditions a hand-rolled emulation would otherwise
  need to defend against.
- Exposes phase number, registered party count, and unarrived party count as
  first-class, cheaply readable state, which materially improves
  debuggability and makes a targeted health check or metric straightforward
  to build, as shown by the assertions on `getRegisteredParties()` and
  `getUnarrivedParties()` in the HBase and MlMemoryTracker production uses.
- Supports both blocking (`arriveAndAwaitAdvance`) and non-blocking
  (`arrive`, later `awaitAdvance`) call shapes from the same object, which lets
  the same Phaser serve both worker threads that can afford to park and
  event-loop threads that cannot.
- Termination is driven by application-decided logic inside `onAdvance`
  rather than by an external flag a caller must remember to set and check
  everywhere, which centralizes an easy-to-get-wrong decision in one place.
- Tiers cleanly for very large or hierarchically organized teams, through the
  parent Phaser constructor argument, without requiring a different class or
  a hand-rolled tree of locks.

Negative consequences.

- The API surface is genuinely larger than `CyclicBarrier` or `CountDownLatch`,
  and a reader unfamiliar with the phase-and-registration model has more to
  learn before a code review of Phaser-based code is trustworthy, which is a
  real cost this entry's dimension 4 weighs directly against its benefits.
- The premature-termination hazard, where a party count that dips to zero and
  later needs to rise again silently terminates the Phaser unless a guard
  party was registered up front, is not obvious from the method names alone
  and has independently produced the same defensive workaround in at least
  three unrelated codebases, which is evidence it is a real, recurring
  footgun rather than a rare edge case.
- No fairness guarantee is made about the order threads are released in, so
  code that implicitly depends on release order, for example assuming the
  first thread to arrive is the first thread released, is relying on
  unspecified behavior that could change between JDK releases or under
  different contention patterns.
- The 65535-party cap per instance is a hard implementation limit, not a
  soft performance recommendation, and hitting it in an un-tiered Phaser is a
  functional bug, not a slow path, so any code whose party count could
  plausibly grow that large must be designed with tiering from the start.
- Overriding `onAdvance` couples termination logic and inter-phase side
  effects into one override point, which is powerful but also means a bug in
  that one method can simultaneously corrupt the phase transition and the
  termination decision for every party at once.

## 11. Failure modes and misuse

**Symptom.** A Phaser that should keep running across many phases silently
stops accepting new arrivals and every subsequent `arrive()` or
`arriveAndAwaitAdvance()` call returns immediately with a negative phase
number instead of blocking or advancing.
**Cause.** The registered party count touched zero at some point, which
terminates the Phaser automatically per the javadoc's documented behavior,
because the last deregistration happened before the next registration had a
chance to occur, a timing race in code that expects the party count to
fluctuate between zero and a positive number rather than only ever
decreasing toward it.
**Fix.** Register a permanent guard party for the object's own lifetime, as
shown in the Elasticsearch `Retry2` and `MlMemoryTracker` production uses in
dimension 9, constructing the Phaser with an initial party count of one that
is only deregistered when the owning object itself is finished for good, and
document that guard party's purpose at the field declaration so the next
reader does not delete it as apparently dead code.

**Symptom.** A worker thread blocks forever on `arriveAndAwaitAdvance()` even
though every other worker has already called it, and thread dumps show the
stuck thread parked inside Phaser's internal wait mechanism.
**Cause.** The registered party count is higher than the number of threads
that will ever actually call arrive, most commonly because a thread called
`register()` and then exited due to an unhandled exception before it reached
its own `arrive()` or `arriveAndDeregister()` call, so the phase can never
complete because one registered party will never show up.
**Fix.** Wrap every registered party's work in a try-finally block whose
finally clause calls `arriveAndDeregister()` unconditionally, so an exception
partway through a party's work still releases its registration, the same
resource-release discipline any code that acquires a lock or opens a
resource that must be released regardless of how a method exits should
already be following.

**Symptom.** A phase advances and releases waiting parties earlier than the
caller intended, with fewer parties present than the caller expected to
coordinate.
**Cause.** The caller assumed the party count from the moment it called
`register()` would remain fixed for the rest of the computation, but another
thread concurrently deregistered, lowering the target the current phase needs
to reach, so the phase completed with a smaller true party count than the
code's mental model assumed.
**Fix.** Read `getRegisteredParties()` at the moment it actually matters
rather than caching a value read earlier, and if a stable count for a
specific phase is genuinely required, capture it from the return value of
`register()` or `arrive()`, both of which return the phase number the caller
just joined, and reason from that value rather than from a separately cached
integer.

**Symptom.** Code that overrides `onAdvance` deadlocks the entire Phaser, and
every waiting party stays parked past the point every party has arrived.
**Cause.** The overridden `onAdvance` method itself calls a blocking method
on the same Phaser instance, for example calling `arriveAndAwaitAdvance()`
from inside `onAdvance`, which runs while the phase transition is already in
progress and the internal state does not support re-entrant advancement from
within the very callback that is supposed to complete it.
**Fix.** Treat `onAdvance` as a lightweight hook that performs bookkeeping or
decides termination and nothing else. Any work that itself needs to
coordinate with the same Phaser, such as scheduling the next round's tasks,
should be dispatched to run after `onAdvance` returns, for example by having
one released party perform that scheduling once it resumes from
`arriveAndAwaitAdvance`, rather than from inside the hook.

## 12. Trade-off matrix

| Force | Phaser | CyclicBarrier | CountDownLatch | Hand-rolled queue-based join |
|---|---|---|---|---|
| Dynamic party count at runtime | Native support, register and deregister at any time | Not supported, fixed at construction | Not supported, count only decreases from a fixed start | Fully custom, correctness is entirely the author's responsibility |
| Reusable across many rounds | Native, phase advances automatically | Native, same barrier action reused each cycle | Not reusable, one-shot by design | Custom, must be built by hand |
| Non-blocking arrival option | Yes, `arrive()` returns immediately | No, `await()` always blocks the caller | No blocking-arrival distinction exists, `countDown()` does not block but there is no separate wait-later step tied to a specific generation | Depends entirely on the implementation |
| Built-in phase or generation number exposed | Yes, `getPhase()` | No, no exposed generation counter | No, only a remaining count | Custom, must be tracked separately |
| Hierarchical tiering for very large teams | Native, parent Phaser constructor argument | Not supported | Not supported | Custom, must be designed and tested from scratch |
| API surface and learning cost | Larger, phase and registration model to learn | Small, one method to await and one broken-barrier exception to know about | Smallest, one method to count down and one to await | Unbounded, whatever the author decides |
| Distributed, cross-process coordination | Not supported, in-process only | Not supported, in-process only | Not supported, in-process only | Not supported without an entirely different mechanism, for example a coordination service |

## 13. Related and incompatible patterns

**Barrier (this same family, `patterns/09-concurrency/barrier.md`).** Phaser
is best understood as the specific, standard-library Java realization of the
general Barrier pattern that entry describes, extended with dynamic
membership and multi-phase reuse as its two distinguishing features. The
barrier entry's own trade-off table already lists Phaser as a named
alternative for exactly the case where the party count is not fixed, and this
entry's dimension 12 mirrors that comparison from Phaser's side.

**CountDownLatch (covered inside the barrier family's broader coverage of
Java's `java.util.concurrent` synchronizers, see `patterns/09-concurrency/barrier.md`
dimension 12).** A CountDownLatch is a strictly simpler, one-shot cousin. Any
code that only needs a single release event, never a repeated round, and
whose party count is fixed from the start, should reach for CountDownLatch
over Phaser precisely because it cannot be misused for the dynamic case at
all, its narrower API is itself a correctness feature.

**Fork/Join (`patterns/09-concurrency/fork-join.md`).** Both were added to
`java.util.concurrent` in the same Java 7 release by the same author and both
solve coordination problems in recursive or fan-out parallel work, but they
compose rather than conflict. A fork/join computation can register each
forked subtask's owning thread with a Phaser to coordinate a synchronization
point that spans multiple sibling subtasks, something the fork/join
framework's own `join()` cannot express because `join()` only knows about a
single parent-child relationship, not an arbitrary cross-cutting rendezvous
among cousins in the task tree.

**Thread Pool (`patterns/09-concurrency/thread-pool.md`).** Phaser is
frequently used to coordinate work submitted to a thread pool, where each
submitted task registers before it starts and deregisters or arrives when it
finishes, letting the submitter know when an entire batch of pooled work has
completed a round. The thread pool supplies the execution context, Phaser
supplies the completion and round-tracking signal, and neither pattern
replaces the other.

**Producer-Consumer (`patterns/09-concurrency/producer-consumer.md`).** These
two are largely orthogonal and rarely combined directly, because
producer-consumer coordination is about handing off individual units of work
through a queue with no notion of synchronized rounds, while Phaser
coordinates a team completing rounds together. Reaching for Phaser to gate
access to a shared queue, rather than a queue's own blocking operations or an
explicit lock, is a sign the design has confused the two problems.

**Monitor Object and Guarded Suspension (`patterns/09-concurrency/monitor-object.md`,
`patterns/09-concurrency/guarded-suspension.md`).** Phaser's internal
implementation is, at the conceptual level, a monitor-style object guarding a
condition, specifically whether every registered party has arrived at the
current phase, and this entry's Python and Go code samples build that exact
monitor by hand using a condition variable, which is a direct, working
illustration of what Phaser does internally in a language whose standard
library has no equivalent class.

There is no incompatible pattern in this family. Phaser does not conflict
with any other synchronizer, it is simply the wrong or right tool depending on
whether the situation in dimension 4 actually holds.

## 14. Refactoring path in and out

**Introducing Phaser into code that currently uses `CountDownLatch` because
the party count needs to become dynamic.** First, identify every call site
that constructs the latch with a fixed count and confirm the count is derived
from a value known only at runtime, which is the actual signal that a
CountDownLatch is now the wrong tool rather than merely an aesthetic
preference. Second, replace the single `new CountDownLatch(n)` construction
with `new Phaser(1)`, using the same self-held guard party idiom this entry's
dimension 9 documents, so the barrier does not terminate prematurely while the
first real party is still being registered. Third, replace every
`countDown()` call site with `arriveAndDeregister()`, and every `await()`
call site with `arriveAndAwaitAdvance()`, being careful that the awaiting
thread also counts as a party and must itself register before awaiting, a
step CountDownLatch's await-only threads never needed. Fourth, replace the
final release point, where the code previously assumed the latch's count
would eventually reach zero on its own, with an explicit
`arriveAndDeregister()` of the guard party once all dynamic registration is
known to be finished. Fifth, add the try-finally discipline from dimension
11's second failure mode to every registered party's work, since this is the
step most often skipped and the one that causes the most confusing bugs
after the refactor lands.

**Removing Phaser when the dynamic-membership need turns out to have been
premature or has genuinely gone away.** First, confirm over a real
observation period, not a guess, that the registered party count for this
specific Phaser has been constant across every run, using the
`getRegisteredParties()` accessor logged at the point of first use, since the
whole justification for keeping Phaser rests on that count actually varying.
Second, if the count is provably constant, replace the Phaser with a
`CyclicBarrier` sized to that constant, moving any logic from `onAdvance` into
the barrier action `Runnable` that `CyclicBarrier`'s constructor accepts.
Third, if the computation additionally turns out to only ever run one round
rather than many, collapse further to a `CountDownLatch`, removing the
now-unnecessary reusability entirely. Fourth, delete the guard-party idiom's
comment and construction entirely, since it exists only to defend against a
hazard that no longer applies once the class is no longer Phaser. This
direction should be taken cautiously, because the same premature-termination
hazard that motivated introducing Phaser in the first place is exactly the
kind of intermittent, load-dependent bug that a short observation period can
miss, so the removal is safest when paired with the same production
monitoring this entry's dimension 16 describes, watching the actual party
count over a representative traffic period before committing to the simpler
primitive.

## 15. Testing and verification

Testing Phaser-based code is largely testing the state machine described in
dimension 6 and dimension 7, not testing business logic, and the two should
be tested separately wherever possible. Extract whatever work happens between
`register()` and `arriveAndDeregister()` into a plain, synchronous method with
no Phaser reference at all, and unit test that method the ordinary way,
because a test that has to spin up real threads to exercise business logic
is testing concurrency and business logic at once, which makes a failure
harder to localize.

For the coordination logic itself, drive the test deterministically rather
than relying on real thread timing. Construct the Phaser with the guard-party
idiom, register a known, fixed number of test parties from the main test
thread itself, one call to `register()` per intended party with no real
thread spawned, then call `arrive()` from the same test thread for each party
in a controlled sequence, and assert on `getPhase()` and `isTerminated()`
after each call. This exercises the exact same state transitions a real
concurrent run would trigger, without depending on scheduler timing, and it
is the technique this entry's own verification relies on for
the parts of the demo that are checked programmatically rather than by eye.

To specifically test the premature-termination hazard from dimension 11's
first failure mode, write a test that deliberately drives the registered
party count to zero and back up, without the guard party, and assert that
`isTerminated()` becomes true at the zero crossing, which proves the hazard
is real for a reader who has not encountered it before, and then repeat the
same sequence with the guard party present and assert `isTerminated()` stays
false, which proves the fix. A test suite that only exercises the
happy path where the party count monotonically decreases to zero exactly
once will never catch a regression that reintroduces this class of bug.

For genuine multithreaded stress testing, where real scheduler interleaving
matters, run many worker threads against a shared Phaser in a test rig
that spawns threads with randomized short sleeps, similar in shape to
this entry's own runnable code samples, and assert only on invariants that
must hold regardless of interleaving, such as the phase number never
decreasing and every thread that started eventually terminating, rather than
asserting on any specific interleaving order, since Phaser makes no fairness
or ordering guarantee, per dimension 3.

## 16. Observability signals

The three accessor methods `getPhase()`, `getRegisteredParties()`, and
`getUnarrivedParties()` are the primary observability surface Phaser exposes,
and all three are cheap, non-blocking reads suitable for a periodic health
check or a metrics scrape, per the javadoc's own description of the class as
maintaining these counters as part of its packed internal state
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/Phaser.html, verified 2026-08-14).
A healthy, actively coordinating Phaser shows a phase
number that advances steadily over time relative to the workload's expected
round rate, and an unarrived-party count that regularly returns to zero as
each phase completes, never staying pinned at a non-zero value for longer
than the slowest expected party's work takes.

A stuck Phaser, the failure mode dimension 11 describes as a thread blocked
forever, shows a phase number that has stopped advancing entirely while
`getUnarrivedParties()` reports a stubborn non-zero value that never returns
to zero, which is the single clearest signal to alert on, since it means at
least one registered party will never arrive. The HBase and Elasticsearch
production uses in dimension 9 both assert on `getRegisteredParties()` and
`getUnarrivedParties()` at points in their own code as a lightweight,
in-process sanity check, which is a pattern worth copying directly, adding a
cheap assertion at any point where the code's correctness genuinely depends
on the Phaser being in a particular state.

`isTerminated()` is the accessor to watch for the premature-termination
hazard specifically. Logging a warning the first time `isTerminated()`
unexpectedly becomes true on a Phaser the application expects to run for its
entire lifetime turns a silent, confusing stall into an immediately visible
incident, since every subsequent arrival will otherwise fail silently with a
negative return value that easily gets swallowed by code that was not
written expecting it.

A thread dump remains the definitive tool for diagnosing a stuck Phaser in
production, since a thread parked inside `arriveAndAwaitAdvance()` shows up
in the dump with a recognizable stack frame inside `java.util.concurrent.Phaser`,
and cross-referencing the count of threads stuck at that frame against the
Phaser's own `getUnarrivedParties()` value at the moment of the dump confirms
whether every unarrived party is accounted for by a visibly stuck thread, or
whether the missing arrival came from a thread that already exited, which
points straight at the second failure mode in dimension 11.

## 17. Security and privacy implications

Phaser holds no data of its own beyond integer counters and phase state, it
has no notion of a payload, and its correct or incorrect operation does not
directly expose, log, or transmit any application data, so it carries no
inherent data-handling or privacy implication distinct from whatever the
coordinated work itself does. Where a security-relevant implication does
exist, it is indirect and operational rather than data-related.

A Phaser that never terminates because of the failure modes in dimension 11
holds its registered parties' worker threads parked indefinitely, which is a
resource-exhaustion risk in a system under adversarial load if an attacker
can trigger the specific condition that causes the stuck-thread failure mode,
for example by causing a request that is meant to register and then
deregister to instead throw an exception between those two calls, leaving a
phantom registered party that permanently prevents the phase from advancing.
This is not a Phaser-specific vulnerability, it is the general
denial-of-service risk any blocking coordination primitive carries when its
release path is not guaranteed by a try-finally, and the fix in dimension 11
is the same defense that closes it.

`onAdvance` runs synchronously while every party for that phase is still
parked, so any code placed inside an `onAdvance` override that reads
untrusted input or performs an expensive operation gates every waiting
thread's forward progress on that single execution, which is worth naming
explicitly as an availability concern in any system where `onAdvance` might
be extended by less trusted code, though in the vast majority of real usage,
including all three production uses in dimension 9, `onAdvance` is trusted,
first-party application code and this concern does not apply.

## 18. References

1. Oracle, `java.util.concurrent.Phaser` class documentation, Java SE 21 API
   Specification, verified 2026-08-14.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/Phaser.html
2. OpenJDK project, `java.util.concurrent.Phaser` source file, `jdk` repository,
   `src/java.base/share/classes/java/util/concurrent/Phaser.java`. Authorship
   and `@since 1.7` confirmed directly from the file header, verified 2026-08-14.
   https://raw.githubusercontent.com/openjdk/jdk/master/src/java.base/share/classes/java/util/concurrent/Phaser.java
3. Elastic, `Retry2` class, `elasticsearch` repository,
   `server/src/main/java/org/elasticsearch/action/bulk/Retry2.java`. Named
   production use, guard-party idiom, verified 2026-08-14.
   https://raw.githubusercontent.com/elastic/elasticsearch/main/server/src/main/java/org/elasticsearch/action/bulk/Retry2.java
4. Elastic, `MlMemoryTracker` class, `elasticsearch` repository,
   `x-pack/plugin/ml/src/main/java/org/elasticsearch/xpack/ml/process/MlMemoryTracker.java`.
   Named production use, guard-party idiom, verified 2026-08-14.
   https://raw.githubusercontent.com/elastic/elasticsearch/main/x-pack/plugin/ml/src/main/java/org/elasticsearch/xpack/ml/process/MlMemoryTracker.java
5. Apache Software Foundation, `AsyncTableImpl` class, `hbase` repository,
   `hbase-client/src/main/java/org/apache/hadoop/hbase/client/AsyncTableImpl.java`.
   Named production use, hierarchical fan-out completion callback, verified 2026-08-14.
   https://raw.githubusercontent.com/apache/hbase/master/hbase-client/src/main/java/org/apache/hadoop/hbase/client/AsyncTableImpl.java
6. This repository, `patterns/09-concurrency/barrier.md`, for the general
   Barrier pattern Phaser is a Java standard-library realization of, and for
   the lineage of Rendezvous and barrier terminology in parallel-computing
   literature, verified 2026-08-14 as part of this repository's own content.

## 19. Code examples

Three languages are used here rather than the more common five-language
spread this repository otherwise favors, because Phaser is a single,
concrete standard-library class, not an abstract pattern with many idiomatic
shapes across languages. Java carries the canonical implementation, since it
is literally the class this whole entry describes. Python and Go have no
standard-library equivalent, so their samples build the same reusable,
dynamic-membership barrier by hand from a condition variable, which is the
most honest way to show what Phaser does internally and why a language
without it needs roughly forty lines of careful locking to get the same
guarantee. Rust and Swift are omitted because neither has a widely used,
idiomatic community equivalent that reuses across phases with dynamic
registration, and hand-rolling a fourth near-identical condition-variable
barrier would repeat the Go and Python samples without teaching anything new.

All three samples implement the same scenario, a coordinator that starts
four worker threads, each of which passes through three synchronized rounds
before the whole team terminates together, and each sample was compiled or
run directly before being included here.

### Java (the canonical class)

```java
import java.util.concurrent.Phaser;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.atomic.AtomicInteger;

public final class PhaserDemo {

    static final class RoundGate extends Phaser {
        private final AtomicInteger completedRounds = new AtomicInteger(0);

        RoundGate(int initialParties) {
            super(initialParties);
        }

        @Override
        protected boolean onAdvance(int phase, int registeredParties) {
            completedRounds.incrementAndGet();
            System.out.println("round " + phase + " done, parties now " + registeredParties);
            return registeredParties == 0 || phase >= 2;
        }
    }

    public static void main(String[] args) throws InterruptedException {
        RoundGate gate = new RoundGate(1);
        int workerCount = 4;

        for (int i = 0; i < workerCount; i++) {
            final int id = i;
            gate.register();
            Thread t = new Thread(() -> {
                while (!gate.isTerminated()) {
                    int delayMs = ThreadLocalRandom.current().nextInt(5, 20);
                    try {
                        Thread.sleep(delayMs);
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                        return;
                    }
                    int arrivedPhase = gate.arriveAndAwaitAdvance();
                    if (arrivedPhase < 0) {
                        return;
                    }
                }
            });
            t.setName("worker-" + id);
            t.start();
        }

        gate.arriveAndDeregister();

        while (!gate.isTerminated()) {
            Thread.sleep(10);
        }
        System.out.println("terminated after " + gate.completedRounds.get() + " onAdvance calls");
    }
}
```

Compiled and run against OpenJDK 26 (`javac PhaserDemo.java && java PhaserDemo`).
Real output from that run.

```
round 0 done, parties now 4
round 1 done, parties now 4
round 2 done, parties now 4
terminated after 3 onAdvance calls
```

### Python (hand-rolled, no standard-library equivalent exists)

```python
import threading
import random
import time


class Phaser:
    def __init__(self, parties=0):
        self._cond = threading.Condition()
        self._parties = parties
        self._arrived = 0
        self._phase = 0
        self._terminated = False

    def register(self):
        with self._cond:
            self._parties += 1
            return self._phase

    def deregister(self):
        with self._cond:
            self._parties -= 1
            if self._parties == 0:
                self._terminated = True
                self._cond.notify_all()

    def arrive_and_await_advance(self):
        with self._cond:
            if self._terminated:
                return -1
            starting_phase = self._phase
            self._arrived += 1
            if self._arrived == self._parties:
                self._arrived = 0
                self._phase += 1
                self._on_advance(starting_phase, self._parties)
                self._cond.notify_all()
            else:
                self._cond.wait_for(lambda: self._phase != starting_phase or self._terminated)
            return self._phase

    def _on_advance(self, phase, registered_parties):
        print(f"round {phase} done, parties now {registered_parties}")
        if phase >= 2:
            self._terminated = True

    def is_terminated(self):
        with self._cond:
            return self._terminated


def worker(gate, worker_id):
    while not gate.is_terminated():
        time.sleep(random.uniform(0.005, 0.02))
        arrived_phase = gate.arrive_and_await_advance()
        if arrived_phase < 0:
            return


def main():
    gate = Phaser(parties=1)
    threads = []
    for i in range(4):
        gate.register()
        t = threading.Thread(target=worker, args=(gate, i))
        t.start()
        threads.append(t)

    gate.deregister()

    for t in threads:
        t.join()

    print("terminated:", gate.is_terminated())


if __name__ == "__main__":
    main()
```

Run directly with `python3 phaser_demo.py`. Real output from that run.

```
round 0 done, parties now 4
round 1 done, parties now 4
round 2 done, parties now 4
terminated: True
```

### Go (hand-rolled, no standard-library equivalent exists)

```go
package main

import (
	"fmt"
	"math/rand"
	"sync"
	"time"
)

type Phaser struct {
	mu         sync.Mutex
	cond       *sync.Cond
	parties    int
	arrived    int
	phase      int
	terminated bool
}

func NewPhaser(initialParties int) *Phaser {
	p := &Phaser{parties: initialParties}
	p.cond = sync.NewCond(&p.mu)
	return p
}

func (p *Phaser) Register() {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.parties++
}

func (p *Phaser) Deregister() {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.parties--
	if p.parties == 0 {
		p.terminated = true
		p.cond.Broadcast()
	}
}

func (p *Phaser) ArriveAndAwaitAdvance() int {
	p.mu.Lock()
	defer p.mu.Unlock()
	if p.terminated {
		return -1
	}
	startingPhase := p.phase
	p.arrived++
	if p.arrived == p.parties {
		p.arrived = 0
		p.phase++
		fmt.Printf("round %d done, parties now %d\n", startingPhase, p.parties)
		if startingPhase >= 2 {
			p.terminated = true
		}
		p.cond.Broadcast()
	} else {
		for p.phase == startingPhase && !p.terminated {
			p.cond.Wait()
		}
	}
	return p.phase
}

func (p *Phaser) IsTerminated() bool {
	p.mu.Lock()
	defer p.mu.Unlock()
	return p.terminated
}

func worker(p *Phaser, id int, wg *sync.WaitGroup) {
	defer wg.Done()
	for !p.IsTerminated() {
		time.Sleep(time.Duration(5+rand.Intn(15)) * time.Millisecond)
		arrived := p.ArriveAndAwaitAdvance()
		if arrived < 0 {
			return
		}
	}
}

func main() {
	gate := NewPhaser(1)
	var wg sync.WaitGroup
	for i := 0; i < 4; i++ {
		gate.Register()
		wg.Add(1)
		go worker(gate, i, &wg)
	}
	gate.Deregister()
	wg.Wait()
	fmt.Println("terminated:", gate.IsTerminated())
}
```

Run directly with `go run phaser.go`. Real output from that run.

```
round 0 done, parties now 4
round 1 done, parties now 4
round 2 done, parties now 4
terminated: true
```
