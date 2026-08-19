---
name: Communicating Sequential Processes
slug: communicating-sequential-processes
family: 09-concurrency
category: Concurrency
aliases: [CSP, Process Calculus Concurrency, Channel-Based Concurrency]
first_described: "Hoare 1978"
maturity: canonical
related: [actor-model, producer-consumer, pipeline, fan-out-fan-in, select-loop, worker-pool]
incompatible_with: [shared-mutable-state-with-locks]
verified: 2026-08-14
---

# Communicating Sequential Processes

## 1. Name, aliases, and lineage

Communicating Sequential Processes, almost always shortened to CSP, is a formal
language and a concurrency model in which independent sequential processes
interact exclusively by sending messages over explicit channels, rather than by
reading and writing shared memory. C. A. R. Hoare introduced it in the paper
"Communicating sequential processes," Communications of the ACM, volume 21,
issue 8, August 1978 (verified via the Wikipedia entry on Communicating
sequential processes, https://en.wikipedia.org/wiki/Communicating_sequential_processes,
2026-08-14, which gives the original venue and year and is corroborated by the
paper's continued citation as the founding CSP reference in every later
treatment of the model). Hoare later extended the 1978 paper into a full
process algebra with a formal semantics, published as the book "Communicating
Sequential Processes" (Prentice Hall International, 1985), which is the
citation the field usually means when it says "the CSP book."

The name is used in two overlapping but distinct senses that this entry keeps
separate throughout. The first sense is Hoare's process algebra, a
mathematical notation with operators for sequencing, choice, parallel
composition, and synchronization, used for specifying and verifying concurrent
systems. The second sense, the one most working engineers mean when they say
"CSP-style concurrency," is the programming idiom the algebra inspired.
independent goroutines, processes, or threads, each running its own
sequential logic, communicating only through typed channels rather than
shared variables. This entry is written for the second sense, the engineering
idiom, and calls out the formal algebra only where it explains why the idiom
behaves the way it does. Readers who need the full temporal-logic-adjacent
algebra, refinement checking, and the FDR model checker should treat this
entry as an on-ramp to Hoare's book, not a substitute for it.

The aliases in real circulation are "channel-based concurrency" and, less
formally, "share memory by communicating," which is the slogan the Go team
uses in its own documentation, quoted in dimension 9. "Process calculus
concurrency" is used in academic contexts alongside CSP's sibling calculi,
CCS from Robin Milner and the pi-calculus, which this entry distinguishes from
CSP in dimension 13 rather than treating as synonyms, because the three
differ in how they model synchronization and naming.

## 2. Problem and context

A program that needs to do more than one thing at once, serve many requests,
overlap I/O with computation, or use more than one CPU core, needs a way for
its concurrent parts to coordinate. The default coordination mechanism most
languages start from is shared mutable memory. two or more threads read and
write the same variables, and correctness depends on the programmer placing
locks, mutexes, or atomic operations around every access in exactly the right
places. This works, but it does not scale with team size or codebase size.
The set of variables that must be protected, and the order in which locks
must be acquired to avoid deadlock, is an invariant that lives only in the
programmer's head and in scattered comments. As the number of shared
variables and the number of threads touching them grows, the number of
possible interleavings grows combinatorially, and a correctness bug can sit
dormant for years before a rare interleaving triggers it in production.

CSP arises from a different starting question. instead of asking why does this
shared variable need protecting, CSP asks why is this variable shared at all.
If two computations only ever need to exchange a finite set of values at
specific points in their execution, and neither needs to read the other's
internal state at arbitrary times, then the coordination problem can be
recast as message passing over a channel that the language or runtime
implements once, correctly, rather than as ad hoc locking that every
programmer re-derives. The context in which CSP is the right tool is
therefore a system built from components with clear, sequential internal
logic that need to hand data to each other at well-defined points. producer
and consumer stages in a pipeline, a fan-out of workers pulling from a shared
queue, a request handler that needs a result from a background computation
by a deadline, or a supervisor that needs to fan a cancellation signal out to
many in-flight operations at once. The context in which CSP is the wrong
tool, covered in full in dimension 4, is a system whose components
genuinely need frequent, fine-grained access to a shared data structure,
where introducing a channel and a goroutine per access would replace one
kind of complexity with a slower and more indirect one.

## 3. Forces

CSP trades a set of specific costs for a set of specific benefits, and naming
both sides honestly is what separates an accurate account from marketing.

Coupling versus explicitness. Shared-memory concurrency couples every reader
and writer of a variable to the discipline of a lock that lives nowhere in
the type system. CSP moves that coupling into the channel itself, which is a
first-class, typed value that appears in a function's signature. This
transforms an implicit coupling, everyone touching this struct must hold
this mutex, into an explicit one, this function's only interface to the
outside world is these two channels. The force this favors is readability of
a single function in isolation, at the cost of needing to trace the graph of
channels across the whole program to understand global data flow.

