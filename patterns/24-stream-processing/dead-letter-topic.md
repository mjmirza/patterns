---
name: Dead-Letter Topic
slug: dead-letter-topic
family: 24-stream-processing
category: Stream Processing
aliases: [Dead Letter Queue Topic, Retry Letter Topic]
first_described: "Hohpe and Woolf, Enterprise Integration Patterns, 2003, the general Dead Letter Channel this entry specializes; Apache Kafka KIP-298, Error Handling in Connect, 2018, Kafka 2.0.0, the stream-native, topic-based formalization this entry documents"
maturity: established
related: [dead-letter-channel, stream-backpressure, watermark, circuit-breaker]
incompatible_with: []
verified: 2026-08-23
---

## 1. Name, aliases, and lineage

Dead Letter Channel, the general messaging pattern this entry specializes,
already exists in this repository as a canonical, eighteen-dimension entry
at family 07-integration, sourced to Hohpe and Woolf's 2003 book and covering
the broker-native queue variants directly, AWS SQS, Azure Service Bus, and
RabbitMQ. This entry deliberately does not re-derive that material. it
documents the genuinely distinct, append-only-log-native shape the same idea
takes inside a stream-processing pipeline, where the dead-letter destination
is itself a durable, replayable, consumer-group-addressable topic rather
than a broker-managed queue feature.

The term predates streaming and messaging systems entirely, from the postal
service. a Dead Letter Office was "first established in 1784" in Britain,
and the United States Post Office "started a dead letter office in 1825" for
the same purpose, undeliverable mail opened to find a forwarding address,
then forwarded, destroyed, or auctioned if still unresolvable. Source.
Wikipedia, "Dead letter office," verified 2026-08-23,
https://en.wikipedia.org/wiki/Dead_letter_office.

The Kafka-native formalization is KIP-298, "Error Handling in Connect,"
accepted and released in Apache Kafka 2.0.0, 2018, authored by Arjun Satish,
introducing errors.tolerance, errors.deadletterqueue.topic.name, and the
retry and logging configuration this entry documents in depth below. A later
extension, KIP-610, "Error Reporting in Sink Connectors," reuses the same
mechanism for the Connect Transformations API's own errant-record reporting.
"The Errant Record Reporter will adhere to the existing DLQ error tolerance
functionality... The error reporter will use the same configurations as the
dead letter queue in KIP-298 to avoid redundant configuration." Source.
Apache Kafka wiki, KIP-298 and KIP-610, verified 2026-08-23,
https://cwiki.apache.org/confluence/display/KAFKA/KIP-298%3A+Error+Handling+in+Connect
and
https://cwiki.apache.org/confluence/display/KAFKA/KIP-610%3A+Error+Reporting+in+Sink+Connectors.

## 2. Problem and context

KIP-298's own motivation states the problem this entry's stream-native
variant answers directly. "There are several places in Connect during which
failures may occur. Any failure to deserialize, convert, process, or
read/write a record in Kafka Connect can cause a task to fail... it is
difficult to [guarantee] correct and valid data or to tell Connect to skip
problematic records." Without this mechanism, a single malformed record
causes the entire Connect task, the framework's own unit of parallelism, to
fail outright, the task-blocking failure mode named in this family's own
sibling entries.

The alternative failure mode, silent data loss, is the exact case the
sibling Watermark entry already documents for the event-time and lateness
side of this same family. its own dimension 11 names "a metric or count
that is silently and permanently short, discovered only when totals fail to
reconcile against a source-of-truth system, often days or weeks later." A
Dead-Letter Topic converts either failure mode, task-blocking or silent
loss, into a third, recoverable outcome, preserved but diverted data.

## 3. Forces

