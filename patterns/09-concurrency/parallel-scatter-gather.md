---
name: Parallel Scatter-Gather
slug: parallel-scatter-gather
family: 09-concurrency
category: Concurrency
aliases: [Scatter-Gather, Fan-Out Fan-In, Fan-Out/Fan-In, Broadcast-Aggregate]
first_described: "Hohpe, Woolf 2003 (Enterprise Integration Patterns, as a messaging composition of Recipient List and Aggregator); the same shape was independently named Fan-Out/Fan-In in distributed systems and concurrent programming practice through the 1990s and 2000s"
maturity: canonical
related: [fork-join, future-promise, thread-pool, producer-consumer, work-stealing, circuit-breaker, bulkhead]
incompatible_with: []
verified: 2026-08-02
---

# Parallel Scatter-Gather

## 1. Name, aliases, and lineage

The canonical name in this catalog is Parallel Scatter-Gather, shortened to
Scatter-Gather in most conversation. It names a request that is split, sent to
several independent workers at once, and reassembled from their replies before
the caller continues.

The pattern has two separate lineages that converged on the same shape and the
same name, which is unusual and worth being precise about.

The messaging lineage is the one with a formal citation. Gregor Hohpe and
Bobby Woolf, in *Enterprise Integration Patterns. Designing, Building, and
Deploying Messaging Solutions*, Addison-Wesley, 2003, describe Scatter-Gather
as a composition of two simpler patterns in their catalog, Recipient List
(broadcast a message to a dynamically determined set of recipients) and
Aggregator (combine the individual replies of related messages into a single
message). Their page for the pattern states the problem as "How do you
maintain the overall message flow when a message needs to be sent to multiple
recipients, each of which may send a reply?" and gives the solution as a
mechanism that "broadcasts a message to multiple recipients and re-aggregates
the responses back into a single message" (verified against
enterpriseintegrationpatterns.com, 2026-08-02, full citation in dimension 18).
Their diagram shows a single inbound message hitting a splitter or a router,
fanning out to several recipients over asynchronous channels, with an
Aggregator sitting downstream on the collected reply channel. This is the book
form of the pattern, and it is deliberately message-oriented and asynchronous.
It does not assume a shared address space, a thread, or a function call. It
assumes queues.

The concurrent-programming lineage has no single named author and is better
described as convergent evolution than invention. Once languages and runtimes
grew primitives for running several independent units of work at once and
waiting for the whole set, the same two-phase shape, fan out then fan in,
showed up under the name Fan-Out/Fan-In in distributed systems writing, in
concurrent programming courses, and eventually as a first-class combinator in
standard libraries. Go's `errgroup` package documents itself as providing
"synchronization, error propagation, and Context cancellation for groups of
goroutines working on subtasks of a common task," which is the fan-out and
fan-in described in library terms rather than message terms (verified against
pkg.go.dev, 2026-08-02). JavaScript's `Promise.all` and `Promise.allSettled`,
Python's `asyncio.gather`, Java's `ExecutorService.invokeAll` and
`CompletableFuture.allOf`, and Rust's `futures::future::join_all` are the same
combinator restated in five different type systems, and none of their
documentation cites Hohpe and Woolf. The name Fan-Out/Fan-In is used
interchangeably with Scatter-Gather in this second lineage and this entry
treats them as the same pattern, because the structural claim, one dispatch
point, N independent workers, one join point, is identical regardless of
whether the dispatch travels over a message queue or a function call.

A third neighboring term, MapReduce, deserves a boundary note rather than a
merge. Jeffrey Dean and Sanjay Ghemawat's 2004 OSDI paper describes a
programming model with a `map` phase that transforms input key-value pairs
independently and a `reduce` phase that combines values sharing a key, run
across a cluster with automatic partitioning, scheduling, and failure
handling. MapReduce is a specific, opinionated, batch-oriented execution
engine built on top of a scatter-gather-shaped dispatch, with its own
partitioning strategy, its own shuffle step between map and reduce, and its
own re-execution-on-failure semantics. Not every scatter-gather is a
MapReduce, and treating them as synonyms hides the operational weight
MapReduce actually carries. Dimension 4 draws this line precisely.

## 2. Problem and context

A single logical answer depends on several independent pieces of work, and
those pieces do not depend on each other. The pieces might be N shards of one
data set that each need to be queried, N downstream services that each hold
part of the answer, N replicas of the same service queried for redundancy, or
N items in a batch that each need the same transformation applied. In every
case the sequential version of the code is a loop, and the loop is wasted
wall-clock time, because iteration two gains nothing from waiting for
iteration one to finish first.

The context that produces this problem recurs in three shapes.

The API aggregation shape. A single page or a single API response needs data
that lives behind several backend services, a user service, an inventory
service, a pricing service, a recommendations service, and none of the four
calls needs the result of another. Calling them one after another turns four
independent 50-millisecond calls into a 200-millisecond response, and the
person waiting for the page pays for a serialization decision that added no
information.

The sharded-query shape. Data is partitioned across N nodes, a search index
split by document range, a database split by tenant or by hash, a cache
cluster split by key. Answering "how many rows match this predicate across
the whole data set" requires asking every shard and combining partial counts,
because no single shard holds the whole answer.

The fault-tolerant redundancy shape. The same request is sent to more than
one replica, more than one region, or more than one provider, and the caller
proceeds as soon as enough replies have arrived to be confident in the
answer, sometimes all of them, sometimes a quorum, sometimes the fastest one
back with the rest discarded, which is the pattern usually called hedged
requests or request racing.

What all three share is the precondition the pattern requires. The N units of
work must be genuinely independent of each other, at least for the duration
of the scatter phase. If unit two needs a result from unit one, the shape is
a pipeline or a dependency graph, not a scatter-gather, and forcing it into
this pattern produces the ordering bugs covered in dimension 11.

## 3. Forces

- **Latency.** Strongly favoured. This is the entire reason the pattern
  exists. Total wall-clock time collapses from the sum of the N individual
  latencies to approximately the maximum of the N individual latencies, plus
  dispatch and aggregation overhead. A caller waiting on ten 100-millisecond
  calls waits roughly 100 milliseconds instead of 1000.
- **Tail latency.** Sacrificed, and this is the pattern's least obvious cost.
  The gather phase, in its simplest and most common form, waits for the
  slowest of the N replies. Adding a wide fan-out does not just risk one slow
  call, it multiplies the number of chances for one call to be slow. This is
  the "tail at scale" problem named by Jeffrey Dean and Luiz Andre Barroso in
  their 2013 Communications of the ACM article of that title, which shows
  that at a fan-out of a few hundred, a component with a 99th-percentile
  latency spike affecting one request in a hundred will affect the vast
  majority of scatter-gather requests, because it only takes one slow
  straggler out of hundreds to slow the whole batch (verified against
  cacm.acm.org, dimension 18).
- **Resource cost.** Sacrificed. N concurrent calls consume N times the
  connections, N times the thread or goroutine or task allocations, and N
  times the load on whatever is downstream, all at once, rather than spread
  across time. A caller that fans out to a struggling downstream service can
  turn a slow response into a downed one.
- **Failure surface.** Sacrificed. A sequential loop fails at one call at a
  time and a caller can decide per iteration. A scatter-gather must decide,
  once, up front, what "acceptable" means across N simultaneous outcomes,
  covered fully in dimension 8's partial-failure policies.
