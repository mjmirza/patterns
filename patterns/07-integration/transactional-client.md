---
name: Transactional Client
slug: transactional-client
family: 07-integration
category: Messaging
aliases: [Transacted Session, Transacted Client, Local Transaction Client]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [guaranteed-delivery, idempotent-receiver, transactional-outbox, point-to-point-channel, message-channel, dead-letter-channel, retry, circuit-breaker]
incompatible_with: [transactional-outbox]
verified: 2026-08-02
---

# Transactional Client

## 1. Name, aliases, and lineage

The canonical name is Transactional Client, one of the messaging patterns
catalogued by Gregor Hohpe and Bobby Woolf in *Enterprise Integration
Patterns. Designing, Building, and Deploying Messaging Solutions*,
Addison-Wesley, 2003, in the Messaging Systems chapter. The book states the
problem as "How can a client control its transactions with the messaging
system", and the solution as "make the client's session with the messaging
system transactional so that the client can specify transaction boundaries"
([Enterprise Integration Patterns, Transactional Client page](https://www.enterpriseintegrationpatterns.com/patterns/messaging/TransactionalClient.html),
verified 2026-08-02).

The pattern is known by several names that all point at the same mechanism
under different vendor documentation. The Jakarta Messaging specification
(the successor to JMS after the Java EE to Jakarta EE transfer) calls the
concept a **transacted session**, created by passing `true` for the
transacted flag when a `Session` is opened
([Jakarta Messaging 3.1 Session javadoc](https://jakarta.ee/specifications/messaging/3.1/apidocs/jakarta.messaging/jakarta/jms/session),
verified 2026-08-02). Microsoft's Message Queuing documentation calls the same
idea an **internal transaction**, implemented by the
`System.Messaging.MessageQueueTransaction` class
([MessageQueueTransaction class reference](https://learn.microsoft.com/en-us/dotnet/api/system.messaging.messagequeuetransaction),
verified 2026-08-02). Apache Kafka's client library calls it a
**transactional producer**, configured with a `transactional.id` and driven
through `initTransactions`, `beginTransaction`, `commitTransaction`, and
`abortTransaction`
([KafkaProducer javadoc, Kafka 4.0](https://kafka.apache.org/40/javadoc/org/apache/kafka/clients/producer/KafkaProducer.html),
verified 2026-08-02). None of these three vendors writes the exact phrase
"Transactional Client" in its own documentation. The name is the catalog's
abstraction over three independently evolved mechanisms that solve the
identical problem at the boundary between an application and a messaging
system.

This entry treats Transactional Client narrowly, as it appears in the EIP
catalog, meaning a local, single-resource transaction scoped to one
messaging session or producer. It is not the same thing as a distributed
transaction spanning a queue and a database, which the pattern explicitly
excludes and which the EIP catalog covers separately under two-phase commit
and, in later industry practice, under the Transactional Outbox pattern. The
distinction matters enough that Spring Framework's own transaction manager
javadoc states it directly for the JMS case, saying "this local strategy is
an alternative to executing JMS operations within JTA transactions... it is
not able to provide XA transactions, for example in order to share
transactions between messaging and database access. A full JTA/XA setup is
required for XA transactions"
([Spring JmsTransactionManager javadoc](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/jms/connection/JmsTransactionManager.html),
verified 2026-08-02). Everything in this entry inherits that boundary.
Transactional Client coordinates one messaging resource. It has nothing to
say about a second resource, database or otherwise, unless a two-phase
commit coordinator (an XA transaction manager) is layered on top of it, and
even then the pattern itself is only the local half of that arrangement.

## 2. Problem and context

A client sends or receives several messages that belong together as one unit
of work, and the messaging system offers no help unless the client asks for
it explicitly. In the ordinary, non-transactional mode, every `send` call
places its message on the channel the instant the call returns, and every
`receive` call removes a message from the channel the instant the call
returns. If the client crashes, throws an exception, or simply decides
partway through that the operation should not have happened, there is no
undo. Three sent messages and one received message are three sent messages
and one received message, permanently, regardless of what the client's own
logic later decides.

This becomes a concrete failure the first time a process must do more than
one messaging operation as a group. A billing service receives an order
message, computes three downstream events (an invoice line, an inventory
reservation, and a shipping request) and sends all three. If the process
crashes after sending the invoice line but before sending the other two, the
system now has a downstream inconsistency that nothing detects automatically.
Restarting the service and letting it reprocess the original order message
produces a duplicate invoice line, because the order message was already
removed from its inbound queue on the first, incomplete pass, unless the
inbound receive is bundled into the same unit of work.

Hohpe and Woolf frame the context precisely around this receive-then-act
shape, in which a client both consumes an input message and produces one or
more output messages, and the two must succeed or fail together, because a
partially applied cycle leaves the system in a state that no compensating
message will describe. The context is therefore not "any code that talks to
a queue". It is specifically code that groups a receive with one or more
sends, or groups several sends, into a single business step, where the
messaging system itself is the only participant that needs to agree on the
boundary.

A second, distinct problem context is throughput. Committing after every
single message is comparatively expensive on most messaging systems, because
a commit is a synchronization point with the broker. Batching many sends or
receives into one transaction and committing once amortizes that cost.
RabbitMQ's own documentation frames the AMQP 0-9-1 transaction class this way,
noting its behavior "is closer to providing a 'batching' feature than ACID
capabilities known from the database world"
([RabbitMQ AMQP 0-9-1 Complete Reference Guide, transactions](https://www.rabbitmq.com/docs/semantics),
verified 2026-08-02), a useful correction to the intuition that a
transactional client is primarily about correctness. In several real systems
it is used primarily to control batch size and commit frequency, with the
atomicity as a secondary, still real, benefit.

## 3. Forces

**Atomicity against throughput.** Grouping many operations into one
transaction reduces round trips to the broker and can raise throughput by a
wide margin, but it also raises the cost of a rollback, because a failure
late in a large batch discards all the work in that batch, not only the
failing operation.

**Correctness against complexity.** A transacted session is conceptually
simple from the client's point of view, begin, do work, commit or rollback,
but it pushes real complexity into the broker or client library, which must
track pending sends and pending acknowledgments per session and reconcile
them on commit, rollback, connection loss, or crash recovery.

**Local scope against distributed scope.** The pattern gives an atomic
boundary around exactly one messaging resource. The moment a business
operation also needs to touch a database, a second queue, or a call to
another service atomically, Transactional Client alone cannot express that,
and the design must either accept an eventually consistent boundary (an
outbox, an idempotent receiver, a saga) or bring in a heavier two-phase
commit coordinator. This is the sharpest force in the whole pattern, and the
one most often ignored by teams who assume "transactional" implies "spans
everything I touch in this method".

**Latency against session affinity.** A transacted session usually binds a
connection, and therefore a network path and a broker node, to one client
thread or session for the duration of the transaction. This favors
correctness and ordering but works against horizontal scale-out designs
that want any worker to handle any message at any moment, since the
transacted session itself becomes a piece of pinned state.

**Operability against silence.** A transaction that is left open, never
committed and never rolled back, holds locks or delays visibility for as
long as it stays open, and most messaging systems give the operator very
little visibility into that state beyond a slowly growing queue depth or a
stalled consumer. The pattern favors correctness for the developer at the
cost of a new operational failure mode that did not exist in the
non-transactional version.

The pattern openly gives up simplicity and horizontal elasticity in
exchange for atomicity and controlled batching, and it gives up
cross-resource guarantees entirely. Any presentation of Transactional Client
that does not name that last trade is describing it incompletely.

## 4. Applicability and non-applicability

Reach for Transactional Client when all of the following hold.

- The client performs more than one send, more than one receive, or a
  mixture of sends and receives against the same messaging resource, and
  those operations must be visible to the rest of the system as one unit or
  not at all.
- A crash between operations must not leave the system in a state where some
  of the group happened and some did not, and no other mechanism (an
  idempotent receiver plus at-least-once delivery, for instance) already
  covers that risk cheaply enough.
- The messaging system in use actually implements local transacted sessions
  or an equivalent, so the atomicity is a genuine platform guarantee and not
  a hand-rolled approximation over a system that does not support it.
- Commit frequency is a real control on throughput, and batching several
  messages per commit is worth the added rollback cost when a batch fails.

Do NOT reach for it in these situations.

- **The business operation spans more than one resource** (a queue and a
  database, or two independent queues managed by different brokers). A local
  transacted session cannot make that atomic. Use a Transactional Outbox to
  couple a database write with a reliable, eventually delivered message
  instead, or accept an idempotent, at-least-once design with compensating
  logic. Reaching for Transactional Client here produces false confidence,
  because the commit only covers the messaging half.
- **The workload is a single send with no accompanying receive or second
  send.** A lone operation is already atomic from the broker's point of
  view, so wrapping it in a transaction only adds the commit round trip for
  no added guarantee. Use ordinary auto-acknowledge or an at-most-once send
  instead.
- **The system is a cloud-native queue that does not offer true transactions
  at all**, such as Amazon SQS, which instead uses a visibility timeout that
  hides a received message from other consumers for a bounded period and
  requires the client to delete it explicitly on success
  ([Enterprise Integration Patterns, Transactional Client page, citing the
  SQS visibility-timeout approach](https://www.enterpriseintegrationpatterns.com/patterns/messaging/TransactionalClient.html),
  verified 2026-08-02). Modeling that as a transaction is a mismatch. Model it
  as a lease with an explicit delete-on-success and a redrive policy instead.
- **Extremely low, predictable per-message latency matters more than
  atomicity or batching**, for example a market-data feed where every
  message stands on its own and a slow commit cycle would introduce jitter
  no downstream consumer can tolerate.
- **The consuming code is horizontally scaled across many stateless
  workers** that must be free to pick up any message at any time, since a
  long-lived transacted session pins a connection and a thread together in a
  way that resists that elasticity.
- **A single-message consumer that already commits offsets or acknowledges
  per message** gains nothing from transactions and only adds overhead. This
  is common in simple event-driven microservices where each inbound event
  triggers exactly one outbound event and an idempotent, non-transactional
  acknowledge-after-process cycle already gives the needed guarantee.

## 5. Structure

- **Transactional Client.** The application code that opens a transacted
  session or transactional producer against a single messaging resource,
  issues one or more sends and receives inside a transaction boundary, and
  explicitly commits or rolls back. This is the participant the pattern is
  named for and the only participant with business logic.
- **Messaging Resource.** The broker, queue manager, or client-side resource
  manager that actually implements the transacted semantics, so it defers
  making sent messages visible to other consumers and defers removing
  received messages from their source channel until the client signals
  commit. Concretely this is a JMS provider's `Session`, an MSMQ
  `MessageQueueTransaction`, or a Kafka broker's transaction coordinator.
- **Transaction Boundary.** The begin and end markers the client issues,
  named `commit` and `rollback` (JMS, MSMQ) or `commitTransaction` and
  `abortTransaction` (Kafka). The boundary defines exactly which operations
  are atomic together. Anything issued before begin or after commit falls
  outside the guarantee.
- **Pending Work Buffer.** The internal, resource-side structure that holds
  sent-but-not-committed messages and marks received-but-not-committed
  messages as tentatively removed. This participant is invisible to the
  client's code but is the mechanism that makes rollback possible. A
  rollback discards the buffer's outbound entries and restores its inbound
  entries to the source channel.
- **Local Recovery Manager.** The component, usually inside the client
  library or the broker connector, responsible for what happens to an
  in-flight transaction when the connection drops or the process crashes
  before commit or rollback. Its behavior, whether the transaction silently
  rolls back, hangs until a timeout, or is recoverable on reconnect with the
  same transactional id, is the single biggest source of surprise in
  production and differs by vendor between JMS, MSMQ, and Kafka.

## 6. ASCII structure diagram

```
+-------------------------+
|   Transactional Client  |
|  (application process)  |
+------------+-------------+
             |
             | begin() / send() / receive() / commit() / rollback()
             v
+-------------------------------------------------+
|              Messaging Resource                 |
|  (broker session, MSMQ transaction, Kafka        |
|   transaction coordinator)                       |
|                                                   |
|   +-------------------------------------------+  |
|   |         Pending Work Buffer                |  |
|   |  outbound  [msg1, msg2, ...]  (not yet     |  |
|   |            visible on the destination      |  |
|   |            channel)                        |  |
|   |  inbound   [msgA]            (tentatively  |  |
|   |            removed from the source          |  |
|   |            channel, restorable on           |  |
|   |            rollback)                        |  |
|   +-------------------------------------------+  |
|                                                   |
|   +-------------------------------------------+  |
|   |         Local Recovery Manager              |  |
|   |  handles connection loss, crash before       |  |
|   |  commit, transaction timeout                 |  |
|   +-------------------------------------------+  |
+-------------------+---------------------+---------+
                     |                     |
                     v                     v
       +--------------------+   +----------------------+
       |  Source Channel     |   |  Destination Channel |
       |  (input queue or    |   |  (output queue or    |
       |   topic partition)  |   |   topic partition)   |
       +--------------------+   +----------------------+
```

## 7. Dynamics

The healthy path groups one or more sends and receives into an atomic
commit. The Jakarta Messaging specification states this directly for the
receive side, saying "when a transaction commits, its atomic unit of input
is acknowledged and its associated atomic unit of output is sent"
([Jakarta Messaging 3.1 Session javadoc](https://jakarta.ee/specifications/messaging/3.1/apidocs/jakarta.messaging/jakarta/jms/session),
verified 2026-08-02).

```
Client            Messaging Resource      Source Channel   Destination Channel
  |                       |                     |                  |
  |--begin transaction--->|                     |                  |
  |                       |                     |                  |
  |--receive()----------->|--tentative pop----->|                  |
  |<--message A-----------|                     |                  |
  |                       |                     |                  |
  |--send(derived msg)--->|                     |                  |
  |                       |--buffer, not yet--------------------->  |
  |                       |  visible                                |
  |                       |                     |                  |
  |--commit()------------>|                     |                  |
  |                       |--finalize pop from source------------->|
  |                       |--publish buffered send----------------->
  |<--ack----------------|                     |                  |
```

The failure path is the point of the pattern. Whatever happened between
begin and rollback is fully undone with respect to the messaging resource,
which is the guarantee ordinary non-transacted sends and receives cannot
give.

```
Client            Messaging Resource      Source Channel   Destination Channel
  |                       |                     |                  |
  |--begin transaction--->|                     |                  |
  |--receive()----------->|--tentative pop----->|                  |
  |<--message A-----------|                     |                  |
  |                       |                     |                  |
  |--send(derived msg)--->|                     |                  |
  |                       |--buffer, not yet--------------------->  |
  |                       |  visible                                |
  |                       |                     |                  |
  |  (client logic throws an exception)         |                  |
  |                       |                     |                  |
  |--rollback()---------->|                     |                  |
  |                       |--restore message A to source---------->|
  |                       |--discard buffered send                 |
  |<--rolled back--------|                     |                  |
```

A third dynamic, unique to this pattern and rarely drawn, is what happens
when the client never calls commit or rollback at all, because the process
crashed, hung, or was killed. The Jakarta Messaging specification's rollback
description covers the crash-recovery half indirectly, stating that a
rollback "destroys sent messages" and "automatically recovers the session's
input"
([Jakarta Messaging 3.1 Session javadoc](https://jakarta.ee/specifications/messaging/3.1/apidocs/jakarta.messaging/jakarta/jms/session),
verified 2026-08-02). Most providers apply the same recovery when a
connection drops mid-transaction, so an abandoned transaction usually
resolves to an automatic rollback once the broker detects the dead
connection, rather than hanging forever. Kafka is the sharper counter
example. Because its `transactional.id` is designed to survive across
producer restarts, stated as "the purpose of the transactional.id is to
enable transaction recovery across multiple sessions of a single producer
instance"
([KafkaProducer javadoc, Kafka 4.0](https://kafka.apache.org/40/javadoc/org/apache/kafka/clients/producer/KafkaProducer.html),
verified 2026-08-02), a new producer instance that reuses the same
transactional id will fence off the previous, possibly still-open
transaction and force it to a terminal state before proceeding, rather than
silently rolling it back the instant the socket closes. The two systems
solve the same problem, an abandoned transaction, with materially different
timing and operational behavior, and that difference is exactly the kind of
thing dimension 11 exists to name.

## 8. Implementation variants

- **JMS or Jakarta Messaging transacted session.** `connection.createSession(true, Session.SESSION_TRANSACTED)`
  produces a `Session` whose acknowledgment mode is implicit. `commit()`
  "commits all messages done in this transaction and releases any locks
  currently held", and `rollback()` "rolls back any messages done in this
  transaction and releases any locks currently held"
  ([Jakarta Messaging 3.1 Session javadoc](https://jakarta.ee/specifications/messaging/3.1/apidocs/jakarta.messaging/jakarta/jms/session),
  verified 2026-08-02). This is the variant the EIP catalog's own diagrams are
  drawn from, and it is a purely local, single-resource transaction unless
  wrapped by an outer JTA `UserTransaction`.
- **MSMQ internal transaction.** `System.Messaging.MessageQueueTransaction`
  is `Begin()`, then passed into overloads of `MessageQueue.Send` and
  `MessageQueue.Receive`, then `Commit()` or `Abort()`. The documentation is
  explicit that "messages sent to transactional queues are removed if the
  transaction is committed" and "messages received from transactional queues
  are returned to the queue if the transaction is rolled back", and that
  passing a transaction object to a non-transactional queue throws a
  "Wrong Transaction Usage" exception
  ([MessageQueueTransaction class reference](https://learn.microsoft.com/en-us/dotnet/api/system.messaging.messagequeuetransaction),
  verified 2026-08-02). MSMQ also supports an implicit transactional client
  mode, `MessageQueueTransactionType.Automatic`, which participates in an
  ambient `System.Transactions` scope instead of an explicit local object,
  the .NET counterpart to layering JTA over JMS.
- **AMQP 0-9-1 transactions (RabbitMQ).** `tx.select` opens a transacted
  channel, `tx.commit` and `tx.rollback` close it. RabbitMQ's own guidance
  frames this class as closer to a batching feature than to database-grade
  ACID
  ([RabbitMQ AMQP 0-9-1 Complete Reference Guide, transactions](https://www.rabbitmq.com/docs/semantics),
  verified 2026-08-02), and in practice most RabbitMQ producers today prefer
  publisher confirms, an asynchronous, per-message acknowledgment mechanism
  that is not the Transactional Client pattern at all, precisely because
  full channel transactions serialize every commit through the broker and
  cap throughput.
- **Kafka transactional producer.** `initTransactions()` must run once before
  any other transactional call. `beginTransaction()` opens a boundary.
  `commitTransaction()` "flushes any unsent records before actually
  committing". `abortTransaction()` discards any unflushed records, and
  `sendOffsetsToTransaction()` folds a consumer group's offset commit into
  the same transaction as the producer's sends, which is how Kafka expresses
  the read-process-write cycle atomically across a source topic and one or
  more destination topics, stated directly as "the transactional producer
  allows an application to send messages to multiple partitions (and
  topics!) atomically"
  ([KafkaProducer javadoc, Kafka 4.0](https://kafka.apache.org/40/javadoc/org/apache/kafka/clients/producer/KafkaProducer.html),
  verified 2026-08-02). This is the most capable variant in the family,
  because it extends the atomic boundary across multiple destination
  partitions and topics, not merely multiple messages to one destination,
  while remaining a single logical resource (the Kafka cluster) rather than
  a true cross-technology XA transaction.
- **Framework-managed transacted session (Spring).** `JmsTransactionManager`
  implements Spring's `PlatformTransactionManager` for a single JMS
  `ConnectionFactory`, binding a thread-local Session so ordinary
  `@Transactional` code and `JmsTemplate` participate automatically, while
  the javadoc is explicit that it "is not able to provide XA transactions...
  a full JTA/XA setup is required" for cross-resource atomicity
  ([Spring JmsTransactionManager javadoc](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/jms/connection/JmsTransactionManager.html),
  verified 2026-08-02). This variant is worth naming separately because it
  is the shape most application developers actually meet, an annotation and
  a managed transaction, with the raw session object never touched by hand.
- **Lease-based imitation, not a true transaction (Amazon SQS).** SQS uses a
  visibility timeout, during which a received message is hidden from other
  consumers, and the client must call `DeleteMessage` explicitly on success.
  No message is left un-produced automatically on failure the way a real
  rollback would, because SQS producers are not transactional against SQS
  consumers at all. This variant is included precisely to mark the boundary
  of the pattern, systems that look similar on the surface but do not give
  the atomicity Transactional Client promises.

## 9. Known production uses

1. **Apache Kafka's exactly-once semantics pipeline**, where the
   transactional producer combined with `read_committed` isolation on
   consumers is the mechanism Confluent and the Kafka project itself
   document as the basis for exactly-once stream processing across
   read-process-write cycles, driven by `initTransactions`,
   `beginTransaction`, `sendOffsetsToTransaction`, and
   `commitTransaction` on the `KafkaProducer` client
   ([KafkaProducer javadoc, Kafka 4.0](https://kafka.apache.org/40/javadoc/org/apache/kafka/clients/producer/KafkaProducer.html),
   verified 2026-08-02).
2. **Spring Framework's JMS integration**, where `JmsTransactionManager` and
   `JmsTemplate` give every Spring application built against a JMS broker
   (ActiveMQ, IBM MQ, Solace, and other JMS-compliant providers) a
   ready-made Transactional Client without hand-written session management,
   documented plainly as the local, single-resource alternative to a
   JTA/XA setup
   ([Spring JmsTransactionManager javadoc](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/jms/connection/JmsTransactionManager.html),
   verified 2026-08-02).
3. **Microsoft Message Queuing (MSMQ)**, where `System.Messaging.MessageQueueTransaction`
   has been the documented mechanism for transacted sends and receives
   against transactional MSMQ queues across every .NET Framework release
   from 1.1 through 4.8.1, used by NServiceBus and MassTransit as one of
   their supported transports specifically because it gives local
   atomicity without a full DTC (Distributed Transaction Coordinator)
   escalation when the operation stays inside MSMQ alone
   ([MessageQueueTransaction class reference](https://learn.microsoft.com/en-us/dotnet/api/system.messaging.messagequeuetransaction),
   verified 2026-08-02).
4. **The Jakarta Messaging (formerly JMS) specification itself**, which
   defines transacted sessions as a normative part of every conformant
   implementation, so every Jakarta EE and Java EE application server
   (WildFly, WebLogic, WebSphere, Payara) and every standalone broker with a
   JMS client (Apache ActiveMQ, IBM MQ, Solace PubSub+) ships this pattern
   as a first-class API surface rather than an add-on
   ([Jakarta Messaging 3.1 Session javadoc](https://jakarta.ee/specifications/messaging/3.1/apidocs/jakarta.messaging/jakarta/jms/session),
   verified 2026-08-02).

## 10. Consequences

Positive.

- The client gets a genuine atomic boundary around a group of sends and
  receives against one messaging resource, closing off the specific class
  of bug where a crash between two related operations leaves the system
  half updated.
- Batching several operations behind one commit reduces the number of
  network round trips to the broker, which is a real throughput gain on
  systems whose commit is a synchronous round trip.
- The failure and recovery story becomes uniform. A client that dies before
  commit produces the same observable effect, nothing happened, whether it
  died after the first operation or the last, which simplifies reasoning
  about retries and idempotency at the layer above.
- Where the underlying system supports it (notably Kafka's
  `sendOffsetsToTransaction`), the atomic boundary can span the consumer
  offset commit and multiple producer sends across multiple destinations,
  which is considerably stronger than what a single non-transacted
  acknowledge-then-produce cycle can offer.

Negative.

- The atomicity is strictly local to one messaging resource. Any code that
  treats it as covering a database write in the same method is wrong, and
  that mistake is not caught by a compiler or a type system, only by an
  incident.
- A long-running transaction holds resources open (locks on received
  messages, buffered unsent messages) for as long as the client's business
  logic takes to run, which couples messaging system health to unrelated
  application latency.
- Rollback discards the entire batch, not only the operation that failed,
  so a large batch size traded for throughput directly raises the blast
  radius of any single failure inside that batch.
- A transacted session or transactional producer usually pins a
  connection, and often a broker partition or node, to a thread for the
  duration of the transaction, which works against designs that want
  stateless, freely load-balanced workers.
- The pattern adds an entire new failure surface, the abandoned transaction,
  whose resolution timing (immediate rollback on disconnect versus a fencing
  wait on reconnect) differs by vendor and must be understood per system
  rather than assumed from experience with a different one.

## 11. Failure modes and misuse

**Symptom.** Two records land in a downstream database when only one was
expected, and both carry data that traces back to the same source event.
**Cause.** The team believed the transacted messaging session also covered a
database write inside the same business method, so they never added
idempotency to the database write, and a redelivery after a broker-side
timeout replayed the messaging transaction while the earlier, uncommitted
database write had already partially executed and was rolled back by the
database, but the compensating logic assumed the messaging commit was the
only thing that mattered.
**Fix.** Treat the messaging transaction and the database transaction as two
independent local transactions from the start, and add either an idempotency
key on the database write or a Transactional Outbox so the database is the
single source of truth for what has actually happened, with messages
produced from it reliably rather than assumed atomic with it.

**Symptom.** Consumer lag on a topic climbs steadily even though the
consumer process is alive and appears to be doing work, and restarting the
consumer temporarily clears the backlog before it returns.
**Cause.** A code path inside the transaction boundary occasionally throws
an exception that is caught somewhere above the messaging call and logged,
but the enclosing catch block never calls `rollback()` (or, in the Kafka case,
`abortTransaction()`), so the session is left open, its buffered sends never
flush, and its receives are never finalized, silently starving the
transaction until an idle timeout eventually forces the broker to open it
back up.
**Fix.** Wrap every begin with a construct that guarantees exactly one of
commit or rollback runs, a try-with-resources or try-finally in Java, a
`using` block in C#, or an explicit try, except, else block in Python that
commits in the else clause and rolls back in the except clause, never
leaving a code path where neither call happens.

**Symptom.** A migration from a queue-per-consumer topology to a shared,
horizontally scaled consumer group causes throughput to fall rather than
rise, and profiling shows most workers idle while one worker is saturated.
**Cause.** The transacted session was opened once and reused across the
worker's lifetime instead of being scoped per unit of work, and because a
transacted session pins its underlying connection, the client library's
connection pool ends up funneling most traffic through whichever connection
happens to hold the long-lived transaction, defeating the pool's ability to
spread load.
**Fix.** Scope the transaction to the smallest sensible unit of work (one
message or one small batch), commit promptly, and let the connection or
session be returned to the pool between transactions rather than held for
the life of the worker.

**Symptom.** A load test that commits after every single message shows far
lower throughput than the same team's earlier benchmark of the broker's
theoretical maximum, and adding hardware does not close the gap.
**Cause.** Committing per message turns every message into a synchronous
round trip to the broker, and RabbitMQ's own documentation calls this shape
out directly, describing the AMQP transaction class as closer to a batching
feature than to ACID and implying the intended usage pattern is batches of
messages per commit, not one
([RabbitMQ AMQP 0-9-1 Complete Reference Guide, transactions](https://www.rabbitmq.com/docs/semantics),
verified 2026-08-02).
**Fix.** Batch a bounded number of messages per transaction, chosen to
balance the throughput gain against the raised rollback blast radius from
consequence 10, and, on brokers where it is available and sufficient,
consider whether a lighter mechanism such as publisher confirms actually
fits the requirement better than a full transaction.

**Symptom.** A Kafka producer restarts after a crash and every subsequent
`send()` call throws a `ProducerFencedException`, even though the new
process instance has never called any transactional method before.
**Cause.** The restarted process reused the same `transactional.id` as the
crashed instance, and Kafka's transaction coordinator, on seeing a new
producer registration replace an older one for that id, correctly fences off the older,
possibly still-open transaction by rejecting any further writes from it,
because "the purpose of the transactional.id is to enable transaction
recovery across multiple sessions of a single producer instance"
([KafkaProducer javadoc, Kafka 4.0](https://kafka.apache.org/40/javadoc/org/apache/kafka/clients/producer/KafkaProducer.html),
verified 2026-08-02), and the developer misread the fencing of the old
instance as a bug in the new one rather than the intended recovery
mechanism working as designed.
**Fix.** Treat a `ProducerFencedException` as an expected, terminal signal
to the fenced instance that a newer instance has taken over, log it, and let
that process exit cleanly rather than retrying, since retrying with a fenced
producer cannot succeed by design.

## 12. Trade-off matrix

| Force | Transactional Client | Idempotent Receiver (at-least-once, no local tx) | Transactional Outbox |
|---|---|---|---|
| Scope of the atomic boundary | One messaging resource only | None, relies on the consumer tolerating duplicates | The producing service's own database, with delivery decoupled |
| Cross-resource (queue plus database) safety | Not provided, a common source of the misuse in dimension 11 | Achieved indirectly, by making duplicate delivery harmless | Achieved directly, by writing the message and the business state in one local database transaction |
| Throughput at small batch sizes | Lower, each commit is a broker round trip | Higher, no commit round trip beyond normal acknowledgment | Comparable to a normal database write, a separate relay process handles publishing |
| Rollback blast radius | The whole in-flight batch is discarded | Not applicable, there is nothing to roll back, only reprocessing | Limited to the local database transaction, the outbox relay retries independently |
| Operational complexity | Moderate, needs monitoring for abandoned or long-held transactions | Low, needs a durable deduplication key instead | Higher, needs a relay or CDC process to publish outbox rows |
| Best fit | Multiple sends and receives against one broker that must succeed or fail together | Simple, single-message, at-least-once processing where duplicates are cheap to detect | Any workflow where a database write and a resulting message must never disagree |

The three alternatives are not mutually exclusive in a real system.
Transactional Outbox usually still uses ordinary, non-transacted sends for
the relay step, and many production pipelines combine an Idempotent Receiver
on the inbound side with a Transactional Client on the outbound side,
accepting duplicate inputs gracefully while keeping the group of outputs
produced from any single processing pass atomic with respect to each other.

## 13. Related and incompatible patterns

**Guaranteed Delivery** is a stronger, orthogonal guarantee about durability
(a message survives a broker restart) that Transactional Client does not by
itself provide. A transacted session on a non-durable queue is atomic but
still loses messages on broker failure, so the two patterns are usually
combined rather than substituted for each other.

**Idempotent Receiver** is the pattern most often reached for instead of
Transactional Client when the cost of a local transaction is not justified,
because at-least-once delivery plus a deduplication key achieves a similar
practical outcome, no double-processing, without the connection pinning and
operational overhead described in dimension 10.

**Transactional Outbox** is listed as incompatible in the sense that it
solves the problem Transactional Client is most often mistakenly believed
to solve, atomicity between a database write and a message. Where a team
needs that specific guarantee, reaching for Transactional Client instead of
Transactional Outbox is the misuse described first in dimension 11, so the
two patterns compete for the same slot in a design rather than composing.
Picking one usually means the other is not needed for that particular
boundary.

**Dead Letter Channel** composes naturally downstream of a Transactional
Client. When a rollback happens repeatedly for the same message because the
client's processing logic keeps failing, a poison-message loop can form
unless a maximum-redelivery policy routes the offending message to a dead
letter channel instead of retrying it inside the same transaction
indefinitely.

**Retry** and **Circuit Breaker** usually wrap the business logic that
runs between begin and commit, not the transaction mechanics themselves.
When that inner logic calls an external, non-transactional dependency (an
HTTP API, for instance) and that call fails, the correct response is
usually to roll back the messaging transaction and let a Retry policy
outside the messaging system decide whether and when to try the whole unit
of work again, rather than retrying the external call while the messaging
transaction stays open.

**Point-to-Point Channel** and **Message Channel** are the structural
patterns that Transactional Client operates against. The transaction is a
property of the client's session with a channel, not a property of the
channel itself, which is why a single physical queue can serve both
transacted and non-transacted clients concurrently, as the EIP catalog notes
directly for mixed explicit and implicit transactional clients on the same
channel
([Enterprise Integration Patterns, Transactional Client page](https://www.enterpriseintegrationpatterns.com/patterns/messaging/TransactionalClient.html),
verified 2026-08-02).

## 14. Refactoring path in and out

Introducing the pattern into code that currently uses ordinary,
non-transacted sends and receives follows a sequence that keeps the system
running throughout.

1. Identify the smallest group of sends and receives against one messaging
   resource that must succeed or fail together as a unit. Resist the urge to
   include unrelated operations only because they happen to run in the same
   method.
2. Confirm the messaging resource actually supports local transactions and
   that the current client library exposes them (a transacted session
   constructor, a `transactional.id` configuration, a transaction object
   passed into send and receive calls).
3. Change the session or producer construction to request a transacted
   resource, and open a transaction at the start of the identified group,
   before the first send or receive in that group.
4. Move every send and receive in the identified group so each one runs
   against the transacted resource rather than a separate, non-transacted
   one. A common mistake at this step is to open the transaction but keep
   using a different, older connection for one of the calls, which silently
   excludes that call from the boundary.
5. Wrap the group in a construct that guarantees exactly one terminal call,
   commit on success, rollback on any exception, using the language's
   resource-management idiom rather than manual bookkeeping, following the
   fix described for the abandoned-transaction failure mode in dimension 11.
6. Add monitoring for transaction duration and for the abandoned-transaction
   failure mode before rolling the change out to production traffic, since
   this failure mode has no equivalent in the non-transacted version of the
   code and is easy to miss until it happens under load.
7. Roll out behind a feature flag or a canary if the messaging platform and
   deployment tooling support it, watching commit latency and rollback rate
   as the primary new signals, then remove the flag once both are stable.

Removing the pattern, when a group's atomicity requirement turns out not to
be real, or when the operational cost (connection pinning, abandoned
transactions) outweighs the benefit for that particular workload, follows
the reverse path.

1. Confirm, with production evidence rather than assumption, that no
   incident or data inconsistency has ever depended on the atomicity this
   transaction provides. Check the dead letter channel and any
   reconciliation reports for the workload first.
2. Replace the transacted session or transactional producer with an
   ordinary one, and change each send and receive call to use the
   non-transacted API directly, removing the begin, commit, and rollback
   calls.
3. If the original motivation was correctness rather than throughput, add
   an Idempotent Receiver (a deduplication key derived from the source
   message) before removing the transaction, so the correctness guarantee
   is replaced rather than simply dropped.
4. Reduce or remove any connection-pinning workarounds that existed only to
   support the long-lived transacted session, and confirm the connection
   pool now spreads load across workers again.
5. Watch the same commit-latency and rollback-rate signals from the
   introduction path in reverse, expecting them to disappear, along with a
   corresponding rise in ordinary send and receive throughput.

## 15. Testing and verification

Unit testing the business logic that runs between begin and commit is
straightforward and is, in fact, one of the pattern's quieter benefits. The
logic can be tested as a plain function that takes an inbound message and
returns zero or more outbound messages, with the transaction mechanics
mocked out entirely, because the transaction boundary is a concern of the
surrounding infrastructure code, not of the business rule itself.

Testing the transaction mechanics themselves requires a different
technique, because the interesting behavior is precisely what happens when
something fails partway through, and a happy-path test cannot exercise it.
The reliable approach is to use an in-memory or embedded broker (ActiveMQ's
embedded broker, an in-memory JMS provider, or a test container running the
real broker under Docker) and write a test that deliberately throws an
exception after the first of two sends inside a transaction, then asserts
that neither send is visible on the destination channel, which is the
direct test of the atomicity guarantee. A second, equally important test
asserts the inverse case. After a successful commit, both sends are visible,
proving the transaction did not silently swallow one of them.

A test double that merely records that commit was called, without modeling
the buffering and visibility rules, is not sufficient, because it cannot
catch the class of bug described in dimension 11 where a code path
accidentally skips both commit and rollback. That specific bug is only
caught by a test that asserts, after the exception-throwing scenario, that
the destination channel remains empty and the source channel's message
becomes visible to other consumers again after the transaction's timeout,
which requires a broker or broker simulation that actually implements the
pending work buffer described in dimension 5, not a bare mock.

Load and fault-injection testing should specifically target the abandoned-transaction
failure mode. Start a transaction, hold it open, and kill the client
process without calling commit or rollback, then measure how long the
broker takes to make the held messages available again, since that
recovery time is a concrete, vendor-specific number that operators need to
know before an incident, not during one.

## 16. Observability signals

The most valuable signal is transaction duration, the elapsed time between
begin and the terminal commit or rollback call, tracked as a histogram per
client or per consumer group. A healthy system shows a tight, low
distribution. A distribution with a growing tail points at business logic
that is doing more work inside the transaction boundary than it should,
which directly raises the operational risk described in dimension 10.

Rollback rate, the fraction of opened transactions that end in rollback
rather than commit, is the second core signal. A near-zero rate that
suddenly rises is usually a sign of a new bug or a downstream dependency
failure inside the transaction body. A rate that has always been high is a
sign the transaction boundary is drawn too widely, wrapping optional or
retryable work inside a boundary meant only for the messaging operations
themselves.

Abandoned or timed-out transaction count deserves its own explicit metric
rather than being inferred from the rollback rate, because most messaging
systems distinguish an explicit client-initiated rollback from an implicit,
broker-initiated recovery after a connection drop or a transaction-idle
timeout, and the two point at different root causes, one in the client's
exception handling and one in the client's health.

Commit batch size, the number of messages included in each committed
transaction, tracked alongside commit latency, tells an operator whether the
throughput-versus-blast-radius trade-off from dimension 3 is tuned
correctly. A size that is far smaller than intended usually indicates the
transaction boundary is being reset more often than expected, defeating the
batching benefit that motivated using the pattern in the first place.

For Kafka specifically, the `transactional.id` and the producer
registration number associated with it are worth surfacing on any dashboard that also shows
`ProducerFencedException` occurrences, since a spike in fencing exceptions
that is not tied to an intended deployment or restart is a strong signal of
an operational problem, such as two instances of the same logical producer
running concurrently, rather than a code defect.

## 17. Security and privacy implications

The transaction boundary itself does not encrypt, authenticate, or
authorize anything. It is a coordination mechanism layered on top of
whatever transport security and access control the underlying messaging
resource already provides, and it inherits that resource's posture without
changing it.

The pattern does introduce one implication worth naming plainly. Because
a transacted session buffers outbound messages before they become visible,
those messages exist, in plaintext or in whatever encoding the client
produced, inside the client process's or broker's memory for the duration
of the transaction, which can extend the window during which sensitive
payload data sits in an intermediate, less-audited location compared with a
non-transacted send that is handed to the broker and forgotten immediately.
For long-running transactions holding sensitive payloads, this argues for
keeping the transaction boundary as short as dimension 3's forces already
recommend for operational reasons, with data sensitivity as a second,
independent reason to do the same thing.

The abandoned-transaction failure mode described in dimension 11 also has a
privacy-adjacent consequence that deserves mention. A message held inside a pending
work buffer that is eventually rolled back or later made available again
after a timeout was, for a period, invisible to legitimate consumers and to
any audit trail that only observes committed, visible messages, which can
complicate incident forensics if the question under investigation is
whether this specific message ever left the source system, since the honest
answer during that window is genuinely ambiguous until the transaction
resolves one way or the other.

Where a Transactional Client is used to move regulated data (personal data
under GDPR, payment data under PCI DSS), the transaction's atomicity should
not be mistaken for an access control or retention guarantee. Messages held
in the pending work buffer are still subject to the same retention and
access rules as any other message on the resource, and a security review of
the messaging platform's own encryption at rest and access control is the
correct place to address those requirements, independent of whether the
client happens to use a transacted session.

## 18. References

- Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns. Designing,
  Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003,
  Messaging Systems chapter, Transactional Client.
- [Enterprise Integration Patterns, Transactional Client page](https://www.enterpriseintegrationpatterns.com/patterns/messaging/TransactionalClient.html),
  verified 2026-08-02.
- [Jakarta Messaging 3.1, Session interface javadoc](https://jakarta.ee/specifications/messaging/3.1/apidocs/jakarta.messaging/jakarta/jms/session),
  verified 2026-08-02.
- [MessageQueueTransaction class reference, .NET API documentation, Microsoft Learn](https://learn.microsoft.com/en-us/dotnet/api/system.messaging.messagequeuetransaction),
  verified 2026-08-02.
- [KafkaProducer javadoc, Apache Kafka 4.0](https://kafka.apache.org/40/javadoc/org/apache/kafka/clients/producer/KafkaProducer.html),
  verified 2026-08-02.
- [Spring JmsTransactionManager javadoc, Spring Framework](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/jms/connection/JmsTransactionManager.html),
  verified 2026-08-02.
- [RabbitMQ AMQP 0-9-1 Complete Reference Guide, transactions section](https://www.rabbitmq.com/docs/semantics),
  verified 2026-08-02.

## Code examples

The samples below model the pattern's mechanics directly, an in-process
messaging resource with a pending work buffer, begin, send, receive,
commit, and rollback, rather than depending on a live broker or a
network-fetched client library, so each one compiles and runs with only the
standard library. The dimension 8 citations above show the exact production
API each language's real client library exposes. These samples make the
same contract visible without external dependencies.

### Java

```java
import java.util.ArrayList;
import java.util.LinkedList;
import java.util.List;
import java.util.Queue;

public class TransactionalQueueClient {

    static final class Broker {
        private final Queue<String> sourceChannel = new LinkedList<>();
        private final Queue<String> destinationChannel = new LinkedList<>();

        Broker(String... seedMessages) {
            for (String m : seedMessages) {
                sourceChannel.add(m);
            }
        }
    }

    static final class TransactedSession {
        private final Broker broker;
        private final List<String> pendingOutbound = new ArrayList<>();
        private final List<String> tentativelyRemoved = new ArrayList<>();
        private boolean open = false;

        TransactedSession(Broker broker) {
            this.broker = broker;
        }

        void begin() {
            if (open) {
                throw new IllegalStateException("transaction already open");
            }
            open = true;
        }

        String receive() {
            requireOpen();
            String msg = broker.sourceChannel.poll();
            if (msg != null) {
                tentativelyRemoved.add(msg);
            }
            return msg;
        }

        void send(String message) {
            requireOpen();
            pendingOutbound.add(message);
        }

        void commit() {
            requireOpen();
            broker.destinationChannel.addAll(pendingOutbound);
            pendingOutbound.clear();
            tentativelyRemoved.clear();
            open = false;
        }

        void rollback() {
            requireOpen();
            for (int i = tentativelyRemoved.size() - 1; i >= 0; i--) {
                ((LinkedList<String>) broker.sourceChannel).addFirst(tentativelyRemoved.get(i));
            }
            tentativelyRemoved.clear();
            pendingOutbound.clear();
            open = false;
        }

        private void requireOpen() {
            if (!open) {
                throw new IllegalStateException("no open transaction");
            }
        }
    }

    public static void main(String[] args) {
        Broker broker = new Broker("order-1", "order-2");

        TransactedSession failing = new TransactedSession(broker);
        failing.begin();
        String order = failing.receive();
        failing.send("invoice-for-" + order);
        try {
            throw new RuntimeException("inventory check failed");
        } catch (RuntimeException e) {
            failing.rollback();
        }
        System.out.println("after rollback, destination empty "
                + broker.destinationChannel.isEmpty());
        System.out.println("after rollback, source restored "
                + broker.sourceChannel.size());

        TransactedSession succeeding = new TransactedSession(broker);
        succeeding.begin();
        String order2 = succeeding.receive();
        succeeding.send("invoice-for-" + order2);
        succeeding.send("shipment-for-" + order2);
        succeeding.commit();
        System.out.println("after commit, destination size "
                + broker.destinationChannel.size());
        System.out.println("after commit, source remaining "
                + broker.sourceChannel.size());
    }
}
```

### Go

```go
package main

import "fmt"

type Broker struct {
	source      []string
	destination []string
}

type TransactedSession struct {
	broker           *Broker
	pendingOutbound  []string
	tentativeRemoved []string
	open             bool
}

func NewTransactedSession(b *Broker) *TransactedSession {
	return &TransactedSession{broker: b}
}

func (s *TransactedSession) Begin() error {
	if s.open {
		return fmt.Errorf("transaction already open")
	}
	s.open = true
	return nil
}

func (s *TransactedSession) Receive() (string, bool) {
	if !s.open || len(s.broker.source) == 0 {
		return "", false
	}
	msg := s.broker.source[0]
	s.broker.source = s.broker.source[1:]
	s.tentativeRemoved = append(s.tentativeRemoved, msg)
	return msg, true
}

func (s *TransactedSession) Send(message string) {
	s.pendingOutbound = append(s.pendingOutbound, message)
}

func (s *TransactedSession) Commit() {
	s.broker.destination = append(s.broker.destination, s.pendingOutbound...)
	s.pendingOutbound = nil
	s.tentativeRemoved = nil
	s.open = false
}

func (s *TransactedSession) Rollback() {
	restored := make([]string, 0, len(s.tentativeRemoved)+len(s.broker.source))
	restored = append(restored, s.tentativeRemoved...)
	restored = append(restored, s.broker.source...)
	s.broker.source = restored
	s.pendingOutbound = nil
	s.tentativeRemoved = nil
	s.open = false
}

func main() {
	broker := &Broker{source: []string{"order-1", "order-2"}}

	failing := NewTransactedSession(broker)
	_ = failing.Begin()
	order, _ := failing.Receive()
	failing.Send("invoice-for-" + order)
	failing.Rollback()
	fmt.Println("after rollback, destination empty", len(broker.destination) == 0)
	fmt.Println("after rollback, source restored", len(broker.source))

	succeeding := NewTransactedSession(broker)
	_ = succeeding.Begin()
	order2, _ := succeeding.Receive()
	succeeding.Send("invoice-for-" + order2)
	succeeding.Send("shipment-for-" + order2)
	succeeding.Commit()
	fmt.Println("after commit, destination size", len(broker.destination))
	fmt.Println("after commit, source remaining", len(broker.source))
}
```

### Python

```python
from dataclasses import dataclass, field
from collections import deque


class TransactionStateError(Exception):
    pass


@dataclass
class Broker:
    source: deque
    destination: deque = field(default_factory=deque)


class TransactedSession:
    def __init__(self, broker: Broker):
        self._broker = broker
        self._pending_outbound: list[str] = []
        self._tentatively_removed: list[str] = []
        self._open = False

    def begin(self) -> None:
        if self._open:
            raise TransactionStateError("transaction already open")
        self._open = True

    def receive(self) -> str | None:
        self._require_open()
        if not self._broker.source:
            return None
        message = self._broker.source.popleft()
        self._tentatively_removed.append(message)
        return message

    def send(self, message: str) -> None:
        self._require_open()
        self._pending_outbound.append(message)

    def commit(self) -> None:
        self._require_open()
        self._broker.destination.extend(self._pending_outbound)
        self._pending_outbound.clear()
        self._tentatively_removed.clear()
        self._open = False

    def rollback(self) -> None:
        self._require_open()
        for message in reversed(self._tentatively_removed):
            self._broker.source.appendleft(message)
        self._tentatively_removed.clear()
        self._pending_outbound.clear()
        self._open = False

    def _require_open(self) -> None:
        if not self._open:
            raise TransactionStateError("no open transaction")


def run_unit_of_work(session: TransactedSession) -> None:
    session.begin()
    try:
        order = session.receive()
        if order is None:
            session.rollback()
            return
        session.send(f"invoice-for-{order}")
        session.send(f"shipment-for-{order}")
        session.commit()
    except Exception:
        session.rollback()
        raise


if __name__ == "__main__":
    broker = Broker(source=deque(["order-1", "order-2"]))

    run_unit_of_work(TransactedSession(broker))
    print("after first commit, destination size", len(broker.destination))
    print("after first commit, source remaining", len(broker.source))

    failing_session = TransactedSession(broker)
    failing_session.begin()
    order = failing_session.receive()
    failing_session.send(f"invoice-for-{order}")
    failing_session.rollback()
    print("after rollback, destination size unchanged", len(broker.destination))
    print("after rollback, source restored", len(broker.source))
```

### TypeScript

```typescript
interface Broker {
  source: string[];
  destination: string[];
}

class TransactionStateError extends Error {}

class TransactedSession {
  private pendingOutbound: string[] = [];
  private tentativelyRemoved: string[] = [];
  private open = false;

  constructor(private readonly broker: Broker) {}

  begin(): void {
    if (this.open) {
      throw new TransactionStateError("transaction already open");
    }
    this.open = true;
  }

  receive(): string | undefined {
    this.requireOpen();
    const message = this.broker.source.shift();
    if (message !== undefined) {
      this.tentativelyRemoved.push(message);
    }
    return message;
  }

  send(message: string): void {
    this.requireOpen();
    this.pendingOutbound.push(message);
  }

  commit(): void {
    this.requireOpen();
    this.broker.destination.push(...this.pendingOutbound);
    this.pendingOutbound = [];
    this.tentativelyRemoved = [];
    this.open = false;
  }

  rollback(): void {
    this.requireOpen();
    this.broker.source.unshift(...this.tentativelyRemoved);
    this.tentativelyRemoved = [];
    this.pendingOutbound = [];
    this.open = false;
  }

  private requireOpen(): void {
    if (!this.open) {
      throw new TransactionStateError("no open transaction");
    }
  }
}

function runUnitOfWork(session: TransactedSession): void {
  session.begin();
  try {
    const order = session.receive();
    if (order === undefined) {
      session.rollback();
      return;
    }
    session.send(`invoice-for-${order}`);
    session.send(`shipment-for-${order}`);
    session.commit();
  } catch (err) {
    session.rollback();
    throw err;
  }
}

const broker: Broker = { source: ["order-1", "order-2"], destination: [] };

runUnitOfWork(new TransactedSession(broker));
console.log("after first commit, destination size", broker.destination.length);
console.log("after first commit, source remaining", broker.source.length);

const failingSession = new TransactedSession(broker);
failingSession.begin();
const order = failingSession.receive();
if (order !== undefined) {
  failingSession.send(`invoice-for-${order}`);
}
failingSession.rollback();
console.log("after rollback, destination size unchanged", broker.destination.length);
console.log("after rollback, source restored", broker.source.length);
```
