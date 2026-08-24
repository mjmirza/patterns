---
name: Replayable Log
slug: replayable-log
family: 24-stream-processing
category: Stream Processing
aliases: [Commit Log, Append-Only Log, Log-Structured Storage]
first_described: "Apache Kafka project (Kreps, Narkhede, Rao), LinkedIn, 2011; retention and compaction model per Apache Kafka design documentation"
maturity: canonical
related: [stream-table-duality, event-time-processing, watermark, exactly-once-processing, idempotent-consumer]
incompatible_with: []
verified: 2026-08-23
---

# Replayable Log

## 1. Name, aliases, and lineage

A replayable log is a durable, append-only, offset-addressable record store that
a consumer can re-read from any past position, rather than a store that
discards a record once it has been delivered. The term is used interchangeably
with commit log, append-only log, and log-structured storage. Apache Kafka is
the reference implementation and the source of most of the vocabulary this
entry uses.

Kafka's own design documentation frames the choice of a log as the central
storage abstraction directly. Confluent's mirror of that documentation states,
"Supporting these uses led to a design with a number of unique elements,
making Kafka more like a database log than a traditional messaging system."
Kafka's introduction page describes a topic the same way, as an append-only,
ordered sequence, "A topic is an ordered log of events (records) stored
durably in Kafka," and, "A topic is append only: When a new event message is
written to a topic, the message is appended to the end of the log."

Kafka itself was created at LinkedIn by Jay Kreps, Neha Narkhede, and Jun Rao,
first described publicly around 2011. Kreps' widely cited 2013 essay on the
log as a unifying abstraction for both messaging and storage is the essay most
often credited with popularizing this way of thinking about a log, but that
essay's original hosting location could not be reached live while researching
this entry, every URL variant returned a dead link. It should not be cited
here as a working source until a reachable copy is confirmed. The durable,
citable lineage for this entry rests on Kafka's own current design
documentation instead, which independently states the same log-centric
architecture.

## 2. Problem and context

A traditional message queue removes a message once it has been consumed. A
new consumer that starts after that point has nothing left to read, and an
existing consumer that needs to reprocess history, because a bug in its
aggregation logic is discovered after the fact, has no way to go back. Amazon
SQS is the clearest example of this model. Its own FAQ states plainly,
"You're responsible for deleting the message and the deletion request
acknowledges that you're done processing the message," and, "If you don't
delete the message, Amazon SQS will deliver it again when it receives another
receive request." Even before an explicit delete, SQS bounds how long a
message can be recovered at all, "You can configure the Amazon SQS message
retention period to a value from 1 minute to 14 days. The default is 4 days,"
and, "Once the message retention quota is reached, your messages are
automatically deleted."

A replayable log solves this by never removing a record on consumption at
all. Consumption in a log-based system is nothing more than a client moving
its own read position forward. Kafka's introduction page states the
consequence of this directly, "The only metadata retained on a per-consumer
basis is the offset or position of that consumer in a topic." Nothing about
reading a record changes what is stored. A late-joining consumer group, an
event-sourced system rebuilding its state, and a pipeline reprocessing a
window of history after a bug fix are all the same operation, seeking to an
earlier offset and reading forward again.

## 3. Forces

**Retention cost against replay flexibility.** A wider retention window means
more history is available to replay, but every retained byte is stored
whether or not anything ever reads it again. A team must decide how far back
replay needs to reach and pay for exactly that, not for an unbounded window
by default.

**Two different retention strategies pull in different directions.** Kafka
supports time or size bounded retention, where every record older than the
window is deleted regardless of its key, and log compaction, where the
retention policy documentation states, "Topic compaction is a mechanism that
allows you to retain the latest value for each message key in a topic, while
discarding older values," described further as, "Log compaction is a
mechanism to provide finer-grained per-record retention instead of
coarser-grained time-based retention." A team can choose either policy per
topic, "This retention policy can be set per-topic, so a single cluster can
have some topics where retention is enforced by size or time and other topics
where retention is enforced by compaction." The two policies serve different
replay needs, delete-based retention favors a bounded event history, compact
retention favors an always-current snapshot of the latest state per key with
no guarantee that intermediate history survives.

