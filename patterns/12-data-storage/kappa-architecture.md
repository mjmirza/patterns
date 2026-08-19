---
name: Kappa Architecture
slug: kappa-architecture
family: 12-data-storage
category: Data and Storage
aliases: [Streaming-Only Architecture, Unified Log Architecture, Single-Path Streaming]
first_described: "Jay Kreps, Questioning the Lambda Architecture, O'Reilly Radar, 2 July 2014"
maturity: established
related: [event-sourcing, cqrs, lambda-architecture, log-compaction, materialized-view, saga-orchestration]
incompatible_with: [two-tier-batch-speed-layer]
verified: 2026-08-02
---

# Kappa Architecture

## 1. Name, aliases, and lineage

Kappa Architecture is the name Jay Kreps gave, half-jokingly, to a data
processing style built around a single stream processing path instead of the
two parallel paths of Lambda Architecture. Kreps introduced the term in an
O'Reilly Radar article published 2 July 2014 titled "Questioning the Lambda
Architecture," writing that the idea "may be too simple of an idea to merit a
Greek letter," a line that stuck as the pattern's origin story (Kreps, J.,
"Questioning the Lambda Architecture," O'Reilly Radar, 2 July 2014, verified
2026-08-02). Kreps was at the time the co-creator of Apache Kafka and had led
data infrastructure at LinkedIn, and the article is a direct reply to
Nathan Marz's Lambda Architecture, which Marz had described a few years
earlier as batch plus speed layers reconciled at query time.

The name has no formal alternate in the literature the way some GoF patterns
do, but practitioners commonly say "streaming-only architecture" or "unified
log architecture" when writing for an audience unfamiliar with the Greek
letter naming convention inherited from Lambda. The pattern is sometimes
mixed up with "event sourcing" or "Kafka Streams" in casual conversation,
but those are implementation techniques a Kappa system typically uses, not
synonyms for the architecture itself. Kreps' own follow-up post, published on
the Confluent blog under the title "Turning the database inside out," extends
the same reasoning to argue that a log-centric architecture applies
beyond analytics pipelines into application state management generally
(Kreps, J., "Turning the Database Inside-Out with Apache Samza," Confluent
Blog, 2015, verified 2026-08-02).

## 2. Problem and context

