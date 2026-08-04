---
name: Synchronous I/O
slug: synchronous-i-o
family: 18-anti-patterns
category: Anti-Pattern
aliases: [Blocking I/O, Blocking Call Anti-Pattern, Synchronous Blocking Call, Sync-Over-Async]
first_described: "No single formal catalog names this anti-pattern. The earliest widely cited technical account of the failure mode at scale is Dan Kegel, The C10k problem, 1999, describing why a thread blocked on I/O per connection stops scaling long before CPU capacity is exhausted (see dimension 1 for the full lineage)"
maturity: established
related: [chatty-i-o, busy-database, bulkhead, circuit-breaker, asynchronous-request-reply, queue-based-load-leveling, n+1-query]
incompatible_with: []
verified: 2026-08-02
---

# Synchronous I/O

## 1. Name, aliases, and lineage

Synchronous I/O, as an anti-pattern name, describes the practice of issuing a
blocking network, disk, or database call from inside a context that a system
depends on to keep serving other concurrent work, and then sitting idle on
that thread, that goroutine, or that process until the operating system wakes
it back up. The word synchronous here is doing double duty and readers new to
the term often confuse the two senses, so it earns a sentence of its own. In
one sense, every I/O call in every language is synchronous with respect to
the statement that issued it, in that the next line of code genuinely does
not run until the call returns, whether the call is `read()`, `await fetch()`,
or a callback firing later. In the anti-pattern sense used in this entry,
synchronous means specifically that the CALLING THREAD is blocked at the
operating system level, unable to do anything else, for the full duration of
the operation, rather than being released to do other useful work while a
separate mechanism, an event loop, a callback, a future, or another thread,
waits on the result instead.

No single paper, book, or catalog coined Synchronous I/O the way the Gang of
Four coined Factory Method. It is a rediscovered failure mode, described
independently by operating systems researchers, web server authors, language
runtime designers, and resilience engineers, each naming a piece of the same
underlying shape. The earliest widely cited technical account of the failure
mode at the scale that made it a named problem worth solving is Dan Kegel's
essay "The C10k problem" (1999), which opens by asking why web servers of the
era could not handle ten thousand simultaneous clients and traces the answer
directly to the thread-per-blocking-connection model. Kegel shows that on a
32 bit machine with roughly 1 GB of user-accessible virtual memory and a
typical 2 MB per-thread stack, a server built as one blocking thread per
connection runs out of virtual memory at around 512 threads, long before it
runs out of CPU, and argues that nonblocking I/O with event notification, or
true asynchronous I/O, is the structural fix rather than tuning the thread
count (Dan Kegel, "The C10k problem", http://www.kegel.com/c10k.html, verified
2026-08-02).

The blocking versus non-blocking distinction that Kegel's essay builds on is
older still, reaching back into Unix system call semantics. The `O_NONBLOCK`
flag on a file descriptor and the `select()` system call both predate the web
by a decade or more, and they exist precisely because programmers already
needed a way to ask "is this ready yet" without committing a thread to wait
for the answer. What changed between the 1980s and the 2000s was not the
existence of the choice, it was the cost of getting the choice wrong at
internet scale, and that cost is what turned blocking I/O from a neutral
implementation detail into a named anti-pattern that shows up in code review
checklists, framework documentation, and postmortems.

The vocabulary has since split by community. Server and network engineers
usually say "blocking I/O" or "blocking call". Concurrency and language
runtime documentation, especially around `async`/`await`, more often says
"sync-over-async" for the specific sub-case of wrapping an asynchronous API
in a blocking wait so that a synchronous caller can pretend the asynchronous
API does not exist. Both terms describe the same structural defect. A thread
that a system relies on for concurrency is voluntarily taken out of service
for the duration of an I/O operation it did not need to occupy that thread
for.

## 2. Problem and context

Picture a request-handling process that serves many clients from a bounded
number of execution contexts, whether that bound is a fixed thread pool, a
single event loop thread, or a limited set of goroutines multiplexed onto a
handful of OS threads. Every one of those execution contexts is a shared,
finite resource. The process was sized, deliberately or by accident, on the
assumption that each unit of work occupies its context for a short, mostly
CPU-bound amount of time before releasing it back to the pool for the next
piece of work.

Now one of those units of work needs to talk to something slow, a spinning
disk, a database over the network, a downstream HTTP service, a DNS
resolver, or a legacy driver with no asynchronous API. The straightforward
way to write that call is the way every introductory tutorial teaches it,
call the function, block, get the result back, keep going. `readFileSync` in
Node.js. `requests.get()` in Python without `asyncio`. A JDBC `Statement`
call in an ordinary Java servlet thread. A `std::net::TcpStream::read` on a
thread with no partner reading concurrently. Each of these is entirely
correct from the point of view of the single request being served. The code
reads top to bottom, errors propagate as ordinary exceptions or return
values, and there is no callback pyramid, no future to chain, no `await` to
remember. That is precisely why the pattern is so persistent. The code that
exhibits it is the code that is easiest to write and easiest to read in
isolation.

The problem only becomes visible at the level of the shared resource. While
that one call is blocked, the execution context it occupies is unavailable
to every other unit of work that also needed it, and the operating system's
own scheduler is not going to hand that thread to anyone else, because as far
as the kernel is concerned the thread asked to wait and is waiting. If the
disk is briefly slow, if the database connection is momentarily saturated, or
if the downstream service has degraded, the number of blocked execution
contexts rises in lockstep with the number of concurrent requests hitting the
slow dependency, and once that number reaches the size of the pool, every
NEW request, including requests that have nothing to do with the slow
dependency, queues behind the backlog rather than being served. A slowdown in
one narrow code path becomes a stall of the entire process.

This is the context in which Synchronous I/O earns the anti-pattern label. It
is not that blocking calls are wrong in an absolute sense, a single-threaded
script reading a configuration file once at startup has no concurrency budget
to protect. It is that a piece of code was written as if it owned its
execution context privately, when in production that context is shared,
finite, and load-bearing for unrelated work.

## 3. Forces

**Simplicity of the call site against safety of the shared resource.** A
blocking call reads as one line and composes naturally with ordinary
control flow, loops, conditionals, exception handling, return values. The
asynchronous alternative, whether callbacks, promises, `async`/`await`, or
explicit thread hand-off, adds a second axis of control flow that has to be
learned, reasoned about, and tested. The anti-pattern exists because the
simpler-looking option is, locally, also the more dangerous one, and the two
do not announce themselves as being in tension until load arrives.

**Latency of the dependency against the size of the pool.** How many
execution contexts a blocking call can safely tie up is a direct function of
how long the call takes and how many can run at once before the pool is
exhausted. A call that reliably returns in one millisecond against a pool of
two hundred threads is a non-issue. The same call, made against a dependency
that occasionally takes thirty seconds under load, against that same pool of
two hundred threads, needs only seven concurrent slow requests before every
thread is occupied. This is a Little's Law relationship in disguise. The
number of contexts consumed at any moment is, on average, the arrival rate of
requests multiplied by how long each one holds a context, and a blocking call
directly sets that holding time.

