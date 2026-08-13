---
name: Envelope Wrapper
slug: envelope-wrapper
family: 07-integration
category: Message Construction
aliases: [Message Envelope, Wrapper Pattern (EIP), Envelope Pattern]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [message, correlation-identifier, format-indicator, channel-adapter, content-based-router, message-sequence]
incompatible_with: []
verified: 2026-08-02
---

# Envelope Wrapper

## 1. Name, aliases, and lineage

The canonical name is Envelope Wrapper. It is catalogued in Gregor Hohpe and
Bobby Woolf, *Enterprise Integration Patterns. Designing, Building, and
Deploying Messaging Solutions*, Addison-Wesley, 2003, in the Message
Construction chapter. The published problem statement reads "How can existing
systems participate in a messaging exchange that places specific requirements
on the message format, such as message header fields or encryption?" and the
solution is stated as "Use an Envelope Wrapper to wrap application data inside
an envelope that is compliant with the messaging infrastructure. Unwrap the
message when it arrives at the destination." (enterpriseintegrationpatterns.com,
"Envelope Wrapper", https://www.enterpriseintegrationpatterns.com/patterns/messaging/EnvelopeWrapper.html,
verified 2026-08-02, reproducing the book's own wording).

The pattern is closely tied to, and often confused with, the more general
**Message** pattern from the same catalog, which simply states that any
information sent over a channel is wrapped into a data structure the messaging
system understands. Envelope Wrapper is Message applied specifically to the
case where an existing application already has its own data format and that
format must be carried inside the messaging infrastructure's own required
shape without being altered. The book positions Envelope Wrapper as one of
several sibling Message Construction patterns, alongside Correlation
Identifier and Return Address, each of which typically rides inside the
envelope as a header field.

Outside the EIP catalog, practitioners use "Message Envelope" interchangeably,
particularly in the SOAP, AMQP and event-streaming communities, where the word
"envelope" appears directly in the wire format's own vocabulary (SOAP calls its
top-level element `Envelope`, see dimension 9). "Wrapper Pattern (EIP)" is a
disambiguation some blog posts use to avoid confusion with the unrelated
object-oriented Adapter or Decorator patterns, which are also informally
called wrappers. There is no competing or superseding name in wide use, and
the pattern has not been renamed since 2003.

## 2. Problem and context

An application was built to produce and consume data in its own native
format, a flat file, a fixed-width record, a plain XML document with no
messaging-specific fields, a CSV row. That application now needs to
participate in a messaging system, and the messaging infrastructure demands
things the application format was never designed to carry. A correlation
identifier so a reply can be matched to its request. A return address so a
reply channel is known. A format indicator so a receiver can tell what shape
of payload it is looking at before parsing it. Header fields for routing,
priority, encryption, or digital signing that a message bus or an enterprise
service bus requires on every message that passes through it.

The naive responses both fail. Changing the application's own data format to
add these fields breaks every other consumer of that data that is not
messaging-aware, for instance a batch job that reads the same file from disk,
or a legacy system that was never going to be migrated. Refusing to carry the
extra fields at all breaks the messaging infrastructure's own requirements,
so the message cannot be routed, correlated, or secured the way every other
message in the system is.

The context in which this problem specifically arises is integration at a
seam between an existing, unmodifiable or expensive-to-modify system and a
messaging layer that was added later, which is the majority of real
enterprise integration work. It is rare to design the application format and
the messaging format together from a blank sheet, because most integration
projects exist precisely because two systems that were not designed together
now need to talk.

## 3. Forces

- **Coupling to the application format.** Favoured. The application's own
  data structure is never touched. Whatever validates, parses, or archives
  that data outside the messaging path keeps working unmodified.
- **Coupling to the messaging infrastructure's contract.** Favoured. The
  envelope satisfies whatever the bus, broker, or ESB requires without asking
  the application to know about it.
- **Payload transparency.** Sacrificed at the infrastructure layer. A
  generic router or logging component that only understands the envelope
  cannot see or reason about the wrapped application data unless the envelope
  also exposes a Format Indicator or a small set of promoted header fields.
- **Message size.** Sacrificed, usually mildly. The envelope adds bytes,
  sometimes doubling the structure when the payload itself must be
  base64-encoded to survive inside a text-based envelope such as XML or JSON.
- **Operational uniformity.** Favoured. Every message the infrastructure
  handles, regardless of which legacy system produced the payload, has the
  same header shape, so retry logic, dead-lettering, tracing, and access
  control can be written once against the envelope rather than once per
  producer.
- **Latency.** Mildly sacrificed. Wrapping and unwrapping cost one
  serialization pass each way, which is usually irrelevant next to network
  and broker latency but is measurable in a high-throughput, low-latency path.
