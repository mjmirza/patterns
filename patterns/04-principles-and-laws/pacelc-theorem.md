---
name: PACELC Theorem
slug: pacelc-theorem
family: 04-principles-and-laws
category: Principle
aliases: [PACELC, PACELC Design Principle, Abadi's Extension to CAP]
first_described: "Abadi 2010 (blog), Abadi 2012 (formal paper)"
maturity: canonical
related: [cap-theorem, quorum-consensus, eventual-consistency, saga, circuit-breaker, bulkhead]
incompatible_with: []
verified: 2026-08-02
---

# PACELC Theorem

## 1. Name, aliases, and lineage

The canonical name is PACELC, pronounced "pass-elk" in most conference talks
and written as a single acronym rather than an initialism read letter by
letter. It stands for Partition, Availability, Consistency, Else, Latency,
Consistency. It is also called the PACELC design principle, and less often
Abadi's extension to CAP, because it was proposed as a direct correction to a
gap its author identified in Eric Brewer's CAP theorem.

Daniel Abadi, at the time an assistant professor at Yale and later a professor
at the University of Maryland and a co-founder of Starling database systems,
first wrote the idea down in a blog post on 23 April 2010, "Problems with CAP,
and Yahoo's little known NoSQL system," where he stated the two-part question
directly. "if there is a partition (P) how does the system tradeoff between
availability and consistency (A and C); else (E) when the system is running
as normal in the absence of partitions, how does the system tradeoff between
latency (L) and consistency (C)?"
([dbmsmusings.blogspot.com, "Problems with CAP, and Yahoo's little known NoSQL system,"
23 April 2010](https://dbmsmusings.blogspot.com/2010/04/problems-with-cap-and-yahoos-little.html),
verified 2026-08-02). In that same post he classified two real systems this
way for the first time, calling Amazon Dynamo "PA/EL" and Yahoo's PNUTS
"PC/EL," and he wrote the sentence that is the actual insight behind the whole
principle, not the acronym itself. "systems that tend to give up consistency
for availability when there is a partition also tend to give up consistency
for latency when there is no partition."

Abadi formalized the idea two years later in a peer-reviewed paper, Daniel J.
Abadi, "Consistency Tradeoffs in Modern Distributed Database System Design.
CAP is Only Part of the Story," IEEE Computer, volume 45, issue 2, February
2012, pages 37 to 42, DOI 10.1109/MC.2012.33
([dl.acm.org record for the paper](https://dl.acm.org/doi/10.1109/MC.2012.33),
verified 2026-08-02). That paper is the citation most engineers reach for when
they say "the PACELC paper," in the same way the Gilbert and Lynch 2002 paper
is the one people cite for CAP even though Brewer stated the conjecture first.
The paper's core claim is stated plainly in its abstract. CAP's coupling of
availability and consistency during a network partition captures only part of
the design space that real distributed data stores actually occupy, because
even when no partition is present, a system still has to choose between
minimizing response latency and guaranteeing that every replica agrees before
answering. This entry treats "PACELC" and "the PACELC theorem" as referring to
the same idea, using "theorem" the way the field does, informally, since
unlike CAP proper, no one has published a formal impossibility proof for the
latency and consistency half. It is closer to a design taxonomy with a proven
lower bound behind one half of it, the P half, which inherits CAP's proof, and
an engineering observation behind the other half, the E half, which is a
description of an inescapable local trade-off inside a single node's request
path, not a theorem about a distributed system's worst case.

## 2. Problem and context

A team picks a distributed database, reads that it is "AP" or "CP" under CAP,
and believes that single letter fully describes how the system will behave in
production. It does not. CAP only speaks about what happens during a network
partition, and a well-run data center rarely experiences a hard partition, it
experiences degraded links, congested switches, garbage collection pauses,
and cross-region round trips, none of which trip the formal definition of a
partition but all of which cost milliseconds on every single request the
system serves. A system can be provably CP under CAP, meaning it never
returns a stale answer during a partition, and still be measurably slow on
every read during ordinary Tuesday afternoon traffic because it insists on
confirming with a majority of replicas, some of them across an ocean, before
it answers anything. CAP has nothing to say about that system's everyday
latency, because CAP's scope stops the moment the partition ends.

The context in which this gap actually bites a team is almost always a
region-selection or a consistency-level decision made while reading vendor
marketing rather than a spec. A team building a checkout service reads that
their chosen database is "highly available," the AP label under CAP, assumes
that also means fast, and later discovers that fast reads under that database
require a weaker consistency knob than the one the CAP label implied,
producing carts that occasionally show the wrong item count. Conversely, a
team building an inventory ledger reads that a competing database is
"strongly consistent," the CP label, picks it for correctness, and only in a
performance review discovers that every write now pays a cross-region round
trip because the vendor's default consistency level demands a majority
acknowledgment even when every replica is perfectly reachable. Both teams made
a decision using half a decision framework. PACELC exists to name the missing
half and to force the second question onto the table at design time rather
than at a post-mortem. Given that the system is up and every replica is
reachable right now, what does it actually cost, in milliseconds, to get a
guarantee that the value you read is the latest one written, and is that
price worth paying on this particular code path.

## 3. Forces

The forces PACELC arbitrates split cleanly along its own two clauses,
because the P clause and the E clause are answering genuinely different
questions with genuinely different physics behind them.

Under partition, the P clause, the deciding force is the same one CAP names.
a partition physically prevents some subset of replicas from talking to each
other, so a request that needs an answer from an unreachable replica has
exactly two exits, wait indefinitely, sacrificing availability, or answer
using only the replicas that are reachable, sacrificing the guarantee that
the answer reflects every write. There is no third option, because the
network itself, not a design choice, has removed the ability to ask the
unreachable replica anything at all. This is a binary, forced choice at the
moment of partition. the system either serves a response it cannot fully
vouch for, or it serves an error, or it serves nothing and the client's
request times out, which most engineering teams treat as functionally
identical to unavailability.

The else clause, the E clause, is a genuinely different kind of force, a
continuous trade-off rather than a binary one, and it is the half most
engineers underweight. Even with every replica perfectly reachable, agreement
takes time proportional to the number of participants that must be consulted
and the network distance to the farthest one, per the physical limit that
information cannot travel faster than light and, in practice, does not travel
anywhere near it across a wide-area network. A round trip between two data
centers on opposite coasts of the continental United States has a
speed-of-light floor around 16 milliseconds one way, and real fiber routing
and switching typically pushes observed cross-country round trips into the
60 to 80 millisecond range, a figure that is a matter of physical geometry,
not of any database's implementation quality. This specific reasoning, that
wide-area latency has a physical floor set by the speed of light in fiber and
by routing distance, is standard networking analysis, and the general shape
of the argument is used explicitly by Abadi in the 2012 paper's introduction
when motivating why latency, not just availability, deserves its own axis
alongside consistency
([Abadi 2012, IEEE Computer 45(2), pp. 37 to 42](https://dl.acm.org/doi/10.1109/MC.2012.33),
verified 2026-08-02). Cost, throughput, operational complexity, and
correctness risk trail behind these two headline forces. A system tuned for
EC, consistency in the normal case, pays that cost on every single request
forever, which compounds across a system's whole request volume in a way a
rare partition event does not, because a partition is an occasional tail
event, but "else" is where a system spends the overwhelming majority of its
operational life. This asymmetry, that E happens constantly and P happens
rarely, is itself one of PACELC's most load-bearing observations, and it is
the reason the E trade-off usually deserves more design attention than the P
trade-off even though the P trade-off gets more attention in interviews and
blog posts.

## 4. Applicability and non-applicability

Reach for PACELC as an analysis lens whenever a decision genuinely spans both
of its clauses. choosing a distributed database or a distributed cache for a
system that spans more than one availability zone or region, setting a
per-operation consistency level in a database that exposes a tunable one
such as Cassandra's consistency levels, DynamoDB's eventually-consistent
versus strongly-consistent reads, or MongoDB's read and write concerns,
designing a replication topology for a service you own, deciding whether a
read path can tolerate a stale replica to shave latency off a hot endpoint,
or explaining to a stakeholder why "highly available" does not automatically
mean "fast." PACELC is also the right lens for post-mortem analysis of a
latency incident in a replicated system, because it gives a vocabulary for
separating "this was slow because of a network partition" from "this is
always this slow because of how we configured consistency," which are
different root causes requiring different fixes.

Non-applicability, and this list is longer than most engineers expect.
First, PACELC says nothing useful about a single-node, non-replicated system,
there is no consistency-versus-latency trade-off to analyze when there is
only one copy of the data, because there is nothing for that one copy to
disagree with. Applying PACELC vocabulary to a single Postgres primary with
no read replicas is a category error, not an analysis. Second, it does not
apply to systems whose consistency model is not really about replica
agreement at all, for example a client-side cache invalidation problem, a
CSS specificity conflict, or a merge conflict in version control. those are
consistency problems in the colloquial sense but not in the CAP or PACELC
sense, which is specifically about linearizability or a comparable
strong-consistency guarantee across replicas of the same mutable state.
Third, PACELC is a design taxonomy, not a concurrency-control mechanism, so
it does not tell you how to build a distributed system, it tells you where a
system you have already built, or are evaluating, sits on a spectrum, and it
composes with mechanisms such as quorum consensus, vector clocks, or a
consensus protocol like Raft or Paxos, rather than replacing any of them.
Fourth, it does not apply usefully to systems with a single writer and
asynchronous fan-out to read-only followers where nobody ever reads from a
follower directly, because if all reads are served by the same writer that
did the write, there is no staleness window to trade against latency in the
first place. the trade-off only exists once reads can be served by a replica
that might not yet have the newest write. Fifth, and this is the subtlest
exclusion, PACELC classification is a statement about a system's default or
configured behavior, and it becomes actively misleading when applied to a
system with per-request tunable consistency as if it had one fixed
classification. Cassandra is commonly labeled PA/EL, but a Cassandra cluster
configured to write and read at QUORUM with replication factor three behaves
close to PC/EC on that specific code path, so labeling "Cassandra" as a
monolithic PA/EL system, full stop, without naming the consistency level in
use, misapplies the framework to the product rather than to the configured
deployment.

## 5. Structure

PACELC is not built from runtime participants the way a design pattern is, it
is a decision framework, so its "structure" is the shape of the decision tree
and the roles the pieces of that tree play in an actual system.

- **The partition detector.** The mechanism, usually a heartbeat, gossip
  protocol, or a coordinator's failure detector, that determines whether a
  given replica is currently reachable. This is the trigger that moves a
  request from the E branch into the P branch of the decision tree. it is not
  part of CAP or PACELC's theory, but every real implementation needs one, and
  its accuracy, false positives where a slow but reachable node is
  misclassified as partitioned, and false negatives, the reverse, directly
  determines how often a system pays the P branch's cost when it did not need
  to.
- **The write path and its acknowledgment policy.** The rule that decides how
  many replicas must confirm a write before the client is told the write
  succeeded. This single number is the dial that sets both halves of PACELC at
  once for that operation. a write requiring acknowledgment from every
  reachable replica is slow under normal operation, paying the EC branch's
  latency cost, and becomes unavailable the moment even one required replica
  is unreachable, paying the PC branch's availability cost, while a write
  acknowledged by a single replica is fast under normal operation, the EL
  branch, and stays available under partition because it never needed the
  unreachable replicas in the first place, the PA branch.
- **The read path and its freshness policy.** The symmetric rule for reads.
  how many replicas, and which ones, must be consulted before an answer is
  returned, and whether the coordinator reconciles disagreements among them
  through read repair before answering or simply picks one.
- **The quorum arithmetic, when quorums are used.** The classic mechanism
  binding the write and read policies together is Gifford's quorum condition,
  W plus R greater than N, where N is the replication factor, W is the number
  of replicas that must acknowledge a write, and R is the number that must be
  consulted on a read. when this inequality holds, every read is guaranteed to
  overlap at least one replica that saw the most recent write, giving strong
  consistency at the cost of requiring more replicas to participate in each
  operation, which raises latency on the busier side (David K. Gifford,
  "Weighted Voting for Replicated Data," Proceedings of the Seventh ACM
  Symposium on Operating Systems Principles, 1979, pages 150 to 162, DOI
  10.1145/800215.806583,
  [ACM Digital Library record](https://dl.acm.org/doi/10.1145/800215.806583),
  verified 2026-08-02).
- **The consistency-versus-latency configuration surface.** Whatever knob a
  given system exposes to let an operator or a client, per query, choose a
  point on the PACELC spectrum, such as Cassandra's consistency level
  parameter per statement, DynamoDB's `ConsistentRead` boolean, MongoDB's
  `readConcern` and `writeConcern` documents, or Cosmos DB's five named
  consistency levels. This is where PACELC stops being an abstract theorem
  and becomes a line of application code.

## 6. ASCII structure diagram

```
                        A REQUEST ARRIVES AT A REPLICATED STORE
                                       |
                                       v
                     +----------------------------------------+
                     |   is a network partition in progress    |
                     |   between the coordinator and one or    |
                     |   more replicas it needs to consult?    |
                     +----------------------------------------+
                          |  yes (P)                | no  (E, "else")
                          v                          v
              +----------------------+   +---------------------------+
              |  choose A or C       |   |  choose L or C             |
              |  (CAP's own axis)    |   |  (PACELC's contribution)   |
              +----------------------+   +---------------------------+
                 |               |          |                    |
                 v               v          v                    v
          answer using     wait / error  answer using       wait for W or R
          reachable         until the    the closest /       replicas of a
          replicas only     partition    fastest replica     quorum to agree
          (PA)              heals (PC)   (EL)                (EC)
                 |               |          |                    |
                 v               v          v                    v
          may return         guarantees    may return          guarantees
          a stale value      no stale      a stale value       no stale
          + low latency      value, but    + low latency       value, but
          + stays up         may block     + fast path          higher
                              or fail                            latency

    A system's PACELC classification is the pair of branches it takes.
    PA/EL   (Dynamo-style)         low latency, weak guarantees, both times
    PA/EC   (Cosmos DB Session)    available under partition, strict otherwise
    PC/EL   (PNUTS-style)          strict during partition, fast otherwise
    PC/EC   (VoltDB, H-Store, Spanner)  strict guarantees, both times
```

## 7. Dynamics

The dynamics are best understood as two independent runtime decisions that
happen to be made by the same system, at different moments, using
structurally similar mechanics. Trace a single write followed by a read in a
quorum-based store with replication factor three to see both halves play out.

Normal operation, the E branch. A client sends a write to a coordinator node.
The coordinator forwards the write to all three replicas and waits for
acknowledgments according to the configured write level. If the write level
is ONE, the coordinator returns success to the client the instant the fastest
single replica acknowledges, typically the replica nearest the coordinator,
and the other two replicas apply the write asynchronously in the background.
this is the EL branch, and the client's write latency tracks the single
fastest round trip in the cluster. If the write level is QUORUM, two of
three, or ALL, three of three, the coordinator waits for the second or third
acknowledgment respectively before answering the client, and the client's
write latency now tracks the slower of the required replicas, not the
fastest. this is progressively closer to the EC branch. A subsequent read
against the same key exhibits the identical shape on the read side. reading
at ONE returns whatever the nearest replica has, which might not yet include
the write if that write was itself only acknowledged at ONE and has not
propagated. reading at QUORUM consults two replicas and, if the write was
also done at QUORUM, is mathematically guaranteed to see the most recent
value because the read set and the write set must overlap by at least one
replica, this is Gifford's quorum intersection argument cited in dimension
5. The client experiences this as a single number, the round-trip time of
its request, and never sees the internal branching. only a system that logs
per-replica acknowledgment timing, or a chaos experiment that artificially
delays one replica, makes the underlying mechanic visible.

Partition, the P branch. Now suppose the link between the coordinator's data
center and the data center holding the third replica drops entirely. A write
issued at write level ONE or QUORUM, two of three, satisfiable using the two
reachable replicas, proceeds exactly as before and the client sees no
difference from a normal-operation write. this is the PA branch in action,
availability preserved because the required quorum did not actually need the
partitioned replica. A write issued at write level ALL, or a read issued at a
level that happens to require the unreachable replica specifically, now
blocks. The coordinator either waits, timing out after its configured
deadline and returning an error to the client, a PC system's typical
behavior, sacrificing availability to avoid ever returning a value it cannot
vouch for, or, in a system explicitly designed to degrade gracefully, falls
back to a weaker read from the reachable replicas and marks the response as
potentially stale, a hybrid behavior some systems expose as an explicit
degraded mode, which is itself evidence that a single fixed PACELC label can
be too coarse for a system with configurable fallback behavior. When the
partition heals, the previously unreachable replica must reconcile the writes
it missed, either through anti-entropy repair, hinted handoff, or a
last-writer-wins or vector-clock-based conflict resolution process, and this
reconciliation window is exactly where a PA system's temporary consistency
sacrifice becomes visible to an operator watching replica divergence metrics.

## 8. Implementation variants

The variants are not different pattern shapes so much as different points
along, and different mechanisms for exposing, the same two axes.

**Fixed classification, no runtime knob.** Some systems commit to one point
on the PACELC map and do not expose a way to change it per request. Google
Cloud Spanner is the sharpest example. It is engineered to sit at PC/EC by
combining Paxos-based synchronous replication with TrueTime, a globally
synchronized clock bound using atomic clocks and GPS receivers in every data
center, so that external consistency, a stronger guarantee than plain
linearizability that orders transactions consistently with real-world wall
clock time, holds both during normal operation and, to the extent physically
possible, during a partition ([Corbett et al., "Spanner. Google's
Globally-Distributed Database," Proceedings of OSDI 2012, USENIX,
pages 251 to 264](https://www.usenix.org/system/files/conference/osdi12/osdi12-final-16.pdf),
verified 2026-08-02). VoltDB and its academic predecessor H-Store take a
different route to the same PC/EC corner, using single-threaded partitioned
execution and synchronous command logging rather than a globally synchronized
clock, trading horizontal read scalability for the same strict-both-times
guarantee (Michael Stonebraker, Samuel Madden, Daniel J. Abadi, Stavros
Harizopoulos, Nabil Hachem, Pat Helland, "The End of an Architectural Era
(It's Time for a Complete Rewrite)," Proceedings of the 33rd International
Conference on Very Large Data Bases, VLDB 2007, pages 1150 to 1160,
[VLDB Endowment archive](https://www.vldb.org/conf/2007/papers/industrial/p1150-stonebraker.pdf),
verified 2026-08-02).

**Per-request tunable knob.** Cassandra, Riak, and DynamoDB, via the
`ConsistentRead` parameter, expose the consistency level as a setting the
caller passes on each individual operation, letting one application make
different trade-offs for different code paths against the same cluster. a
shopping cart's "add item" write might use QUORUM for correctness while a
"recently viewed items" read uses ONE for speed, both against the same
DynamoDB table. This is the variant that most directly operationalizes the
PACELC framework, because the classification genuinely changes on a
per-operation basis rather than describing the product as a whole (Amazon
DynamoDB documentation, "Read Consistency,"
[docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadConsistency.html](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadConsistency.html),
verified 2026-08-02, describes eventually consistent reads as roughly half the
latency and cost of strongly consistent reads on the same table).

**Named consistency-level presets.** Rather than exposing raw quorum
arithmetic, some systems name a small set of intermediate points explicitly.
Azure Cosmos DB ships five named levels, Strong, Bounded Staleness, Session,
Consistent Prefix, and Eventual, each documented with a specific latency and
availability trade-off, with Session, read-your-own-writes for the writing
client and weaker for everyone else, as the default because Microsoft's own
engineering documentation states it is the level most applications actually
need (Microsoft, "Consistency levels in Azure Cosmos DB,"
[learn.microsoft.com/en-us/azure/cosmos-db/consistency-levels](https://learn.microsoft.com/en-us/azure/cosmos-db/consistency-levels),
verified 2026-08-02). This is effectively PACELC classification exposed as a
first-class product feature with a name attached to each point on the
spectrum, rather than a raw W and R quorum count the caller must reason about
themselves.

**Asynchronous primary-replica with explicit staleness bound.** Yahoo's
PNUTS, and its architectural descendants, choose per-record mastership,
routing every write for a given record to a single designated master replica,
giving strict ordering and a single source of truth for that record, the PC
half, while allowing asynchronous, best-effort propagation to other regions'
replicas that primarily serve local reads at low latency, the EL half. Brian
F. Cooper et al., "PNUTS. Yahoo!'s Hosted Data Serving Platform," Proceedings
of the VLDB Endowment, volume 1, issue 2, 2008, pages 1277 to 1288, DOI
10.14778/1454159.1454167 ([VLDB Endowment
paper](https://www.vldb.org/pvldb/1/1454167.pdf), verified 2026-08-02),
is the paper Abadi's own original blog post used as the PC/EL example that
motivated PACELC in the first place, precisely because PNUTS's asymmetric
behavior, strict during a partition and deliberately loose otherwise, was the
kind of system CAP's single letter grade could not describe.

## 9. Known production uses

Apache Cassandra ships with a documented, tunable consistency level per
statement, ONE, QUORUM, LOCAL_QUORUM, ALL, and others, and its own
documentation explicitly frames the choice as a consistency-versus-latency
trade-off the operator makes per query, defaulting most production
deployments toward ONE or LOCAL_QUORUM for latency-sensitive workloads
(Apache Cassandra documentation, "Consistency,"
[cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html](https://cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html),
verified 2026-08-02). This is the textbook PA/EL system in most default
configurations, and the textbook example used across the PACELC literature.

Amazon DynamoDB defaults every read to eventually consistent unless the
caller explicitly sets `ConsistentRead: true`, and its own developer guide
states that eventually consistent reads offer both lower latency and lower
cost than strongly consistent reads on the same table, which is PACELC's E
clause described in AWS's own words rather than an outside label
([docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadConsistency.html](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadConsistency.html),
verified 2026-08-02).

Google Cloud Spanner is documented by Google's own OSDI 2012 paper as
providing external consistency using TrueTime-bounded synchronous Paxos
replication, explicitly accepting the latency cost of a commit wait,
observed as single-digit to double-digit milliseconds of induced delay per
commit in the paper's own reported measurements, in exchange for strict
guarantees under normal operation and, to the degree a partition's minority
side permits, during a partition as well
([usenix.org/system/files/conference/osdi12/osdi12-final-16.pdf](https://www.usenix.org/system/files/conference/osdi12/osdi12-final-16.pdf),
verified 2026-08-02), which is the canonical production PC/EC example cited
across the distributed systems literature that followed the PACELC paper.

MongoDB, in its default replica-set configuration with `w:1` write concern
and reads directed at the primary, is documented by MongoDB's own manual as
capable of losing acknowledged writes if the primary fails before
replicating them to secondaries, which is availability-favoring behavior
during a failure. the same manual documents that setting `w:"majority"`
write concern together with `readConcern:"majority"` moves the same product
toward the PC/EC corner at the cost of added write latency, making MongoDB a
clear example of a single product occupying different PACELC classifications
depending entirely on its configured write and read concern (MongoDB, Inc.,
"Read Concern," and "Write Concern,"
[www.mongodb.com/docs/manual/reference/read-concern/](https://www.mongodb.com/docs/manual/reference/read-concern/) and
[www.mongodb.com/docs/manual/reference/write-concern/](https://www.mongodb.com/docs/manual/reference/write-concern/),
both verified 2026-08-02).

## 10. Consequences

Positive. PACELC gives teams a vocabulary that separates two genuinely
different engineering problems that a single CAP letter had been collapsing
into one, which directly improves the quality of both database-selection
decisions and post-mortem root-cause analysis. an incident report that says
"we were PA/EL, so a stale cache read reached the customer during elevated
load" is diagnostically sharper than one that says "the database was
eventually consistent," because it names which half of the trade-off, the
partition half or the everyday half, actually produced the customer-visible
symptom. It also surfaces a design decision, the everyday latency versus
consistency trade-off, that is easy to leave implicit and therefore easy to
get wrong by accident, since most engineers reason carefully about partition
behavior, because outages are memorable, but reason far less carefully about
the steady-state cost of a strong consistency default, because it is a
constant, invisible tax rather than a dramatic event. Naming the E axis
turns that invisible tax into a line item a team can decide to pay or not.
It also composes cleanly with existing distributed-systems vocabulary rather
than replacing it, since PACELC classification is typically expressed
alongside, not instead of, the underlying mechanism, quorum size,
replication factor, consensus protocol, giving a two-level description, the
mechanism and the resulting classification, that a team can reason about at
either altitude depending on the conversation.

Negative. The classification itself is coarse, a four-cell grid trying to
summarize a continuous, often per-operation, configuration space, and
treating a system's PACELC label as a fixed, permanent property rather than a
function of its current configuration is a real and common misuse, visible
in the number of blog posts that state flatly "MongoDB is PA" or "Cassandra
is PA/EL" as an unqualified fact about the product rather than about a
specific deployment's write and read concern settings. The framework also has
no formal proof behind its E half the way CAP's P half has Gilbert and
Lynch's proof. it is best understood as a well-evidenced engineering
observation and a useful taxonomy rather than a mathematical theorem with the
same epistemic weight as CAP, and presenting it to a team as "proven" the way
CAP is proven overstates its rigor. It also, by design, ignores every force
outside its two named axes. a system can be a textbook PA/EL system and still
be the wrong choice for a workload because of its operational cost, its
query model, its consistency-per-key granularity, or its ecosystem maturity,
none of which the PACELC grid has any vocabulary for, so treating the
four-cell classification as a complete decision criterion, rather than one
input among several, is its most common downstream misuse.

## 11. Failure modes and misuse

**Symptom.** A team selects a database because a comparison chart lists it as
"CP" or "highly consistent," ships it, and later gets paged for latency
regressions on a hot read path with no partition anywhere in the incident
timeline.
**Cause.** The team read only the P half of the system's behavior and never
asked what its default write and read concern cost during ordinary,
fully-connected operation. the system was in fact behaving exactly as
designed, paying its EC latency tax on every single request, and the
regression is not a bug, it is the documented steady-state cost of the
consistency guarantee the team selected.
**Fix.** Re-derive the system's actual PACELC classification from its
configured write and read concern, not from a marketing label, identify
which specific code paths genuinely require the strong guarantee, and move
the remaining, latency-sensitive paths to a weaker consistency level for
that specific operation where the business logic tolerates staleness,
verified against the quorum arithmetic in dimension 5 rather than against
intuition.

**Symptom.** During a real network partition, a service that the team
believed was "always available" starts returning errors or timing out on
writes, contradicting its assumed classification.
**Cause.** The write path in question was configured with a write concern
requiring more replicas than the reachable side of the partition can supply,
for example `w:"majority"` against a replica set where the majority now sits
on the other side of the split, silently making that write path PC even
though a different write path in the same application, using default write
concern, remains PA. the team classified the whole product rather than the
specific operation.
**Fix.** Audit every write and read path individually for its configured
consistency level rather than assuming a single classification applies
cluster-wide, and, where availability genuinely matters more than strict
ordering for that specific operation, deliberately relax the concern level
and add downstream reconciliation, idempotent writes, conflict-free
replicated data types, or an explicit last-writer-wins policy, to handle the
resulting divergence once the partition heals.

**Symptom.** A replicated cache or read-replica fleet occasionally serves
data that is a few seconds, or in bad cases minutes, out of date, and nobody
can explain why, because "the system is eventually consistent, so this is
expected" has become the reflexive, unexamined answer to every staleness
report.
**Cause.** "Eventually consistent" describes only that convergence will
happen, not how long it will take, and the actual staleness window is a
function of replication lag, which itself is a function of the write path's
acknowledgment level, the EL side of the system's configuration, combined
with real network conditions. treating "eventually consistent" as a
sufficient explanation, rather than measuring the actual replication lag
distribution, hides a genuine and often fixable operational problem, an
overloaded replica, a slow cross-region link, a backpressure bug, behind a
theoretical label.
**Fix.** Instrument and alert on actual replication lag as a first-class
metric, not as an assumed-negligible implementation detail, and treat a
growing lag distribution as an operational incident in its own right, because
the PACELC framework describes the trade-off's existence, not its magnitude,
and the magnitude is precisely what production monitoring exists to reveal.

## 12. Trade-off matrix

| Force | PA/EL, e.g. Cassandra default, Dynamo | PA/EC, e.g. Cosmos DB Session | PC/EL, e.g. PNUTS | PC/EC, e.g. Spanner, VoltDB |
|---|---|---|---|---|
| Steady-state read/write latency | Lowest, single nearest-replica round trip | Low to moderate, session-bound guarantee adds some coordination | Low for the per-record master's own region, higher for followers reading cross-region | Highest, every operation pays quorum or global-clock coordination cost |
| Availability during a hard partition | Highest, minority side keeps serving | High, but session guarantees can degrade or block on the minority side | Lower, writes for a record block if that record's master is unreachable | Lowest, the system will refuse a majority-quorum operation on the minority side |
| Read-your-own-writes guarantee | Not guaranteed by default | Guaranteed within one client session | Guaranteed if reads route to the record's master | Guaranteed globally |
| Cross-replica staleness window | Unbounded in principle, bounded in practice by replication lag | Bounded per client session, not globally | Near zero for master-region reads, variable for follower reads | Effectively zero, external consistency holds |
| Operational complexity to run correctly | Lower, tolerant of a slow or unreachable node | Moderate, session token routing adds a moving part | Moderate, per-record mastership needs routing logic | Highest, needs tightly bounded clock synchronization or single-threaded partitioning discipline |
| Best-fit workload | Caches, session state, high-volume telemetry, shopping-cart-style data tolerant of brief staleness | Collaborative apps where a user must see their own edits immediately, but global ordering is less critical | Workloads with a natural per-record home region and mostly local access | Financial ledgers, inventory counts, anything where two clients disagreeing about the current value is a correctness bug, not a UX nuisance |

## 13. Related and incompatible patterns

PACELC extends the CAP theorem and shares its P clause verbatim, so
`cap-theorem` is the direct parent this entry composes with rather than
duplicates. read CAP first for the formal partition-time proof, and read this
entry for the everyday-operation half CAP is silent about. Quorum consensus,
the W plus R greater than N arithmetic from Gifford's 1979 paper cited in
dimension 5, is the mechanism most systems actually use to implement a chosen
PACELC point, so `quorum-consensus` is the "how" to this entry's "which point
on the map." Eventual consistency is the specific consistency model that sits
at the EL end of the else axis, describing what a system guarantees once it
has chosen to favor latency, and `eventual-consistency` is the pattern that
names the reconciliation mechanics, read repair, anti-entropy, vector clocks,
last-writer-wins, a PA/EL or PA/EC system needs once it has accepted that
replicas will temporarily disagree. The saga pattern for distributed
transactions is a complementary technique for systems that have deliberately
chosen the availability-and-latency side of PACELC and therefore cannot rely
on a single atomic cross-replica or cross-service commit, so `saga` is the
application-level answer to "given that I chose PA/EL, how do I still get
correct multi-step business outcomes." A circuit breaker and a bulkhead,
`circuit-breaker` and `bulkhead`, are the operational mechanisms that decide
what a caller does when the underlying store's chosen PACELC point produces a
slow or failing response, converting a PACELC-driven latency spike into a
contained, isolated failure rather than a cascading one. they operate one
layer above PACELC, at the calling service's boundary, rather than inside the
data store itself. There is no pattern this entry is incompatible with in the
strict sense, because PACELC is a taxonomy applied to a system's behavior
rather than a mechanism competing with other mechanisms for the same slot in
an architecture. the closest thing to an incompatibility is applying PACELC
vocabulary to a non-replicated system, covered in dimension 4's
non-applicability list.

## 14. Refactoring path in and out

Introducing PACELC-aware thinking into a codebase that currently treats its
data store as a monolithic black box starts with an audit, not a code change.
First, enumerate every distinct read and write path against the replicated
store and, for each one, record its actual configured consistency level,
write concern, read concern, consistency level parameter, or the vendor's
documented default if none is set explicitly, because most codebases have
never done this and the true answer is frequently a surprise even to the team
that wrote the code. Second, for each path, ask the business-logic question
PACELC exists to force onto the table. if this specific read returned a value
that is a few hundred milliseconds stale, does anything downstream actually
break, or does it only look slightly wrong to a human who would not notice
anyway. Paths where staleness is genuinely harmless, a "last seen online"
timestamp, a view counter, a recommendation feed, are refactoring candidates
to move toward the EL end of the spectrum, trading a now-unnecessary
consistency guarantee for latency the business will actually feel. Third, for
paths where staleness is a correctness bug, an account balance, an inventory
count that gates a purchase, a unique-username check, verify the configured
consistency level actually delivers the guarantee assumed, rather than
inheriting a store-wide default that may have been tuned for a different,
unrelated path elsewhere in the same codebase. Fourth, add the replication
lag and per-path consistency level as an explicit, tested, and monitored
property of the system, per dimension 15 and 16 below, so the classification
stops being folklore and starts being a verifiable fact the team can point
to.

Refactoring PACELC-driven consistency choices back out, meaning simplifying
away a tuned, per-path consistency scheme once it stops earning its
complexity, is the mirror image. identify paths where a team paid the EC
latency cost historically but the underlying business requirement has
loosened, a feature was deprecated, a compliance requirement changed, traffic
patterns shifted so the hot path is no longer the one that needed strong
consistency, and collapse those paths back to the store's simpler default
consistency level, removing the special-cased per-query override and the
extra test coverage it required. This direction is refactoring out complexity
that outlived its justification, and it composes with the general discipline
of removing dead configuration once its business justification is gone, and
with the broader principle that a per-operation override is a piece of state
that must be actively maintained or it silently rots into either an
unnecessary latency tax nobody remembers the reason for, or a consistency gap
nobody remembers signing up for.

## 15. Testing and verification

This dimension is mostly engineering judgement about practice, stated
plainly here per the template's judgement-versus-sourced-claim guidance.

Testing a system's actual PACELC behavior requires fault injection, because
unit tests against a healthy, fully-connected cluster will never exercise the
P branch of the decision tree at all, and will exercise the E branch's
latency characteristics only if the test rig measures wall-clock timing
rather than merely asserting correctness. A practical test suite for a
consistency-sensitive code path has three layers. First, a correctness test
against a healthy cluster asserting that a read immediately following a
write, at the configured consistency levels, returns the value just written,
this is the test that catches an accidentally-too-weak consistency level
configured for a path that actually needs strong guarantees. Second, a
partition-injection test, using a network fault injection tool, Jepsen is
the standard tool in this space for exactly this kind of testing,
deliberately partitioning a real cluster under a real workload and checking
for consistency violations against a formal linearizability or
causal-consistency checker, or a test double that simulates unreachable
replicas at the client library level, asserting that the system's behavior
during the simulated partition matches its documented or intended
classification, meaning a PA-classified path should keep serving during the
simulated partition and a PC-classified path should correctly refuse or
degrade rather than silently serving a stale value it claims not to. Third,
a latency-budget test under normal, fully-connected conditions, because a
regression in the E branch, a consistency level accidentally tightened by a
config change, or a new cross-region replica added to a quorum, is exactly
the kind of change that passes every correctness test while silently
doubling steady-state latency on a hot path, and only an explicit latency
assertion in the test suite, or a latency budget enforced in a load test,
will catch it before it reaches production. What becomes genuinely easier to
test because of an explicit PACELC-aware design is the negative case,
verifying that a specific path degrades gracefully rather than hanging or
erroring opaquely when a quorum cannot be met. what becomes harder is
achieving deterministic, repeatable tests at all, since partition and
latency behavior are inherently timing-sensitive and non-deterministic
without a controlled fault-injection rig, which is why ad hoc "turn off
a Docker container and see what happens" testing consistently under-tests
this area compared to a proper tool built for the purpose.

## 16. Observability signals

Judgement note. the specific metrics named below are standard operational
practice in the distributed-systems and site-reliability field rather than
claims traceable to a single citable source, and are presented as such.

A healthy PA/EL-style deployment shows a tight, low, and stable latency
distribution on both reads and writes, a replication lag metric, the time
delta between a write landing on the fastest-acknowledging replica and
landing on the slowest one, that stays within a known, alerted-on bound
rather than growing unboundedly, and a low but non-zero rate of read-repair
or reconciliation events, which is evidence the eventual-consistency
mechanism is actually functioning rather than silently failing to converge
at all. A dashboard for this kind of system typically surfaces p50, p95, and
p99 latency per consistency level in use, since a single store often serves
multiple consistency levels concurrently across different code paths, and
averaging them together hides which path is actually degrading, plus a
staleness histogram if the store or client library can report the age of the
data a read actually returned relative to the last known write for that key.

A healthy PC/EC-style deployment shows the inverse profile. a higher but
tightly bounded and predictable latency floor, since the cost is paid on
every operation by design, a healthy system's latency should look like a
consistent, expected constant rather than an occasional spike, essentially
zero replication lag because writes are not considered complete until they
are already replicated, and, critically, a clear, alertable signal the
moment a quorum or a global-clock guarantee cannot be met, since a PC
system's correct behavior under stress is to refuse rather than degrade
silently, and an operator needs to see that refusal rate rise, an
availability metric trending down, as clearly as a latency metric trending
up. For a system using a physical-clock-based approach like Spanner's
TrueTime, the clock uncertainty bound itself, the interval width the system
reports for "now," is a first-class signal worth graphing, because a
widening uncertainty bound, from a degraded GPS or atomic clock reference,
directly translates into rising commit latency even with no other change in
the system.

Across both profiles, the single most valuable cross-cutting signal is a
per-operation label recording which consistency level was actually used for
that specific request, correlated against its latency and its correctness
outcome where verifiable, because without that label a dashboard can only
show an aggregate that blends fast, weak-guarantee reads together with slow,
strong-guarantee reads into one misleading average that accurately describes
neither.

## 17. Security and privacy implications

This dimension is genuinely mostly analytical judgement rather than a
citable finding, stated here plainly per the template's guidance, because
PACELC is a consistency-and-latency framework and its security surface is
indirect, arising from what a chosen consistency level does or does not
guarantee about the freshness of security-relevant data, not from the
framework itself carrying a direct vulnerability.

A system tuned toward PA/EL for a code path that gates an authorization
decision creates a real, concrete window of risk. if a permission revocation,
removing a user's access, disabling a compromised API key, banning an
account, is written with a weak write concern and read back with a weak read
concern on the authorization check itself, a revoked credential can remain
functionally valid for however long the replication lag window happens to
be, which converts an abstract eventual-consistency trade-off into a
concrete time-bounded privilege-retention vulnerability. this is precisely
the kind of code path dimension 14's audit step is meant to flag as
requiring the stronger, EC end of the spectrum regardless of what
consistency level the rest of the system defaults to. Rate limiting and
quota enforcement have a milder version of the same issue, where a PA/EL-
tuned counter can permit brief overshoot past a configured limit during the
staleness window, which is usually an acceptable business trade-off but is
worth stating explicitly rather than discovering during an abuse incident.
On the data-handling side, a PC/EC system's insistence on strong, globally
ordered guarantees, and especially a physical-clock-based implementation
like TrueTime, introduces its own operational dependency, on a trustworthy
and tamper-resistant time source, as a security-adjacent concern in its own
right, since an attacker capable of skewing a node's clock in a system that
leans on wall-clock time for ordering could, in principle, undermine the
very guarantee the architecture exists to provide. production systems in
this category mitigate this with hardware-backed, redundant time sources and
bounded uncertainty windows precisely because the ordering guarantee's
integrity depends on it. PACELC's E axis has no privacy implication of its
own beyond this general observation that staleness windows are,
functionally, a bounded time gap during which a system may act on
out-of-date authorization or entitlement state, and any code path handling
personally identifiable information under a data-subject deletion or
correction request, a GDPR-style erasure request being the clearest example,
should be audited the same way an authorization path is, since a PA/EL-
configured delete can leave a replica serving the supposedly-deleted data for
the length of the replication lag window.

## Code examples

The examples below implement the same tunable, quorum-based key-value store
in three languages, one that lets a caller choose ONE, QUORUM, or ALL as its
write and read level, mirroring the real knob Cassandra, Riak, and DynamoDB
expose. The demo function runs the same store first at ALL and QUORUM,
PC/EC-leaning behavior, and then at ONE and ONE, PA/EL-leaning behavior, and
finally shows what each configuration does when two of the three replicas
become unreachable, simulating a partition. All three were run against a
local toolchain during authoring, `python3 -m py_compile`, `go vet` plus
`go run`, and `tsc --strict --noEmit` plus `node`, and each produced the
expected output, PC/EC blocking the write during the simulated partition and
PA/EL accepting it.

### TypeScript

```typescript
type Level = "ONE" | "QUORUM" | "ALL";

interface Replica {
  name: string;
  latencyMs: number;
  reachable: boolean;
  value: number;
  version: number;
}

class TunableStore {
  constructor(
    private replicas: Replica[],
    private writeLevel: Level,
    private readLevel: Level
  ) {}

  private quorumSize(level: Level): number {
    const n = this.replicas.length;
    if (level === "ONE") return 1;
    if (level === "ALL") return n;
    return Math.floor(n / 2) + 1;
  }

  write(value: number): { ok: boolean; latencyMs: number } {
    const need = this.quorumSize(this.writeLevel);
    const version = Math.max(0, ...this.replicas.map((r) => r.version)) + 1;
    const ordered = [...this.replicas].sort((a, b) => a.latencyMs - b.latencyMs);
    let acked = 0;
    let elapsed = 0;
    for (const r of ordered) {
      if (!r.reachable) continue;
      r.value = value;
      r.version = version;
      elapsed = Math.max(elapsed, r.latencyMs);
      acked += 1;
      if (acked >= need) return { ok: true, latencyMs: elapsed };
    }
    return { ok: false, latencyMs: elapsed };
  }

  read(): { value: number | null; latencyMs: number; stale: boolean } {
    const need = this.quorumSize(this.readLevel);
    const ordered = [...this.replicas].sort((a, b) => a.latencyMs - b.latencyMs);
    const seen: Replica[] = [];
    let elapsed = 0;
    for (const r of ordered) {
      if (!r.reachable) continue;
      seen.push(r);
      elapsed = Math.max(elapsed, r.latencyMs);
      if (seen.length >= need) break;
    }
    if (seen.length < need) return { value: null, latencyMs: elapsed, stale: false };
    const latest = seen.reduce((a, b) => (b.version > a.version ? b : a));
    const stale = seen.some((r) => r.version !== latest.version);
    return { value: latest.value, latencyMs: elapsed, stale };
  }
}

function demo(): void {
  const replicas: Replica[] = [
    { name: "east", latencyMs: 5, reachable: true, value: 0, version: 0 },
    { name: "west", latencyMs: 60, reachable: true, value: 0, version: 0 },
    { name: "eu", latencyMs: 110, reachable: true, value: 0, version: 0 },
  ];

  const pcec = new TunableStore(replicas, "ALL", "QUORUM");
  const w1 = pcec.write(42);
  const r1 = pcec.read();
  console.log(`PC/EC write ok=${w1.ok} latency=${w1.latencyMs}ms read value=${r1.value} stale=${r1.stale}`);

  for (const r of replicas) r.version = 0;
  const pael = new TunableStore(replicas, "ONE", "ONE");
  const w2 = pael.write(42);
  const r2 = pael.read();
  console.log(`PA/EL write ok=${w2.ok} latency=${w2.latencyMs}ms read value=${r2.value} stale=${r2.stale}`);

  replicas[1].reachable = false;
  replicas[2].reachable = false;
  console.log(`During partition, PC/EC write ok=${pcec.write(99).ok}`);
  console.log(`During partition, PA/EL write ok=${pael.write(99).ok}`);
}

demo();
```

### Python

```python
from dataclasses import dataclass
from enum import Enum


class Level(Enum):
    ONE = 1
    QUORUM = 2
    ALL = 3


@dataclass
class Replica:
    name: str
    latency_ms: float
    reachable: bool = True
    value: int = 0
    version: int = 0


@dataclass
class TunableStore:
    replicas: list
    write_level: Level
    read_level: Level

    def _quorum_size(self, level: Level) -> int:
        n = len(self.replicas)
        if level is Level.ONE:
            return 1
        if level is Level.ALL:
            return n
        return n // 2 + 1

    def write(self, value: int) -> tuple[bool, float]:
        need = self._quorum_size(self.write_level)
        acked, elapsed = 0, 0.0
        version = max((r.version for r in self.replicas), default=0) + 1
        ordered = sorted(self.replicas, key=lambda r: r.latency_ms)
        for r in ordered:
            if not r.reachable:
                continue
            r.value, r.version = value, version
            elapsed = max(elapsed, r.latency_ms)
            acked += 1
            if acked >= need:
                return True, elapsed
        return False, elapsed

    def read(self) -> tuple[int | None, float, bool]:
        need = self._quorum_size(self.read_level)
        ordered = sorted(self.replicas, key=lambda r: r.latency_ms)
        seen, elapsed = [], 0.0
        for r in ordered:
            if not r.reachable:
                continue
            seen.append(r)
            elapsed = max(elapsed, r.latency_ms)
            if len(seen) >= need:
                break
        if len(seen) < need:
            return None, elapsed, False
        latest = max(seen, key=lambda r: r.version)
        stale = any(r.version != latest.version for r in seen)
        return latest.value, elapsed, stale


def demo() -> None:
    replicas = [
        Replica("east", latency_ms=5),
        Replica("west", latency_ms=60),
        Replica("eu", latency_ms=110),
    ]

    pc_ec = TunableStore(replicas, Level.ALL, Level.QUORUM)
    ok, ms = pc_ec.write(42)
    val, read_ms, stale = pc_ec.read()
    print(f"PC/EC write ok={ok} latency={ms}ms  read val={val} latency={read_ms}ms stale={stale}")

    for r in replicas:
        r.version = 0
    pa_el = TunableStore(replicas, Level.ONE, Level.ONE)
    ok, ms = pa_el.write(42)
    val, read_ms, stale = pa_el.read()
    print(f"PA/EL write ok={ok} latency={ms}ms  read val={val} latency={read_ms}ms stale={stale}")

    replicas[1].reachable = False
    replicas[2].reachable = False
    ok, ms = pc_ec.write(99)
    print(f"During partition, PC/EC write ok={ok} (availability sacrificed)")
    ok, ms = pa_el.write(99)
    print(f"During partition, PA/EL write ok={ok} (consistency at risk, availability kept)")


if __name__ == "__main__":
    demo()
```

### Go

```go
package main

import (
	"fmt"
	"sort"
)

type ConsistencyLevel int

const (
	LevelOne ConsistencyLevel = iota
	LevelQuorum
	LevelAll
)

type Replica struct {
	Name      string
	LatencyMS int
	Reachable bool
	Value     int
	Version   int
}

type TunableStore struct {
	Replicas   []*Replica
	WriteLevel ConsistencyLevel
	ReadLevel  ConsistencyLevel
}

func quorumSize(n int, level ConsistencyLevel) int {
	switch level {
	case LevelOne:
		return 1
	case LevelAll:
		return n
	default:
		return n/2 + 1
	}
}

func (s *TunableStore) Write(value int) (bool, int) {
	need := quorumSize(len(s.Replicas), s.WriteLevel)
	version := 0
	for _, r := range s.Replicas {
		if r.Version > version {
			version = r.Version
		}
	}
	version++
	ordered := append([]*Replica(nil), s.Replicas...)
	sort.Slice(ordered, func(i, j int) bool { return ordered[i].LatencyMS < ordered[j].LatencyMS })
	acked, elapsed := 0, 0
	for _, r := range ordered {
		if !r.Reachable {
			continue
		}
		r.Value, r.Version = value, version
		if r.LatencyMS > elapsed {
			elapsed = r.LatencyMS
		}
		acked++
		if acked >= need {
			return true, elapsed
		}
	}
	return false, elapsed
}

func (s *TunableStore) Read() (int, int, bool, bool) {
	need := quorumSize(len(s.Replicas), s.ReadLevel)
	ordered := append([]*Replica(nil), s.Replicas...)
	sort.Slice(ordered, func(i, j int) bool { return ordered[i].LatencyMS < ordered[j].LatencyMS })
	var seen []*Replica
	elapsed := 0
	for _, r := range ordered {
		if !r.Reachable {
			continue
		}
		seen = append(seen, r)
		if r.LatencyMS > elapsed {
			elapsed = r.LatencyMS
		}
		if len(seen) >= need {
			break
		}
	}
	if len(seen) < need {
		return 0, elapsed, false, false
	}
	latest := seen[0]
	for _, r := range seen {
		if r.Version > latest.Version {
			latest = r
		}
	}
	stale := false
	for _, r := range seen {
		if r.Version != latest.Version {
			stale = true
		}
	}
	return latest.Value, elapsed, true, stale
}

func main() {
	replicas := []*Replica{
		{Name: "east", LatencyMS: 5, Reachable: true},
		{Name: "west", LatencyMS: 60, Reachable: true},
		{Name: "eu", LatencyMS: 110, Reachable: true},
	}

	pcec := &TunableStore{Replicas: replicas, WriteLevel: LevelAll, ReadLevel: LevelQuorum}
	ok, ms := pcec.Write(42)
	val, rms, hit, stale := pcec.Read()
	fmt.Printf("PC/EC write ok=%v latency=%dms  read val=%d latency=%dms hit=%v stale=%v\n", ok, ms, val, rms, hit, stale)

	for _, r := range replicas {
		r.Version = 0
	}
	pael := &TunableStore{Replicas: replicas, WriteLevel: LevelOne, ReadLevel: LevelOne}
	ok, ms = pael.Write(42)
	val, rms, hit, stale = pael.Read()
	fmt.Printf("PA/EL write ok=%v latency=%dms  read val=%d latency=%dms hit=%v stale=%v\n", ok, ms, val, rms, hit, stale)

	replicas[1].Reachable = false
	replicas[2].Reachable = false
	ok, _ = pcec.Write(99)
	fmt.Printf("During partition, PC/EC write ok=%v (availability sacrificed)\n", ok)
	ok, _ = pael.Write(99)
	fmt.Printf("During partition, PA/EL write ok=%v (consistency at risk, availability kept)\n", ok)
}
```

## 18. References

- Daniel Abadi, "Problems with CAP, and Yahoo's little known NoSQL system,"
  DBMS Musings blog, 23 April 2010,
  [dbmsmusings.blogspot.com/2010/04/problems-with-cap-and-yahoos-little.html](https://dbmsmusings.blogspot.com/2010/04/problems-with-cap-and-yahoos-little.html),
  verified 2026-08-02. The original coinage of PACELC.
- Daniel J. Abadi, "Consistency Tradeoffs in Modern Distributed Database
  System Design. CAP is Only Part of the Story," IEEE Computer, volume 45,
  issue 2, 2012, pages 37 to 42, DOI 10.1109/MC.2012.33,
  [dl.acm.org/doi/10.1109/MC.2012.33](https://dl.acm.org/doi/10.1109/MC.2012.33),
  verified 2026-08-02. The formal, peer-reviewed statement of PACELC.
- Seth Gilbert and Nancy Lynch, "Brewer's Conjecture and the Feasibility of
  Consistent, Available, Partition-Tolerant Web Services," ACM SIGACT News,
  volume 33, issue 2, 2002, pages 51 to 59, DOI 10.1145/564585.564601,
  [dl.acm.org/doi/10.1145/564585.564601](https://dl.acm.org/doi/10.1145/564585.564601),
  verified 2026-08-02. The formal proof underlying PACELC's P clause.
- David K. Gifford, "Weighted Voting for Replicated Data," Proceedings of the
  Seventh ACM Symposium on Operating Systems Principles, SOSP 1979, pages 150
  to 162, DOI 10.1145/800215.806583,
  [dl.acm.org/doi/10.1145/800215.806583](https://dl.acm.org/doi/10.1145/800215.806583),
  verified 2026-08-02. The quorum-intersection arithmetic, W plus R greater
  than N, most tunable PACELC implementations use.
- James C. Corbett et al., "Spanner. Google's Globally-Distributed Database,"
  Proceedings of the 10th USENIX Symposium on Operating Systems Design and
  Implementation, OSDI 2012, pages 251 to 264,
  [usenix.org/system/files/conference/osdi12/osdi12-final-16.pdf](https://www.usenix.org/system/files/conference/osdi12/osdi12-final-16.pdf),
  verified 2026-08-02. The canonical production PC/EC system using
  TrueTime-bounded synchronous replication.
- Michael Stonebraker, Samuel Madden, Daniel J. Abadi, Stavros Harizopoulos,
  Nabil Hachem, Pat Helland, "The End of an Architectural Era (It's Time for
  a Complete Rewrite)," Proceedings of the 33rd International Conference on
  Very Large Data Bases, VLDB 2007, pages 1150 to 1160,
  [vldb.org/conf/2007/papers/industrial/p1150-stonebraker.pdf](https://www.vldb.org/conf/2007/papers/industrial/p1150-stonebraker.pdf),
  verified 2026-08-02. The H-Store architecture behind VoltDB's PC/EC design.
- Brian F. Cooper et al., "PNUTS. Yahoo!'s Hosted Data Serving Platform,"
  Proceedings of the VLDB Endowment, volume 1, issue 2, 2008, pages 1277 to
  1288, DOI 10.14778/1454159.1454167,
  [vldb.org/pvldb/1/1454167.pdf](https://www.vldb.org/pvldb/1/1454167.pdf),
  verified 2026-08-02. The PC/EL system Abadi used as a founding PACELC
  example.
- Apache Cassandra documentation, "Consistency,"
  [cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html](https://cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html),
  verified 2026-08-02. The tunable per-statement consistency level system.
- Amazon Web Services, "Read Consistency," Amazon DynamoDB Developer Guide,
  [docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadConsistency.html](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadConsistency.html),
  verified 2026-08-02. DynamoDB's eventually-consistent-by-default read
  behavior and its documented latency and cost trade-off.
- MongoDB, Inc., "Read Concern," MongoDB Manual,
  [www.mongodb.com/docs/manual/reference/read-concern/](https://www.mongodb.com/docs/manual/reference/read-concern/),
  verified 2026-08-02, and "Write Concern," MongoDB Manual,
  [www.mongodb.com/docs/manual/reference/write-concern/](https://www.mongodb.com/docs/manual/reference/write-concern/),
  verified 2026-08-02. MongoDB's configurable read and write concern, which
  moves the same product between PA/EC-leaning and PC/EC-leaning behavior.
- Microsoft, "Consistency levels in Azure Cosmos DB," Microsoft Learn,
  [learn.microsoft.com/en-us/azure/cosmos-db/consistency-levels](https://learn.microsoft.com/en-us/azure/cosmos-db/consistency-levels),
  verified 2026-08-02. The five named consistency levels as an explicit
  product-level exposure of the PACELC spectrum.
