---
name: Selective Consumer
slug: selective-consumer
family: 07-integration
category: Enterprise Integration
aliases: [Message Selector, Message Filter, Content-Based Consumer]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [message-filter, competing-consumers, datatype-channel, publish-subscribe-channel, content-based-router]
incompatible_with: []
verified: 2026-08-02
---

# Selective Consumer

## 1. Name, aliases, and lineage

The canonical name is Selective Consumer. It appears in Gregor Hohpe and Bobby
Woolf, *Enterprise Integration Patterns. Designing, Building, and Deploying
Messaging Solutions*, Addison-Wesley, 2003, in the Message Endpoints chapter,
under the heading "Selective Consumer". The book states the intent as letting a
message consumer filter the messages delivered by its channel so that it only
receives the ones matching its criteria (Hohpe and Woolf, *Enterprise
Integration Patterns*, 2003, Selective Consumer, also summarised on the
companion site at
https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessageSelector.html,
verified 2026-08-02, which mirrors the book's wording and is maintained by the
authors).

The pattern goes by several names across the ecosystems that implement it,
and the naming choice tracks which side of the wire the vendor is describing.
The Java Message Service specification calls the mechanism a message
selector, a string parameter passed when a `MessageConsumer` is created that
the provider evaluates before delivery. Jakarta Messaging 3.1 keeps the same
term, describing message selection in section 3.8, "Message selection", where
it states that "message selection allows a client to specify, by means of a
message selector, which messages it is interested in receiving" (Eclipse
Foundation, *Jakarta Messaging Specification*, version 3.1, section 3.8,
https://jakarta.ee/specifications/messaging/3.1/jakarta-messaging-spec-3.1,
verified 2026-08-02). The enterpriseintegrationpatterns.com companion page
lists Message Filter as an informal synonym in the same family of patterns,
though the book reserves a distinct entry for a related but different pattern
also named Message Filter, discussed under dimension 13. Content-Based
Consumer is a description used in integration middleware documentation for
the same idea when the filtering criteria are drawn from the message body
rather than from header metadata. It is not a name the GoF-adjacent EIP
catalog itself uses, and this entry treats it as a descriptive alias rather
than a distinct pattern.

The pattern sits in the Message Endpoints section of the EIP catalog, which
groups the patterns that describe how application code attaches to a
messaging system, alongside Competing Consumers, Message Dispatcher, and
Polling Consumer. Selective Consumer is the endpoint-side answer to a
producer-side problem, a channel carries more message variety than any one
consumer wants, and something has to narrow that stream down before
application code sees it.

## 2. Problem and context

A consuming application is attached to a message channel that carries a
heterogeneous stream. A single order-events topic might carry created,
updated, cancelled, and shipped events for every region a company operates
in. A single stock-price channel might publish every symbol on an exchange.
A single audit-log channel might carry events from every microservice in a
platform. Most consumers attached to a channel like this care about a narrow
slice of what flows through it.

Without a mechanism to narrow the stream at the point of delivery, the
consumer has exactly two bad choices. The first is to receive every message
and discard the ones it does not want inside application code, after the
network transfer, after deserialization, and after whatever business logic
runs before the discard check. This wastes bandwidth, wastes CPU on
deserializing messages nobody will act on, and pushes filtering logic into
every consumer that shares the channel, duplicated as many times as there are
consumers. The second bad choice is to split the single channel into many
narrow channels, one per message variant a consumer might want, which is the
Datatype Channel pattern taken to its limit. That works when the variants are
few and stable, and breaks down when the number of interesting slices grows
combinatorially, for example when a consumer wants orders from region EU
above 1000 euros and a second consumer wants orders from region US of any
value, because a channel-per-combination explosion is not a workable design.

The context that produces this problem has three recurring shapes. First, a
publish-subscribe channel broadcasting a domain event stream to many
subscribers, where each subscriber only cares about a subset of event types
or a subset of tenants. Second, a point-to-point work queue shared by workers
that specialise, for example a fulfilment queue where some workers only
process orders below a certain weight because they operate hand trucks and
others process anything because they operate forklifts. Third, a
multi-tenant system where one physical channel carries traffic for many
customers and a given consumer instance is only authorised, or only
provisioned, to see one customer's traffic.

Selective Consumer answers the question directly. Let the consumer state its
selection criteria when it attaches to the channel, and let either the
broker or a filtering layer evaluate those criteria before the message
reaches the consumer's business logic.

## 3. Forces

- Network and processing cost versus flexibility. Filtering as close to
  the producer as possible, ideally at the broker before serialization onto
  the wire to that consumer, saves bandwidth and CPU. Filtering deep inside
  the consumer's business logic costs the least engineering effort per
  consumer but wastes every resource the message consumed on its way there.
  Selective Consumer favours moving the filter earlier, at the cost of
  needing the broker or an intermediary to understand the selection
  language.
- Coupling to a selector language. A selector expressed in a query
  language such as JMS's SQL-92 subset couples the consumer to whatever
  syntax and whatever fields the broker exposes for filtering. Simpler
  approaches, matching a single header value or a routing-key pattern,
  sacrifice expressive power for a smaller coupling surface.
- Message design discipline. The pattern depends on the producer putting
  the right selection values into headers or a routable field, not buried
  inside an opaque payload the broker cannot inspect without deserializing
  it. This forces a design discipline on the producer side that a
  filter-in-consumer-code approach does not require, because filter-in-code
  can reach into the fully deserialized payload freely.
- Delivery guarantees under filtering. On a point-to-point channel, a
  message a Selective Consumer rejects still needs to go somewhere, either
  requeued for another consumer or dead-lettered. On a publish-subscribe
  channel every subscriber technically still receives the message unless the
  broker actively prunes delivery, so the pattern's efficiency payoff depends
  heavily on whether the specific broker technology supports server-side
  filtering or only client-side discard.
