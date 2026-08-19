---
name: Reactor
slug: reactor
family: 09-concurrency
category: Concurrency
aliases: [Dispatcher, Notifier, Non-blocking I/O Event Loop]
first_described: "Schmidt 1995"
maturity: canonical
related: [proactor, half-sync-half-async, leader-followers, active-object, thread-pool, observer, command, template-method, strategy]
incompatible_with: [proactor]
verified: 2026-08-02
---

# Reactor

## 1. Name, aliases, and lineage

The canonical name is Reactor. Douglas C. Schmidt first described it in "Reactor.
An Object Behavioral Pattern for Demultiplexing and Dispatching Handles for
Synchronous Events," presented at the first Pattern Languages of Programs
conference in Monticello, Illinois in 1994 and printed in James O. Coplien and
Douglas C. Schmidt (editors), *Pattern Languages of Program Design*,
Addison-Wesley, 1995
([Wikipedia summary of the origin and the paper title](https://en.wikipedia.org/wiki/Reactor_pattern),
verified 2026-08-02, cross-checked against
[Schmidt's own publication page](https://www.dre.vanderbilt.edu/~schmidt/patterns-ace.html),
verified 2026-08-02, which gives the paper's full title as "Reactor. An Object
Behavioral Pattern for Event Demultiplexing and Event Handler Dispatching" and
confirms the 1994 conference and the 1994 to 1995 print venue). Schmidt later
folded the pattern into Chapter 3 of Douglas C. Schmidt, Michael Stal, Hans
Rohnert, and Frank Buschmann, *Pattern-Oriented Software Architecture, Volume 2.
Patterns for Concurrent and Networked Objects*, John Wiley and Sons, 2000,
ISBN 978-0-471-60695-6
([Wikipedia's summary of the POSA series and this volume's authors, year, and ISBN](https://en.wikipedia.org/wiki/Pattern-Oriented_Software_Architecture),
verified 2026-08-02, the ISBN's 0-471 registrant range is Wiley's own and can
be checked by any reader against the ISBN registry). POSA2 is the book most
practitioners cite today, because it places Reactor next to the five sibling
patterns it is usually paired or contrasted with. Proactor, Half-Sync/Half-Async,
Leader/Followers, Active Object, and Wrapper Facade.

Reactor grew out of Schmidt's work on the ACE framework (the Adaptive
Communication Environment), a C++ networking toolkit built to remove the
copy-pasted select loop that every socket server in the early 1990s reinvented
by hand. The pattern is the name Schmidt gave to that loop once its shape had
stabilized across enough ACE-based servers to be worth writing down.

Three aliases show up in real documentation and all three name the same
mechanism from a different angle. "Dispatcher" appears in frameworks that put
the emphasis on the routing step rather than the waiting step, most visibly in
libevent's internal naming of its `event_base` as the thing that dispatches
ready events to callbacks. "Notifier" is an older ACE-adjacent term for the
same role, used when the emphasis is on telling application code that
something happened rather than on the mechanics of finding out what happened.
"Non-blocking I/O event loop" is the plain-English description used by
developers who have never heard the pattern's name and simply built one,
usually the exact shape POSA2 formalizes.

A caution belongs here because the phrase "event loop" is used for three
distinct things and conflating them is the most common source of confused
Reactor discussions.

- **Reactor proper.** A single loop that blocks in a synchronous demultiplexer
  (select, poll, epoll, kqueue), wakes when one or more handles are ready, and
  dispatches each ready handle to its registered handler, which runs to
  completion inline on the loop's own thread before the loop blocks again.
- **Proactor.** A loop that dispatches on completion of an operation the
  operating system already performed, not on readiness to perform one. The
  operating system does the read or write itself and hands back the finished
  buffer. Windows I/O Completion Ports is the classic native example, and it
  is a genuinely different pattern from Reactor, formalized separately in the
  same POSA2 chapter and distinguished explicitly by the Asio library's own
  documentation, which names its own `io_context` a Proactor and states it
  "calls the asynchronous event demultiplexer to dequeue events, and dispatches
  the completion handler" for an operation that has already finished
  ([Asio core overview](https://think-async.com/Asio/asio-1.30.2/doc/asio/overview/core/async.html),
  verified 2026-08-02). See dimension 4 and dimension 13 for how the two relate.
- **A generic run loop or message loop.** GUI toolkits, Android's `Looper`, and
  cooperative task schedulers all have a central loop that pulls the next unit
  of work and runs it. That loop is a Reactor only when the thing it is
  demultiplexing is a set of OS-level handles through a readiness call. A
  message queue drained in FIFO order with no readiness multiplexing at all is
  a different, simpler pattern, closer to Command dispatch than to Reactor.

## 2. Problem and context

A server accepts many concurrent client connections, and at any instant almost
all of them are idle. waiting for the client to send the next request, waiting
for the client to read a response, waiting for a keep-alive timeout. A small
minority are ready to be read from or written to right now. The server has to
notice which minority that is, without wasting a thread on every connection
that is doing nothing.

The naive first design is a thread per connection, each thread blocked inside
a synchronous `read()` call. This works cleanly up to a few hundred
connections and starts to hurt at a few thousand, the situation later named
the C10k problem after Dan Kegel's writeup of the trouble commodity servers
had scaling past ten thousand simultaneous connections
([Wikipedia's framing of the problem Reactor addresses](https://en.wikipedia.org/wiki/Reactor_pattern),
verified 2026-08-02). Each blocked thread costs a fixed stack allocation
(commonly one to eight megabytes of virtual address space depending on the
platform and runtime default), a kernel scheduling entry, and a context switch
every time the scheduler decides it is that thread's turn even though it has
nothing to do. Ten thousand mostly-idle threads means ten thousand mostly-idle
stacks and a scheduler doing real work just to keep cycling through
connections that are not ready.

The context that produces this problem has three recurring parts. First, the
number of concurrent connections is large relative to the number of CPU
cores, so a one-thread-per-connection model cannot map cleanly onto hardware
parallelism, most threads are waiting, not computing. Second, the operating
system already exposes a mechanism to ask which of these many handles is
ready right now, through `select`, `poll`, `epoll` on Linux, `kqueue` on the
BSDs and macOS, or I/O Completion Ports on Windows, so the information the
server needs already exists at the kernel level and does not have to be
invented. Third, the per-connection work, once a handle actually is ready, is
usually small and fast, parse a request line, copy a buffer, write a
response, so a single thread can service many ready handles in sequence
without any one of them monopolizing it, provided none of them blocks.

Reactor is the pattern that turns "ask the kernel which handles are ready,
then run each ready handle's handler" into a reusable structure instead of a
loop every server author writes by hand and every server author gets subtly
wrong in a different way.

## 3. Forces

- **Thread cost.** Favored heavily. A Reactor holds open connections as
  passive data, not as blocked threads, so the number of concurrent
  connections a single reactor thread can track is bounded by memory for
  per-connection state, not by OS thread limits or per-thread stack size.
- **Latency of a single event.** Favored when handlers are short. Dispatch is
  a map lookup plus a function call, cheap compared to the blocking-thread
  wakeup and scheduling latency of the thread-per-connection alternative.
- **Latency under a slow handler.** Sacrificed, and this is the pattern's
  sharpest cost. A single-threaded Reactor runs every ready handler on the
  same thread that runs the demultiplexer. One handler that blocks, spins, or
  performs a long computation stalls every other connection registered with
  that reactor for as long as the offending handler runs.
- **Cognitive load.** Sacrificed. Handler code is inverted, control returns to
  the reactor after every partial unit of work rather than flowing linearly
  through a function the way blocking code does. A request that spans several
  reads is written as a small state machine rather than as a straight-line
  function, and tracing what happens next through a stack trace no longer
  works, because there is no call stack connecting one event to the next.
- **CPU parallelism.** Sacrificed by a single Reactor instance, recoverable by
  running several Reactor instances (one per core, see dimension 8), at the
  cost of needing a way to spread accepted connections across them.
- **Portability.** Sacrificed at the implementation level, favored at the API
  level. `select`, `poll`, `epoll`, `kqueue`, and IOCP are five different
  system calls with five different semantics, so a portable Reactor
  implementation needs a platform abstraction layer underneath its uniform
  registration API. Every production Reactor named in dimension 9 carries
  exactly this layer.
- **Backpressure.** Mildly favored. Because the reactor thread only advances
  when a handle is genuinely ready, it naturally will not spin on idle
  connections the way a naive polling loop would, and the number of
  registered handlers gives a direct, cheap-to-read count of current load.
- **Debuggability under load.** Sacrificed. A stalled Reactor looks identical
  from the outside to a Reactor doing legitimate work quickly, both show one
  busy thread and many idle-looking connections, and the only way to tell them
  apart is to measure event-loop lag directly, see dimension 16.

Nothing here is free. A pattern that cost nothing would not need a name.

## 4. Applicability and non-applicability

Reach for Reactor when the following hold together.

- The workload is dominated by connections or handles that are idle most of
  the time and only occasionally ready for I/O, the classic mostly-idle,
  many-connection server shape.
- Individual units of work, once a handle is ready, are short and bounded, a
  parse, a buffer copy, a small state transition, never a long computation or
  a blocking call to another synchronous resource.
- Predictable, low per-connection memory matters more than keeping the
  control flow of each connection's handling code linear and easy to trace
  with a debugger's call stack.
- The target platform exposes a genuine readiness-based multiplexing
  primitive (epoll, kqueue, poll, or at minimum select), so the pattern is not
  being emulated on top of something that does not naturally support it.

Do NOT reach for Reactor in these cases, and the reason is the point, not the
rule itself.

- **The handler does real CPU work.** A Reactor cannot protect other
  connections from a handler that spends milliseconds computing instead of
  microseconds dispatching. Hand CPU-bound or blocking work off to a worker
  thread pool and keep the reactor thread doing only I/O readiness dispatch,
  which is exactly the seam the Half-Sync/Half-Async pattern names. Bolting a
  compute-heavy handler directly onto a Reactor produces a server that looks
  fast under light load and falls over under real load, because every slow
  request stalls every concurrent request sharing that reactor thread.
- **The natural primitive is completion, not readiness.** Windows I/O
  Completion Ports notify on a finished read, not a readable socket, and the
  kernel does the copy itself. Modeling that as a Reactor forces an artificial
  readiness abstraction over a completion-based primitive, which is exactly
  backwards. Proactor is the honest pattern there, see dimension 13. The same
  argument applies to Linux's `io_uring`, whose submission and completion
  queue model notifies the application when an operation is finished rather
  than when a descriptor merely becomes ready
  ([unixism.net's explanation of io_uring's submission and completion queues](https://unixism.net/loti/what_is_io_uring.html),
  verified 2026-08-02), so a system built around `io_uring` from the ground
  up is naturally Proactor-shaped, not Reactor-shaped, even though today most
  `io_uring`-backed servers still layer it under an existing Reactor-flavored
  API for compatibility rather than exposing the completion model directly.
  This last sentence is an architectural read of where the ecosystem is
  heading rather than a settled, sourced fact, and it should be weighed as
  such.
- **A handful of long-lived, low-volume connections.** If a service talks to
  five peers and each connection carries occasional traffic, thread-per-
  connection with blocking reads is simpler to write, simpler to debug with a
  stack trace, and the thread cost this pattern exists to avoid never
  materializes at that scale. Reactor is speculative machinery here.
- **A handler that must block on a mutex, a synchronous database driver, or
  any resource with unbounded wait time.** The stall it causes is
  indistinguishable, from the outside, between a legitimately busy loop and a
  wedged one, and it takes down every other connection sharing the thread
  along with it.
- **An existing event loop already owns the thread.** A GUI toolkit's main
  loop or a game engine's frame loop is itself a demultiplexing and
  dispatching loop. Running a second, independent Reactor on the same thread
  produces two loops competing to be the one that actually calls `select`,
  which is not composable, integrate with the host loop's own registration
  API (most GUI toolkits expose exactly this hook) rather than layering a
  competing Reactor underneath it.
- **The goal is parallel throughput on a CPU-bound pipeline.** Reactor
  reduces thread count for I/O-bound waiting, it does nothing for a workload
  that is limited by compute, where a thread or process pool sized to the
  core count is the correct tool.

## 5. Structure

Four participants, named the way Schmidt and POSA2 name them, because those
names are what production code and papers both use.

- **Handle.** An operating-system-level resource identifier, a file
  descriptor, a socket, a Windows `HANDLE`, that the Synchronous Event
  Demultiplexer can wait on. The Reactor never touches the Handle's data
  directly, only its readiness.
- **Synchronous Event Demultiplexer.** The system call that blocks the calling
  thread until one or more registered Handles become ready for a specified
  operation (read, write, accept, or exception), then returns the ready
  subset. `select`, `poll`, `epoll_wait`, `kevent`, and `WaitForMultipleObjects`
  each play this role on their respective platforms.
- **Event Handler.** An interface (or, in a language with first-class
  functions, a plain callback) with one method invoked when its associated
  Handle becomes ready for the event type it registered for. Concrete
  handlers hold whatever state they need, an accept handler holds the
  listening socket, a read handler holds the connection and a partial-message
  buffer.
- **Initiation Dispatcher (the Reactor itself).** Owns the registration table
  mapping each Handle and event type to its Event Handler, drives the
  Synchronous Event Demultiplexer in a loop, and on each return dispatches
  every ready Handle to the correct Event Handler by looking it up in the
  table.

Relationships. The Initiation Dispatcher depends on Event Handler only through
its abstract interface, never on a concrete handler type, which is what lets
new handler kinds be added without touching the dispatcher. Concrete handlers
depend on Handle through the operating system's I/O primitives directly. A
handler frequently registers or unregisters other handlers as a side effect
of running, an accept handler's whole job is to register a fresh read handler
for the connection it just accepted, which is the one place the pattern's
static structure and its runtime behavior are hardest to separate cleanly.

## 6. ASCII structure diagram

```
              register(handle, event, handler)
   +----------------------------------------------------------+
   |                                                            |
   |              +------------------------+                    |
   |              |  Initiation Dispatcher | (the Reactor)       |
   |              |------------------------|                    |
   +------------->| + register_handler()   |                    |
                  | + remove_handler()     |                    |
                  | + handle_events()      |                    |
                  | - handle_table Map     |                    |
                  +------------------------+                    |
                        |            ^                          |
             wait()     |            | ready handles            |
                        v            |                          |
         +-----------------------------------+                  |
         | Synchronous Event Demultiplexer    |                  |
         | (select / poll / epoll / kqueue)   |                  |
         +-----------------------------------+                  |
                        ^                                        |
                        |  watches                                |
              +---------+---------+---------+                    |
              |         |         |         |                    |
          +-------+ +-------+ +-------+ +-------+                |
          |Handle1| |Handle2| |Handle3| |HandleN|                |
          +-------+ +-------+ +-------+ +-------+                |
                                                                  |
                    dispatch(handle) -> lookup -> call            |
                                                                  |
      +-----------------+    implements     +------------------+ |
      |  <<interface>>  |<------------------|  ConcreteHandler | |
      |  Event Handler  |                   |------------------| |
      |------------------|                  | + handle_event() |-+
      | + handle_event() |                  | (AcceptHandler,  |
      +-----------------+                   |  ReadHandler...) |
                                             +------------------+

   The dispatcher owns the handle_table. Each ConcreteHandler owns
   its own application state (buffers, connection objects).
```

## 7. Dynamics

```
Application     InitiationDispatcher   Demultiplexer   AcceptHandler   ReadHandler
    |                    |                   |               |             |
    |-- register(listen_fd, ACCEPT,          |               |             |
    |     acceptHandler) ------------------->|               |             |
    |                    |-- add to watch set ------------->|               |
    |                    |                   |               |             |
    |-- handle_events() ->|                   |               |             |
    |                    |-- select()/wait() ->|               |             |
    |                    |    (BLOCKS here)  |               |             |
    |                    |                   |               |             |
    |                    |<-- listen_fd ready -|               |             |
    |                    |-- dispatch(listen_fd) ------------>|             |
    |                    |                   |               |-- accept() |
    |                    |                   |               |-- register(client_fd,
    |                    |                   |               |    READ, readHandler) ->|
    |                    |<-- add to watch set (client_fd) -------------------|
    |                    |                   |               |             |
    |                    |-- select()/wait() ->|               |             |
    |                    |    (BLOCKS again) |               |             |
    |                    |<-- client_fd ready -|               |             |
    |                    |-- dispatch(client_fd) ---------------------------->|
    |                    |                   |               |             |-- read()
    |                    |                   |               |             |-- respond()
    |                    |                   |               |             |-- (if done
    |                    |                   |               |             |    unregister)
    |                    |-- select()/wait() ->|               |             |
    |                    |     loop continues indefinitely     |             |
```

Three properties of the flow are worth stating outright because they are
where most hand-written Reactors go wrong.

First, `handle_events` (sometimes called `run` or `serve_forever`) is a
blocking call that the application calls once, and control does not return to
the application until the loop is told to stop. Every subsequent unit of work
happens through the registered handlers, not through the application calling
back into the loop.

Second, the demultiplexer call is the only place the thread genuinely blocks.
Every event handler invocation, between one `select` return and the next,
must be non-blocking and fast, because it runs on the same thread that is
about to go block in `select` again on behalf of every other registered
handle. A handler that performs a blocking call turns the shared
demultiplexer wait into an unbounded stall for every other connection.

Third, registration and unregistration typically happen from inside a
handler, not from outside the loop. An accept handler registers a new read
handler. A read handler that detects end-of-stream unregisters itself and
closes its handle. Because this mutation happens on the same thread that is
about to call the demultiplexer again, most Reactor implementations either
apply registration changes immediately (single-threaded reactors) or queue
them for application at the top of the next loop iteration (reactors that
must also accept registrations from other threads, where mutating the
watch set concurrently with the demultiplexer call would race).

## 8. Implementation variants

**Single-reactor, single-thread.** The textbook form. One thread runs the
demultiplexer and every handler. Simplest to reason about, and the natural
fit for a language whose runtime is inherently single-threaded for
application code, JavaScript being the clearest example, where the one event
loop, one thread model is not an implementation choice but a language
guarantee.

**Multi-reactor, multi-thread (N reactors).** One reactor instance per CPU
core, each in its own OS thread, each with its own demultiplexer instance and
its own registration table. New connections are spread across the reactors,
either by the operating system (Linux's `SO_REUSEPORT` lets several
listening sockets share one port and the kernel load-balances accepted
connections across them) or by the application handing an accepted
connection off to whichever reactor is least loaded. Netty's
`NioEventLoopGroup` and nginx's worker-process model both take this shape,
see dimension 9.

**Reactor plus a bounded worker pool.** The reactor thread does only I/O
readiness dispatch and hands the actual request handling to a fixed-size
thread pool, so a slow or CPU-heavy handler stalls a worker, not the reactor
thread that every other connection depends on. This is the point where
Reactor stops standing alone and composes with Half-Sync/Half-Async, the
reactor is the asynchronous layer, the worker pool is the synchronous layer,
and a queue between them is the seam.

**Interface-and-subclass form.** The form the structure diagram shows
directly. A language with interfaces or abstract classes (Java, C++, C#)
declares an `EventHandler` interface with one dispatch method, and concrete
handlers implement it. Java's `java.nio.channels.Selector`, described in the
JDK's own API documentation as "a multiplexor of `SelectableChannel` objects"
([Oracle Java SE 21 API, `java.nio.channels.Selector`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/channels/Selector.html),
verified 2026-08-02), is this exact structure exposed as a standard library
primitive, with `SelectionKey.attach()` playing the role of the dispatch
table's handler lookup.

**Function-valued (closure) variant.** In a language where a function is a
value, first-class registration replaces the handler-interface hierarchy
entirely. Python's `selectors` module returns a `SelectorKey` carrying
arbitrary `data` on `select()`, and application code stores a plain callable
there instead of an object implementing an interface
([Python 3 documentation, `selectors` module](https://docs.python.org/3/library/selectors.html),
verified 2026-08-02). Node's `net.Socket` follows the same shape through
`EventEmitter.on('data', callback)`.

**The reactor hidden inside the runtime.** Go takes this furthest. Ordinary
Go code calling `conn.Read()` looks like a blocking call on a dedicated
goroutine, not like Reactor at all, but underneath, the Go runtime's own
network poller registers the file descriptor with the operating system's
readiness primitive and parks the goroutine rather than the OS thread. On
Linux this is implemented directly against `epoll`, confirmed in the
runtime's own source, where `netpollinit` calls `EpollCreate1` and the poller
uses `EpollWait` to find ready descriptors
([`runtime/netpoll_epoll.go`, Go standard library source](https://github.com/golang/go/blob/master/src/runtime/netpoll_epoll.go),
verified 2026-08-02). The Reactor is real, it is simply implemented once
inside the language runtime instead of once per application, and the
application-facing API presents an illusion of blocking, thread-per-request
code on top of it. Whether this fully counts as an instance of the pattern or
as a runtime feature that makes the pattern unnecessary at the application
layer is a matter of where the reader draws the line between the pattern and
the language, and this entry treats it as the pattern relocated rather than
eliminated, which is a judgement call, not a sourced claim.

**Async-task-plus-reactor hybrid.** Rust's Tokio runtime documents its own
architecture as including "an I/O event loop, called the driver, which
drives I/O resources and dispatches I/O events to tasks that depend on them"
([Tokio `runtime` module documentation, docs.rs](https://docs.rs/tokio/latest/tokio/runtime/index.html),
verified 2026-08-02). Here the Event Handler role is played by a suspended
`async fn` task rather than by an object or a closure, the driver wakes the
task's `Waker` instead of calling a method directly, and a separate
cooperative task scheduler decides which woken task actually runs next. The
demultiplexing half of Reactor is intact, the dispatch half is mediated by
the language's async/await machinery instead of a direct method call.

## 9. Known production uses

- **nginx.** Each nginx worker process runs one event loop that multiplexes
  every connection assigned to it, choosing the most efficient mechanism the
  platform offers, `epoll` on Linux 2.6 and newer, `kqueue` on the BSD family
  and macOS, documented directly in nginx's own connection-processing
  reference, which lists these methods and states nginx "will normally select
  the most efficient method automatically"
  ([nginx documentation, "Connection processing methods"](https://nginx.org/en/docs/events.html),
  verified 2026-08-02). This is the multi-reactor, multi-thread (here,
  multi-process) variant from dimension 8.
- **Node.js, via libuv.** libuv, the C library originally written for Node.js,
  performs "all (network) I/O ... on non-blocking sockets which are polled
  using the best mechanism available on the given platform, epoll on Linux,
  kqueue on OSX and other BSDs, event ports on SunOS and IOCP on Windows"
  ([libuv design overview documentation](https://docs.libuv.org/en/v1.x/design.html),
  verified 2026-08-02, the same page states libuv "was originally written for
  Node.js"). JavaScript's `EventEmitter`-based socket API is the
  application-facing handler-registration surface sitting on top of this
  single-reactor loop.
- **Netty.** `NioEventLoop` is documented in Netty's own API reference as "a
  `SingleThreadEventLoop` implementation which register the `Channel`'s to a
  `Selector` and so does the multi-plexing of these in the event loop"
  ([Netty 4.1 API, `io.netty.channel.nio.NioEventLoop`](https://netty.io/4.1/api/io/netty/channel/nio/NioEventLoop.html),
  verified 2026-08-02). Netty groups several `NioEventLoop` instances into an
  `EventLoopGroup`, one loop's worth of Java NIO `Selector` per CPU-bound
  worker thread, the multi-reactor variant described in dimension 8.
- **Twisted.** The Twisted networking library for Python names the pattern's
  Initiation Dispatcher role explicitly `reactor`, documented as "the core of
  the event loop within Twisted, the loop which drives applications using
  Twisted," which "works by calling some internal or external event
  provider, which generally blocks until an event has arrived, and then
  calls the relevant event handler"
  ([Twisted documentation, "Reactor Basics"](https://docs.twisted.org/en/stable/core/howto/reactor-basics.html),
  verified 2026-08-02). Twisted is the rare library that literally uses the
  pattern's own name for the object.
- **Java NIO / the JDK.** `java.nio.channels.Selector` is the JDK's built-in
  Synchronous Event Demultiplexer, and its own API documentation describes it
  plainly as "a multiplexor of `SelectableChannel` objects" that maintains a
  registered key set and a selected-key set of channels ready for at least
  one interested operation
  ([Oracle Java SE 21 API, `java.nio.channels.Selector`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/channels/Selector.html),
  verified 2026-08-02).
- **Redis.** Redis's core command execution runs on a single thread, and
  Redis's own FAQ confirms this directly, noting "as of version 4.0, Redis
  has started implementing threaded actions" only for a narrow set of
  background operations, and that scaling across CPUs is achieved by "running
  multiple Redis instances" rather than by threading the main loop
  ([Redis FAQ, "How can Redis use multiple CPUs or cores?"](https://redis.io/docs/latest/develop/get-started/faq/),
  verified 2026-08-02). Redis's core event loop is a textbook single-reactor,
  single-thread implementation, and it is the concrete reason a slow Lua
  script or a large `KEYS *` call stalls every other client talking to that
  Redis instance, the exact failure mode named in dimension 11.

## 10. Consequences

Positive.

- Bounded, predictable memory per connection, no per-connection OS thread
  stack, which is what lets a single machine hold open tens of thousands of
  concurrent connections that would exhaust thread limits under a
  thread-per-connection design.
- No lock contention between connections for shared, connection-agnostic
  state, because only one thread (per reactor instance) ever touches the
  registration table or runs handler code at a time, removing an entire
  category of concurrency bugs from the connection-handling layer itself.
- A natural, cheap backpressure signal, the registered-handle count and the
  time spent per `select` call both directly reflect current load, without
  needing separate instrumentation to derive them.
- Composability with a worker pool (dimension 8) lets the pattern keep its
  memory advantage for the I/O layer while still using multiple cores for
  the actual request work, rather than forcing an all-or-nothing choice.

Negative.

- One slow or blocking handler stalls every connection sharing that reactor
  thread. This is not a rare edge case, it is the pattern's central operating
  constraint, and every production deployment of Reactor lives or dies on
  whether that constraint is respected everywhere in the handler code.
  Cross-reference dimension 11 for the concrete symptom.
- Handler code is written as callbacks or short state-machine steps instead
  of straight-line blocking code, which raises the cost of writing and
  reading correct connection-handling logic, particularly for multi-step
  protocols that a blocking design would express as a simple sequential
  function.
- Debugging tools built around thread stack traces are much less useful. A
  stalled reactor thread's stack trace shows only whatever handler happened
  to be running at the moment of the snapshot, not the history of the
  connections waiting behind it, so root-causing a stall requires different
  tooling than root-causing a deadlocked thread pool.
- A single reactor instance cannot use more than one CPU core, and scaling to
  more cores requires the multi-reactor variant, which introduces its own
  problem, spreading accepted connections evenly across reactor instances
  without creating a hot reactor and several idle ones.

## 11. Failure modes and misuse

- **Symptom.** Every connection served by one process or worker suddenly
  stalls at once, latency spikes across the board, and the process shows one
  thread pinned busy while every other thread (if any exist) sits idle.
  **Cause.** A single handler invocation performed a blocking call, a
  synchronous file read, a blocking database driver call, a `sleep`, or a
  long computation, and the reactor thread cannot return to `select` until
  that handler returns. **Fix.** Move the blocking or CPU-heavy work to a
  worker pool and have the handler only enqueue work and return, per the
  Reactor-plus-worker-pool variant in dimension 8, or replace the blocking
  call with its non-blocking or asynchronous equivalent if one exists.

- **Symptom.** Memory grows without bound over hours or days even though
  connection count is stable, and eventually the process is killed by the
  operating system's out-of-memory mechanism. **Cause.** A handler
  unregisters its socket from the demultiplexer, or the connection is closed
  by the peer, but the application never removes the corresponding entry
  from its own handler table, or never releases the buffer it allocated for
  that connection. The demultiplexer stops delivering events for a closed
  handle, so nothing ever triggers cleanup of the orphaned application-side
  state. **Fix.** Tie handler-object lifetime to handle lifetime explicitly,
  unregister and free application state in the same code path that closes
  the handle, and verify it with the leak-detection technique in dimension
  15.

- **Symptom.** A small percentage of connections silently receive no response
  ever, with no error logged anywhere. **Cause.** A registration race, a new
  handle is registered with the demultiplexer from a thread other than the
  reactor thread while the reactor is inside its `select` call, and the
  underlying OS call does not see the new registration until after its
  current, already-in-flight wait returns, or the registration table update
  itself is not applied atomically with respect to the reactor thread and
  gets silently dropped or applied out of order. **Fix.** Route every
  registration and unregistration through a single mutation point the
  reactor thread itself drains at the top of each loop iteration (a
  thread-safe queue of pending registrations), never mutate the
  registration table directly from another thread.

- **Symptom.** CPU usage on the reactor thread is pegged at or near 100
  percent even though connections are mostly idle, and the process is
  otherwise responsive. **Cause.** The demultiplexer is being called with a
  timeout of zero, or in a tight loop with no blocking wait at all, turning
  what should be an efficient blocking wait into a busy-poll. This is a
  classic beginner mistake when hand-rolling a Reactor, forgetting that the
  entire value of the pattern depends on the demultiplexer call actually
  blocking. **Fix.** Pass a real timeout (or a blocking-indefinitely option
  where the API allows) to the demultiplexer call and confirm with a CPU
  profiler that the reactor thread is asleep, not spinning, between events.

- **Symptom.** Throughput plateaus well below what the hardware should
  support, and adding more worker threads to the application does nothing,
  while a single core is visibly saturated. **Cause.** All connections are
  registered with a single reactor instance and the workload has scaled past
  what one core can dispatch, the multi-reactor variant was never adopted.
  **Fix.** Move to N reactors, one per core, either via `SO_REUSEPORT` at the
  listening socket or by explicitly distributing accepted connections across
  a fixed pool of reactor instances, matching the shape nginx and Netty both
  use in production, per dimension 9.

- **Symptom.** A handler that reads a partial message correctly the first
  time fails intermittently on subsequent reads, sometimes dropping bytes,
  sometimes duplicating them. **Cause.** The handler assumes a single `read`
  call always returns a complete logical message, which is only true for
  small, rarely fragmented payloads, and TCP gives no such guarantee for
  larger or backpressured streams. **Fix.** Buffer partial reads explicitly
  and only hand a complete message to application logic once a
  protocol-defined boundary (a length prefix, a delimiter, a fixed frame
  size) has actually arrived, treating every `read` as delivering an
  arbitrary-length fragment rather than a whole message.

## 12. Trade-off matrix

| Force | Reactor | Thread-per-connection | Proactor | Active Object |
|---|---|---|---|---|
| Memory per idle connection | Low, no dedicated stack | High, one OS thread stack each | Low to moderate, depends on pending-operation buffers | Moderate, a method-request queue entry per pending call |
| Handles CPU-bound handler well | No, stalls the shared thread | Yes, one thread per connection isolates the rest | Depends on the completion-callback thread model | Yes, work runs on the object's own dedicated thread |
| Natural fit for readiness-based OS APIs | Yes, this is its native shape | Not applicable, blocking calls hide readiness entirely | No, natural fit is completion-based APIs (IOCP, io_uring) | Not tied to a specific I/O model |
| Debuggability via thread stack traces | Poor, one snapshot hides queued work | Good, one stack per connection | Poor, similar to Reactor | Moderate, one queue plus one worker thread to inspect |
| Scales across CPU cores unaided | No, needs the N-reactor variant | Yes, naturally, at high thread-count cost | Depends on the OS thread pool backing completions | Yes, if multiple active objects run on separate threads |
| Code reads as sequential logic | No, callback or state-machine shaped | Yes, straight-line blocking code | No, completion-callback shaped | Partially, calls are async but each object's queue runs sequentially |

Proactor is the nearest alternative and the one most often confused with
Reactor, because both solve the same problem (many concurrent I/O-bound
connections on few threads) with the polarity reversed, Reactor waits for
readiness and does the I/O itself, Proactor waits for a completion the
operating system already performed. Thread-per-connection is the model
Reactor exists to displace, and it remains the right answer whenever handler
work is not reliably short (see dimension 4). Active Object solves a
different problem, method calls on an object need to run asynchronously on
that object's own thread, and it is frequently used as the concurrency model
for a worker in the Reactor-plus-worker-pool variant rather than as a
competing choice for the I/O layer itself.

## 13. Related and incompatible patterns

- **Proactor.** The completion-based sibling. Both patterns solve many
  connections, few threads, and both are named and formalized together in
  POSA2. They are largely mutually exclusive as the core dispatch model of a
  single I/O subsystem, a subsystem is naturally built around readiness or
  around completion, not literally both at once, though a library can expose
  one pattern's API while implementing it in terms of the other underneath
  (a common shape on Windows, where Proactor-native IOCP is sometimes used to
  emulate a readiness-style API for portability). The Asio library documents
  itself explicitly as implementing the Proactor pattern through its
  `io_context`, while using a Reactor internally (`select` or `epoll`) on
  platforms without native completion ports, which is the clearest
  documented example of the two patterns coexisting inside one library at
  different layers
  ([Asio core overview](https://think-async.com/Asio/asio-1.30.2/doc/asio/overview/core/async.html),
  verified 2026-08-02).
- **Half-Sync/Half-Async.** Composes directly with Reactor rather than
  competing with it. The reactor thread is the asynchronous layer, a bounded
  worker thread pool is the synchronous layer, and a queue between them is
  the boundary. This is the standard fix for the handler-does-real-work
  non-applicability case in dimension 4.
- **Leader/Followers.** An alternative to the N-reactor variant for spreading
  demultiplexer work across a thread pool without a dedicated reactor thread
  per core, one thread at a time takes the role of the demultiplexing
  leader, hands off leadership before dispatching, and the handoff protocol
  is the pattern's distinguishing feature over simply running N independent
  reactors.
- **Active Object.** Frequently used inside a Reactor's worker layer, each
  worker can itself be structured as an Active Object with its own method
  request queue, decoupling method invocation from method execution the same
  way Reactor decouples event detection from event handling.
- **Observer.** Reactor's dispatch step is a specialized, single-event
  variant of Observer, one event source, one interested handler per
  registration, rather than Observer's usual many-subscribers-per-subject
  shape. Where Observer answers who else needs to know this changed, Reactor
  answers which one handler owns this particular ready handle.
- **Command.** A concrete Event Handler is frequently implemented as a small
  Command object, particularly in the interface-and-subclass variant from
  dimension 8, encapsulating what to do when this handle is ready as a
  standalone, substitutable unit.
- **Template Method.** The Initiation Dispatcher's `handle_events` loop is
  itself a fixed algorithm (wait, then dispatch) with one customizable step,
  which handler runs for which handle, making the overall Reactor loop a
  Template Method whose varying step is filled in per-handle rather than
  per-subclass.
- **Strategy.** The choice of Synchronous Event Demultiplexer implementation,
  select versus poll versus epoll versus kqueue, is a Strategy the Reactor
  selects once at startup based on the running platform, exactly the
  portability layer named in dimension 3.

## 14. Refactoring path in and out

Introducing Reactor into a codebase that currently uses thread-per-connection.

1. Identify the connection-handling loop and separate accepting a connection
   from reading a connection into two distinct responsibilities, even
   before touching threading. This makes the eventual Accept Handler and Read
   Handler split visible in the existing code.
2. Introduce a single non-blocking socket set and a `select` or `epoll` call
   around the existing per-connection read logic for one connection type
   first, while leaving the rest of the system on the old blocking model.
   Prove the demultiplexer wiring works in isolation before converting
   everything at once.
3. Extract an `EventHandler` interface (or, in a language with closures, a
   callback signature) from the logic that currently runs per-connection, and
   move state that used to live on the stack of a blocking thread into an
   explicit per-connection object the handler can find again on the next
   invocation, because the callback returns and is called again later rather
   than running the whole conversation in one stack frame.
4. Build the Initiation Dispatcher's registration table and loop around the
   proven demultiplexer wiring from step 2, and migrate connection types onto
   it one at a time, watching for handlers that secretly block, the single
   most common defect introduced during this migration.
5. Once every connection type is on the reactor, remove the now-dead
   thread-per-connection code path and its associated thread pool
   configuration.

Removing Reactor from a codebase where it has stopped earning its place.

1. Confirm the actual reason for removal. If it is handlers keep blocking
   the loop, the correct fix is usually adopting the Reactor-plus-worker-pool
   variant (dimension 8) rather than removing the pattern outright, since the
   underlying I/O-bound, many-connection shape has not changed.
2. If connection volume has genuinely dropped to a level where
   thread-per-connection is simpler and the thread cost is irrelevant,
   collapse each handler's state machine back into a single linear function
   and restore a blocking read loop, reversing step 3 above.
3. Remove the demultiplexer wiring and the registration table only after the
   blocking version has been verified against the same test suite the
   reactor version used (dimension 15), so a regression in connection
   handling is caught before the reactor code is deleted, not after.

## 15. Testing and verification

Reactor's structure makes one kind of testing easier and one kind
substantially harder, and both should be tested deliberately rather than
assumed.

**Easier.** The demultiplexer boundary is a clean seam. A test can register a
fake, in-memory handle (a pipe, a socket pair, or a purpose-built test double
that reports itself ready on command) and assert exactly which handler fires
and with what arguments, without needing real network sockets or real
timing. Event handler logic itself, given a ready handle and a fixed input
buffer, is deterministic and testable exactly like any other pure function
once it is separated from the loop that calls it, which is a strong argument
for keeping handler logic thin and independently unit-testable rather than
inline inside registration callbacks.

**Harder.** Concurrency between the reactor thread and any other thread that
registers or unregisters handlers (dimension 11's registration-race failure
mode) is exactly the kind of bug that a single test run rarely surfaces,
because it depends on the precise interleaving of the registration call and
the demultiplexer's blocking wait. Stress-test this seam explicitly, spin up
many concurrent registration and unregistration calls from separate threads
against a running reactor and assert, after a bounded settle time, that
every handle that should be registered is dispatched and no handle that was
unregistered ever fires, rather than trusting that the happy-path test
covered it.

**Leak detection.** Because the failure mode in dimension 11 is silent by
nature, an explicit test should open and cleanly close a large number of
connections in sequence (tens of thousands, run against a small,
purpose-built reactor instance in the test process rather than the full
production one) and assert that the registration table's size returns to
its starting count and that process memory does not grow monotonically
across the run, catching an orphaned-handler leak before it reaches
production rather than after.

**Slow-handler injection.** Deliberately register one handler that sleeps or
spins for a fixed, known duration, and assert that every other registered
connection experiences latency of roughly that duration during the sleep and
recovers immediately after. This converts dimension 11's most damaging
failure mode from an incident into a repeatable, assertable test, and it is
the single most valuable test a Reactor-based system can carry, because it is
the one failure mode production traffic will eventually trigger regardless
of how carefully the handler code was reviewed.

**Fairness under load.** With several handles simultaneously ready, assert
that the dispatcher does not starve any one handle indefinitely in favor of
others, some demultiplexer implementations return ready handles in an order
that is not fair across repeated calls under certain patterns of readiness,
and a test that keeps one handle perpetually ready while measuring how long
a second, occasionally-ready handle waits for dispatch will surface a
starvation bug that a single-iteration test cannot.

## 16. Observability signals

- **Event loop lag.** The single most important number to expose. Measure
  the gap between when the demultiplexer call should have returned control
  (based on a timer scheduled just before entering the loop) and when it
  actually did. A healthy reactor shows lag in the low single-digit
  milliseconds or less under normal load. A reactor with a value climbing
  into tens or hundreds of milliseconds is exhibiting the blocking-handler
  failure mode from dimension 11 in real time, whether or not any individual
  request has failed yet.
- **Registered handle count.** A cheap, direct load gauge, the size of the
  Initiation Dispatcher's registration table at any moment. A count that
  grows without the corresponding connection count growing (or without
  connections ever closing) is the leak failure mode from dimension 11
  surfacing before it becomes an out-of-memory incident.
- **Per-handler dispatch duration.** Time each individual handler invocation
  and log or histogram anything past a small threshold, a few milliseconds
  for a supposedly non-blocking handler is already suspicious. This
  identifies which specific handler type is responsible for lag, rather than
  only knowing that lag exists.
- **Demultiplexer wakeup count and ready-set size per wakeup.** A healthy
  reactor under moderate load shows a moderate number of wakeups, each with a
  handful of ready handles. A reactor waking constantly with an empty or
  near-empty ready set is exhibiting the busy-poll failure mode from
  dimension 11 (timeout misconfigured to zero or near-zero).
- **CPU utilization of the reactor thread specifically**, isolated from any
  worker threads, since a saturated reactor thread with idle worker threads
  points directly at the dispatch loop itself rather than at application
  logic, and vice versa.
- **A healthy dashboard** shows low, flat event-loop lag, a registered-handle
  count that tracks real connection count, and a moderate per-wakeup ready
  set. **A failing one** shows a lag graph with a sudden step change (one bad
  deploy introduced a blocking call), a handle count with a slow, monotonic
  climb (a leak), or a wakeup rate pegged high with near-zero ready sets (a
  busy-poll bug).

## 17. Security and privacy implications

**Denial of service through handler cost, not connection count.** Because
every connection shares the same reactor thread, an attacker does not need
to open enough connections to exhaust a resource limit, one connection whose
traffic is crafted to trigger an expensive or blocking code path inside a
single handler invocation can stall every other connection on that reactor.
This is a materially different threat model from thread-per-connection
servers, where the equivalent attack requires exhausting the thread pool
itself, not merely triggering one slow request. Bound every handler's
worst-case execution time explicitly, and route anything that cannot be
bounded to a worker pool, per dimension 4 and dimension 8.

**Slow-loris-style attacks.** A client that opens a connection and sends
data at an artificially slow rate, one byte every few seconds, ties up a
registration table entry and its associated buffer for an extended period
without ever becoming fully idle (so it is not caught by a simple idle
timeout) and without ever completing (so its resources are never released
through the normal close path). A production Reactor needs an explicit,
separate timeout on time-since-connection-opened, not merely
time-since-last-activity, to bound this class of attack, since the naive
idle timeout is exactly what this attack is designed to evade.

**Handler-table poisoning through unbounded registration.** If handle
registration is exposed, even indirectly, to untrusted input (an application
that lets a client-controlled value influence how many auxiliary handles a
single request registers, a fan-out pattern gone wrong), an attacker can
grow the registration table far faster than legitimate traffic would, which
is the leak failure mode from dimension 11, deliberately induced rather than
accidental. Cap the number of handles any single logical client or request
can cause to be registered.

On privacy the pattern is largely neutral, with one practical note. Because
handler dispatch duration and registration-table size are the primary
observability signals (dimension 16), and both can correlate with the volume
or shape of a specific client's traffic, exposing per-connection metrics at
too fine a granularity in shared dashboards or logs can leak information
about one tenant's traffic pattern to operators or dashboards scoped to a
different tenant in a multi-tenant deployment. Aggregate observability
signals across tenants before they leave the reactor's own process boundary,
the same discipline any shared-infrastructure metric needs.

## Code examples

Three languages, chosen because each maps to a real, cited production use
from dimension 9 rather than to an arbitrary language list. Java shows the
interface-and-subclass form directly against the JDK's own `Selector`, the
same primitive Netty builds `NioEventLoop` on. Python shows the
function-valued form against the standard library's `selectors` module,
which is what Twisted's own reactor implementations sit on. TypeScript shows
the pattern as it appears from inside Node.js, where the reactor itself
lives in libuv and application code only ever sees the handler-registration
surface through `EventEmitter`.

### Java

```java
import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.SelectionKey;
import java.nio.channels.Selector;
import java.nio.channels.ServerSocketChannel;
import java.nio.channels.SocketChannel;
import java.util.Iterator;

interface EventHandler {
    void handleEvent(SelectionKey key) throws IOException;
}

final class AcceptHandler implements EventHandler {
    private final ServerSocketChannel server;
    private final Selector selector;

    AcceptHandler(ServerSocketChannel server, Selector selector) {
        this.server = server;
        this.selector = selector;
    }

    public void handleEvent(SelectionKey key) throws IOException {
        SocketChannel client = server.accept();
        if (client == null) {
            return;
        }
        client.configureBlocking(false);
        SelectionKey clientKey = client.register(selector, SelectionKey.OP_READ);
        clientKey.attach(new ReadHandler(client));
    }
}

final class ReadHandler implements EventHandler {
    private final SocketChannel channel;

    ReadHandler(SocketChannel channel) {
        this.channel = channel;
    }

    public void handleEvent(SelectionKey key) throws IOException {
        ByteBuffer buffer = ByteBuffer.allocate(256);
        int read = channel.read(buffer);
        if (read == -1) {
            channel.close();
            key.cancel();
            return;
        }
        buffer.flip();
        channel.write(buffer);
    }
}

public final class Reactor {
    private final Selector selector;
    private volatile boolean running = true;

    Reactor(int port) throws IOException {
        selector = Selector.open();
        ServerSocketChannel server = ServerSocketChannel.open();
        server.bind(new InetSocketAddress(port));
        server.configureBlocking(false);
        SelectionKey acceptKey = server.register(selector, SelectionKey.OP_ACCEPT);
        acceptKey.attach(new AcceptHandler(server, selector));
    }

    void stop() {
        running = false;
        selector.wakeup();
    }

    void eventLoop() throws IOException {
        while (running) {
            selector.select(1000);
            Iterator<SelectionKey> ready = selector.selectedKeys().iterator();
            while (ready.hasNext()) {
                SelectionKey key = ready.next();
                ready.remove();
                if (!key.isValid()) {
                    continue;
                }
                EventHandler handler = (EventHandler) key.attachment();
                handler.handleEvent(key);
            }
        }
    }

    public static void main(String[] args) throws IOException {
        Reactor reactor = new Reactor(0);
        reactor.stop();
    }
}
```

### Python

```python
import selectors
import socket
from typing import Callable

Handler = Callable[[socket.socket], None]


class Reactor:
    def __init__(self) -> None:
        self._sel = selectors.DefaultSelector()
        self._running = False

    def register(self, sock: socket.socket, events: int, handler: Handler) -> None:
        sock.setblocking(False)
        self._sel.register(sock, events, data=handler)

    def unregister(self, sock: socket.socket) -> None:
        self._sel.unregister(sock)

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        self._running = True
        while self._running:
            for key, _mask in self._sel.select(timeout=1.0):
                handler: Handler = key.data
                handler(key.fileobj)  # type: ignore[arg-type]


class EchoServer:
    def __init__(self, reactor: Reactor, host: str, port: int) -> None:
        self._reactor = reactor
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((host, port))
        listener.listen(128)
        reactor.register(listener, selectors.EVENT_READ, self._on_accept)
        self._listener = listener

    def _on_accept(self, listener: socket.socket) -> None:
        client, _addr = listener.accept()
        self._reactor.register(client, selectors.EVENT_READ, self._on_read)

    def _on_read(self, client: socket.socket) -> None:
        data = client.recv(1024)
        if not data:
            self._reactor.unregister(client)
            client.close()
            return
        client.sendall(data)


if __name__ == "__main__":
    reactor = Reactor()
    server = EchoServer(reactor, "127.0.0.1", 0)
    reactor.stop()
```

### TypeScript

```typescript
import * as net from "node:net";

class EchoConnectionHandler {
  constructor(private readonly socket: net.Socket) {
    this.socket.on("data", this.onData);
    this.socket.on("close", this.onClose);
  }

  private onData = (chunk: Buffer): void => {
    this.socket.write(chunk);
  };

  private onClose = (): void => {
    this.socket.removeListener("data", this.onData);
  };
}

function startReactorServer(port: number): net.Server {
  const server = net.createServer((socket) => {
    new EchoConnectionHandler(socket);
  });
  server.listen(port);
  return server;
}

const server = startReactorServer(0);
server.close();
```

The TypeScript sample never calls the demultiplexer or the dispatch loop
directly, because in Node.js both live inside libuv, outside the reach of
JavaScript code entirely. What application code sees is only the handler
registration surface, `server.on`, `socket.on`, which is the Reactor pattern
with its Initiation Dispatcher and Synchronous Event Demultiplexer both
implemented once, in C, and never re-implemented by application authors, the
same relocation described for Go in dimension 8.

## 18. References

1. Douglas C. Schmidt. "Reactor. An Object Behavioral Pattern for
   Demultiplexing and Dispatching Handles for Synchronous Events." In James
   O. Coplien and Douglas C. Schmidt (editors), *Pattern Languages of Program
   Design*. Addison-Wesley, 1995. Title and venue confirmed via
   [Wikipedia's Reactor pattern article](https://en.wikipedia.org/wiki/Reactor_pattern),
   verified 2026-08-02, and Schmidt's own publications page at
   [dre.vanderbilt.edu](https://www.dre.vanderbilt.edu/~schmidt/patterns-ace.html),
   verified 2026-08-02.
2. Douglas C. Schmidt, Michael Stal, Hans Rohnert, Frank Buschmann.
   *Pattern-Oriented Software Architecture, Volume 2. Patterns for Concurrent
   and Networked Objects*. John Wiley and Sons, 2000. ISBN 978-0-471-60695-6.
   Source of the four-participant terminology used in dimension 5 and the
   pairing with Proactor, Half-Sync/Half-Async, Leader/Followers, and Active
   Object. Authors, year, and ISBN confirmed via
   [Wikipedia's Pattern-Oriented Software Architecture article](https://en.wikipedia.org/wiki/Pattern-Oriented_Software_Architecture),
   verified 2026-08-02.
3. Oracle. *Java SE 21 API Specification*, `java.nio.channels.Selector`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/channels/Selector.html
   Verified 2026-08-02. Source for the JDK's built-in Synchronous Event
   Demultiplexer description in dimensions 8 and 9.
4. The Netty Project. *Netty 4.1 API documentation*,
   `io.netty.channel.nio.NioEventLoop`.
   https://netty.io/4.1/api/io/netty/channel/nio/NioEventLoop.html
   Verified 2026-08-02. Source for the Netty production use in dimension 9.
5. Python Software Foundation. *Python 3 documentation*, `selectors` module.
   https://docs.python.org/3/library/selectors.html
   Verified 2026-08-02. Source for the `DefaultSelector` abstraction used in
   the Python code example and dimension 8.
6. F5, Inc. (nginx). *nginx documentation*, "Connection processing methods."
   https://nginx.org/en/docs/events.html
   Verified 2026-08-02. Source for the nginx production use in dimension 9.
7. libuv project. *libuv design overview*.
   https://docs.libuv.org/en/v1.x/design.html
   Verified 2026-08-02. Source for the Node.js and libuv production use in
   dimension 9.
8. Redis Ltd. *Redis documentation*, "Redis FAQ."
   https://redis.io/docs/latest/develop/get-started/faq/
   Verified 2026-08-02. Source for the Redis single-threaded command
   execution claim in dimension 9.
9. Twisted Matrix Labs. *Twisted documentation*, "Reactor Basics."
   https://docs.twisted.org/en/stable/core/howto/reactor-basics.html
   Verified 2026-08-02. Source for the Twisted production use in dimension 9.
10. The Tokio project. *Tokio API documentation*, `tokio::runtime` module.
    https://docs.rs/tokio/latest/tokio/runtime/index.html
    Verified 2026-08-02. Source for the async-task-plus-driver variant in
    dimension 8.
11. Christopher M. Kohlhoff. *Asio C++ Library documentation*, "Core
    Concepts, Proactor Design Pattern."
    https://think-async.com/Asio/asio-1.30.2/doc/asio/overview/core/async.html
    Verified 2026-08-02. Source for the Proactor distinction in dimensions 1,
    4, and 13.
12. unixism.net. "What is io_uring."
    https://unixism.net/loti/what_is_io_uring.html
    Verified 2026-08-02. Source for the submission and completion queue
    description of `io_uring` in dimension 4.
13. The Go Authors. *Go standard library source*, `runtime/netpoll_epoll.go`.
    https://github.com/golang/go/blob/master/src/runtime/netpoll_epoll.go
    Verified 2026-08-02. Source for the Go runtime's internal epoll-based
    network poller described in dimension 8.
