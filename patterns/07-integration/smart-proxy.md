---
name: Smart Proxy
slug: smart-proxy
family: 07-integration
category: Enterprise Integration
aliases: [Direct Reply-To, Reply Interception Proxy, Tracking Proxy]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [return-address, correlation-identifier, request-reply, wire-tap, content-based-router]
incompatible_with: [event-message]
verified: 2026-08-13
---

## 1. Name, aliases, and lineage

The canonical name is Smart Proxy. Gregor Hohpe and Bobby Woolf catalogued it in
"Enterprise Integration Patterns, Designing, Building, and Deploying Messaging
Solutions" (Addison-Wesley, 2003), in the System Management chapter, alongside
Wire Tap, Message History, Detour, and Control Bus. The book's own companion
site states the problem it answers this way, verified live on the enterprise
integration patterns site on 2026-08-13. "How can you track messages on a
service that publishes reply messages to the Return Address specified by the
requestor?" And the solution it names. "Use a Smart Proxy to store the Return
Address supplied by the original requestor and replace it with the address of
the Smart Proxy. When the service sends the reply message route it to the
original Return Address"
(enterpriseintegrationpatterns.com/patterns/messaging/SmartProxy.html, verified
2026-08-13). The site frames this as the direct successor to a limitation of
Wire Tap. "A pair of Wire Taps can be used to track messages that flow through
a component. However, this approach assumes that the component publishes
messages to a fixed output channel. However, many service-style components
publish reply messages to the channel specified by the Return Address included
in the request message" (same source). A Wire Tap works because it copies
traffic off a channel whose destination is known in advance. A reply message
whose destination is a per-message, data-driven Return Address has no fixed
channel to tap, so the pattern that generalises Wire Tap for that case has to
sit inside the reply routing decision itself rather than beside it.

The one production system on record that names its own implementation of this
exact mechanism is RabbitMQ, whose broker feature is literally called Direct
Reply-To. RabbitMQ's own documentation confirms the broker "transparently
rewrites reply-to" so that replies are delivered through a pseudo-queue tied to
the requesting connection rather than to a queue the requestor manages itself
(rabbitmq.com/docs/direct-reply-to, verified 2026-08-13, full quotation and
mechanics in dimension 8). That is a genuine, sourced alias, not a guess, and it
is used here as the frontmatter alias precisely because it is the closest thing
the pattern has to an alternate catalog name in a real, shipping system. Two
further terms circulate informally among integration engineers who have not
read the catalog by name, Reply Interception Proxy and Tracking Proxy. Neither
is attributable to a single documented source the way Direct Reply-To is, they
are recorded here as engineering judgement about common usage, not as sourced
catalog aliases, and a reader should weigh them accordingly.

Two other things called "proxy" in nearby literature are worth separating from
this pattern by name alone, because the overlap in vocabulary is a real source
of confusion in code review.

- **GoF Proxy, the "smart proxy" applicability case.** The structural Proxy
  pattern in Gamma, Helm, Johnson, and Vlissides' *Design Patterns* names four
  applicability cases, remote proxy, virtual proxy, protection proxy, and a
  fourth in-process case. A widely used secondary reference on the GoF catalog
  labels that fourth case "smart proxy" and describes it as an object that
  performs additional bookkeeping on every access to a wrapped object, counting
  references so the real object can be freed once nothing points at it, loading
  a persisted object into memory on first access, or checking a lock before
  letting a call through (sourcemaking.com/design_patterns/proxy, verified
  2026-08-13). That is a single-process, in-memory object wrapper around one
  reference. It shares a name with the pattern in this entry and shares
  nothing else. It has no message, no channel, no network hop, and nothing that
  could be called a Return Address. A reader who has met the GoF proxy first
  and hears "smart proxy" in an integration conversation should not assume the
  two are related.
- **A reverse proxy or API gateway with routing rules.** A general-purpose
  gateway that forwards HTTP requests based on path or header rules is a
  Message Router, not a Smart Proxy, unless it specifically captures and
  substitutes a caller-supplied reply destination the way this pattern
  describes. Most gateways never do that, because most gateways sit in front of
  synchronous request-response protocols where the reply travels back over the
  same connection the request arrived on and there is no separate Return
  Address to intercept in the first place.

The useful test for whether a component is genuinely a Smart Proxy in the
Hohpe and Woolf sense is narrow and mechanical. does it read a Return Address
out of an inbound message, remember it under a key, replace it with its own
address before forwarding, and later use that remembered value to redirect the
reply. If any one of those four steps is missing, the component is something
else, most often a plain Message Router or a plain Content Enricher.

## 2. Problem and context

A team wants the same operational visibility into a Request-Reply exchange
that a Wire Tap already gives them on any ordinary point-to-point channel, a
copy of every message going by, without touching the service or the client.
Wire Tap solves that cleanly when the channel is fixed, defined once in
configuration, and every message on it goes to the same place. A service that
implements Return Address does not behave that way on its reply leg. Each
requestor supplies its own address in the request, the service reads that
address out of the message it was just handed, and the reply for requestor A
goes somewhere different from the reply for requestor B, decided per message,
at runtime, by data the service did not choose. Tapping a channel whose
destination changes on every message tells an observer nothing useful about
where any single reply actually went, because there is no one channel to tap.

The context is specifically a Request-Reply exchange over an asynchronous
messaging fabric, a queue, a topic, or a broker connection, where the reply
route is carried in message metadata rather than fixed by wiring. This is
exactly the situation Return Address exists to solve for the client and
service, and it is exactly the situation that defeats a naive Wire Tap for an
operator who wants to observe the traffic without being either the client or
the service. The operational need that creates this problem shows up
repeatedly in practice. an integration team supports a shared service used by
many internal consumers and needs latency and error data per consumer without
asking every consumer team to add logging on their own side, a compliance
requirement demands proof that a specific reply reached its intended requestor
and how long that took, or a platform team is debugging an intermittent issue
where replies appear to be delayed or lost and needs to see both legs of the
exchange from one vantage point rather than reconciling two different teams'
independent logs after the fact.

The pattern does not apply, and has nothing to intercept, outside a genuine
Request-Reply exchange. A pure Event Message, published once with no reply
expected, carries no Return Address for a Smart Proxy to capture in the first
place, which is why this entry lists Event Message as incompatible rather than
merely out of scope. A synchronous protocol where the reply travels back over
the same connection the request used, a plain HTTP request-response cycle
being the obvious example, also has no separate reply address to substitute,
because the return path is the transport connection itself rather than a piece
of message data. The pattern belongs specifically to the family of protocols
and buses where Return Address is a real, addressable field carried alongside
the payload.

## 3. Forces

**Transparency to both endpoints versus a new stateful hop.** The strongest
force in favour of this pattern is that neither the requestor nor the service
has to change. The requestor still supplies its own Return Address exactly as
it always did, the service still reads whatever Return Address the message
carries and replies there exactly as it always did. All of the new behaviour
lives entirely inside the proxy. The price paid for that transparency is a new
component that must remember state, per in-flight request, for as long as that
request is outstanding, which is the opposite of the stateless, fire-and-move-on
posture most messaging components are built around.

