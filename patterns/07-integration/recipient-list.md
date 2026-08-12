---
name: Recipient List
slug: recipient-list
family: 07-integration
category: Messaging
aliases: [Recipient List Router, Dynamic Recipient List, Fan-Out Router]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [content-based-router, message-filter, splitter, aggregator, publish-subscribe-channel, pipes-and-filters, dynamic-router, correlation-identifier]
incompatible_with: []
verified: 2026-08-02
---

# Recipient List

## 1. Name, aliases, and lineage

The canonical name is Recipient List. It is catalogued in Gregor Hohpe and
Bobby Woolf, *Enterprise Integration Patterns. Designing, Building, and
Deploying Messaging Solutions*, Addison-Wesley, 2003, ISBN 0-321-20068-3,
chapter 4, "Messaging Systems", in the Message Routing section. The book's own
reference page states the problem as "How do we route a message to a list of
dynamically specified recipients?" and gives the solution as "Define a channel
for each recipient. Then use a Recipient List to inspect an incoming message,
determine the list of desired recipients, and forward the message to all
channels associated with the recipients in the list" (Recipient List,
enterpriseintegrationpatterns.com,
https://www.enterpriseintegrationpatterns.com/patterns/messaging/RecipientList.html,
verified 2026-08-02). The same page notes the pattern works in two conceptual
parts, first computing the recipient list, then traversing it to send message
copies to each recipient, and draws the explicit contrast that it does this
"similar to a Content-Based Router but without modifying message contents"
(same source, verified 2026-08-02).

That contrast in the book's own words is worth repeating precisely, because it
is the single fact that keeps this pattern from being confused with its
sibling. A Content-Based Router picks exactly one destination per message and
the message goes down exactly one path. A Recipient List computes a SET of
destinations and sends a copy of the same message to every member of that set.
The router is an exclusive choice, the list is a fan-out. See dimension 13 for
the full comparison.

Every messaging framework that implements the Enterprise Integration Patterns
catalog ships this pattern under a name close to the original. Apache Camel
calls it the Recipient List EIP, implemented with the `recipientList` DSL
verb, and documents it with the identical problem statement as the book,
"How do we route a message to a list of dynamically specified recipients?"
(Recipient List EIP, Apache Camel component reference,
https://camel.apache.org/components/latest/eips/recipientList-eip.html,
verified 2026-08-02). Camel's own documentation also states plainly that the
Recipient List is layered on top of a more general primitive, "The Multicast
EIP has many features and is also used as a baseline for the Recipient List
and Split EIPs" (Multicast EIP, Apache Camel component reference,
https://camel.apache.org/components/latest/eips/multicast-eip.html, verified
2026-08-02). Spring Integration ships the same idea as
`RecipientListRouter`, described in its own reference manual as a router that
"sends each received message to a statically defined list of message
channels", with a per-recipient `selector-expression` that can make the list
dynamic per message (Spring Integration Reference Manual, Router
Implementations,
https://docs.spring.io/spring-integration/reference/router/implementations.html,
verified 2026-08-02). None of these product names displace the catalog name.
Recipient List is what cross-vendor conversation uses, and it is the name used
throughout this entry.

## 2. Problem and context

A single message must reach more than one downstream consumer at once, and the
exact SET of consumers that should receive a given message is not fixed at
design time. It depends on the content of the message, on a subscription list
that changes at runtime, or on business rules evaluated per message.

The shape recurs across very different domains. An order confirmation must go
to the fulfilment system, the invoicing system, and the customer's chosen
notification channel, and which notification channel that is, email, SMS, a
push service, depends on a preference stored per customer. A trade execution
report at a broker must be copied to the position-keeping system, the
compliance archive, and, only when the trade exceeds a regulatory threshold,
to a surveillance system, so the third recipient is conditional on the
message's own content. A build pipeline event must reach every team's chat
channel that owns a service touched by that build, and the set of owning
teams is read from an ownership file, not hardcoded into the pipeline.

What separates this from a plain Publish-Subscribe Channel is that in a pure
publish-subscribe topology, every subscriber is a passive, symmetric
participant of one broadcast channel and receives everything published there,
with the fan-out being the channel's own structural property, not a decision
made per message by the sender or an intermediary. A Recipient List instead
computes, per message, the specific subset of channels or endpoints that
message should reach, based on the message itself. The list is a decision, not
a subscription. Two orders with different customer notification preferences
produce two different recipient sets even though both flow through the exact
same Recipient List component.

The naive alternative, wiring every possible destination into the sending
application and looping over an if-statement per recipient, works until the
recipient set needs to change. Adding a new notification channel, a new
compliance jurisdiction, or a new team's chat channel then means redeploying
the sender. The Recipient List exists to move that decision out of the sender
and into a single, independently changeable component, the same motivation
that drives every routing pattern in the Enterprise Integration Patterns
catalog, stated by the book as keeping "the sender of a message... unaware of
the identity of the receiver or receivers" (Recipient List,
enterpriseintegrationpatterns.com,
https://www.enterpriseintegrationpatterns.com/patterns/messaging/RecipientList.html,
verified 2026-08-02).

## 3. Forces

Fan-out breadth against blast radius. The more recipients a single message can
reach, the more downstream systems a single bad message, a schema change, or a
recipient outage can affect at once. A Recipient List concentrates the
decision of who gets this into one place, which is good for changeability and
bad for containment if that one place is wrong.

Coupling location against coupling amount. The pattern does not remove
coupling between the sender's data and the set of recipients, it relocates
that coupling from the sender's code into the Recipient List's rule set, a
lookup table, a rules engine, a subscription registry. That relocation is
usually a net win because the rule set changes far more often than the sender
does, but the coupling itself is not eliminated and someone still owns keeping
the rule set correct.

