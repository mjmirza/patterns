# Family 11. Domain-Driven Design

Origin. Evans, Vernon

35 entries, 264,798 words. Every entry carries all 18
dimensions from [the entry contract](../../docs/ENTRY-TEMPLATE.md).

## Anti-pattern

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Big Ball of Mud](big-ball-of-mud.md) | canonical | 8,391 | A system starts small. One person, or a small team under real time pressure, writes code that solves the problem in front of them using whatever shortcut gets a working result ... |

## Architectural

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Layered Architecture](layered-architecture.md) | canonical | 8,385 | A system has several kinds of work happening inside it at once, work that talks to a person through a screen or an API, work that decides what the business rules say should ... |

## Behavioral

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Event Storming](event-storming.md) | established | 8,206 | A team is about to build software for a business domain nobody on the team fully understands alone. |
| [Process Manager](process-manager.md) | canonical | 8,296 | A business process spans more than one service, more than one aggregate, or more than one external system, and it cannot complete in a single local transaction. |

## Domain-Driven Design

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Aggregate](aggregate.md) | canonical | 7,789 | A domain model contains rules that span more than one object. |
| [Aggregate Root](aggregate-root.md) | canonical | 8,677 | A domain model accumulates Entities and Value Objects that reference one another. |
| [Application Service](application-service.md) | canonical | 7,949 | A rich domain model, built from entities, value objects, and aggregates that enforce their own invariants, still needs a caller. |
| [Domain Service](domain-service.md) | canonical | 7,032 | A team modeling a domain in an object-oriented style eventually meets an operation that genuinely spans more than one object and does not belong to either. |
| [Factory](factory.md) | canonical | 8,338 | A domain model accumulates two kinds of complexity as it grows. |
| [Module](module.md) | canonical | 7,323 | A domain model that stays in one undifferentiated pile of classes becomes unreadable long before it becomes incorrect. |
| [Repository](repository.md) | canonical | 6,783 | A domain layer needs to load and save the objects it works with, but the code that expresses business rules should not know whether an order lives in PostgreSQL, in a document ... |
| [Specification](specification.md) | canonical | 7,066 | A domain accumulates rules that decide whether an object qualifies for something. |
| [Value Object](value-object.md) | canonical | 7,547 | A domain model accumulates concepts that are not things, they are measurements, descriptions, or quantities. |

## Domain-Driven Design, Strategic

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Published Language](published-language.md) | canonical | 6,457 | Two or more bounded contexts need to exchange information, and at least one of the following is true. |

## Integration

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Anticorruption Layer](anticorruption-layer.md) | canonical | 7,220 | A team owns a domain model they have deliberately shaped to match the Ubiquitous Language of their Bounded Context, see patterns/11-domain-driven-design/ubiquitous-language.md and ... |

## Strategic

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Domain Storytelling](domain-storytelling.md) | established | 8,120 | A team building software for a business domain needs an accurate, shared picture of how work actually happens before it can decide what the software should do. |
| [Generic Subdomain](generic-subdomain.md) | canonical | 6,775 | A team building a real product spends real engineering time on things the business does not actually compete on. |
| [Ubiquitous Language](ubiquitous-language.md) | canonical | 6,581 | A software team building a system for a business domain sits between two worlds that speak differently about the same reality. |

## Strategic Design

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Bounded Context](bounded-context.md) | canonical | 6,827 | A software system of any real size accumulates more than one team, more than one department's worldview, and more than one legitimate meaning for the same word. |
| [Conformist](conformist.md) | canonical | 6,538 | Two bounded contexts need to exchange data or invoke each other's behaviour, and one of the two, the upstream, owns a model neither side is free to renegotiate. |
| [Context Canvas](context-canvas.md) | established | 7,622 | A team has decided, usually from an Event Storming session or from a Context Map already in hand, that a particular slice of the domain deserves its own bounded context. |
| [Context Map](context-map.md) | canonical | 7,312 | A system reaches a certain size and a certain number of contributing teams before a single, internally consistent domain model stops being achievable. |
| [Core Domain](core-domain.md) | canonical | 6,670 | A team building a non-trivial system faces a resource allocation problem long before it faces a technical one. |
| [Customer-Supplier](customer-supplier.md) | canonical | 7,914 | Any system large enough to be split across more than one Bounded Context, see the bounded-context entry in this repository, produces integration points where one context's model ... |
| [Open Host Service](open-host-service.md) | canonical | 9,358 | A bounded context that has real internal complexity attracts multiple downstream consumers over time. |
| [Partnership](partnership.md) | canonical | 7,024 | Two teams each own a Bounded Context, and the two Contexts must integrate, but neither team can honestly claim to be upstream of the other. |
| [Separate Ways](separate-ways.md) | canonical | 9,250 | A team splits a system into more than one Bounded Context for good reasons, because two departments' vocabularies genuinely diverge, because two teams cannot coordinate closely ... |
| [Shared Kernel](shared-kernel.md) | canonical | 7,408 | Two Bounded Contexts model a piece of the domain in a compatible way, not because either team designed it that way on purpose, but because the concept genuinely is the same ... |
| [Subdomain Discovery](subdomain-discovery.md) | established | 7,371 | A team about to build or re-architect a nontrivial system faces a boundary problem before it faces a single line of code. |
| [Supporting Subdomain](supporting-subdomain.md) | canonical | 6,681 | A team building a system of real size eventually owns far more functionality than any one part of the business actually differentiates on. |

## Structural

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Open Host Service and Published Language](open-host-service-and-published-language.md) | canonical | 6,483 | A bounded context that has valuable capability inside it eventually needs to expose that capability to other bounded contexts, and often to more than one. |

## Structural, Distributed Coordination

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Saga versus Process Manager](saga-versus-process-manager.md) | canonical | 8,377 | The concrete situation is this. A business operation spans more than one service, each service owns its own datastore, and no distributed transaction coordinator is available or ... |

## Tactical

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Domain Event](domain-event.md) | canonical | 7,792 | A codebase modeling a real domain accumulates behavior that has to happen "because something else happened," and that dependency keeps landing in the wrong place. |

## Tactical Modeling

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Domain Primitive](domain-primitive.md) | canonical | 7,263 | A codebase accretes validation logic at the edges and loses track of where the truth lives. |
| [Entity](entity.md) | canonical | 7,973 | Every large domain contains two very different kinds of things, and conflating them is one of the most common sources of subtle correctness bugs in business software. |

## Reading order

Entries are independent. Each one names the patterns it composes with and
the patterns it conflicts with in dimension 13, so following those links
gives a better path than reading top to bottom.

Generated by `tools/gen-indexes.py`. Do not edit by hand.