Fail-fast versus tolerate-and-continue, stated as a literal two-value switch
by the framework's own current source code doc string. "'none' is the
default value and signals that any error will result in an immediate
connector task failure, 'all' changes the behavior to skip over problematic
records." Confluent's own guidance names which side of that switch to pick
and why. "if the pipeline is such that any erroneous messages are unexpected
and indicate a serious problem upstream then failing immediately... makes
sense," against, "if you are perhaps streaming data to storage for analysis
or low-criticality processing, then so long as errors are not propagated it
is more important to keep the pipeline running." Source. Robin Moffatt,
"Kafka Connect [Closer Look], Error Handling and Dead Letter Queues," Confluent
blog, verified 2026-08-23,
https://www.confluent.io/blog/kafka-connect-deep-dive-error-handling-dead-letter-queues/.

How many retries before giving up is a time budget, not a count. "The
maximum duration in milliseconds that a failed operation will be
reattempted. The default is 0, which means no retries will be attempted,"
so by default the framework attempts zero retries and goes straight to the
tolerance decision on the first failure. When retry is enabled, KIP-298
states the shape. "starting with a fixed duration, value of 300ms, and with
exponential backoff between each retry," capped by errors.retry.delay.max.ms,
default 60000, with a detail the original 2018 KIP does not mention but the
current source code doc string does. "Jitter will be added to the delay
once this limit is reached to prevent thundering herd issues."

The cost of an unbounded, unmonitored dead-letter topic if the root cause is
never fixed, named directly by Moffatt's own blog. "by default it won't log
the fact that messages are being dropped... This is hardly elegant but it
does show that we're dropping messages, and since there's no mention in the
log of it we'd be none the wiser." A team can silently accumulate an
unbounded, unmonitored dead-letter topic purely by turning on tolerance
without also turning on logging, since both default to off independently.

## 4. Applicability and non-applicability

Reach for this pattern when a per-record failure, deserialization,
transform, conversion, or a watermark and lateness horizon in the sibling
entries' sense, is independent of the health of the stream as a whole, and
a genuine downstream plan exists for the diverted records.

Do not reach for it when the correct response to an unprocessable message is
to halt and alert immediately, Confluent's own stated criterion for this,
"any erroneous messages are unexpected and indicate a serious problem
upstream." A financial reconciliation pipeline is a natural application of
that same directly-sourced principle, an unreconciled or silently-dropped
record is a correctness failure there, not a tolerable one, though this
entry states plainly that no source it fetched used the words financial
reconciliation directly, this is a reasoned application, not a quoted
example. Do not reach for it during a systemic, not message-specific,
downstream outage, without a circuit breaker in front of the failing
dependency first, covered further in Related and incompatible patterns
below, or every message in flight during the outage looks identical to a
genuinely poison one and floods the dead-letter topic with false positives.
Kafka Connect's own scope is itself a non-applicability boundary. the
mechanism "applies exclusively to sink connectors," per KIP-298, so a source
connector reading from an external system into Kafka cannot reach for this
specific implementation at all.

## 5. Structure

Two structurally distinct shapes exist in stream processing, presented
separately since no source unifies them under one API.

Kafka Connect, purpose-built, declarative, sink-connector-only. the
tolerance switch, errors.tolerance, default none. the retry budget,
errors.retry.timeout, default 0, and its backoff cap,
errors.retry.delay.max.ms, default 60000. the logging toggles,
errors.log.enable, default false, and errors.log.include.messages, default
false, which "prevent[s] record keys, values, and headers from being
written to log files" by default. the destination itself,
errors.deadletterqueue.topic.name, default blank, "which means that no
messages are to be recorded in the DLQ," an ordinary Kafka topic that
inherits Kafka's own retention, replication, and consumer-group semantics.
its auto-provisioned replication factor, errors.deadletterqueue.topic.replication.factor,
default 3. and diagnostic headers, errors.deadletterqueue.context.headers.enable,
default false, which attaches error context prefixed __connect.errors. to
avoid clashing with the original record's own headers. Source. Apache Kafka
source, ConnectorConfig and SinkConnectorConfig doc strings, apache/kafka
trunk branch, verified 2026-08-23,
https://github.com/apache/kafka/blob/trunk/connect/runtime/src/main/java/org/apache/kafka/connect/runtime/ConnectorConfig.java.

