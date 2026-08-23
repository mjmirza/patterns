---
name: Exactly-Once Processing
slug: exactly-once-processing
family: 24-stream-processing
category: Stream Processing
aliases: [Exactly-Once Semantics, EOS, Effectively-Once Processing]
first_described: "Akidau et al, MillWheel, VLDB 2013; formalized for Kafka in KIP-98, Exactly Once Delivery and Transactional Messaging"
maturity: canonical
related: [idempotent-consumer, idempotency-key, transactional-outbox, dead-letter-topic, stream-table-duality, replayable-log, watermark, event-time-processing]
incompatible_with: []
verified: 2026-08-23
---

# Exactly-Once Processing

## 1. Name, aliases, and lineage

Exactly-once processing is the guarantee that a stream processing pipeline
reflects each input record's effect exactly one time, even when the pipeline
retries after a failure. The clearest and earliest primary description of
this guarantee, and the specific limitation that comes with it, is Google's
MillWheel paper, "MillWheel. Fault-Tolerant Stream Processing at Internet
Scale," Akidau, Balikov, Bekiroglu, Chernyak, Haberman, Lax, McVeety, Mills,
Nordstrom, and Whittle, presented at VLDB 2013. Its motivation section states
this as a hard requirement, "The system should provide exactly-once delivery
of records," and its architecture section is explicit about scope, "All
internal updates within the MillWheel framework resulting from record
processing are atomically checkpointed per-key and records are delivered
exactly once. This guarantee does not extend to external systems." Section
6.1.1 of the paper, titled exactly "Exactly-Once Delivery," describes the
mechanism as at-least-once delivery with a deduplication pass layered on top,
"Deliveries in MillWheel are retried until they are ACKed in order to meet
our at-least-once requirement, which is a prerequisite for exactly-once."

Apache Kafka formalized the same guarantee for its own ecosystem in KIP-98,
"Exactly Once Delivery and Transactional Messaging," which shipped in Kafka
0.11.0. Its motivation states the gap it closes plainly, "Kafka currently
provides at least once semantics... Users of messaging systems greatly
benefit from the more stringent idempotent producer semantics, viz. Every
message write will be persisted exactly once, without duplicates and without
data loss, even in the event of client retries or broker failures."

The alternate term effectively-once circulates informally in the streaming
community to describe the same honest scoping the MillWheel paper states
directly, that the guarantee covers internal state and Kafka-to-Kafka or
checkpoint-aligned transfers, never an arbitrary external side effect. That
exact term could not be confirmed inside Google's own current Dataflow
documentation or the original 2015 Dataflow Model paper during this entry's
research, so it is presented here as informal community usage rather than a
directly sourced vendor term.

## 2. Problem and context

A stream processor that crashes mid-batch and restarts will, by default,
reprocess whatever it had not yet acknowledged. Under at-least-once delivery
this is correct but incomplete, the same record can now be processed twice,
and if the processing step increments a counter, charges a payment, or
aggregates a metric, that duplicate silently corrupts the result. The
MillWheel paper's own motivating example is a trend-detection pipeline,
Zeitgeist, where a duplicate delivery causes "spurious spikes" in the
aggregated output, and the paper states plainly that its revenue-processing
customers depend on this correctness rather than "reinventing their own
deduplication mechanism." Exactly-once processing exists to remove that
double-counting risk from the processing layer itself, rather than leaving
every consumer to build its own ad hoc deduplication.

## 3. Forces

**Correctness against throughput and latency.** Committing work transactionally
costs measurable throughput. A Confluent benchmark of Kafka's raw
transactional producer and consumer found, "for a producer producing 1KB
records at maximum throughput, committing messages every 100ms results in
only a 3% degradation in throughput," while "the transactional consumer
shows no degradation in throughput when reading transactional messages in
read_committed mode." The cost is higher once a processing framework layers
its own transaction cycle on top, a separate Confluent benchmark of Kafka
Streams found a commit interval of 100 ms produced "a throughput degradation
of 15% to 30% depending on the message size," though "a larger commit
interval of 30 seconds has no overhead at all for larger message sizes of 1
KB or higher."