**Observability versus latency and availability risk.** Every request and
every reply for a tracked exchange now makes an extra hop through the proxy on
both legs, not one leg. That hop adds latency, however small, to every single
call, and it adds a new component whose own uptime now bounds the effective
uptime of the service it observes, even though the service itself may be
perfectly healthy. The pattern accepts this cost deliberately, because the
alternative, changing the service's own code to add the same visibility, is
often unavailable in the exact cases this pattern is reached for, a vendor
service, a legacy system nobody wants to touch, or a service owned by a
different team on a release cycle the observing team does not control.

**Correlation correctness versus concurrency.** The proxy must be able to tell
which stored Return Address belongs to which incoming reply when many requests
are in flight to the same service at once. This forces a dependency on
Correlation Identifier that is not optional the way it sometimes is in a
simple one-request-at-a-time integration. Get the correlation wrong and the
proxy does not merely lose data, it delivers requestor A's reply to requestor
B, a silent misdelivery that is far worse than the visibility gap the pattern
was built to close.

**Centralised control versus a new single point of failure.** Concentrating
tracking, timing, and forwarding logic in one component makes that logic easy
to change, audit, and reason about in one place. It also means that component
is now on the critical path of every tracked exchange in both directions, so
its failure modes, memory growth, a crash that loses in-flight correlation
state, a slow downstream write to a monitoring store, become failure modes of
the tracked service by extension, whether or not the service itself is
implicated.

**Faithful pass-through versus the temptation to do more.** The pattern is
narrowly scoped to substitution and restoration of one header field. It is
built to observe, not to change the meaning of the exchange. The moment the
proxy starts altering payload content, dropping messages it judges
uninteresting, or making routing decisions the original service would not have
made, it stops being a Smart Proxy and becomes a different, more invasive
component, typically a Content Filter or a full Message Router applied to
business logic rather than to a single tracking header. This is a boundary
worth holding on purpose, because a tracking component that also changes
behaviour is much harder to reason about and much easier to blame incorrectly
during an incident.

## 4. Applicability and non-applicability

Reach for Smart Proxy when.

- The service being observed cannot be modified, because it belongs to a
  vendor, a different team, a legacy system on its own release cadence, or a
  third-party integration where source access simply does not exist.
- The exchange is a genuine Request-Reply pair over an asynchronous channel
  where the reply destination is carried as a Return Address in the message
  rather than fixed by static wiring, so a plain Wire Tap on the reply side has
  nothing to attach to.
- Operational data, per-hop latency, error rates, reply arrival confirmation,
  needs to exist independent of whatever logging discipline the service itself
  happens to have, because the observing team cannot rely on the service's own
  instrumentation being complete, correct, or even present.
- The visibility is needed for one specific Request-Reply service or a small
  set of them, not for an entire multi-hop pipeline, where Message History or a
  full distributed tracing deployment would answer a broader question at a
  broader cost.
- A migration or consolidation effort needs to insert a tracking or metering
  point in front of an existing service without a coordinated release with
  every consumer of that service, since only the routing configuration in
  front of the proxy needs to change, not any client code.

Do NOT reach for Smart Proxy in these cases, and the reason matters more than
the rule.

- **The service can simply be changed.** If the team that owns the service can
  add its own logging, its own Message History entry, or its own metrics
  emission directly, that is strictly less risky than adding a new stateful hop
  in front of it, because it avoids creating a second component whose own
  failure modes become the service's failure modes. Reach for Smart Proxy only
  once direct instrumentation has been ruled out, not before.
- **The exchange is a plain synchronous call.** A REST request-response pair,
  a gRPC unary call, or any protocol where the reply travels back over the same
  connection the request used has no separate Return Address field to
  substitute. Ordinary reverse-proxy or API gateway logging already gives full
  visibility here at a fraction of the engineering cost, because there is
  nothing asynchronous to correlate.
- **The message is a one-way event with no reply.** An Event Message publishes
  once and expects nothing back. There is no Return Address in the message and
  nothing for a Smart Proxy to intercept, which is the concrete reason this
  entry marks Event Message as incompatible rather than simply irrelevant.
- **A full distributed tracing deployment already covers this service.** If
  every hop, including this one, is already instrumented with a correlation
  token and a tracing collector, building a second, narrower tracking mechanism
  in front of one service duplicates effort and risks disagreeing with the
  tracing data during exactly the incident where agreement matters most.
  Extend the existing tracing instrumentation to this service instead.
- **The organisation cannot commit to operating a new stateful component.**
  A Smart Proxy that is never monitored for its own correlation table growth,
  memory use, or crash recovery becomes, over time, the least observed part of
  a system built specifically to make other things observable. If nobody is
  going to own that operational burden, the pattern's cost outweighs its
  benefit before it is even deployed.
- **The volume is high enough that the extra hop is itself the bottleneck.**
  On a very high throughput service, doubling the number of network hops per
  exchange and adding a correlation table write per request can become the
  binding constraint on total system throughput. A sampled approach, or an
  infrastructure-level implementation like RabbitMQ's Direct Reply-To that
  avoids a persisted correlation table altogether, is the better fit at that
  scale, discussed in dimension 8.

## 5. Structure

Five participants, named by the role each plays.

- **Requestor.** The original client of the Request-Reply service. Sets its
  own Return Address, its own reply channel, and a Correlation Identifier on
  the outgoing request, exactly as it would if no Smart Proxy existed. It never
  learns that a proxy is in the path.
- **Smart Proxy.** The intermediary this pattern is named for. Owns two
  things, a Correlation Table mapping each in-flight Correlation Identifier to
  the Return Address the Requestor originally supplied, and its own dedicated
  reply channel that it listens on. On an incoming request it records the
  original Return Address, overwrites the Return Address field with its own
  reply channel, and forwards the message unchanged otherwise. On an incoming
  reply it looks up the Correlation Identifier, retrieves the original Return
  Address, and forwards the reply there, unmodified, using a Message Router.
- **Request-Reply Service.** The real backend being observed. It never knows
  the proxy exists. It reads whatever Return Address arrives on the request it
  receives and replies there, exactly as it always has, because that address
  now happens to belong to the proxy rather than to the original Requestor.
- **Correlation Table.** The proxy's own state, a keyed store from Correlation
  Identifier to the original Return Address, plus, in any implementation
  intended for production, an eviction policy so an unanswered request does not
  occupy a table entry forever.
- **Reply Router.** The forwarding step inside the proxy that, once a reply's
  original Return Address has been recovered from the Correlation Table, sends
  that reply on to it. The catalog description names this explicitly as a
  Message Router, and it is deliberately the simplest possible one, a single
  lookup and a single forward, with no content inspection of the payload
  itself.

A Smart Proxy is frequently paired with an internal Wire Tap that copies the
request and reply pair it observes to a separate monitoring or storage
channel, since capturing the pair is the entire operational reason the pattern
was reached for in the first place. That pairing is a common composition, not
a required structural participant, and is discussed further in dimension 13.

## 6. ASCII structure diagram

```
   +---------------+          +--------------------------------+
   |   Requestor   |          |           Smart Proxy           |
   |---------------|          |----------------------------------|
   | ReplyChannel R|          | Correlation Table. id -> Address |
   +---------------+          | Own Reply Channel. P             |
          |                   +--------------------------------+
          | request                    |              ^
          | ReplyTo=R                  | rewrite      | restore
          | CorrId=C                   | ReplyTo:=P   | ReplyTo:=R
          v                            v              |
   +----------------------------------------------------------+
   |                    Request Channel                        |
   +----------------------------------------------------------+
                              |                              ^
                              | forwarded request            | reply
                              | ReplyTo=P, CorrId=C           | sent to P
                              v                              |
                   +------------------------------------------+
                   |          Request-Reply Service            |
                   |  (replies to whatever ReplyTo it reads,   |
                   |   with no knowledge P is not the original |
                   |   requestor)                              |
                   +------------------------------------------+
```

