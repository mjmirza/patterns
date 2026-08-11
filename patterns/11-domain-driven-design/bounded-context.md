---
name: Bounded Context
slug: bounded-context
family: 11-domain-driven-design
category: Strategic Design
aliases: [Context Boundary, Model Boundary]
first_described: "Evans 2003"
maturity: canonical
related: [aggregate, repository, anti-corruption-layer, domain-event, cqrs, saga]
incompatible_with: []
verified: 2026-08-02
---

# Bounded Context

## 1. Name, aliases, and lineage

The canonical name is Bounded Context. It was introduced by Eric Evans in
*Domain-Driven Design. Tackling Complexity in the Heart of Software*,
Addison-Wesley, 2003, Part IV, "Strategic Design", in the chapter titled
"Maintaining Model Integrity". Evans defines it as the delimited applicability
of a particular model, the boundary within which a term, a class, and a rule
carry one specific meaning and one specific implementation, and outside of
which that same term can mean something else entirely (Eric Evans,
*Domain-Driven Design*, Addison-Wesley, 2003, ch. 14, "Maintaining Model
Integrity").

Evans coined the term in reaction to a failure mode he had watched repeatedly.
Teams try to build one unified model for an entire enterprise, the model grows
under the weight of every department's private vocabulary, and it collapses
into either a lowest common denominator that satisfies nobody or a tangle of
special cases that satisfies nobody either. His answer was not to try harder at
unification, it was to draw an explicit line around each model, name what is
inside it, and stop pretending a single word means the same thing everywhere.
This is documented directly in the book's introduction to Part IV, where Evans
writes about the futility of a single model for a whole enterprise and proposes
bounded contexts and explicit context maps as the antidote.

Vaughn Vernon, writing a decade later, treats Bounded Context as one of two
strategic pillars of DDD, the other being the Ubiquitous Language, and argues
the two cannot be separated. A language is only unambiguous inside a context,
and a context is only useful once it has a language (Vaughn Vernon,
*Implementing Domain-Driven Design*, Addison-Wesley, 2013, ch. 2, "Domains,
Subdomains, and Bounded Contexts"). Vernon also popularized the term Context
Map as the artifact that names every bounded context in a whole system and
the relationships between them, a term Evans used but did not centre as
strongly in the original book.

In casual industry usage "Context Boundary" and "Model Boundary" appear as
loose synonyms, most often in talks and blog posts rather than in the primary
literature, and they refer to the same idea, the edge past which a model's
meaning is no longer guaranteed
([Martin Fowler, "BoundedContext"](https://martinfowler.com/bliki/BoundedContext.html),
verified 2026-08-02).

A distinction worth making precisely, because conflating it with a
"microservice" is the single most common misreading in industry talks, is
that a Bounded Context is a MODELING boundary, not automatically a deployment
boundary, a database boundary, or a network boundary. Two bounded contexts can
share a process and a database schema (with separate table namespaces or
schemas) and still be two bounded contexts, and one microservice can span
multiple bounded contexts if a team is sloppy about it, which is itself
usually a design smell. Fowler is explicit about this on the same bliki page,
a bounded context is fundamentally about a linguistic and conceptual boundary,
and physical deployment decisions follow from it, they do not define it.

## 2. Problem and context

A software system of any real size accumulates more than one team, more than
one department's worldview, and more than one legitimate meaning for the same
word. Take "Customer". In a sales context a Customer is a prospect with a
pipeline stage, a probability of closing, and an assigned sales rep. In a
support context a Customer is an account with open tickets, an SLA tier, and a
satisfaction score. In a billing context a Customer is a payer with an
invoicing address, a tax jurisdiction, and a payment method. In a shipping
context a Customer is a recipient with a delivery address and a set of
fulfilment preferences. None of these four is wrong. Each is the correct
model for the problem that context is solving, and each would be actively
harmful bolted onto the others, because a shipping Customer does not need a
sales pipeline stage and a billing Customer should not carry an SLA tier.

The problem this pattern answers is what happens when a team tries to avoid
that proliferation by building one shared Customer class that every department
uses. The class accretes an optional field for every department's need,
validation rules from one department silently break another department's flow,
a migration for the billing team's tax logic risks the sales team's pipeline
data, and eventually nobody on the team can explain what a null value in a
given field means, because it depends on which department last touched the
record. Evans calls the endpoint of this trajectory the "Big Ball of Mud", a
model with no explicit boundary that has absorbed every contradiction its
stakeholders hold (Eric Evans, *Domain-Driven Design*, Addison-Wesley, 2003,
ch. 14).

The context in which Bounded Context applies is specifically a domain with
more than one subdomain whose experts use overlapping vocabulary to mean
different things, most often because the organisation itself has more than one
team with a distinct area of responsibility. A single small team building a
single small product with one internally consistent vocabulary has no need to
carve up its own model, and imposing bounded contexts there manufactures
translation overhead for no organisational reason. The pattern earns its
place exactly where Conway's Law is already operating, multiple groups of
people, multiple mental models, one shared codebase or one shared enterprise,
and the pain shows up as ambiguous terms, contradictory business rules, and a
domain model nobody trusts.

## 3. Forces

**Model consistency versus enterprise-wide reuse.** A single unified model is
attractive because it promises one source of truth and no duplicated logic.
The competing force is that unifying two departments' models by force produces
a model that is internally inconsistent, because the two departments'
underlying concepts really are different, not merely differently named. Evans
argues consistency inside a boundary matters more than reuse across
boundaries, and this is the single defining choice of the pattern.

**Team autonomy versus integration cost.** Splitting the model into contexts
lets each team evolve its own model, its own release cadence, and its own
storage independently, which is a major win for velocity in a multi-team
organisation. The cost is that any data or behaviour crossing a context
boundary needs deliberate translation, an explicit integration contract, and
ongoing maintenance of that translation as both sides evolve. A single-team
system pays this integration tax for no benefit, since there is no second team
whose model needs protecting.

**Explicitness versus effort.** Drawing and naming a boundary, agreeing an
Ubiquitous Language inside it, and documenting the relationship to neighbouring
contexts on a Context Map is real, visible, up-front work. The alternative,
letting boundaries emerge implicitly from whichever module happens to own a
database table, is cheaper today and produces the ambiguous-term problem
described in dimension 2 as the system grows.

**Coupling direction and who bears the translation cost.** When two contexts
must integrate, the relationship pattern (Vernon and Evans both formalise this
as Shared Kernel, Customer-Supplier, Conformist, or Anticorruption Layer, see
dimension 13) decides which side absorbs the model mismatch. A downstream
context that conforms to an upstream model saves translation effort but
inherits every future change the upstream team makes without negotiation. A
downstream context that builds an Anticorruption Layer pays ongoing
translation cost but is insulated from upstream churn. This is a genuine
trade-off with no universally correct answer, it depends on the political and
technical trust between the two teams.

**Cognitive load per developer.** A developer working inside one bounded
context needs to hold only that context's model in their head. The moment a
developer must reason across two contexts simultaneously, whether by reading
two codebases, joining two databases, or translating two vocabularies by hand,
cognitive load rises sharply, which is exactly why the translation is
deliberately concentrated at the boundary rather than spread throughout the
code (Vaughn Vernon, *Implementing Domain-Driven Design*, Addison-Wesley,
2013, ch. 3, "Context Maps").

## 4. Applicability and non-applicability

Reach for Bounded Context when

- More than one team or more than one department's domain experts use the
  same word for genuinely different concepts, and the ambiguity is already
  causing bugs, wrong assumptions in code review, or arguments about what a
  field means.
- The domain is large enough to decompose into distinct subdomains (core,
  supporting, generic, in Evans's terminology), each with its own natural
  vocabulary and its own rate of change.
- Different parts of the system need to evolve, deploy, or scale
  independently, and a shared model would force lockstep releases across
  teams that do not need to be in lockstep.
- The organisation is already structured into multiple teams (Conway's Law is
  in effect regardless of whether the code acknowledges it), and the goal is
  to make the software's seams match the team's seams deliberately rather than
  accidentally.
- A legacy system is being strangled or decomposed, and bounded contexts give
  a principled unit of extraction, one context at a time, rather than an
  all-or-nothing rewrite.

Do NOT reach for Bounded Context when

- The system is small enough for one team to hold the entire domain model in
  their heads without ambiguity. Imposing context boundaries here adds
  translation layers and integration contracts that serve no real
  organisational seam, purely as ceremony. Vernon calls this over-applying
  strategic patterns to a problem that does not need strategy
  (*Implementing Domain-Driven Design*, Addison-Wesley, 2013, ch. 2).
- The domain genuinely has one consistent vocabulary across every consumer.
  Not every enterprise system has the Customer problem described in dimension
  2, and forcing a split where the vocabulary truly is shared creates
  needless duplication with no corresponding benefit.
- The team is using bounded contexts as a proxy for "one microservice per
  context" without first confirming the modeling boundary is real. A
  boundary drawn around infrastructure convenience rather than around a
  genuine model discontinuity produces distributed monolith symptoms, tight
  coupling across a network instead of tight coupling inside one process,
  which is strictly worse because network calls are slower and less
  observable than in-process calls.
- The organisation cannot sustain the ongoing translation cost. An
  Anticorruption Layer relationship (dimension 13) is not a one-time setup,
  it needs a person on each side who owns keeping the translation correct as
  both models change. A two-person team drawing three bounded contexts is
  manufacturing more coordination overhead than the domain complexity
  justifies.
- The problem is really about data consistency across an operation that spans
  what would be two contexts, and the team is tempted to merge the contexts
  back into one to get a single transaction. The correct answer in DDD is
  usually a Saga or a Domain Event, not context merging, see dimension 13.

## 5. Structure

A Bounded Context is not a class or an interface, it is an organisational and
architectural boundary, so its structure is a set of participants and
artifacts rather than a class diagram.

- **The Ubiquitous Language.** The shared, precise vocabulary that domain
  experts and developers inside this one context use identically, in
  conversation, in code, in tests, and in documentation. A term's meaning is
  guaranteed only inside its owning context.
- **The domain model.** The Aggregates, Entities, Value Objects, and Domain
  Services that implement this context's concepts, per the Aggregate pattern
  in this same family (`aggregate.md`). Everything in the model belongs to
  exactly one bounded context.
- **The boundary itself.** Not necessarily a technical artifact by itself,
  though it is usually realised as a module boundary, a service boundary, a
  bounded API surface, or a set of database schemas. What makes it a
  boundary is that no code outside it references the internal model types
  directly.
- **The published language, or the context's public contract.** What this
  context exposes to the outside, an API, an event schema, a published
  message contract. This is deliberately narrower and more stable than the
  internal model.
- **The Anticorruption Layer, when present.** A translation component sitting
  at the boundary, converting this context's internal model to and from a
  neighbouring context's model, so neither model leaks into the other's
  vocabulary. Detailed in its own entry in this repository.
- **The Context Map.** The artifact, often a literal diagram, naming every
  bounded context in the system and the relationship pattern between each
  pair, Shared Kernel, Customer-Supplier, Conformist, Anticorruption Layer,
  Open Host Service, Published Language, or Separate Ways, per Vernon,
  *Implementing Domain-Driven Design*, Addison-Wesley, 2013, ch. 3.

## 6. ASCII structure diagram

```
+-----------------------------+        +-----------------------------+
|      SALES CONTEXT          |        |    BILLING CONTEXT          |
|  Ubiquitous Language        |        |  Ubiquitous Language        |
|   "Customer" = a prospect   |        |   "Customer" = a payer      |
|   with a pipeline stage     |        |   with a tax jurisdiction   |
|                              |        |                              |
|  +------------------------+ |        | +------------------------+  |
|  |  SalesCustomer         | |        | |  BillingCustomer       |  |
|  |  (Aggregate Root)      | |        | |  (Aggregate Root)      |  |
|  |  pipelineStage         | |        | |  taxJurisdiction        |  |
|  |  assignedRep           | |        | |  paymentMethod          |  |
|  +------------------------+ |        | +------------------------+  |
|                              |        |                              |
|  Published Language          |        |  Anticorruption Layer       |
|  CustomerWonEvent             |------->|  CustomerWonEventTranslator |
|  { customerId, dealValue }   |        |  converts event fields into |
+-----------------------------+        |  a new BillingCustomer      |
                                        +-----------------------------+

         one term, "Customer", two independent models,
         connected only through an explicit published event
```

## 7. Dynamics

The runtime behaviour of a bounded context is dominated by what happens at its
edges, since inside the boundary it behaves exactly like the domain model
described in the Aggregate entry.

```
1. Sales context wins a deal.
   SalesCustomer.markWon(dealValue)
       -> validates internal invariants (pipeline stage transition legal)
       -> raises CustomerWonEvent { customerId, dealValue, wonAt }
       -> event is part of Sales's PUBLISHED LANGUAGE, a stable contract,
          not the internal SalesCustomer type

2. Event crosses the boundary.
   CustomerWonEvent is placed on a message broker, or delivered via a
   webhook, or read from an outbox table. Billing context subscribes to
   this published contract, never to Sales's internal database or
   internal model types.

3. Billing's Anticorruption Layer receives the event.
   CustomerWonEventTranslator.handle(event)
       -> looks up or creates a BillingCustomer by customerId
       -> maps event.dealValue into billing's own vocabulary,
          e.g. initialContractValue, NOT a field called "dealValue"
       -> persists BillingCustomer using Billing's own aggregate rules
       -> Billing's model never sees a "pipelineStage" field, it does
          not exist in Billing's Ubiquitous Language

4. If Billing's model changes internally (a new tax rule, a new
   invoicing cadence) Sales's model and Sales's published event are
   completely unaffected, because the two contexts were never coupled
   through shared types, only through the stable published contract.
```

The essential dynamic is that translation happens exactly once, at the
boundary, and every consumer inside a context works only with that context's
own vocabulary from that point forward. No context reaches across the
boundary to read another context's internal state directly.

## 8. Implementation variants

- **Package or module boundary, single deployable.** The most common starting
  point and the one Evans himself recommends beginning with
  (*Domain-Driven Design*, Addison-Wesley, 2003, ch. 14, closing section on
  applying the pattern practically). Each bounded context is a separate
  package or namespace inside one codebase and one deployable process, with a
  linter or an architecture test (for example ArchUnit in Java, or an ESLint
  boundary rule in TypeScript) enforcing that internal types never cross a
  package boundary except through an explicitly exported facade.
- **Separate service, shared database.** Each context is its own deployable
  service, but multiple services still read from the same physical database,
  usually with separate schemas or table prefixes per context. This is a
  transitional variant, common when extracting contexts from a legacy
  monolith database that cannot yet be split, and it is explicitly called out
  by Vernon as an acceptable intermediate step rather than an end state
  (*Implementing Domain-Driven Design*, Addison-Wesley, 2013, ch. 4,
  "Architecture").
- **Separate service, separate database (microservice-per-context).** The
  fullest realisation, each context owns its own service and its own
  persistent store, communicating only through published APIs or events.
  This is what most industry talks mean by "DDD-aligned microservices", and
  Sam Newman treats bounded context alignment as the primary heuristic for
  drawing microservice boundaries (Sam Newman, *Building Microservices*, 2nd
  edition, O'Reilly, 2021, ch. 1, "What Is a Microservice").
- **Modular monolith with an event bus.** Contexts remain in-process modules
  but communicate exclusively through an internal event bus or message
  broker rather than direct method calls, so the eventual extraction to
  separate services (variant above) requires no change to the communication
  pattern, only to the transport.
- **Context per bounded API surface (Open Host Service).** Rather than
  organising code around a context, the context is defined by a stable,
  well-documented API that many consumers integrate against, with the
  implementation behind it free to be organised however the owning team
  likes. Evans and Vernon both name this the Open Host Service relationship
  pattern, most useful when a context has many, possibly unknown, downstream
  consumers.

## 9. Known production uses

- **Uber's platform architecture** is documented as being organised around
  domain-oriented microservices, with the engineering blog explicitly
  describing the move from a monolithic architecture to a set of services
  each owning a distinct business domain and its own datastore, a direct
  application of bounded contexts at scale
  ([Uber Engineering, "Domain-Oriented Microservice Architecture"](https://www.uber.com/blog/microservice-architecture/),
  verified 2026-08-02).
- **Netflix's streaming platform** is built as a large set of independently
  deployable services, and the Netflix Technology Blog describes coordinating
  a set of independently owned service boundaries around distinct business
  capabilities such as playback, billing, and recommendations, framing the
  coordination problem in terms of independently owned domain boundaries
  ([Netflix Technology Blog, "Netflix Conductor. A microservices orchestrator"](https://netflixtechblog.com/netflix-conductor-a-microservices-orchestrator-2e8d4771bf40),
  verified 2026-08-02).
- **Zalando's fashion platform** is documented by Zalando's own engineering
  team as having been restructured from two coarse-grained services into
  eight smaller ones by examining the entity-relationship diagram and
  splitting services along the business context each one served, so that
  every resulting service serves one purpose, a direct application of
  bounded contexts to correct a boundary drawn in the wrong place
  ([Zalando Engineering, "Four Lessons Learned When Working With
  Microservices"](https://engineering.zalando.com/posts/2016/04/four-lessons-with-microservices.html),
  verified 2026-08-02).
- **The .NET reference implementation "eShopOnContainers"**, published and
  maintained by Microsoft, is explicitly structured as a set of bounded
  contexts, an Ordering context, a Catalog context, a Basket context, and an
  Identity context, each with its own service, database, and API, cited by
  Microsoft's own architecture guide as a worked example of applying DDD
  bounded contexts to a microservices architecture
  ([Microsoft, ".NET Microservices. Architecture for Containerized .NET Applications", "Design a DDD-oriented microservice"](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/),
  verified 2026-08-02).

## 10. Consequences

Positive.

- Each context's model stays internally consistent, because it only has to
  satisfy the concerns of the domain experts who actually speak that
  context's Ubiquitous Language, not every stakeholder in the organisation.
- Teams gain the ability to evolve, release, and scale their own context
  independently of every other team, which is the primary enabler for
  parallel work at organisational scale.
- Ambiguous terms are resolved by construction. "Customer" can mean four
  different things across four contexts and no developer is confused,
  because each context's code only ever means one of them.
- The explicit boundary makes integration risk visible and reviewable at the
  Context Map level, rather than being an implicit, undocumented set of
  cross-module dependencies discovered only when something breaks.
- Legacy decomposition gets a principled unit. One bounded context can be
  extracted, rewritten, or replaced at a time, with the Context Map defining
  exactly what contract the replacement must honour.

Negative.

- Every boundary crossing costs real engineering effort, an explicit
  translation, an API contract, or an event schema that must be designed,
  documented, and maintained as both sides evolve. This cost is invisible in
  the small, unified-model alternative, until that alternative's own cost
  arrives later as an unmaintainable ball of mud.
- Data that conceptually belongs to "the same real-world thing" now lives in
  multiple places under multiple representations, for example a customer's
  data split across SalesCustomer and BillingCustomer, which raises genuine
  questions about eventual consistency and about which context is the
  system of record for which fact.
- Drawing the boundary in the wrong place, for example splitting a context
  that genuinely shares one model, or failing to split one that genuinely
  needs two, is expensive to correct later, since correcting it means
  renegotiating the Context Map and possibly re-migrating data across a
  boundary that is now baked into two teams' deployment pipelines.
- Overhead is disproportionate for small teams and small domains, as noted
  in dimension 4. The pattern's cost is roughly constant while its benefit
  scales with organisational size, so applying it below a certain scale is a
  net loss.
- Cross-context queries and reports become genuinely harder, since a report
  that needs fields from three contexts' models can no longer be a single
  join, it needs either a read-model that aggregates published events from
  each context (a CQRS-style projection) or an explicit, slower federated
  query across service boundaries.

## 11. Failure modes and misuse

- **Symptom.** Two microservices call each other synchronously, in both
  directions, for almost every request, and a deploy of one routinely breaks
  the other.
  **Cause.** The "bounded contexts" were drawn along infrastructure lines
  (one service per database table, or one service per CRUD resource) rather
  than along real modeling discontinuities, so the two services are actually
  one model split across a network, producing tight coupling with none of
  the latency or failure-isolation benefits a real boundary would provide.
  **Fix.** Re-examine the Ubiquitous Language on each side. If the two
  services genuinely use the same vocabulary for the same concepts, merge
  them back into one context. If they genuinely differ, replace the
  synchronous call chain with an asynchronous published event and an
  Anticorruption Layer, so each side can evolve without the other's release
  train blocking it.

- **Symptom.** A shared library of common domain types, Customer, Order,
  Product, is imported by every service in the system, and a change to that
  library requires coordinating a release across every team.
  **Cause.** This is a disguised Shared Kernel that was never agreed as a
  Shared Kernel, it was created by accident as a convenience utility
  package, so none of the governance Vernon prescribes for a real Shared
  Kernel (a small, jointly-owned surface, changed only by joint agreement,
  frequently tested end to end) is in place, and every team pays the
  coordination cost with none of the intentional benefit.
  **Fix.** Either formalise the shared package as a real, deliberately small
  Shared Kernel with joint ownership and a change process both teams agree
  to, or eliminate it entirely and let each context define its own local
  Customer type, translating at the boundary as usual.

- **Symptom.** A single Customer table with fifty nullable columns, most of
  which are null for most rows depending on which department created the
  record, and a migration in one area routinely breaks a query in another.
  **Cause.** This is the exact failure mode Bounded Context exists to
  prevent, described in dimension 2, a single unified model absorbing every
  department's contradictory needs with no boundary. Bounded Context was
  never applied, or was applied to the code but not to the underlying data
  store.
  **Fix.** Identify the real subdomains hiding inside the fifty columns,
  split the table along those seams into per-context tables or schemas, and
  introduce an explicit event or API to keep the split data eventually
  consistent where it genuinely needs to be, rather than one wide row.

- **Symptom.** A team calls their bounded context boundaries "microservices"
  in every meeting, but every one of the twelve services shares one
  PostgreSQL instance and multiple services write directly to tables owned
  by another service.
  **Cause.** The organisational and API boundaries were drawn, but the data
  ownership boundary was not, so the contexts are not actually independent,
  a schema migration in one context's tables can silently break another
  context that was reading those tables directly rather than through the
  published contract.
  **Fix.** Enforce that each context owns its data exclusively, no other
  service is granted write, and ideally not read, access to another
  context's tables. All cross-context data flow goes through the published
  API or published events, even if that means duplicating some data into a
  local read-model.

## 12. Trade-off matrix

| Force | Bounded Context (many contexts, translated) | Single Shared Model (Anemic Enterprise Model) | Shared Kernel |
|---|---|---|---|
| Internal model consistency | High, each context is internally coherent | Low, model absorbs every stakeholder's contradictions | High inside the kernel, but the kernel itself must stay small and jointly governed |
| Cross-boundary integration cost | High, every crossing needs explicit translation | Zero, there is no boundary to cross | Medium, changes need joint agreement but no runtime translation |
| Team autonomy | High, each team owns and evolves its context independently | Low, every team is coupled to one shared schema and its migrations | Medium, both teams are coupled on the kernel's surface only |
| Vocabulary ambiguity | None inside a context, by construction | High, the same word means different things depending on who wrote the row | Low inside the kernel, unresolved outside it |
| Onboarding cognitive load per context | Low, a new developer learns one context's model | High, a new developer must learn every department's exceptions to understand any query | Low for the kernel, but the kernel's discipline must be explained separately |
| Best fit | Multi-team domains with genuinely divergent subdomain vocabularies | Small, single-team systems with one truly shared vocabulary | Two closely allied teams who deliberately co-own a small, stable, shared concept |

## 13. Related and incompatible patterns

- **Aggregate** (`aggregate.md`, same family). Every bounded context is
  implemented internally as one or more Aggregates. Bounded Context is the
  strategic-level boundary around a set of Aggregates and the language that
  describes them, Aggregate is the tactical-level consistency boundary
  inside a single context. An Aggregate never spans two bounded contexts.
- **Anti-corruption Layer**. The mechanism most often used to protect one
  context's model from another's vocabulary leaking in through an
  integration. Nearly every real cross-context integration that is not a
  Shared Kernel uses one.
- **Domain Event**. The typical mechanism for a Published Language, the
  stable contract a context exposes to its downstream consumers, seen in
  dimension 7's dynamics.
- **Saga**. When a business process genuinely needs to coordinate state
  changes across more than one bounded context without a shared database
  transaction, a Saga orchestrates the sequence of local transactions and
  compensations, rather than pulling the contexts back into one merged
  model to get a single ACID transaction.
- **CQRS**. Frequently paired with Bounded Context to answer the
  cross-context reporting problem named in dimension 10, a read-model
  projection subscribes to multiple contexts' published events and builds a
  denormalised view for querying, without any context's write model needing
  to know about the others.
- **Shared Kernel**. Not incompatible, but in tension with the core idea of
  Bounded Context, since a Shared Kernel is a deliberately shared piece of
  model between two contexts. Vernon frames it as the exception that
  requires the tightest joint governance of any context relationship
  (*Implementing Domain-Driven Design*, Addison-Wesley, 2013, ch. 3), because
  the more a Shared Kernel grows, the more it erodes the independence
  Bounded Context is meant to provide.
- **Repository**. A per-context concern, each context defines its own
  Repository interfaces for its own Aggregates, and a Repository never
  reaches across a context boundary to fetch another context's aggregate
  directly.

## 14. Refactoring path in and out

Introducing a bounded context into an existing unbounded model, incrementally.

1. Interview the domain experts for the area under suspicion and write down
   their vocabulary verbatim. If the same term, "Customer", "Order",
   "Account", means visibly different things to two groups of experts, that
   is the seam.
2. Draw a proposed boundary on paper, a Context Map sketch, before touching
   code. Name the relationship to every neighbouring context, is it a
   Customer-Supplier, a Conformist, does it need an Anticorruption Layer.
3. Introduce the new context as a package or module inside the existing
   codebase first, per the package-boundary variant in dimension 8, rather
   than jumping straight to a separate service. This lets the team validate
   the boundary is correct with a fast feedback loop, a code review, rather
   than a deployment.
4. Duplicate the relevant model into the new context under its own type
   names, deliberately not reusing the old shared type. Write an
   Anticorruption Layer or a translation function at the seam, converting
   between the old shared model and the new context's model.
5. Redirect all reads and writes for the new context's concern through the
   new model exclusively, retiring the corresponding fields from the old
   shared model once nothing references them.
6. Once the module boundary has proven stable, and only if independent
   deployment or independent scaling is actually needed, extract the module
   into its own service, following the same translation contract that was
   already established at the module boundary. This is the strangler fig
   approach recommended by Vernon for legacy decomposition
   (*Implementing Domain-Driven Design*, Addison-Wesley, 2013, ch. 4).

Removing a bounded context that has stopped earning its place.

1. Confirm the two contexts' Ubiquitous Languages have actually converged,
   the same team now owns both, or the vocabularies turned out to be
   identical all along. If the vocabularies genuinely still differ, do not
   merge, the pain is organisational, not architectural.
2. Pick the surviving model, usually the one with more consumers or the
   richer invariants.
3. Migrate the losing context's data into the surviving model's shape, field
   by field, using the existing translation layer as the map of how the two
   models relate.
4. Redirect all callers to the surviving model, then delete the losing
   context's module or service, its database, and its translation layer, in
   that order, only after every caller has been redirected and verified.

## 15. Testing and verification

Bounded Context makes intra-context testing easier, because each context's
domain model can be tested in complete isolation, with no need to spin up or
mock a second context's infrastructure to test the first context's business
rules. Unit tests for SalesCustomer never need to know BillingCustomer exists.

What becomes harder is verifying the boundary itself.

- **Contract tests at the integration point.** The published API or event
  schema a context exposes needs a contract test, verifying the actual
  wire format has not silently drifted from what consumers expect. Tools
  like Pact are built specifically for this, consumer-driven contract
  testing across a service boundary
  ([Pact documentation, "Why Pact?"](https://docs.pact.io/), verified
  2026-08-02).
- **Anticorruption Layer unit tests.** The translation function at a
  boundary is itself pure logic, event or payload in, local model out, and
  should be unit tested with representative and edge-case inputs from the
  upstream context, without needing the upstream context running.
- **Consumer-driven contract or schema-registry checks in CI.** Where
  contexts communicate over an event bus, a schema registry with
  compatibility checking (for example Confluent Schema Registry's backward
  and forward compatibility modes) catches a breaking schema change before
  it reaches a downstream context's consumer at runtime.
- **End-to-end tests across the boundary, sparingly.** A small number of
  true end-to-end tests that exercise a real cross-context flow, place an
  order in Sales, verify it is billed correctly in Billing, are valuable to
  catch integration drift, but should be few, because they are slow, they
  are the most brittle tests in the suite (any change on either side can
  break them), and they duplicate coverage that unit and contract tests
  already provide within and at each context's own boundary.
- **Architecture fitness functions.** A static check, whether a linter rule,
  an ArchUnit test, or a dependency-cruiser rule, that fails the build if
  code in one context's package imports a type from another context's
  internal package, as opposed to its published API, catching boundary
  erosion in review rather than discovering it in production.

## 16. Observability signals

What to instrument, so a bounded-context architecture is visible in
production rather than a diagram nobody checks against reality.

- **Per-context service metrics, tagged by context name.** Latency, error
  rate, and throughput should be attributable to a specific bounded context,
  not aggregated across the whole system, because the whole point of the
  boundary is that one context's health should not be conflated with
  another's.
- **Boundary-crossing traffic volume and error rate.** Distributed tracing
  (for example OpenTelemetry spans annotated with the source and
  destination context) that specifically highlights calls or events
  crossing a context boundary lets a team see, at a glance, which
  integrations are the busiest and which are failing, which is the traffic
  most likely to hide a translation bug.
- **Event lag for asynchronous published contracts.** If Context A publishes
  events that Context B consumes, the lag between publication and
  consumption is a direct signal of eventual-consistency risk, a growing lag
  means downstream reads are increasingly stale relative to the source of
  truth.
- **Schema or contract compatibility violations in CI and at runtime.** A
  metric or alert on the count of contract test failures or schema-registry
  compatibility rejections catches boundary drift before or immediately as
  it happens, rather than as a mystery bug report from a downstream team.
- **Dead letter queue depth for event consumers.** A rising count of events
  that a downstream context's Anticorruption Layer failed to translate is
  the clearest possible signal that the upstream model has changed in a way
  the translation layer has not been updated to handle.

A healthy instance shows low, flat, boundary-crossing error rates, near
real-time event lag, and zero contract violations in CI over time. A failing
instance shows event lag climbing steadily, a dead letter queue that is not
being drained, or a spike in errors specifically on boundary-crossing calls
while each individual context's internal error rate stays flat, the
signature of a translation mismatch rather than an internal bug.

## 17. Security and privacy implications

Bounded Context has real, direct security and privacy implications, because it
is fundamentally a decision about where data lives and who is allowed to see
it in its native form.

- **Data minimisation at the boundary.** A well-designed Published Language
  or Anticorruption Layer is a natural enforcement point for data
  minimisation, a context only exposes the fields a downstream consumer
  genuinely needs, rather than the downstream context gaining implicit
  access to every field in the upstream context's internal model. This maps
  directly onto GDPR's data minimisation principle, Article 5(1)(c) of
  Regulation (EU) 2016/679, which requires personal data to be adequate,
  relevant, and limited to what is necessary for the stated purpose
  ([EUR-Lex, Regulation (EU) 2016/679, Article 5](https://eur-lex.europa.eu/eli/reg/2016/679/oj),
  verified 2026-08-02).
- **Blast radius containment.** Because a context owns its own data store and
  does not grant other contexts direct access to it, a credential
  compromise or an injection vulnerability in one context's service does
  not automatically expose another context's data, unlike a shared-database
  architecture where a single compromised service credential can often read
  every table in the system.
- **PII concentration risk at the translation layer.** The Anticorruption
  Layer or event consumer at a boundary is precisely the place where two
  contexts' personal data fields get correlated, for example joining a
  Sales context's prospect data with a Billing context's payment data by a
  shared customer identifier. This correlation point deserves specific
  security review and audit logging, since it is where re-identification
  risk concentrates even when each individual context's data alone would
  not be sensitive.
- **Right-to-erasure complexity.** When one real person's data is split
  across multiple bounded contexts, honouring a data-subject erasure
  request under GDPR Article 17 requires coordinating deletion across every
  context that holds a copy or a derived projection of that person's data,
  which is a genuine operational burden this pattern introduces and which
  must be designed for explicitly, typically via a registry of which
  contexts hold which subject's data, rather than discovered reactively
  when the first erasure request arrives.

This dimension's operational claims about registries and audit logging are
engineering judgement drawn from common practice, not a specific cited
standard, stated here to flag them honestly rather than dress them as a
sourced requirement.

## 18. References

- Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
  Software*, Addison-Wesley, 2003, Part IV, chapter 14, "Maintaining Model
  Integrity". Primary source for the pattern's name, definition, and
  motivating problem.
- Vaughn Vernon, *Implementing Domain-Driven Design*, Addison-Wesley, 2013,
  chapters 2 and 3, "Domains, Subdomains, and Bounded Contexts" and "Context
  Maps". Primary source for the context relationship patterns (Shared
  Kernel, Customer-Supplier, Conformist, Anticorruption Layer, Open Host
  Service) and for the strangler-fig style incremental extraction approach.
- Sam Newman, *Building Microservices*, 2nd edition, O'Reilly, 2021, chapter
  1, "What Is a Microservice". Cited in dimension 8 for treating bounded
  context alignment as the primary microservice-boundary heuristic.
- Martin Fowler, "BoundedContext",
  [https://martinfowler.com/bliki/BoundedContext.html](https://martinfowler.com/bliki/BoundedContext.html),
  verified 2026-08-02. Cited in dimension 1 for the distinction between a
  modeling boundary and a deployment boundary.
- Uber Engineering, "Domain-Oriented Microservice Architecture",
  [https://www.uber.com/blog/microservice-architecture/](https://www.uber.com/blog/microservice-architecture/),
  verified 2026-08-02. Cited in dimension 9.
- Netflix Technology Blog, "Netflix Conductor. A microservices orchestrator",
  [https://netflixtechblog.com/netflix-conductor-a-microservices-orchestrator-2e8d4771bf40](https://netflixtechblog.com/netflix-conductor-a-microservices-orchestrator-2e8d4771bf40),
  verified 2026-08-02. Cited in dimension 9.
- Microsoft, ".NET Microservices. Architecture for Containerized .NET
  Applications", "Design a DDD-oriented microservice",
  [https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/),
  verified 2026-08-02. Cited in dimension 9.
- Pact documentation, "Why Pact?",
  [https://docs.pact.io/](https://docs.pact.io/), verified 2026-08-02. Cited
  in dimension 15 for consumer-driven contract testing across a service
  boundary.
- EUR-Lex, Regulation (EU) 2016/679 (GDPR), Article 5,
  [https://eur-lex.europa.eu/eli/reg/2016/679/oj](https://eur-lex.europa.eu/eli/reg/2016/679/oj),
  verified 2026-08-02. Cited in dimension 17 for the data minimisation
  principle.

## Code examples

The following three examples implement the same integration scenario from the
diagrams above, a Sales context publishing a domain event and a Billing
context translating it through an Anticorruption Layer, in TypeScript,
Python, and Go. Each example is a self-contained, minimal illustration of the
pattern's essential mechanic, publishing at a stable boundary and translating
on receipt, rather than a full application.

### TypeScript

```typescript
// Sales context: its own internal model and its own published language.
interface CustomerWonEvent {
  customerId: string;
  dealValue: number;
  wonAt: string;
}

class SalesCustomer {
  constructor(
    public readonly customerId: string,
    private pipelineStage: string
  ) {}

  markWon(dealValue: number): CustomerWonEvent {
    if (this.pipelineStage === "won") {
      throw new Error("deal already won");
    }
    this.pipelineStage = "won";
    return {
      customerId: this.customerId,
      dealValue,
      wonAt: new Date().toISOString(),
    };
  }
}

// Billing context: its own internal model, unaware "pipelineStage" exists.
class BillingCustomer {
  constructor(
    public readonly customerId: string,
    public initialContractValue: number,
    public onboardedAt: string
  ) {}
}

// Anticorruption Layer: the only place the two vocabularies meet.
class CustomerWonEventTranslator {
  translate(event: CustomerWonEvent): BillingCustomer {
    return new BillingCustomer(
      event.customerId,
      event.dealValue,
      event.wonAt
    );
  }
}

function run(): void {
  const sales = new SalesCustomer("cust-1", "negotiation");
  const event = sales.markWon(15000);

  const translator = new CustomerWonEventTranslator();
  const billingCustomer = translator.translate(event);

  console.log(
    `Billing now owns customer ${billingCustomer.customerId} ` +
      `with contract value ${billingCustomer.initialContractValue}`
  );
}

run();
```

### Python

```python
from dataclasses import dataclass
from datetime import datetime, timezone


# Sales context: its own internal model and its own published language.
@dataclass(frozen=True)
class CustomerWonEvent:
    customer_id: str
    deal_value: float
    won_at: str


class SalesCustomer:
    def __init__(self, customer_id: str, pipeline_stage: str) -> None:
        self.customer_id = customer_id
        self._pipeline_stage = pipeline_stage

    def mark_won(self, deal_value: float) -> CustomerWonEvent:
        if self._pipeline_stage == "won":
            raise ValueError("deal already won")
        self._pipeline_stage = "won"
        return CustomerWonEvent(
            customer_id=self.customer_id,
            deal_value=deal_value,
            won_at=datetime.now(timezone.utc).isoformat(),
        )


# Billing context: its own internal model, unaware "pipeline_stage" exists.
@dataclass
class BillingCustomer:
    customer_id: str
    initial_contract_value: float
    onboarded_at: str


# Anticorruption Layer: the only place the two vocabularies meet.
class CustomerWonEventTranslator:
    def translate(self, event: CustomerWonEvent) -> BillingCustomer:
        return BillingCustomer(
            customer_id=event.customer_id,
            initial_contract_value=event.deal_value,
            onboarded_at=event.won_at,
        )


def run() -> None:
    sales = SalesCustomer("cust-1", "negotiation")
    event = sales.mark_won(15000.0)

    translator = CustomerWonEventTranslator()
    billing_customer = translator.translate(event)

    print(
        f"Billing now owns customer {billing_customer.customer_id} "
        f"with contract value {billing_customer.initial_contract_value}"
    )


if __name__ == "__main__":
    run()
```

### Go

```go
package main

import (
	"errors"
	"fmt"
	"time"
)

// Sales context: its own internal model and its own published language.
type CustomerWonEvent struct {
	CustomerID string
	DealValue  float64
	WonAt      string
}

type SalesCustomer struct {
	CustomerID    string
	pipelineStage string
}

func (s *SalesCustomer) MarkWon(dealValue float64) (CustomerWonEvent, error) {
	if s.pipelineStage == "won" {
		return CustomerWonEvent{}, errors.New("deal already won")
	}
	s.pipelineStage = "won"
	return CustomerWonEvent{
		CustomerID: s.CustomerID,
		DealValue:  dealValue,
		WonAt:      time.Now().UTC().Format(time.RFC3339),
	}, nil
}

// Billing context: its own internal model, unaware "pipelineStage" exists.
type BillingCustomer struct {
	CustomerID           string
	InitialContractValue float64
	OnboardedAt          string
}

// Anticorruption Layer: the only place the two vocabularies meet.
type CustomerWonEventTranslator struct{}

func (t CustomerWonEventTranslator) Translate(e CustomerWonEvent) BillingCustomer {
	return BillingCustomer{
		CustomerID:           e.CustomerID,
		InitialContractValue: e.DealValue,
		OnboardedAt:          e.WonAt,
	}
}

func main() {
	sales := &SalesCustomer{CustomerID: "cust-1", pipelineStage: "negotiation"}
	event, err := sales.MarkWon(15000.0)
	if err != nil {
		panic(err)
	}

	translator := CustomerWonEventTranslator{}
	billingCustomer := translator.Translate(event)

	fmt.Printf(
		"Billing now owns customer %s with contract value %.2f\n",
		billingCustomer.CustomerID,
		billingCustomer.InitialContractValue,
	)
}
```

Swift, Java, and Rust are omitted for this entry. Bounded Context is a
strategic, organisational-scale pattern rather than a language-level idiom,
and the mechanic it illustrates, publishing a stable contract and translating
it at a boundary, does not change shape across a fourth or fifth language in
a way that would teach anything the three examples above do not already show.
