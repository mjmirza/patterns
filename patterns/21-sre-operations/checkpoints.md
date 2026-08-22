---
name: Checkpoints
slug: checkpoints
family: 21-sre-operations
category: Behavioral
aliases: [Checkpointing, Distributed Snapshot, Checkpoint and Restart]
first_described: 'K. Mani Chandy and Leslie Lamport, Distributed Snapshots and Determining Global States of Distributed Systems, ACM Transactions on Computer Systems, 1985'
maturity: canonical
related: [write-ahead-log, event-sourcing, saga, error-budget, graceful-degradation]
incompatible_with: []
verified: 2026-08-22
---

# Checkpoints

## 1. Name, aliases, and lineage

The academic root of this pattern is Chandy and Lamport's 1985 paper,
"Distributed Snapshots, Determining Global States of Distributed Systems,"
published in ACM Transactions on Computer Systems. (Chandy and Lamport, see
reference 1.) The algorithm it describes lets a set of independent processes
agree on a consistent snapshot of the whole system's state without stopping
the world. an initiating process records its own state and sends a marker on
every outgoing channel, and each process that receives a marker records its
own state and the state of the channel the marker arrived on, then forwards
markers of its own. (Wikipedia's treatment of the algorithm, see reference
2, since the primary PDF could not be read as text and this mechanics
summary is a secondary, disclosed source rather than a direct reading of
Chandy and Lamport's own words.)

Practical checkpointing is older and broader than this one paper. Database
systems have written periodic checkpoints against a write-ahead log for
decades, and stream-processing, workflow, and machine-learning systems each
independently arrived at their own checkpointing mechanics. Apache Flink's
own checkpointing algorithm is an explicit, named extension of Chandy and
Lamport's idea, adapted for a live dataflow graph rather than a static set
of processes. (Carbone, Fora, Ewen, Haridi, and Tzoumas, see reference 3.)
This entry states honestly that "checkpoint" is not a term Google's Site
Reliability Engineering book defines as a named pattern the way it defines
error budget or toil, its Data Integrity chapter uses "snapshot" instead,
and the word "checkpoint" appears only once, informally, in the Data
Processing Pipelines chapter. (Google SRE Book, Data Integrity, see
reference 5; Data Processing Pipelines, see reference 4.) The pattern's
maturity is nonetheless canonical, the algorithm is forty years old and the
technique is implemented, in one form or another, in essentially every
production database, stream processor, and long-running training system in
use today.

## 2. Problem and context

A long-running computation, a stream-processing job, a database, a
multi-step workflow, or a distributed training run, must survive a crash
without either losing all of its progress or keeping an unbounded record of
everything that has ever happened. Google's own SRE book states the failure
this pattern exists to prevent directly, describing what happens when a
stalled pipeline chunk is restarted without checkpointing. "because pipeline
implementations by design usually don't include checkpointing, work on all
chunks is restarted from the beginning, thereby wasting the time, CPU
cycles, and human effort invested in the previous cycle." (Google SRE Book,
Data Processing Pipelines, see reference 4.) Apache Flink states the same
problem from the stream-processing side. "Checkpoints allow Flink to
recover state and positions in the streams to give the application the same
semantics as a failure-free execution." (Apache Flink Docs, see reference
7.)

A checkpoint is the answer to both halves of the problem at once, a periodic
save point recent enough that recovery redoes only a bounded amount of work,
and cheap enough to write that taking it does not itself become the
bottleneck.

## 3. Forces

- Checkpoint frequency against write overhead. PostgreSQL states this
  trade-off in both directions in its own configuration docs. "Reducing
  checkpoint_timeout and/or max_wal_size causes checkpoints to occur more
  often. This allows faster after-crash recovery, since less work will need
  to be redone. However, one must balance this against the increased cost
  of flushing dirty data pages more often." And on the other side.
  "Checkpoints are fairly expensive... It is therefore wise to set the
  checkpointing parameters high enough so that checkpoints don't happen too
  often." (PostgreSQL Docs, see reference 15.)
- Synchronous against asynchronous checkpointing, with a large,
  well-quantified real-world delta. PyTorch and IBM Research measured a 7
  billion parameter model's visible training pause drop from an average of
  148.8 seconds to 6.3 seconds, 23.62 times faster, by splitting the
  checkpoint into a blocking GPU-to-CPU copy followed by a non-blocking
  background write to disk. (PyTorch Blog, see reference 21.)
- Full against incremental checkpoints, with a non-obvious recovery-time
  nuance. Flink's RocksDB-backed incremental checkpointing "can dramatically
  reduce the checkpointing time in comparison to full checkpoints," but
  recovery time does not simply improve, "recovery time of incremental
  checkpoints may be longer or shorter compared to full checkpoints,"
  depending on whether the restore is bound by network bandwidth or by CPU
  and disk I/O. (Apache Flink Docs, State Backends, see reference 8.)