Apache Pulsar, a native, topic-based variant with a distinct intermediate
stage. "Dead letter topic allows you to continue message consumption even
when some messages are not consumed successfully," configured via
DeadLetterPolicy and a maxRedeliverCount, with a naming convention of
topicname-subscriptionname-DLQ. Pulsar distinctively routes through a retry
letter topic first, carrying a reconsume-count tracking property, before the
terminal dead letter topic once the redelivery budget is exhausted. "Once
the maximum number of retries has been reached, the unconsumed messages are
moved to a dead letter topic for manual processing." Source. Apache Pulsar
documentation, "Messaging," verified 2026-08-23,
https://pulsar.apache.org/docs/next/concepts-messaging/.

## 6. ASCII structure diagram

```
KAFKA CONNECT (sink connector, per-record, retry-triggered)

  source topic -> [ sink connector task: convert, transform, put() ]
                              |
                       record fails
                              v
              [ retry, exponential backoff, jitter-capped at
                errors.retry.delay.max.ms, bounded total by
                errors.retry.timeout, default 0 ]
                              |
                    retries exhausted
                              v
                errors.tolerance == none (default)
                   |                          |
                  yes                         no
                   v                          v
       [ task fails,                errors.tolerance == all
         pipeline stops ]                     |
                                    optional: errors.log.enable
                                       -> Connect worker log
                                               |
                             errors.deadletterqueue.topic.name set?
                                |                          |
                               no                         yes
                                v                          v
                  record silently              record plus optional
                  dropped, no trace             __connect.errors.*
                                                 headers -> ordinary
                                                 Kafka topic

FLINK (windowed stream, event-time and lateness triggered, no retry loop)

  event stream -> [ watermark advances past window end + allowedLateness ]
                              |
                    sideOutputLateData(tag) configured?
                       |                          |
                      no                         yes
                       v                          v
          silently dropped,            ctx.output(tag, record)
          no trace                     -> a separate DataStream,
                                          retrieved via
                                          getSideOutput(tag),
                                          sunk wherever the
                                          pipeline author chooses
```

## 7. Dynamics

The retry-then-tolerate-then-route sequence, live-verified against Apache
Kafka's own current source code. a processing operation fails. retry is
attempted first, bounded by a total time budget rather than a count, zero
by default. once the budget is exhausted, errors.tolerance decides the
outcome, a binary switch with no built-in graduated policy such as tolerate
the first N errors then fail. if tolerating, two independently-defaulted-off
toggles decide what evidence survives, error logging and whether the record
body itself is logged. independently of logging, if the dead-letter topic
name is set, the record is written there, auto-creating the topic if needed
at the configured replication factor, with diagnostic headers attached if
enabled. there is no automatic redrive built into the framework, recovery
is manual or external.

The Flink side-output mechanism is structurally different and event-time-
triggered rather than retry-triggered. there is no retry loop at all in
this path, because too late is not a transient condition a retry could
resolve. "By default, late elements are dropped when the watermark is past
the end of the window," extendable via allowedLateness, after which only
elements still past that extended horizon are candidates for
sideOutputLateData diversion. unlike Kafka Connect's config-only toggle,
enabling this requires the pipeline author to declare an OutputTag, chain
it onto the windowed stream, and separately retrieve and sink the resulting
stream, and unlike Kafka Connect's DLQ headers, no diagnostic context is
attached by the mechanism itself, only the record's own original payload
and timestamp. Source. Apache Flink documentation, "Side Outputs" and
"Windows," verified 2026-08-23,
https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/side_output/
and
https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/operators/windows/.

## 8. Implementation variants

Kafka Connect, the primary, most precisely documented variant, covered in
full above. sink-connector-only, config-driven, an ordinary Kafka topic as
the destination.