**Ordering and offset stability against storage reclamation.** Compaction
removes superseded values but never reorders or renumbers what remains, "The
offset for a message never changes. It is the permanent identifier for a
position in the log," and, "Ordering of messages is always maintained.
Compaction will never reorder messages, remove some records instead." This
lets a replaying consumer trust that the sequence it reads is still the
original sequence, even though gaps now exist where superseded values used to
be.

## 4. Applicability and non-applicability

Reach for a replayable log when a system needs event sourcing or state
rebuild from history, change data capture pipelines that multiple downstream
consumers read independently, audit or compliance trails where the original
sequence of events must remain inspectable, machine learning feature backfill
against historical data, or multi-consumer fan-out where each consumer needs
to progress through the same data at its own pace without coordinating with
the others.

Do not reach for it when the workload is a simple task queue where a message
should be processed exactly once by exactly one worker and then discarded.
SQS's own model, an explicit per-message delete backed by a short default
retention window, is the better fit there, because paying for a replayable
retention window buys nothing a one-time job queue will ever use.

## 5. Structure

A log is divided into partitions, each an independently ordered, append-only
sequence, "Topics are broken up into partitions, meaning a single topic log
is broken into multiple logs located on different Kafka brokers." A producer
writes new records to the end of a partition, "Producers are clients that
write events to Kafka," and controls which partition each record lands in.
A consumer reads forward from a position it tracks itself, "Consumers are
clients that read events from Kafka," and because "the only metadata retained
on a per-consumer basis is the offset or position of that consumer in a
topic," any number of independent consumer groups can each hold a different
position in the same partition at the same time, with no coordination between
them and no effect on what is stored.

Every record's position is permanent once assigned, "The offset for a
message never changes. It is the permanent identifier for a position in the
log." That permanence is what makes an offset a stable address a consumer can
seek back to, days or months later, and land on exactly the same record it
would have read at the time.

## 6. ASCII structure diagram

```
Partition, an append-only log, growing left to right

head, oldest, subject to retention
tail, newest, producer appends here

records:  0  1  2  3  4  5  6  7  8  9  10  11
                                              ^
                                    new records land here

Consumer Group B, offset 1, replaying from near the start
Consumer Group A, offset 8, caught up
Consumer Group C, offset 11, just joined
  (auto.offset.reset=earliest would instead seek to 0)

Three independent groups, three independent cursors, one
unchanged log.
```

## 7. Dynamics

Replay is driven entirely by moving a consumer's own read position, never by
asking the log to send old data again through a separate mechanism. Kafka's
current consumer client exposes this directly. `seek(TopicPartition, long)`
"overrides the fetch offsets that the consumer will use on the next
poll(timeout)." `seekToBeginning(Collection<TopicPartition>)` will "seek to
the first offset for each of the given partitions," and `seekToEnd` does the
same for the last offset. `offsetsForTimes(Map<TopicPartition, Long>)` will
"look up the offsets for the given partitions by timestamp," which lets a
consumer replay from a specific point in wall clock time rather than a raw
offset number.

A brand new consumer group, one with no committed offset yet, decides where
to start via the `auto.offset.reset` client setting, most commonly either
earliest, which replays the entire retained log from the start, or latest,
which skips straight to the current tail and only sees records written from
that point forward. This single setting is the difference between a group
that bootstraps its state from full history and one that only ever sees new
events.

Replay also happens involuntarily when a consumer's committed offset has
aged out of the retention window, because the record it was pointing at no
longer exists. The consumer's next fetch fails with an offset out of range
condition, and `auto.offset.reset` decides what happens next, jump to
earliest and reprocess whatever is still retained, jump to latest and
silently skip past whatever was lost, or throw and require a person to
decide. A slow or offline consumer that falls behind its retention window
long enough hits exactly this condition, and any data older than the window
is gone regardless of which choice the consumer makes.

## 8. Implementation variants

