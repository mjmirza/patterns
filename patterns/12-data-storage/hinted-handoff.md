---
name: Hinted Handoff
slug: hinted-handoff
family: 12-data-storage
category: Data and Storage
aliases: [Sloppy Quorum Write, Hint Delivery]
first_described: "DeCandia et al. 2007"
maturity: canonical
related: [quorum, leaderless-replication, gossip-protocol, merkle-tree, vector-clock, write-ahead-log]
incompatible_with: [two-phase-commit]
verified: 2026-08-02
---

# Hinted Handoff

## 1. Name, aliases, and lineage

The canonical name is Hinted Handoff. It was introduced by Giuseppe DeCandia,
Deniz Hastorun, Madan Jampani, Gunavardhan Kakulapati, Avinash Lakshman, Alex
Pilchin, Swaminathan Sivasubramanian, Peter Vosshall and Werner Vogels in
"Dynamo. Amazon's Highly Available Key-value Store," Proceedings of the 21st
ACM Symposium on Operating Systems Principles (SOSP), 2007
(https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf,
verified 2026-08-02), section 4.5, "Handling Temporary Failures." The paper
describes a scenario where a coordinator wants to write a replica to node A
but A is unreachable, so the replica is instead sent to node D along with a
hint in its metadata recording that the replica belongs to A. D keeps that
replica in a separate local store and, once it detects that A has recovered,
attempts to deliver the replica to A and remove it from its own store once
the transfer succeeds.

The pattern is sometimes described as the write-side companion to a Sloppy
Quorum, and the two names are frequently used together because a hinted write
is what makes a sloppy quorum durable rather than merely available. Apache
Cassandra's own documentation keeps the same name and the same mechanics,
describing hints as "a best-effort technique ... used in the write path"
(https://cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html,
verified 2026-08-02). Riak, built directly on the Dynamo paper's design,
calls the receiving node a "fallback node" and the mechanism "handoff"
without changing its meaning. A fallback node stands in for an unreachable
owner of a partition, holding data until the owner returns
(https://docs.riak.com/riak/kv/2.2.3/learn/concepts/replication/index.html,
verified 2026-08-02). No competing name for this specific mechanism is in
wide use across the systems that implement it, which is unusual for a
distributed systems pattern and helps anyone searching for it land on the
right term on the first try.

## 2. Problem and context

A leaderless, replicated key-value store assigns each key to a fixed set of N
nodes, typically the next N nodes clockwise on a consistent-hashing ring. A
write is considered successful once W of those N nodes acknowledge it, and a
read is considered successful once R of them agree on a value, following the
quorum arithmetic described in DeCandia et al. 2007 section 4.4. This design
assumes that most of the time, the N nodes responsible for a key are
reachable. Networks, disks, garbage-collection pauses, and process restarts
make that assumption false often enough that the system needs an answer for
what a coordinator does when one or more of the correct N nodes cannot be
reached at write time.

The naive answer is to fail the write, or to lower the effective W by one and
accept a write with fewer acknowledgments than the configured durability
target implies. Both answers trade away something the operator asked for.
Failing the write trades away availability, and silently accepting a
degraded write trades away the promised replication factor without telling
anyone. Hinted handoff exists to give a third answer, accepting the write at
full W by routing the replica meant for the unreachable node to a different,
reachable node instead, and treating that substitute node as a temporary,
labeled parking spot rather than a permanent owner of the data. The problem
the pattern solves is specifically the temporary unavailability case, a node
that is down for seconds, minutes, or a few hours because of a restart, a
deploy, or a transient network partition, not a node that is permanently
gone and needs its data rebuilt from the other replicas by an entirely
different mechanism.

## 3. Forces

Availability for writes pulls toward accepting a write from any reachable
node, regardless of whether that node is one of the key's designated owners.
Durability and correctness pull the other way, because a write accepted by a
non-owner node is not yet visible to a normal quorum read that only queries
the designated owners, so the write is durable in the sense that data is not
lost, but not yet durable in the sense of being consistently readable.
Consistency is the force most directly in tension with availability here. A
sloppy quorum accepted by substitute nodes can produce a period during which
different clients reading through different coordinators see different
answers, because the substitute nodes are outside the normal read path until
the hint is delivered or a read-repair or anti-entropy pass reconciles the
inconsistency.

