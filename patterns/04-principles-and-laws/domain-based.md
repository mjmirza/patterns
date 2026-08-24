---
name: Domain-based
slug: domain-based
family: 04-principles-and-laws
category: Structural principle
aliases: [Domain-oriented organization, Package by feature, Vertical slicing, Business capability alignment]
first_described: "Evans 2003 (Domain-Driven Design, strategic patterns); Bogard 2018 (Vertical Slice Architecture, as a codebase-organization name)"
maturity: canonical
related: [bounded-context, aggregate, hexagonal-architecture, strategy, facade, single-responsibility-principle]
incompatible_with: [layered-architecture-as-primary-axis]
verified: 2026-08-02
---

# Domain-based

## 1. Name, aliases, and lineage

The canonical name in this catalog is Domain-based, meaning the principle of
organizing code, services, teams, and infrastructure around a business domain
or subdomain rather than around a technical concern such as a layer, a data
type, or a protocol. It is a structural principle, not a single pattern with
one inventor, and it shows up under several names depending on which axis of
the system it is applied to.

At the level of a domain model, the principle traces to Eric Evans, *Domain-
Driven Design. Tackling Complexity in the Heart of Software*, Addison-Wesley,
2003, in the strategic design chapters that introduce Bounded Context and
Subdomain. Evans did not invent the idea that code should mirror the business,
that observation is older and appears informally in structured-design writing
from the 1970s, but he is the person who gave the domain-oriented boundary a
name, a vocabulary, and a repeatable method, and the term is now used almost
universally in that Evans sense. Martin Fowler's summary of the concept states
plainly that Evans introduced Bounded Context and that "total unification of
the domain model for a large system will not be feasible or cost-effective",
which is the reasoning that motivates splitting a system along domain lines in
the first place (Martin Fowler, "BoundedContext",
https://martinfowler.com/bliki/BoundedContext.html, verified 2026-08-02).

At the level of a single codebase's folder layout, the same idea is called
Package by Feature (as opposed to Package by Layer) in Java and C# communities,
and Vertical Slice Architecture in the name Jimmy Bogard gave it when he wrote
"in this style, my architecture is built around distinct requests, encapsulating
and grouping all concerns from front-end to back", adding the rule "minimize
coupling between slices, and maximize coupling in a slice" (Jimmy Bogard,
"Vertical Slice Architecture", https://www.jimmybogard.com/vertical-slice-architecture/,
verified 2026-08-02). Bogard's post did not invent slicing by feature either,
the practice predates his naming, but the label Vertical Slice Architecture is
now the common name for domain-based organization at the file-and-folder level
in the .NET and increasingly the broader web-backend community.

At the level of a service boundary in a distributed system, the same axis is
called Microservices by Business Capability, described at length in Microsoft's
Azure Architecture Center guidance, "Use Domain Analysis to Model Microservices",
which states "design microservices around business capabilities, not horizontal
layers like data access or messaging" and walks through deriving service
boundaries from a Domain-Driven Design domain analysis
(https://learn.microsoft.com/en-us/azure/architecture/microservices/model/domain-analysis,
verified 2026-08-02). At the level of infrastructure and access control the same
axis appears as namespace-per-team or namespace-per-domain in Kubernetes, where
the official documentation describes namespaces as intended "for use in
environments with many users spread across multiple teams, or projects"
(Kubernetes documentation, "Namespaces",
https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/,
verified 2026-08-02); Kubernetes itself is deliberately silent on whether a
namespace maps to a business domain, a team, or a deployment stage, so this
citation supports the mechanism, not the domain-mapping convention that
platform teams layer on top of it, and that layering is engineering judgement
recorded honestly in dimension 9.

This entry treats all four of those as one underlying structural choice viewed
at four different granularities, folder, module, service, and cluster, because
the forces, the failure modes, and the trade-offs are the same shape at every
level, only the unit being organized changes.

## 2. Problem and context

A system of any real size grows two kinds of edges as it is built. Technical
edges, the seams between a controller and a service and a repository, between
a route handler and a database client, between a UI component and a state
store. And business edges, the seams between Billing and Shipping, between
Catalog and Pricing, between Onboarding and Risk. Most codebases, left to grow
without a deliberate choice, organize themselves around the technical edges
first, because that is what the framework's own folder scaffold suggests. A
typical generated web project ships `controllers/`, `services/`,
`repositories/`, `models/`, `middleware/`, one folder per technical layer, and
every new feature adds one file to each of those folders.

The problem this creates becomes visible at a specific, recognisable moment.
Someone needs to change how refunds work. The change touches
`controllers/OrderController.ts`, `services/RefundService.ts`,
`services/PaymentService.ts`, `repositories/OrderRepository.ts`,
`models/Refund.ts`, and two files under `middleware/`. Seven files across six
folders, none of them named "refund" at the top level, and the reviewer has no
single directory to open to see the whole feature. Meanwhile a change to how
shipping estimates are calculated touches an almost disjoint set of files that
happen to sit in the very same six folders, interleaved line by line in a
`git blame` with the refund work. Two teams that have nothing to do with each
other now collide constantly in the same handful of large files, because the
folder structure encodes "what kind of thing is this" instead of "what part of
the business does this belong to".

The context in which the domain-based answer is worth its cost has three
ingredients. First, the system has more than one recognisable subdomain, a
single-purpose tool with one job has nothing to align by domain. Second, more
than one person or more than one team touches the system, because the payoff
of the boundary is mostly social, it reduces how often unrelated people collide
in the same file, and a solo maintainer captures much less of that value.
Third, the domains genuinely differ in their rate and kind of change, Billing
rules change on a finance calendar, Catalog changes on a merchandising
calendar, and a shared layered folder forces both calendars to share the same
files.

## 3. Forces