**Kafka retention and compaction.** Delete based retention removes every
record past a time or size bound regardless of key. Log compaction instead
keeps only the latest value per key, discarding superseded values while
guaranteeing offset order is never disturbed, though it does not guarantee
exactly one record per key at every instant, "Compaction in Kafka does not
guarantee there is only one record with the same key at any one time. There
may be multiple records with the same key," since compaction runs
periodically, not on every write.

**Kafka tiered storage.** KIP-405, "production-ready since Kafka 3.9,"
addresses the cost side of long retention by splitting storage into a fast
local tier and a cheaper remote tier backed by object storage. Recent,
latency sensitive reads are served locally, "Latency sensitive applications
perform tail reads and are served from local tier," while old data needed
for a backfill or a failure recovery is served from the remote tier,
"Backfill and other applications recovering from a failure that needs data
older than what is in the local tier are served from the remote tier." This
lets a team shrink the expensive local retention window down to hours while
extending the cheap remote window to months, without changing what a replaying
consumer can see.

**Amazon Kinesis Data Streams.** Retention defaults to 24 hours and can be
extended, "A Kinesis data stream stores records from 24 hours by default, up
to 8760 hours (365 days)," via an explicit operation, "You can increase the
retention period up to a maximum of 8760 hours (365 days) using the
IncreaseStreamRetentionPeriod operation or the Kinesis Data Streams console,"
at a cost, "Additional charges apply for streams with a retention period set
above 24 hours." Shrinking the window back down takes effect quickly and
permanently, "Kinesis Data Streams almost immediately makes records older
than the new retention period inaccessible upon decreasing the retention
period," so a team cannot casually shrink retention and expect to change its
mind later.

**Apache Pulsar.** Pulsar separates the serving layer from the storage layer.
Its broker is described as "a stateless component," while the underlying
BookKeeper storage layer "is horizontally scalable in both capacity and
throughput. Capacity can be immediately increased by adding more bookies to a
cluster." Pulsar also ships its own tiered storage, moving sealed,
never-again-written segments to cheaper long-term storage, "Pulsar's Tiered
Storage feature allows older backlog data to be moved from BookKeeper to
long-term and cheaper storage," while keeping them fully replayable, "After
transferring ledgers to long-term storage, the messages within these ledgers
remain accessible to Pulsar consumers and readers."

**Event-sourcing datastores.** KurrentDB, the current name for the project
formerly known as EventStoreDB, treats the replayable log itself as the
primary datastore rather than a transport layer in front of one, marketing
directly on this capability, "Replay, rewind or rebuild to any moment," and,
"Projects the same source data into any new shape," backed by, "Immutable,
globally ordered log providing chronological sequencing across all events."
Note the rename, older references to EventStoreDB now redirect to the
KurrentDB product.

## 9. Known production uses

Apache Kafka's own production users page names direct examples of replay
driven and history-dependent workloads. Cloudflare runs a "Log processing and
analytics pipeline (hundreds of billions events daily)." Evident Systems uses
Kafka for "Event Sourcing and CQRS applications," an architecture that
depends entirely on the ability to replay history to rebuild state. Grab
describes its use as "TB/hour scale event logs, event sourcing, and stream
processing," again naming event sourcing directly. DataVisor runs a
"Critical real-time data pipeline for fraud detection," a workload that
regularly needs historical replay to retrain or re-score against past
events. LinkedIn, the system's origin, lists "Activity stream data and
operational metrics" as its own production use.

## 10. Consequences

Positive. A new consumer can bootstrap its state directly from history with
no separate backfill pipeline to build and maintain. A bug found in
downstream aggregation logic can be fixed and the affected window
reprocessed by replaying, rather than by reconstructing lost state from
secondary records. Multiple independent consumers can each read the same
history at their own pace with no coordination between them.

Negative. Storage cost scales with the retention window chosen, or, under
compaction, with the number of distinct keys ever written, since compaction
keeps the latest value per key forever rather than discarding it after a
fixed time. Retention and compaction policy is a real per-topic decision a
team must make deliberately, not a default that can be ignored. Replaying
data into a downstream system that is not built to tolerate reprocessing
duplicates whatever side effects that downstream system produced the first
time.

