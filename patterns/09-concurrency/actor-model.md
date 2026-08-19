---
name: Actor Model
slug: actor-model
family: 09-concurrency
category: Concurrency
aliases: [Actors, Actor-Based Concurrency]
first_described: "Hewitt, Bishop, Steiger 1973"
maturity: canonical
related: [producer-consumer, active-object, monitor-object, thread-pool, reactor]
incompatible_with: [double-checked-locking, monitor-object]
verified: 2026-08-02
---

# Actor Model

## 1. Name, aliases, and lineage

The canonical name is the Actor Model, sometimes written as actor-based
concurrency or simply actors. The idea was first proposed by Carl Hewitt, Peter
Bishop, and Richard Steiger in 1973, and the operational semantics were later
formalized by Irene Greif as part of her doctoral research
([Wikipedia, Actor model, "History" section](https://en.wikipedia.org/wiki/Actor_model),
verified 2026-08-02). Hewitt's original work grew out of artificial
intelligence research at MIT and framed an actor as a universal primitive of
computation, not a narrow concurrency mechanism.

The model sat mostly in academic and AI languages for a decade. It reached wide
industrial use through Erlang, designed at Ericsson starting in 1986 for
building fault-tolerant telecom switches, where the language's process model is
a direct, if independently rediscovered, implementation of the actor idea. From
Erlang the model spread into Scala and Java through Akka, into the JVM more
broadly through Pekko, the Apache Software Foundation fork of Akka created
after Akka's 2022 license change, into .NET through Microsoft Orleans, and into
the BEAM ecosystem again through Elixir's `GenServer` abstraction, which is a
structured wrapper over the same underlying Erlang process primitive.

The word actor is used loosely in some frameworks to mean any unit of
isolated, message-driven state, and this rule distinguishes three things that
are often conflated. A **classical actor** as Hewitt defined it reacts to a
received message by doing some combination of three things, in Hewitt's own
terms, creating new actors, sending messages to actors it knows about, and
designating the behavior to use for its next message, with no shared mutable
state and no synchronous blocking between actors. A **virtual actor**, the
term Orleans introduced, has a permanent logical identity that the runtime
activates and deactivates transparently, so the caller never manages the
actor's lifecycle directly. And a **process** in the Erlang or Elixir sense,
which predates and is not derived from Hewitt's papers but converges on the
same guarantees, isolated state, asynchronous message-only communication, and
no direct memory sharing.

## 2. Problem and context

A concurrent program needs many pieces of independent state to change over
time, driven by events arriving from different sources, without a lock,
mutex, or shared memory region becoming the single point of contention and the
single source of a whole class of bugs. The traditional answer is shared-memory
threads with explicit synchronization, locks around every mutable field, or
lock-free structures with an even sharper learning curve. Both scale in
throughput on a single machine but not in correctness. As the number of shared
mutable objects grows, verifying the absence of a deadlock, a race, or a
missed release becomes a program-wide obligation rather than a local one.

The actor model reframes the problem. Rather than asking how multiple threads
can safely touch one piece of state, it asks what happens if no thread ever
touches that state except one, and everyone else only sends it messages. An
actor is an entity that owns its state exclusively, processes exactly one
message at a time from its own private mailbox, and communicates with the
outside world only by sending messages to the mailboxes of other actors. A
computation is not a shared object graph mutated by parallel threads. It is a
network of actors exchanging asynchronous, fire-and-forget messages, each of
whose internal state is private by construction.

This context arises directly wherever many independent, stateful entities need
to run concurrently and communicate, a game server tracking thousands of
players, a chat or presence system tracking millions of connections, a device
gateway holding one logical connection per IoT sensor, a workflow engine
tracking many in-flight orders, or a telecom switch routing millions of calls.
It is a poor fit for a single tightly coupled computation over one shared
dataset, where the cost of message-passing indirection and the loss of direct
in-process aggregate queries outweighs the isolation benefit.

## 3. Forces

**Isolation versus throughput on a single piece of state.** An actor
serializes all access to its own state by processing one message at a time.
This removes intra-actor races for free, but it makes that actor a strict
serialization point. No matter how many CPU cores are idle, a single actor's
state can only be advanced by one logical thread of execution at a time. High
write contention on one logical entity therefore does not parallelize by
adding actors, it requires partitioning that entity's state across more
actors, which is a design decision, not a runtime knob.

**Location transparency versus latency and failure visibility.** Because
actors communicate only by message, the address of an actor can, in principle,
be local or remote without changing the sender's code. This is a genuine power
for distributed systems, letting the same actor code run across a cluster. It
also hides the difference between a same-process, nanosecond-scale send and a
cross-machine, millisecond-scale send with real failure modes, which is
precisely the distributed computing fallacy trap, treating network calls as
if they were free and reliable local calls.

**Asynchrony versus program comprehension.** Actors communicate by sending and
receiving messages asynchronously rather than by calling methods and getting
return values inline. This removes lock-ordering deadlocks but replaces
straight-line reasoning with reasoning about message ordering, mailbox
interleavings, and the eventual, not immediate, effect of a send. A team fluent
in synchronous call-and-return code pays a real ramp-up cost.

**Fault containment versus operational complexity.** An actor that crashes
does not corrupt any other actor's state, because there is no shared memory
to corrupt. Supervision hierarchies, most fully realized in Erlang's OTP and
carried into Akka, let a parent actor restart a failed child cleanly. This
buys resilience but adds a second discipline the team must learn, designing
supervision trees, restart strategies, and what state is safe to lose on
restart versus what must be checkpointed externally.

**Cognitive load and debuggability versus concurrency correctness.**
Traditional thread-and-lock debugging tools, stack traces and breakpoints,
map awkwardly onto a system where what happens next depends on a queue of
messages rather than a call stack. In exchange, the actor model removes entire
categories of bugs, data races on shared mutable fields, and most classic
lock-ordering deadlocks, that dominate concurrency post-mortems in
lock-based systems.

## 4. Applicability and non-applicability

Reach for the actor model when:

- Many independent, stateful entities must run concurrently and their natural
  unit of consistency is per-entity, not global (a player, a device
  connection, a shopping cart, a chat room, a workflow instance).
- The system must survive partial failure gracefully, and isolating a crash to
  one entity without corrupting the rest is a real operational requirement.
- The workload is message-driven and bursty rather than a tight,
  data-parallel numeric loop.
- The team needs to scale the same logical model from one process to a
  cluster without a rewrite, and location transparency is a genuine asset
  rather than a hidden cost.
- Explicit locking has already produced deadlocks, lock-ordering bugs, or
  unmaintainable synchronized blocks in the current design.

Do NOT reach for the actor model when:

- The computation is a single, tightly coupled operation over one large
  shared dataset with heavy cross-cutting reads, for example a numeric
  simulation working on one large in-memory matrix. Splitting that dataset
  into actors adds message-passing overhead and loses the ability to read
  consistent aggregate state without coordination, where a data-parallel
  model, fork-join or a GPU kernel, fits the forces far better.
- The problem needs strict, multi-entity transactional consistency, a
  classic ACID transaction spanning several rows, more than it needs
  isolation and fault containment. Cross-actor transactions require an
  explicit, hand-built saga or two-phase protocol on top of the model, the
  model does not give you one.
- The workload is CPU-bound and embarrassingly parallel with no real shared
  mutable state to isolate in the first place, a plain thread pool or
  fork-join over independent work items has less overhead and is simpler
  to reason about.
- Latency budgets are in the low microseconds and every message send's
  scheduling and mailbox overhead is unacceptable, a lock-free data
  structure or a single-writer, single-reader ring buffer will outperform a
  general actor runtime.
- The team has no operational experience with the chosen actor runtime and
  the project timeline has no room to build supervision, backpressure, and
  failure-handling discipline before shipping, a naive actor system without
  supervision degrades into unbounded mailboxes and silent message loss.

## 5. Structure

- **Actor.** The unit of computation. Owns exactly one private mailbox and
  exactly one piece of mutable state that no other actor can touch directly.
  Reacts to a received message by doing some combination of three things,
  sending messages to actors whose address it knows, creating new actors, and
  designating the behavior that will handle its next message.
- **Mailbox.** The actor's private, ordered, per-sender in most runtimes,
  inbound message queue. Decouples the sender's send call, which returns
  immediately, from the receiver's processing, which happens whenever the
  actor's single logical thread of execution next dequeues.
- **Message.** An immutable value passed by copy or by reference to an
  immutable object, never a mutable reference the sender continues to touch.
  Immutability of messages is what keeps the no-shared-mutable-state
  guarantee intact once a message crosses actor boundaries.
- **Address, or reference.** The only thing another actor holds to reach an
  actor, an opaque handle used for sending, never a way to reach into the
  actor's internal fields.
- **Scheduler, or dispatcher.** The runtime component that decides which
  actor's mailbox to service next on which underlying OS thread. This is
  where the model's promise of millions of actors on few OS threads is kept,
  actors are userspace, cooperatively scheduled entities, not one-to-one with
  OS threads.
- **Supervisor.** An actor whose specific responsibility is to watch child
  actors, decide the restart or escalation policy on child failure, and form
  the fault-containment tree. Present as a first-class concept in Erlang OTP
  and Akka, absent, and left to ad hoc code, in lighter-weight actor
  libraries.

## 6. ASCII structure diagram

```
                     +-----------------------------+
                     |          Actor A             |
                     |  +------------------------+  |
   send(msg) ------->|  |  Mailbox (FIFO queue)  |  |
                     |  +-----------+------------+  |
                     |              |                |
                     |              v                |
                     |  +------------------------+  |
                     |  |  Private state (owned  |  |
                     |  |  exclusively by A)     |  |
                     |  +------------------------+  |
                     |              |                |
                     |   one message at a time       |
                     +--------------|-----------------+
                                    |
                    creates / sends / becomes(next behavior)
                                    |
              +---------------------+---------------------+
              v                     v                     v
        +-----------+        +-----------+          +-----------+
        | Actor B   |        | Actor C   |          | Actor D   |
        | (address  |        | (address  |          | (address  |
        |  known by |        |  known by |          |  known by |
        |    A)     |        |    A)     |          |    A)     |
        +-----------+        +-----------+          +-----------+

        No shared memory between A, B, C, D.
        Every arrow above is an async message send, never a direct call.
```

## 7. Dynamics

```
Sender                     Actor's Mailbox              Actor's Behavior
  |                              |                              |
  |--- send(msg1) -------------->|                              |
  |     (returns immediately)    | msg1 queued                  |
  |                              |                              |
  |--- send(msg2) -------------->|                              |
  |                              | msg2 queued                  |
  |                              |                              |
  |                              |--- dequeue msg1 ------------>|
  |                              |                       process msg1
  |                              |                       may mutate own state
  |                              |                       may send to other actors
  |                              |                       may spawn new actors
  |                              |                       may designate next behavior
  |                              |<---- ready for msg2 ---------|
  |                              |--- dequeue msg2 ------------>|
  |                              |                       process msg2
  |                              |                        (using the behavior
  |                              |                         msg1 may have set)
  v                              v                              v

On failure inside "process msgN", the actor's own runtime state is discarded,
the failure is reported to the actor's supervisor, not to the sender, and the
supervisor decides restart, escalate, or stop, independent of any other actor.
```

## 8. Implementation variants

- **Classical actor libraries (Akka, Pekko, Elixir GenServer).** The actor is
  a long-lived object with an explicit `receive`/`handle` function and a
  mutable field set that only that function touches. Restart on crash resets
  the mutable fields to a fresh instance unless the actor explicitly persists
  state, which is the classic OTP `gen_server` shape formalized in Erlang/OTP
  ([Erlang, "The Erlang Runtime System," process model description](https://www.erlang.org/doc/system/ref_man_processes.html),
  verified 2026-08-02).
- **Virtual actors (Microsoft Orleans grains).** The actor's identity is
  permanent and logical, the runtime transparently activates it in memory on
  first message and may deactivate it after idle time, so callers never
  explicitly create or destroy an actor instance
  ([Microsoft Learn, "Orleans overview," "The actor model" section](https://learn.microsoft.com/en-us/dotnet/orleans/overview),
  verified 2026-08-02). This trades explicit lifecycle control for the
  ability to always address an actor by a stable key, whether or not it is
  currently resident.
- **Typed actors (Akka Typed, Orleans grain interfaces).** The set of
  messages an actor accepts is expressed as a closed type, an interface, a
  sealed class hierarchy, or an algebraic data type, so the compiler rejects
  a message the actor cannot handle, closing the gap left by untyped actor
  systems where sending an unhandled message is only a runtime error.
- **Language-native process model (Erlang, Elixir).** Rather than a library
  bolted onto a general-purpose language, the actor is the language's own
  unit of concurrency. `spawn` returns a process identifier, and `!` (send)
  and `receive` are core language constructs, not framework calls. This is
  the tightest, lowest-overhead implementation because the runtime, the BEAM
  virtual machine, is co-designed with the model.
- **Software Transactional Memory hybrids and CSP-style channels.** Not a pure
  actor implementation, but adjacent. Go's goroutines with channels and
  Clojure's `core.async` give message-passing concurrency without the strict
  one-mailbox-per-actor, owns-its-own-state discipline. A goroutine can
  still share memory if the programmer chooses to, so the isolation guarantee
  is a convention rather than an enforced invariant. This is worth naming
  because engineers often reach for actor model language when describing a
  CSP-style system, and the two are related but distinct. Actors name and
  address a persistent entity, CSP channels are typically unnamed pipes
  between anonymous goroutines.

## 9. Known production uses

- **Ericsson's telecom switches, built in Erlang.** Erlang's process model,
  independently converging on the actor model's guarantees, was created at
  Ericsson for building carrier-grade, fault-tolerant switching systems, and
  the AXD301 ATM switch is documented as an extremely scaleable production
  system built substantially in Erlang, with several hundred engineers and
  about 850,000 lines of Erlang code
  ([Erlang FAQ, "Introduction," system description](https://www.erlang.org/faq/introduction.html),
  verified 2026-08-02).
- **Discord's real-time gateway, built in Elixir on the BEAM.** Discord's own
  engineering blog describes each user's realtime connection as spinning up a
  `GenServer` session process that communicates with per-guild processes
  across Erlang nodes, and states the system reached roughly five million
  concurrent users and millions of events per second on this architecture
  ([Discord Engineering Blog, "How Discord Scaled Elixir to 5,000,000 Concurrent Users"](https://discord.com/blog/how-discord-scaled-elixir-to-5-000-000-concurrent-users),
  verified 2026-08-02).
- **Microsoft's internal cloud services, built on Orleans.** Microsoft states
  Orleans, its virtual-actor framework, is used inside Azure, Xbox, Skype,
  Halo, PlayFab, and Gears of War, alongside its public availability as an
  open-source .NET framework
  ([Microsoft Learn, "Orleans overview," "What can be done with Orleans?" section](https://learn.microsoft.com/en-us/dotnet/orleans/overview),
  verified 2026-08-02).
- **The JVM ecosystem's Akka and Pekko toolkits.** Akka documents the actor
  model directly as its concurrency abstraction, stating that it alleviates
  the developer from having to deal with explicit locking and thread
  management, and that an actor instance processes one message at a time with
  no synchronization primitives needed inside it
  ([Akka documentation, "Actors" (Typed)](https://doc.akka.io/libraries/akka-core/current/typed/actors.html),
  verified 2026-08-02). Pekko is the Apache Software Foundation's fork of
  Akka's pre-license-change codebase and preserves the same actor
  abstraction for organizations that cannot adopt Akka's post-2022 license.

## 10. Consequences

Positive.

- Eliminates data races on an actor's own state by construction, since only
  that actor's single logical thread ever touches it.
- Removes most classic lock-ordering deadlocks, because there is no
  application-level lock to order in the first place.
- Fault isolation is structural. A crashed actor cannot corrupt another
  actor's memory, only its own, which supervision trees can then restart.
- Scales the programming model from a single process to a cluster with the
  same code, because messages, not memory references, are the only channel
  actors use to interact.
- Encourages decomposing a system into small, independently testable units
  that each own a clear, narrow slice of state.

Negative.

- Trades synchronous, easy-to-trace call-and-return code for asynchronous
  message flows that are genuinely harder to step through and to reason
  about under concurrent load.
- Per-actor throughput is capped by the actor's single-message-at-a-time
  discipline, hotspot actors must be explicitly sharded by the designer, the
  runtime will not do it automatically.
- Cross-actor consistency, a transaction spanning two or more actors, is not
  provided by the model and must be hand-built as a saga or a two-phase
  protocol, adding real design and testing burden.
- Mailbox growth under sustained overload is a real failure mode. An actor
  slower than its inbound message rate accumulates an unbounded backlog
  unless the runtime or the developer adds explicit backpressure.
- Message-passing and scheduling overhead, while small per message, is not
  zero, and a design with millions of tiny, chatty actors can spend more
  time in the scheduler and serialization path than in actual work.

## 11. Failure modes and misuse

- **Symptom, memory grows unbounded on one node under load, eventually
  crashing the process.** Cause, an actor's mailbox has no bound and callers
  keep sending faster than the actor drains, so messages queue forever with
  no backpressure signal to slow producers. Fix, bound the mailbox and define
  an explicit overflow policy, drop, reject with a signal to the sender, or
  block the sender, and size the actor pool or shard the hot actor so
  sustained throughput matches sustained demand.
- **Symptom, a single entity, one user, one hot account, one popular game
  room, becomes a visible latency bottleneck while the rest of the system is
  idle.** Cause, all traffic for that entity is pinned to a single actor,
  which serializes it to one logical thread of execution, adding more actors
  elsewhere does nothing for this hotspot. Fix, partition the hot entity's
  work into sub-actors keyed by a finer axis, for example per-shard or
  per-region actors that a parent aggregates, or move the specific
  hot-path operation out of the strict per-entity serialization if it does
  not actually need it.
- **Symptom, state silently vanishes after a routine restart or deploy, and
  nobody can explain why.** Cause, the actor's in-memory state was treated as
  durable when the runtime's contract is that a crashed or restarted actor
  starts from a clean state unless explicitly persisted, the developer
  assumed actor memory behaves like a database. Fix, identify which actor
  state must survive a restart, and persist it explicitly through the
  runtime's event-sourcing or snapshot facility, Akka Persistence, Orleans
  grain persistence, an OTP `gen_server` that checkpoints to storage, rather
  than relying on in-memory continuity.
- **Symptom, two actors appear to deadlock, each waiting on a reply from the
  other, even though actors do not deadlock was the stated reason to adopt
  the model.** Cause, the code used a blocking request-response pattern, a
  synchronous `ask` with a timeout, or a manual future-await, between two
  actors that also happen to send to each other, recreating a classic
  circular-wait outside the actor runtime's own guarantees, which only
  protect intra-actor state, not the caller's own blocking choices. Fix,
  prefer fire-and-forget `tell` with an explicit reply message the receiving
  actor sends back asynchronously, where a genuine request-response is
  needed, keep it strictly one-directional per call and add a timeout with a
  defined failure path, never an unbounded wait.
- **Symptom, message order between two actors appears to interleave in a way
  the developer did not expect, producing inconsistent downstream state.**
  Cause, most actor runtimes guarantee ordering only along a single
  sender-to-receiver mailbox path, not a global order across multiple
  senders, and the code implicitly assumed a total order across all senders
  to one actor. Fix, design the message protocol so ordering-sensitive
  operations either come from a single logical sender, or carry an explicit
  sequence number the receiving actor can use to reorder or reject
  out-of-order messages.
- **Symptom, a supervisor restarts a failing child in an infinite crash
  loop, consuming CPU and flooding logs.** Cause, the restart strategy has no
  backoff or maximum-restarts-in-a-window policy, so a persistently failing
  cause, a bad message, a corrupted external dependency, triggers immediate,
  unthrottled restarts forever. Fix, configure a restart intensity limit,
  maximum restarts within a time window, so the supervisor escalates to its
  own parent, or stops the child, once the limit is exceeded, rather than
  restarting forever.

## 12. Trade-off matrix

| Force | Actor Model | Shared-memory threads with locks | CSP-style channels (Go, core.async) | Software Transactional Memory |
|---|---|---|---|---|
| Isolation of mutable state | Enforced by convention within one actor, strong | None, every shared field is a hazard until proven safe | Not enforced, goroutines can still share memory | Enforced at the transaction boundary, not per-entity |
| Deadlock risk | Low for pure fire-and-forget, possible if blocking `ask` reintroduced | High, grows with number of locks and their ordering | Low for pipeline patterns, possible with cyclic channel waits | Low, livelock under high contention is the analogous risk |
| Fault containment | Strong, structural via supervision | Weak, a corrupted shared structure can affect every thread | Weak, no built-in supervision concept | Weak, a failed transaction retries, but no crash-isolation model |
| Cross-entity consistency | Must be hand-built, saga or 2PC | Native, via a single lock or transaction spanning the data | Must be hand-built via coordinating goroutines | Native within one transaction, across the memory it touches |
| Per-entity throughput ceiling | One message at a time per actor, must shard to scale | Depends on lock granularity, can be finer-grained | Depends on channel design, generally similar to actors | Depends on contention, retries cost throughput under contention |
| Distribution to multiple machines | Natural extension via location-transparent addresses | Not native, needs an entirely different mechanism (RPC, queues) | Not native in the base model, needs an external transport | Not native, STM is typically single-process |
| Learning curve for a synchronous-code team | Moderate to high, new mental model for message flow | Familiar syntax, hazards are subtle and easy to introduce | Moderate, closer to synchronous code via blocking channel ops | Moderate, but retries and side-effect discipline are unfamiliar |

## 13. Related and incompatible patterns

- **Producer-Consumer.** The mailbox itself is a producer-consumer queue
  between senders and the actor, and the actor model can be seen as a
  disciplined generalization, every entity in the system is simultaneously a
  producer to others and a consumer of its own inbound queue.
- **Active Object.** Shares the goal of decoupling method invocation from
  execution by queuing requests and running them on the object's own thread,
  and is close enough to a single actor that some texts treat Active Object
  as the actor model's expression in an object-oriented, method-call
  vocabulary rather than a message vocabulary.
- **Monitor Object.** Actively incompatible in intent. A monitor synchronizes
  concurrent access to one shared object using a mutex and condition
  variables, which is precisely the shared-mutable-state approach the actor
  model replaces. Mixing the two on the same piece of state, an actor whose
  internal fields are also guarded by a monitor for outside access, defeats
  the actor's isolation guarantee and reintroduces the hazards actors exist
  to remove.
- **Double-Checked Locking.** Also incompatible where applied to actor state.
  The entire premise of double-checked locking is safe lazy initialization
  of a value shared across threads under a lock, which has no reason to
  exist once that value is owned exclusively by one actor and reached only
  through messages.
- **Thread Pool.** Composes underneath the actor model rather than competing
  with it. Most actor runtimes dispatch actors onto a bounded pool of OS
  threads, multiplexing many actors per thread, so the actor model is one
  layer of scheduling policy built on top of a thread pool's raw execution
  resource.
- **Reactor.** Composes at the I/O layer. A reactor-style event loop is a
  common mechanism for delivering inbound network events into an actor
  system's mailboxes, and several actor runtimes are themselves implemented
  as a reactor-driven scheduler underneath the actor abstraction.

## 14. Refactoring path in and out

Introducing the actor model into a codebase that does not have it.

1. Identify the mutable state currently protected by explicit locks or by
   ad hoc, only-this-one-thread-touches-it conventions, and treat each
   independently-lockable unit of state as a candidate actor.
2. Define the message protocol for that state before writing the actor body,
   what operations exist, what each operation needs as input, and what
   reply, if any, it produces. Prefer immutable message types.
3. Move the state and its mutating operations into a new actor, replacing
   every direct method call from outside code with a message send to the
   actor's address, and every direct return value with either a reply
   message or an explicitly modeled fire-and-forget operation that has no
   caller-visible result.
4. Replace the locks that used to protect this state with nothing. The
   actor's single-message-at-a-time processing is the new synchronization
   mechanism, and any remaining lock around the actor's own fields is a sign
   step 3 is incomplete.
5. Add supervision once more than a trivial number of these actors exist.
   Define what should happen when this actor crashes, restart with fresh
   state, restart from a persisted snapshot, or propagate the failure to a
   parent, rather than leaving the failure mode implicit.
6. Introduce bounded mailboxes and an overflow policy before load testing,
   not after a production incident surfaces the unbounded case.

Removing the actor model from a codebase where it no longer earns its place.

1. Confirm the actual failure mode driving removal. Usually either the
   asynchronous, message-passing style adds more debugging cost than the
   isolation buys, or the workload turned out to be a tightly coupled,
   shared-dataset computation that never needed per-entity isolation.
2. Collapse actors that communicate purely synchronously, send message,
   immediately block waiting for reply, never do anything else meanwhile,
   back into plain method calls on a shared object protected by a
   conventional lock or a single-threaded event loop, since the actor
   indirection was providing no asynchrony benefit in that specific path.
3. Where genuine concurrency across entities is still needed but the actor
   runtime's overhead or operational complexity is the objection, consider
   moving to a lighter data-parallel or CSP-channel model rather than
   removing concurrency isolation altogether. Outright removal back to raw
   shared-memory threads reintroduces every hazard the actor model was
   adopted to remove.
4. Migrate persisted actor state to whatever storage model the replacement
   design uses, verifying the actor's implicit consistency guarantees,
   single-writer per entity, are replaced with an explicit equivalent, a
   lock, a database row-level lock, or an application-level queue, so
   the replacement is not silently less safe than what it replaces.

## 15. Testing and verification

Testing gets easier for the logic inside a single actor. Because an actor
processes one message at a time against private state, a unit test can send a
sequence of messages to a test instance of the actor and assert on the
sequence of outbound messages and final state, without any thread
synchronization in the test itself. Most actor runtimes ship a dedicated
synchronous test kit for exactly this, Akka's `BehaviorTestKit` and
`ActorTestKit`, Erlang's `common_test` combined with direct process message
assertions, Orleans's in-process test cluster for grain-level tests.

Testing gets harder for cross-actor timing and ordering. A test that spawns
several real actors and asserts on the eventual global outcome is inherently
about eventual consistency, and a naive test will be flaky if it asserts
immediately after sending a message rather than waiting for an observable
signal that processing completed. The correct technique is to make
completion observable, have the actor under test send a final reply or
publish an event the test can await, rather than sleeping an arbitrary
duration and hoping the actor finished.

For supervision and failure handling specifically, inject the failure
deliberately, send a message engineered to make the actor throw, or kill the
actor's underlying process, and assert on the supervisor's observable
response, a restart producing fresh state, an escalation to the parent, or a
stop, rather than merely asserting the system did not crash, which proves
nothing about whether the intended policy actually ran.

For mailbox overflow and backpressure, load-test with a producer sending
faster than the actor's stated processing rate and assert the configured
overflow policy actually triggers, a bounded mailbox rejects, a drop policy
drops, a blocking-send policy blocks the producer, rather than assuming
correct behavior from configuration alone. A mismatched runtime default,
unbounded by default in several actor libraries, is a common source of
untested-in-development, first-seen-in-production incidents.

## 16. Observability signals

This dimension is largely engineering judgement drawn from operating actor
systems, not a single sourced specification.

A healthy actor system shows steady mailbox depth close to zero across the
population of actors, with occasional, short-lived bursts that drain
quickly, per-actor message processing latency, time from dequeue to the
actor becoming ready for its next message, staying flat under load, and a
supervision restart rate near zero, with restarts, when they occur, clearly
attributable to a specific, understood cause.

A failing or degrading actor system shows a small number of actors with
persistently growing mailbox depth, the classic hotspot or slow-consumer
signature, a rising tail latency on message processing that does not
correlate with overall traffic, suggesting one actor or one actor type is
doing unexpectedly expensive work per message, and a nonzero, sustained
restart rate on one or a small set of actor types, which usually indicates
either a poison message the actor cannot handle or an external dependency
that specific actor type depends on has degraded.

The metrics worth exporting from an actor runtime, where it supports it, are
per-actor-type mailbox size, current and a trailing maximum, message
processing duration distribution, restart counts partitioned by actor type
and by restart reason, and dead-letter counts, messages sent to an actor
that no longer exists or never existed, since a rising dead-letter count is
often the earliest external signal of a lifecycle bug that would otherwise
surface only as a silent, dropped operation.

## 17. Security and privacy implications

An actor's isolation of its own state is a correctness property, not a
security boundary, unless the runtime explicitly enforces one. In most actor
libraries, Akka, Erlang, Orleans, all actors within one process or one
cluster trust each other by default, and any actor holding another actor's
address can send it any message its protocol accepts. A malicious or
compromised actor within the same trust domain can therefore still attempt
to flood another actor's mailbox, a denial-of-service against a specific
entity, or send malformed messages designed to trigger an unhandled
exception and force a restart loop. Message protocols that accept
externally-supplied data, a client-facing gateway actor forwarding raw
network input as a message, should validate and sanitize at that boundary,
exactly as any other trust boundary requires, since the actor model itself
does not authenticate or authorize a sender.

Location transparency has a specific privacy and data-residency implication
in a distributed actor system. Because an actor's address does not reveal
whether it is local or on a remote node, a message containing personal data
can silently cross a machine, a data center, or a jurisdictional boundary as
part of ordinary routing, unless the deployment explicitly pins actors
carrying regulated data to a specific region or partition. Systems handling
data subject to residency requirements, GDPR-scoped personal data for
example, need explicit placement policy, not the runtime's default
placement strategy, to guarantee where an actor holding that data actually
runs.

Persisted actor state, via event sourcing or snapshots, as in Akka
Persistence or Orleans grain persistence, is written to durable storage
outside the actor's memory isolation, and inherits the security posture of
that storage directly. Encryption at rest, access control on the underlying
store, and retention policy are the operator's responsibility and are not
provided by the actor abstraction itself.

## 18. References

- Hewitt, C., Bishop, P., Steiger, R. (1973), as summarized in
  "History" section, [Wikipedia, "Actor model"](https://en.wikipedia.org/wiki/Actor_model),
  verified 2026-08-02.
- [Erlang, "The Erlang Runtime System, Processes," official documentation](https://www.erlang.org/doc/system/ref_man_processes.html),
  verified 2026-08-02.
- [Erlang FAQ, "1.4 What kind of applications is Erlang particularly suitable for", and system history](https://www.erlang.org/faq/introduction.html),
  verified 2026-08-02.
- [Akka documentation, "Actors" (Akka Typed)](https://doc.akka.io/libraries/akka-core/current/typed/actors.html),
  verified 2026-08-02.
- [Microsoft Learn, "Orleans overview," ".NET"](https://learn.microsoft.com/en-us/dotnet/orleans/overview),
  verified 2026-08-02.
- [Discord Engineering Blog, "How Discord Scaled Elixir to 5,000,000 Concurrent Users"](https://discord.com/blog/how-discord-scaled-elixir-to-5-000-000-concurrent-users),
  verified 2026-08-02.

## Code examples

### TypeScript

A minimal actor runtime built directly on the language, using an async
message loop and a private mailbox array as the queue. No framework.

```typescript
type Message =
  | { kind: "deposit"; amount: number }
  | { kind: "withdraw"; amount: number; replyTo: (ok: boolean) => void }
  | { kind: "balance"; replyTo: (balance: number) => void };

class Actor {
  private mailbox: Message[] = [];
  private processing = false;
  private balance = 0;

  send(msg: Message): void {
    this.mailbox.push(msg);
    this.drain();
  }

  private async drain(): Promise<void> {
    if (this.processing) return;
    this.processing = true;
    while (this.mailbox.length > 0) {
      const msg = this.mailbox.shift()!;
      await this.handle(msg);
    }
    this.processing = false;
  }

  private async handle(msg: Message): Promise<void> {
    switch (msg.kind) {
      case "deposit":
        this.balance += msg.amount;
        break;
      case "withdraw":
        if (msg.amount <= this.balance) {
          this.balance -= msg.amount;
          msg.replyTo(true);
        } else {
          msg.replyTo(false);
        }
        break;
      case "balance":
        msg.replyTo(this.balance);
        break;
    }
  }
}

const account = new Actor();
account.send({ kind: "deposit", amount: 100 });
account.send({
  kind: "withdraw",
  amount: 40,
  replyTo: (ok) => console.log("withdraw ok", ok),
});
account.send({
  kind: "balance",
  replyTo: (balance) => console.log("balance", balance),
});
```

### Python

The same account actor, expressed with a background thread draining a
`queue.Queue`, which is Python's closest standard-library analogue to a
mailbox with a dedicated single-threaded consumer.

```python
import queue
import threading
from dataclasses import dataclass
from typing import Callable, Union


@dataclass
class Deposit:
    amount: int


@dataclass
class Withdraw:
    amount: int
    reply_to: Callable[[bool], None]


@dataclass
class Balance:
    reply_to: Callable[[int], None]


Message = Union[Deposit, Withdraw, Balance]


class AccountActor:
    def __init__(self) -> None:
        self._mailbox: "queue.Queue[Message]" = queue.Queue()
        self._balance = 0
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def send(self, msg: Message) -> None:
        self._mailbox.put(msg)

    def _run(self) -> None:
        while True:
            msg = self._mailbox.get()
            if isinstance(msg, Deposit):
                self._balance += msg.amount
            elif isinstance(msg, Withdraw):
                if msg.amount <= self._balance:
                    self._balance -= msg.amount
                    msg.reply_to(True)
                else:
                    msg.reply_to(False)
            elif isinstance(msg, Balance):
                msg.reply_to(self._balance)


if __name__ == "__main__":
    account = AccountActor()
    account.send(Deposit(amount=100))
    account.send(Withdraw(amount=40, reply_to=lambda ok: print("withdraw ok", ok)))
    account.send(Balance(reply_to=lambda b: print("balance", b)))
    import time

    time.sleep(0.1)
```

### Go

Go has no built-in actor abstraction, but a goroutine reading from a single
channel and owning its own state directly implements the model's core
guarantee, the state below is touched by exactly one goroutine.

```go
package main

import "fmt"

type withdrawMsg struct {
	amount int
	reply  chan bool
}

type balanceMsg struct {
	reply chan int
}

type depositMsg struct {
	amount int
}

type mailbox struct {
	deposits  chan depositMsg
	withdraws chan withdrawMsg
	balances  chan balanceMsg
}

func newAccountActor() *mailbox {
	mb := &mailbox{
		deposits:  make(chan depositMsg, 16),
		withdraws: make(chan withdrawMsg, 16),
		balances:  make(chan balanceMsg, 16),
	}
	go func() {
		balance := 0
		for {
			select {
			case m := <-mb.deposits:
				balance += m.amount
			case m := <-mb.withdraws:
				if m.amount <= balance {
					balance -= m.amount
					m.reply <- true
				} else {
					m.reply <- false
				}
			case m := <-mb.balances:
				m.reply <- balance
			}
		}
	}()
	return mb
}

func main() {
	acc := newAccountActor()
	acc.deposits <- depositMsg{amount: 100}

	withdrawReply := make(chan bool)
	acc.withdraws <- withdrawMsg{amount: 40, reply: withdrawReply}
	fmt.Println("withdraw ok", <-withdrawReply)

	balanceReply := make(chan int)
	acc.balances <- balanceMsg{reply: balanceReply}
	fmt.Println("balance", <-balanceReply)
}
```

TypeScript, Python, and Go each show the model without a framework, a private
state variable, a single consuming loop or goroutine, and messages as the
only way in. Java, Rust, and Swift are omitted here since the pattern's core
idea, single-consumer ownership of state via a queue, is fully captured by
the three above and does not gain a materially different idiom in the
omitted languages beyond syntax. A reader working in Akka (Java or Scala) or
Actix (Rust) should consult that framework's own actor API directly rather
than a hand-rolled minimal example, since the framework's supervision and
mailbox-overflow handling is the part hand-rolled code in those languages
would otherwise have to reimplement.