Storage and network cost is a real, if secondary, force. Every node that
holds hints on behalf of other nodes is spending disk space and I/O on data
it will discard as soon as delivery succeeds, and the eventual replay of
that data is an extra network transfer beyond the original write. Operability
is a force in the other direction from availability. Hinted handoff adds a
subsystem, a storage location, a delivery thread pool, a time window
configuration, and a set of metrics that an operator must understand,
because a hints backlog that never drains is itself a failure mode distinct
from the node failure that created it. The pattern favors availability and
accepts a bounded, temporary consistency cost in exchange, and it accepts
operational complexity as the price of not making the client wait or fail.

## 4. Applicability and non-applicability

Reach for hinted handoff when the failure model is mostly short, transient
outages, such as a rolling restart, a JVM garbage-collection pause, a
brief network partition, a node being drained for maintenance, or a
short-lived process crash with automatic supervision that restarts it within
seconds or minutes. It fits systems that already accept eventual consistency
as their normal operating mode and that already run a background
reconciliation process such as read repair or Merkle-tree anti-entropy,
because hinted handoff is explicitly a best-effort optimization layered on
top of that reconciliation, never a substitute for it. It fits systems where
write availability during a partial outage matters more than every reader
immediately seeing every write, which is why it appears in shopping-cart,
session-store, and telemetry-ingestion workloads and does not appear in
systems built around strict serializability.

Do not reach for it when the workload needs linearizable reads or
strong consistency, because a client can write successfully through a
sloppy quorum and then read stale or absent data from the designated owners
before the hint is delivered, and no amount of hinted-handoff tuning removes
that window, only shortens it. Do not reach for it as the primary durability
mechanism for a node that is permanently gone, since a hint has a bounded
time-to-live and a node down longer than that window loses its hints
entirely, per Cassandra's own documented behavior that data is "permanently
out of sync until either read-repair or full/incremental anti-entropy
repair" runs once the window has passed
(https://cassandra.apache.org/doc/latest/cassandra/managing/operating/hints.html,
verified 2026-08-02). Do not reach for it in a system with a small, fixed
cluster where every node is close to its capacity limit, because the extra
storage and I/O load of holding another node's hints on top of normal
traffic can push a healthy node toward the same kind of overload that caused
the original outage, a cascading-failure risk the pattern does not defend
against on its own. Do not reach for it as a way to avoid choosing a
consistency level, since it changes the availability and staleness trade-off
of a write, it does not remove the trade-off.

## 5. Structure

**Coordinator.** The node that receives a client's write request and is
responsible for fanning it out to the N replicas assigned to the key. The
coordinator decides, replica by replica, whether the assigned node is
reachable, and if it is not, selects a substitute and attaches a hint.

**Preference list.** The ordered list of N nodes assigned to a key by the
partitioning scheme, most commonly consistent hashing. The coordinator walks
this list to find replica targets, and when a designated member is
unreachable, it extends the walk past the first N members to find a
reachable substitute, the "sloppy" part of sloppy quorum.

**Hint.** A small piece of metadata attached to the replica payload recording
which node the data actually belongs to, so the substitute node knows whom
to hand the data to later, and so the substitute node can distinguish hinted
data it is merely holding from its own normal replica data.

**Substitute node (hint holder).** A reachable node, not normally an owner of
the key, that accepts the hinted write, stores the payload and its hint
separately from its regular data, and is responsible for attempting delivery
once it learns the original owner has recovered.

**Failure detector.** The subsystem, commonly gossip-based, that the
substitute node consults to learn when the original owner has rejoined the
cluster and become reachable again, triggering an attempt to replay the
hint.

**Anti-entropy process.** The independent background mechanism, most often
read repair or a Merkle-tree comparison, that reconciles any inconsistency
hinted handoff did not resolve, either because the hint's time window
expired or because the substitute node itself failed before it could
deliver the hint.

## 6. ASCII structure diagram