- Operability and debuggability. A message dropped silently by a selector
  because it did not match is invisible unless it is logged somewhere. This
  trades an easy-to-trace linear flow for a filtering step that a person
  debugging a "why didn't my consumer get message X" incident must know to
  look at.
- Fairness among competing consumers. Selective Consumer combined with
  Competing Consumers on the same point-to-point channel raises a starvation
  risk. If every competing consumer applies a narrow selector and a burst of
  messages arrives that only one selector matches, that one consumer is
  overloaded while its peers sit idle, defeating the load-balancing purpose
  Competing Consumers exists for.

The pattern favours reducing wasted work and cleanly separating what a
consumer wants from what it does with a message, and it sacrifices
simplicity of the delivery model and, in naive implementations, some
fairness guarantees.

## 4. Applicability and non-applicability

Reach for Selective Consumer when the following hold.

- A single physical channel legitimately carries more than one logical kind
  of message, and splitting into a channel per kind is impractical because
  the number of relevant slices is large, dynamic, or defined by a value
  rather than a type.
- The messaging technology in use exposes a selection mechanism that runs
  before full deserialization or before network transfer to the specific
  consumer, so filtering genuinely saves work rather than only moving the
  `if` statement.
- Different consumer instances of the same logical service need different
  subsets of the same stream, for example region-sharded workers, tenant-
  scoped workers, or workers specialised by message priority.
- The selection criteria are stable properties of the message, expressible
  as header values or as fields the broker can inspect, rather than the
  result of a computation the consumer must run over the full payload.
- The team wants filtering logic centralised in configuration, a selector
  string or a binding pattern, rather than scattered as `if` statements
  across every consumer that shares the channel.

Do NOT reach for Selective Consumer in these cases.

- There is only one product and no plausible second kind of message on the
  channel. There is nothing to select. A plain consumer on a Datatype
  Channel is simpler and has no selector expression to maintain.
  Introducing a selector here is speculative generality with an extra
  moving part and no payoff.
- The filtering criterion requires business logic beyond simple
  comparisons. JMS-style selectors support a restricted SQL-92 expression
  subset. A criterion such as "route to the consumer whose current load is
  lowest" or "select messages whose payload, once parsed, satisfies a
  five-step validation" cannot live in a selector string and belongs in
  application code or in a Content-Based Router placed ahead of the
  consumer.
- Every consumer on the channel needs every message, just processed
  differently per type. That is a dispatch problem inside one consumer, not
  a selection problem between consumers. A Message Dispatcher or a plain
  type switch inside the handler is the honest shape. Wrapping it in a
  selector adds indirection with no filtering benefit since nothing is
  actually excluded.
- The broker or client library provides no server-side filter and the
  team implements the pattern purely as an `if` at the top of the handler.
  This is not wrong, and the EIP catalog explicitly allows client-side
  discard on publish-subscribe channels as a valid, if less efficient,
  implementation. But at that point the benefit is limited to code
  organisation, not resource savings, and a simpler guard clause may be all
  that is warranted rather than formalising it as a named pattern with its
  own selector-string maintenance burden.
- Ordering guarantees for the full stream matter to the consumer. A
  selector that skips non-matching messages can, depending on the broker,
  leave gaps that make it harder to reason about relative ordering between
  matched and unmatched messages if the consumer ever needs to correlate
  them. Where strict total ordering across the whole stream matters, filter
  after consuming in order rather than at the selector layer.
- The selection criteria change extremely frequently, on the order of
  per-request. Broker-side selectors are typically bound once when a
  consumer subscribes. A selector that must be recomputed and rebound for
  every message defeats the purpose and belongs in application logic or a
  Content-Based Router instead.

## 5. Structure

- Message Channel. The shared conduit, point-to-point or
  publish-subscribe, carrying a heterogeneous stream of messages.
- Specifying Producer. The role a message producer plays when it attaches
  selection values, typically as headers or properties, that a downstream
  Selective Consumer can filter on. The producer does not need to know which
  consumers exist or what they will select for. It only needs to populate
  the fields consistently.
- Selection Value. The header, property, or routable field a Selective
  Consumer's criteria are evaluated against. This is metadata attached to
  the message envelope, kept separate from the opaque payload so it can be
  inspected without full deserialization.
- Selective Consumer. The consumer that supplies a selector, a predicate
  over Selection Values, when it attaches to the channel. Only messages
  whose Selection Values satisfy the predicate are delivered to, or retained
  by, this consumer.
- Filtering point. The place the predicate is actually evaluated. In a
  broker-native implementation this is the broker itself, before the message
  crosses the wire to this specific consumer. In a client-side
  implementation this is a thin layer inside the consumer, immediately after
  receipt and before the message reaches business logic. The EIP catalog
  treats both as valid realisations of the same pattern. The structural
  difference is only where the box labelled "filter" sits relative to the
  network boundary.

## 6. ASCII structure diagram

```
                          +---------------------+
                          |  Specifying Producer |
                          |  (sets Selection      |
                          |   Values on message)  |
                          +----------+-----------+
                                     |
                                     v
                          +---------------------+
                          |   Message Channel    |
                          | (point-to-point  or   |
                          |  publish-subscribe)   |
                          +----------+-----------+
                                     |
              +----------------------+----------------------+
              |                      |                       |
              v                      v                       v
   +-------------------+  +-------------------+   +-------------------+
   | Selective Consumer |  | Selective Consumer |   | Selective Consumer |
   | selector:           |  | selector:           |   | selector:           |
   |  region = 'EU'      |  |  region = 'US'      |   |  priority > 5       |
   |-------------------|  |-------------------|   |-------------------|
   | [filter point]      |  | [filter point]      |   | [filter point]      |
   | evaluates Selection |  | evaluates Selection |   | evaluates Selection |
   | Values, discards or |  | Values, discards or |   | Values, discards or |
   | never receives a    |  | never receives a    |   | never receives a    |
   | non-matching message|  | non-matching message|   | non-matching message|
   +---------+-----------+  +---------+-----------+   +---------+-----------+
             |                        |                         |
             v                        v                         v
     business logic          business logic            business logic
     sees only EU orders     sees only US orders        sees only priority>5

   On a broker-native selector, the filter point sits inside the broker,
   before delivery. On a client-side selector, it sits inside the consumer,
   after receipt and before dispatch to business logic.
```