## 7. Dynamics

The runtime flow has two legs, and the property worth stating plainly is that
the Smart Proxy sits on both of them, request and reply, not merely on the
reply.

```
Requestor            Smart Proxy                       Service
   |                     |                                 |
   |-- Request --------->|                                 |
   |  ReplyTo=R          | table[C] := R                   |
   |  CorrId=C           | rewrite ReplyTo := P            |
   |                     |-- Request ---------------------->|
   |                     |  ReplyTo=P, CorrId=C             |
   |                     |                                 | process
   |                     |<-- Reply -------------------------|
   |                     |  sent to P, CorrId=C             |
   |                     | lookup table[C] -> R             |
   |                     | evict table[C]                   |
   |<-- Reply -----------|                                 |
   |  forwarded          |                                 |
   |  unmodified         |                                 |
   |  CorrId=C           |                                 |
```

Two properties of this sequence are worth calling out because they are easy to
get wrong in a first implementation. First, the substitution on the request
leg must happen before the message reaches the service, and the restoration on
the reply leg must happen strictly after the correlation lookup succeeds, never
before, or a reply that arrives with an unrecognised or already-consumed
Correlation Identifier will be forwarded to a stale or empty address rather
than routed to a Dead Letter Channel where an operator can actually see the
problem. Second, the two legs are asynchronous with respect to each other.
Nothing in the sequence blocks the proxy from accepting a second request from
a different Requestor while the first request's reply is still outstanding,
which is exactly why the Correlation Table has to be keyed correctly and why
Correlation Identifier collisions are a real, not theoretical, failure mode,
covered in dimension 11.

## 8. Implementation variants

**Persisted correlation table, the catalog form.** A dedicated intermediary
service or library holds an explicit map from Correlation Identifier to
original Return Address, in memory or in a fast external store, exactly as
Hohpe and Woolf describe it. This is the most flexible variant, because the
proxy is a normal, independently deployable component that can be built with
whatever integration framework a team already uses, and it is the variant the
code examples in this entry implement. Its cost is the one this entry has
returned to repeatedly, a piece of durable-enough state that must be sized,
evicted, and monitored, or it silently grows without bound.

**Broker-native address rewriting, no persisted table at all.** RabbitMQ's
Direct Reply-To feature implements the identical mechanism at the broker
layer, and it avoids the correlation table entirely by tying the substitute
address to the requesting connection rather than to a stored lookup value.
RabbitMQ's own documentation states that in AMQP 0.9.1, "RabbitMQ transparently
rewrites reply-to to amq.rabbitmq.reply-to.<opaque-suffix>" where the suffix
identifies the requester's own connection, and that "the responder's AMQP 1.0
session or AMQP 0.9.1 channel process delivers the reply directly to the
requester's session/channel process without going through an actual queue"
(rabbitmq.com/docs/direct-reply-to, verified 2026-08-13). This is the strongest
production realisation of the pattern surveyed for this entry, because it
solves the exact stateful-table cost named as this pattern's central force in
dimension 3 by making the substitution a property of the live connection
itself rather than a fact that has to be remembered and evicted separately.
The trade is that it works only within the broker's own connection lifetime,
it cannot forward a reply to a Requestor that is no longer connected, which the
catalog form, with a durable table and a durable reply channel, can in
principle still do.

**Protocol-native substitution over WS-Addressing.** In a SOAP-based
integration, the ReplyTo header block defined by WS-Addressing carries exactly
the Return Address this pattern operates on, and the W3C specification is
explicit that it "provides the value for the reply endpoint property" so a
service knows where to direct its response (w3.org/TR/ws-addr-core, verified
2026-08-13). Apache CXF, a widely used open-source implementation of JAX-WS,
implements this directly, and its own documentation confirms that
"WS-Addressing allows for a decoupled endpoint to be used for receiving the
response and CXF will then correlate it with the appropriate request," with an
AddressingProperties API that lets calling code call setReplyTo to a different
address than the original sender's own endpoint
(cxf.apache.org/docs/ws-addressing.html, verified 2026-08-13). A gateway built
on this stack implements Smart Proxy by setting its own decoupled endpoint as
the ReplyTo value before forwarding a SOAP request onward, then correlating the
asynchronous response back to the caller using the RelatesTo relationship the
specification defines for exactly this purpose. The specification's own
security considerations section places the burden of validation and
authentication on the intermediary itself, before it acts on any WS-Addressing
construct, precisely so an unauthenticated party cannot redirect a message
(w3.org/TR/ws-addr-core, verified 2026-08-13), which is a direct, sourced
statement of the security concern this entry returns to in dimension 17.

**Gateway-managed connection identity, the persistent-connection form.** A
WebSocket gateway that keeps a live, addressable connection per client is
performing a long-lived version of the same substitution, with the connection
identifier standing in for a Return Address that lasts the life of the
connection rather than the life of one request. AWS API Gateway's WebSocket
support works this way. a backend service posts to a path shaped like
`/{stage}/@connections/{connectionId}` on the gateway's Management API to
deliver an asynchronous message to a specific connected client, and the
gateway is the only component that actually holds the live socket
(docs.aws.amazon.com, API Gateway WebSocket connections guide, verified
2026-08-13). The backend never talks to the client directly, it always talks
through the gateway, which is functionally identical to a Smart Proxy that
never lets go of the reply channel it substituted, because the substitution
and the connection are the same lifetime.

**Notably absent from the two most common open-source integration
frameworks.** Apache Camel's own catalog of the System Management EIPs it
implements lists ControlBus, Detour, Wire Tap, Message History, Log, and Step,
and does not include a named Smart Proxy implementation
(camel.apache.org/components/latest/eips/enterprise-integration-patterns.html,
verified 2026-08-13). A team using Camel that wants this exact behaviour has to
compose it from a Content Enricher that rewrites the header, a Correlation
Identifier-keyed Aggregator, and a Recipient List, rather than reaching for a
single named DSL keyword the way it can for Wire Tap or Message History. This
is worth stating plainly rather than implying the pattern is universally
supported, it is a composition every team building it in Camel or a similar
framework has to assemble by hand.

## 9. Known production uses

**RabbitMQ**, one of the most widely deployed open-source message brokers,
ships Direct Reply-To as a first-class broker feature specifically for the
Request-Reply case this pattern addresses, avoiding a persisted correlation
table by tying the substitute address to the requester's live connection
(rabbitmq.com/docs/direct-reply-to, verified 2026-08-13).

**AWS API Gateway**, part of Amazon Web Services and used across a very large
share of production serverless HTTP and WebSocket backends, implements the
gateway-managed connection-identity variant for its WebSocket API product, a
backend never replies to a connected client directly, it always posts through
the gateway's Management API using the connection identifier the gateway
itself issued and owns (docs.aws.amazon.com, API Gateway WebSocket connections
guide, verified 2026-08-13).

