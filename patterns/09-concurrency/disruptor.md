---
name: Disruptor
slug: disruptor
family: 09-concurrency
category: Concurrency
aliases: [LMAX Disruptor, Ring Buffer Messaging Pattern]
first_described: "Thompson, LMAX Development Team, 2011"
maturity: established
related: [producer-consumer, pipeline, object-pool, mediator, chain-of-responsibility, observer]
incompatible_with: []
verified: 2026-08-02
---

# Disruptor

## 1. Name, aliases, and lineage

The canonical name is Disruptor. It is also called the LMAX Disruptor, after the
company that built it, and occasionally described in general terms as a ring
buffer messaging pattern when a team wants the design without the specific
library. The pattern was designed and open sourced by LMAX, a financial
trading venue, and first written up in a technical paper hosted on the
project's own site and dated 2011-06-22 in its file metadata, with Martin
Thompson as the author recorded in that metadata
([Disruptor technical paper PDF](https://lmax-exchange.github.io/disruptor/files/Disruptor-1.0.pdf),
verified 2026-08-02). The wider public introduction to the same ideas came a
few weeks later from Martin Fowler, who wrote up the surrounding LMAX
architecture, including the Disruptor's role in it, on 12 July 2011
([Fowler, "The LMAX Architecture"](https://martinfowler.com/articles/lmax.html),
verified 2026-08-02).

The name itself is a pun on the company's stated goal of disrupting the
exchange business, and the library kept the name once it moved out of LMAX and
into general use as an Apache 2.0 licensed open source project on GitHub
([LMAX-Exchange/disruptor repository](https://github.com/LMAX-Exchange/disruptor),
verified 2026-08-02). The project describes itself plainly as a
"High Performance Inter-Thread Messaging Library" in that repository, and the
official project site frames the goal as removing the latency that queues were
adding between processing stages
([Disruptor project overview](https://lmax-exchange.github.io/disruptor/),
verified 2026-08-02).

Three related terms are worth separating before going further, because they
get flattened together in casual conversation.

- **Ring buffer, the data structure.** A fixed-size circular array addressed
  with modular arithmetic. Ring buffers on their own say nothing about
  concurrency, ownership, or how a reader knows what is safe to read. Many
  single-threaded systems use a ring buffer purely as a bounded FIFO.
- **Disruptor, the concurrency pattern.** A ring buffer combined with a
  specific set of coordination primitives, a monotonically increasing sequence
  per producer and per consumer, a barrier that lets a consumer discover how
  far it may safely read, and an explicit publish step that makes a slot
  visible only once it is fully written. The pattern's identity comes from
  that coordination machinery, not from the array underneath it.
- **The com.lmax.disruptor library.** The specific Java implementation that
  ships classes named `RingBuffer`, `Sequence`, `SequenceBarrier`, and the
  rest. A team can implement the Disruptor pattern in any language without
  touching this library, and this entry does exactly that in three languages
  later on.

A useful test for whether a design is genuinely the Disruptor pattern rather
than a plain ring buffer. If removing the sequence barrier and the gating
sequence does not change correctness, it was never the Disruptor to begin
with, it was a ring buffer with a lock bolted on somewhere else.

## 2. Problem and context

Picture a system that has to move a stream of small, frequent messages
between threads and needs the handoff itself to add almost nothing to the
total latency budget. A market data feed handler passing ticks to a pricing
engine. A logging framework moving log events from an application thread to
an I/O thread. A trading engine passing orders through validation, risk
checking, and matching in sequence. In every one of these the obvious first
choice is a blocking queue, `ArrayBlockingQueue` in Java or an equivalent in
any other runtime, and for most systems that choice is fine.

It stops being fine once the target latency for the handoff itself drops into
the tens of nanoseconds to low microseconds, and the throughput target climbs
into the tens of millions of messages per second on one core. Beyond that
point the queue itself becomes the bottleneck, and the reason is not the
algorithm inside the queue, it is the hardware underneath it. LMAX's own
account of building their exchange states plainly that performance testing
showed queues between processing stages were the source of the latency they
were trying to remove ([Disruptor project overview](https://lmax-exchange.github.io/disruptor/),
verified 2026-08-02). Fowler's write up of the same system names the specific
mechanisms behind that observation, which is worth restating because it is
the whole reason the pattern exists rather than a generic queue with padding
added to it.

A conventional bounded queue with a head index and a tail index written by
different threads places both indices close together in memory. Two cores
that write to memory addresses on the same cache line invalidate each other's
cached copy on every write even though they are logically writing to
different variables, a phenomenon usually called false sharing. Fowler's
article calls this out directly as a driver of the design, describing how the
Disruptor pads its sequence counters onto their own cache lines specifically
to avoid it ([Fowler, "The LMAX Architecture"](https://martinfowler.com/articles/lmax.html),
verified 2026-08-02). A second driver is that a queue built around locks
requires kernel arbitration whenever a thread must wait, and that arbitration
cost, plus the unpredictability of when the scheduler will run the waiting
thread again, produces both average latency and tail latency that are far
worse than the CPU work alone would suggest. A third driver, specific to
managed runtimes like the JVM, is garbage. A queue of boxed message objects
that are allocated on publish and discarded after consumption keeps handing
young objects to the collector, and once enough of those objects are promoted
to the old generation before they can be collected, a full garbage collection
pause becomes a latency spike that dwarfs everything the algorithm was trying
to save.

The context in which the Disruptor becomes the right answer, then, is not
"any concurrent producer-consumer problem". It is specifically a
single-process, shared-memory, multi-core system with a small, bounded,
mostly-fixed-shape message and a latency or throughput requirement tight
enough that the coordination overhead of a general-purpose queue is itself
the problem being solved. Everywhere else, a blocking queue remains the
correct, simpler default.

## 3. Forces

Several of the judgements below are engineering trade-offs weighed from how
the pattern behaves in practice, not facts sourced to a document, and are
labelled that way.

- **Throughput against fairness.** The pattern is built for one producer
  publishing as fast as possible and one or more consumers draining as fast
  as possible. It has no concept of fairness among multiple unrelated
  producers, and the multi-producer variant adds a compare-and-swap step
  specifically to serialize the one operation that must be serialized, the
  claim of a slot, while leaving everything else lock free.
- **Mechanical sympathy against portability.** Padding a sequence counter
  onto its own cache line, choosing a busy-spin wait strategy, and pinning
  threads to cores are all decisions made in service of a specific
  processor's cache line size and a specific deployment's spare core budget.
  Move the same code to a shared, oversubscribed virtual machine and several
  of those decisions stop paying for themselves and can make things worse.
  This is judgement drawn from how the pattern is deployed in production
  rather than a documented guarantee.
- **Predictable latency against average latency.** A busy-spin consumer wakes
  within nanoseconds of data becoming available because it never sleeps. A
  blocking consumer has a lower resource footprint at rest but a worse and
  less predictable wake-up latency because it depends on the operating
  system's scheduler. The four wait strategies documented by the project
  exist specifically to let a team pick a point on this curve rather than
  accept one default for every workload
  ([Disruptor user guide](https://lmax-exchange.github.io/disruptor/user-guide/index.html),
  verified 2026-08-02).
- **Garbage-free operation against ease of use.** Preallocating every slot's
  event object once, at ring buffer construction time, and mutating those
  objects in place on every publish removes per-message allocation entirely.
  It also means every field of an event must be assigned on every publish,
  including fields that happen to match the previous occupant of that slot,
  because a stale field silently carries data forward. This is a discipline
  a team has to maintain by hand, and it is judgement, drawn from the failure
  modes below, that this is the single most common way the pattern is
  misused.
- **Bounded capacity against unbounded queueing.** A ring buffer is a fixed
  size, chosen once, and a producer that outruns every consumer eventually
  has to slow down rather than let memory grow without limit. This is a
  design choice in the pattern's favor for operability, a fixed-size buffer
  is easy to reason about and impossible to run a process out of memory with,
  but it pushes the question of what happens when a consumer falls behind
  onto the team, who must decide whether the producer blocks, drops, or
  switches strategy.
- **Cognitive load against the built-in familiarity of a queue.** Every
  engineer already understands `put` and `take`. Very few already understand
  claim, publish, sequence barriers, and gating sequences on first
  encounter. That unfamiliarity is a real, ongoing cost against the team that
  adopts the pattern, and it is judgement based on how often the pattern
  shows up misapplied in codebases that did not need it.

## 4. Applicability and non-applicability

Reach for the Disruptor when most of the following hold at once.

- A single process needs to move a high volume of small, roughly
  fixed-shape messages between threads and the coordination cost of the
  handoff is measurable against the total latency budget.
- The target throughput is in the tens of millions of messages per second
  per producer thread, the kind of number the project's own single-producer
  benchmark reports, roughly 78 to 89 million operations per second on the
  hardware it was measured on
  ([Disruptor user guide](https://lmax-exchange.github.io/disruptor/user-guide/index.html),
  verified 2026-08-02).
- The team can afford to preallocate the message shape and reuse it, which
  usually means the message is a small, mutable, fixed-field object rather
  than an arbitrary, variably-shaped payload.
- More than one downstream stage needs the same stream of events, and those
  stages have a known dependency order, journal before replicate before
  apply business logic, for example, rather than being genuinely independent
  consumers competing for one message each.
- The system already has, or can afford, spare CPU capacity to dedicate to
  the consumer threads, because several of the pattern's fastest
  configurations trade CPU cycles for latency.

Non-applicability. The pattern is the wrong tool, or at minimum an expensive
one, in these situations.

- The messages cross a network boundary, a process boundary, or any boundary
  where the shared-memory assumption the pattern is built on does not hold.
  A ring buffer coordinates threads inside one address space, it has nothing
  to say about serialization, retries, or partial failure across a wire.
- The workload is I/O bound rather than CPU bound. If a consumer spends most
  of its time waiting on a database or a remote call, the microseconds saved
  in the handoff are invisible against the milliseconds spent elsewhere, and
  a plain thread pool with a standard queue is simpler and equally fast in
  practice.
- Throughput is low, in the thousands or even low millions of messages per
  second, and latency in the low milliseconds is acceptable. A blocking
  queue meets that bar with far less code and far fewer ways to get it
  wrong.
- The message shape genuinely varies in size or structure from call to call
  in a way that defeats preallocation, for example arbitrary user-uploaded
  payloads. Forcing that shape into a fixed preallocated slot usually means
  boxing it into a wrapper anyway, which throws away the allocation benefit
  the pattern exists to provide.
- The team cannot dedicate a consumer thread, or spare CPU, to the workload.
  A busy-spin or yielding wait strategy on an oversubscribed host competes
  with every other thread on that core and can make the whole system slower,
  not faster.
- There is no genuine multi-core parallelism opportunity, the workload runs
  fine single threaded, and the change would introduce concurrency purely to
  use the pattern rather than to solve a measured problem. Introducing
  concurrency where none was needed is itself a cost, not a feature.

## 5. Structure

- **RingBuffer.** The fixed-size, power-of-two-length array that holds
  preallocated event slots, plus the logic a producer uses to claim the next
  writable slot and later publish it. Power-of-two sizing lets the
  implementation replace an expensive modulo operation with a cheap bitwise
  AND against a mask, which is confirmed directly in the project's own
  repository description of the ring buffer's design
  ([LMAX-Exchange/disruptor repository](https://github.com/LMAX-Exchange/disruptor),
  verified 2026-08-02).
- **Sequence.** A padded, monotonically increasing 64-bit counter. Every
  producer and every consumer owns one. A producer's sequence marks the
  highest slot it has published. A consumer's sequence marks the highest
  slot it has fully processed. The padding around the counter's value exists
  to give it its own cache line so that unrelated writes on a neighboring
  core do not invalidate it, which the project documents as a deliberate
  measure against false sharing
  ([Disruptor user guide](https://lmax-exchange.github.io/disruptor/user-guide/index.html),
  verified 2026-08-02).
- **Sequencer.** The component that owns the claim protocol for producers. A
  single-producer sequencer needs no synchronization at all because only one
  thread ever calls it. A multi-producer sequencer uses a compare-and-swap
  loop to serialize the one moment that genuinely requires it, deciding
  which producer thread gets which sequence number, while leaving the actual
  write into the slot unsynchronized.
- **SequenceBarrier.** The object a consumer asks "how far may I safely
  read". It holds a reference to the sequence it is gated on, either the
  producer's published sequence directly, or the sequence of an upstream
  consumer it must wait for first, and it applies the wait strategy while
  the answer is not yet available. The project's own description of the
  barrier states it "contains the logic to determine if there are any events
  available for the consumer to process"
  ([Disruptor user guide](https://lmax-exchange.github.io/disruptor/user-guide/index.html),
  verified 2026-08-02).
- **WaitStrategy.** The pluggable policy for what a thread does while it is
  blocked on a barrier. The project ships at minimum a blocking strategy
  built on a lock and a condition variable, a sleeping strategy built on
  parking with a short timeout, a yielding strategy that spins and calls
  `Thread.yield`, and a pure busy-spin strategy with no yield at all,
  ordered here from lowest CPU use and highest latency to highest CPU use
  and lowest latency
  ([Disruptor user guide](https://lmax-exchange.github.io/disruptor/user-guide/index.html),
  verified 2026-08-02).
- **EventFactory and EventTranslator.** The preallocation and mutation
  contract. The factory is called once per slot when the ring buffer is
  constructed, to build the reusable event object that will live in that
  slot for the process's lifetime. The translator is the piece of code
  supplied at publish time to copy the actual message fields into whichever
  reused object the sequencer handed back, which is the mechanism that
  keeps the design free of per-message allocation
  ([Disruptor user guide](https://lmax-exchange.github.io/disruptor/user-guide/index.html),
  verified 2026-08-02).
- **EventProcessor and EventHandler.** The consumer side. An event processor
  is the loop that owns a consumer's sequence, waits on its barrier, and
  drains a batch of newly available slots. The event handler is the small
  piece of business logic the processor calls once per event inside that
  batch.
- **Gating sequence.** Not a distinct class so much as a role. Whichever
  sequence a producer or an upstream consumer must not overtake is that
  actor's gating sequence. A producer is gated on the slowest consumer
  reading from the buffer, so that it can never publish into a slot that has
  not yet been consumed. This is the mechanism that gives the pattern its
  backpressure without any lock, and it is the single detail that separates
  a Disruptor from a bare ring buffer with no coordination.

## 6. ASCII structure diagram

```
                         claim / publish
        producer  ----------------------------->  cursor sequence
             |                                          |
             v                                          v
        +----+----+----+----+----+----+----+----+----+----+
 slots  | e0 | e1 | e2 | e3 | e4 | e5 | e6 | e7 | .. |e(n-1)|
        +----+----+----+----+----+----+----+----+----+----+
             ^  index = sequence & (size - 1), size is power of two
             |
   +---------+---------+          +---------------------+
   |  SequenceBarrier   | <------- | consumer sequence   |
   |  (gates producer)  |          | (journaler)         |
   +--------------------+          +-----------+---------+
                                                |
                                    then()      v
                                    +---------------------+
                                    | consumer sequence    |
                                    | (business logic)     |
                                    +-----------------------+

   producer may not claim a slot the slowest consumer has not
   yet consumed. that consumer's sequence is the producer's
   gating sequence.
```

## 7. Dynamics

The runtime flow has four repeating steps for a producer and a mirrored four
steps for each consumer, and the two sides never take a lock against each
other. This description is written from the mechanics documented across the
project's user guide and repository, combined into a single ordered account
([Disruptor user guide](https://lmax-exchange.github.io/disruptor/user-guide/index.html);
[LMAX-Exchange/disruptor repository](https://github.com/LMAX-Exchange/disruptor),
both verified 2026-08-02).

```
PRODUCER                                  CONSUMER
--------                                  --------
1. claim next sequence n                  1. ask barrier for highest
   (single producer: local counter++         published sequence >= my
    multi producer: CAS loop)                 next-to-process sequence
   spin if n - bufferSize would               spin or park per WaitStrategy
   overtake the gating (slowest              while none is available yet
   consumer) sequence
                                           2. read slots from my
2. write full event fields into              next-to-process sequence
   slot[n & mask], every field,              up to the available sequence,
   including ones that repeat the            as a batch
   previous occupant's value
                                           3. call the EventHandler once
3. publish: store n into the                 per event in that batch
   producer's cursor sequence with
   a release-ordered write so the         4. advance my own sequence to
   slot's contents are visible               the last processed value,
   before the sequence number is             which becomes the gating
   observed by any consumer                  sequence for whichever
                                              producer or downstream
4. repeat from step 1 for the                consumer depends on me
   next message
```

The two properties that make this safe without a lock are the ordering
guarantee on the publish step, the event's data must become visible to other
threads strictly before the sequence number that announces it, and the
gating check on the claim step, a producer or an upstream stage can never
claim a slot that a downstream reader has not yet finished with. Both
guarantees are enforced entirely through the sequence values and the memory
ordering of reading and writing them, never through a mutex.

Batching happens naturally as a side effect of this loop rather than as a
separate mechanism. If a consumer falls behind while a producer publishes
several sequences in a row, the next time that consumer checks its barrier it
sees every one of those sequences already available and processes them as one
batch instead of waking up once per message. Fowler's account of the design
calls this out directly as a latency-reducing effect that appears exactly
when the system is under load, which is also when it matters most
([Fowler, "The LMAX Architecture"](https://martinfowler.com/articles/lmax.html),
verified 2026-08-02).

## 8. Implementation variants

- **Single producer sequencer.** No compare-and-swap anywhere on the
  publishing path, because only one thread ever advances the producer
  sequence. This is the fastest configuration the project ships and the one
  its own benchmark reports at roughly 78 to 89 million operations per
  second on the hardware it measured
  ([Disruptor user guide](https://lmax-exchange.github.io/disruptor/user-guide/index.html),
  verified 2026-08-02).
- **Multi producer sequencer.** A compare-and-swap loop claims a contiguous
  range of sequences for whichever producer thread wins the race, at a
  documented cost, the same source reports roughly 26 to 29 million
  operations per second under contention from multiple producer threads on
  the same hardware ([Disruptor user guide](https://lmax-exchange.github.io/disruptor/user-guide/index.html),
  verified 2026-08-02).
- **Wait strategy selection.** The blocking, sleeping, yielding, and
  busy-spin strategies documented above are not one design choice, they are
  four separate deployment profiles, and swapping between them is usually
  the first and cheapest tuning knob a team reaches for once a Disruptor
  based system is in production.
- **Consumer dependency graphs.** The Disruptor DSL lets a team wire several
  event handlers into parallel stages, sequential stages, or a mix of both.
  Two independent handlers reading the same events in parallel, followed by
  a third handler that only proceeds once both of the first two have
  finished, is the documented shape, expressed with `handleEventsWith` for
  the parallel stage and `then` for the dependent stage
  ([Disruptor user guide](https://lmax-exchange.github.io/disruptor/user-guide/index.html),
  verified 2026-08-02). Fowler's account of the LMAX system itself describes
  exactly this three-stage shape in production, a journaler and a replicator
  running in parallel off the same input, with the business logic stage
  gated behind both of them
  ([Fowler, "The LMAX Architecture"](https://martinfowler.com/articles/lmax.html),
  verified 2026-08-02).
- **Hand rolled minimal implementations.** A team that only needs the core
  claim, publish, gate, and wait mechanics, without the full DSL, event
  translator abstraction, or worker pool support, can implement a small
  single-producer, single-consumer version directly on top of an atomic
  64-bit counter and a fixed array, which is what the three code samples in
  this entry do, each in a different language, to demonstrate the mechanics
  without depending on the library.
- **Ports and reimplementations outside Java.** The pattern's ideas travel.
  The project's own site notes that a .NET port of the Disruptor exists
  alongside the Java original ([Disruptor project overview](https://lmax-exchange.github.io/disruptor/),
  verified 2026-08-02), and the mechanics translate directly into any
  language with atomic integers and a memory model that supports
  acquire and release ordering, which is why the Go and Rust samples below
  are implemented from first principles rather than as bindings to the Java
  library.

The real, published `com.lmax.disruptor` public API differs in naming and
ceremony from the from-scratch samples in this entry, without differing in
the underlying mechanics. A minimal sketch of that API's shape, shown here as
plain text rather than compiled code because the library is not vendored in
this repository, looks like this.

```text
EventFactory<OrderEvent> factory = OrderEvent::new;
Disruptor<OrderEvent> disruptor =
    new Disruptor<>(factory, bufferSize, threadFactory,
                     ProducerType.SINGLE, new YieldingWaitStrategy());

disruptor.handleEventsWith(journaler, replicator)
         .then(businessLogicHandler);

RingBuffer<OrderEvent> ringBuffer = disruptor.start();
long sequence = ringBuffer.next();
try {
    OrderEvent event = ringBuffer.get(sequence);
    event.setOrderId(orderId);
    event.setPrice(price);
} finally {
    ringBuffer.publish(sequence);
}
```

## 9. Known production uses

- **LMAX Exchange.** The pattern's origin and its first production
  deployment. The project's own overview states plainly that the Disruptor
  "grew out of LMAX's research into concurrency, performance and
  non-blocking algorithms and today forms a core part of their Exchange's
  infrastructure" ([LMAX-Exchange/disruptor repository wiki](https://github.com/LMAX-Exchange/disruptor/wiki),
  verified 2026-08-02).
- **Apache Log4j2, asynchronous loggers.** Log4j2's asynchronous logging
  mode is built directly on the LMAX Disruptor rather than on a queue. The
  project's own manual states it explicitly, "Asynchronous loggers have been
  a new feature since Log4j 2. They are based on LMAX Disruptor, a lock-free
  inter-thread communication library, instead of queues", and further
  documents a configurable ring buffer size defaulting to 256 times 1024
  slots, sized to absorb bursts without ever growing or shrinking at runtime
  ([Log4j2 asynchronous logging manual](https://logging.apache.org/log4j/2.x/manual/async.html),
  verified 2026-08-02).
- **Apache Storm, storm-core.** Storm's core module carried a direct Maven
  dependency on the `com.lmax:disruptor` artifact for its internal executor
  message queues in its 1.x release line, confirmed by the dependency block
  present in the `storm-core` module's build file at tag v1.2.3
  ([Apache Storm storm-core pom.xml, tag v1.2.3](https://raw.githubusercontent.com/apache/storm/v1.2.3/storm-core/pom.xml),
  verified 2026-08-02). Reviewing the current default branch of the project
  showed no direct Disruptor dependency in the equivalent module, so this
  use is best described as historical rather than current, and is included
  because it demonstrates real, sustained adoption of the pattern outside
  LMAX for a substantial period rather than a passing experiment.

## 10. Consequences

Positive.

- Removes lock arbitration from the hot path entirely on the read side and
  reduces it to a single compare-and-swap on the write side only when there
  is more than one producer, which is the direct cause of the throughput
  numbers cited in dimension 8.
- Produces predictable, low tail latency because there is no lock queue for
  a thread to sit in, and because the wait strategy is chosen deliberately
  rather than inherited from a generic queue implementation's default
  blocking behavior.
- Removes per-message allocation once the event objects are fully
  preallocated and reused, which removes an entire class of garbage
  collection pause from the system's latency profile in a managed runtime.
- Makes the batching effect an automatic consequence of the design rather
  than an optimization a team has to add later, a consumer that falls
  behind processes a batch on its next wake-up instead of one message at a
  time, which improves throughput exactly when the system is under load.
- Keeps the business logic itself trivially testable, because a
  single-writer consumer can be exercised by calling its handler method
  directly with a constructed event, with no thread, no mock queue, and no
  timing dependency involved at all.

Negative.

- Introduces a fixed capacity a team must size correctly ahead of time. Too
  small and the producer stalls under a burst it should have absorbed. Too
  large and the system wastes memory on preallocated slots that sit idle.
- Adds real cognitive load. Claim, publish, sequence barrier, and gating
  sequence are unfamiliar vocabulary to most engineers on first encounter,
  and debugging a subtle sequence math error is harder than debugging a
  stuck lock, because there is no lock to inspect, only two numbers that
  should have agreed and did not.
- Trades CPU for latency on the aggressive end of the wait strategy range.
  A busy-spin consumer occupies its core fully even when idle, which is a
  real operational cost on shared hardware and a real decision a team has
  to make consciously rather than inherit by default.
- Couples correctness to memory ordering details, acquire and release
  semantics on the sequence read and write, that most application code
  never has to reason about directly. A hand rolled implementation that gets
  this wrong fails intermittently and only under real concurrent load,
  which is exactly the kind of bug that is expensive to find.
- Assumes shared memory and a single process. None of the throughput or
  latency benefit survives a network hop, so the pattern solves nothing for
  a distributed system boundary and can mislead a team that reaches for it
  as a general messaging solution rather than an intra-process one.

## 11. Failure modes and misuse

The following are drawn from how the pattern is known to fail in production,
stated as engineering judgement rather than sourced facts, with the
observable symptom given first because that is what a reader will actually
encounter.

- Symptom, a consumer thread pegs one CPU core at 100 percent even while the
  system is idle and no messages are flowing. Cause, a busy-spin or
  yielding wait strategy was chosen without a matching decision to isolate
  or dedicate a core to that thread, so the spin loop runs continuously
  regardless of load. Fix, switch to a blocking or sleeping wait strategy
  for consumers that do not need nanosecond wake-up latency, and reserve the
  aggressive strategies for the specific threads on the specific hardware
  where the trade is actually worth it.
- Symptom, the producer occasionally stalls for a period far longer than
  any single message's processing time should explain. Cause, the ring
  buffer is sized too small relative to the slowest consumer's worst case
  processing latency, so the producer's claim step hits the gating sequence
  and has to wait for that consumer to catch up before it can wrap around
  and reuse a slot. Fix, size the buffer to cover the worst case stall a
  downstream consumer can experience, not the average case, and treat a
  producer stall event as a metric worth alerting on rather than a silent
  occurrence.
- Symptom, a consumer occasionally reads a field value that belongs to a
  different, earlier message than the one it thinks it is reading. Cause,
  the preallocated event object was not fully overwritten on every publish,
  so a field left unset on this publish still carries the value from
  whichever earlier message last occupied that slot. Fix, treat every field
  of the reused event object as mandatory to assign on every publish, and
  consider clearing the object at the start of the translator step so that
  a missing assignment fails loudly rather than silently carrying stale
  data forward.
- Symptom, the system was supposed to be garbage free but the collector's
  logs still show regular allocation and promotion activity proportional to
  message volume. Cause, the preallocated event object holds a nested
  mutable field, a list, a string builder, or a boxed number, that gets
  replaced with a freshly allocated instance on every publish instead of
  being mutated in place. Fix, preallocate the nested structures too, and
  mutate their contents rather than replacing the reference.
- Symptom, throughput collapses under multiple producer threads even though
  a single producer benchmark on the same hardware looked fine. Cause, the
  team assumed the single-producer sequencer's lock-free performance would
  carry over unchanged to multiple producers, without accounting for the
  compare-and-swap contention the multi-producer sequencer introduces at
  the claim step. Fix, benchmark the actual producer topology the system
  will run in production, not a simplified single-producer case, and
  consider funnelling multiple logical producers through one physical
  producer thread if the workload allows it.
- Symptom, the pattern was adopted for a service that talks to a database
  or a downstream HTTP call on every message, and the team is disappointed
  that overall latency barely moved. Cause, the Disruptor only ever
  addresses the cost of the in-process handoff between threads, and that
  cost was never the bottleneck in an I/O bound workload to begin with.
  Fix, profile the actual latency budget before adopting the pattern, and
  recognise that this is a non-applicability case rather than a tuning
  problem.

## 12. Trade-off matrix

Named alternatives, each a real pattern or a real, commonly reached for
mechanism rather than a strawman.

| Force | Disruptor | ArrayBlockingQueue (locked bounded queue) | CSP channel (Go channels) | Lock-free MPMC queue (for example JCTools) |
|---|---|---|---|---|
| Peak throughput, single writer | Highest, tens of millions of ops per second, no lock on the hot path | Bounded by lock arbitration, typically an order of magnitude lower | Comparable structure to a queue, still pays scheduler and channel overhead | High, comparable in the multi-producer case, no gating consumer graph |
| Tail latency predictability | Strong when tuned with an aggressive wait strategy, weak default without tuning | Weak, dependent on OS scheduler wake-up for blocked threads | Moderate, runtime scheduler manages goroutine wake-up efficiently but is still a scheduler | Moderate, no lock but still relies on the caller's own wait behavior |
| Backpressure model | Explicit, gating sequence blocks the producer against the slowest consumer | Explicit, blocking put on a full queue | Explicit, an unbuffered or small buffered channel blocks the sender | Usually none built in, caller must add it |
| Garbage pressure in a managed runtime | None once preallocated and mutated in place | One allocation per enqueued object unless pooled by hand | Depends on payload, channels themselves add no per-message allocation beyond the payload | Depends on payload, same as above |
| Multiple independent downstream consumers of the same stream | Built in via the consumer dependency graph, `handleEventsWith` and `then` | Not built in, needs one queue per consumer or a fan-out wrapper | Not built in, needs one channel per consumer or a fan-out goroutine | Not built in, single-consumer or competing-consumer semantics only |
| Learning curve and debuggability | Steep, unfamiliar vocabulary, concurrency bugs show up only under real load | Shallow, most engineers already know queues | Shallow within a Go codebase, channels are idiomatic there | Moderate, still a lock-free structure with its own subtleties |
| Fit for cross-process or cross-network messaging | None, in-process shared memory only | None, same limitation | None, same limitation | None, same limitation |

## 13. Related and incompatible patterns

- **Producer-Consumer.** The Disruptor is a specific, highly tuned
  implementation of the producer-consumer relationship. Every generic
  description of producer-consumer applies to it, and the pattern's value
  is entirely in how it implements that relationship without a lock.
- **Pipeline and Chain of Responsibility.** The consumer dependency graph,
  built with `handleEventsWith` followed by `then`, is a pipeline where each
  stage's gating sequence is the previous stage's output sequence. A team
  that already understands Chain of Responsibility will recognise the shape
  immediately, the difference is that each link in this chain runs on its
  own thread and reads from a shared buffer rather than passing an object
  reference directly to the next handler.
- **Object Pool.** The preallocated, reused event objects inside every ring
  buffer slot are an Object Pool in miniature, fixed in count, indexed by
  position rather than checked out and returned, and reused for the life of
  the process.
- **Observer.** An EventHandler resembles an Observer in that it reacts to
  something happening upstream, but the resemblance stops at intent. An
  Observer is typically pushed a single event synchronously on the
  publisher's own thread. An EventHandler is pulled a batch of events on its
  own thread, at its own pace, gated by a barrier, which is a materially
  different runtime shape even though both patterns answer "how does this
  code find out that something happened".
- **Mediator.** The Disruptor DSL orchestrator that wires producers,
  consumers, and their dependency graph together plays a role similar to a
  Mediator, centralising the wiring decisions so that individual handlers
  do not need to know about each other directly.
- **Incompatible or conflicting designs.** Any design that assumes
  unbounded queue growth as a safety valve, an actor system with an
  unbounded mailbox, for example, sits in direct tension with the
  Disruptor's fixed-capacity, backpressure-by-blocking model. Combining the
  two usually means picking one philosophy for backpressure and applying it
  consistently, rather than mixing an unbounded mailbox in front of a
  bounded ring buffer and hoping the mismatch resolves itself.

## 14. Refactoring path in and out

Introducing the pattern into a system that does not already have it is safest
done in the order below, because each step is independently verifiable before
the next one adds risk.

1. Profile first. Confirm, with real measurements, that the inter-thread
   handoff itself, not the work done on either side of it, is the latency or
   throughput bottleneck. Skipping this step is the single most common
   reason teams adopt the pattern for no measured benefit.
2. Extract the handoff behind a small interface, publish this message,
   consume the next message, so the call sites do not depend on the concrete
   queue implementation. This is the standard Extract Interface move applied
   specifically to the boundary that is about to change.
3. Implement the new side of that interface with a minimal, single-producer,
   single-consumer ring buffer, using the safest available wait strategy
   first, a blocking strategy, so behaviour under load stays close to the
   queue it is replacing while the team gets comfortable with the new
   vocabulary.
4. Swap the implementation behind the interface and verify correctness
   under load with the tests described in dimension 15 before touching
   anything else.
5. Only after correctness is verified, tune the wait strategy toward
   yielding or busy-spin, and only if the measured latency or throughput
   still falls short of the target after step 4.
6. If multiple downstream consumers are needed, introduce the dependency
   graph incrementally, one additional handler at a time, verifying the
   gating behaviour after each addition rather than wiring the whole graph
   in one change.

Removing the pattern, when the throughput or latency need has genuinely gone
away, or when the team decides the maintenance cost outweighs the benefit, is
the mirror image and is usually simpler than the introduction, because the
interface from step 2 above is still there.

1. Confirm current load no longer requires the pattern's throughput or
   latency profile, using the same measurement discipline as step 1 of the
   introduction path.
2. Replace the ring buffer implementation behind the existing interface with
   a standard bounded queue and an executor or thread pool.
3. Remove the preallocation and in-place mutation discipline from the event
   objects, since a standard queue does not require it, and let those
   objects go back to being allocated normally.
4. Delete the wait strategy tuning and any core pinning or isolation
   configuration that existed purely to support the ring buffer's
   consumers.

## 15. Testing and verification

The pattern's single biggest testing advantage is one Fowler calls out
directly about the LMAX system as a whole, that running the actual business
logic single threaded, driven by one sequence of preallocated events, makes
it possible to unit test that logic deterministically with no threading, no
mocking of a queue, and no timing dependency at all
([Fowler, "The LMAX Architecture"](https://martinfowler.com/articles/lmax.html),
verified 2026-08-02). In practice this means the EventHandler implementation
can and should be tested by constructing an event by hand, calling the
handler method directly, and asserting on the result, the same way any other
plain method is tested, with no ring buffer involved at all.

What genuinely requires concurrency-aware testing is the coordination
machinery itself, whether hand rolled or from the library, and the following
techniques cover the cases that matter.

- Contention tests. Start several producer threads against a shared,
  synchronized starting point, a `CountDownLatch` or equivalent barrier so
  they all begin claiming at roughly the same instant, and assert that every
  claimed sequence number is unique and that no message is ever lost or
  duplicated across the full run.
- Wrap-around tests. Publish more messages than the ring buffer's capacity
  while a consumer deliberately lags behind, and assert that the producer
  correctly blocks rather than overwriting a slot the consumer has not yet
  read, which is the single property that most distinguishes a correct
  Disruptor implementation from a buggy one.
- Gating tests. Wire a deliberately slow consumer stub into a multi-stage
  dependency graph and assert that a downstream stage never processes an
  event before every upstream stage it depends on has processed it first.
- Memory ordering stress tests. Run the contention and wrap-around tests
  repeatedly under load, on real multi-core hardware rather than only in a
  single-threaded test runner, because incorrect memory ordering in a hand
  rolled implementation is exactly the class of bug that a low-contention
  test run will not surface.
- Backpressure behavior tests. Assert explicitly on what happens when a
  producer is blocked waiting for a gating sequence to advance, whether that
  manifests as the producing thread parking, spinning, or returning a
  signal the caller can act on, since this is the property most likely to
  surprise an operator in production if it was never exercised in a test.

## 16. Observability signals

A healthy Disruptor based system, seen on a dashboard, shows a ring buffer
whose remaining capacity oscillates but never approaches zero, and consumer
sequences that stay close to the producer's cursor sequence at all times. The
following signals are the ones worth exposing explicitly, as engineering
judgement about what actually shows trouble first in production.

- Ring buffer remaining capacity, computed as the buffer size minus the gap
  between the producer's cursor sequence and the slowest consumer's
  sequence. A value that trends toward zero over time, rather than merely
  spiking under a burst, means a consumer is systematically falling behind
  the producer.
- Per-consumer sequence lag, the gap between each individual consumer's
  sequence and the producer's cursor sequence, tracked separately for every
  stage in a multi-consumer dependency graph. This is the single most useful
  signal for finding which specific stage is the slow one in a pipeline,
  rather than only knowing that the pipeline as a whole is behind.
- Producer stall count, a counter incremented every time a producer's claim
  step has to wait on the gating sequence rather than proceeding
  immediately. A rising rate here is the earliest warning that the ring
  buffer is undersized or a downstream consumer has degraded, well before
  the ring buffer's remaining capacity metric would show it.
- Wait strategy time spent, whether measured as park duration for a
  blocking or sleeping strategy, or as spin iteration counts for a
  yielding or busy-spin strategy, correlated against message volume. A
  sudden jump in this figure without a corresponding jump in volume points
  at a consumer that has slowed down for reasons unrelated to load, a
  downstream dependency, a garbage collection pause, or a scheduling issue
  on the host.
- Correlation with garbage collection pause events, in any managed runtime
  deployment, since a Disruptor based system that is genuinely garbage free
  should show no correlation at all between GC pause timing and consumer
  sequence lag spikes. A visible correlation is a direct signal that the
  preallocation discipline described in dimension 11 has been broken
  somewhere in the event objects.

## 17. Security and privacy implications

This pattern operates entirely inside one process's address space and never
crosses a network or a process boundary on its own, so it does not open a
network-facing attack surface, and this is a plain observation about its
scope rather than a sourced claim. Two implications are worth stating
explicitly rather than being left silent, because they are the kind of thing
a team building a system that handles sensitive data would want flagged.

The first is data retention inside preallocated memory. Because every event
slot is a long-lived, reused object rather than a freshly allocated one, a
sensitive field written into a slot on one publish remains present in that
object's memory until a later publish explicitly overwrites it. In a normal
running process this is invisible, the next publish always does overwrite
every field. It becomes visible the moment that memory is captured outside
the normal flow of the program, in a heap dump taken for debugging, in a
core dump after a crash, or in memory swapped to disk, where stale sensitive
data from several messages back can sit in the preallocated ring long after
the message that carried it was logically processed and forgotten by the
rest of the system. A team handling regulated or personal data through a
Disruptor based pipeline should treat this the same way it would treat any
other long-lived buffer holding sensitive fields, and consider whether
fields need to be explicitly cleared rather than merely overwritten, and
whether heap dumps and core dumps from that process need the same handling
discipline as the live data itself.

The second is the trust boundary implied by shared memory. Every producer and
every consumer wired into a ring buffer runs inside the same process with no
isolation between them, so a Disruptor is not, and should never be treated
as, a security boundary. Any code that can obtain a reference to the ring
buffer, or to an event handler registered on it, can read or write anything
another component publishes, with no access control of any kind. This is
fine and expected within a single trusted codebase, and it is the wrong
mechanism entirely for passing data between components that do not trust
each other, where a process boundary, an authenticated API, or a message
broker with its own access control is the correct tool instead.

## 18. References

1. Disruptor technical paper, LMAX, PDF file metadata records an author of
   Martin Thompson and a creation date corresponding to 2011-06-22 in the
   file's own timestamp.
   [https://lmax-exchange.github.io/disruptor/files/Disruptor-1.0.pdf](https://lmax-exchange.github.io/disruptor/files/Disruptor-1.0.pdf),
   verified 2026-08-02.
2. Disruptor project overview, LMAX Exchange. States the queue-latency
   origin story and the existence of a .NET port.
   [https://lmax-exchange.github.io/disruptor/](https://lmax-exchange.github.io/disruptor/),
   verified 2026-08-02.
3. LMAX-Exchange/disruptor, GitHub repository. Ring buffer, sequence,
   sequence barrier, producer types, wait strategies, event handler
   description, license, and star count.
   [https://github.com/LMAX-Exchange/disruptor](https://github.com/LMAX-Exchange/disruptor),
   verified 2026-08-02.
4. LMAX-Exchange/disruptor wiki, GitHub. States the Disruptor "forms a core
   part" of LMAX Exchange's infrastructure.
   [https://github.com/LMAX-Exchange/disruptor/wiki](https://github.com/LMAX-Exchange/disruptor/wiki),
   verified 2026-08-02.
5. Disruptor user guide, LMAX Exchange. Wait strategy descriptions,
   false sharing padding, EventFactory and EventTranslator, SequenceBarrier
   role, handleEventsWith and then dependency wiring, and single versus
   multi producer throughput figures.
   [https://lmax-exchange.github.io/disruptor/user-guide/index.html](https://lmax-exchange.github.io/disruptor/user-guide/index.html),
   verified 2026-08-02.
6. Martin Fowler, "The LMAX Architecture", 12 July 2011. Single-writer
   principle, mechanical sympathy, ring buffer and sequence description,
   false sharing padding, garbage collection concerns, batching effect
   under load, and the journaler and replicator parallel-stage example.
   [https://martinfowler.com/articles/lmax.html](https://martinfowler.com/articles/lmax.html),
   verified 2026-08-02.
7. Apache Log4j2, "Asynchronous Loggers", official manual. States that
   asynchronous logging is built on the LMAX Disruptor rather than a queue,
   and documents the configurable ring buffer size default of 256 times
   1024 slots.
   [https://logging.apache.org/log4j/2.x/manual/async.html](https://logging.apache.org/log4j/2.x/manual/async.html),
   verified 2026-08-02.
8. Apache Storm, `storm-core` module build file, tag v1.2.3. Contains a
   direct dependency on `com.lmax:disruptor`.
   [https://raw.githubusercontent.com/apache/storm/v1.2.3/storm-core/pom.xml](https://raw.githubusercontent.com/apache/storm/v1.2.3/storm-core/pom.xml),
   verified 2026-08-02.

## Code

The pattern is demonstrated here from first principles in three languages,
each implementing a minimal single-producer, single-consumer ring buffer
with a claim step, a publish step, a wait-for-availability step on the
consumer side, and an explicit gating sequence that stops the producer from
overtaking the consumer. All three samples were compiled or type-checked and
run locally against a total of 100000 published values, and all three
produced the correct sum of 4999950000, confirming that no message was lost,
duplicated, or corrupted across the wrap-around boundary of a 1024-slot
buffer.

### Java

```java
import java.util.concurrent.atomic.AtomicLong;

public final class SingleProducerRingBuffer {
    private static final int SIZE = 1024;
    private static final int MASK = SIZE - 1;

    private final long[] slots = new long[SIZE];
    private final AtomicLong cursor = new AtomicLong(-1);
    private final AtomicLong consumed = new AtomicLong(-1);
    private long producerSequence = -1;

    public long claim() {
        long candidate = producerSequence + 1;
        long wrapPoint = candidate - SIZE;
        while (wrapPoint > consumed.get()) {
            Thread.onSpinWait();
        }
        producerSequence = candidate;
        return candidate;
    }

    public void publish(long sequence, long value) {
        slots[(int) (sequence & MASK)] = value;
        cursor.lazySet(sequence);
    }

    public long waitFor(long sequence) {
        long available;
        while ((available = cursor.get()) < sequence) {
            Thread.onSpinWait();
        }
        return available;
    }

    public long get(long sequence) {
        return slots[(int) (sequence & MASK)];
    }

    public void markConsumed(long sequence) {
        consumed.lazySet(sequence);
    }

    public static void main(String[] args) throws InterruptedException {
        SingleProducerRingBuffer buffer = new SingleProducerRingBuffer();
        long total = 100_000;

        Thread consumerThread = new Thread(() -> {
            long nextToRead = 0;
            long sum = 0;
            while (nextToRead < total) {
                long available = buffer.waitFor(nextToRead);
                while (nextToRead <= available) {
                    sum += buffer.get(nextToRead);
                    buffer.markConsumed(nextToRead);
                    nextToRead++;
                }
            }
            System.out.println("consumed sum=" + sum);
        });
        consumerThread.start();

        for (long i = 0; i < total; i++) {
            long seq = buffer.claim();
            buffer.publish(seq, i);
        }
        consumerThread.join();
    }
}
```

The `producerSequence` field needs no atomic wrapper because only one
producer thread ever touches it, which is the single-writer principle this
entry describes in dimension 2. Only the two sequences that cross the
thread boundary, `cursor` and `consumed`, are atomic.

### Go

```go
package main

import (
	"fmt"
	"sync/atomic"
)

const size = 1024
const mask = size - 1

type ringBuffer struct {
	slots    [size]int64
	cursor   atomic.Int64
	consumed atomic.Int64
}

func newRingBuffer() *ringBuffer {
	r := &ringBuffer{}
	r.cursor.Store(-1)
	r.consumed.Store(-1)
	return r
}

func (r *ringBuffer) claim(next int64) int64 {
	wrapPoint := next - size
	for wrapPoint > r.consumed.Load() {
	}
	return next
}

func (r *ringBuffer) publish(sequence, value int64) {
	r.slots[sequence&mask] = value
	r.cursor.Store(sequence)
}

func (r *ringBuffer) waitFor(sequence int64) int64 {
	for {
		available := r.cursor.Load()
		if available >= sequence {
			return available
		}
	}
}

func (r *ringBuffer) get(sequence int64) int64 {
	return r.slots[sequence&mask]
}

func (r *ringBuffer) markConsumed(sequence int64) {
	r.consumed.Store(sequence)
}

func main() {
	buffer := newRingBuffer()
	const total = int64(100000)
	done := make(chan int64)

	go func() {
		var nextToRead int64
		var sum int64
		for nextToRead < total {
			available := buffer.waitFor(nextToRead)
			for nextToRead <= available {
				sum += buffer.get(nextToRead)
				buffer.markConsumed(nextToRead)
				nextToRead++
			}
		}
		done <- sum
	}()

	for i := int64(0); i < total; i++ {
		seq := buffer.claim(i)
		buffer.publish(seq, i)
	}

	sum := <-done
	fmt.Println("consumed sum=", sum)
}
```

The Go sample uses the calling loop's own counter, `i`, as the candidate
sequence passed into `claim`, since a single producer goroutine already owns
a sequential counter for free in its own `for` loop, and there is nothing a
separate producer sequence field would add over that.

### Rust

```rust
use std::sync::atomic::{AtomicI64, Ordering};
use std::sync::Arc;
use std::thread;

const SIZE: usize = 1024;
const MASK: i64 = (SIZE - 1) as i64;

struct RingBuffer {
    slots: [AtomicI64; SIZE],
    cursor: AtomicI64,
    consumed: AtomicI64,
}

impl RingBuffer {
    fn new() -> Self {
        const ZERO: AtomicI64 = AtomicI64::new(0);
        RingBuffer {
            slots: [ZERO; SIZE],
            cursor: AtomicI64::new(-1),
            consumed: AtomicI64::new(-1),
        }
    }

    fn claim(&self, next: i64) -> i64 {
        let wrap_point = next - SIZE as i64;
        while wrap_point > self.consumed.load(Ordering::Acquire) {
            std::hint::spin_loop();
        }
        next
    }

    fn publish(&self, sequence: i64, value: i64) {
        self.slots[(sequence & MASK) as usize].store(value, Ordering::Relaxed);
        self.cursor.store(sequence, Ordering::Release);
    }

    fn wait_for(&self, sequence: i64) -> i64 {
        loop {
            let available = self.cursor.load(Ordering::Acquire);
            if available >= sequence {
                return available;
            }
            std::hint::spin_loop();
        }
    }

    fn get(&self, sequence: i64) -> i64 {
        self.slots[(sequence & MASK) as usize].load(Ordering::Relaxed)
    }

    fn mark_consumed(&self, sequence: i64) {
        self.consumed.store(sequence, Ordering::Release);
    }
}

fn main() {
    let buffer = Arc::new(RingBuffer::new());
    let total: i64 = 100_000;

    let consumer_buffer = Arc::clone(&buffer);
    let consumer = thread::spawn(move || {
        let mut next_to_read: i64 = 0;
        let mut sum: i64 = 0;
        while next_to_read < total {
            let available = consumer_buffer.wait_for(next_to_read);
            while next_to_read <= available {
                sum += consumer_buffer.get(next_to_read);
                consumer_buffer.mark_consumed(next_to_read);
                next_to_read += 1;
            }
        }
        sum
    });

    for i in 0..total {
        let seq = buffer.claim(i);
        buffer.publish(seq, i);
    }

    let sum = consumer.join().unwrap();
    println!("consumed sum={}", sum);
}
```

The Rust sample makes the memory ordering explicit where Java and Go leave
it implicit inside their standard library primitives. The publish step uses
`Ordering::Release` on the cursor write specifically so that the slot write
immediately above it, using the cheaper `Ordering::Relaxed`, cannot be
reordered to happen after the cursor becomes visible to the consumer thread,
and the consumer's read of the cursor uses the matching `Ordering::Acquire`
to establish that same ordering from its side. This is the precise mechanism
dimension 7 describes in words, the event's data must become visible before
the sequence number that announces it, made explicit in the type system
rather than left to a general-purpose atomic wrapper's default behaviour.

A fourth language from the template's approved set, TypeScript, was
considered and deliberately left out. JavaScript and TypeScript run their
event loop on a single thread with no shared-memory multithreading exposed
to normal application code, so the specific coordination problem this
pattern solves, two threads racing over the same memory, does not exist
there in the form this pattern addresses, and a faithful sample would either
be a misleading single-threaded simulation or would need to reach for
`SharedArrayBuffer` and `Atomics` in a way that adds ceremony without adding
insight beyond what the Rust sample already shows explicitly.