Delivery semantics against complexity. A message copied to five recipients can
be delivered synchronously and sequentially, in parallel with a join, or
fire-and-forget with no join at all. Each choice trades latency, failure
isolation, and implementation complexity against the other two. Sequential
delivery is simple to reason about and slow. Parallel delivery with a join is
fast and needs an Aggregator or an explicit timeout policy for a recipient
that never answers. Fire-and-forget is fastest and cheapest to build and
offers the weakest guarantee that every recipient actually got the message.

Idempotency against retry safety. Because the pattern often sits in front of
retryable transports, a partial failure, where three of five recipients
succeeded and two did not, creates a genuine question of whether to retry the
whole fan-out, risking duplicate delivery to the three that already succeeded,
or retry only the failed two, which requires the component to track
per-recipient delivery state. Neither answer is free.

Static list against computed list. A recipient list that never changes at
runtime is barely more than a Publish-Subscribe Channel with extra ceremony.
The pattern earns its complexity precisely when the list is computed per
message from content, from a subscription registry, or from business rules,
and that computation is itself a place bugs live, because an empty or wrong
computed list fails silently unless something asserts that the list is
non-empty.

## 4. Applicability and non-applicability

Reach for a Recipient List when the same logical message genuinely needs to
reach more than one consumer, and which consumers depends on the message's own
content or on a subscription set that changes independently of the sender.
Reach for it when the current set of recipients is expected to grow or shrink
over the system's life, so hardcoding the fan-out into every producer would
mean redeploying producers every time a recipient is added. Reach for it when
different recipients legitimately need the identical message body, not a
transformed or filtered variant, because the pattern by the book's own
definition sends copies "without modifying message contents"
(enterpriseintegrationpatterns.com, verified 2026-08-02). Reach for it when
the routing decision has enough business logic behind it, a lookup table, a
rules engine, per-tenant configuration, that centralising the decision in one
component is clearly worth the extra hop compared to leaving the decision
scattered across senders.

Do not reach for it when exactly one recipient should ever receive a given
message. That is a Content-Based Router, and building a Recipient List that
happens to always compute a list of length one is needless indirection that
still pays the fan-out and join cost for a decision that was never a fan-out.

Do not reach for it when every consumer genuinely wants every message with no
per-message variation. That is a plain Publish-Subscribe Channel, and a
Recipient List computing the identical static list on every invocation adds a
computation step, a source of drift between the list and the subscribers, and
a place for a bug to accidentally drop a subscriber, with no offsetting
benefit over letting the broker's own subscription mechanism do the fan-out.

Do not reach for it when the recipients need materially different payloads,
not the same message. If invoicing needs the full order and the shipping
label printer needs only an address and a weight, sending the identical
message to both and making each recipient discard what it does not need is a
sign the boundary is wrong, a Content Enricher or per-recipient transformation
ahead of delivery belongs in the picture, or the fan-out belongs after a
Splitter that produces recipient-specific messages rather than one message
sent unmodified to all.

Do not reach for it as a substitute for a proper event bus in a system with
dozens of independent, evolving consumers that should not need to be known by
name anywhere central. A Recipient List whose rule set has to enumerate every
consuming team by name becomes an operational bottleneck exactly like a
hardcoded sender did, only one hop downstream, and a topic-based
Publish-Subscribe Channel with filtering, where consumers declare their own
interest, avoids that central enumeration entirely. Amazon SNS message
filtering is the production illustration of exactly this alternative, where
"a filter policy is a JSON object containing properties that define which
messages the subscriber receives" and the subscriber, not a central list,
owns the policy (Amazon SNS message filtering, AWS documentation,
https://docs.aws.amazon.com/sns/latest/dg/sns-message-filtering.html, verified
2026-08-02).

Do not reach for it when delivery order across recipients matters and cannot
be relaxed. The pattern's natural implementations are either sequential,
which is slow, or parallel, which by construction offers no ordering
guarantee across recipients unless something downstream imposes one.

## 5. Structure

Message Producer. The component that emits the original message with no
knowledge of who receives it.

Recipient List. The central component. It accepts one inbound message,
evaluates a Recipient Selection Rule against that message to produce an
ordered or unordered set of recipient identifiers, then dispatches an
unmodified copy of the message to each identified recipient's channel. It
owns the decision of who receives the message and the mechanics of sending to
each of them.

Recipient Selection Rule. The logic, whether a static configuration list, a
lookup table keyed on message content, a rules engine evaluation, or a query
against a subscription registry, that turns one inbound message into a set of
recipient identifiers. This is often externalised so it can change without a
code deployment.

Recipient Channel. One Message Channel per recipient, exactly as the book
specifies, "Define a channel for each recipient" (Recipient List,
enterpriseintegrationpatterns.com, verified 2026-08-02). Each channel leads to
exactly one Message Endpoint, whether that endpoint is a queue consumer, an
HTTP webhook, an email transport, or another service's inbound API.

Message Endpoint, per recipient. The actual downstream consumer that
receives its copy of the message and acts on it. Endpoints are unaware of
each other and unaware of the Recipient List's selection logic.

Delivery Coordinator, optional. Present when the fan-out needs a completion
signal, a partial-failure policy, or a join. Frequently implemented as a
Scatter-Gather composition of the Recipient List with an Aggregator, tracked
per-message with a Correlation Identifier so responses, if any recipient
replies, can be matched back to the original fan-out.

## 6. ASCII structure diagram

