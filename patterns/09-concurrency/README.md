# Family 09. Concurrency and Parallelism

Origin. Schmidt POSA 2

40 entries, 318,564 words. Every entry carries all 18
dimensions from [the entry contract](../../docs/ENTRY-TEMPLATE.md).

## Concurrency

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Active Object](active-object.md) | canonical | 7,829 | An object's public methods are typically called synchronously. |
| [Actor Model](actor-model.md) | canonical | 6,038 | A concurrent program needs many pieces of independent state to change over time, driven by events arriving from different sources, without a lock, mutex, or shared memory region ... |
| [Async Await](async-await.md) | canonical | 9,262 | A function that needs a result from somewhere slow, a network call, a disk read, a timer, a lock, has two honest choices before async/await exists in a language. |
| [Backpressure](backpressure.md) | canonical | 8,912 | Every pipeline has at least two speeds, the rate at which work arrives and the rate at which work can be processed. |
| [Balking](balking.md) | established | 6,673 | An object exposes an operation that is only meaningful, or only safe, in a subset of the object's possible states. |
| [Barrier](barrier.md) | canonical | 8,229 | A computation is organized into a fixed number of concurrent workers, and the work naturally divides into phases. |
| [Communicating Sequential Processes](communicating-sequential-processes.md) | canonical | 7,486 | A program that needs to do more than one thing at once, serve many requests, overlap I/O with computation, or use more than one CPU core, needs a way for its concurrent parts to ... |
| [Compare-and-Swap Loop](compare-and-swap-loop.md) | canonical | 7,321 | A thread wants to update a single shared memory location, a counter, a pointer, a flag, based on its current value, and it wants to do this without taking a lock. |
| [Copy-on-Write](copy-on-write.md) | canonical | 8,948 | The problem copy-on-write solves is a specific tension between two things a system wants at once, the ability to hand out what looks like an independent copy of a piece of data ... |
| [Countdown Latch](countdown-latch.md) | canonical | 6,820 | A piece of code has to wait until a known, fixed number of independent operations are all finished before it can proceed, and it does not otherwise care about the order those ... |
| [Disruptor](disruptor.md) | established | 8,333 | Picture a system that has to move a stream of small, frequent messages between threads and needs the handoff itself to add almost nothing to the total latency budget. |
| [Double-Checked Locking](double-checked-locking.md) | contested | 6,147 | A piece of expensive, shared state, a database connection pool, a parsed configuration object, a cache of compiled regular expressions, a singleton service object, needs to be ... |
| [Fork-Join](fork-join.md) | canonical | 8,083 | You have a computation that can be split into independent subproblems whose results are then combined, and the computation is large enough, or repeated often enough, that running ... |
| [Future Promise](future-promise.md) | canonical | 7,575 | A piece of code needs a value that will not be ready immediately. |
| [Guarded Suspension](guarded-suspension.md) | canonical | 8,261 | A thread calls a method on a shared object, and the method cannot proceed safely or sensibly until some condition involving that object's state becomes true. |
| [Half-Sync/Half-Async](half-sync-half-async.md) | canonical | 8,046 | A concurrent system that talks to the outside world, over a network, a disk, a device driver, or another process, has two kinds of code living inside it at once, and the two kinds ... |
| [Immutable Object](immutable-object.md) | canonical | 7,552 | Two or more threads share a reference to the same object. |
| [Leader/Followers](leader-followers.md) | canonical | 9,034 | A server, or any concurrent program, has a set of event sources, such as socket handles for connected clients, and it must service events that arrive on those sources with as many ... |
| [Lock Striping](lock-striping.md) | canonical | 7,978 | A single mutable structure, most often a hash table, a counter map, a cache, or an in-memory index, is accessed by many threads at once. |
| [Map-Reduce](map-reduce.md) | canonical | 7,927 | A team has a dataset far too large to process on one machine in an acceptable amount of time, and the transformation they need to run over it decomposes into two things. |
| [Monitor Object](monitor-object.md) | canonical | 6,457 | An object holds mutable state that more than one thread will call methods on concurrently. |
| [Parallel Scatter-Gather](parallel-scatter-gather.md) | canonical | 9,946 | A single logical answer depends on several independent pieces of work, and those pieces do not depend on each other. |
| [Phaser](phaser.md) | established | 7,798 | A team of workers needs to pass through a sequence of stages together, where no worker may begin stage N+1 until every worker that is still participating has finished stage N, and ... |
| [Pipeline Parallelism](pipeline-parallelism.md) | canonical | 7,255 | A program has to apply several distinct transformations to a large or unbounded stream of items, and the transformations are heterogeneous. |
| [Proactor](proactor.md) | canonical | 7,282 | A server, or any program, needs to service many concurrent long-running operations, most commonly network reads and writes, disk I/O, or timers, without paying the cost of one ... |
| [Producer-Consumer](producer-consumer.md) | canonical | 6,435 | A piece of work is generated by one part of a system at a rate, and shape, that does not match the rate or shape at which another part of the system can consume it. |
| [Rate Limiter](rate-limiter.md) | canonical | 6,898 | A shared, finite resource is exposed to a population of independent callers whose combined demand can exceed the resource's safe operating capacity at any given moment, and there ... |
| [Reactor](reactor.md) | canonical | 8,484 | A server accepts many concurrent client connections, and at any instant almost all of them are idle. |
| [Read-Copy-Update](read-copy-update.md) | canonical | 9,591 | A data structure is read far more often than it is changed, and the readers must never be made to wait for a writer, ever, not even briefly, because the read path sits on a hot ... |
| [Read-Write Lock](read-write-lock.md) | canonical | 7,855 | A single piece of shared, mutable state is accessed by multiple threads. |
| [Scheduler](scheduler.md) | canonical | 6,621 | A system has more units of work that want to run than it has execution resources to run them on, or those units of work become eligible at different and unpredictable times, and ... |
| [Scoped Locking](scoped-locking.md) | canonical | 8,785 | A piece of code acquires a lock to protect a critical section, and every path out of that critical section, the normal return, the early return, the thrown exception, the break ... |
| [Semaphore](semaphore.md) | canonical | 8,341 | A fixed, known number of interchangeable resources exist. |
| [Strategized Locking](strategized-locking.md) | canonical | 9,027 | A reusable component, a cache, a connection pool, a queue, a counter, a buffer manager, is built once and deployed into more than one concurrency environment. |
| [Structured Concurrency](structured-concurrency.md) | established | 7,965 | A function spawns concurrent work, a network call, a background computation, a fan-out to several services, and returns before that work is guaranteed to be done. |
| [Thread Pool](thread-pool.md) | canonical | 7,592 | A server, or any long-running process, receives a stream of independent units of work. |
| [Thread-Safe Interface](thread-safe-interface.md) | canonical | 8,248 | An object holds mutable state that more than one thread can reach at the same time, and the object exposes more than one public operation on that state. |
| [Thread-Specific Storage](thread-specific-storage.md) | canonical | 10,259 | A piece of state is logically global, in the sense that every function in a call chain wants to read or write it through one shared name, and yet the state must physically differ ... |
| [Work Queue](work-queue.md) | canonical | 7,614 | A system receives units of work that are independent of each other, and the rate at which work arrives does not match the rate at which any single processor can do it. |
| [Work Stealing](work-stealing.md) | canonical | 9,657 | A program decomposes into many small units of work, and the units are created dynamically during execution rather than known up front. |

## Reading order

Entries are independent. Each one names the patterns it composes with and
the patterns it conflicts with in dimension 13, so following those links
gives a better path than reading top to bottom.

Generated by `tools/gen-indexes.py`. Do not edit by hand.