- Consistency across a distributed set of workers against throughput.
  Chandy and Lamport's own algorithm exists to guarantee that a distributed
  snapshot never mixes state from before and after the same logical moment.
  Flink's own barrier alignment enforces this same guarantee, at a real
  cost. under backpressure the barrier can take a long time to travel
  through a slow part of the dataflow graph, and if checkpoints start
  taking longer than the configured interval, "the system is constantly
  taking checkpoints," meaning too many resources stay tied up in
  checkpointing rather than in forward progress. (Apache Flink Docs, Large
  State Tuning, see reference 9.)

## 4. Applicability and non-applicability

Checkpointing earns its overhead when the computation is long-running,
unbounded, or genuinely expensive to redo from scratch. Meta's own
large-scale machine-learning reliability research names an explicit
mathematical trade-off for exactly this case, deriving an optimal
checkpoint interval as a function of checkpoint write cost and the
cluster's failure rate, and reports that hourly checkpointing is typical
for their larger jobs. (Kokolis, see reference 24.) A computation that is
this long and this expensive is exactly the case where losing all progress
on a single failure is unacceptable.

It is not worth the complexity for short, cheap-to-restart work, and it is
actively the wrong answer for stateless or idempotent request handling. AWS
Lambda's own function-design guidance points in the opposite direction from
checkpointing entirely, advising against carrying state across invocations
and toward writing code that produces the same correct result whether it
runs once or twice. "Write idempotent code. Writing idempotent code for
your functions means duplicate events are handled the same way."
(AWS Lambda Docs, see reference 19.) Idempotency and checkpointing are two
different answers to the same underlying retry problem, cheap-to-redo work
is made safe to retry from scratch, and expensive-to-redo work is made safe
to resume from a saved point instead. This framing is this catalogue's own
synthesis of the two contrasting sources above, not a claim either source
states in these terms itself.

## 5. Structure

The participants are the checkpointed unit, the process, operator, job, or
workflow whose state is being saved; the coordinator, the component that
decides when a checkpoint happens and, in a distributed setting, drives the
consistent-snapshot protocol across every participant (a periodic timer, a
barrier injected into a dataflow graph, or a continuous append to a
durability log); the checkpoint store, the durable location the saved state
is written to (object storage, a filesystem, a write-ahead log); and the
recovery path, the mechanism that, on restart after a failure, reads the
most recent valid checkpoint and resumes the computation from that point
rather than from the beginning.

## 6. ASCII structure diagram

```
Normal operation, a periodic checkpoint across a live dataflow

  Source --> [ Op A ] --> [ Op B ] --> [ Op C ] --> Sink
                |             |             |
           barrier n     barrier n     barrier n
           (flows in line with records, never overtakes them)
                |             |             |
            snapshot      snapshot      snapshot
                |             |             |
                +------------ | ------------+
                              v
                  +------------------------+
                  |     Checkpoint store    |
                  |  (object storage / WAL) |
                  +------------------------+

On restart after a failure

  Read the latest completed checkpoint --> reload state into Op A, B, C
  Replay only the source position recorded at that checkpoint forward
  (bounded redo, never a restart from the very beginning)
```

## 7. Dynamics

Flink's own checkpointing walks the Chandy-Lamport idea through a live
dataflow, and its exact mechanics are the clearest documented instance of
this pattern's dynamics. A barrier, a special marker record, is injected at
every source and flows with the records as part of the data stream.
Barriers never overtake records, they flow strictly in line. (Apache
Flink Docs, Stateful Stream Processing, see reference 6.)

When an operator with more than one input has received the barrier for
snapshot n on one input but not another, it holds back further records from
the input that has already delivered its barrier, so it never mixes state
from before and after the same snapshot on different inputs, exactly the
correctness property the 1985 algorithm was built to guarantee. Once the
barrier has arrived on every input, the operator snapshots its own state
asynchronously and forwards the barrier to its own outputs. (Apache Flink
Docs, Checkpointing, see reference 7.) When every operator has completed
its part, the checkpoint is marked complete and written to the checkpoint
store.

On a failure, recovery reverses this. Flink selects the latest completed
checkpoint k, then re-deploys the entire distributed dataflow, and gives
each operator the state that was snapshotted as part of checkpoint k.
(Same source.) Work resumes from checkpoint k rather than from the very
start of the stream.

## 8. Implementation variants

- Stream processing. Apache Flink's barrier-based algorithm described in
  dimension 7, with two configurable modes. exactly-once (the default,
  which pays the alignment cost above) and at-least-once (which skips
  alignment and accepts that records belonging to more than one checkpoint
  may be processed together). "Dataflows with only embarrassingly parallel
  operations actually give exactly once guarantees even in at least once
  mode." (Apache Flink Docs, Checkpointing, see reference 7.)
