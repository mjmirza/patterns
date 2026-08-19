---
name: CRDT
slug: crdt
family: 12-data-storage
category: Data and Storage
aliases: [Conflict-free Replicated Data Type, Convergent Replicated Data Type, Commutative Replicated Data Type]
first_described: "Shapiro, Preguica, Baquero, Zawirski 2011"
maturity: established
related: [event-sourcing, vector-clocks, eventual-consistency, gossip-protocol, operational-transformation]
incompatible_with: [strong-consistency-linearizability]
verified: 2026-08-02
---

# CRDT

## 1. Name, aliases, and lineage

The canonical name is CRDT, an acronym that carries two accepted expansions
depending on which formal property is being emphasized. Conflict-free
Replicated Data Type is the more common expansion in product documentation.
Convergent Replicated Data Type and Commutative Replicated Data Type are the
two precise variants defined in the original paper, state-based and
operation-based respectively, and the acronym CRDT deliberately covers both
without committing to one.

The concept was formally named and defined by Marc Shapiro, Nuno Preguica,
Carlos Baquero, and Marek Zawirski in "Conflict-Free Replicated Data Types,"
published in Stabilization, Safety, and Security of Distributed Systems
(Lecture Notes in Computer Science, volume 6976), pages 386 to 400, 2011
(publication details verified against the Wikipedia summary of the paper,
https://en.wikipedia.org/wiki/Conflict-free_replicated_data_type, verified
2026-08-02). The same group of authors also circulated a longer INRIA
INRIA research report the same year, covering the full catalog of convergent
and commutative data type constructions, which is the document most
implementers actually cite for the formal proofs, because the conference
paper itself only summarizes them.

The idea predates the name. Distributed systems researchers had built
individual convergent counters and sets since the 1980s, but nobody had
articulated the general design rule that unifies them, which is why the 2011
paper is treated as the founding reference rather than a survey of prior art.
The name itself is sometimes used loosely, where people say "a CRDT" to mean
any operation that commutes, without the formal convergence proof the term
requires. This entry uses CRDT strictly in the Shapiro et al. sense, a data
type with a mathematically proven convergence guarantee under concurrent,
unordered, possibly duplicated delivery.

## 2. Problem and context

A system replicates the same logical data across more than one node, and more
than one node accepts writes without first coordinating with the others. This
happens for three distinct reasons a reader should be able to recognize in
their own architecture. Geographic distribution, where round trips to a
single leader cost too much latency for interactive use. Offline-first client
software, where a device must accept edits with no network connection at
all. Peer-to-peer collaboration, where there is no server in the write path
by design.

In every one of these situations, two replicas can each accept a write for
the same logical object before either replica has heard from the other. The
system must then decide what happens when those two histories are merged
back together. The traditional answer, requiring a single writer or a
distributed lock before any write is accepted, throws away the latency and
availability the architecture was chosen for in the first place. The
traditional fallback, last-write-wins on a wall clock timestamp, silently
discards one of the two concurrent edits, which is unacceptable when both
edits carry real user intent, for example two collaborators each adding a
different item to a shared shopping list.

CRDTs exist for exactly this problem. Replicas must accept local writes
immediately, without coordination, and later reconcile with any other
replica's writes, in any order, with any number of duplicate deliveries, and
still reach the same final state everywhere, without losing either
concurrent edit and without a human resolving a conflict by hand.

## 3. Forces

Availability versus coordination. A CRDT trades the coordination a strongly
consistent system pays for on every write for a merge function paid once per
convergence. This is the central force the pattern resolves, and it only
makes sense in a system that has already decided availability during a
partition matters more than a single global order of operations, which is a
value judgment CAP theorem framings force on the architect before CRDTs are
even considered.

Memory and bandwidth versus merge simplicity. State-based CRDTs (CvRDTs)
merge by comparing and combining entire replica states, which makes the
merge function trivially idempotent and commutative at the cost of
transmitting or storing the whole state, or a delta of it, on every
synchronization. Operation-based CRDTs (CmRDTs) transmit small operations
instead, which is far cheaper over the wire, but require a reliable causal
broadcast layer underneath, which is a real piece of infrastructure the
state-based variant does not need. This is a genuine implementation cost
trade, not a free choice.

