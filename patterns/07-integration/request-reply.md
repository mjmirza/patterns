---
name: Request-Reply
slug: request-reply
family: 07-integration
category: Messaging
aliases: [Request-Response, RPC over Messaging, Synchronous Messaging]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [return-address, correlation-identifier, message-endpoint, competing-consumers, saga]
incompatible_with: [event-driven-architecture-tight-coupling]
verified: 2026-08-02
---

# Request-Reply

## 1. Name, aliases, and lineage

The canonical name is Request-Reply. It is catalogued as a messaging pattern in
Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns. Designing,
Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003, in the
Messaging Patterns chapter, alongside Return Address and Correlation
Identifier. The pattern's own site puts the intent plainly. "Send a pair of
Request-Reply messages, each on its own channel"
(https://www.enterpriseintegrationpatterns.com/patterns/messaging/RequestReply.html,
verified 2026-08-02). The two participants are named a Requestor, which sends
a request and waits for an answer, and a Replier, which receives the request
and sends the reply back.

The most common alias is Request-Response, used interchangeably in almost
every protocol specification that implements the same idea over a different
transport. RFC 9110, the current HTTP semantics specification, opens its
overview with the sentence "HTTP is a stateless request/response protocol for
exchanging messages across a connection" (RFC 9110 section 3.4,
https://www.rfc-editor.org/rfc/rfc9110.html#name-overview, verified
2026-08-02), which is Request-Reply under HTTP's own vocabulary. RPC over
Messaging is the name used when the pattern is deliberately built on top of an
asynchronous transport that was not designed for it, for example a message
broker, and the name signals that the synchronous feel is an illusion built on
a substrate that was asynchronous to begin with.

Request-Reply predates its formal name by decades. Remote procedure call, as
described in Andrew Birrell and Bruce Nelson's 1984 paper "Implementing Remote
Procedure Calls" (ACM Transactions on Computer Systems, volume 2, issue 1),
is the same shape at the network layer, one message out, one message back,
matched by a call identifier. Hohpe and Woolf's contribution was not the idea
of a two-way exchange, which is as old as networking itself, but naming its
two constituent sub-patterns, Return Address and Correlation Identifier, and
showing that the combination of these two simpler patterns is what makes
Request-Reply work reliably on a channel that carries many concurrent
conversations at once. That decomposition is why this entry treats
Request-Reply as a composite pattern rather than a single primitive.

A pattern is easy to confuse with plain synchronous method calls, so it is
worth stating precisely what distinguishes them. A local function call binds
caller and callee in the same process, the same memory space, and the same
failure domain. Request-Reply names the pattern used specifically when caller
and responder are separated by a network or a broker, so the call can fail in
ways a local call cannot, timeout, partial delivery, duplicate delivery, or a
responder that is not currently running at all. Every dimension below is
shaped by that separation.

## 2. Problem and context

A component needs an answer from another component before it can continue,
and the two components do not share a process, a thread, or a call stack.

This is the ordinary shape of almost every distributed system interaction. A
web browser needs the contents of a page before it can render anything, so it
sends an HTTP GET and blocks the user interface until a response body
arrives. A checkout service needs an authorization decision from a payment
gateway before it can mark an order paid, and it cannot proceed on a guess.
An order-processing worker needs the current inventory count from a warehouse
service before it can decide whether to fulfil or backorder a line item. In
every one of these, the caller's own logic cannot advance without a piece of
information or a decision that only lives on the other side of a network
boundary, and it cannot fabricate that piece of information locally without
producing a wrong answer.

The context in which Request-Reply is the correct choice, rather than a fire
and forget notification, has one defining property, the caller has a real
decision or a real value that depends on the specific answer. If the caller
would behave identically regardless of the reply's content, or if it does not
need the reply at all to keep functioning, the situation calls for a
one-way message or an event, not Request-Reply, and forcing a reply channel
onto that situation adds coupling with no compensating benefit. The pattern
also assumes the responder can be reached in a bounded time relevant to the
caller's own operation. A caller willing to wait hours for an answer does not
need this pattern, it needs an asynchronous workflow with a callback or a
poll, because a genuinely long wait held open as a synchronous call ties up a
thread, a connection, or a UI for no reason.

Two transport shapes host this pattern and they carry different problems.
Over a direct connection, HTTP, gRPC, a raw TCP request, the transport itself
supplies the return path, the same socket the request arrived on carries the
reply back, so there is no ambiguity about where the reply goes. Over a
message broker, the transport has no built-in return path, a message
published to a queue or topic is consumed once by whichever consumer picks it
up, and that consumer has no built-in way to reach back to the original
sender unless the sender tells it how. This second shape is exactly why
Return Address and Correlation Identifier exist as separate sub-patterns
rather than being folded silently into Request-Reply, because a
broker-mediated Request-Reply cannot function without both of them.

## 3. Forces

- **Latency versus decoupling.** Favours latency at the cost of decoupling.
  The caller is bound to the responder's actual availability and response
  time for the duration of the call, which is the opposite of what an
  event-driven, fire-and-forget architecture buys. A slow responder makes
  every caller slow, transitively, all the way up the call chain.