```
                         +-------------------+
  Message Producer  ---->|  Recipient List   |
                         |-------------------|
                         | selection rule.    |
                         |  msg -> {r1, r2,   |
                         |          r3, ...}  |
                         +---------+---------+
                                   |
              +--------------------+--------------------+
              |                    |                     |
              v                    v                     v
     +----------------+   +----------------+    +----------------+
     | Recipient       |   | Recipient       |    | Recipient       |
     | Channel r1      |   | Channel r2      |    | Channel r3      |
     +--------+--------+   +--------+--------+    +--------+--------+
              |                    |                     |
              v                    v                     v
     +----------------+   +----------------+    +----------------+
     | Endpoint A       |   | Endpoint B       |   | Endpoint C       |
     | (unmodified copy)|   | (unmodified copy)|   | (unmodified copy)|
     +----------------+   +----------------+    +----------------+

  Note. the recipient set {r1, r2, r3} is computed PER MESSAGE.
  A different message on the same channel may resolve to {r2} alone,
  or to {r1, r4}, if r4 exists and this message's content selects it.
```

## 7. Dynamics

```
  1. Message m arrives on the Recipient List's input channel.

  2. Recipient List evaluates SelectionRule(m) -> recipients = {r1, r2, r3}

     if recipients is empty.
         -> log/alert (an empty result is almost always a bug, not
            a legitimate "nobody wants this" outcome, see dimension 11)
         -> optionally route to a default channel

  3. for each recipient r in recipients.
         copy <- deep_copy(m)              # each recipient gets its own copy
         copy.headers.correlationId <- m.id  # for optional gather later
         send(copy) -> Channel(r)

     Two delivery strategies branch here.

     Sequential.
         for r in recipients. send and wait for channel-accept before next r
         -> simple to reason about, total latency = sum of per-send latency

     Parallel (fire-and-forget or joined).
         for r in recipients. send asynchronously, do not block on r
         if a join is required.
             -> hand off correlationId to an Aggregator (see dimension 13)
             -> Aggregator waits for N of len(recipients) responses or a
                timeout, then completes the gather
         -> total latency approx = max per-send latency, not the sum

  4. Producer's original send() call returns once the Recipient List has
     accepted the message. It does NOT normally block on downstream
     endpoints actually consuming it, unless the transport is itself
     synchronous request-reply per recipient.

  5. Failure at a single recipient's channel (r2 unreachable, say).
         - ignore-and-continue. log the failure, still deliver to r1 and r3
         - fail-fast. abort the whole fan-out, roll back or dead-letter m
         - retry-that-recipient-only. requeue a copy addressed only to r2

     The choice is a policy decision, not something the pattern itself
     dictates. Spring Integration exposes it directly as a per-router
     'ignore-send-failures' flag, defaulting to false, which is fail-fast.
```

## 8. Implementation variants

Static configuration list. The simplest form, a fixed list of channels
configured once, evaluated identically for every message. Spring
Integration's `RecipientListRouter` in its simplest configuration is exactly
this, "sends each received message to a statically defined list of message
channels" (Spring Integration Reference Manual, verified 2026-08-02). This
variant is honestly closer to a Publish-Subscribe Channel in behaviour and is
usually a stepping stone toward a conditional variant rather than a
destination in itself.

Per-recipient selector expression. Each candidate channel carries its own
boolean predicate evaluated against the message, and only channels whose
predicate is true receive a copy. Spring Integration's own example shows this
directly, `selector-expression="payload.equals('foo')"` on one recipient and
`selector-expression="headers.containsKey('bar')"` on another, in the same
router (Spring Integration Reference Manual, Router Implementations, verified
2026-08-02). This is the most common production shape because it keeps the
decision for each recipient local and independently testable rather than
buried in one large branching function.

DSL fluent method on a routing engine. Apache Camel's `recipientList()` verb
takes an expression that evaluates, per message, to a delimited string or a
collection of endpoint URIs, computed inline in the route rather than
configured as a static list, matching Camel's documented framing of the
pattern as inspecting "an incoming message, determine the list of desired
recipients, and forward the message to all channels" (Recipient List EIP,
Apache Camel, verified 2026-08-02).

Multicast-with-list, built on a lower-level primitive. Some frameworks do not
ship a dedicated Recipient List construct at all and instead build it as a
thin layer over a general Multicast primitive that sends the same message to
N statically or dynamically supplied endpoints, exactly as Camel itself
documents its own layering, "The Multicast EIP has many features and is also
used as a baseline for the Recipient List and Split EIPs" (Multicast EIP,
Apache Camel, verified 2026-08-02). Implementers who build this pattern from
scratch, without a framework, are effectively reconstructing a small Multicast
plus a selection function.

Broker-side filter subscription, the inverted variant. Instead of one central
component owning the recipient set, each candidate recipient declares its own
interest as a filter attached to a shared topic, and the broker computes,
per message, which subscribers match, which is structurally the same fan-out
outcome achieved from the opposite direction, subscriber-declared instead of
sender-computed. Amazon SNS's filter policy mechanism is the clearest named
production instance, where "Amazon SNS compares the message attributes or the
message body to the properties in the filter policy for each of the topic's
subscriptions" and delivers only where the policy matches (Amazon SNS message
filtering, AWS, verified 2026-08-02). This variant trades central visibility
of the full recipient list for looser coupling between the recipient set and
any one owning component, discussed further in dimension 13.

Language-idiomatic closures over an explicit switch. In languages with
first-class functions, the selection rule is frequently written as a plain
function from a message to a list of channels rather than a class hierarchy
or a configuration file, closing over whatever registry or lookup table it
needs. This is the shape used in the code examples below, and it is the
natural default in TypeScript, Python, and Go where building a full
Strategy-pattern class hierarchy purely to select a list would be unnecessary
ceremony.

