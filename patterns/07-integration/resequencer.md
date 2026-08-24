---
name: Resequencer
slug: resequencer
family: 07-integration
category: Integration (Message Routing)
aliases: [Reordering Filter, Sequence Resequencer, Message Resequencer, Reorder Buffer]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [message-sequence, correlation-identifier, message-filter, guaranteed-delivery, dead-letter-channel, idempotent-consumer]
incompatible_with: []
verified: 2026-08-02
---

# Resequencer

## 1. Name, aliases, and lineage

The canonical name is Resequencer. It is documented as one of the Message
Routing patterns in Gregor Hohpe and Bobby Woolf, *Enterprise Integration
Patterns. Designing, Building, and Deploying Messaging Solutions*,
Addison-Wesley, 2003, in the Message Routing chapter. The companion reference
site for the book states the problem the pattern answers as "How can we get a
stream of related but out-of-sequence messages back into the correct order?"
and the solution as "Use a stateful filter, a Resequencer, to collect and
re-order messages so that they can be published to the output channel in a
specified order" (Enterprise Integration Patterns, "Resequencer",
https://www.enterpriseintegrationpatterns.com/patterns/messaging/Resequencer.html,
verified 2026-08-02).

The pattern predates the book's name for it. Every packet-switched network
protocol that numbers its units and reorders them on arrival is an instance,
and those protocols were standardized decades earlier, so Resequencer is best
read as the name Hohpe and Woolf gave to a pattern that networking engineers
already built routinely, generalized to the messaging domain. The book itself
places it as a specialization of the Aggregator pattern, one that collects
messages into a group the way an Aggregator does but never combines them,
only reorders and forwards them unchanged.

Two implementation communities use different names for the same idea.
Messaging middleware calls it a Resequencer, matching the book, and it appears
under that exact name in Apache Camel and Spring Integration, both cited in
dimension 9. Networking and streaming systems call the equivalent component a
jitter buffer, a reorder buffer, or a reassembly buffer, and RFC 3550
describes RTP receivers performing the same function under the term
"restoring packet sequence" rather than resequencing. A reader who has met the
idea only as a jitter buffer in a WebRTC stack and a reader who has met it
only as a Camel `resequence()` DSL call are describing the same pattern under
two names drawn from two communities that rarely read each other's
literature.

## 2. Problem and context

A producer emits a series of related units, each carrying an explicit position
in a sequence, a timestamp, or an ordinal, and the units are meant to be
consumed, displayed, or applied in that order. Between the producer and the
consumer sits a transport that does not guarantee delivery order. This is not
a hypothetical edge case, it is the default behavior of almost every
transport that scales past a single ordered pipe.

A message queue with multiple competing consumers on one queue delivers
messages to whichever consumer happens to be free next, so two messages sent
one after another can be processed by two different consumers running at two
different speeds, and the second can finish first. A load-balanced set of HTTP
workers processing webhook callbacks has the same property, the callbacks
arrive at the load balancer in order but fan out to workers whose response
times differ. A Kafka topic with more than one partition preserves order only
within a partition, so any producer key that spans more than one partition, or
any consumer that reads from several partitions and merges the results, sees
interleaving. A network path with two possible routes, one congested and one
not, delivers packets sent later ahead of packets sent earlier whenever the
faster route wins the race. A batch of parallel API calls issued to speed up
a fan-out, then awaited and processed as results arrive, produces results in
whatever order the calls happen to complete.

The context that makes Resequencer the right tool has three properties. The
units genuinely have a defined order, carried explicitly in the data rather
than inferred from arrival time. The consumer's correctness or the
downstream contract depends on processing them in that order, not merely on
processing all of them eventually. And the disorder is bounded, meaning most
units arrive close to their correct position and a small buffer holding the
recent window is enough to restore order, rather than units arriving in a
pattern so scrambled that the buffer would need to hold the entire stream.
Outside that context, the pattern either does nothing useful or becomes
unbounded, both covered in dimension 4.

## 3. Forces

- **Latency versus correctness.** Sacrificed is timeliness. A Resequencer
  cannot release a unit until it is certain that unit is next, which means
  holding it, and holding costs wall-clock time on the critical path. Favoured
  is order correctness, which the pattern buys directly at that cost.
- **Memory versus completeness.** A Resequencer must retain every
  out-of-order unit it has already received until the gap in front of it
  closes. An unbounded buffer guarantees completeness at unbounded memory
  cost. A bounded buffer bounds memory at the cost of a policy decision about
  what happens when a unit never arrives, covered under timeout and capacity
  in dimension 8.
- **Statefulness versus operability.** The pattern is inherently stateful,
  the opposite of the stateless routers and filters that sit beside it in the
  Message Routing family. State means a restart, a failover, or a rebalance
  can lose in-flight buffered units unless that state is externalized,
  which is itself a cost in infrastructure and complexity.
- **Throughput versus fairness across keys.** When one correlated sequence
  stalls waiting for a missing unit, a naive implementation that processes
  sequences one at a time can starve every other sequence behind it. A
  correct implementation partitions its buffer by correlation key so one
  stuck sequence never blocks another, which costs more bookkeeping.
  Hohpe and Woolf's own book warns that Resequencer usage should stay to
  short sequences with small gaps for exactly this reason, a point echoed
  directly in Apache Camel's own documentation, cited in dimension 9.
- **Simplicity of the consumer versus complexity of the pipeline.** Favoured
  is a downstream consumer that can assume strict order and therefore stay
  simple, often stateless itself. Sacrificed is pipeline simplicity, because
  a new stateful, failure-prone component now sits between producer and
  consumer.
