---
name: Correlation Identifier
slug: correlation-identifier
family: 07-integration
category: Integration
aliases: [Correlation ID, Correlation Token, Request ID Echo]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [request-reply, return-address, message, aggregator, event-message]
incompatible_with: []
verified: 2026-08-02
---

# Correlation Identifier

## 1. Name, aliases, and lineage

The canonical name is Correlation Identifier. It is documented as one of the
Message Construction patterns in Gregor Hohpe and Bobby Woolf, *Enterprise
Integration Patterns. Designing, Building, and Deploying Messaging Solutions*,
Addison-Wesley, 2003, in the chapter on Messaging Systems, and it is also
published on the companion site as its own page. The site states the problem
this way. "How does a requestor that has received a reply know which request
this is the reply for?" and gives the solution in one sentence. "Each reply
message should contain a Correlation Identifier, a unique identifier that
indicates which request message this reply is for"
(https://www.enterpriseintegrationpatterns.com/patterns/messaging/CorrelationIdentifier.html,
verified 2026-08-02).

In day-to-day engineering conversation the pattern is called by three
interchangeable names depending on the community. Message-queue engineers,
following the book, say Correlation Identifier. Web and HTTP-API engineers say
Correlation ID or Correlation Token, most often referring to a header such as
`X-Correlation-ID` that a gateway stamps on an inbound request and every
downstream call echoes. Distributed-tracing engineers use the closely related
but not identical term trace ID, defined by the W3C Trace Context
specification as "the ID of the whole trace forest," used "to uniquely
identify a distributed trace through a system" (https://www.w3.org/TR/trace-context/,
verified 2026-08-02). A trace ID and a correlation identifier solve the same
underlying problem, matching scattered events back to one logical operation,
but a trace ID is standardized, propagated automatically by tracing
middleware, and typically carries no business meaning, while a correlation
identifier is usually chosen and threaded by the application itself and often
does carry meaning, such as an order number reused as its own correlation key.
The distinction matters for dimension 13 below.

The name Request ID Echo is not a name from any catalog. It is used here only
to describe the mechanical action at the center of the pattern, so a reader
who has not memorized the formal name still recognizes the technique on sight,
copy the identifier of the thing you are answering into the answer you send
back.

## 2. Problem and context

A process sends a message and does not receive its answer over the same
connection it used to send it. This happens whenever the transport is
asynchronous, one-way, or fanned out, over a message queue, a pub-sub topic, a
webhook callback, an event stream, or a batch of parallel outbound HTTP calls
whose responses arrive out of order on shared infrastructure such as a
connection pool or an event loop. Under a synchronous call, the runtime stack
itself remembers which call is waiting for which answer, because the answer
comes back on the same call frame that sent the request. Once the send and the
receive are decoupled, that bookkeeping disappears, and the receiving side
faces a genuinely hard question with an incoming pile of replies and no shared
call stack to consult, which of my outstanding requests does this particular
reply belong to.

The concrete situation looks like this in a real system. A service places an
order, publishes an `OrderPlaced` event onto a topic, and continues doing
other work. Minutes later a `PaymentAuthorized` event arrives on a different
topic, produced by a different service that never saw the original order
object. Nothing about the payload of `PaymentAuthorized` on its own says which
order it authorizes, unless the payment service was handed something from the
order and told to carry it forward unchanged into its own output. The same
shape recurs for a request-reply exchange over a queue, where a requestor
places several requests on an outbound queue before any reply has come back,
and the replies land on a shared inbound queue in whatever order the replier
happens to finish them, which is rarely the order they were sent. It recurs
again for a fan-out over HTTP, where one caller issues ten concurrent requests
to ten remote services and the responses complete on ten different threads at
ten different times.

The pattern belongs specifically in this context, two or more messages that
are logically related, produced or consumed at different points in time, by
parties that do not share a synchronous call stack, transaction, or memory
space, where the relationship between them has to be reconstructed from the
messages themselves. Outside that context, when a call is genuinely
synchronous and its answer arrives on the same stack frame that issued it,
correlation is already free and adding an explicit identifier is ceremony with
no payoff.

## 3. Forces

Coupling versus statelessness. The lightest possible correlation scheme is for
the requestor to keep no state at all and let the identifier itself carry
everything needed to resume, for example encoding a callback URL or a
resumable cursor inside the identifier. The heaviest is a fully stateful
requestor that maintains a table mapping outstanding correlation identifiers
to pending continuations, timers, and partial results, which is more capable
but couples the requestor to the lifetime of every request it has sent. The
pattern does not decide which one to use, it only supplies the key the two
sides agree to compare.

Uniqueness guarantee versus generation cost. A correlation identifier only
does its job if it is, in practice, unique among every outstanding request the
receiving side could plausibly confuse it with. A monotonically increasing
integer scoped to one process is cheap to generate and trivially unique inside
that process, but breaks the moment two processes both start counting from
one. A UUID version 4 is unique across any number of independent processes
with no coordination and negligible collision probability, at the cost of 128
bits and a small amount of entropy-generation work per message. Systems that
already have a natural business key, an order number, an account number, a
device serial, frequently reuse that key as the correlation identifier
instead of minting a new one, trading a slightly weaker uniqueness guarantee,
the business key must genuinely be unique in the relevant time window, for
zero extra allocation and, more valuably, for a correlation identifier a
human operator can recognize on sight in a log line.