## 9. Known production uses

Apache Camel ships `recipientList()` as a first-class DSL verb across every
supported language binding (Java, XML, YAML), with dedicated options for
parallel processing, custom aggregation strategies, ignoring invalid
endpoints, and stop-on-exception semantics, documented in full at Recipient
List EIP, Apache Camel component reference,
https://camel.apache.org/components/latest/eips/recipientList-eip.html,
verified 2026-08-02.

Spring Integration ships `RecipientListRouter` as a supported router
implementation with XML namespace support, Java DSL support
(`.routeToRecipients(...)`), a JMX and Control Bus management interface for
adding and removing recipients at runtime since version 4.1, and per-recipient
selector expressions in SpEL, documented at Spring Integration Reference
Manual, Router Implementations,
https://docs.spring.io/spring-integration/reference/router/implementations.html,
verified 2026-08-02.

Amazon Simple Notification Service implements the broker-side filter variant
of this pattern's intent at production cloud scale, where a single published
message can be delivered to a computed subset of an arbitrary number of
subscribed endpoints (SQS queues, Lambda functions, HTTP endpoints, email,
SMS) based on a JSON filter policy evaluated per subscription against the
message's attributes or body, documented at Amazon SNS message filtering, AWS
documentation, https://docs.aws.amazon.com/sns/latest/dg/sns-message-filtering.html,
verified 2026-08-02.

## 10. Consequences

Positive. The recipient set becomes a single, independently changeable piece
of configuration or logic rather than logic duplicated or scattered across
every message producer, so adding, removing, or conditionally including a
recipient is a change in exactly one place. Producers stay genuinely ignorant
of who consumes their messages, preserving the same decoupling goal every
routing pattern in the Enterprise Integration Patterns catalog shares. The
pattern composes cleanly with a downstream Aggregator, via Scatter-Gather,
when a joined response across all recipients is needed, and with a Message
Filter ahead of it to keep obviously irrelevant messages from ever reaching
the selection logic.

Negative. The Recipient List becomes a concentration point, both for
operational risk, a bug in the selection rule silently drops or
over-broadcasts to recipients across every message that flows through it, and
for the blast radius of any single bad message, one malformed message can now
reach every computed recipient rather than one. Fan-out multiplies downstream
load linearly with the recipient count for every message that passes through,
which is easy to overlook when the recipient count is small during
development and grows in production. Partial failure across recipients
introduces a genuine design decision, discussed in dimension 3, that has no
free answer, and skipping that decision, treating "sent to some" as
equivalent to "sent to all", is a common and expensive mistake. The pattern
also, by definition, sends every recipient the identical message body, so any
recipient that only needed a subset of the data still receives and must parse
the whole thing, which is wasted bandwidth and a minor information exposure
multiplied across every recipient on the list.

## 11. Failure modes and misuse

Symptom. A recipient stops receiving messages it used to receive, with no
error anywhere. Cause. The selection rule was changed, a configuration edit,
a new deployment of the rules engine, an expired subscription record, and the
recipient silently dropped out of the computed list, and because an empty or
reduced list is not, by itself, an error condition, nothing alerts. Fix.
Assert a minimum expected recipient count, or alert on a recipient list that
shrank compared to its historical baseline, and treat every change to the
selection rule as a reviewed, tested change exactly like application code,
because functionally it is application code even when it lives in a
configuration file or a rules-engine UI.

Symptom. The same downstream side effect happens twice, an email sent twice,
a payment processed twice, at a recipient endpoint. Cause. A retry of the
whole fan-out after a partial failure re-sent to a recipient that had already
succeeded on the first attempt, because the retry logic retried the entire
recipient set rather than only the recipients that had failed. Fix. Track
per-recipient delivery outcome for the duration of a retry window, and retry
only the recipients recorded as failed, or make every recipient's own
processing idempotent, a Message ID de-duplication check, so a duplicate
delivery is harmless rather than merely unlikely.

Symptom. Producer-side latency grows unpredictably and is hard to correlate
with producer load. Cause. The fan-out delivery was implemented sequentially
and blocking, so producer latency now equals the sum of every recipient's
response time, and a single slow recipient, a webhook to a third party
having a bad day, silently degrades every message, not only the ones
addressed to that recipient. Fix. Deliver in parallel with a bounded
per-recipient timeout, and decouple producer acceptance latency from
recipient processing latency by treating "accepted by the Recipient List" and
"delivered to every recipient" as two different, separately observable
events.

Symptom. A message reaches a recipient that clearly should not have
received it, and nobody can explain why from reading the code. Cause. The
Recipient List and a Content-Based Router upstream of it were conflated, or
the selection rule's default branch, what happens when none of the explicit
conditions match, silently includes a recipient meant only for the matched
case, a common off-by-one in rule authoring where the else clause was copied
from an earlier version of the rule and never revisited. Fix. Give the
selection rule an explicit, tested default case, and write a unit test per
recipient asserting the specific message shapes that should and should not
include it, rather than testing only the happy path.

Symptom. The fan-out silently sends to zero recipients for an entire class
of message, and nobody notices until a customer or auditor asks where a
message went. Cause. An empty recipient list was treated as a normal, silent
outcome rather than a suspicious one, and no code path distinguishes "this
message legitimately has no interested recipients" from "the selection rule
has a bug and matched nothing when it should have matched something". Fix.
An empty recipient list should be a logged, ideally alerted, event by
default, with an explicit, named opt-out for the rare legitimate cases where
zero recipients really is a correct outcome, so silence is never the default.

## 12. Trade-off matrix