**Throughput of the fast path against the tail behavior of the slow path.**
Most requests to most systems complete quickly. The forces here favor
optimizing for the median case with a straightforward blocking call, because
that is where the bulk of the work lives and where developer time is best
spent. The anti-pattern's damage is concentrated entirely in the tail, the
p99 and p99.9 requests, or the requests that arrive during a dependency
outage, where the blocking model converts a localized slowdown into a
process-wide one.

**Portability of code against the concurrency model of the runtime.** A
blocking database driver, a blocking file API, and a blocking third-party
SDK are the lowest common denominator across languages. They exist
everywhere and require no runtime-specific integration. Adopting a
non-blocking equivalent, or wrapping a blocking one in a thread offload,
ties the code to a specific runtime's concurrency primitives, whether that
is libuv, `asyncio`'s event loop, or a particular executor service. Some
teams accept the portability cost for the safety win, some accept the
safety risk to keep the code simple to move between environments.

**Operational cost of over-provisioning against the cost of an outage.**
One common and partially effective mitigation is simply to size the thread
pool or the process count generously enough that the blocking calls rarely
exhaust it. This trades memory and operational complexity, more threads
mean more stack memory, more context-switching overhead, and a harder
capacity-planning problem, against the risk of a cascading stall. This is
judgment, not a sourced fact. over-provisioning buys headroom, it does not
remove the anti-pattern, and it tends to fail exactly when the traffic
pattern changes enough to invalidate the sizing assumption that produced the
original headroom.

## 4. Applicability and non-applicability

Synchronous I/O, as a call SHAPE, is applicable, meaning it is a reasonable
default choice rather than a defect, in these situations.

- A single-shot script or command-line tool with no concurrent request
  load to protect, where the process exists to do exactly one thing and
  exit.
- A one-time startup or initialization path, executed once before a server
  begins accepting concurrent traffic, such as reading a configuration file
  or running a database migration before the listener socket opens.
- A dedicated worker process pulled from a queue, where the process
  handles exactly one unit of work at a time by design and blocking on that
  one unit's I/O has no other concurrent work to starve.
- Any environment whose concurrency model already makes a "blocking style"
  call cheap because the runtime multiplexes many logical units of work
  onto a small number of OS threads underneath. Go is the clearest current
  example. a goroutine that calls `net.Dial` or reads from a `net.Conn`
  reads as an ordinary blocking call in the source, but the Go runtime
  parks the goroutine and frees the underlying OS thread to run other
  goroutines while the operation is outstanding, because "Goroutines are
  multiplexed onto multiple OS threads so if one should block, such as
  while waiting for I/O, others continue to run" (The Go Authors, "Effective
  Go", Goroutines section, https://go.dev/doc/effective_go, verified
  2026-08-02). Erlang and Elixir's BEAM scheduler, and languages built on
  virtual threads or green threads more broadly, share this property.
- A batch or offline pipeline whose throughput target is measured in
  records per hour rather than requests per second, where a small number of
  long-running worker processes each doing blocking I/O in sequence is
  simpler to reason about than an event-driven pipeline and the concurrency
  ceiling is a deliberate, sized choice rather than an accident.

Synchronous I/O is NOT applicable, meaning a blocking call in this context is
the anti-pattern rather than a reasonable default, in these situations.

- Inside a single-threaded event loop runtime, such as Node.js or a
  Python `asyncio` application, where one blocked call stalls every other
  piece of concurrent work in the entire process, not merely the caller.
  Node's own documentation is explicit that the synchronous variants of the
  file system, crypto, compression, and child-process APIs should not be
  used in a server, precisely because "if the file you access is in a
  distributed file system like NFS, access times can vary widely" and that
  variability now stalls the whole event loop, not one request (Node.js
  documentation, "Blocking the Event Loop. Node.js Core Modules",
  https://nodejs.org/en/learn/asynchronous-work/dont-block-the-event-loop,
  verified 2026-08-02).
- Inside a request-handling thread drawn from a small, fixed-size thread
  pool shared across many concurrent requests, such as a Java servlet
  container's worker pool or a .NET thread pool, where a blocking call
  ties up that shared resource for its full duration and every other queued
  request pays the cost.
- Anywhere the calling code is itself inside an asynchronous function or
  coroutine and reaches for a blocking wait to fake synchronous behavior
  around an asynchronous API, the sync-over-async sub-case, which risks
  deadlock in addition to throughput loss. Microsoft's own C# guidance
  states plainly that "synchronous blocking on asynchronous operations can
  lead to deadlocks and should be avoided whenever possible. The preferred
  solution is to use async/await throughout your call stack" (Microsoft,
  "Asynchronous programming scenarios - C#", Microsoft Learn,
  https://learn.microsoft.com/en-us/dotnet/csharp/asynchronous-programming/async-scenarios,
  verified 2026-08-02).
- Any path that is, or can plausibly become, on the critical path of a
  large number of concurrent user-facing requests, even if today's traffic
  is low. The anti-pattern's cost scales with concurrency, so code that
  starts safe at low traffic can become the outage cause at higher traffic
  without a single line changing.
- A CPU-bound calculation mistakenly treated the same way as I/O-bound
  work. Offloading CPU-bound work to a background thread inside an
  `async` method solves a different problem, keeping a UI or event loop
  responsive during computation, and is not itself an instance of, or a fix
  for, the I/O-blocking anti-pattern. Conflating the two leads to the wrong
  remedy being applied, for example spawning a thread pool sized for I/O
  concurrency to run CPU-bound work that actually needs to be sized to the
  number of physical cores instead.

## 5. Structure

The anti-pattern has three participants, and the failure lives entirely in
how the second one is used, never in the third one by itself.

**The shared execution context.** The finite resource a system depends on to
serve concurrent work, a single event loop thread, a fixed-size worker
thread pool, or a bounded number of OS threads that a language runtime
multiplexes many logical units of work onto. Its size is either fixed by
configuration or fixed by the number of physical threads the operating
system will schedule.

**The blocking call.** Any operation whose contract is "the calling thread
does not proceed past this statement until the operating system reports the
result", issued against a resource whose latency the caller does not fully
control, disk, network socket, database connection, DNS resolver, or a
third-party SDK built on any of these. The call itself is not the
anti-pattern, it is a correct, well-defined primitive.

**The concurrent workload.** Every OTHER unit of work, request, or task that
also depends on the shared execution context being available. This is the
participant whose existence turns a blocking call from a local implementation
detail into a shared-resource hazard, and it is also the participant most
often missing from a developer's mental model at the moment the blocking
call is written, because a single request handled in isolation during local
testing never exposes contention with anyone else.