**Apache CXF**, an Apache Software Foundation project and one of the most
widely used open-source JAX-WS stacks for SOAP web services, implements the
WS-Addressing decoupled-endpoint variant directly, exposing a setReplyTo call
on its AddressingProperties API so a caller or an intermediary can direct a
SOAP reply to an address other than the original sender's own endpoint
(cxf.apache.org/docs/ws-addressing.html, verified 2026-08-13), on top of the
ReplyTo mechanism the W3C standardised for exactly this purpose
(w3.org/TR/ws-addr-core, verified 2026-08-13).

**Jakarta Messaging (JMS)**, the Java platform's standard messaging API and the
foundation nearly every JMS-based Smart Proxy implementation is built on
whether via ActiveMQ, IBM MQ, or a Java EE application server's own broker,
defines the JMSReplyTo header field that the catalog form of this pattern
reads and rewrites. the specification states plainly that "the JMSReplyTo
header field contains the destination where a reply to the current message
should be sent" (jakarta.ee, Jakarta Messaging 3.1 API specification,
`jakarta.jms.Message`, verified 2026-08-13). The specification itself describes
only the sender setting this field, not an intermediary rewriting it, which is
consistent with this pattern being something a team builds on top of the JMS
contract rather than something the contract mandates or names on its own.

The two most widely used open-source enterprise integration frameworks,
Apache Camel and, by extension, Spring Integration's equivalent System
Management surface, do not ship this as a named, first-class EIP the way they
do for Wire Tap and Message History, confirmed directly against Camel's own
published catalog of the EIPs it implements
(camel.apache.org/components/latest/eips/enterprise-integration-patterns.html,
verified 2026-08-13). Where this pattern is needed on either framework, it is
assembled from a Content Enricher, an Aggregator keyed on Correlation
Identifier, and a Recipient List, rather than invoked as a single DSL keyword.

## 10. Consequences

Positive.

- Gives an operator full visibility into a Request-Reply exchange, both the
  request and the eventual reply, without a single line of change to either
  the requesting client or the service being observed, which is precisely the
  case a Wire Tap on a fixed channel cannot cover.
- Centralises timing, error, and delivery-confirmation data for a service at
  exactly one hop, which makes it possible to compute a genuine end-to-end
  reply latency figure per exchange, request received to reply forwarded,
  something neither endpoint alone can compute on its own without the other
  endpoint's clock and cooperation.
- Provides a single point to add resilience behaviour later, a timeout on
  waiting for a reply, a retry, a circuit breaker, without renegotiating a
  contract change with the service team, because the substitution point is
  already where all of the traffic for that service already flows.
- Works on services the observing team does not own and cannot modify, a
  vendor product, a legacy application, or a third-party integration, which is
  the single most common reason teams reach for this pattern in the first
  place rather than direct instrumentation.
- Composes cheaply with Wire Tap for durable capture. once the proxy already
  sees both legs of the exchange, tapping that traffic to a monitoring or
  storage channel is a small addition rather than a new integration point.

Negative.

- Introduces a genuinely stateful component into an architecture that was, up
  to that point, built around stateless, fire-and-forward messaging hops, and
  that state, the correlation table, has its own sizing, persistence, and
  eviction concerns that did not exist before the proxy was added.
- Adds a real hop and real latency on both legs of every tracked exchange, not
  one, and makes the proxy's own availability a hard dependency of the
  service it is meant to be observing, even when that service is perfectly
  healthy on its own.
- Requires perfectly faithful substitution and restoration logic, because a
  bug in either direction corrupts delivery for every client of the tracked
  service at once, not merely the proxy's own diagnostic goal, which is a
  much larger blast radius than most monitoring code carries.
- Duplicates effort with, and can quietly drift out of agreement with, a full
  distributed tracing deployment if one already covers the same service, since
  the two mechanisms are answering an overlapping question through two
  independent code paths that nobody has committed to keeping synchronised.
- Concentrates a genuinely larger data-exposure surface in one component than
  either endpoint had on its own, both the request and the reply for every
  client of the service, discussed further in dimension 17.

## 11. Failure modes and misuse

**Symptom.** The correlation table grows steadily over hours or days with no
corresponding decrease, eventually exhausting memory on the proxy host.
**Cause.** A subset of requests never receive a reply, because the service
crashed mid-processing, dropped the message, or the reply itself was lost
downstream, and the table entry recorded for that Correlation Identifier has
no eviction policy attached to it. **Fix.** Attach a time-to-live to every
table entry, sized to a small multiple of the service's own expected reply
latency, and evict on expiry regardless of whether a reply ever arrives, with
the eviction itself logged so an operator can see how often the tracked
service simply fails to reply at all, a fact the original Requestor's own
timeout logic would otherwise hide from anyone but that one Requestor.

**Symptom.** A reply is delivered to the wrong Requestor, a serious
misdelivery discovered only when the wrong client acts on data meant for
someone else. **Cause.** Two concurrent requests, from different Requestors,
were assigned the same Correlation Identifier, either because one Requestor's
identifier generation is not sufficiently unique or because a Requestor itself
reused an identifier from an earlier, already-completed exchange before that
exchange's table entry had been evicted. **Fix.** Never trust Correlation
Identifier uniqueness across Requestors without verifying the generation
scheme, prefer a scheme with enough entropy that collision within any
plausible in-flight window is effectively impossible, and, where the proxy
controls channel assignment, consider scoping the correlation key to
requestor-plus-identifier rather than identifier alone as a second line of
defence.

**Symptom.** A reply arrives at the proxy's own reply channel with a
Correlation Identifier the table has no entry for, and the proxy either drops
it silently or, worse, forwards it to whatever default address happens to be
configured. **Cause.** The entry was already evicted, either by the time-to-live
policy above or because a duplicate reply arrived after the first reply for
the same Correlation Identifier had already been forwarded and the entry
removed, which happens on any transport that offers at-least-once rather than
exactly-once delivery. **Fix.** Route an unmatched reply to a Dead Letter
Channel or Invalid Message Channel explicitly, never to a default or fallback
address, and log the Correlation Identifier so a duplicate-delivery pattern is
visible rather than silently discarded, since a silently discarded reply looks
identical, from the outside, to a reply that was correctly delivered.

**Symptom.** The proxy crashes and restarts, and every request that was
in-flight at the moment of the crash never receives its reply, even though the
underlying service processed it correctly and sent a reply that arrived at the
proxy's old reply channel after the restart. **Cause.** The correlation table
was held only in the proxy process's own memory, with no durability, so a
restart discards every mapping the table held, and a reply that then arrives
addressed to the proxy has nowhere to go. **Fix.** For any deployment where the
underlying transport already offers Guaranteed Delivery, persist the
correlation table with matching durability guarantees, not merely the messages
it correlates, or accept explicitly, and document, that a proxy restart is a
data-loss event for in-flight exchanges and size the acceptable blast radius
of that event before choosing an in-memory-only implementation.

**Symptom.** Latency figures the proxy reports for the tracked service are
consistently higher than the service's own internal timing shows, and nobody
can explain the gap during an incident review. **Cause.** The proxy's own
processing, the table write on the request leg and the table lookup and
forward on the reply leg, is included in the measured interval without being
separated out from the service's own processing time, so a slow proxy under
load inflates every latency figure it reports for a service that may be
perfectly healthy. **Fix.** Record and expose the proxy's own per-hop
processing time as a distinct metric from the end-to-end figure it computes,
so a reader of the dashboard can tell, at a glance, whether a latency spike
originates in the tracked service or in the tracking mechanism itself.

