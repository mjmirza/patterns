---
name: Read-Copy-Update
slug: read-copy-update
family: 09-concurrency
category: Concurrency
aliases: [RCU, Read-Copy Update, Quiescent-State-Based Reclamation, Epoch-Based Reclamation (sibling technique)]
first_described: "Slingwine, McKenney patent 1995; McKenney, Slingwine 'Read-Copy Update' USENIX 1998"
maturity: canonical
related: [copy-on-write, double-checked-locking, read-write-lock, immutable-object, versioned-value, optimistic-concurrency-control]
incompatible_with: [pessimistic-locking-only-designs]
verified: 2026-08-02
---

# Read-Copy-Update

## 1. Name, aliases, and lineage

The canonical name is Read-Copy Update, almost always written as the acronym
RCU. The mechanism was patented by James Slingwine and Paul E. McKenney, U.S.
Patent 5,442,758, granted August 1995, which the patent record describes as
implemented first in Sequent Computer Systems' DYNIX/ptx kernel and later in
Linux ([Wikipedia, "Read-copy-update", history section](https://en.wikipedia.org/wiki/Read-copy-update),
verified 2026-08-02). The formal write-up under the name "Read-Copy Update"
that the field cites as the origin paper is McKenney and Slingwine's 1998
USENIX paper of that title, which is why the pattern's first_described date in
this entry's frontmatter marks 1998 as the point the technique got its
public name and a general description, separate from the earlier 1995 patent
filing that covers the same mechanism in DYNIX/ptx.

An earlier, independently arrived-at RCU-like technique appears in U.S. Patent
4,809,168, filed by James P. Hennessy, Damian L. Osisek, and Joseph W. Seigh
II, granted 1989, describing a defer-and-reclaim scheme used in IBM's VM/XA
mainframe operating system (Wikipedia, same page, verified 2026-08-02).
Academic work by H. T. Kung and Q. Lehman, and independently by Udi Manber and
Richard Rashid, and by William Pugh, described related lock-free read
techniques with deferred reclamation in the 1980s and early 1990s, which the
same source records as parallel discovery of the same idea rather than direct
lineage into the Linux implementation.

Paul E. McKenney merged RCU into the Linux kernel as an exported API. The
Linux kernel's own RCU documentation, contributed and maintained by McKenney,
describes the read side as `rcu_read_lock()` and `rcu_read_unlock()`, the
update side as `rcu_assign_pointer()` and `synchronize_rcu()`, and the read
dereference as `rcu_dereference()` ([The Linux Kernel documentation, "A Tutorial
Introduction to RCU"](https://www.kernel.org/doc/html/latest/RCU/whatisRCU.html),
verified 2026-08-02). Wikipedia's history section states that Dipankar Sarma
added RCU to Linux kernel version 2.5.43 in October 2002, which is the point
RCU became a first-class, generally available kernel synchronization
primitive rather than a subsystem-specific trick.

"Quiescent-State-Based Reclamation" (QSBR) and "Epoch-Based Reclamation" (EBR)
are the two dominant strategies by which an implementation decides when a
grace period has ended, discussed in dimension 8. Neither is a separate
pattern from RCU. Both are RCU's grace-period detection mechanism wearing a
different name, and treating them as unrelated patterns is a common
misclassification this entry corrects in dimension 13.

## 2. Problem and context

A data structure is read far more often than it is changed, and the readers
must never be made to wait for a writer, ever, not even briefly, because the
read path sits on a hot loop that runs millions of times per second, a
routing table lookup on every packet, a directory-entry cache lookup on every
file open, a listener list walk on every event, a configuration read on every
request.

A `read-write lock` solves the correctness problem but not the latency
problem. Even an uncontended `RWLock::read()` call performs an atomic
increment on a shared counter, which forces a cache-line bounce between every
core that has recently taken the lock. On a machine with sixty-four cores all
hammering the same read lock, that cache-line ping-pong becomes the
bottleneck long before any writer shows up, because the readers are now
serialized against each other through the reader-count variable even though
they are not serialized against any actual writer. Wikipedia's discussion of
RCU's motivation puts this plainly, RCU exists specifically for the case
where "the number of readers greatly outnumber the number of writers" and the
synchronization overhead of even a lightweight lock on the read side is the
thing to eliminate, not merely reduce (Wikipedia, "Read-copy-update", verified
2026-08-02).

The context that produces this problem has a recognizable shape. There is a
pointer, held in a well-known location, to an immutable or mostly-immutable
data structure, a routing table, a directory-cache entry, a configuration
object, a list of registered callbacks. Many threads dereference that pointer
concurrently and only read through it. Occasionally, one thread needs to
change what the pointer refers to, either by mutating a copy and swapping the
pointer, or by unlinking a node from a linked structure. The old version must
not be freed or reused while any reader that started before the change might
still be following a reference into it, and yet none of those readers can be
asked to announce their presence with a lock, an atomic increment, or even a
memory fence on the fast path, because that announcement is exactly the cost
RCU exists to remove.

RCU's answer is to split "delete" into two separate moments in time. The
writer atomically removes the old reference so that no *new* reader can find
it, which is cheap, a single atomic pointer store. Then the writer waits, or
schedules a callback to run later, until it can prove that every reader who
might have already grabbed the old reference before the removal has finished
using it. Only then is the memory reclaimed. That waiting period, from "the
old reference is unreachable to new readers" to "it is provably unreachable
to every reader," is called the grace period, and it is the single defining
concept of the entire pattern.

## 3. Forces

- **Read-path latency.** Strongly favoured, to the point of being the entire
  reason the pattern exists. `rcu_dereference()` compiles down to a plain
  load plus a compiler barrier on most architectures, with no atomic
  read-modify-write instruction and no cache-line contention between readers
  ([kernel.org RCU tutorial](https://www.kernel.org/doc/html/latest/RCU/whatisRCU.html),
  verified 2026-08-02).
- **Reclamation latency.** Sacrificed. Memory freed by a writer is not
  actually freed until the grace period ends, which can be microseconds under
  QSBR with cooperative readers, or effectively unbounded if a reader thread
  is preempted or blocked mid-critical-section and never returns to release
  its grace-period debt. The pattern trades a bounded, predictable read cost
  for an unbounded, workload-dependent reclamation delay.
- **Memory footprint.** Sacrificed. Because reclamation is deferred, more than
  one version of a structure can be alive at once, sometimes several versions
  under sustained high write rates with slow readers. A system with readers
  that can block for a long time, holding an RCU read-side critical section
  open across a page fault for instance, can accumulate an unbounded amount
  of stale memory, which is why RCU implementations forbid blocking inside a
  read-side critical section in the classic kernel form, see dimension 4.
- **Write-path throughput.** Mixed. A single writer pays only the cost of
  building the new version and one atomic pointer swap, which is cheap.
  Multiple concurrent writers must still be serialized against each other by
  a separate lock, because RCU says nothing about writer-writer coordination,
  only about reader-writer coordination.
- **Consistency model.** Sacrificed relative to a mutex, deliberately. A
  reader that starts before an update and one that starts after it can be
  running concurrently against two different, both internally-consistent,
  versions of the data. This is a stated design choice, not a bug. RCU
  guarantees that a reader sees a coherent single point-in-time snapshot for
  the duration of its own critical section, never a torn or half-updated
  view, but it does not guarantee that two readers active at the same wall
  clock instant see the same snapshot as each other.
- **Structural flexibility.** Sacrificed for in-place field mutation, favoured
  for whole-node replacement. Because a reader may be mid-dereference of a
  node at any point, a writer cannot safely mutate an existing field a reader
  might be reading unless that single field write is naturally atomic, a
  machine word. Any change larger than one atomically-writable word requires
  building a new node and swapping a pointer to it, never editing the old
  node in place.
- **Cognitive load.** Sacrificed. The grace-period concept, the requirement
  that read-side critical sections never block, and the platform-specific
  memory-ordering rules around `rcu_assign_pointer` and `rcu_dereference` are
  genuinely hard to internalize correctly, which is why misuse dominates
  dimension 11.
- **Portability across languages.** Sacrificed outside systems languages with
  manual memory management or an escape hatch from the garbage collector. In
  a garbage-collected language, the reclamation half of RCU is frequently
  unnecessary, because the collector already defers freeing an object until
  no reference to it remains reachable, see dimension 8's discussion of the
  garbage-collected simplification.

## 4. Applicability and non-applicability

Reach for RCU, or one of its language-level analogues, when the following
hold together.

- Reads vastly outnumber writes, by an order of magnitude or more, and the
  read path is latency-sensitive enough that even an uncontended lock's
  atomic-instruction cost is unacceptable.
- The protected data structure can be read as an immutable, or effectively
  immutable, snapshot for the duration of one read-side critical section.
  Readers do not need to see writes made by other threads mid-critical
  section.
- The update is naturally expressible as either a single-pointer swap to a
  freshly built replacement, or an atomic unlink of one node from a larger
  structure that other nodes do not need to be aware changed.
- Read-side critical sections are short and bounded, and can be guaranteed
  never to block, sleep, wait on I/O, or recursively enter a lock that a
  writer might be holding while waiting for the grace period.
- The platform provides, or the language runtime already provides for free,
  a mechanism to detect when a grace period has ended, quiescent-state
  reporting, an epoch counter, hazard pointers, or, in a garbage-collected
  runtime, the collector itself.

Do NOT reach for RCU in the following cases, and the reason is the important
part.

- **Writes are frequent or comparable in volume to reads.** RCU's entire
  value proposition is a cheap read path bought by an expensive, deferred
  write path. A workload with a roughly even read-write mix gets none of the
  benefit and all of the reclamation-latency and memory-overhead cost. A
  plain mutex, or an optimistic-concurrency-control scheme with retry, is the
  honest choice, see dimension 12.
- **A read-side critical section must block.** If a reader might sleep, wait
  on a channel, perform I/O, or otherwise yield the processor while still
  holding a live reference into the protected structure, the grace period
  that a synchronous writer is waiting on can be delayed indefinitely, which
  in the worst case looks exactly like a deadlock even though no lock is
  held. The classic Linux kernel RCU flavor forbids blocking in a read-side
  critical section for exactly this reason (kernel.org RCU tutorial, verified
  2026-08-02). Sleepable RCU (SRCU) exists precisely to relax this constraint
  at the cost of a heavier per-critical-section cost, see dimension 8.
- **Multiple fields must be updated together, and torn intermediate states
  matter across node boundaries, not just within one node.** RCU guarantees a
  reader never sees a torn write to a single word, and never sees a
  partially-constructed node, because the node is fully built before the
  publishing pointer swap. It says nothing about consistency across two
  separate RCU-protected pointers updated by two separate writer
  transactions. A reader that dereferences pointer A, then pointer B, can
  observe a state where A reflects the new version and B still reflects the
  old one, if the writer updated them as two independent RCU updates rather
  than one. Multi-object transactional consistency needs a different pattern,
  see the trade-off table in dimension 12, or a single top-level RCU pointer
  that encompasses both A and B inside one immutable snapshot.
- **The language and runtime already give you safe concurrent reads for
  free.** In a language with a stop-the-world or concurrent tracing garbage
  collector and a memory model that makes a single reference read or write
  atomic, Java's `volatile` field semantics, or CPython's Global Interpreter
  Lock serializing all bytecode including attribute reads, reimplementing
  RCU's reclamation machinery by hand is very often solving a problem the
  runtime has already solved. `CopyOnWriteArrayList` in the Java standard
  library is exactly this. The copy-on-write half of RCU implemented as a
  library type, with the reclamation half handled entirely by the garbage
  collector once the old array becomes unreachable (Oracle Java SE 21 API
  documentation, `java.util.concurrent.CopyOnWriteArrayList`,
  https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/CopyOnWriteArrayList.html,
  verified 2026-08-02). Hand-rolling grace-period tracking on top of a GC is
  usually solving an already-solved problem, see dimension 8.
- **The whole structure is small and copying it is genuinely cheap in
  absolute terms.** If a copy of the protected structure is a few dozen
  bytes, plain `copy-on-write` with an atomic reference swap and no explicit
  grace-period tracking, relying on the language's ownership or GC for
  reclamation, is simpler than RCU's manual grace-period machinery and
  achieves the same read-side cost. RCU's additional machinery earns its
  place specifically when reclamation cannot be handed to a collector or an
  ownership system, most often in a systems language managing memory by
  hand, see the sibling `copy-on-write` entry and dimension 13.
- **Strong linearizability across the whole structure is a hard requirement.**
  RCU is intentionally not linearizable in the classical sense. Two
  concurrent reads can observe different versions even though neither reader
  is wrong. A system that must present a single, globally-agreed order of
  all operations, a distributed consensus log for example, needs a pattern
  built for that guarantee, not RCU.

## 5. Structure

RCU does not name classes the way an object-oriented pattern does. Its
participants are roles played by code paths and by the reclamation
subsystem.

- **Protected Data.** The structure being read and updated, a pointer, a
  linked list node, or a hash table bucket chain. Treated as immutable once
  published; a writer never mutates a live, published node in place except
  through a single atomically-writable field.
- **Reader.** Any thread that enters a read-side critical section
  (`rcu_read_lock()` / `rcu_read_unlock()` in the kernel API, or the
  equivalent guard object in a userspace library), dereferences the
  protected pointer through the reclamation-safe accessor
  (`rcu_dereference()`), and uses the data it finds, without ever writing to
  it and without blocking while inside the section.
- **Writer (updater).** The thread performing a change. Builds the new
  version of the data off to the side, where no reader can see it yet.
  Publishes it with a single atomic, ordered store
  (`rcu_assign_pointer()`), which makes it visible to any reader that starts
  a critical section from that point onward. Existing in-flight readers may
  still be following the pointer to the old version; the writer does not
  wait for them synchronously before returning from the update, it defers.
- **Grace Period Detector.** The subsystem that determines when the old
  version is provably unreachable to any reader that could have obtained it
  before the update. This is the part that varies most across
  implementations, see dimension 8. It can be quiescent-state reporting
  (readers periodically declare "I hold no reference right now"), epoch
  counting (a global generation counter each reader stamps on entry and
  compares on exit), hazard pointers (each reader publishes exactly which
  pointer it currently holds), or, in the kernel, a scheduler-cooperative
  scheme where a full pass through every CPU's scheduler counts as proof
  every reader on that CPU has exited any critical section it was in.
- **Reclaimer.** The code that actually frees the old version, invoked either
  synchronously after `synchronize_rcu()` returns, the writer blocks until
  the grace period is over then frees inline, or asynchronously via
  `call_rcu()`, the writer hands the free operation to a callback queue and
  returns immediately, and the reclamation subsystem runs the callback once
  the grace period elapses.

## 6. ASCII structure diagram

```
+--------------------+
| Published Pointer  |
| (atomic, one word) |
+--------------------+
           |
           | rcu_dereference (readers follow)
           | rcu_assign_pointer (writer publishes)
           v
+--------------------------+
| Version N (live)         |
| immutable once published |
+--------------------------+

Reader A:
  rcu_read_lock()
  p = rcu_dereference()
  use(*p)  -- reading Version N
  rcu_read_unlock()

Reader B (started earlier, still holds ptr to Version N):
  ... still inside its critical section ...
  rcu_read_unlock()  -- exits later, and that is allowed

Writer:
  build Version N+1 (off to the side, no reader can see
  it yet)
  rcu_assign_pointer(--> N+1)
  Published Pointer now -> N+1. New readers see N+1
  immediately.
           |
           v
+-------------------------------------------+
| Grace Period Detector                     |
| waits until every reader that could hold  |
| Version N has exited its critical section |
+-------------------------------------------+
           |
           v
+----------------------------------------+
| Reclaimer                              |
| frees Version N                        |
| (synchronize_rcu or call_rcu callback) |
+----------------------------------------+
```

## 7. Dynamics

The property worth internalizing is that the writer's publish step and the
reclaimer's free step are separated in time by an interval whose length the
writer does not control and does not need to know in advance. The publish is
synchronous and instant. The reclamation is deferred and asynchronous.

```
Reader R1              Published Ptr           Writer W               Grace Period
--------              -------------           --------               ------------
rcu_read_lock()
p1 = deref() ---------------> Version N
                                                build Version N+1
                                                (no readers can see it)
                       Version N <--------------|
use(p1)                                          |
  (still reading N)                              |-- rcu_assign_pointer(N+1)
                       Version N+1 <-------------|
                                                  |  new readers now see N+1
rcu_read_unlock()                                |
                                                  |-- call_rcu(free, N) OR
                                                  |   synchronize_rcu(); free(N)
                                                  |
                                                  |----------------------------> starts
                                                  |                              tracking
                                                  |                              has R1
                                                  |                              exited its
                                                  |                              section that
                                                  |                              began before
                                                  |                              the update
R1's rcu_read_unlock()
already happened above ------------------------------------------------------> YES, R1 quiesced
                                                                                  |
                                                                                  v
                                                                          grace period ends
                                                                          reclaimer frees
                                                                          Version N
```

Two timing properties matter beyond the diagram. First, `synchronize_rcu()`
and its equivalents are not instantaneous, and calling it from inside another
reader's critical section, or from a context that a reader's critical section
might itself be blocked waiting on, is the textbook way to construct a
deadlock that looks like a hang rather than a classic lock-ordering cycle,
covered in dimension 11. Second, RCU makes no promise about how long an
in-flight reader takes to finish; a reader that is preempted for a long time
by the scheduler, or that incorrectly blocks inside its critical section,
extends the grace period for that entire duration, and every writer waiting
on `synchronize_rcu()` is stalled behind it.

## 8. Implementation variants

**Kernel RCU with `synchronize_rcu()`, blocking form.** The writer publishes
the new pointer, then calls `synchronize_rcu()`, which blocks the writer's
own thread until the grace period has elapsed, then the writer frees the old
version inline. Simplest to reason about; the writer pays the full
grace-period latency synchronously.

**Kernel RCU with `call_rcu()`, deferred callback form.** The writer
publishes, registers a callback and the pointer to free, and returns
immediately without waiting. The reclamation subsystem invokes the callback
once the grace period ends, typically from a softirq context. Removes writer
latency at the cost of a slightly more complex API and callbacks that must
themselves be safe to run in that context (kernel.org RCU tutorial, verified
2026-08-02).

**SRCU, sleepable RCU.** A variant of the same idea for the case where a
reader's critical section genuinely must block, waiting on a mutex, doing
I/O. Each SRCU domain tracks its own grace periods independently and pays a
noticeably higher per-critical-section cost than classic RCU in exchange for
allowing readers to sleep, which classic RCU forbids.

**Quiescent-State-Based Reclamation (QSBR).** Readers do not mark the
boundaries of every critical section explicitly. Instead, each reader thread
periodically calls a single "I am quiescent right now" function from a
natural point in its own loop, and a writer's grace period ends once every
registered reader has reported quiescence at least once since the update.
This is the cheapest read side of any RCU flavor, because a reader that never
needs to report anything mid-loop pays literally zero synchronization cost
per read, but it requires application code to cooperate by calling into the
quiescent-state API at a bounded interval, which DPDK's RCU library documents
explicitly for packet-processing loops, treating the top of a `while(1)`
receive loop as the natural quiescent point (DPDK Programmer's Guide, "RCU
Library", https://doc.dpdk.org/guides/prog_guide/rcu_lib.html, verified
2026-08-02). Userspace RCU's `liburcu-qsbr` flavor is the same idea
implemented as a standalone library outside the kernel (liburcu.org, verified
2026-08-02).

**Epoch-Based Reclamation (EBR).** A close relative of QSBR that reasons in
terms of a small number of globally shared epoch counters rather than
explicit per-thread quiescence reports. A reader "pins" the current global
epoch on entry to a critical section by incrementing a per-thread counter; a
writer that wants to reclaim memory advances the global epoch and can only
free objects retired two epochs ago, once it has confirmed no thread is still
pinned to an older epoch. Rust's `crossbeam-epoch` crate implements this
strategy explicitly. A `Guard` returned by `pin()` marks the pinning thread's
participation, `Atomic<T>` provides the lock-free published pointer, and
`Guard::defer_destroy()` schedules destruction once the epoch has advanced
far enough that no pinned reader can still be referencing the object
(docs.rs, `crossbeam_epoch` crate documentation,
https://docs.rs/crossbeam-epoch/latest/crossbeam_epoch/, verified 2026-08-02).
The crate's own documentation does not use the term "RCU" (confirmed against
the fetched page, verified 2026-08-02); this entry states the relationship as
engineering judgement, not a sourced claim. Epoch-based reclamation and RCU
solve the identical deferred-reclamation problem with structurally
equivalent designs, a published atomic pointer plus a proof that no reader
predates the current version, and the academic and userspace-RCU literature
generally treats EBR as one of RCU's grace-period-detection strategies rather
than a separate invention, which is why this entry lists it as an alias for
one implementation family rather than a distinct pattern.

**Hazard pointers.** A different, per-object rather than per-epoch,
grace-period substitute. Each reader publishes, in a small fixed array
visible to writers, the exact pointer it currently holds. A writer that wants
to reclaim an object scans every reader's hazard-pointer slots and only frees
the object once no slot names it. This trades a slightly higher per-read cost,
a store to the hazard slot plus a fence, for a much lower worst-case
reclamation delay than epoch or quiescent-state schemes, because a single
slow reader only blocks reclamation of the specific object it is holding, not
every object retired since it started.

**Manual pointer-swap RCU with a background reclaimer thread.** The
lightest-weight userspace implementation. An atomic pointer to an immutable
version, a per-reader epoch counter array the writer scans to confirm every
reader has advanced past the update, and a dedicated thread that performs the
actual free once the scan confirms quiescence. This is the shape used in the
Go and Rust code examples in the code examples section, chosen because it
compiles from the standard library alone and demonstrates every moving part
without a third-party crate.

**Copy-on-write with garbage-collector reclamation, the simplified,
GC-backed form.** In a language with a tracing garbage collector, and a
memory model where a single reference field's read or write is not torn, the
reclamation half of RCU is unnecessary. Once the old version becomes
unreachable from the published pointer, the collector frees it in its own
time, whenever no reference to it survives anywhere, including inside any
reader that is still using it. This is exactly what
`java.util.concurrent.CopyOnWriteArrayList` does. Every mutating operation
makes "a fresh copy of the underlying array," and readers hold a stable
snapshot reference that "will not reflect additions, removals, or changes to
the list since the iterator was created," with no explicit grace-period
tracking anywhere in the implementation, because the collector is the grace
period detector (Oracle Java SE 21 API documentation,
`CopyOnWriteArrayList`, verified 2026-08-02). The TypeScript and Python code
examples below use the same simplification, appropriately, because both
languages give the programmer either a full garbage collector, both, or a
Global Interpreter Lock that makes a single reference assignment or read
atomic, CPython specifically, which removes the need to hand-roll a grace
period.

## 9. Known production uses

**Linux kernel, directory-entry cache and routing subsystems.** The kernel's
own RCU tutorial documents `rcu_read_lock()`, `rcu_dereference()`,
`rcu_assign_pointer()`, and `synchronize_rcu()` as the standing kernel API,
and Dipankar Sarma merged RCU into mainline Linux 2.5.43 in October 2002
(kernel.org RCU tutorial, verified 2026-08-02; Wikipedia "Read-copy-update"
history section, verified 2026-08-02). RCU protects hot lookup paths executed
on every system call that touches the filesystem or the network stack,
exactly the "reads vastly outnumber writes" shape this entry describes in
dimension 2.

**Userspace RCU library (liburcu), across multiple independent daemons.**
liburcu's own project page lists Knot DNS, GlusterFS, ISC BIND, XFS user
tools, netsniff-ng, and Sheepdog among the projects it powers, offering
multiple flavors including `liburcu-qsbr` for the fastest read side and
`liburcu-bp`, "bulletproof," for embedding into tracing libraries without
requiring the host application to be modified (liburcu.org, verified
2026-08-02). This is the strongest evidence that RCU's benefit generalizes
past a single monolithic kernel into ordinary userspace daemons that face the
same read-heavy, low-latency lookup problem.

**Java standard library, `java.util.concurrent.CopyOnWriteArrayList`.**
Documented by Oracle as implementing every mutative operation "by making a
fresh copy of the underlying array," explicitly recommended "when traversal
operations vastly outnumber mutations," which is the standard-library
embodiment of RCU's copy-on-write half with the JVM garbage collector
standing in for the grace-period reclaimer (Oracle Java SE 21 API
documentation, verified 2026-08-02). Its most common production use is
protecting listener and observer lists that are iterated far more often than
they are mutated.

**FreeBSD kernel, `epoch(9)`.** FreeBSD's epoch framework, present since
FreeBSD 11.0, provides `epoch_enter`, `epoch_exit`, `epoch_wait`, and
`epoch_call`, described in its own manual page as deferring "reclamation and
mutation until a grace period has elapsed" so that "entering and leaving an
epoch section will never block" (FreeBSD manual pages, `epoch(9)`, verified
2026-08-02). FreeBSD's network stack, including packet-filter (`pf`) address
list traversal, is documented as a consumer of this exact mechanism, again
matching the hot-lookup-path profile.

**DPDK RCU library, network function packet processing.** DPDK documents its
`rte_rcu` library as solving the deferred-reclamation problem for lock-free
data structures on the data plane, using a quiescent-state-based scheme where
the natural loop boundary of a packet-receive `while(1)` loop is treated as
the quiescent point, with `rte_rcu_qsbr_synchronize()` for the writer side
(DPDK Programmer's Guide, "RCU Library", verified 2026-08-02). This is a
production use in high-throughput network function virtualization, where the
per-packet read cost this entry's forces section describes is not a
theoretical concern but the entire performance budget of the system.

## 10. Consequences

Positive.

- Readers pay essentially zero synchronization cost, a load and a compiler
  barrier, with no atomic read-modify-write instruction and no shared
  cache-line contention between concurrently reading cores.
- Read-side scalability is close to perfectly linear with core count, since
  readers do not contend with each other or with writers in any way that
  requires a shared mutable counter on the fast path.
- A reader is guaranteed a fully consistent, never-torn view of the structure
  for the entire duration of its critical section, because it is always
  looking at one complete, immutable version.
- Writers never block readers, and readers never block writers from
  publishing; the two sides only interact through the deferred reclamation
  step, which happens off the critical path of both.
- The pattern composes cleanly with lock-free linked structures. Unlinking
  one node from a list is a single atomic pointer write, independent of the
  structure's total size.

Negative.

- Reclamation is deferred and its timing is not controlled by the writer,
  which means memory usage can spike under a write-heavy burst combined with
  slow or numerous concurrent readers, and worst-case memory overhead is
  workload-dependent rather than a fixed constant.
- A reader that blocks, sleeps, or is preempted for an extended period while
  holding a live read-side reference extends every pending grace period for
  as long as it is stalled, which can starve writers indefinitely in
  pathological cases.
- Multi-object updates are not atomic across separate RCU-protected pointers.
  A reader can observe old-version-A paired with new-version-B if the writer
  updated them as two separate publish steps rather than one, see dimension 4.
- The correctness of the grace-period detector is subtle and platform- and
  memory-model-specific; a missing memory barrier around
  `rcu_assign_pointer` or its equivalent can allow a reader to observe a
  partially initialized new object, which is exactly the class of bug this
  pattern exists to prevent and can silently reintroduce if implemented
  incorrectly by hand.
- Debugging a stalled grace period, in production, looks like a hang with no
  obvious lock held, because RCU's write-side wait is not a lock wait and
  does not show up in a conventional lock-contention profiler the same way.

## 11. Failure modes and misuse

**Blocking inside a read-side critical section.** Symptom. Under sustained
write load, writer threads calling `synchronize_rcu()` or its equivalent
appear to hang indefinitely, with no deadlock cycle visible to a lock
analyzer because no conventional lock is involved. Cause. A reader entered
its critical section, then called into code that slept, waited on I/O, or
took a blocking lock, extending the reader's critical section, and therefore
the grace period, for the duration of that block. Fix. Audit every code path
reachable from inside `rcu_read_lock()` / `rcu_read_unlock()` for anything
that can yield the processor; move such work outside the critical section, or
switch to a sleepable variant such as SRCU that is designed for this case.

**Missing publish barrier.** Symptom. A reader occasionally observes a
partially initialized version of the new node, a pointer field that is set
but a length or size field that still reads as the old value, producing an
out-of-bounds read or a crash that reproduces rarely and only under real
concurrency, never in a single-threaded test. Cause. The writer built the new
node's fields and then published the pointer with a plain store instead of
the ordered `rcu_assign_pointer()`, or the language's release-ordered atomic
store, so the CPU or compiler reordered the node's field writes to happen
after the pointer became visible to another core. Fix. Always publish through
the release-ordered primitive the platform provides, never a plain
assignment, and never assume that a language's default variable assignment
carries the necessary memory ordering across threads.

**Treating RCU as a general-purpose replacement for locking.** Symptom. A
team introduces RCU-protected pointers throughout a codebase with a roughly
even read-write ratio, and overall throughput drops rather than improves.
Cause. RCU's write side, particularly the writer-writer serialization a
separate lock must still provide plus the grace-period wait, is more
expensive than a plain mutex acquisition when writes are frequent; the
pattern's entire value proposition depends on the read-heavy assumption in
dimension 4, and violating that assumption inverts the trade-off. Fix.
Measure the actual read-write ratio before adopting RCU; fall back to a
read-write lock or plain mutex when writes are not rare.

**Freeing memory the instant the pointer is swapped.** Symptom. A crash or
memory-corruption bug that reproduces only under concurrent load, where a
reader dereferences a pointer to memory that has already been freed and
possibly reused for something else. Cause. A developer implemented the
copy-on-write half of RCU, build new version, swap the pointer, but skipped
the grace-period wait entirely, freeing the old version immediately after the
swap, which is a plain, unsafe copy-and-swap rather than RCU, and is unsafe
precisely because it discards the one property RCU exists to provide. Fix.
Never free the old version synchronously at the point of publish; always
route it through the grace-period mechanism, whether that is
`synchronize_rcu()`, `call_rcu()`, an epoch-guard's deferred destructor, or,
in a garbage-collected language, simply letting the collector do its job by
never manually freeing at all.

**Multi-pointer update mistaken for atomic.** Symptom. A reader sees an
internally inconsistent combination of two related RCU-protected structures,
for example a routing table entry that references a next-hop object that no
longer exists in the corresponding next-hop table, because the two tables
were updated as two separate RCU publish operations. Cause. The design
assumed RCU gives cross-structure atomicity, which it does not, see dimension
4. Fix. Fold the related structures into a single top-level immutable
snapshot object published through one pointer, so that one publish step
updates everything a reader needs to see consistently together.

## 12. Trade-off matrix

Compared against the concurrency-control patterns readers most often confuse
RCU with, or reach for in the same situation.

| Dimension | Read-Copy-Update | Read-Write Lock | Plain `copy-on-write` (no grace period) | Optimistic Concurrency Control (retry-on-conflict) | Immutable Object with GC reclamation |
|---|---|---|---|---|---|
| Read-side cost | Load plus compiler barrier, no atomic RMW | Atomic increment or decrement per acquire, cache-line contention under many readers | Same as RCU's read side | Read is cheap, but must validate or retry on conflicting write | Same as RCU's read side |
| Writer-writer coordination | Needs a separate lock or CAS loop; RCU says nothing about this | Built in, exclusive write lock | Needs a separate lock or CAS loop | Built in via the validate-and-retry protocol | Needs a separate lock or CAS loop |
| Blocking readers allowed | No (classic form); needs SRCU variant to allow it | Yes | Yes | Yes | Yes |
| Reclamation timing | Deferred to a proven grace period; manual bookkeeping in a non-GC language | Immediate; the lock itself prevents unsafe reuse | Immediate and unsafe unless the language's GC or ownership system defers it | Immediate; no stale-version problem because nothing is swapped | Deferred entirely to the collector; no manual bookkeeping needed |
| Cross-structure atomicity | No, unless folded into one top-level snapshot | Yes, if both structures share the same lock | No | Depends on the transaction's read/write set | No, unless folded into one top-level snapshot |
| Best read-write ratio | Very read-heavy, order of magnitude or more | Balanced to read-heavy | Very read-heavy, and small enough that copying is cheap | Low-contention writes with occasional conflicting retries | Very read-heavy, when GC already exists |
| Needs manual memory reclamation logic | Yes, in a non-GC language | No | No, but unsafe without it | No | No |

## 13. Related and incompatible patterns

**`copy-on-write` (sibling entry, this repository).** RCU's publish step,
build a new version and atomically swap a pointer to it, is exactly the
copy-on-write pattern applied to a single reference. RCU is the superset. It
adds the grace-period reclamation discipline that makes copy-on-write safe to
use with manual memory management, and it also covers the narrower case of
unlinking a single node from a larger structure without copying the whole
structure, which plain copy-on-write as usually described does not address.
Where the language provides a garbage collector, plain copy-on-write and RCU
converge, see dimension 8.

**`double-checked-locking` (sibling entry, this repository).** Both patterns
exist to make a read path cheap by avoiding a lock on the common case. They
differ in what they protect. Double-checked locking optimizes a one-time
lazy initialization check, re-verifying under a lock only on the rare
first-access race, while RCU optimizes an ongoing, repeatedly-read,
occasionally-updated structure. A correct double-checked-locking
implementation in a language without RCU-grade memory ordering guarantees
needs the same publish-with-a-barrier discipline RCU requires, which is why
the two patterns share a failure mode, missing publish barrier, dimension
11, even though they solve different problems.

**`read-write-lock` (sibling entry, this repository).** The direct competing
pattern for the same problem, and the trade-off matrix in dimension 12
compares them head to head. RCU and a read-write lock are almost never used
together for the same piece of data, because doing so reintroduces exactly
the lock-contention cost RCU exists to remove; they can coexist in the same
system protecting different data structures with different read-write
ratios.

**`immutable-object` (sibling entry, this repository).** RCU's Protected
Data participant is, in every implementation, an instance of an immutable
object once published. RCU is best understood as immutable-object plus a
protocol for safely swapping which immutable instance is currently
published, plus a protocol for safely reclaiming the previous one.

**Optimistic Concurrency Control and versioned values.** Where RCU defers
reclamation until readers provably finish, optimistic concurrency defers
conflict detection until a writer commits, retrying the writer's work if a
conflicting write is detected. The two are not interchangeable. RCU makes no
promise that a writer's update is based on the latest version, a writer that
built its new version from a stale read may clobber a concurrent writer's
change, whereas optimistic concurrency's validation step exists specifically
to catch that case. A system that needs both cheap reads and conflict-safe
writes based on the value actually read may combine RCU-style publication for
the read path with a compare-and-swap or version-stamp check on the write
path.

**Incompatible with designs that assume a single, globally exclusive lock
protects all mutable state.** A codebase built around one big lock cannot
adopt RCU incrementally for a subset of its state without carefully auditing
that no code path holds the big lock while inside an RCU read-side critical
section that a writer's grace period might be waiting on, because that
combination is precisely the blocking-reader deadlock pattern described in
dimension 11.

## 14. Refactoring path in and out

Introducing RCU into code that currently uses a `read-write-lock` or a
plain mutex around a rarely-changing structure.

1. Confirm the actual read-write ratio with production measurement, not
   intuition; RCU is a net loss below roughly a ten-to-one read-to-write
   ratio, per the forces discussion in dimension 3.
2. Identify every field a reader currently reads while holding the lock, and
   check whether the entire read-side use fits within a single, short,
   non-blocking critical section. If any reader currently sleeps, does I/O,
   or recursively acquires another lock while holding the read lock, that
   code path must be restructured before RCU can be introduced safely.
3. Wrap the protected structure behind a single published pointer, or, in a
   garbage-collected language, a single mutable reference, rather than
   exposing individual mutable fields for direct access.
4. Replace the read lock acquisition with the platform's RCU read-side
   primitive, or, in a garbage-collected language, a plain load of the
   reference, since the language's memory model already guarantees a
   non-torn read of a single reference in the common case; verify this
   against the specific language's memory model rather than assuming it.
5. Replace the write path with build-new-version-then-publish, and route
   the old version's disposal through the platform's grace-period mechanism
   rather than freeing it directly; in a garbage-collected language this
   step can often be a no-op, because simply dropping the last reference and
   letting the collector run is the entire reclamation mechanism.
6. Serialize concurrent writers with a separate, narrow-scope lock or a
   compare-and-swap loop; RCU does not provide this on its own, per
   dimension 5.
7. Add the misuse checks from dimension 11 to code review or static analysis
   where the platform supports it, particularly the no-blocking-inside-the-
   critical-section rule.

Removing RCU when the read-write ratio has shifted, or the manual
reclamation machinery has become a maintenance burden disproportionate to
its benefit.

1. Measure whether reads still dominate writes by the margin that justified
   the original adoption; if writes have become frequent, this is a strong
   signal to remove RCU rather than tune it further.
2. Replace the published pointer and its grace-period-tracked reclamation
   with a conventional `read-write-lock` guarding the same structure, which
   restores writer-blocks-readers semantics but removes the grace-period
   bookkeeping entirely.
3. Delete the reader-registration, epoch-tracking, or hazard-pointer
   machinery once no code path still calls into it; leaving dead
   reader-registration code after removing its last caller is a common
   source of confusion in a later refactor.
4. Re-run the same production measurement from step one of the introduction
   path afterward, to confirm the removal did not reintroduce the original
   lock-contention problem the RCU adoption was solving; if it did, the
   correct fix is very often not "put RCU back everywhere" but "put RCU back
   only on the specific hot lookup path that showed the contention," per the
   applicability discussion in dimension 4.

## 15. Testing and verification

RCU's read side is easy to test for functional correctness in isolation,
because a single reader against a single, unchanging version behaves exactly
like reading any immutable object. The difficulty is entirely in the
concurrent interleaving between a writer's publish, a slow reader still
holding the old version, and the reclaimer.

- **Deterministic single-threaded tests for the data transformation itself.**
  Test that the writer's build-the-new-version step produces a correct new
  structure given a correct old one, with no concurrency involved at all.
  This is ordinary unit testing and should cover the overwhelming majority of
  logic bugs before any concurrency test runs.
- **A reader-outlives-the-update test, run deterministically.** Start a
  reader, have it capture the published reference, then perform an update
  from a second thread, or, in a single-threaded test rig, simply
  perform the update between the reader's dereference and its use of the
  data, and assert that the reader's already-captured version is unchanged
  and still fully valid. This catches the freeing-memory-instantly misuse
  from dimension 11 without needing a real race.
- **Torn-read detection via a canary field.** Give the protected structure a
  field whose correct value can only be produced by a fully completed
  construction, a checksum of the other fields, or a sentinel written last,
  and have readers assert on that field. Combined with a stress test that
  hammers concurrent publish and read from many threads, a missing publish
  barrier from dimension 11 will eventually manifest as a canary mismatch,
  though this style of test is probabilistic and can pass many times before
  catching a real ordering bug, particularly on a strongly-ordered
  architecture where the missing barrier happens not to matter in practice.
- **Thread and race sanitizers.** In languages that support them, Go's
  `-race` detector, Rust's Miri or ThreadSanitizer via LLVM, C and C++'s
  ThreadSanitizer, run every concurrency-sensitive RCU test under the
  sanitizer. These tools are specifically good at catching missing memory
  ordering on the publish path, which is otherwise one of the hardest bug
  classes to reproduce reliably by hand.
- **Grace-period liveness tests.** Assert that a writer's `synchronize_rcu()`
  equivalent actually returns within a bounded time when readers are well
  behaved, and, separately, write an explicit negative test that a reader
  which deliberately blocks inside its critical section does, in fact,
  delay the grace period, to confirm the test rig itself can detect the
  failure mode from dimension 11 rather than merely hoping it would.
- **Load testing at the target read-write ratio.** Because the entire case
  for RCU depends on the ratio assumption in dimension 4, a load test that
  exercises writes at production frequency is necessary to validate the
  adoption decision itself, not just the correctness of the implementation.

## 16. Observability signals

- **Grace period duration, as a histogram, not just an average.** The
  distribution's tail matters far more than its mean; a p99 grace-period
  duration that has crept upward over weeks is the earliest reliable signal
  that some reader is starting to hold its critical section open longer than
  intended, before that turns into an outage.
- **Count of versions currently retired but not yet reclaimed.** A healthy
  system keeps this near zero, spiking briefly during a burst of writes and
  falling back down once the grace period clears. A steadily growing count
  is the signal that reclamation is falling behind, which precedes an
  out-of-memory condition.
- **Reader critical-section duration.** Instrument entry and exit of the
  read-side critical section itself, even if only in a debug or canary
  build, since this instrumentation itself adds cost to the hot path in
  production, to catch the specific reader that is blocking or running long,
  rather than only observing the aggregate grace-period symptom downstream.
- **Writer stall time on `synchronize_rcu()` or its equivalent.** Distinct
  from grace-period duration in systems using deferred `call_rcu()`-style
  reclamation, because a writer using the deferred form does not stall at
  all; if it does stall unexpectedly, that is a signal the code has
  regressed from the deferred form back to a blocking wait somewhere.
- **Reader registration and deregistration counts, for QSBR and hazard
  pointer flavors.** A reader thread that registers but is later killed
  without deregistering, a crashed worker, an unhandled panic, can leave a
  stale registration that a naive grace-period detector waits on forever;
  monitoring the registered-reader count against the actually-alive thread
  count catches this class of leak.
- **Kernel and userspace-RCU implementations expose this directly.** The
  Linux kernel's own RCU documentation is explicit that the grace-period and
  callback-queue machinery is itself instrumented and inspectable via
  `/proc` and tracepoints for exactly this reason (kernel.org RCU tutorial,
  verified 2026-08-02); a homegrown userspace RCU implementation that skips
  building the equivalent observability from day one is choosing to debug
  production stalls blind.

## 17. Security and privacy implications

RCU's core guarantee, that a reader always sees a fully-formed, never-torn
version of the protected structure, is itself a defensive property. It rules
out an entire class of memory-safety bugs where a reader observes a
partially-initialized object and interprets uninitialized or stale memory as
valid data, which in an unmanaged language can be an information-disclosure
or memory-corruption primitive. Correctly implemented RCU is, in this
specific sense, a hardening technique rather than a risk.

The risk lives in the failure modes, not the pattern's intent. A missing
publish barrier, dimension 11, can, on a weakly-ordered architecture, allow a
reader to observe a genuinely uninitialized field of the new version, which
in the worst case is exactly the read-uninitialized-memory-across-a-trust-
boundary bug class attackers look for; this is a defect in an incorrect
implementation, not a property of RCU used correctly. A grace-period stall
caused by a reader that never returns, dimension 11's blocking-reader case,
is available as a resource-exhaustion vector in any system where an attacker
can influence how long a read-side critical section runs, for example by
triggering an expensive computation inside a critical section that should
have been kept short; the fix is the same discipline dimension 4 already
requires. This paragraph is stated as an analytical implication, not a
sourced incident; no published CVE attributing this class of exhaustion to
RCU specifically was found as of this entry's verification date.

There is no data-handling implication specific to RCU beyond ordinary memory
safety. The pattern decides when memory is reclaimed, not what is stored in
it, and does not itself introduce or remove any obligation around encryption,
access control, or data residency.

## 18. References

1. Slingwine, J., McKenney, P. E. "Method for Managing Concurrent Access to
   Shared Data by Multiple Programs," U.S. Patent 5,442,758, granted August
   1995. Cited via Wikipedia, "Read-copy-update", history section,
   https://en.wikipedia.org/wiki/Read-copy-update, verified 2026-08-02.
2. Hennessy, J. P., Osisek, D. L., Seigh, J. W. II. U.S. Patent 4,809,168,
   granted 1989. Cited via Wikipedia, "Read-copy-update", history section,
   https://en.wikipedia.org/wiki/Read-copy-update, verified 2026-08-02.
3. Wikipedia, "Read-copy-update", https://en.wikipedia.org/wiki/Read-copy-update,
   verified 2026-08-02.
4. The Linux Kernel documentation, "A Tutorial Introduction to RCU",
   https://www.kernel.org/doc/html/latest/RCU/whatisRCU.html, verified
   2026-08-02.
5. Oracle, Java SE 21 API documentation,
   `java.util.concurrent.CopyOnWriteArrayList`,
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/CopyOnWriteArrayList.html,
   verified 2026-08-02.
6. docs.rs, `crossbeam_epoch` crate documentation,
   https://docs.rs/crossbeam-epoch/latest/crossbeam_epoch/, verified
   2026-08-02.
7. liburcu.org, userspace RCU library project page, https://liburcu.org/,
   verified 2026-08-02.
8. FreeBSD manual pages, `epoch(9)`,
   https://man.freebsd.org/cgi/man.cgi?query=epoch&sektion=9, verified
   2026-08-02.
9. DPDK Programmer's Guide, "RCU Library",
   https://doc.dpdk.org/guides/prog_guide/rcu_lib.html, verified 2026-08-02.

## Code examples

RCU is a memory-reclamation strategy. Five languages are shown below,
chosen to make the manual-versus-garbage-collected distinction visible
rather than to hide it.

Go and Rust implement the mechanism close to how a real RCU library does it,
using only the standard library, with an explicit per-reader epoch array and
a writer that scans it before reclaiming, because both languages give the
programmer manual control over when memory is actually freed and neither has
a garbage collector that would make the exercise moot. Go does have a GC,
but its `atomic.Pointer` is used here specifically to demonstrate the
lock-free publish step that RCU depends on across any language; the
epoch-scan reclamation logic is the genuinely RCU-specific part.

TypeScript and Python are shown using the garbage-collected simplification
from dimension 8. The copy-on-write publish step is real and idiomatic in
both languages, and the grace-period reclamation half is delegated entirely
to the runtime's collector, which is the honest, idiomatic way to get RCU's
read-side benefit in a managed language, not a diminished version of the
pattern.

Swift is shown using a concurrent-queue-with-barrier idiom,
`DispatchQueue.concurrent` plus `.barrier` writes, which is a commonly used
Swift server-side pattern for exactly RCU's problem, cheap concurrent reads,
serialized and non-blocking-for-readers writes, but it is stated plainly here
as an approximation. Dispatch's barrier semantics serialize and exclude
readers from writers at the queue level rather than through an atomic
pointer and a proven grace period, so it does not give Swift code the
literal lock-free read guarantee the other four examples demonstrate. A
production Swift system wanting the stronger guarantee would reach for the
`swift-atomics` package's `ManagedAtomic` over a class reference, which is
not part of the base toolchain used to compile this entry's example and is
therefore not shown as running code here.

### Go

Close to a real userspace RCU. A lock-free `atomic.Pointer[Config]` for the
publish step, and a small per-reader epoch array a writer scans before
reclaiming, mirroring quiescent-state-based reclamation without a
third-party library.

```go
package main

import (
	"fmt"
	"sync"
	"sync/atomic"
)

type Config struct {
	Version int
	Rules   []string
}

// RCUConfig publishes Config lock-free and reclaims old versions only
// after every reader's epoch has advanced past the update, the same
// quiescent-state proof real RCU implementations use.
type RCUConfig struct {
	current    atomic.Pointer[Config]
	writeMu    sync.Mutex
	readEpochs []*atomic.Uint64 // one per registered reader goroutine
}

func NewRCUConfig(initial *Config, readers int) *RCUConfig {
	r := &RCUConfig{}
	r.current.Store(initial)
	for i := 0; i < readers; i++ {
		r.readEpochs = append(r.readEpochs, &atomic.Uint64{})
	}
	return r
}

// Read is the hot path: one atomic load, no lock, no contention between
// readers. This is the entire cost RCU pays on every read.
func (r *RCUConfig) Read(readerID int) *Config {
	r.readEpochs[readerID].Add(1) // odd = "inside a critical section"
	defer r.readEpochs[readerID].Add(1) // even again = "quiescent"
	return r.current.Load()
}

// Update builds a new version, publishes it with a single atomic store,
// then blocks until every reader has proven it has passed through a
// quiescent point since the publish, mirroring synchronize_rcu().
func (r *RCUConfig) Update(newCfg *Config) {
	r.writeMu.Lock()
	defer r.writeMu.Unlock()

	r.current.Store(newCfg) // the publish: one atomic word write

	// Grace period: wait until every reader's epoch is even (quiescent)
	// and has changed since we snapshot it here.
	snapshot := make([]uint64, len(r.readEpochs))
	for i, e := range r.readEpochs {
		snapshot[i] = e.Load()
	}
	for i, e := range r.readEpochs {
		for {
			cur := e.Load()
			if cur%2 == 0 && cur != snapshot[i] {
				break // this reader has quiesced since our snapshot
			}
			if cur == snapshot[i] {
				break // reader was already idle, never entered
			}
		}
	}
	// Grace period complete: it is now safe to drop the reference to
	// the old version and let Go's own GC reclaim it.
}

func main() {
	cfg := NewRCUConfig(&Config{Version: 1, Rules: []string{"allow-all"}}, 4)

	var wg sync.WaitGroup
	for reader := 0; reader < 4; reader++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			c := cfg.Read(id)
			fmt.Printf("reader %d saw version %d\n", id, c.Version)
		}(reader)
	}
	wg.Wait()

	cfg.Update(&Config{Version: 2, Rules: []string{"deny-external"}})
	c := cfg.Read(0)
	fmt.Printf("after update, reader 0 sees version %d\n", c.Version)
}
```

### Rust

The same quiescent-state-based scheme, implemented with `AtomicPtr` from the
standard library only, no `crossbeam-epoch` dependency, to keep the example
compilable with `rustc` alone.

```rust
use std::sync::atomic::{AtomicPtr, AtomicU64, Ordering};
use std::sync::Mutex;

struct Config {
    version: u32,
    rules: Vec<String>,
}

/// RCU-style config: readers dereference a raw AtomicPtr with no lock.
/// A writer publishes a new Box, then proves via per-reader epoch
/// counters that no reader can still hold the old pointer before it
/// is freed with Box::from_raw.
struct RcuConfig {
    current: AtomicPtr<Config>,
    write_lock: Mutex<()>,
    reader_epochs: Vec<AtomicU64>,
}

impl RcuConfig {
    fn new(initial: Config, reader_count: usize) -> Self {
        let boxed = Box::into_raw(Box::new(initial));
        let mut epochs = Vec::with_capacity(reader_count);
        for _ in 0..reader_count {
            epochs.push(AtomicU64::new(0));
        }
        RcuConfig {
            current: AtomicPtr::new(boxed),
            write_lock: Mutex::new(()),
            reader_epochs: epochs,
        }
    }

    /// Hot read path: an odd epoch marks "inside a critical section",
    /// an even epoch marks "quiescent". No lock, no atomic RMW beyond
    /// the epoch increment, no contention with other readers.
    fn read<'a>(&'a self, reader_id: usize) -> &'a Config {
        self.reader_epochs[reader_id].fetch_add(1, Ordering::AcqRel);
        let ptr = self.current.load(Ordering::Acquire);
        // Safety: the writer never frees the version this pointer
        // refers to until every reader has quiesced past this point.
        let cfg = unsafe { &*ptr };
        self.reader_epochs[reader_id].fetch_add(1, Ordering::AcqRel);
        cfg
    }

    /// Publishes a new Config, waits for a full grace period, then
    /// reclaims the old one, mirroring synchronize_rcu() plus free().
    fn update(&self, new_cfg: Config) {
        let _guard = self.write_lock.lock().unwrap();
        let new_ptr = Box::into_raw(Box::new(new_cfg));
        let old_ptr = self.current.swap(new_ptr, Ordering::AcqRel);

        let snapshot: Vec<u64> = self
            .reader_epochs
            .iter()
            .map(|e| e.load(Ordering::Acquire))
            .collect();
        for (epoch, &start) in self.reader_epochs.iter().zip(snapshot.iter()) {
            loop {
                let cur = epoch.load(Ordering::Acquire);
                if cur % 2 == 0 && cur != start {
                    break; // quiesced since the snapshot
                }
                if cur == start {
                    break; // was already idle
                }
                std::hint::spin_loop();
            }
        }

        // Grace period complete. No reader can still hold old_ptr.
        unsafe {
            drop(Box::from_raw(old_ptr));
        }
    }
}

fn main() {
    let cfg = RcuConfig::new(
        Config {
            version: 1,
            rules: vec!["allow-all".to_string()],
        },
        2,
    );

    {
        let seen = cfg.read(0);
        println!("reader 0 saw version {}", seen.version);
    }

    cfg.update(Config {
        version: 2,
        rules: vec!["deny-external".to_string()],
    });

    let seen = cfg.read(1);
    println!("after update, reader 1 sees version {}", seen.version);
}
```

### TypeScript

The garbage-collected simplification from dimension 8. The publish step is
a plain reference swap, and reclamation is left entirely to the runtime,
which is the idiomatic form in a managed language, not a diminished one.

```typescript
interface Config {
  readonly version: number;
  readonly rules: readonly string[];
}

/**
 * RCU-style config in a garbage-collected runtime. Readers hold a stable
 * snapshot reference; the writer publishes a new object by reassigning
 * one field. The grace period is implicit: the old Config is reclaimed
 * whenever the last reader holding it drops the reference, which the
 * garbage collector, not this class, decides and enforces.
 */
class RcuConfig {
  private current: Config;

  constructor(initial: Config) {
    this.current = initial;
  }

  // Hot read path: one property read, no lock, no atomic instruction.
  // Safe because JavaScript's single-threaded event loop guarantees
  // this read cannot interleave with a concurrent write mid-assignment.
  read(): Config {
    return this.current;
  }

  // Publish: build the new version off to the side, then swap the
  // reference in one synchronous assignment. Old snapshots already
  // held by in-flight readers remain valid and unaffected.
  update(next: Config): void {
    this.current = next;
  }
}

function main(): void {
  const cfg = new RcuConfig({ version: 1, rules: ["allow-all"] });

  const readerSnapshot = cfg.read();
  console.log(`reader captured version ${readerSnapshot.version}`);

  cfg.update({ version: 2, rules: ["deny-external"] });

  console.log(`reader's snapshot is still version ${readerSnapshot.version}`);
  console.log(`a new read sees version ${cfg.read().version}`);
}

main();
```

### Python

CPython's Global Interpreter Lock makes a single reference read or write
atomic with respect to other threads, which is exactly the property RCU's
publish step needs; the grace period is, again, delegated to the reference
counter and garbage collector.

```python
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class Config:
    version: int
    rules: List[str] = field(default_factory=list)


class RcuConfig:
    """RCU-style config relying on CPython's GIL for atomic reference
    reads and on reference counting plus the cyclic collector for
    deferred reclamation. A reader that has already captured
    self._current keeps a valid, immutable snapshot even after
    update() reassigns the attribute to a newer version.
    """

    def __init__(self, initial: Config) -> None:
        self._current = initial

    def read(self) -> Config:
        # A single attribute read of a plain reference is atomic under
        # the GIL in CPython; no lock is needed on this path. Note this
        # guarantee is specific to the GIL and does not hold under
        # free-threaded (no-GIL) CPython builds without an explicit
        # atomic or lock, which is why this is stated as a CPython
        # implementation detail rather than a language-level guarantee.
        return self._current

    def update(self, new_config: Config) -> None:
        # Publish: the new, fully-constructed Config replaces the old
        # reference in one atomic attribute assignment. The old Config
        # is reclaimed once the last reference to it, including any
        # reader still holding a snapshot, is dropped.
        self._current = new_config


def main() -> None:
    cfg = RcuConfig(Config(version=1, rules=["allow-all"]))

    snapshot = cfg.read()
    print(f"reader captured version {snapshot.version}")

    cfg.update(Config(version=2, rules=["deny-external"]))

    print(f"reader's snapshot is still version {snapshot.version}")
    print(f"a new read sees version {cfg.read().version}")


if __name__ == "__main__":
    main()
```

### Swift

An approximation using `DispatchQueue`'s concurrent-reads-exclusive-writes
barrier idiom, stated plainly as an approximation rather than literal RCU.
Dispatch serializes writers against readers at the queue-scheduling level,
which gives readers a consistent snapshot without blocking each other, but
it is not a lock-free atomic-pointer publish with a proven grace period the
way the Go and Rust examples are.

```swift
import Dispatch

struct Config {
    let version: Int
    let rules: [String]
}

/// Approximates RCU's read-cheap, write-serialized contract using a
/// concurrent DispatchQueue. Reads run concurrently with each other.
/// A write is submitted as a barrier block, which Dispatch guarantees
/// runs exclusively (no reads execute concurrently with it) and after
/// every read already queued ahead of it has completed, without the
/// barrier block itself blocking the calling thread from returning
/// once dispatched asynchronously.
final class RCUConfig {
    private var current: Config
    private let queue = DispatchQueue(
        label: "rcu-config",
        attributes: .concurrent
    )

    init(_ initial: Config) {
        self.current = initial
    }

    // Hot read path: dispatched onto the concurrent queue, so many
    // reads proceed in parallel with each other and are never blocked
    // by another read, only briefly serialized around a write barrier.
    func read() -> Config {
        queue.sync {
            current
        }
    }

    // Publish: a barrier block, guaranteed exclusive with respect to
    // both reads and other writes on this queue, replaces the
    // reference. Callers already holding an old Config value (a
    // struct, copied by value on read) are unaffected.
    func update(_ next: Config) {
        queue.async(flags: .barrier) {
            self.current = next
        }
    }
}

let cfg = RCUConfig(Config(version: 1, rules: ["allow-all"]))

let snapshot = cfg.read()
print("reader captured version \(snapshot.version)")

cfg.update(Config(version: 2, rules: ["deny-external"]))

// Because Config is a value type, `snapshot` is an independent copy
// and is unaffected by the update above.
print("reader's snapshot is still version \(snapshot.version)")
```