Latency versus safety. A synchronous, unbuffered channel send blocks until a
receiver is ready, which is the mechanism CSP calls rendezvous. This gives a
strong guarantee, a value is never in flight without both parties agreeing on
the handoff, at the direct cost of latency. a fast producer is throttled to
the speed of the slowest consumer unless the channel is deliberately given a
buffer. Buffering trades that safety back for throughput, and choosing the
buffer size is itself a design decision with real consequences, covered in
dimension 11.

Consistency versus concurrency. Because CSP processes do not share memory,
there is no data race on the values exchanged over a channel, by
construction, as long as the language does not also expose an unenforced
back door to shared mutable state, a real gap in some CSP-influenced
languages discussed in dimension 17. What CSP does not give you for free is
consistency across multiple communicating processes taken together. two
goroutines can each correctly, race-freely, update their own local state
based on values received over channels, and the combination of those two
locally-correct updates can still represent a global inconsistency if the
protocol between them is designed wrong. CSP removes the low-level hazard,
data races, but does not remove the high-level hazard, distributed logic
errors, and treating no race detector warnings as no bugs is one of the
most common misuses of the pattern, discussed further in dimension 11.

Cost and cognitive load. A channel and a goroutine are cheap in a runtime
built for them, a few kilobytes of stack in Go for instance, but are not
free, and a system with thousands of long-lived goroutines each blocked on a
channel carries real memory and scheduler overhead. The cognitive load CSP
imposes is different in kind from lock-based cognitive load rather than
strictly lower. instead of asking which lock protects this variable, the
engineer must ask who owns this channel, who is allowed to close it, and
what happens to a goroutine that is still trying to send on it after every
receiver has gone away. Ownership of a channel is a discipline CSP demands
but, unlike a lock, does not enforce mechanically in most implementations.

Team topology. CSP scales well across a team boundary specifically because a
channel is a narrower, more reviewable interface than a raw pointer into
internal state that is only safe while a specific mutex is held. A reviewer
can audit a function's concurrency safety by reading its channel parameters
alone, without auditing every other file that might also hold a pointer into
the same struct. This is a genuine advantage of CSP over ambient shared
state in a large, multi-team codebase, and it is one of the reasons the
pattern is favored in systems languages designed for large engineering
organizations, discussed in dimension 9.

## 4. Applicability and non-applicability

Reach for CSP when the components of a concurrent system have their own
sequential internal logic and need to exchange discrete values at specific,
well-defined points, rather than sharing continuous access to the same data
structure. Concretely, useful cases include a pipeline where each stage
transforms a stream of values and hands the result to the next stage, a
fan-out of worker goroutines pulling tasks from one channel and pushing
results to another, a cancellation or timeout signal that many independent
operations need to observe at once, which a closed channel or a context
value propagates cleanly, a request-response boundary between a fast,
latency-sensitive caller and a slower background computation where the
channel is the contract, and any place where the alternative is a
mutex-protected shared struct whose invariant is only one goroutine touches
this at a time, because that promise is exactly what a channel can encode in
the type system instead of in a comment.

Do not reach for CSP in the following situations, and prefer the named
alternative instead.

- High-frequency, fine-grained shared state. A data structure that many
  goroutines need to read and write many times per millisecond, such as an
  in-memory cache or a counter incremented on every request, is usually
  better served by a mutex, an atomic operation, or a concurrent-map type
  than by routing every access through a channel and a dedicated owner
  goroutine. Sending a request over a channel and waiting for a reply on a
  per-access basis adds a scheduling round trip that a direct atomic
  increment or a short critical section does not pay. Go's own
  documentation is explicit that channels are not a universal replacement
  for mutexes, and the Go Memory Model and the sync package continue to
  specify mutexes and atomics as first-class primitives precisely because
  CSP-style channels are the wrong tool for this case.
- A single producer and a single, always-ready consumer with no need for
  back-pressure or cancellation. A plain function call or a simple queue
  data structure is simpler and carries less overhead than standing up a
  goroutine and a channel for a relationship that never actually needs
  concurrency, only sequencing.
- Systems requiring location transparency across a network boundary as a
  first-class concern. CSP channels in languages like Go are in-process
  constructs. If the real requirement is passing messages between processes
  on different machines with supervision, restart, and location-independent
  addressing, the Actor Model, covered in dimension 13, is the closer fit,
  because it was designed from the start around named, location-transparent
  mailboxes rather than in-process typed pipes.
- Extremely latency-critical hot paths where allocation and scheduling
  overhead of a channel operation is measurable. An unbuffered channel send
  involves the scheduler. in a hot loop executed billions of times, this
  overhead can dominate, and lock-free algorithms or plain atomics are the
  correct tool there.
- A team unfamiliar with the ownership discipline CSP demands, working
  under deadline pressure. CSP replaces one discipline, hold the right
  lock, with another, know who owns and closes this channel, and a team
  that has not internalized the second discipline will reproduce the same
  class of bugs, a goroutine leak instead of a deadlock, in a new shape,
  covered fully in dimension 11.
- Problems that are not actually concurrent. If the processes never run at
  the same time, or if there is exactly one caller and one callee with a
  strict call-then-return relationship, the concurrency machinery is pure
  overhead over a direct function call.

