---
name: Open Host Service
slug: open-host-service
family: 11-domain-driven-design
category: Strategic Design
aliases: [OHS, Public Host Interface, Open API Context Relationship]
first_described: "Evans 2003"
maturity: canonical
related: [published-language, anti-corruption-layer, conformist, customer-supplier, bounded-context, context-map, shared-kernel]
incompatible_with: [shared-kernel, conformist]
verified: 2026-08-02
---

# Open Host Service

## 1. Name, aliases, and lineage

The canonical name is Open Host Service, commonly shortened to OHS in
architecture diagrams and context maps. It was first described by Eric Evans
in *Domain-Driven Design. Tackling Complexity in the Heart of Software*,
Addison-Wesley, 2003, ISBN 0-321-12521-5, chapter 14, "Maintaining Model
Integrity". Evans states the pattern's intent as defining a protocol that
gives access to a subsystem as a set of services, and opening that protocol
so that anyone who needs to integrate can use it, rather than negotiating a
custom translation for every new consumer. The chapter presents Open Host
Service as one of several relationship patterns a team can choose when
drawing a context map, alongside Shared Kernel, Customer-Supplier, Conformist,
and Anti-Corruption Layer.

Vaughn Vernon carries the pattern forward in *Implementing Domain-Driven
Design*, Addison-Wesley, 2013, ISBN 978-0-321-83457-7, chapter 3, "Context
Maps", where he restates the same protocol definition and pairs it explicitly
with Published Language, illustrating both with a RESTful resource design.
Vernon's treatment is the one most working teams reach for today because it
grounds the pattern in HTTP and JSON rather than leaving it abstract, and it
is the reason "REST API as Open Host Service" has become the default reading
of the pattern in industry conversation (Vernon, chapter 3, section on
Open Host Service, cited in the Vernon 2013 gist table of contents summary,
https://gist.github.com/dimabory/4cda22040d23994a31087ffc61060ad2, verified
2026-08-02, and confirmed against the O'Reilly chapter listing at
https://www.oreilly.com/library/view/implementing-domain-driven-design/9780133039900/ch03.html
verified 2026-08-02).

No alternative name has displaced Evans's original in the literature. Some
architecture-review writeups call it a "Public Host Interface" or an "Open
API context relationship" when they want to avoid DDD jargon in front of a
non-DDD audience, but these are descriptive paraphrases rather than
recognised aliases with their own citation trail. The name is not contested
and the pattern is not known by a materially different name in any adjacent
community; API design writing independently arrives at the same shape under
plain terms such as "public API" or "platform API", without crediting DDD,
which is itself a useful signal that the pattern describes something teams
converge on whether or not they have read Evans.

One naming confusion is worth flagging early because it recurs across
blog-length treatments of the pattern. Open Host Service is a relationship
between two bounded contexts on a context map, not a synonym for having a
REST API. A context can have an HTTP API and still not be practising Open
Host Service, if that API exposes internal domain types directly, changes
shape whenever the internal model changes, or was designed around one
particular consumer's needs. The pattern requires an explicit intent to
serve many consumers through one stable, versioned surface, and it requires
the translation described in dimension 5 below. Ownership of a documented
protocol is what earns the name, not the transport it happens to run over.

## 2. Problem and context

A bounded context that has real internal complexity attracts multiple
downstream consumers over time. The first consumer arrives and the team
building the upstream context negotiates a bespoke integration with them,
matching field names, semantics, and even quirks of the internal model,
because doing anything more general felt like premature investment for one
caller. A second consumer arrives, wants something close but not identical,
and the upstream team either builds a second bespoke integration or bends
the first one to serve both, coupling the two consumers to each other
through a shared endpoint neither of them controls. A third consumer
arrives. By now every internal refactor inside the upstream context risks
breaking one, two, or three downstream systems that each depend on a
slightly different slice of the internal model, exposed through code paths
nobody planned to make load-bearing.

This is the concrete failure this pattern targets. The upstream team spends
an increasing share of its capacity on integration support rather than on
its own domain, because every schema change is now a cross-team negotiation
with whichever consumer happens to be affected. The internal model, which
should be free to evolve as the team's understanding of the domain deepens,
becomes pinned in place by external dependents who reached in and grabbed
whatever shape was convenient at integration time. Evans frames this as the
cost of a Customer-Supplier relationship, and even a Conformist relationship
where downstream simply accepts upstream's model, multiplied across many
downstream teams. one relationship the upstream team can plan around is
manageable, N ad-hoc relationships where N grows without bound is not (Evans
2003, chapter 14).

The context in which Open Host Service is the right answer has three
recognisable features. First, the number of consumers is genuinely plural,
either already or predictably soon, so the cost of designing one stable
protocol is paid once and recovered many times over. Second, the upstream
team is in a position of some authority over the relationship, meaning it
can reasonably say "integrate with this contract" rather than being forced
to accommodate whatever each consumer already built, which is the situation
Evans calls being "upstream" on the context map. Third, the internal model
of the upstream context has its own reasons to keep changing, driven by
domain learning rather than by external demand, so a mechanism is needed to
let that internal change happen without forcing every consumer to change in
lockstep. Where those three conditions hold, the alternative to Open Host
Service is not "no integration pattern", it is an accumulation of ad-hoc
Customer-Supplier or Conformist relationships, each cheaper individually and
more expensive in aggregate.

## 3. Forces

- **Coupling.** Favoured for the downstream side. Every consumer couples to
  one published contract instead of to the upstream's internal model or to
  each other's individual arrangements. The upstream side accepts a new kind
  of coupling in exchange, a commitment to the contract itself, which is
  harder to walk back than an internal refactor would otherwise be.
- **Team autonomy for the upstream team.** Favoured, and this is the primary
  force the pattern optimises. Once the protocol and its Published Language
  are fixed, the upstream team can restructure aggregates, rename internal
  concepts, and change persistence, all without a cross-team meeting, as
  long as the translation layer keeps producing the same published shape.
- **Team autonomy for downstream teams.** Favoured as a byproduct. A
  downstream team building against a documented, versioned contract does not
  need standing access to the upstream team's calendar to integrate or to
  keep working after an upstream release.
- **Cost of change for the contract itself.** Sacrificed. Once several
  consumers depend on a version of the Published Language, changing that
  version is expensive in the same way changing a public library's API is
  expensive, and it is the direct trade for the coupling reduction above.
- **Consistency of consumer experience.** Favoured. Every consumer sees the
  same semantics for the same concept, which a set of bespoke integrations
  cannot guarantee once they have drifted independently for a year.
- **Latency and payload shape.** Mixed. A generalised, many-consumer contract
  frequently returns more fields than any one consumer needs, or fewer than
  a specific consumer would prefer, because it is designed for the union of
  reasonable use cases rather than for one caller's exact query.
