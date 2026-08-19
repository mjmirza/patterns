---
name: Half-Sync/Half-Async
slug: half-sync-half-async
family: 09-concurrency
category: Concurrency
aliases: [HSHA, Half-Sync-Half-Async]
first_described: "Schmidt, Cranor 1995; Schmidt, Stal, Rohnert, Buschmann 2000"
maturity: canonical
related: [reactor, proactor, leader-followers, active-object, monitor-object, thread-pool, producer-consumer, pipeline]
incompatible_with: []
verified: 2026-08-02
---

# Half-Sync/Half-Async

## 1. Name, aliases, and lineage

The canonical name is Half-Sync/Half-Async, written with the slash and no
spaces in the original literature. The pattern was first published by
Douglas C. Schmidt and Chuck Cranor as "Half-Sync/Half-Async - An
Architectural Pattern for Efficient and Well-Structured Concurrent I/O",
presented at the Second Pattern Languages of Programs conference in
Monticello, Illinois, September 6-8, 1995, and later collected in James O.
Coplien, John Vlissides, and Norman Kerth (editors), *Pattern Languages of
Program Design 2*, Addison-Wesley, 1996
([publication list, dre.vanderbilt.edu](https://www.dre.vanderbilt.edu/~schmidt/patterns-ace.html),
verified 2026-08-02). The pattern was also given a fuller structural
treatment as part of Douglas C. Schmidt, Michael Stal, Hans Rohnert, and
Frank Buschmann, *Pattern-Oriented Software Architecture, Volume 2. Patterns
for Concurrent and Networked Objects*, John Wiley and Sons, 2000
([publisher record via Wikipedia](https://en.wikipedia.org/wiki/Pattern-Oriented_Software_Architecture),
verified 2026-08-02, ISBN 978-0-471-60695-6). Both sources agree on the same
name and the same three-layer structure, so this entry cites the pattern by
both its original PLoP paper and its book-length treatment, POSA2.

The abbreviation HSHA appears in networking and middleware source trees as a
shorthand for the pattern, most often attached to a thread-pool class or a
connector configuration flag. There is no rival name for this exact pattern.
What does vary across sources is which side is called which. Some authors
label the non-blocking side the "async layer" and the blocking side the "sync
layer", which is the vocabulary this entry uses throughout, matching the
original paper's own layer names, the Asynchronous Service Layer and the
Synchronous Service Layer, joined by a Queueing Layer.

Half-Sync/Half-Async is a structural sibling to two other Schmidt-authored
concurrency patterns, Reactor and Proactor, and it is common for a reader to
meet it only as the pattern behind a Reactor's worker pool, because in
practice a Reactor and a Half-Sync/Half-Async queueing layer are so often
built together that people stop distinguishing them. They are not the same
pattern. Reactor describes how one thread demultiplexes many I/O-ready
events. Half-Sync/Half-Async describes how a system as a whole is divided
into a non-blocking half and a blocking half, connected by a queue, and a
Reactor is one common way to build the non-blocking half, not the whole
pattern.

## 2. Problem and context

A concurrent system that talks to the outside world, over a network, a disk,
a device driver, or another process, has two kinds of code living inside it
at once, and the two kinds want opposite programming models.

The first kind is I/O-bound demultiplexing. A server accepting connections
from thousands of clients cannot afford to dedicate an operating-system
thread to every connection that is merely idle, waiting for its next byte.
The natural way to service many idle connections cheaply is a small number of
threads, often one, driving an event loop over a readiness notification
mechanism such as `select`, `poll`, `epoll`, or `kqueue`, reacting to whichever
socket becomes readable next. Code written this way is non-blocking by
construction. A call that would block is illegal inside this loop, because
one blocked call stalls every connection the loop is responsible for, not
only the slow one.

The second kind is business logic. Parsing a request, running a database
query, resizing an image, computing a hash over a large buffer, calling out
to a legacy synchronous library. This code is naturally written as a
straight-line sequence of blocking calls, because that is how the libraries,
the SQL drivers, and the file system APIs are shaped, and because a linear
function is far easier for a person to read, test, and reason about than the
same logic split across a callback chain or a state machine.

The tension is structural, not incidental. Writing the entire system in the
non-blocking style makes the demultiplexing efficient but turns every piece
of business logic into a callback-driven state machine, which is hard to
write correctly and hard to keep correct as it grows, because the control
flow that a debugger and a human reader expect to see in one function is
scattered across handler registrations. Writing the entire system in the
blocking style makes the business logic easy to read but forces a thread per
connection, which does not scale past a few thousand concurrent connections
on typical operating systems because of per-thread stack memory, context
switch overhead, and scheduler contention.

Half-Sync/Half-Async names the middle path directly. Keep exactly one small
piece of the system, the part that demultiplexes arriving work, in the
non-blocking style, and let it stay small on purpose. Move everything else,
including all business logic, into a pool of ordinary threads that are free
to block, because there are few enough of them that blocking is affordable.
Connect the two halves with a queue, so the non-blocking half never has to
wait on the blocking half and the blocking half never has to touch the
readiness-notification machinery at all.

## 3. Forces

This dimension weighs competing engineering pressures rather than stating
sourced facts. The rankings below reflect how the trade-off usually plays out
in practice, not a measured constant.

**Throughput versus code simplicity.** A fully non-blocking system can, in
principle, serve more concurrent connections per megabyte of memory than a
thread-per-connection system, because it needs far fewer OS threads. A fully
blocking system is far simpler to write correctly. Half-Sync/Half-Async
trades away some of the non-blocking system's peak connection-count ceiling
in exchange for keeping the business-logic code linear.

**Latency versus isolation.** Passing work across the queueing layer costs a
context switch and a memory hand-off that a purely single-threaded, fully
non-blocking pipeline does not pay. In return, a slow or misbehaving piece of
business logic in one worker thread cannot stall the demultiplexer that
serves every other connection, because the two run on separate threads with
only the queue between them.

**Number of threads versus contention.** More sync-layer worker threads
raise the ceiling on how much blocking work can run at once, but every
additional thread adds scheduler pressure and, if the workers share mutable
state, adds lock contention. The pool size is a tuning knob with a real cost
on both sides, not a free lever.

**Coupling to the queue's discipline.** The queueing layer's behavior under
load, unbounded, bounded with blocking producers, or bounded with dropping
producers, changes the pattern's failure mode entirely. An unbounded queue
never applies backpressure and can grow until the process runs out of memory.
A bounded queue that blocks the async layer on a full queue reintroduces the
exact blocking-in-the-event-loop problem the pattern exists to avoid. Only a
bounded queue with a non-blocking, explicit-backpressure offer preserves the
pattern's central promise.

**Debuggability versus efficiency.** Two threads of control, joined by a
queue, are individually easier to step through than a callback chain, but a
bug that only appears under specific interleavings of the async and sync
sides is harder to reproduce than a bug in a single-threaded reactor, because
the failure now depends on scheduling, not only on input.

## 4. Applicability and non-applicability

Use Half-Sync/Half-Async when the system genuinely needs both halves at once.

- The workload mixes a large number of mostly-idle I/O connections with
  per-request work that calls blocking APIs, such as a relational database
  driver, a synchronous cryptography library, or a legacy RPC client that
  offers no async variant.
- The team wants business logic written as ordinary, linear, blocking code,
  and is not willing to accept a callback-per-step or coroutine-per-step
  style across the whole codebase.
- The number of concurrent connections is large enough that a thread per
  connection is not viable, but the amount of per-request CPU or blocking
  work is small enough that a bounded pool of worker threads, sized well
  below the connection count, can absorb it.
- The system already has, or needs, a natural queueing point between
  accepting work and doing work, for example to apply admission control, rate
  limiting, or priority ordering before the blocking side sees a request.

Do not reach for it in these situations, with the reason named.

- **Every piece of work is already non-blocking end to end**, for example a
  service whose only downstream calls are other network services reached
  through async client libraries with no blocking calls anywhere in the path.
  Adding a queueing layer and a thread pool here adds latency and complexity
  for no gain, because there is no blocking work to isolate. A pure Reactor
  or Proactor is the better fit.
- **The workload is CPU-bound rather than I/O-bound**, for example numeric
  computation with no waiting on external resources. Half-Sync/Half-Async is
  aimed at hiding blocking I/O and blocking library calls behind a queue, not
  at parallelizing CPU work. A plain thread pool or a data-parallel pattern
  fits CPU-bound work better, because there is no async demultiplexing side
  to build.
- **Connection count is low and known**, for example an internal service with
  a handful of long-lived peer connections. Thread-per-connection is simpler
  to write and reason about here, and the queueing layer buys nothing when
  there are only a few connections to demultiplex in the first place.
- **The system cannot tolerate the added latency of crossing the queue**, for
  example a hard-real-time control loop where every extra context switch
  threatens a deadline. A single-threaded, purely synchronous design, or a
  lock-free single-writer design, avoids the hand-off cost entirely.
- **The team cannot afford to own and tune two different concurrency models
  in one codebase.** Half-Sync/Half-Async is not free to maintain. Someone has
  to reason about a non-blocking demultiplexer, a bounded queue's
  backpressure policy, and a blocking thread pool's sizing, all at once. A
  smaller team on a smaller system is often better served by choosing one
  model, fully async with an async database driver, or fully synchronous with
  a large thread pool, and living with its ceiling.

## 5. Structure

The pattern names three participants, and the middle one is the part most
descriptions gloss over even though it carries the pattern's real guarantee.

- **Asynchronous Service Layer.** One thread, or a very small fixed number of
  threads, running an event-demultiplexing loop over a readiness notification
  mechanism. It performs no blocking operation of any kind beyond the wait
  inside the demultiplexer call itself. Its only job toward the rest of the
  system is to read or write the smallest useful unit of I/O and hand
  complete units of work to the Queueing Layer with a call that never blocks.
- **Queueing Layer.** A message queue, almost always bounded, that mediates
  between the two service layers. It owns the synchronization, the mutex or
  lock-free structure protecting the queue's internal state, so that neither
  service layer has to reason about the other's threading model directly.
  The queueing layer is also the natural place to apply a scheduling policy,
  first-in-first-out by default, but priority ordering, fairness across
  clients, or admission control are all decisions that belong here rather
  than in either service layer.
- **Synchronous Service Layer.** A pool of worker threads, sized well below
  the number of concurrent connections the async layer serves. Each worker
  pulls one unit of work from the queueing layer, and is free to perform any
  blocking call the work requires, a database round trip, a file read, a
  call into a synchronous library, without concern for stalling anything
  else, because every other worker and the async layer are on separate
  threads.

A fourth, often-implicit participant is the External Event Source, the
operating system's I/O readiness mechanism, that the Asynchronous Service
Layer is built on top of. It is not part of the pattern proper, it is the
substrate the async layer demultiplexes, but naming it separates the
pattern's own responsibility, moving work from async to sync, from the
platform's responsibility, telling the async layer when a socket is ready.

## 6. ASCII structure diagram

```
+---------------------------------------------------------------+
|                 External Event Source                         |
|      (OS readiness notification. epoll, kqueue, IOCP)          |
+------------------------------+----------------------------------+
                               |
                               v
+---------------------------------------------------------------+
|              Asynchronous Service Layer                        |
|   one demultiplexing thread, non-blocking calls only           |
|   - reads readiness events                                     |
|   - assembles a complete unit of work                          |
|   - hands it off with a non-blocking enqueue                   |
+------------------------------+----------------------------------+
                               |  non-blocking offer
                               v
+---------------------------------------------------------------+
|                    Queueing Layer                               |
|         bounded message queue, owns the synchronization         |
+------------------------------+----------------------------------+
                               |  blocking take
                +--------------+--------------+--------------+
                v              v              v              v
            worker 1       worker 2       worker 3       worker N
+---------------------------------------------------------------+
|              Synchronous Service Layer                          |
|   fixed thread pool, blocking calls are welcome here             |
|   - database queries, file I/O, legacy sync libraries            |
+---------------------------------------------------------------+
```

## 7. Dynamics

The interesting part of the dynamics is what each side is permitted to wait
on. The async layer is allowed to wait, but only inside the OS readiness call
itself, never on anything downstream of the queue. The sync layer is allowed
to wait wherever it wants, on the queue and on any blocking call inside a
worker's own logic, because a stalled worker never propagates its stall
anywhere else.

```
Client         Async layer        Queueing layer      Sync worker
  |                 |                    |                 |
  |--- bytes ------>|                    |                 |
  |                 | non-blocking read  |                 |
  |                 | assembles Request  |                 |
  |                 |--- offer(Request) ->|                 |
  |                 | (never blocks,      |                 |
  |                 |  drops on full)     |                 |
  |                 |                    |<-- take() -------|
  |                 |                    |    (blocks       |
  |                 |                    |     until ready) |
  |                 |                    |                 | blocking DB call
  |                 |                    |                 | ... work ...
  |<---------------------------------------- response ------|
  |                 |                    |                 |
```

A request arrives over the wire and the async layer's demultiplexer notices
the socket is readable. It performs one non-blocking read, and once enough
bytes have arrived to assemble a complete unit of work, typically a parsed
request object, it calls the queueing layer's non-blocking enqueue operation
and returns immediately to the demultiplexing loop to service the next ready
socket. It never waits to find out whether a worker picked the request up.

Independently, and on its own thread, a sync-layer worker sits blocked inside
the queue's take operation until work is available, pulls the next request,
and runs it start to finish as ordinary sequential code, including any
blocking calls the logic needs. When the worker finishes, it either writes
the response directly, if it has been handed the connection or a callback
that can do so safely, or it enqueues a result back through a second queue
that the async layer polls for outbound writes. Both designs exist in real
systems, and the choice is discussed under implementation variants.

## 8. Implementation variants

**Single queue, symmetric hand-off.** One bounded queue carries requests from
async to sync. The worker, after finishing, writes the response through the
same connection object it was handed, using a thread-safe write path. This is
the simplest variant to build and is common when each connection's socket
object already supports being written to from any thread, guarded by its own
lock.

**Two queues, request and response.** A second bounded queue carries
completed results from sync workers back to the async layer, which performs
the actual write as part of its own non-blocking loop. This keeps every
socket write inside the async layer, avoiding a separate lock per
connection, at the cost of an additional hand-off and a second queue to size
and monitor. Systems that already route all I/O, read and write, through one
event loop favor this shape.

**Bounded queue with an explicit drop or reject policy.** Because a blocking
offer on a full queue would reintroduce blocking into the async layer, a
faithful implementation must decide what happens when the queue is full. The
two defensible choices are dropping the new unit of work with a logged or
counted rejection, or immediately signaling backpressure to the client, for
example by closing the accepting side of a listening socket temporarily. An
unbounded queue avoids the decision but trades it for unbounded memory growth
under sustained overload, which is a worse failure mode.

**Fixed pool versus elastic pool.** The classic description uses a fixed-size
thread pool sized once at startup. A common production variant grows and
shrinks the pool within configured bounds based on queue depth, trading
implementation complexity for better utilization when load is bursty. An
elastic pool still needs a hard upper bound, or it degenerates back toward
thread-per-connection under sustained load.

**Layer-per-priority.** Some systems run more than one Synchronous Service
Layer, each with its own queue and its own worker pool, keyed by request
priority or request class, so that a flood of low-priority work cannot starve
high-priority work even though both pass through the same async front end.
Real-time CORBA's threading service, cited in the original pattern
literature, describes this as multiple lanes feeding from one demultiplexer.

**Language-idiomatic variants.** In languages with lightweight, runtime-
scheduled concurrency, goroutines in Go, green threads in Erlang, virtual
threads in Java 21 and later, the sync-layer thread pool can be a pool of
these lightweight tasks instead of OS threads, which changes the tuning
question from thread count to scheduler-level concurrency limits, but the
pattern's shape, an async demultiplexer handing work across a bounded queue
to workers that are free to block, is unchanged. This entry's Go example
below shows this variant directly, with goroutines standing in for the
classic thread pool.

## 9. Known production uses

**libuv, the async I/O library underneath Node.js and several other
runtimes.** libuv runs a single-threaded event loop for network I/O, and
delegates operations that have no portable non-blocking primitive, file
system calls, DNS lookups, and user-submitted work, to a shared thread pool
that the event loop enqueues work onto. The project's own design
documentation states that libuv "currently uses a global thread pool on which
all loops can queue work" for exactly these operation classes
([libuv Design Overview, docs.libuv.org](https://docs.libuv.org/en/v1.x/design.html),
verified 2026-08-02). The direction is the mirror image of the classic
network-server description, an async front end offloading blocking work
outward to a queue-fed pool, but the shape, one non-blocking demultiplexer
plus a bounded work queue plus a pool of workers that may block, is the same
pattern.

**Netty, the Java network application framework.** Netty's `ChannelPipeline`
lets a handler be attached with a dedicated `EventExecutorGroup`, separate
from the I/O-thread `EventLoopGroup`, specifically so that a handler
performing a lengthy operation does not stall the I/O thread. Netty's own API
documentation for `addLast(EventExecutorGroup, ChannelHandler...)` explains
the purpose as being able to run a business-logic handler's event methods "in
a different thread than an I/O thread so that the I/O thread is not blocked
by a time-consuming task"
([Netty 4.1 ChannelPipeline Javadoc, netty.io](https://netty.io/4.1/api/io/netty/channel/ChannelPipeline.html),
verified 2026-08-02). The I/O `EventLoopGroup` is the Asynchronous Service
Layer, the handler's `EventExecutorGroup` is the Synchronous Service Layer,
and the internal task queue each executor group services is the Queueing
Layer.

**The Linux kernel's interrupt handling.** Every hardware interrupt handler
in the Linux kernel runs in a restricted top half that must return quickly
because interrupts are disabled while it runs, and defers the bulk of the
work to a bottom half, a softirq, tasklet, or workqueue, that runs later with
interrupts enabled. The kernel's own hacking documentation states that the
top-half handler "has to be fast", typically only acknowledging the
interrupt and marking a software interrupt for later execution before it
exits, and that the deferred mechanism runs afterward, where, in the
document's own words, "much of the real interrupt handling work is done"
([Linux Kernel Hacking Guide, kernel.org](https://www.kernel.org/doc/html/latest/kernel-hacking/hacking.html),
verified 2026-08-02). This is the pattern at the operating system's own core.
the interrupt handler is a strictly non-blocking async layer, the
softirq or workqueue mechanism is the queueing layer, and the deferred
processing context is the synchronous half free to do real work, including
work that can sleep, in the workqueue case.

**Apache Tomcat's NIO connector.** Tomcat's HTTP connector configuration
exposes a non-blocking poller, tuned by settings such as `pollerThreadPriority`
and `selectorTimeout`, alongside a separate executor whose thread-pool
settings, `maxThreads` and `minSpareThreads`, govern the threads that actually
process requests. The documentation notes that if a shared executor is not
specified for a connector, "the connector will use a private, internal
executor to provide the thread pool"
([Apache Tomcat 9 HTTP Connector configuration reference](https://tomcat.apache.org/tomcat-9.0-doc/config/http.html),
verified 2026-08-02). The poller is the Asynchronous Service Layer performing
non-blocking `select` over client sockets, and the executor's thread pool is
the Synchronous Service Layer that runs servlet code, which is free to call
blocking JDBC drivers and file I/O without affecting the poller.

**The ADAPTIVE Communication Environment, ACE.** The pattern's own authors
built and shipped it inside ACE, the C++ networking framework from which the
original PLoP paper's examples are drawn, and the pattern description itself
names BSD Unix networking, where interrupt-driven, non-blocking protocol
processing hands packets to blockable, schedulable kernel threads for the
rest of the network stack's work, as the pattern's original motivating
example, per the paper title and abstract listed on the publication's own
index page
([Half-Sync/Half-Async publication entry, dre.vanderbilt.edu](https://www.dre.vanderbilt.edu/~schmidt/patterns-ace.html),
verified 2026-08-02).

## 10. Consequences

The costs and benefits below are drawn from general practice with this
pattern rather than from a single sourced study, and are presented as
engineering judgement.

**Positive.**

- Business logic in the Synchronous Service Layer is written as plain,
  linear, blocking code, which is easier to write correctly, easier to test
  with ordinary unit tests, and easier for a new engineer to read than an
  equivalent callback chain or state machine.
- The Asynchronous Service Layer stays small, simple, and free of blocking
  calls, which keeps the demultiplexer efficient and its behavior predictable
  under high connection counts, because it is doing exactly one job.
- A slow or misbehaving unit of work in one sync-layer worker cannot stall
  the async layer or any other worker, because the only thing they share is a
  queue, and the queue's own synchronization is the single well-tested piece
  of shared-state code in the whole design.
- The queueing layer is a natural point to add scheduling policy, priority
  ordering, admission control, metrics, or rate limiting, without touching
  either service layer's own code.
- Sizing the sync-layer pool becomes an isolated, empirically tunable
  parameter, separate from how many connections the async layer can hold
  open, which lets the two scale independently.

**Negative.**

- Every unit of work pays an extra hand-off, a queue push and pop plus a
  thread wake-up, that a single-threaded, fully async pipeline does not pay,
  adding latency that is small but not zero.
- The system now has two concurrency models to reason about at once, and a
  bug that appears only under a particular interleaving of the two sides is
  harder to reproduce than a bug confined to one model.
- A wrongly sized worker pool becomes a second bottleneck behind the
  connection-accepting front end, and the two must be tuned together, not
  independently, because a pool too small starves the queue while the async
  layer keeps accepting more work than the sync side can drain.
- The queueing layer's backpressure policy has to be an explicit design
  decision, not a default, because an unbounded queue and a blocking-on-full
  bounded queue both silently reintroduce a failure mode the pattern exists
  to avoid.
- Moving a result back across the sync-to-async boundary, when the response
  write must happen on the async layer, adds a second queue and a second
  synchronization point, which is easy to omit by accident and then discover
  under load as a correctness bug rather than a performance one.

## 11. Failure modes and misuse

The observed symptoms below are the visible surface a reader would actually
notice in production. The causes and fixes are drawn from field experience
with this pattern rather than from a single sourced incident report.

**Symptom.** The event loop occasionally freezes for tens or hundreds of
milliseconds under otherwise normal load, visible as a spike in every
connection's latency at once, not only one connection's.
**Cause.** A call inside the Asynchronous Service Layer that the author
believed was non-blocking is not, in practice, a DNS lookup made from inside
an event-handler callback, a lock shared with a sync-layer worker acquired
without a timeout, or a queue offer implemented with a blocking put instead
of a non-blocking offer when the queue is full.
**Fix.** Audit every call reachable from the async layer's event-handling
path for a blocking primitive, add a timeout or a non-blocking variant
wherever one exists, and change the queue's full-queue behavior to reject
rather than block. A code-level guard, such as forbidding any call to a
blocking API from the thread that owns the event loop, catches this class of
regression before it reaches production.

**Symptom.** Memory usage climbs steadily under sustained load and the
process eventually is killed by the operating system's out-of-memory
handling, even though CPU usage on the sync-layer workers looks reasonable.
**Cause.** The queueing layer is unbounded, or bounded so large that it is
effectively unbounded for the traffic the system sees, so a sync-layer pool
that cannot keep pace with the async layer's ingestion rate lets the queue
grow without limit instead of applying backpressure.
**Fix.** Bound the queue to a size that reflects the sync layer's real
throughput, decide and implement an explicit policy for what happens on a
full queue, reject, drop with a metric, or briefly stop accepting new
connections, and alert on queue depth as a leading indicator well before
memory pressure appears.

**Symptom.** Throughput plateaus and then degrades as more sync-layer worker
threads are added, the opposite of the intended effect.
**Cause.** The sync-layer workers share a mutable resource, a connection
pool, a cache, or a piece of application state, guarded by a single lock, so
adding threads increases contention on that lock faster than it increases
useful parallel work. This is a misuse of the pattern rather than a defect in
it, because Half-Sync/Half-Async only isolates the async layer from blocking,
it does nothing to remove contention that the business logic itself
introduces.
**Fix.** Profile for lock contention specifically, not only for CPU
utilization, and either shard the contended resource per worker, size the
underlying resource pool, for example a database connection pool, to match
the worker count, or reduce the time each worker holds the lock for.

**Symptom.** Responses occasionally never arrive for a client whose request
was clearly accepted and logged as processed by a sync-layer worker.
**Cause.** The system uses the two-queue variant, and the response queue from
sync back to async is unbounded or not drained promptly, or the connection
the response is destined for has since closed and the async layer silently
drops the orphaned result instead of logging it, so a real completed unit of
work disappears with no trace.
**Fix.** Treat the response path with the same rigor as the request path, a
bounded queue, an explicit policy for a closed destination, and a metric or
log line for every dropped result, so a silent loss becomes an observable
event instead of an unexplained client-visible failure.

**Symptom.** The system behaves correctly under load testing with uniform
requests but falls over when one class of request is disproportionately
represented in production traffic.
**Cause.** All request classes share one queue and one worker pool, so a
burst of one expensive request type, for example a report generation
endpoint that takes seconds, occupies enough workers to starve cheap,
latency-sensitive requests that arrive at the same time, because the queue
enforces no ordering by class or cost.
**Fix.** Split into multiple queueing-layer and sync-layer pairs by request
class or priority, the layer-per-priority variant described above, so an
expensive class cannot exhaust the workers a cheap class depends on.

## 12. Trade-off matrix

| Force | Half-Sync/Half-Async | Pure Reactor, all non-blocking | Thread-per-connection | Leader/Followers |
|---|---|---|---|---|
| Blocking library calls in business logic | Freely allowed, isolated in sync layer | Forbidden, forces async rewrites of every downstream call | Freely allowed, no isolation needed | Freely allowed while a follower holds the current unit of work |
| Peak concurrent connections per host | High, bounded mainly by memory for queued work, not by threads | Highest, limited mainly by file descriptors | Lowest, one OS thread per connection caps it early | High, similar to Half-Sync/Half-Async, without a separate queue thread hand-off |
| Latency added by the design itself | One queue hand-off per unit of work | None beyond the event loop's own scheduling | None, but scheduler contention grows with thread count | Lower than Half-Sync/Half-Async, no separate queueing thread, but a role hand-off still occurs |
| Isolation of a slow request from others | Strong, a stalled worker cannot stall the async layer or other workers | Weak, one blocking call anywhere stalls the whole loop | Strong, each connection has its own thread | Strong, similar to Half-Sync/Half-Async |
| Code style for business logic | Linear, blocking, easy to read | Callback or coroutine-driven, harder to read linearly | Linear, blocking, easy to read | Linear, blocking, easy to read |
| Operational tuning surface | Two independent knobs, connection concurrency and pool size, plus a queue policy | One knob, the event loop's own concurrency, usually fixed | One implicit knob, the OS thread limit, hard to tune deliberately | Two knobs similar to Half-Sync/Half-Async, plus the leader hand-off protocol |
| Implementation complexity | Moderate to high, two concurrency models plus a queue | Moderate, one model, but every call site must stay non-blocking forever | Low, one model, the simplest to build correctly at small scale | High, avoids the extra queue but the leader-election hand-off is subtle |

## 13. Related and incompatible patterns

**Reactor.** A Reactor is the most common way to build the Asynchronous
Service Layer's demultiplexing loop. The two patterns are frequently used
together, Reactor inside the async half, Half-Sync/Half-Async describing the
system-level split around it, and it is a common mistake to treat mentioning
one as having described the other, since Reactor says nothing about what
happens after an event is dispatched, and Half-Sync/Half-Async says nothing
about how readiness events are detected.

**Proactor.** Where Reactor notifies a handler that an operation is ready to
be performed without blocking, Proactor lets the operating system perform the
I/O itself and notifies a handler when the operation has already completed.
A Proactor-based async layer, common on platforms with true asynchronous I/O
completion, such as Windows I/O Completion Ports, still benefits from a
Half-Sync/Half-Async split if the completion handler needs to run business
logic that blocks, because the completion callback itself must stay as
non-blocking as a Reactor's event handler would.

**Leader/Followers.** This pattern is often positioned as an alternative to
Half-Sync/Half-Async for the same problem, a pool of threads sharing one
event source, where one thread at a time takes the leader role of waiting on
the event source directly, and hands leadership to a follower once it picks
up a unit of work, rather than handing the work across a separate queue.
Leader/Followers avoids the queue's extra hand-off and the memory allocation
a queued message requires, at the cost of a subtler protocol for passing
leadership safely, and it is a closer fit when the cost of that extra queue
hop genuinely matters.

**Active Object.** Active Object gives each object its own thread and a
private queue of method-invocation requests, decoupling a caller from the
thread that actually executes a call. A Synchronous Service Layer built from
a set of Active Objects, one per resource type, is a common way to combine
the two patterns, letting Half-Sync/Half-Async's queueing layer feed
requests into per-resource Active Objects that serialize access to a shared
resource without an explicit lock.

**Monitor Object.** Where a sync-layer worker needs to coordinate with other
workers around a shared piece of state, a Monitor Object gives that state its
own synchronization boundary and condition variables, which composes cleanly
underneath a Synchronous Service Layer without touching the async side at
all.

**Thread Pool.** The Synchronous Service Layer is, structurally, a Thread
Pool with one specific input, the Queueing Layer, and one specific
constraint, its workers are expected to block. Half-Sync/Half-Async narrows
Thread Pool to this particular role inside a larger, two-halved system.

**Producer-Consumer.** The relationship between the Asynchronous Service
Layer and the Synchronous Service Layer, mediated by the Queueing Layer, is
an instance of Producer-Consumer at the architectural level, with the async
layer as the sole producer and the worker pool as a set of competing
consumers.

**Tension with strict actor designs.** A strict actor-model design, where
every piece of state is owned by exactly one actor and all communication is
asynchronous message passing with no shared mutable state anywhere, sits in
tension with Half-Sync/Half-Async's sync-layer worker pool, because that pool
typically shares a common view of downstream resources such as a connection
pool. The two can be combined, but doing so usually means treating the whole
Synchronous Service Layer as a single actor-equivalent boundary rather than
letting individual workers touch shared state directly.

## 14. Refactoring path in and out

**Introducing the pattern into a thread-per-connection system.** Start by
identifying the accept-and-read path that currently blocks one thread per
connection, and replace it with a single non-blocking demultiplexer over the
same set of sockets, without changing anything about how requests are
processed yet. Introduce a bounded queue between the new demultiplexer and
the existing per-connection processing logic, and change that logic to run
inside a fixed-size worker pool that pulls from the queue instead of running
inline on a per-connection thread. Verify, under load, that the connection
count the system can hold open rises while the per-request processing
latency stays flat, since that is the signal the split is actually working
rather than only having moved the bottleneck. Only after the split is stable
should the worker pool size be tuned down from one thread per prior
connection toward the smaller number the blocking work actually needs.

**Introducing the pattern into a fully non-blocking, callback-driven
system.** Identify the specific callback paths that call, or would like to
call, a blocking API, and extract exactly that logic into a function with no
callback-chain dependencies, an ordinary blocking function signature. Add a
bounded queue and a worker pool sized to the blocking work's real
concurrency needs, route only those specific requests through the queue, and
leave every already-non-blocking path untouched. This partial adoption,
async for what is already async, sync-behind-a-queue only for the parts that
need to block, is the far more common real-world refactor than converting an
entire system at once, and it is visible in the Netty and libuv production
examples above, where only the specific handlers or operation types that need
to block are routed to the worker pool.

**Removing the pattern once it stops earning its place.** If profiling shows
the queueing layer's hand-off cost dominates request latency and the
sync-layer workers are never actually blocked, meaning every downstream call
already has a genuine async equivalent, the pattern has outlived its reason
for existing. The removal path is to migrate the sync-layer logic, one
request class at a time, to call the async equivalents directly from the
async layer, shrinking the worker pool's responsibility class by class until
the queue carries nothing and can be deleted along with the now-empty
Synchronous Service Layer. Removing the queue before every caller has an
async replacement reintroduces blocking calls directly into the event loop,
which is a regression back to the failure mode named in dimension 11, so this
migration is done request class by request class, verified after each step,
never in one cut.

## 15. Testing and verification

Testing the Asynchronous Service Layer in isolation is straightforward
because its contract is narrow. Feed it synthetic readiness events or raw
bytes and assert that it produces the correct complete units of work on the
queue, and separately assert, with a static analysis rule or a runtime
assertion that fails fast, that no call on its thread ever blocks longer than
a strict, small time budget. A test that injects a slow fake socket and
confirms the demultiplexer's other connections are still serviced promptly
directly verifies the pattern's central promise.

Testing the Synchronous Service Layer is easier than testing the whole
system, because each worker's logic is ordinary linear code and can be unit
tested exactly as if the queue did not exist, calling the worker's processing
function directly with a constructed request and asserting on the result. The
blocking calls inside worker logic, database drivers, file I/O, are the usual
targets for dependency injection and test doubles, no different from testing
any other synchronous code.

The queueing layer itself deserves its own focused tests independent of
either service layer, exercised with property-based tests that push and pop
under concurrent access from multiple simulated producers and consumers,
checking that no unit of work is ever lost or duplicated, that the bounded
capacity is honestly enforced, and that a full-queue offer never blocks the
caller. A queue that occasionally blocks a non-blocking offer under a
particular race condition is the single most dangerous bug this pattern can
harbor, because it silently reintroduces the exact failure this whole
architecture exists to prevent.

End-to-end verification needs load and chaos testing, not only unit tests.
Drive the system with a mix of fast and deliberately slow synthetic requests
and confirm that a slow request's latency does not leak into a fast
request's latency, that queue depth under sustained overload behaves as the
chosen backpressure policy predicts, and that killing or hanging one
sync-layer worker does not stall the async layer or the other workers.
Fault injection, deliberately blocking one worker thread indefinitely, is a
direct, repeatable way to confirm the isolation the pattern claims to
provide, rather than assuming it from the design alone.

## 16. Observability signals

The signals below reflect operational practice rather than a formal
specification, so treat the specific thresholds as starting points to tune
per system.

Queue depth over time is the single most informative signal in the whole
system, because it is the leading indicator for every failure mode named in
dimension 11 before any of them become visible to a client. A healthy system
shows queue depth oscillating near zero, briefly rising under load bursts and
draining promptly once the burst passes. A steadily rising queue depth is the
earliest sign that the sync-layer pool cannot keep pace with the async
layer's ingestion rate, well before memory pressure or latency complaints
appear.

Per-worker utilization, the fraction of time each sync-layer thread spends
actively processing versus blocked waiting on the queue, distinguishes an
under-provisioned pool, uniformly high utilization with a growing queue, from
a contention problem, moderate utilization with high wall-clock time per
request, which points at lock contention or a slow downstream dependency
rather than at pool size.

Time spent in the queue per unit of work, measured from enqueue to dequeue,
is the direct measurement of the hand-off latency the pattern trades away for
isolation, and it should be tracked as its own metric distinct from
processing time, because the two point at different fixes, queue time points
at pool sizing or backpressure policy, processing time points at the
business logic itself.

A count of rejected or dropped units of work, from a full-queue policy, is a
signal that must never be silent. Every drop is either a lost client request
or a deliberate backpressure decision, and either way it needs to be visible
as a metric with an alert threshold, not discovered later by correlating
client-reported errors against server logs after the fact.

Finally, the async layer's own loop iteration time, how long each pass
through the event-demultiplexing loop takes, is the direct measurement of
dimension 11's first failure mode, an accidental blocking call inside the
async layer. This metric is worth alerting on with a strict threshold,
because any sustained rise here means the async layer's core promise,
staying non-blocking, has already been broken somewhere in the code.

## 17. Security and privacy implications

Most of this dimension is engineering judgement rather than a sourced claim,
because the pattern's security surface follows from its shape rather than
from a documented vulnerability class attached to the pattern by name.

The bounded queue between the two layers is the pattern's primary
denial-of-service consideration. An attacker who can generate many cheap
requests that each occupy a sync-layer worker for a disproportionately long
time, for example by triggering an expensive database query or a slow
downstream call on every request, can exhaust the worker pool and fill the
queue even though each individual request looks legitimate. Rate limiting
and request-cost-aware admission control belong at, or ahead of, the
queueing layer specifically because that is the single narrowest point
through which every unit of work must pass.

Because the async layer and the sync layer run as separate threads sharing
process memory, any request data placed on the queue is visible, in memory,
to every worker thread in the pool, not only the one that eventually
processes it, for the lifetime the request sits in the queue. Systems that
carry sensitive fields, credentials, personally identifiable data, through
the queue should minimize how long that data sits there and should avoid
logging queue contents wholesale, since a queue dump captured for debugging
can inadvertently capture in-flight sensitive payloads from unrelated
requests.

Because sync-layer workers commonly share a downstream connection pool, a
database connection pool or a shared client to another service, a request
handled by one worker can, if the worker logic has a bug, leave state behind
on a shared connection, for example an uncommitted transaction or a
connection left in a non-default session mode, that then leaks into a
different client's request handled later by the same worker on the same
connection. This is not unique to Half-Sync/Half-Async, but the pattern's
pooled-worker shape makes this class of cross-request leakage a concrete risk
to check for specifically in code review of the sync-layer worker logic.

The async layer's non-blocking demultiplexer is, by itself, a smaller attack
surface than a thread-per-connection accept loop, because it does not
allocate an OS thread per connection attempt, which somewhat raises the bar
for a pure connection-exhaustion attack aimed at thread or memory limits, but
it does not remove the need for connection-level limits and timeouts, which
remain the primary defense against a slow-connection or slow-request style
denial-of-service attempt regardless of which concurrency pattern is in use.

## Code examples

Three languages chosen for how differently each one expresses the two
threading models the pattern joins. Java shows the pattern with an explicit
`ExecutorService` worker pool and a `BlockingQueue`, close to the original
description's own vocabulary. Go shows the pattern built from channels and
goroutines, where the queueing layer is a native language primitive rather
than a library class. Rust shows the pattern with `std::sync::mpsc` channels
and a shared receiver guarded by a mutex, standing in for how a language
without a built-in multi-consumer channel type still expresses the same
three-layer shape using only its standard library.

### Java

```java
import java.util.concurrent.*;

record Request(int id, String payload) {}
record Result(int id, String output) {}

final class QueueingLayer {
    private final BlockingQueue<Request> inbox = new ArrayBlockingQueue<>(64);

    boolean offer(Request request) {
        return inbox.offer(request);
    }

    Request take() throws InterruptedException {
        return inbox.take();
    }
}

final class AsyncServiceLayer implements Runnable {
    private final QueueingLayer queue;
    private final BlockingQueue<Request> arrivals;
    private volatile boolean running = true;

    AsyncServiceLayer(QueueingLayer queue, BlockingQueue<Request> arrivals) {
        this.queue = queue;
        this.arrivals = arrivals;
    }

    void stop() {
        running = false;
    }

    public void run() {
        while (running) {
            Request request = arrivals.poll();
            if (request == null) {
                continue;
            }
            if (!queue.offer(request)) {
                System.out.println("backpressure: dropped request " + request.id());
            }
        }
    }
}

final class SyncServiceLayer {
    private final ExecutorService workers;
    private final int poolSize;
    private final QueueingLayer queue;
    private final BlockingQueue<Result> results;

    SyncServiceLayer(int poolSize, QueueingLayer queue, BlockingQueue<Result> results) {
        this.poolSize = poolSize;
        this.workers = Executors.newFixedThreadPool(poolSize);
        this.queue = queue;
        this.results = results;
    }

    void start() {
        for (int i = 0; i < poolSize; i++) {
            workers.submit(this::loop);
        }
    }

    private void loop() {
        try {
            while (!Thread.currentThread().isInterrupted()) {
                Request request = queue.take();
                Thread.sleep(1);
                results.put(new Result(request.id(), request.payload().toUpperCase()));
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    void shutdown() {
        workers.shutdownNow();
    }
}

public final class HalfSyncHalfAsyncDemo {
    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<Request> arrivals = new LinkedBlockingQueue<>();
        BlockingQueue<Result> results = new LinkedBlockingQueue<>();
        QueueingLayer queue = new QueueingLayer();

        AsyncServiceLayer async = new AsyncServiceLayer(queue, arrivals);
        Thread asyncThread = new Thread(async, "async-demux");
        asyncThread.start();

        SyncServiceLayer sync = new SyncServiceLayer(4, queue, results);
        sync.start();

        for (int i = 0; i < 8; i++) {
            arrivals.put(new Request(i, "req-" + i));
        }

        for (int i = 0; i < 8; i++) {
            Result result = results.take();
            System.out.println(result.id() + " -> " + result.output());
        }

        async.stop();
        sync.shutdown();
        asyncThread.join(1000);
    }
}
```

### Go

```go
package main

import (
	"fmt"
	"sync"
)

type Request struct {
	ID      int
	Payload string
}

type Result struct {
	ID     int
	Output string
}

func newQueue(capacity int) chan Request {
	return make(chan Request, capacity)
}

func asyncServiceLayer(arrivals <-chan Request, queue chan<- Request, done <-chan struct{}) {
	for {
		select {
		case r, ok := <-arrivals:
			if !ok {
				close(queue)
				return
			}
			select {
			case queue <- r:
			default:
				fmt.Println("backpressure: dropped request", r.ID)
			}
		case <-done:
			close(queue)
			return
		}
	}
}

func syncServiceLayer(id int, queue <-chan Request, results chan<- Result, wg *sync.WaitGroup) {
	defer wg.Done()
	for r := range queue {
		results <- Result{ID: r.ID, Output: r.Payload + "-done"}
	}
	_ = id
}

func main() {
	const workers = 4
	arrivals := make(chan Request)
	queue := newQueue(16)
	results := make(chan Result, 16)
	done := make(chan struct{})

	go asyncServiceLayer(arrivals, queue, done)

	var wg sync.WaitGroup
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go syncServiceLayer(i, queue, results, &wg)
	}

	go func() {
		for i := 0; i < 8; i++ {
			arrivals <- Request{ID: i, Payload: fmt.Sprintf("req-%d", i)}
		}
		close(arrivals)
	}()

	go func() {
		wg.Wait()
		close(results)
	}()

	for r := range results {
		fmt.Println(r.ID, r.Output)
	}
}
```

### Rust

```rust
use std::sync::mpsc::{self, Receiver, Sender};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;

struct Request {
    id: u32,
    payload: String,
}

struct Outcome {
    id: u32,
    output: String,
}

fn async_service_layer(arrivals: Receiver<Request>, queue: Sender<Request>) {
    for request in arrivals {
        if queue.send(request).is_err() {
            break;
        }
    }
}

fn main() {
    let (arrival_tx, arrival_rx) = mpsc::channel::<Request>();
    let (queue_tx, queue_rx) = mpsc::channel::<Request>();
    let (outcome_tx, outcome_rx) = mpsc::channel::<Outcome>();

    let async_thread = thread::spawn(move || async_service_layer(arrival_rx, queue_tx));

    let queue_rx = Arc::new(Mutex::new(queue_rx));
    let mut workers = Vec::new();
    for id in 0..4u32 {
        let queue_rx = Arc::clone(&queue_rx);
        let outcome_tx = outcome_tx.clone();
        workers.push(thread::spawn(move || loop {
            let received = {
                let rx = queue_rx.lock().unwrap();
                rx.recv()
            };
            match received {
                Ok(request) => {
                    thread::sleep(Duration::from_millis(1));
                    let output = format!("{}-worker{}", request.payload, id);
                    if outcome_tx.send(Outcome { id: request.id, output }).is_err() {
                        break;
                    }
                }
                Err(_) => break,
            }
        }));
    }
    drop(outcome_tx);

    for i in 0..8u32 {
        arrival_tx
            .send(Request { id: i, payload: format!("req-{}", i) })
            .unwrap();
    }
    drop(arrival_tx);

    for _ in 0..8 {
        let outcome = outcome_rx.recv().unwrap();
        println!("{} -> {}", outcome.id, outcome.output);
    }

    async_thread.join().unwrap();
    for worker in workers {
        let _ = worker.join();
    }
}
```

## 18. References

1. Douglas C. Schmidt and Chuck Cranor, "Half-Sync/Half-Async - An
   Architectural Pattern for Efficient and Well-Structured Concurrent I/O",
   Proceedings of the Second Pattern Languages of Programs conference,
   Monticello, Illinois, September 6-8, 1995, collected in James O. Coplien,
   John Vlissides, and Norman Kerth (editors), *Pattern Languages of Program
   Design 2*, Addison-Wesley, 1996. Publication record at
   [dre.vanderbilt.edu/~schmidt/patterns-ace.html](https://www.dre.vanderbilt.edu/~schmidt/patterns-ace.html),
   verified 2026-08-02.
2. Douglas C. Schmidt, Michael Stal, Hans Rohnert, and Frank Buschmann,
   *Pattern-Oriented Software Architecture, Volume 2. Patterns for Concurrent
   and Networked Objects*, John Wiley and Sons, 2000, ISBN 978-0-471-60695-6.
   Publisher and authorship confirmed via
   [en.wikipedia.org/wiki/Pattern-Oriented_Software_Architecture](https://en.wikipedia.org/wiki/Pattern-Oriented_Software_Architecture),
   verified 2026-08-02.
3. libuv project, "Design overview", section on the shared thread pool used
   for file system operations, DNS functions, and user-submitted work.
   [docs.libuv.org/en/v1.x/design.html](https://docs.libuv.org/en/v1.x/design.html),
   verified 2026-08-02.
4. Netty project, `ChannelPipeline` API documentation, entry for
   `addLast(EventExecutorGroup, ChannelHandler...)`, describing running a
   handler off the I/O thread to avoid blocking it.
   [netty.io/4.1/api/io/netty/channel/ChannelPipeline.html](https://netty.io/4.1/api/io/netty/channel/ChannelPipeline.html),
   verified 2026-08-02.
5. The Linux Kernel Documentation project, "A guide to the Kernel Development
   Process, Unreliable Guide To Hacking The Linux Kernel", section describing
   top-half interrupt handlers and deferred bottom-half processing.
   [kernel.org/doc/html/latest/kernel-hacking/hacking.html](https://www.kernel.org/doc/html/latest/kernel-hacking/hacking.html),
   verified 2026-08-02.
6. Apache Software Foundation, "Apache Tomcat 9 Configuration Reference, The
   HTTP Connector", entries for `pollerThreadPriority`, `selectorTimeout`,
   `maxThreads`, and the internal executor thread pool.
   [tomcat.apache.org/tomcat-9.0-doc/config/http.html](https://tomcat.apache.org/tomcat-9.0-doc/config/http.html),
   verified 2026-08-02.
