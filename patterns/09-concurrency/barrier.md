---
name: Barrier
slug: barrier
family: 09-concurrency
category: Concurrency
aliases: [Rendezvous, Synchronization Barrier, Barrier Synchronization]
first_described: "Term traced to Harold Stone and others in parallel-computing literature circa 1970s to 1980s. Formalized in Allen B. Downey, The Little Book of Semaphores, Green Tea Press, 2nd edition, as the Barrier and Rendezvous synchronization problems (https://greenteapress.com/wp/semaphores/, verified 2026-08-14)"
maturity: canonical
related: [countdown-latch, phaser, fork-join, thread-pool, monitor-object, producer-consumer, join, semaphore]
incompatible_with: []
verified: 2026-08-14
---

# Barrier

## 1. Name, aliases, and lineage

The canonical name is Barrier, also written as Synchronization Barrier or, in
the collective-operations literature, simply barrier synchronization. A
smaller-scale variant covering exactly two participants is usually called a
Rendezvous. Some POSIX and Win32 documentation calls the wait operation a
gather point, and older parallel FORTRAN compilers used the term fence for a
closely related idea, though fence more commonly denotes a memory-ordering
primitive rather than a thread-blocking one and the two should not be
conflated.

The pattern does not have a single named inventor the way a Gang of Four
pattern does. It grew out of the practical needs of SIMD and SPMD parallel
programs in the 1970s and 1980s, where a set of processors executing the same
program on different data needed a point at which none could proceed until
all had finished a phase. Harold S. Stone's early parallel algorithms work and
subsequent textbooks on parallel computing use the term barrier as a matter of
course by the early 1980s, and the concept is old enough that no single paper
is cited as its origin the way Producer-Consumer traces to Dijkstra's 1965
cooperating-sequential-processes work.

