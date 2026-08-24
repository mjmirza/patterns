---
name: Vector Clock
slug: vector-clock
family: 12-data-storage
category: Data and Storage
aliases: [Vector Timestamp, Fidge-Mattern Clock]
first_described: "Fidge 1988, Mattern 1989"
maturity: canonical
related: [lamport-timestamp, version-vector, gossip-protocol, crdt, eventual-consistency, read-repair]
incompatible_with: []
verified: 2026-08-02
---

# Vector Clock

## 1. Name, aliases, and lineage

The canonical name is Vector Clock. The mechanism was published independently
and almost simultaneously by two researchers who were not aware of each
other's work. Colin J. Fidge described it in "Timestamps in Message-Passing
Systems That Preserve the Partial Ordering", Proceedings of the 11th
Australian Computer Science Conference, 1988, pages 56 to 66
(https://www.semanticscholar.org/paper/Timestamps-in-Message-Passing-Systems-That-Preserve-Fidge/e706b8ae2952740cb95c0182c4c44b0d11cc54c1,
verified 2026-08-02). Friedemann Mattern described the same construction under
the name "vector time" in "Virtual Time and Global States of Distributed
Systems", in Parallel and Distributed Algorithms, North-Holland, 1989, pages
215 to 226. Because the two papers arrived at the identical data structure by
different routes, the literature commonly calls the construction the
Fidge-Mattern clock, and this entry uses that as a secondary alias.

The vector clock generalizes an earlier, weaker mechanism. Leslie Lamport
introduced the single-integer logical clock, now called the Lamport
timestamp, in "Time, Clocks, and the Ordering of Events in a Distributed
System", Communications of the ACM, volume 21, number 7, July 1978
(https://www.cs.cmu.edu/afs/cs/academic/class/15712-f08/www/lectures/Lamport78lecture.pdf,
verified 2026-08-02). Lamport's scalar clock gives every event in a
distributed system a single number consistent with the happens-before
relation, but a Lamport timestamp is not injective with respect to
concurrency, meaning two events that are genuinely concurrent can still
receive comparable Lamport numbers, and the reader cannot recover from the
number alone whether one event genuinely happened before another or merely
got a larger number by coincidence of scheduling. Fidge and Mattern each set
out to fix that gap by replacing the single integer with a vector of
integers, one slot per process in the system, so that the resulting partial
order over vectors is exactly the causal happens-before order and nothing
more, nothing less. A vector clock therefore does what a Lamport clock
cannot. it lets two processes look at two timestamps and determine with
certainty whether the underlying events are causally ordered or genuinely
concurrent, with no false positives and no false negatives.

The name is sometimes applied loosely in industry documentation to a related
but distinct structure called a version vector, first described by D. Stott
Parker and colleagues for the Locus distributed operating system in "Detection
of Mutual Inconsistency in Distributed Systems", IEEE Transactions on
Software Engineering, volume SE-9, number 3, May 1983. A version vector
tracks one counter per REPLICA of a single piece of DATA, incremented on
writes to that replica, and is used to detect a mismatch between copies of
an object that have drifted apart. A vector clock tracks one counter per
PROCESS in an entire system and is stamped on every EVENT that process
performs, not only writes. The two are isomorphic in their algebra, the
comparison rule is identical, but their scope differs, and dimension 13
returns to this distinction because most production systems that advertise
"vector clocks" for conflict detection are, strictly, using version vectors
over a fixed replica set. This entry follows the common industry usage and
treats version vectors as the storage-layer application of the vector clock
idea, while flagging the terminological looseness plainly here so a reader
is not confused later.

## 2. Problem and context

A distributed system has no single authoritative clock. Each process
(a node, a replica, an actor, a client session) runs its own local clock,
and physical clocks drift relative to one another even with NTP
synchronization, so wall-clock timestamps from two different machines cannot
be trusted to order events correctly, particularly at the millisecond or
microsecond granularity where real conflicts occur. Two updates to the same
piece of data, issued from two different nodes within the same clock-skew
window, can carry physical timestamps in either order regardless of which
one a human observer would call "first".

The concrete situation that creates the need looks like this. A key-value
store replicates a record across three nodes for availability. A client
writes to node A while a network partition has isolated node A from nodes B
and C. A second client, unaware of the first write, writes a different value
to node B during the same partition. When the partition heals, nodes A and B
must reconcile two versions of the same key. A wall-clock comparison answers
the wrong question, because the two writes were concurrent from the system's
point of view, neither one causally preceded the other, and picking "the one
with the later timestamp" (last-write-wins) silently discards one client's
work without ever telling either client that a conflict happened. The
concrete need that makes a vector clock the right tool is precisely this.
the system must distinguish "A happened before B", "B happened before A",
and "A and B are concurrent and both must be preserved or explicitly
merged", and it must do so without relying on synchronized physical clocks
or on a single global sequencer, because a global sequencer is itself a
single point of failure and a latency bottleneck that a partition-tolerant,
available system cannot afford. Compare Eric Brewer's CAP framing, as
formalized by Seth Gilbert and Nancy Lynch in "Brewer's Conjecture and the
Feasibility of Consistent, Available, Partition-Tolerant Web Services", ACM
SIGACT News, volume 33, issue 2, June 2002. a system that chooses
availability under partition needs exactly this kind of causal bookkeeping
to reconcile the split copies that availability makes possible.

## 3. Forces

- **Causal correctness versus space.** Favours correctness. A vector clock
  with N processes costs N integers per timestamp, and every message or
  stored version must carry the whole vector. This is the central cost of
  the pattern and the reason most production systems bound or prune it, see
  dimension 11.
- **Precision versus availability.** Favours availability. The entire point
  of adopting vector clocks in a storage system is to permit concurrent,
  uncoordinated writes during a partition rather than blocking one side, so
  the pattern trades a synchronous consensus step for an asynchronous
  reconciliation step performed later, at read time or during anti-entropy.
- **Decision latency versus data growth.** The comparison of two vectors is
  O(N) and cheap at read time, so latency is not the bottleneck. Storage
  growth is. an unbounded set of participating processes produces an
  unboundedly wide vector, see dimension 11's clock bloat entry.
- **Determinism versus physical time.** Favours determinism. A vector clock
  gives an exact answer to whether A is causally before B with no dependence
  on clock synchronization, at the cost of giving no answer at all to when,
  in wall-clock terms, an event occurred. A vector clock cannot tell an
  operator what time an event occurred, only how it relates causally to
  other events.
