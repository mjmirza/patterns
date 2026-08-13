---
name: Content Filter
slug: content-filter
family: 07-integration
category: Integration
aliases: [Data Filter, Field Selector, Response Filter, Payload Trimmer]
first_described: "Hohpe, Woolf 2003"
maturity: canonical
related: [content-enricher, message-filter, splitter, content-based-router, channel-adapter]
incompatible_with: []
verified: 2026-08-02
---

# Content Filter

## 1. Name, aliases, and lineage

The canonical name is Content Filter. It is one of the message transformation
patterns catalogued in Gregor Hohpe and Bobby Woolf, *Enterprise Integration
Patterns. Designing, Building, and Deploying Messaging Solutions*,
Addison-Wesley, 2003, in the Message Transformation section of the book. The
authors state the intent directly. "Use a Content Filter to remove unimportant
data items from a message leaving only important items"
([Enterprise Integration Patterns, Content Filter](https://www.enterpriseintegrationpatterns.com/patterns/messaging/ContentFilter.html),
verified 2026-08-02). The problem statement in the same source reads, "How do
you simplify dealing with a large message, when you are interested only in a
few data items?"

The pattern is deliberately the mirror image of its sibling in the same
catalog, Content Enricher, which adds data a message is missing rather than
removing data a message has too much of. The two are described on the same
page in the book because a reader who understands one understands the shape
of the other by inversion.

Industry practice has settled on several informal names for the same shape,
none of them from the original catalog but all describing the identical
mechanism.

- **Field Selector.** Common in API documentation, describing a request
  parameter or configuration that names which fields a response should carry,
  for example the `fields` system parameter documented for Google Cloud APIs
  ([Google Cloud, System Parameters](https://docs.cloud.google.com/apis/docs/system-parameters),
  verified 2026-08-02).
- **Response Filter.** Used when the filtering happens at the boundary of an
  HTTP API rather than inside a message queue, describing the same allow-list
  or deny-list mechanism applied to an outbound payload.
- **Payload Trimmer.** An informal, operational term used inside messaging and
  event-streaming teams for a pipeline stage whose only job is to shrink a
  message before it crosses a network or cost boundary. It is not a term from
  any specification, and it is included here as a label a reader is likely to
  encounter, not as an authoritative alias.
- **Data Filter.** Appears in some vendor documentation as a synonym, most
  often when the pattern is implemented as a generic transformer step inside
  an ESB or integration platform rather than as a named, dedicated component.

One naming confusion deserves an explicit warning because it recurs constantly
in code review. Content Filter is not Message Filter. Message Filter, covered
separately in this catalog, is a routing pattern. It evaluates a predicate
against an incoming message and either passes the entire message through
unchanged or discards it entirely, deciding which messages travel further.
Content Filter never makes a whole-message keep-or-discard decision. It always
passes a message through, but it changes what is inside that message,
deciding which fields survive. A pipeline stage named `OrderFilter` that
sometimes drops an entire order and sometimes strips two fields from an order
is really two patterns glued into one component, and that conflation is
exactly the kind of code smell dimension 11 of this entry names directly.

## 2. Problem and context

A consumer receives a message that is far larger, richer, or more deeply
nested than anything it needs, and forwarding or storing that full message
creates real cost. It wastes bandwidth on a constrained channel, it couples
the consumer's code to fields it never reads, so an unrelated schema change
upstream can break a consumer that never touched those fields, or it exposes
data the consumer has no business seeing at all.

The situation is recognisable in almost any integration codebase. An
enterprise resource planning system exports a customer order as a deeply
nested XML document with forty fields, because the ERP's own internal model
carries forty fields for every order it has ever processed since 1998. A
downstream shipping service needs six of them, the order id, the recipient
name, the shipping address, and three line items. A partner-facing webhook
needs to publish order confirmations to a third party that should never see
the customer's payment instrument, internal fraud-review notes, or the
customer's full profile, only the order id, the item list, and the total. A
mobile client on a metered connection needs a product catalogue response that
does not carry every locale's description and every historical price when the
device is only going to render three fields per row.

In each case the underlying data exists, is correct, and was legitimately
produced by the upstream system. The problem is not that the data is wrong.
The problem is a mismatch between what the producer emits by default and what
a specific consumer, at a specific point in a pipeline, is entitled or able to
use. Content Filter is the named answer to that mismatch, a distinct,
addressable stage that receives the rich message and emits a narrower one,
so the decision about what a given hop needs lives in one place instead of
being duplicated, ad hoc, inside every consumer that receives the full
payload and picks out what it wants by hand.

The pattern also solves a second, related problem that the book calls out
explicitly. Messages produced by external systems and packaged applications
are frequently structured as deep, irregular hierarchies that reflect that
system's internal object model rather than any information the receiver
actually needs shaped that way. Content Filter's flattening variant, covered
in dimension 8, converts such a tree "into a simple list of elements than can
be more easily understood and processed by other systems"
([Enterprise Integration Patterns, Content Filter](https://www.enterpriseintegrationpatterns.com/patterns/messaging/ContentFilter.html),
verified 2026-08-02), independent of whether any fields are actually removed.

## 3. Forces

Content Filter sits at a specific point of tension between several
competing pressures, and the pattern only earns its place when the balance
genuinely favours filtering over the alternatives.

- **Coupling versus completeness.** Forwarding the full, unfiltered message
  is the path of least resistance today, because no filter spec has to be
  written or maintained. But every field a consumer is exposed to is a field
  it can, accidentally or deliberately, come to depend on, which then locks
  the producer's schema against safe evolution. A narrow, explicit contract
  reduces that coupling at the cost of an extra artifact, the filter spec
  itself, that now has to be kept current.
- **Bandwidth and storage versus processing cost.** Filtering trades CPU work
  at one hop for reduced network transfer, reduced storage, and reduced
  downstream parse cost at every hop after it. For a message read by many
  downstream consumers, or transmitted over a metered or high-latency link,
  that trade is usually favourable. For a message read once, over a fast
  local link, the filter's own overhead can exceed what it saves.
- **Data minimization versus recoverability.** Removing fields the consumer
  does not need is good security and privacy hygiene, but it is also
  destructive. Once a field is filtered out and the filtered message is the
  only copy retained, the information is gone. The pattern favours
  minimization at the channel it operates on, and depends on a separate
  mechanism, an archive, a Claim Check, or the still-intact upstream system,
  to preserve recoverability elsewhere.
- **Static simplicity versus dynamic flexibility.** A fixed, versioned
  allow-list is simple to reason about, simple to test, and simple to audit.
  A filter whose field selection is driven per-request by the caller, the way
  a GraphQL query or a `fields` parameter works, is more flexible but pushes
  the filter specification outside the integration layer and into the API
  contract itself, and it introduces a new question, whether an untrusted
  caller can request fields it should not be allowed to see, or construct a
  path expression that reaches somewhere unintended.
- **Statelessness versus context.** Content Filter, unlike its sibling
  Content Enricher, is meant to be a pure function of the message it
  receives, with no external lookup, no side effect, and no dependency on
  anything outside the message itself. That statelessness is a deliberate
  design force, not an accident, because it is what keeps the pattern cheap,
  parallelizable, and easy to test. A filter stage that starts calling out to
  another service to decide what to keep has, in practice, become a Content
  Enricher wearing a filter's name, and the two responsibilities should be
  split back into two stages.

## 4. Applicability and non-applicability

Reach for Content Filter when the situation matches one or more of the
following.

- A consumer genuinely needs only a subset of a much larger message, and that
  subset is stable enough to express as an explicit, named contract.
- Sensitive fields, payment instruments, government identifiers, internal
  notes, employee-only annotations, must never cross a particular boundary,
  such as a partner webhook, a public API response, or a log sink, while
  other, non-sensitive fields from the same source message legitimately
  should.
- An upstream system produces a deeply nested, irregular structure that
  reflects its own internal object model, and downstream code would be
  simpler and less fragile against unrelated upstream changes if it operated
  on a flat, purpose-shaped representation instead.
- The channel the message travels over is bandwidth-, latency-, or
  cost-constrained (mobile networks, IoT links, metered cloud egress, a
  message broker billed per byte), and the size reduction from dropping
  unused fields is material.
- Multiple consumers of the same upstream feed need materially different,
  narrower views, and it is cheaper and clearer to produce those views as
  distinct, named filter stages than to have every consumer parse the full
  message and discard what it does not need in its own code, duplicated N
  times.

Do not reach for Content Filter, or replace it with something else, when any
of the following holds.

- **The consumer needs the full message for audit, replay, or debugging
  later.** Filtering is destructive by default. If a downstream stage, a
  compliance process, or a future incident investigation will need the
  original, unfiltered message, archive the original first, a durable log, a
  Claim Check reference, an event store, and apply Content Filter only to the
  copy that travels onward, never to the only copy that exists.
- **The set of fields a consumer needs varies per request in a way a fixed
  pipeline stage cannot anticipate.** A statically configured Content Filter
  stage that has to be redeployed every time a client's needs change is the
  wrong tool. A client-driven projection mechanism at the API layer, a
  GraphQL selection set or a validated `fields` query parameter, is the
  better fit, because it lets the caller specify the shape without requiring
  a new integration artifact for every combination of fields.
- **A field being removed is required for correctness at a later stage in
  the same pipeline**, even if the immediate consumer at this hop does not
  read it. Filtering too early, at a shared upstream hop that multiple
  downstream consumers or stages depend on, silently starves whichever
  consumer needed the field, and the resulting failure surfaces far away from
  the filter that caused it. See dimension 11 for the exact failure signature.
- **The filtering decision requires an expensive lookup, a call to another
  service, or knowledge the message itself does not contain.** That is
  Content Enricher's job, or possibly a Content-Based Router's, not Content
  Filter's. A stage that both looks something up externally and removes
  fields is doing two patterns at once and should be split.
- **The oversharing is the producer's fault and the fix belongs there.**
  Content Filter is frequently reached for as a workaround for a producer
  that emits far more than any consumer needs by design, an internal object
  graph serialized wholesale rather than a deliberate output contract. That
  workaround is legitimate as an interim measure, but it should be recognised
  as a symptom, not treated as the permanent architecture. The durable fix,
  where the producer is under the same team's control, is usually to narrow
  what the producer emits by default, or to expose a purpose-built,
  already-narrow endpoint, and retire the filter once that is in place.

## 5. Structure

- **Original Message.** The message as produced by the upstream system,
  carrying every field that system's own model exposes, including fields the
  eventual consumer neither needs nor should see.
- **Filter Specification.** The rule set the filter applies, an explicit
  allow-list of paths to keep, a deny-list of paths to remove, or a
  reshaping template that both selects and restructures. The specification is
  the thing that must be versioned, reviewed, and tested. The filter
  component itself is usually generic and reusable across many
  specifications.
- **Content Filter.** The stage that receives the original message, applies
  the filter specification, and emits a new, narrower message. It performs no
  external lookups and has no side effects beyond producing that output. It
  is a pure transformation from one message to another.
- **Filtered Message.** The output, structurally similar to, or a
  deliberately flattened reshaping of, the original, but carrying only the
  fields the specification retained.
- **Consumer.** The recipient the filtered message is produced for. In a
  pipeline with several distinct consumers, each with different needs, there
  is typically one Content Filter instance, with its own specification, per
  consumer shape, rather than one filter trying to serve every consumer at
  once.

## 6. ASCII structure diagram

```
+------------+        +-----------------------+        +------------+
| Producer   |------->|    Content Filter      |------->| Consumer   |
| (full,     |        |  applies a Filter      |        | (needs a   |
|  rich      |        |  Specification. an     |        |  narrow    |
|  message)  |        |  allow-list, a deny-   |        |  subset)   |
+------------+        |  list, or a reshaping  |        +------------+
                       |  template              |
                       +-----------+-------------+
                                   ^
                                   |
                       +-----------+-------------+
                       |  Filter Specification    |
                       |  (versioned paths,        |
                       |   schema, or template)    |
                       +---------------------------+
```

## 7. Dynamics

```
Producer            Content Filter                    Consumer
   |                       |                              |
   |-- full message ------>|                              |
   |  (all fields)         |                              |
   |                       |-- load Filter Specification   |
   |                       |   (allow-list / template)     |
   |                       |                                |
   |                       |-- project / strip fields       |
   |                       |   per specification            |
   |                       |                                |
   |                       |-- filtered message ----------->|
   |                       |   (only retained fields)       |
   |                       |                                |
```

At runtime a Content Filter is invoked once per message, does not block on
anything outside the message, and produces exactly one output message per
input message. It never fans a single input into multiple outputs, which
distinguishes it from a Splitter, and it never drops the message wholesale,
which distinguishes it from a Message Filter. If a specification names a
path that is absent from a given message, the correct default behaviour,
covered further in dimension 11, is to omit that path from the output
silently rather than to error, unless the specification explicitly marks the
path as required.

## 8. Implementation variants

- **Allow-list projection.** The specification names the exact paths to
  retain. Everything not named is dropped. This is the security-preferred
  shape because it fails closed. a new field added upstream that nobody has
  reviewed yet is excluded by default rather than leaking through.
- **Deny-list masking.** The specification names the exact paths to remove.
  Everything else passes through unchanged. This is the shape Elasticsearch
  ships as its `remove` ingest processor, whose documentation states plainly
  that it "removes existing fields"
  ([Elastic, remove processor](https://www.elastic.co/guide/en/elasticsearch/reference/current/remove-processor.html),
  verified 2026-08-02). Deny-list masking is simpler to author when only a
  small, known set of fields is sensitive, but it fails open. a new sensitive
  field added upstream leaks by default until the deny-list is updated to
  name it, the exact failure mode analysed in dimension 11.
- **Template-based reshaping.** The specification is a template that both
  selects data from the source and restructures the result into a different
  shape, typically flattening nesting. Amazon EventBridge's input
  transformer is a production example. it lets a rule author define
  variables via JSON path against the source event and then compose an
  output template from those variables, producing a payload with a different
  shape than the original event
  ([AWS, Amazon EventBridge input transformation](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-transform-target-input.html),
  verified 2026-08-02). Bazaarvoice's Jolt ships the same idea as a
  standalone JSON-to-JSON transform library, with a dedicated `remove`
  transform stage described as removing "data from the tree"
  ([bazaarvoice/jolt, README](https://github.com/bazaarvoice/jolt),
  verified 2026-08-02).
- **Schema-driven projection.** The filter specification is generated from,
  or validated against, a formal schema rather than hand-maintained as a
  freestanding list, so a path that does not exist in the schema is rejected
  at authoring time instead of silently doing nothing at runtime. Protocol
  Buffers' `FieldMask`, referenced by Google's own API guidance for the
  `fields` system parameter used for response filtering
  ([Google Cloud, System Parameters](https://docs.cloud.google.com/apis/docs/system-parameters),
  verified 2026-08-02), is the clearest production example of this variant.
  the mask is itself a typed, structural reference into the schema rather
  than a free-text path string.
- **Streaming, per-record filtering.** In a stream-processing topology, the
  filter is a stateless mapping stage applied to every record as it flows
  through, rather than a request-response transformation. The implementation
  concern shifts from parsing a whole document and then trimming it, to
  avoiding materialising the parts about to be discarded, because at
  streaming volumes the cost of fully deserializing a message only to throw
  most of it away can dominate the pipeline's CPU budget.
- **Client-specified dynamic filtering.** The filter specification is not
  fixed at deployment time. the caller supplies it per request, as with a
  GraphQL query's selection set or an API's `fields` parameter. This is not a
  fixed pipeline stage in the classic EIP sense so much as it is the same
  underlying mechanism, projection to a named subset of fields, moved up to
  be part of the request contract itself. It trades the operational
  simplicity of a versioned, reviewable specification for flexibility, and it
  reintroduces the security question named in dimension 3, whether an
  untrusted caller's field selection has been validated against what that
  caller is actually permitted to request, not merely against what the
  schema allows to be requested by anyone.
- **Framework-generic implementation.** Not every integration framework
  ships Content Filter as a named, dedicated component. Spring Integration,
  for example, documents a Content Enricher explicitly but has no equivalent
  dedicated Content Filter stage in its message transformation
  documentation. The same effect is achieved with its generic Transformer
  component, configured with a SpEL expression or a plain Java method that
  returns a narrower payload
  ([Spring Integration, Message Transformation](https://docs.spring.io/spring-integration/reference/message-transformation.html),
  verified 2026-08-02). This matters for implementers. the absence of a
  dedicated `ContentFilter` class in a given framework does not mean the
  pattern is unavailable there, only that it is expressed through a more
  general transformation primitive, and the design discipline of dimension
  14, treating the field list as a first-class, versioned artifact rather
  than an inline expression buried in configuration, still applies.

## 9. Known production uses

- **Google Cloud APIs, `fields` system parameter.** Google's cross-API
  system parameter documentation defines a `fields` (or `$fields`) parameter,
  surfaced via the `X-Goog-FieldMask` header on some APIs, that "enables
  FieldMask ... used for response filtering", with the documented default
  that "if empty, all fields should be returned unless documented otherwise"
  ([Google Cloud, System Parameters](https://docs.cloud.google.com/apis/docs/system-parameters),
  verified 2026-08-02). This is Content Filter applied at the API response
  boundary, driven by the caller as a schema-typed field mask rather than a
  free-text expression.
- **Amazon EventBridge, input transformer.** AWS documents the input
  transformer as a mechanism to customize the text from an event before
  EventBridge passes the information to the target of a rule, built from a
  JSON-path-based Input Path that extracts named values from the source
  event and an Input Template that composes the outbound payload from those
  extracted values only
  ([AWS, Amazon EventBridge input transformation](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-transform-target-input.html),
  verified 2026-08-02). Fields not referenced by the Input Path never reach
  the target at all, which is the template-based reshaping variant described
  in dimension 8.
- **Elasticsearch, `remove` ingest processor.** Elastic's ingest pipeline
  documentation states that the `remove` processor "removes existing fields",
  throwing on a missing field by default unless `ignore_missing` is set
  ([Elastic, remove processor](https://www.elastic.co/guide/en/elasticsearch/reference/current/remove-processor.html),
  verified 2026-08-02). Teams use this to strip PII or internal-only fields
  from a document before it is indexed and becomes queryable by anyone with
  cluster read access, a deny-list implementation of the pattern sitting
  directly in front of a datastore rather than in a message broker.
- **Jolt (Bazaarvoice).** Jolt is a JSON-to-JSON transformation library built
  and maintained by Bazaarvoice, distributed as a set of composable "stock
  transforms" that include a dedicated `remove` transform, described in the
  project's own documentation as removing "data from the tree"
  ([bazaarvoice/jolt, README](https://github.com/bazaarvoice/jolt),
  verified 2026-08-02). The project's documentation notes that instances are
  reused to service multiple web requests from a Dropwizard service,
  indicating this Content Filter implementation runs as a shared,
  request-scoped stage inside a production HTTP service rather than as a
  one-off script.

## 10. Consequences

Positive consequences.

- Reduced bandwidth, storage, and downstream parsing cost, because every hop
  after the filter carries and processes only the fields that hop needs.
- Reduced coupling between the consumer and the producer's internal schema.
  a field the consumer never received cannot become an accidental dependency,
  and the producer retains more freedom to change fields the filter already
  excludes without breaking anything downstream.
- Improved data minimization and, by extension, a smaller blast radius if a
  downstream system, log, or partner is ever compromised, because sensitive
  fields that never leave the filter stage cannot leak from anything after
  it.
- A single, auditable place to answer what a given consumer actually
  receives, instead of that answer being implicit in scattered
  consumer-side code that reads a subset of a full payload by convention.
- Simplified downstream code when the filter also flattens a deeply nested
  source structure, because consumers work against a shape purpose-built for
  their needs rather than against the producer's internal object graph.

Negative consequences.

- Information loss is the default, not an edge case. Once a field is
  filtered out of the only copy of a message that is retained, that
  information is gone from that message's lineage. Recovering it requires
  going back to the original source, if the source still has it, or to a
  separately archived original.
- An extra hop, and an extra component to operate, monitor, and version. Even
  a fast, stateless filter adds latency and adds one more place a bug can
  live.
- Filter specifications drift. A field a consumer newly needs is easy to
  forget to add to an allow-list, and a newly introduced sensitive field is
  easy to forget to add to a deny-list. Both are silent failures that surface
  only when something downstream breaks or a security review catches the
  leak, not at the moment the upstream schema actually changed.
- A filter that accumulates business logic beyond simple field selection,
  conditional inclusion rules, derived fields, format conversions specific to
  one consumer, stops being a pure projection and becomes a bespoke,
  hard-to-test transformation wearing the Content Filter name, which erodes
  the simplicity that made the pattern worth adopting in the first place.
- Debugging a missing field now spans two systems instead of one. is the
  field genuinely absent from the source, or is it present at the source and
  being stripped by the filter. Every filter deployment should make that
  question answerable quickly, which is the subject of dimension 16.

## 11. Failure modes and misuse

This dimension states symptoms as a reader would actually observe them in
production, in Symptom, Cause, Fix form, per the project's own guidance for
distinguishing engineering judgement from sourced fact. The specific symptom
and fix pairings below are drawn from operational experience with this class
of pipeline stage rather than from a single citable source.

1. **Symptom.** A consumer that previously received a field, or a newly
   onboarded consumer that expects a field documented as available upstream,
   silently stops seeing it, with no corresponding change on the producer
   side.
   **Cause.** The Content Filter's allow-list was never updated when the
   consumer's requirements changed, or a new consumer was pointed at an
   existing filtered feed without checking whether the existing
   specification already covers what it needs. An allow-list, unlike a
   deny-list, fails closed by design, so an un-updated allow-list quietly
   starves anything that was not anticipated when it was written.
   **Fix.** Treat the filter specification as part of the consumer's API
   contract, not as private implementation detail of the pipeline. Version
   it alongside consumer-facing changes, and add a contract test, described
   in dimension 15, that asserts every field a registered consumer declares
   as required survives the current specification, run automatically
   whenever the specification changes.

2. **Symptom.** An intermittent error, several hops downstream from the
   filter, referencing a field that used to be there, occurring only for
   some code paths and not others, and not correlated with any recent
   deployment of the failing stage itself.
   **Cause.** The filter was placed at a shared upstream hop serving several
   distinct downstream stages or consumers, and its specification was
   written to satisfy the immediate, visible consumer at that point in the
   pipeline, not the full set of everything downstream that ultimately
   depends on the same feed. A field the immediate consumer at hop one does
   not read, but a stage three hops later still needs, gets silently
   stripped before it ever reaches the stage that required it.
   **Fix.** Filter as close to the final, specific consumer as possible,
   never at a shared point multiple independent consumers or later stages
   depend on. When a shared filter genuinely cannot be avoided, its
   specification must be the union of everything every downstream consumer
   needs, not the intersection, and every new downstream consumer of the
   shared feed must be checked against that union before it goes live.

3. **Symptom.** A compliance review, or a post-incident forensic review,
   finds personally identifiable information present in a log store,
   analytics pipeline, or partner system that the team believed was
   protected by a Content Filter stage.
   **Cause.** The filter was implemented as a deny-list naming specific,
   known-sensitive field names or paths, and a new field carrying equivalent
   sensitive data was later introduced upstream under a different name, in a
   different location in the structure, or nested one level deeper than the
   deny-list expression matches, so it passed through by default. A
   deny-list is, by construction, a statement about what was known to be
   sensitive at the time it was written, not a statement about what is
   sensitive now.
   **Fix.** For anything security- or privacy-sensitive, prefer an
   allow-list over a deny-list, so an unrecognised new field is excluded by
   default rather than included by default. Where a deny-list must be used
   for operational reasons, pair it with an automated schema-diff check,
   described in dimension 15, that flags every new field introduced upstream
   for an explicit human decision before it can pass through unreviewed.

4. **Symptom.** The filter stage's CPU usage and added latency scale with
   message size even though only a small fraction of the message is
   ultimately retained, and it becomes a throughput bottleneck under load
   long before any consumer of the filtered output does.
   **Cause.** The implementation fully deserializes the entire source
   document, for example building a complete XML DOM or an in-memory JSON
   tree, before selecting and discarding most of it, so the cost of
   filtering scales with the size of the data being thrown away rather than
   with the size of the data being kept.
   **Fix.** For high-volume or large-document filtering, use a streaming or
   event-driven parse (a SAX-style XML parser, a streaming JSON tokenizer)
   that can skip unselected subtrees without fully materialising them, or
   push the filtering down to the wire-format layer, as Protocol Buffers'
   `FieldMask` does, so the fields never have to be deserialized to be
   dropped at all.

5. **Symptom.** Two independently maintained integrations that are meant to
   produce a trimmed customer view for two different partners emit
   subtly different shapes for logically identical filtered data, and
   downstream code has to special-case each one.
   **Cause.** Each integration hand-rolled its own filter logic, ad hoc field
   lists, or bespoke templates, independently, rather than sharing a single,
   versioned filter specification, so the two implementations drifted apart
   even though the business intent behind both was the same.
   **Fix.** Centralize the filter specification itself, not only the filter
   component's code, as a shared, versioned artifact, a checked-in field
   mask, a shared JSON Schema subset, or a registered GraphQL persisted
   query, so that two consumers asking for the same trimmed view are
   provably asking for the same thing rather than two things that happen to
   look similar today.

## 12. Trade-off matrix

Compared against the named alternatives that are most often confused with, or
proposed in place of, Content Filter.

| Force | Content Filter | Content Enricher | Message Filter | Content-Based Router | Client-driven projection (GraphQL / `fields` param) |
|---|---|---|---|---|---|
| Reduces coupling to producer schema | Strong | None, it adds coupling to an external source | None, it decides pass or drop, not shape | None, it decides destination, not shape | Strong, and shifts the decision to the caller |
| Reduces bandwidth per message | Strong | Weakens it, output is usually larger than input | None, message is unchanged when it passes | None, message is unchanged | Strong, potentially per-request optimal |
| Statelessness | Pure function of the message | Requires an external call or lookup | Pure function of the message | Pure function of the message | Pure function of the message plus caller-supplied selection |
| Can it drop the whole message | No, always emits one output | No, always emits one output | Yes, that is its entire job | No, it forwards to one of several destinations | Not applicable, applies within one already-selected message |
| Security posture | Strong when allow-list, weak when deny-list drifts (dimension 11) | Not a data-minimization control | Not a data-minimization control, coarse pass/drop only | Not a data-minimization control | Requires validating the caller's requested field set against authorization, not only against the schema |
| Operational cost | One extra hop, one specification to maintain | One extra hop plus a dependency on the enrichment source | One extra hop, one predicate to maintain | One extra hop, one routing table to maintain | No dedicated pipeline hop, but the schema and resolver layer must enforce field-level authorization |
| Best fit | Fixed, known set of downstream consumers with stable, distinct needs | Message is missing data a consumer needs, not carrying too much | Deciding which messages continue, not what is inside them | Deciding where a message goes, not what is inside it | Consumer needs vary per request and cannot be anticipated at deploy time |

## 13. Related and incompatible patterns

- **Content Enricher.** The direct inverse. Content Enricher adds data a
  message is missing, typically by calling out to another system or data
  source. Content Filter removes data a message has too much of, without
  calling anything external. A pipeline frequently uses both in sequence, an
  Enricher to add a derived or looked-up field a downstream stage needs,
  followed later by a Filter that narrows the now-richer message down to
  what a specific consumer is entitled to see.
- **Message Filter.** A routing pattern, not a transformation pattern, and
  the confusion between the two is common enough that dimension 1 addresses
  it directly. Message Filter decides which whole messages continue. Content
  Filter decides which fields inside a message that is continuing survive.
  They are frequently placed adjacent to each other in a pipeline, a Message
  Filter first discarding messages that should not be processed at all,
  followed by a Content Filter narrowing the fields on the messages that
  remain.
- **Splitter.** The book's own documentation of Content Filter names Splitter
  as a related pattern specifically because the flattening variant of
  Content Filter, described in dimension 8, is often applied precisely so a
  subsequent Splitter can iterate a now-simple list of elements, rather than
  having to trace through the source system's original, irregular nesting to find
  the records it needs to split
  ([Enterprise Integration Patterns, Content Filter](https://www.enterpriseintegrationpatterns.com/patterns/messaging/ContentFilter.html),
  verified 2026-08-02).
- **Channel Adapter.** Content Filter frequently lives immediately after a
  Channel Adapter that has recently translated a message out of a legacy or
  external format, because that is the point in a pipeline where the
  producer's native, irregular structure first becomes available for
  processing, and the earliest natural point to trim it down.
- **Content-Based Router.** A router decides which channel or destination a
  message travels to next, based on the message's content. it does not
  change what the message contains. A Content Filter can be placed after a
  router so that different destinations, each reached via a different route,
  each receive a payload trimmed for that destination's specific needs.
- **Claim Check.** The pattern most directly in tension with Content
  Filter's destructive nature. Where Content Filter permanently discards
  data from the message that carries it forward, Claim Check preserves the
  full data by storing it externally and replacing it in the message with a
  reference the data can later be retrieved by. When a pipeline needs both
  a narrow, fast in-flight message and the ability to recover the full
  original later, the correct combination is Claim Check first, to preserve
  everything durably, followed by Content Filter on the copy that
  continues, never Content Filter alone discarding the only record that
  ever existed.
- **Guaranteed Delivery.** Not incompatible, but a documented tension.
  Guaranteed Delivery assures a message will arrive, it says nothing about
  whether that message still carries everything a receiver assumes it does.
  A team that relies on delivery guarantees as evidence that the data made
  it through, without separately verifying that a Content Filter upstream
  did not silently strip a field the receiver needed, has confused two
  different guarantees.

## 14. Refactoring path in and out

**Introducing the pattern.** Start from a producer sending a full, rich
message and one or more consumers each reading only a subset of it inline,
inside their own consumer code.

1. For each consumer, trace or grep its actual field access to build a
   concrete list of paths it reads today, rather than guessing from
   documentation, which is frequently stale relative to the code.
2. Turn that list into an explicit, named, versioned Filter Specification, an
   allow-list by default per dimension 11's security guidance, checked into
   source control as its own artifact rather than embedded inline in
   transformation code.
3. Insert the Content Filter as a distinct, addressable stage between the
   producer and this specific consumer, whether that is a new topic, a
   gateway middleware step, or a transformer configured in whatever
   integration platform is already in use.
4. Add a contract test, described fully in dimension 15, asserting that every
   path the consumer's code actually reads is present in the specification's
   allow-list, so the refactor cannot silently starve the very consumer it
   was written for.
5. Cut the consumer over to reading the filtered output instead of the full
   message, and monitor for expected-field-missing errors, dimension 16's
   primary health signal, in the period immediately after cutover.
6. Once the filtered feed is stable, evaluate whether the producer itself
   should narrow its default output, or expose a purpose-built, already-
   narrow endpoint for this consumer's use case, so that the standalone
   filter stage eventually becomes redundant.

**Removing the pattern.** A Content Filter is a candidate for removal, not
merely for tolerance, when any of the following becomes true.

- The size difference between the full message and the filtered message has
  shrunk to the point of being negligible, because the upstream schema
  itself grew narrower over time, and the filter is now doing almost nothing.
- Exactly one consumer ever reads the filtered output, and that consumer
  owns, or can reasonably absorb, the filtering logic itself. Removing the
  standalone hop and inlining the projection into the consumer eliminates a
  network round trip and an operational component with no loss of clarity.
- The allow-list has grown, over successive additions, to cover nearly every
  field the source message carries, at which point the filter provides
  negligible narrowing and its remaining maintenance cost outweighs its
  remaining benefit. Pass the full message and let it go.
- The producer or platform has since adopted a client-driven projection
  mechanism, a GraphQL API or a validated `fields` parameter, that lets each
  consumer request exactly the shape it needs at call time, at which point
  a fixed, pre-deployed Content Filter stage becomes a redundant, less
  flexible duplicate of a capability the API layer now provides natively.

## 15. Testing and verification

- **Golden-file tests.** For each known upstream schema version, pair a
  representative input message fixture with the exact expected filtered
  output fixture, and assert byte-for-byte or structurally exact equality.
  This is the cheapest, highest-signal test for a pattern whose entire job
  is a deterministic transformation of one message into another.
- **Contract tests per registered consumer.** For every consumer known to
  depend on the filtered feed, maintain a machine-readable list of the paths
  it requires, and run a test, on every change to the Filter Specification,
  that asserts each of those paths still survives the current specification.
  This is the direct, automated defence against failure mode 1 in dimension
  11, and it should run in continuous integration, not only manually before
  a release.
- **Property-based tests.** Content Filter's correctness is well captured by
  a small set of invariants that hold regardless of the specific message
  content, which makes it a good target for generated, randomised input.
  Filtering is idempotent, applying the filter twice produces the same
  result as applying it once. Filtering is a strict projection, every field
  present in the output is present, and unmodified in value, at the same
  logical path in the input. the filter never introduces a new value, only
  removes or restructures existing ones. Filtering never introduces a key
  that was not, directly or as a rename target of, a key already present in
  the source.
- **Fuzz and malformed-input tests.** Feed the filter messages with expected
  paths missing, with unexpected types at a path the specification expects
  a scalar or an object, and with deeply or unusually nested structures, and
  assert the filter fails predictably, either by omitting the missing path
  silently or by raising a clearly typed error for a specification
  explicitly marked as requiring that path, never by throwing an unhandled
  exception or silently including data the specification did not intend to
  select.
- **Schema-diff tests in continuous integration.** Whenever the upstream
  producer's schema changes, run an automated check comparing the new schema
  against the current Filter Specification, and fail the build, or open a
  required review, if a new field exists that the specification neither
  explicitly retains nor explicitly excludes. This closes the gap named in
  failure mode 3 of dimension 11, where an unreviewed new field is the exact
  mechanism by which sensitive data leaks through a stale deny-list, or is
  silently unavailable through a stale allow-list.

## 16. Observability signals

- **Size reduction ratio.** Track input bytes divided by output bytes,
  per message and aggregated, as the primary health metric. This ratio
  should be stable over time for a given specification and message type. A
  sudden drop toward one, no reduction happening, most often means the
  filter has regressed into a passthrough, which for a security-purposed
  filter is a leak, not merely an inefficiency, and should page whoever owns
  the filter, not merely be logged.
- **Fields-dropped counters, broken down by field name or family, not only
  a raw total.** A single aggregate count of fields dropped cannot answer
  whether the sensitive field actually got dropped this time. A per-field or
  per-field-family counter can, and is the signal a security review should
  actually look at.
- **Expected-field-missing error rate.** The count of downstream errors, or
  a dedicated check emitted by the filter itself, where a consumer's
  contract test or runtime code encountered a path it declared as required
  and that path was absent from the filtered output. This is the direct
  runtime counterpart to the contract test in dimension 15, and it is the
  clearest signal that failure mode 1 or 2 from dimension 11 is happening in
  production right now.
- **Filter stage latency, both absolute and as a fraction of total pipeline
  latency.** A filter's added latency should be small and should scale
  sub-linearly, ideally not at all, with input size if the implementation
  correctly avoids fully materialising fields it is about to discard. A
  latency that climbs with message size under load is the operational
  signature of the full-materialisation failure mode described as failure 4
  in dimension 11.
- **Filter specification version in distributed traces.** The filter should
  emit, as a span attribute or a log field, the version identifier of the
  specification it applied to a given message. Without this, diagnosing a
  downstream bug report of a missing field requires guessing which
  configuration was live at the time the affected message actually passed
  through the filter. with it, the trace answers the question directly.

A healthy Content Filter shows a flat, unsurprising size-reduction ratio, a
near-zero expected-field-missing error rate, and latency that is small and
stable relative to the surrounding pipeline. An unhealthy one shows any of a
sudden jump toward a one-to-one size ratio (likely misconfiguration or a
security-relevant regression), a spike in missing-field errors correlated
with a recent deploy of either the filter or a consumer (likely a
specification that was not updated in step with a real requirement change),
or latency and CPU climbing with message size under load (likely a
full-document-materialisation implementation that needs to move to a
streaming or wire-level variant).

## 17. Security and privacy implications

Content Filter is one of the more directly security-relevant patterns in
this catalog, because it is very often the actual, concrete control that
sits between a data-rich internal system and a less-trusted boundary, a
partner integration, a third-party webhook, a public API response, a general
log sink, or an analytics pipeline with a broader audience than the source
system itself.

Used as an allow-list, the pattern is a genuine, mechanical enforcement of
data minimization. only what is explicitly, reviewably named as needed is
allowed to cross the boundary, and anything new that appears upstream and has
not yet been reviewed is excluded by default rather than included by default.
Whether a given jurisdiction's data-protection framework requires
minimization is a legal question outside this entry's scope to assert as
settled fact for every reader's situation, and that determination should be
made by the reader against their own applicable law. What can be stated as
straightforward engineering analysis is that an allow-list Content Filter is
a mechanism well suited to implementing whatever minimization requirement
applies, precisely because it fails closed.

Used as a deny-list, the same pattern is a common, recurring source of
exactly the leakage it was meant to prevent, for the reason detailed as
failure mode 3 in dimension 11. a deny-list is a snapshot of what was known
to be sensitive at authoring time, and it says nothing at all about a field
introduced afterward under a different name or a different nesting level. A
team relying on a deny-list Content Filter as its sole data-minimization
control, with no automated schema-diff check watching for new, unreviewed
fields, should treat that as an active gap, not a settled control.

The filter specification itself can become an attack surface when it is not
fixed at deployment time but is instead derived, even partially, from
untrusted client input, as in the client-driven projection variant described
in dimension 8. A field-selection expression accepted from an API caller and
used naively, for instance evaluated directly as a path expression against a
live internal object graph rather than validated against a known,
authorization-aware schema, can allow a caller to request fields it should
never see, or in poorly bounded implementations to traverse into unintended
parts of the underlying data model. Any dynamic, caller-supplied field
selection must be validated against both a schema, so an unknown path is
rejected outright, and an authorization check scoped to that specific caller,
so a syntactically valid path the caller is nonetheless not permitted to see
is rejected as well. a schema check alone is not an authorization check.

Content Filter is also, deliberately, not a substitute for transport
security or access control. It removes data from a message body before that
message travels further. it does not encrypt the channel the filtered
message travels over, and it does not authenticate or authorize who is
allowed to read the filtered message once it arrives. Pairing a correctly
implemented Content Filter with an unencrypted channel, or with an
overly-permissive access policy on whatever store or system the filtered
message lands in, still leaves the retained fields, the ones the filter
deliberately kept because the intended consumer needs them, exposed to
anyone else with access to that channel or store.

Finally, because filtering is destructive by default, applying it before a
message reaches whatever archive or audit log is expected to satisfy a legal
hold, an incident investigation, or a regulatory retention requirement can
conflict directly with that requirement, permanently destroying the only
record of data that later turns out to have been needed. The correct
sequencing, named explicitly in dimension 13's discussion of Claim Check, is
to preserve the full, original message durably first, then apply Content
Filter only to whatever copy continues onward to a specific, narrower
consumer, never to filter the one and only copy that will ever exist.

## Code examples

Every example below implements the same scenario. an order message carrying
a customer's name, email, and government identifier, a card number and its
last four digits, an internal fraud note, and order totals, filtered down to
a public-facing view that keeps the order id, the customer's name, the line
items, the card's last four digits, and the totals, while dropping the
customer id, the email, the government identifier, the full card number, and
the internal note. All three samples were executed against the toolchain
available on this machine, `tsc --strict`, `python3`, and `go vet` plus
`go run`, and each one produced the filtered output shown below.

```typescript
type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue };
type JsonObject = { [key: string]: JsonValue };

class ContentFilter {
  private readonly paths: string[][];

  constructor(allowPaths: string[]) {
    this.paths = allowPaths.map((p) => p.split("."));
  }

  apply(message: JsonObject): JsonObject {
    const result: JsonObject = {};
    for (const keys of this.paths) {
      const value = getPath(message, keys);
      if (value !== undefined) setPath(result, keys, value);
    }
    return result;
  }
}

function getPath(obj: JsonValue, keys: string[]): JsonValue | undefined {
  if (keys.length === 0) return obj;
  if (obj === null || typeof obj !== "object" || Array.isArray(obj)) {
    return undefined;
  }
  const [head, ...rest] = keys;
  if (!(head in obj)) return undefined;
  return getPath(obj[head], rest);
}

function setPath(target: JsonObject, keys: string[], value: JsonValue): void {
  const [head, ...rest] = keys;
  if (rest.length === 0) {
    target[head] = value;
    return;
  }
  const child = target[head];
  if (typeof child !== "object" || child === null || Array.isArray(child)) {
    target[head] = {};
  }
  setPath(target[head] as JsonObject, rest, value);
}

const orderMessage: JsonObject = {
  orderId: "ORD-4471",
  customerId: "CUST-9001",
  customer: {
    name: "Amelia Reyes",
    email: "amelia@example.com",
    ssn: "078-05-1120",
  },
  items: [
    { sku: "WIDGET-1", qty: 2 },
    { sku: "WIDGET-9", qty: 1 },
  ],
  payment: { cardNumber: "4111111111111111", last4: "1111" },
  totals: { amount: 84.5, currency: "USD" },
  internalNotes: "flagged for manual fraud review",
};

const publicOrderFilter = new ContentFilter([
  "orderId",
  "customer.name",
  "items",
  "payment.last4",
  "totals.amount",
  "totals.currency",
]);

const filtered = publicOrderFilter.apply(orderMessage);
console.log(JSON.stringify(filtered, null, 2));
```

```python
from __future__ import annotations

from typing import Any

_MISSING = object()


class ContentFilter:
    def __init__(self, allow_paths: list[str]) -> None:
        self.paths = [p.split(".") for p in allow_paths]

    def apply(self, message: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for keys in self.paths:
            value = _get(message, keys)
            if value is not _MISSING:
                _set(result, keys, value)
        return result


def _get(obj: Any, keys: list[str]) -> Any:
    if not keys:
        return obj
    if not isinstance(obj, dict) or keys[0] not in obj:
        return _MISSING
    return _get(obj[keys[0]], keys[1:])


def _set(target: dict[str, Any], keys: list[str], value: Any) -> None:
    head, rest = keys[0], keys[1:]
    if not rest:
        target[head] = value
        return
    if not isinstance(target.get(head), dict):
        target[head] = {}
    _set(target[head], rest, value)


order_message: dict[str, Any] = {
    "order_id": "ORD-4471",
    "customer_id": "CUST-9001",
    "customer": {
        "name": "Amelia Reyes",
        "email": "amelia@example.com",
        "ssn": "078-05-1120",
    },
    "items": [
        {"sku": "WIDGET-1", "qty": 2},
        {"sku": "WIDGET-9", "qty": 1},
    ],
    "payment": {"card_number": "4111111111111111", "last4": "1111"},
    "totals": {"amount": 84.5, "currency": "USD"},
    "internal_notes": "flagged for manual fraud review",
}

public_order_filter = ContentFilter(
    [
        "order_id",
        "customer.name",
        "items",
        "payment.last4",
        "totals.amount",
        "totals.currency",
    ]
)

filtered = public_order_filter.apply(order_message)
assert "ssn" not in filtered["customer"]
assert "card_number" not in filtered["payment"]
assert "internal_notes" not in filtered
assert "customer_id" not in filtered
print(filtered)
```

```go
package main

import (
	"encoding/json"
	"fmt"
	"strings"
)

type ContentFilter struct {
	paths [][]string
}

func NewContentFilter(allowPaths []string) *ContentFilter {
	paths := make([][]string, 0, len(allowPaths))
	for _, p := range allowPaths {
		paths = append(paths, strings.Split(p, "."))
	}
	return &ContentFilter{paths: paths}
}

func (f *ContentFilter) Apply(message map[string]interface{}) map[string]interface{} {
	result := map[string]interface{}{}
	for _, keys := range f.paths {
		if value, ok := getPath(message, keys); ok {
			setPath(result, keys, value)
		}
	}
	return result
}

func getPath(obj interface{}, keys []string) (interface{}, bool) {
	if len(keys) == 0 {
		return obj, true
	}
	m, ok := obj.(map[string]interface{})
	if !ok {
		return nil, false
	}
	v, ok := m[keys[0]]
	if !ok {
		return nil, false
	}
	return getPath(v, keys[1:])
}

func setPath(target map[string]interface{}, keys []string, value interface{}) {
	head, rest := keys[0], keys[1:]
	if len(rest) == 0 {
		target[head] = value
		return
	}
	child, ok := target[head].(map[string]interface{})
	if !ok {
		child = map[string]interface{}{}
		target[head] = child
	}
	setPath(child, rest, value)
}

func main() {
	orderMessage := map[string]interface{}{
		"orderId":    "ORD-4471",
		"customerId": "CUST-9001",
		"customer": map[string]interface{}{
			"name":  "Amelia Reyes",
			"email": "amelia@example.com",
			"ssn":   "078-05-1120",
		},
		"items": []interface{}{
			map[string]interface{}{"sku": "WIDGET-1", "qty": 2},
			map[string]interface{}{"sku": "WIDGET-9", "qty": 1},
		},
		"payment": map[string]interface{}{
			"cardNumber": "4111111111111111",
			"last4":      "1111",
		},
		"totals":        map[string]interface{}{"amount": 84.5, "currency": "USD"},
		"internalNotes": "flagged for manual fraud review",
	}

	filter := NewContentFilter([]string{
		"orderId", "customer.name", "items",
		"payment.last4", "totals.amount", "totals.currency",
	})

	filtered := filter.Apply(orderMessage)
	out, _ := json.MarshalIndent(filtered, "", "  ")
	fmt.Println(string(out))
}
```

Java, Rust, and Swift were not included as fourth and fifth samples for this
entry, not because the pattern does not translate, it translates cleanly to
any language with structural data types, but because three languages already
demonstrate every implementation-relevant idea the pattern carries, a simple
recursive path get and set over a nested map, and a fourth or fifth sample
would repeat that same shape rather than reveal anything new about the
pattern itself.

## 18. References

1. Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns. Designing,
   Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003,
   Message Transformation chapter, Content Filter.
2. [Enterprise Integration Patterns, Content Filter](https://www.enterpriseintegrationpatterns.com/patterns/messaging/ContentFilter.html), verified 2026-08-02.
3. [Google Cloud, API System Parameters](https://docs.cloud.google.com/apis/docs/system-parameters), verified 2026-08-02.
4. [AWS, Amazon EventBridge input transformation](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-transform-target-input.html), verified 2026-08-02.
5. [Elastic, remove processor](https://www.elastic.co/guide/en/elasticsearch/reference/current/remove-processor.html), verified 2026-08-02.
6. [bazaarvoice/jolt, README](https://github.com/bazaarvoice/jolt), verified 2026-08-02.
7. [Spring Integration, Message Transformation](https://docs.spring.io/spring-integration/reference/message-transformation.html), verified 2026-08-02.