A team running analytics or derived views over an event stream commonly
starts with a batch pipeline. Nightly jobs read raw logs from a data
warehouse, compute aggregates, and write results a downstream service reads.
This works until the business needs those aggregates sooner than the next
batch window, at which point the team is tempted to also stand up a
streaming pipeline that computes the same aggregates in near real time and
serves them until the batch job "catches up" and overwrites the approximate
streaming result with the exact batch one. That is Lambda Architecture, and
it solves the latency problem, but it creates a second one. Every
transformation, every join, every business rule now has to be implemented
twice, once in the batch framework's idioms and once in the streaming
framework's idioms, and the two implementations drift apart the moment
either one is patched without the other. Kreps' article states the core
complaint directly. The two versions of the code will drift, testing them
consistently is hard, and running two systems that must agree is
operationally more expensive than running one (Kreps, J., "Questioning the
Lambda Architecture," O'Reilly Radar, 2 July 2014, verified 2026-08-02).

The Kappa problem statement is narrower than "how do we process data." It is
specifically this. How do we get low-latency continuous processing of a data
set while keeping the ability to reprocess the entire history when the
processing logic changes, a schema evolves, a bug is found, or a new
downstream consumer needs a fresh materialized view built from scratch,
without maintaining two codebases. The context in which this problem arises
assumes three things are already true or attainable. The raw events can be
captured as an ordered, replayable log rather than only as row updates in a
transactional database. The retention window of that log can be made long
enough, or cheap enough via tiered storage, to cover the reprocessing need.
And the stream processing framework in use can consume historical data at
whatever throughput the backlog demands, not merely at the live event rate.
When any of those three preconditions is false, for example when the source
system is a mutable OLTP database with no change log and no retention
policy that keeps history, Kappa is not directly applicable and the team
either builds a change data capture layer to create the log first, or falls
back to a batch-oriented design.

## 3. Forces

The dominant force Kappa optimizes is engineering consistency between
historical and live processing, at the cost of accepting that all
processing, including bulk reprocessing of years of history, must run
through the same stream processing engine. This trades operational
simplicity, one code path, one deployment target, one set of monitoring
dashboards, against a real constraint. Stream processing engines are
general-purpose compute over unbounded data, and they are not always as
throughput-efficient per core as a batch engine purpose-built for scanning a
columnar warehouse table. A backfill that a batch engine handles in ten
minutes might take Kappa's own reprocessing job an hour if the throughput
tuning is not done deliberately, which is precisely the operational tuning
Uber's engineering team documented when building their production Kappa
pipeline (Uber Engineering, "Designing a Production-Ready Kappa Architecture
for Timely Data Stream Processing," Uber Blog, verified 2026-08-02).

Latency is a force Kappa strongly favors. Because there is only one
processing path and it is the streaming one, results are available
continuously rather than waiting for a batch window, and there is no
window during which an approximate streaming answer and an eventual exact
batch answer disagree. Consistency between what a consumer sees during
reprocessing and what it saw during live processing is a second favored
force, since replaying the same code against the same ordered log is
deterministic given deterministic processing logic. The forces Kappa
sacrifices are storage cost and reprocessing throughput headroom. Retaining
enough log history to reprocess from scratch, and paying for the compute
to do so at a pace acceptable to the business, is a real and ongoing cost
that a Lambda batch layer, backed by cheap object storage and elastic batch
compute, sometimes handles more cheaply. Coupling to a single stream
processing framework is also a force sacrificed. A Lambda shop can pick the
best tool independently for the batch and speed layers. A Kappa shop is
betting that one framework, usually Flink or Kafka Streams, is good enough
at both continuous and bulk-historical processing to avoid needing a second
tool at all.

## 4. Applicability and non-applicability

Reach for Kappa Architecture when the source of truth can be represented as
an append-only, ordered, replayable log of events, and when the business
genuinely needs both continuous low-latency views and the ability to
recompute those views from history without maintaining two codebases.
Concretely, Kappa fits fraud detection and risk scoring pipelines where a
model update must be backfilled against the last several months of
transactions using the identical scoring code that will run live tomorrow,
close to the case Uber describes for their sessionization and pricing
pipelines (Uber Engineering, "Designing a Production-Ready Kappa
Architecture for Timely Data Stream Processing," Uber Blog, verified
2026-08-02). It fits materialized view maintenance, where a downstream
read model, a search index, a cache, a denormalized table, is a pure
function of the event log and rebuilding it from scratch is a required
operational capability, not a rare emergency. It fits organizations that
have already standardized on Kafka or an equivalent durable, replayable log
as their integration backbone, since the reprocessing capability Kappa
needs is close to free once the log exists and its retention or tiering is
configured for it.

Kappa is the wrong choice when the source data genuinely lives in a
mutable, non-append-only system with no practical way to produce an ordered
change log, for example a legacy database accessed only via periodic full
exports with no primary-key-based change tracking. In that situation
building the log itself is the hard part, and a batch-first design that
reads the exports directly may be simpler until change data capture is in
place. It is the wrong choice when the processing genuinely needs a
computation model batch engines are much better suited to, such as large
iterative joins across denormalized warehouse tables that do not decompose
naturally into a streaming windowed join, where forcing the join into a
stream processor produces either unbounded state growth or an approximation
the business will not accept. It is the wrong choice when reprocessing
history is rare enough, and the volume small enough, that a scheduled batch
job run once a quarter is genuinely cheaper in engineering time than
building and operating a permanently-online stream processing cluster
sized to also absorb full-history reprocessing runs. Not every team has
Uber's or Disney's event volume, and for a modest-scale internal reporting
pipeline a nightly batch job with no streaming layer at all can be the
correct, boring answer. It is also the wrong choice when strict
exactly-once, cross-partition transactional consistency across many
downstream tables is required at all times and the chosen stream processing
engine's consistency guarantees for that scenario are weaker than what a
transactional batch ETL tool provides, a real limitation Martin Kleppmann
discusses when comparing log-based derived data pipelines to transactional
systems (Kleppmann, M., "Designing Data-Intensive Applications," O'Reilly,
1st edition, 2017, Chapter 11, "Stream Processing," p. 439-475).

## 5. Structure

A Kappa system has four participant roles. The Event Log is the durable,
ordered, append-only, replayable store of raw events, most commonly an
Apache Kafka topic, sometimes with tiered storage extending its retention
to object storage so replay is affordable at large scale. Its responsibility
is to accept writes in order, assign each event a monotonically increasing
offset within its partition, and serve reads from any offset a consumer
requests, including offset zero for a full replay. The Stream Processor is
the single computation engine, typically Apache Flink, Kafka Streams,
Apache Spark Structured Streaming, or a managed equivalent, and its
responsibility is to run one codebase that consumes the log, applies the
business logic (filtering, joining, windowing, aggregating), and writes
results to a Serving Store. The Serving Store, sometimes a key-value
store, a search index, a relational read replica, or another Kafka topic, is
the materialized view a downstream consumer actually queries. Its
responsibility is to expose the current output of the stream processor's
logic with acceptable read latency, and it is treated as fully disposable,
rebuildable at any time by replaying the log through the stream processor
again. The fourth participant, present in every real deployment even though
Kreps' original article does not name it separately, is the Reprocessing
Job Instance, a second, temporary instance of the same stream processor
code, started when logic changes, consuming the log from an earlier offset
(often the beginning) into a new, parallel Serving Store, which is then
atomically swapped in to replace the old one once it has caught up to the
live event position.

The structural rule that separates Kappa from an arbitrary
streaming pipeline is that there is exactly one processing codebase for both
the "normal" continuous consumer and the "reprocessing" consumer. They
differ only in their starting offset and their output destination, never in
their logic. This is the structural property that removes the Lambda
Architecture's dual-codebase problem.

## 6. ASCII structure diagram

```
+------------------------------------------------------------+
|                     EVENT LOG (Kafka)                       |
|  partition 0: [e0][e1][e2][e3][e4][e5][e6]---> (live tail)  |
|  partition 1: [e0][e1][e2][e3][e4]------------> (live tail) |
|  retention. N days, or tiered to object storage for N years |
+---------------------+----------------------------------------+
                       |  offset X (live)      |  offset 0 (replay)
                       v                        v
        +--------------------------+   +---------------------------+
        |  STREAM PROCESSOR         |   |  STREAM PROCESSOR          |
        |  (live instance)          |   |  (reprocessing instance)   |
        |  same codebase, version N |   |  same codebase, version N+1|
        +-------------+-------------+   +--------------+--------------+
                       |                                |
                       v                                v
        +--------------------------+   +---------------------------+
        |  SERVING STORE (current)  |   |  SERVING STORE (shadow)    |
        |  read by consumers today  |   |  built in the background   |
        +--------------------------+   +--------------+--------------+
                                                        |
                                        once caught up, |  atomic swap
                                                        v
                                        becomes the new "current" store
```

## 7. Dynamics

In steady state, a producer appends an event to the log. The log assigns it
an offset and durably persists it (Kafka's default is replication across a
configurable number of brokers before the write is acknowledged). The live
stream processor instance, which has an open, continuously advancing
consumer position, reads the event, applies its transformation and
aggregation logic, and writes the resulting update to the current serving
store, typically within single-digit seconds of the event being produced.
A downstream consumer querying the serving store observes the update almost
immediately after it happened.

When the processing logic must change, for example a bug fix, a new
aggregation window, or a schema migration, the operator does not patch the
live instance in place if the change affects historical correctness.
Instead, they deploy a second instance of the updated code, pointed at a
fresh consumer group with its offset reset to the earliest retained point
in the log, or to whatever offset is old enough to cover the required
reprocessing window, and directed to write into a new, empty serving store
rather than the live one. This reprocessing instance consumes the backlog
as fast as its resources allow, typically far faster than real-time event
arrival because it is not waiting on new events, until its consumer
position catches up to the live tail of the log. At that point the operator
performs a cutover. Downstream consumers are repointed from the old serving
store to the new one, an operation Kreps describes as swapping "output data
to a new output table" once the reprocessing catches up (Kreps, J.,
"Questioning the Lambda Architecture," O'Reilly Radar, 2 July 2014, verified
2026-08-02). The old live instance and its now-superseded serving store are
decommissioned. This sequence is the entire "how do we deploy a logic
change" story in Kappa. There is no separate migration tooling, because
replay against the log is itself the migration mechanism.

```
producer          log (offsets)          live processor    serving store A (current)
  |  write e --------> [.. e0..eN] --------->  process e --------> write result
  |                                                                 read by consumers
  |
  |  (later. logic change deployed)
  |
                   reprocessing consumer (new group, offset 0)
                        |
                        v
                   process e0..eN (fast catch-up) -----> serving store B (shadow, building)
                        |
                        v (reaches live tail)
                   cutover. consumers repointed A -> B
                   store A decommissioned
```

## 8. Implementation variants

The most common production variant pairs Apache Kafka as the log with
Apache Flink as the stream processor, using Flink's savepoint mechanism
to checkpoint and later restore or fork job state. Flink's own documentation
states plainly that savepoints let an operator "stop-and-resume, fork, or
update your Flink jobs" (Apache Flink Documentation, "Savepoints," Apache
Software Foundation, verified 2026-08-02), which is the mechanism many teams
use instead of a full cold replay when the change is small enough to be
expressed as a state-compatible upgrade rather than a full history
reprocessing.

