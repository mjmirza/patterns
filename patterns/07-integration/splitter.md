---
name: Splitter
slug: splitter
family: 07-integration
category: Message Routing
aliases: [Sequencer, Message Splitter, Fan-Out]
first_described: "Hohpe and Woolf 2003"
maturity: canonical
related: [aggregator, correlation-identifier, message-sequence, content-based-router, recipient-list, composed-message-processor, resequencer]
incompatible_with: []
verified: 2026-08-02
---

# Splitter

## 1. Name, aliases, and lineage

The canonical name is Splitter. It is documented as one of the message routing
patterns in Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns.
Designing, Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003,
in the chapter on message routing. The book's companion site states the pattern
plainly. "Use a Splitter to break out the composite message into a series of
individual messages, each containing data related to one item"
([enterpriseintegrationpatterns.com, Splitter](https://www.enterpriseintegrationpatterns.com/patterns/messaging/Sequencer.html),
verified 2026-08-02). That page opens with the canonical framing problem, an
order placed by a customer that consists of more than one line item, and each
line item may need to travel to a different inventory system for fulfillment
(same source, verified 2026-08-02).

The alias Sequencer is a naming quirk in the pattern catalog itself rather than
a separate community term. The Splitter pattern page on
enterpriseintegrationpatterns.com is served from the file path `Sequencer.html`
and the pattern's icon is `Sequencer.gif` (same source, verified 2026-08-02),
which is a leftover from an earlier draft of the book where the pattern that
became Splitter was provisionally named Sequencer, distinct from the later,
separately named Resequencer pattern that reorders a stream. Readers who search
the book's companion site for "sequencer" and land on the Splitter page are not
finding a different pattern, they are finding the same pattern under its old
working title. This entry treats Sequencer as a historical alias only, and
keeps it distinct from Resequencer (dimension 13).

Message Splitter and Fan-Out are the working names most engineers actually use
in conversation and in framework documentation. Apache Camel calls its
implementation the Split EIP and documents it as implementing the Hohpe and
Woolf pattern
([Apache Camel, Split EIP](https://camel.apache.org/components/next/eips/split-eip.html),
verified 2026-08-02). Spring Integration calls its implementation the Splitter
and states directly that "the splitter is a component whose role is to
partition a message into several parts and send the resulting messages to be
processed independently"
([Spring Integration Reference, Splitter](https://docs.spring.io/spring-integration/reference/splitter.html),
verified 2026-08-02). Fan-out is the term used more often at the
infrastructure layer, where the splitting happens not inside a message but
across delivery, one inbound event producing many outbound deliveries, as in
Amazon SNS topic fan-out to multiple SQS queues. This entry treats fan-out as
the same structural idea applied one layer down, from splitting a message body
into splitting a single inbound event into many independent deliveries, and
covers both.

## 2. Problem and context

A message arrives that is a container for several logically independent units
of work, and the downstream processing needs to happen per unit, not per
container.

The shape is familiar from any order-processing, batch-import, or ETL system.
An order contains line items, and each line item routes to a different
fulfillment center depending on the product category. A CSV upload contains
thousands of rows, and each row needs independent validation, independent
retry on failure, and an independent audit trail. A webhook payload from a
third-party system carries an array of ten events in a single HTTP POST, and
the receiving service processes events one at a time internally. A batch of
telemetry readings arrives compressed into one Kafka record and each reading
needs its own downstream aggregation window.

In every one of these situations, the alternative to splitting is to write
processing logic that operates on the whole container at once, iterating
internally, and that internal iteration quietly reintroduces every problem a
message-oriented architecture exists to solve. A failure partway through the
loop leaves the system in an ambiguous state, because nothing outside that one
process knows which items succeeded. Retrying the whole message reprocesses
items that already succeeded. Scaling the work across more machines requires
rewriting the loop as a distributed job rather than simply adding consumers,
because the unit of concurrency, the whole container, is too coarse. Routing
different items to different destinations requires branching logic buried
inside the loop rather than a router acting on each item independently.

The context in which Splitter is the right answer has three properties working
together. The incoming message genuinely decomposes into items that are
processing-independent of each other, meaning no item's outcome depends on
another item's outcome within the same message. The per-item processing
benefits from being addressed, retried, and observed individually, which is
almost always true once volume or heterogeneity rises past a handful of items.
And a place exists, later in the flow or never, where the results either need
to be recombined into a response shaped like the original container, or are
legitimately fine remaining independent forever. That third property decides
whether an Aggregator (dimension 13) belongs downstream of this Splitter or
whether the split items are simply the final, correct unit of work with no
recombination step at all.

## 3. Forces

**Granularity of failure isolation against processing overhead.** Splitting
turns one unit of work into N units, each independently retriable, observable,
and routable. That isolation is the entire value of the pattern, but each
split item now carries its own message envelope, its own header set, its own
acknowledgment cycle, and its own place in whatever tracing system is in use.
For a two-item message the overhead swamps the benefit. For a ten-thousand-item
message the overhead is the correct trade.

**Ordering against parallelism.** Once a message becomes N independent
messages, nothing enforces that they are processed in the order they were
split, unless something is added on purpose to enforce it. A downstream
consumer pool naturally wants to process split items in parallel for
throughput. If the original order carries meaning, item three must apply after
item two, that meaning is lost the moment the split happens unless the split
attaches a sequence number and something downstream honors it, which is a
distinct pattern, the Resequencer.

**Correlation cost against reassembly need.** If nothing downstream ever needs
to know that message seventeen and message eighteen both came from customer
order 4471, the split can be cheap, only N messages with no shared metadata.
The moment anything downstream needs to reassemble a response, generate a
combined receipt, or decide when all items from one order have finished, every
split item must carry a correlation identifier and, usually, a sequence
number and total count, which is real payload weight and real bookkeeping on
both the splitting side and the reassembling side.

**Memory pressure against latency to first result.** A splitter that must
first read the entire input into memory to know how many items exist, then
emit them all, trades a predictable but higher memory footprint for a simple
implementation. A streaming splitter that emits each item as soon as it is
recognized in the input keeps memory flat regardless of input size and lets
downstream consumers start working before the source is fully read, at the
cost of a harder implementation that cannot easily report how many items there
were until the stream ends. Apache Camel documents this directly, noting that
streaming mode "splits the original message on-demand, and each split message
is processed one by one. This reduces memory usage as the splitter does not
split all messages first"
([Apache Camel, Split EIP](https://camel.apache.org/components/next/eips/split-eip.html),
verified 2026-08-02).

**Semantic granularity, item versus subset.** The pattern is often described
as producing one message per element, but the useful unit is not always the
smallest element in the source. Batching split output into fixed-size chunks,
for example groups of one hundred rows rather than one row per message,
trades finer failure isolation for lower per-message overhead, and the right
answer depends entirely on what downstream processing actually costs per
message versus per item inside a message.

## 4. Applicability and non-applicability

Reach for Splitter when.

- A single inbound message genuinely contains multiple logically independent
  units of work, and independence is the operative word, not merely multiple
  fields.
- Different items within one message may need to be routed to different
  destinations, which is the classic combination of Splitter feeding a
  Content-Based Router per item.
- Per-item retry, per-item dead-lettering, or per-item observability matters
  more than treating the whole container as one atomic success-or-fail unit.
- The volume of items per message is high enough, or variable enough, that a
  fixed internal loop cannot scale independently of the container-processing
  logic.
- The source is too large to hold comfortably in memory as a single parsed
  structure, which pushes toward a streaming splitter regardless of whether
  the destination cares about item independence.

Do NOT reach for Splitter when.

- The items inside the message are not independent, meaning correct
  processing of item two genuinely requires knowing the outcome of item one
  within the same transaction. Splitting here manufactures a distributed
  transaction problem that a single-threaded loop inside one transaction
  boundary would not have had.
- The message has very few items, usually fewer than five, and they are
  always processed identically and atomically. The messaging overhead of N
  envelopes, N acknowledgments, and N trace spans is pure cost with no
  offsetting benefit at that scale.
- Strict ordering across the whole message is a hard requirement and no
  Resequencer or ordered-partition mechanism exists downstream to restore it.
  Splitting first and trying to bolt ordering back on afterward is more
  expensive than never breaking the order in the first place.
- The only reason to split is to satisfy a size limit on a single message
  transport, for example a queue's maximum payload size, and the items are not
  otherwise independent. In that narrow case a large-message pattern that
  stores the body externally and passes a reference, sometimes called
  Claim Check, is closer to the actual problem than Splitter, because the
  goal is fitting one logical message through a pipe, not decomposing
  independent work.
- The destination system already accepts the batch as a whole and processes it
  as a batch more efficiently than N individual calls, for example a bulk
  insert API. Splitting before a bulk API turns one efficient call into N
  inefficient ones for no isolation benefit, since the bulk API itself
  provides per-row result reporting.

## 5. Structure

- **Splitter.** The active participant. Receives one composite message,
  determines the decomposition strategy (whole-element, sub-tree, delimited
  chunk, or streamed token), and emits one message per resulting item onto an
  output channel. It is stateless with respect to any individual item, it
  does not wait for or depend on how downstream processing of one item
  affects another.
- **Composite message.** The input. A container whose payload encodes more
  than one logical unit, structured (an array field in JSON or XML, repeating
  elements) or unstructured (a delimited text file, a stream of records).
- **Split message.** Each output of the Splitter. Carries the data for exactly
  one item, plus, when reassembly matters, a correlation identifier tying it
  back to the composite message it came from, and usually a sequence number
  and a total count so a downstream Aggregator knows both the item's position
  and when all items have arrived.
- **Downstream consumer(s).** One or more endpoints that receive split
  messages independently. May be a single consumer type applied uniformly, or
  a Content-Based Router directing different split messages to different
  consumer types.
- **Aggregator (optional).** The counterpart participant that collects split
  messages sharing a correlation identifier and combines them back into a
  single outgoing message once a completion condition is met. Present only
  when the flow needs a response shaped like the original composite message,
  many real Splitter uses have no Aggregator downstream at all because the
  split items are the final unit of work.

## 6. ASCII structure diagram

```
                    +-------------------------------------------+
                    |            Composite Message               |
                    |  { orderId: 4471,                          |
                    |    items: [lineItem1, lineItem2, ...] }    |
                    +--------------------+------------------------+
                                         |
                                         v
                          +--------------------------+
                          |         Splitter          |
                          |  reads composite payload  |
                          |  emits one message/item   |
                          +--------------------------+
                                         |
             +---------------+----------+----------+---------------+
             v               v                     v               v
      +-------------+ +-------------+       +-------------+ +-------------+
      | Split Msg 1 | | Split Msg 2 |  ...  | Split Msg N |  correlation  |
      | correlId:   | | correlId:   |       | correlId:   |  id 4471,     |
      |   4471      | |   4471      |       |   4471      |  seq N/N      |
      | seq: 1/N    | | seq: 2/N    |       | seq: N/N    |               |
      +------+------+ +------+------+       +------+------+ +-------------+
             |                |                     |
             v                v                     v
      +-------------+  +-------------+       +-------------+
      |  Consumer / |  |  Consumer / |  ...  |  Consumer / |
      |   Router    |  |   Router    |       |   Router    |
      +-------------+  +-------------+       +-------------+
             |                |                     |
             +----------------+----------+----------+
                                          v
                              +--------------------------+
                              |   Aggregator (optional)   |
                              |  collects by correlId,    |
                              |  releases at seq N/N or   |
                              |  a timeout/completion rule |
                              +--------------------------+
                                          |
                                          v
                              +--------------------------+
                              |    Recombined Message     |
                              +--------------------------+
```

## 7. Dynamics

```
Producer          Splitter            Channel/Broker        Consumer(s)         Aggregator
   |                  |                      |                    |                  |
   | composite msg    |                      |                    |                  |
   |----------------->|                      |                    |                  |
   |                  | parse, decompose     |                    |                  |
   |                  | assign correlId,     |                    |                  |
   |                  | seq 1..N             |                    |                  |
   |                  |                      |                    |                  |
   |                  | emit split msg 1     |                    |                  |
   |                  |--------------------->|                    |                  |
   |                  | emit split msg 2     |                    |                  |
   |                  |--------------------->|                    |                  |
   |                  |          ...         |                    |                  |
   |                  | emit split msg N     |                    |                  |
   |                  |--------------------->|                    |                  |
   |                  |                      |                    |                  |
   |                  |                      | deliver msg 1      |                  |
   |                  |                      |------------------->|                  |
   |                  |                      |                    | process item 1   |
   |                  |                      |                    | ack              |
   |                  |                      |<-------------------|                  |
   |                  |                      |                    | forward result   |
   |                  |                      |                    |----------------->|
   |                  |                      | deliver msg 2      |                  |
   |                  |                      |------------------->|                  |
   |                  |                      |                    | process item 2   |
   |                  |                      |                    | (may run in      |
   |                  |                      |                    |  parallel with   |
   |                  |                      |                    |  item 1)         |
   |                  |                      |                    | ack              |
   |                  |                      |<-------------------|                  |
   |                  |                      |                    |----------------->|
   |                  |                      |         ...        |                  |
   |                  |                      |                    |                  | receives item N/N,
   |                  |                      |                    |                  | completion condition
   |                  |                      |                    |                  | met, release combined
   |                  |                      |                    |                  | message downstream
```

Streaming variant, where the total count N is not known until the source
is exhausted, differs in one respect. The splitter never buffers the full item
list, and any downstream Aggregator that depends on a known total count must
either be told the count out of band once the source finishes, or use a
different release strategy such as a timeout or an explicit end-of-stream
marker message rather than counting up to a pre-known N.

## 8. Implementation variants

**Eager, in-memory split.** The splitter fully parses the composite message
into a data structure, iterates it, and emits every split message before the
splitter's own processing of the original message completes. Simplest to
implement, and correct when the total item count is genuinely useful to know
up front, for example to stamp every split message with `sequenceSize`. Costs
memory proportional to the whole message.

**Streaming split.** The splitter uses a tokenizer or streaming parser and
emits each item as soon as it is recognized, never holding the whole message
in memory. Apache Camel documents this directly for large XML payloads,
warning that a DOM-based XPath evaluation "will load the entire XML content
into memory," which is why the framework offers streaming tokenizers as an
alternative "for very big XML payloads"
([Apache Camel, Split EIP](https://camel.apache.org/components/next/eips/split-eip.html),
verified 2026-08-02). Streaming trades knowledge of the total count for flat
memory usage, and any correlation scheme downstream must accommodate an
unknown or late-known total.

**Delimiter-driven text split.** The composite message is unstructured text,
most often a CSV, NDJSON, or fixed-width file, and the splitter emits one
message per line or per record boundary rather than parsing a nested
structure. This is functionally the streaming variant applied to flat text,
and is the shape most ETL and batch-import splitters take.

**Structural sub-tree split.** For deeply nested formats such as XML or
protobuf, the splitter targets a repeated sub-element (an XPath expression, a
JSONPath expression, or a repeated field) rather than the top level of the
document, and emits one message per matched sub-tree while optionally
preserving shared context from the parent, such as a common header block that
every split item needs a copy of.

**Chunked split.** Rather than one message per element, the splitter groups
elements into fixed-size or fixed-byte-size batches and emits one message per
batch. This is the correct choice when per-item messaging overhead outweighs
the per-item processing benefit and the downstream consumer can process a
small batch atomically without losing the failure isolation that matters, trading
fine-grained retry for lower messaging cost.

**Event-driven fan-out at the infrastructure layer.** Rather than one program
parsing a payload and calling a decomposition function, the split happens as a
property of the transport itself. A publish-subscribe topic delivering one
published event to many independently-configured subscribers has the
same fan-out shape, even though no single piece of code holds a loop that
emits N messages, the broker's subscription mechanism performs the
decomposition instead. Amazon SNS to multiple SQS queues and Kafka topics with
multiple consumer groups both realize this variant.

**Splitter with immediate re-aggregation, the Composed Message Processor.**
Hohpe and Woolf name the common combination of a Splitter immediately followed
by processing and an Aggregator as its own named composite pattern, referenced
directly from the Splitter page's related patterns and its own dedicated page
([enterpriseintegrationpatterns.com, Composed Message Processor](https://www.enterpriseintegrationpatterns.com/DistributionAggregate.html),
referenced from the Spring Integration documentation,
verified 2026-08-02). It is worth naming as a variant because framework
support, in particular Spring Integration's `AggregatingMessageHandler` wiring for
scatter-gather, treats it as a first-class combined shape rather than two
independently wired patterns.

## 9. Known production uses

- **Apache Camel's Split EIP.** A first-class enterprise integration
  component implementing this pattern directly, with both eager and streaming
  modes, an `AggregationStrategy` hook for recombining results, and dedicated
  streaming tokenizer support for XML documents too large to parse into
  memory ([Apache Camel, Split EIP](https://camel.apache.org/components/next/eips/split-eip.html),
  verified 2026-08-02).
- **Spring Integration's Splitter component.** Ships as a core Spring
  Integration building block, described as partitioning "a message into
  several parts and send[ing] the resulting messages to be processed
  independently," and automatically stamping every produced message with
  `CORRELATION_ID`, `SEQUENCE_SIZE`, and `SEQUENCE_NUMBER` headers precisely
  so that a downstream aggregator can reassemble the set
  ([Spring Integration Reference, Splitter](https://docs.spring.io/spring-integration/reference/splitter.html),
  verified 2026-08-02).
- **AWS Step Functions, the Map state.** Runs "a set of workflow steps for
  each item in a dataset," accepting a JSON array, a CSV file in S3, or an S3
  object listing as the source, and running each item's workflow as an
  independent execution. In Distributed mode it scales to "up to 10,000
  parallel child workflow executions" precisely because each mapped item is
  processed as a genuinely independent unit of work, which is the Splitter
  pattern realized as a managed orchestration primitive rather than a
  message-queue component ([AWS documentation, Map workflow state](https://docs.aws.amazon.com/step-functions/latest/dg/state-map.html),
  verified 2026-08-02).

## 10. Consequences

Positive.

- Per-item failure isolation. One malformed line item in a ten-thousand-row
  import fails and dead-letters independently, rather than aborting or
  silently skipping the whole import.
- Independent scalability. Split items can be consumed by an elastic pool of
  workers sized to the item-processing workload, decoupled from however the
  composite messages themselves arrive.
- Per-item routing. Combined with a Content-Based Router, different items
  from the same message can be sent to entirely different destinations
  without the source system needing to know that destination logic at all.
- Fine-grained observability. Tracing, metrics, and dead-letter inspection
  operate at the level that actually matters to an operator, the individual
  order line or the individual imported row, rather than an opaque bulk job.
- Flat memory usage available. The streaming variant decouples message size
  limits from the splitter's own memory footprint, letting arbitrarily large
  sources be processed without a corresponding increase in splitter memory.

Negative.

- Messaging overhead multiplies by the item count. Envelope size, broker
  throughput, acknowledgment round trips, and, if used, tracing spans all
  scale with N, which is wasted cost when N is small or items are cheap to
  process.
- Ordering is lost by default. Nothing about the pattern preserves the
  original sequence unless a sequence number is attached and something
  downstream deliberately honors it, parallel consumers will process split
  items out of order as a matter of course.
- Reassembly is a second problem, not a free byproduct. Any flow that needs
  to know when all items from one message have finished, or needs a combined
  result, must build and operate a correlated Aggregator, which introduces
  its own state, its own completion-condition logic, and its own failure
  modes (dimension 11).
- Partial failure becomes a first-class state the system must model. Where a
  monolithic batch either fully succeeds or fully fails, a split batch can be
  seventy percent successful with the rest pending retry, and every consumer
  of order-completion status now has to answer a more complicated question
  than yes or no.
- Debugging a single logical transaction requires stitching correlation
  identifiers back together across N independently logged and independently
  timed messages, which is strictly harder than reading one linear execution
  trace for one message.

## 11. Failure modes and misuse

**Symptom.** Downstream storage or a metrics dashboard reports orders that
never seem to complete.
**Cause.** Split messages were emitted without a stable, unique correlation
identifier, or the identifier collides across concurrent composite messages,
for example reusing a timestamp instead of a real order ID, so the
Aggregator's grouping logic silently merges items from two different orders
or never groups them at all.
**Fix.** Use the source system's real unique identifier as the correlation
key, generate one deterministically from the source if none exists, and add a
test that asserts two composite messages processed concurrently never share a
correlation identifier.

**Symptom.** The splitter's memory usage grows linearly with the size of the
largest message it has ever seen, and eventually the process is killed by an
out-of-memory event on an unusually large input.
**Cause.** An eager, fully-buffered split implementation was used on a source
whose size is not bounded, most often when a batch-import feature that
started with small files quietly grows to accept larger and larger uploads
over the life of the product.
**Fix.** Switch to a streaming split for any source whose size is not bounded
by a hard, enforced upload limit, and add a test with an input several times
larger than the largest input observed in production to prove memory stays
flat.

**Symptom.** An order that should generate five line-item messages
intermittently generates four, and the missing item is never processed,
never dead-lettered, and never logged as an error.
**Cause.** The split loop silently skips an element that fails a
decomposition check, for example a line item missing an expected field,
rather than emitting it to an invalid-message channel. This is the single
most common Splitter defect, because a try-and-continue inside a split loop
looks harmless in code review and produces no visible error anywhere.
**Fix.** Route decomposition failures to an Invalid Message Channel or dead
letter with the original composite message's correlation identifier attached,
never drop silently, and assert item-count-in equals successfully-split-count
plus explicitly-routed-invalid-count in an integration test.

**Symptom.** A downstream Aggregator hangs indefinitely, never releasing a
combined result, for a small but nonzero fraction of composite messages.
**Cause.** The completion condition depends on a total count, `sequenceSize`,
known at split time, but the splitter is a streaming implementation that
determines the total only after the source is exhausted, and a race exists
where the aggregator's release check runs before the splitter has finished
emitting the last item and communicating the final count.
**Fix.** Either switch the splitter to eager mode so the total count is known
before the first item is emitted, or switch the aggregator's release strategy
to an explicit end-of-stream marker message rather than a pre-known count,
and never mix a streaming producer with a count-based release strategy.

**Symptom.** A customer-facing bulk operation, for example importing fifty
thousand contacts, runs correctly but takes noticeably longer and costs
noticeably more in message-broker throughput than an equivalent bulk database
insert would.
**Cause.** Splitter was applied to a workload where the items are not
actually independent in any way that matters to the business, every item
goes to the same destination, is processed identically, and no per-item
retry or routing is ever exercised in practice, so the pattern's isolation
and routing benefits are paid for in overhead but never collected.
**Fix.** Measure whether per-item independence is exercised in production,
different retry outcomes, different routes, different consumers, if not,
replace the fine-grained split with a chunked split at a batch size the
destination's bulk API actually benefits from, per the chunked-split variant
in dimension 8.

## 12. Trade-off matrix

| Force | Splitter | Content-Based Router alone | A single internal loop, no messaging |
|---|---|---|---|
| Per-item failure isolation | Native, each split message fails independently | None, a single message routes as one unit even if its body contains many logical items | None, one exception can abort the whole loop |
| Per-item routing to different destinations | Native, combines naturally with a router applied per split item | Native for whole messages, but cannot route sub-parts of one message differently without first splitting it | Requires hand-written branching inside the loop, mixing routing logic with iteration logic |
| Memory footprint on very large inputs | Can stay flat with a streaming implementation | Not applicable, routing does not touch message internals | Bounded only by however the loop itself was written, commonly loads the whole input first |
| Preserves original item ordering by default | No, requires an explicit sequence number and a Resequencer to restore order | Yes, whole messages are usually processed in arrival order | Yes, a simple loop processes items in source order unless explicitly parallelized |
| Operational complexity added | Real, correlation identifiers, sequence headers, and often a paired Aggregator must be built and operated | Low, one routing decision per message, no new state | Lowest, no new infrastructure, but all complexity lives inside one function |
| Best fit | High-volume or heterogeneous composite messages needing independent per-item processing | Whole messages that need to go to different destinations, with no need to decompose the message body | Small, fixed-size, tightly coupled item sets where independence and isolation are not needed |

## 13. Related and incompatible patterns

**Aggregator.** The natural downstream counterpart. An Aggregator collects
messages sharing a correlation identifier and releases a combined result once
a completion condition is met, commonly all N items received or a timeout
elapsed. Splitter and Aggregator are frequently deployed together but are
independently useful, many Splitter deployments have no Aggregator at all
because the split items are the final destination for the work, and many
Aggregators consume from something other than a Splitter, for example
combining independent responses from a Scatter-Gather across different
services.

**Correlation Identifier.** The mechanism, not a separate architectural
component, that makes reassembly possible. Every split message that will ever
need to be regrouped must carry one, and the identifier's uniqueness and
stability across the lifetime of the composite message's processing is the
single most load-bearing detail in a correct Splitter and Aggregator pairing.

**Message Sequence.** The related concept of stamping split messages with a
position and total count, `sequenceNumber` and `sequenceSize`, which Spring
Integration implements directly on every message its Splitter produces
([Spring Integration Reference, Splitter](https://docs.spring.io/spring-integration/reference/splitter.html),
verified 2026-08-02). Message Sequence headers are what make a count-based
Aggregator release strategy possible.

**Resequencer.** The opposite-direction repair pattern. Where Splitter breaks
order apart as a side effect of parallelizable processing, Resequencer
collects out-of-order messages and reorders them into a strict sequence
before passing them on. A Splitter feeding parallel consumers that then feed
a Resequencer is a common combination when a flow needs both the throughput
of parallel per-item processing and the guarantee of strictly ordered output.

**Content-Based Router.** Frequently chained immediately after a Splitter, so
each split item is examined individually and routed to the correct
destination, which is precisely the line-item-to-inventory-system example the
pattern's own description opens with
([enterpriseintegrationpatterns.com, Splitter](https://www.enterpriseintegrationpatterns.com/patterns/messaging/Sequencer.html),
verified 2026-08-02).

**Composed Message Processor.** The named composite of Splitter feeding
per-item processing feeding an Aggregator, treated as its own pattern by
Hohpe and Woolf because the combination recurs often enough to name on its
own, and because framework scatter-gather implementations wire the whole
triad as a single configurable unit.

**Recipient List.** A sibling routing pattern rather than a relative.
Recipient List sends one whole, unsplit message to a computed list of
recipients, Splitter decomposes one message into several messages, each
potentially going to only one recipient. The two are sometimes confused
because both produce one message becoming several deliveries, but Recipient
List never touches the message body and Splitter's entire purpose is to
change what is inside each delivered message.

**Incompatible with strict single-transaction atomicity.** A Splitter is
incompatible in structure with a requirement that the whole composite message
succeed or fail as one atomic unit across a distributed system, because the
split items are, by the pattern's own definition, independently processed. A
flow with that requirement should not use Splitter at all, it should keep the
composite message intact and process it inside a single transaction boundary,
or use a saga-style compensation pattern designed explicitly for partial
failure across distributed steps rather than pretending Splitter provides
atomicity it does not.

## 14. Refactoring path in and out

**Introducing Splitter into existing code.** Start from a method that
receives one composite payload and contains an internal loop over its items.
First, extract the loop body into a standalone function that takes a single
item and has no dependency on loop state from any other iteration, this alone
often surfaces hidden coupling between items that must be resolved before the
pattern applies at all. Second, replace the loop with a call that emits one
message per item onto an outbound channel rather than calling the extracted
function directly, keeping the message shape minimal at first, only the item
payload and a correlation identifier. Third, stand up a consumer on the
outbound channel that calls the same extracted per-item function, at this
point the behavior is unchanged but now decoupled through messaging. Fourth,
only if reassembly is genuinely needed, add sequence headers and a paired
Aggregator, do not add this step speculatively, since an unused Aggregator is
pure operational cost.

**Removing Splitter when it stops earning its place.** The signal that a
Splitter should be retired is usually the chunked-split misuse case from
dimension 11, items are consistently processed identically with no observed
difference in routing or retry outcome. Fold the per-item consumer function
back into a single method, replace the split-and-recombine flow with a direct
call, and if the volume is still meaningfully large, replace individual
message emission with a single bulk call to whatever downstream system
exists, using its native bulk API rather than N individual calls. Remove the
correlation and sequence headers only after confirming no other consumer of
the message stream depends on them, since headers are cheap to leave in place
but expensive to add back once removed if something downstream was silently
relying on them.

## 15. Testing and verification

What becomes easy to test is the per-item logic itself, once extracted into a
standalone function with no loop-state dependency, it is trivially unit
tested with a table of item inputs and expected outputs, independent of any
messaging infrastructure.

What becomes harder to test is the behavior of a whole composite message
end to end, because a correct test now has to assert on N independently
delivered messages rather than one return value. The needed test doubles are
an in-memory or test-mode message channel that captures every emitted
message without a real broker, and, for the reassembly path, a test rig
that can trigger completion events, either all N arrived or a simulated
timeout, deterministically rather than relying on real wall-clock time.

A correct Splitter test suite verifies at minimum, that item count in equals
successfully-split-count plus explicitly-invalid-count, never a silent
mismatch, per the silent-drop failure mode in dimension 11. That every
emitted split message carries a stable, unique correlation identifier tied to
its source composite message, verified by processing two composite messages
concurrently and asserting no identifier collision. That a streaming
implementation's memory usage, measured directly or via a bounded-buffer
assertion, does not grow with input size beyond a small constant factor. And,
where an Aggregator is downstream, an integration test that deliberately
delivers split messages out of order and confirms the Aggregator still
releases the correct combined result, since out-of-order delivery is the
normal case for a Splitter feeding parallel consumers, not an edge case.

## 16. Observability signals

Log or emit a metric at the moment of split recording the composite message's
correlation identifier, the item count produced, or, for a streaming
splitter, an incrementing counter with no fixed total, and the time taken to
perform the decomposition, since decomposition time on unexpectedly large or
malformed inputs is the earliest signal of the memory-growth failure mode.

Emit a per-item metric on the consumer side tagged with the same correlation
identifier, so that a single logical transaction, one order, one imported
file, can be reconstructed across every downstream system by filtering on
that one tag, which is the operational payoff for the bookkeeping cost paid
in dimension 3.

Where an Aggregator exists downstream, track two additional signals directly.
The count of correlation groups currently open and awaiting completion, since
a growing backlog of never-completing groups is the clearest indicator of the
correlation-identifier collision or the count-based race described in
dimension 11. And the age of the oldest open group, since a group open far
longer than the expected processing time, start to finish, for a single item almost
always means one split item was silently lost rather than merely slow.

A healthy dashboard for a Splitter-based flow shows the open-group count
oscillating near zero, rising only during active processing bursts and
returning to a low baseline, a failing instance shows the open-group count
climbing without bound, or the item-count-in versus item-count-out gap
widening over time rather than staying flat.

## 17. Security and privacy implications

Splitting a composite message multiplies the number of message envelopes that
carry data derived from that message, and each split message usually
carries at minimum an item payload plus a correlation identifier tying it
back to the source. Where the source message contains personal or otherwise
sensitive data, and the item-level payload includes that data, for example a
customer's name or address embedded in every line item of an order, the
attack surface for that data is now N delivery points, N points of access
control, and N places a logging or tracing system might capture the payload,
rather than one. Access control and field-level redaction decisions made
correctly for the composite message must be re-verified as still correct
once applied per split item, since a policy written assuming the whole order
is one access-controlled unit may not translate cleanly to each line item
being independently readable by whichever service happens to consume that
particular split queue.

Correlation identifiers themselves deserve a specific note. If the identifier
chosen is a value that also functions as a sensitive identifier elsewhere in
the system, for example a customer's own account number reused directly as
the correlation key, then every log line, every trace span, and every
message broker payload that carries that correlation identifier is now also
carrying that sensitive identifier, propagated far beyond wherever it was
originally scoped to be visible. Preferring an opaque, purpose-generated
correlation identifier over reuse of a sensitive business identifier avoids
this propagation without losing any of the reassembly benefit the identifier
exists to provide.

## 18. References

- Gregor Hohpe, Bobby Woolf, *Enterprise Integration Patterns. Designing,
  Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003, chapter
  on message routing, the Splitter pattern.
- [Enterprise Integration Patterns companion site, Splitter](https://www.enterpriseintegrationpatterns.com/patterns/messaging/Sequencer.html),
  verified 2026-08-02.
- [Enterprise Integration Patterns companion site, Composed Message Processor](https://www.enterpriseintegrationpatterns.com/DistributionAggregate.html),
  verified 2026-08-02.
- [Apache Camel documentation, Split EIP](https://camel.apache.org/components/next/eips/split-eip.html),
  verified 2026-08-02.
- [Spring Integration Reference Documentation, Splitter](https://docs.spring.io/spring-integration/reference/splitter.html),
  verified 2026-08-02.
- [AWS Step Functions Developer Guide, Map workflow state](https://docs.aws.amazon.com/step-functions/latest/dg/state-map.html),
  verified 2026-08-02.

## Code

### TypeScript

```typescript
interface OrderItem {
  sku: string;
  quantity: number;
}

interface Order {
  orderId: string;
  items: OrderItem[];
}

interface SplitMessage {
  correlationId: string;
  sequenceNumber: number;
  sequenceSize: number;
  item: OrderItem;
}

function splitOrder(order: Order): SplitMessage[] {
  const total = order.items.length;
  return order.items.map((item, index) => ({
    correlationId: order.orderId,
    sequenceNumber: index + 1,
    sequenceSize: total,
    item,
  }));
}

function aggregate(messages: SplitMessage[]): Order | null {
  if (messages.length === 0) return null;
  const first = messages[0];
  const complete = messages.length === first.sequenceSize;
  if (!complete) return null;
  const sorted = [...messages].sort((a, b) => a.sequenceNumber - b.sequenceNumber);
  return {
    orderId: first.correlationId,
    items: sorted.map((m) => m.item),
  };
}

function main(): void {
  const order: Order = {
    orderId: "order-4471",
    items: [
      { sku: "WIDGET-1", quantity: 2 },
      { sku: "GADGET-9", quantity: 1 },
      { sku: "GIZMO-3", quantity: 5 },
    ],
  };

  const split = splitOrder(order);
  for (const msg of split) {
    console.log(
      `split ${msg.sequenceNumber}/${msg.sequenceSize} correlationId=${msg.correlationId} sku=${msg.item.sku}`,
    );
  }

  const rebuilt = aggregate(split);
  console.log("rebuilt", JSON.stringify(rebuilt));
}

main();
```

### Python

```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class OrderItem:
    sku: str
    quantity: int


@dataclass
class Order:
    order_id: str
    items: list[OrderItem]


@dataclass
class SplitMessage:
    correlation_id: str
    sequence_number: int
    sequence_size: int
    item: OrderItem


def split_order(order: Order) -> list[SplitMessage]:
    total = len(order.items)
    return [
        SplitMessage(
            correlation_id=order.order_id,
            sequence_number=index + 1,
            sequence_size=total,
            item=item,
        )
        for index, item in enumerate(order.items)
    ]


def aggregate(messages: list[SplitMessage]) -> Optional[Order]:
    if not messages:
        return None
    total = messages[0].sequence_size
    if len(messages) != total:
        return None
    ordered = sorted(messages, key=lambda m: m.sequence_number)
    return Order(order_id=messages[0].correlation_id, items=[m.item for m in ordered])


def main() -> None:
    order = Order(
        order_id="order-4471",
        items=[
            OrderItem(sku="WIDGET-1", quantity=2),
            OrderItem(sku="GADGET-9", quantity=1),
            OrderItem(sku="GIZMO-3", quantity=5),
        ],
    )

    split = split_order(order)
    for msg in split:
        print(
            f"split {msg.sequence_number}/{msg.sequence_size} "
            f"correlationId={msg.correlation_id} sku={msg.item.sku}"
        )

    rebuilt = aggregate(split)
    print("rebuilt", rebuilt)


if __name__ == "__main__":
    main()
```

### Go

```go
package main

import (
	"fmt"
	"sort"
)

type OrderItem struct {
	SKU      string
	Quantity int
}

type Order struct {
	OrderID string
	Items   []OrderItem
}

type SplitMessage struct {
	CorrelationID  string
	SequenceNumber int
	SequenceSize   int
	Item           OrderItem
}

func splitOrder(order Order) []SplitMessage {
	total := len(order.Items)
	messages := make([]SplitMessage, 0, total)
	for i, item := range order.Items {
		messages = append(messages, SplitMessage{
			CorrelationID:  order.OrderID,
			SequenceNumber: i + 1,
			SequenceSize:   total,
			Item:           item,
		})
	}
	return messages
}

func aggregate(messages []SplitMessage) (Order, bool) {
	if len(messages) == 0 {
		return Order{}, false
	}
	total := messages[0].SequenceSize
	if len(messages) != total {
		return Order{}, false
	}
	sorted := make([]SplitMessage, len(messages))
	copy(sorted, messages)
	sort.Slice(sorted, func(i, j int) bool {
		return sorted[i].SequenceNumber < sorted[j].SequenceNumber
	})
	items := make([]OrderItem, 0, len(sorted))
	for _, m := range sorted {
		items = append(items, m.Item)
	}
	return Order{OrderID: messages[0].CorrelationID, Items: items}, true
}

func main() {
	order := Order{
		OrderID: "order-4471",
		Items: []OrderItem{
			{SKU: "WIDGET-1", Quantity: 2},
			{SKU: "GADGET-9", Quantity: 1},
			{SKU: "GIZMO-3", Quantity: 5},
		},
	}

	split := splitOrder(order)
	for _, msg := range split {
		fmt.Printf(
			"split %d/%d correlationId=%s sku=%s\n",
			msg.SequenceNumber, msg.SequenceSize, msg.CorrelationID, msg.Item.SKU,
		)
	}

	rebuilt, ok := aggregate(split)
	fmt.Println("rebuilt", rebuilt, ok)
}
```

C#, Java, Rust, Swift, and Kotlin are omitted from this entry not because the
pattern fails to translate, it translates cleanly to any language with
collections and structs, but because the three languages above already cover
the three idiomatic shapes that matter. A functional-array transformation
(TypeScript), a dataclass-and-comprehension shape typical of Python ETL code
(Python), and an explicit-loop, explicit-struct shape typical of statically
typed systems languages (Go). A fourth or fifth language would repeat the same
shape without adding a new implementation idea.