```
                         preference list for key K
                         (N = 3, consistent-hash ring)

    +-------------+     designated       +-------------+
    |   Node A    |<-------------------->|   Node B    |
    | (owner 1)   |                      | (owner 2)   |
    +-------------+                      +-------------+
           ^
           |  A is unreachable at write time
           |
    +-------------+     write(K, v)      +-------------+
    |  Coordinator |<--------------------|   Client    |
    +-------------+                      +-------------+
           |
           |  A unreachable, walk past N to find substitute
           v
    +---------------------------+
    |         Node D            |
    |  (not an owner of K)      |
    |                            |
    |  hints store.              |
    |  { for: A, key: K,         |
    |    value: v, ts: T1 }      |
    +---------------------------+
           |
           |  gossip detects A back online
           v
    +---------------------------+
    |  Node D delivers hint      |
    |  to Node A, then drops it  |
    +---------------------------+
           |
           v
    +-------------+
    |   Node A    |  now holds K = v again, in sync with B
    +-------------+
```

## 7. Dynamics

```
Client                Coordinator          Node A (down)   Node D (substitute)   Node A (back up)

  |  write(K, v, W=2)     |                     |                 |                  |
  |----------------------->|                     |                 |                  |
  |                        |--- send to B ------>|                 |                  |
  |                        |     (ack)            |                 |                  |
  |                        |<---------------------|                 |                  |
  |                        |--- send to A ------->|  timeout        |                  |
  |                        |          X            |                 |                  |
  |                        |--- send to D                        |                  |
  |                        |   with hint(for=A) ----------------->|                  |
  |                        |                                       |--- store hint     |
  |                        |                                       |   locally         |
  |                        |<--- ack from D -------------------------|                  |
  |                        |                                       |                  |
  |  (2 acks, W=2 met)     |                                       |                  |
  |<-----------------------|                                       |                  |
  |  write succeeds        |                                       |                  |
  |                        |                                       |                  |
  |                        |                                       |    A recovers,   |
  |                        |                                       |    gossip sees   |
  |                        |                                       |    A reachable   |
  |                        |                                       |<-----------------|
  |                        |                                       |--- deliver K,v -->|
  |                        |                                       |    to A           |
  |                        |                                       |<--- ack ----------|
  |                        |                                       |--- drop hint      |
  |                        |                                       |    locally        |
```

A read for K issued between the write succeeding and the hint being
delivered may reach a coordinator that queries only B and A, sees A's
current value, and returns a stale answer unless it also queries D or a
read-repair pass has already reconciled the inconsistency. This is the
consistency window a sloppy quorum accepts, and it is bounded by how quickly
node D detects A's recovery, not by the client's original request.

## 8. Implementation variants

**Metadata-only hint, coordinator-attached.** The variant described in the
original Dynamo paper. The coordinator itself decides at write time to route
past an unreachable node and attaches the hint metadata before forwarding
the payload, so the substitute node's only job is to store and later replay
what it is given.

**Separate hints store versus inline data store.** Cassandra keeps hints in
flat files under a dedicated `hints` directory rather than in its normal
SSTable data path, one file series per target node, so hint delivery never
competes with normal read and write I/O for the same on-disk data structures
(https://cassandra.apache.org/doc/latest/cassandra/managing/operating/hints.html,
verified 2026-08-02). Riak instead stores hinted data through the normal
vnode storage backend, tagged with the original partition identifier, and
relies on its handoff subsystem rather than a physically separate file
format (https://docs.riak.com/riak/kv/2.2.3/learn/concepts/replication/index.html,
verified 2026-08-02). The trade-off is isolation versus simplicity, and it
runs both ways. A separate store keeps hint traffic from touching the normal
read path at all, at the cost of a second storage engine to operate, while
reusing the normal store is simpler to build but means hint volume competes
with live traffic for compaction and cache pressure.

**Bounded time window.** Nearly every production implementation caps how
long a substitute node will keep a hint before giving up and relying on
anti-entropy instead, because holding hints forever for a node that never
comes back is an unbounded storage liability. Cassandra's default is three
hours, configurable via `max_hint_window`
(https://cassandra.apache.org/doc/latest/cassandra/managing/operating/hints.html,
verified 2026-08-02).

