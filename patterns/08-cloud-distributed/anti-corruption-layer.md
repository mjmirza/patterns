---
name: Anti-Corruption Layer
slug: anti-corruption-layer
family: 08-cloud-distributed
category: Integration
aliases: [ACL, Translation Layer (informally, though Evans treats the two as distinct)]
first_described: "Evans 2003"
maturity: canonical
related: [adapter, facade, strangler-fig, circuit-breaker, retry, bulkhead, saga, bounded-context, shared-kernel, open-host-service]
incompatible_with: [shared-kernel]
verified: 2026-08-02
---

# Anti-Corruption Layer

## 1. Name, aliases, and lineage

The canonical name is Anti-Corruption Layer, almost always shortened to ACL in
conversation and in code. That abbreviation collides with the far more common
meaning of ACL as Access Control List, and a reader skimming a pull request
that mentions "the ACL" without context has a real chance of guessing wrong.
This entry writes the name out in full at every point where the ambiguity
could bite, and the same discipline is worth carrying into production code
and documentation.

Eric Evans introduced the pattern in *Domain-Driven Design. Tackling
Complexity in the Heart of Software*, Addison-Wesley, 2003, in Part IV,
chapter 14, "Maintaining Model Integrity," under the section heading
ANTICORRUPTION LAYER, written in the book as one capitalized word without
a hyphen. The chapter's own working notes state the core claim plainly.
"An ANTICORRUPTION LAYER defends your system from having to adapt to a
divergent external model" (Eric Evans, Domain-Driven Design, Addison-Wesley,
2003, chapter 14; discussion excerpts published at
[dddcommunity.org, "Chapter 14"](https://www.dddcommunity.org/uncategorized/ch14/),
verified 2026-08-02). Evans draws a line inside chapter 14 that most later
retellings drop. a TRANSLATION LAYER exists where two teams have reached a
meeting of minds and are willing to accommodate each other's models, while an
ANTICORRUPTION LAYER exists where one team has judged the other model
incompatible or of lower quality and refuses to let it leak in. The chapter
notes frame this with a defensive image, physical barriers and a guarded
crossing point, set against a bridge, and state that the difference is one of
"intent, in posture" rather than of mechanism (same source, verified
2026-08-02). Two implementations of the pattern can be identical line for
line and still be a Translation Layer in one team's mouth and an
Anti-Corruption Layer in another's, because the label describes a judgment
about the other system's model, not a shape of code.

Twenty years later, the pattern was catalogued a second time with a
different framing. The Azure Architecture Center lists Anti-Corruption Layer
as one of its cloud design patterns, crediting Evans by name in its opening
line, but describing it in purely mechanical terms as a facade or adapter
between "different subsystems that don't share the same semantics" that
exists so that "dependencies on outside subsystems don't limit an
application's design" ([Anti-Corruption Layer pattern, Azure Architecture
Center, Microsoft Learn](https://learn.microsoft.com/en-us/azure/architecture/patterns/anti-corruption-layer),
verified 2026-08-02). AWS Prescriptive Guidance takes the same mechanical
framing further, scoping the pattern narrowly to one recurring situation. a
monolith calling a service that has recently been extracted out of it during
a migration, where the extracted service's domain model no longer matches the
shape it had inside the monolith
([Anti-corruption layer pattern, AWS Prescriptive
Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/acl.html),
verified 2026-08-02).

These are not the same pattern wearing two names, and treating them as
interchangeable is the most common source of confusion in practitioner
writing. Evans's version is a strategic decision about which of two models a
team refuses to let corrupt its own, made in the context of a broader map of
bounded-context relationships that also includes Shared Kernel, Conformist,
Customer/Supplier, and Open Host Service. It applies as much between two
internal teams that have simply grown apart as it does between an internal
system and an external one, and it carries a judgment. this other model is
not good enough to live inside mine. The cloud-catalog version generalizes
the mechanism to any semantic mismatch across an integration boundary,
including one where the other side's model is not bad, merely different and
outside your release control, and it is most often invoked for a single
concrete scenario. a temporary seam during a monolith-to-service migration.
Both framings earn the name. Evans's is the deeper, judgment-carrying
original; the cloud catalogs are a narrower, migration-flavored specialization
of the same mechanism, and this entry treats both as legitimate while keeping
the distinction visible, because conflating them is exactly how an entry gets
built to defend a domain model but gets sold to a team as a disposable
migration shim, or the reverse.

A third, purely structural framing shows up in day-to-day code review, where
"anti-corruption layer" is used loosely for what is really only a Facade
(GoF) or Adapter (GoF) applied at a system boundary with no domain judgment
behind it at all. Section 4 draws that line explicitly, because reaching for
the strategic-sounding name when nothing strategic is happening is its own
small form of corruption, of vocabulary rather than of a model.

## 2. Problem and context

A team owns a domain model it has deliberately kept clean. types named for
the business, invariants enforced in one place, a vocabulary the whole team
shares without translation. That model has to talk to a system the team does
not control. a legacy monolith that predates the team, a service another
team owns and evolves on its own schedule, an acquired company's database, a
vendor's API that changes on the vendor's release calendar, not the team's.

Left unguarded, the foreign system's shape starts to show up everywhere the
team's own code touches it. A field that only exists because of a botched
data migration five years ago becomes a nullable property the domain model
has to account for. An enum with fourteen legacy status codes, half of them
meaning roughly the same thing for historical reasons nobody remembers,
becomes a switch statement duplicated at every call site. A boolean flag
named for an internal implementation detail of the other system becomes part
of the vocabulary the team uses to talk about its own business, because that
is the name that showed up in the API response and nobody stopped to rename
it. None of this happens in one commit. It accretes, one call site at a
time, until the domain model no longer speaks the team's own concepts. it
speaks a negotiated compromise between the team's concepts and whatever the
other system happened to expose. That drift is the corruption the chapter
title names, and it is corruption of a model, not merely of a database
column.

The situation recurs in three recognizable shapes.

- A monolith is being taken apart feature by feature. During the transition,
  code still inside the monolith has to call a feature that has already been
  extracted into a service, and that service's newly designed model does not
  match the shape the feature had when it lived inside the monolith. Every
  extraction reopens this problem, and it lasts exactly as long as the
  monolith still has callers of the old shape.
- Two teams, each with a bounded context that grew independently, need to
  exchange data without merging their models. Two order-management systems
  after an acquisition is the textbook case. one calls the customer's postal
  code `zip`, the other calls it `postleitzahl` and stores it with a country
  prefix baked into the string.
