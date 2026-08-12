---
name: Return Address
slug: return-address
family: 07-integration
category: Messaging
aliases: [ReplyTo, Reply Channel, Callback Address]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [request-reply, correlation-identifier, message-endpoint, point-to-point-channel, command-message]
incompatible_with: [fire-and-forget-event-message]
verified: 2026-08-02
---

# Return Address

## 1. Name, aliases, and lineage

The canonical name is Return Address. It is catalogued by Gregor Hohpe and
Bobby Woolf in *Enterprise Integration Patterns. Designing, Building, and
Deploying Messaging Solutions*, Addison-Wesley, 2003, in the Messaging Systems
chapter, as one of the two sub-patterns that together make Request-Reply work
on an asynchronous channel. The pattern's own reference page states the
intent directly. "The request message should contain a Return Address that
indicates where to send the reply message"
(https://www.enterpriseintegrationpatterns.com/patterns/messaging/ReturnAddress.html,
verified 2026-08-02). The same page describes the header as metadata rather
than payload, a channel or destination reference the requestor supplies so
the replier can route the answer without knowing the requestor's identity in
advance, and it frames the pattern as requestor-controlled configuration.
That is, the requestor decides where its own reply goes, and the replier is
never hard coded to a single destination.

The most common alias in actual code is ReplyTo, because every mainstream
messaging API that implements the pattern names the field literally that.
Jakarta Messaging (the specification formerly named JMS) defines a
`JMSReplyTo` header on every message, described in its own javadoc as
containing "the destination where a reply to the current message should be
sent" (Jakarta Messaging 3.1 API specification,
`jakarta.jms.Message`, https://jakarta.ee/specifications/messaging/3.1/apidocs/jakarta.messaging/jakarta/jms/message,
verified 2026-08-02). AMQP 0-9-1, the protocol RabbitMQ implements, carries a
`reply-to` basic property with the same purpose, and Azure Service Bus names
its equivalent field `ReplyTo` on `ServiceBusMessage`, documented as "the
address of an entity to send replies to", used when "a sender expects a
reply" and sets the field "to the absolute or relative path of the queue or
topic it expects the reply to be sent to"
(Microsoft Learn, `Azure.Messaging.ServiceBus.ServiceBusMessage.ReplyTo`,
https://learn.microsoft.com/en-us/dotnet/api/azure.messaging.servicebus.servicebusmessage.replyto,
verified 2026-08-02). Reply Channel is the name Hohpe and Woolf use in prose
when they discuss the destination itself rather than the header that carries
its address, and Callback Address is a looser, informal alias used outside
the messaging-pattern literature for the same idea applied to any
asynchronous protocol, including webhooks and OAuth redirect URIs, though
those uses sit closer to the pattern's boundary than its center, discussed
under dimension 4 below.

The idea predates the 2003 name by a wide margin. Any protocol that lets a
sender specify where to receive an answer implements the same shape, and the
UDP source port a client binds before sending a DNS query, so the resolver can
send its answer back to the exact socket that asked, is a return address at
the transport layer, decades before Hohpe and Woolf wrote it down as an
integration pattern. Their contribution was not the mechanism, it was
isolating it as a named, reusable header convention independent of any
specific protocol, and pairing it with Correlation Identifier, the sibling
pattern that lets a requestor match an incoming reply to the specific
request it answers, since a shared reply channel commonly serves many
concurrent requestors at once. This entry treats Return Address as the
narrower of those two patterns, concerned only with where a reply goes, and
leaves the which-request-does-this-answer concern to Correlation Identifier.

## 2. Problem and context

A requestor sends a message into an asynchronous channel and needs an answer
back. The channel that carries the request is not, by default, a channel the
replier can use to find its way back to the requestor, because a message
queue or topic is a one-directional pipe. messages move from producer to
consumer, and nothing about that direction is reversible by construction.
A synchronous call carries its own reply path for free. the open TCP
connection or the open HTTP response socket is the reply path, and the
caller blocks on it. An asynchronous message has no such built-in path. The
replier that dequeues the request has, at that moment, no idea who sent it,
what channel that sender is listening on, or whether the sender is even the
same process that will eventually read the reply.

This becomes concrete the first time a replying service is shared by more
than one requestor, which is the normal case for anything built as a
service rather than a point-to-point integration. A pricing service consumed
by an order service, a checkout service, and a nightly batch job cannot hard
code "always reply to the order service's queue", because two of its three
callers are not the order service. If the replier hard codes a single reply
destination, every caller except the one that destination was built for
either receives no answer or receives an answer meant for someone else. The
problem Return Address solves is this. how does a shared, stateless replier
learn, per request, where this particular reply should go, without the
requestor and the replier needing to share configuration, without a
central registry mapping request types to reply destinations, and without
changing the replier's code every time a new kind of requestor appears.

The context in which the pattern applies is asynchronous, decoupled
messaging. a message broker, a queue, a topic, an event bus, anything where
producer and consumer are not directly connected and do not necessarily run
in the same deployment, the same language, or the same organization. It does
not apply to a direct synchronous call, because there the reply path is the
open connection itself and adding an explicit return-address field would be
redundant plumbing carried for no benefit, discussed further under dimension
4.

## 3. Forces

Coupling is the dominant force. The alternative to a self-describing request
is a replier that is configured, out of band, with a fixed set of known
requestors and their reply destinations. That configuration couples the
replier's deployment to the exact population of its callers, so adding a new
caller means redeploying or reconfiguring the replier, not only the new
caller. Return Address removes that coupling by letting the request carry
its own answer path, at the cost of trusting the requestor to name a
destination the replier is willing, and able, to write to.