## 12. Trade-off matrix

| Dimension | Smart Proxy | Distributed Tracing (correlation token, out-of-band) | Direct Service Instrumentation | Message History (in-band, cooperating hops) |
|---|---|---|---|---|
| Requires changing the tracked service's code | No | Usually yes, an instrumentation library must be added | Yes, by definition | Yes, every recording hop must participate |
| Works on a vendor or unmodifiable service | Yes | Only if the vendor already instruments it | No | No |
| Adds a network hop on both request and reply | Yes, on both legs | No, propagates a small token in-band | No | No, rides the existing message |
| Requires a new persisted, keyed state store | Yes, the correlation table, unless the broker-native variant is used | No, correlation lives in the collector, not on the message path | No | No, the history rides inside the message itself |
| Answers "where did this reply actually go" | Yes, directly, that is the pattern's purpose | Indirectly, via a query against the collector | Only if the service logs it itself | Not directly, it answers path, not reply destination |
| Query and search across many exchanges at once | Poor, one exchange at a time unless paired with a Wire Tap into a store | Excellent, purpose-built for this | Depends entirely on the service's own logging quality | Poor, requires reading each message's history individually |
| Risk introduced by the mechanism itself | A new single point of failure and misdelivery risk on both legs | Low, failure of the tracing backend does not block the exchange itself | None beyond the service's own existing risk | Low, a non-recording hop simply leaves a gap, it does not block delivery |

## 13. Related and incompatible patterns

**Return Address.** Smart Proxy has nothing to operate on without Return
Address as the underlying mechanism the tracked exchange already uses, it
reads the Return Address field the Requestor set, and its entire job is to
substitute that field's value temporarily and restore the original routing
intent once the reply is in hand. A service that hardcodes its reply
destination rather than reading it from the request has no Return Address for
this pattern to intercept.

**Correlation Identifier.** A hard dependency, not an optional companion. The
proxy cannot know which stored original address a given reply belongs to
without one, and any deployment handling more than one in-flight request at a
time needs it to avoid the misdelivery failure mode described in dimension 11.
Correlation Identifier answers a narrower question than this pattern does,
which reply belongs to which request, while Smart Proxy uses that answer to
solve a broader operational problem, where should this reply actually go now
that its address has been substituted.

**Message Router.** The forwarding step on the reply leg, once the original
Return Address has been recovered from the correlation table, is explicitly a
Message Router in the catalog's own description, deliberately the simplest
possible instance of one, a single lookup and a single forward with no
content-based branching on the payload itself.

**Wire Tap.** The pattern this entry exists specifically to generalise for the
reply-side, data-driven-destination case a plain Wire Tap cannot cover. The two
compose naturally rather than compete, a Smart Proxy is frequently built with
an internal Wire Tap attached to the request and reply pair it already sees,
so the observed traffic can be durably persisted to a monitoring channel or a
Message Store without adding that persistence step to the critical delivery
path itself. Where Wire Tap alone can observe a fixed channel with zero added
latency and zero state, Smart Proxy trades both of those away specifically to
cover the case Wire Tap cannot.

**Message History.** A different resolution of a related visibility problem.
Message History answers which components a message passed through, in what
order, by having every cooperating hop append to the message itself, in-band,
requiring cooperation from every recording component along a potentially long
path. Smart Proxy answers a narrower question, where did the reply for this
one exchange actually go, at exactly one hop, with zero cooperation required
from the service being observed. A team that already has a Message History
deployment covering the same service is very likely duplicating effort by
adding a Smart Proxy in front of it too, which is exactly the non-applicability
case named in dimension 4.

**Request-Reply.** The message-exchange pattern this entry is scoped to
entirely. Smart Proxy is meaningless outside a genuine Request-Reply exchange,
because there is no reply leg to intercept in an exchange that never expects
one back.

**Content Enricher.** The request-leg mutation, overwriting the Return Address
field before forwarding, is structurally a narrow instance of enriching, or
here more precisely replacing, one piece of message metadata. It is a
deliberately narrower operation than a general Content Enricher, which
typically adds data the message was missing by calling out to an external
resource. Smart Proxy replaces a field the message already had with a value
the proxy already knows, its own address, and makes no external call to do so.

**Detour.** Camel's own catalog describes Detour as routing a message through
one or more intermediate steps, for validation, testing, or debugging, before
it continues on its original path (camel.apache.org, verified 2026-08-13).
Smart Proxy can be read as a specialised Detour applied specifically to the
reply leg of a Request-Reply exchange, where the intermediate step is the
correlation lookup and restoration rather than a generic validation or
debugging step.

**Event Message, incompatible.** A one-way, fire-and-forget message has no
Return Address and expects no reply, so there is nothing for a Smart Proxy to
capture or restore. Attempting to apply this pattern to a pure Event Message
exchange is a category error, not merely an unnecessary one, and the
incompatibility is recorded in frontmatter for exactly that reason.

## 14. Refactoring path in and out

Introducing the pattern into an existing, working Request-Reply integration
should never require a coordinated change with the Requestor or the Service,
because losing that property defeats the entire reason to reach for this
pattern in the first place.

1. Confirm the exchange genuinely carries a data-driven Return Address today,
   not a fixed reply channel, by reading a sample of real request messages
   rather than assuming the wiring documentation is current.
2. Stand up the new proxy component with an empty correlation table and its
   own dedicated reply channel, deployed but not yet in the traffic path, and
   verify its substitution and restoration logic in isolation first, ideally
   with the in-memory test technique described in dimension 15.
3. Change only the routing configuration in front of the service, never the
   Requestor's own code, so that requests destined for the service's request
   channel pass through the new proxy first. On a broker that supports it
   natively, this can be as small as pointing consumers at the broker's own
   address-rewriting feature rather than deploying a separate component at
   all, as RabbitMQ's Direct Reply-To demonstrates.
4. Point the proxy's own forwarding logic at the service's real request
   channel, and confirm with a synthetic Test Message, injected through the
   full path end to end, that a round trip through the proxy produces an
   identical reply to the direct path it is about to replace, before any real
   traffic depends on it.
5. Cut real traffic over by routing configuration alone, watch the correlation
   table size and the eviction counter from dimension 16 for the first live
   traffic window, and keep the direct, un-proxied path available to roll back
   to until that window has passed without a surprise.

Removing the pattern once it has stopped earning its place, most often because
a full distributed tracing deployment now covers the same service and the two
mechanisms have started to duplicate effort, follows the reverse order and one
extra caution the introduction did not need.

1. Confirm no other component now depends on data the proxy produces as a
   byproduct, most commonly a Wire Tap feeding a Message Store or a dashboard
   built against the proxy's own latency metric, and migrate or retire those
   dependents first.
2. Point the routing configuration back at the service's real reply mechanism
   directly, restoring requestors to talking to the service without an
   intermediary, again without any change to the Requestor's own code.
3. Do not decommission the proxy process itself the moment traffic is
   redirected. Let the correlation table drain naturally, replies for requests
   that were already in flight at the moment of the cutover still need to be
   forwarded, and only remove the component once that table has emptied or the
   maximum time-to-live window from dimension 11 has elapsed, whichever comes
   first, so no in-flight exchange is orphaned by the removal itself.