**Scope against completeness.** The guarantee is only as strong as its
weakest hop. Apache Flink's own fault-tolerance documentation states this as
a hard requirement, "To achieve exactly once end-to-end, so that every event
from the sources affects the sinks exactly once... your sources must be
replayable, and your sinks must be transactional (or idempotent)." One
non-transactional hop anywhere in the pipeline breaks the end-to-end
guarantee even if every other hop is correctly configured.

**Internal guarantee against external side effects.** No framework's
exactly-once mechanism reaches an arbitrary external system by default. The
MillWheel paper states this directly, "This guarantee does not extend to
external systems," and Google's current Dataflow documentation makes the
identical scoping claim decades later, "Side effects are not guaranteed to
have exactly-once semantics. Importantly, this includes writing output to an
external store, unless the sink also implements exactly-once semantics," and
"If a transform makes a remote service call, that call might be made
multiple times for the same record." This is not a gap any framework has
closed, it is a structural limit, an external call is non-deterministic from
the framework's point of view and cannot be made transactional by the
framework alone.

## 4. Applicability and non-applicability

Reach for exactly-once processing when duplicate or lost events have a
direct correctness cost, financial counting, billing, and revenue reporting
being the clearest case, exactly the workload the MillWheel paper names its
own customer base around. Apache Pulsar's own transactions documentation
names the same category directly, "In the financial industry, financial
institutions use stream processing engines to process debits and credits for
users. This type of use case requires that every message is processed
exactly once, without exception."

Do not reach for it as a default. The throughput cost above is real, and a
pipeline whose final side effect is an external, non-idempotent call gets no
correctness benefit from an internally exactly-once processing layer, since
that side effect sits entirely outside the guarantee's scope. Netflix's own
Keystone pipeline is a documented example of a team choosing weaker
guarantees deliberately for cost reasons, describing an at-most-once producer
configuration and stating, "we've worked with teams that depend upon our
infrastructure to arrive at an acceptable amount of data loss, while
balancing cost." When the workload tolerates that trade, paying for
exactly-once buys nothing.

## 5. Structure

Kafka's transactional architecture, from KIP-98, assigns each transactional
producer a unique producer ID during initialization and a dedicated
transaction coordinator, "Similar to the consumer group coordinator, each
producer is assigned a transaction coordinator, and all the logic of
assigning PIDs and managing transactions is done by the transaction
coordinator." Every message a producer sends carries a per-partition
sequence number, "Every new producer will be assigned a unique PID during
initialization... For a given PID, sequence numbers will start from zero and
be monotonically increasing, with one sequence number per topic partition
produced to." The broker uses this sequence to reject duplicates and detect
loss, "The broker will reject a produce request if its sequence number is
not exactly one greater than the last committed message from that
PID/TopicPartition pair."

On the consuming side, a reader must opt into transaction awareness, "In the
default 'read_uncommitted' isolation level, all messages are visible to
consumers even if they were part of an aborted transaction, but in
'read_committed' isolation level, the consumer will only return messages
from transactions which were committed." A consumer downstream of a
transactional producer that stays on the default `read_uncommitted` level
sees uncommitted and eventually aborted data as if it were final, which
breaks the guarantee regardless of how correctly the producer side is
configured.

Flink's structural equivalent, for a checkpoint-coupled transactional sink,
is described by the `TwoPhaseCommitSinkFunction` base class contract, "a
recommended base class for all of the SinkFunction that intend to implement
exactly-once semantic," implementing "a two phase commit algorithm on top of
the CheckpointedFunction and CheckpointListener." Its lifecycle methods,
`beginTransaction`, `invoke` (write within the open transaction), `preCommit`
(triggered by an arriving checkpoint barrier), `commit` (only after every
operator has acknowledged the checkpoint), and `abort`, are the direct
structural counterpart to Kafka's producer, coordinator, and epoch. The newer
unified Sink API, proposed in FLIP-143 to "let the user develop sink once and
run it everywhere," splits the same responsibility into a per-subtask writer
and a separate committer role that performs the actual commit once every
writer has produced its committable state.

## 6. ASCII structure diagram

```
Source (must be replayable)
   |
   v
Processing operator  ---- checkpoint barrier flows through ---->
   | (at-least-once retry loop with per-key dedup, MillWheel style)
   v
Transactional sink (must be transactional, or idempotent)
   |
   beginTransaction() --> invoke()/write() --> preCommit() --> commit()
   |                                                 ^
   |                                                 |
   +------- gated on ALL operators acking the checkpoint -------+

   [ everything inside this box is covered by the guarantee ]
   [ an outbound API call, an email, a non-transactional store  ]
   [ triggered by processing sits OUTSIDE this box and is NOT   ]
   [ covered. "This guarantee does not extend to external       ]
   [ systems." MillWheel, section 3.                            ]
```

