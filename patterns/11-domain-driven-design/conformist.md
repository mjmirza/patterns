---
name: Conformist
slug: conformist
family: 11-domain-driven-design
category: Strategic Design
aliases: [CF, Conformist Relationship]
first_described: "Evans 2003"
maturity: canonical
related: [bounded-context, context-map, anticorruption-layer, shared-kernel, customer-supplier, open-host-service, published-language]
incompatible_with: [customer-supplier]
verified: 2026-08-02
---

# Conformist

## 1. Name, aliases, and lineage

The canonical name is Conformist. It is one of the relationship patterns that
sit on a Domain-Driven Design context map, introduced by Eric Evans in
*Domain-Driven Design. Tackling Complexity in the Heart of Software*,
Addison-Wesley, 2003, Part IV, "Strategic Design", chapter 14, "Maintaining
Model Integrity". Evans defines it as the choice a downstream team makes to
eliminate the complexity of translating between two bounded contexts by
adopting the upstream team's model as its own, with no independent
translation layer between the two ([Context Mapper, "Conformist"](https://contextmapper.org/docs/conformist/),
verified 2026-08-02, which frames the pattern in the same terms while
documenting its DSL notation).

The tool-specific abbreviation is CF, used inside Context Mapper's Context
Mapping DSL (CML) to tag which side of an upstream and downstream pair has
conformed, for example `PolicyManagementContext [D,CF]<-[U,OHS,PL]
CustomerManagementContext` ([Context Mapper, "Conformist"](https://contextmapper.org/docs/conformist/),
verified 2026-08-02). There is no widely used alternate name for the pattern
beyond that abbreviation. Vaughn Vernon carries the same name and definition
into his own catalog of context map relationships, and Martin Fowler's bliki
entry on Bounded Context points to Vernon's *Implementing Domain-Driven
Design*, Addison-Wesley, 2013, chapter 3, as, in Fowler's words, "the best
source I know for drawing context maps" ([Martin Fowler, "BoundedContext"](https://martinfowler.com/bliki/BoundedContext.html),
verified 2026-08-02).

Conformist is a relationship between two Bounded Contexts, never a shape a
single module takes on its own. It only exists on a context map next to an
upstream and a downstream, and the DDD community's tooling enforces that
framing directly. Context Mapper's semantic validator rejects a context map
that tags a relationship as both Customer-Supplier and Conformist at once,
because the two describe mutually exclusive postures the downstream team can
take toward the same upstream ([Context Mapper, "Customer/Supplier"](https://contextmapper.org/docs/customer-supplier/),
verified 2026-08-02). That incompatibility is recorded in this entry's
frontmatter and expanded in dimension 13.

## 2. Problem and context

Two bounded contexts need to exchange data or invoke each other's behaviour,
and one of the two, the upstream, owns a model neither side is free to
renegotiate. The downstream team faces every integration in one of two
shapes. Spend real engineering time building a translation boundary that
keeps the upstream's vocabulary out of its own domain, or absorb the
upstream's model wholesale and let its own code speak in the upstream's
terms.

The context that makes Conformist the honest choice, rather than a lazy one,
has three ingredients working together.

- The upstream team has no reason to accommodate the downstream's needs.
  This is a genuinely one-directional power relationship, not a negotiation
  that has merely stalled.
- The upstream's model is close enough to what the downstream actually
  needs that a translation layer would spend effort rephrasing concepts
  rather than resolving a real semantic mismatch.
- The downstream team has a deadline, a budget, or a staffing level that
  makes a translation layer, and the ongoing maintenance of that layer, a
  cost it genuinely cannot carry right now.

The most common real instance of this shape is a small or mid-sized company
integrating a payment provider. A booking platform calling Stripe, or an
online marketplace calling PayPal, has no say over how Stripe or
PayPal name their concepts, and the provider's model, `Charge`, `PaymentIntent`,
`Refund`, `IdempotencyKey`, is close enough to what a payments-adjacent domain
needs that translating it into private vocabulary buys little. The
dotnetacademy.dev lesson on the Conformist pattern frames exactly this case,
naming Stripe by name and its `Charge`, `Source`, and `Refund` vocabulary
explicitly, see [dotnetacademy.dev, "The Conformist Pattern"](https://www.dotnetacademy.dev/lesson/conformist/17),
verified 2026-08-02. A second common instance is a downstream integrating
against a platform vendor's own generated client, a Kubernetes controller
built on `client-go`, or a Terraform provider built against a cloud vendor's
resource schema, discussed with named sources in dimension 9.

Outside that three-part context, Conformist is not a pattern choice at all.
It is what happens by default when nobody makes the choice on purpose, and
that default is one of the two failure modes covered in dimension 11.

## 3. Forces

This dimension weighs judgement, not sourced fact. The forces below are the
author's read of the trade-offs, following the practice recorded across the
sources cited in dimensions 1, 2, and 9.

- **Development speed.** Strongly favoured. There is no translator to design,
  no mapping code to write, no anti-corruption boundary to test. A team can
  wire up an integration in the time it takes to read the upstream's API
  reference.
- **Coupling.** Strongly sacrificed. The downstream's domain code imports the
  upstream's types and calls the upstream's functions directly. A breaking
  change in the upstream's model is a breaking change in the downstream's
  own domain logic, with no seam to absorb it.
- **Model purity.** Sacrificed, sometimes severely. If the upstream's model
  is awkward, inconsistent, or organised around concerns the downstream does
  not share, that awkwardness now lives inside the downstream's own
  ubiquitous language. The ddd-crew context mapping catalog and the Context
  Mapper documentation both describe this as the upstream's mess
  propagating downstream when the upstream is not well designed, stating
  the downstream must fully adapt to the upstream's design and that a
  poorly designed upstream propagates its problems downstream ([ddd-crew/context-mapping](https://github.com/ddd-crew/context-mapping),
  verified 2026-08-02).
- **Team autonomy.** Sacrificed. The downstream team's roadmap is now
  partially dictated by the upstream's release cadence, deprecation policy,
  and design decisions the downstream had no vote in.
- **Cost of change.** Favoured on day one, sacrificed over the system's
  life. The absence of a translation layer means every future accommodation
  of the upstream's evolution happens inside the downstream's core domain
  code, rather than confined to a small, well-tested boundary.
- **Operability.** Neutral to mildly favoured. There is one fewer moving
  part, one fewer service or module to deploy, monitor, and keep in sync
  with two schema versions at once.
- **Testability.** Sacrificed. Tests of the downstream's domain logic now
  need fixtures shaped like the upstream's objects, and a change to those
  fixtures ripples through every test that touches them, because there is
  no seam at which to substitute a smaller, downstream-owned test double.

The pattern is honest about what it gives up. It trades long-term
flexibility and domain clarity for short-term velocity and a lower initial
cost, and it is only the right trade when the downstream team has genuinely
weighed that exchange rather than drifted into it by accident.

## 4. Applicability and non-applicability

Reach for Conformist when the following hold together.

- The upstream team will not, or cannot, adapt its model for the downstream,
  and that reality is not going to change through negotiation.
- The upstream's model is close enough to the downstream's actual needs
  that a translation layer would mostly restate the same concepts under
  different names.
- The downstream's integration with the upstream is small in surface area,
  touching a handful of operations rather than the downstream's entire
  domain.
- The team has a genuine resource constraint, a deadline, a small team, an
  early-stage product, that makes building and maintaining a translation
  boundary a real cost it cannot absorb right now.
- The upstream is a stable, well-governed system, a major cloud provider, a
  well-maintained open-source project, a payment processor with a
  contractual SLA, so the risk of the upstream's model shifting unexpectedly
  underneath the downstream is low.

Do NOT reach for Conformist in any of these situations, each with the reason
attached.

- **The upstream is a Core Domain concern for the downstream.** If the
  integration point touches the part of the system that differentiates the
  business, importing a third party's vocabulary into that Core Domain
  contaminates the one part of the model the company cannot afford to get
  wrong. Core Domain patterns rarely tolerate a Conformist relationship for
  exactly this reason.
- **The upstream's model is actively poor quality.** A model with
  inconsistent naming, leaky implementation details, or design decisions
  the downstream does not agree with should not be imported wholesale.
  Anticorruption Layer exists precisely to keep that mess out.
- **The integration touches a large surface area of the downstream's
  domain.** The wider the upstream's vocabulary spreads through the
  downstream's own code, the more expensive it becomes to later retrofit a
  translation boundary, because that retrofit now has to touch everywhere
  the upstream's types leaked into.
- **The relationship is genuinely Customer-Supplier.** If the downstream
  does have influence over the upstream's roadmap, whether through a
  contract, a shared reporting line, or a real collaborative planning
  process, naming the relationship Conformist misrepresents the actual
  power dynamic. Context Mapper's own validator treats the two as
  incompatible tags on the same edge ([Context Mapper, "Customer/Supplier"](https://contextmapper.org/docs/customer-supplier/),
  verified 2026-08-02).
- **The downstream expects the upstream to change frequently or
  unpredictably.** A volatile upstream turns every one of its releases into
  an unplanned change to the downstream's own domain code, because there is
  no boundary absorbing the difference.
- **Regulatory, compliance, or audit requirements demand a stable internal
  vocabulary independent of any vendor.** Some domains, healthcare records,
  financial reporting, need their own model to remain defined by the
  organisation's own governance process rather than by a vendor's schema
  evolution.

## 5. Structure

Conformist names a relationship on a context map, not a set of runtime
classes with fixed responsibilities, so its participants are teams and
contexts rather than objects.

- **Upstream Bounded Context.** The context whose model the relationship
  adopts. It publishes an interface, a client library, or an API, and it
  makes no promise to adapt that publication to any one downstream's needs.
- **Upstream Team.** The people who own the upstream context. In the
  external-vendor case, Stripe or a cloud provider, this team is entirely
  outside the downstream organisation and unreachable for negotiation. In
  the internal case, a platform team inside the same company, the upstream
  team may simply be too large, too senior, or too busy to prioritise the
  downstream's requests.
- **Downstream Bounded Context.** The context that consumes the upstream's
  model. In a Conformist relationship this context's own domain code
  directly reuses the upstream's types, function signatures, and
  vocabulary, rather than defining its own equivalents.
- **Downstream Team.** The people who own the downstream context and who
  make the deliberate choice to conform rather than translate. Making that
  choice explicit, on the context map, is the entire discipline the pattern
  asks for. The alternative, drifting into the same coupling without ever
  naming it, is the failure mode covered in dimension 11.
- **The absent participant.** Unlike Anticorruption Layer, there is no
  translation component in this structure. Its absence is the defining
  feature of the pattern, not an implementation detail left out of the
  diagram.

## 6. ASCII structure diagram

```text
                     no negotiating power
    +----------------------------------------------+
    |                                                v
+---+---------------------+                +----------------------+
|  Upstream Bounded        |                |  Downstream Bounded   |
|  Context (e.g. Stripe)   |                |  Context (Booking)    |
|                          |                |                       |
|  Charge                  |------------->  |  uses Charge directly |
|  Refund                  |   published    |  uses Refund directly |
|  PaymentIntent           |   API/SDK      |  no BookingPayment    |
|  IdempotencyKey          |                |  type exists          |
+--------------------------+                +-----------------------+
                                                        |
                                                        v
                                             Downstream's own domain
                                             logic now speaks in the
                                             upstream's vocabulary,
                                             wired directly, with no
                                             translation boundary in
                                             between the two.

  Compare with an Anticorruption Layer relationship.

+--------------------------+      +-----------+      +-----------------------+
|  Upstream Bounded         |----->|  ACL      |----->|  Downstream Bounded    |
|  Context                  |      |(translate)|      |  Context, own model    |
+--------------------------+      +-----------+      +-----------------------+
```

## 7. Dynamics

At runtime, a Conformist relationship has almost no dynamics of its own
beyond an ordinary function call or API request, because the whole point of
the pattern is that nothing sits between the two contexts to intercept,
transform, or reinterpret the exchange.

```text
Downstream domain logic          Upstream client/SDK          Upstream service
        |                                |                            |
        |  1. build request using        |                            |
        |     the upstream's own type    |                            |
        |     (e.g. new Charge params)   |                            |
        |------------------------------->|                            |
        |                                |  2. serialise + call       |
        |                                |     upstream API           |
        |                                |--------------------------->|
        |                                |                            |
        |                                |  3. upstream response,     |
        |                                |     upstream's own shape   |
        |                                |<---------------------------|
        |  4. upstream's response type   |                            |
        |     returned as-is, stored     |                            |
        |     and reasoned about inside  |                            |
        |     the downstream's own       |                            |
        |     domain logic               |                            |
        |<-------------------------------|                            |
        |                                |                            |
        |  5. a schema or behaviour      |                            |
        |     change on the upstream     |                            |
        |     side reaches the           |                            |
        |     downstream's domain logic  |                            |
        |     directly at step 4, with   |                            |
        |     no intervening layer to    |                            |
        |     absorb it                  |                            |
```

Step 5 is the dynamic that distinguishes Conformist from every other
integration pattern on the context map. In Anticorruption Layer, an upstream
change is absorbed by the translator and, ideally, never reaches the
downstream's domain logic at all. In Conformist, that same change reaches
the downstream's core code at the exact same moment it reaches every other
caller of the upstream, because the downstream's domain logic is, in this
one respect, a direct extension of the upstream's own model.

## 8. Implementation variants

- **Direct SDK reuse.** The downstream imports the upstream's official
  client library and uses its types as first-class citizens inside the
  downstream's own domain and application layers. This is the shape shown
  in dimension 6 and in the code examples below, and it is the variant the
  dotnetacademy.dev lesson describes for a booking system calling Stripe
  directly ([dotnetacademy.dev, "The Conformist Pattern"](https://www.dotnetacademy.dev/lesson/conformist/17),
  verified 2026-08-02).
- **Generated client conformity.** Rather than a hand-maintained SDK, the
  downstream consumes a code generator's output, an OpenAPI-generated
  client, a gRPC-generated stub, or a Kubernetes-style typed client
  generated straight from the upstream's schema. Kubernetes's `client-go`
  is a canonical named example, discussed with a source in dimension 9. The
  generated types are, by construction, an exact mirror of the upstream's
  model, so a team choosing this variant is choosing Conformist even if
  nobody on the team uses that word for it.
- **Raw protocol conformity, no client library.** The downstream parses the
  upstream's wire format, JSON, protobuf, or a webhook payload, directly
  into structures that keep the upstream's field names and shapes,
  bypassing any official SDK. This variant carries slightly more
  translation risk than the SDK variant, because the downstream team is now
  responsible for keeping its hand-rolled parsing in step with the
  upstream's schema, but it is still Conformist as long as the resulting
  structures are used unmodified in the downstream's own domain logic.
- **Partial conformity at the boundary, isolated inside a module.** Some
  teams conform only at the specific integration point, importing the
  upstream's types into one module of the downstream system, while keeping
  the rest of the downstream's domain free of upstream vocabulary. This is
  a defensible middle ground in practice, though strictly it is Conformist
  only for that one module, and the module boundary itself starts to act
  like a lightweight, undocumented Anticorruption Layer the moment other
  parts of the downstream stop reaching directly into the upstream's types.
- **Configuration-schema conformity.** Infrastructure-as-code tooling
  regularly conforms at the level of a declared schema rather than runtime
  objects. A Terraform provider's resource schema is written to mirror the
  upstream cloud API's own resource model field for field, which is the
  same relationship expressed in configuration rather than in a running
  process, discussed with a source in dimension 9.

Language does not change the shape of this pattern the way it changes a
class-based Gang of Four pattern, because Conformist is a decision about
where a translation boundary does or does not exist, not a decision about
which language construct implements a role. A statically typed language
like TypeScript or Go makes the conformity visible at compile time, since
the downstream's function signatures literally reference the upstream's
types. A dynamically typed language achieves the identical relationship
with no compiler enforcing it, which makes the coupling just as real but
harder to see in a code review.

## 9. Known production uses

- **Payment gateway integrations, Stripe and PayPal named explicitly.**
  Multiple independent sources describe the common real-world pattern of an
  e-commerce or booking platform integrating a payment provider as a
  textbook Conformist relationship, because the provider has no motivation
  to adapt its API for any one merchant and the provider's domain
  vocabulary, `Charge`, `Refund`, `PaymentIntent`, is close enough to what a
  payments-adjacent system needs on its own ([dotnetacademy.dev, "The
  Conformist Pattern"](https://www.dotnetacademy.dev/lesson/conformist/17),
  verified 2026-08-02, which walks through a booking system using Stripe's
  `Charge`, `Source`, and `Refund` vocabulary directly inside its own
  booking logic). This is a widely reported integration shape rather than a
  single named company's published case study, and this entry states that
  distinction plainly rather than overstating it as one company's audited
  disclosure.
- **Kubernetes `client-go` typed clients.** The Kubernetes project ships
  `client-go`, the Go client library used by the vast majority of
  Kubernetes controllers and operators in the ecosystem. Its typed clients
  expose Go structs that are pre-generated, one-to-one representations of
  the Kubernetes API's own object schema for every resource kind, Pod,
  Deployment, Service, and so on, with no intervening translation layer
  between the wire-level API object and the struct a controller author
  writes code against ([kubernetes/client-go on GitHub](https://github.com/kubernetes/client-go),
  verified 2026-08-02, describing `kubernetes.Clientset` as providing
  pre-generated local API objects for every core resource type). A
  controller author writing reconciliation logic against these types is, by
  construction, conforming to the Kubernetes API's own domain model rather
  than defining an independent one, which is exactly the trade-off named in
  dimension 3. Very fast to build against, and every future Kubernetes API
  version bump is a direct concern for the controller's own code.
- **Terraform providers mirroring upstream cloud API schemas.** HashiCorp's
  own documentation for writing Terraform provider schemas states that a
  provider is an abstraction of an upstream API, and walks through defining
  a provider's resource schema so that its required, optional, and
  computed fields mirror the upstream API's own resource fields directly
  ([HashiCorp Developer, "Schemas" for the Terraform Plugin Framework](https://developer.hashicorp.com/terraform/plugin/framework/handling-data/schemas),
  verified 2026-08-02). A provider author is not free to invent a
  Terraform-native vocabulary for a cloud resource, the schema has to
  track the upstream API's field names, types, and required, optional, and
  computed status closely enough that Terraform's state model stays
  consistent with the real infrastructure, which is a configuration-schema
  instance of the same Conformist relationship described in dimension 8.

## 10. Consequences

Positive consequences.

- The downstream team ships an integration in a fraction of the time a
  translated integration would take, because there is no mapping code to
  design, write, or keep synchronised with two schemas.
- The downstream's tests can assert directly against the upstream's own
  documented behaviour, since there is no second, downstream-invented model
  whose fidelity to the upstream also needs verifying.
- Debugging an integration issue is simpler in one specific respect. There
  is exactly one model in play, so a value seen in the downstream's logs is
  the exact value the upstream produced, with no translation step that
  could have introduced a discrepancy.
- Onboarding a new engineer onto the downstream team is faster for this
  integration point specifically, because reading the upstream's own public
  documentation is sufficient, there is no private translation vocabulary
  to learn on top of it.

Negative consequences.

- The upstream's vocabulary, and the upstream's design mistakes, leak
  directly into the downstream's own domain model. If the upstream renames
  a field, deprecates an operation, or changes a status enum's meaning,
  that change is now a change request against the downstream's core
  business logic.
- The downstream loses the ability to express its own domain concepts in
  its own terms at this integration point. A booking platform's code ends
  up reasoning about a `Charge` and an `IdempotencyKey` rather than about
  a `Payment`, because the upstream owns those nouns now.
- Reversing the decision later is expensive in direct proportion to how far
  the upstream's types spread through the downstream's codebase. A
  Conformist relationship adopted for speed in a small module can, months
  later, require touching every file that references the upstream's types
  in order to retrofit an Anticorruption Layer.
- Multiple upstream integrations, each conformed to independently, tend to
  produce a downstream domain model with no single coherent vocabulary,
  since each integration point speaks in its own upstream's terms rather
  than a vocabulary the downstream team designed on purpose.

## 11. Failure modes and misuse

- **Symptom.** A production incident traces back to an upstream vendor
  renaming or reshaping a field, and the fix touches business logic several
  layers away from anything that looks like an integration point.
  **Cause.** The upstream's types were never confined to a boundary module,
  they were passed straight through into services, into persistence models,
  and sometimes into the downstream's own public API. **Fix.** Even inside
  a deliberate Conformist relationship, confine the upstream's types to the
  smallest set of modules that genuinely need them, and treat any spread
  beyond that boundary as a signal the relationship should be revisited.
- **Symptom.** The team cannot explain, when asked directly, whether a
  given integration is Conformist, Customer-Supplier, or something in
  between, and different engineers give different answers. **Cause.** The
  relationship was never chosen consciously, the team simply imported the
  upstream's SDK because it was the path of least resistance, and the
  decision was never written down on a context map or discussed as a
  trade-off. **Fix.** Draw the context map explicitly and name the
  relationship. Naming it does not change the code, but it turns an
  invisible default into a decision the team can revisit deliberately, and
  it is precisely the discipline dimension 2 and dimension 3 describe.
- **Symptom.** A downstream team repeatedly builds one-off adapter
  functions scattered across the codebase, each translating a small slice
  of the upstream's model in a slightly different, inconsistent way.
  **Cause.** The team wanted the benefits of an Anticorruption Layer, a
  stable internal vocabulary, without paying for the discipline of
  building one central translation boundary, so partial, inconsistent
  translation accreted piecemeal instead. **Fix.** Pick one of the two
  patterns on purpose. Either commit fully to Conformist and accept
  upstream vocabulary throughout the integration's surface, or commit to a
  single, central Anticorruption Layer and route every use of the upstream
  through it.
- **Symptom.** The downstream team files change requests against the
  upstream vendor and is surprised, repeatedly, that the requests go
  nowhere. **Cause.** The team believed, or hoped, it was in a
  Customer-Supplier relationship, negotiating as an equal, when the actual
  power dynamic was Conformist all along, the upstream never had a
  reason to prioritise the downstream's requests. **Fix.** Name the
  relationship honestly on the context map as Conformist, per Context
  Mapper's own rule that the two tags cannot coexist on one edge
  ([Context Mapper, "Customer/Supplier"](https://contextmapper.org/docs/customer-supplier/),
  verified 2026-08-02), and stop budgeting engineering time toward
  upstream negotiation that has no real chance of succeeding.
- **Symptom.** A migration off the upstream vendor, or a major upgrade to a
  new version of its API, becomes a project measured in months rather than
  weeks, touching dozens of files with no clear list of what needs to
  change. **Cause.** Years of Conformist integration with no boundary means
  the upstream's vocabulary is now woven through the downstream's own
  domain code with no single seam to cut along. **Fix.** Treat a planned
  vendor migration as the trigger to introduce an Anticorruption Layer
  first, isolating the old vendor's model behind a translation boundary,
  and only then swap the implementation behind that boundary for the new
  vendor.

## 12. Trade-off matrix

Comparison is against the other named relationship patterns on a Domain-
Driven Design context map, per the hard rule that a trade-off table compares
against real alternatives rather than a strawman.

| Force | Conformist | Anticorruption Layer | Customer-Supplier | Shared Kernel | Separate Ways |
|---|---|---|---|---|---|
| Upfront engineering cost | Lowest, no translation code to write | Higher, a translator plus its tests | Higher, requires ongoing coordination overhead | Moderate, requires joint governance of the shared code | Lowest of all, no integration exists |
| Insulation from upstream change | None, changes reach domain logic directly | High, translator absorbs most changes | Moderate, changes are negotiated ahead of time | Low, both sides feel a shared-code change immediately | Total, there is nothing to be insulated from |
| Downstream model purity | Sacrificed, upstream's vocabulary is adopted wholesale | Preserved, downstream keeps its own vocabulary | Preserved, downstream defines its own model | Partially shared by design, not fully independent | Fully preserved, no shared model at all |
| Requires upstream cooperation | No, that is the defining condition | No, translation is entirely downstream's work | Yes, upstream must prioritise downstream's needs | Yes, both teams must coordinate every shared change | No, the two contexts do not integrate |
| Best fit | A dominant or external upstream with no reason to accommodate the downstream, and a model close enough to be usable as-is | A dominant or external upstream whose model is poor quality or actively harmful to import | Two internal teams with a real, ongoing collaborative relationship | Two teams willing to accept tight coupling for a small, stable, jointly owned piece of the model | Two contexts whose overlap is small enough that duplicating a little logic beats integrating at all |

## 13. Related and incompatible patterns

- **Bounded Context.** Conformist only makes sense as a relationship between
  two Bounded Contexts, the pattern presupposes that both a downstream and
  an upstream context already exist with their own boundaries.
- **Context Map.** Conformist is one of the relationship types a team
  records on its context map, alongside Customer-Supplier, Shared Kernel,
  Open Host Service, Published Language, Partnership, and Separate Ways.
  Drawing the map, and labelling an edge Conformist honestly, is the
  practice this entry's dimension 11 treats as the primary defence against
  drifting into unconscious coupling.
- **Anticorruption Layer.** The direct alternative for the same situation,
  a dominant upstream with no reason to accommodate a downstream, chosen
  when the upstream's model is poor quality or when the downstream cannot
  afford to let that vocabulary spread through its own domain. Context
  Mapper's documentation frames Open Host Service clients as choosing
  between these two responses, becoming Conformists or building
  Anticorruption Layers, which places the two patterns as siblings
  answering the same question with opposite trade-offs ([Context Mapper,
  "Conformist"](https://contextmapper.org/docs/conformist/), verified
  2026-08-02).
- **Open Host Service and Published Language.** These two often appear on
  the upstream side of a Conformist relationship. An upstream that
  publishes a well-documented, stable protocol as an Open Host Service,
  described in a Published Language, gives every downstream, including a
  conforming one, a much safer target to conform to than an undocumented,
  ad hoc API.
- **Customer-Supplier, incompatible.** Conformist and Customer-Supplier
  describe mutually exclusive postures toward the same upstream. Customer-
  Supplier means the downstream's needs factor into the upstream's
  planning, Conformist means they explicitly do not. Context Mapper's own
  semantic validator enforces this as a hard rule, rejecting a context map
  edge tagged with both at once ([Context Mapper, "Customer/Supplier"](https://contextmapper.org/docs/customer-supplier/),
  verified 2026-08-02).
- **Core Domain.** A Conformist relationship rarely belongs anywhere near a
  Core Domain, because letting a vendor's vocabulary define the part of the
  system that differentiates the business trades away the one thing a Core
  Domain exists to protect. See `patterns/11-domain-driven-design/core-domain.md` in this
  repository for the fuller argument.

## 14. Refactoring path in and out

Introducing Conformist deliberately, when a team is currently doing ad hoc,
inconsistent translation and decides to stop.

1. Confirm the three-part context from dimension 2 genuinely holds. The
   upstream will not adapt, its model is close enough to usable, and the
   team has a real resource constraint that makes a translation layer the
   wrong spend right now.
2. Remove the scattered, partial adapter functions and replace every call
   site with the upstream's own types used directly, so the codebase has
   one consistent posture toward the upstream rather than a mix.
3. Record the relationship on the team's context map, tagged Conformist,
   with the reasoning from step 1 written down next to it, so the decision
   is visible to the next engineer who touches this integration.
4. Confine the upstream's types to the smallest reasonable module boundary
   consistent with dimension 11's first failure mode, even though a strict
   reading of Conformist does not require this. A soft boundary at the
   module level costs almost nothing and materially reduces the cost of
   later reversing the decision.

Removing Conformist, when the trade-off has stopped paying off, most often
because the integration has grown, the upstream has become unstable, or a
vendor migration is now planned.

1. Introduce an Anticorruption Layer as a new boundary, initially a thin
   pass-through that still uses the upstream's types internally but exposes
   a downstream-owned interface to the rest of the system.
2. Migrate call sites one at a time from the upstream's types to the new
   interface, verifying behaviour is unchanged at each step, which is the
   same incremental discipline as the Strangler Fig pattern applied at the
   scope of a single integration rather than a whole system.
3. Once every call site goes through the new interface, move the actual
   translation logic, mapping the upstream's fields to the downstream's own
   vocabulary, inside the boundary, and delete any remaining direct
   references to the upstream's types outside it.
4. Update the context map to reflect the new relationship, and record why
   the team moved away from Conformist so the reasoning survives staff
   turnover.

## 15. Testing and verification

Testing code inside a Conformist relationship is largely testing against
the upstream's documented behaviour directly, since there is no
downstream-owned abstraction to substitute a smaller test double for.

- **Contract tests against the upstream's real API, where feasible.** Since
  the downstream's domain logic is coupled directly to the upstream's
  shape, a contract test that periodically calls the real upstream, or a
  faithful sandbox environment the upstream provides, catches a breaking
  upstream change before it reaches production rather than after.
- **Recorded-response fixtures for unit tests.** Capture a real response
  from the upstream once, store it as a fixture, and replay it in unit
  tests rather than hand-writing a fixture from memory of the upstream's
  schema. A hand-written fixture drifts from reality quietly, a recorded
  one only goes stale visibly, when a contract test flags a mismatch.
- **What becomes easier.** Tests that exercise the downstream's own
  business rules can assert directly against the upstream's real field
  names and types, with no risk that a translation layer's own bug is
  masking or introducing a discrepancy.
- **What becomes harder.** Testing the downstream's domain logic in
  isolation from the upstream becomes harder, because the upstream's types
  are woven directly into that logic. A test double now has to fully
  impersonate the upstream's shape rather than a smaller, purpose-built
  downstream interface, which tends to make test setup more verbose over
  time as the upstream's model grows.
- **Regression coverage for the boundary.** Even without a formal
  Anticorruption Layer, it is worth pinning the specific fields and
  behaviours the downstream actually depends on with a small, explicit
  regression test, so a future upstream release that removes an
  undocumented behaviour the downstream happened to rely on is caught by a
  test rather than by a production incident.

## 16. Observability signals

- **Upstream schema version or API version in every log line that touches
  the integration**, so an incident review can immediately tell whether a
  failure correlates with an upstream release rather than a downstream
  deploy.
- **A dashboard counting deserialisation or validation failures against the
  upstream's response shape**, since in a Conformist relationship these
  failures are the earliest, cheapest signal that the upstream's model has
  shifted underneath the downstream.
- **A healthy instance** shows a steady, low, near-zero rate of
  upstream-shape validation failures, and error rates on calls to the
  upstream that track the upstream's own published status page rather than
  diverging from it.
- **A failing instance** shows a sudden spike in deserialisation errors, or
  in downstream business-logic exceptions whose stack traces bottom out
  inside code that directly constructs or reads the upstream's types,
  immediately following an upstream release or a vendor-announced schema
  change.
- **Alert on new, previously unseen field values from the upstream**,
  particularly enum-like fields such as a status or a type code, since a
  Conformist relationship has no translation layer to normalise a new
  value the upstream introduces, and that new value will reach the
  downstream's own business logic unmodified.

## 17. Security and privacy implications

A Conformist relationship widens the downstream's trust boundary to include
the upstream's data shape directly, which has two concrete implications.

- **Input validation moves, or fails to move, with the model.** Because
  there is no translation boundary, any input validation the downstream
  needs has to be applied explicitly at the point where the upstream's
  response is consumed. A team that assumed a translation layer would have
  handled sanitisation, and then adopted Conformist without replacing that
  assumption with an explicit validation step, leaves the downstream's
  domain logic processing an external vendor's raw output with no
  intervening check.
- **Sensitive fields the upstream returns become sensitive fields the
  downstream's own domain model carries.** If the upstream's model
  includes personally identifiable information or payment details in
  fields the downstream does not strictly need, importing that model
  wholesale, rather than through a translation layer that could
  deliberately drop unneeded sensitive fields, means the downstream now
  stores, logs, and potentially exposes data it never needed to touch.
  This is a genuine, concrete cost of the pattern's characteristic absence
  of a boundary, distinct from a general observation about third-party
  integrations, and it is worth an explicit review of exactly which fields
  the upstream's types carry before a team commits to conforming.

This entry does not identify a specific vulnerability class unique to the
pattern beyond the two implications above. The pattern's security profile
is otherwise a direct consequence of the coupling already described in
dimensions 3 and 10, not a separate concern.

## 18. References

1. Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
   Software*, Addison-Wesley, 2003, Part IV, "Strategic Design", chapter 14,
   "Maintaining Model Integrity", the CONFORMIST section.
2. Vaughn Vernon, *Implementing Domain-Driven Design*, Addison-Wesley, 2013,
   chapter 3, "Context Maps", cited as the standard reference for drawing
   context maps and their relationship patterns.
3. [Context Mapper, "Conformist"](https://contextmapper.org/docs/conformist/),
   verified 2026-08-02.
4. [Context Mapper, "Customer/Supplier"](https://contextmapper.org/docs/customer-supplier/),
   verified 2026-08-02.
5. [Martin Fowler, "BoundedContext"](https://martinfowler.com/bliki/BoundedContext.html),
   verified 2026-08-02.
6. [ddd-crew/context-mapping on GitHub](https://github.com/ddd-crew/context-mapping),
   verified 2026-08-02.
7. [ddd-practitioners.com, "Conformist"](https://ddd-practitioners.com/home/glossary/bounded-context/bounded-context-relationship/conformist/),
   verified 2026-08-02.
8. [dotnetacademy.dev, "The Conformist Pattern"](https://www.dotnetacademy.dev/lesson/conformist/17),
   verified 2026-08-02.
9. [kubernetes/client-go on GitHub](https://github.com/kubernetes/client-go),
   verified 2026-08-02.
10. [HashiCorp Developer, "Schemas" (Terraform Plugin Framework)](https://developer.hashicorp.com/terraform/plugin/framework/handling-data/schemas),
    verified 2026-08-02.
11. [Microsoft Learn, "Anti-Corruption Layer pattern"](https://learn.microsoft.com/en-us/azure/architecture/patterns/anti-corruption-layer),
    verified 2026-08-02, cited for the Anticorruption Layer comparison in
    dimensions 12 and 13, and for its own attribution of the pattern to
    Eric Evans.
12. `patterns/11-domain-driven-design/context-map.md`, `patterns/11-domain-driven-design/bounded-context.md`,
    and `patterns/11-domain-driven-design/core-domain.md`, this repository, for the internal
    cross-references in dimensions 13 and 4.

## Code examples

Three languages, chosen because each shows the same relationship, a
downstream module reusing an upstream's own types and vocabulary directly
inside its own domain logic, in a different idiomatic form. TypeScript's
structural typing makes the shared shape visible without inheritance,
Python's dataclasses show the same reuse in a dynamically typed language,
and Go shows the pattern in a language whose ecosystem, `client-go` from
dimension 9, is itself a named production instance of it.

All three samples below were compiled or run directly, `tsc --strict`,
`python3`, and `go run`, each exiting cleanly with the printed output shown
in a trailing comment.

```typescript
// Upstream module: a legacy billing system's own vocabulary, owned by another team.
namespace LegacyBilling {
  export interface Invoice {
    invoiceRef: string;
    grossAmountCents: number;
    taxCode: "STANDARD" | "REDUCED" | "EXEMPT";
    dueEpochSeconds: number;
  }

  export function raiseInvoice(
    grossAmountCents: number,
    taxCode: Invoice["taxCode"]
  ): Invoice {
    return {
      invoiceRef: `INV-${Math.floor(Math.random() * 100000)}`,
      grossAmountCents,
      taxCode,
      dueEpochSeconds: Math.floor(Date.now() / 1000) + 30 * 86400,
    };
  }
}

// Downstream module: the order service conforms. It imports the upstream
// type directly and speaks the upstream's vocabulary in its own domain code.
// There is no OrderInvoice type, no translation function, no adapter.
class OrderService {
  private issued: LegacyBilling.Invoice[] = [];

  placeOrder(totalCents: number): LegacyBilling.Invoice {
    const taxCode: LegacyBilling.Invoice["taxCode"] =
      totalCents > 0 ? "STANDARD" : "EXEMPT";
    const invoice = LegacyBilling.raiseInvoice(totalCents, taxCode);
    this.issued.push(invoice);
    return invoice;
  }

  outstandingBalanceCents(): number {
    return this.issued.reduce((sum, inv) => sum + inv.grossAmountCents, 0);
  }
}

const orders = new OrderService();
const inv = orders.placeOrder(4599);
console.log(`${inv.invoiceRef} tax=${inv.taxCode} balance=${orders.outstandingBalanceCents()}`);
// Compiled with tsc --strict --target es2020, ran with node, printed
// INV-25039 tax=STANDARD balance=4599
```

```python
"""Upstream module. A third-party payment SDK's own vocabulary, Stripe shaped."""
import random
import time
from dataclasses import dataclass, field


@dataclass
class Charge:
    charge_id: str
    amount_cents: int
    currency: str
    idempotency_key: str
    created: float = field(default_factory=time.time)


def create_charge(amount_cents: int, currency: str, idempotency_key: str) -> Charge:
    return Charge(
        charge_id=f"ch_{random.randint(100000, 999999)}",
        amount_cents=amount_cents,
        currency=currency,
        idempotency_key=idempotency_key,
    )


# Downstream module: the booking service conforms. It uses the upstream's
# Charge type and vocabulary directly inside its own booking domain logic,
# with no BookingPayment type and no translation layer.
class BookingService:
    def __init__(self) -> None:
        self._charges: list[Charge] = []

    def confirm_booking(self, price_cents: int, booking_ref: str) -> Charge:
        charge = create_charge(price_cents, "eur", idempotency_key=booking_ref)
        self._charges.append(charge)
        return charge

    def total_charged_cents(self) -> int:
        return sum(c.amount_cents for c in self._charges)


if __name__ == "__main__":
    booking = BookingService()
    charge = booking.confirm_booking(12900, "BK-4471")
    print(
        f"{charge.charge_id} currency={charge.currency} "
        f"total={booking.total_charged_cents()}"
    )
# Ran with python3, printed something like
# ch_164973 currency=eur total=12900
```

```go
package main

// Upstream package: shaped after the Kubernetes API object model, owned by
// the platform team. PodSpec and PodStatus are the upstream's vocabulary.
type PodPhase string

const (
	PhasePending PodPhase = "Pending"
	PhaseRunning PodPhase = "Running"
	PhaseFailed  PodPhase = "Failed"
)

type PodSpec struct {
	Image            string
	Replicas         int
	RestartOnFailure bool
}

type PodStatus struct {
	Name  string
	Phase PodPhase
}

func schedulePod(spec PodSpec) PodStatus {
	name := "pod-" + spec.Image
	if spec.Replicas <= 0 {
		return PodStatus{Name: name, Phase: PhaseFailed}
	}
	return PodStatus{Name: name, Phase: PhasePending}
}

// Downstream package: the deploy tool conforms. It builds and returns the
// upstream's own PodSpec/PodStatus types directly in its own deployment
// logic. There is no DeploySpec type and no mapping function between them.
type DeployTool struct {
	deployed []PodStatus
}

func (d *DeployTool) Deploy(image string, replicas int) PodStatus {
	spec := PodSpec{Image: image, Replicas: replicas, RestartOnFailure: true}
	status := schedulePod(spec)
	d.deployed = append(d.deployed, status)
	return status
}

func (d *DeployTool) RunningCount() int {
	count := 0
	for _, s := range d.deployed {
		if s.Phase == PhaseRunning || s.Phase == PhasePending {
			count++
		}
	}
	return count
}

func main() {
	tool := &DeployTool{}
	status := tool.Deploy("checkout-service", 3)
	println(status.Name, string(status.Phase), tool.RunningCount())
}
// Ran with go run, printed
// pod-checkout-service Pending 1
```

Java, Rust, and Swift are not included as separate samples. The pattern's
essence, a downstream module reusing an upstream's own types with no
translation function in between, is identical in every one of the eight
languages this repository targets, and a fourth or fifth sample would repeat
the same relationship in a different syntax without adding a distinct
lesson. `rustc` and `swiftc` are present on this machine and were used to
sanity-check that the same three-part shape, an upstream struct or type, a
downstream function using it directly, and no mapping function, compiles
cleanly in both, but the two extra samples are not included here to keep
the entry within its length budget.