## 15. Testing and verification

The substitution and restoration logic is straightforward to test in complete
isolation from any real broker, and doing so should be the first test written,
before any integration test that requires a live messaging fabric at all. A
fake, in-memory channel implementation, exactly the shape used in the code
examples for this entry, a map of channel name to an ordered list of messages,
is sufficient to exercise every behaviour that matters, published and consumed
in the right order, the request leg records the correct table entry and
rewrites the Return Address field to the proxy's own channel, and the reply
leg looks up, forwards, and evicts correctly.

Three specific scenarios deserve dedicated tests beyond the straightforward
happy path, because each corresponds directly to a failure mode named in
dimension 11 and each is easy to miss with only a single-request test.

- **Concurrency correctness.** Send two or more requests with distinct
  Correlation Identifiers and distinct original Return Addresses before either
  reply arrives, then deliver the replies out of order, and assert that each
  reply reaches its own original Requestor rather than being swapped. This is
  the single most important test for this pattern, because a swapped reply is
  a silent misdelivery, not a visible crash, and will not surface on its own
  in a naive single-request test suite.
- **Unmatched reply handling.** Deliver a reply whose Correlation Identifier
  the table has no entry for, either because it was never issued or because it
  was already evicted, and assert it is routed to a dead-letter or invalid
  message path rather than silently dropped or forwarded to a stale address.
- **Eviction under a bounded time-to-live.** Advance a controllable clock past
  the configured time-to-live for a request with no reply, and assert the
  table entry is removed and an eviction event is recorded, so this behaviour
  is proven deterministically rather than relying on an integration test that
  waits in real time for the window to pass.

Once the proxy's own logic is proven this way, the Test Message pattern is the
right tool for verifying a live deployment end to end without depending on
real client traffic. Hohpe and Woolf describe Test Message as existing
specifically to catch "a component actively processing messages, but garbling
outgoing messages due to an internal fault," verified by injecting synthetic
test data into the live stream rather than relying on a heartbeat alone
(enterpriseintegrationpatterns.com/patterns/messaging/TestMessage.html,
verified 2026-08-13). A synthetic request, carrying a Correlation Identifier
and Return Address the test itself controls, run through the deployed proxy on
a schedule, is exactly the same mechanism applied to this pattern specifically,
and it is the only reliable way to prove the substitution and restoration are
still correct on the real broker, not only in the isolated unit test.

## 16. Observability signals

The proxy sits on both legs of every tracked exchange, which makes it a
genuinely good source of metrics the two endpoints cannot compute on their
own, provided the metrics are designed to separate the proxy's own overhead
from the service's own processing time, per the last failure mode in
dimension 11.

- **Correlation table depth, as a live gauge.** The number of currently
  outstanding entries. A gauge that climbs steadily with no corresponding
  decrease over a normal traffic window is the earliest warning sign of the
  memory-growth failure mode in dimension 11, well before it becomes an actual
  memory exhaustion incident.
- **Eviction counter, split by cause.** A count of entries removed by
  time-to-live expiry, separate from a count of entries removed by a genuine
  matched reply. A rising time-to-live eviction rate is a direct, quantified
  signal of how often the tracked service simply fails to reply at all, a fact
  each individual Requestor's own client-side timeout would otherwise hide
  from anyone but that one Requestor.
- **Unmatched reply counter.** A count of replies that arrived with a
  Correlation Identifier the table had no entry for. A nonzero, sustained rate
  here points either at duplicate delivery from the underlying transport or at
  a bug in the eviction window being too aggressive relative to real service
  latency.
- **Round-trip latency, separated from proxy overhead.** The full interval
  from request received to reply forwarded, reported alongside the proxy's own
  processing time on each leg as a distinct figure, so a dashboard reader can
  tell whether a spike originates in the service or in the tracking mechanism
  itself.
- **Synthetic Test Message success rate.** The pass or fail result of the
  scheduled synthetic round trip described in dimension 15, which is the one
  signal that directly answers whether the substitution and restoration logic
  is still correct right now, independent of whatever real traffic happens to
  be flowing at the moment.

A healthy proxy, read from these signals together, shows a correlation table
depth that oscillates around a steady baseline proportional to real in-flight
concurrency rather than trending upward, an eviction rate made up mostly of genuine
matched replies rather than time-to-live expiry, a near-zero unmatched reply
rate, and a passing synthetic Test Message on every scheduled run. A failing
one typically shows exactly one of these breaking loose first, well before any
Requestor notices anything is wrong.

## 17. Security and privacy implications

The proxy sees both the request and the reply for every client of the tracked
service, which is a strictly larger visibility surface than either the
Requestor or the Service has on its own, the Requestor sees only its own
traffic, the Service sees each exchange in isolation without a cross-client
view, and the proxy alone sees every exchange for the service it fronts, in
one place. That concentration is precisely why the proxy has to become a
deliberately hardened point of the architecture rather than an incidental one,
access-controlled, encrypted at rest for anything it persists, and covered by
whatever data retention policy governs the most sensitive field that passes
through it.

The substitution mechanism itself is a genuine interception primitive, not
merely an observability convenience, and the W3C's own WS-Addressing
specification says so directly in its security considerations, placing the
burden of validation and authentication on the intermediary before it acts on
a WS-Addressing construct, specifically to keep an unauthenticated party from
redirecting a message (w3.org/TR/ws-addr-core, verified 2026-08-13). A compromised or
misconfigured proxy is not merely a source of stale metrics, it is a component
that can silently redirect a reply meant for one party to an address of its
choosing, which is exactly the capability a well-behaved proxy uses for
legitimate tracking and exactly the capability an attacker who gained control
of it would use for interception. Authentication of who is permitted to
publish onto the proxy's own reply channel, and validation that a forwarded
reply's destination genuinely matches a recovered, trusted table entry rather
than an attacker-supplied value, are not optional hardening steps, they are
the same mechanism the pattern's own correctness already depends on.

If the Requestor's Return Address itself carries information beyond a bare
routing token, an internal hostname, a tenant-specific queue name that reveals
account structure, or anything that would count as sensitive if it appeared in
a log line, storing it in the correlation table extends that information's
retention footprint to a new component with its own retention policy, which
must independently satisfy whatever compliance regime already governs the
original data. A team building this pattern should treat the correlation table
as a place holding exactly that kind of routing metadata, minimise what it
retains beyond the bare address and identifier needed for correctness, and
apply the same time-to-live discipline used for correctness in dimension 11 as
a privacy control too, since a shorter-lived table is also a smaller exposure
window if the proxy itself is ever compromised.

## 18. References

1. Gregor Hohpe, Bobby Woolf. *Enterprise Integration Patterns. Designing,
   Building, and Deploying Messaging Solutions.* Addison-Wesley, 2003. System
   Management chapter, the Smart Proxy pattern description.
2. Enterprise Integration Patterns, Smart Proxy pattern page.
   https://www.enterpriseintegrationpatterns.com/patterns/messaging/SmartProxy.html,
   verified 2026-08-13.
3. Enterprise Integration Patterns, Return Address pattern page.
   https://www.enterpriseintegrationpatterns.com/patterns/messaging/ReturnAddress.html,
   verified 2026-08-13.
