---
name: Distributed Transaction Coordinator Antipattern
slug: distributed-transaction-coordinator-antipattern
family: 10-microservices
category: Antipattern
aliases: [XA Across Services, Two-Phase Commit Across Microservices, Global Transaction Manager Antipattern, Distributed ACID Antipattern]
first_described: "Richardson, Microservices Patterns, Manning 2018, chapter 4, and Helland, Life beyond Distributed Transactions. An Apostate's Opinion, CIDR 2007"
maturity: established
related: [saga, transactional-outbox, idempotent-consumer, domain-event, transaction-log-tailing, database-per-service]
incompatible_with: [saga, database-per-service]
verified: 2026-08-17
---

# Distributed Transaction Coordinator Antipattern

## 1. Name, aliases, and lineage

The pattern this entry documents is not a pattern to adopt. It is the reuse of
a coordinator built for two-phase commit, XA, or a global transaction manager,
carried across an independently deployable service boundary in a microservice
architecture. The canonical antipattern name in circulation is Distributed
Transaction Coordinator Antipattern, sometimes shortened to XA Across
Services or Two-Phase Commit Across Microservices. Chris Richardson, in
*Microservices Patterns*, Manning Publications, 2018, chapter 4, "Managing
transactions with sagas", frames the constraint directly. a microservices
architecture needs a mechanism for maintaining data consistency across
services, and two-phase commit is ruled out early in that chapter as
unsuitable, with the saga pattern introduced as the replacement. Richardson's
companion pattern catalog states the same constraint in one line on the saga
page. "2PC is not an option" (Chris Richardson, "Pattern. Saga",
[microservices.io/patterns/data/saga.html](https://microservices.io/patterns/data/saga.html),
verified 2026-08-17).

The underlying mechanism, the two-phase commit protocol and its coordinator
role, is not itself an antipattern. It is a real, well studied distributed
algorithm, first formalized by Jim Gray, "Notes on Data Base Operating
Systems", in *Operating Systems*, Lecture Notes in Computer Science, volume
60, Springer, 1978, and standardized for heterogeneous resource managers as
the X/Open XA specification, published by The Open Group as "Distributed
Transaction Processing. The XA Specification", 1991. The XA specification
defines the coordinator role, called the Transaction Manager, and the
participant role, called the Resource Manager, connected through a fixed
`xa_prepare`, `xa_commit`, `xa_rollback` interface. What turns a legitimate
implementation of that specification into the antipattern documented here is
the placement of the coordinator across a network boundary that separates
independently owned, independently deployed services, rather than across
resources that live inside a single administrative and operational domain,
such as two databases owned by the same service.

The strongest theoretical case against carrying 2PC across that boundary comes
from Pat Helland, "Life beyond Distributed Transactions. An Apostate's
Opinion", position paper, CIDR 2007,
[ics.uci.edu/~cs223/papers/cidr07p15.pdf](https://ics.uci.edu/~cs223/papers/cidr07p15.pdf),
verified 2026-08-17. Helland, who had spent much of his career building and
advocating transactional platforms at Tandem and Microsoft, argues in that
paper that global serializability across autonomous services does not scale
and does not survive partition, and that the honest replacement is to accept
that each service owns one entity's worth of ACID, and that anything crossing
services is a message, not a transaction.

## 2. Problem and context

A team is decomposing a monolith, or is starting a new system, along service
boundaries chosen so that each service owns its own data, per the
[Database per Service](database-per-service.md) pattern. Somewhere in the
business logic there is an operation that used to be a single database
transaction inside the monolith. an order is placed and a customer's credit
limit is checked and reserved in the same commit. After decomposition, the
order lives in an Order service and the credit reservation lives in a Customer
service, each with its own database.

The team wants the SAME atomicity guarantee it had before decomposition. The
familiar tool for atomicity across more than one resource is a distributed
transaction coordinator. On the Java platform this is a JTA transaction
manager, commonly Atomikos or the JBoss project Narayana, wired to XA drivers
for each database, or a custom in-house global lock service. The team wraps
the call from the Order service to the Customer service, and the two local
database commits, inside one distributed transaction, expecting the same
begin, prepare, commit sequence that used to run inside one process and one
database connection pool.

This is the antipattern context. it appears specifically when the participants
in the transaction are OWNED BY DIFFERENT SERVICES that are independently
deployed and independently scaled, and reached over a network that can
partition, be slow, or be temporarily unavailable, rather than resources that
share one administrative domain and one deployment lifecycle. The single most
common trigger is a lift-and-shift migration where a monolith's local
transaction boundary is preserved literally, service by service, instead of
being redrawn around what data genuinely needs to be consistent together.

## 3. Forces

- **Atomicity versus availability.** Two-phase commit is a blocking protocol.
  If the coordinator crashes after every participant has voted yes but before
  the commit message is sent, every participant is required to hold its locks
  and wait, because it cannot unilaterally decide whether to commit or abort.
  This is documented as the fundamental liveness weakness of 2PC. it trades
  availability for consistency during a coordinator or network failure,
  reflected in the CAP framing that 2PC sits on the CP side of that trade-off.
- **Latency versus correctness.** A prepare round trip to every participant,
  followed by a commit round trip to every participant, adds at minimum two
  full network round trips to every request, and the request is only as fast
  as its slowest participant. Under microservice deployment, participants are
  frequently in different processes, containers, and sometimes different
  availability zones, so this latency is not the same as the in-process
  latency the pattern was designed around.
- **Coupling versus independent deployability.** The entire premise of a
  microservice architecture is that each service is deployed on its own
  schedule. A shared distributed transaction coordinator reintroduces runtime
  coupling. every participant must be reachable and responsive at the same
  moment for any transaction to complete, which defeats the purpose of
  decomposing the system in the first place.
- **Lock duration versus throughput.** Every resource enrolled in the
  transaction holds its locks for the full duration of the two phases,
  including the time spent waiting on the slowest or least available
  participant. Under real production load this holds row and table locks
  across services for durations the originating database was never designed
  or tuned to sustain, and it degrades throughput on every enrolled resource,
  not only the one that is actually slow.
- **Operational simplicity versus a new class of failure.** A working 2PC
  deployment requires a recovery log the coordinator persists before sending
  the prepare message, a recovery procedure run on coordinator restart, and
  monitoring for in-doubt or heuristically completed transactions. This is a
  genuinely new operational surface a microservices team now owns, on top of
  the operational surface each individual service already owns.

## 4. Applicability and non-applicability

Reach for a distributed transaction coordinator, in its legitimate form,
when all of the following hold.

- The resources being enrolled are owned by ONE team, deployed on ONE release
  cadence, and reachable within one low-latency network segment, for example
  two databases used by a single service, or a service and a message broker
  it exclusively owns.
- The workload's throughput and concurrency requirements are modest enough
  that lock hold time across the enrolled resources during the prepare phase
  is acceptable, which in practice means batch, back office, or low
  concurrency operational tooling rather than a customer facing hot path.
- A resource is genuinely XA capable and the driver is production tested for
  it, because a resource that only degrades to a best effort or single phase
  enlistment silently defeats the guarantee the whole mechanism exists for.

Do NOT reach for a distributed transaction coordinator, and treat its
presence as this antipattern, when any of the following hold.

- The participants are owned by different services with independent
  deployment pipelines. This is the defining condition of the antipattern
  documented here, and it is present in essentially every microservice
  architecture by design.
- The workload is customer facing and latency sensitive, because the added
  round trips and lock duration are paid on every request, not only during
  failure.
- A participant is not a classic ACID resource manager, for example a REST
  API, a third party SaaS, a cache, or most modern message brokers, none of
  which speak the XA `prepare` and `commit` protocol in a way that is safe to
  rely on in production.
- High availability during a coordinator or network failure matters more than
  strict cross-service atomicity, which is true of nearly every internet
  facing system, and is the exact condition Helland's 2007 paper argues for
  abandoning global serializability in favor of message based consistency.
- The team's actual requirement, on inspection, is eventual consistency with
  a defined compensating action for failure, which is a strictly weaker and
  operationally cheaper requirement than the strict atomicity a 2PC
  coordinator provides, and is what the [Saga](../08-cloud-distributed/saga.md)
  pattern is built to satisfy without a shared coordinator or held locks.

The one documented exception worth naming explicitly. purpose built globally
distributed databases, such as Google Cloud Spanner, DO implement a form of
two-phase commit internally, but they do so as a single vendor operated
system with a TrueTime bounded clock and internal Paxos replicated
participants under one operational ownership, not as a coordinator bolted
across independently owned application services. Building a Spanner
equivalent is an infrastructure investment measured in engineering years, and
using one is different from wiring a generic JTA coordinator across service
boundaries with off the shelf drivers.

## 5. Structure

- **Transaction Coordinator (also Transaction Manager in XA terminology).**
  The single process that drives the two-phase protocol. it assigns a global
  transaction identifier, sends the prepare request to every enlisted
  participant, collects votes, decides commit or abort based on unanimous
  agreement, sends the second phase decision, and persists a recovery log
  entry before each phase so it can resume after its own crash.
- **Resource Manager (Participant).** Each enrolled resource, typically a
  relational database reached through an XA capable driver. On prepare it
  must durably record enough state to guarantee it can honor either a later
  commit or a later rollback, which in practice means acquiring and holding
  locks on the affected rows through both phases.
- **Application Server or Framework Integration Layer.** In the Java
  ecosystem this is the JTA container, for example WildFly's built in
  transaction subsystem, which is implemented by the Narayana project as its
  transaction manager (confirmed in WildFly's own developer documentation,
  "Jakarta Transactions Reference",
  [github.com/wildfly/wildfly/blob/main/docs/src/main/asciidoc/_developer-guide/Jakarta_Transactions_Reference.adoc](https://github.com/wildfly/wildfly/blob/main/docs/src/main/asciidoc/_developer-guide/Jakarta_Transactions_Reference.adoc),
  verified 2026-08-17). The antipattern occurs when this integration layer
  is used to enlist resources that live behind a network call to a different
  microservice, rather than resources local to one service's own process.
- **The service boundary itself.** In the antipattern's structure, the
  service boundary is drawn incorrectly relative to the transactional
  boundary. two services are pulled into one atomic unit of work at runtime,
  which contradicts the boundary the services were decomposed along.

## 6. ASCII structure diagram

```
                         WORKING CASE (single service, own data)
    +--------------------------------------------------------------+
    |                        Order Service                         |
    |                                                                |
    |   +----------------+       +-----------------+                |
    |   | Order table     |<---->| Coordinator (JTA)|                |
    |   +----------------+       +-----------------+                |
    |                                    |                          |
    |                             +----------------+                |
    |                             | Outbox table    |                |
    |                             +----------------+                |
    +--------------------------------------------------------------+
    One process, one deployment, one operational owner.

                    ANTIPATTERN CASE (coordinator crosses services)
    +----------------+          prepare/commit         +----------------+
    |  Order Service  | <==============================> | Customer Service|
    |  +-----------+  |                                  |  +-----------+  |
    |  | Order DB  |  |        +------------------+       |  | Cust. DB  |  |
    |  +-----------+  |------->|  Global Transaction |<----|  +-----------+  |
    +----------------+        |     Coordinator      |     +----------------+
                               +------------------+
                                        ^
                                        |  prepare/commit, own release cadence
                                        v
                               +------------------+
                               | Inventory Service |
                               |  +-----------+     |
                               |  | Inv. DB   |     |
                               |  +-----------+     |
                               +------------------+
    Three independently deployed services, one coordinator forcing them to
    vote and lock in lockstep. If any one is slow or down, the other two
    hold locks and cannot proceed.
```

## 7. Dynamics

```
Order Service        Coordinator          Customer Service     Inventory Service
     |  begin tx          |                     |                     |
     |-------------------->|                     |                     |
     |  reserve order       |                     |                     |
     |  (local write)       |                     |                     |
     |                      | PREPARE ------------------------------->  |
     |                      | PREPARE --------->  |                     |
     |                      |                     |  lock row, vote YES |
     |                      | <----------- vote YES|                     |
     |                      | <---------------------------- vote YES ---|
     |                      | (all YES: proceed)  |                     |
     |                      | COMMIT ----------->  |                     |
     |                      | COMMIT -------------------------------->  |
     |                      |                     | release lock, ack   |
     |  <--- tx complete ---|                     |                     |

Failure branch, the case this antipattern is named for:

     |  begin tx           |                     |                     |
     |-------------------->|                     |                     |
     |                      | PREPARE ----------> |                     |
     |                      | <---------- vote YES |  row LOCKED, waiting|
     |                      | PREPARE -------------------------------->  |
     |                      |    X  network partition or coordinator    |
     |                      |    X  crash before COMMIT is sent          |
     |                      |                     |                     |
     | Customer Service now holds the row lock indefinitely. It cannot  |
     | unilaterally commit (might contradict a later abort decision) or |
     | abort (might contradict a later commit decision) without hearing|
     | from the coordinator, so the lock is held until coordinator      |
     | recovery, which may take minutes to hours depending on ops       |
     | response time.                                                   |
```

## 8. Implementation variants

- **XA plus JTA (Java).** The most common concrete form, using a JTA
  transaction manager such as Atomikos Transaction Essentials or Narayana,
  each wired to XA drivers for every enrolled database. Atomikos is
  positioned explicitly for standalone use outside an application server,
  which makes it easy to reach for inside individual microservices without
  realizing the coordinator is about to be asked to span more than one of
  them (Atomikos documentation, "Atomikos vs JBoss Transaction Manager
  (Narayana)",
  [atomikos.com/Documentation/AtomikosVsJBossNarayana](https://www.atomikos.com/Documentation/AtomikosVsJBossNarayana),
  verified 2026-08-17).
- **A hand rolled coordinator service.** A team that has never used XA
  sometimes writes its own lightweight coordinator, a service that calls a
  `/prepare` and a `/commit` endpoint on each participating service over
  HTTP. This carries every weakness of formal 2PC, plus the loss of the
  formal durability and recovery guarantees the XA specification actually
  requires of a conforming Resource Manager, because a REST endpoint has no
  standardized in-doubt transaction log the way an XA driver does.
- **A distributed lock service used as an ad hoc coordinator.** A variant
  where the team does not implement two full phases, but uses a distributed
  lock (implemented on top of a system such as ZooKeeper or etcd) to hold a
  cross-service critical section open across multiple remote calls. This
  shares the antipattern's core defect, request latency now depends on
  every participant's availability, and a stuck holder can starve the whole
  workflow, even though it is not literally the XA protocol.
- **Database level sharding coordinators.** Some sharded database platforms
  offer XA as one of several internal consistency modes for cross-shard
  writes, for example Apache ShardingSphere's integration with Atomikos,
  Bitronix, and Narayana as pluggable transaction managers (Apache
  ShardingSphere, "The mixed open-source distributed transaction solution",
  [shardingsphere.medium.com/the-mixed-open-source-distributed-transaction-solution-1024a5f2c95c](https://shardingsphere.medium.com/the-mixed-open-source-distributed-transaction-solution-1024a5f2c95c),
  verified 2026-08-17). This is legitimate because the shards are owned and
  operated by one platform, not by independently deployed application
  services, and it illustrates the boundary drawn in dimension 4. the same
  mechanism is sound within one operational domain and unsound across
  service ownership boundaries.

## 9. Known production uses

The pattern documented here is an antipattern, so "known production uses"
means named systems whose coordinator role is real and well documented,
together with the boundary at which its use is sound versus where reusing
it across services becomes the failure mode this entry warns against.

- **WildFly (Red Hat, formerly JBoss Application Server).** Ships Narayana
  as its built in Jakarta Transactions implementation and default
  transaction manager, coordinating XA resources enlisted within a single
  deployed application. This is the coordinator mechanism itself in
  legitimate, single application server use (WildFly developer
  documentation, "Jakarta Transactions Reference",
  [github.com/wildfly/wildfly/blob/main/docs/src/main/asciidoc/_developer-guide/Jakarta_Transactions_Reference.adoc](https://github.com/wildfly/wildfly/blob/main/docs/src/main/asciidoc/_developer-guide/Jakarta_Transactions_Reference.adoc),
  verified 2026-08-17).
- **Atomikos Transaction Essentials, in Spring Boot deployments.** Documented
  as a commonly chosen JTA transaction manager for Spring Boot applications
  specifically because of its ease of integration outside a full application
  server, which is exactly the packaging that makes it easy to enlist across
  independently deployed services by accident (Atomikos product
  documentation, "Atomikos ExtremeTransactions for Cloud-Native XTP and
  SOA", [atomikos.com/Main/ExtremeTransactions](https://www.atomikos.com/Main/ExtremeTransactions),
  verified 2026-08-17).
- **Apache ShardingSphere.** Offers XA as one of its distributed transaction
  modes for coordinating writes across database shards, invoking Atomikos,
  Bitronix, or Narayana as the underlying coordinator implementation. It is
  scoped to shards under ShardingSphere's own operational control, not to
  arbitrary microservice participants, which is the condition under which
  this mechanism remains sound (Apache ShardingSphere Medium engineering
  blog, "The mixed open-source distributed transaction solution",
  [shardingsphere.medium.com/the-mixed-open-source-distributed-transaction-solution-1024a5f2c95c](https://shardingsphere.medium.com/the-mixed-open-source-distributed-transaction-solution-1024a5f2c95c),
  verified 2026-08-17).
- **Chris Richardson's Microservices Patterns catalog, as the documented
  counter case.** Richardson's own pattern catalog names the constraint that
  triggers this antipattern entry directly on the Saga pattern page,
  "2PC is not an option", presented as the forcing function for adopting
  sagas instead of a cross-service coordinator (Chris Richardson, "Pattern.
  Saga", [microservices.io/patterns/data/saga.html](https://microservices.io/patterns/data/saga.html),
  verified 2026-08-17).

## 10. Consequences

Positive, when confined to its legitimate scope inside one operational
domain (dimension 4).

- Provides strict, provable atomicity across more than one resource without
  the application writing any compensating logic.
- Gives the application a familiar transactional programming model. begin,
  do work, commit or rollback, identical to a single database transaction.
- Recovers automatically after a coordinator restart, because the protocol
  is specifically designed with a durable in-doubt transaction log for that
  purpose, unlike an ad hoc distributed lock.

Negative, and dominant once the coordinator crosses independently deployed
service boundaries.

- Availability of the entire transaction is bounded by the availability of
  its least available participant, for every single request, not only
  during an outage.
- Lock hold time extends across the full network round trip of every
  participant's prepare phase, which degrades throughput on resources that
  are otherwise healthy and unrelated to any slowdown.
- Reintroduces deployment coupling between services that were split apart
  specifically to remove that coupling, undermining the stated goal of the
  [Database per Service](database-per-service.md) decomposition.
- A coordinator crash between phases leaves participants in an in-doubt
  state that can require manual operator intervention (a heuristic commit
  or heuristic rollback decision) to resolve, which is an operational
  failure mode most microservice teams have no runbook for.
- Most modern infrastructure the industry has standardized on, including the
  majority of message brokers and virtually all third party HTTP APIs, does
  not implement the XA protocol, so a coordinator built this way structurally
  cannot cover the majority of a modern microservice's dependencies, and the
  team ends up maintaining two consistency mechanisms rather than one.

## 11. Failure modes and misuse

- **Symptom.** A single slow database, days after the coordinator was
  introduced, now causes request timeouts on two or three unrelated
  services that have nothing to do with the slow database's feature.
  **Cause.** All of the enrolled resources share one prepare-phase blocking
  window, so the slowest participant sets the effective minimum latency for
  every transaction, on every enrolled service.
  **Fix.** Remove the shared coordinator, replace the cross-service
  interaction with an asynchronous [Saga](../08-cloud-distributed/saga.md),
  and let each service commit its own local transaction independently.

- **Symptom.** After a deployment or a brief network blip, one service's
  database shows rows locked with no active session holding them, and the
  lock does not clear on its own.
  **Cause.** The coordinator crashed, was restarted onto a different host
  without its recovery log, or the network partitioned between the prepare
  vote and the commit decision, leaving the participant correctly, per the
  protocol, unwilling to unilaterally resolve the transaction.
  **Fix.** Restore or recover the coordinator's transaction log so it can
  complete the in-doubt transactions, and add monitoring specifically for
  in-doubt transaction age so this is caught in minutes, not discovered by a
  customer facing outage.

- **Symptom.** A team observes that only some of its external dependencies,
  usually the relational databases, actually participate correctly in the
  distributed transaction, while calls to a message broker, a cache, or a
  third party API appear to commit even when the surrounding transaction
  later rolls back.
  **Cause.** Those dependencies do not implement the XA `prepare` contract.
  A non-XA resource enlisted as a "last resource" or wrapped in a naive
  adapter can only approximate participation, and it is the first thing to
  silently violate atomicity under load.
  **Fix.** Do not enlist non-XA resources in the coordinator at all. Model
  the interaction with that resource as an event published after the local
  transaction commits, using [Transactional Outbox](transactional-outbox.md)
  and [Transaction Log Tailing](transaction-log-tailing.md), so atomicity
  is guaranteed only for the one resource that is actually transactional,
  and everything downstream is handled through at-least-once delivery plus
  [Idempotent Consumer](idempotent-consumer.md).

- **Symptom.** Independent services now have to be deployed and rolled back
  together, defeating the release calendar the microservice split was
  supposed to enable, and an incident in one service now pages the on-call
  engineer for a completely unrelated service.
  **Cause.** The coordinator has become a shared, stateful piece of
  infrastructure that every enrolled service is implicitly coupled to at
  runtime, which is the structural symptom of this antipattern regardless
  of whether locks are currently stuck.
  **Fix.** Redraw the transactional boundary to match the service boundary.
  identify the ONE service that should genuinely own the invariant in
  question, and make every other participant reachable only through
  published domain events and compensating actions.

## 12. Trade-off matrix

| Force | Distributed Transaction Coordinator (this antipattern) | Saga (choreography or orchestration) | Transactional Outbox plus Idempotent Consumer |
|---|---|---|---|
| Cross-service atomicity | Strict, all or nothing | None, eventual consistency with compensation | None, eventual consistency, no compensation needed if design is additive |
| Availability under one participant's outage | Every participant blocked | Only the affected step blocks, others proceed or compensate | Publisher is fully decoupled from consumer availability |
| Added request latency | At least two full round trips to every participant, every request | One round trip per saga step, steps run independently | One local commit, publish is asynchronous |
| Requires a shared, stateful coordinator process | Yes | No, for choreography. Yes, for orchestration, but the orchestrator does not hold cross-service locks | No |
| Works with non-transactional resources, brokers, third party APIs | No, requires XA support | Yes, this is the common case | Yes, this is the common case |
| Operational burden introduced | In-doubt transaction recovery, heuristic decisions | Compensating action design and testing per step | Outbox table cleanup, consumer deduplication |
| Coupling to other services' deployment schedule | High, all enrolled services must be reachable at once | Low, steps are decoupled through events or an orchestrator's own retry logic | Low, producer and consumer evolve independently |

## 13. Related and incompatible patterns

- **[Saga](../08-cloud-distributed/saga.md).** The direct replacement this
  antipattern entry exists to route a team toward. Saga trades strict
  atomicity for a sequence of local transactions plus compensating actions,
  and is the pattern Richardson's own catalog names as the answer once 2PC
  is ruled out.
- **[Transactional Outbox](transactional-outbox.md) and
  [Transaction Log Tailing](transaction-log-tailing.md).** These solve the
  narrower, genuinely hard part of the original problem, atomically
  combining a local database write with reliably publishing an event about
  it, without needing any resource outside the service's own database to be
  XA capable.
- **[Idempotent Consumer](idempotent-consumer.md).** Required alongside
  Saga and Transactional Outbox because removing the coordinator means
  removing exactly-once delivery. every consumer of a cross-service event
  must tolerate redelivery.
- **[Domain Event](domain-event.md).** The message shape that replaces the
  coordinator's prepare and commit calls as the mechanism for one service
  to inform another that something happened.
- **[Database per Service](database-per-service.md).** This is the pattern
  whose intent the antipattern directly undermines. Database per Service is
  chosen specifically so that each service's data can evolve and scale
  independently, and reintroducing a coordinator across those databases
  reverses that decision without reversing the decomposition that motivated
  it.
- **Incompatible with Saga and Database per Service**, in the sense that a
  service that is genuinely coordinated by a cross-service 2PC transaction
  has, in practice, stopped being an independently deployable service for
  the duration of that transaction, which is the property both of those
  patterns depend on.

## 14. Refactoring path in and out

Path a team typically follows INTO this antipattern, so it can be
recognized early.

1. A monolith is decomposed by extracting a service, following
   [Decompose by Business Capability](decompose-by-business-capability.md) or
   [Decompose by Subdomain](decompose-by-subdomain.md).
2. An existing local transaction, previously spanning two tables in one
   database, is discovered to now span the extracted service and the
   remaining monolith, or two newly extracted services.
3. Rather than redesigning the operation, the team reaches for the
   transaction manager already in use inside the monolith, for example
   Atomikos or Narayana, and configures it to enlist the new service's
   database over its existing XA driver.
4. The operation appears to work correctly in development and light staging
   load, because failure and partition are rare in that environment, and the
   antipattern's true cost only appears under production concurrency or a
   real coordinator or network failure.

Path OUT of the antipattern, once it is identified.

1. Identify the actual business invariant the original transaction
   protected, separately from the code that happened to implement it as one
   database commit. usually this is a much narrower guarantee than "these
   two tables are always in sync", for example "an order is never confirmed
   against a customer whose credit limit is already exceeded at confirmation
   time", which does not require the credit check to be inside the same
   atomic commit as the order write.
2. Pick the single service that should own that invariant going forward, and
   design the remaining services' involvement as either a synchronous
   validation call that happens BEFORE any local write (no coordinator
   needed, because nothing has committed yet on either side), or an
   asynchronous compensating step after the fact, following Saga.
3. Introduce Transactional Outbox at the service whose local write must
   reliably trigger downstream action, so that the local commit and the
   publish of the resulting event are atomic without needing the downstream
   service enlisted in anything.
4. Add Idempotent Consumer at every service that consumes the resulting
   events, since at-least-once delivery is now the guarantee in place of
   exactly-once.
5. Remove the cross-service enlistment from the transaction manager
   configuration last, only after the saga steps and compensations have
   been tested under the failure conditions dimension 15 describes, so
   there is no window where neither mechanism is actually protecting the
   invariant.

## 15. Testing and verification

Testing a system still carrying this antipattern is itself a diagnostic
signal. the tests a team is forced to write reveal the coupling.

- A correct integration test for a 2PC coordinated flow must bring up every
  enrolled service's database simultaneously, in a state where all can
  actually communicate with the coordinator, which is expensive and slow
  compared to testing one service's local transaction in isolation. If a
  team finds it cannot write a fast, single-service test for an operation
  anymore, that is direct evidence the transactional boundary has spread
  wider than the service boundary.
- Fault injection is mandatory, not optional, because the antipattern's
  entire failure surface is the coordinator or network failing BETWEEN the
  two phases. tests should specifically kill the coordinator process, or
  drop the network connection to one participant, after that participant
  has voted yes but before it receives the commit decision, and assert that
  the participant correctly remains blocked, holding its lock, rather than
  guessing at the outcome. Confirming the correct behavior IS blocking is
  the actual verification here, which is the opposite of what most test
  suites check for.
- Once the refactor to Saga plus Transactional Outbox is complete,
  verification shifts to testing each compensating action independently.
  every forward step needs a corresponding test that its compensation
  correctly reverses partial effects when injected after that step alone
  has succeeded, and Idempotent Consumer needs a test that delivering the
  same event twice produces the same end state as delivering it once.

## 16. Observability signals

- **In-doubt transaction count and age**, read directly from the
  coordinator's transaction log. any transaction older than the expected
  prepare-to-commit window and still open is the primary early warning
  signal for this antipattern's characteristic failure, and should page
  someone, not sit in a log.
- **Lock wait time on each enrolled database**, broken out specifically for
  connections associated with the distributed transaction manager versus
  ordinary local transactions. a widening gap between the two is the
  throughput cost of the antipattern becoming visible under load.
- **Coordinator restart count and recovery duration**, since every restart
  triggers a recovery scan of the transaction log, and the duration of that
  scan is additional time during which the previously enrolled resources
  may remain blocked.
- **Cross-service call latency histogram for the specific endpoint that
  performs the enlistment**, which will show a visibly different shape,
  typically bimodal, compared to the same service's other endpoints that do
  not participate in the distributed transaction, because it now inherits
  tail latency from every participant.
- After migrating away from the coordinator, the equivalent healthy signal
  is the age distribution of unprocessed outbox rows and the count of
  events a consumer has retried past its normal delivery count, which
  surface stuck sagas without requiring any cross-service lock state at all.

## 17. Security and privacy implications

A cross-service distributed transaction coordinator is, structurally, a
single process trusted to reach into and hold locks on the private data
stores of every enrolled service. This concentrates several implications
that a single-service transaction manager does not carry.

- The coordinator's credentials to each participant's database are, by
  necessity, broad enough to prepare and commit arbitrary writes, which
  makes the coordinator itself a high value target. compromising it is
  equivalent to compromising write access to every enrolled service's data
  store simultaneously, which is a materially larger blast radius than
  compromising any single service.
- Because the coordinator crosses a network boundary that a well designed
  microservice architecture would otherwise keep as a narrow, audited API
  surface, it typically requires opening direct database network access
  between services, weakening the data-store isolation that
  [Database per Service](database-per-service.md) is partly adopted to
  provide as a security boundary, not only a scalability one.
- The in-doubt transaction log the coordinator persists for recovery
  necessarily contains enough state to resolve a partially applied write
  across services, which can include sensitive field values in transit
  between the prepare and commit phases, and this log needs the same
  encryption at rest and access control review as the databases it is
  coordinating, a requirement that is easy to omit because the log is
  infrastructure the application team rarely looks at directly.
- The migration path out, Saga plus Transactional Outbox plus Idempotent
  Consumer, has its own but smaller surface. the outbox table and the
  events it produces should carry only the fields a downstream consumer
  genuinely needs, since an event, unlike a row locked behind a database
  network boundary, is durably persisted on a broker that other consumers
  can potentially subscribe to.

## 18. References

- Chris Richardson, *Microservices Patterns*, Manning Publications, 2018,
  chapter 4, "Managing transactions with sagas".
- Chris Richardson, "Pattern. Saga", microservices.io pattern catalog,
  [microservices.io/patterns/data/saga.html](https://microservices.io/patterns/data/saga.html),
  verified 2026-08-17.
- Pat Helland, "Life beyond Distributed Transactions. An Apostate's
  Opinion", CIDR 2007 position paper,
  [ics.uci.edu/~cs223/papers/cidr07p15.pdf](https://ics.uci.edu/~cs223/papers/cidr07p15.pdf),
  verified 2026-08-17.
- Jim Gray, "Notes on Data Base Operating Systems", in *Operating Systems*,
  Lecture Notes in Computer Science, volume 60, Springer, 1978. Original
  formalization of the two-phase commit protocol.
- The Open Group, "Distributed Transaction Processing. The XA
  Specification", 1991. The interoperability standard defining the
  Transaction Manager and Resource Manager roles referenced throughout this
  entry.
- WildFly project, "Jakarta Transactions Reference", developer
  documentation,
  [github.com/wildfly/wildfly/blob/main/docs/src/main/asciidoc/_developer-guide/Jakarta_Transactions_Reference.adoc](https://github.com/wildfly/wildfly/blob/main/docs/src/main/asciidoc/_developer-guide/Jakarta_Transactions_Reference.adoc),
  verified 2026-08-17.
- Atomikos, "Atomikos vs JBoss Transaction Manager (Narayana)", product
  documentation,
  [atomikos.com/Documentation/AtomikosVsJBossNarayana](https://www.atomikos.com/Documentation/AtomikosVsJBossNarayana),
  verified 2026-08-17.
- Atomikos, "Atomikos ExtremeTransactions for Cloud-Native XTP and SOA",
  [atomikos.com/Main/ExtremeTransactions](https://www.atomikos.com/Main/ExtremeTransactions),
  verified 2026-08-17.
- Apache ShardingSphere, "The mixed open-source distributed transaction
  solution", engineering blog,
  [shardingsphere.medium.com/the-mixed-open-source-distributed-transaction-solution-1024a5f2c95c](https://shardingsphere.medium.com/the-mixed-open-source-distributed-transaction-solution-1024a5f2c95c),
  verified 2026-08-17.

## Code examples

The following three examples show the same operation, an order placement
that must not exceed a customer's credit limit, implemented first as the
antipattern (Java, using JTA style pseudocode against a UserTransaction to
keep the example runnable without a full application server), and then
correctly as a Saga step in TypeScript and Go. All three were written to
compile or run standalone.

### Java, the antipattern, minimal reproduction of the coordinator hazard

This does not depend on Atomikos or Narayana. it models what their
`UserTransaction.commit()` call does at the coordination level, so the
failure mode is visible without external dependencies. It compiles with
`javac` on a standard JDK.

```java
import java.util.ArrayList;
import java.util.List;

public class DistributedTransactionAntipattern {

    interface Participant {
        boolean prepare();
        void commit();
        void rollback();
    }

    static class RemoteServiceParticipant implements Participant {
        private final String serviceName;
        private final boolean simulateCrashAfterVote;

        RemoteServiceParticipant(String serviceName, boolean simulateCrashAfterVote) {
            this.serviceName = serviceName;
            this.simulateCrashAfterVote = simulateCrashAfterVote;
        }

        public boolean prepare() {
            System.out.println(serviceName + ": locking rows, voting YES");
            return true;
        }

        public void commit() {
            if (simulateCrashAfterVote) {
                throw new IllegalStateException(
                    serviceName + ": network partition before commit received. "
                    + "Rows remain LOCKED until coordinator recovery.");
            }
            System.out.println(serviceName + ": committing, releasing locks");
        }

        public void rollback() {
            System.out.println(serviceName + ": rolling back, releasing locks");
        }
    }

    static void twoPhaseCommit(List<Participant> participants) {
        List<Participant> prepared = new ArrayList<>();
        for (Participant p : participants) {
            if (!p.prepare()) {
                for (Participant done : prepared) {
                    done.rollback();
                }
                throw new IllegalStateException("Prepare phase failed, aborted.");
            }
            prepared.add(p);
        }
        for (Participant p : prepared) {
            p.commit();
        }
    }

    public static void main(String[] args) {
        List<Participant> participants = new ArrayList<>();
        participants.add(new RemoteServiceParticipant("OrderService", false));
        participants.add(new RemoteServiceParticipant("CustomerService", true));

        try {
            twoPhaseCommit(participants);
        } catch (IllegalStateException e) {
            System.out.println("Coordinator failure surfaced to caller: " + e.getMessage());
            System.out.println("OrderService already committed and cannot be undone "
                + "unilaterally; system is now inconsistent until manual recovery.");
        }
    }
}
```

Running this with `javac DistributedTransactionAntipattern.java` and
`java DistributedTransactionAntipattern` prints OrderService committing
successfully, then CustomerService raising the simulated partition, which
demonstrates the exact inconsistency window described in dimension 7.
OrderService has already committed by the time CustomerService's failure is
known, and nothing in the two-phase protocol as coded here can undo that.

### TypeScript, the replacement, an orchestrated Saga step

Compiles with a standard `tsc` against the `es2020` lib, no external
dependencies.

```typescript
type StepResult = { ok: true } | { ok: false; reason: string };

interface SagaStep {
  name: string;
  execute(): Promise<StepResult>;
  compensate(): Promise<void>;
}

class ReserveOrderStep implements SagaStep {
  name = "ReserveOrder";
  async execute(): Promise<StepResult> {
    console.log(`${this.name}: local commit, order status = PENDING_CREDIT_CHECK`);
    return { ok: true };
  }
  async compensate(): Promise<void> {
    console.log(`${this.name}: local commit, order status = CANCELLED`);
  }
}

class CheckCreditStep implements SagaStep {
  name = "CheckCredit";
  constructor(private readonly creditAvailable: boolean) {}
  async execute(): Promise<StepResult> {
    if (!this.creditAvailable) {
      return { ok: false, reason: "credit limit exceeded" };
    }
    console.log(`${this.name}: local commit, credit reserved`);
    return { ok: true };
  }
  async compensate(): Promise<void> {
    console.log(`${this.name}: local commit, credit released`);
  }
}

async function runSaga(steps: SagaStep[]): Promise<void> {
  const completed: SagaStep[] = [];
  for (const step of steps) {
    const result = await step.execute();
    if (!result.ok) {
      console.log(`Saga aborted at ${step.name}: ${result.reason}`);
      for (const done of completed.reverse()) {
        await done.compensate();
      }
      return;
    }
    completed.push(step);
  }
  console.log("Saga completed, no coordinator, no cross-service locks held.");
}

async function main() {
  await runSaga([new ReserveOrderStep(), new CheckCreditStep(false)]);
}

main();
```

Running this with `npx tsc saga.ts --lib es2020,dom --target es2020 && node saga.js`
shows ReserveOrderStep committing locally and immediately, CheckCreditStep
failing on its own local check with no network round trip to another
service's coordinator, and the compensation running only for the step that
actually committed, all without any resource being locked across a network
boundary at any point.

### Go, the replacement's consumer side, an idempotent event handler

Compiles and runs with `go run idempotent_consumer.go`.

```go
package main

import "fmt"

type processedStore struct {
	seen map[string]bool
}

func newProcessedStore() *processedStore {
	return &processedStore{seen: make(map[string]bool)}
}

func (s *processedStore) alreadyProcessed(eventID string) bool {
	return s.seen[eventID]
}

func (s *processedStore) markProcessed(eventID string) {
	s.seen[eventID] = true
}

type creditReservedEvent struct {
	eventID    string
	customerID string
	amount     int
}

func handleCreditReserved(store *processedStore, evt creditReservedEvent) {
	if store.alreadyProcessed(evt.eventID) {
		fmt.Printf("event %s already applied, skipping duplicate delivery\n", evt.eventID)
		return
	}
	fmt.Printf("applying credit reservation for customer %s, amount %d\n",
		evt.customerID, evt.amount)
	store.markProcessed(evt.eventID)
}

func main() {
	store := newProcessedStore()
	evt := creditReservedEvent{eventID: "evt-42", customerID: "cust-1", amount: 500}

	handleCreditReserved(store, evt)
	handleCreditReserved(store, evt)
}
```

Running this prints the reservation applied once, then the duplicate
delivery correctly skipped, which is the behavior an at-least-once broker
requires from every consumer once the shared coordinator, and the
exactly-once delivery it implicitly provided, has been removed.

C#, Swift, and Kotlin are omitted. the antipattern and its replacement are
runtime coordination concerns, not language idiom concerns, and the three
languages above already demonstrate the failure mode, the orchestrated
replacement, and the consumer-side obligation the replacement introduces,
without the additional length of restating the same three shapes three more
times.
