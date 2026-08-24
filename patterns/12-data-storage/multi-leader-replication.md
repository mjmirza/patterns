---
name: Multi-Leader Replication
slug: multi-leader-replication
family: 12-data-storage
category: Data and Storage
aliases: [Multi-Master Replication, Active-Active Replication, Master-Master Replication, Multi-Primary Replication]
first_described: "Kleppmann, Designing Data-Intensive Applications, 2017, chapter 5"
maturity: established
related: [single-leader-replication, leaderless-replication, crdt, event-sourcing, conflict-free-replicated-data-type, saga, outbox-pattern]
incompatible_with: [strict-serializability, single-writer-invariant]
verified: 2026-08-02
---

## 1. Name, aliases, and lineage

The canonical name in the database-internals literature is multi-leader
replication. Martin Kleppmann uses this exact term as a chapter heading in
Designing Data-Intensive Applications, distinguishing it from single-leader
replication and leaderless replication as the three families of replication
topology (Kleppmann, Designing Data-Intensive Applications, O'Reilly, 2017,
chapter 5, "Replication"). The pattern is also widely called multi-master
replication or active-active replication in vendor documentation and older
distributed-systems literature, and multi-primary in more recent MySQL and
PostgreSQL documentation, which moved away from master and slave
terminology around 2020. All four names describe the same structural idea.
More than one node in a replicated data store can accept writes for the
same logical dataset, and each node propagates its writes to the others.

The idea predates any single named source. Multi-master replication schemes
existed in commercial relational databases in the 1990s. Oracle's advanced
replication, Sybase's replication server, and Lotus Notes' document
replication all shipped write-anywhere replication before 2000, so unlike a
Gang of Four pattern this is not attributable to one paper or one team.
What Kleppmann's chapter did was give the pattern a settled name and a
settled place in a three-way taxonomy against single-leader and leaderless
replication, which is the framing this repository follows, because it is
the framing that lets an engineer choose correctly between the three rather
than reaching for whichever one they read about most recently.

CouchDB's own documentation uses the phrase "multi-master replication" for
its own bidirectional, revision-tracked replication model (CouchDB
documentation, "Replication Protocol", https://docs.couchdb.org/en/stable/replication/protocol.html,
verified 2026-08-02). MySQL's Group Replication documentation uses
"multi-primary mode" as the formal configuration term (MySQL 8.0 Reference
Manual, "Multi-Primary Mode", https://dev.mysql.com/doc/refman/8.0/en/group-replication-multi-primary-mode.html,
verified 2026-08-02). This entry treats multi-master, active-active, and
multi-primary as synonyms of multi-leader and uses multi-leader as the
default term, following the taxonomy this repository standardizes on.

## 2. Problem and context

A team runs a database that serves write traffic from more than one
geographic region, or from more than one autonomous system that must keep
working during a network partition between them. Single-leader replication
solves availability for reads by fanning followers out from one leader, but
every write still has to reach that one leader, cross whatever network
distance and however many partitions separate the writer from it, and wait
for the leader to accept the write before the writer can proceed. When the
leader is in one datacenter and half the writers are on another continent,
every write pays a full round trip of inter-region latency, and when the
network between the writer and the leader is down, writes from that region
stop entirely even though the region's local database is healthy and
reachable to local clients.

Two concrete situations create the need for multi-leader replication. The
first is a globally distributed application, for example a SaaS product
with users in Europe, North America, and Asia, where write latency for a
European user going to a US-based leader is measured in the hundreds of
milliseconds, enough to make an interactive product feel sluggish, and
where the business wants each region to keep functioning if the
transatlantic link fails. The second is offline-first client software, for
example a mobile calendar app, a collaborative note-taking tool, or a
version-control system, where each device's local copy of the data is
itself a leader that accepts writes while the device is disconnected from
every other copy, and reconciliation happens whenever connectivity returns.

In both situations the alternative topologies fail the requirement in a
specific, nameable way. Single-leader replication fails the multi-region
case on write latency and fails the offline case entirely, because there is
by definition no reachable leader while offline. Leaderless replication
(quorum-based systems such as Cassandra or Riak) solves the availability
problem differently, by having every replica independently accept writes
for the keys it owns and using read repair plus hinted handoff to converge,
but it does not use the leader-then-fan-out replication topology at all,
and it generally trades away the kind of ordered, log-shipping replication
that multi-leader systems retain per node. Apache Cassandra's own
documentation states that "every replica can independently accept
mutations to every key that it owns" (Apache Cassandra documentation,
"Dynamo", https://cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html,
verified 2026-08-02), which is the leaderless model, distinct from the
multi-leader model where each participating node is itself a leader for
the whole dataset with its own log. Multi-leader replication targets the
middle ground. Keep the leader-based replication topology, so each node
still has a coherent write-ahead log and a well-understood single-node
consistency model, but let more than one node in the topology hold the
leader role at once.

## 3. Forces

This dimension is largely engineering judgement about which force matters
most in which deployment shape, stated as reasoning rather than as a
sourced claim, except where a specific vendor behavior is cited.

The central force is write availability and write latency against
consistency. A single leader gives a total order for every write, which
makes reasoning about the resulting data trivial, because there is one
history. Multiple leaders give up that total order, because two leaders
can each accept a conflicting write to the same record within the same
window before either has heard of the other's write, and no amount of
clever engineering removes this, it only changes how the conflict is
detected and resolved after the fact. A team choosing multi-leader
replication is trading a provably consistent single history for lower
write latency and continued write availability during a partition, and
every other design decision in this pattern flows from having made that
trade deliberately.