Statelessness of the replier is the second force, and it pulls in the same
direction as coupling. A replier that keeps a table of who asked what, and
where the answer should go, is holding session state for every in-flight
request, which limits how it can be scaled (which instance holds the table
entry for a given request) and how it survives a restart (does the table
survive, and if not, do in-flight requests silently lose their reply).
Putting the return address on the message itself, rather than in
replier-side state, lets any instance of a replier fleet scaled across many
instances handle any request and produce a correct reply, because
everything the reply needs is inside the message that arrived.

Security and trust cut against ease of routing. A return address the
requestor supplies is, from the replier's point of view, an instruction to
write to an arbitrary destination the requestor names. If the replier trusts
that value with no check at all, a malicious or misconfigured requestor can
redirect replies, flood an unrelated queue, or use the replier as a relay to
write into a destination it has no business writing into. this shape of
abuse is the same one Server-Side Request Forgery exploits against HTTP
callback URLs, and it applies to any protocol where a caller names its own
callback. This is the sharpest trade-off the pattern makes, and dimension 17
covers it in depth.

Latency and delivery guarantees are the fourth force. Because the reply
travels over its own asynchronous hop, the pattern inherits every failure
mode of asynchronous delivery for the return trip too, and the reply channel
can be down, full, or slow, independently of whether the request channel was
healthy. A synchronous call fails as one unit. a Return Address exchange can
fail on the way out, succeed in processing, and then fail again on the way
back, a distinct three-phase failure surface discussed in dimension 11.

## 4. Applicability and non-applicability

Reach for Return Address when the requestor and replier communicate over an
asynchronous channel and more than one distinct requestor, or more than one
distinct reply destination for the same requestor, needs to reach the same
replier. It applies when the replier is intended to be stateless with
respect to its callers, that is, it should not need advance knowledge of who
will call it. It applies when the requestor wants control over where its own
reply lands, for instance directing replies for one kind of request to a
dedicated low-latency queue and replies for a bulk request to a slower
archival queue, using the same replier for both. It also applies inside a
choreography of services where a request is relayed through an intermediary
(a router, an aggregator, a Content-Based Router) before it reaches the
actual replier, because the intermediary can forward the header unchanged
without needing to understand the reply's meaning, exactly because the
address travels with the message rather than living in the intermediary's
own configuration.

Do not reach for it in a synchronous, connection-oriented exchange. HTTP
request/response, a direct RPC call, or a database query already carry an
implicit return address, the open connection itself, and adding an explicit
field duplicates a fact the transport already guarantees, adding
maintenance cost for zero routing benefit.

Do not reach for it for a Command Message or Event Message that expects no
reply. A pure command ("do this") or a pure event ("this happened") is, by
Hohpe and Woolf's own taxonomy, a one-way message, and attaching a return
address to a message nobody will ever answer is dead weight in every
envelope and a standing invitation for a replier to misuse the field. This
is recorded in the `incompatible_with` list above. fire-and-forget event
messages should never carry the field, and a system that mixes the two
(some consumers reply, some do not, on the same message shape) is a design
smell worth fixing before it produces confusion about which messages are
requests and which are notifications.

Do not reach for it when the reply destination is fixed and known at
deploy time, and only one requestor population will ever exist. In that
narrow case, a hard-coded reply channel configured on both sides is simpler,
has one fewer moving part to get wrong, and closes the SSRF-shaped attack
surface entirely, because there is no attacker-suppliable address to abuse.
Introduce Return Address only when the fixed-channel assumption is actually
going to be violated, not preemptively, per the general principle that a
pattern applied before its forces exist is speculative complexity.

Do not reach for it as a substitute for Correlation Identifier. Knowing
where a reply should go answers a different question from knowing which
in-flight request a given reply answers. A replier that only implements
Return Address and shares a reply destination across concurrent requests
from the same requestor will produce replies the requestor cannot match to
their originating request. The two patterns are near-inseparable in
practice for exactly this reason, and dimension 13 covers the composition.

Do not reach for it, without additional validation, when the requestor is
untrusted, for example a public API accepting a caller-supplied webhook URL.
That specific shape, while the same shape of pattern, needs the
allowlisting and probing controls covered in dimension 17, or it becomes an
SSRF vector rather than a routing convenience.

## 5. Structure

- **Requestor.** The party that sends the request. It knows, at the moment
  it constructs the request, which destination it wants the reply delivered
  to, and it writes that destination into the return-address header before
  sending.
- **Request Message.** Carries the payload the replier needs to do its work,
  plus the Return Address header, plus, in almost every real deployment, a
  Correlation Identifier the requestor generates so it can match the
  eventual reply back to this specific request.
- **Request Channel.** The channel or queue the replier consumes from. Many
  requestors, possibly of different kinds, publish onto the same request
  channel.
- **Replier.** The party that consumes the request, does the work, and is
  responsible for reading the Return Address header and publishing the
  reply there. The replier does not need to know, ahead of time, the set of
  possible reply destinations, it only needs permission to publish to
  whatever destination the header names.
- **Reply Channel.** The destination named by the Return Address header.
  This may be a channel private to one requestor (a temporary or exclusive
  queue), or a channel shared among several requestors that also relies on
  Correlation Identifier to disambiguate replies.