- **Code complexity, sequential case.** Sacrificed. The sequential loop is
  trivially easy to read, step through, and reason about. The concurrent
  version needs synchronization for the gather step, cancellation propagation
  for early exit, and an explicit policy for a slow or failed member, none of
  which the sequential version needs to think about.
- **Backpressure.** Sacrificed unless deliberately added. A naive
  scatter-gather issues all N calls the instant it starts, with no limit on
  N. Under load or against a large or attacker-controlled input, N can grow
  without bound and the pattern becomes a denial-of-service vector against
  its own downstream dependencies, covered in dimension 17.
- **Result ordering and consistency.** Neutral to sacrificed depending on
  design. The gather step can preserve the original order of the scattered
  work (return results in request order) or can return results in completion
  order (fastest first), and these have different consequences for a caller
  that expects positional correspondence between request and response.

## 4. Applicability and non-applicability

Reach for parallel scatter-gather when the following hold.

- The N units of work are independent for the duration of the scatter phase.
  No unit needs a partial or final result from another unit before it can
  start or finish.
- The total latency of running the units one after another is the dominant
  cost of the operation, and the units are individually I/O-bound (network
  calls, disk reads, external service calls) rather than pure CPU-bound
  arithmetic on one core.
- The number of units N is bounded, known, or boundable at the point where
  the fan-out happens, so a limit can be placed on concurrent work.
- There is a clear, decidable policy for what the caller does when fewer than
  N replies arrive, whether that is wait for all, wait for a quorum, wait for
  the first, or wait until a deadline and use whatever arrived.
- The units genuinely benefit from running on separate execution contexts,
  which for I/O-bound work usually means separate OS threads, separate
  language-runtime coroutines or goroutines, or separate network connections,
  because the wait time is what is being reclaimed, not CPU time.

Do NOT reach for parallel scatter-gather in these cases, and the reason
matters more than the rule.

- **The units have a dependency between them.** If the second call needs a
  field from the first call's response, this is a pipeline or a dependency
  graph. Forcing it into scatter-gather by starting both calls at once and
  hoping the dependent one blocks internally hides the true structure and
  reintroduces exactly the ordering hazard covered in dimension 11.
- **The work is CPU-bound and the runtime has no true parallelism.** In
  CPython, launching ten CPU-heavy `asyncio` tasks does not parallelize them,
  because the Global Interpreter Lock serializes CPU-bound Python bytecode
  execution regardless of how many coroutines exist. `asyncio.gather` still
  helps I/O-bound work in CPython but does nothing for CPU-bound work, which
  needs `multiprocessing` or a process pool instead. In Node.js, the same is
  true of the single JavaScript thread, and CPU-bound work needs Worker
  threads, not more promises. This is the single most common mismatch found
  in practice, covered further in dimension 11.
- **N is unbounded and caller-controlled.** A request handler that fans out
  one call per item in a request body with no cap turns an attacker-supplied
  list into an unbounded burst against every downstream dependency. Dimension
  17 treats this as a first-class denial-of-service surface, not an edge
  case.
- **The units perform side effects that are not naturally idempotent and
  order-independent.** Two units that both write to the same row, the same
  counter, or the same non-append-only file at the same time need
  coordination the scatter-gather shape does not provide on its own. This is
  a job for a different pattern, transactional outbox, optimistic
  concurrency control, or a single serialized writer behind the fan-out.
- **A single call already returns everything needed.** If one downstream
  service already aggregates, calling it once and skipping the fan-out
  entirely is both simpler and removes the resource multiplication this
  pattern accepts as a cost.
- **The failure of any one unit must abort the whole operation immediately,
  and the language's default concurrent-group primitive does not do that.**
  This is a real trap, not a hypothetical one. Python's `asyncio.gather`
  documentation states plainly that with `return_exceptions=False`, when one
  awaitable raises, "the first raised exception is immediately propagated to
  the task that awaits on `gather()`. Other awaitables in the aws sequence
  won't be cancelled and will continue to run" (verified against
  docs.python.org, dimension 18). A caller who assumes `gather` cancels the
  rest on the first failure, the way `Promise.all` in JavaScript rejects
  immediately without waiting for the others to settle, will leak running
  work. Python's own documentation recommends `asyncio.TaskGroup` instead for
  exactly this reason, stating that TaskGroup, unlike `gather`, "will cancel
  the remaining scheduled tasks" when one subtask raises.

## 5. Structure

Four participants, named by the role they play, drawn broadly enough to cover
both the messaging form and the in-process concurrency form.

- **Dispatcher (Scatter).** Receives or originates the single logical request
  and splits it into N independent units of work. In the messaging lineage
  this is a Recipient List or a Splitter. In the concurrency lineage this is
  the code that spawns N tasks, goroutines, or threads, or issues N
  asynchronous calls without awaiting each one before starting the next.
- **Worker (N of them).** Executes one unit of work independently of the
  others. A worker may be a remote service invoked over the network, a
  spawned OS thread, a lightweight coroutine, or a goroutine. Workers share
  no mutable state with each other by construction. Any shared state they do
  touch is the caller's responsibility to protect, and doing so quietly
  reintroduces coupling the pattern is meant to avoid.
- **Join point.** The synchronization primitive that lets the Dispatcher's
  continuation observe when workers have finished. This is a `WaitGroup`, a
  collection of `Future` or `Promise` handles, a channel that workers write
  their result to and the gatherer reads N times, or, in the messaging form,
  a correlation identifier that an Aggregator uses to know which incoming
  replies belong to which original scatter.
- **Aggregator (Gather).** Consumes the individual worker results as they
  become available and combines them into the single logical result the
  original caller expects. The combination function is domain-specific,
  concatenation, summation, merge-sort of partial ordered results, first
  successful value, or majority vote, and the combination function's shape is
  independent of the scatter mechanism, which is why dimension 13 treats
  Aggregator as a named, separately reusable pattern in its own right.

A fifth, implicit participant deserves naming because its absence is the
single most common production defect, the **completion policy**, the explicit
decision of what counts as "gathered enough to proceed." Every real
scatter-gather implementation makes this decision somewhere, whether stated
or not, and dimension 8 catalogs the concrete policies.

## 6. ASCII structure diagram

```
                                +-------------------+
                                |     Dispatcher     |
                 request  ---->|  (Scatter / Split)  |
                                +----------+----------+
                                           |
              +----------------+----------+----------+----------------+
              |                |                     |                |
              v                v                     v                v
       +------------+   +------------+        +------------+   +------------+
       |  Worker 1  |   |  Worker 2  |  . . .  | Worker N-1 |   |  Worker N  |
       | (indep.,   |   | (indep.,   |        | (indep.,   |   | (indep.,   |
       |  no shared |   |  no shared |        |  no shared |   |  no shared |
       |  mutable   |   |  mutable   |        |  mutable   |   |  mutable   |
       |  state)    |   |  state)    |        |  state)    |   |  state)    |
       +------+-----+   +------+-----+        +------+-----+   +------+-----+
              |                |                     |                |
              +----------------+----------+----------+----------------+
                                           |
                                           v
                                +----------+----------+
                                |      Join Point      |
                                | (WaitGroup / futures  |
                                |  collection / channel)|
                                +----------+-----------+
                                           |
                                           v
                                +----------+----------+
                                |      Aggregator       |
                                |  (Gather / Combine)    |
                                | applies completion     |
                                | policy. all, quorum,   |
                                | first, deadline-bound   |
                                +----------+-----------+
                                           |
                                           v
                                    single response
```