- **Simplicity of caller logic versus resilience.** Favours simplicity. A
  caller that gets its answer inline, right where it asked for it, is easier
  to read, test, and reason about than one that must register a callback,
  store partial state, and resume later. The cost is paid in resilience,
  because the caller's thread or connection is now a resource held hostage to
  a remote party's behaviour.
- **Consistency versus availability.** Favours a fresh, consistent answer.
  The caller gets the responder's current state at the moment of the call,
  never a stale cached guess, which matters for anything involving money,
  inventory, or authorization. The trade is that the caller's own
  availability now depends on the responder's availability, a direct
  instance of the CAP-theorem tension applied to a single synchronous call
  rather than a replicated data store.
- **Operational simplicity versus throughput.** A direct connection
  Request-Reply, HTTP or gRPC, is operationally simple to trace, a request in
  a log line has an obvious matching response a few milliseconds later. A
  broker-mediated Request-Reply trades that simplicity for the broker's
  throughput and buffering properties, at the cost of needing Correlation
  Identifier bookkeeping and a temporary or shared reply channel that must
  itself be managed, monitored, and cleaned up.
- **Coupling in time.** The pattern couples caller and responder in time,
  both must be reachable during the same window, even when the broker
  decouples them in location and in process. This is a subtler force than it
  looks, because a system can be fully decoupled at the messaging layer and
  still be tightly coupled in availability if every interaction is
  Request-Reply.
- **Cost of correctness under failure.** Favours explicit failure handling
  at the cost of code volume. A local call either returns or the whole
  process crashes, there is rarely a silent partial failure. A networked
  Request-Reply can fail in the request leg, the processing, or the reply
  leg, and each failure mode needs its own handling, which the caller cannot
  distinguish from the outside without a timeout and a well-defined retry
  policy.

A pattern that resolved every one of those tensions for free would not need a
name. Request-Reply buys a simple mental model for the caller in exchange for
temporal coupling and a resilience burden that the caller must actively
design for, never assume away.

## 4. Applicability and non-applicability

Reach for Request-Reply when the following hold.

- The caller genuinely needs a specific answer, a value or a decision, before
  it can proceed correctly, and a guess or a default is not acceptable.
- The responder can be reached in a time frame the caller can tolerate
  holding open, whether that is milliseconds over HTTP or a few seconds over
  a broker-mediated RPC.
- The interaction is naturally one caller waiting on one specific answer from
  one logical responder, not a broadcast to many interested parties.
- The failure mode of "the responder did not answer" has a sensible,
  implementable caller-side behaviour, retry, fallback, error surfaced to the
  user, or a circuit breaker trip.

Do NOT reach for Request-Reply, and prefer a one-way message, an event, or an
asynchronous workflow instead, when any of these hold.

- The caller does not need the specific content of a reply to keep working,
  it only needs to know the action was accepted. A fire-and-forget command or
  an acknowledgment-only pattern removes the coupling for free.
- Many parties are interested in the outcome, not one. A published event with
  multiple subscribers scales without the caller enumerating every
  interested party and issuing a separate Request-Reply to each.
- The true processing time is long relative to how long a caller can hold a
  connection or a thread open, a document conversion that takes minutes, a
  human approval step that takes days. Forcing this into Request-Reply either
  times out the caller or ties up resources for the whole duration; an
  asynchronous request-acknowledge-poll or callback pattern fits the shape of
  the work.
- The responder is expected to be intermittently unavailable by design, for
  example a mobile device or an edge node with unreliable connectivity.
  Request-Reply against a party that is offline half the time produces
  constant caller-side failure handling for a condition that is actually
  normal, and a durable queue with eventual delivery fits better.
- The system already leans on event-driven architecture for decoupling, and
  introducing Request-Reply across a service boundary reintroduces the exact
  temporal coupling the event-driven design was chosen to avoid. This is
  recorded in the frontmatter `incompatible_with` field, not because the two
  can never coexist in one system, they routinely do at different
  boundaries, but because layering Request-Reply onto a boundary another
  team deliberately decoupled with events is a design regression that should
  be named and deliberately chosen, never accidental.

## 5. Structure

- **Requestor.** The party that initiates the exchange. It constructs a
  request message, attaches a Return Address so the reply can find its way
  back, attaches a Correlation Identifier so it can match an eventual reply
  to this specific request among possibly many outstanding ones, sends the
  request, and then waits, either by blocking a thread or by registering a
  continuation, for a bounded amount of time.
- **Replier.** The party that receives the request, does the work the
  request asks for, and sends a reply message addressed to the Return
  Address supplied in the request, carrying the same Correlation Identifier
  back unchanged so the Requestor can match it.
- **Request channel.** The path the request travels, a direct connection, a
  request queue, or a topic the Replier is known to consume.