## 7. Dynamics

Kafka's transactional producer follows a fixed sequence. `initTransactions()`
must run first, and internally "[guarantees] any transactions initiated by
previous instances of the producer with the same transactional.id are
completed" and fetches the producer's current epoch, this is the moment a
zombie producer from an earlier session gets fenced. `beginTransaction()`
opens exactly one transaction at a time. `send()` calls write records that
are not visible to a `read_committed` consumer until the transaction
resolves. `sendOffsetsToTransaction()` binds the consumer group's offset
commit to the same transaction as the produced records, "typically in a
consume-transform-produce pattern," requiring the paired consumer to disable
auto-commit. `commitTransaction()` flushes and commits, or throws if any send
failed, in which case the transaction is not committed at all. A
`read_committed` consumer filters out anything from an aborted transaction
entirely.

Flink's equivalent sequence is driven by checkpointing rather than an
explicit API call sequence. A checkpoint barrier flows through the job graph,
and multi-input operators perform barrier alignment, "so that the snapshot
will reflect the state resulting from consuming events from both input
streams up to (but not past) both barriers." When the barrier reaches a
transactional sink configured with `DeliveryGuarantee.EXACTLY_ONCE`, the sink
pre-commits its buffered Kafka transaction, and the global commit only
happens once every operator has acknowledged the checkpoint. This coupling
between checkpoint interval and transaction lifetime creates a real
operational constraint, the Kafka producer's `transaction.timeout.ms` must
stay comfortably longer than the maximum checkpoint duration plus the
maximum restart duration, or Kafka can expire an open transaction before
Flink commits it, silently losing the buffered data.

Barrier alignment itself is optional and is exactly what a team gives up to
move down to at-least-once, Flink's own docs state, "Barrier alignment is
only needed for providing exactly once guarantees. If you don't need this,
you can gain some performance by configuring Flink to use
CheckpointingMode.AT_LEAST_ONCE, which has the effect of disabling barrier
alignment."

## 8. Implementation variants

**Kafka idempotent producer.** Deduplicates on producer retry alone, no
transaction coordinator involved. Since Kafka 3.0, `enable.idempotence`
defaults to true. This alone covers producer-retry duplicates but not
multi-partition atomicity.

**Kafka transactional producer and consumer (KIP-98).** Adds a
`transactional.id`, a transaction coordinator, and `read_committed` isolation
on the consumer side, giving atomic multi-partition, multi-topic writes.

**Kafka Streams `processing.guarantee=exactly_once_v2`.** The current and
only exactly-once value in Kafka Streams' config, introduced in the 2.6.0
release as a more efficient implementation than the original mechanism, "As
of the 3.0.0 release, the first version of exactly-once has been deprecated.
Users are encouraged to use exactly-once v2 for exactly-once processing from
now on." Turning it on is close to a single config flip for a topology that
does not perform external, non-transactional I/O.

**Apache Flink, `TwoPhaseCommitSinkFunction`.** The older, still documented,
two-phase-commit base class, its lifecycle described above in dimension 5.

**Apache Flink, unified Sink API with `KafkaSink`.** The current
recommended path, `.setDeliveryGuarantee(DeliveryGuarantee.EXACTLY_ONCE)`
paired with a unique `setTransactionalIdPrefix` per job, tied to Flink's
checkpointing (`execution.checkpointing.mode`, default `EXACTLY_ONCE`).

**Google Cloud Dataflow and Apache Beam.** Achieves the same effect through
per-record unique IDs and a receiver-side dedup catalog, "every message is
tagged with a unique ID. Each receiver stores a catalog of all IDs that have
already been seen and processed," combined with checkpointed intermediate
storage between steps, "if the same message is sent multiple times due to
repeated RPC calls, the message is only committed to storage once." The
current live documentation states its own scope limit in the same words
MillWheel used in 2013, side effects and external stores are excluded unless
the sink itself is exactly-once aware.

