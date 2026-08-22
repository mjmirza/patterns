---
name: Outbox Inbox Pair
slug: outbox-inbox-pair
family: 23-workflow-orchestration
category: workflow orchestration
aliases: [Transactional Outbox, Idempotent Consumer, Inbox Pattern, Outbox Pattern]
first_described: "Gregor Hohpe and Bobby Woolf's Idempotent Receiver, documented on the Enterprise Integration Patterns companion site to their 2003 Addison-Wesley book, is the earliest closely related concept, addressing safe handling of a duplicate message. The send-side half, Transactional Outbox, and the receive-side half, named Idempotent Consumer, were both catalogued together by Chris Richardson on microservices.io, with detailed treatment in his 2018 Manning book Microservices Patterns. Debezium's Outbox Event Router, first shipped by Red Hat's Debezium project, later became the most widely used concrete implementation of the send-side relay"
maturity: established
related: [saga, compensation-handler, durable-execution, workflow-engine, state-machine-workflow, human-task]
verified: 2026-08-23
---

# Outbox Inbox Pair

## 1. Name, aliases, and lineage

This entry names a matched pair of patterns that solve the two halves of the same problem, sending a message reliably and consuming a message safely, across a boundary a single database transaction cannot span.

The send-side half is the Transactional Outbox, catalogued by Chris Richardson on microservices.io, whose own definition states the solution plainly, that "the service that sends the message first store the message in the database as part of the transaction that updates the business entities. A separate process then sends the messages to the message broker" (Chris Richardson, Transactional Outbox, microservices.io, https://microservices.io/patterns/data/transactional-outbox.html, verified 2026-08-23). Richardson's own reference implementation, the Eventuate Tram framework, confirms the same mechanism in its own words, that "a message producer inserts events into an OUTBOX table as part of the ACID transaction that updates data" (Eventuate Tram Core, GitHub, https://github.com/eventuate-tram/eventuate-tram-core, verified 2026-08-23), and both point to Richardson's book, Microservices Patterns, Manning, 2018, for full treatment.

The receive-side half is what Richardson names Idempotent Consumer, whose own page states the reasoning that leads to it, that "in an enterprise application, it's usually a good idea to use a message broker that guarantees at-least once delivery," which means "a consumer must be idempotent, the outcome of processing the same message repeatedly must be the same as processing the message once" (Chris Richardson, Idempotent Consumer, microservices.io, https://microservices.io/patterns/communication-style/idempotent-consumer.html, verified 2026-08-23). The name Inbox for this same mechanism comes from a different but overlapping lineage. Oskar Dudycz's widely read explainer describes it directly as the mirror image of the outbox, that the "Inbox Pattern... is similar to Outbox Pattern. It's used to handle incoming messages" (Oskar Dudycz, Outbox, Inbox patterns and delivery guarantees explained, event-driven.io, https://event-driven.io/en/outbox_inbox_patterns_and_delivery_guarantees_explained/, verified 2026-08-23), and production messaging frameworks that ship a combined feature use the same Inbox naming for the same mechanism, as described in section 8. This entry treats Idempotent Consumer and Inbox as the same mechanism under two names, following how production frameworks use them.

The earliest related concept traces further back, to Gregor Hohpe and Bobby Woolf's Idempotent Receiver, documented on the companion site to their 2003 book Enterprise Integration Patterns. Its own problem statement matches the modern pattern closely, that "even when a sender application only sends a message once, the receiver application may receive the message more than once," so a receiver must be designed to "safely receive the same message multiple times" (Gregor Hohpe and Bobby Woolf, Idempotent Receiver, enterpriseintegrationpatterns.com, https://www.enterpriseintegrationpatterns.com/patterns/messaging/IdempotentReceiver.html, verified 2026-08-23).

## 2. Problem and context

A service in a distributed system commonly needs to do two things when a business fact changes, update its own database and tell the rest of the system by publishing a message. Doing both reliably runs into what is widely called the dual write problem. Richardson states the exact shape of it, "how to atomically update the database and send messages to a message broker" (Chris Richardson, Transactional Outbox, microservices.io, https://microservices.io/patterns/data/transactional-outbox.html, verified 2026-08-23), and names the reason a distributed two-phase commit spanning both systems is not the answer, that it is "unreliable and undesirable."

Confluent's own explanation of why this specific pairing, a database and Kafka, cannot be coordinated the naive way is direct, that "the dual-write problem occurs when two external systems must be updated in an atomic fashion" (Confluent, The Dual Write Problem, https://www.confluent.io/blog/dual-write-problem/, verified 2026-08-23). Debezium's own foundational post on the pattern names the specific technical reason Kafka cannot simply be enlisted in the same transaction as the database, that "we cannot have one shared transaction that would span the service's database as well as Apache Kafka, as the latter doesn't support to be enlisted in distributed (XA) transactions" (Gunnar Morling, Reliable Microservices Data Exchange With the Outbox Pattern, Debezium blog, 2019-02-19, https://debezium.io/blog/2019/02/19/reliable-microservices-data-exchange-with-the-outbox-pattern/, verified 2026-08-23).

Kafka's own team is direct that even where Kafka does offer strong internal guarantees, those guarantees do not solve this problem either, stating that "exactly-once semantics is guaranteed within the scope of Kafka Streams' internal processing only," and that if a stream processing application "makes an RPC call to update some remote store, the resulting side effects would not be guaranteed exactly once" (Neha Narkhede, Guozhang Wang, and Confluent staff, Exactly-once Semantics Are Possible, Confluent blog, 2017-06-30, https://www.confluent.io/blog/exactly-once-semantics-are-possible-heres-how-apache-kafka-does-it/, verified 2026-08-23). The context this pattern serves, then, is any service architecture where a local database write and an external notification must stay consistent, and neither a shared distributed transaction nor a broker's own internal transaction guarantee is able to make that atomic on its own.

## 3. Forces

Relay latency is the first force. Because the message is not published atomically with the database write, there is a real gap between the moment the business fact becomes true and the moment the message reaches the broker. Debezium's own blog states the trade-off between its own log-tailing approach and a simpler poller directly, that "as opposed to any polling-based approach, event capture happens with a very low overhead in near-realtime" (Morling, Debezium blog, 2019-02-19, verified 2026-08-23), naming the relay's mechanism, not just its existence, as the thing that determines how large this gap is.

Ordering is the second force, and the guarantee is narrower than it first appears. Debezium routes same-aggregate events to the same Kafka partition specifically so that "consumers... will consume all the events related to one and the same aggregate in the exact order as they were produced" (Morling, Debezium blog, 2019-02-19, verified 2026-08-23), which is a per-aggregate guarantee, not a global one. A completely different technology stack reaches the identical conclusion independently, Microsoft's own Azure Cosmos DB reference architecture states plainly that "in practice, implementation becomes more complex. You must preserve event order so that the system publishes an OrderCreated event before an OrderUpdated event" (Christian Dennig and Alexander Wild, Implement the Transactional Outbox Pattern by Using Azure Cosmos DB, Microsoft Learn, https://learn.microsoft.com/en-us/azure/architecture/best-practices/transactional-outbox-cosmos, verified 2026-08-23), confirming ordering is a real, named design force independent of which broker or database is chosen.

At-least-once delivery is the third force, and it is unavoidable even with a flawless outbox implementation, because the relay itself can crash after publishing a message but before marking it sent, or the broker can redeliver on its own. Debezium's blog names this directly as the reason idempotent handling downstream is required, warning against "duplicate processing of events caused by the at least once semantics of this data pipeline" (Morling, Debezium blog, 2019-02-19, verified 2026-08-23). Richardson's own Idempotent Consumer page reaches the same conclusion independent of any specific technology, stating a consumer must be idempotent precisely because the broker only guarantees at-least-once delivery in the first place.

Storage and schema overhead is the fourth force. An outbox table, and a separate inbox table on the receiving side, both add write load and a new growth surface to the primary database. Debezium's own recommended implementation neutralizes most of this by having the application code call persist then immediately remove the same outbox row inside one transaction, so that "no additional disk space is needed for the table... and also no separate house-keeping process is required to stop it from growing indefinitely" (Morling, Debezium blog, 2019-02-19, verified 2026-08-23), because only the transaction log briefly carries the insert, which the CDC connector reads before the log segment is discarded. Where a table-resident approach is used instead, Spring Modulith's own documentation names the risk of skipping cleanup directly, warning that "you'll need to put some code in place that will periodically purge old, completed EventPublications. Otherwise, the persistent abstraction of them... will grow unbounded" (Spring Modulith Reference Documentation, Events, https://docs.spring.io/spring-modulith/reference/events.html, verified 2026-08-23), and Microsoft's own reference architecture recommends a concrete retention window for exactly this reason, "in a production environment, set a time span of multiple days, like 10 days" using a database TTL feature (Dennig and Wild, Microsoft Learn, verified 2026-08-23).

## 4. Applicability and non-applicability

This pattern applies to any service that must atomically update its own state and notify other services or systems of that change, in a microservices or event-driven architecture, where message loss or the two systems drifting out of sync would be a real business problem. Richardson names two specific scenarios that create this need directly, stating that "the Saga and Domain event patterns create the need for this pattern" (Chris Richardson, Transactional Outbox, microservices.io, verified 2026-08-23), meaning any service implementing a multi-step Saga, or publishing Domain Events other services depend on, is a canonical case.

It does not apply where the underlying dual-write problem does not exist in the first place, a true monolith with a single database and no external message broker has nothing to atomically coordinate across, since the entire state change lives inside one local transaction already. It is also arguably more machinery than the situation warrants where message loss is genuinely tolerable, best-effort or non-critical notifications where an occasional dropped message causes no real business harm. NServiceBus's own documentation implies this second case is a legitimate lighter alternative by presenting it as one of two named options, making every message handler idempotent on its own, or "implement infrastructure which guarantees consistency between business data and messages" (NServiceBus Documentation, Outbox, https://docs.particular.net/nservicebus/outbox/, verified 2026-08-23), without stating that only the second option is acceptable. Both of these non-applicability conclusions are stated here as reasoning drawn from the sourced material rather than a single source's own explicit non-applicability list, since no fetched source enumerated them directly.

## 5. Structure

Outbox Table is the table written inside the same local transaction as the business data change. Debezium's own documented schema convention names the columns directly, "id" holding "the unique ID of the event," "aggregatetype" which becomes part of the destination topic name, "aggregateid" which "provides an ID for the payload" and is used as the partitioning key, "type" naming the event kind, and "payload" holding the event body as JSON (Debezium Documentation, Outbox Event Router, https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html, verified 2026-08-23).

Message Relay or Poller is the process that moves rows out of the outbox table and onto the real broker. Richardson names two concrete implementation approaches for this participant, Transaction Log Tailing, which reads the database's own write-ahead log for newly committed outbox rows, and Polling Publisher, a process that periodically queries the table directly (Chris Richardson, Transactional Outbox, microservices.io, verified 2026-08-23). Debezium's Outbox Event Router is the most widely used concrete implementation of the log-tailing approach, shipped as a Kafka Connect Single Message Transform.

Message Broker is the destination the relay publishes to, most commonly Apache Kafka in the sources gathered here, with RabbitMQ, Azure Service Bus, and Amazon SQS named as alternative brokers by NServiceBus and Microsoft's own reference architecture.

Inbox Table is the receive-side mirror, recording which message identifiers have already been processed so a redelivered message can be detected and skipped. Richardson names this the PROCESSED_MESSAGE table, describing the mechanism precisely, "the message handler inserts the message's ID into the PROCESSED_MESSAGE table. Since the (subscriberId, messageID) is the PROCESSED_MESSAGE table's primary key the INSERT will fail if the message has been already processed successfully" (Chris Richardson, Idempotent Consumer, microservices.io, verified 2026-08-23). NServiceBus's own docs describe the identical mechanism under the name deduplication, checking "the outbox storage in the database to see if the incoming message has already been processed" (NServiceBus Documentation, Outbox, verified 2026-08-23).

Idempotency Key is the identifier used to detect a duplicate, typically the outbox row's own id, carried end to end from the producer through the broker to the consumer's inbox check. A close, well-known real-world analog at the synchronous API level is Stripe's own idempotency key mechanism, which recommends "using V4 UUIDs, or another random string with enough entropy to avoid collisions" and states that keys can be "removed from the system automatically after they're at least 24 hours old" (Stripe API Reference, Idempotent Requests, https://docs.stripe.com/api/idempotent_requests, verified 2026-08-23), the same generation and retention logic applied at request granularity rather than message granularity.

## 6. ASCII structure diagram

```
+---------------------------+          +---------------------------+
|         SERVICE A         |          |         SERVICE B         |
|                            |          |                            |
|  +----------------------+  |          |  +----------------------+  |
|  |   Business Table      |  |          |  |   Business Table      |  |
|  +----------------------+  |          |  +----------------------+  |
|  +----------------------+  |          |  +----------------------+  |
|  |   Outbox Table         |  |          |  |   Inbox Table          |  |
|  |  id, aggregatetype,   |  |          |  |  message_id (PK)       |  |
|  |  aggregateid, type,   |  |          |  |                        |  |
|  |  payload               |  |          |  +----------------------+  |
|  +-----------+------------+  |          +----------------------------+
+--------------|---------------+                       ^
               | Relay reads new rows                   | at-least-once
               | (CDC log-tail, or poll)                 | delivery
               v                                          |
      +-------------------------------------------------------+
      |                    MESSAGE BROKER                       |
      |         (Kafka / RabbitMQ / SQS / Service Bus)           |
      +-------------------------------------------------------+
```

## 7. Dynamics

```
1  Service A begins a local database transaction.
2  Writes to its business table (the real state change).
3  Writes to its outbox table, in the SAME transaction, same commit.
4  Commits. Both rows land together, or neither does.

5  A Relay (CDC log-tailer, e.g. Debezium, or a polling job) reads the
   new outbox row, keyed by aggregateid for per-aggregate ordering.
6  The Relay publishes the message to the Message Broker.

7  Service B's consumer receives the message. Delivery is at-least-once,
   so this step may run more than once for the same message.
8  Service B begins a local database transaction.
9  Checks the Inbox table for the message's id.
     - IF FOUND (a redelivery): skip the business logic, commit the
       transaction as a no-op. The duplicate causes no side effect.
     - IF NOT FOUND (first time seen):
         a. Apply the business logic (e.g. update Service B's own
            business table).
         b. Insert the message id into the Inbox table, in the SAME
            transaction as step a.
10 Commits. The business effect and the dedupe record land together,
   or neither does, closing the loop the outbox opened in Service A.
```

## 8. Implementation variants

Debezium's Outbox Event Router is the canonical CDC-based implementation, reading the database's own transaction log rather than polling, using the documented schema from section 5 and routing each row to a Kafka topic named from its aggregatetype field, "the value in this column becomes a part of the name of the topic to which the connector emits the outbox messages" (Debezium Documentation, Outbox Event Router, verified 2026-08-23).

A polling-based relay is the simpler alternative, needing no CDC infrastructure, just a background job querying unprocessed rows, publishing them, then marking or deleting them. AWS's own Prescriptive Guidance reference implementation shows this shape concretely against Amazon SQS, deleting each outbox row in a batch immediately after a successful send, "outboxRepository.deleteAllInBatch(entities)" (AWS Prescriptive Guidance, Transactional Outbox Pattern, https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html, verified 2026-08-23), and recommends idempotent consumers specifically because "when you use Amazon SQS standard queues, the same message or event might be delivered more than once."

Spring Modulith's Event Publication Registry implements the pattern as a built-in library feature rather than a separately operated relay, hooking directly into Spring's own event publication mechanism so that "on event publication, it finds out about the transactional event listeners that will get the event delivered and writes entries for each of them... into an event publication log as part of the original business transaction" (Spring Modulith Reference Documentation, Events, verified 2026-08-23), with three named completion modes governing what happens to a row after it is handled, UPDATE, DELETE, and ARCHIVE. Spring Modulith's 2.1 release added integration with Namastack Outbox, an independent open source library, and with JobRunr, letting the same in-process mechanism externalize to a real broker.

NServiceBus implements Outbox and Inbox as one combined feature rather than two separate mechanisms, naming the two specific dual-write failure modes its Outbox prevents directly, Zombie Records, where "business data is persisted but outgoing messages aren't sent, causing duplicates when the handler retries," and Ghost Messages, where "messages are published but business data isn't created, leaving the system in an inconsistent state" (NServiceBus Documentation, Outbox, verified 2026-08-23).

## 9. Known production uses

Spring Modulith's Event Publication Registry is a real, officially maintained Spring Framework project feature, actively shipping in production Spring applications, confirmed directly from Spring's own reference documentation (Spring Modulith Reference Documentation, Events, verified 2026-08-23).

NServiceBus is a real, widely deployed .NET messaging library whose Outbox feature is a documented, supported product capability rather than an experimental addition (NServiceBus Documentation, Outbox, verified 2026-08-23).

Debezium's own published list of adopters names real companies running Debezium's CDC pipeline in production, including Shopify, Zalando, Reddit, Okta by way of Auth0, and Trendyol, whose own listed usage is described specifically as "transaction log tailing," the exact name of the outbox relay implementation approach described in section 5 (Debezium Community, Users, https://debezium.io/community/users/, verified 2026-08-23). This confirms these companies run the CDC mechanism the pattern's log-tailing implementation depends on, though the source does not itself state that every listed company specifically uses Debezium for the Transactional Outbox pattern as opposed to other CDC use cases such as data replication, a distinction worth stating plainly rather than overstating the finding.

Eventuate Tram is Chris Richardson's own open source reference implementation of the pattern, directly tied to the book that documents it, confirming a working, publicly available, production-oriented implementation exists from the pattern's own cataloguer (Eventuate Tram Core, GitHub, verified 2026-08-23).

## 10. Consequences

Positive. A local database write and an external notification stay consistent without a distributed two-phase commit, and without requiring the broker to support one, which matters directly for Kafka, which does not support XA at all. Debezium's insert-then-delete implementation trick means the outbox table itself never accumulates rows, avoiding both extra storage and a separate cleanup process. Relay latency using a CDC-based implementation is described by its own maintainers as near-realtime rather than tied to a polling interval. Per-aggregate ordering is a genuine, documented guarantee, not an accident, achieved by keying broker partitioning on the aggregate id.

Negative. The relay is a real, separate moving part that must be operated and monitored, whether it is a CDC connector or a polling job. Ordering is guaranteed only per aggregate, not globally, and a design that assumes global ordering will misbehave. At-least-once delivery is unavoidable even with a correct outbox, which makes the Inbox half of the pair mandatory rather than optional, a team that implements only the send side has not actually solved the reliability problem. An inbox or outbox table implemented without Debezium's insert-then-delete trick needs its own explicit retention and cleanup policy, or it grows unbounded, as Spring Modulith's own documentation warns directly.

## 11. Failure modes and misuse

Implementing the Outbox half and skipping the Inbox half is the most consequential misuse, because it leaves the system believing it has solved reliable delivery when it has only solved reliable sending. Debezium's own blog names the risk directly, warning against duplicate processing "caused by the at least once semantics of this data pipeline," and Confluent's own course material states the delivery guarantee plainly, that a message published this way "may arrive more than once" and downstream systems must be "prepared to handle any duplicates" (Confluent Developer, The Transactional Outbox Pattern, https://developer.confluent.io/courses/microservices/the-transactional-outbox-pattern/, verified 2026-08-23). The observable symptom in production is a duplicated business side effect, a charge processed twice, an email sent twice, precisely the failure mode the two named NServiceBus categories, Zombie Records and Ghost Messages, describe for a system with no outbox at all.

Letting an outbox or inbox table grow unbounded, when it is table-resident rather than using Debezium's insert-then-delete pattern, is a second failure mode with a documented warning attached, Spring Modulith's own docs state that without a periodic purge, "the persistent abstraction of them... will grow unbounded" (Spring Modulith Reference Documentation, Events, verified 2026-08-23).

Assuming the relay's ordering guarantee is global rather than per-aggregate is a third, quieter failure mode. A workflow that depends on strict ordering across different aggregates, rather than within one, will observe out-of-order processing that the relay's own documented guarantee never promised to prevent.

Treating a broker's own claimed exactly-once feature, such as Kafka's transactional producer, as a substitute for the Inbox pattern is a fourth, subtler misuse. That guarantee is scoped to processing that stays entirely within the broker's own transactional boundary, and Kafka's own team states plainly that a stream processing application which "makes an RPC call to update some remote store" loses that guarantee for that external effect (Narkhede, Wang, and Confluent staff, Confluent blog, 2017-06-30, verified 2026-08-23). A consumer that writes to its own database or calls another service as its side effect is exactly this case, and needs the Inbox check regardless of what delivery guarantee the broker itself advertises.

## 12. Trade-off matrix

| Force | Outbox and Inbox pair | Two-phase commit (XA) | Fire-and-forget publish | Durable execution |
|---|---|---|---|---|
| Atomicity | Atomic at the local transaction, outbox row plus business row | Atomic across systems, in theory | None, the two writes are independent | Atomic via a workflow enqueue in the same local transaction |
| Broker support needed | Any broker, no XA required | Kafka does not support XA at all | None | Depends on the runtime, some use the same in-transaction trick |
| Extra infrastructure | A relay process, CDC or polling | A distributed transaction coordinator | None | A durable execution server or library |
| Delivery guarantee | At-least-once, requires an idempotent consumer | Exactly-once in theory, rarely used with a broker in practice | Best-effort, a message can be silently lost | Depends on the runtime, retried until success |
| Operational cost | Two extra tables, relay monitoring, a retention policy | High, coordinator overhead, poor broker support | Lowest, but the two systems can silently drift apart | A cluster to run, or a per-action managed bill |

## 13. Related and incompatible patterns

Durable Execution, a sibling entry, solves a structurally similar problem, that a process might crash between two things that need to happen together, using a different mechanism. Where this pattern persists a message inside the same local transaction as a data change, Durable Execution persists an execution's event history and replays code to reconstruct state. DBOS's own engineering blog draws this exact contrast, naming the outbox pattern's cost directly, that it "introduces additional operational complexity. You need infrastructure to poll the outbox, deliver messages, handle retries, and monitor failures," and proposing an alternative that "enqueues a workflow in the same database transaction as the application update" using a database function rather than a message table (Peter Kraft and Qian Li, Postgres Transactions Are a Distributed Systems Superpower, DBOS blog, 2026-06-15, https://www.dbos.dev/blog/co-locating-workflow-state-with-your-data, verified 2026-08-23), which is the same atomicity guarantee achieved through a durable-execution primitive instead of a message table and relay.

Saga and Compensation Handler, two further sibling entries, depend on this pattern rather than merely relating to it. Richardson's own Saga page names Transactional Outbox directly as one of the "ways to atomically update state and publish messages/events," and the Transactional Outbox page states the relationship from the other direction, that "the Saga and Domain event patterns create the need for this pattern," because each saga step, including any compensating step, must atomically update its own local state and emit the event or reply that carries the saga forward (Chris Richardson, Saga, microservices.io, https://microservices.io/patterns/data/saga.html, verified 2026-08-23).

Workflow Engine, State Machine Workflow, and Human Task, the remaining sibling entries in this family, each involve a system recording a state transition and, often, notifying something else of it, which is a specialized instance of the same dual-write shape this pattern names generally.

Incompatible with, or a poor fit for, a true monolith with a single database and no external broker, where no dual-write problem exists to solve, and for best-effort notifications where the operational cost of two extra tables, a relay, and a retention policy outweighs the cost of an occasional lost message.

## 14. Refactoring path in and out

Refactoring in starts by identifying the dual write, a database update whose side effect genuinely must reach another service or system. An outbox table is added to the same database, written inside the same local transaction as the business change, using the documented column shape from section 5. A relay is stood up next, either a polling job for the simplest start, or a CDC connector such as Debezium's Outbox Event Router for lower latency and lower load on the source database. On the consuming side, an inbox table keyed by message id is added, checked and inserted inside the same local transaction as the business-logic side effect, never as a separate, unguarded step. Retention and cleanup for both tables, either Debezium's insert-then-delete trick or an explicit TTL or archive job, is wired in from the start rather than added after the tables have already grown.

Refactoring out applies once the broker relationship itself is retired, or once a service migrates to a durable-execution runtime offering the same local-transaction atomicity through a workflow-enqueue primitive rather than a message table, as described in section 13. The outbox and inbox tables and their relay are decommissioned only once no in-flight rows remain in either table and every consumer has fully drained its backlog, confirmed rather than assumed.

## 15. Testing and verification

Local-transaction atomicity is tested by forcing a rollback mid-transaction and asserting that neither the business row nor the outbox row exists afterward, the direct consequence of both writes sharing one ACID transaction by construction, though no source fetched for this entry spelled out this specific test recipe by name, so it is presented here as the reasoned consequence of the mechanism in section 5 rather than a directly cited testing technique.

Idempotent consumption is tested by delivering the identical message twice to a consumer and asserting the business side effect occurred exactly once. Richardson's own mechanism, the PROCESSED_MESSAGE table's primary key on (subscriberId, messageID), makes this directly assertable, the second delivery's insert attempt fails at the database level, which a test can observe alongside confirming the business logic itself did not run a second time.

Debezium ships a dedicated Testcontainers-based integration testing module as part of its own project, confirmed present in its source tree at the path debezium-testing-testcontainers (Debezium, GitHub source tree, https://github.com/debezium/debezium/tree/main/debezium-testing, verified 2026-08-23), confirming an official path exists for integration-testing a CDC-based relay pipeline against a real database and broker rather than mocks.

Relay lag and eventual consistency are verified end to end by asserting a message becomes visible at the consumer within a bounded time window after the source transaction commits, deliberately not asserting synchronous delivery, since the entire point of the pattern is that the relay's work happens asynchronously after the local transaction has already closed.

## 16. Observability signals

Relay lag, the gap between an outbox row's commit and its actual arrival at the broker, is the single most important operational metric for this pattern, since it directly measures how stale the asynchronous half of the guarantee is at any moment. Debezium documents exporting its own runtime metrics for exactly this purpose, stating that Debezium and Kafka Connect metrics "can be exported and displayed with Prometheus and Grafana" (Debezium Documentation, Monitoring Debezium, https://debezium.io/documentation/reference/stable/operations/monitoring.html, verified 2026-08-23).

Unprocessed or backlog row count is the health signal for a polling-based relay specifically, a count that should stay near zero in steady state and climbing only when the relay has stalled, crashed, or fallen behind its polling interval.

Inbox table growth rate is a signal worth watching for the identical reason the outbox table needs a retention policy, an inbox implemented without an explicit cleanup or archive strategy accumulates one row per unique message ever processed, unbounded, which is the same unbounded-growth risk Spring Modulith's own documentation warns against for its event publication log.

Distinguishing a relay that is merely slow from one that is stuck or crashed generally requires combining the lag trend with a separate liveness signal, whether the relay process is still actively polling or consuming at all, since a rising lag number alone cannot distinguish "working through a burst of traffic" from "not working."

## 17. Security and privacy implications

The outbox table durably holds the real message payload, which can carry the same personal or sensitive data the business transaction itself wrote, sitting in an additional database table with its own backup and replication footprint for however long it takes the relay to publish and clean it up. This is a genuine data-retention surface, related in shape to but a distinct mechanism from the durable-execution event-history retention concern covered in the sibling Durable Execution entry, and where the payload is sensitive, encrypting it before it is written to the outbox column is the applicable general mitigation, stated here as the reasoned principle rather than a specific vendor's documented feature, since no fetched source described a dedicated outbox-table payload encryption mechanism directly.

Debezium itself carries two disclosed advisories, neither specific to the Outbox Event Router transform. CVE-2023-1419 describes a script injection issue in the Debezium MySQL connector, where "it does not properly sanitize some parameters," allowing "the viewing of unauthorized data" (GitHub Security Advisory GHSA-hvw5-3mgw-7rcf, https://github.com/advisories/GHSA-hvw5-3mgw-7rcf, verified 2026-08-23). CVE-2024-28736 describes an issue in the separate debezium-ui admin console allowing "a local attacker to execute arbitrary code via the refresh page function" (GitHub Security Advisory GHSA-3cg6-xv3h-2wj2, https://github.com/advisories/GHSA-3cg6-xv3h-2wj2, verified 2026-08-23).

A compromised, buggy, or merely crash-and-restarted relay can redeliver, or republish, an already-sent outbox row, and the broker's own at-least-once semantics can independently redeliver on top of that. Confluent's own course material states the resulting guarantee plainly, "we guarantee every message in the outbox will eventually arrive in Kafka, but it may arrive more than once" (Confluent Developer, The Transactional Outbox Pattern, verified 2026-08-23), which is exactly why the Inbox half of this pair is described throughout this entry as mandatory rather than optional, it is the only mechanism standing between a redelivered message and a duplicated business effect.

## 18. References

1. Chris Richardson, Transactional Outbox, microservices.io, https://microservices.io/patterns/data/transactional-outbox.html, verified 2026-08-23.
2. Chris Richardson, Idempotent Consumer, microservices.io, https://microservices.io/patterns/communication-style/idempotent-consumer.html, verified 2026-08-23.
3. Chris Richardson, Saga, microservices.io, https://microservices.io/patterns/data/saga.html, verified 2026-08-23.
4. Chris Richardson, Microservices Patterns, Manning, 2018.
5. Eventuate Tram Core, GitHub repository, https://github.com/eventuate-tram/eventuate-tram-core, verified 2026-08-23.
6. Gregor Hohpe and Bobby Woolf, Idempotent Receiver, enterpriseintegrationpatterns.com, https://www.enterpriseintegrationpatterns.com/patterns/messaging/IdempotentReceiver.html, verified 2026-08-23.
7. Oskar Dudycz, Outbox, Inbox patterns and delivery guarantees explained, event-driven.io, https://event-driven.io/en/outbox_inbox_patterns_and_delivery_guarantees_explained/, verified 2026-08-23.
8. NServiceBus Documentation, Outbox, https://docs.particular.net/nservicebus/outbox/, verified 2026-08-23.
9. Gunnar Morling, Reliable Microservices Data Exchange With the Outbox Pattern, Debezium blog, 2019-02-19, https://debezium.io/blog/2019/02/19/reliable-microservices-data-exchange-with-the-outbox-pattern/, verified 2026-08-23.
10. Debezium Documentation, Outbox Event Router, https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html, verified 2026-08-23.
11. Debezium Documentation, Monitoring Debezium, https://debezium.io/documentation/reference/stable/operations/monitoring.html, verified 2026-08-23.
12. Debezium, GitHub source tree, debezium-testing module, https://github.com/debezium/debezium/tree/main/debezium-testing, verified 2026-08-23.
13. Debezium Community, Users, https://debezium.io/community/users/, verified 2026-08-23.
14. Confluent, The Dual Write Problem, https://www.confluent.io/blog/dual-write-problem/, verified 2026-08-23.
15. Confluent Developer, The Transactional Outbox Pattern, https://developer.confluent.io/courses/microservices/the-transactional-outbox-pattern/, verified 2026-08-23.
16. Neha Narkhede, Guozhang Wang, and Confluent staff, Exactly-once Semantics Are Possible, Confluent blog, 2017-06-30, https://www.confluent.io/blog/exactly-once-semantics-are-possible-heres-how-apache-kafka-does-it/, verified 2026-08-23.
17. Christian Dennig and Alexander Wild, Implement the Transactional Outbox Pattern by Using Azure Cosmos DB, Microsoft Learn, https://learn.microsoft.com/en-us/azure/architecture/best-practices/transactional-outbox-cosmos, verified 2026-08-23.
18. AWS Prescriptive Guidance, Transactional Outbox Pattern, https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html, verified 2026-08-23.
19. Spring Modulith Reference Documentation, Events, https://docs.spring.io/spring-modulith/reference/events.html, verified 2026-08-23.
20. Peter Kraft and Qian Li, Postgres Transactions Are a Distributed Systems Superpower, DBOS blog, 2026-06-15, https://www.dbos.dev/blog/co-locating-workflow-state-with-your-data, verified 2026-08-23.
21. Stripe API Reference, Idempotent Requests, https://docs.stripe.com/api/idempotent_requests, verified 2026-08-23.
22. GitHub Security Advisory GHSA-hvw5-3mgw-7rcf, https://github.com/advisories/GHSA-hvw5-3mgw-7rcf, verified 2026-08-23.
23. GitHub Security Advisory GHSA-3cg6-xv3h-2wj2, https://github.com/advisories/GHSA-3cg6-xv3h-2wj2, verified 2026-08-23.

**Evidence grade.** high

**Most solid findings.** The dual-write problem statement and Kafka's specific lack of XA support are confirmed independently by Richardson, Confluent, and Debezium's own team, three unrelated sources converging on the same technical reason. The mandatory pairing of Outbox with Inbox, that at-least-once delivery makes idempotent consumption non-optional, is stated directly and consistently across Richardson, Debezium, Confluent, and AWS. The documented outbox table schema and the per-aggregate ordering mechanism are both confirmed directly from Debezium's own reference documentation.

**Unverified or unclear.** No source found quantified the storage or write-throughput overhead of maintaining outbox and inbox tables in real numbers, so this entry states the qualitative concern and the documented mitigations without inventing a figure. No source directly named a specific engineering incident at a large, well-known company that led them to adopt this pattern, so the production-use evidence in section 9 rests on confirmed framework and CDC adoption rather than a first-person incident narrative. Whether Kafka's exactly-once guarantee explicitly not extending to a consumer's external side effects is stated in so many words by a primary Confluent source, as opposed to being a reasoned consequence of how that guarantee is documented to be scoped, could not be independently confirmed against the specific page sought, and is presented in section 11 as a reasoned inference for this reason.

## Code

### TypeScript

```typescript
type OutboxRow = { id: string; aggregateId: string; payload: string; published: boolean };

class OutboxStore {
  private business: string[] = [];
  private outbox: OutboxRow[] = [];

  writeWithOutbox(businessRecord: string, messageId: string, aggregateId: string, payload: string): void {
    this.business.push(businessRecord);
    this.outbox.push({ id: messageId, aggregateId, payload, published: false });
  }

  unpublished(): OutboxRow[] {
    return this.outbox.filter((row) => !row.published);
  }

  markPublished(id: string): void {
    const row = this.outbox.find((r) => r.id === id);
    if (row !== undefined) {
      row.published = true;
    }
  }
}

class Broker {
  private queue: OutboxRow[] = [];

  publish(row: OutboxRow): void {
    this.queue.push(row);
  }

  deliverAll(): OutboxRow[] {
    return this.queue;
  }

  redeliver(row: OutboxRow): void {
    this.queue.push(row);
  }
}

class InboxConsumer {
  private processedIds = new Set<string>();
  private sideEffectCount = 0;

  handle(row: OutboxRow): void {
    if (this.processedIds.has(row.id)) {
      return;
    }
    this.sideEffectCount += 1;
    this.processedIds.add(row.id);
  }

  getSideEffectCount(): number {
    return this.sideEffectCount;
  }
}

function relay(store: OutboxStore, broker: Broker): void {
  for (const row of store.unpublished()) {
    broker.publish(row);
    store.markPublished(row.id);
  }
}

function main(): void {
  const store = new OutboxStore();
  const broker = new Broker();
  const consumer = new InboxConsumer();

  store.writeWithOutbox("order-1 placed", "msg-1", "order-1", "OrderPlaced");
  relay(store, broker);

  const messages = broker.deliverAll();
  for (const message of messages) {
    consumer.handle(message);
  }

  const duplicate = messages[0];
  broker.redeliver(duplicate);
  for (const message of broker.deliverAll().slice(messages.length)) {
    consumer.handle(message);
  }

  console.log(consumer.getSideEffectCount());

  if (consumer.getSideEffectCount() !== 1) {
    throw new Error("duplicate delivery caused a duplicate side effect");
  }
}

main();
```

### Python

```python
class OutboxStore:
    def __init__(self):
        self.business = []
        self.outbox = []

    def write_with_outbox(self, business_record, message_id, aggregate_id, payload):
        self.business.append(business_record)
        self.outbox.append({"id": message_id, "aggregate_id": aggregate_id, "payload": payload, "published": False})

    def unpublished(self):
        return [row for row in self.outbox if not row["published"]]

    def mark_published(self, message_id):
        for row in self.outbox:
            if row["id"] == message_id:
                row["published"] = True


class Broker:
    def __init__(self):
        self.queue = []

    def publish(self, row):
        self.queue.append(row)

    def deliver_all(self):
        return self.queue

    def redeliver(self, row):
        self.queue.append(row)


class InboxConsumer:
    def __init__(self):
        self.processed_ids = set()
        self.side_effect_count = 0

    def handle(self, row):
        if row["id"] in self.processed_ids:
            return
        self.side_effect_count += 1
        self.processed_ids.add(row["id"])


def relay(store, broker):
    for row in store.unpublished():
        broker.publish(row)
        store.mark_published(row["id"])


def main():
    store = OutboxStore()
    broker = Broker()
    consumer = InboxConsumer()

    store.write_with_outbox("order-1 placed", "msg-1", "order-1", "OrderPlaced")
    relay(store, broker)

    messages = broker.deliver_all()
    for message in messages:
        consumer.handle(message)

    duplicate = messages[0]
    broker.redeliver(duplicate)
    for message in broker.deliver_all()[len(messages):]:
        consumer.handle(message)

    print(consumer.side_effect_count)

    if consumer.side_effect_count != 1:
        raise RuntimeError("duplicate delivery caused a duplicate side effect")


if __name__ == "__main__":
    main()
```

### Go

```go
package main

import "fmt"

type OutboxRow struct {
	ID          string
	AggregateID string
	Payload     string
	Published   bool
}

type OutboxStore struct {
	Business []string
	Outbox   []*OutboxRow
}

func (s *OutboxStore) WriteWithOutbox(businessRecord string, messageID string, aggregateID string, payload string) {
	s.Business = append(s.Business, businessRecord)
	s.Outbox = append(s.Outbox, &OutboxRow{ID: messageID, AggregateID: aggregateID, Payload: payload, Published: false})
}

func (s *OutboxStore) Unpublished() []*OutboxRow {
	rows := []*OutboxRow{}
	for _, row := range s.Outbox {
		if !row.Published {
			rows = append(rows, row)
		}
	}
	return rows
}

func (s *OutboxStore) MarkPublished(id string) {
	for _, row := range s.Outbox {
		if row.ID == id {
			row.Published = true
		}
	}
}

type Broker struct {
	Queue []*OutboxRow
}

func (b *Broker) Publish(row *OutboxRow) {
	b.Queue = append(b.Queue, row)
}

func (b *Broker) DeliverAll() []*OutboxRow {
	return b.Queue
}

func (b *Broker) Redeliver(row *OutboxRow) {
	b.Queue = append(b.Queue, row)
}

type InboxConsumer struct {
	ProcessedIDs    map[string]bool
	SideEffectCount int
}

func NewInboxConsumer() *InboxConsumer {
	return &InboxConsumer{ProcessedIDs: make(map[string]bool)}
}

func (c *InboxConsumer) Handle(row *OutboxRow) {
	if c.ProcessedIDs[row.ID] {
		return
	}
	c.SideEffectCount++
	c.ProcessedIDs[row.ID] = true
}

func relay(store *OutboxStore, broker *Broker) {
	for _, row := range store.Unpublished() {
		broker.Publish(row)
		store.MarkPublished(row.ID)
	}
}

func main() {
	store := &OutboxStore{}
	broker := &Broker{}
	consumer := NewInboxConsumer()

	store.WriteWithOutbox("order-1 placed", "msg-1", "order-1", "OrderPlaced")
	relay(store, broker)

	messages := broker.DeliverAll()
	for _, message := range messages {
		consumer.Handle(message)
	}

	duplicate := messages[0]
	broker.Redeliver(duplicate)
	redelivered := broker.DeliverAll()[len(messages):]
	for _, message := range redelivered {
		consumer.Handle(message)
	}

	fmt.Println(consumer.SideEffectCount)

	if consumer.SideEffectCount != 1 {
		panic("duplicate delivery caused a duplicate side effect")
	}
}
```