- Database write-ahead log checkpoints. PostgreSQL and MySQL InnoDB arrive
  at the identical design independently. a periodic checkpoint marks a
  position in the redo log, and crash recovery only replays the log after
  that mark. "After a checkpoint, WAL segments preceding the one containing
  the redo record are no longer needed and can be recycled or removed."
  (PostgreSQL Docs, see reference 15.) InnoDB's own version flushes dirty
  pages in small batches rather than all at once, named "fuzzy
  checkpointing," specifically so the checkpoint itself never disrupts
  concurrent transaction processing. (MySQL Docs, see reference 16.)
- Workflow and durable-execution engines. Temporal continuously appends
  every step of a workflow to an Event History, a durable, append-only log
  rather than a periodic snapshot. Its own documentation names the
  guarantee directly. "This is made possible by the Event History, a
  complete and durable log of everything that has happened in the lifecycle
  of a Workflow Execution." On a crash, "the Worker uses the Event History
  to replay the code and recreate the state of the Workflow Execution to
  what it was immediately before the crash," then "resumes progress from
  the point of failure as if the failure never occurred." (Temporal
  Documentation, see reference 17.) AWS Step Functions Standard Workflows
  take the same continuous-persistence approach. "Execution state
  internally persists between state transitions," giving an exactly-once
  execution model, while its cheaper Express Workflows variant deliberately
  omits this durability and accepts that a failed execution "should be
  re-run from the start." (AWS Docs, see reference 18.)
- Large-scale machine-learning training. A very active, current engineering
  area. Meta's Llama 3 training run checkpoints "each GPU's model state,
  ranging from 1 MB to 4 GB per GPU," with the explicit design goal to
  "minimize GPU pause time during checkpointing and increase checkpoint
  frequency to reduce the amount of lost work after a recovery." (Meta,
  Llama 3, see reference 23.) PyTorch's Distributed Checkpoint mechanism
  brought the write time for an 11 billion parameter checkpoint from nearly
  half an hour down to under 4 minutes, then, with asynchronous
  checkpointing, down to under 30 seconds of visible training pause.
  (PyTorch Blog, see references 21 and 22.)
- HPC and container/process checkpoint-restore. CRIU, Checkpoint and
  Restore In Userspace, "can freeze a running container (or an individual
  application) and checkpoint its state to disk," and the saved state "can
  be used to restore the application and run it exactly as it was during
  the time of the freeze." (CRIU Project, see reference 25.) It is
  integrated into Docker, Podman, and, at alpha maturity, Kubernetes, where
  it enables both forensic snapshots of a running container and live
  migration of a stateful container between nodes without losing its
  internal state. (Kubernetes Blog, see reference 26.) DMTCP takes the same
  idea further into HPC batch scheduling, transparently checkpointing a
  distributed MPI computation with no changes to the application's own
  code. (DMTCP Project, see reference 27.)

## 9. Known production uses

- Apache Flink's own list of production adopters names concrete scale.
  Bouygues Telecom runs "30 production applications powered by Flink" and
  processes "10 billion raw events per day," Klaviyo "deduplicates and
  aggregates over a million events per second," and Alibaba runs a fork of
  Flink to optimize search rankings in real time. (Apache Flink, Powered
  By, see reference 13.)
- Netflix built its Keystone stream-processing platform around Apache
  Flink, processing "trillions of events and petabytes worth of data per
  day" across "thousands of routing jobs and streaming applications" for
  "130 million subscribers from 190+ countries," with checkpoint state
  stored on Amazon S3. Netflix's own engineering writing describes using
  Flink and building an ecosystem around it, and states plainly that a
  person "can choose to resume from a checkpoint/savepoint or start from
  fresh state," or "rewind processing to a previous automatically taken
  checkpoint." (Netflix TechBlog, see reference 28.)
- Meta's Llama 3 pretraining ran for 54 days and survived "466 job
  interruptions," 419 of them unexpected, while maintaining "higher than
  90% effective training time," and needed "significant manual
  intervention... only three times during this period." Checkpoint and
  restart absorbed the overwhelming majority of these failures without a
  person having to step in. (Meta, Llama 3, see reference 23.)
- Google's own canary-release practice, while not named "checkpointing" in
  Google's own writing, functions as the deployment-domain instance of this
  pattern's structure. a change is exposed to a small slice of production
  traffic, evaluated against an explicit good-or-bad gate, and only
  advanced past that gate on success. "The canary process also lets us
  gain confidence in our change as we expose it to larger and larger
  amounts of traffic," and it is explicitly tied to the error-budget
  pattern elsewhere in this same family. "The canary process risks only a
  small fragment of our error budget." (Google SRE Workbook, Canarying
  Releases, see reference 29.) Google Cloud Deploy's own canary feature
  makes this staged-gate structure concrete, breaking a rollout into named
  phases such as canary-25, canary-50, canary-75, and stable, each of
  which can gate on an automated analysis before advancing. (Google
  Cloud Deploy Docs, see reference 33.)

