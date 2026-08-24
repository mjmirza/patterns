---
name: Content-Based Router
slug: content-based-router
family: 07-integration
category: Messaging
aliases: [Message Router, Smart Router, Routing Slip Router (related, distinct)]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [message-filter, recipient-list, pipes-and-filters, message-endpoint, dynamic-router, splitter, aggregator]
incompatible_with: []
verified: 2026-08-02
---

# Content-Based Router

## 1. Name, aliases, and lineage

The canonical name is Content-Based Router. It is one of the message routing
patterns catalogued in Gregor Hohpe and Bobby Woolf, *Enterprise Integration
Patterns. Designing, Building, and Deploying Messaging Solutions*,
Addison-Wesley, 2003, ISBN 0-321-20068-3, chapter 4, "Messaging Systems",
section on Message Routing. The book's own reference page states the intent as
routing a message to the correct recipient based on the message content when
"the recipient of the message is not known at compile time and needs to be
determined based on data contained in the message" ([Content-Based Router,
enterpriseintegrationpatterns.com](https://www.enterpriseintegrationpatterns.com/patterns/messaging/ContentBasedRouter.html),
verified 2026-08-02). The book uses the icon of an arrow splitting into three
labelled outputs and gives the one-line solution as "Use a Content-Based
Router to route each message to the correct recipient based on message
content" (same source, verified 2026-08-02).

