---
name: Anticorruption Layer
slug: anticorruption-layer
family: 11-domain-driven-design
category: Integration
aliases: [ACL, Anti-Corruption Layer, Translation Layer]
first_described: "Eric Evans 2003"
maturity: canonical
related: [bounded-context, context-map, conformist, customer-supplier, shared-kernel, adapter, facade, strangler-fig]
incompatible_with: [shared-kernel]
verified: 2026-08-02
---

# Anticorruption Layer

## 1. Name, aliases, and lineage

The canonical name is Anticorruption Layer, commonly abbreviated ACL and also
written as Anti-Corruption Layer with hyphens. Eric Evans first described it in
*Domain-Driven Design. Tackling Complexity in the Heart of Software*,
Addison-Wesley, 2003, Chapter 14, "Maintaining Model Integrity," in the section
titled "ANTICORRUPTION LAYER." Evans placed it inside a family of integration
patterns for relating Bounded Contexts, alongside Shared Kernel,
Customer-Supplier, Conformist, and Separate Ways.

Vaughn Vernon revisited the pattern a decade later in *Implementing
Domain-Driven Design*, Addison-Wesley, 2013, Chapter 13, "Integrating Bounded
Contexts," in the section "Implementing the REST Client Using an
Anticorruption Layer," page 463. Vernon's treatment is notable because it moves
the pattern out of the abstract and into a concrete worked example built from a
Facade, an Adapter, and a set of Translators wired together over a RESTful
resource client, which is the shape most practitioners now reach for.

Microsoft's Azure Architecture Center republished the pattern under the name
Anti-Corruption Layer Pattern as one of its catalogued cloud design patterns,
crediting Evans directly. "Eric Evans first described this pattern in
*Domain-Driven Design. Tackling Complexity in the Heart of Software*."
(<https://learn.microsoft.com/en-us/azure/architecture/patterns/anti-corruption-layer>,
verified 2026-08-02). The Azure Architecture Center article is useful evidence
that the pattern travelled from a domain-modelling book into mainstream cloud
architecture vocabulary without being renamed.

The name itself is a metaphor Evans chose deliberately. A model is a set of
concepts and rules a team agrees to hold consistent. A second system, whether a
legacy application, a vendor API, or another team's Bounded Context, carries
its own concepts and rules. Where the two touch, the pressure runs one way, the
foreign model tends to leak into the local one through the path of least
resistance, a shared field name, a shared enum, a shared assumption about what
null means. Evans named the defensive structure after what it prevents, not
after what it is built from, which is why the pattern reads as a stance before
it reads as a design.

## 2. Problem and context

A team owns a domain model they have deliberately shaped to match the
Ubiquitous Language of their Bounded Context, see
`patterns/11-domain-driven-design/ubiquitous-language.md` and
`patterns/11-domain-driven-design/bounded-context.md`. That model must exchange data with
another system whose model was shaped by a different team, a different era, or
a different vendor, and was never designed to agree with the local one.

The situation shows up in three recurring shapes.

- **Legacy integration.** A new service is being built to eventually replace a
  legacy system, but for a transition period both must operate, and the new
  service still needs data the legacy system owns. The legacy schema was
  designed under constraints, technology, requirements, staffing, that no
  longer hold, and its data model reflects years of accumulated compromise
  rather than the domain as currently understood.
- **Third-party or vendor integration.** An external API, a payment processor,
  a shipping carrier, a CRM, exposes a model that reflects that vendor's
  product decisions, not the calling team's domain. The vendor's `Customer`
  object might conflate what the calling team treats as two distinct concepts,
  a billing account and a person, because the vendor never needed to
  distinguish them.
- **Cross-team integration inside one organisation.** Two Bounded Contexts
  inside the same company, built by different teams, each with a coherent
  internal model, need to exchange information, and neither model was
  designed with the other in mind. This is the case the Customer-Supplier and
  Conformist relationships in `patterns/11-domain-driven-design/context-map.md` also address,
  and Anticorruption Layer is the choice when the downstream team has neither
  the standing nor the willingness to adopt the upstream team's model
  wholesale, see `patterns/11-domain-driven-design/conformist.md`.

In all three shapes the naive move is to let the foreign model's types, field
names, and invariants flow straight through the boundary and into the domain
layer, because that is the fastest way to get data moving. Evans's argument is
that this fastest path is also the one that eventually destroys the local
model, because every place the foreign type appears becomes a place where the
local model must accommodate a concept it did not choose. The Anticorruption
Layer exists to stop that leak at the boundary, once, in one place, rather than
at every call site that touches the foreign system.

## 3. Forces

The pattern trades several concrete forces against each other. Which side wins
depends on the concrete integration, and the pattern only pays for itself when
the forces genuinely favour it, see dimension 4.

- **Model purity versus integration cost.** Favours purity. The local domain
  model stays shaped by its own Ubiquitous Language, but the cost is a
  translation layer that must be written, tested, and kept synchronised with
  both sides as they evolve.
- **Coupling direction.** Favours decoupling the domain from the foreign
  system's release schedule and technology. Without an ACL, a schema change in
  the legacy system or a breaking change in a vendor API ripples directly into
  domain logic. With an ACL, the ripple stops at the translation layer, and
  only the translator needs to change.
- **Latency and operability.** Sacrificed to some degree. Every translated call
  crosses an extra hop, at minimum a function call, at worst a network call if
  the ACL runs as its own service. The Azure Architecture Center names this
  cost directly, "The anti-corruption layer adds latency to calls between the
  two systems," and adds that the layer itself becomes something you must
  deploy, scale, and monitor.
  (<https://learn.microsoft.com/en-us/azure/architecture/patterns/anti-corruption-layer>,
  verified 2026-08-02).
- **Development cost versus long-term maintainability.** Sacrificed up front,
  gained later. Building the translators, the anti-corruption tests, and the
  facade takes real engineering time before any domain feature ships. The
  payoff shows up months later, when the legacy system changes and only one
  file needs updating instead of every consumer of the foreign type.