Apache Pulsar, a second, independently-built, topic-native variant, with a
genuinely distinct feature the Kafka side has no equivalent of, an
intermediate retry letter topic stage before the terminal dead letter topic,
tracked with its own reconsume-count property. one documented caveat.
"Without enableRetry(true), the redelivery counter that drives
maxRedeliverCount is not persisted and can be reset unexpectedly."

AWS Lambda's event source mapping on-failure destination, for Kinesis and
DynamoDB Streams, a third, structurally different shape worth naming
precisely because the difference is consequential. configured with
MaximumRetryAttempts and MaximumRecordAgeInSeconds, an age and attempts
budget against a shard rather than a receive-count on a queue.
BisectBatchOnFunctionError "splits a failed batch into two smaller batches,
isolating bad records and avoiding timeouts," a batch-bisection retry
strategy with no analogue in either Kafka Connect or Pulsar. The sharpest
structural distinction of the whole entry, for Kinesis and DynamoDB
specifically the destination record does not contain the original payload,
only shard and sequence-number metadata. "Because Lambda sends only the
metadata for these destination types, use the streamArn, shardId,
startSequenceNumber, and endSequenceNumber fields to obtain the full
original record... The actual records aren't included, so you must process
this record and retrieve them from the stream before they expire and are
lost." In a queue-native system the dead-lettered message itself is durably
copied into the destination. here the dead letter is a pointer back into
the source log, inheriting that log's own retention window, so a pointer
that is never followed in time loses its target even though the pointer
itself was delivered successfully. Source. AWS documentation, "Using
AWS Lambda with Amazon Kinesis," verified 2026-08-23,
https://docs.aws.amazon.com/lambda/latest/dg/with-kinesis.html.

SQS, Azure Service Bus, and RabbitMQ's own broker-native dead-lettering are
already documented in depth in the general Dead Letter Channel entry and are
not repeated here.

## 9. Known production uses

Uber Engineering's Reliable Reprocessing. its Insurance Engineering team
built a tiered Kafka retry-topic architecture terminating in a dead letter
topic, "If a consumer of the last retry topic still does not return
success, then it will publish that message to the dead letter topic,"
chaining retry topics with increasing delay, "When the handler of a
particular topic returns an error response for a given message, it will
publish that message to the next retry topic below it." Their DLQ tooling
supports "listing for viewing the contents of the queue, purging for
clearing those contents, and merging for reprocessing the dead-lettered
messages." Named production context, their Driver Injury Protection program
runs "in more than 200 cities." no specific message-volume figure was
given, and this entry does not invent one. Source. Uber Engineering blog,
"Reliable Reprocessing," verified 2026-08-23,
https://www.uber.com/blog/reliable-reprocessing/.

A second, independently-sourced named case was searched for and not found
within the attempts made for this entry. Confluent's and AWS's own
customer-story index pages were checked live and neither surfaces a
DLQ-specific case study on its visible index content, this is an
absence-of-evidence-on-the-index-page finding, not proof no such case study
exists elsewhere.

## 10. Consequences

A Kafka dead-letter topic inherits the source platform's own durability and
consumer-group model for free, redrive requires no special API, Moffatt's
own blog demonstrates reprocessing a DLQ topic with a second, ordinary
consumer, "just as we would with any other topic," because it is exactly
that.

The same property removes a consequence a broker-native queue gives for
free. a built-in depth and age metric. SQS exposes ApproximateNumberOfMessages
and ApproximateAgeOfOldestMessage directly on its DLQ, an ordinary Kafka
topic has no built-in equivalent, Moffatt's own blog builds one manually via
a ksqlDB aggregate query over a time window. the monitoring burden the
general Dead Letter Channel entry already warns about is structurally
heavier on a log-based DLQ than a queue-based one, because the platform
itself provides nothing to alert on out of the box.

The Kinesis and DynamoDB on-failure destination introduces a consequence
with no queue-based analogue at all, already named in Implementation
variants above, the dead-lettered pointer can itself expire and vanish,
separately from the destination record that referenced it, a second-order
data-loss risk unique to systems where the DLQ stores a reference into a
replayable log rather than a durable copy of the payload.