- **Exactly-once framing versus at-least-once transports.** Most transports
  that need a Resequencer are at-least-once, and a redelivered unit is not
  distinguishable from a legitimate retry without additional bookkeeping.
  The pattern must decide whether a duplicate of an already-released
  sequence number is dropped, retained, or passed through, which is the
  `allowDuplicates` and `rejectOld` decision documented for Camel in
  dimension 9.

## 4. Applicability and non-applicability

Reach for Resequencer when the following hold together.

- Units carry an explicit, monotonic sequence number, timestamp, or ordinal
  that the consumer can compare, not merely a best-effort arrival time.
- The consumer's logic is genuinely order-dependent. A financial ledger that
  applies debits and credits in wall-clock order, a video decoder that needs
  frames in presentation order, a state machine driven by ordered events, an
  audit log that must read back in the order events occurred.
- The transport between producer and consumer can reorder units, and you do
  not control or cannot change that transport's ordering guarantee cheaply.
- The amount of disorder is bounded. Units arrive within a window you can
  size, whether that window is measured in a fixed count of units or a fixed
  span of time.
- You are willing to pay the added latency of holding units, because the
  cost of processing out of order is worse than the cost of a bounded delay.

Do NOT reach for Resequencer in these cases, and the reason matters as much
as the rule.

- **The transport already guarantees order for the scope you need.** A
  single-partition Kafka topic with a single consumer, a point-to-point
  queue with one consumer, or an in-process channel already delivers in
  order. Adding a Resequencer on top adds latency and a stateful failure
  point for a guarantee you already have. Verify the guarantee at the
  actual boundary you depend on, not at a boundary that merely sounds
  ordered, a multi-partition Kafka topic consumed by one consumer preserves
  order per partition, not across partitions.
- **Order does not actually matter to the consumer.** If the consumer is
  commutative, for example summing independent counters, merging into a set,
  or writing keyed upserts where the last write wins on a timestamp already
  carried in the payload, resequencing buys nothing and only adds latency.
  This is the single most common misapplication, covered in dimension 11.
- **The disorder is unbounded or adversarial.** If units can arrive in an
  order with no bound on how far out of place a unit can be, for example a
  batch job that reprocesses a full historical dataset in arbitrary order
  after a stream restart, a Resequencer's buffer either grows without limit
  or drops units it should have kept. A sort-based batch step is the honest
  tool for unbounded disorder, not a streaming Resequencer.
- **Idempotent, order-independent processing is available downstream and
  cheaper to build.** If the consumer can be made to tolerate any arrival
  order, for example by storing each unit keyed by its sequence number and
  computing derived state on read rather than on write, that design removes
  the need for resequencing entirely and is usually less code than a correct
  Resequencer with timeout, capacity, and duplicate handling.
- **You need to combine related messages into one, not merely reorder
  them.** That is Aggregator's job. A Resequencer that also merges is
  usually an Aggregator that someone has mislabeled, and building it as a
  Resequencer will fight the pattern's contract of passing messages through
  unchanged, which Spring Integration states explicitly as the distinction
  between the two (Spring Integration Reference, "Resequencer",
  https://docs.spring.io/spring-integration/reference/resequencer.html,
  verified 2026-08-02).
- **Strict wall-clock real-time delivery matters more than order.** A
  Resequencer trades latency for order. In a domain where a late unit is
  worthless, such as a live sports score overlay where a stale frame should
  be dropped rather than delayed, the correct pattern is Message Filter or a
  bounded discard policy, not a buffer that holds things back.
- **The sequence gap is caused by a genuine loss, not merely a reordering.**
  A Resequencer that waits forever for a unit that was actually dropped by
  the transport never releases anything after it. Either pair the
  Resequencer with Guaranteed Delivery so loss cannot happen upstream, or
  give the Resequencer an explicit timeout policy, covered in dimension 8,
  so a permanently missing unit does not stall the sequence forever.

## 5. Structure

Four participants, named by the role each plays.

- **Sequence Identifier.** A field on each unit, explicit in the data, that
  defines the correct order. Most commonly an integer counter, sometimes a
  timestamp, sometimes a composite of a correlation key plus a counter
  scoped to that key. The Resequencer trusts this field completely, it has
  no other way to know the correct order.
- **Correlation Key.** The field, often distinct from the sequence
  identifier, that groups units belonging to the same logical sequence.
  When only one logical sequence flows through the component the
  correlation key can be implicit, but any component handling more than one
  concurrent sequence needs it to keep sequences from interleaving in the
  buffer.
- **Buffer.** The stateful store holding units that have arrived but cannot
  yet be released because an earlier unit in the same sequence has not yet
  arrived. The buffer is keyed by correlation key and, within a key, ordered
  by sequence identifier. It is the component's memory and its single point
  of failure.
- **Release Policy.** The rule deciding when a held unit, or a run of held
  units, is allowed to leave the buffer and move to the output. The two
  dominant policies are contiguity, release as soon as the next expected
  sequence number is present, and completeness, release only once the whole
  known sequence has arrived. A timeout or capacity bound is a third,
  necessary policy that overrides the first two when they would otherwise
  wait forever, covered in dimension 8.

A fifth, implicit participant deserves naming because it is where most
production bugs live, the **Discard or Escape Path**, the destination for a
unit the Resequencer decides it will never be able to place in order, whether
because its sequence number is older than anything still eligible for
release, because a timeout expired with a gap still open, or because the
buffer hit capacity. A Resequencer with no discard path either drops units
silently or blocks forever, and dimension 11 catalogs both failures.