**Push versus pull delivery.** The most common variant is push. The
substitute node watches for the owner's recovery through the failure
detector and initiates delivery on its own schedule, using a bounded thread
pool so hint replay does not saturate the network during a mass recovery,
such as an entire rack coming back online at once. A pull variant, less
common in practice, has the recovering node request outstanding hints from
its peers on rejoin rather than waiting for pushes, trading a coordination
step for tighter control over the recovering node's own ingest rate while
it is still catching up on normal traffic.

**Local versus multi-datacenter hint scope.** Multi-datacenter deployments
typically restrict hints to the local datacenter of the substitute node
because cross-datacenter hint replay is expensive in both bandwidth and
latency, and a datacenter that is down as a whole is better served by full
datacenter-level repair than by hints accumulating on the other side of a
wide-area link.

## 9. Known production uses

Amazon's internal Dynamo system, as documented in the original 2007 paper,
is the system that introduced the mechanism, used to keep the company's
shopping cart and other core internal services available during transient
node failures without blocking writes (DeCandia et al. 2007, section 4.5,
https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf,
verified 2026-08-02).

Apache Cassandra implements hinted handoff as a first-class, independently
tunable write-path feature, enabled by default, documented with its own
configuration keys including `hinted_handoff_enabled` and
`max_hint_window`, and explicitly described as a best-effort technique that
complements, rather than replaces, anti-entropy repair
(https://cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html
and
https://cassandra.apache.org/doc/latest/cassandra/managing/operating/hints.html,
both verified 2026-08-02).

Riak, built explicitly on the Dynamo paper's design by Basho Technologies,
implements the same mechanism under the name handoff, using fallback vnodes
that hold data for an unreachable partition owner and hand it back once the
owner rejoins the ring
(https://docs.riak.com/riak/kv/2.2.3/learn/concepts/replication/index.html,
verified 2026-08-02).

## 10. Consequences

Positive. Writes continue to succeed during short, common failure modes
without the coordinator falling back to a lower consistency level or failing
outright, which is the entire point of the pattern and its largest benefit.
The mechanism is self-limiting in scope, activating only for the specific
key ranges owned by the node that went down, so a single node failure does
not affect the availability of keys owned entirely by healthy nodes. It
requires no coordination protocol beyond gossip-based failure detection,
so it adds no additional consensus round trip to the write path itself, the
extra work happens asynchronously after the client already has its
acknowledgment.

Negative. A write accepted through a sloppy quorum is not immediately
visible to a plain quorum read against the designated owners, creating a
consistency window whose length depends on how quickly the failed node
recovers and how quickly the failure detector notices, neither of which the
client controls or is told about. A substitute node that fails before
delivering its held hints loses that data unless another mechanism, such as
Merkle-tree anti-entropy, later reconciles the gap, which means hinted
handoff is not itself a durability guarantee independent of the anti-entropy
process it depends on. During a widespread or long-lasting outage, hints
accumulate on the remaining reachable nodes, consuming disk and adding
delivery load once the outage resolves, and a system that never tunes or
monitors this backlog can turn a transient node failure into a
capacity problem for the nodes that stayed up.

## 11. Failure modes and misuse

**Symptom.** A read immediately after a successful write returns stale or
missing data. **Cause.** The write was accepted through a sloppy quorum
while one of the key's designated owners was unreachable, and the read went
to the coordinator's normal quorum path, which does not consult the
substitute node holding the hint. **Fix.** Use a read-your-writes strategy
such as sticky sessions to the same coordinator, or accept the staleness
window as inherent to the consistency level chosen, or raise R and W so the
read set and write set are large enough that this specific race cannot
occur without also failing the write.

**Symptom.** Disk usage on a handful of nodes grows steadily and does not
shrink even though the cluster looks otherwise healthy. **Cause.** One or
more nodes are down for longer than expected, and every other node that has
tried to write to them is accumulating hints faster than they can be
delivered, or a bug or misconfiguration is preventing hint delivery threads
from draining the backlog. **Fix.** Check the down node's actual status
first, since the correct remedy is usually bringing it back, not tuning
hints; if the node is genuinely gone, disable hints for it explicitly and
run a full anti-entropy repair once a replacement node is provisioned,
rather than letting hints accumulate against a time window that will
eventually expire and discard the data anyway.