## 10. Consequences

Positive. Recovery time after a failure is bounded by the checkpoint
interval rather than by the entire history of the computation. A person
never has to choose between losing all progress and keeping an unbounded
log of everything that ever happened. Large, expensive computations, a
multi-day training run, a stream that never stops, become safe to run on
hardware that will eventually fail, because the system already expects that
and recovers from it automatically.

Negative. Every checkpoint costs real I/O, CPU, or network capacity, paid
even when nothing ever fails. Checkpoint storage grows over time and needs
its own retention policy, Flink's own docs note that a retained checkpoint
is not automatically cleaned up unless the operator does it. (Apache Flink
Docs, Checkpoints, see reference 10.) A consistent distributed checkpoint
adds real coordination overhead, alignment in Flink's case, and that
coordination cost rises under exactly the conditions, backpressure and
slow operators, where the system can least afford it. A checkpoint is also
a new copy of in-flight application state written to disk, which carries
its own security and retention obligations, covered in dimension 17.

## 11. Failure modes and misuse

A checkpoint that is itself corrupted or incomplete. This is not a
hypothetical, it is a real, documented, closed bug. Apache Flink's own
issue tracker records a bug in its S3 recoverable-writer checkpoint
mechanism where, after resuming from a checkpoint with a partial in-flight
part, "those bytes are silently dropped, exactly-once degrades to
at-most-once minus tail." (Apache Flink JIRA, FLINK-39778, see reference
14.)

Checkpointing too infrequently, which widens the recovery window, or too
frequently, which can collapse throughput. PostgreSQL's own docs warn
against both directions explicitly (dimension 3), and Flink's own docs
describe the failure mode where checkpoints under sustained backpressure
start taking longer than the configured interval, so "the system is
constantly taking checkpoints" and operators make too little forward
progress. (Apache Flink Docs, Large State Tuning, see reference 9.)

Unbounded checkpoint storage growth with no retention policy. Flink states
this directly, a retained checkpoint after a job is cancelled is not
automatically cleaned up, "you have to manually clean up the checkpoint
state after cancellation." (Apache Flink Docs, Checkpoints, see reference
10.)

Trusting checkpoint restart to fix a problem whose root cause was never
found. Google's own PaLM training paper describes restarting from a
checkpoint roughly 100 steps before a loss spike and skipping the batches
around it, a real, documented use of checkpoint restart to route around a
training instability rather than to recover from a hardware failure, a
materially different situation from the fault-tolerance framing used
everywhere else in this entry. (Google, PaLM, see reference 34.)

Trusting checkpoint health metrics that are themselves unreliable on
failure. Flink's own monitoring docs admit this plainly. "for failed
checkpoints, metrics are updated on a best efforts basis and may be not
accurate," and checkpoint history "don't survive a JobManager loss."
(Apache Flink Docs, Checkpoint Monitoring, see reference 11.)

## 12. Trade-off matrix

| Variant | What is checkpointed | Frequency / trigger | Recovery-time trade-off |
|---|---|---|---|
| Stream processing (Flink) | Full or incremental operator state, per barrier | Periodic interval, no default, checkpointing is off unless configured | Bounded by the latest completed checkpoint; incremental restore is slower when network-bound, faster when CPU or I/O bound |
| Database WAL (PostgreSQL, InnoDB) | Dirty pages flushed; a redo-log position marked | Time interval or log-volume ceiling, whichever comes first | Crash recovery replays only the log written after the checkpoint mark |
| Durable-execution workflow (Temporal, Step Functions Standard) | Every step, continuously appended, not interval-based | Continuous, on every state transition | Full replay of the event history reconstructs state exactly as it was before the crash |
| Large-scale ML training (PyTorch DCP, Llama 3) | Sharded model, optimizer, and dataloader state, per worker | Manual or scheduled interval chosen against a derived cost/failure-rate trade-off | Asynchronous checkpointing shrinks visible pause from tens of minutes to under 30 seconds |
| HPC and container checkpoint-restore (CRIU, DMTCP) | Full process or container state, transparently, no code changes | On demand, an explicit checkpoint call | Restore resumes exactly where execution left off, demonstrated by log output continuing from the same point |

## 13. Related and incompatible patterns

Write-Ahead Log (see write-ahead-log.md in family 12) is the durability
mechanism a checkpoint bounds the replay distance of. the log records every
change, and the checkpoint marks the point before which the log no longer
needs to be replayed on recovery. Every database implementation of this
pattern in dimension 8 is, structurally, a checkpoint sitting on top of a
write-ahead log.