| Force | Recipient List | Content-Based Router | Publish-Subscribe Channel |
|---|---|---|---|
| Number of recipients per message | Many, computed per message | Exactly one, chosen per message | All current subscribers, fixed by the channel's subscription set |
| Where the recipient decision lives | Central component, per-message computed list | Central component, per-message single choice | Distributed, each subscriber's own subscription decision |
| Coupling of sender to recipients | None, sender knows only the Recipient List's input channel | None, sender knows only the router's input channel | None at send time, but broker holds the subscription state |
| Adding a new recipient | Change the selection rule in one place | Not applicable, only one recipient exists per message | Subscribe to the channel, no central change needed |
| Message content changed per recipient | No, all recipients get the same message body | Not applicable, only one recipient receives it | No, all subscribers get the same message |
| Blast radius of a bad message | High, reaches every computed recipient at once | Low, reaches exactly one recipient | High, reaches every current subscriber |
| Fits "who should react to this specific content" | Yes, this is the core use case | Yes, when the answer is exactly one | No, subscription is content-independent unless combined with filtering |
| Fits "everyone always wants everything" | Poor fit, needless computation for a static outcome | Not applicable | Best fit, this is the channel's native behaviour |

## 13. Related and incompatible patterns

Content-Based Router is the pattern most often confused with this one,
because both inspect message content to make a routing decision, and the
distinction the book itself draws is the cleanest way to keep them apart, a
router chooses one destination, a Recipient List computes a set and sends a
copy to each (enterpriseintegrationpatterns.com, verified 2026-08-02). A
system frequently uses both together, a Content-Based Router deciding which
of several Recipient Lists a message should even reach, followed by that
Recipient List computing the actual fan-out for its category of message.

Splitter is a common upstream companion, not a substitute. Where a Recipient
List sends the SAME message body to multiple destinations, a Splitter breaks
ONE message into several DIFFERENT messages, each of which may end up aimed
at a different single recipient. A pipeline that needs both breaking a batch
order into per-line-item messages and sending each line item to every
interested downstream system chains a Splitter into a Recipient List, in
that order.

Scatter-Gather is the composed form of this pattern with an Aggregator. The
Recipient List is the scatter half. When the fan-out needs a joined,
correlated response, a Correlation Identifier is attached to each dispatched
copy, and an Aggregator downstream collects responses that share that
correlation identifier until a completion condition, all N recipients
responded, or a timeout elapsed, is met. A Recipient List used purely for
fire-and-forget notification, with no expectation of a reply, does not need
this composition at all.

Publish-Subscribe Channel is the pattern this one is most often mistaken as a
special case of, and the direction of control is the distinguishing fact.
Publish-Subscribe puts the decision in the recipients' hands, each subscriber
declares its own interest and the broker computes membership from those
declarations. A Recipient List puts the decision in one central component's
hands, computed from the message. Amazon SNS's filter-policy mechanism sits
structurally between the two, technically a Publish-Subscribe Channel at the
transport level, but functionally delivering the Recipient List's outcome
because the effective per-message recipient set still varies with content,
computed in a distributed rather than centralised way
(https://docs.aws.amazon.com/sns/latest/dg/sns-message-filtering.html,
verified 2026-08-02).

Message Filter is a natural companion placed ahead of the Recipient List to
discard messages that no configured recipient would ever want, avoiding the
cost of evaluating a selection rule against traffic that structurally cannot
match anything, though this is an optimisation, not a requirement.

Dynamic Router is a close cousin used when the routing decision itself needs
to change its own logic based on prior messages or feedback, rather than
being a fixed, if content-dependent, rule. A Recipient List with a selection
rule that consults external, frequently changing state, a live subscription
registry, blurs into Dynamic Router territory, and the line between a
Recipient List whose rule reads dynamic state and a Dynamic Router that
happens to fan out is a matter of emphasis rather than a hard technical
boundary.

No pattern in this catalog is structurally incompatible with a Recipient
List. The pattern composes at the message-flow level with almost everything
around it. The closest thing to friction is using it where a simpler
Publish-Subscribe Channel would suffice, which is a misapplication, dimension
4, rather than a true incompatibility.

## 14. Refactoring path in and out

Introducing the pattern into code that lacks it typically starts from a
producer with an explicit loop or an if-else chain that sends to several
hardcoded destinations directly. The first step is to extract that loop's
body into a pure function, a message-to-recipient-list function, with no side
effects, and write tests against that function alone before touching any
sending code, because the selection logic is where the real business rules
live and it deserves to be tested in isolation from any transport. The second
step is to introduce a Recipient List component, a class, a route, a
function, that owns both the extracted selection function and the send loop,
and redirect the producer to send once to that component's single input
channel instead of iterating destinations itself. The third step, often
skipped and often needed later, is to externalise the selection rule from
code into configuration once its shape stabilises, whether that is a
configuration file, a database table, or a rules-engine definition, so that
adding a recipient becomes an operational change rather than a code
deployment. Each step should ship independently and be observable before the
next begins, since combining the extraction step with the externalisation
step in one change makes it hard to tell which change caused a subsequent
bug.

Removing the pattern, when it stops earning its place, most often happens
because the recipient set has, in practice, become static and nobody has
added or removed a recipient in a long time, at which point the fan-out
machinery is pure overhead versus a plain Publish-Subscribe Channel or even a
hardcoded list of sends. The refactor collapses the selection rule to
whatever it currently, always evaluates to, deletes the general-purpose
dispatch loop in favour of that fixed set, and, if a broker is already in the
architecture, moves the fan-out onto the broker's own native subscription
mechanism rather than reimplementing it in application code. This should be
done cautiously and only after confirming, from real production logs
collected over a sufficiently long window, that the computed list truly has
stopped varying, not merely that it has not varied during the recent
observation period, since the whole reason the pattern was introduced was
usually that the set changes occasionally rather than never.