## 11. Failure modes and misuse

A consumer that falls behind its retention window loses access to whatever
data aged out while it was behind, silently and permanently, regardless of
whether it later chooses to replay from the earliest available offset. The
data that expired during the outage is gone, not merely unread. This is the
single most common way a team is surprised by a replayable log's actual
retention behavior, they assume the log itself is a permanent record, when
in practice a delete-based retention policy is a moving window, not an
archive.

A second misuse is assuming compaction produces exactly one record per key
at all times. It does not, "Compaction in Kafka does not guarantee there is
only one record with the same key at any one time. There may be multiple
records with the same key," because compaction runs as a periodic background
process rather than on every write. Code that reads a compacted topic and
assumes it will see at most one record per key between compaction passes
will see stale, superseded values it did not expect.

A third failure mode is replaying history into a non-idempotent downstream
system, an email send, a payment charge, a counter increment with no
deduplication, and producing every one of those side effects a second time.
Replayability is a property of the log, not of whatever reads it, and a
consumer must be built to tolerate reprocessing before replay is safe to
rely on. See idempotent-consumer and exactly-once-processing for the
patterns that address this directly.

## 12. Trade-off matrix

| Force | Replayable log (Kafka style) | Delete-on-ack queue (SQS style) | Event-sourcing store (KurrentDB style) |
|---|---|---|---|
| Replay capability | Full replay from any retained offset or timestamp, by any number of independent consumer groups | None once a message is explicitly deleted, bounded further by a maximum 14 day retention | Replay is the primary mode of interaction, not a secondary capability |
| Storage cost | Grows with the retention window, or per distinct key under compaction, mitigated by tiered storage | Bounded and small, capped at 14 days, cheapest of the three | Effectively unbounded, since keeping full history is the product's purpose |
| Consumer coupling | Fully decoupled, each consumer group tracks its own offset independently | Effectively single-consumer per message, coordinated through a visibility timeout | Decoupled via projections built on top of the raw event stream |
| Operational complexity | Higher, retention and compaction policy must be chosen and tuned per topic | Lowest, a single managed retention setting | Comparable to higher, since projections and read models must be built and maintained on top of the log |

## 13. Related and incompatible patterns

**Stream-table duality** is the closest sibling in this family. A Kafka
Streams KTable is built by replaying a compacted topic into local state, so
the KTable materialization step is a direct application of a replayable log
to rebuilding in-memory state from history. See this repository's
stream-table-duality entry for the mechanics of that materialization.

**Exactly-once-processing** and **idempotent-consumer** are the patterns a
team reaches for once it starts relying on replay, because replaying history
into a system that is not idempotent duplicates every side effect the
original processing pass produced. A replayable log without an idempotent or
transactional consumer downstream is the misuse described in dimension 11.

**Watermark** and **event-time-processing**, the other family siblings,
govern how a replay run correctly reconstructs event-time ordering and
windowing when it is reprocessing at a different wall clock time than the
original run.

**Change data capture** is a common upstream producer feeding a replayable
log, turning a database's own write history into a replayable stream other
systems can consume independently.

## 14. Refactoring path in and out

**In.** A team on a traditional delete-on-ack queue gains replay the moment
it migrates to a log based system, since a log never removes data on
consumption. No consumer code change is required to gain the capability,
only to use it, calling `seekToBeginning` or configuring
`auto.offset.reset=earliest` for a new group. Turning on compaction for an
existing topic is a live, per-topic configuration change and does not
require migrating existing data.

**Out.** A team whose consumers have become stateful in ways that make replay
dangerous, incrementing external counters or sending notifications with no
deduplication, should not keep relying on raw replay as their recovery
mechanism. The correct move is either making the consumer idempotent, the
durable fix, or introducing periodic state snapshots so recovery resumes from
the last snapshot instead of from the true beginning, trading some replay
flexibility for safety and a faster recovery path.

## 15. Testing and verification