- **Reply channel, the Return Address participant.** The path the reply
  travels back. Over a direct connection this is implicit, the same socket.
  Over a broker this is an explicit value carried inside the request
  message, commonly a queue name, so the Replier knows where to publish the
  answer without a hardcoded, tightly coupled reference to the Requestor.
- **Correlation Identifier participant.** A value, generated by the
  Requestor and echoed unchanged by the Replier, that lets a Requestor
  servicing many outstanding requests over one shared reply channel match
  each incoming reply to the request that produced it.
- **Timeout and failure handler, at the Requestor.** The logic that decides
  what happens when no reply arrives within a bounded window, retry the
  request, fail the caller's operation, or fall back to a default.

## 6. ASCII structure diagram

```
+------------+                                   +------------+
| Requestor  |                                   |  Replier   |
|            |                                   |            |
|  build     |----- request channel ------------>|   receive  |
|  request   |    (id=42, reply_to=Q_reply)       |   request  |
|            |                                   |            |
|  wait /    |                                   |   process  |
|  block on  |                                   |            |
|  reply_to  |<---- reply channel ---------------|   build    |
|            |    (id=42, result=...)            |   reply    |
|  match by  |                                   |   echo id  |
|  correl-id |                                   |            |
+------------+                                   +------------+

        Direct-connection variant (HTTP, gRPC unary):

+------------+                                   +------------+
| Requestor  |====== single connection =========>|  Replier   |
| (client)   |<===== reply on same socket ========|  (server)  |
+------------+                                   +------------+
      no explicit Return Address or Correlation Identifier needed,
      the transport itself supplies both.
```

## 7. Dynamics

```
Direct-connection sequence (e.g. gRPC unary RPC, HTTP):

  Requestor                         Replier
     |                                 |
     |----- open connection --------->|
     |----- request message --------->|
     |                                 | process request
     |<---- response message ---------|
     |----- close/reuse connection----|
     |                                 |

Broker-mediated sequence (e.g. RabbitMQ RPC pattern):

  Requestor                Broker              Replier
     |                        |                    |
     | generate correlation_id                     |
     | declare exclusive reply_to queue             |
     |----- publish(request,                        |
     |       reply_to=Q_r,                          |
     |       correlation_id=cid) ------->|          |
     |                        |----- deliver ------>|
     |                        |                    | process
     |                        |<---- publish(reply, |
     |                        |       correlation_id=cid) |
     |<---- deliver reply ----|                    |
     | match cid against outstanding map            |
     | resolve caller's waiting future              |

Timeout path:

  Requestor                                    Replier
     |----- request (cid=99) -------------------->| (never responds,
     |  start timer                                |  crashed or slow)
     |  timer expires, no reply for cid=99          |
     | remove cid=99 from outstanding map           |
     | surface timeout error to caller              |
```

The direct-connection sequence needs no explicit correlation because a single
TCP or HTTP/2 stream already ties one request to one response by construction.
The broker-mediated sequence needs the Correlation Identifier because a shared
reply queue can carry replies for many outstanding requests interleaved in
arbitrary order, and only the identifier tells the Requestor which reply has
arrived.

## 8. Implementation variants

- **Direct synchronous call (HTTP, gRPC unary).** The simplest variant. The
  transport layer supplies both the return path and the correlation
  implicitly, so application code writes what looks like a plain function
  call. gRPC's own documentation puts it directly, calling this the case
  where "the client sends a single request to the server and gets a single
  response back," the same shape as an ordinary function call
  (https://grpc.io/docs/what-is-grpc/core-concepts/, verified 2026-08-02).
- **Blocking call over a message broker.** The Requestor thread publishes a
  request and blocks on a future or a condition variable until a reply with
  the matching Correlation Identifier arrives on its reply queue, or a
  timeout fires. RabbitMQ's own RPC tutorial documents exactly this shape,
  stating that a client "sends a request message and a server replies with a
  response message," using the `reply_to` property, "commonly used to name a
  callback queue," and the `correlation_id` property, "useful to correlate
  RPC responses with requests"
  (https://www.rabbitmq.com/tutorials/tutorial-six-python, verified
  2026-08-02).
- **Asynchronous callback over a message broker.** The Requestor does not
  block a thread. It registers a callback keyed by the Correlation
  Identifier and returns control to its own event loop immediately, invoking
  the callback later when the matching reply arrives. This is the shape used
  by non-blocking client libraries and is the only viable variant inside a
  single-threaded event loop runtime such as Node.js.
- **Shared reply queue versus per-request reply queue.** A Requestor can
  declare one durable or exclusive reply queue reused for every outstanding
  request, distinguishing replies purely by Correlation Identifier, which is
  the RabbitMQ tutorial's approach, or it can create a fresh, ephemeral reply
  destination per request and let the destination itself disambiguate,
  trading a small setup cost per call for a simpler matching story with no
  identifier bookkeeping at all.
- **Language-idiomatic future or promise wrapping.** In languages with
  first-class futures, promises, or async/await, the blocking-versus-callback
  distinction collapses into one idiom, the Requestor function returns a
  future immediately, and calling code either awaits it, which reads exactly
  like a blocking call, or attaches a continuation, which is the callback
  shape, without the library author needing to choose one variant over the
  other.
- **JSON-RPC style envelope over any transport.** Rather than relying on
  transport-native correlation, the payload itself carries an explicit `id`
  field the responder must echo. The JSON-RPC 2.0 specification says the
  identifier "MUST contain a String, Number, or NULL value if included" on
  the request, and on the response, "It MUST be the same as the value of the
  id member in the Request Object," calling it "the primary correlation
  tool" (https://www.jsonrpc.org/specification, verified 2026-08-02). This
  variant is useful precisely when the transport underneath, a WebSocket or
  a raw pub-sub channel, has no native request-response semantics at all.

## 9. Known production uses

- **HTTP as the substrate of the World Wide Web.** RFC 9110, the current IETF
  standard defining HTTP semantics, states the protocol's own nature in its
  overview. "HTTP is a stateless request/response protocol for exchanging
  'messages' across a connection" (RFC 9110 section 3.4,
  https://www.rfc-editor.org/rfc/rfc9110.html#name-overview, verified
  2026-08-02). Every browser, API client, and web server on the internet
  runs Request-Reply as its foundational interaction model.