**Apache Pulsar transactions.** A newer addition covering multi-partition
consume-process-produce as one atomic unit, "All the operations involved in
a transaction succeed or fail as one single unit," addressing a gap the
idempotent producer alone cannot close, since an idempotent producer works
only "on a single partition and within a single producer session."

## 9. Known production uses

Uber's ad-billing pipeline is a directly documented, named production case.
"Real-Time Exactly-Once Ad Event Processing with Apache Flink, Kafka, and
Pinot," Uber Engineering, September 2021, states the requirement plainly,
"This requires processing events exactly-once," and describes a
checkpoint-aligned Flink and Kafka transactional pipeline processing
"hundreds of millions of ad events per week." The same post is also the
clearest documented confirmation of dimension 3's scope limit in production,
every downstream sink the pipeline touches still needed its own idempotency
mechanism layered on top of the transactional core, an idempotency key for
the ad-budget service call, a deduplication identifier for the Hive sink, and
Pinot's own upsert feature to prevent duplicate records reaching that store.

The same company also documents the opposite choice for a different
workload. "Building Reliable Reprocessing and Dead Letter Queues with Apache
Kafka," Uber Engineering, February 2018, states, "Kafka offers at-least-once
semantics by default," and builds a reprocessing and dead-letter pipeline
directly on top of that weaker guarantee plus consumer-side idempotency,
rather than adopting transactions. The two posts together are a real,
citable illustration of the applicability decision in dimension 4 being made
deliberately, by the same engineering organization, in opposite directions
for two different workloads.

## 10. Consequences

Positive. Removes duplicate-caused corruption from counting, billing, and
aggregation workloads without every consumer inventing its own
deduplication. Confluent's own framing of the design goal states the intent
directly, a correctly configured application should see "no throughput
regression" on the parts of the system that do not opt into the feature.

Negative. Measurable throughput cost that grows with commit frequency, from
roughly 3% at the raw Kafka transaction layer to 15 to 30% at the Kafka
Streams layer for a short commit interval, falling back toward zero as the
commit interval widens. Genuine operational overhead, a transaction
coordinator and its own replicated internal log, Kafka's own producer and
Streams documentation both state a minimum of three brokers is the
recommended production configuration for this. And, unavoidably, zero
correctness benefit for whatever falls outside the guarantee's scope, an
external API call, an email send, any non-transactional side effect.

## 11. Failure modes and misuse

**Assuming the guarantee reaches an external side effect.** The single most
common misuse, and the one every primary source in this entry states
explicitly rather than leaving implicit. A stream processor's exactly-once
guarantee stops at its own transactional or checkpointed boundary. Uber's own
production pipeline needed three separate idempotency mechanisms layered on
top of an already-transactional Flink and Kafka core precisely because of
this boundary.

**Zombie producers.** An old producer instance that has lost leadership or
been superseded but has not crashed can still attempt to write. KIP-98's
epoch mechanism exists specifically to stop this, "Bumps up the epoch of the
PID, so that the any previous zombie instance of the producer is fenced off
and cannot move forward with its transaction." This is not a legacy design
note, the current Kafka client source still enforces it, a producer whose
epoch no longer matches what the broker expects fails with
`InvalidProducerEpochException`, whose current javadoc instructs the
application to "abort the ongoing transaction... which would try to send
initPidRequest and reinitialize the producer under the hood."

**Mixing a transactional producer with a non-transactional consumer
downstream.** If the consumer does not set `isolation.level=read_committed`
and disable auto-commit, it will see uncommitted, possibly-aborted data as
final, and its own offset commits advance independently of the producer's
transaction boundary. The guarantee is only as strong as its weakest
participant, and a default-configured consumer downstream of a carefully
configured transactional producer silently breaks the whole chain.

## 12. Trade-off matrix

| Force | At-most-once | At-least-once | Exactly-once / effectively-once |
|---|---|---|---|
| Correctness | Messages may be lost, never duplicated | No loss, duplicates possible, must be tolerated downstream | Each record's effect reflected once, but only within the guarantee's stated scope |
| Throughput cost | Lowest, no retries, no dedup bookkeeping | Low, Kafka's own default behavior | Measurable, roughly 3% at the raw transactional producer level, 15 to 30% at a short-interval Kafka Streams commit cycle, falling toward zero at wider intervals |
| Implementation complexity | Lowest | Moderate, correctness burden shifts to a downstream idempotent consumer | Highest, a transaction coordinator, a minimum three-broker cluster, checkpoint-aligned sinks, and still an idempotent consumer wherever the guarantee does not reach |
| Typical use case | Metrics or logging pipelines where occasional loss is acceptable against cost, Netflix's Keystone pipeline is a documented example of this choice | General-purpose event pipelines where a cheap downstream dedup key is available | Financial counting, billing, and revenue-reporting workloads, Uber's ad-billing pipeline and Pulsar's stated financial debit and credit use case are both documented examples |

