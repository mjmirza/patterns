---
name: Transactional Outbox
slug: transactional-outbox
family: 10-microservices
category: Structural
aliases: [Outbox Pattern, Event Outbox, Application Events Table]
first_described: "Richardson, microservices.io pattern catalog, and Morling, Debezium blog, Reliable Microservices Data Exchange With the Outbox Pattern, 2019"
maturity: canonical
related: [saga, api-composition, database-per-service, decompose-by-business-capability, decompose-by-subdomain]
incompatible_with: [shared-database]
verified: 2026-08-03
---

# Transactional Outbox

## 1. Name, aliases, and lineage

The canonical name in the microservices catalog literature is Transactional
Outbox, shortened almost everywhere in practitioner writing to the Outbox
Pattern. Chris Richardson, who curates the microservices.io pattern catalog
and wrote *Microservices Patterns*, Manning, 2019, places it in the data
category and states the problem it answers this way, how to atomically
update the database and send messages to a message broker
([microservices.io, "Transactional outbox"](https://microservices.io/patterns/data/transactional-outbox.html),
verified 2026-08-02). His solution statement is equally direct. the service
which sends the message first stores the message in the database, as
part of the same transaction that updates the business entities, and a
separate process then delivers the messages to the broker (same page,
verified 2026-08-02).

The name that stuck in day-to-day engineering conversation, Outbox Pattern,
was popularised largely through Gunnar Morling's 2019 Debezium blog post,
which frames the idea using the same "outbox" noun, an actual table named
`outbox` sitting in the service's own schema, holding rows that represent
messages waiting to leave the building
(Gunnar Morling, ["Reliable Microservices Data Exchange With the Outbox Pattern"](https://debezium.io/blog/2019/02/19/reliable-microservices-data-exchange-with-the-outbox-pattern/),
Debezium blog, 19 February 2019, verified 2026-08-03). Morling's own text is
careful to say the idea is not new, that it predates microservices and shows
up even where JMS-style brokers could in principle join a distributed
transaction, because avoiding that coupling was already worth it before
message brokers like Apache Kafka made distributed transactions
impractical outright (same source, verified 2026-08-03).

A third name worth recording because it appears in .NET shops specifically is
Application Events Table, used in Microsoft's own reference documentation for
the eShopOnContainers sample, where the concrete table is called
`IntegrationEventLog` rather than `outbox`
([Microsoft Learn, "Subscribing to events"](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/multi-container-microservice-net-applications/subscribe-events),
verified 2026-08-03). The table plays the identical structural role. This
entry uses Outbox and Transactional Outbox interchangeably, and treats
`IntegrationEventLog` as the same participant under a different vendor's
naming convention.

The pattern is closely related to, and is frequently confused with, three
neighbours worth separating up front.

- **Change Data Capture (CDC).** A generic mechanism for turning row-level
  database changes into a stream of events by reading the write-ahead log.
  CDC is one of the two ways to build the message relay half of Transactional
  Outbox (see dimension 8), but CDC applied directly to domain tables,
  without an outbox table, is a different and riskier design, covered under
  non-applicability in dimension 4.
- **Event Sourcing.** Stores every state change as the durable record of
  truth and derives current state by replaying events. Transactional Outbox
  stores current state as usual and adds a narrow, separate log of only the
  events meant for other services. The two are frequently paired but are not
  the same commitment, and the Microsoft reference above explicitly frames
  the outbox table as "a simplified ES system" applied only to integration
  events, not domain state
  ([Microsoft Learn, "Subscribing to events"](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/multi-container-microservice-net-applications/subscribe-events),
  verified 2026-08-03).
- **Saga.** A separate pattern for coordinating a multi-step business
  transaction across services with compensation on failure. A saga's steps
  are commonly triggered by events, and those events are commonly delivered
  through an outbox. Outbox is a delivery guarantee, and Saga is a
  coordination protocol built on top of reliable delivery.

## 2. Problem and context

A service owns its own database, as the Database per Service pattern in this
same family requires. As part of handling a request, the service both writes
to that database and needs to tell other services, or a downstream system,
that something happened, by publishing a message to a broker such as Apache
Kafka, RabbitMQ, or a cloud queue.

The two writes, the database commit and the broker publish, target two
different systems. A relational database and a message broker cannot, in
the general case, be enrolled in one distributed transaction. Kafka in
particular offers no support for being coordinated by an external
transaction manager (XA) at all. Even where a broker technically can join a
two-phase commit, as some JMS brokers historically could, doing so couples
the service's availability to the broker's availability at write time and is
avoided in practice for exactly that reason
([Gunnar Morling, Debezium blog, 2019](https://debezium.io/blog/2019/02/19/reliable-microservices-data-exchange-with-the-outbox-pattern/),
verified 2026-08-03).

So the two writes end up issued separately, and that separation creates the
dual write problem. The database commit can succeed while the broker publish
fails, for instance because of a transient network partition between the
service and the broker. The reverse can also happen. the publish succeeds
and the process then crashes before the local commit, or before the
transaction that was supposed to persist the same fact ever runs. Either
outcome leaves the system in a state the two writes were meant to prevent,
a record with no corresponding event, or an event with no corresponding
record. In an order-placement flow this shows up concretely as an order
that exists in the order service's database with nobody downstream ever
told about it, so a shipment is never created, or the mirror image, a
shipment created for an order that, from the order service's own point of
view, was never actually placed.

The context in which Transactional Outbox is the right answer has three
parts. The service already owns a transactional database it can write to
locally. The service needs to notify other parties asynchronously of state
changes it makes, not synchronously call them. And the service can tolerate
eventual delivery, on the order of milliseconds to low seconds under normal
operation, rather than requiring the message to leave atomically with the
commit.

## 3. Forces

- **Consistency.** Favoured, but of a specific kind. The pattern gives you
  atomicity between the local write and the *record of intent to publish*,
  never atomicity between the local write and the message actually landing
  in the broker. Downstream, that is at-least-once delivery with
  eventual consistency, not exactly-once, and every design decision in this
  entry follows from accepting that.
- **Read your own writes.** Favoured for the writing service itself. Because
  the domain write and the outbox write commit together in one local
  transaction, a query against the local database immediately after the
  request completes sees the new state, unlike a design that publishes
  first and derives local state from consuming its own event
  (Morling names this "read your own writes" explicitly as the property this
  design preserves, [Debezium blog, 2019](https://debezium.io/blog/2019/02/19/reliable-microservices-data-exchange-with-the-outbox-pattern/),
  verified 2026-08-03).
- **Coupling.** Reduced at write time. The service that raises an event no
  longer needs the broker to be reachable, or even to exist, at the moment
  it commits the business fact. The coupling moves to the relay component,
  which is a separate concern with its own retry and backoff behaviour.
- **Latency.** Slightly worsened for message delivery, favourably unaffected
  for the request path. The request itself only pays for one extra insert
  into the outbox table inside the transaction it was already opening. The
  broker publish happens later, on the relay's schedule, typically hundreds
  of milliseconds behind the commit for a polling relay and closer to
  real time for a log-tailing relay.
- **Operability.** Sacrificed. A new component exists that did not exist
  before, the relay, and it needs its own monitoring for lag, error rate,
  and a growth-bounded table. An operator who does not know this component
  exists will not understand why events are delayed or missing.
- **Storage cost and cleanup.** Sacrificed. The outbox table grows without
  bound unless something prunes or archives published rows, and unmanaged
  growth degrades both the table and, in Postgres specifically, autovacuum
  behaviour on a hot table with a high delete or update churn.
- **Delivery guarantee shape.** The pattern trades "exactly once" for
  "at-least-once, with the row's own identity available for dedup." This is
  a deliberate, named trade in every source consulted for this entry, never
  an accident. idempotent consumption is a requirement of adopting Outbox,
  not an optional refinement.

## 4. Applicability and non-applicability

Reach for Transactional Outbox when the following hold together.

- A single service already owns a transactional database for its own state,
  and the events to publish are a direct consequence of a write to that
  database, for instance an order row insert that should also raise
  `OrderPlaced`.
- Downstream consumers can tolerate eventual, not synchronous, delivery,
  and a delay on the order of the relay's polling interval or CDC lag is
  acceptable for the business process involved.
- The team is willing to run and monitor an additional component, the
  relay, whether that is a scheduled poller inside the service or a shared
  CDC connector such as Debezium.
- Consumers either are, or can be made, idempotent, because at-least-once
  delivery is the contract, not a corner case.

Do not reach for Transactional Outbox when any of these hold.

- The write and the notification target two databases owned by different
  services rather than one service's own database and its own outbox row.
  Outbox solves the local dual-write problem for a single service. it does
  not solve cross-service consistency, which is what Saga is for.
- The system genuinely needs synchronous confirmation that a downstream
  party received and acted on the change before the original request
  returns. That is a request-response call, or a synchronous Saga step, not
  an asynchronous outbox publish.
- The database in question has no durable, ordered read mechanism a poller
  or CDC connector can use. A key-value store with no ordering guarantee
  and no way to scan "new since last checkpoint" cannot host a reliable
  outbox table the way a relational database, or a document store with a
  change stream, can.
- CDC is going to be pointed directly at the domain tables instead of a
  dedicated outbox table, on the theory that this saves a table. This is a
  real, documented alternative, transaction log tailing of domain data, but
  it is a different and more fragile design. it exposes internal schema
  changes as breaking changes to every consumer, and it forces a mapping
  from low-level row changes back up to business-level events that the
  outbox table exists specifically to avoid having to write
  ([Microsoft Learn, "Subscribing to events"](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/multi-container-microservice-net-applications/subscribe-events),
  verified 2026-08-03, describes this exact trade-off under "transaction
  log mining").
- The volume and size of events would make the outbox table itself the
  bottleneck, for instance publishing large binary payloads at high
  frequency. The outbox row should carry a reference or a compact payload,
  not the thing itself.
- A full Event Sourcing model is already in place for the aggregate in
  question, storing every domain event as the record of truth. Layering a
  second outbox table on top of an event store is usually redundant. the
  event store's own append log can typically serve as the source the relay
  reads from directly.

## 5. Structure

- **Business transaction.** The unit of work in the service, for example
  placing an order, that both mutates domain state and decides an event
  must be raised. It is the only participant permitted to write to the
  outbox table, and it writes exactly once, inside the same local
  transaction as the domain mutation.
- **Domain table(s).** The service's own tables holding its business state,
  unaffected in shape by the presence of the outbox. Any of the Database per
  Service family's rules about ownership continue to apply unchanged.
- **Outbox table.** A table in the same database and same transactional
  scope as the domain tables. Each row represents one message the service
  intends to deliver, carrying enough identity, an aggregate type and id,
  a payload, and a delivery state to let the relay and downstream consumers
  do their jobs without consulting anything else. The canonical column
  shape, as used in Debezium's own worked example, is `id`, `aggregatetype`,
  `aggregateid`, `type`, `payload`
  ([Gunnar Morling, Debezium blog, 2019](https://debezium.io/blog/2019/02/19/reliable-microservices-data-exchange-with-the-outbox-pattern/),
  verified 2026-08-03).
- **Message relay.** A process, separate from the request path, that reads
  outbox rows not yet delivered and publishes each to the message broker.
  It is implemented either as a polling publisher, which periodically
  queries the table, or as a transaction log tailer, which reads the
  database's own write-ahead log for inserts into the outbox table. Both
  variants are described in dimension 8.
- **Message broker.** The transport the relay publishes to, for example
  Apache Kafka, RabbitMQ, or a cloud-native equivalent. The broker's own
  delivery guarantees, at-least-once in the overwhelming majority of
  configurations used in practice, become the effective guarantee the whole
  pipeline offers downstream.
- **Consumer(s).** Services that subscribe to the events the relay
  publishes and must tolerate, and correctly handle, redelivery of a
  message they have already processed.

## 6. ASCII structure diagram

```text
+----------------------------------------------------------+
|                    Order Service (one DB)                |
|                                                            |
|   Business tx:  BEGIN                                     |
|                    INSERT INTO orders (...)                |
|                    INSERT INTO outbox (...)                |
|                  COMMIT                                    |
|                                                            |
|   +--------------+          +-------------------------+   |
|   | orders table |          |      outbox table        |   |
|   +--------------+          +-------------------------+   |
|                                        |                   |
+----------------------------------------|-------------------+
                                          | read (poll or WAL tail)
                                          v
                              +-------------------------+
                              |      Message Relay       |
                              |  (poller or CDC tailer)  |
                              +-------------------------+
                                          |
                                          | publish
                                          v
                              +-------------------------+
                              |      Message Broker      |
                              |     (Kafka / RabbitMQ)   |
                              +-------------------------+
                                    |             |
                                    v             v
                        +-------------------+  +-------------------+
                        | Shipment Service  |  | Customer Service  |
                        |  (idempotent      |  |  (idempotent      |
                        |   consumer)       |  |   consumer)       |
                        +-------------------+  +-------------------+
```

## 7. Dynamics

```text
1. Client -> Order Service : place order
2. Order Service           : BEGIN local transaction
3. Order Service -> orders : INSERT order row (status = placed)
4. Order Service -> outbox : INSERT outbox row
                              (aggregatetype=order, type=OrderPlaced,
                               payload={...}, published_at=NULL)
5. Order Service           : COMMIT
   -- domain fact and intent-to-publish are now durable together --
6. Order Service -> Client : 200 OK  (does not wait on the broker)

-- concurrently, on the relay's own schedule --

7. Relay -> outbox   : SELECT rows WHERE published_at IS NULL
                        ORDER BY id LIMIT batch_size
8. Relay -> Broker   : publish(row.payload, key = row.aggregateid)
9. Broker -> Relay   : ack
10. Relay -> outbox  : UPDATE row SET published_at = now()
                        (second, separate local transaction)

-- if the process crashes between step 9 and step 10 --

11. Relay (restart) -> outbox : re-selects the same row (still NULL)
12. Relay -> Broker            : publish(row.payload, ...)  -- REDELIVERY
13. Consumer -> Consumer state : dedupe on row.id, no-op on redelivery
```

The one moment worth naming explicitly, steps 8 through 10 are two separate
local resources, the broker and the outbox row's own update, and there is no
way to make the pair of them atomic without reintroducing the original dual
write problem one level down. The design's answer is not to eliminate that
gap. it is to shrink the blast radius of the gap down to "the consumer may
see this message twice," and to hand the consumer the tools, the row's own
id, to make that harmless.

## 8. Implementation variants

- **Polling publisher.** The relay runs a query filtered to unpublished rows,
  ordered and limited to a batch, publishes the batch, then updates each
  row's state. Simple to build and reason about, and it needs no
  database-specific tooling. Its costs are polling latency, messages sit
  for up to one polling interval before leaving, and lock contention if
  more than one relay instance polls the same table concurrently. A
  skip-locked select (Postgres, MySQL 8) removes the contention problem
  by letting concurrent pollers each claim a disjoint batch.
- **Transaction log tailing (CDC).** A connector such as Debezium reads the
  database's own write-ahead log (Postgres WAL, MySQL binlog) and turns
  every insert into the outbox table into an event, near-real-time and with
  far lower overhead than repeated polling, because it never issues a query
  against the live table at all
  ([Gunnar Morling, Debezium blog, 2019](https://debezium.io/blog/2019/02/19/reliable-microservices-data-exchange-with-the-outbox-pattern/),
  verified 2026-08-03). Debezium ships a purpose-built Single Message
  Transform for this exact shape, the Outbox Event Router, added after the
  original blog post specifically "to simplify usage of the outbox pattern"
  so that a custom relay is no longer required at all (same source, update
  dated 13 September 2019, verified 2026-08-03).
- **Hybrid poll-plus-notify.** Postgres's LISTEN/NOTIFY can wake a
  poller immediately on insert instead of waiting for the next interval,
  giving near-CDC latency without operating a separate CDC connector. It
  still needs a fallback poll on a longer interval to cover the case where a
  notification is missed while the listener was briefly disconnected.
- **Immediate publish, table as insurance.** Publish synchronously right
  after commit, and only fall back to the outbox row when that publish
  fails, using the row purely as a safety net a background sweep can
  retry from. This is the "first approach" Microsoft documents for
  eShopOnContainers, publish immediately after the local transaction
  commits, then use a second local transaction to mark the row published,
  with no separate worker needed in the common case
  ([Microsoft Learn, "Subscribing to events"](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/multi-container-microservice-net-applications/subscribe-events),
  verified 2026-08-03). The same source is explicit that this variant does
  not handle every failure case on its own and recommends the dedicated
  worker, the classic relay, for anything that must genuinely survive
  failures in a cloud deployment (same source).
- **Framework-provided outbox.** Rather than hand-rolling the table and
  relay, adopt a library that ships both, for example the Eventuate Tram
  framework, built by the same Chris Richardson who authored the pattern,
  which wires an outbox table plus a CDC-based or polling relay into a
  Spring or plain-Java service directly
  ([eventuate.io, "Eventuate Tram"](https://eventuate.io/abouteventuatetram.html),
  verified 2026-08-03).
- **Column shape variants.** Beyond the minimal `id, aggregatetype,
  aggregateid, type, payload` shape, production tables commonly add a
  `created_at` for ordering and observability, a `headers`/`metadata`
  column for tracing context, and either a `published_at` timestamp
  (nullable) or a boolean `published` flag as the delivery-state field the
  relay filters on and the cleanup job later uses to decide what is safe to
  prune.

## 9. Known production uses

- **Eventuate Tram**, an open source Java/Spring framework by Chris
  Richardson that implements Transactional Outbox as a first-class,
  reusable mechanism, an application's outbox table plus a message relay
  wired in for it, rather than a pattern each team re-derives on its own
  ([eventuate.io, "Eventuate Tram"](https://eventuate.io/abouteventuatetram.html),
  verified 2026-08-03; the microservices.io catalog page names Eventuate
  Tram directly as an implementation of this pattern,
  [microservices.io, "Transactional outbox"](https://microservices.io/patterns/data/transactional-outbox.html),
  verified 2026-08-02).
- **Debezium's Outbox Event Router**, a Kafka Connect Single Message
  Transform shipped as part of the Debezium project specifically to route
  outbox-table changes into per-aggregate Kafka topics without a
  hand-written relay. Debezium's own announcement frames it as replacing
  the custom SMT that had to be written by hand in the original 2019
  worked example, meaning the pattern moved from something you implement
  yourself to a supported feature of a widely deployed CDC platform
  ([Gunnar Morling, Debezium blog, 2019, update dated 13 September 2019](https://debezium.io/blog/2019/02/19/reliable-microservices-data-exchange-with-the-outbox-pattern/),
  verified 2026-08-03).
- **Microsoft's eShopOnContainers reference architecture**, the official
  .NET Microservices sample application maintained by Microsoft, uses an
  `IntegrationEventLog` table in the same database as each service's
  domain entities, written in the same local transaction as the domain
  update, exactly matching the Outbox table's structural role under a
  different name
  ([Microsoft Learn, "Subscribing to events"](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/multi-container-microservice-net-applications/subscribe-events),
  verified 2026-08-03, which shows the actual `IntegrationEventLogService`
  call sequence and the concrete GitHub source for it).
- **A widely cited independent .NET reference implementation**, documented
  by Kamil Grzybek, a practitioner whose write-up of the Outbox Pattern is
  itself linked from Microsoft's own architecture guide as the source for
  the pattern's name inside the .NET community
  ([Kamil Grzybek, "The Outbox Pattern"](https://www.kamilgrzybek.com/design/the-outbox-pattern/),
  verified 2026-08-03; referenced directly from
  [Microsoft Learn, "Subscribing to events"](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/multi-container-microservice-net-applications/subscribe-events),
  verified 2026-08-03).

## 10. Consequences

Positive.

- Removes the dual write race between a local database commit and a broker
  publish, without requiring a distributed transaction the broker likely
  cannot join in the first place.
- Preserves read-your-own-writes for the service that raised the event,
  because the domain write and the outbox write commit together, unlike a
  publish-then-derive-local-state design.
- Decouples the request path's success from the broker's availability at
  the moment of the write. a broker outage delays delivery, it does not
  fail the request.
- Gives every downstream consumer a natural, stable dedup key, the outbox
  row's own id, which the pattern's producers are expected to hand along in
  the payload or headers.
- Composes cleanly with CDC tooling that many organisations already operate
  for other reasons, turning adoption into adding a table and a routing
  rule rather than standing up new infrastructure.

Negative.

- Introduces a new operational component, the relay, with its own failure
  modes, a stalled poller, an expired CDC connector offset, broker
  backpressure, that must be monitored independently of the service's own
  health check.
- Guarantees at-least-once delivery only, which is a genuine requirement
  pushed onto every consumer, not a nicety. a consumer written as if
  delivery were exactly-once will eventually double-process a message.
- The outbox table grows monotonically unless something prunes or archives
  published rows, and an unmanaged table degrades index performance and,
  on Postgres specifically, autovacuum behaviour under high row churn.
- Adds one extra write, and in the polling variant, one extra scheduled
  query, to every request path that raises an event, a cost that is small
  per request but is a real, measurable addition once request volume is high.
- Couples the payload shape stored in the outbox to a schema every consumer
  depends on going forward, which is a benefit, stability against internal
  refactors, that is also a new long-lived contract someone has to own and
  version.

## 11. Failure modes and misuse

- **Symptom.** Events are duplicated downstream even though only one order
  was placed.
  **Cause.** This is not a bug, it is the pattern's own at-least-once
  contract surfacing, most often triggered by a relay crash between
  publishing to the broker and marking the outbox row published (dimension
  7, steps 9-10).
  **Fix.** Make consumers idempotent on the outbox row's id, either via a
  dedup table keyed on that id or by designing the handled operation to be
  naturally idempotent, an upsert rather than an insert, for instance.
- **Symptom.** The outbox table's row count grows without bound and query
  latency against it climbs over weeks.
  **Cause.** Published rows are never deleted or archived, so both the
  table and its indexes keep growing, and on Postgres a high-churn,
  never-vacuumed table also accumulates dead tuples faster than autovacuum
  can clear them under default settings.
  **Fix.** Run a periodic cleanup job that deletes or archives rows past a
  retention window once `published_at` is set, and, on Postgres, consider a
  more aggressive autovacuum setting scoped to the outbox table
  specifically.
- **Symptom.** Two relay instances running for redundancy both publish the
  same batch of rows, doubling every event.
  **Cause.** Naive polling with no locking lets two pollers select the same
  unpublished rows in the same window.
  **Fix.** Use a skip-locked select (Postgres, MySQL 8) so concurrent
  pollers claim disjoint rows, or run exactly one active poller behind a
  leader-election lock, or move to a CDC-based relay, which by design has
  a single reader per replication slot.
- **Symptom.** One malformed or oversized row blocks every event after it
  from being delivered, and the relay's lag climbs steadily.
  **Cause.** A strictly ordered poll, or an ordered CDC stream, retries the
  same failing row forever, and nothing behind it in the batch can proceed
  while it is stuck, head-of-line blocking.
  **Fix.** Move a row to a dead-letter state, a separate column or table,
  after a bounded retry count, so the relay can skip past it and keep the
  rest of the stream flowing, and alert on anything landing in that state.
- **Symptom.** Consumer ordering is wrong. a cancellation event is
  processed before the creation event it depends on, even though both came
  from the same aggregate.
  **Cause.** Multiple relay workers or unpartitioned publishing let events
  for the same aggregate leave out of insertion order.
  **Fix.** Partition the broker topic, and the relay's publish key, on
  `aggregateid`, Kafka's per-partition ordering guarantee is the mechanism
  Debezium's own routing SMT relies on for exactly this reason, and if
  using multiple pollers, shard their claimed rows by the same key rather
  than by arbitrary row ranges.
- **Symptom.** The outbox table is used as a general-purpose message queue
  for large payloads, and write latency on the domain transaction climbs.
  **Cause.** Storing full documents, images, or large JSON blobs directly
  in the payload column inflates the transaction's write-ahead log volume
  and slows down every commit that touches the table, not just the ones
  that need to.
  **Fix.** Keep the payload compact and store a reference, an object
  storage key, a foreign key into a details table, for anything large,
  publishing the reference rather than the content.

## 12. Trade-off matrix

Compared against the named alternatives for the same dual-write problem.

| Force | Transactional Outbox | Two-phase commit (XA) | Full Event Sourcing | "Listen to yourself" (publish first, derive local state) | Raw CDC of domain tables |
|---|---|---|---|---|---|
| Consistency between DB and broker | Eventual, at-least-once | Atomic, if both resources support XA | Eventual, but the event is the truth | Eventual, and briefly stale locally | Eventual, tightly coupled to schema |
| Broker support required | Any broker, no XA needed | Broker must support XA, Kafka does not | Any broker | Any broker | CDC connector for the DB engine |
| Read your own writes | Yes, immediately | Yes, immediately | Yes, if replaying is fast | No, until self-consumption completes | Yes, immediately |
| New infrastructure | An outbox table, optionally CDC tooling | A distributed transaction coordinator | An event store, replay tooling | None beyond the broker | A CDC connector, no outbox table |
| Coupling to internal schema | Low, payload shape is a deliberate contract | Low | Low, events are the contract by design | Low | High, consumers see raw table shape |
| Operational cost | Medium, a relay to run and watch | High, XA coordinators are heavy and rare in modern stacks | High, a new storage model for the whole aggregate | Low, no relay, but adds self-consumption complexity | Medium, but fragile to schema change |

## 13. Related and incompatible patterns

- **Saga.** Directly composes with Transactional Outbox. A saga's
  choreography or orchestration steps are commonly triggered by events, and
  those events are commonly the ones an outbox reliably delivers. Outbox
  answers how to reliably emit the event a saga step depends on, and
  Saga answers how to coordinate the multi-step business transaction
  those events drive.
- **Change Data Capture.** A mechanism Transactional Outbox can use for its
  relay half (dimension 8), not a competing pattern. CDC applied to domain
  tables directly, without an outbox table, is the non-applicable variant
  described in dimension 4.
- **Event Sourcing.** Overlapping in spirit, distinct in commitment. Where
  both are used together, the outbox table typically narrows down to
  carrying only the subset of domain events meant for external consumers,
  while the event store remains the full internal record.
- **Idempotent Receiver / Idempotent Consumer.** A required companion, not
  optional. Because Outbox guarantees at-least-once delivery, every
  consumer of an outbox-relayed event is expected to implement this pattern
  on the receiving end. the two are effectively adopted as a pair.
- **Database per Service.** A precondition, not a companion by choice. The
  outbox table only atomically commits with the domain write because both
  live in the one database a service already owns per that pattern.
- **Shared Database (anti-pattern, listed as incompatible).** Directly at
  odds with the reasoning behind Outbox. If two services already share one
  database, the local-transaction guarantee an outbox depends on is
  meaningless as an isolation boundary, because the coupling problem Outbox
  solves for message delivery already exists, unaddressed, for the shared
  schema itself.
- **API Composition.** A read-side sibling in the same family, unrelated to
  outbox mechanically, but often deployed in the same system. Outbox moves
  write-side facts out asynchronously, while API Composition assembles
  read-side views synchronously across services at query time.

## 14. Refactoring path in and out

Introducing Transactional Outbox into a service that currently publishes
directly, with no reliability guarantee, follows a fixed order.

1. Add the outbox table to the service's own database, using the minimal
   `id, aggregatetype, aggregateid, type, payload` shape (or an equivalent),
   plus a `published_at` column for delivery state.
2. Change every code path that currently calls the broker's publish
   directly, inside a domain transaction, to instead write an outbox row in
   that same transaction, and stop calling the broker from the request
   path.
3. Stand up the relay, starting with a polling publisher for simplicity.
   this is the smallest change that closes the reliability gap, since it
   needs no new infrastructure beyond a scheduled job.
4. Point consumers at the relay's output and add idempotent handling
   (dimension 13) before removing whatever ad hoc deduplication, if any,
   existed under the old direct-publish design.
5. Once the polling relay is stable and its latency is measured, decide
   whether to keep it or migrate to a CDC-based relay, Debezium's Outbox
   Event Router or equivalent, for lower latency and lower query load. this
   step is optional and purely a latency and load optimisation, not a
   correctness fix.
6. Add the cleanup job for published rows before the table's growth becomes
   an operational problem, not after.

Removing Transactional Outbox, when a service's needs change, most commonly
happens for one of two reasons. the service adopted full Event Sourcing and
the outbox table became a redundant, narrower duplicate of the event store,
or the service was consolidated into a monolith and no longer needs
asynchronous cross-service delivery at all. In the first case, retire the
outbox table once the event store's own append log has been wired to the
same relay or an equivalent CDC pipeline, and confirm consumers see no gap
in event coverage during the cutover. In the second case, the removal is
simply deleting the table and the relay once nothing external subscribes to
its events any longer, verified by watching consumer lag drop to zero
before the table is dropped.

## 15. Testing and verification

What becomes easy to test because of this pattern is the write path.
Unit and integration tests that assert placing an order also records the
right outbox row need no broker at all. they assert against the local
database's outbox table directly, inside the same transaction boundary
the production code uses, which is fast and fully deterministic.

What becomes harder is end-to-end delivery. A test that wants to assert
the shipment service eventually receives the OrderPlaced event now depends
on the relay actually running, which means either running the real poller
(or a real CDC connector) against a real broker in an integration
environment, using a tool such as Testcontainers to stand up Postgres plus
Kafka plus a Debezium connector for the test's lifetime, or substituting an
in-memory fake relay that reads the same outbox table shape and calls a
fake broker synchronously, trading fidelity for speed.

Specific techniques worth naming.

- **Crash-injection tests for the relay**, deliberately killing the relay
  process between publishing to a fake broker and marking the row
  published, then asserting the redelivery on restart is exactly what the
  consumer-side dedup logic is built to absorb. this is the single test
  that most directly proves the pattern's own contract rather than an
  implementation detail.
- **Idempotency tests on the consumer**, feeding the exact same message
  twice and asserting the observable side effect, a row created, a balance
  changed, happens once, not twice.
- **Ordering tests keyed on aggregate id**, publishing a burst of events
  for one aggregate through concurrent relay workers or partitions and
  asserting the consumer observes them in the order they were committed,
  not the order the relay happened to read them.
- **Outbox-growth tests**, asserting the cleanup job actually removes rows
  past its retention window and never removes an unpublished row, which is
  a correctness property distinct from the growth being merely handled
  somehow.

## 16. Observability signals

- **Relay lag**, the age of the oldest unpublished outbox row, is the
  single most important metric. a healthy relay keeps this near the
  polling interval (for a poller) or near replication lag (for CDC). a
  climbing lag is the first sign of a stalled or overwhelmed relay.
- **Outbox table size and row age distribution**, watched as both an
  absolute count and a rate of growth, to catch a stalled cleanup job
  before it becomes a table-bloat incident rather than after.
- **Publish error rate and retry count**, per outbox row, to distinguish
  transient broker unavailability, self-healing, expected to clear, from a
  row that is genuinely malformed and heading toward a dead-letter state.
- **Duplicate-delivery rate at the consumer**, tracked deliberately rather
  than silently absorbed, because a rate that suddenly spikes indicates a
  relay bug, for instance a lost claim lock letting two pollers race, even
  though a low background rate is expected and normal under this pattern's
  own contract.
- **CDC connector offset lag**, when the relay variant in use is
  transaction log tailing, tracked the same way any Kafka Connect
  consumer's offset lag would be, since a connector that falls behind the
  database's WAL retention window can lose its ability to resume.
- **Per-event trace propagation**, carrying a correlation or trace id in
  the outbox row's headers/metadata column so a request can be followed
  from the original write, through the relay, to the consumer's handling of
  it, which is otherwise the hardest hop to observe in the whole system
  because it crosses from a synchronous request into an asynchronous
  pipeline.

## 17. Security and privacy implications

The outbox table is a second, durable copy of whatever data goes into event
payloads, and it typically lives inside the same database and backup set as
the primary domain data, so it inherits that database's access controls by
default rather than earning its own. Two implications follow directly. A
consumer-facing payload that includes personal data now has that data
resting, however briefly, in the outbox table as well as the domain table,
which matters for data-minimisation and retention obligations under regimes
such as GDPR. the cleanup job in dimension 15 is not only an operational
concern, it is also the mechanism by which that second copy stops existing
once it is no longer needed. Any backup or replica of the primary database
also carries the outbox table's contents, including any payload that was
never meant to be retained as long as the primary domain rows are.

The relay itself, whichever variant is chosen, needs credentials with read
access to the outbox table and publish access to the broker. a CDC-based
relay in particular typically needs broader database privileges to read
the write-ahead log, Postgres's REPLICATION role attribute, or MySQL's
REPLICATION SLAVE grant, which is a broader grant than the row-level read
a polling relay needs, and should be scoped to a dedicated connector
identity rather than reused from an application's own database user.

Nothing in this pattern changes the trust boundary of the broker or its
consumers. a message published through an outbox carries exactly the
authorisation implications a message published any other way would, so
payload-level authorisation, whether this consumer should even be allowed
to see this field, remains the payload designer's responsibility,
unaffected by how reliably the message got delivered.

## 18. References

- Chris Richardson. "Transactional outbox." microservices.io pattern
  catalog. <https://microservices.io/patterns/data/transactional-outbox.html>
  Verified 2026-08-02.
- Chris Richardson. *Microservices Patterns*. Manning, 2019.
- Gunnar Morling. "Reliable Microservices Data Exchange With the Outbox
  Pattern." Debezium blog, 19 February 2019.
  <https://debezium.io/blog/2019/02/19/reliable-microservices-data-exchange-with-the-outbox-pattern/>
  Verified 2026-08-03.
- eventuate.io. "About Eventuate Tram."
  <https://eventuate.io/abouteventuatetram.html>
  Verified 2026-08-03.
- Microsoft Learn. ".NET Microservices Architecture for Containerized .NET
  Applications, Subscribing to events."
  <https://learn.microsoft.com/en-us/dotnet/architecture/microservices/multi-container-microservice-net-applications/subscribe-events>
  Verified 2026-08-03.
- Microsoft Learn. ".NET Microservices Architecture for Containerized .NET
  Applications, Implementing event-based communication between
  microservices (integration events)."
  <https://learn.microsoft.com/en-us/dotnet/architecture/microservices/multi-container-microservice-net-applications/integration-event-based-microservice-communications>
  Verified 2026-08-03.
- Kamil Grzybek. "The Outbox Pattern."
  <https://www.kamilgrzybek.com/design/the-outbox-pattern/>
  Verified 2026-08-03.

## Code examples

The three samples below model the same shape, a domain write and an outbox
write in one atomic transaction, a relay that reads unpublished rows and
publishes them, and a consumer that deduplicates on the outbox row's own id
because the delivery contract is at-least-once, never exactly-once.

TypeScript, Python, and Go were chosen because the pattern's real weight
sits in the transaction boundary and the polling or CDC-reading loop, all
of which are equally idiomatic to express in a backend service written in
any of the three. Java, Rust, Kotlin, C#, and Swift were left out of this
entry not because the pattern does not apply there, the .NET reference
implementation named in dimension 9 is proof it does, but because three
working, compiled samples already demonstrate every mechanical decision
this pattern requires without repeating the same shape a fourth and fifth
time.

```typescript
// Transactional Outbox: an in-process store standing in for a database,
// a polling relay, and an idempotent consumer. No external drivers, so the
// shapes below are the ones a real Postgres/pg or MySQL/mysql2 adapter
// would implement; only the SQL is elided.

interface OutboxRow {
  readonly id: string;
  readonly aggregateType: string;
  readonly aggregateId: string;
  readonly eventType: string;
  readonly payload: unknown;
  readonly createdAt: number;
  publishedAt: number | null;
}

interface Order {
  readonly id: string;
  status: "placed" | "cancelled";
}

// Stands in for a single relational database connection or transaction.
class Database {
  private orders = new Map<string, Order>();
  private outbox: OutboxRow[] = [];
  private nextOutboxId = 1;

  // The one commit that must be atomic: the domain row and the outbox
  // row land together, or neither does.
  placeOrder(orderId: string, payload: unknown): void {
    if (this.orders.has(orderId)) {
      throw new Error(`order ${orderId} already exists`);
    }
    this.orders.set(orderId, { id: orderId, status: "placed" });
    this.outbox.push({
      id: String(this.nextOutboxId++),
      aggregateType: "order",
      aggregateId: orderId,
      eventType: "OrderPlaced",
      payload,
      createdAt: Date.now(),
      publishedAt: null,
    });
  }

  // The message relay reads through this, never through the domain table.
  unpublished(limit: number): OutboxRow[] {
    return this.outbox.filter((r) => r.publishedAt === null).slice(0, limit);
  }

  markPublished(id: string): void {
    const row = this.outbox.find((r) => r.id === id);
    if (row) row.publishedAt = Date.now();
  }

  order(orderId: string): Order | undefined {
    return this.orders.get(orderId);
  }
}

interface Broker {
  publish(topic: string, key: string, payload: unknown): Promise<void>;
}

// The message relay: polls the outbox, publishes, then marks the row
// published in a second, separate local transaction. A crash between
// publish and mark is the one case that produces a duplicate downstream,
// which is why the payload carries the outbox id as its dedup key.
class OutboxRelay {
  constructor(
    private readonly db: Database,
    private readonly broker: Broker,
    private readonly batchSize = 50
  ) {}

  async tick(): Promise<number> {
    const batch = this.db.unpublished(this.batchSize);
    for (const row of batch) {
      await this.broker.publish(row.aggregateType, row.aggregateId, {
        eventId: row.id,
        type: row.eventType,
        payload: row.payload,
      });
      this.db.markPublished(row.id);
    }
    return batch.length;
  }
}

// A consumer that treats at-least-once delivery as the contract and
// de-duplicates on the event id rather than assuming exactly-once.
class IdempotentConsumer {
  private seen = new Set<string>();
  private handled: string[] = [];

  handle(message: { eventId: string; type: string; payload: unknown }): void {
    if (this.seen.has(message.eventId)) return;
    this.seen.add(message.eventId);
    this.handled.push(message.eventId);
  }

  get processedCount(): number {
    return this.handled.length;
  }
}

async function main(): Promise<void> {
  const db = new Database();
  const consumer = new IdempotentConsumer();
  const broker: Broker = {
    async publish(_topic, _key, payload) {
      // Simulate a redelivery: the consumer sees the same message twice.
      consumer.handle(payload as { eventId: string; type: string; payload: unknown });
      consumer.handle(payload as { eventId: string; type: string; payload: unknown });
    },
  };
  const relay = new OutboxRelay(db, broker);

  db.placeOrder("order-1", { sku: "SKU-1", qty: 2 });
  db.placeOrder("order-2", { sku: "SKU-2", qty: 1 });

  const published = await relay.tick();
  if (published !== 2) throw new Error(`expected 2 published, got ${published}`);
  if (consumer.processedCount !== 2) {
    throw new Error(`expected 2 deduplicated events, got ${consumer.processedCount}`);
  }
  if (db.unpublished(10).length !== 0) throw new Error("outbox not drained");

  console.log("ok:", db.order("order-1")?.status, "events processed:", consumer.processedCount);
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
```

```python
"""Transactional outbox against a real SQLite database. SQLite lacks a
publish-subscribe broker, so the relay step is a plain function call, but the
transactional shape, one commit for both tables, is the real thing."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Callable


def open_store(path: str = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE orders (id TEXT PRIMARY KEY, status TEXT NOT NULL)"
    )
    conn.execute(
        """
        CREATE TABLE outbox (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aggregate_type TEXT NOT NULL,
            aggregate_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            payload TEXT NOT NULL,
            published_at TEXT
        )
        """
    )
    return conn


def place_order(conn: sqlite3.Connection, order_id: str, payload: dict) -> None:
    """The one commit that must be atomic. Domain row and outbox row land
    in the same transaction, or an exception rolls both back."""
    with conn:
        conn.execute(
            "INSERT INTO orders (id, status) VALUES (?, 'placed')", (order_id,)
        )
        conn.execute(
            """
            INSERT INTO outbox (aggregate_type, aggregate_id, event_type, payload)
            VALUES ('order', ?, 'OrderPlaced', ?)
            """,
            (order_id, json.dumps(payload)),
        )


@dataclass(frozen=True)
class OutboxMessage:
    event_id: int
    event_type: str
    payload: dict


def relay_tick(
    conn: sqlite3.Connection,
    publish: Callable[[OutboxMessage], None],
    batch_size: int = 50,
) -> int:
    """Reads unpublished rows, publishes each, marks it published in its own
    short transaction. A crash between publish and mark can redeliver, which
    is why consumers dedupe on event_id rather than assuming exactly once."""
    rows = conn.execute(
        """
        SELECT id, event_type, payload FROM outbox
        WHERE published_at IS NULL
        ORDER BY id
        LIMIT ?
        """,
        (batch_size,),
    ).fetchall()
    for row_id, event_type, payload_json in rows:
        message = OutboxMessage(row_id, event_type, json.loads(payload_json))
        publish(message)
        with conn:
            conn.execute(
                "UPDATE outbox SET published_at = datetime('now') WHERE id = ?",
                (row_id,),
            )
    return len(rows)


class IdempotentConsumer:
    def __init__(self) -> None:
        self._seen: set[int] = set()
        self.processed: list[int] = []

    def handle(self, message: OutboxMessage) -> None:
        if message.event_id in self._seen:
            return
        self._seen.add(message.event_id)
        self.processed.append(message.event_id)


def main() -> None:
    conn = open_store()
    consumer = IdempotentConsumer()

    def publish_with_redelivery(message: OutboxMessage) -> None:
        # Simulate an at-least-once broker redelivering once.
        consumer.handle(message)
        consumer.handle(message)

    place_order(conn, "order-1", {"sku": "SKU-1", "qty": 2})
    place_order(conn, "order-2", {"sku": "SKU-2", "qty": 1})

    published = relay_tick(conn, publish_with_redelivery)
    assert published == 2, f"expected 2 published rows, got {published}"
    assert len(consumer.processed) == 2, "duplicate redelivery leaked through"

    remaining = conn.execute(
        "SELECT count(*) FROM outbox WHERE published_at IS NULL"
    ).fetchone()[0]
    assert remaining == 0, "outbox not drained"

    status = conn.execute(
        "SELECT status FROM orders WHERE id = 'order-1'"
    ).fetchone()[0]
    print("ok:", status, "events processed:", len(consumer.processed))


if __name__ == "__main__":
    main()
```

```go
// Transactional outbox modeled with an in-process store standing in for a
// database transaction. A real implementation swaps outboxStore for a SQL
// table written inside the same *sql.Tx as the domain row.
package main

import (
	"errors"
	"fmt"
	"sync"
)

type OutboxRow struct {
	ID            int
	AggregateType string
	AggregateID   string
	EventType     string
	Payload       map[string]any
	Published     bool
}

type Order struct {
	ID     string
	Status string
}

// Store stands in for a single relational connection. Every write below
// happens under one mutex to model "one local transaction."
type Store struct {
	mu     sync.Mutex
	orders map[string]Order
	outbox []OutboxRow
	nextID int
}

func NewStore() *Store {
	return &Store{orders: make(map[string]Order)}
}

// PlaceOrder is the atomic commit: the domain row and the outbox row are
// written together, or neither is.
func (s *Store) PlaceOrder(orderID string, payload map[string]any) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if _, exists := s.orders[orderID]; exists {
		return errors.New("order already exists")
	}
	s.orders[orderID] = Order{ID: orderID, Status: "placed"}
	s.nextID++
	s.outbox = append(s.outbox, OutboxRow{
		ID:            s.nextID,
		AggregateType: "order",
		AggregateID:   orderID,
		EventType:     "OrderPlaced",
		Payload:       payload,
	})
	return nil
}

func (s *Store) Unpublished(limit int) []OutboxRow {
	s.mu.Lock()
	defer s.mu.Unlock()
	var out []OutboxRow
	for _, row := range s.outbox {
		if !row.Published {
			out = append(out, row)
			if len(out) == limit {
				break
			}
		}
	}
	return out
}

func (s *Store) MarkPublished(id int) {
	s.mu.Lock()
	defer s.mu.Unlock()
	for i := range s.outbox {
		if s.outbox[i].ID == id {
			s.outbox[i].Published = true
			return
		}
	}
}

type Publisher func(row OutboxRow)

// RelayTick reads a batch of unpublished rows, publishes each, then marks
// it published. A crash between the two steps can redeliver, so consumers
// dedupe on row.ID rather than trusting exactly-once delivery.
func RelayTick(s *Store, publish Publisher, batchSize int) int {
	batch := s.Unpublished(batchSize)
	for _, row := range batch {
		publish(row)
		s.MarkPublished(row.ID)
	}
	return len(batch)
}

type IdempotentConsumer struct {
	seen      map[int]bool
	processed []int
}

func NewIdempotentConsumer() *IdempotentConsumer {
	return &IdempotentConsumer{seen: make(map[int]bool)}
}

func (c *IdempotentConsumer) Handle(row OutboxRow) {
	if c.seen[row.ID] {
		return
	}
	c.seen[row.ID] = true
	c.processed = append(c.processed, row.ID)
}

func main() {
	store := NewStore()
	consumer := NewIdempotentConsumer()

	publishWithRedelivery := func(row OutboxRow) {
		// Simulate an at-least-once broker redelivering once.
		consumer.Handle(row)
		consumer.Handle(row)
	}

	if err := store.PlaceOrder("order-1", map[string]any{"sku": "SKU-1", "qty": 2}); err != nil {
		panic(err)
	}
	if err := store.PlaceOrder("order-2", map[string]any{"sku": "SKU-2", "qty": 1}); err != nil {
		panic(err)
	}

	published := RelayTick(store, publishWithRedelivery, 50)
	if published != 2 {
		panic(fmt.Sprintf("expected 2 published, got %d", published))
	}
	if len(consumer.processed) != 2 {
		panic(fmt.Sprintf("expected 2 deduplicated events, got %d", len(consumer.processed)))
	}
	if len(store.Unpublished(10)) != 0 {
		panic("outbox not drained")
	}

	fmt.Println("ok: placed events processed:", len(consumer.processed))
}
```

All three samples were run, not merely compiled. `node dist/s.js` (compiled
from the TypeScript above), `python3 s.py`, and `go run s.go` each print
`ok: placed events processed: 2`, confirming the atomic write, the polling
relay drain, and the consumer-side dedup against a simulated redelivery all
behave as described.