## 5. Structure

A CSP-style system is built from three kinds of participant.

Processes. A goroutine, a green thread, or a lightweight OS thread that
executes sequential, ordinary imperative code. A process owns no memory that
another process can reach directly. it is a black box from the perspective
of every other process. Its only interface to the rest of the system is the
set of channels it was given.

Channels. A typed conduit through which values of one specific type pass
from a sender to a receiver. A channel is a first-class value in the
language, passable as an argument, storable in a data structure, and closed
by whichever process is designated its owner. A channel may be unbuffered,
in which case a send blocks until a matching receive is ready, called
synchronous rendezvous, or buffered with a fixed capacity, in which case a
send blocks only once the buffer is full.

A selector or multiplexer. A construct, `select` in Go, `alt` in occam,
that lets a process wait on several channel operations at once and proceed
with whichever one becomes ready first, including a default case for
non-blocking behavior and a timeout case built from a timer channel. The
selector is what lets a single process coordinate several independent
channels without dedicating a thread to each one.

The relationships among these participants follow three rules. a process
holds zero or more channel endpoints. a channel connects exactly the
processes currently holding a reference to it, which may be exactly two for
a simple pipe or many for a fan-out or fan-in point. and ownership of a
channel, meaning the responsibility to close it once no more values will be
sent, belongs to exactly one process, conventionally the sole sender, never
a receiver.

## 6. ASCII structure diagram

```
                    +-------------------+
                    |  generator (proc) |
                    +---------+---------+
                              |
                       chan<int>  (unbuffered)
                              |
                              v
                    +-------------------+
                    |  square (proc)    |
                    +---------+---------+
                              |
                       chan<int>  (unbuffered)
                              |
                              v
                    +-------------------+
                    |  main (proc)      |
                    |  accumulates sum  |
                    +-------------------+

Fan-out / fan-in shape (worker pool):

  +--------+     jobs chan     +---------+
  | source |------------------>| worker1 |---+
  +--------+        |          +---------+   |
                     |--------->| worker2 |---+---> results chan --> sink
                     |          +---------+   |
                     |--------->| worker3 |---+
                     |          +---------+
                     v
              (each worker receives
               from the SAME jobs channel;
               Go's runtime round-robins
               waiting receivers)
```

## 7. Dynamics

The runtime behavior of a CSP system is best understood as a sequence of
synchronization events, each one a rendezvous between a sender and a
receiver, interleaved with each process's own sequential execution between
those events. In the pipeline shown above, the generator process runs its
loop body, then blocks on a send. Nothing proceeds until the square process
reaches its own blocking point, a receive inside its range loop. At the
instant both processes are ready, the runtime performs the handoff. the
value crosses from the generator's stack to the square process's local
variable, and both processes resume independently. This repeats until the
generator has sent every value and closes its output channel, which is
itself a synchronization event. any process currently blocked in a receive
on that channel is released immediately, and the receive's second return
value reports that the channel is now closed and drained, which is exactly
the signal that terminates the range loop in the consuming process.

In the fan-out shape, the dynamics are the same rendezvous mechanism applied
to a channel with more than two potential parties. When a value is sent on
the shared jobs channel, exactly one of the waiting workers is chosen by the
runtime's scheduler to receive it. this is not broadcast. each value is
consumed by exactly one worker, which is precisely the property that makes
the shared channel a correct load-balancing primitive without any additional
locking. When a select statement is involved, the dynamics add one more
rule. a process blocked in a select with several ready channel operations
has the runtime pick one of the ready cases pseudo-randomly, Go's specified
behavior, to prevent one channel from starving another by always being
checked first, execute that case's body, and then re-enter the select on
the next iteration if it is inside a loop.

```
time -->

generator:  [compute i=1]--send-->|blocked|          [compute i=2]--send-->
square:                 |blocked|--recv-->[compute i*i]--send-->|blocked|
main:                                          |blocked|--recv-->[sum+=v]

Each arrow crossing at a shared column is one rendezvous. both processes
are present at that instant, the value crosses, both resume independently.
```

## 8. Implementation variants

Unbuffered, synchronous channels. The default, strictest form, and the
closest runtime realization of Hoare's original process algebra. a send and
its matching receive are a single atomic event. This gives the strongest
guarantee. the sender knows, at the moment its send call returns, that the
receiver has taken the value, which is a useful synchronization primitive in
its own right, independent of the value transferred.

Buffered channels. A channel with a fixed-capacity internal queue. a send
only blocks once the buffer is full, and a receive only blocks once the
buffer is empty. This decouples producer and consumer speed up to the buffer
size, at the cost of losing the synchronous handoff guarantee, since the
sender no longer knows the receiver has actually processed the value, only
that it has been queued. Choosing a buffer size equal to the expected
fan-out count, for example buffering a done-signal channel to the number of
goroutines that will send on it, is a well-known idiom for avoiding a
goroutine leak when the receiving side may stop listening early, and this is
documented in the Go standard library's own worked example for the pattern.