Expressiveness versus convergence proof. The set of operations a CRDT can
support is bounded by what can be proven to commute or to form a
semilattice. An arbitrary business rule, for example that an account balance
may never go negative, generally cannot be expressed as a CRDT without
weakening the guarantee, because enforcing an invariant across concurrent,
unordered updates is precisely the coordination problem CRDTs are built to
avoid paying for. This is judgment. The practical boundary of what is
expressible keeps expanding as new CRDT constructions are published, but it
is never unbounded.

Metadata growth versus tombstone-free deletion. Sets that support removal
generally need to retain some record of what was removed, or a resurrection
bug appears, where a delete performed on one replica is undone by an add
from another replica that had not yet heard about the delete. That retained
record, whether a tombstone or a version vector entry, tends to grow over
time unless the CRDT design includes an explicit garbage collection
mechanism, which itself usually requires a form of coordination the rest of
the pattern was built to avoid.

Cognitive load on the team. A CRDT-based data model asks engineers to think
in terms of a merge function and a partial order rather than in terms of a
single mutable record, which is a genuine shift in mental model for a team
used to a row-locking relational database, and that shift has a real
onboarding and debugging cost that a trade-off table cannot capture as a
number.

## 4. Applicability and non-applicability

Reach for a CRDT when the following all hold. Writes must be accepted
locally without waiting for a remote round trip. More than one replica
genuinely accepts writes concurrently, not merely reads. The domain
operations can be expressed as a small, closed set of commutative or
state-mergeable operations. Losing a strict global order of operations is
acceptable because the domain only needs eventual, deterministic
convergence.

Do not reach for a CRDT for any of the following reasons, each with a
concrete reason it fails.

- The domain has a hard invariant that spans replicas, for example a bank
  account balance that must never go negative, or a unique username that
  must never be claimed twice. CRDTs converge to a defined merged state, but
  they do not enforce cross-replica invariants during the window before
  convergence, so a naive counter CRDT can transiently, and sometimes
  permanently under concurrent decrements, let a balance go negative before
  any human notices. Use consensus (Raft or Paxos backed single-writer
  state) or a saga with compensation instead.
- There is only ever one writer at a time, for example a single primary
  database with read replicas that never accept writes. There is no
  conflict to free the system from, so the CRDT merge machinery is pure
  overhead with no benefit, and a plain replicated log is simpler and
  easier to reason about.
- The team needs a strict, auditable order of events for compliance or
  debugging, for example a financial ledger that regulators expect to read
  as a single ordered sequence. A CRDT's partial order is not the same
  thing as a total order, and reconstructing what really happened first
  from a CRDT merge history is often impossible by design, because the
  whole point is that concurrent operations have no defined order relative
  to each other.
- The data set is large and the operation set is unbounded or ad hoc, for
  example a general-purpose document with arbitrary formatting rules
  invented after the fact. Building a correct CRDT for a genuinely novel
  operation requires a real convergence proof, which is research-grade
  work, not a weekend implementation task, and getting it wrong produces
  silent data corruption rather than a crash.
- The system already has a reliable, low-latency path to a single
  coordinator, for example a same-region monolith with one Postgres
  primary. The forces a CRDT trades against, coordination latency and
  availability during partition, are not actually present, so the added
  complexity buys nothing.

## 5. Structure

- Replica. A node holding a local copy of the CRDT-typed value. Each replica
  can accept local update operations without contacting any other replica.
- Payload (state). The concrete data structure carried by the CRDT, for
  example a set of element-and-tag pairs for an Observed-Remove Set, or a
  pair of vectors for a PN-Counter. The payload's shape is chosen
  specifically so that a merge function over it forms a join-semilattice.
- Update operation. A local mutation, for example an add, a remove, or an
  increment. In a state-based CRDT the operation only mutates local state
  and produces a new state to be gossiped later. In an operation-based CRDT
  the operation itself, or a derived downstream operation, is broadcast to
  every other replica.
- Merge function (state-based) or apply function (operation-based). The
  function every replica runs when it receives a peer's state or operation.
  For state-based CRDTs this must be commutative, associative, and
  idempotent, which are exactly the three algebraic properties of a join in
  a join-semilattice. For operation-based CRDTs the apply function must be
  commutative for concurrent operations, which is typically achieved by
  relying on the underlying broadcast layer to guarantee causal delivery
  order for non-concurrent operations.
- Causal broadcast (operation-based only). The delivery infrastructure that
  guarantees an operation is never applied before the operations it
  causally depends on. This is a hard external dependency for CmRDTs and its
  absence is the most common reason a from-scratch CmRDT implementation is
  subtly wrong.