## 7. Dynamics

The runtime flow differs depending on whether the filter point is broker-side
or client-side. Both are shown, because the choice materially changes where
the wasted work goes.

```
Broker-side selector (JMS-style, filter evaluated by the provider)

Producer          Broker                  Consumer A          Consumer B
   |                 |                    (selector:            (selector:
   |                 |                     region='EU')          region='US')
   |-- publish ----->|                        |                     |
   | (region=EU)     |-- evaluate selector -->|                     |
   |                 |    against A: match    |                     |
   |                 |-- deliver ------------>|                     |
   |                 |                        |-- process --------->|
   |                 |                        |                     |
   |                 |-- evaluate selector -->|                     |
   |                 |    against B: no match |                     |
   |                 |   (never sent to B)    |                     |
   |                 |                        |                     |

   B never receives the bytes for the EU message. No deserialization,
   no network transfer to B occurred for that message.
```

```
Client-side selector (publish-subscribe fan-out, filter evaluated by consumer)

Producer          Broker                  Consumer A          Consumer B
   |-- publish ----->|                        |                     |
   | (region=EU)     |-- fan out to all  ---->|                     |
   |                 |   subscribers   ------------------------------>|
   |                 |                        |                     |
   |                 |                        |-- check selector -->|
   |                 |                        |   region='EU': match|
   |                 |                        |-- dispatch to  ---->|
   |                 |                        |   business logic    |
   |                 |                        |                     |-- check selector
   |                 |                        |                     |   region='EU': no
   |                 |                        |                     |   match, discard
   |                 |                        |                     |   silently
```

The broker-side variant saves the wire transfer and deserialization cost for
the non-matching consumer. The client-side variant still pays those costs for
every consumer, and only saves the cost of running business logic on the
discarded message. Both variants share one operability property. A discarded
message leaves no trace unless the filtering step explicitly logs it, which
is the source of the most common failure mode in dimension 11.

## 8. Implementation variants

JMS and Jakarta Messaging message selector. A SQL-92-like string, for
example `region = 'EU' AND priority > 5`, passed as an argument when a
`MessageConsumer` is created, evaluated by the provider against message
header fields and application-set properties (Eclipse Foundation, *Jakarta
Messaging Specification*, version 3.1, section 3.8.1, verified 2026-08-02).
This is the canonical broker-side, string-expression form the EIP catalog was
written against, and the reference form most later implementations echo in
spirit if not in syntax.

Topic exchange routing-key pattern (AMQP, RabbitMQ). The producer sets a
dot-delimited routing key, for example `orders.eu.created`, and each consumer
binds its queue to a topic exchange with a pattern using `*` for exactly one
word and `#` for zero or more words. RabbitMQ's own tutorial states that "a
message sent with a particular routing key will be delivered to all the
queues that are bound with a matching binding key" (RabbitMQ, "RabbitMQ
tutorial 5, topics",
https://www.rabbitmq.com/tutorials/tutorial-five-python.html, verified
2026-08-02). This is a broker-side variant, but the selection language is a
structured hierarchical string rather than a general expression, which
trades expressive power for a routing table the broker can index cheaply.

Attribute-based subscription filter policy (AWS SNS, cloud pub-sub
services). The subscriber attaches a JSON filter policy against message
attributes or, in newer scopes, against the message body itself. AWS states
that "if a subscription doesn't have a filter policy, the subscriber
receives every message published to its topic," and that Amazon SNS compares
attributes or body properties against the policy per subscription before
deciding to deliver (AWS, "Amazon SNS message filtering",
https://docs.aws.amazon.com/sns/latest/dg/sns-message-filtering.html, verified
2026-08-02). This is a declarative, structured-condition variant, broker
side, aimed at cloud-native fan-out topologies with many heterogeneous
subscribers.

Header predicate at the client, checked immediately on receipt. A
lightweight variant with no broker cooperation. The consumer receives every
message the channel delivers and evaluates a predicate function against
headers before dispatching to business logic, discarding non-matches
immediately. This is the shape most application frameworks fall into when
the broker offers no native selector, or when the team wants portability
across brokers rather than a broker-specific selector string.

Consumer-group partition assignment as an implicit selector. In
partitioned log systems such as Kafka, a consumer within a consumer group is
assigned a subset of partitions by the group coordinator, and if the
producer partitions by a key correlated with the selection criterion, for
example partitioning by tenant ID, each consumer instance implicitly
receives only messages for its assigned tenants without an explicit selector
expression at all. This is a structural variant rather than an expression
based one. The filtering happens through partition assignment, not through
evaluating a predicate per message, and it is the shape favoured when strict
per-key ordering must be preserved, since a JMS-style selector gives no
ordering guarantee across the messages it skips.

Content-Based Router placed ahead of dumb consumers. Instead of teaching
each consumer to select, a single router component upstream inspects each
message and forwards it to one of several downstream channels, each of
which is a Datatype Channel that a plain, non-selective consumer reads. This
achieves the same outcome, isolation of a consumer from message variants it
does not want, by moving the selection logic to a distinct component rather
than to the endpoint itself. The EIP catalog treats Content-Based Router as
a related pattern rather than an implementation variant of Selective
Consumer, and this entry follows that distinction in dimension 13, but it is
worth naming here because teams often reach for one when they meant the
other.

## 9. Known production uses