- **gRPC unary RPC.** gRPC, the RPC framework originated at Google and now a
  Cloud Native Computing Foundation graduated project, documents its
  simplest call shape explicitly as Request-Reply, describing it as one where
  "the client sends a single request to the server and gets a single
  response back," equivalent to an ordinary function call
  (https://grpc.io/docs/what-is-grpc/core-concepts/, verified 2026-08-02).
- **RabbitMQ's official RPC tutorial.** RabbitMQ, the widely deployed
  open-source message broker, ships an official tutorial demonstrating
  Request-Reply built on top of AMQP messaging, using the `reply_to` and
  `correlation_id` message properties precisely as Return Address and
  Correlation Identifier, and describing the resulting design as one where
  "multiple servers can process requests from a single client queue, while
  minimizing network overhead through single round-trip communication"
  (https://www.rabbitmq.com/tutorials/tutorial-six-python, verified
  2026-08-02).
- **AWS Lambda synchronous invocation.** AWS's own Lambda documentation
  describes the synchronous invocation type as one where "Lambda runs the
  function and waits for a response. When the function completes, Lambda
  returns the response from the function's code"
  (https://docs.aws.amazon.com/lambda/latest/dg/invocation-sync.html,
  verified 2026-08-02), which is Request-Reply mediated by AWS's own
  invocation control plane rather than by application code managing a
  correlation identifier directly.
- **JSON-RPC 2.0 as used by the Language Server Protocol and the Model
  Context Protocol.** The JSON-RPC 2.0 specification's explicit id-based
  correlation mechanism, described as being "used to correlate the context
  between the two objects" (https://www.jsonrpc.org/specification, verified
  2026-08-02), is the wire-level Request-Reply implementation underlying
  both the Language Server Protocol, used by editors including Visual
  Studio Code to talk to language servers, and the Model Context Protocol
  used by AI coding assistants to call external tool servers; both build
  directly on JSON-RPC's request and response object shapes rather than
  inventing a new correlation scheme.

## 10. Consequences

Positive.

- The caller's logic reads linearly, get the answer, then act on it, which
  is easier to write and review than a workflow split across a request
  handler and a separate reply handler.
- Errors are visible at the call site. A failed or timed-out Request-Reply
  surfaces exactly where the caller asked for the answer, not somewhere
  downstream in an unrelated event handler.
- The pattern composes cleanly with existing transport-level tooling, load
  balancers, HTTP proxies, connection pools, and distributed tracing systems,
  all of which are built around the request-then-response shape.
- Over a direct connection the pattern needs no extra bookkeeping at all,
  the transport supplies correlation and return addressing for free.

Negative.

- The Requestor is temporally coupled to the Replier's availability and
  response time for the full duration of every call, and that coupling
  compounds across a call chain, a slow Replier three hops deep makes every
  caller above it slow.
- A broker-mediated implementation adds real operational surface, a reply
  queue that must be declared, monitored, and cleaned up, and a Correlation
  Identifier generation and matching scheme that is easy to get subtly wrong
  under high concurrency.
- Holding a thread, a connection, or a memory-resident future open while
  waiting for a reply is a real resource cost, and at scale, thousands of
  concurrent Request-Reply calls can exhaust a thread pool or a connection
  pool well before the responder itself becomes the bottleneck.
- The pattern gives no natural fan-out. A Requestor that needs the same
  answer acknowledged by many parties must issue many separate
  Request-Reply calls or step outside the pattern entirely, which is the
  reason event-driven publish-subscribe exists as a complementary, not
  competing, pattern.

## 11. Failure modes and misuse

- **Symptom.** Requests pile up and threads block indefinitely; the process
  eventually runs out of thread pool capacity and stops accepting new work.
  **Cause.** No timeout was set on the wait for a reply, so a Replier that
  never answers, whether crashed, deadlocked, or simply slow, holds the
  Requestor's thread forever. **Fix.** Every Request-Reply call carries an
  explicit, bounded timeout, and the caller has defined behaviour for the
  timeout case, not only an unhandled exception.