## 6. ASCII structure diagram

```
   Input Channel                    Resequencer                 Output Channel
  (out of order)          +--------------------------------+    (in order)
       |                  |                                |         |
       |  seq=1,3,2,4      |   Correlation Key -> Buffer   |          |
       +----------------->|   Buffer for key A               |          |
                          |     1 released already          |          |
                          |     2 held pending arrival       |          |
                          |     3 held pending gap close     |          |
                          |   Buffer for key B                |          |
                          |     5 held waiting for 4          |          |
                          |                                  |          |
                          |   Release Policy                 |          |
                          |     contiguous run from next-     |          |
                          |     expected key emits forward    |----------+
                          |                                  |
                          |   Timeout / Capacity Guard        |
                          |     expired or over-capacity      |
                          +-----------+----------------------+
                                      |
                                      v
                              Discard / Escape Channel
                             (send-partial-result-on-expiry,
                              dead letter, or reject-old path)
```

## 7. Dynamics

The flow below shows the contiguity release policy, the one used by stream
mode implementations such as Apache Camel's stream resequencer and by the
buffer described for RTP receivers. Units 1, 3, 2, 4 arrive in that order for
one correlation key. The Resequencer holds 3 because 2 has not yet arrived,
then releases 2 and 3 together the instant 2 arrives, because releasing is
driven by contiguity from the next expected sequence number, not by arrival
order.

```
Producer        Input Channel         Resequencer            Output Channel
   |                  |                    |                        |
   |-- unit(seq=1) -->|                    |                        |
   |                  |-- unit(seq=1) ---->|                        |
   |                  |                    |-- next=1, emit 1 ----->|
   |                  |                    |   next becomes 2       |
   |                  |                    |                        |
   |-- unit(seq=3) -->|                    |                        |
   |                  |-- unit(seq=3) ---->|                        |
   |                  |                    |-- 3 not next, hold 2   |
   |                  |                    |   buffer holds 3       |
   |                  |                    |                        |
   |-- unit(seq=2) -->|                    |                        |
   |                  |-- unit(seq=2) ---->|                        |
   |                  |                    |-- 2 is next, emit 2 -->|
   |                  |                    |   next becomes 3        |
   |                  |                    |-- 3 in buffer, emit -->|
   |                  |                    |   next becomes 4        |
   |                  |                    |   buffer empty          |
   |                  |                    |                        |
   |-- unit(seq=4) -->|                    |                        |
   |                  |-- unit(seq=4) ---->|                        |
   |                  |                    |-- 4 is next, emit 4 -->|
   |                  |                    |   next becomes 5        |
```

Two properties this diagram makes visible. First, arrival order (1, 3, 2, 4)
and release order (1, 2, 3, 4) differ, which is the entire point of the
pattern. Second, a single arrival can trigger more than one release, the
arrival of unit 2 releases both 2 and 3 in the same step, because 3 was
already sitting in the buffer waiting for exactly that gap to close. A
correct implementation must loop the release check after every insertion
rather than checking only the newly arrived unit, which is a common source of
the stuck-buffer bug in dimension 11.

## 8. Implementation variants

**Batch mode with a fixed-size or fixed-time window.** The Resequencer
collects a bounded set of units, either a count (`batchSize`) or a time span
(`batchTimeout`), sorts the whole set once the window closes, and releases
the sorted set as one block. Apache Camel documents this as its default
mode, with a default batch size of 100 and a default batch timeout of 1000
milliseconds (Apache Camel Documentation, "Resequence EIP",
https://camel.apache.org/components/next/eips/resequence-eip.html,
verified 2026-08-02). Batch mode is the simplest to reason about and the
easiest to make correct, because sorting a closed, bounded collection has no
edge cases the way an open-ended stream does. Its cost is that every unit in
the batch waits for the batch to close, even a unit that arrived first and
in order, which adds latency proportional to the batch window regardless of
how well-ordered the input actually was.

**Stream mode with gap detection.** The Resequencer processes a continuous
stream and releases each unit the instant it becomes the next expected one,
holding only the units genuinely out of place. Camel documents this mode as
detecting gaps between messages and releasing as soon as a gap closes, with
a `capacity` bound, defaulting to 1000 elements, to prevent unbounded memory
growth, and a `timeout` that discards pending messages when a successor
fails to arrive within the configured window (Apache Camel Documentation,
"Resequence EIP", same source as above, verified 2026-08-02). Stream mode
adds latency only to units that are genuinely out of order, which is the
correct trade-off when most traffic already arrives close to order and only
a minority needs holding.

**Contiguous-partial release versus complete-sequence release.** Within
either mode, a further choice is whether to release a contiguous prefix as
soon as it forms, or to wait for every unit in a defined group before
releasing any of them. Spring Integration exposes this directly as the
`release-partial-sequences` attribute. Setting it `true` sends ordered runs
as soon as they are valid, and `false`, the default, waits for the entire
group, identified by a `SEQUENCE_SIZE` header or a custom release strategy,
before releasing anything (Spring Integration Reference, "Resequencer", same
URL as dimension 4, verified 2026-08-02). Complete-sequence release is
appropriate when the consumer genuinely needs the whole group at once, for
example reconstructing a multi-part document. Partial release is appropriate
when the consumer can process units one at a time as long as their relative
order is correct, which is the more common case in streaming pipelines.