## 15. Testing and verification

The selection rule, being a pure function from message to recipient set in
most idiomatic implementations, is the easiest and most valuable part to
test directly, with no fan-out machinery, no transport, and no mocks beyond
constructing input messages. Every branch of the rule deserves at least one
test asserting both what is included and what is explicitly excluded, because
the failure mode most often missed, dimension 11, is an incorrect exclusion,
not an incorrect inclusion, and a test suite that only checks whether
recipient X is present for a given message shape never catches whether
recipient Z was wrongly included too.

The dispatch mechanics, separately, are tested with a test double standing in
for each Recipient Channel, a Test Spy that records every message it
received rather than a full fake endpoint, so the assertion can check both
the number of recipients that received a copy and that each copy's content
matches the original message unmodified, per the pattern's own definition of
sending "without modifying message contents"
(enterpriseintegrationpatterns.com, verified 2026-08-02). A single test that
asserts the recipient count equals the expected count without also asserting
message equality per recipient can pass even when the pattern is silently
corrupting or truncating the payload for some recipients.

Partial-failure behaviour needs its own explicit test category, not an
afterthought, precisely because dimension 3 identifies it as a genuine design
choice with no default that is obviously correct. a test that fails one
recipient's channel, a Test Stub that throws or returns an error, and asserts
the chosen policy, either that the remaining recipients still received their
copies (ignore-and-continue) or that none did (fail-fast), depending on which
policy the system is meant to implement. Testing only the all-succeed and
all-fail cases and skipping the partial-failure case leaves the single most
production-relevant scenario unverified.

Contract or integration tests against real recipient endpoints, sparing and
targeted rather than exhaustive, still earn their place to catch drift
between what the selection rule believes a recipient's channel identifier
means and what the actual transport configuration resolves that identifier
to, a class of bug that unit tests against a Test Spy cannot see because the
spy never validates the channel identifier's real-world routability.

## 16. Observability signals

Per-invocation, log the inbound message's identifier, the computed recipient
count, and the identifiers of the computed recipients themselves, at a level
that survives into aggregated metrics, not only into a debug-level trace that
is disabled in production, because the recipient count over time is the
primary signal for the silent-empty-list failure mode in dimension 11. A
dashboard tile showing recipient count distribution, median, and specifically
the count of zero-recipient events, over a rolling window turns that failure
mode from something a customer reports into something an on-call engineer
sees before the customer notices.

Per-recipient delivery outcome, success, failure, or timeout, tagged with the
recipient identifier and the message identifier, is the second signal that
matters most, because it is what makes the partial-failure question in
dimension 3 answerable in production rather than only in a design document. A
healthy Recipient List's dashboard shows delivery success rate near one
hundred percent per recipient, stable across recipients. A failing instance
shows either one specific recipient's success rate degrading, that
recipient's endpoint has a problem, or every recipient's success rate
degrading together, the Recipient List's own dispatch mechanism, not any
individual endpoint, has a problem, and the two look identical in an
aggregate overall success rate metric but require completely different
remediation, which is why per-recipient tagging is not optional.

End-to-end fan-out latency, from message acceptance to the last recipient's
acknowledgment, when a join is used, or to dispatch completion, when it is
not, distinguishes producer-facing latency from the true worst-case
downstream latency described in dimension 11's sequential-blocking failure
mode. A sudden shift in this distribution's tail, without a corresponding
shift in per-recipient latency, points at the recipient set itself growing,
which is a capacity signal worth alerting on independently of any error rate.

Recipient set drift, a diff between today's computed recipient sets, sampled
or aggregated, against a recent historical baseline, catches configuration or
rule regressions that produce no errors at all, only a quietly wrong answer,
which is the hardest class of Recipient List failure to see through
conventional error-rate monitoring alone.

## 17. Security and privacy implications

This is judgement, not a sourced fact, drawn from the pattern's structural
properties rather than from a named source.

A Recipient List, because it forwards a message unmodified to every computed
recipient, is a place where over-broad data exposure quietly accumulates. A
message built for one original purpose, and one original set of trusted
consumers, frequently grows new fields over its lifetime for a new
recipient's benefit, and because the pattern forwards the whole body to
everyone on the list, every existing recipient silently starts receiving
every new field too, whether or not that recipient should see it. A message
containing a customer's full profile, added so a marketing recipient can
personalise an email, also now reaches an operational logging recipient that
had no legitimate need for that customer's personal data, a privacy exposure
introduced by a change nobody reviewed against every existing recipient's
actual need. Where recipients have materially different data-access
entitlements, this pattern's property of sending the same message to every
recipient is a liability, and a per-recipient projection or field-level
filter ahead of dispatch, rather than the raw unmodified copy the pattern
specifies by definition, is the safer shape when regulated or sensitive data
is in play.

The selection rule itself is an authorization decision in disguise even when
nobody designed it as one, deciding who receives what, and if that rule is
externalised into configuration that a broader group of people can edit than
the group authorized to decide data-access policy, the rule becomes a path
around whatever access controls exist elsewhere in the system. Treating
changes to the selection rule with the same review rigor as a change to an
access-control list, rather than as an ordinary operational configuration
tweak, closes that gap.

A Recipient List that logs its own computed recipient list and message
identifiers for observability, dimension 16, is, by construction, also
logging who received what, which is frequently exactly the audit trail a
compliance-sensitive system needs, but that same log becomes a second copy
of routing metadata that now needs its own retention and access-control
policy, distinct from the policy governing the messages themselves.

## 18. References

