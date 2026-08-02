---
name: Claim Check
slug: claim-check
family: 08-cloud-distributed
category: Messaging and Integration
aliases: [Store in Library, Claim-Check Pattern, Reference-Based Messaging]
first_described: "Hohpe and Woolf 2003 (Enterprise Integration Patterns, Claim Check); cloud realization documented in the Azure Architecture Center"
maturity: canonical
related: [content-enricher, splitter, transactional-outbox, materialized-view, gateway-aggregation, publisher-subscriber, circuit-breaker, retry]
incompatible_with: []
verified: 2026-08-02
---

# Claim Check

## 1. Name, aliases, and lineage

The canonical name is **Claim Check**, recorded by Gregor Hohpe and Bobby
Woolf in *Enterprise Integration Patterns. Designing, Building, and
Deploying Messaging Solutions*, Addison-Wesley, 2003, in the Message
Transformation chapter. The book's own pattern page states the problem
plainly, "How can we reduce the data volume of message sent across the
system without sacrificing information content?", and answers it with,
"Store message data in a persistent store and pass a Claim Check to
subsequent components. These components can use the Claim Check to
retrieve the stored information" ([Enterprise Integration Patterns, Claim
Check](https://www.enterpriseintegrationpatterns.com/patterns/messaging/StoreInLibrary.html),
verified 2026-08-02). The page's own breadcrumb places it under Message
Transformation, next to Content Enricher, Content Filter, Envelope Wrapper,
Normalizer, and Canonical Data Model, which matters, because the two
patterns that appear closest to it in the book, Content Enricher and Claim
Check, are near mirror images of each other, see dimension 13.

The book records **Store in Library** as its own internal alias for the
same pattern, and the file name of the canonical page,
`StoreInLibrary.html`, still carries it twenty years later. The name Claim
Check itself borrows a physical world object. A traveller checks a bag at
an airline counter, receives a small numbered token, and carries only the
token for the rest of the trip. The airline is free to route, load,
and store the actual bag out of sight, and the traveller only needs the
token to get it back at the far end. The pattern applies the same idea to
a message. The bulky data goes into a data store, and only a small token,
the claim check, travels through the messaging system.

Cloud platform vendors kept the name largely unchanged. Microsoft
catalogues it in the Azure Architecture Center as the **Claim-Check
pattern**, with a one-line summary that matches the original intent almost
word for word, "Store a large message payload in an external data store
and send only a reference token, called a claim check, through a messaging
system" ([Microsoft Learn, Claim-Check
pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/claim-check),
verified 2026-08-02). Outside the two canonical sources, engineers
frequently call the same shape **reference-based messaging**, or describe
implementations of it as storing a pointer instead of the payload, but
neither of those phrases names a distinct pattern. They describe the same
Claim Check under a plainer label.

One naming trap is worth flagging early. The word "claim" also appears in
unrelated senses, an authorization claim in a JWT, an insurance claim in a
domain model, a claim in a distributed lock. None of those are this
pattern. The Claim Check pattern is specifically about a token that stands
in for data too bulky to travel with the message that references it.

## 2. Problem and context

A service publishes a message that needs to carry a large piece of data,
a scanned document, a video file, a full order history export, a machine
learning feature vector, a rendered PDF invoice, and the message has to
travel through a messaging system built and tuned for many small,
frequent messages rather than occasional large ones.

The situation surfaces in a codebase in one of two ways. Either the
message flatly will not fit, because the broker enforces a hard size
limit, or the message technically fits but degrades everything sharing
the same infrastructure. Both failure shapes trace back to the same root
cause named directly by Hohpe and Woolf's problem statement, quoted above,
reducing the data volume of a message without losing the information it
carries.

Concrete examples of the limit failure. Amazon SQS and SNS cap a message
body at 256 KB per the Amazon SQS Extended Client Library documentation
([AWS documentation, Managing large Amazon SQS messages using Java and
Amazon
S3](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/s3-messages.html),
verified 2026-08-02), and a broker connector that tries to publish
anything larger simply rejects the call. Concrete examples of the
performance failure. A shared broker sized for a steady stream of small
event payloads slows down, and its persistence and replication cost rises,
the moment a producer starts pushing multi-megabyte blobs through the same
topic, an effect the Azure Architecture Center calls out plainly when it
states that large messages "not only risk exceeding these limits but can
also degrade the performance of the entire system" ([Microsoft Learn,
Claim-Check
pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/claim-check),
verified 2026-08-02).

The context that makes Claim Check the right answer, rather than raising
the broker's limit or compressing the payload, has three parts.

- The data is bulky relative to the messaging system's sweet spot, and the
  bulk itself, not the number of messages, is the thing straining
  throughput or cost.
- A durable, independently addressable data store already exists, or can
  reasonably be added, that is not the message broker itself, an object
  store, a blob container, a shared file system, a database table built
  for large binary or JSON content.
- At least one downstream component in the pipeline does not need the
  bulky payload at all, only the fact that a message occurred and enough
  metadata to route or filter on, which is exactly the secondary use case
  the Azure pattern page names under complex routing scenarios.

Outside that context the fix is usually something plainer, a bigger broker
tier, compression, or simply keeping the payload inline, see dimension 4.

## 3. Forces

The pattern balances several competing pressures at once, and states its
trade honestly rather than pretending the win is free.

- **Message size and broker throughput.** Favoured heavily. Removing the
  bulk from the channel is the entire point, and it is the one force every
  cited source agrees on without qualification.
- **Cost.** Favoured, usually. Object storage priced per gigabyte per month
  is normally cheaper than the same data replicated and persisted inside a
  message broker's own storage layer, and the Azure Architecture Center's
  Cost Optimization guidance says directly that reducing the size of
  message bodies might enable use of a cheaper messaging solution
  ([Microsoft Learn, Claim-Check
  pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/claim-check),
  verified 2026-08-02).
- **Latency.** Sacrificed on the consumer side. A consumer that needs the
  actual payload pays for a second network round trip to fetch it from the
  data store, on top of receiving the message. For a consumer that never
  needs the payload, latency instead improves, because it never
  deserializes bulk data it was going to discard.
- **Consistency.** Sacrificed, and this is the sharpest force in the whole
  pattern. The message and the stored object are now two separate pieces
  of state, written by two separate operations, with no shared
  transaction. A gap between an object written and a message published, or
  between a message consumed and an object deleted, is where every
  meaningful failure mode in dimension 11 lives.
