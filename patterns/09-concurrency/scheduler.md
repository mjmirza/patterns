---
name: Scheduler
slug: scheduler
family: 09-concurrency
category: Concurrency
aliases: [Task Scheduler, Cooperative Scheduler, Runnable Queue]
first_described: "Schmidt, Stal, Rohnert, Buschmann 2000"
maturity: canonical
related: [thread-pool, work-queue, future-promise, active-object, reactor, producer-consumer]
incompatible_with: []
verified: 2026-08-02
---

# Scheduler

## 1. Name, aliases, and lineage

The canonical name is Scheduler. As a distinct architectural concern separate
from any one mechanism, it is discussed in Douglas C. Schmidt, Michael Stal,
Hans Rohnert and Frank Buschmann, *Pattern-Oriented Software Architecture,
Volume 2. Patterns for Concurrent and Networked Objects*, Wiley, 2000, where
the Half-Sync/Half-Async and Leader/Followers chapters both name a scheduling
component responsible for deciding which unit of work runs next and on which
execution resource. The word predates that book by decades as the name of the
kernel subsystem that multiplexes processes onto a CPU, and the pattern entry
here covers both the operating-system sense and the application-level sense,
because the same structural problem repeats at every layer of a system.

**Task Scheduler** is the common name in application and job-processing
contexts, used by Quartz Scheduler, a Java scheduling library whose own quick
start guide describes a `Scheduler` object that manages `Job` and `Trigger`
objects and controls when each job runs
([Quartz Scheduler, Quick Start Guide, Quartz 2.3.0](https://www.quartz-scheduler.org/documentation/quartz-2.3.0/quick-start.html),
verified 2026-08-02). **Cooperative Scheduler** names the specific variant
where the scheduled units of work run to completion or to an explicit yield
point rather than being preempted, the shape used by Go's goroutine scheduler
and by Python's `asyncio` event loop. **Runnable Queue** names the internal
data structure a scheduler almost always contains, a queue or priority queue
of units of work that can run immediately, distinct from units that are
waiting on I/O or on a timer.

Three things get called a scheduler and confusing them is the source of most
misapplied advice about this pattern.

- **A CPU or OS-thread scheduler.** Decides which OS thread the kernel runs
  next on a physical core. The Linux Completely Fair Scheduler is the default
  example, and application code almost never implements this variant, it only
  lives underneath every other variant.
- **A cooperative or green-thread scheduler.** Decides which lightweight,
  user-space unit of work, a goroutine, a coroutine, an actor, a fiber, runs
  next on a small pool of OS threads. The Go runtime's GMP scheduler is the
  canonical modern example, described in the runtime's own source comments as
  distributing runnable goroutines over worker threads
  ([Go source, runtime/proc.go, top-of-file scheduler comment](https://go.dev/src/runtime/proc.go),
  verified 2026-08-02, quoting "The scheduler's job is to distribute
  ready-to-run goroutines over worker threads").
- **A time-based or job scheduler.** Decides not which unit of work to run
  next among many that can already run, but WHEN a unit of work becomes
  eligible in the first place, based on a delay, a fixed rate, a cron
  expression, or a dependency graph. `java.util.concurrent.ScheduledExecutorService`
  is the canonical library-level example, and Kubernetes's kube-scheduler and
  Apache Airflow are canonical distributed-system examples.

This entry treats the pattern at the structural level shared by all three,
the separation of deciding what runs next from the code that does the
running, and calls out where the three variants diverge.

## 2. Problem and context

A system has more units of work that want to run than it has execution
resources to run them on, or those units of work become eligible at different
and unpredictable times, and something has to decide, repeatedly, which one
runs next, on which resource, and when.

The naive shape without a scheduler is code that starts a unit of work the
instant it is created, either by spawning an OS thread per unit, by calling
directly into the next step of a pipeline, or by running everything on a
single caller's stack. This works until the number of units of work exceeds
the number of resources by any real margin. Spawning one OS thread per
incoming request degrades under load because thread creation, context
switching, and stack memory all cost real resources, and the operating
system's own scheduler starts thrashing between thousands of runnable
threads. Running everything synchronously on one stack means a single slow
unit of work blocks every other unit behind it, because there is no
structure that lets a second unit take the resource while the first is
waiting.

The context that produces a Scheduler is any of the following, usually more
than one at once.

- Units of work arrive faster, or in greater number, than can each get a
  dedicated execution resource.
- Units of work have different priorities, deadlines, or fairness
  requirements, so first-come-first-served is the wrong policy.
- Units of work need to run at a specific future time, or repeatedly on an
  interval, rather than immediately.
- The execution resource itself is scarce, expensive, or externally limited,
  a fixed pool of OS threads, a fixed CPU core count, a downstream service's
  rate limit, or a fixed number of nodes in a cluster.

A Scheduler is the component that owns the policy for these decisions,
separated from the components that either produce units of work or execute
them. This is the same separation of concerns that a Thread Pool's internal
work queue performs at a smaller scope, and a Scheduler is frequently the
component that sits on top of one or more Thread Pools, deciding what gets
submitted to them and when, rather than replacing them.

## 3. Forces

- **Fairness versus throughput.** Favoured toward whichever the policy
  chooses, and this is the central design decision of any scheduler, not a
  side effect. Strict priority pushes throughput up for high-priority work at
  the cost of possible starvation for low-priority work. Round-robin and
  fair-share policies favour fairness at the cost of some throughput, because
  a scheduler that always services the highest-value work first will, on
  average, complete more valuable work per unit time than one that spreads
  attention evenly.
- **Latency versus resource efficiency.** A scheduler that keeps resources
  fully saturated, running the next unit the instant one finishes, cuts
  idle capacity but can make an individual unit of work wait behind a long
  queue. A scheduler that reserves headroom, or preempts long-running work
  for short work, lowers tail latency for the short work at the cost of total
  throughput.
- **Determinism versus adaptivity.** A fixed-rate or cron-style schedule is
  fully predictable, a person can read the schedule and know exactly when a
  task will run, which matters for compliance and debugging. A load-adaptive
  or priority-adaptive scheduler reacts to the actual state of the system,
  which improves real-world outcomes but makes the exact next execution time
  unpredictable from the schedule definition alone.
- **Preemption versus cooperation.** Sacrificed in cooperative schedulers by
  design, favoured in preemptive ones. A cooperative scheduler is cheaper to
  build correctly and cheaper to run, because it never has to save and
  restore execution state at an arbitrary point, but a single unit of work
  that never yields can starve every other unit forever. A preemptive
  scheduler removes that failure mode at the cost of the machinery needed to
  interrupt work safely at an arbitrary point.
- **Coupling.** Favoured toward decoupling producers of work from consumers
  of work. The scheduler is the only component that needs to know both the
  full set of pending work and the full set of available resources, producers
  submit work without knowing which resource will run it, and executors run
  work without knowing where it came from.
- **Operability.** Mixed. A scheduler concentrates scheduling decisions into
  one component, which makes the system easier to reason about and easier to
  observe from a single place, dimension 16 covers this directly. It also
  concentrates risk into that one component. A scheduler bug or a scheduler
  outage can silently stop all scheduled work at once, in a way that a
  system without a central scheduler cannot fail all at once.

A scheduler that claims to raise fairness, throughput, and low tail
latency at the same time with no policy trade-off is describing an aspiration,
not a real scheduler. Every scheduler in production practice makes at least
one of the choices above explicit and pays the corresponding cost.

## 4. Applicability and non-applicability

Reach for a Scheduler when the following hold.

- There are more units of work eligible to run, at some point in the
  system's life, than there are execution resources to run them
  concurrently, so an ordering decision is unavoidable.
- Units of work need to run at a specific time, after a delay, or on a
  repeating interval, and that timing has to be honoured even while other
  work is running.
- Different units of work carry different priority, deadline, or fairness
  requirements that a plain queue cannot express.
- The system needs a single place to observe, throttle, cancel, or reprioritize
  pending work, rather than that logic being scattered across every producer.
- The execution resource is genuinely scarce or externally rate-limited, and
  wasting it on a low-value unit of work while a high-value one waits is a
  real cost.

Do NOT reach for a Scheduler in these situations.

- The number of units of work is small and bounded, and the language runtime
  or platform already schedules them adequately. Spawning three OS threads
  for three genuinely independent, short-lived tasks does not need a
  scheduler in front of it, the OS scheduler already does the job.
- There is exactly one unit of work at a time, submitted synchronously and
  waited on before the next arrives. A scheduler adds a decision point with
  nothing to decide, and the correct pattern is a plain function call or, at
  most, a Future/Promise for the single asynchronous result, see the
  Future/Promise entry.
- The timing requirement is "as soon as possible with no ordering policy",
  and a single unbounded queue with one or more consumers already satisfies
  it. Adding a scheduler on top of a Work Queue that has no competing
  priorities or delays is unneeded layering, a plain Producer-Consumer queue
  is the correct fit.
- The system cannot tolerate a scheduling policy at all, because every unit
  of work has an identical, non-negotiable, immediate deadline. In that case
  the actual requirement is enough dedicated resources for worst-case
  concurrent demand, not smarter scheduling among too few resources, and no
  scheduling policy fixes a genuine resource shortfall.
- Correctness requires strict, verifiable real-time guarantees, a hard
  real-time system where a missed deadline is a safety failure. General
  purpose schedulers, including every implementation shown in this entry, are
  built for average-case throughput and soft deadlines, not hard real-time
  guarantees, and using one where a certified real-time operating system
  scheduler is required is a category error, not a scheduling policy choice.

## 5. Structure

- **Task, or Job, or Runnable.** The unit of work. Carries whatever the
  scheduler's ordering policy needs to see, most commonly a priority value, a
  ready time, a deadline, or a repeat interval, plus the actual work to run,
  usually a closure or a callback.
- **Scheduler.** Owns the ordering policy and the collection of pending
  tasks. Exposes a way to submit a task and, internally, a way to select the
  next task that should run. The scheduler does not itself execute the task's
  work in most designs, it hands the task to an executor.
- **Executor, or Worker, or Runner.** Actually runs a task's work once the
  scheduler has selected it. Frequently a Thread Pool, an OS thread, an event
  loop iteration, or, in a distributed job scheduler, a whole worker node.
  This is the seam where Scheduler composes with Thread Pool, dimension 13
  covers this composition.
- **Ready set, or run queue, or wait heap.** The internal data structure
  holding tasks eligible to run right now, ordered by the policy. This is
  usually a priority queue keyed by priority or by next-run time, a plain
  FIFO queue for round-robin policies, or several per-priority FIFO queues
  for multilevel policies.
- **Clock, or time source.** Provides the current time, and in a time-based
  scheduler, is the thing the scheduler compares each task's ready time
  against. Injecting the clock, rather than reading a global wall clock
  directly, is what makes the pattern testable without real waiting, see
  dimension 15.
- **Policy.** Not always a separate object, but always a separable concern,
  the function that decides ordering among tasks in the ready set. Making
  this a swappable strategy, rather than baking the ordering rule into the
  scheduler's core loop, is what lets a system change from priority-based to
  fair-share scheduling without rewriting the scheduler.

## 6. ASCII structure diagram

```
                +-------------------+
   submit(task) |    Scheduler      |
  producers --->|-------------------|
                |  ready set /      |
                |  wait heap        |
                |  (ordered by      |
                |   Policy)         |
                +---------+---------+
                          |
                    select next
                    task eligible
                    to run
                          |
                          v
                +---------+---------+
                |     Executor      |
                |  (Thread Pool,    |
                |   worker node,    |
                |   event loop)     |
                +---------+---------+
                          |
                     runs task.work()
                          |
                          v
                +---------+---------+
                |       Clock       |<---- Scheduler reads
                +--------------------+     current time to
                                            decide readiness
```

## 7. Dynamics

The core loop shared by every variant of this pattern, shown as a repeating
sequence.

```
Producer                Scheduler                    Executor
   |                        |                            |
   |-- submit(task) ------->|                             |
   |                        | insert into ready set,      |
   |                        | ordered by Policy            |
   |                        |                             |
   |                        | loop                          |
   |                        |   t = clock.now()            |
   |                        |   if ready_set has a task    |
   |                        |      whose ready_time <= t   |
   |                        |     pop highest-priority     |
   |                        |     eligible task              |
   |                        |------- dispatch(task) ------>|
   |                        |                             | run task.work()
   |                        |                             |
   |                        |<--- on complete, if the -----|
   |                        |     task repeats, reinsert   |
   |                        |     it with next ready_time  |
   |                        |                             |
   |                        |   else sleep until the       |
   |                        |   earliest ready_time in     |
   |                        |   the ready set, or until     |
   |                        |   a new submit() wakes it     |
```

Three points in this sequence separate the variants covered in dimension 1.

- A pure priority scheduler skips the ready-time check entirely, every
  submitted task is immediately eligible, and the loop only ever compares
  priority.
- A cooperative green-thread scheduler like Go's replaces "run task.work()"
  with "resume the goroutine until it yields, blocks, or returns", and the
  yield point is where control returns to the scheduler loop, rather than the
  scheduler waiting for full completion.
- A distributed job scheduler like Kubernetes's kube-scheduler replaces a
  single Executor with a pool of candidate nodes and inserts a two-phase
  filtering and scoring decision between "pop the next task" and "dispatch",
  described in the Kubernetes documentation as first finding the set of
  nodes where it is feasible to schedule the pod, then ranking the surviving
  nodes and assigning the pod to the node with the highest ranking
  ([Kubernetes documentation, "kube-scheduler"](https://kubernetes.io/docs/concepts/scheduling-eviction/kube-scheduler/),
  verified 2026-08-02, quoting "kube-scheduler selects a node for the pod in
  a 2-step operation" for the two named phases, filtering and scoring, and
  "kube-scheduler assigns the Pod to the Node with the highest ranking" for
  the final step).

## 8. Implementation variants

- **Priority queue scheduler.** The ready set is a binary heap keyed by
  priority. `select next` is a heap-pop, `submit` is a heap-insert, both
  logarithmic in the number of pending tasks. This is the shape most
  in-process, single-node schedulers use, including the code samples in this
  entry.
- **Time-wheel scheduler.** Instead of a heap keyed by absolute time, tasks
  are bucketed into a circular array of time slots, and a single pointer
  advances one slot per tick, running every task in the current slot. This
  trades heap logarithmic insert and remove cost for constant-time insert and
  remove at the cost of coarser timing resolution and bounded maximum delay
  per wheel size, and is the shape used by network timer subsystems handling
  very high volumes of short timeouts, such as connection timeout tracking in
  high-throughput servers.
- **Multilevel feedback queue.** Several separate FIFO queues, one per
  priority level, where a task that uses its full time slice without
  finishing is demoted to a lower-priority queue and a task that yields early
  is promoted or kept at its current level. This is the shape most general
  purpose OS process schedulers historically used before completely fair
  scheduling, because it approximates shortest-job-first without knowing job
  length in advance.
- **Cooperative work-stealing scheduler.** Each execution resource, an OS
  thread in Go's case, owns a local ready queue, and an idle resource steals
  work from another resource's queue rather than all resources contending on
  one shared queue. Go's GMP model uses this shape, where P, processor,
  objects each carry a local run queue of goroutines and an idle M, worker
  thread, steals from another P's queue when its own is empty, reducing
  contention on any single shared structure
  ([Go source, runtime/proc.go, scheduler design comment](https://go.dev/src/runtime/proc.go),
  verified 2026-08-02).
- **Cron-style declarative scheduler.** Tasks are not submitted imperatively
  at the moment they should run, they are registered once with a schedule
  expression, and the scheduler itself computes each next run time from the
  expression and the clock. `java.util.concurrent.ScheduledExecutorService`
  offers a narrower version of this with `scheduleAtFixedRate` and
  `scheduleWithFixedDelay`, described in its own documentation as submitting
  a periodic action that runs first after an initial delay and then either at
  a fixed rate from the start of each execution or after a fixed delay from
  the end of each execution
  ([Oracle, Java SE 21 API documentation, ScheduledExecutorService](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ScheduledExecutorService.html),
  verified 2026-08-02, quoting "Submits a periodic action that becomes
  enabled first after the given initial delay, and subsequently with the
  given period" for the fixed-rate variant, and "subsequently with the given
  delay between the termination of one execution and the commencement of the
  next" for the fixed-delay variant). Quartz Scheduler extends this to full
  cron expressions and persistent, clustered job storage.
- **Cooperative single-threaded event loop.** The scheduler and the executor
  collapse into the same loop on a single thread. Node.js's event loop and
  Python's `asyncio` event loop both work this way, where the ready set is
  the callback queue, the clock check handles timers, and there is never more
  than one task running at once, so no locking is needed inside a single
  task's own code, only around anything the loop itself shares with other
  threads.

## 9. Known production uses

- **Kubernetes kube-scheduler.** The default Kubernetes cluster component
  that assigns each newly created pod to a node, using the two-phase
  filtering and scoring process described in dimension 7
  ([Kubernetes documentation, "kube-scheduler"](https://kubernetes.io/docs/concepts/scheduling-eviction/kube-scheduler/),
  verified 2026-08-02).
- **The Go runtime's GMP scheduler.** Every Go program's goroutines are
  scheduled by this component, described directly in the runtime source as
  distributing runnable goroutines over worker threads, with a design
  document referenced from the same source comment
  ([Go source, runtime/proc.go](https://go.dev/src/runtime/proc.go), verified
  2026-08-02).
- **`java.util.concurrent.ScheduledExecutorService`**, and its standard
  implementation `ScheduledThreadPoolExecutor`, part of the Java Class
  Library since Java 5, used throughout Java server and enterprise
  applications for delayed and periodic task execution
  ([Oracle, Java SE 21 API documentation, ScheduledExecutorService](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ScheduledExecutorService.html),
  verified 2026-08-02).
- **Quartz Scheduler.** An open source Java scheduling library, in
  production use across enterprise Java applications for cron-style and
  calendar-based job scheduling since its early releases, exposing
  `Scheduler`, `Job`, and `Trigger` as its core abstractions
  ([Quartz Scheduler, Quick Start Guide](https://www.quartz-scheduler.org/documentation/quartz-2.3.0/quick-start.html),
  verified 2026-08-02).
- **The Linux Completely Fair Scheduler.** The default CPU process scheduler
  in the Linux kernel since kernel version 2.6.23, which orders runnable
  tasks by a virtual runtime value rather than fixed time slices, documented
  in the kernel's own scheduler design documentation as aiming to model an
  "ideal, precise multi-tasking CPU" that runs every runnable task
  simultaneously at an equal, fair share of CPU power
  ([The Linux Kernel documentation, "CFS Scheduler"](https://www.kernel.org/doc/html/latest/scheduler/sched-design-CFS.html),
  verified 2026-08-02).

## 10. Consequences

Positive.

- Producers of work are fully decoupled from the policy that decides
  execution order, so priority, fairness, or timing policy can change without
  touching any producer.
- A single place exists to observe, throttle, cancel, or reprioritize
  pending work, which is a real operability win over scattered ad hoc timers
  and thread spawns.
- Resource usage becomes bounded and predictable, because the scheduler
  controls how many units of work are active at once rather than every
  producer independently deciding to start work immediately.
- Time-based variants make delayed and repeating work a first-class,
  testable concept rather than a scattered collection of `sleep` calls.

Negative.

- The scheduler becomes a single point of concentrated risk. A bug in the
  ordering policy, or an outage of the scheduler component itself, can
  silently stop all scheduled work at once, a failure mode a system without a
  central scheduler by its own design cannot have in the same form.
- Debugging becomes harder in the cooperative and multi-resource variants,
  because "why did this task run at this time, on this resource" now depends
  on the scheduler's internal state at that moment rather than being visible
  at the call site, the same cost the Thread Pool entry names for pooled
  execution, compounded by the added timing dimension.
- A poorly chosen policy actively harms the system it was meant to help.
  Strict priority scheduling can starve low-priority work indefinitely, and a
  cooperative scheduler is defenseless against a single task that never
  yields, dimension 11 covers both in detail.
- Every scheduler variant adds real implementation and maintenance cost, a
  priority queue, a clock abstraction, and a dispatch loop, none of which is
  free, and dimension 4 exists precisely because this cost is not always
  worth paying.

## 11. Failure modes and misuse

**Symptom.** Low-priority tasks never run, even though the system is not
overloaded on average. **Cause.** A strict priority policy with an unbounded
or high-volume stream of high-priority work, so the ready set always has a
higher-priority task available whenever the executor is free, and the
scheduler's policy has no starvation prevention such as priority aging.
**Fix.** Add priority aging, where a task's effective priority increases the
longer it waits, or switch to a weighted fair-share policy that guarantees
every priority level a minimum share of execution time.

**Symptom.** A single scheduled task hangs the entire system, and no other
scheduled work runs while it is stuck. **Cause.** A cooperative scheduler
running a task that never yields, blocks on a call the scheduler's runtime
does not know how to reschedule around, such as a blocking system call made
directly instead of through the runtime's async I/O, or an infinite loop with
no cooperative yield point. **Fix.** Route every blocking operation through
the scheduler's own non-blocking primitives, and where a genuinely blocking
call is unavoidable, dispatch it to a separate dedicated thread pool rather
than running it inside the cooperative scheduler's own worker, which is
exactly why Go's runtime detaches an M from its P during a blocking syscall
rather than letting the syscall block the whole processor.

**Symptom.** Scheduled tasks silently stop firing at all after the process
has been running for a long time, with no crash or error logged. **Cause.**
The scheduler's clock or timer wheel has an integer overflow or a fixed
maximum delay, and a task scheduled far enough in the future silently wraps
or is dropped, a documented historical class of bug in timer wheel
implementations with a fixed number of slots and a naive overflow bucket.
**Fix.** Use a scheduler library with a documented and tested maximum delay,
and add an explicit assertion or rejection path for any submitted delay that
exceeds it, rather than allowing silent wraparound.

**Symptom.** The same repeating task appears to run twice for one scheduled
occurrence, or drifts later and later over time. **Cause.** Confusing
`scheduleAtFixedRate` semantics, which anchors successive runs to the
original start time and can fire back-to-back to catch up after a delay,
with `scheduleWithFixedDelay` semantics, which anchors the next run to the
end of the previous one and never catches up, or the reverse confusion.
**Fix.** Pick the semantics deliberately, catch-up bursts are correct and
desired for some periodic maintenance tasks and actively harmful for others,
and name the choice explicitly in code rather than accepting whichever the
library defaults to.

**Symptom.** Under load, submitting new work makes the system slower in a way
that is disproportionate to the amount of new work submitted. **Cause.** The
scheduler's ready set is a single shared, lock-protected data structure, and
every submit and every dispatch contends on that one lock, so contention
grows faster than the actual work does. **Fix.** Shard the ready set, either
per priority level or per execution resource with work stealing between
shards, which is precisely the structural choice Go's GMP scheduler makes
with per-P local run queues rather than one global run queue.

## 12. Trade-off matrix

Comparing Scheduler against its two nearest named alternatives, Thread Pool
alone with no separate scheduling policy, and a plain Producer-Consumer
queue with no timing or priority concept.

| Force | Scheduler | Thread Pool alone | Producer-Consumer queue |
|---|---|---|---|
| Ordering policy | Explicit and swappable, priority, fairness, or time based | Implicit, whatever order the pool's internal queue happens to use, usually FIFO | None, pure FIFO with no priority concept |
| Time-based execution | First-class, delayed and repeating tasks are native | Not supported without adding a timer on top | Not supported |
| Coupling to execution resource | Low, scheduler can target any executor, a pool, a single thread, or a remote node | N/A, the pool is both the queue and the executor combined | N/A, consumers pull directly |
| Implementation cost | Highest, needs a clock abstraction, an ordered ready set, and a dispatch loop | Lower, a bounded queue plus a fixed set of worker threads | Lowest, a single shared queue |
| Best fit | Competing priorities, deadlines, or scheduled timing across shared resources | Uniform, immediately-runnable work with no ordering requirement | Uniform, immediately-runnable work, simplest possible case |

## 13. Related and incompatible patterns

- **Thread Pool.** A Scheduler very frequently sits directly on top of one or
  more thread pools, using the pool as its Executor. The two compose rather
  than compete, a scheduler decides what runs next, a thread pool decides
  where it physically executes and bounds how many run at once. Reaching for
  a Scheduler without an underlying pool or resource abstraction is unusual
  outside a single-threaded event loop.
- **Work Queue.** The ready set inside a Scheduler is a specialised Work
  Queue, ordered by policy instead of plain FIFO. A system that only needs
  FIFO ordering with no priority or timing concept should use a plain Work
  Queue and has no need for the extra machinery a Scheduler adds.
- **Future/Promise.** A Scheduler commonly returns a Future or Promise
  representing the eventual result of a submitted task, letting the caller
  observe completion without blocking on the scheduler's internal timing
  decisions. `ScheduledExecutorService.schedule` returns a
  `ScheduledFuture` for exactly this reason.
- **Reactor and Proactor.** A single-threaded event loop scheduler, the
  cooperative variant described in dimension 8, is frequently built directly
  on top of a Reactor, using the Reactor's readiness notifications to decide
  which registered callback runs next. The Reactor supplies the readiness
  signal, the Scheduler supplies the ordering policy among multiple
  simultaneously ready signals.
- **Active Object.** An Active Object's internal activation queue is a small,
  single-consumer scheduler scoped to one object's own method calls, ordering
  incoming method requests before a dedicated thread serves them one at a
  time. It is the same structural idea as a full Scheduler, narrowed to a
  single object's own method dispatch rather than a system-wide resource.
- **Leader/Followers.** An alternative to a Scheduler-plus-Thread-Pool pair
  for a specific case, event demultiplexing where any one of several worker
  threads can take the leader role directly rather than a separate component
  dispatching to them, trading a simpler structure for a design that is
  harder to extend with rich priority policy.
- **Incompatible with nothing at the structural level**, but a Scheduler and a hard
  real-time scheduling guarantee are in practical tension, dimension 4 covers
  why a general purpose scheduler like every implementation in this entry is
  the wrong tool where certified hard real-time behaviour is the actual
  requirement.

## 14. Refactoring path in and out

Introducing a Scheduler into code that currently starts work immediately, in
place, wherever it is produced.

1. Identify every call site that currently starts a unit of work directly,
   spawning a thread, calling a function synchronously, or setting a raw
   timer. List them, because every one is a future call to `submit`.
2. Extract the unit of work at each call site into an explicit Task value,
   carrying whatever the intended policy needs, most simply the closure to
   run, then a priority or ready time once the policy needs one.
3. Build the Scheduler with the simplest correct policy first, an unordered
   FIFO ready set dispatching to a single existing executor, and verify the
   system behaves identically to before the refactor with no policy change
   yet, this step is pure structural extraction with a behaviour-preserving
   test, see dimension 15.
4. Replace each direct call site from step 1 with a call to
   `scheduler.submit(task)`, one call site at a time, re-running the
   behaviour-preserving test after each.
5. Only once every call site is going through the scheduler, introduce the
   actual policy change that motivated the refactor, priority ordering, a
   time-based ready check, or a fairness rule, as its own separate change
   with its own test, so a regression is attributable to the policy and not
   to the structural extraction.

Removing a Scheduler once it stops earning its place, most commonly because
the system converged to a small, uniform, always-immediately-runnable
workload where dimension 4's non-applicability conditions now hold.

1. Confirm the ready set's ordering policy is, in practice, indistinguishable
   from plain FIFO by observing production dispatch order over a real
   window, not by assumption.
2. Replace the scheduler's `submit` call sites with direct calls to the
   underlying executor, one call site at a time, re-verifying behaviour after
   each, mirroring step 4 above in reverse.
3. Delete the now-unused Scheduler, Task, and Policy types only after every
   call site is migrated and the test suite is green, never before, so a
   missed call site fails loudly rather than silently losing its scheduling
   behaviour.

## 15. Testing and verification

Injecting the Clock as an explicit dependency, rather than reading the
system's real wall clock inside the scheduler, is what makes time-based
scheduling logic testable at all. A test constructs the scheduler with a
fake clock that only advances when the test tells it to, submits tasks with
known ready times, advances the fake clock past each ready time in
controlled steps, and asserts exactly which tasks the scheduler dispatched
at each step, with no real waiting and no timing flakiness. This is the same
technique used across this repository's other time-dependent entries and is
not specific to any one language, only to whether the clock was designed as
an injectable seam.

This pattern makes the ordering policy considerably easier to test than it
would otherwise be. The priority queue and the readiness check are pure
functions of the ready set's state and the clock, so a test can submit tasks,
advance the fake clock, and assert dispatch order against a trivial fake
executor that records what it was handed, with no real thread and no real
sleep anywhere in the test.

What becomes harder to test is the interaction between the scheduler and a
real concurrent executor, where a genuine race condition between `submit`
running on one thread and `select next` running concurrently on another can
only be caught by actual concurrent execution, not by a single-threaded unit
test with a fake clock. Stress testing with many concurrent submitters
against a real thread pool executor, run repeatedly under a race detector
such as Go's `-race` flag or ThreadSanitizer for C and C++, is the correct
technique for this half of the surface, and no amount of fake-clock unit
testing substitutes for it.

## 16. Observability signals

This dimension is largely engineering judgement drawn from operating
scheduler-shaped systems, not a single sourced specification.

- **Queue depth of the ready set**, sampled over time. A steadily growing
  depth under steady submission rate is the earliest and clearest signal
  that dispatch throughput has fallen behind arrival rate, well before any
  task actually misses a deadline.
- **Time in queue per task**, the gap between submission time and dispatch
  time, broken down by priority level if the policy uses one. A widening gap
  at a specific priority level, while overall depth stays flat, points at a
  starvation problem rather than a raw capacity problem.
- **Dispatch rate versus submission rate**, as two separate counters. When
  submission rate exceeds dispatch rate for a sustained window, the system is
  falling behind regardless of what queue depth alone shows at any single
  instant.
- **Task execution duration**, per task type, distinct from time in queue.
  This is what separates "the scheduler is slow" from "the executors are
  slow", a distinction that queue depth alone cannot make.
- **Missed deadline count**, for any variant with an explicit deadline or
  scheduled time, counted as a hard signal separate from time-in-queue
  percentiles, because a percentile can look acceptable while a specific
  high-value task still misses its individual deadline.
- **Executor utilization**, the fraction of time each execution resource
  spends actually running task work versus idle. Low utilization alongside
  growing queue depth points at a dispatch bug, the scheduler is not handing
  off runnable work fast enough, rather than a genuine capacity shortfall.
- A healthy scheduler on a dashboard shows flat or bounded queue depth,
  dispatch rate tracking submission rate closely, and a time-in-queue
  distribution with a stable tail. A failing one shows queue depth climbing
  without bound, a growing gap between submission and dispatch rate, or a
  time-in-queue tail that keeps widening at one priority level while others
  stay flat, the starvation signature.

## 17. Security and privacy implications

A scheduler that accepts externally-influenced priority or timing values is
an unbounded resource consumption vector. If an untrusted caller can set an
arbitrarily high priority, or submit an unbounded number of tasks, they can
starve every other legitimate task, this is the same starvation failure mode
from dimension 11, reachable deliberately rather than accidentally. Any
scheduler exposed, directly or indirectly, to input from outside a trust
boundary must bound the number of pending tasks per submitter, clamp or
authorize the priority range a submitter can request, and reject submissions
once the ready set exceeds a configured maximum rather than growing it
without bound, an unbounded ready set is a memory exhaustion vector on top of
the scheduling-fairness vector.

A scheduler that logs task contents for observability, dimension 16, must
treat task payloads as potentially sensitive data with the same care as any
other logging path, a scheduled task carrying a user's personal data in its
closure or arguments and logged in full on dispatch or failure is a data
exposure through an unexpected surface. A distributed job scheduler that
serializes tasks to persistent storage or across the network to a remote
executor, such as Quartz's persistent job store or Kubernetes's pod
specifications, extends this concern to whatever that storage or transport
layer's own access control and encryption guarantees are, the scheduler
itself is silent on this unless it explicitly declares stronger guarantees.

## 18. References

1. Douglas C. Schmidt, Michael Stal, Hans Rohnert, Frank Buschmann,
   *Pattern-Oriented Software Architecture, Volume 2. Patterns for
   Concurrent and Networked Objects*, Wiley, 2000, Half-Sync/Half-Async and
   Leader/Followers chapters.
2. Kubernetes documentation, "kube-scheduler".
   https://kubernetes.io/docs/concepts/scheduling-eviction/kube-scheduler/,
   verified 2026-08-02.
3. Go source, `runtime/proc.go`, top-of-file scheduler design comment.
   https://go.dev/src/runtime/proc.go, verified 2026-08-02.
4. Oracle, Java SE 21 API documentation,
   `java.util.concurrent.ScheduledExecutorService`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ScheduledExecutorService.html,
   verified 2026-08-02.
5. Quartz Scheduler, Quick Start Guide, version 2.3.0.
   https://www.quartz-scheduler.org/documentation/quartz-2.3.0/quick-start.html,
   verified 2026-08-02.
6. The Linux Kernel documentation, "CFS Scheduler".
   https://www.kernel.org/doc/html/latest/scheduler/sched-design-CFS.html,
   verified 2026-08-02.

## Code examples

Three languages, chosen because a min-heap based priority-and-time scheduler
is idiomatic in each without extra framework scaffolding. TypeScript and
Python both express the ready set with a simple array-backed binary heap.
Go expresses it with the standard library's `container/heap` interface,
which is the idiomatic way to build a priority queue in Go.

### TypeScript

```typescript
interface Task {
  readyAt: number;
  priority: number;
  run: () => void;
}

class Scheduler {
  private heap: Task[] = [];

  submit(task: Task): void {
    this.heap.push(task);
    this.bubbleUp(this.heap.length - 1);
  }

  private less(a: Task, b: Task): boolean {
    if (a.readyAt !== b.readyAt) return a.readyAt < b.readyAt;
    return a.priority > b.priority;
  }

  private bubbleUp(i: number): void {
    while (i > 0) {
      const parent = (i - 1) >> 1;
      if (!this.less(this.heap[i], this.heap[parent])) break;
      [this.heap[i], this.heap[parent]] = [this.heap[parent], this.heap[i]];
      i = parent;
    }
  }

  private bubbleDown(i: number): void {
    const n = this.heap.length;
    while (true) {
      let smallest = i;
      const left = 2 * i + 1;
      const right = 2 * i + 2;
      if (left < n && this.less(this.heap[left], this.heap[smallest])) smallest = left;
      if (right < n && this.less(this.heap[right], this.heap[smallest])) smallest = right;
      if (smallest === i) break;
      [this.heap[i], this.heap[smallest]] = [this.heap[smallest], this.heap[i]];
      i = smallest;
    }
  }

  // Pops and returns the next task if it is eligible to run at now, else null.
  dispatchIfReady(now: number): Task | null {
    if (this.heap.length === 0 || this.heap[0].readyAt > now) return null;
    const top = this.heap[0];
    const last = this.heap.pop()!;
    if (this.heap.length > 0) {
      this.heap[0] = last;
      this.bubbleDown(0);
    }
    return top;
  }

  size(): number {
    return this.heap.length;
  }
}

function demo(): void {
  const sched = new Scheduler();
  const log: string[] = [];
  sched.submit({ readyAt: 0, priority: 1, run: () => log.push("low@0") });
  sched.submit({ readyAt: 0, priority: 5, run: () => log.push("high@0") });
  sched.submit({ readyAt: 10, priority: 3, run: () => log.push("mid@10") });

  for (const now of [0, 5, 10]) {
    let task: Task | null;
    while ((task = sched.dispatchIfReady(now)) !== null) {
      task.run();
    }
  }
  console.log(log.join(", "));
}

demo();
```

### Python

```python
import heapq
import itertools
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass(order=True)
class _Entry:
    ready_at: float
    priority: int
    seq: int
    run: Callable[[], None] = field(compare=False)


class Scheduler:
    def __init__(self) -> None:
        self._heap: list[_Entry] = []
        self._counter = itertools.count()

    def submit(self, ready_at: float, priority: int, run: Callable[[], None]) -> None:
        entry = _Entry(ready_at, -priority, next(self._counter), run)
        heapq.heappush(self._heap, entry)

    def dispatch_if_ready(self, now: float) -> Optional[Callable[[], None]]:
        if not self._heap or self._heap[0].ready_at > now:
            return None
        return heapq.heappop(self._heap).run

    def size(self) -> int:
        return len(self._heap)


def demo() -> None:
    sched = Scheduler()
    log: list[str] = []
    sched.submit(0, 1, lambda: log.append("low@0"))
    sched.submit(0, 5, lambda: log.append("high@0"))
    sched.submit(10, 3, lambda: log.append("mid@10"))

    for now in (0, 5, 10):
        run = sched.dispatch_if_ready(now)
        while run is not None:
            run()
            run = sched.dispatch_if_ready(now)

    print(", ".join(log))


if __name__ == "__main__":
    demo()
```

### Go

```go
package main

import (
	"container/heap"
	"fmt"
)

type task struct {
	readyAt  int
	priority int
	run      func()
}

type readySet []*task

func (r readySet) Len() int { return len(r) }

func (r readySet) Less(i, j int) bool {
	if r[i].readyAt != r[j].readyAt {
		return r[i].readyAt < r[j].readyAt
	}
	return r[i].priority > r[j].priority
}

func (r readySet) Swap(i, j int) { r[i], r[j] = r[j], r[i] }

func (r *readySet) Push(x any) { *r = append(*r, x.(*task)) }

func (r *readySet) Pop() any {
	old := *r
	n := len(old)
	t := old[n-1]
	*r = old[:n-1]
	return t
}

type scheduler struct {
	heap readySet
}

func newScheduler() *scheduler {
	s := &scheduler{}
	heap.Init(&s.heap)
	return s
}

func (s *scheduler) submit(t *task) {
	heap.Push(&s.heap, t)
}

// dispatchIfReady pops and returns the next task if it is eligible to run at now, else nil.
func (s *scheduler) dispatchIfReady(now int) *task {
	if s.heap.Len() == 0 || s.heap[0].readyAt > now {
		return nil
	}
	return heap.Pop(&s.heap).(*task)
}

func main() {
	s := newScheduler()
	log := []string{}
	s.submit(&task{readyAt: 0, priority: 1, run: func() { log = append(log, "low@0") }})
	s.submit(&task{readyAt: 0, priority: 5, run: func() { log = append(log, "high@0") }})
	s.submit(&task{readyAt: 10, priority: 3, run: func() { log = append(log, "mid@10") }})

	for _, now := range []int{0, 5, 10} {
		for {
			t := s.dispatchIfReady(now)
			if t == nil {
				break
			}
			t.run()
		}
	}
	fmt.Println(log)
}
```