**Symptom.** A node that recently rejoined the cluster after maintenance
experiences a sudden latency and CPU spike. **Cause.** Every other node in
the cluster that was holding hints for it begins delivering them at once,
and the recovering node is trying to absorb both this hint replay traffic
and its normal share of live read and write traffic simultaneously. **Fix.**
Throttle hint delivery concurrency, bring nodes back into rotation gradually
behind a load balancer or gossip-state gate rather than all at once, and
size the hint delivery thread pool so it does not exceed what the
recovering node can absorb on top of live traffic.

**Symptom.** Two clients reading through different coordinators at the same
moment see two different values for the same key, and the mismatch
resolves itself a few seconds later without operator intervention.
**Cause.** This is expected, not a bug. It is the visible consequence of the
sloppy-quorum consistency window, and it self-heals once the hint is
delivered or a read-repair pass runs. **Fix.** Nothing to fix in the
mechanism itself; if this staleness window is unacceptable for the
application's correctness requirements, the fix is choosing a stronger
consistency level or a linearizable store for that specific data, not tuning
hinted handoff.

**Misuse.** Treating hinted handoff as a substitute for read repair or
anti-entropy rather than a complement to it, on the assumption that hints
alone guarantee eventual consistency. The pattern is explicitly best-effort.
A substitute node can crash before delivering a hint, and a hint's time
window can expire before the owner returns, either of which silently drops
the pending write unless a separate reconciliation pass exists to catch it.

## 12. Trade-off matrix

| Force | Hinted handoff (sloppy quorum write) | Strict quorum, no handoff | Two-phase commit |
|---|---|---|---|
| Write availability during a node outage | High, write succeeds via substitute node | Degraded or blocked if fewer than W owners are reachable | Blocked if any participant is unreachable |
| Read-your-writes guarantee | Not guaranteed until hint delivers or repair runs | Guaranteed once quorum is met, owners never bypassed | Guaranteed once the transaction commits |
| Latency added to the write path | None beyond normal quorum wait, hint replay is async | None beyond normal quorum wait | Extra prepare and commit round trips |
| Operational surface | Hints storage, delivery threads, time window tuning | None beyond normal replica management | Coordinator log, participant recovery protocol |
| Failure recovery model | Best-effort hint replay plus anti-entropy backstop | Anti-entropy or manual repair only | Blocking recovery from the coordinator's log |
| Behavior on prolonged outage | Hints expire, gap persists until anti-entropy repairs it | Write availability for the affected key range drops | Entire transaction blocks until the participant returns |

## 13. Related and incompatible patterns

**Quorum** is the consistency model hinted handoff extends. A plain quorum
assumes reads and writes always touch the designated N owners; hinted
handoff is specifically what happens when a write cannot reach one of those
owners and needs a temporary, honest substitute rather than a silent
reduction in W.

**Leaderless replication** is the broader architecture hinted handoff is
built for. Systems with a single leader per key generally do not need
hinted handoff on the write path, because a leader failure is handled by
leader election rather than by routing writes to an arbitrary standby; the
pattern is specific to designs where any coordinator can accept a write for
any key and no single node has exclusive write authority.

**Gossip protocol** supplies the failure-detection signal that tells a
substitute node when the original owner has become reachable again, which
is what triggers hint delivery. Without a gossip-based (or equivalent)
membership view, a substitute node has no reliable way to know when to
attempt replay rather than continuing to poll or wait indefinitely.

**Merkle tree** anti-entropy is the reconciliation backstop hinted handoff
depends on for correctness when a hint is lost, either through the
substitute node crashing or the time window expiring. The two are
complementary, not overlapping. Hinted handoff resolves the common,
fast-recovery case cheaply, and Merkle-tree comparison resolves whatever
hinted handoff missed, more slowly and more expensively.

**Vector clock** versioning is what allows a node receiving a delivered hint
to determine whether the hinted value is newer, older, or concurrent with
whatever value it may have received through other means in the meantime,
resolving the write conflicts that can arise when a hint arrives after the
owner has already accepted a fresher write from another coordinator.