## 13. Related and incompatible patterns

**Idempotent-consumer and idempotency-key** are the patterns exactly-once
processing hands off to at the exact boundary dimension 3 and dimension 11
describe. Every primary source in this entry agrees on the same shape, a
processor's internal transactional guarantee stops at its own boundary, and
anything past it, an outbound call, a non-transactional store, needs its own
idempotency at the receiver. Uber's production pipeline layers exactly this
combination, a transactional Flink and Kafka core plus idempotent-consumer
style handling at every external sink.

**Transactional-outbox** solves an adjacent but distinct problem, atomically
publishing an event alongside a local database write, and composes cleanly
with exactly-once processing further downstream in the same pipeline.

**Dead-letter-topic** remains necessary regardless of delivery guarantee. A
record that is genuinely poison, one that will never succeed no matter how
many times it is retried, exhausts retries whether the pipeline is
at-least-once or transactionally exactly-once, and needs a destination that
is not an infinite retry loop.

**Stream-table-duality and replayable-log**, the sibling family entries,
describe the mechanics a Kafka Streams `exactly_once_v2` topology depends on
directly, the compacted changelog topics backing a KTable's local state are
themselves rebuilt through log replay, and that rebuild must be exactly-once
consistent with the rest of the topology for the guarantee to hold end to
end.

**Watermark and event-time-processing** govern correct time-based windowing
when a checkpoint restores state and reprocesses a window, which is a
prerequisite for the checkpoint-and-commit cycle in dimension 7 to produce
the same aggregated result on every retry.

## 14. Refactoring path in and out

**In.** For Kafka Streams, this is close to a single config flip,
`processing.guarantee` from `at_least_once` to `exactly_once_v2`, provided
the topology performs no external, non-transactional I/O, since the config
change alone does not extend the guarantee past Kafka's own boundary. For
Flink, the path is enabling checkpointing at `EXACTLY_ONCE` mode, the
documented default, and switching the sink to a transactional one, a
`KafkaSink` with `DeliveryGuarantee.EXACTLY_ONCE` and a unique transactional
ID prefix, or a custom two-phase-commit sink for a non-Kafka destination.

**Out.** The reverse move is symmetric, and the sourced throughput numbers in
dimension 10 are the real, quantified reason a team makes it, Kafka Streams'
`processing.guarantee` back to `at_least_once`, or Flink's
`CheckpointingMode.AT_LEAST_ONCE`, which "has the effect of disabling barrier
alignment" for a direct performance gain. Uber's own reprocessing and
dead-letter post is documented evidence of a team choosing exactly this
downgrade for a workload where at-least-once plus an idempotent consumer was
the better trade. The idempotent-consumer pattern is the landing point for a
team making this move, since it is what carries the correctness burden once
the transactional mechanism is removed.

## 15. Testing and verification

Test the failure path directly rather than trusting the happy path. Kill a
producer mid-transaction and restart it with the same `transactional.id`,
then assert the next `initTransactions()` call correctly aborts the
in-flight transaction rather than leaving partial writes visible to a
`read_committed` consumer. For Kafka Streams, force a rebalance or a broker
failure during processing and assert the aggregated output shows no
duplicate and no gap once the topology has recovered. For a Flink pipeline,
trigger a mid-checkpoint failure and restart from the last completed
checkpoint, then assert the sink's output matches what a clean, uninterrupted
run would have produced. Separately, and explicitly, test every downstream
side effect that sits outside the transactional boundary, an outbound API
call or a non-transactional write, under a forced retry, to confirm its own
idempotency actually holds rather than assuming the upstream guarantee
covers it.

## 16. Observability signals