## 11. Failure modes and misuse

Shard-level head-of-line blocking, up to the full retention window, on
Kinesis specifically. "With the default settings, this means that a bad
record can block processing on the affected shard for up to one week," a
concrete, sourced worst-case bound worth carrying directly into any
MaximumRecordAgeInSeconds and MaximumRetryAttempts configuration decision.

Silent secondary data loss if the DLQ delivery itself fails. "If Lambda
can't send a message to the dead-letter queue, it deletes the event and
emits the DeadLetterErrors metric." The pattern's own last line of defense
can itself fail, and the platform's answer is not retry the DLQ write, it
is drop the event and emit a metric a team must already be watching to
notice.

A DLQ that fills for the wrong reason because errors.tolerance was set
without matching the workload's real criticality. Confluent's own guidance,
already quoted in Forces, frames this as an explicit design decision, not a
bug. misapplying tolerate-all to a pipeline where every error genuinely does
indicate a serious upstream problem converts what should be a loud, blocking
failure into a quiet trickle nobody is watching, compounding the
unmonitored-graveyard failure mode the general Dead Letter Channel entry
already documents.

## 12. Trade-off matrix

Fail-fast, skip-and-log, dead-letter-and-continue, and infinite-retry as
four named alternatives.

| Force | Fail-fast | Skip-and-log | Dead-letter-and-continue | Infinite-retry |
|---|---|---|---|---|
| Preserves the failed record | No, the record is never processed | No, discarded, only a log line survives | Yes, with diagnostic context, headers or a redelivery counter | Yes, but it never leaves the hot path |
| Protects healthy traffic from one poison record | No, the whole pipeline halts by design | Yes, at the cost of losing the record | Yes, this is the pattern's whole reason for existing | No, a single record can block a shard or partition for the full retention window on Kinesis |
| Ongoing operational cost | Lowest, but every incident pages someone | Lowest, but invisible failure accumulates | Real, a queue gives depth and age metrics for free, a topic must build that monitoring itself | Can silently degrade throughput as the poison record consumes retry budget forever |
| Directly endorsed by a fetched source | Confluent, "any erroneous messages are unexpected and indicate a serious problem upstream" | Not endorsed by any source fetched, the implicit worse-than-dead-lettering baseline | Confluent, "so long as errors are not propagated it is more important to keep the pipeline running" | Not endorsed, Pulsar's maxRedeliverCount and Kinesis's MaximumRetryAttempts exist specifically to bound it |

## 13. Related and incompatible patterns

Dead Letter Channel, the general ancestor this entry specializes, already
published in family 07-integration at canonical depth, covering the
Hohpe-and-Woolf lineage and the broker-native SQS, Azure Service Bus, and
RabbitMQ variants this entry deliberately does not repeat.

Watermark, the published sibling, states the relationship from its own side
directly, quoted verbatim. "Dead-Letter Topic, queued. The natural companion
to the silent-drop failure mode named in Failure modes and misuse above.
Rather than letting data past the watermark, allowed-lateness, or grace-
period horizon vanish, a deliberately designed pipeline routes it to a side
output or dead-letter sink, Flink's sideOutputLateData being the concrete,
sourced example, instead of discarding it." The honest nuance this entry
adds from its own side, Flink's side output is triggered by lateness, a
temporal completeness concern, not by a processing exception, so late-data
side output and dead-letter topic answer companion but distinct questions,
what happened versus when it happened, not the same trigger condition.

Stream Backpressure, the published sibling, names this pattern in its own
trade-off matrix directly, quoted verbatim. "Load shedding, dropping or
dead-lettering excess data instead of buffering or signaling upstream,
trades correctness and completeness for a hard, predictable latency and
memory ceiling, the right choice when a pipeline's downstream SLA cannot
tolerate the propagation delay backpressure itself introduces." Here
dead-lettering is offered as an alternative strategy to backpressure,
trading completeness for a latency ceiling, a distinct relationship from
the Watermark one above, where dead-lettering is a companion to a specific
failure mode rather than an alternative to a different mechanism entirely.