A second variant uses Kafka Streams or ksqlDB as the processing
engine instead of a separate cluster like Flink, trading operational
independence (Kafka Streams runs as a library inside the application
process, with no separate cluster to manage) for a tighter coupling to the
JVM and to Kafka specifically. Confluent's own developer education content
frames compacted Kafka topics as "perfect for providing backing to ksqlDB
tables, or Kafka Streams KTables" (Confluent, "Compaction," Confluent
Developer, verified 2026-08-02), which is the log-compaction-backed serving
store variant.

A third variant, which Uber documented explicitly as their production
choice, uses Apache Spark Streaming for both the live and the
reprocessing paths, treating a historical Hive table as a synthetic
streaming source for the backfiller so the same windowing and correctness
semantics apply whether the input is the live Kafka topic or the historical
Hive data (Uber Engineering, "Designing a Production-Ready Kappa
Architecture for Timely Data Stream Processing," Uber Blog, verified
2026-08-02). This variant is notable because it shows Kappa does not
strictly require the historical source to be the same physical log the live
path reads from, only that the same processing code and semantics apply to
both.

A fourth, lighter-weight variant relies on log compaction instead of full
retention to bound storage cost. Rather than retaining every raw event
forever, a compacted topic retains only the most recent value per key,
which the Kafka documentation states is designed to "keep the most recent
value for a given key" (Apache Kafka Documentation, "Log Compaction,"
Apache Software Foundation, verified 2026-08-02), so replaying a compacted
topic reconstructs current state cheaply, at the cost of losing the ability
to replay the full sequence of intermediate updates, which matters if the
downstream logic depends on transitions rather than only final values.

