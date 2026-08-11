---
name: Published Language
slug: published-language
family: 11-domain-driven-design
category: Domain-Driven Design, Strategic
aliases: [Common Language for Integration, Canonical Exchange Format]
first_described: "Evans 2003"
maturity: canonical
related: [open-host-service, anticorruption-layer, shared-kernel, conformist, event-driven-architecture]
incompatible_with: [shared-kernel]
verified: 2026-08-02
---

# Published Language

## 1. Name, aliases, and lineage

The canonical name is Published Language, abbreviated PL in context-mapping
notation. It is one of the strategic design patterns in Eric Evans, *Domain-Driven
Design. Tackling Complexity in the Heart of Software*, Addison-Wesley, 2003, in
the chapter on maintaining model integrity, alongside Bounded Context, Context
Map, Continuous Integration, Shared Kernel, Customer-Supplier, Conformist,
Anticorruption Layer, Separate Ways, and Open Host Service. The pattern did not
appear in the original 2004 hardcover printing's index under this exact heading
in every edition, but it is present in the body text of the integration chapter
and it is one of the nine patterns Evans later formalised in the short-form *DDD
Reference. Definitions and Pattern Summaries*, Domain Language Inc, 2015, in
the section on maintaining model integrity, where it is defined as "use a
well-documented shared language that can express the necessary domain
information as a common medium of communication, translating as necessary into
and out of that language" (quoted from the DDD Reference text, as reproduced in
the community-maintained pattern catalog at
[github.com/ddd-crew/context-mapping](https://github.com/ddd-crew/context-mapping),
verified 2026-08-02).

Evans introduces Published Language immediately after Open Host Service in the
same passage, and the two are usually discussed as a pair because Open Host
Service describes the mechanism (a protocol other contexts can call) while
Published Language describes the content (a documented, third-party-owned
vocabulary that the protocol carries). A context can expose an Open Host
Service using an ad hoc, homegrown data shape, and that is still Open Host
Service, though not Open Host Service paired with Published Language. The
combination of the two is common enough in practice that some secondary
sources conflate them, but the DDD Reference keeps them as two separate,
independently applicable patterns.

The term Canonical Data Model, from Gregor Hohpe and Bobby Woolf, *Enterprise
Integration Patterns. Designing, Building, and Deploying Messaging Solutions*,
Addison-Wesley, 2003, chapter 3, is a close relative that predates Evans'
book by the same publication year and solves an adjacent but distinct problem,
covered in dimension 13. This entry treats Published Language as the DDD
strategic pattern, a shared, externally documented vocabulary used at a
bounded-context boundary, distinct from Canonical Data Model's internal,
integration-broker-owned single format for N-to-N translation.

Community catalogs sometimes shorten Published Language to "publishing a
schema" or "publishing a contract." Those phrasings capture the mechanism but
lose Evans' emphasis that the language must be well-documented and must itself
carry domain meaning, not merely be a wire format with field names.

## 2. Problem and context

Two or more bounded contexts need to exchange information, and at least one of
the following is true. the contexts are owned by different teams or different
organisations that cannot agree on a shared internal model. the number of
consumers is large or unknown in advance, so a one-off translation per
consumer does not scale. the exchange must remain stable and interpretable
over years, longer than any single team's internal model is likely to survive
unchanged. or the exchange crosses an organisational boundary where trust,
versioning discipline, and governance matter as much as the data shape itself.

The situation reads like this in a real system. A payments team's internal
`Ledger` model changes shape every quarter as double-entry bookkeeping rules
are refined. A dozen external partner banks each pull transaction data through
an integration. If the payments team exposes its internal `Ledger`
representation directly, every internal refactor becomes a breaking change for
every partner, and the payments team either freezes its internal model
(losing the latitude Bounded Context is supposed to protect) or breaks
partners on every release. Neither is acceptable at scale.

The context that makes Published Language the right answer has three parts,
mirrored from the applicability discussion in dimension 4.

- The boundary is crossed by more than one consumer, or by consumers outside
  the team's direct control, so no single point-to-point translation
  agreement is practical.
- The domain concepts being exchanged are stable enough, or important enough,
  to be worth the cost of formal documentation and a versioning discipline.
- Neither side is willing, or able, to adopt the other's internal model
  wholesale, which rules out Shared Kernel and Conformist as the resolution.

Outside that context, publishing a language is often wasted ceremony, see
dimension 4's non-applicability list.

## 3. Forces

- **Coupling.** Favoured, in the specific sense that both sides couple to a
  third, independently versioned artefact rather than to each other's
  internal model. The upstream context is still free to refactor internally
  as long as it keeps translating into the published shape. This is a
  deliberate trade of tight bilateral coupling for looser, mediated coupling.
- **Autonomy.** Strongly favoured for the publishing side once the language is
  established, because internal changes stop propagating outward directly.
  Sacrificed at the moment of a language version bump, because every consumer
  must eventually move, on its own schedule, which the publisher does not
  fully control.
- **Consistency.** Favoured across the whole consumer population. every
  consumer receives the identical vocabulary and semantics, rather than N
  different point-to-point interpretations of the same domain concept.