Track transaction commit rate against abort rate per producer, a rising
abort rate signals contention or a misconfigured `transaction.timeout.ms`
relative to processing latency. Track consumer lag under `read_committed`
isolation specifically, since an aborted or slow-committing transaction
holds back everything after it in the log from that consumer's point of
view, an effect a `read_uncommitted` consumer would never show. For Kafka
Streams, track the checkpoint or commit interval actually achieved against
the configured `commit.interval.ms`, since the throughput cost from
dimension 10 is directly a function of how often commits actually happen.
For Flink, track checkpoint duration and barrier alignment time per
operator, a rising alignment time under backpressure is the concrete,
visible cost dimension 3 describes as a force.

## 17. Security and privacy implications

A transaction coordinator's internal log, and any checkpointed state
backing a two-phase-commit sink, retains in-flight data until it is
committed or aborted, which means personal data flowing through the
pipeline exists in two places at once during that window, the processor's
own checkpoint or transaction log and its eventual destination. Access
control on the transaction coordinator's internal topics, and on the
checkpoint storage backend, should be treated with the same sensitivity as
the pipeline's primary data store, not as internal plumbing. Zombie fencing
itself, described in dimension 11, is a genuine security-adjacent property,
it prevents a stale, potentially compromised or misbehaving producer
instance from writing after it should have stopped, which is a real
availability and integrity guarantee, not only a correctness one.

## 18. References

Akidau, Balikov, Bekiroglu, Chernyak, Haberman, Lax, McVeety, Mills,
Nordstrom, Whittle. "MillWheel. Fault-Tolerant Stream Processing at Internet
Scale." Proceedings of the VLDB Endowment, Vol. 6, No. 11, VLDB 2013.
Verified 2026-08-23.
https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/41378.pdf.

Apache Software Foundation. "KIP-98. Exactly Once Delivery and Transactional
Messaging." Verified 2026-08-23.
https://cwiki.apache.org/confluence/display/KAFKA/KIP-98+-+Exactly+Once+Delivery+and+Transactional+Messaging.

Apache Software Foundation. Kafka design documentation, apache/kafka trunk
branch. Verified 2026-08-23.
https://raw.githubusercontent.com/apache/kafka/trunk/docs/design/design.md.

Apache Software Foundation. Kafka Streams core concepts documentation,
apache/kafka trunk branch. Verified 2026-08-23.
https://raw.githubusercontent.com/apache/kafka/trunk/docs/streams/core-concepts.md.

Apache Software Foundation. "KafkaProducer" and "KafkaConsumer" Javadoc,
Kafka 40. Verified 2026-08-23.
https://kafka.apache.org/40/javadoc/org/apache/kafka/clients/producer/KafkaProducer.html.

Apache Software Foundation. "FLIP-143. Unified Sink API." Verified
2026-08-23.
https://cwiki.apache.org/confluence/display/FLINK/FLIP-143%3A+Unified+Sink+API.

Apache Software Foundation. Apache Flink fault tolerance and Kafka connector
documentation, current stable release. Verified 2026-08-23.
https://nightlies.apache.org/flink/flink-docs-stable/docs/learn-flink/fault_tolerance/.

Google Cloud. "Exactly-once processing," Dataflow documentation. Verified
2026-08-23.
https://docs.cloud.google.com/dataflow/docs/concepts/exactly-once.

Apache Software Foundation. "Pulsar transactions." Verified 2026-08-23.
https://pulsar.apache.org/docs/next/txn-why/.

Uber Engineering. "Real-Time Exactly-Once Ad Event Processing with Apache
Flink, Kafka, and Pinot." Tsafatinos, Bondaruk, Fu, Kwon. September 23,
2021. Verified 2026-08-23.
https://www.uber.com/en-US/blog/real-time-exactly-once-ad-event-processing/.

Uber Engineering. "Building Reliable Reprocessing and Dead Letter Queues
with Apache Kafka." Ning Xia. February 16, 2018. Verified 2026-08-23.
https://www.uber.com/en-US/blog/reliable-reprocessing/.

Netflix Technology Blog. "Kafka Inside Keystone Pipeline." April 27, 2016.
Verified 2026-08-23.
https://netflixtechblog.com/kafka-inside-keystone-pipeline-dd5aeabaf6bb.

Confluent. "Exactly-Once Semantics Are Possible. Here's How Apache Kafka
Does It." Neha Narkhede, Guozhang Wang. June 30, 2017. Verified 2026-08-23.
https://www.confluent.io/en-gb/blog/enabling-exactly-once-kafka-streams/.

