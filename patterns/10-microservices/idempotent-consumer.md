---
name: Idempotent Consumer
slug: idempotent-consumer
family: 10-microservices
category: Reliability
aliases: [Idempotent Receiver, Deduplicating Consumer, Exactly-Once Consumer]
first_described: "Richardson, microservices.io pattern catalog, and Microservices Patterns, Manning 2018"
maturity: canonical
related: [transactional-outbox, transaction-log-tailing, domain-event, saga, database-per-service]
incompatible_with: []
verified: 2026-08-02
---

# Idempotent Consumer

## 1. Name, aliases, and lineage

The canonical name in this catalog is Idempotent Consumer. Chris Richardson
catalogs it under this exact name at
[microservices.io/patterns/communication-style/idempotent-consumer.html](https://microservices.io/patterns/communication-style/idempotent-consumer.html)
(verified 2026-08-02), and again in his book *Microservices Patterns*, Manning,
2018, chapter 3, in the discussion of message broker delivery guarantees. The
page states the solution plainly, in effect telling the reader to make a
consumer idempotent by having it record the IDs of processed messages in the
database, so a message that arrives twice is discarded on the second arrival
rather than applied twice.

**Idempotent Receiver** is the same idea under a different label, used in
enterprise-integration writing that predates the microservices vocabulary.
Gregor Hohpe and Bobby Woolf's *Enterprise Integration Patterns*, Addison-Wesley,
2003, does not carry a pattern of this exact name in its own catalog, but the
book's Message and Message Endpoint chapters establish the delivery-guarantee
vocabulary, at-least-once and guaranteed delivery among them, that the
Idempotent Consumer pattern answers. Framework and vendor documentation from
the 2010s onward picked up Idempotent Receiver as a synonym once message-driven
architectures moved from ESBs to brokers like Kafka and SQS, and both names are
used interchangeably in production engineering writing today.

**Deduplicating Consumer** and **Exactly-Once Consumer** describe the same
mechanism from the outcome side rather than the mechanism side. A team that
says it deduplicates at the consumer and a team that says its consumer is
idempotent are describing the identical code shape, a check against a record
of what has already been processed, performed before the side effect runs.

The pattern is not new engineering. Databases have offered upsert-style
inserts and unique constraints for this exact purpose since long before
message brokers existed, and TCP itself deduplicates at the transport layer
using sequence numbers. What Richardson's catalog entry does is name the
application-level version of the same idea explicitly, for the specific case
where the durability guarantee a message broker gives, that a message will
arrive, possibly more than once, does not match the guarantee the business
operation needs, which is that a payment must be captured exactly once.

## 2. Problem and context

A service consumes messages or events from a broker, whether that is Kafka,
Amazon SQS, RabbitMQ, Azure Service Bus, Google Pub/Sub, or an HTTP webhook
delivered by another service. Every one of these transports, when configured
for reliable delivery, gives an at-least-once guarantee, never an
exactly-once one at the wire level. A consumer can crash after processing a
message but before acknowledging it. A network partition can cause a broker
to resend a message it never received an acknowledgment for. A producer
retrying a failed publish, or a webhook sender retrying a failed HTTP call,
can hand the same logical event to the consumer twice under two different
delivery attempts. None of these are bugs in the transport. They are the
transport doing exactly what an at-least-once contract promises, never
silently dropping a message, even at the cost of occasionally delivering it
more than once.

The problem surfaces the moment the consumer's handler is not naturally
idempotent. Debiting a bank account by a fixed amount, sending an email,
incrementing a counter, appending a row to an audit log, calling a
third-party payment API, decrementing inventory, none of these operations
produce the same end state when run twice with the same input. Run the debit
handler twice for one logical payment message and the customer is charged
twice. Run the inventory decrement twice and stock goes negative for a sale
that happened once. The business operation is not naturally idempotent even
though the underlying data store might be.

The context that makes this pattern necessary, rather than merely convenient,
has three parts. First, the transport is at-least-once by contract, not by
accident, so the consumer cannot rely on the assumption that the broker will
only send a message once, even under normal, non-failure operation, because
acknowledgment loss on the network back to the broker is itself a normal
failure mode, not an edge case. Second, the operation the message triggers
has a side effect outside the message system itself, a write to a different
database, a call to another service, a charge on a card. Third, the service
cannot simply ignore the problem by relying on a downstream idempotency
mechanism, because the downstream system, an email provider, a legacy
mainframe, a partner API, may not offer one, or the service may not control
it.

## 3. Forces

This is engineering judgement about which pressures matter most, not a
sourced claim.

**Correctness against write amplification.** The whole reason the pattern
exists is that at-least-once delivery, left unhandled, turns into
at-least-once side effects. The pattern trades a small amount of extra state
and a lookup on every message for the guarantee that the business effect
happens exactly once. Skipping this trade produces the double-charge and
negative-stock failures described above.

**Storage cost against retention length.** Recording every processed message
ID costs storage that grows without bound unless it is pruned. The pattern
forces a decision about how long a message ID must be remembered, forever, for
a fixed retention window, or scoped to a natural business boundary like an
order or an invoice. A retention window that is too short reopens the
duplicate-processing hole for messages replayed after the window closes, which
happens routinely when an operator manually replays a dead-letter queue days
after the original failure.

**Latency against the extra round trip.** Checking whether a message ID has
already been processed is at minimum one extra read against a store, and
recording it after success is at minimum one extra write. For a
high-throughput consumer this is a real cost per message, not a rounding
error, and it competes directly with the throughput the message system was
chosen to provide.

**Atomicity against the two-write problem.** The check-then-act shape, has
this ID been seen, if not, apply the effect and record the ID, is itself
vulnerable to a race unless the record-of-processing and the business effect
commit as one atomic unit. This is the same dual-write problem that motivates
the Transactional Outbox pattern on the producing side, mirrored on the
consuming side. Getting this wrong reintroduces the exact bug the pattern
exists to prevent, just with a smaller window.

**Coupling to message identity against message design freedom.** The pattern
depends on every message carrying a stable, unique identifier that survives
retries and redeliveries unchanged. This constrains upstream message design.
A producer that regenerates a random ID on every retry, rather than reusing
the original message's ID, silently defeats every idempotent consumer
downstream of it, no matter how well the consumer side is built.

## 4. Applicability and non-applicability

Reach for Idempotent Consumer when the following hold together.

- The transport delivers at-least-once, which includes essentially every
  production message broker configured for durability, Kafka with manual
  offset commit, SQS standard queues, RabbitMQ with manual ack, Azure Service
  Bus with peek-lock, and any webhook sender that retries on non-2xx or on
  timeout.
- The handler produces a side effect that is not naturally idempotent, a
  monetary transaction, a notification send, a stock mutation, a call to a
  system that does not itself deduplicate.
- The consumer does not fully control the producer, or cannot guarantee the
  producer never retries with a fresh message identity, so relying on the
  producer alone to prevent duplicates is not a safe assumption.
- Losing a message silently is worse than the operational cost of
  occasionally seeing, and discarding, a duplicate, which is the entire
  reason at-least-once transports exist in the first place.

Do not reach for it in these cases.

- **The handler is already naturally idempotent.** An operation that sets a
  status to a fixed value, or an HTTP PUT that replaces a resource wholesale,
  produces the same end state no matter how many times it runs. Adding a
  deduplication table on top of an operation that is already idempotent by
  construction adds storage and latency for no correctness gain. Prefer
  designing the operation to be naturally idempotent, an absolute assignment
  instead of a relative increment, a PUT instead of a POST, before reaching
  for this pattern.
- **The transport already gives an exactly-once guarantee end to end for this
  specific use case, and that guarantee is verified, not assumed.** Kafka's
  idempotent producer plus a consumer that commits offsets and its own state
  change in a single transaction, Kafka's read-process-write exactly-once
  semantics, using `enable.idempotence=true` on the producer and a
  transactional consumer, documented at
  [kafka.apache.org/documentation/#semantics](https://kafka.apache.org/documentation/#semantics)
  (verified 2026-08-02), can remove the need for an application-level dedup
  table when the entire read-process-write cycle stays inside Kafka. The
  moment the side effect leaves Kafka, for example a call to an external
  payment API, the guarantee no longer covers it and the application-level
  pattern is needed again for that external call specifically.
- **A single, short-lived process where a crash means the whole workflow
  restarts from scratch anyway.** A batch job that reprocesses its entire
  input on any failure, with no partial commits, does not need per-message
  idempotency because there is no partial-progress state to protect against
  double-application, it needs job-level idempotency instead, which is a
  different, usually simpler, mechanism.
- **The volume is low enough, and the effect cheap enough to correct by
  hand, that the operational cost of occasionally fixing a duplicate manually
  is lower than the engineering cost of building and maintaining a dedup
  store.** This is a legitimate, if narrow, judgement call for an early-stage
  system with a human in the loop reviewing every transaction anyway.

## 5. Structure

**Consumer.** The service process that receives a message from the transport
and is responsible for applying its side effect exactly once. Owns the
decision of whether to process, skip, or reject a given message.

**Message.** The unit of work delivered by the transport, carrying a message
identifier that is stable across redelivery attempts. The identifier is the
single most load-bearing field in the whole pattern, since everything
downstream depends on the producer never changing it on retry.

**Deduplication store, or Processed Message Log.** The record of which
message identifiers have already been applied. Richardson's catalog describes
this as either a dedicated table, commonly named something like
`PROCESSED_MESSAGES`, or fields embedded directly on the business entity the
message affects (microservices.io, idempotent-consumer, verified 2026-08-02).
The store must support an atomic check-and-record operation, most commonly a
unique constraint on the message ID column that the database enforces for
you.

**Business transaction.** The actual side effect the message triggers,
together with the write to the deduplication store. These two writes must
commit as a single atomic unit, or the pattern degrades back into a race
between applying the effect and recording that it was applied.

**Acknowledgment.** The signal back to the transport that the message was
handled and can be removed from the queue, or that the consumer's offset can
advance past it. Acknowledgment happens only after the business transaction
and the dedup record both commit, never before, or a crash between the two
reintroduces duplicate delivery on redelivery of an unacknowledged message.

## 6. ASCII structure diagram

```
+------------------+        +--------------------------+
|   Message         |        |       Consumer            |
|   Broker          |------->|                            |
|  (Kafka / SQS /   |  msg   |  1. extract message_id    |
|   RabbitMQ /      |        |  2. begin transaction     |
|   webhook sender) |        |  3. check dedup store     |
+------------------+        |  4. if seen, skip and ack |
        ^                    |     if new, apply effect   |
        |                    |          record message_id |
        |                    |     commit transaction     |
        | ack after commit   |  5. acknowledge message   |
        +--------------------|                            |
                              +--------------------------+
                                        |
                                        v
                              +--------------------------+
                              | Dedup store               |
                              | PROCESSED_MESSAGES         |
                              | ---------------------------|
                              | message_id  PK (unique)    |
                              | processed_at                |
                              | (or, dedup fields embedded  |
                              |  directly on the business   |
                              |  entity row itself)         |
                              +--------------------------+
                                        |
                                        v
                              +--------------------------+
                              | Business entity / effect   |
                              | (account balance, order,   |
                              |  inventory row, outbound    |
                              |  email send record)         |
                              +--------------------------+
```

## 7. Dynamics

```
First delivery of message M (id = "evt-4471")

  Broker -> Consumer      : deliver M
  Consumer -> DedupStore  : SELECT 1 FROM processed_messages
                             WHERE message_id = 'evt-4471'
  DedupStore -> Consumer  : no row found
  Consumer -> BusinessDB  : BEGIN TXN
  Consumer -> BusinessDB  :   apply effect (debit account, decrement stock)
  Consumer -> DedupStore  :   INSERT INTO processed_messages
                               VALUES ('evt-4471', now())
  Consumer -> BusinessDB  : COMMIT TXN
  Consumer -> Broker      : ack(M)

Redelivery of the SAME message M after a crash before ack, or a
producer retry that reuses the same message_id

  Broker -> Consumer      : deliver M (again)
  Consumer -> DedupStore  : SELECT 1 FROM processed_messages
                             WHERE message_id = 'evt-4471'
  DedupStore -> Consumer  : row found
  Consumer -> Broker      : ack(M)   -- no business effect applied a second time

Two consumer instances racing on the same message under
at-least-once fan-out (competing consumers, same message_id)

  Broker -> Consumer A    : deliver M
  Broker -> Consumer B    : deliver M (duplicate delivery, e.g. visibility
                             timeout expired before A's ack landed)
  Consumer A -> DedupStore: INSERT INTO processed_messages VALUES ('evt-4471', ..)
  Consumer B -> DedupStore: INSERT INTO processed_messages VALUES ('evt-4471', ..)
  DedupStore              : unique constraint on message_id rejects B's insert
  Consumer B               : catches constraint violation, treats as duplicate,
                              rolls back its own business-effect write, acks M
```

## 8. Implementation variants

**Dedicated dedup table with a unique constraint, Richardson's default.** A
`PROCESSED_MESSAGES` table with `message_id` as the primary key or a unique
index. The business write and the insert into this table happen in one
database transaction. This is the variant Richardson describes as the
primary solution at
microservices.io/patterns/communication-style/idempotent-consumer.html
(verified 2026-08-02), and it is the easiest to reason about because the
uniqueness guarantee is enforced by the database itself rather than by
application logic racing against itself.

**Dedup fields embedded on the business entity.** Instead of a separate
table, the business row itself carries a `last_processed_message_id` column,
and the update is written as a conditional update that only applies when the
stored message ID differs from the incoming one. This variant avoids a
second table and a second write, and it is Richardson's alternative
description of the same pattern (microservices.io, idempotent-consumer,
verified 2026-08-02). It only works when each entity is affected by a single
in-flight message stream at a time, and it does not generalize cleanly to an
entity that receives messages from several independent producers, because
one column cannot remember more than one producer's most recent message ID.

**External-request idempotency key, client-supplied, server-stored.** The
consumer is itself the origin of an outbound call to a third party, and the
third party exposes an idempotency-key mechanism. Stripe's API accepts an
`Idempotency-Key` header on POST requests and returns the identical original
response, including the original status code, if the same key is replayed,
retaining the key for at least 24 hours before it is eligible for reuse
([docs.stripe.com/api/idempotent_requests](https://docs.stripe.com/api/idempotent_requests),
verified 2026-08-02). In this variant the idempotency mechanism lives on the
callee's side, and the consumer's job is only to derive a stable key from the
message ID and pass it through consistently on every retry of the outbound
call.

**Broker-native deduplication window.** Some transports offer deduplication
as a transport feature rather than an application concern. Amazon SQS FIFO
queues deduplicate messages sharing a `MessageDeduplicationId`, explicit or
content-based via a SHA-256 hash of the body, within a five-minute sliding
window, after which the same ID can be reused without being treated as a
duplicate
([docs.aws.amazon.com, SQS FIFO queues guide](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues.html),
verified 2026-08-02). Azure Service Bus offers duplicate detection on a
queue or topic, tracking the application-supplied `MessageId` within a
configurable history window that defaults to ten minutes, with a minimum of
twenty seconds and a maximum of seven days, and discards a resend carrying an
already-seen `MessageId` inside that window
([learn.microsoft.com, Azure Service Bus duplicate detection](https://learn.microsoft.com/en-us/azure/service-bus-messaging/duplicate-detection),
verified 2026-08-02). This variant is cheaper to operate than an
application-level table, because the broker does the bookkeeping, but it only
protects redelivery inside the configured window. An outage or a manual
replay that resends a message after the window has closed is not covered,
and the application-level pattern is the only thing that closes that gap
completely.

**Time-to-live-bound external store for stateless functions.** Serverless
consumers that do not own a long-lived database connection commonly store the
dedup record in a separate key-value store with a time-to-live, rather than
in the same relational database as the business effect, because the
function's own database transaction is often short-lived or absent. AWS's
Powertools for Lambda idempotency utility is a widely used implementation of
exactly this shape, hashing the event payload, or a configured subset of it,
into a key, storing it in DynamoDB with a TTL, and returning the saved
response on a repeated invocation with the same key
([docs.aws.amazon.com/powertools/python/latest/utilities/idempotency](https://docs.aws.amazon.com/powertools/python/latest/utilities/idempotency/),
verified 2026-08-02). Because the dedup write and the business effect are not
in the same transaction in this variant, it trades perfect atomicity for
operational simplicity, and it is the correct trade for handlers whose
external database, if any, does not sit close enough to the function runtime
to make a single transaction practical.

## 9. Known production uses

**Eventuate.** Richardson's own Eventuate platform, the reference
implementation accompanying the microservices.io catalog and the
*Microservices Patterns* book, implements Idempotent Consumer as one of its
core reliability mechanisms for message-driven services
([microservices.io/patterns/communication-style/idempotent-consumer.html](https://microservices.io/patterns/communication-style/idempotent-consumer.html),
verified 2026-08-02).

**Stripe's API.** Stripe's idempotency-key mechanism is the pattern applied
at the API boundary rather than at a message-broker boundary. A client
resubmits a POST request with the same `Idempotency-Key` after a timeout or a
network failure, and Stripe returns the original result rather than creating
a second charge, refund, or customer record. Stripe explicitly documents that
the saved result is returned regardless of whether the original request
succeeded or failed, including on a 500 error, so that a client cannot tell,
from the response alone, whether its retry actually triggered a fresh
execution
([docs.stripe.com/api/idempotent_requests](https://docs.stripe.com/api/idempotent_requests),
verified 2026-08-02).

**AWS SQS FIFO queues.** Amazon implements broker-level idempotent delivery
as a first-class queue feature, deduplicating on `MessageDeduplicationId`
within a five-minute window so that a producer's network retry does not
result in the message being delivered, and therefore processed, twice by a
downstream consumer
([docs.aws.amazon.com, SQS FIFO queues guide](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues.html),
verified 2026-08-02).

**Azure Service Bus.** Microsoft implements the equivalent mechanism as
duplicate detection on standard and premium tier queues and topics, tracking
the sender-supplied `MessageId` within a configurable history window, and
the documentation frames it explicitly around the same failure scenario this
pattern exists to solve, a sender left in doubt about whether its message
was committed, resending it, and the broker silently dropping the resend
([learn.microsoft.com, Azure Service Bus duplicate detection](https://learn.microsoft.com/en-us/azure/service-bus-messaging/duplicate-detection),
verified 2026-08-02).

**AWS Lambda Powertools idempotency utility.** AWS ships a maintained,
first-party idempotency helper for Lambda functions triggered by SQS,
EventBridge, and API Gateway, which hashes the incoming event into a key and
stores the outcome in DynamoDB with a TTL so a retried invocation of the
same event returns the previously computed response instead of re-executing
the handler
([docs.aws.amazon.com/powertools/python/latest/utilities/idempotency](https://docs.aws.amazon.com/powertools/python/latest/utilities/idempotency/),
verified 2026-08-02). This is a named, first-party AWS tool, not a
third-party library, and it exists precisely because Lambda behind SQS is
one of the most common places engineers rediscover the need for this
pattern.

## 10. Consequences

Positive.

- **Correctness under the delivery guarantee the transport actually offers.**
  The consumer becomes safe under at-least-once delivery instead of merely
  hoping duplicates never arrive, which they eventually will under any
  sustained production load.
- **The business effect and the fact of having processed it become
  co-located and auditable.** A dedicated dedup table doubles as an audit
  trail of exactly which message caused exactly which effect, which is
  useful independent of the deduplication itself when investigating an
  incident.
- **It decouples the consumer's correctness from the producer's retry
  behavior**, within the limit that the producer must still preserve
  message identity across retries. The consumer no longer has to trust that
  the producer, or the network between them, never duplicates.

Negative.

- **Extra storage that grows without bound unless actively managed.** Every
  processed message leaves a permanent row unless a retention policy prunes
  it, and choosing the retention window is itself a correctness decision,
  not only a cost one, because a message ID that has already been forgotten
  and then genuinely redelivered defeats the check silently.
- **An extra read and an extra write on the hot path of every single
  message**, which is a real, measurable latency and throughput cost at
  scale, not a theoretical one.
- **It only protects the exact operation guarded by the transaction.** If
  the handler performs a side effect outside the transaction boundary, for
  example an outbound email send that happens after the database commit,
  that side effect is not covered and can still duplicate even with a
  perfectly correct dedup table in place. This is the single most common
  way engineers believe they have solved the problem and have not.
- **The message identifier becomes a hard external contract.** Once
  consumers depend on message ID stability across retries, changing how the
  producer generates that ID becomes a breaking change for every downstream
  consumer, even though nothing in the message schema itself changed.

## 11. Failure modes and misuse

This dimension is largely engineering judgement drawn from operational
experience, not a set of sourced facts.

| Symptom | Cause | Fix |
|---|---|---|
| A payment is captured twice, or an email is sent twice, despite a dedup table existing in the schema | The business effect and the dedup-table insert are committed in two separate transactions, so a crash between them leaves the effect applied with no matching dedup record, and redelivery reapplies it | Put the business write and the dedup-table insert inside one atomic transaction, never two sequential commits |
| Duplicates reappear weeks after an incident, well after the original bug was fixed | The dedup store's retention window, a TTL, or a manual pruning job, expired before a manually replayed dead-letter queue was reprocessed | Size the retention window to the longest realistic replay delay in the operation, not to the transport's own redelivery window, and treat dead-letter-queue replay as a first-class scenario when choosing that window |
| Deduplication silently stops working after a producer deploy, with no error anywhere | The producer started generating a fresh message ID, a UUID from a library call, on every retry attempt instead of reusing the original ID, which defeats the consumer's check even though the consumer code has not changed | Contractually pin message-ID generation to happen once, at first send, and to be carried through unchanged on every retry, and add a producer-side test that resending the same logical event across a simulated retry preserves the same ID |
| The dedup table grows without bound and eventually degrades write throughput on every message | No pruning policy was ever implemented, because the pattern was adopted for correctness and retention was treated as an afterthought | Add a scheduled job or a native TTL feature, such as DynamoDB TTL or a Postgres partition dropped on schedule, sized to the chosen retention window from day one, not after the table becomes a production incident |
| Duplicate side effects happen under load specifically, but not in staging | Competing consumers, multiple instances reading the same queue, both fetch the same redelivered message before either one's dedup insert commits, and the application code does not handle the unique-constraint violation as an expected outcome, so it crashes or silently double-applies before the constraint is even reached | Rely on the database's unique constraint as the source of truth for who won the race, and explicitly catch and handle the constraint violation as a duplicate, rolling back the business write and acknowledging the message, rather than trying to prevent the race with application-level locking alone |
| A fixed version of the handler still double-applies effects that happen after the transaction commits | The idempotency check only wraps the database write, and a downstream call, an outbound webhook, a third-party charge, a queued follow-up event, happens after commit and is not covered by the same guard | Extend the idempotent boundary to cover every externally visible side effect the handler performs, using the external-request idempotency-key variant from dimension 8 for calls the consumer does not control the retry semantics of |

## 12. Trade-off matrix

Comparison against named alternative strategies for the same
at-least-once-delivery problem, across the forces from dimension 3.

| Approach | Correctness under retries | Latency cost per message | Storage growth | Coupling to producer behavior |
|---|---|---|---|---|
| Idempotent Consumer, dedup table, this pattern | Strong, enforced at the database via a unique constraint | One extra read, one extra write, in the same transaction | Unbounded unless a retention policy is added | Depends on the producer preserving message ID across retries |
| Naturally idempotent operation design, absolute assignment instead of relative increment | Strong, and free of extra storage entirely | None beyond the operation itself | None | No dependency on message identity at all |
| Broker-native deduplication window, SQS FIFO, Azure Service Bus duplicate detection | Strong inside the configured window, absent outside it | Handled by the broker, invisible to application code | Bounded by the broker's own window, not application-managed | Same dependency on stable message ID, enforced by the broker instead of the application |
| Exactly-once stream processing, Kafka transactional producer plus transactional consumer, read-process-write entirely inside Kafka | Strong, but only for effects that stay inside the Kafka cluster | Higher, due to transaction coordination overhead on every batch | None beyond Kafka's own transaction log retention | No dependency on application-level message ID discipline, but does not extend past Kafka's boundary |
| Do nothing, rely on the producer to send exactly once | Weak, violated by any producer retry, network partition, or consumer crash before ack | None | None | Total, correctness collapses the moment any retry occurs anywhere in the path |

## 13. Related and incompatible patterns

**Transactional Outbox.** The producer-side mirror of this pattern. Outbox
guarantees a producer publishes a message exactly once for a given database
transaction by writing the event and the business change atomically and
relaying it out later. Idempotent Consumer assumes the opposite is not
guaranteed and protects the receiving side regardless of whether the sender
used an outbox. The two compose naturally, an outbox on the producer reduces
how often duplicates occur, and an idempotent consumer covers the cases an
outbox cannot reach, such as a network-level redelivery after the outbox
message was already relayed successfully.

**Transaction Log Tailing.** One of the two relay mechanisms that feed a
Transactional Outbox, and therefore an indirect producer of the very
at-least-once stream this pattern exists to consume safely. Log tailing
implementations are themselves prone to replaying already-published entries
after a relay restart, which makes an idempotent consumer on the receiving
end even more necessary than with a simpler polling relay.

**Domain Event.** The message payload this pattern most often protects. A
domain event describes something that already happened and is frequently
delivered by the same at-least-once transports this pattern is built for.
The event's own identifier is typically the field an idempotent consumer
keys its dedup check on.

**Saga.** A saga coordinates a sequence of local transactions across
services using messages, and every step of a saga is itself a message-driven
handler that needs the same at-least-once protection as any other consumer.
An unprotected saga step that double-applies its compensating or forward
action can corrupt the saga's own state machine, so idempotency at each step
is treated as a prerequisite for a saga implementation to be considered
correct, not an optional add-on.

**Database Per Service.** Idempotent Consumer's dedup table lives inside the
consuming service's own database, which is only possible, and only cleanly
scoped, when that service owns its data store outright rather than sharing
one with other services. A shared database, see Shared Database, marked
incompatible with several patterns in this family, makes it awkward to
decide which service's schema the dedup table belongs to.

There is no pattern in this catalog that is structurally incompatible with
Idempotent Consumer. It composes with essentially every message-driven
pattern because it operates purely on the receiving side and makes no
assumption about how the message was produced.

## 14. Refactoring path in and out

**Introducing it into a consumer that currently assumes exactly-once
delivery.** Start by confirming every message the consumer receives carries
a stable, retry-safe identifier. If the producer does not guarantee this
yet, fix that first, because no amount of consumer-side work compensates for
an identifier that changes on retry. Add a dedup table with a unique
constraint on that identifier. Wrap the existing business-effect write and a
new insert into the dedup table inside the same database transaction the
handler already opens, a change most ORMs and query builders make small and
local rather than a rewrite. Explicitly catch the unique-constraint
violation and treat it as the normal already-processed path, rather than
letting it surface as an unhandled error. Only after this lands, audit the
handler for side effects that occur after the transaction commits, outbound
API calls, emails, follow-on messages, and extend coverage to those using
the external-request idempotency-key variant, because the transaction-scoped
fix alone does not reach them.

**Removing it when it is no longer needed.** This is rare in practice,
because downgrading delivery guarantees is unusual, but it happens when a
system migrates from a general-purpose at-least-once broker to a transport
that offers a verified, end-to-end exactly-once guarantee for the specific
operation in question, such as consolidating a read-process-write pipeline
entirely inside Kafka's transactional semantics. Before removing the
application-level dedup table, confirm the new guarantee actually covers
every side effect the handler performs, not merely the write to the primary
data store. If any side effect leaves the transactional boundary, the
application-level pattern must stay in place for that side effect even
after the primary write no longer needs it.

## 15. Testing and verification

Testing this pattern is largely a matter of practice rather than a citable
methodology.

The defining test is delivering the same message twice to the handler in a
single test run and asserting the business effect happened exactly once, not
merely that no exception was thrown. A test that only checks for the absence
of an error on duplicate delivery, without asserting the side effect's
cardinality, passes even on a broken implementation that silently
double-applies the effect without erroring.

A second essential test simulates the race condition directly, two
concurrent calls into the handler with the same message ID, asserting that
exactly one of them applies the business effect and the other observes the
constraint violation and takes the duplicate path. This requires either two
real threads or processes racing against a real database, an integration
test rather than a unit test with a mocked store, because the correctness of
this pattern lives entirely in the atomicity guarantee the real database
provides. A mock that does not enforce uniqueness proves nothing about
whether the production constraint is even declared correctly.

A third test asserts the negative case for retention, a message ID that was
processed, then pruned from the dedup store after its retention window,
correctly gets processed again if redelivered after pruning. This is not a
bug to fix, but a boundary the team should decide about deliberately and
test for, so the retention window's behavior is documented in the test suite
rather than discovered in an incident.

Test doubles for the dedup store itself should be avoided in favor of a real
database, or a real embedded equivalent, such as an in-memory Postgres or
SQLite instance with the actual unique constraint declared, precisely
because the uniqueness enforcement is the mechanism under test, and an
in-memory fake map is very easy to write in a way that is subtly non-atomic
under concurrency, which defeats the point of the test.

## 16. Observability signals

A healthy Idempotent Consumer produces a low, steady rate of duplicate
detections, non-zero, because duplicates are an expected, routine outcome of
at-least-once delivery under any real production load, not an anomaly.

Log or emit a metric on every duplicate detection distinctly from every
fresh-processing event, with the message ID attached, so an operator can
tell duplicate rate apart from throughput. A sudden spike in the duplicate
rate usually indicates a redelivery storm, commonly caused by a consumer
group rebalance, a visibility-timeout misconfiguration on SQS, or a
downstream outage causing the broker to retry aggressively. A sudden drop to
zero after previously being non-zero on a system with real network variance
is itself worth investigating, because it can mean the dedup check silently
stopped working, for example because the unique constraint was dropped in a
migration, or the message-ID field started arriving empty.

Track the size and growth rate of the dedup store as a first-class metric,
not an afterthought, since unbounded growth is one of the pattern's named
consequences. Alert on the pruning job's own health separately from the
consumer's health. A pruning job that silently stops running is invisible
in every other metric until the table's growth starts affecting write
latency, by which point the fix is more disruptive than it needed to be.

Trace the check-then-act sequence, dedup lookup, business write, dedup
insert, acknowledgment, as a single logical span where distributed tracing
is in use, so that a slow consumer can be diagnosed as slow on the dedup
lookup versus slow on the business effect versus slow to acknowledge, which
are three different operational problems with three different fixes.

## 17. Security and privacy implications

The message identifier used as the dedup key must not itself carry
sensitive data, because it is retained, often for longer than the business
record it protects, in a table whose access controls may be looser than the
primary business table's, since it was added for reliability rather than
designed as a data store from the start. Stripe's own documentation makes
this point directly, advising against using emails or other personal
identifiers as idempotency keys, precisely because the key is stored and can
outlive the data-retention assumptions made for the primary record
([docs.stripe.com/api/idempotent_requests](https://docs.stripe.com/api/idempotent_requests),
verified 2026-08-02).

An idempotency mechanism that trusts a client-supplied key without
validating its provenance opens a distinct attack surface. An attacker who
can guess or observe another user's idempotency key, or who can reuse their
own key across requests they should not be able to link, can potentially
cause a server to return a cached result for a request it never actually
authorized, or can correlate two logically separate requests that were meant
to be independent. Any idempotency key accepted from outside the trust
boundary should be scoped to, or validated against, the authenticated caller
who originally created it, not treated as a bare, caller-agnostic token.

The dedup store becomes an audit trail by construction, which is a security
benefit for incident investigation, since it answers whether a system
already acted on this event, but also means it is subject to the same
data-retention and right-to-erasure obligations as any other store holding a
record tied to a specific transaction or user, if the message ID or its
associated metadata can be linked back to an individual under a regime like
GDPR. Retention-window decisions made purely for storage-cost reasons, from
dimension 3, should be cross-checked against these obligations rather than
decided in isolation.

## 18. References

- Chris Richardson. "Idempotent consumer." microservices.io pattern
  catalog. <https://microservices.io/patterns/communication-style/idempotent-consumer.html>
  Verified 2026-08-02.
- Chris Richardson. *Microservices Patterns*. Manning, 2018, chapter 3.
- Gregor Hohpe and Bobby Woolf. *Enterprise Integration Patterns*.
  Addison-Wesley, 2003, the Message and Message Endpoint chapters.
- Stripe. "Idempotent requests." Stripe API documentation.
  <https://docs.stripe.com/api/idempotent_requests>
  Verified 2026-08-02.
- Amazon Web Services. "Amazon SQS FIFO (First-In-First-Out) queues." AWS
  SQS Developer Guide.
  <https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues.html>
  Verified 2026-08-02.
- Amazon Web Services. "Idempotency utility." Powertools for AWS Lambda
  (Python) documentation.
  <https://docs.aws.amazon.com/powertools/python/latest/utilities/idempotency/>
  Verified 2026-08-02.
- Microsoft. "Duplicate detection." Azure Service Bus documentation.
  <https://learn.microsoft.com/en-us/azure/service-bus-messaging/duplicate-detection>
  Verified 2026-08-02.
- Apache Software Foundation. "Kafka documentation, semantics." Apache
  Kafka documentation.
  <https://kafka.apache.org/documentation/#semantics>
  Verified 2026-08-02, for the boundary of Kafka's own exactly-once
  guarantee referenced in dimension 4.

## Code examples

Three languages, TypeScript, Python, and Go. All three were chosen because
the pattern is a common, idiomatic building block in message-driven backend
services across all three ecosystems, and each sample below was compiled or
syntax-checked against its own toolchain before inclusion.

Each sample simulates an at-least-once transport by delivering one message
twice, and demonstrates that the business effect, a balance mutation, is
applied exactly once while the second delivery is detected and discarded.

```typescript
interface Message {
  id: string;
  accountId: string;
  amountCents: number;
}

class DuplicateMessageError extends Error {}

class DedupStore {
  private seen = new Set<string>();

  // Atomic in a real database via a unique constraint on message_id.
  // A Set.add-then-check simulates that atomicity for this in-memory sample.
  markProcessed(messageId: string): void {
    if (this.seen.has(messageId)) {
      throw new DuplicateMessageError(messageId);
    }
    this.seen.add(messageId);
  }
}

class AccountLedger {
  private balances = new Map<string, number>();

  applyDebit(accountId: string, amountCents: number): void {
    const current = this.balances.get(accountId) ?? 0;
    this.balances.set(accountId, current - amountCents);
  }

  balanceOf(accountId: string): number {
    return this.balances.get(accountId) ?? 0;
  }
}

class IdempotentConsumer {
  constructor(
    private readonly dedup: DedupStore,
    private readonly ledger: AccountLedger,
  ) {}

  // The dedup write and the business write commit as one unit in production.
  // Here that atomicity is represented by ordering, not a real transaction.
  handle(message: Message): "applied" | "duplicate" {
    try {
      this.dedup.markProcessed(message.id);
    } catch (err) {
      if (err instanceof DuplicateMessageError) {
        return "duplicate";
      }
      throw err;
    }
    this.ledger.applyDebit(message.accountId, message.amountCents);
    return "applied";
  }
}

function main(): void {
  const consumer = new IdempotentConsumer(new DedupStore(), new AccountLedger());
  const message: Message = { id: "evt-4471", accountId: "acct-1", amountCents: 500 };

  const first = consumer.handle(message);
  const secondDelivery = consumer.handle(message); // broker redelivers the same id

  if (first !== "applied" || secondDelivery !== "duplicate") {
    throw new Error("idempotent consumer did not behave as expected");
  }
}

main();
```

```python
from dataclasses import dataclass


class DuplicateMessageError(Exception):
    pass


@dataclass(frozen=True)
class Message:
    id: str
    account_id: str
    amount_cents: int


class DedupStore:
    def __init__(self) -> None:
        self._seen: set[str] = set()

    def mark_processed(self, message_id: str) -> None:
        # A real store enforces this with a unique constraint on message_id,
        # committed in the same transaction as the business write below.
        if message_id in self._seen:
            raise DuplicateMessageError(message_id)
        self._seen.add(message_id)


class AccountLedger:
    def __init__(self) -> None:
        self._balances: dict[str, int] = {}

    def apply_debit(self, account_id: str, amount_cents: int) -> None:
        current = self._balances.get(account_id, 0)
        self._balances[account_id] = current - amount_cents

    def balance_of(self, account_id: str) -> int:
        return self._balances.get(account_id, 0)


class IdempotentConsumer:
    def __init__(self, dedup: DedupStore, ledger: AccountLedger) -> None:
        self._dedup = dedup
        self._ledger = ledger

    def handle(self, message: Message) -> str:
        try:
            self._dedup.mark_processed(message.id)
        except DuplicateMessageError:
            return "duplicate"
        self._ledger.apply_debit(message.account_id, message.amount_cents)
        return "applied"


def main() -> None:
    consumer = IdempotentConsumer(DedupStore(), AccountLedger())
    message = Message(id="evt-4471", account_id="acct-1", amount_cents=500)

    first = consumer.handle(message)
    second_delivery = consumer.handle(message)

    assert first == "applied"
    assert second_delivery == "duplicate"
    assert consumer._ledger.balance_of("acct-1") == -500


if __name__ == "__main__":
    main()
```

```go
package main

import (
	"errors"
	"fmt"
	"sync"
)

var ErrDuplicateMessage = errors.New("duplicate message")

type Message struct {
	ID          string
	AccountID   string
	AmountCents int
}

type DedupStore struct {
	mu   sync.Mutex
	seen map[string]bool
}

func NewDedupStore() *DedupStore {
	return &DedupStore{seen: make(map[string]bool)}
}

// MarkProcessed simulates the unique-constraint check a real database
// performs atomically alongside the business write in the same transaction.
func (d *DedupStore) MarkProcessed(messageID string) error {
	d.mu.Lock()
	defer d.mu.Unlock()
	if d.seen[messageID] {
		return ErrDuplicateMessage
	}
	d.seen[messageID] = true
	return nil
}

type AccountLedger struct {
	mu       sync.Mutex
	balances map[string]int
}

func NewAccountLedger() *AccountLedger {
	return &AccountLedger{balances: make(map[string]int)}
}

func (l *AccountLedger) ApplyDebit(accountID string, amountCents int) {
	l.mu.Lock()
	defer l.mu.Unlock()
	l.balances[accountID] -= amountCents
}

func (l *AccountLedger) BalanceOf(accountID string) int {
	l.mu.Lock()
	defer l.mu.Unlock()
	return l.balances[accountID]
}

type IdempotentConsumer struct {
	dedup  *DedupStore
	ledger *AccountLedger
}

func (c *IdempotentConsumer) Handle(m Message) (string, error) {
	err := c.dedup.MarkProcessed(m.ID)
	if errors.Is(err, ErrDuplicateMessage) {
		return "duplicate", nil
	}
	if err != nil {
		return "", err
	}
	c.ledger.ApplyDebit(m.AccountID, m.AmountCents)
	return "applied", nil
}

func main() {
	consumer := &IdempotentConsumer{dedup: NewDedupStore(), ledger: NewAccountLedger()}
	message := Message{ID: "evt-4471", AccountID: "acct-1", AmountCents: 500}

	first, err := consumer.Handle(message)
	if err != nil {
		panic(err)
	}
	secondDelivery, err := consumer.Handle(message)
	if err != nil {
		panic(err)
	}

	if first != "applied" || secondDelivery != "duplicate" {
		panic(fmt.Sprintf("unexpected results, first=%s second=%s", first, secondDelivery))
	}
	if consumer.ledger.BalanceOf("acct-1") != -500 {
		panic("balance should reflect exactly one debit")
	}
}
```

Java, Rust, and Swift are omitted from this entry, not because the pattern
does not translate, it translates cleanly to all three, but because the
three languages above already demonstrate every idiomatic shape the pattern
takes, an exception-based guard, a Python assertion-checked guard, and a
mutex-guarded map with an explicit sentinel error, and a fourth or fifth
language would repeat the same shape without adding a new idea.