The pattern is old enough that most integration middleware ships a first-class
construct for it under a product-specific name. Apache Camel calls its
implementation the Choice EIP, built from `choice`, `when`, and `otherwise`
building blocks, described as Camel's "if-then-else" and, when several `when`
clauses are chained, its content-based router
([Choice EIP, Apache Camel component reference](https://camel.apache.org/components/latest/eips/choice-eip.html),
consulted through the Apache Camel documentation site, verified 2026-08-02).
Spring Integration groups its equivalents under "Message Routing" and ships
several concrete router classes, among them `PayloadTypeRouter` and
`HeaderValueRouter` ([Spring Integration Reference Manual, Router
Implementations](https://docs.spring.io/spring-integration/reference/router/implementations.html),
verified 2026-08-02). MuleSoft's Mule runtime calls the same construct a
Choice router in its flow control category. None of these product names
replace the pattern name in this catalog. Content-Based Router is the name the
industry uses in cross-vendor conversation, and it is the name used throughout
this entry.

A naming trap worth flagging early. "Router" alone is ambiguous across the
Enterprise Integration Patterns catalog. A Content-Based Router picks ONE
destination per message from its content and the message continues to exactly
that one channel. A Recipient List sends a COPY of the message to a computed
SET of channels. A Splitter breaks one message into many messages that may
each then be routed. Confusing a Content-Based Router with a Recipient List is
the single most common misreading of this pattern, and it changes the delivery
semantics from exclusive-or to fan-out, see dimension 13.

## 2. Problem and context

A single logical message stream must be handled by more than one downstream
consumer, and which consumer handles a given message depends on data inside
that message, not on which channel it happened to arrive on.

The situation shows up in a specific, recognisable shape. An order intake
system receives every order on one queue. Domestic orders need one fulfilment
path, international orders need a different one because of customs paperwork.
A logging pipeline receives every log line on one topic, but security events
need to reach a SIEM within seconds while debug lines can wait for a nightly
batch job. A claims processor receives every insurance claim on one channel,
but a claim under five hundred dollars can auto-approve while a claim over
that threshold needs a human adjuster. In every one of these the sender does
not, and should not, know the destination. The order-placing customer has no
idea whether their order is domestic or international from a routing
perspective, the application emitting a log line has no idea whether it is a
security event, and the claim submission form does not know which adjuster
queue eventually receives the claim.

The naive fix is to make the sender decide. The order service checks the
shipping country and publishes to one of two queues directly. This couples the
sender to the full set of destinations and their selection logic, and every
new destination means a code change in the sender. The second naive fix is a
single shared consumer with a large if-else block that dispatches internally
by calling different functions. This avoids touching the sender but collapses
independent deployability, one team's routing logic sits inside a process
owned by a different team, and a bug in the international-order branch can
take down domestic-order processing because they now share a process.

Content-Based Router exists for the context where the sender must stay
decoupled from the number and identity of possible destinations, the routing
decision depends only on the message itself, and the destinations are
independently deployable services or channels rather than internal function
calls.

## 3. Forces

- **Coupling.** Favoured for the sender, sacrificed at the router. The sender
  knows nothing about destinations. The router now knows every destination and
  every routing rule, and becomes the one place that must change whenever a
  new destination or a new rule appears.
- **Latency.** Sacrificed by one hop. Every message pays the cost of arriving
  at the router, being inspected, and being re-published, compared against a
  sender that published directly to the final destination.
- **Single point of evaluation.** Favoured. The routing logic exists exactly
  once, in one place, instead of being duplicated in every sender or baked
  into every consumer's intake filter.
- **Testability of routing logic.** Favoured. The rules can be unit tested in
  isolation from both the sender and the destinations, because the router is a
  pure function from message to destination channel.
- **Operability.** Mixed. A dedicated router gives operators one place to
  watch routing health and one place to see a full audit trail of decisions,
  but it also becomes a single component whose outage stops delivery to every
  destination at once, see dimension 11.
- **Cognitive load for a reader tracing a message.** Sacrificed. Given a
  message in a destination queue, a reader cannot tell why it ended up there
  without finding and reading the router's rule set, whereas a directly
  published message shows its destination at the publish call site.
  Compensated in dimension 16 by making the decision itself an observable
  event.
- **Rule complexity growth.** A genuine risk rather than a clean trade. A
  router with two rules is trivial to reason about. A router with forty rules
  encoding business logic is a hidden business-rule engine wearing a
  messaging component's clothes, and the fix is named directly in dimension 4.
- **Coupling of destinations to a shared contract.** Favoured, and easy to
  miss. Because one router serves every destination, all destinations
  implicitly agree to accept the same message shape on their inbound channel,
  which is a form of the "aggregate contract" tension every shared
  integration component carries.

## 4. Applicability and non-applicability

Reach for a Content-Based Router when the following hold.

- The routing destination is determined entirely by data already present in
  the message, such as a message type field, a header, a monetary amount, a
  country code, or a claim category.
- The sender must remain unaware of the set of possible destinations, because
  destinations are added, removed, or reassigned independently of the sender's
  release cycle.
- Exactly one destination should receive the message for a given content
  match, an exclusive-or delivery semantic, not a broadcast.
- The routing rules are simple enough, or few enough, to be expressed as
  conditionals, a lookup table, or a small rules engine, and are owned by the
  team operating the integration layer rather than by arbitrary business
  users.
- The destinations already communicate over channels the messaging
  infrastructure understands, a queue, a topic, an HTTP endpoint the broker
  can address, so the router genuinely needs only to pick a channel, not to
  perform protocol translation as well.

Do NOT reach for Content-Based Router in these cases, and the reason is the
useful part.

- **The destination is known at compile time or configuration time and never
  varies per message.** A static one-to-one channel binding needs no router.
  Adding one here is speculative infrastructure that adds a hop and a failure
  point for a decision that was never actually dynamic.
- **Every consumer must receive every message.** That is a Publish-Subscribe
  Channel, not a router. A router that is configured with rules matching
  "everything" to every destination is a Recipient List or a Publish-Subscribe
  Channel wearing a router's name, see dimension 13.
- **The routing rules encode substantial, frequently changing business
  policy, the kind product managers edit weekly.** That belongs in a rules
  engine or a business process management tool with its own versioning,
  approval workflow, and audit trail, not in router configuration deployed
  alongside infrastructure code. A router with forty conditional branches
  encoding pricing tiers is the symptom named in dimension 11.
- **The message must be transformed, not just routed, before a destination
  can consume it.** A Content-Based Router does not translate formats. Reach
  for a Message Translator ahead of or behind the router, or a Content
  Enricher, rather than growing translation logic inside routing rules.
- **The decision requires calling out to an external system, a database
  lookup, or a slow computation, on the hot path of every single message.**
  This turns the router into a latency and availability liability shared by
  every downstream consumer. Consider caching the lookup, denormalising the
  routing key into the message ahead of time, or accepting the coupling and
  moving the decision earlier in the pipeline.
- **The set of possible destinations is itself unknown until runtime, driven
  by a registry of subscribers rather than a fixed rule set.** That is the
  Dynamic Router variant or, further still, a Recipient List computed from a
  subscription table, see dimension 13.
- **A single consumer process can happily hold the if-else itself with no
  independent deployability requirement.** A plain conditional inside one
  service is not weaker than a Content-Based Router, it is simply not the same
  problem. Introducing a message broker and a separate router component to
  solve a problem a private function already solves is the classic
  "distributed monolith" trap.

## 5. Structure

- **Message Producer.** Publishes a message onto a single inbound channel,
  with no knowledge of downstream destinations.
- **Message.** Carries a body plus metadata, typically headers or an envelope
  field, that the router inspects to make its decision. The content examined
  can be the payload itself, a header set by an upstream Content Enricher, or
  both.
- **Content-Based Router.** A message endpoint that consumes from the inbound
  channel, evaluates a set of rules against the message, and republishes to
  exactly one outbound channel chosen by those rules. It holds the mapping
  from condition to destination channel and nothing else. It does not
  transform the message body.
- **Rule Set.** The ordered or unordered collection of predicate-to-channel
  mappings the router evaluates. Modelled separately from the router
  component proper because its shape, hardcoded conditionals, a lookup table,
  an externalised rules engine, is the single largest design decision inside
  this pattern, see dimension 8.
- **Destination Channel (one or many).** Each named outbound channel the
  router can select. A router with N possible outcomes owns N outbound
  channel references, plus optionally a default or error channel for the
  unmatched case.
- **Message Consumer (per destination).** An independently deployable service
  or process that consumes from exactly one destination channel and has no
  awareness that a router, rather than a direct publisher, placed the message
  there.

## 6. ASCII structure diagram

```
+----------+
| Producer |
+----------+
     | inbound channel
     v
+----------------------------+
| Content-Based Router       |
| rule 1: type == "domestic" |
| rule 2: type == "intl"     |
| rule N: (default)          |
+----------------------------+
     | evaluates rules, exactly one edge fires
     +-----------------+-----------------+
     v                 v                 v
+--------------+  +----------+  +-------------+
| Domestic Svc |  | Intl Svc |  | Default /   |
|              |  |          |  | Dead-letter |
+--------------+  +----------+  +-------------+

Exactly one outbound edge fires per message. Producer and
consumers never see each other. The router owns the rule
set and every channel reference.
```

## 7. Dynamics

```
Producer          Inbound Channel      Content-Based Router      Outbound Channel      Consumer
   |                     |                       |                       |                 |
   |-- publish(msg) ---->|                       |                       |                 |
   |                     |-- deliver(msg) ------>|                       |                 |
   |                     |                       |-- evaluate rule set   |                 |
   |                     |                       |   against msg content |                 |
   |                     |                       |                       |                 |
   |                     |                       |   (match found: rule 1 -> Channel A)     |
   |                     |                       |-- publish(msg) ------>|                 |
   |                     |                       |                       |-- deliver(msg)->|
   |                     |                       |                       |                 |
   |                     |                       |   (no rule matched, default configured) |
   |                     |                       |-- publish(msg) --> Default Channel       |
   |                     |                       |                       |                 |
   |                     |                       |   (no rule matched, no default)          |
   |                     |                       |-- log error, dead-letter, or drop        |
```

Two timing notes worth naming. First, the evaluation step is normally
synchronous with message consumption from the inbound channel, one message
in, one routing decision, one publish out, and the router does not batch or
reorder. Second, when the router itself is stateless and idempotent per
message, retries after a transient publish failure to the outbound channel
are safe to replay from the broker's own redelivery mechanism, but when the
routing decision depends on external mutable state, a database lookup that
can change between retries, the same message can legitimately route
differently on retry, which is a design hazard covered in dimension 11.

## 8. Implementation variants

**Hardcoded conditional chain.** The router body is a sequence of if-else or
switch statements evaluated in the host language. Fastest to write, fastest
to execute, and the only variant with compile-time type safety on the
conditions. Every new rule is a code change and a redeploy of the router.
Apache Camel's Choice EIP is exactly this shape, expressed declaratively as
`choice().when(predicate).to(endpoint).otherwise().to(endpoint)` rather than
as raw host-language conditionals, but it compiles down to the same evaluate
in order, first match wins semantic
([Choice EIP, Apache Camel](https://camel.apache.org/components/latest/eips/choice-eip.html),
verified 2026-08-02).

**Declarative mapping table.** The router holds a data structure, a map from
a single field's value to a destination channel, rather than arbitrary
predicates. Spring Integration's `PayloadTypeRouter` maps Java class to
channel and its `HeaderValueRouter` maps a single header's value to a channel
name, both configured as XML or annotation mappings rather than code
([Spring Integration Reference Manual, Router
Implementations](https://docs.spring.io/spring-integration/reference/router/implementations.html),
verified 2026-08-02). This variant trades expressiveness, it can only ever
express equality on one field, for the ability to add a rule by editing
configuration rather than recompiling.

**Externalised rules engine.** The predicate-to-channel mapping is evaluated
by a general-purpose rules engine, a decision table, or an expression
language interpreted at runtime. Spring Integration's SpEL-based
`@Router`-annotated method falls partway into this category, evaluating an
arbitrary expression against the message to compute a channel name or a
`MessageChannel` reference at runtime
([Spring Integration Reference Manual, Router
Implementations](https://docs.spring.io/spring-integration/reference/router/implementations.html),
verified 2026-08-02). A full rules-engine variant, backed by something like a
Rete-algorithm engine, earns its complexity only when non-engineers must be
able to change rules without a deployment, per the non-applicability list in
dimension 4.

**Pattern-matching event filter.** The router evaluates a declarative
matching document against the whole event, rather than a single field, and
attaches a rule to a target rather than embedding a rule inside a routing
component's code. AWS EventBridge rules are this shape, a JSON event pattern
matched against `source`, `detail-type`, and nested `detail` fields, with each
matching rule invoking one or more targets
([Creating Amazon EventBridge event
patterns](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-patterns.html),
verified 2026-08-02). This variant blurs into a managed content-based routing
service rather than an application-level component, and its rule set lives in
infrastructure configuration rather than in the codebase.

**Predicate object composition.** In languages with first-class functions,
each rule is a `(Message) -> boolean` predicate paired with a destination,
held in an ordered list evaluated top to bottom. This is functionally
identical to the hardcoded conditional chain but keeps each rule as an
independently testable unit rather than a branch inside one large function,
and it composes cleanly with the Strategy pattern for the evaluation itself.

**Content-based subscription rather than active routing.** Instead of the
router deciding and pushing, consumers each register a subscription predicate
against a broker (a topic filter, a JMS message selector, an EventBridge
rule attached directly to a consumer), and the broker performs the content
match on delivery. This removes the router as a distinct component entirely
and relies on broker-native content matching. It is the correct choice when
the broker already has efficient content filtering and no single team should
own a shared routing component.

## 9. Known production uses

**Apache Camel, the Choice EIP.** Camel's routing DSL provides `choice()`,
`when(predicate)`, and `otherwise()` as first-class route-building
constructs, described in Camel's own EIP documentation as its
if-then-else and content-based routing mechanism, used to route an exchange
to one of several destination endpoints based on predicates evaluated against
the message
([Choice EIP, Apache Camel component reference](https://camel.apache.org/components/latest/eips/choice-eip.html),
verified 2026-08-02).

**Spring Integration, `PayloadTypeRouter` and `HeaderValueRouter`.** Spring
Integration ships concrete router implementations under its Message Routing
module, including a router that dispatches by the Java class of the message
payload and a router that dispatches by the value of a named message header,
each configurable through XML, Java DSL, or annotations
([Spring Integration Reference Manual, Router
Implementations](https://docs.spring.io/spring-integration/reference/router/implementations.html),
verified 2026-08-02).

**AWS EventBridge, rule-based event pattern matching.** EventBridge lets a
publisher send every event to a single event bus while EventBridge itself
evaluates each event against every rule's event pattern and forwards a
matching event to that rule's configured targets, explicitly built so the
publisher of an event needs no knowledge of which consumers will receive it
([Creating Amazon EventBridge event
patterns](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-patterns.html),
verified 2026-08-02).

**Spring Integration, SpEL-based `@Router` methods.** Beyond the fixed router
classes, Spring Integration allows a plain method annotated `@Router` to
return the destination channel name or a `MessageChannel`, computed from an
arbitrary Spring Expression Language expression evaluated against the
message, which is the framework's escape hatch for routing logic that a
single-field mapping cannot express
([Spring Integration Reference Manual, Router
Implementations](https://docs.spring.io/spring-integration/reference/router/implementations.html),
verified 2026-08-02).

## 10. Consequences

Positive.

- The message producer is fully decoupled from the number, identity, and
  even the existence of downstream consumers, so consumers can be added,
  removed, or replaced without touching the producer.
- Routing logic exists in exactly one place, which makes it possible to
  reason about, audit, and test the complete set of routing rules without
  reading every consumer's intake code.
- New destinations are added by adding a rule and a channel binding, not by
  modifying every existing sender that might produce a relevant message.
- The routing decision becomes a natural point to attach cross-cutting
  concerns, logging every decision, counting matches per rule, or enforcing
  an authorisation check before a message reaches a sensitive destination.
- When paired with a message broker, the router benefits from the broker's
  own delivery guarantees, at-least-once or exactly-once semantics, rather
  than needing to reimplement them.

Negative.

- The router becomes a single shared component whose outage or misconfiguration
  can silently stop delivery to every destination at once, see dimension 11.
- Every message pays one extra network hop and one extra serialization and
  deserialization cycle compared to direct publication.
- The rule set, if left unchecked, tends to accumulate business logic that
  properly belongs elsewhere, turning an infrastructure component into an
  undocumented, hard-to-test business rules engine.
- Tracing why a specific message ended up on a specific destination requires
  either reading the router's rule set or having deliberately instrumented
  the routing decision as an observable event, see dimension 16.
- The router couples every possible destination to a single shared message
  contract, since one set of rules must be able to interpret the content of
  every message that could conceivably arrive, which discourages destinations
  from evolving their expected input shape independently.

## 11. Failure modes and misuse

**The router grows into a business rules engine.** Symptom. A single router
component with dozens of nested conditionals encoding pricing tiers,
eligibility rules, or regulatory thresholds, changed by a different team every
sprint, deployed through the integration team's release process. Cause.
Business logic that changes on a business cadence was placed inside an
infrastructure component that changes on an engineering cadence. Fix.
Extract the decision into a dedicated business rules service or a rules
engine with its own versioning and approval flow, and reduce the router back
to a thin dispatch on the rules service's answer.

**Silent drop on unmatched content.** Symptom. Messages disappear with no
error, discovered only when a downstream team asks why expected data never
arrived. Cause. The rule set has no default or catch-all branch, and the
router's implementation treats "no rule matched" as a no-op rather than an
error. Fix. Always configure an explicit default channel, typically a
dead-letter or review queue, and alert on any traffic landing there, per
dimension 16.

**The router as an unintended single point of failure.** Symptom. Every
downstream consumer stops receiving traffic simultaneously during an
unrelated deployment or resource exhaustion event, even though the consumers
themselves are healthy. Cause. All routed traffic passes through one
router instance or one under-provisioned router cluster with no redundancy.
Fix. Run the router as a horizontally scaled, stateless component behind the
broker's own consumer-group or partition mechanism, so router capacity scales
independently of any single instance, and monitor router-specific health
signals separately from consumer health.

**Non-deterministic routing under retry.** Symptom. The same message, resent
after a transient failure, lands on a different destination the second time,
producing duplicate or conflicting downstream processing. Cause. A routing
rule depends on external mutable state, a database row that changed between
the first attempt and the retry, rather than solely on the message's own
immutable content. Fix. Either make the routing decision solely a function of
the message's content, denormalising any needed external value into the
message before it reaches the router, or make the downstream consumers
idempotent to a changed routing outcome.

**Rule ordering bugs in first-match-wins engines.** Symptom. A newly added
rule never fires, or an existing destination suddenly stops receiving
traffic it used to receive, after what looked like an additive change. Cause.
Most implementations, Camel's Choice EIP among them, evaluate rules in order
and take the first match, so a broader rule placed earlier in the list
silently shadows a narrower rule placed later. Fix. Order rules from most
specific to least specific, add an automated test asserting the full set of
expected message-to-destination mappings, and prefer engines that warn on
unreachable rules where available.

**Coupling the router to a payload shape it does not own.** Symptom. The
router breaks whenever an upstream service changes its message schema, even
though the router itself never processes the payload beyond one field. Cause.
The router's rules reach deep into the payload body, for example a nested
JSON path, rather than a stable, purpose-built header set specifically
designed to be routing metadata. Fix. Route on a small, explicitly versioned
header contract populated by a Content Enricher or the message producer
itself, and keep the deep payload body opaque to the router.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Content-Based Router | Recipient List | Publish-Subscribe Channel | Message Filter | Broker-native content subscription (JMS selector, EventBridge rule per consumer) |
|---|---|---|---|---|---|
| Delivery semantics | Exclusive, exactly one destination per message | Fan-out to a computed subset | Fan-out to every subscriber | Pass-through or drop, no branching | Exclusive, broker decides per subscriber |
| Sender coupling to destinations | None | None, but sender or router must compute the recipient set | None | None | None |
| Where the routing rule lives | One shared component | One shared component | Not applicable, all subscribers get everything | One shared component | Distributed across each consumer's own subscription |
| Adding a new destination | Edit router rule set | Edit recipient computation | Just subscribe, no change needed | Not applicable | Consumer registers its own subscription, no shared component touched |
| Single point of failure risk | High, one shared component | High, one shared component | Lower, broker fans out natively | High, one shared component | Lower, no dedicated routing component |
| Auditability of "why here" | Good if instrumented, poor otherwise | Good if instrumented, poor otherwise | Trivial, everyone always gets it | Good if instrumented | Poor, scattered across consumer configs |
| Suitable for many, frequently changing consumers | Moderate, requires router redeploy or config change | Moderate, same constraint | Excellent, zero router changes | Not applicable | Excellent, no shared component to touch |
| Complexity of the rule expression | Can be arbitrary, up to a full predicate language | Similar to router, plus recipient-set computation | None | Single boolean predicate | Bounded by broker's selector language, often SQL-92 subset or JSON pattern matching |

Reading of the table. Content-Based Router wins where exactly one destination
should receive a message and that decision benefits from being centralised
and auditable in one place. Recipient List wins where more than one, but not
all, destinations should receive a message. Publish-Subscribe Channel wins
where the answer is genuinely everyone. Message Filter wins where the only
decision is keep-or-drop rather than pick-a-destination. Broker-native
subscription wins where the number of independently evolving consumers is
large enough that a shared router component becomes the bottleneck for
change, at the cost of losing one central place to audit routing decisions.

## 13. Related and incompatible patterns

- **Recipient List.** The pattern most often confused with Content-Based
  Router, and the distinction is exact. A Content-Based Router selects one
  channel from a fixed or rule-derived set, exclusive-or semantics. A
  Recipient List computes a set of channels and sends the message to every
  one of them, fan-out semantics. A router whose rules are all written to
  match and forward to multiple channels simultaneously has quietly become a
  Recipient List and should be renamed and reasoned about as one.
- **Message Filter.** A degenerate, single-outcome special case. A Message
  Filter is a Content-Based Router with exactly one real destination and an
  implicit "drop" as the only alternative outcome. Any router with exactly
  one populated branch and a default of nothing should probably be simplified
  to a Message Filter, which makes the drop-on-no-match behaviour explicit
  rather than implicit.
- **Dynamic Router.** A variant where the set of destination channels is
  itself discovered or negotiated at runtime, often via a control channel the
  router subscribes to, rather than fixed in the router's own configuration.
  Reach for a Dynamic Router when destinations register and deregister
  themselves rather than being known ahead of time by whoever configures the
  static router.
- **Content Enricher.** Frequently sits immediately upstream of a
  Content-Based Router. When the field a router needs to make its decision
  is not present in the raw incoming message, a Content Enricher adds it,
  keeping the router's own rules simple and keeping the enrichment lookup
  logic, which is often what actually needs caching or external calls, out of
  the router.
- **Pipes and Filters.** The architectural umbrella. A Content-Based Router
  is itself one filter in a pipes-and-filters composition, one that happens to
  have multiple possible output pipes instead of the usual single output pipe
  every other filter has.
- **Splitter and Aggregator.** Composable but address a different axis. A
  Splitter breaks one message into several before routing, an Aggregator
  reassembles several messages into one. Neither replaces routing, and a
  Content-Based Router commonly sits downstream of a Splitter to distribute
  the resulting sub-messages to different handlers.
- **Message Endpoint.** The general parent category. A Content-Based Router
  is a specialised message endpoint that consumes from one channel and
  produces to a channel chosen dynamically, rather than to a single fixed
  channel.
- **Service Locator or Registry lookup inside application code.** Conflicts
  in effect, not in principle. Reaching into a service registry inside a
  handler to decide where to forward work internally reproduces this pattern
  without a broker and without the auditability a dedicated router component
  provides, and it hides a genuinely architectural decision inside application
  code.

## 14. Refactoring path in and out

Introducing the pattern into a system that currently has senders publishing
directly, or conditionally, to multiple destinations. Ordered steps.

1. Identify every sender currently containing a branch, a switch, or an
   if-else, that decides between two or more outbound channels or endpoints
   based on message content. List every distinct condition and its current
   destination.
2. Confirm the condition depends solely on data already present in, or easily
   attachable to, the message, not on state private to the sender that cannot
   travel with the message.
3. Stand up a single new inbound channel that every affected sender will
   publish to instead of publishing directly to destinations. Do not remove
   the old direct publication yet.
4. Build the router as a new, separately deployable component consuming that
   inbound channel, reproducing the exact same conditions and destinations the
   senders currently encode, verified with the type-per-rule test described in
   dimension 15.
5. Switch one sender at a time to publish to the new inbound channel instead
   of its old direct destinations, and remove that sender's now-dead
   conditional. Verify traffic reaches the correct destination through the
   router before moving to the next sender.
6. Once every sender publishes through the router, delete the router's
   default-channel fallback only after confirming, from the observability
   signals in dimension 16, that no traffic has landed there over a
   representative window, since silent unmatched traffic during migration is
   exactly the failure mode named in dimension 11.
7. Document the rule set as the single source of truth for "why does this
   message go here", replacing whatever tribal knowledge previously lived
   inside each sender's conditional.

Removing the pattern when it stops earning its place. Signals include a
router whose rule set has collapsed to a single always-true condition because
consolidation left only one real destination, or a router whose rules have
grown into business logic that belongs in a dedicated rules engine per
dimension 11.

1. Confirm the rule set genuinely has one live outcome, or confirm the
   business-logic extraction target can already own the decision instead.
2. For the single-outcome case, redirect every sender to publish directly to
   the one remaining destination channel, verifying no other rule has traffic
   first.
3. For the rules-engine extraction case, replace the router's internal rule
   evaluation with a call to the new rules service, keeping the router as a
   thin dispatcher on the service's answer, then over time move even that
   dispatch responsibility to wherever consumes the rules service's decision
   directly.
4. Decommission the router component and its inbound channel only after a
   full observation window confirms no traffic still depends on it, and after
   downstream consumers have been repointed to their new, direct source.

## 15. Testing and verification

Easier because of the pattern.

- The complete routing rule set can be tested in total isolation from every
  producer and every consumer, because a router is a pure function from
  message to destination channel with no side effects beyond the final
  publish.
- A single table-driven test, one row per rule plus one row for the default
  case, gives complete coverage of the routing decision without needing to
  stand up any real downstream service.
- Because the router does not transform the payload, tests never need to
  assert anything about payload shape, only about which channel a given
  message ends up on, which keeps the test surface small even as the payload
  schema evolves independently.

Harder because of the pattern.

- An end-to-end test that a message genuinely reaches the correct running
  consumer now spans at least three components, sender, router, and
  consumer, each of which may need to be running or faked for the test to say
  anything real about production behaviour.
- A rule that shadows another rule, the ordering bug from dimension 11, is
  invisible to a test that only checks each rule individually rather than
  checking the full ordered rule set against a matrix of inputs.

Techniques that apply.

- **Rule matrix test.** One test case per condition-to-destination mapping,
  including at least one message engineered to satisfy no rule, asserting the
  configured default or dead-letter behaviour rather than assuming it.
- **Rule ordering regression test.** For first-match-wins engines, a test
  that deliberately constructs a message matching two rules and asserts which
  one wins, so that reordering the rule set is a change a test suite catches
  rather than a silent behaviour shift.
- **Contract test on the routing header set.** Since the router depends on a
  small, stable set of fields, a contract test asserting every upstream
  producer populates those fields correctly protects the router from an
  upstream schema change that silently starves one of its rules.
- **Fault-injection test on the default path.** Deliberately publish a
  message that matches nothing, in a staging environment wired to real
  alerting, and confirm the alert fires, closing the loop on the silent-drop
  failure mode rather than trusting the configuration alone.

## 16. Observability signals

The pattern hides "why did this message go here" from the source code
entirely, so that answer has to live in telemetry or it does not exist for an
operator at 3 a.m.

What to record.

- On every routing decision, a structured log line or span attribute carrying
  the message identifier, the matched rule identifier or condition
  description, and the destination channel chosen. This single field is what
  turns dimension 14's "why does this go here" from tribal knowledge into a
  queryable fact.
- A counter of routed messages labelled by matched rule and destination
  channel, which is the primary dashboard signal, since its distribution
  answers whether the traffic mix matches expectations.
- A separate, alertable counter for messages that hit the default or
  dead-letter channel, since this is the router's single most dangerous
  silent failure mode and deserves its own alert threshold independent of
  general error rates.
- A histogram of time spent evaluating the rule set per message, particularly
  important for the externalised rules engine and pattern-matching variants
  from dimension 8, where evaluation cost is not a fixed compile-time
  constant.
- End-to-end latency from producer publish to consumer receipt, decomposed
  into producer-to-router and router-to-consumer segments, so a latency
  regression can be localised to the router hop specifically rather than
  blamed on "the pipeline" generally.

A healthy instance on a dashboard. The per-rule counter distribution tracks
the expected business mix and moves only in step with known changes, deploys,
seasonality, marketing campaigns. The default-channel counter sits at or near
zero. Evaluation latency is flat and small relative to network transit time.

A failing instance. The default-channel counter climbs, which means either an
upstream schema drifted or a genuinely new message shape has appeared that no
rule anticipated. One rule's counter drops to zero while its sibling rules
keep firing, which usually means an upstream producer stopped populating the
field that rule depends on, or a rule-ordering change shadowed it, per
dimension 11. Evaluation latency develops a long tail correlated with one
particular rule, which points at an externalised lookup or expensive
predicate inside that rule specifically rather than at the router as a whole.

## 17. Security and privacy implications

The pattern is not neutral on security, because it is, by construction, a
single component that inspects the content of every message flowing through
an integration layer, which makes it a natural place both to add protection
and to introduce a new attack surface.

**A single point of content inspection is a natural policy enforcement
point, and also a natural target.** Because the router already reads every
message's routing-relevant fields, it is a reasonable place to enforce a
coarse authorisation check, refusing to route a message tagged for a
destination the producer's identity is not entitled to reach, before the
message ever leaves the router. Conversely, an attacker who can influence
routing-relevant fields, a header the producer sets from user input rather
than from trusted server-side logic, can potentially redirect a message to an
unintended destination. Populate routing fields from data the sender's own
trust boundary controls, never directly from unvalidated client input.

**Rule set changes are a privileged operation and should be treated as
one.** Because the rule set determines where every message in the system can
end up, a change to it is functionally equivalent to a change in system
access control for message flow. Treat rule-set changes with the same review
and audit rigour as a change to firewall rules or IAM policy, rather than as
an ordinary code change, especially in the externalised rules engine variant
from dimension 8 where a rule can be edited without a code review at all.

**Denial of service through expensive routing decisions.** If a rule's
predicate performs an external call, a database lookup, or an expensive
regular expression against attacker-influenced content, a flood of messages
engineered to hit that specific rule can exhaust the router's own capacity
and stop delivery to every destination it serves, not just the one under
attack. Bound the cost of every predicate and apply a per-message evaluation
timeout inside the router itself.

On privacy, the router's observability signals from dimension 16 are the
practical concern rather than the routing logic itself. Logging the full
message content alongside a routing decision, for debugging convenience,
turns the router's own logs into a copy of every payload it ever routed,
including any personal data those payloads carried. Log the routing-relevant
fields and the decision outcome, not the full message body, and apply the
same retention and access controls to router audit logs that apply to the
data the messages themselves carry.

## 18. References

1. Gregor Hohpe, Bobby Woolf. *Enterprise Integration Patterns. Designing,
   Building, and Deploying Messaging Solutions*. Addison-Wesley, 2003.
   ISBN 0-321-20068-3. Chapter 4, Messaging Systems, Message Routing section.
   Source of the pattern name, intent, icon, and the exclusive-destination
   framing distinguished from Recipient List.
2. Gregor Hohpe, Bobby Woolf. "Content-Based Router."
   https://www.enterpriseintegrationpatterns.com/patterns/messaging/ContentBasedRouter.html
   Verified 2026-08-02. The book's own online reference page, used for the
   verbatim problem and solution statement quoted in dimension 1 and 2.
3. Apache Software Foundation. "Choice EIP." Apache Camel component
   reference. https://camel.apache.org/components/latest/eips/choice-eip.html
   Verified 2026-08-02. Source for Camel's implementation of Content-Based
   Router as the Choice EIP and its first-match-wins evaluation order.
4. VMware, Spring Team. "Router Implementations." Spring Integration
   Reference Manual.
   https://docs.spring.io/spring-integration/reference/router/implementations.html
   Verified 2026-08-02. Source for `PayloadTypeRouter`, `HeaderValueRouter`,
   `RecipientListRouter`, and the SpEL-based `@Router` annotation.
5. Amazon Web Services. "Creating Amazon EventBridge event patterns." AWS
   EventBridge User Guide.
   https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-patterns.html
   Verified 2026-08-02. Source for the EventBridge event-pattern production
   use and the pattern-matching implementation variant.

## Code examples

Three languages chosen for genuinely different idiomatic shapes. TypeScript
shows the predicate-list variant common in Node.js messaging middleware. Go
shows the same shape using Go's native function values and no inheritance,
since Go has none to offer. Python shows a declarative mapping-table variant,
closest in spirit to Spring Integration's `HeaderValueRouter`.

### TypeScript

```typescript
type OrderMessage = {
  orderId: string;
  country: string;
  amountCents: number;
};

type Rule = {
  name: string;
  matches: (msg: OrderMessage) => boolean;
  destination: string;
};

class ContentBasedRouter {
  private rules: Rule[] = [];
  private defaultDestination = "review-queue";

  addRule(rule: Rule): this {
    this.rules.push(rule);
    return this;
  }

  route(msg: OrderMessage): { destination: string; ruleName: string } {
    for (const rule of this.rules) {
      if (rule.matches(msg)) {
        return { destination: rule.destination, ruleName: rule.name };
      }
    }
    return { destination: this.defaultDestination, ruleName: "default" };
  }
}

const router = new ContentBasedRouter()
  .addRule({
    name: "high-value-international",
    matches: (m) => m.country !== "DE" && m.amountCents > 100_000,
    destination: "manual-review-queue",
  })
  .addRule({
    name: "international",
    matches: (m) => m.country !== "DE",
    destination: "international-fulfilment-queue",
  })
  .addRule({
    name: "domestic",
    matches: (m) => m.country === "DE",
    destination: "domestic-fulfilment-queue",
  });

const decision = router.route({ orderId: "o-1", country: "US", amountCents: 250_00 });
console.log(decision.destination, decision.ruleName);
```

### Go

```go
package main

import "fmt"

type OrderMessage struct {
	OrderID     string
	Country     string
	AmountCents int
}

type Rule struct {
	Name        string
	Matches     func(OrderMessage) bool
	Destination string
}

type ContentBasedRouter struct {
	rules              []Rule
	defaultDestination string
}

func (r *ContentBasedRouter) AddRule(rule Rule) *ContentBasedRouter {
	r.rules = append(r.rules, rule)
	return r
}

func (r *ContentBasedRouter) Route(msg OrderMessage) (destination string, ruleName string) {
	for _, rule := range r.rules {
		if rule.Matches(msg) {
			return rule.Destination, rule.Name
		}
	}
	return r.defaultDestination, "default"
}

func main() {
	router := &ContentBasedRouter{defaultDestination: "review-queue"}
	router.AddRule(Rule{
		Name:        "high-value-international",
		Matches:     func(m OrderMessage) bool { return m.Country != "DE" && m.AmountCents > 100_000 },
		Destination: "manual-review-queue",
	}).AddRule(Rule{
		Name:        "international",
		Matches:     func(m OrderMessage) bool { return m.Country != "DE" },
		Destination: "international-fulfilment-queue",
	}).AddRule(Rule{
		Name:        "domestic",
		Matches:     func(m OrderMessage) bool { return m.Country == "DE" },
		Destination: "domestic-fulfilment-queue",
	})

	dest, rule := router.Route(OrderMessage{OrderID: "o-1", Country: "US", AmountCents: 25000})
	fmt.Println(dest, rule)
}
```

### Python

The declarative mapping-table variant, closest to a `HeaderValueRouter`,
matching a single field's value against a lookup table rather than arbitrary
predicates.

```python
from dataclasses import dataclass


@dataclass
class OrderMessage:
    order_id: str
    order_type: str
    amount_cents: int


class HeaderValueRouter:
    def __init__(self, field: str, mapping: dict[str, str], default: str) -> None:
        self._field = field
        self._mapping = mapping
        self._default = default

    def route(self, msg: OrderMessage) -> str:
        value = getattr(msg, self._field)
        return self._mapping.get(value, self._default)


router = HeaderValueRouter(
    field="order_type",
    mapping={
        "domestic": "domestic-fulfilment-queue",
        "international": "international-fulfilment-queue",
    },
    default="review-queue",
)

if __name__ == "__main__":
    msg = OrderMessage(order_id="o-1", order_type="international", amount_cents=25000)
    print(router.route(msg))
    unmatched = OrderMessage(order_id="o-2", order_type="unknown", amount_cents=100)
    print(router.route(unmatched))
```