- Gregor Hohpe, Bobby Woolf. *Enterprise Integration Patterns. Designing,
  Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003, ISBN
  0-321-20068-3, chapter 4, Messaging Systems, Message Routing section.
- Recipient List, enterpriseintegrationpatterns.com,
  https://www.enterpriseintegrationpatterns.com/patterns/messaging/RecipientList.html,
  verified 2026-08-02.
- Content-Based Router, enterpriseintegrationpatterns.com,
  https://www.enterpriseintegrationpatterns.com/patterns/messaging/ContentBasedRouter.html,
  verified 2026-08-02.
- Recipient List EIP, Apache Camel component reference,
  https://camel.apache.org/components/latest/eips/recipientList-eip.html,
  verified 2026-08-02.
- Multicast EIP, Apache Camel component reference,
  https://camel.apache.org/components/latest/eips/multicast-eip.html,
  verified 2026-08-02.
- Spring Integration Reference Manual, Router Implementations,
  https://docs.spring.io/spring-integration/reference/router/implementations.html,
  verified 2026-08-02.
- Amazon SNS message filtering, AWS documentation,
  https://docs.aws.amazon.com/sns/latest/dg/sns-message-filtering.html,
  verified 2026-08-02.

## Code examples

### TypeScript

```typescript
// recipient-list.ts
// A Recipient List that computes a per-message recipient set and
// dispatches an unmodified copy of the message to each recipient's
// channel, with a policy for partial failure.

type OrderMessage = {
  id: string;
  country: string;
  amountCents: number;
  notifyChannel: "email" | "sms" | "push";
};

type Channel<T> = {
  name: string;
  send: (msg: T) => Promise<void>;
};

type DeliveryOutcome = {
  recipient: string;
  ok: boolean;
  error?: string;
};

class RecipientList<T> {
  constructor(
    private readonly channels: Map<string, Channel<T>>,
    private readonly selectRecipients: (msg: T) => string[],
    private readonly ignoreSendFailures: boolean = false
  ) {}

  async dispatch(msg: T): Promise<DeliveryOutcome[]> {
    const recipients = this.selectRecipients(msg);

    if (recipients.length === 0) {
      throw new Error(
        "recipient list resolved to zero recipients, this is almost " +
          "always a selection-rule bug, not a legitimate outcome"
      );
    }

    const outcomes = await Promise.all(
      recipients.map(async (name): Promise<DeliveryOutcome> => {
        const channel = this.channels.get(name);
        if (!channel) {
          const outcome = { recipient: name, ok: false, error: "unknown channel" };
          if (!this.ignoreSendFailures) throw new Error(outcome.error);
          return outcome;
        }
        try {
          // Send an unmodified copy. The message object is not mutated.
          await channel.send(msg);
          return { recipient: name, ok: true };
        } catch (err) {
          const outcome = { recipient: name, ok: false, error: String(err) };
          if (!this.ignoreSendFailures) throw err;
          return outcome;
        }
      })
    );

    return outcomes;
  }
}

// Selection rule. fulfilment always, compliance only above a threshold,
// notification channel varies by the customer's own stored preference.
function selectOrderRecipients(order: OrderMessage): string[] {
  const recipients = ["fulfilment", `notify-${order.notifyChannel}`];
  if (order.amountCents >= 1_000_000) {
    recipients.push("compliance");
  }
  return recipients;
}

async function demo(): Promise<void> {
  const channels = new Map<string, Channel<OrderMessage>>([
    ["fulfilment", { name: "fulfilment", send: async (m) => console.log("fulfilment got", m.id) }],
    ["compliance", { name: "compliance", send: async (m) => console.log("compliance got", m.id) }],
    ["notify-email", { name: "notify-email", send: async (m) => console.log("emailed", m.id) }],
    ["notify-sms", { name: "notify-sms", send: async (m) => console.log("texted", m.id) }],
    ["notify-push", { name: "notify-push", send: async (m) => console.log("pushed", m.id) }],
  ]);

  const list = new RecipientList(channels, selectOrderRecipients, true);

  const small: OrderMessage = { id: "o-1", country: "DE", amountCents: 5_000, notifyChannel: "push" };
  const large: OrderMessage = { id: "o-2", country: "US", amountCents: 2_500_000, notifyChannel: "email" };

  console.log(await list.dispatch(small));
  console.log(await list.dispatch(large));
}

demo();
```

### Python