Propagation discipline versus flexibility. The pattern only works if every
intermediary between the original sender and the eventual replier copies the
identifier forward unchanged rather than regenerating, transforming, or
dropping it. This is a discipline that has to be enforced across every hop,
including hops nobody who designed the correlation scheme controls, such as a
third-party message broker, a serverless function platform that may
re-package the payload, or a legacy adapter that only understands a fixed
schema with no room for an extra field. A rigid, mandatory field in every
message envelope makes propagation reliable but demands that every producer
and consumer, including old ones, be updated to carry it. A convention-based
approach, stash it in a free-form metadata bag if one exists, is flexible and
incrementally adoptable but silently loses the identifier the first time a
component strips unknown metadata.

Correlation identifier versus return address. A correlation identifier only
tells the receiver which request a reply matches. It says nothing about where
to send that reply. In many systems the two travel together, in others they
are deliberately separated because the reply channel and the identity of the
requestor are matters of routing while the match-up between request and
answer is a matter of bookkeeping, and conflating the two forces every
receiver to also become a router. Hohpe and Woolf treat this as a related but
distinct pattern, Return Address, in the same chapter, and the two are
frequently implemented as a pair, a Return Address says where, a Correlation
Identifier says which one.

## 4. Applicability and non-applicability

Reach for Correlation Identifier when the situation matches one of these.

- Requests and their replies travel over an asynchronous, one-way, or
  fanned-out channel, so no shared call stack links a send to its receive.
- More than one request from the same requestor, or from the same logical
  workflow, can be outstanding at the same time on the same channel.
- Replies can arrive out of order relative to the order the requests were
  sent, whether because of parallel processing, retries, or variable
  processing time on the replying side.
- Several downstream services each emit independent events about the same
  originating business operation, and something downstream needs to
  reassemble those events, which is the exact situation the Aggregator
  pattern solves using a correlation identifier as its grouping key. Apache
  Camel's Aggregator EIP documentation says the logic for combining messages
  together is "correlated in buckets based on a correlation key. Messages
  with the same correlation key are aggregated together," and its
  `correlationExpression` parameter is mandatory, described as "the
  expression used to calculate the correlation key to use for aggregation"
  (https://camel.apache.org/components/next/eips/aggregate-eip.html, verified
  2026-08-02).
- A long-running operation is polled for status by a separate call than the
  one that started it, so the poll needs a stable identifier to look up
  against. The Azure Architecture Center's Asynchronous Request-Reply pattern
  builds exactly this shape. The accepting function "generates a request ID
  and adds it as metadata to the queue message," then embeds that same
  identifier in the URL of the status endpoint returned to the caller
  (https://learn.microsoft.com/en-us/azure/architecture/patterns/async-request-reply,
  verified 2026-08-02).

Do not reach for Correlation Identifier when the situation matches one of these.

- The exchange is a genuinely synchronous call whose response returns on the
  same stack frame or the same HTTP connection that issued the request. The
  language runtime, the socket, or the promise object already performs the
  correlation for free, and adding a manual identifier duplicates a
  mechanism that already exists and cannot be made more correct by hand.
- Only one request can ever be outstanding at a time on a given channel, for
  example a single strictly sequential request-then-wait loop where the next
  request is never sent until the previous reply has been consumed. There is
  nothing to disambiguate, because there is never more than one candidate
  match.
- The messages in question do not need to be matched back to anything, they
  are pure fire-and-forget notifications where no reply, no downstream
  aggregation, and no later lookup will ever occur. Attaching a correlation
  identifier to a message nothing will ever correlate against is dead weight.
- Full distributed tracing across the whole call graph is what is actually
  needed, not just matching one request to one reply. A dedicated trace
  context, per the W3C Trace Context specification, is a better fit than
  hand-rolling a correlation scheme, because it standardizes propagation
  across every hop, vendor, and language, which an ad hoc business-level
  correlation identifier does not attempt to do, and dimension 13 expands on
  this.
- The correlation would need to survive across an untrusted boundary where
  the identifier itself must not leak information, because a naively chosen
  correlation identifier, a sequential integer or a business key, can leak
  volume, ordering, or identity information to a party who should not have
  it. Dimension 17 covers this in depth.

## 5. Structure

- **Requestor.** The party that originates the first message in a related
  pair or group. It is responsible for either generating the correlation
  identifier itself before sending, or for recognizing and remembering an
  identifier the receiving side assigns during acknowledgment, and for
  retaining a lookup table, timer, or continuation keyed by that identifier
  so that when a reply eventually arrives it can be matched to the pending
  work that is waiting for it.
- **Correlation identifier.** A value, most commonly a string, carried as a
  distinct field in the message envelope or as metadata rather than buried
  inside the business payload, whose sole job is to be compared for equality.
  It must be unique enough, in the scope where it will be compared, that two
  genuinely different logical exchanges never collide on the same value.
- **Replier.** The party that receives the original message and eventually
  produces one or more responses to it. It is responsible for copying the
  correlation identifier from the inbound message into every outbound message
  that answers it, unchanged, rather than generating a fresh identifier or
  discarding the original one.
- **Correlating consumer.** The party, often but not always the same process
  as the requestor, that reads incoming messages off a shared or fanned-in
  channel and dispatches each one to the correct pending operation by looking
  up its correlation identifier. In an aggregation scenario this role belongs
  to an Aggregator, which groups messages that share a correlation key into
  one composite result rather than matching a single request to a single
  reply.
- **Correlation store.** The data structure, in-memory map, database table, or
  distributed cache, that the correlating consumer consults to translate a
  correlation identifier back into the pending work it belongs to. For a
  short-lived in-process exchange this can be a hash map. For a long-running
  workflow that must survive a process restart, it has to be durable.