4. Enterprise Integration Patterns, Correlation Identifier pattern page.
   https://www.enterpriseintegrationpatterns.com/patterns/messaging/CorrelationIdentifier.html,
   verified 2026-08-13.
5. Enterprise Integration Patterns, Test Message pattern page.
   https://www.enterpriseintegrationpatterns.com/patterns/messaging/TestMessage.html,
   verified 2026-08-13.
6. RabbitMQ documentation. Direct reply-to.
   https://www.rabbitmq.com/docs/direct-reply-to, verified 2026-08-13. Source
   for the broker-native address rewriting variant in dimension 8 and the
   named production use in dimension 9.
7. Amazon Web Services. API Gateway developer guide, "Use @connections
   commands in your backend service."
   https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-how-to-call-websocket-api-connections.html,
   verified 2026-08-13. Source for the gateway-managed connection-identity
   variant in dimension 8.
8. World Wide Web Consortium. *Web Services Addressing 1.0, Core.* W3C
   Recommendation.
   https://www.w3.org/TR/ws-addr-core/, verified 2026-08-13. Source for the
   ReplyTo definition in dimension 8 and the security considerations quoted in
   dimension 17.
9. Apache Software Foundation. Apache CXF documentation, "WS-Addressing."
   https://cxf.apache.org/docs/ws-addressing.html, verified 2026-08-13. Source
   for the named production use in dimension 9.
10. Apache Software Foundation. Apache Camel documentation, "Enterprise
    Integration Patterns" catalog.
    https://camel.apache.org/components/latest/eips/enterprise-integration-patterns.html,
    verified 2026-08-13. Source for the notably absent finding in dimensions 8
    and 9, and for the Detour pattern description cited in dimension 13.
11. Eclipse Foundation. Jakarta Messaging 3.1 API specification,
    `jakarta.jms.Message`, the `JMSReplyTo` field.
    https://jakarta.ee/specifications/messaging/3.1/apidocs/jakarta.messaging/jakarta/jms/message,
    verified 2026-08-13. Source for the JMS-based production use in dimension
    9.
12. SourceMaking. "Proxy design pattern."
    https://sourcemaking.com/design_patterns/proxy, verified 2026-08-13.
    Source for the GoF "smart proxy" applicability case disambiguated from
    this pattern in dimension 1.
13. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides. *Design
    Patterns. Elements of Reusable Object-Oriented Software.* Addison-Wesley,
    1994. Structural Patterns chapter, Proxy. Source for the underlying GoF
    Proxy pattern referenced in dimension 1.

## Code examples

Four languages, all implementing the same shape, a broker abstracted behind a
minimal in-memory channel so each example is runnable on its own with no
external dependency, which keeps the example focused on the substitution and
correlation logic rather than on any one vendor's client library. Every sample
below was compiled or run against the toolchain present on the machine this
entry was written on, and every sample demonstrates the concurrency-safety
property from dimension 15 directly, two concurrent requestors, two distinct
correlation identifiers, and an assertion that each one receives its own
reply rather than the other's.

### TypeScript

Compiled with `tsc --noEmit --strict`, and separately compiled and run under
Node to confirm the runtime output.

```typescript
interface Message {
  payload: string;
  replyTo: string;
  correlationId: string;
}

class Broker {
  private channels = new Map<string, Message[]>();

  publish(channel: string, msg: Message): void {
    const queue = this.channels.get(channel) ?? [];
    queue.push(msg);
    this.channels.set(channel, queue);
  }

  consume(channel: string): Message | undefined {
    const queue = this.channels.get(channel);
    return queue?.shift();
  }
}

class SmartProxy {
  private correlationTable = new Map<string, string>();

  constructor(
    private readonly broker: Broker,
    private readonly ownReplyChannel: string,
    private readonly serviceChannel: string
  ) {}

  handleRequest(msg: Message): void {
    this.correlationTable.set(msg.correlationId, msg.replyTo);
    const forwarded: Message = { ...msg, replyTo: this.ownReplyChannel };
    this.broker.publish(this.serviceChannel, forwarded);
  }

  handleReply(msg: Message): boolean {
    const originalReplyTo = this.correlationTable.get(msg.correlationId);
    this.correlationTable.delete(msg.correlationId);
    if (originalReplyTo === undefined) {
      this.broker.publish("dead-letter", msg);
      return false;
    }
    this.broker.publish(originalReplyTo, msg);
    return true;
  }
}

function runServiceOnce(broker: Broker, serviceChannel: string): void {
  const req = broker.consume(serviceChannel);
  if (req === undefined) return;
  const reply: Message = {
    payload: `processed ${req.payload}`,
    replyTo: "",
    correlationId: req.correlationId,
  };
  broker.publish(req.replyTo, reply);
}

function main(): void {
  const broker = new Broker();
  const proxy = new SmartProxy(broker, "proxy-reply", "service-request");

  const requestA: Message = { payload: "order-1", replyTo: "client-a-inbox", correlationId: "corr-a" };
  const requestB: Message = { payload: "order-2", replyTo: "client-b-inbox", correlationId: "corr-b" };

  proxy.handleRequest(requestA);
  proxy.handleRequest(requestB);

  runServiceOnce(broker, "service-request");
  runServiceOnce(broker, "service-request");

  const reply1 = broker.consume("proxy-reply")!;
  const reply2 = broker.consume("proxy-reply")!;

  proxy.handleReply(reply1);
  proxy.handleReply(reply2);

  const aInbox = broker.consume("client-a-inbox")!;
  const bInbox = broker.consume("client-b-inbox")!;
  console.log(aInbox.payload, aInbox.correlationId);
  console.log(bInbox.payload, bInbox.correlationId);
}

main();
```

### Python

Compiled with `python3 -m py_compile` and run directly.

```python
from dataclasses import dataclass


@dataclass
class Message:
    payload: str
    reply_to: str
    correlation_id: str


class Broker:
    def __init__(self) -> None:
        self.channels: dict[str, list[Message]] = {}

    def publish(self, channel: str, msg: Message) -> None:
        self.channels.setdefault(channel, []).append(msg)

    def consume(self, channel: str) -> Message | None:
        queue = self.channels.get(channel, [])
        if not queue:
            return None
        return queue.pop(0)


class SmartProxy:
    def __init__(self, broker: Broker, own_reply_channel: str, service_channel: str) -> None:
        self.broker = broker
        self.own_reply_channel = own_reply_channel
        self.service_channel = service_channel
        self.correlation_table: dict[str, str] = {}

    def handle_request(self, msg: Message) -> None:
        self.correlation_table[msg.correlation_id] = msg.reply_to
        forwarded = Message(msg.payload, self.own_reply_channel, msg.correlation_id)
        self.broker.publish(self.service_channel, forwarded)

    def handle_reply(self, msg: Message) -> bool:
        original_reply_to = self.correlation_table.pop(msg.correlation_id, None)
        if original_reply_to is None:
            self.broker.publish("dead-letter", msg)
            return False
        self.broker.publish(original_reply_to, msg)
        return True


def run_service_once(broker: Broker, service_channel: str) -> None:
    req = broker.consume(service_channel)
    if req is None:
        return
    reply = Message(f"processed {req.payload}", "", req.correlation_id)
    broker.publish(req.reply_to, reply)


def main() -> None:
    broker = Broker()
    proxy = SmartProxy(broker, own_reply_channel="proxy-reply", service_channel="service-request")

    request_a = Message("order-1", reply_to="client-a-inbox", correlation_id="corr-a")
    request_b = Message("order-2", reply_to="client-b-inbox", correlation_id="corr-b")

    proxy.handle_request(request_a)
    proxy.handle_request(request_b)

    run_service_once(broker, "service-request")
    run_service_once(broker, "service-request")

    reply_1 = broker.consume("proxy-reply")
    reply_2 = broker.consume("proxy-reply")
    assert reply_1 is not None and reply_2 is not None

    proxy.handle_reply(reply_1)
    proxy.handle_reply(reply_2)

    a_inbox = broker.consume("client-a-inbox")
    b_inbox = broker.consume("client-b-inbox")
    assert a_inbox is not None and a_inbox.correlation_id == "corr-a"
    assert b_inbox is not None and b_inbox.correlation_id == "corr-b"
    print(a_inbox.payload, a_inbox.correlation_id)
    print(b_inbox.payload, b_inbox.correlation_id)


if __name__ == "__main__":
    main()
```

