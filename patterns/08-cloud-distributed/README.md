# Family 08. Cloud and Distributed

Origin. Azure Architecture Center, Nygard

34 entries, 305,444 words. Every entry carries all 18
dimensions from [the entry contract](../../docs/ENTRY-TEMPLATE.md).

## Cloud Distributed

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Asynchronous Request-Reply](asynchronous-request-reply.md) | canonical | 7,657 | A client calls an API expecting an answer inside the budget of one HTTP connection, typically well under a second. |
| [Index Table](index-table.md) | canonical | 8,260 | A data store organizes its records by a primary key so that, given the key, it can locate the record in close to constant time. |
| [Messaging Bridge](messaging-bridge.md) | canonical | 6,068 | An organization that has been running for more than a few years rarely has one messaging system. |

## Cloud Distributed Systems

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [External Configuration Store](external-configuration-store.md) | canonical | 8,367 | An application reads its behavior-controlling values, a database connection string, a feature toggle, a rate limit, a UI theme choice, a downstream service URL, from a file that ... |

## Cloud and Distributed

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Backends for Frontends](backends-for-frontends.md) | established | 7,877 | A product ships to more than one kind of client. |
| [Cache-Aside](cache-aside.md) | canonical | 11,151 | A service reads the same records far more often than it writes them, and the read path is expensive. |
| [Federated Identity](federated-identity.md) | canonical | 8,634 | An organization runs several applications. |
| [Gateway Aggregation](gateway-aggregation.md) | canonical | 7,007 | A client needs data or a decision that no single backend service owns end to end. |
| [Gateway Offloading](gateway-offloading.md) | canonical | 9,619 | An application is built as a set of backend instances, whether that is one service replicated many times or several distinct services behind one entry point. |
| [Materialized View](materialized-view.md) | canonical | 8,521 | An application reads data far more often than it writes it, and the shape a write path needs is almost never the shape a read path wants. |

## Cloud and Distributed Systems

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Ambassador](ambassador.md) | canonical | 7,796 | A service needs network capabilities that are not really its own concern. |
| [Gateway Routing](gateway-routing.md) | canonical | 8,277 | A client, whether a browser, a mobile app, or another service, needs to talk to a system that is actually made of several independently deployed backends. |

## Coordination

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Leader Election](leader-election.md) | canonical | 7,764 | A fleet of otherwise identical replicas exists for availability. |

## Data Distribution

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Sharding](sharding.md) | canonical | 7,039 | A single database server has a hard limit on what it can do. |

## Data and Consistency

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Command Query Responsibility Segregation](cqrs.md) | established | 11,603 | A single model is being asked to serve two jobs whose requirements have diverged, and the model is losing on both. |

## Data and Persistence

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Event Sourcing](event-sourcing.md) | established | 9,797 | A system needs to answer questions about how it reached its current state, and the storage model it uses has already destroyed the answer. |

## Data consistency

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Compensating Transaction](compensating-transaction.md) | canonical | 8,001 | A single database transaction gives you atomicity for free. |
| [Saga](saga.md) | canonical | 9,350 | A business operation spans several stores of record and must either happen in full or leave nothing of consequence behind, and there is no transaction manager that can span them. |

## Deployment and Scale

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Deployment Stamps](deployment-stamps.md) | canonical | 9,272 | A team ships a SaaS product as a single deployed instance, one application tier, one database, one everything, and every customer's traffic and data flow through that one instance. |

## Geo-Distribution and Availability

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Geode](geode.md) | established | 10,088 | A service with users spread across a continent, or across the world, starts from the simplest possible shape. |

## Integration

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Anti-Corruption Layer](anti-corruption-layer.md) | canonical | 8,210 | A team owns a domain model it has deliberately kept clean. |

## Messaging and Integration

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Choreography](choreography.md) | established | 9,041 | A business process spans more than one service, and each service owns a slice of state that no other service is allowed to touch directly, because that is the entire point of ... |
| [Claim Check](claim-check.md) | canonical | 8,847 | A service publishes a message that needs to carry a large piece of data, a scanned document, a video file, a full order history export, a machine learning feature vector, a ... |
| [Publisher-Subscriber](publisher-subscriber.md) | canonical | 8,855 | A component in a system needs to tell other components that something happened, and it does not know, and should not need to know, who those other components are. |

## Migration

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Strangler Fig](strangler-fig.md) | canonical | 10,348 | A system has been running in production for years. |

## Reliability

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Health Endpoint Monitoring](health-endpoint-monitoring.md) | canonical | 8,420 | A service running behind a load balancer, an orchestrator, or a service mesh can fail in ways that are invisible from outside the process. |

## Resilience

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Bulkhead](bulkhead.md) | canonical | 9,972 | A process holds a finite pool of something that every request needs. |
| [Retry](retry.md) | canonical | 9,997 | A caller sends a request across a boundary it does not control. |

## Resilience and Traffic Management

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Competing Consumers](competing-consumers.md) | canonical | 7,217 | A system produces units of work faster, or in bursts larger, than a single consumer process can absorb, and the units of work are independent of one another, meaning any one of ... |
| [Queue-Based Load Leveling](queue-based-load-leveling.md) | canonical | 9,730 | A system accepts work at a rate that varies over time, sometimes sharply, while the component that actually performs the work has a roughly fixed processing capacity per unit time. |
| [Rate Limiting](rate-limiting.md) | canonical | 10,988 | A service exposes an operation that costs something to perform. |
| [Throttling](throttling.md) | canonical | 10,477 | A service exposes an operation that costs something to run. |

## Security

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Gatekeeper](gatekeeper.md) | established | 9,190 | A cloud service exposes one or more API endpoints across an untrusted network, typically the public internet. |

## Stability

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Circuit Breaker](circuit-breaker.md) | canonical | 12,004 | A service calls a remote dependency. The dependency degrades in the worst possible way, which is not by refusing connections but by accepting them and answering slowly or not at ... |

## Reading order

Entries are independent. Each one names the patterns it composes with and
the patterns it conflicts with in dimension 13, so following those links
gives a better path than reading top to bottom.

Generated by `tools/gen-indexes.py`. Do not edit by hand.
