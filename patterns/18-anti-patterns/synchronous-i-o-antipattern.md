---
name: Synchronous I O Antipattern
slug: synchronous-i-o-antipattern
family: 18-anti-patterns
category: Anti-Pattern
aliases: [Blocking I O, Blocking Call, Sync-over-Async, Main Thread I O]
first_described: "industry concurrency practice, no single canonical origin"
maturity: established
related: [reactor, proactor, half-sync-half-async, bulkhead, circuit-breaker, queue-based-load-leveling, chatty-i-o]
incompatible_with: [event-loop-per-request]
verified: 2026-08-02
---

# Synchronous I O Antipattern

## 1. Name, aliases, and lineage

Synchronous I O Antipattern is the practice of performing disk, network,
process, database, DNS, compression, cryptographic, or other wait-heavy input
or output on an execution context that is shared by many units of work. The
name is descriptive. It has no single catalog author comparable to the Gang of
Four patterns. It appears under aliases such as Blocking I O, Blocking Call,
Sync-over-Async, Main Thread I O, and Blocking the Event Loop.

The lineage comes from concurrency and user interface practice rather than from
one book. Event-loop systems warned against it because one blocked loop delays
all work assigned to that loop. Node.js documents an event loop plus worker
pool model and says that a blocked event loop or worker cannot serve other
clients while it is busy
(https://nodejs.org/learn/asynchronous-work/dont-block-the-event-loop,
verified 2026-08-02). Vert.x gives the same rule for its event loops and logs
warnings when an event loop has not returned for too long
(https://vertx.io/docs/vertx-core/java/, verified 2026-08-02). Android
StrictMode detects disk and network access on the application main thread, the
thread that receives UI operations and runs animation work
(https://developer.android.com/reference/android/os/StrictMode, verified
2026-08-02). ASP.NET Core Kestrel has an `AllowSynchronousIO` switch whose
default is false, and Microsoft warns that many blocking synchronous I O
operations can lead to thread pool starvation
(https://learn.microsoft.com/en-sg/aspnet/core/fundamentals/servers/kestrel,
verified 2026-08-02).

This entry is an anti-pattern entry, not a ban on every blocking call. A command
line migration tool can block on a file read and remain correct. A service that
uses one dedicated worker per slow tape drive can block without harming
unrelated requests. The anti-pattern name applies when the wait happens on a
scarce scheduler thread, a UI thread, an event loop, or a request worker pool
whose capacity was planned around fast return to the scheduler.

Engineering judgement. The most useful short test is this. If a thread that
blocks is the same thread that must accept more work from other users, animate a
screen, dispatch callbacks, or free a small request worker pool, the call
belongs under suspicion.

## 2. Problem and context

A service, UI, or runtime handles many independent tasks through a bounded
number of execution contexts. In Node.js the visible JavaScript callbacks run
on one event loop thread, while selected work goes to a worker pool
(https://nodejs.org/learn/asynchronous-work/dont-block-the-event-loop,
verified 2026-08-02). In Vert.x a `Vertx` instance owns several event loops,
and handlers are normally called on an event-loop thread
(https://vertx.io/docs/vertx-core/java/, verified 2026-08-02). In ASP.NET Core,
HTTP request work can consume thread-pool threads, and synchronous request or
response I O is disabled by default in Kestrel
(https://learn.microsoft.com/en-sg/aspnet/core/fundamentals/servers/kestrel,
verified 2026-08-02). In Android, the main thread receives UI events and drives
visible responsiveness (https://developer.android.com/reference/android/os/StrictMode,
verified 2026-08-02).

The problem starts when ordinary code treats those contexts as if each request
or screen action owned an isolated thread. A handler reads a template file with
`readFileSync`. An endpoint loads a large request body through a synchronous
stream. A UI callback performs a network lookup. An event-loop callback waits
on a database client that exposes a blocking API. The call may be simple and
locally readable. Its cost is paid by work that is not local to the function.

The failure rarely arrives as one dramatic line of code. It arrives as tail
latency. A few requests run long, then many requests queue behind them. CPU may
look low because threads are parked in kernel waits. The database may look
normal because the queue is inside the application. Users see frozen screens,
timeouts, slow health checks, or broad request latency spikes that do not map
to one failing dependency.

This context makes the anti-pattern different from Slow I O in general. Slow I
O is a dependency property. Synchronous I O Antipattern is a scheduling
property. The same slow disk read is tolerable in a dedicated background worker
and harmful on a UI thread or event loop. The issue is not the existence of a
blocking API. It is putting that API on a shared path whose contract assumes
quick return.

Two code reviews can reach opposite conclusions about the same line and both
can be correct if they are reviewing different contexts. `Files.readString` in
a Java migration that runs once during release is plain and acceptable.
`Files.readString` in a servlet filter on every request is a capacity decision
hidden inside business code. `Path.read_text` in a Python test helper is fine.
The same call inside an asyncio route handler can pause other coroutines until
the file system returns. `readFileSync` in a Node.js bootstrap script may be
the clearest option. `readFileSync` in a request callback gives one client's
storage wait to every client assigned to that process.

The context also includes call frequency. A blocking call that happens once per
hour on an operator path has a different risk profile from the same call inside
a hot route, a polling loop, or a health check. Health checks deserve special
mention. They are often treated as harmless because they return little data,
but they run during incidents and deploys, exactly when slow disks, DNS, and
remote services are already under stress. A health check that performs blocking
I O on the same pool that serves traffic can make the orchestrator's probing
traffic part of the outage.

## 3. Forces

Engineering judgement. This anti-pattern is a bad balance among real forces,
which is why experienced teams still introduce it.

- **Latency.** Synchronous calls optimize local latency reasoning. The function
  returns when data is available, and errors are raised at the point of use.
  The system loses global latency because other work waits behind that call.
- **Coupling.** Blocking I O couples the caller's scheduler to the callee's
  speed. A file system, DNS resolver, shell command, remote service, or object
  store becomes part of the caller's scheduling budget.
- **Consistency.** The synchronous shape can make state changes easier to
  order. The cost is that consistency is bought by occupying an execution
  context during the wait.
- **Operability.** Stack traces are easier with blocking code because the stack
  still shows the caller. Operability is weaker when queueing moves into the
  runtime and the only external symptom is starvation.
- **Cost.** Blocking code often costs less to write and review. It can cost
  more to run because capacity must cover parked threads, extra instances, and
  retry traffic caused by timeouts.
- **Team topology.** A library team may expose only synchronous APIs because
  they are portable and easy to consume. Application teams then inherit the
  scheduling cost in event-loop, UI, and request-pool runtimes.
- **Cognitive load.** Async control flow adds state machines, cancellation
  paths, and error propagation rules. Blocking control flow is easier to read,
  which tempts teams to ignore where it runs.
- **Failure isolation.** A dedicated blocking pool can contain damage. An
  unbounded shared pool or event loop spreads one slow dependency across every
  request class.

The anti-pattern favors local readability and caller simplicity. It sacrifices
fair scheduling, isolation, and predictable tail latency.

## 4. Applicability and non-applicability

Reach for synchronous I O only when these conditions hold.

- The program is a short-lived command line tool, setup script, migration, test
  fixture, or one-shot batch job where no other user-facing work waits on the
  same thread.
- The call runs in a dedicated worker context whose whole purpose is to wait on
  that device or dependency, and the queue in front of it is bounded.
- The I O happens during process startup before the server accepts traffic or
  before the UI is interactive.
- The platform has no usable non-blocking API for the operation, and a worker
  pool or process pool has been sized, bounded, timed, and instrumented.
- The call is on a cold administrative path with explicit concurrency limits,
  such as a single operator export job.

Do NOT use synchronous I O in the following cases.

- **On an event loop.** Reason. One blocked loop delays all callbacks assigned
  to it. Node.js and Vert.x both document this scheduling constraint in their
  event-loop guidance (https://nodejs.org/learn/asynchronous-work/dont-block-the-event-loop
  and https://vertx.io/docs/vertx-core/java/, verified 2026-08-02).
- **On a UI main thread.** Reason. Input handling, drawing, and animation share
  the same thread. Android StrictMode exists in part to catch disk and network
  work there (https://developer.android.com/reference/android/os/StrictMode,
  verified 2026-08-02).
- **Inside a high-concurrency request handler.** Reason. Parked request
  workers reduce available capacity and can starve the thread pool. Kestrel's
  synchronous I O default of false is one production-facing guardrail for this
  risk (https://learn.microsoft.com/en-sg/aspnet/core/fundamentals/servers/kestrel,
  verified 2026-08-02).
- **Before a timeout, cancellation, or queue limit exists.** Reason. A blocking
  call without a bound can hold capacity longer than any caller or user still
  cares about.
- **Behind an async facade that waits internally.** Reason. Returning a promise,
  future, or coroutine does not make the operation non-blocking if the work has
  already occupied the scheduler thread.
- **In fan-out loops.** Reason. Ten serial blocking calls multiply tail
  latency. Ten concurrent blocking calls can exhaust a pool. Use async fan-out
  with bounded concurrency or move the work to a queue.
- **For per-request file reads of stable assets.** Reason. Load at startup,
  cache with invalidation, or serve through a static file path designed for
  that purpose.
- **As a migration bridge with no exit date.** Reason. Temporary blocking
  adapters tend to become permanent unless a removal path is assigned.

## 5. Structure

The anti-pattern has six participants.

- **Shared execution context.** The event loop, UI thread, request worker,
  reactor thread, or small worker pool that is meant to cycle quickly through
  many tasks.
- **Request or event handler.** The application code running on that context.
  It owns business logic and has a strict scheduling budget, even if the code
  does not say so.
- **Blocking I O call.** A call that waits for a file, network peer, process,
  DNS answer, database operation, or similar external condition before the
  caller can continue.
- **Slow resource.** The device, service, kernel operation, remote process, or
  library that controls when the call returns.
- **Hidden queue.** Work that piles up while the execution context is blocked.
  It may be a socket accept backlog, event queue, HTTP request queue, thread
  pool queue, or user input queue.
- **Affected neighbor.** Another user action or request that did not cause the
  slow I O but waits behind it.

The harmful relationship is not a direct dependency from one request to another.
It is an indirect dependency through the shared execution context. That is why
the bug can escape code review. Each handler reads like a normal, sequential
function, while the scheduler-level coupling lives outside the file.

## 6. ASCII structure diagram

```text
                 shared execution context
      +------------------------------------------------+
      | event loop, UI thread, or request worker pool  |
      +--------------------------+---------------------+
                                 |
                                 | runs
                                 v
      +--------------------------+---------------------+
      | request or event handler                       |
      | reads config, opens socket, runs shell, etc.   |
      +--------------------------+---------------------+
                                 |
                                 | synchronous wait
                                 v
      +--------------------------+---------------------+
      | blocking I O call                              |
      +--------------------------+---------------------+
                                 |
                                 | waits on
                                 v
      +--------------------------+---------------------+
      | slow resource                                  |
      | disk, DNS, DB, remote API, child process       |
      +------------------------------------------------+

      while the wait is active

      +---------------------+      +--------------------+
      | hidden queue        |----->| affected neighbor  |
      | pending work        |      | unrelated request  |
      +---------------------+      +--------------------+
```

## 7. Dynamics

The runtime story is queueing, not syntax. A blocking call that looks local
turns into a scheduler stall.

```text
client A        shared context        slow resource        client B
   |                  |                     |                 |
   | request A        |                     |                 |
   |----------------->|                     |                 |
   |                  | open/read/call      |                 |
   |                  |-------------------->|                 |
   |                  | waits               |                 |
   |                  |=====================|                 |
   |                  |                     | request B       |
   |                  |<--------------------------------------|
   |                  | cannot run B yet    |                 |
   |                  |                     |                 |
   |                  | result              |                 |
   |                  |<--------------------|                 |
   | response A       |                     |                 |
   |<-----------------|                     |                 |
   |                  | now starts B        |                 |
   |                  |-------------------------------------->|
```

In a UI program, replace client B with a click, redraw, or animation frame. In
a server, replace it with a health check or unrelated tenant request. In a
thread pool, the same timeline repeats across all workers until the queue grows
or the pool starves.

An async wrapper changes the timeline only if the wait moves off the shared
context and is bounded. If the wrapper calls a synchronous library before
returning a future, the caller still pays the stall. If it moves work to an
unbounded pool, the event loop may survive while memory, thread count, or the
downstream service becomes the next failure point.

## 8. Implementation variants

**Direct synchronous API call.** The handler calls `readFileSync`, `executeQuery`
on a blocking driver, `execSync`, a synchronous HTTP client, or an equivalent
library method. This is the simplest form and the easiest to grep.

**Sync-over-async wait.** Code calls an async API and then blocks for the result
with a method such as `get`, `join`, `Result`, or a semaphore. The resource may
be non-blocking underneath, but the caller still occupies the scheduler thread.

**Blocking adapter behind an async signature.** A function returns a promise,
future, or coroutine while its body performs blocking work. This variant fools
callers and reviewers because the public shape looks async.

**Offload to a shared worker pool.** The event loop survives, but every slow
call consumes pool capacity. This is acceptable only with a bounded queue,
timeouts, cancellation, and metrics. Python's asyncio documentation shows
`run_in_executor` for file operations that can block the event loop
(https://docs.python.org/3/library/asyncio-eventloop.html, verified
2026-08-02).

**Dedicated bulkhead pool.** Calls to a legacy blocking dependency run in a
small named pool with its own queue and rejection policy. This is often the
right transitional design. It turns an unbounded scheduler stall into a
visible dependency budget.

**Blocking route or worker verticle.** Some frameworks provide a formal escape
hatch. Vert.x Web has `blockingHandler`, called using a worker-pool thread
rather than an event loop (https://vertx.io/docs/vertx-web/java/, verified
2026-08-02). The feature is a containment tool, not a reason to make every
handler blocking.

**Asynchronous kernel or runtime I O.** The call shape changes to callback,
future, promise, coroutine, async stream, or completion event. This removes the
thread wait but adds cancellation, backpressure, ordering, and lifetime rules.

**Preload or cache.** The system reads configuration, templates, certificates,
or lookup tables at startup, then serves requests from memory. This removes
per-request I O when the data changes rarely enough to have a clear reload
rule.

**Async streaming.** Large payloads are read or written as chunks through an
async stream rather than loaded synchronously as one value. This variant matters
when the operation cannot be preloaded, such as uploads, exports, and proxying.
It trades a simple return value for backpressure, partial failure handling, and
resource lifetime management. The benefit is that the scheduler can run other
work between chunks.

**Process isolation.** Some legacy tools expose only command line interfaces.
Running them inline with `execSync` or equivalent calls blocks the caller and
ties request latency to process startup time. A safer shape is a small job
runner process, queue, or pool with limits on concurrency, input size, output
size, wall time, and environment. This does not make the tool fast. It makes
the waiting visible and gives the main service a rejection point.

**Concurrency-cheap runtimes.** Go goroutines and modern virtual-thread models
can make blocking cheaper by reducing the cost of a parked unit of execution.
That changes the threshold, not the principle. A goroutine waiting on a remote
service still consumes memory, holds request state, may hold locks, and can
multiply downstream load. The anti-pattern is weaker in such runtimes, but it
returns when concurrency is unbounded or when blocking work holds scarce
resources.

## 9. Known production uses

**Node.js server guidance and core APIs.** Node.js documents that server code
should avoid blocking the event loop and worker pool. The same page lists
synchronous APIs in modules such as file system, crypto, zlib, and child
process as APIs that are not intended for server request paths
(https://nodejs.org/learn/asynchronous-work/dont-block-the-event-loop,
verified 2026-08-02). This is a named production runtime with an explicit
anti-pattern rule.

**ASP.NET Core Kestrel.** Kestrel's `AllowSynchronousIO` option controls
whether synchronous I O is allowed for request and response bodies, and its
documented default is false. Microsoft warns that a large number of blocking
operations can cause thread pool starvation and an unresponsive app
(https://learn.microsoft.com/en-sg/aspnet/core/fundamentals/servers/kestrel,
verified 2026-08-02). The production use is a default runtime guardrail.

**Android StrictMode.** Android's StrictMode is a developer tool that can catch
disk and network access on the application main thread. The documentation ties
that thread to UI operations and animations, and describes main-thread
responsiveness as a way to avoid Application Not Responding dialogs
(https://developer.android.com/reference/android/os/StrictMode, verified
2026-08-02). The production lesson is enforced during development for Android
apps.

**Eclipse Vert.x.** Vert.x core documentation says its APIs are non-blocking
with few exceptions, and it warns that blocking event loops can halt progress.
It also logs blocked event-loop warnings with stack traces for diagnosis
(https://vertx.io/docs/vertx-core/java/, verified 2026-08-02). Vert.x Web
offers `blockingHandler` for legacy blocking work on worker-pool threads rather
than event-loop threads (https://vertx.io/docs/vertx-web/java/, verified
2026-08-02).

**NGINX thread pools.** NGINX documents a `thread_pool` directive for
multi-threaded reading and sending of files without blocking worker processes
(https://nginx.org/en/docs/ngx_core_module.html, verified 2026-08-02). Its
development guide describes offloading tasks that would otherwise block an
NGINX worker process, including file I O and libraries without asynchronous
interfaces (https://nginx.org/en/docs/dev/development_guide.html, verified
2026-08-02). This is a production web server containment design.

## 10. Consequences

Positive consequences, when the synchronous call is used within its proper
scope.

- Code is linear and easy to step through in a debugger.
- Error handling can use ordinary exceptions or return values at the point of
  use.
- Startup scripts, migrations, and small command line tools avoid async
  machinery they do not need.
- Legacy libraries can be adopted quickly while a bounded worker boundary is
  designed.
- Stack traces often show the full call path without async frame stitching.

Negative consequences, when the anti-pattern appears on shared contexts.

- Tail latency grows for requests that did not perform the slow I O.
- Thread pools starve while CPU appears underused.
- UI frames, input events, and animations stall behind storage or network
  waits.
- Retries amplify load because callers time out while the original work keeps
  holding capacity.
- Failure isolation is weak. One slow dependency can consume all scheduler
  contexts.
- Autoscaling reacts late because queue depth and parked threads can rise
  before CPU saturation.
- Debugging is misleading. The slow resource may look healthy while the
  application queue is the true bottleneck.
- Async APIs above the blocking point inherit the stall and give callers false
  confidence.

## 11. Failure modes and misuse

**Event-loop freeze.** Symptom. All routes on one process pause together,
metrics show event-loop lag, and logs show a synchronous file, child-process,
DNS, or crypto call in a callback. Cause. A wait-heavy operation ran on the
event loop. Fix. Replace it with a non-blocking API, preload the data, or move
the work to a bounded worker pool with a timeout.

**Thread pool starvation.** Symptom. Request latency climbs, health checks time
out, CPU stays moderate or low, and thread count or queue depth rises. Cause.
Many request workers are parked in synchronous I O. Fix. Use async I O through
the request path, or isolate the legacy client behind a small bulkhead with
fast rejection.

**UI application not responding.** Symptom. Taps, window paint, scrolling, or
animation stop during a file, database, or network operation. Cause. I O ran on
the main UI thread. Fix. Move the operation to a background worker and marshal
only UI updates back to the main thread.

**Async facade that still blocks.** Symptom. Callers await a function that
appears async, but event-loop lag or worker starvation remains. Cause. The
function performs blocking work before returning its future or promise. Fix.
Make the underlying client non-blocking, or make the offload explicit and
bounded.

**Unbounded offload.** Symptom. Event-loop lag improves while memory, thread
count, context switching, or downstream load explodes. Cause. Blocking work was
moved to an unbounded executor. Fix. Set a hard pool size, bounded queue,
timeout, cancellation policy, and rejection path.

**Serial fan-out.** Symptom. A request with many items is much slower than a
request with one item, and latency grows linearly with item count. Cause. A loop
performs blocking I O one item at a time. Fix. Batch, cache, or run async calls
with bounded concurrency.

**Hidden startup regression.** Symptom. Deployment or cold start becomes slow
after adding certificate, template, schema, or config loads. Cause. Synchronous
I O moved from request time to startup without a startup budget or readiness
gate. Fix. Keep startup preload, but measure it, fail fast on missing files,
and expose readiness only after preload completes.

**Missing cancellation.** Symptom. Clients give up, but server threads continue
waiting on old I O and consume capacity. Cause. The synchronous API has no
caller cancellation path. Fix. Use an API that accepts cancellation or run the
call in a process or pool where timed abandonment and capacity limits are
enforced.

## 12. Trade-off matrix

| Force | Synchronous I O Antipattern | Non-blocking I O | Dedicated bulkhead pool | Queue-based load leveling | Preload and cache |
|---|---|---|---|---|---|
| Local readability | High. Linear call flow | Medium. Async state and callbacks | Medium. Caller sees offload | Medium. Caller sees enqueue | High after startup |
| Tail latency | Poor on shared contexts | Good when backpressure exists | Good until the bulkhead fills | Good for accepted async work | Good for cached reads |
| Coupling to dependency speed | Strong | Medium. Await still observes delay | Contained to one pool | Decoupled by queue | Shifted to reload path |
| Consistency | Simple within one call | Requires async ordering rules | Same as blocking call | Often eventual | Depends on cache policy |
| Operability | Poor unless scheduler is measured | Good with spans and event-loop lag | Good with per-pool metrics | Good with queue metrics | Good with hit and reload metrics |
| Cost to implement | Low | Medium to high | Medium | Medium to high | Medium |
| Failure isolation | Poor | Medium | Strong for one dependency | Strong across time | Strong for stable data |
| Team topology | Pushes cost to runtime owners | Requires async contracts across teams | Allows legacy boundary | Requires producer and consumer ownership | Requires data ownership |
| Cancellation | Often poor | Good when API supports it | Medium. Depends on worker API | Good before dequeue | Not applicable for hot reads |
| Best fit | Small tools, startup, isolated jobs | High-concurrency request paths | Legacy blocking dependency | Slow work that need not finish inline | Stable data read often |

Reading of the table. Non-blocking I O is the preferred shape for request and
event-loop paths. A dedicated bulkhead pool is the transition shape for a
blocking dependency that cannot yet be replaced. Queue-based load leveling is
the right answer when the caller does not need the result inline. Preload and
cache win when the data is stable enough to remove per-request I O.

## 13. Related and incompatible patterns

- **Reactor.** Synchronous I O on a reactor thread conflicts with the reactor's
  core loop. The reactor demultiplexes readiness and dispatches handlers. A
  handler that blocks prevents dispatch for other ready events.
- **Proactor.** Proactor designs complete operations asynchronously and notify
  completion handlers later. They replace the wait with a completion event,
  which addresses the scheduling problem at the cost of async state management.
- **Half-Sync Half-Async.** This pattern can contain blocking work by separating
  an async event layer from a synchronous service layer behind a queue. It is a
  mitigation when synchronous code must remain.
- **Bulkhead.** A named pool with a bounded queue is a bulkhead for blocking
  dependencies. It keeps one slow dependency from consuming the main scheduler.
- **Circuit Breaker.** Circuit breakers pair with bulkheads. Once blocking
  calls begin timing out or filling the queue, the breaker can reject early.
- **Queue-Based Load Leveling.** If a user does not need a result during the
  same request, queueing the work avoids holding request capacity.
- **Chatty I O.** Chatty I O and synchronous I O often appear together. Chatty
  I O is about too many calls. This anti-pattern is about where waiting occurs.
  A system can have one blocking call that is harmful, or many async calls that
  are chatty.
- **Event-Loop-per-Request.** Treating an event loop as if it were a private
  request thread conflicts with reactor and Vert.x style runtimes. It removes
  the economy those runtimes were chosen for.

## 14. Refactoring path in and out

Introducing the repair.

1. Locate synchronous I O on shared paths with static search first. Look for
   names such as `Sync`, `blocking`, `execute`, `join`, `get`, `Result`,
   `wait`, `sleep`, and synchronous stream reads.
2. Classify each call by context. Startup, command line, request path, event
   loop, UI thread, worker pool, and background job have different budgets.
3. Add measurement before changing behavior. Record scheduler lag, queue depth,
   thread pool usage, call duration, timeout count, and caller route.
4. Remove easy per-request file I O by preloading stable data at startup with a
   readiness gate and a reload rule.
5. Replace direct synchronous clients with non-blocking clients where the
   runtime supports them.
6. For clients that cannot change, create a dedicated bulkhead pool per
   dependency. Set maximum threads, queue length, timeout, cancellation, and
   rejection behavior.
7. Change fan-out loops to batch calls or to bounded async concurrency.
8. Push work that does not need an inline answer through a queue and return an
   accepted status or job identifier.
9. Add tests and alerts from dimensions 15 and 16 before deleting the old path.

The smallest useful refactoring is often not "make the whole service async."
It is "make this wait honest." An honest wait has a name, a timeout, a
concurrency limit, and a metric. Once those exist, the team can decide whether
to keep the blocking dependency behind a bulkhead, replace it with a true async
client, precompute the data, or move the workflow behind a queue. Without that
first boundary, all choices blur together and every incident becomes a search
through stack dumps.

For a brownfield service, migrate by route value rather than by file count.
Pick one hot route with a visible blocking call. Add a fast-path benchmark or
load test that includes one slow dependency response and one cheap unrelated
request. Make the cheap request stay cheap. That target prevents a common
mistake: replacing one blocking call with an async call while leaving another
blocking step in the same route. The route is repaired only when unrelated work
no longer waits behind its slow dependency.

Removing a repair when synchronous I O becomes acceptable again.

1. Confirm the path is no longer shared by user-facing work, or that concurrency
   is externally limited to the worker count.
2. Confirm the resource has a bounded latency contract or a timeout controlled
   by the caller.
3. Replace the async or worker boundary only where the simpler synchronous code
   reduces real maintenance cost.
4. Keep the metric. A future move may put the call back onto a shared path.
5. Delete unused pools, queue wiring, and adapters in the same change so the
   system does not retain a fake isolation boundary.

Named refactorings that often apply are Substitute Algorithm for replacing a
blocking client path, Extract Function for isolating the I O call, Replace
Temp with Query when preloaded data should be read through a query method, and
Replace Conditional with Polymorphism when different dependencies need distinct
bulkhead policies.

## 15. Testing and verification

Engineering judgement. Unit tests that assert returned values are not enough.
This anti-pattern is about scheduler behavior, so tests must include time,
queueing, and context.

- **Static guard tests.** Add lint or repository checks that reject forbidden
  synchronous API names in event-loop, UI, or request-handler directories.
- **Context tests.** In UI and event-loop frameworks, assert that blocking
  adapters are not called from the main context. Android StrictMode is one
  platform tool for surfacing such calls during development
  (https://developer.android.com/reference/android/os/StrictMode, verified
  2026-08-02).
- **Concurrency tests.** Run many concurrent requests through a handler while
  the dependency is delayed. A healthy async path keeps accepting unrelated
  cheap requests. A blocking path makes cheap requests wait behind slow ones.
- **Timeout tests.** Simulate a dependency that never returns and assert the
  caller releases capacity through timeout, cancellation, or rejection.
- **Bulkhead tests.** Fill the dedicated pool and queue, then assert new work
  fails fast with the intended status rather than spilling into the main pool.
- **Fan-out tests.** Use fake dependencies with controlled delay to show that
  item count does not multiply latency without a bound.
- **Startup tests.** When preloading replaces request-time I O, test missing
  files, corrupt files, reload failure, and readiness behavior.

Test doubles that fit the problem are fake slow resources, controllable clocks,
bounded executors with small capacities, and probes that record which thread or
event loop executed a call. Avoid sleeps in tests when the framework offers
manual clocks or latches. Where sleeps are unavoidable, use short deadlines and
make the test assert a clear queueing property rather than a fragile exact
duration.

## 16. Observability signals

Record signals at the scheduler boundary and at the I O boundary. One without
the other leaves the diagnosis incomplete.

- Event-loop lag or main-thread stall duration.
- Thread-pool active count, queued work, completed work, and rejection count.
- Per-dependency blocking call duration, tagged by route, operation, and
  dependency.
- Timeout count and cancellation count.
- Bulkhead queue depth, pool saturation, and rejected submissions.
- Request latency split by cheap routes and slow routes. Cheap routes getting
  slower during slow dependency periods is a strong starvation signal.
- UI frame time, input latency, and main-thread StrictMode violations for
  client applications.
- Startup preload duration and readiness time when moving I O out of requests.

A healthy dashboard shows low event-loop lag, bounded pool queues, flat cheap
route latency while slow routes wait, and rejection before global starvation.
A failing dashboard shows rising queue depth, growing tail latency across
unrelated routes, low CPU with many blocked threads, increasing timeout and
retry counts, or blocked-event-loop warnings. Vert.x documents automatic
blocked-thread warnings with stack traces for this class of diagnosis
(https://vertx.io/docs/vertx-core/java/, verified 2026-08-02).

Log with care. The operation name and dependency label are useful. Full file
paths, URLs, command lines, SQL text, and request bodies can expose secrets or
personal data. Prefer stable route and operation labels, and attach detailed
values only under a controlled debug mode.

A useful dashboard layout has three rows. The first row is user-visible
latency by route or screen action, with p50, p95, and p99. The second row is
scheduler health, event-loop lag, main-thread stalls, active workers, queued
workers, and rejected work. The third row is dependency wait time, split by the
operation that caused the wait. When the first row degrades and the third row
shows one slow dependency, the fault may be external. When the first row
degrades across unrelated routes while the second row shows scheduler pressure,
the application is amplifying the dependency delay.

Metrics should distinguish "waiting" from "working." CPU samples, allocation
profiles, and database dashboards can miss parked threads. Thread states,
executor queues, event-loop delay, and blocked-call spans show the missing
half. In incident review, ask whether the system was slow because the resource
was slow, or because the wait happened in the wrong place. The remediation is
different.

## 17. Security and privacy implications

The anti-pattern has a real availability risk. Node.js explicitly connects
blocked event-loop or worker threads with denial of service risk when crafted
input can make a thread block
(https://nodejs.org/learn/asynchronous-work/dont-block-the-event-loop,
verified 2026-08-02). The same principle applies outside Node.js. If a client
can control file size, path count, DNS names, URLs, decompression input, regex
input, or subprocess arguments, the client may be able to hold scarce execution
contexts and deny service to other users.

Privacy risks are indirect. Blocking I O often appears in logging, export,
template, and diagnostic paths because those paths feel operational rather than
product-facing. When such code blocks, teams may raise log detail to diagnose
it and accidentally record paths, URLs, payload fragments, command lines, or
customer identifiers. Treat blocking-call telemetry as production data. Bound
cardinality, redact arguments, and keep high-detail traces behind short
retention.

Integrity risks come from timeout confusion. A caller may time out and retry
while the blocking operation continues. If the operation performs a write, the
system can create duplicates or apply changes after the user has moved on. Use
idempotency keys, cancellation-aware APIs, and explicit completion records for
write operations that were moved behind worker pools or queues.

Engineering judgement. A repair can introduce a new attack surface. Worker
pools, queues, and subprocess wrappers need limits. Without them, the fix for
event-loop blocking can become a memory exhaustion path or a process-spawning
denial of service path.

## 18. References

1. Node.js Project. "Don't Block the Event Loop (or the Worker Pool)." Node.js
   Learn documentation. https://nodejs.org/learn/asynchronous-work/dont-block-the-event-loop.
   Verified 2026-08-02. Source for Node.js event-loop and worker-pool guidance,
   synchronous API cautions, and denial-of-service framing.
2. Microsoft. "Kestrel web server in ASP.NET Core." Microsoft Learn.
   https://learn.microsoft.com/en-sg/aspnet/core/fundamentals/servers/kestrel.
   Verified 2026-08-02. Source for Kestrel `AllowSynchronousIO` default and
   thread-pool starvation warning.
3. Google. "StrictMode." Android API reference.
   https://developer.android.com/reference/android/os/StrictMode. Verified
   2026-08-02. Source for detecting disk and network access on the application
   main thread and for main-thread responsiveness guidance.
4. Eclipse Vert.x Project. "Vert.x Core." https://vertx.io/docs/vertx-core/java/.
   Verified 2026-08-02. Source for Vert.x event-loop blocking guidance and
   blocked-thread warning behavior.
5. Eclipse Vert.x Project. "Vert.x Web." https://vertx.io/docs/vertx-web/java/.
   Verified 2026-08-02. Source for `blockingHandler` running work on a worker
   pool rather than an event loop.
6. Python Software Foundation. "Event loop." Python 3 asyncio documentation.
   https://docs.python.org/3/library/asyncio-eventloop.html. Verified
   2026-08-02. Source for `loop.run_in_executor` and its use with blocking file
   operations.
7. NGINX. "Core functionality." NGINX documentation.
   https://nginx.org/en/docs/ngx_core_module.html. Verified 2026-08-02. Source
   for the `thread_pool` directive and file I O offload.
8. NGINX. "Development guide." NGINX documentation.
   https://nginx.org/en/docs/dev/development_guide.html. Verified 2026-08-02.
   Source for offloading tasks that would otherwise block NGINX worker
   processes.

## Code examples

The examples use TypeScript, Python, Go, and Swift because they show four
common runtime shapes. TypeScript shows event-loop blocking and the async
replacement. Python shows an asyncio executor boundary for legacy blocking file
work. Go shows containment with a bounded worker pool, even though goroutines
make blocking cheaper than OS-thread-per-request designs. Swift shows an async
facade that moves legacy file work into a detached task.

### TypeScript

```typescript
const { readFileSync } = require("node:fs");
const { readFile } = require("node:fs/promises");

function badConfigValue(path: string): string {
  return readFileSync(path, "utf8").trim();
}

async function goodConfigValue(path: string): Promise<string> {
  const text = await readFile(path, "utf8");
  return text.trim();
}

async function demo(): Promise<void> {
  const path = process.argv[2] ?? "config.txt";
  console.log(badConfigValue(path));
  console.log(await goodConfigValue(path));
}

demo().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
```

### Python

```python
import asyncio
from pathlib import Path


def load_text_blocking(path: str) -> str:
    return Path(path).read_text(encoding="utf-8").strip()


async def load_text(path: str) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, load_text_blocking, path)


async def main() -> None:
    Path("config.txt").write_text("blue\n", encoding="utf-8")
    print(await load_text("config.txt"))


if __name__ == "__main__":
    asyncio.run(main())
```

### Go

```go
package main

import (
	"fmt"
	"os"
	"strings"
)

type Job struct {
	Path  string
	Reply chan Result
}

type Result struct {
	Text string
	Err  error
}

func worker(jobs <-chan Job) {
	for job := range jobs {
		data, err := os.ReadFile(job.Path)
		job.Reply <- Result{Text: strings.TrimSpace(string(data)), Err: err}
	}
}

func main() {
	_ = os.WriteFile("config.txt", []byte("green\n"), 0o600)
	jobs := make(chan Job, 2)
	go worker(jobs)

	reply := make(chan Result, 1)
	jobs <- Job{Path: "config.txt", Reply: reply}
	result := <-reply
	if result.Err != nil {
		panic(result.Err)
	}
	fmt.Println(result.Text)
}
```

### Swift

```swift
import Foundation

func loadTextBlocking(_ url: URL) throws -> String {
    let text = try String(contentsOf: url, encoding: .utf8)
    return text.trimmingCharacters(in: .whitespacesAndNewlines)
}

func loadText(_ url: URL) async throws -> String {
    try await Task.detached {
        try loadTextBlocking(url)
    }.value
}

@main
struct Demo {
    static func main() async throws {
        let url = URL(fileURLWithPath: "config.txt")
        try "violet\n".write(to: url, atomically: true, encoding: .utf8)
        print(try await loadText(url))
    }
}
```
