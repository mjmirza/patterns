---
name: Message Sequence
slug: message-sequence
family: 07-integration
category: Integration
aliases: [Multi-Part Message, Sequenced Message, Message Chunking]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [splitter, aggregator, correlation-identifier, competing-consumers, claim-check]
incompatible_with: []
verified: 2026-08-02
---

# Message Sequence

## 1. Name, aliases, and lineage

The canonical name is Message Sequence. It is one of the sixty-five patterns
catalogued in Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns.
Designing, Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003,
in the Message Construction chapter. The pattern's own reference page states
that Bobby Woolf described it and that the book has a first edition from 2003
and a twentieth anniversary edition from 2023, both covering the same pattern
without a change to its intent ([Enterprise Integration Patterns, Message
Sequence](https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessageSequence.html),
verified 2026-08-02).

The pattern shows up under a handful of working names across the industry
literature and the tooling that implements it, and the differences are mostly
cosmetic rather than a sign of a different idea.

- **Multi-Part Message** is the name used when the emphasis is on the payload
  being one logical document cut into physical pieces, the way a mail client
  or an EDI translator would describe a message with attachments split across
  several frames.
- **Sequenced Message** appears in messaging middleware documentation when the
  vendor wants to stress the ordering guarantee rather than the splitting
  mechanism, for example describing a queue feature that preserves the order
  in which segments arrive.
- **Message Chunking** is the term developers reach for informally, borrowed
  from HTTP's chunked transfer encoding, even though HTTP chunking is a
  streaming transport mechanism without the explicit sequence and size
  metadata that the messaging pattern requires. Treating the two as
  interchangeable is a common source of confusion, covered in dimension 11.

Message Sequence sits beside two patterns it is frequently mistaken for. The
Splitter pattern is the mechanism that produces a sequence, turning one
composite message into many, and Message Sequence is the data contract those
produced messages carry so a downstream consumer can reassemble or process
them in order. The Correlation Identifier pattern is the general mechanism for
tagging a group of related messages, and Message Sequence specialises it by
adding position and size or completion information on top of a shared
identifier, so a consumer does not only know two messages are related, it
knows exactly where each one sits in a total ordering.

## 2. Problem and context

A producer has one logical unit of data to move across a messaging channel,
and the unit is larger than the channel, the broker, or the receiving
application can accept as a single message. Message brokers commonly cap
individual message size, JMS providers historically limited practical message
size to a few megabytes for performance reasons, and even brokers without a
hard limit slow down sharply once a single message grows past a modest size
because the broker has to hold the whole payload in memory to route it. The
producer's actual data, a bulk export from a database, a large file transfer,
or the full result set of a query that returned more rows than expected, does
not respect that limit.

The context in which this problem shows up is specifically asynchronous,
message-oriented integration, not request and response over a synchronous
protocol that already streams bytes as a matter of course. A REST API
returning a large JSON body over HTTP can rely on the transport layer's own
chunked or streamed transfer, because the connection itself is a single
ordered byte stream between two parties that stay connected for the duration.
A message channel breaks that assumption. Each message is usually an
independent unit routed, queued, and potentially load balanced across several
consumer instances, with no guarantee that the same physical connection or the
same consumer instance handles message two after it handled message one. The
producer therefore needs a way to say, inside the messaging system's own data
model rather than relying on the transport, that these particular messages
belong together and belong in a specific order, so that whichever consumer
eventually reads them can reconstruct the original unit correctly regardless
of how the broker delivered or distributed them.

The pattern also shows up in the mirror-image situation, where the receiver
rather than the sender needs to send a lot of data back. A request-reply
exchange whose reply payload is large runs into the same channel-size
constraint on the return trip, and the reply has to be broken into a sequence
using the same mechanism, correlated back to the original request through a
Correlation Identifier while carrying its own sequence metadata for the
returned chunks.

## 3. Forces

**Message size against broker and network limits.** The producer wants to
send the data as one unit conceptually, but the infrastructure imposes a
cap. Splitting relieves the cap at the cost of a reassembly step the
producer would rather not build.

**Ordering guarantees against broker delivery semantics.** Many message
brokers do not guarantee the order in which messages are delivered to
consumers, particularly once more than one consumer is reading from the same
channel for throughput. Message Sequence pushes the ordering responsibility
into the payload itself, at the cost of the consumer doing reordering work
that a strictly ordered channel would have done for free.

**Consumer-side state against statelessness.** A consumer that must
reassemble a sequence has to hold partial state, buffering earlier parts
until the missing ones arrive, which conflicts with the common goal of
keeping message consumers stateless, so that more instances can be started or
stopped freely to match load. Every part of a sequence has to land at a
consumer instance that shares that buffered state, which is itself a routing
and scaling constraint (see Failure Modes, dimension 11).

**Simplicity against completeness detection.** The pattern needs a way to
know a sequence is finished, either an explicit total count sent with every
message or an explicit end-of-sequence flag on the last one. A fixed count
known in advance is simple but breaks if the producer discovers the true size
only partway through generation, such as streaming rows out of a query it is
still executing. An end marker handles the unknown-size case but leaves the
consumer unable to detect that a message went missing in the middle, only
that the sequence never terminated.