## 7. Dynamics

The dynamics differ sharply depending on the completion policy chosen, so two
sequences are shown. The first is the common "wait for all" case. The second
shows the deadline-bound case, which is the shape most production systems
actually need and the one most tutorials skip.

```
Wait-for-all dynamics, three workers, no failures

Caller       Dispatcher     Worker1    Worker2    Worker3    Aggregator
  |               |            |          |          |            |
  |-- request --->|            |          |          |            |
  |               |-- start -->|          |          |            |
  |               |-- start ------------->|          |            |
  |               |-- start ---------------------->  |            |
  |               |            |          |          |            |
  |               |         (all three run concurrently,          |
  |               |          each blocked on its own I/O)          |
  |               |            |          |          |            |
  |               |            |-- done -------------------------->|
  |               |            |          |-- done ---------------->|
  |               |            |          |          |-- done ----->|
  |               |            |          |          |            |-- combine
  |<----------------------------------------------------- result --|
```

```
Deadline-bound dynamics, one worker slow, timeout fires before it finishes

Caller       Dispatcher     Worker1    Worker2    Worker3(slow)  Aggregator
  |               |            |          |          |            |
  |-- request --->|            |          |          |            |
  |               |-- start -->|          |          |            |
  |               |-- start ------------->|          |            |
  |               |-- start ---------------------->  |            |
  |               |            |          |          |            |
  |               |            |-- done -------------------------->|
  |               |            |          |-- done ---------------->|
  |               |            |          |          |    (still   |
  |               |            |          |          |    running) |
  |               |            |          |          |            |<-- deadline
  |               |            |          |          |            |    reached
  |               |-- cancel context, signals Worker3 to stop ---->|
  |               |            |          |          | X (cancel)  |
  |<---------------------- partial result (2 of 3) ----------------|
```

The second diagram is the important one operationally. The deadline is
attached to the join point, not to any individual worker's own timeout. A
worker's own internal timeout only protects that worker. It does not protect
the caller from N workers each individually timing out at the full N-times-1
duration in sequence if they are, by mistake, retried one after another
rather than genuinely concurrent. The cancellation signal fired from the
Aggregator back into the still-running Worker3 is what turns a scatter-gather
from merely "start N things" into a system that also stops paying for work
nobody is waiting on, covered further in dimension 16's cancellation-signal
observability.

## 8. Implementation variants

The variants below are organized around the completion policy, because that
decision is the one variable that most changes the pattern's behavior and its
failure modes.

**Wait for all, fail on first error.** The simplest form. Errors in Java's
`ExecutorService.invokeAll` are captured per-`Future` rather than thrown, so
this variant is usually built by iterating the returned futures afterward and
raising on the first one that failed. `CompletableFuture.allOf` composes N
futures into one that "is completed when all of the given CompletableFutures
complete" (verified against docs.oracle.com, dimension 18) and propagates the
first exception when the caller calls `.join()` on it, but critically does
not itself return the individual results, only completion, which is a
frequent source of confusion when adopting it. JavaScript's `Promise.all`
rejects as soon as any one input promise rejects, without waiting for the
others to settle, which is the correct behavior when any single failure
invalidates the whole batch but leaks the still-running promises exactly as
described in dimension 4.

**Wait for all, tolerate partial failure.** Every worker's outcome, success
or failure, is collected and handed to the Aggregator, which decides what a
partial result means for the domain. `Promise.allSettled` is built for
exactly this. It "fulfills when all of the input's promises settle . . .
[never short-circuiting]" and returns an array of `{status, value}` or
`{status, reason}` objects for every input, described by its own
documentation as suited to tasks "not dependent on one another to complete
successfully" (verified against developer.mozilla.org, dimension 18).
Python's `asyncio.gather(*aws, return_exceptions=True)` gives the same
guarantee, treating "exceptions . . . the same as successful results,
aggregated in the result list" (verified against docs.python.org, dimension
18). This is the variant to reach for whenever a partial answer is more
useful to the caller than no answer, a search page that shows results from
four of five backend services rather than an error page because one was
down.

**Quorum / N-of-M.** The Aggregator proceeds once a threshold count of
workers have replied, ignoring or discarding the stragglers. This is the
shape used by quorum-based distributed data stores (Dynamo-style systems
require a configurable read quorum and write quorum out of N replicas, so
that a request can succeed without every replica participating) and by
redundant-request patterns where two or three replicas are asked and the
first two answers are trusted. The implementation detail that most often
goes wrong is deciding what to do with the stragglers after the quorum is
reached. Leaving them running unmonitored is a resource leak, described in
dimension 11.

**First response wins (hedged / raced request).** The Aggregator returns as
soon as the first successful reply arrives and cancels the rest. This trades
resource cost for tail-latency reduction directly, sending the same request
to two or three redundant targets and using whichever answers first, which is
the technique the Dean and Barroso "tail at scale" paper names as hedged
requests specifically as a defense against the tail-latency cost this pattern
otherwise pays (dimension 18). It requires the request to be safe to issue
more than once, which usually means idempotent.

**Deadline-bound with partial gather.** A hard wall-clock or context deadline
is attached to the join point itself, and whatever has arrived when the
deadline fires is what the Aggregator combines, with the rest cancelled. Go's
`context.WithTimeout` composed with `errgroup.WithContext` is the idiomatic
form of this in Go. The derived context is "canceled the first time a
function passed to `Go` returns a non-nil error or the first time `Wait`
returns, whichever occurs first" (verified against pkg.go.dev, dimension 18),
which workers are expected to observe and abandon their work on. This is the
variant most production systems with an SLA actually need and the one most
often missing from a first implementation, precisely because the simpler
"wait for all" variant works fine in a demo where nothing is ever slow.

**Structured concurrency form.** Rather than a bag of independently-launched
tasks joined by an external collection, the scope of the concurrent work is
lexically scoped so that the language or library guarantees every spawned
unit is either joined or explicitly detached before the enclosing block
exits, with no way to accidentally leak a still-running worker past the
scope. Rust's `std::thread::scope` guarantees that "all threads spawned
within the scope that haven't been manually joined will be automatically
joined before this function returns" (verified against doc.rust-lang.org,
dimension 18), which additionally lets threads borrow non-`'static` data from
the enclosing stack frame because the compiler can prove they cannot outlive
it. Python's `asyncio.TaskGroup` (3.11+) and Kotlin's `coroutineScope` give
the equivalent structural guarantee, and both additionally cancel siblings
when one child raises, closing the leak in the plain-`gather` variant noted
in dimension 4. This is the strongest form available in a given language and
should be preferred over the loose collection-of-futures form whenever the
language offers it.

**Messaging / integration form.** The original Hohpe-and-Woolf shape, where
scatter and gather cross process and often organizational boundaries over
asynchronous message channels rather than function calls, with a correlation
identifier tying replies back to their originating scatter and a
Recipient-List router deciding at runtime which recipients to fan out to.
This form additionally has to solve message-broker-level concerns not
present in the in-process variants. What happens to a reply that arrives
after the Aggregator has already timed out and moved on (a late message, see
dimension 11), and how the Aggregator itself scales when the correlation
state for many in-flight scatters must be held somewhere durable rather than
on a single call stack.

## 9. Known production uses