```
      +----------------------------+
      |   Shared Execution Pool    |
      |  (event loop thread, or    |
      |   N worker threads)        |
      +----------------------------+
        |        |        |    ...
        v        v        v
   +--------+ +--------+ +--------+
   |Request | |Request | |Request |
   |Handler | |Handler | |Handler |
   |   A    | |   B    | |   C    |
   +--------+ +--------+ +--------+
        |
        |  A calls a BLOCKING operation
        v
   +--------------------------+
   |  Slow dependency         |
   |  (disk, DB, network)     |
   +--------------------------+

   While A's thread waits for the dependency, that thread cannot
   serve B or C. If the pool has only a few threads, B and C queue
   behind A even though B and C need nothing from the slow dependency.
```

## 6. ASCII structure diagram

```
   Pool size = 3 threads.  4 requests arrive.  Dependency is slow.

   t=0    [T1: Req A -> BLOCKED on disk read]
          [T2: Req B -> BLOCKED on disk read]
          [T3: Req C -> BLOCKED on disk read]
          [Req D -------- WAITING, no free thread --------]

   t=50ms [T1: Req A -> still blocked]
          [T2: Req B -> still blocked]
          [T3: Req C -> still blocked]
          [Req D -------- still waiting --------]

   t=100ms[T1: Req A -> DONE, thread freed]
          [T1: Req D -> now starts, only now]

   Request D's total latency is its own service time PLUS the full
   duration that every thread ahead of it was blocked, even though D
   never touched the slow dependency itself.
```

## 7. Dynamics

At runtime the anti-pattern plays out as a queueing problem, and the
sequence below traces one representative incident from a healthy state
through the point where the pool saturates.

```
Time -->

Healthy state.
  Client --request--> [Free thread] --blocking call--> [fast dependency]
                                    <--result, ~5ms-----
  [Thread returned to pool immediately]

Dependency slows down.
  Client A --request--> [Thread 1] --blocking call--> [slow dependency]
                                    (thread 1 waits, no other work possible)
  Client B --request--> [Thread 2] --blocking call--> [slow dependency]
                                    (thread 2 waits)
  Client C --request--> [Thread 3] --blocking call--> [slow dependency]
                                    (thread 3 waits, pool now has 0 free)

Pool exhausted.
  Client D --request--> [no free thread] --queues--
  Client E --request--> [no free thread] --queues--
  Health-check probe --> [no free thread] --queues, times out--

Cascading effect.
  Load balancer marks the instance unhealthy (failed health check)
  Traffic reroutes to remaining instances
  Remaining instances receive the same slow-dependency traffic
  Remaining instances repeat the same exhaustion sequence
```

The critical transition is the moment the last free thread is consumed. Up
to that point, the system degrades gracefully. individual requests to the
slow dependency get slower, but unrelated requests are unaffected. Past that
point, the system degrades catastrophically. EVERY request, including
requests that never touch the slow dependency, and often including the
health-check endpoint itself, now queues behind the backlog. This is why
outages caused by this anti-pattern so often present as a sudden, total loss
of a service instance rather than a gradual slowdown proportional to the
underlying dependency's own degradation. The pool exhaustion point is a
threshold, not a slope.

## 8. Implementation variants

**Direct synchronous call, no mitigation.** The plain case. a request
handler calls a blocking function with no thread offload, no timeout, and no
isolation from other work. This is the default outcome of using a
straightforward blocking API in a shared-thread server framework without
deliberately reaching for the asynchronous equivalent. It is the variant
every other item on this list exists to move away from.

**Sync-over-async wrapping.** Code that already has access to an
asynchronous API chooses instead to block on it synchronously, typically by
calling `.Result`, `.Wait()`, `.get()` on a future, or an equivalent blocking
accessor, so that a synchronous caller does not have to change its own
signature. .NET's own guidance names this pattern directly and ranks the
available blocking techniques from most to least risky, while stating
plainly that "blocking the current thread as a means to wait synchronously
for a Task item to complete can result in deadlocks and blocked context
threads" (Microsoft, "Asynchronous programming scenarios - C#", Microsoft
Learn,
https://learn.microsoft.com/en-us/dotnet/csharp/asynchronous-programming/async-scenarios,
verified 2026-08-02). This variant is distinctive because it can fail two
different ways, ordinary throughput loss from occupying a thread, and, when
the asynchronous continuation is scheduled to resume on the very thread that
is now blocked waiting for it, an outright deadlock.

**Thread-per-connection with an uncapped pool.** Instead of a fixed pool, the
server spawns a new OS thread per incoming connection with no upper bound.
This avoids queueing delay under moderate load, at the cost of unbounded
memory growth and scheduler thrashing under high load, which is precisely
the failure Kegel's C10k essay documents. on a 32-bit process the thread
stacks alone exhaust addressable virtual memory around 512 threads (Dan
Kegel, "The C10k problem", http://www.kegel.com/c10k.html, verified
2026-08-02). Even on 64-bit systems with no addressing ceiling, an unbounded
thread count still exhausts scheduler capacity and per-thread kernel
resources well before it exhausts physical memory.

**Blocking call issued inside a single-threaded event loop.** The most
severe variant, because the shared execution context has exactly one member.
Node.js explicitly enumerates the synchronous APIs it recommends against for
this reason, including the synchronous variants of `crypto`, `zlib`,
filesystem, and `child_process` functions, and separately warns that even
ordinary `JSON.parse` and `JSON.stringify` on a sufficiently large payload
become an event-loop-blocking operation despite not being an I/O call at all
(Node.js documentation, "Blocking the Event Loop. Node.js Core Modules",
https://nodejs.org/en/learn/asynchronous-work/dont-block-the-event-loop,
verified 2026-08-02).

**Blocking call issued inside an async coroutine without offloading.** In
Python's `asyncio`, calling a blocking function such as `time.sleep` or a
synchronous database driver directly from inside a coroutine occupies the
one OS thread the event loop runs on, and the official documentation states
the consequence directly. "if a function performs a CPU-intensive
calculation for 1 second, all concurrent asyncio Tasks and IO operations
would be delayed by 1 second" (Python documentation, "Developing with
asyncio", https://docs.python.org/3/library/asyncio-dev.html, verified
2026-08-02). The documented remedy is `loop.run_in_executor()`, which hands
the blocking call to a separate thread, interpreter, or process so the event
loop's own thread stays free.

**Isolated, bounded blocking with a dedicated pool.** A deliberate variant
rather than an accident. the blocking call is still blocking, but it runs on
a thread pool dedicated to that one dependency, sized and monitored
independently of the pool serving other work. Netflix's Hystrix library
built exactly this as its default execution model, isolating each
dependency's calls "on separate threads. This isolates them from the calling
thread (Tomcat thread pool) so that the caller may 'walk away' from a
dependency call that is taking too long" (Netflix, Hystrix Wiki, "How it
Works", https://github.com/Netflix/Hystrix/wiki/How-it-Works, verified
2026-08-02). This variant does not eliminate the underlying blocking
behavior, it contains its blast radius so that one slow dependency cannot
consume threads that unrelated requests also need.

## 9. Known production uses