**Comparator-driven ordering rather than a strict integer counter.** Camel's
`expression()` configuration accepts any expression, not only an integer
sequence number, so a timestamp, a composite key, or a business-defined
comparator can drive the sort, and a `reverse` flag can invert the direction
(Apache Camel Documentation, "Resequence EIP", same URL as above, verified
2026-08-02). This generalizes the pattern beyond a literal counter to any
totally ordered field, at the cost that a comparator with ties or a
non-strict order can produce ambiguous release decisions that a strict
integer counter cannot.

**Duplicate and stale-unit policy.** A redelivered unit or a unit whose
sequence number is older than the last one already released needs an
explicit decision. Camel's stream mode exposes `allowDuplicates`, which
retains a duplicate instead of dropping it, and `rejectOld`, which throws
when an incoming unit is strictly older than the last delivered one (Apache
Camel Documentation, "Resequence EIP", same URL as above, verified
2026-08-02). Building a Resequencer without this decision made explicit is
the single most common gap between a demo implementation and a production
one, because at-least-once transports guarantee that a redelivery will
eventually happen.

**Windowed buffering as a cousin rather than the pattern itself.** Kafka
Streams offers `TimeWindows.ofSizeAndGrace(size, afterWindowEnd)`, where the
grace period admits out-of-order records for a bounded time after a window's
nominal end before the window is finally closed, described in its Javadoc as
determining "the time to admit out-of-order events after the end of the
window", with records older than the grace period dropped (Apache Kafka
Javadoc, `org.apache.kafka.streams.kstream.TimeWindows`,
https://kafka.apache.org/38/javadoc/org/apache/kafka/streams/kstream/TimeWindows.html,
verified 2026-08-02). This is not the Resequencer pattern in the strict
sense, because a windowed aggregation re-emits an updated aggregate on every
late arrival rather than releasing individual units in corrected order, but
it solves the same underlying forces, bounded lateness tolerance traded
against buffering cost, and a reader coming from stream processing rather
than messaging middleware will recognize the shape immediately.

**External state store for durability.** Any variant that must survive a
process restart, a consumer rebalance, or a failover externalizes the buffer
to a database, a key-value store, or a durable message store rather than
holding it in process memory. Spring Integration's `message-store` attribute
is exactly this seam, defaulting to a volatile in-memory store and
accepting a pluggable durable one (Spring Integration Reference,
"Resequencer", same URL as dimension 4, verified 2026-08-02). Every
production deployment that cannot tolerate losing in-flight buffered units
on a restart needs this variant, and it is the single largest jump in
operational complexity the pattern can require.

## 9. Known production uses

**Apache Camel, Resequence EIP.** Camel ships resequencing as a first-class
DSL construct, `resequence(expression)`, configurable into batch mode with
`.batch()` or stream mode with `.stream()`, exposing the `batchSize`,
`batchTimeout`, `capacity`, `timeout`, `allowDuplicates`, and `rejectOld`
options documented above. Apache Camel Documentation, "Resequence EIP",
https://camel.apache.org/components/next/eips/resequence-eip.html, verified
2026-08-02.

**Spring Integration, Resequencer.** Spring Integration ships a `Resequencer`
component, configurable via XML, Java DSL, or annotations, that groups
messages by a correlation strategy and releases them by sequence number
according to a configurable release strategy, backed by a pluggable message
store for durability. Spring Integration Reference, "Resequencer",
https://docs.spring.io/spring-integration/reference/resequencer.html,
verified 2026-08-02.

**RTP, RFC 3550.** The Real-time Transport Protocol, the transport underlying
nearly all VoIP and video conferencing traffic including WebRTC, carries
an explicit sequence number in every packet's fixed header specifically so
the receiver can restore the sender's original order. The RFC states the
sequence number "increments by one for each RTP data packet sent, and may be
used by the receiver to detect packet loss and to restore packet sequence,"
and further notes that "the sequence numbers included in RTP allow the
receivers to reconstruct the sender's packet sequence." IETF RFC 3550,
"RTP. A Transport Protocol for Real-Time Applications," Section 5.1,
https://www.rfc-editor.org/rfc/rfc3550.html, verified 2026-08-02. Every
jitter buffer implementation in a production VoIP or video stack, from
browser WebRTC engines to hardware conferencing endpoints, is a Resequencer
built against this field.

## 10. Consequences

Positive.

- The consumer can be written against a strict ordering contract and stay
  simple, deferring the hard problem of transport-level disorder to one
  named, testable component instead of scattering ordering checks through
  every downstream handler.
- The pattern makes an implicit assumption, that messages arrive in order,
  explicit and enforced, which surfaces reordering bugs as a visible,
  measurable buffer depth rather than as silent downstream corruption.
- Isolating reordering into one component gives a single place to add
  metrics, tracing, and alerting for out-of-order rates, which is otherwise
  nearly impossible to observe once disorder has propagated into business
  logic.
- The pattern composes cleanly with Guaranteed Delivery and Idempotent
  Consumer to build a full at-least-once, in-order delivery guarantee out of
  three narrowly scoped, independently testable pieces.

Negative.

- Every held unit adds latency proportional to how long the gap in front of
  it takes to close, and that latency is on the critical path for the
  consumer, not merely an internal implementation detail.
- The component is stateful in a system that may otherwise be entirely
  stateless, which changes its failure and scaling story. It cannot be
  freely restarted, horizontally duplicated, or load-balanced the way a
  stateless filter can without externalizing that state first.