- **Organisational trust and negotiating power.** This force is not covered
  well by most catalog descriptions, but it decides whether Anticorruption
  Layer, Conformist, or Customer-Supplier is the right relationship on a
  Context Map, see `patterns/11-domain-driven-design/context-map.md`. When the downstream team
  cannot influence the upstream model, either because it is a vendor, a legacy
  system with no active owner, or an upstream team that will not
  collaborate, an ACL is close to mandatory. When the two teams can negotiate
  a shared published contract, a lighter Open Host Service and Published
  Language relationship, or a Customer-Supplier relationship with real
  upstream accountability, may cost less than a full translation layer.

## 4. Applicability and non-applicability

Reach for an Anticorruption Layer when the following hold together.

- The domain model on the protected side is actively developed and its
  conceptual integrity matters, a supporting or legacy service with no
  intention of further investment does not need protecting.
- The foreign system's model genuinely conflicts with the local model, not
  merely uses different names for the same concepts. A field rename is not
  worth an ACL. A different aggregate boundary, a different notion of what a
  valid state is, or a different lifecycle for what looks like the same
  entity, is.
- The team does not control, or cannot economically influence, the foreign
  model. This includes vendor APIs, legacy systems slated for eventual
  replacement, and upstream teams unwilling to accommodate the downstream
  team's needs, the Conformist and Customer-Supplier relationships in
  `patterns/11-domain-driven-design/context-map.md` cover the alternative postures when this
  condition does not hold.
- The integration is expected to persist long enough, or matter enough, to
  justify writing and maintaining a translation layer instead of accepting the
  coupling. Michelin's migration used the pattern specifically because the
  legacy and modern systems needed to run in parallel for an extended
  transition (<https://blogit.michelin.io/anti-corruption-layer/>, verified
  2026-08-02).

Do NOT reach for an Anticorruption Layer in these situations.

- **The two models genuinely agree, or agreement is achievable at low cost.**
  If a shared model across two Bounded Contexts is not only possible but
  actually cheaper to maintain than two models plus a translator, Shared
  Kernel is the correct relationship, see `patterns/11-domain-driven-design/shared-kernel.md`.
  Building an ACL to translate between two models that could simply be one
  model is pure overhead with no protective benefit, and it is incompatible
  with a Shared Kernel relationship for exactly this reason, the two patterns
  express opposite answers to whether the models should converge.
- **The downstream side has no real domain model to protect.** A thin
  reporting service, a CRUD proxy, or a component that only reads and
  re-displays foreign data without applying its own business rules gains
  nothing from a translation layer, because there is no local conceptual
  integrity at risk. Adopting the upstream model directly, the Conformist
  relationship, is cheaper and honestly reflects the situation, see
  `patterns/11-domain-driven-design/conformist.md`.
- **The integration is short-lived by design.** A one-off data migration
  script that runs once and is deleted does not need the ongoing maintenance
  investment an ACL represents. A single Adapter or a throwaway mapping
  function is enough.
- **The team lacks the capacity to own the layer over time.** An ACL that
  nobody maintains rots into exactly the corruption it was built to prevent,
  because a stale translator silently mistranslates as both sides drift. If
  there is no owner for the layer, the pattern will cost more than the
  problem it claims to solve.
- **Real-time, extremely latency-sensitive paths where the translation cost
  itself is the bottleneck.** The Azure Architecture Center explicitly flags
  added latency as a cost of the pattern (verified 2026-08-02, URL above).
  When a call path has a hard microsecond budget, a translation hop, however
  thin, may not be affordable, and a narrower point-of-use Adapter without a
  dedicated service boundary is often the better trade.

## 5. Structure

The pattern is not one class, it is a small assembly of roles, matching the
shape Vernon made explicit and the shape the Azure Architecture Center
diagrams. Every serious implementation names these participants even when the
names in code differ.

- **Client, or Downstream Model.** The domain code inside the protected
  Bounded Context. It calls the ACL's public interface using only its own
  domain types and never sees a foreign type.
- **Facade.** The single entry point the client calls. Its job is to present a
  clean interface shaped by the downstream domain's needs, hiding the
  existence of the foreign system, its transport, and its authentication
  behind method signatures the domain would have chosen for itself.
- **Adapter.** Sits behind the Facade and knows how to actually talk to the
  foreign system, HTTP client details, message queue bindings, database
  connection details, retry and timeout policy. It receives a request in the
  Facade's terms and forwards it in whatever form the foreign system expects.
- **Translator.** Converts the foreign system's response, its data transfer
  objects or wire payloads, into the downstream domain's own types. This is
  where the real anticorruption work happens, and it is usually the part of
  the layer that grows and changes most, because it is where every
  discrepancy between the two models gets resolved explicitly, in one place,
  rather than implicitly, in many places.
- **Foreign Model, or Upstream System.** The legacy application, vendor API,
  or upstream Bounded Context the ACL protects the domain from. It is treated
  as a black box whose internal representation must never cross the boundary
  unconverted.

Two supporting participants appear in most production implementations even
though the classic write-ups understate them.

- **Anticorruption tests, or Contract Tests.** A test suite that exercises the
  ACL against the real foreign system, or a recorded fixture of its actual
  responses, so a change on the foreign side is caught at the boundary instead
  of surfacing as a subtle domain bug. Michael Feathers's *Working
  Effectively with Legacy Code* describes this class of test as a way to pin
  the current behaviour of code you do not fully trust, and the same
  discipline applies to an external system you do not control.
- **Correlation and Observability hooks.** Because the ACL sits on the one
  path every cross-boundary call must take, it is the natural place to attach
  correlation IDs, structured logging of translation failures, and metrics,
  see dimension 16.

## 6. ASCII structure diagram