**Node.js's core module design and documentation.** Node.js ships its file
system, cryptography, compression, and child-process modules with both a
synchronous and an asynchronous variant of nearly every function, and the
project's own performance guide names the synchronous variants as the ones a
server author "should not use", walking through concrete cases like NFS
latency and large-payload `JSON.parse` cost (Node.js documentation, "Blocking
the Event Loop. Node.js Core Modules",
https://nodejs.org/en/learn/asynchronous-work/dont-block-the-event-loop,
verified 2026-08-02). The entire single-threaded event loop architecture
that Node.js is known for is a direct, load-bearing response to this
anti-pattern. it makes the cost of a blocking call visible and severe on
purpose, and its ecosystem of asynchronous-first APIs exists because of it.

**Python's `asyncio` executor offload mechanism.** The Python standard
library documents `loop.run_in_executor()` as the sanctioned way to run
blocking code from inside an `asyncio` application without stalling the
event loop, explicitly framing the alternative, calling blocking code
directly, as delaying "all concurrent asyncio Tasks and IO operations"
(Python documentation, "Developing with asyncio",
https://docs.python.org/3/library/asyncio-dev.html, verified 2026-08-02).
Every production Python service that mixes `asyncio` with a synchronous
database driver, a synchronous HTTP client, or any legacy blocking library
relies on this mechanism specifically to avoid the anti-pattern.

**Netflix Hystrix's thread-pool isolation.** Hystrix, the resilience library
Netflix built and operated at scale for its microservice architecture, uses
per-dependency thread pools as its default isolation strategy specifically
because, as the project's own wiki states, "most network access is
performed synchronously" and a caller needs the ability to "walk away" from
a dependency that has become slow without that dependency's threads
consuming resources shared with the rest of the application (Netflix,
Hystrix Wiki, "How it Works", https://github.com/Netflix/Hystrix/wiki/How-it-Works,
verified 2026-08-02). Hystrix is now in maintenance mode with Netflix
recommending newer libraries for new work, but its design vocabulary,
bulkhead isolation around blocking calls, remains the reference architecture
the industry still names when discussing this exact problem.

**HikariCP's connection pool sizing guidance.** HikariCP, one of the most
widely deployed JDBC connection pool implementations in the Java ecosystem,
publishes an explicit sizing formula derived from PostgreSQL's own
observation that pool size should track `((core_count * 2) + effective_spindle_count)`
rather than the number of concurrent application threads, and states plainly
that once a workload is I/O bound, "less blocking... therefore fewer threads
will perform better than more threads" (Brett Wooldridge, "About Pool
Sizing", HikariCP wiki,
https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing, verified
2026-08-02). This is a named, widely cited production artifact of the same
underlying force. a blocking connection pool's useful concurrency ceiling is
bounded by the dependency's own capacity, not by however many application
threads happen to want a connection.

**.NET's async/await guidance and `ConfigureAwait` discipline.** Microsoft's
own documentation for the Task-based asynchronous pattern names the
sync-over-async sub-case directly, ranks the available ways to block on a
`Task` from most to least preferred, and states that the deadlock risk
specifically arises in scenarios involving a synchronization context, especially UI applications and legacy ASP.NET request contexts (Microsoft,
"Asynchronous programming scenarios - C#", Microsoft Learn,
https://learn.microsoft.com/en-us/dotnet/csharp/asynchronous-programming/async-scenarios,
verified 2026-08-02). The widespread .NET convention of appending
`ConfigureAwait(false)` to library-internal awaits exists as a direct,
production-tested countermeasure to the deadlock variant of this
anti-pattern.

## 10. Consequences

Positive, when the applicability conditions in dimension 4 genuinely hold.

- The call site is trivially readable, one statement, ordinary control
  flow, no additional abstraction to learn.
- Error handling is ordinary exception or return-value handling, with no
  separate error channel to keep in sync with a success channel.
- Stack traces at the point of failure show the real call chain, because
  the operation never left the calling thread's own execution context.
- No callback registration, future composition, or executor management
  code is needed, which removes an entire class of bugs, a forgotten
  `.catch()`, an unhandled rejection, a callback fired twice, that only
  exist in the asynchronous alternative.

Negative, when the applicability conditions do not hold, which is the
anti-pattern's actual operating condition in a shared-resource server.

- Throughput collapses non-linearly once concurrent slow requests approach
  the size of the shared execution pool, converting a partial dependency
  slowdown into a total service stall, as traced in dimension 7.
- The failure is load-dependent and often invisible in development and
  in low-traffic staging environments, which means it is discovered in
  production, frequently during exactly the traffic spike or dependency
  degradation event a system most needs to survive.
- Health checks and readiness probes queue behind the same backlog as
  ordinary requests when they share the same pool, so an orchestrator can
  mark an instance unhealthy and remove it from rotation for a reason
  that has nothing to do with the instance's own resource limits, which
  then concentrates the same load onto fewer remaining instances and can
  cascade the outage across a whole fleet.
- Blocking a thread that is also the continuation target for an
  asynchronous operation can deadlock outright rather than merely degrade,
  the sync-over-async case, which is a qualitatively worse failure than
  slow throughput because it does not resolve on its own once load drops.
- Capacity planning becomes coupled to a dependency's tail latency rather
  than to the service's own CPU or memory budget, so a team can provision
  generously for their own code's resource needs and still be surprised by
  an outage rooted entirely in someone else's slow API.

## 11. Failure modes and misuse

**Symptom.** A service's request latency and error rate spike sharply and
simultaneously across every endpoint, including endpoints that never call
the slow dependency, and the spike correlates with a slowdown in one
specific downstream call. **Cause.** The pool of execution contexts serving
all endpoints is shared, and enough concurrent requests to the slow
dependency have occupied every context in the pool, so unrelated requests
queue behind them. **Fix.** Isolate the dependency's blocking calls onto a
pool dedicated to that dependency, sized and monitored independently, the
Hystrix bulkhead pattern, so exhaustion in one dependency's pool cannot
starve requests that do not use it.

**Symptom.** An `async` method never returns, the request appears to hang
indefinitely, and there is no exception, timeout, or error in the logs, only
silence. **Cause.** Code inside the asynchronous call chain blocked
synchronously, `.Result`, `.Wait()`, `Task.Wait()`, or an equivalent, on a
`Task` whose continuation was scheduled to resume on the very thread that is
now blocked waiting for it, so neither side can proceed, the sync-over-async
deadlock Microsoft's own guidance warns about directly (Microsoft,
"Asynchronous programming scenarios - C#", Microsoft Learn,
https://learn.microsoft.com/en-us/dotnet/csharp/asynchronous-programming/async-scenarios,
verified 2026-08-02). **Fix.** Replace the blocking wait with `await`
throughout the call stack, and where a genuine synchronous boundary is
unavoidable, prefer `GetAwaiter().GetResult()` over `.Result` or `.Wait()`
to avoid the extra `AggregateException` wrapping, or use
`ConfigureAwait(false)` on library-internal awaits to remove the
synchronization-context dependency that makes the deadlock possible in the
first place.

