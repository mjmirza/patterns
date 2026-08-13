---
name: Claim Check
slug: claim-check
family: 07-integration
category: Integration
aliases: ["Store in Library (early EIP working title)", "Claim-Check Token", "Reference Message Pattern"]
first_described: "Hohpe and Woolf 2003"
maturity: canonical
related: [content-enricher, message-expiration, guaranteed-delivery, dead-letter-channel, saga]
incompatible_with: []
verified: 2026-08-02
---

# Claim Check

## 1. Name, aliases, and lineage

The canonical name is Claim Check. The pattern is catalogued in Gregor Hohpe
and Bobby Woolf, *Enterprise Integration Patterns. Designing, Building, and
Deploying Messaging Solutions*, Addison-Wesley, 2003, in the Message
Construction chapter. The companion website states the intent plainly, that
the pattern exists to "reduce the data volume of message sent across the
system without sacrificing information content," and gives the solution as
follows. "Store message data in a persistent store and pass a Claim Check to
subsequent components. These components can use the Claim Check to retrieve
the stored information."
([enterpriseintegrationpatterns.com, Claim Check](https://www.enterpriseintegrationpatterns.com/patterns/messaging/StoreInLibrary.html),
verified 2026-08-02, book citation Bobby Woolf and Gregor Hohpe, copyright
line reading 2003, 2023 on the current page).

The page's own URL is `StoreInLibrary.html`, not `ClaimCheck.html`. That is an
observable fact about the site's file naming, not a claim about the printed
book text, and it is consistent with how the EIP catalog evolved during
authoring. Several patterns in the book carry a published name that differs
from the working file name the authors used while drafting the site. Read as
evidence rather than as a documented anecdote, it suggests an early working
title of "Store in Library" for what shipped as "Claim Check." This is stated
here as an inference from the URL structure, not as a sourced historical
fact, and a reader who wants the definitive account should consult the
printed book or an interview with the authors rather than treat the URL
alone as proof.

The name itself is an analogy borrowed from air travel and coat-check
counters. A traveler checking luggage receives a small paper or plastic tag,
the claim check, that carries no luggage of its own weight or bulk. The
traveler continues onward unburdened, and presents the claim check at the
destination to retrieve the actual bag. The EIP page draws this analogy
directly, comparing the pattern to "when you check your luggage. You are
given a receipt for your luggage instead of having to carry it around with
you"
([enterpriseintegrationpatterns.com, Claim Check](https://www.enterpriseintegrationpatterns.com/patterns/messaging/StoreInLibrary.html),
verified 2026-08-02).

Cloud vendors have since published their own restatements of the same
pattern under the same name. Microsoft's Azure Architecture Center writes it
Claim-Check with a hyphen and defines it as storing "a large message payload
in an external data store" and sending "only a reference token, called a
*claim check*, through a messaging system"
([Microsoft Learn, Claim-Check pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/claim-check),
verified 2026-08-02). No vendor has proposed a competing name for the pattern
itself, though implementation-specific artifacts inside a given product
carry their own vocabulary, for example a reference message in some
messaging middleware literature, or a pointer message in ad hoc engineering
blog posts. None of those terms has independent lineage back to a named
catalog entry the way Claim Check does, so this entry treats them as
informal synonyms rather than as separate patterns.

## 2. Problem and context

A component in a message-based system needs to communicate a large amount of
data, an image, a video, a document, a bulk export, a machine learning
feature vector, a full customer record, to one or more downstream
components, but the transport connecting them was not built to carry that
much data per message.

This shows up in a codebase or an architecture diagram in a specific shape.
A message broker, queue, or event bus sits between a producer and one or
more consumers. The broker enforces, or performs badly past, some maximum
message size. Amazon SQS enforces 256 KB per message, stated directly in
AWS's own example code as "the standard maximum message size"
([AWS documentation, Managing large Amazon SQS messages using Java and
Amazon S3](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/s3-messages.html),
verified 2026-08-02). Azure Service Bus enforces 256 KB per message on the
Basic and Standard tiers, and up to 100 MB for a single message over AMQP on
Premium, with a 1 MB cap for batched sends across all protocols and tiers
([Microsoft Learn, Azure Service Bus quotas and limits](https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-quotas),
verified 2026-08-02). Google Cloud Pub/Sub caps the `data` field of a single
message at 10 MB
([Google Cloud documentation, Pub/Sub quotas and limits](https://docs.cloud.google.com/pubsub/quotas),
verified 2026-08-02). These are not arbitrary numbers picked by one vendor.
Every message broker the pattern applies to draws a line somewhere, because
brokers are built to hold many small messages in memory and replicate them
quickly, and a broker asked to hold gigabyte-scale payloads in the same
storage tier as its routing metadata degrades for every tenant sharing that
broker, not only the one sending the large payload.

The naive response is to raise the limit, if the broker allows it, or to
split the payload across many small messages and reassemble it downstream.
Both responses treat the symptom. Raising the limit, and Azure Premium's 100
MB tier is the vendor's own answer to this pressure, still leaves the broker
storing and replicating the full payload, which is expensive at scale even
when it fits, and does nothing to protect components that only need to read
the message envelope, not the payload, from wasted bandwidth and
deserialization cost. Splitting into chunks reintroduces a hand-rolled
reassembly and ordering problem that guaranteed-delivery message brokers
already solved once for whole messages and now have to solve again for
chunk sequences.

The context in which Claim Check is the right answer has three parts,
echoed independently by Microsoft's own framing of when to use the pattern
([Microsoft Learn, Claim-Check pattern, "When to use the Claim-Check
pattern"](https://learn.microsoft.com/en-us/azure/architecture/patterns/claim-check),
verified 2026-08-02).

- The payload is large relative to the transport's practical or enforced
  limit, or large enough that carrying it through every hop in a multi-step
  pipeline, serialize, deserialize, encrypt, decrypt, log, route, adds up to
  real latency and cost even when no single hop rejects the message.
- A durable, addressable external store already exists, or is cheap to stand
  up, that both the producer and every consumer of the payload can reach,
  object storage, a blob store, a shared file system, a database with a
  binary column, a content-addressed store.
- Not every downstream component needs the payload itself. Some only need
  to route, filter, or audit based on metadata that fits comfortably inside
  a small message, and those components should never pay the cost of
  touching the large payload at all.

## 3. Forces

Claim Check trades one set of costs for another rather than removing cost
outright. Naming the forces honestly is what separates a correct
application of the pattern from a reflexive one applied to every message
regardless of size.

**Transport size and throughput versus storage indirection.** Removing the
payload from the message body keeps the broker fast and cheap for every
consumer, including consumers that never touch the payload. In exchange, the
system now depends on a second store being reachable, and every consumer
that does need the payload pays a round trip to that store on top of the
message receive. For a payload genuinely near the broker's limit this trade
favors storage indirection heavily. For a payload comfortably under the
limit, the trade is a net loss, an extra network hop and an extra failure
mode for no benefit.

**Consistency between the message and the stored payload.** The write to the
store and the send of the message are two separate operations against two
separate systems. If the store write succeeds and the message send fails,
the system has orphaned data nobody will ever retrieve. If the message send
succeeds and the store write failed or has not yet become visible, eventual
consistency on some object stores, a consumer receives a claim check that
resolves to nothing. The pattern does not solve this on its own. It composes
with delivery guarantees and, in the harder cases, with transactional
outbox or saga-style compensation, discussed in dimension 13.

**Coupling to the store's availability and access model.** Every consumer
that needs the payload now has a runtime dependency on the external store's
reachability, authentication, and permission model, in addition to the
broker's. A consumer that could previously process a message with only a
queue client library now also needs a storage client, credentials scoped to
read that store, and its own retry and backoff logic against a second
service with its own failure modes.

**Lifecycle and cost of the stored payload.** Message brokers already give
message expiration and dead-letter semantics for free in most products. An
externally stored payload does not inherit those semantics automatically.
The system has to decide, and enforce, when a stored payload is deleted, and
that decision has real storage cost attached to it if left unmade.
Microsoft's own guidance names this directly as an issue to consider,
telling readers to delete consumed messages and payloads once a receiving
application has consumed them, unless the payload needs to be archived
([Microsoft Learn, Claim-Check pattern, "Issues and considerations with the
Claim-Check pattern"](https://learn.microsoft.com/en-us/azure/architecture/patterns/claim-check),
verified 2026-08-02).

**Security surface, in both directions.** Moving a payload out of the
message can reduce exposure, because the broker, and anything with
visibility into broker traffic such as monitoring or queue-inspection
tooling, never sees the sensitive content, only an opaque reference.
Microsoft names this as a secondary use case in its own right, not only a
side effect of size management, writing that the Claim-Check pattern is
appropriate whenever "payloads contain sensitive data that you don't want
visible to the messaging system"
([Microsoft Learn, Claim-Check pattern, "When to use the Claim-Check
pattern"](https://learn.microsoft.com/en-us/azure/architecture/patterns/claim-check),
verified 2026-08-02). The reverse force applies with equal weight. The
external store now becomes the place an attacker targets, and a claim check
token that is guessable, sequential, or insufficiently scoped turns the
pattern into a confused-deputy problem where possessing the small message is
enough to fetch data the holder was never meant to see. Dimension 17 treats
this in depth.

## 4. Applicability and non-applicability

Reach for Claim Check when payload size or payload sensitivity, not message
volume or message ordering, is the pressure the system is under.

- The payload approaches or exceeds the broker's documented limit for a
  single message, whether that limit is a hard rejection, Amazon SQS's 256
  KB ceiling, Google Cloud Pub/Sub's 10 MB ceiling, or a soft tier boundary
  the team does not want to pay to raise, Azure Service Bus Premium's 100 MB
  tier over the 256 KB Standard tier.
- The payload is only needed by a minority of the consumers on a given
  channel, and the majority would otherwise pay deserialization and network
  cost for data they discard.
- The payload contains data that should not be visible to broker-level
  tooling, logging, or operators with queue access, and an access-controlled
  external store already exists or is cheap to add.
- The system has multiple hops, a pipeline of several processing stages,
  where carrying the full payload through every hop multiplies
  serialization and network cost that carrying only a reference avoids.
- Payload durability and retention requirements differ from message
  durability and retention requirements. A message can safely expire from
  the broker after delivery while the underlying document needs to persist
  for years for compliance reasons, or the reverse.

The non-applicability list below matters at least as much, and each item
carries the specific reason the pattern is the wrong tool.

- **Small, uniformly-sized messages, even at high volume.** Claim Check
  answers a size problem, not a throughput problem. A system pushing
  millions of 50-byte sensor readings per second needs partitioning,
  batching, and backpressure handling, not an external store per reading.
  Adding a store round trip to every message in that workload multiplies
  latency and cost for no size benefit, and most brokers already handle
  high-volume small messages well.
- **Payloads that are large only occasionally, with no consistent size
  threshold policy.** If the team applies Claim Check ad hoc, per message,
  based on a developer's guess at the moment of writing rather than a
  measured threshold, every consumer now has to handle two message shapes,
  one with an inline payload and one with a reference, and the branching
  logic to tell them apart becomes a second source of defects. Microsoft's
  own guidance frames the threshold decision as something the sending
  application should apply conditionally, incorporating logic that reaches
  for the pattern only once a message surpasses the transport's limit and
  bypassing it for smaller messages
  ([Microsoft Learn, Claim-Check pattern, "Issues and considerations with
  the Claim-Check pattern"](https://learn.microsoft.com/en-us/azure/architecture/patterns/claim-check),
  verified 2026-08-02). Do not apply the pattern without codifying that
  threshold as a policy every producer follows.
- **Real-time or low-latency paths where an extra network hop is
  unacceptable.** A trading system, a game server tick loop, or a voice
  codec pipeline cannot absorb the round trip to an external store on the
  hot path. If the payload is genuinely too large for the transport in that
  context, the fix is choosing a transport built for large low-latency
  payloads, a dedicated media stream, a shared-memory ring buffer, rather
  than adding storage indirection to a path that cannot tolerate its
  latency.
- **Systems with no durable external store, and no budget to add one.** The
  pattern assumes the store is at least as reliable as the message channel.
  Standing up a new storage dependency purely to unblock one oversized
  message type, without addressing its operational ownership, backup, and
  access control, moves the size problem into an unmanaged new failure
  surface rather than solving it.
- **Payloads that are inherently transient and cheap to regenerate.** If the
  large data can be recomputed by the consumer from information already in
  the message, or from a cache the consumer already maintains, storing and
  retrieving it externally adds cost and a consistency risk for no benefit
  over regeneration.

## 5. Structure

The pattern names five participants, matching the five-step flow the EIP
catalog page itself lists
([enterpriseintegrationpatterns.com, Claim Check](https://www.enterpriseintegrationpatterns.com/patterns/messaging/StoreInLibrary.html),
verified 2026-08-02).

**Sender.** The component that originates a message carrying a payload
large enough, or sensitive enough, to warrant removal from the message body.

**Data Store.** A durable, addressable, external persistence layer, separate
from the message channel, capable of storing the payload and returning it
on request by a key. In practice this is object storage, Amazon S3, Azure
Blob Storage, Google Cloud Storage, a shared file system, or a database.

**Claim Check.** The reference itself, not a participant with behavior but
an artifact. A unique, resolvable key that identifies exactly one stored
payload and, ideally, carries enough scoping, an access-controlled URL, a
short-lived signed token, that presenting it is both necessary and
sufficient to retrieve the payload, and nothing more than that payload.

**Message Channel.** The transport carrying the now-lightweight message,
containing the claim check plus whatever metadata downstream routing and
filtering components need without touching the payload.

**Receiver.** The component that reads the message, extracts the claim
check, and, only if it actually needs the payload, presents the claim check
to the Data Store to retrieve it. The EIP page describes this retrieval role
through the lens of the Content Enricher pattern, since resolving a claim
check into a full payload is exactly what a Content Enricher does, enrich a
thin message with data pulled from an external source.

Two roles deserve separate naming because they are easy to conflate in an
implementation, even though the catalog treats them as one logical step.
The Check-In responsibility, write the payload, mint the claim check, strip
the payload from the outgoing message, and the Check-Out responsibility,
read the claim check, retrieve the payload, optionally delete it once
consumed, are frequently implemented as two distinct pieces of code,
sometimes in different components entirely, particularly when the data
store enforces different access policies for writers and readers.

## 6. ASCII structure diagram

```text
                         +-------------------------------+
                         |          Data Store            |
                         |  (object storage / blob /       |
                         |   file share / database)        |
                         +----------------+-----------------+
                                  ^                |
                         (2) put  |                | (5) get
                         payload  |                | payload
                                  |                v
   +----------+        +---------+---------+     +------------------+
   |  Sender  |  (1)   |     Check-In       |     |    Check-Out     |
   |          |------->|  (mints the claim  |     | (resolves the    |
   +----------+ large  |     check)         |     |  claim check)    |
                payload +---------+---------+     +---------+--------+
                                  |                          ^
                         (3) send | thin message              | (4) thin message
                         (claim   | + claim check              | + claim check
                          check)  v                          |
                          +---------------------------+--------+
                          |      Message Channel                |
                          |  (queue, topic, event bus)           |
                          +---------------------------------------+
                                         |
                                         v
                                 +---------------+
                                 |   Receiver    |
                                 +---------------+
```

## 7. Dynamics

The runtime sequence follows the same five steps the pattern's origin
describes
([enterpriseintegrationpatterns.com, Claim Check](https://www.enterpriseintegrationpatterns.com/patterns/messaging/StoreInLibrary.html),
verified 2026-08-02), expanded here with the branch points a real
implementation has to decide.

```text
Sender                 Check-In         Data Store        Channel          Receiver
  |                        |                 |               |                |
  | large payload arrives  |                 |               |                |
  |----------------------->|                 |                |                |
  |                        | size >= threshold?               |                |
  |                        |----(yes)------->|                |                |
  |                        | put(payload) -> key              |                |
  |                        |<----------------|                |                |
  |                        | build thin message                |                |
  |                        | { claim_check = key, meta... }    |                |
  |                        |------------------------------->---|                |
  |                        |                 |               | route/filter    |
  |                        |                 |               | on meta only    |
  |                        |                 |               |--------------->|
  |                        |                 |               |                |
  |                        |                 |               |  needs payload? |
  |                        |                 |               |----(yes)------->
  |                        |                 |               |                | get(key)
  |                        |                 |               |                |-------->|
  |                        |                 |               |                |<--------|
  |                        |                 |               |                | payload
  |                        |                 |               |                | process
  |                        |                 |               |                |
  |                        |                 |               |                | delete(key)?
  |                        |                 |               |                | (sync or async,
  |                        |                 |               |                |  see dimension 4)
```

Two branch points carry real design weight and are worth calling out
separately from the diagram. The size-threshold check at Check-In must be a
deterministic policy, not a per-message ad hoc decision, or the Receiver
cannot reliably tell an inline payload from a claim check without inspecting
message content it may not otherwise need to touch. Most production
implementations solve this by always sending a claim check for a given
message type, or by carrying an explicit boolean or type discriminator
field in the message envelope rather than inferring shape from content. The
deletion step at the end is genuinely optional and its timing is a policy
decision on its own, covered in dimension 4's applicability discussion and
revisited in dimension 16.

## 8. Implementation variants

**Always-claim-check per message type.** The simplest and most testable
variant. A given message type, an image-uploaded event, a report-generated
event, always carries its payload as a claim check, never inline, regardless
of the actual size of any individual instance. This trades a small,
constant overhead on every message, even small ones, for the simplicity of
never branching on size at the Receiver. Teams that expect payload size to
grow over time, or that want one code path to test, favor this variant.

**Conditional, threshold-based claim check.** The variant Microsoft's own
Azure guidance recommends by name, applying the pattern only once a message
surpasses the messaging system's limit and sending small messages inline
otherwise
([Microsoft Learn, Claim-Check pattern, "Issues and considerations with the
Claim-Check pattern"](https://learn.microsoft.com/en-us/azure/architecture/patterns/claim-check),
verified 2026-08-02). This variant requires the Receiver, or a shared
message envelope contract, to disambiguate the two shapes unambiguously,
typically via an explicit discriminator field rather than inferring it from
whether a claim-check field happens to be populated, because an empty or
null field is a weaker contract than an explicit tag.

**Library-transparent claim check.** The transport client library itself
implements the size check, the store write, and the reference substitution,
so application code sends and receives what looks like an ordinary message
of any size and never handles a claim check directly. The AWS SQS Extended
Client Library for Java is the clearest named example of this variant. AWS
states that with the library, a caller can specify whether messages are
always stored in Amazon S3 or only when a message exceeds 256 KB, send a
message that references a single object stored in an S3 bucket, retrieve
that object, and delete it, all through the ordinary SQS client interface
([AWS documentation, Managing large Amazon SQS messages using Java and
Amazon S3](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/s3-messages.html),
verified 2026-08-02). The library wraps the standard `SqsClient` with an
`AmazonSQSExtendedClient` decorator, and callers keep calling `sendMessage`
and `receiveMessage` exactly as before. The library owns the threshold
decision, `withPayloadSupportEnabled`, configurable to always-store or
threshold-store, the S3 key generation, and, on receipt, the transparent
substitution of the stored payload back into the message body the caller
sees. This variant is the closest thing to zero application-code awareness
of the pattern, at the cost of vendor lock-in to that specific client
library and store pairing, and of a caveat AWS states directly, that the
Extended Client Library can manage large SQS messages with S3 "*only* with
the AWS SDK for Java," and cannot be used from the AWS CLI, the SQS console,
the SQS HTTP API, or any other AWS SDK
([AWS documentation, Managing large Amazon SQS messages using Java and
Amazon S3](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/s3-messages.html),
verified 2026-08-02). A team that stands up any tooling outside that one
SDK, a monitoring dashboard reading the queue directly, a different-language
consumer, has to reimplement the substitution logic by hand or those tools
will see the raw reference and nothing else.

**Framework middleware or data-bus claim check.** A messaging framework
provides claim check as a cross-cutting feature applied declaratively to
selected message fields, rather than to the whole message. Particular
Software's NServiceBus DataBus feature is the named example. Rather than
serializing data within the message itself, DataBus stores the payload in a
separate location that both sender and receiver can reach, and puts a
reference to that location in the message
([Particular Software documentation, NServiceBus DataBus](https://docs.particular.net/nservicebus/databus/),
verified 2026-08-02). DataBus is applied per property on a message class,
so a message can carry ordinary small fields inline and a single large
binary field, wrapped in a `DataBusProperty<T>`, via claim check, in the
same message instance. It ships multiple storage backends behind a common
interface, a File Share Data Bus using Windows file shares, an Azure Blob
Storage Data Bus using Azure's cloud storage, and custom backends through an
`IDataBusSerializer` interface for organizations that build their own
storage integration
([Particular Software documentation, NServiceBus DataBus](https://docs.particular.net/nservicebus/databus/),
verified 2026-08-02). This variant is the most fine-grained of the four,
because the threshold decision moves from applying to a whole message down
to applying to one field of one message, at the cost of a heavier framework
dependency and a serialization contract the whole team has to learn.

**Content Enricher retrieval, decoupled from Check-In.** In every variant
above, retrieval is described as happening synchronously inside the
Receiver. A distinct implementation choice, orthogonal to the four above, is
whether retrieval happens eagerly on receipt, the Receiver always resolves
the claim check before doing anything else, or lazily on first access, the
claim check is resolved only if and when downstream code actually reads the
payload field. Lazy resolution preserves more of the original benefit,
consumers that never touch the payload never pay the store round trip at
all, but it pushes a hidden network call, and a hidden new failure mode,
into what looks like an ordinary field access, which is a real cost to code
readability and to a caller's ability to reason about latency at a glance.

## 9. Known production uses

**Amazon SQS Extended Client Library for Java.** AWS's own SDK-adjacent
library, distributed as `amazon-sqs-java-extended-client-lib`, implements
Claim Check specifically to work around SQS's 256 KB message limit, using
Amazon S3 as the external store, and documents payload sizes ranging "from
256 KB to 2 GB"
([AWS documentation, Managing large Amazon SQS messages using Java and
Amazon S3](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/s3-messages.html),
verified 2026-08-02). The library is open source on GitHub under `awslabs`,
and AWS's own published example configures an S3 bucket lifecycle rule to
expire stored payload objects after 14 days, which is the vendor's own
concrete answer to the store-lifecycle force named in dimension 3.

**Azure Architecture Center's reference implementations.** Microsoft ships
four separate, runnable code samples implementing Claim Check across
different Azure messaging products, Azure Queue Storage, Azure Event Hubs
Standard API, Azure Service Bus, and Azure Event Hubs Kafka API, each
paired with Azure Blob Storage as the external store, hosted on GitHub under
`Azure-Samples/cloud-design-patterns`
([Microsoft Learn, Claim-Check pattern, "Claim-check pattern
examples"](https://learn.microsoft.com/en-us/azure/architecture/patterns/claim-check),
verified 2026-08-02). Two of the four samples use Azure Event Grid to
generate the claim-check token automatically the moment the sending
application transfers the payload to Blob Storage, which is the vendor's own
event-driven variant of the always-claim-check pattern from dimension 8.

**Particular Software's NServiceBus DataBus.** A first-party feature of the
NServiceBus messaging framework for .NET, shipped and maintained by
Particular Software, implementing per-property claim check across multiple
storage backends including Windows file shares and Azure Blob Storage
([Particular Software documentation, NServiceBus DataBus](https://docs.particular.net/nservicebus/databus/),
verified 2026-08-02). Particular Software is a commercial vendor building
exclusively on top of NServiceBus for production customers, so DataBus is
not a proof of concept but a maintained, versioned, customer-facing feature
with its own extensibility contract, `IDataBusSerializer`, for teams that
need a storage backend beyond the two shipped ones.

Each of these three is independently verifiable through its own vendor
documentation and, for the first two, through public source code, which
satisfies the requirement that a named production use trace to a real,
checkable system rather than to an unattributed claim that the pattern is
widely used.

## 10. Consequences

**Positive.** The message channel carries only what routing, filtering, and
audit logic need, so throughput and per-message cost on the broker are
decoupled from payload size. Consumers that never need the payload never pay
its network or deserialization cost. A consuming component with narrower
access rights than the payload's sensitivity requires can be denied access
to the store entirely while still participating in the messaging flow via
the metadata-only message. Payload storage and message durability can be
tuned independently, an important property when compliance retention
requirements for the data, years, differ sharply from the operational
retention needed for the message itself, hours or days.

**Negative.** Every consumer that does need the payload now performs two
network operations instead of one, and the system now depends on two
independently available services, the broker and the store, rather than
one. The write to the store and the send of the message are not atomic
against each other by default, which reintroduces a distributed-consistency
problem the pattern does not solve on its own, only relocates. Operational
visibility gets harder in one direction, an operator inspecting a queue for
troubleshooting sees an opaque reference rather than the data itself, which
is the security benefit from dimension 3 read from the opposite side as an
observability cost. The team now owns a second lifecycle policy, when to
delete a stored payload, that has real cost attached if left unmade, as
Microsoft's own considerations section states directly, per dimension 3.
Finally, the pattern adds genuine implementation surface, a store client, an
access-control model, a key-naming and collision-avoidance scheme, that a
team applying it to a payload well under the transport's limit pays for no
corresponding benefit.

## 11. Failure modes and misuse

**Symptom.** A consumer receives a message, resolves the claim check, and
the retrieval fails with a not-found error, intermittently and only for
recently sent messages.
**Cause.** The store write and the message send are two separate operations
against systems with different consistency models. If the store is
eventually consistent for new-object visibility, or if the send races ahead
of the store write completing, a common bug when the store write is fired
asynchronously and not awaited before the send, the message can arrive and
even be processed before the payload is durably visible at the store.
**Fix.** Make the store write complete, and its success confirmed, strictly
before the message send is issued, in the same logical unit of work at the
Sender. Where the store's own consistency model allows eventual visibility
for newly written objects, rare for the major object stores on first-write,
but real for some replicated file systems, add a bounded retry with backoff
at the Check-Out step rather than treating the first not-found as fatal.

**Symptom.** Storage costs for the external store grow unbounded over
months, tracking roughly with total message volume rather than with active
data volume, and nobody can explain what most of the stored objects are
for.
**Cause.** No deletion policy was implemented for consumed payloads, which
Microsoft's own guidance flags directly as a required design decision, not
an optional cleanup task, per dimension 3. Every payload written at
Check-In survives forever by default in most object stores, because object
stores do not know a payload was consumed the way a queue knows a message
was acknowledged.
**Fix.** Implement either synchronous deletion, the consumer deletes the
payload immediately after it finishes processing, tying deletion cost to
the message-handling workflow, or asynchronous deletion, a separate
scheduled process or the store's own lifecycle rule, the exact mechanism
AWS's own example configures, a 14-day expiration lifecycle rule on the S3
bucket, that removes objects past a retention window independent of the
message flow. Pick one deliberately rather than defaulting to neither.

**Symptom.** A load test or a security review discovers that anyone who can
guess or enumerate claim-check keys can retrieve payloads they were never
sent a message about.
**Cause.** The claim check was implemented as a predictable identifier, an
auto-incrementing integer, a timestamp-derived key, or a hash of low-entropy
input, and the store's access control was left open or scoped too broadly,
a bucket-wide read policy rather than object-level, time-limited grants.
**Fix.** Generate claim-check keys with cryptographically strong
randomness, a UUID v4 or equivalent is a floor, not a ceiling, for this
purpose, and prefer time-limited, single-purpose signed URLs, an S3 or Blob
Storage pre-signed URL with a short expiry, over a durable, broadly-scoped
credential whenever the store and client library support it. Treat the
claim check as a bearer credential, because functionally it is one, and
review dimension 17 before shipping the design.

**Symptom.** Adding a new consumer to an existing message channel requires
copying storage credentials, storage client library code, and retry logic
into the new consumer before it can do anything useful, even when that
consumer only needs to route on metadata.
**Cause.** The message envelope was not designed with enough useful
metadata inline to let metadata-only consumers do their job without ever
touching the claim check, so every consumer was written assuming it would
eventually need the payload.
**Fix.** Design the thin message to carry every field a routing, filtering,
or audit consumer plausibly needs, content type, size, a correlation
identifier, a coarse category, inline, and reserve the claim check purely
for the bytes those consumers genuinely never need. This is the same design
discipline the Content Enricher pattern names from the opposite direction,
put only the minimum in the message and enrich on demand, applied here to
avoid over-thinning the message rather than over-fattening it.

**Symptom.** Two different consumers of the same claim check retrieve two
different payloads over time, causing intermittent, hard-to-reproduce data
mismatches between systems that were supposed to be looking at the same
document.
**Cause.** The Data Store key was reused for a mutable object, and the
payload behind the key was overwritten after the claim check was already
distributed to some consumers but not yet read by others.
**Fix.** Treat every claim check as pointing to an immutable object.
Generate a new key for every write, never overwrite an existing key in
place, and rely on the store's own versioning or lifecycle features, rather
than in-place mutation, for any update to the underlying data.

## 12. Trade-off matrix

The comparison below is against the two named alternatives a team
realistically considers instead of Claim Check when a message is too large
for its transport, sending the payload inline anyway on a broker tier that
permits it, Azure Service Bus Premium's 100 MB AMQP tier is the concrete
example, per dimension 2, and chunking the payload into an ordered sequence
of smaller messages reassembled by the consumer.

| Force | Claim Check | Inline on a higher-limit tier | Chunked message sequence |
|---|---|---|---|
| Broker cost at scale | Broker stores only small reference messages, independent of payload size | Broker stores and replicates the full payload for every message, at the vendor's per-tier price | Broker stores the full payload split across N messages, same total bytes as inline, plus per-message overhead |
| Consumers that ignore the payload | Pay nothing beyond the thin message | Still pay full deserialization and network cost even if they never read the payload field | Still pay cost for every chunk even if the payload is discarded |
| Consistency risk introduced | Genuine, two systems to keep in sync, per dimension 11 | None beyond the broker's own delivery guarantee | Genuine, must guarantee all chunks of a sequence arrive and reassemble correctly before the consumer can safely process anything |
| Extra operational dependency | Yes, a second store the team now owns | No, only the broker | No, only the broker, but reassembly logic is new application code |
| Vendor lock-in or tier cost | Depends on store choice, portable across brokers | Tied to the specific vendor tier that permits the size, can be costly | None, portable, but reassembly code must be maintained per language and per consumer |
| Payload access control independent of message access | Yes, store and broker permissions can differ | No, anything with message access has payload access | No, anything with message access has payload access |
| Implementation complexity | Moderate, new store client and key scheme | Lowest, no new code beyond raising a config limit | Highest, custom sequencing, buffering, and reassembly logic per consumer |

## 13. Related and incompatible patterns

**Content Enricher.** The step where a Receiver resolves a claim check back
into the full payload is a specific instance of Content Enricher, adding
missing information to a message
([enterpriseintegrationpatterns.com, Claim Check](https://www.enterpriseintegrationpatterns.com/patterns/messaging/StoreInLibrary.html),
verified 2026-08-02, listing Content Enricher among the page's own related
patterns). Reading dimension 6's Check-Out box literally as a Content
Enricher instance clarifies its contract, it is not free-form retrieval, it
is a well-defined enrichment step that turns a thin message into a complete
one for exactly the consumer that asked for it.

**Content Filter.** The inverse relationship to the same named page's other
sibling pattern. Content Filter removes unneeded data from a message before
passing it on, and Claim Check removes the payload before passing the
message on and preserves the ability to bring it back. A team that only
ever needs the removal, never the retrieval, for a given field should reach
for Content Filter, not Claim Check, because standing up a store and a
retrieval path for data nobody will ever fetch again is pure waste.

**Message Expiration.** Because a stored payload's lifecycle must be
managed deliberately, dimension 11's second failure mode, Message
Expiration on the broker side and an equivalent time-to-live or lifecycle
policy on the store side are companion mechanisms, not competitors, and a
mature implementation sets both, keeping the two windows aligned so a
message never outlives the payload it references, or the reverse, an
orphaned payload nobody can reach.

**Guaranteed Delivery.** Claim Check does not weaken a broker's delivery
guarantee for the thin message. It does introduce a second delivery-like
guarantee the team must reason about separately, that the payload write is
durable before the message referencing it is considered sent, discussed in
dimension 11's first failure mode. Guaranteed Delivery on the channel and a
durability guarantee on the store composed together, not either alone, are
what the pattern actually needs to be sound end to end.

**Saga.** When the store write and the message send genuinely need to be
kept consistent across a failure, and a simple write-then-send order with
the send only issued on confirmed write success is not sufficient because of
a partial failure after the write but before any consumer sees the
reference, a Saga-style compensating action, delete the orphaned payload on
a timeout, or mark it unreachable, is the pattern to reach for rather than
inventing bespoke reconciliation logic.

**Incompatible with.** No pattern is structurally incompatible with Claim
Check. The closest to a genuine conflict is applying Claim Check to a
payload the consumer needs synchronously on every single message with no
tolerance for the extra round trip, which is not so much an incompatible
pattern as the applicability boundary already described in dimension 4.

## 14. Refactoring path in and out

Introducing Claim Check into an existing system that currently sends
payloads inline follows this sequence.

1. Measure real message sizes in production over a representative window,
   rather than guessing. Identify the actual distribution, not just the
   worst case, because the threshold decision in step 3 depends on it.
2. Stand up, or select, the external store, and settle its access-control
   model and its lifecycle, retention and deletion, policy before writing
   any application code against it. Doing this last, after the pattern is
   already live, is how the second failure mode in dimension 11 happens.
3. Add an explicit size-or-sensitivity discriminator field to the message
   envelope, defaulting to inline for the current behavior, so the change is
   additive and can ship without breaking existing consumers on day one.
4. Implement Check-In behind a feature flag or a per-message-type opt-in,
   so the store write path can be exercised against real traffic at low
   volume before being trusted for the full flow.
5. Update, or confirm, that every consumer of the affected channel already
   tolerates the new discriminator field, and add Check-Out logic only to
   the consumers that genuinely need the payload, leaving metadata-only
   consumers untouched.
6. Cut the threshold, or the per-message-type opt-in, over fully once
   Check-In and Check-Out have both been exercised against production-shaped
   data, and only then remove the inline code path for the affected message
   types, rather than keeping both paths live indefinitely as unreviewed
   dead weight.

Removing Claim Check once it no longer earns its place, typically because
the broker's own limits were later raised, or because payload sizes shrank
after an upstream format change made the pattern's overhead no longer worth
paying, follows a mirrored sequence.

1. Confirm the new, higher inline limit genuinely covers the current and
   reasonably projected payload sizes for the affected message type, not
   only today's median.
2. Reverse step 3 above. Flip the message envelope's discriminator back to
   inline for new messages, while Check-Out logic remains live for any
   already-sent messages still in flight or still referenced by messages not
   yet fully processed.
3. Once the store's retention window, dimension 11, confirms no
   still-referenced claim checks remain outstanding, remove Check-Out logic
   from consumers, and only then decommission or repurpose the store
   dependency for that message type.
4. Do not delete the store or its data ahead of that retention confirmation.
   A payload deleted while a claim check referencing it is still in flight
   recreates the not-found failure mode from dimension 11 in the opposite
   direction.

## 15. Testing and verification

Claim Check makes one class of test easier and one class harder, and both
deserve explicit test coverage rather than being left to integration tests
alone.

Easier. Routing, filtering, and audit logic that only reads message
metadata can now be tested entirely against thin messages, with no store
dependency at all, because that is exactly the contract the pattern
establishes, metadata-only consumers never need the payload. Unit tests for
these consumers should assert this contract directly, construct a message
with a claim check pointing at a store the test double will reject any call
to, and confirm the consumer under test never calls it.

Harder. Check-In and Check-Out both introduce a genuine external dependency
that a naive test either skips, leaving the store interaction untested, or
calls for real, making the test slow, flaky, and dependent on network and
credentials. The correct middle ground is a store abstraction behind an
interface narrow enough to fake convincingly, put, get, and delete by key,
tested with a real in-memory or local-filesystem-backed implementation in
unit tests, and against the real store only in a smaller set of integration
tests that specifically exercise the store's own failure modes, not-found,
access-denied, throttling, that a fake cannot faithfully reproduce.

Three test doubles carry real weight here and deserve to be named
explicitly rather than left implicit.

A fake store, an in-memory map behind the same put, get, or delete
interface the real store exposes, should back the majority of Check-In and
Check-Out unit tests, and should be capable of returning not-found on
demand, so tests can exercise the first failure mode from dimension 11
deterministically rather than relying on a race against a real store.

A spy or mock message channel should be used to assert the exact shape of
the thin message Check-In produces, specifically that the discriminator
field is set correctly and that the payload itself never appears in the
outgoing message when the threshold policy says it should not, which is the
single most valuable assertion in the whole test suite because a leaked
payload defeats the pattern's entire purpose silently.

A contract test run against the real store, kept separate from the fast
unit suite and run less frequently, on a schedule or before a release
rather than on every commit, should assert that the fake store's behavior
for not-found, for a successful round trip, and for deletion genuinely
matches the real store's behavior, because a fake that drifts from the real
store's contract is worse than no fake at all, it gives false confidence.

## 16. Observability signals

A healthy Claim Check implementation should expose, at minimum, the
following measurements, and a dashboard or alert should treat their
absence, not only their presence at an alarming value, as something worth
investigating.

- Store write latency and error rate at Check-In, tagged by message type,
  so a slow or failing store does not manifest only as a mysterious
  increase in end-to-end message latency several hops downstream where it
  is much harder to trace back to its source.
- The ratio of messages sent via claim check versus inline, for systems
  using the conditional variant from dimension 8. A sudden shift in this
  ratio often indicates an upstream change in payload shape, a new field
  added to what used to be a small message, an image resolution bump, that
  the team should notice and evaluate deliberately, rather than only
  discovering weeks later when store costs rise.
- Store retrieval latency and not-found rate at Check-Out, again tagged by
  message type. A nonzero, sustained not-found rate is the direct symptom
  of the first failure mode in dimension 11, and should page or alert on a
  threshold well below every retrieval failing, because a system that only
  alerts once retrieval is completely broken has already lost substantial
  data for however long the partial failure was silent.
- Storage growth over time, and the fraction of stored objects past their
  intended retention window still present. This is the direct measurement
  for the second failure mode in dimension 11, unbounded storage growth,
  and it should be graphed against message volume so a team can
  distinguish organic growth from a genuine leak in the deletion policy.
- Access-denied and unusual-access-pattern events at the store, which are
  the earliest warning of the security failure mode in dimension 11, a
  predictable or over-broadly-scoped claim check being probed or
  enumerated, and should be reviewed with the same seriousness as
  authentication failure logs anywhere else in the system, not treated as
  routine noise from the store's own access layer.

A healthy instance of the pattern in production shows a store write latency
that tracks payload size predictably, a stable ratio of claim-check to
inline messages that only moves when the team deliberately changes the
threshold or the upstream data shape, a near-zero not-found rate at
retrieval, and storage growth that flattens once the retention policy
reaches steady state rather than growing linearly with cumulative message
volume forever.

## 17. Security and privacy implications

The pattern's security profile cuts in two directions at once, and treating
only one of them is a common and dangerous half-measure.

The benefit. Removing sensitive payload data from the message body means
the broker itself, and every piece of tooling with visibility into broker
traffic, a monitoring agent, a queue-browsing admin console, a log shipper
that captures message bodies for debugging, never sees the sensitive
content, only an opaque reference. Microsoft names this as a first-class
use case rather than a side effect, writing that the pattern is called for
whenever payloads carry sensitive data the team does not want visible to
the messaging system
([Microsoft Learn, Claim-Check pattern, "When to use the Claim-Check
pattern"](https://learn.microsoft.com/en-us/azure/architecture/patterns/claim-check),
verified 2026-08-02). For a system with a data classification policy, this
lets the message channel, and everything that operates it, sit at a lower
classification tier than the payload store, which can be a real reduction
in audit scope and in the blast radius of a broker-level compromise.

The cost. The claim check itself is now the single credential that
determines who can retrieve the sensitive payload, so its design carries
all the weight a bearer token normally carries. A predictable, guessable, or
overly long-lived claim check turns the pattern into a confused-deputy
vulnerability, anyone who obtains the small, ostensibly harmless message
also obtains everything needed to fetch the sensitive payload, and the
broker's own access controls, which the team may have relied on to gate
access to the message, no longer gate access to the data the message
actually pointed at, because the store's access model, not the broker's, is
what actually decides who can retrieve the payload.

Concrete practices that follow directly from that framing, each tied to a
specific mechanism named earlier in this entry rather than stated as
generic advice.

- Generate claim-check keys with strong, unguessable randomness, never from
  a sequence, a timestamp, or a hash of predictable input, because a
  store's access control is only as strong as the difficulty of guessing a
  valid key in front of it.
- Prefer time-limited, single-object, single-permission credentials over
  durable, broadly-scoped ones wherever the store supports them, a
  pre-signed URL with a short expiry on Amazon S3 or Azure Blob Storage
  rather than a long-lived API key with bucket-wide read access, so a
  leaked message containing a claim check has a bounded window of
  usefulness to an attacker rather than an indefinite one.
- Encrypt the payload at rest in the store independent of, and in addition
  to, any encryption the broker itself provides for the message channel,
  because the pattern deliberately moves the sensitive bytes to a system
  whose encryption-at-rest posture may not have been reviewed under the
  same scrutiny as the broker's, precisely because it is newly introduced
  by adopting this pattern.
- Apply the same retention and deletion discipline named in dimension 11 as
  a privacy control, not only a cost control. A payload stored past the
  point it is legitimately needed is a growing store of sensitive data with
  no corresponding business justification, and that fact matters
  independently of what it costs to keep it, particularly for payloads
  subject to a regulatory retention limit shorter than indefinite.
- Audit and alert on access to the store itself, not only on delivery of
  messages through the broker, because an attacker who compromises the
  store's credentials directly, bypassing the broker entirely, is invisible
  to any monitoring that only watches the message channel.

## 18. References

- Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns. Designing,
  Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003, Message
  Construction chapter, Claim Check.
- [Enterprise Integration Patterns companion site, Claim Check](https://www.enterpriseintegrationpatterns.com/patterns/messaging/StoreInLibrary.html), verified 2026-08-02.
- [Microsoft Learn, Claim-Check pattern, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/claim-check), verified 2026-08-02.
- [AWS documentation, Managing large Amazon SQS messages using Java and Amazon S3](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/s3-messages.html), verified 2026-08-02.
- [Particular Software documentation, NServiceBus DataBus](https://docs.particular.net/nservicebus/databus/), verified 2026-08-02.
- [Google Cloud documentation, Pub/Sub quotas and limits](https://docs.cloud.google.com/pubsub/quotas), verified 2026-08-02.
- [Microsoft Learn, Azure Service Bus quotas and limits](https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-quotas), verified 2026-08-02.
- [AWS Labs, amazon-sqs-java-extended-client-lib, GitHub](https://github.com/awslabs/amazon-sqs-java-extended-client-lib), verified 2026-08-02.
- [Azure Samples, cloud-design-patterns, claim-check code samples, GitHub](https://github.com/Azure-Samples/cloud-design-patterns/tree/main/claim-check), verified 2026-08-02.

## Code examples

The three samples below implement the always-claim-check variant from
dimension 8, a Check-In step that writes a payload to a store and returns a
thin reference, and a Check-Out step that resolves the reference back to
the payload. Each defines the store behind a narrow interface, matching the
testing guidance in dimension 15, so a real object-store client can be
substituted for the in-memory implementation shown here without changing
the Check-In or Check-Out logic. All three were run, not only written,
against the toolchains recorded below.

TypeScript, compiled with `tsc --strict --target es2022`.

```typescript
interface ClaimCheckStore {
  put(bytes: Uint8Array): Promise<string>;
  get(key: string): Promise<Uint8Array>;
  remove(key: string): Promise<void>;
}

interface ThinMessage {
  claimCheck: string;
  contentType: string;
  byteLength: number;
}

class InMemoryStore implements ClaimCheckStore {
  private readonly objects = new Map<string, Uint8Array>();
  private counter = 0;

  async put(bytes: Uint8Array): Promise<string> {
    const key = `payload-${++this.counter}`;
    this.objects.set(key, bytes);
    return key;
  }

  async get(key: string): Promise<Uint8Array> {
    const bytes = this.objects.get(key);
    if (!bytes) {
      throw new Error(`claim check not found ${key}`);
    }
    return bytes;
  }

  async remove(key: string): Promise<void> {
    this.objects.delete(key);
  }
}

async function checkIn(
  store: ClaimCheckStore,
  contentType: string,
  payload: Uint8Array
): Promise<ThinMessage> {
  const key = await store.put(payload);
  return { claimCheck: key, contentType, byteLength: payload.byteLength };
}

async function checkOut(
  store: ClaimCheckStore,
  message: ThinMessage,
  deleteAfter: boolean
): Promise<Uint8Array> {
  const payload = await store.get(message.claimCheck);
  if (deleteAfter) {
    await store.remove(message.claimCheck);
  }
  return payload;
}

async function demo(): Promise<void> {
  const store = new InMemoryStore();
  const largeReport = new TextEncoder().encode("x".repeat(300_000));

  const thin = await checkIn(store, "application/octet-stream", largeReport);
  console.log(`sent thin message, byteLength=${thin.byteLength}, claimCheck=${thin.claimCheck}`);

  const resolved = await checkOut(store, thin, true);
  console.log(`resolved payload length ${resolved.byteLength}`);
}

void demo();
```

Python, checked with `python3 -m py_compile`.

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
import itertools


class ClaimCheckStore(Protocol):
    def put(self, payload: bytes) -> str: ...
    def get(self, key: str) -> bytes: ...
    def remove(self, key: str) -> None: ...


class InMemoryStore:
    def __init__(self) -> None:
        self._objects: dict[str, bytes] = {}
        self._ids = itertools.count(1)

    def put(self, payload: bytes) -> str:
        key = f"payload-{next(self._ids)}"
        self._objects[key] = payload
        return key

    def get(self, key: str) -> bytes:
        if key not in self._objects:
            raise KeyError(f"claim check not found {key}")
        return self._objects[key]

    def remove(self, key: str) -> None:
        self._objects.pop(key, None)


@dataclass(frozen=True)
class ThinMessage:
    claim_check: str
    content_type: str
    byte_length: int


def check_in(store: ClaimCheckStore, content_type: str, payload: bytes) -> ThinMessage:
    key = store.put(payload)
    return ThinMessage(claim_check=key, content_type=content_type, byte_length=len(payload))


def check_out(store: ClaimCheckStore, message: ThinMessage, delete_after: bool) -> bytes:
    payload = store.get(message.claim_check)
    if delete_after:
        store.remove(message.claim_check)
    return payload


def demo() -> None:
    store = InMemoryStore()
    large_report = b"x" * 300_000

    thin = check_in(store, "application/octet-stream", large_report)
    print(f"sent thin message, byte_length={thin.byte_length}, claim_check={thin.claim_check}")

    resolved = check_out(store, thin, delete_after=True)
    print(f"resolved payload length {len(resolved)}")


if __name__ == "__main__":
    demo()
```

Go, checked with `go vet`.

```go
package main

import (
	"fmt"
	"strings"
	"sync"
)

type ClaimCheckStore interface {
	Put(payload []byte) (string, error)
	Get(key string) ([]byte, error)
	Remove(key string) error
}

type InMemoryStore struct {
	mu      sync.Mutex
	objects map[string][]byte
	counter int
}

func NewInMemoryStore() *InMemoryStore {
	return &InMemoryStore{objects: make(map[string][]byte)}
}

func (s *InMemoryStore) Put(payload []byte) (string, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.counter++
	key := fmt.Sprintf("payload-%d", s.counter)
	s.objects[key] = payload
	return key, nil
}

func (s *InMemoryStore) Get(key string) ([]byte, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	payload, ok := s.objects[key]
	if !ok {
		return nil, fmt.Errorf("claim check not found %s", key)
	}
	return payload, nil
}

func (s *InMemoryStore) Remove(key string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.objects, key)
	return nil
}

type ThinMessage struct {
	ClaimCheck  string
	ContentType string
	ByteLength  int
}

func CheckIn(store ClaimCheckStore, contentType string, payload []byte) (ThinMessage, error) {
	key, err := store.Put(payload)
	if err != nil {
		return ThinMessage{}, err
	}
	return ThinMessage{ClaimCheck: key, ContentType: contentType, ByteLength: len(payload)}, nil
}

func CheckOut(store ClaimCheckStore, message ThinMessage, deleteAfter bool) ([]byte, error) {
	payload, err := store.Get(message.ClaimCheck)
	if err != nil {
		return nil, err
	}
	if deleteAfter {
		if err := store.Remove(message.ClaimCheck); err != nil {
			return nil, err
		}
	}
	return payload, nil
}

func main() {
	store := NewInMemoryStore()
	largeReport := []byte(strings.Repeat("x", 300000))

	thin, err := CheckIn(store, "application/octet-stream", largeReport)
	if err != nil {
		panic(err)
	}
	fmt.Printf("sent thin message, byteLength=%d, claimCheck=%s\n", thin.ByteLength, thin.ClaimCheck)

	resolved, err := CheckOut(store, thin, true)
	if err != nil {
		panic(err)
	}
	fmt.Printf("resolved payload length %d\n", len(resolved))
}
```