```
                         Bounded Context (protected domain)
   +----------------------------------------------------------------+
   |                                                                 |
   |   Domain Service / Aggregate                                   |
   |        |                                                       |
   |        | calls, using ONLY domain types                        |
   |        v                                                       |
   |   +-----------+                                                |
   |   |  Facade   |  <-- the only entry point the domain sees      |
   |   +-----------+                                                |
   |        |                                                       |
   |        v                                                       |
   |   +-----------+        +---------------+                       |
   |   |  Adapter  |------->|  Translator   |                       |
   |   |(transport)|<-------| (data shapes) |                       |
   |   +-----------+        +---------------+                       |
   |        |                                                       |
   +--------|-------------------------------------------------------+
            |  foreign protocol (REST, SOAP, SQL, gRPC, message bus)
            v
   +----------------------------------------------------------------+
   |          Foreign System (legacy app, vendor API, upstream BC)   |
   |          owns its own model, its own invariants, its own pace   |
   +----------------------------------------------------------------+
```

## 7. Dynamics

The runtime flow is the same whether the foreign system is queried
synchronously or notifies the ACL asynchronously through events. Both shapes
are shown because production systems use both, sometimes in the same layer.

```
Synchronous request path

Domain Service            Facade            Adapter          Foreign System
     |                       |                 |                    |
     |  fetchCustomer(id)    |                 |                    |
     |---------------------->|                 |                    |
     |                       | translateRequest|                    |
     |                       |---------------->|                    |
     |                       |                 |  GET /legacy/cust  |
     |                       |                 |------------------->|
     |                       |                 |  legacy DTO        |
     |                       |                 |<-------------------|
     |                       | Translator.toDomain(dto)              |
     |                       |<----------------|                    |
     |  domain Customer      |                 |                    |
     |<-----------------------|                |                    |
     |                       |                 |                    |

Asynchronous notification path

Foreign System        Adapter (listener)     Translator        Domain (event bus)
     |                       |                    |                    |
     |  legacy event         |                    |                    |
     |----------------------->|                   |                    |
     |                       | raw payload        |                    |
     |                       |------------------->|                    |
     |                       |                    | toDomain(payload)  |
     |                       |                    |------------------->|
     |                       |                    |  domain event      |
     |                       |                    |    published       |
```

The synchronous path is a pull, the domain asks and waits. The asynchronous
path is a push, the foreign system emits and the ACL converts on receipt
before the domain ever sees the event. A production ACL frequently combines
both, a synchronous read path for on-demand lookups and an asynchronous
listener that keeps a local read model in sync, which is exactly the pattern
Vernon uses when he pairs the REST client ACL with a background poller that
keeps a cache warm, *Implementing Domain-Driven Design*, Chapter 13.

## 8. Implementation variants

- **In-process library, single service.** The Facade, Adapter, and Translator
  live inside the same codebase as the domain, usually in their own package
  or module, with the domain layer forbidden by convention, or by a linting
  rule, from importing anything from the translation package's internals.
  This is the cheapest variant and the one most teams should start with.
- **Standalone service, network boundary.** The ACL runs as its own deployable
  unit, called over the network by the domain service. The Azure
  Architecture Center's conceptual implementation is exactly this shape, an
  Azure Function performing the translation, invoked through API Management,
  observed through Application Insights
  (<https://learn.microsoft.com/en-us/azure/architecture/patterns/anti-corruption-layer>,
  verified 2026-08-02). This variant is worth the extra deployment and network
  cost when multiple downstream services need the same translation, or when
  the ACL must scale independently of any one consumer.
- **Strangler-adjacent ACL for migration.** During a Strangler Fig migration,
  see `patterns/08-cloud-distributed/strangler-fig.md`, the ACL sits inside
  the legacy monolith itself and intercepts calls destined for a
  newly-extracted service, translating in the other direction, from the
  monolith's internal calling convention outward to the new service's API.
  The AWS sample repository demonstrates exactly this shape, an ASP.NET
  monolith containing an ACL that routes User-service calls to an extracted
  AWS Lambda function behind API Gateway, backed by DynamoDB, while the
  calling code inside the monolith remains unaware of the translation
  (<https://github.com/aws-samples/anti-corruption-layer-pattern>, verified
  2026-08-02). This is the mirror image of the usual direction, protecting
  the new service from having to speak the monolith's dialect, and it is a
  temporary structure meant to be removed once the migration completes.
- **Integration-framework-hosted ACL.** Rather than hand-writing the Adapter
  and routing logic, teams build the translation on top of an enterprise
  integration framework. Apache Camel is specifically called out by
  ThoughtWorks as suited to this role, "Apache Camel's fluent Java interface,
  unit testing support and connectors provide for an effective anti-corruption
  layer when implementing distributed applications"
  (<https://www.thoughtworks.com/radar/tools/apache-camel>, verified
  2026-08-02). This variant trades a dependency on the framework for less
  hand-rolled plumbing code around retries, routing, and protocol adapters.
- **Event-driven ACL.** Rather than translating on every call, the ACL
  subscribes to the foreign system's change events, or polls it, and
  publishes translated domain events onto the protected side's own event bus.
  The Azure Architecture Center's Example section names this as an
  alternative to the synchronous request-response shape, using Azure Service
  Bus, Event Grid, or Event Hubs to decouple the modern domain from the
  legacy system's throughput constraints (verified 2026-08-02, URL above).
  This variant fits best when the domain needs a locally-owned, queryable
  read model rather than a live round trip on every access.

## 9. Known production uses