Circuit Breaker, published in family 08-cloud-distributed. the real
distinction, corroborated by every source fetched for this entry. a circuit
breaker stops calling a failing dependency, a systemic, dependency-health
concern protecting the caller from a downstream outage, while a dead-letter
topic preserves a specific unprocessable message, a message-level,
data-preservation concern. The composition case named in the general Dead
Letter Channel entry applies unchanged here, a dead-letter-only system with
no circuit breaker in front of a flaky downstream call floods its DLQ with
false positives during an outage, since every message in flight looks
identical to a genuinely poison one from the threshold policy's point of
view.

## 14. Refactoring path in and out

Migrating in, Kafka Connect, concrete and config-only. set
errors.tolerance to all. name a errors.deadletterqueue.topic.name. lower
errors.deadletterqueue.topic.replication.factor from its default of 3 on a
single-broker or small cluster. turn on
errors.deadletterqueue.context.headers.enable, since without it the DLQ
topic holds only the raw failed payload with no attached reason,
undermining the diagnostic value the whole pattern exists to provide.
Redrive is then a second, ordinary consumer, or a second Connect sink
connector, pointed at the DLQ topic, no special API required.

Migrating in, AWS Lambda event source mappings for Kinesis and DynamoDB
Streams, a genuinely different concrete path from SQS's. configure
MaximumRetryAttempts, MaximumRecordAgeInSeconds, and a destination on the
event source mapping itself, not on a queue. because the destination
receives only a pointer, not the payload, per Implementation variants
above, a team must additionally decide a retrieval plan for the referenced
range before the source stream's own retention window expires it, a
decision the SQS path does not require.

When to deliberately not adopt this pattern, grounded directly in
Confluent's own stated criterion, quoted in Applicability above, when any
erroneous messages are unexpected and indicate a serious problem upstream,
failing immediately, not dead-lettering, is the explicitly recommended
choice.

Removing a dead-letter topic once adopted carries a cost the general Dead
Letter Channel entry's queue-oriented framing does not surface as sharply.
because a Kafka or Pulsar topic carries its own retention and storage cost
independent of consumer activity, decommissioning must include deleting or
repurposing the topic itself, not merely disabling the routing
configuration that feeds it, an inert but still-retaining-data DLQ topic is
a real, ongoing storage cost an idle SQS or Service Bus queue is not.

## 15. Testing and verification

Because the destination is, in Moffatt's own words already quoted above,
an ordinary topic and nothing more, verifying Kafka Connect's dead-letter
behavior does not require a dedicated framework test utility class. a test
feeds a deliberately malformed
record through the connector under test, then asserts, with an ordinary
Kafka consumer subscribed to the configured errors.deadletterqueue.topic.name,
that the record arrives there carrying the expected __connect.errors.*
diagnostic headers, proving the retry, tolerate, and route sequence from
Dynamics end to end. this entry could not locate a dedicated, currently
published Javadoc page for Kafka Connect's own embedded test-cluster utility
within this session, and states that gap honestly rather than naming a
class this entry did not verify live.

## 16. Observability signals

errors.log.enable and errors.log.include.messages, Kafka Connect's own
logging toggles, are the primary, directly-sourced signal, both default to
false independently, so a team relying on tolerance alone without also
enabling logging has, by construction, no log-based signal that anything is
being dropped. On Kinesis and DynamoDB, the DeadLetterErrors CloudWatch
metric, already named in Failure modes above, is the signal that the
pattern's own last line of defense has itself failed, and it is the only
signal in that specific failure path, since the event itself is deleted, not
retried, when the DLQ write fails. Where the dead-letter destination is an
ordinary Kafka or Pulsar topic, standard consumer-group lag on that topic is
this entry's own reasoned extension of the already-sourced fact that it is
just another topic, a growing, unconsumed backlog there is the same kind of
signal an idle SQS DLQ's ApproximateNumberOfMessages already gives for
free, built manually rather than provided by the platform.