**Two-phase commit** is incompatible in spirit with hinted handoff. Two-phase
commit requires every participant to be reachable and to vote before a
transaction can commit at all, which is precisely the availability trade-off
hinted handoff exists to avoid; a system built around two-phase commit has
no place to route an accepted write to a substitute participant, because
the protocol's correctness depends on the actual designated participants,
not a stand-in.

## 14. Refactoring path in and out

Introducing hinted handoff into a system that currently fails writes when a
replica is unreachable starts with defining the preference list walk. Given
the N designated owners of a key, the coordinator needs an ordered fallback
list of additional nodes to try when a designated owner does not respond
within the write timeout, most naturally the next reachable nodes on the
same consistent-hashing ring. Next, add a hint field to the write payload's
wire format so a substitute node can record which node the data actually
belongs to, and add a separate storage path, whether a dedicated directory,
a distinct table, or a tagged partition, so hinted data is never confused
with the substitute node's own normal replica data during compaction or
reads. Then wire the failure detector's recovery signal to a hint-delivery
worker that attempts replay when the owner rejoins, with a bounded
concurrency limit and a maximum time window past which a hint is abandoned
rather than held indefinitely. Finally, verify that the existing anti-entropy
mechanism, or a newly added one, covers the case where a hint is lost, since
hinted handoff is only correct as an optimization layered on top of a
mechanism that can recover without it.

Removing hinted handoff, for a system moving toward a leader-based or
strongly consistent design where sloppy writes no longer make sense, starts
by disabling new hint creation while leaving delivery of existing hints
running until the backlog drains to zero, confirmed by a metric or a direct
query of hint storage, rather than an assumed drain time. Once no
substitute node holds any outstanding hints, remove the fallback-routing
logic from the coordinator's write path so a write to an unreachable
designated owner once again fails or blocks according to the configured
consistency level, and remove the now-unused hint storage format and
delivery worker. Confirm that the anti-entropy mechanism the system still
relies on for other purposes, such as read repair, remains configured and
running, since removing hinted handoff removes one layer of the
availability and consistency trade-off but does not remove the need for
reconciliation of any other kind of replica inconsistency.

## 15. Testing and verification

Unit-level testing is straightforward for the parts that do not involve
timing. Given a preference list and a set of reachable and unreachable
nodes, assert that the coordinator selects the correct substitute node and
attaches a hint with the correct target identifier, and assert that a
substitute node correctly stores hinted data separately from its own
regular replica data. What is easy to test because of the pattern's
explicit metadata is that the hint's target is always inspectable directly,
unlike an implicit failover mechanism where the intended owner might have
to be inferred.

What becomes harder is the timing-dependent behavior, verifying that
delivery actually happens once the owner recovers, that it happens within a
bounded time, and that a hint older than the configured window is correctly
discarded rather than delivered late with stale data. This class of test
needs either a fake clock the failure detector and hint-expiry logic can be
driven with directly, or an integration test rig that can simulate a node
going down and back up on a compressed timeline, because waiting out a
real multi-hour window in a test suite is not practical. Fault injection at
the network layer, killing the connection to a specific node mid-write and
observing that the coordinator falls back to a substitute rather than
failing the client's request, is the most direct way to verify the
availability property the pattern is meant to provide.

Verification that the pattern does not silently mask data loss requires an
end-to-end test that deliberately kills the substitute node before it
delivers a held hint and then confirms that the anti-entropy or read-repair
mechanism eventually reconciles the missing write, since a test suite that
only checks the happy path of successful hint delivery would not catch a
regression in the reconciliation backstop the pattern depends on.

## 16. Observability signals

The count of hints currently stored, per target node and in aggregate
across the cluster, is the single most important signal, because a number
that only grows indicates either a node that is down longer than expected
or a delivery pipeline that has stalled. The rate of hints created per
second, broken down by target node, indicates which node is currently the
source of unavailability and how much write traffic is being redirected
because of it. The rate of hints successfully delivered per second, paired
against the creation rate, shows whether the backlog is draining or
growing.