- A missing unit, whether lost upstream or delayed indefinitely, either
  stalls every unit behind it in the same correlation key forever, or
  requires an explicit timeout policy whose choice of value is a genuine
  trade-off between waiting long enough to be safe and waiting short enough
  to be useful.
- Memory usage is proportional to the depth of disorder, not merely to
  throughput, so a transport that occasionally reorders by a wide margin
  can spike the buffer far beyond its steady-state size.
- Correlation-key partitioning, timeout handling, and duplicate handling
  are each individually simple but together make a correct Resequencer
  noticeably more code and more edge cases than its one-sentence
  description suggests, and a naive implementation that skips any one of
  them tends to work in testing and fail only under production load
  patterns, covered next.

## 11. Failure modes and misuse

**The stuck buffer.** Symptom. Buffer depth for one correlation key climbs
and never falls, while other keys flow normally, and the consumer for that
key stops receiving anything at all. Cause. The unit that would fill the gap
was lost upstream, not merely delayed, and the Resequencer has no timeout or
discard policy, so it waits forever. Fix. Configure an explicit timeout with
a defined discard or escalation path, such as Camel's stream-mode `timeout`
or Spring Integration's `group-timeout` combined with
`send-partial-result-on-expiry`, and alert on buffer age rather than only
buffer depth.

**Resequencing where order does not matter.** Symptom. A Resequencer sits in
front of a consumer that is provably commutative, for example an upsert
keyed by an entity ID where the payload itself carries a timestamp the
database uses for last-write-wins, and the team cannot explain what would
break if it were removed. Cause. The pattern was added by habit or by
copying an existing pipeline, not because the consumer's correctness
actually depends on order. Fix. Remove it and let the idempotent,
order-tolerant consumer absorb the disorder directly, which eliminates
latency and a stateful failure point for zero loss of correctness.

**Single-threaded resequencing collapsing throughput.** Symptom. A pipeline
that previously scaled by adding consumers now bottlenecks on one component,
and adding more consumers upstream of the Resequencer does not improve
throughput, only buffer depth. Cause. Correct resequencing for N independent
correlation keys requires processing them independently. A naive
implementation that resequences the entire stream as one sequence, ignoring
the correlation key, forces every key through one global ordering point.
Fix. Partition the buffer by correlation key, as both Camel's expression-
based grouping and Spring Integration's `correlation-strategy` do by
default, so unrelated sequences never block each other.

**Losing buffered state on restart.** Symptom. Every deployment or pod
restart silently drops in-flight, partially-resequenced units, and the gap
they were waiting to fill never fills because the units on the other side
of the gap already arrived and were discarded from a now-gone in-memory
buffer, or worse, a duplicate of an already-released unit is treated as new
after the restart. Cause. The buffer lives only in process memory with no
externalized state store. Fix. Back the buffer with a durable store, the
seam Spring Integration exposes as `message-store`, and confirm the restart
path actually reloads the buffer rather than merely persisting to a store
nothing reads on startup.

**Silent drop on capacity overflow.** Symptom. Units disappear with no error,
no log line, and no metric, and the team only notices because a downstream
reconciliation job finds a gap in sequence numbers days later. Cause. A
capacity-bounded buffer, such as Camel's stream-mode `capacity`, evicted the
oldest held unit to make room for a new one, and the eviction path was never
wired to a dead-letter channel or a log. Fix. Treat every eviction as an
error-path event with its own observable signal, per dimension 16, never as
a silent no-op.

**Treating batch-mode latency as a bug to route around with a smaller
timeout.** Symptom. `batchTimeout` gets tuned down repeatedly to chase lower
latency, until it is smaller than the actual jitter in the transport, and
the Resequencer starts emitting batches that are still internally
out-of-order because the batch closed before all the late arrivals for that
window showed up. Cause. Batch mode fundamentally trades latency for
simplicity, and no amount of tuning turns it into stream mode's
gap-detecting behavior. Fix. If sub-batch-window latency is required,
switch to stream mode rather than shrinking the batch window past the
point where it still guarantees order.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Resequencer | Aggregator | Idempotent Consumer alone | Sort-based batch step | Single-partition ordered queue |
|---|---|---|---|---|---|
| Restores per-unit order for a live consumer | Yes, that is its purpose | No, combines rather than orders | No, only prevents duplicate side effects | No, only after the whole dataset is closed | Yes, by construction, no buffer needed |
| Added latency per unit | Bounded by gap-close time or batch window | Bounded by group-completion time | None | High, the whole dataset must land first | None beyond the transport itself |
| Memory cost | Proportional to disorder depth | Proportional to group size | None for ordering, some for a dedup index | Proportional to full dataset size | None |
| Handles unbounded or dataset-scale disorder | Poorly, buffer either grows or drops | Poorly, same constraint | Not applicable, does not attempt ordering | Well, that is its design point | Not applicable, disorder cannot occur |
| Requires a durable state store to survive restart | Yes, for correctness across failures | Yes, same reason | Only for the dedup index, not for ordering | No, runs to completion each invocation | No |
| Fits a real-time streaming consumer | Yes, especially in stream mode | Poorly, waits for group completion | Yes, trivially | No, inherently a batch step | Yes, best fit when available |
| Cost when order does not actually matter | Wasted latency and state for no benefit | Not applicable, different purpose | Correct minimal-cost choice | Wasted, unnecessary sort | Not applicable |