- **Discoverability and onboarding cost.** Favoured once the contract exists,
  sacrificed while it is being built. A documented protocol with a schema
  and examples lets a new consumer integrate without a conversation, but
  producing that documentation and keeping it current is real, continuing
  work that a bespoke integration never asked anyone to do.
- **Governance and versioning overhead.** Sacrificed. A one-off integration
  has no version policy because it has one consumer to keep happy. A
  published protocol needs a stated deprecation window, a compatibility
  policy, and someone accountable for both, which is organisational weight a
  small team may not want to carry for a domain with only one consumer.

The pattern trades the upstream team's freedom to move fast on external
matters, since the contract now constrains what a release can silently
change, for the upstream team's freedom to move fast on internal matters,
since the internal model is no longer directly exposed. Whether that trade
is worth making depends entirely on whether the number of consumers and the
churn rate of the internal model justify the fixed cost of building and
governing the contract, which is exactly what dimension 4 works out.

## 4. Applicability and non-applicability

Reach for Open Host Service when the following hold.

- More than one consumer needs to integrate with a bounded context, or the
  team can see that number growing, and negotiating each integration
  separately would cost more than designing one shared contract.
- The upstream team wants freedom to refactor its internal domain model
  without coordinating that refactor with every downstream team on every
  release.
- The context is genuinely upstream in the relationship, meaning it has
  either organisational authority, technical influence, or both, to set the
  terms of integration rather than accept whatever shape each consumer
  demands.
- The domain concept being exposed is stable enough, at the level the
  contract describes it, that a versioned schema is a realistic commitment
  rather than a fiction the team will break every release anyway.
- The context sits at an organisational boundary where a documented,
  self-service contract genuinely reduces coordination cost, such as a
  platform team serving several product teams, or a vendor serving external
  customers.

Do NOT reach for Open Host Service in these cases.

- **There is exactly one consumer and no credible plan for a second.**
  Designing a general, versioned, publicly documented protocol for a single
  known caller is speculative generality applied to integration design. A
  direct Customer-Supplier relationship, where the two teams negotiate the
  contract together and evolve it together, costs less and serves the one
  relationship better, because both sides can move in lockstep instead of
  paying a stability tax neither of them asked for.
- **The consumer should simply accept the upstream model as-is.** When
  downstream has no independent domain concerns and no interest in shaping
  the contract, Conformist is the honest relationship, and building a
  translation layer that both sides ignore in practice is wasted structure.
- **The two contexts are actually cooperating on one shared concept that
  both teams co-own.** That is Shared Kernel, and Open Host Service is the
  wrong tool because a published, versioned, one-directional contract
  implies exactly the ownership asymmetry Shared Kernel exists to avoid.
- **The upstream context's model changes too fast, or is too poorly
  understood, to freeze even a narrow published slice of it.** Publishing a
  contract against a model still in flux produces a version 1 that is
  obsolete before any consumer finishes integrating, and the churn cost
  lands on every downstream team instead of staying inside the upstream
  team where it belongs. Wait until the model has settled enough to support
  a contract, or scope the contract narrower than the parts still moving.
- **The organisation cannot or will not fund ongoing contract governance.**
  A Published Language without a deprecation policy, a schema registry, and
  someone who owns backward compatibility decisions degrades into an
  unversioned API within a year, at which point the pattern has been
  adopted in name only and downstream teams are back to being Conformists
  who happen to call it a "public API".
- **The integration is internal, low-stakes, and short-lived**, such as a
  temporary batch job that reads from another team's database during a
  migration. Building a durable public contract for a caller that will stop
  existing in a quarter is effort spent on the wrong horizon.
- **A synchronous, generalised request-response contract does not fit the
  actual integration need**, for instance when downstream mainly needs to
  react to state changes over time rather than to query current state. That
  is the domain of domain events and an event-carried Published Language,
  and while events can still be an Open Host Service, forcing a
  request-response API onto a fundamentally event-driven need produces a
  contract nobody is happy calling.

## 5. Structure

Four participants, named by the role each plays, following the same
role-naming discipline the family uses for Evans's other context-mapping
patterns.

- **Upstream Bounded Context.** The team and the internal domain model that
  own the capability being exposed. It contains the real aggregates,
  domain services, and invariants, and none of that internal shape is
  visible to any consumer directly.
- **Open Host Service, the protocol boundary.** The set of operations the
  upstream context exposes deliberately, described independently of the
  internal model. This is the service in the pattern's name, and it is a
  boundary artifact, not a class. concretely it is usually an HTTP resource
  set, a gRPC service definition, or a schema of emitted domain events, but
  the pattern itself is transport-agnostic. Evans's original wording is
  intentionally protocol-neutral (Evans 2003, chapter 14).
- **Published Language.** The shared vocabulary and wire schema the protocol
  speaks. This is the companion pattern Evans introduces in the same
  chapter, and in practice the two are inseparable, because an open
  protocol with no documented, stable schema degenerates into ad hoc
  payloads that change whenever the implementation changes. The ddd
  practitioners glossary entry states plainly that Published Language is
  often combined with Open Host Service
  (https://ddd-practitioners.com/home/glossary/bounded-context/bounded-context-relationship/open-host-service/,
  verified 2026-08-02). The Published Language is usually expressed as an
  OpenAPI document, a Protobuf or Avro schema, a GraphQL SDL file, or a
  CloudEvents-shaped event schema, and it is versioned independently of the
  upstream team's internal release cadence.
- **Consumer.** Any downstream bounded context, service, or team that
  integrates against the protocol without needing to know anything about
  the upstream context's internal model. A well-designed Open Host Service
  can gain new consumers with zero coordination cost to the upstream team,
  which is the concrete payoff dimension 3 promised.

The critical relationship to draw explicitly on a structure diagram is the
translation step inside the upstream context, between its internal
aggregates and the Published Language it emits. That translation is the
mechanism that makes the internal model free to change. Without an explicit
translation layer, an "Open Host Service" is often just a REST controller
that serialises the internal entities directly, which is not the pattern,
it is the exact coupling the pattern exists to prevent, wearing an HTTP
frontend.

## 6. ASCII structure diagram

```
Upstream Bounded Context

+------------------------+
| Internal Domain Model  |
| aggregates, invariants |
+------------------------+
     | reads
     v
+---------------------------------------------------+
| Host Translator (Open Host Service adapter layer) |
+---------------------------------------------------+
     | emits
     v
+--------------------------------------------+
| Published Language                         |
| versioned schema, OpenAPI, Protobuf, event |
| contract                                   |
+--------------------------------------------+

Internal Domain Model changes freely, no external notice
needed. Only the Host Translator sees both the internal
model and the Published Language.

One stable, documented, versioned protocol, downstream:

+--------------------------------------------------+
| Consumer A, own model, translates Published Lang |
+--------------------------------------------------+
+--------------------------------------------------+
| Consumer B, own model, translates Published Lang |
+--------------------------------------------------+
...
+--------------------------------------------------+
| Consumer N, own model, translates Published Lang |
+--------------------------------------------------+

No consumer, and no part of the internal model, ever
crosses the Host Translator boundary directly.
```