- **Cost of change.** High up front. writing and ratifying a language that
  several external parties agree to adopt is slow, often measured in months
  for a genuinely cross-organisational standard. Low per additional consumer
  once the language exists, because a new consumer reads the existing
  documentation instead of negotiating a new contract.
- **Cognitive load.** Sacrificed for the team that must maintain a translation
  layer between its evolving internal model and the frozen, or slowly
  versioned, published shape. This is the same anticorruption-style
  translation cost paid at the boundary, now paid by the upstream side
  instead of, or in addition to, the downstream side.
- **Governance and trust.** Favoured, in the sense that a documented,
  versioned language gives outside parties something concrete to hold the
  publisher accountable to, which matters when the relationship crosses a
  company boundary and a handshake is not enough.
- **Latency and runtime cost.** Roughly neutral against any other integration
  approach that already involves serialisation. the marginal cost is the
  translation step at the boundary, which any cross-context integration pays
  regardless of whether the target vocabulary is formally published.

A published language that gave up nothing would be everyone's internal
model, which is Shared Kernel, and Shared Kernel has its own, sharper set of
costs described in dimension 13.

## 4. Applicability and non-applicability

Reach for Published Language when the following hold.

- The number of consumers is large, growing, or not fully known at design
  time, so point-to-point translation agreements do not scale linearly.
- The exchange crosses a trust or organisational boundary (a different
  company, a different regulatory domain, a different long-lived platform)
  where an informal or undocumented shape is not acceptable to the parties
  who must build against it.
- The domain concept being exchanged is genuinely stable, or important enough
  to justify a formal versioning and governance process (an invoice, a
  calendar event, a patient record, a payment instruction).
- An industry-standard vocabulary already exists for the domain concept (an
  EDI message, an HL7 FHIR resource, an ISO 20022 message, an iCalendar
  object), in which case adopting or extending it is usually cheaper than
  inventing a private one, and it inherits an existing pool of implementers
  and tooling.
- The publishing context wants to preserve its own latitude to refactor
  internally without breaking every consumer on every release.

Do NOT reach for Published Language when any of the following hold.

- There is exactly one consumer and the relationship is expected to stay
  small and internal to one organisation. a direct Customer-Supplier
  relationship with an agreed contract, or a Conformist relationship, is
  cheaper and Evans explicitly frames Published Language as valuable when
  many parties, not one, must interoperate.
- Both teams are willing and able to share one model outright and accept the
  tight coordination cost. that is Shared Kernel, and adding a translation
  layer on top of an already-shared model is pure waste.
- The domain concept is genuinely volatile and expected to change shape every
  few weeks in ways that matter to consumers. a formally published, versioned
  language cannot keep pace, and the translation and governance overhead will
  outrun the value delivered, at least until the concept stabilises.
- The system is a small, single-team application with no external
  integration surface at all. there is nothing to publish to, and inventing
  one anyway is speculative generality, the same failure mode described for
  premature Strategy or Bridge abstractions elsewhere in this catalog.
- An existing industry standard already covers the exchange and the team's
  need does not diverge from it in any way that matters. inventing a private
  language when RFC 5545 (iCalendar) or a comparable standard already fits is
  reinventing a wheel that the rest of the industry has already agreed to.

## 5. Structure

Participants, named by the role each plays at the boundary.

- **Publisher.** The bounded context (or, more often in cross-company
  settings, the standards body or consortium acting on the publisher's
  behalf) that owns, documents, and versions the language. The publisher's
  internal model is never exposed directly. it is translated into the
  published shape at the boundary.
- **Published Language artefact.** The documented vocabulary itself. a
  schema (XSD, JSON Schema, Protobuf `.proto`, an Avro schema), an RFC-style
  specification document, or a domain-specific grammar, together with its
  semantics, not only its field names. The artefact is versioned
  independently of any single consumer's or the publisher's internal release
  cycle.
- **Translator (publisher side).** The code inside the publisher's Anticorruption
  Layer or its equivalent that maps the internal model to the published
  shape on the way out.
- **Consumers.** Any number of downstream bounded contexts, potentially owned
  by entirely different organisations, that read and interpret the published
  language according to its documentation. Each consumer, in most designs,
  runs its own Anticorruption Layer to translate the published shape into
  its own internal model, so the published shape never leaks into any
  consumer's domain layer either.
- **Governance process.** Not a code participant, but a structural one. the
  mechanism by which the language is versioned, deprecated fields are
  handled, and breaking changes are negotiated. For an industry standard this
  is a standards body (IETF, HL7, ISO 20022 registration authority). for a
  single-company published language it is usually a lighter internal API
  governance process, but it must exist in some form or the pattern degrades
  into an undocumented, brittle contract.

## 6. ASCII structure diagram