Confluent. "Transactions in Apache Kafka." Apurva Mehta, Jason Gustafson.
November 17, 2017. Verified 2026-08-23.
https://www.confluent.io/blog/transactions-apache-kafka/.

**Evidence grade.** high

**Most solid findings.** The MillWheel paper's own explicit scoping language,
"this guarantee does not extend to external systems," and Google's current
Dataflow documentation using nearly identical scoping language over a decade
later, is an unusually strong, independently corroborated finding across two
different eras of the same lineage. The Kafka mechanics (KIP-98 transaction
coordinator, PID and epoch, isolation level, and the current
`exactly_once_v2` config) are all confirmed against live, current primary
source documentation and source code. Uber's two blog posts, describing the
same engineering organization choosing exactly-once for one workload and
at-least-once for another, are an unusually direct, citable illustration of
the applicability judgment in dimension 4.

**Unverified or unclear.** The term effectively-once could not be confirmed
as language either Apache Beam, Google Cloud Dataflow, or the original 2015
Dataflow Model paper actually use, despite circulating informally in the
streaming community, and is not presented above as a directly sourced vendor
term. A second and third named company beyond Uber, using genuine
transactional exactly-once processing in production, could not be
independently confirmed this session and is not claimed.

## Code examples

A minimal simulation of exactly-once processing across three languages.
Each implements a producer-side sequence number check for duplicate
rejection and a two-phase commit sink, pre-commit buffers a batch, commit
only applies it once every batch in the round has pre-committed.

### TypeScript

```typescript
interface Committable<T> {
  batch: T[];
  committed: boolean;
}

class SequenceGuard {
  private lastSequence = -1;

  accept(sequence: number): boolean {
    if (sequence <= this.lastSequence) {
      return false;
    }
    this.lastSequence = sequence;
    return true;
  }
}

class TwoPhaseCommitSink<T> {
  private pending: Committable<T> | null = null;
  private applied: T[] = [];

  preCommit(batch: T[]): void {
    this.pending = { batch, committed: false };
  }

  commit(): void {
    if (this.pending && !this.pending.committed) {
      this.applied.push(...this.pending.batch);
      this.pending.committed = true;
    }
  }

  abort(): void {
    this.pending = null;
  }

  get appliedRecords(): readonly T[] {
    return this.applied;
  }
}
```

### Python

```python
from dataclasses import dataclass, field


class SequenceGuard:
    def __init__(self):
        self._last_sequence = -1

    def accept(self, sequence: int) -> bool:
        if sequence <= self._last_sequence:
            return False
        self._last_sequence = sequence
        return True


@dataclass
class Committable:
    batch: list
    committed: bool = False


class TwoPhaseCommitSink:
    def __init__(self):
        self._pending: Committable | None = None
        self._applied: list = []

    def pre_commit(self, batch: list) -> None:
        self._pending = Committable(batch=batch)

    def commit(self) -> None:
        if self._pending is not None and not self._pending.committed:
            self._applied.extend(self._pending.batch)
            self._pending.committed = True

    def abort(self) -> None:
        self._pending = None

    @property
    def applied_records(self) -> list:
        return self._applied
```

### Go

```go
package exactlyonce

type SequenceGuard struct {
	lastSequence int
}

func NewSequenceGuard() *SequenceGuard {
	return &SequenceGuard{lastSequence: -1}
}

func (g *SequenceGuard) Accept(sequence int) bool {
	if sequence <= g.lastSequence {
		return false
	}
	g.lastSequence = sequence
	return true
}

type committable struct {
	batch     []interface{}
	committed bool
}

type TwoPhaseCommitSink struct {
	pending *committable
	applied []interface{}
}

func (s *TwoPhaseCommitSink) PreCommit(batch []interface{}) {
	s.pending = &committable{batch: batch}
}

func (s *TwoPhaseCommitSink) Commit() {
	if s.pending != nil && !s.pending.committed {
		s.applied = append(s.applied, s.pending.batch...)
		s.pending.committed = true
	}
}

func (s *TwoPhaseCommitSink) Abort() {
	s.pending = nil
}

func (s *TwoPhaseCommitSink) AppliedRecords() []interface{} {
	return s.applied
}
```