Jakarta Messaging (formerly Java Message Service), message selectors.
Every compliant provider, including Apache ActiveMQ Artemis and the
reference implementation shipped with Jakarta EE application servers, must
support message selectors as a standard `MessageConsumer` creation argument.
The specification devotes section 3.8 to "Message selection" and states that
selectors let a client "specify, by means of a message selector, which
messages it is interested in receiving" (Eclipse Foundation, *Jakarta
Messaging Specification*, version 3.1, section 3.8,
https://jakarta.ee/specifications/messaging/3.1/jakarta-messaging-spec-3.1,
verified 2026-08-02). This is the reference production use the EIP catalog
itself was written against.

RabbitMQ topic exchanges. RabbitMQ's own tutorial series documents topic
exchanges as the mechanism for selective, pattern-based consumption from a
single logical exchange, with the `*` and `#` wildcard operators forming the
selector language, and states that binding a queue with `#` alone "can behave
like other exchanges", specifically a fanout exchange that delivers
everything, showing the pattern degrades gracefully to the no-selection case
(RabbitMQ, "RabbitMQ tutorial 5, topics",
https://www.rabbitmq.com/tutorials/tutorial-five-python.html, verified
2026-08-02).

Amazon SNS subscription filter policies. AWS's own documentation for
message filtering on SNS topics describes exactly the Selective Consumer
structure. A Specifying Producer publishes message attributes, a broker
evaluates a per-subscription filter policy, and delivery is gated on the
match. AWS states "Amazon SNS compares the message attributes or the message
body to the properties in the filter policy for each of the topic's
subscriptions" before deciding whether to deliver (AWS, "Amazon SNS message
filtering",
https://docs.aws.amazon.com/sns/latest/dg/sns-message-filtering.html,
verified 2026-08-02).

Spring's `@JmsListener` selector attribute. The Spring Framework's JMS
listener annotation exposes a `selector` attribute that is passed straight
through to the underlying `MessageConsumer` creation call, so a Spring bean
can declare `@JmsListener(destination = "orders", selector = "region =
'EU'")` and have the container wire up a Selective Consumer without the
developer touching the JMS API directly. Spring Framework reference
documentation for the `jms` module documents the `selector` element on the
`<jms:listener>` XML configuration and the equivalent annotation attribute as
being forwarded to the JMS provider's selector mechanism (VMware Tanzu,
*Spring Framework Reference Documentation*, JMS integration, "Annotation-
driven listener endpoints", section on `@JmsListener` attributes, current at
https://docs.spring.io/spring-framework/reference/integration/jms.html,
verified 2026-08-02). This is a framework-level production use showing the
pattern surfacing as a first-class annotation attribute rather than a raw
API call, evidence the pattern is common enough to warrant dedicated
framework support.

## 10. Consequences

Positive.

- Application code that consumes a shared channel no longer needs to
  implement discard logic for every message shape it does not care about.
  The discard happens before the message reaches business logic, or before
  it reaches the consumer at all.
- A single physical channel can carry a heterogeneous stream without forcing
  a Datatype Channel per variant, which keeps the number of physical
  channels, and the operational surface of managing them, small even as the
  number of logical message kinds grows.
- Where the broker supports server-side selection, network and
  deserialization cost for non-matching messages is eliminated for that
  consumer, which matters directly for cost and latency at scale.
- Selection criteria live in a declarative selector string, a routing
  pattern, or a filter policy, rather than scattered as conditional logic
  inside handler methods, which centralises the criteria somewhere a
  reviewer or an operator can read without opening the consumer's source.
- New consumer variants can attach to the existing channel with a new
  selector and start receiving a slice of the existing stream without any
  change to the producer or to other consumers, which is an Open Closed
  Principle payoff applied to message routing.

Negative.

- A message a Selective Consumer's criteria reject leaves no trace by
  default. Diagnosing why a consumer did not receive a message requires
  either broker-level tracing or an explicit dead-letter or audit path,
  neither of which the pattern provides on its own.
- On a point-to-point channel with Competing Consumers applying different
  selectors, load balancing is no longer guaranteed. A burst of messages
  matching only one selector overloads that one consumer while its siblings
  idle, and the EIP catalog names this combination explicitly as a case
  requiring care.
- Selector expressiveness is bounded by whatever the broker's query language
  supports. JMS's SQL-92 subset, for instance, has no support for evaluating
  against a deserialized payload structure, only against headers and
  application-set properties, which forces message design discipline onto
  the Specifying Producer.
- A selector string or routing pattern is untyped and unchecked at compile
  time in most implementations, so a typo in a field name or a routing
  segment silently produces zero matches rather than a build error, and the
  failure surfaces only as an absent stream of expected messages, an
  absence rather than a positive signal.
- Every selector adds a piece of stateful configuration, bound at consumer
  startup in most broker-native implementations, that must be kept
  consistent with the message header schema the producer emits. A header
  rename on the producer side silently breaks every selector referencing the
  old name.

## 11. Failure modes and misuse

The silent black hole. Symptom. A consumer team reports that expected
messages never arrive, with no error, no exception, and nothing in the
consumer's own logs, because nothing ever reached the consumer to log.
Cause. A typo or a stale field name in the selector expression, or a
producer-side header rename that was not propagated to every consumer's
selector string. Fix. Log or trace at the broker or filter-point level when
messages are evaluated and rejected, at least at a sampled rate, and add an
automated check that every deployed selector references a header name the
current producer schema actually emits.

Competing consumers with disjoint selectors starving one another. Symptom.
One worker instance in a pool is pegged at high CPU and its queue depth
climbs, while sibling instances in the same consumer pool sit idle with
their queues empty. Cause. Each competing consumer was given a distinct,
narrow selector for load-partitioning purposes, but the actual traffic mix
shifted so one selector's slice now dominates the incoming stream. Fix.
Either widen the selectors so more than one consumer can serve the hot
slice, switch to selector-free Competing Consumers with the discrimination
moved to a Content-Based Router upstream that can rebalance dynamically, or
move to partition-based implicit selection with a partition key chosen to
spread load evenly, per dimension 8.