Directional channel types. A language-level restriction, present in Go as a
send-only channel type and a receive-only channel type, that narrows a
bidirectional channel to one direction when it is passed into a function.
This is a static-typing variant, not a runtime one. it costs nothing at
execution time and buys a compiler-checked guarantee that a function
receiving a receive-only parameter cannot accidentally send on it, which
narrows the set of things a reviewer needs to check about that function's
concurrency safety.

Select-based multiplexing with a default case. Adding a default case to a
select statement turns a blocking wait into a non-blocking poll, letting a
process check a channel opportunistically without committing to wait for
it. This variant trades the blocking guarantee for responsiveness, and is
the mechanism used to implement cooperative cancellation checks inside a
tight loop.

Language-level variants beyond Go. occam, the language INMOS designed
directly for the transputer processor, implements CSP's PAR and ALT
constructs as first-class language keywords rather than library functions,
and its channels are unbuffered by default, hewing closer to the original
algebra than Go's optionally-buffered channels. this is confirmed by the
Wikipedia entry on Communicating sequential processes, verified 2026-08-14,
which states CSP was highly influential in occam's design. Clojure's
core.async library implements the same channel-and-go-block idiom as a
library on top of a language that otherwise has no built-in concurrency
primitives of this shape, using callback-based parking instead of native OS
or green threads to avoid blocking the JVM thread pool, a variant chosen
specifically to fit CSP-style code onto a host runtime that was not built
for it. The influence relationship between CSP and core.async is recorded
on the Wikipedia CSP entry cited above. this entry does not claim
core.async's own documentation makes the same claim, since a direct check
of clojure.github.io/core.async and github.com/clojure/core.async on
2026-08-14 found no such statement in either.

## 9. Known production uses

The Go programming language builds its concurrency model directly on CSP.
Go's own Effective Go documentation states, in the Concurrency section,
"Although Go's approach to concurrency originates in Hoare's Communicating
Sequential Processes (CSP), it can also be seen as a type-safe
generalization of Unix pipes" (https://go.dev/doc/effective_go#concurrency,
verified 2026-08-14, exact sentence confirmed live). Go is used in
production by, among many others, the servers behind Google's own
infrastructure, Docker's container runtime, and Kubernetes' control plane,
all of which rely on goroutines and channels as their primary concurrency
idiom rather than shared-memory locking as the default.

The INMOS T9000 transputer, a microprocessor line designed in the 1980s
specifically to run networks of CSP processes in hardware, used CSP as its
formal specification and verification language during design, and occam,
the language INMOS built for the transputer, compiled directly to the
processor's native CSP-style process-and-channel instructions (Wikipedia
entry on Communicating sequential processes, verified 2026-08-14).

CSP has been used for formal verification of safety-critical avionics.
researchers at the Bremen Institute for Safe Systems, working with
Daimler-Benz Aerospace, modeled a fault-management system for the
International Space Station's avionics, roughly 23,000 lines of code, in
CSP to verify its correctness before deployment (Wikipedia entry on
Communicating sequential processes, verified 2026-08-14). Praxis High
Integrity Systems, now Altran Praxis, applied CSP during the development of
a secure smart-card certification authority system of roughly 100,000 lines
of code, using the formal model to support the system's security
certification, per the same source, verified 2026-08-14.

CSP's model checker, FDR, was used by Gavin Lowe to discover a previously
unknown man-in-the-middle attack against the Needham-Schroeder public-key
authentication protocol by model-checking a CSP specification of the
protocol against an intruder model, a result that is one of the most cited
early successes of applying CSP-based formal methods to security protocol
analysis (Wikipedia entry on Communicating sequential processes, verified
2026-08-14).

## 10. Consequences

Positive. Eliminates data races on the values passed over channels by
construction, because a value has exactly one owner at any instant, either
in the sender's stack before the send or in the receiver's stack after the
receive, never in both places at once and never accessible from a second
party mid-transfer. Makes a function's concurrency contract visible in its
signature, since a function whose only external interface is its channel
parameters can be understood in isolation without auditing the rest of the
codebase for other holders of the same mutex. Composes cleanly. pipelines,
fan-out and fan-in, and cancellation propagation are all built from the
same two primitives, channels and select, rather than requiring a different
specialized tool for each shape. Scales naturally with team size because
the interface between two teams' code is a narrow, typed channel rather
than a shared struct with an implicit locking convention that lives only in
a wiki page.

Negative. Does not eliminate deadlock, livelock, or goroutine leaks. CSP
removes one class of concurrency bug, the data race, and leaves a different
class, ownership and lifecycle bugs, fully in the programmer's hands,
detailed in dimension 11. Adds real runtime cost per send and receive,
which is small in a runtime purpose-built for it but is not zero, and can
dominate in a sufficiently hot loop. Requires learning a distinct
discipline, channel ownership, that has no compiler enforcement in most
implementations, since a channel can be closed by the wrong party, or never
closed at all, and the type system will not catch either mistake. Global
data flow becomes harder to trace than in a shared-memory design with a
small number of well-documented locks, because understanding what a large
CSP system does end to end requires following the graph of channels across
many files, whereas a shared-memory design at least concentrates the state
in one place even if access to it is undisciplined.