Test replay behavior directly rather than assuming it works because the
happy path does. Seed a topic with a known sequence of records, consume it
once, then start a second consumer group with `auto.offset.reset=earliest`
and assert it reads the identical sequence in the identical order. For
compaction, write multiple values for the same key, trigger or wait for
compaction, and assert only the latest value survives while offsets remain
monotonic. For the offset out of range failure mode, shrink a test topic's
retention aggressively, let a committed offset age out, and assert the
consumer's chosen `auto.offset.reset` behavior actually happens, rather than
assuming it will.

## 16. Observability signals

Track consumer lag, the difference between the log's current end offset and
each consumer group's committed offset, per partition. A group whose lag
grows without bound is falling toward the retention window and eventual data
loss on that partition. Track the log's actual retained span, oldest
available offset or timestamp against the newest, so an operator can see how
much replay history genuinely exists before a consumer needs it. For
compacted topics, track the ratio of live to superseded records and how
recently the last compaction pass ran, since a stalled compaction job lets
storage grow unexpectedly. A healthy instance shows consumer lag flat or
recovering and the retained span consistently exceeding every active
consumer's worst observed downtime.

## 17. Security and privacy implications

A replayable log retains every write for the length of its retention window,
including any personal data a producer wrote into it, which means a delete
request under a privacy regulation cannot simply remove one record the way a
row delete in a database can. Compaction with a tombstone record, a record
with a null value for a given key, is the usual mechanism for expressing a
logical delete inside a compacted topic, but the tombstone itself is only
removed after its own retention period, and any consumer that already
replayed the original value before the tombstone was written retains a copy
outside the log entirely. Retention and compaction policy for any topic
carrying personal data should be a deliberate decision made with this
constraint in mind, not an operational default.

## 18. References

Confluent. "Kafka Design." Verified 2026-08-23.
https://docs.confluent.io/kafka/design/index.html.

Confluent. "Introduction to Apache Kafka." Verified 2026-08-23.
https://docs.confluent.io/kafka/introduction.html.

Confluent. "Log Compaction." Verified 2026-08-23.
https://docs.confluent.io/kafka/design/log_compaction.html.

Amazon Web Services. "Amazon Simple Queue Service FAQs." Verified 2026-08-23.
https://aws.amazon.com/sqs/faqs/.

Apache Software Foundation. "KIP-405. Kafka Tiered Storage." Verified
2026-08-23.
https://cwiki.apache.org/confluence/display/KAFKA/KIP-405%3A+Kafka+Tiered+Storage.

Amazon Web Services. "Changing the Data Retention Period." Amazon Kinesis
Data Streams Developer Guide. Verified 2026-08-23.
https://docs.aws.amazon.com/streams/latest/dev/kinesis-extended-retention.html.

Apache Software Foundation. "Pulsar Concepts and Architecture." Verified
2026-08-23.
https://pulsar.apache.org/docs/next/concepts-architecture-overview/.

Apache Software Foundation. "Pulsar Tiered Storage." Verified 2026-08-23.
https://pulsar.apache.org/docs/next/tiered-storage-overview/.

Kurrent. "KurrentDB" product page. Verified 2026-08-23.
https://kurrentdb.kurrent.io/eventstoredb.

Apache Software Foundation. "Powered By." Verified 2026-08-23.
https://kafka.apache.org/powered-by.

Apache Software Foundation. "KafkaConsumer" Javadoc, Kafka 4.3. Verified
2026-08-23.
https://kafka.apache.org/43/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html.

This repository. patterns/24-stream-processing/stream-table-duality.md, for
the compacted topic to KTable cross reference.

**Evidence grade.** medium

**Most solid findings.** The Kafka partition, offset, and per-consumer-group
independence model, the delete versus compaction retention distinction, and
the KIP-405 tiered storage mechanics all rest on live, directly quoted,
official Kafka or Confluent documentation. The Kinesis and Pulsar variant
facts are similarly direct quotes from current AWS and Apache Pulsar
documentation.

