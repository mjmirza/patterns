---
name: Busy Front End
slug: busy-front-end
family: 18-anti-patterns
category: Anti-Pattern
aliases: [CPU-Bound Work on the Web Tier, Fire-and-Forget Contention]
first_described: "Microsoft Azure Architecture Center performance antipatterns catalog, authored by claytonsiemens77, dated 2017-06-05"
maturity: canonical
related: [queue-based-load-leveling, throttling, priority-queue, bulkhead, competing-consumers, circuit-breaker, busy-database, chatty-i-o]
incompatible_with: []
verified: 2026-08-02
---

# Busy Front End

## 1. Name, aliases, and lineage

The canonical name for this anti-pattern is Busy Front End. It is documented
under that exact name by Microsoft's Azure Architecture Center, inside the
same catalog of ten cloud performance anti-patterns that also names Busy
Database. The page states the problem in one sentence. "Performing
asynchronous work on a large number of background threads can starve other
concurrent foreground tasks of resources, decreasing response times to
unacceptable levels." The page metadata records the author as
claytonsiemens77, with an original publication date of 2017-06-05 and a most
recent content update of 2026-06-12
([Azure Architecture Center, Busy Front End antipattern](https://learn.microsoft.com/en-us/azure/architecture/antipatterns/busy-front-end/),
verified 2026-08-02).

The word "front end" in this name is a source of genuine confusion, and this
entry addresses it directly because the confusion is common enough to derail
a reader's understanding of the whole pattern. In the Azure Architecture
Center's usage, and in the usage of every source cited in this entry, front
end means the request-handling tier of a server-side system, the web role,
the API host, the ASP.NET or Express or Flask process that accepts an
incoming HTTP request and returns a response. It does not mean a browser, a
single-page application, or client-side JavaScript running on a person's
device. The companion anti-pattern in the same Azure catalog, Busy Database,
names the data tier one hop further back. Busy Front End names the compute
tier one hop in front of it, the tier a client actually talks to. A reader
coming from web development, where "front end" usually means the browser
side of a client-server split, should mentally substitute "web tier" or
"request-handling tier" everywhere this entry says front end, because that is
the concept the name actually points at.

No independently citable source under this exact name predates the Azure
catalog entry, and this entry states that plainly rather than inventing an
earlier origin, following the same judgement-versus-sourced-claim convention
this repository applies throughout. The underlying idea, that spawning
CPU-bound work on a background thread inside a request-handling process still
consumes the resources that process needs to serve other requests, is older
and is a specific, named instance of a more general concern that operating
systems and runtime engineers call thread pool starvation or, in a
narrower .NET-specific framing, "sync over async" turned inside out. This
entry keeps that broader term distinct from the anti-pattern's own name in
its alias list, because thread pool starvation is a mechanism, something that
can happen for several different reasons, while Busy Front End names one
specific, common way a team causes it, spawning genuinely CPU-bound
processing on a background thread that shares a process with request
handling, rather than moving that processing to a separate tier entirely.

## 2. Problem and context

The context is a server-side application built as, or converged into over
time, a single deployable process that does two structurally different jobs
at once, accepting and answering client requests, and running whatever
business logic those requests trigger. Azure's own framing names this
directly as the root cause. "This problem typically occurs when an
application is developed as monolithic piece of code, with all of the
business logic combined into a single tier shared with the presentation
layer"
([Azure Architecture Center, Busy Front End antipattern](https://learn.microsoft.com/en-us/azure/architecture/antipatterns/busy-front-end/),
verified 2026-08-02).

The specific problem this entry names has a shape that is easy to miss
because it looks, at the point a developer writes it, like the correct
solution to a different and real problem. A developer notices that a
particular request handler, uploading a file that needs virus scanning and
thumbnailing, generating a PDF report, recalculating a set of derived
values, takes several seconds of CPU-bound work to complete. Blocking the
calling thread on that work for the whole request would make the endpoint
feel slow and would tie up one request-handling slot for the whole duration.
The instinctively correct-feeling fix is to launch the work on a background
thread inside the same process and return an immediate response, an HTTP 202
Accepted, to the caller. The endpoint now responds in milliseconds. Load
testing it alone, with one user, confirms the fix worked.

What that fix does not change is where the CPU-bound work actually runs. It
still runs inside the same operating system process, competing for the same
finite pool of CPU cores and, on many runtimes, the same finite pool of
worker threads that the process also uses to accept and process the next
incoming request. Azure's own explanation of the mechanism is precise about
this. "Resource-intensive tasks can increase the response times for user
requests and cause high latency... However, tasks that run on a background
thread still consume resources. If there are too many of them, they can
starve the threads that are handling requests"
([Azure Architecture Center, Busy Front End antipattern](https://learn.microsoft.com/en-us/azure/architecture/antipatterns/busy-front-end/),
verified 2026-08-02). The page defines resource broadly on purpose, noting
in an inline aside that "the term resource can encompass many things, such as
CPU utilization, memory occupancy, and network or disk I/O" (same source,
verified 2026-08-02), because the contention is not limited to CPU cycles
alone. it can equally be exhaustion of a fixed thread pool, of available
memory, or of open file or socket handles that the request-handling code path
also needs.

A second recurring context, common enough that it appears in Microsoft's own
worked example, is a team correcting one mistake by walking directly into
this one. A synchronous, blocking endpoint is identified as the cause of poor
responsiveness, and the fix is described internally as "make it async."
Wrapping the CPU-bound work in a background thread or an unawaited task
technically satisfies that instruction, the calling code no longer blocks,
but it silently converts a per-request latency problem into a system-wide
throughput and contention problem that only appears once real, concurrent
production traffic arrives, which is the gap between a one-user demo
and a production incident that this entry's dimension 11 returns to.

## 3. Forces

Perceived per-request latency versus aggregate system throughput. Moving
work to a background thread makes the individual request that triggered it
feel instant, because the calling code returns before the work is done. That
gain is entirely local to the one request. Every other concurrent request
against the same process pays a cost, because the background work is still
consuming CPU cycles or thread-pool slots those other requests need, and
under load the aggregate cost is what a user actually experiences as the
system getting slow.

Simplicity of an in-process fix versus the operational cost of a separate
tier. Spawning a thread or an unawaited task is a one-line change inside the
same codebase, the same deployment, the same process. A queue and a worker
tier is a second deployable, a message broker or managed queue service, a
second thing to monitor and keep running. The force toward the simple,
in-process fix is strongest under deadline pressure, which is precisely when
it is least likely to be caught by review or by a single-user load test.

Async as a concurrency primitive versus async as a growth strategy for
capacity. `await`, `Task.Run`, a spawned goroutine, and a Python thread are
all genuine, correct tools for not blocking a calling thread while waiting on
I/O, a network call, a disk read, a database round trip, because the thread
is idle during that wait and can serve other work in the meantime. None of
them create new CPU capacity. Applying the same vocabulary, background,
asynchronous, non-blocking, to CPU-bound work quietly elides the difference,
because the underlying resource being contended, the processor itself, has
not grown, only the appearance of blocking has been removed from the
caller's perspective.

Ease of adding instances on the two sides of the boundary. The
request-handling tier and a decoupled worker tier both can, in principle, add
more instances under load. The force that makes them different in practice
is that a request-handling tier's instance count is usually driven by
request volume or by latency SLOs on the client-facing endpoints, while a
worker tier's instance count can be driven by queue depth, a signal that
tracks the actual backlog of CPU-bound work directly. Keeping the work on the
front end couples two different growth signals into one control knob, so the
team's autoscaling rule for the client-facing tier now has to also account
for background work it was never designed to measure.

Cost of infrastructure versus cost of overprovisioned front-end capacity. A
message queue and a worker fleet are additional line items on a cloud bill.
The alternative, silently accepted in the Busy Front End shape, is
overprovisioning the front-end tier to absorb both jobs, which is usually the
more expensive path at high traffic, because the front end is typically
provisioned for the peak concurrent request volume the client-facing SLO
demands, and adding CPU-bound work to that same fleet means paying
front-end-tier prices, often bundled with a stateful web server license or a
higher per-instance cost, for capacity that a purpose-built worker fleet
could provide more cheaply. This entry treats the specific magnitude of that
cost delta as engineering judgement, since it depends heavily on the hosting
platform and instance pricing, but the direction of the trade-off, that a
dedicated worker tier is usually cheaper per unit of CPU-bound work than an
overprovisioned request-handling tier, is a widely observed one.

## 4. Applicability and non-applicability

There is no case in which running genuinely CPU-bound work on a
request-handling process, in a way that grows with client traffic, is the
right long-term structure. The applicability list below is therefore about
when an in-process background thread is a defensible, temporary, or
genuinely low-risk choice, not an endorsement of the anti-pattern itself.

- A single-tenant, low-traffic internal tool where the team has measured, not
  assumed, that peak concurrent CPU-bound requests will never exceed a
  handful at once, and where a latency spike affecting every user
  simultaneously during that rare peak is an acceptable, explicitly accepted
  risk rather than an unnoticed one.
- A short, bounded, genuinely brief unit of background work, well under the
  size of the CPU spikes Azure's own example uses, where the team has load
  tested the actual concurrent-user behavior, not only the single-request
  behavior, and confirmed the aggregate CPU cost stays well below the
  process's available headroom at expected peak concurrency.
- A prototype or an early-stage product where the team has explicitly and
  visibly decided to defer the queue-and-worker investment until real
  traffic data justifies it, with a specific, tracked follow-up rather than
  a silent, permanent decision.

## Non-applicability, when not to run background work in the request-handling process

- Any CPU-bound task whose volume grows with client traffic, image
  processing, report generation, PDF rendering, video transcoding,
  recalculating derived data, virus scanning, because the anti-pattern's
  cost grows exactly as fast as the load the system is trying to serve,
  which is the worst possible growth curve for a shared, contended resource.
- Any task running inside a process that also serves latency-sensitive,
  unrelated endpoints, because the whole point of the anti-pattern's failure
  mode is that unrelated foreground traffic degrades even though nothing
  about that traffic changed. Azure's own worked example makes this
  explicit, an unrelated `GET` endpoint's response time degrades purely
  because of concurrent load on a different `POST` endpoint sharing the same
  process
  ([Azure Architecture Center, Busy Front End antipattern](https://learn.microsoft.com/en-us/azure/architecture/antipatterns/busy-front-end/),
  verified 2026-08-02).
- A workload that must survive a front-end instance restart or crash without
  losing in-flight work. A background thread's state dies with the process.
  A durable queue's messages do not.
- A workload the team wants to grow, throttle, prioritize, or retry
  independently of the client-facing tier. All four of those operational
  controls require the work to be a distinct, separately observable unit,
  which an in-process background thread is not.
- Any I/O-bound wait, a network call, a database query, a call to a
  downstream service, mistaken for the kind of work this anti-pattern
  targets. Azure's own guidance is explicit that the fix is not to avoid
  asynchronous code altogether. "This doesn't mean you should avoid
  asynchronous operations. Performing an asynchronous await on a network
  call is a recommended practice... The problem here is that CPU-intensive
  work was spawned on another thread"
  ([Azure Architecture Center, Busy Front End antipattern](https://learn.microsoft.com/en-us/azure/architecture/antipatterns/busy-front-end/),
  verified 2026-08-02). An `await` on a network call frees the underlying
  thread while it waits, it does not consume CPU during that wait, and
  treating it the same as a CPU-bound background spawn is a category error
  this entry's dimension 11 returns to as a specific, common misuse.

## 5. Structure

- The Client, a browser, a mobile app, or another service, that issues a
  request and, in the anti-pattern's shape, receives an immediate,
  misleadingly fast acknowledgment while the actual work is still pending.
- The Front End Process, the request-handling tier, the web role, API host,
  or application server, that in a healthy structure does nothing but
  accept, validate, and route requests, and in this anti-pattern
  additionally hosts and executes CPU-bound background work inside the same
  process boundary.
- The Shared Resource Pool, the operating system threads, the CPU cores, and
  on many runtimes a fixed-size managed thread pool, that every concurrent
  request handler and every spawned background task inside the same process
  draws from. This is the actual bottleneck. it is shared, finite, and
  invisible to a single-request view of the system.
- Concurrent Foreground Requests, the unrelated, latency-sensitive requests
  that arrive at the same process while background work is executing, and
  that pay the cost of the anti-pattern without themselves doing anything
  wrong.
- In the corrected structure, two additional participants appear. a Durable
  Queue, sitting between the front end and the work, and a Worker Tier, a
  separately deployed, independently managed process or fleet that pulls
  from the queue and performs the CPU-bound work entirely outside the front
  end's resource pool.

## 6. ASCII structure diagram

```
Busy Front End structure, work stays on the shared pool

  +----------+   HTTP request     +---------------------------------+
  |  Client  | -----------------> |         Front End Process        |
  |          | <----------------- |  accepts request, spawns work    |
  +----------+  fast "Accepted"   |  on a background thread inside   |
                                  |  the SAME process                |
                                  |                                   |
                                  |   +---------------------------+   |
                                  |   |   Shared Resource Pool    |   |
                                  |   |  (CPU cores, thread pool) |   |
                                  |   |                           |   |
                                  |   |  [foreground request A]   |   |
                                  |   |  [foreground request B]   |   |
                                  |   |  [background CPU work]  <-+---+-- starves A and B
                                  |   +---------------------------+   |
                                  +---------------------------------+

Corrected structure, work moves to an independent tier

  +----------+   HTTP request     +----------------+     +----------+
  |  Client  | -----------------> |   Front End    | --> |  Durable |
  |          | <----------------- |  (thin, only   |     |  Queue   |
  +----------+  fast "Accepted"   |   accepts and  |     +----+-----+
                                  |   enqueues)     |          |
                                  +----------------+          |
                                                               v
                                                       +----------------+
                                                       |  Worker Tier   |
                                                       |  (separate     |
                                                       |   process,     |
                                                       |   grows on     |
                                                       |   queue depth) |
                                                       +----------------+
```

## 7. Dynamics

```
Sequence under rising concurrent load, Busy Front End shape

500 users        100 users            Front End Process
(UserProfile GET) (WorkInFrontEnd POST)     |
   |------GET-------->|                     |
   |<--fast reply------|                     | ~500 req/s sustained,
   |------GET-------->|                     | light load only
   |<--fast reply------|                     |
   |                    |------POST--------->|
   |                    |<--202 Accepted------|  spawns background
   |                    |                     |  thread, CPU rises
   |------GET-------->| (queued behind       |
   |     ... slower ... contended process)   |
   |<---reply, slower---|                     |
   |                    |------POST--------->|
   |------GET-------->|                     |
   |    ... slower ... (throughput falls    |
   |<---reply, slower---| toward ~150 req/s) |
   |                    |------POST--------->|
   |------GET-------->|                     |
   |<--reply, slowest--| CPU near 100%,      |
   |                    | GET throughput     |
   |                    | keeps dropping     |

Microsoft's own load test reproduced this exact shape. GET throughput held
near 500 requests per second under a constant load of 500 users until a step
load of 100 additional users began sending POST requests; GET throughput then
fell toward roughly 150 requests per second and kept declining as POST volume
rose, purely because both request types shared one process's CPU
(Azure Architecture Center, Busy Front End antipattern, verified 2026-08-02).

After moving the POST handler's work onto a Service Bus queue drained by a
separate worker, the same load pattern produced a much larger volume of
handled requests over a comparable window, rising from roughly 2,759
requests to roughly 23,565 requests in Microsoft's own before-and-after
comparison, with front-end CPU utilization never reaching saturation
(same source, verified 2026-08-02).
```

## 8. Implementation variants

The concrete shapes this anti-pattern takes across runtimes, ordered roughly
from most to least common in this author's experience, labeled as judgement
rather than a sourced ranking, since no single survey of relative frequency
across languages was found to cite.

Fire-and-forget on the framework's own thread pool. In .NET, `new Thread(...)`
started from inside a controller action, or an unawaited `Task.Run(...)`,
both put CPU-bound work directly into contention with the ASP.NET Core
process. Azure's own pseudocode example is exactly this shape, a `Post`
method that starts `new Thread(() => { Thread.SpinWait(...) })` and returns
immediately
([Azure Architecture Center, Busy Front End antipattern](https://learn.microsoft.com/en-us/azure/architecture/antipatterns/busy-front-end/),
verified 2026-08-02).

Async void or unawaited async calls treated as background work. `async void`
handlers, or an `async Task` method whose returned task is deliberately left
unawaited so the caller does not wait for it, are a common way this pattern
appears in modern C# and Node.js code, because both languages make it
syntactically easy to start work without waiting on it, and the syntax gives
no visual signal that the started work is CPU-bound rather than I/O-bound.

Thread pool starvation via genuinely long-running work sharing the request
pool. David Fowler's ASP.NET Core diagnostic guidance, maintained under
Microsoft's own GitHub organization structure and widely referenced in the
.NET community for exactly this failure class, states the underlying
mechanism directly. "Stealing a thread-pool thread for long-running work is
bad since it takes that thread away from other work that could be done"
([davidfowl, AspNetCoreDiagnosticScenarios, AsyncGuidance.md](https://github.com/davidfowl/AspNetCoreDiagnosticScenarios/blob/master/AsyncGuidance.md),
verified 2026-08-02), and recommends either a dedicated background thread
with `IsBackground = true` for genuinely long blocking work, or, more
directly, moving the work off the request-handling process entirely
onto a queue, which is this entry's core prescribed fix.

Python threads used for CPU-bound work under the Global Interpreter Lock. A
`threading.Thread` spawned from inside a Flask or FastAPI request handler to
run a CPU-bound function does not gain parallelism, because CPython's Global
Interpreter Lock serializes bytecode execution across threads in one
process, so the spawned thread still contends directly with the interpreter
thread serving other requests for the same limited execution slots, and, on
a WSGI or ASGI server configured with multiple worker processes rather than
threads, a CPU-bound thread inside one worker process still starves every
request that worker is separately assigned.

Goroutines with no bound on concurrent CPU-bound work. Go's runtime
multiplexes goroutines onto a limited number of OS threads governed by
`GOMAXPROCS`, and a CPU-bound goroutine, one that runs tight computation
without a function call the runtime's cooperative preemption can interrupt
at, competes for that same limited thread pool with the goroutines handling
concurrent HTTP requests via the standard library's `net/http` server. The
symptom is the same as the .NET case, request latency rising under
concurrent CPU-bound load, expressed through a different scheduler.

In-process background services doing scheduled or triggered CPU work.
.NET's `BackgroundService` and `IHostedService`, Node's `setInterval` or
`worker_threads` used incorrectly, and equivalent hosted-background
constructs in other frameworks, run inside the same process as the web
server by design, which is exactly right for lightweight, bounded
housekeeping and exactly the anti-pattern when the hosted work is
CPU-intensive and grows with request volume rather than running on a fixed
schedule independent of traffic.

## 9. Known production uses

Microsoft's Azure Architecture Center documents a concrete, measured
reproduction of the anti-pattern, built specifically to demonstrate it. An
ASP.NET Web API application exposing a `UserProfile` GET controller and a
`WorkInFrontEnd` POST controller that spawns a CPU-bound background thread
using `Thread.SpinWait`, deployed as an Azure App Service. Under a load test
holding a constant 500 users against the GET endpoint, throughput remained
near 500 requests per second until a step load of 100 additional users began
issuing POST requests, at which point GET throughput fell toward roughly 150
requests per second and continued declining, while CPU and network telemetry
captured via AppDynamics showed CPU utilization climbing toward saturation.
After rewriting the POST handler to enqueue a message to an Azure Service Bus
queue and moving the actual CPU-bound work to a separate worker process
reading from that queue, the same test topology handled a substantially
larger volume of requests over a comparable interval, rising from
approximately 2,759 to approximately 23,565, with CPU utilization on the
front end never reaching 100 percent
([Azure Architecture Center, Busy Front End antipattern](https://learn.microsoft.com/en-us/azure/architecture/antipatterns/busy-front-end/),
verified 2026-08-02).

Heroku's own platform documentation encodes the fix for this exact
anti-pattern as a first-class architectural primitive available to every
production application hosted on the platform, the web dyno and worker dyno
split. Heroku's Dev Center states the rationale for the split directly.
"Handling long-running work with background workers has many benefits. It
avoids tying up your web dynos, preventing them from serving other requests,
and keeps your site snappy"
([Heroku Dev Center, Background Jobs and Queueing](https://devcenter.heroku.com/articles/background-jobs-queueing),
verified 2026-08-02). The same documentation names the specific failure this
protects against, timeouts on the web-facing dyno caused by other work
competing for its process capacity, which is a platform-level, named
production instance of the same resource-contention mechanism Azure's
worked example demonstrates, generalized across every application built on
the platform rather than confined to one Azure customer engagement.

Microsoft's own ASP.NET Core team, through the widely referenced diagnostic
guidance repository maintained by David Fowler, a Microsoft engineer on the
ASP.NET Core team, documents the identical underlying resource-contention
mechanism as a recurring, real production failure pattern in ASP.NET Core
applications specifically, independent of the Azure catalog entry. The
guidance states plainly that stealing a thread-pool thread for long-running
work removes that thread from other work the same process needs to perform,
and recommends offloading genuinely long-running or CPU-bound work away from
the shared thread pool that also serves incoming requests
([davidfowl, AspNetCoreDiagnosticScenarios, AsyncGuidance.md](https://github.com/davidfowl/AspNetCoreDiagnosticScenarios/blob/master/AsyncGuidance.md),
verified 2026-08-02). The repository is maintained specifically as a
collection of real diagnostic scenarios observed in ASP.NET Core production
applications, which makes it independent, cross-platform evidence, distinct
from a single vendor's own worked example, that this failure mode recurs
across real deployed systems built on this specific runtime.

## 10. Consequences

Positive, when the anti-pattern is the shape a team ships, deliberately or
accidentally.

- The individual request that triggers the CPU-bound work returns to the
  caller almost immediately, which reads as a fast, well-engineered endpoint
  in isolation.
- No new infrastructure is required. the fix is a code change inside the
  existing deployable, with no message broker, no second process, and no
  additional service to provision, monitor, or pay for.
- The change is fast to write and fast to ship, which is genuinely valuable
  under deadline pressure for a low-traffic feature.

Negative, and the reason this shape is named as an anti-pattern rather than a
neutral trade-off.

- Response times for entirely unrelated endpoints degrade non-linearly as
  concurrent CPU-bound load rises, because the contention is on a shared
  resource pool, not on anything specific to the endpoint a client is
  actually calling.
- The failure is invisible to the exact kind of testing a team is most
  likely to run under time pressure, a single request against the
  background-work endpoint, because contention by definition requires
  concurrent load to manifest.
- The system's effective throughput limit is set by whichever tier is
  weakest under the combined load, request handling and background CPU work
  together, rather than by the request-handling tier's own, independently
  known capacity.
- Recovering from saturation under this shape is expensive. thread pool
  exhaustion, unbounded queued work inside the process, or out-of-memory
  conditions from an unbounded number of spawned threads can turn into
  the process becoming entirely unresponsive rather than merely slow, at
  which point client-visible errors, HTTP 500 or HTTP 503 responses, replace
  degraded latency.
- Adding more instances of the front-end tier, the team's natural first
  instinct under an incident, does not fix the underlying contention,
  because each new instance recreates the same shared-pool problem at its
  own, smaller measure, and the team pays for additional front-end capacity
  that is structurally the wrong tier to add.

## 11. Failure modes and misuse

Symptom. Response times for a completely unrelated, previously fast endpoint
climb sharply under moderate concurrent load, and the endpoint that
degraded has no code changes in the deployment that introduced the
regression. Cause. A different endpoint in the same process spawns
CPU-bound background work per request, and the two endpoints are silently
coupled through the shared resource pool even though nothing in the code
references that coupling directly. Fix. Move the CPU-bound work to a
separate, independently deployed worker tier behind a durable queue, per
Queue-Based Load Leveling, and confirm the fix by re-running a concurrent
load test against both endpoints together, not against either endpoint in
isolation.

Symptom. End users report intermittent HTTP 500 or HTTP 503 errors, or
requests time out, specifically during periods of higher traffic, and the
application's own logs show exceptions related to thread creation or a
thread-pool queue length metric growing without bound. Cause. An unbounded
number of background threads or unawaited tasks are being spawned, one per
incoming request, with no cap on concurrent background work, so the process
eventually exhausts an operating-system or runtime-imposed limit on
concurrent threads. Fix. Bound the concurrency explicitly, either by
introducing a fixed-size worker pool with backpressure, or, preferably, by
moving the work off the process entirely onto a queue whose depth becomes
an explicit, monitorable signal rather than an invisible internal one.

Symptom. A load test performed by a single tester, or an automated test
suite issuing requests sequentially, shows no performance problem, but the
identical endpoint degrades badly once real concurrent production traffic
arrives. Cause. The anti-pattern's cost is a function of concurrent load on
a shared resource pool, so any test methodology that never generates
genuine concurrency against the affected endpoint structurally cannot
reveal it, regardless of how many total requests the test issues over time.
Fix. Load test with realistic concurrent user counts before shipping any
"make it async" fix for a CPU-bound endpoint, mirroring the two-phase
before-and-after methodology Microsoft's own worked example uses, a
constant baseline load plus a concurrent step load against the suspected
endpoint.

Symptom. A team responds to a performance incident by adding more instances
of the front-end tier, and the incident's latency symptoms persist or the
cloud bill rises sharply without a proportional improvement in response
time. Cause. Each new front-end instance recreates the same in-process
contention between foreground requests and background CPU work at its own,
smaller measure, so adding more of the wrong tier increases total capacity
without removing the coupling that caused the degradation, and the team is
now paying front-end-tier prices for capacity that a purpose-built worker
tier would provide more cheaply. Fix. Diagnose which tier is actually
CPU-bound before adding capacity, using per-process CPU and thread-pool
telemetry rather than aggregate request latency alone, and grow the worker
tier, not the front end, once the work has been correctly separated.

Symptom. A developer converts a slow, synchronous endpoint to `async` and
the endpoint's own measured latency improves, but the team later discovers
the "fix" made overall system throughput worse, not better, once it reached
production. Cause. The developer correctly identified that the endpoint was
blocking, but treated `async` as a synonym for "moves work off the CPU,"
when in fact `async` only frees a thread during a genuine I/O wait, network,
disk, database. Wrapping CPU-bound computation in `Task.Run` or an
unawaited task does not create new CPU capacity, it only changes which line
of code appears not to block. Fix. Separate the diagnosis explicitly. an
I/O-bound wait is correctly fixed with `await` on the existing thread. a
CPU-bound computation is correctly fixed by moving the work to a different
tier, never by merely rescheduling it within the same process.

## 12. Trade-off matrix

| Force | Busy Front End (in-process background thread) | Throttling alone, no queue | Queue-Based Load Leveling (the corrected shape) |
|---|---|---|---|
| Perceived latency for the triggering request | Lowest, appears instant because the caller does not wait for real completion | Can reject the request outright once a limit is hit, which is honest but user-visible | Low, an enqueue is a fast, bounded operation, and completion is reported separately |
| Behavior of unrelated foreground requests under load | Degrades non-linearly, coupled to background CPU work through the shared resource pool | Protected from the specific offending caller, but still shares the process with any background work that gets through | Fully decoupled, unrelated requests never contend with the background work at all |
| Where the CPU-bound work actually executes | Inside the request-handling process, on the shared thread pool | Inside the request-handling process, on the shared thread pool, only less often | On an independent worker tier, sized and watched on its own signal |
| Operational complexity to introduce | Lowest, a code change inside the existing deployable | Low to moderate, a rate limiter and a policy for what happens to rejected requests | Higher, a durable queue, a worker deployable, and monitoring for queue depth and dead letters |
| Resilience to a front-end instance crash or restart | None, in-flight background work is lost with the process | Same as Busy Front End for any work that was accepted before the limit engaged | Durable, a properly configured queue retains unprocessed messages across a worker or front-end restart |
| Independent growth signal for the CPU-bound work | None, it grows implicitly with front-end instance count | None, same limitation, throttling only bounds how much gets in | Queue depth, a direct, explicit, monitorable measure of backlog |
| Best fit | Never, as a permanent production shape, only as a knowingly accepted, temporary, low-traffic exception | A useful complement once a queue exists, to protect the queue's producers from a single caller, not a substitute for one | The default correct shape for any CPU-bound work whose volume grows with client traffic |

## 13. Related and incompatible patterns

Queue-Based Load Leveling is the direct, prescribed fix for this
anti-pattern, and Azure's own guidance names it as such in a single sentence.
"Use queue-based load leveling to buffer requests and process them at an
appropriate pace on a separate back end. This situation shouldn't be
addressed with additional scaling of the front end"
([Azure Architecture Center, Busy Front End antipattern](https://learn.microsoft.com/en-us/azure/architecture/antipatterns/busy-front-end/),
verified 2026-08-02). The queue decouples the rate at which work arrives
from the rate at which it is processed, which is precisely the coupling this
anti-pattern's failure mode depends on
([Azure Architecture Center, Queue-Based Load Leveling pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/queue-based-load-leveling),
verified 2026-08-02).

Competing Consumers describes the shape of the worker tier on the far side
of that queue, multiple independent worker instances pulling from the same
queue so the worker tier itself can add capacity to match backlog, which is
what makes the corrected structure actually elastic rather than merely
moved.

Throttling and Priority Queue are complementary, not substitutes. Azure's
own Throttling pattern documentation explicitly cross-references load
leveling as one of the strategies throttling can compose with, describing
"load leveling" as smoothing "activity volume by using a queue," and names
Priority Queue as the way to differentiate which queued work gets processed
first when tenants or callers have different service levels
([Azure Architecture Center, Throttling pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/throttling),
verified 2026-08-02). Applying throttling to the front end without also
introducing a queue reduces how often the anti-pattern's failure mode
triggers, by rejecting some callers outright, but it does not change where
accepted CPU-bound work actually executes, so it mitigates the symptom
without correcting the structure.

Bulkhead is a partial, in-process mitigation for the rare, explicitly
accepted case named in dimension 4, where background work must temporarily
stay in-process. isolating the background work's thread pool or resource
quota from the pool serving foreground requests prevents total starvation,
though it does not remove the underlying coupling the way moving the work to
a separate tier does, and this entry treats Bulkhead as a stopgap rather than
a resolution.

Busy Database is this anti-pattern's sibling in the same Azure catalog, one
tier further back in a typical request path. both name the same underlying
mechanism, general-purpose processing migrating onto the least flexible,
most shared tier available, applied to a different tier in each case. A
system can exhibit both simultaneously, a request handler that both spawns
CPU-bound background work in-process and pushes formatting logic into the
database, and the two anti-patterns compound rather than cancel.

Chatty I/O names a different failure entirely, too many network round trips
between tiers, rather than too much CPU work concentrated on one tier, and
this entry flags the distinction because Azure's own worked example notes a
team correcting Chatty I/O or Extraneous Fetching by consolidating work into
a single call can walk directly into Busy Front End or Busy Database if that
consolidated work is CPU-bound and lands on the wrong tier.

## 14. Refactoring path in and out

Introducing the anti-pattern, the path a team walks in practice, almost
always without intending to create a permanent structural problem.

1. A request handler is identified as slow because it performs genuine,
   real, CPU-bound work inline, and the team's stated goal is simply "make
   the endpoint respond faster."
2. A developer wraps the CPU-bound work in a background thread, an
   unawaited task, or a fire-and-forget call, and the endpoint's own
   measured response time drops from seconds to milliseconds.
3. The change is verified with a single manual test or a lightweight,
   sequential automated test, neither of which generates concurrent load
   against the endpoint, and the fix ships as a clear win.
4. Traffic grows, or a marketing push, a seasonal spike, or simple organic
   growth increases concurrent usage of the endpoint that triggers the
   background work.
5. Unrelated endpoints sharing the same process begin showing latency
   regressions that nobody connects to the earlier change, because the
   earlier change's own commit history shows an improvement, not a
   regression, in the one endpoint it touched.

Removing the anti-pattern, staged so the fix can be verified at each step
rather than shipped as one large, risky change.

1. Confirm the diagnosis before writing any fix. capture CPU and thread-pool
   utilization on the front-end process during a load test that combines a
   steady baseline of unrelated traffic with a step load specifically
   against the suspected background-spawning endpoint, mirroring Microsoft's
   own two-phase test methodology, and confirm the unrelated traffic's
   latency degrades in step with the background load.
2. Identify every code path in the process that spawns a thread, an
   unawaited task, or an in-process hosted background service whose
   workload volume grows with request volume, since a single endpoint is
   rarely the only offender once a team starts looking.
3. Introduce a durable queue, a managed service such as Azure Service Bus,
   Amazon SQS, or a self-hosted broker, and change the identified endpoint
   to enqueue a message describing the work rather than performing or
   spawning it directly. The endpoint's contract with its caller should
   already look like an acknowledgment, an HTTP 202 with a status or
   tracking identifier, which this refactor preserves rather than changes.
4. Build a separate worker deployable that consumes from the queue and
   performs the actual CPU-bound work, entirely outside the front-end
   process's resource pool, following the Competing Consumers shape so the
   worker tier itself can grow with backlog rather than being a single
   point of contention in its own right.
5. If the original endpoint's contract requires reporting completion or a
   result back to the caller, add an explicit status or result channel, a
   polling endpoint, a webhook, or a push notification, since a queue is a
   one-way communication mechanism and does not itself provide a response
   path back to the original caller.
6. Re-run the exact concurrent load test from step 1 against the corrected
   structure and confirm both that unrelated foreground traffic no longer
   degrades under the same background load, and that the background work
   itself still completes correctly, before removing the old, in-process
   code path.
7. Add monitoring for queue depth and processing latency on the worker
   tier, since the failure mode has not disappeared, it has moved to a
   place where it is now an explicit, observable backlog rather than an
   invisible, in-process contention effect, and an unmonitored, growing
   queue is its own, quieter incident waiting to happen.

## 15. Testing and verification

Testing that this anti-pattern is present, or that a fix removed it,
requires deliberately generating concurrent load, because the entire failure
mechanism is a property of contention under concurrency and is invisible to
any test that exercises the suspected endpoint alone. A single-request
integration test can verify the endpoint's own response shape and status
code, but it cannot verify the absence of Busy Front End, because absence of
degradation under isolation says nothing about behavior under contention.

The correct test methodology mirrors Microsoft's own two-phase approach, a
sustained baseline load of unrelated, latency-sensitive requests, combined
with a separate, deliberately varied step load against the suspected
CPU-bound endpoint, while capturing per-tier CPU utilization, thread-pool
queue length, and end-to-end latency for both traffic streams
([Azure Architecture Center, Busy Front End antipattern](https://learn.microsoft.com/en-us/azure/architecture/antipatterns/busy-front-end/),
verified 2026-08-02). A test that shows the baseline traffic's latency
tracking the step load's volume, rising and falling together even though the
two traffic streams are logically unrelated, is a positive, confirmed
diagnosis of the anti-pattern.

Once a fix moves the CPU-bound work behind a queue, testing shifts to two
separate concerns that were previously conflated inside one process. First,
the front-end enqueue operation itself should be tested the way any
I/O-bound operation is, with a fake or in-memory queue client substituted in
unit tests, and a contract test against the real queue service in an
integration environment, verifying the enqueue call returns quickly and
independent of downstream processing time. Second, the worker's consumption
logic should be tested independently, with the queue itself mocked or
replaced by a local, in-memory equivalent, verifying the worker correctly
processes a message, handles a malformed message by routing it to a dead
letter path rather than looping indefinitely, and behaves correctly under at
least one redelivery of the same message, since most managed queue services
provide only at-least-once delivery and a consumer that is not idempotent
will double-process a redelivered message.

A regression test worth keeping permanently, given how easily this
anti-pattern reintroduces itself, is a lightweight concurrency smoke test
run in CI. issue a burst of concurrent requests against a known
latency-sensitive endpoint while a separate, simulated CPU-bound task is
deliberately triggered in the background, and assert that the
latency-sensitive endpoint's response time stays within a fixed budget. Such
a test will not catch every instance of the anti-pattern, but it catches the
specific, recurring mistake of introducing a new in-process background
thread that shares the process with an endpoint the team has already
decided must stay fast.

## 16. Observability signals

The single most direct signal is per-process CPU utilization correlated
against a breakdown of which logical operation is running at the moment
utilization rises, rather than CPU utilization alone, because a busy front
end and a healthy, simply high-traffic front end can look identical on a
bare CPU graph. Instrumenting each request handler and each background task
with its own duration and resource-consumption metric, the same
instrumentation approach Microsoft's own diagnosis walkthrough uses, is what
turns an aggregate CPU spike into an attributable one
([Azure Architecture Center, Busy Front End antipattern](https://learn.microsoft.com/en-us/azure/architecture/antipatterns/busy-front-end/),
verified 2026-08-02).

Thread-pool queue length, on runtimes that expose it, is a leading indicator
that arrives before user-visible latency does. a rising queue of work
waiting for an available thread means the pool is already saturated even
if individual requests have not yet started timing out. On .NET this is
exposed through `ThreadPool` metrics and event counters, and the general
diagnostic guidance this entry cites in dimension 9 is built specifically
around reading that signal correctly rather than reacting only to visible
latency.

End-to-end latency percentiles, specifically p95 and p99 rather than an
average, split by endpoint, are the client-facing symptom to watch. Azure's
own detection guidance names the concrete downstream signals a team should
expect once the front end is genuinely saturated. "End users are likely to
report extended response times or failures caused by services timing
out... These failures could also return HTTP 500 (Internal Server) errors
or HTTP 503 (Service Unavailable) errors... Dependent services, such as
database or storage, start to throttle requests... HTTP queue length metric
grows"
([Azure Architecture Center, Busy Front End antipattern](https://learn.microsoft.com/en-us/azure/architecture/antipatterns/busy-front-end/),
verified 2026-08-02).

Once a fix introduces a queue and a worker tier, the observability surface
changes shape rather than disappearing. queue depth over time, the age of
the oldest unprocessed message, worker-tier CPU and error rates, and
dead-letter queue depth all become the new signals that matter, and a
healthy corrected system shows front-end CPU staying flat under the same
load that previously caused it to spike, with the queue depth graph
absorbing the burst instead.

## 17. Security and privacy implications

This anti-pattern's most direct security implication is availability, not
confidentiality. because unrelated foreground endpoints degrade purely as a
function of concurrent CPU-bound background load, an attacker who can
trigger the CPU-bound code path repeatedly, an unauthenticated upload
endpoint, a public report-generation endpoint, a search feature that
triggers heavy computation, has a low-cost, application-layer denial of
service vector against every other endpoint the same process serves, not
merely against the endpoint they are directly calling. This is a materially
different risk profile from a normal capacity-planning concern, because the
blast radius extends to functionality the attacker never directly touches.

Moving CPU-bound work behind a queue narrows, but does not eliminate, this
concern, and introduces a related one of its own. an unauthenticated or
weakly rate-limited producer can still flood the queue itself, which shifts
the denial-of-service surface from the front end's CPU to the queue's
storage and to the worker tier's processing capacity, and an unbounded
queue can itself become an unmonitored, silently growing liability rather
than a visible incident. Authorization and rate limiting at the point of
enqueue, not only at the point of processing, remain necessary regardless of
which tier ultimately does the work.

On data handling, this entry finds no distinct implication beyond what
already applies to whatever payload the background work operates on. a
message placed on a queue carries the same sensitivity as the request that
produced it, and a team moving work from an in-process background thread to
a queued, external message broker should apply the same encryption,
retention, and access-control review to the queue and the worker tier that
already applies to the front end, since the data has moved to a new system
boundary even though its sensitivity has not changed.

## 18. References

- [Azure Architecture Center, Busy Front End antipattern](https://learn.microsoft.com/en-us/azure/architecture/antipatterns/busy-front-end/), Microsoft Learn, authored by claytonsiemens77, original date 2017-06-05, updated 2026-06-12, verified 2026-08-02.
- [Azure Architecture Center, Performance testing and antipatterns index](https://learn.microsoft.com/en-us/azure/architecture/antipatterns/), Microsoft Learn, verified 2026-08-02.
- [Azure Architecture Center, Busy Database antipattern](https://learn.microsoft.com/en-us/azure/architecture/antipatterns/busy-database/), Microsoft Learn, verified 2026-08-02.
- [Azure Architecture Center, Queue-Based Load Leveling pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/queue-based-load-leveling), Microsoft Learn, verified 2026-08-02.
- [Azure Architecture Center, Throttling pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/throttling), Microsoft Learn, verified 2026-08-02.
- [Heroku Dev Center, Background Jobs and Queueing](https://devcenter.heroku.com/articles/background-jobs-queueing), Salesforce/Heroku, verified 2026-08-02.
- [davidfowl, AspNetCoreDiagnosticScenarios, AsyncGuidance.md](https://github.com/davidfowl/AspNetCoreDiagnosticScenarios/blob/master/AsyncGuidance.md), GitHub, verified 2026-08-02.
- [AWS, Message Queue Benefits](https://aws.amazon.com/message-queue/), Amazon Web Services, verified 2026-08-02.

## Code examples

Three languages are shown because the anti-pattern's mechanism differs
meaningfully by runtime. Node.js contends for a single event-loop thread,
Python contends under the Global Interpreter Lock even with genuine OS
threads, and Go contends for a `GOMAXPROCS`-bounded pool of OS threads
shared across goroutines. Each example pairs the anti-pattern with its
corrected, queue-based shape. All three were compiled or run directly
before inclusion.

### TypeScript, Node.js

The anti-pattern. CPU-bound work is scheduled with `setTimeout`, which looks
non-blocking but still executes on the single thread the HTTP server would
use to accept the next connection.

```typescript
function spinCpu(ms: number): void {
  const end = Date.now() + ms;
  while (Date.now() < end) {
    // busy loop standing in for report generation or image work
  }
}

function handleWork(id: number): void {
  setTimeout(() => {
    spinCpu(50);
    console.log(`work ${id} finished inline, front end was blocked`);
  }, 0);
}

for (let i = 0; i < 3; i++) {
  handleWork(i);
}
console.log("requests accepted immediately, work still queued on same process");
```

The fix. Work is handed to a queue and drained by a separate consumer,
representing a worker process reading from Service Bus, SQS, or Redis.

```typescript
interface Job {
  id: number;
}

class WorkQueue {
  private jobs: Job[] = [];

  enqueue(job: Job): void {
    this.jobs.push(job);
    console.log(`accepted job ${job.id}, handed to queue, front end free`);
  }

  drainOnWorker(process: (job: Job) => void): void {
    let job: Job | undefined;
    while ((job = this.jobs.shift())) {
      process(job);
    }
  }
}

function spinCpu(ms: number): void {
  const end = Date.now() + ms;
  while (Date.now() < end) {}
}

const queue = new WorkQueue();
for (let i = 0; i < 3; i++) {
  queue.enqueue({ id: i });
}
console.log("front end has returned control to the next request already");
queue.drainOnWorker((job) => {
  spinCpu(50);
  console.log(`worker finished job ${job.id}, off the request path`);
});
```

### Python

The anti-pattern. A `threading.Thread` spawned per request looks
asynchronous, but CPython's Global Interpreter Lock means it still
serializes against every other thread in the same interpreter.

```python
import threading
import time


def spin_cpu(ms: int) -> None:
    end = time.monotonic() + ms / 1000
    while time.monotonic() < end:
        pass  # stands in for report or export work


def handle_request(request_id: int) -> None:
    t = threading.Thread(target=spin_cpu, args=(80,))
    t.start()
    print(f"request {request_id} accepted, thread spawned on same process")


for i in range(3):
    handle_request(i)
print("front end reports success immediately, CPU is still contended")
```

The fix. Work is enqueued and drained by a separate worker, representing an
RQ, Celery, or SQS-triggered consumer running outside the request process.

```python
from collections import deque
from dataclasses import dataclass
import time


@dataclass
class Job:
    job_id: int


class WorkQueue:
    def __init__(self) -> None:
        self._jobs: deque[Job] = deque()

    def enqueue(self, job: Job) -> None:
        self._jobs.append(job)
        print(f"accepted job {job.job_id}, handed to queue, front end free")

    def drain_on_worker(self, process) -> None:
        while self._jobs:
            process(self._jobs.popleft())


def spin_cpu(ms: int) -> None:
    end = time.monotonic() + ms / 1000
    while time.monotonic() < end:
        pass


queue = WorkQueue()
for i in range(3):
    queue.enqueue(Job(i))
print("front end has returned control to the next request already")
queue.drain_on_worker(
    lambda job: (spin_cpu(80), print(f"worker finished job {job.job_id}"))
)
```

### Go

The anti-pattern. A goroutine spawned per request still competes for the
same `GOMAXPROCS`-bounded pool of OS threads the `net/http` server uses to
serve every other request.

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

func spinCPU(d time.Duration) {
	end := time.Now().Add(d)
	for time.Now().Before(end) {
		// busy loop standing in for formatting or aggregation work
	}
}

func handleRequest(id int, wg *sync.WaitGroup) {
	go func() {
		defer wg.Done()
		spinCPU(50 * time.Millisecond)
		fmt.Printf("request %d finished inline on the same process\n", id)
	}()
}

func main() {
	var wg sync.WaitGroup
	for i := 0; i < 3; i++ {
		wg.Add(1)
		handleRequest(i, &wg)
	}
	fmt.Println("front end accepted all requests immediately")
	wg.Wait()
}
```

The fix. A channel stands in for a durable queue, and a separate drain loop
stands in for an independently deployed worker.

```go
package main

import (
	"fmt"
	"time"
)

type job struct {
	id int
}

func spinCPU(d time.Duration) {
	end := time.Now().Add(d)
	for time.Now().Before(end) {
	}
}

func main() {
	queue := make(chan job, 10)
	for i := 0; i < 3; i++ {
		queue <- job{id: i}
		fmt.Printf("accepted job %d, handed to queue, front end free\n", i)
	}
	close(queue)
	fmt.Println("front end has returned control to the next request already")

	for j := range queue {
		spinCPU(50 * time.Millisecond)
		fmt.Printf("worker finished job %d, off the request path\n", j.id)
	}
}
```