- **Symptom.** A reply arrives, but the caller applies it to the wrong
  in-flight operation, producing a result that is internally consistent but
  factually wrong, for example crediting the wrong account. **Cause.** A
  shared reply queue is in use, but the Correlation Identifier is reused,
  colliding, or dropped somewhere in the pipeline, so two outstanding
  requests' replies get swapped. **Fix.** Generate identifiers with
  collision-resistant randomness or a monotonic sequence scoped to the
  Requestor instance, never a value that could repeat while requests are
  still outstanding, and reject or log any reply whose identifier does not
  match a currently tracked outstanding request.
- **Symptom.** The system behaves correctly under light load and falls over
  under moderate concurrent traffic, with no single component showing high
  CPU. **Cause.** Every downstream call in a call chain is Request-Reply,
  and thread-per-request or connection-per-request resource exhaustion
  cascades upward, a classic cause of what is colloquially called a "retry
  storm" once timeout-triggered retries pile onto an already saturated
  Replier. **Fix.** Bound concurrency with a connection pool or a semaphore
  sized to the Replier's real capacity, and pair timeouts with a circuit
  breaker so retries stop feeding a Replier that has already fallen over.
- **Symptom.** A reply is processed twice, producing a duplicate side
  effect, a duplicate charge or a duplicate row in a database. **Cause.**
  The Requestor retried a request after a timeout that was actually a slow
  reply rather than a lost one, and the original reply eventually arrived
  and was processed alongside the retry's reply. **Fix.** Make the
  Requestor's reply handling idempotent keyed by Correlation Identifier, so
  a second reply for an identifier already resolved is discarded rather than
  reapplied, and make the Replier's own processing idempotent where the
  request itself could be delivered more than once.
- **Symptom.** A team that adopted event-driven architecture specifically to
  decouple services finds that a change in one service still routinely
  breaks or slows down an unrelated service. **Cause.** Request-Reply calls
  were layered on top of the event backbone at synchronous decision points
  without anyone noticing the temporal coupling this reintroduces, quietly
  eroding the isolation the architecture was chosen for. **Fix.** Audit
  cross-service calls for hidden Request-Reply usage and replace decision
  points that do not strictly need a live answer with an event plus a
  locally cached read model, per dimension 4's non-applicability guidance.

## 12. Trade-off matrix

| Force | Request-Reply | Publish-Subscribe (event, no reply) | Polling |
|---|---|---|---|
| Freshness of answer | Always current at call time | Eventually current, consumer-dependent lag | Current as of last poll interval |
| Caller-side coupling to responder availability | High, blocks or awaits directly | Low, publisher does not know or care who consumes | Low, poller tolerates a target being briefly down |
| Fan-out to many interested parties | Poor, one call per interested party | Native, any number of subscribers | Poor, one poller per interested party |
| Resource cost while waiting | A held thread, connection, or future per outstanding call | None, fire and forget | Periodic wasted calls even when nothing changed |
| Failure visibility to the caller | Immediate, at the call site | Delayed or absent, caller may never know a downstream step failed | Delayed by up to one poll interval |
| Suitability for long-running work | Poor without a timeout-and-resume redesign | Good, publish a completion event when ready | Good, but wastes resources when the interval is much shorter than the work |
| Implementation complexity, direct connection | Low, transport supplies correlation | Low to moderate, needs a broker and subscription management | Low, a scheduled call and a local cache |
| Implementation complexity, broker-mediated | Moderate, needs Return Address and Correlation Identifier discipline | Low relative to Request-Reply, no reply path to manage | Low |

## 13. Related and incompatible patterns

- **Return Address.** A strict sub-pattern of Request-Reply over any
  transport that does not implicitly supply a reply path. Every
  broker-mediated Request-Reply implementation contains a Return Address
  implementation inside it; the two are described separately in the
  literature only because Return Address is independently useful in
  one-way notification scenarios that still need an acknowledgment path.
- **Correlation Identifier.** The other strict sub-pattern, needed whenever
  a single reply channel can carry replies belonging to more than one
  outstanding request. On a direct connection this collapses into the
  connection itself and needs no explicit implementation; over a shared
  broker queue it is mandatory.
- **Message Endpoint.** Request-Reply's Requestor and Replier are each an
  instance of the more general Message Endpoint pattern, the component that
  connects an application to a messaging system; Request-Reply specialises
  Message Endpoint by requiring the endpoint pair to exchange exactly two
  correlated messages per interaction.
- **Competing Consumers.** Composes naturally on the Replier side of a
  broker-mediated Request-Reply, several Replier instances consume from the
  same request queue to scale throughput, each still replying individually
  to the Return Address and Correlation Identifier carried in whichever
  request it happened to pick up.