## 7. Dynamics

Two flows matter, a request-response query against the protocol, and the
much less discussed but equally important flow of the upstream team
changing its internal model without breaking anyone.

```
Consumer A          Open Host Service          Host Translator      Internal Model
    |                       |                          |                   |
    |-- GET /orders/42 ---->|                          |                   |
    |   Accept-Version. 3   |                          |                   |
    |                       |-- load Order(id=42) --------------------->  |
    |                       |                          |<-- Order aggregate|
    |                       |                          |   (internal shape)|
    |                       |<-- translate to v3 -------|                   |
    |                       |    PublishedOrder         |                   |
    |<-- 200 OK, PublishedOrder (v3 schema) -------------|                   |
    |                       |                          |                   |

   Later, the upstream team splits the internal Order aggregate into
   Order and Fulfillment for its own domain reasons.

    |                       |                          |                   |
    |                       |-- load Order + Fulfillment ------------->    |
    |                       |                          |<-- two aggregates |
    |                       |<-- translate BOTH into ---|                   |
    |                       |    the SAME v3 PublishedOrder shape          |
    |<-- 200 OK, PublishedOrder (v3 schema, unchanged) --|                   |
    |                       |                          |                   |
    |  Consumer A observes no difference. The Host Translator absorbed     |
    |  the internal split entirely.                                        |
```

The dynamics that make the pattern work are the two lines at the end. the
consumer's request and response shape are identical before and after an
internal refactor, because every internal change is absorbed inside the
Host Translator before it reaches the Published Language boundary. When a
change genuinely cannot be absorbed, meaning the meaning of the published
contract itself must change, that is the moment a new protocol version is
introduced, an additive field in a permissive schema, or a new version
segment such as Stripe's dated `Stripe-Version` header or GitHub's dated
`X-GitHub-Api-Version` header, both discussed with citations in dimension
9, rather than the existing version silently changing shape under
consumers who never agreed to that change.

## 8. Implementation variants

**Synchronous HTTP API with a header- or path-based version.** The most
common form in current practice. The protocol is REST or REST-adjacent
JSON over HTTP, the Published Language is described by an OpenAPI document,
and the version is negotiated either through a URL path segment
(`/v3/orders/42`), a custom header (Stripe's `Stripe-Version`, GitHub's
`X-GitHub-Api-Version`), or content negotiation via the `Accept` header. The
Azure Architecture Center's microservices guidance recommends exactly this
combination for Open Host Service in a microservices context, pointing at
OpenAPI as the concrete Published Language mechanism (Microsoft Learn,
"Use Domain Analysis to Model Microservices", verified 2026-08-02, see
dimension 9 for the full citation).

**GraphQL schema as the Published Language.** The protocol is a single
GraphQL endpoint, and the Published Language is the schema definition
language document itself, with its own deprecation directive
(`@deprecated(reason. "...")`) built into the type system rather than
layered on top of it as a separate versioning scheme. Consumers query only
the fields they need, which softens the payload-shape force from dimension
3 at the cost of a more complex host-side resolver layer that must still
translate every field back to the internal model.

**gRPC or Protobuf-defined service.** The protocol is a `.proto` service
definition, and the Published Language is the Protobuf schema, which
carries its own field-numbering discipline for backward-compatible
evolution, additive fields get new numbers, fields are never renumbered or
reused. This variant trades human readability for binary efficiency and
strong client code generation, and it is the dominant choice for internal,
polyglot service-to-service Open Host Services inside a single
organisation where a shared IDL toolchain is already standard.

**Event-carried Open Host Service.** The protocol is a stream of domain
events on a broker, and the Published Language is the event schema, often
Avro or a CloudEvents envelope with a JSON body, registered in a schema
registry that enforces compatibility rules on every new schema version. The
key structural difference from the request-response variants is that the
upstream context pushes state changes rather than answering pulls, which
suits consumers that need to react to change over time rather than query
current state, and which sidesteps the request-response coupling entirely
at the cost of eventual rather than immediate consistency for consumers.

**Batch or file-based publication.** For domains where near-real-time
integration is unnecessary, such as end-of-day reference data, the Open
Host Service can be a published file format on cloud storage, an SFTP drop,
or a data warehouse table with a documented, versioned schema. It is
structurally the same pattern, the Host Translator writes the file, the
Published Language is the file's documented schema, and consumers pull on
their own schedule, but it is worth naming as its own variant because teams
sometimes fail to recognise batch integration as an instance of the same
pattern and reinvent its governance from scratch.

**Language and runtime note.** Open Host Service is a boundary-level
pattern, not a language-level construct, so no language changes its shape
the way a first-class function changes Factory Method's shape. What
differs across languages is how the Host Translator is implemented inside
the upstream context. an explicit mapping class in Java or C#, a pure
function with an exhaustive discriminated-union match in TypeScript, a
dataclass-to-dataclass converter in Python, or a struct-to-struct
conversion function in Go. In every case the translator is deliberately
kept thin and free of business logic, its only job is shape conversion, so
that domain rules never leak into the boundary layer.

## 9. Known production uses

**Stripe API, versioned via the `Stripe-Version` header.** Stripe's API
follows a rolling versioning model where, since the 2024-09-30 release
process change, monthly releases are additive and backward compatible, and
twice a year a new named major version (for example `acacia`, and the
version current at verification time, `2026-07-29.dahlia`) is released that
may include breaking changes. Every API request made with an organization
API key must include the `Stripe-Version` header, and each SDK version
pins to the API version current at the time that SDK was released unless
the caller overrides it. This is a textbook Open Host Service, one team
owns the payments domain internally, and every one of Stripe's thousands of
integrating merchants consumes the same documented, versioned, published
contract rather than a bespoke integration each. Stripe Documentation, "SDK
versioning" and "API versioning",
https://docs.stripe.com/sdks/versioning and
https://docs.stripe.com/api/versioning, verified 2026-08-02.

**GitHub REST API, versioned via the `X-GitHub-Api-Version` header.**
Requests to the GitHub REST API can specify a dated API version such as
`2026-03-10` via the `X-GitHub-Api-Version` header, requests without the
header default to the `2022-11-28` version, a request for an API version no
longer supported returns HTTP 410 Gone, and GitHub commits to supporting a
previous version for at least 24 months after a new version is released.
The published, dated version acts as the Published Language's version
identifier, and GitHub's own internal implementation of pull requests,
issues, and repositories can change freely behind that stable, documented
surface. GitHub Docs, "API Versions",
https://docs.github.com/en/rest/about-the-rest-api/api-versions, verified
2026-08-02.