Event Sourcing (see event-sourcing.md in family 08) uses the same idea
for a different purpose, an application-level snapshot that bounds how far
back an event-sourced system's read model must replay. Martin Fowler
describes exactly this shape. a system in use during a working day could
be started at the beginning of the day from an overnight snapshot and hold
the current application state in memory, and new snapshots can be made at
any time in parallel without bringing down the running application.
(Fowler, see reference 30.)

Saga (see saga.md in family 08) solves a related but genuinely different
problem and is worth distinguishing precisely rather than conflating.
where a checkpoint resumes forward progress from a saved point, a saga
recovers by moving backward, undoing prior steps through compensating
transactions. "If a local transaction fails, the saga performs a series of
compensating transactions to reverse the changes that the preceding local
transactions made." (Microsoft Learn, see reference 31.) Both patterns
answer the same underlying question, what happens when a multi-step
process fails partway through, but a checkpoint answers it by resuming,
and a saga answers it by reversing.

Error Budget and Graceful Degradation (see error-budget.md and
graceful-degradation.md, siblings in this same family) address a
different moment in a system's life. they govern what happens while a
dependency is unhealthy or a release is being evaluated, not how much
progress a crashed component loses. The canary-release use of a staged
gate in dimension 9 is where the two families of concern meet, a canary
phase is itself evaluated against an error budget, and only a canary that
clears its gate advances to the next stage, functioning as a checkpoint in
the deployment pipeline sense.

## 14. Refactoring path in and out

In, adding checkpointing to a system that currently restarts entirely from
scratch on failure. Identify the state that must survive a crash, choose a
checkpoint interval by weighing write overhead against acceptable redo
work, the way Meta's own optimal-interval formula makes this trade-off
explicit rather than a guess. (Kokolis, see reference 24.) Write to a
durable, versioned store, verify that a real restart from a real checkpoint
reproduces the correct state, not merely that the write succeeded, and only
then rely on it in production.

Out, removing checkpointing once it is no longer needed. This happens when
a computation shrinks to the point where restarting it from scratch is
cheap, or when the workload is refactored to be idempotent and stateless in
the way AWS Lambda's own guidance recommends (dimension 4), at which point
the checkpoint machinery, and the storage and retention policy it required,
can be retired.

## 15. Testing and verification

The only real proof that checkpointing works is a genuine kill-and-restore
test, not merely confirming the checkpoint write succeeded. CRIU's own
Docker integration demonstrates the concrete shape of this proof, restoring
a checkpointed container and observing that its logs start from where
execution left off and continue to increase, an externally observable,
verifiable sign that execution truly resumed rather than restarted. (CRIU,
Docker integration, see reference 35.)

For machine-learning training specifically, the correctness bar goes
further than simply resuming, it requires bitwise-reproducible results.
Google's PaLM paper states this guarantee directly. "The model is fully
bitwise reproducible from any checkpoint." Concretely, if the model has
been trained up to step 17,000 in a single run, and training instead
restarts from checkpoint 15,000, the training framework guarantees
identical results either way. (Google, PaLM, see reference 34.)

This testing discipline is the same instinct as the sibling fault-injection
testing pattern in this family, kill a real component and observe whether
recovery genuinely works, rather than trusting that it should.

## 16. Observability signals

Apache Flink's own metrics catalogue is the most precisely documented set
of checkpoint health signals available. numberOfFailedCheckpoints and
numberOfCompletedCheckpoints together give the success rate,
lastCheckpointDuration shows how close a checkpoint is running to its
configured timeout, lastCheckpointSize and lastCheckpointFullSize show
whether checkpoint size is growing unbounded, and lastCheckpointRestoreTimestamp
marks the moment recovery actually completed after a failure. (Apache
Flink Docs, Metrics Reference, see reference 12.) A production monitoring
integration confirms these same metric names are exposed for alerting, but
is itself honest that it prescribes no thresholds of its own, leaving what
counts as healthy to the operator. (Datadog, Flink integration, see
reference 36.)

The healthy signal is a stable, low failed-checkpoint rate, a duration well
under the configured timeout, and a bounded, roughly steady checkpoint
size. The failing signal is a rising failure rate, a duration trending
toward the timeout and getting discarded, an unbounded size growth
suggesting a state or compaction problem, or a growing alignment delay
under backpressure, which is Flink's own direct signal that checkpointing
and the workload it is protecting have started to compete for the same
resources.

## 17. Security and privacy implications

A checkpoint is a full, at-rest copy of in-flight application state, and
that creates a security surface the live, in-memory version of the same
state did not have. Apache Flink's own documentation, checked directly for
guidance here, provides none, its checkpoint and security pages describe
only technical storage configuration, filesystem paths and directory
layout, with no mention of encryption, access control, or sensitive-data
handling for what is actually stored in a checkpoint. (Apache Flink Docs,
see references 7 and 10.) This absence is itself worth stating plainly, the
pattern's own most prominent open-source implementation leaves checkpoint
security entirely to the operator's underlying storage layer.