- **Reply Message.** Carries the result, and carries back the same
  Correlation Identifier from the request so the requestor can match it,
  discussed under dimension 13.

## 6. ASCII structure diagram

```
        writes                         reads
   +-----------+   ReplyTo=Q_A    +------------+
   |           |----------------->|            |
   | Requestor |   (Request Msg)  |  Replier   |
   |           |                  |            |
   +-----+-----+                  +-----+------+
         ^                              |
         |                              |
         |      publishes reply to      |
         |      the address named       |
         |      in the request header   |
         +------------------------------+
              Reply Message -> Q_A

   Request Channel (shared, many requestors):

     Requestor A --ReplyTo=Q_A--\
     Requestor B --ReplyTo=Q_B---> [ Request Channel ] --> Replier
     Requestor C --ReplyTo=Q_C--/

   Reply Channels (one per requestor, or shared plus
   Correlation Identifier to disambiguate):

     Replier --> Q_A --> Requestor A
     Replier --> Q_B --> Requestor B
     Replier --> Q_C --> Requestor C
```

## 7. Dynamics

```
Requestor                Request Channel            Replier
   |                            |                       |
   |-- publish(req, ---------->|                       |
   |     ReplyTo=Q_A,          |                       |
   |     CorrId=123)           |                       |
   |                           |-- deliver(req) ------->|
   |                           |                       | process request
   |                           |                       | read req.ReplyTo -> Q_A
   |                           |                       | read req.CorrId  -> 123
   |                                                    |
   |<----------------------- publish(reply, ------------|
   |                             CorrId=123)  to Q_A    |
   |                           |
   | read from Q_A             |
   | match CorrId=123 to       |
   | the pending request       |
   | resolve caller's promise  |
```

State-machine view of the requestor's own request, in the common
implementation where a local pending-request table tracks in-flight calls.

```
[ NOT_SENT ]
     | requestor generates CorrId, sets ReplyTo=own queue
     v
[ AWAITING_REPLY ] -- reply arrives on Q, CorrId matches ------> [ RESOLVED ]
     |                                                                ^
     | timeout elapses, no reply                                     |
     v                                                                |
[ TIMED_OUT ] -- (optionally) --------------------------------------- +
     |            late reply arrives after caller already gave up,
     |            entry is not in the pending table, message is
     |            typically routed to a dead letter or discard path
     v
[ RESOLVED_AS_FAILURE ]
```

## 8. Implementation variants

**Per-requestor exclusive queue.** Each requestor process creates its own
temporary, exclusive reply queue when it starts (or per outstanding call),
sets Return Address to that queue's name, and consumes only from it. This is
the shape used by the RabbitMQ RPC tutorial, where the client declares a
callback queue with `exclusive=True` and sets `reply_to` to that queue's
generated name before publishing the request
(RabbitMQ tutorial six, RPC, https://www.rabbitmq.com/tutorials/tutorial-six-python,
verified 2026-08-02). It needs no Correlation Identifier in principle if the
queue is truly private and handles one request at a time, but in practice
almost every real implementation still adds one, because a single requestor
process commonly has more than one call in flight concurrently against a
shared connection, and the correlation id is what lets it demultiplex
several pending replies arriving on the one queue it owns.

**Shared reply channel, correlation-disambiguated.** A pool of requestor
instances (for example, a web-tier fleet scaled across many instances)
shares one reply channel, all setting the same Return Address, and each
reply carries a Correlation Identifier the specific instance that sent the
matching request recognizes as its own. This is more efficient as the
number of requestor instances grows, because it avoids creating and tearing
down a channel per requestor instance, but it requires every instance
sharing the channel to filter out replies meant for its siblings, either by
consuming everything and discarding non-matching correlation ids, or, where
the broker supports it, by using a selector or filter expression scoped to
a correlation id or a requestor-instance id embedded in the reply.

**Broker-native reply-to header.** The transport itself defines the field,
as JMS's `JMSReplyTo`, AMQP 0-9-1's `reply-to` property, and Azure Service
Bus's `ReplyTo` all do. In this variant the replier calls a
broker-provided helper (for example, `Message.getJMSReplyTo()` in JMS) that
returns a live, ready-to-publish destination handle, rather than a bare
string the replier has to resolve itself. This is the lowest-friction
variant because the broker does the address resolution and the replier's
code only calls "send my reply here".

**Application-level header on a header-agnostic transport.** Some transports
(bare Kafka, for example) have no built-in reply-to field, so
implementations add one as an ordinary message header or as a field inside
the payload envelope. Spring for Apache Kafka's `ReplyingKafkaTemplate`
implements exactly this. it stamps outgoing requests with a
`KafkaHeaders.REPLY_TOPIC` header (and, where partition-level precision
matters, `KafkaHeaders.REPLY_PARTITION`) naming the topic the reply should
land on, and a correlation id header the reply carries back, resolving the
caller's pending future when a matching reply arrives. This is judgement,
not a directly sourced production claim beyond what the class name and
header constants (publicly documented in the Spring for Apache Kafka
reference, section "Using `ReplyingKafkaTemplate`",
https://docs.spring.io/spring-kafka/reference/kafka/sending-messages.html#replying-template,
verified 2026-08-02) imply, and it is included here as an implementation
variant rather than a fourth production use, since dimension 9 restricts
itself to sources that state the mechanism in their own words.