- Metadata (tags, tombstones, version vectors, unique replica identifiers).
  The extra bookkeeping most CRDTs carry alongside the visible payload so
  that add-remove races and duplicate delivery resolve deterministically.
  This metadata is the actual engineering cost center of most real CRDT
  implementations and is usually invisible in a textbook description.

## 6. ASCII structure diagram

```
                 +-------------------------------+
                 |         Logical Value          |
                 |   (e.g. a shared shopping set) |
                 +-------------------------------+
                              ^
                merge / apply |  merge / apply
             +----------------+----------------+
             |                                 |
   +--------------------+           +--------------------+
   |     Replica A       |           |     Replica B       |
   |  local payload +     |          |  local payload +     |
   |  metadata (tags,     | <------> |  metadata (tags,     |
   |  version vector)     |  gossip  |  version vector)     |
   +--------------------+  or ops    +--------------------+
             |                                 |
     local update ops                  local update ops
             |                                 |
   +--------------------+           +--------------------+
   |  Client / user A     |           |  Client / user B     |
   +--------------------+           +--------------------+

  Property proven for every merge/apply pair, regardless of order,
  duplication, or delay.
      merge(merge(x, y), z) == merge(x, merge(y, z))   (associative)
      merge(x, y) == merge(y, x)                        (commutative)
      merge(x, x) == x                                  (idempotent)
```

## 7. Dynamics

```
Replica A                         Replica B
   |                                  |
   | add("milk")   [local, instant]  |
   |----> payload_A                  |
   |                                  | add("bread") [local, instant]
   |                                  |----> payload_B
   |                                  |
   |            (network partition, both replicas usable offline)
   |                                  |
   |  ---- gossip round or op-broadcast, order not guaranteed ---->
   |                                  |
   | payload_A --------------------->| merge(payload_B, payload_A)
   |                                  |    = {"milk","bread"}
   |<---------------------------- payload_B
   | merge(payload_A, payload_B)     |
   |    = {"milk","bread"}           |
   |                                  |
   v                                  v
Both replicas now hold the identical merged state, with no message
having required acknowledgement from the other side before it was
allowed to be produced locally.
```

For an operation-based (CmRDT) counter, the dynamics differ in one important
respect. Instead of shipping the whole payload, each replica ships the delta
operation itself, for example an increment by 3, and the causal broadcast
layer, not the merge function, is what guarantees every replica applies
non-concurrent operations in the same relative order. Concurrent operations
may still apply in either order at different replicas, which is why the
operation itself must be designed to commute.

## 8. Implementation variants

State-based (CvRDT), full state gossip. The entire local state is sent on
every sync round and merged with the merge operator. Simple to implement and
to reason about because merge only needs the three semilattice properties,
but bandwidth grows with the size of the payload, which is why production
systems almost never ship the naive full-state version.

State-based with deltas (delta-CRDT). Instead of the whole state, a replica
sends only the incremental change to its own state since the last sync, and
the receiving replica still applies it through the same commutative,
idempotent merge operator, so the correctness proof carries over unchanged
while the bandwidth cost drops close to that of an operation-based system.
This is the variant most production state-based systems actually deploy once
naive full-state gossip proves too expensive.

Operation-based (CmRDT). Only the update operation is transmitted, which is
cheap, but the design now depends on a reliable causal broadcast channel
that guarantees exactly-once, causally-ordered delivery for non-concurrent
operations, pushing real complexity into the network layer instead of the
data structure itself.

Two-Phase Set (2P-Set) and Observed-Remove Set (OR-Set). The classic
progression for a mergeable set. A 2P-Set tracks a set of additions and a
disjoint set of removals, and once an element is removed it can never be
re-added, which is a correctness limitation many real applications cannot
accept. The OR-Set fixes this by tagging every add with a unique identifier
and only removing the specific tags a replica has actually observed,
allowing an element to be removed and later re-added as a genuinely new
element.

PN-Counter. A counter that supports both increment and decrement by
tracking two separate vectors, one of per-replica increment totals and one
of per-replica decrement totals, with the visible value computed as the
element-wise sum of the increment vector minus the element-wise sum of the
decrement vector. This sidesteps the fact that a single scalar counter
cannot be merged commutatively once both increments and decrements are
allowed from multiple replicas.