- **Team topology.** Favoured. The team that owns the legacy system does not
  need to learn or agree to the messaging schema. A Channel Adapter or
  gateway team owns the wrapping and unwrapping in one place.

The pattern gives up payload transparency at the infrastructure layer and a
modest overhead in size and latency in exchange for leaving the application
untouched and giving the messaging layer a uniform contract to build on.

## 4. Applicability and non-applicability

Reach for Envelope Wrapper when the following hold.

- An existing system's data format cannot or should not be changed, because
  other consumers depend on it, because it is externally standardised, or
  because the cost of changing it exceeds the cost of wrapping it.
- The messaging infrastructure requires fields the application format has no
  place for, correlation identifiers, reply addresses, format indicators,
  security tokens, routing hints, or trace context.
- Several different producer systems, each with its own native format, must
  feed one messaging infrastructure that expects one uniform envelope shape.
- The wrapping and unwrapping logic is naturally a Channel Adapter's job, a
  single, well-tested seam rather than logic scattered through every
  producer and consumer.

Do NOT reach for Envelope Wrapper in these cases, and the reason matters more
than the rule.

- **The system is being designed from scratch and will only ever speak to
  the messaging infrastructure.** There is no legacy format to preserve, so
  design the message format to include the required fields directly. Wrapping
  a format that was invented for the messaging layer in the first place is
  pure overhead, an envelope with nothing legacy inside it.
- **The messaging infrastructure needs to see and act on the payload's own
  fields, not only route by envelope headers.** If every consumer must parse
  through the envelope to reach fields it actually needs, most of the
  supposed decoupling is fiction, and a shared schema across producer and
  consumer is the honest design. Cross reference Content-Based Router, which
  in that situation is usually better served by promoting the routing key
  into a header rather than wrapping and then unwrapping only to route.
- **A single point-to-point integration with one producer and one
  consumer, both under your control, exists.** A shared, versioned schema
  agreed between the two parties is simpler than wrapping and unwrapping, and
  removes a translation step that has nothing to protect against.
- **The payload itself must be inspected by every intermediary along the
  route, for instance a message-content-aware firewall or a schema
  validator that runs against the business data.** An opaque envelope hides
  exactly what those intermediaries need. Keep the payload format visible at
  the protocol level instead, using a Format Indicator rather than an opaque
  wrapper, or use a self-describing envelope such as CloudEvents where the
  data is a first-class, typed field rather than an opaque blob.
- **The overhead of double serialization is unacceptable on the hot path.**
  High-frequency trading systems and similarly latency-sensitive paths
  sometimes accept a tighter coupling between producer and consumer schema
  specifically to avoid this cost. Measure before assuming this applies.

## 5. Structure

- **Sender Application.** The existing system producing data in its own
  native format. It has no knowledge of the messaging infrastructure's
  requirements and should stay that way.
- **Wrapping component.** Usually implemented as, or alongside, a Channel
  Adapter. Takes the sender's native payload, constructs the envelope, and
  places the payload inside it, either unchanged, encoded, or transformed
  into a form the envelope can carry (for instance base64 for binary data
  inside a text envelope).
- **Envelope.** The messaging-infrastructure-compliant structure. Carries
  the required header fields, for instance a correlation identifier, a
  return address, a format indicator, security or routing metadata, and a
  designated slot for the opaque or semi-opaque application payload.
- **Message Channel.** Carries the envelope, not the raw application data,
  through the messaging infrastructure. Every Message Router, Message
  Filter, or other infrastructure component along the way operates on the
  envelope's header fields.
- **Unwrapping component.** The mirror of the wrapping component at, or near,
  the receiving application. Extracts the original application payload from
  the envelope and hands it to the Receiver Application in the format that
  application expects, discarding or logging the envelope metadata as
  appropriate.
- **Receiver Application.** The existing system consuming data in its own
  native format, equally unaware of the messaging infrastructure.

The wrapping and unwrapping components are the only parts of the system that
know about both the application format and the envelope format. This is
deliberate. Confining that knowledge to two symmetric, testable seams is the
entire value of the pattern.

## 6. ASCII structure diagram

```
   +-----------------+         +----------------------------+
   |  Sender          |         |  Wrapping Component        |
   |  Application     |-------->|  (often a Channel Adapter)  |
   |  (native format) |  raw    |----------------------------|
   +-----------------+  payload |  builds Envelope,          |
                                  |    header. correlation id, |
                                  |    header. return address, |
                                  |    header. format indicator|
                                  |    body.   raw payload     |
                                  +--------------+-------------+
                                                 |
                                                 v
                                   +---------------------------+
                                   |     Message Channel       |
                                   |  (carries Envelope only)  |
                                   +--------------+-------------+
                                                 |
                                                 v
                                  +--------------+-------------+
                                  |  Unwrapping Component      |
                                  |----------------------------|
                                  |  reads Envelope headers,   |
                                  |  extracts body,            |
                                  |  restores native format    |
                                  +--------------+-------------+
                                                 |  native
                                                 |  payload
                                                 v
                                   +-----------------+
                                   |  Receiver        |
                                   |  Application     |
                                   |  (native format) |
                                   +-----------------+

   Everything between the two Application boxes deals in Envelopes.
   Neither Application box has ever seen an Envelope header.
```

