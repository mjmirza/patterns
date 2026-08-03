# Family 10. Microservices

Origin. Richardson

29 entries, 213,571 words. Every entry carries all 18
dimensions from [the entry contract](../../docs/ENTRY-TEMPLATE.md).

## Behavioral

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Domain Event](domain-event.md) | canonical | 6,667 | An operation on one part of a domain model needs to trigger a reaction in another part of the model, or in another bounded context entirely, and the class performing the operation ... |

## Communication

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Client-side Service Discovery](client-side-service-discovery.md) | canonical | 5,946 | A microservices architecture replaces a small number of long-lived, statically addressed processes with many short-lived, dynamically addressed ones. |
| [Remote Procedure Invocation](remote-procedure-invocation.md) | canonical | 6,005 | A microservice architecture splits a system into many independently deployable services, and almost every non-trivial request touches more than one of them. |

## Communication Style

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Messaging](messaging.md) | canonical | 5,733 | A microservice architecture splits one application into many independently deployable services, and Richardson is explicit that this decomposition alone does not remove the need ... |

## Cross-Cutting Concerns

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Microservice Chassis](microservice-chassis.md) | canonical | 8,226 | A single microservice, considered in isolation, is a small and cheap thing to write. |

## Data

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Polling Publisher](polling-publisher.md) | canonical | 6,038 | The context is the second half of the Transactional Outbox story, and it is worth stating precisely because Polling Publisher is frequently confused with the outbox pattern itself. |

## Data Integration

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Transaction Log Tailing](transaction-log-tailing.md) | canonical | 8,647 | A service owns a database, per the Database per Service pattern, and its database is private. |

## Data Query

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [API Composition](api-composition.md) | canonical | 9,045 | A client, whether a mobile app, a web frontend, or another service, needs a single response that draws on data owned by more than one microservice, and no single service holds all ... |

## Deployment

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Serverless Deployment](serverless-deployment.md) | established | 7,884 | A team owns a piece of business logic that is genuinely small and genuinely bursty. |
| [Service Deployment Platform](service-deployment-platform.md) | canonical | 7,181 | A team has decomposed an application into a set of independently deployable services, following one of the decomposition patterns in this family, and has chosen how a single ... |
| [Service Instance per Container](service-instance-per-container.md) | canonical | 8,926 | A team is moving an application, or building a new one, on top of microservices, and has to decide the packaging and scheduling unit for each service instance. |
| [Service Instance per Host](service-instance-per-host.md) | established | 7,761 | You have already decomposed a system into services, and each service runs as one or more service instances for throughput and redundancy, the same starting context Richardson ... |
| [Service Instance per VM](service-instance-per-vm.md) | established | 9,283 | A team has already split a system into microservices, one deployable unit per business capability, following the Microservice Architecture pattern. |

## Deployment and Discovery

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Third Party Registration](third-party-registration.md) | canonical | 8,071 | A caller wants to invoke a service that runs as more than one instance, and those instances are not static. |

## Domain Modeling

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Aggregate](aggregate.md) | canonical | 8,793 | A service, whether a monolith module or a microservice, owns a piece of the domain that contains more than one related object, and some of the rules that govern that piece span ... |

## Integration

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Shared Database](shared-database.md) | contested | 6,110 | A codebase is being decomposed into services, or several teams are building services that need to see overlapping pieces of business data. |

## Microservices

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [API Gateway](api-gateway.md) | canonical | 7,645 | A client of a microservices system, whether a mobile app, a single-page web application, or a third-party integration, needs data or an action that in a monolith would have been a ... |
| [Self Registration](self-registration.md) | canonical | 6,007 | A service instance's network location changes on every deployment, every autoscaling event, and every crash-and-restart. |
| [Server-Side Service Discovery](server-side-service-discovery.md) | canonical | 7,771 | A service instance's network address is not static. |
| [Service Registry](service-registry.md) | canonical | 6,188 | A service instance in a cloud environment does not have a fixed network location. |

## Reliability

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Idempotent Consumer](idempotent-consumer.md) | canonical | 6,810 | A service consumes messages or events from a broker, whether that is Kafka, Amazon SQS, RabbitMQ, Azure Service Bus, Google Pub/Sub, or an HTTP webhook delivered by another ... |

## Structural

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Database per Service](database-per-service.md) | canonical | 7,094 | A team is decomposing a monolith into services, or is designing a new system as microservices from the start, per Decompose by Business Capability or Decompose by Subdomain. |
| [Decompose by Business Capability](decompose-by-business-capability.md) | canonical | 6,765 | A team owns a monolith, or is building a new system, and needs to draw service boundaries. |
| [Decompose by Subdomain](decompose-by-subdomain.md) | established | 7,192 | A team owns a system that has grown past the point where one deployable, one shared database, and one release train can move at the speed the business needs. |
| [Self-Contained Service](self-contained-service.md) | established | 6,998 | A team owns a piece of business capability end to end, say "product catalog" or "checkout" or "order history", and wants to release a change to that capability without asking ... |
| [Service Mesh](service-mesh.md) | established | 6,980 | A system decomposed into many independently deployable services, following Decompose by Business Capability or Decompose by Subdomain, replaces in-process method calls with ... |
| [Service per Team](service-per-team.md) | canonical | 7,510 | A system has been split into services, using Decompose by Business Capability or Decompose by Subdomain or simply by growing that way over years. |
| [Strangler Application](strangler-application.md) | canonical | 8,747 | A team owns a monolithic application that has become expensive to change. |
| [Transactional Outbox](transactional-outbox.md) | canonical | 7,548 | A service owns its own database, as the Database per Service pattern in this same family requires. |

## Reading order

Entries are independent. Each one names the patterns it composes with and
the patterns it conflicts with in dimension 13, so following those links
gives a better path than reading top to bottom.

Generated by `tools/gen-indexes.py`. Do not edit by hand.