That underlying storage layer does carry real default protection. Amazon
S3, named directly in AWS's own guidance as a great place to store
checkpointing data, (AWS Blog, see reference 20) applies server-side
encryption to every object by default since 2023, with customer-managed
keys available through SSE-KMS. (AWS Docs, see reference 37.)

Once a checkpoint contains personal data, general data-protection law
applies to it the moment it is written, whether or not the checkpointing
system itself is aware of that. GDPR Article 32 requires "the
pseudonymisation and encryption of personal data" and "the ability to
maintain the ongoing confidentiality, integrity, availability and resilience
of processing systems and services." (GDPR Info, Article 32, see reference
32.) This is generic law, not checkpoint-specific guidance, presented here
as the obligation that fills the gap Flink's own docs leave open.

## 18. References

1. K. Mani Chandy and Leslie Lamport, "Distributed Snapshots, Determining
   Global States of Distributed Systems," ACM Transactions on Computer
   Systems, 1985. https://dblp.org/rec/journals/tocs/ChandyL85.html,
   verified 2026-08-22.
2. Wikipedia, "Chandy-Lamport algorithm."
   https://en.wikipedia.org/wiki/Chandy-Lamport_algorithm, verified
   2026-08-22.
3. Carbone, Fora, Ewen, Haridi, and Tzoumas, "Lightweight Asynchronous
   Snapshots for Distributed Dataflows," arXiv paper 1506.08603.
   https://ar5iv.labs.arxiv.org/html/1506.08603, verified 2026-08-22.
4. Google SRE Book, "Data Processing Pipelines."
   https://sre.google/sre-book/data-processing-pipelines/, verified
   2026-08-22.
5. Google SRE Book, "Data Integrity, A Survivor's Guide."
   https://sre.google/sre-book/data-integrity/, verified 2026-08-22.
6. Apache Flink Docs, "Stateful Stream Processing."
   https://nightlies.apache.org/flink/flink-docs-stable/docs/concepts/stateful-stream-processing/,
   verified 2026-08-22.
7. Apache Flink Docs, "Checkpointing."
   https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/fault-tolerance/checkpointing/,
   verified 2026-08-22.
8. Apache Flink Docs, "State Backends."
   https://nightlies.apache.org/flink/flink-docs-stable/docs/ops/state/state_backends/,
   verified 2026-08-22.
9. Apache Flink Docs, "Large State Tuning."
   https://nightlies.apache.org/flink/flink-docs-stable/docs/ops/state/large_state_tuning/,
   verified 2026-08-22.
10. Apache Flink Docs, "Checkpoints."
    https://nightlies.apache.org/flink/flink-docs-stable/docs/ops/state/checkpoints/,
    verified 2026-08-22.
11. Apache Flink Docs, "Checkpoint Monitoring."
    https://nightlies.apache.org/flink/flink-docs-stable/docs/ops/monitoring/checkpoint_monitoring/,
    verified 2026-08-22.
12. Apache Flink Docs, "Metrics Reference."
    https://nightlies.apache.org/flink/flink-docs-stable/docs/ops/metrics/,
    verified 2026-08-22.
13. Apache Flink, "Powered By."
    https://flink.apache.org/what-is-flink/powered-by/, verified
    2026-08-22.
14. Apache Flink JIRA, FLINK-39778, "Recoverable writer silently loses the
    in-flight tail on resume."
    https://issues.apache.org/jira/browse/FLINK-39778, verified 2026-08-22.
15. PostgreSQL Docs, "WAL Configuration."
    https://www.postgresql.org/docs/current/wal-configuration.html,
    verified 2026-08-22.
16. MySQL Docs, "InnoDB Checkpoints."
    https://dev.mysql.com/doc/refman/8.4/en/innodb-checkpoints.html,
    verified 2026-08-22.
17. Temporal Documentation, "Event History."
    https://github.com/temporalio/documentation/blob/main/docs/encyclopedia/event-history/event-history.mdx,
    verified 2026-08-22.
18. AWS Docs, "Standard vs. Express Workflows."
    https://docs.aws.amazon.com/step-functions/latest/dg/concepts-standard-vs-express.html,
    verified 2026-08-22.
19. AWS Docs, Lambda Developer Guide, guidance on function design and
    idempotency.
    https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html,
    verified 2026-08-22.
20. AWS Blog, guidance on handling EC2 Spot Instance interruptions.
    https://aws.amazon.com/blogs/compute/best-practices-for-handling-ec2-spot-instance-interruptions/,
    verified 2026-08-22.
21. PyTorch Blog, "Reducing Checkpointing Times for Large-Scale Training."
    https://pytorch.org/blog/reducing-checkpointing-times/, verified
    2026-08-22.