Coupling and operational surface area are the second force. A
single-leader topology has one thing to get right, leader election and
failover. A multi-leader topology multiplies this by needing conflict
detection, conflict resolution semantics that the whole engineering
organization has to understand and agree with, and replication topology
management, which node replicates to which, and what happens when a link
in that topology is partitioned. The operability cost is not hypothetical.
It shows up as an entire extra class of bug, the silent data-loss-on-
conflict bug, that a single-leader system structurally cannot produce.

Cost and team topology matter in the multi-region case specifically.
Running a leader per region means running full database infrastructure,
monitoring, and on-call coverage per region, which is a materially larger
operational footprint and cost than running one leader and read replicas.
Teams choose multi-leader replication when the business case for regional
write latency or regional write availability is strong enough to fund that
footprint, not as a default choice.

Cognitive load is the force multi-leader replication most consistently
loses on. A single-leader system's failure modes are learnable by most
engineers on a team within a few incidents. A multi-leader system's
failure modes, a conflict silently resolved the wrong way, a replication
link that has been down for six hours without anyone noticing, a write
that appears to succeed locally and then disappears when the conflict
resolver picks the other side, require a genuinely different mental model,
and teams that adopt multi-leader replication without training their whole
engineering organization on that model consistently under-invest in the
observability this pattern needs, see dimension 16.

## 4. Applicability and non-applicability

Reach for multi-leader replication in these cases.

- Writers are genuinely distributed across regions or across disconnected
  devices, and the business requirement is that each location keeps
  accepting writes even when it cannot reach the others, not merely that
  reads are fast locally.
- The application's data model tolerates eventual consistency and the
  application team is willing to design explicit conflict-resolution
  semantics, because the pattern forces this design work whether or not
  the team wants to do it.
- The write conflict rate is genuinely low, either because different
  regions or devices touch mostly disjoint data, a common case being
  users in Europe mostly editing their own records rather than records
  owned by users in Asia, or because the conflicting field has a
  resolution rule that is obviously correct, a monotonically increasing
  counter, or a last-writer-wins timestamp on a field where losing an
  update is an acceptable cost.
- The product is explicitly offline-first, where a leader-per-device
  model is not a scaling choice but the only model that satisfies the
  requirement that the product works with no network at all.

Do NOT reach for multi-leader replication in these cases.

- The application needs strong consistency for the conflicting writes, for
  example financial ledger entries, inventory counts that must never go
  negative, or any invariant that must hold across concurrent writers.
  Multi-leader replication cannot enforce a cross-node invariant at write
  time, only detect and resolve a violation after both writes have already
  landed locally, which is too late for many financial and inventory
  invariants. Use single-leader replication, or a consensus-based
  single-writer-per-key design, instead.
- The write conflict rate would be high. If the same records are
  frequently written from more than one leader within the replication lag
  window, the system spends more engineering and operational effort
  resolving conflicts than it saves in latency, and the conflict-resolution
  logic itself becomes a source of subtle bugs. This is the single most
  common misapplication of the pattern. Teams adopt it for latency without
  first measuring how often two leaders would actually collide on the same
  key.
- The team does not have the operational maturity to run and monitor
  multiple leaders, detect replication lag and topology partitions, and
  triage conflict-resolution outcomes. A multi-leader deployment with no
  one watching replication lag is not more available, it is silently
  drifting apart.
- A single-leader deployment with read replicas already satisfies the
  actual latency requirement. Most read-heavy applications with a
  geographically distributed read audience but a small, latency-tolerant
  write audience, an admin console, an internal tool, a low-frequency
  content-publishing workflow, do not need multi-leader replication at
  all. They need read replicas near the readers and a single leader for
  writes.
- Strict serializability or any global total order over writes is a
  requirement. This is listed under incompatible_with because it is a
  structural incompatibility, not a tuning problem. A system with more
  than one node accepting writes concurrently, propagating asynchronously,
  cannot by construction produce a single global total order without
  adding a synchronous consensus step for every write, at which point it
  is a single-leader (or leaderless-with-quorum) system with extra steps,
  not a multi-leader system anymore.

## 5. Structure

The participants in a multi-leader replication topology are as follows.

- **Leader node.** A database instance that accepts both reads and writes
  for the full dataset, or its assigned partition of the dataset, and
  maintains its own write-ahead log or oplog of the writes it has accepted
  locally. In multi-leader replication there are two or more of these,
  typically one per datacenter, region, or, in the offline-first case, one
  per client device.
- **Replication link.** The channel over which one leader ships its local
  write log to another leader. Topology matters here. Links can form an
  all-to-all mesh, where every leader replicates directly to every other
  leader, a circular topology, leader A to B to C back to A, or a star
  topology, where every leader replicates through one hub. Kleppmann
  specifically flags circular and star topologies as needing a mechanism
  to prevent infinite replication loops, typically by tagging each write
  with the identifier of the node that originated it and having a node
  refuse to re-apply a write it recognizes as its own (Kleppmann,
  Designing Data-Intensive Applications, 2017, chapter 5, section
  "Multi-Leader Replication Topologies").
- **Version metadata.** Per-record metadata attached to each write that
  lets a receiving leader determine causal relationships between two
  versions of the same record. This is a vector clock, a version vector, a
  Lamport timestamp, or in CouchDB's case a revision tree of MVCC tokens
  shaped `N-sig`, where N is a monotonically increasing generation number
  and sig is a signature of the document content, which lets CouchDB
  represent multiple concurrent leaf revisions of the same document
  explicitly rather than silently discarding one (CouchDB documentation,
  "Replication Protocol", verified 2026-08-02).
- **Conflict detector.** The component, usually embedded in the
  replication application logic on the receiving leader, that determines
  whether an incoming write from another leader conflicts with a write
  already applied locally, by comparing version metadata to see if the two
  writes are causally concurrent, neither happened before the other,
  rather than one being a strict successor of the other.
