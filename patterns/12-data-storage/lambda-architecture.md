---
name: Lambda Architecture
slug: lambda-architecture
family: 12-data-storage
category: Data Processing
aliases: [Batch/Realtime Architecture]
first_described: "Nathan Marz 2011"
maturity: contested
related: [cqrs, event-sourcing, materialized-view, saga]
incompatible_with: [kappa-architecture]
verified: 2026-08-02
---

# Lambda Architecture

## 1. Name, aliases, and lineage

Lambda Architecture is a data processing pattern for computing arbitrary
functions over a data set by running two parallel processing paths, a batch
path that recomputes results from the complete history and a stream path that
covers the gap while the batch path is still working, then merging the two at
query time.

Nathan Marz, the creator of Apache Storm, coined the term in a 2011 blog post,
originally calling it the batch/realtime architecture before settling on the
Greek letter name because a diagram of the three layers resembles the shape
of the letter lambda ([Wikipedia, Lambda architecture](https://en.wikipedia.org/wiki/Lambda_architecture),
verified 2026-08-02). Marz later formalized the pattern in Nathan Marz with
James Warren, *Big Data*, Manning, 2015 (the full title and subtitle are
given at the publisher's listing cited below). The book's publisher listing
credits Marz as the originator of the pattern and the creator of Apache
Storm, the stream processor he built to serve as the speed layer
implementation ([Manning, Big Data by Nathan Marz and James Warren](https://www.manning.com/books/big-data),
verified 2026-08-02).

There is no second name in wide use for the whole pattern, but the three
components each carry their own vocabulary across vendors. The batch path is
called the batch layer in Marz's own terminology, and the same role is called
the cold path or the historical path in Microsoft's reference architectures.
The stream path is the speed layer in Marz's terms, the hot path or real-time
path elsewhere. The merge point is the serving layer everywhere the pattern is
discussed, because this name never collided with an existing term.

The pattern is marked contested in this catalog, not because it is rare in
production, but because a widely read and widely cited rebuttal exists from
Jay Kreps, then an engineer at LinkedIn and later a co-founder of Confluent,
arguing that maintaining two codebases to compute the same result is not worth
the cost, and proposing a single-path alternative he named Kappa architecture
([Jay Kreps, Questioning the Lambda Architecture, O'Reilly Radar, 2 July 2014](https://www.oreilly.com/radar/questioning-the-lambda-architecture/),
verified 2026-08-02). The debate between the two names is part of the
pattern's own history and is treated in full in dimension 13 below.

## 2. Problem and context

A team needs to answer a query over an ever-growing data set, and the query
must be both correct over the full history and current within seconds of the
latest event, and no single processing engine available to the team can give
them both at once.

The concrete shape of the problem looks like this. A recommendation service
needs a count of how many times every item has been viewed, ever, so that
new items can be ranked against the full history, and it also needs the last
few minutes of views reflected immediately so that a viral item shows up in
rankings within the hour rather than the next morning. A batch engine that
scans the entire event log nightly gives a correct count that is up to a day
stale. A stream processor that keeps a running tally in memory gives a
current count that has never been checked against the full history and will
drift from it whenever a worker restarts, a message is delivered twice, or a
bug in the streaming code silently miscounts for a week before anyone
notices.

The context that produces this problem has three ingredients present at
once. The data set is too large to recompute on every write, so some form of
precomputation into a queryable view is required. The correctness bar is
high enough that eventual, unauditable answers from a stream-only system are
not acceptable on their own, because a streaming job that double-counts for
a week and is only caught by chance leaves no way to know how wrong the
historical numbers already are. And the freshness bar is tight enough that
waiting for the next batch cycle, commonly hours, is not acceptable either.
Marz frames the underlying goal as human fault tolerance rather than only
machine fault tolerance. code has bugs, and a system that can be corrected by
recomputing from an immutable record of raw events is recoverable from a bad
deploy in a way that a system that mutates state in place is not (Nathan
Marz and James Warren, *Big Data*, Manning, 2015, chapter 1).

## 3. Forces

**Latency versus correctness.** The stream path buys low latency by
computing over an incomplete, unordered, and sometimes duplicated view of
the world. The batch path buys correctness by waiting for a complete,
sorted, deduplicated pass over everything. Lambda Architecture does not
resolve this tension, it accepts both answers and schedules the correct one
to eventually replace the fast one.

**Recomputability versus storage cost.** Keeping every raw event forever, in
an append-only, immutable master data set, is what makes the batch layer
able to recompute an entire view from scratch after a bug fix. That
immutability is the single design decision the whole pattern depends on, and
it is expensive. it means paying to store data that the current query logic
may never look at again, on the bet that a future query logic will need it.

**Operational simplicity versus dual implementation.** The pattern asks a
team to write, test, deploy, and operate the same business logic twice, once
in a batch idiom (a MapReduce job, a Spark batch transform) and once in a
streaming idiom (a Storm topology, a Flink job), against two different
runtime models. This is the force the pattern's critics attack hardest, and
it is real. two implementations of one aggregation function drift apart the
moment one of them is patched and the other is not.

**Consistency of the merged view versus availability of each half.** The
serving layer must expose a single answer, but it is built from two sources
that disagree by design during the window before a batch recompute catches
up. The pattern resolves this by making the serving layer's merge rule
explicit rather than accidental. batch views are authoritative once
computed, speed views only cover the delta since the last batch run, and the
speed-layer state for a window is discarded the moment the batch layer
absorbs that window.

**Team topology and cognitive load.** A batch layer written in a
functional, immutable style and a speed layer written against an
incrementally updated, mutable state machine call for different engineering
instincts, and a small team frequently ends up with the batch layer
maintained well and the speed layer treated as a stopgap nobody wants to
own, or the reverse.

## 4. Applicability and non-applicability

Applicability. Reach for Lambda Architecture when all of these hold together.

- The query needs to run over the full, growing history of the data, and
  recomputing that history occasionally is a real requirement, not a
  hypothetical one, because the transformation logic is expected to change
  over the system's lifetime and old results will need to be reproduced
  under the new logic.
- A correctness audit trail matters. regulators, finance, or an internal
  team need to be able to explain a number by pointing at the raw events
  that produced it, not only trust a running counter.
- Some subset of queries has a genuine low-latency requirement, seconds to a
  few minutes, that the batch cycle cannot meet, and that subset is worth
  the added engineering cost of a second, streaming code path.
- The team has, or is willing to build, the operational capacity to run two
  distinct processing systems, because this pattern trades engineering time
  for correctness plus freshness, and that trade only pays off when both
  halves are staffed.

Non-applicability, with the reason.

- The workload has no correctness-critical recomputation requirement, only
  a need for current numbers. this describes most operational dashboards
  and most product analytics, and a single stream-only pipeline (Kappa
  architecture, dimension 13) removes the second codebase entirely.
- The data volume is small enough that a batch job can run end to end in
  seconds or low minutes on the whole data set. at that size the batch
  layer itself is the fast path, and adding a speed layer buys nothing.
- The team cannot staff two runtime paradigms. a two-person team running
  both a Spark batch pipeline and a Flink streaming pipeline, each with
  its own deployment, monitoring, and on-call burden, is choosing an
  operational load that most small teams cannot sustain, and the pattern's
  own inventor now points toward a unified engine for most new systems
  where one is available (see the discussion of Marz's own later position
  in dimension 13).
- The transformation logic is genuinely fixed and will not need a full
  historical replay. an append-only log that only ever needs the same
  aggregation applied to it does not need a second, batch-computed source of
  truth to reconcile against.
- The domain tolerates eventual consistency and approximate counts without
  an audit requirement, for example live view counts on a video that are
  allowed to be off by a small percentage. a simpler streaming-only counter
  with periodic reconciliation is cheaper to build and to run.

## 5. Structure

- **Master data set.** An append-only, immutable log of every raw event the
  system has ever received, timestamped, never updated in place, never
  deleted except by an explicit, out-of-band retention policy. This is the
  single source of truth every other component is derived from.
- **Batch layer.** A component that reads the master data set on a schedule
  or on demand, and computes batch views, which are precomputed, queryable
  projections of the data answering the queries the system needs to serve.
  The batch layer is stateless between runs in the sense that it always
  recomputes a batch view from the master data set rather than
  incrementally updating a prior result, which is what makes it correctable
  by a full replay after a bug fix.
- **Serving layer.** A store, typically a key-value or wide-column store
  optimized for fast random reads and bulk writes, that holds the current
  batch views and answers queries against them. It is written to only by the
  batch layer, in bulk, and is treated as read-only from the query path.
- **Speed layer.** A stream processing component that consumes the same
  events as they arrive, before the batch layer has absorbed them, and
  incrementally maintains real-time views covering only the window of data
  the batch layer has not yet processed. Unlike the batch layer, the speed
  layer updates its state incrementally rather than recomputing from
  scratch, which is what buys it low latency at the cost of being harder to
  correct after a bug.
- **Query merge.** The component, sometimes a thin layer in the application,
  sometimes folded into the serving layer's client library, that answers a
  query by combining the batch view with the speed layer's real-time view
  for the window not yet covered by batch, and discards the speed layer's
  state for a window the moment the batch layer's next run absorbs it.

## 6. ASCII structure diagram

```
                              +-------------------+
                 all events   |   Master Data Set  |
        raw ---------------->|  (append only log)  |
                              +----------+----------+
                                         |
                        +----------------+----------------+
                        |                                 |
                        v                                 v
             +--------------------+           +--------------------+
             |    Batch Layer      |           |    Speed Layer      |
             |  full recompute,    |           |  incremental,       |
             |  hours to run,      |           |  seconds of lag,    |
             |  perfectly correct  |           |  approximate        |
             +----------+----------+           +----------+----------+
                        |                                 |
                        v                                 v
             +--------------------+           +--------------------+
             |    Batch Views      |           |  Real-Time Views    |
             |  in the serving     |           |  in fast, mutable   |
             |  layer, bulk write  |           |  storage            |
             +----------+----------+           +----------+----------+
                        |                                 |
                        +----------------+----------------+
                                         |
                                         v
                              +--------------------+
                              |    Query Merge      |
                              |  batch view plus    |
                              |  the delta window    |
                              +----------+----------+
                                         |
                                         v
                                    application
```

## 7. Dynamics

Two clocks run against the same master data set at once, and the query path
reads from both.

```
time ---->

events:    e1  e2  e3  e4  e5  e6  e7  e8  e9  e10 e11 e12 ...

speed      [-- consumes e1..e12 as they arrive, updates ----]
layer:     [-- real-time view incrementally, seconds of lag -]

batch      [------ run N processes e1..e6 -------] result R(N)
layer:                                              published
                                            [------ run N+1 processes
                                             e1..e12 ----------] R(N+1)
                                                                 published

serving    ................R(N)....................R(N+1)........
layer:     (stale until          (updated in a single
            R(N) published)        bulk write, atomically
                                    swapped in)

query at   answer = R(N) (batch, covers e1..e6)
time T1:            + speed layer's view of e7..e12 (the delta
                       window batch has not yet absorbed)

query at   answer = R(N+1) (batch, now covers e1..e12)
time T2:             + speed layer's view of anything after e12
(after         (speed layer discards its state for e1..e12 the
 R(N+1) is       moment R(N+1) is published, because that window
 published)      is now covered by an authoritative batch answer)
```

The critical transition is the moment a new batch run is published. the
serving layer's bulk write is atomic from the query path's point of view, and
the speed layer's expiry of the window that batch has now absorbed is what
keeps the speed layer's storage bounded, because it only ever holds the
delta since the last successful batch run, never the whole history.

## 8. Implementation variants

- **Marz's original stack.** Hadoop MapReduce for the batch layer, Storm for
  the speed layer, ElephantDB (a read-only, batch-loaded key-value store
  Marz also built) for the batch-view half of the serving layer, and
  Cassandra for the incrementally-updatable speed-view half. This is the
  concrete stack described across *Big Data*, Manning, 2015, and it is the
  variant most early adopters reproduced with substitutions.
- **Spark unified variant.** Apache Spark's batch API and Spark Structured
  Streaming API share a single engine and a largely shared programming
  model, which lets a team write one transformation and run it in both a
  batch job and a micro-batch streaming job against the same code, closing
  much of the dual-codebase gap the pattern is criticized for, though the
  two execution paths still have different failure and latency
  characteristics and are still deployed and monitored separately.
- **Cloud-managed variant.** A batch layer built from a data warehouse's own
  scheduled query engine (for example a nightly transformation job) paired
  with a managed stream processor (for example a cloud provider's streaming
  SQL or Flink-as-a-service offering), writing both outputs into the same
  analytical store and relying on the store's own upsert semantics to do the
  merge, rather than building a bespoke query-merge layer.
- **Serving-layer-only merge versus application-side merge.** Some
  implementations push the batch and speed views into the same physical
  table, keyed so that a newer speed-layer row for the same key overwrites
  an older batch-layer row, letting a plain point read do the merge. Others
  keep the two views in separate stores and merge explicitly in the
  application or an API gateway. The former is simpler to query but couples
  the write schema of two very different write patterns into one table.
- **Reprocessing trigger variants.** Some implementations recompute the
  batch layer on a fixed schedule regardless of whether logic changed.
  Others trigger a batch recompute only when the transformation code
  changes, treating the scheduled runs as incremental extensions of the
  batch view rather than full historical replays, which reduces cost but
  narrows the pattern's core promise that any bug is fully correctable by
  a complete replay.

## 9. Known production uses

- **Twitter, via the BackType analytics platform.** Nathan Marz built the
  original batch/realtime architecture that became Lambda Architecture while
  leading the analytics team at BackType, which Twitter acquired in 2011,
  and he is credited across both the pattern's own Wikipedia entry and his
  publisher's listing as both the creator of Apache Storm and the
  originator of the pattern
  ([Manning, Big Data by Nathan Marz and James Warren](https://www.manning.com/books/big-data),
  verified 2026-08-02).
- **Yahoo, via Storm-on-YARN.** Yahoo built and open-sourced storm-yarn, a
  project enabling Storm streaming and micro-batch applications to run
  alongside Hadoop batch applications on the same YARN-managed cluster, the
  explicit combination of a Hadoop batch layer and a Storm speed layer that
  defines this pattern's canonical stack, described in Yahoo's own project
  repository
  ([github.com/yahoo/storm-yarn](https://github.com/yahoo/storm-yarn),
  verified 2026-08-02).
- **Netflix, in its earlier content-discovery and playback analytics
  pipeline.** Netflix engineer Daniel Bryant documented, in an InfoQ article
  dated 8 February 2018, that Netflix's original pipeline for this workload
  ran batch-style ETL over HDFS and Amazon S3 using Spark, Pig, Hive, and
  Hadoop, that this batch-only approach carried more than 24 hours of
  analysis latency, and that Netflix evaluated and ultimately moved away
  from a full Lambda Architecture toward a Kafka-and-Flink streaming-only
  pipeline specifically to avoid maintaining the dual batch and speed
  codebases the pattern requires
  ([Daniel Bryant, Migrating Batch ETL to Stream Processing, InfoQ, 8 February 2018](https://www.infoq.com/articles/netflix-migrating-stream-processing/),
  verified 2026-08-02). Netflix's own trajectory, adopting the batch half
  early, considering the full lambda split, and then consolidating to a
  single streaming path, is itself a documented data point in the debate
  covered in dimension 13.

## 10. Consequences

Positive.

- A bug in the transformation logic is recoverable by recomputing the batch
  view from the immutable master data set, rather than by trying to patch a
  running, stateful aggregate whose history of intermediate states is gone.
- The system tolerates human error, not only machine failure, because the
  raw events are never overwritten and a wrong deploy can always be
  corrected by a full replay against a fixed input.
- Read latency for most queries is low, because the serving layer answers
  from a precomputed view rather than scanning raw events on every read.
- The speed layer's blast radius is small. because its state only ever
  covers the delta window since the last batch run, a bug in the streaming
  code corrupts at most a few hours or minutes of the answer, and the next
  batch run silently erases the damage.

Negative.

- Every piece of business logic that needs both an eventually correct
  historical answer and a fresh recent answer must be implemented twice,
  once in the batch engine's idiom and once in the stream engine's idiom,
  and the two implementations drift the moment one is patched without the
  other.
- The operational surface roughly doubles. two schedulers, two sets of
  failure modes, two on-call runbooks, and two places a metric can silently
  stop updating.
- Storing the full, immutable event history indefinitely is a real and
  growing storage cost, paid up front for a recomputation capability the
  team may only exercise a handful of times a year.
- The query-merge step is a new piece of custom logic with its own
  correctness bar, deciding exactly which window belongs to speed and which
  to batch, and getting the boundary wrong produces either a gap (data
  neither view covers) or a double count (data both views cover).

## 11. Failure modes and misuse

Judgement, drawn from the pattern's own well documented criticism history
and from common implementation mistakes described across production
write-ups, not sourced fact for every line.

- **Symptom.** Two dashboards, one fed by the batch view and one fed by the
  speed layer, disagree by a growing amount over weeks, not because either
  is wrong today but because nobody re-derives the streaming aggregation
  logic when the batch logic changes. **Cause.** the two implementations of
  the same business rule were built once and never kept in lockstep, which
  is exactly the maintenance burden Jay Kreps identified as the pattern's
  central weakness. **Fix.** treat the transformation logic as a single
  specification with two backends where the engine supports it (the Spark
  unified variant in dimension 8), or add an automated reconciliation job
  that periodically diffs speed-layer output against the next batch run and
  alerts on drift rather than trusting the two to agree.
- **Symptom.** The serving layer's data appears to jump backward, a number
  that was higher a moment ago reads lower after a batch run publishes.
  **Cause.** the query-merge boundary was implemented incorrectly, so the
  new batch view does not yet include a window the speed layer had already
  reported on, and the speed layer's state for that window was expired
  before the batch view that should have replaced it was actually live.
  **Fix.** make the swap of the batch view and the expiry of the
  corresponding speed-layer window a single atomic operation, never two
  separate steps that can be observed mid-transition by a concurrent query.
- **Symptom.** The speed layer's storage grows without bound and eventually
  falls over. **Cause.** the speed layer was built to accumulate state
  forever instead of only for the delta window since the last batch run,
  which is a common mistake when a team reuses a general-purpose streaming
  aggregation library without adding the explicit expiry step the pattern
  requires. **Fix.** the speed layer must actively discard state for any
  window the batch layer has absorbed, on every batch publish, not merely
  rely on the store's own retention or TTL settings, which are tuned for a
  different purpose and will not align with batch-run boundaries.
- **Symptom.** A team adopts the full pattern for a workload that turns out
  to need only current numbers, and the second codebase sits unmaintained
  within a year, quietly diverging until someone deletes it. **Cause.**
  the applicability check in dimension 4 was skipped, and correctness
  auditability was assumed to matter without confirming a real requirement
  for it. **Fix.** confirm the recomputation and audit requirement before
  building the batch half at all, and default to a single streaming path
  (dimension 13) when that requirement is not real.

## 12. Trade-off matrix

| Force | Lambda Architecture | Kappa Architecture | Batch-only pipeline |
|---|---|---|---|
| Correctness after a logic bug | High. full replay from the immutable master data set corrects any past miscalculation | Medium to high. replay is possible from a log with sufficient retention, but only if the retention window covers the needed history | High while the job is correct, but a bug is corrected by rerunning the same single batch path, no separate fast path exists to expose the gap sooner |
| Query freshness | Seconds to minutes, via the speed layer | Seconds to minutes, via the single streaming path | Hours, bound to the batch schedule |
| Codebases to maintain for one transformation | Two, batch and stream, unless a unified engine narrows the gap | One | One |
| Operational surface | Two schedulers, two failure domains | One processing system, plus log retention management | One scheduler, simplest to operate |
| Storage cost | High, an immutable full history plus two sets of derived views | High, a long-retention log plus one set of derived views | Moderate, raw data retention driven by the batch job's own needs, no permanent event log required |
| Best fit | Audit-critical, high-volume systems that also need low latency and where the team can staff two runtime paradigms | Systems needing both freshness and eventual correctness, on a single, sufficiently capable stream engine | Systems where daily or hourly freshness is genuinely acceptable |

## 13. Related and incompatible patterns

Lambda Architecture composes with **CQRS**, because the batch layer and the
speed layer are, in effect, two different write-side derivations feeding one
read-optimized model, and the query-merge step is exactly the read-side
responsibility CQRS names explicitly. It also composes with **Event
Sourcing**, because the immutable master data set the batch layer replays
from is a specific instance of an event-sourced log, and a system already
built around Event Sourcing has most of the master data set's requirements
satisfied before Lambda Architecture is even considered. It relates to
**Materialized View**, because both the batch view and the real-time view
are materialized views over the same underlying events, differing only in
how they are kept up to date, full recomputation versus incremental update.

**Kappa Architecture is the named, direct alternative, and is marked
incompatible with this pattern** because the two disagree on the central
structural question, whether a system needs two separate processing paths at
all. Jay Kreps proposed Kappa Architecture specifically as a response to
Lambda Architecture's dual-codebase cost, keeping a single stream processing
path against a log with sufficiently long retention, and replaying the
stream itself, rather than a separate batch engine, when a full recompute is
needed
([Jay Kreps, Questioning the Lambda Architecture, O'Reilly Radar, 2 July 2014](https://www.oreilly.com/radar/questioning-the-lambda-architecture/),
verified 2026-08-02). A single system does not run both patterns for the
same workload at once, because Kappa Architecture's entire premise is that
the second, batch path is unnecessary. Choosing between the two is a
dimension 4 applicability decision, not a matter of composing them.

It is worth recording, as part of this pattern's own lineage, that Nathan
Marz has himself written, on his personal site, that later systems he
worked on moved away from the two-codebase split where a single engine could
serve both roles, which softens the disagreement with Kreps into a question
of which processing engines were available at the time each system was
built rather than a permanent architectural stance
([Wikipedia, Lambda architecture](https://en.wikipedia.org/wiki/Lambda_architecture),
verified 2026-08-02, summarizing the documented positions of both Marz and
Kreps).

## 14. Refactoring path in and out

Introducing the pattern into a system that currently has only a batch
pipeline. First, stop deleting raw events after they are consumed. establish
an append-only master data set, even if the existing batch job keeps reading
from wherever it already reads, because nothing else in this refactor works
without an immutable history to replay from. Second, stand up the speed
layer against the same event source used to feed the master data set,
computing only the specific views that have a real freshness requirement,
never the whole batch job's output surface, to keep the second codebase as
small as the actual need. Third, add the query-merge step at the read path,
starting with the boundary logic described in dimension 6, and instrument
it so a gap or a double count between the two views is caught by a metric
rather than a support ticket. Fourth, once the speed layer is trusted, widen
its coverage only as specific new freshness requirements appear, resisting
the urge to make the speed layer a general mirror of the batch layer.

Introducing the pattern into a system that currently has only a streaming
pipeline. First, establish the immutable master data set if the streaming
system does not already retain its own input durably, because the point of
adding a batch layer is the ability to recompute from scratch, which is
worthless without a durable, complete input. Second, build the batch layer
against that master data set, computing the same views the speed layer
already produces, and run it in shadow, writing to a separate table, before
it is trusted to feed the serving layer. Third, once the batch layer's
output is verified to agree with a manually audited sample of the streaming
output, cut the serving layer over to read the batch view as authoritative
and narrow the streaming layer's job to the delta window only.

Removing the pattern, when the applicability check in dimension 4 no longer
holds, most often when a single stream engine capable of both roles becomes
available or when the correctness-audit requirement that justified the
batch half turns out not to be real. Confirm first that the retention window
on the streaming system's input log is long enough to satisfy the same
replay requirement the batch layer used to provide, then migrate the batch
layer's transformation logic into the streaming engine as a reprocessing job
against that retained log (the Kappa Architecture path described in
dimension 13), verify the reprocessed output against the last several known
batch results, and only then decommission the separate batch scheduler and
its dedicated compute.

## 15. Testing and verification

The batch layer is the easier half to test, because it is a pure function
of an immutable input. a unit test can construct a small, fixed slice of the
master data set, run the batch transformation against it, and assert on the
exact output, with no timing, ordering, or concurrency concerns to account
for. Property-based testing fits the batch layer well. generate arbitrary
sequences of input events and assert invariants that must hold regardless of
event order, since a correct batch layer's output should not depend on the
order events were originally ingested in, only on the set of events present.

The speed layer is harder, because its correctness is a function of timing
and incremental state, not only of input. Test doubles for the message
source (an in-memory queue standing in for the real streaming platform) let
a test drive a specific sequence and timing of events without a live
cluster. The most valuable test for the speed layer is not a unit test of
its aggregation logic in isolation, but a reconciliation test that runs the
same input through both the batch and speed implementations and asserts
their outputs converge once the batch layer has absorbed the same window,
because this is precisely the invariant a production drift bug (dimension
11) violates silently.

The query-merge boundary needs its own explicit test suite, asserting three
cases separately. a query for a window fully covered by a batch view, a
query for a window fully covered by the speed layer's delta, and a query
spanning the boundary between the two, checking that no event is counted by
neither view (a gap) and no event is counted by both (a double count).

## 16. Observability signals

A healthy instance of this pattern shows a batch layer completing on a
predictable schedule with a stable run duration, a speed layer whose lag
behind the live event stream stays within a known small bound, typically
seconds to low minutes, and a reconciliation metric comparing the speed
layer's rolling output against the next batch run's output for the same
window, staying near zero.

Signals to log and alert on. batch job start and completion time, and the
size of the input it processed, to catch a batch run that silently skipped
data. speed layer consumer lag, the gap between the latest event ingested
and the latest event the speed layer has incorporated, because a growing lag
means the speed layer is falling behind and the delta window it is
responsible for is silently expanding past what it can accurately compute.
the reconciliation diff between batch and speed for the same window, logged
on every batch publish, which is the single most direct signal that the two
codebases have drifted apart (dimension 11). and the age of the master data
set's oldest retained event relative to the retention policy, because a
replay-based recovery is only possible for data still present.

A failing instance shows one or more of these going wrong quietly rather
than loudly. the reconciliation diff creeping upward over weeks without
crossing any single alert threshold, a speed layer whose consumer lag rises
gradually as event volume grows past what its current resource allocation
can keep up with, or a batch job whose run duration grows until it no longer
finishes before the next scheduled run starts, silently skipping a cycle.

## 17. Security and privacy implications

This is a dimension where the implication is analytical, not sourced from a
named incident.

Retaining a complete, immutable, append-only history of every raw event a
system has ever received is the pattern's central mechanism, and it is also
a direct expansion of the system's data retention footprint and its exposure
under data protection law. A right-to-erasure request under a regime like
the GDPR is structurally at odds with an immutable master data set, because
the pattern's whole recoverability story depends on never deleting or
mutating a past event, while erasure requires exactly that. Systems adopting
this pattern for data containing personal information need an explicit
design for erasure that does not depend on deleting from the master data
set directly, commonly a separate mapping from a person's identifier to a
tombstone applied at read time in the batch and speed views, or a
cryptographic erasure scheme where each subject's events are encrypted with
a key that can be destroyed independently of the event bytes themselves.

The batch layer's full recompute capability is also an access-control
surface. because it reads the entire historical master data set on every
run, any process with the batch layer's read credentials has, by
construction, access to the full history of every event the system has ever
recorded, which is a materially larger blast radius than a streaming
component that only ever sees a rolling window of recent events. Access
control and audit logging on the batch layer's credentials deserve the same
scrutiny given to the master data set itself, not the lighter scrutiny a
component touching only recent data might otherwise receive.

## 18. References

- Nathan Marz and James Warren, *Big Data*, Manning, 2015.
- Manning Publications, book listing for *Big Data* by Nathan Marz and
  James Warren, https://www.manning.com/books/big-data, verified 2026-08-02.
- Wikipedia, "Lambda architecture",
  https://en.wikipedia.org/wiki/Lambda_architecture, verified 2026-08-02.
- Jay Kreps, "Questioning the Lambda Architecture", O'Reilly Radar,
  2 July 2014,
  https://www.oreilly.com/radar/questioning-the-lambda-architecture/,
  verified 2026-08-02.
- Yahoo, storm-yarn project repository,
  https://github.com/yahoo/storm-yarn, verified 2026-08-02.
- Daniel Bryant, "Migrating Batch ETL to Stream Processing. A Netflix Case
  Study with Kafka and Flink", InfoQ, 8 February 2018,
  https://www.infoq.com/articles/netflix-migrating-stream-processing/,
  verified 2026-08-02.

## Code examples

The batch layer, the speed layer, and the query-merge boundary are shown
below against a minimal shared example, counting page views per page id.
Each sample keeps a tiny in-memory master data set, computes a batch view by
folding over the whole set, maintains a speed-layer delta incrementally, and
merges the two at query time, discarding the speed layer's entry for a page
once the batch view covers it.

### TypeScript

```typescript
type ViewEvent = { pageId: string; ts: number };

class LambdaCounter {
  private masterLog: ViewEvent[] = [];
  private batchView = new Map<string, number>();
  private batchWatermark = -1;
  private speedView = new Map<string, number>();

  ingest(e: ViewEvent): void {
    this.masterLog.push(e);
    this.speedView.set(e.pageId, (this.speedView.get(e.pageId) ?? 0) + 1);
  }

  runBatch(): void {
    const view = new Map<string, number>();
    for (const e of this.masterLog) {
      view.set(e.pageId, (view.get(e.pageId) ?? 0) + 1);
    }
    this.batchView = view;
    this.batchWatermark = this.masterLog.length - 1;
    this.speedView.clear();
    for (let i = this.batchWatermark + 1; i < this.masterLog.length; i++) {
      const e = this.masterLog[i];
      this.speedView.set(e.pageId, (this.speedView.get(e.pageId) ?? 0) + 1);
    }
  }

  query(pageId: string): number {
    const fromBatch = this.batchView.get(pageId) ?? 0;
    const fromSpeed = this.speedView.get(pageId) ?? 0;
    return fromBatch + fromSpeed;
  }
}

const c = new LambdaCounter();
c.ingest({ pageId: "home", ts: 1 });
c.ingest({ pageId: "home", ts: 2 });
c.runBatch();
c.ingest({ pageId: "home", ts: 3 });
console.log(c.query("home"));
```

Run with `npx tsx` or compile with `npx tsc --strict`. The output is `3`, two
counted by the batch view published after the first run and one held in the
speed layer's delta since that run.

### Python

```python
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class Event:
    page_id: str
    ts: int


class LambdaCounter:
    def __init__(self) -> None:
        self.master_log: list[Event] = []
        self.batch_view: dict[str, int] = {}
        self.batch_watermark = -1
        self.speed_view: dict[str, int] = defaultdict(int)

    def ingest(self, e: Event) -> None:
        self.master_log.append(e)
        self.speed_view[e.page_id] += 1

    def run_batch(self) -> None:
        view: dict[str, int] = defaultdict(int)
        for e in self.master_log:
            view[e.page_id] += 1
        self.batch_view = dict(view)
        self.batch_watermark = len(self.master_log) - 1
        self.speed_view = defaultdict(int)
        for e in self.master_log[self.batch_watermark + 1:]:
            self.speed_view[e.page_id] += 1

    def query(self, page_id: str) -> int:
        return self.batch_view.get(page_id, 0) + self.speed_view.get(page_id, 0)


if __name__ == "__main__":
    c = LambdaCounter()
    c.ingest(Event("home", 1))
    c.ingest(Event("home", 2))
    c.run_batch()
    c.ingest(Event("home", 3))
    print(c.query("home"))
```

Run with `python3 lambda_counter.py`. It prints `3`, the same result as the
TypeScript sample, confirming both implementations of the same query-merge
boundary agree.

### Go

```go
package main

import "fmt"

type Event struct {
	PageID string
	TS     int
}

type LambdaCounter struct {
	masterLog      []Event
	batchView      map[string]int
	batchWatermark int
	speedView      map[string]int
}

func NewLambdaCounter() *LambdaCounter {
	return &LambdaCounter{
		batchView:      make(map[string]int),
		batchWatermark: -1,
		speedView:      make(map[string]int),
	}
}

func (c *LambdaCounter) Ingest(e Event) {
	c.masterLog = append(c.masterLog, e)
	c.speedView[e.PageID]++
}

func (c *LambdaCounter) RunBatch() {
	view := make(map[string]int)
	for _, e := range c.masterLog {
		view[e.PageID]++
	}
	c.batchView = view
	c.batchWatermark = len(c.masterLog) - 1
	c.speedView = make(map[string]int)
	for _, e := range c.masterLog[c.batchWatermark+1:] {
		c.speedView[e.PageID]++
	}
}

func (c *LambdaCounter) Query(pageID string) int {
	return c.batchView[pageID] + c.speedView[pageID]
}

func main() {
	c := NewLambdaCounter()
	c.Ingest(Event{PageID: "home", TS: 1})
	c.Ingest(Event{PageID: "home", TS: 2})
	c.RunBatch()
	c.Ingest(Event{PageID: "home", TS: 3})
	fmt.Println(c.Query("home"))
}
```

Run with `go run lambda_counter.go`. It prints `3`.

Rust and Java were not used for this entry. The pattern here is a data
processing topology and a merge rule, not a language-idiomatic construct like
a closure replacing a class, so a fourth or fifth language would repeat the
same three collections and one loop shown above without adding anything a
reader could not already see in the three samples given, and effort was spent
on live-verified citations and the observability, security, and testing
dimensions instead.