- **Coupling.** Favoured within a technical concern, sacrificed within a
  domain. Domain-based organization deliberately increases how much a
  controller, a service, and a data-access call for one feature sit next to
  each other and change together, and deliberately decreases how much a
  refund controller needs to know about a shipping controller. This is the
  named trade Bogard states directly, minimize coupling between slices,
  maximize coupling in a slice.
- **Team topology.** Strongly favoured. A domain boundary is the only boundary
  in this list that a reviewer, an on-call rotation, or a repository's CODEOWNERS
  file can be drawn along without inventing an artificial split, because it
  matches how the business itself is already divided into functions. This is
  the practical payoff behind Conway's Law observations that a system's
  structure mirrors its organization's communication structure, and the honest
  reading is that domain-based organization is often an attempt to align the
  code deliberately with an organizational split that is going to happen
  whether the code plans for it or not.
- **Findability for a newcomer.** Favoured, once the domain names are the
  business's actual vocabulary. A person joining the refunds team who finds a
  `refunds/` directory containing everything refunds needs orients in minutes.
  Sacrificed when the domain boundaries are drawn wrong or too finely, because
  then a newcomer has to search across several small domain folders to find one
  coherent feature.
- **Reuse of technical infrastructure.** Sacrificed at the small end. A
  layered folder structure makes it trivial to find every repository, every
  controller, every validator in one place and apply a cross-cutting change,
  a new logging middleware, a new pagination convention, once. A domain-based
  structure spreads that same technical concern across every domain folder, so
  a cross-cutting change now touches N places instead of one.
- **Duplication versus premature abstraction.** A genuine cost. Two domains
  that independently need "compute a total from line items" will each write
  their own version rather than share a layer-level utility, because sharing
  it would recreate the coupling the boundary exists to avoid. This is a real
  trade, not a myth, some of that duplication earns its place because the two
  domains' totals are computed by different rules that will diverge later, and
  some of it is wasted effort that a shared kernel subdomain would have
  avoided, see dimension 11.
- **Consistency of cross-domain invariants.** Sacrificed. When Order and
  Inventory live in separate bounded contexts, keeping "an order can only be
  placed if inventory is reserved" true across both requires an explicit
  integration mechanism, a saga, an event, a synchronous call, rather than a
  shared transaction. The domain boundary buys independence at the cost of the
  strong consistency a single shared model would give for free.
- **Cost of getting the boundary wrong.** Asymmetric and favours caution.
  Moving a file from `services/` to `repositories/` inside a layered structure
  is a mechanical, low-risk change. Moving a capability from one bounded
  context to another means renegotiating an API contract, a data ownership
  question, and often an organizational reporting line, because the boundary
  is now social as well as technical. This is why dimension 14 treats moving
  a subdomain boundary as expensive and worth deferring until the boundary is
  well understood.

## 4. Applicability and non-applicability

Reach for domain-based organization when the following hold.

- The system has more than one subdomain that a domain expert can name in one
  sentence each, and those names are stable, "Billing", "Shipping",
  "Catalog", not "the part that talks to Stripe".
- More than one person, and ideally more than one team, works in the codebase
  concurrently, so the value captured is the reduced collision rate between
  people working on unrelated business concerns.
- The domains change at genuinely different rates or for genuinely different
  reasons, so a shared layered file would otherwise force unrelated diffs to
  interleave in the same review.
- The team wants the folder structure, the service boundary, or the namespace
  layout to become a living map of the business that a new domain expert or a
  new engineer can read without a diagram.
- The organization is going to split along business lines regardless, new
  teams, new on-call rotations, new ownership, and the code should support
  that split rather than fight it. This is the Conway's Law argument for
  choosing the boundary deliberately rather than discovering it painfully
  later.

Do NOT reach for domain-based organization in these cases, and the reason
matters more than the rule.

- **The system genuinely has one domain.** A small internal tool, a single
  CLI utility, a library with one clear purpose, gains nothing from domain
  folders and loses the easy "everything of one technical kind lives in one
  place" lookup that a small system actually benefits from. Splitting a
  120-line script into `domains/reporting/{controllers,services}` is
  ceremony with no payoff.
- **The team is one person, or a small team where everyone touches
  everything.** The main value of the boundary is reduced collision between
  people who do not talk to each other daily. A three-person team that pairs
  constantly captures almost none of that value and pays the full search cost
  of hunting across domain folders for a technical concern.
- **The domain boundaries are not yet known, or are still churning weekly.**
  Drawing folder or service lines around a domain model that is still being
  discovered locks in guesses that will be wrong, and moving a subdomain later
  is expensive, see dimension 3 and dimension 14. In an unstable early-stage
  product, a layered structure that is cheap to reorganize is often the
  honest choice until the domain model stabilises.
- **A strong cross-cutting technical concern outweighs the business split.**
  A data pipeline whose entire value is a uniform transform-and-load flow over
  many data types benefits more from being organized by pipeline stage,
  extract, transform, load, than by which business entity flows through it,
  because the stages are what actually varies in complexity and risk.
- **The chosen boundary would split a strongly consistent invariant across two
  domains for no benefit.** If two concepts must always agree inside a single
  database transaction and nothing about the business calendar or ownership
  argues for separating them, forcing a domain split trades free consistency
  for manufactured eventual consistency, see the aggregate entry for the DDD
  guidance on what belongs inside one transactional boundary.
- **The team cannot yet name the domains correctly.** A folder named `misc/`,
  `core/`, `common/`, or `shared/` sitting beside two or three "real" domain
  folders is a signal the domain analysis is incomplete, not a signal the
  approach failed, but shipping it in that state teaches the team the wrong
  lesson about what domain-based organization looks like.

## 5. Structure

Domain-based organization has no single set of class-level participants the
way a Gang of Four pattern does, because it operates on files, modules,
services, or infrastructure units rather than on objects at runtime. The
structural elements it defines are boundaries and their contents.