**Symptom.** A Node.js process's request handling stalls in short, sharp
bursts that correlate with specific endpoints, and CPU usage during the
stall is either near zero, waiting on disk, or near one full core pegged,
CPU-bound work mistaken for I/O. **Cause.** A synchronous file system call,
a synchronous crypto operation, or a large `JSON.parse`/`JSON.stringify` ran
on the single event loop thread, and because Node.js is single-threaded for
JavaScript execution, that one call stalls every other request the process
is handling, not merely the request that issued it. **Fix.** Replace
synchronous filesystem, crypto, and compression calls with their
asynchronous equivalents, and for large JSON payloads, use a streaming
parser or partition the work across `setImmediate` callbacks so no single
turn of the event loop consumes an unbounded amount of time (Node.js
documentation, "Blocking the Event Loop. Node.js Core Modules",
https://nodejs.org/en/learn/asynchronous-work/dont-block-the-event-loop,
verified 2026-08-02).

**Symptom.** Adding more application server instances, or raising the
thread pool size, does not raise overall throughput past a certain point,
and beyond that point additional threads or instances make average latency
WORSE rather than better. **Cause.** The bottleneck has moved to the
downstream dependency's own concurrency ceiling, most often a database
connection pool, and every additional application thread is now competing
for a fixed number of connections, adding context-switching and queueing
overhead on both sides without adding real parallelism. HikariCP's sizing
guidance names this directly. past the point where the workload is I/O
bound rather than CPU bound, "fewer threads will perform better than more
threads" (Brett Wooldridge, "About Pool Sizing", HikariCP wiki,
https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing, verified
2026-08-02). **Fix.** Size the connection pool from the dependency's own
capacity outward, using a formula grounded in core count and disk
parallelism rather than in application-side concurrency, and treat any
further application thread growth past that point as adding queueing delay,
not throughput.

**Symptom.** A batch job or fan-out operation that calls the same slow
downstream service N times takes roughly N times as long as calling it once,
even though the downstream service itself has spare capacity and the calls
are logically independent. **Cause.** The calls are issued one after another
synchronously in a single thread of control, so their latencies sum rather
than overlap, an algorithmic instance of the anti-pattern that has nothing
to do with thread pool exhaustion and everything to do with failing to
express independence in the code, the same failure mode this repository's
Chatty I/O entry documents from the round-trip-count angle rather than the
blocking-thread angle. **Fix.** Fan the independent calls out concurrently,
across goroutines, `asyncio.gather()`, `Promise.all()`, or a bounded worker
pool sized to the downstream service's real capacity, so their latencies
overlap instead of accumulating.

## 12. Trade-off matrix

The comparison below is scoped to a service handling many concurrent
requests from a shared, finite pool of execution contexts, which is the
context in which the anti-pattern actually causes harm, see dimension 4 for
where the comparison does not apply.

| Concern | Synchronous I/O (this anti-pattern) | Bulkhead isolation (dedicated thread pool per dependency) | Non-blocking / asynchronous I/O | Concurrency-cheap runtime (Go goroutines, Erlang processes) |
|---|---|---|---|---|
| Call-site readability | Highest, ordinary top-to-bottom code | Same as synchronous, isolation is configured, not coded per call | Lower, callbacks, futures, or `await` chains to reason about | Highest, reads exactly like blocking code |
| Blast radius of a slow dependency | Unbounded, can exhaust the shared pool and stall unrelated work | Bounded to that dependency's own pool | Bounded, one slow call occupies only its own callback state, not a thread | Bounded, the runtime schedules around the blocked unit automatically |
| Deadlock risk | Present when combined with sync-over-async inside an async call stack | Same risk as plain synchronous within its isolated pool, but contained | Generally low, though chaining futures incorrectly can still deadlock in some runtimes | Low, the scheduler, not the developer, owns thread hand-off |
| Operational cost to adopt | None, this is the default in most languages | Moderate, per-dependency pool sizing and monitoring | High, rewrites call sites and error handling across the codebase | Low to moderate, mainly a language or runtime choice made once |
| Effectiveness against tail-latency cascades | Poor, this is the failure mode being described | Good, contains the cascade to one dependency | Good, no thread is ever held hostage by a slow call | Good, blocking-style code gets the safety of async without the syntax |
| Best fit | Single-shot scripts, startup code, dedicated single-task workers | Multi-dependency services that must keep working when one dependency degrades | High-concurrency single-threaded or thread-lean runtimes | New systems where the language choice is still open |

## 13. Related and incompatible patterns

**Chatty I/O.** A close relative that is frequently mistaken for the same
problem. Chatty I/O is about the NUMBER of round trips a piece of code makes
to a dependency, too many small calls instead of one larger one, and its
damage comes mostly from summed network latency even when every call is
non-blocking. Synchronous I/O is about the CONCURRENCY MODEL of each call, a
single call occupying a shared thread it did not need to occupy. Code can
have either defect without the other. a single blocking call per request is
Synchronous I/O without Chatty I/O, and a hundred small non-blocking calls
issued concurrently is Chatty I/O without Synchronous I/O. The two often
appear together, because a codebase that reaches for blocking calls by
default also tends to issue them in a naive per-item loop rather than
batching.

**Busy Database.** A downstream consequence rather than a cause. when
Synchronous I/O is combined with an uncapped or overly generous thread
pool, as in the thread-per-connection variant in dimension 8, the
application can push far more concurrent queries at the database than it
would if blocking calls were properly bounded, turning the database itself
into the bottleneck described in that entry.

**Bulkhead.** The direct architectural fix demonstrated by Hystrix in
dimension 8 and 9. isolate blocking calls to a resource behind their own
dedicated pool so exhaustion in one pool cannot spread to others. A system
that has fully adopted bulkhead isolation around every blocking dependency
has, in effect, contained this anti-pattern without necessarily eliminating
the blocking calls themselves.

**Circuit Breaker.** A companion pattern rather than a replacement.
bulkhead isolation limits how many threads a slow dependency can consume at
once, while a circuit breaker stops sending it requests at all once it is
confirmed unhealthy, which reduces the number of blocked threads directly
rather than merely bounding them.

**Asynchronous Request-Reply.** The architectural-level analogue of moving
away from Synchronous I/O. instead of a client blocking on a synchronous
call while a long-running operation completes, the operation is dispatched
and the client polls or is notified later, which removes the requirement
that any single thread stay occupied for the operation's full duration at
all.

**Queue-Based Load Leveling.** A different, complementary mitigation. rather
than changing how a single call blocks, this pattern absorbs bursts of
demand in a queue so the number of concurrent blocking calls issued to a
downstream dependency at any moment stays within a sustainable bound, even
if each individual call remains synchronous.

**N+1 Query.** A frequent co-occurrence in ORM-heavy code. a loop issues one
synchronous query per item instead of one batched query for all items, which
combines the algorithmic serial-latency failure mode from dimension 11 with
the specific, well-documented database access-pattern problem that entry
covers.