## 7. Dynamics

```
Sender App     Wrapping Component      Message Channel      Unwrapping Component   Receiver App
   |                    |                      |                       |                 |
   |-- native payload ->|                      |                       |                 |
   |                    |-- generate corr-id   |                       |                 |
   |                    |-- set format hint    |                       |                 |
   |                    |-- wrap payload       |                       |                 |
   |                    |   into Envelope      |                       |                 |
   |                    |-- send(Envelope) --->|                       |                 |
   |                    |                      |-- route by headers -->|                 |
   |                    |                      |   (router/filter      |                 |
   |                    |                      |    never opens body)  |                 |
   |                    |                      |-- deliver(Envelope) ->|                 |
   |                    |                      |                       |-- read headers  |
   |                    |                      |                       |-- extract body  |
   |                    |                      |                       |-- restore native|
   |                    |                      |                       |   format        |
   |                    |                      |                       |-- deliver ------>|
   |                    |                      |                       |                 |
                                                                        |-- reply path uses
                                                                           return-address header
                                                                           from original Envelope
```

One timing detail matters in practice. Intermediate infrastructure
components, a Message Router, a dead letter mechanism, a security filter,
operate entirely at the envelope layer and never deserialize the wrapped
payload. This is what makes routing and filtering cheap. If a router must
open the envelope to make a routing decision, the correlating fields belong
in the envelope header instead, which is a design signal rather than a bug in
this pattern.

## 8. Implementation variants

**Opaque byte-blob envelope.** The payload is carried as an untyped byte
array or base64 string inside a header-plus-body envelope. Simplest to
implement, works across any payload type including binary, but a Format
Indicator header becomes mandatory, otherwise the unwrapping component has
no way to know how to parse the body.

**Typed, self-describing envelope.** The envelope declares the payload's
content type as a first-class field, for instance a `Content-Type` header
carrying the value `application/json`, or a `datacontenttype` attribute, so
intermediaries can make a limited decision (for instance, reject unsupported
content types) without fully parsing the body. CloudEvents (see dimension 9)
is the modern standardised form of this variant.

**Header table plus opaque body, at the protocol layer.** Rather than a
document wrapping a document, the envelope is expressed as protocol-level
metadata attached alongside an unmodified payload, with no document nesting
at all. AMQP's basic properties and Kafka's record headers are both this
variant, see dimension 9. The advantage is that no encoding transformation
is needed for the body, since the transport already separates metadata from
payload at the wire level.

**Nested XML or JSON envelope.** The payload is embedded as a child element
or nested object inside a parent structure that also carries the header
fields. SOAP's `Envelope` and `Header` and `Body` structure is the canonical
example. This variant is the most portable across text-based transports
that have no native metadata channel, and the most expensive in bytes and
parsing cost, because the whole document must be parsed to reach the body
even when only the headers are needed.

**Encrypted or signed envelope.** The wrapping step also encrypts or signs
the payload, and the envelope carries the metadata needed to reverse that
step, a key identifier, an algorithm identifier, a signature. This is a
common combination with Envelope Wrapper specifically because encryption and
signing both require metadata the application format was never designed to
carry, which is exactly the motivating problem from dimension 2.

**Language and framework note.** In frameworks with a built-in Message
abstraction, Spring Integration's `Message<T>`, Apache Camel's `Exchange`, or
NServiceBus's message context, the framework itself is playing the role of
the envelope at the in-process level, and the wrapping and unwrapping
components are the framework's own channel adapters at the process boundary.
Application code inside such a framework rarely constructs an envelope by
hand, it constructs a payload object and lets the framework's adapter attach
headers on the way out and strip them on the way in.

## 9. Known production uses

**SOAP, the `Envelope` element.** SOAP 1.2 defines a top-level `Envelope`
element information item containing an optional `Header` and a mandatory
`Body`. The specification states the envelope contains, in order, "An
optional Header element information item ... A mandatory Body element
information item," and notes that Part 1 of the specification "mandates no
particular structure or interpretation" of the body's contents, leaving the
application payload opaque to the envelope itself. W3C, "SOAP Version 1.2
Part 1. Messaging Framework (Second Edition)", section 5, "SOAP Envelope",
https://www.w3.org/TR/soap12-part1/, verified 2026-08-02.