### Java

Compiled with `javac -nowarn` and run directly.

```java
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.HashMap;
import java.util.Map;

final class Message {
    final String payload;
    final String replyTo;
    final String correlationId;

    Message(String payload, String replyTo, String correlationId) {
        this.payload = payload;
        this.replyTo = replyTo;
        this.correlationId = correlationId;
    }
}

final class Broker {
    private final Map<String, Deque<Message>> channels = new HashMap<>();

    void publish(String channel, Message msg) {
        channels.computeIfAbsent(channel, k -> new ArrayDeque<>()).addLast(msg);
    }

    Message consume(String channel) {
        Deque<Message> queue = channels.get(channel);
        if (queue == null || queue.isEmpty()) {
            return null;
        }
        return queue.removeFirst();
    }
}

final class SmartProxy {
    private final Broker broker;
    private final String ownReplyChannel;
    private final String serviceChannel;
    private final Map<String, String> correlationTable = new HashMap<>();

    SmartProxy(Broker broker, String ownReplyChannel, String serviceChannel) {
        this.broker = broker;
        this.ownReplyChannel = ownReplyChannel;
        this.serviceChannel = serviceChannel;
    }

    void handleRequest(Message msg) {
        correlationTable.put(msg.correlationId, msg.replyTo);
        Message forwarded = new Message(msg.payload, ownReplyChannel, msg.correlationId);
        broker.publish(serviceChannel, forwarded);
    }

    boolean handleReply(Message msg) {
        String originalReplyTo = correlationTable.remove(msg.correlationId);
        if (originalReplyTo == null) {
            broker.publish("dead-letter", msg);
            return false;
        }
        broker.publish(originalReplyTo, msg);
        return true;
    }
}

public final class Demo {
    static void runServiceOnce(Broker broker, String serviceChannel) {
        Message req = broker.consume(serviceChannel);
        if (req == null) {
            return;
        }
        Message reply = new Message("processed " + req.payload, "", req.correlationId);
        broker.publish(req.replyTo, reply);
    }

    public static void main(String[] args) {
        Broker broker = new Broker();
        SmartProxy proxy = new SmartProxy(broker, "proxy-reply", "service-request");

        Message requestA = new Message("order-1", "client-a-inbox", "corr-a");
        Message requestB = new Message("order-2", "client-b-inbox", "corr-b");

        proxy.handleRequest(requestA);
        proxy.handleRequest(requestB);

        runServiceOnce(broker, "service-request");
        runServiceOnce(broker, "service-request");

        Message reply1 = broker.consume("proxy-reply");
        Message reply2 = broker.consume("proxy-reply");

        proxy.handleReply(reply1);
        proxy.handleReply(reply2);

        Message aInbox = broker.consume("client-a-inbox");
        Message bInbox = broker.consume("client-b-inbox");
        System.out.println(aInbox.payload + " " + aInbox.correlationId);
        System.out.println(bInbox.payload + " " + bInbox.correlationId);
    }
}
```

### Go

Compiled with `go vet` and run directly.

```go
package main

import "fmt"

type Message struct {
	Payload       string
	ReplyTo       string
	CorrelationID string
}

type Broker struct {
	channels map[string][]Message
}

func NewBroker() *Broker {
	return &Broker{channels: map[string][]Message{}}
}

func (b *Broker) publish(channel string, msg Message) {
	b.channels[channel] = append(b.channels[channel], msg)
}

func (b *Broker) consume(channel string) (Message, bool) {
	q := b.channels[channel]
	if len(q) == 0 {
		return Message{}, false
	}
	msg := q[0]
	b.channels[channel] = q[1:]
	return msg, true
}

type SmartProxy struct {
	broker           *Broker
	ownReplyChannel  string
	serviceChannel   string
	correlationTable map[string]string
}

func NewSmartProxy(broker *Broker, ownReplyChannel, serviceChannel string) *SmartProxy {
	return &SmartProxy{
		broker:           broker,
		ownReplyChannel:  ownReplyChannel,
		serviceChannel:   serviceChannel,
		correlationTable: map[string]string{},
	}
}

func (p *SmartProxy) handleRequest(msg Message) {
	p.correlationTable[msg.CorrelationID] = msg.ReplyTo
	forwarded := Message{Payload: msg.Payload, ReplyTo: p.ownReplyChannel, CorrelationID: msg.CorrelationID}
	p.broker.publish(p.serviceChannel, forwarded)
}

func (p *SmartProxy) handleReply(msg Message) bool {
	originalReplyTo, ok := p.correlationTable[msg.CorrelationID]
	if !ok {
		p.broker.publish("dead-letter", msg)
		return false
	}
	delete(p.correlationTable, msg.CorrelationID)
	p.broker.publish(originalReplyTo, msg)
	return true
}

func runServiceOnce(broker *Broker, serviceChannel string) {
	req, ok := broker.consume(serviceChannel)
	if !ok {
		return
	}
	reply := Message{Payload: "processed " + req.Payload, CorrelationID: req.CorrelationID}
	broker.publish(req.ReplyTo, reply)
}

func main() {
	broker := NewBroker()
	proxy := NewSmartProxy(broker, "proxy-reply", "service-request")

	requestA := Message{Payload: "order-1", ReplyTo: "client-a-inbox", CorrelationID: "corr-a"}
	requestB := Message{Payload: "order-2", ReplyTo: "client-b-inbox", CorrelationID: "corr-b"}

	proxy.handleRequest(requestA)
	proxy.handleRequest(requestB)

	runServiceOnce(broker, "service-request")
	runServiceOnce(broker, "service-request")

	reply1, _ := broker.consume("proxy-reply")
	reply2, _ := broker.consume("proxy-reply")

	proxy.handleReply(reply1)
	proxy.handleReply(reply2)

	aInbox, _ := broker.consume("client-a-inbox")
	bInbox, _ := broker.consume("client-b-inbox")
	fmt.Println(aInbox.Payload, aInbox.CorrelationID)
	fmt.Println(bInbox.Payload, bInbox.CorrelationID)
}
```

All four samples print the same two lines, the processed order-1 payload with
correlation id corr-a followed by the processed order-2 payload with
correlation id corr-b, confirming neither reply crossed over to the other
requestor's inbox.