- **Coupling.** Mixed. The message broker loses its coupling to payload
  size, but every consumer gains a new coupling, to the data store's
  address, its authentication, and its availability. A consumer that
  previously depended on one system now depends on two.
- **Security exposure.** Favoured, when applied deliberately. A payload
  that stays out of the broker never passes through every intermediary hop,
  every broker administrator's console, and every log line that happens to
  capture message bodies, which is exactly the sensitive data protection
  secondary use case the Azure Architecture Center names.
- **Operability.** Sacrificed. There are now two systems to monitor for
  health, two systems that can fail independently, and a new class of
  incident, the orphaned or missing object, that a broker-only pipeline
  never produced.

No cited source claims the pattern is free. Every gain listed above is
paid for somewhere else in the list, most heavily in consistency and
operability.

## 4. Applicability and non-applicability

Reach for Claim Check when the following hold.

- The payload regularly, not occasionally, exceeds the message broker's
  hard size limit, and there is no cheaper way to stay under it.
- Large payloads are measurably degrading broker throughput, latency, or
  cost for every message sharing the same infrastructure, even when each
  individual message technically fits.
- The payload contains sensitive data that should not be visible to every
  component that merely routes or forwards the message, and a separately
  access-controlled data store is available to hold it.
- Some consumers in the pipeline route, filter, or audit on metadata alone
  and never touch the bulky payload, so most of the pipeline's hops are
  cheaper once the bulk is out of the message.
- Messages must be retried or replayed without re-transmitting the bulky
  data on every retry, only the small claim needs to travel again.

Do NOT reach for Claim Check in these cases, and each reason is the one a
generic catalog tends to skip.

- **The payload is comfortably small and stays that way.** Adding a data
  store, a claim token, and a fetch step to shrink a message that already
  fits well under the broker's limit is added machinery for no measured
  gain. A plain inline message is simpler and has one fewer moving part
  that can fail.
- **Every consumer in the pipeline needs the full payload immediately.**
  Moving the bulk out of the broker only relocates the cost. Every hop now
  pays a network round trip to the data store instead of reading the
  payload it already received, and the pipeline gains a new external
  dependency with nothing removed in exchange.
- **The message delivery guarantee and the payload's durability must be
  transactionally consistent, and the data store cannot join that
  transaction.** Most message brokers offer at-least-once or exactly-once
  delivery inside their own boundary. An external object store almost
  never participates in that guarantee, so a crash between the store write
  and the message publish, or between message consumption and object
  deletion, creates either an orphaned object or a dangling claim, see
  dimension 11.
- **No independently durable, separately available store exists, and one
  is impractical to add.** A claim check that points at a store no more
  reliable than the broker itself trades one dependency for two without
  raising overall reliability.
- **The data is short lived and disposable, and losing it if a consumer is
  delayed carries no cost.** A time-to-live cache with straightforward
  eviction is a simpler answer than a claim token, a persistent store, and
  the cleanup logic in dimension 11.
- **The path is latency sensitive to the point where a second network
  round trip is unacceptable**, for example a sub-millisecond matching or
  pricing path. Keeping the data inline, even if that forces a smaller
  payload elsewhere, avoids the fetch hop entirely.
- **The bulky data is structured and needs to be queried, filtered, or
  aggregated by consumers, rather than fetched whole.** A blob-and-pointer
  hides structure behind an opaque object. A Materialized View or a CQRS
  read model built for querying is the better fit for that shape of
  problem, and Claim Check should stay reserved for genuinely opaque
  blobs, documents, and media.

## 5. Structure

Five participants, named by the role each one plays in the flow.

- **Sender.** The component that owns the original, full-size payload. It
  decides whether the payload needs a claim, per the threshold discussed
  in dimension 8, and is the only participant that writes to the data
  store on the way in.
- **Data Store.** A durable, addressable store separate from the message
  channel, an object store, a blob container, a key-value store, or a
  relational table with a large-object column. It exposes at minimum a
  write-and-return-key operation and a read-by-key operation.
- **Claim Check.** The token itself, a small, unique, ideally unguessable
  key that identifies exactly one stored object. It is the only artefact
  that ever travels through the messaging channel in place of the payload.
- **Messaging Channel.** The queue, topic, or event bus that would
  otherwise have carried the full payload. After the pattern is applied it
  carries only the claim check plus whatever small metadata the pipeline
  needs for routing.
- **Receiver.** The component that consumes the message. If it needs the
  payload, it presents the claim check back to the Data Store to retrieve
  it. Some receivers in a fan-out pipeline never need the payload and
  simply act on the metadata, which is one of the pattern's clearest wins.

An optional sixth participant, a **Cleanup Agent**, owns removing stored
objects once every interested Receiver has consumed its claim, either
synchronously as part of the consuming workflow or asynchronously through
a lifecycle or time-to-live policy on the Data Store itself. Whether
cleanup is synchronous or asynchronous is the single design decision most
responsible for the failure modes in dimension 11, and Azure's own
documentation names exactly this trade off in its considerations section.

## 6. ASCII structure diagram

```
   +-----------+          1. put(payload)          +--------------+
   |  Sender   | ---------------------------------> |  Data Store  |
   +-----------+                                     +--------------+
        |                                                    |
        | 2. returns claim key                              |
        |<---------------------------------------------------
        |
        | 3. publish(claim, small metadata)
        v
   +-----------------------------+
   |     Messaging Channel       |
   |  (queue / topic / event bus)|
   +-----------------------------+
        |                       |
        | 4a. deliver           | 4b. deliver
        v                       v
   +-----------+           +-----------+
   | Receiver A|           | Receiver B|
   | (metadata |           | (needs the|
   |  only)    |           |  payload) |
   +-----------+           +-----------+
        |                       |
        | acts on metadata      | 5. get(claim)
        | alone, done            v
                            +--------------+
                            |  Data Store  |
                            +--------------+
                                   |
                            6. returns payload
                                   |
                                   v
                            +-----------+
                            | Receiver B|
                            | processes |
                            | payload,  |
                            | optionally|
                            | remove()  |
                            +-----------+

   Only the claim (a small key) crosses the Messaging Channel.
   The full payload never enters the broker's own storage layer.
```

## 7. Dynamics

The runtime flow separates cleanly into a write phase, owned by the
Sender, and a read phase, owned by whichever Receiver actually needs the
payload. The two phases are not wrapped in one transaction, which is the
single most important fact about how this pattern behaves under failure.