**Shopify Admin API, versioned on a quarterly calendar schedule.** Shopify
releases a new dated API version (for example `2026-04`) every three months,
each stable version is supported for a minimum of twelve months with at
least nine months of overlap between consecutive versions, and a field
deprecated in one release is only removed in a later release once that
overlap window has passed. Shopify explicitly documents three version
states, stable, release candidate, and unstable, which is a Published
Language governance model few other public APIs state as plainly. Shopify
Dev Documentation, "About Shopify API versioning" and "About REST Admin API
versioning", https://shopify.dev/docs/api/usage/versioning and
https://shopify.dev/docs/api/admin-rest/usage/versioning, verified
2026-08-02.

**Kubernetes API, versioned by API group and enforced by a stated
deprecation policy.** Kubernetes resources such as Deployments are addressed
through a versioned API group, for example `apps/v1`, and the project's
deprecation policy states that a beta API must remain supported for at
least nine months or three releases after deprecation, and a stable API for
at least twelve months or three releases, that an API element can only be
removed by incrementing the group version, and that since Kubernetes 1.19 a
call to a deprecated endpoint returns an HTTP `Warning` header (RFC 7234
section 5.5) rather than silently degrading. Every cluster operator and
every controller author across a vast, decentralised ecosystem integrates
against these versioned API groups instead of the internal object model of
whichever cloud provider or distribution they happen to run, which is Open
Host Service operating at the scale of an entire industry standard.
Kubernetes documentation, "Kubernetes Deprecation Policy",
https://kubernetes.io/docs/reference/using-api/deprecation-policy/, verified
2026-08-02 via the mirrored content at
https://github.com/kubernetes/website/blob/main/content/en/docs/reference/using-api/deprecation-policy.md.

**Microsoft's own architecture guidance names the pattern explicitly for
microservices.** The Azure Architecture Center's domain-driven microservices
guidance lists Open Host Service and Published Language as one of four
named context-mapping relationships a team should choose between when
designing service boundaries, states that the upstream context exposes a
well-defined API, Open Host Service, described in a shared format,
Published Language, that downstream contexts consume, and points readers
at the OpenAPI specification as the concrete Published Language artifact
for REST-based microservices. Microsoft Learn, "Use Domain Analysis to
Model Microservices",
https://learn.microsoft.com/en-us/azure/architecture/microservices/model/domain-analysis,
verified 2026-08-02. This is evidence that the pattern is not merely a
retrospective label applied to APIs that happened to work well, it is an
architecture recommendation major vendors ship in their own official
guidance.

## 10. Consequences

Positive.

- The internal domain model inside the upstream context is free to
  refactor, split, merge, and rename without a cross-team release
  negotiation, as long as the Host Translator continues to satisfy the
  published contract.
- A new consumer can integrate with zero synchronous coordination cost to
  the upstream team, reading documentation and a schema instead of
  scheduling a meeting, which is the direct payoff of the coupling
  reduction described in dimension 3.
- Every consumer receives the same semantics for the same concept, which
  removes an entire category of "why does team X's integration behave
  differently from team Y's" incident.
- The explicit Host Translator becomes a single, auditable seam where every
  outbound field is deliberate, which tends to surface accidental leakage
  of internal or sensitive fields before it ships, because someone has to
  decide to add the mapping rather than it happening by accident through
  reflection-based serialization.
- A documented, versioned contract is a natural place to attach a
  deprecation policy, a changelog, and a support commitment, all of which
  make the upstream context legible to the rest of the organisation as a
  platform rather than as a black box other teams poke at.

Negative.

- Building and maintaining the Host Translator, the Published Language
  schema, and the versioning policy is real, continuing engineering cost
  that a bespoke integration never asked the upstream team to pay, and that
  cost does not disappear even when the number of active consumers is
  small.
- The published contract inevitably lags the internal model's true
  expressive power, because it is designed for the union of reasonable
  external needs rather than for any one internal concept at full fidelity,
  which frustrates the consumer who genuinely needs the field the contract
  chose not to expose.
- A deprecated version cannot simply be deleted the moment the upstream
  team wants to, it must be supported for the stated window, which is a
  standing constraint on the team's own roadmap that a one-off integration
  does not impose.
- Governance overhead scales with the number of consumers and the rate of
  external demand for new fields, and a team that under-invests in that
  governance ends up with an unversioned, ad hoc API wearing the name
  "Open Host Service" without any of the discipline that makes the pattern
  earn its keep.
- The pattern can become a place where organisational politics hide inside
  technical language, a slow-moving, heavily governed contract is sometimes
  the correct engineering answer and sometimes a convenient excuse for a
  platform team to avoid responding to a legitimate downstream need.

## 11. Failure modes and misuse

**The pass-through host.** Symptom. The published response body is a direct
JSON serialization of the internal entity or ORM row, field names match the
database columns, and any internal schema migration breaks the public
contract on the next deploy. Cause. No Host Translator was actually built,
only a controller was placed in front of the internal model. Fix. Insert an
explicit mapping layer, even a thin one, between the internal aggregate and
the response DTO, and add a contract test (dimension 15) that fails when
that mapping is bypassed.

**Version sprawl with no deprecation discipline.** Symptom. The API
documentation lists version 1 through version 11, most consumers are
unknown to the platform team, and nobody can say which versions are safe to
retire without breaking a customer nobody has talked to in two years. Cause.
New versions were minted whenever a breaking change felt convenient, with
no stated support window and no consumer registry. Fix. Adopt a dated or
semantic version policy with an explicit minimum support duration, the
Shopify and GitHub examples in dimension 9 both name theirs, and require
every consumer to register or authenticate so retirement decisions are
based on real usage telemetry rather than guesswork.

**The Published Language that nobody documents.** Symptom. The contract is
technically stable, the response shape has not changed in a year, but new
consumers cannot integrate without reading the upstream team's source code
or asking in a chat channel, because no schema, no OpenAPI document, and no
changelog exists anywhere consumers can find. Cause. The team built the
translation discipline but skipped the publication half of Published
Language, treating the pattern as purely a runtime concern. Fix. Generate
and publish machine-readable schema artifacts, OpenAPI, Protobuf, or a
GraphQL SDL file, from the same source that drives the Host Translator, so
documentation cannot silently drift from behaviour.

