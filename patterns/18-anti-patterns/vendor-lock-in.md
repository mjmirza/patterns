---
name: Vendor Lock-in
slug: vendor-lock-in
family: 18-anti-patterns
category: Anti-pattern
aliases: [Platform Lock-in, Cloud Lock-in, Proprietary Coupling, Golden Handcuffs]
first_described: "Term in general commercial use since at least the 1970s IBM mainframe era; first academic treatment of switching costs as a lock-in mechanism appears in Paul Klemperer, Market with Consumer Switching Costs, Quarterly Journal of Economics, 1987"
maturity: established
related: [hexagonal-architecture, adapter, strangler-fig-application, anti-corruption-layer, facade, dependency-inversion-principle, repository]
incompatible_with: [hexagonal-architecture]
verified: 2026-08-02
---

# Vendor Lock-in

## 1. Name, aliases, and lineage

The canonical name in software engineering discourse is Vendor Lock-in, sometimes
narrowed to Cloud Lock-in when the vendor in question is a public cloud
provider, or Platform Lock-in when the coupling is to an operating system,
mobile app store, or SaaS platform rather than infrastructure. The underlying
idea is older than software. It describes any situation where switching from
one supplier to another carries a cost so high that the customer stays even
after the terms of the relationship stop favouring them.

The pattern does not have a single named author the way a Gang of Four pattern
does, because it is not a design choice anyone sets out to build. It is a
byproduct of decisions made for other reasons, observed and named after the
fact. The earliest rigorous economic treatment of the mechanism is Paul
Klemperer's 1987 paper on markets with consumer switching costs, which models
how a firm can charge above competitive prices to an already committed customer
base, precisely because the cost of leaving exceeds the cost of staying
(Klemperer, "Markets with Consumer Switching Costs", *Quarterly Journal of
Economics*, vol. 102, no. 2, 1987, pp. 375 to 394; summary confirmed via
[the paper's abstract on the Oxford Academic QJE archive](https://academic.oup.com/qje/article-abstract/102/2/375/1931195),
verified 2026-08-02). The IBM mainframe era of the 1960s and 1970s is
frequently cited as the origin case in industry retrospectives, because
proprietary IBM System/360 hardware, OS/360 software, and IBM's own storage
formats bound customers to a single supplier for decades before "open systems"
became a marketing and engineering counter-movement in the 1980s.

In cloud computing specifically, the term entered mainstream engineering
vocabulary through vendor-neutral advocacy groups and standards bodies rather
than a single paper. The Cloud Native Computing Foundation, founded in 2015 as
part of the Linux Foundation, states portability across cloud providers as an
explicit design goal for the Kubernetes project it stewards, and frames that
goal directly in opposition to lock-in (see the CNCF's own charter language at
[cncf.io/about](https://www.cncf.io/about/), verified 2026-08-02, which lists
"cloud portable platforms" among its stated technical priorities). This entry
treats Vendor Lock-in as an anti-pattern in the architectural sense used
throughout this catalog, a recurring, recognisable, and often unintentional
structural decision whose short-term convenience creates a long-term structural
liability, distinct from a deliberate, informed business trade-off.

## 2. Problem and context

A team building a system needs to store data, run compute, send messages,
authenticate users, and observe the running system. Every one of those needs
has a fast path, adopt the managed service the cloud provider already offers,
call its SDK directly from application code, and use its proprietary query
language, event format, or configuration surface because that is what the
tutorial shows and what the fastest path to a working demo looks like. Each
individual decision is locally rational. The team ships faster, avoids
operating undifferentiated infrastructure, and gets first-party support.

The problem surfaces months or years later, not at decision time. Once
business logic, IAM policies, data models, and operational tooling are wired
directly to a specific provider's proprietary surface, three things become
true at once. First, the cost of switching away exceeds the perceived benefit
of switching, even when the current vendor is now more expensive, less
reliable, or has changed terms unfavourably, because the switching cost itself
has become the dominant factor in the decision, exactly the mechanism
Klemperer modelled. Second, the vendor's own incentives shift once the
customer is committed. A vendor with low switching costs must compete
continuously on price and service; a vendor whose customers face six figure
migration projects has far less pressure to do so. Third, and the part most
teams underestimate, the coupling is rarely confined to infrastructure. It
propagates into the domain model itself, a schema shaped by a proprietary
NoSQL API's item size limits, a codebase full of scattered SDK calls threaded
through business logic instead of confined to an edge, an authorization model
built entirely around one provider's IAM primitives with no independent
concept of a role or a permission.

The context in which lock-in becomes a genuine anti-pattern, rather than a
sound business decision, is specific. It arises when the coupling was never
weighed as a decision at all, when the switching cost was not estimated before
it was incurred, when the proprietary surface reaches deep into business logic
rather than staying at the system's edges, and when no organisational owner is
accountable for the resulting concentration risk. Outside that context,
choosing a single vendor deliberately, with eyes open about the trade, is
sound engineering, and section 4 draws that line explicitly.

## 3. Forces

Vendor lock-in is the observable consequence of a real trade-off, not a simple
mistake, and understanding the pattern means understanding which side of each
force a team is choosing, often without realising it is choosing at all.

**Velocity versus optionality.** Adopting a provider's managed, proprietary
service, a specific example is Amazon DynamoDB's native item and query API
rather than a SQL compatible interface, is almost always faster to build
against than an abstraction layer that could later target multiple backends.
The abstraction layer costs real engineering time up front and adds a layer
of indirection that must be maintained forever, whether or not the team ever
switches. Every hour spent on portability is an hour not spent on the feature
the business actually needs today. This is the single most important force,
and it means the anti-pattern is not "using managed services" but "using
managed services without ever weighing this trade-off explicitly."

**Feature depth versus surface neutrality.** Cloud providers differentiate on
depth. AWS DynamoDB's transactional writes, single digit millisecond latency
at scale, and built-in streams are only available through DynamoDB's own API.
Abstracting behind a generic key-value interface, say, an interface that could
also target Redis or a self-hosted database, means giving up the very
features that made the vendor's service attractive in the first place. The
deeper the feature set a team wants to exploit, the harder true portability
becomes, because portability by construction means restricting yourself to
the lowest common denominator across every backend you might ever switch to.

**Cost predictability versus negotiating power.** A single vendor
relationship at scale often comes with volume discounts, committed use
pricing, and dedicated support that a multi vendor posture cannot match dollar
for dollar in the near term. Concentrating spend is frequently the
economically rational near term choice. The cost only becomes visible when the
vendor changes pricing terms unilaterally, which is precisely the scenario
Oracle's customers experienced in January 2023, when Oracle restructured Java
SE licensing from a per processor and per user model to a blanket per
employee subscription, producing documented renewal quotes that increased by
several hundred percent up to more than thirty times the prior figure,
depending on the customer's employee to Java usage ratio (Azul Systems,
"Oracle Java Pricing Change FAQ",
[azul.com/products/core/oracle-pricing-change-faq](https://www.azul.com/products/core/oracle-pricing-change-faq/),
verified 2026-08-02, reporting Oracle's own published 2023 Java SE Universal
Subscription price list and resulting customer renewal cases).

**Cognitive load versus multi target complexity.** An engineering team that
learns one provider's tooling deeply, end to end, builds real operational
expertise, they know the failure modes, the quirks, the support escalation
paths. A team that must design for portability across N providers either
carries N sets of operational knowledge or restricts itself to the shared
subset of behaviour, both of which raise cognitive load in different ways.
Genuine multi cloud operation, not merely multi cloud capable code, but
actually running production traffic across two or more providers
simultaneously, is one of the most expensive operating postures in software
engineering, and most organisations that attempt it never reach the point
where the redundancy pays for the complexity.

**Regulatory and geopolitical risk versus commercial simplicity.** For
regulated industries and public sector customers, data residency law, export
control, and the risk that a single foreign vendor could be compelled or
choose to withdraw service creates a force that has nothing to do with
technical velocity at all. This force has grown sharply since 2022 in the
European Union specifically, where the EU's Digital Markets Act and a series
of national sovereign cloud initiatives treat hyperscaler concentration as a
policy problem rather than only an engineering one (European Commission,
"The Digital Markets Act",
[digital-markets-act.ec.europa.eu](https://digital-markets-act.ec.europa.eu/index_en),
verified 2026-08-02, which designates gatekeeper platforms and imposes
interoperability obligations specifically to reduce this class of dependency).

The pattern favours velocity, feature depth, and near term cost predictability.
It sacrifices optionality, negotiating power over time, and resilience to a
single supplier's unilateral decisions. No engineering choice eliminates this
trade-off; every mitigation in this entry, Facade, Anti-Corruption Layer,
Hexagonal Architecture, trades some velocity back for some optionality, at a
cost that must itself be weighed rather than assumed to always be worth
paying.

## 4. Applicability and non-applicability

### When accepting some lock-in is the sound decision

- The organisation is small, the product is early stage, and the dominant risk
  is running out of runway before finding product market fit, not the five
  year cost of a hypothetical migration that may never happen.
- The proprietary capability being adopted delivers a genuine, differentiated
  advantage that no portable alternative offers at comparable cost or
  reliability, and the team has explicitly decided that advantage is worth the
  coupling.
- The switching cost has been estimated, even roughly, and weighed against the
  probability and cost of needing to switch, as a conscious build versus buy
  decision rather than a default.
- The system's lifetime is short by design, a time boxed internal tool, a
  proof of concept meant to be replaced within a fixed period, and the cost of
  building an abstraction layer would exceed the system's total lifetime
  value.
- A regulatory, contractual, or partnership requirement mandates a specific
  vendor, removing the choice from the engineering team's hands entirely.

### When lock-in is the anti-pattern, not a decision

- The proprietary coupling reaches into core domain logic rather than staying
  confined to a well defined edge of the system, a repository implementation,
  an adapter, a small number of integration modules.
- No one on the team can estimate what a migration would cost, because the
  provider specific calls, data formats, and configuration are scattered
  through the codebase with no inventory or boundary.
- The decision to depend deeply on a single vendor was never made
  consciously; it accumulated as the sum of many small, locally reasonable
  choices, none of which anyone weighed against the cumulative effect.
- The system is expected to run and evolve for many years, is core to the
  business rather than peripheral, and carries meaningful switching cost risk
  that has not been priced into any budget or risk register.
- The vendor relationship shows early warning signs described in section 11,
  unilateral pricing changes, API deprecations with short notice, degrading
  support, and the organisation has no ability to respond because there is no
  abstraction boundary to exploit.

Applying an anti lock-in mitigation, sections 8 and 14, to every dependency
indiscriminately is itself a failure mode, described in section 11 as
premature portability. The applicability question is never "should we avoid
lock-in" in the abstract; it is "have we decided, with the switching cost and
its probability both estimated, whether this specific coupling is worth
accepting."

## 5. Structure

Vendor lock-in is not a design pattern with cooperating participants in the
usual sense; it is the absence of a boundary where one is warranted. The
structural elements worth naming are the parties and artefacts involved in
both the problem and its mitigation.

- **The consuming system.** The application, service, or platform whose code
  directly or indirectly depends on a vendor's proprietary surface.
- **The proprietary surface.** The specific vendor capability creating the
  coupling, a non standard API such as DynamoDB's item and query shape rather
  than SQL, a proprietary data format such as a cloud data warehouse's
  internal micro partition layout, a domain specific configuration language
  such as a provider's IAM policy document, which has no equivalent syntax
  elsewhere, or a distribution channel with unilateral gatekeeper rules such
  as an app store's review and revenue share terms.
- **The coupling points.** The literal call sites, schema definitions, and
  configuration files inside the consuming system that reference the
  proprietary surface directly. In an unmitigated system these are scattered
  through business logic. In a mitigated system they are concentrated behind
  a small number of named boundaries.
- **The mitigating boundary, when present.** An interface, port, or adapter
  layer, typically implemented with the Adapter or Facade patterns and
  organised according to Hexagonal Architecture's ports and adapters
  discipline, that the domain logic depends on instead of depending on the
  vendor surface directly.
- **The switching cost.** Not a physical artefact but the measurable quantity
  the whole pattern is about, engineering time, data migration risk, and
  business disruption required to replace the vendor. This quantity is what
  every mitigation in this entry exists to bound.

The absence of boundary framing matters because it distinguishes this entry
from a pattern like Adapter, which is a structural solution you apply. Vendor
Lock-in is the name for what happens in the structure's absence, which is why
its "structure" section is mostly about naming what is missing.

## 6. ASCII structure diagram

Unmitigated coupling, the anti-pattern as it commonly occurs.

```
+----------------------------------------------------+
|                  Application code                  |
|                                                      |
|  +------------------+   +----------------------+    |
|  | Order service     |-->| AWS SDK DynamoDB      |   |
|  | (business logic)  |   | PutItem / Query calls |   |
|  +------------------+   +----------------------+    |
|                                                      |
|  +------------------+   +----------------------+    |
|  | Auth middleware    |-->| Provider IAM policy  |   |
|  | (business logic)  |   | document, provider    |   |
|  +------------------+   |  native format         |   |
|                          +----------------------+    |
|  +------------------+   +----------------------+    |
|  | Report generator  |-->| Data warehouse's       |  |
|  | (business logic)  |   | proprietary SQL dialect|  |
|  +------------------+   +----------------------+    |
+----------------------------------------------------+
        No boundary. Every domain module calls the
        vendor surface directly. Switching any one
        vendor means editing every module that touches it.
```

Mitigated structure, with a bounded boundary applied deliberately.

```
+----------------------------------------------------+
|                  Application code                  |
|                                                      |
|  +------------------+                               |
|  | Order service      |                              |
|  | (business logic)   |                              |
|  +---------+----------+                              |
|            |  depends on interface                    |
|            v                                          |
|  +------------------+                               |
|  | OrderRepository    |  <-- port (interface)         |
|  |  (interface)       |                               |
|  +---------+----------+                               |
|            ^                                          |
|            |  implements                                |
|  +------------------+                               |
|  | DynamoDbOrderRepo  |  <-- adapter (one file)        |
|  +---------+----------+                               |
+------------|-----------------------------------------+
             v
     +----------------------+
     | AWS DynamoDB          |   only this file changes
     +----------------------+   on a provider switch
```

## 7. Dynamics

At development time, the failure sequence usually follows a predictable arc.

```
Week 1.   Team picks DynamoDB. Prototype calls PutItem directly
          from the order creation handler. Ships fast, demo works.

Month 3.  Second feature needs the same table. A second handler
          also calls PutItem directly, with slightly different
          item shaping logic (schema drift begins).

Month 9.  Team wants a transactional multi table write for a new
          feature. Discovers DynamoDB's transaction API has
          different semantics from what business logic assumed.
          A workaround is bolted onto the direct call site rather
          than reconsidered, because touching every call site is
          now expensive.

Month 18. Pricing review flags DynamoDB read/write capacity costs
          have grown fourfold with traffic. Someone asks how hard
          it would be to move this to Postgres. No one can answer,
          because DynamoDB specific item shapes, indexes, and
          access patterns are embedded in twenty call sites across
          six services, with no single point of change.

Month 19. Migration estimate comes back at four engineer months
          minimum, with data migration risk on a live system
          carrying customer orders. Migration is deprioritised
          indefinitely. The team is now, functionally, locked in,
          whether or not anyone ever said the word lock-in out loud.
```

At runtime, once lock-in exists, its most consequential dynamic is not a
crash or an error, but a decision the organisation never gets to make freely
again. The vendor renews terms, the vendor changes pricing, the vendor
deprecates an API version, or the vendor experiences an outage, and the
organisation's only two options are to absorb it or to absorb an expensive,
risky migration under pressure. The pattern's dynamics are economic and
organisational as much as technical; the technical coupling is the mechanism,
the loss of negotiating and decision-making freedom is the consequence.

## 8. Implementation variants

Because this entry describes an anti-pattern rather than a solution,
"variants" here means the recognisable shapes the coupling takes in practice,
each with a different profile of how it forms and how it can be mitigated.

- **SDK in business logic.** The most common variant. A provider's SDK, for
  example a cloud storage client or a cloud object client, is imported and
  called directly inside domain or application service code, rather than
  confined to an infrastructure layer. Mitigated by the Adapter pattern
  behind a domain owned interface, as shown in section 6's second diagram.
- **Proprietary data model coupling.** The shape of a proprietary storage
  API, item size limits, partition key design, eventual consistency
  semantics, leaks into the domain model itself, so that even a well adapted
  interface cannot hide the coupling because the domain objects were designed
  around the vendor's constraints, not the business's. This variant is the
  hardest to mitigate after the fact, because fixing it means redesigning the
  domain model, not just adding an adapter.
- **Configuration language coupling.** Infrastructure as code written
  directly against a provider's proprietary format, one vendor's stack
  templates or another's resource manager templates, with no portable layer
  above it. Terraform and similar tools are a partial mitigation for this
  variant specifically, though Terraform's own provider blocks reintroduce
  vendor specific resource types underneath a common syntax, so the
  mitigation is real but partial.
- **Identity and access coupling.** Authorization logic built entirely around
  a provider's IAM primitives, such as a specific cloud's policy documents or
  role definitions, with no independent concept of a role, permission, or
  policy the application itself owns. This variant is subtle because it is
  rarely visible in application code at all; it lives in infrastructure
  configuration and in the mental model of who can do what that the team
  carries around, which makes it easy to overlook during a migration estimate.
- **Distribution and platform lock-in.** A variant with no code level fix at
  all, dependence on a single app store, marketplace, or platform for
  distribution and payment, where the lock-in is contractual and commercial
  rather than architectural. A major mobile platform's app review guidelines
  and mandated in app purchase terms are the canonical example; no adapter
  pattern mitigates a platform's unilateral right to reject or delist an app.
- **Tooling and licensing lock-in.** A variant distinct from infrastructure
  coupling, dependence on a specific vendor's build tool, runtime, or
  developer tooling under terms that can change unilaterally, as with
  Oracle's 2023 Java SE relicensing (section 3) or HashiCorp's August 2023
  relicensing of Terraform from the Mozilla Public License to the Business
  Source License, a non open source license under the Open Source
  Initiative's definition, which triggered an industry response resulting in
  the OpenTofu fork, adopted by the Linux Foundation in September 2023 and
  released as a stable, MPL licensed alternative in January 2024 (see
  [en.wikipedia.org/wiki/OpenTofu](https://en.wikipedia.org/wiki/OpenTofu) and
  [opentofu.org/blog/opentofu-announces-fork-of-terraform](https://opentofu.org/blog/opentofu-announces-fork-of-terraform/),
  both verified 2026-08-02). This variant is mitigated not by an adapter
  pattern but by the open source community itself acting as a collective
  anti lock-in mechanism through forking rights the original license
  preserved.

## 9. Known production uses

Vendor lock-in is unusual among the entries in this catalog in that its known
uses are best documented not as successful applications of a pattern, but as
well documented cases of organisations discovering the switching cost the
hard way, and a smaller number of organisations documenting how they avoided
it.

- **37signals, Basecamp and HEY, 2022 to 2023.** After roughly fifteen years
  running on AWS and Google Cloud, 37signals publicly documented moving
  Basecamp, HEY, and five other production applications off the public cloud
  onto owned hardware, citing that promised cost, speed, and simplicity
  benefits had not materialised at their scale, and projecting savings of
  approximately ten million dollars over five years against roughly six
  hundred thousand dollars in server hardware investment, achieved without
  adding staff (37signals, "Leaving the Cloud",
  [basecamp.com/cloud-exit](https://basecamp.com/cloud-exit), verified
  2026-08-02). This is a case of an organisation that had already accepted
  deep cloud coupling and paid a real, bounded, but substantial cost to
  reverse it once the economics stopped favouring the vendor relationship.
- **Oracle Java SE licensing customers, 2023 onward.** Multiple independently
  reported customer cases, including a documented United Kingdom financial
  services firm with roughly twelve thousand employees whose Java SE renewal
  quote moved from approximately one hundred eighty thousand dollars under
  the prior named user model to approximately two point one million dollars
  under the 2023 per employee subscription model, illustrate the mechanism
  directly. Once an organisation's build and runtime toolchain is dependent
  on a single vendor's proprietary licensing terms, the vendor can
  restructure those terms with limited recourse for existing customers short
  of a full toolchain migration (Azul Systems, "Oracle Java Pricing Change
  FAQ",
  [azul.com/products/core/oracle-pricing-change-faq](https://www.azul.com/products/core/oracle-pricing-change-faq/),
  verified 2026-08-02, reporting figures drawn from Oracle's published 2023
  price list and subsequent customer renewal cases).
- **Netflix's multi year investment in cloud agnostic tooling.** Netflix has
  publicly documented building and open sourcing infrastructure tooling,
  including Spinnaker, a multi cloud continuous delivery platform originally
  built to deploy to both AWS and Google Cloud Platform, specifically to
  avoid being structurally dependent on a single cloud provider's deployment
  primitives, even while remaining primarily an AWS customer for compute
  (Spinnaker's own project history documents its origin as a multi cloud
  successor to Netflix's earlier internal Asgard tool; see
  [spinnaker.io/docs/concepts](https://spinnaker.io/docs/concepts/), verified
  2026-08-02, which describes the platform's explicit multi cloud provider
  model). This is a case of an organisation deliberately paying the velocity
  cost described in section 3 to preserve deployment level optionality, as a
  conscious strategic choice rather than an accident.
- **The Cloud Native Computing Foundation's Kubernetes project.** Kubernetes
  was explicitly designed and is explicitly governed to run identically
  across AWS, Google Cloud, Azure, and on premises infrastructure, and the
  CNCF states cloud portability as a stated technical goal of the project it
  stewards, distinct from any single hyperscaler's proprietary orchestration
  service (CNCF, "About the CNCF",
  [cncf.io/about](https://www.cncf.io/about/), verified 2026-08-02).
  Kubernetes is widely adopted specifically as an anti lock-in mitigation at
  the compute orchestration layer, even though the managed Kubernetes
  control planes themselves still carry their own, narrower vendor specific
  surface for identity, networking, and storage integration, illustrating
  that no single technology fully eliminates the pattern; it only moves the
  boundary.
- **The European Union's regulatory response to hyperscaler concentration.**
  The Digital Markets Act, in force since 2022 with enforcement beginning in
  2023 and 2024, designates large platform gatekeepers and imposes
  interoperability and data portability obligations on them specifically
  because policymakers identified vendor lock-in at hyperscale as a market
  failure requiring regulatory intervention, not one that market competition
  alone was resolving (European Commission, "The Digital Markets Act",
  [digital-markets-act.ec.europa.eu/index_en](https://digital-markets-act.ec.europa.eu/index_en),
  verified 2026-08-02). This is a case where the anti-pattern's consequences
  became visible at a scale that triggered government intervention rather
  than only individual organisation mitigation.

## 10. Consequences

### Positive, the reasons the coupling forms in the first place

- Faster initial delivery, because a proprietary managed service typically
  requires less integration code than a portable abstraction over an
  equivalent capability.
- Access to genuinely differentiated vendor features, transactional
  guarantees, latency characteristics, or managed operations quality, that a
  portable interface would have to give up to stay vendor neutral.
- Reduced day to day operational burden, since a single, deeply understood
  vendor relationship is often cheaper to operate than a multi vendor,
  multi tool posture, at least in the near term.
- Potential commercial bargaining power through committed use discounts, volume
  pricing, and dedicated support that come with concentrating spend.

### Negative

- Diminished or eliminated negotiating power once the switching cost
  exceeds the perceived value of switching, allowing the vendor to shift
  pricing or terms with limited customer recourse, exactly as observed with
  Oracle Java SE licensing.
- Concentration risk, a single vendor's outage, policy change, business
  failure, or unilateral API deprecation becomes a direct, unmitigated risk
  to the consuming system, with no fallback path.
- Migration cost that grows over time, not linearly with the size of the
  system but often faster, because coupling accumulates in more places the
  longer the system runs, and untangling it years later is harder than
  bounding it early would have been.
- Regulatory and contractual exposure in jurisdictions or industries where
  single vendor, single jurisdiction dependency creates compliance risk
  independent of the technical merits of the vendor relationship.
- Organisational atrophy of the skills needed to operate an alternative,
  since a team that has only ever run against one vendor's primitives for
  years loses the fluency needed to evaluate or execute a switch even when
  the decision to switch has been made.

## 11. Failure modes and misuse

**Silent accumulation with no inventory.** The most common failure mode is not
a single bad decision but the absence of any point at which someone asks what
it would cost to leave this vendor. Symptom, nobody on the team can answer
that question within an order of magnitude when asked. Cause, proprietary
calls, schema decisions, and configuration were made independently by many
engineers over time, each locally reasonable, with no single owner tracking
the cumulative coupling. Fix, an explicit, periodic dependency inventory
(section 14 describes the mechanics) that treats vendor coupling as a tracked
architectural liability, the same way technical debt or security exposure is
tracked, rather than an invisible byproduct of normal development.

**Coupling that reaches the domain model, not just the infrastructure edge.**
Symptom, a migration estimate reveals that even after building an adapter
layer, the domain objects themselves, their field shapes, their consistency
assumptions, their size limits, were designed around the vendor's specific
constraints and cannot represent an equivalent operation against a different
backend without a genuine redesign, not just a new adapter implementation.
Cause, the team adopted the vendor's data model as the domain model instead
of designing an independent domain model and mapping it to the vendor's
storage shape. Fix, this is the hardest failure mode to fix retroactively;
the practical remedy is the Strangler Fig Application pattern (see related
patterns, section 13) applied deliberately over an extended period,
redesigning the domain model incrementally rather than attempting a single
cutover.

**Premature portability, the overcorrection.** Symptom, the team has spent
significant engineering effort building a generic, multi backend abstraction
layer for a capability the business has never needed to switch, and probably
never will, and that abstraction layer is now itself a maintenance burden
that slows every feature touching it, because it must satisfy the lowest
common denominator of every backend it was designed to support. Cause,
treating avoid lock-in as a blanket rule rather than a cost benefit decision
made per dependency, ignoring the velocity force from section 3 entirely.
Fix, reserve portability investment for the small number of dependencies
where the switching cost risk genuinely justifies it, core data storage,
primary authentication, and payment processing are frequent candidates; a
logging sink or a transactional email provider usually is not, and accept
direct coupling deliberately everywhere else, documenting that decision so it
reads as a choice rather than an oversight later.

**Mistaking an abstraction layer for actual portability.** Symptom, a team
built an interface with a single implementation, congratulates itself on
being cloud agnostic, and discovers at migration time that the interface's
method signatures, error types, and consistency guarantees were shaped
entirely around the one vendor it was built against, so a second
implementation still requires substantial rework, not a clean drop in.
Cause, the interface was extracted from the existing vendor specific
implementation rather than designed independently from the business's actual
requirements. Fix, design the port from the domain's needs outward, and if
genuine multi backend support matters, prove the interface by implementing at
least two adapters, even a lightweight in memory or local file adapter for
testing counts, before trusting that the interface is truly vendor neutral.

**Ignoring the warning signs of a deteriorating vendor relationship.**
Symptom, in hindsight, after a costly forced migration, the team recognises
that pricing changes, deprecation notices with unusually short migration
windows, declining support quality, or a license change away from an open
license, as with HashiCorp's 2023 Terraform relicensing, had been visible for
months before the organisation acted. Cause, no one owned monitoring the
vendor relationship's health as an ongoing responsibility, treating the
initial adoption decision as a one time event rather than an ongoing risk to
be reassessed. Fix, assign explicit ownership, an architecture or platform
team, even if only as a fraction of one role, for periodically reassessing
key vendor dependencies against the criteria in section 16.

## 12. Trade-off matrix

Compared against the named architectural patterns most commonly used to
prevent or mitigate lock-in, across the forces identified in section 3.

| Approach | Velocity | Feature depth retained | Switching cost after adoption | Ongoing maintenance cost | Best suited when |
|---|---|---|---|---|---|
| Direct SDK coupling, the anti-pattern, unmitigated | Highest | Full | Very high, grows over time | Lowest, no extra abstraction to maintain | Short lived systems, or a deliberate, documented single vendor bet |
| Facade over a single vendor | High | Full | High but bounded to the facade's coverage | Low, one layer to maintain | Team wants a clean internal API today, not multi vendor support yet |
| Adapter with a single implementation, interface designed for portability | Medium | Full, one adapter | Medium, second adapter is new work but the seam already exists | Medium | Team expects to switch eventually but is not switching yet |
| Hexagonal Architecture, ports and adapters, multiple adapters maintained | Lower | Depends on interface design, often reduced to shared subset | Low, switching means writing a new adapter against a proven port | High, every port and every adapter is ongoing surface | Core, long lived, business critical dependency where switching risk is real and estimated |
| Genuine active multi cloud, simultaneous production traffic on two or more providers | Lowest | Reduced to lowest common denominator across providers, or duplicated logic per provider | Lowest for a single provider failure, but overall system complexity risk rises | Highest, effectively many times the operational surface | Regulatory mandate, extreme availability requirement, or negotiating power is worth the sustained cost |

No row in this table is universally correct. The matrix exists to make the
trade explicit for a specific dependency, not to recommend the bottom row as
inherently superior; most organisations that attempt the bottom row for most
of their dependencies regret it, per the premature portability failure mode
in section 11.

## 13. Related and incompatible patterns

- **Hexagonal Architecture, Ports and Adapters.** The primary structural
  mitigation. Hexagonal Architecture's core discipline, keeping domain logic
  dependent only on interfaces it defines itself, with adapters implementing
  those interfaces against specific external systems, is the architectural
  pattern that, applied deliberately at the right boundaries, prevents
  vendor coupling from reaching the domain model. Vendor Lock-in is, in a
  real sense, what Hexagonal Architecture exists to prevent, which is why it
  is listed as both related and, when fully applied at a system's edges,
  functionally incompatible with the anti-pattern in its purest unmitigated
  form.
- **Adapter.** The tactical, per dependency instrument that implements a
  Hexagonal Architecture port against a specific vendor's proprietary
  surface. Where Hexagonal Architecture is the overall discipline, Adapter is
  the individual class or module that does the translation.
- **Facade.** A lighter weight relative of Adapter, useful when the goal is
  simplifying and centralising calls to a vendor's SDK without committing to
  full multi backend portability. A Facade concentrates the coupling into one
  place, which bounds the switching cost, even without designing the
  interface for a second implementation the way a true port does.
- **Anti-Corruption Layer.** Domain Driven Design's term for a boundary that
  translates between a system's own domain model and an external system's
  model, preventing the external model's concepts from leaking in. It is the
  same structural idea as the Adapter mitigation here, framed specifically
  around protecting domain model integrity rather than switching cost,
  making it the sharpest tool against the domain model coupling failure mode
  in section 11.
- **Strangler Fig Application.** The pattern for incrementally replacing a
  system's dependency on something, including a vendor's proprietary
  surface, by routing an increasing share of traffic to a new implementation
  while the old one still runs, rather than attempting a single risky
  cutover. This is the practical remedy once lock-in has already accumulated
  and a migration is underway, as distinct from the boundary patterns above,
  which prevent the accumulation in the first place.
- **Dependency Inversion Principle.** The underlying object oriented design
  principle, high level modules should not depend on low level modules, both
  should depend on abstractions, that Hexagonal Architecture and the Adapter
  pattern both operationalise for the specific case of external vendor
  dependencies.
- **Repository.** A common, narrower application of the same boundary idea,
  specifically for data access coupling, and the pattern most often
  demonstrated in the code examples below.
- **Incompatibility with unmitigated single vendor architecture.** A system
  that has fully and deliberately embraced deep, direct coupling to one
  vendor as a conscious, well reasoned bet, section 4's first list, is, by
  construction, not applying Hexagonal Architecture at that boundary. This is
  not a flaw; it is simply the honest statement that the two postures are
  mutually exclusive at any given boundary, and a team should be able to say
  plainly which one it has chosen at each boundary, rather than believing it
  has both.

## 14. Refactoring path in and out

### Introducing the mitigation, refactoring out of unmitigated lock-in

1. **Inventory the coupling.** Before writing any code, grep the codebase for
   the vendor SDK's import statements, proprietary API calls, and vendor
   specific configuration files. Produce a concrete list of every call site.
   This step alone frequently surprises teams with how widely scattered the
   coupling has become.
2. **Estimate the switching cost as it exists today.** For each coupling
   point, estimate roughly how much work replacing it would take. This
   produces the number that section 11's first failure mode calls out as
   missing in most organisations, and it is the number that justifies, or
   fails to justify, the remaining steps.
3. **Define the port from the domain's actual needs, not the vendor's
   shape.** Write the interface the domain logic should have always
   depended on, expressed in the domain's own vocabulary, an order
   repository that saves an order, not a raw client call against a table
   with vendor specific parameters, independent of how the current vendor
   happens to implement the underlying operation.
4. **Implement the existing vendor as one adapter behind that port.** Move
   the existing proprietary calls, unmodified in behaviour, into a single
   adapter class that implements the new interface. This step should not
   change runtime behaviour at all; it is a pure extract interface and move
   method refactoring, and it should be covered by the existing test suite,
   or a new characterisation test suite written first if coverage is thin,
   before and after, exactly as this catalog's testing and verification
   dimension always demands for any behaviour preserving refactor.
5. **Update the domain and application layers to depend on the interface.**
   Replace every direct call site identified in step 1 with a call through
   the new port, injecting the concrete adapter at the system's composition
   root rather than instantiating it inside domain logic.
6. **Decide, explicitly, whether to build a second adapter now or defer it.**
   Building a second, real adapter, even a minimal one, or a local file
   backed adapter used only in tests, is the only reliable way to prove the
   interface is genuinely portable rather than merely relabelled, per the
   fourth failure mode in section 11. If the switching cost estimate from
   step 2 does not justify this investment yet, stop here deliberately,
   having still achieved the concentration benefit of steps 3 through 5, and
   record the decision.

### Removing the mitigation, when the abstraction has stopped earning its place

1. Confirm, honestly, that the interface has only ever had one real
   implementation and there is no credible near term scenario requiring a
   second one; this is the premature portability failure mode recognised
   late.
2. Inline the single adapter's implementation back into the call sites that
   use it, or leave the boundary in place if it still provides a
   readability or testing benefit independent of portability, since a
   Facade's value is not solely about vendor switching optionality.
3. Remove the interface only if it adds no remaining value; keeping a thin,
   low maintenance interface around a single implementation is frequently
   still worthwhile for testability even after portability is ruled out as a
   goal, so this final step should be the most conservative one in the whole
   sequence.

## 15. Testing and verification

Testing for vendor lock-in has two distinct concerns, verifying that the
mitigation, when one is applied, actually works, and verifying, in an ongoing
way, that the coupling has not silently crept back in.

**Testing the port and adapter boundary.** Once a port interface exists, the
domain and application logic that depends on it should be tested entirely
against a test double implementing the same interface, a fake, an in memory
implementation, or a hand written stub, never against the real vendor. This
is the standard advantage Hexagonal Architecture provides for testability,
and it applies directly here. If the domain logic's tests require network
access to the real vendor to pass, the port boundary has not actually
decoupled anything yet, and the tests themselves reveal the incomplete
mitigation.

**Contract tests for each adapter.** Each concrete adapter, including the
real vendor backed one, should be verified against a shared contract test
suite that exercises the interface's documented behaviour, so that a second
adapter written later can be validated against the same expectations the
first one satisfies, without either adapter's test suite silently diverging
from what the interface actually promises. This is the standard technique
for proving genuine substitutability rather than accidental compatibility.

**Verifying the coupling has not crept back.** Because the failure mode most
associated with this pattern is silent accumulation rather than a single
event, verification is not a one time activity. A static check, a lint rule,
a dependency boundary tool, or even a simple continuous integration search
for the vendor SDK's import path outside the designated adapter module, that
fails the build when a new, unauthorised call site to the vendor's SDK
appears outside the adapter layer, is the most reliable ongoing verification
available, because it turns an architectural intention into an enforced
constraint rather than a convention that erodes under deadline pressure.

**Verifying the switching cost estimate stays current.** Because the
estimate from refactoring step 2 is the number that justifies, or does not
justify, further investment, it is worth re-checking periodically,
particularly after any significant feature that touches the boundary, rather
than treating it as a one time calculation that stays valid indefinitely.

## 16. Observability signals

Vendor lock-in itself does not emit a runtime signal the way a bug does,
because the system usually works correctly right up until the day the vendor
relationship changes. The observability concern here is organisational and
architectural rather than a metric on a dashboard, though several concrete
signals are worth tracking deliberately.

- **Coupling surface area over time.** The count of distinct files or modules
  that import a given vendor's SDK directly, tracked over successive
  releases. A number that is flat or shrinking, concentrated inside a
  defined adapter layer, indicates the boundary is holding. A number that is
  growing across unrelated modules indicates re-accumulation.
- **Vendor contract and pricing change frequency.** Tracking, as a matter of
  process rather than tooling, how often a given vendor has changed its
  pricing model, terms of service, or licensing terms over the relationship's
  lifetime, since a rising frequency, as with Oracle's Java licensing changes
  or HashiCorp's 2023 relicensing, is itself a leading indicator that the
  switching cost risk is becoming a live concern rather than a theoretical
  one.
- **API deprecation notice windows.** The length of notice a vendor typically
  gives before deprecating an API version the system depends on. A shrinking
  window, or a deprecation announced with less lead time than the system's
  own release cadence can absorb, is a concrete early warning signal.
- **Time to estimate a hypothetical migration.** How long it currently takes
  the team to produce even a rough estimate of what switching a given vendor
  dependency would cost, re measured periodically. A team that can no longer
  answer this within a day or two, because the coupling has grown too diffuse
  to reason about, has lost visibility into its own risk, independent of
  whether a migration is ever actually planned.
- **Support and reliability trend for the vendor relationship itself.**
  Ticket response times, incident frequency attributable to the vendor, and
  account management responsiveness, tracked as a simple qualitative trend
  over quarters, since a deteriorating vendor relationship is one of the
  clearest practical triggers for reassessing an accepted lock-in decision.

## 17. Security and privacy implications

Vendor lock-in carries security and privacy implications distinct from, and
in some respects opposed to, the availability and cost implications discussed
above.

**Concentration of the attack surface.** A single, deeply integrated vendor
relationship means a single vendor's security posture, breach history, and
incident response quality become directly load bearing for the consuming
system's own security, with limited ability to compensate independently. A
compromise of the vendor's control plane, credentials, or supply chain
propagates directly, and the consuming organisation has fewer independent
controls to fall back on than it would with a more distributed architecture.

**Reduced ability to respond to a vendor side incident quickly.** If a vendor
suffers a security incident that requires customers to rotate credentials,
change configurations, or temporarily suspend a capability, a deeply coupled
system with the vendor's specifics scattered through its codebase and
infrastructure takes longer to respond safely than a system where the vendor
integration is confined to a bounded adapter layer that can be
reconfigured, disabled, or swapped in one place.

**Data residency and cross border transfer risk.** For personal or regulated
data, deep coupling to a single vendor's specific regional infrastructure and
data handling practices, adopted without an abstraction that could allow
switching to a vendor with different jurisdictional guarantees, directly
constrains an organisation's ability to respond to changing data protection
law, this is a substantial part of the motivation behind the EU's regulatory
attention described in section 3 and section 9. An abstraction boundary at
the storage or processing layer does not eliminate this risk, since the
underlying data still resides wherever the current adapter's vendor stores
it, but it materially lowers the engineering cost of responding once a
residency requirement changes, compared to a system with the vendor's
storage API called from every module that touches the data.

**The mitigation itself is not risk free.** An abstraction layer,
particularly one designed to support multiple vendors, is itself an
additional piece of code with its own attack surface, and a poorly designed
port can introduce authorization or validation gaps that neither the domain
logic nor any single adapter fully owns, if responsibility for enforcing
security invariants is not clearly assigned to one side of the boundary.
This entry does not treat that as a reason to avoid the mitigation, but it is
a genuine cost that a careful design must account for, consistent with this
dimension's role throughout the catalog, naming the security implication
honestly rather than presenting either the anti-pattern or its remedy as
free of trade-offs.

## 18. References

1. Paul Klemperer, "Markets with Consumer Switching Costs", *Quarterly
   Journal of Economics*, vol. 102, no. 2, 1987, pp. 375 to 394. Abstract
   confirmed via
   [academic.oup.com/qje/article-abstract/102/2/375/1859061](https://academic.oup.com/qje/article-abstract/102/2/375/1931195),
   verified 2026-08-02.
2. Cloud Native Computing Foundation, "About the CNCF",
   [cncf.io/about](https://www.cncf.io/about/), verified 2026-08-02.
3. 37signals, "Leaving the Cloud",
   [basecamp.com/cloud-exit](https://basecamp.com/cloud-exit), verified
   2026-08-02.
4. Azul Systems, "Oracle Java Pricing Change FAQ",
   [azul.com/products/core/oracle-pricing-change-faq](https://www.azul.com/products/core/oracle-pricing-change-faq/),
   verified 2026-08-02.
5. "OpenTofu", Wikipedia,
   [en.wikipedia.org/wiki/OpenTofu](https://en.wikipedia.org/wiki/OpenTofu),
   verified 2026-08-02.
6. OpenTofu, "OpenTofu Announces Fork of Terraform",
   [opentofu.org/blog/opentofu-announces-fork-of-terraform](https://opentofu.org/blog/opentofu-announces-fork-of-terraform/),
   verified 2026-08-02.
7. Netflix / Spinnaker project, "Concepts",
   [spinnaker.io/docs/concepts](https://spinnaker.io/docs/concepts/),
   verified 2026-08-02.
8. European Commission, "The Digital Markets Act",
   [digital-markets-act.ec.europa.eu/index_en](https://digital-markets-act.ec.europa.eu/index_en),
   verified 2026-08-02.
9. Alistair Cockburn, "Hexagonal Architecture", original description of the
   ports and adapters pattern this entry's mitigation is grounded in,
   [alistair.cockburn.us/hexagonal-architecture](https://alistair.cockburn.us/hexagonal-architecture/),
   verified 2026-08-02.
10. Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
    Software*, Addison-Wesley, 2003, chapter 14, for the Anti-Corruption
    Layer pattern referenced in section 13.

## Code examples

The pattern being demonstrated is the mitigation, not the anti-pattern
itself, since the anti-pattern is simply the absence of the boundary shown
below. Each example defines a small storage port from the domain's own
vocabulary, then provides one concrete adapter, proving the port is not
merely a relabelling of the vendor's shape, per the fourth failure mode in
section 11.

### TypeScript

```typescript
interface Order {
  id: string;
  total: number;
}

interface OrderRepository {
  save(order: Order): Promise<void>;
  findById(id: string): Promise<Order | null>;
}

class InMemoryOrderRepository implements OrderRepository {
  private store = new Map<string, Order>();

  async save(order: Order): Promise<void> {
    this.store.set(order.id, order);
  }

  async findById(id: string): Promise<Order | null> {
    return this.store.get(id) ?? null;
  }
}

class OrderService {
  constructor(private repo: OrderRepository) {}

  async placeOrder(id: string, total: number): Promise<void> {
    if (total <= 0) {
      throw new Error("total must be positive");
    }
    await this.repo.save({ id, total });
  }

  async getOrder(id: string): Promise<Order | null> {
    return this.repo.findById(id);
  }
}

async function main() {
  const service = new OrderService(new InMemoryOrderRepository());
  await service.placeOrder("ord-1", 42.5);
  const found = await service.getOrder("ord-1");
  console.log(found);
}

main();
```

### Go

```go
package main

import (
	"errors"
	"fmt"
)

type Order struct {
	ID    string
	Total float64
}

type OrderRepository interface {
	Save(order Order) error
	FindByID(id string) (Order, bool)
}

type InMemoryOrderRepository struct {
	store map[string]Order
}

func NewInMemoryOrderRepository() *InMemoryOrderRepository {
	return &InMemoryOrderRepository{store: make(map[string]Order)}
}

func (r *InMemoryOrderRepository) Save(order Order) error {
	r.store[order.ID] = order
	return nil
}

func (r *InMemoryOrderRepository) FindByID(id string) (Order, bool) {
	order, ok := r.store[id]
	return order, ok
}

type OrderService struct {
	repo OrderRepository
}

func NewOrderService(repo OrderRepository) *OrderService {
	return &OrderService{repo: repo}
}

func (s *OrderService) PlaceOrder(id string, total float64) error {
	if total <= 0 {
		return errors.New("total must be positive")
	}
	return s.repo.Save(Order{ID: id, Total: total})
}

func main() {
	service := NewOrderService(NewInMemoryOrderRepository())
	if err := service.PlaceOrder("ord-1", 42.5); err != nil {
		panic(err)
	}
	order, found := service.repo.FindByID("ord-1")
	fmt.Println(order, found)
}
```

### Python

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class Order:
    id: str
    total: float


class OrderRepository(ABC):
    @abstractmethod
    def save(self, order: Order) -> None:
        raise NotImplementedError

    @abstractmethod
    def find_by_id(self, order_id: str) -> Optional[Order]:
        raise NotImplementedError


class InMemoryOrderRepository(OrderRepository):
    def __init__(self) -> None:
        self._store: dict[str, Order] = {}

    def save(self, order: Order) -> None:
        self._store[order.id] = order

    def find_by_id(self, order_id: str) -> Optional[Order]:
        return self._store.get(order_id)


class OrderService:
    def __init__(self, repo: OrderRepository) -> None:
        self._repo = repo

    def place_order(self, order_id: str, total: float) -> None:
        if total <= 0:
            raise ValueError("total must be positive")
        self._repo.save(Order(id=order_id, total=total))

    def get_order(self, order_id: str) -> Optional[Order]:
        return self._repo.find_by_id(order_id)


if __name__ == "__main__":
    service = OrderService(InMemoryOrderRepository())
    service.place_order("ord-1", 42.5)
    print(service.get_order("ord-1"))
```

A fourth language, Rust, is omitted deliberately here. The pattern's essential
shape, an interface owned by the domain, one adapter implementing it, is
fully demonstrated by the three examples above, and a Rust trait based
version would add no new structural insight over the Go and TypeScript
interfaces already shown; the repository family entries elsewhere in this
catalog carry a Rust example where the trait object dispatch trade-offs are
the point being made.