Reading of the table. Choose a single-partition ordered queue whenever the
transport can give you the guarantee natively, it is strictly cheaper than
building a Resequencer on top of a transport that could have preserved
order in the first place. Choose Idempotent Consumer alone when the
consumer's correctness does not depend on order, only on not double-applying
a unit. Choose a sort-based batch step when the disorder is not bounded and
the workload is not a live stream. Choose Resequencer specifically when
order matters to a live consumer, the transport cannot guarantee it, and the
disorder is bounded enough for a sized buffer to hold.

## 13. Related and incompatible patterns

- **Aggregator.** The closest sibling and the one most often confused with
  it. Both are stateful filters that collect related messages by a
  correlation key before releasing anything. Aggregator combines the
  collected messages into one new message. Resequencer releases the
  original messages unchanged, only in a different order. A Resequencer
  that starts merging payloads has quietly become an Aggregator and should
  be renamed and documented as one.
- **Message Sequence.** The upstream partner. Message Sequence is how a
  producer marks each unit with the sequence number, position, and total
  count that a downstream Resequencer needs to do its job at all. A
  Resequencer with no Message Sequence metadata to key on cannot function.
  The two patterns are usually implemented together, one on the producer
  side and one on the consumer side of the same integration.
- **Correlation Identifier.** Supplies the grouping key a Resequencer needs
  when more than one logical sequence flows through the same channel. Where
  Message Sequence gives ordering within a group, Correlation Identifier
  gives the grouping itself.
- **Idempotent Consumer.** Frequently paired downstream of a Resequencer
  built on an at-least-once transport, because resequencing order does not
  by itself prevent a redelivered duplicate from being processed twice. The
  Resequencer's duplicate-handling options, `allowDuplicates` and
  `rejectOld`, cited in dimension 8, are a partial substitute but an
  explicit Idempotent Consumer downstream is the more reliable combination.
- **Guaranteed Delivery.** A precondition, not a composed component. If the
  transport can genuinely lose a unit, no Resequencer timeout policy can
  distinguish still-in-flight from gone-forever with certainty, so pairing
  with Guaranteed Delivery removes that ambiguity at the source rather than
  papering over it with a timeout guess.
- **Dead Letter Channel.** The natural destination for the discard or
  escape path named in dimension 5, receiving units that timed out, that
  arrived too old to place, or that overflowed capacity, so they are
  visible and recoverable rather than silently dropped.
- **Message Filter.** An alternative when late arrival makes a unit
  worthless rather than merely delayed. Where Resequencer holds a unit
  hoping to place it correctly, Message Filter discards it outright once a
  freshness threshold passes, and the two are sometimes combined, filtering
  units that are hopelessly stale before they ever reach the resequencing
  buffer.
- **Content-Based Router.** Composes upstream. A router can split traffic
  by correlation key before it reaches a Resequencer, letting each key's
  Resequencer instance run independently rather than sharing one buffer,
  which mitigates the single-threaded-bottleneck failure in dimension 11
  at the infrastructure level rather than the implementation level.

## 14. Refactoring path in and out

Introducing the pattern into a pipeline that does not yet have it.

1. Confirm the ordering assumption is real. Trace one concrete downstream
   effect that breaks if two units are processed out of order, and write it
   down. If nothing breaks, stop here, the pipeline does not need this
   pattern, see the misuse case in dimension 11.
2. Confirm the producer already carries an explicit sequence identifier and
   correlation key on every unit. If it does not, this is a producer-side
   change, adding Message Sequence, and must land before any consumer-side
   resequencing can work at all.
3. Introduce the Resequencer as a pass-through step that does nothing but
   log the observed disorder, buffer depth, and gap duration for a
   representative period in production traffic. This measurement step is
   the only reliable way to size the capacity and timeout parameters in
   step 5, guessing them from first principles routinely gets them wrong by
   an order of magnitude.
4. Choose batch mode or stream mode based on the measurement from step 3.
   If most units already arrive close to order and only a small tail is
   late, stream mode's per-unit gap detection wastes the least latency. If
   disorder is pervasive and roughly window-shaped, batch mode is simpler
   to reason about and to test.
5. Configure capacity and timeout from the measured distribution, not from
   defaults, and wire the discard or timeout path to a Dead Letter Channel
   with its own alert, never to a silent drop.
6. Cut the consumer over to expect strict order, and delete any
   order-tolerance logic the consumer had accumulated as a workaround for
   the disorder the Resequencer now absorbs. Leaving that logic in place is
   not incorrect but it is dead complexity the introduction of this pattern
   was meant to remove.

Removing the pattern when it stops earning its place.

1. Confirm, with the same kind of concrete trace as step 1 above, that the
   consumer no longer has an order dependency, either because the consumer
   was rewritten to be idempotent and order-tolerant, or because the
   transport underneath was changed to guarantee order natively, for
   example by moving a Kafka consumer group to a single partition per key.
2. Measure the Resequencer's buffer depth and average hold time in
   production for a representative window. A depth and hold time near zero
   is strong evidence the transport rarely reorders in practice and the
   pattern may already be doing nothing, independent of consumer
   tolerance.
3. Remove the Resequencer from the pipeline behind a feature flag or a
   staged rollout, watching the same order-dependent trace from step 1 of
   introduction to confirm it still behaves correctly without the buffer.
4. Delete the now-unused correlation and sequence metadata plumbing only
   after confirming no other consumer downstream still depends on it. A
   Resequencer removal is a strictly consumer-side change and should never
   silently remove producer-side Message Sequence metadata that another
   consumer might still need.

## 15. Testing and verification

Easier because of the pattern.

- The Resequencer's contract, given this arrival order produce that release
  order, is a pure function of a sequence of inputs to a sequence of
  outputs, and can be tested with permutations of a fixed input set without
  any real transport, network, or timing dependency.
