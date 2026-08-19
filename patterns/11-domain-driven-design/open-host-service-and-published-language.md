---
name: Open Host Service and Published Language
slug: open-host-service-and-published-language
family: 11-domain-driven-design
category: Structural
aliases: [OHS/PL, Open Host Service, Published Language, Well-Published Interface]
first_described: "Evans 2003"
maturity: canonical
related: [anti-corruption-layer, shared-kernel, customer-supplier, conformist, api-gateway, event-carried-state-transfer, hexagonal-architecture, facade]
incompatible_with: [shared-kernel, conformist]
verified: 2026-08-02
---

## 1. Name, aliases, and lineage

The canonical name is Open Host Service, almost always paired with its
companion Published Language and written as the compound OHS/PL. Eric Evans
first named both as separate context mapping patterns in Part IV of
"Domain-Driven Design. Tackling Complexity in the Heart of Software"
(Addison-Wesley, 2003), where the strategic design chapters catalog the ways
two bounded contexts can relate to one another. Evans places Open Host
Service and Published Language beside Shared Kernel, Customer-Supplier,
Conformist, Anticorruption Layer, and Separate Ways as the vocabulary a team
uses to name the integration relationship it has chosen, deliberately or by
default, with a neighboring context (Evans, "Domain-Driven Design," 2003,
Part IV). Vaughn Vernon's "Implementing Domain-Driven Design"
(Addison-Wesley, 2013) is the second primary source and the one most
practitioners actually learn the pattern from, because Vernon gives OHS/PL
a full worked treatment in his context mapping chapter and ties it directly
to REST resources, domain events, and a concrete e-commerce bounded context,
where the pattern reads as an operational design decision rather than a
catalog entry (Vernon, "Implementing Domain-Driven Design," 2013, Chapter 3).