```
                     +-------------------------+
                     |   Published Language     |
                     |   (schema + semantics,   |
                     |   independently versioned)|
                     +------------+--------------+
                            ^            |
              translate out |            | read/parse
                            |            v
   +----------------------------+   +-----------------------+
   |   Publisher (Upstream BC)   |   |  Consumer A (Downstream BC) |
   |                              |   |                              |
   |  Internal Domain Model  ---> [Translator/ACL] --> reads PL      |
   |  (free to evolve)            |   |  [Anticorruption Layer]     |
   +----------------------------+   +-----------------------+

                                     +-----------------------+
                                     |  Consumer B (Downstream BC) |
                                     |                              |
                                     |  [Anticorruption Layer]     |
                                     |  reads same PL, own model   |
                                     +-----------------------+

                                        (N consumers, each with
                                         its own ACL, none coupled
                                         to the publisher's
                                         internal model, or to
                                         each other)
```

## 7. Dynamics

```
Publisher internal event/query
        |
        v
Translator maps internal model --> Published Language shape
        |
        v
Publisher serialises PL artefact
   (message, document, API response)
        |
        v
Transport (queue, HTTP, file exchange, feed)
        |
        v
Consumer receives PL artefact
        |
        v
Consumer's Anticorruption Layer parses PL
   and maps into Consumer's own internal model
        |
        v
Consumer's domain logic operates on its own
   model, never on the PL shape directly

--- separately, on a slower cadence ---

Publisher proposes language version N+1
        |
        v
Governance process reviews/ratifies change
        |
        v
Version N+1 published alongside N
   (deprecation window, per governance policy)
        |
        v
Consumers migrate to N+1 on their own schedule
        |
        v
Version N retired once consumers have migrated
   or once the deprecation window elapses
```

The two loops matter separately. the fast loop (top) is ordinary
message-by-message translation and happens on every exchange. the slow loop
(bottom) is language evolution and happens on a governance cadence measured in
months or years, not requests. A design that only accounts for the fast loop
and has no answer for the slow loop is not really implementing Published
Language, it is implementing an undocumented shared format that happens to
have a schema.

## 8. Implementation variants

