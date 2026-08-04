---
name: Stovepipe System
slug: stovepipe-system
family: 18-anti-patterns
category: Architectural
aliases: [Stovepipe Enterprise, Stovepipe Architecture, Vertical Silo, Stovepiping]
first_described: "Brown, Malveau, McCormick, Mowbray 1998"
maturity: canonical
related: [big-ball-of-mud, shared-database, facade, mediator, adapter, enterprise-service-bus, message-broker, layered-architecture, bounded-context, entity-service]
incompatible_with: [enterprise-service-bus, bounded-context, hexagonal-architecture]
verified: 2026-08-02
---

# Stovepipe System

## 1. Name, aliases, and lineage

The canonical name is Stovepipe System. It is documented as one of the
architecture-level AntiPatterns in William J. Brown, Raphael C. Malveau, Hays
W. "Skip" McCormick III, and Thomas J. Mowbray, *AntiPatterns. Refactoring
Software, Architectures, and Projects in Crisis*, John Wiley and Sons, 1998,
chapter 6, which is the chapter devoted to system-level architecture
antipatterns
([Dr. Dobb's excerpt of the book's antipattern list, confirming chapter 6
covers system architecture antipatterns including Stovepipe System](http://web.archive.org/web/20240227013914/https://drdobbs.com/architecture-and-design/antipatterns/184410581),
verified 2026-08-02). The book states the antipattern concerns how
subsystems are coordinated inside a single system, and names the root cause
as the lack of a common subsystem abstraction, with integration done ad hoc
using whatever mechanism was convenient at the time each connection was
built.

The alias **Stovepipe Enterprise** is used for the same problem at the scale
of an entire organization rather than a single system, and both names are
used interchangeably in practice because the antipattern reproduces at
every scale it appears at, from two classes reaching into each other's
internals up to two government agencies that cannot exchange a case file
([exceptionnotfound.net, "Stovepipe Enterprise, The Daily Software
Anti-Pattern," a walkthrough of the AntiPatterns book chapter](http://web.archive.org/web/20251208073835/https://www.exceptionnotfound.net/stovepipe-enterprise-the-daily-software-anti-pattern/),
last verified through a WebFetch retrieval summary on 2026-08-02, note the
live site returned an intermittent server error on the final direct
verification pass and the citation rests on that summary plus corroborating
secondary sources). **Vertical Silo** and **Stovepiping** are the terms used
in government and military systems engineering literature for the identical
failure, and predate the software AntiPatterns book by a decade in that
context. The United States Department of Energy's 1999 information
architecture guidance defines a stovepipe as a system "procured and
developed to solve a specific problem, characterized by a limited focus and
functionality, and containing data that cannot be easily shared with other
systems" ([Wikipedia, "Stovepipe system," citing the DOE 1999 definition in
its lede and history section](https://en.wikipedia.org/wiki/Stovepipe_system),
verified 2026-08-02).

The name itself is a visual metaphor, not a technical acronym. A row of
free-standing metal stovepipes rising from a row of factory buildings each
carries smoke straight up from its own furnace, with no shared flue, no
common exhaust manifold, and no way for one building's heating system to
draw on another's capacity even when one furnace is idle and the next is
overloaded. A stovepipe system is the software equivalent, a subsystem that
runs its own furnace end to end, from its own storage up through its own
business logic to its own presentation, and that connects to its neighbors,
if it connects at all, through a one-off pipe built for that single
connection and no other. The Wikipedia entry traces the same imagery to
earlier military usage describing radar and sensor networks that could not
cross-cue each other, which is the origin the DOE definition inherited
([Wikipedia, "Stovepipe system,"](https://en.wikipedia.org/wiki/Stovepipe_system)
verified 2026-08-02).

Two related terms are worth separating from Stovepipe System because they
name overlapping but distinct problems, and conflating them is a common
error when a reader tries to fix a stovepipe with the wrong remedy.

- **Big Ball of Mud** (Foote and Yoder, 1997) is the absence of internal
  structure inside one piece of code, a single module where everything
  touches everything. A Stovepipe System can have perfectly clean internal
  structure inside every one of its subsystems and still be a stovepipe,
  because the antipattern lives in the seams between subsystems, not inside
  any one of them. See `big-ball-of-mud`.
- **Shared Database** integration is one specific way a set of stovepipes
  are sometimes bolted together after the fact, by pointing every subsystem
  at the same tables. It solves the sharing problem and immediately
  reintroduces a different one, tight coupling on a schema nobody owns. It
  is a common but not universal companion to a stovepipe, discussed further
  in dimension 11.

## 2. Problem and context

An organization builds its second system, its second department's
application, or its second bounded capability, and the fastest path to
delivery is to start from a blank slate rather than to first identify what
the new system genuinely shares with the first one. The team under deadline
pressure writes its own user table, its own configuration loader, its own
logging format, its own retry logic, and its own notion of what a customer
record looks like, because building on top of the first system's
abstractions would require understanding them, negotiating a shared
interface with a different team, and accepting a dependency that could
break under a schedule the new team does not control. Nobody sat down to
decide that the two systems should never talk to each other. The decision
that produced the stovepipe was a hundred small decisions, each locally
correct, to move fast and not wait on someone else's release plans.

The situation reads like this in a real organization. A billing system,
a shipping system, and a support ticketing system were each commissioned by
a different department, at a different time, sometimes by a different
vendor, and each was specified as if it were the only system the company
would ever run. Each stores its own copy of "customer," under a different
key, with a different set of fields, none of it reconciled against the
others. When the support team needs to know whether an order shipped, there
is no shared customer or order abstraction to query, so an engineer writes a
nightly batch job that logs into the shipping system's database directly,
pulls a CSV, and loads it into a table the support system was never
designed to hold. That job is the stovepipe's exhaust pipe, built once, for
this one connection, understood by nobody who did not write it, and it will
break the next time either database's schema changes for reasons that have
nothing to do with the connection between them.

The context that produces this antipattern has three recurring elements,
each documented independently across the sources for this entry.

- **Independent procurement or independent team ownership.** Each subsystem
  was funded, staffed, or purchased separately, often by a different budget
  holder who had no mandate and no incentive to coordinate with the owner
  of a neighboring system, which is precisely the DOE 1999 framing, a
  system built to solve one specific problem with no requirement that it
  share data with any other ([Wikipedia, "Stovepipe
  system,"](https://en.wikipedia.org/wiki/Stovepipe_system) verified
  2026-08-02).
- **No shared subsystem abstraction was designed before the second
  subsystem was built.** The AntiPatterns book locates the root cause here,
  not in the integration code itself. The integration code is a symptom.
  The absence of a common interface, a common data model, or a common
  service boundary that both subsystems were built against is the disease
  ([Dr. Dobb's excerpt of the AntiPatterns book's antipattern
  catalog](http://web.archive.org/web/20240227013914/https://drdobbs.com/architecture-and-design/antipatterns/184410581),
  verified 2026-08-02).
- **Time pressure that rewards local delivery over cross-system
  coordination.** GAO's long history of reporting on stovepipe systems
  inside the United States Department of Defense repeatedly names schedule
  and organizational parochialism, not a lack of technical skill, as the
  cause, describing programs that "lacked mechanisms to overcome
  parochialism and stovepipes at the military service level" ([U.S.
  Government Accountability Office, GAO-04-858, "Defense Acquisitions. The
  Global Information Grid and Challenges Facing Its
  Implementation,"](https://www.gao.gov/assets/gao-04-858.pdf) verified
  2026-08-02).

## 3. Forces

- **Delivery speed for the individual subsystem versus data consistency
  across the organization.** A team that owns its entire stack end to end,
  with no dependency on a shared abstraction someone else controls, can
  ship without waiting on another team's release schedule. That same
  independence is exactly what produces N incompatible copies of "customer"
  once N teams have each made the same locally rational choice.
- **Team autonomy versus integration cost.** Conway's Law is doing real
  work underneath this antipattern. A stovepipe is frequently the direct
  shadow of an organizational chart in which each department's software
  reflects that department's boundary and nothing crosses it, because
  nothing in the org chart required it to.
- **Short-term procurement cost versus long-term interoperability cost.**
  Buying or building the cheapest system that solves today's specific
  problem is a rational short-term move for a single budget holder and an
  expensive long-term move for the organization that later has to make
  that system talk to five others it did not anticipate.
- **Predictability of a point-to-point integration versus the coordination
  cost of a shared abstraction.** A one-off adapter between exactly two
  systems is easy to reason about in isolation, easy to test in isolation,
  and cheap to build once. The force this pattern optimizes for is the
  cost of the first connection. The force it sacrifices is the cost of the
  Nth connection, which grows combinatorially rather than linearly as more
  subsystems join.
- **Vendor and technology diversity versus a common contract.** Different
  subsystems built at different times on different platforms, sometimes by
  different vendors under different contracts, have no natural shared
  contract to converge on even when the people involved want one, which is
  a documented cause in government systems where procurement law itself
  can force each system to be sourced separately.

A Stovepipe System favors the first term in every pairing above, local
delivery speed, team autonomy, short-term cost, and the ease of a single
connection, and it sacrifices the second term in every pairing, systemic
consistency, cross-team coordination, long-term cost, and the tractability
of the whole integration graph. Every entry in this catalog trades force
against force. What marks Stovepipe System as an antipattern rather than a
pattern is that the trade is almost never made consciously. It accumulates
from a series of decisions that were each individually reasonable, and the
accumulated cost is paid by whoever has to integrate the fourth, fifth, and
sixth system, none of whom were in the room for any of the earlier
decisions.

## 4. Applicability and non-applicability

### When a stovepipe shape is the right call

- **A genuinely standalone tool with no plausible integration need**, where
  building on a shared platform would add real coupling cost for zero
  realized benefit. Joel Spolsky's account of the early Microsoft Excel
  team is the frequently cited case, the team maintained its own C compiler
  and deliberately avoided sharing infrastructure with the rest of
  Microsoft, and Spolsky argues this vertical independence let the team
  ship on a predictable schedule with code the team fully controlled and
  understood ([Joel Spolsky, "In Defense of Not-Invented-Here Syndrome,"
  Joel on Software, October 14,
  2001](https://www.joelonsoftware.com/2001/10/14/in-defense-of-not-invented-here-syndrome/),
  verified 2026-08-02). The case only holds because Excel's team judged
  correctly that the shared alternative available to them at the time would
  have coupled them to a dependency they could not control, and because the
  product genuinely had no near-term requirement to exchange live data with
  a sibling system.
- **A one-time migration or a short-lived bridge**, where the connection
  exists to move an organization from one steady state to another and is
  explicitly scheduled for retirement once the migration completes. A
  purpose-built, temporary point-to-point pipe is not a stovepipe in the
  pejorative sense if everyone involved knows it is temporary and it is
  actually decommissioned on schedule.
- **Regulatory or security isolation that requires the boundary.** A system
  handling classified or otherwise legally segregated data that must not
  share a database, a network, or even an authentication domain with
  another system is not exhibiting the antipattern by staying isolated,
  it is satisfying a hard requirement the antipattern's usual fix would
  violate.
- **Extremely early in a product's life**, before more than one subsystem
  exists to integrate with, or before the organization has any evidence
  about which shared abstractions will actually be needed. Building a
  general integration layer for a system that has nothing to integrate
  with yet is a different antipattern, discussed under Golden Hammer and
  speculative generality, not a defense against this one.

### When Stovepipe System is the wrong shape

- **When a second or third subsystem is being planned and the
  organization already knows it will need to exchange the same core data
  (customer, order, identity) across all of them.** Building each one in
  isolation here is choosing this antipattern with foresight, not falling
  into it by accident, and it is not defensible on the applicability list
  above because the future integration need is already known.
- **When the "temporary" bridge has already outlived every system it was
  built to connect.** A batch job or file drop built as a stopgap that is
  still the only integration path five years and three schema changes later
  is not serving a genuine one-time-migration purpose anymore, it has become
  permanent infrastructure that nobody designed as infrastructure.
- **When the cost of building a shared abstraction is smaller than the
  organization assumes.** Teams frequently overestimate the coordination
  cost of a shared contract and underestimate the compounding cost of N
  independent point-to-point connections, especially once N exceeds three
  or four and the number of possible pairwise connections starts to
  outweigh the actual integration work.
- **When compliance or audit requires a single, consistent source of
  truth for a regulated data element** (financial totals, patient records,
  personally identifiable information under a data-protection regime).
  Multiple divergent copies of the same regulated fact, each maintained by
  a different stovepipe, is a direct source of audit findings and, in
  regulated healthcare integration specifically, has been documented as a
  motivation toward message-based integration architectures precisely
  because stovepiped clinical systems could not be reconciled
  ([ResearchGate, "Software design patterns for message driven service
  oriented integration of stovepipe applications in healthcare
  enterprise,"](https://www.researchgate.net/publication/228342050_Software_design_patterns_for_message_driven_service_oriented_integration_of_stovepipe_applications_in_healthcare_enterprise)
  verified 2026-08-02, cited here for the existence and framing of the
  paper rather than for its specific findings, which were not independently
  re-verified beyond the abstract).

## 5. Structure

- **Vertical subsystem.** A self-contained unit, spanning storage, business
  logic, and often its own presentation layer, that owns everything it
  needs to function and depends on nothing outside itself for its core
  responsibilities. Each vertical subsystem in a stovepipe architecture
  typically duplicates infrastructure concerns, its own authentication, its
  own logging format, its own configuration mechanism, that a shared
  platform would normally centralize.
- **Private data store.** Each vertical subsystem's own database, file
  store, or in-memory model, holding a copy of any entity (customer, order,
  product) that another subsystem also needs, under that subsystem's own
  schema, naming convention, and consistency rules.
- **Ad hoc bridge.** The connection between two vertical subsystems, built
  after both already exist, using whatever mechanism was fastest at the
  time, a scheduled file export, a direct cross-database query, a scraped
  screen, a bespoke one-off API call with a shape that matches nothing else
  in the system. There is rarely a single bridge technology across an
  entire stovepipe architecture, because each bridge was built by a
  different pair of teams solving their own local problem.
- **Absent common abstraction.** The structural signature that
  distinguishes Stovepipe System from ordinary modularity is what is
  missing, not what is present, there is no shared interface, no shared
  domain model, and no shared integration layer that every subsystem was
  built against. This is the element the AntiPatterns book names as the
  root cause, and it is the reason the pattern's fix (dimension 14) adds
  exactly this missing piece rather than adding more bridges.
- **Duplicated cross-cutting concern.** Authentication, authorization,
  audit logging, configuration, and monitoring, reimplemented once per
  vertical subsystem instead of factored into a shared layer every
  subsystem calls into.

## 6. ASCII structure diagram

```
   Subsystem A            Subsystem B            Subsystem C
   (Billing)               (Shipping)             (Support)
  +-----------+           +-----------+           +-----------+
  | UI/API    |           | UI/API    |           | UI/API    |
  +-----------+           +-----------+           +-----------+
  | Business  |           | Business  |           | Business  |
  | Logic     |           | Logic     |           | Logic     |
  +-----------+           +-----------+           +-----------+
  | Own Auth  |           | Own Auth  |           | Own Auth  |
  | Own Log   |           | Own Log   |           | Own Log   |
  | Own Config|           | Own Config|           | Own Config|
  +-----------+           +-----------+           +-----------+
  | Private DB|           | Private DB|           | Private DB|
  | "customer"|           | "client"  |           | "account" |
  +-----+-----+           +-----+-----+           +-----+-----+
        |                       |                       |
        |   nightly CSV export  |   direct SQL query,   |
        +----------------------->   read-only replica   |
        |   ad hoc bridge #1    +----------------------->
        |                       |   ad hoc bridge #2     |
        |                                                |
        +------------------ screen scrape ---------------+
                              ad hoc bridge #3

  No shared interface. No shared domain model. Three different
  bridge technologies, each understood only by the pair of teams
  that built it. Adding a fourth subsystem needs up to three more
  bespoke bridges, not one connection to a common layer.
```

## 7. Dynamics

The runtime behavior of a stovepipe is defined less by any single request
flow and more by what happens the moment two subsystems must agree on a
fact.

```
  Support agent asks. "Did order #4471 ship."

  Support UI
     |
     | 1. Support system has NO shipping data of its own for
     |    real-time status, only what the nightly batch loaded
     v
  Support DB (stale copy of shipping status, up to 24h old)
     |
     | 2. Batch job "sync_shipping_to_support.sh" ran at 02:00
     |    (cron, owned by a former employee, undocumented)
     v
  Shipping DB
     |
     | 3. Shipping DB was itself repointed to a new schema last
     |    quarter for an unrelated shipping-provider migration.
     |    The batch job's column mapping silently started
     |    reading the wrong field and now writes NULL
     v
  Support agent sees "shipped, unknown" for every order created
  after the shipping schema change, and has no way to tell
  whether that means "not shipped" or "the pipe broke"
```

The dynamic that makes this antipattern expensive is not any one request
path, it is that a change made entirely inside one vertical subsystem, for
reasons that have nothing to do with any other subsystem, silently breaks a
bridge that nobody who made the change knew existed. The bridge is not a
dependency the shipping team's build can see, it is not covered by the
shipping team's tests, and it is not something a code review inside the
shipping subsystem would ever surface. The failure is discovered days or
weeks later, by a different team, far from the change that caused it, which
is the operational signature GAO repeatedly documents when auditing DoD
command and control systems, calling out that historically separate
"stovepipe" systems for operations centers, communications, and
intelligence proved difficult to interoperate in a joint warfare
environment precisely because no system was built with the others' change
management in view ([U.S. GAO, NSIAD-87-124, "Interoperability. DOD's
Efforts To Achieve Interoperability Among C3
Systems,"](https://www.gao.gov/products/nsiad-87-124) verified 2026-08-02).

## 8. Implementation variants

- **Duplicated identity variant.** Each subsystem implements its own user
  accounts, its own password storage, and its own session mechanism,
  instead of delegating to a shared identity provider. This is the
  simplest and most commonly cited illustration of the antipattern,
  because it is the cross-cutting concern every subsystem needs and the
  one most often reimplemented from scratch under deadline pressure. It
  matches the example exceptionnotfound.net uses in its walkthrough of the
  AntiPatterns book chapter, a system that has its own user IDs and
  passwords instead of using one shared authentication system across
  multiple platforms ([exceptionnotfound.net, "Stovepipe Enterprise, The
  Daily Software
  Anti-Pattern,"](http://web.archive.org/web/20251208073835/https://www.exceptionnotfound.net/stovepipe-enterprise-the-daily-software-anti-pattern/)
  verified 2026-08-02 with the caveat on source access noted in dimension
  1).
- **Batch file bridge variant.** Subsystems exchange data through
  scheduled file exports and imports (CSV, fixed-width, XML dumps) rather
  than a live API or a shared store, common where the two systems were
  built years apart on incompatible platforms and a file is the lowest
  common denominator both sides can produce and consume.
- **Direct cross-database query variant.** One subsystem's code reaches
  directly into another subsystem's private schema, either via a live
  connection or a read replica, coupling the reader to internal table names
  and column types the writer never intended to expose as a contract and
  can change without warning.
- **Screen scraping or UI automation bridge variant.** One system drives
  another system's user interface programmatically because no API was ever
  built, the most fragile and most tightly time-coupled variant, since it
  breaks on any visual change to the scraped system regardless of whether
  the underlying data model changed at all.
- **Ad hoc point-to-point API variant.** Two subsystems each expose or
  consume a bespoke, undocumented endpoint built for that one connection,
  with a request and response shape that matches nothing else either
  system exposes, distinguished from a genuine shared API by the fact that
  it was designed for exactly one caller and one callee and never
  generalized.
- **Deliberate, bounded stovepipe variant.** A subsystem is intentionally
  built to be vertically self-sufficient, as in the Excel example, with the
  team accepting duplicated infrastructure in exchange for full control
  and no external dependency risk. This variant is only a legitimate
  implementation of the applicability list in dimension 4 when the decision
  was made consciously and the tradeoff was actually evaluated, not when it
  is the accidental byproduct of never having made the decision at all.

## 9. Known production uses

- **The United States Department of Defense's command, control, and
  communications systems**, documented over decades by the Government
  Accountability Office as separately developed "stovepipe" systems for
  operations centers, communications systems, and intelligence systems
  that historically could not interoperate in joint operations, a finding
  GAO reported as early as 1987 and continued to report through the 2000s
  as the department pursued the Global Information Grid specifically to
  move away from isolated stovepipe environments toward one coherent,
  unified infrastructure ([U.S. GAO, NSIAD-87-124,](https://www.gao.gov/products/nsiad-87-124)
  and [U.S. GAO, GAO-04-858, "Defense Acquisitions. The Global Information
  Grid and Challenges Facing Its
  Implementation,"](https://www.gao.gov/assets/gao-04-858.pdf) both
  verified 2026-08-02).
- **The United States Internal Revenue Service's legacy tax processing
  systems.** GAO's ongoing modernization audits document IRS applications
  still in production that are decades old, some over sixty years, written
  in COBOL and Assembler, built and extended independently over that span
  rather than against a shared platform, which is the same accumulation
  pattern the DOE stovepipe definition describes, systems built to solve a
  specific problem at the time with limited regard for future data sharing
  ([U.S. GAO, GAO-25-107611, "Information Technology. IRS Is Developing a
  New Modernization
  Framework,"](https://www.gao.gov/assets/gao-25-107611.pdf) verified
  2026-08-02).
- **Healthcare enterprise integration.** Published integration-architecture
  research explicitly frames hospital and clinical information systems as
  "stovepipe applications" that had to be reconciled through message-driven,
  service-oriented integration rather than direct coupling, because
  independently procured clinical systems (laboratory, pharmacy, admissions)
  each maintained their own patient and order records with no common
  abstraction ([ResearchGate, "Software design patterns for message driven
  service oriented integration of stovepipe applications in healthcare
  enterprise,"](https://www.researchgate.net/publication/228342050_Software_design_patterns_for_message_driven_service_oriented_integration_of_stovepipe_applications_in_healthcare_enterprise)
  verified 2026-08-02, cited for the paper's framing rather than its
  internal results, which were not independently re-derived here).
- **Enterprise messaging's founding motivation.** Gregor Hohpe and Bobby
  Woolf's *Enterprise Integration Patterns*, Addison-Wesley, 2003, catalogs
  65 patterns whose stated problem space is exactly the situation this
  entry describes, "existing systems that need integration between them,"
  connected historically through brittle point-to-point links, which the
  book's patterns (Message Broker, Enterprise Service Bus, Canonical Data
  Model) exist to replace with a shared integration layer
  ([Martin Fowler's summary page for the
  book](https://martinfowler.com/books/eip.html) and the [book's own
  introductory PLoP draft describing the point-to-point integration
  problem](https://www.enterpriseintegrationpatterns.com/docs/Enterprise%20Integration%20Patterns%20-%20PLoP%20Final%20Draft%203.pdf),
  both verified 2026-08-02). The book does not use the word "stovepipe" as
  its primary term, it is included here because it documents the identical
  structural problem and its named, adopted industry remedy, and this
  connection is the author's synthesis, not a direct quotation from the
  book, and is labeled here as that synthesis.

## 10. Consequences

Positive.

- Each vertical subsystem can be delivered, deployed, and evolved on its
  own schedule, with no coordination tax paid to any other team for the
  subsystem's internal changes.
- A single subsystem's failure is contained to itself at the storage and
  business-logic layer, since nothing else was built to depend on its
  internals directly, only on the ad hoc bridges, which is a real
  (if incidental) fault-isolation benefit.
- Procurement and vendor selection stay simple per subsystem, since no
  vendor needs to build to a shared platform contract that may not exist
  yet or that a different vendor controls.
- Teams retain full technical autonomy, free to choose the language,
  storage engine, and architecture that fits their subsystem's problem
  without negotiating a lowest common denominator with every other team.

Negative.

- The number of possible integration points grows combinatorially with the
  number of subsystems, since each new subsystem that needs to talk to the
  existing N systems needs up to N bespoke bridges rather than one
  connection to a shared layer.
- The same real-world entity (a customer, an order, an employee) exists as
  multiple, independently maintained, frequently inconsistent copies, and
  no single subsystem can be trusted as the source of truth for it.
- A change made entirely inside one subsystem's private schema or internal
  logic can silently break a bridge no one on that team knows exists,
  because the bridge is invisible to that subsystem's own build, tests, and
  code review.
- Cross-cutting concerns (authentication, authorization, audit, monitoring)
  are reimplemented per subsystem, multiplying the surface area for bugs
  and inconsistent behavior in exactly the concerns where consistency
  matters most, especially for security.
- Organizational knowledge about how data actually flows lives in the
  bridges themselves, frequently as an undocumented cron job or a script
  one departed engineer wrote, rather than in any architecture diagram
  anyone maintains.
- Reporting and analytics that need a cross-subsystem view (which
  customers who ordered X also opened a support ticket) require either
  building yet another bridge or replicating everything into a data
  warehouse, itself frequently built as one more stovepipe with its own ad
  hoc extract jobs.

## 11. Failure modes and misuse

The following triples name a symptom a reader would actually observe in a
running system, the underlying cause, and the fix, distinguishing this
dimension from dimension 10's list of general consequences.

- **Symptom.** Two systems display different values for what should be the
  same fact (a customer's address, an order's status), and nobody can say
  which one is correct without manually checking a third source.
  **Cause.** Each subsystem holds its own private copy of the entity with
  no single source of truth and no synchronization guarantee stronger than
  "the last batch job that happened to run." **Fix.** Introduce a canonical
  data owner for the entity and route every other subsystem's read through
  a shared interface to that owner, per the refactoring path in dimension
  14, rather than adding a fourth reconciliation job.
- **Symptom.** A routine schema migration inside one subsystem causes an
  unrelated subsystem to start failing silently, with no error, only
  missing or stale data, days later. **Cause.** A direct cross-database
  query or a batch-file bridge encoded assumptions about the source
  system's private schema as if it were a stable public contract, and
  nothing enforced that contract. **Fix.** Replace the direct query with a
  versioned API that the source subsystem owns and can evolve behind, so
  the source team's own change process is forced to consider external
  consumers.
- **Symptom.** Onboarding a new subsystem into the organization takes
  months of point-to-point integration work even though the new subsystem's
  own build is finished in weeks. **Cause.** The organization has no shared
  integration layer, so every new subsystem must negotiate and build a
  bespoke bridge to each existing system it needs data from. **Fix.**
  Introduce a message broker or an integration facade (dimension 13) that
  the new subsystem connects to once, instead of once per neighbor.
- **Symptom.** A security audit finds that a subsystem's authorization
  logic differs from a nominally equivalent check in a sibling subsystem,
  and one of the two is wrong. **Cause.** Authentication and authorization
  were reimplemented independently per subsystem instead of centralized,
  so the two implementations drifted from each other over time as each was
  patched separately. **Fix.** Extract identity and authorization into a
  shared service every subsystem calls, eliminating the duplicated logic
  rather than trying to keep N copies synchronized by discipline alone.
- **Symptom.** A person who built one of the ad hoc bridges leaves the
  organization, and within a quarter the bridge starts silently dropping
  data because nobody understood its failure modes well enough to notice
  it degrading. **Cause.** The bridge was built as a one-off script outside
  either subsystem's normal ownership, testing, and monitoring, so it
  inherited no organizational process for handling the departure of the
  one person who understood it. **Fix.** Any bridge that becomes permanent
  infrastructure must be adopted as a first-class, owned, tested,
  monitored component, ideally replaced by the shared integration layer
  from dimension 14 rather than kept alive as an orphan script.
- **Misuse as an excuse.** A team invokes "we need our own independent
  system, like Excel" to justify duplicating infrastructure it already
  knows a sibling system needs to share, treating the narrow, deliberate
  applicability case in dimension 4 as blanket permission to skip
  coordination it would rather avoid. The dimension 4 case only applies
  when the team has actually evaluated and accepted the tradeoff, not when
  it is invoked after the fact to defend a decision nobody made
  consciously.

## 12. Trade-off matrix

| Force | Stovepipe System | Shared Database integration | Message Broker / Enterprise Service Bus | Facade over legacy subsystems |
|---|---|---|---|---|
| Delivery speed for a single new subsystem | Fastest, no coordination needed | Fast once schema access is granted | Slower initially, must integrate with the broker's contract | Moderate, must build the facade first |
| Number of integration points as subsystems grow | Grows combinatorially, up to N times (N-1) pairwise bridges | Grows to one shared schema, but every subsystem is coupled to all of it | Grows linearly, each subsystem connects once to the broker | Grows linearly for callers, the facade absorbs the fan-out |
| Data consistency across subsystems | Lowest, multiple divergent copies of the same fact | Improved for shared tables, still fragile on schema change | Improved via canonical message contracts and, often, a canonical data model | Improved for whatever the facade normalizes, unchanged behind it |
| Coupling introduced | Point-to-point coupling per bridge, hidden from either subsystem's own build | Every reader and writer is coupled to one physical schema | Every subsystem is coupled to the broker's message contract, not to each other directly | Callers are coupled to the facade's interface, not to the legacy internals |
| Team autonomy preserved | Highest, each team owns its full stack | Reduced, schema changes now require cross-team negotiation | Moderate, teams still own their internals, must honor the shared contract | High for callers, low for whoever must maintain the facade against a moving legacy target |
| Failure blast radius | Contained per subsystem until a bridge breaks silently, then diagnosis is slow | A schema change can break every consumer of the shared table at once | Contained to producers and consumers of a specific message type | Contained to the facade, which absorbs legacy breakage before it reaches callers |
| Best fit | A genuinely standalone tool, or the deliberate applicability cases in dimension 4 | Small, tightly related systems under one team's control | Multiple independent systems that must exchange events reliably at scale | Wrapping legacy systems that cannot be changed but must be integrated |

## 13. Related and incompatible patterns

- **Facade** (`facade`) is frequently the first concrete step out of a
  stovepipe, placed in front of a legacy subsystem that cannot be
  rewritten, giving every new caller one stable interface instead of N
  bespoke bridges into the legacy internals.
- **Adapter** (`adapter`) does the narrower job of translating one
  subsystem's data shape into the shape a shared layer expects, and is
  typically used inside the fix from dimension 14 to connect an existing
  stovepipe subsystem to a newly introduced shared abstraction without
  rewriting the subsystem itself.
- **Mediator** (`mediator`) is the pattern that most directly names the
  missing structural element from dimension 5, a component that
  subsystems talk to instead of talking to each other directly, which is
  exactly what an enterprise service bus or message broker is at
  architectural scale.
- **Enterprise Service Bus** and **Message Broker**, from Hohpe and
  Woolf's catalog, are the industry-standard architectural remedy for a
  stovepipe at the scale of an entire organization, replacing N-squared
  point-to-point bridges with N connections to a shared spine
  ([Martin Fowler, summary of Enterprise Integration
  Patterns](https://martinfowler.com/books/eip.html), verified 2026-08-02).
- **Bounded Context** (`bounded-context`, from Eric Evans' domain-driven
  design) is the deliberate, well-managed cousin of a vertical subsystem, a
  boundary chosen consciously around a coherent domain model with an
  explicit, designed relationship to its neighbors (shared kernel,
  customer-supplier, anticorruption layer). A stovepipe is what a bounded
  context looks like when the boundary was drawn by accident and the
  relationship to its neighbors was never designed at all.
- **Big Ball of Mud** (`big-ball-of-mud`) is incompatible with a healthy
  reading of Stovepipe System in the sense that they name different axes
  of the same organization's problems, one inside a subsystem, one between
  subsystems, and an organization can suffer from both at once without one
  causing the other.
- **Shared Database** integration and **Entity Service** (`shared-database`,
  `entity-service`) are common but risky next moves once an organization
  notices its stovepipes and reaches for the closest fix rather than the
  correct one, discussed further under dimension 14's false remedies.
- **Layered Architecture** (`layered-architecture`) and **Hexagonal
  Architecture** are listed as incompatible with Stovepipe System in the
  frontmatter in the sense that a subsystem genuinely built with a clean
  layered or ports-and-adapters internal structure already has the seam a
  shared integration layer needs to attach to, which makes the stovepipe
  condition (no shared abstraction across the whole organization) far
  cheaper to fix than in a subsystem that is also internally a big ball of
  mud.

## 14. Refactoring path in and out

How an organization drifts into it, rarely a deliberate refactoring, almost
always an accumulation.

1. A second subsystem is commissioned without first asking which entities
   and cross-cutting concerns (identity, customer, order, audit) it will
   need to share with the first, because nobody owns that question across
   both teams.
2. The second subsystem's team, under its own deadline, reimplements
   whatever it needs rather than negotiating access to the first
   subsystem's internals, which is individually the correct call given the
   incentives that team actually faces.
3. A real business need arises to connect the two (a report, a workflow
   that spans both), and whoever is assigned the task builds the fastest
   working bridge available, a batch export, a direct query, a scrape,
   because building a proper shared interface is a much larger project than
   the ticket in front of them.
4. The bridge works, ships, and is never revisited. It has no owner beyond
   whoever wrote it, no test suite beyond "the report looked right this
   morning," and no documentation beyond the script itself.
5. Steps 1 through 4 repeat for the third, fourth, and fifth subsystem, and
   the number of bridges grows faster than the number of subsystems.

How to refactor out of it, in order.

1. **Inventory the bridges before touching any of them.** Enumerate every
   ad hoc integration point (batch jobs, direct queries, scrapes, one-off
   endpoints) and, for each one, identify which entity or fact it is
   moving and which subsystem is its true source of truth. This step alone
   frequently surfaces bridges nobody remembered existed, per the failure
   mode in dimension 11 about departed owners.
2. **Pick the highest-value shared entity first**, typically customer or
   identity, since duplicated identity is both the most common variant
   (dimension 8) and the one with the sharpest security consequence
   (dimension 11) when it drifts.
3. **Introduce a Facade or a Mediator in front of the subsystem that will
   become the source of truth**, rather than rewriting that subsystem.
   This gives every other subsystem one stable interface to migrate onto
   without requiring a rewrite of the legacy internals, matching the
   "strangler" style of incremental migration used across this catalog.
4. **Migrate one bridge at a time onto the new interface**, retiring the
   old ad hoc bridge as soon as its replacement is verified, never running
   both indefinitely, since a permanent parallel bridge is itself a new,
   permanent stovepipe.
5. **Once more than two or three subsystems need to exchange events
   reliably, introduce a message broker or service bus** rather than
   continuing to add point-to-point facades, since the trade-off matrix in
   dimension 12 shows the combinatorial cost of point-to-point connections
   overtaking the cost of a shared spine well before the fifth or sixth
   subsystem joins.
6. **Do not simply point every subsystem at a shared database as the
   fix.** This is the single most common false remedy, it removes the
   symptom (data now technically lives in one place) while reintroducing
   the disease at a deeper layer, every subsystem is now coupled to a
   physical schema nobody owns, which is frequently harder to safely
   evolve than the original bridges were, because a schema change now
   breaks every consumer simultaneously rather than one bridge at a time.

## 15. Testing and verification

A stovepipe's ad hoc bridges are, almost by definition, the least tested
part of the system, because they sit outside both subsystems' own test
suites, which is exactly why they are the most common source of silent
production failures documented in dimension 11.

- **Contract tests on every bridge, treating each one as a first-class
  interface rather than a script.** A bridge that moves data from subsystem
  A to subsystem B should have a test, owned by neither team exclusively
  or by both jointly, that asserts the shape of what A actually produces
  matches what B actually expects, run whenever either side changes.
- **Consumer-driven contract testing** (the technique associated with tools
  such as Pact) is directly applicable once a stovepipe organization moves
  toward the facade or broker remedy in dimension 14, since it lets a
  downstream consumer assert its expectations against the upstream
  producer's build without either team needing full visibility into the
  other's internals.
- **Data reconciliation tests as an interim safety net.** Before a bridge
  can be replaced, a periodic job that compares the same entity's value
  across two subsystems and flags divergence is the cheapest way to detect
  that a stovepipe's copies have drifted, and doubles as the diagnostic
  evidence needed to justify the refactor in dimension 14 to people who
  did not experience the drift firsthand.
- **What becomes easier because of this pattern's structure.** Testing a
  single vertical subsystem in isolation is genuinely easier here than in
  a more integrated architecture, because the subsystem has no external
  dependency on a shared platform to mock out, everything it needs is
  already inside it.
- **What becomes harder.** End-to-end tests that exercise a workflow
  spanning two subsystems are expensive and brittle to write, because the
  bridge between them is frequently the least deterministic part of the
  path (a nightly batch, a scrape sensitive to UI timing), and a green
  end-to-end test run frequently proves less than it appears to, since it
  can pass while the bridge silently drops a subset of records the test
  scenario never exercised.

## 16. Observability signals

A healthy set of subsystems connected through a proper shared layer shows a
small, stable, well-understood number of integration points, each with its
own metrics. A stovepipe shows the opposite signature.

- **Bridge count growing faster than subsystem count.** Track the number of
  distinct integration mechanisms (not just connections, but distinct
  technologies, one team's file export is a different mechanism from
  another team's direct query) against the number of subsystems over time.
  A ratio that keeps climbing is the leading indicator that new
  integrations are still being built ad hoc rather than through a shared
  layer.
- **Data staleness and divergence metrics per shared entity.** For any
  entity known to be duplicated across subsystems (customer, order status),
  a dashboard tracking the time since last reconciliation and the count of
  detected divergences is the direct observability signal for the
  consequence named in dimension 10.
- **Bridge ownership gaps.** Whether every bridge has a named owning team
  in whatever system tracks service ownership. A bridge with no owner is
  the leading indicator for the departed-maintainer failure mode in
  dimension 11, and it is a signal that is cheap to check and almost never
  checked in practice.
- **Silent failure rate on batch bridges specifically.** Batch and file
  bridges tend to fail by producing zero rows or stale rows rather than by
  throwing an alertable error, so the useful signal is not "did the job
  succeed" but "did the row count and the freshness of the output match
  expectations," alerted on independently of the job's own exit code.
- **What a healthy instance looks like.** A small number of well-known
  integration technologies (ideally one, a broker or a set of owned APIs),
  each with an on-call owner, each with a monitored contract, and a data
  reconciliation dashboard trending toward zero divergence, is the target
  state this dimension is measuring the organization's distance from.

## 17. Security and privacy implications

Stovepipe System has direct, well-documented security consequences,
distinct from its architectural cost, and they are largely a matter of
engineering judgement extrapolated from the structural facts established
in earlier dimensions rather than independently sourced claims.

- **Duplicated authentication and authorization logic drifts, and drift in
  a security control is a vulnerability, not merely an inconsistency.**
  The identity variant named in dimension 8 means an organization can have
  N different password policies, N different session timeout values, and N
  different privilege checks for what should be the same person's access,
  and an attacker only needs to find the weakest of the N.
- **Ad hoc bridges frequently carry credentials scoped far wider than the
  data they actually move requires.** A batch job or a direct
  cross-database query typically runs with a service account that has far
  more access than the specific data it moves actually requires, because
  scoping it tightly would require the kind of cross-team negotiation the
  bridge was built specifically to avoid. That overprivileged credential,
  once it exists, is a standing target regardless of whether the bridge
  itself is ever compromised through any other means.
- **No single point to apply a security control consistently.** Encryption
  at rest, field-level access control, and audit logging for a regulated
  data element (personal data, financial records, protected health
  information) must each be independently implemented and independently
  audited in every subsystem that holds a copy, multiplying both the
  implementation surface and the audit burden, and multiplying the number
  of places a single missed control can leak the data.
- **Undocumented bridges are a blind spot for incident response.** When a
  breach or a data-quality incident is being investigated, an
  undocumented, unowned batch job moving data between two systems is
  exactly the kind of path that is missed in the initial containment and
  discovered only later, extending the window an incident remains active.
- **This is where the fix helps most directly, not just architecturally.**
  Consolidating identity and access control into a single shared layer, as
  described in dimension 14, is simultaneously the architectural fix and
  the security fix, since it collapses N independently drifting
  implementations of the same control into one implementation that can
  actually be kept correct and audited.

## 18. References

1. William J. Brown, Raphael C. Malveau, Hays W. "Skip" McCormick III, and
   Thomas J. Mowbray, *AntiPatterns. Refactoring Software, Architectures,
   and Projects in Crisis*, John Wiley and Sons, 1998, chapter 6.
2. Dr. Dobb's, excerpt and summary of the AntiPatterns book's catalog of
   architecture-level antipatterns.
   http://web.archive.org/web/20240227013914/https://drdobbs.com/architecture-and-design/antipatterns/184410581,
   verified 2026-08-02.
3. Wikipedia, "Stovepipe system," including the cited U.S. Department of
   Energy 1999 definition and the origin of the visual metaphor.
   https://en.wikipedia.org/wiki/Stovepipe_system, verified 2026-08-02.
4. exceptionnotfound.net, "Stovepipe Enterprise, The Daily Software
   Anti-Pattern." http://web.archive.org/web/20251208073835/https://www.exceptionnotfound.net/stovepipe-enterprise-the-daily-software-anti-pattern/,
   content verified through an automated retrieval summary on 2026-08-02
   after the live site returned an intermittent server error on direct
   re-fetch, treat this specific source as lower confidence than the
   others in this list and prefer source 1 or 3 for the same claims where
   they overlap.
5. Joel Spolsky, "In Defense of Not-Invented-Here Syndrome," Joel on
   Software, October 14, 2001.
   https://www.joelonsoftware.com/2001/10/14/in-defense-of-not-invented-here-syndrome/,
   verified 2026-08-02.
6. U.S. Government Accountability Office, GAO/NSIAD-87-124, "Interoperability.
   DOD's Efforts To Achieve Interoperability Among C3 Systems."
   https://www.gao.gov/products/nsiad-87-124, verified 2026-08-02.
7. U.S. Government Accountability Office, GAO-04-858, "Defense Acquisitions.
   The Global Information Grid and Challenges Facing Its Implementation."
   https://www.gao.gov/assets/gao-04-858.pdf, verified 2026-08-02.
8. U.S. Government Accountability Office, GAO-25-107611, "Information
   Technology. IRS Is Developing a New Modernization Framework."
   https://www.gao.gov/assets/gao-25-107611.pdf, verified 2026-08-02.
9. ResearchGate, "Software design patterns for message driven service
   oriented integration of stovepipe applications in healthcare
   enterprise." https://www.researchgate.net/publication/228342050_Software_design_patterns_for_message_driven_service_oriented_integration_of_stovepipe_applications_in_healthcare_enterprise,
   verified 2026-08-02, cited for the paper's existence and framing, its
   internal methodology and results were not independently re-verified.
10. Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns.
    Designing, Building, and Deploying Messaging Solutions*, Addison-Wesley,
    2003.
11. Martin Fowler, summary and endorsement page for *Enterprise
    Integration Patterns*. https://martinfowler.com/books/eip.html,
    verified 2026-08-02.
12. Gregor Hohpe and Bobby Woolf, "Enterprise Integration Patterns," PLoP
    conference final draft, describing the point-to-point integration
    problem the book's catalog addresses.
    https://www.enterpriseintegrationpatterns.com/docs/Enterprise%20Integration%20Patterns%20-%20PLoP%20Final%20Draft%203.pdf,
    verified 2026-08-02.

## Code examples

Three languages illustrate the antipattern the way it actually appears in a
codebase, three vertical subsystems, each with its own duplicated identity
logic, each connected to its neighbors through a different ad hoc bridge
technology, and no shared abstraction anywhere in sight. The value of the
example is recognition of the shape, not imitation of it. All three were
run directly. Java, Rust, C#, and Kotlin were skipped for this entry, since
the antipattern is architectural rather than language-specific, and three
languages already show three different bridge technologies (a direct
in-process call standing in for a cross-database query, a JSON file
standing in for a batch export, and a hand-parsed string response standing
in for a one-off point-to-point API) without needing a fourth to make the
shape clear.

TypeScript, the duplicated-identity variant plus a direct-query-style bridge.
Billing and Shipping each maintain their own user store with their own
password rules, and Shipping reaches directly into Billing's private map to
look up a customer rather than calling any shared interface.

```typescript
// billing.ts
class BillingUsers {
  private store = new Map<string, { pass: string; tier: string }>([
    ["alice", { pass: "hunter2", tier: "gold" }],
  ]);

  login(name: string, pass: string): boolean {
    const u = this.store.get(name);
    return !!u && u.pass === pass && pass.length >= 6;
  }

  // exposed only so shipping.ts can reach in directly, not a real API
  peekCustomer(name: string) {
    return this.store.get(name);
  }
}

// shipping.ts
class ShippingUsers {
  private store = new Map<string, { pass: string; zone: string }>([
    ["alice", { pass: "hunter2", zone: "EU" }],
  ]);

  login(name: string, pass: string): boolean {
    const u = this.store.get(name);
    // note the different, drifted password rule, no length check here
    return !!u && u.pass === pass;
  }

  shipFor(name: string, billing: BillingUsers): string {
    const b = billing.peekCustomer(name); // ad hoc bridge, reaches into billing directly
    if (!b) return `no billing record for ${name}, cannot ship`;
    return `shipping to ${name}, tier ${b.tier}, zone ${this.store.get(name)?.zone}`;
  }
}

const billing = new BillingUsers();
const shipping = new ShippingUsers();
console.log("billing login", billing.login("alice", "hunter2"));
console.log("shipping login", shipping.login("alice", "hunter2"));
console.log(shipping.shipFor("alice", billing));
```

Python, the batch file bridge variant. Support has no live connection to
Shipping at all, only a nightly-exported JSON file it reads on demand, so a
key rename in Shipping's export silently breaks Support without either
side's own tests noticing.

```python
import json
import tempfile
import os

# shipping subsystem writes its own nightly export, its own format
_shipping_orders = {"4471": {"status": "shipped", "carrier": "UPS"}}

def shipping_export_job(path):
    with open(path, "w") as f:
        json.dump(_shipping_orders, f)

# support subsystem only ever reads that file, it has no other way to know
def support_lookup_shipping_status(path, order_id):
    if not os.path.exists(path):
        return "unknown, bridge file missing"
    with open(path) as f:
        data = json.load(f)
    order = data.get(order_id)
    if order is None:
        return "unknown, no record in last export"
    return order.get("status", "unknown, status field missing")

tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
tmp.close()
try:
    shipping_export_job(tmp.name)
    print("support sees", support_lookup_shipping_status(tmp.name, "4471"))

    # shipping renames its field, entirely for its own internal reasons
    _shipping_orders["4471"] = {"shipping_status": "shipped", "carrier": "UPS"}
    shipping_export_job(tmp.name)
    print("support sees after rename", support_lookup_shipping_status(tmp.name, "4471"))
finally:
    os.unlink(tmp.name)
```

Go, the ad hoc point-to-point API variant. Reporting talks to Billing over a
bespoke, one-off endpoint whose response shape was designed for exactly
this single caller, with no shared contract, no versioning, and no schema
either side treats as stable.

```go
package main

import "fmt"

// billing's own private notion of a customer, never generalized
type billingCustomer struct {
	Name string
	Tier string
}

var billingStore = map[string]billingCustomer{
	"alice": {Name: "alice", Tier: "gold"},
}

// a bespoke, one-off "API" built only for reporting to call, nothing else
// in the system uses this shape and it was never designed as a contract
func billingReportEndpoint(name string) (string, bool) {
	c, ok := billingStore[name]
	if !ok {
		return "", false
	}
	return fmt.Sprintf("name=%s;tier=%s", c.Name, c.Tier), true
}

// reporting subsystem parses that ad hoc string format itself, by hand
func reportingFetchCustomerLine(name string) string {
	raw, ok := billingReportEndpoint(name)
	if !ok {
		return fmt.Sprintf("no billing data for %s", name)
	}
	return fmt.Sprintf("report row, %s", raw)
}

func main() {
	fmt.Println(reportingFetchCustomerLine("alice"))
	fmt.Println(reportingFetchCustomerLine("bob"))
}
```