**Latency against completeness.** A consumer that must wait for the whole
sequence before acting on any of it trades responsiveness for correctness.
Some designs let the consumer act on each part as it arrives, which favours
latency and forces the design to tolerate partial, in-progress state as a
first-class condition rather than an edge case.

**Cost of failure handling against simplicity.** Deciding what happens when a
part never arrives, whether to time out, request retransmission, or discard
the entire partial sequence, adds real design and operational cost. Systems
that never define this policy explicitly tend to discover the answer during
an incident rather than during design.

## 4. Applicability and non-applicability

Reach for Message Sequence when all of the following hold.

- The payload genuinely exceeds a size limit imposed by the broker, the
  network, or the consuming application, and that limit is not something the
  team controls or wants to raise.
- The messages must travel over an asynchronous channel where the transport
  itself gives no ordering or streaming guarantee, so the ordering has to
  live in the message data.
- The receiving side is able to buffer and reassemble, either because it is a
  single consumer instance per sequence or because the architecture routes an
  entire sequence to the same consumer instance deterministically.
- The producer can reliably assign a stable sequence identifier and either
  a known total count or a reliable end-of-sequence indicator before or during
  production.

Do not reach for it in these situations, and prefer the alternative named.

- **The payload is large but the transport already streams.** Over HTTP, gRPC,
  or a raw TCP socket held open for the duration of the transfer, the
  transport's own streaming or chunked-encoding mechanism already delivers
  ordered bytes without an application-level sequence contract. Building
  Message Sequence on top of an already-streaming transport duplicates work
  the transport does for free and adds a reassembly step that was
  unnecessary.
- **The data does not need to stay ordered or reassembled as one unit.** If
  the real requirement is simply to process many independent items faster,
  the correct pattern is the Splitter feeding a pool of workers under
  Competing Consumers, with no sequence tracking at all, because there is no
  original composite unit to reconstruct.
- **The payload is large because it references bulk data rather than
  containing it.** When the actual bytes are a file, an image, or a large
  blob, Claim Check is the better fit. Store the blob out of band and pass a
  reference through the message channel, keeping every message small instead
  of chopping the blob into a sequence of message-sized fragments.
- **The broker supports message compression or a larger message-size tier
  that comfortably fits the payload.** If simply raising a configuration
  limit or turning on compression solves the size problem without touching
  the application, that is a cheaper fix and should be tried first, because
  Message Sequence adds permanent consumer-side complexity that outlives the
  original size constraint.
- **Exactly one consumer instance can never be guaranteed to see every part
  of a given sequence**, and the system has no mechanism, such as a partition
  key, sticky routing, or an external correlation store, to guarantee it.
  Without that guarantee the pattern degrades into parts being buffered
  nowhere or buffered redundantly across instances, which is a reliability
  regression, not an improvement.

## 5. Structure

**Producer.** The originating component that has one logical unit of data
larger than the channel accepts. It is responsible for deciding the
partitioning of that data into ordered parts and for stamping each part with
the sequence metadata below before sending.

**Message part.** Each individual message in the sequence, carrying three
pieces of sequence metadata in addition to its normal payload and headers.

- **Sequence identifier.** A value shared by every part of one sequence and
  distinct from the identifier of any other sequence in flight, so a consumer
  seeing many interleaved sequences from many producers can tell which parts
  belong together. This is the Correlation Identifier applied specifically to
  sequence membership.
- **Position indicator.** The part's own place in the ordering, most commonly
  a one-based or zero-based integer index, sometimes expressed as an
  explicit predecessor or successor reference instead of a raw index.
- **Size or completion indicator.** Either the total count of parts in the
  sequence, known up front and repeated on every part, or a boolean or marker
  flag set only on the final part, used when the total count is not known
  until production finishes.

**Consumer.** The receiving component that reads parts, groups them by
sequence identifier, holds the ones that have arrived out of order, and
either reassembles the complete original unit before acting or processes each
part in order as it becomes available, depending on the variant chosen
(dimension 8).

**Sequence store.** The buffering structure the consumer uses to hold
partially arrived sequences, whether that is in-memory state inside a single
consumer process, a shared external store such as a database table or a
distributed cache keyed by sequence identifier, or the built-in windowing
state of a stream-processing framework's aggregation operator.

**Timeout or cleanup policy.** A bound on how long the consumer will wait for
missing parts of an incomplete sequence before declaring it failed, discarded,
or escalated, without which a lost or never-sent part leaves buffered state
accumulating forever.

## 6. ASCII structure diagram