## 17. Security and privacy implications

errors.log.include.messages defaults to false specifically as a stated
privacy default, its own doc string frames the choice directly. "This is
'false' by default, which will prevent record keys, values, and headers
from being written to log files," an explicit, sourced acknowledgment that
a failed record's contents can carry sensitive data a team may not want in
application logs. The dead-letter topic itself carries a wider surface than
that same concern once diagnostic headers are enabled. the raw failed
payload plus, when errors.deadletterqueue.context.headers.enable is on, a
full exception stacktrace and class name attached as headers, which can
itself leak internal system details, file paths, class names, to anyone
with read access to the topic. this entry's own reasoning from the
documented header contents in Structure above, not a directly quoted
security warning, since no source fetched for this entry frames it in
these terms. On Kinesis and DynamoDB specifically, the destination record
containing only metadata rather than payload, already named in
Implementation variants, is a genuine privacy mitigation in the opposite
direction, a party with access only to the on-failure destination cannot
read the original data without separately retrieving it from the source
stream.

## 18. References

Wikipedia. "Dead letter office." Verified 2026-08-23.
https://en.wikipedia.org/wiki/Dead_letter_office.

Apache Kafka wiki. "KIP-298. Error Handling in Connect." Verified
2026-08-23.
https://cwiki.apache.org/confluence/display/KAFKA/KIP-298%3A+Error+Handling+in+Connect.

Apache Kafka wiki. "KIP-610. Error Reporting in Sink Connectors." Verified
2026-08-23.
https://cwiki.apache.org/confluence/display/KAFKA/KIP-610%3A+Error+Reporting+in+Sink+Connectors.

Robin Moffatt. "Kafka Connect [Closer Look]. Error Handling and Dead Letter
Queues." Confluent blog. Verified 2026-08-23.
https://www.confluent.io/blog/kafka-connect-deep-dive-error-handling-dead-letter-queues/.

Apache Kafka source. ConnectorConfig and SinkConnectorConfig doc strings.
apache/kafka trunk branch. Verified 2026-08-23.
https://github.com/apache/kafka/blob/trunk/connect/runtime/src/main/java/org/apache/kafka/connect/runtime/ConnectorConfig.java.

Apache Pulsar documentation. "Messaging." Verified 2026-08-23.
https://pulsar.apache.org/docs/next/concepts-messaging/.

Apache Flink documentation. "Side Outputs." Verified 2026-08-23.
https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/side_output/.

Apache Flink documentation. "Windows." Verified 2026-08-23.
https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/operators/windows/.

AWS documentation. "Using AWS Lambda with Amazon Kinesis." Verified
2026-08-23. https://docs.aws.amazon.com/lambda/latest/dg/with-kinesis.html.

Uber Engineering blog. "Reliable Reprocessing." Verified 2026-08-23.
https://www.uber.com/blog/reliable-reprocessing/.

**Evidence grade.** medium-high.

Most solid findings. the Kafka Connect config surface, defaults, and retry
mechanics are sourced directly to the framework's own current source code
and its original design KIP, cross-corroborated by an independent
practitioner blog written by a named Confluent engineer. the Kinesis
pointer-versus-payload distinction and its one-week worst-case blocking
bound are both directly quoted from AWS's own current documentation.

Unverified or unclear. a second, independently-named production use beyond
Uber's could not be confirmed within the attempts made for this entry.
dimension 15's testing approach and dimension 17's stacktrace-leak framing
are this entry's own reasoning from already-sourced mechanics, not directly
quoted procedures or warnings. no dedicated Kafka Connect test-utility-class
Javadoc could be located live in this session, the same gap the entry's own
research independently found for the Connect runtime's internal
DeadLetterQueueReporter class, which appears not to be published on the
public Javadoc site at all. WebSearch was unavailable for the session this
entry was researched in, so source discovery relied on direct WebFetch
against known or reconstructed canonical URLs.

## Code examples