## 11. Failure modes and misuse

Goroutine leak from an unreceived send. A goroutine blocked forever on an
unbuffered channel send because the intended receiver has already returned,
for example after a request timeout, will never be garbage collected. it
sits in memory holding its stack forever. Symptom, an apparently idle
service whose goroutine count, visible via a runtime goroutine counter or a
pprof goroutine profile, climbs steadily over time without bound, eventually
exhausting memory. Cause, a sender with no way to know that its intended
receiver has stopped listening. Fix, give the sender a second channel or
context to select on alongside the primary send, so it can abandon the send
if the receiver is known to be gone, or size a result-collecting channel's
buffer to the maximum number of senders so no sender ever blocks waiting for
a receiver that chose to stop early. This exact idiom, and this exact leak,
is documented as a named pitfall in the Go blog's own pipelines article.

Deadlock from circular wait across channels. Two goroutines, each blocked
trying to send on a channel the other is supposed to receive from, while
that other goroutine is itself blocked trying to send on a channel the
first is supposed to receive from. Symptom, the program hangs completely
and, in Go specifically, the runtime detects that every goroutine is asleep
and prints a fatal deadlock error before exiting, which is a genuinely
useful diagnostic most shared-memory deadlocks do not offer for free.
Cause, an unbuffered channel protocol where two parties both need to send
before either can receive, an ordering the code did not enforce. Fix,
establish and document a strict ordering for which party sends first in any
two-way protocol, or introduce a buffer large enough to absorb the first
message without requiring the receiver to be ready.

Send or close on a closed channel causing a panic. Sending to an
already-closed channel, or closing a channel a second time, is a runtime
panic in Go, not a silent no-op. Symptom, a crash reporting a send on a
closed channel or a close of an already-closed channel, often surfacing
intermittently because it depends on the exact interleaving of a race
between the closer and another sender. Cause, more than one goroutine
believing it owns the right to close a channel, which is the
ownership-discipline failure this pattern most directly warns against.
Fix, the rule with no exception. only the sole sender closes a channel, and
if multiple goroutines could plausibly be the last sender, use a wait group
to have exactly one designated goroutine close the channel only after every
other sender has finished.

Treating no data race as no bug. A team that adopts channels and then sees
the race detector go quiet can wrongly conclude the concurrency logic is
correct. Symptom, a subtle logic bug, a value processed twice, an event
handled out of order relative to another related event, that has nothing to
do with a data race and everything to do with the protocol between two
processes being under-specified. Cause, conflating the guarantee CSP
actually gives, no torn reads or writes on the values crossing a channel,
with a guarantee it does not give, correct sequencing of the broader
business logic those values represent. Fix, treat the channel protocol
itself as a piece of logic that needs its own tests and its own
documentation of invariants, not as a substitute for that documentation.

Unbounded buffered channel as a hidden memory leak. Giving a channel a very
large or effectively unbounded buffer to solve a blocking problem without
addressing the underlying speed mismatch between producer and consumer.
Symptom, memory usage grows linearly with how far behind the consumer
falls, with no back-pressure signal ever reaching the producer to slow it
down. Cause, buffering used as a band-aid over a design that needed actual
flow control. Fix, use a small, deliberately-sized buffer, or no buffer at
all, so that a slow consumer naturally applies back-pressure to its
producer by making the producer's sends block, which is a feature of CSP,
not a defect, when the goal is a stable system under load.

## 12. Trade-off matrix

| Force | CSP (channels) | Mutex plus shared state | Actor Model | Software Transactional Memory |
|---|---|---|---|---|
| Data race safety | Guaranteed by construction on channel values | Manual, only as correct as lock discipline | Guaranteed, mailbox is the only shared surface | Guaranteed, conflicts detected and retried |
| Latency for fine-grained shared counters | Poor, a round trip per access | Excellent, direct atomic or short critical section | Poor, same round-trip cost as CSP | Moderate, retry overhead under contention |
| Interface visible in function signature | Yes, channel type is a parameter | No, the lock is external convention | Partially, mailbox message types are visible, sender identity is not | No, transaction boundaries are implicit in code structure |
| Cross-process or cross-machine transparency | No, in-process construct in most languages | No | Yes, native to Erlang and Akka's design | No |
| Deadlock possible | Yes, circular channel wait | Yes, circular lock acquisition | Rare in practice, no blocking send by default in most implementations | No by construction, transactions abort and retry instead of blocking |
| Runtime overhead per operation | Moderate, scheduler-mediated handoff | Low, a few instructions for an uncontended lock | Moderate to high, message allocation and mailbox delivery | Moderate to high, versioning and conflict detection |
| Team-boundary interface clarity | High, channel is the contract | Low, requires documented locking convention | High, message schema is the contract | Low, requires understanding transaction scope |

## 13. Related and incompatible patterns

Producer-Consumer. CSP's unbuffered and buffered channels are the canonical
mechanism for implementing the Producer-Consumer pattern in a CSP-style
language. the two are not competitors, CSP is one concrete implementation
strategy for the more general pattern, alongside a lock-protected queue as
an alternative implementation strategy for the same pattern.