## 9. Known production uses

Uber built and documented a production Kappa architecture for its
sessionization pipeline, combining a live Spark Streaming job processing
"75 cores and 1.2 terabytes of memory" with a Hive-table-backed backfiller
that reprocesses "approximately 10 terabytes of Hive data across nine days"
using the identical windowing logic as the live path, specifically to solve
the problem that some downstream teams needed second-level latency while
others needed month-over-month accuracy that only a full reprocess could
guarantee (Uber Engineering, "Designing a Production-Ready Kappa
Architecture for Timely Data Stream Processing," Uber Blog, verified
2026-08-02).

Twitter migrated an internal analytics pipeline from a Lambda-style design
to Kappa on Google Cloud Platform, reporting that the migrated pipeline
processes "approximately 400 billion events in real-time" daily and
achieves lower operational cost alongside architectural simplicity compared
to the two-path predecessor, according to a technical summary citing
Twitter's own migration writeup (Waehner, K., "Kappa Architecture is
Mainstream, Replacing Lambda," kai-waehner.de, 23 September 2021, verified
2026-08-02).

Disney routes production data writes through Kafka as the system of record.
"All data writes at Disney go through Kafka as the source of truth," using
Kafka's tiered storage to keep long retention affordable so that
downstream applications, including analytics and personalization systems,
can consume both the live tail and, when needed, replay historical data
from the same log rather than maintaining a separate batch pipeline for
history (Waehner, K., "Kappa Architecture is Mainstream, Replacing Lambda,"
kai-waehner.de, 23 September 2021, verified 2026-08-02).

## 10. Consequences

The positive consequences are concentrated on engineering and operational
simplification. There is one codebase for both the live path and any
reprocessing, so a bug fix or a logic change is written once and applies
identically to history and to the future, removing the drift risk Kreps
identified as Lambda's core flaw (Kreps, J., "Questioning the Lambda
Architecture," O'Reilly Radar, 2 July 2014, verified 2026-08-02). There is
one processing framework to operate, monitor, and staff for, rather than a
batch framework and a streaming framework each needing separate expertise.
Latency for consumers of the live path is uniformly low, because there is
no waiting for a periodic batch job to reconcile an approximate streaming
result with an eventual exact one. Every result the serving store holds was
produced by the same deterministic logic. Reprocessing, when needed, is a
first-class, routinely exercised operation rather than a rare disaster
recovery procedure, which in practice means teams that adopt Kappa tend to
also gain confidence that their reprocessing path actually works, because
it is the same path used for every deployment of new logic.

The negative consequences center on cost and coupling. Retaining enough log
history to support full reprocessing, or paying for tiered storage to
extend retention cheaply, is an ongoing infrastructure cost that scales
with both event volume and the reprocessing window the business demands.
Waehner's writeup frames tiered storage as the technology that made
large-scale Kappa "cost-efficient," implying that before it was widely
available the storage cost of Kappa at scale was a real barrier (Waehner,
K., "Kappa Architecture is Mainstream, Replacing Lambda," kai-waehner.de, 23
September 2021, verified 2026-08-02). Reprocessing throughput is bounded by
how efficiently the chosen stream processing engine can run in a
backlog-catch-up mode, and Uber's own writeup treats sizing that
reprocessing capacity as a deliberate, real engineering exercise
rather than something that comes for free (Uber Engineering, "Designing a
Production-Ready Kappa Architecture for Timely Data Stream Processing,"
Uber Blog, verified 2026-08-02). The architecture also creates a strong
dependency on a single stream processing framework being adequate for every
processing need the organization has, including patterns, such as large
denormalized batch joins, that some stream processors handle awkwardly
compared to a batch engine purpose-built for them, an observation
Kleppmann develops at length when comparing the strengths of batch and
stream processing models (Kleppmann, M., "Designing Data-Intensive
Applications," O'Reilly, 1st edition, 2017, Chapter 10 and Chapter 11, p.
403-475).