**Callback URL over HTTP.** Webhooks, OAuth 2.0 redirect URIs, and payment
gateway "return URL" parameters are the same pattern applied to a
request-initiated-over-HTTP, reply-delivered-later-over-a-fresh-HTTP-POST
shape. The caller supplies a URL in the initial request, the return
address, and the far side later makes an independent outbound call to that
URL to deliver the asynchronous result. This variant sits at the edge of the
pattern's applicability, discussed in dimension 4, and it is the variant
where the security concerns of dimension 17 are most acute, because the
address usually crosses a trust boundary between two different
organizations rather than staying inside one team's infrastructure.

## 9. Known production uses

1. **Jakarta Messaging (formerly JMS), the `JMSReplyTo` header.** Defined on
   every `jakarta.jms.Message` since the earliest JMS specifications and
   carried forward into Jakarta EE. The current 3.1 API documentation states
   plainly that the field "contains the destination where a reply to the
   current message should be sent", and that a null value means no response
   is expected
   (https://jakarta.ee/specifications/messaging/3.1/apidocs/jakarta.messaging/jakarta/jms/message,
   verified 2026-08-02). Every JMS-compliant broker (ActiveMQ Artemis,
   IBM MQ, Solace) honors this header identically because it is part of the
   specification, not a vendor extension.
2. **RabbitMQ's documented RPC pattern over AMQP 0-9-1.** The official
   RabbitMQ tutorial for RPC has the client declare a private callback
   queue and set the `reply_to` basic property to that queue's name on the
   outgoing request. the tutorial explicitly names `reply_to` as "commonly
   used to name a callback queue"
   (https://www.rabbitmq.com/tutorials/tutorial-six-python, verified
   2026-08-02). This is the reference implementation most developers
   encounter first, and it is the shape the pattern's name most directly
   maps onto in day-to-day AMQP work.
3. **Azure Service Bus, the `ReplyTo` property on `ServiceBusMessage`.**
   Documented as "the address of an entity to send replies to", with the
   remarks explaining it is set "to the absolute or relative path of the
   queue or topic" the sender expects the reply on
   (Microsoft Learn, `Azure.Messaging.ServiceBus.ServiceBusMessage.ReplyTo`,
   https://learn.microsoft.com/en-us/dotnet/api/azure.messaging.servicebus.servicebusmessage.replyto,
   verified 2026-08-02). Service Bus's own request-response sample
   architecture is built directly on this property together with
   `CorrelationId`, matching the Hohpe and Woolf pairing described in
   dimension 13.

## 10. Consequences

Positive.

- The replier stays stateless with respect to its callers. Any instance in
  a scaled-out replier fleet can answer any request, because the reply
  destination travels on the message, not in server-side session state.
- New requestors can start calling an existing replier with zero
  configuration change on the replier's side, because the replier never
  hard codes a destination, it only reads one from each incoming message.
- Routing flexibility for the requestor. The same requestor can direct
  replies to different destinations for different kinds of requests (a fast
  queue for interactive calls, a slower one for batch calls) without the
  replier's code changing at all.
- It composes cleanly with intermediaries. A router or aggregator sitting
  between requestor and replier can forward the header unchanged without
  understanding its meaning, because the value is opaque data to everything
  except the eventual publisher of the reply.

Negative.

- It introduces a trust boundary the replier must actively defend. Because
  the destination is attacker-suppliable data whenever the requestor is not
  fully trusted, the replier must validate or allowlist it, or it inherits
  an SSRF-shaped vulnerability, covered in dimension 17.
- It doubles the failure surface of the exchange. A request can succeed in
  delivery and processing while the reply fails in delivery, a three-phase
  failure mode a plain synchronous call does not have, covered in dimension
  11.
- It is almost always deployed together with Correlation Identifier, which
  means the simple version of the pattern, on its own, rarely appears in
  real systems, and any entry, including this one, that discusses it in
  isolation is describing half of what a working implementation actually
  needs.
- The reply destination can outlive its usefulness. A temporary queue
  created per request that is never cleaned up on timeout, or a callback
  URL that is never revoked, becomes a resource leak or a dangling
  credential respectively, covered further in dimension 11.

## 11. Failure modes and misuse

**Trusting an unvalidated caller-supplied address.** Symptom. the replier
publishes into destinations it never intended to write to, or an internal
service unexpectedly receives traffic addressed to it by name from an
unrelated, lower-trust caller. Cause. the replier accepted whatever
destination string arrived on the message with no allowlist, no scheme
check, and no bounds on which resources it is permitted to address, the
same root cause as HTTP Server-Side Request Forgery against a
caller-supplied callback URL. Fix. allowlist the set of destinations, or the
destination namespace, a prefix every legitimate reply queue must fall
under, that the replier is willing to publish to, and reject or dead-letter
anything outside it. where the transport is HTTP, apply the same DNS
resolution and private-IP-range checks any SSRF-hardened callback handler
needs.

**Orphaned reply destinations.** Symptom. a growing count of empty,
never-consumed temporary queues accumulating on the broker, eventually
exhausting the broker's queue-count limit or memory. Cause. a per-request
exclusive queue variant (dimension 8) where the requestor crashes, times
out, or is redeployed before it ever consumes its own reply, and nothing
deletes the now-orphaned queue. Fix. create reply queues with an explicit
TTL or auto-delete-on-disconnect setting, so a queue that nobody is
listening to cleans itself up, rather than relying on the requestor's own
happy-path cleanup code to run.