**Consumer-driven scope creep.** Symptom. The contract accumulates
consumer-specific query parameters, optional fields, and conditional
response shapes, each added to satisfy exactly one caller, until the
"general" contract is really eleven bespoke contracts wearing one version
number. Cause. The upstream team said yes to every consumer request without
asking whether the requested capability belongs in the general contract or
in that consumer's own translation of it. Fix. Push consumer-specific
shaping to the consumer side, a downstream Anti-Corruption Layer, and keep
the published contract limited to genuinely general-purpose fields and
operations.

**Breaking change shipped as a patch.** Symptom. A field's type or meaning
changes within what the documentation calls the same version, and multiple
consumers fail simultaneously with no warning, because the change was
judged small by the upstream team without consulting the compatibility
policy. Cause. No automated compatibility check exists between the current
schema and the previous published one, so a human judgement call
substitutes for a guarantee. Fix. Run schema-compatibility checking in CI
against the last published schema, a Protobuf or Avro schema registry's
built-in compatibility check, or an OpenAPI diff tool, and treat any
incompatible change as requiring a new version, never a same-version patch.

**Treating the internal model as already the Published Language.** Symptom.
The team believes it has adopted Open Host Service because it has a REST
API, but every internal refactor still requires touching the API layer in
lockstep, because the "contract" is generated automatically from the
internal entity classes with no independent schema of its own. Cause. The
Host Translator step from dimension 5 was skipped entirely, collapsing
Published Language into whatever the internal model currently looks like,
serialized. Fix. Separate the wire DTO type from the internal domain type
at the code level, even when they currently have identical fields, so the
compiler forces a deliberate mapping decision the moment they diverge.

## 12. Trade-off matrix

Compared against named alternatives from the same context-mapping family,
across the forces from dimension 3.

| Force | Open Host Service | Customer-Supplier | Conformist | Shared Kernel | Anti-Corruption Layer (downstream-owned) |
|---|---|---|---|---|---|
| Who bears translation cost | Upstream, once, for all consumers | Negotiated jointly per relationship | Downstream, by accepting upstream's model wholesale | Neither, both sides share one model | Downstream, once, for that one relationship |
| Scales to many consumers | Strong, that is its purpose | Weak, cost grows per relationship | Weak, each conforming team repeats the same acceptance | Weak, sharing does not scale past a few tightly coordinated teams | Weak, cost grows per relationship |
| Upstream internal freedom to refactor | High, absorbed by the Host Translator | Medium, upstream must negotiate breaking changes | High, downstream absorbs the change by re-conforming | Low, both teams must agree before either changes the shared part | High, downstream absorbs the change |
| Downstream domain independence | High, downstream keeps its own model | High, downstream keeps its own model | None, downstream's model is upstream's model | Low, the shared part is not independently owned by either | High, and explicitly the point of the pattern |
| Governance overhead | High, versioning, schema, deprecation policy | Medium, ongoing negotiation between two teams | Low, downstream simply accepts what arrives | Medium, requires continuous joint agreement | Low to medium, owned entirely by the downstream team |
| Organisational relationship required | Any, works even with unknown future consumers | Cooperative, both teams have a seat at the table | Asymmetric, downstream has little or no influence | Highly cooperative, near-peer teams | Any, does not require upstream's cooperation at all |
| Best suited to | A platform serving many, possibly unknown, downstream consumers | Two teams building one integration together with mutual investment | A downstream team integrating with a system it cannot influence, such as a vendor | Two teams that genuinely co-own one concept and can coordinate tightly | A downstream team protecting itself from an upstream model it does not trust to stay stable |

Reading of the table. Open Host Service is the pattern that scales, it pays
a fixed governance cost once and amortises it across every consumer, which
is exactly why Customer-Supplier and Conformist both degrade as the number
of integrations grows while Open Host Service does not. Anti-Corruption
Layer solves a closely related problem from the opposite side of the
relationship, and the two frequently appear together, a well-designed
consumer of an Open Host Service still wraps that contract in its own
Anti-Corruption Layer so the consumer's internal model is equally
insulated from the upstream contract's evolution, not only from its
internals. Shared Kernel is the outlier in the row, it is not really
competing to solve the same coordination problem, it solves the case where
sharing rather than translating is the cheaper answer, which is rare enough
that the incompatibility noted in the frontmatter is deliberate.

## 13. Related and incompatible patterns

- **Published Language.** Not merely related, effectively inseparable in
  practice. Open Host Service is the protocol boundary, Published Language
  is the vocabulary that protocol speaks, and Evans introduces both in the
  same passage of chapter 14 for exactly this reason. A team that builds
  one without deliberately building the other has built half the pattern.
- **Anti-Corruption Layer.** The consumer-side mirror of this pattern.
  Where Open Host Service is the upstream team protecting every downstream
  consumer at once, Anti-Corruption Layer is a single downstream team
  protecting itself, and a mature integration frequently has both. an Open
  Host Service on the upstream side, consumed through an Anti-Corruption
  Layer on the downstream side, so that neither side's internal model is
  exposed to the other's evolution.
- **Customer-Supplier.** The relationship Open Host Service typically
  replaces once the number of consumers stops being one. Customer-Supplier
  remains the right choice for the first, closely-coordinated relationship,
  and a team sometimes deliberately starts there and migrates to Open Host
  Service once a second consumer arrives, rather than over-building a
  general contract for a single caller from day one.
- **Conformist.** The relationship a downstream team falls into by default
  when the upstream team offers no negotiation and no translation help at
  all. A well-run Open Host Service is explicitly the alternative to
  leaving every consumer to conform, because the upstream team has done the
  translation work once so downstream teams do not each have to accept the
  internal model wholesale.
- **Shared Kernel.** Incompatible in intent, not merely different. Shared
  Kernel means two teams jointly own one piece of model and change it
  together, Open Host Service means one team owns a model and deliberately
  keeps everyone else out of it behind a translated boundary. Attempting
  both on the same relationship at once produces confusion about who is
  actually allowed to change what.
- **Bounded Context.** The precondition. Open Host Service only means
  something as a relationship drawn on a context map between two already
  identified bounded contexts, it is not a pattern that applies inside a
  single context.
- **Context Map.** The artifact this pattern is a labelled edge on. A
  context map that never states which edges are Open Host Service
  relationships is missing the information a new team member needs to know
  where they can integrate freely versus where they need a conversation
  first.
- **Domain Events.** A frequent implementation substrate rather than a
  competing pattern, see the event-carried variant in dimension 8. An
  Open Host Service expressed as a stream of published domain events is
  still Open Host Service, the events themselves are the Published
  Language.
- **API Gateway, an architectural pattern rather than a DDD pattern.**
  Frequently conflated with Open Host Service because both sit at a system
  boundary and both are commonly implemented as an HTTP layer. An API
  Gateway is usually a cross-cutting infrastructure concern, routing,
  authentication, rate limiting, that can sit in front of one or many Open
  Host Services, or in front of no Open Host Service at all if it merely
  proxies internal services directly. Putting a gateway in front of a
  pass-through host, dimension 11's first failure mode, does not turn that
  pass-through into an Open Host Service.