- A vendor or partner's API is the only way to reach functionality the team
  does not want to build itself, and that API's shape reflects the vendor's
  own history, not the team's domain. The vendor ships breaking changes on
  its own schedule, and the team has no seat at that table.

All three share the same underlying shape. one side's model is not
negotiable, and the team decides to pay a translation cost once, at a single
seam, rather than let the foreign shape spread through every place that
needs the data.

## 3. Forces

The weighting of these forces below reflects the judgment behind choosing
this pattern rather than a citable fact, and is stated as such.

- **Model integrity against integration necessity.** The whole reason to
  build the layer is to keep the domain model clean, but the business
  functionality genuinely lives, in part, on the other side of the boundary.
  Refusing to integrate is not on the table; the question is only where the
  translation happens.
- **Isolation against added latency.** Every call through the layer is at
  minimum one extra function call, and often one extra network hop if the
  layer runs as its own service. That cost buys decoupling; whether it is
  worth paying depends on how latency-sensitive the call path already is.
- **Absorbing churn at one seam against scattering it everywhere.** The team
  does not control the other side's release schedule. Concentrating the
  fallout of a foreign schema change into one translator is usually the
  entire point, but it also means that translator becomes a single point
  every future foreign-side change has to pass through.
- **One-time build and ongoing run cost against the compounding cost of
  corruption.** A layer with its own tests, its own deployment if it is a
  service, and its own on-call burden is real, recurring cost. The
  alternative cost, a domain model slowly redrawn around someone else's
  schema, is diffuse and easy to discount until it has already happened.
- **Ownership and team topology.** Who builds and runs the layer changes who
  bears its maintenance. Evans's own framing favors the calling team owning
  it, since that team is the one being protected, but a shared or
  platform-owned layer is common in practice when several consuming teams
  would otherwise each build their own.
- **Transience against permanence.** A layer built to bridge a migration
  window has a natural expiry, when the legacy side is gone. A layer built to
  face a vendor API has no natural expiry at all, because the vendor is not
  going anywhere. Confusing the two, treating a permanent boundary as
  temporary scaffolding or a temporary seam as a permanent fixture, is a
  recurring source of the failure modes in section 11.
- **Cognitive load, concentrated against distributed.** Centralizing
  translation in one place lowers cognitive load everywhere else in the
  codebase, but it raises the load of understanding that one place, which can
  turn into its own kind of complexity if the layer accumulates
  responsibilities it was never meant to carry.

## 4. Applicability and non-applicability

Reach for an Anti-Corruption Layer when at least one of these holds.

- Integrating with a system whose model the team judges incompatible with,
  or of lower quality than, its own, and the team wants to protect its
  domain model rather than accommodate the other one.
- Running a migration where a monolith and a newly extracted service must
  call each other for a bounded window, and neither side's callers should
  have to know that the other side's shape changed underneath them
  (the scenario AWS Prescriptive Guidance scopes the pattern to; verified
  2026-08-02).
- Integrating a vendor or partner API whose shape and release schedule the
  team has no control over, and the cost of a schema change reaching every
  call site directly would be unacceptable.
- A core subdomain, the part of the system that is the actual competitive
  differentiator, must stay pristine even at the cost of an extra layer,
  because that subdomain is where the team's real design investment lives.
