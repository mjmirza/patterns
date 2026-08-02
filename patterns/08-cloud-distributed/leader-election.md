---
name: Leader Election
slug: leader-election
family: 08-cloud-distributed
category: Coordination
aliases: [Master Election, Coordinator Election, Election Algorithm]
first_described: "Garcia-Molina 1982 (Bully Algorithm); Lamport 1998 (Paxos); Ongaro and Ousterhout 2014 (Raft)"
maturity: canonical
related: [saga, circuit-breaker, retry, bulkhead, health-endpoint-monitoring, competing-consumers]
incompatible_with: []
verified: 2026-08-02
---

# Leader Election

## 1. Name, aliases, and lineage

The canonical name in distributed systems literature is Leader Election, also
written coordinator election or master election in older papers. The problem
was first formalized by Hector Garcia-Molina in "Elections in a Distributed
Computing System", IEEE Transactions on Computers, volume C-31, issue 1,
January 1982. The paper introduced the Bully Algorithm. A process that
detects the coordinator has failed sends election messages to every process
with a higher identifier, and the highest surviving identifier declares
itself leader. The paper is available as a scanned reprint through IEEE
Xplore, DOI 10.1109/TC.1982.1675885, verified 2026-08-02.

A second lineage runs through consensus algorithms rather than pure election
algorithms. Leslie Lamport's Paxos, described in "The Part-Time Parliament",
ACM Transactions on Computer Systems, volume 16, issue 2, May 1998, treats
leader election as an optimization on top of a leaderless consensus protocol.
A distinguished proposer reduces the number of message rounds needed to
reach agreement, but Paxos remains correct even when two processes believe
they are the proposer at once, because the protocol's safety does not depend
on there being exactly one. Diego Ongaro and John Ousterhout's "In Search of
an Understandable Consensus Algorithm", USENIX ATC 2014, took the opposite
design stance. Raft makes leader election a first class, load bearing part of
the protocol, with randomized election timeouts and a strict term counter,
because the authors judged that a protocol organized around a single leader
would be easier for engineers to reason about and implement correctly. The
paper is available at [raft.github.io/raft.pdf](https://raft.github.io/raft.pdf)
(verified 2026-08-02), and the project's own summary page describes Raft
plainly as "a consensus algorithm that is designed to be easy to understand",
equivalent to Paxos in fault tolerance and performance
([raft.github.io](https://raft.github.io/), verified 2026-08-02).

A third, more practical lineage comes from Google's Chubby lock service, Mike
Burrows, "The Chubby Lock Service for Loosely-Coupled Distributed Systems",
OSDI 2006. Chubby popularized the pattern most engineers actually reach for
today. Rather than implementing an election algorithm directly, a service
elects a leader by racing to acquire an exclusive, lease backed lock in a
strongly consistent coordination service, and treats holding the lock as
synonymous with being the leader. Every coordination service in production
use descends from this design. Apache ZooKeeper, etcd, and Consul all
implement leader election as a thin recipe layered on top of a more
primitive lock or sequential node facility, not as a separate algorithm.

This entry treats Leader Election as it is actually built in 2026, as a
coordination pattern for electing a single active worker in a fleet of
otherwise interchangeable replicas, implemented on top of a strongly
consistent store, not as an academic exercise in implementing Bully or Raft
from a textbook. Raft and Paxos are covered here as the consensus substrate
the coordination services are built on, and as an implementation variant for
teams who embed a consensus library directly in their own service rather
than depending on an external coordinator.

## 2. Problem and context

A fleet of otherwise identical replicas exists for availability. If one
process dies, another must take over without a human paging anyone at 3 a.m.
But some part of the workload cannot safely run on more than one replica at
once. A cron style job that must fire exactly once per interval. A control
loop, of the kind Kubernetes runs for kube-controller-manager and
kube-scheduler, where two active copies computing conflicting decisions in
parallel would corrupt cluster state rather than merely waste CPU. A database
migration runner. A background compaction process that would double the
write amplification on a shared store if two nodes ran it concurrently. A
message consumer that must process a partition strictly in order, where two
consumers racing on the same partition would interleave writes and violate
the ordering guarantee the downstream system depends on.

The naive fix, running the singleton job on one designated box, throws away
availability. That box's failure now takes the job down with it, and every
operator ends up building an ad hoc "is the primary machine still up"
watchdog by hand. The pattern exists to keep the availability of a
horizontally scaled fleet while still enforcing that exactly one member does
the singleton work at any moment, and that when the current leader dies, a
survivor takes over automatically and quickly.

The context that makes this a genuinely hard problem, rather than a
straightforward feature, is that "exactly one" is a safety property being
enforced across machines that do not share memory, whose clocks drift
independently, and which can each independently experience an unbounded
pause. A stop the world garbage collection cycle, an oversubscribed
hypervisor stealing CPU, a kernel scheduling stall, or simply a slow disk
write blocking a thread everyone assumed was still running. Martin
Kleppmann's analysis of this problem is the standard citation. With an
unbounded pause possible on any node, no lease duration is ever provably
long enough, because "if the GC pause lasts longer than the lease expiry
period, and the client doesn't realise that it has expired, it may go ahead
and make some unsafe change"
([Kleppmann, "How to do distributed locking", 2016-02-08](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html),
verified 2026-08-02). Kleppmann further notes that HBase, a production
system, suffered exactly this failure historically, with observed GC pauses
running several minutes, well past any lease timeout a designer would
consider reasonable. Leader election is, at bottom, the pattern that manages
this inherent uncertainty rather than a pattern that eliminates it.

## 3. Forces

**Safety versus liveness.** These are the two properties consensus theory
separates explicitly, and Leader Election sits directly on the fault line
between them. Safety means at most one leader is ever recognized as
authoritative at a given moment. Liveness means a leader eventually exists
and eventually recovers after a failure. The trade here is that
strengthening safety, long confirmation windows, quorum reads on every
decision, weakens liveness, slower failover, longer windows with no active
leader, and the reverse is equally true. A design that never sacrifices
either does not exist. The honest engineering question is which one
degrades, and by how much, under a given failure.

**Split brain versus availability during partition.** A network partition can
leave two groups of nodes each believing they can see a majority. A design
that refuses to elect a new leader without provable majority contact
sacrifices availability during the partition, in exchange for the guarantee
that only one side can ever hold leadership. A design that prioritizes
staying available on both sides of a partition accepts the risk of two
leaders acting concurrently, the literal split brain, and must instead layer
another mechanism, most commonly fencing, to bound the damage.

**Detection speed versus false positive rate.** Failure detection in an
asynchronous network cannot distinguish "the leader crashed" from "the leader
is alive but a message was delayed". A short heartbeat interval detects a
real failure fast but false-triggers a costly re-election on transient
network jitter. A long interval is stable but leaves the singleton work
unattended for longer after a genuine crash. Every leader election
implementation embeds a specific choice here, usually a heartbeat interval,
a lease duration, and a missed-heartbeat threshold, and that choice is a
direct trade of mean time to recovery against false failover rate.

**Coordination cost versus operational simplicity.** Implementing a full
consensus protocol, Raft, Paxos, or a Paxos variant, inside the application
gives full control over the failure model but requires the team to run and
operate a consensus cluster correctly, including the quorum sizing, log
compaction, and membership change edge cases that make consensus hard to
implement correctly. Delegating to an external coordination service, etcd,
ZooKeeper, Consul, the Kubernetes API server, moves that operational burden
onto infrastructure the team likely already runs, at the cost of introducing
a dependency whose own availability now gates the application's ability to
elect a leader at all.

**Clock assumptions.** Lease based election, etcd, Chubby, Kubernetes Leases,
relies on a bounded clock drift assumption between the lock holder and the
lock service to make the lease duration meaningful. Log based consensus
election, Raft, relies instead on randomized election timeouts and does not
require synchronized wall clocks, but pays for that in extra message rounds
during every election. A design that silently assumes synchronized clocks
while running on hardware where that assumption does not hold, virtualized
cloud instances under CPU contention being the common offender, inherits
Kleppmann's failure mode without the team realizing they made that
assumption.

## 4. Applicability and non-applicability

**Reach for Leader Election when:**

- Exactly one instance of a periodic or singleton job must run across a fleet
  of otherwise interchangeable replicas, and the fleet must survive the loss
  of whichever instance is currently doing that work.
- A control loop or reconciliation process would corrupt shared state, or
  waste real resources, if two copies ran concurrently and neither
  copy is designed to be idempotent against the other's concurrent writes.
- The team already operates, or is willing to operate, a strongly consistent
  coordination service (etcd, ZooKeeper, Consul) or already runs on a
  platform that exposes one (Kubernetes Leases, cloud provider managed Paxos
  or Raft services).
- The cost of a brief gap with no active leader, during the failover window,
  is acceptable to the business, because that gap is inherent to the pattern
  and cannot be engineered away entirely.

**Do NOT reach for Leader Election when:**

- The work is naturally idempotent and safe to run concurrently from
  multiple workers. Competing Consumers with a durable queue, the queue's
  own visibility timeout or acknowledgment semantics prevent double
  processing, solves the same shape of problem without the coordination
  overhead of an election, and scales the work across all replicas instead
  of concentrating it on one.
- The work can be partitioned deterministically ahead of time, for example
  by consistent hashing a key space across a fixed set of workers, so each
  worker owns a disjoint slice permanently rather than the whole fleet
  contending for one shared role. Static partitioning removes the failover
  latency window entirely for the partitions that stay assigned, and trades
  that for a harder rebalancing problem when the fleet size changes.
- A single, non-redundant instance is genuinely acceptable, and the team
  would rather accept that instance's downtime as a known, monitored risk
  than take on a coordination dependency. This is a legitimate choice for
  low-stakes internal tooling, not a compromise that needs justifying every
  time.
- The application cannot tolerate even a brief window with two believed
  leaders and cannot add a fencing mechanism to the downstream resource
  being protected. If the protected resource cannot reject a stale writer,
  no compare-and-swap, no monotonic token check, no unique constraint, no
  election algorithm alone makes concurrent writers from two believed
  leaders safe, because the unbounded pause problem from Section 2 is
  intrinsic to distributed systems and not specific to any one election
  implementation.
- The team has no operational capacity to run or depend on a coordination
  service, and the platform they deploy to does not provide one. Building a
  from-scratch Raft or Paxos implementation for a single feature is rarely
  the right trade against adopting an existing coordination primitive.

## 5. Structure

**Candidate.** A process instance that is eligible to become the leader. In a
horizontally scaled deployment, every replica of a service is typically a
candidate. A candidate that is not currently the leader is a follower or a
standby, and it is expected to be doing one of two things, watching for the
current leader to disappear, or actively performing the singleton work if it
holds leadership.

**Coordination service (or embedded consensus module).** The strongly
consistent store that arbitrates who holds leadership. This is the
participant that provides the safety guarantee. It is the single source of
truth for who is currently the leader, and every candidate's belief about
leadership must ultimately be checked against it, not cached indefinitely.
Concretely this is etcd, Apache ZooKeeper, Consul, or the Kubernetes API
server's Lease resource. In an embedded design it is a Raft or Paxos group
running inside the application's own process fleet rather than delegated to
an external service.

**Lease, or sequential node, or term.** The concrete unit of leadership the
coordination service issues. In lease based designs, etcd, Chubby,
Kubernetes Leases, this is a time bounded grant that must be renewed before
it expires. In sequential-ephemeral-node designs, ZooKeeper, this is instead
a strict ordering assigned at creation time combined with automatic cleanup
on session loss, with no independent time bound of its own. In log based
consensus designs, Raft, this is a monotonically increasing term number, and
leadership for a given term is established by winning a majority vote, not
by holding a time bounded grant.

**Fencing token.** A monotonically increasing number, tied to the lease or
term, that the current leader must attach to every write it sends to
whatever resource it is protecting. This participant closes the gap between
the coordination service believing X is the leader and the protected
resource being able to safely tell a genuine current leader apart from a
stale one that has not yet noticed its lease expired. Kleppmann is explicit
that this participant is not optional if the design must be safe under an
unbounded pause. The storage service on the receiving end must itself
"remember that it has already processed a write with a higher token
number... and so it rejects the request with [a lower] token"
([Kleppmann 2016-02-08](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html),
verified 2026-08-02).

**Health check or heartbeat mechanism.** The signal that determines when the
current leader is considered gone and a new election should start. This can
be implicit in the coordination primitive itself, an ephemeral ZooKeeper node
disappearing when its owning session's TCP connection drops or its heartbeat
lapses, or explicit, a lease that a Kubernetes controller must actively renew
by writing an updated renewTime before leaseDurationSeconds elapses.

**Followers' watch mechanism.** How non-leader candidates learn that
leadership has changed. In ZooKeeper's recipe this is a watch set on exactly
one other node, chosen deliberately to avoid every follower waking up at
once, described in the official recipes documentation. "The idea is to have
a znode... such that each znode creates a child znode... with both flags
SEQUENCE|EPHEMERAL", and a candidate "avoids the herd effect by not having
all clients watching the same znode"
([Apache ZooKeeper, ZooKeeper Recipes and Solutions, Leader Election](https://zookeeper.apache.org/doc/current/recipes.html),
verified 2026-08-02). In lease based designs this is instead typically a
periodic poll of the lease's current holder and expiry time, since these
systems do not always provide a native long-poll watch primitive with the
same herd-avoidance property.

## 6. ASCII structure diagram

```
                        +---------------------------+
                        |   Coordination Service     |
                        |  (etcd / ZooKeeper /       |
                        |   Consul / k8s API server)  |
                        |                             |
                        |  holds: current lease/term  |
                        |  issues: fencing token       |
                        +--------------+--------------+
                                       |
                 elect / renew / watch |  grant / expire / notify
                                       |
        +------------------------------+------------------------------+
        |                              |                              |
        v                              v                              v
  +-----------+                  +-----------+                  +-----------+
  | Candidate |                  | Candidate |                  | Candidate |
  |  node-a   |<--- watches ---- |  node-b   |<--- watches ---- |  node-c   |
  |           |                  | (leader)  |                  |           |
  | standby   |                  | performs  |                  | standby   |
  +-----------+                  | singleton |                  +-----------+
                                  |   work    |
                                  +-----+-----+
                                        |
                          writes with fencing token
                                        |
                                        v
                              +-------------------+
                              | Protected Resource |
                              | (rejects stale     |
                              |  fencing tokens)    |
                              +-------------------+
```

## 7. Dynamics

```
Normal operation
-----------------
node-b: acquire(lease) -> coordination service grants lease, token=42
node-b: becomes leader, begins singleton work
node-a, node-c: watch node-b (directly or via lease expiry poll)
node-b: renew(lease) every renewInterval < leaseDuration
node-b: write(resource, token=42) -> resource accepts, 42 > highestSeen

Leader failure and re-election
-------------------------------
node-b: crashes, or stalls past leaseDuration (GC pause, CPU starvation)
coordination service: lease expires, ephemeral node removed, or heartbeat missed
node-a: detects the change (watch fires, or poll sees expired lease)
node-c: detects the change independently
node-a, node-c: both attempt acquire(lease) at ~the same time
coordination service: grants to exactly one, say node-a, token=43
node-c: acquire fails, remains standby, watches node-a
node-a: becomes leader, begins singleton work with token=43

The dangerous case this pattern must survive
----------------------------------------------
node-b: was paused past leaseDuration but did NOT crash
node-b: resumes execution, still believes it holds the lease
node-b: write(resource, token=42) -> resource has highestSeen=43
resource: REJECTS the write, because 42 < 43
node-b: (correctly) discovers it is no longer leader, steps down
```

The critical property visible in the third block is that safety here is
enforced by the protected resource checking the fencing token, not by
node-b's own belief about its leadership status. Node-b's local state is
unreliable after an unbounded pause. The resource's compare-and-reject check
is not, because it depends only on a monotonic counter and a comparison,
both of which are safe to evaluate locally at the resource without any
further coordination.

## 8. Implementation variants

**Lease based, external coordination service.** The dominant production
pattern. A candidate calls an atomic acquire-or-renew operation against
etcd, Consul, or an equivalent store. The store either grants the lease to
the caller, confirms the caller already holds it, or refuses because someone
else holds an unexpired lease. etcd's own concurrency documentation frames
this directly. "common distributed patterns using etcd include leader
election, distributed locks, and monitoring machine liveness"
([etcd documentation, "Why etcd"](https://etcd.io/docs/v3.6/learning/why/),
verified 2026-08-02), and the mechanism combines a lease's TTL with etcd's
per-key revision number so that mutual exclusion is enforced by the
combination of revision number and lease ID, not by the TTL in isolation.

**Sequential ephemeral node, ZooKeeper style.** Each candidate creates a
sequentially numbered, session bound node under a shared election path. The
candidate holding the lowest sequence number is the leader. Every other
candidate watches only the node immediately below its own sequence number,
per the herd-avoidance design described in Section 5. When a session drops,
whether from a crash, a network partition, or a missed heartbeat, ZooKeeper's
server side removes the corresponding ephemeral node automatically, which is
what triggers the watch on the next candidate in line.

**Kubernetes Lease objects.** A Kubernetes native variant in which the
coordination service is the Kubernetes API server itself, and the lease is a
first class API resource in the coordination.k8s.io group. The official
documentation states plainly that Kubernetes uses Leases so that only one
instance of a component is running at any given time, and that this is used
by control plane components like kube-controller-manager and kube-scheduler
in HA configurations
([Kubernetes documentation, Leases](https://kubernetes.io/docs/concepts/architecture/leases/),
verified 2026-08-02). The same document explicitly invites application
authors to define their own Lease objects for custom controllers. "You define
a Lease so that the controller replicas can select or elect a leader, using
the Kubernetes API for coordination." The client-go leaderelection package
implements this variant as a reusable library most controller authors
consume rather than reimplement.

**Session and lock based, Consul style.** Consul frames the same pattern
around its session and key-value lock primitives rather than a lease API.
Consul's support for sessions and watches allows building a client-side
leader election process where clients use a lock on a key in the KV datastore
for mutual exclusion, with graceful handling of failures
([HashiCorp Consul documentation, Leader Election](https://developer.hashicorp.com/consul/docs/dynamic-app-config/sessions/application-leader-election),
verified 2026-08-02). The recommended pattern is a well-known key path such
as service/serviceName/leader, where a Consul session ties the lock's
lifetime to a configurable set of health checks, so the lock is released
automatically if the holding process's health check fails.

**Embedded consensus, Raft or Paxos in-process.** Rather than depending on an
external coordination service, the application embeds a consensus library,
HashiCorp's raft package, etcd-io/raft, or a custom implementation, and runs
the consensus protocol among its own replicas directly. Leadership here is
intrinsic to the consensus algorithm's term mechanism. A candidate that wins
a majority vote for a given term is the leader for that term, with no
separate acquire-a-lock step layered on top. This variant removes the
external coordination service as a dependency but obliges the team to
operate a correctly sized, correctly quorate consensus group themselves, and
it is usually chosen only by teams building the coordination service itself,
a database, a distributed cache, a message broker, rather than by teams
building an application that merely needs one singleton job.

**Database backed advisory lock.** A lighter weight variant common in
smaller deployments already running a relational database. PostgreSQL's
advisory locks, pg_try_advisory_lock, or a row with a compare-and-swap
UPDATE with a WHERE clause on the expected holder, provide a poor man's
lease. This variant trades away watch based notification, so followers must
poll, and it inherits whatever availability characteristics the single
database instance has, which is frequently weaker than a purpose built
coordination service's, but it avoids introducing a new operational
dependency for a team that already runs and trusts the database.

## 9. Known production uses

- **Kubernetes control plane.** kube-controller-manager and kube-scheduler
  run as multiple replicas in high availability clusters and use the Lease
  based leader election described in Section 8 so only one replica of
  each is actively reconciling cluster state at a time, per the Kubernetes
  project's own architecture documentation
  ([Kubernetes documentation, Leases](https://kubernetes.io/docs/concepts/architecture/leases/),
  verified 2026-08-02).
- **etcd itself, and systems built on it.** etcd's concurrency package ships
  a leader election primitive that etcd's own documentation names directly
  as one of the "common distributed patterns" the store is designed to
  support ([etcd documentation, "Why etcd"](https://etcd.io/docs/v3.6/learning/why/),
  verified 2026-08-02). This primitive is consumed by numerous downstream
  systems, most visibly by Kubernetes itself, whose control plane state
  store is etcd.
- **Apache ZooKeeper deployments across Hadoop-ecosystem and Kafka-adjacent
  infrastructure.** ZooKeeper's Leader Election recipe, described in its own
  official recipes documentation, is the pattern historically used by Apache
  HBase to elect a single active HMaster, and by Apache Kafka prior to
  Kafka's 2022 migration to KRaft, to elect the controller broker
  responsible for partition leader assignment
  ([Apache ZooKeeper, Recipes and Solutions](https://zookeeper.apache.org/doc/current/recipes.html),
  verified 2026-08-02).
- **HashiCorp Consul based service fleets.** Consul's documented leader
  election pattern using sessions and KV locks is the mechanism HashiCorp
  itself recommends for applications that already run Consul for service
  discovery and want to add singleton coordination without a second
  coordination service
  ([Consul documentation, Application Leader Election](https://developer.hashicorp.com/consul/docs/dynamic-app-config/sessions/application-leader-election),
  verified 2026-08-02).
- **Databases and distributed systems built on embedded Raft.** CockroachDB,
  etcd itself, which is built on the etcd-io/raft library, HashiCorp Consul's
  own internal server cluster, and HashiCorp Vault's high availability mode
  each use an embedded Raft implementation to elect a single active leader
  among their own server replicas, distinct from the application level
  leader election these systems expose to their clients as described above.
  This is the design point Ongaro and Ousterhout targeted directly. A
  consensus algorithm intended to be implementable correctly by engineering
  teams building real systems, not only a theoretical construct
  ([Ongaro and Ousterhout, "In Search of an Understandable Consensus Algorithm"](https://raft.github.io/raft.pdf),
  verified 2026-08-02).

## 10. Consequences

**Positive.**

- A singleton job or control loop can run on a horizontally scaled,
  disposable fleet instead of a hand-maintained single instance, gaining
  automatic failover without a human intervening.
- Failover latency becomes a tunable, observable parameter, the lease
  duration or election timeout, rather than an unbounded process of someone
  noticing the box is down and restarting the job by hand.
- When combined with fencing tokens, the pattern gives a provable safety
  guarantee even under the pathological failure case of an arbitrarily long
  pause on the previous leader, which is a stronger guarantee than most
  teams realize they need until Kleppmann's analysis makes it explicit.
- Delegating to an existing coordination service, etcd, ZooKeeper, Consul,
  Kubernetes, means most teams get this guarantee by consuming a
  well-tested library rather than by writing consensus code themselves.

**Negative.**

- The pattern introduces a hard dependency on the coordination service's own
  availability. If etcd, ZooKeeper, or the Kubernetes API server is
  unreachable, the application cannot determine who the leader is, and most
  implementations correctly choose to have every candidate step down rather
  than guess, which means the singleton work stops entirely during a
  coordination service outage, even if every application replica is
  healthy.
- There is an inherent, non-zero window during every failover in which no
  leader is active, bounded below by however long the coordination service
  takes to detect the previous leader's failure and grant a new lease or
  term. Applications that need singleton work performed with near-zero
  interruption cannot get that from this pattern alone.
- Without fencing tokens, the pattern is unsafe under the unbounded pause
  scenario described in Section 2, and adding fencing tokens after the fact
  usually requires a schema or API change to the protected resource, which
  is significantly more expensive than designing it in from the start.
- Operating an external coordination service correctly, with proper quorum
  sizing, disk performance for its write-ahead log, and monitoring for its
  own leader election, is a genuine additional operational burden, and teams
  that underinvest in it discover the coordination service itself becomes
  their least reliable dependency.

## 11. Failure modes and misuse

**Symptom.** Two processes both perform the singleton work simultaneously,
visible as duplicate writes, double-charged customers, or a corrupted shared
resource.
**Cause.** The protected resource has no fencing token check, so a stale
leader that resumes after an unbounded pause writes successfully even though
the coordination service has already granted leadership to someone else.
**Fix.** Add a monotonically increasing token to the protected resource's
write path and reject any write whose token is not at least as high as the
highest one previously accepted, exactly as Kleppmann prescribes.

**Symptom.** Leadership flaps rapidly between two or three nodes under
normal load, visible as repeated "became leader" and "lost leadership" log
lines within seconds of each other.
**Cause.** The heartbeat interval or lease renewal interval is too close to
the lease duration itself, so ordinary network jitter or garbage collection
pauses well within normal operating bounds are enough to miss a renewal
deadline.
**Fix.** Widen the ratio between renewal interval and lease duration, a
common rule of thumb being renewal at roughly one third of the lease
duration, and separately investigate why the renewing process is pausing
for that long in the first place, since the flapping is frequently a symptom
of an unrelated performance problem surfacing through the election
mechanism.

**Symptom.** After a coordination service outage or network partition, no
leader is elected even once connectivity is restored, and the singleton
work stays stopped indefinitely.
**Cause.** An implementation bug in which a candidate that failed to acquire
the lease during the outage does not retry the acquisition loop, only its
renewal loop, so a candidate that was never leader before the outage has no
code path that brings it back into contention afterward.
**Fix.** The acquisition attempt and the renewal attempt should be the same
code path, an idempotent acquire-or-renew call issued on every tick
regardless of the candidate's currently believed role, which is how etcd's
concurrency package and the Kubernetes client-go leaderelection package are
both structured.

**Symptom.** The coordination service reports a clean single leader at all
times, but the downstream system it protects still shows evidence of
concurrent writers, and the team concludes the coordination service itself
is buggy.
**Cause.** This is very rarely a bug in the coordination service. It is
almost always the unbounded pause scenario from Section 2 combined with a
missing fencing token, and the coordination service is behaving entirely
correctly by its own guarantees, which only ever promise that it will not
simultaneously grant the same lease or term to two candidates, never that a
candidate cannot act on stale local state after its lease has already
expired elsewhere.
**Fix.** Treat this as a fencing token gap, not a coordination service
defect, and verify the protected resource actually enforces the token
before concluding otherwise.

**Symptom.** Election takes an unexpectedly long time to converge on a
large fleet, well beyond the configured timeout, visible as many candidates
all attempting to acquire the lease at once in a thundering herd.
**Cause.** Every candidate is watching the same shared is-there-a-leader
signal directly rather than following the ZooKeeper-style
predecessor-watching pattern, so a single leader failure wakes every
follower simultaneously and they all attempt acquisition at once, adding
contention exactly when the system is trying to recover quickly.
**Fix.** Stagger acquisition attempts with jitter, or, where the
coordination primitive supports it, adopt the sequential-node
predecessor-watch structure so only one follower is woken per failure
rather than the entire fleet.

## 12. Trade-off matrix

| Concern | Leader Election | Competing Consumers | Static Partitioning (consistent hashing) |
|---|---|---|---|
| Handles non-idempotent singleton work | Yes, by design | No, requires idempotent work | Yes, per partition |
| Failover latency | Bounded by lease/election timeout, typically seconds | None, any consumer can pick up any message | None for a live partition, but rebalance latency on membership change |
| Requires external coordination service | Yes (or an embedded consensus module) | No, only a durable queue with visibility timeouts | No, only a consistent hash ring and membership tracking |
| Scales work across the fleet | No, work stays on one node until failover | Yes, work spreads across all consumers | Yes, work is pre-spread across partitions |
| Safety under a leader's unbounded pause | Only with fencing tokens on the protected resource | N/A, no single-writer assumption to violate | Requires fencing at the partition boundary during rebalance |
| Operational cost | Coordination service to run and monitor | Queue's own operational cost, usually already present | Membership tracking and rehashing logic |

## 13. Related and incompatible patterns

**Saga.** A saga coordinates a multi-step business transaction across
several services, and the orchestration variant of Saga specifically needs
exactly one orchestrator instance driving a given saga instance forward at a
time. Leader Election is frequently the mechanism that guarantees a saga
orchestrator fleet has exactly one active coordinator, making the two
patterns compose directly rather than compete.

**Circuit Breaker.** Independent of Leader Election, but commonly deployed
alongside it on the same call path. The elected leader still needs to
protect itself from a failing downstream dependency while it performs the
singleton work, and Circuit Breaker is the standard mechanism for that,
unrelated to which node is currently the leader.

**Health Endpoint Monitoring.** Most leader election implementations depend
on a health signal, whether that is a coordination service's own session
heartbeat or an explicit application level health check tied to a lock's
lease, to decide when the current leader should be considered gone. The two
patterns are frequently implemented as the same subsystem in practice.

**Competing Consumers.** The direct alternative discussed in Sections 4 and
12, not a composed pattern. A team choosing Leader Election over Competing
Consumers is choosing a single active worker over a pool of concurrently
active workers, for work that cannot tolerate concurrent execution.

**Bulkhead.** Orthogonal. Bulkhead isolates failure domains within a single
process or service by partitioning resources like thread pools or
connections. It says nothing about which process, among a fleet, is
authoritative. The two compose without conflict when the elected leader
itself wants to isolate its own internal resource pools.

**Incompatible with.** No pattern in this catalog is structurally
incompatible with Leader Election in the sense of the two being unable to
coexist in the same system. The closest to a genuine conflict is applying
Leader Election to work that Competing Consumers already handles correctly.
Layering an election on top of naturally idempotent, horizontally
parallelizable work adds coordination overhead and a failover latency
window for no safety benefit, which is a misapplication rather than a true
incompatibility.

## 14. Refactoring path in and out

**Introducing Leader Election into a system that currently runs a singleton
job on a single, manually managed instance.**

1. Identify the exact write path that must never be executed by two writers
   concurrently, and confirm it is genuinely non-idempotent. If it can be
   made idempotent with reasonable effort, prefer that and stop here,
   adopting Competing Consumers instead.
2. Choose a coordination service. If the deployment platform already
   provides one, Kubernetes Leases on a Kubernetes deployment, Consul
   sessions on a Consul-managed fleet, prefer it over introducing a new
   dependency.
3. Wrap the singleton work's entry point in an acquire-or-renew loop
   against the chosen coordination service, using a well-tested client
   library, client-go's leaderelection package, etcd's concurrency package,
   a ZooKeeper recipes library, rather than a hand rolled implementation.
4. Add a fencing token to the protected resource's write path before
   removing the old single-instance deployment, not after. This ordering
   matters. The most dangerous window is the transition period when both
   the old single-instance process and the new elected fleet might briefly
   coexist.
5. Deploy the new fleet alongside the old single instance, verify via logs
   or metrics that exactly one leader is elected and the fencing token
   correctly rejects a deliberately injected stale write in a staging
   environment, then decommission the old single instance.

**Removing Leader Election once it is no longer justified**, typically
because the underlying work has since been made idempotent, or because the
team has moved the workload onto a managed platform primitive, a cloud
provider's managed cron, a serverless scheduled function with a provider
guaranteed single invocation, that removes the need to build this
coordination in-house.

1. Confirm the replacement mechanism's own single-invocation or idempotency
   guarantee is real and sourced from its provider's documentation, not
   assumed.
2. Migrate the singleton work's callers to the replacement mechanism while
   the election based implementation is still running, verifying no
   duplicate execution occurs during the overlap window.
3. Remove the acquire-or-renew loop and the coordination service dependency
   only after the replacement has run in production long enough to observe
   at least one of its own failover or retry events, confirming its
   guarantee holds under real failure, not only under the happy path.
4. Leave the fencing token check on the protected resource in place even
   after the election code is removed, if any other client of that
   resource could plausibly still send a stale write. Removing a safety
   check is a separate decision from removing the coordination pattern
   that originally motivated it.

## 15. Testing and verification

Unlike most patterns in this catalog, testing this pattern correctly
requires proving a negative under an adversarial condition, not merely
exercising the happy path.

**Unit level.** Test the fencing token check on the protected resource in
isolation, independent of any real coordination service. Given a sequence
of writes with tokens 1, 2, 5, and 3, assert the write with token 3 is
rejected because it arrives after token 5 was already accepted, regardless
of the order the caller intended. This is the cheapest, highest value test
in the whole pattern, because it directly verifies the property that makes
the pattern safe.

**Integration level, against a real or embedded coordination service.**
Run the actual acquire-or-renew loop against a real etcd, ZooKeeper, or
Consul instance, or an embedded, in-process equivalent used for testing,
such as etcd's integration test fixture, and verify three things. A fresh
candidate can acquire when no leader exists. A second candidate is refused
while a valid lease is held. The second candidate successfully acquires
once the first candidate's process is killed and its lease naturally
expires.

**Chaos and fault injection level.** This is where the pattern's actual
claim gets tested. Deliberately pause the current leader process past its
lease duration, a SIGSTOP followed by a delayed SIGCONT is a close, cheap
simulation of the GC pause Kleppmann describes, and verify two things
together. A new leader is correctly elected while the old one is paused,
and the old leader's subsequent write, once it resumes and attempts to act
on its stale belief that it is still leader, is rejected by the fencing
token check. A test suite that only verifies the first half of this and
never resumes the paused process to check the second half has not actually
tested the property this pattern exists to provide.

**Test doubles.** A fake coordination service that implements the same
acquire-or-renew interface in memory, with an injectable clock, is the
standard technique for making the timing dependent scenarios above
deterministic and fast rather than reliant on real wall clock sleeps, which
is exactly what the code examples in Section 8 and the implementation note
below demonstrate at a small scale.

## 16. Observability signals

- **Current leader identity**, exposed as a gauge or a labeled metric per
  candidate, so a dashboard can show at a glance which instance currently
  believes itself the leader, and a monitoring rule can alert if two
  instances report themselves as leader simultaneously, which should never
  happen and is the single highest value alert this pattern can have.
- **Leadership transition count and timestamp**, incremented every time a
  candidate acquires leadership, with the previous leader's identity
  attached if known, to distinguish healthy, infrequent failovers from the
  flapping failure mode described in Section 11.
- **Time since last successful renewal**, tracked from the current leader's
  perspective, as a leading indicator of an impending unwanted failover
  before the lease actually expires. A value trending upward toward the
  lease duration is a warning sign worth alerting on independently of an
  actual failover event.
- **Fencing token rejection count**, on the protected resource, incremented
  every time a write is rejected for carrying a stale token. This metric
  should normally read zero. A non-zero value proves the safety mechanism
  fired and prevented an actual split brain write, which is valuable
  evidence that the unbounded pause scenario is not merely theoretical in
  this deployment, and worth alerting on even though it represents the
  system behaving correctly, because it indicates the underlying pause
  condition that caused it is still worth investigating.
- **Coordination service availability**, tracked independently of the
  application's own health, since Section 10 notes the application's
  ability to elect a leader at all is gated on this dependency. An outage
  here should surface as its own distinct alert rather than being conflated
  with no leader elected, which has a different root cause and a different
  remediation.

## 17. Security and privacy implications

The coordination service itself becomes a high value target. An attacker
who can write to the election key, lease, or znode path can force an
election, or worse, forge a claim to leadership without going through the
intended candidate processes at all. Access to the specific keys or paths
used for election should be restricted with the coordination service's own
authentication and authorization mechanism, etcd's role based access
control, ZooKeeper's ACLs, Consul's ACL system, or Kubernetes RBAC scoped to
the specific Lease resource, separate from and in addition to whatever
broader access the coordination service grants for other purposes.

Fencing tokens themselves carry no confidential information and need no
privacy protection. They are safe to log and expose in metrics without
redaction, which is useful given how central they are to debugging the
failure modes in Section 11.

A leader that has been compromised, rather than merely paused, is a threat
this pattern does not address at all. Fencing tokens defend against a stale
but otherwise honest leader continuing to act after its lease has silently
expired. They provide no defense against an actively malicious process
that holds a currently valid lease and is using it to perform unauthorized
writes. Leader Election is a coordination pattern, not an authorization
mechanism, and the protected resource's own authorization checks on the
leader's identity remain necessary regardless of whether that identity
currently holds a valid lease.

## Implementation note

The three examples below each isolate one variant from Section 8 in a form
small enough to run without a live coordination service, so the safety
property in question can be demonstrated deterministically rather than
observed only under real network timing. None of them is a production
implementation. Each omits retry backoff, TLS, and the coordination
service's own client library in favor of showing the core mechanism
plainly.

### Fencing token enforcement (Go), the lease based variant from Section 8

```go
package main

import (
	"errors"
	"fmt"
	"sync"
)

// FencedStore models a storage service that rejects writes carrying a
// fencing token lower than the highest token it has already accepted.
type FencedStore struct {
	mu          sync.Mutex
	highestSeen int64
	value       string
}

func (s *FencedStore) Write(token int64, value string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if token < s.highestSeen {
		return fmt.Errorf("write rejected, token %d is behind highest seen token %d", token, s.highestSeen)
	}
	s.highestSeen = token
	s.value = value
	return nil
}

// LeaseElector grants a single lease at a time and hands out a strictly
// increasing fencing token with every grant, mirroring etcd's revision
// number attached to a lease.
type LeaseElector struct {
	mu      sync.Mutex
	token   int64
	current string
}

func (e *LeaseElector) Acquire(candidate string) (int64, error) {
	e.mu.Lock()
	defer e.mu.Unlock()
	if e.current != "" && e.current != candidate {
		return 0, errors.New("lease already held")
	}
	e.token++
	e.current = candidate
	return e.token, nil
}

func (e *LeaseElector) Expire() {
	e.mu.Lock()
	defer e.mu.Unlock()
	e.current = ""
}

func main() {
	elector := &LeaseElector{}
	store := &FencedStore{}

	tokenA, err := elector.Acquire("node-a")
	if err != nil {
		panic(err)
	}
	fmt.Printf("node-a acquired lease with fencing token %d\n", tokenA)

	// Simulate a long GC pause on node-a. Its lease silently expires and a
	// second node acquires a fresh lease with a higher token before node-a
	// resumes and tries to write with its now-stale token.
	elector.Expire()
	tokenB, err := elector.Acquire("node-b")
	if err != nil {
		panic(err)
	}
	fmt.Printf("node-b acquired lease with fencing token %d after node-a's lease expired\n", tokenB)

	if err := store.Write(tokenB, "written by node-b"); err != nil {
		panic(err)
	}
	fmt.Println("node-b's write accepted")

	if err := store.Write(tokenA, "written by stale node-a"); err != nil {
		fmt.Println("stale write from node-a correctly rejected,", err)
	} else {
		panic("split brain, stale writer was accepted")
	}
}
```

Compiled and run with `go run` on Go 1.x. Output.

```
node-a acquired lease with fencing token 1
node-b acquired lease with fencing token 2 after node-a's lease expired
node-b's write accepted
stale write from node-a correctly rejected, write rejected, token 1 is behind highest seen token 2
```

### Sequential ephemeral node election (Python), the ZooKeeper variant from Section 8

```python
"""Simulates the ZooKeeper sequential ephemeral znode leader election
recipe. Each candidate creates a sequence numbered node under an
election path. The candidate with the lowest sequence number is the
leader. Every other candidate watches only the node immediately below
its own number, avoiding the herd effect."""

from dataclasses import dataclass, field


@dataclass
class ElectionPath:
    next_seq: int = 0
    nodes: dict[int, str] = field(default_factory=dict)

    def create_candidate(self, name: str) -> int:
        seq = self.next_seq
        self.next_seq += 1
        self.nodes[seq] = name
        return seq

    def remove(self, seq: int) -> None:
        self.nodes.pop(seq, None)

    def predecessor_of(self, seq: int) -> int | None:
        lower = [s for s in self.nodes if s < seq]
        return max(lower) if lower else None

    def leader(self) -> str | None:
        if not self.nodes:
            return None
        return self.nodes[min(self.nodes)]


def run_election(path: ElectionPath, candidates: list[str]) -> list[tuple[str, str]]:
    log: list[tuple[str, str]] = []
    seqs: dict[str, int] = {}
    for name in candidates:
        seq = path.create_candidate(name)
        seqs[name] = seq
        pred = path.predecessor_of(seq)
        role = "leader" if pred is None else f"watches seq {pred}"
        log.append((name, f"joined at seq {seq}, {role}"))

    while path.nodes:
        current_leader = path.leader()
        log.append((current_leader, f"is leader, election path has {len(path.nodes)} node(s)"))
        path.remove(seqs[current_leader])

    return log


if __name__ == "__main__":
    path = ElectionPath()
    for name, event in run_election(path, ["node-a", "node-b", "node-c"]):
        print(f"{name}: {event}")
```

Run with `python3`. Output.

```
node-a: joined at seq 0, leader
node-b: joined at seq 1, watches seq 0
node-c: joined at seq 2, watches seq 1
node-a: is leader, election path has 3 node(s)
node-b: is leader, election path has 2 node(s)
node-c: is leader, election path has 1 node(s)
```

### Lease renewal and expiry (TypeScript), the Kubernetes Lease variant from Section 8

```typescript
// Models the Kubernetes Lease object pattern. A single Lease record carries
// holderIdentity, leaseDurationSeconds, and a renewTime. A candidate becomes
// leader by writing its identity into the lease, and must renew before
// leaseDurationSeconds elapses or another candidate may take over.

interface Lease {
  holderIdentity: string | null;
  leaseDurationSeconds: number;
  renewTime: number;
}

class LeaseStore {
  private lease: Lease = { holderIdentity: null, leaseDurationSeconds: 15, renewTime: 0 };

  private isExpired(now: number): boolean {
    return now - this.lease.renewTime > this.lease.leaseDurationSeconds;
  }

  tryAcquireOrRenew(candidate: string, now: number): boolean {
    if (
      this.lease.holderIdentity === null ||
      this.isExpired(now) ||
      this.lease.holderIdentity === candidate
    ) {
      this.lease.holderIdentity = candidate;
      this.lease.renewTime = now;
      return true;
    }
    return false;
  }

  currentHolder(): string | null {
    return this.lease.holderIdentity;
  }
}

function main(): void {
  const store = new LeaseStore();

  console.log("t=0  node-a acquires:", store.tryAcquireOrRenew("node-a", 0));
  console.log("t=5  node-b tries, lease still fresh:", store.tryAcquireOrRenew("node-b", 5));

  const stallEnd = 0 + 15 + 1;
  console.log(`t=${stallEnd} node-b takes over after expiry:`, store.tryAcquireOrRenew("node-b", stallEnd));
  console.log("current holder:", store.currentHolder());

  console.log(`t=${stallEnd + 1} stale node-a tries to renew:`, store.tryAcquireOrRenew("node-a", stallEnd + 1));
  console.log("current holder after stale renew attempt:", store.currentHolder());
}

main();
```

Compiled with `tsc --target es2020 --module commonjs` and run with `node`.
Output.

```
t=0  node-a acquires: true
t=5  node-b tries, lease still fresh: false
t=16 node-b takes over after expiry: true
current holder: node-b
t=17 stale node-a tries to renew: false
current holder after stale renew attempt: node-b
```

Swift and Java are omitted here not because the pattern does not translate.
Production Kubernetes controllers are frequently written in Go and the
client-go library is the reference implementation most teams actually
depend on, so Go was chosen as the primary example over a fourth or fifth
language repeating the same acquire-or-renew shape.

## 18. References

- Hector Garcia-Molina, "Elections in a Distributed Computing System", IEEE
  Transactions on Computers, volume C-31, issue 1, January 1982, DOI
  10.1109/TC.1982.1675885. Original formalization of the leader election
  problem and the Bully Algorithm.
- Leslie Lamport, "The Part-Time Parliament", ACM Transactions on Computer
  Systems, volume 16, issue 2, May 1998. Original Paxos paper.
- Diego Ongaro and John Ousterhout, "In Search of an Understandable Consensus
  Algorithm", USENIX ATC 2014,
  [raft.github.io/raft.pdf](https://raft.github.io/raft.pdf), verified
  2026-08-02.
- [raft.github.io](https://raft.github.io/), the Raft project's own summary
  page, verified 2026-08-02.
- Mike Burrows, "The Chubby Lock Service for Loosely-Coupled Distributed
  Systems", OSDI 2006. Origin of the lock-based, lease-driven leader election
  pattern used by essentially every modern coordination service.
- Martin Kleppmann, "How to do distributed locking",
  [martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html),
  2016-02-08, verified 2026-08-02. Source for the unbounded pause problem and
  the fencing token remedy.
- etcd documentation, "Why etcd",
  [etcd.io/docs/v3.6/learning/why/](https://etcd.io/docs/v3.6/learning/why/),
  verified 2026-08-02.
- Apache ZooKeeper, "ZooKeeper Recipes and Solutions", Leader Election
  section,
  [zookeeper.apache.org/doc/current/recipes.html](https://zookeeper.apache.org/doc/current/recipes.html),
  verified 2026-08-02.
- Kubernetes documentation, "Leases",
  [kubernetes.io/docs/concepts/architecture/leases/](https://kubernetes.io/docs/concepts/architecture/leases/),
  verified 2026-08-02.
- HashiCorp Consul documentation, "Application Leader Election",
  [developer.hashicorp.com/consul/docs/dynamic-app-config/sessions/application-leader-election](https://developer.hashicorp.com/consul/docs/dynamic-app-config/sessions/application-leader-election),
  verified 2026-08-02.