## 14. Refactoring path in and out

Introducing the pattern into a context that currently has ad hoc
integrations. This is not one of the named refactorings in the classical
refactoring catalog, because it operates at the architectural boundary
level rather than inside a single method, so the steps below are drawn from
DDD integration practice rather than from a single cited source.

1. Inventory every existing consumer of the context, including informal
   ones such as direct database reads, and for each one record which
   internal fields or tables it actually touches. This inventory is what
   later tells the team whether it has one relationship or genuinely many.
2. Once a second real consumer is confirmed, or credibly imminent, design
   the Published Language for the union of what those consumers need,
   deliberately choosing to omit internal fields no consumer has justified
   needing, rather than exposing everything to be safe.
3. Build the Host Translator as new code that sits beside, not inside, the
   internal domain model, mapping internal aggregates to the new published
   DTO types. Keep this step additive, do not yet remove any existing
   direct access.
4. Stand up the new protocol endpoint or event stream serving the
   translated shape, and migrate the friendliest existing consumer to it
   first as a validation that the translation is complete and correct.
5. Once the new contract is validated against a real consumer, migrate the
   remaining consumers one at a time, removing each one's direct or
   bespoke access as it moves over, so at every point in the migration the
   system is running rather than blocked on a big-bang cutover.
6. Once no consumer touches the internal model directly, add the schema
   compatibility check from dimension 11 to CI, publish the schema
   artifact, and write the deprecation and support policy down somewhere
   every consumer can find it. This step is what turns having an API into
   having a genuine Open Host Service.
7. Only now does the internal model regain the freedom described in
   dimension 3, verify that a real internal refactor can be made without
   touching the Host Translator's output shape, which is the acceptance
   test for the whole migration.

Removing the pattern when it stops earning its place. Signals include a
consumer count that dropped to one and shows no sign of growing again, or
an organisational merger that puts the upstream and downstream teams under
one roadmap where Customer-Supplier's tighter coordination is now cheaper
than the governance overhead of a formal contract.

1. Confirm the consumer count and trend, not just the count today, since a
   temporary dip is not the same as a permanent one.
2. Move the relationship to an explicit Customer-Supplier arrangement,
   agreeing directly with the remaining consumer team on a shared
   evolution cadence rather than a formal version policy.
3. Relax or retire the version negotiation machinery, the deprecation
   window commitments, and the schema-compatibility gate in CI, since they
   now protect against a population of unknown consumers that no longer
   exists.
4. Keep the Host Translator itself for one more release cycle even after
   relaxing governance, because it still provides the coupling reduction
   described in dimension 10, only remove it if the remaining consumer
   explicitly wants direct access to the internal model, which converts
   the relationship to Conformist and should be a deliberate choice, not a
   drift.

## 15. Testing and verification

Easier because of the pattern.

- The Host Translator is a pure function from internal aggregate to
  published DTO, or close to it, which makes it trivial to unit test with
  a table of representative internal states and their expected published
  output, with no HTTP server, no database, and no consumer involved.
- Consumer teams can build against a documented schema and a set of
  recorded example payloads without needing a live upstream environment at
  all, which is a testability gain the ad hoc integration this pattern
  replaces never offered.
- Because the internal model and the published model are explicitly
  separate types, a change that would silently break the contract shows up
  as a compile error or a failing mapping test the moment the internal
  type changes, rather than as a runtime surprise discovered by a
  consumer in production.

Harder because of the pattern.

- The upstream team now needs to test against multiple live protocol
  versions simultaneously if more than one is in its support window, which
  multiplies the test matrix compared with a system that only ever serves
  its current shape.
- Genuine end-to-end confidence requires testing the real consumer against
  the real contract, not just the Host Translator's output in isolation,
  because a schema-valid payload can still fail a specific consumer's
  semantic expectations in ways a unit test of the translator alone cannot
  catch.

Techniques that apply.

- **Consumer-driven contract testing**, where each consumer publishes a
  small set of expectations, a contract, against the provider, and the
  upstream team's CI runs every registered consumer's contract before any
  release. Pact is the tool most associated with this technique in
  practice, and it directly targets the version-sprawl and breaking-change
  failure modes from dimension 11 by catching an incompatible change before
  it ships rather than after a consumer reports it.
- **Schema compatibility checking in CI**, running the current Published
  Language schema against the previously published version with a
  compatibility checker appropriate to the schema format, a Protobuf or
  Avro registry's built-in check, or an OpenAPI diff tool, and failing the
  build on an incompatible change that was not accompanied by a version
  bump.
- **Golden-file or snapshot tests on the Host Translator**, asserting the
  exact published output for a fixed set of representative internal
  states, so a future internal refactor that accidentally changes the
  translator's output is caught by a diff even when no consumer has run
  their own tests yet.
- **A fake or record-and-replay double of the Open Host Service on the
  consumer side**, built from real recorded responses, so consumer test
  suites do not depend on the live upstream context being available or
  seeded with matching data.

## 16. Observability signals

The pattern's whole purpose is to decouple two teams, and decoupled teams
lose the informal visibility a tightly coupled pair has into each other's
behaviour, so deliberate telemetry has to replace that informal knowledge.

What to record.

- A request or event counter labelled by protocol version, which is the
  single most operationally important signal a governed Open Host Service
  needs, because it tells the upstream team exactly which versions still
  have live traffic before any deprecation decision.
- A per-consumer identifier on every request, via an API key, a client
  certificate, or a required client identifier header, propagated into
  logs and traces, so a specific consumer can be identified when its
  traffic pattern changes or when it needs to be contacted about an
  upcoming deprecation.
- Latency and error-rate histograms labelled by protocol version and by
  operation, so a regression introduced by an internal refactor that
  changed the Host Translator's cost is visible immediately rather than
  discovered from a downstream team's complaint.
- A schema validation failure counter on the consumer side, where
  practical, so the upstream team learns about a contract violation from
  telemetry rather than solely from a support ticket.
- A deprecated-version usage alert, firing when traffic on a version past
  its stated end-of-support date exceeds a defined threshold, mirroring
  the Kubernetes deprecated-API `Warning` header mechanism cited in
  dimension 9, which turns a passive documentation commitment into an
  active operational signal.

A healthy instance on a dashboard. Traffic is concentrated on the current
and immediately previous protocol version, with a visible, declining tail
on older versions that matches the deprecation schedule rather than a flat
line of stubborn legacy usage. Per-consumer error rates stay low and stable
across an internal upstream release, which is the direct evidence that the
Host Translator is doing its job. New consumers appear in the per-consumer
breakdown without a corresponding spike in support tickets to the upstream
team, evidence that documentation and schema alone were sufficient for
onboarding.