## 6. ASCII structure diagram

```
+-----------------------------------+
| Requestor                         |
| generates correlation id "abc123" |
| stores "abc123" -> pending op     |
+-----------------------------------+
     | 1. request msg, header correlationId=abc123
     v
+----------------------------------------------------+
| Replier                                            |
| receives request, reads correlationId from headers |
| copies same correlationId into reply headers,      |
| unchanged                                          |
+----------------------------------------------------+
     | 2. reply msg, header correlationId=abc123
     v
Requestor looks up "abc123" in its pending ops table,
finds the waiting operation.

Fan-in view, several outstanding requests on one shared
inbound channel. Order of arrival is irrelevant. Order
of dispatch is by id, not by time.

  Requestor sends            Shared channel receives,
                             any order

  req(id=A) --.              .--- reply(id=B)
  req(id=B) --+-[ async  ]--+---- reply(id=D)
  req(id=C) --+-[transport]--+---- reply(id=A)
  req(id=D) --'              '---- reply(id=C)

  Correlating consumer
    lookup(B) -> resumes op B
    lookup(D) -> resumes op D
    lookup(A) -> resumes op A
    lookup(C) -> resumes op C
```

## 7. Dynamics

```
Requestor              Message channel            Replier
   |                        |                         |
   | generate id="abc123"   |                         |
   | store pending[abc123]  |                         |
   |----- send req(abc123) ------------------------->  |
   |                        |                         | read req
   |                        |                         | correlationId = abc123
   |                        |                         | process request
   |                        |                         | build reply
   |                        |                         | reply.correlationId = abc123
   |  <----- reply(abc123) ---------------------------|
   | receive reply           |                         |
   | id = reply.correlationId|                         |
   | lookup pending[id]      |                         |
   | found -> resume waiting |                         |
   | op, remove from pending |                         |
   |                        |                         |

Timeout branch, no reply arrives inside a deadline

   | start_timer(abc123, T) |                         |
   |    ... T elapses ...   |                         |
   | timer fires for abc123 |                         |
   | lookup pending[abc123] |                         |
   | still present -> treat as failed/timed out        |
   | remove pending[abc123] |                         |
   | (a late reply that arrives afterward finds no      |
   |  entry in pending[] and is discarded or logged     |
   |  as an orphan reply, see dimension 11)             |
```

## 8. Implementation variants

- **Header-carried identifier, application-generated.** The requestor
  generates a UUID or ULID before sending and places it in a dedicated
  message header or property, such as JMS `JMSCorrelationID`, an AMQP
  `correlation-id` application property, or an HTTP `X-Correlation-ID`
  header. Azure Service Bus documents its own `CorrelationId` broker property
  as one that "enables an application to specify a context for the message
  for the purposes of correlation, for example reflecting the MessageId of a
  message that's being replied to"
  (https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-messages-payloads,
  verified 2026-08-02). This is the most common variant because most message
  brokers reserve a first-class header slot for it, keeping the identifier
  out of the business payload.
- **MessageId echo.** Rather than generating a fresh identifier, the replier
  reuses the request's own message identifier as the reply's correlation
  identifier. Azure Service Bus documents this exact pattern for simple
  request-reply, noting that when the consumer responds, "it copies the
  MessageId of the handled message into the CorrelationId property of the
  reply message"
  (https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-messages-payloads,
  verified 2026-08-02). This variant needs no extra field to be minted at all,
  it reuses infrastructure, at the cost of tying the correlation identifier's
  format to whatever the broker's message identifier format happens to be.
- **Business key as correlation identifier.** The correlation identifier is
  not a synthetic value at all but an existing, already-unique business key,
  an order number, a shipment tracking number, an account ID. This is the
  variant with the lowest ceremony, because nothing new has to be generated,
  and it has the operational advantage that a human reading a log line
  immediately recognizes what the identifier refers to, unlike an opaque
  UUID. It is only safe when the business key is genuinely unique within the
  window where correlation can occur, and it can leak information, discussed
  in dimension 17.
- **Correlation-set expression, used by an Aggregator.** Instead of a single
  scalar field, the correlation key is computed by evaluating an expression
  against each incoming message, which is how Camel's Aggregator EIP works,
  taking a mandatory `correlationExpression` that is evaluated per message to
  produce the bucket key
  (https://camel.apache.org/components/next/eips/aggregate-eip.html, verified
  2026-08-02). This variant generalizes correlation from matching a bare
  field to matching a computed value, which is necessary when the natural
  correlating value is not stored verbatim in every message but has to be
  derived, for example the first eight characters of an order number plus a
  region code.
- **URL-embedded polling identifier.** For an asynchronous HTTP workflow, the
  correlation identifier is embedded directly in the URL of a status endpoint
  the client is told to poll, rather than in a header the client must
  remember to resend. The Azure sample cited above builds the status URL as
  `https://{host}/api/RequestStatus/{requestId}` and stores that same
  `requestId` as message metadata on the queued work item
  (https://learn.microsoft.com/en-us/azure/architecture/patterns/async-request-reply,
  verified 2026-08-02), so the correlation identifier and the return address
  are fused into one URL rather than kept as two separate fields.