- **Domain (or Subdomain).** A named area of business capability, identified
  by a domain expert's vocabulary rather than by a data model. Core, Supporting,
  and Generic subdomains, in the classification Microsoft's DDD guidance uses,
  deserve different levels of investment, a Core subdomain earns the most
  careful modelling because it is where the business competes, a Generic
  subdomain, user accounts is the example given in the Microsoft guidance, is
  often satisfied by an off-the-shelf or shared solution rather than custom
  domain modelling.
- **Domain module (or slice, or bounded context, or service, or namespace).**
  The concrete unit that carries the domain's name at whichever granularity is
  in play. Inside it, every technical layer the domain needs lives together,
  its own controller-equivalent, its own service-equivalent, its own
  data-access-equivalent. This is the container dimension 4's applicability
  list is judging.
- **Domain boundary.** The explicit line the module does not let outside code
  cross without going through a published interface. At the folder level this
  is enforced by convention and, ideally, a lint rule against cross-domain
  imports. At the service level it is enforced by the network, another
  service cannot reach into your database. At the namespace level it is
  enforced by Kubernetes role-based access control.
- **Shared kernel (optional).** A small, explicitly agreed area that more than
  one domain is allowed to depend on, reserved for genuinely universal
  concepts, a Money type, a UserId type, an authentication check, that are
  cheaper to share than to duplicate across every domain and stable enough
  that sharing them will not recreate the coupling problem the boundary exists
  to avoid.
- **Integration mechanism.** The explicit, visible way one domain's module
  talks to another's, a published event, a synchronous call through a defined
  interface, a message queue, rather than a direct reach into the other
  domain's internal files or tables. Evans's Context Map vocabulary, Customer
  Supplier, Open Host Service, Anti-corruption Layer, Separate Ways, names the
  common shapes this integration takes (cited via the Microsoft guidance's
  summary of Evans's relationship patterns, verified 2026-08-02).

## 6. ASCII structure diagram

```
LAYER-BASED (the axis this principle replaces as primary)

  controllers/        services/            repositories/
  +-------------+     +---------------+    +----------------+
  | OrderCtrl   |     | OrderService  |    | OrderRepo      |
  | RefundCtrl  |     | RefundService |    | RefundRepo     |
  | ShipCtrl    |     | ShipService   |    | ShipRepo       |
  +-------------+     +---------------+    +----------------+
        ^                    ^                    ^
        |     one feature touches every column     |
        +---------------------+--------------------+
                    (refund change = 3 folders)


DOMAIN-BASED (the axis this principle makes primary)

  domains/refunds/          domains/shipping/         domains/catalog/
  +--------------------+    +--------------------+    +--------------------+
  | controller.ts      |    | controller.ts      |    | controller.ts      |
  | service.ts         |    | service.ts         |    | service.ts         |
  | repository.ts      |    | repository.ts      |    | repository.ts      |
  | model.ts           |    | model.ts           |    | model.ts           |
  +--------------------+    +--------------------+    +--------------------+
           |                          |                          |
           |   published interface    |   published interface    |
           +-----------> shared-kernel/ (Money, UserId) <---------+
                          (small, explicit, agreed)

  A feature that stays inside "refunds" touches one folder.
  A change that crosses domains goes through the published interface,
  never a direct import into another domain's internal file.
```

## 7. Dynamics

The dynamics of domain-based organization are less a runtime call sequence and
more a decision process, exercised twice, once when a new capability is placed
and once when a request actually flows through the system at runtime. Both are
shown.

```
PLACEMENT DECISION (exercised by a developer, not by a program)

New requirement arrives
        |
        v
Which subdomain's vocabulary does this belong to?
        |
   +----+----------------------------+
   | belongs to one existing domain  | belongs to no domain cleanly
   v                                  v
Add file inside that domain's       Is this a new subdomain, or a
folder/module/service. Done.        cross-cutting technical concern?
                                            |
                              +-------------+--------------+
                              | new subdomain                | technical concern
                              v                                v
                    Create new domain module,          Place in shared-kernel
                    define its published interface,    ONLY if genuinely
                    map its integration to neighbours   universal and stable,
                                                          else it stays local
                                                          to the one domain
                                                          that needs it.


RUNTIME FLOW (a request that must cross two domains)

Client        Refunds module        Shipping module (published interface)
  |                  |                          |
  |-- POST /refund ->|                          |
  |                  |-- refund.approve() ----->|
  |                  |    (internal, same domain)
  |                  |                          |
  |                  |-- ShippingApi.reverseShipment(orderId) --->|
  |                  |    (crosses the boundary through the       |
  |                  |     PUBLISHED interface, never a direct    |
  |                  |     import of shipping's internal types)   |
  |                  |<-- ShipmentReversed event -----------------|
  |<-- 200 refunded -|                          |
```

The property worth naming is the second flow. Refunds never imports
Shipping's internal `Shipment` type or reaches into its table. It calls a
narrow, versioned surface Shipping publishes for exactly this purpose. That
narrow surface is what keeps the two domains independently deployable and
independently owned, and it is the piece most often skipped by teams that
adopt domain-named folders without adopting the discipline behind them, see
dimension 11.

## 8. Implementation variants

**Package by feature (folder level, single codebase).** The most common form
in web backends. Every domain gets one top-level folder holding its own
controller, service, and data-access files. A cross-domain import lint rule,
where the tooling supports it, is what turns this from a naming convention
into an enforced boundary, without it the folders are advisory only and drift
back into cross-imports under deadline pressure.

**Vertical slice per use case (finer than per domain).** Bogard's original
formulation slices at the level of a single request or command, not a whole
domain, so `CreateOrder/`, `CancelOrder/`, and `RefundOrder/` are each their
own slice inside the Orders area, each with its own handler and its own
request and response shape, deliberately accepting some duplication between
slices rather than sharing a generic `OrderService`. This is the strongest
form of "minimize coupling between slices, maximize coupling in a slice"
because even two use cases inside the same domain do not share code unless
that sharing is deliberate.

**Bounded context per service (distributed systems).** Each domain becomes an
independently deployable service with its own datastore, communicating only
through published APIs or events, following the Microsoft Azure Architecture
Center's domain-analysis-to-microservice-boundary process cited in dimension
one. This is the variant that pays the largest infrastructure cost, network
calls, eventual consistency, deployment pipelines per service, and earns that
cost only when the domains genuinely need independent scaling, independent
release cadence, or independent team ownership, not merely independent code.

**Namespace or account per domain (infrastructure level).** Kubernetes
namespaces, cloud provider accounts or projects, and access-control groups
scoped one-per-domain give the boundary teeth at the infrastructure layer,
someone in the Shipping namespace cannot read a Secret in the Billing
namespace by accident. Kubernetes documentation is explicit that namespaces
exist for dividing resources among multiple teams or projects, and is
deliberately silent on domain semantics, so a domain-per-namespace mapping is
a convention a platform team adopts on top of the mechanism, not something
Kubernetes itself prescribes.

**Modular monolith (a hybrid worth naming explicitly).** Domain modules live
inside one deployable and one repository, each with its own package and its
own internal data-access, but they compile and deploy together and can still
share a single database, provided each module owns its own tables and no
module writes directly to another's tables. This variant is often the correct
middle point between the layered monolith's collision problem and the
distributed bounded-context's operational cost, because it gets the folder and
ownership benefits of dimension 3 without paying network latency or deployment
fragmentation for domains that do not yet need independent scaling.

**Package by feature inside a functional or scripting language.** In Python
and Go, where there is no framework-imposed `controllers/services/repositories`
scaffold to fight, domain-based organization is closer to the path of least
resistance, a `refunds` package or module holding everything refunds needs,
with the language's own visibility rules, an unexported name in Go, a
name prefixed with a single leading `_` character in Python, standing in
for the published interface from dimension 5.

## 9. Known production uses

**Netflix, Domain-Oriented Microservice Architecture (DOMA).** Netflix's
engineering blog describes organizing microservices around business domains
with explicit ownership and integration points as a named internal
architectural approach for large service estates, framed around the same
bounded-context reasoning cited above, applied at Netflix's scale of hundreds
of independently owned services (Netflix Technology Blog, engineering posts on
service architecture at netflixtechblog.com, verified 2026-08-02 that the
publication exists and covers microservice organization at Netflix; the exact
DOMA post could not be independently re-verified at a stable URL during this
session because the direct link redirected through a login-gated redirect
page, so this claim is recorded at the level Netflix's own public engineering
communications generally support rather than quoted from one specific
unreachable page).

**Microsoft Azure Architecture Center, reference microservices guidance.**
Microsoft's own architecture guidance for building microservices on Azure
walks through Domain-Driven Design's strategic phase, subdomain
classification into Core, Supporting, and Generic, and bounded-context
definition as the prescribed method for deciding microservice boundaries,
explicitly stating "design microservices around business capabilities, not
horizontal layers like data access or messaging" (Microsoft, "Use Domain
Analysis to Model Microservices", Azure Architecture Center,
https://learn.microsoft.com/en-us/azure/architecture/microservices/model/domain-analysis,
verified 2026-08-02).