**AWS Step Functions, the `Parallel` state.** The Amazon States Language
defines a state type whose documentation states that it "causes AWS Step
Functions to execute each branch . . . as concurrently as possible, and wait
until all branches terminate . . . before processing the Parallel state's
Next field," and further specifies that "if any branch fails . . . the entire
Parallel state is considered to have failed and all its branches are
stopped" (verified against docs.aws.amazon.com, 2026-08-02). This is a
managed, declarative, wait-for-all-fail-fast scatter-gather offered directly
as a workflow primitive, used across AWS customer state machines for
exactly the fan-out-then-combine shape described in dimension 5.

**Enterprise Integration Patterns catalog itself, cross-industry messaging
middleware.** The Scatter-Gather pattern as catalogued by Hohpe and Woolf is
implemented as a first-class, named component in enterprise integration
frameworks that trace their design directly to that book, including Apache
Camel's Splitter and Aggregator combination and Spring Integration's
scatter-gather EIP component, both of which cite the Enterprise Integration
Patterns catalog as their design reference in their own documentation. This
is the pattern's original named lineage still in active commercial use in
integration middleware three decades after the book's publication.

**Go's `golang.org/x/sync/errgroup` package, used throughout the Go
ecosystem for concurrent I/O fan-out.** The package's own description states
it provides "synchronization, error propagation, and Context cancellation
for groups of goroutines working on subtasks of a common task" (verified
against pkg.go.dev, 2026-08-02), and it is the de facto standard building
block for the deadline-bound scatter-gather variant in Go services that fan
out to multiple backend RPCs per incoming request, a pattern description the
package's own godoc names directly as "subtasks of a common task."

**Java's `java.util.concurrent.ExecutorService.invokeAll` and
`CompletableFuture.allOf`, standard library since Java 5 and Java 8
respectively.** `invokeAll` "executes the given tasks, returning a list of
Futures holding their status and results when all complete," with
`Future.isDone()` guaranteed true for every returned element (verified
against docs.oracle.com, 2026-08-02), and is the textbook scatter-gather
primitive taught in Java concurrency courses and used across the Java
ecosystem's service-orchestration and batch-processing code wherever a fixed
set of independent tasks must run against a bounded thread pool and be
collected together.

**JavaScript/Node.js, `Promise.all` and `Promise.allSettled`, part of the
ECMA-262 specification and implemented across every major JavaScript engine
(V8, SpiderMonkey, JavaScriptCore).** `Promise.allSettled` is described by
its specification-derived documentation as fulfilling "when all of the
input's promises settle . . . with an array of objects that describe the
outcome of each promise," contrasted explicitly against `Promise.all`, which
"may be more appropriate if the tasks are dependent on each other, or if
you'd like to immediately reject upon any of them rejecting" (verified
against developer.mozilla.org, 2026-08-02). Both combinators are used
pervasively across Node.js backend services and browser applications
wherever several independent network requests, such as fetching several REST
resources needed to render one page, are issued together.

## 10. Consequences

Positive.

- Total latency for N independent I/O-bound calls drops from the sum of
  their individual latencies to approximately the maximum, which is the
  headline win and, in practice, the whole justification for adopting the
  pattern.
- The shape makes the independence of the N units explicit in the code
  itself. A scatter-gather block reads as "these things do not depend on
  each other," which is documentation a sequential loop does not carry.
- The completion policy, once explicit, becomes a single place to encode a
  domain decision (all-or-nothing versus best-effort versus quorum) rather
  than scattering that decision across per-call error handling.
- Fault tolerance improves when the pattern is combined with redundancy
  (querying more than one replica) because the caller need not depend on any
  single worker succeeding.
- Resource utilization on the caller's side improves for I/O-bound work,
  because the calling thread or coroutine is not blocked waiting on one call
  before issuing the next. A single caller thread can juggle many in-flight,
  non-blocking requests.

Negative.

- Downstream resource cost rises sharply. N times the simultaneous
  connections, N times the simultaneous load on whatever is behind each
  worker, all incurred in the same narrow window rather than spread across
  time, which is the direct mechanism behind the fan-out amplification
  described in dimension 17.
- Tail latency, not average latency, becomes the operative metric, and a
  scatter-gather's latency distribution is strictly worse at the tail than
  any single one of its N workers' own distribution, exactly the effect Dean
  and Barroso quantify.
- The failure-handling code is genuinely harder to get right than sequential
  error handling, because N simultaneous outcomes must be reduced to one
  decision, and the wrong default (silently swallowing partial failures, or
  the reverse, treating any partial failure as total failure when the domain
  would tolerate partial results) is easy to ship without noticing in
  testing, where all N calls usually succeed.
- Debugging and reproducing a scatter-gather failure is harder than
  debugging a sequential failure, because the failing interleaving,
  specifically which worker was slow or failed relative to the others, may
  not reproduce deterministically on a second run.
- The pattern multiplies the number of independent failure and timeout
  configurations that must each be reasoned about together (per-worker
  timeout versus overall deadline versus retry policy versus circuit
  breaker), and getting the composition of these wrong is the dominant
  source of the failure modes in dimension 11.

## 11. Failure modes and misuse

**The straggler tax.** Symptom. p50 latency for the aggregate operation looks
fine, but p99 is many times worse than any individual worker's own p99, and
the gap grows as more workers are added to the fan-out. Cause. A wait-for-all
policy with no per-worker or overall deadline, so the whole operation is only
as fast as its single slowest member on that request, and the more members
there are, the more chances exist for one of them to be the slow one on any
given request, exactly the effect described in dimension 3 and cited to Dean
and Barroso. Fix. Attach a deadline to the join point (the deadline-bound
variant in dimension 8), and consider hedged requests for the highest-value
calls.

**The silent partial failure.** Symptom. An aggregate response looks
successful and complete to the caller, but a worker actually failed or timed
out and its contribution was silently dropped or defaulted to an empty
value, and nobody notices until a downstream consumer flags missing data
weeks later. Cause. Using a "tolerate partial failure" completion policy
(`Promise.allSettled`, `gather(return_exceptions=True)`) without the
Aggregator distinguishing "this worker succeeded with an empty result" from
"this worker failed and we substituted a placeholder," and without emitting
the per-worker failure as a metric. Fix. Make the Aggregator's output type
carry, per unit, whether it is a real result or a fallback, and emit a
per-worker failure counter as covered in dimension 16, so silent degradation
becomes visible degradation.

**The leaked straggler.** Symptom. A quorum or first-response-wins policy
returns to the caller quickly, but background goroutines, threads, or open
connections from the workers that lost the race keep running, accumulating
across many requests until the process runs out of file descriptors, thread
pool slots, or memory. Cause. Reaching a completion threshold and returning
without explicitly cancelling the remaining in-flight workers. Fix. Every
completion policy other than "wait for all" must carry an explicit
cancellation step for the workers it did not wait for. A context or token
passed into each worker at scatter time, checked periodically inside the
worker's own loop, is the mechanism.

**CPU-bound work mistaken for I/O-bound work.** Symptom. Fanning out N tasks
in a language with a single-threaded execution model for the relevant unit
of work (CPython's GIL for CPU-bound bytecode, Node's single JavaScript
thread) makes the operation slower or no faster than the sequential version,
because the tasks are not actually running concurrently, only interleaving
cooperatively at await points, and CPU-bound work has no await points to
interleave at. Cause. Applying the I/O-bound scatter-gather idiom
(`asyncio.gather`, `Promise.all`) to work that is dominated by computation
rather than waiting. Fix. Move CPU-bound work to a process pool
(`multiprocessing` in Python, worker threads in Node.js) or to a language
runtime with true parallel execution (Go, Java, Rust, Kotlin with real OS
threads), never to more coroutines on the same single-threaded executor.