- **Michelin**, the tyre and mobility technology company, used an
  Anticorruption Layer while migrating a legacy relational application to a
  cloud-native, Kubernetes-hosted microservices architecture. The layer
  mapped nine interconnected legacy tables into a single PostgreSQL record
  with a JSONB column, using a Facade for data retrieval, an Adapter for
  orchestration, and a Translator for format conversion, while the legacy and
  modern systems ran side by side under a Strangler Fig migration
  (<https://blogit.michelin.io/anti-corruption-layer/>, verified 2026-08-02).
- **Microsoft Azure Architecture Center** documents the Anti-Corruption Layer
  as one of its catalogued cloud design patterns and publishes a reference
  architecture using Azure API Management for the external facade, Azure
  Functions for the translation logic between a REST DTO and the domain
  model, and Azure Monitor with Application Insights for observability of
  translation success and latency
  (<https://learn.microsoft.com/en-us/azure/architecture/patterns/anti-corruption-layer>,
  verified 2026-08-02). This is a vendor-endorsed reference implementation
  rather than a single company's internal system, but it demonstrates the
  pattern deployed with named, real cloud services rather than as an abstract
  diagram.
- **AWS Samples**, Amazon Web Services' own official samples organisation,
  publishes a working reference implementation, an ASP.NET monolith
  containing an ACL that extracts a User microservice behind Amazon API
  Gateway, AWS Lambda, and Amazon DynamoDB, while the monolith's calling code
  remains unmodified
  (<https://github.com/aws-samples/anti-corruption-layer-pattern>, verified
  2026-08-02).
- **Apache Camel**, an open source integration framework maintained under the
  Apache Software Foundation, is recommended by ThoughtWorks' Technology Radar
  specifically as a tool for building anti-corruption layers in distributed
  systems, citing its routing DSL, connector library, and testing support
  (<https://www.thoughtworks.com/radar/tools/apache-camel>, verified
  2026-08-02).

## 10. Consequences

Positive consequences.

- The protected domain model stays coherent and expressive in its own
  Ubiquitous Language, free to evolve without every change rippling out to
  every place a foreign concept was allowed to leak in.
- A change on the foreign side, a legacy schema migration, a vendor API
  version bump, is absorbed in one place, the translator, rather than hunted
  down across every call site that previously depended on the foreign shape
  directly.
- The boundary becomes a natural place to add cross-cutting protections that
  would otherwise be scattered, input validation, sanitisation, correlation
  IDs, and translation-failure metrics, which the Azure Architecture Center
  calls out explicitly as design considerations for the layer (verified
  2026-08-02, URL above).
- It enables incremental migration strategies. A legacy system can be
  strangled feature by feature, each newly extracted piece protected from the
  parts of the legacy system not yet replaced, which is exactly how Michelin
  and the AWS sample both use it.

Negative consequences.

- It is genuine extra code that must be designed, written, tested, and
  maintained for as long as the integration exists, and for a temporary
  migration ACL that is never retired on schedule, the layer becomes
  permanent accidental complexity nobody budgeted for.
- It adds a translation hop to every call, with a latency cost, and if
  deployed as its own service, an additional operational surface to deploy,
  scale, and monitor, both explicitly named as trade-offs by the Azure
  Architecture Center (verified 2026-08-02, URL above).
- A translator that is not kept honest against the real foreign system, see
  dimension 15, silently drifts, and a silently drifting translator is worse
  than no translator, because it produces confidently wrong domain objects
  rather than an obvious integration failure.
- It can become a dumping ground for logic that does not belong there.
  Business rules and orchestration decisions occasionally get written into
  the translator because it is the file that happens to be open when a
  discrepancy is noticed, which the Azure Architecture Center warns against
  directly, advising to keep the layer focused on translation logic even when
  the two systems have few semantic differences (verified 2026-08-02, URL
  above).

## 11. Failure modes and misuse

Each entry below states the observable symptom first, then the underlying
cause, then the fix. The specific symptom language reflects common
engineering experience rather than a single cited source, and is labelled
here as judgement.

- **Symptom.** Domain code contains a scattered handful of null checks,
  string parsing, or type coercions around calls that supposedly go through
  the ACL. **Cause.** The Facade's interface leaks a partial abstraction,
  some foreign-system quirks are translated, others are passed through raw
  because a developer under deadline pressure took a shortcut on one field.
  **Fix.** Audit every field the domain touches from the ACL's return type
  and confirm none of it still requires the caller to know about the foreign
  system's representation, not even implicitly through a comment saying "this
  is null when the legacy record is archived."
- **Symptom.** A production incident traces back to the ACL returning stale
  or subtly wrong data, but the ACL's own tests were all green. **Cause.**
  The ACL's tests mock the foreign system's response shape from memory or
  from outdated documentation, rather than exercising the real system or a
  recorded real fixture, so the tests validate the translator against a
  fiction that has drifted from reality. **Fix.** Add contract tests that run
  against the real foreign system in a staging environment, or against
  recorded response fixtures refreshed on a schedule, so a foreign-side
  change breaks the build instead of breaking production.
- **Symptom.** The translator file has grown into the largest, most feared
  file in the codebase, containing conditional business rules such as "if the
  legacy status is X and the amount is over Y, treat it as pending" rather
  than pure shape conversion. **Cause.** Business logic that belongs in the
  domain layer was written into the translator because that is where the
  discrepancy was first noticed, and nobody moved it afterward. **Fix.**
  Separate pure data-shape translation from business interpretation. The
  translator converts a foreign DTO into a domain value object or entity
  faithfully. Any decision about what that value MEANS belongs in a domain
  service that consumes the translated object.
- **Symptom.** A migration ACL, originally scoped as temporary, is still in
  the codebase two years after the legacy system it protected against was
  decommissioned, and nobody remembers why. **Cause.** No owner and no
  removal criterion were assigned when the layer was introduced, so it
  outlived its purpose by default rather than by decision. **Fix.** Record an
  explicit removal condition when the ACL is introduced, for example "remove
  once the legacy order table has zero active writers," and revisit that
  condition on a schedule, see dimension 14.
- **Symptom.** Two different parts of the codebase each built their own
  ad-hoc translation logic for the same foreign system, and they disagree on
  edge cases, for example how a missing field should be defaulted. **Cause.**
  There was never a single, discoverable entry point, the Facade, so
  different teams each wrote their own Adapter and Translator independently.
  **Fix.** Consolidate behind one Facade with one owner, and make it the only
  sanctioned way to reach the foreign system, enforced by code review, an
  architectural fitness function, or a dependency-boundary lint rule.

## 12. Trade-off matrix

Compared against the other Bounded Context integration relationships from
Eric Evans's own catalog, and against the plain Adapter pattern it is built
from.

| Approach | Model purity | Coupling to foreign changes | Upfront cost | Ongoing maintenance | When it wins |
|---|---|---|---|---|---|
| Anticorruption Layer | High, domain never sees foreign types | Low, absorbed at one boundary | High, Facade, Adapter, Translator, tests | Ongoing, must track foreign side | Foreign model genuinely conflicts and the team has no influence over it |
| Conformist (`patterns/11-domain-driven-design/conformist.md`) | None, domain adopts upstream model wholesale | High, every upstream change is a downstream change | Low, no translation to build | Low day to day, high if upstream changes often | Upstream will not collaborate and translation is not worth its cost |
| Customer-Supplier (`patterns/11-domain-driven-design/context-map.md`) | High, downstream negotiates its own model | Managed, upstream accounts for downstream needs | Moderate, requires ongoing coordination | Moderate, relationship must be actively maintained | Both teams are in the same organisation and can negotiate priorities |
| Shared Kernel (`patterns/11-domain-driven-design/shared-kernel.md`) | Deliberately merged, not separate | Very high by design, shared code is shared risk | Low to start, one model instead of two | High coordination cost as both sides change it together | The two contexts genuinely should evolve as one model, closely-collaborating teams |
| Plain Adapter (`patterns/01-design-patterns-gof/adapter.md`) alone | Low, converts interface shape but not deeper model conflicts | Partial, absorbs interface mismatch, not conceptual mismatch | Low, a single class | Low | The mismatch is purely structural, method signatures differ but concepts agree |

## 13. Related and incompatible patterns

- **Bounded Context, `patterns/11-domain-driven-design/bounded-context.md`.** The Anticorruption
  Layer only makes sense at the seam between two Bounded Contexts, or between
  a Bounded Context and a system outside the organisation's modelling
  authority entirely. Without a defined, protected context on the inside,
  there is nothing for the layer to protect.
- **Context Map, `patterns/11-domain-driven-design/context-map.md`.** The Context Map is where
  a team decides, per relationship, whether Anticorruption Layer, Conformist,
  Customer-Supplier, or Shared Kernel governs a given seam. The ACL is one
  entry in that map, not a universal default.
- **Conformist, `patterns/11-domain-driven-design/conformist.md`.** The direct alternative when
  the downstream team decides translation is not worth its cost and instead
  adopts the upstream model as-is. Choosing between the two is a judgement
  about the cost of translation versus the cost of foreign concepts leaking
  in, discussed in dimension 3 and dimension 4.
- **Customer-Supplier, `patterns/11-domain-driven-design/customer-supplier.md`.** A softer
  relationship for when the two teams can negotiate, sometimes used alongside
  a lighter ACL that mainly handles versioning rather than deep semantic
  conflict.
- **Adapter (GoF), `patterns/01-design-patterns-gof/adapter.md`, and Facade (GoF),
  `patterns/01-design-patterns-gof/facade.md`.** The Anticorruption Layer is best understood
  as a composition of these two GoF patterns plus an explicit Translator role,
  applied specifically at a domain-model boundary rather than at an arbitrary
  interface mismatch. An Adapter alone converts a mismatched interface. An ACL
  additionally asserts that the concepts on each side are not the same and
  must never be treated as interchangeable.
- **Strangler Fig, `patterns/08-cloud-distributed/strangler-fig.md`.** During
  an incremental legacy migration, an ACL frequently sits at the strangling
  seam, protecting newly extracted services from the legacy system that has
  not yet been fully replaced, and is removed once the migration completes,
  as seen in both the Michelin case and the AWS sample repository.
- **Shared Kernel, `patterns/11-domain-driven-design/shared-kernel.md`, incompatible.** These
  two patterns express opposite decisions about the same question, should the
  two models converge into one, or should they be kept deliberately separate
  with translation at the boundary. A codebase cannot honestly claim both for
  the same seam at the same time. Choosing Shared Kernel for a relationship
  means accepting shared risk in exchange for zero translation cost, the
  precise trade Anticorruption Layer refuses to make.

## 14. Refactoring path in and out

Introducing an Anticorruption Layer into code that currently calls a foreign
system directly.

1. Identify every call site in the domain layer that references a foreign
   system's types directly, by searching for imports of the foreign SDK,
   foreign DTOs, or foreign field names used in domain logic.
2. Define the domain-shaped interface the calling code should have been using
   all along, the Facade, expressed entirely in the downstream domain's own
   vocabulary and types.
3. Write the Translator first, in isolation, converting a captured real
   response from the foreign system into the domain type. Test it against
   that captured response before wiring anything else.
4. Write the Adapter to perform the actual foreign call, initially as a thin
   pass-through that the Translator sits behind.
5. Redirect one call site at a time to go through the new Facade instead of
   the foreign system directly, verifying behaviour is unchanged after each
   redirection, in the spirit of the Strangler Fig incremental approach, see
   `patterns/08-cloud-distributed/strangler-fig.md`.
6. Once every call site is redirected, add a dependency-boundary check,
   whether a lint rule, an architecture test, or a code review checklist item,
   that forbids any future import of the foreign SDK or foreign DTO type
   outside the ACL's own package.
7. Add contract tests against the real foreign system, or a fixture refreshed
   on a schedule, per dimension 15, so drift on the foreign side is caught at
   the boundary.

Removing an Anticorruption Layer once it has served a temporary purpose,
usually after a legacy system it protected against has been fully
decommissioned.

1. Confirm the removal condition set when the layer was introduced, per
   dimension 11, actually holds, the legacy system genuinely has zero
   remaining consumers or writers.
2. Confirm no domain code depends on any translation quirk the ACL introduced
   that would not otherwise be true, for example a default value the
   Translator supplied for a field the legacy system sometimes omitted.
3. Delete the Adapter and its foreign-system dependency first, since it is
   the piece most tightly bound to the system being retired.
4. Decide whether the Translator's target types remain correct as the
   permanent domain types, or whether the domain model should be revisited
   now that the foreign influence is gone entirely.
5. Remove the dependency-boundary check for the retired foreign SDK, and
   archive or delete the contract tests that exercised the now-removed
   integration.

## 15. Testing and verification

Testing an Anticorruption Layer well means testing three distinct concerns
separately, because conflating them is how the failure modes in dimension 11
happen.

- **Translator unit tests.** Pure, fast, no network. Feed the Translator a
  captured real response, or a range of edge-case responses, missing fields,
  null values, unexpected enum values, and assert the resulting domain object
  is correct. Property-based testing is well suited here when the foreign
  schema has many optional fields, generating combinations of presence and
  absence to catch translator branches nobody thought to hand-write a test
  for.
- **Adapter integration tests against a real or realistic double.** Verify
  the Adapter correctly performs the transport-level call, handles timeouts,
  retries, and authentication, against either the real foreign system in a
  staging environment or a high-fidelity stub that mirrors its actual
  behaviour, including its actual error responses, not an idealised
  happy-path stub.
- **Contract tests, run on a schedule, not only at commit time.** These are
  the tests that catch drift, the failure mode where the foreign system
  changes underneath a translator that was never updated. A contract test
  captures the current real shape of the foreign system's response and fails
  loudly the moment that shape changes, before the change reaches production
  domain logic. Michael Feathers's discipline of characterisation tests in
  legacy code applies directly, these tests exist to detect change, not to
  assert a specification the team fully controls.
- **What becomes easier because of the ACL.** Domain-layer tests no longer
  need to construct or mock foreign-system objects at all, they can construct
  plain domain types directly, which is a real simplification the
  pattern buys back for every test that touches the affected domain area.
- **What becomes harder.** Tests that exercise the whole path,
  domain through ACL through the real foreign system, now depend on that
  foreign system's availability and state, which is exactly the coupling the
  ACL was meant to remove from the domain layer, but it has not disappeared,
  it has moved into the ACL's own test suite, where it belongs and is easier
  to isolate.

## 16. Observability signals

- **Translation failure rate and reason.** Every time the Translator cannot
  cleanly map a foreign response, whether because a field is missing, an enum
  value is unrecognised, or the response fails a sanity check, that event
  should be logged with enough structure to distinguish causes, and counted
  as a metric. A rising translation-failure rate is the earliest warning that
  the foreign system has changed underneath the ACL.
- **Latency of the translation hop, separate from the foreign call's own
  latency.** Instrumenting these separately answers whether a slowdown is the
  foreign system being slow, or the translation logic itself being expensive,
  which is a different fix in each case. The Azure Architecture Center names
  tracking success and latency of the translation explicitly as part of a
  healthy ACL deployment (verified 2026-08-02, URL above).
- **Correlation IDs carried across the boundary.** Because the ACL is the one
  place every cross-system call passes through, it is the natural place to
  attach or propagate a correlation ID, so a request can be traced from the
  domain, through the translation, into the foreign system's own logs, and
  back. Without this, a production incident that spans the boundary is far
  harder to diagnose, because the two systems' logs cannot be joined.
- **A healthy dashboard shows** a low, stable translation-failure rate near
  zero, translation latency that is a small, predictable fraction of total
  request latency, and no unexplained spikes correlated with foreign-system
  deployments. **A failing instance shows** a translation-failure rate that
  climbs after an upstream deploy and stays high, which usually means a
  foreign-side schema change slipped past the contract tests in dimension 15,
  or those tests were not actually wired into the upstream team's release
  process.

## 17. Security and privacy implications

The Anticorruption Layer sits directly on a trust boundary between two
systems that were built under different assumptions, and the Azure
Architecture Center calls this out as a design consideration in its own
right, "Because the anti-corruption layer mediates systems that might have
different trust levels, consider enforcing input validation and sanitization
at this boundary."
(<https://learn.microsoft.com/en-us/azure/architecture/patterns/anti-corruption-layer>,
verified 2026-08-02). This is a sourced claim from that page, and the
remainder of this dimension is engineering judgement built on top of it.

A legacy system in particular may have been built before current input
validation standards existed, or may tolerate malformed data that the
protected domain would never accept, so the ACL is a natural place to enforce
validation that the domain layer should be able to assume has already
happened, rather than defensively re-checking foreign data at every domain
call site. Treating the ACL as a security boundary, not merely a data-shape
boundary, also means the Translator should fail closed, reject and log an
unrecognised or malformed foreign payload rather than passing through a
best-effort guess, since a best-effort guess is exactly how a subtly wrong
domain object slips past dimension 11's first failure mode.

Where the foreign system and the protected domain operate under different
data-handling or regulatory regimes, for example a legacy system that
predates a data-minimisation policy the domain now enforces, the ACL is the
correct place to strip or redact fields that should never cross into the
domain layer at all, rather than translating them faithfully and relying on
domain code to ignore them. A field silently carried through untranslated is
a field that some future domain code will eventually read by accident.

## 18. References

- Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
  Software*, Addison-Wesley, 2003, Chapter 14, "Maintaining Model Integrity,"
  section "ANTICORRUPTION LAYER."
- Vaughn Vernon, *Implementing Domain-Driven Design*, Addison-Wesley, 2013,
  Chapter 13, "Integrating Bounded Contexts," section "Implementing the REST
  Client Using an Anticorruption Layer," page 463.
- Microsoft, "Anti-Corruption Layer Pattern," Azure Architecture Center,
  <https://learn.microsoft.com/en-us/azure/architecture/patterns/anti-corruption-layer>,
  verified 2026-08-02.
- Michelin, "Anti-Corruption Layer. Transforming Legacy Applications into
  Modern Cloud Native Applications," Michelin Engineering Blog,
  <https://blogit.michelin.io/anti-corruption-layer/>, verified 2026-08-02.
- Amazon Web Services, "anti-corruption-layer-pattern," AWS Samples,
  <https://github.com/aws-samples/anti-corruption-layer-pattern>, verified
  2026-08-02.
- ThoughtWorks, "Apache Camel," Technology Radar,
  <https://www.thoughtworks.com/radar/tools/apache-camel>, verified
  2026-08-02.
- ThoughtWorks, "Autonomous bubble pattern," Technology Radar,
  <https://www.thoughtworks.com/en-us/radar/techniques/autonomous-bubble-pattern>,
  verified 2026-08-02.
- Michael Feathers, *Working Effectively with Legacy Code*, Prentice Hall,
  2004, on characterisation tests as a way to pin the current behaviour of
  code, or a system, a team does not fully control.

## Code examples

The pattern is shown in TypeScript, Python, Go, and Java. All four are
idiomatic hosts for the Facade plus Adapter plus Translator composition. Each
sample models the same scenario, a legacy order system whose record uses a
flat status code and a cents-as-string amount, translated into a domain
`Order` with a typed status enum and an integer minor-unit amount, following
the money-as-integer-minor-units discipline this repository's other entries
also use.

### TypeScript

```typescript
// Foreign shape, exactly as the legacy system returns it. Never imported
// outside this file.
interface LegacyOrderRecord {
  order_id: string;
  status_code: "P" | "S" | "C" | "X";
  amount_cents_str: string;
  customer_ref: string | null;
}

type OrderStatus = "Pending" | "Shipped" | "Cancelled";

interface Order {
  id: string;
  status: OrderStatus;
  amountMinorUnits: number;
  customerId: string;
}

class TranslationError extends Error {}

// Translator, a pure function, no I/O, easy to unit test with fixtures.
function translateOrder(record: LegacyOrderRecord): Order {
  const statusMap: Record<LegacyOrderRecord["status_code"], OrderStatus> = {
    P: "Pending",
    S: "Shipped",
    C: "Cancelled",
    X: "Cancelled",
  };
  const status = statusMap[record.status_code];
  if (!status) {
    throw new TranslationError(`unrecognised status code ${record.status_code}`);
  }
  const amount = Number.parseInt(record.amount_cents_str, 10);
  if (Number.isNaN(amount)) {
    throw new TranslationError(`unparsable amount ${record.amount_cents_str}`);
  }
  if (!record.customer_ref) {
    throw new TranslationError("missing customer_ref");
  }
  return {
    id: record.order_id,
    status,
    amountMinorUnits: amount,
    customerId: record.customer_ref,
  };
}

// Adapter, knows how to reach the legacy system, swappable independently
// of the Translator above it.
interface LegacyOrderClient {
  fetchOrder(id: string): Promise<LegacyOrderRecord>;
}

// Facade, the only surface the domain layer is allowed to call.
class OrderAntiCorruptionLayer {
  constructor(private readonly client: LegacyOrderClient) {}

  async getOrder(id: string): Promise<Order> {
    const record = await this.client.fetchOrder(id);
    return translateOrder(record);
  }
}

// A fake standing in for the real HTTP adapter, used to demonstrate the
// facade end to end without a network call.
class InMemoryLegacyOrderClient implements LegacyOrderClient {
  async fetchOrder(id: string): Promise<LegacyOrderRecord> {
    return {
      order_id: id,
      status_code: "S",
      amount_cents_str: "4599",
      customer_ref: "cust-1042",
    };
  }
}

async function main(): Promise<void> {
  const acl = new OrderAntiCorruptionLayer(new InMemoryLegacyOrderClient());
  const order = await acl.getOrder("ord-1");
  console.log(order.status, order.amountMinorUnits, order.customerId);
}

main();
```

### Python

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class TranslationError(Exception):
    pass


@dataclass(frozen=True)
class LegacyOrderRecord:
    order_id: str
    status_code: str
    amount_cents_str: str
    customer_ref: str | None


class OrderStatus(Enum):
    PENDING = "Pending"
    SHIPPED = "Shipped"
    CANCELLED = "Cancelled"


@dataclass(frozen=True)
class Order:
    id: str
    status: OrderStatus
    amount_minor_units: int
    customer_id: str


_STATUS_MAP: dict[str, OrderStatus] = {
    "P": OrderStatus.PENDING,
    "S": OrderStatus.SHIPPED,
    "C": OrderStatus.CANCELLED,
    "X": OrderStatus.CANCELLED,
}


def translate_order(record: LegacyOrderRecord) -> Order:
    status = _STATUS_MAP.get(record.status_code)
    if status is None:
        raise TranslationError(f"unrecognised status code {record.status_code}")
    try:
        amount = int(record.amount_cents_str)
    except ValueError as exc:
        raise TranslationError(f"unparsable amount {record.amount_cents_str}") from exc
    if not record.customer_ref:
        raise TranslationError("missing customer_ref")
    return Order(
        id=record.order_id,
        status=status,
        amount_minor_units=amount,
        customer_id=record.customer_ref,
    )


class LegacyOrderClient(Protocol):
    def fetch_order(self, order_id: str) -> LegacyOrderRecord: ...


class InMemoryLegacyOrderClient:
    def fetch_order(self, order_id: str) -> LegacyOrderRecord:
        return LegacyOrderRecord(
            order_id=order_id,
            status_code="S",
            amount_cents_str="4599",
            customer_ref="cust-1042",
        )


class OrderAntiCorruptionLayer:
    def __init__(self, client: LegacyOrderClient) -> None:
        self._client = client

    def get_order(self, order_id: str) -> Order:
        record = self._client.fetch_order(order_id)
        return translate_order(record)


def main() -> None:
    acl = OrderAntiCorruptionLayer(InMemoryLegacyOrderClient())
    order = acl.get_order("ord-1")
    print(order.status, order.amount_minor_units, order.customer_id)


if __name__ == "__main__":
    main()
```

### Go

```go
package main

import (
	"errors"
	"fmt"
	"strconv"
)

// LegacyOrderRecord is the foreign shape. It never leaves this file.
type LegacyOrderRecord struct {
	OrderID        string
	StatusCode     string
	AmountCentsStr string
	CustomerRef    string
}

type OrderStatus int

const (
	Pending OrderStatus = iota
	Shipped
	Cancelled
)

func (s OrderStatus) String() string {
	switch s {
	case Pending:
		return "Pending"
	case Shipped:
		return "Shipped"
	case Cancelled:
		return "Cancelled"
	default:
		return "Unknown"
	}
}

type Order struct {
	ID               string
	Status           OrderStatus
	AmountMinorUnits int64
	CustomerID       string
}

var statusMap = map[string]OrderStatus{
	"P": Pending,
	"S": Shipped,
	"C": Cancelled,
	"X": Cancelled,
}

// TranslateOrder is the pure Translator function. No I/O.
func TranslateOrder(r LegacyOrderRecord) (Order, error) {
	status, ok := statusMap[r.StatusCode]
	if !ok {
		return Order{}, fmt.Errorf("unrecognised status code %s", r.StatusCode)
	}
	amount, err := strconv.ParseInt(r.AmountCentsStr, 10, 64)
	if err != nil {
		return Order{}, fmt.Errorf("unparsable amount %q, %w", r.AmountCentsStr, err)
	}
	if r.CustomerRef == "" {
		return Order{}, errors.New("missing customer ref")
	}
	return Order{
		ID:               r.OrderID,
		Status:           status,
		AmountMinorUnits: amount,
		CustomerID:       r.CustomerRef,
	}, nil
}

// LegacyOrderClient is the Adapter's interface, kept small on purpose.
type LegacyOrderClient interface {
	FetchOrder(id string) (LegacyOrderRecord, error)
}

type inMemoryLegacyOrderClient struct{}

func (inMemoryLegacyOrderClient) FetchOrder(id string) (LegacyOrderRecord, error) {
	return LegacyOrderRecord{
		OrderID:        id,
		StatusCode:     "S",
		AmountCentsStr: "4599",
		CustomerRef:    "cust-1042",
	}, nil
}

// OrderAntiCorruptionLayer is the Facade. It is the only type the domain
// layer is allowed to depend on.
type OrderAntiCorruptionLayer struct {
	client LegacyOrderClient
}

func NewOrderAntiCorruptionLayer(client LegacyOrderClient) *OrderAntiCorruptionLayer {
	return &OrderAntiCorruptionLayer{client: client}
}

func (a *OrderAntiCorruptionLayer) GetOrder(id string) (Order, error) {
	record, err := a.client.FetchOrder(id)
	if err != nil {
		return Order{}, err
	}
	return TranslateOrder(record)
}

func main() {
	acl := NewOrderAntiCorruptionLayer(inMemoryLegacyOrderClient{})
	order, err := acl.GetOrder("ord-1")
	if err != nil {
		panic(err)
	}
	fmt.Println(order.Status, order.AmountMinorUnits, order.CustomerID)
}
```

### Java

```java
import java.util.Map;
import java.util.Optional;

public final class AntiCorruptionLayerDemo {

    // Foreign shape. Confined to this file, never referenced by domain code.
    record LegacyOrderRecord(
            String orderId,
            String statusCode,
            String amountCentsStr,
            String customerRef) {
    }

    enum OrderStatus { PENDING, SHIPPED, CANCELLED }

    record Order(String id, OrderStatus status, long amountMinorUnits, String customerId) {
    }

    static final class TranslationException extends RuntimeException {
        TranslationException(String message) {
            super(message);
        }
    }

    private static final Map<String, OrderStatus> STATUS_MAP = Map.of(
            "P", OrderStatus.PENDING,
            "S", OrderStatus.SHIPPED,
            "C", OrderStatus.CANCELLED,
            "X", OrderStatus.CANCELLED
    );

    // Translator, pure, no I/O, testable in isolation.
    static Order translateOrder(LegacyOrderRecord record) {
        OrderStatus status = Optional.ofNullable(STATUS_MAP.get(record.statusCode()))
                .orElseThrow(() -> new TranslationException(
                        "unrecognised status code " + record.statusCode()));
        long amount;
        try {
            amount = Long.parseLong(record.amountCentsStr());
        } catch (NumberFormatException e) {
            throw new TranslationException("unparsable amount " + record.amountCentsStr());
        }
        if (record.customerRef() == null || record.customerRef().isBlank()) {
            throw new TranslationException("missing customerRef");
        }
        return new Order(record.orderId(), status, amount, record.customerRef());
    }

    // Adapter contract, deliberately narrow.
    interface LegacyOrderClient {
        LegacyOrderRecord fetchOrder(String id);
    }

    static final class InMemoryLegacyOrderClient implements LegacyOrderClient {
        @Override
        public LegacyOrderRecord fetchOrder(String id) {
            return new LegacyOrderRecord(id, "S", "4599", "cust-1042");
        }
    }

    // Facade, the sole entry point the domain layer is allowed to call.
    static final class OrderAntiCorruptionLayer {
        private final LegacyOrderClient client;

        OrderAntiCorruptionLayer(LegacyOrderClient client) {
            this.client = client;
        }

        Order getOrder(String id) {
            LegacyOrderRecord record = client.fetchOrder(id);
            return translateOrder(record);
        }
    }

    public static void main(String[] args) {
        OrderAntiCorruptionLayer acl = new OrderAntiCorruptionLayer(new InMemoryLegacyOrderClient());
        Order order = acl.getOrder("ord-1");
        System.out.println(order.status() + " " + order.amountMinorUnits() + " " + order.customerId());
    }
}
```

Rust, Swift, C#, and Kotlin are omitted here not because the pattern does not
translate, it does, an Anticorruption Layer is language-agnostic by nature,
but because the four languages above already demonstrate the pattern across
a language with structural typing and interfaces (TypeScript), a dynamically-typed
language with protocols (Python), a language without exceptions that forces
explicit error values at the translation boundary (Go), and a statically
typed, enterprise-integration-heavy language where the pattern originated in
practice (Java). A fifth or sixth language would repeat the same shape without
adding a genuinely new implementation concern.