**Apache Kafka, record headers (KIP-82).** Kafka Improvement Proposal 82
added a native `Headers` collection to every Kafka record, a mutable list of
key-value pairs carried alongside, and structurally separate from, the
record's key and value payload, encoded on the wire as a `Header` structure
holding a UTF-8 encoded key string and a byte-array value, with duplicate
keys and order preservation both supported. Apache Kafka wiki, "KIP-82 - Add
Record Headers",
https://cwiki.apache.org/confluence/display/KAFKA/KIP-82+-+Add+Record+Headers,
verified 2026-08-02.

**AMQP 0-9-1, basic message properties.** AMQP 0-9-1, the protocol RabbitMQ
implements, defines a set of message properties, content type, headers
table, correlation ID, reply-to, message ID, expiration, timestamp, that are
"set by publishers at the time of publishing" and travel separately from the
message body, with the broker itself treating them as opaque metadata for
applications to interpret. RabbitMQ documentation, "Publishers",
https://www.rabbitmq.com/docs/publishers, verified 2026-08-02.

**Spring Integration, the `Message<T>` interface.** Spring Integration's
core abstraction is `Message<T>`, "a generic container for data" where "any
object can be provided as the payload, and each Message instance includes
headers containing user-extensible properties as key-value pairs," with
`MessageHeaders` implementing `java.util.Map` but rejecting mutation after
construction to keep messages immutable across concurrent consumers.
Broadcom (Spring Integration project), Spring Integration Reference
documentation, "Message",
https://docs.spring.io/spring-integration/reference/message.html,
verified 2026-08-02.

## 10. Consequences

Positive.

- The application's own data format and the systems that already depend on
  it are never touched.
- Messaging infrastructure requirements, correlation, routing, security, are
  satisfied without leaking into application code.
- Wrapping and unwrapping logic lives in one tested place per direction
  rather than being duplicated across every producer and consumer.
- Adding a new producer with its own native format costs one new wrapping
  component, not a change to the shared envelope contract.
- Intermediate infrastructure, routers, filters, dead letter handling, is
  written once against the envelope and works uniformly regardless of which
  legacy format is inside.

Negative.

- Every message carries the overhead of the envelope structure in addition
  to the payload, which matters at scale and on latency-sensitive paths.
- Payload data is opaque to generic infrastructure by design, so any
  component that genuinely needs to see inside the payload must either
  fully unwrap it or rely on fields specifically promoted into the header,
  which duplicates data between envelope and body if not managed carefully.
- Two encoding and decoding steps are added per hop, wrap on the way in,
  unwrap on the way out, each a place a bug can silently corrupt or drop
  data.
- A binary payload inside a text-based envelope typically needs base64 or
  similar encoding, inflating size by roughly a third and adding CPU cost.
- The envelope's own schema becomes a second contract that must be
  versioned and evolved alongside the payload's contract, doubling the
  surface area that integration partners must agree on.

## 11. Failure modes and misuse

**Header and body drift.** Symptom. A field exists in both the envelope
header and the payload body, and downstream consumers disagree on which one
is authoritative, producing inconsistent routing or duplicate processing.
Cause. A value was promoted into the header for routing convenience without
removing or formally deprecating the same field inside the body. Fix. Pick
one source of truth per field and document it, or derive the header value
from the body at wrap time and treat the header as strictly derived, never
independently settable downstream.

**Missing Format Indicator on an opaque envelope.** Symptom. The unwrapping
component throws a parse error, or silently misinterprets bytes, when a
second payload format is introduced into a system that assumed only one.
Cause. The opaque byte-blob variant was chosen without a content-type or
format-indicator header, so the unwrapping component hardcoded an assumption
about what is inside. Fix. Add a Format Indicator header before adding a
second payload shape, never infer format from content sniffing in
production.

**Double wrapping.** Symptom. A payload arrives already inside one envelope,
travels through a second Channel Adapter that wraps it again, and the
consumer receives an envelope inside an envelope, or a correlation
identifier that no longer matches what the original sender expects. Cause.
Two independent integration points both believe they are the first hop
responsible for wrapping. Fix. Make wrapping idempotent by checking for an
existing envelope signature before wrapping, or draw a clear ownership
boundary for exactly one wrapping point per integration path.

**Broken correlation across a fan-out.** Symptom. A request is wrapped,
correlation ID attached, then split (see Splitter) into several messages
that are each separately wrapped by a downstream component, and replies
cannot be correlated back to the original request. Cause. The wrapping
component regenerated a new correlation identifier per split message
instead of propagating the original one. Fix. Propagate the original
correlation identifier through every derived message, and use Message
Sequence fields for the fan-out position rather than substituting a new
correlation ID.

**Encryption metadata lost on unwrap.** Symptom. A message that was
encrypted at wrap time cannot be decrypted at the destination, or is
decrypted with the wrong key. Cause. The key identifier or algorithm
identifier the wrapping component recorded in the envelope header was
stripped or overwritten by an intermediate hop that only understood a subset
of the envelope schema. Fix. Treat security-relevant envelope fields as
required and validate their presence at every hop, never assume an
intermediate component is transparent to header contents it does not use.