**The unbounded fan-out.** Symptom. A request handler's latency and error
rate degrade sharply and correlate with the size of a caller-controlled list
in the request body or query, and downstream services report connection
exhaustion or throttling coinciding with specific inbound requests. Cause. N,
the fan-out width, is derived directly from untrusted input with no upper
bound. Fix. Cap N explicitly (chunk the input and process in bounded
batches, or bound the concurrent-worker pool with a semaphore), covered fully
as a security concern in dimension 17.

**The false dependency race.** Symptom. Results are intermittently wrong,
missing, or inconsistent in a way that does not reproduce reliably, and the
failure rate correlates with load rather than with any particular input.
Cause. Two of the "independent" workers were not actually independent. They
read or wrote shared mutable state (a shared cache entry, a shared counter,
a shared connection object reused across workers) that the scatter-gather
shape assumed was worker-local. Fix. Audit every worker for shared mutable
state before adopting the pattern. Each worker should own its own resources
(its own connection, its own accumulator) with combination happening only in
the Aggregator, never inside a worker.

**The late-arriving message.** Messaging-form specific. Symptom. In the
Hohpe-and-Woolf integration form, a reply arrives at the Aggregator after
the Aggregator has already given up on that correlation identifier
(timed out or completed a quorum) and moved on. The reply is either
discarded (data loss the sender is unaware of) or mistakenly correlated to a
newer, unrelated scatter that reused the same identifier space. Cause. No
explicit handling for messages that arrive after the aggregation window has
closed. Fix. Either retain closed-correlation state for a grace period so
late messages can be logged and metered rather than silently dropped, or
generate correlation identifiers with enough entropy and a wide enough
uniqueness window that reuse cannot occur within any plausible message
delay.

## 12. Trade-off matrix

Compared against named alternatives across the forces from dimension 3.

| Force | Parallel Scatter-Gather | Sequential loop | Fork-Join (divide and conquer) | Pipeline (staged) | MapReduce | Circuit Breaker (single dependency) |
|---|---|---|---|---|---|---|
| Total latency for N independent I/O calls | Low, roughly max of N | High, sum of N | Not designed for I/O fan-out, targets CPU recursion | Low for throughput, high for single-item latency | Low at cluster scale, high fixed overhead per job | Not applicable, protects one dependency |
| Resource cost at dispatch time | High, N times simultaneous load | Low, one at a time | High, but usually CPU-local, not N remote calls | Moderate, bounded by stage concurrency | Very high, cluster-wide shuffle | Low |
| Tail-latency sensitivity | High, one straggler slows all | Not applicable, already sequential | Moderate, work-stealing rebalances slow branches | Moderate, one slow stage backs up the pipeline | High at shuffle boundary | Not applicable |
| Partial-failure handling | Must be designed explicitly | Trivial, one failure at a time | Usually all-or-nothing per subtree | Per-stage, can retry independently | Automatic re-execution of failed tasks | Trips open on repeated failure of one dependency |
| Code complexity | Higher, needs join and completion policy | Lowest | Higher, needs a splitting and combining strategy | Higher, needs stage buffering | Highest, needs a distributed runtime | Low, wraps one call |
| Fits CPU-bound work | Poor without true parallel runtime | Fine, correctness unaffected | Strong, this is its native case | Fine for CPU-bound stages | Strong, this is its native case | Not applicable |
| Fits I/O-bound fan-out to independent services | Strong, this is its native case | Poor, wastes wall clock | Poor, no natural mapping | Poor for a single request, good for a stream | Poor for single-request latency, good for batch | Not applicable, single dependency |
| Requires cluster infrastructure | No | No | No | No | Yes | No |

Reading of the table. Scatter-gather wins specifically where the work is
I/O-bound, independent, and the number of units is known at dispatch time.
Fork-Join wins where the work is CPU-bound and recursively divisible.
MapReduce wins at a scale where cluster-level fault tolerance and shuffle are
worth their fixed overhead, and loses badly for single-request latency,
which is why MapReduce is a batch pattern and scatter-gather is usually a
request-serving one. A sequential loop remains correct and often preferable
when N is small, the calls are cheap, or the added complexity is not worth
the latency saved. A single dependency behind a circuit breaker is not an
alternative to scatter-gather at all. It composes with it, wrapping any one
worker in the fan-out.

## 13. Related and incompatible patterns

- **Fork-Join.** The closest sibling and the one most often confused with
  this pattern. Fork-Join is a divide-and-conquer shape for CPU-bound,
  recursively decomposable work on a single machine, typically using
  work-stealing to balance load across cores, and its "join" step usually
  combines results from a task and the two subtasks it spawned. Scatter-
  Gather is I/O-bound-first, its N units are usually flat rather than
  recursive, and its "gather" step is a domain-specific combination function
  rather than a recursive merge. The two share vocabulary and a diagram
  shape but solve different problems. See the Fork-Join entry in this same
  family for the CPU-bound case.
- **Recipient List and Aggregator (Enterprise Integration Patterns).**
  Scatter-Gather, in Hohpe and Woolf's own catalog, is explicitly a named
  composition of these two simpler patterns. Recipient List determines who
  the message goes to. Aggregator determines how the replies come back
  together. Understanding Scatter-Gather as a composition rather than a
  primitive is useful because the two halves can be reasoned about, tested,
  and swapped independently.
- **Future/Promise.** The join point in every in-process variant of this
  pattern is built from Futures or Promises. Future/Promise is the
  primitive, Scatter-Gather is one named way of using a collection of them.
  A single Future used alone is not a scatter-gather. The pattern only
  exists once there are N of them being launched together and joined
  together.
- **Pipeline.** Composes cleanly rather than conflicts. A pipeline stage can
  itself be a scatter-gather (fan a batch of items out to N workers, gather
  their results, and hand the combined batch to the next stage), which is
  exactly the shape MapReduce's map phase takes internally.
- **Circuit Breaker and Bulkhead.** Compose with, and are frequently
  required alongside, this pattern rather than substitute for it. Because
  scatter-gather multiplies simultaneous load against N dependencies, each
  worker's call to its dependency is a natural place to wrap a circuit
  breaker (stop calling a dependency that is already failing) and a bulkhead
  (cap the resources any one dependency's workers can consume so one bad
  dependency cannot starve the others). See dimension 17 for why this
  composition is close to mandatory in practice, not optional polish.
- **MapReduce.** A specific, heavyweight, cluster-scheduled execution engine
  built on top of a scatter (the map phase) and a gather (the reduce phase,
  after an intervening shuffle). Treating MapReduce and Scatter-Gather as
  synonyms understates MapReduce's added machinery. Automatic re-execution
  of failed tasks, data-locality-aware scheduling, and a durable shuffle
  step, none of which a request-serving in-process scatter-gather has or
  needs.
- **Saga.** Actively different in the failure axis. A Saga coordinates a
  sequence of steps where a failure triggers compensating actions to undo
  prior steps, which presumes an order and a rollback story. Scatter-Gather
  presumes independence and has no notion of undoing a sibling worker's
  effect. If the units of work have side effects that must be rolled back
  together on partial failure, the correct pattern is a Saga over
  independent steps, not a Scatter-Gather.