Selector evaluated too late to save anything. Symptom. A team adopts a
selective-consumer approach expecting bandwidth or CPU savings, and
observes no measurable improvement in network usage or deserialization time.
Cause. The selector is implemented as a client-side `if` after full message
receipt and deserialization, on a broker that offers no server-side
filtering, so every byte and every parse still happens for every message on
every consumer. Only the business-logic dispatch was actually avoided. Fix.
Confirm ahead of adoption whether the specific broker supports server-side
selection at all. If it does not, treat the pattern as a code-organisation
choice, not a performance optimisation, and set expectations accordingly.

Selector coupling breaking on a routine schema change. Symptom. A
deployment of the producer service silently breaks every selective consumer
attached to a shared topic, with no deploy-time error on either side, only a
slow drop in message delivery to the affected consumers discovered hours
later. Cause. A field the selectors depend on was renamed, retyped, or moved
from a header into the message body during an unrelated refactor of the
producer, and nothing enforced that selector expressions and producer schema
stay in lockstep. Fix. Treat Selection Values as a versioned, published
contract, with the same change-management discipline as a public API field,
and add a consumer-side canary or integration test that asserts a known
selector still matches a known sample message after every producer
deployment.

Overreliance on the selector as the only access control. Symptom. A
subscriber that should not see a particular tenant's data receives it
anyway, discovered during a security review rather than through an
exception. Cause. The selector was treated as an authorisation mechanism,
restricting which messages a consumer can act on, when it is only a
filtering convenience the consumer itself supplied and can change or remove
at will. A malicious or misconfigured consumer can simply omit the selector
and receive the full unfiltered stream if the broker enforces no separate
access control on the channel. Fix. Enforce tenant or sensitivity boundaries
with channel-level authorisation or channel partitioning, per Datatype
Channel or a dedicated per-tenant channel, and treat the selector purely as
an efficiency and convenience mechanism layered on top of, never as a
substitute for, real access control.

Selector expression injection. Symptom. A consumer that builds its
selector string dynamically from user input, for example a UI field letting
a support engineer type a free-text filter, is found to accept a crafted
input that widens the selector far beyond its intended scope. Cause. Selector
strings are typically evaluated as a restricted query language, and
concatenating unsanitised input into that string is structurally the same
mistake as building SQL by string concatenation. Fix. Never build selector
strings from unsanitised external input. Use a parameterised or templated
approach if the broker's client library offers one, and validate any
user-influenced selector fragment against an explicit allow-list before it
is submitted to the broker.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Selective Consumer | Datatype Channel per variant | Content-Based Router upstream | Client-side `if` in a plain consumer | Message Filter |
|---|---|---|---|---|---|
| Wasted work on non-matching messages | Low, when broker-side; unchanged from plain consumer when client-side | Zero, by construction, since each channel already carries one kind | Low, router discards before the downstream channel | High, full receipt and deserialization always occurs | Low to zero, discarded at the filter step before the channel |
| Number of physical channels required | One, shared | One per message variant, can grow large | Two or more, one per route | One, shared | One in, one out, plus a discard sink |
| Coupling to a selector language | Medium to high, depends on broker query syntax | None | Low, routing logic is regular code, not a broker query string | None | None, filtering logic is regular code |
| Where selection logic lives | Declarative, bound at consumer subscribe time | Implicit, by channel choice at publish time | Centralised in the router component | Scattered inside each consumer's handler | Centralised in the filter component |
| Load balancing under Competing Consumers | Can starve if selectors are disjoint and traffic skews | Not applicable, each channel already has its own consumer pool | Router can rebalance downstream channel assignment dynamically | Preserved, since all consumers see all messages before discarding | Not applicable, upstream of any competing pool |
| Debuggability of a missing message | Poor by default, requires explicit tracing at the filter point | Good, the message either is or is not on the channel it was expected on | Good if the router logs its routing decision | Good, the discard happens visibly inside application code and logs | Good if the filter component logs discards |
| Cost of adding a new consumer variant | Low, new selector, no producer or peer changes | High, may require a new channel and producer change | Medium, new route and possibly a new downstream channel | Low, new handler code, but duplicates filtering logic per consumer | Medium, extends or forks the filter's criteria |
| Suited to strict cross-message ordering guarantees | Poor for general expression selectors; good for partition-key based implicit selection | Good, each channel preserves its own order | Depends on router implementation | Good, since nothing is skipped before the consumer sees it in order | Depends on filter implementation |

Reading of the table. Selective Consumer wins when the number of relevant
message slices is large or dynamic and the broker offers real server-side
filtering, so the savings are structural rather than cosmetic. Datatype
Channel wins when the variant set is small, stable, and known in advance.
Content-Based Router wins when the selection logic itself needs to be more
expressive than a broker query language allows, or needs central, dynamic
rebalancing. A client-side `if` in a plain consumer wins when there is
exactly one consumer and formalising a pattern around a single guard clause
would be over-engineering. Message Filter, discussed in dimension 13, is the
closest sibling and differs mainly in where the filtering component sits
architecturally rather than in the mechanics of filtering itself.

## 13. Related and incompatible patterns

- Message Filter. The closest sibling, and frequently conflated with
  Selective Consumer because both discard non-matching messages. The EIP
  catalog treats Message Filter as a distinct pattern, a pipeline component
  placed between a producer and a channel, or between two channels, that
  evaluates a criterion and either forwards a message or drops it entirely,
  independent of any particular consumer's identity. Selective Consumer,
  by contrast, is defined from the consumer's point of view. The criterion
  belongs to a specific consumer instance, and other consumers on the same
  channel may still receive the message unfiltered. A useful test, if
  removing one consumer changes what a different consumer sees, it is
  Selective Consumer. If the filtering happens once for everyone downstream,
  it is Message Filter.
- Datatype Channel. An alternative rather than a composition partner in
  most cases. Where Selective Consumer narrows a heterogeneous channel per
  consumer, Datatype Channel narrows it structurally by splitting the
  channel itself. The two can combine. A system might split by broad
  category into a handful of Datatype Channels and then apply a Selective
  Consumer within each channel for finer-grained slicing, for example a
  channel per event type with a selector per region inside each.
