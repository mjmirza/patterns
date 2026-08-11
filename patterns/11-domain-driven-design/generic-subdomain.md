---
name: Generic Subdomain
slug: generic-subdomain
family: 11-domain-driven-design
category: Strategic
aliases: [Generic Domain, Commodity Subdomain, Buy-not-Build Subdomain]
first_described: "Evans 2003"
maturity: canonical
related: [bounded-context, context-map, ubiquitous-language, anti-corruption-layer, core-domain]
incompatible_with: []
verified: 2026-08-02
---

# Generic Subdomain

## 1. Name, aliases, and lineage

The canonical name is Generic Subdomain, one of the three subdomain types in
the strategic half of Domain-Driven Design, alongside Core Domain and
Supporting Subdomain. The term originates with Eric Evans, *Domain-Driven
Design. Tackling Complexity in the Heart of Software*, Addison-Wesley, 2003,
chapter 15, "Distillation," in the section titled "Generic Subdomains," which
sits next to "Core Domain" and "Choosing the Core" in the same chapter
(confirmed against the chapter table of contents and section listing at
[domainlanguage.com DDD Reference](https://www.domainlanguage.com/wp-content/uploads/2016/05/DDD_Reference_2015-03.pdf)
and the archived manuscript listing at
[fabiofumarola.github.io](https://fabiofumarola.github.io/nosql/readingMaterial/Evans03.pdf),
verified 2026-08-02). Evans frames distillation as the discipline of pulling a
model apart so that what matters is not buried under what does not, and the
Generic Subdomain is the half of that split that does not matter to the
business even though it must still work.

Evans warns in the same section, under the heading "Generic Doesn't Mean
Reusable," that generic is a statement about competitive value, not about
whether the code happens to be technically reusable. A subdomain can be
generic and still be hard to build. Hard and unimportant are independent axes,
and conflating them is the single most common misreading of the term.

Vaughn Vernon gave the three-way split its modern, load-bearing shape.
*Implementing Domain-Driven Design*, Addison-Wesley, 2013, uses a single
running case study, a multitenant SaaS system called SaaSOvation, and splits
it into a Collaboration Context, the Core Domain, an agile project management
and team-collaboration product, and an Identity and Access Context, which the
book treats as generic, existing only because every multitenant product needs
users, roles, and tenants, and providing no competitive edge on its own
(confirmed via search of the book's chapter structure and the SaaSOvation case
study description, [O'Reilly listing for the book](https://www.oreilly.com/library/view/implementing-domain-driven-design/9780133039900/),
verified 2026-08-02). Vernon's *Domain-Driven Design Distilled*, Addison-Wesley,
2016, restates the same three-way split, Core, Supporting, Generic, as the
first strategic decision a team makes before any tactical modeling starts.

Vladik Khononov's *Learning Domain-Driven Design*, O'Reilly, 2021, chapter 1,
"Analyzing Business Domains," gives the classification the sharpest modern
statement, defining a generic subdomain as work that is "not special" to the
business, is solved the same way by every company that needs it, and is a
strong candidate for buying an existing product rather than writing one
(confirmed against the chapter's stated content and structure via search of
the O'Reilly table of contents, verified 2026-08-02). Khononov's phrasing, buy
first, build only what is truly core, has become the working shorthand the
DDD community uses when the formal Evans and Vernon definitions are too dense
for a planning meeting.

No serious source disputes the name or the three-way split today. The
disagreement that does exist, covered under dimension 11, is about where the
line between Generic and Supporting actually falls in a specific system, which
is a classification dispute, not a naming dispute.

## 2. Problem and context

A team building a real product spends real engineering time on things the
business does not actually compete on. User authentication, password reset,
audit logging, PDF generation, currency conversion, address validation, email
delivery, SMS delivery. Every one of these is a genuine engineering problem
with edge cases, security implications, and operational cost, and every one of
them is, from the business's point of view, identical to the version every
other company in the same problem space also needs.

The failure this pattern exists to prevent shows up in a specific, recognizable
shape. A team is under a delivery deadline. The thing that actually
differentiates the product, the pricing engine, the matching algorithm, the
recommendation logic, is genuinely hard and genuinely novel, so it absorbs the
senior engineers' full attention. Meanwhile someone spends three sprints
building a password-reset flow with the correct token expiry, the correct
rate limiting, the correct email templating, and the correct handling of a
user who requests five resets in a row, because nobody explicitly decided that
authentication was out of scope for custom engineering. The three sprints did
not make the product better. They made it later, and the resulting
home-grown authentication system is now a permanent maintenance and security
liability that a specialist vendor would have carried for a monthly fee.

The context in which the pattern applies is any system whose scope includes
capabilities that recur, unmodified in their basic shape, across many
unrelated businesses. The pattern does not apply, and actively misleads, when
a capability looks generic on the surface but the way a specific business
performs it is the actual source of its advantage. Evans's own caution, generic
does not mean reusable, is really a caution against the opposite mistake too.
a capability can look boring and still be core, if the business lives or dies
by doing it slightly better than everyone else.

A second, quieter version of the same problem appears once a system has
several bounded contexts and each one independently reinvents the same
generic capability. Two teams each build their own password-reset flow, each
with its own bugs, because nobody drew a system-wide line between what is
generic and what is not. The Generic Subdomain classification is as much an
organizational coordination tool as it is a modeling tool. Once a capability
is labeled Generic anywhere in the system, the default expectation becomes
that every other context reuses the same integration rather than building a
sibling of its own.

## 3. Forces

**Engineering attention versus scope breadth.** Every hour spent on a generic
capability is an hour not spent on the capability that actually earns revenue
or defends market position. The pattern exists to protect scarce senior
attention for the parts of the system that repay it.

**Vendor risk versus build risk.** Buying introduces a dependency on a
third party's roadmap, pricing, uptime, and continued existence. Building
introduces the cost of ongoing maintenance, security patching, and the
opportunity cost of the people doing that maintenance instead of something
else. Neither risk is zero, and the pattern is a bet that vendor risk on a
commodity capability is smaller than the compounding cost of maintaining a
bespoke version of the same commodity capability forever.

**Integration friction versus modeling purity.** A bought generic subdomain
rarely maps cleanly onto the rest of the domain model. It comes with its own
vocabulary, its own object shapes, its own failure modes. Absorbing it cleanly
usually needs a translation layer, which is itself work, so the pattern only
pays off when the translation cost is smaller than the build-and-maintain
cost it replaces.

**Data gravity and lock-in versus speed to market.** A generic subdomain that
holds identity, payment, or communication data accumulates data gravity. Once
years of user history live inside a vendor's system, migrating away is
expensive regardless of how the integration was designed. The pattern trades
early speed for a later switching cost that grows over time.

**Compliance transfer versus compliance ownership.** Regulated capabilities,
payment card handling, identity verification, health data storage, carry
compliance obligations such as PCI DSS, KYC, and HIPAA, depending on
jurisdiction. Buying a specialist generic-subdomain vendor for one of these
usually transfers a meaningful share of that compliance burden to a party
whose entire business model depends on carrying it correctly. Building it
in-house means the team carries the full weight of the audit.

**Team topology versus system topology.** A generic subdomain integration
usually needs only a small, thin team, sometimes a single engineer, to own the
adapter and the vendor relationship. A Core Domain usually needs a dedicated,
long-lived team that can hold the domain's complexity in their heads. Getting
this allocation wrong shows up as Conway's Law working against the system.
a team accidentally structured around the generic capability starves the
actual Core Domain of the staffing depth it needs, while a team over-invested
in the generic integration has nothing left to do once the adapter is stable
and either stagnates or starts adding unwanted richness to compensate.

The pattern favors focus, speed, and compliance transfer. It sacrifices some
control, accepts an ongoing vendor dependency, and accepts an integration
tax at the boundary. A team that cannot tolerate any of those three
sacrifices is not ready to apply it, and should re-examine whether the
capability is really generic for their business.

## 4. Applicability and non-applicability

**Reach for it when.**

- The capability is solved the same way by every company that needs it, and
  a specific competitor doing it slightly worse than you would not move any
  customer's buying decision. Authentication, transactional email delivery,
  SMS delivery, PDF rendering, address validation, tax rate lookup, and
  currency conversion are the recurring textbook examples across Evans,
  Vernon, and Khononov.
- A mature, well-supported product or open-source project already implements
  the capability to a standard your team could not realistically match with
  the engineering budget available.
- The team's competitive advantage lies elsewhere, and every hour spent on
  this capability is an hour of opportunity cost against the Core Domain.
- The capability carries meaningful regulatory or security weight, such as
  payment card data or identity verification, that a specialist vendor is
  better positioned to carry than a small in-house team.

**Do NOT reach for it when.**

- The capability looks generic on the surface but the business's specific way
  of doing it is the actual differentiator. A logistics company's route
  planning looks like a commodity optimization problem until you notice that
  beating the market on route efficiency is the entire business model, at
  which point it is Core, not Generic. Khononov makes exactly this argument
  using Uber's routing as an example of a capability that looks generic and
  is not, per the search-confirmed content of *Learning Domain-Driven
  Design*, chapter 1, verified 2026-08-02.
- No vendor or open-source project actually exists at the maturity the
  business needs. A capability being conceptually generic does not guarantee
  a market has formed to serve it. In that case it becomes an unplanned
  Supporting Subdomain, built in-house but without the investment level of a
  Core Domain, until the market catches up.
- The switching cost of a wrong vendor choice is existential, for example a
  very early-stage startup betting its entire identity layer on a vendor
  whose pricing model would bankrupt the company at ten times its current
  scale. The generic classification is still correct, but the specific
  vendor decision needs its own risk analysis.
- The integration surface required to absorb the generic subdomain cleanly
  would itself require a translation layer more complex than the capability
  being replaced. This is rare but does happen with legacy systems that have
  deeply entangled identity concepts throughout the domain model, where a
  clean anti-corruption layer is not actually cheap to build.
- A regulator or a contractual clause explicitly requires the capability to
  be operated in-house, which overrides the classification regardless of how
  generic the capability would otherwise be.

## 5. Structure

A Generic Subdomain is not a code-level structural pattern the way a GoF
pattern is. It is a strategic classification applied to a Bounded Context, see
`bounded-context.md`, and its structure describes how that context relates to
the rest of the system, not what happens inside it.

**Participants.**

- **The Generic Subdomain itself.** A Bounded Context, either an external
  vendor product or an internally maintained module, that solves a
  capability the business needs but does not differentiate on. It has its own
  model, which the rest of the system does not need to understand in detail.
- **The consuming Bounded Contexts.** One or more contexts, usually including
  the Core Domain, that need the generic capability but should not absorb its
  vocabulary or its failure modes directly into their own model.
- **The integration boundary.** A translation layer, most often an
  Anti-Corruption Layer or an Open Host Service with a Published Language, see
  `context-map.md` for the full catalog of integration patterns, that
  converts between the generic subdomain's model and the consuming context's
  own ubiquitous language.
- **The Context Map entry.** The documented relationship between the generic
  subdomain and each of its consumers, recording which side has upstream
  power, whether the relationship is Customer or Supplier, Conformist, or
  Anti-Corruption Layer, and who owns the translation.

The critical structural decision the pattern drives is investment
allocation, not code shape. Vernon's advice, echoed by Khononov, is to give a
Core Domain a rich, expressive model with a dedicated team, to give a
Supporting Subdomain a competent but plain model, and to give a Generic
Subdomain the thinnest integration layer that correctly isolates it, because
any richness invested inside the generic subdomain's own model is richness
the business will never be paid for.

## 6. ASCII structure diagram

```
+-------------------------------------------------------------+
|                     The whole system                        |
|                                                               |
|   +----------------------+     +---------------------------+|
|   |  Core Domain          |    |  Generic Subdomain          |
|   |  (rich model,          |    |  (thin or bought,           |
|   |   dedicated team,     |    |   Identity, Payments,        |
|   |   deep investment)     |    |   Email, PDF rendering)      |
|   |                        |    |                             |
|   |  AccountRegistration   |--->|  IdentityProvider (port)     |
|   |  PricingEngine         |    |  PaymentGateway (port)       |
|   +-----------+------------+    +---------------+-------------+
|               |                                 |
|               v                                 v
|   +------------------------+       +--------------------------+
|   | Anti-Corruption Layer  |       | Vendor adapter            |
|   | translates vendor      |<------| Auth0Adapter, StripeAdapter|
|   | shapes into the        |       | implements the port,       |
|   | ubiquitous language    |       | calls the external API     |
|   +------------------------+       +--------------------------+
|                                                               |
+-------------------------------------------------------------+
                          |
                          v
              +---------------------------+
              | External vendor or         |
              | standalone service         |
              | Auth0, Okta, Stripe,       |
              | SendGrid, an internal      |
              | commodity module           |
              +---------------------------+
```

## 7. Dynamics

The runtime dynamics of a Generic Subdomain are, deliberately, unremarkable.
The pattern's whole point is that nothing interesting should happen inside it
from the Core Domain's perspective. What matters is the sequence at the
boundary.

```
Core Domain            Port (interface)      Adapter               Vendor
    |                        |                   |                    |
    | register(user, token)  |                   |                    |
    |----------------------->|                   |                    |
    |                        | verifyToken(token) |                    |
    |                        |------------------>|                    |
    |                        |                   | POST /oauth/verify |
    |                        |                   |------------------->|
    |                        |                   |                    | validates,
    |                        |                   |                    | returns claims
    |                        |                   | 200 sub, email      |
    |                        |                   |<--------------------
    |                        | Claims{...}       |                    |
    |                        |<------------------|                    |
    | Claims translated into |                   |                    |
    | the Core Domain's own  |                   |                    |
    | AccountIdentity value  |                   |                    |
    |<-----------------------|                   |                    |
    |                        |                   |                    |
    | continue registration  |                   |                    |
    | using AccountIdentity, |                   |                    |
    | never Auth0's raw JWT  |                   |                    |
    | claims shape           |                   |                    |
```

The two properties that matter in this flow. The Core Domain code never
imports a vendor SDK type directly, only the port, and any vendor-specific
error, rate limit, or outage surfaces at the adapter boundary as a domain-level
failure the Core Domain already knows how to handle, rather than leaking a
vendor exception type up through business logic.

## 8. Implementation variants

- **Pure buy, thin adapter.** The generic subdomain is entirely a third-party
  SaaS product such as Auth0, Okta, Stripe, or SendGrid. The team writes only
  a narrow adapter implementing a domain-owned port. This is the cheapest and
  most common variant and is the one Khononov and Vernon both recommend as the
  default.
- **Open-source, self-hosted.** The team runs an open-source implementation of
  the generic capability, for example Keycloak for identity or a self-hosted
  mail transfer agent, to satisfy a data-residency or cost constraint that
  rules out SaaS. The classification stays Generic even though the team now
  operates the software, because the modeling investment is still deliberately
  shallow. Only the operational burden changed.
- **Internal shared platform team.** In a large organization, a platform team
  builds and operates the generic capability once, centrally, and exposes it
  to every product team as an internal service. This is common for identity
  and notifications inside companies past a certain scale, and functions as an
  internally-vendored version of the buy strategy. Product teams still treat
  it as a thin, bought-in dependency behind a port, without paying an
  external invoice for it.
- **Published Language integration.** When the vendor or internal platform
  publishes a well-documented API contract, an OpenAPI schema or a stable
  webhook schema, the team can rely on a thinner Anti-Corruption Layer because
  the vendor's published shape is already close to a domain-neutral
  representation. See `context-map.md` for the Open Host Service and
  Published Language patterns this variant depends on.
- **Cohesive Mechanism.** Evans distinguishes Generic Subdomain from what he
  calls a Cohesive Mechanism, a generic, reusable algorithmic capability such
  as a constraint solver or a specialized search algorithm, that is generic in
  the sense of being domain-agnostic but is still built and owned in-house
  because it is elaborate enough to deserve its own careful model, distinct
  from both the Core Domain's business logic and a bought commodity service.
  This is confirmed against the chapter 15 section list, "Generic Subdomain
  Versus Cohesive Mechanism," at
  [domainlanguage.com](https://www.domainlanguage.com/wp-content/uploads/2016/05/DDD_Reference_2015-03.pdf),
  verified 2026-08-02. This variant is worth naming because it is the case
  most often mistaken for the pure-buy variant when the answer is neither buy
  nor treat-as-core, but a third, narrower kind of in-house investment.

## 9. Known production uses

- **Figma's payment and storage layers.** Figma's own architecture, as
  analyzed by a third-party DDD case study, treats subscription billing as a
  generic subdomain served by Stripe and object storage as a generic subdomain
  served by AWS S3, reserving in-house engineering depth for design-file
  collaboration and rendering, which are the parts of the product Figma
  actually competes on. Source. [lazebny.io, "Domain-Driven Design. Core,
  Supporting and Generic Subdomains"](https://lazebny.io/domain-driven-design-core-supporting-generic-subdomains/),
  verified 2026-08-02.
- **Auth0 as a vendored Identity and Access generic subdomain.** Auth0
  describes its own product as "an identity platform to manage access to your
  applications," explicitly positioned so that a business assembles the
  building blocks of an identity and access management solution rather than
  building authentication and authorization from scratch. Source.
  [auth0.com/docs/get-started](https://auth0.com/docs/get-started), verified
  2026-08-02. This is the productized, market-facing form of the exact
  Identity and Access Context that Vernon's SaaSOvation case study treats as
  generic in *Implementing Domain-Driven Design*.
- **Stripe as a vendored Payments generic subdomain.** Stripe positions itself
  as a unified payments platform spanning online payments, in-person
  transactions, subscriptions, and financial operations, explicitly framing
  the value as saving a business's own development resources and absorbing
  PCI compliance and regulatory burden so the business's engineers can spend
  their time elsewhere. Source. [stripe.com/payments](https://stripe.com/payments),
  verified 2026-08-02. This is a direct, named instance of the compliance
  transfer force from dimension 3.
- **SaaSOvation's Identity and Access Context.** Vaughn Vernon's own worked
  example across *Implementing Domain-Driven Design* deliberately builds an
  Identity and Access bounded context as an explicitly generic, low-investment
  context, in contrast to the Collaboration Context that carries the actual
  product's competitive logic, to demonstrate the classification inside a
  single coherent codebase rather than only in the abstract. Confirmed against
  the book's described chapter structure and case study, see
  [O'Reilly listing](https://www.oreilly.com/library/view/implementing-domain-driven-design/9780133039900/),
  verified 2026-08-02.

## 10. Consequences

**Positive.**

- Frees senior engineering attention for the Core Domain, where it compounds
  into actual competitive advantage instead of maintaining a commodity.
- Reduces time to market for the capability itself, since a mature vendor
  product has already absorbed years of edge cases a from-scratch build would
  rediscover the hard way.
- Transfers a meaningful share of security and compliance burden to a party
  whose business model depends on carrying it correctly, in the buy and
  open-source-hosted variants.
- Makes the system's investment priorities legible. A context map that marks
  contexts Core, Supporting, and Generic tells a new engineer, in one glance,
  where care and creativity are expected and where a boring, well-tested
  integration is the correct and complete answer.

**Negative.**

- Introduces a durable dependency on a third party's pricing, roadmap,
  reliability, and continued existence, which is a real risk even for a truly
  commodity capability.
- Creates an integration tax at every boundary, the Anti-Corruption Layer or
  adapter code, which is real engineering effort even though it is smaller
  than a full build would have been.
- Accumulates data gravity and switching cost over time. The generic
  subdomain that was trivial to adopt on day one can become expensive to
  leave by year five, especially for identity and payments, where the data
  held by the vendor is deeply entangled with every other part of the system.
- Misclassification is expensive in both directions. Treating a true Core
  capability as generic starves it of the investment it needed to become a
  differentiator. Treating a true Generic capability as core wastes senior
  engineering time that could not be recovered later.

## 11. Failure modes and misuse

**Symptom.** A capability everyone agreed was mere plumbing quietly becomes
the thing customers actually mention when they explain why they chose a
competitor instead.
**Cause.** The team classified the capability as generic based on its surface
appearance rather than the business's actual differentiation, mistaking
boring to build for unimportant to the business, the exact inversion Evans's
"Generic Doesn't Mean Reusable" warning targets, though here the mistake runs
the opposite direction, treating a hard, differentiating capability as if it
were merely generic.
**Fix.** Re-run the classification explicitly against the business strategy,
not against engineering difficulty. Khononov's test, would a competitor buying
the exact same off-the-shelf product erase our advantage, is the sharpest
version of this check. If the answer is yes, the capability was never
generic.

**Symptom.** The Core Domain's own model accumulates vendor vocabulary. Method
names, field names, and even exception types from the identity or payments
vendor start showing up inside the Core Domain's business logic.
**Cause.** No Anti-Corruption Layer was built, or the team built one but let
call sites bypass it one time under deadline pressure, and the bypass
became the norm.
**Fix.** Reintroduce the port. Move every direct vendor-type reference behind
it. Treat a leaked vendor type inside the Core Domain the same way a code
review would treat a leaked database row type inside a domain entity, as a
layering violation to reject, not a style preference.

**Symptom.** Switching or upgrading the generic subdomain's vendor turns into
a multi-quarter project that touches half the codebase.
**Cause.** The team correctly bought the generic capability but skipped the
translation boundary, wiring the vendor's SDK directly into dozens of call
sites because the adapter felt like unnecessary ceremony for something
labeled plain, ordinary generic.
**Fix.** This is the same root cause as the previous failure mode with a
different symptom, and the same fix applies. The Anti-Corruption Layer is not
optional ceremony. It is the mechanism that makes the vendor swappable, which
is the entire justification for treating the capability as generic in the
first place rather than binding the system to one vendor permanently.

**Symptom.** The team builds an in-house version of a genuinely generic
capability, and it is worse, slower, and more expensive to maintain than any
mature vendor product would have been, with no compensating business benefit.
**Cause.** Organizational reasons unrelated to the classification, a
procurement process too slow to approve a vendor contract, a security team
that distrusts all third-party data processors regardless of the specific
vendor's track record, or simple inertia from a team that has always built
everything itself.
**Fix.** This is not a modeling failure and the Generic Subdomain pattern
cannot fix it by itself. Surfacing the classification explicitly, stating out
loud that a capability has been labeled Generic and should therefore be
bought, at least turns an invisible default into a visible decision an
organization can choose to override with its reasons on the record, rather
than an unexamined habit.

**Symptom.** A generic subdomain integration works fine in isolation, but the
Core Domain's own domain events end up carrying vendor-shaped payloads because
someone wired the adapter's raw callback directly into the event bus instead
of translating it first.
**Cause.** The team built the inbound half of the Anti-Corruption Layer, the
port the Core Domain calls out through, but skipped the outbound half, the
translation of vendor webhooks or callbacks back into domain events the rest
of the system already understands.
**Fix.** Treat inbound and outbound translation as one boundary, not two. Any
webhook or callback from the vendor passes through the same adapter module
that handles outbound calls, and it emits a domain event shaped in the
system's own ubiquitous language, never a re-broadcast of the vendor's own
payload shape.

## 12. Trade-off matrix

| Force | Generic Subdomain (buy or thin-integrate) | Supporting Subdomain (build plain, in-house) | Core Domain (build rich, in-house) | Cohesive Mechanism (Evans) |
|---|---|---|---|---|
| Engineering investment | Minimal, spent on the adapter only | Moderate, competent but not deep | Maximal, dedicated team | Moderate to high, but scoped narrowly to the algorithm |
| Business differentiation | None by design | Low, supports the core without competing on it | High, the reason customers choose this product | None, it is domain-agnostic machinery |
| Vendor or ownership risk | Real, an external party controls roadmap and pricing | Low, fully owned, but low investment means low resilience too | Low ownership risk, but high delivery risk if under-resourced | Low ownership risk, contained by its narrow scope |
| Data or algorithm reuse across products | High, the same vendor product often serves unrelated businesses | Low, tailored to this product's supporting needs | Low, deliberately specific to this business | High, the mechanism itself can be reused across unrelated domains |
| Compliance burden | Largely transferred to the vendor | Fully owned in-house | Fully owned in-house | Fully owned in-house, but usually not compliance-sensitive |
| Correct default when uncertain | Prefer this when in doubt for a low-differentiation capability | Prefer this for necessary but non-differentiating custom logic | Reserve for the capability the business strategy actually depends on | Reserve for a genuinely reusable, elaborate algorithm, not a business rule |

## 13. Related and incompatible patterns

- **Open Host Service and Published Language.** These are the specific
  integration-pattern names Evans and Vernon give to the boundary described in
  dimension 5. An Open Host Service exposes a stable, documented protocol at
  the generic subdomain's edge, and a Published Language is the schema that
  protocol speaks. Together they are what makes the Anti-Corruption Layer on
  the consuming side thin rather than heavy, because most of the translation
  work has already been done once, at the boundary, rather than separately by
  every consumer.

- **Bounded Context (`bounded-context.md`).** A prerequisite. Generic
  Subdomain is a strategic label applied to a Bounded Context, and the
  classification is meaningless without a context to classify.
- **Context Map (`context-map.md`).** Where the classification becomes
  visible and actionable. The relationship type recorded on the map, an
  Anti-Corruption Layer, a Conformist relationship, or a Customer or Supplier
  relationship, is chosen partly based on whether the upstream side is Core,
  Supporting, or Generic.
- **Ubiquitous Language (`ubiquitous-language.md`).** A Generic Subdomain
  deliberately does not share its ubiquitous language with the Core Domain.
  The translation boundary exists precisely to keep the vendor's vocabulary
  from polluting the Core Domain's own carefully cultivated language.
- **Anti-Corruption Layer.** The structural mechanism that makes adopting a
  Generic Subdomain safe. Without it, the pattern degrades into direct vendor
  coupling, one of the primary failure modes above.
- **Core Domain.** The pattern's direct complement. A subdomain classification
  exercise always produces both labels together. Naming what is Generic is
  most useful precisely because it clarifies, by exclusion, what is Core.
- **Incompatible with treating the capability as a place for creative
  modeling.** Investing DDD's full tactical toolkit inside a subdomain
  correctly classified as Generic, a rich aggregate design, domain events, a
  carefully cultivated ubiquitous language, is a direct contradiction of the
  classification's purpose. If a team finds itself doing that, either the
  classification was wrong, or the modeling effort is misallocated.

## 14. Refactoring path in and out

**Introducing the pattern into a codebase that does not have it.** Start from
a system where authentication, payments, or another commodity capability is
built in-house or where a vendor is already in use but wired in directly.

1. Name the port. Write a domain-owned interface expressing exactly what the
   rest of the system needs from the capability, in the domain's own
   vocabulary, not the vendor's. This is a variant of Extract Interface as
   described in Martin Fowler, *Refactoring. Improving the Design of Existing
   Code*, 2nd edition, Addison-Wesley, 2018.
2. Move every call site that currently touches the capability's concrete
   implementation, whether an in-house class or a vendor SDK, to depend on the
   new port instead. This is Extract Interface applied at the boundary, done
   incrementally, one call site at a time, kept green after each step.
3. Write the adapter that implements the port against the real
   implementation. If a vendor is being adopted for the first time, this
   adapter is also where the vendor's actual SDK calls live, isolated from
   the rest of the codebase.
4. Verify no import of the vendor SDK, or the old in-house implementation's
   concrete type, remains outside the adapter module. A simple static grep
   for the vendor's package name across the rest of the codebase is often
   sufficient to confirm this step.
5. Only after the boundary is clean does a vendor migration, if one is
   planned, become a change confined to the adapter alone.

**Removing the pattern.** This direction is rare and usually only correct when
a classification was wrong in the first place, discovered because the
supposedly generic capability turned out to matter competitively.

1. Confirm the reclassification with the same rigor as the original
   classification, ideally against a concrete business signal, a lost deal or
   a competitor's explicit advantage, rather than an engineer's hunch that the
   code feels important.
2. Do not delete the port. Keep the same interface and begin investing real
   domain modeling depth inside the implementation behind it, promoting the
   subdomain's status without necessarily changing its external contract on
   day one.
3. Gradually replace the thin adapter with a richer domain model as the
   business case for the investment plays out, treating this as a normal
   Core Domain build rather than a special reclassification operation.

## 15. Testing and verification

A related, easily missed test is a contract-drift test, run on a schedule
rather than per commit, that replays a recorded, known-good vendor response
against the adapter's parsing logic and fails loudly the day the shape no
longer matches what the vendor actually returns. Vendors evolve their APIs
without always breaking backward compatibility in an obvious way, adding a
field, deprecating another, and a Generic Subdomain integration that has no
independent signal for this drift finds out only when the translation
failures counted in dimension 16 start climbing in production.

The port makes the Core Domain's own tests trivial to isolate. The Core
Domain's unit tests exercise `AccountRegistration`, or whatever consumes the
port, against a hand-written test double implementing the port's interface,
never against the real vendor. This is the direct payoff of the boundary
described in dimensions 5 through 7, and it is the single easiest way to tell,
during code review, whether a Generic Subdomain integration was done
correctly. If a Core Domain unit test needs network access, a vendor sandbox
account, or vendor-specific mocking libraries, the port is leaking.

The adapter itself needs a different kind of test, a contract test against
the real vendor or against the vendor's documented sandbox environment,
because the adapter's whole job is faithfully translating the vendor's real
behavior, including its real error responses, rate limits, and edge cases,
into the domain's port contract. A hand-rolled fake vendor response is not
sufficient evidence that the adapter is correct. Only the real integration,
run periodically even if not on every commit, proves that.

What becomes harder to test is any scenario that depends on the generic
subdomain's specific failure modes surfacing correctly through the whole
system, for example an identity provider outage during checkout or a payment
gateway timeout mid-transaction. These need explicit fault-injection tests at
the adapter boundary, simulating the vendor returning a 503, a malformed
response, or a timeout, rather than relying on the real vendor's sandbox to
reliably misbehave on demand.

## 16. Observability signals

A healthy Generic Subdomain integration is boring to watch. The signals that
matter live almost entirely at the adapter boundary, not inside the vendor or
inside the Core Domain.

- **Adapter-level latency and error rate**, tagged separately from the Core
  Domain's own request latency, so a vendor slowdown is immediately
  distinguishable from a genuine performance regression in business logic.
- **Vendor SLA compliance**, tracked against the specific numbers the vendor
  publishes, so a degradation is caught against a documented baseline rather
  than against a felt sense that things seem slower.
- **Circuit breaker state**, if one wraps the adapter, since a generic
  subdomain integration is one of the most common places a circuit breaker
  earns its keep, given that the dependency is external and outside the
  team's control.
- **Translation failures**, distinct from vendor failures, counted whenever
  the adapter receives a response it cannot map into the port's contract. A
  rising count here usually means the vendor changed its API shape without
  the team noticing.
- **A dashboard panel that groups every generic subdomain dependency
  together**, separate from Core Domain service health, so an on-call
  engineer's first triage question, whether the problem is us or a vendor,
  has a direct answer instead of requiring investigation.

A failing instance looks like rising adapter-level error rates with flat or
normal Core Domain error rates elsewhere, a growing translation-failure count
after a vendor release, or a circuit breaker that trips more often than the
vendor's published incident history would predict, which usually means the
integration's timeout or retry configuration is miscalibrated rather than the
vendor genuinely being unreliable.

## 17. Security and privacy implications

Judgement. The security posture of a Generic Subdomain depends heavily on
which capability it is and which variant from dimension 8 is chosen, so this
section is analytical rather than a single universal rule.

Buying a Generic Subdomain for identity or payments transfers a substantial
share of a serious attack surface, credential storage, token issuance, card
data handling, to a vendor whose entire business depends on defending it well,
which for most teams is a net security improvement over an in-house
equivalent built without dedicated security staff. This is the concrete
mechanism behind Stripe's own stated PCI-compliance value proposition cited
in dimension 9.

The trade is a new and different attack surface, the integration boundary
itself. A leaked API key for the vendor, an insufficiently scoped OAuth
client, or a webhook endpoint that does not verify the vendor's signature all
become the actual point of failure, and none of them are the vendor's fault to
fix. The Anti-Corruption Layer that isolates the vendor's model from the Core
Domain should also be the place where these controls live, credential
storage, signature verification, scope minimization, because it is already
the single choke point every interaction with the vendor passes through.

Data residency and cross-border transfer become a genuine concern the moment
personal data, identity claims, payment metadata, message content for a
communications vendor, leaves the system's own infrastructure. A generic
subdomain classification does not remove the obligation to know, contractually
and technically, where that data physically lives and under which
jurisdiction's law it sits, particularly for regulated data categories.

A final, judgement-based note worth stating plainly. The security review of a
Generic Subdomain integration is often skipped entirely, on the reasoning that
the vendor "handles security." Vendor-handled security covers the vendor's
own infrastructure. It does not cover how the adapter stores the vendor's
credentials, how the webhook signature is verified, or how the translated
domain event is authorized before it reaches the rest of the system. Every
one of those remains the integrating team's own responsibility, and treating
the whole boundary as someone else's problem is the single most common
security gap this pattern's own success tends to create, precisely because
the rest of the integration is genuinely low-risk enough to lull a reviewer
into skipping the part that is not.

## Code examples

Three languages, chosen because they show the pattern in a statically typed
object-oriented style (TypeScript), a dynamically typed style with an
explicit abstract base (Python), and an interface-based style with no
inheritance at all (Go). All three compile or run as shown.

Each sample models the same shape. a domain-owned `IdentityProvider` port, an
`Auth0IdentityProvider` adapter implementing it, and an `AccountRegistration`
service that depends only on the port, never on the adapter or the vendor
directly. Compiled and run 2026-08-02 with `npx tsc`, `python3`, and
`go run` respectively.

```typescript
interface IdentityProvider {
  verifyToken(token: string): Promise<{ subjectId: string; email: string }>;
}

class Auth0IdentityProvider implements IdentityProvider {
  constructor(private readonly domain: string, private readonly clientId: string) {}

  async verifyToken(token: string): Promise<{ subjectId: string; email: string }> {
    if (token.length === 0) {
      throw new Error("empty token");
    }
    return { subjectId: `auth0|${token.slice(0, 6)}`, email: "user@example.com" };
  }
}

class AccountRegistration {
  constructor(private readonly identity: IdentityProvider) {}

  async register(token: string): Promise<string> {
    const claims = await this.identity.verifyToken(token);
    return `account created for ${claims.subjectId}`;
  }
}

async function main() {
  const provider = new Auth0IdentityProvider("example.us.auth0.com", "abc123");
  const registration = new AccountRegistration(provider);
  const result = await registration.register("token-xyz789");
  console.log(result);
}

main();
```

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass(frozen=True)
class Claims:
    subject_id: str
    email: str

class IdentityProvider(ABC):
    @abstractmethod
    def verify_token(self, token: str) -> Claims:
        raise NotImplementedError

class Auth0IdentityProvider(IdentityProvider):
    def __init__(self, domain: str, client_id: str) -> None:
        self.domain = domain
        self.client_id = client_id

    def verify_token(self, token: str) -> Claims:
        if not token:
            raise ValueError("empty token")
        return Claims(subject_id=f"auth0|{token[:6]}", email="user@example.com")

class AccountRegistration:
    def __init__(self, identity: IdentityProvider) -> None:
        self.identity = identity

    def register(self, token: str) -> str:
        claims = self.identity.verify_token(token)
        return f"account created for {claims.subject_id}"

def main() -> None:
    provider = Auth0IdentityProvider("example.us.auth0.com", "abc123")
    registration = AccountRegistration(provider)
    print(registration.register("token-xyz789"))

if __name__ == "__main__":
    main()
```

```go
package main

import (
	"errors"
	"fmt"
)

type Claims struct {
	SubjectID string
	Email     string
}

type IdentityProvider interface {
	VerifyToken(token string) (Claims, error)
}

type Auth0IdentityProvider struct {
	Domain   string
	ClientID string
}

func (a Auth0IdentityProvider) VerifyToken(token string) (Claims, error) {
	if token == "" {
		return Claims{}, errors.New("empty token")
	}
	end := 6
	if len(token) < end {
		end = len(token)
	}
	return Claims{SubjectID: "auth0|" + token[:end], Email: "user@example.com"}, nil
}

type AccountRegistration struct {
	Identity IdentityProvider
}

func (r AccountRegistration) Register(token string) (string, error) {
	claims, err := r.Identity.VerifyToken(token)
	if err != nil {
		return "", err
	}
	return fmt.Sprintf("account created for %s", claims.SubjectID), nil
}

func main() {
	provider := Auth0IdentityProvider{Domain: "example.us.auth0.com", ClientID: "abc123"}
	registration := AccountRegistration{Identity: provider}
	result, err := registration.Register("token-xyz789")
	if err != nil {
		panic(err)
	}
	fmt.Println(result)
}
```

Java, Rust, and Swift are omitted here. the pattern is a strategic
classification rather than a code-level structural pattern, so the port and
adapter shape above is identical in spirit across every language this
repository targets, and a fourth or fifth translation of the same twenty
lines would not show anything the three above do not already demonstrate.

## 18. References

1. Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
   Software*, Addison-Wesley, 2003, chapter 15, "Distillation," sections
   "Core Domain," "Generic Subdomains," and "Generic Doesn't Mean Reusable."
   Section structure confirmed against
   [Eric Evans, DDD Reference (domainlanguage.com)](https://www.domainlanguage.com/wp-content/uploads/2016/05/DDD_Reference_2015-03.pdf)
   and the archived manuscript index at
   [fabiofumarola.github.io/nosql/readingMaterial/Evans03.pdf](https://fabiofumarola.github.io/nosql/readingMaterial/Evans03.pdf),
   verified 2026-08-02.
2. Vaughn Vernon, *Implementing Domain-Driven Design*, Addison-Wesley, 2013.
   The SaaSOvation case study, its Collaboration Context, the Core Domain, and
   its Identity and Access Context, the Generic Subdomain, described via the
   publisher listing at
   [O'Reilly, Implementing Domain-Driven Design](https://www.oreilly.com/library/view/implementing-domain-driven-design/9780133039900/),
   verified 2026-08-02.
3. Vaughn Vernon, *Domain-Driven Design Distilled*, Addison-Wesley, 2016.
   Restates the Core, Supporting, Generic classification as the first
   strategic step, per the publisher's own description at
   [Amazon listing, Domain-Driven Design Distilled](https://www.amazon.com/Domain-Driven-Design-Distilled-Vaughn-Vernon/dp/0134434420),
   verified 2026-08-02.
4. Vladik Khononov, *Learning Domain-Driven Design*, O'Reilly, 2021, chapter
   1, "Analyzing Business Domains." Chapter title and the three-way subdomain
   classification confirmed via the publisher's chapter listing search
   result, verified 2026-08-02.
5. Martin Fowler, "Bounded Context," martinfowler.com bliki, 15 January 2014,
   [martinfowler.com/bliki/BoundedContext.html](https://martinfowler.com/bliki/BoundedContext.html),
   verified 2026-08-02. Cited for the strategic-design framing that Generic
   Subdomain classification depends on.
6. "Domain-Driven Design. Core, Supporting and Generic Subdomains,"
   [lazebny.io](https://lazebny.io/domain-driven-design-core-supporting-generic-subdomains/),
   verified 2026-08-02. Cited for the Figma production-use case, treating
   Stripe (payments) and AWS S3 (storage) as generic subdomains.
7. Auth0, "Get Started" documentation,
   [auth0.com/docs/get-started](https://auth0.com/docs/get-started), verified
   2026-08-02. Cited for Auth0's own description of itself as an identity
   platform assembled instead of built in-house.
8. Stripe, "Payments" product page,
   [stripe.com/payments](https://stripe.com/payments), verified 2026-08-02.
   Cited for Stripe's stated value proposition of transferring development
   effort and compliance burden away from the adopting business.
9. Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
   edition, Addison-Wesley, 2018. Cited for the Extract Interface refactoring
   used in dimension 14's introduction path.