- **Conflict resolver.** The component that decides the final value of a
  record once a conflict is detected. This can be automatic, last-writer-
  wins by timestamp, a merge function, a CRDT merge operator, or it can
  surface the conflict to the application or to a human, as CouchDB does
  by keeping both leaf revisions in the revision tree until the
  application picks a winner.
- **Client or writer.** The application code or end user issuing a write.
  In the multi-leader model the writer is directed to its geographically
  or logically nearest leader, and in the offline-first model the writer
  is simply whatever process is running locally on the disconnected
  device.

## 6. ASCII structure diagram

```
MULTI-LEADER REPLICATION
all-to-all mesh, 3 regions

+------------------+
| Leader A (EU)    |
| local WAL / log  |
| version metadata |
+------------------+
        <-- replication link -->
+------------------+
| Leader B (US)    |
| local WAL / log  |
| version metadata |
+------------------+
        <-- replication link -->
+------------------+
| Leader C (APAC)  |
| local WAL / log  |
| version metadata |
+------------------+
        <-- replication link, A and C connect directly too -->

Each leader accepts local reads and writes. Each
replication link is async, may lag, may partition
independently. A write applied at A is queued to
replicate to both B and C. A write applied concurrently
at B for the same record is a conflict once it arrives
at A or C, neither write happened before the other in
the version metadata's partial order.
```

## 7. Dynamics

```
        CONCURRENT WRITE AND CONFLICT RESOLUTION, TWO LEADERS

  Leader A (EU)                                      Leader B (US)
  --------------                                      --------------
  t0  write(record=42, val="red")
      commit locally
      version = {A:1}
                                                       t0  write(record=42, val="blue")
                                                           commit locally
                                                           version = {B:1}
  t1  replicate to B  ---------------------------->
                                                       t1  receive write from A
                                                           compare {A:1} vs local {B:1}
                                                           neither is an ancestor -> CONCURRENT
                                                           CONFLICT DETECTED
  t2  receive write from B  <----------------------
      compare {B:1} vs local {A:1}
      neither is an ancestor -> CONCURRENT
      CONFLICT DETECTED

  Both leaders now independently resolve the same conflict.
  t3  resolver picks a winner (LWW timestamp, app-level merge,
      or surface both to the client as siblings)
      -> if the resolver is deterministic and given the same
         inputs on both sides, A and B converge to the same value
      -> if the resolver is NOT deterministic (for example, wall
         clock LWW with clock skew between A and B), A and B may
         converge to DIFFERENT winners, which is a silent
         disagreement bug, not a crash
```

The critical property this diagram makes visible is that conflict
resolution must run, and must reach the same answer, on every leader that
observes the conflict independently, with no coordinator to arbitrate.
This is why resolution functions for multi-leader systems are required to
be commutative and deterministic given the same two conflicting versions,
regardless of which leader received which write first, which is exactly
the mathematical property that Conflict-free Replicated Data Types, see
dimension 13, are built to guarantee.

## 8. Implementation variants

**Last-writer-wins by timestamp.** Every write carries a timestamp, wall
clock or a hybrid logical clock, and on conflict the write with the higher
timestamp wins, the other is discarded. This is the variant Azure Cosmos DB
uses by default for its multi-region-write accounts. Its own documentation
states that "this resolution policy, by default, uses a system-defined
timestamp property. If two or more items conflict on insert or replace
operations, the item with the highest value for the conflict resolution
path becomes the winner" (Microsoft Learn, "Conflict Resolution Types and
Resolution Policies, Azure Cosmos DB", https://learn.microsoft.com/en-us/azure/cosmos-db/conflict-resolution-policies,
verified 2026-08-02). This is the cheapest variant to implement and the
most dangerous to use blindly, because a discarded write is silently
deleted data, and clock skew between leaders, or, in the mobile case, a
device with a wrong system clock, can make an objectively later write lose
to an earlier one.