A failing instance. A deprecated version's traffic refuses to decline
despite its published end-of-support date approaching, which means either
the consumer registry is wrong about who owns that traffic or the
deprecation communication never reached them. A latency or error spike
appears on one specific protocol version immediately after an internal
release, which localises a regression in the Host Translator's mapping for
that version to a specific deploy. An unidentified or unauthenticated
client shows up in traffic with no registered owner, which is a signal
either that the contract is being consumed informally, defeating the whole
governance model, or that access controls on the protocol are weaker than
intended.

## 17. Security and privacy implications

Unlike a purely internal pattern, Open Host Service defines the edge of a
trust boundary by design, so its security implications are substantial
rather than incidental.

**The published contract is the attack surface, and it is intentionally
wide open to many, sometimes unknown, callers.** Every field the Host
Translator chooses to expose is a field an external actor can now read, and
every operation the protocol offers is an operation an external actor can
now attempt, which means the field-by-field deliberateness dimension 10
credits as a positive consequence is also the primary security control.
The Host Translator is exactly the place to enforce that internal fields
never leak by default, contrasted with a naive serialization of the
internal aggregate, which tends to expose whatever the internal model
happens to contain, including fields never meant for external eyes,
precisely the pass-through-host failure mode in dimension 11.

**Authentication and authorization must happen at the protocol boundary,
not be assumed from network position.** Because the pattern is designed to
serve consumers the upstream team may not know in advance, and because the
contract is documented and discoverable by design, the protocol cannot
rely on obscurity or on being reachable only from a trusted internal
network. Every one of the production examples in dimension 9 requires an
API key or an equivalent credential on every request, which is not
incidental to those systems' design, it is a direct consequence of
deliberately opening a host service to a plural, evolving consumer
population.

**Version proliferation is a security liability, not only an engineering
one.** An old, unpatched protocol version kept alive past its intended
support window because deprecation telemetry from dimension 16 was never
built is a version whose security posture nobody is actively reviewing,
which is a genuine, observed category of risk in long-lived public APIs
generally, distinct from any specific vulnerability, this is an
architectural observation rather than a claim about a documented incident
in any of the named systems above.

**Rate limiting and abuse controls belong at the Open Host Service
boundary.** Because the protocol is deliberately made easy to discover and
integrate with, it is also easy for a misbehaving or malicious consumer to
generate load against it, and the pattern's openness means the upstream
team cannot rely on a small, trusted set of known callers to self-limit.
Per-consumer rate limiting, tied to the same consumer identifier used for
the observability signals in dimension 16, is a natural extension of the
governance the pattern already requires.

On privacy specifically, the Published Language is the point at which the
upstream team makes an explicit, durable decision about what personal or
sensitive data leaves the bounded context. Because that decision is
encoded in a versioned schema rather than left implicit in whatever the
internal model happens to serialize to, Open Host Service is, when done
correctly, a genuine privacy improvement over ad hoc integration, the
Host Translator is a natural enforcement point for field-level redaction,
data minimisation, and purpose limitation, and a change to what personal
data the contract exposes is forced to be a deliberate, reviewable,
version-bumping decision rather than an accidental byproduct of an
unrelated internal refactor.

## 18. References

1. Eric Evans. *Domain-Driven Design. Tackling Complexity in the Heart of
   Software*. Addison-Wesley, 2003. ISBN 0-321-12521-5. Chapter 14,
   "Maintaining Model Integrity". Origin of Open Host Service and Published
   Language, and the source for the pattern's intent statement in
   dimension 1 and the context described in dimension 2.
2. Vaughn Vernon. *Implementing Domain-Driven Design*. Addison-Wesley,
   2013. ISBN 978-0-321-83457-7. Chapter 3, "Context Maps". Restates the
   pattern paired with Published Language and illustrates it with a
   RESTful resource design. Table of contents confirmed against
   https://gist.github.com/dimabory/4cda22040d23994a31087ffc61060ad2 and
   the publisher's own chapter listing at
   https://www.oreilly.com/library/view/implementing-domain-driven-design/9780133039900/ch03.html
   both verified 2026-08-02.
3. Domain-driven Design. A Practitioner's Guide. Glossary entry, "Open
   Host Service".
   https://ddd-practitioners.com/home/glossary/bounded-context/bounded-context-relationship/open-host-service/
   Verified 2026-08-02. Source for the statement that Published Language is
   commonly combined with Open Host Service, cited in dimension 5.
4. Microsoft. Azure Architecture Center. "Use Domain Analysis to Model
   Microservices".
   https://learn.microsoft.com/en-us/azure/architecture/microservices/model/domain-analysis
   Verified 2026-08-02. Source for the explicit naming of Open Host Service
   and Published Language as a microservices context-mapping
   recommendation, and the pointer to OpenAPI as the concrete Published
   Language artifact, cited in dimensions 8 and 9.
5. Stripe. "SDK versioning" and "API versioning".
   https://docs.stripe.com/sdks/versioning and
   https://docs.stripe.com/api/versioning
   Verified 2026-08-02. Source for the Stripe production use in dimension
   9, the `Stripe-Version` header mechanism, and the monthly-additive,
   semi-annual-breaking release model.
6. GitHub. "API Versions".
   https://docs.github.com/en/rest/about-the-rest-api/api-versions
   Verified 2026-08-02. Source for the GitHub REST API production use in
   dimension 9, the `X-GitHub-Api-Version` header, the default version
   behaviour, the HTTP 410 response for unsupported versions, and the
   24-month support commitment.
7. Shopify. "About Shopify API versioning" and "About REST Admin API
   versioning". https://shopify.dev/docs/api/usage/versioning and
   https://shopify.dev/docs/api/admin-rest/usage/versioning
   Verified 2026-08-02. Source for the Shopify production use in dimension
   9, the quarterly dated-version release schedule, and the twelve-month
   minimum support with nine-month overlap policy.
8. Kubernetes. "Kubernetes Deprecation Policy".
   https://kubernetes.io/docs/reference/using-api/deprecation-policy/
   mirrored at
   https://github.com/kubernetes/website/blob/main/content/en/docs/reference/using-api/deprecation-policy.md
   Verified 2026-08-02. Source for the Kubernetes production use in
   dimension 9, the versioned API group model, the alpha, beta, and stable
   support windows, the rule that removal requires an API group version
   increment, and the deprecated-endpoint `Warning` header behaviour since
   Kubernetes 1.19.

## Code examples