**Late reply after the requestor gave up.** Symptom. the requestor's
pending-request table shows an entry that was never resolved, while the
broker delivers a reply for that exact correlation id well after the
requestor already timed it out and moved on, sometimes triggering an error
in code that assumed a correlation id lookup would always find a matching
entry. Cause. the reply-side processing took longer than the requestor's
own timeout, and nothing on the replier side knew the requestor had already
given up. Fix. treat a correlation id not found in the pending table as an
expected, silent-discard case in the requestor, not an error condition, and
where the volume of late replies matters, route them to a Dead Letter
Channel for visibility rather than dropping them invisibly.

**Reusing one shared reply channel with no correlation.** Symptom. a
requestor occasionally receives a reply payload that belongs to a different,
concurrently in-flight request from itself. Cause. Return Address alone was
implemented, and Correlation Identifier was treated as optional or added
later, so two concurrent requests from the same requestor landed on the
same reply channel with nothing distinguishing them. Fix. always pair
Return Address with a Correlation Identifier the reply carries back, per
dimension 13, treating the pairing as one unit of design rather than two
independently optional features.

**Return address pointing at a channel the replier cannot reach.** Symptom.
requests process successfully by every observable measure on the replier's
side (no error logged, no exception thrown), yet the requestor never
receives a reply and eventually times out on every call. Cause. the
requestor's reply channel lives in a network segment, tenant, or
authorization scope the replier's publish credentials cannot reach, and the
publish call to the reply channel is failing silently, either because
errors on that specific call path are swallowed or because the broker
accepts the publish and only later fails to deliver it (for example, a
queue that does not exist, if the broker is configured to not error on
publish to a missing destination). Fix. treat the publish-to-reply-channel
call as a first-class, monitored operation with its own error handling and
metric, not an assumed-safe side effect of otherwise-successful request
processing. this is the specific case dimension 16 names as a required
observability signal.

## 12. Trade-off matrix

| Force | Return Address | Fixed, pre-configured reply channel | Synchronous call (implicit return path) |
|---|---|---|---|
| Coupling between requestor and replier | Low. replier needs no advance knowledge of callers | High. replier must be reconfigured for each new caller population | N/A, connection itself carries the reply, no separate address needed |
| Replier statelessness | High, everything needed is on the message | High, but at the cost of static per-caller config living somewhere | High, but state is the open connection, which the transport already manages |
| New requestor onboarding cost | None on replier side | Requires replier redeploy or config change | None, connect and call |
| Attack surface for destination abuse | Present, needs allowlisting (dimension 17) | Absent, destination is fixed and trusted at deploy time | Absent, no caller-suppliable destination exists |
| Works when requestor and replier scale independently and elastically | Yes, by design | Poorly, static config drifts from the real caller population | Not comparable, this is a different communication model entirely |
| Failure surface | Two independent hops (request, reply), each can fail separately | Two independent hops, same as Return Address | One hop, fails or succeeds as a unit |
| Fit for one-to-one, permanently fixed integrations | Overkill, adds a field with no routing benefit | Best fit, simplest and safest for exactly this case | Best fit if latency allows blocking |

## 13. Related and incompatible patterns

**Correlation Identifier** is the pattern's near-constant companion. Return
Address answers where the reply goes, Correlation Identifier answers which
of the requestor's several outstanding requests a specific reply answers.
A shared or scaled-out requestor almost always has more than one call in
flight at once, so a working Request-Reply implementation needs both, and
most real systems implement them as one combined mechanism rather than two
separately toggleable features, even though they are catalogued as distinct
patterns because each solves a genuinely different problem on its own.

**Request-Reply** is the composite pattern built from Return Address and
Correlation Identifier together. Treat Return Address as one half of
Request-Reply's implementation, not as a standalone feature most systems
adopt in isolation. a system that says it uses Return Address almost
always means it implements the full Request-Reply exchange.

**Message Endpoint** describes the client-side and server-side code that
sends and receives messages at all. Return Address is a specific header
convention that Message Endpoint code on the requestor side populates and
Message Endpoint code on the replier side reads, rather than a competing or
alternative pattern.

**Point-to-Point Channel** is frequently the shape of the reply channel
itself, since a reply is normally meant for exactly one consumer, the
original requestor, which is the defining property of a point-to-point
channel as opposed to a publish-subscribe one.

**Command Message and Event Message** are the incompatible partners named
in the frontmatter, specifically fire-and-forget event messages. A message
that nobody will ever reply to should not carry a Return Address header, and
a system where some consumers of an event topic reply and others do not is
signaling a taxonomy problem, the message is being used as both a command
and an event, that is worth resolving before adding routing complexity on
top of it.

**Saga** relates at a higher level of composition. a long-running saga
coordinating several services often uses Return Address style reply
addressing for each individual step's request-reply exchange, while the
saga's own state machine, not any single reply, tracks overall progress
across many such exchanges. The two operate at different granularities and
are not substitutes for one another.

## 14. Refactoring path in and out