**Wrapping component becomes a bottleneck.** Symptom. Throughput degrades
noticeably compared to a benchmark of the raw payload path, and profiling
shows time spent in serialization rather than business logic. Cause. A
nested XML or JSON envelope variant was chosen for a high-throughput path
where a protocol-level header-plus-opaque-body variant, or no envelope at
all, would have avoided the double parse. Fix. Measure the specific
serialization cost before choosing the nested-document variant on a hot
path, and prefer transport-native headers (Kafka, AMQP) when the transport
already offers them.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Envelope Wrapper | Shared schema, no wrapper | Content-Based Router with body parsing | Format Indicator alone (no envelope) | Sidecar or Channel Adapter translation with schema conversion |
|---|---|---|---|---|---|
| Leaves application format untouched | Yes | No, both sides must adopt the shared schema | Yes for the payload, but routing logic still parses it | Yes | Yes |
| Infrastructure can route without parsing payload | Yes, via headers | Yes, fields are native to the one shared schema | No, by definition it parses the body | Partially, only format is known, not content | Yes, after conversion the target schema is native |
| Number of contracts to maintain | Two, envelope and payload | One | Two in practice, envelope-equivalent header plus payload | One plus a format tag | Two, source schema and target schema |
| Overhead per message | Header plus body, one wrap and one unwrap | None beyond the shared schema itself | Router pays full parse cost on the hot path | Minimal, one tag | Full conversion cost, potentially higher than wrapping |
| Fits multiple legacy producers with different formats | Strong, each gets its own wrapping component | Poor, every producer must adopt the shared schema | Poor, router must understand every payload shape | Weak, only tells you what to parse with, not how to route | Strong, but requires a full schema mapping per producer |
| Security and correlation metadata support | Native, that is a primary motivation | Must be designed into the shared schema from the start | Not addressed directly | Not addressed | Depends on target schema |
| Suitable for greenfield, single producer, single consumer | Overkill | Best fit | Overkill unless routing genuinely needs body content | Insufficient alone | Overkill unless formats genuinely differ |

Reading of the table. Envelope Wrapper wins specifically at the seam between
an unmodifiable legacy format and a messaging infrastructure with header
requirements the legacy format cannot express. A shared schema wins when
there is no legacy constraint. Content-Based Router with full body parsing
is the fallback when routing genuinely cannot be decided from headers alone,
and it should be treated as a signal to promote the deciding field into the
envelope rather than the default choice.

## 13. Related and incompatible patterns

- **Message.** The parent pattern. Envelope Wrapper is Message applied
  specifically to the case of preserving an existing application format
  inside the messaging infrastructure's required shape. Every envelope is a
  Message, not every Message is wrapping a pre-existing legacy format.
- **Correlation Identifier.** Composes directly. The correlation ID is
  almost always one of the header fields the envelope exists to carry,
  because the application format has no native concept of request-reply
  correlation.
- **Return Address.** Composes directly, for the same reason as Correlation
  Identifier. A reply channel is infrastructure metadata the legacy format
  was never designed to hold.
- **Format Indicator.** Frequently a required companion, not an alternative.
  When the envelope carries an opaque payload, the Format Indicator header
  tells the unwrapping component, or any intermediary, how to interpret the
  body without guessing.
- **Channel Adapter.** The usual host. Wrapping and unwrapping are typically
  implemented as the outbound and inbound halves of a Channel Adapter that
  sits at the boundary between the legacy system and the messaging
  infrastructure.
- **Content-Based Router.** A tension, not a conflict. A router that must
  open the envelope to inspect the payload body to make its routing decision
  has partially defeated the purpose of the envelope. The healthy
  relationship is a router that decides purely from envelope headers, with
  routing-relevant payload fields promoted into a header at wrap time.
- **Message Translator.** A near neighbour that is sometimes confused with
  it. Message Translator changes the shape or meaning of the payload data
  itself between two different schemas. Envelope Wrapper does not alter the
  payload's meaning at all, it adds a surrounding structure while leaving
  the payload byte-for-byte or structurally intact inside.
- **Canonical Data Model.** A different, often complementary, strategy for
  the same underlying problem of format diversity. A Canonical Data Model
  standardises the payload's own schema across every system in the
  integration, whereas Envelope Wrapper standardises only the surrounding
  metadata and leaves each producer's payload format as-is. They are not
  incompatible, a canonical payload can still ride inside an envelope for
  its metadata needs, but they solve different halves of the format
  mismatch problem and neither substitutes for the other.

## 14. Refactoring path in and out

Introducing the pattern into an integration that currently has none.