```
Sender          Data Store        Channel          Receiver B
  |                  |               |                  |
  |-- put(payload) ->|               |                  |
  |                  |-- durable --  |                  |
  |                  |   write done  |                  |
  |<-- claim key ----|               |                  |
  |                  |               |                  |
  |-- publish(claim, metadata) ----->|                  |
  |                  |               |-- deliver ------>|
  |                  |               |                  |
  |                  |<---- get(claim) ------------------|
  |                  |               |                  |
  |                  |-- payload --------------------->  |
  |                  |               |                  |
  |                  |               |          process payload
  |                  |<---- remove(claim) (sync variant) |
  |                  |               |                  |
  |                  |               |            ack the message
```

Two timing notes carry real operational weight. First, the store write
must complete and be confirmed durable before the message publish, never
the other way round. Publishing the claim first risks a Receiver fetching
an object that is not yet written or not yet visible, especially against
an eventually consistent store, see dimension 11. Second, the `remove`
step at the bottom of the diagram belongs to the synchronous deletion
variant only. In the asynchronous variant that step never appears in this
sequence at all, and cleanup happens later, on its own schedule, driven by
a lifecycle policy on the Data Store rather than by the Receiver's own
workflow, exactly the choice Azure's documentation frames as synchronous
versus asynchronous deletion.

## 8. Implementation variants

**Store-then-publish, the classical shape.** The Sender writes the
payload, waits for confirmation, then publishes the claim. This is the
shape shown in dimensions 6 and 7, and every other variant below is a
refinement of it.

**Conditional application.** The Sender checks the payload size against a
threshold and only invokes the pattern when the payload is over it,
sending everything else inline. Azure's own considerations section
recommends exactly this, stating that a sending application should apply
the Claim-Check pattern if the message size surpasses the messaging
system's limit and bypass it for smaller messages to reduce latency
([Microsoft Learn, Claim-Check
pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/claim-check),
verified 2026-08-02). This is the variant demonstrated in the code examples
below, because an unconditional Claim Check on every message, including
tiny ones, is one of the concrete misuses in dimension 11.