- Content-Based Router. A structurally similar mechanism placed
  upstream of the channel rather than at the consumer's point of attachment.
  The two solve the same problem from opposite ends. Content-Based Router
  decides where a message goes before it lands on any channel. Selective
  Consumer decides what a specific consumer accepts after the message has
  already landed on a shared channel. A system with many consumers and
  simple, stable routing criteria tends to favour a router. A system with
  few consumers and criteria that vary per consumer, or criteria that change
  without a deployment, tends to favour Selective Consumer.
- Competing Consumers. Composes, with the caveat named in dimension 11.
  Selective Consumer is frequently layered on top of Competing Consumers to
  give a pool of workers specialised subsets of the workload, but the
  combination requires the selector distribution to track the actual
  traffic distribution or one competing consumer starves while another
  idles.
- Publish-Subscribe Channel. The natural host for the client-side
  variant. The EIP catalog states explicitly that on a publish-subscribe
  channel every subscriber technically receives every message and a
  Selective Consumer simply ignores the copies it does not want, which is
  the shape most publish-subscribe implementations without native filtering
  fall into.
- Point-to-Point Channel. The natural host for the broker-side variant
  when combined with Competing Consumers, since only one consumer among the
  pool ultimately receives any given message and a selector determines which
  one is eligible.
- Idempotent Receiver. A useful companion rather than a conflict. Because
  selector expressions are typically evaluated by the broker as an
  approximate, sometimes eventually-consistent filter in distributed broker
  deployments, a small number of non-matching messages can occasionally slip
  through depending on the broker's consistency model. A consumer that
  additionally validates the selector criterion in application code, and
  is otherwise built as an Idempotent Receiver, tolerates that edge case
  gracefully.
- Message Selector as an access-control substitute. Actively conflicts,
  as covered in dimension 11. A selector is a convenience filter the
  consumer itself controls, never an authorisation boundary, and treating it
  as one is a misuse rather than a legitimate variant.

## 14. Refactoring path in and out

Introducing the pattern into a system where a consumer currently discards
unwanted messages deep inside its business logic.

1. Identify every place inside the consumer's handling code where a message
   is received, inspected, and then explicitly ignored or short-circuited
   based on a value already present in the message's headers or a small set
   of top-level fields. Confirm the discard decision genuinely depends only
   on values available before the full payload needs parsing. If it depends
   on parsed payload content, this refactoring does not apply, see
   dimension 4.
2. Confirm the producer already sets those values as headers or application
   properties on the message envelope, not only inside the serialized body.
   If it does not, this is the point to add a Specifying Producer step, set
   the relevant fields as headers at publish time, without changing the
   payload shape or breaking existing consumers that ignore the new headers.
3. Extract the discard condition into an explicit selector expression or
   predicate, matching the broker's native selector syntax if one exists, or
   as a standalone predicate function if it does not. Keep the discard
   behaviour identical for now. Run the existing test suite to confirm no
   behaviour changed.
4. Where the broker supports native selectors, move the extracted predicate
   into the consumer's subscription call as a selector string, and delete
   the now-dead discard branch from the handler body. Where it does not,
   leave the predicate as an early-return guard clause at the top of the
   handler, clearly separated from business logic, and consider this the
   stopping point. Formalising further without broker support adds
   ceremony without payoff.
5. Add explicit logging or a metric at the discard point, whether broker-
   native or client-side, so the silent-black-hole failure mode from
   dimension 11 is observable from day one rather than discovered later
   during an incident.
6. If several consumers on the same channel each extracted a similar
   predicate in step 3, consider whether the criteria are stable and shared
   enough to warrant promoting them to a Content-Based Router upstream
   instead, per dimension 13, rather than maintaining near-duplicate
   selector strings across consumers.

Removing the pattern when it stops earning its place. Signals include a
selector that has matched one hundred percent of traffic for a long period,
meaning the underlying variance it was built to filter no longer exists, or
a channel that has been split into per-variant Datatype Channels for other
reasons, making the selector redundant.

1. Confirm, using the observability metrics from dimension 16, that the
   selector's match rate has been effectively total for a representative
   period, not merely quiet during a low-traffic window.
2. Remove the selector expression from the consumer's subscription call, or
   delete the client-side guard clause, and add an explicit comment or
   changelog entry stating why, referencing the match-rate evidence, so a
   future reader does not wonder if the removal was an oversight.
3. Watch the discard metric, or its absence, for a full traffic cycle after
   removal to confirm no previously-filtered traffic reappears unexpectedly.
4. If the Selection Values were added to the message schema solely to
   support the now-removed selector and serve no other consumer, consider
   deprecating those header fields on the producer side as a separate,
   later change, following the producer's own schema evolution policy
   rather than removing them in the same change as the consumer-side
   cleanup.

## 15. Testing and verification

Easier because of the pattern.

- A consumer's business logic can be tested completely independently of the
  filtering concern, by constructing test messages that already satisfy the
  selector and asserting only on the handler's behaviour, since the filter
  is a separate concern evaluated before the handler ever runs.
- The selector expression itself, when expressed as a standalone predicate
  or a broker query string, becomes independently testable against a table
  of sample messages, matching and non-matching, without standing up the
  handler at all.
- Where the selector is a client-side predicate function, ordinary unit
  testing applies directly with no messaging infrastructure required.

Harder because of the pattern.

- Broker-native selector strings are typically not type-checked or
  validated until a message is evaluated against them at runtime, so a
  syntax error or a stale field reference in the selector often only
  surfaces as a silently empty consumer, not as a test failure at build
  time, unless the test suite specifically exercises the selector against
  a live or emulated broker.