**Kubernetes, namespace-scoped multi-tenancy.** The Kubernetes project itself
documents namespaces as the mechanism "for use in environments with many users
spread across multiple teams, or projects", and the widely adopted operational
convention on top of that mechanism, one namespace per business domain or
product team, with role-based access control scoped to the namespace, is the
standard way large organizations partition a shared cluster (Kubernetes
documentation, "Namespaces",
https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/,
verified 2026-08-02).

**.NET community, Vertical Slice Architecture in production ASP.NET Core
codebases.** Jimmy Bogard's MediatR library, one of the most widely used
request-dispatch libraries in the .NET ecosystem, is built specifically to
support the vertical-slice style he named, where each request type is its own
self-contained handler rather than a method on a shared, layered service
class, and his own writing frames the whole approach as an alternative to
n-tier layering for exactly the file-collision reasons in dimension 2 (Jimmy
Bogard, "Vertical Slice Architecture",
https://www.jimmybogard.com/vertical-slice-architecture/, verified 2026-08-02).

## 10. Consequences

Positive.

- A newcomer, or a domain expert who is not an engineer, can find their way
  around the system by the business vocabulary they already know, "where is
  refunds" resolves to one folder or one service, not a search across six.
- Unrelated features stop colliding in the same file, which reduces merge
  conflicts and makes code review scoped to the actual feature under change
  rather than everything that happened to touch the same layer that week.
- Team ownership boundaries have an honest place to attach, a CODEOWNERS
  entry, an on-call rotation, a service's deploy pipeline, can each be scoped
  to a domain the team actually understands end to end.
- A domain can be extracted into its own deployable later with dramatically
  less rework than extracting one from a layered structure, because its files
  are already co-located and its dependencies on other domains are already
  forced through a published interface, when the boundary discipline in
  dimension 5 was actually followed.
- Deletion becomes cheap. A domain that is retired can, in the healthy case,
  be deleted as one directory or decommissioned as one service, rather than
  hunted for across every layer folder.

Negative.

- Genuine, correct duplication appears at the domain boundary, the same
  validation rule or the same small calculation written twice because sharing
  it would reintroduce coupling, and a team unused to this trade-off will read
  it as sloppiness rather than as the cost the boundary is buying.
- A cross-cutting technical change, a new required header on every outgoing
  call, a new logging field, now touches every domain module instead of one
  shared layer, and needs its own automation or checklist to land consistently.
- Drawing the boundary wrong is expensive to undo, more expensive than moving
  a file between layer folders, because a wrong domain boundary often carries
  a wrong data-ownership decision and, at the service level, a wrong network
  contract with it.
- A "shared" or "common" or "core" folder tends to accumulate anything nobody
  can cleanly place, and once it exists it grows, quietly reintroducing the
  cross-cutting coupling the boundary was meant to remove, see dimension 11.
- At the distributed-service variant specifically, the domain gains
  independent deployability at the cost of a real distributed system, network
  failures, eventual consistency, and operational surface area that a single
  well-organized monolith with domain modules does not pay.

## 11. Failure modes and misuse

**The junk-drawer shared folder.** Symptom. A `common/`, `shared/`, or
`utils/` package that grows every sprint and is imported by every domain
module, until it is effectively the old layered structure wearing a new name.
Cause. No one owns deciding what genuinely belongs in the shared kernel, so
anything that is inconvenient to duplicate gets dumped there by default. Fix.
Require an explicit, reviewed decision before anything enters the shared
kernel, and periodically audit it for things that turned out to be
domain-specific after all and should move back out.

**Domain names that are really technical concerns in a business costume.**
Symptom. Folders named `notifications/`, `logging/`, `validation/` sitting
beside `refunds/` and `shipping/` at the same level, as if they were peer
domains. Cause. The team applied the folder pattern without doing the domain
analysis dimension 4 requires. Fix. Ask a domain expert, someone who is not an
engineer, whether the name is one they use; if the answer is no, the folder is
a technical layer that should either live inside the one domain that needs it
or become genuine shared infrastructure, not a peer domain.

**Cross-domain imports that bypass the published interface.** Symptom. A
`grep` for imports from `../shipping/internal/` inside the `refunds/`
directory returns hits. Cause. Under deadline pressure, reaching directly into
another domain's internals is faster than defining and versioning a proper
interface, and nothing enforced the boundary. Fix. A lint rule, an
architecture test such as those built with ArchUnit for Java or import-linter
for Python, or a module-boundary feature in the build tool, that fails the
build on a cross-domain internal import.

**The distributed monolith.** Symptom. Every deploy of Refunds requires
Shipping and Billing to deploy at the same time or the system breaks, even
though they are three separate services. Cause. The service split happened at
the domain level, but the data model, or a shared synchronous call chain that
never tolerates partial failure, did not, so the services are contractually
coupled even though they are physically separate. Fix. This is a design defect
to correct, not a domain-boundary defect, either merge the services back into
one deployable that shares a transaction honestly, or fix the contract so each
service can evolve and fail independently, following the guidance in the
bounded-context and aggregate entries on where a transactional boundary
actually belongs.

**Premature service extraction along a guessed domain line.** Symptom. A
service was split out early, and eighteen months later half its endpoints
exist only because another, still-young domain needed them, and the two
services now deploy in lockstep anyway. Cause. The domain boundary was drawn
before the domain model was understood, see the non-applicability list in
dimension 4. Fix. Merge the services back, keep the domain-based folder
structure inside the merged deployable, and defer the physical split until the
boundary has stayed stable for a long stretch, following the refactoring
path in dimension 14.

**One domain silently owns another domain's data.** Symptom. The `refunds`
service's database has a table called `shipments` that it writes to directly.
Cause. It was faster, at the time, to skip Shipping's API and write straight
to what looked like the same database. Fix. Establish and enforce data
ownership per domain, one writer per table or per aggregate, with every other
domain going through the owner's published interface, which is the same
discipline the aggregate entry requires inside a single bounded context,
applied here across bounded contexts.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Domain-based organization | Layered (technical) organization | Vertical Slice per use case | Hexagonal / Ports and Adapters (orthogonal axis) |
|---|---|---|---|---|
| Locating one feature's code | One folder or module, direct | Search across N technical layers | One folder, even narrower than domain | Depends on the port, not primarily on feature |
| Cross-cutting technical change | Touches every domain module | Touches one shared layer | Touches every slice | Touches the adapters that implement the port |
| Team collision rate | Low, teams own domains | High, everyone edits the same layer files | Lowest, even two engineers on one domain rarely collide | Orthogonal, does not directly address this force |
| Duplication | Moderate, at domain boundaries and shared logic | Low, shared services reused freely | Highest, duplication is the explicit trade accepted | Orthogonal |
| Onboarding via business vocabulary | Strong, folder names match the domain expert's language | Weak, folder names are technical | Strong at the use-case level, sometimes too fine to see the whole domain | Weak, port names are technical (input port, output port) |
| Independent deployability later | Cheap to extract if boundary discipline held | Expensive, dependencies are scattered by layer | Cheap per use case, but a whole domain still needs assembling | Enables swapping an adapter, not extracting a domain |
| Cost of a wrong boundary | High, often carries a data-ownership mistake with it | Low, moving a file between layers is mechanical | Medium, a wrong use-case split is cheaper to fix than a wrong domain split | Low to medium, an adapter can be replaced without moving the domain core |
| Strong transactional consistency across the boundary | Deliberately sacrificed across domains | Free within one shared transaction | Sacrificed at the use-case level too, by design | Not affected by this axis directly |

Reading of the table. Domain-based organization and Vertical Slice
Architecture sit on the same axis and differ mainly in granularity, domain
versus single use case, so a codebase often uses both together, domain folders
at the top level and vertical slices inside each domain. Hexagonal
Architecture is an orthogonal axis entirely, it separates a domain's core
logic from its infrastructure adapters, and a domain-based module commonly has
its own internal hexagonal shape, ports for the things the domain depends on,
adapters for the concrete infrastructure, without that changing which domain
the module belongs to. Layered organization remains the right default when the
system is small enough, or the team small enough, that the collision force in
row three does not yet bite.

## 13. Related and incompatible patterns

- **Bounded Context.** The direct ancestor at the domain-modelling level.
  Bounded Context is the DDD concept that names the boundary within which one
  domain model applies consistently, and domain-based organization at the
  folder, service, and namespace level is largely the practice of making a
  codebase's physical structure mirror an already-identified bounded context.
  A domain-based folder drawn without first doing the bounded-context analysis
  is guessing at the line, which is exactly the failure mode in dimension 11.
- **Aggregate.** Composes below it. Inside one domain module, the aggregate
  pattern decides where the transactional consistency boundary sits, which
  entities must change together atomically. Domain-based organization decides
  which domain module those entities belong to in the first place; aggregate
  design then happens inside that module.
- **Hexagonal Architecture, Ports and Adapters.** An orthogonal, complementary
  axis, as noted in dimension 12. A domain module commonly applies Hexagonal
  Architecture internally, so the domain's core rules stay independent of
  which database or which external API implements a given port, while the
  domain-based boundary decides which domain owns that hexagon in the first
  place.
- **Strategy.** A tactical pattern that frequently lives inside a domain
  module rather than replacing the domain boundary. Where a domain has several
  interchangeable business rules, a pricing strategy per customer tier for
  example, Strategy expresses that variation inside the Pricing domain, it
  does not decide where the Pricing domain's boundary sits.
- **Facade.** Frequently the shape of the published interface a domain module
  exposes to its neighbours, see dimension 5. A domain's Facade hides its
  internal controller, service, and repository files behind a small, stable
  surface the rest of the system is allowed to call.
- **Layered Architecture as the primary organizing axis.** Directly
  incompatible as a top-level choice, though not incompatible as a secondary
  one. A codebase cannot have both "the top-level folders are technical
  layers" and "the top-level folders are business domains" as its primary
  organizing principle at once; a team can, however, use domain folders at the
  top level and a light internal layered shape, `controller.ts`,
  `service.ts`, `repository.ts`, inside each domain folder, which is the
  common healthy combination shown in dimension 6.
- **Shared Kernel (a DDD relationship pattern, not a separate catalog entry
  here).** Deliberately compatible in small, disciplined doses, and actively
  in tension with the boundary in large ones, see dimension 11's junk-drawer
  failure mode.

## 14. Refactoring path in and out

Introducing domain-based organization into a codebase that is currently
organized by layer.

1. Do the domain analysis first, before moving a single file. List the
   subdomains a domain expert would name, and classify each as Core,
   Supporting, or Generic following the method in dimension 9's Microsoft
   citation. Skipping this step and mechanically renaming layer folders to
   guessed domain names is the single most common cause of the technical-
   concerns-in-a-domain-costume failure in dimension 11.
2. Pick the domain with the clearest, most stable boundary and the least
   traffic from other parts of the system as the first one to move, not the
   most important domain. The first migration should prove the pattern
   cheaply, not bet the riskiest area of the business on an unproven
   convention.
3. Create the new domain folder or module and copy, do not yet delete, the
   files that clearly belong to it from the layered structure into it,
   `controller.ts`, `service.ts`, `repository.ts` inside `domains/refunds/`.
   Run the tests.
4. Redirect imports across the codebase from the old layered paths to the new
   domain path, one call site at a time, keeping both the old and new files
   present until every caller has moved. Run the tests after each batch.
5. Delete the now-unused files from the old layered folders. This is Move
   File plus Inline, applied at module granularity, see the refactoring
   family entries for the file-level versions of both.
6. Add the cross-domain import lint rule from dimension 11 before moving the
   second domain, so the first migrated domain does not silently regress back
   into cross-imports while attention is on the next one.
7. Repeat per domain, in order of clearest boundary first, most entangled
   boundary last, because each earlier migration teaches the team the
   vocabulary and the discipline the harder migrations will need.

Removing domain-based organization when it stops earning its place. Signals
this has happened include a solo maintainer inheriting a multi-team system
after the team shrank, or a domain split that has stayed contractually
coupled, see the distributed-monolith failure mode, long enough that the
independence it was meant to buy never materialised.

1. Confirm the collision force from dimension 3 has genuinely gone away, not
   merely that the current team feels the ceremony is annoying, before
   flattening the structure, because the boundary is cheap to keep and
   expensive to rebuild if the team grows again.
2. If several domains have become tightly, permanently coupled, follow the
   distributed-monolith fix in dimension 11, merge the coupled services or
   modules back into one deployable, but keep the domain folders inside it as
   documentation of the original boundary rather than flattening straight to
   a layered structure.
3. Only flatten fully to a layered structure when the system has genuinely
   shrunk to one effective domain, in which case remove the domain folder
   nesting and move each domain's controller, service, and repository files
   back under the corresponding technical layer folder, reversing the steps
   above.

## 15. Testing and verification

Easier because of the pattern.

- A test suite naturally organizes itself the same way the code does, a
  `refunds/` test directory covers the refunds domain end to end, which makes
  it obvious which tests must pass before a change to that domain ships and
  which are unrelated noise from a different area.
- Contract tests at the published interface, see dimension 5, become a
  natural place to pin the promise one domain makes to its neighbours,
  independent of either domain's internal implementation, so Refunds' team can
  refactor freely inside their module as long as the contract test against
  Shipping's published API still passes.
- A domain module with a disciplined boundary is easier to test in isolation,
  because its dependencies on other domains are already forced through a small
  interface that a test double can stand in for, rather than a tangle of
  direct calls into another layer's concrete classes.

Harder because of the pattern.

- An end-to-end scenario that genuinely spans several domains, place an order,
  reserve inventory, schedule shipping, needs a test that exercises the real
  integration across module or service boundaries, and that test is slower and
  more fragile than a single-domain unit test, and needs its own strategy for
  where it lives, since it does not belong cleanly inside any one domain
  folder.
- Detecting an accidental cross-domain coupling, see dimension 11, is not
  caught by ordinary unit tests at all, it needs an architecture test, a
  static import check, or a dependency-direction test, run as its own gate.

Techniques that apply.

- **Architecture tests.** Tools such as ArchUnit for Java and Kotlin, or
  import-linter for Python, or a custom ESLint rule for TypeScript, that fail
  the build when a file inside one domain imports an internal file of another
  domain, are the mechanical enforcement for the boundary described narratively
  in dimension 5.
- **Consumer-driven contract tests at the published interface.** Each
  downstream domain records the shape of the calls it makes against its
  neighbour's published interface, and the upstream domain runs those
  recorded contracts in its own test suite, catching a breaking change before
  it reaches the consuming domain rather than after.
- **Domain-scoped test suites in CI.** Running only the tests inside the
  domain a change actually touched, plus the contract tests at its published
  boundary, rather than the entire system's test suite on every change, is
  both a testing-speed technique and a forcing function that keeps a domain's
  test suite honestly scoped to that domain.

## 16. Observability signals

The organizational boundary is invisible to a program at runtime unless it is
deliberately surfaced, so what to record depends on the granularity in play.

What to record.

- At the service or namespace granularity, tag every request, log line, and
  trace span with the owning domain as a first-class attribute, so a request
  that crosses from Refunds into Shipping shows the boundary crossing
  explicitly in a distributed trace rather than appearing as one undifferentiated
  call chain.
- A counter of cross-domain calls, labelled by source domain and target
  domain, is the single most useful signal for judging whether the boundary
  drawn matches how the system actually behaves; a pair of domains with a
  very high call volume between them is a candidate for merging, see
  dimension 14.
- A counter of contract-test failures at each published interface, so a
  domain team can see, before a deploy, whether their change is about to break
  a promise a neighbouring domain relies on.
- At the folder or module granularity inside a single deployable, ownership
  metadata, a CODEOWNERS entry per domain folder, gives a code-frequency and
  code-ownership signal that a dashboard can turn into "which domain folder
  changed the most this quarter" and "which folder has no clear owner",
  directly surfacing the junk-drawer failure mode from dimension 11.

A healthy instance on a dashboard. Cross-domain call volume is low relative to
within-domain call volume, and stable over time. Contract-test failures are
rare and caught pre-deploy, not discovered as a production incident. Every
domain folder or service has a clear, current owner. Deploy frequency per
domain is roughly independent of deploy frequency in other domains, meaning a
domain team can ship without waiting on another team's release train.

A failing instance. Cross-domain call volume climbs steadily between two
specific domains, pointing at the distributed-monolith failure mode.
Contract-test failures cluster around one published interface, pointing at a
domain that keeps changing its contract without warning its consumers. A
folder or service with no clear owner in the CODEOWNERS data, or with commits
from an unusually wide spread of unrelated teams, is the junk-drawer signal
surfacing in the metrics rather than only in a manual code review.

## 17. Security and privacy implications

Domain-based organization has direct, largely positive security consequences,
because the same boundary that reduces accidental coupling also reduces
accidental access.

**Least privilege by domain.** When the boundary is enforced at the
infrastructure level, a namespace per domain in Kubernetes, a separate cloud
account or project per domain, access control can be scoped to the domain a
person actually works on rather than granted broadly across the whole system.
This is the practical security payoff of the mechanism the Kubernetes
namespace documentation describes for dividing cluster resources among teams,
applied deliberately along business-domain lines.

**Data ownership reduces the blast radius of a credential leak.** If Refunds'
service credentials are compromised, and Refunds genuinely does not hold a
direct connection to Shipping's database because every cross-domain call goes
through Shipping's published interface, see dimension 5, the compromise is
contained to Refunds' own data rather than automatically exposing Shipping's
as well. This benefit disappears entirely if the boundary is nominal only, see
the silently-owns-another-domain's-data failure mode in dimension 11, so it is
a property the discipline earns, not a property the folder names alone
provide.

**A published interface is a natural place to enforce authorization
consistently.** Because every cross-domain access is forced through one
narrow surface rather than scattered direct calls, that surface is also the
one place a policy check, this caller may read refund status but not modify
it, needs to be implemented and audited, rather than needing to be
re-implemented correctly at every call site across the codebase.

One genuine risk this entry states plainly rather than glossing over. A
poorly drawn domain boundary can scatter personal data across more services,
tables, and namespaces than a single well-controlled data store would, which
complicates a data-subject deletion or export request under privacy
regulation, because now every domain that independently stores a piece of a
person's data must be located and updated. This is a real cost of the
distributed-service variant specifically, and the mitigation is the same
discipline dimension 5 already asks for, one domain owns each piece of data,
with an explicit, documented map of which domain holds what, so a deletion
request can be routed correctly rather than requiring an ad hoc search across
every service.

## 18. References

1. Eric Evans. *Domain-Driven Design. Tackling Complexity in the Heart of
   Software*. Addison-Wesley, 2003. ISBN 0-321-12521-2. Strategic design
   chapters, source of Bounded Context, Subdomain, and the Context Map
   relationship vocabulary, Customer Supplier, Open Host Service, Anti-
   corruption Layer, Separate Ways, cited in dimensions 1 and 5.
2. Martin Fowler. "BoundedContext". martinfowler.com bliki entry.
   https://martinfowler.com/bliki/BoundedContext.html
   Verified 2026-08-02. Source for the summary of Evans's reasoning that a
   single unified domain model does not scale to a large system, cited in
   dimension 1.
3. Microsoft. "Use Domain Analysis to Model Microservices". Azure
   Architecture Center.
   https://learn.microsoft.com/en-us/azure/architecture/microservices/model/domain-analysis
   Verified 2026-08-02. Source for the business-capability design guidance,
   the Core, Supporting, Generic subdomain classification, and the
   description of bounded contexts and context maps, cited in dimensions 1, 5,
   and 9.
4. Kubernetes project. "Namespaces". Kubernetes documentation.
   https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/
   Verified 2026-08-02. Source for the namespace-as-team-or-project-division
   mechanism, cited in dimensions 1, 8, 9, and 17. The documentation does not
   itself claim a domain mapping; that convention is recorded as engineering
   judgement in dimension 8.
5. Jimmy Bogard. "Vertical Slice Architecture". jimmybogard.com.
   https://www.jimmybogard.com/vertical-slice-architecture/
   Verified 2026-08-02. Source for the Vertical Slice Architecture name, the
   coupling-minimization framing, and the MediatR production-use claim, cited
   in dimensions 1, 8, and 9.
6. Melvin Conway. "How Do Committees Invent?". *Datamation*, April 1968.
   Source of the observation, referenced by Microsoft's own domain-analysis
   guidance under the name Conway's Law, that a system's structure tends to
   mirror the communication structure of the organization that builds it,
   cited as motivation in dimension 3. Cited at the level Microsoft's own
   guidance cites it; the original 1968 article was not independently
   re-verified in this session.

## Code examples

Three languages, chosen because each shows domain-based organization at a
genuinely different mechanism for enforcing the boundary. Go uses package
visibility, an unexported identifier is invisible outside its package, so the
language itself enforces "no reaching into another domain's internals".
TypeScript shows the folder-and-published-interface shape most web backends
use, where the boundary is a convention the code follows rather than something
the compiler enforces on its own. Python shows the same convention with the single leading `_` character
signal Python developers use in place of a compiler-checked private keyword. Java is intentionally not shown, not because
the pattern does not apply there, ArchUnit is one of the most common tools for
enforcing exactly this boundary in Java codebases, but because no Java runtime
was available in the environment used to write this entry, and claiming a
compiled result without one would be dishonest, see the note at the end of
this section.

### Go

```go
package main

import "fmt"

// Package-level visibility is the enforcement mechanism here.
// Only exported (capitalized) names cross the domain boundary.

// --- domain: refunds ---
type Refund struct {
	OrderID string
	Amount  int
}

// unexported: internal to the refunds domain, cannot be reached from outside
func validateRefund(r Refund) error {
	if r.Amount <= 0 {
		return fmt.Errorf("refund amount must be positive")
	}
	return nil
}

// exported: the refunds domain's published interface
func ApproveRefund(r Refund, reverseShipment func(orderID string) error) error {
	if err := validateRefund(r); err != nil {
		return err
	}
	return reverseShipment(r.OrderID)
}

// --- domain: shipping ---
type shipment struct {
	OrderID  string
	Reversed bool
}

var shipments = map[string]*shipment{
	"order-42": {OrderID: "order-42"},
}

// exported: shipping's published interface, this is what refunds is allowed to call
func ReverseShipment(orderID string) error {
	s, ok := shipments[orderID]
	if !ok {
		return fmt.Errorf("no shipment for order %s", orderID)
	}
	s.Reversed = true
	return nil
}

func main() {
	r := Refund{OrderID: "order-42", Amount: 1999}
	if err := ApproveRefund(r, ReverseShipment); err != nil {
		fmt.Println("refund failed:", err)
		return
	}
	fmt.Println("refund approved, shipment reversed:", shipments["order-42"].Reversed)
}
```

### TypeScript

The two domain modules are shown as if in separate files, `domains/refunds/service.ts`
and `domains/shipping/service.ts`. They are concatenated into one block here only
so the sample runs standalone. In a real codebase each domain's file exports only
its published surface and the entry point imports from both file paths.

```typescript
namespace RefundsDomain {
  interface Refund {
    orderId: string;
    amount: number;
  }

  // Not exported outside this namespace: internal to the refunds domain.
  function validateRefund(r: Refund): void {
    if (r.amount <= 0) throw new Error("refund amount must be positive");
  }

  // Exported: the refunds domain's published surface.
  export function approveRefund(
    r: Refund,
    reverseShipment: (orderId: string) => boolean
  ): boolean {
    validateRefund(r);
    return reverseShipment(r.orderId);
  }
}

namespace ShippingDomain {
  interface Shipment {
    orderId: string;
    reversed: boolean;
  }

  const shipments = new Map<string, Shipment>([
    ["order-42", { orderId: "order-42", reversed: false }],
  ]);

  // Exported: shipping's published interface. Refunds is only allowed to call
  // this, never to reach into `shipments` directly.
  export function reverseShipment(orderId: string): boolean {
    const s = shipments.get(orderId);
    if (!s) throw new Error(`no shipment for order ${orderId}`);
    s.reversed = true;
    return true;
  }
}

// entry point: wires the two domain modules through their published interfaces
const ok = RefundsDomain.approveRefund(
  { orderId: "order-42", amount: 1999 },
  ShippingDomain.reverseShipment
);
console.log("refund approved:", ok);
```

### Python

```python
# domains/refunds/service.py
class Refund:
    def __init__(self, order_id: str, amount: int):
        self.order_id = order_id
        self.amount = amount


def _validate_refund(refund: Refund) -> None:
    # Leading underscore: internal to this domain, not part of the published interface.
    if refund.amount <= 0:
        raise ValueError("refund amount must be positive")


def approve_refund(refund: Refund, reverse_shipment) -> bool:
    # No underscore: this is the refunds domain's published interface.
    _validate_refund(refund)
    return reverse_shipment(refund.order_id)


# domains/shipping/service.py
_shipments = {"order-42": {"order_id": "order-42", "reversed": False}}


def reverse_shipment(order_id: str) -> bool:
    # Published interface. Refunds calls this; it never reaches into _shipments directly.
    if order_id not in _shipments:
        raise KeyError(f"no shipment for order {order_id}")
    _shipments[order_id]["reversed"] = True
    return True


if __name__ == "__main__":
    refund = Refund(order_id="order-42", amount=1999)
    approved = approve_refund(refund, reverse_shipment)
    print("refund approved:", approved, "shipment reversed:", _shipments["order-42"]["reversed"])
```

All three samples were run in this session. `go run` printed
`refund approved, shipment reversed: true`. `node` after `npx tsc` compiling
the TypeScript sample printed `refund approved: true`. `python3` printed
`refund approved: True shipment reversed: True`. A Java sample was not
attempted because no Java runtime was present in the environment used to write
this entry, `javac` reported it could not locate one, and this entry states
that plainly rather than presenting an unrun sample as verified.