**Broker-transparent, event driven generation.** The token is generated
automatically by an event mechanism rather than by application code. In
Azure's own reference implementations, a producer writes the payload to
Blob Storage, and Azure Event Grid fires a blob created event that
generates the claim check and forwards it to the messaging system without
the sending application ever calling a claim generating API directly,
documented across four separate sample combinations of Azure Queue
Storage, Event Hubs, and Service Bus ([Microsoft Learn, Claim-Check
pattern, Claim-check pattern
examples](https://learn.microsoft.com/en-us/azure/architecture/patterns/claim-check),
verified 2026-08-02).

**Client-library transparent claim check.** The application code sends and
receives messages through its normal client library, and the library
itself performs the split, store, and reassemble steps invisibly. The
Amazon SQS Extended Client Library for Java is the clearest named example.
It lets a caller specify whether messages are always stored in Amazon S3
or only when the size of a message exceeds 256 KB, and application code
continues to call `sendMessage` and `receiveMessage` exactly as before
([AWS documentation, Managing large Amazon SQS messages using Java and
Amazon
S3](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/s3-messages.html),
verified 2026-08-02). This variant trades the Sender's explicit control
over the store, shown in dimension 5, for near zero application code
change.

**Encrypted, security first claim check.** The stored object is encrypted
at rest, and access to it is gated separately from access to the message
channel, so a component that can read messages off the broker still
cannot read the sensitive payload without its own, separately granted
credential to the data store. This directly serves the secondary use case
Azure names for sensitive data protection, and it is the variant to
reach for whenever dimension 3's security force dominates over the raw
size force.

**Stack based, intra-pipeline detour.** Rather than crossing a network
boundary, the claim check temporarily shrinks a message for a chain of
in-process filters, then restores the original content at the end of the
chain. Apache Camel implements this with explicit `push` and `pop`
operations on top of its keyed `get`, `getAndRemove`, and `set` operations,
letting a pipeline stack multiple claim checks without needing a key for
each one ([Apache Camel documentation, Claim Check
EIP](https://camel.apache.org/components/latest/eips/claimCheck-eip.html),
verified 2026-08-02). This is the pattern applied inside one process
rather than across a distributed system, useful when a chain of processors
must temporarily strip and later restore attachments or headers.

**Outbox integrated claim check.** The store write happens inside the same
local database transaction that also writes the outbox row driving the
eventual message publish, rather than as a separate, unguarded call before
the publish. This closes part of the write side race named in dimension
11, at the cost of requiring the data store to be reachable from within
the same transactional boundary as the outbox table, which is not always
true for an external object store. This variant composes Claim Check with
Transactional Outbox, see dimension 13, and the trade off described here
is engineering judgement rather than a claim drawn from a named source.

## 9. Known production uses

**Apache Camel, the Claim Check EIP component.** Camel implements the
pattern as a first class enterprise integration pattern component inside
its routing engine, offering five operations, Get, GetAndRemove, Set,
Push, and Pop, and documents them as a direct realization of the classic
Enterprise Integration Patterns Claim Check concept inside a route
([Apache Camel documentation, Claim Check
EIP](https://camel.apache.org/components/latest/eips/claimCheck-eip.html),
verified 2026-08-02). Camel is a widely deployed open source integration
framework, and this is the pattern implemented essentially by name, inside
a general purpose routing engine used across many organizations'
integration layers.

**Microsoft Azure, the Claim-Check pattern reference architecture.**
Microsoft's Azure Architecture Center ships four separate, runnable code
samples on GitHub, each combining a different pair of Azure services,
Azure Queue Storage with Azure Event Grid, Azure Event Hubs with the
Standard API, Azure Service Bus, and Azure Event Hubs over the Kafka API,
all writing large payloads to Azure Blob Storage and passing only a claim
check token through the chosen messaging system ([Microsoft Learn,
Claim-Check pattern, Claim-check pattern
examples](https://learn.microsoft.com/en-us/azure/architecture/patterns/claim-check),
verified 2026-08-02). This is a vendor documented, production oriented
reference implementation, not a toy example, and it is cited by
architecture teams designing large message handling on Azure.

**AWS, the SQS Extended Client Library for Java.** AWS publishes and
maintains an official library, `amazon-sqs-java-extended-client-lib`, that
wraps the standard SQS client so payloads between 256 KB and 2 GB are
stored in an Amazon S3 bucket automatically, with only a small reference
message sent through the SQS queue. The AWS documentation describes it as
letting a caller send a message that references a single message object
stored in an S3 bucket, retrieve the message object from an Amazon S3
bucket, and delete the message object from an Amazon S3 bucket ([AWS
documentation, Managing large Amazon SQS messages using Java and Amazon
S3](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/s3-messages.html),
verified 2026-08-02). AWS's own worked example configures an S3 lifecycle
rule that permanently deletes stored objects fourteen days after creation,
which is a concrete instance of the asynchronous cleanup strategy discussed
in dimensions 8 and 11.

## 10. Consequences

Positive.

- Large payloads stop consuming the message broker's own storage,
  replication, and bandwidth budget, which the Azure Architecture Center
  credits with directly improving efficiency of sending and receiving
  applications and the messaging system ([Microsoft Learn, Claim-Check
  pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/claim-check),
  verified 2026-08-02).
- A cheaper, smaller messaging tier can sometimes replace a premium,
  large-message capable tier, because message bodies stay small once the
  bulk moves out.
- Consumers that only need routing metadata never deserialize or transmit
  the bulky payload at all, which reduces work across every hop that does
  not touch the actual data.
- Sensitive content can be pulled out of every intermediary the broker
  passes through and placed behind its own, independently controlled
  access policy.
- Retrying or replaying a message no longer re-transmits the bulky
  payload, only the small claim check needs to move again.

Negative.

- The message and the payload become two independently failing pieces of
  state with no shared transaction, and every failure mode in dimension 11
  traces back to that gap.
- Every consumer that actually needs the payload gains a second network
  round trip and a new dependency, on the data store's availability,
  authentication, and consistency model, that did not exist when the
  payload travelled inline.
- Cleanup becomes a real design problem rather than something the broker
  handles automatically through its own retention policy, and getting it
  wrong produces either storage growth or premature data loss.
- Observability effort roughly doubles, because a healthy system now needs
  signals from two independent stores rather than one, see dimension 16.
- The pattern adds a small, constant overhead, one extra write and at
  least one extra read per message that needs it, that a small payload
  would never have paid at all.

## 11. Failure modes and misuse

**Claim token expired before consumption.** Symptom. Consumers processing
a genuine, not yet stale, backlog of unprocessed messages start failing
with a not found error when they present their claim, particularly during
a traffic spike or an extended outage of the consuming service. Cause. The
data store's lifecycle or time to live policy deletes an object before the
still-queued message referencing it has been consumed, because the
object's expiry window is shorter than the broker's own maximum message
age or maximum redelivery delay. Fix. Set the object's expiry comfortably
longer than the maximum time a message can plausibly sit unconsumed,
factoring in retry backoff and dead letter delay, or drop independent
expiry entirely and delete strictly on consumption acknowledgement instead.
Treat a genuine claim miss as an alertable event rather than a silently
swallowed failure, exactly the case the `ClaimExpiredError` in the Python
example below is written to surface loudly instead of hiding.

**Orphaned objects, the storage cleanup failure.** Symptom. The object
store's bucket or container grows without bound, or its storage bill
climbs steadily, with objects that no consumer ever fetched and no message
ever referenced a second time. Cause. A synchronous delete tied to
successful consumption never fires, most often because the consuming
process crashed, threw, or was killed between reading the payload and
acknowledging the message, and no independent sweep exists to catch the
gap. Fix. Prefer the asynchronous cleanup variant, an independent lifecycle
or time to live policy on the store itself, as a backstop even when
synchronous deletion is also in place, mirroring the fourteen day S3
lifecycle rule in AWS's own SQS Extended Client Library example. A sweep
that runs on a schedule and is decoupled from any single consumer's health
degrades gracefully in a way a purely synchronous delete cannot.

**Write side race, the message published before the object is visible.**
Symptom. A Receiver processes the message almost immediately after
publish and gets a not found or an incomplete object back from the store,
even though the Sender's write call appeared to succeed. Cause. The Sender
publishes the claim before the store confirms the write is both committed
and visible for reads, which is a real risk against a store with
eventually consistent read after write behaviour, especially across
regions. Fix. Only publish the claim after the store's write call returns
a success acknowledgement backed by a strongly consistent read path for
that object, and add a short bounded retry with backoff on the consumer's
first fetch to absorb any residual replication lag.

**Predictable or over privileged claim tokens.** Symptom. A security
review finds that any component holding broker read access can also read
every stored payload, or that claim keys are sequential and guessable.
Cause. Treating the claim token as security through obscurity rather than
as an actual access control boundary, and granting the data store broad
read access to every consumer instead of scoping it. Fix. Generate keys
from a cryptographically random source, and either issue short-lived,
scoped, pre-signed access to each specific object or enforce per-object
policy so possessing the claim, not merely knowing it exists, is what
grants access.

**Unconditional application to small payloads.** Symptom. A pipeline shows
measurably higher latency and cost after adopting the pattern, even though
most messages were always small. Cause. Every message, regardless of size,
is written to the store and given a claim, exactly the shape Azure's
documentation warns against with its recommendation to apply the pattern
conditionally. Fix. Add the size threshold check shown in dimension 8's
conditional variant, and reserve the pattern for messages that actually
need it.

**Key collision from reused or overwritten storage keys.** Symptom. A
Receiver fetches a payload and gets content that does not match what the
Sender originally wrote, or a payload disappears while a still valid claim
for it exists. Cause. The Sender uses a `set`-style overwrite on a shared
or predictable key instead of minting a fresh, unique key per message.
Fix. Derive the storage key from a message identifier guaranteed unique
per send, a UUID or the broker's own message id, and never reuse a key
across two distinct payloads.

## 12. Trade-off matrix

Compared against named alternatives that solve the same underlying
problem, large data travelling through a constrained channel, across the
forces from dimension 3.

| Force | Claim Check | Content Enricher (reverse direction) | Splitter and Aggregator | Message compression | Broker premium or large-message tier | Transactional Outbox with an inline reference |
|---|---|---|---|---|---|---|
| Reduces bytes on the wire | Strong. Bulk never enters the channel | Not addressed. Adds data, does not remove it | Partial. Splits one large message into many smaller ones, total bytes unchanged | Strong when data compresses well, weak on already-dense binary or media | Not addressed. Raises the ceiling rather than lowering the load | Strong, same mechanism as Claim Check, plus transactional write safety |
| New consistency risk introduced | High. Message and object are two uncoordinated writes | Low. Enrichment reads from a source of truth, no new write | Medium. Aggregator must correctly reassemble every part | Low. Compression and decompression are local, symmetric operations | None. No new state is introduced | Lower than plain Claim Check. Object write and outbox write share one local transaction |
| Operational cost added | Medium. One more store to run and monitor | Low. Usually reuses an existing lookup source | Medium. Aggregator state and timeout handling | Low. A codec, no new infrastructure | Cost shifts to a pricier broker tier instead of new infrastructure | Medium, plus the constraint that the store must be reachable from the outbox transaction |
| Fits binary or media payloads | Strong. Purpose built for this | Poor. Assumes structured, mergeable data | Poor. Splitting a video or PDF meaningfully is rarely possible | Medium. Depends heavily on the codec and the data | Strong, simply avoids the problem at higher cost | Strong, same fit as Claim Check |
| Consumer complexity | Medium. Consumers that need the data add a fetch step | Low. Consumers see one complete message as before | High. Consumers must handle partial and out of order parts | Low. Consumers decompress transparently in most client libraries | None. No consumer code change | Medium, same as Claim Check on the read side |
| Cost profile at scale | Favourable. Object storage is typically the cheapest tier available | Neutral | Neutral to unfavourable, more messages to route and store | Favourable on CPU for the win in bytes, unless compression itself is expensive | Unfavourable. Premium broker tiers charge for the capability directly | Favourable, same profile as Claim Check |

Reading of the table. Claim Check and its Transactional Outbox integrated
variant win decisively whenever the payload is genuinely large, opaque, or
sensitive, binary, media, or bulky documents in particular. Compression
wins when the data is compressible text or structured data and the goal is
purely fewer bytes with no new infrastructure. Splitter and Aggregator
wins when the payload can be meaningfully broken into independently useful
parts, which large binary blobs almost never can. Simply raising the
broker's own limit wins only when the organization already pays for a
premium tier and the payload size problem is occasional rather than
routine, because it solves nothing about the underlying cost or security
forces from dimension 3.

## 13. Related and incompatible patterns

- **Content Enricher.** A near mirror image, catalogued in the same
  Message Transformation chapter of the Enterprise Integration Patterns
  book. Content Enricher adds missing data to a thin message by looking it
  up elsewhere. Claim Check removes bulky data from a fat message by
  storing it elsewhere. A pipeline commonly runs both, Claim Check on the
  way out to shrink a message, and Content Enricher on the way back in to
  restore the fields a particular consumer needs without fetching the
  entire original payload.
- **Splitter.** A substitute in the narrow case where the bulky payload can
  be broken into independently meaningful, reassemblable pieces rather
  than treated as one opaque blob. Where that split is not natural, Claim
  Check is the better fit, see dimension 12.
- **Transactional Outbox.** Composes cleanly, and directly addresses the
  write side half of the consistency force from dimension 3. Writing the
  claimed object inside the same local transaction that also writes the
  outbox row removes the gap between the object existing and the message
  eventually being published, though it does not remove the corresponding
  gap on the read side, deleting the object only once every consumer has
  genuinely finished with it.
- **Materialized View and CQRS.** A substitute when the bulky data is
  structured and queryable rather than genuinely opaque. A blob and
  pointer forces every consumer to fetch the whole object even to read one
  field. A materialized read model, or a CQRS read side built for the
  query pattern, avoids that entirely for structured data, and Claim Check
  should stay reserved for content that is honestly opaque, documents,
  media, and large binary payloads.
- **Gateway Aggregation.** A frequent neighbour rather than a substitute.
  When an aggregating gateway calls several backends and combines their
  responses into one large composite payload, that composite result is
  itself a candidate for a claim check before it travels onward through a
  message driven part of the system.
- **Publisher-Subscriber.** The most common host channel. Claim Check does
  not specify a channel type, and in cloud deployments it most often rides
  on top of a publish subscribe topic, where several independent
  subscribers each decide separately whether they need to fetch the
  payload the claim refers to.
- **Circuit Breaker and Retry.** Directly protect the extra network call
  the pattern introduces. The fetch from the data store, and in some
  implementations the initial store write, is exactly the kind of remote
  call these two patterns exist to guard, with a circuit breaker
  preventing a struggling data store from being hammered by every
  Receiver's fetch, and retry with backoff absorbing the write side race
  described in dimension 11.
- **Two phase commit and strictly transactional messaging.** Conflicts in
  practice rather than in principle. A system that assumes its message
  broker is the single, transactionally consistent source of truth for
  every write in a request cannot simply bolt Claim Check on top without
  first accepting that the object store's state and the message's state
  are no longer coordinated by that same guarantee, see dimension 4's non
  applicability list.

## 14. Refactoring path in and out

Introducing the pattern into a pipeline that currently sends everything
inline, ordered steps.

1. Measure first. Confirm the payload is genuinely, routinely large
   relative to the broker's limit or its observed throughput impact,
   rather than reaching for the pattern on a hunch, per dimension 4.
2. Stand up or identify the data store that will hold the payload,
   confirming it offers strongly consistent reads immediately after a
   write for the objects this pipeline will create.
3. Add the store write and claim generation behind a size threshold check
   in the Sender, so small messages keep travelling inline while only
   oversized ones take the new path, the conditional variant from
   dimension 8.
4. Change the message schema to carry the claim and a small amount of
   routing metadata instead of the bulky field, keeping the change
   additive if any existing consumers cannot be updated in the same
   deployment.
5. Update every Receiver that genuinely needs the payload to fetch it by
   claim, and leave Receivers that only needed metadata entirely
   unchanged, since that is one of the pattern's direct wins.
6. Decide the cleanup strategy explicitly, synchronous delete on
   consumption, an independent lifecycle policy, or both together as a
   primary path with a backstop, rather than leaving it as an
   afterthought, per dimension 11.
7. Add the observability signals from dimension 16 before declaring the
   migration complete, particularly the claim miss counter, since that
   metric is the earliest warning of every failure mode in this pattern.

Removing the pattern once it stops earning its place, ordered steps.

1. Confirm the payload sizes involved have genuinely fallen, or the broker
   tier has changed, so inline delivery is realistic again, rather than
   removing the pattern while the original problem still exists.
2. Widen the conditional threshold from dimension 8 gradually rather than
   removing the store path outright, watching broker throughput and cost
   as more messages travel inline.
3. Once no traffic is taking the claim check path in practice, remove the
   store write and claim generation from the Sender, and change the
   schema to carry the payload directly again.
4. Update Receivers that were fetching by claim to read the inline payload
   instead, and delete the now unused fetch and cleanup code.
5. Decommission the data store, or repurpose it, only after a monitoring
   window confirms no client is still presenting a claim against it,
   because an in flight message created before the change can still
   reference an object created under the old path.

## 15. Testing and verification

Easier because of the pattern.

- The data store's read and write behaviour can be tested against a fake,
  in memory implementation of its interface, exactly as the `InMemoryStore`
  and `DataStore` types in the code examples below demonstrate, with no
  real object storage service needed for most test runs.
- The conditional threshold from dimension 8 is a single, easily
  parameterized boundary, which makes it a natural fit for a boundary
  value test, one payload one byte under the limit, one exactly at the
  limit, and one one byte over it, asserting the correct path is taken in
  each case.
- Because the claim itself is opaque to consumers, a test double for the
  Sender's storage client can return deterministic, predictable keys
  instead of random ones, making assertions on message content
  straightforward.

Harder because of the pattern.

- A meaningful integration test now needs two systems running together, or
  convincingly faked together, the message channel and the data store,
  rather than one, and the interaction between their two independent
  failure modes is exactly what unit tests against either system alone
  cannot catch.
- The consistency race from dimension 11, where a message is published
  before the store write is durably visible, is a timing bug, and timing
  bugs resist deterministic unit tests unless the store's consistency
  behaviour is explicitly modelled and its delay is injectable.

Techniques that apply directly.

- **Fake store with an injectable delay.** Wrap the real store behind an
  interface, per dimension 5, and give the test double the ability to
  simulate a period during which a written object is not yet readable,
  reproducing the eventual consistency race from dimension 11 on demand
  rather than hoping to catch it in a flaky integration environment.
- **Claim miss injection.** A test double that deliberately returns not
  found for a specific key exercises the failure path directly, asserting
  the Receiver surfaces a clear, loud error, matching the
  `ClaimExpiredError` behaviour in the Python example, rather than
  silently treating a missing payload as an empty one.
- **Idempotent redelivery test.** Because most brokers offer at least once
  delivery, a test that delivers the same claim bearing message twice
  should assert the consuming side behaves correctly whether the object
  was already deleted by a first successful processing pass or still
  present because the first pass failed after fetching but before
  acknowledging.
- **Lifecycle or time to live simulation.** For the asynchronous cleanup
  variant, a test that advances a fake clock past the configured
  expiration, exactly the pattern in the Python example's
  `sweep_expired` call, verifies cleanup fires only when it should and
  never before a plausible processing window has passed.

## 16. Observability signals

The pattern introduces a second system into the critical path, so a
healthy Claim Check deployment needs signals from both the messaging
channel and the data store, correlated by the claim itself.

What to record.

- A counter of claim checks created, labelled by producer and message
  type, giving the baseline rate against which every other metric below
  is read.
- A counter of claim fetches, split by hit and miss, where the miss branch
  is the single most important number in the whole pattern, since a
  nonzero, rising miss rate is the earliest signal of either the expiry
  failure mode or the write side race from dimension 11.
- A histogram of fetch latency for the data store, separated from the
  broker's own delivery latency, so a slow store and a slow broker never
  get conflated into one undiagnosable message processing is slow
  symptom.
- For the asynchronous cleanup variant, a gauge of object count and total
  bytes currently held in the store, alongside a counter of objects
  removed per sweep, so an unbounded growth trend, the orphaned object
  failure mode, shows up on a dashboard well before a storage bill does.
- A counter of store write failures on the send side, since a Sender that
  cannot durably write a payload must never proceed to publish a claim for
  it, and this counter is the guardrail proving that invariant holds in
  production.

A healthy instance on a dashboard. The claim miss rate sits at or near
zero, fetch latency is flat and well under the surrounding request budget,
and the stored object count tracks the expected consumption rate rather
than climbing without bound. Created and fetched counts stay roughly in
proportion once accounting for consumers that intentionally never fetch.

A failing instance. A rising claim miss rate that correlates with recent
deploys or traffic spikes points at the expiry failure mode. A steadily
climbing object count with a flat or falling fetch count points at the
orphaned object failure mode. A fetch latency histogram that develops a
long tail only during known peak write periods points at the write side
consistency race. Any nonzero store write failure count paired with a
nonzero claim publish count is itself a defect, since it means the
invariant from the last bullet above has been violated somewhere in the
Sender's code path.

## 17. Security and privacy implications

Unlike Factory Method, which is largely silent on security in its
classical form, Claim Check has real, structural security consequences
the moment it is adopted, because it deliberately relocates data out of
one system and into another.

**A genuine reduction in exposure surface, when done correctly.** Every
intermediary between Sender and Receiver that only ever sees the broker,
a monitoring console, a message inspection tool, an operations engineer
debugging a stuck queue, no longer sees the payload at all, only the
claim. This is precisely the secondary use case the Azure Architecture
Center names for sensitive data protection, and the Well-Architected
Framework's security guidance states directly that the pattern can
extract sensitive data from messages and store it in a secure data store
so that only the services intended to use the sensitive data can access
it, while hiding it from unrelated services, such as those used for queue
monitoring ([Microsoft Learn, Claim-Check pattern, Security
pillar](https://learn.microsoft.com/en-us/azure/architecture/patterns/claim-check),
verified 2026-08-02). This benefit is real only when the data store's own
access control is genuinely tighter than the broker's, not merely
different from it.

**Claim tokens are an access control surface, not decoration.** A claim
that grants access to whoever presents it is functionally a bearer
credential for the object it names. Treating it as an obscure identifier
rather than a scoped credential is the exact misuse named in dimension 11.
The stronger designs generate cryptographically random keys, scope object
access per consumer with short lived, pre-signed access rather than a
standing broad read grant, and log every access to the store separately
from the broker's own delivery logs, so an audit trail exists for who
actually read a given payload, not merely who received a message
referencing it.

**Data residency and compliance now span two systems.** Once the payload
lives in an object store that may sit in a different region, a different
account, or under a different retention regime than the message broker,
any data residency or regulatory retention requirement applying to the
payload has to be enforced at the store, and separately reconciled against
whatever retention the broker applies to its own message metadata. A
retention policy correctly configured on the broker gives no guarantee
whatsoever about the retention or deletion of the payload sitting in the
separate store, which is engineering judgement rather than a claim drawn
from the cited sources, but follows directly from the two systems being
independently governed.

**Denial of service through uncontrolled store writes.** A Sender that
accepts an oversized or attacker influenced payload and writes it to the
store on every request, with no per request or per tenant bound on size or
frequency, turns the data store into an amplification target, a small,
cheap message can trigger an arbitrarily expensive write. Bounding payload
size at the point of acceptance, before it ever reaches the Claim Check
logic, and rate limiting writes per caller, closes this rather than
leaving it to the store's own quota to absorb.

On broad privacy grounds the pattern is neutral by default and favourable
when deliberately used for its sensitive data protection use case. The one
consistent caveat across every implementation is that the claim key
itself, and any metadata still travelling inline in the message, must be
reviewed for what they leak. A predictable key or a descriptive metadata
field can quietly reconstruct exactly the sensitive information the
pattern was adopted to hide.

## Code examples

Three languages, each idiomatic to a different implementation shape of
the pattern. TypeScript demonstrates the conditional variant, deciding
per message whether a payload needs a claim, with delete on consume.
Python demonstrates the asynchronous cleanup variant, where an
independent sweep function, driven by an explicit clock, removes expired
objects on its own schedule, matching the lifecycle policy approach AWS
documents for its SQS Extended Client Library. Go demonstrates the
pattern under concurrent producers writing to a shared, mutex guarded
store, closer to how a real service handles several Senders publishing at
once. All three compiled or ran successfully against the toolchains
available in this environment, `tsc` 7.0.2, `python3` 3.14.6, and `go`
1.26.4.

### TypeScript

```typescript
interface DataStore {
  put(key: string, payload: string): Promise<void>;
  get(key: string): Promise<string | undefined>;
  remove(key: string): Promise<void>;
}

interface Channel<T> {
  send(message: T): Promise<void>;
  receive(): Promise<T | undefined>;
}

type Envelope =
  | { kind: "inline"; id: string; body: string }
  | { kind: "claim"; id: string; claim: string; sizeBytes: number };

class InMemoryStore implements DataStore {
  private readonly objects = new Map<string, string>();

  async put(key: string, payload: string): Promise<void> {
    this.objects.set(key, payload);
  }

  async get(key: string): Promise<string | undefined> {
    return this.objects.get(key);
  }

  async remove(key: string): Promise<void> {
    this.objects.delete(key);
  }

  size(): number {
    return this.objects.size;
  }
}

class InMemoryChannel<T> implements Channel<T> {
  private readonly buffer: T[] = [];

  async send(message: T): Promise<void> {
    this.buffer.push(message);
  }

  async receive(): Promise<T | undefined> {
    return this.buffer.shift();
  }
}

// Conditional variant: only payloads over this size get a claim.
// Small payloads travel inline and skip the extra round trip.
const INLINE_LIMIT_BYTES = 256;

async function sendWithClaimCheck(
  store: DataStore,
  channel: Channel<Envelope>,
  id: string,
  payload: string
): Promise<void> {
  if (payload.length <= INLINE_LIMIT_BYTES) {
    await channel.send({ kind: "inline", id, body: payload });
    return;
  }
  const claim = `claims/${id}`;
  await store.put(claim, payload);
  await channel.send({
    kind: "claim",
    id,
    claim,
    sizeBytes: payload.length,
  });
}

// Delete on consume, tied to the workflow, not a background sweep.
async function receiveAndResolve(
  store: DataStore,
  channel: Channel<Envelope>
): Promise<string | undefined> {
  const message = await channel.receive();
  if (!message) {
    return undefined;
  }
  if (message.kind === "inline") {
    return message.body;
  }
  const payload = await store.get(message.claim);
  if (!payload) {
    throw new Error(`claim miss: ${message.claim} was not found in the store`);
  }
  await store.remove(message.claim);
  return payload;
}

async function main(): Promise<void> {
  const store = new InMemoryStore();
  const channel = new InMemoryChannel<Envelope>();

  const small = "ok";
  const large = "x".repeat(4096);

  await sendWithClaimCheck(store, channel, "order-1", small);
  await sendWithClaimCheck(store, channel, "order-2", large);

  const first = await receiveAndResolve(store, channel);
  const second = await receiveAndResolve(store, channel);

  console.log("first payload length:", first?.length);
  console.log("second payload length:", second?.length);
  console.log("objects remaining in store after both consumed:", store.size());
}

main();
```

Compiled with `tsc --target es2020 --module commonjs --strict`, no errors,
and run with `node`, producing "first payload length. 2", "second payload
length. 4096", and "objects remaining in store after both consumed. 0",
confirming the small message travelled inline while the large one used the
store and was cleaned up on consumption.

### Python

```python
"""Claim Check pattern, asynchronous cleanup variant.
A sweep function deletes expired objects, decoupled from consuming."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Optional


@dataclass
class StoredObject:
    payload: bytes
    expires_at: float


class DataStore:
    def __init__(self) -> None:
        self._objects: dict[str, StoredObject] = {}

    def put(self, payload: bytes, ttl_seconds: float) -> str:
        key = f"claims/{uuid.uuid4()}"
        self._objects[key] = StoredObject(payload, time.time() + ttl_seconds)
        return key

    def get(self, key: str) -> Optional[bytes]:
        obj = self._objects.get(key)
        return obj.payload if obj else None

    def sweep_expired(self, now: float) -> list[str]:
        expired = [k for k, v in self._objects.items() if v.expires_at <= now]
        for key in expired:
            del self._objects[key]
        return expired

    def size(self) -> int:
        return len(self._objects)


@dataclass
class Envelope:
    order_id: str
    inline_body: Optional[bytes] = None
    claim: Optional[str] = None


class Channel:
    def __init__(self) -> None:
        self._buffer: list[Envelope] = []

    def send(self, message: Envelope) -> None:
        self._buffer.append(message)

    def receive(self) -> Optional[Envelope]:
        return self._buffer.pop(0) if self._buffer else None


INLINE_LIMIT_BYTES = 256


def send_with_claim_check(
    store: DataStore, channel: Channel, order_id: str, payload: bytes, ttl_seconds: float
) -> None:
    if len(payload) <= INLINE_LIMIT_BYTES:
        channel.send(Envelope(order_id=order_id, inline_body=payload))
        return
    claim = store.put(payload, ttl_seconds)
    channel.send(Envelope(order_id=order_id, claim=claim))


class ClaimExpiredError(RuntimeError):
    """A claim was presented after the sweep already removed it."""


def receive_and_resolve(store: DataStore, channel: Channel) -> Optional[bytes]:
    message = channel.receive()
    if message is None:
        return None
    if message.inline_body is not None:
        return message.inline_body
    assert message.claim is not None
    payload = store.get(message.claim)
    if payload is None:
        raise ClaimExpiredError(f"{message.claim} was swept before consumption")
    return payload


def main() -> None:
    store = DataStore()
    channel = Channel()

    small = b"ok"
    large = b"x" * 4096

    send_with_claim_check(store, channel, "order-1", small, ttl_seconds=60.0)
    send_with_claim_check(store, channel, "order-2", large, ttl_seconds=60.0)

    print("stored objects before consumption:", store.size())

    first = receive_and_resolve(store, channel)
    second = receive_and_resolve(store, channel)

    print("first payload length:", len(first) if first else None)
    print("second payload length:", len(second) if second else None)

    # Nothing has expired yet at real "now", so the sweep is a no-op.
    swept_now = store.sweep_expired(now=time.time())
    print("swept at real time (should be empty, TTL not reached):", swept_now)
    print("stored objects still present until sweep:", store.size())

    far_future_sweep = store.sweep_expired(now=time.time() + 3600)
    print("objects removed by a far-future sweep:", len(far_future_sweep))


if __name__ == "__main__":
    main()
```

Run with `python3`, producing "stored objects before consumption. 1",
confirming only the large payload took the store path, followed by both
lengths resolving correctly, an empty result from the immediate sweep
because the sixty second time to live had not elapsed, and one object
removed once the sweep was run against a simulated point an hour in the
future, demonstrating the expiry gap named in dimension 11 directly.

### Go

```go
package main

import (
	"errors"
	"fmt"
	"sync"
)

type dataStore struct {
	mu      sync.Mutex
	objects map[string][]byte
}

func newDataStore() *dataStore {
	return &dataStore{objects: make(map[string][]byte)}
}

func (s *dataStore) put(key string, payload []byte) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.objects[key] = payload
}

func (s *dataStore) get(key string) ([]byte, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	payload, ok := s.objects[key]
	return payload, ok
}

func (s *dataStore) remove(key string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.objects, key)
}

func (s *dataStore) size() int {
	s.mu.Lock()
	defer s.mu.Unlock()
	return len(s.objects)
}

type envelope struct {
	orderID    string
	inlineBody []byte
	claim      string
}

const inlineLimitBytes = 256

var errClaimMiss = errors.New("claim miss: object not found in the store")

// sendWithClaimCheck stores the payload only past the inline limit.
// Small payloads travel in the envelope itself.
func sendWithClaimCheck(store *dataStore, channel chan<- envelope, orderID string, payload []byte) {
	if len(payload) <= inlineLimitBytes {
		channel <- envelope{orderID: orderID, inlineBody: payload}
		return
	}
	claim := fmt.Sprintf("claims/%s", orderID)
	store.put(claim, payload)
	channel <- envelope{orderID: orderID, claim: claim}
}

func receiveAndResolve(store *dataStore, channel <-chan envelope) ([]byte, error) {
	msg, ok := <-channel
	if !ok {
		return nil, nil
	}
	if msg.inlineBody != nil {
		return msg.inlineBody, nil
	}
	payload, found := store.get(msg.claim)
	if !found {
		return nil, fmt.Errorf("%s: %w", msg.claim, errClaimMiss)
	}
	store.remove(msg.claim)
	return payload, nil
}

func main() {
	store := newDataStore()
	channel := make(chan envelope, 2)

	small := []byte("ok")
	large := make([]byte, 4096)
	for i := range large {
		large[i] = 'x'
	}

	var producers sync.WaitGroup
	producers.Add(2)
	go func() {
		defer producers.Done()
		sendWithClaimCheck(store, channel, "order-1", small)
	}()
	go func() {
		defer producers.Done()
		sendWithClaimCheck(store, channel, "order-2", large)
	}()
	producers.Wait()
	close(channel)

	total := 0
	for {
		payload, err := receiveAndResolve(store, channel)
		if err != nil {
			fmt.Println("error:", err)
			continue
		}
		if payload == nil {
			break
		}
		total += len(payload)
	}

	fmt.Println("total bytes resolved across both messages:", total)
	fmt.Println("objects remaining in store after consumption:", store.size())
}
```

Run with `go run`, after a clean `gofmt -l` and a clean `go vet` on the
file, producing "total bytes resolved across both messages. 4098", the sum
of the two byte lengths sent, and "objects remaining in store after
consumption. 0", confirming the mutex guarded store handled two concurrent
producers correctly and the consumed claim was removed.

Java, Rust, and Swift are omitted from this entry. Rust and Swift were
available in this environment but the pattern's basic shape, a keyed
put and get against an external store plus a small reference travelling
through a channel, does not change in a way that would justify a fourth
near identical example once TypeScript, Python, and Go each already show a
distinct implementation angle, conditional dispatch, time based cleanup,
and concurrency safety respectively.

## 18. References

- Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns.
  Designing, Building, and Deploying Messaging Solutions*, Addison-Wesley,
  2003, Message Transformation chapter, the Claim Check pattern.
- [Enterprise Integration Patterns, Claim Check (Store In Library)](https://www.enterpriseintegrationpatterns.com/patterns/messaging/StoreInLibrary.html),
  verified 2026-08-02.
- [Enterprise Integration Patterns, messaging pattern index](https://www.enterpriseintegrationpatterns.com/patterns/messaging/),
  verified 2026-08-02.
- [Microsoft Learn, Claim-Check pattern, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/claim-check),
  verified 2026-08-02.
- [AWS documentation, Managing large Amazon SQS messages using Java and Amazon S3](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/s3-messages.html),
  verified 2026-08-02.
- [Apache Camel documentation, Claim Check EIP](https://camel.apache.org/components/latest/eips/claimCheck-eip.html),
  verified 2026-08-02.
- [AWS open source, amazon-sqs-java-extended-client-lib](https://github.com/awslabs/amazon-sqs-java-extended-client-lib),
  linked directly from the AWS documentation above, verified 2026-08-02.
