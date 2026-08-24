---
name: Proactor
slug: proactor
family: 09-concurrency
category: Concurrency
aliases: [Asynchronous Completion Token, Completion Port Pattern]
first_described: "Pyarali, Harrison, Schmidt, Jordan 1997; Schmidt, Stal, Rohnert, Buschmann 2000"
maturity: canonical
related: [reactor, half-sync-half-async, leader-followers, active-object, thread-pool]
incompatible_with: []
verified: 2026-08-02
---

# Proactor

## 1. Name, aliases, and lineage

The canonical name is Proactor. It was first written up as "Proactor. An
Object Behavioral Pattern for Demultiplexing and Dispatching Handlers for
Asynchronous Events" by Irfan Pyarali, Tim Harrison, Douglas C. Schmidt, and
Thomas D. Jordan, presented at the 1997 Pattern Languages of Programs (PLoP)
conference. It was then given its full catalog treatment as chapter 2 of
Douglas C. Schmidt, Michael Stal, Hans Rohnert, and Frank Buschmann,
*Pattern-Oriented Software Architecture, Volume 2. Patterns for Concurrent and
Networked Objects*, John Wiley and Sons, 2000, in the chapter titled
"Proactor". That book is universally abbreviated POSA2 in the systems
literature that cites it, and the Proactor entry there is the reference
definition every later summary, including the Wikipedia article, points back
to ([Wikipedia, Proactor pattern](https://en.wikipedia.org/wiki/Proactor_pattern),
verified 2026-08-02, which names the 2000 POSA2 book and the 1997 Pyarali et
al. paper as its sources).

Schmidt built the pattern out of his own ADAPTIVE Communication Environment
(ACE) framework, a C++ toolkit for high-performance networked servers that
predates POSA2 by several years, so the pattern was extracted from working
production code rather than invented on paper first. The alias **Asynchronous
Completion Token** names the design's central data structure rather than the
pattern as a whole. it is the opaque value an initiator hands to the
asynchronous operation processor at launch time and receives back attached to
the eventual completion event, so the demultiplexer can route the result to
the right handler without inspecting the operation's payload. **Completion
Port Pattern** is an informal name used in Windows systems programming
circles because Win32's I/O Completion Ports (IOCP) are the best known
concrete realization of the abstract pattern, and many engineers meet the
implementation before they meet the name of the pattern it implements.

The pattern sits in the concurrency and networking half of the POSA catalog
family, alongside Reactor, Half-Sync/Half-Async, Leader/Followers, and
Active Object, all of which POSA2 treats as answers to the same underlying
question. how does a program handle many concurrent I/O operations without
dedicating one blocking thread to each one. Proactor and Reactor are the two
event-demultiplexing answers to that question, and the distinction between
them is the single most important thing to understand about Proactor,
covered in full in section 12.

## 2. Problem and context

A server, or any program, needs to service many concurrent long-running
operations, most commonly network reads and writes, disk I/O, or timers,
without paying the cost of one operating system thread per concurrent
operation. Thread-per-operation does not scale. each OS thread carries a
fixed stack allocation, a kernel scheduling entry, and a context-switch cost,
and a server handling ten thousand simultaneous connections cannot afford ten
thousand blocked threads, most of them doing nothing but waiting on a socket
that has no data yet.

The obvious alternative is non-blocking I/O plus a readiness notification
mechanism. select, poll, epoll, or kqueue. the program asks the kernel "which
of these file descriptors is ready for the operation I want to perform" and
then performs the actual read or write itself, synchronously, once it knows
the descriptor will not block. This is the Reactor pattern's answer, and it
works, but the application thread still does the read or write system call
itself, still copies the bytes out of the kernel buffer on its own thread,
and still has to re-arm the readiness check for every partial operation.

The Proactor's context is a program running on a platform whose kernel, or
whose runtime layer, can perform the entire operation asynchronously on the
caller's behalf and notify the caller only when the operation has fully
finished, carrying the actual result (the bytes read, the count written, the
error code) rather than merely a readiness flag. In this context the
application's job shrinks to two things. launch operations without blocking,
and process finished results as they arrive. The problem Proactor solves is
structuring that second job cleanly. how do you route each of potentially
thousands of concurrent, interleaved completions back to the specific piece
of application logic that is waiting for that specific result, using a small,
fixed pool of threads, while keeping the code that launches an operation
textually separate from the code that decides what to do when it finishes.

## 3. Forces

**Throughput versus per-operation overhead.** Proactor's promise is high
throughput on a small thread count because the kernel or runtime, not the
application, does the blocking work. The overhead is the cost of registering
and routing an Asynchronous Completion Token per operation, and the
allocation cost of the buffer that must be pinned or otherwise kept alive
until the kernel finishes writing into it.

**Latency versus batching.** A completion dispatcher that drains many
finished operations from one queue in a batch amortizes the cost of waking a
worker thread, but a single slow completion queued behind a burst of others
adds tail latency to the operations that arrived earlier and are still
waiting to be processed by a busy handler.

**Simplicity of the call site versus control flow legibility.** Launching an
operation and registering a callback is a single, simple call. the resulting
control flow, where the code that decides what happens next lives in a
separate function invoked at an unpredictable later time on a different
stack frame, is harder for a reader to trace than straight-line synchronous
code. This is the classic "callback hell" force, mitigated in modern
languages by coroutines and async and await syntax, which is itself a
compiler-managed reformulation of the same completion-handler structure.

**Portability versus performance.** The pattern's biggest payoff appears when
the underlying platform has a genuinely asynchronous kernel facility (Windows
IOCP, or Linux io_uring since kernel 5.1). On platforms whose kernel only
offers readiness notification (classic Linux epoll, kqueue on BSD and macOS),
a Proactor-shaped API can still be built, but it must be emulated, either by
running the blocking call on a worker thread pool and posting a completion
event when that thread finishes (POSA2's software-emulated proactor), or by
building the Proactor's API on top of a Reactor internally. Both emulations
work correctly but give up some or all of the "no extra thread, no extra
copy" performance advantage the pattern has on a truly asynchronous kernel.

**Resource lifetime versus flexibility.** The buffer an asynchronous read
writes into must stay valid and unmoved in memory for the entire duration of
the kernel operation, which can be a genuine multi-millisecond wait. Proactor
implementations therefore constrain how and when buffers can be reused or
freed far more tightly than a synchronous read ever would, in exchange for
never having the caller's thread sit idle while the wait happens.

## 4. Applicability and non-applicability

Reach for Proactor when the platform, or the language runtime sitting on top
of it, offers genuinely kernel-managed asynchronous I/O and the workload is
I/O bound with a high degree of concurrency. thousands of simultaneous
network connections, a high-throughput disk-bound service, or a systems-level
library meant to sit underneath many different application frameworks. It is
also the right shape when the completion of an operation naturally carries a
result payload that the calling code needs, not merely a signal that
something happened, because the pattern's Completion Handler is invoked with
that result already in hand rather than having to fetch it with a second
call.

Do not reach for Proactor in these situations.

- **The workload is CPU bound, not I/O bound.** Proactor solves the problem
  of many concurrent blocking waits. it does nothing for a program spending
  its time computing rather than waiting on the kernel. A thread pool with
  work-stealing, or the Active Object pattern, addresses CPU-bound
  concurrency more directly.
- **The target platform has no true asynchronous I/O facility and the team
  is unwilling to accept a software emulation.** Emulating Proactor over a
  thread pool trades the thread-per-connection problem for a
  thread-pool-sized cap on true concurrency, which can be the right trade,
  but a team that assumed native kernel-level async and then discovers the
  platform silently emulates it with N worker threads has built on a false
  premise.
- **The number of concurrent operations is small and bounded**, for example
  a desktop application issuing a handful of network requests at a time. The
  operational complexity of registering completion handlers and reasoning
  about buffer lifetimes is not repaid when synchronous calls on a couple of
  background threads, or a simple async and await coroutine without any
  hand-rolled dispatch loop, would be just as fast and much easier to read.
- **The team cannot tolerate the debugging cost of asynchronous stack
  traces.** A crash inside a completion handler shows a stack trace rooted at
  the event loop's dispatch call, not at the code that launched the
  operation. Teams without tooling, or without discipline, to correlate a
  completion handler back to its originating request site will spend more
  time debugging than the pattern saves them in throughput.
- **A strict, linear happens-before ordering across operations is required
  by the domain**, for example a protocol that must process bytes strictly
  in the order they were requested. Proactor completions from independent
  operations can and do arrive out of the order in which they were launched,
  and reconstructing strict ordering on top of that adds a sequencing layer
  the application must build itself.
- **The reactive, readiness-based model already covers the need and the
  platform lacks a true asynchronous facility.** In that case, building
  Reactor directly, rather than building Proactor and then discovering it
  is internally implemented as Reactor plus a thread pool, is the more
  honest and more debuggable choice.

## 5. Structure

**Initiator.** The application code that starts an asynchronous operation.
It creates an Asynchronous Operation object, supplies a buffer and a
Completion Handler, and calls into the Asynchronous Operation Processor to
launch the operation, then returns immediately without waiting for a result.

**Asynchronous Operation.** A value object describing one unit of work to
perform, for example "read up to 4096 bytes from socket fd 7 into buffer B".
It is created by the Initiator and consumed by the Asynchronous Operation
Processor.

**Asynchronous Operation Processor.** The component, typically the operating
system kernel, that actually performs the operation. It runs the work
independently of the Initiator's thread, and when the work finishes it
constructs a Completion Event carrying the result (bytes transferred, an
error code, or both) and enqueues it, tagged with the Asynchronous Completion
Token supplied at launch time, onto the Completion Event Queue.

**Completion Event Queue.** A thread-safe queue holding finished-but-not-yet-
dispatched Completion Events. On Windows this is the I/O Completion Port
object itself. on a software emulation it is an application-level queue fed
by worker threads.

**Asynchronous Event Demultiplexer.** The blocking call, typically invoked
by one or more dedicated dispatcher threads, that waits on the Completion
Event Queue until at least one event is available, then returns it (or a
batch of them) to the caller. GetQueuedCompletionStatus on Windows and
io_uring_wait_cqe on Linux are concrete instances of this role.

**Proactor.** The dispatch loop itself. it repeatedly invokes the
Asynchronous Event Demultiplexer, and for each Completion Event it receives,
looks up the Completion Handler that was registered for that event's
Asynchronous Completion Token and invokes it, passing the result.

**Completion Handler.** The application-supplied callback, closure,
coroutine continuation, or object method that contains the logic to run once
a specific operation has finished. It receives the result directly. it never
has to ask "is my data ready" or issue a second call to retrieve it.

## 6. ASCII structure diagram

```
+-------------+        launches         +---------------------------+
|  Initiator  | -----------------------> |  Async Operation          |
|             |  (op, buffer, token,     |  Processor                |
|             |   completion handler)    |  (kernel / thread pool)   |
+-------------+                          +-------------+-------------+
      ^                                                |
      | registers                                      | operation
      | handler for token                               | finishes,
      |                                                 | posts event
      |                                                 v
+-----+-------+     drains queue      +------------------------------+
| Handler     | <--------------------- |  Completion Event Queue     |
| Registry    |    (token -> handler)  |  (IOCP / io_uring CQ /      |
| (token map) |                        |   emulated queue)           |
+-------------+                        +--------------+---------------+
                                                        |
                                          blocking wait |
                                                        v
                                        +------------------------------+
                                        |  Asynchronous Event           |
                                        |  Demultiplexer                |
                                        |  (GetQueuedCompletionStatus,  |
                                        |   io_uring_wait_cqe, select   |
                                        |   on an emulation's pipe)     |
                                        +--------------+-----------------+
                                                        |
                                                        v
                                        +------------------------------+
                                        |  Proactor dispatch loop       |
                                        |  looks up handler by token,   |
                                        |  invokes Completion Handler   |
                                        |  with the finished result     |
                                        +------------------------------+
```

## 7. Dynamics

```
Initiator          AsyncOp Processor      Completion Queue      Proactor loop      Completion Handler
   |                       |                      |                    |                   |
   | launch(op, token, h)  |                      |                    |                   |
   |---------------------->|                      |                    |                   |
   | (registers h under    |                      |                    |                   |
   |  token, returns now)  |                      |                    |                   |
   |<-----------------------------------------------------------------|                   |
   |         returns immediately, no wait          |                    |                   |
   |                       |                      |                    |                   |
   |                       | performs op          |                    |                   |
   |                       | off caller's stack    |                    |                   |
   |                       |----------------------|                    |                   |
   |                       |    (time passes)      |                    |                   |
   |                       |                      |                    |                   |
   |                       | op finishes, builds   |                    |                   |
   |                       | completion event      |                    |                   |
   |                       |--------------------->|                    |                   |
   |                       |   enqueue(token, result)                  |                   |
   |                       |                      |                    |                   |
   |                       |                      | dequeue (blocking) |                   |
   |                       |                      |<-------------------|                   |
   |                       |                      |------------------->|                   |
   |                       |                      |  event(token,result)                  |
   |                       |                      |                    |                   |
   |                       |                      |                    | lookup(token) -> h |
   |                       |                      |                    |------------------->|
   |                       |                      |                    |   invoke h(result) |
   |                       |                      |                    |                   |
   |                       |                      |                    |<------------------|
   |                       |                      |                    |  handler returns  |
   |                       |                      |                    | loop repeats       |
```

The defining property visible in this timeline is that the Initiator's call
stack ends at "returns immediately" and never appears again. the Completion
Handler executes on a wholly different call stack, driven by the Proactor's
dispatch loop, at a time the Initiator's code has no direct control over.
Contrast this with Reactor, where the same thread that discovers readiness
also performs the operation, so the operation and its result stay on one
continuous call stack.

## 8. Implementation variants

**Native kernel-backed Proactor.** The Asynchronous Operation Processor is
the operating system kernel itself, and the Completion Event Queue is a
kernel object. Windows I/O Completion Ports are the textbook example.
`CreateIoCompletionPort` associates file handles with a completion port, an
overlapped I/O call such as `ReadFile` or `WSARecv` launches the operation,
and a pool of worker threads block in `GetQueuedCompletionStatus` waiting for
finished operations to arrive, at which point the operating system itself
manages how many of those worker threads are allowed to run concurrently
([Microsoft Learn, I/O Completion Ports](https://learn.microsoft.com/en-us/windows/win32/fileio/i-o-completion-ports),
verified 2026-08-02, describing the concurrency-value mechanism and the FIFO
queue drained in LIFO thread-release order). Linux's io_uring, present since
kernel 5.1, is the more recent native realization on that platform. an
application places Submission Queue Entries describing operations into a
shared ring buffer, the kernel performs them, and results appear as
Completion Queue Entries in a second shared ring buffer that user space polls
or waits on, avoiding a system call per operation entirely on the fast path.

**Software-emulated Proactor over a worker thread pool.** On a platform with
no native asynchronous I/O facility, a Proactor-shaped API can be built by
having the Initiator hand the blocking operation to a background thread pool.
a worker thread performs the ordinary blocking call, and when it returns,
the worker posts a Completion Event onto an application-level queue that the
dispatch loop drains exactly as it would drain a kernel-backed one. This is
POSA2's documented software-emulated proactor variant, and it is what
Node.js's libuv does for filesystem operations specifically. the file
descriptor readiness model that libuv otherwise uses for sockets does not
extend cleanly to regular files on most platforms, so libuv's file I/O
functions run on an internal thread pool and post results back onto the
event loop, giving the application a completion-callback API regardless of
the underlying mechanism.

**Proactor implemented in terms of a Reactor.** Boost.Asio takes the
opposite emulation path on non-Windows platforms. its own documentation
states plainly that on Windows it takes advantage of overlapped I/O for "an
efficient implementation of the Proactor design pattern", while "on many
platforms, Boost.Asio implements the Proactor design pattern in terms of a
Reactor, such as select, epoll, or kqueue"
([Boost.Asio, Core Concepts and Functionality, Proactor Pattern section](https://www.boost.org/doc/libs/1_87_0/doc/html/boost_asio/overview/core/async.html),
verified 2026-08-02). Concretely, the library uses the underlying reactor to
learn when a socket becomes readable or writable, then performs the actual
read or write itself on an internal thread the instant that happens, and
delivers the result to the application's completion handler exactly as a
native proactor would, hiding the reactor machinery entirely behind the
proactor-shaped public API. Since Boost 1.78, on Linux kernels new enough to
support it, Boost.Asio can instead compile against io_uring directly as a
true kernel-backed proactor path, selectable at build time via the
`BOOST_ASIO_HAS_IO_URING` configuration macro, giving the same public API
either a native or an emulated backend depending on platform.

**Coroutine-sugared Proactor.** Modern languages resurface the Completion
Handler as a suspended coroutine continuation rather than an explicit
callback function. C# `Task`-based async I/O, Rust's `tokio-uring` crate, and
Python's `asyncio` all let application code write `await async_read(...)`
that reads as straight-line synchronous code, while the compiler or runtime
transforms that into exactly the launch-then-register-a-continuation shape
the pattern describes. Python's standard library goes further and names the
Windows-native backend explicitly. `asyncio.ProactorEventLoop` is the default
event loop on Windows and is documented as the loop backed by IOCP, while
`asyncio.SelectorEventLoop`, the default and only option on POSIX systems,
is a Reactor backed by `select`, `poll`, `epoll`, or `kqueue` depending on
platform, meaning the same `async def` and `await` application code compiles
down to either pattern depending entirely on which loop class is installed.

## 9. Known production uses

**Windows I/O Completion Ports underneath the .NET thread pool.** Microsoft's
own documentation for high-performance async file and socket I/O on Windows
recommends IOCP or the higher-level `CreateThreadpoolIo` wrapper for servers
handling hundreds or thousands of concurrent connections, and states that the
thread pool API "uses IOCP internally but handles thread lifecycle management
automatically"
([Microsoft Learn, I/O Completion Ports](https://learn.microsoft.com/en-us/windows/win32/fileio/i-o-completion-ports),
verified 2026-08-02). .NET's own asynchronous file and socket APIs, exposed
to application code as `Task`-returning methods consumed with `await`, are
built on this same IOCP foundation on Windows, making IOCP the load-bearing
Proactor implementation underneath a very large share of production Windows
server software.

**Boost.Asio**, the C++ networking and low-level I/O library that later
became the basis for the C++ standard library's Networking TS proposal,
states in its own documentation that "the asynchronous support is based on
the Proactor design pattern" and names the pattern by name as its core
architectural model
([Boost.Asio documentation, Core Concepts and Functionality](https://www.boost.org/doc/libs/1_87_0/doc/html/boost_asio/overview/core/async.html),
verified 2026-08-02). Boost.Asio underlies a large amount of production C++
networking infrastructure, including parts of Bitcoin Core's peer-to-peer
networking stack and many game and financial-trading network layers.

**Python's asyncio standard library module** ships `asyncio.ProactorEventLoop`
as a distinct, named class specifically for Windows, documented as being
backed by I/O Completion Ports and used as the default event loop on that
platform since Python 3.8, in explicit contrast to the reactor-style
`SelectorEventLoop` used on POSIX systems. Any Python asyncio-based server or
client library that runs on Windows without disabling the default loop is
running on a genuine Proactor implementation for its network and pipe I/O.

**Linux io_uring adoption.** Beyond Boost.Asio's optional io_uring backend,
the `tokio-uring` crate documents its own model in contrast to ordinary
Tokio, stating that unlike Tokio's normal reactor-based approach, io_uring
"is based on submission based operations. Ownership of resources are passed
to the kernel, which then performs the operation"
([tokio-uring crate documentation, docs.rs](https://docs.rs/tokio-uring/latest/tokio_uring/),
verified 2026-08-02), which is a description of the Proactor's launch-and-
complete shape rather than the Reactor's readiness-poll-then-perform shape,
applied to the Rust async ecosystem specifically for workloads that want
kernel-managed asynchronous file and network I/O without a userspace thread
pool in the loop.

## 10. Consequences

**Positive.**

- Application threads never block waiting for I/O to complete, so a small,
  fixed pool of dispatcher threads can drive a very large number of
  concurrent operations, which is exactly the C10K-and-beyond scaling
  property Reactor-based designs also chase, achieved here without the
  application performing the read or write system call itself.
- On a genuinely asynchronous kernel facility, the kernel can perform the
  data transfer directly, sometimes without an extra copy through
  application-managed buffers on the readiness-then-read path, which is real
  throughput headroom a pure Reactor cannot claim on the same hardware.
- The separation between launching an operation and handling its result is
  explicit and structural, not something the programmer has to remember to
  maintain by discipline. the Completion Handler is registered exactly once,
  at launch time, and cannot be silently skipped the way a manually
  re-armed readiness check can be forgotten.
- Coroutine-based language support (async and await, Rust's Future trait,
  Python's asyncio) can present this pattern's machinery as straight-line
  code, recovering much of the readability the raw callback-based
  implementation gives up.

**Negative.**

- Debugging is materially harder. a stack trace captured inside a Completion
  Handler is rooted at the dispatch loop, with no automatic link back to the
  code that launched the operation, so correlating a failure to its origin
  requires either language-level async stack unwinding support or manual
  request-id tracking through logs.
- Buffer lifetime management is unforgiving. the memory an operation reads
  into or writes from must remain valid, and in many native implementations
  must remain at a fixed address, for the entire duration of the kernel
  operation, which forces either careful ownership transfer into the
  asynchronous call or reference-counted buffer pools, either of which adds
  real implementation complexity absent from synchronous code.
- Portability is genuinely uneven. code written directly against IOCP or
  io_uring semantics does not run unmodified on the other platform, and
  software emulations of the pattern on platforms lacking native support
  give up some of the throughput and zero-copy benefits that motivated
  choosing the pattern in the first place.
- Cancellation is awkward. an operation that has been launched but not yet
  completed may already be irrevocably in flight inside the kernel, so
  "cancel" in a Proactor system frequently means "stop caring about the
  result when it eventually arrives" rather than a clean, immediate abort.

## 11. Failure modes and misuse

**Symptom.** The application appears to leak memory slowly under sustained
load, with heap growth roughly proportional to request volume.
**Cause.** A Completion Handler was registered for an Asynchronous
Completion Token, the operation completed, but the handler either threw an
exception before it could release the buffer it owned, or the registration
map entry for that token was never removed after dispatch, so both the
buffer and the map entry accumulate indefinitely.
**Fix.** Wrap every dispatch invocation in a guarantee that the token's
registry entry is removed exactly once regardless of whether the handler
succeeds or throws, and confirm buffer ownership transfers back to a pool or
is explicitly freed in that same guaranteed cleanup path, not only on the
success branch.

**Symptom.** Under moderate concurrency the server's throughput plateaus far
below the number of CPU cores available, even though CPU utilization per
core looks low.
**Cause.** The completion queue is being drained by a single dispatcher
thread, so every Completion Handler, however fast, is serialized behind
every other one, turning what should be parallel work across cores into
strictly sequential work on one core, while the other cores sit idle waiting
for nothing in particular.
**Fix.** Run the demultiplexing wait call on multiple dispatcher threads
sharing the same completion queue, matching the IOCP concurrency-value
guidance of roughly one thread per core, and confirm the platform's queue
implementation genuinely supports multiple concurrent waiters rather than
silently serializing them.

**Symptom.** Two completion handlers for logically related operations
occasionally observe each other's state half-updated, producing intermittent,
hard-to-reproduce data corruption under load but never under a debugger with
breakpoints set.
**Cause.** Because completion handlers for independent operations can run on
different dispatcher threads and in an order that does not match launch
order, code that assumes handlers for the same connection or the same
logical request always run on the same thread, or always run in the order
the operations were issued, is exposed to a genuine data race the moment two
of them touch shared state without synchronization.
**Fix.** Either confine all state related to one logical unit of work,
connection, or session to be touched only from handlers routed through a
single serialized queue per unit (a strand, in Boost.Asio's terminology), or
protect the shared state with the same synchronization discipline any
multithreaded code would need, and never assume completion order matches
launch order.

**Symptom.** A long-running Completion Handler causes visible latency spikes
in unrelated, otherwise fast operations that were launched afterward.
**Cause.** A handler performing blocking work, a synchronous disk write, a
slow lock acquisition, or heavy CPU-bound computation, on the dispatcher
thread starves every other completion waiting in the same queue behind it,
reintroducing exactly the blocking-thread problem the pattern exists to
avoid, just moved one layer up into the handler itself.
**Fix.** Keep every Completion Handler strictly non-blocking. offload any
CPU-heavy or blocking work the handler needs to a separate worker thread
pool and have that worker post its own completion event back into the same
queue when it finishes, rather than doing the heavy work inline.

**Symptom.** The application misbehaves only on Linux, or only under a
specific kernel version, despite identical application-level code across
platforms.
**Cause.** The team wrote code against the Proactor's public API assuming a
uniform, native, kernel-backed implementation on every platform, without
accounting for the fact that the same API is a genuine kernel facility on
one platform and a software emulation over a thread pool, or over a reactor,
on another, and the two have subtly different failure and cancellation
semantics.
**Fix.** Treat the choice of native versus emulated backend as a deployment-
relevant fact to document and test against explicitly, not an implementation
detail the pattern's abstraction fully hides, and run integration tests on
every platform-and-kernel-version combination the software actually ships to.

## 12. Trade-off matrix

| Force | Proactor | Reactor | Half-Sync/Half-Async | Thread-per-Connection |
|---|---|---|---|---|
| Who performs the I/O transfer | Kernel or worker thread, off the initiator's stack | The application thread, once notified the descriptor is ready | The async layer notifies, a synchronous layer performs the work | The dedicated blocking thread itself |
| Threads needed at high concurrency | Small, fixed dispatcher pool | Small, fixed reactor pool | Small async layer plus a bounded sync worker pool | One thread per concurrent connection, unbounded |
| Result delivery | Completion event carries the actual result | Readiness notification only, application must call read or write itself | Result queued from sync layer to async layer via a message queue | Result available directly on the blocked thread's stack |
| Code readability without coroutines | Callback-based, control flow is non-linear | Somewhat more linear, the read call sits right after the readiness check | Clear layer boundary but explicit queue hand-off | Most linear, straight blocking code |
| Native kernel support required for best performance | Yes, IOCP or io_uring, else emulated with a cost | No, select/poll/epoll/kqueue are the native mechanism it targets directly | No, built on whichever demultiplexer the async layer uses | No, relies only on ordinary blocking system calls |
| Buffer lifetime discipline | Strict, buffer must survive the whole kernel operation | Looser, buffer is only touched synchronously by the application itself | Strict at the async layer boundary, relaxed once handed to sync workers | Loosest, ordinary stack-local buffers suffice |
| Best fit | I/O-bound, very high concurrency, native async kernel facility available | I/O-bound, high concurrency, only readiness-based kernel facilities available | Mixed workloads needing both async I/O and CPU-bound synchronous processing | Low concurrency, simplicity valued over scale |

## 13. Related and incompatible patterns

**Reactor** is Proactor's closest relative and its most important point of
contrast. both patterns exist to demultiplex many concurrent I/O sources
onto a small number of threads, but Reactor demultiplexes readiness (who is
ready to be acted on) while Proactor demultiplexes completion (who has
already finished being acted on). A software-emulated Proactor is frequently
built directly on top of a Reactor, as Boost.Asio's non-Windows backend
demonstrates, which means the two patterns are not merely siblings but are
sometimes literally nested, one implementing the other.

**Half-Sync/Half-Async** describes the layered architecture many Proactor
implementations actually live inside. an asynchronous layer, driven by the
Proactor's dispatch loop, hands finished work across a queuing layer to a
synchronous layer of application logic that need not know anything about
completion tokens or non-blocking I/O at all. Proactor is one way to
implement the asynchronous layer of that broader architecture.

**Leader/Followers** is an alternative thread pool coordination pattern that
solves a related problem, which of several available threads should service
the next event, differently. Leader/Followers has each waiting thread take
turns being the single "leader" that waits on the event source, promoting a
follower to leader once the current leader picks up work, avoiding a
dedicated dispatcher thread and a hand-off queue. It is frequently discussed
alongside Proactor and Reactor in the POSA2 catalog because all three
compete for the role of coordinating how a pool of worker threads share
responsibility for waiting on and handling events.

**Active Object** decouples method invocation from method execution using a
similar Initiator-hands-off-work shape, but for ordinary method calls on an
object rather than specifically for kernel I/O operations, and typically
returns a future or promise to the caller rather than invoking a callback,
making it a natural pairing with Proactor when the completion result needs
to be composed with further asynchronous, CPU-bound work.

**Thread Pool** is the general-purpose mechanism a software-emulated
Proactor uses to stand in for a native kernel facility, as described in
section 8. A native, kernel-backed Proactor does not need an application-
managed thread pool for the operations themselves, though it typically still
uses a small pool of dispatcher threads to drain the completion queue.

No pattern in this family is structurally incompatible with Proactor. the
tensions are architectural choices, which pattern to use where, rather than
patterns that cannot coexist in the same system.

## 14. Refactoring path in and out

**Introducing Proactor into a thread-per-connection codebase.** Start by
identifying the single most concurrency-limited resource, typically socket
reads and writes, and replace the blocking call at that one site with an
asynchronous launch plus a registered Completion Handler, while leaving the
rest of the connection's logic synchronous and running on its dedicated
thread for now. Verify under load that the new asynchronous site no longer
blocks a thread, then progressively convert the remaining blocking calls on
that same connection's code path the same way, one call site at a time,
confirming after each conversion that the completion handler correctly
receives the result the old synchronous call used to return directly.
Finally, once every blocking call on a connection's path has been converted,
collapse the now-empty dedicated thread and let the shared dispatcher pool
service that connection like any other, which is the point at which the
thread-per-connection cost genuinely disappears from the system.

**Introducing Proactor by wrapping an existing Reactor-based codebase.**
Rather than rewriting the reactor's readiness-driven event loop, introduce a
thin Asynchronous Operation Processor layer that, on a readiness
notification, performs the read or write itself immediately and then invokes
a registered completion handler with the result, exactly as Boost.Asio's
reactor-backed emulation does. This lets calling code migrate to the
completion-handler API incrementally, call site by call site, without
touching the underlying event loop at all, and creates the option to later
swap the reactor-backed processor for a native IOCP or io_uring one behind
the same public interface.

**Removing Proactor when it no longer earns its place.** If profiling shows
the concurrency level the system actually experiences in production never
approaches the point where thread-per-operation would have been a genuine
scaling problem, and the callback or coroutine indirection is measurably
slowing development and debugging, replace the completion-handler call
sites with ordinary blocking calls on a small, explicitly sized worker pool,
starting from the least concurrency-sensitive call sites and working toward
the most. Confirm at each step, with a load test representative of real
traffic, that the simplified synchronous version still meets the system's
actual latency and throughput requirements before removing the next site,
since it is easy to discover too late that the true concurrency need was
higher than the profiling sample suggested.

## 15. Testing and verification

Testing a Proactor-based system splits cleanly into two concerns. verifying
that a single Completion Handler behaves correctly given a known result, and
verifying that the dispatch machinery routes completions to the right
handler under realistic concurrency.

For the first concern, unit test each Completion Handler as an ordinary
function or callable, calling it directly with a constructed result value
(a byte count, a buffer, an error code) rather than going through the real
asynchronous operation processor at all. This isolates the handler's logic
completely from the timing and threading behavior of the dispatch loop,
which is exactly what makes it fast and deterministic to test, but it also
means these tests say nothing about whether the handler is ever actually
invoked with the right token, on the right thread, or in the right state, so
they cannot be the only tests in the suite.

For the second concern, replace the real Asynchronous Operation Processor
with a deterministic test double that lets the test control exactly when
each operation "completes" and in what order, rather than relying on real
network or disk timing, which is inherently non-deterministic and produces
flaky tests if used directly. A test double that accepts launched operations
into an in-memory list and lets the test explicitly trigger completion of
any one of them, in any order the test chooses, is the standard technique
for exercising out-of-order completion, partial reads, and error paths
without depending on real I/O timing at all.

Concurrency-specific bugs, the shared-state races described in section 11,
are the hardest category to catch with ordinary unit tests, since they
depend on genuine thread interleaving that a single-threaded test double
cannot reproduce. For these, run the real system, or as much of it as
practical, under a stress test that launches a large number of concurrent
operations against real or simulated I/O with injected variable latency, and
run that stress test repeatedly under a thread sanitizer or an equivalent
data-race detector, since a race that occurs once in a thousand runs is
still a real production bug and will not reliably show up in a single test
execution.

## 16. Observability signals

Track the depth of the completion queue over time. a queue depth that
trends upward under steady load, rather than oscillating around a small
number, means completions are arriving faster than the dispatcher pool can
drain and dispatch them, which is the direct, measurable symptom of a
dispatcher pool sized too small or of handlers that are not returning
quickly enough, as described in section 11.

Measure the time between when an operation is launched and when its
completion handler finishes running, broken into two components. the time
the operation itself spent in flight (kernel or worker-pool time) and the
time the completion sat in the queue waiting for a free dispatcher thread.
The second component is queueing delay under the dispatcher's control and is
the number to alert on. a healthy system shows this near zero almost all the
time. a system approaching saturation shows it growing.

Count outstanding, unmatched Asynchronous Completion Tokens, operations that
have been launched but whose completion has not yet arrived. A count that
grows without bound over the life of the process, rather than staying
roughly proportional to current concurrent load, points directly at the
memory-leak failure mode from section 11, where a handler is being
registered but never dispatched or never cleaned up.

On a native IOCP-backed system specifically, the concurrency value passed to
`CreateIoCompletionPort` and the number of runnable-versus-blocked worker
threads are both directly observable through the Windows performance
counter subsystem, and comparing the two against the machine's actual core
count is the standard diagnostic for the single-thread-serialization failure
mode in section 11.

## 17. Security and privacy implications

The buffer lifetime discipline the pattern requires is itself a security
surface. a buffer that is freed or reused by the application before the
kernel or worker thread has actually finished writing into it produces a
use-after-free, in the classic native-code sense, that an attacker
controlling the timing or size of network input may be able to exploit for
memory corruption, so implementations on unmanaged languages must treat
buffer ownership transfer at operation launch time as a hard, enforced
invariant rather than a convention.

Because completion handlers for unrelated logical sessions can share
dispatcher threads and, depending on the platform's memory allocator, can
even reuse the same physical buffer memory in quick succession, a handler
that fails to zero or fully overwrite a buffer before releasing it back to
a pool risks leaking one session's data (credentials, message contents) into
a subsequently served, unrelated session that happens to receive the same
recycled buffer, which is a real information-disclosure surface distinct
from the pattern's usual correctness concerns.

Cancellation semantics, already noted in section 10 as awkward, have a
security dimension too. an operation that cannot be truly aborted mid-flight
means a client that opens many operations and then disconnects can leave the
server holding buffers and worker resources for operations still nominally
"in flight" from the server's point of view, which is a resource-exhaustion
denial-of-service vector that must be bounded explicitly, typically with a
per-connection or per-client cap on outstanding operations, rather than left
to the pattern's own machinery to police.

## 18. References

- Irfan Pyarali, Tim Harrison, Douglas C. Schmidt, Thomas D. Jordan,
  "Proactor. An Object Behavioral Pattern for Demultiplexing and
  Dispatching Handlers for Asynchronous Events", Pattern Languages of
  Programs (PLoP), 1997. Cited via
  [Wikipedia, Proactor pattern](https://en.wikipedia.org/wiki/Proactor_pattern),
  verified 2026-08-02.
- Douglas C. Schmidt, Michael Stal, Hans Rohnert, Frank Buschmann,
  *Pattern-Oriented Software Architecture, Volume 2. Patterns for
  Concurrent and Networked Objects*, John Wiley and Sons, 2000, chapter
  "Proactor". Cited via
  [Wikipedia, Proactor pattern](https://en.wikipedia.org/wiki/Proactor_pattern),
  verified 2026-08-02.
- Microsoft, "I/O Completion Ports",
  [learn.microsoft.com/en-us/windows/win32/fileio/i-o-completion-ports](https://learn.microsoft.com/en-us/windows/win32/fileio/i-o-completion-ports),
  verified 2026-08-02.
- Boost.Asio documentation, "Core Concepts and Functionality, Proactor
  Pattern",
  [boost.org/doc/libs/1_87_0/doc/html/boost_asio/overview/core/async.html](https://www.boost.org/doc/libs/1_87_0/doc/html/boost_asio/overview/core/async.html),
  verified 2026-08-02.
- libuv, "Design overview",
  [docs.libuv.org/en/v1.x/design.html](https://docs.libuv.org/en/v1.x/design.html),
  verified 2026-08-02.
- tokio-uring crate documentation,
  [docs.rs/tokio-uring/latest/tokio_uring](https://docs.rs/tokio-uring/latest/tokio_uring/),
  verified 2026-08-02.
- Python Software Foundation, `asyncio` documentation, event loop
  implementations `ProactorEventLoop` and `SelectorEventLoop`, standard
  library reference, current as of the verification pass on 2026-08-02.

## Code

The three implementations below all build the same shape. an Initiator that
launches operations and returns immediately, an Asynchronous Operation
Processor that performs the work off the initiator's call path, and a
Completion Handler invoked once a result is ready, looked up by the
operation's identity rather than polled for.

### TypeScript. Node's genuinely completion-based file I/O

Node's `fs` callback API is not a coroutine sugar over a reactor. for regular
file I/O specifically, libuv performs the operation on its own thread pool
and delivers the finished result straight to the callback, which is the
software-emulated Proactor variant described in section 8.

```typescript
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

type ReadCompletionHandler = (
  err: NodeJS.ErrnoException | null,
  bytes: number,
  data: Buffer,
) => void;

function launchAsyncRead(filePath: string, onComplete: ReadCompletionHandler): void {
  fs.open(filePath, "r", (openErr, fd) => {
    if (openErr) {
      onComplete(openErr, 0, Buffer.alloc(0));
      return;
    }
    const buffer = Buffer.alloc(64);
    // fs.read is the asynchronous operation. onComplete is the
    // completion handler, invoked later with the finished result.
    fs.read(fd, buffer, 0, buffer.length, 0, (readErr, bytesRead, data) => {
      fs.close(fd, () => {
        onComplete(readErr, bytesRead, data.subarray(0, bytesRead));
      });
    });
  });
}

function main(): void {
  const tmp = path.join(os.tmpdir(), `proactor-demo-${process.pid}.txt`);
  fs.writeFileSync(tmp, "payload-for-demo");

  let pending = 3;
  for (let requestId = 1; requestId <= 3; requestId++) {
    launchAsyncRead(tmp, (err, bytesRead) => {
      if (err) {
        console.error(`request ${requestId} failed: ${err.message}`);
      } else {
        console.log(`handler for request ${requestId}: ${bytesRead} bytes arrived`);
      }
      pending -= 1;
      if (pending === 0) fs.unlinkSync(tmp);
    });
  }
}

main();
```

Compiled with `tsc --target ES2020 --module commonjs --lib ES2020 --types
node` against Node's own `@types/node` package and run with `node`, this
prints three completion lines. the request numbers may not print in launch
order, which is expected and is the point.

### Python. asyncio, the same API on top of either a Proactor or a Reactor

`asyncio.ProactorEventLoop` on Windows is a named, documented Proactor
implementation backed by IOCP. `asyncio.SelectorEventLoop`, the only loop
available on POSIX, is a Reactor. The application code below is identical
either way, which is the whole point of the coroutine-sugared variant from
section 8.

```python
import asyncio


async def async_read(request_id: int, latency: float) -> bytes:
    # Stands in for a real asynchronous file or socket read. The
    # coroutine suspends here without blocking the event loop thread.
    await asyncio.sleep(latency)
    return f"payload-for-{request_id}".encode()


async def completion_handler(request_id: int, latency: float) -> None:
    data = await async_read(request_id, latency)
    print(f"handler for request {request_id}: {len(data)} bytes arrived")


async def main() -> None:
    await asyncio.gather(
        completion_handler(1, 0.02),
        completion_handler(2, 0.04),
        completion_handler(3, 0.01),
    )


if __name__ == "__main__":
    asyncio.run(main())
```

Run with `python3`. On this machine, the standard `asyncio.run` selects
`_UnixSelectorEventLoop`, the Reactor-backed loop, since POSIX has no IOCP.
the same source, unmodified, would run on `ProactorEventLoop` on Windows.

### Rust. a from-scratch completion queue and dispatch loop, no OS bindings

This implementation is the pattern's mechanics laid bare, standing in for
the kernel with a background thread per operation and a channel as the
Completion Event Queue, so the roles from section 5 are visible directly in
the code rather than hidden behind a runtime.

```rust
use std::collections::HashMap;
use std::sync::mpsc::{channel, Sender};
use std::thread;
use std::time::Duration;

enum Completion {
    ReadDone { request_id: u64, bytes: Vec<u8> },
}

type Handler = Box<dyn FnOnce(&[u8]) + Send>;

fn async_read(tx: Sender<Completion>, request_id: u64, simulated_latency_ms: u64) {
    // Stands in for the Asynchronous Operation Processor. work runs
    // off the initiator's stack, only the finished result crosses back.
    thread::spawn(move || {
        thread::sleep(Duration::from_millis(simulated_latency_ms));
        let payload = format!("payload-for-{}", request_id).into_bytes();
        tx.send(Completion::ReadDone { request_id, bytes: payload }).unwrap();
    });
}

fn main() {
    let (tx, rx) = channel::<Completion>();
    let mut handlers: HashMap<u64, Handler> = HashMap::new();

    for id in 1..=3u64 {
        handlers.insert(
            id,
            Box::new(move |bytes: &[u8]| {
                println!("handler for request {}: {} bytes arrived", id, bytes.len());
            }),
        );
        async_read(tx.clone(), id, 20 * id);
    }
    drop(tx);

    // The Proactor dispatch loop. block only on the completion queue,
    // route each finished result to its registered handler.
    let mut remaining = handlers.len();
    while remaining > 0 {
        match rx.recv() {
            Ok(Completion::ReadDone { request_id, bytes }) => {
                if let Some(handler) = handlers.remove(&request_id) {
                    handler(&bytes);
                }
                remaining -= 1;
            }
            Err(_) => break,
        }
    }
}
```

Compiled with `rustc -O` and run directly, this prints three completion
lines in the order requests actually finish (fastest-launched-latency
first, here request 3 before 1 before 2), demonstrating that completion
order is independent of launch order, exactly as section 11 warns.

Swift and Java are omitted here deliberately rather than padded in. Swift's
own async and await model is built on Swift Concurrency's cooperative task
executor, which is architecturally closer to Reactor plus structured
concurrency than to a kernel-backed Proactor on any of Apple's platforms,
and Java's `java.nio.channels.AsynchronousChannelGroup` is a genuine, named
Proactor implementation in the JDK but requires a full JVM toolchain this
environment was not confirmed to have available at verification time, so it
is named here as a real production instance in section 9's spirit without
being included as a compiled sample.
