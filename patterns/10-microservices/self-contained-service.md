---
name: Self-Contained Service
slug: self-contained-service
family: 10-microservices
category: Structural
aliases: [Self-Contained System, SCS, Vertical Slice Service]
first_described: "Self-Contained Systems community, self-contained-systems.org, first published guidance circa 2015; Newman 2021 discusses the same shape under service boundary design"
maturity: established
related: [decompose-by-business-capability, decompose-by-subdomain, backends-for-frontends, api-gateway, database-per-service, saga]
incompatible_with: [shared-database]
verified: 2026-08-03
---

# Self-Contained Service

## 1. Name, aliases, and lineage

The canonical name in the wider literature is Self-Contained System, abbreviated
SCS, and the pattern catalog in this repository uses the service-scoped name
Self-Contained Service to keep it alongside the other 10-microservices entries
that describe a single service's shape rather than a whole-system architecture.
The two names describe the same structural idea at two different scopes. an SCS
is a self-contained service that also owns its own user interface and is meant
to be deployed and operated as a complete, independently releasable unit within
a larger system made of several such units.

The name and its defining rules were published by a group of German
practitioners, most visibly Eberhard Wolff and Stefan Tilkov, on the site
self-contained-systems.org, which lists eight defining characteristics. each
SCS is an autonomous web application, it owns its data exclusively, it can
operate without depending synchronously on other systems at request time, it
is one deployment unit per team, communication with other SCSs happens
asynchronously where possible, UI integration happens for old-style
server-rendered content across systems rather than only via a single unifying
frontend, and each SCS should be a natural fit for one autonomous team
([self-contained-systems.org, "Characteristics"](https://scs-architecture.org/),
verified 2026-08-03). The community's own site draws an explicit comparison to microservices and
states plainly that the SCS approach can be combined with finer-grained
microservices, and elsewhere in the wider SCS community's public talks and
writing (Stefan Tilkov and Eberhard Wolff, in conference talks associated with
the site) the discipline is described as predating the word microservice and
adding a UI-ownership requirement microservices alone do not carry
([scs-architecture.org, FAQ page](https://scs-architecture.org/faq.html),
verified 2026-08-03, page content confirmed live but the specific comparative
framing is reported here as community discourse around the site rather than a
single verbatim quoted sentence from this exact page).

Sam Newman, in *Building Microservices*, 2nd edition, O'Reilly, 2021, does not
use the SCS name but describes the same underlying structural commitment under
the heading of service boundaries aligned to business capability, arguing that
a service boundary drawn around a business capability, and not around a
technical layer such as "the UI layer" or "the database layer", is what lets a
team release independently without coordinating a lockstep deploy across
layers (Newman, chapter 1, "What Is a Microservice", and chapter 2, "How to
Model Microservices"). The SCS community's own writing credits the same
underlying motivation, decoupling deployability from a shared UI or a shared
data layer, and cites the earlier "Vertical Slice" and "Bounded Context"
framing from Eric Evans, *Domain-Driven Design*, Addison-Wesley, 2003, as the
domain-modeling ancestor of the idea, since a bounded context is exactly the
kind of boundary an SCS is meant to make deployable
([self-contained-systems.org, "History"](https://scs-architecture.org/faq.html),
verified 2026-08-03).

The alias Vertical Slice Service is used in this entry, and elsewhere in
practitioner writing, to describe the same shape informally, emphasizing that
the service cuts vertically through every layer of the stack, UI, business
logic, and data, for one piece of business capability, rather than
horizontally through one layer for the whole system.

## 2. Problem and context

A team owns a piece of business capability end to end, say "product catalog"
or "checkout" or "order history", and wants to release a change to that
capability without asking three other teams to release in lockstep. In a
layered architecture, "checkout" is spread across a shared frontend
application, a shared backend-for-frontend layer, a shared checkout
microservice, and a shared database, and a change to checkout's UI, business
logic, or schema forces a coordinated deploy across whichever of those shared
layers it touches.

The context in which this becomes acute is a multi-team organization building
one customer-facing product where the UI is currently a single monolithic
frontend that every team contributes screens to, and the release cadence of
the frontend has become the release cadence of the whole company, because a
change from any team can break the shared frontend build, and a broken
frontend build blocks every other team's release too. This is the
well-documented frontend-monolith failure mode. backend services decompose
cleanly along team lines, but the UI stays a single deployable artifact, and
the coordination cost that microservices were meant to remove at the backend
reappears at the frontend layer. The SCS community names this directly as
their founding motivation, arguing that decomposing only the backend into
microservices while keeping one shared frontend just moves the coupling
problem up a layer rather than removing it
([self-contained-systems.org, "Motivation"](https://scs-architecture.org/faq.html),
verified 2026-08-03).

Self-Contained Service answers this by drawing the service boundary around a
full vertical slice, UI included, so that "checkout" is one deployable unit
that renders its own screens, holds its own logic, and owns its own data
store, and a checkout release touches nothing that another team's slice
depends on at deploy time.

## 3. Forces

**Deployability versus consistent user experience.** Giving each service its
own UI means each team can ship on its own schedule, but a person moving
between two SCSs may see two different visual styles, two different loading
behaviors, or two different session models unless the organization invests
separately in a shared design system and shared conventions that are
versioned and adopted, not enforced by a single shared codebase.

**Team autonomy versus duplicate infrastructure.** Each SCS is meant to build,
test, and deploy without coordinating with another SCS's team at request time,
which means each SCS typically needs its own build pipeline, its own hosting,
its own monitoring dashboards, and often its own authentication integration
code, even when that infrastructure is nearly identical across SCSs. The SCS
community's own writing acknowledges this cost and argues that duplicated
infrastructure code is a lesser cost than shared code that couples releases,
but this is a judgment call, not a settled fact, and teams with small
headcounts feel the duplication cost more acutely than the coupling cost it
avoids.

**Data ownership versus cross-cutting queries.** Each SCS owns its data
exclusively and other SCSs must not read that data store directly. This
removes the tight coupling a shared database creates, but it means a query
that spans two business capabilities, "show a customer their orders and their
support tickets on one page", cannot be a single database join anymore and
must be assembled either by an aggregating UI shell, by asynchronous data
replication into a read model, or by a runtime call between SCSs, each of
which carries the classic Saga or CQRS trade-off described in the related
patterns dimension below.

**Synchronous coupling versus response completeness.** SCS strongly favors
asynchronous communication between systems and treats an SCS that must call
another SCS synchronously to answer its own screen as a design smell, because
a synchronous call at request time reintroduces exactly the availability
coupling SCS exists to remove. In practice most systems cannot fully avoid
this, so the honest engineering position is minimizing synchronous cross-SCS
calls, not eliminating them, and treating any that remain as a deliberately
accepted exception with a timeout and a fallback.

**Operational uniformity versus operational independence.** A platform team
wants every service instrumented the same way, deployed through the same
pipeline shape, and secured the same way, while an SCS team wants the freedom
to pick its own language, framework, and release cadence. SCS favors
independence and treats a shared framework mandate as a violation of the
one-team-per-system rule, but this trades away the economy of scale a
platform team gets from a single golden path.

## 4. Applicability and non-applicability

Reach for Self-Contained Service when the following hold together, not
individually.

- The organization has multiple product teams that each own a distinct,
  user-facing piece of business capability, and those teams currently share a
  single frontend codebase that has become a release bottleneck.
- The business capabilities being split are large enough, and used
  independently enough by end users, that giving each one its own UI screens
  is a net win rather than a fragmentation of a workflow the user experiences
  as one continuous task.
- The organization is willing to invest in a shared design system, a shared
  authentication and session convention, and a UI-composition layer
  (server-side includes, edge-side includes, or a client-side shell) so that
  independently built SCS UIs still feel like one product to the end user.
- Team boundaries can realistically be drawn one-to-one, or close to it, with
  service boundaries, so that "who owns this SCS" has one unambiguous answer.

Do not reach for Self-Contained Service in these situations.

- **A single small team builds the whole product.** SCS solves a multi-team
  coordination problem. A single team gains nothing from splitting its own UI
  into several independently deployed UI fragments and pays the integration
  cost for no benefit, which follows directly from the site's own
  characteristics list requiring one team per system, since a single team has
  no second team to decouple from
  ([scs-architecture.org, "Characteristics"](https://scs-architecture.org/),
  verified 2026-08-03).
- **The user-facing workflow is a single, tightly interleaved task that
  genuinely spans several business capabilities on one screen**, for example
  a live checkout flow that must show inventory, pricing, and payment status
  in one continuously updating view. Splitting that screen across
  independently deployed SCS fragments adds integration latency and failure
  surface to a flow where the user experiences it as one atomic interaction,
  and a backend-for-frontend aggregating a single API is usually the better
  fit.
- **The product has no meaningful UI**, for example a pure backend API
  product, a data pipeline, or an internal batch job. SCS's defining
  characteristic is UI ownership. a service with no UI is better described by
  a plain service-per-business-capability decomposition, not SCS.
- **Regulatory or data-residency requirements force a single audited data
  store for a class of records.** SCS's exclusive-data-ownership rule
  conflicts directly with a compliance requirement for one queryable system
  of record across a whole domain, and forcing SCS onto that requirement
  produces either a compliance failure or a covert shared database that
  violates the pattern in practice while claiming to follow it on paper.
- **The team lacks the platform maturity to run several independently
  deployed UI fragments in production**, meaning no shared observability
  convention, no shared authentication library, and no established
  UI-composition mechanism. Adopting SCS before that maturity exists tends to
  produce several inconsistent, hard-to-debug UI fragments rather than the
  intended autonomy.

## 5. Structure

- **Self-Contained Service.** One deployment unit that includes a web-facing
  UI layer (its own rendered screens, or its own fragment contributed into a
  composed page), a business logic layer implementing one coherent business
  capability, and a private data store that no other SCS reads or writes
  directly. Owned end to end by one team.
- **UI composition layer.** A mechanism, separate from any single SCS, that
  assembles fragments from multiple SCSs into a coherent page for the end
  user. This can be server-side includes at an edge or reverse-proxy layer,
  edge-side includes, a client-side shell that fetches and mounts fragments,
  or simple hyperlinking between full-page SCS applications, a set of
  integration mechanisms discussed across the SCS community's public writing
  and talks associated with the site
  ([scs-architecture.org](https://scs-architecture.org/), verified 2026-08-03,
  the mechanisms themselves are reported here as engineering judgement drawn
  from the wider SCS community discourse, not a single verbatim page quote).
- **Asynchronous integration channel.** An event bus, message queue, or
  scheduled batch replication mechanism used when one SCS needs data that
  another SCS owns, avoiding a synchronous request-time dependency between
  the two.
- **Private data store.** A database instance, schema, or storage bucket that
  belongs to exactly one SCS. Never shared, never queried directly by another
  SCS's code.
- **Shared design system, external to any single SCS.** A published,
  versioned set of visual components, style tokens, and interaction
  conventions that each SCS's UI layer consumes so that independently
  deployed fragments still read as one product.
- **Identity and session provider, external to any single SCS.** A shared
  authentication mechanism, typically a token-based scheme such as OpenID
  Connect, that every SCS trusts without needing to call a central session
  service synchronously on every request.

## 6. ASCII structure diagram

```
+-----------------------------------------------------------------+
|                     UI Composition Layer                        |
|         (edge includes, or plain hyperlinks between SCSs)       |
+-----------------------------------------------------------------+
        |                     |                     |
        v                     v                     v
+---------------+   +----------------+   +----------------------+
| SCS: Catalog  |   | SCS: Checkout  |   | SCS: Order History   |
| Team A        |   | Team B         |   | Team C                |
|               |   |                |   |                       |
| +-----------+ |   | +------------+ |   | +-------------------+ |
| |  UI/Views | |   | |  UI/Views  | |   | |  UI/Views         | |
| +-----------+ |   | +------------+ |   | +-------------------+ |
| +-----------+ |   | +------------+ |   | +-------------------+ |
| |  Logic    | |   | |  Logic     | |   | |  Logic            | |
| +-----------+ |   | +------------+ |   | +-------------------+ |
| +-----------+ |   | +------------+ |   | +-------------------+ |
| | Own Data  | |   | | Own Data   | |   | | Own Data          | |
| +-----------+ |   | +------------+ |   | +-------------------+ |
+---------------+   +----------------+   +----------------------+
        |                     |                     ^
        |     async events    |     async events     |
        +---------------------+----------------------+
                          Event Bus

     Shared, external to every SCS, consumed not owned by any one.
     - Design System (versioned components and style tokens)
     - Identity Provider (token issuance, trusted by every SCS)
```

No arrow runs from one SCS's data store into another SCS's process. Every
cross-SCS arrow is either through the UI composition layer, at rendering
time, or through the asynchronous event bus, never a synchronous service call
reading another SCS's private storage.

## 7. Dynamics

The common runtime path for a user request that stays inside one SCS.

```
Browser -> UI Composition Layer -> (route to owning SCS)
   Catalog SCS receives request
     -> Catalog SCS UI layer renders response
        -> Catalog SCS logic layer queries Catalog SCS's own database
     <- HTML or fragment returned
   <- UI Composition Layer returns page (or forwards fragment) to Browser
```

The path for a composed page spanning two SCSs, using server-side or
edge-side inclusion.

```
Browser requests "My Account" page
  -> UI Composition Layer fetches
       fragment A from Order History SCS  (its own render, its own data)
       fragment B from Loyalty Points SCS (its own render, its own data)
  -> UI Composition Layer assembles A + B into one HTML response
  <- Browser receives one page; each fragment was rendered independently
```

The path for data that one SCS needs but another SCS owns, kept
asynchronous.

```
Checkout SCS. order placed
  -> publishes OrderPlaced event to Event Bus
       (Checkout SCS does not know or care who consumes this)

Order History SCS. subscribed to OrderPlaced
  -> consumes event asynchronously
  -> writes a denormalized copy into its own private data store

Later. Order History SCS renders "your orders" page
  -> reads only its own local copy, no runtime call to Checkout SCS
```

The deliberate cost visible in the last diagram. Order History SCS holds a
denormalized, eventually consistent copy of order data it does not own, and
must reconcile the case where its local copy is stale relative to Checkout
SCS's system of record, which is the same eventual-consistency trade-off
described in the CQRS and event-driven-architecture entries elsewhere in this
catalog.

## 8. Implementation variants

**Full-page SCS with hyperlink integration.** Each SCS serves complete HTML
pages, and cross-SCS routing is a plain anchor tag pointing at another SCS's
URL. This is the variant the SCS community itself calls the simplest and
recommends starting with, because it requires no shared rendering
infrastructure at all, only a shared visual language so the pages feel
consistent, a preference reflected in the site's emphasis on the UI as the
primary integration surface
([scs-architecture.org](https://scs-architecture.org/), verified 2026-08-03).
The visible cost is a full page reload on every
cross-SCS link, which some products treat as an acceptable trade for
independence and others treat as an unacceptable UX regression from a
single-page-application feel.

**Server-side or edge-side include composition.** A reverse proxy or edge
layer, for example an Nginx SSI configuration, an edge-side-includes-capable
CDN, or a purpose-built composition gateway, fetches HTML fragments from
several SCSs at request time and assembles them into one response before the
browser ever sees a request boundary. This preserves the "one page" feel
while keeping each SCS's rendering independent.

**Client-side fragment mounting, micro-frontends.** Each SCS exposes a
JavaScript entry point that a thin shell application loads and mounts into a
region of the page at runtime, commonly using Webpack Module Federation or a
similar dynamic-loading mechanism. This is the variant most associated with
the broader micro-frontends label, and it trades server-side simplicity for a
single-page-application feel, at the cost of a more complex build and
versioning story for the shared shell.

**Asynchronous-only backend integration with a single unified UI shell.**
Some teams adopt the backend half of SCS, exclusive data ownership per
service and asynchronous cross-service communication, while keeping one
shared UI shell that calls into each service's API. This is a partial
adoption. the SCS community does not endorse it as "true SCS" because it
fails the UI-ownership characteristic, but it is common enough in practice
that it is worth naming as a variant, and it is closer to plain
decompose-by-business-capability than to full SCS.

## 9. Known production uses

- **OTTO (otto.de), the German online retailer, is widely reported in SCS
  community talks and writing (Wolff and Tilkov, the practitioners who
  published the SCS characteristics) as an early adopter that restructured
  its platform into independently deployable systems, each owning its own UI
  and data.** The site defining the pattern's eight characteristics that
  OTTO's engineering is reported to have adopted resolves live and was
  independently confirmed
  ([scs-architecture.org, "Characteristics"](https://scs-architecture.org/),
  verified 2026-08-03); the OTTO-specific case study text itself could not be
  independently located at a stable URL during this session and is reported
  here as community-attested rather than directly quoted.
- **Zalando, the European e-commerce company, organizes its engineering so
  that small teams own, deploy, and operate their own services end to end**,
  which is the team-ownership and independent-deployability half of SCS's
  definition applied at Zalando's scale, as Zalando's own published API
  guidelines state directly. "Small engineering teams own, deploy and operate
  these microservices in their (team) accounts"
  ([opensource.zalando.com, RESTful API Guidelines, "Introduction"](https://opensource.zalando.com/restful-api-guidelines/),
  verified 2026-08-03).
- **SoundCloud is a well-documented early production case of decomposing a
  monolith into small, independently deployable, bounded-context-aligned
  services**, the boundary-drawing discipline that a Self-Contained Service
  extends by additionally requiring each service to own its own UI. "In this
  style, engineers separate domain logic into very small components. These
  components expose a well-defined API, and implement a Bounded Context"
  ([SoundCloud Backstage Blog, "Building Products at SoundCloud, Part I"](https://developers.soundcloud.com/blog/building-products-at-soundcloud-part-1-dealing-with-the-monolith),
  verified 2026-08-03). SoundCloud's own account does not describe its
  services as additionally owning their own UI in the SCS sense, so this
  entry cites it as evidence for the backend-boundary half of the pattern
  only, consistent with the "Asynchronous-only backend integration" variant
  named in dimension 8, not as a claim that SoundCloud runs full SCS.

Because the underlying structural idea, a fully vertical, UI-inclusive,
team-owned service, predates and overlaps with the broader micro-frontends
movement, the reader should also treat the well-documented micro-frontends
adopters, companies composing independently deployed UI fragments per team,
as adjacent evidence for the same structural forces, while noting that not
every micro-frontends adopter satisfies the SCS community's stricter,
asynchronous-first, no-shared-database definition.

## 10. Consequences

Positive.

- Each team can release its full vertical slice, UI, logic, and data schema,
  on its own schedule, without a cross-team deploy coordination meeting,
  because no other team's build depends on this team's UI code compiling.
- A production incident inside one SCS's business logic or database, in the
  common case, degrades only that SCS's screens rather than bringing down the
  whole product, because there is no shared runtime process or shared
  database connection pool for a bug to exhaust across SCSs.
- New team members can hold the whole vertical slice for their business
  capability in their head, UI to database, because it lives in one
  repository or a small, coherent set of repositories, rather than being
  spread across a shared frontend repo, a shared backend-for-frontend repo,
  and a shared backend service repo.
- Technology choice per SCS is genuinely free. one team's SCS can be a
  server-rendered application in one language while another team's SCS is a
  single-page application in a different language, because no shared build
  tool or shared runtime couples them.

Negative.

- Duplicated cross-cutting concerns. authentication integration, logging
  setup, error-page styling, and CI pipeline configuration are typically
  reimplemented per SCS rather than written once, unless the organization
  invests separately in shared libraries or scaffolding templates that are
  themselves versioned and optionally adopted, never mandatorily shared
  code.
- The end-user experience risks visible seams, a slightly different loading
  spinner, a slightly different error page, or a full page reload where a
  single-page application would have transitioned smoothly, unless a shared
  design system is maintained with real discipline across every team.
- A workflow that a user experiences as one continuous task but that spans
  two SCSs, for example "browse the catalog, then check out", now crosses a
  real deployment and often a real page boundary, which can introduce a UX
  discontinuity that a single monolithic frontend would not have had.
- Operational surface area grows. more deployment pipelines, more monitoring
  dashboards, more on-call rotations to define, and more places a
  misconfigured header or a misconfigured cache policy can diverge from
  every other SCS's configuration.

## 11. Failure modes and misuse

- **Symptom.** Two SCSs quietly share a database instance for one query, and
  a migration in one SCS breaks the other SCS's queries with no warning at
  deploy time.
  **Cause.** A team under deadline pressure takes a shortcut, reading
  another SCS's tables directly instead of asking for an event feed or an
  API, because it is faster in the moment and the database is technically
  reachable.
  **Fix.** Enforce exclusive data ownership at the infrastructure layer,
  separate database credentials, separate network policy, or even separate
  database instances per SCS, so the shortcut is not merely discouraged but
  physically unavailable.

- **Symptom.** The shared design system drifts, and after six months the
  product looks like four different products stitched together.
  **Cause.** Each SCS team copies the design system's components once at
  adoption time and then never upgrades, because there is no mechanism to
  enforce or even measure design system version currency across
  independently deployed SCSs.
  **Fix.** Publish the design system as a versioned package with an
  explicit deprecation and support window, and track version currency per
  SCS on a shared dashboard, treating an out-of-date design system version
  as a defect the same way an out-of-date security-patched dependency is
  treated.

- **Symptom.** Page load time for a composed page silently doubles or
  triples after adding a new fragment, and nobody notices until a customer
  complains.
  **Cause.** Each SCS fragment is fetched serially by the composition
  layer, or each fragment's own render time has crept upward
  independently, and because no single team owns the composed page's
  end-to-end latency, no one is watching the aggregate number.
  **Fix.** Assign explicit ownership of the composed page's end-to-end
  latency budget to the team that owns the composition layer, fetch
  fragments in parallel where the composition mechanism allows it, and set
  a per-fragment timeout with a documented fallback, a cached last-good
  fragment or a graceful placeholder, so one slow SCS cannot stall the
  whole page.

- **Symptom.** A so-called self-contained service turns out to make three
  synchronous calls to other SCSs to render its own screen, and an outage
  in any one of those three takes this SCS down too.
  **Cause.** The team drew the service boundary around a UI screen without
  first checking whether the business logic behind that screen actually
  fits inside one bounded context, so the screen needs data that
  genuinely lives in another team's domain, and the team reached for a
  synchronous call as the path of least resistance rather than redesigning
  the boundary or accepting eventual consistency via an event feed.
  **Fix.** Revisit the domain boundary (see decompose-by-subdomain) before
  adding the synchronous call, and where a small amount of cross-domain
  data is genuinely needed, replicate a read-only copy into this SCS's own
  store via an asynchronous event, accepting eventual consistency, rather
  than calling out synchronously at request time.

- **Symptom.** Onboarding a new engineer takes weeks because
  self-contained in practice meant every SCS reinvented its own bespoke
  deployment pipeline, logging format, and configuration convention.
  **Cause.** Team autonomy was interpreted as license to diverge on every
  operational decision, not only on technology choice within the SCS's own
  business logic, so there is no shared operational vocabulary across the
  organization even though each SCS individually is well built.
  **Fix.** Separate what technology this SCS's business logic uses,
  genuinely free per SCS, from how this SCS is deployed, logged, and
  monitored, which is worth standardizing as a shared, strongly encouraged
  platform convention, distinct from a shared runtime library that would
  recouple releases.

## 12. Trade-off matrix

| Force | Self-Contained Service | Backends for Frontends | Decompose by Business Capability (backend only, shared UI) |
|---|---|---|---|
| Deploy independence, UI included | High. UI and logic and data release together, per team. | Medium. Backend releases independently, but the shared frontend still couples UI releases across teams. | Low. Backend services release independently, but the single shared frontend remains the release bottleneck. |
| Consistency of end-user experience | Requires deliberate investment in a shared design system, without it seams are visible. | High, because one frontend renders everything with one visual language by construction. | High, for the same reason as BFF. |
| Cross-capability workflow latency | Higher when a workflow spans two SCSs and must compose fragments or wait on eventual consistency. | Lower, because one BFF can aggregate several backend calls behind one API without a UI-composition step. | Similar to BFF at the API layer, but the frontend itself still assembles multiple API calls into one screen. |
| Team autonomy over technology choice | High, per SCS, UI included. | Medium. Backend teams choose freely, but the shared frontend constrains frontend technology choice organization-wide. | Medium, same constraint as BFF. |
| Operational surface area | Highest. Each SCS needs its own full pipeline, hosting, and monitoring, UI included. | Medium. One BFF per frontend plus N backend services. | Lowest of the three at the UI layer, since there is only one frontend to operate, though N backend services still exist. |
| Data ownership clarity | Highest. Exclusive ownership is a defining rule, enforced structurally. | Depends entirely on the backend services behind the BFF, BFF itself does not dictate this. | Depends on how the backend decomposition was drawn, not guaranteed by this pattern alone. |

## 13. Related and incompatible patterns

- **Decompose by Business Capability** and **Decompose by Subdomain** describe
  how to draw the boundary a Self-Contained Service occupies. SCS adds a
  requirement neither of those patterns requires on its own, that the
  boundary include the UI, not only the backend logic and data.
- **Backends for Frontends** is the pattern most often reached for instead of
  SCS when a team wants independent backend release cadence but is not
  ready, or does not want, to split the UI itself. A BFF composes multiple
  backend services behind one API for one shared frontend, which is a
  strictly different shape from SCS's per-capability UI ownership, and the
  two are not typically combined for the same slice of functionality, since
  combining them would mean the SCS's own UI calling through a BFF that also
  serves other UIs, reintroducing the shared-layer coupling SCS exists to
  avoid.
- **API Gateway** commonly sits in front of a set of SCSs for the small
  fraction of interactions that are genuinely API-to-API rather than
  browser-to-UI, for example a partner integration calling into the platform
  programmatically rather than through the composed web UI.
- **Database per Service** is a strict prerequisite for SCS's data-ownership
  rule. SCS can be described as Database per Service applied at the
  vertical-slice, UI-inclusive scope rather than at the plain backend-service
  scope.
- **Saga** and **CQRS**, event-driven read models, are the mechanisms an SCS
  reaches for when it needs data another SCS owns, since SCS forbids the
  synchronous cross-service query a shared database would otherwise make
  trivial, and both patterns describe how to accept eventual consistency
  deliberately rather than accidentally.
- **Incompatible, Shared Database.** SCS's defining rule of exclusive data
  ownership directly conflicts with the Shared Database pattern. A system
  that has two SCSs reading from one database instance has, by the
  self-contained-systems community's own definition, stopped being SCS,
  regardless of what the deployment topology otherwise looks like
  ([self-contained-systems.org, "Characteristics"](https://scs-architecture.org/),
  verified 2026-08-03).

## 14. Refactoring path in and out

Introducing SCS into a system that currently has a shared frontend monolith
and several backend microservices.

1. Identify one business capability whose screens are cleanly separable from
   the rest of the shared frontend, meaning a user rarely needs to see that
   capability's screens interleaved, on the same visible page, with another
   capability's screens. Order history is a common first candidate, since it
   is usually a self-contained read-mostly view.
2. Stand up a new deployable unit that owns that capability's UI rendering,
   moving the relevant screens out of the shared frontend and into the new
   service, alongside the backend logic and data that already exist, or
   moving the backend logic and data alongside the UI if they were
   previously separate services.
3. Introduce a minimal UI composition mechanism, starting with the simplest
   variant, a hyperlink from the old shared frontend into the new SCS's own
   pages, so the migration does not require solving fragment composition on
   day one.
4. Replace any synchronous call the new SCS was making into another team's
   service, to read data at request time, with an asynchronous event
   subscription and a locally owned, denormalized copy of that data.
5. Cut the old shared frontend's routes for that capability once the new
   SCS is serving production traffic and the team is confident in its
   independence, then repeat the process for the next capability.

Removing SCS, folding a vertical slice back into a shared frontend, is the
right move when a business capability turns out to be used so tightly
interleaved with another capability that the composition overhead is a
persistent UX cost with no offsetting deployment-independence benefit, most
commonly when the two capabilities are, in practice, always maintained and
released by the same team anyway.

1. Confirm the SCS genuinely has no independent release cadence in
   practice, by checking its deploy history against the team that would
   absorb it. if its releases already happen in lockstep with the
   absorbing team's releases, the independence SCS provides was not being
   used.
2. Move the SCS's UI templates or components into the absorbing shared
   frontend's codebase, adapting them to that frontend's composition
   mechanism.
3. Fold the SCS's private data store into the absorbing service's data
   layer, or leave it as an internally called service if the logic
   boundary still earns its place even after the UI boundary is removed,
   since dimension 4's applicability list, not this one, governs whether
   the underlying service boundary itself should also be removed.
4. Retire the SCS's independent deployment pipeline last, after traffic
   has been fully cut over and the merged frontend has run in production
   without the old fragment for a full release cycle.

## 15. Testing and verification

Testing a Self-Contained Service is, by design, closer to testing a small
standalone application than to testing one microservice in a larger backend
mesh, because the UI, logic, and data live together and can be exercised
together.

- Because each SCS owns its full stack, it can run a full end-to-end test
  suite, browser through database, entirely inside its own CI pipeline,
  without needing a shared staging environment that spins up every other
  SCS, which is a genuine testing advantage over a shared-frontend
  architecture where an end-to-end test of one capability requires the
  whole frontend build.
- What becomes harder is testing the composed experience across two or
  more SCSs, the assembled "My Account" page, since that composition
  happens at the UI composition layer, outside any single SCS's test
  suite. This needs a separate, thinner suite of composition tests, owned
  by whichever team owns the composition layer, asserting that each SCS's
  contract for its fragment, the HTML shape it promises to emit or the API
  shape a client-side shell expects, is honored, closer to a contract test
  than a full integration test.
- Consumer-driven contract testing is the applicable technique for the
  asynchronous event integration between SCSs. The consuming SCS publishes
  the shape of the event it expects, and the producing SCS's CI pipeline
  verifies its published events against every known consumer's contract
  before deploying a change to the event's shape, which is the same
  discipline described for asynchronous messaging integration in the
  broader microservices testing literature.
- A test double standing in for another SCS's fragment or event, in this
  SCS's own test suite, should be built from the actual published
  contract, not from an assumption about what the other SCS currently
  returns, so that a contract change on the other side is caught by a
  broken test locally rather than discovered in production.

## 16. Observability signals

- Per-SCS deploy frequency and lead time, tracked separately per service, is
  the most direct signal of whether the pattern is delivering its core
  promise. a set of SCSs whose deploy frequencies have converged to the same
  cadence as each other is a sign that hidden coupling has crept back in.
- Composed-page end-to-end latency, broken down by which fragment
  contributed how much of the total time, should be visible on one
  dashboard owned by the composition layer team, since no single SCS team
  can see this number from inside their own service's metrics alone.
- Per-fragment error rate and per-fragment timeout rate at the composition
  layer, so that a degrading SCS shows up as a localized problem, one
  fragment's error rate rising, rather than only as a vague rise in the
  composed page's overall failure rate.
- Event-consumer lag, for every SCS that subscribes to another SCS's
  events, because a growing lag is the earliest visible sign that an SCS's
  local, denormalized copy of another SCS's data is drifting stale, before
  any user actually notices incorrect data on screen.
- Design-system version currency per SCS, on a shared dashboard, since this
  is otherwise an invisible form of drift that only shows up as a visual
  inconsistency complaint from a user or a designer, well after the drift
  has already occurred.

A healthy fleet of SCSs shows independently varying deploy frequencies
(proof that teams are not coordinating releases), low and stable event-
consumer lag, and design-system versions clustered near the current
release. An unhealthy fleet shows deploy frequencies converging toward one
shared cadence, growing event lag on one or more consumers, and design-
system versions spread across many old releases.

## 17. Security and privacy implications

- Because each SCS owns its own authentication integration, a
  misconfiguration in any one SCS's session handling is a per-SCS attack
  surface, not a shared one, which is a genuine security benefit versus a
  single monolithic frontend where one session-handling bug affects every
  screen at once. The trade-off is that this same duplication means each
  SCS must be independently kept current on authentication library
  security patches, and a security team auditing session handling across
  the platform must now audit N implementations instead of one.
- Personal data replicated into an SCS's local, denormalized copy via the
  asynchronous event channel is a second, or third, or Nth, copy of that
  data at rest, which directly affects data-subject-access and
  data-deletion obligations under regimes such as GDPR. a deletion request
  must now be propagated as an event to every SCS holding a denormalized
  copy, and the system's deletion completeness depends on every subscriber
  correctly handling that deletion event, not on deleting one row in one
  shared table.
- The UI composition layer, when it fetches fragments from several SCSs at
  request time, is a natural point to enforce or accidentally weaken
  cross-origin and content-security-policy protections. a composed page
  that mixes fragments from multiple origins without a carefully designed
  content security policy can widen the cross-site-scripting attack
  surface compared to a single-origin monolithic frontend, and this must
  be designed deliberately rather than left to each SCS's own default.
- The event bus used for asynchronous cross-SCS integration becomes a
  shared piece of infrastructure that, if compromised, can leak or
  corrupt data flowing between multiple business domains at once, so the
  event bus itself typically warrants stronger access control and
  auditing than any single SCS's own internal logs, since it is the one
  place where data from every SCS's domain passes through in transit.

## 18. References

1. Self-Contained Systems community. "Characteristics."
   https://scs-architecture.org/ Verified 2026-08-03.
2. Self-Contained Systems community. "FAQ" (includes "How is an SCS different
   from a microservice", "When not to use SCS", "Integration Techniques",
   "History", "Motivation").
   https://scs-architecture.org/faq.html Verified 2026-08-03.
3. Self-Contained Systems community. "Case Studies" (lists organizations
   including OTTO's own architecture principles, alongside Phoenix Contact,
   Breuninger, Vorwerk Thermomix, Galeria Kaufhof, and Kühne+Nagel).
   https://scs-architecture.org/case-studies.html Verified 2026-08-03. The
   site restructured this page from its former examples.html path since the
   entries above were first drafted.
4. Sam Newman, *Building Microservices*, 2nd edition, O'Reilly, 2021, chapter
   1, "What Is a Microservice", and chapter 2, "How to Model Microservices".
5. Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
   Software*, Addison-Wesley, 2003, part IV, "Strategic Design" (bounded
   context, the domain-modeling ancestor of the SCS boundary).

## Code

What is worth demonstrating in code is not the whole web stack, it is the
shape of a service module that owns a private store no other module touches
directly, exposes its own rendering or response function rather than handing
raw data to a shared layer, and communicates with a peer service only through
a published event, never through a direct call into the peer's storage. The
three samples below model one SCS, Orders, publishing an event and a second
SCS, Loyalty, consuming it into its own private store, entirely decoupled
from Orders at read time.

### TypeScript

```typescript
type OrderPlacedEvent = { orderId: string; customerId: string; total: number };

class EventBus {
  private subscribers: Array<(e: OrderPlacedEvent) => void> = [];
  subscribe(handler: (e: OrderPlacedEvent) => void): void {
    this.subscribers.push(handler);
  }
  publish(event: OrderPlacedEvent): void {
    for (const handler of this.subscribers) handler(event);
  }
}

class OrdersService {
  private orders: Map<string, OrderPlacedEvent> = new Map();
  constructor(private bus: EventBus) {}
  placeOrder(orderId: string, customerId: string, total: number): void {
    const event = { orderId, customerId, total };
    this.orders.set(orderId, event);
    this.bus.publish(event);
  }
  renderReceipt(orderId: string): string {
    const order = this.orders.get(orderId);
    if (!order) return "Order not found.";
    return `Order ${order.orderId}, total ${order.total.toFixed(2)}.`;
  }
}

class LoyaltyService {
  private pointsByCustomer: Map<string, number> = new Map();
  constructor(bus: EventBus) {
    bus.subscribe((event) => this.onOrderPlaced(event));
  }
  private onOrderPlaced(event: OrderPlacedEvent): void {
    const earned = Math.floor(event.total);
    const current = this.pointsByCustomer.get(event.customerId) ?? 0;
    this.pointsByCustomer.set(event.customerId, current + earned);
  }
  renderPointsScreen(customerId: string): string {
    const points = this.pointsByCustomer.get(customerId) ?? 0;
    return `You have ${points} loyalty points.`;
  }
}

const bus = new EventBus();
const orders = new OrdersService(bus);
const loyalty = new LoyaltyService(bus);
orders.placeOrder("o-1", "c-42", 87.5);
console.log(orders.renderReceipt("o-1"));
console.log(loyalty.renderPointsScreen("c-42"));
```

### Python

```python
from dataclasses import dataclass
from typing import Callable
import math


@dataclass
class OrderPlacedEvent:
    order_id: str
    customer_id: str
    total: float


class EventBus:
    def __init__(self) -> None:
        self._subscribers: list[Callable[[OrderPlacedEvent], None]] = []

    def subscribe(self, handler: Callable[[OrderPlacedEvent], None]) -> None:
        self._subscribers.append(handler)

    def publish(self, event: OrderPlacedEvent) -> None:
        for handler in self._subscribers:
            handler(event)


class OrdersService:
    def __init__(self, bus: EventBus) -> None:
        self._bus = bus
        self._orders: dict[str, OrderPlacedEvent] = {}

    def place_order(self, order_id: str, customer_id: str, total: float) -> None:
        event = OrderPlacedEvent(order_id, customer_id, total)
        self._orders[order_id] = event
        self._bus.publish(event)

    def render_receipt(self, order_id: str) -> str:
        order = self._orders.get(order_id)
        if order is None:
            return "Order not found."
        return f"Order {order.order_id}, total {order.total:.2f}."


class LoyaltyService:
    def __init__(self, bus: EventBus) -> None:
        self._points_by_customer: dict[str, int] = {}
        bus.subscribe(self._on_order_placed)

    def _on_order_placed(self, event: OrderPlacedEvent) -> None:
        earned = math.floor(event.total)
        current = self._points_by_customer.get(event.customer_id, 0)
        self._points_by_customer[event.customer_id] = current + earned

    def render_points_screen(self, customer_id: str) -> str:
        points = self._points_by_customer.get(customer_id, 0)
        return f"You have {points} loyalty points."


if __name__ == "__main__":
    bus = EventBus()
    orders = OrdersService(bus)
    loyalty = LoyaltyService(bus)
    orders.place_order("o-1", "c-42", 87.5)
    print(orders.render_receipt("o-1"))
    print(loyalty.render_points_screen("c-42"))
```

### Go

```go
package main

import (
	"fmt"
	"math"
)

type OrderPlacedEvent struct {
	OrderID    string
	CustomerID string
	Total      float64
}

type EventBus struct {
	subscribers []func(OrderPlacedEvent)
}

func (b *EventBus) Subscribe(handler func(OrderPlacedEvent)) {
	b.subscribers = append(b.subscribers, handler)
}

func (b *EventBus) Publish(event OrderPlacedEvent) {
	for _, handler := range b.subscribers {
		handler(event)
	}
}

type OrdersService struct {
	bus    *EventBus
	orders map[string]OrderPlacedEvent
}

func NewOrdersService(bus *EventBus) *OrdersService {
	return &OrdersService{bus: bus, orders: make(map[string]OrderPlacedEvent)}
}

func (s *OrdersService) PlaceOrder(orderID, customerID string, total float64) {
	event := OrderPlacedEvent{OrderID: orderID, CustomerID: customerID, Total: total}
	s.orders[orderID] = event
	s.bus.Publish(event)
}

func (s *OrdersService) RenderReceipt(orderID string) string {
	order, ok := s.orders[orderID]
	if !ok {
		return "Order not found."
	}
	return fmt.Sprintf("Order %s, total %.2f.", order.OrderID, order.Total)
}

type LoyaltyService struct {
	pointsByCustomer map[string]int
}

func NewLoyaltyService(bus *EventBus) *LoyaltyService {
	svc := &LoyaltyService{pointsByCustomer: make(map[string]int)}
	bus.Subscribe(svc.onOrderPlaced)
	return svc
}

func (s *LoyaltyService) onOrderPlaced(event OrderPlacedEvent) {
	earned := int(math.Floor(event.Total))
	s.pointsByCustomer[event.CustomerID] += earned
}

func (s *LoyaltyService) RenderPointsScreen(customerID string) string {
	return fmt.Sprintf("You have %d loyalty points.", s.pointsByCustomer[customerID])
}

func main() {
	bus := &EventBus{}
	orders := NewOrdersService(bus)
	loyalty := NewLoyaltyService(bus)
	orders.PlaceOrder("o-1", "c-42", 87.5)
	fmt.Println(orders.RenderReceipt("o-1"))
	fmt.Println(loyalty.RenderPointsScreen("c-42"))
}
```

Java, Rust, and Swift are omitted from this entry's code samples. the pattern
is a structural, cross-service integration shape rather than a language
feature, and the three samples above already demonstrate the shape, private
storage, an event-driven boundary, no synchronous cross-service read, across
a dynamically typed language, a statically typed compiled language, and a
statically typed language with structural interfaces, which is enough
language diversity to show the pattern is not tied to any one type system or
runtime.
