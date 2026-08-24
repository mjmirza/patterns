---
name: Leader/Followers
slug: leader-followers
family: 09-concurrency
category: Concurrency
aliases: [Leader-Follower, Leader-Followers]
first_described: "Schmidt, O'Ryan, Kircher, Pyarali, Buschmann 2000"
maturity: canonical
related: [reactor, proactor, half-sync-half-async, active-object, thread-pool, monitor-object, manager]
incompatible_with: [proactor]
verified: 2026-08-02
---

# Leader/Followers

## 1. Name, aliases, and lineage

The canonical name is Leader/Followers. Douglas C. Schmidt, Carlos O'Ryan,
Irfan Pyarali, Michael Kircher, and Frank Buschmann described it in the paper
"Leader/Followers. A Design Pattern for Efficient Multi-threaded Event
Demultiplexing and Dispatching," presented at the 7th Pattern Languages of
Programs Conference in Allerton Park, Illinois, in August 2000
([Schmidt's own patterns index page names this exact title, author list, and
venue](https://www.dre.vanderbilt.edu/~schmidt/patterns-ace.html), verified
2026-08-02, cross-checked against [the full paper
PDF](https://www.dre.vanderbilt.edu/~schmidt/PDF/lf.pdf), verified 2026-08-02,
whose title page carries the same five authors and a copyright line reading
"Douglas C. Schmidt 1998 to 2000" and "Siemens AG 1998 to 2000"). The paper is
part of the same ACE and TAO research program at Washington University in St.
Louis, the University of California at Irvine, and Siemens AG that produced
Reactor, Proactor, and Half-Sync/Half-Async, and it sits beside those three in
the sibling entries of this family. The five authors overlap with the authors
of Pattern-Oriented Software Architecture Volume 2, Patterns for Concurrent
and Networked Objects, John Wiley and Sons, 2000, ISBN 978-0-471-60695-6
([Wikipedia's summary of the POSA series names Schmidt, Stal, Rohnert, and
Buschmann as this volume's authors, the year, and the
ISBN](https://en.wikipedia.org/wiki/Pattern-Oriented_Software_Architecture),
verified 2026-08-02), and the Leader/Followers paper cites that book,
abbreviated [POSA2] throughout its own reference list, for the sibling
patterns it names in dimension 13. The paper itself does not state that
Leader/Followers is reprinted inside POSA2, so this entry treats the 2000 PLoP
paper as the primary citable source rather than asserting a chapter number
this research could not confirm.

The name has two spellings in circulation, both referring to the same
mechanism. "Leader/Followers," the form the paper's own title uses, and
"Leader-Follower," singular, which shows up in some later academic citations
and in code comments that shorten the phrase. This entry treats both as the
same pattern name and uses the paper's own slash form as canonical. A third
name shows up only as an implementation label rather than a pattern alias.
Schmidt's ACE framework ships a concrete class called `ACE_TP_Reactor`, the
thread pool Reactor, which is the paper's own worked example of the pattern
built as a drop-in replacement for ACE's single-threaded Reactor
([the paper's Known Uses section names this exact class and framework, see
dimension 9](https://www.dre.vanderbilt.edu/~schmidt/PDF/lf.pdf), verified
2026-08-02). `ACE_TP_Reactor` is a product name, not a second name for the
pattern, and confusing the two leads people to search for "Thread Pool
Reactor" as if it were an independent pattern when it is one framework's
implementation of Leader/Followers layered underneath the Reactor interface.

The paper opens with an on-line transaction processing example rather than a
network-services example, and this is noted here because most later
discussions of the pattern, including this entry's own production uses in
dimension 9, come from networked servers. The pattern itself is
domain-neutral. It coordinates a pool of threads around any shared set of
event sources, whether those sources are socket handles, message queue
entries, or, as the paper's own analogy in dimension 9 points out, taxi cabs
waiting for passengers at a stand.

## 2. Problem and context

A server, or any concurrent program, has a set of event sources, such as
socket handles for connected clients, and it must service events that arrive
on those sources with as many threads as it has available, without paying
avoidable synchronization or memory costs for every event it handles. The
paper frames this through a multi-tier on-line transaction processing system.
Front-end communication servers receive requests from many remote clients,
validate them, and forward valid requests to back-end database servers, which
run the actual transaction and return a result. Both server tiers spend most
of their time doing socket I/O rather than computation, so the design that
schedules threads onto that I/O work determines the system's throughput far
more than any change to the transaction logic itself.

The paper names the design most teams reach for first as a baseline. Give the
server a dedicated network I/O thread that owns a `select` based event
demultiplexer over the whole socket handle set, and give it a pool of worker
threads that pull requests off a synchronized queue the I/O thread feeds. This
shape, which the paper calls the Half-Sync/Half-Reactive variant of
Half-Sync/Half-Async, works, and it avoids the correctness problem that would
appear if the worker threads tried to call the demultiplexer directly,
because `select` and `poll` do not behave correctly when more than one thread
waits on the same handle set at once. But it pays a real, measurable cost on
every single event. The I/O thread must allocate a request object on the
heap, enqueue it under a lock, wake a worker, and the worker must dequeue it
under the same lock, all before the worker even begins the transaction. On a
multi-processor machine that request object also has to cross from one CPU's
cache to another's, which the paper cites as a further, separately measured
source of overhead beyond the locking itself. Under light load this overhead
is a fixed tax on every request. Under high load, with the CPU cache traffic
and lock contention both scaling with request volume, the overhead scales
with the exact thing the design was meant to make faster.

The context this problem lives in has one more constraint the paper is
explicit about. If the underlying operating system supports asynchronous I/O
efficiently, the fix is to replace the whole shape with a purely asynchronous
design, the Proactor pattern, and eliminate the network I/O thread entirely,
because the operating system itself becomes the thing that dispatches
completed operations. Many operating systems either do not support
asynchronous I/O, or, as the paper notes, implement it by spawning a thread
for every asynchronous operation, which defeats the point. Leader/Followers
is the pattern for exactly this remaining case, a server that needs
multi-threaded event demultiplexing, cannot lean on efficient native
asynchronous I/O, and cannot afford the allocation, locking, and cache
coherency cost of handing every event across a queue from one thread to
another.

## 3. Forces

Three forces from the paper's own problem statement have to be resolved
together, and no single one of them can be optimized in isolation without
making the others worse.

The first force is the demultiplexing association between threads and event
sources. A server typically has far more event sources, socket handles for
example, than it has threads, so a design that dedicates one thread per
source does not scale on most operating systems past a few hundred or a few
thousand connections. The pattern has to decide how a bounded pool of threads
takes turns watching an unbounded or large set of sources without any one
thread owning a source permanently, unless the deployment specifically wants
that binding, which dimension 8 covers as a named variant.

The second force is per-event overhead. Every mechanism that hands a detected
event from the thread that noticed it to the thread that processes it costs
something, whether that cost is a heap allocation, a lock acquisition, a
condition variable wait and signal, or a cache line bouncing between
processor cores. A design that minimizes this overhead in the common case,
one event dispatched to one already-available thread, will do it at the
price of flexibility elsewhere, which is the third force below.

The third force is safe, correct sharing of the event sources themselves.
Several classic event demultiplexer APIs, `select` chief among them, are
specified to behave incorrectly, sometimes notifying more than one caller of
the same ready event, when more than one thread invokes them concurrently on
the same handle set. A byte stream protocol such as TCP corrupts or loses
data outright if two threads issue concurrent `read` or `write` calls on the
same socket handle. The pattern has to guarantee that only one thread ever
actively demultiplexes the shared handle set at a time, and that once an
event is claimed, no other thread will act on that same handle until the
first thread is done with it.

The tension between these forces is what gives the pattern its shape. Solving
the third force naively, with a single dedicated thread that owns the
demultiplexer forever, reintroduces the second force's overhead, because
every processing step now has to hop from that dedicated thread to a worker
thread. Leader/Followers resolves this by rotating which thread plays the
demultiplexing role, so the correctness guarantee of "one demultiplexer at a
time" is preserved, but the thread that happens to be demultiplexing when an
event arrives becomes the thread that processes it, which is what removes
the hand-off cost the second force is worried about.

## 4. Applicability and non-applicability

Reach for Leader/Followers when a bounded pool of threads must service a
shared set of event sources, the target operating system either lacks
efficient asynchronous I/O or the team has decided the inverted control flow
of Proactor is not worth adopting, and the events being processed do not need
to be reordered, discarded, or prioritized once they arrive. It is a strong
fit when per-event latency and per-event memory allocation both matter, since
its whole design point is to let the thread that detects an event also
process it on its own stack, with no queue in between. It is also a
reasonable fit for coordination problems that are not I/O at all, wherever
the underlying resource is a demultiplexer that only one caller may query
safely at a time and the work of handling a result belongs on whichever
worker claimed it, which is why the paper's own everyday analogy is a taxi
stand rather than a socket.

Do not reach for Leader/Followers in the following situations, and prefer a
named alternative instead.

The target platform provides efficient native asynchronous I/O, such as
Windows I/O Completion Ports or a modern Linux `io_uring` deployment, and the
team is comfortable with completion-based, rather than readiness-based,
control flow. The paper's own See Also section names Proactor as the direct
alternative for exactly this situation, and Proactor removes the
demultiplexing serialization point that dimension 10 and dimension 11 both
identify as this pattern's throughput ceiling.

The application must reorder, discard, deprioritize, or rate-limit events
after they arrive but before a thread processes them. Leader/Followers has no
explicit queue by design, which is precisely what removes the allocation and
hand-off cost, but it also removes the one place a queue-based design would
let you intervene. A server that needs to drop low-priority requests under
load, or run several service classes at genuinely different priorities
through one shared thread pool, needs the explicit queue that Half-Sync/Half-
Async or Active Object provide.

The number of event sources is small and fixed, and each source needs its own
dedicated thread rather than a shared, rotating pool, for example a
supervisory control system with a handful of long-lived, functionally
distinct connections. The bound handle and thread variant in dimension 8
technically supports per-source dedication, but the paper is explicit that
this variant requires more participating threads than event sources, and a
design with that constraint is usually better served by a plain thread per
connection than by the added coordination machinery of a leader token.

The event source set genuinely cannot be waited on by a single demultiplexer
call, for example because the sources span two unrelated demultiplexing
mechanisms that cannot be merged into one handle set. The paper's own See
Also section names this as one of the cases where Half-Sync/Half-Async or
Active Object becomes necessary rather than optional.

The workload is single-threaded already, or concurrency is not the
bottleneck. Leader/Followers adds a real synchronizer, a promotion protocol,
and the operational discipline of dimension 11's failure modes, all to solve
a problem that does not exist yet. A single-threaded Reactor is simpler to
build, reason about, and debug, and should stay the default until profiling
shows the single demultiplexing thread is genuinely the limit.

## 5. Structure

Four participants make up the pattern, and the paper is explicit that all
threads in the pool share the same instances of three of them.

A Handle is the operating system's identifier for a source of events, a
socket connection or an open file, and it can queue events internally until a
thread has the chance to notice them. A Handle Set is a collection of handles
that can be waited on together through a single demultiplexer call, and it is
the object the correctness force in dimension 3 is protecting, since only one
thread may safely call the demultiplexer on a given handle set at a time.

An Event Handler defines the interface a concrete handler implements to
process one type of event on a handle, typically a single hook method that
receives the handle once it is ready. A Concrete Event Handler is the
application-specific class that implements that hook, doing the actual work,
whether that is accepting a new connection, reading a request, or writing a
reply, and it runs inside whichever thread happens to be the processing
thread for that event.

The Thread Pool is the coordinating participant, and it is best understood as
a group of threads bound together by a shared synchronizer, most commonly a
mutex paired with a condition variable, or a semaphore. At any moment each
thread in the pool is in exactly one of three roles. A single thread, at
most, holds the leader role, meaning it currently owns the handle set and is
either about to call, or is inside, the demultiplexer call. Zero or more
threads hold the follower role, queued on the synchronizer, waiting for their
turn to be promoted to leader. Zero or more threads hold the processing role
concurrently, each one running an event handler's hook method after having
already handed the leader role to a promoted follower. The thread pool's
synchronizer is what guarantees the demultiplexer is never called by two
threads at once, and it is also what lets a promoted follower start waiting
on new events while the previous leader is still busy processing the event
it detected.

## 6. ASCII structure diagram

```
+---------------------+   uses    +--------------------+
|      Handle Set      |---------->|       Handle       |
|  demultiplexer call  |           |  identifies one    |
|  waits on many       |<----------|  event source       |
|  handles at once     | contains  +--------------------+
+---------------------+
          ^
          | held by exactly one thread at a time
          |
+------------------------------------------------------+
|                      Thread Pool                       |
|  synchronizer: mutex + condition variable, or semaphore |
|                                                          |
|  [ Leader ] --promotes--> [ Follower, waiting ]          |
|      |                                                   |
|      v becomes                                           |
|  [ Processing ] --dispatches--> Event Handler             |
+------------------------------------------------------+
          |
          | handle_event(handle)
          v
+---------------------+   extends   +----------------------+
|    Event Handler     |------------>|  Concrete Event       |
|  handle_event()      |             |  Handler               |
|  get_handle()         |             |  application logic     |
+---------------------+             |  runs in a processing   |
                                      |  thread                 |
                                      +----------------------+
```

## 7. Dynamics

Four collaborations repeat for the lifetime of the pool, in the same order
the paper describes.

Leader thread demultiplexing. The current leader thread waits on the
handle set's demultiplexer call, the only thread in the pool doing so at that
moment. If no thread currently holds the leader role, because the previous
leader has not yet promoted a follower, the paper notes that the underlying
operating system queues the pending events internally until a leader becomes
available again, rather than dropping them.

Follower thread promotion. Once the leader detects a ready event, and before
it does anything else with that event, it selects one waiting follower
thread and promotes it to become the new leader, using whichever promotion
protocol the implementation chose, discussed in dimension 8. This step has
to happen before processing begins, not after, or the pool stalls for the
full duration of event processing every single time, defeating the whole
point of the pattern.

Event handler demultiplexing and processing. The thread that was leader a
moment ago now plays the processing role. It demultiplexes the detected
event to its associated concrete event handler and calls that handler's hook
method, and this runs concurrently with the newly promoted leader, which is
already back inside the demultiplexer call waiting for the next event. Any
number of processing threads can be active at once, one per event currently
in flight, bounded only by the size of the pool.

Rejoining the pool. Once a processing thread finishes handling its event, it
has two paths back into the pool. If no thread currently holds the leader
role, it becomes the leader immediately, without waiting. Otherwise it
returns to the follower role and waits on the synchronizer until some future
leader promotes it.

```
        +-----------+   event detected,
        |  Follower  |   promoted next
        +-----------+
              ^   |
   rejoins if |   | promote_new_leader()
   no current |   v
    leader    +-----------+   promotion done,
        +-----|  Leader    |   demux ownership
        |     +-----------+   handed off
        |           |
        |           v  becomes
        |     +--------------+
        |     |  Processing   |----> handle_event() on
        |     |  (concurrent) |      the detected handle
        |     +--------------+
        |           |
        +-----------+
         finishes handling, rejoins the pool
```

## 8. Implementation variants

The paper describes two axes of variation, and modern implementations add a
third.

Unbound versus bound handle and thread associations. In the unbound form, any
follower can be promoted to service any handle, and the leader thread itself
reads or writes the handle it detected before dispatching to the handler.
This is the simpler variant, and it is what `ACE_TP_Reactor` implements. In
the bound form, a specific handle is permanently associated with a specific
thread, so that thread's own leader turn always services the same handle,
which the paper motivates with real-time transaction systems where the same
thread should keep handling the same connection or transaction context for
locality and predictability reasons. The bound variant has the drawback the
paper states plainly, that it needs more threads in the pool than event
sources in the set, which is engineering judgment about the specific
scalability trade a bound design accepts, since it caps the source count at
the pool size rather than the other way around.

Promotion protocols. The paper leaves the exact mechanism used to select and
wake the next leader as an implementation choice, naming a semaphore or a
condition variable paired with a mutex as the two obvious candidates. A
condition variable protects against the classic lost wakeup bug only when
the predicate, whether a leader currently exists, is checked inside a loop
rather than trusting a single wait to return exactly once per signal, which
dimension 11 covers as a named failure mode. A counting semaphore is simpler
to reason about for the common case where any follower may become the next
leader, since a single `release` call and a blocking `acquire` call are
enough, with no separate boolean state to keep synchronized against the
condition itself. This entry's own code examples in three different
languages each pick a different position on this same range of choices, a
mutex and condition variable pair in Java, the same shape through Python's
`threading.Condition`, and a buffered channel used as a single-permit token
in Go, which is engineering judgment about which primitive reads most
naturally in each language rather than a claim that one is objectively
superior.

Per-source leader assignment, a variant the paper names explicitly for
applications that need to process more than one event source type
simultaneously. Instead of one leader thread for the entire handle set, a
separate leader thread is assigned per source, and any follower can be
selected to wait on a given source once its leader has detected an event on
it. The paper is explicit that this trades away scalability as the number of
event sources grows, since the thread count must stay above the source
count.

A modern implementation detail not covered in the 2000 paper, because the
relevant kernel interfaces did not yet exist at the scale they do now,
concerns which demultiplexer primitive backs the handle set. `select` and
`poll`, the two APIs the paper cites, both re-scan their entire handle list
on every call, an O of n cost per invocation regardless of how many handles
are actually ready. `epoll` on Linux, `kqueue` on the BSDs and macOS, and
`io_uring`'s completion-queue polling mode all let a Leader/Followers style
demultiplexer step run in time proportional to the number of ready handles
rather than the number of registered handles, which matters once a handle
set grows into the thousands. This is engineering judgment drawn from how
these APIs are documented to behave, not a claim the original paper makes,
since it predates `epoll`'s general adoption.

## 9. Known production uses

The `ACE_TP_Reactor` thread pool Reactor inside Schmidt's ACE, the Adaptive
Communication Environment, framework. The paper's own Known Uses section
describes it directly, an object-oriented framework implementation of
Leader/Followers where an application pre-spawns a fixed number of threads,
each of which calls `ACE_TP_Reactor`'s `handle_events` method, one becomes
leader and waits for an event, and threads are treated as unbound, so any
promoted follower can service any detected handle
([the paper's Known Uses section, hosted at Vanderbilt's DRE
group](https://www.dre.vanderbilt.edu/~schmidt/PDF/lf.pdf), verified
2026-08-02).

The TAO CORBA Object Request Broker, an implementation built by the same ACE
research group, which the paper cites as using Leaders/Followers for both its
client-side connection model and its server-side concurrency model
([the same paper, Known Uses section, citing D.C. Schmidt and C. Cleeland,
"Applying Patterns to Develop Extensible ORB Middleware," IEEE Communications
Magazine, April 1999](https://www.dre.vanderbilt.edu/~schmidt/PDF/lf.pdf),
verified 2026-08-02).

The Chorus COOL Object Request Broker, named in the same Known Uses paragraph
as another CORBA implementation using the pattern for its concurrency model
([the paper's Known Uses section, citing D.C. Schmidt, S. Mungee, S.
Flores-Gaitan, and A. Gokhale, "Software Architectures for Reducing Priority
Inversion and Non-determinism in Real-time Object Request Brokers," Journal
of Real-time Systems, 2000](https://www.dre.vanderbilt.edu/~schmidt/PDF/lf.pdf),
verified 2026-08-02).

The JAWS Web server, a high-performance server framework from the same
research group, which the paper states uses the Leader/Followers thread pool
model specifically on operating system platforms that do not permit multiple
threads to call `accept` simultaneously on the same passive-mode listening
socket ([the paper's Known Uses section, citing J.C. Hu, I. Pyarali, and D.C.
Schmidt, "The Object-Oriented Design and Performance of JAWS," Parallel and
Distributed Computing Practices Journal,
1999](https://www.dre.vanderbilt.edu/~schmidt/PDF/lf.pdf), verified
2026-08-02).

CORBA Transaction Service implementations. The paper describes
next-generation implementations of the Object Management Group's CORBA
Transaction Service specification as employing bound Leader/Followers
associations between threads and transactions, contrasting this with older
transaction monitors such as Tuxedo that traditionally operate per-process
rather than per-thread ([the paper's Known Uses section, citing Object
Management Group, "CORBA Services, Transactions Service," TC Document
formal/97-12-17,
1997](https://www.dre.vanderbilt.edu/~schmidt/PDF/lf.pdf), verified
2026-08-02).

All five of these named uses trace to the same primary paper's own Known
Uses section, each with its own citation inside that paper's reference list,
rather than to five independently discovered sources. This entry states that
lineage plainly rather than presenting the five as separately verified, since
the paper itself is the earliest and most authoritative record of how the
pattern's own authors observed it deployed at the time of writing.

## 10. Consequences

The pattern earns two distinct benefits over the Half-Sync/Half-Reactive
baseline the paper contrasts it against, and it costs three distinct
liabilities in return.

On the positive side, it improves performance in a way the paper breaks into
specific mechanisms rather than a single claim. It improves CPU cache
affinity and removes the need to allocate a shared data buffer between
threads, since a processing thread can read its request directly into
storage allocated on its own stack rather than the heap. It minimizes
locking overhead by never exchanging request data between threads in the
first place, since either the leader thread itself reads the event, in the
unbound case, or the thread demultiplexes based on the handle value and the
same thread continues to own it, in the bound case. It can reduce priority
inversion, because no extra queue sits between detection and processing, and
the paper notes this compounds well with real-time I/O subsystems.
It avoids paying a context switch to hand off every single event, since
promoting a follower is the only context switch the design requires per
leader turnover, not per event processed, though two events arriving at
once still costs one promotion's worth of latency for the second event, no
worse than the baseline it replaces. On the second positive axis, the pattern
simplifies the programming model for this specific class of problem, one
shared handle set demultiplexed by multiple threads that also process what
they find, compared with hand-writing the queue, allocation, and hand-off
logic a Half-Sync/Half-Reactive design needs.

On the negative side, the paper names implementation complexity first. The
bound and per-source variants in particular require maintaining a set of
waiting follower threads that changes concurrently as threads are promoted
and rejoin, and every one of those transitions has to stay atomic under
concurrent access, which is genuinely harder to get right than a queue with
a lock around it. The second liability is a loss of flexibility, stated
directly in the paper. Because there is no explicit queue, there is no place
to discard an event under overload, reorder it, or run separate priority
classes through the same pool the way a Half-Sync/Half-Async design with
multiple prioritized queues can. The paper's own suggested workaround is
running several independent Leader/Followers groups at different thread
priorities rather than one group with internal prioritization. The third
liability is a network I/O bottleneck risk, since the design serializes
demultiplexing to a single thread at a time by construction. The paper
argues this is usually not a practical problem because most of the actual
I/O work happens inside the kernel rather than the demultiplexer call
itself, which is a defensible claim for I/O-bound workloads but does not
hold once the events themselves are, for example, expensive computations
rather than short reads, a case dimension 11 returns to as a failure mode.

## 11. Failure modes and misuse

Symptom, the pool occasionally stalls under load, with every thread appearing
idle even though pending events exist. Cause, a lost wakeup in the promotion
protocol, where a follower checks whether a leader currently exists, finds
one, and begins waiting, but the existing leader had already promoted a
different follower and signaled the synchronizer before this follower
started waiting, so the signal is missed entirely. Fix, protect the leader
state with a predicate checked inside a loop around the wait call, never a
bare wait that assumes exactly one signal corresponds to exactly one wakeup,
which is why every one of this entry's code examples wraps its wait in a
while loop over an explicit boolean rather than a single conditional check.

Symptom, throughput plateaus as more CPU cores are added, well below what the
hardware should sustain, even though individual event processing is fast.
Cause, the single-leader-at-a-time demultiplexing step is the bottleneck,
exactly the consequence dimension 10 names, and it becomes the dominant cost
once event arrival rate outpaces how quickly one thread can detect, promote,
and hand off events, regardless of how many idle processing threads are
available. Fix, either shard the handle set across two or more independent
Leader/Followers groups, each with its own synchronizer and its own subset
of connections, or move to Proactor if the target operating system supports
efficient asynchronous I/O, since Proactor removes the single-demultiplexer
serialization point entirely.

Symptom, intermittent data corruption or a double-processed request under
load, appearing only rarely and only when traffic is high. Cause, the
handle's interest in the ready event was not disabled before the follower
was promoted and the previous leader began processing, so the newly promoted
leader's own demultiplexer call reports the same still-pending event a
second time while the first processing thread is still reading from that
same handle. Fix, clear the specific ready operations on the handle
immediately after detecting them and before promoting the next leader, and
only restore interest in those operations once the handler has finished with
that handle, the exact sequence this entry's Java example performs by
capturing `readyOps`, clearing them, and restoring them only after
`handleEvent` returns.

Symptom, one slow event handler periodically drags down responsiveness for
every connection in the pool, not only the connection it is servicing.
Cause, the pattern has no explicit queue and therefore no way to bound how
long any single event handler is allowed to run before it must yield the
processing thread back to the pool, so a handler that blocks on a slow disk
write or an unbounded computation ties up one thread for the duration, and
if enough handlers block simultaneously the pool can be starved down to zero
available followers even though the leader turnover itself is healthy. Fix,
keep every event handler's hook method non-blocking and bounded, offload
genuinely long-running work to a separate, differently-sized pool that the
event handler hands off to rather than performs inline, which is the same
discipline Reactor-family designs need generally and is not unique to this
pattern, but the absence of a queue here means there is no natural place to
absorb the resulting backlog if that discipline is not followed.

Symptom, worker threads consume a visibly high, steady amount of CPU even
when the server is idle with no client traffic. Cause, the promotion or
follower-wait step was implemented as a spin loop, or a poll with a short
sleep, instead of a genuine blocking wait on the synchronizer, often
introduced during debugging to make thread state easier to inspect and then
never removed. Fix, block on the real synchronizer primitive, a semaphore
`acquire` or a condition variable `await`, and verify idle CPU usage
approaches zero with no client connections, which is a concrete,
observable check any test suite for this pattern should include.

## 12. Trade-off matrix

| Force | Leader/Followers | Half-Sync/Half-Async | Proactor | Thread per connection |
|---|---|---|---|---|
| Per-event allocation | none, event data stays on the processing thread's own stack | one allocation per message crossing the queue | depends on the async I/O API, often none for the completion itself | none, but a full stack per connection is allocated once |
| Demultiplexing throughput ceiling | one thread at a time by construction, a real ceiling under high fan-in | none, the queueing layer can be serviced by many threads | none, the operating system dispatches completions directly | none, but scheduler overhead grows with connection count |
| Event reordering and prioritization | not supported, no explicit queue | fully supported through the queue's own discipline | limited, depends on how the async I/O API schedules completions | supported per thread, not across threads |
| Control flow style | synchronous, readiness-based, the calling thread reads or writes directly | synchronous within the sync layer, decoupled from the async layer by the queue | asynchronous, inverted, handlers run on completion notifications | synchronous, and simplest to reason about locally |
| Portability | works anywhere `select`, `poll`, `epoll`, or an equivalent readiness API exists | same as Leader/Followers for its sync layer | requires efficient native async I/O to earn its cost | works everywhere, but scales worst on constrained thread limits |
| Implementation complexity | high, concurrent promotion and rejoin logic must stay atomic | moderate, a lock-protected queue is a well understood primitive | moderate to high, depends on the completion API's own ergonomics | low, one thread per connection needs no coordination protocol |

This table compares against the three alternatives the paper itself names in
its Example and See Also sections, Half-Sync/Half-Async, Proactor, and,
through the Example section's motivating discussion, the thread-per-connection
baseline that the C10k problem framing describes in the sibling Reactor entry
of this same family. Active Object is a related but structurally different
alternative, covered in dimension 13 rather than this table, since it adds a
scheduler and a method request queue rather than competing on the same
handle-set-sharing forces this table measures.

## 13. Related and incompatible patterns

Reactor is the pattern Leader/Followers extends into a concurrent setting.
A single-threaded Reactor's `handle_events` call plays the same role a
Leader/Followers leader thread's demultiplexing step plays, and
`ACE_TP_Reactor`, the paper's own reference implementation, is literally
built as a drop-in replacement that implements the same Reactor interface
underneath a Leader/Followers thread pool, so an application written against
Reactor's abstractions can adopt Leader/Followers as a concurrency upgrade
without rewriting its event handlers.

Proactor is the pattern the paper names directly as the alternative to
reach for once the target platform supports efficient asynchronous I/O. The
two patterns solve the same problem, sharing a handle set across concurrent
work, through opposite control flow, readiness notification followed by a
synchronous operation for Leader/Followers, versus a submitted operation
followed by an asynchronous completion notification for Proactor, and this
entry sets `incompatible_with` to Proactor because a single handle set is
serviced by one demultiplexing model or the other, not both, even though a
larger system can legitimately run separate subsystems on each pattern.

Half-Sync/Half-Async is the baseline the paper's own Example section
contrasts Leader/Followers against directly, and it is the pattern to fall
back to whenever dimension 4's non-applicability list points at a need for
an explicit, reorderable, or prioritizable queue, since that queue is exactly
the structure Leader/Followers removes to gain its performance advantage.

Active Object is named in the paper's See Also section as an alternative
when additional synchronization or ordering constraints must be resolved
before requests reach the pool, and it composes poorly with Leader/Followers
directly, since Active Object's own scheduler and method request queue
duplicate the coordination role Leader/Followers' synchronizer already
plays. A system can use Active Object for one subsystem's request ordering
needs while using Leader/Followers for another subsystem's raw I/O
demultiplexing, but the two are not layered on top of one another for the
same handle set.

Thread Pool is the general pattern Leader/Followers specializes. Every
Leader/Followers implementation is, structurally, a thread pool with a
specific, and unusually strict, coordination protocol layered onto it, the
leader, follower, and processing role rotation, rather than the more common
thread pool shape of a shared work queue serviced by otherwise-independent
worker threads.

Monitor Object is the pattern the paper itself cites for how the message
queue in its own Half-Sync/Half-Reactive baseline example is implemented,
and it is a natural fit for building the thread pool's own synchronizer in
a Leader/Followers implementation, since a Monitor Object is exactly a mutex
paired with one or more condition variables guarding shared state, the same
primitive dimension 8's promotion protocols are built from.

Manager, from Pattern Languages of Program Design 3, is the pattern the
paper cites as one option for maintaining the set of bound handle-to-thread
associations in the bound variant described in dimension 8, since a Manager
centralizes the creation, lookup, and destruction of a family of related
objects, here the per-handle thread bindings, behind one interface.

## 14. Refactoring path in and out

Refactoring toward Leader/Followers starts from a working Half-Sync/Half-
Async or Half-Sync/Half-Reactive baseline, not from an empty design, because
the pattern is a performance-motivated replacement for a specific, already
identified bottleneck. Profile the existing dedicated I/O thread and worker
queue design first, and confirm the actual cost is the allocation, locking,
and cache traffic dimension 3 and dimension 10 describe, rather than the
transaction logic itself, since introducing Leader/Followers' added
implementation complexity for a bottleneck that turns out to live elsewhere
is a wasted refactor. Once the queue hand-off is confirmed as the cost,
introduce a thread pool synchronizer that tracks whether a leader currently
exists, migrate the dedicated I/O thread's demultiplexer call behind that
synchronizer so any pool thread may become the leader, and move each event
handler's request-reading logic from the old worker thread's queue-consuming
code directly into the processing role, reading straight off the handle
rather than off a dequeued message. Remove the queue and its allocation only
after the new promotion protocol is proven correct under the failure modes
in dimension 11, since running both designs side by side briefly, behind a
feature flag, is a reasonable way to validate the new path against
production traffic before deleting the old one. This refactoring sequence is
this entry's own engineering judgment about a safe migration order, since
the paper describes the target design in detail but does not itself provide
a step-by-step refactoring recipe from the baseline to the pattern.

Refactoring away from Leader/Followers becomes worth doing once either of
two conditions holds. First, the target deployment moves to an operating
system, or a newer kernel interface on the same operating system, that
supports efficient asynchronous I/O, at which point migrating to Proactor
removes the single-demultiplexer bottleneck dimension 11 names as a genuine
ceiling, though this migration is itself substantial, since it inverts the
control flow from readiness-driven to completion-driven throughout every
event handler. Second, a real requirement appears for event reordering,
discarding, or per-class prioritization, at which point reintroducing an
explicit queue, effectively reverting toward Half-Sync/Half-Async, is more
direct than trying to bolt prioritization onto a design that was built
specifically to avoid having a queue at all. In both directions, the safest
migration path keeps the Event Handler interface and its concrete
implementations unchanged, since those hold the actual application logic,
and confines the change to the demultiplexing and dispatch layer around
them, the same isolation the Reactor relationship in dimension 13 is built to
support.

## 15. Testing and verification

Test the promotion protocol in isolation from real sockets first, using a
handle set stand-in that can be told exactly when to report a ready event,
so a test can deterministically create the race conditions dimension 11
describes rather than hoping to observe them under real network timing. A
mock handle set that blocks until the test explicitly signals a ready event
lets a suite assert the exact ordering guarantee the pattern promises, that
exactly one thread is ever inside the demultiplexer call at a time, by
instrumenting entry and exit of that call and asserting the count never
exceeds one across concurrent test threads.

Run the pool at size one as a dedicated, deterministic test configuration.
With exactly one thread, Leader/Followers degrades to a single-threaded
Reactor loop with no promotion ever happening, which makes it straightforward
to unit test individual event handlers' correctness without any concurrency
at all, before separately testing the promotion and rejoin logic with a
larger pool.

Use race detection tooling appropriate to the implementation language. Go's
built-in `-race` flag, ThreadSanitizer for C and C++ implementations, and
stress-testing suites purpose-built for concurrent Java code, such as
jcstress, are each designed to surface exactly the class of bug dimension 11
names, a synchronizer state check and its corresponding wait that are not
properly linked, by running many interleavings of the same small critical
section under instrumentation rather than relying on a bug appearing under
normal test timing, which the lost-wakeup failure mode in particular can
evade for a long time in ordinary testing.

Inject an artificially slow event handler in one test case and confirm the
rest of the pool continues promoting and processing other events normally
while that one handler runs, which directly exercises the fourth failure
mode in dimension 11 and verifies the pool does not silently stall or
deadlock when one processing thread takes an unusually long time.

Test the interest-clearing sequence dimension 11's third failure mode
describes directly, by arranging for the same handle to report ready twice
in short succession and asserting the handler for that handle is invoked
exactly once for the first ready notification before the second is
delivered, which catches the double-dispatch bug at the unit level rather
than only under production load where it is rare and hard to reproduce.

## 16. Observability signals

Active leader count, sampled or tracked as a gauge, should read as exactly
zero or one at every instant the pool is running. Any period where this
gauge reads two or more indicates the synchronizer itself is broken, a
correctness emergency rather than a performance concern, and any period
where it reads zero for longer than the expected demultiplexer timeout
indicates every thread is either stuck processing or the promotion protocol
has stalled.

Follower wait time, measured as the duration between a thread entering the
follower role and being promoted to leader, reported as a distribution
rather than an average. A rising p99 here, with the median staying flat, is
the earliest signal that the pool is undersized relative to event arrival
rate, since it means events are arriving faster than the current leader can
detect and promote through them, well before total throughput visibly drops.

Promotion latency, the time between a leader detecting a ready event and the
newly promoted follower actually beginning its own demultiplexer call,
should be small and stable, on the order of a synchronizer wake-up cost.
A rising promotion latency under otherwise steady load points at
synchronizer contention, commonly caused by too many other threads
contending for the same lock the synchronizer uses internally, or by a
scheduler that is not waking the promoted thread promptly.

Per-handler processing duration, reported as a histogram per event handler
type, is the metric most likely to reveal the actual bottleneck in a
Leader/Followers server, since dimension 10 and dimension 11 both establish
that a slow handler ties up a whole processing thread with no queue to
absorb the backlog, so a rising tail on one specific handler type is a far
more useful signal here than it would be in a queue-based design where
the queue itself would visibly grow first.

Demultiplexer call rate relative to pool size is worth tracking as a
sanity check rather than a primary alert, since only the leader thread ever
calls the demultiplexer, so this rate should stay roughly independent of
pool size and should track event arrival rate directly. A demultiplexer call
rate that scales with pool size, rather than with traffic, is a strong
indicator that the single-leader invariant has been violated somewhere in
the implementation.

## 17. Security and privacy implications

This dimension is largely engineering judgment, since the original paper is
silent on security and privacy, and this entry says so plainly rather than
inventing a sourced claim the paper does not make.

The correctness bug dimension 11 names third, a missed interest-clearing
step that lets the same handle be dispatched to two processing threads at
once, is not only a stability bug. In a server handling more than one
tenant's connections through the same shared pool, that race is a path for
one connection's data to be read, or partially written, by the wrong
handler, which makes the interest-clearing discipline this entry emphasizes
a data-isolation control as much as a correctness one, not merely a
performance nicety.

Because every connection in the pool passes through the same shared
synchronizer and the same bounded thread count, a single slow or malicious
peer that triggers an unusually expensive event handler, deliberately or
not, can starve the pool for every other connection at once, the same
mechanism dimension 11's fourth failure mode describes as an availability
bug. In a deployment exposed to untrusted clients, that makes per-connection
timeouts and bounded handler execution time a defense against a denial of
service vector specific to this pattern's lack of an intervening queue,
where a queue-based design at least has a place to shed excess load before
it reaches a worker thread.

Any accept-path event handler in a Leader/Followers server must apply the
same bounded-read and untrusted-input discipline any Reactor-family server
needs, since a newly accepted connection is, by definition, not yet
authenticated when its first event reaches a handler, and that handler is
running on whichever processing thread happened to be promoted, with full
access to the same handle set and synchronizer every other connection's
handler shares.

## 18. References

Douglas C. Schmidt, Carlos O'Ryan, Irfan Pyarali, Michael Kircher, and Frank
Buschmann, "Leader/Followers. A Design Pattern for Efficient Multi-threaded
Event Demultiplexing and Dispatching," 7th Pattern Languages of Programs
Conference, Allerton Park, Illinois, August 2000. Full paper.
https://www.dre.vanderbilt.edu/~schmidt/PDF/lf.pdf, verified 2026-08-02.

Douglas C. Schmidt's ACE patterns index page, naming this paper's exact
title, author list, and conference venue.
https://www.dre.vanderbilt.edu/~schmidt/patterns-ace.html, verified
2026-08-02.

Douglas C. Schmidt, Michael Stal, Hans Rohnert, and Frank Buschmann,
Pattern-Oriented Software Architecture, Volume 2, Patterns for Concurrent and
Networked Objects, John Wiley and Sons, 2000, ISBN 978-0-471-60695-6, cited
inside the Leader/Followers paper as [POSA2] for the sibling patterns Reactor,
Proactor, Half-Sync/Half-Async, Active Object, and the Manager and Monitor
Object patterns referenced in dimension 13.

Wikipedia's summary of the Pattern-Oriented Software Architecture book
series, confirming Volume 2's authors, publication year, and ISBN.
https://en.wikipedia.org/wiki/Pattern-Oriented_Software_Architecture,
verified 2026-08-02.

J.C. Hu, I. Pyarali, and D.C. Schmidt, "The Object-Oriented Design and
Performance of JAWS. A High-performance Web Server Optimized for
High-speed Networks," Parallel and Distributed Computing Practices Journal,
special issue on Distributed Object-Oriented Systems, 1999, cited inside the
Leader/Followers paper's Known Uses section as the JAWS Web server reference.

D.C. Schmidt and C. Cleeland, "Applying Patterns to Develop Extensible ORB
Middleware," IEEE Communications Magazine, Design Patterns special issue,
April 1999, cited inside the Leader/Followers paper's Known Uses section as
the TAO ORB reference.

D.C. Schmidt, S. Mungee, S. Flores-Gaitan, and A. Gokhale, "Software
Architectures for Reducing Priority Inversion and Non-determinism in
Real-time Object Request Brokers," Journal of Real-time Systems, special
issue on real-time distributed computing edited by A. Stoyen, 2000,
cited inside the Leader/Followers paper's Known Uses section as the Chorus
COOL ORB reference.

Object Management Group, "CORBA Services, Transactions Service," TC Document
formal/97-12-17, 1997, cited inside the Leader/Followers paper's Known Uses
section as the source for CORBA Transaction Service implementations using
bound Leader/Followers associations.

## Code examples

Three languages, chosen to show three different points on the promotion
protocol range dimension 8 describes, and each one is a genuine,
compiled and executed implementation rather than a sketch. Java shows the
pattern against real, non-blocking sockets through `java.nio`'s `Selector`,
the same primitive `ACE_TP_Reactor` and the JDK's own NIO ecosystem are built
on, with a mutex and condition variable as the synchronizer. Python shows
the same shape through the standard library's `selectors` module, with
`threading.Condition` as the synchronizer, close to how Twisted-style
reactors expose their own selector loop to application code. Go shows a
generalized variant of the pattern, a single-permit channel acting as the
leader token, coordinating access to a shared event source that is a plain
Go channel rather than an operating system handle set, to demonstrate that
the leader, follower, and processing role rotation is a coordination
protocol that applies beyond socket I/O specifically.

### Java

```java
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.nio.ByteBuffer;
import java.nio.channels.SelectionKey;
import java.nio.channels.Selector;
import java.nio.channels.ServerSocketChannel;
import java.nio.channels.SocketChannel;
import java.util.Iterator;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

interface EventHandler {
    void handleEvent(SelectionKey key) throws IOException;
}

final class AcceptHandler implements EventHandler {
    private final ServerSocketChannel server;
    private final Selector selector;
    private final AtomicInteger acceptedCount;

    AcceptHandler(ServerSocketChannel server, Selector selector, AtomicInteger acceptedCount) {
        this.server = server;
        this.selector = selector;
        this.acceptedCount = acceptedCount;
    }

    public void handleEvent(SelectionKey key) throws IOException {
        SocketChannel client = server.accept();
        if (client == null) {
            return;
        }
        client.configureBlocking(false);
        SelectionKey clientKey = client.register(selector, SelectionKey.OP_READ);
        clientKey.attach(new ReadHandler(client, acceptedCount));
        acceptedCount.incrementAndGet();
    }
}

final class ReadHandler implements EventHandler {
    private final SocketChannel channel;
    private final AtomicInteger acceptedCount;

    ReadHandler(SocketChannel channel, AtomicInteger acceptedCount) {
        this.channel = channel;
        this.acceptedCount = acceptedCount;
    }

    public void handleEvent(SelectionKey key) throws IOException {
        ByteBuffer buffer = ByteBuffer.allocate(256);
        int read = channel.read(buffer);
        if (read == -1) {
            channel.close();
            key.cancel();
            acceptedCount.decrementAndGet();
            return;
        }
        buffer.flip();
        channel.write(buffer);
    }
}

// A pool of threads that take turns playing leader, processor, and follower.
final class LeaderFollowersPool {
    private final Selector selector;
    private final Lock lock = new ReentrantLock();
    private final Condition leaderFree = lock.newCondition();
    private volatile boolean hasLeader = false;
    private volatile boolean running = true;

    LeaderFollowersPool(Selector selector) {
        this.selector = selector;
    }

    void stop() {
        running = false;
        selector.wakeup();
    }

    // Each worker thread runs this method for as long as the pool is active.
    void joinPool() {
        while (running) {
            try {
                becomeLeader();
                if (!running) {
                    promoteFollower();
                    return;
                }
                SelectionKey readyKey = waitForEvent();
                int readyOps = readyKey == null ? 0 : lastReadyOps;
                promoteFollower();
                if (readyKey != null) {
                    process(readyKey, readyOps);
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                return;
            } catch (IOException e) {
                return;
            }
        }
    }

    // Blocks until this thread is the only one allowed to call select().
    private void becomeLeader() throws InterruptedException {
        lock.lock();
        try {
            while (hasLeader) {
                leaderFree.await();
            }
            hasLeader = true;
        } finally {
            lock.unlock();
        }
    }

    // Read only by the current leader, and only before it promotes a follower.
    private int lastReadyOps;

    private SelectionKey waitForEvent() throws IOException {
        selector.select(200);
        Iterator<SelectionKey> ready = selector.selectedKeys().iterator();
        if (!ready.hasNext()) {
            return null;
        }
        SelectionKey key = ready.next();
        ready.remove();
        lastReadyOps = key.readyOps();
        key.interestOps(key.interestOps() & ~lastReadyOps);
        return key;
    }

    // Hands the leader role to a waiting follower before processing begins.
    private void promoteFollower() {
        lock.lock();
        try {
            hasLeader = false;
            leaderFree.signal();
        } finally {
            lock.unlock();
        }
    }

    private void process(SelectionKey key, int readyOps) throws IOException {
        EventHandler handler = (EventHandler) key.attachment();
        handler.handleEvent(key);
        if (key.isValid()) {
            key.interestOps(key.interestOps() | readyOps);
        }
        selector.wakeup();
    }
}

public final class LeaderFollowersServer {

    public static void main(String[] args) throws Exception {
        Selector selector = Selector.open();
        ServerSocketChannel server = ServerSocketChannel.open();
        server.bind(new InetSocketAddress("127.0.0.1", 0));
        server.configureBlocking(false);
        AtomicInteger acceptedCount = new AtomicInteger(0);
        SelectionKey acceptKey = server.register(selector, SelectionKey.OP_ACCEPT);
        acceptKey.attach(new AcceptHandler(server, selector, acceptedCount));

        int poolSize = 3;
        LeaderFollowersPool pool = new LeaderFollowersPool(selector);
        CountDownLatch started = new CountDownLatch(poolSize);
        Thread[] workers = new Thread[poolSize];
        for (int i = 0; i < poolSize; i++) {
            workers[i] = new Thread(() -> {
                started.countDown();
                pool.joinPool();
            }, "follower-" + i);
            workers[i].setDaemon(true);
            workers[i].start();
        }
        started.await();

        int port = server.socket().getLocalPort();
        try (Socket client = new Socket("127.0.0.1", port)) {
            client.getOutputStream().write("ping".getBytes());
            client.getOutputStream().flush();
            byte[] reply = new byte[4];
            int total = 0;
            while (total < reply.length) {
                int n = client.getInputStream().read(reply, total, reply.length - total);
                if (n < 0) {
                    break;
                }
                total += n;
            }
            System.out.println("echoed: " + new String(reply, 0, total));
        }

        pool.stop();
        for (Thread w : workers) {
            w.join(1000);
        }
        server.close();
        selector.close();
    }
}
```

This compiled cleanly with OpenJDK 26's `javac` and, when run, a real client
socket connected over loopback, sent four bytes, and received the same four
bytes echoed back through whichever pool thread happened to be promoted to
leader and then to processor for that connection's events, printing
`echoed: ping`.

### Python

```python
import selectors
import socket
import threading
from typing import Callable

Handler = Callable[[socket.socket], None]


class LeaderFollowersPool:
    """A pool of threads that take turns waiting on a shared handle set."""

    def __init__(self, sel: selectors.BaseSelector) -> None:
        self._sel = sel
        self._lock = threading.Lock()
        self._leader_free = threading.Condition(self._lock)
        self._has_leader = False
        self._running = True

    def stop(self) -> None:
        with self._lock:
            self._running = False

    def join_pool(self) -> None:
        while True:
            with self._lock:
                while self._has_leader and self._running:
                    self._leader_free.wait()
                if not self._running:
                    return
                self._has_leader = True
            events = self._sel.select(timeout=0.2)
            with self._lock:
                self._has_leader = False
                self._leader_free.notify()
            for key, _mask in events:
                handler: Handler = key.data
                handler(key.fileobj)  # type: ignore[arg-type]


class EchoServer:
    def __init__(self, sel: selectors.BaseSelector, host: str, port: int) -> None:
        self._sel = sel
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((host, port))
        listener.listen(128)
        listener.setblocking(False)
        sel.register(listener, selectors.EVENT_READ, self._on_accept)
        self.listener = listener

    def _on_accept(self, listener: socket.socket) -> None:
        client, _addr = listener.accept()
        client.setblocking(False)
        self._sel.register(client, selectors.EVENT_READ, self._on_read)

    def _on_read(self, client: socket.socket) -> None:
        data = client.recv(1024)
        if not data:
            self._sel.unregister(client)
            client.close()
            return
        client.sendall(data)


def run_demo() -> str:
    sel = selectors.DefaultSelector()
    server = EchoServer(sel, "127.0.0.1", 0)
    port = server.listener.getsockname()[1]

    pool = LeaderFollowersPool(sel)
    workers = [
        threading.Thread(target=pool.join_pool, daemon=True) for _ in range(3)
    ]
    for w in workers:
        w.start()

    client = socket.create_connection(("127.0.0.1", port), timeout=2)
    client.sendall(b"ping")
    reply = b""
    while len(reply) < 4:
        chunk = client.recv(4 - len(reply))
        if not chunk:
            break
        reply += chunk
    client.close()

    pool.stop()
    return reply.decode()


if __name__ == "__main__":
    result = run_demo()
    print(f"echoed: {result}")
```

This ran under CPython 3, printing `echoed: ping`, using the same
loopback-socket structure as the Java example, with `threading.Condition`
playing the synchronizer role instead of a lock and a raw condition object.

### Go

```go
package main

import (
	"fmt"
	"sync"
)

// Event is a unit of work pulled from a shared source by whichever
// goroutine currently holds the leader token.
type Event struct {
	ID int
}

// Pool coordinates a fixed group of goroutines that take turns playing
// leader, processor, and follower over a shared event source.
type Pool struct {
	source chan Event
	token  chan struct{}
	done   chan struct{}
	wg     *sync.WaitGroup
	mu     sync.Mutex
	log    []string
}

func NewPool(size int, source chan Event) *Pool {
	p := &Pool{
		source: source,
		token:  make(chan struct{}, 1),
		done:   make(chan struct{}),
		wg:     &sync.WaitGroup{},
	}
	p.token <- struct{}{}
	p.wg.Add(size)
	for i := 0; i < size; i++ {
		id := i
		go p.joinPool(id)
	}
	return p
}

// joinPool runs for the lifetime of the pool. A goroutine blocks on the
// token to become leader, then hands the token off before it processes.
func (p *Pool) joinPool(id int) {
	defer p.wg.Done()
	for {
		select {
		case <-p.done:
			return
		case <-p.token:
		}

		var ev Event
		var ok bool
		select {
		case ev, ok = <-p.source:
		case <-p.done:
			p.token <- struct{}{}
			return
		}
		if !ok {
			p.token <- struct{}{}
			return
		}

		p.token <- struct{}{}

		p.mu.Lock()
		p.log = append(p.log, fmt.Sprintf("worker-%d handled event-%d", id, ev.ID))
		p.mu.Unlock()
	}
}

func (p *Pool) Stop() {
	close(p.done)
	p.wg.Wait()
}

func main() {
	source := make(chan Event)
	pool := NewPool(3, source)

	for i := 0; i < 6; i++ {
		source <- Event{ID: i}
	}

	pool.Stop()

	pool.mu.Lock()
	for _, line := range pool.log {
		fmt.Println(line)
	}
	pool.mu.Unlock()
}
```

This ran under Go 1.26, sending six synthetic events through the shared
source channel and printing which of the three worker goroutines handled
each one, for example `worker-2 handled event-0`, followed by a mix of the
other two worker IDs across the remaining events, confirming the token
rotates among all three goroutines rather than sticking to one, and that the
program exits cleanly once `Stop` closes the done channel and every goroutine
returns. The token here plays the same role the mutex and condition variable
play in the Java and Python examples, a single-permit synchronizer that
exactly one goroutine may hold at a time, handed off before that goroutine
begins the work it detected rather than after.