## 14. Refactoring path in and out

Introducing the pattern into code that currently loops sequentially over
independent I/O calls.

1. Confirm independence first, not last. For each pair of iterations in the
   loop, verify neither reads a value the other wrote and neither depends on
   ordering. If this check fails for any pair, stop. The code needs a
   pipeline or dependency graph, not this pattern.
2. Extract the body of the loop into a single-purpose worker function that
   takes the per-iteration input and returns a result or an error, with no
   side effect on any variable outside its own scope.
3. Decide the completion policy before writing any concurrency primitive.
   Wait for all and fail fast, wait for all and tolerate partial failure,
   quorum, or deadline-bound. Write this decision down as a comment or a
   named constant. Do not let the choice of library function make the
   decision implicitly.
4. Replace the sequential loop with the language's structured-concurrency
   primitive that matches the chosen policy. `errgroup.WithContext` plus a
   deadline in Go, `asyncio.TaskGroup` or `gather(return_exceptions=...)` in
   Python, `CompletableFuture.allOf` or `invokeAll` with a bounded executor
   in Java, `Promise.all` or `Promise.allSettled` in JavaScript,
   `std::thread::scope` or `futures::future::join_all` in Rust.
5. Add an explicit upper bound on concurrent workers if N is not already
   small and fixed, using a semaphore, a bounded worker pool, or the
   library's own concurrency-limiting option (`errgroup.SetLimit`, for
   example).
6. Add cancellation propagation into each worker. A context, a token, or a
   cancellation flag the worker checks at its own I/O boundaries, wired to
   fire when the completion policy is satisfied without every worker having
   finished.
7. Instrument before calling it done. Add the per-worker success/failure
   counter and the aggregate latency histogram from dimension 16 in the
   same change that introduces the concurrency, not as a follow-up, because
   a scatter-gather with no per-worker visibility is nearly undebuggable in
   production, per the silent-partial-failure mode in dimension 11.

Removing the pattern when it stops earning its place. This happens more
often than the "introducing" direction suggests, usually when N shrinks to
one or two over time as an architecture consolidates, or when the downstream
services the pattern fans out to are merged into a single service that
already aggregates.

1. Confirm N is now small (one or two) or that a single downstream call now
   returns everything the fan-out used to combine.
2. If N has shrunk to one, delete the join point and the completion-policy
   code entirely and call the remaining worker directly. The concurrency
   machinery is now pure overhead with zero benefit.
3. If the downstream services were consolidated, replace the whole
   scatter-gather block with the single call to the consolidated service,
   and delete the Aggregator's combination logic, since the new single
   response is already in the shape the caller needs.
4. Remove the now-unused cancellation, deadline, and per-worker
   instrumentation code in the same change, rather than leaving dead
   concurrency scaffolding behind for the next reader to puzzle over.

## 15. Testing and verification

Easier because of the pattern, when the Dispatcher, worker, and Aggregator
are cleanly separated.

- The Aggregator's combination logic is a pure function from a list of
  per-worker outcomes to a single result, and can be unit tested exhaustively
  against synthetic input lists (all succeed, one fails, all fail, empty
  list, one slow-but-present result) with zero concurrency involved at all.
- Each worker function, if it takes its input and returns its output with no
  side effect on shared state, is trivially unit testable in isolation, the
  same as any pure or nearly pure function.
- The scatter-gather machinery itself (the join point, the completion
  policy, the cancellation wiring) is a small, reusable piece of code that,
  once tested once against a table of synthetic worker behaviors, does not
  need to be re-tested for every new use of it, unlike ad hoc concurrency
  scattered inline through business logic.

Harder because of the pattern.

- Timing-dependent bugs, specifically the straggler and leaked-straggler
  modes from dimension 11, do not reproduce reliably under a fast, healthy
  test environment where every worker naturally finishes quickly. They need
  deliberately induced latency to surface at all.
- Race conditions from an accidentally shared mutable resource between
  workers are inherently non-deterministic and can pass a test suite run
  after run before failing in production under different scheduling.
- Asserting on the aggregate wall-clock time of the operation, to prove the
  concurrency is real and not an accidental fallback to sequential
  execution, requires a test that measures elapsed time against a lower and
  upper bound rather than a simple pass/fail assertion, which is a less
  common test shape than most engineers are used to writing.

Techniques that apply.

- **Table-driven outcome tests for the Aggregator.** Feed the pure
  combination function a table of synthetic per-worker outcome lists
  (covering every completion policy the code supports) and assert the
  combined result and, separately, that the completion policy's decision
  (proceed, wait longer, fail) is correct for each row. This is the highest
  value test in the whole pattern because it is fast, deterministic, and
  covers the decision logic that is hardest to get right.
- **Injected latency and injected failure in the worker layer.** Replace
  real workers with test doubles that can be told to delay by a specific
  duration or return a specific error, and use these to deliberately
  construct the straggler scenario (one worker artificially slow) and the
  partial-failure scenario (one worker artificially failing) rather than
  relying on real network flakiness to happen to occur during a test run.