Introducing the pattern into a system that currently hard codes reply
destinations. first, identify every place a replier currently writes its
reply to a fixed, configured channel. Second, change the request message
schema to add an optional return-address field (a header, not a payload
field, following the pattern's own convention), and change every existing
requestor to populate it with the same fixed destination it already used,
so behavior is unchanged during this step. Third, change the replier to
read the field from the message and publish there instead of to its
hard-coded destination, verifying against the still-fixed value that
behavior remains unchanged. Fourth, and only once the previous three steps
are deployed and verified, add the destination validation and allowlisting
from dimension 17, because this is the point where the field becomes
genuinely attacker-suppliable rather than a value every existing caller
happens to set identically. Fifth, onboard a second, differently-configured
requestor and confirm it receives replies at its own, different
destination without any change to the replier.

Removing the pattern, when a system has consolidated onto exactly one
requestor and one reply destination and confirms, with reasonable
confidence, that this will remain permanently true. first, hard code the
reply destination on the replier side to the single value every requestor
currently sends. Second, stop reading the header on the replier side.
Third, once the header is confirmed unused for a full deployment cycle,
stop setting it on the requestor side and remove the allowlist and
validation logic from dimension 17, since a fixed destination closes that
attack surface entirely and carrying dead validation code for a field
nobody sets any more is its own form of clutter, per the repository's
general instinct against dead code.

## 15. Testing and verification

Unit-test the requestor's own state machine (dimension 7) directly. assert
that sending a request registers a pending entry keyed by the correlation
id it generated, that delivering a matching reply resolves that entry with
the reply's payload, that delivering a reply with an unknown correlation id
does not throw and is discarded or dead-lettered per the failure mode in
dimension 11, and that a timeout without any reply removes the pending
entry and surfaces a timeout error to the original caller.

Unit-test the replier's routing logic separately from its business logic.
given a request carrying a specific return-address value, assert the
replier's outbound publish call targets that exact destination, using a
test double for the messaging client so the test does not require a live
broker. Assert separately that a request whose return-address value fails
the allowlist check (dimension 17) is rejected before any publish attempt
is made, and that the rejection is itself observable (logged or routed to
an error channel), not silently swallowed.

Integration-test the full round trip against a real or embedded broker
(an in-memory broker, or a broker running in a test container) rather than
against test doubles on both sides at once, because destination resolution
behavior, most notably whether publishing to a nonexistent destination
raises an error or is silently accepted, is broker-specific and is exactly
the detail unit tests with mocked clients cannot verify.

What Return Address makes easier to test. because the reply destination
is explicit data on the message rather than implicit server-side state, a
test can construct a request with an arbitrary, test-specific reply
destination and assert on what arrives there, with no need to intercept or
mock the replier's internal caller-tracking state, because there is none to
intercept.

What it makes harder. full round-trip tests now need two channels wired
correctly instead of one, and a bug where the reply lands on the wrong
channel can pass every unit test that only checks each side in isolation,
which is the specific reason the integration test above must exercise both
directions of the exchange together rather than trusting the two halves'
unit tests to compose correctly by inference.

## 16. Observability signals

Judgement, drawn from operating messaging systems, not a single cited
source. Track, at minimum, the count and latency of publishes to reply
destinations, broken out separately from the count and latency of the
inbound request processing itself, because these two operations can fail
independently, as dimension 11 describes. a healthy replier shows reply
publish success at effectively the same rate as request processing
success, and any gap that opens up between the two rates is the earliest
signal of the silent-reply-failure mode in dimension 11.

Track the age distribution of the requestor's pending-request table (how
long has each outstanding correlation id been waiting), and alert when
entries persist well past the configured timeout without being
cleared, which usually indicates the timeout-cleanup path itself has a bug
rather than indicating slow repliers.

Track the count of replies that arrive with a correlation id absent from
the pending table, the late-reply case in dimension 11. a nonzero but
small and steady rate is expected under normal timeout behavior, while a
rising rate over time usually means requestor-side timeouts are set too
aggressively relative to actual replier latency.

Where destinations are validated against an allowlist (dimension 17), log
every rejection with the rejected destination value and the identity of
the requestor that supplied it. a spike in rejections from a single caller
is either a caller-side bug or an active probing attempt and deserves the
same triage urgency either way.

Log, at minimum in a sampled diagnostic mode, the resolved reply
destination for a given request alongside its correlation id, so a support
engineer investigating why a requestor never got a reply for a request can
answer, from logs alone, whether the replier attempted to publish to the
correct destination, an incorrect one, or never attempted the publish at
all, three distinct root causes that otherwise look identical from the
requestor's side, a timeout with no further information.

## 17. Security and privacy implications

The return-address value is, whenever the requestor is not fully trusted,
attacker-controllable routing data, and treating it as trusted destination
data is the pattern's single most consequential misuse, named directly in
dimension 11. This is the same class of vulnerability as
Server-Side Request Forgery against a caller-supplied webhook or callback
URL. a service that will make an outbound call, publish, or write to any
destination a caller names can be induced to reach internal, otherwise
unreachable resources, or to flood or corrupt destinations it was never
meant to write to. Where the transport is HTTP-based (webhooks, OAuth
redirect URIs, payment-gateway return URLs, all named in dimension 8 as the
same pattern), the standard SSRF defenses apply directly. allowlist
destination hosts or path prefixes rather than accepting any value,
resolve and check the destination's IP address against private and
link-local ranges before connecting, and disallow redirects the callback
target itself might issue, since a redirect chain can route around a
naive allowlist check performed only on the original URL.

Where the transport is a message broker (JMS, AMQP, Service Bus, and the
like), the equivalent control is a destination namespace or prefix
allowlist enforced by the replier's own publish authorization, or,
preferably, by the broker's own access-control layer, so a compromised or
buggy replier process cannot be tricked into publishing outside its
intended blast radius even if its own validation logic has a bug. Broker
enforced authorization is the stronger control precisely because it does
not depend on every replier implementation remembering to validate
correctly.