Nothing in this repository is formally incompatible with Synchronous I/O in
the sense the frontmatter field captures, because the anti-pattern is a
property of a call site's execution model rather than a structural pattern
that conflicts with another structural pattern. The closest thing to an
incompatibility is conceptual. a system that has adopted a fully
non-blocking, single-threaded event-loop architecture, Node.js being the
clearest example, treats any remaining synchronous call as a defect by
definition, because that architecture's entire performance model depends on
no call ever occupying the one thread for longer than a few milliseconds.

## 14. Refactoring path in and out

**Introducing it, why a team would do this on purpose.** Starting a new,
low-traffic service, or a script, with straightforward blocking calls is a
legitimate choice when the applicability conditions in dimension 4 hold. The
"introduction" here is really a decision to defer the asynchronous rewrite
until load or dependency latency makes it necessary, and the honest
refactoring step is to record that decision, ideally as a load threshold or
a specific dependency's latency SLA that would trigger the follow-up work,
rather than as an unstated assumption that nobody revisits until an outage
forces the question.

**Removing it, the general path.** The refactor almost always proceeds in
the same order regardless of language, because the risk is concentrated in
the same place, the shared execution context, not the individual call.

1. **Measure first.** Identify which blocking call sites are actually on a
   shared, load-bearing execution path, using the observability signals in
   dimension 16, rather than converting every blocking call in the codebase
   indiscriminately. A blocking call in a start-up path or a single-task
   worker is not the target.
2. **Bound the blast radius before changing the call shape.** Introduce
   bulkhead isolation, a dedicated thread pool per dependency, sized from
   that dependency's own known capacity, as demonstrated by Hystrix in
   dimension 9. This is the cheapest step and it converts a total-outage
   risk into a partial-degradation risk immediately, without touching call
   site code beyond configuration.
3. **Add a timeout to every remaining blocking call**, if one does not
   already exist. A blocking call with no timeout can occupy its execution
   context for as long as the dependency takes to fail, which in a network
   partition can be effectively forever, a bounded timeout caps the
   worst-case occupancy time even before the call itself is made
   non-blocking.
4. **Convert the call site to the runtime's non-blocking equivalent.** In
   Python `asyncio`, this means either replacing the blocking library with
   an async-native one, or, where no async-native equivalent exists,
   wrapping the existing call in `loop.run_in_executor()` as the standard
   library documents (Python documentation, "Developing with asyncio",
   https://docs.python.org/3/library/asyncio-dev.html, verified 2026-08-02).
   In Node.js, this means swapping the `Sync` suffix function for its
   asynchronous counterpart. In C#, this means threading `await` up through
   the call stack rather than blocking on a `Task` partway through it, per
   Microsoft's own guidance (Microsoft, "Asynchronous programming scenarios
   - C#", Microsoft Learn,
   https://learn.microsoft.com/en-us/dotnet/csharp/asynchronous-programming/async-scenarios,
   verified 2026-08-02).
5. **Re-verify concurrency behavior, not correctness alone.** A converted
   call site can be functionally correct, return the same result, and still
   fail to solve the underlying problem if, for example, the conversion
   introduces its own sync-over-async wrapper somewhere upstream. The
   testing techniques in dimension 15 are what catch this.
6. **Retire the bulkhead sizing once load-tested, or keep it.** Once the
   call is genuinely non-blocking, the dedicated thread pool from step 2 may
   no longer be strictly necessary for that dependency, but many production
   systems keep the isolation anyway as a defense against a future
   regression reintroducing a blocking call at that call site.

**Refactoring family cross-reference.** This path is, at the code level, an
instance of Extract Method followed by a change in the extracted method's
calling convention from a direct return to a callback, future, or `await`
expression, the same mechanical shape this repository's refactoring family
documents for converting a synchronous API into an asynchronous one, applied
specifically to I/O rather than to arbitrary computation.

## 15. Testing and verification

Correctness testing of the call itself is what makes this anti-pattern easy
to miss. unit tests that mock the dependency, or that run against a fast
local database with no contention, will pass identically whether the call
is blocking or non-blocking, because correctness and concurrency behavior
are orthogonal properties. A test suite proves nothing about this
anti-pattern unless it specifically exercises concurrency and dependency
latency together.

**Load testing with an artificially slowed dependency.** The single most
direct verification technique. introduce a deliberate, configurable delay
into the dependency, a test double, a proxy, or a feature flag in the real
dependency's test environment, and drive concurrent load at the service
while measuring whether unrelated request latency and error rate stay flat.
If unrelated requests degrade in step with the injected delay, the shared
execution pool is not properly isolated. This is the same technique used to
validate the demonstration code in the code examples section of this entry,
where a fixed-size thread or executor pool is deliberately starved
by blocking work to make the exhaustion effect observable and measurable
rather than theoretical.

**Saturation testing of the pool itself.** Rather than testing one request
at a time, drive exactly as many concurrent slow requests as the shared pool
has capacity, plus a small excess, and confirm the excess requests queue and
eventually succeed rather than time out or crash the process. This
distinguishes a system that degrades gracefully at its capacity boundary
from one that fails abruptly past it.

**Deadlock-specific testing for sync-over-async.** Where a codebase has any
call to `.Result`, `.Wait()`, `Task.Wait()`, or an equivalent blocking
accessor on a future inside a context that has a synchronization context, a
UI thread, or a legacy request context that captures one, a targeted test
should exercise that exact code path under the synchronization context it
runs under in production, not merely under a console test runner that has no
synchronization context and therefore cannot reproduce the deadlock at all.
This is the specific gap that makes the deadlock variant so often escape
unit testing. the test double for "run this async method" frequently omits
the very context capture that causes the production deadlock.

**Fault injection on the dependency's timeout behavior.** Test what happens
when the dependency accepts a connection but never responds, as distinct
from refusing the connection outright or responding with an error. A
connection accepted but never completed is exactly the case an
unconfigured or misconfigured timeout fails to bound, and it is a common
gap. many test suites exercise "the dependency returned an error" far more
thoroughly than "the dependency never returns at all".

**Test doubles that model latency, not only return values.** A mock or stub
that returns instantly, even one that returns the correct error for a
timeout scenario, cannot demonstrate whether the calling code's execution
context is actually held during the call. A test double for this specific
anti-pattern needs to model TIME, sleeping or otherwise holding the thread
for a configurable duration, which is exactly what the `blocking_call`
helper functions in the code examples for this entry do.

## 16. Observability signals

**Thread or worker pool active and queued counts, sampled continuously.** The
single highest-value signal. a pool whose active count sits at its
configured maximum for a sustained period, with a nonzero and growing queue
depth behind it, is the direct, real-time symptom of this anti-pattern in
progress, well before request latency alone would make the cause obvious.

**Per-call latency histograms broken down by dependency, not aggregated
across all outbound calls.** An aggregate p99 latency number can look
acceptable even while one specific dependency's calls are individually
taking seconds, because that dependency's calls may be a small fraction of
total call volume. Breaking latency down per dependency is what surfaces
which specific blocking call is the one consuming pool capacity.