1. Identify every field the messaging infrastructure requires that the
   application's native format has no place for, correlation ID, reply
   address, security token, routing key, format tag. List them explicitly.
2. Design the envelope's header shape first, independent of any specific
   application format, so multiple producers can share one envelope schema.
3. Build the wrapping component as a single, isolated function or class
   that takes the native payload and the required header values and
   produces the envelope. Do not embed this logic inside business logic
   code, keep it at the integration seam.
4. Build the symmetric unwrapping component that extracts the native
   payload and hands it, unchanged, to the receiving application, while
   surfacing the header fields to whatever infrastructure component needs
   them, for instance a reply mechanism reading the return address.
5. Add a Format Indicator header if the envelope will ever carry more than
   one payload shape, even if only one shape exists on day one. Adding it
   later is a breaking change to every existing consumer.
6. Route the first real integration through the new wrapping and unwrapping
   pair end to end, verifying the payload is byte-for-byte or structurally
   identical after a round trip through wrap and unwrap, before onboarding
   a second producer.
7. Onboard additional producers by adding their own wrapping component
   against the same shared envelope schema, never by branching the schema
   per producer.

Removing the pattern when it stops earning its place. Signals include a
system where every consumer parses through the envelope to reach payload
fields anyway, or a single producer and single consumer pair that never
gained a second party.

1. Confirm no intermediary genuinely depends on envelope-only headers for
   routing or security decisions. If one does, the pattern is still earning
   its place and only the payload-facing side should simplify.
2. Introduce a shared schema directly between the producer and consumer
   that includes the fields the envelope used to carry as headers,
   correlation ID, format hint, and so on, as native fields of that schema.
3. Migrate the producer to emit the shared schema directly, and the
   consumer to read it directly, retiring the wrapping and unwrapping
   components once both sides have migrated.
4. Delete the envelope schema and its wrapping and unwrapping components
   only after confirming no other producer or consumer, including any
   dead-letter or audit tooling, still depends on the envelope shape.

## 15. Testing and verification

Easier because of the pattern.

- The wrapping and unwrapping components can be tested in complete
  isolation from both the messaging infrastructure and the application
  logic, a pure round-trip test, wrap a known payload, unwrap it, assert the
  result equals the original.
- Infrastructure components that route or filter on envelope headers can be
  tested against synthetic envelopes with fabricated headers and an empty
  or dummy body, without needing a real payload of any particular format.
- Contract tests against the envelope schema, correlation ID present,
  format indicator matches a known set, timestamp within an expected range,
  can run independently of whichever application format happens to be
  inside.

Harder because of the pattern.

- An end-to-end test that only exercises the envelope layer can pass while
  the payload inside is silently corrupted by an encoding mismatch, for
  instance base64 versus raw bytes, so a genuine round-trip assertion on
  the actual payload bytes, not only the envelope structure, is necessary
  and easy to skip by accident.
- Version skew between the envelope schema and the payload schema can pass
  unit tests on each side independently while failing in integration,
  because neither side alone can detect that the other has changed.

Techniques that apply.

- **Round-trip property test.** Generate a range of representative native
  payloads, including edge cases such as empty payloads, maximum size
  payloads, and payloads containing bytes that could be misinterpreted by
  the envelope's own encoding, wrap each, unwrap it, and assert equality
  with the original.
- **Envelope schema contract test.** A test suite that validates only the
  envelope's own required headers are present and well-formed, independent
  of payload content, run against every producer's output before it is
  allowed to enter the shared channel.
- **Consumer-driven contract testing** between the wrapping component and
  the messaging infrastructure's own expectations, so infrastructure
  changes that would break a required header are caught before deployment
  rather than discovered when a message is silently dropped or dead
  lettered.
- **Fuzzing the unwrapping component** with malformed or partially
  corrupted envelopes, since the unwrapping component is a security and
  reliability boundary consuming data that arrived over a network, not
  purely a trusted internal call.

## 16. Observability signals

What to record.

- A counter of wrap operations and unwrap operations, labelled by producer
  or consumer identity and by format indicator, so a mismatch between the
  two counts over time flags messages that are being wrapped but never
  successfully unwrapped somewhere downstream.
- A counter of unwrap failures, labelled by the reason, missing format
  indicator, unknown format, size mismatch, decryption failure, since each
  reason points at a different failure mode from dimension 11.
- The correlation identifier and any trace context propagated as span
  attributes on both the wrap and unwrap spans, so a distributed trace can
  show the full path a payload took even though intermediate infrastructure
  never inspected the payload itself.
- A histogram of envelope size versus native payload size, to catch
  unexpected bloat from an encoding choice, for instance an unintentional
  double base64 encoding.
- A gauge or counter for the age of an envelope at unwrap time, timestamp
  now minus the envelope's own timestamp header, to catch messages that sat
  in a queue far longer than expected before being processed.