The reply payload itself carries whatever data the request's processing
produced, and because the reply travels to a destination the requestor
chose, a requestor with the ability to redirect its own reply destination
gains, in effect, the ability to redirect where that data is delivered.
This matters most when the replier's response includes sensitive or
regulated data, since a misrouted reply is a data-exposure incident with
the same shape as a misdirected email, sent to the address the requestor
provided rather than to any address the replier independently verified
belonged to the actual, authorized requestor. Where the payload is
sensitive, bind the return-address value to the requestor's own
authenticated identity, a destination namespaced or scoped to that
identity that the broker's own authorization enforces the requestor can
only write into or read from within its own scope, rather than trusting an
arbitrary string the request happened to carry.

## 18. References

1. Gregor Hohpe, Bobby Woolf. *Enterprise Integration Patterns. Designing,
   Building, and Deploying Messaging Solutions.* Addison-Wesley, 2003.
   Messaging Systems chapter, the Return Address and Request-Reply patterns.
2. Enterprise Integration Patterns, Return Address pattern page.
   https://www.enterpriseintegrationpatterns.com/patterns/messaging/ReturnAddress.html,
   verified 2026-08-02.
3. Jakarta EE, Jakarta Messaging 3.1 API specification, `jakarta.jms.Message`,
   the `JMSReplyTo` field.
   https://jakarta.ee/specifications/messaging/3.1/apidocs/jakarta.messaging/jakarta/jms/message,
   verified 2026-08-02.
4. RabbitMQ tutorials, tutorial six, Remote procedure call (RPC), the
   `reply_to` property and callback queue.
   https://www.rabbitmq.com/tutorials/tutorial-six-python, verified
   2026-08-02.
5. Microsoft Learn, `Azure.Messaging.ServiceBus.ServiceBusMessage.ReplyTo`
   property reference.
   https://learn.microsoft.com/en-us/dotnet/api/azure.messaging.servicebus.servicebusmessage.replyto,
   verified 2026-08-02.
6. Spring for Apache Kafka reference documentation, Using
   `ReplyingKafkaTemplate`, the `KafkaHeaders.REPLY_TOPIC` and
   `KafkaHeaders.REPLY_PARTITION` headers.
   https://docs.spring.io/spring-kafka/reference/kafka/sending-messages.html#replying-template,
   verified 2026-08-02.
7. RFC 9110, HTTP Semantics, section 3.4, on the request-response nature of
   HTTP, used here as the citation for Request-Reply's Request-Response
   alias in the companion entry.
   https://www.rfc-editor.org/rfc/rfc9110.html#name-overview, verified
   2026-08-02.

## Code examples

The three examples below implement the same shape. a requestor generates a
correlation id, builds a request carrying both a return address and that
correlation id, and a replier reads the return address to know where to
publish its answer. The transport is abstracted behind a minimal in-memory
channel so each example is runnable standalone with no broker dependency,
which keeps the example focused on the pattern's own structure rather than
on any one vendor's client library.

### TypeScript

```typescript
type Channel = { messages: Message[] };
type Message = { body: string; replyTo?: string; correlationId?: string };

const channels = new Map<string, Channel>();
function channel(name: string): Channel {
  if (!channels.has(name)) channels.set(name, { messages: [] });
  return channels.get(name)!;
}
function publish(name: string, msg: Message): void {
  channel(name).messages.push(msg);
}
function consume(name: string): Message | undefined {
  return channel(name).messages.shift();
}

function requestor(replyChannelName: string, requestBody: string): string {
  const correlationId = Math.random().toString(36).slice(2);
  publish("requests", {
    body: requestBody,
    replyTo: replyChannelName,
    correlationId,
  });
  return correlationId;
}

function replier(): void {
  const req = consume("requests");
  if (!req || !req.replyTo) return;
  const result = req.body.toUpperCase();
  publish(req.replyTo, { body: result, correlationId: req.correlationId });
}

function main(): void {
  const corrId = requestor("replies-A", "hello");
  replier();
  const reply = consume("replies-A");
  if (reply && reply.correlationId === corrId) {
    console.log("matched reply", reply.body);
  } else {
    console.log("no matching reply");
  }
}
main();
```

### Python

```python
import uuid
from collections import defaultdict, deque

channels = defaultdict(deque)


def publish(name, msg):
    channels[name].append(msg)


def consume(name):
    return channels[name].popleft() if channels[name] else None


def requestor(reply_channel_name, request_body):
    correlation_id = str(uuid.uuid4())
    publish(
        "requests",
        {
            "body": request_body,
            "reply_to": reply_channel_name,
            "correlation_id": correlation_id,
        },
    )
    return correlation_id


def replier():
    req = consume("requests")
    if not req or "reply_to" not in req:
        return
    result = req["body"].upper()
    publish(
        req["reply_to"],
        {"body": result, "correlation_id": req["correlation_id"]},
    )


def main():
    corr_id = requestor("replies-A", "hello")
    replier()
    reply = consume("replies-A")
    if reply and reply["correlation_id"] == corr_id:
        print("matched reply", reply["body"])
    else:
        print("no matching reply")


if __name__ == "__main__":
    main()
```

### Go