Three languages, chosen because each demonstrates a distinct, real
implementation shape for the Host Translator described in dimension 5.
TypeScript shows the pattern as a set of narrow interfaces with an explicit
version-tagged handler, the shape most REST or GraphQL back ends actually
use. Go shows it as a package boundary with unexported internal types and
an exported translator, which is the idiomatic way Go enforces the
boundary the compiler can check. Python shows it as a pair of frozen
dataclasses with a standalone translation function, the shape most Python
services actually use at a service boundary. Java was attempted as a
fourth language but is omitted, this machine has the `javac` and `java`
launcher stubs on its PATH but no installed JDK behind them, both commands
fail with "Unable to locate a Java Runtime" before compiling a single
line, so a Java sample is not included rather than presented as verified
when it was not. All three included samples were compiled or run locally
before inclusion.

### TypeScript

Compiled with `npx tsc --strict --noEmit open-host-service.ts`, zero
errors.

```typescript
// Internal domain model. Never leaves this module.
interface OrderLine {
  sku: string;
  quantity: number;
  unitPriceCents: number;
}

interface Order {
  id: string;
  customerId: string;
  lines: OrderLine[];
  internalRiskScore: number; // never published
  placedAt: Date;
}

// Published Language, version 3. This is the only shape any consumer sees.
interface PublishedOrderV3 {
  orderId: string;
  itemCount: number;
  totalCents: number;
  placedAt: string; // ISO 8601, stable regardless of internal Date handling
}

// The Host Translator. Pure function, no side effects, easy to unit test.
function toPublishedOrderV3(order: Order): PublishedOrderV3 {
  const totalCents = order.lines.reduce(
    (sum, line) => sum + line.unitPriceCents * line.quantity,
    0,
  );
  return {
    orderId: order.id,
    itemCount: order.lines.reduce((sum, line) => sum + line.quantity, 0),
    totalCents,
    placedAt: order.placedAt.toISOString(),
  };
}

// Simulated protocol boundary. In a real system this is an HTTP handler.
function handleGetOrder(order: Order, version: "v3"): PublishedOrderV3 {
  if (version !== "v3") {
    throw new Error(`unsupported protocol version. ${version}`);
  }
  return toPublishedOrderV3(order);
}

const sample: Order = {
  id: "ord_42",
  customerId: "cust_9",
  lines: [
    { sku: "widget", quantity: 2, unitPriceCents: 500 },
    { sku: "gadget", quantity: 1, unitPriceCents: 1200 },
  ],
  internalRiskScore: 0.03,
  placedAt: new Date("2026-08-01T10:00:00Z"),
};

const published = handleGetOrder(sample, "v3");
console.log(JSON.stringify(published, null, 2));
```

### Go

Run with `go run open_host_service.go`, output verified.

```go
package main

import (
	"encoding/json"
	"fmt"
	"time"
)

// internal domain types, deliberately unexported outside this file's role
type orderLine struct {
	sku            string
	quantity       int
	unitPriceCents int
}

type order struct {
	id                string
	customerID        string
	lines             []orderLine
	internalRiskScore float64 // never published
	placedAt          time.Time
}

// PublishedOrderV3 is the Published Language. Exported and stable.
type PublishedOrderV3 struct {
	OrderID    string `json:"order_id"`
	ItemCount  int    `json:"item_count"`
	TotalCents int    `json:"total_cents"`
	PlacedAt   string `json:"placed_at"`
}

// toPublishedOrderV3 is the Host Translator. Only function that sees both types.
func toPublishedOrderV3(o order) PublishedOrderV3 {
	total := 0
	items := 0
	for _, line := range o.lines {
		total += line.unitPriceCents * line.quantity
		items += line.quantity
	}
	return PublishedOrderV3{
		OrderID:    o.id,
		ItemCount:  items,
		TotalCents: total,
		PlacedAt:   o.placedAt.UTC().Format(time.RFC3339),
	}
}

func handleGetOrder(o order, version string) (PublishedOrderV3, error) {
	if version != "v3" {
		return PublishedOrderV3{}, fmt.Errorf("unsupported protocol version. %s", version)
	}
	return toPublishedOrderV3(o), nil
}

func main() {
	sample := order{
		id:         "ord_42",
		customerID: "cust_9",
		lines: []orderLine{
			{sku: "widget", quantity: 2, unitPriceCents: 500},
			{sku: "gadget", quantity: 1, unitPriceCents: 1200},
		},
		internalRiskScore: 0.03,
		placedAt:          time.Date(2026, 8, 1, 10, 0, 0, 0, time.UTC),
	}

	published, err := handleGetOrder(sample, "v3")
	if err != nil {
		panic(err)
	}
	out, _ := json.MarshalIndent(published, "", "  ")
	fmt.Println(string(out))
}
```

### Python

Run with `python3 open_host_service.py`, output verified.

```python
from dataclasses import dataclass
from datetime import datetime, timezone


# Internal domain model. Never leaves this module.
@dataclass(frozen=True)
class OrderLine:
    sku: str
    quantity: int
    unit_price_cents: int


@dataclass(frozen=True)
class Order:
    id: str
    customer_id: str
    lines: list[OrderLine]
    internal_risk_score: float  # never published
    placed_at: datetime


# Published Language, version 3. This is the only shape any consumer sees.
@dataclass(frozen=True)
class PublishedOrderV3:
    order_id: str
    item_count: int
    total_cents: int
    placed_at: str


# The Host Translator. Pure function, no side effects, easy to unit test.
def to_published_order_v3(order: Order) -> PublishedOrderV3:
    total_cents = sum(
        line.unit_price_cents * line.quantity for line in order.lines
    )
    item_count = sum(line.quantity for line in order.lines)
    return PublishedOrderV3(
        order_id=order.id,
        item_count=item_count,
        total_cents=total_cents,
        placed_at=order.placed_at.astimezone(timezone.utc).isoformat(),
    )


# Simulated protocol boundary. In a real system this is an HTTP handler.
def handle_get_order(order: Order, version: str) -> PublishedOrderV3:
    if version != "v3":
        raise ValueError(f"unsupported protocol version. {version}")
    return to_published_order_v3(order)


if __name__ == "__main__":
    sample = Order(
        id="ord_42",
        customer_id="cust_9",
        lines=[
            OrderLine(sku="widget", quantity=2, unit_price_cents=500),
            OrderLine(sku="gadget", quantity=1, unit_price_cents=1200),
        ],
        internal_risk_score=0.03,
        placed_at=datetime(2026, 8, 1, 10, 0, 0, tzinfo=timezone.utc),
    )
    published = handle_get_order(sample, "v3")
    print(published)
```

The Python form separates the two record types the same way the Go and
TypeScript samples do, and the boundary function raises rather than
silently accepting an unrecognised version, which is the same fail-closed
behaviour the other two samples apply to a protocol negotiation the Host
Translator does not recognise.