A healthy instance on a dashboard. Wrap and unwrap counts track each other
closely over any reasonable time window, per producer and per consumer.
Unwrap failure rate sits near zero and does not correlate with deploys.
Envelope size stays a stable, small overhead over native payload size.
Correlation identifiers reliably link a reply span to its originating
request span in the trace view.

A failing instance. Wrap count climbs while unwrap count for the matching
consumer flatlines, pointing at a stuck queue or a silently crashing
consumer. Unwrap failures spike immediately after a producer deploy,
pointing at a schema change that was not coordinated with the envelope
contract. Envelope size balloons for one producer only, pointing at an
encoding regression. Correlation identifiers stop appearing in reply
messages, pointing at the fan-out correlation failure from dimension 11.

## 17. Security and privacy implications

The envelope is frequently where security metadata lives specifically
because the wrapped application format was never designed to carry it,
which means the envelope becomes a genuine security boundary, not a neutral
container.

**Header tampering in transit.** If the envelope's headers are not
themselves signed or protected, an intermediary or an attacker with access
to the channel can modify routing headers, correlation identifiers, or a
declared format indicator, causing a message to be misrouted, misattributed,
or misparsed by the unwrapping component. Sign the envelope headers that
matter for security decisions, not only the payload, or use a transport
that guarantees header integrity end to end.

**Confidentiality of the payload versus the headers.** Encrypting the
payload while leaving routing and correlation headers in plaintext is a
deliberate and often necessary trade-off, since infrastructure needs to
route without decrypting, but it means the envelope headers themselves are
an information-disclosure surface. A correlation identifier or a return
address that encodes a customer identifier or a tenant name leaks
information to anyone who can observe the envelope on the wire or in a
broker's own logs, even when the payload is fully encrypted. Treat header
values with the same data-classification discipline as payload fields when
they can carry identifying information, and prefer opaque, randomly
generated identifiers over ones that embed meaning.

**Injection through the format indicator or content-type header.** An
unwrapping component that trusts the format indicator header without
validating it against an allowlist can be tricked into deserializing a
payload with an unintended, potentially unsafe deserializer, for instance a
format indicator claiming a safe data format while the body actually
contains a payload targeting a known deserialization vulnerability in a
different parser the unwrapping component also happens to support.
Validate the format indicator against an explicit allowlist before
dispatching to a deserializer, never dispatch dynamically based on an
attacker-influenced field.

**Replay and duplicate processing.** Because the envelope is what carries
correlation and identity information, an envelope that is replayed, either
maliciously or as an artifact of at-least-once delivery from the underlying
transport, can cause the unwrapping side to process the same payload twice
if the unwrapping component does not itself enforce idempotency using the
envelope's own message identifier. This is not unique to Envelope Wrapper,
but the pattern is precisely where the identifier needed to detect a replay
lives, so the responsibility to check it also sits at the unwrapping seam.

On privacy specifically, the header fields the pattern exists to carry,
correlation identifiers, return addresses, security tokens, timestamps, are
metadata that broker logs, tracing systems, and dead-letter stores routinely
retain even when the payload itself is encrypted or dropped after
processing. Apply the same retention and access-control policy to envelope
headers stored in logs and traces as would apply to the equivalent data if
it appeared directly in the payload.

## Code examples

Three languages, chosen for three genuinely different framing of the
pattern. TypeScript shows the plain document-envelope variant with an
explicit wrap and unwrap function pair, which is the shape most integration
code written against a message broker actually takes. Go shows the
protocol-level header-plus-opaque-body variant, matching how Kafka and AMQP
clients actually expose headers separately from the payload, using a
byte-map type the way Kafka's own headers are represented. Python shows a
typed, self-describing envelope closer to the CloudEvents style, using a
dataclass so the header shape is explicit and the payload stays an opaque,
independently serializable field.

### TypeScript

```typescript
interface Envelope {
  correlationId: string;
  formatIndicator: string;
  returnAddress?: string;
  timestamp: number;
  body: string;
}

interface NativeOrder {
  orderId: string;
  sku: string;
  quantity: number;
}

function wrap(payload: NativeOrder, returnAddress?: string): Envelope {
  return {
    correlationId: crypto.randomUUID(),
    formatIndicator: "application/vnd.orders.v1+json",
    returnAddress,
    timestamp: Date.now(),
    body: JSON.stringify(payload),
  };
}

function unwrap(envelope: Envelope): NativeOrder {
  if (envelope.formatIndicator !== "application/vnd.orders.v1+json") {
    throw new Error(`unsupported format: ${envelope.formatIndicator}`);
  }
  return JSON.parse(envelope.body) as NativeOrder;
}

const original: NativeOrder = { orderId: "A-100", sku: "WIDGET-9", quantity: 3 };
const envelope = wrap(original, "reply.orders.service-a");
const restored = unwrap(envelope);
console.log(JSON.stringify(envelope));
console.log(JSON.stringify(restored) === JSON.stringify(original));
```