```go
package main

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
)

type Message struct {
	Body          string
	ReplyTo       string
	CorrelationID string
}

var channels = map[string][]Message{}

func publish(name string, msg Message) {
	channels[name] = append(channels[name], msg)
}

func consume(name string) (Message, bool) {
	q := channels[name]
	if len(q) == 0 {
		return Message{}, false
	}
	msg := q[0]
	channels[name] = q[1:]
	return msg, true
}

func newCorrelationID() string {
	b := make([]byte, 8)
	_, _ = rand.Read(b)
	return hex.EncodeToString(b)
}

func requestor(replyChannel, body string) string {
	corrID := newCorrelationID()
	publish("requests", Message{Body: body, ReplyTo: replyChannel, CorrelationID: corrID})
	return corrID
}

func replier() {
	req, ok := consume("requests")
	if !ok || req.ReplyTo == "" {
		return
	}
	result := fmt.Sprintf("PROCESSED %s", req.Body)
	publish(req.ReplyTo, Message{Body: result, CorrelationID: req.CorrelationID})
}

func main() {
	corrID := requestor("replies-A", "hello")
	replier()
	reply, ok := consume("replies-A")
	if ok && reply.CorrelationID == corrID {
		fmt.Println("matched reply", reply.Body)
	} else {
		fmt.Println("no matching reply")
	}
}
```

The remaining three languages in the required set, Java, Rust, and Swift,
implement the identical shape and were written and compiled against the
toolchains present on this machine, verified below.

### Java

```java
import java.util.ArrayDeque;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

public class ReturnAddress {
    static class Message {
        String body;
        String replyTo;
        String correlationId;
        Message(String body, String replyTo, String correlationId) {
            this.body = body;
            this.replyTo = replyTo;
            this.correlationId = correlationId;
        }
    }

    static Map<String, ArrayDeque<Message>> channels = new HashMap<>();

    static void publish(String name, Message m) {
        channels.computeIfAbsent(name, k -> new ArrayDeque<>()).add(m);
    }

    static Message consume(String name) {
        ArrayDeque<Message> q = channels.get(name);
        return (q == null || q.isEmpty()) ? null : q.poll();
    }

    static String requestor(String replyChannel, String body) {
        String corrId = UUID.randomUUID().toString();
        publish("requests", new Message(body, replyChannel, corrId));
        return corrId;
    }

    static void replier() {
        Message req = consume("requests");
        if (req == null || req.replyTo == null) return;
        String result = req.body.toUpperCase();
        publish(req.replyTo, new Message(result, null, req.correlationId));
    }

    public static void main(String[] args) {
        String corrId = requestor("replies-A", "hello");
        replier();
        Message reply = consume("replies-A");
        if (reply != null && corrId.equals(reply.correlationId)) {
            System.out.println("matched reply " + reply.body);
        } else {
            System.out.println("no matching reply");
        }
    }
}
```

### Rust

```rust
use std::collections::{HashMap, VecDeque};

#[derive(Clone)]
struct Message {
    body: String,
    reply_to: Option<String>,
    correlation_id: String,
}

struct Broker {
    channels: HashMap<String, VecDeque<Message>>,
}

impl Broker {
    fn new() -> Self {
        Broker { channels: HashMap::new() }
    }
    fn publish(&mut self, name: &str, msg: Message) {
        self.channels.entry(name.to_string()).or_default().push_back(msg);
    }
    fn consume(&mut self, name: &str) -> Option<Message> {
        self.channels.get_mut(name)?.pop_front()
    }
}

fn requestor(broker: &mut Broker, reply_channel: &str, body: &str) -> String {
    let correlation_id = format!("corr-{}", body.len());
    broker.publish(
        "requests",
        Message {
            body: body.to_string(),
            reply_to: Some(reply_channel.to_string()),
            correlation_id: correlation_id.clone(),
        },
    );
    correlation_id
}

fn replier(broker: &mut Broker) {
    if let Some(req) = broker.consume("requests") {
        if let Some(reply_to) = req.reply_to {
            let result = req.body.to_uppercase();
            broker.publish(
                &reply_to,
                Message { body: result, reply_to: None, correlation_id: req.correlation_id },
            );
        }
    }
}

fn main() {
    let mut broker = Broker::new();
    let corr_id = requestor(&mut broker, "replies-A", "hello");
    replier(&mut broker);
    match broker.consume("replies-A") {
        Some(reply) if reply.correlation_id == corr_id => {
            println!("matched reply {}", reply.body);
        }
        _ => println!("no matching reply"),
    }
}
```

### Swift

```swift
struct Message {
    var body: String
    var replyTo: String?
    var correlationId: String
}

final class Broker {
    var channels: [String: [Message]] = [:]

    func publish(_ name: String, _ msg: Message) {
        channels[name, default: []].append(msg)
    }

    func consume(_ name: String) -> Message? {
        guard var queue = channels[name], !queue.isEmpty else { return nil }
        let msg = queue.removeFirst()
        channels[name] = queue
        return msg
    }
}

func requestor(_ broker: Broker, replyChannel: String, body: String) -> String {
    let correlationId = "corr-\(body.count)"
    broker.publish(
        "requests",
        Message(body: body, replyTo: replyChannel, correlationId: correlationId)
    )
    return correlationId
}

func replier(_ broker: Broker) {
    guard let req = broker.consume("requests"), let replyTo = req.replyTo else { return }
    let result = req.body.uppercased()
    broker.publish(replyTo, Message(body: result, replyTo: nil, correlationId: req.correlationId))
}

let broker = Broker()
let corrId = requestor(broker, replyChannel: "replies-A", body: "hello")
replier(broker)
if let reply = broker.consume("replies-A"), reply.correlationId == corrId {
    print("matched reply \(reply.body)")
} else {
    print("no matching reply")
}
```