## 11. Failure modes and misuse

- **Symptom.** Reprocessing a full history takes days and the business
  cannot wait. Cause. The reprocessing job was never load-tested at full
  historical volume, or the stream processing cluster is sized only for
  live-rate throughput, not for the burst throughput a cold replay demands.
  Fix. Treat reprocessing throughput as a capacity-planned, tested
  operation, size the cluster (or use elastic autoscaling during a replay
  window) for the worst-case backlog volume, and, as Uber did, measure and
  publish the actual time to catch up for a known backlog size so the
  business has a real expectation to plan around rather than an assumption
  (Uber Engineering, "Designing a Production-Ready Kappa Architecture for
  Timely Data Stream Processing," Uber Blog, verified 2026-08-02).

- **Symptom.** Two consumers of the "same" log see different results for
  the same event. Cause. Nondeterminism has crept into the processing
  logic, commonly through wall-clock timestamps, random number generation,
  or external service calls made mid-stream whose answer can differ between
  the live run and a later replay. Fix. Audit the processing code for any
  source of nondeterminism and replace wall-clock reads with event-time
  fields carried in the event itself, and replace any external lookups with
  either a versioned, replayable side input or an explicit acceptance that
  the external answer is allowed to legitimately change between runs,
  documented as such.

- **Symptom.** Storage cost for the event log grows without bound and
  nobody can explain why. Cause. Retention policy was set to keep data
  forever by default without a corresponding compaction or tiering
  strategy, or the log is retaining every intermediate update for a
  key with many distinct values when only the latest value per key is ever
  needed downstream. Fix. Apply log compaction where only current-value
  semantics are needed, since compaction is explicitly designed to "keep
  the most recent value for a given key" (Apache Kafka Documentation, "Log
  Compaction," Apache Software Foundation, verified 2026-08-02), and apply
  tiered storage or an explicit, business-justified retention window
  everywhere full history genuinely must be kept.

- **Symptom.** A "quick fix" is patched directly into the live processing
  instance instead of going through a fresh reprocessing run, and
  downstream consumers start seeing inconsistent historical and current
  values. Cause. Under time pressure, an operator bypasses the Kappa
  discipline of treating every logic change as a new reprocessing instance
  with a cutover, patching the running job in place. Fix. This is process
  discipline, not a technical control. The failure is the team abandoning
  the pattern's core guarantee under pressure, and the remedy is treating
  the reprocess-and-cutover sequence as the only sanctioned deployment path
  for any change that affects historical correctness, with a fast,
  well-rehearsed cutover procedure so patching live stops being the path of
  least resistance.

- **Symptom.** The serving store swap during cutover causes a visible gap
  or a flicker of stale data for consumers. Cause. The cutover was
  implemented as a slow, multi-step DNS or configuration change rather than
  an atomic switch, or the new serving store was not fully warmed and
  validated before traffic was redirected to it. Fix. Use an atomic
  pointer-swap mechanism at the serving layer (an alias, a routing table
  entry, a load balancer target group flip) rather than a gradual rollout,
  and validate the shadow serving store's completeness and correctness
  against a sample of known-good historical answers before the swap, not
  after.

## 12. Trade-off matrix

| Force | Kappa Architecture | Lambda Architecture | Event Sourcing (application-level) |
|---|---|---|---|
| Codebase count for one derived view | One, shared by live and reprocessing | Two, batch and speed layers implemented separately | One, but the write model and the log are usually application-owned rather than infrastructure-owned |
| Latency of current answer | Low, continuous, no batch-window wait | Low from speed layer, but approximate until batch layer reconciles | Low, depends on how projections are updated |
| Correctness of current answer over time | Deterministic replay of one logic path | Eventually exact once batch layer catches up, temporarily approximate before that | Deterministic, same guarantee as Kappa when backed by a log |
| Reprocessing cost model | Ongoing, paid via stream processor compute at replay speed | Paid separately via the batch engine, often cheaper per unit of historical data processed | Same as Kappa if backed by an external durable log, can be cheaper if events are small and the aggregate state is compact |
| Operational surface area | One processing framework, one operational runbook | Two frameworks, two runbooks, reconciliation logic between them | One framework, but often embedded per-service rather than centrally operated |
| Best fit | Continuous derived views over a naturally streamable, high-volume log with routine reprocessing needs | Environments where the batch engine is meaningfully cheaper or more capable for historical computation and the two-codebase cost is accepted | Single-service, transactional systems where the log is the authoritative write model of one bounded context, not a cross-team integration backbone |

## 13. Related and incompatible patterns

Kappa Architecture composes naturally with event sourcing, since an
event-sourced aggregate's append-only event stream is itself a valid Kappa
log for the bounded context that owns it. The difference is scope, event
sourcing is usually scoped to a single service's write model, while Kappa is
usually applied at the integration or analytics layer across many
producers and consumers. It composes with CQRS, since the serving store
in a Kappa system is precisely a CQRS read model, materialized by
projecting the event log through the stream processor, and Kappa's
reprocess-and-cutover discipline is the natural way to rebuild a CQRS
projection from scratch when its shape changes. It composes with log
compaction, which is the mechanism most Kappa deployments use to bound
storage cost for the subset of state where only the latest value per key
matters, as opposed to the full event history.

Kappa Architecture directly replaces Lambda Architecture in the sense
that Kreps proposed it specifically as an alternative to Lambda's
dual-codebase design, and adopting Kappa is usually a decision to retire an
existing Lambda pipeline's separate batch layer once the streaming layer's
reprocessing capability has been proven equivalent. It is incompatible, in
the sense of directly contradicting its own core discipline, with a
two-tier batch-and-speed-layer design where the batch layer's logic is
allowed to drift from the streaming layer's logic over time. A system that
claims to be Kappa but maintains a separate, independently-evolving batch
correction path is not actually Kappa, it is Lambda wearing a different
label, which is the exact anti-pattern Kreps' original article warns
against.

## 14. Refactoring path in and out

To introduce Kappa into an existing Lambda-style pipeline, first confirm the
raw event source can be captured as an ordered, replayable log with a
retention window at least as long as the longest reprocessing scenario the
business needs. If the current source is a mutable database with no change
log, stand up change data capture (writing to a Kafka topic via a CDC
connector) before anything else, since this is the prerequisite the rest of
the migration depends on. Next, port the batch layer's logic into the
streaming framework, running it initially as a shadow pipeline that writes
to a new serving store while the existing Lambda output continues serving
production traffic unchanged, so the two can be compared for correctness
without any consumer-facing risk. Once the shadow streaming pipeline's
output matches the batch layer's output on a representative historical
window, exercise the reprocessing path deliberately, replaying the full
retained history through the streaming logic into a fresh serving store,
and validate that a from-scratch replay produces the same result as the
live-accumulated one, since this is the capability the whole migration is
buying and it must be proven before the old batch layer is retired. Only
after the reprocessing path has been validated end to end should the
Lambda batch layer and its speed-layer reconciliation logic be
decommissioned, and the streaming pipeline's serving store becomes the sole
source downstream consumers read from.

To move away from Kappa when it stops earning its place, most often because
reprocessing cost or throughput has become the dominant operational
expense, the reverse path is to identify which parts of the processing
logic genuinely need continuous low latency and keep only those in the
streaming path, while reintroducing a batch layer specifically for the
parts of the workload that are large, infrequent, historical
recomputations poorly suited to a stream processor's execution model, in
effect a deliberate, scoped return to a Lambda-style split rather than a
full architectural reversal. This is a judgment call about which forces
matter more at the new scale, not a mechanical refactoring recipe, and it
should be driven by measured reprocessing cost and latency data from the
existing Kappa deployment rather than a hypothetical concern.

## 15. Testing and verification

Testing a Kappa pipeline centers on one property that does not exist in a
Lambda pipeline. The same logic must produce the same output whether it is
run live, one event at a time, or replayed in bulk from the beginning of
the log. The most direct verification technique is a determinism replay
test, capturing a fixed, representative slice of the log as a test
fixture, running the processing logic against it twice, once simulating
live one-event-at-a-time delivery and once simulating bulk replay, and
asserting the two runs produce byte-identical output. Any mismatch
indicates a hidden nondeterminism, commonly a wall-clock read, a random number
generator, or an external call, that must be found and removed before the
pipeline can be trusted to reprocess correctly. Flink's testing guidance for
stateful functions similarly emphasizes exercising restore-from-savepoint
paths as part of normal test coverage, not only forward execution, because
the restore path is exactly the reprocessing path in Kappa terms (Apache
Flink Documentation, "Savepoints," Apache Software Foundation, verified
2026-08-02).

A second test worth running is a backfill-versus-live equivalence test at
integration scale. Run a known historical window through both the live
consumer group (by replaying it as if live) and the reprocessing consumer
group, and diff the resulting serving stores key by key. This is the
integration-level analogue of the unit-level determinism test and is the
test Uber's own writeup implies was necessary before trusting their
backfiller in production, since they explicitly preserved "the same
windowing semantics as production" in their Hive-backed backfiller (Uber
Engineering, "Designing a Production-Ready Kappa Architecture for Timely
Data Stream Processing," Uber Blog, verified 2026-08-02). A third technique
is rehearsing the cutover procedure itself under failure conditions.
Simulate the shadow-store-to-live-store swap under load, including a
rollback, so that the operational procedure is proven safe before it is
needed under real production pressure during an actual logic migration.

## 16. Observability signals

The single most important observability signal in a Kappa system is
consumer lag, the difference between the log's current write offset and
a consumer's current read offset, measured per consumer group and per
partition. For the live processing instance, lag should be small and
stable. A steadily growing lag means the live instance cannot keep up with
the event rate, which will eventually produce staleness in the serving
store that looks identical to an outage from a downstream consumer's
perspective. For a reprocessing instance mid-replay, lag is expected to be
large and should be monitored as a rate of decrease, offsets consumed per
second, so operators can project a completion time, the same measurement
Uber's team implicitly relied on when they reported a nine-day backfill
window for a ten-terabyte replay (Uber Engineering, "Designing a
Production-Ready Kappa Architecture for Timely Data Stream Processing,"
Uber Blog, verified 2026-08-02).

Serving store freshness, measured as the timestamp of the most recently
applied event versus wall-clock time, is the second signal worth tracking, and
should be watched separately for the live store and, during a migration, the
shadow store being built. Log retention headroom, the gap between the
oldest retained offset and the oldest offset any planned reprocessing might
need, should be alerted on before it becomes zero, since a log that has
expired the data a reprocessing job needs cannot be replayed at all,
silently removing Kappa's core capability. Dashboards should also track
reprocessing throughput, events per second consumed during a replay, over
time across successive migrations, since a downward trend in that number as
data volume grows is the earliest warning that the stream processing
cluster needs to be scaled before the next scheduled logic change becomes
operationally painful.

## 17. Security and privacy implications

Because a Kappa log retains raw events for as long as any future
reprocessing might need them, often far longer than a transactional
database would retain the same data, it substantially expands the retention
footprint of any personal or sensitive data captured in those events, which
has direct implications under data protection regimes that require the
ability to delete a specific individual's data on request. A durable,
append-only log is structurally difficult to selectively delete from
without breaking the offset-based replay contract every downstream
consumer depends on, so teams building Kappa systems over data subject to a
right-to-erasure requirement need an explicit design for it, commonly
either encrypting each subject's events with a per-subject key that can be
destroyed to render the data unrecoverable (a technique often called
crypto-shredding), or routing personal data through a mutable, compacted
topic keyed by subject identifier where a tombstone record can be written
and compaction will eventually purge the value.

Access control on the log itself is a broader attack surface than access
control on a single database table, since every consumer that can read the
log, live or historical, gains access to the full raw event history, not
merely to a current-state view. A serving store can be scoped to expose
only derived, minimized fields to a given downstream consumer, but any
consumer with direct log access effectively has access to everything ever
written to it, which argues for treating direct log read access as a
narrowly-granted, audited permission rather than a default for every team
that wants to build a new derived view. This is an analytical point
drawn from the architecture's replay-everything design, not a claim sourced
to any single publication.

## 18. References

- Kreps, J., "Questioning the Lambda Architecture," O'Reilly Radar, 2 July
  2014, https://www.oreilly.com/radar/questioning-the-lambda-architecture/,
  verified 2026-08-02.
- Kreps, J., "Turning the Database Inside-Out with Apache Samza," Confluent
  Blog, 2015, verified 2026-08-02.
- Uber Engineering, "Designing a Production-Ready Kappa Architecture for
  Timely Data Stream Processing," Uber Blog,
  https://www.uber.com/en-BR/blog/kappa-architecture-data-stream-processing/,
  verified 2026-08-02.
- Waehner, K., "Kappa Architecture is Mainstream, Replacing Lambda,"
  kai-waehner.de, 23 September 2021,
  https://www.kai-waehner.de/blog/2021/09/23/real-time-kappa-architecture-mainstream-replacing-batch-lambda/,
  verified 2026-08-02.
- Apache Kafka Documentation, "Log Compaction," Apache Software Foundation,
  verified 2026-08-02.
- Confluent, "Compaction," Confluent Developer,
  https://developer.confluent.io/courses/architecture/compaction/, verified
  2026-08-02.
- Apache Flink Documentation, "Savepoints," Apache Software Foundation,
  verified 2026-08-02.
- Kleppmann, M., "Designing Data-Intensive Applications," O'Reilly Media,
  1st edition, 2017, Chapter 10 "Batch Processing" and Chapter 11 "Stream
  Processing," p. 403-475.

## Code examples

### TypeScript. A minimal Kappa-style replayable reducer

The same pure function is used for live, one-event-at-a-time processing and
for bulk replay from offset zero, which is the structural property that
makes an implementation "Kappa" rather than merely "streaming."

```typescript
type LogEvent = { offset: number; key: string; amount: number };
type State = Map<string, number>;

function applyEvent(state: State, event: LogEvent): State {
  const current = state.get(event.key) ?? 0;
  state.set(event.key, current + event.amount);
  return state;
}

function processLive(state: State, event: LogEvent): State {
  return applyEvent(state, event);
}

function replayFromLog(log: LogEvent[], fromOffset: number): State {
  const state: State = new Map();
  for (const event of log) {
    if (event.offset >= fromOffset) {
      applyEvent(state, event);
    }
  }
  return state;
}

const log: LogEvent[] = [
  { offset: 0, key: "acct-1", amount: 100 },
  { offset: 1, key: "acct-2", amount: 50 },
  { offset: 2, key: "acct-1", amount: -30 },
];

let liveState: State = new Map();
for (const event of log) {
  liveState = processLive(liveState, event);
}

const reprocessedState = replayFromLog(log, 0);

const liveMatchesReplay =
  JSON.stringify([...liveState.entries()].sort()) ===
  JSON.stringify([...reprocessedState.entries()].sort());

console.log("live", [...liveState.entries()]);
console.log("replay", [...reprocessedState.entries()]);
console.log("deterministic replay matches live", liveMatchesReplay);
```

### Python. Reprocessing instance with a cutover simulation

This models the two-instance, atomic-swap cutover from dimension 7. A live
consumer keeps a serving store current, and a reprocessing consumer builds a
shadow store from offset zero, which is only swapped in once it has caught
up.

```python
from dataclasses import dataclass


@dataclass
class Event:
    offset: int
    key: str
    amount: int


def process_event(store: dict, event: Event) -> None:
    store[event.key] = store.get(event.key, 0) + event.amount


def run_consumer(log: list[Event], from_offset: int) -> dict:
    store: dict = {}
    for event in log:
        if event.offset >= from_offset:
            process_event(store, event)
    return store


def cutover(live_store: dict, shadow_store: dict, live_offset: int,
            shadow_offset: int) -> dict:
    if shadow_offset < live_offset:
        raise RuntimeError("shadow store has not caught up, refusing cutover")
    return shadow_store


log = [
    Event(0, "acct-1", 100),
    Event(1, "acct-2", 50),
    Event(2, "acct-1", -30),
    Event(3, "acct-3", 75),
]

live_store = run_consumer(log, from_offset=0)
live_offset = log[-1].offset

updated_logic_shadow_store = run_consumer(log, from_offset=0)
shadow_offset = log[-1].offset

new_live_store = cutover(live_store, updated_logic_shadow_store,
                          live_offset, shadow_offset)

assert new_live_store == live_store, "reprocessed logic should match live for unchanged logic"
print("live store", live_store)
print("cutover succeeded, new live store", new_live_store)
```

### Go. Consumer lag observability signal

This implements the dimension 16 consumer-lag calculation, the primary
observability signal for a Kappa pipeline, as a small standalone program.

```go
package main

import "fmt"

type ConsumerGroup struct {
	Name           string
	LastReadOffset int64
}

type Topic struct {
	LatestOffset int64
}

func lag(topic Topic, group ConsumerGroup) int64 {
	l := topic.LatestOffset - group.LastReadOffset
	if l < 0 {
		l = 0
	}
	return l
}

func main() {
	topic := Topic{LatestOffset: 1000000}

	liveGroup := ConsumerGroup{Name: "live-processor", LastReadOffset: 999950}
	reprocessGroup := ConsumerGroup{Name: "reprocessing-v2", LastReadOffset: 400000}

	fmt.Printf("%s lag %d (healthy if small and stable)\n",
		liveGroup.Name, lag(topic, liveGroup))
	fmt.Printf("%s lag %d (expected large during replay, track rate of decrease)\n",
		reprocessGroup.Name, lag(topic, reprocessGroup))

	if lag(topic, liveGroup) > 10000 {
		fmt.Println("ALERT. live processor falling behind, serving store going stale")
	} else {
		fmt.Println("live processor lag within healthy bound")
	}
}
```

All three samples were executed locally. `npx tsc --strict --noEmit`
compiled the TypeScript sample cleanly after renaming the local type from
`Event` to `LogEvent` to avoid colliding with the DOM lib's global `Event`
type, and `node --experimental-strip-types` ran it and printed matching
live and replay output. `python3` ran the Python sample and printed the
expected live store and cutover output. `go run` executed the Go sample
and printed both lag calculations plus the healthy-bound check. A fourth
language was not added because three named languages already give the
pattern's structural property, determinism between live and replayed
processing, coverage across a dynamically typed language, a statically
typed compiled language, and a systems language with explicit numeric
types, and a fourth sample would repeat the same reducer shape without
adding a new implementation-variant insight.