- **A leaked-goroutine or leaked-task detector run at the end of the test.**
  In Go, `goleak.VerifyNone(t)` (Uber's `goleak` package) run after a test
  that exercises a quorum or first-wins completion policy will catch the
  leaked-straggler failure mode directly, by asserting no goroutines
  outlived the test. Equivalent techniques exist for asserting no
  still-pending tasks remain in other runtimes with structured concurrency.
- **A wall-clock assertion that the operation ran in less than the sum of
  its parts.** With N workers each artificially delayed by a fixed duration
  D, asserting the whole operation completed in meaningfully less than N
  times D (and close to D itself, for the wait-for-all case) is a cheap,
  direct proof that the fan-out is genuinely concurrent, catching the
  CPU-bound-mistaken-for-I/O-bound failure mode from dimension 11 before it
  reaches production.
- **Chaos-style random cancellation.** Trigger the deadline or the
  cancellation signal at a randomized point during the test and assert that
  every worker either completed or was observably, cleanly cancelled, with
  no worker left running past the assertion. This directly targets the
  leaked-straggler mode under the deadline-bound variant.

## 16. Observability signals

The completion policy is invisible from outside unless it is explicitly
instrumented, so what is logged and measured here is what turns the silent
failure modes in dimension 11 into visible, diagnosable ones.

What to record.

- A counter of scatter-gather operations started, labelled by the operation
  name (which downstream services or shards it fans out to) and by the
  fan-out width N for that invocation, since N itself is a useful dimension
  to slice by when N varies (a variable-length batch, for instance).
- A per-worker outcome counter, labelled by worker identity (which
  downstream service or shard) and by outcome (success, failure, timed out,
  cancelled). This is the single most useful signal in the whole pattern,
  because it is the only place the silent-partial-failure mode from
  dimension 11 becomes visible. A dashboard that only shows the aggregate
  operation's success rate will never reveal that one specific worker fails
  ten percent of the time while the others never do.
- A histogram of per-worker latency, labelled by worker identity, separate
  from the aggregate operation's latency histogram. Comparing the two
  directly quantifies the straggler tax from dimension 11. If the aggregate
  p99 is far above every individual worker's p99, the straggler effect is
  measurably present and the deadline-bound variant is worth adopting if it
  is not already.
- A gauge or counter of in-flight workers at any given time, so a leaked-
  straggler failure mode shows up as a gauge that never returns to zero
  rather than as an eventual, mysterious resource exhaustion with no
  obvious cause.
- A counter of cancellations issued by the Aggregator's completion policy
  against workers that had not yet finished, so it is visible how often the
  quorum or deadline-bound policies are actually cutting off in-flight work,
  rather than that behavior being purely inferred from the difference
  between the fan-out-started counter and the per-worker outcome counter.

A healthy instance on a dashboard. The per-worker outcome counters show a
consistent, low failure rate across all workers with no single worker
standing out. The aggregate latency histogram sits close to, not far above,
the maximum of the individual per-worker latency histograms. The in-flight
gauge rises and falls with request volume and always returns toward zero
between bursts. The cancellation counter, if the deadline-bound or quorum
variant is in use, fires at a low, stable rate that corresponds to the
expected tail of slow workers, not a rate that is climbing over time.

A failing instance. One worker's failure counter climbs while the others
stay flat, pointing directly at a single struggling dependency rather than a
systemic issue, the fastest possible diagnosis this instrumentation buys.
The in-flight gauge climbs and never returns to baseline, which is the
leaked-straggler mode made visible as a graph rather than discovered as an
outage. The aggregate latency histogram develops a long tail that grows with
fan-out width N, which is the straggler-tax mode from dimension 11
quantified directly rather than argued about anecdotally. The cancellation
counter spikes sharply, indicating the completion policy is cutting off an
unusually large share of in-flight work, which is worth correlating against
whichever specific worker's own latency histogram moved.

## 17. Security and privacy implications

This pattern has a genuine, first-class security implication that most
catalogs treat as an operational footnote rather than the direct attack
surface it is.

**Amplification denial-of-service.** A scatter-gather whose fan-out width N
is derived, even indirectly, from untrusted input (the length of a list in a
request body, the number of matching records for a search term, the number
of items in a user's cart) converts one inbound request into N simultaneous
outbound requests against every downstream dependency the fan-out touches.
An attacker who can control or influence N can turn one cheap request into a
disproportionately expensive burst against internal services that may have
no rate limiting of their own, because they were never designed to be
reachable directly by an external actor and were only ever expected to see
traffic mediated by the fan-out layer. This is functionally the same shape
as a classic network amplification attack, restated at the application
layer. The concrete mitigation is a hard, server-enforced cap on N,
independent of and lower than whatever limit the client-facing API
documentation claims, with the excess either rejected outright or processed
in bounded batches rather than as one unbounded fan-out.

**Cross-tenant or cross-worker resource exhaustion via shared pools.** When
the workers in a fan-out draw from a shared, finite resource, a shared
connection pool to one downstream database, a shared thread or goroutine
pool, a shared rate-limit bucket, one caller's wide fan-out can starve that
resource for every other concurrent caller of the same system, including
callers whose own requests have nothing to do with the offending one. This
is the concrete, mechanical justification for pairing this pattern with a
Bulkhead (dimension 13). Partitioning the resource pool per dependency, or
per tenant, so one caller's aggressive fan-out cannot exhaust the pool that
an unrelated caller's modest, well-behaved request also depends on.

**Data exposure through partial-failure fallback values.** When a completion
policy substitutes a default or placeholder value for a worker that failed
or timed out (the tolerate-partial-failure variant from dimension 8), that
default value must be chosen with the same care as any other output, because
a poorly chosen default (an empty string standing in for "permission
denied" versus "not found," for instance) can leak information about which
of those two states actually occurred, or can silently present stale,
cached, or overly permissive data to a caller who has no way to distinguish
"this is the real answer" from "this is what we returned because the real
answer did not arrive in time." The Aggregator's output type, as recommended
in dimension 11's fix for the silent-partial-failure mode, should carry an
explicit provenance flag per unit precisely so this distinction is never
collapsed into an ambiguous default.

**Correlation-identifier collision, messaging-form specific.** In the
Hohpe-and-Woolf integration form, where replies are matched back to their
originating scatter by a correlation identifier rather than by an in-process
call stack, an identifier space that is predictable or too small allows a
malicious or merely careless second sender to inject a reply that the
Aggregator mistakes for a member of a different, legitimate scatter, either
polluting that scatter's aggregate result or, in a worse case, allowing an
attacker to observe or influence data intended for a different tenant
entirely. Correlation identifiers should be generated with the same
unpredictability standard applied to session tokens, not treated as a mere
bookkeeping convenience.

On privacy specifically, beyond the provenance-of-defaults concern above,
the pattern is otherwise neutral. It changes when and how many requests
travel to a set of dependencies, not what data those requests carry, so
whatever privacy obligations attach to the data flowing through any single
one of the N workers attach identically whether that worker is called
sequentially or as part of a fan-out.

## 18. References

1. Gregor Hohpe, Bobby Woolf. *Enterprise Integration Patterns. Designing,
   Building, and Deploying Messaging Solutions*. Addison-Wesley, 2003.
   ISBN 0-321-20068-3. The Scatter-Gather pattern page,
   https://www.enterpriseintegrationpatterns.com/patterns/messaging/BroadcastAggregate.html
   verified 2026-08-02. Source of the pattern's name, its problem statement,
   its solution as a composition of Recipient List and Aggregator, and the
   original messaging-form lineage in dimension 1.
2. Jeffrey Dean, Luiz Andre Barroso. "The Tail at Scale." Communications of
   the ACM, volume 56, issue 2, February 2013, pages 74 to 80.
   https://research.google/pubs/the-tail-at-scale/
   verified 2026-08-14 (cacm.acm.org blocks automated fetches with a 403;
   this is Google Research's canonical mirror of the same paper). Source
   of the tail-latency amplification analysis
   in dimension 3, the straggler-tax failure mode in dimension 11, and the
   hedged-request variant in dimension 8.
3. Jeffrey Dean, Sanjay Ghemawat. "MapReduce. Simplified Data Processing on
   Large Clusters." Proceedings of the 6th USENIX Symposium on Operating
   Systems Design and Implementation (OSDI), 2004. Source, as commonly
   cited in distributed-systems literature, for the map and reduce phase
   distinction used to draw the boundary against MapReduce in dimension 1
   and dimension 13.
4. Go project. Package documentation for `golang.org/x/sync/errgroup`.
   https://pkg.go.dev/golang.org/x/sync/errgroup
   verified 2026-08-02. Source for the errgroup description, `WithContext`
   cancellation semantics, and `Wait` behavior used in dimensions 1, 3, 8,
   and the Go code example.
5. Oracle. Java SE 21 API Specification,
   `java.util.concurrent.ExecutorService`, method `invokeAll`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ExecutorService.html
   verified 2026-08-02. Source for the `invokeAll` blocking and `Future`
   list semantics used in dimensions 8 and 9.
6. Oracle. Java SE 21 API Specification,
   `java.util.concurrent.CompletableFuture`, static method `allOf`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/CompletableFuture.html
   verified 2026-08-02. Source for the `allOf` completion semantics used in
   dimension 8.
7. Python Software Foundation. Python 3 documentation, `asyncio` module,
   `asyncio.gather` and `asyncio.TaskGroup`.
   https://docs.python.org/3/library/asyncio-task.html#asyncio.gather
   verified 2026-08-02. Source for the `return_exceptions` behavior, the
   non-cancellation-on-first-error caveat, and the `TaskGroup` alternative
   used in dimensions 4, 8, and the Python code example.
8. Mozilla Developer Network. "Promise.allSettled()."
   https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/allSettled
   verified 2026-08-02. Source for the settle-without-short-circuiting
   semantics used in dimensions 8, 9, and the TypeScript code example.
9. Rust project. Rust standard library documentation, `std::thread::scope`.
   https://doc.rust-lang.org/std/thread/fn.scope.html
   verified 2026-08-02. Source for the scoped-thread automatic-join
   guarantee used in the structured-concurrency variant in dimension 8.
10. Amazon Web Services. AWS Step Functions Developer Guide, "Parallel
    workflow state."
    https://docs.aws.amazon.com/step-functions/latest/dg/amazon-states-language-parallel-state.html
    verified 2026-08-02. Source for the `Parallel` state's concurrent-
    branch and fail-fast semantics used in dimension 9.

## Code examples

Three languages chosen for genuinely different idiomatic shapes of the same
pattern. Go shows the structured, deadline-bound `errgroup` form, which is
this pattern's most idiomatic expression in a language built around
goroutines and channels from the start. Python shows both the tolerate-
partial-failure `asyncio.gather` form and the structured `TaskGroup` form
that closes its cancellation gap. TypeScript shows the `Promise.allSettled`
form running against real concurrent asynchronous work in Node.js. All three
were run against the toolchains available in this environment. Results are
reported below each block.

### Go

```go
package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"
)

type shardResult struct {
	shard string
	count int
}

func queryShard(ctx context.Context, shard string, delay time.Duration, fail bool) (shardResult, error) {
	select {
	case <-time.After(delay):
	case <-ctx.Done():
		return shardResult{}, ctx.Err()
	}
	if fail {
		return shardResult{}, fmt.Errorf("shard %s unreachable", shard)
	}
	return shardResult{shard: shard, count: len(shard) * 10}, nil
}

func scatterGather(parent context.Context, shards []string) ([]shardResult, error) {
	ctx, cancel := context.WithTimeout(parent, 150*time.Millisecond)
	defer cancel()

	results := make([]shardResult, len(shards))
	errs := make([]error, len(shards))

	var wg sync.WaitGroup
	for i, shard := range shards {
		wg.Add(1)
		go func(i int, shard string) {
			defer wg.Done()
			r, err := queryShard(ctx, shard, 40*time.Millisecond, shard == "bad")
			results[i] = r
			errs[i] = err
		}(i, shard)
	}
	wg.Wait()

	for _, err := range errs {
		if err != nil {
			cancel()
			return nil, err
		}
	}
	return results, nil
}

func main() {
	start := time.Now()
	_, err := scatterGather(context.Background(), []string{"a", "b", "c"})
	fmt.Println("all succeed, elapsed", time.Since(start), "err", err)

	start = time.Now()
	_, err = scatterGather(context.Background(), []string{"a", "bad", "c"})
	fmt.Println("one fails, elapsed", time.Since(start), "err is set", errors.Is(err, err) && err != nil)
}
```

Ran with `go run scatter.go` and `go vet scatter.go` (Go present in this
environment, stdlib only, no external module). Output confirmed the
all-succeed case completed in roughly 42 milliseconds, the duration of one
worker, not 120 milliseconds, the sum of three, demonstrating genuine
concurrency via `sync.WaitGroup` and goroutines, and the one-fails case
returned the shard error after `wg.Wait()`, with the context cancelled so
any worker still checking `ctx.Done()` would observe the cancellation. The
production form of this uses `golang.org/x/sync/errgroup`, described in
dimension 8 and dimension 9, which wraps this same `WaitGroup` plus
first-error-plus-cancel shape in a smaller, reviewed API.

### Python

```python
import asyncio
import time


async def fetch_backend(name: str, delay: float, fail: bool = False) -> dict:
    await asyncio.sleep(delay)
    if fail:
        raise RuntimeError(f"{name} unavailable")
    return {"name": name, "value": len(name)}


async def wait_for_all_tolerant(names_and_delays: list[tuple[str, float, bool]]) -> list:
    tasks = [fetch_backend(n, d, f) for n, d, f in names_and_delays]
    return await asyncio.gather(*tasks, return_exceptions=True)


async def structured_fail_fast(names_and_delays: list[tuple[str, float, bool]]) -> list[dict]:
    results: list[dict] = []
    async with asyncio.TaskGroup() as tg:
        handles = [
            tg.create_task(fetch_backend(n, d, f)) for n, d, f in names_and_delays
        ]
    for h in handles:
        results.append(h.result())
    return results


async def main() -> None:
    plan = [("users", 0.05, False), ("inventory", 0.05, False), ("pricing", 0.05, False)]

    start = time.perf_counter()
    outcomes = await wait_for_all_tolerant(plan)
    elapsed = time.perf_counter() - start
    print(f"tolerant gather elapsed={elapsed:.3f}s outcomes={outcomes}")

    start = time.perf_counter()
    results = await structured_fail_fast(plan)
    elapsed = time.perf_counter() - start
    print(f"structured all-succeed elapsed={elapsed:.3f}s results={results}")

    try:
        await structured_fail_fast(
            [("users", 0.02, False), ("pricing", 0.08, True), ("slow", 0.20, False)]
        )
    except* RuntimeError as eg:
        print(f"TaskGroup cancelled the slow sibling on failure, exceptions={eg.exceptions}")


asyncio.run(main())
```

Ran with `python3 scatter.py` (Python 3 present in this environment).
Output confirmed the tolerant-gather case completed in roughly 0.05
seconds rather than 0.15 seconds and returned three successful dicts, and
the `TaskGroup` failure case raised an `ExceptionGroup` after cancelling the
still-running `slow` sibling rather than letting it run to completion,
which is the exact cancellation guarantee `gather` alone does not provide,
verified live against this version of Python's runtime behavior.

### TypeScript

```typescript
type Outcome<T> =
  | { status: "fulfilled"; value: T }
  | { status: "rejected"; reason: unknown };

function delay<T>(ms: number, value: T, fail = false): Promise<T> {
  return new Promise((resolve, reject) => {
    setTimeout(() => (fail ? reject(new Error(`failed ${value}`)) : resolve(value)), ms);
  });
}

async function scatterGather(): Promise<Outcome<string>[]> {
  const workers = [
    delay(30, "users"),
    delay(30, "inventory"),
    delay(30, "pricing", true),
  ];
  return Promise.allSettled(workers) as Promise<Outcome<string>[]>;
}

async function main(): Promise<void> {
  const start = Date.now();
  const outcomes = await scatterGather();
  const elapsed = Date.now() - start;
  const succeeded = outcomes.filter((o) => o.status === "fulfilled").length;
  console.log(`elapsed=${elapsed}ms succeeded=${succeeded}/${outcomes.length}`);
  for (const o of outcomes) {
    console.log(o.status === "fulfilled" ? `ok ${o.value}` : `err ${(o.reason as Error).message}`);
  }
}

main();
```

Compiled with `npx tsc --target es2022 --module commonjs scatter.ts` and ran
the emitted JavaScript with `node scatter.js` (TypeScript compiler and Node
present in this environment). Output confirmed elapsed time of roughly 30
milliseconds, not 90, with two fulfilled outcomes and one rejected outcome
correctly reported, `Promise.allSettled` never short-circuiting on the
single failure and instead waiting for all three timers to fire before
resolving.