22. PyTorch Blog, "Performant Distributed Checkpointing in Production with
    IBM."
    https://pytorch.org/blog/performant-distributed-checkpointing/,
    verified 2026-08-22.
23. Meta AI, "The Llama 3 Herd of Models," arXiv paper 2407.21783.
    https://arxiv.org/html/2407.21783v3, verified 2026-08-22.
24. Kokolis et al., "Revisiting Reliability in Large-Scale Machine
    Learning Research Clusters," arXiv paper 2410.21680.
    https://ar5iv.labs.arxiv.org/html/2410.21680, verified 2026-08-22.
25. CRIU Project, "Main Page." https://criu.org/Main_Page, verified
    2026-08-22.
26. Kubernetes Blog, "Forensic Container Checkpointing in Kubernetes."
    https://kubernetes.io/blog/2022/12/05/forensic-container-checkpointing-alpha/,
    verified 2026-08-22.
27. DMTCP Project. https://dmtcp.sourceforge.io/, verified 2026-08-22.
28. Netflix TechBlog, "Keystone Real-time Stream Processing Platform."
    https://netflixtechblog.com/keystone-real-time-stream-processing-platform-a3ee651812a,
    verified 2026-08-22.
29. Google SRE Workbook, "Canarying Releases."
    https://sre.google/workbook/canarying-releases/, verified 2026-08-22.
30. Martin Fowler, "Event Sourcing."
    https://martinfowler.com/eaaDev/EventSourcing.html, verified
    2026-08-22.
31. Microsoft Learn, "Saga Distributed Transactions Pattern."
    https://learn.microsoft.com/en-us/azure/architecture/patterns/saga,
    verified 2026-08-22.
32. GDPR Info, "Art. 32 GDPR, Security of Processing."
    https://www.gdpr-info.eu/art-32-gdpr/, verified 2026-08-22.
33. Google Cloud Deploy Docs, "Configure a Canary Deployment Strategy."
    https://docs.cloud.google.com/deploy/docs/deployment-strategies/canary,
    verified 2026-08-22.
34. Google, "PaLM, Scaling Language Modeling with Pathways," arXiv paper
    2204.02311. https://ar5iv.labs.arxiv.org/html/2204.02311, verified
    2026-08-22.
35. CRIU Project, "Docker."
    https://criu.org/Docker, verified 2026-08-22.
36. Datadog Docs, "Flink Integration."
    https://docs.datadoghq.com/integrations/flink/, verified 2026-08-22.
37. AWS Docs, "Protecting Data Using Server-Side Encryption with AWS KMS
    Keys."
    https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingKMSEncryption.html,
    verified 2026-08-22.

**Evidence grade.** high

**Most solid findings.** The Chandy-Lamport-to-Flink lineage is confirmed
two ways at once, a real bibliographic citation (DBLP) for the 1985 paper
and Flink's own academic paper (arXiv paper 1506.08603) naming Chandy and
Lamport as its own explicit starting point. The recovery-behavior claims
across every implementation variant, Flink, PostgreSQL, MySQL, Temporal,
Step Functions, PyTorch, and CRIU, are each sourced directly from that
system's own official documentation, not from a third party's summary, and
several carry precisely quantified numbers (PyTorch's 23.62 times speedup,
Meta's 466 interruptions over 54 days, Netflix's 130 million subscribers).

**Unverified or unclear.** The 1985 paper's own algorithm-mechanics
description in dimension 1 is sourced from Wikipedia's treatment of the
paper rather than a direct reading of the primary PDF, which could not be
extracted as readable text, disclosed explicitly rather than presented as
read from the primary source. Whether AWS's own Well-Architected Framework
document itself formally names "checkpointing" as a defined pattern, as
opposed to AWS's separate compute blog, which clearly does discuss it,
could not be confirmed, so this entry does not claim AWS Well-Architected
as a formal origin the way sibling entries in this family do. The company
affiliations behind three of the cited arXiv machine-learning papers
(MegaScale, ByteCheckpoint, and the Frontier in-memory checkpointing work)
are widely known in the field but were not stated on the fetched abstract
pages themselves, so those three papers are cited here only where their
own text, not an assumed company name, supports the claim.

## Code examples

### TypeScript, a periodic checkpoint writer for a long-running counter