- **Saga.** Where a single logical business transaction spans several
  services, a naive implementation strings together several Request-Reply
  calls held open across the whole chain; Saga replaces that chain with a
  sequence of independently committed local transactions coordinated by
  events or an orchestrator, precisely to remove the temporal coupling a
  long chain of Request-Reply calls would otherwise impose. The two are not
  mutually exclusive, a Saga step frequently still uses Request-Reply for
  its own single, bounded call to one service, it simply refuses to hold
  that call open across the entire multi-step transaction.
- **Event-Driven Architecture, tight coupling variant.** Recorded in this
  entry's frontmatter as incompatible in the specific sense described in
  dimension 4, layering unbounded Request-Reply calls across boundaries an
  event-driven design deliberately decoupled reintroduces the coupling the
  architecture exists to remove. This is a design-discipline incompatibility,
  not a technical one, both patterns can and do coexist correctly at
  different boundaries within the same system.

## 14. Refactoring path in and out

Introducing Request-Reply into code that currently has none.

1. Identify the specific decision point where the caller currently guesses,
   uses a stale cached value, or is missing information it needs.
2. Define the request and reply message shapes as explicit types or schemas,
   not ad hoc dictionaries, so both sides agree on the contract independently
   of the transport.
3. Choose the transport. If caller and responder are already directly
   connected, a plain synchronous call or an HTTP/gRPC call is usually the
   right first move, correlation is free. If they communicate over an
   existing broker, add a Return Address field to the request payload and a
   Correlation Identifier, generated fresh per request.
4. Add an explicit, bounded timeout on the Requestor side before wiring
   anything else. A Request-Reply call with no timeout is not really this
   pattern, it is an accidental unbounded block waiting to happen.
5. Decide the failure behaviour up front, retry with backoff, surface an
   error to the caller's own caller, or fall back to a cached or default
   value, and implement it before the happy path ships, not after the first
   production timeout.
6. If the Replier side must scale, add Competing Consumers on the request
   channel once a single Replier instance becomes the bottleneck, verifying
   that reply routing by Correlation Identifier still works correctly with
   multiple concurrent Repliers.

Removing Request-Reply once it stops earning its place, most often because
step 4 of dimension 4's non-applicability list starts to bite as the system
grows.

1. Confirm the caller genuinely does not need the specific reply content to
   proceed correctly, only that the request was accepted; if it does still
   need the content, this refactor is not applicable and the correct next
   step is scaling the Replier, not removing the pattern.
2. Convert the Replier's response into a published event instead of a direct
   reply, carrying the same information the reply used to carry.
3. Convert the Requestor from a blocking or awaiting call into a
   fire-and-forget publish, plus a subscription to the new event for any
   code path that still needs to react to the eventual outcome.
4. Remove the Correlation Identifier and Return Address plumbing only after
   confirming no remaining code path depends on synchronous correlation; a
   partial removal that leaves dead correlation bookkeeping in place is a
   common source of confusion during later maintenance.
5. Add a read model or local cache if downstream code previously relied on
   the reply's freshness guarantee, so removing the synchronous call does not
   silently introduce stale-data bugs where none previously existed.

## 15. Testing and verification

Request-Reply makes the happy path trivially easy to test, a straightforward
call-and-assert against a mock or a stub Replier, but it makes the failure
paths the part that actually needs deliberate coverage.

- **Test the timeout path explicitly**, not only the success path. Use a
  test double for the Replier that never answers, or answers after a delay
  longer than the configured timeout, and assert the Requestor surfaces the
  correct timeout error rather than hanging the test suite itself.
- **Test correlation under concurrency.** Fire several requests
  concurrently against a test double that deliberately replies out of
  order, and assert each caller receives the reply matching its own
  request, not simply the next reply that happened to arrive. This is the
  test that catches Correlation Identifier bugs that a single-request test
  never exercises.
- **Test idempotent reply handling.** Deliver the same reply twice to the
  Requestor's handling code and assert the second delivery is a no-op, per
  the duplicate-processing failure mode in dimension 11.
- **Contract test the request and reply schemas independently of the
  transport.** Because the message shapes are the actual interface between
  Requestor and Replier, a schema-level contract test, run against both
  sides in continuous integration, catches a shape mismatch before it
  reaches a live environment, which is cheaper than debugging a live
  timeout that turns out to be a silently rejected malformed request.
- **For a broker-mediated implementation, use the broker's own test tooling
  or an in-memory fake**, rather than a live broker, for unit-level tests,
  reserving a real broker for a smaller number of integration tests that
  specifically verify the reply-queue declaration and cleanup lifecycle.
- **Test double consideration.** A mock that simply returns a canned reply
  synchronously verifies the caller's happy-path logic but proves nothing
  about correlation or timeout handling; a fake that models real
  asynchronous, possibly out-of-order delivery is the one that actually
  exercises this pattern's distinguishing behaviour.

## 16. Observability signals

- **Round-trip latency per Requestor-Replier pair, not only an aggregate.**
  A percentile histogram (p50, p95, p99) of the time between request sent
  and reply received, tagged by which Replier instance actually answered
  when Competing Consumers is in play, is the single most useful signal;
  a healthy instance shows a tight, stable distribution, a failing one
  shows a growing tail or a bimodal distribution as some requests silently
  degrade to the timeout path.