The age of the oldest undelivered hint per target node matters more than
the raw count, since a small number of very old hints close to expiring is
a more urgent signal than a large number of hints that are seconds old and
draining normally. The number of hints that expired without being
delivered, meaning the anti-entropy backstop is now responsible for that
data, should be tracked and alerted on directly, because a silently rising
expiry count is exactly the case where hinted handoff has quietly stopped
being sufficient on its own. Disk space consumed by hint storage, tracked
separately from normal data storage where the storage engine keeps them
apart, is a direct capacity signal that should be alerted on before it
threatens the node's overall disk budget. A healthy cluster shows hint
counts at or near zero most of the time, with brief, self-draining spikes
correlated to observed node restarts or deploys; a cluster in trouble
shows a hint count with a sustained upward trend uncorrelated with any
recent, resolved node event.

## 17. Security and privacy implications

Hinted data held by a substitute node is, for the duration it is held, a
second copy of that key's payload sitting on a node that is not one of the
key's designated owners and that would not normally hold that data at all,
under any encryption-at-rest, access-control, or data-residency policy
written with the assumption that only the N designated owners ever hold a
given key. A system operating under a data-residency requirement that keys
must remain within a specific datacenter or region needs to confirm that
substitute-node selection during hinted handoff respects the same
constraint the normal preference list does, since an implementation that
falls back to any reachable node regardless of location can silently move
regulated data across a boundary it was never supposed to cross.

The hint metadata itself, recording which node a piece of data belongs to,
is not sensitive on its own, but the payload it carries has the same
sensitivity as the original write, so any encryption applied to data at
rest on the designated owner nodes needs to apply equally to the hints
storage location on substitute nodes, and any audit or access log that
tracks which nodes have held which keys needs to account for the fact that
a key's set of holders is not fixed to its preference list during periods
of node unavailability. Retention and deletion policies that assume data
for a key lives only on its N designated owners need a corresponding check
of hint storage across the cluster when honoring a deletion request during
or shortly after a period of node instability, or a deleted key can persist
undetected in a substitute node's hint store until its expiry window
passes.

## 18. References

DeCandia, G., Hastorun, D., Jampani, M., Kakulapati, G., Lakshman, A.,
Pilchin, A., Sivasubramanian, S., Vosshall, P., Vogels, W., "Dynamo. Amazon's
Highly Available Key-value Store," Proceedings of the 21st ACM Symposium on
Operating Systems Principles (SOSP), 2007, section 4.5, "Handling Temporary
Failures." https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf,
verified 2026-08-02.

Apache Cassandra documentation, "Dynamo," describing hinted handoff as a
best-effort write-path technique complemented by anti-entropy repair.
https://cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html,
verified 2026-08-02.

Apache Cassandra documentation, "Hints," describing the on-disk hints
format, the `max_hint_window` and `max_hints_delivery_threads` settings, and
the behavior once a node's hint window has elapsed.
https://cassandra.apache.org/doc/latest/cassandra/managing/operating/hints.html,
verified 2026-08-02.

Riak KV 2.2.3 documentation, "Replication," describing fallback vnodes,
handoff, and the "hand off any objects it has processed" behavior on
recovery. https://docs.riak.com/riak/kv/2.2.3/learn/concepts/replication/index.html,
verified 2026-08-02.

Wikipedia, "Dynamo (storage system)," summarizing the Dynamo paper's
authorship, venue, and year, and listing hinted handoff and sloppy quorum
as its named techniques for handling temporary failures.
https://en.wikipedia.org/wiki/Dynamo_(storage_system), verified 2026-08-02.

## Code examples

### TypeScript