- **Simplicity of reasoning versus operational transparency.** Favours
  reasoning correctness, sacrifices operability. A vector of forty
  small integers is not something an operator can eyeball in a log line
  the way a wall-clock timestamp can, so debugging tools and dashboards need
  purpose-built comparison logic, see dimension 16.
- **Client burden versus server simplicity.** In client-driven reconciliation
  designs (Dynamo's approach, see dimension 9), the server stores and
  compares vectors cheaply but pushes the burden of actually MERGING
  divided values back onto the application or the end user, because the
  vector clock alone can detect a conflict but cannot resolve one. semantic
  merge logic is outside its scope, see dimension 4.

## 4. Applicability and non-applicability

Reach for a vector clock when the following hold.

- The system permits concurrent, uncoordinated writes from more than one
  process to the same logical piece of state, and the system must be able
  to detect, after the fact, whether two versions are causally related or
  genuinely concurrent.
- Availability under network partition matters more than serializing every
  write through a single leader or coordinator, so the design already
  accepts eventual consistency, sloppy quorums, or multi-master replication.
- The number of independent writers (nodes, replicas, or actors) is small
  and roughly stable over the system's lifetime, so the vector stays a
  manageable width.
- The application, or a human operator, is prepared to resolve a detected
  conflict, whether automatically through a specific merge function (a
  CRDT, a set union, "keep both and let the client choose") or manually.
- Causal message ordering must be preserved across an asynchronous,
  unreliable network, for example in causally-ordered multicast or in
  distributed debugging and record-replay tooling.

Do NOT reach for a vector clock in these cases, and the reason matters more
than the rule.

- **A single writer per key already holds true.** If every key is owned by
  exactly one primary at a time, as in a leader-based system with
  linearizable writes (a Raft or Paxos-backed store), there is never a
  concurrent write to detect, and the entire mechanism is unearned
  complexity. A simple monotonic version number per key is sufficient
  because there is no partial order to represent, only a total one.
- **Last-write-wins is an acceptable and understood business rule.** If the
  application genuinely does not care which of two concurrent writes wins,
  because the data is a cache, a metric, or a value where staleness is
  tolerable, a physical timestamp with LWW resolution is far cheaper and the
  vector clock's precision buys nothing. Riak's own guidance, and the
  documented history of systems that started with vector clocks and later
  simplified, both support this, see dimension 11.
- **The number of writers is large or unbounded.** A system where clients
  themselves act as independent vector-clock participants, rather than a
  small fixed set of server replicas, produces clock bloat, because the
  vector must carry an entry for every participant that has ever written,
  see the clock bloat failure mode in dimension 11. This is the single most
  cited practical objection to vector clocks in production key-value stores.
- **The application needs wall-clock time, not causal order.** A vector
  clock answers whether A happened before B, never what time A happened. If
  the requirement is an audit trail with real timestamps, a vector clock is
  the wrong tool entirely, though it can be paired with a physical timestamp
  stored alongside it for that separate purpose.
- **A CRDT already resolves the merge without needing explicit causal
  detection.** State-based CRDTs (see the CRDT entry) are designed so that
  merge is commutative, associative, and idempotent, and many of them
  achieve convergence without exposing a vector clock to the application at
  all, folding the causal bookkeeping into the CRDT's own internal state.
  When a CRDT already fits the data type, adding a vector clock on top is
  redundant.
- **Global total order is actually required.** Some cases, for example a
  ledger where transaction order has legal or financial meaning, need a
  single agreed total order, not a partial causal order. Vector clocks
  cannot produce a total order on their own. that requires consensus
  (Paxos, Raft) or a designated sequencer.

## 5. Structure

- **Process (or Replica).** A participant that performs local events and
  exchanges messages with other processes. In a replicated storage system
  this is typically a storage node or a replica; in a distributed
  application it can be a thread, an actor, or a service instance. Each
  process owns exactly one slot in the vector and is the only entity
  permitted to increment that slot.
- **Vector Clock (Timestamp).** An array or map of N non-negative integers,
  one per participating process, where N is the number of processes the
  system is currently tracking. `VC[i]` is process i's own count of events
  it has locally observed to have happened, either its own local events or
  events it learned about transitively through received messages.
- **Local Event.** Any state change a process performs on its own, with no
  message involved. a write, a computation step, an internal transition.
- **Send Event and Receive Event.** The two halves of message-passing
  communication between processes, which are the mechanism by which causal
  knowledge propagates from one process's vector into another's.
- **Merge (Join) Operation.** The pointwise maximum of two vectors, applied
  when a process receives a message and must fold the sender's vector into
  its own knowledge. This is the operation that makes vector clocks a join
  semilattice, a property dimension 13 connects directly to CRDTs.
- **Comparator.** The partial-order relation over vectors. `VC_a <= VC_b` if
  and only if every component of `VC_a` is less than or equal to the
  corresponding component of `VC_b`. `VC_a < VC_b` (strictly happens-before)
  if `VC_a <= VC_b` and the two vectors are not equal. Two vectors are
  concurrent, written `VC_a || VC_b`, if neither `VC_a <= VC_b` nor
  `VC_b <= VC_a` holds, which happens exactly when at least one component of
  `VC_a` exceeds the corresponding component of `VC_b` and at least one
  component of `VC_b` exceeds the corresponding component of `VC_a`.

The relationships. every Process owns one slot of the shared Vector Clock
schema. every Local Event increments the owning process's own slot. every
Send Event attaches a copy of the sender's current vector to the outgoing
message. every Receive Event first increments the receiver's own slot, then
merges in the sender's attached vector via the pointwise maximum. the
Comparator consumes two vectors and returns one of three outcomes, never a
single boolean, which is the structural property that distinguishes a vector
clock from a scalar Lamport clock.

## 6. ASCII structure diagram

```
   +------------------------------------------------------------+
   |                     Vector Clock Schema                    |
   |  index    0        1        2       ...      N-1           |
   |  owner   Proc_0   Proc_1   Proc_2   ...     Proc_N-1        |
   +------------------------------------------------------------+
                 ^          ^          ^                ^
                 |          |          |                |
       each Proc_i owns and may ONLY increment slot i
                 |          |          |                |
   +----------+  |   +----------+  |   +----------+     |
   |  Proc_0  |--+   |  Proc_1  |--+   |  Proc_2  |-----+
   |----------|      |----------|      |----------|
   | local VC |      | local VC |      | local VC |
   | [3,1,0]  |      | [2,5,0]  |      | [0,0,7]  |
   +----------+      +----------+      +----------+
        |                  |                 |
        |   send(msg, VC)  |                 |
        +----------------->|                 |
                            |  on receive     |
                            |  VC[self]++     |
                            |  VC = max(VC,   |
                            |      msg.VC)    |
                            v
                       merged VC carries forward

   Comparator over two stamped vectors A, B.
     A <= B   pointwise    ->  A happened-before-or-equal B
     A <  B   strict       ->  A happened strictly before B
     A || B   incomparable ->  A and B are CONCURRENT
```

## 7. Dynamics

The defining behaviour of a vector clock is the three-rule update algorithm,
identical in Fidge's and Mattern's independent formulations, and the
sequence below traces two processes exchanging one message and then a third
process observing a conflict.

```
Proc_A                 Proc_B                  Proc_C (observer)
VC_A=[0,0,0]           VC_B=[0,0,0]             VC_C=[0,0,0]
  |                       |                          |
  |-- local write x=1 --->|                          |
  |   VC_A[A]++           |                          |
  |   VC_A=[1,0,0]        |                          |
  |                       |                          |
  |-- send(x=1, VC_A) --->|                          |
  |                       |-- receive --             |
  |                       |   VC_B[B]++              |
  |                       |   VC_B = [0,1,0]         |
  |                       |   VC_B = max(VC_B,VC_A)  |
  |                       |   VC_B = [1,1,0]         |
  |                       |                          |
  |-- local write y=2     |                          |
  |   (no message to B)   |-- local write x=2         |
  |   VC_A[A]++           |   VC_B[B]++              |
  |   VC_A=[2,0,0]        |   VC_B=[1,2,0]           |
  |                       |                          |
  |----------------- both versions replicate ------->|
  |                       |                          |
  |                       |    VC_C compares         |
  |                       |    [2,0,0] vs [1,2,0]    |
  |                       |    neither <= the other  |
  |                       |    => CONCURRENT WRITE    |
  |                       |    both versions kept,    |
  |                       |    sibling resolution     |
  |                       |    required at read time  |
```

The three rules, stated precisely, are as follows. First, before executing
any local event, a process increments only its own component of its vector
clock. Second, every outgoing message carries a copy of the sender's vector
clock at the moment of sending. Third, on receiving a message, the receiver
first increments its own component (this event, the receipt itself, is also
a local event), then takes the componentwise maximum of its own vector and
the vector attached to the message, and adopts that maximum as its new
vector. This third rule is the merge step and is what allows causal
knowledge to propagate transitively. process C, which never spoke to process
A directly, still learns that A's event happened before some event C now
knows about, as long as that knowledge reached C through some chain of
messages.

A subtlety worth stating plainly. two events with `VC_a < VC_b` are
GUARANTEED to be causally ordered, but two concurrent-looking events might
still, in physical wall-clock time, have occurred in a particular order that
the vector clock simply does not and cannot record, because no message
carried that information between the two processes. This is by design, not
a defect. the vector clock captures exactly the causal order the system can
prove, no more.

## 8. Implementation variants

**Full vector, one slot per node, fixed membership.** The classical Fidge
and Mattern form. simplest to implement and reason about, correct as long as
the process set is known and stable. Breaks down, or rather grows without
bound, when membership churns, see dimension 11.

**Version vector over a bounded replica set.** The storage-system adaptation
where the "processes" are a small, administratively fixed set of storage
replicas rather than arbitrary clients, and the vector is attached to a
DATA VERSION rather than to every message. This is what Amazon's Dynamo
paper and most Dynamo-derived systems implement, see dimension 9. Bounding
the slot count to the replica set, rather than to every client that ever
wrote, is the single most important production adaptation of the academic
construction.

**Dotted version vector (DVV).** Developed by Nuno Preguica and colleagues
to fix a specific correctness gap in plain version vectors used for
conflict detection. a plain version vector can, under repeated same-node
overwrites without an intervening read, fail to detect a real sibling and
silently drop a concurrent write. The dotted version vector adds a "dot", a
minimal per-event tag identifying the exact write that produced a value, so
that identity survives across merges. Riak KV adopted DVVs as the default
logical clock starting with Riak 2.0, replacing plain vector clocks
(https://docs.riak.com/riak/kv/2.1.1/learn/concepts/causal-context/, verified
2026-08-02). See dimension 9 for the full production account.

**Interval tree clock.** A variant designed by Paulo Almeida, Carlos Baquero
and Victor Fonte specifically to solve dynamic membership. instead of a
fixed array, the clock is represented as a tree that can be split when a
process forks (spawning a new replica) and joined when a process retires,
so the representation size tracks the number of CURRENTLY active
participants rather than the historical total. This directly answers the
clock bloat problem that plain vector clocks cannot solve on their own.

**Bitmapped or compressed vector for sparse membership.** In practice most
implementations store the vector as a sparse map from process identifier to
counter rather than a dense array, since most processes have a zero entry
for most other processes' clocks at any given moment, which is a pure space
optimization with no change to the algebra.

**Client-side versus server-side vector clocks.** Two placement choices
exist for who computes and carries the vector. server-side, where storage
nodes maintain and merge vectors transparently and the client sees only an
opaque token to echo back on the next write (this is Dynamo's and Riak's
approach), versus client-side, where an SDK exposes the vector directly and
the application code performs the merge logic itself. Server-side placement
is dominant in practice because it keeps the causal bookkeeping out of
application code and lets the storage layer evolve its internal
representation (for example, moving from vector clocks to dotted version
vectors) without breaking client contracts.

## 9. Known production uses

**Amazon Dynamo, the 2007 SOSP paper.** Every object version in Dynamo is
stamped by the replica that accepted the write with a vector clock, a list
of (node, counter) pairs. On a read, Dynamo compares the vector clocks of
all returned versions. if one version's clock is a strict ancestor of
another's, the older is discarded automatically; if the clocks are
incomparable, both ("sibling") versions are returned to the client for
application-level reconciliation. Giuseppe DeCandia, Deniz Hastorun, Madan
Jampani, Gunavardhan Kakulapati, Avinash Lakshman, Alex Pilchin, Swaminathan
Sivasubramanian, Peter Vosshall, Werner Vogels, "Dynamo. Amazon's Highly
Available Key-value Store", Proceedings of the 21st ACM Symposium on
Operating Systems Principles, Stevenson WA, October 2007,
https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf,
verified 2026-08-02. Dynamo's own authors record having observed clock
growth as a real operational problem and describe truncating the oldest
(node, counter) pairs by timestamp once a vector exceeds a configured
threshold, trading a small risk of incorrect reconciliation for bounded
storage, a trade-off returned to in dimension 11.

**Riak KV, pre-2.0 versus 2.0 and later.** Riak, built by Basho and directly
inspired by the Dynamo paper, used plain vector clocks (called "vclocks" in
Riak's own documentation) as its sole causal-context mechanism through the
1.x line. Starting with Riak 2.0, Basho replaced the default mechanism with
dotted version vectors, citing a specific correctness defect in plain
vector clocks under Riak's own multi-datacenter and sibling-resolution
model, where repeated writes without a read in between could allow a
concurrent update's causal history to be silently overwritten. Basho, "Riak
KV Causal Context" documentation,
https://docs.riak.com/riak/kv/2.1.1/learn/concepts/causal-context/, verified
2026-08-02; and Basho's own engineering account, "Vector Clocks Revisited
Part 2. Dotted Version Vectors",
https://riak.com/posts/technical/vector-clocks-revisited-part-2-dotted-version-vectors/index.html,
verified 2026-08-02. Riak KV kept the ability to switch a bucket type back
to plain vector clocks for backward compatibility, but DVVs became the
recommended and default logical clock.

**Voldemort, LinkedIn's distributed key-value store.** Voldemort, built at
LinkedIn and heavily modeled on the Dynamo paper's design, uses vector
clocks as its versioning mechanism to detect stale reads and to support a
"versioned put" interface where a caller can supply a vector clock obtained
from a prior read, so that concurrent updates to the same key are exposed to
the client as siblings requiring explicit resolution, the same pattern
Dynamo established. Voldemort source repository,
`src/java/voldemort/versioning/VectorClock.java`,
https://github.com/voldemort/voldemort, verified 2026-08-18, the
VectorClock class implementing the versioning scheme, and the project
README confirming data items are versioned to maximize integrity across
node failures without compromising availability, the same tradeoff
Dynamo established.

**Apache Cassandra, early history only, superseded.** Cassandra's original
design, described in Avinash Lakshman and Prashant Malik, "Cassandra. A
Decentralized Structured Storage System", ACM SIGOPS Operating Systems
Review, volume 44, issue 2, April 2010, was explicitly modeled on Dynamo's
architecture for partitioning and replication, but Cassandra's authors chose
timestamp-based last-write-wins conflict resolution rather than vector
clocks for the reason discussed in dimension 4, avoiding the
client-visible-sibling burden vector clocks impose. Cassandra is noted here
as a documented example of a Dynamo-lineage system that deliberately did NOT
adopt vector clocks, which is itself informative for dimension 12's
trade-off comparison, not as a positive production use.

## 10. Consequences

Positive.

- Detects true concurrency between writes with no false positives, which no
  physical-timestamp scheme can guarantee under clock skew.
- Requires no synchronized global clock and no single coordinating
  sequencer, so it composes naturally with partition-tolerant, multi-master
  replication designs that must remain available during a network split.
- The comparator is a pure, cheap, local computation over two vectors, with
  no network round trip needed to determine causal relationship.
- Forms a join semilattice under the pointwise-maximum merge operation,
  which is exactly the algebraic structure state-based CRDTs are built on,
  so a system already using vector clocks has a natural path toward CRDT
  adoption for specific data types.
- Makes concurrency visible to the application rather than silently
  resolving it, which is a benefit when data loss from a hidden
  last-write-wins decision is unacceptable.

Negative.

- Space cost grows linearly with the number of distinct writers the system
  tracks, and in a design where clients rather than a fixed replica set act
  as vector-clock participants, this growth is effectively unbounded, see
  the clock bloat failure mode.
- Detecting a conflict is not the same as resolving one. the pattern pushes
  the actual merge logic to the application or to a human, which is real
  engineering work the vector clock itself does nothing to reduce.
- Every write and every replicated version must carry the full vector,
  which is pure overhead on the wire and on disk compared to a single
  scalar timestamp or a single monotonic counter.
- Wrong mental model risk. engineers who have only seen scalar version
  numbers frequently misread a vector clock as a single "version", and
  write comparison code that treats incomparability as an error rather than
  as the expected, valid outcome of a concurrent write.
- Does not by itself give a total order, so it cannot answer which of two
  concurrent writes happened first in wall-clock terms, only that neither
  is a causal descendant of the other.

## 11. Failure modes and misuse

**Clock bloat from unbounded participant growth.** Symptom. Stored object
metadata grows steadily over the system's lifetime even for keys that are
rarely written, and eventually a single object's vector clock metadata
exceeds the size of the object's actual payload. Cause. The system attaches
a vector clock entry per CLIENT or per ephemeral process rather than per
fixed replica, so every new client instance, container restart, or deploy
adds a permanent new slot that is never retired. This is the most widely
documented practical objection to vector clocks and the specific problem
that motivated Riak's move to dotted version vectors and motivated Dynamo's
own truncation heuristic. Fix. Scope vector clock participants to a small,
administratively bounded replica set (the version-vector variant from
dimension 8) rather than to clients; where dynamic membership is
unavoidable, adopt interval tree clocks or a comparable structure designed
to shrink when a participant retires.

**Sibling explosion with no reconciliation policy.** Symptom. Reads return
an ever-growing list of "sibling" versions for a hot key, latency on that
key degrades, and eventually reads start timing out or returning errors
because the reconciliation payload is too large to transmit. Cause. The
application never resolves the concurrent siblings the vector clock
correctly detected; it only appends new writes, so unresolved conflicts
accumulate indefinitely. Fix. Enforce a read-before-write pattern so every
write includes the vector clock context from a prior read (this is how
Dynamo's "versioned put" API and Voldemort's client library are designed to
be used), and implement an explicit merge function, semantic where
possible, or a documented last-write-wins fallback with a bounded sibling
count where not.

**Truncation applied silently, without informing the application.** Symptom.
An old-but-not-ancestor write occasionally reappears as if newer, or a
conflict that should have been detected is missed entirely, and this only
shows up rarely, under specific replay or replica-recovery scenarios that
are hard to reproduce. Cause. A system truncated the vector clock (dropped
old entries to bound its size, as Dynamo's paper itself describes) without
a mechanism to guarantee the truncated entries were no longer relevant,
introducing a small but real correctness gap in exchange for bounded
storage. Fix. If truncation is necessary, document the correctness trade-
off explicitly, bias truncation toward the least-recently-updated entries
as Dynamo does, and monitor for the specific symptom (a version accepted as
an ancestor that should have been flagged concurrent) rather than assuming
truncation is free.

**Comparator treated as returning a boolean.** Symptom. Code that calls a
"newer than" check on two vector clocks and branches on true or false,
which compiles and runs, but silently discards one of two genuinely
concurrent writes because the comparator implementation defaults to
"return false, meaning not newer, so keep the existing value" whenever the
vectors are actually incomparable. Cause. The comparator has three possible
outcomes (before, after, concurrent) but was implemented or consumed as if
it had only two. Fix. Make the comparator return an explicit three-state
result (an enum, not a boolean), and write a test asserting that two
crafted, genuinely incomparable vectors are reported as concurrent rather
than silently resolved either way.

**Merge applied on send instead of receive, or applied to the wrong copy.**
Symptom. Causal ordering appears to work in single-hop testing but breaks
under multi-hop message relay. process C, which learned about A's event only
through B, fails to recognize the causal relationship. Cause. The
implementation merges the sender's vector into the receiver's vector at the
point of sending rather than at the point of receiving, or merges into a
scratch copy that is discarded rather than into the process's persistent
vector state. Fix. Confirm the merge (rule three in dimension 7) happens
exactly once, on receipt, against the process's actual persisted vector, and
add a three-hop integration test (A sends to B, B sends to C with no direct
A-to-C link) specifically because it is the case single-hop tests miss.

**Vector clock confused with, or substituted for, a version vector without
adjusting the scope.** Symptom. Code written against academic Fidge or
Mattern pseudocode, which stamps every EVENT, is applied directly to a
storage system that only needs to stamp WRITES, producing far more vector
churn than the storage use case requires and complicating client code that
now has to reason about read events too. Cause. Treating the two closely
related but distinct constructions (dimension 1) as interchangeable without
adapting the scope. Fix. For a storage system, deliberately narrow the
scope to the version-vector variant, one entry per replica, incremented
only on accepted writes, not on every local operation.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Vector Clock | Lamport (scalar) timestamp | Physical timestamp + LWW | Dotted Version Vector | Consensus-ordered write (Raft or Paxos) | CRDT (state-based) |
|---|---|---|---|---|---|---|
| Detects true concurrency | Yes, exactly | No, gives a total order that hides concurrency | No, picks a winner and discards the loser silently | Yes, exactly, plus fixes the same-node overwrite gap | Not applicable, there is no concurrency by construction | Not exposed directly; folded into the merge function |
| Requires synchronized clocks | No | No | Yes, and is sensitive to clock skew | No | No, but requires a leader or quorum round trip | No |
| Space per version | O(number of writers) | O(1), one integer | O(1), one timestamp | O(number of writers) plus one dot | O(1), one log index | Varies by CRDT, often larger than a scalar |
| Availability under partition | High, both sides can accept writes | High | High | High | Low, the minority partition cannot commit writes | High |
| Who resolves a detected conflict | Application or human, explicitly | Not applicable, no conflict is exposed | Nobody, the loser is silently gone | Application or human, explicitly | Not applicable | The CRDT's own merge function, automatically |
| Handles dynamic membership well | Poorly, without a variant like interval tree clocks | Well, no per-process state | Well, no per-process state | Poorly, same limitation as plain vector clocks | Well, membership changes are themselves consensus operations | Depends on the specific CRDT |
| Operational transparency | Low, needs custom tooling | Medium | High, a timestamp is human-readable | Low, same as vector clocks | Medium to high, a log is auditable | Low to medium |

Reading of the table. a vector clock or its dotted variant is the correct
choice exactly when the system needs to detect concurrency precisely and is
willing to push resolution to the application in exchange for availability
during a partition. A Lamport scalar clock is cheaper but answers a weaker
question and should not be reached for when the actual requirement is
concurrency detection rather than a total order. Physical timestamps with
last-write-wins are the cheapest and most operationally legible option and
are correct when silent data loss on genuine conflict is an acceptable
trade, which Cassandra's designers judged to be true for their target
workloads. Consensus-based ordering removes the need for any of this
machinery by removing concurrency itself, at the cost of availability during
a partition. CRDTs move the resolution logic into the data type itself,
trading vector-clock-style explicit conflict exposure for automatic,
type-specific convergence.

## 13. Related and incompatible patterns

- **Lamport Timestamp.** The direct ancestor. A vector clock is what results
  from strengthening a Lamport clock so that the induced order captures
  concurrency exactly rather than approximately. Any system already using
  Lamport clocks and finding that it needs to detect concurrency, not merely
  produce a consistent total order, is a candidate to upgrade to vector
  clocks.
- **Version Vector.** The storage-layer specialization discussed throughout
  this entry, scoped to a fixed replica set and stamped on writes rather
  than on every event. In practice this is what most production key-value
  stores implement under the "vector clock" name.
- **Dotted Version Vector.** A refinement of the version vector that fixes a
  specific correctness gap (dimension 8), and the pattern most current
  Dynamo-lineage systems have migrated to in place of plain vector clocks.
- **Interval Tree Clock.** A refinement aimed at the dynamic-membership
  weakness that neither plain vector clocks nor dotted version vectors
  solve, allowing the representation to grow and shrink with the active
  participant set rather than only growing.
- **CRDT (Conflict-free Replicated Data Type).** Composes closely. the
  pointwise-maximum merge that vector clocks use is the same join-semilattice
  operation state-based CRDTs are defined on, and several CRDT
  implementations (for example an observed-remove set) use a version-vector-
  like structure internally to track which replica removed which element.
  Where a suitable CRDT exists for the data type in question, it can
  eliminate the need for the application to write its own vector-clock-based
  conflict resolution logic.
- **Gossip Protocol.** Frequently the transport that carries vector clocks
  between replicas during anti-entropy repair in a Dynamo-style system.
  gossip propagates both the data and its causal metadata so that
  out-of-sync replicas eventually converge on a shared, merged view.
- **Read Repair.** The operational technique, used alongside vector clocks in
  Dynamo and Riak, of resolving detected staleness at read time by writing
  the reconciled or newer version back to the lagging replica, so that
  conflicts exposed by the vector clock comparator get healed
  incrementally rather than requiring a separate batch process.
- **Consensus protocols (Raft, Paxos, Multi-Paxos).** Incompatible in intent
  rather than in mechanism. consensus protocols exist to PREVENT concurrent
  writes to the same piece of state by serializing them through a leader or
  a quorum decision, so a system built around consensus has no concurrent
  writes for a vector clock to detect. Combining the two on the same data
  path is redundant, though a single system can legitimately use consensus
  for some state (cluster membership, configuration) and vector clocks for
  other state (user data under a multi-master model), as several production
  systems do.
- **Last-Write-Wins (physical timestamp resolution).** A direct alternative
  for the same problem, not a composing pattern. a system chooses one or the
  other for a given class of data, as Cassandra's designers explicitly chose
  LWW over the vector clocks used by its Dynamo-lineage siblings.

## 14. Refactoring path in and out

Introducing vector clocks into a replicated system that currently uses
physical-timestamp last-write-wins, or that currently has no conflict
detection at all because it has never needed to handle concurrent writes.

1. Confirm the system genuinely permits concurrent writes to the same
   logical key from more than one node, without a single coordinator
   serializing them. If a leader already serializes every write to a key,
   stop here, there is nothing to detect.
2. Identify the fixed, bounded set of writers that should participate in
   the vector (replicas, not arbitrary clients), per the version-vector
   variant in dimension 8. Enumerating this set explicitly, rather than
   letting it grow implicitly, is the step that prevents clock bloat later.
3. Extend the stored record format to carry a vector alongside the value,
   defaulting every existing record's vector to the zero vector or to a
   single-entry vector recording an unknown prior history, so the migration
   does not require rewriting historical data before the change can ship.
4. Change the write path so that every accepted write increments the
   accepting replica's own slot and, where the write includes a client-
   supplied token (the vector read on a prior GET), merges that value in
   before incrementing, exactly as Dynamo's "versioned put" is specified.
5. Change the read path to fetch from a quorum, compare the returned
   vectors with the three-state comparator, discard any version that is a
   strict causal ancestor of another, and expose the remaining siblings, if
   more than one, to the caller rather than silently picking one.
6. Add explicit, tested reconciliation logic at the point where siblings are
   exposed, whether automatic (a specific merge function or a CRDT) or
   manual (return both to the end user).
7. Add the truncation or dotted-version-vector upgrade from dimension 8 or
   11 before deploying at a scale where clock bloat is a realistic risk,
   rather than discovering the problem after metadata size becomes a
   production incident.

Removing the pattern when it stops earning its place. Signals include a
sibling rate near zero in production telemetry over a sustained period,
meaning concurrent writes to the same key almost never happen in practice,
or a decision to move the data path behind a single leader for other
reasons (stronger consistency requirements elsewhere in the system).

1. Confirm from real telemetry, not from intuition, that the observed
   sibling rate is genuinely negligible, using the counter from dimension
   16.
2. If moving to a single-leader model, introduce the leader and route all
   writes for the affected keys through it, which removes the possibility
   of concurrent writes at the source; the vector clock field becomes
   provably always a chain, never a fork, and can then be replaced with a
   monotonic integer.
3. If staying multi-master but accepting last-write-wins, replace the vector
   comparator with a physical-timestamp comparison, remove the sibling
   exposure from the read path, and document plainly, in the API and in
   the team's own operational runbook, that a future concurrent write will
   now be silently resolved rather than shown to the caller, since that is
   a real behavioural change the team must consciously accept.
4. Delete the vector clock field from the record format only after a
   migration window has passed and no client code still expects it,
   following the same staged-removal discipline as any other stored-field
   deprecation.

## 15. Testing and verification

Easier because of the pattern.

- Causal ordering claims become directly assertable. a test can construct
  two vectors by hand and assert the comparator's exact three-state
  outcome, with no timing, sleeping, or wall-clock mocking required, unlike
  testing physical-timestamp-based ordering.
- The merge operation is a pure function (pointwise maximum) and is trivial
  to property-test. commutativity, associativity, and idempotence of merge
  are exactly the join-semilattice laws and can be checked directly with
  randomly generated vectors.
- Multi-hop causal propagation (the A-to-B-to-C scenario from dimension 11)
  is fully deterministic given a fixed message order, so it can be tested
  without any real network, using an in-process simulated message bus that
  controls delivery order explicitly.

Harder because of the pattern.

- End-to-end tests that must produce a genuine sibling require deliberately
  simulating a partition or deliberately interleaving two writers before
  either has seen the other's vector, which needs either fault-injection
  infrastructure or careful manual sequencing in the test, rather than
  simply calling two functions in a row.
- Regression tests for the sibling-explosion failure mode (dimension 11)
  require sustained, repeated concurrent writes with no intervening
  reconciliation, which is a longer-running scenario than a typical unit
  test and belongs in an integration or soak-test suite instead.

Techniques that apply.

- **Property-based testing of the comparator and merge.** Generate random
  vectors of a fixed width and assert the mathematical laws directly.
  reflexivity and antisymmetry of the partial order, commutativity and
  idempotence of merge, and the specific claim that `merge(a, b) >= a` and
  `merge(a, b) >= b` for every generated pair.
- **A deterministic, in-process message-bus test double** that lets a test
  control exact delivery order of send and receive events across three or
  more simulated processes, so the multi-hop transitivity case from
  dimension 11 can be exercised reliably rather than depending on real
  network timing.
- **A fault-injection or partition-simulation test rig** at the integration
  level, deliberately isolating two nodes, sending one write to each, then
  healing the partition and asserting that both writes are exposed as
  siblings at read time, which is the single most important behaviour a
  vector-clock-based system must get right and the one hardest to exercise
  with a plain unit test.
- **A metamorphic test on truncation**, where a full-fidelity vector and a
  truncated version of the same vector are compared against the same
  reference vector, asserting that truncation only ever produces a
  false "not concurrent" verdict under the documented, accepted trade-off,
  never a false "concurrent" verdict where the untruncated comparison would
  have said "ancestor".

## 16. Observability signals

What to record.

- A counter of sibling (unresolved concurrent version) detections per key
  or per key class, since this is the primary signal of how often real
  conflicts are occurring in production, and is the number dimension 14
  step 1 needs before any decision to remove the pattern.
- A gauge or histogram of vector clock width, the number of populated
  entries in a stored vector, tracked over time, because steady growth in
  this number with no corresponding growth in the actual replica count is
  the direct signal of the clock bloat failure mode.
- The size in bytes of the vector clock metadata relative to the size of
  the value it is attached to, which turns clock bloat from an abstract
  concern into a concrete, alertable ratio.
- A counter of truncation events, if truncation is enabled, so operators
  can see how often the correctness trade-off from dimension 11 is
  actually being exercised rather than assuming it is rare.
- On the write path, latency of the merge and comparator operations,
  though these are typically negligible (microseconds for a vector of
  reasonable width) and mainly useful as a sanity check that the width has
  not grown so large as to make an O(N) comparison itself a bottleneck.

A healthy instance on a dashboard. the sibling detection counter shows a
low, roughly stable rate consistent with the system's actual concurrent-
write workload, and every detected sibling is followed, within a bounded
time window, by a merge or resolution event, so the sibling count does not
accumulate. Vector width tracks the administratively configured replica
count and stays flat.

A failing instance. vector width climbs steadily with no plateau, which is
clock bloat in progress and typically traces back to a design where clients
rather than replicas are participating in the vector. Sibling detections
climb without a matching rate of resolutions, which is the sibling
explosion failure mode and usually means a client library is not correctly
including prior read context on writes. Truncation events climb sharply
after being rare, which signals the vector clock metadata has begun growing
faster than the truncation threshold accounts for and the correctness
trade-off is being exercised far more than the original design assumed.

## 17. Security and privacy implications

Vector clocks are close to silent on confidentiality. the vector itself
carries only integers and replica or process identifiers, not application
data, so it does not by itself expose sensitive content. Three genuine,
narrower implications are worth naming precisely rather than inventing a
broader concern.

**Process or replica identifiers as metadata leakage.** If the slots in the
vector are keyed by a descriptive identifier, a hostname, a datacenter code,
or a client session identifier rather than an opaque replica index, the
vector clock attached to a piece of stored data can leak topology
information (which nodes have touched this record, roughly how many
distinct clients wrote to it) to anyone who can read the record's metadata.
Where this matters, key the vector by an opaque, rotated internal identifier
rather than by a directly descriptive one, and treat the vector as part of
the record's access-control boundary, not as harmless bookkeeping exempt
from it.

**Denial of service through vector clock inflation.** Because vector width
grows with the number of distinct participants a system tracks, a design
where an ATTACKER-INFLUENCED value (for example, a client-visible session
or device identifier used directly as a vector slot key) can be added
without bound gives an attacker a cheap way to inflate stored metadata size
across many records, degrading storage and network efficiency system-wide.
This is the clock bloat failure mode (dimension 11) reframed as an
adversarial concern rather than an organic one, and the same fix applies.
bound participation to a small, administratively controlled set, never to
an externally supplied identifier directly.

**Causal metadata as a side channel in multi-tenant systems.** In a system
where the same vector-clock infrastructure is shared across tenants, a
carefully timed sequence of reads and writes can, in principle, allow one
tenant to infer information about another tenant's write activity by
observing changes in shared counters or shared replica state, if isolation
between tenants is not otherwise enforced at a layer below the vector clock.
This is a general multi-tenant isolation concern, not specific to vector
clocks, and the vector clock component of it is narrow. do not rely on the
vector clock's opacity as an isolation boundary; enforce tenant isolation at
the storage and access-control layer independently.

On privacy specifically, the pattern is neutral. it stores no personal data
of its own. any privacy obligation attaches to the underlying record the
vector clock is stamped on, and standard data-retention and access-control
rules for that record should be applied uniformly, including to the vector
clock field itself when it is retained after the record's primary value has
been deleted, since a stale vector clock can itself be a small residual
trace of activity that a strict deletion policy should also clear.

## 18. References

1. Colin J. Fidge. "Timestamps in Message-Passing Systems That Preserve the
   Partial Ordering". Proceedings of the 11th Australian Computer Science
   Conference, 1988, pages 56 to 66.
   https://www.semanticscholar.org/paper/Timestamps-in-Message-Passing-Systems-That-Preserve-Fidge/e706b8ae2952740cb95c0182c4c44b0d11cc54c1
   Verified 2026-08-02. Source of the independent original algorithm and the
   Fidge attribution in dimension 1.
2. Friedemann Mattern. "Virtual Time and Global States of Distributed
   Systems". In Parallel and Distributed Algorithms, North-Holland, 1989,
   pages 215 to 226. Source of the independent "vector time" formulation
   and the Mattern attribution in dimension 1, confirmed via publication
   record at https://www.researchgate.net/publication/2949837_Virtual_Time_and_Global_States_of_Distributed_Systems
   verified 2026-08-02.
3. Leslie Lamport. "Time, Clocks, and the Ordering of Events in a
   Distributed System". Communications of the ACM, volume 21, number 7,
   July 1978.
   https://www.cs.cmu.edu/afs/cs/academic/class/15712-f08/www/lectures/Lamport78lecture.pdf
   Verified 2026-08-02. Source of the antecedent Lamport scalar clock and
   the happens-before relation discussed in dimension 1 and dimension 2.
4. D. Stott Parker Jr. et al. "Detection of Mutual Inconsistency in
   Distributed Systems". IEEE Transactions on Software Engineering, volume
   SE-9, number 3, May 1983. Source of the original version vector
   construction distinguished from the vector clock in dimension 1.
5. Giuseppe DeCandia, Deniz Hastorun, Madan Jampani, Gunavardhan Kakulapati,
   Avinash Lakshman, Alex Pilchin, Swaminathan Sivasubramanian, Peter
   Vosshall, Werner Vogels. "Dynamo. Amazon's Highly Available Key-value
   Store". Proceedings of the 21st ACM Symposium on Operating Systems
   Principles, Stevenson WA, October 2007.
   https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf
   Verified 2026-08-02. Source of the Dynamo production use in dimension 9
   and the truncation trade-off discussed in dimension 11.
6. Basho Technologies. "Riak KV. Causal Context" documentation.
   https://docs.riak.com/riak/kv/2.1.1/learn/concepts/causal-context/
   Verified 2026-08-02. Source of the Riak vector clock to dotted version
   vector migration in dimension 8 and dimension 9.
7. Basho Technologies engineering blog. "Vector Clocks Revisited Part 2.
   Dotted Version Vectors".
   https://riak.com/posts/technical/vector-clocks-revisited-part-2-dotted-version-vectors/index.html
   Verified 2026-08-02. Source of the specific correctness defect in plain
   vector clocks that motivated the dotted version vector, dimension 8 and
   dimension 9.
8. Voldemort source repository. `VectorClock.java`.
   https://github.com/voldemort/voldemort
   Verified 2026-08-18. Source of the Voldemort production use in
   dimension 9.
9. Avinash Lakshman, Prashant Malik. "Cassandra. A Decentralized Structured
   Storage System". ACM SIGOPS Operating Systems Review, volume 44, issue
   2, April 2010. Source of Cassandra's documented Dynamo lineage and its
   deliberate choice of last-write-wins over vector clocks, referenced in
   dimension 9 and dimension 12.
10. Seth Gilbert, Nancy Lynch. "Brewer's Conjecture and the Feasibility of
    Consistent, Available, Partition-Tolerant Web Services". ACM SIGACT
    News, volume 33, issue 2, June 2002. Source of the CAP framing used in
    dimension 2 to motivate why availability-preserving conflict detection
    is needed at all.

## Code examples

Three languages chosen for genuinely different idiomatic shapes. Go, because
its map type and small structs make the classical Fidge-Mattern algorithm
read almost exactly like the mathematical definition, and because several
real Dynamo-lineage systems are implemented in languages with a similarly
direct mapping. Python, because dictionaries make the sparse-vector
optimization from dimension 8 natural to express. Rust, because its
ownership model forces an explicit, correct answer to who owns the merge,
which is easy to get subtly wrong in a garbage-collected language, and
directly relevant to the failure mode in dimension 11 about merging into
the wrong copy.

### Go

```go
package main

import "fmt"

type VectorClock map[string]int

type Ordering int

const (
	Before Ordering = iota
	After
	Equal
	Concurrent
)

func (vc VectorClock) copy() VectorClock {
	out := make(VectorClock, len(vc))
	for k, v := range vc {
		out[k] = v
	}
	return out
}

func (vc VectorClock) Tick(process string) VectorClock {
	out := vc.copy()
	out[process] = out[process] + 1
	return out
}

func (vc VectorClock) Merge(other VectorClock) VectorClock {
	out := vc.copy()
	for k, v := range other {
		if v > out[k] {
			out[k] = v
		}
	}
	return out
}

func Compare(a, b VectorClock) Ordering {
	aLessOrEq, bLessOrEq := true, true
	keys := make(map[string]bool)
	for k := range a {
		keys[k] = true
	}
	for k := range b {
		keys[k] = true
	}
	for k := range keys {
		if a[k] > b[k] {
			bLessOrEq = false
		}
		if b[k] > a[k] {
			aLessOrEq = false
		}
	}
	switch {
	case aLessOrEq && bLessOrEq:
		return Equal
	case aLessOrEq:
		return Before
	case bLessOrEq:
		return After
	default:
		return Concurrent
	}
}

func main() {
	a := VectorClock{}.Tick("nodeA")
	msg := a.copy()
	b := VectorClock{}.Tick("nodeB").Merge(msg).Tick("nodeB")
	a2 := a.Tick("nodeA")
	fmt.Println(Compare(a2, b))
}
```

### Python

```python
from dataclasses import dataclass, field
from enum import Enum, auto


class Ordering(Enum):
    BEFORE = auto()
    AFTER = auto()
    EQUAL = auto()
    CONCURRENT = auto()


@dataclass(frozen=True)
class VectorClock:
    counts: dict[str, int] = field(default_factory=dict)

    def tick(self, process: str) -> "VectorClock":
        new_counts = dict(self.counts)
        new_counts[process] = new_counts.get(process, 0) + 1
        return VectorClock(new_counts)

    def merge(self, other: "VectorClock") -> "VectorClock":
        new_counts = dict(self.counts)
        for proc, count in other.counts.items():
            if count > new_counts.get(proc, 0):
                new_counts[proc] = count
        return VectorClock(new_counts)

    def compare(self, other: "VectorClock") -> Ordering:
        keys = set(self.counts) | set(other.counts)
        a_le_b = all(self.counts.get(k, 0) <= other.counts.get(k, 0) for k in keys)
        b_le_a = all(other.counts.get(k, 0) <= self.counts.get(k, 0) for k in keys)
        if a_le_b and b_le_a:
            return Ordering.EQUAL
        if a_le_b:
            return Ordering.BEFORE
        if b_le_a:
            return Ordering.AFTER
        return Ordering.CONCURRENT


if __name__ == "__main__":
    a = VectorClock().tick("nodeA")
    msg_from_a = a
    b = VectorClock().tick("nodeB").merge(msg_from_a).tick("nodeB")
    a2 = a.tick("nodeA")
    print(a2.compare(b))
```

### Rust

```rust
use std::collections::HashMap;
use std::cmp::Ordering as StdOrdering;

#[derive(Debug, Clone, PartialEq, Eq)]
struct VectorClock {
    counts: HashMap<String, u64>,
}

#[derive(Debug, PartialEq, Eq)]
enum Ordering {
    Before,
    After,
    Equal,
    Concurrent,
}

impl VectorClock {
    fn new() -> Self {
        VectorClock { counts: HashMap::new() }
    }

    fn tick(&self, process: &str) -> VectorClock {
        let mut counts = self.counts.clone();
        *counts.entry(process.to_string()).or_insert(0) += 1;
        VectorClock { counts }
    }

    fn merge(&self, other: &VectorClock) -> VectorClock {
        let mut counts = self.counts.clone();
        for (proc, &count) in other.counts.iter() {
            let entry = counts.entry(proc.clone()).or_insert(0);
            if count > *entry {
                *entry = count;
            }
        }
        VectorClock { counts }
    }

    fn compare(&self, other: &VectorClock) -> Ordering {
        let keys: std::collections::HashSet<&String> =
            self.counts.keys().chain(other.counts.keys()).collect();
        let mut a_le_b = true;
        let mut b_le_a = true;
        for k in keys {
            let a_val = *self.counts.get(k).unwrap_or(&0);
            let b_val = *other.counts.get(k).unwrap_or(&0);
            match a_val.cmp(&b_val) {
                StdOrdering::Greater => b_le_a = false,
                StdOrdering::Less => a_le_b = false,
                StdOrdering::Equal => {}
            }
        }
        match (a_le_b, b_le_a) {
            (true, true) => Ordering::Equal,
            (true, false) => Ordering::Before,
            (false, true) => Ordering::After,
            (false, false) => Ordering::Concurrent,
        }
    }
}

fn main() {
    let a = VectorClock::new().tick("nodeA");
    let msg_from_a = a.clone();
    let b = VectorClock::new().tick("nodeB").merge(&msg_from_a).tick("nodeB");
    let a2 = a.tick("nodeA");
    println!("{:?}", a2.compare(&b));
}
```