**Thread state sampling, or its language-specific equivalent.** Periodic
thread dumps, or an `asyncio` event loop's task inspection, that reveal a
large number of threads or tasks all blocked in the same call, the same
file, or the same stack frame, is a direct, unambiguous fingerprint of this
anti-pattern, distinct from a generically slow or CPU-bound system where
thread state would be varied rather than clustered.

**Connection pool wait time and checkout time, kept as two separate
metrics.** HikariCP and most mature connection pool implementations expose
both how long a caller waited to acquire a connection and how long the
connection was held once acquired. a rising wait time alongside a flat or
rising hold time is the metric-level signature of pool exhaustion driven by
blocking calls holding connections longer than the pool was sized for.

**Health check and readiness probe latency, measured separately from
business request latency.** Because health checks frequently share the same
execution pool as ordinary requests, a health check that starts timing out
is often the earliest externally visible symptom of pool exhaustion, and it
is worth alerting on directly rather than only inferring pool exhaustion
from business-metric degradation after the fact.

**Correlated deploy and configuration change markers on the same timeline as
the above.** Because this anti-pattern is triggered by load and dependency
latency rather than by a code change alone, the actual code that introduced
a blocking call is frequently deployed and running safely for a long period
before a traffic increase or a dependency slowdown first exposes it,
so annotating dashboards with both deploy events and known dependency
incidents is necessary to distinguish "we shipped the bug today" from
"we shipped the bug months ago and today's traffic finally exposed it".

## 17. Security and privacy implications

Synchronous I/O has no direct data confidentiality or integrity implication
of its own. a blocking call and a non-blocking call carrying the same
payload expose the same data over the same transport with the same
encryption, if any. The implications are entirely on the availability side.

**Denial of service amplification.** Because a small number of slow or
stalled requests can exhaust an entire execution pool, as traced in
dimension 7, this anti-pattern turns an ordinary, low-volume attack, such as
opening connections and sending data slowly enough to keep a downstream call
pending without ever completing it, into a disproportionately effective
denial-of-service vector. A service properly isolated with bulkhead pools
and enforced timeouts degrades to reduced capacity under such an attack, a
service with unbounded, unisolated blocking calls can be taken fully offline
by a comparatively small number of slow, malicious connections, the same
resource-exhaustion mechanics documented generally for slow-request attacks
against thread-per-connection servers.

**Timeout absence as an availability control gap, not merely a performance
gap.** A blocking call with no timeout is, from a security posture
standpoint, an unbounded trust extension to whatever is on the other end of
that call. nothing in the calling code limits how long an unresponsive or
adversarial peer can hold a shared resource hostage. This is judgment, not a
sourced fact. teams that treat "add a timeout" as purely a performance
tuning task, rather than as a baseline availability control comparable to
input validation or authentication, tend to under-prioritize it relative to
its actual risk.

**No direct implication for data-in-transit or data-at-rest protections.**
Whether a database call is issued synchronously or asynchronously has no
bearing on whether that call uses TLS, whether credentials are stored
securely, or whether the query itself is parameterized against injection.
those are entirely separate concerns governed by other patterns and
practices in this repository, and this entry takes no position on them
beyond noting explicitly that fixing this anti-pattern does not fix, and
is not a substitute for fixing, any of those separate concerns.

## Code examples

The five examples below share one structure on purpose. a periodic
"heartbeat" or a set of independent concurrent tasks represents the OTHER
work a shared execution context needs to keep serving, and a stand-in
blocking operation represents the slow dependency. Each example shows the
anti-pattern's effect first, then the fix, in the same run, so the
difference is measured rather than asserted. Java is omitted from the
runnable set for this entry because no JDK was available in the environment
used to write it. the anti-pattern and its fix are identical in shape to the
C# example already provided, `Task.Run` and `await` in place of a blocking
call, and to the sync-over-async case documented in dimension 8 for that
language's own `Future.get()`.

TypeScript demonstrates the single-threaded event loop case directly.
`blockingWork` stands in for something like `fs.readFileSync` on a large
file, and a `setInterval` heartbeat is used to make the stall observable.

```typescript
function heartbeat(): ReturnType<typeof setInterval> {
  let ticks = 0;
  return setInterval(() => {
    ticks += 1;
    console.log(`heartbeat ${ticks} at ${Date.now()}`);
  }, 20);
}

function blockingWork(ms: number): void {
  const until = Date.now() + ms;
  while (Date.now() < until) {
    // stands in for fs.readFileSync or a synchronous database driver call
  }
}

async function nonBlockingWork(ms: number): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, ms));
}

async function main(): Promise<void> {
  console.log("--- synchronous call blocks the heartbeat ---");
  const hb1 = heartbeat();
  const start1 = Date.now();
  blockingWork(200);
  console.log(`blockingWork returned after ${Date.now() - start1}ms`);
  clearInterval(hb1);

  await new Promise((r) => setTimeout(r, 50));

  console.log("--- asynchronous call lets the heartbeat run ---");
  const hb2 = heartbeat();
  const start2 = Date.now();
  await nonBlockingWork(200);
  console.log(`nonBlockingWork returned after ${Date.now() - start2}ms`);
  clearInterval(hb2);
}

main();
```

Compiled with `npx tsc --target es2020 --module commonjs --strict` and run
with `node`. The output shows zero heartbeat ticks during the 200
millisecond blocking call and roughly nine ticks, at the expected 20
millisecond interval, during the equivalent-length non-blocking call, the
same effect Node.js's own documentation warns about for the real
synchronous file system and cryptography APIs.

Python demonstrates the `asyncio` executor-offload fix that the standard
library documents directly.

```python
import asyncio
import time


async def heartbeat(label: str) -> None:
    for tick in range(5):
        print(f"[{label}] heartbeat {tick} at {time.monotonic():.3f}")
        await asyncio.sleep(0.02)


def blocking_call(seconds: float) -> None:
    time.sleep(seconds)  # stands in for a blocking DB driver or synchronous file read


async def bad_handler() -> None:
    blocking_call(0.15)


async def good_handler() -> None:
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, blocking_call, 0.15)


async def main() -> None:
    print("--- calling blocking code directly stalls the event loop ---")
    await asyncio.gather(heartbeat("bad"), bad_handler())

    print("--- offloading to an executor keeps the loop alive ---")
    await asyncio.gather(heartbeat("good"), good_handler())


asyncio.run(main())
```

Run with `python3`. In the `bad` run, the heartbeat prints once, then a gap
of roughly 150 milliseconds appears before the next tick, matching
`blocking_call`'s duration exactly, because the coroutine holding that call
occupies the event loop's one OS thread the entire time. In the `good` run,
the heartbeat ticks continue on their normal 20 millisecond schedule because
`run_in_executor` moved the blocking call to a separate thread from the
default thread pool executor.

Go demonstrates the case where blocking-style syntax is not the anti-pattern
by itself, because goroutines make it cheap, and the actual defect is
issuing independent calls serially rather than concurrently.