- Integration testing a Selective Consumer honestly requires exercising the
  real filtering mechanism, not a mock, because the interesting failure
  modes, wrong field name, wrong operator precedence, unexpected null
  handling, live inside the broker's evaluation of the selector string
  itself, which a unit test of the handler alone cannot catch.

Techniques that apply.

- Selector contract test, run against a real or embedded broker. A test
  that publishes a small, fixed table of sample messages, some intended to
  match and some intended not to, and asserts the deployed selector accepts
  exactly the matching set. Run this on every deployment, not only once at
  authoring time, so a producer-side schema drift is caught the moment it
  breaks the selector, per the failure mode in dimension 11.
- Predicate unit test for client-side variants. A plain unit test over
  the extracted predicate function using representative headers, covering
  the boundary cases the selector expression is meant to distinguish, for
  example a priority exactly at the threshold value.
- Discard observability test. An integration test that publishes a
  deliberately non-matching message and asserts that the discard metric or
  log line from dimension 16 actually fires, so the observability
  instrumentation itself does not silently rot.
- Starvation simulation for competing selective consumers. A load test
  that varies the mix of matching traffic across several selectors on a
  shared point-to-point channel and asserts queue depth and processing
  latency stay within bounds for every consumer, catching the starvation
  failure mode from dimension 11 before it appears in production traffic.

## 16. Observability signals

The filtering step is, by construction, the point in the system where
information about a message quietly disappears from one consumer's view, so
it needs its own dedicated telemetry or that disappearance is invisible.

What to record.

- A counter of messages evaluated against a given selector, labelled by
  match versus discard outcome, per consumer. This is the single most
  useful signal. The match rate over time tells an operator whether the
  selector is still doing meaningful work or has drifted to matching
  everything or nothing.
- For broker-native selectors where the broker itself exposes per-
  subscription delivery counts, correlate the broker's reported delivered
  count against the channel's total published count to derive an effective
  match rate without instrumenting the consumer at all.
- A log line, at debug level for high-frequency channels and info level for
  low-frequency ones, recording the selection values of a discarded message
  when discard is happening client-side, so a support engineer can search
  logs to answer whether message X even reached consumer Y's filter step.
- For the Competing Consumers combination, a per-consumer queue depth or
  processing lag gauge, so the starvation failure mode from dimension 11
  shows up as a visible divergence between sibling consumers on a dashboard
  rather than as a slow, silent backlog.
- A counter of selector evaluation errors, for brokers where a malformed
  selector string produces a runtime error rather than a silent zero-match
  result, so a schema drift that breaks selector syntax is caught
  immediately rather than only through the absence of expected traffic.

A healthy instance on a dashboard. The match rate for each selector sits in
a stable band consistent with the known traffic mix, moving only when a
deployment or a deliberate traffic-shape change explains the shift. Queue
depth or processing lag is roughly even across sibling competing consumers
sharing disjoint selectors on the same channel. The selector evaluation
error counter stays at zero.

A failing instance. A selector's match rate drops to zero with no
corresponding change in overall published traffic, pointing at the silent
black hole failure mode. One competing consumer's queue depth climbs while
its siblings' stay flat, pointing at the starvation failure mode. The
selector evaluation error counter, where the broker exposes one, moves off
zero right after a producer deployment, pointing at a broken selector
contract from a schema change.

## 17. Security and privacy implications

The pattern carries a genuine, specific security implication rather than
being neutral, unlike some structural patterns where inventing a concern
would be dishonest.

The access-control misuse. As covered in dimension 11, a selector is a
filter the consumer itself declares and controls, not a boundary the
producer or the broker enforces on the consumer's behalf in most
implementations. A consumer that omits or widens its own selector can, in
the general case, receive the full unfiltered stream a channel carries,
including messages intended for a different tenant, a different region, or a
different sensitivity tier. Treating a selector as sufficient tenant
isolation is a genuine and recurring production mistake, not a hypothetical
one. Teams that need real isolation should enforce it with channel-level
access control, per-tenant channels, or broker authorisation policies that
the consumer cannot bypass by changing its own subscription parameters.

Selector expression injection. Where a selector string is built by
concatenating externally influenced input, an operator typing a free-text
filter, a value derived from a query parameter, the same class of injection
risk that applies to building SQL by string concatenation applies here,
because JMS-style selectors are evaluated as a restricted SQL-92 expression
language against the broker. An attacker able to influence the selector
string could, depending on the broker's implementation, widen the selector
far beyond its intended scope or, in a poorly-hardened broker, attempt to
exploit parser edge cases. Treat externally-influenced selector fragments
with the same discipline as parameterised SQL. Validate against an
allow-list of known field names and operators before submission, and never
concatenate raw external input into a selector string.

Selection values as leaked metadata. Because Selection Values live in
message headers or properties rather than inside an encrypted or otherwise
protected payload, and because the whole point of the pattern is that the
broker or an intermediary must be able to inspect them without full
decryption of the body, any sensitive value used as a Selection Value is, by
construction, visible to the broker and to any component with access to the
channel's metadata, even where the payload itself is end-to-end encrypted.
A team that end-to-end encrypts payloads but routes on a customer identifier
or a personal attribute placed in the clear as a Selection Value has
reintroduced exactly the exposure the encryption was meant to close. Where a
routing criterion is itself sensitive, use a tokenised or hashed
representation as the Selection Value rather than the raw sensitive field.

On denial of service, the pattern is mildly protective rather than a new
exposure surface. Because a well-implemented broker-side selector discards
non-matching messages before delivery, a flood of traffic aimed at other
consumers on the same shared channel does not, by itself, add load to a
consumer whose selector correctly excludes it, which is a genuine, if
secondary, security-adjacent benefit worth noting alongside the two
liabilities above.

## 18. References

1. Gregor Hohpe, Bobby Woolf. *Enterprise Integration Patterns. Designing,
   Building, and Deploying Messaging Solutions*. Addison-Wesley, 2003.
   ISBN 0-321-20068-3. Message Endpoints chapter, "Selective Consumer".
   Source of the pattern name, intent, the Specifying Producer and Selection
   Value terminology, and the point-to-point versus publish-subscribe
   distinction.