Pipeline. A chain of processes each connected to the next by a channel,
exactly as shown in dimension 6, is the direct realization of the Pipeline
pattern in CSP. every pipeline stage is a CSP process and every stage
boundary is a channel.

Fan-out and Fan-in. The worker-pool shape in dimension 6 is CSP's native
expression of these two composable patterns. a single channel shared by
multiple readers for fan-out, and a single channel shared by multiple
writers, or a dedicated merging goroutine reading from several channels via
select, for fan-in.

Select Loop. The select statement is itself frequently named as its own
pattern, the event loop or reactor pattern realized with channels instead
of callbacks, and is the mechanism that lets a single CSP process multiplex
several concurrent concerns, timeouts, cancellation, and multiple data
sources, without spawning a dedicated process for each one.

Actor Model, the closest sibling and the one most often confused with CSP.
Both models reject shared mutable memory in favor of message passing. The
structural difference is where identity lives. in the Actor Model, from
Carl Hewitt and realized prominently in Erlang and Akka, a message is
addressed to a named actor's mailbox, and the sender must know the
receiver's identity or address. the mailbox itself is typically unbounded
and asynchronous by default. In CSP, a message is sent on a channel, an
anonymous, shared conduit that neither party needs to know the other's
identity to use, and the default channel, unbuffered, is synchronous. an
actor's mailbox does not block its sender the way an unbuffered CSP channel
does. This is why the two are related but not interchangeable. CSP
naturally expresses in-process pipelines and fan-out with shared channels.
the Actor Model naturally expresses distributed, supervised, individually
addressable units of state with location transparency. A system can use
both at once, actors within a process communicating with each other over
CSP channels, or vice versa, and this is a real, documented design choice
rather than a contradiction.

Pi-calculus. The theoretical concurrency calculus, developed by Robin
Milner, Joachim Parrow, and David Walker, that generalizes CSP by allowing
channel names themselves to be passed as messages over other channels,
letting the communication topology change at runtime. CSP's channel set is
fixed once processes are wired together. pi-calculus permits dynamic
reconfiguration of who can talk to whom. This entry treats pi-calculus as
related theory rather than a competing engineering idiom, because it is
rarely surfaced directly as an application-level programming pattern the
way CSP channels are in Go or occam.

Incompatible with ad hoc shared mutable state protected by locks, used as
the primary coordination mechanism within the same subsystem a CSP pipeline
already owns. Mixing the two within one tightly coupled subsystem, some
fields protected by a mutex and others exchanged over a channel, without a
clear boundary between which fields belong to which discipline,
reintroduces the exact hazard CSP exists to remove, because a channel
offers no protection to a field that a second goroutine reaches directly
through a stored pointer, bypassing the channel entirely. This is not a
claim that mutexes and channels can never coexist in one program. Go's own
standard library uses both. it is a claim that within a single, well-defined
boundary, choose one discipline for that boundary's state and apply it
consistently.

## 14. Refactoring path in and out

Introducing CSP into code that currently shares state through a mutex.
Start by identifying the smallest unit of work a background goroutine can
perform that has a clear input and a clear output, and give that unit
exactly two channels, one it only receives from and one it only sends to,
using the directional channel types from dimension 8 to make the
restriction compiler-checked immediately. Move the shared mutable state that
unit depended on so that it becomes local to the new goroutine, reachable
only through those two channels, deleting the mutex that used to protect it
once nothing outside the goroutine can reach the state directly. Verify with
the race detector that no other code path still holds a reference into the
state that was just made local, because a lingering reference held
elsewhere is the single most common way this refactor fails silently.
Repeat one unit at a time rather than converting an entire subsystem in one
change, so that each step is independently reviewable and revertible.

Removing CSP where it has stopped earning its place. The signal that a
channel-based design should be simplified back toward a direct function
call or a mutex is a channel that is used exactly once per invocation with
exactly one sender and one always-ready receiver, and where no concurrency,
no cancellation, and no fan-out ever actually occurs at that boundary in
practice. Inline the goroutine's logic directly into the caller as a plain
function call, deleting the channel and the spawn statement together, and
confirm via a benchmark that latency improved, since the removal of a
scheduler round trip is the whole point of this direction. Where a channel
was being used purely to protect a piece of shared state from concurrent
access, rather than to coordinate a genuine handoff between independently
running processes, replace it with a mutex directly around that state
instead, which is very often faster and no less safe, per the applicability
guidance in dimension 4.

## 15. Testing and verification

CSP-style code is, in one specific respect, easier to test than
lock-protected shared state. a channel's type and direction constrain what
a unit test needs to set up, a channel and a value to send on it, without
needing to construct a broader shared struct and its full locking
discipline. A test can send known input values on the channel a process
receives from, then assert on the values that process sends to its output
channel, treating the process as a pure function from an input stream to an
output stream even though it is internally implemented with imperative,
stateful code.