```go
package main

import (
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"sync"
	"time"
)

func slowHandler(w http.ResponseWriter, r *http.Request) {
	time.Sleep(50 * time.Millisecond)
	fmt.Fprintln(w, "ok")
}

func fetchSync(url string) {
	resp, err := http.Get(url)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	io.Copy(io.Discard, resp.Body)
}

func main() {
	server := httptest.NewServer(http.HandlerFunc(slowHandler))
	defer server.Close()

	urls := []string{server.URL, server.URL, server.URL, server.URL}

	start := time.Now()
	for _, u := range urls {
		fetchSync(u)
	}
	fmt.Printf("serial synchronous calls: %v\n", time.Since(start))

	start = time.Now()
	var wg sync.WaitGroup
	for _, u := range urls {
		wg.Add(1)
		go func(url string) {
			defer wg.Done()
			fetchSync(url)
		}(u)
	}
	wg.Wait()
	fmt.Printf("concurrent goroutines: %v\n", time.Since(start))
}
```

Checked with `go vet` and run with `go run`. Each call to a fifty
millisecond test server is a genuine, ordinary blocking `http.Get`, exactly
as Effective Go describes, and no part of this example uses `async`,
`await`, or a callback. The serial loop takes roughly four times as long as
the concurrent version, because four fifty millisecond calls issued one
after another sum to roughly two hundred milliseconds, while four calls
issued as four goroutines overlap and finish in roughly one call's worth of
wall-clock time. The fix here is not to make the calls non-blocking, Go
already made that cheap, it is to stop expressing four independent
operations as a sequential loop.

Rust demonstrates the thread pool exhaustion mechanism directly, using only
the standard library, with a small worker pool and a large one processing
the same batch of purely synchronous, blocking work.

```rust
use std::sync::{mpsc, Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};

fn synchronous_blocking_call(id: u32) {
    // stands in for a blocking database driver call or a synchronous file read
    thread::sleep(Duration::from_millis(50));
    let _ = id;
}

fn run_pool(pool_size: usize, requests: u32) -> Duration {
    let (tx, rx) = mpsc::channel::<u32>();
    let rx = Arc::new(Mutex::new(rx));

    let start = Instant::now();
    let mut workers = Vec::new();
    for _ in 0..pool_size {
        let rx = Arc::clone(&rx);
        workers.push(thread::spawn(move || loop {
            let job = { rx.lock().unwrap().recv() };
            match job {
                Ok(id) => synchronous_blocking_call(id),
                Err(_) => break,
            }
        }));
    }

    for id in 0..requests {
        tx.send(id).unwrap();
    }
    drop(tx);

    for w in workers {
        w.join().unwrap();
    }
    start.elapsed()
}

fn main() {
    let small_pool = run_pool(2, 8);
    println!("pool of 2 threads, 8 blocking requests: {:?}", small_pool);

    let large_pool = run_pool(8, 8);
    println!("pool of 8 threads, 8 blocking requests: {:?}", large_pool);
}
```

Compiled with `rustc --edition 2021` and run directly. A pool of two worker
threads processing eight blocking requests, each holding its worker for
fifty milliseconds, takes roughly four times as long, close to two hundred
milliseconds, as a pool of eight workers processing the same eight requests
in parallel, close to fifty milliseconds, which is the queueing delay from
dimension 7 reproduced with nothing but `std::thread` and a channel. no
network, no async runtime, and no external crate.

Swift demonstrates the sync-over-async variant. wrapping a completion-handler
based asynchronous operation in a `DispatchSemaphore.wait()` so a caller can
treat it as synchronous, then showing the same throughput collapse under a
limited concurrency pool that the other examples show for genuine blocking
I/O.

```swift
import Foundation

func asyncOperation(id: Int, completion: @escaping (Int) -> Void) {
    DispatchQueue.global().asyncAfter(deadline: .now() + 0.05) {
        completion(id * id)
    }
}

// Anti-pattern: block the calling thread until the async operation reports back.
func syncWrapper(id: Int) -> Int {
    let semaphore = DispatchSemaphore(value: 0)
    var result = 0
    asyncOperation(id: id) { value in
        result = value
        semaphore.signal()
    }
    semaphore.wait()
    return result
}

func runWithConcurrencyLimit(limit: Int, jobs: Int, work: @escaping (Int) -> Void) -> TimeInterval {
    let slotSemaphore = DispatchSemaphore(value: limit)
    let group = DispatchGroup()
    let start = Date()
    for id in 0..<jobs {
        group.enter()
        DispatchQueue.global().async {
            slotSemaphore.wait()
            work(id)
            slotSemaphore.signal()
            group.leave()
        }
    }
    group.wait()
    return Date().timeIntervalSince(start)
}

let smallPool = runWithConcurrencyLimit(limit: 2, jobs: 8) { id in
    _ = syncWrapper(id: id)
}
print(String(format: "concurrency limit 2, 8 blocking-wrapped calls: %.3fs", smallPool))

let largePool = runWithConcurrencyLimit(limit: 8, jobs: 8) { id in
    _ = syncWrapper(id: id)
}
print(String(format: "concurrency limit 8, 8 blocking-wrapped calls: %.3fs", largePool))
```

Parsed and run with `swiftc`. `syncWrapper` is the sync-over-async anti
pattern named in dimensions 8 and 11. it takes a perfectly well-behaved
asynchronous API, `asyncOperation`, and forces callers back into blocking
semantics with `DispatchSemaphore.wait()`. Run at a concurrency limit of
two, eight such calls take roughly four times as long as at a concurrency
limit of eight, reproducing the same exhaustion curve as the Rust and Go
examples, and demonstrating that this specific anti-pattern is not tied to
any one language's I/O primitives. it reappears wherever an async API is
forced back into a blocking shape.

## 18. References

1. Dan Kegel, "The C10k problem", 1999, http://www.kegel.com/c10k.html, verified 2026-08-02.
2. Node.js documentation, "Blocking the Event Loop. Node.js Core Modules", https://nodejs.org/en/learn/asynchronous-work/dont-block-the-event-loop, verified 2026-08-02.
3. Python documentation, "Developing with asyncio", section "Running Blocking Code", https://docs.python.org/3/library/asyncio-dev.html, verified 2026-08-02.
4. Netflix, Hystrix Wiki, "How it Works", https://github.com/Netflix/Hystrix/wiki/How-it-Works, verified 2026-08-02.
5. Microsoft, "Asynchronous programming scenarios - C#", Microsoft Learn, https://learn.microsoft.com/en-us/dotnet/csharp/asynchronous-programming/async-scenarios, verified 2026-08-02.
6. The Go Authors, "Effective Go", section "Goroutines", https://go.dev/doc/effective_go, verified 2026-08-02.
7. Brett Wooldridge, "About Pool Sizing", HikariCP wiki, https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing, verified 2026-08-02.
8. PostgreSQL Global Development Group, "Connection Settings", PostgreSQL documentation, section on max_connections, https://www.postgresql.org/docs/current/runtime-config-connection.html, verified 2026-08-02.