2. Gregor Hohpe, Bobby Woolf. *Enterprise Integration Patterns* companion
   site, "Selective Consumer".
   https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessageSelector.html
   Verified 2026-08-02. Author-maintained summary mirroring the book's
   wording, used to confirm intent and problem statement phrasing.
3. Eclipse Foundation. *Jakarta Messaging Specification*, version 3.1,
   section 3.8, "Message selection".
   https://jakarta.ee/specifications/messaging/3.1/jakarta-messaging-spec-3.1
   Verified 2026-08-02. Source for the message selector definition, syntax
   reference, and section location cited in dimensions 1, 8, and 9.
4. RabbitMQ (Broadcom / VMware Tanzu). "RabbitMQ tutorial 5, topics".
   https://www.rabbitmq.com/tutorials/tutorial-five-python.html
   Verified 2026-08-02. Source for the topic exchange routing-key
   pattern-matching production use in dimensions 8 and 9.
5. Amazon Web Services. "Amazon SNS message filtering".
   https://docs.aws.amazon.com/sns/latest/dg/sns-message-filtering.html
   Verified 2026-08-02. Source for the SNS filter policy production use in
   dimensions 8 and 9.
6. VMware Tanzu. *Spring Framework Reference Documentation*, integration
   module, JMS, annotation-driven listener endpoints, `@JmsListener`
   selector attribute.
   https://docs.spring.io/spring-framework/reference/integration/jms.html
   Verified 2026-08-02. Source for the Spring `@JmsListener` `selector`
   attribute production use in dimension 9.

## Code examples

Three languages representative of the three shapes the pattern actually
takes in practice. TypeScript shows a broker-agnostic client-side predicate,
the shape most application code reaches for when the messaging library
offers no native selector, or when portability across brokers matters more
than squeezing out the broker-side saving. Python shows the same shape
applied against message headers arriving from a generic pub-sub client, with
a small registry of named selectors standing in for the declarative selector
string a real broker client would accept. Go shows the pattern implemented
as a composable predicate type over a channel abstraction, which is the
idiomatic Go shape given the language's preference for small function types
over inheritance-based extension points. Go has no broker-native selector
concept built into its standard library, so this example models the
client-side variant explicitly, including the discard-metric hook from
dimension 16.

### TypeScript

```typescript
interface EnvelopeHeaders {
  region: string;
  priority: number;
  eventType: string;
}

interface Message {
  headers: EnvelopeHeaders;
  body: unknown;
}

type Selector = (headers: EnvelopeHeaders) => boolean;

function euHighPriority(): Selector {
  return (h) => h.region === "EU" && h.priority > 5;
}

class SelectiveConsumer {
  private matched = 0;
  private discarded = 0;

  constructor(
    private readonly selector: Selector,
    private readonly handle: (m: Message) => void
  ) {}

  receive(message: Message): void {
    if (this.selector(message.headers)) {
      this.matched++;
      this.handle(message);
    } else {
      this.discarded++;
    }
  }

  stats(): { matched: number; discarded: number } {
    return { matched: this.matched, discarded: this.discarded };
  }
}

const consumer = new SelectiveConsumer(euHighPriority(), (m) =>
  console.log("handling", m.headers.eventType)
);

consumer.receive({
  headers: { region: "EU", priority: 8, eventType: "order.created" },
  body: {},
});
consumer.receive({
  headers: { region: "US", priority: 9, eventType: "order.created" },
  body: {},
});

console.log(consumer.stats());
```

### Python

```python
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Headers:
    region: str
    priority: int
    event_type: str


@dataclass(frozen=True)
class Envelope:
    headers: Headers
    body: object


Selector = Callable[[Headers], bool]


def eu_high_priority() -> Selector:
    return lambda h: h.region == "EU" and h.priority > 5


class SelectiveConsumer:
    def __init__(self, selector: Selector, handle: Callable[[Envelope], None]) -> None:
        self._selector = selector
        self._handle = handle
        self.matched = 0
        self.discarded = 0

    def receive(self, message: Envelope) -> None:
        if self._selector(message.headers):
            self.matched += 1
            self._handle(message)
        else:
            self.discarded += 1


if __name__ == "__main__":
    consumer = SelectiveConsumer(
        eu_high_priority(),
        lambda m: print("handling", m.headers.event_type),
    )

    consumer.receive(Envelope(Headers("EU", 8, "order.created"), {}))
    consumer.receive(Envelope(Headers("US", 9, "order.created"), {}))

    print("matched", consumer.matched, "discarded", consumer.discarded)
```

### Go

```go
package main

import "fmt"

type Headers struct {
	Region    string
	Priority  int
	EventType string
}

type Message struct {
	Headers Headers
	Body    any
}

type Selector func(Headers) bool

func euHighPriority() Selector {
	return func(h Headers) bool {
		return h.Region == "EU" && h.Priority > 5
	}
}

type SelectiveConsumer struct {
	selector  Selector
	handle    func(Message)
	matched   int
	discarded int
}

func NewSelectiveConsumer(s Selector, handle func(Message)) *SelectiveConsumer {
	return &SelectiveConsumer{selector: s, handle: handle}
}

func (c *SelectiveConsumer) Receive(m Message) {
	if c.selector(m.Headers) {
		c.matched++
		c.handle(m)
		return
	}
	c.discarded++
}

func main() {
	consumer := NewSelectiveConsumer(euHighPriority(), func(m Message) {
		fmt.Println("handling", m.Headers.EventType)
	})

	consumer.Receive(Message{Headers: Headers{"EU", 8, "order.created"}, Body: nil})
	consumer.Receive(Message{Headers: Headers{"US", 9, "order.created"}, Body: nil})

	fmt.Println("matched", consumer.matched, "discarded", consumer.discarded)
}
```