```typescript
type Hint = { forNode: string; key: string; value: string; ts: number };

class SubstituteNode {
  private hints: Hint[] = [];

  storeHint(h: Hint): void {
    this.hints.push(h);
  }

  deliverPendingFor(nodeId: string, deliver: (h: Hint) => boolean): number {
    const remaining: Hint[] = [];
    let delivered = 0;
    for (const h of this.hints) {
      if (h.forNode === nodeId && deliver(h)) {
        delivered += 1;
      } else {
        remaining.push(h);
      }
    }
    this.hints = remaining;
    return delivered;
  }

  pendingCount(): number {
    return this.hints.length;
  }
}

function coordinatorWrite(
  ownerReachable: boolean,
  substitute: SubstituteNode,
  key: string,
  value: string
): void {
  if (ownerReachable) {
    return;
  }
  substitute.storeHint({ forNode: "A", key, value, ts: Date.now() });
}

const sub = new SubstituteNode();
coordinatorWrite(false, sub, "K", "v1");
console.log("pending hints for A", sub.pendingCount());
const applied: string[] = [];
const delivered = sub.deliverPendingFor("A", (h) => {
  applied.push(`${h.key}=${h.value}`);
  return true;
});
console.log("delivered", delivered, "applied", applied, "remaining", sub.pendingCount());
```

### Python

```python
import time
from dataclasses import dataclass


@dataclass
class Hint:
    for_node: str
    key: str
    value: str
    ts: float


class SubstituteNode:
    def __init__(self) -> None:
        self._hints: list[Hint] = []

    def store_hint(self, h: Hint) -> None:
        self._hints.append(h)

    def deliver_pending_for(self, node_id: str, deliver) -> int:
        remaining: list[Hint] = []
        delivered = 0
        for h in self._hints:
            if h.for_node == node_id and deliver(h):
                delivered += 1
            else:
                remaining.append(h)
        self._hints = remaining
        return delivered

    def pending_count(self) -> int:
        return len(self._hints)


def coordinator_write(owner_reachable: bool, substitute: SubstituteNode, key: str, value: str) -> None:
    if owner_reachable:
        return
    substitute.store_hint(Hint(for_node="A", key=key, value=value, ts=time.time()))


if __name__ == "__main__":
    sub = SubstituteNode()
    coordinator_write(False, sub, "K", "v1")
    print("pending hints for A", sub.pending_count())

    applied: list[str] = []

    def deliver(h: Hint) -> bool:
        applied.append(f"{h.key}={h.value}")
        return True

    delivered = sub.deliver_pending_for("A", deliver)
    print("delivered", delivered, "applied", applied, "remaining", sub.pending_count())
```

### Go

```go
package main

import (
	"fmt"
	"time"
)

type Hint struct {
	ForNode string
	Key     string
	Value   string
	TS      time.Time
}

type SubstituteNode struct {
	hints []Hint
}

func (s *SubstituteNode) StoreHint(h Hint) {
	s.hints = append(s.hints, h)
}

func (s *SubstituteNode) DeliverPendingFor(nodeID string, deliver func(Hint) bool) int {
	remaining := s.hints[:0]
	delivered := 0
	for _, h := range s.hints {
		if h.ForNode == nodeID && deliver(h) {
			delivered++
		} else {
			remaining = append(remaining, h)
		}
	}
	s.hints = remaining
	return delivered
}

func (s *SubstituteNode) PendingCount() int {
	return len(s.hints)
}

func coordinatorWrite(ownerReachable bool, sub *SubstituteNode, key, value string) {
	if ownerReachable {
		return
	}
	sub.StoreHint(Hint{ForNode: "A", Key: key, Value: value, TS: time.Now()})
}

func main() {
	sub := &SubstituteNode{}
	coordinatorWrite(false, sub, "K", "v1")
	fmt.Println("pending hints for A", sub.PendingCount())

	var applied []string
	delivered := sub.DeliverPendingFor("A", func(h Hint) bool {
		applied = append(applied, h.Key+"="+h.Value)
		return true
	})
	fmt.Println("delivered", delivered, "applied", applied, "remaining", sub.PendingCount())
}
```

Java, Rust, C#, and Kotlin samples are omitted here. The pattern is a
storage and networking coordination behavior rather than a language-level
idiom, and the three samples above already show the same shape, a hint
record, a store keyed by intended owner, and a delivery sweep, in a
statically typed compiled language (Go), a garbage-collected scripting
language (Python), and a structurally typed language commonly used for
server-side coordinators (TypeScript), which covers the range of runtime
models this pattern is implemented in without repeating the same logic a
fourth and fifth time.