**Unverified or unclear.** Jay Kreps' 2013 essay on the log as a unifying
abstraction, widely credited as the popularizing account of this pattern,
could not be reached at any of its commonly cited URLs during this entry's
research and is not cited above as a working source. The exact current
config property spelling for delete versus compact retention policy, and the
precise current doc string for the auto.offset.reset out of range behavior,
were not confirmed against a clean, unambiguous live page and are described
here at the concept level rather than quoted verbatim.

## Code examples

Minimal in-memory replayable log across three languages. Each implements
append-only storage with permanent offsets, an independent read cursor per
consumer, and a seek operation that moves a cursor to any offset without
touching the underlying log.

### TypeScript

```typescript
interface LogRecord<T> {
  offset: number;
  value: T;
}

class ReplayableLog<T> {
  private records: LogRecord<T>[] = [];

  append(value: T): number {
    const offset = this.records.length;
    this.records.push({ offset, value });
    return offset;
  }

  readFrom(offset: number, limit: number): LogRecord<T>[] {
    return this.records.slice(offset, offset + limit);
  }

  get endOffset(): number {
    return this.records.length;
  }
}

class LogCursor<T> {
  private position = 0;

  constructor(private readonly log: ReplayableLog<T>) {}

  seek(offset: number): void {
    this.position = Math.max(0, Math.min(offset, this.log.endOffset));
  }

  seekToBeginning(): void {
    this.seek(0);
  }

  poll(maxRecords: number): LogRecord<T>[] {
    const batch = this.log.readFrom(this.position, maxRecords);
    if (batch.length > 0) {
      this.position = batch[batch.length - 1].offset + 1;
    }
    return batch;
  }
}
```

### Python

```python
from dataclasses import dataclass


@dataclass
class LogRecord:
    offset: int
    value: object


class ReplayableLog:
    def __init__(self):
        self._records: list[LogRecord] = []

    def append(self, value: object) -> int:
        offset = len(self._records)
        self._records.append(LogRecord(offset=offset, value=value))
        return offset

    def read_from(self, offset: int, limit: int) -> list[LogRecord]:
        return self._records[offset:offset + limit]

    @property
    def end_offset(self) -> int:
        return len(self._records)


class LogCursor:
    def __init__(self, log: ReplayableLog):
        self._log = log
        self._position = 0

    def seek(self, offset: int) -> None:
        self._position = max(0, min(offset, self._log.end_offset))

    def seek_to_beginning(self) -> None:
        self.seek(0)

    def poll(self, max_records: int) -> list[LogRecord]:
        batch = self._log.read_from(self._position, max_records)
        if batch:
            self._position = batch[-1].offset + 1
        return batch
```

### Go

```go
package replayablelog

type LogRecord struct {
	Offset int
	Value  interface{}
}

type ReplayableLog struct {
	records []LogRecord
}

func (l *ReplayableLog) Append(value interface{}) int {
	offset := len(l.records)
	l.records = append(l.records, LogRecord{Offset: offset, Value: value})
	return offset
}

func (l *ReplayableLog) ReadFrom(offset int, limit int) []LogRecord {
	if offset >= len(l.records) {
		return nil
	}
	end := offset + limit
	if end > len(l.records) {
		end = len(l.records)
	}
	return l.records[offset:end]
}

func (l *ReplayableLog) EndOffset() int {
	return len(l.records)
}

type LogCursor struct {
	log      *ReplayableLog
	position int
}

func NewLogCursor(log *ReplayableLog) *LogCursor {
	return &LogCursor{log: log}
}

func (c *LogCursor) Seek(offset int) {
	if offset < 0 {
		offset = 0
	}
	if offset > c.log.EndOffset() {
		offset = c.log.EndOffset()
	}
	c.position = offset
}

func (c *LogCursor) SeekToBeginning() {
	c.Seek(0)
}

func (c *LogCursor) Poll(maxRecords int) []LogRecord {
	batch := c.log.ReadFrom(c.position, maxRecords)
	if len(batch) > 0 {
		c.position = batch[len(batch)-1].Offset + 1
	}
	return batch
}
```