What becomes harder is testing the timing and cancellation edges. did the
process correctly exit when its context was cancelled mid-computation, did
it close the channels it owns exactly once, did it avoid leaking a goroutine
when its consumer stopped early. These require tests that deliberately
introduce a cancellation or a stopped-consumer scenario and then assert,
using a runtime goroutine counter before and after in Go, or an equivalent
leak detector, that no goroutine outlived the test. The goleak library,
Uber's open-source goroutine-leak detector for Go tests, is the standard
tool for this in Go's ecosystem and should run as a teardown check in any
test suite exercising CSP-style code with cancellation paths.

Deadlock detection deserves a specific note. Go's runtime detects and
reports a true global deadlock, every goroutine asleep, automatically at
test time and at run time, which is a meaningful safety net this pattern
gets essentially for free in that language, but it does not detect a
deadlock between only a subset of goroutines while other goroutines remain
runnable elsewhere in the program, so a test suite still needs deliberate
timeout-based tests, a send raced against a timer channel via select, then
an assertion that the timer path was not taken, to catch a partial deadlock
that the runtime-level detector cannot see.

## 16. Observability signals

A healthy CSP system, observed over time, shows goroutine or process counts
that are stable or that track load in a bounded, predictable way, rising
under a traffic spike and falling back down once the spike passes, rather
than climbing monotonically. In Go, a goroutine counter exposed as a metric,
or a periodic pprof goroutine profile, is the primary signal for this. a
monotonically increasing goroutine count under otherwise steady load is
close to a definitive signature of the goroutine-leak failure mode from
dimension 11. Channel buffer occupancy, where the language exposes it, is a
useful gauge for whether a pipeline stage is falling behind its upstream
producer. a buffer consistently near capacity is the early warning sign of
the back-pressure condition described in dimension 11, before it becomes an
unbounded memory problem. Send and receive latency, measured as the time a
goroutine spends blocked in a channel operation, is the concurrency-specific
analogue of lock contention time in a mutex-based system, and a rising
trend in it indicates a downstream consumer that has become the bottleneck.
A failing instance typically shows one of two shapes on a dashboard. a hard
stop, where all throughput drops to zero and stays there, consistent with a
true deadlock and, in Go, likely accompanied by the runtime's own fatal
deadlock log line, or a slow bleed, where goroutine count and memory climb
together while throughput stays nominally healthy, consistent with the
leaked-goroutine failure mode where abandoned senders accumulate quietly.

## 17. Security and privacy implications

CSP's channel discipline does not, by itself, introduce a distinctive new
attack surface, but its absence of enforcement is a place where a security
property can be silently lost. A channel-based design that is documented as
the only way to reach this state is through this channel is only true as
long as no code anywhere in the program also holds and uses a direct
reference to the same underlying state through a closure, a pointer stored
in a struct, or an exported field, and most CSP-influenced languages do not
prevent that second reference from existing. this is a case where the
security or correctness invariant a team relies on is a convention the
compiler cannot check, and a code reviewer or a static analysis rule is the
only enforcement mechanism available, which is worth naming explicitly
rather than assuming the type system covers it. On the positive side, CSP's
formal algebra has itself been used as a security-analysis tool rather than
merely a subject of one. Gavin Lowe's use of the FDR CSP model checker to
find the Needham-Schroeder man-in-the-middle attack, cited in dimension 9,
is a documented instance of CSP's formal semantics directly finding a
protocol-level security flaw that informal review had missed for over a
decade after the protocol's original publication, which is a genuine
strength of the model in its formal-methods sense rather than its
day-to-day engineering-idiom sense. On data privacy specifically, CSP's
in-process channel model has no direct implication one way or the other.
values crossing a channel are exactly as sensitive as the data itself, and
a channel provides no encryption, redaction, or access control beyond which
goroutines happen to hold a reference to it, so a system handling sensitive
data over channels still needs its usual data-handling controls applied at
the point where that data enters or leaves the channel-based subsystem, the
same as it would with any other in-process data structure.

## 18. References

1. C. A. R. Hoare. Communicating sequential processes. Communications of
   the ACM, volume 21, issue 8, August 1978. Cited via the Wikipedia entry
   "Communicating sequential processes,"
   https://en.wikipedia.org/wiki/Communicating_sequential_processes, which
   gives the original publication venue, volume, issue, and year, verified
   2026-08-14.
2. C. A. R. Hoare. Communicating Sequential Processes. Prentice Hall
   International, 1985. The extended book-length treatment of the process
   algebra, referenced by title and publisher for readers who need the full
   formal semantics. page-level citations are not made here because the
   text was not directly re-verified for this entry, only its existence and
   status as the canonical follow-up to the 1978 paper.
3. The Go Programming Language. Effective Go, Concurrency section,
   https://go.dev/doc/effective_go#concurrency, verified 2026-08-14. Source
   of the exact quoted sentence "Although Go's approach to concurrency
   originates in Hoare's Communicating Sequential Processes (CSP), it can
   also be seen as a type-safe generalization of Unix pipes," confirmed
   present on the live page at verification time.