- Because the buffer state is explicit, a test can assert on buffer
  contents directly after each simulated arrival, rather than only on final
  output, which makes debugging a failing release-order test far faster
  than debugging the same defect if it were smeared across ad hoc ordering
  checks in the consumer.
- Property-based testing fits this pattern unusually well. Generate a
  random permutation of a known sequence, feed it to the Resequencer, and
  assert the output equals the sorted sequence. Run this across thousands
  of permutations including adversarial ones such as full reversal and a
  sequence with the first and last elements swapped.

Harder because of the pattern.

- Timeout and capacity behavior is inherently time-dependent and
  hard to exercise deterministically with real clocks. A Resequencer test
  suite needs a controllable clock or scheduler rather than `sleep` calls,
  or timeout paths will be flaky or effectively untested.
- Multi-key interaction, confirming that one stuck correlation key does not
  block another, requires a test that interleaves two or more correlation
  keys deliberately, which is easy to omit if tests are written one key at
  a time.
- Restart and failover behavior, confirming the durable buffer store
  actually restores in-flight state, requires a test that kills and
  restarts the component mid-sequence, which most unit test setups do not
  naturally exercise.

Techniques that apply.

- **Permutation and property tests**, as described above, for the core
  ordering contract.
- **A fake or injectable clock** for every timeout and capacity-eviction
  test, so a test can advance simulated time deterministically rather than
  waiting on a wall clock.
- **A chaos or fault-injection setup** that deliberately drops a unit
  from the middle of a sequence and asserts the timeout and discard path
  fires correctly, rather than only testing the happy path where every
  unit eventually arrives.
- **A restart test** against a real or embedded instance of the durable
  message store, asserting that a buffer populated before a simulated
  crash is fully present and correctly ordered after the process restarts.

## 16. Observability signals

What to record.

- **Buffer depth per correlation key**, as a gauge, is the single most
  important signal. A healthy Resequencer has this near zero most of the
  time, rising briefly and falling back on each transient reordering event.
- **Hold duration per released unit**, as a histogram, measuring the time
  from a unit's arrival to its release. This is the direct latency cost the
  pattern imposes and should be watched against the SLA the consumer needs.
- **A counter of timeout or capacity-driven discards**, labelled by
  correlation key and reason, because a silent discard is the failure mode
  in dimension 11 that causes the most damage precisely because it produces
  no signal by default.
- **A counter of duplicate or stale units observed**, when `allowDuplicates`
  or `rejectOld`-style handling is in play, so a sudden rise in duplicates
  is visible as evidence of an upstream redelivery storm rather than
  discovered downstream.
- **A gauge of the oldest unresolved gap's age**, per correlation key, which
  is a leading indicator distinct from raw buffer depth. A buffer can be
  small in count but hold one unit that has been waiting a dangerously long
  time.

A healthy instance on a dashboard. Buffer depth per key oscillates near zero
and never grows monotonically. Hold duration is a tight distribution well
under the consumer's latency budget, with an occasional outlier that
resolves quickly. Discard and duplicate counters are flat at or near zero.

A failing instance. Buffer depth for one or more keys climbs without
returning to zero, which points at either a permanently missing unit or the
single-threaded-bottleneck failure from dimension 11. Hold duration
distribution develops a long tail that keeps growing, which usually means
capacity or timeout values were sized from an unrepresentative sample and
production traffic has since drifted. The discard counter, previously flat,
starts climbing, which is the clearest possible signal that upstream
reliability has degraded and the Resequencer's timeout is now doing real
work rather than sitting idle as a safety net.

## 17. Security and privacy implications

The pattern is largely silent on security in its narrowest form, a
component that buffers and reorders opaque units without inspecting their
content. Three implications become genuine once the pattern is deployed in
a real system rather than described in the abstract.

**Buffer exhaustion as a denial-of-service vector.** A Resequencer's memory
usage is proportional to how out of order its input is, not to its
throughput. An attacker who can influence message ordering upstream, for
example by controlling which of several competing consumers or network
paths a message takes, can deliberately widen the observed disorder to grow
the buffer far past its expected steady-state size. Capacity limits,
covered in dimension 8, are a security control as much as a memory control,
and a Resequencer with no bound on buffered units per correlation key, or
no bound on the number of distinct correlation keys tracked concurrently,
is exposed to this even when its throughput looks entirely ordinary.

**Sequence number manipulation.** Because the release decision trusts the
sequence identifier field completely, per dimension 5, any actor who can
forge or replay that field can manipulate release order or force a
particular unit to be held indefinitely by claiming a sequence number that
will never be filled, effectively a targeted denial of service against one
correlation key without needing to flood the whole buffer. Where the
sequence identifier originates outside a trust boundary, it needs the same
authentication and integrity protection as any other trusted input field,
not merely the correlation key or the payload.

**Timing side channels through observable hold duration.** In a system
where an external observer can measure when a unit is released relative to
when it was likely sent, the hold duration itself leaks information about
the presence or absence of other units in the same sequence, and in
adversarial settings, about network conditions or system load an attacker
might otherwise not be able to observe directly. This is a narrow and
usually low-severity concern, worth naming rather than ignoring in any
deployment where the Resequencer sits at a trust boundary and its timing
behavior is externally observable, such as a payment gateway ordering
callback events from an untrusted merchant integration.

On data retention, buffered units are, by definition, held in a store for
longer than a stateless component would ever hold them, which extends the
window during which sensitive payload data sits in memory or in a durable
message store. Any data classification or retention policy applied to the
payload should account for the Resequencer's hold duration, not only for
its final resting place after release.