```
+-----------+     splits one unit into N ordered parts
| Producer  |------------------------------------------------+
+-----------+                                                 |
                                                                v
                    +---------------------------------------------+
                    |               Message Channel                |
                    |  each part carries: seqId, position, total  |
                    +---------------------------------------------+
                        |            |            |            |
                        v            v            v            v
                   +--------+   +--------+   +--------+   +--------+
                   | part 1 |   | part 2 |   | part 3 |   | part 4 |
                   | pos=1  |   | pos=2  |   | pos=3  |   | pos=4  |
                   | of=4   |   | of=4   |   | of=4   |   | of=4   |
                   +--------+   +--------+   +--------+   +--------+
                        \            \            /            /
                         \            \          /            /
                          v            v        v            v
                         +-------------------------------------+
                         |         Consumer / Aggregator        |
                         |  buckets parts by seqId, orders by   |
                         |  position, waits for total or end    |
                         |  marker before releasing the unit    |
                         +-------------------------------------+
                                         |
                                         v
                              +-----------------------+
                              | Reassembled original   |
                              | logical unit            |
                              +-----------------------+
```

## 7. Dynamics

```
Producer                Channel                 Consumer
   |                       |                        |
   |-- part(seqId=A,      |                        |
   |    pos=1, total=4) -->|                        |
   |                       |-- deliver ------------->|  buffer: {1}
   |                       |                        |  waiting for 2,3,4
   |-- part(seqId=A,      |                        |
   |    pos=3, total=4) -->|                        |
   |                       |-- deliver ------------->|  buffer: {1,3}
   |                       |                        |  (out of order, held)
   |-- part(seqId=A,      |                        |
   |    pos=2, total=4) -->|                        |
   |                       |-- deliver ------------->|  buffer: {1,2,3}
   |                       |                        |  reorder 1,2,3
   |-- part(seqId=A,      |                        |
   |    pos=4, total=4) -->|                        |
   |                       |-- deliver ------------->|  buffer: {1,2,3,4}
   |                       |                        |  total=4 satisfied
   |                       |                        |  -> reassemble, emit
   |                       |                        |  -> clear buffer for A
```

A second, equally common dynamic uses an end-of-sequence flag instead of a
known total, which changes only the release condition, not the buffering and
reordering behaviour.

```
Producer                Channel                 Consumer
   |                       |                        |
   |-- part(seqId=B,      |                        |
   |    pos=1, last=false)-->|                      |  buffer: {1}
   |-- part(seqId=B,      |                        |
   |    pos=2, last=false)-->|                      |  buffer: {1,2}
   |-- part(seqId=B,      |                        |
   |    pos=3, last=true) -->|                      |  buffer: {1,2,3}
   |                       |                        |  last=true seen at
   |                       |                        |  pos=3, and 1..3 are
   |                       |                        |  contiguous
   |                       |                        |  -> reassemble, emit
```

The dynamics diagram deliberately shows the out-of-order arrival at position
three before position two, because a consumer implementation that assumes
strict channel ordering is the single most common defect in real Message
Sequence code, addressed directly in dimension 11.

## 8. Implementation variants

**Fixed-count sequence, buffer-then-release.** The producer knows the total
part count before sending the first part, includes it on every part, and the
consumer buffers all parts and only acts once every position from one through
the total has arrived. This is the simplest variant to reason about and the
one most integration frameworks implement as their default aggregation
strategy, because the release condition is a plain count comparison.

**Unknown-count sequence with an end marker.** The producer streams parts as
it generates them, without knowing in advance how many there will be, for
example while paging through a database cursor of unknown final size, and
marks only the last part with a completion flag. The consumer must track
contiguity as well as the end marker, because seeing the end marker at
position seven does not confirm positions one through six all arrived, only
that seven was the last one sent.

**Streaming, act-as-you-go.** Instead of buffering until the whole sequence
is present, the consumer processes each part as it arrives in the correct
order, holding only the parts that have arrived early relative to the next
expected position, and releasing buffered parts to processing as soon as the
gap closes. This trades a larger, simpler all-or-nothing memory footprint for
lower latency to first processed part, at the cost of a design that has to
define what it means for a partial commit to already be visible downstream
when the sequence later turns out to be incomplete.

**Windowed aggregation in a stream-processing framework.** Frameworks built
around continuous event streams implement essentially the same buffer-order-
release logic as a built-in operator, keyed by the sequence identifier and
governed by a size or time-based completion condition rather than hand-rolled
buffering code. The application supplies the key extraction and the
completion predicate; the framework supplies the state store, the timers, and
the exactly-once or at-least-once delivery semantics around it.

**Persisted correlation table instead of in-memory buffer.** When a single
consumer process cannot be guaranteed to see every part of a sequence,
because the deployment runs many consumer instances at once without
partition affinity, the buffer moves out of process memory and into a shared
database table or distributed cache keyed by sequence identifier, so any
consumer instance that reads a part can check and update the shared state
regardless of which instance handled an earlier part. This variant sacrifices
the simplicity of in-memory buffering for correctness when the consumer count
changes, and it needs its own locking or optimistic-concurrency discipline to
avoid two instances racing to release the same completed sequence twice.