- **Outstanding request count.** The number of requests a Requestor has sent
  and is still waiting on a reply for, sampled continuously. A healthy
  system shows this hovering near zero or a small, stable number; a growing,
  unbounded count is the earliest visible sign of the resource-exhaustion
  failure mode described in dimension 11, well before thread pools or
  connection pools actually saturate.
- **Timeout rate as a distinct counter from error rate.** Timeouts and
  explicit application-level errors have different root causes, a rising
  timeout rate with a flat error rate points at Replier slowness or network
  degradation, while a rising error rate with flat timeouts points at the
  Replier actively rejecting requests.
- **Correlation mismatch or orphaned-reply counter.** Any reply that arrives
  with a Correlation Identifier the Requestor is not currently tracking
  should be counted, not silently dropped; a nonzero rate here indicates
  either a bug in identifier generation, a Requestor restart that lost
  in-memory tracking state while replies were still in flight, or a
  duplicate-delivery scenario from the broker.
- **Reply-queue depth**, for a broker-mediated implementation, watched
  independently of request-queue depth; a growing reply-queue depth with a
  stable request rate means Requestors are falling behind consuming their
  own replies, which is a Requestor-side problem distinct from Replier
  overload.
- **Distributed trace propagation across the request and reply legs.** A
  trace ID threaded through both the request and the reply, alongside the
  Correlation Identifier, lets an operator follow one logical call across
  service boundaries in a tracing tool, which is the practical, deployable
  version of the sequence diagrams in dimension 7.

## 17. Security and privacy implications

- **Reply-channel spoofing over a broker.** Because the Return Address is
  carried as data inside the request message rather than being a built-in
  transport property, a broker with permissive access control lets any
  publisher claim an arbitrary reply destination; a malicious or
  misconfigured client could direct a Replier to publish sensitive reply
  content to a destination it does not own. Restrict which principals may
  declare or bind reply queues, and where the broker supports it, scope
  reply-queue permissions to the Requestor's own connection or identity.
- **Correlation Identifier as an information leak, not a secret, but still
  worth minimising.** A Correlation Identifier is a coordination value, not
  an access-control token, and it should never be treated as one; a Replier
  that trusts a Correlation Identifier as authorization for anything beyond
  matching a reply to a request has confused two unrelated concerns. Prefer
  a value with no predictable structure, an incrementing counter can leak
  the Requestor's request volume to anyone who can observe the channel.
- **Amplification via unbounded retries.** A Requestor that retries
  aggressively on timeout, without backoff or a cap, can itself become a
  denial-of-service vector against its own Replier during a partial outage,
  the exact retry-storm failure mode in dimension 11 has a security
  dimension whenever the Replier is a shared, multi-tenant service.
- **Data exposure in transit for the reply leg specifically.** It is common
  to secure the request leg carefully, an authenticated API call, while
  overlooking that the reply leg, especially over a broker where the reply
  is one more ordinary message on a queue, carries the same or greater
  sensitivity, an authorization decision or account data. Both legs need
  the same transport encryption and access-control rigor; treating the
  reply as an internal, implicitly trusted detail is a common oversight.
- **Timeout as a resource-exhaustion attack surface.** An attacker who can
  induce a Requestor to issue Request-Reply calls against a slow or
  unresponsive Replier, directly or indirectly, can tie up the Requestor's
  thread or connection pool cheaply; this is one specific instance of a
  broader denial-of-service pattern and is mitigated by the same bounded
  concurrency and circuit-breaker controls named in dimension 11's fixes,
  not by anything specific to Request-Reply beyond recognising that the
  pattern's own resource-holding behaviour is the exploitable surface.

## 18. References

- Gregor Hohpe, Bobby Woolf, *Enterprise Integration Patterns. Designing,
  Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003,
  Messaging Patterns chapter, Request-Reply, Return Address, Correlation
  Identifier.
- Enterprise Integration Patterns, "Request-Reply,"
  https://www.enterpriseintegrationpatterns.com/patterns/messaging/RequestReply.html,
  verified 2026-08-02.
- Andrew D. Birrell, Bruce Jay Nelson, "Implementing Remote Procedure Calls,"
  ACM Transactions on Computer Systems, volume 2, issue 1, 1984.
- IETF, RFC 9110, "HTTP Semantics," section 3.4, Messages,
  https://www.rfc-editor.org/rfc/rfc9110.html#name-overview, verified
  2026-08-02.
- gRPC Authors, "Core concepts, architecture and lifecycle,"
  https://grpc.io/docs/what-is-grpc/core-concepts/, verified 2026-08-02.
- RabbitMQ, "RabbitMQ tutorial 6, RPC (Python),"
  https://www.rabbitmq.com/tutorials/tutorial-six-python, verified
  2026-08-02.
- Amazon Web Services, "Invoke a Lambda function synchronously,"
  https://docs.aws.amazon.com/lambda/latest/dg/invocation-sync.html,
  verified 2026-08-02.