Sequence CRDTs (RGA, LSEQ, Fugue, and the algorithm behind Yjs's YATA). The
variant used for collaborative text and rich document editing, where the
"set" being merged is an ordered sequence of characters or blocks, each
carrying a stable identifier that survives concurrent insertions at the same
position without the classic interleaving bug earlier sequence CRDTs
suffered from. This is the most actively researched CRDT sub-family because
ordering under concurrency is substantially harder than merging an unordered
set or a counter.

Language-idiomatic variants. In a language with algebraic data types and
strong immutability defaults, such as Rust or a functional-first language, a
CRDT is often expressed as a typeclass or trait constraining any type that
implements a lawful merge, letting the compiler enforce the semilattice laws
are at least type-checked even though the algebraic laws themselves still
require a separate proof or property test. In an object-oriented language
such as Java, the same idea is typically expressed as an interface with a
merge method and the laws are documented but not compiler-enforced.

## 9. Known production uses

Redis Software Active-Active geo-distributed databases. Redis's own
documentation states plainly that Active-Active databases only use
conflict-free replicated data types for conflict resolution across
geographically distributed primary nodes, and that the implementation is
internally called an Active-Active database, formerly known as a CRDB
(source https://redis.io/docs/latest/operate/rs/databases/active-active/,
verified 2026-08-02).

Riak KV Data Types. Basho's Riak documentation states that Riak KV has
Riak-specific data types based on convergent replicated data types, and
offers five CRDT-inspired data types (flags, registers, counters, sets, and
maps) as first-class values a client can operate on directly (source
https://docs.riak.com/riak/kv/2.2.3/developing/data-types/index.html,
verified 2026-08-02). Riak's CRDT data types were one of the first CRDT
implementations shipped in a general-purpose production database.

Automerge. Automerge's own GitHub README states that Automerge is a library
which provides fast implementations of several different CRDTs, a compact
compression format for these CRDTs, and a sync protocol for efficiently
transmitting those changes over the network, and the project is maintained
by the Ink and Switch research lab, with commercial users including
GoodNotes (source https://github.com/automerge/automerge, verified
2026-08-02). Automerge is the reference implementation most local-first
application developers reach for first.

Yjs. The Yjs README describes the project directly as a CRDT implementation
that exposes its internal data structure as shared types, and lists a "who
is using Yjs" section naming production adopters including GitBook and
AFFiNE among more than fifty named organizations (source
https://github.com/yjs/yjs, verified 2026-08-02). Yjs is the CRDT most
commonly embedded in real-time collaborative text editors built on top of
frameworks such as ProseMirror and Tiptap.

## 10. Consequences

Positive.

- Local writes never block on a network round trip, so perceived latency
  for a write is bounded by local processing rather than by the slowest
  reachable replica.
- The system remains fully available to writers during a network
  partition, trading a temporary divergence in state for continued
  availability, which is the AP side of the CAP trade-off made explicit and
  mathematically disciplined rather than ad hoc.
- Convergence is deterministic and provable for the operations the CRDT
  actually supports, which removes an entire class of manual conflict
  resolution code and the bugs that come with hand-written merge logic.
- Peer-to-peer topologies become possible without a central coordinator in
  the write path at all, because any two replicas that can exchange state
  or operations, in any order, will converge.

Negative.

- The set of supported operations is smaller than what an unconstrained
  data model allows, and expressing a new operation correctly, so that it
  commutes or merges as a lattice join, is genuinely hard and easy to get
  subtly wrong.
- Metadata (tags, tombstones, version vectors) grows over the lifetime of
  the data unless the CRDT design includes an explicit, coordinated garbage
  collection step, which reintroduces some of the coordination the pattern
  exists to avoid.
- Cross-replica invariants (uniqueness, non-negativity, referential
  integrity spanning two CRDT-typed objects) are not enforced by the merge
  function and must be handled by a separate mechanism, or accepted as
  eventually, not immediately, true.
- Debugging is harder than with a single-writer system, because the state a
  developer observes on one replica may legitimately differ from another
  replica's state for an unbounded, application-defined period before
  convergence, and reproducing a specific merge order for a bug report
  requires deliberately replaying the same interleaving.

## 11. Failure modes and misuse

Symptom. A deleted item silently reappears after a sync.
Cause. The CRDT uses a naive 2P-Set or an add-set without tags design, so a
concurrent add from a replica that had not yet observed the remove is merged
back in as if it were a fresh element, because the merge function has no way
to distinguish an add that happened after the remove from an add that is
concurrent with the remove.
Fix. Move to an Observed-Remove Set, where every add carries a unique tag
and a remove only removes the specific tags the removing replica had
actually observed at removal time, so a genuinely concurrent add survives on
purpose while a causally later add over a genuinely stale remove does not
resurrect.

Symptom. Storage or message size for the CRDT grows without bound over
weeks of normal use, even though the visible data set stays small.
Cause. Tombstones or per-replica metadata (unique tags, version vector
entries) accumulate forever because no garbage collection path was designed
in, which is easy to miss in an initial implementation because the effect is
invisible until the system has been running long enough to accumulate real
history.
Fix. Design an explicit, periodic garbage collection protocol from the
start, for example a stability threshold where metadata older than the
oldest still un-synced replica's watermark is safe to prune, and budget for
the fact that this step reintroduces some coordination cost the rest of the
CRDT was built to avoid.

Symptom. A numeric total (inventory count, account balance) goes negative
or exceeds a hard cap, even though no single replica ever issued an
operation that should have produced that value.
Cause. A plain counter CRDT, or a naive PN-Counter used for a quantity with
a business floor, has no concept of a cross-replica invariant, so two
replicas each independently and validly decrementing near the floor can
combine to push the merged total below it.
Fix. Recognize this as outside the CRDT's applicability, per dimension 4,
and either route the invariant-bearing operation through a coordinated path
(consensus, single-writer partition per account), or accept and reconcile
transient invariant violations explicitly at the application layer, for
example flagging an overdrawn account for manual review rather than
pretending the CRDT prevented it.

Symptom. Two users typing concurrently at the same position in a
collaborative document see their characters interleaved into gibberish
instead of appearing as two intact, adjacent runs of text.
Cause. An early or naive sequence CRDT design, as some early RGA and LSEQ
variants suffered, assigns identifiers to inserted characters in a way that
allows two concurrent insertions at the same logical position to interleave
character by character rather than staying as contiguous blocks.
Fix. Use a sequence CRDT algorithm specifically designed to preserve
insertion intention under concurrency, such as the algorithm underlying Yjs,
known as YATA, or the more recent Fugue algorithm, and treat this as a
solved but non-trivial research area rather than something to reinvent
casually.

Symptom. The team ships a hand-rolled CRDT for a new domain object, and QA
later finds two replicas that never converge to the same final state.
Cause. The merge function was written to look idempotent and commutative on
the examples the author tried, but was never actually proven, and a case
outside those examples, such as three-way concurrent operations or a
specific interleaving of add and remove, violates one of the three lattice
laws.
Fix. Treat proving the merge function forms a join-semilattice as a
required step, not an optional nicety, and cover it with property-based
tests that generate random operation orderings and assert the merged result
is independent of order, per dimension 15.

## 12. Trade-off matrix

| Force | CRDT | Operational Transformation (OT) | Single-leader with distributed lock | Vector-clock last-write-wins |
|---|---|---|---|---|
| Coordination on write | None required | None required, but transform requires a central server or agreed transform order in practice | Required on every write | None required |
| Data loss on concurrent edit | None, both edits preserved per the type's semantics | None in a correct OT implementation, but correctness proofs are notoriously hard to get right | None, writes are serialized | One edit is discarded by the LWW rule |
| Network dependency for correctness | None for CvRDT, a causal broadcast layer for CmRDT | A central transformation server or a total order broadcast in most real deployments | A lock service or leader must be reachable | None, but requires synchronized or logical clocks to compare |
| Expressiveness of operations | Bounded by what has a proven commutative or lattice-merge design | Broader in practice, text editing OT has decades of accumulated transform functions | Unbounded, since writes are fully serialized | Unbounded per key, but no merge semantics beyond overwrite |
| Implementation difficulty for a new operation | High, requires a convergence proof | High, requires a correct transform function against every other operation type | Low, ordinary code with a lock | Low, but semantically weak |
| Storage or bandwidth overhead | Metadata (tags, version vectors, tombstones) that can grow unbounded without garbage collection | Operation log or transform history, typically discarded once acknowledged | None beyond the lock itself | A version vector per key |

## 13. Related and incompatible patterns

Event Sourcing. A CRDT and an event-sourced aggregate both replace the
current value with a history plus a deterministic function, but an
event-sourced aggregate typically assumes a single, ordered log of events
per aggregate, replayed in that fixed order, while a CRDT is specifically
designed to converge correctly even when the order of concurrent events
differs between replicas. The two compose when an event-sourced system
needs to support multi-writer, offline-capable aggregates. The event
payloads themselves can be CRDT-typed so that replaying them in any order
still produces the same final state.

Vector Clocks and version vectors. A vector clock is the causality tracking
primitive many CRDT implementations use internally, particularly
Observed-Remove Sets and delta-CRDTs, to distinguish a causally later
operation from a genuinely concurrent one. A CRDT is not itself a vector
clock, but most non-trivial CRDTs are built on top of one.

Eventual Consistency. CRDTs are one specific, mathematically disciplined
mechanism for achieving eventual consistency. The broader pattern also
includes weaker mechanisms, such as anti-entropy repair with manual
conflict resolution or simple last-write-wins, that converge but without
the loss-free, deterministic guarantee a CRDT provides. Choosing a CRDT is
a strictly stronger commitment within the eventual-consistency family, not
a separate alternative to it.

Gossip Protocol. State-based CRDTs are almost always propagated over a
gossip protocol, where each replica periodically exchanges state with a
randomly or topologically chosen peer. The gossip protocol supplies the
guarantee that eventually every replica hears from every other replica, the
delivery guarantee a CRDT's merge function depends on for convergence. The
CRDT supplies the guarantee that whatever order gossip delivers state in,
the result is the same.

Operational Transformation, incompatible in practice within one system. OT
and CRDTs solve the same collaborative-editing problem with genuinely
different mechanisms, and mixing the two within a single document's
synchronization layer is not a recognized, supported architecture. A system
picks one approach for a given shared data structure. They are commonly
compared rather than composed, and the choice between them is usually
driven by whether a central server is acceptable in the write path,
favoring OT, which most production OT systems rely on, or whether true
peer-to-peer, serverless convergence is required, favoring CRDTs.

Consensus protocols (Raft, Paxos), incompatible for the same value. A
single logical value cannot simultaneously be governed by a consensus
protocol, which enforces a single total order and a single leader at a
time, and by a CRDT, which explicitly permits multiple concurrent writers
with no leader. A system can use both, but not for the same field.
Consensus for the fields that carry hard invariants, CRDTs for the fields
that must remain available and mergeable under partition.

## 14. Refactoring path in and out

Introducing a CRDT into existing single-writer code. Start by identifying
the specific fields or aggregates that actually need multi-writer,
partition-tolerant behavior, rather than converting an entire data model at
once. Most systems only need this for a small subset of their data, a
shared document body or a collaborative task list, while the rest stays
comfortably single-writer. Replace the target field's plain mutable
representation with a CRDT-typed payload plus its required metadata, while
keeping the field's external read API unchanged so calling code is
unaffected. Add the merge function and wire it into whatever
synchronization transport already exists, a message queue, a peer-to-peer
channel, a periodic batch sync, verifying convergence with property-based
tests, per dimension 15, before removing any of the old locking or
coordination code that field previously relied on. Only after the new path
has run in production long enough to build confidence should the old
coordination path be deleted, and it should be deleted, not left dormant,
because a stale second write path is a source of the exact consistency bugs
the migration was meant to remove.

Removing a CRDT once it stops earning its place. This most often happens
when a product decision eliminates true concurrent multi-writer usage, for
example when a shared-document feature is descoped to single-owner
documents. Confirm the field genuinely has at most one writer at a time in
the new design, then replace the CRDT-typed payload with a plain value plus
a monotonically increasing version number, migrate existing CRDT state to
its final merged value as the new plain value, and remove the merge
function and its metadata. Do this migration behind a feature flag and keep
the old CRDT-read path available for a rollback window, because the point
at which a team is confident concurrency genuinely stopped is exactly the
point at which someone finds an edge case where it did not.

## 15. Testing and verification

The single most important testing technique for a CRDT is property-based
testing of the merge function's algebraic laws, because example-based tests
of specific merge scenarios cannot catch a violation that only appears
under a particular interleaving the author did not think to write by hand.
A property test should generate two or more independently mutated replicas
of the CRDT with a randomized sequence of operations each, then assert that
merging in any grouping produces the same result as merging in any other
grouping (associativity), that merging two replicas in either order
produces the same result (commutativity), and that merging a replica with
itself produces itself (idempotence), and additionally assert that applying
the same set of operations to two replicas in any two different orders
yields the same final merged state, the actual convergence property the
algebraic laws exist to guarantee.

CRDTs also make an unusual class of scenario easy to test that a
single-writer system cannot express at all. Simulate a network partition by
running two replicas with zero synchronization for a period, apply
divergent operations to each, then merge and assert both replicas converge
to the expected value, including the specific add-remove race scenarios
named in dimension 11.

What becomes harder to test. Any assertion about global invariants across
the whole data set, uniqueness or sum totals staying within a range,
requires a separate, explicit test layer that simulates the worst-case
interleaving of concurrent operations, because unit tests against a single
replica in isolation will not surface an invariant violation that only
appears after a merge.

Useful test doubles. A deterministic, seedable network simulator that can
replay a specific, previously-buggy delivery order, out-of-order,
duplicated, or delayed messages, is worth building once and reusing across
every CRDT in the system, because the failure modes in dimension 11 are
almost always triggered by a specific delivery order rather than by any
single operation in isolation.

## 16. Observability signals

Log or trace, per replica, the local operation count and the last
successful merge or sync timestamp against each known peer, so an operator
can immediately see whether a specific replica has silently stopped
propagating or receiving updates, which is the CRDT-specific equivalent of
replication lag in a traditional leader-follower database.

Measure and alert on divergence duration, the time between when two
replicas last held different states for the same logical object and when
they converged, because an unbounded or growing divergence duration is the
earliest observable sign that the gossip or broadcast layer underneath the
CRDT has degraded, even though the CRDT's own correctness guarantee means
the application will never crash from it.

Measure metadata size growth over time, tombstone count and version vector
entry count, per CRDT instance, because unbounded growth here, as described
in dimension 11, is invisible in the visible application data and only
shows up as a storage or message-size problem weeks or months later if
nobody is watching it from day one.

A healthy CRDT instance on a dashboard shows divergence duration bounded
and roughly constant across normal operation, metadata size growing
sub-linearly relative to visible data size, or flat once garbage collection
is running, and merge or apply operation latency that stays flat regardless
of how many concurrent writers are active, since the entire point of the
pattern is that merge cost does not scale with writer count the way lock
contention does. A failing instance shows metadata size growing linearly or
faster with time regardless of visible data size, divergence duration
climbing without bound, or merge latency growing as payload size grows
unbounded, which typically means the team is still on naive full-state
CvRDT gossip rather than a delta-CRDT or operation-based design.

## 17. Security and privacy implications

A CRDT's core guarantee, that any replica can accept and apply writes
without authenticating or coordinating with any other party first, is
precisely the property that removes the natural chokepoint most
access-control systems rely on to reject an unauthorized write before it is
accepted. Any production CRDT system needs an authorization check at the
point where a local write is first issued, not merely at a central server,
because there generally is no single gate every write passes through. A
client that has been compromised, or that is simply malicious, can inject
an operation that will faithfully and correctly propagate to every other
replica exactly as designed, which is a security property to plan for
rather than a bug in the CRDT itself.

Data retained for CRDT correctness, tombstones in particular, can retain a
record that an item existed and was removed for longer than the visible
application data suggests, which has a direct privacy implication under
regimes such as GDPR's right to erasure. Deleting a record from the visible
state of an Observed-Remove Set does not necessarily remove the tag or
tombstone identifying who removed it and when, and a genuine right to be
forgotten implementation on top of a CRDT needs an explicit, coordinated
purge step that goes beyond the normal merge-based deletion the CRDT
provides by default.

Metadata such as per-replica unique identifiers embedded in add-tags can
leak which device or user account originated a specific piece of data,
which is a consideration in any system where the CRDT's internal metadata
is inadvertently exposed to other, less trusted parties through the sync
protocol, even when the visible application data itself is not sensitive.

## 18. References

1. Marc Shapiro, Nuno Preguica, Carlos Baquero, Marek Zawirski, "Conflict-Free
   Replicated Data Types," Stabilization, Safety, and Security of Distributed
   Systems (SSS 2011), Lecture Notes in Computer Science, volume 6976, pages
   386 to 400, 2011. Publication details verified against
   https://en.wikipedia.org/wiki/Conflict-free_replicated_data_type, verified
   2026-08-02.
2. Redis, "Active-Active geo-distributed Redis,"
   https://redis.io/docs/latest/operate/rs/databases/active-active/, verified
   2026-08-02.
3. Basho/Riak documentation, "Riak Data Types,"
   https://docs.riak.com/riak/kv/2.2.3/developing/data-types/index.html,
   verified 2026-08-02.
4. Automerge project, README, https://github.com/automerge/automerge,
   verified 2026-08-02.
5. Yjs project, README, https://github.com/yjs/yjs, verified 2026-08-02.

## Code examples

### TypeScript, a Grow-only Counter (G-Counter) as a minimal CvRDT

```typescript
type GCounter = Map<string, number>;

function increment(counter: GCounter, replicaId: string, by = 1): GCounter {
  const next = new Map(counter);
  next.set(replicaId, (next.get(replicaId) ?? 0) + by);
  return next;
}

function mergeCounters(a: GCounter, b: GCounter): GCounter {
  const merged = new Map(a);
  for (const [replicaId, value] of b) {
    merged.set(replicaId, Math.max(merged.get(replicaId) ?? 0, value));
  }
  return merged;
}

function value(counter: GCounter): number {
  let total = 0;
  for (const v of counter.values()) total += v;
  return total;
}

const a: GCounter = increment(new Map(), "replica-a", 3);
const b: GCounter = increment(new Map(), "replica-b", 5);
const mergedAB = mergeCounters(a, b);
const mergedBA = mergeCounters(b, a);

if (value(mergedAB) !== value(mergedBA)) {
  throw new Error("merge is not commutative");
}
console.log("converged value", value(mergedAB));
```

### Go, an Observed-Remove Set (OR-Set)

```go
package main

import "fmt"

type Tag struct {
	Element string
	Unique  string
}

type ORSet struct {
	Adds    map[Tag]bool
	Removes map[Tag]bool
}

func NewORSet() *ORSet {
	return &ORSet{Adds: map[Tag]bool{}, Removes: map[Tag]bool{}}
}

func (s *ORSet) Add(element, unique string) {
	s.Adds[Tag{element, unique}] = true
}

func (s *ORSet) Remove(element string) {
	for tag := range s.Adds {
		if tag.Element == element && !s.Removes[tag] {
			s.Removes[tag] = true
		}
	}
}

func (s *ORSet) Merge(other *ORSet) *ORSet {
	merged := NewORSet()
	for tag := range s.Adds {
		merged.Adds[tag] = true
	}
	for tag := range other.Adds {
		merged.Adds[tag] = true
	}
	for tag := range s.Removes {
		merged.Removes[tag] = true
	}
	for tag := range other.Removes {
		merged.Removes[tag] = true
	}
	return merged
}

func (s *ORSet) Elements() map[string]bool {
	live := map[string]bool{}
	for tag := range s.Adds {
		if !s.Removes[tag] {
			live[tag.Element] = true
		}
	}
	return live
}

func main() {
	replicaA := NewORSet()
	replicaA.Add("milk", "a-1")

	replicaB := NewORSet()
	replicaB.Add("bread", "b-1")

	replicaA.Remove("milk")

	merged := replicaA.Merge(replicaB)
	fmt.Println(merged.Elements())
}
```

### Python, a PN-Counter (increment and decrement)

```python
from dataclasses import dataclass, field


@dataclass
class PNCounter:
    increments: dict[str, int] = field(default_factory=dict)
    decrements: dict[str, int] = field(default_factory=dict)

    def increment(self, replica_id: str, by: int = 1) -> None:
        self.increments[replica_id] = self.increments.get(replica_id, 0) + by

    def decrement(self, replica_id: str, by: int = 1) -> None:
        self.decrements[replica_id] = self.decrements.get(replica_id, 0) + by

    def merge(self, other: "PNCounter") -> "PNCounter":
        merged_inc = dict(self.increments)
        for replica_id, value in other.increments.items():
            merged_inc[replica_id] = max(merged_inc.get(replica_id, 0), value)
        merged_dec = dict(self.decrements)
        for replica_id, value in other.decrements.items():
            merged_dec[replica_id] = max(merged_dec.get(replica_id, 0), value)
        return PNCounter(merged_inc, merged_dec)

    def value(self) -> int:
        return sum(self.increments.values()) - sum(self.decrements.values())


replica_a = PNCounter()
replica_a.increment("a", 10)
replica_a.decrement("a", 3)

replica_b = PNCounter()
replica_b.increment("b", 4)

merged_ab = replica_a.merge(replica_b)
merged_ba = replica_b.merge(replica_a)
assert merged_ab.value() == merged_ba.value()
print("converged value", merged_ab.value())
```