Minimal, illustrative simulations of the retry-then-tolerate-then-route
sequence described above. a fixed retry budget, a tolerance switch, and a
dead-letter sink that records diagnostic context. These are teaching
illustrations of the protocol's shape, not a reimplementation of Kafka
Connect's own error-handling pipeline.

### TypeScript

```typescript
type DeadLetterRecord = {
  key: string;
  originalTopic: string;
  errorClass: string;
  errorMessage: string;
};

type ProcessFn = (key: string) => void;

class DeadLetterRouter {
  private readonly maxRetries: number;
  private readonly tolerateAll: boolean;
  private readonly deadLetters: DeadLetterRecord[] = [];

  constructor(maxRetries: number, tolerateAll: boolean) {
    this.maxRetries = maxRetries;
    this.tolerateAll = tolerateAll;
  }

  process(key: string, originalTopic: string, fn: ProcessFn): boolean {
    let attempt = 0;
    while (attempt <= this.maxRetries) {
      try {
        fn(key);
        return true;
      } catch (err) {
        attempt += 1;
        if (attempt > this.maxRetries) {
          if (!this.tolerateAll) {
            throw err;
          }
          const error = err as Error;
          this.deadLetters.push({
            key,
            originalTopic,
            errorClass: error.constructor.name,
            errorMessage: error.message,
          });
          return false;
        }
      }
    }
    return false;
  }

  drainDeadLetters(): DeadLetterRecord[] {
    return [...this.deadLetters];
  }
}
```

### Python

```python
from dataclasses import dataclass
from typing import Callable


@dataclass
class DeadLetterRecord:
    key: str
    original_topic: str
    error_class: str
    error_message: str


class DeadLetterRouter:
    def __init__(self, max_retries: int, tolerate_all: bool) -> None:
        self.max_retries = max_retries
        self.tolerate_all = tolerate_all
        self.dead_letters: list[DeadLetterRecord] = []

    def process(self, key: str, original_topic: str, fn: Callable[[str], None]) -> bool:
        attempt = 0
        while attempt <= self.max_retries:
            try:
                fn(key)
                return True
            except Exception as err:
                attempt += 1
                if attempt > self.max_retries:
                    if not self.tolerate_all:
                        raise
                    self.dead_letters.append(
                        DeadLetterRecord(
                            key=key,
                            original_topic=original_topic,
                            error_class=type(err).__name__,
                            error_message=str(err),
                        )
                    )
                    return False
        return False

    def drain_dead_letters(self) -> list[DeadLetterRecord]:
        return list(self.dead_letters)
```

### Go

```go
package deadlettertopic

import "fmt"

type DeadLetterRecord struct {
	Key           string
	OriginalTopic string
	ErrorClass    string
	ErrorMessage  string
}

type ProcessFn func(key string) error

type DeadLetterRouter struct {
	MaxRetries  int
	TolerateAll bool
	deadLetters []DeadLetterRecord
}

func NewDeadLetterRouter(maxRetries int, tolerateAll bool) *DeadLetterRouter {
	return &DeadLetterRouter{MaxRetries: maxRetries, TolerateAll: tolerateAll}
}

func (r *DeadLetterRouter) Process(key string, originalTopic string, fn ProcessFn) (bool, error) {
	attempt := 0
	for attempt <= r.MaxRetries {
		err := fn(key)
		if err == nil {
			return true, nil
		}
		attempt++
		if attempt > r.MaxRetries {
			if !r.TolerateAll {
				return false, err
			}
			r.deadLetters = append(r.deadLetters, DeadLetterRecord{
				Key:           key,
				OriginalTopic: originalTopic,
				ErrorClass:    fmt.Sprintf("%T", err),
				ErrorMessage:  err.Error(),
			})
			return false, nil
		}
	}
	return false, nil
}

func (r *DeadLetterRouter) DrainDeadLetters() []DeadLetterRecord {
	out := make([]DeadLetterRecord, len(r.deadLetters))
	copy(out, r.deadLetters)
	return out
}
```