- JSON-RPC Working Group, "JSON-RPC 2.0 Specification,"
  https://www.jsonrpc.org/specification, verified 2026-08-02.

## Code examples

### TypeScript, direct HTTP-style Request-Reply with Correlation Identifier and timeout

```typescript
type RRRequest = { id: string; payload: unknown };
type RRReply = { id: string; result?: unknown; error?: string };

class Requestor {
  private pending = new Map<string, (r: RRReply) => void>();

  constructor(private send: (req: RRRequest) => void) {}

  onReply(reply: RRReply): void {
    const resolve = this.pending.get(reply.id);
    if (!resolve) return;
    this.pending.delete(reply.id);
    resolve(reply);
  }

  async call(payload: unknown, timeoutMs: number): Promise<RRReply> {
    const id = crypto.randomUUID();
    const req: RRRequest = { id, payload };
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`timeout waiting for reply ${id}`));
      }, timeoutMs);
      this.pending.set(id, (reply) => {
        clearTimeout(timer);
        resolve(reply);
      });
      this.send(req);
    });
  }
}

class Replier {
  constructor(private handle: (payload: unknown) => unknown) {}

  receive(req: RRRequest): RRReply {
    try {
      const result = this.handle(req.payload);
      return { id: req.id, result };
    } catch (e) {
      return { id: req.id, error: (e as Error).message };
    }
  }
}

const replier = new Replier((p) => ({ doubled: (p as { n: number }).n * 2 }));
let inFlight: Requestor;
const requestor = new Requestor((req) => {
  const reply = replier.receive(req);
  setTimeout(() => inFlight.onReply(reply), 5);
});
inFlight = requestor;

requestor.call({ n: 21 }, 1000).then((r) => console.log(r));
```

### Python, broker-mediated Request-Reply modelling reply_to and correlation_id

```python
import queue
import threading
import time
import uuid


class Broker:
    def __init__(self):
        self.queues = {}

    def declare_queue(self, name):
        self.queues.setdefault(name, queue.Queue())
        return self.queues[name]

    def publish(self, queue_name, message):
        self.declare_queue(queue_name).put(message)


class Requestor:
    def __init__(self, broker, request_queue):
        self.broker = broker
        self.request_queue = request_queue
        self.reply_queue_name = f"reply.{uuid.uuid4()}"
        self.reply_queue = broker.declare_queue(self.reply_queue_name)

    def call(self, payload, timeout_s=2.0):
        correlation_id = str(uuid.uuid4())
        message = {
            "correlation_id": correlation_id,
            "reply_to": self.reply_queue_name,
            "payload": payload,
        }
        self.broker.publish(self.request_queue, message)
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            remaining = deadline - time.monotonic()
            try:
                reply = self.reply_queue.get(timeout=max(remaining, 0))
            except queue.Empty:
                break
            if reply.get("correlation_id") == correlation_id:
                return reply
        raise TimeoutError(f"no reply for {correlation_id}")


class Replier:
    def __init__(self, broker, request_queue, handler):
        self.broker = broker
        self.request_queue = broker.declare_queue(request_queue)
        self.handler = handler

    def run_once(self):
        req = self.request_queue.get(timeout=1)
        result = self.handler(req["payload"])
        self.broker.publish(
            req["reply_to"],
            {"correlation_id": req["correlation_id"], "result": result},
        )


if __name__ == "__main__":
    broker = Broker()
    replier = Replier(broker, "rpc.requests", lambda p: p["n"] * 2)
    threading.Thread(target=replier.run_once, daemon=True).start()
    requestor = Requestor(broker, "rpc.requests")
    reply = requestor.call({"n": 21})
    print(reply)
```

### Go, direct synchronous Request-Reply over an in-process channel pair

```go
package main

import (
	"errors"
	"fmt"
	"time"
)

type Request struct {
	ID      string
	Payload int
	ReplyTo chan Reply
}

type Reply struct {
	ID     string
	Result int
}

func replier(requests <-chan Request) {
	for req := range requests {
		req.ReplyTo <- Reply{ID: req.ID, Result: req.Payload * 2}
	}
}

func call(requests chan<- Request, payload int, timeout time.Duration) (Reply, error) {
	replyTo := make(chan Reply, 1)
	req := Request{ID: "req-1", Payload: payload, ReplyTo: replyTo}
	requests <- req

	select {
	case reply := <-replyTo:
		return reply, nil
	case <-time.After(timeout):
		return Reply{}, errors.New("timeout waiting for reply")
	}
}

func main() {
	requests := make(chan Request)
	go replier(requests)

	reply, err := call(requests, 21, time.Second)
	if err != nil {
		fmt.Println("error:", err)
		return
	}
	fmt.Printf("reply id=%s result=%d\n", reply.ID, reply.Result)
}
```

I compiled and ran the Go example with `go run`, the TypeScript example against
`node` after transpiling with `npx tsc`, and the Python example with
`python3`. All three produced the expected doubled result with no errors.