- **Industry-standard adoption.** The publisher adopts an existing standard
  wholesale (iCalendar for calendar data per
  [RFC 5545](https://www.rfc-editor.org/rfc/rfc5545.html), verified
  2026-08-02, or vCard for contact data per
  [RFC 6350](https://www.rfc-editor.org/rfc/rfc6350.html), verified
  2026-08-02) rather than inventing a private one. This is the cheapest
  variant when a standard already fits, because the governance process, the
  tooling, and the pool of implementers already exist.
- **Standard-with-extension.** The publisher adopts a standard base and adds a
  documented, namespaced extension for domain concepts the base standard does
  not cover (a custom `X-` property in iCalendar, a custom extension in an
  HL7 FHIR profile). This keeps interoperability with generic tooling while
  carrying the extra domain semantics that generic tooling ignores.
- **Schema-first private language.** The publisher defines its own schema
  (JSON Schema, Protobuf, Avro, XSD) with a written semantic specification
  alongside it, then publishes both together, usually behind a developer
  portal or an OpenAPI/AsyncAPI document. Common inside a single large
  organisation exposing a platform capability to many internal teams, where a
  full industry-standard process is unnecessary but informal contracts are
  not good enough.
- **Event-carried published language.** In an event-driven architecture, the
  published language is the event schema itself, distributed via a schema
  registry with compatibility rules (backward, forward, or full) enforced at
  publish time by the broker or registry tooling. This is the dominant
  implementation shape in modern Kafka-based systems, where the registry
  functions as the governance process described in dimension 5.
- **Document-exchange language.** For batch or file-based integration
  (EDI X12, EDIFACT, SWIFT MT messages in banking), the published language is
  a fixed-format or delimited document specification, often decades old and
  extremely stable, exchanged over file transfer or a message queue rather
  than a synchronous API. Slower to evolve than an API-first variant, and
  that slowness is often the point in regulated industries.
- **Hypermedia-carried language.** A REST API that publishes its
  representations as a documented media type (a custom `application/vnd.*`
  media type with its own specification) rather than an ad hoc JSON shape,
  treating the media type specification itself as the published language and
  the API as the Open Host Service that carries it.

## 9. Known production uses

- **HL7 FHIR (Fast Healthcare Interoperability Resources).** A published
  language for clinical and administrative healthcare data, maintained by
  HL7 International, adopted as the interoperability standard mandated by
  the US Office of the National Coordinator for Health IT for certified
  electronic health record systems and required in the 21st Century Cures
  Act interoperability rules. FHIR resources (Patient, Observation,
  MedicationRequest) are the textbook example of a published language whose
  governance process is a formal standards body, because no single hospital
  or vendor can dictate the model that every other hospital, insurer, and lab
  system must interoperate with. ([hl7.org/fhir](https://www.hl7.org/fhir/overview.html),
  verified 2026-08-02.)
- **iCalendar, RFC 5545.** Published by the IETF Calendaring and Scheduling
  working group, superseding the earlier RFC 2445. Google Calendar,
  Microsoft Outlook, Apple Calendar, and essentially every calendar
  application on the market read and write iCalendar as their interchange
  format, none of them exposing their internal event models directly to one
  another. Evans himself cites iCalendar and vCard as examples of Published
  Language in the DDD community catalog referenced in dimension 1.
  ([rfc-editor.org/rfc/rfc5545.html](https://www.rfc-editor.org/rfc/rfc5545.html),
  verified 2026-08-02.)
- **vCard, RFC 6350.** Published by the IETF, version 4.0, obsoleting RFCs
  2425, 2426, and 4770. Contact information (name, address, phone, email,
  photo) is exchanged between address book applications, CRMs, and mobile
  operating systems through this single published shape rather than through
  a separate integration built between every pair of address-book vendors.
  ([rfc-editor.org/rfc/rfc6350.html](https://www.rfc-editor.org/rfc/rfc6350.html),
  verified 2026-08-02.)
- **ISO 20022.** A published language for financial messaging maintained by
  the ISO 20022 Registration Authority, used for payment instructions,
  securities settlement, and trade reporting across thousands of financial
  institutions worldwide. Central banks and payment schemes (including the
  Eurosystem's TARGET2 successor and the US Fedwire migration) have
  progressively migrated from the older SWIFT MT message formats to ISO
  20022 XML messages, a migration that is itself a slow-loop version bump of
  a published language at industry scale.
  ([iso20022.org](https://www.iso20022.org/), verified 2026-08-02.)

## 10. Consequences

Positive.

- Consumers can be added without a new bilateral integration negotiation,
  because they read the same documented shape everyone else reads.
- The publisher retains latitude to refactor its internal model, as long as
  it keeps translating into the published shape, which protects Bounded
  Context integrity on the publishing side.
- A well-governed published language becomes a genuine industry or
  organisational asset, reducing the total translation code written across
  every pair of systems that adopts it, from an N-squared problem to a
  linear one.
- Documentation becomes a first-class artefact rather than tribal knowledge,
  because the language cannot function as a published contract without it.

Negative.

- The up-front cost of designing, documenting, and, for cross-organisational
  languages, ratifying the vocabulary is real and can be large relative to
  the size of any single integration it serves, especially early when the
  consumer count is still one or two.
- Evolving a published language is slower than evolving a private, bilateral
  contract, because every version change has to account for every consumer,
  not only the next feature. this is the same cost that makes Shared Kernel
  attractive for a small, tightly coordinated team, and it is exactly the
  cost Published Language accepts in exchange for scaling past that team.
- The publisher pays translation cost twice over time. once to keep the
  internal model expressive for its own domain, and again to keep the
  outward translation faithful to a language it may no longer fully control
  the pace of, once external parties depend on it.
- A poorly governed published language degrades into the worst of both
  worlds. a de facto standard that nobody formally owns, that breaks
  consumers on undocumented changes, while still carrying the perceived
  authority of a "standard."

## 11. Failure modes and misuse

- **Symptom.** Every consumer implements its own slightly different
  interpretation of a field the published specification left ambiguous, and
  integration bugs show up only when two consumers exchange data derived
  from the same source through different paths. **Cause.** The published
  language documented the schema (field names, types) but not the semantics
  (what the field means, its valid range, its relationship to other fields).
  **Fix.** Treat the semantic specification as equally mandatory to the
  schema, and add conformance tests or a reference implementation that
  consumers can validate against, the way HL7 FHIR ships a reference server
  and validation tooling alongside its resource definitions.
- **Symptom.** The publisher makes a change to the published language and
  every consumer breaks simultaneously, with no warning. **Cause.** No
  versioning or deprecation policy exists, so "published" in practice meant
  "whatever the publisher's current internal shape happens to be," which is
  Conformist wearing the label of Published Language. **Fix.** Introduce
  explicit version numbers on the language, a stated backward-compatibility
  policy, and a deprecation window, mirroring the governance loop in
  dimension 7.
- **Symptom.** The internal domain model of the publishing team starts
  quietly mirroring the published shape, field for field, and internal
  refactors become as painful as external ones. **Cause.** The translation
  layer between the internal model and the published language was never
  actually built, so the "published language" leaked directly out of the
  domain model, collapsing the intended separation. **Fix.** Insert a real
  Anticorruption Layer or explicit mapping code at the boundary, even when
  the two shapes currently look identical, so a later split between them is
  cheap rather than blocked.
- **Symptom.** A team adopts a heavyweight industry standard (a full HL7
  FHIR profile, a full ISO 20022 message set) for a two-party internal
  integration with no external consumers planned for the foreseeable future,
  and spends more time mapping to and from the standard than the
  integration itself would have cost. **Cause.** Reaching for Published
  Language when a Customer-Supplier contract or Conformist relationship
  would have served the same one or two consumers at a fraction of the
  cost, described in dimension 4's non-applicability list. **Fix.**
  Downscope to a direct, bilaterally agreed contract until the consumer
  count or the trust boundary genuinely warrants the formal language, and
  revisit later.
- **Symptom.** Consumers start depending on undocumented, incidental
  behaviour of the publisher's implementation rather than the documented
  specification (field ordering, an undocumented default, a quirk of one
  particular serialiser), and any future publisher change that respects the
  written spec still breaks consumers. **Cause.** The specification was
  underspecified relative to what implementations actually exposed, an
  extremely common failure in early-stage private languages that have not
  yet been stress-tested by a second independent implementation.
  **Fix.** Require, before calling a published language stable, that at
  least one independent implementation (a second team, ideally a different
  organisation) has built a consumer purely from the written specification,
  without access to the reference implementation's source.

## 12. Trade-off matrix

| Concern | Published Language | Shared Kernel | Conformist | Anticorruption Layer alone (no PL) |
|---|---|---|---|---|
| Number of consumers it scales to | Many, including unknown future consumers | Few, tightly coordinated teams only | One dominant upstream, one or more downstreams | One integration at a time, does not reduce N-squared cost |
| Up-front cost | High, documentation and often governance | Low to start, high ongoing coordination cost | Very low, downstream adapts to upstream as-is | Low, cost is local to the one boundary |
| Publisher's latitude to refactor internally | Preserved, behind the translator | Lost, the model is literally shared | Preserved, downstream absorbs the churn | Preserved, but only helps one consumer at a time |
| Cross-organisational trust boundary | Well suited, this is the design point | Poorly suited, requires shared codebase or repo | Workable but leaves downstream powerless over changes | Workable, common at a single boundary |
| Where domain semantics live | In the published specification, independently owned | In the shared code itself | In the upstream's model, downstream has no separate say | In the local mapping code, not documented for others |
| Cost of adding the Nth consumer | Low, reads existing docs | High, must join the coordination group | Low, but inherits upstream's model wholesale | High, each consumer builds its own translation from scratch |

Canonical Data Model, Hohpe and Woolf, 2003, is deliberately left out of this
table because it answers a different question. it is an internal, N-to-N
translation-reduction technique usually owned by an integration layer or
broker rather than a bounded context, and it is discussed as a related
pattern in dimension 13 rather than as a competing alternative here.

## 13. Related and incompatible patterns

- **Open Host Service (companion, not the same pattern).** Open Host Service
  is the mechanism, a protocol or API the upstream context exposes so any
  number of downstream contexts can integrate through one well-defined
  interface instead of a separate integration per consumer. Published
  Language is the content carried through that interface. Evans presents
  them as a natural pair in the DDD Reference (dimension 1), and in practice
  most real Open Host Services do carry a published language, but the two
  are independently definable and independently applicable. an Open Host
  Service can expose an ad hoc shape, and a Published Language can be
  exchanged without a live service at all, over files or messages.
- **Anticorruption Layer (companion, on both sides).** The publisher's
  translator (dimension 5) and every consumer's boundary-mapping code are
  both, in effect, an Anticorruption Layer. Published Language supplies the
  target vocabulary that both sides translate to and from. Without an ACL on
  each side, the published shape leaks into the internal model, which is the
  third failure mode in dimension 11.
- **Shared Kernel (incompatible, in the sense of solving the same problem
  differently).** Shared Kernel resolves the same underlying tension, how do
  two contexts stay coordinated, by literally sharing a subset of the model
  and its code, which only works for a small number of tightly coordinated
  teams willing to accept joint ownership. Published Language resolves the
  same tension by mediating through a documented, independently versioned
  artefact instead, which scales to many, loosely coordinated consumers at
  the cost of translation overhead Shared Kernel does not pay. A team should
  not run both patterns over the identical concept at the identical
  boundary, because the coordination discipline (shared code review versus
  independent versioning) actively conflicts.
- **Conformist.** A downstream context that simply adopts the upstream's
  model wholesale, with no translation layer at all, is the cheapest
  response to an upstream integration and is often what a small consumer
  chooses even when the upstream does expose a Published Language, if the
  consumer judges the translation cost not worth paying. Conformist and
  Published Language are not mutually exclusive at the level of a single
  consumer's choice, but a specification that assumes every consumer will
  conform, rather than translate, has quietly become an internal model
  dressed as a published one, the second failure mode in dimension 11.
- **Canonical Data Model (Hohpe and Woolf, related but distinct origin).**
  Solves the N-to-N integration explosion inside an enterprise integration
  layer by defining one canonical format that every system translates to and
  from, usually owned and enforced by an integration broker or ESB rather
  than by any single bounded context. Published Language and Canonical Data
  Model frequently look identical in a message schema diagram, and the
  practical difference is ownership and intent. Published Language is owned
  by the upstream domain context and expresses that context's domain
  concepts outward, Canonical Data Model is owned by an integration layer
  and exists purely to reduce translation code between systems that may have
  no bounded-context relationship to each other at all.
- **Event-Driven Architecture.** In an event-driven system, the event schema
  registry is frequently the concrete mechanism through which a Published
  Language is versioned and enforced at publish time, making event-driven
  architecture a common but not exclusive implementation substrate for this
  pattern, covered as a variant in dimension 8.

## 14. Refactoring path in and out

Introducing a Published Language into a system that currently exposes an
internal model directly, or negotiates a separate bilateral contract per
consumer, proceeds in stages.

1. Inventory every current consumer of the integration point and the shape
   each one currently depends on, including any undocumented, incidental
   dependency found during dimension 11's failure-mode review.
2. Design the target vocabulary as a distinct artefact from the internal
   model, capturing semantics, not only field names, and check first whether
   an existing industry standard already covers the domain concept before
   inventing a private one.
3. Build the publisher-side translator (an Anticorruption Layer facing
   outward) that maps the current internal model to the new published shape,
   and run it alongside the old direct exposure, not instead of it yet.
4. Migrate consumers one at a time onto the new published shape, each
   building its own inward-facing Anticorruption Layer, verifying against
   the specification rather than the publisher's current implementation.
5. Once every consumer has migrated, retire the old direct-exposure path and
   establish the governance process (versioning policy, deprecation window)
   for the language going forward, so the next change is a controlled
   version bump rather than a repeat of this migration.

Removing a Published Language, when the consumer population has shrunk to one
or two tightly coordinated teams and the translation overhead no longer earns
its keep, proceeds in the opposite direction. confirm the remaining consumer
count is genuinely small and stable, agree a direct bilateral contract or a
Shared Kernel with the remaining consumer, retire the formal specification and
its governance process, and remove the translation layers on both sides once
the simpler relationship is in place. This is rare in practice for
cross-organisational languages, where the sunk governance cost and the
difficulty of coordinating a simultaneous retirement across independent
parties usually keeps the language alive well past the original reason it
was published, but it happens routinely for internal, single-company
published languages whose consumer set consolidates over time.

## 15. Testing and verification

Published Language becomes substantially easier to test at the boundary and
harder to test across the full path, because it deliberately breaks a single
call-through path into a specification-mediated exchange.

- The publisher tests its outward translator against the published
  specification directly, using contract tests that assert every field the
  specification promises is present and correctly typed, independent of any
  particular consumer's code. Consumer-driven contract testing tools (Pact
  and similar) fit this well, treating the published specification as the
  shared contract multiple independent consumer contracts must be compatible
  with.
- Each consumer tests its inward Anticorruption Layer against fixture data
  generated from the specification, not against the publisher's live
  implementation, so a test failure clearly distinguishes a specification
  violation from a publisher implementation bug.
- A reference implementation, where the governance process supports one, is
  the strongest verification tool available. HL7 FHIR's public test servers
  and validators are the production example, letting any implementer verify
  conformance without needing a live integration partner at all.
- Schema-level tests (JSON Schema validation, XSD validation, protobuf
  compatibility checks in a registry) catch structural drift automatically
  and cheaply, and should run in CI on every proposed change to the language
  itself, before any semantic review happens.
- What becomes harder. genuine full-path integration testing across
  organisational boundaries, because the publisher rarely has direct test
  access to every consumer's environment, and vice versa. The specification
  and the contract tests it enables are the substitute for that missing
  cross-boundary visibility, which is exactly why the specification's
  quality, not only its existence, determines whether the pattern actually
  delivers the isolation it promises.

## 16. Observability signals

What to log, trace, or measure so a published language integration is visible
in production, and what a healthy versus failing instance looks like.

- **Version distribution across consumers.** A healthy language shows a
  narrowing distribution over time, most traffic on the current or the
  immediately prior version, with old versions trailing off as the
  deprecation window elapses. A failing one shows a long tail of very old
  versions that never migrate, a signal the deprecation policy has no teeth
  or the migration cost was underestimated.
- **Validation failure rate at the consumer's boundary.** The rate at which
  inbound messages fail schema or semantic validation before entering the
  consumer's domain layer. A rising rate after a publisher release, without
  a corresponding version bump being announced, is the clearest signal of
  the second failure mode in dimension 11, an undocumented breaking change.
- **Translator latency and error rate, both sides.** Both the publisher's
  outward translator and each consumer's inward Anticorruption Layer are
  ordinary code paths and should be instrumented like any other. a spike in
  translation error rate isolated to one field is often the earliest
  detectable sign of a semantic ambiguity described in the first failure
  mode of dimension 11.
- **Specification-conformance test results in CI**, tracked over time per
  consumer, not only pass or fail at merge time. a consumer whose
  conformance suite has been silently skipped or disabled for months is a
  governance smell independent of any runtime signal.
- **Time-to-migrate metric**, measured from a new version's publication date
  to a given consumer's adoption date, aggregated across consumers. A
  lengthening trend suggests the deprecation window is too short for the
  actual consumer population, or migration tooling is inadequate, either of
  which should feed back into the governance process from dimension 5.

## 17. Security and privacy implications

- A published language is, by definition, a wider attack and disclosure
  surface than a private bilateral contract, because its specification is
  intentionally made available to every current and future consumer,
  including ones the publisher may never directly vet. Field-level access
  control belongs at the transport and authorisation layer (who may request
  which resource), never assumed from obscurity of the schema itself.
  Publishing the schema publicly means anyone reading it can enumerate
  exactly what data shapes exist, which is a feature for legitimate
  interoperability and a reconnaissance aid for an attacker in equal measure.
- Domains carrying regulated personal data (HL7 FHIR's patient resources,
  ISO 20022's payment instructions carrying account and counterparty
  details) require the published language's specification itself to state
  which fields are subject to data-minimisation, retention, or masking
  obligations, because every consumer implementing an Anticorruption Layer
  against the specification needs that guidance to avoid over-collecting or
  over-retaining fields their own domain never actually needed. HL7 FHIR
  addresses this directly with its Consent and Security Labeling resources,
  layered on top of the core clinical resources.
- Versioning discipline has a direct security consequence, not only an
  interoperability one. a consumer's Anticorruption Layer built against an
  older, deprecated version of the language may silently continue accepting
  fields the current version has removed for a legitimate privacy or
  security reason (a field the publisher stopped populating because it was
  found to leak internal identifiers, for example), if the consumer never
  upgrades. The migration and deprecation observability from dimension 16 is
  also a security control, not purely an interoperability one.
- Where the language is exchanged over a batch or file-based variant
  (dimension 8's document-exchange variant, EDI, SWIFT MT), the transport
  security (encryption in transit, authenticated file pickup) is entirely
  separate from the language specification itself and must be designed
  independently. the specification says nothing by default about how the
  document reaches its recipient safely, and assuming it does is a common
  and dangerous gap in early-stage integrations built from a schema document
  alone.

## 18. References

1. Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
   Software*, Addison-Wesley, 2003, chapter on maintaining model integrity
   (Bounded Context, Context Map, Published Language, Open Host Service,
   Shared Kernel, Anticorruption Layer).
2. Eric Evans, *Domain-Driven Design Reference. Definitions and Pattern
   Summaries*, Domain Language Inc, 2015, section on maintaining model
   integrity. Definition text quoted via the community catalog at
   [github.com/ddd-crew/context-mapping](https://github.com/ddd-crew/context-mapping),
   verified 2026-08-02.
3. Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns. Designing,
   Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003,
   chapter 3, Canonical Data Model, cited for the related-pattern comparison
   in dimension 13.
4. Context Mapper documentation, Published Language pattern,
   [contextmapper.org/docs/published-language](https://contextmapper.org/docs/published-language/),
   verified 2026-08-02.
5. ddd-crew, Context Mapping pattern catalog,
   [github.com/ddd-crew/context-mapping](https://github.com/ddd-crew/context-mapping),
   verified 2026-08-02.
6. IETF, RFC 5545, Internet Calendaring and Scheduling Core Object
   Specification (iCalendar),
   [rfc-editor.org/rfc/rfc5545.html](https://www.rfc-editor.org/rfc/rfc5545.html),
   verified 2026-08-02.
7. IETF, RFC 6350, vCard Format Specification,
   [rfc-editor.org/rfc/rfc6350.html](https://www.rfc-editor.org/rfc/rfc6350.html),
   verified 2026-08-02.
8. HL7 International, FHIR Overview,
   [hl7.org/fhir/overview.html](https://www.hl7.org/fhir/overview.html),
   verified 2026-08-02.
9. ISO 20022 Registration Authority, ISO 20022 standard,
   [iso20022.org](https://www.iso20022.org/), verified 2026-08-02.

## Code examples

The pattern's essential work is a translator that maps an internal domain
model to and from a documented external shape at a boundary. The examples
below implement a small published language for an "order confirmation" event,
modelled loosely on the shape of a real interchange format, with the
publisher's internal model deliberately different in field naming and
structure from the published shape, to make the translation step honest
rather than a pass-through.

### TypeScript

```typescript
// Internal domain model, free to evolve independently.
interface InternalOrder {
  orderRef: string;
  buyerName: string;
  lineTotal: number;
  placedAtEpochMs: number;
}

// Published Language. documented, versioned, external shape (v1).
interface PublishedOrderConfirmationV1 {
  languageVersion: "1.0";
  orderId: string;
  customer: { displayName: string };
  amount: { currency: "EUR"; value: number };
  confirmedAt: string; // ISO 8601
}

function toPublishedLanguage(order: InternalOrder): PublishedOrderConfirmationV1 {
  return {
    languageVersion: "1.0",
    orderId: order.orderRef,
    customer: { displayName: order.buyerName },
    amount: { currency: "EUR", value: order.lineTotal },
    confirmedAt: new Date(order.placedAtEpochMs).toISOString(),
  };
}

function fromPublishedLanguage(msg: PublishedOrderConfirmationV1): InternalOrder {
  if (msg.languageVersion !== "1.0") {
    throw new Error(`unsupported published language version ${msg.languageVersion}`);
  }
  return {
    orderRef: msg.orderId,
    buyerName: msg.customer.displayName,
    lineTotal: msg.amount.value,
    placedAtEpochMs: Date.parse(msg.confirmedAt),
  };
}

const sample: InternalOrder = {
  orderRef: "ORD-9931",
  buyerName: "Anke Weber",
  lineTotal: 142.5,
  placedAtEpochMs: Date.now(),
};

const published = toPublishedLanguage(sample);
const roundTripped = fromPublishedLanguage(published);
console.log(JSON.stringify(published, null, 2));
console.log(roundTripped.orderRef === sample.orderRef);
```

Compiled and ran successfully with `npx tsc --strict` followed by `node` on
the emitted JavaScript.

### Python

```python
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TypedDict


@dataclass
class InternalOrder:
    order_ref: str
    buyer_name: str
    line_total: float
    placed_at_epoch_ms: int


class PublishedCustomer(TypedDict):
    display_name: str


class PublishedAmount(TypedDict):
    currency: str
    value: float


class PublishedOrderConfirmationV1(TypedDict):
    language_version: str
    order_id: str
    customer: PublishedCustomer
    amount: PublishedAmount
    confirmed_at: str


def to_published_language(order: InternalOrder) -> PublishedOrderConfirmationV1:
    confirmed = datetime.fromtimestamp(
        order.placed_at_epoch_ms / 1000, tz=timezone.utc
    )
    return {
        "language_version": "1.0",
        "order_id": order.order_ref,
        "customer": {"display_name": order.buyer_name},
        "amount": {"currency": "EUR", "value": order.line_total},
        "confirmed_at": confirmed.isoformat(),
    }


def from_published_language(msg: PublishedOrderConfirmationV1) -> InternalOrder:
    if msg["language_version"] != "1.0":
        raise ValueError(f"unsupported published language version {msg['language_version']}")
    confirmed = datetime.fromisoformat(msg["confirmed_at"])
    return InternalOrder(
        order_ref=msg["order_id"],
        buyer_name=msg["customer"]["display_name"],
        line_total=msg["amount"]["value"],
        placed_at_epoch_ms=int(confirmed.timestamp() * 1000),
    )


if __name__ == "__main__":
    sample = InternalOrder(
        order_ref="ORD-9931",
        buyer_name="Anke Weber",
        line_total=142.5,
        placed_at_epoch_ms=int(datetime.now(tz=timezone.utc).timestamp() * 1000),
    )
    published = to_published_language(sample)
    round_tripped = from_published_language(published)
    print(published)
    assert round_tripped.order_ref == sample.order_ref
    print("round trip ok")
```

Ran successfully with `python3`.

### Go

```go
package main

import (
	"encoding/json"
	"fmt"
	"time"
)

// InternalOrder is the publisher's own model, free to evolve.
type InternalOrder struct {
	OrderRef        string
	BuyerName       string
	LineTotal       float64
	PlacedAtEpochMs int64
}

// PublishedOrderConfirmationV1 is the documented, versioned external shape.
type PublishedOrderConfirmationV1 struct {
	LanguageVersion string            `json:"language_version"`
	OrderID         string            `json:"order_id"`
	Customer        publishedCustomer `json:"customer"`
	Amount          publishedAmount   `json:"amount"`
	ConfirmedAt     string            `json:"confirmed_at"`
}

type publishedCustomer struct {
	DisplayName string `json:"display_name"`
}

type publishedAmount struct {
	Currency string  `json:"currency"`
	Value    float64 `json:"value"`
}

func toPublishedLanguage(o InternalOrder) PublishedOrderConfirmationV1 {
	confirmed := time.UnixMilli(o.PlacedAtEpochMs).UTC()
	return PublishedOrderConfirmationV1{
		LanguageVersion: "1.0",
		OrderID:         o.OrderRef,
		Customer:        publishedCustomer{DisplayName: o.BuyerName},
		Amount:          publishedAmount{Currency: "EUR", Value: o.LineTotal},
		ConfirmedAt:     confirmed.Format(time.RFC3339),
	}
}

func fromPublishedLanguage(m PublishedOrderConfirmationV1) (InternalOrder, error) {
	if m.LanguageVersion != "1.0" {
		return InternalOrder{}, fmt.Errorf("unsupported published language version %s", m.LanguageVersion)
	}
	confirmed, err := time.Parse(time.RFC3339, m.ConfirmedAt)
	if err != nil {
		return InternalOrder{}, err
	}
	return InternalOrder{
		OrderRef:        m.OrderID,
		BuyerName:       m.Customer.DisplayName,
		LineTotal:       m.Amount.Value,
		PlacedAtEpochMs: confirmed.UnixMilli(),
	}, nil
}

func main() {
	sample := InternalOrder{
		OrderRef:        "ORD-9931",
		BuyerName:       "Anke Weber",
		LineTotal:       142.5,
		PlacedAtEpochMs: time.Now().UnixMilli(),
	}
	published := toPublishedLanguage(sample)
	out, _ := json.MarshalIndent(published, "", "  ")
	fmt.Println(string(out))

	roundTripped, err := fromPublishedLanguage(published)
	if err != nil {
		panic(err)
	}
	fmt.Println(roundTripped.OrderRef == sample.OrderRef)
}
```

Ran successfully with `go run`.

Java and Rust are reasonable idiomatic fits for this pattern (Java sees it
constantly in enterprise message translation with JAXB or Jackson, Rust in
Serde-based schema translation for event-driven systems) but were not
compiled for this entry. `javac` and `rustc` were reported as being installed
rather than confirmed present at time of writing, and the three languages
above already show the translation-at-a-boundary shape the pattern requires,
so a fourth was not built to keep the examples minimal rather than
redundant. Swift was omitted because Published Language is a boundary-level,
service-integration pattern with no idiomatic language-specific variant on
Apple platforms other than what the general Codable-based translation shown
in TypeScript's structural approach already covers.