- Two bounded contexts have genuinely diverged in vocabulary and the team has
  the standing to refuse a Conformist relationship (silently adopting the
  other side's model wholesale) in favor of translating on its own terms.

**Do not** reach for this pattern in the following situations, and treat
each as a reason to actively avoid it rather than merely a case where it
happens not to help.

- The two systems already share compatible semantics. Inserting a
  translation boundary between models that already agree adds latency and a
  maintenance surface for zero protective value; that relationship is a
  Shared Kernel or a Partnership in Evans's vocabulary, not an
  Anti-Corruption Layer situation, and the two are incompatible by
  definition (you cannot simultaneously defend a boundary and deliberately
  share the model across it).
- A short-lived script or a prototype that will be thrown away. The cost of
  building and testing a translation boundary is not worth paying for code
  with no expected lifetime.
- The team actually wants, and has the organizational standing to get, the
  two models to converge. An Anti-Corruption Layer that never gets removed
  can quietly institutionalize a split that should have been fixed by
  changing the upstream model instead; see the "living forever" failure
  mode in section 11.
- An extremely latency-sensitive hot path where even a lightweight
  in-process translation step is a measurable fraction of the call's total
  time budget. Measure first; do not default to inserting a layer on a
  microsecond-budget path without a benchmark showing the cost is
  acceptable.
- There is no real semantic gap. mapping between two structurally identical
  DTOs is a copy, not a domain-boundary defense, and naming it an
  Anti-Corruption Layer overstates what is happening.
- The only difference between the two shapes is field naming or a missing
  wrapper object, with no business-rule reconciliation involved. A plain
  Adapter or Facade (GoF) is the honest name here; see section 13 for how
  the strategic and structural patterns differ.

## 5. Structure

- **Consumer.** Code inside the protected bounded context that needs a
  capability the foreign system provides. It calls the layer using only the
  domain's own types and vocabulary, and has no knowledge of the foreign
  system's shape, protocol, or quirks.
- **Facade (also called the Port).** The layer's only public surface, and
  the only part the Consumer ever sees. Its method signatures are expressed
  entirely in the domain's own types, both for arguments and for return
  values, including errors.
- **Translator, one per direction.** A request translator converts a domain
  object into the shape the foreign system expects; a response translator
  converts what the foreign system returns, including its errors, back into
  domain types or domain-meaningful exceptions. This is where the field
  renaming, unit conversion, enum reconciliation, and default-value logic
  for missing foreign fields actually live, and it is the part worth the
  most unit-test attention, since a silent mistranslation here produces
  wrong data that looks correct to everything downstream.
- **Gateway (also called the Adapter, in the narrow GoF sense).** The
  technical transport concern. the HTTP client, the message queue producer,
  the SOAP client, whatever protocol the foreign system actually speaks.
  Kept separate from the Translator so that translation logic can be unit
  tested without touching a network, a queue, or a mock server.
- **External system.** The foreign model, outside the team's control, with
  its own release schedule and its own reasons, often historical, for the
  shape it exposes.
- **Resilience collaborators, optional but common.** In production, the
  layer is frequently the single choke point for a dependency the team does
  not control, so it is a natural place to attach a Circuit Breaker, a
  Retry policy, or a cache, discussed further in section 13.

## 6. ASCII structure diagram

```
+---------------------------------------------------------------+
|                     Protected Bounded Context                 |
|                                                                 |
|  +------------+       +------------------------------------+  |
|  |  Consumer  | ----> |       Anti-Corruption Layer         |  |
|  | (domain    |       |                                      | |
|  |  service)  | <---- |  +----------+   +----------------+  |  |
|  +------------+       |  | Facade   |-->|  Translator    |  |  |
|                        |  | (Port)   |   |  (req + resp)  |  |  |
|                        |  +----------+   +--------+-------+  |  |
|                        |                          |          |  |
|                        |                          v          |  |
|                        |                 +------------------+ |  |
|                        |                 |      Gateway     | |  |
|                        |                 | (HTTP, SOAP, MQ) | |  |
|                        |                 +---------+--------+ |  |
|                        +---------------------------|----------+  |
+----------------------------------------------------|-------------+
                                                       |
                                                       v
                                    +-------------------------------+
                                    |    External / Legacy System    |
                                    |   foreign model, own schema,   |
                                    |     own release schedule       |
                                    +-------------------------------+
```

## 7. Dynamics

A normal request follows a fixed round trip. the Consumer never sees
anything but its own domain types, and every foreign shape is confined to
the space between the Translator and the Gateway.

```
Consumer      Facade         Translator       Gateway       External
   |             |                |               |             |
   |--callByID-->|                |               |             |
   |             |--toExternal()->|               |             |
   |             |                |---call------->|             |
   |             |                |               |--request--->|
   |             |                |               |<--response--|
   |             |                |<---return------|             |
   |             |<--toDomain()---|               |             |
   |<--Domain----|                |               |             |
   |   Object    |                |               |             |
```

The failure path matters as much as the happy path, and it is where teams
most often skip the translation step. When the Gateway call fails, whether
by timeout, a transport error, or a foreign error payload, the Translator's
job is to turn that failure into a domain-meaningful outcome rather than let
it propagate raw. A SOAP fault code or an HTTP 409 with a vendor-specific
error body has no meaning to the Consumer; a domain exception such as
`OrderAlreadyFulfilled` does. Skipping this step is the shortcut most often
taken under deadline pressure, and it is the one that reintroduces exactly
the corruption the pattern exists to prevent, only on the error path
instead of the success path.

```
Consumer      Facade         Translator       Gateway       External
   |             |                |               |             |
   |--callByID-->|                |               |             |
   |             |--toExternal()->|               |             |
   |             |                |---call------->|             |
   |             |                |               |--request--->|
   |             |                |               |<--409 fault-|
   |             |                |<--rawError-----|             |
   |             |                | (translate to  |             |
   |             |                |  domain error) |             |
   |             |<--DomainError--|               |             |
   |<--throws----|                |               |             |
```

## 8. Implementation variants

- **In-process class, no separate deployment.** The Facade, Translator, and
  Gateway are all classes inside the calling application's own process. This
  is the lightest-weight variant and the one AWS Prescriptive Guidance shows
  as its reference implementation, where the layer is a class such as
  `UserServiceFacade` sitting inside the monolith and calling out to the
  newly extracted service ([AWS Prescriptive
  Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/acl.html),
  verified 2026-08-02). It suits the monolith-migration scenario directly,
  since the layer lives exactly where the old code used to.
- **Dedicated service or sidecar.** When several independent consumers need
  the same translation, or when the translation logic is large enough to
  scale or fail on its own, the layer runs as its own deployable unit. Azure
  Architecture Center's own reference implementation places the layer inside
  a serverless function reached through an API gateway, so that
  authentication, throttling, and the REST facade are handled by the
  gateway and the domain-mapping logic lives in the function
  ([Azure Architecture
  Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/anti-corruption-layer),
  verified 2026-08-02).
- **Event-driven, asynchronous translation.** Instead of a synchronous
  request-response call, the layer consumes events published in the foreign
  system's shape and republishes translated domain events on the team's own
  topic. The same Azure documentation names this explicitly as an
  alternative to the synchronous form, built on a message broker so that the
  domain side is decoupled from the foreign system's own throughput limits
  (same source, verified 2026-08-02).
- **One-directional versus bidirectional.** Some boundaries only need
  protection reading data in (a vendor feed the team consumes but never
  writes back to); others need the full round trip, translating both
  outbound commands and inbound responses.
- **Language-idiomatic shapes.** In TypeScript and Python, the Facade is
  commonly an interface or a Protocol plus a pair of pure mapping functions.
  In Go, the Facade is an interface satisfied by a struct that wraps the
  Gateway, and foreign errors are wrapped into a domain error type rather
  than passed through unchanged, so the Consumer's error-handling code never
  needs to know about the foreign system's error shape. In a functional
  style, the Translator collapses into two pure functions, `toExternal` and
  `toDomain`, passed as arguments to a small higher-order wrapper around the
  Gateway call, with no class at all.

## 9. Known production uses

Michelin's engineering team documented a live production use of this
pattern while modernizing an order system. Their legacy relational schema
held order data across nine tables joined by foreign keys, "with many flags
and fields that were not being utilized." They chose to route the migration
through an Anti-Corruption Layer that consolidated those nine tables into a
single JSONB record for the modern application, deliberately excluding
unused legacy fields during translation. The account is also candid about
the pattern's real cost. the team weighed whether reconciliation logic
belonged inside the layer or in a separate microservice, and warned that
choosing wrong "could prove to be detrimental to our modern application and
our timelines when we remove the ACL," noting their own layer grew "much
more complex than the original solution" once they decided to have the
modern application own new data at creation time rather than only at
migration time (Ruthie Ballenger, "Anti-Corruption Layer. Transforming
Legacy Applications into Modern Cloud Native Applications," Michelin
Engineering Blog, published 2026-02-12, verified 2026-08-02, at
[blogit.michelin.io](https://blogit.michelin.io/anti-corruption-layer/)).

AWS publishes an official reference implementation of the pattern in the
`aws-samples` GitHub organization, built for the monolith-to-Lambda
migration scenario described in section 8. a `UserInMonolith` class calling
through a `UserServiceACL` class that translates to and from a user service
exposed behind Amazon API Gateway and implemented as an AWS Lambda function
([aws-samples/anti-corruption-layer-pattern,
GitHub](https://github.com/aws-samples/anti-corruption-layer-pattern),
verified 2026-08-02, referenced from
[AWS Prescriptive
Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/acl.html)).
This is AWS's own vendor-published reference rather than a named customer's
production system, and this entry states that distinction plainly rather
than implying otherwise.

Microsoft's Azure Architecture Center likewise ships a documented reference
architecture for the pattern, routing external exposure and authentication
through Azure API Management, implementing the domain-mapping logic in an
Azure Function named `ProcessOrderFunction`, and wiring Azure Monitor and
Application Insights to trace translation latency and error rates separately
from the legacy system's own latency ([Azure Architecture
Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/anti-corruption-layer),
verified 2026-08-02). As with the AWS example, this is a vendor's own
documented reference architecture, offered here for the concreteness of its
observability wiring rather than as evidence of a specific customer's
deployment.

Outside the cloud vendors, the pattern also has a widely referenced open
source teaching implementation in the `iluwatar/java-design-patterns`
project, an MIT-licensed catalog of pattern implementations used across the
Java community as a reference when a team is building its own version of a
pattern for the first time. Its Anti-Corruption Layer example models a
`LegacyShop` with a flat `LegacyOrder` structure against a `ModernShop` with
a nested `Customer` and `Shipment` model, with an `AntiCorruptionLayer`
class validating and translating orders in both directions so the two shops
can run side by side during a migration ([Anti-Corruption Layer pattern,
Java Design
Patterns](https://java-design-patterns.com/patterns/anti-corruption-layer/),
verified 2026-08-02). Like the two vendor examples, this is a reference
implementation rather than a live production deployment, named here because
of how frequently it is copied into real codebases as a starting point.

## 10. Consequences

**Positive.**

- The domain model stays named for the business rather than for a foreign
  schema, and stays that way even as the foreign system changes underneath
  the layer.
- The cost of an awkward or low-quality external API is paid once, at one
  seam, instead of being repeated at every call site that needs the data.
- It enables incremental migration. new code is written entirely against
  the clean domain shape and never has to touch the legacy shape directly,
  which is what lets a Strangler Fig migration proceed feature by feature.
- It gives the team one obvious place to attach resilience concerns, retry
  policies, a circuit breaker, or a cache, for a dependency it does not
  control.
- The domain-facing side becomes trivially testable with fakes; the
  translation logic becomes testable in complete isolation from the
  network, which is usually the fastest and highest-value part of the test
  suite (see section 15).

**Negative.**

- Every call pays an extra hop, or at minimum an extra function call, and if
  the layer is deployed as its own service it is extra infrastructure to
  build, scale, and keep on call for. AWS's own guidance lists this
  explicitly among the pattern's operational costs, alongside the layer
  becoming a single point of failure and a scaling bottleneck if it is
  shared across many consumers ([AWS Prescriptive
  Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/acl.html),
  verified 2026-08-02).
- Two shapes of the same concept now exist side by side, the domain type and
  the foreign shape, and someone has to keep the mapping between them
  correct as either side evolves.
- Because the layer is the one place that understands both worlds, it is a
  natural dumping ground for logic that does not obviously belong anywhere
  else, which is the leading failure mode discussed in section 11.
- A layer built as migration scaffolding, but never decommissioned once the
  migration finishes, becomes a permanent translation tax the team keeps
  paying without ever re-evaluating whether it is still earning its keep.

## 11. Failure modes and misuse

**Symptom.** Pull requests touching the Anti-Corruption Layer module grow
steadily larger, and new team members learn, by word of mouth, that adding a
special case here is the path of least resistance. **Cause.** Because the
layer already understands both models, it becomes the easiest place to drop
logic that actually belongs elsewhere, a business rule about reconciling a
legacy discount code with a modern pricing engine, for instance, which is a
domain decision, not a translation. **Fix.** Hold the layer to translation
only, shape and vocabulary conversion with no decisions attached. Anything
that decides something, rather than merely renames or restates it, belongs
in a domain service the layer calls into, not inside the translator itself.

**Symptom.** A layer estimated to run for three months during a migration
is still running three years later, and nobody on the current team can
explain why some of its mapping branches exist. **Cause.** The migration it
was scaffolding stalled or was deprioritized, and the layer's removal was
never tracked as its own piece of work. **Fix.** Record an explicit removal
criterion when the layer is created, a specific event such as "last legacy
caller migrated" rather than a vague someday, and track it as technical
debt with an owner, exactly as AWS's own guidance recommends when the
intended use is interim rather than permanent ([AWS Prescriptive
Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/acl.html),
verified 2026-08-02).

**Symptom.** Under load, a distributed trace shows the layer itself as the
bottleneck, even though the systems on either side of it individually scale
fine. **Cause.** The layer is implemented as a single shared component,
often one process with one thread pool, serving every consumer, so it
becomes a chokepoint that does not scale in step with either side it
connects. **Fix.** Scale the layer independently, horizontally if it is its
own service, or partitioned per consuming service if the logic is shared,
and load-test the seam itself rather than assuming that healthy endpoints on
either side imply a healthy path between them.

**Symptom.** A change on the foreign system's side, a renamed field or a new
enum value, breaks production silently, and the break is discovered only
when a downstream invariant fails far from the layer itself. **Cause.** The
translator has no test against the real external shape, so drift on the
other side accumulates undetected until it produces bad domain data.
**Fix.** Pin a contract test, either a consumer-driven contract or a schema
snapshot replayed against a recorded real response, run on a schedule or in
CI, so the boundary fails loudly the moment the foreign shape moves, instead
of letting a malformed domain object escape into the rest of the system.

**Symptom.** Two features behave inconsistently when interpreting the same
ambiguous foreign field, and investigation reveals two different teams each
built their own partial translation for the same external system. **Cause.**
No single owned layer exists, so translation logic grew independently in
more than one place, and the two versions quietly disagree. **Fix.** Name an
explicit owner for the layer, favoring the calling team since it bears the
cost of corruption, and make the layer the only sanctioned path to the
foreign system, enforced by keeping the raw client out of any package's
public surface except the layer's own.

**Symptom.** During an outage of the external system, load against it
climbs instead of falling. **Cause.** The layer absorbed retry logic without
a circuit breaker, so every consumer's retries against an already-struggling
dependency compound the outage instead of backing off from it. **Fix.** Pair
the layer with a Circuit Breaker so that repeated failure stops generating
load rather than retrying blindly into a system that is already down; see
section 13.

## 12. Trade-off matrix

The comparison is against named alternatives, not a strawman "do nothing"
option, following the shape most catalogs skip.

| Dimension | Anti-Corruption Layer | Adapter (GoF) | Facade (GoF) | Shared Kernel (DDD) | Conformist (DDD) |
|---|---|---|---|---|---|
| Defends the domain model from foreign concepts | Yes, by explicit design intent | Only incidentally, it adapts shape, not semantic meaning | No, it simplifies access without judging the other model | No, the opposite intent, the two sides deliberately share one model | No, the downstream side absorbs the upstream model wholesale |
| Requires the two sides to agree on shared types | No, and deliberately does not | No | No | Yes, explicitly, by definition | Yes, one-sided, downstream conforms fully |
| Added indirection or latency | One extra hop, in-process or networked | Minimal, usually in-process | Minimal | None, same code and schema | None |
| Typical ownership | The consuming team, per Evans's framing | Whoever needs the adapted interface | Whoever exposes the simplified API | Jointly by both teams, requiring tight coordination | The downstream team absorbs the cost of change |
| Typical lifespan | Often transitional during a migration; permanent for uncontrollable vendor APIs | Permanent, tied to the interface it adapts | Permanent | Permanent, and costly to unwind | Permanent unless later upgraded to an Anti-Corruption Layer |

Open Host Service paired with a Published Language is worth naming
separately, because it is the mirror image rather than a direct competitor.
it protects the upstream, provider side by publishing a stable, versioned
contract, whereas an Anti-Corruption Layer protects the downstream,
consuming side against a contract it does not control. The two frequently
appear on opposite ends of the same integration. a provider that offers an
Open Host Service is making its downstream consumers' Anti-Corruption Layers
smaller and cheaper to build.

## 13. Related and incompatible patterns

Adapter and Facade (GoF) are the structural building blocks an
Anti-Corruption Layer is usually assembled from, but the strategic pattern
is not merely their sum. an Adapter changes an interface's shape to match
what a caller expects; an Anti-Corruption Layer additionally defends the
meaning of the data crossing the boundary, which is why translation of
errors and enums into domain-meaningful equivalents, not only field
renaming, is part of the pattern and not an optional extra.

Strangler Fig names the broader migration strategy that an Anti-Corruption
Layer most often serves as a component of. the layer is commonly the routing
and translation seam that lets old and new systems run side by side while
traffic gradually shifts from one to the other. Zhamak Dehghani's guidance on
breaking a monolith into microservices recommends exactly this shape when a
newly extracted service must still be called back into from the monolith.
"expose a new API from the monolith, and access the API through an
anti-corruption layer in the new service," so that the API "reflects the
well defined domain concepts and structures, even though the monolith's
internal implementation might be otherwise" (Zhamak Dehghani, "How to break
a Monolith into Microservices," martinfowler.com, verified 2026-08-02, at
[martinfowler.com/articles/break-monolith-into-microservices.html](https://martinfowler.com/articles/break-monolith-into-microservices.html)).
AWS's own Strangler Fig documentation cross-references the Anti-Corruption
Layer pattern as related content for the same reason
([AWS Prescriptive
Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html),
verified 2026-08-02).

Circuit Breaker and Retry compose naturally once the layer becomes the
single choke point for a flaky dependency the team does not control,
directly addressing the amplified-outage failure mode in section 11. Bulkhead
composes for the same reason at the resource-isolation level, keeping a slow
foreign call from starving unrelated work by giving the layer its own bounded
pool of threads or connections. Saga is worth naming because when the layer
wraps a call that is one step of a longer distributed transaction, a
translated failure has to feed into the saga's compensation logic rather than
being swallowed at the boundary, which is a common integration bug when the
two patterns meet.

Bounded Context and its accompanying Context Map are the broader vocabulary
Evans places Anti-Corruption Layer inside, alongside the sibling
relationships Shared Kernel, Conformist, Customer/Supplier, and Open Host
Service. Anti-Corruption Layer is the specific relationship a team chooses
when it refuses either of the two easier defaults, sharing a model outright
or conforming to the other side's model as-is. This is also the source of
the one direct incompatibility. Shared Kernel and Anti-Corruption Layer
cannot describe the same boundary at the same time, since choosing one is
explicitly the decision not to choose the other.

## 14. Refactoring path in and out

**Introducing the layer into code that calls a foreign system directly.**

1. Find every call site that touches the foreign system's shape directly,
   whether through a generated client, a raw HTTP call, or a shared DTO
   imported from the other system's codebase.
2. Define the team's own domain type for the concept involved, named in the
   team's own vocabulary and independent of the foreign shape, even where
   the two happen to look similar today.
3. Extract a Facade interface expressed purely in that domain type. this
   step is the strategic decision that everything else follows from.
4. Move the actual foreign call behind a Gateway, and write Translator
   functions in each direction. Mechanically this is an Extract Function
   (renamed from Extract Method in the second edition of Fowler's catalog,
   since the book moved its examples to a language with first-class
   functions) followed by an Extract Class, pulling the translation logic
   out of the call site and into its own named unit (Martin Fowler,
   Refactoring. Improving the Design of Existing Code, 2nd edition,
   Addison-Wesley, 2018; catalog entries "Extract Function" and "Extract
   Class" at [refactoring.com/catalog](https://refactoring.com/catalog/),
   verified 2026-08-02).
5. Redirect every call site found in step 1 to the new Facade, and remove
   any way to reach the raw foreign client from outside the layer's own
   package, sealing the boundary so a future call site cannot accidentally
   bypass the translation.
6. Add unit tests for the translation functions directly, plus at least one
   contract test against the real foreign shape, per section 15.

**Retiring the layer once it is no longer earning its cost**, typically
after a migration's legacy side is fully decommissioned.

1. Confirm, from telemetry or from a repository-wide search, that no caller
   still reaches the layer through the legacy shape, and that no consumer
   depends on error-normalization behavior the layer happens to also
   provide beyond translation, which is worth checking explicitly since such
   dependencies tend to be undocumented.
2. If the now-sole system's own model is clean enough that the boundary is
   no longer buying real protection, collapse the domain type and the
   foreign type into one, in a single reviewed change rather than
   incrementally, so the removal is easy to revert if something was missed.
3. Delete the Translator, the Gateway, and the layer's own package together
   with its tests in that same change.
4. Watch specifically for the case where downstream code came to rely on a
   default value the Translator silently applied for a missing legacy
   field; that behavior can be load-bearing even though it was never
   intended as a permanent feature, and it is the most common cause of a
   removal that has to be reverted.

## 15. Testing and verification

Test the Facade against a fake Gateway, in-memory and deterministic, and
assert that the Consumer's tests never need to construct or inspect anything
in the foreign shape. If a domain-side test has to import a foreign DTO to
pass, that is itself a sign the boundary has already leaked.

Give the Translator functions the largest share of test-writing effort of
anything in the layer. these are pure functions, foreign shape in, domain
shape out and back, and they are where a silent, hard-to-notice
mistranslation actually lives. Table-driven tests covering every enum value,
every historically odd flag, and every field the legacy system is known to
sometimes omit belong here, not in an integration test that may never
happen to exercise the tricky case.

Add a contract test against the real external system or, more practically,
against a recorded fixture, a captured real response replayed
deterministically, so that a schema change on the other side is caught by a
fast, reliable test rather than discovered by a flaky full-system run or,
worse, in production. This is the test suite most teams skip under deadline
pressure, and it is the one that would have caught the drift-based failure
mode in section 11.

What becomes easier because of the layer. business logic on the domain side
can be tested completely independent of the foreign system, using only
domain fakes, with no network calls and no test doubles standing in for
legacy quirks anywhere outside the layer's own test suite.

What becomes harder. a full-system test that exercises the real foreign
system now necessarily also exercises the layer, so a bug purely in
translation and a bug purely in the foreign system can look identical from
the outside, a request goes in and the wrong thing comes back. Keeping the
Translator's own unit tests fast, isolated, and run separately from any
full-system suite is what lets a failure be localized quickly instead of
requiring a full trace through the network call to find out which side broke.

## 16. Observability signals

Log and count translation failures as a signal distinct from transport
failures. an unmapped enum value, an unexpected null, a field that failed
validation, are schema drift on the foreign side, while a timeout or a 5xx
is the foreign system itself struggling. Mixing the two into one generic
"ACL error" counter hides exactly the distinction an on-call engineer needs
to triage quickly.

Give the layer its own span in distributed tracing, separate from the
foreign system's own latency, so that the translation step's contribution
to the overall request time is visible on its own rather than folded into
"time spent calling the dependency."

Track a specific counter for "unmapped value encountered" or "default
applied because a field was missing," since this tells the team the foreign
system introduced something new before that new value has a chance to
silently produce wrong domain data further downstream.

A healthy instance looks like a near-zero translation-failure rate, with
latency coming almost entirely from the actual foreign call rather than from
the translation step itself. translation should be cheap, in-memory, and
fast, and if it is not, that is its own signal that something unintended, an
accidental N+1 lookup inside a mapper is the common case, has crept into the
layer.

A failing instance shows one of two distinct shapes, and the shape tells the
on-call engineer where to look first. a rising translation-failure counter
with flat upstream latency points at schema drift on the foreign side and a
translator that needs a code change; a rising upstream latency or error rate
with a flat translation-failure counter points at the foreign system itself
degrading, which is not the layer's fault and does not need a code change to
the translator at all.

## 17. Security and privacy implications

The layer already inspects and reworks every field crossing the boundary,
which makes it a natural place to enforce input validation and
sanitization, and AWS's own guidance names this explicitly. "Because the
anti-corruption layer mediates systems that might have different trust
levels, consider enforcing input validation and sanitization at this
boundary" ([AWS Prescriptive
Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/acl.html),
verified 2026-08-02).

A translator built as a naive field-by-field copy, rather than an explicit
allowlist of the fields the domain model actually needs, defeats the
pattern's own purpose. it can carry sensitive fields, personal data or
internal-only flags the foreign system happens to expose, straight into the
domain model and from there into a database, a log line, or a downstream
event the domain side publishes, none of which were meant to be a channel
for that data.

Authentication and authorization credentials for the outbound call to the
foreign system belong in the Gateway, not in the Translator, so the
translation logic, which is where most of the unit tests live, can be
exercised in full without any secret ever needing to be present in a test
environment.

If the layer runs as a shared service reached by several internal
consumers, it becomes a single point that needs its own access control,
since it already holds credentials for, and speaks the authenticated
protocol of, the foreign system, and a compromise of the layer is a
compromise of that access for every consumer at once.

Debug logging of the raw foreign payload is a tempting move during an
incident, since the layer is exactly where an unfamiliar payload first
becomes visible, but it risks writing data that had one retention and
access policy on the foreign side into a log store governed by different,
often looser, rules. Redact or allowlist what the layer is permitted to log
at this specific boundary, rather than logging the raw payload by default.

## 18. References

1. Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
   Software*, Addison-Wesley, 2003, Part IV, chapter 14, "Maintaining Model
   Integrity," section "ANTICORRUPTION LAYER."
2. "Chapter 14," discussion notes on Evans's chapter, dddcommunity.org,
   verified 2026-08-02, [https://www.dddcommunity.org/uncategorized/ch14/](https://www.dddcommunity.org/uncategorized/ch14/).
3. "Anti-Corruption Layer Pattern," Azure Architecture Center, Microsoft
   Learn, verified 2026-08-02,
   [https://learn.microsoft.com/en-us/azure/architecture/patterns/anti-corruption-layer](https://learn.microsoft.com/en-us/azure/architecture/patterns/anti-corruption-layer).
4. "Anti-corruption layer pattern," AWS Prescriptive Guidance, verified
   2026-08-02,
   [https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/acl.html](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/acl.html).
5. `aws-samples/anti-corruption-layer-pattern`, GitHub, verified 2026-08-02,
   [https://github.com/aws-samples/anti-corruption-layer-pattern](https://github.com/aws-samples/anti-corruption-layer-pattern).
6. "Strangler fig pattern," AWS Prescriptive Guidance, verified 2026-08-02,
   [https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html).
7. Ruthie Ballenger, "Anti-Corruption Layer. Transforming Legacy
   Applications into Modern Cloud Native Applications," Michelin
   Engineering Blog, published 2026-02-12, verified 2026-08-02,
   [https://blogit.michelin.io/anti-corruption-layer/](https://blogit.michelin.io/anti-corruption-layer/).
8. Zhamak Dehghani, "How to break a Monolith into Microservices,"
   martinfowler.com, verified 2026-08-02,
   [https://martinfowler.com/articles/break-monolith-into-microservices.html](https://martinfowler.com/articles/break-monolith-into-microservices.html).
9. "Anti-Corruption Layer Pattern in Java," Java Design Patterns
   (`iluwatar/java-design-patterns`), verified 2026-08-02,
   [https://java-design-patterns.com/patterns/anti-corruption-layer/](https://java-design-patterns.com/patterns/anti-corruption-layer/).
10. Martin Fowler, *Refactoring. Improving the Design of Existing Code*,
    2nd edition, Addison-Wesley, 2018, catalog entries "Extract Function"
    and "Extract Class," verified against the online catalog 2026-08-02,
    [https://refactoring.com/catalog/](https://refactoring.com/catalog/).

## Code

The four examples below model the same scenario in TypeScript, Python, Go,
and Swift. a legacy order system exposing a flat, string-typed shape with a
numeric status code, and a domain model with a `Money` value object and an
`OrderStatus` enum. Each example shows the Facade, the Translator, and a
stub Gateway standing in for the network call, plus one failure-path
translation.

### TypeScript

```typescript
// Foreign shape, exactly as the legacy system returns it.
interface LegacyOrderRecord {
  order_id: string;
  cust_ref: string;
  amount_cents: number;
  currency_cd: string;
  status_cd: number; // 1=new 2=paid 3=shipped 9=cancelled, undocumented gaps exist
}

// Domain shape, named for the business, independent of the legacy schema.
type OrderStatus = "New" | "Paid" | "Shipped" | "Cancelled";

interface Money {
  amount: number;
  currency: string;
}

interface Order {
  orderId: string;
  customerId: string;
  total: Money;
  status: OrderStatus;
}

class UnknownLegacyStatusError extends Error {
  constructor(public readonly rawStatusCode: number) {
    super(`legacy status code ${rawStatusCode} has no known domain mapping`);
  }
}

// Gateway: the only piece that knows about transport.
interface LegacyOrderGateway {
  fetchOrder(orderId: string): Promise<LegacyOrderRecord>;
}

// Translator: pure, unit-testable, no network.
function toDomainStatus(code: number): OrderStatus {
  switch (code) {
    case 1:
      return "New";
    case 2:
      return "Paid";
    case 3:
      return "Shipped";
    case 9:
      return "Cancelled";
    default:
      throw new UnknownLegacyStatusError(code);
  }
}

function toDomainOrder(record: LegacyOrderRecord): Order {
  return {
    orderId: record.order_id,
    customerId: record.cust_ref,
    total: { amount: record.amount_cents / 100, currency: record.currency_cd },
    status: toDomainStatus(record.status_cd),
  };
}

// Facade: the only surface the domain consumer ever sees.
class OrderAntiCorruptionLayer {
  constructor(private readonly gateway: LegacyOrderGateway) {}

  async getOrder(orderId: string): Promise<Order> {
    const record = await this.gateway.fetchOrder(orderId);
    return toDomainOrder(record);
  }
}

// A fake gateway stands in for the network in this runnable sample.
class FakeLegacyOrderGateway implements LegacyOrderGateway {
  async fetchOrder(orderId: string): Promise<LegacyOrderRecord> {
    return {
      order_id: orderId,
      cust_ref: "CUST-42",
      amount_cents: 15999,
      currency_cd: "EUR",
      status_cd: 2,
    };
  }
}

async function main(): Promise<void> {
  const acl = new OrderAntiCorruptionLayer(new FakeLegacyOrderGateway());
  const order = await acl.getOrder("ORD-1001");
  console.log(order);

  try {
    toDomainStatus(77);
  } catch (err) {
    if (err instanceof UnknownLegacyStatusError) {
      console.log(`translation failure signal: ${err.message}`);
    }
  }
}

main();
```

### Python

```python
from dataclasses import dataclass
from enum import Enum
from typing import Protocol


# Foreign shape, exactly as the legacy system returns it.
@dataclass
class LegacyOrderRecord:
    order_id: str
    cust_ref: str
    amount_cents: int
    currency_cd: str
    status_cd: int  # 1=new 2=paid 3=shipped 9=cancelled, undocumented gaps exist


class OrderStatus(Enum):
    NEW = "New"
    PAID = "Paid"
    SHIPPED = "Shipped"
    CANCELLED = "Cancelled"


@dataclass(frozen=True)
class Money:
    amount: float
    currency: str


@dataclass
class Order:
    order_id: str
    customer_id: str
    total: Money
    status: OrderStatus


class UnknownLegacyStatusError(Exception):
    def __init__(self, raw_status_code: int) -> None:
        self.raw_status_code = raw_status_code
        super().__init__(
            f"legacy status code {raw_status_code} has no known domain mapping"
        )


# Gateway boundary as a Protocol so tests can substitute a fake.
class LegacyOrderGateway(Protocol):
    def fetch_order(self, order_id: str) -> LegacyOrderRecord: ...


_STATUS_MAP = {
    1: OrderStatus.NEW,
    2: OrderStatus.PAID,
    3: OrderStatus.SHIPPED,
    9: OrderStatus.CANCELLED,
}


def to_domain_status(code: int) -> OrderStatus:
    if code not in _STATUS_MAP:
        raise UnknownLegacyStatusError(code)
    return _STATUS_MAP[code]


def to_domain_order(record: LegacyOrderRecord) -> Order:
    return Order(
        order_id=record.order_id,
        customer_id=record.cust_ref,
        total=Money(amount=record.amount_cents / 100, currency=record.currency_cd),
        status=to_domain_status(record.status_cd),
    )


class OrderAntiCorruptionLayer:
    def __init__(self, gateway: LegacyOrderGateway) -> None:
        self._gateway = gateway

    def get_order(self, order_id: str) -> Order:
        record = self._gateway.fetch_order(order_id)
        return to_domain_order(record)


class FakeLegacyOrderGateway:
    def fetch_order(self, order_id: str) -> LegacyOrderRecord:
        return LegacyOrderRecord(
            order_id=order_id,
            cust_ref="CUST-42",
            amount_cents=15999,
            currency_cd="EUR",
            status_cd=2,
        )


if __name__ == "__main__":
    acl = OrderAntiCorruptionLayer(FakeLegacyOrderGateway())
    order = acl.get_order("ORD-1001")
    print(order)

    try:
        to_domain_status(77)
    except UnknownLegacyStatusError as exc:
        print(f"translation failure signal: {exc}")
```

### Go

```go
package main

import "fmt"

// LegacyOrderRecord is the foreign shape, exactly as the legacy
// system returns it. Note the undocumented status gaps.
type LegacyOrderRecord struct {
	OrderID     string
	CustRef     string
	AmountCents int
	CurrencyCd  string
	StatusCd    int // 1=new 2=paid 3=shipped 9=cancelled
}

// OrderStatus is the domain type, named for the business.
type OrderStatus string

const (
	StatusNew       OrderStatus = "New"
	StatusPaid      OrderStatus = "Paid"
	StatusShipped   OrderStatus = "Shipped"
	StatusCancelled OrderStatus = "Cancelled"
)

type Money struct {
	Amount   float64
	Currency string
}

type Order struct {
	OrderID    string
	CustomerID string
	Total      Money
	Status     OrderStatus
}

// UnknownLegacyStatusError is the domain-meaningful translation failure.
type UnknownLegacyStatusError struct {
	RawStatusCode int
}

func (e *UnknownLegacyStatusError) Error() string {
	return fmt.Sprintf("legacy status code %d has no known domain mapping", e.RawStatusCode)
}

// LegacyOrderGateway is the transport boundary. only it knows the wire shape.
type LegacyOrderGateway interface {
	FetchOrder(orderID string) (LegacyOrderRecord, error)
}

func toDomainStatus(code int) (OrderStatus, error) {
	switch code {
	case 1:
		return StatusNew, nil
	case 2:
		return StatusPaid, nil
	case 3:
		return StatusShipped, nil
	case 9:
		return StatusCancelled, nil
	default:
		return "", &UnknownLegacyStatusError{RawStatusCode: code}
	}
}

func toDomainOrder(record LegacyOrderRecord) (Order, error) {
	status, err := toDomainStatus(record.StatusCd)
	if err != nil {
		return Order{}, err
	}
	return Order{
		OrderID:    record.OrderID,
		CustomerID: record.CustRef,
		Total: Money{
			Amount:   float64(record.AmountCents) / 100,
			Currency: record.CurrencyCd,
		},
		Status: status,
	}, nil
}

// OrderAntiCorruptionLayer is the Facade. the only surface a domain
// consumer ever sees.
type OrderAntiCorruptionLayer struct {
	gateway LegacyOrderGateway
}

func NewOrderAntiCorruptionLayer(gateway LegacyOrderGateway) *OrderAntiCorruptionLayer {
	return &OrderAntiCorruptionLayer{gateway: gateway}
}

func (a *OrderAntiCorruptionLayer) GetOrder(orderID string) (Order, error) {
	record, err := a.gateway.FetchOrder(orderID)
	if err != nil {
		return Order{}, fmt.Errorf("legacy gateway call failed: %w", err)
	}
	return toDomainOrder(record)
}

// fakeLegacyOrderGateway stands in for the network in this runnable sample.
type fakeLegacyOrderGateway struct{}

func (fakeLegacyOrderGateway) FetchOrder(orderID string) (LegacyOrderRecord, error) {
	return LegacyOrderRecord{
		OrderID:     orderID,
		CustRef:     "CUST-42",
		AmountCents: 15999,
		CurrencyCd:  "EUR",
		StatusCd:    2,
	}, nil
}

func main() {
	acl := NewOrderAntiCorruptionLayer(fakeLegacyOrderGateway{})
	order, err := acl.GetOrder("ORD-1001")
	if err != nil {
		fmt.Println("unexpected error:", err)
		return
	}
	fmt.Printf("%+v\n", order)

	if _, err := toDomainStatus(77); err != nil {
		fmt.Println("translation failure signal:", err)
	}
}
```

### Swift

```swift
import Foundation

// Foreign shape, exactly as the legacy system returns it.
struct LegacyOrderRecord {
    let orderId: String
    let custRef: String
    let amountCents: Int
    let currencyCd: String
    let statusCd: Int // 1=new 2=paid 3=shipped 9=cancelled
}

// Domain shape, named for the business.
enum OrderStatus: String {
    case new = "New"
    case paid = "Paid"
    case shipped = "Shipped"
    case cancelled = "Cancelled"
}

struct Money {
    let amount: Double
    let currency: String
}

struct Order {
    let orderId: String
    let customerId: String
    let total: Money
    let status: OrderStatus
}

enum TranslationError: Error, CustomStringConvertible {
    case unknownLegacyStatus(Int)

    var description: String {
        switch self {
        case .unknownLegacyStatus(let code):
            return "legacy status code \(code) has no known domain mapping"
        }
    }
}

// Gateway boundary. only it knows the transport.
protocol LegacyOrderGateway {
    func fetchOrder(orderId: String) throws -> LegacyOrderRecord
}

func toDomainStatus(_ code: Int) throws -> OrderStatus {
    switch code {
    case 1: return .new
    case 2: return .paid
    case 3: return .shipped
    case 9: return .cancelled
    default: throw TranslationError.unknownLegacyStatus(code)
    }
}

func toDomainOrder(_ record: LegacyOrderRecord) throws -> Order {
    Order(
        orderId: record.orderId,
        customerId: record.custRef,
        total: Money(amount: Double(record.amountCents) / 100.0, currency: record.currencyCd),
        status: try toDomainStatus(record.statusCd)
    )
}

// Facade. the only surface a domain consumer ever sees.
final class OrderAntiCorruptionLayer {
    private let gateway: LegacyOrderGateway

    init(gateway: LegacyOrderGateway) {
        self.gateway = gateway
    }

    func getOrder(orderId: String) throws -> Order {
        let record = try gateway.fetchOrder(orderId: orderId)
        return try toDomainOrder(record)
    }
}

// A fake gateway stands in for the network in this runnable sample.
struct FakeLegacyOrderGateway: LegacyOrderGateway {
    func fetchOrder(orderId: String) throws -> LegacyOrderRecord {
        LegacyOrderRecord(
            orderId: orderId,
            custRef: "CUST-42",
            amountCents: 15999,
            currencyCd: "EUR",
            statusCd: 2
        )
    }
}

let acl = OrderAntiCorruptionLayer(gateway: FakeLegacyOrderGateway())
do {
    let order = try acl.getOrder(orderId: "ORD-1001")
    print(order)
} catch {
    print("unexpected error:", error)
}

do {
    _ = try toDomainStatus(77)
} catch {
    print("translation failure signal:", error)
}
```