The community shorthand OHS/PL appears throughout later DDD literature and
in practitioner tooling such as arc42's quality model catalog, which defines
Open Host Service as exposing "one well-defined protocol in a documented
shared language, so any number of consumers integrate without bespoke
per-consumer translation," and explicitly pairs it with Published Language as
"a documented, versioned shared model such as an OpenAPI or event schema"
(arc42 Quality Model, "Open Host Service," verified 2026-08-02,
https://quality.arc42.org/approaches/open-host-service). There is no
serious naming dispute in the literature. Some teams informally call the
resulting artifact a well-published interface or a public contract, but
these are descriptions of the same pattern rather than competing names, and
none of the primary or secondary sources consulted here treat OHS and PL as
separable in practice, even though Evans originally described them as two
patterns that are usually applied together.

## 2. Problem and context

A bounded context that has valuable capability inside it eventually needs to
expose that capability to other bounded contexts, and often to more than
one. The naive path is for the owning team to answer every integration
request as a special case, a bespoke endpoint for the billing team, a
different bespoke endpoint for the fulfillment team, a one-off database view
for reporting, and a direct table read for whichever team asks loudest. Each
of these bespoke integrations is cheap the first time and expensive
forever after, because every one of them is now a private contract the
owning team must never break, even though nobody wrote it down as a
contract. The owning team's internal model becomes pinned in place by
consumers who never agreed to be pinned to anything, so a rename of an
internal field breaks a downstream team the owning team did not know
existed.

The problem gets worse with the shape of the org chart. As the number of
consuming bounded contexts grows past two or three, the number of distinct
point-to-point integrations grows faster than the number of teams, because
each new consumer either negotiates its own translation with the producer or
reads the producer's internals directly. This is the same combinatorial
pressure that motivates the Facade pattern at the object level and the API
Gateway pattern at the service level, but at the strategic, team-boundary
level the cost is social as much as technical. Every new consumer is a
meeting, a support burden, and a hidden dependency the producing team
carries without being asked. Open Host Service and Published Language exist
for exactly this situation, a bounded context with a genuine capability, a
plural and growing set of consumers, and a producing team that wants to stop
negotiating the integration contract one relationship at a time.

The context in which the pattern belongs is deliberately narrower than "any
two systems talk to each other." It applies where one team is a real
upstream authority for a capability, where the number of downstream
consumers is plural or expected to grow, and where the upstream team has
both the mandate and the discipline to publish and hold a stable interface.
It does not apply to a single, tightly coupled pair of teams who can afford
to co-evolve their models together, which is the situation Shared Kernel and
Customer-Supplier are built for instead (Evans, "Domain-Driven Design,"
2003, Part IV).

## 3. Forces

Coupling versus autonomy is the central force. Publishing a stable language
decouples every consumer from the producer's internal model, but it also
freezes a piece of the producer's public surface, so every internal
refactor that would change the published shape now needs a translation
layer or a version bump instead of a plain rename. The producing team trades
some of its own latitude to move fast internally for the latitude of every
consuming team to move independently of it.

Consistency versus latency and availability shows up in how the published
language is delivered. A synchronous OHS, most often a REST or GraphQL API,
gives consumers a strongly consistent, on-demand view of the producer's
state at the cost of a network round trip and a shared availability budget.
If the producer is down, every consumer that calls it synchronously is
degraded too. A published language delivered as domain events shipped
through a broker relaxes that coupling into eventual consistency and lets
consumers keep working when the producer is briefly unavailable, at the
cost of consumers having to reason about staleness and about event
ordering. This is the same latency-versus-consistency trade the CAP theorem
names at the data layer, applied here at the integration layer (judgement).

Cost and team topology matter because a Published Language is not free to
build or to hold. It needs a schema, versioning discipline, documentation, a
deprecation policy, and usually a contract test suite, all of which are
ongoing costs the producing team pays on behalf of every consumer.
Organizations that adopt Team Topologies language would call the producing
team a platform team relative to its consumers, and the pattern only earns
its cost when the plural-consumer condition in dimension 2 actually holds.
Building an OHS for a single known consumer is paying platform-team cost for
a point-to-point relationship (judgement, drawing on the general
observation that integration patterns should match the actual number and
stability of consumers rather than an imagined future one).

Cognitive load is the force most often underweighted. A well-designed
Published Language reduces cognitive load for every consumer, because they
learn one vocabulary instead of reverse-engineering N different producers'
internals. It increases cognitive load for the producing team, who must now
think in two models at once, the internal domain model that is able to
evolve, and the published model that is a promise. Evans's own guidance is
that the published model should be a translation layer at the boundary of
the context, not the internal model itself, precisely so that the producing
team is not forced to design its domain model around what is convenient to
publish (Evans, "Domain-Driven Design," 2003, Part IV).

## 4. Applicability and non-applicability

Reach for Open Host Service and Published Language when a bounded context is
a genuine upstream authority for a capability that more than one other
context needs, when the set of consumers is plural today or is expected to
grow, when the producing team can commit to a versioning and deprecation
policy it will actually hold to, when consumers are organizationally
separate enough that co-designing a shared internal model with each of them
is not realistic, and when the integration needs to be discoverable and
self-describing rather than something each new consumer has to be walked
through by hand.

Do not reach for it in the following situations, each with the reason it
fails.

A single, stable, tightly collaborating pair of teams. If there is exactly
one consumer and the two teams already coordinate closely, a Shared Kernel
or a direct Customer-Supplier relationship is cheaper, because the
translation and versioning machinery of a Published Language is overhead
with no plural audience to amortize it across (Evans, "Domain-Driven
Design," 2003, Part IV).

A capability that is genuinely internal to one bounded context and has no
outside consumer, present or planned. Publishing a language for a capability
nobody outside the context needs is speculative generality. The YAGNI
argument against building for a hypothetical future consumer applies here
exactly as it does anywhere else, and Evans's own framing of the pattern
assumes there is already a set of teams that need the integration, not a
guess that some team someday might (Evans, "Domain-Driven Design," 2003,
Part IV).

A short-lived migration or a one-time data extraction. Building and holding
a versioned public contract is a long-term commitment. A batch job that
runs once to move data from a legacy system does not need the discipline of
a published interface, it needs a script (judgement).

A situation where the producing team cannot realistically commit to
stability. If the internal model is still in heavy flux, publishing a
language now means either breaking it repeatedly, which defeats the point,
or freezing internal design decisions prematurely to protect a contract
that was published too early. Vernon's guidance is to let the model
stabilize inside the bounded context before exposing it, and to keep the
published version deliberately conservative rather than mirroring every
internal concept (Vernon, "Implementing Domain-Driven Design," 2013,
Chapter 3).

A relationship where the consuming team is willing and able to conform to
the producer's internal model as-is with no translation. That situation is
better named and handled as the Conformist pattern, and layering an OHS/PL
translation on top of a relationship that is already a clean conformist fit
adds a contract nobody asked for (Evans, "Domain-Driven Design," 2003, Part
IV).

## 5. Structure

The pattern has four participants. The Producing Bounded Context is the
upstream authority that owns the capability and the internal domain model
behind it, and its internal types are never exposed directly. The Open Host
Service is the protocol adapter layer inside the producing context whose
sole job is translating between the internal model and the published one.
It is a Facade in the classic Gang of Four sense, applied at the boundary of
a bounded context rather than at the boundary of a class (Evans,
"Domain-Driven Design," 2003, Part IV). The Published Language is the
artifact itself, a versioned schema, whether an OpenAPI document, a
GraphQL schema, a JSON Schema, an Avro or Protobuf definition, or a
documented event catalog, that is independently readable and testable
without reading the producer's source code. The Consuming Bounded Context is
any of the plural downstream contexts that build against the Published
Language rather than against the producer's internals. Each consumer may
additionally run its own Anticorruption Layer to translate the published
language into its own internal model, and that translation is a separate,
composable pattern rather than part of OHS/PL itself.

The relationship between the participants is asymmetric by design. The
producing context owns and versions the Published Language unilaterally. It
consults consumers as a courtesy and as an input to prioritization, but it
does not require every consumer's agreement before evolving the contract,
provided it honors its stated versioning and deprecation policy. Consumers
depend on the Published Language, never on the producing context's internal
model, and the Open Host Service is the only component inside the producing
context that is permitted to know both models at once.

## 6. ASCII structure diagram

```
+-------------------------------------------------------------+
|              Producing Bounded Context                      |
|                                                               |
|   +---------------------+       +-------------------------+  |
|   | Internal Domain      |------>| Open Host Service        |  |
|   | Model (able to        |       | (translation adapter)   |  |
|   | evolve internally)    |<------|                          |  |
|   +---------------------+       +-------------------------+  |
|                                              |                |
+----------------------------------------------|----------------+
                                                v
                                   +-------------------------+
                                   |    Published Language     |
                                   |  (versioned schema. REST, |
                                   |   GraphQL, event catalog) |
                                   +-------------------------+
                                       ^        ^        ^
                                       |        |        |
                       +---------------+   +----+---+   +----------------+
                       | Consumer A     |   |Consumer B|  | Consumer C     |
                       | (own ACL, own  |   |(own ACL) |  | (own ACL)      |
                       |  internal model)|   |          |  |                |
                       +---------------+   +----------+   +----------------+
```

## 7. Dynamics

The runtime interaction differs depending on whether the Published Language
is delivered synchronously as a service, or asynchronously as a stream of
domain events, and both are legitimate implementation variants of the same
pattern.

For the synchronous request-response case, a consumer calls the Open Host
Service directly against the Published Language contract, pinning
a specific API version in the request so that the producer's later
evolution of the contract cannot silently break the call.

```
Consumer A                Open Host Service              Internal Model
    |                            |                              |
    |--- GET /v2/orders/8842 --->|                              |
    |                            |--- load Order aggregate ---->|
    |                            |<--- internal Order object ---|
    |                            | translate to Published       |
    |                            | Language shape (v2 schema)   |
    |<--- 200 OK, OrderV2 JSON --|                              |
    |                            |                              |
Consumer B                                                       |
    |--- GET /v1/orders/8842 --->|                              |
    |                            |--- load Order aggregate ---->|
    |                            |<--- internal Order object ---|
    |                            | translate to Published       |
    |                            | Language shape (v1 schema,   |
    |                            | still supported)             |
    |<--- 200 OK, OrderV1 JSON --|                              |
```

For the event-carried case, the producing context does not wait for a
consumer to ask. It publishes a domain event onto the Published Language the
moment its internal state changes, and every subscribed consumer reacts
independently and asynchronously.

```
Internal Model         Open Host Service          Event Broker
    |                       |                          |
    | Order confirmed       |                          |
    |----------------------->                          |
    |                       | translate to published    |
    |                       | OrderConfirmed v1 event    |
    |                       |------------------------->|
    |                       |                          |--> Consumer A (billing)
    |                       |                          |--> Consumer B (fulfillment)
    |                       |                          |--> Consumer C (analytics)
```

Vernon treats a domain event that crosses a bounded context boundary as
itself a member of the Published Language, subject to the same versioning
discipline as any request or response shape, and this event-carried variant
is the one he develops most fully in his worked example (Vernon,
"Implementing Domain-Driven Design," 2013, Chapter 3).

## 8. Implementation variants

The REST resource variant exposes the Published Language as a set of
versioned HTTP resources, usually documented with an OpenAPI specification
that consumers, and increasingly automated tooling, can read to generate
clients. Version pinning is handled per request or per account default,
which is the shape Stripe's public API uses. A request header or the
account's configured default selects a dated API version, and Stripe
distinguishes backward-compatible monthly releases from breaking major
releases such as its named "Acacia" release, so that an integrator who has
not opted in never sees a breaking change land under them (Stripe,
"Versioning," verified 2026-08-02,
https://docs.stripe.com/api/versioning).

The GraphQL schema variant treats the schema itself as the Published
Language and lets consumers either introspect it live or download a
canonical copy, which is the approach GitHub takes for its public GraphQL
API, offering both direct introspection against the live API and a
downloadable copy of the current public schema as the artifact integrators
build against (GitHub Docs, "Public schema," verified 2026-08-02,
https://docs.github.com/en/graphql/overview/public-schema). GraphQL's
own type system additionally gives the producing team a built-in
deprecation mechanism, the `@deprecated` directive, which lets fields be
marked as retiring without immediately removing them from the schema.

The event-schema variant, most common inside a single organization's
service mesh rather than exposed publicly, publishes domain events with a
schema enforced by a schema registry, commonly Avro or Protobuf, so that
producer and consumer are validated against the same published shape at
build or deploy time rather than discovering drift at runtime. This
variant trades API surface for event surface and is the natural fit when
the integration is mainly about state changes over time rather than
point-in-time queries.

The industry-standard variant is the case where the Published Language is
not owned by a single producing team at all, but by a standards body that
many independent producers and consumers implement against, which removes
the single-producer asymmetry from dimension 5 but keeps the same shape
of the pattern. One documented, versioned schema serves plural
integrators without bespoke per-consumer translation. HL7 FHIR for
healthcare interoperability and iCalendar for calendar data exchange are
both cited by arc42's catalog as examples of this variant (arc42 Quality
Model, "Open Host Service," verified 2026-08-02,
https://quality.arc42.org/approaches/open-host-service).

Language-idiomatic variants at the code level are modest for this pattern,
because OHS/PL is a strategic, boundary-level pattern rather than an
object-level one. The translation layer inside the Open Host Service
itself takes different shapes per language. an explicit mapper function or
class in Java and C#-style languages, a set of pure translation functions in
functional-leaning TypeScript or Go code, and a small set of `Codable`
conformances with custom `init(from:)` decoders in Swift, each doing the
same job of keeping the internal model and the published shape from ever
being the same type.

## 9. Known production uses

Stripe's public API is a documented, named Open Host Service with a
versioned Published Language. Consumers select a dated API version, monthly
releases are guaranteed backward-compatible, and major releases such as
"Acacia" are named and changelogged so integrators know precisely which
contract version they are building against, with per-SDK version pinning
documented for Ruby, Python, PHP, Java, Node, Go, and .NET clients (Stripe,
"Versioning," verified 2026-08-02, https://docs.stripe.com/api/versioning).

GitHub exposes both a REST API and a GraphQL API as Open Host Services. The
GraphQL API in particular treats its schema as the Published Language
artifact directly, offering live introspection and a downloadable canonical
schema file so that any of GitHub's very large and heterogeneous set of
integrators, from CI systems to IDEs to bots, can build against one
documented contract rather than negotiating individually with GitHub's
platform team (GitHub Docs, "Public schema," verified 2026-08-02,
https://docs.github.com/en/graphql/overview/public-schema).

HL7 FHIR (Fast Healthcare Interoperability Resources) is a named,
standards-body-owned example of the pattern operating across an entire
industry rather than a single company. It defines a documented, versioned
resource schema that lets electronic health record systems, laboratory
systems, and insurance systems integrate against one shared clinical data
language instead of each pair of systems negotiating a bespoke interface,
and it is explicitly cited as an Open Host Service example because it can
"serve several hosts at once" (arc42 Quality Model, "Open Host Service,"
verified 2026-08-02, https://quality.arc42.org/approaches/open-host-service).

## 10. Consequences

Positive consequences.

- Every consumer is decoupled from the producer's internal model, so the
  producing team can refactor behind the published contract as long
  as the contract itself is held stable, which is the same
  information-hiding benefit Parnas argued for at the module level, applied
  here at the bounded-context level.
- New consumers can be onboarded without a bespoke integration project,
  because the contract is documented and self-describing rather than
  something a producing-team engineer has to explain over a call.
- The producing team gets a single place, the Open Host Service, where
  every external-facing concern (authentication, rate limiting, versioning,
  backward compatibility) is enforced once, rather than scattered across N
  bespoke integrations.
- The published contract becomes a natural boundary for contract testing,
  which catches breaking changes before they reach any consumer.

Negative consequences.

- Holding a published language is an ongoing commitment. Every field, every
  event shape, and every deprecated-but-still-supported version is a
  promise the team must keep, and the cost of that promise compounds as the
  number of live versions grows.
- There is real translation overhead, both in code, where the Open Host
  Service layer must be written and maintained, and in design attention,
  because every internal model change must be evaluated for whether it
  should also change the published shape.
- The pattern can create a false sense of decoupling if the Open Host
  Service is built as a thin pass-through of internal types rather than a
  genuine translation layer. In that case the internal model is pinned in
  place exactly as it would be without the pattern, only now with extra
  ceremony on top.
- Publishing a language too early, before the internal model has
  stabilized, locks in design decisions that would otherwise have been
  cheap to change, which is why Vernon advises deliberately conservative,
  minimal published shapes rather than mirroring every internal concept
  (Vernon, "Implementing Domain-Driven Design," 2013, Chapter 3).

## 11. Failure modes and misuse

**Consumers break on unrelated refactors.** Symptom. Consumers file bugs
whenever the producing team ships an unrelated internal refactor, even
though the endpoint URL and version number did not change. Cause. The Open
Host Service is a thin pass-through that serializes internal domain objects
directly instead of translating to an independently defined published
shape, so any rename or restructuring inside the domain model leaks
straight through to the wire format. Fix. Introduce an explicit translation
step with its own data transfer types that are defined and versioned
independently of the internal model, so the two can change on different
schedules.

**Version bump in name only.** Symptom. A "v2" of the API exists in name
only, and every consumer who switches to it immediately breaks, because v2
removed fields v1 still promised. Cause. The team treats versioning as a
label rather than a compatibility contract, changing behavior within a
version instead of cutting a genuinely new one, or dropping fields without
a deprecation window. Fix. Adopt an explicit compatibility policy modeled
on the distinction Stripe makes between backward-compatible monthly
releases and named breaking major releases, and enforce it with contract
tests that fail the build if a currently supported version's shape changes
incompatibly (Stripe, "Versioning," verified 2026-08-02,
https://docs.stripe.com/api/versioning).

**The frozen internal model.** Symptom. The producing team is afraid to
change anything in the published schema, so the internal model has quietly
frozen in place even though the business has moved on, and every new
internal requirement is bent to fit the old published shape instead of
being modeled cleanly. Cause. There is no deprecation and sunset policy, so
every published version is treated as permanent, which removes the escape
hatch that makes controlled evolution possible in the first place. Fix.
Publish a stated support window for each version, a fixed number of months
or a fixed number of major versions back, and hold to it, so the producing
team always has a path to retire an old shape rather than carrying it
forever.

**Applying it to a pair that never needed it.** Symptom. Two teams that
already sit next to each other, ship together, and talk daily are
maintaining a full versioned API between themselves, with more process
overhead than either team's actual integration needs. Cause. OHS/PL was
applied to a tightly coupled pair relationship that never had a
plural-consumer problem, the exact non-applicability case in dimension 4.
Fix. Collapse the relationship to a Shared Kernel or a direct
Customer-Supplier integration and delete the versioning machinery. It is
solving a problem that does not exist here.

**Published in name, internal in fact.** Symptom. A consuming team builds
directly against the producer's internal naming and internal invariants
because "the published API is essentially the same as their database
anyway," and then breaks the moment the producer renames a column. Cause.
The producing team never actually built a translation boundary, so the
Published Language was published in name but was the internal model in
fact, collapsing back into the first failure mode above from the
consumer's side.

## 12. Trade-off matrix

| Force | Open Host Service / Published Language | Shared Kernel | Conformist | Anticorruption Layer alone |
|---|---|---|---|---|
| Coupling to producer's internals | Low, consumers depend on a translated contract | High, both teams share the same model | High, consumer adopts producer's model wholesale | Producer's model still leaks in, but consumer absorbs the cost, not the producer |
| Number of consumers it scales to | Many, cost amortizes across consumers | One tightly coordinated team, does not scale | One consumer per relationship, each pays conformance cost separately | Any number, but each pays its own translation cost independently |
| Producer's latitude to refactor internally | High, protected by the translation layer | Low, any change is a joint change | High, producer owes nothing to conformists | High, producer is unaware the pattern is being used |
| Consumer's translation burden | Low to moderate, contract is designed to be consumed | None, shared code | None, consumer adopts producer's concepts directly | High, entire translation cost sits on the consumer |
| Ongoing maintenance cost, producing side | Real and continuous, versioning and deprecation discipline | Shared with the partner team | Minimal, producer does not accommodate anyone | None, producer need not know it exists |
| Best fit | Plural, growing, organizationally distant consumers | One pair of closely collaborating teams | A consumer willing to be subordinate to an upstream authority | A single consumer protecting itself from a legacy or unstable upstream |

## 13. Related and incompatible patterns

Anticorruption Layer composes naturally with Open Host Service and
Published Language on the consuming side. The producer's OHS/PL gives every
consumer a stable, documented contract to build against, and each consumer
may still choose to run its own Anticorruption Layer to translate that
published contract into its own internal model, so the two patterns are
frequently deployed together at opposite ends of the same integration, one
protecting the producer's latitude to refactor and one protecting each
consumer's latitude to model independently (Evans, "Domain-Driven Design,"
2003, Part IV).

API Gateway is a common infrastructure vehicle for implementing an Open
Host Service in a microservice architecture, fronting one or more producing
services with a single documented entry point, though the two patterns are
not identical. An API Gateway is an infrastructure and routing concern,
while OHS/PL is a strategic design decision about who owns a shared
vocabulary and how it evolves. A gateway can host an OHS, but a gateway with
no coherent published schema behind it is not an instance of this pattern.

Event-Carried State Transfer is the natural implementation vehicle when the
Published Language is delivered as domain events rather than as a
request-response API, and dimension 7's second diagram is exactly this
combination. The events published onto the broker are the Published
Language, and the mechanism by which they carry enough state for consumers
to act without a callback is Event-Carried State Transfer.

Hexagonal Architecture (Ports and Adapters) is the object-level structural
pattern that the Open Host Service most often sits inside. The OHS is one of
the outbound adapters at the boundary of the bounded context, translating
between the port the internal domain model exposes and the published
external contract.

Facade is the object-level ancestor of the Open Host Service's translation
role. Where Facade simplifies access to a subsystem inside a single
process, OHS/PL applies the same idea across a bounded-context boundary
with the added discipline of explicit versioning.

Shared Kernel and Conformist are listed as incompatible in the frontmatter
in the specific sense described in dimension 12. They solve the same
general problem, two bounded contexts that need to relate, but they solve
it by choosing a different point on the coupling scale, and a team cannot
simultaneously run a Shared Kernel with a partner team and also maintain a
fully versioned, backward-compatible Published Language for that same
relationship without the two mechanisms fighting over which one governs the
shared vocabulary. Customer-Supplier is compatible in the sense that Vernon
and Evans both treat OHS/PL as one concrete way a supplier context can
serve a customer context, but a given relationship should be described as
one or the other, not layered as both at once for the same pair of teams.

## 14. Refactoring path in and out

To introduce the pattern into a set of bespoke, per-consumer integrations,
start by inventorying every existing consumer of the producing context and
the exact shape each one currently depends on, because these bespoke shapes
are the requirements the Published Language must satisfy on day one. Skip
this step and the first version of the new contract will immediately break
someone. Next, design the Published Language as its own artifact,
independent of the internal model, choosing the delivery mechanism from
dimension 8 that fits the actual usage pattern, synchronous queries versus
state-change notifications. Build the Open Host Service as an explicit
translation layer with its own types, never serializing internal domain
objects directly, and write contract tests against the published shape
before wiring any real consumer to it. Migrate consumers one at a time onto
the new contract, keeping the old bespoke integrations alive in parallel
until each consumer has verifiably cut over, then retire the bespoke paths.
Only after the first real, working version is in production should the
producing team commit publicly to a versioning and deprecation policy,
because a policy announced before there is anything to version is a
promise made in the abstract.

To remove the pattern once it stops earning its place, most often because
the plural-consumer condition has collapsed back to a single consumer or
because the organization has consolidated the producing and consuming teams
into one team, first confirm the consumer count genuinely is down to one
and is expected to stay there. A temporary dip during a reorg is not
sufficient reason to remove a contract other teams may still need. If the
condition holds, communicate a sunset date for the published version, give
the remaining consumer a migration path to a simpler direct integration or
a Shared Kernel, and only delete the Open Host Service's translation layer
after the last consumer has confirmed the cutover, mirroring the same
one-at-a-time discipline used to introduce it. Removing the layer before
consumers have migrated reintroduces exactly the tight coupling the pattern
existed to prevent, only now as an unplanned breaking change rather than a
managed one.

## 15. Testing and verification

Contract testing is the primary technique this pattern makes both possible
and necessary. Because the Published Language is an explicit, versioned
artifact rather than an implicit shape inferred from whatever the internal
model happens to look like today, it can be tested directly. A schema
validation suite asserts that every response the Open Host Service actually
produces conforms to the documented schema for that version, and this suite
can run in the producing team's own CI pipeline without any consumer's
participation. Consumer-driven contract testing, where each consumer team
publishes the subset of the schema it actually depends on and the producing
team's CI runs those consumer contracts before every deploy, is a stronger
technique that catches a break for a specific consumer even when the
overall schema validation still passes, because schema validation alone
cannot know that consumer B specifically depends on a field that is
technically optional in the schema.

What becomes easier to test because of this pattern is the internal domain
model in isolation, since it no longer has to be tested against every
consumer's expectations directly. The internal model's tests only need to
prove the domain logic is correct, and the Open Host Service's translation
tests separately prove the mapping from internal model to published shape
is correct, which is a cleaner separation of concerns than testing the
combined behavior end to end for every consumer.

What becomes harder is testing the full integration end to end across
organizational boundaries, because a genuine test across the full path now requires
either a live deployment of both the producing and consuming systems or a
carefully maintained set of fixtures that mirror the Published Language.
These fixtures themselves must be kept in sync with schema changes or the
test suite silently stops testing anything real, which is a known
maintenance burden with contract-testing setups generally rather than a
concern unique to OHS/PL (judgement, drawing on general contract-testing
practice).

## 16. Observability signals

A healthy Open Host Service shows a clear distribution of traffic across
API versions, with the newest supported version carrying the bulk of new
integrations and older versions showing a declining, bounded tail rather
than flat or growing usage, which is evidence that the deprecation policy
from dimension 14 is actually working. Schema validation failure rate
should sit at or near zero in steady state. Any nonzero rate of responses
failing their own declared schema shows that the translation layer
has drifted from the documented contract, which is a defect regardless of
whether any consumer has yet noticed. Per-version error rates and latency
percentiles, tracked separately per API version rather than aggregated,
reveal whether an older version is being kept alive at a real operational
cost, which is useful evidence when deciding whether a deprecation deadline
should hold firm.

For the event-carried variant, the metrics to track are event schema
version distribution among published events, consumer lag per subscriber,
meaning how far behind the head of the stream each consumer sits, and the
rate of schema-registry rejections, which occur when a producer attempts to
publish an event that does not conform to its declared schema and is the
asynchronous counterpart of the synchronous schema validation failure rate
above. A dashboard that shows these metrics per contract version, rather
than only in aggregate, is what lets an operations team tell the difference
between "the service is unhealthy" and "one deprecated version is unhealthy
and should be retired on schedule."

## 17. Security and privacy implications

Publishing a language widens the attack surface deliberately and by design,
because the entire point is to make a capability reachable by more
consumers than a bespoke, private integration would be. Every field added
to the Published Language is a field that must be evaluated for what
information it discloses to any consumer with access to the contract, not
only the consumer the field was originally added for. Field-level exposure
review matters more here than in an internal-only model, because a field
that is harmless inside a single bounded context, such as an internal risk
score or an internal customer tier, can leak sensitive business logic or
personal data once it is published where multiple, organizationally
separate teams can read it. Versioning itself has a privacy dimension. A
field marked deprecated but still present in a supported older version
continues to disclose whatever it discloses for as long as that version is
kept alive, so a deprecation decided for data-minimization reasons should
be enforced on the same timeline as any other supported-version sunset, not
left to linger simply because some consumer has not yet migrated.

Authentication and authorization sit at the Open Host Service boundary and
must be enforced there rather than assumed to be handled downstream,
because the OHS is, by design, the one place every external consumer
passes through. A scoping mistake at this single chokepoint, for example
granting a token access to a full resource when it should only see a
filtered view, exposes every consumer's data to every other consumer's
token rather than being contained to one bespoke integration. Where the
Published Language carries domain events rather than request-response
data, the same field-level review applies to event payloads, and access
control must additionally account for the fact that a broker-delivered
event, once published, has already been sent to every current subscriber
and cannot be recalled the way a request-scoped API response can be
withheld after the fact.

## Code examples

Three languages, each showing the same shape. an Open Host Service class
whose only job is translating an internal model into a versioned Published
Language shape, so the internal field never reaches the wire. All three were
run against the exact source shown.

### TypeScript

```typescript
interface InternalOrder {
  orderId: string;
  buyerEmail: string;
  totalCents: number;
  placedAt: Date;
  internalRiskScore: number;
}

interface OrderPublishedV1 {
  order_id: string;
  total_cents: number;
  placed_at: string;
}

class OpenHostService {
  toPublishedV1(order: InternalOrder): OrderPublishedV1 {
    return {
      order_id: order.orderId,
      total_cents: order.totalCents,
      placed_at: order.placedAt.toISOString(),
    };
  }
}

const internal: InternalOrder = {
  orderId: "ord_8842",
  buyerEmail: "buyer@example.com",
  totalCents: 4599,
  placedAt: new Date("2026-08-01T10:00:00Z"),
  internalRiskScore: 12,
};

const ohs = new OpenHostService();
const published = ohs.toPublishedV1(internal);
console.log(JSON.stringify(published));
if ("internalRiskScore" in (published as unknown as Record<string, unknown>)) {
  throw new Error("published shape leaked an internal field");
}
```

Compiled with `tsc --strict` and run with `node`, printing
`{"order_id":"ord_8842","total_cents":4599,"placed_at":"2026-08-01T10:00:00.000Z"}`
with no leaked field.

### Python

```python
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class InternalOrder:
    order_id: str
    buyer_email: str
    total_cents: int
    placed_at: datetime
    internal_risk_score: int


class OpenHostService:
    def to_published_v1(self, order: InternalOrder) -> dict:
        return {
            "order_id": order.order_id,
            "total_cents": order.total_cents,
            "placed_at": order.placed_at.isoformat(),
        }


if __name__ == "__main__":
    order = InternalOrder(
        order_id="ord_8842",
        buyer_email="buyer@example.com",
        total_cents=4599,
        placed_at=datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc),
        internal_risk_score=12,
    )
    ohs = OpenHostService()
    published = ohs.to_published_v1(order)
    print(published)
    assert "internal_risk_score" not in published, "published shape leaked an internal field"
```

Run with `python3`, printing
`{'order_id': 'ord_8842', 'total_cents': 4599, 'placed_at': '2026-08-01T10:00:00+00:00'}`
and the assertion passing silently.

### Go

```go
package main

import (
	"encoding/json"
	"fmt"
	"time"
)

type InternalOrder struct {
	OrderID           string
	BuyerEmail        string
	TotalCents        int
	PlacedAt          time.Time
	InternalRiskScore int
}

type OrderPublishedV1 struct {
	OrderID    string `json:"order_id"`
	TotalCents int    `json:"total_cents"`
	PlacedAt   string `json:"placed_at"`
}

type OpenHostService struct{}

func (OpenHostService) ToPublishedV1(o InternalOrder) OrderPublishedV1 {
	return OrderPublishedV1{
		OrderID:    o.OrderID,
		TotalCents: o.TotalCents,
		PlacedAt:   o.PlacedAt.UTC().Format(time.RFC3339),
	}
}

func main() {
	order := InternalOrder{
		OrderID:           "ord_8842",
		BuyerEmail:        "buyer@example.com",
		TotalCents:        4599,
		PlacedAt:          time.Date(2026, 8, 1, 10, 0, 0, 0, time.UTC),
		InternalRiskScore: 12,
	}
	ohs := OpenHostService{}
	published := ohs.ToPublishedV1(order)
	out, _ := json.Marshal(published)
	fmt.Println(string(out))
}
```

Run with `go run`, printing
`{"order_id":"ord_8842","total_cents":4599,"placed_at":"2026-08-01T10:00:00Z"}`.
Note the struct field ordering has no bearing on the JSON output, only the
`json` tags do, which is the mechanism Go idiomatically uses to enforce the
Open Host Service boundary at compile time rather than by convention.

Java, Rust, and Swift are omitted here not because the pattern fails to
translate, the translation-layer shape is identical in any statically typed
language, but because the three languages above already cover the object-oriented
class form, the dataclass form, and the struct-with-tags form that between
them represent every idiomatic variant this pattern takes at the code level.

## 18. References

1. Eric Evans, "Domain-Driven Design. Tackling Complexity in the Heart of
   Software," Addison-Wesley, 2003, Part IV (Strategic Design, the Open
   Host Service and Published Language sections and their companion
   patterns Shared Kernel, Customer-Supplier, Conformist, Anticorruption
   Layer, and Separate Ways).
2. Vaughn Vernon, "Implementing Domain-Driven Design," Addison-Wesley,
   2013, Chapter 3 (Context Maps), for the worked treatment of Open Host
   Service, Published Language, and domain events published across a
   bounded context boundary.
3. arc42 Quality Model, "Open Host Service," verified 2026-08-02,
   https://quality.arc42.org/approaches/open-host-service, for the
   working definition, the pairing with Published Language, and the HL7
   FHIR and iCalendar production examples.
4. Stripe, "Versioning" (API reference), verified 2026-08-02,
   https://docs.stripe.com/api/versioning, for the named production
   example of dated API versions, backward-compatible monthly releases,
   and named major releases such as "Acacia."
5. GitHub Docs, "Public schema" (GraphQL API overview), verified
   2026-08-02, https://docs.github.com/en/graphql/overview/public-schema,
   for the named production example of a canonical, introspectable,
   downloadable schema as the Published Language artifact.