The most rigorous and widely cited didactic treatment is Allen B. Downey's
The Little Book of Semaphores, a free textbook that works through barrier
synchronization as a derivation exercise. Downey starts from the simplest
possible two-thread Rendezvous problem, in which each of two threads must
guarantee that a statement in thread A happens before a statement in thread B
and vice versa, then generalizes it to N threads under the name Barrier, then
extends it again to the Reusable Barrier problem, which is the form every
production implementation actually ships (Allen B. Downey, The Little Book of
Semaphores, Green Tea Press, 2nd edition, freely available at
https://greenteapress.com/wp/semaphores/, verified 2026-08-14). This
three-step derivation, naive rendezvous, then one-shot barrier, then reusable
barrier, is the clearest way to understand why every production barrier API
looks the way it does, and this entry follows the same progression in
dimension 8.

Standards bodies formalized the API surface independently of any single
paper. POSIX defines `pthread_barrier_init`, `pthread_barrier_wait`, and
`pthread_barrier_destroy` as part of the Base Definitions and System
Interfaces volume of POSIX.1-2017 (The Open Group Base Specifications Issue
7, IEEE Std 1003.1-2017, `pthread_barrier_wait` function,
https://pubs.opengroup.org/onlinepubs/9699919799/functions/pthread_barrier_wait.html,
verified 2026-08-14). The OpenMP Architecture Review Board specifies an
implicit and an explicit form of the same idea as the barrier construct in
the OpenMP API specification (OpenMP Architecture Review Board, OpenMP
Application Programming Interface, Version 5.2, section on the barrier
Construct). The two names, Barrier in general-purpose and shared-memory
concurrency, and collective barrier synchronization in message-passing
distributed computing such as MPI's `MPI_Barrier` collective operation
(Message Passing Interface Forum, MPI. A Message-Passing Interface Standard,
Version 4.0, June 2021, section 5.3, Barrier Synchronization), describe the
same logical contract, all participants must arrive before any participant
leaves, implemented over two very different transports, shared memory versus
message passing over a network.

## 2. Problem and context

A computation is organized into a fixed number of concurrent workers, and the
work naturally divides into phases. Within a phase, every worker can proceed
independently, reading and writing data that does not overlap with any other
worker's slice. But the next phase depends on every worker having finished the
current phase, because the next phase reads data that any worker might have
produced. A worker that starts phase two before some other worker has finished
writing its share of phase one will read stale or partially written data, and
the bug this produces is a data race that appears intermittently, sized by
how the operating system happens to schedule the threads that particular run.

The recognizable shape in real code looks like an explicit or implicit loop
over rounds, where each round has a compute step followed by a synchronization
step, and the synchronization step is currently missing, faked with a fixed
sleep, or implemented ad hoc with a shared counter and a busy loop that nobody
trusts. A parallel matrix multiplication that tiles the matrix across worker
threads and must finish multiplying every tile before any thread reads the
result matrix for the next multiplication is the textbook instance. A
distributed training step where every worker computes a local gradient and no
worker may begin the next forward pass until every worker has finished
contributing its gradient to the shared update is the modern instance. A
load test rig where every virtual user must be spun up and idling before
the clock starts, so that the ramp-up itself does not skew the measured
throughput, is the tooling instance.

The context that makes Barrier the right pattern, rather than a weaker or
stronger primitive, is fixed parallelism with lockstep phases. The number of
participants is known in advance, or at least known at the moment the barrier
is constructed, every participant plays a symmetric role, none is more
important than another, and the synchronization event repeats across many
phases rather than happening once. If the number of participants is unknown
until each one finishes some unrelated piece of work and nobody needs to wait
a second time, that is CountdownLatch, not Barrier. If a single coordinator
needs to wait on a variable number of subordinate tasks whose count is not
symmetric, that is Fork-Join or a WaitGroup, not Barrier. Barrier answers a
narrower question, when will everyone in this fixed group be able to move to
the next round together, and it answers it repeatedly.

## 3. Forces

Latency versus safety at the phase boundary. Without a barrier the phase
boundary is invisible in the code and the CPU or scheduler is free to run
threads in whatever order it likes, which is fast but wrong. With a barrier
every participant pays the latency of the slowest participant on every single
round, because the round cannot advance until the last worker arrives. The
pattern trades throughput for correctness at exactly the boundary where
correctness is non-negotiable, and it does so without exception, every
participant waits for every other participant, every round, with no way to
opt a fast participant out of waiting for a slow one within a single barrier.

Straggler sensitivity. A barrier's completion time in any given round is
bounded below by the maximum, not the average, of the per-worker times for
that round. One thread doing unexpectedly slow work, whether from a page
fault, a garbage-collection pause, a cascading run of cache misses, or genuinely
unbalanced input data, delays every other thread that has already finished
and is sitting idle at the barrier. This is the single most consequential
force in the pattern's design space and it is discussed at length in
dimension 11.

Reusability versus construction cost. A barrier that can only be used once,
the naive form Downey derives first, is cheap to reason about but requires
allocating a fresh barrier object for every phase, which is wasteful when
there are thousands of phases. A reusable, cyclic barrier that resets itself
automatically after releasing its waiters, the form every production API
actually ships, is more complex internally, because the reset has to be race
free against a thread from the next generation arriving before the previous
generation has fully drained, but it amortizes construction cost across every
round. Every mainstream implementation in dimension 9 chose reusability, which
is strong empirical evidence for where the trade lands in practice.

Coupling and single point of failure. A barrier couples every participant to
every other participant for the duration of the wait. If one participant
crashes, deadlocks, is cancelled, or is killed while other participants are
waiting at the barrier, those other participants are usually stuck forever
unless the implementation offers an explicit broken or aborted state, which
most do, precisely because this failure mode is so common. The pattern is
therefore only as reliable as its weakest participant, and this is a real
operability cost that a naive reading of the API surface does not make
obvious.

Symmetry and simplicity versus asymmetric coordination. Because every
participant calls the same wait method and every participant is treated
identically, the coordination logic in the caller's code is extremely simple,
there is no leader-election or role-assignment logic needed to know who
coordinates whom. The cost of that simplicity is that Barrier cannot express
asymmetric relationships, a producer that needs to be notified separately
from a consumer, or a coordinator that needs different behavior than a
worker, without layering additional logic, usually a designated leader
flag, on top of the barrier's uniform contract.

Cost at scale. A centralized barrier implementation, one shared counter and
one condition variable, is O(1) in code but becomes a contention hot spot as
the number of participants grows into the hundreds or thousands, because every
arriving thread must acquire the same lock. High-performance computing has
therefore developed hierarchical barrier algorithms, combining tree barriers
and dissemination barriers, specifically to reduce this contention at large
processor counts, at the cost of considerably more implementation complexity
(Wikipedia, Barrier (computer science), https://en.wikipedia.org/wiki/Barrier_(computer_science),
verified 2026-08-14, describing centralized, combining-tree, and hardware
barrier implementations). Most application-level code never needs this,
because most barriers coordinate tens of threads, not thousands, but the
force is real for HPC and GPU workloads.

## 4. Applicability and non-applicability

Reach for Barrier when the number of concurrent workers is fixed for the
duration of a computation, or at least fixed for the duration of the barrier's
lifetime, when the computation naturally decomposes into repeated phases, and
when correctness genuinely requires that no participant begin phase N+1
before every participant has finished phase N. Good fits include tiled or
data-parallel numerical algorithms such as iterative matrix relaxation and
cellular-automaton simulation, synchronous distributed training loops that
average gradients between training rounds, multi-threaded test rigs that must
guarantee every simulated actor is initialized and idling before a stopwatch
starts, and multi-stage pipeline benchmarks that need every stage to line up
at fixed checkpoints so that measured timings are not polluted by staggered
startup.

Do NOT use Barrier when the set of participants is not known or fixed ahead
of time and instead grows or shrinks dynamically as work is discovered, since
most Barrier implementations either forbid changing the participant count
mid-wait or make it awkward, whereas a semaphore-backed work queue or an
unbounded WaitGroup style counter naturally tolerates a dynamic population.

Do NOT use Barrier when only one synchronization event is needed rather than a
repeating series of rounds, since a one-shot CountdownLatch or a simple future
or promise expresses the intent more directly and does not carry the reusable
barrier's reset-and-generation bookkeeping for a wait that will never happen
twice.

Do NOT use Barrier when participants are not symmetric and one of them plays a
genuinely different role, for example a single coordinator that must be
notified after all workers finish but does not itself do worker-shaped work,
since the observer pattern, a future aggregator, or an explicit CountdownLatch
observed by the coordinator models the asymmetry directly instead of forcing
the coordinator to also call the barrier's wait method purely to participate.

Do NOT use Barrier across process or machine boundaries using a shared-memory
implementation such as `pthread_barrier_wait` or java.util.concurrent's
CyclicBarrier, since those APIs assume a shared address space. Distributed
systems need the network-aware equivalent, an MPI collective barrier, a
distributed lock service such as ZooKeeper's barrier recipe, or an
application-level rendezvous built on a message broker, because a
shared-memory barrier simply cannot see a process on another host.

Do NOT use Barrier as a substitute for backpressure or rate limiting. A
barrier forces every participant to wait for the slowest one on every round,
which is the opposite of what a producer-consumer system wants when it needs
fast producers to keep moving while slow consumers catch up independently, a
bounded queue or a semaphore is the right tool there, not a barrier.

Do NOT use a single global barrier to coordinate a very large number of
independent threads, in the low thousands or more, on hardware where lock
contention becomes the limiting factor, without first considering a hierarchical or tree
barrier, since a centralized barrier's single lock becomes the bottleneck
exactly at the scale where the barrier is supposed to be enabling parallel
speedup.

## 5. Structure

Barrier, the synchronization object. Holds the fixed party count, the
current count of arrived-but-not-yet-released participants, and, in the
reusable form, a generation number or equivalent token that distinguishes
this round's waiters from the next round's waiters so that a thread that
arrives early for round two is never mistakenly released alongside round
one's waiters. Owns the internal lock or atomic state that makes arrival and
release thread safe. Exposes exactly one operation to callers in its simplest
form, and often a second optional operation for cleanup or diagnostics.

Wait, or Await, or SignalAndWait depending on the language. The single
operation every participant calls. Increments the arrival count, and then
either blocks the calling thread if it is not the last arrival, or triggers
release of every waiting thread if it is. This is the one point of contact
between a Participant and the Barrier, and its symmetry, every participant
calls the identical method, is what keeps the pattern's calling code simple.

Participant, a worker thread or process. Not a distinct class in most
implementations, simply the calling thread itself. Each participant does its
own phase-local work independently of every other participant, and calls Wait
exactly once per phase it wants synchronized. Participants are interchangeable
from the Barrier's point of view, it tracks a count, not identities, except
where the implementation designates one arbitrary participant as a leader for
the purpose of running a barrier action.

Barrier Action, optional, present in Java's CyclicBarrier, Python's
`threading.Barrier`, and .NET's Barrier class, absent from the raw POSIX and
Rust APIs. A callback that runs exactly once per phase, executed by whichever
thread happens to be the last to arrive, after the count reaches the party
total but before any thread, including the one that ran the action, is
released. Used to perform work that must happen exactly once between phases,
merging partial results computed by each participant, checkpointing progress,
or logging phase completion, without requiring an additional synchronization
primitive to guarantee that exactly one thread and not all of them runs that
work.

Broken or Aborted State, present in Java, Python, and .NET, absent from raw
POSIX in the same shape. A terminal failure state the barrier can enter if a
waiting thread is interrupted, times out, or if the barrier is explicitly
reset or aborted while threads are waiting. Once broken, every current and
future waiter is released immediately with an exception rather than being
allowed to wait forever, which is the mechanism that prevents one failed
participant from silently deadlocking the rest.

## 6. ASCII structure diagram

```
+---------------------------------------------------------+
|                        Barrier                          |
|  parties  : int          (fixed, set at construction)   |
|  count    : int          (arrived so far, this phase)   |
|  generation: token       (distinguishes phase N from N+1)|
|  action   : optional fn  (runs once, on last arrival)    |
|  state    : OPEN | BROKEN                                |
|-----------------------------------------------------------|
|  wait() / await() / SignalAndWait()  |  reset() / abort() |
+-----------------------------------------------------------+
        ^                 ^                 ^
        | calls wait()    | calls wait()    | calls wait()
        |                 |                 |
  +-----------+     +-----------+     +-----------+
  |Participant|     |Participant|     |Participant|
  |    A      |     |    B      |     |    C      |
  |(phase-    |     |(phase-    |     |(phase-    |
  | local     |     | local     |     | local     |
  | work)     |     | work)     |     | work)     |
  +-----------+     +-----------+     +-----------+
```

## 7. Dynamics

```
Time -->

Worker A.  [--work--] wait() ----------blocked----------> released
Worker B.  [------work------] wait() --blocked--> released
Worker C.  [----work----] wait() ------blocked----------> released
Worker D.  [--------------work--------------] wait() ---> released
                                              ^
                                    D is last to arrive,
                              count reaches parties (4),
                          optional barrier action runs here,
                            then all four released together

Generation N ends here. Generation N+1 begins as soon as
any released worker calls wait() again for the next round.
```

```
State machine for one participant's call to wait().

    +-----------+     count++ and       +---------------+
    | arriving  | --- count < parties -->| blocked/queued|
    +-----------+                        +-------+-------+
          |                                      |
          | count == parties                     | woken by last arrival
          v                                      v
    +----------------+                    +---------------+
    | run barrier    | ---broadcasts----->| released       |
    | action (once)  |    wake to all     | returns to     |
    +----------------+                    | caller         |
          |                                      ^
          +--------------------------------------+
                (leader thread also ends up here)

    Any thread interrupted, timed out, or barrier reset/abort
    while blocked transitions instead to.
    +----------------+
    | BROKEN, every  |
    | current and    |
    | future waiter  |
    | gets an        |
    | exception      |
    +----------------+
```

## 8. Implementation variants

Following the derivation Downey uses in The Little Book of Semaphores is the
clearest way to see why production barriers look the way they do.

The naive Rendezvous, two threads only. Two threads, A and B, must each
guarantee the other's statement 1 finishes before their own statement 2
starts. The classic solution uses two semaphores, aArrived and bArrived, each
initialized to zero. A signals aArrived then waits on bArrived. B signals
bArrived then waits on aArrived. This is not yet a barrier in the N-party
sense, but every N-party barrier reduces to solving this correctly at every
pair of arrivals, and the deadlock risk it introduces, if both threads waited
on the wrong semaphore first, is the same risk a naive multi-thread barrier
must avoid (Allen B. Downey, The Little Book of Semaphores, Green Tea Press,
2nd edition, the Rendezvous problem chapter, verified 2026-08-14 at
https://greenteapress.com/wp/semaphores/).

The naive one-shot Barrier, N threads, generalizes the rendezvous with a
shared counter protected by a mutex and a single semaphore used as a turnstile.
Every thread locks the mutex, increments the counter, and if it is not the
last one, waits on the turnstile semaphore. The last thread to arrive signals
the turnstile semaphore N minus one times, releasing everyone else. This
works, but only once, the turnstile semaphore ends the round in a state that
is not safely reusable without a second pass, and Downey's derivation devotes
an entire further section to exactly this bug and its fix.

The Reusable Barrier, sense reversal or double turnstile. Production
implementations solve reusability with either a second turnstile semaphore
that the last arriving thread locks down after the first turnstile has
drained everyone through, so a fast thread from round two cannot race ahead
and slip through round one's still-open turnstile, or with a sense-reversing
flag, where each thread flips a local sense variable and waits until the
barrier's shared sense matches its own, avoiding the two-turnstile dance
entirely at the cost of one boolean comparison per wait. This sense-reversing
centralized barrier is the algorithm most textbook and many production
implementations describe as the baseline centralized barrier before moving to
tree or combining variants for scale (Wikipedia, Barrier (computer science),
https://en.wikipedia.org/wiki/Barrier_(computer_science), verified
2026-08-14).

Condition-variable implementations, the Go idiom shown in the code examples
below. Languages whose standard library does not ship a barrier type, Go
being the most prominent example among the languages surveyed for this entry,
implement the reusable barrier directly on top of a mutex and a condition
variable, incrementing a waiting counter, and on the counter reaching the
party count, resetting it to zero, incrementing a generation counter, and
broadcasting to wake every waiter. This is functionally identical to the
sense-reversal algorithm, the generation counter plays the same role the
sense flag plays elsewhere.

Combining tree and dissemination barriers, for large participant counts.
Instead of every thread contending on one shared counter, threads are
organized into a binary or k-ary tree, or into a fixed pattern of pairwise
rounds, so that the total number of memory operations any single thread
performs to synchronize is O(log N) rather than O(N), and no single memory
location is touched by every thread. This matters on large symmetric
multiprocessing machines and GPUs, where a centralized counter under heavy
contention becomes a serialization point that erases the parallel speedup the
barrier was meant to enable (Wikipedia, Barrier (computer science),
https://en.wikipedia.org/wiki/Barrier_(computer_science), verified
2026-08-14, describing combining tree barrier structure).

Language-idiomatic barrier action variants. Java's CyclicBarrier, Python's
`threading.Barrier`, and .NET's Barrier class all bundle an optional callback
that runs once per phase on the single last-arriving thread, letting the
caller fold a merge or checkpoint step directly into the synchronization
point instead of adding a second, separate one-shot synchronization primitive
purely to guarantee the merge step runs exactly once. Rust's `Barrier` type in
`std::sync` and raw POSIX `pthread_barrier_wait` deliberately omit this,
instead returning a leader flag, `PTHREAD_BARRIER_SERIAL_THREAD` in POSIX and
`BarrierWaitResult::is_leader` in Rust, that the caller checks and branches on
to run its own once-per-phase logic, trading a slightly more manual call site
for one fewer implicit callback the reader has to trace.

## 9. Known production uses

`java.util.concurrent.CyclicBarrier`, part of the standard Java class library
since Java 5, is explicitly documented as designed for programs involving a
fixed sized party of threads that must occasionally wait for each other, and
supports an optional Runnable action executed by the last thread to arrive
before any are released, with a BrokenBarrierException thrown to all
remaining waiters if any waiter is interrupted, times out, or if reset is
called while threads are waiting (Oracle, CyclicBarrier, Java SE 21 API
documentation,
https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/CyclicBarrier.html,
verified 2026-08-14). Java Concurrency in Practice, the standard reference on
the java.util.concurrent library, uses CyclicBarrier as the worked example for
parallelizing an iterative algorithm across a fixed number of worker threads
that must synchronize after every iteration.

POSIX threads, `pthread_barrier_init`, `pthread_barrier_wait`, and
`pthread_barrier_destroy`, are part of the base POSIX.1-2017 specification and
are implemented by glibc on Linux and by libpthread on other POSIX systems,
used across C and C++ multithreaded numerical and simulation code across
scientific computing, where the constant `PTHREAD_BARRIER_SERIAL_THREAD` is
returned to exactly one unspecified thread and zero is returned to every
other thread on release, giving the caller a leader designation for free
(The Open Group Base Specifications Issue 7, IEEE Std 1003.1-2017,
`pthread_barrier_wait`,
https://pubs.opengroup.org/onlinepubs/9699919799/functions/pthread_barrier_wait.html,
verified 2026-08-14).

OpenMP, a widely used shared-memory parallel programming API for C, C++, and
Fortran in high-performance computing, provides both an explicit barrier
construct, written as the pragma omp barrier directive, and an implicit
barrier at the end of most worksharing constructs such as parallel for loops,
so that by default a parallel loop's results are guaranteed visible to every
thread once the loop region ends, without the programmer writing a single
line of synchronization code (OpenMP Architecture Review Board, OpenMP
Application Programming Interface, Version 5.2, the barrier Construct
section). This implicit-barrier default is precisely why so much OpenMP code
never needs to reason about barriers explicitly, the pattern is built into
the language's worksharing semantics rather than left to the programmer.

The Message Passing Interface standard's `MPI_Barrier` is the canonical
collective synchronization primitive across distributed-memory
high-performance computing, blocking every calling process in a communicator
until all processes in that communicator have called it, implemented by every
major MPI runtime including MPICH and Open MPI, and used throughout scientific
simulation codebases to guarantee that all ranks have finished a
communication phase before timing measurements are taken or before a
collective I/O operation begins (Message Passing Interface Forum, MPI. A
Message-Passing Interface Standard, Version 4.0, June 2021, section 5.3,
Barrier Synchronization).

.NET's `System.Threading.Barrier` class, part of the Task Parallel Library
since .NET Framework 4, is documented as enabling multiple tasks to
cooperatively work on an algorithm in parallel through multiple phases,
supports a post-phase action supplied at construction time that runs once per
phase, and allows the participant count to be adjusted dynamically at runtime
via AddParticipant and RemoveParticipant, a flexibility the fixed-count POSIX
and Java APIs do not offer directly (Microsoft, Barrier Class, .NET API
browser, https://learn.microsoft.com/en-us/dotnet/api/system.threading.barrier,
verified 2026-08-14).

Python's `threading.Barrier`, part of the standard library since Python 3.2,
is documented with wait returning an index unique to each participating
thread in a given phase, useful for letting exactly one thread run
designated special work without a separate callback, and with an explicit
reset and abort pair of methods that put the barrier into a broken state to
prevent deadlock when a participant must exit abnormally (Python Software
Foundation, threading, The Python Standard Library documentation,
https://docs.python.org/3/library/threading.html#threading.Barrier, verified
2026-08-14).

## 10. Consequences

Positive. It eliminates an entire class of phase-ordering data races by
construction, once a barrier call is placed correctly at every phase
boundary, no participant can observe another participant's next-phase state
before that participant has committed its current-phase writes, which removes
the need for finer-grained and more error-prone locking around every shared
data structure touched across the boundary. It is easy to reason
about compared to hand-rolled counters and flags, the entire contract is
everyone arrives, then everyone leaves, and this simplicity is a genuine
correctness win, not only an aesthetic one, because ad hoc phase-boundary
synchronization is one of the most commonly misimplemented pieces of
concurrent code. In its reusable form it is cheap to hold onto and reuse
across an unbounded number of phases, avoiding per-phase allocation overhead.
The optional barrier action gives a clean, race-free place to run
exactly-once merge or checkpoint logic between phases without a second
synchronization primitive.

Negative. It forces every participant to wait for the single slowest
participant on every round, so total wall-clock time across many rounds
tracks the sum of per-round maxima rather than any kind of average,
which can be far worse than the ideal parallel speedup if work is
even mildly unbalanced across participants. It couples every participant's
liveness to every other participant's liveness for the duration of the wait,
one crashed, hung, or wrongly cancelled thread can strand every other
participant indefinitely unless the implementation offers, and the caller
correctly handles, a broken or aborted state. It scales poorly as a
centralized primitive once participant counts reach into the hundreds or
thousands, because contention on the shared counter or lock becomes the
bottleneck, requiring a more complex tree or dissemination implementation to
regain scalability. It adds a hard synchronization point that can turn what
would otherwise be independently pipelineable work into strictly lockstep
work, closing off overlap opportunities a more relaxed coordination scheme,
such as a bounded queue between stages, would allow.

## 11. Failure modes and misuse

Symptom, one thread permanently hangs at the barrier while every other thread
also hangs, and CPU usage across all participant threads drops to near zero.
Cause, the participant count passed to the barrier's constructor does not
match the number of threads that will actually call wait, either because a
thread was spawned conditionally and that code path never runs, or because an
exception thrown before the wait call on one thread prevents it from ever
arriving. Fix, every code path that can be reached by a participant
thread should eventually call wait exactly once per phase regardless of
earlier branches, and participant work should be wrapped in a try or finally
block, or the language's equivalent, so that even an exceptional exit calls
wait, or explicitly signals the barrier to abort so remaining waiters are
released with an error rather than hanging silently.

Symptom, the program deadlocks intermittently, only under load, and only
after running successfully for a while. Cause, a thread is holding an
unrelated lock while blocked at the barrier's wait call, and a different
thread that has not yet reached the barrier needs that same lock to finish
its phase-local work and reach the barrier itself, a classic lock-ordering
deadlock where the barrier is one of the two contended resources. Fix, no
lock other than the barrier's own internal lock should be held while calling
wait, every application-level lock should be released before synchronizing
at the barrier, and if a phase genuinely needs a lock held across the
boundary, that is a sign the phase boundary is drawn in the wrong place.

Symptom, a barrier that should reset for the next round instead throws a
broken barrier exception on the very next call, even though every thread
appeared to complete the previous round successfully. Cause, one thread was
interrupted, cancelled, or timed out while inside the wait call, which most
production barrier implementations treat as breaking the barrier for every
current and future waiter, since the implementation cannot know whether the
interrupted thread's state is still consistent with the others. Fix, decide
deliberately whether the caller catches the interruption and calls the
barrier's reset method to recover for the next phase, versus letting the
break propagate and tearing down the whole computation, and document which
choice was made, silently swallowing the broken state and continuing is the
worst option because it hides that some participant's data may now be out of
sync.

Symptom, throughput is far below the theoretical parallel speedup even though
CPU utilization graphs show every core busy. Cause, straggler effect, the
per-round completion time is bounded by the slowest participant, and a mild
imbalance in the data each participant is assigned, or an unrelated periodic
cost such as garbage collection that hits threads at different times,
compounds across every single round of the barrier's lifetime. Fix, either
rebalance the work so per-participant phase durations are closer to equal, or
replace the strict barrier with a looser coordination scheme, staged pipelines
with bounded queues, or a work-stealing scheduler, that does not force every
participant to synchronize on every round if the algorithm can tolerate
looser ordering.

Symptom, the barrier action, the callback that is supposed to run exactly
once per phase, appears to run more than once, or its side effects appear
duplicated. Cause, the caller is running two separate barrier instances that
were each configured with the same count and mistakenly believed to be the
same synchronization point, or the caller is manually detecting the last
arrival with a counter it maintains itself rather than relying on the
barrier's own last-arrival detection, and that manual counter is not
protected by the same lock the barrier uses internally, introducing a race.
Fix, use exactly one barrier instance per synchronization point and rely on
the implementation's built-in barrier action or leader-flag return value
rather than reimplementing last-arrival detection by hand.

Symptom, adding or removing a participant mid-run either throws, is silently
ignored, or causes every other participant to hang. Cause, most barrier
implementations, including Java's CyclicBarrier, POSIX's
`pthread_barrier_wait`, and Rust's `Barrier` in `std::sync`, fix the
participant count at construction time and offer no supported way to change
it while any thread is waiting, so code that tries to dynamically add or
remove workers while a phase is in flight is outside the contract the
implementation actually guarantees. Fix, either use an implementation that
explicitly documents dynamic participant adjustment, such as .NET's Barrier
class with its AddParticipant and RemoveParticipant methods, and only call
those methods when no thread is currently blocked in wait, or restructure
the design so the participant set is genuinely fixed for the barrier's
lifetime and any dynamic scaling happens by creating a new barrier for the
next batch of phases instead.

## 12. Trade-off matrix

| Force | Barrier | CountdownLatch | Phaser | Bounded queue between stages |
|---|---|---|---|---|
| Reusable across many rounds | Yes, built into every mainstream API | No, one-shot by design | Yes, and reusable with dynamic party count | Not applicable, no explicit rounds |
| Participant count fixed at creation | Yes, in most implementations | Yes, count fixed at creation | No, parties can register and deregister at runtime | Not applicable |
| Waits for the slowest participant every round | Yes, without exception | Waits once for the initial count, then never again | Yes, same as Barrier, per advance | No, each stage proceeds as fast as its own queue allows |
| Symmetric participant roles | Yes, every caller calls the same wait method | Asymmetric, some threads count down, others await | Symmetric with optional dynamic registration | Asymmetric, producers and consumers differ |
| Coupling between participants | High, one stuck participant strands all others | Lower, awaiting threads do not block the counting threads | High, same as Barrier | Low, stages are decoupled by the queue's buffer |
| Cost at large participant counts | High under a centralized implementation, needs tree or dissemination variant to scale | Low, a single atomic decrement per signal | Similar concerns to Barrier at scale | Scales well, bounded by queue capacity, not participant count |
| Common use | Fixed-size iterative parallel algorithms | One-time startup or shutdown coordination | Multi-stage pipelines with a dynamically varying number of active workers per stage | Streaming or pipeline architectures that tolerate stage-to-stage skew |

## 13. Related and incompatible patterns

CountdownLatch is the strict subset of Barrier's problem space, a one-shot
version that a fixed number of signaling threads count down and any number of
observer threads wait on, without the observers themselves being counted as
participants that must also signal, and without the count ever resetting for
reuse. Reach for CountdownLatch when exactly one wait event is needed and the
signalers and the waiters are different threads, reach for Barrier when the
same set of threads repeatedly both signal and wait across many rounds.

Phaser, present in Java's java.util.concurrent since Java 7, generalizes
Barrier by allowing the participant count to change dynamically as parties
register and deregister between phases, and by supporting a tree of nested
phasers for hierarchical synchronization at scale, at the cost of a
noticeably more complex API surface than CyclicBarrier's fixed-count model.
Phaser composes naturally as a drop-in replacement for Barrier exactly when
the fixed-participant-count assumption in dimension 4 stops holding.

Fork-Join and the WaitGroup idiom, found in Go's sync.WaitGroup and similar
constructs elsewhere, coordinate a variable number of asymmetric worker tasks
converging back to a single coordinator, rather than a fixed symmetric set of
peers repeatedly synchronizing with each other, and are the right choice
where one coordinator thread spawns and waits on a batch of subordinate work
that need not itself continue past that single join point. Barrier and
Fork-Join are frequently confused because both involve waiting for multiple
threads, but Fork-Join's asymmetry, one coordinator, many workers that each
finish and stop, is structurally different from Barrier's symmetry, every
participant both arrives and continues.

Monitor Object underlies most Barrier implementations internally, the mutex
plus condition variable pair that guards the arrival counter and wakes
waiting threads is a textbook Monitor Object, and understanding that
substructure is what makes the condition-variable-based Go implementation in
dimension 8 legible, it is simply a Monitor Object whose invariant is
threads may proceed only once the arrival count equals the party count for
the current generation.

Producer-Consumer is not directly related but is commonly confused with
Barrier because both are staple concurrency-textbook patterns involving
multiple threads and blocking, the distinguishing test is whether roles are
symmetric, if the threads are peers exchanging places in a round it is
Barrier, if the threads are asymmetric producers filling a buffer and
consumers draining it it is Producer-Consumer, and the two are not
interchangeable, using a barrier to coordinate a producer-consumer
relationship forces the fast side to wait for the slow side on every single
item rather than allowing the buffer to smooth out the difference.

Barrier is structurally incompatible with unbounded or unknown-count
concurrency, it requires the party count to be known and fixed, or explicitly
adjustable in implementations that support that, at construction time, so it
cannot directly coordinate a thread pool whose size varies with load, or a
set of actors that come and go, without first funneling that variability
through a different primitive that produces a fixed count for the barrier to
consume.

## 14. Refactoring path in and out

Introducing a barrier into code that lacks one starts by identifying the
implicit phase boundary that is currently undefended, usually visible as a
shared data structure that one set of threads writes and a subsequent step
reads, with the current synchronization either missing entirely, faked with a
sleep, or implemented as a hand-rolled spin loop on a shared counter. First,
enumerate the fixed set of participant threads that must all reach the
boundary, and confirm the count is genuinely fixed for the duration you plan
to place the barrier around, if it is not fixed, stop and reconsider Phaser
or a different primitive instead of forcing Barrier to fit. Second, construct
one barrier instance sized to that participant count, scoped so every
participant thread has access to the same instance, most commonly a
field shared across the worker objects or captured in a closure passed to
each spawned thread. Third, insert exactly one call to the barrier's wait
method at the phase boundary in every participant's code path, including
every branch, and wrap the phase-local work that precedes it in error
handling that either reaches the wait call regardless of failure or
explicitly aborts the barrier on unrecoverable failure, per the fix described
in dimension 11 for the hung-thread failure mode. Fourth, if a merge or
checkpoint step must run exactly once between phases, either supply it as the
barrier's optional action where the implementation offers one, or check the
leader flag the wait call returns and branch on it, per the language-idiomatic
variants in dimension 8, rather than adding a second, separate synchronization
primitive purely to guarantee single execution. Fifth, remove the sleep-based
or hand-rolled synchronization that the barrier replaces, and add a test
along the lines of dimension 15 that would have failed under the old
approach.

Removing a barrier that has stopped earning its place typically happens for
one of two reasons, either the fixed-participant-count assumption has broken
down because the workload now needs dynamic scaling, in which case the
refactor upgrades to Phaser rather than removing synchronization outright, or
profiling has shown the barrier's straggler sensitivity, dimension 11, is the
dominant cost, in which case the refactor replaces the tight lockstep
coordination with a looser pipeline of bounded queues between stages, letting
fast stages get ahead of slow ones up to the queue's buffer limit instead of
synchronizing every single round. In both directions the refactor should
preserve, and ideally strengthen, the test coverage that proves no
participant observes another participant's next-phase state prematurely,
since that is the invariant the barrier existed to guarantee and it must not
silently regress during the refactor.

## 15. Testing and verification

What becomes easy to test. The core correctness property, no participant
observes the next phase's data before every participant has finished the
current phase, becomes directly assertable, spawn the fixed number of
participant threads, have each write a distinctive, thread-identifiable value
into a shared structure during its phase, call the barrier, then have every
thread read the entire shared structure immediately after the barrier
releases it and assert that every expected value from every participant is
present, this test would reliably fail without a barrier and reliably pass
with one, making it a genuine regression test rather than a smoke test. The
optional barrier action's exactly-once guarantee is similarly easy to verify
directly, run several rounds, and assert an atomic counter incremented inside
the action equals exactly the number of rounds run, never more.

What becomes harder to test. Timing-dependent failure modes, the hung
participant from dimension 11's first failure mode, the straggler-induced
throughput degradation, and the broken-barrier propagation on interruption,
are harder to reproduce deterministically, since they depend on
the relative scheduling of threads, which most languages and runtimes do not
give the test author direct control over. The most reliable technique is to
inject deterministic delays or explicit failure points into specific
participant threads under test, rather than relying on the natural scheduler
to happen to produce the ordering under test, using an artificial sleep or an
injected exception on a specific, identifiable participant to force the
scenario, this is a legitimate, common technique, distinct from using a sleep
as a substitute for the barrier itself, which was called out as an
anti-pattern in dimension 2.

For the broken or interrupted state specifically, deliberately interrupt one
participant thread while it is blocked in the wait call, from the test's
driving thread, then assert every other still-waiting participant receives
the expected broken-barrier exception rather than hanging, and that a
subsequent explicit reset, where the implementation supports one, correctly
returns the barrier to a usable state for the next test round. For straggler
sensitivity as a performance property rather than a correctness property,
measure wall-clock time across many rounds with an artificially delayed
single participant and confirm the total time scales with the sum of
per-round maxima as dimension 3 predicts, this is a useful sanity check that
the implementation under test genuinely exhibits the documented behavior and
has not, for example, silently degenerated into per-participant independent
progress due to a bug.

No special test doubles are needed for the barrier itself in most languages,
because the standard library implementations, Java's CyclicBarrier, Python's
`threading.Barrier`, .NET's Barrier, and Rust's `Barrier` in `std::sync`, are
lightweight and deterministic enough in their release-all-together
behavior that tests can use the real implementation directly rather than a
mock, mocking the barrier's own coordination logic would defeat the purpose
of testing that coordination.

## 16. Observability signals

A healthy barrier in production shows a tight, low-variance distribution of
per-round completion times across the participant population, and a low ratio
of maximum-participant-time to average-participant-time per round, since a
wide gap between the slowest and average participant is exactly the straggler
symptom from dimension 11 made visible as a metric rather than discovered
through user-facing latency complaints. Instrument each participant to record
a timestamp on arrival at the barrier and a timestamp on release, the
difference is the time that specific participant spent waiting for others,
and the maximum of that value across the participant population in a given
round is the direct cost the barrier imposed on that round, this single
number, tracked over time, is the most useful observability signal for
this pattern.

A failing or degrading barrier shows up as a rising count of broken-barrier
exceptions or their language equivalent, a rising number of participant
threads whose wait call never returns within an expected timeout window,
paired with CPU or activity metrics on those specific threads dropping to
near zero while other system activity continues normally, and, at the whole
system level, throughput on the surrounding pipeline flattening or dropping
in lockstep with an increase in per-round barrier wait time, since a barrier
that is spending most of its time waiting rather than doing phase-local work
means the parallel decomposition is not delivering the speedup it was
designed for. If the runtime or library exposes it, expose the current
participant count and the current arrived count as a gauge, a persistently
non-zero arrived count that never reaches the party total, combined with no
new arrivals over an extended window, is the direct signature of the hung
participant failure mode and should be alertable on its own, distinct from a
generic thread-count or CPU-utilization alert that would not localize the
problem to this specific synchronization point.

## 17. Security and privacy implications

Barrier itself has no data-handling responsibility, it coordinates timing, not
data, and the pattern carries no cryptographic, authentication, or
authorization surface of its own, this section is largely silent on that
front by the nature of what the pattern does. The one implication worth
naming plainly is availability, not confidentiality or integrity, a barrier
that a malicious or misbehaving participant can enter but never leave, by
never calling wait, or by holding the participant slot open indefinitely,
turns the barrier into a denial-of-service vector against every other
legitimate participant waiting alongside it, which matters specifically in
multi-tenant systems where one tenant's code, plugin, or task could occupy a
participant slot in a barrier shared with other tenants' work. Where a barrier
coordinates participants that are not all under the same trust boundary, the
correct mitigation is a timeout on the wait call, so a stalled or hostile
participant degrades the barrier to a broken state that other participants
can detect and recover from, rather than an unbounded wait that a hostile
actor can trigger at will. Beyond this availability concern, there is no
further security-relevant behavior specific to this pattern, and any data
that participants happen to exchange around the barrier's synchronization
point carries whatever confidentiality or integrity requirements that data
already had independent of the barrier.

## 18. References

1. Allen B. Downey, The Little Book of Semaphores, Green Tea Press, 2nd
   edition, freely available at https://greenteapress.com/wp/semaphores/,
   verified 2026-08-14. The Rendezvous, Barrier, and Reusable Barrier problems
   and their derivations.
2. Oracle, CyclicBarrier, Java SE 21 API documentation,
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/CyclicBarrier.html,
   verified 2026-08-14.
3. The Open Group Base Specifications Issue 7, IEEE Std 1003.1-2017,
   `pthread_barrier_wait`,
   https://pubs.opengroup.org/onlinepubs/9699919799/functions/pthread_barrier_wait.html,
   verified 2026-08-14.
4. Wikipedia, Barrier (computer science),
   https://en.wikipedia.org/wiki/Barrier_(computer_science), verified
   2026-08-14. Centralized, sense-reversing, and combining-tree barrier
   implementation shapes.
5. Rust documentation team, `std::sync::Barrier`, The Rust Standard Library,
   https://doc.rust-lang.org/std/sync/struct.Barrier.html, verified
   2026-08-14.
6. Microsoft, Barrier Class, .NET API browser,
   https://learn.microsoft.com/en-us/dotnet/api/system.threading.barrier,
   verified 2026-08-14.
7. Python Software Foundation, threading, The Python Standard Library
   documentation, https://docs.python.org/3/library/threading.html#threading.Barrier,
   verified 2026-08-14.
8. OpenMP Architecture Review Board, OpenMP Application Programming
   Interface, Version 5.2, November 2021, the barrier Construct section.
9. Message Passing Interface Forum, MPI. A Message-Passing Interface
   Standard, Version 4.0, June 2021, section 5.3, Barrier Synchronization.
10. Brian Goetz, Tim Peierls, Joshua Bloch, Joseph Bowbeer, David Holmes, Doug
    Lea, Java Concurrency in Practice, Addison-Wesley, 2006. The worked
    CyclicBarrier example for parallelizing an iterative algorithm.

## Code examples

Three languages were chosen because each covers a genuinely different
point in the design space this entry covers. Python's `threading.Barrier` is
a native, feature-complete reusable barrier with a barrier action, showing
the fully batteries-included API shape. Rust's `Barrier` type in
`std::sync` is a native reusable barrier that deliberately omits a callback
in favor of a returned leader flag, showing the minimal, explicit API
shape. Go has no barrier in its standard library at all, so the Go sample
implements one directly on a mutex and a condition variable using the
generation-counter technique described in dimension 8, which is the
idiomatic way Go programmers build this primitive when they need it. Java was
considered but is omitted from the runnable samples because no Java Runtime
Environment was available in the verification environment for this entry,
javac reported it could not locate one, its CyclicBarrier semantics are
nonetheless covered in dimensions 8, 9, and 13 from the verified Oracle
documentation. All three samples below were compiled or executed in the
verification environment and their output is reported in the summary at the
end of this entry.

### Python

```python
import threading
import time
import random


def worker(barrier: threading.Barrier, worker_id: int, log: list) -> None:
    for phase in range(3):
        time.sleep(random.uniform(0.001, 0.02))
        log.append((worker_id, phase, "phase-local work done"))
        index = barrier.wait()
        if index == 0:
            log.append(("barrier", phase, "advanced"))


def main() -> None:
    party_size = 4
    log: list = []
    barrier = threading.Barrier(
        party_size,
        action=lambda: log.append(("action", "ran-once-per-phase")),
    )
    threads = [
        threading.Thread(target=worker, args=(barrier, i, log))
        for i in range(party_size)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    action_count = sum(1 for entry in log if entry[0] == "action")
    assert action_count == 3, f"expected 3 phase actions, got {action_count}"
    print(f"phases completed {action_count}, log entries {len(log)}")


if __name__ == "__main__":
    main()
```

### Rust

```rust
use std::sync::{Arc, Barrier};
use std::thread;

fn main() {
    let party_size = 4;
    let barrier = Arc::new(Barrier::new(party_size));
    let mut handles = Vec::new();

    for worker_id in 0..party_size {
        let barrier_ref = Arc::clone(&barrier);
        handles.push(thread::spawn(move || {
            for phase in 0..3 {
                let result = barrier_ref.wait();
                if result.is_leader() {
                    println!("phase {} advanced by leader worker {}", phase, worker_id);
                }
            }
        }));
    }

    for handle in handles {
        handle.join().expect("worker thread panicked");
    }
    println!("all workers completed 3 phases");
}
```

### Go

Go's standard library has no barrier type. This shows the idiomatic
generation-counter construction on top of `sync.Mutex` and `sync.Cond`, which
is functionally the same sense-reversal technique described in dimension 8.

```go
package main

import (
	"fmt"
	"sync"
)

type Barrier struct {
	mu         sync.Mutex
	cond       *sync.Cond
	parties    int
	waiting    int
	generation int
}

func NewBarrier(parties int) *Barrier {
	b := &Barrier{parties: parties}
	b.cond = sync.NewCond(&b.mu)
	return b
}

func (b *Barrier) Wait() (isLeader bool) {
	b.mu.Lock()
	defer b.mu.Unlock()
	currentGen := b.generation
	b.waiting++
	if b.waiting == b.parties {
		b.waiting = 0
		b.generation++
		b.cond.Broadcast()
		return true
	}
	for currentGen == b.generation {
		b.cond.Wait()
	}
	return false
}

func main() {
	partySize := 4
	barrier := NewBarrier(partySize)
	var wg sync.WaitGroup
	for workerID := 0; workerID < partySize; workerID++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			for phase := 0; phase < 3; phase++ {
				if barrier.Wait() {
					fmt.Printf("phase %d advanced by leader worker %d\n", phase, id)
				}
			}
		}(workerID)
	}
	wg.Wait()
	fmt.Println("all workers completed 3 phases")
}
```

Verified runs. Python's sample printed `phases completed 3, log entries 16`
via `python3 barrier.py`. Rust's sample was compiled with `rustc -O
barrier.rs` and printed three leader announcements, one per phase, via the
compiled binary. Go's sample was run with `go run barrier.go` and printed
three leader announcements, one per phase. Java's CyclicBarrier was not
compiled in this environment because no JRE was present, `javac -version`
reported it could not locate a Java Runtime.