4. The Go Programming Language. The Go Blog, Go Concurrency Patterns.
   Pipelines and cancellation, golang.org/blog. Referenced for the
   documented buffer-sizing idiom used to avoid a goroutine leak on early
   consumer exit, discussed in dimensions 8 and 11. not independently
   re-fetched for this entry, cited from established prior knowledge of the
   Go blog's own worked examples and flagged here as such rather than
   claimed as freshly verified.
5. Wikipedia. Communicating sequential processes,
   https://en.wikipedia.org/wiki/Communicating_sequential_processes,
   verified 2026-08-14. Source for occam's design being highly influenced
   by CSP and its use on the INMOS transputer, the International Space
   Station avionics fault-management modeling effort of roughly 23,000
   lines of code by the Bremen Institute for Safe Systems and Daimler-Benz
   Aerospace, the Praxis High Integrity Systems smart-card certification
   authority verification effort of roughly 100,000 lines of code, Gavin
   Lowe's discovery of a man-in-the-middle attack on the Needham-Schroeder
   public-key protocol using the FDR CSP model checker, and CSP's influence
   on Clojure's core.async, Limbo, Erlang, Crystal, and Go.
6. GitHub. clojure/core.async repository README,
   https://github.com/clojure/core.async, checked 2026-08-14. Does not
   itself state a CSP influence in the text retrieved. the core.async CSP
   lineage claim in this entry rests on reference 5, not on core.async's
   own documentation, and this distinction is stated explicitly in
   dimension 8 to avoid overclaiming a source that does not support it.
7. go.uber.org/goleak. Uber's open-source goroutine-leak detector for Go
   test suites, referenced by name and purpose in dimension 15 as the
   standard tool for asserting no goroutine outlives a test. not
   independently re-fetched for this entry.

## Code examples

### Go

The idiomatic realization. an unbuffered channel pipeline with a generator
stage, a transform stage, and a consuming main goroutine.

```go
package main

import "fmt"

func generator(out chan<- int, n int) {
	for i := 1; i <= n; i++ {
		out <- i
	}
	close(out)
}

func square(in <-chan int, out chan<- int) {
	for v := range in {
		out <- v * v
	}
	close(out)
}

func main() {
	nums := make(chan int)
	squares := make(chan int)
	go generator(nums, 5)
	go square(nums, squares)
	sum := 0
	for v := range squares {
		sum += v
	}
	fmt.Println("sum of squares:", sum)
}
```

Compiled and run with `go run main.go`. Output confirmed. `sum of squares: 55`.

### Rust

Rust's standard `std::sync::mpsc` channel is not CSP's synchronous
rendezvous by default, it is an asynchronous multi-producer single-consumer
queue, but it is the closest channel-based primitive in Rust's standard
library and is the idiomatic way to write CSP-style pipelines in Rust
without a third-party dependency.

```rust
use std::sync::mpsc;
use std::thread;

fn generator(tx: mpsc::Sender<i32>, n: i32) {
    for i in 1..=n {
        tx.send(i).unwrap();
    }
}

fn main() {
    let (tx1, rx1) = mpsc::channel::<i32>();
    let (tx2, rx2) = mpsc::channel::<i32>();

    thread::spawn(move || generator(tx1, 5));

    thread::spawn(move || {
        for v in rx1 {
            tx2.send(v * v).unwrap();
        }
    });

    let sum: i32 = rx2.iter().sum();
    println!("sum of squares: {}", sum);
}
```

Compiled with `rustc -O main.rs -o main` and run. Output confirmed. `sum of
squares: 55`.

### Python

Python's standard library has no native CSP-style channel. `queue.Queue`
approximates a buffered channel but does not give the synchronous
rendezvous guarantee, so this example implements a small unbuffered channel
directly on top of a lock and a condition variable, matching the semantics
described in dimensions 5 and 7 exactly. a send blocks until a receive
takes the value.

```python
import threading


class Channel:
    def __init__(self):
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)
        self._value = None
        self._has_value = False
        self._closed = False

    def send(self, value):
        with self._cond:
            while self._has_value:
                self._cond.wait()
            self._value = value
            self._has_value = True
            self._cond.notify_all()
            while self._has_value:
                self._cond.wait()

    def receive(self):
        with self._cond:
            while not self._has_value and not self._closed:
                self._cond.wait()
            if self._closed and not self._has_value:
                return None, False
            value = self._value
            self._has_value = False
            self._cond.notify_all()
            return value, True

    def close(self):
        with self._cond:
            self._closed = True
            self._cond.notify_all()


def generator(out, n):
    for i in range(1, n + 1):
        out.send(i)
    out.close()


def square(inp, out):
    while True:
        v, ok = inp.receive()
        if not ok:
            break
        out.send(v * v)
    out.close()


def main():
    nums = Channel()
    squares = Channel()
    threading.Thread(target=generator, args=(nums, 5)).start()
    threading.Thread(target=square, args=(nums, squares)).start()
    total = 0
    while True:
        v, ok = squares.receive()
        if not ok:
            break
        total += v
    print("sum of squares:", total)


if __name__ == "__main__":
    main()
```

Run with `python3 main.py`. Output confirmed. `sum of squares: 55`.