```python
"""recipient_list.py

A Recipient List that computes a per-message recipient set from a pure
selection rule, then dispatches an unmodified copy to each recipient's
channel, with an explicit partial-failure policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional


@dataclass(frozen=True)
class Order:
    order_id: str
    country: str
    amount_cents: int
    notify_channel: str  # "email" | "sms" | "push"


@dataclass
class DeliveryOutcome:
    recipient: str
    ok: bool
    error: Optional[str] = None


class RecipientList:
    def __init__(
        self,
        channels: Dict[str, Callable[[Order], None]],
        select_recipients: Callable[[Order], List[str]],
        ignore_send_failures: bool = False,
    ) -> None:
        self._channels = channels
        self._select_recipients = select_recipients
        self._ignore_send_failures = ignore_send_failures

    def dispatch(self, order: Order) -> List[DeliveryOutcome]:
        recipients = self._select_recipients(order)

        if not recipients:
            raise ValueError(
                "recipient list resolved to zero recipients, this is "
                "almost always a selection-rule bug, not a legitimate "
                "outcome"
            )

        outcomes: List[DeliveryOutcome] = []
        for name in recipients:
            channel = self._channels.get(name)
            if channel is None:
                outcome = DeliveryOutcome(name, False, "unknown channel")
                if not self._ignore_send_failures:
                    raise KeyError(outcome.error)
                outcomes.append(outcome)
                continue
            try:
                # channel receives the SAME order, unmodified.
                channel(order)
                outcomes.append(DeliveryOutcome(name, True))
            except Exception as exc:  # noqa: BLE001 - policy decides
                outcome = DeliveryOutcome(name, False, str(exc))
                if not self._ignore_send_failures:
                    raise
                outcomes.append(outcome)
        return outcomes


def select_order_recipients(order: Order) -> List[str]:
    recipients = ["fulfilment", f"notify-{order.notify_channel}"]
    if order.amount_cents >= 1_000_000:
        recipients.append("compliance")
    return recipients


def _demo() -> None:
    channels: Dict[str, Callable[[Order], None]] = {
        "fulfilment": lambda o: print("fulfilment got", o.order_id),
        "compliance": lambda o: print("compliance got", o.order_id),
        "notify-email": lambda o: print("emailed", o.order_id),
        "notify-sms": lambda o: print("texted", o.order_id),
        "notify-push": lambda o: print("pushed", o.order_id),
    }

    recipient_list = RecipientList(channels, select_order_recipients, ignore_send_failures=True)

    small = Order("o-1", "DE", 5_000, "push")
    large = Order("o-2", "US", 2_500_000, "email")

    print(recipient_list.dispatch(small))
    print(recipient_list.dispatch(large))


if __name__ == "__main__":
    _demo()
```

### Go

```go
// recipient_list.go
// A Recipient List that computes a per-message recipient set from a pure
// selection function, then dispatches an unmodified copy of the message
// to each recipient's channel, in parallel, with a partial-failure policy.

package main

import (
	"errors"
	"fmt"
	"sync"
)

type Order struct {
	ID            string
	Country       string
	AmountCents   int
	NotifyChannel string // "email" | "sms" | "push"
}

type DeliveryOutcome struct {
	Recipient string
	OK        bool
	Err       error
}

type SendFunc func(Order) error

type RecipientList struct {
	channels           map[string]SendFunc
	selectRecipients   func(Order) []string
	ignoreSendFailures bool
}

func NewRecipientList(
	channels map[string]SendFunc,
	selectRecipients func(Order) []string,
	ignoreSendFailures bool,
) *RecipientList {
	return &RecipientList{
		channels:           channels,
		selectRecipients:   selectRecipients,
		ignoreSendFailures: ignoreSendFailures,
	}
}

func (rl *RecipientList) Dispatch(order Order) ([]DeliveryOutcome, error) {
	recipients := rl.selectRecipients(order)
	if len(recipients) == 0 {
		return nil, errors.New(
			"recipient list resolved to zero recipients, this is almost " +
				"always a selection-rule bug, not a legitimate outcome",
		)
	}

	outcomes := make([]DeliveryOutcome, len(recipients))
	var wg sync.WaitGroup
	var firstErr error
	var mu sync.Mutex

	for i, name := range recipients {
		wg.Add(1)
		go func(i int, name string) {
			defer wg.Done()
			send, exists := rl.channels[name]
			if !exists {
				outcome := DeliveryOutcome{Recipient: name, OK: false, Err: errors.New("unknown channel")}
				outcomes[i] = outcome
				if !rl.ignoreSendFailures {
					mu.Lock()
					if firstErr == nil {
						firstErr = outcome.Err
					}
					mu.Unlock()
				}
				return
			}
			// send receives the same order value, unmodified (Order is
			// a value type here, so each goroutine already has its own copy).
			err := send(order)
			outcomes[i] = DeliveryOutcome{Recipient: name, OK: err == nil, Err: err}
			if err != nil && !rl.ignoreSendFailures {
				mu.Lock()
				if firstErr == nil {
					firstErr = err
				}
				mu.Unlock()
			}
		}(i, name)
	}

	wg.Wait()
	return outcomes, firstErr
}

func selectOrderRecipients(o Order) []string {
	recipients := []string{"fulfilment", "notify-" + o.NotifyChannel}
	if o.AmountCents >= 1_000_000 {
		recipients = append(recipients, "compliance")
	}
	return recipients
}

func main() {
	channels := map[string]SendFunc{
		"fulfilment":   func(o Order) error { fmt.Println("fulfilment got", o.ID); return nil },
		"compliance":   func(o Order) error { fmt.Println("compliance got", o.ID); return nil },
		"notify-email": func(o Order) error { fmt.Println("emailed", o.ID); return nil },
		"notify-sms":   func(o Order) error { fmt.Println("texted", o.ID); return nil },
		"notify-push":  func(o Order) error { fmt.Println("pushed", o.ID); return nil },
	}

	list := NewRecipientList(channels, selectOrderRecipients, true)

	small := Order{ID: "o-1", Country: "DE", AmountCents: 5_000, NotifyChannel: "push"}
	large := Order{ID: "o-2", Country: "US", AmountCents: 2_500_000, NotifyChannel: "email"}

	outcomesSmall, _ := list.Dispatch(small)
	fmt.Println(outcomesSmall)

	outcomesLarge, _ := list.Dispatch(large)
	fmt.Println(outcomesLarge)
}
```

Java and Rust are omitted here not because the pattern does not translate,
Spring Integration's `RecipientListRouter`, dimension 8, is itself a Java
implementation of exactly this pattern in production, but because a local
Java toolchain was not available to compile and verify a sample at authoring
time, and shipping an unverified Java sample would contradict the
verify-before-claiming discipline this catalog holds itself to. Rust was
omitted for scope. the three samples above already cover the closure-based,
dynamically-typed, and statically-typed-with-goroutine-concurrency variants
of the same dispatch mechanics.
