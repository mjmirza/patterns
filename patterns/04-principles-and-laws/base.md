---
name: BASE
slug: base
family: 04-principles-and-laws
category: Principle
aliases: [Basically Available Soft State Eventually Consistent, BASE Consistency Model, ACID Alternative]
first_described: "Pritchett 2008 (named and formalized), Brewer 1997-2000 (informal precursor)"
maturity: canonical
related: [cap-theorem, quorum-consensus, saga, single-source-of-truth, fail-fast]
incompatible_with: []
verified: 2026-08-02
---

# BASE

## 1. Name, aliases, and lineage

BASE is a backronym for Basically Available, Soft state, Eventually consistent.
The name and the formal three-part definition were introduced by Dan Pritchett,
then chief architect at eBay, in "BASE. An ACID Alternative," ACM Queue, volume
6, issue 3, pages 48 to 55, May 2008
([queue.acm.org/detail.cfm?id=1394128](https://queue.acm.org/detail.cfm?id=1394128),
verified 2026-08-02). Pritchett states plainly in the paper that BASE was coined
as a deliberate wordplay against ACID, the transactional guarantee that
relational databases had offered for decades, and that the letters were chosen
to spell a real word so the idea would be memorable to engineers who had never
heard of it.

The intellectual lineage predates the acronym by a decade. Eric Brewer, at the
time a professor at UC Berkeley and the founder of the search company Inktomi,
argued through the middle and late 1990s that internet-scale systems had to
trade strict consistency for availability, and he stated this formally as what
became known as the CAP theorem in a keynote at the ACM Symposium on Principles
of Distributed Computing in 2000
([sites.cs.ucsb.edu, "CAP Twelve Years Later," Brewer, IEEE Computer 45(2),
2012](https://sites.cs.ucsb.edu/~rich/class/cs293b-cloud/papers/brewer-cap.pdf),
verified 2026-08-02, which recounts the 2000 keynote and Brewer's own account of
Inktomi's design choices in the years before it). BASE is the constructive
answer to the CAP theorem's negative result. Where CAP states what a networked
data system cannot simultaneously guarantee, BASE describes the operating
posture a system takes once it has chosen availability over strict consistency
under partition, and Pritchett's paper is explicit that eBay's own architecture
motivated the write. This repository's own [CAP theorem](cap-theorem.md) entry
covers the impossibility result. BASE is its practitioner-facing complement,
concerned with how a system actually behaves once the trade-off has been made,
not with proving that a trade-off exists.

A second, older lineage sits underneath both. The Dynamo system built inside
Amazon and described in Giuseppe DeCandia and eight co-authors, "Dynamo.
Amazon's Highly Available Key-value Store," Proceedings of the 21st ACM
Symposium on Operating Systems Principles (SOSP), October 2007
([Werner Vogels, "Amazon's Dynamo," All Things Distributed, 2007-10-02](https://www.allthingsdistributed.com/2007/10/amazons_dynamo.html),
verified 2026-08-02, an author's own summary of the SOSP paper), never uses the
word BASE, because the paper predates Pritchett's coinage by roughly a year, but
it is the most cited engineering description of exactly the operating posture
BASE later named. Dynamo's own vocabulary, always writable, sloppy quorums,
vector clocks, read repair, and anti entropy, became the standard implementation
toolkit that every subsequent BASE-labelled system reuses. Reading Dynamo before
reading Pritchett is common in practice and this entry treats the two as one
continuous idea, named twice by two different engineering communities working on
the same problem within a year of each other.

No alternate name for BASE is in wide circulation. "Eventual consistency" is
sometimes used loosely as a synonym, but that phrase names only the third letter
of the acronym. A system can be eventually consistent without being basically
available, a system that blocks writes during a partition and only becomes
consistent once the partition heals is eventually consistent but not basically
available, so treating the two as interchangeable understates what BASE
actually asks for.

## 2. Problem and context

A system holds one logical piece of data on more than one physical machine,
because a single machine cannot serve the read and write volume, cannot survive
its own failure, or sits too far from some of its readers to answer inside an
acceptable latency budget. The moment a value exists in more than one place,
somebody has to decide what happens when a client asks to read it while the
copies disagree, and what happens when a client asks to write it while some of
the copies cannot be reached.

A single-machine relational database never faces this problem, because there is
only one copy of the row and the transaction manager can lock it. ACID
guarantees are a promise that a well-defined single copy of truth behaves
predictably. As soon as replication crosses a network boundary that can
partition, that promise becomes expensive to keep, and the expense is not a
constant tax, it is a decision the system makes every single request, whether
the request notices it or not.

The context in which BASE becomes the honest description of a system, rather
than an excuse for sloppy engineering, has three concrete markers. First, the
data is replicated across machines, data centers, or regions that can lose
contact with each other independently of any single machine failing. Second,
the business consequence of serving a slightly stale read, or of accepting a
write that later needs reconciling against a conflicting write, is genuinely
smaller than the business consequence of refusing to serve the request at all.
A shopping cart that briefly shows last week's item count is an inconvenience.
A shopping cart that refuses to add an item because two data centers cannot
currently agree is a lost sale. Third, the system has, or can build, a
mechanism for resolving disagreement after the fact, because eventual
consistency is a promise with a deadline attached only in the sense that the
deadline is "when connectivity and time permit," and a system with no repair
mechanism is not eventually consistent, it is simply inconsistent.

Pritchett frames the eBay context directly. eBay's databases were partitioned by
function and by data range specifically to avoid the two-phase commit and
cross-shard locking that a single ACID database would need at that scale, and
BASE names the operating discipline that made partitioning workable, aggregate
functions computed approximately and refined later, and a strong bias toward
availability over strict cross-shard consistency
([queue.acm.org/detail.cfm?id=1394128](https://queue.acm.org/detail.cfm?id=1394128),
verified 2026-08-02).

## 3. Forces

BASE resolves a specific tension among competing pressures, and naming which
pressures it favors and which it deliberately gives up is the difference
between understanding BASE and merely being able to expand the acronym.

Availability under partition is the force BASE protects above nearly every
other. A system committed to BASE will accept a write, or serve a read, even
when it cannot immediately confirm that every replica agrees, because refusing
the request is treated as the worse failure. This is a direct application of
Brewer's original observation that a system facing a network partition must
choose between consistency and availability, and BASE is the branch that
chooses availability, articulated as an engineering discipline rather than as
a one-time architectural decision.

Latency is closely coupled to availability here and deserves separate mention,
because the two are often conflated. A quorum system that requires a majority
of replicas to acknowledge a write before it succeeds is still, in the CAP
sense, choosing availability over strict consistency, because it does not wait
for every replica, but it pays a latency cost proportional to the slowest
replica in the majority. BASE systems typically favor low, predictable latency
over completeness of agreement, which is why sloppy quorums, hinted handoff,
and read repair exist as separate mechanisms rather than a single blocking
write path.

Operability is a force that BASE increases the burden on, in direct exchange
for the availability it buys. A single-copy ACID system has one thing to keep
healthy. A BASE system has N replicas, a convergence mechanism, and a class of
production incident, the split-brain write, the unrepaired conflict, the
anti-entropy job that silently stopped running, that a strictly consistent
system does not produce. The operational cost is real and recurring, not a
one-time design cost, and any honest account of BASE names it.

Consistency, specifically the strength and the freshness of what a reader sees,
is the force BASE explicitly and deliberately weakens. This is not a
side-effect. It is the trade being made. A BASE system promises that replicas
will converge given no further writes and enough time, not that any given read
reflects the most recent write, and the gap between those two promises is
exactly where application-level bugs live when engineers reach for BASE without
internalizing what it costs.

Cost, in the literal infrastructure sense, favors BASE at scale, because
strict consistency across geographically distributed replicas requires either a
consensus protocol whose latency grows with the number of participants and the
distance between them, or a single writer, both of which cap horizontal
scalability in ways that eventual consistency with local, independent replica
writes does not.

Cognitive load on the application developer is a force BASE shifts rather than
reduces. The database no longer carries the burden of resolving every
disagreement synchronously, but the application, or a conflict resolution
layer sitting above the database, now has to reason about stale reads, about
concurrent writes to the same key, and about what "eventually" means for the
specific feature being built. A team that adopts BASE without building this
reasoning into its application code is trading a database problem for a much
harder distributed application problem.

## 4. Applicability and non-applicability

Reach for BASE when the following hold.

- The data is naturally partitioned or shardable by a key that most operations
  already use, a user id, a session id, a product id, so that most reads and
  writes touch one shard's replica set and cross-shard coordination is rare.
- The system must survive the loss of a data center, a rack, or a single
  replica without refusing traffic, and the business impact of a request being
  refused outright exceeds the impact of it being served with slightly stale
  or eventually-reconciled data.
- The write workload benefits from being accepted locally, close to the writer,
  rather than routed to a single global leader, because cross-region latency
  would otherwise outweigh the cost of a local write and its later
  reconciliation.
- A merge or reconciliation strategy exists, or can be built, that is correct
  for the specific data shape. Grow-only counters, sets with tombstones,
  last-writer-wins registers with a trustworthy clock, or an application-level
  merge function that understands the domain, a shopping cart union, a social
  feed union, a metric sum.
- The read path can tolerate returning a value that is provably not the very
  latest write, and the product surface communicates or hides that gap in a
  way users accept, a "processing" indicator, a background refresh, an
  eventual notification.

Do NOT reach for BASE when the following hold.

- The operation is a financial transfer, an inventory decrement against a hard
  physical limit, a ticket allocation, or any operation where two conflicting
  writes both succeeding is a business or legal defect, not an inconvenience.
  These need serializable transactions or a consensus-backed single writer, not
  a merge function applied after the fact. BASE has no answer for "exactly one
  of these two concurrent writes may win and the loser must be told it lost,"
  because that is precisely the strict-consistency guarantee BASE gives up.
- The team has no engineering capacity to build, test, and operate a conflict
  resolution or reconciliation mechanism. A BASE system with no working
  anti-entropy process is not eventually consistent, it is a system that is
  quietly and permanently inconsistent, which is worse than a system that is
  honestly and visibly unavailable during a partition.
- The dataset is small enough, and the availability requirement modest enough,
  that a single well-replicated ACID database with synchronous or
  near-synchronous replication meets the latency and availability targets
  without the added operational surface of a BASE system. Most internal admin
  tools and most systems under a few thousand requests per second on a single
  region fall here, and adopting BASE for them buys operational cost with no
  corresponding benefit.
- Regulatory or audit requirements demand that the system can state, at any
  instant, an unambiguous single value for a piece of data, with no window in
  which two readers can observe different answers to the same question. Some
  compliance regimes for financial ledgers and healthcare records fall into
  this category, and a BASE system's soft state window is a direct conflict
  with that requirement unless the reconciliation is proven to complete inside
  a bounded, audited time window, which most BASE implementations do not
  guarantee.
- The team, product, and support organization are not prepared to explain a
  stale read or a resolved conflict to a confused end user. BASE moves a
  technical trade-off into user-visible behavior, and a product that cannot
  absorb that visibility should not adopt it silently.

## 5. Structure

BASE names an operating posture rather than a fixed architecture, so its
"structure" is the recurring set of participants that any real BASE
implementation assembles, whether it is Dynamo, Cassandra, Riak, DynamoDB, or a
hand-rolled application-level cache.

- **Client.** Issues reads and writes. Under BASE, the client is often given
  explicit control over the consistency it requests for a given operation, a
  read that asks for a fast, possibly-stale answer versus a read that asks for
  a quorum-confirmed, more-current answer.
- **Coordinator or router.** The node, proxy, or client-side library that
  receives a request and forwards it to the replica set responsible for the
  requested key. In Dynamo-derived systems this is any node in the ring that
  happens to receive the request, not a fixed leader.
- **Replica set.** N nodes that each hold a full copy of a given key's data.
  The replica set is usually determined by consistent hashing over the key,
  so that adding or removing nodes reshuffles only a fraction of the keyspace.
- **Write quorum W and read quorum R.** Configurable counts of replicas that
  must acknowledge a write, or respond to a read, before the coordinator
  answers the client. W and R are the dial that trades latency and
  availability against read-your-writes freshness, and the classic Dynamo
  result is that when W + R > N the read set and the write set are guaranteed
  to overlap by at least one node, which bounds, but does not eliminate, the
  staleness a reader can see.
- **Soft state.** The value or values a replica currently holds for a key,
  understood as provisional rather than final. A key can legitimately hold
  more than one concurrent value, called siblings, when two writes happen
  concurrently on different replicas without one causally preceding the other.
- **Version metadata.** A mechanism, most often a vector clock or a
  per-replica logical timestamp, that lets the system distinguish "this write
  causally followed that one, discard the older" from "these two writes are
  concurrent and cannot be ordered, keep both and let the application or a
  merge function decide."
- **Anti-entropy process.** A background mechanism, running independently of
  any client request, that compares replicas pairwise, typically using a
  Merkle tree to find divergent key ranges cheaply, and repairs
  inconsistencies it finds. This is the mechanism that makes "eventually"
  actually arrive rather than remaining a promise.
- **Hinted handoff.** A fallback write path used when a replica that should
  receive a write is temporarily unreachable. A different, healthy node
  accepts the write on the unreachable replica's behalf and holds a hint to
  forward it once the original replica returns, which is the specific
  mechanism that lets a write succeed, and the system remain basically
  available, even when the "correct" replica set is not fully reachable.
- **Read repair.** An opportunistic correction applied during a normal read.
  When a coordinator reads from R replicas and notices they disagree, it
  writes the reconciled value back to the stale replicas before returning to
  the client, folding some of the anti-entropy work into the ordinary read
  path rather than waiting for the background process alone.

## 6. ASCII structure diagram

```
                        +------------------+
                        |      Client      |
                        +---------+--------+
                                  |
                                  v
                        +------------------+
                        |   Coordinator    |
                        | (any ring node)  |
                        +---+----+----+----+
                            |    |    |
              write to W of N    read from R of N
                            |    |    |
              +-------------+    |    +-------------+
              v                  v                   v
       +-------------+   +-------------+      +-------------+
       | Replica A   |   | Replica B   |      | Replica C   |
       | soft state, |   | soft state, |      | UNREACHABLE |
       | v={5,7,2}   |   | v={5,6,2}   |      |             |
       +------+------+   +------+------+      +-------------+
              |                 |                     ^
              |   anti-entropy  |                     |
              +--- (Merkle tree +---------------------+
                    diff + repair, runs continuously)
                            |
              hinted handoff, a healthy node holds
              the write meant for Replica C until it
              rejoins, then forwards it and Replica C
              catches up via read repair or anti-entropy
```

## 7. Dynamics

The sequence below shows a single write with N = 3 replicas, W = 2, one
replica temporarily unreachable, followed by the two mechanisms, hinted
handoff and read repair, that carry the system from "basically available and
soft" to "eventually consistent."

```
time  event
----  --------------------------------------------------------------
t0    Client sends PUT key=cart-42 value={items:[A,B]} v_client={}
t1    Coordinator resolves the 3 replicas for cart-42: R1, R2, R3
t2    Coordinator writes to R1, R2 in parallel. R3 is unreachable.
t3    R1 acks with vclock {R1:1}. R2 acks with vclock {R2:1}.
t4    W=2 satisfied (R1, R2 acked). Coordinator returns SUCCESS
      to the client even though R3 never received the write.
      -- this is "basically available", the write succeeded
      -- despite one of three replicas being unreachable.
t5    Coordinator hands the write meant for R3 to a healthy
      stand-in node, R2, as a hint. "deliver this to R3 when
      it returns." R2 stores the hint alongside its own data.
      -- the value on R1 and R2 is now "soft state", it is
      -- accepted, but not yet present everywhere it should be.
t6    R3 recovers and rejoins the ring.
t7    R2 detects R3 is reachable, forwards the hinted write.
      R3 applies it, now holding vclock {R1:1, R2:1}.
t8    Later, a client GET on cart-42 with R=2 reads from R1
      and R3. Both return the same value and vclock. No
      conflict. Coordinator returns it directly.
t9    Separately, the nightly anti-entropy job compares Merkle
      tree roots for R1, R2, R3's key ranges, finds no
      remaining divergence for cart-42, and moves on.
      -- the system has now converged, this is "eventually
      -- consistent," reached through hinted handoff, not
      -- through the anti-entropy job alone, which acts as a
      -- backstop for gaps hinted handoff does not close.
```

A second, shorter sequence shows the concurrent-write case that BASE forces
the application to confront directly, which the happy path above never
exposes.

```
t0    Client X reads cart-42, sees v={R1:1,R2:1}, items=[A,B]
t0    Client Y reads cart-42, sees v={R1:1,R2:1}, items=[A,B]
      (both clients read the same version concurrently)
t1    Client X writes items=[A,B,C], new vclock {R1:2,R2:1}
t1    Client Y writes items=[A,B,D], new vclock {R1:1,R2:2}
      (neither vclock is a strict descendant of the other,
       this is a genuine concurrent write, not a stale one)
t2    A later read observes both siblings and must resolve
      them. A last-writer-wins policy would silently drop
      one client's item. A domain-aware merge (union the
      item sets, since this is a shopping cart) returns
      items=[A,B,C,D], preserving both concurrent additions.
```

## 8. Implementation variants

**Dynamo-style, quorum plus vector clocks plus siblings exposed to the client.**
The write and read paths use configurable W, R, and N, and when concurrent
writes cannot be causally ordered, the system exposes both values, called
siblings, to the reader rather than silently picking one. Resolving siblings is
the application's job. This is the approach the original Dynamo paper describes
and the approach Riak, a direct implementation of the Dynamo paper's ideas,
exposes to application code
([DeCandia et al., SOSP 2007, summarized by Vogels, 2007-10-02](https://www.allthingsdistributed.com/2007/10/amazons_dynamo.html),
verified 2026-08-02). It is the most faithful implementation of BASE's "soft
state" letter, because the system genuinely holds more than one value at once
and says so, rather than hiding the ambiguity.

**Last-writer-wins with a trusted clock.** Instead of exposing siblings, the
system attaches a timestamp, often a hybrid logical clock or a server-assigned
timestamp with bounded clock skew guarantees, to every write, and on conflict
keeps the write with the later timestamp, discarding the other silently.
Cassandra's default conflict resolution for a single column is last-writer-wins
by timestamp
([docs.datastax.com, "About data consistency," Apache Cassandra 2.1
documentation](https://docs.datastax.com/en/cassandra-oss/2.1/cassandra/dml/dmlAboutDataConsistency.html),
verified 2026-08-02). This variant is simpler to reason about and to operate,
at the direct cost that a genuinely concurrent write can be silently lost, so
it is only correct when the data shape tolerates losing one of two concurrent
writes, or when writes to the same key are rare enough that concurrent writes
are a negligible edge case rather than a routine occurrence.

**CRDT-based, mathematically guaranteed convergence.** Conflict-free Replicated
Data Types are data structures, counters, sets, registers, sequences, whose
merge operation is defined to be commutative, associative, and idempotent, so
that replicas that have received the same set of updates in any order, any
number of times, converge to the same state without any coordinator deciding a
winner. This variant removes the application-level burden of writing a merge
function, at the cost of restricting the data model to the specific CRDT types
available, and it is the variant Riak adopted as an alternative to raw
sibling resolution for common data shapes
([Basho, Riak KV Data Types, documented CRDT support in Riak's data type
system, cited via the Riak KV documentation archive](https://docs.riak.com/riak/kv/latest/developing/data-types/index.html),
verified 2026-08-02).

**Quorum-tunable per-operation.** Rather than a single fixed consistency level
for the whole system, the client chooses, per read and per write, how many
replicas must participate, trading availability and latency against freshness
on a request-by-request basis. Apache Cassandra exposes this directly as a
per-query consistency level, ONE, QUORUM, ALL, and others, letting an
application demand strong consistency for a critical read and eventual
consistency for a bulk background scan against the same table
([Baeldung, "Consistency Levels in Cassandra"](https://www.baeldung.com/cassandra-consistency-levels),
verified 2026-08-02, corroborated by the DataStax documentation cited above).

**Managed, opaque BASE as a service.** Amazon DynamoDB and Azure Cosmos DB
offer BASE-style eventual consistency as the default or as one selectable
mode, with the anti-entropy, hinted handoff, and vector-clock machinery
entirely hidden from the operator, exposed only as a consistency-level knob
and a documented staleness bound. This trades the operational burden of
running the convergence machinery for a much narrower set of tuning options
than a self-operated Dynamo-style cluster provides.

## 9. Known production uses

- **Amazon Dynamo, and by direct descent Amazon DynamoDB.** Dynamo was built
  inside Amazon specifically to keep the shopping cart, and other
  high-write-volume, high-availability services, responding even during
  partial data center failures, using sloppy quorums and vector clocks to
  remain "always writable." DynamoDB, Amazon's managed successor, inherits the
  same eventual-consistency-by-default posture, offering strongly consistent
  reads only as an explicit, costlier option
  ([DeCandia et al., SOSP 2007, summarized by Werner Vogels,
  "Amazon's Dynamo," 2007-10-02](https://www.allthingsdistributed.com/2007/10/amazons_dynamo.html),
  verified 2026-08-02).
- **Apache Cassandra at Netflix.** Netflix operates Cassandra across multiple
  AWS regions for user-facing state, and for responsiveness-critical services
  it deliberately favors availability during a network partition, accepting
  that a service may serve slightly stale data rather than refuse to respond,
  with convergence completing once the partition heals
  ([Cassandra's tunable, per-operation consistency model as documented by
  DataStax](https://docs.datastax.com/en/cassandra-oss/2.1/cassandra/dml/dmlAboutDataConsistency.html),
  verified 2026-08-02, describing the ONE-level reads Netflix-style
  availability-favoring deployments rely on).
- **Riak, built explicitly as a Dynamo implementation.** Riak KV was designed
  from the outset to follow the Dynamo paper's architecture, including vector
  clocks, sloppy quorums, hinted handoff, and, later, built-in CRDTs as an
  alternative to raw sibling resolution, making it the clearest open-source,
  publicly documented realization of the BASE operating model described in
  this entry
  ([docs.riak.com, Riak KV Data Types documentation](https://docs.riak.com/riak/kv/latest/developing/data-types/index.html),
  verified 2026-08-02).
- **eBay's own partitioned architecture, the source of the acronym.** Dan
  Pritchett describes eBay's databases as partitioned both functionally and
  horizontally specifically to avoid distributed two-phase commit at scale,
  aggregate values computed with intentional imprecision and reconciled on a
  schedule, which is the concrete production system BASE was coined to
  describe
  ([Pritchett, "BASE. An ACID Alternative," ACM Queue 6(3), May 2008](https://queue.acm.org/detail.cfm?id=1394128),
  verified 2026-08-02).

## 10. Consequences

**Positive.**

- Availability during partial failure. A BASE system can accept writes and
  serve reads even when some replicas, or an entire data center, are
  unreachable, which a strictly consistent system with a single writer or a
  synchronous quorum across regions generally cannot.
- Lower and more predictable write latency, because a write can be
  acknowledged after a small, local quorum rather than after every replica,
  or every region, confirms.
- Horizontal scalability without a coordination bottleneck. Adding replicas or
  shards does not require every write to pay the cost of coordinating across
  all of them, only across the quorum the operation actually touches.
- Graceful degradation. A system built on BASE from the start tends to have
  explicit, tested behavior for the partial-failure case, because partial
  failure is the normal operating condition it was designed for, rather than
  an untested edge case bolted onto a system that assumed full connectivity.

**Negative.**

- Stale reads are a routine, expected occurrence, not an exceptional one, and
  every part of the application that reads this data must be built with that
  assumption, which is a pervasive design constraint, not a localized one.
- Conflict resolution is a real engineering artifact that must exist, be
  tested, and be maintained. A last-writer-wins policy silently discards data.
  A sibling-exposing policy pushes complexity into every client. A CRDT
  restricts the data model. None of these costs disappears, they only move.
- Operational surface area grows. Anti-entropy jobs, hinted handoff queues,
  and vector clock bookkeeping are additional subsystems that can themselves
  fail, drift, or silently stop running, producing a class of incident that
  does not exist in a single-copy system.
- Debugging becomes probabilistic. "Why did the user see the old value" can
  have an answer that depends on which replica happened to serve the read,
  which is a much harder class of bug to reproduce than a deterministic
  single-database inconsistency.

## 11. Failure modes and misuse

**Silent data loss from last-writer-wins on genuinely concurrent writes.**
Symptom, two users report that one of their changes "disappeared" with no
error, and support logs show both writes succeeded individually. Cause, the
conflict resolution strategy picks a single winner by timestamp without
checking whether the writes were causally related, so two concurrent, unrelated
edits collide and one is discarded without anyone being told. Fix, replace
last-writer-wins with vector-clock-based sibling detection for any field where
concurrent edits are expected, or move to a CRDT whose merge is defined to
preserve both contributions, such as a set union for a shopping cart.

**The anti-entropy or repair job silently stops running.** Symptom, staleness
between replicas that used to resolve within seconds now persists for days,
noticed only when a customer complains, not through any alert. Cause, the
convergence mechanism is a background process, and background processes that
never surface a user-facing error when they stop are a classic blind spot,
nobody is watching whether "eventually" is actually arriving. Fix, instrument
and alert on convergence lag directly, the age of the oldest unreconciled
divergence, rather than inferring health only from the absence of user
complaints, per the observability signals in dimension 16 below.

**Treating "eventually consistent" as "consistent enough to skip
read-your-writes handling."** Symptom, a user submits a form, is redirected to
a confirmation or detail page, and the detail page shows the pre-submission
state, producing a support ticket that reads "my change didn't save" when it
in fact did. Cause, the write path and the read path hit different replicas,
and the read arrived before that replica had received the write. Fix, for any
flow where the same actor immediately reads what they just wrote, either route
that specific read to the replica that accepted the write, use a quorum read
that satisfies W + R > N for that operation, or design the UI to optimistically
reflect the write locally rather than re-fetching from a possibly-stale
replica.

**Applying BASE to an operation that requires a hard invariant.** Symptom, an
inventory count goes negative, or two concurrent bookings both succeed for the
same physical seat. Cause, a merge function, or a last-writer-wins policy, was
applied to data whose correctness depends on a global invariant, at most N
units sold, at most one occupant per seat, that cannot be expressed as a
commutative, order-independent merge. Fix, this class of operation belongs
under strict consistency, a single writer, a consensus protocol, or a
serializable transaction, not under BASE, and recognizing which category an
operation falls into before choosing the storage model is the single most
consequential decision in this entire entry.

**Sibling explosion left unresolved.** Symptom, reads against a hot key get
progressively slower and larger over time, and eventually the client library
or the storage engine rejects the key as too large. Cause, a client reads a
key, is supposed to resolve any siblings it observes and write back a single
reconciled value, but a buggy or lazy client writes a new value without
resolving the existing siblings, so the set of concurrent versions grows
without bound on every subsequent write. Fix, every client library that
performs a BASE-style read-then-write cycle must always fold observed siblings
into its write, and the storage layer should cap sibling count and alert well
before the cap is hit.

## 12. Trade-off matrix

| Force | BASE (quorum-tunable) | Strong consistency (single-leader / consensus) | Sequential consistency (Raft/Paxos-backed) | Client-side caching with TTL |
|---|---|---|---|---|
| Availability under partition | High. Minority partitions keep serving | Low. Minority partition typically refuses writes | Low to medium. Only the leader's partition serves writes | High, but staleness is unbounded and unmanaged |
| Write latency | Low, local quorum acknowledges | Higher, waits for leader plus replication | Higher, waits for a quorum consensus round | Very low, no network round trip on cache hit |
| Read freshness | Tunable, R controls the bound | Always current from the leader | Always current, linearizable | Bounded only by TTL, not by causality |
| Conflict handling | Explicit, application or CRDT owns it | Not needed, single writer serializes | Not needed, consensus serializes | Not applicable, no shared write path |
| Operational complexity | High, anti-entropy, hinted handoff, vector clocks | Medium, replication and failover tooling | High, consensus protocol tuning and quorum sizing | Low, but invalidation correctness is its own hard problem |
| Correctness under concurrent writes | Weak by default, strong only with CRDTs | Strong, serialized by the leader | Strong, linearizable | Undefined, caches do not arbitrate writes |
| Best fit | Shopping carts, session state, social feeds, metrics counters | Financial ledgers, inventory with hard limits, seat allocation | Configuration state, leader election, distributed locks | Read-mostly, rarely-changing reference data |

## 13. Related and incompatible patterns

**[CAP theorem](cap-theorem.md).** BASE is the practitioner-facing operating
discipline that follows from choosing availability over consistency in the
CAP theorem's trade-off. CAP proves the trade-off exists and is unavoidable
under partition. BASE describes what a system that has made that choice
actually does, mechanically, to remain available and to converge afterward.
Reading the two together is close to mandatory, because CAP without BASE is an
abstract impossibility result with no operational content, and BASE without CAP
is a set of engineering techniques with no stated justification for why they
are necessary.

**Quorum consensus.** BASE-style systems commonly use partial quorums, W and R
smaller than N, as their availability mechanism, which composes with, but is
distinct from, full-quorum consensus protocols like Raft or Paxos that
guarantee strict linearizability at the cost of requiring a majority to be
reachable for every operation. A BASE system can use quorum arithmetic without
adopting consensus, and the difference between the two is exactly the
difference between "most replicas agree, eventually" and "a majority must
agree, right now, or the operation is refused."

**Saga.** Where BASE resolves inconsistency between replicas of the same
logical data, the Saga pattern resolves the analogous problem across a
sequence of operations spanning multiple services or databases that together
would have needed a single ACID transaction. Both patterns share the same
underlying acceptance, that a distributed system cannot always get atomicity
for free, and both substitute a recovery or compensation mechanism, anti-entropy
for BASE, compensating transactions for Saga, for the synchronous guarantee a
single-machine transaction would have provided.

**[Single Source of Truth](single-source-of-truth.md).** BASE appears, at
first glance, to conflict with the idea of a single source of truth, because
it explicitly permits multiple replicas to hold different values for a
window of time. The two are reconciled by distinguishing the logical source of
truth, the one key, the one intended value, which BASE preserves, from the
physical, momentary state of any one replica, which BASE explicitly allows to
diverge. A BASE system remains a single source of truth at the logical level
precisely because its convergence guarantee is that all replicas eventually
agree on what that one value is.

**[Fail Fast](fail-fast.md).** The two are frequently, and wrongly, treated as
opposites, since BASE seems to say "keep going even when something is wrong."
The reconciliation is that BASE fails fast on the dimension it controls,
availability, by refusing to block a request waiting for an unreachable
replica, while deliberately not failing fast on strict consistency, which it
has already decided to relax. A well-built BASE system still fails fast and
loudly when its own invariants are actually violated, an unresolved sibling
count exceeding its cap, an anti-entropy job that has not run in longer than
its expected interval, rather than failing silently in those cases.

**Incompatible in practice, not in principle, with two-phase commit.** A
system committed to BASE for a given dataset should not simultaneously wrap
that dataset in a two-phase-commit transaction spanning the same replicas for
some operations and rely on quorum-based eventual consistency for others,
because the two protocols make contradictory assumptions about whether a
replica that has not yet acknowledged is "pending," 2PC's view, or simply
"will converge later," BASE's view, and mixing them on the same data produces
exactly the kind of undebuggable partial-commit state both protocols exist to
prevent.

## 14. Refactoring path in and out

**Introducing BASE into a system built on a single ACID database.**

1. Identify the specific operations, not the whole system, that are latency-
   or availability-bound today. Do this by measuring, not guessing, which
   endpoints time out or queue during peak load or partial infrastructure
   failure, per the dimension 3 forces above.
2. For each candidate operation, classify its correctness requirement using
   the applicability test in dimension 4. If it needs a hard invariant, stop,
   it is not a BASE candidate, and the refactor should look elsewhere for
   relief, read replicas with bounded staleness communicated explicitly, or
   caching, rather than BASE.
3. For operations that pass the classification, design the merge function or
   choose the CRDT before writing any replication code. The single most common
   failure in this refactor is standing up quorum reads and writes first and
   discovering only in production that nobody decided what happens when two
   writes conflict.
4. Introduce replication with a conservative W and R, commonly W = R = a
   majority of N, which keeps strong read-your-writes behavior in the common
   case while adding availability headroom, then deliberately test the
   partition case, kill a replica, verify the system remains available and
   the merge function behaves correctly, before loosening W and R further.
5. Build the anti-entropy or read-repair mechanism, and its observability,
   from day one rather than as a later addition, since a BASE system with no
   working convergence path is not a lesser BASE system, it is a broken one.
6. Migrate the specific operations identified in step 1 onto the new
   replicated path, leaving everything else on the original ACID database
   unless and until it independently passes the same classification.

**Removing BASE, moving an operation back to strict consistency.**

1. Confirm the actual driver for removal. The most common honest reasons are
   a discovered hard invariant that the merge function cannot express
   correctly, or an operational cost that turned out to exceed the
   availability benefit gained. Distinguish this from "we are seeing bugs,"
   since most BASE-removal requests trace to a missing or buggy merge
   function rather than to BASE being the wrong model.
2. Freeze new sibling creation for the affected key range by routing all
   writes for it to a single elected replica, or through a consensus
   protocol, while leaving existing reads on the old quorum path.
3. Run the anti-entropy process to completion against the frozen range,
   verifying via the Merkle tree comparison, or an equivalent checksum, that
   every replica agrees before proceeding, since migrating unreconciled
   siblings into a strict-consistency store bakes the ambiguity in
   permanently.
4. Cut reads over to the single writer or consensus-backed path, verify
   correctness against production traffic under shadow or canary conditions,
   and only then decommission the quorum write path for that key range.
5. Keep the merge function and vector clock code available, but marked dead,
   for at least one full retention cycle, in case a downstream consumer still
   depends on reading vector-clock metadata that the migration removed.

## 15. Testing and verification

Testing a BASE system requires deliberately inducing the conditions the
happy-path test suite never exercises, since the entire value of BASE lives in
the failure and concurrency cases.

- **Partition injection tests.** Use a network fault injection tool, or a
  test rig that can drop or delay traffic between specific replica pairs,
  to verify that writes still succeed with W of N replicas reachable, that
  hinted handoff correctly queues and later delivers the missed write, and
  that the client receives the availability guarantee the system claims
  rather than an error.
- **Concurrent write tests.** Deliberately issue two writes to the same key
  from two different coordinators without allowing either to observe the
  other's vector clock first, then assert on the resulting behavior, siblings
  correctly surfaced, or a CRDT merge correctly preserving both contributions,
  or a documented, tested last-writer-wins outcome if that is the chosen
  policy. A test suite that never produces a genuine concurrent write has not
  tested the part of the system that BASE exists to handle.
- **Convergence tests.** After inducing a partition and allowing conflicting
  writes, heal the partition and assert that all replicas converge to the
  same value within the documented convergence bound, not merely that they
  eventually stop returning errors.
- **Read-your-writes tests for the specific flows that need it.** For any
  user flow where the product requires the writer to immediately see their
  own write, test that flow explicitly against the actual replica topology,
  since this is exactly the case dimension 11 identifies as the most common
  BASE-related support ticket.
- **Sibling accumulation tests.** Write to a key repeatedly without ever
  performing a read-and-reconcile cycle, and assert that the system either
  caps and alerts on sibling count, or that the reconciliation happens
  automatically, rather than allowing unbounded growth.
- **Fault-injection and game-day exercises.** Beyond unit and integration
  tests, a BASE system's real failure modes, the anti-entropy job silently
  stopping, a hinted handoff queue growing unbounded on a node that stays
  down too long, are operational and are best surfaced by periodically and
  deliberately inducing them in a controlled environment and verifying the
  alerting fires correctly, rather than relying solely on pre-deployment
  test suites.

## 16. Observability signals

A healthy BASE system's dashboards should make the following visible, and a
BASE system with none of these signals should be treated as unverified, since
"eventually consistent" without a measured "eventually" is an unfalsifiable
claim.

- **Replica staleness, per replica pair.** The measured lag, in time or in
  version-vector distance, between the most current replica and the least
  current one for a given key range. This is the single most important BASE
  metric and should have an alerting threshold, not just a dashboard.
- **Anti-entropy job liveness and completion time.** Whether the background
  repair process ran within its expected schedule, and how long a full pass
  over the keyspace takes, trending over time. A silently stalled repair job
  is the single most common cause of BASE systems drifting from "eventually
  consistent" to simply "inconsistent," per dimension 11.
- **Hinted handoff queue depth and age.** How many writes are currently
  queued as hints waiting for an unreachable replica to return, and how old
  the oldest hint is. A queue that only grows indicates a replica that is
  down longer than the system's handoff retention window, which risks losing
  the hinted write entirely.
- **Sibling count distribution.** The number of concurrent, unreconciled
  versions observed per key, as a distribution across all keys, not just an
  average, since a small number of pathologically hot keys accumulating
  siblings is the typical failure shape.
- **Quorum failure rate.** How often a read or write fails to achieve its
  configured R or W within a timeout, broken out by cause, replica down
  versus replica slow versus network partition, which distinguishes a
  genuine availability event from a latency regression.
- **Read repair and reconciliation counts.** How frequently reads trigger a
  read-repair write-back, as a proxy for how often replicas are actually
  diverging in normal operation, which should correlate with, and cross-check
  against, the replica staleness metric above.

## 17. Security and privacy implications

BASE's soft-state window has direct, concrete privacy and security
consequences that a purely functional description of the pattern omits.

A revocation or deletion is itself a write, and under BASE it is subject to
the same convergence delay as any other write. A user who revokes access, or
requests deletion of their data under a regulation such as GDPR, may have that
revocation accepted by the system, satisfying "basically available," while a
stale replica continues to serve the old, un-revoked or un-deleted state for
some window before convergence completes. Any system handling access
revocation or right-to-erasure requests under BASE must treat the
convergence bound as a compliance-relevant number, not merely a performance
metric, and in some jurisdictions and data categories this window may itself
need to be small enough, or bounded and disclosed, to satisfy the regulation.

Conflict resolution logic is a place where security-relevant fields can be
merged incorrectly if the merge function was designed for a different field on
the same record. A CRDT or sibling-resolution strategy that correctly unions a
shopping cart's item list will silently corrupt a field like "account
locked," where the correct merge is not a union or a last-writer-wins pick but
an explicit "if either replica believes the account is locked, the merged
state is locked," a fail-safe merge rather than a naive one. Applying a
generic conflict resolution policy uniformly across every field on a record,
rather than choosing the resolution strategy per field based on its security
implications, is a common source of this class of bug.

Sloppy quorums and hinted handoff mean that, during a partition, a write can
be temporarily held by a node that is not one of the key's normal replicas.
That stand-in node briefly possesses the data, which widens the set of
machines that hold a copy of potentially sensitive information beyond the
system's steady-state replica set, and any encryption-at-rest, access-control,
or audit-logging design for the data must account for the stand-in node as a
legitimate, if temporary, holder of the data, not treat it as an anomaly to
special-case away.

## 18. References

1. Dan Pritchett, "BASE. An ACID Alternative," ACM Queue, volume 6, issue 3,
   pages 48 to 55, May 2008.
   [queue.acm.org/detail.cfm?id=1394128](https://queue.acm.org/detail.cfm?id=1394128),
   verified 2026-08-02.
2. Eric Brewer, "CAP Twelve Years Later. How the 'Rules' Have Changed," IEEE
   Computer, volume 45, issue 2, pages 23 to 29, 2012, DOI 10.1109/MC.2012.37,
   recounting the substance of Brewer's PODC 2000 keynote.
   [sites.cs.ucsb.edu/~rich/class/cs293b-cloud/papers/brewer-cap.pdf](https://sites.cs.ucsb.edu/~rich/class/cs293b-cloud/papers/brewer-cap.pdf),
   verified 2026-08-02.
3. Giuseppe DeCandia et al., "Dynamo. Amazon's Highly Available Key-value
   Store," Proceedings of the 21st ACM Symposium on Operating Systems
   Principles (SOSP), October 2007, summarized by co-author Werner Vogels in
   "Amazon's Dynamo," All Things Distributed, 2007-10-02.
   [allthingsdistributed.com/2007/10/amazons_dynamo.html](https://www.allthingsdistributed.com/2007/10/amazons_dynamo.html),
   verified 2026-08-02.
4. DataStax, "About data consistency," Apache Cassandra 2.1 documentation,
   describing tunable per-operation consistency levels and last-writer-wins
   conflict resolution.
   [docs.datastax.com/en/cassandra-oss/2.1/cassandra/dml/dmlAboutDataConsistency.html](https://docs.datastax.com/en/cassandra-oss/2.1/cassandra/dml/dmlAboutDataConsistency.html),
   verified 2026-08-02.
5. Baeldung, "Consistency Levels in Cassandra."
   [baeldung.com/cassandra-consistency-levels](https://www.baeldung.com/cassandra-consistency-levels),
   verified 2026-08-02.
6. Basho, Riak KV Data Types documentation, describing built-in CRDT support
   as an alternative to raw sibling resolution.
   [docs.riak.com/riak/kv/latest/developing/data-types/index.html](https://docs.riak.com/riak/kv/latest/developing/data-types/index.html),
   verified 2026-08-02.
7. This repository, [CAP Theorem](cap-theorem.md), for the impossibility
   result BASE is the constructive, operational answer to.

## Code examples

The three samples below model the same scenario from different angles of the
BASE contract, a small replicated key-value store with vector-clock causality
tracking, sibling detection on concurrent writes, and a quorum read and write
path. All three were run against the toolchain available on this machine.

### TypeScript, vector-clock causality and sibling detection

Models the soft-state and eventual-consistency letters directly. A value can
have multiple concurrent siblings, and the system can tell a causal update
apart from a genuine conflict.

```typescript
type VClock = Record<string, number>;

interface Versioned<T> {
  value: T;
  clock: VClock;
}

function compare(a: VClock, b: VClock): "before" | "after" | "concurrent" | "equal" {
  let aLess = false;
  let bLess = false;
  const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
  for (const k of keys) {
    const av = a[k] ?? 0;
    const bv = b[k] ?? 0;
    if (av < bv) aLess = true;
    if (av > bv) bLess = true;
  }
  if (!aLess && !bLess) return "equal";
  if (aLess && !bLess) return "before";
  if (!aLess && bLess) return "after";
  return "concurrent";
}

class Replica<T> {
  private siblings: Versioned<T>[] = [];
  constructor(private readonly id: string) {}

  write(value: T, baseClock: VClock): void {
    const clock: VClock = { ...baseClock, [this.id]: (baseClock[this.id] ?? 0) + 1 };
    const survivors = this.siblings.filter(
      (s) => compare(s.clock, clock) !== "before"
    );
    this.siblings = [...survivors, { value, clock }];
  }

  read(): Versioned<T>[] {
    return this.siblings;
  }
}

function mergeVClocks(clocks: VClock[]): VClock {
  const merged: VClock = {};
  for (const c of clocks) {
    for (const [k, v] of Object.entries(c)) {
      merged[k] = Math.max(merged[k] ?? 0, v);
    }
  }
  return merged;
}

const r1 = new Replica<string[]>("r1");
r1.write(["A", "B"], {});
const base = r1.read()[0].clock;

r1.write(["A", "B", "C"], base);
const r2 = new Replica<string[]>("r2");
r2.write(["A", "B"], base);
r2.write(["A", "B", "D"], base);

const observed = [...r1.read(), ...r2.read()];
console.log("siblings observed:", observed.length);
for (const s of observed) {
  console.log(JSON.stringify(s.clock), s.value);
}

const mergedItems = Array.from(
  new Set(observed.flatMap((s) => s.value))
).sort();
const mergedClock = mergeVClocks(observed.map((s) => s.clock));
console.log("union merge result:", mergedItems, JSON.stringify(mergedClock));
```

### Python, quorum write and read with W plus R over N

Models the basically-available letter. A write succeeds once W of N replicas
acknowledge, even when one replica is unreachable, and a quorum read shows how
W plus R greater than N bounds staleness without eliminating it.

```python
from dataclasses import dataclass, field


@dataclass
class Replica:
    name: str
    reachable: bool = True
    value: str | None = None
    version: int = 0

    def write(self, value: str, version: int) -> bool:
        if not self.reachable:
            return False
        self.value = value
        self.version = version
        return True


@dataclass
class QuorumStore:
    replicas: list[Replica]
    w: int
    r: int

    def write(self, value: str) -> bool:
        version = max((rep.version for rep in self.replicas), default=0) + 1
        acks = sum(1 for rep in self.replicas if rep.write(value, version))
        return acks >= self.w

    def read(self) -> tuple[str | None, bool]:
        responses = [
            (rep.value, rep.version)
            for rep in self.replicas
            if rep.reachable
        ]
        if len(responses) < self.r:
            return None, False
        latest = max(responses, key=lambda pair: pair[1])
        return latest[0], True


n = 3
w = 2
r = 2
replicas = [Replica(f"r{i}") for i in range(n)]
store = QuorumStore(replicas=replicas, w=w, r=r)

assert store.write("cart={A,B}") is True

replicas[2].reachable = False
ok = store.write("cart={A,B,C}")
print("write with one replica down, W=%d of N=%d:" % (w, n), ok)
assert ok is True

value, satisfied = store.read()
print("quorum read result:", value, "quorum satisfied:", satisfied)
assert w + r > n
assert satisfied is True

replicas[2].reachable = True
replicas[2].write("cart={A,B,C}", max(rep.version for rep in replicas))
print("all replicas converged:", all(rep.value == "cart={A,B,C}" for rep in replicas))
```

### Go, a grow-only CRDT counter that merges without coordination

Models the eventually-consistent letter with a mathematical guarantee. A
G-Counter is commutative, associative, and idempotent, so any merge order
across any number of replicas converges to the same total.

```go
package main

import "fmt"

type GCounter struct {
	counts map[string]int
}

func NewGCounter() *GCounter {
	return &GCounter{counts: make(map[string]int)}
}

func (g *GCounter) Increment(replicaID string, amount int) {
	g.counts[replicaID] += amount
}

func (g *GCounter) Value() int {
	total := 0
	for _, v := range g.counts {
		total += v
	}
	return total
}

func Merge(a, b *GCounter) *GCounter {
	merged := NewGCounter()
	for id, v := range a.counts {
		if v > merged.counts[id] {
			merged.counts[id] = v
		}
	}
	for id, v := range b.counts {
		if v > merged.counts[id] {
			merged.counts[id] = v
		}
	}
	return merged
}

func main() {
	replicaA := NewGCounter()
	replicaB := NewGCounter()
	replicaC := NewGCounter()

	replicaA.Increment("a", 5)
	replicaB.Increment("b", 3)
	replicaC.Increment("c", 7)

	pathOne := Merge(Merge(replicaA, replicaB), replicaC)
	pathTwo := Merge(replicaA, Merge(replicaB, replicaC))
	pathThree := Merge(Merge(replicaC, replicaA), replicaB)

	fmt.Println("merge order (A,B) then C ->", pathOne.Value())
	fmt.Println("merge order A then (B,C) ->", pathTwo.Value())
	fmt.Println("merge order (C,A) then B ->", pathThree.Value())

	if pathOne.Value() != pathTwo.Value() || pathTwo.Value() != pathThree.Value() {
		panic("CRDT merge is not order-independent, something is wrong")
	}
	fmt.Println("all merge orders converged to the same total: 15")

	replayed := Merge(pathOne, replicaA)
	fmt.Println("re-merging an already-applied update stays idempotent:", replayed.Value())
}
```

No C#, Kotlin, Java, or Rust sample is included. The pattern's canonical
demonstrations, quorum arithmetic, vector clocks, and CRDT merges, are equally
idiomatic across nearly every general-purpose language, so the three languages
above were chosen for toolchain availability and coverage across a dynamically
typed, a statically typed with a runtime, and a compiled systems language,
rather than because the pattern is language-specific in any of the omitted
languages.