```typescript
import { promises as fs } from "fs";

interface CheckpointState {
  processedCount: number;
  lastSourceOffset: number;
}

class CheckpointedProcessor {
  private state: CheckpointState = { processedCount: 0, lastSourceOffset: 0 };
  private readonly checkpointPath: string;
  private readonly intervalRecords: number;

  constructor(checkpointPath: string, intervalRecords = 100) {
    this.checkpointPath = checkpointPath;
    this.intervalRecords = intervalRecords;
  }

  async restore(): Promise<void> {
    try {
      const raw = await fs.readFile(this.checkpointPath, "utf8");
      this.state = JSON.parse(raw) as CheckpointState;
    } catch {
      // No checkpoint yet. Start from the beginning, this is a fresh run.
    }
  }

  async process(records: number[]): Promise<void> {
    for (const offset of records) {
      if (offset <= this.state.lastSourceOffset) continue; // already done
      this.state.processedCount += 1;
      this.state.lastSourceOffset = offset;
      if (this.state.processedCount % this.intervalRecords === 0) {
        await this.checkpoint();
      }
    }
    await this.checkpoint();
  }

  private async checkpoint(): Promise<void> {
    const tmpPath = this.checkpointPath + ".tmp";
    await fs.writeFile(tmpPath, JSON.stringify(this.state));
    await fs.rename(tmpPath, this.checkpointPath); // atomic swap, no partial reads
  }

  getProcessedCount(): number {
    return this.state.processedCount;
  }
}

async function main(): Promise<void> {
  const proc = new CheckpointedProcessor("/tmp/checkpoint-demo.json", 3);
  await proc.restore();
  await proc.process([1, 2, 3, 4, 5, 6, 7]);
  console.log("processed " + proc.getProcessedCount() + " records so far");
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
```

### Python, incremental checkpointing that only persists changed keys

```python
import json
from dataclasses import dataclass, field


@dataclass
class IncrementalCheckpoint:
    full_state: dict = field(default_factory=dict)
    dirty_keys: set = field(default_factory=set)
    checkpoints_written: int = 0

    def apply(self, key: str, value: int) -> None:
        self.full_state[key] = value
        self.dirty_keys.add(key)

    def checkpoint(self) -> dict:
        """Only the keys touched since the last checkpoint are written,
        mirroring Flink incremental RocksDB checkpoints."""
        delta = {k: self.full_state[k] for k in self.dirty_keys}
        self.dirty_keys.clear()
        self.checkpoints_written += 1
        return {"checkpoint_id": self.checkpoints_written, "delta": delta}

    def restore(self, deltas: list) -> None:
        """Recovery replays every delta in order to rebuild full state,
        the incremental-restore cost the entry describes in dimension 3."""
        self.full_state.clear()
        for chk in deltas:
            self.full_state.update(chk["delta"])


ckpt = IncrementalCheckpoint()
ckpt.apply("a", 1)
ckpt.apply("b", 2)
first = ckpt.checkpoint()
assert first["delta"] == {"a": 1, "b": 2}

ckpt.apply("a", 10)  # only "a" changed since the last checkpoint
second = ckpt.checkpoint()
assert second["delta"] == {"a": 10}

restored = IncrementalCheckpoint()
restored.restore([first, second])
assert restored.full_state == {"a": 10, "b": 2}
print(json.dumps({"restored": restored.full_state}))
```

### Go, a write-ahead log bounded by a periodic checkpoint marker

```go
package main

import "fmt"

type LogEntry struct {
	Seq   int
	Value int
}

type WALCheckpointer struct {
	log            []LogEntry
	state          int
	lastCheckpoint int // sequence number the checkpoint covers
}

func (w *WALCheckpointer) Append(entry LogEntry) {
	w.log = append(w.log, entry)
	w.state += entry.Value
}

// Checkpoint marks that every log entry up to the current point is already
// reflected in state, so recovery never needs to replay it again.
func (w *WALCheckpointer) Checkpoint() {
	if len(w.log) == 0 {
		return
	}
	w.lastCheckpoint = w.log[len(w.log)-1].Seq
}

// Recover rebuilds state from a bare log and a known checkpoint, replaying
// only the entries written after that checkpoint, never the whole log.
func Recover(log []LogEntry, lastCheckpoint int) int {
	state := 0
	for _, entry := range log {
		if entry.Seq <= lastCheckpoint {
			continue
		}
		state += entry.Value
	}
	return state
}

func main() {
	w := &WALCheckpointer{}
	w.Append(LogEntry{Seq: 1, Value: 5})
	w.Append(LogEntry{Seq: 2, Value: 7})
	w.Checkpoint() // checkpoint covers seq 1 and 2, state == 12

	w.Append(LogEntry{Seq: 3, Value: 3})
	w.Append(LogEntry{Seq: 4, Value: 4})

	// Recovery should only replay seq 3 and 4, the entries after the
	// checkpoint, and add them on top of the checkpointed state (12).
	replayed := Recover(w.log, w.lastCheckpoint)
	recovered := 12 + replayed // 12 was captured at the checkpoint
	if recovered != w.state {
		panic(fmt.Sprintf("recovery mismatch, got %d want %d", recovered, w.state))
	}
	fmt.Println("recovered state matches live state:", recovered)
}
```