**Custom merge procedure.** The application supplies a deterministic
function that takes both conflicting versions and produces a merged
result, rather than picking one whole version as the winner. Azure Cosmos
DB supports this as its "Custom" resolution policy, which registers a
merge stored procedure invoked automatically under a database transaction
when a conflict is detected, with an exactly once execution guarantee for
that procedure (Microsoft Learn, "Conflict Resolution Types and Resolution
Policies", verified 2026-08-02). This variant preserves more information
than last-writer-wins, for example merging two concurrent edits to
different fields of the same record rather than discarding one edit
entirely, at the cost of the application team having to write and
exhaustively test that merge function for every record type that can
conflict.

**Surface conflicts to the application or user.** Rather than resolving
automatically, the database keeps every conflicting version and returns
all of them to the application, which decides. CouchDB does this by
keeping multiple leaf revisions in a document's revision tree after a
conflicting replication, requiring the application to query for conflicts
and pick a winning revision explicitly (CouchDB documentation,
"Replication Protocol", verified 2026-08-02, which documents that
"documents may have multiple leaf revisions... due to concurrent
updates"). Git's merge conflict markers are the most familiar instance of
this variant outside the database world. This is the safest variant for
correctness because no data is silently discarded, and the most expensive
in engineering effort because every conflicting record type needs a
resolution UI or a resolution API.

**Multi-primary with automatic per-transaction rollback.** MySQL Group
Replication in multi-primary mode, with
`group_replication_single_primary_mode=OFF`, lets every compatible group
member "process write transactions, even if they are issued concurrently",
using a certification-based protocol. A transaction is optimistically
executed locally, and at commit time the group votes on a global
certification order using Paxos-based total order broadcast. If the
transaction would conflict with one already certified, it is rolled back
on the node that lost the race rather than silently applied (MySQL 8.0
Reference Manual, "Multi-Primary Mode",
https://dev.mysql.com/doc/refman/8.0/en/group-replication-multi-primary-mode.html,
verified 2026-08-02). This is a structurally different variant from the
other three, because it detects conflicts synchronously before commit
rather than asynchronously after both writes have already been applied
locally, at the cost of every writer paying the latency of a group-wide
certification round trip, which erodes some of the local-write-latency
benefit that motivates choosing multi-leader replication in the first
place. It sits closer to a synchronously replicated single-writer-per-key
system than to the asynchronous, offline-tolerant multi-leader systems
described above, and teams choosing it should understand they are trading
availability during a network partition, a certification vote needs a
majority of the group reachable, for stronger consistency than the
asynchronous variants provide.

**Conflict-free Replicated Data Types (CRDTs).** Rather than resolving a
conflict after the fact, the data structure itself is designed so that any
two divergent replicas can be merged with a mathematically commutative,
associative, and idempotent merge operation, guaranteeing convergence with
no conflict-detection step needed at all. This variant is covered in depth
in its own entry, see dimension 13, and is increasingly the default choice
for new multi-leader systems built after roughly 2015, because it removes
the class of bug where two leaders' resolvers disagree.

## 9. Known production uses

**Apache CouchDB.** CouchDB's HTTP replication protocol is explicitly
designed for multi-master replication between any two CouchDB instances,
or between CouchDB and compatible databases such as PouchDB, using MVCC
revision trees to represent and preserve conflicting document versions
rather than silently overwriting one. This is documented in CouchDB's
official Replication Protocol documentation, which describes the revision
numbering and multi-leaf-revision behavior directly (CouchDB
documentation, "Replication Protocol", https://docs.couchdb.org/en/stable/replication/protocol.html,
verified 2026-08-02).

**MySQL Group Replication, multi-primary mode.** Multi-primary mode is a
documented, first-party configuration of MySQL's Group Replication
plugin, in production use wherever operators set
`group_replication_single_primary_mode=OFF`, letting every group member
accept writes concurrently with certification-based conflict detection at
commit time (MySQL 8.0 Reference Manual, "Multi-Primary Mode", verified
2026-08-02).

**Azure Cosmos DB.** Cosmos DB's multi-region-write feature is a
production, generally-available capability where an account configured
with multiple write regions accepts concurrent writes to the same item in
more than one region, and resolves the resulting insert, replace, and
delete conflicts through the Last-Write-Wins or Custom policies described
in dimension 8 (Microsoft Learn, "Conflict Resolution Types and
Resolution Policies", verified 2026-08-02).

**Git and other content-addressed version control systems.** Every clone
of a Git repository is a full leader. It accepts local commits
independently of every other clone, and reconciliation between clones
happens through an explicit merge or rebase step that surfaces
conflicting hunks to the developer when Git's automatic three-way merge
cannot resolve them unambiguously. This is the "surface conflicts to the
application" variant from dimension 8 operating at the scale of a
distributed version control system rather than a database, and it is the
multi-leader system most working engineers have direct, daily hands-on
experience with, which makes it a useful teaching analogy even though
this entry does not treat source control as a database replication
topology in the formal sense.

## 10. Consequences

Positive consequences follow.

- Writers get local write latency, because a write only has to reach the
  nearest leader, not a leader that may be a continent away, which
  concretely improves interactive application responsiveness for
  geographically distributed users.
- Each leader, and by extension each region or device, continues to accept
  writes during a network partition that isolates it from the other
  leaders, which is a genuine availability property that single-leader
  replication structurally cannot provide for writes.
- The topology tolerates the permanent or long-term loss of any single
  leader, or the link to it, without losing write capability elsewhere,
  which matters for offline-first products where the other copies being
  unreachable is not an edge case but the normal operating condition.

Negative consequences follow.

- The system gives up a global total order over writes. Any invariant
  that spans records that could be written concurrently on different
  leaders, a unique constraint, a monotonic counter that must never
  decrease, a balance that must never go negative, can be violated
  between the moment both leaders locally accept conflicting writes and
  the moment the conflict is detected and resolved, and during that
  window every reader of either leader can observe the violated
  invariant.
- Conflict resolution is a second, independent place where application
  logic can be wrong, in addition to the primary write logic, and bugs in
  it manifest as silent, hard to reproduce data loss or data disagreement
  between replicas rather than as a crash or a visible error, which makes
  them disproportionately expensive to diagnose after the fact.
- Operational complexity roughly multiplies with the number of leaders.
  Each additional leader is additional infrastructure, additional
  replication links to monitor for lag and partition, and additional
  surface area for the topology-loop problem described in dimension 5.

## 11. Failure modes and misuse

This dimension draws on documented failure classes plus engineering
experience with replicated systems generally, stated as judgement rather
than as universally sourced fact except where a specific behavior is
cited.

**Two regions show different values for the same record, and neither is
obviously wrong.** Symptom. Reading the same record from two leaders
returns two different values that both look plausible. Cause. Last-writer-
wins conflict resolution combined with clock skew between the two
leaders, so the write that was objectively issued later loses because its
originating leader's clock was behind. Fix. Use a hybrid logical clock or
a monotonic per-node counter composed with the wall-clock timestamp
rather than raw wall-clock time alone, and monitor clock skew between
leaders as a first-class operational metric, not an assumption.

**A record silently reverts to an older value some time after an update,
with no error anywhere.** Symptom. A field a user recently changed appears
to revert to its previous value minutes or hours later. Cause. A delayed
replication message carrying an older write arrives and is applied after
a newer write, because the conflict detector's version metadata was not
correctly compared, commonly because a node was restored from a backup
that reset its version vector, making the restored node's subsequent
writes look causally older than they actually are. Fix. Never reset or
regenerate version metadata, vector clocks or revision generations, on
restore. Restore the metadata alongside the data, and treat any node whose
version metadata had to be manually reconstructed as suspect until a full
re-sync against a trusted peer confirms convergence.

**Replication between two leaders silently stops making progress,
noticed only when a customer reports stale data days later.** Symptom. A
customer in one region sees data that is days out of date while every
other region is current. Cause. A replication link failure, a network
partition, a credential expiry, a schema change on one side that the
replication protocol cannot represent, that does not raise any alert
because the system was designed with the availability property that each
leader keeps working during a partition, and no one built the
complementary observability that would surface that this leader has been
unable to reach that leader for six hours. Fix. Replication lag and
last-successful-replication-timestamp per link must be a monitored,
alerted metric, see dimension 16, because in a multi-leader system,
silence from a link is not distinguishable from health without explicit
instrumentation.

**The same write appears to loop between three or more leaders
indefinitely, or storage grows unboundedly.** Symptom. A single logical
write results in an ever-growing number of duplicate replication events
observed on a circular or star topology. Cause. The topology, per
dimension 5, has no mechanism to prevent a node from re-propagating a
write it already received from elsewhere, so the write circulates the
topology forever. Fix. Tag every write with its originating node
identifier and have every node refuse to re-apply or re-forward a write
whose origin tag it already applied, which is the mechanism Kleppmann
specifically calls out as necessary for non-mesh topologies (Kleppmann,
Designing Data-Intensive Applications, 2017, chapter 5).

**Adopting multi-leader replication for a low-write-latency requirement,
then finding the correctness cost outweighed the benefit.** Symptom.
Write latency did not measurably improve, or correctness incidents
increased, with no clear win to show for the added complexity. Cause. The
team measured expected read latency improvement but never measured the
actual concurrent-write conflict rate before committing to the pattern,
so the operational and cognitive cost from dimension 3 was paid without
the availability benefit ever being needed in practice, because the
application's actual write pattern rarely if ever had two leaders touch
the same record concurrently, meaning single-leader replication with
regional read replicas would have delivered the same practical outcome at
a fraction of the complexity. Fix. This is a misuse of the pattern's
applicability criteria in dimension 4, and the fix is process, not code.
Measure the concurrent-conflict rate against production-shaped traffic
before choosing multi-leader over single-leader-with-read-replicas.

## 12. Trade-off matrix

| Force | Multi-Leader Replication | Single-Leader Replication | Leaderless Replication (Dynamo-style) |
|---|---|---|---|
| Write latency for a remote writer | Low, writes go to the nearest leader | High, every write crosses the network to the one leader | Low to moderate, writes go to the nearest coordinator and wait for a write quorum |
| Write availability during a partition | Every reachable leader keeps accepting writes | Writers isolated from the leader cannot write at all | Writers can still write as long as a write quorum of replicas is reachable |
| Global write ordering | None, only a partial causal order via version metadata | Total order, defined by the single leader's log | None, order is per key via quorum reads and read repair, not global |
| Conflict handling | Explicit detection and resolution logic required | Not applicable, there is only one writer | Handled per key via quorums, vector clocks, or last-writer-wins at read time |
| Operational complexity | High, multiple leaders and replication topology to run and monitor | Low to moderate, one leader plus followers | Moderate to high, requires tuning read and write quorums, hinted handoff, anti-entropy |
| Cognitive load on engineering team | High, every write path must consider concurrent conflicting writers | Low, one coherent write history | High, eventual consistency and quorum reasoning are pervasive |
| Fit for strong invariants, uniqueness, non-negative balances | Poor, invariants can be violated between concurrent leaders | Good, one writer enforces invariants at write time | Poor for the same reason as multi-leader |

## 13. Related and incompatible patterns

**Single-leader replication.** Multi-leader replication is best understood
as single-leader replication generalized to more than one leader node, and
it inherits single-leader replication's per-node mechanics, write-ahead
logging, follower catch-up, while adding the conflict layer. Teams
frequently start with single-leader replication and evolve to multi-leader
only when a concrete latency or availability requirement forces the
trade. This repository's single-leader-replication entry is the
prerequisite reading for this one.

**Leaderless replication.** A structurally different way to get write
availability without a single leader, using quorum reads and writes
across an undifferentiated set of replicas rather than a small number of
full leaders each with their own log. Cassandra's documentation is
explicit that "every replica can independently accept mutations to every
key that it owns" (Apache Cassandra documentation, "Dynamo", verified
2026-08-02), which sounds superficially similar to multi-leader
replication but differs in a load-bearing way. A leaderless system
typically has many more participating nodes than a multi-leader system
has leaders, coordinates correctness through per-request quorums rather
than through a small, enumerable set of named leaders, and does not
usually give each node its own durable, independently-replayable log the
way each leader in a multi-leader topology does.

**Conflict-free Replicated Data Types (CRDTs).** The mathematically
principled way to build the conflict resolver in dimension 8, replacing
an ad hoc merge function with a data structure whose merge operation is
provably commutative, associative, and idempotent, guaranteeing that
every leader converges to the same value regardless of the order in which
it receives concurrent writes. A multi-leader system built entirely on
CRDTs for its mutable state removes the conflict-detection step from
dimension 6 almost entirely, because a CRDT merge never needs to
determine which write wins, only how to combine them.

**Event Sourcing.** An event-sourced system that appends immutable events
rather than mutating state in place sidesteps some multi-leader conflict
problems by making the append itself commutative, two leaders each
appending a different event to the same stream is not a conflict, both
events happened and both are kept, but it reintroduces the ordering
problem one level up, in how the events from different leaders are
interleaved into a single causally consistent view.

**Saga pattern and the outbox pattern.** These patterns manage
cross-service consistency in a distributed system built from
independently deployed services rather than from replicas of one
database, and they are frequently confused with multi-leader replication
because both deal with more than one place producing writes that must
eventually agree, but they operate at the application-workflow layer
rather than the storage replication layer, and combining a saga with
multi-leader storage underneath each participating service is common
rather than contradictory.

**Incompatible with strict serializability.** As stated in dimension 4,
strict serializability requires a single global total order over
transactions, which an asynchronously replicated multi-leader system
cannot produce without adding synchronous consensus for every write, at
which point the system is no longer functioning as an asynchronous
multi-leader system in the sense this entry describes.

**Incompatible with a single-writer invariant.** Any invariant whose
correctness proof depends on there being exactly one writer for a given
key or record at a time, a common assumption in single-leader system
design, and in many application-level locking schemes, is violated by
definition the moment that key can be written concurrently on two
leaders, so patterns and invariants built on that assumption cannot be
layered directly onto multi-leader storage without redesign.

## 14. Refactoring path in and out

Introducing multi-leader replication into a single-leader system follows
these steps.

1. Before touching infrastructure, instrument the existing single-leader
   system to measure the actual concurrent-write conflict rate the new
   topology would experience. Log, per record, whether it was written by
   more than one logical writer, user, region, device, within a window
   equal to the expected replication lag. This directly tests the
   applicability criterion from dimension 4 before committing engineering
   effort.
2. Choose and design the conflict resolution strategy from dimension 8 for
   every record type that the measurement in step 1 showed can genuinely
   conflict, and write it down as an explicit specification the whole
   engineering team reviews, not as an implicit property of whatever
   database client library is chosen.
3. Stand up the second, and subsequent, leader as a replica of the first,
   verify it can serve reads correctly and its replication lag is bounded
   and monitored, before allowing it to accept any writes at all.
4. Enable writes on the second leader for a narrow, low-risk subset of
   traffic first, a specific tenant, a specific region's internal test
   traffic, a specific record type known from step 1 to almost never
   conflict, and verify the conflict resolution logic from step 2 behaves
   correctly against real, not synthetic, concurrent writes.
5. Roll out write-enablement on additional leaders incrementally, widening
   the traffic that flows to each new leader only after the conflict rate
   and resolution correctness at the current scope are confirmed healthy
   for a full business cycle, long enough to see the traffic patterns that
   are rare but real, such as an end-of-month batch process.
6. Build and dashboard the observability from dimension 16 before, not
   after, the rollout is considered complete, because a multi-leader
   system with no visibility into replication lag and conflict rate is not
   verifiably correct in production, only assumed to be.

Removing multi-leader replication and reverting to single-leader follows
these steps.

1. Confirm the actual conflict rate has been low enough, for long enough,
   that the pattern is not earning its operational cost, which is
   frequently the honest outcome of the measurement discipline this entry
   recommends. Many systems that adopt multi-leader replication for
   latency discover the conflict rate was near zero and the pattern was
   solving a problem read replicas would also have solved.
2. Pick the leader that will become the sole surviving leader, usually the
   one already carrying the most write traffic, to minimize the migration
   window's write disruption.
3. Freeze writes on every other leader, drain their in-flight replication
   to the surviving leader, and confirm every leader's data has fully
   converged, zero pending conflicts, zero replication lag, before
   proceeding, because converting a still-disagreeing multi-leader system
   directly into a single-leader system bakes in whatever inconsistency
   existed at the moment of the cutover.
4. Repoint every writer's client configuration at the surviving leader,
   and demote the other former leaders to read-only followers of it,
   reusing the existing single-leader replication machinery rather than
   building anything new, since the surviving leader plus its now-read-
   only followers is exactly a single-leader topology.
5. Remove the conflict-detection and conflict-resolution code paths only
   after a full monitoring cycle confirms no write traffic is still being
   routed to a demoted node, because a client that was never repointed
   would otherwise silently write to a node that can no longer replicate
   those writes anywhere.

## 15. Testing and verification

Testing code that uses multi-leader replication requires deliberately
constructing the concurrent-write scenario the production system will
eventually hit by accident, because a test suite that only ever issues
writes sequentially, even against multiple leaders, will never exercise
the conflict path at all.

The primary technique is a Jepsen-style linearizability and convergence
test. Run a workload that issues concurrent, conflicting writes to two or
more leaders simultaneously, using a barrier to guarantee true
concurrency rather than relying on network timing, inject a partition
between the leaders for a controlled window, heal the partition, and then
assert that every leader converges to the same final value for every
record, and that the value it converges to is one of the actually-written
values, never a value that was never written, because a corrupted merge
is a distinct and worse bug than an unexpected but valid winner. This
class of test is what the Jepsen testing project popularized for
distributed systems generally, and it applies directly here because
multi-leader replication is exactly the family of system Jepsen-style
testing was built to probe.

Unit-test the conflict resolver in complete isolation from the
replication transport, feeding it pairs of synthetically constructed
conflicting versions, including adversarial cases such as identical
timestamps, clock skew in both directions, one side missing a field the
other side has, and asserting the resolver's output is correct and,
critically, that calling it with the arguments swapped produces the same
result, which directly tests the commutativity property every
multi-leader conflict resolver needs.

Test replication topology behavior separately from conflict resolution.
For circular or star topologies, construct a test that injects a write at
one node and asserts it eventually appears exactly once at every other
node, never zero times, a lost write, and never more than once, an
infinite loop, per the failure mode in dimension 11.

Fault-injection testing in a staging environment that mirrors the
production topology, deliberately partitioning replication links for
extended periods and verifying both that each leader remains available
for local writes during the partition and that the system converges
correctly once the partition heals, is the practice most production
multi-leader deployments described in dimension 9 rely on before
trusting the pattern with real traffic, because the failure modes in
dimension 11 are, almost without exception, only reproducible under an
actual network partition, not under a unit test.

## 16. Observability signals

Every replication link between two leaders needs its own per-link
replication lag metric, time since the last write successfully applied
from the source leader, and its own last-successful-heartbeat timestamp,
alerted independently, because the failure mode in dimension 11, a link
silently stops making progress, is otherwise invisible by design. The
system's whole point is that each leader keeps working locally, so
nothing about local health signals a remote replication failure.

Conflict rate per record type or per table is a first-class metric, not a
debugging afterthought. A sudden spike in conflicts on a record type that
was expected to rarely conflict is an early signal either of a bug
upstream, a client writing to the wrong region, or of the applicability
assumption from dimension 4 having quietly become false as traffic
patterns evolved.

Log every resolved conflict with enough detail to reconstruct the
decision after the fact, both conflicting versions, their version
metadata, which leader detected the conflict, which resolution strategy
fired, and the resulting value. This log is what makes the silent-data-
loss failure mode in dimension 11 diagnosable rather than merely
suspected. Without it, a customer report that their data changed
unexpectedly is nearly impossible to root-cause after the fact because
both original versions are gone once the resolver has run.

Clock skew between leaders, measured directly using an NTP-synchronized
reference or a periodic round-trip probe between leaders, is a required
metric wherever last-writer-wins by wall-clock timestamp is in use as the
resolution strategy, because skew directly determines how often the wrong
write wins, silently.

A convergence check, a periodic background job that reads the same key
from every leader and confirms they agree, run continuously in
production against a sample of keys and, after any detected partition
heals, against every key touched during the partition, is the closest
thing to a production-grade proof that the system's core promise,
eventual consistency across leaders, is actually holding, as opposed to
being an assumption nobody is verifying.

## 17. Security and privacy implications

Multi-leader replication expands the network attack surface relative to
single-leader replication in direct proportion to the number of leaders.
Every additional leader is an additional node that must authenticate
incoming replication traffic, and every replication link is an
additional network path that must be encrypted in transit, because a
compromised or spoofed replication message from a rogue node can inject
arbitrary writes directly into a leader's log, bypassing whatever access
control the leader's normal client-facing API enforces, unless the
replication transport itself independently authenticates and authorizes
its peer leaders.

Because each leader independently accepts writes and only later
reconciles them, a write made and then deleted at one leader can exist,
briefly or for as long as a partition persists, on other leaders that
have not yet received the delete, which has direct implications for any
data-deletion requirement driven by privacy regulation. A request to
delete a user's data is not actually complete, from a regulatory
standpoint, until it has been confirmed to have propagated and been
applied at every leader, not merely accepted at the leader the deletion
request happened to reach. Systems with legal deletion-completeness
requirements need an explicit propagation-confirmation step layered on
top of the pattern's normal eventual-consistency behavior, not an
assumption that eventual consistency alone satisfies the requirement.

Conflict resolution logic that surfaces both conflicting versions to an
end user or to an administrative interface, the "surface to application"
variant in dimension 8, can leak information across a trust boundary if
the two conflicting versions were written by two different users with
different access permissions to the underlying data, for example if user
A and user B concurrently edit a record that only one of them should be
able to see the full contents of. The conflict-surfacing mechanism must
apply the same authorization checks to each version it presents as the
normal read path would, which is easy to overlook because conflict
resolution code paths are frequently built and tested separately from the
main authorization-checked read and write paths.

## 18. References

1. Kleppmann, Martin. Designing Data-Intensive Applications. O'Reilly
   Media, 2017. Chapter 5, "Replication", section "Multi-Leader
   Replication". Print and digital edition, ISBN 978-1449373320.
2. Apache CouchDB documentation. "Replication Protocol."
   https://docs.couchdb.org/en/stable/replication/protocol.html
   Verified 2026-08-02.
3. MySQL 8.0 Reference Manual. "Group Replication, Multi-Primary Mode."
   https://dev.mysql.com/doc/refman/8.0/en/group-replication-multi-primary-mode.html
   Verified 2026-08-02.
4. Microsoft Learn. "Conflict Resolution Types and Resolution Policies,
   Azure Cosmos DB."
   https://learn.microsoft.com/en-us/azure/cosmos-db/conflict-resolution-policies
   Verified 2026-08-02.
5. Apache Cassandra documentation. "Dynamo."
   https://cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html
   Verified 2026-08-02. Cited here for the leaderless-replication
   distinction in dimension 2, dimension 12, and dimension 13, not as a
   multi-leader production use.

## Code examples

Three languages, each implementing the same core mechanism from
dimension 7. Two leaders, A and B, each accept one write while unaware
of the other, detect the resulting write as causally concurrent using a
version vector (dimension 5), and resolve it with a deterministic
last-writer-wins rule composed with a merged version vector, so both
leaders converge to the same value and the same version regardless of
which side resolves first. Java and Rust are omitted here because the
version-vector comparison and the merge step are identical shape in
every general-purpose language, and TypeScript, Python, and Go already
cover the map-oriented, dictionary-oriented, and struct-oriented idioms
for holding that vector.

### TypeScript

```typescript
type VersionVector = Record<string, number>;

interface Record_ {
  value: string;
  version: VersionVector;
  writtenAtMs: number;
}

function dominates(a: VersionVector, b: VersionVector): boolean {
  const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
  let strictlyGreater = false;
  for (const k of keys) {
    const av = a[k] ?? 0;
    const bv = b[k] ?? 0;
    if (av < bv) return false;
    if (av > bv) strictlyGreater = true;
  }
  return strictlyGreater;
}

function isConcurrent(a: VersionVector, b: VersionVector): boolean {
  return !dominates(a, b) && !dominates(b, a);
}

function lastWriterWins(local: Record_, incoming: Record_): Record_ {
  if (isConcurrent(local.version, incoming.version)) {
    return incoming.writtenAtMs >= local.writtenAtMs ? incoming : local;
  }
  return dominates(incoming.version, local.version) ? incoming : local;
}

function mergeVersions(a: VersionVector, b: VersionVector): VersionVector {
  const merged: VersionVector = {};
  for (const k of new Set([...Object.keys(a), ...Object.keys(b)])) {
    merged[k] = Math.max(a[k] ?? 0, b[k] ?? 0);
  }
  return merged;
}

function applyIncoming(local: Record_, incoming: Record_): Record_ {
  const winner = lastWriterWins(local, incoming);
  return { ...winner, version: mergeVersions(local.version, incoming.version) };
}

function main(): void {
  const leaderA: Record_ = { value: "red", version: { A: 1 }, writtenAtMs: 1000 };
  const leaderB: Record_ = { value: "blue", version: { B: 1 }, writtenAtMs: 1005 };

  console.log("concurrent write detected", isConcurrent(leaderA.version, leaderB.version));

  const resolvedAtA = applyIncoming(leaderA, leaderB);
  const resolvedAtB = applyIncoming(leaderB, leaderA);

  console.log("resolved at A", resolvedAtA.value, resolvedAtA.version);
  console.log("resolved at B", resolvedAtB.value, resolvedAtB.version);
  console.log("converged", resolvedAtA.value === resolvedAtB.value);
}

main();
```

Compiled with `npx tsc --strict --target es2020 --module commonjs` and
run with `node`. The run confirms both leaders detect the write as
concurrent and converge to the same winning value and the same merged
version vector.

### Python

```python
from dataclasses import dataclass
from typing import Dict

@dataclass
class Record:
    value: str
    version: Dict[str, int]
    written_at_ms: int

def dominates(a: Dict[str, int], b: Dict[str, int]) -> bool:
    keys = set(a) | set(b)
    strictly_greater = False
    for k in keys:
        av, bv = a.get(k, 0), b.get(k, 0)
        if av < bv:
            return False
        if av > bv:
            strictly_greater = True
    return strictly_greater

def is_concurrent(a: Dict[str, int], b: Dict[str, int]) -> bool:
    return not dominates(a, b) and not dominates(b, a)

def last_writer_wins(local: Record, incoming: Record) -> Record:
    if is_concurrent(local.version, incoming.version):
        return incoming if incoming.written_at_ms >= local.written_at_ms else local
    return incoming if dominates(incoming.version, local.version) else local

def merge_versions(a: Dict[str, int], b: Dict[str, int]) -> Dict[str, int]:
    return {k: max(a.get(k, 0), b.get(k, 0)) for k in set(a) | set(b)}

def apply_incoming(local: Record, incoming: Record) -> Record:
    winner = last_writer_wins(local, incoming)
    merged_version = merge_versions(local.version, incoming.version)
    return Record(winner.value, merged_version, winner.written_at_ms)

def main() -> None:
    leader_a = Record(value="red", version={"A": 1}, written_at_ms=1000)
    leader_b = Record(value="blue", version={"B": 1}, written_at_ms=1005)

    print("concurrent write detected", is_concurrent(leader_a.version, leader_b.version))

    resolved_at_a = apply_incoming(leader_a, leader_b)
    resolved_at_b = apply_incoming(leader_b, leader_a)

    print("resolved at A", resolved_at_a.value, resolved_at_a.version)
    print("resolved at B", resolved_at_b.value, resolved_at_b.version)
    print("converged", resolved_at_a.value == resolved_at_b.value)

if __name__ == "__main__":
    main()
```

Run with `python3`. The run matches the TypeScript run, both leaders
converge to the same value with the same merged version vector.

### Go

```go
package main

import "fmt"

type version map[string]int

type record struct {
	value       string
	ver         version
	writtenAtMs int
}

func dominates(a, b version) bool {
	keys := map[string]bool{}
	for k := range a {
		keys[k] = true
	}
	for k := range b {
		keys[k] = true
	}
	strictlyGreater := false
	for k := range keys {
		av, bv := a[k], b[k]
		if av < bv {
			return false
		}
		if av > bv {
			strictlyGreater = true
		}
	}
	return strictlyGreater
}

func isConcurrent(a, b version) bool {
	return !dominates(a, b) && !dominates(b, a)
}

func lastWriterWins(local, incoming record) record {
	if isConcurrent(local.ver, incoming.ver) {
		if incoming.writtenAtMs >= local.writtenAtMs {
			return incoming
		}
		return local
	}
	if dominates(incoming.ver, local.ver) {
		return incoming
	}
	return local
}

func mergeVersions(a, b version) version {
	merged := version{}
	for k, v := range a {
		merged[k] = v
	}
	for k, v := range b {
		if v > merged[k] {
			merged[k] = v
		}
	}
	return merged
}

func applyIncoming(local, incoming record) record {
	winner := lastWriterWins(local, incoming)
	winner.ver = mergeVersions(local.ver, incoming.ver)
	return winner
}

func main() {
	leaderA := record{value: "red", ver: version{"A": 1}, writtenAtMs: 1000}
	leaderB := record{value: "blue", ver: version{"B": 1}, writtenAtMs: 1005}

	fmt.Println("concurrent write detected", isConcurrent(leaderA.ver, leaderB.ver))

	resolvedAtA := applyIncoming(leaderA, leaderB)
	resolvedAtB := applyIncoming(leaderB, leaderA)

	fmt.Println("resolved at A", resolvedAtA.value, resolvedAtA.ver)
	fmt.Println("resolved at B", resolvedAtB.value, resolvedAtB.ver)
	fmt.Println("converged", resolvedAtA.value == resolvedAtB.value)
}
```

Run with `go run`. The run matches the TypeScript and Python runs.