### Go

```go
package main

import (
	"encoding/json"
	"fmt"
)

type Headers map[string][]byte

type NativeOrder struct {
	OrderID  string `json:"orderId"`
	SKU      string `json:"sku"`
	Quantity int    `json:"quantity"`
}

func wrap(payload NativeOrder, correlationID string) (Headers, []byte, error) {
	body, err := json.Marshal(payload)
	if err != nil {
		return nil, nil, err
	}
	headers := Headers{
		"correlation-id":   []byte(correlationID),
		"format-indicator": []byte("application/vnd.orders.v1+json"),
	}
	return headers, body, nil
}

func unwrap(headers Headers, body []byte) (NativeOrder, error) {
	var order NativeOrder
	format, ok := headers["format-indicator"]
	if !ok || string(format) != "application/vnd.orders.v1+json" {
		return order, fmt.Errorf("unsupported or missing format-indicator")
	}
	if err := json.Unmarshal(body, &order); err != nil {
		return order, err
	}
	return order, nil
}

func main() {
	original := NativeOrder{OrderID: "A-100", SKU: "WIDGET-9", Quantity: 3}
	headers, body, err := wrap(original, "corr-42")
	if err != nil {
		panic(err)
	}
	restored, err := unwrap(headers, body)
	if err != nil {
		panic(err)
	}
	fmt.Printf("correlation-id=%s\n", headers["correlation-id"])
	fmt.Printf("restored equals original: %v\n", restored == original)
}
```

### Python

```python
from dataclasses import dataclass, field
import json
import time
import uuid


@dataclass(frozen=True)
class Envelope:
    correlation_id: str
    format_indicator: str
    body: bytes
    timestamp: float = field(default_factory=time.time)
    return_address: str | None = None


def wrap(payload: dict, return_address: str | None = None) -> Envelope:
    body = json.dumps(payload).encode("utf-8")
    return Envelope(
        correlation_id=str(uuid.uuid4()),
        format_indicator="application/vnd.orders.v1+json",
        body=body,
        return_address=return_address,
    )


def unwrap(envelope: Envelope) -> dict:
    if envelope.format_indicator != "application/vnd.orders.v1+json":
        raise ValueError(f"unsupported format: {envelope.format_indicator}")
    return json.loads(envelope.body.decode("utf-8"))


if __name__ == "__main__":
    original = {"orderId": "A-100", "sku": "WIDGET-9", "quantity": 3}
    envelope = wrap(original, return_address="reply.orders.service-a")
    restored = unwrap(envelope)
    print(f"correlation_id={envelope.correlation_id}")
    print(f"restored equals original: {restored == original}")
```

## 18. References

1. Gregor Hohpe, Bobby Woolf. *Enterprise Integration Patterns. Designing,
   Building, and Deploying Messaging Solutions*. Addison-Wesley, 2003.
   ISBN 0-321-20068-3. Message Construction chapter, Envelope Wrapper.
   Source of the problem statement, solution summary, and the pattern's
   relationship to Message, Correlation Identifier, Return Address, and
   Format Indicator.
2. Enterprise Integration Patterns companion site. "Envelope Wrapper".
   https://www.enterpriseintegrationpatterns.com/patterns/messaging/EnvelopeWrapper.html
   Verified 2026-08-02. Reproduces the book's problem and solution wording
   used in dimension 1.
3. World Wide Web Consortium. "SOAP Version 1.2 Part 1. Messaging
   Framework (Second Edition)", section 5, "SOAP Envelope".
   https://www.w3.org/TR/soap12-part1/
   Verified 2026-08-02. Source for the SOAP Envelope production use in
   dimension 9 and the nested-envelope implementation variant in dimension 8.
4. Apache Software Foundation, Apache Kafka project. "KIP-82 - Add Record
   Headers", Apache Kafka wiki.
   https://cwiki.apache.org/confluence/display/KAFKA/KIP-82+-+Add+Record+Headers
   Verified 2026-08-02. Source for the Kafka record headers production use
   in dimension 9.
5. Broadcom (RabbitMQ). "Publishers", RabbitMQ documentation.
   https://www.rabbitmq.com/docs/publishers
   Verified 2026-08-02. Source for AMQP 0-9-1 basic message properties as a
   production use in dimension 9.
6. Broadcom (VMware Tanzu), Spring Integration project. "Message", Spring
   Integration Reference documentation.
   https://docs.spring.io/spring-integration/reference/message.html
   Verified 2026-08-02. Source for the `Message<T>` and `MessageHeaders`
   production use in dimension 9, and the immutable-headers detail in
   dimension 10.