- **Distributed trace ID, adjacent but distinct.** The W3C Trace Context
  `traceparent` header carries a `trace-id` generated once at the root of a
  call graph and propagated, unmodified, by every hop's tracing middleware,
  "used to uniquely identify a distributed trace through a system"
  (https://www.w3.org/TR/trace-context/, verified 2026-08-02). Some systems
  deliberately reuse the trace ID as their application-level correlation
  identifier, which avoids maintaining two parallel identifiers, at the cost
  of coupling business correlation to the lifecycle and cardinality rules of
  the tracing system, discussed further in dimension 13.

## 9. Known production uses

- **Apache Camel's Aggregator EIP** requires a `correlationExpression` on
  every aggregation route and groups exchanges into buckets by the value that
  expression produces, explicitly describing the mechanism as correlating
  messages "in buckets based on a correlation key"
  (https://camel.apache.org/components/next/eips/aggregate-eip.html, verified
  2026-08-02).
- **Azure Service Bus** ships `CorrelationId` as one of its predefined broker
  properties on every message, and its documentation walks through the
  simple request-reply pattern by name, describing how the consumer "copies
  the MessageId of the handled message into the CorrelationId property of
  the reply message"
  (https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-messages-payloads,
  verified 2026-08-02).
- **Azure's reference implementation of the Asynchronous Request-Reply
  pattern**, published on the Azure Architecture Center and backed by a
  runnable sample on GitHub, generates a `requestId`, attaches it to the
  queued Service Bus message as the `RequestGUID` application property, and
  embeds the same identifier in the status-polling URL it hands back to the
  caller, with the worker function reading `message.ApplicationProperties["RequestGUID"]`
  back out when it writes the result
  (https://learn.microsoft.com/en-us/azure/architecture/patterns/async-request-reply,
  verified 2026-08-02).
- **The W3C Trace Context specification**, a W3C Recommendation implemented
  across essentially every major distributed tracing system including
  OpenTelemetry, standardizes a `trace-id` field precisely so independently
  operated services can correlate the pieces of one logical operation without
  agreeing on a proprietary correlation scheme beforehand
  (https://www.w3.org/TR/trace-context/, verified 2026-08-02).
- **The Enterprise Integration Patterns catalog itself**, the originating
  source of the pattern's name and canonical description, documents
  Correlation Identifier as a standard, load-bearing pattern in
  request-reply messaging architectures rather than as a niche technique,
  placing it in its Message Construction category alongside Return Address
  and Message Sequence
  (https://www.enterpriseintegrationpatterns.com/patterns/messaging/CorrelationIdentifier.html,
  verified 2026-08-02).

## 10. Consequences

Positive.

- Decouples the timing of a reply from the timing of its request. A
  requestor can send many requests before receiving any replies, and
  replies can arrive in whatever order the replying side happens to finish
  them, without either side needing to reason about ordering.
- Makes fan-out and fan-in trivially safe. A requestor can issue N concurrent
  requests over a shared channel and correctly reassemble N replies, because
  each carries its own unmatched-to-anything-else identifier.
- Enables idempotent, stateless intermediaries. A broker, a load balancer, or
  a proxy sitting between requestor and replier does not need to track which
  request maps to which reply, because the endpoints carry that information
  in the message itself.
- Turns log correlation from guesswork into a grep. When every log line for
  an operation carries the same correlation identifier, an operator can
  reconstruct the full path a single logical operation took across many
  services with one search, which is the practical payoff most engineers
  actually experience day to day.
- Composes cleanly with Aggregator, Return Address, and dead-letter handling,
  because all three need exactly the same field to do their own jobs.

Negative.

- The correlation identifier is one more piece of state the requestor must
  keep, remember to clean up, and eventually time out. An unbounded pending
  table is a memory leak with a very specific, very common shape, one entry
  per request that never got its reply.
- Correlation only works if propagation is disciplined across every hop. A
  single intermediary that regenerates, drops, or truncates the identifier
  silently breaks correlation for every message that passes through it,
  and the failure usually surfaces far downstream as an unrelated-looking
  bug, an orphan reply, or a stuck timeout, not as an obvious error at the
  point where the identifier was lost.
- Reusing a predictable value, a sequential integer or an easily-guessable
  business key, as the correlation identifier can leak operational
  information, order volume, session count, or user identity, to any party
  positioned to observe the traffic, discussed further in dimension 17.
- It adds a field, and therefore a small amount of payload size and
  serialization cost, to every single message in the system, even the vast
  majority of messages that will never actually need it, which matters at
  sufficiently high message volume.
- It is easy to reach for a correlation identifier as a substitute for
  proper distributed tracing, producing a partial, hand-rolled tracing
  system that answers which reply matches which request but not what the
  whole call graph looked like, a question a standardized trace context
  answers by design.

## 11. Failure modes and misuse

- **Symptom.** Replies pile up in a dead-letter or unroutable-message queue,
  and nobody can explain why. **Cause.** An intermediary hop, commonly a
  message translator, an adapter to a legacy system with a fixed schema, or a
  serialization layer that drops unknown fields, strips or overwrites the
  correlation identifier in transit, so the receiving side can no longer find
  a matching pending request. **Fix.** Make the correlation field a mandatory,
  first-class part of the message envelope or protocol header rather than an
  optional metadata entry that a strict schema or a lossy adapter is free to
  discard, and add a contract test that asserts the identifier survives every
  hop end to end.

- **Symptom.** The requestor's memory usage grows steadily over time under
  normal load, with no obvious leak in application code. **Cause.** The
  correlation store, the pending-operations table keyed by correlation
  identifier, has no expiry policy, so every request whose reply never
  arrives, because of a crash on the replier's side, a dropped message, or a
  network partition, leaves a permanent entry. **Fix.** Attach a timeout to
  every pending correlation entry, and evict entries whose deadline has
  passed regardless of whether a matching reply ever shows up, logging the
  eviction as a timeout so it is distinguishable from a normal completion.

- **Symptom.** A reply arrives for a correlation identifier the requestor has
  no record of, and the process either crashes on a missing-key lookup or
  silently swallows the reply with no log entry. **Cause.** The requestor
  already evicted the entry, most often because its own timeout fired first
  and the reply was simply late, or, more rarely, because the identifier
  collided with a stale or reused value from an earlier, already-completed
  exchange. **Fix.** Treat a lookup miss as an expected, named case rather
  than an error, log it as an orphan reply with the identifier and, if
  available, a timestamp of when the corresponding request was originally
  sent, and if orphan-reply volume is meaningfully nonzero, widen the timeout
  or investigate why replies are consistently arriving after it.

- **Symptom.** Two logically unrelated operations occasionally get their
  results swapped, producing silent data corruption rather than a visible
  error. **Cause.** The correlation identifier is not actually unique in the
  scope where it is compared, most commonly because a low-cardinality
  business key or a per-process sequential counter was reused across two
  processes, or because a counter wrapped around after enough requests.
  **Fix.** Switch to a generation scheme with a strong uniqueness guarantee
  across the actual scope of comparison, a UUID version 4 or a ULID, or, if
  a business key must be kept for readability, compose it with a
  process-unique or time-based suffix so the combined value is unique in
  every scope it is ever compared within.

- **Symptom.** An aggregation step produces incomplete or wrongly grouped
  results, combining messages that should have stayed separate or failing to
  combine ones that should have been grouped together. **Cause.** The
  correlation expression used by the Aggregator is evaluated inconsistently
  across the messages that are supposed to belong together, for example
  because one producer serializes the correlating field as a string and
  another as a number, or because the expression depends on a field whose
  value can legitimately change partway through the sequence of messages
  being aggregated. **Fix.** Pin the correlation expression to a field that is
  guaranteed immutable and identically typed and formatted across every
  producer that emits into the aggregation, and add a test that feeds the
  aggregator messages from every real producer, not only from one reference
  implementation.

## 12. Trade-off matrix

| Force | Correlation Identifier | Synchronous request-response | W3C Trace Context, trace-id |
|---|---|---|---|
| Works over asynchronous, one-way, or fanned-out channels | Yes, this is its purpose | No, requires a live call stack or connection | Yes, purpose-built for this |
| Correlates one request to its one reply | Yes, directly | Yes, for free, via the call stack | Indirectly, via span relationships, not a direct match |
| Correlates many related events across many services into one logical operation | Only if paired with an Aggregator | No, out of scope | Yes, this is its core design goal |
| Standardized wire format across vendors | No, application-defined | Not applicable | Yes, W3C Recommendation |
| Requires the requestor to keep pending-request state | Yes | No, the runtime call stack is the state | Yes, but usually handled by tracing middleware, not application code |
| Adds payload or header size to every message | Yes, a small field | No extra field needed | Yes, a `traceparent` header |
| Suitable when only match-up is needed, not full call-graph visibility | Yes, the simpler and cheaper choice | Not applicable | Overkill, brings tracing infrastructure for a simple match |
| Human-readable identifier possible | Yes, if a business key is reused | Not applicable | No, `trace-id` is opaque hex |

## 13. Related and incompatible patterns

- **Return Address.** Correlation Identifier answers which request a reply
  belongs to. Return Address answers where the reply should be sent.
  The two are frequently implemented together in the same message envelope,
  a correlation identifier field plus a reply-to field, but they are
  logically independent, and a system can use one without the other, for
  example a fixed reply channel with no return-address field but a
  correlation identifier to disambiguate which of several outstanding
  requests each reply on that fixed channel answers.
- **Aggregator.** An Aggregator collects several related messages into one
  composite result, and it needs a way to decide which messages are related
  to which other messages, which is exactly the job a correlation identifier,
  or a correlation expression as in Camel's Aggregator EIP, performs. An
  Aggregator without a correlation key has no way to form its groups
  correctly.
- **Message Sequence.** Where Correlation Identifier says these messages
  belong together, Message Sequence, a companion pattern in the same
  catalog, says and here is their order within that group, typically via a
  sequence number and a total-count field carried alongside the correlation
  identifier. The two compose directly, the correlation identifier groups,
  the sequence number orders within the group.
- **Distributed trace context, W3C Trace Context.** Related in purpose,
  incompatible in scope if conflated carelessly. A trace context is built to
  propagate automatically through every hop of a call graph and to represent
  parent-child relationships between spans, not merely a flat request-reply
  match. Using a trace ID as an application-level correlation identifier is a
  legitimate simplification for systems that already have tracing wired
  through every hop, but it silently fails the moment any hop in the
  business-relevant chain is not instrumented for tracing, because the trace
  context then breaks or restarts there while the business relationship
  between the messages has not actually ended. A dedicated, application-owned
  correlation identifier has no such dependency on tracing infrastructure
  being present at every hop.
- **Idempotent Receiver.** A correlation identifier is frequently reused, or
  paired with a separate idempotency key, to detect and discard duplicate
  replies or duplicate processing of the same logical request, which an
  Idempotent Receiver implements by tracking which identifiers it has already
  handled. The two patterns solve different problems, matching versus
  deduplicating, but share the same underlying identifier in many real
  implementations.

## 14. Refactoring path in and out

Introducing Correlation Identifier into a system that does not yet have one.

1. Identify the exact pair, or group, of messages that currently cannot be
   matched, and confirm the failure mode is genuine, not merely a design
   preference. If a synchronous call already correlates for free, stop here.
2. Choose a generation scheme, a fresh UUID, an echoed message identifier, or
   an existing business key, weighing the forces from dimension 3, and decide
   at what point in the flow the identifier is generated, at the requestor
   before sending, or by the first broker or gateway the message passes
   through.
3. Add the identifier as a first-class field in the message envelope or
   protocol header, not buried inside the business payload, so that
   intermediaries which do not parse the payload can still see and, where
   necessary, log or route on it.
4. Update every replier in the chain to copy the identifier from the inbound
   message into every outbound message it produces in response, unchanged.
5. Add a correlation store on the requesting side, a map from identifier to
   pending operation, with an explicit timeout policy from the start, not
   added later, because an unbounded store is the single most common failure
   mode in production, per dimension 11.
6. Add a contract test, or an end-to-end integration test, that sends a
   request through the full real chain of intermediaries and asserts the
   identifier survives to the reply unchanged, so a future change to any hop
   that silently drops the field is caught immediately rather than months
   later as an unexplained pile of orphan replies.

Removing Correlation Identifier once it stops earning its place.

1. Confirm the system genuinely no longer needs it, most commonly because the
   asynchronous channel that motivated it has been replaced by a synchronous
   one, or because a proper distributed tracing system has taken over the
   correlation responsibility end to end.
2. Remove the correlation store and its timeout logic from the requestor
   first, since it is dead code the moment nothing consults it, and confirm
   no other component, an Aggregator, a dead-letter handler, a log pipeline,
   still depends on the field being present.
3. Only after confirming no downstream consumer depends on the field, stop
   populating it at the point of generation. Leave the field itself in the
   schema, marked optional, for one deployment cycle if backward
   compatibility with older producers or consumers is a concern, then remove
   it from the schema entirely in a subsequent, clearly versioned change.

## 15. Testing and verification

What becomes easy to test because of this pattern, individual request-reply
exchanges can be tested in complete isolation from timing and ordering,
because a test can assert purely on the equality of the correlation
identifier between a captured request and a captured reply, without needing
to control or reason about the order in which messages actually arrive. This
turns what would otherwise be a flaky, timing-dependent integration test into
a deterministic assertion.

What becomes harder, testing the correlation store's eviction and timeout
behavior correctly requires either injecting a controllable clock or using a
fake-time test rig, because a real wall-clock-based timeout test is slow
and, worse, intrinsically flaky under CI load. Testing propagation across the
full real chain of intermediaries, not a mocked one, requires either a true
end-to-end integration environment or a contract test against each
intermediary in isolation, because a unit test of any single hop cannot prove
the field survives the whole chain.

The techniques that apply directly.

- **Golden-path correlation test.** Send a request with a known, injected
  correlation identifier through the full real or realistic pipeline, and
  assert the eventual reply carries the exact same identifier, byte for
  byte, not merely a value that looks similar.
- **Orphan-reply test.** Deliver a reply carrying a correlation identifier
  that has no corresponding entry in the correlation store, and assert the
  system handles it as an explicitly logged, named case, per the failure
  mode in dimension 11, rather than throwing an unhandled exception or
  silently discarding it with no trace.
- **Collision test.** For a scheme that reuses a business key rather than a
  synthetic identifier, generate two requests that are known to share the
  same business key by construction, and assert the system either rejects
  the second as a duplicate or explicitly and correctly disambiguates them,
  rather than silently letting the second overwrite the first's pending
  entry.
- **Timeout eviction test, using a fake clock.** Register a pending
  correlation entry, advance the fake clock past its deadline, and assert
  the entry is evicted and reported as a timeout, then assert a late reply
  that subsequently arrives for that same, now-evicted identifier is handled
  as an orphan reply rather than resurrecting stale state.
- **Middleware-in-the-loop propagation test.** For each real intermediary in
  the actual production chain, a serializer, an adapter, a broker
  configuration, send a message through it alone and assert the correlation
  field is present, unchanged, on the other side, catching a silent-drop
  regression at the exact hop that introduced it rather than only at the
  end of the whole chain.

## 16. Observability signals

Every log line, metric, and trace span emitted while processing a request or
its reply should carry the correlation identifier as a structured field, not
interpolated into a free-text message, so that log aggregation and search
tooling can filter and group on it directly. A healthy system shows, for
every correlation identifier, exactly one request event and either exactly
one reply event, for a strict request-reply exchange, or a bounded, expected
number of reply events, for a fan-out or an aggregation, arriving within the
configured timeout window.

Signals to watch for on a dashboard.

- **Orphan-reply rate.** The count of replies received whose correlation
  identifier has no matching entry in the correlation store. A sustained
  nonzero rate indicates either a timeout set too aggressively relative to
  actual reply latency, or a duplicate-delivery problem on the replying
  side, per dimension 11.
- **Pending-correlation table size, over time.** A steadily climbing count
  of entries in the correlation store that is not matched by a
  correspondingly climbing request rate indicates an eviction or timeout
  bug, the memory-leak failure mode from dimension 11, and should alert
  well before the process runs out of memory.
- **Correlation match latency.** The time elapsed between a request's send
  timestamp and its matched reply's receive timestamp, keyed by correlation
  identifier, is a direct measurement of end-to-end responsiveness for the
  asynchronous exchange and is the metric most timeout values should be set
  relative to, using a high percentile, not the mean, since timeouts must
  survive tail latency, not typical latency.
- **Propagation-loss alerts.** Where feasible, an intermediary hop that is
  expected to always carry the correlation field forward should itself emit
  a metric or a log warning any time it observes a message with the field
  missing, so propagation loss is caught at the point of loss rather than
  inferred later from a rising orphan-reply rate several hops downstream.

## 17. Security and privacy implications

A correlation identifier is, by its nature, a value that ties multiple
otherwise-separate messages together, and that linking capability is
information in its own right, independent of what the messages' business
payloads contain. Three concrete implications follow from that fact.

First, a predictable correlation identifier, a sequential integer or a small
counter, leaks operational metadata to anyone who can observe the traffic or
the reply, most obviously request volume and approximate ordering, and in
some designs it can let one party infer the existence or approximate count of
other parties' concurrent requests. A cryptographically random identifier, a
UUID version 4, closes this leak, because a random value carries no
information about anything other than itself.

Second, reusing a genuine business key, an order number, an account
identifier, a user's email address, as the correlation identifier means that
value now travels through every hop of the messaging infrastructure,
including logging, monitoring, and any intermediary that inspects headers,
even hops that have no legitimate business need to see it. This can turn a
routine log line into an unintended disclosure of personal or business data,
and it means the correlation identifier field must be brought into the same
data-classification and retention policy that governs the business key
itself, rather than being treated as a low-sensitivity technical field by
default.

Third, a correlation identifier that also functions as, or is trivially
derivable into, an authorization token, most commonly when a system lets any
holder of a correlation identifier retrieve the full result of the operation
it refers to with no additional authentication, turns the identifier into a
de facto bearer credential. The Azure Asynchronous Request-Reply reference
pattern illustrates the correct mitigation for exactly this shape. After
processing completes, the status endpoint does not return the result inline,
it issues an HTTP 303 redirect to a separately access-controlled resource URL,
generated with a time-limited user delegation SAS token, rather than treating
knowledge of the correlation identifier itself as sufficient proof of the
right to read the result
(https://learn.microsoft.com/en-us/azure/architecture/patterns/async-request-reply,
verified 2026-08-02). Any system that lets a correlation identifier double as
an access-control mechanism should apply the same discipline, treat the
identifier as good for matching, never as good for authorizing.

## Code examples

### TypeScript

```typescript
type CorrelatedMessage<T> = {
  correlationId: string;
  payload: T;
};

class RequestorTS {
  private pending = new Map<
    string,
    { resolve: (v: unknown) => void; reject: (e: Error) => void; timer: NodeJS.Timeout }
  >();

  send<TReq, TRes>(
    payload: TReq,
    sendFn: (msg: CorrelatedMessage<TReq>) => void,
    timeoutMs: number
  ): Promise<TRes> {
    const correlationId = crypto.randomUUID();
    return new Promise<TRes>((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(correlationId);
        reject(new Error(`timed out waiting for reply to ${correlationId}`));
      }, timeoutMs);
      this.pending.set(correlationId, { resolve: resolve as (v: unknown) => void, reject, timer });
      sendFn({ correlationId, payload });
    });
  }

  onReply<TRes>(msg: CorrelatedMessage<TRes>): void {
    const entry = this.pending.get(msg.correlationId);
    if (!entry) {
      console.warn(`orphan reply for unknown correlationId ${msg.correlationId}`);
      return;
    }
    clearTimeout(entry.timer);
    this.pending.delete(msg.correlationId);
    entry.resolve(msg.payload);
  }
}

function replyTo<TReq, TRes>(
  request: CorrelatedMessage<TReq>,
  buildReply: (req: TReq) => TRes
): CorrelatedMessage<TRes> {
  return { correlationId: request.correlationId, payload: buildReply(request.payload) };
}

const requestor = new RequestorTS();
const promise = requestor.send<{ orderId: string }, { status: string }>(
  { orderId: "ord-42" },
  (msg) => {
    const reply = replyTo(msg, (req) => ({ status: `paid:${req.orderId}` }));
    setTimeout(() => requestor.onReply(reply), 5);
  },
  1000
);
promise.then((res) => console.log("resolved", res));
```

### Python

```python
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class CorrelatedMessage:
    correlation_id: str
    payload: Any


@dataclass
class PendingEntry:
    deadline: float
    result: Any = None
    done: bool = False


class Requestor:
    def __init__(self) -> None:
        self.pending: dict[str, PendingEntry] = {}

    def send(
        self,
        payload: Any,
        send_fn: Callable[[CorrelatedMessage], None],
        timeout_seconds: float,
    ) -> str:
        correlation_id = str(uuid.uuid4())
        self.pending[correlation_id] = PendingEntry(deadline=time.time() + timeout_seconds)
        send_fn(CorrelatedMessage(correlation_id, payload))
        return correlation_id

    def on_reply(self, msg: CorrelatedMessage) -> None:
        entry = self.pending.get(msg.correlation_id)
        if entry is None:
            print(f"orphan reply for unknown correlation_id {msg.correlation_id}")
            return
        entry.result = msg.payload
        entry.done = True

    def sweep_timeouts(self) -> list[str]:
        now = time.time()
        expired = [cid for cid, e in self.pending.items() if not e.done and e.deadline < now]
        for cid in expired:
            del self.pending[cid]
        return expired


def reply_to(request: CorrelatedMessage, build_reply: Callable[[Any], Any]) -> CorrelatedMessage:
    return CorrelatedMessage(request.correlation_id, build_reply(request.payload))


requestor = Requestor()
outbox: list[CorrelatedMessage] = []
cid = requestor.send({"order_id": "ord-42"}, outbox.append, timeout_seconds=1.0)
request = outbox[0]
reply = reply_to(request, lambda req: {"status": f"paid:{req['order_id']}"})
requestor.on_reply(reply)
print(requestor.pending[cid].result)
```

### Go

```go
package main

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"fmt"
	"sync"
	"time"
)

// newCorrelationID returns a random 16-byte identifier encoded as hex.
// A production system would reach for a maintained UUID library instead
// of a hand-rolled generator, this keeps the example dependency-free.
func newCorrelationID() string {
	b := make([]byte, 16)
	_, _ = rand.Read(b)
	return hex.EncodeToString(b)
}

type CorrelatedMessage struct {
	CorrelationID string
	Payload       any
}

type pendingEntry struct {
	result chan any
}

type Requestor struct {
	mu      sync.Mutex
	pending map[string]pendingEntry
}

func NewRequestor() *Requestor {
	return &Requestor{pending: make(map[string]pendingEntry)}
}

func (r *Requestor) Send(payload any, send func(CorrelatedMessage), timeout time.Duration) (any, error) {
	id := newCorrelationID()
	entry := pendingEntry{result: make(chan any, 1)}

	r.mu.Lock()
	r.pending[id] = entry
	r.mu.Unlock()

	send(CorrelatedMessage{CorrelationID: id, Payload: payload})

	select {
	case res := <-entry.result:
		r.mu.Lock()
		delete(r.pending, id)
		r.mu.Unlock()
		return res, nil
	case <-time.After(timeout):
		r.mu.Lock()
		delete(r.pending, id)
		r.mu.Unlock()
		return nil, fmt.Errorf("timed out waiting for reply to %s", id)
	}
}

func (r *Requestor) OnReply(msg CorrelatedMessage) error {
	r.mu.Lock()
	entry, ok := r.pending[msg.CorrelationID]
	r.mu.Unlock()
	if !ok {
		return errors.New("orphan reply for unknown correlation id " + msg.CorrelationID)
	}
	entry.result <- msg.Payload
	return nil
}

func ReplyTo(request CorrelatedMessage, build func(any) any) CorrelatedMessage {
	return CorrelatedMessage{CorrelationID: request.CorrelationID, Payload: build(request.Payload)}
}

func main() {
	requestor := NewRequestor()

	var captured CorrelatedMessage
	res, err := requestor.Send(map[string]string{"orderId": "ord-42"}, func(msg CorrelatedMessage) {
		captured = msg
		go func() {
			reply := ReplyTo(captured, func(p any) any {
				req := p.(map[string]string)
				return map[string]string{"status": "paid:" + req["orderId"]}
			})
			_ = requestor.OnReply(reply)
		}()
	}, time.Second)

	if err != nil {
		fmt.Println("error", err)
		return
	}
	fmt.Println("resolved", res)
}
```

## Which languages, and why

TypeScript, Python, and Go were chosen because the pattern's core mechanic,
generate an identifier, stash a pending continuation keyed by it, match an
incoming reply against that key, and enforce a timeout, is naturally
expressed with each language's own concurrency idiom. a `Promise` and
`setTimeout` in TypeScript, a plain dictionary with an explicit deadline
sweep in Python, and a `chan` plus `select` with `time.After` in Go, close to
how a correlation-aware requestor is actually built in each ecosystem's real
messaging client libraries. The Go sample generates its identifier with
`crypto/rand` rather than a UUID library so the file compiles standalone,
with no external module, a real project would reach for a maintained UUID
library instead. Java, Rust, and Swift were omitted from the runnable set for
this entry, not because the pattern translates poorly to them, JMS's own
`JMSCorrelationID` field is a Java ecosystem citizen, but to keep the example
set to the three where the async-timeout-and-lookup shape is most
idiomatically compact without a framework dependency.

## Compilation and execution notes

The TypeScript sample was type-checked with `npx tsc --noEmit`, which
requires `@types/node` for `NodeJS.Timeout` and the DOM lib for
`crypto.randomUUID`, and passed against `--target es2022 --lib es2022,dom`.
The Python sample was run directly with `python3` and produced
`{'status': 'paid:ord-42'}`. The Go sample was compiled and run with `go run`, using only the standard
library (`crypto/rand`, `encoding/hex`, `sync`, `time`, `errors`, `fmt`), and
printed `resolved map[status:paid:ord-42]`.

## References

1. Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns. Designing,
   Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003,
   Messaging Systems chapter, Correlation Identifier.
2. Enterprise Integration Patterns companion site, "Correlation Identifier,"
   https://www.enterpriseintegrationpatterns.com/patterns/messaging/CorrelationIdentifier.html,
   verified 2026-08-02.
3. Apache Camel documentation, "Aggregate EIP,"
   https://camel.apache.org/components/next/eips/aggregate-eip.html, verified
   2026-08-02.
4. Microsoft Learn, Azure Architecture Center, "Asynchronous Request-Reply
   pattern,"
   https://learn.microsoft.com/en-us/azure/architecture/patterns/async-request-reply,
   verified 2026-08-02.
5. Microsoft Learn, "Azure Service Bus messages, payloads, and
   serialization,"
   https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-messages-payloads,
   verified 2026-08-02.
6. W3C Recommendation, "Trace Context," https://www.w3.org/TR/trace-context/,
   verified 2026-08-02.