## 18. References

1. Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns. Designing,
   Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003,
   Message Routing chapter, Resequencer pattern.
2. Enterprise Integration Patterns companion site, "Resequencer",
   https://www.enterpriseintegrationpatterns.com/patterns/messaging/Resequencer.html,
   verified 2026-08-02.
3. Apache Camel Documentation, "Resequence EIP",
   https://camel.apache.org/components/next/eips/resequence-eip.html,
   verified 2026-08-02.
4. Spring Integration Reference Documentation, "Resequencer",
   https://docs.spring.io/spring-integration/reference/resequencer.html,
   verified 2026-08-02.
5. Apache Kafka Javadoc, `org.apache.kafka.streams.kstream.TimeWindows`,
   https://kafka.apache.org/38/javadoc/org/apache/kafka/streams/kstream/TimeWindows.html,
   verified 2026-08-02.
6. H. Schulzrinne, S. Casner, R. Frederick, V. Jacobson, IETF RFC 3550,
   "RTP. A Transport Protocol for Real-Time Applications," Section 5.1,
   https://www.rfc-editor.org/rfc/rfc3550.html, verified 2026-08-02.

## Code examples

Three languages, each showing the stream-mode, contiguous-release variant
from dimension 8, because it is the shape most implementations converge on
and the one that most directly demonstrates the pattern's core mechanism, a
next-expected pointer and a buffer keyed by sequence number. TypeScript and
Python show the same structure in a dynamically typed and a class-based
style respectively. Go shows the same structure using its native map and
struct idioms, with no inheritance to lean on, which is a fair
representation because the pattern does not depend on inheritance in any
language.

### TypeScript

```typescript
type Unit<T> = { seq: number; payload: T };

class StreamResequencer<T> {
  private buffer = new Map<number, T>();
  private nextExpected: number;
  private readonly capacity: number;

  constructor(startAt: number, capacity: number) {
    this.nextExpected = startAt;
    this.capacity = capacity;
  }

  push(unit: Unit<T>): T[] {
    if (unit.seq < this.nextExpected) {
      return [];
    }
    if (!this.buffer.has(unit.seq)) {
      if (this.buffer.size >= this.capacity) {
        throw new Error(`resequencer buffer over capacity at seq=${unit.seq}`);
      }
      this.buffer.set(unit.seq, unit.payload);
    }

    const released: T[] = [];
    while (this.buffer.has(this.nextExpected)) {
      released.push(this.buffer.get(this.nextExpected) as T);
      this.buffer.delete(this.nextExpected);
      this.nextExpected += 1;
    }
    return released;
  }
}

function demo(): void {
  const r = new StreamResequencer<string>(1, 10);
  const arrivals: Array<[number, string]> = [
    [1, "a"],
    [3, "c"],
    [2, "b"],
    [4, "d"],
  ];
  for (const [seq, payload] of arrivals) {
    const released = r.push({ seq, payload });
    if (released.length > 0) {
      console.log(`release: ${released.join(",")}`);
    }
  }
}

demo();
```

### Python

```python
class StreamResequencer:
    def __init__(self, start_at, capacity):
        self._buffer = {}
        self._next_expected = start_at
        self._capacity = capacity

    def push(self, seq, payload):
        if seq < self._next_expected:
            return []
        if seq not in self._buffer:
            if len(self._buffer) >= self._capacity:
                raise RuntimeError(f"resequencer buffer over capacity at seq={seq}")
            self._buffer[seq] = payload

        released = []
        while self._next_expected in self._buffer:
            released.append(self._buffer.pop(self._next_expected))
            self._next_expected += 1
        return released


def demo():
    r = StreamResequencer(start_at=1, capacity=10)
    arrivals = [(1, "a"), (3, "c"), (2, "b"), (4, "d")]
    for seq, payload in arrivals:
        released = r.push(seq, payload)
        if released:
            print(f"release: {','.join(released)}")


if __name__ == "__main__":
    demo()
```

### Go

```go
package main

import "fmt"

type StreamResequencer struct {
	buffer       map[int]string
	nextExpected int
	capacity     int
}

func NewStreamResequencer(startAt, capacity int) *StreamResequencer {
	return &StreamResequencer{
		buffer:       make(map[int]string),
		nextExpected: startAt,
		capacity:     capacity,
	}
}

func (r *StreamResequencer) Push(seq int, payload string) ([]string, error) {
	if seq < r.nextExpected {
		return nil, nil
	}
	if _, exists := r.buffer[seq]; !exists {
		if len(r.buffer) >= r.capacity {
			return nil, fmt.Errorf("resequencer buffer over capacity at seq=%d", seq)
		}
		r.buffer[seq] = payload
	}

	released := []string{}
	for {
		payload, ok := r.buffer[r.nextExpected]
		if !ok {
			break
		}
		released = append(released, payload)
		delete(r.buffer, r.nextExpected)
		r.nextExpected++
	}
	return released, nil
}

func main() {
	r := NewStreamResequencer(1, 10)
	type arrival struct {
		seq     int
		payload string
	}
	arrivals := []arrival{{1, "a"}, {3, "c"}, {2, "b"}, {4, "d"}}
	for _, a := range arrivals {
		released, err := r.Push(a.seq, a.payload)
		if err != nil {
			fmt.Println("error:", err)
			continue
		}
		if len(released) > 0 {
			fmt.Printf("release: %v\n", released)
		}
	}
}
```