**Header-carried metadata against envelope-carried metadata.** Some
implementations put the sequence identifier, position, and total in message
headers or properties, keeping the payload untouched and letting
infrastructure such as a message router act on the sequence metadata without
parsing the body. Others embed the same fields inside a structured envelope
wrapping the payload, which is more portable across transports that do not
support rich headers but requires every consumer to parse the envelope
before it can even see the sequence metadata.

## 9. Known production uses

**Apache Camel's Splitter EIP.** Camel's implementation of the Splitter
pattern, which produces a Message Sequence as its output, stamps three
exchange properties on every sub-message it creates, `CamelSplitIndex`, "A
split counter that increases for each Exchange being split. The counter
starts from 0", `CamelSplitSize`, "The total number of Exchanges that was
split", and `CamelSplitComplete`, "Whether this Exchange is the last"
([Apache Camel documentation, Split
EIP](https://camel.apache.org/components/latest/eips/split-eip.html),
verified 2026-08-02). This is a direct, named implementation of the
fixed-count and completion-flag metadata from dimension 5, wired into a
widely deployed open-source integration framework.

**Apache Kafka's idempotent producer.** Kafka attaches a producer identifier
and, per the design document for the feature, "for a given PID, sequence
numbers will start from zero and be monotonically increasing, with one
sequence number per topic partition produced to." The broker enforces
ordering and gap detection using that sequence number. "The broker maintains
in memory the sequence numbers it receives for each topic partition from
every PID. The broker will reject a produce request if its sequence number is
not exactly one greater than the last committed message from that PID or
TopicPartition pair", distinguishing a lower, duplicate sequence number from
a higher, out-of-sequence one that signals lost messages ([Apache Kafka,
KIP-98, Exactly Once Delivery and Transactional
Messaging](https://cwiki.apache.org/confluence/display/KAFKA/KIP-98+-+Exactly+Once+Delivery+and+Transactional+Messaging),
verified 2026-08-02). This is not the Message Sequence pattern used to split
one oversized logical payload the way Camel's Splitter is, but it is the
identical structural idea, a monotonic position value scoped by an identifier
and validated for contiguity, applied to a different problem. It detects
duplicate or lost delivery rather than reassembling a payload, and it is
included here because it is the clearest large-scale production evidence
that the position-plus-identifier contiguity check from dimension 5 and
dimension 7 is a real, load-bearing mechanism in a widely operated system,
not a textbook abstraction.

**Amazon SQS FIFO queue message groups.** Amazon's managed queue service
documents that "in FIFO (First-In-First-Out) queues, MessageGroupId is an
attribute that organizes messages into distinct groups. Messages within the
same message group are always processed one at a time, in strict order."
`MessageGroupId` plays the role of the sequence identifier from dimension 5,
and no two messages from the same group are ever processed at the same time,
so SQS's own ordering guarantee inside a group takes over the position-
tracking work a hand-rolled Message Sequence consumer would otherwise have to
do itself ([AWS documentation, Using the message group ID with Amazon SQS
FIFO
Queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/using-messagegroupid-property.html),
verified 2026-08-02). This is a concrete production example of the pattern's
ordering half being absorbed directly into the messaging infrastructure
rather than the application layer, addressed further in dimension 14.

## 10. Consequences

**Positive.**

- Removes the hard cap on how much logical data one producer-to-consumer
  interaction can move over a size-limited asynchronous channel, without
  requiring the broker itself to change its limits.
- Keeps every individual message small enough to route, persist, and retry
  cheaply, which is friendlier to broker throughput and to per-message retry
  and dead-letter mechanisms than one giant message would be.
- Makes ordering an explicit, inspectable property of the data rather than an
  implicit assumption about channel behaviour, so a consumer can detect
  reordering, duplication, or loss directly from the metadata instead of
  trusting the transport.
- Enables a streaming, act-as-you-go consumer design when latency to first
  usable result matters more than having the whole unit available at once.

**Negative.**

- Moves ordering and completeness responsibility onto the consumer, which now
  needs buffering state, a reassembly algorithm, and a policy for missing or
  duplicate parts, none of which existed before the split.
- Introduces a new failure mode, the incomplete sequence, that a single
  unsplit message could never have, along with the operational question of
  how long to wait and what to do when a part never arrives.
- Requires either sticky routing of every part in a sequence to the same
  consumer instance or a shared, externally visible correlation store, both
  of which are additional infrastructure and additional coordination cost
  compared to a stateless one-message-in, one-message-out consumer.
- Couples producer and consumer to a shared sequence-metadata contract, which
  becomes another interface that has to be versioned and kept compatible
  alongside the payload schema itself.

## 11. Failure modes and misuse

**Symptom.** A consumer occasionally drops or silently skips a legitimate
sequence, with no error logged.
**Cause.** The consumer's release condition compares the buffered count to
the declared total, but never checks that positions one through total are
actually the ones present, only that the count matches. A duplicate delivery
of one position combined with a genuine loss of another produces the correct
count with the wrong membership, and the sequence releases as if it were
whole.
**Fix.** Track the actual set of positions seen, not merely a counter, and
release only when that set exactly equals the expected range or contiguous
run, per the dynamics shown in dimension 7.

**Symptom.** Memory usage on the consumer grows without bound over time, and
eventually the process is killed for exhausting available memory, seemingly
unrelated to overall message volume.
**Cause.** No timeout policy exists for incomplete sequences. A sequence
whose producer crashed, or whose last part was dropped by an upstream retry
mechanism that silently deduplicated it, sits in the buffer forever, and
every such orphaned sequence accumulates alongside all the others over the
life of the process.
**Fix.** Attach an expiry to every buffered sequence, and run a background
sweep that discards or escalates sequences that have not received a new part
within the timeout, per the sequence store and cleanup policy described in
dimension 5.

**Symptom.** The same reassembled unit is processed, and its side effects
applied, more than once.
**Cause.** The completion condition is checked and the reassembled unit is
released for processing without the check-and-clear being atomic. Two threads
or two consumer instances each observe the sequence as complete at nearly the
same moment, both proceed to reassemble and emit, and the shared buffer clear
happens after both have already acted.
**Fix.** Make the transition from incomplete to complete, and the clearing of
the buffer, a single atomic operation, whether that is a lock inside one
process or an optimistic-concurrency update against the shared correlation
table described in the persisted-buffer variant of dimension 8.

**Symptom.** A sequence that was clearly complete in the producer's logs
never triggers reassembly on the consumer, and the buffer for it sits full
but inert.
**Cause.** Message Sequence was confused with a transport-level chunking
mechanism such as HTTP chunked transfer encoding, and the code assumes the
channel itself will guarantee that all parts of a sequence land at the same
consumer instance in order, the way HTTP chunks arrive at one open
connection. On a load-balanced queue, later parts land at a different
consumer instance than the one holding the partial buffer, and neither
instance ever sees a full set.
**Fix.** Route by sequence identifier, either through partition-key-aware
consumer assignment or through the shared correlation-table variant, so
membership in the same sequence guarantees visibility to the same buffering
state regardless of which physical consumer instance handles which part.

**Symptom.** Two entirely unrelated logical units get merged into one
reassembled result, corrupting both.
**Cause.** The sequence identifier is not actually unique across the
producer's lifetime, for example a naive incrementing integer that wraps or
resets, or a timestamp with insufficient resolution reused by two sequences
started in the same millisecond, so two genuinely distinct sequences collide
on the same identifier in the consumer's buffer.
**Fix.** Generate sequence identifiers with enough entropy or enough
namespace scoping, such as a UUID or a producer-instance-qualified counter,
that collision across concurrently in-flight sequences is not a realistic
occurrence, and validate that assumption under the actual concurrency level
the system runs at rather than assuming it.

## 12. Trade-off matrix

| Force | Message Sequence | Splitter feeding Competing Consumers (no reassembly) | Claim Check |
|---|---|---|---|
| Payload size handled | Large logical unit split into ordered small parts | Independent items processed in parallel, no size cap per item | Small reference message, actual bulk data stored out of band |
| Ordering guarantee | Explicit, carried in the payload metadata, consumer enforces it | None needed, items are independent by design | Not applicable, one message per reference |
| Consumer state required | Buffering per in-flight sequence, plus a completeness policy | None, each message is processed and forgotten independently | None, consumer fetches the referenced data on demand |
| Failure mode introduced | Incomplete or duplicated sequences, orphaned buffers | Individual item failure only, isolated per message | Broken or expired reference to the stored blob |
| Best fit | One logical unit must be reconstructed intact and in order | Many independent items that never need to be reassembled | Payload is bulk data (file, blob) rather than many ordered pieces |
| Infrastructure cost | Sequence store, timeout sweeper, correlation routing | Worker pool and load balancing only | External blob store and its own access control |

## 13. Related and incompatible patterns

**Splitter.** The producing half of the pipeline that most often generates a
Message Sequence. Splitter is the mechanism that turns one composite message
into many; Message Sequence is the metadata contract those many messages
carry so a consumer can tell they came from the same split and in what order.
A Splitter does not have to produce a Message Sequence if the resulting parts
are independent and never need reassembly, which is exactly the
non-applicability case in dimension 4.

**Aggregator.** The consuming counterpart that implements the buffer-order-
release logic described in dimension 7 and dimension 8. In integration
framework terminology, an Aggregator is the general pattern for combining
related messages into one, and a Message-Sequence-aware Aggregator is simply
an Aggregator whose completeness condition requires all positions from one
through the declared total, or up to the end marker, to have arrived, rather
than some other grouping rule such as a fixed time window or a fixed count
with no ordering requirement.

**Correlation Identifier.** Message Sequence's sequence identifier is a
direct application of Correlation Identifier, specialised to mean membership
in the same ordered group rather than the more general response to the same
request use that Correlation Identifier most commonly serves in request-reply
scenarios. Every Message Sequence implementation needs a Correlation
Identifier; not every Correlation Identifier use case needs sequence position
and completeness metadata on top.

**Competing Consumers.** These two patterns are frequently deployed together
and require care where they interact. Competing Consumers raises throughput
by letting several consumer instances pull from the same channel, which is
exactly the situation that breaks a naive in-memory Message Sequence buffer,
as described in dimension 11's routing failure mode. The two compose safely
only when sequence membership is routed deterministically to the same
consumer instance, or when the buffer lives in a shared store visible to
every competing consumer instance.

**Claim Check.** An alternative rather than a companion in the common case
where the oversized payload is a single blob rather than many logically
ordered pieces. Where Message Sequence chops the blob into a sequence of
message-sized fragments and asks the consumer to reassemble them, Claim Check
stores the blob once, outside the messaging channel, and passes a small
reference. The two are not incompatible; a system can use Claim Check for the
bulk data and still use Message Sequence for an unrelated stream of naturally
ordered events, but applying both to the same oversized-blob problem is
redundant, and Claim Check is almost always the simpler and cheaper choice
for that specific problem, per the non-applicability discussion in dimension
4.

**Request-Reply.** Message Sequence composes with Request-Reply when a reply
payload itself is too large for one message, in which case the reply is sent
as a sequence correlated back to the original request identifier as well as
carrying its own internal sequence identifier for the reply parts, effectively
nesting one Correlation Identifier scheme inside another.

## 14. Refactoring path in and out

**Introducing it into a system that currently sends one oversized message per
logical unit.** Start by confirming the size limit that is actually being
hit and whether raising a broker configuration limit or enabling compression
resolves the immediate pain more cheaply, per dimension 4's non-applicability
guidance, before committing to the pattern. If the limit is structural rather
than configurable, define the sequence identifier scheme first, in isolation,
and prove it generates collision-free identifiers under the system's real
concurrency before touching the splitting logic, because a broken identifier
scheme corrupts data quietly rather than failing loudly (dimension 11). Next,
introduce the Splitter on the producer side behind a feature flag or a
parallel code path, so the old single-message path and the new sequence path
can run side by side during rollout and be compared. On the consumer side,
build the Aggregator with an explicit timeout and an explicit metric for
incomplete sequences before switching real traffic over, since the
operational visibility into incomplete sequences is what turns dimension 11's
failure modes from a silent data-corruption incident into a monitored,
recoverable condition. Only after the consumer's completeness detection and
cleanup have been observed working correctly under the parallel path should
the old single-message path be retired.

**Removing it once it stops earning its place.** The two situations that most
often make this pattern removable are the underlying size constraint going
away, for instance a broker migration or configuration change that raises the
practical message-size cap above what the payloads actually need, or a
transport migration onto something that already streams on its own, such as moving a
bulk transfer off a message queue and onto a service that already streams,
which removes the need for application-level sequencing entirely. Before
removing it, confirm no downstream consumer has grown a dependency on the
sequence metadata itself for something other than reassembly, such as using
the position field for progress reporting or the completion flag as a
trigger for an unrelated side effect, because those secondary uses will break
silently if the sequence fields simply stop being populated. Remove the
consumer-side Aggregator and its buffering state first, verify no incomplete-
sequence metric or alert still exists to fire on their absence, and only then
remove the producer-side Splitter and the sequence-identifier generation,
reverting to single, unsplit messages.

## 15. Testing and verification

Testing a Message Sequence implementation is easier in one respect and harder
in another compared with ordinary stateless message handling. It is easier
because the producer side is a pure function from one input to a list of
ordered outputs and is straightforward to unit test with exact assertions on
position and total fields for a range of input sizes, including the boundary
case of a single-part sequence and the case of a sequence whose size is not
evenly divisible by whatever chunking rule the producer uses. It is harder
because the consumer side is necessarily stateful and has to be exercised
against the actual failure conditions from dimension 11, not only the happy
path of parts arriving once, in order.

The consumer's test suite should include, at minimum, parts arriving in
reverse order, parts arriving with one position genuinely missing followed by
a timeout, a duplicate delivery of one position while the rest of the
sequence is otherwise complete, two distinct sequences with interleaved
delivery of their parts to confirm the buffer keeps them separate by
identifier, and the release-once-not-twice race condition from dimension 11
under concurrent delivery, which usually requires an explicit test that
delivers the final part from two threads or two simulated consumer instances
simultaneously and asserts the downstream side effect happened exactly once.
A test double that plays back a scripted, deliberately reordered and
deliberately incomplete delivery sequence against the real Aggregator code is
more valuable here than a mock of the broker itself, because the behaviour
under test is the state machine's response to disorder, not the wiring to the
transport.

Contract tests between producer and consumer teams should assert on the
sequence-identifier generation scheme's uniqueness property under load,
because that property is exactly the kind of thing that looks fine in every
manual test and fails only under real concurrent traffic, matching the
identifier-collision failure mode in dimension 11.

## 16. Observability signals

The single most useful metric is a live count or gauge of currently
incomplete, buffered sequences, broken down by how long each has been
incomplete, since a healthy system's buffer should be small and short-lived,
with most sequences completing within a bounded window measured in the
normal delivery latency of the channel, while a system with a routing or
delivery problem shows that gauge climbing steadily or accumulating a long
tail of sequences stuck well past their expected completion time. Alongside
that gauge, count sequences that were released after the timeout as
incomplete or discarded, distinct from sequences that completed normally,
because a nonzero and growing rate of timeout-based discards is the earliest
observable sign of the missing-part failure mode from dimension 11, well
before it shows up as a downstream data-quality complaint.

Log, at minimum, the sequence identifier, the total expected count or the
completion-marker state, and the set of positions actually received, at the
moment a sequence is released, whether it was released as complete or
discarded as incomplete, so an incident investigation can reconstruct exactly
what the consumer saw for any specific sequence identifier after the fact.
Trace each part of a sequence with the sequence identifier attached as a
correlation field in distributed tracing, so a single trace query can pull up
every part of one logical unit's path from producer through channel to
consumer, which is the practical equivalent for asynchronous flows of a
request trace in a synchronous system.

A healthy dashboard for this pattern shows the incomplete-sequence gauge
staying near a small, roughly constant baseline proportional to normal
in-flight traffic, a near-zero rate of timeout discards, and a completion
latency distribution with a tight, bounded tail. A failing instance shows the
gauge trending upward without bound, a rising rate of timeout discards, or a
completion latency distribution whose tail stretches out toward the timeout
threshold itself, which usually indicates a routing problem sending parts
of the same sequence to different consumer instances that never share state.

## 17. Security and privacy implications

Buffering partial sequences in memory or in a shared correlation store means
sensitive payload fragments persist in that buffer for the duration of the
incomplete window, which extends the window during which that data is
readable by anything with access to the consumer process's memory or to the
shared store, compared with a design where each message is processed and
discarded immediately on arrival. Any data-retention or purge policy that
applies to the payload itself needs to also apply to the buffered, not-yet-
released partial state, and the timeout sweep from dimension 11 should be
treated as a data-lifecycle control, not only an operational one, particularly
for payloads subject to a regulatory data-minimisation requirement.

The sequence identifier itself is, in effect, a routing key visible to
anything that can observe the channel, including any broker-level monitoring
or logging that captures headers, and if that identifier is derived in a way that can be guessed from information such as a customer account number or an
incrementing counter tied to real-world volume, an observer with channel
visibility can infer activity patterns, such as the approximate size or
frequency of a given producer's logical units, from the sequence metadata
alone even without decrypting the payload. Where that inference is a genuine
concern, the sequence identifier should be generated with the same care given
to any other identifier exposed on the wire, independent from any internally
significant counter or account reference.

A shared correlation store used by the persisted-buffer variant from
dimension 8 is a new piece of infrastructure holding, at minimum, sequence
identifiers and possibly partial payload data, and it needs the same access
control review as any other data store in the system rather than being
treated as incidental plumbing, since it is functioning as a temporary cache
of in-flight, potentially sensitive data.

## 18. References

- Gregor Hohpe, Bobby Woolf, *Enterprise Integration Patterns. Designing,
  Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003, Message
  Construction chapter, Message Sequence.
- Enterprise Integration Patterns, [Message
  Sequence](https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessageSequence.html),
  verified 2026-08-02.
- Apache Camel documentation, [Split
  EIP](https://camel.apache.org/components/latest/eips/split-eip.html),
  verified 2026-08-02.
- Apache Kafka, [KIP-98, Exactly Once Delivery and Transactional
  Messaging](https://cwiki.apache.org/confluence/display/KAFKA/KIP-98+-+Exactly+Once+Delivery+and+Transactional+Messaging),
  verified 2026-08-02.
- AWS documentation, [Using the message group ID with Amazon SQS FIFO
  Queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/using-messagegroupid-property.html),
  verified 2026-08-02.

## Code examples

### TypeScript

```typescript
interface SequencePart<T> {
  sequenceId: string;
  position: number;
  total: number;
  payload: T;
}

class SequenceAggregator<T> {
  private buffers = new Map<string, Map<number, T>>();
  private totals = new Map<string, number>();

  accept(part: SequencePart<T>): T[] | null {
    if (!this.buffers.has(part.sequenceId)) {
      this.buffers.set(part.sequenceId, new Map());
      this.totals.set(part.sequenceId, part.total);
    }
    const bucket = this.buffers.get(part.sequenceId)!;
    bucket.set(part.position, part.payload);

    const expected = this.totals.get(part.sequenceId)!;
    if (bucket.size !== expected) {
      return null;
    }
    for (let i = 1; i <= expected; i++) {
      if (!bucket.has(i)) {
        return null;
      }
    }
    const ordered: T[] = [];
    for (let i = 1; i <= expected; i++) {
      ordered.push(bucket.get(i) as T);
    }
    this.buffers.delete(part.sequenceId);
    this.totals.delete(part.sequenceId);
    return ordered;
  }
}

function splitIntoSequence<T>(sequenceId: string, items: T[]): SequencePart<T>[] {
  return items.map((payload, index) => ({
    sequenceId,
    position: index + 1,
    total: items.length,
    payload,
  }));
}

const parts = splitIntoSequence("seq-A", ["row1", "row2", "row3"]);
const aggregator = new SequenceAggregator<string>();
const shuffled = [parts[1], parts[0], parts[2]];
let result: string[] | null = null;
for (const p of shuffled) {
  result = aggregator.accept(p);
}
console.log(result);
```

### Python

```python
from dataclasses import dataclass
from typing import Generic, TypeVar, Optional

T = TypeVar("T")


@dataclass
class SequencePart(Generic[T]):
    sequence_id: str
    position: int
    total: int
    payload: T


class SequenceAggregator(Generic[T]):
    def __init__(self) -> None:
        self._buffers: dict[str, dict[int, T]] = {}
        self._totals: dict[str, int] = {}

    def accept(self, part: SequencePart[T]) -> Optional[list[T]]:
        bucket = self._buffers.setdefault(part.sequence_id, {})
        self._totals[part.sequence_id] = part.total
        bucket[part.position] = part.payload

        expected = self._totals[part.sequence_id]
        if len(bucket) != expected:
            return None
        if not all(i in bucket for i in range(1, expected + 1)):
            return None

        ordered = [bucket[i] for i in range(1, expected + 1)]
        del self._buffers[part.sequence_id]
        del self._totals[part.sequence_id]
        return ordered


def split_into_sequence(sequence_id: str, items: list[T]) -> list[SequencePart[T]]:
    total = len(items)
    return [
        SequencePart(sequence_id, position=i + 1, total=total, payload=item)
        for i, item in enumerate(items)
    ]


if __name__ == "__main__":
    parts = split_into_sequence("seq-A", ["row1", "row2", "row3"])
    aggregator: SequenceAggregator[str] = SequenceAggregator()
    shuffled = [parts[1], parts[0], parts[2]]
    result = None
    for p in shuffled:
        result = aggregator.accept(p)
    print(result)
```

### Go

```go
package main

import "fmt"

type SequencePart struct {
	SequenceID string
	Position   int
	Total      int
	Payload    string
}

type SequenceAggregator struct {
	buffers map[string]map[int]string
	totals  map[string]int
}

func NewSequenceAggregator() *SequenceAggregator {
	return &SequenceAggregator{
		buffers: make(map[string]map[int]string),
		totals:  make(map[string]int),
	}
}

func (a *SequenceAggregator) Accept(part SequencePart) []string {
	bucket, ok := a.buffers[part.SequenceID]
	if !ok {
		bucket = make(map[int]string)
		a.buffers[part.SequenceID] = bucket
	}
	a.totals[part.SequenceID] = part.Total
	bucket[part.Position] = part.Payload

	expected := a.totals[part.SequenceID]
	if len(bucket) != expected {
		return nil
	}
	for i := 1; i <= expected; i++ {
		if _, present := bucket[i]; !present {
			return nil
		}
	}
	ordered := make([]string, 0, expected)
	for i := 1; i <= expected; i++ {
		ordered = append(ordered, bucket[i])
	}
	delete(a.buffers, part.SequenceID)
	delete(a.totals, part.SequenceID)
	return ordered
}

func splitIntoSequence(sequenceID string, items []string) []SequencePart {
	total := len(items)
	parts := make([]SequencePart, total)
	for i, item := range items {
		parts[i] = SequencePart{
			SequenceID: sequenceID,
			Position:   i + 1,
			Total:      total,
			Payload:    item,
		}
	}
	return parts
}

func main() {
	parts := splitIntoSequence("seq-A", []string{"row1", "row2", "row3"})
	aggregator := NewSequenceAggregator()
	shuffled := []SequencePart{parts[1], parts[0], parts[2]}
	var result []string
	for _, p := range shuffled {
		if r := aggregator.Accept(p); r != nil {
			result = r
		}
	}
	fmt.Println(result)
}
```

Java and Rust are natural fits for this pattern too, Java through the same
`Map`-of-positions bucket shape used above and Rust through a `HashMap`
keyed by sequence identifier holding a `BTreeMap` of position to payload so
contiguity can be checked cheaply, but three verified, runnable examples are
included here and a reader extending this entry to those languages should
follow the identical buffer-order-release shape shown above rather than
inventing a new one. Swift is a reasonable fit on Apple platforms for the
producer side, generating sequence parts before handing them to a messaging
client, but the pattern itself is not idiomatic to any one platform's
concurrency model, so it is omitted here in favour of the three shown.

All three examples above were run directly. TypeScript was compiled and
executed with `npx tsc` followed by `node`, producing `[ 'row1', 'row2',
'row3' ]` after being fed the parts out of order. Python was run with
`python3`, producing `['row1', 'row2', 'row3']`. Go was run with `go run`,
producing `[row1 row2 row3]`. Each program deliberately delivers position two
before position one to exercise the reordering and completeness logic from
dimension 7, not only the happy path.
